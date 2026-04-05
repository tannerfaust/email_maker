import base64
import atexit
import json
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid
from io import BytesIO
from typing import List, Optional

import fcntl
from dotenv import load_dotenv
from openai import OpenAI
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini-2025-08-07")
# Sender address (used for .eml and Send now). Default: contact@stackfuse.pro.
DEFAULT_FROM = os.getenv("DEFAULT_FROM", "").strip() or "Stackfuse <contact@stackfuse.pro>"

# Optional: SMTP so the bot can send the email for you (no .eml to open). If set, we show a "Send now" button.
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")

# Optional: Gmail API with "Sign in with Google" (OAuth). No app password needed.
GMAIL_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "gmail_token.json")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()

def _gmail_credentials():
    """Return Gmail API credentials from token file or from env (refresh_token)."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        return None
    if os.path.isfile(GMAIL_TOKEN_PATH):
        try:
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, scopes=["https://www.googleapis.com/auth/gmail.send"])
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return creds if (creds and creds.valid) else None
        except Exception:
            pass
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GMAIL_REFRESH_TOKEN:
        try:
            return Credentials(
                token=None,
                refresh_token=GMAIL_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=GOOGLE_CLIENT_ID,
                client_secret=GOOGLE_CLIENT_SECRET,
                scopes=["https://www.googleapis.com/auth/gmail.send"],
            )
        except Exception:
            pass
    return None

GMAIL_CREDS = _gmail_credentials()
CAN_SEND = bool(SMTP_HOST and SMTP_USER and SMTP_PASSWORD) or bool(GMAIL_CREDS)


if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is required.")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is required.")


client = OpenAI(api_key=OPENAI_API_KEY)


TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "email_template.html")
LOCK_PATH = os.path.join(os.path.dirname(__file__), ".bot.lock")


class SingleInstanceLock:
    def __init__(self, path: str):
        self.path = path
        self.handle = None

    def acquire(self) -> None:
        self.handle = open(self.path, "a+", encoding="utf-8")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.seek(0)
            owner = self.handle.read().strip() or "unknown"
            raise RuntimeError(
                "Another bot instance is already running. "
                f"Lock file: {self.path}. "
                f"Recorded owner PID: {owner}."
            ) from exc

        self.handle.seek(0)
        self.handle.truncate()
        self.handle.write(str(os.getpid()))
        self.handle.flush()
        atexit.register(self.release)

    def release(self) -> None:
        if not self.handle:
            return
        try:
            self.handle.seek(0)
            self.handle.truncate()
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


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
    to_address: Optional[str] = None  # recipient email extracted by GPT from the message


def load_template() -> str:
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def render_sections_html(sections: List[EmailSection]) -> str:
    if not sections:
        return ""

    blocks: List[str] = []

    for section in sections:
        metric_suffix = ""
        if section.metric_label and section.metric_value:
            metric_suffix = f" ({section.metric_label}: {section.metric_value})"

        blocks.append(
            f"""
            <p style="margin: 0 0 14px 0; font-size: 14px; line-height: 1.7; color: #d2d2d2;">
              <strong style="color: #f5f5f5;">{section.title}</strong><br />
              {section.body}{metric_suffix}
            </p>
            """
        )

    return "\n".join(blocks)


def fill_template(structured: StructuredEmail) -> str:
    template = load_template()
    sections_html = render_sections_html(structured.sections)

    replacements = {
        "{{subject}}": structured.subject,
        "{{preheader}}": structured.preheader,
        "{{company_name}}": structured.company_name,
        "{{tagline}}": structured.tagline,
        "{{hero_title}}": structured.hero_title,
        "{{hero_subtitle}}": structured.hero_subtitle,
        "{{intro_paragraph}}": structured.intro_paragraph,
        "{{sections_html}}": sections_html,
        "{{cta_text}}": structured.cta_text,
        "{{cta_url}}": structured.cta_url,
        "{{closing_paragraph}}": structured.closing_paragraph,
        "{{sender_name}}": structured.sender_name,
        "{{sender_role}}": structured.sender_role,
        "{{footer_note}}": structured.footer_note,
    }

    html = template
    for key, value in replacements.items():
        html = html.replace(key, value or "")

    return html


def build_email_message(
    structured: StructuredEmail,
    html_body: str,
    to_address: str,
    from_address: Optional[str] = None,
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = structured.subject
    msg["To"] = to_address
    # Always set From so the .eml opens as a draft (not as a forwarded message). Use DEFAULT_FROM or placeholder.
    msg["From"] = from_address or DEFAULT_FROM
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="stackfuse.pro")

    # Plain-text fallback for clients that don't support HTML
    plain_intro = structured.intro_paragraph
    if structured.sections:
        plain_intro += "\n\nKey points:\n"
        for section in structured.sections:
            line = f"- {section.title}: {section.body}"
            if section.metric_label and section.metric_value:
                line += f" ({section.metric_label}: {section.metric_value})"
            plain_intro += f"{line}\n"

    msg.set_content(plain_intro.strip())
    msg.add_alternative(html_body, subtype="html")
    return msg


def send_email_via_smtp(
    to_address: str,
    subject: str,
    html_body: str,
    plain_body: str,
    from_address: str,
) -> None:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg["Date"] = formatdate(localtime=True)
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        if SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASSWORD)
        smtp.send_message(msg)


def send_email_via_gmail(
    to_address: str,
    subject: str,
    html_body: str,
    plain_body: str,
    from_address: str,
) -> None:
    """Send using Gmail API (Sign in with Google)."""
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = GMAIL_CREDS
    if not creds:
        raise RuntimeError("Gmail credentials not configured")
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


def parse_structured_email(json_str: str) -> StructuredEmail:
    data = json.loads(json_str)

    sections_data = data.get("sections", []) or []
    sections: List[EmailSection] = []
    for item in sections_data:
        sections.append(
            EmailSection(
                title=item.get("title", "").strip(),
                body=item.get("body", "").strip(),
                metric_label=(item.get("metric_label") or "").strip() or None,
                metric_value=(item.get("metric_value") or "").strip() or None,
            )
        )

    to_addr = (data.get("to_address") or "").strip() or None
    return StructuredEmail(
        subject=data.get("subject", "").strip(),
        preheader=data.get("preheader", "").strip(),
        company_name=data.get("company_name", "Your Team").strip(),
        tagline=data.get("tagline", "Production AI Engineering").strip(),
        hero_title=data.get("hero_title", "").strip(),
        hero_subtitle=data.get("hero_subtitle", "").strip(),
        intro_paragraph=data.get("intro_paragraph", "").strip(),
        sections=sections,
        cta_text=data.get("cta_text", "Choose Your Path").strip(),
        cta_url=data.get("cta_url", "https://stackfuse.pro/start").strip(),
        closing_paragraph=data.get("closing_paragraph", "").strip(),
        sender_name=data.get("sender_name", "Stackfuse Team").strip(),
        sender_role=data.get("sender_role", "Production AI Engineering").strip(),
        footer_note=data.get(
            "footer_note",
            "You’re receiving this because you asked about AI systems, automation, or workflow design with Stackfuse.",
        ).strip(),
        to_address=to_addr,
    )


def call_openai_for_email_structuring(raw_text: str) -> StructuredEmail:
    """
    Send the HTML template as the instruction to OpenAI, plus the user's email text.
    Model returns JSON that we use to fill the template and build the .eml.
    """
    template_html = load_template()

    system_prompt = (
        "You are an expert email copy architect for Stackfuse, an AI automation agency "
        "(https://stackfuse.pro/). Your job is to turn rough email notes into structured content "
        "that will be inserted into a fixed HTML email template.\n\n"
        "Below is the exact HTML template used for the email. It contains placeholders in double "
        "curly braces (e.g. {{subject}}, {{hero_title}}). You must produce a JSON object that, when "
        "these placeholders are filled (and 'sections' rendered as HTML from your sections array), "
        "results in a complete, client-ready email.\n\n"
        "Placeholders you must fill via your JSON:\n"
        "- subject, preheader, company_name, tagline, hero_title, hero_subtitle\n"
        "- intro_paragraph\n"
        "- sections: array of { title, body, metric_label (optional), metric_value (optional) }\n"
        "- cta_text, cta_url, closing_paragraph, sender_name, sender_role, footer_note\n"
        "- to_address: if the user specifies a recipient email (e.g. 'send to john@acme.com', 'for client@x.com', or just an email in the message), extract it and set to_address to that email; otherwise null.\n\n"
        "Rules:\n"
        "- Use plain text only (no markdown, no HTML in your strings).\n"
        "- Tone: practical, concrete B2B outreach (like a thoughtful cold email).\n"
        "- tagline must be short and punchy: 2-6 words max.\n"
        "- Treat the user's text as the source of truth. Keep their structure, voice, and key sentences.\n"
        "- By default, preserve at least 85-90% of the original wording.\n"
        "- Only allowed edits:\n"
        "  * fix obvious grammar/typos,\n"
        "  * split into paragraphs where it helps readability,\n"
        "  * very light trimming of repetition.\n"
        "- intro_paragraph should usually start with the greeting (e.g. 'Hi {company_name} team,') and first 1–2 paragraphs.\n"
        "- sections should be empty by default. Only use sections if the user explicitly provides a list that should stay a list.\n"
        "- Do NOT add marketing fluff, buzzwords, extra claims, or new ideas not present in user input.\n"
        "- Do NOT add extra headers, labels, or formatting markers like 'To:', 'For:', 'Brief:', 'Next step:', etc.\n"
        "- Output valid JSON only.\n\n"
        "=== HTML TEMPLATE (instruction) ===\n"
        f"{template_html}\n"
        "=== END HTML TEMPLATE ==="
    )

    user_prompt = (
        "Here is the raw email text / notes from the user. Structure it into the template "
        "placeholders and return a single JSON object with the schema described above.\n\n"
        "=== USER EMAIL INPUT ===\n"
        f"{raw_text.strip()}\n"
        "=== END USER INPUT ==="
    )

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        max_completion_tokens=8192,
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned empty content")
    return parse_structured_email(content.strip())


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Send me the rough text or notes for an email.\n\n"
        "Include who it’s for (e.g. start with TO: client@company.com or say “send to john@acme.com”) and I’ll set the recipient in the .eml. "
        "Use 'Sign in with Google' once (run google_oauth_login.py) or set SMTP in .env to get a Send now button; otherwise I'll send an .eml."
    )
    await update.message.reply_text(text)


def _looks_like_email(s: str) -> bool:
    return "@" in s and "." in s and len(s) < 256


def extract_addresses(raw_text: str) -> tuple[str, Optional[str]]:
    """
    Parse optional TO: line at the top of the message.
    Returns (cleaned_text_without_headers, to_address or None).
    """
    lines = raw_text.splitlines()
    to_address: Optional[str] = None
    remaining_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("TO:"):
            maybe = stripped[3:].strip()
            if maybe and _looks_like_email(maybe):
                to_address = maybe
        else:
            remaining_lines.append(line)

    cleaned_text = "\n".join(remaining_lines).strip()
    return cleaned_text, to_address


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    raw_text = update.message.text
    await update.message.reply_chat_action("typing")

    cleaned_text, parsed_to = extract_addresses(raw_text)
    if not cleaned_text:
        cleaned_text = raw_text

    try:
        structured = call_openai_for_email_structuring(cleaned_text)
        # To: use explicit TO: line first, then GPT-extracted to_address, else placeholder
        to_address = parsed_to or structured.to_address
        if not to_address or not _looks_like_email(to_address):
            to_address = "recipient@example.com"

        html_body = fill_template(structured)
        msg = build_email_message(structured, html_body, to_address=to_address, from_address=None)

        plain_body = structured.intro_paragraph
        if structured.sections:
            plain_body += "\n\nKey points:\n"
            for section in structured.sections:
                line = f"- {section.title}: {section.body}"
                if section.metric_label and section.metric_value:
                    line += f" ({section.metric_label}: {section.metric_value})"
                plain_body += f"{line}\n"
        plain_body = plain_body.strip()

        if update.effective_user:
            context.user_data["last_email"] = {
                "to": to_address,
                "subject": structured.subject,
                "html": html_body,
                "plain": plain_body,
                "from": DEFAULT_FROM,
            }

        eml_bytes = msg.as_bytes()
        buffer = BytesIO(eml_bytes)
        buffer.name = "stackfuse-email.eml"

        preview = f"Subject: {structured.subject}\nTo: {to_address}"

        if CAN_SEND:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Send now", callback_data="send_now")],
            ])
            await update.message.reply_document(
                document=InputFile(buffer),
                caption=(
                    "You can download the .eml or tap Send now to send this email from the bot.\n\n"
                    f"{preview}"
                ),
                reply_markup=keyboard,
            )
        else:
            await update.message.reply_document(
                document=InputFile(buffer),
                caption=(
                    "Run 'Sign in with Google' once (see README) or set SMTP in .env to get a Send now button. "
                    "Otherwise use the .eml (e.g. drag into Drafts).\n\n"
                    f"{preview}"
                ),
            )
    except Exception as e:
        await update.message.reply_text(
            f"Something went wrong while generating the email:\n{e}\n\n"
            "Please try again or simplify the input."
        )


async def handle_send_now(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or query.data != "send_now":
        return
    await query.answer()

    payload = (context.user_data or {}).get("last_email")
    if not payload:
        await query.edit_message_caption(caption="No email to send. Generate one first by sending your email text.")
        return

    try:
        if GMAIL_CREDS:
            send_email_via_gmail(
                to_address=payload["to"],
                subject=payload["subject"],
                html_body=payload["html"],
                plain_body=payload["plain"],
                from_address=payload["from"],
            )
        elif SMTP_HOST and SMTP_USER and SMTP_PASSWORD:
            send_email_via_smtp(
                to_address=payload["to"],
                subject=payload["subject"],
                html_body=payload["html"],
                plain_body=payload["plain"],
                from_address=payload["from"],
            )
        else:
            await query.edit_message_caption(caption="No send method configured (Gmail OAuth or SMTP).", reply_markup=None)
            return
        await query.edit_message_caption(caption=f"Sent to {payload['to']}.", reply_markup=None)
    except Exception as e:
        await query.edit_message_caption(caption=f"Send failed: {e}", reply_markup=None)


def main() -> None:
    lock = SingleInstanceLock(LOCK_PATH)
    lock.acquire()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_send_now, pattern="^send_now$"))

    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        lock.release()


if __name__ == "__main__":
    main()
