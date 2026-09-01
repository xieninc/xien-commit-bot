# XiEn Commit Bot

Bir git reposunda gün içinde rastgele saatlerde otomatik commit ve push işlemi yapan, Telegram üzerinden yönetilen bir otomasyon botu.

---

## 🇹🇷 Türkçe

### Özellikler

* Günlük 4–7 arası (ayarlanabilir) rastgele sayıda commit atar
* Commit'ler belirlenen saat aralığına rastgele dağıtılır
* Tüm yönetim Telegram bot komutlarıyla yapılır
* Bağımlılıklar ve sanal ortam (`.venv`) ilk çalıştırmada otomatik kurulur
* Tüm ayarlar `.env` dosyasından okunur, kod içinde gizli bilgi bulunmaz

### Kurulum

1. Bu repoyu klonla veya indir.
2. `.env.example` dosyasını `.env` olarak kopyala ve kendi bilgilerinle doldur:
   * `COMMIT_BOT_TOKEN` — Telegram bot token'ı
   * `COMMIT_BOT_ADMIN_ID` — botu yönetecek Telegram kullanıcı ID'si
   * `COMMIT_BOT_REPO_PATH` — commit atılacak hedef reponun local yolu
   * `COMMIT_BOT_TARGET_FILE` — değiştirilecek dosya (varsayılan: `README.md`)
   * `COMMIT_BOT_MIN_PER_DAY` / `COMMIT_BOT_MAX_PER_DAY` — günlük commit aralığı
   * `COMMIT_BOT_WINDOW_START_HOUR` / `COMMIT_BOT_WINDOW_END_HOUR` — commit'lerin dağılacağı saat penceresi
   * `COMMIT_BOT_LANG` — `tr` veya `en`
3. Botu başlat:
   ```
   python main.py
   ```
   İlk çalıştırmada sanal ortam oluşturulur ve gerekli paketler otomatik kurulur.

### Telegram Komutları

| Komut | Açıklama |
|---|---|
| `/start` | Komut listesini gösterir |
| `/enable` | Otomasyonu başlatır |
| `/disable` | Otomasyonu durdurur |
| `/status` | Güncel durumu gösterir |
| `/runonce` | Hemen bir işlem çalıştırır |
| `/lang tr\|en` | Bot dilini değiştirir |

### Güvenlik

`.env` dosyası `.gitignore` ile hariç tutulmuştur, repoya asla commit edilmez.

---

## 🇬🇧 English

### Features

* Runs 4–7 (configurable) random commits per day
* Runs are distributed randomly within a configurable time window
* Fully managed through Telegram bot commands
* Dependencies and a virtual environment (`.venv`) are set up automatically on first run
* All configuration is read from `.env`, no secrets live in the code

### Setup

1. Clone or download this repo.
2. Copy `.env.example` to `.env` and fill in your own values:
   * `COMMIT_BOT_TOKEN` — Telegram bot token
   * `COMMIT_BOT_ADMIN_ID` — Telegram user ID allowed to control the bot
   * `COMMIT_BOT_REPO_PATH` — local path of the target repo to commit to
   * `COMMIT_BOT_TARGET_FILE` — file to modify (default: `README.md`)
   * `COMMIT_BOT_MIN_PER_DAY` / `COMMIT_BOT_MAX_PER_DAY` — daily commit range
   * `COMMIT_BOT_WINDOW_START_HOUR` / `COMMIT_BOT_WINDOW_END_HOUR` — time window for runs
   * `COMMIT_BOT_LANG` — `tr` or `en`
3. Start the bot:
   ```
   python main.py
   ```
   On first run, a virtual environment is created and dependencies are installed automatically.

### Telegram Commands

| Command | Description |
|---|---|
| `/start` | Shows the command list |
| `/enable` | Starts automation |
| `/disable` | Stops automation |
| `/status` | Shows current status |
| `/runonce` | Runs one job immediately |
| `/lang tr\|en` | Changes bot language |

### Security

`.env` is excluded via `.gitignore` and is never committed to the repo.