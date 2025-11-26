import os
import subprocess
import datetime
import requests
import sys
import logging
from pathlib import Path

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_backups():
    backups = sorted(Path(BACKUP_DIR).glob(f"{BACKUP_NAME_PREFIX}*.dump"))
    if len(backups) > 2:
        for old_file in backups[:-2]:
            try:
                old_file.unlink()
                logger.info(f"Удален старый бэкап: {old_file.name}")
            except Exception as e:
                logger.warning(f"Не удалось удалить {old_file.name}: {e}")

def run_pg_dump():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    dump_name = f"{BACKUP_NAME_PREFIX}{timestamp}.dump"
    dump_path = os.path.join(BACKUP_DIR, dump_name)

    os.makedirs(BACKUP_DIR, exist_ok=True)

    cmd = [
        "pg_dump",
        "-h", PG_HOST,
        "-p", PG_PORT,
        "-U", PG_USER,
        "-d", PG_DATABASE,
        "-F", "c",
        "-f", dump_path
    ]

    env = os.environ.copy()
    env["PGPASSWORD"] = PG_PASSWORD

    try:
        logger.info(f"Запуск pg_dump в {dump_path}...")
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
        logger.info("Бэкап успешно завершен")
        return dump_name, True, ""
    except subprocess.CalledProcessError as e:
        logger.error("Ошибка при снятии бэкапа:")
        logger.error(e.output.decode())
        return None, False, e.output.decode()

def update_telegram(status, dump_name=None, error=None):
    text = ""
    if status:
        text = f"✅ Бэкап успешно сохранен в {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Файл: `{dump_name}`"
    else:
        text = f"❌ Ошибка при сохранении бэкапа в {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        text += f"Ошибка: `{error.strip()[:200]}`"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_id": TELEGRAM_MESSAGE_ID,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        resp = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText", data=payload)
        logger.info(f"Telegram: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.warning(f"Не удалось обновить Telegram-сообщение: {e}")

# Переменные окружения
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_USER = os.getenv("PG_USER", "asd")
PG_PASSWORD = os.getenv("PG_PASSWORD", "asd")
PG_DATABASE = os.getenv("PG_DATABASE", "asd")

BACKUP_NAME_PREFIX = os.getenv("BACKUP_NAME_PREFIX", "backup-")
BACKUP_DIR = os.getenv("BACKUP_DIR", "/data")

TELEGRAM_ENABLED = os.getenv("TELEGRAM", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", 0)
TELEGRAM_MESSAGE_ID = os.getenv("TELEGRAM_MESSAGE_ID", 0)

cleanup_old_backups()

dump_name, success, error = run_pg_dump()

if TELEGRAM_ENABLED:
    update_telegram(success, dump_name, error if not success else None)

