import os
import sys
import venv
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")


def _venv_python_path():
    if os.name == "nt":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def _running_inside_target_venv():
    return os.path.abspath(_venv_python_path()) == os.path.abspath(sys.executable)


def bootstrap_venv_and_relaunch():
    if not os.path.isdir(VENV_DIR):
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)

    venv_python = _venv_python_path()
    req_path = os.path.join(SCRIPT_DIR, "requirements.txt")

    if os.path.exists(req_path):
        subprocess.run([venv_python, "-m", "pip", "install", "-r", req_path, "-q"], check=True)

    result = subprocess.run([venv_python, os.path.abspath(__file__), *sys.argv[1:]])
    sys.exit(result.returncode)


if not _running_inside_target_venv():
    bootstrap_venv_and_relaunch()

import random
import logging
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "python-dotenv", "-q"])
    from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

load_dotenv()


def _env(key, default=None, required=False):
    value = os.environ.get(key, default)
    if required and not value:
        print(f"MISSING_ENV: {key}")
        sys.exit(1)
    return value


BOT_TOKEN = _env("COMMIT_BOT_TOKEN", required=True)
ADMIN_ID = int(_env("COMMIT_BOT_ADMIN_ID", required=True))
REPO_PATH = _env("COMMIT_BOT_REPO_PATH", required=True)
TARGET_FILE = _env("COMMIT_BOT_TARGET_FILE", "README.md")
MIN_COMMITS_PER_DAY = int(_env("COMMIT_BOT_MIN_PER_DAY", "4"))
MAX_COMMITS_PER_DAY = int(_env("COMMIT_BOT_MAX_PER_DAY", "7"))
DAY_START_HOUR = int(_env("COMMIT_BOT_WINDOW_START_HOUR", "9"))
DAY_END_HOUR = int(_env("COMMIT_BOT_WINDOW_END_HOUR", "23"))
LANG = _env("COMMIT_BOT_LANG", "tr").lower()
if LANG not in ("tr", "en"):
    LANG = "tr"

STRINGS = {
    "tr": {
        "not_authorized": "Yetkisiz.",
        "start": (
            "Commit Bot hazır.\n\n"
            "/enable — otomasyonu başlat\n"
            "/disable — otomasyonu durdur\n"
            "/status — mevcut durumu göster\n"
            "/runonce — hemen 1 commit at\n"
            "/lang tr|en — dil değiştir"
        ),
        "enabled": "✅ Otomasyon açıldı. Bugün için {count} işlem planlandı.",
        "disabled": "⛔ Otomasyon durduruldu, bekleyen işlemler iptal edildi.",
        "status": "Durum: {state}\nBugün planlanan: {planned}\nBugün yapılan: {done}\nSon çalışma: {last}",
        "state_on": "AÇIK",
        "state_off": "KAPALI",
        "running": "Çalıştırılıyor...",
        "commit_ok": "🟢 İşlem başarılı ({ts})",
        "commit_fail": "🔴 İşlem başarısız: {err}",
        "lang_set": "Dil ayarlandı: {lang}",
        "lang_usage": "Kullanım: /lang tr veya /lang en",
    },
    "en": {
        "not_authorized": "Not authorized.",
        "start": (
            "Commit Bot ready.\n\n"
            "/enable — start automation\n"
            "/disable — stop automation\n"
            "/status — show current status\n"
            "/runonce — run one commit now\n"
            "/lang tr|en — change language"
        ),
        "enabled": "✅ Automation enabled. {count} run(s) planned for today.",
        "disabled": "⛔ Automation disabled, pending runs cancelled.",
        "status": "Status: {state}\nPlanned today: {planned}\nDone today: {done}\nLast run: {last}",
        "state_on": "ON",
        "state_off": "OFF",
        "running": "Running...",
        "commit_ok": "🟢 Run succeeded ({ts})",
        "commit_fail": "🔴 Run failed: {err}",
        "lang_set": "Language set: {lang}",
        "lang_usage": "Usage: /lang tr or /lang en",
    },
}


