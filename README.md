## Stackfuse Email Maker

**Goal**: Turn rough email notes into a beautiful, Stackfuse-style HTML email and return a ready-to-send `.eml` file via a Telegram bot.

The bot:

- Uses **OpenAI** to structure your free-form notes into a clean B2B email.
- Fills a dark, product-grade HTML template inspired by [`stackfuse.pro`](https://stackfuse.pro/).
- Sends you a `.eml` file that you can open in your email client or sending system.

---

### 1. Setup

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate  # on macOS / Linux
# .venv\Scripts\activate   # on Windows (PowerShell / CMD)

pip install -r requirements.txt
```

Create a `.env` file next to `bot.py`:

```bash
OPENAI_API_KEY=sk-your-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token

# Optional: override the default OpenAI model
# e.g. OPENAI_MODEL=gpt-5-mini  (or your actual model name)
OPENAI_MODEL=gpt-4.1-mini
```

The code uses `OPENAI_MODEL` if set, otherwise falls back to `gpt-4.1-mini`.  
You can point it at any compatible model you have access to (including your `gpt-5 mini`).

---

### 2. Run the bot

```bash
python bot.py
```

In Telegram:

1. Open your bot (created via BotFather) and send `/start`.
2. Then send your email notes as a normal message.

You can optionally specify addresses at the top:

```text
TO: client@company.com
FROM: you@stackfuse.pro

Here are my notes for the email...
- Explain what we do
- Mention we can help scope AI projects
- Ask for a 30-minute call next week
```

The bot will:

- Call OpenAI to turn this into a structured, Stackfuse-style email.
- Fill the HTML template in `email_template.html`.
- Build a MIME email with both plain text and HTML.
- Send back `stackfuse-email.eml` as a document attachment.

---

### 3. Manually sending the .eml (no setup)

You don’t have to use “Send now”. To send the email yourself:

1. **Save the .eml file** from Telegram to your Mac/PC.
2. **Desktop mail app (e.g. Apple Mail, Thunderbird, Outlook):**  
   Drag the `.eml` file into the **Drafts** folder (or use File → Import if your app has it). Open the new draft — To and Subject are already set — then click **Send**.
3. **Zoho Mail (web):** Open Zoho Mail in the browser, start a **new message**, set To and Subject to match the .eml. Then open the .eml file in a text editor or in Apple Mail, copy the HTML/body content, and paste into the new Zoho message (or attach the .eml and send — the recipient will get the email; some clients show it as a normal message).

So: either use a desktop client and **drag .eml into Drafts → open draft → Send**, or in Zoho compose a new email and copy over To/Subject/body (or attach the .eml).

---

### 4. Send now from contact@stackfuse.pro (Zoho)

To get a **Send now** button so the bot sends from **contact@stackfuse.pro** (Zoho Mail):

1. In `.env`, set your Zoho password (the one you use to sign in at Zoho Mail):
   ```bash
   DEFAULT_FROM=Stackfuse <contact@stackfuse.pro>
   SMTP_HOST=smtppro.zoho.com
   SMTP_PORT=587
   SMTP_USER=contact@stackfuse.pro
   SMTP_PASSWORD=your-zoho-password
   SMTP_USE_TLS=true
   ```
2. Custom-domain Zoho often uses **smtppro.zoho.com**. If send fails, try **smtp.zoho.com** for `SMTP_HOST`.
3. Restart the bot. When you generate an email, tap **Send now** — it will send from contact@stackfuse.pro.

---

### 5. Send now with Gmail (Sign in with Google)

To get a **Send now** button in Telegram so the bot sends the email for you:

**Option A — Sign in with Google (recommended)**  
No app password; uses Google’s recommended OAuth flow.

1. [Google Cloud Console](https://console.cloud.google.com/) → create/select project → **APIs & Services** → **Enable "Gmail API"**.
2. **Credentials** → **Create credentials** → **OAuth 2.0 Client ID** → Application type: **Desktop app** → Create.
3. Download the client JSON and save it as `credentials.json` in this project folder.
4. Run once:
   ```bash
   python google_oauth_login.py
   ```
5. Your browser opens → **Sign in with Google** → allow “Send email on your behalf”. Token is saved as `gmail_token.json`.
6. Restart the bot. When you generate an email, tap **Send now** — the email is sent from your Gmail via the API.

---

### 6. Customizing the template

- Edit `email_template.html` to tweak:
  - Colors, typography, spacing.
  - Copy blocks (e.g. tagline, footer text).
- Keep the placeholders like `{{hero_title}}`, `{{sections_html}}`, etc. — these are filled by `bot.py`.

If you want different structures (e.g. more sections, another CTA), you can:

- Update the JSON schema in `call_openai_for_email_structuring`.
- Update how sections are rendered in `render_sections_html`.
- Add new placeholders in the HTML and the `fill_template` replacement map.

---

### 7. Production notes

- For production, you may want to:
  - Run the bot on a small VM or container with a process supervisor.
  - Restrict access to the bot username so only your team can use it.
  - Log prompts / outputs (with PII care) to refine tone and structure.

For now, you can treat this as your internal **email composer copilot** that always matches the Stackfuse visual style.

