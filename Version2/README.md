## Stackfuse Email Maker - Version2

This is a hardened rewrite focused on reliability and startup safety.

### Why this version is safer

- Token-scoped process lock in `/tmp/stackfuse-email-maker-locks/...`.
  - Prevents two local instances from using the same Telegram token at once.
- Startup webhook cleanup (`delete_webhook(drop_pending_updates=True)`) before polling.
- Explicit conflict diagnostics if Telegram reports another `getUpdates` consumer.
- Better runtime logging and `/health` command.
- OpenAI call retries for transient failures.
- HTML escaping for injected template fields.

---

### 1. Setup

```bash
cd Version2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` with your keys.

---

### 2. Run

```bash
cd Version2
source .venv/bin/activate
python3 bot.py
```

In Telegram:

1. Send `/start`
2. Send your rough email notes
3. (Optional) Include recipient as first line: `TO: client@company.com`

---

### 3. Health check

Send `/health` to the bot.

It returns:

- PID
- active model
- lock file path

---

### 4. If you still get conflict

Conflict means another process (local or remote machine) is still polling the same token.

Local cleanup command:

```bash
pkill -f "/Users/mediaalamedia/stackfuse-email-maker"
```

Then run Version2 again.

If conflict persists after local cleanup, another machine/environment is running with the same bot token.

---

### 5. Send now support

`Send now` appears when either is configured:

- Gmail OAuth (`gmail_token.json` generated via `google_oauth_login.py`)
- SMTP (`SMTP_*` vars in `.env`)

Otherwise the bot still returns a valid `.eml` file.

---

### 6. Files

- `bot.py` - hardened runtime bot
- `email_template.html` - HTML template
- `google_oauth_login.py` - one-time Gmail OAuth helper
- `requirements.txt`
- `.env.example`