def t(key, **kwargs):
    return STRINGS[LANG][key].format(**kwargs)


logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger("commit_bot")

state = {
    "enabled": False,
    "scheduler": None,
    "today_planned": 0,
    "today_done": 0,
    "last_run": None,
}


def is_admin(update):
    return update.effective_user is not None and update.effective_user.id == ADMIN_ID


def run_commit_and_push():
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        target_path = os.path.join(REPO_PATH, TARGET_FILE)

        with open(target_path, "a", encoding="utf-8") as f:
            f.write(f"\n<!-- sync: {timestamp} -->")

        subprocess.run(["git", "add", TARGET_FILE], cwd=REPO_PATH, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"chore: sync {timestamp}", "--no-gpg-sign"],
            cwd=REPO_PATH,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=REPO_PATH, check=True)

        state["today_done"] += 1
        state["last_run"] = timestamp
        return True, timestamp
    except subprocess.CalledProcessError as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


def plan_todays_runs(scheduler, app):
    count = random.randint(MIN_COMMITS_PER_DAY, MAX_COMMITS_PER_DAY)
    state["today_planned"] = count
    state["today_done"] = 0

    now = datetime.now()
    window_start = now.replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)
    window_end = now.replace(hour=DAY_END_HOUR, minute=0, second=0, microsecond=0)

    if now > window_start:
        window_start = now

    window_seconds = int((window_end - window_start).total_seconds())
    if window_seconds <= 0:
        return

    offsets = sorted(random.sample(range(window_seconds), k=min(count, window_seconds)))

    for i, offset in enumerate(offsets):
        run_time = window_start.fromtimestamp(window_start.timestamp() + offset)
        scheduler.add_job(
            scheduled_job,
            trigger=DateTrigger(run_date=run_time),
            args=[app],
            id=f"job_{run_time.strftime('%H%M%S')}_{i}",
            misfire_grace_time=3600,
        )


async def scheduled_job(app):
    ok, info = run_commit_and_push()
    msg = t("commit_ok", ts=info) if ok else t("commit_fail", err=info)
    logger.info(msg)
    try:
        await app.bot.send_message(chat_id=ADMIN_ID, text=msg)
    except Exception:
        pass


def daily_planning_job(scheduler, app):
    if state["enabled"]:
        plan_todays_runs(scheduler, app)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(t("start"))


async def enable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    state["enabled"] = True
    plan_todays_runs(state["scheduler"], context.application)
    await update.message.reply_text(t("enabled", count=state["today_planned"]))


async def disable(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    state["enabled"] = False
    for job in state["scheduler"].get_jobs():
        if job.id.startswith("job_"):
            job.remove()
    await update.message.reply_text(t("disabled"))


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(
        t(
            "status",
            state=t("state_on") if state["enabled"] else t("state_off"),
            planned=state["today_planned"],
            done=state["today_done"],
            last=state["last_run"] or "-",
        )
    )


async def runonce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        return
    await update.message.reply_text(t("running"))
    ok, info = run_commit_and_push()
    await update.message.reply_text(t("commit_ok", ts=info) if ok else t("commit_fail", err=info))


async def lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global LANG
    if not is_admin(update):
        return
    if not context.args or context.args[0].lower() not in ("tr", "en"):
        await update.message.reply_text(t("lang_usage"))
        return
    LANG = context.args[0].lower()
    await update.message.reply_text(t("lang_set", lang=LANG))


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    scheduler = AsyncIOScheduler()
    state["scheduler"] = scheduler
    scheduler.add_job(
        daily_planning_job,
        trigger="cron",
        hour=DAY_START_HOUR,
        minute=0,
        args=[scheduler, app],
        id="daily_planner",
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("enable", enable))
    app.add_handler(CommandHandler("disable", disable))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("runonce", runonce))
    app.add_handler(CommandHandler("lang", lang))

    scheduler.start()
    app.run_polling()


if __name__ == "__main__":
    main()