import base64
import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

from cryptography.fernet import Fernet, InvalidToken
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

DATA_DIR = Path("data")
EMAIL_FILE = DATA_DIR / "emails.enc"
NUMBER_FILE = DATA_DIR / "numbers.enc"
STATE_FILE = DATA_DIR / "state.enc"
PAGE_SIZE = 10
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
NUMBER_RE = re.compile(r"(?<!\w)(\+?\d[\d\s\-()]{6,}\d)(?!\w)")


def build_fernet() -> Fernet:
    secret = os.getenv("BOT_DATA_KEY", "")
    if not secret:
        raise RuntimeError("BOT_DATA_KEY is required.")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def key_fingerprint() -> str:
    return hashlib.sha256(os.getenv("BOT_DATA_KEY", "").encode("utf-8")).hexdigest()


class EncryptedStore:
    def __init__(self, fernet: Fernet):
        self.fernet = fernet
        DATA_DIR.mkdir(exist_ok=True)
        self._check_or_reset_key()

    def _encrypt_obj(self, obj: object) -> bytes:
        raw = json.dumps(obj, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return self.fernet.encrypt(raw)

    def _decrypt_obj(self, payload: bytes):
        raw = self.fernet.decrypt(payload)
        return json.loads(raw.decode("utf-8"))

    def _check_or_reset_key(self) -> None:
        current_fp = key_fingerprint()
        if not STATE_FILE.exists():
            STATE_FILE.write_bytes(self._encrypt_obj({"fingerprint": current_fp}))
            return
        try:
            state = self._decrypt_obj(STATE_FILE.read_bytes())
            if state.get("fingerprint") != current_fp:
                self.reset_all()
        except (InvalidToken, json.JSONDecodeError, OSError):
            self.reset_all()

    def reset_all(self) -> None:
        for path in (EMAIL_FILE, NUMBER_FILE):
            path.write_bytes(self._encrypt_obj([]))
        STATE_FILE.write_bytes(self._encrypt_obj({"fingerprint": key_fingerprint()}))

    def load_list(self, path: Path) -> List[str]:
        if not path.exists():
            path.write_bytes(self._encrypt_obj([]))
            return []
        try:
            data = self._decrypt_obj(path.read_bytes())
            if isinstance(data, list):
                return [str(x) for x in data]
        except (InvalidToken, json.JSONDecodeError, OSError):
            pass
        self.reset_all()
        return []

    def save_list(self, path: Path, values: List[str]) -> None:
        path.write_bytes(self._encrypt_obj(values))


@dataclass
class MemoryData:
    emails: Set[str] = field(default_factory=set)
    numbers: Set[str] = field(default_factory=set)


store: EncryptedStore
memory = MemoryData()


def load_memory() -> None:
    memory.emails = set(store.load_list(EMAIL_FILE))
    memory.numbers = set(store.load_list(NUMBER_FILE))


def persist_memory() -> None:
    store.save_list(EMAIL_FILE, sorted(memory.emails))
    store.save_list(NUMBER_FILE, sorted(memory.numbers))


def normalize_number(raw: str) -> str:
    raw = raw.strip()
    plus = raw.startswith("+")
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 7:
        return ""
    return f"+{digits}" if plus else digits


def mask_email(email: str) -> str:
    local, domain = email.split("@", 1)
    if len(local) <= 4:
        local_masked = local[0] + "*" * max(1, len(local) - 1)
    else:
        local_masked = f"{local[:5]}***{local[-2:]}"
    return f"{local_masked}@{domain}"


def extract_from_text(text: str) -> Tuple[List[str], List[str]]:
    emails = sorted(set(m.group(0).lower() for m in EMAIL_RE.finditer(text)))
    nums = []
    for m in NUMBER_RE.finditer(text):
        n = normalize_number(m.group(1))
        if n:
            nums.append(n)
    numbers = sorted(set(nums))
    return emails, numbers


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton("Get Emails")], [KeyboardButton("Get Numbers")], [KeyboardButton("Empty")]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "Send me any message with emails/numbers and I will save them automatically.\n"
        "Use buttons or /del commands to manage saved items.",
        reply_markup=keyboard,
    )


