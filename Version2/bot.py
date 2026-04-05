import atexit
import base64
import hashlib
import html
import json
import logging
import os
import re
import signal
import smtplib
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv
from openai import OpenAI
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InputFile, Update
from telegram.error import Conflict
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

if os.name == "nt":
    import msvcrt
else:
    import fcntl


LOGGER = logging.getLogger("stackfuse.bot.v2")
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)


@dataclass(frozen=True)
class AppConfig:
    openai_api_key: str
    telegram_bot_token: str
    openai_model: str
    default_from: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool
    google_client_id: str
    google_client_secret: str
    gmail_refresh_token: str
    script_dir: Path
    template_path: Path
    gmail_token_path: Path
    lock_root: Path


@dataclass
class EmailSection:
    title: str
    body: str
    metric_label: Optional[str] = None
    metric_value: Optional[str] = None


@dataclass
class StructuredEmail:
    subject: str
    preheader: str
    company_name: str
    tagline: str
    hero_title: str
    hero_subtitle: str
    intro_paragraph: str
    sections: List[EmailSection]
    cta_text: str
    cta_url: str
    closing_paragraph: str
    sender_name: str
    sender_role: str
    footer_note: str
    to_address: Optional[str] = None


@dataclass
class RuntimeState:
    config: AppConfig
    client: OpenAI
    gmail_creds: object
    can_send: bool


