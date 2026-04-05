#!/usr/bin/env python3
"""
One-time "Sign in with Google" to send email via Gmail API (no app password).

1. Go to https://console.cloud.google.com/
2. Create or select a project → APIs & Services → Enable "Gmail API"
3. APIs & Services → Credentials → Create credentials → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download the JSON and save as credentials.json in this folder
4. Run: python google_oauth_login.py
5. Browser opens → Sign in with Google → allow Gmail send access
6. Token is saved as gmail_token.json; the bot will use it for "Send now".
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_PATH = os.path.join(SCRIPT_DIR, "gmail_token.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def main() -> None:
    if not os.path.isfile(CREDENTIALS_PATH):
        print("Missing credentials.json")
        print("Download it from Google Cloud Console: Create OAuth 2.0 Client ID (Desktop app), then save as credentials.json here.")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"Saved token to {TOKEN_PATH}")
    print("You can now run the bot; 'Send now' will use Gmail (Sign in with Google).")


if __name__ == "__main__":
    main()