async def get_emails(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    body = "\n".join(sorted(memory.emails)) if memory.emails else "No emails saved."
    await update.message.reply_text(body)


async def get_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    body = "\n".join(sorted(memory.numbers)) if memory.numbers else "No numbers saved."
    await update.message.reply_text(body)


def build_email_page(page: int, selected: Set[str]) -> InlineKeyboardMarkup:
    emails = sorted(memory.emails)
    total_pages = max(1, (len(emails) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = max(0, min(page, total_pages - 1))
    subset = emails[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    rows: List[List[InlineKeyboardButton]] = []
    for email in subset:
        marker = "✅" if email in selected else "☐"
        rows.append([InlineKeyboardButton(f"{marker} {mask_email(email)}", callback_data=f"toggle:{page}:{email}")])

    nav: List[InlineKeyboardButton] = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"page:{page+1}"))

    rows.append(nav)
    rows.append(
        [
            InlineKeyboardButton("Delete Selected", callback_data=f"delete_selected:{page}"),
            InlineKeyboardButton("Delete All", callback_data=f"delete_all:{page}"),
        ]
    )
    rows.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(rows)


async def empty_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["selected"] = set()
    if not memory.emails:
        await update.message.reply_text("No emails to manage.")
        return
    await update.message.reply_text(
        "Select emails to delete:",
        reply_markup=build_email_page(0, context.user_data["selected"]),
    )


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if text == "Get Emails":
        await get_emails(update, context)
        return
    if text == "Get Numbers":
        await get_numbers(update, context)
        return
    if text == "Empty":
        await empty_menu(update, context)
        return

    emails, numbers = extract_from_text(text)
    added_e = [e for e in emails if e not in memory.emails]
    added_n = [n for n in numbers if n not in memory.numbers]
    if added_e:
        memory.emails.update(added_e)
    if added_n:
        memory.numbers.update(added_n)
    if added_e or added_n:
        persist_memory()
        await update.message.reply_text(f"Saved {len(added_e)} email(s) and {len(added_n)} number(s).")
    else:
        await update.message.reply_text("No new email/number found.")


async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    arg = " ".join(context.args).strip()
    if not arg:
        await update.message.reply_text("Usage: /del email1,email2 OR /del no1,no2 OR /del all emails OR /del all number")
        return

    lower = arg.lower().strip()
    if lower.startswith("all"):
        if any(x in lower for x in ["mail", "email", "emails", "e"]):
            count = len(memory.emails)
            memory.emails.clear()
            persist_memory()
            await update.message.reply_text(f"Deleted all emails ({count}).")
            return
        if any(x in lower for x in ["no", "number", "numbers"]):
            count = len(memory.numbers)
            memory.numbers.clear()
            persist_memory()
            await update.message.reply_text(f"Deleted all numbers ({count}).")
            return

    parts = [p.strip() for p in arg.split(",") if p.strip()]
    removed = 0
    for p in parts:
        lp = p.lower()
        if "@" in p:
            if lp in memory.emails:
                memory.emails.remove(lp)
                removed += 1
        else:
            n = normalize_number(p)
            if n and n in memory.numbers:
                memory.numbers.remove(n)
                removed += 1
    persist_memory()
    await update.message.reply_text(f"Deleted {removed} item(s).")


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data or ""
    selected: Set[str] = context.user_data.setdefault("selected", set())

    if data == "noop":
        return
    if data == "cancel":
        context.user_data["selected"] = set()
        await query.edit_message_text("Cancelled.")
        return
    if data.startswith("page:"):
        page = int(data.split(":", 1)[1])
        await query.edit_message_reply_markup(reply_markup=build_email_page(page, selected))
        return
    if data.startswith("toggle:"):
        _, page_s, email = data.split(":", 2)
        if email in selected:
            selected.remove(email)
        else:
            selected.add(email)
        await query.edit_message_reply_markup(reply_markup=build_email_page(int(page_s), selected))
        return
    if data.startswith("delete_selected:"):
        page = int(data.split(":", 1)[1])
        deleted = 0
        for email in list(selected):
            if email in memory.emails:
                memory.emails.remove(email)
                deleted += 1
        context.user_data["selected"] = set()
        persist_memory()
        if not memory.emails:
            await query.edit_message_text(f"Deleted {deleted} selected email(s). No emails remaining.")
            return
        await query.edit_message_reply_markup(reply_markup=build_email_page(page, set()))
        return
    if data.startswith("delete_all:"):
        count = len(memory.emails)
        memory.emails.clear()
        context.user_data["selected"] = set()
        persist_memory()
        await query.edit_message_text(f"Deleted all emails ({count}).")


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required.")

    global store
    store = EncryptedStore(build_fernet())
    load_memory()

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("del", del_command))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
