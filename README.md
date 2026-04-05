# Stackfuse Email Maker

This project is now a webhook-driven Telegram bot for Cloudflare Workers.

## What the bot actually does

The original bot had one core job:

1. Accept rough outbound-email notes in Telegram.
2. Extract `TO:` if present, and otherwise let OpenAI infer a recipient email when the text includes one.
3. Ask OpenAI to reshape the notes into a structured JSON object that fits the Stackfuse email template.
4. Render that JSON into a fixed dark HTML template.
5. Build a multipart `.eml` draft with both plain-text and HTML parts.
6. Send that `.eml` back to the Telegram user as `stackfuse-email.eml`.

The Cloudflare rewrite preserves that flow, but changes the runtime model:

- No polling process.
- No Python runtime.
- No local lock files.
- Telegram now delivers updates to a Worker webhook.
- The Worker returns `200` immediately and finishes the email generation in background work.

## Current architecture

- [src/worker.mjs](/Users/mediaalamedia/stackfuse-email-maker/src/worker.mjs): Cloudflare Worker entrypoint and all runtime logic.
- [wrangler.jsonc](/Users/mediaalamedia/stackfuse-email-maker/wrangler.jsonc): Worker configuration.
- [tests/worker.test.mjs](/Users/mediaalamedia/stackfuse-email-maker/tests/worker.test.mjs): smoke tests for parsing, templating, and `.eml` generation.

## Runtime behavior

- `GET /`: status payload describing the service.
- `GET /health`: lightweight health check.
- `POST /webhook/telegram`: Telegram webhook endpoint protected by `X-Telegram-Bot-Api-Secret-Token`.

Supported Telegram interactions:

- `/start`: explains how to use the bot.
- Plain text message: generates and returns an `.eml` draft.

Not carried over:

- The old optional `Send now` flow. The previous implementation relied on SMTP or Gmail OAuth from a long-running Python process. That is not portable to Cloudflare Workers without a different mail-delivery integration.

## Required secrets

Configure these in Cloudflare as Worker secrets:

- `OPENAI_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`

Optional plain-text vars:

- `OPENAI_MODEL`
- `DEFAULT_FROM`

For local development, copy [.dev.vars.example](/Users/mediaalamedia/stackfuse-email-maker/.dev.vars.example) to `.dev.vars`.

## Local verification

```bash
node --test
```

## Deployment notes

The Worker is intended to run on `workers.dev` and receive Telegram webhooks directly. After deployment, Telegram should point to:

```text
https://<worker-name>.<workers-subdomain>.workers.dev/webhook/telegram
```

with the configured secret token.

## Sources used for the rewrite

- [Cloudflare Workers best practices](https://developers.cloudflare.com/workers/best-practices/workers-best-practices/)
- [Cloudflare Wrangler docs](https://developers.cloudflare.com/workers/wrangler/)
- [Telegram Bot API: setWebhook](https://core.telegram.org/bots/api#setwebhook)
- [OpenAI migration guide for Responses and structured output changes](https://developers.openai.com/api/docs/guides/migrate-to-responses)