class TokenScopedLock:
    def __init__(self, token: str, lock_root: Path):
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:20]
        self._path = lock_root / f"telegram-bot-{digest}.lock"
        self._handle = None

    @property
    def path(self) -> Path:
        return self._path

    def acquire(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self._path, "a+", encoding="utf-8")

        try:
            self._lock_file()
        except OSError as exc:
            owner = self._read_owner_metadata()
            raise RuntimeError(
                "Another instance is already running for this Telegram token. "
                f"Lock: {self._path}. Owner metadata: {owner}"
            ) from exc

        metadata = {
            "pid": os.getpid(),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "script": str(Path(__file__).resolve()),
            "cwd": str(Path.cwd()),
            "python": sys.executable,
        }
        self._handle.seek(0)
        self._handle.truncate()
        self._handle.write(json.dumps(metadata))
        self._handle.flush()
        atexit.register(self.release)

    def release(self) -> None:
        if not self._handle:
            return
        try:
            self._handle.seek(0)
            self._handle.truncate()
            self._unlock_file()
        finally:
            self._handle.close()
            self._handle = None

    def _lock_file(self) -> None:
        if os.name == "nt":
            try:
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise OSError("lock unavailable") from exc
        else:
            try:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise OSError("lock unavailable") from exc

    def _unlock_file(self) -> None:
        if os.name == "nt":
            try:
                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)

    def _read_owner_metadata(self) -> str:
        if not self._handle:
            return "unknown"
        try:
            self._handle.seek(0)
            data = self._handle.read().strip()
            return data or "unknown"
        except Exception:
            return "unknown"


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def build_config() -> AppConfig:
    load_dotenv()
    script_dir = Path(__file__).resolve().parent

    openai_api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    telegram_bot_token = (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()

    if not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is required")
    if not telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required")

    lock_root = Path(tempfile.gettempdir()) / "stackfuse-email-maker-locks"

    return AppConfig(
        openai_api_key=openai_api_key,
        telegram_bot_token=telegram_bot_token,
        openai_model=(os.getenv("OPENAI_MODEL") or "gpt-5-mini-2025-08-07").strip(),
        default_from=(os.getenv("DEFAULT_FROM") or "").strip() or "Stackfuse <contact@stackfuse.pro>",
        smtp_host=(os.getenv("SMTP_HOST") or "").strip(),
        smtp_port=int((os.getenv("SMTP_PORT") or "587").strip()),
        smtp_user=(os.getenv("SMTP_USER") or "").strip(),
        smtp_password=(os.getenv("SMTP_PASSWORD") or "").strip(),
        smtp_use_tls=(os.getenv("SMTP_USE_TLS") or "true").strip().lower() in {"1", "true", "yes"},
        google_client_id=(os.getenv("GOOGLE_CLIENT_ID") or "").strip(),
        google_client_secret=(os.getenv("GOOGLE_CLIENT_SECRET") or "").strip(),
        gmail_refresh_token=(os.getenv("GMAIL_REFRESH_TOKEN") or "").strip(),
        script_dir=script_dir,
        template_path=script_dir / "email_template.html",
        gmail_token_path=script_dir / "gmail_token.json",
        lock_root=lock_root,
    )


def load_gmail_credentials(config: AppConfig):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        return None

    scopes = ["https://www.googleapis.com/auth/gmail.send"]

    if config.gmail_token_path.is_file():
        try:
            creds = Credentials.from_authorized_user_file(str(config.gmail_token_path), scopes=scopes)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            if creds and creds.valid:
                return creds
        except Exception as exc:
            LOGGER.warning("Could not load gmail_token.json: %s", exc)

    if config.google_client_id and config.google_client_secret and config.gmail_refresh_token:
        try:
            creds = Credentials(
                token=None,
                refresh_token=config.gmail_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=config.google_client_id,
                client_secret=config.google_client_secret,
                scopes=scopes,
            )
            return creds
        except Exception as exc:
            LOGGER.warning("Could not build Gmail credentials from env: %s", exc)

    return None


def can_send_now(config: AppConfig, gmail_creds: object) -> bool:
    smtp_ready = bool(config.smtp_host and config.smtp_user and config.smtp_password)
    return smtp_ready or bool(gmail_creds)


def load_template(template_path: Path) -> str:
    if not template_path.is_file():
        raise RuntimeError(f"Template file not found: {template_path}")
    return template_path.read_text(encoding="utf-8")


def render_sections_html(sections: List[EmailSection]) -> str:
    if not sections:
        return ""

    rows: List[str] = []
    for section in sections:
        safe_title = html.escape(section.title or "")
        safe_body = html.escape(section.body or "")
        metric_html = ""
        if section.metric_label and section.metric_value:
            safe_metric_label = html.escape(section.metric_label)
            safe_metric_value = html.escape(section.metric_value)
            metric_html = (
                f"<div style=\"margin-top: 8px; color: #b8b8b8; font-size: 12px;\">"
                f"<strong style=\"color:#78ffaa; text-transform: uppercase; letter-spacing: 0.08em;\">{safe_metric_label}</strong>"
                f"<span style=\"color:#f3f3f3; margin-left: 6px;\">{safe_metric_value}</span>"
                f"</div>"
            )

        rows.append(
            "\n".join(
                [
                    "<tr>",
                    "  <td style=\"padding: 0 0 10px 0;\">",
                    "    <table width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" role=\"presentation\" style=\"border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; background: rgba(255,255,255,0.03);\">",
                    "      <tr>",
                    "        <td style=\"padding: 14px 14px 12px 14px;\">",
                    f"          <div style=\"font-size: 14px; font-weight: 600; color: #f5f5f5; margin-bottom: 4px;\">{safe_title}</div>",
                    f"          <div style=\"font-size: 13px; line-height: 1.7; color: #cfcfcf;\">{safe_body}</div>",
                    f"          {metric_html}",
                    "        </td>",
                    "      </tr>",
                    "    </table>",
                    "  </td>",
                    "</tr>",
                ]
            )
        )
    return "\n".join(rows)


def fill_template(template_html: str, structured: StructuredEmail) -> str:
    def _safe(value: str) -> str:
        return html.escape((value or "").strip())

    replacements = {
        "{{subject}}": _safe(structured.subject),
        "{{preheader}}": _safe(structured.preheader),
        "{{company_name}}": _safe(structured.company_name),
        "{{tagline}}": _safe(structured.tagline),
        "{{hero_title}}": _safe(structured.hero_title),
        "{{hero_subtitle}}": _safe(structured.hero_subtitle),
        "{{intro_paragraph}}": _safe(structured.intro_paragraph),
        "{{sections_html}}": render_sections_html(structured.sections),
        "{{cta_text}}": _safe(structured.cta_text),
        "{{cta_url}}": _safe(structured.cta_url),
        "{{closing_paragraph}}": _safe(structured.closing_paragraph),
        "{{sender_name}}": _safe(structured.sender_name),
        "{{sender_role}}": _safe(structured.sender_role),
        "{{footer_note}}": _safe(structured.footer_note),
    }

    html = template_html
    for key, value in replacements.items():
        html = html.replace(key, value or "")
    return html


def build_plain_text(structured: StructuredEmail) -> str:
    text = structured.intro_paragraph.strip()
    if structured.sections:
        text += "\n\nKey points:\n"
        for section in structured.sections:
            line = f"- {section.title}: {section.body}"
            if section.metric_label and section.metric_value:
                line += f" ({section.metric_label}: {section.metric_value})"
            text += line + "\n"
    if structured.closing_paragraph:
        text += "\n" + structured.closing_paragraph.strip() + "\n"
    return text.strip()


def build_email_message(structured: StructuredEmail, html_body: str, to_address: str, from_address: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = structured.subject
    msg["To"] = to_address
    msg["From"] = from_address
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="stackfuse.pro")

    msg.set_content(build_plain_text(structured))
    msg.add_alternative(html_body, subtype="html")
    return msg


def parse_structured_email(json_str: str) -> StructuredEmail:
    data = json.loads(json_str)

    sections_raw = data.get("sections", []) or []
    sections: List[EmailSection] = []
    for item in sections_raw:
        sections.append(
            EmailSection(
                title=(item.get("title") or "").strip(),
                body=(item.get("body") or "").strip(),
                metric_label=(item.get("metric_label") or "").strip() or None,
                metric_value=(item.get("metric_value") or "").strip() or None,
            )
        )

    to_addr = (data.get("to_address") or "").strip() or None
    return StructuredEmail(
        subject=(data.get("subject") or "").strip(),
        preheader=(data.get("preheader") or "").strip(),
        company_name=(data.get("company_name") or "Your Team").strip(),
        tagline=(data.get("tagline") or "Production AI Engineering").strip(),
        hero_title=(data.get("hero_title") or "").strip(),
        hero_subtitle=(data.get("hero_subtitle") or "").strip(),
        intro_paragraph=(data.get("intro_paragraph") or "").strip(),
        sections=sections,
        cta_text=(data.get("cta_text") or "Choose Your Path").strip(),
        cta_url=(data.get("cta_url") or "https://stackfuse.pro/start").strip(),
        closing_paragraph=(data.get("closing_paragraph") or "").strip(),
        sender_name=(data.get("sender_name") or "Stackfuse Team").strip(),
        sender_role=(data.get("sender_role") or "Production AI Engineering").strip(),
        footer_note=(
            data.get("footer_note")
            or "You are receiving this because you asked about AI systems, automation, or workflow design with Stackfuse."
        ).strip(),
        to_address=to_addr,
    )


def call_openai_for_email_structuring(client: OpenAI, model: str, template_html: str, raw_text: str) -> StructuredEmail:
    system_prompt = (
        "You are an expert email copy architect for Stackfuse (https://stackfuse.pro/). "
        "Turn rough email notes into structured values for an existing HTML template.\n\n"
        "Return exactly one JSON object with these keys:\n"
        "subject, preheader, company_name, tagline, hero_title, hero_subtitle, intro_paragraph, "
        "sections (array of {title, body, metric_label, metric_value}), cta_text, cta_url, "
        "closing_paragraph, sender_name, sender_role, footer_note, to_address.\n\n"
        "Rules:\n"
        "- Plain text only in all fields (no markdown or HTML).\n"
        "- Keep the user's intent and tone. Tighten wording only where needed.\n"
        "- Keep sections concise. If not needed, return an empty sections array.\n"
        "- If user gives an email address, set to_address. Else set null.\n"
        "- Output valid JSON only.\n\n"
        "Template context:\n"
        f"{template_html}"
    )

    user_prompt = (
        "User raw notes:\n"
        f"{raw_text.strip()}\n\n"
        "Return the JSON object now."
    )

    last_error: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=4096,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("OpenAI returned empty content")
            return parse_structured_email(content.strip())
        except Exception as exc:
            last_error = exc
            if attempt == 3:
                break
            time.sleep(1.5 * attempt)

    raise RuntimeError(f"OpenAI structuring failed after retries: {last_error}")


def extract_to_override(raw_text: str) -> Tuple[str, Optional[str]]:
    lines = raw_text.splitlines()
    to_address: Optional[str] = None
    remaining: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("TO:"):
            candidate = stripped[3:].strip()
            if EMAIL_RE.fullmatch(candidate):
                to_address = candidate
            continue
        remaining.append(line)

    cleaned = "\n".join(remaining).strip()
    return cleaned or raw_text.strip(), to_address


def _find_first_email(text: str) -> Optional[str]:
    match = EMAIL_RE.search(text)
    return match.group(0) if match else None


def send_email_via_smtp(config: AppConfig, to_address: str, subject: str, html_body: str, plain_body: str, from_address: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        if config.smtp_use_tls:
            smtp.starttls()
        smtp.login(config.smtp_user, config.smtp_password)
        smtp.send_message(msg)


def send_email_via_gmail(gmail_creds: object, to_address: str, subject: str, html_body: str, plain_body: str, from_address: str) -> None:
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = gmail_creds
    if not creds:
        raise RuntimeError("Gmail credentials are not configured")

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    service = build("gmail", "v1", credentials=creds)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _runtime(context: ContextTypes.DEFAULT_TYPE) -> RuntimeState:
    state = context.application.bot_data.get("runtime")
    if not isinstance(state, RuntimeState):
        raise RuntimeError("Runtime state not initialized")
    return state


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Send your rough email notes.\n\n"
        "Optional recipient format: TO: client@company.com\n"
        "I will return a ready-to-send .eml file."
    )


async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    state = _runtime(context)
    lock_path = context.application.bot_data.get("lock_path", "unknown")
    await update.message.reply_text(
        f"OK\nPID: {os.getpid()}\nModel: {state.config.openai_model}\nLock: {lock_path}"
    )


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    state = _runtime(context)
    raw_text = update.message.text

    await update.message.reply_chat_action("typing")
    cleaned_text, explicit_to = extract_to_override(raw_text)

    try:
        template_html = load_template(state.config.template_path)
        structured = await _to_thread(
            call_openai_for_email_structuring,
            state.client,
            state.config.openai_model,
            template_html,
            cleaned_text,
        )

        to_address = explicit_to or structured.to_address or _find_first_email(raw_text) or "recipient@example.com"

        html_body = fill_template(template_html, structured)
        plain_body = build_plain_text(structured)
        msg = build_email_message(structured, html_body, to_address, state.config.default_from)

        context.user_data["last_email"] = {
            "to": to_address,
            "subject": structured.subject,
            "html": html_body,
            "plain": plain_body,
            "from": state.config.default_from,
        }

        buffer = BytesIO(msg.as_bytes())
        buffer.name = "stackfuse-email.eml"

        preview = f"Subject: {structured.subject}\nTo: {to_address}"

        if state.can_send:
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Send now", callback_data="send_now")]])
            await update.message.reply_document(
                document=InputFile(buffer),
                caption="Generated email. Download the .eml or tap Send now.\n\n" + preview,
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_document(
                document=InputFile(buffer),
                caption="Generated email (.eml). Configure Gmail OAuth or SMTP to enable Send now.\n\n" + preview,
            )
    except Exception as exc:
        LOGGER.exception("Email generation failed")
        await update.message.reply_text(
            "Generation failed.\n"
            f"Error: {exc}\n\n"
            "Try a shorter message or check your API credentials."
        )


async def on_send_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or query.data != "send_now":
        return
    await query.answer()

    state = _runtime(context)
    payload = context.user_data.get("last_email")
    if not payload:
        await query.edit_message_caption(caption="No email ready to send. Generate one first.", reply_markup=None)
        return

    try:
        if state.gmail_creds:
            await _to_thread(
                send_email_via_gmail,
                state.gmail_creds,
                payload["to"],
                payload["subject"],
                payload["html"],
                payload["plain"],
                payload["from"],
            )
        elif state.config.smtp_host and state.config.smtp_user and state.config.smtp_password:
            await _to_thread(
                send_email_via_smtp,
                state.config,
                payload["to"],
                payload["subject"],
                payload["html"],
                payload["plain"],
                payload["from"],
            )
        else:
            await query.edit_message_caption(
                caption="Send now is not configured. Add Gmail OAuth or SMTP settings.",
                reply_markup=None,
            )
            return

        await query.edit_message_caption(caption=f"Sent to {payload['to']}", reply_markup=None)
    except Exception as exc:
        LOGGER.exception("Send now failed")
        await query.edit_message_caption(caption=f"Send failed: {exc}", reply_markup=None)


async def post_init(app: Application) -> None:
    me = await app.bot.get_me()
    await app.bot.delete_webhook(drop_pending_updates=True)
    LOGGER.info("Bot authorized as @%s (%s)", me.username, me.id)


def find_local_competitors() -> List[str]:
    if os.name == "nt":
        return []

    try:
        result = subprocess.run(
            ["ps", "-ax", "-o", "pid=,command="],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []

    current_pid = os.getpid()
    matches: List[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pid_str, command = line.split(maxsplit=1)
            pid = int(pid_str)
        except ValueError:
            continue

        if pid == current_pid:
            continue

        cmd_lower = command.lower()
        if "python" in cmd_lower and "bot.py" in cmd_lower and "stackfuse-email-maker" in cmd_lower:
            matches.append(f"PID {pid}: {command}")
    return matches


def install_signal_logging() -> None:
    def _handler(signum, _frame):
        LOGGER.warning("Received signal %s, shutting down", signum)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handler)
        except Exception:
            pass


def run_bot(runtime: RuntimeState, lock: TokenScopedLock) -> None:
    app = (
        ApplicationBuilder()
        .token(runtime.config.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    app.bot_data["runtime"] = runtime
    app.bot_data["lock_path"] = str(lock.path)

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("health", cmd_health))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_send_now, pattern=r"^send_now$"))

    try:
        app.run_polling(drop_pending_updates=True, close_loop=True)
    except Conflict as exc:
        competitors = find_local_competitors()
        extra = ""
        if competitors:
            extra = "\nLocal competitor processes detected:\n" + "\n".join(competitors)

        raise RuntimeError(
            "Telegram polling conflict detected (another getUpdates consumer exists for this bot token).\n"
            "This usually means another bot instance is still running on this or another machine.\n"
            f"Token lock: {lock.path}{extra}"
        ) from exc


async def _to_thread(func, *args):
    try:
        import asyncio

        return await asyncio.to_thread(func, *args)
    except AttributeError:
        # Python <3.9 fallback
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: func(*args))


def main() -> None:
    configure_logging()
    install_signal_logging()

    config = build_config()
    gmail_creds = load_gmail_credentials(config)
    runtime = RuntimeState(
        config=config,
        client=OpenAI(api_key=config.openai_api_key),
        gmail_creds=gmail_creds,
        can_send=can_send_now(config, gmail_creds),
    )

    lock = TokenScopedLock(config.telegram_bot_token, config.lock_root)
    lock.acquire()
    LOGGER.info("Acquired token lock: %s", lock.path)

    try:
        run_bot(runtime, lock)
    finally:
        lock.release()
        LOGGER.info("Released token lock: %s", lock.path)


if __name__ == "__main__":
    main()
