# Telegram Contact Saver Bot (Python)

A Python Telegram bot that automatically saves emails and phone numbers you send.

## Features
- Auto-detects and saves emails + phone numbers from any text message.
- `/start` shows buttons:
  - **Get Emails** (one per line)
  - **Get Numbers** (one per line)
  - **Empty** (email delete UI)
- **Empty** opens paginated email management:
  - 10 emails per page
  - masked email labels (`treas***01@...` style)
  - select multiple
  - **Delete Selected**
  - **Delete All**
  - **Cancel**
- `/del` command supports:
  - `/del email1,email2`
  - `/del no1,no2`
  - `/del all mail`
  - `/del all email`
  - `/del all emails`
  - `/del all e`
  - `/del all no`
  - `/del all number`

## Security / storage
- Data is saved in encrypted JSON payloads in `data/*.enc`.
- Set env key with `BOT_DATA_KEY`.
- If the key changes, saved data is reset automatically.

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="<your_bot_token>"
export BOT_DATA_KEY="<strong_secret>"
python bot.py
```
