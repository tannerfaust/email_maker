const DEFAULT_OPENAI_MODEL = "gpt-5-mini-2025-08-07";
const DEFAULT_FROM = "Stackfuse <contact@stackfuse.pro>";
const TELEGRAM_WEBHOOK_PATH = "/webhook/telegram";
const TEMPLATE_HTML = `<!DOCTYPE html>
<html lang="en" style="margin:0; padding:0;">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{subject}}</title>
    <meta name="x-preheader" content="{{preheader}}" />
    <style>
      @media only screen and (max-width: 600px) {
        .container {
          width: 100% !important;
        }
        .inner {
          padding: 20px !important;
        }
        .stack-column,
        .stack-column td {
          display: block !important;
          width: 100% !important;
        }
        .module-rail {
          width: 100% !important;
          border-right: none !important;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        }
        .hero-title {
          font-size: 24px !important;
        }
        .hero-subtitle {
          font-size: 16px !important;
        }
      }
    </style>
  </head>
  <body
    style="
      margin: 0;
      padding: 0;
      background-color: #000000;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: #f3f3f3;
    "
  >
    <div
      style="
        display: none;
        font-size: 1px;
        line-height: 1px;
        max-height: 0;
        max-width: 0;
        opacity: 0;
        overflow: hidden;
        mso-hide: all;
        visibility: hidden;
      "
    >
      {{preheader}}
    </div>

    <table
      role="presentation"
      cellpadding="0"
      cellspacing="0"
      border="0"
      width="100%"
      style="
        background-color: #000000;
        background-image: radial-gradient(circle at top, rgba(52, 211, 153, 0.12), rgba(0, 0, 0, 0) 34%);
        padding: 24px 0;
      "
    >
      <tr>
        <td align="center">
          <table
            role="presentation"
            cellpadding="0"
            cellspacing="0"
            border="0"
            width="100%"
            class="container"
            style="
              max-width: 640px;
              width: 100%;
              border-radius: 24px;
              background: linear-gradient(180deg, rgba(9, 9, 9, 0.98), rgba(3, 3, 3, 0.98));
              border: 1px solid rgba(255, 255, 255, 0.1);
              box-shadow: 0 24px 64px rgba(0, 0, 0, 0.55);
              overflow: hidden;
            "
          >
            <tr>
              <td
                style="
                  height: 4px;
                  background: linear-gradient(90deg, rgba(120, 255, 170, 0.75), rgba(59, 130, 246, 0.28), rgba(255, 255, 255, 0));
                  font-size: 0;
                  line-height: 0;
                "
              >
                &nbsp;
              </td>
            </tr>
            <tr>
              <td
                style="
                  padding: 18px 28px 14px 28px;
                  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                  background: rgba(255, 255, 255, 0.01);
                "
              >
                <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                  <tr>
                    <td align="left">
                      <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                        <tr>
                          <td style="width: 24px; padding-right: 9px; vertical-align: middle;">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="471.98 357.24 979.74 1097.98" width="20" height="20" style="display:block;" aria-hidden="true">
                              <path fill="#f4f4f4" transform="scale(1.91211 1.91211)" d="M511.563 186.828C513.244 188.872 522.343 228.804 523.618 233.994L543.097 312.361L555.406 361.301C557.382 369.4 559.91 378.793 561.259 386.885C576.452 374.875 592.174 360.238 607.061 347.575L715.991 254.911C713.55 266.139 709.262 279.47 706.009 290.734L691.097 342.799C680.327 379.623 670.099 418.039 659.768 455.098C682.535 454.745 705.607 455.279 728.358 455.053C734.71 454.989 753.986 455.477 759.221 454.52C748.967 467.404 738.392 482.464 728.64 495.849L674.123 570.884C678.44 578.235 683.658 589.7 687.519 597.617C694.781 612.604 702.15 627.539 709.627 642.42C712.765 648.697 717.12 657.99 720.725 663.827C685.058 663.5 649.389 663.382 613.72 663.471C610.959 669.261 608.299 675.859 605.561 681.806L569.256 761.054C563.962 755.442 559.019 749.558 553.827 743.854L516.391 702.895C510.449 696.378 495.226 681.074 491.139 675.217C476.781 683.455 459.883 691.539 445.021 699.077L386.151 729.336L346.575 749.558C348.012 744.894 355.786 728.037 358.119 722.522L386.571 655.49L266.338 656.011C272.585 651.443 279.88 645.307 286.045 640.431L329.88 605.507C335.892 600.7 348.177 590.234 354.16 586.304L246.835 384.073C250.509 386.166 255.464 389.672 259.143 392.048L284.386 408.327L337.754 442.595C351.387 451.412 365.82 461.061 379.582 469.501C375.898 460.557 372.141 448.563 368.993 439.253C362.408 420.157 356.025 400.992 349.844 381.762L320.684 294.041C317.064 283.145 312.99 272.365 309.584 261.433C361.154 304.555 415.151 346.356 467.244 388.968C474.051 355.794 481.457 323.012 488.876 289.987C496.524 255.943 503.365 220.647 511.563 186.828Z"/>
                              <path fill="#0f0f0f" transform="scale(1.91211 1.91211)" d="M593.826 434.939L594.107 435.257C594.16 438.017 591.266 453.204 590.75 457.748C587.873 483.09 583.162 508.979 580.27 534.235L678.032 495.407C659.26 516.658 640.667 542.02 621.739 562.603C634.16 580.933 646.181 599.531 657.793 618.383C637.9 617.305 617.956 614.701 598.058 613.446C594.611 613.228 591.096 612.944 587.69 612.386C578.345 639.722 569.707 668.01 560.948 695.565C549.557 679.278 536.712 663.07 524.691 647.224C518.618 639.219 511.458 630.672 505.823 622.469L499.169 625.652C475.227 636.594 449.385 647.183 426.053 658.191C431.376 649.366 438.304 639.492 444.147 630.788L477.345 581.802C467.43 569.148 457.417 556.355 447.308 543.861C440.46 535.398 433.003 527.195 426.107 518.691C431.58 521.102 444.306 524.546 450.55 526.537C466.922 531.757 483.456 536.695 499.676 542.441C499.209 529.327 497.531 512.947 496.564 499.495C495.534 485.148 494.628 466.557 492.782 452.692C508.119 471.593 527.12 497.511 541.168 517.528C551.638 501.553 562 485.508 572.256 469.394C579.755 457.723 586.901 447.031 593.826 434.939Z"/>
                            </svg>
                          </td>
                          <td style="color:#f4f4f4; font-size:13px; font-weight:600; letter-spacing:0.03em;">
                            Stackfuse
                          </td>
                        </tr>
                      </table>
                    </td>
                    <td align="right" style="font-size:12px; color:#9a9a9a;">
                      For {{company_name}}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <tr>
              <td style="padding: 0 28px 8px 28px;">
                <p
                  style="
                    margin: 0;
                    font-size: 14px;
                    line-height: 1.75;
                    color: #d2d2d2;
                  "
                >
                  {{intro_paragraph}}
                </p>
              </td>
            </tr>

            <tr>
              <td style="padding: 12px 28px 4px 28px;">
                <div
                  style="
                    font-size: 14px;
                    line-height: 1.7;
                    color: #d2d2d2;
                  "
                >
                  {{sections_html}}
                </div>
              </td>
            </tr>

            <tr>
              <td style="padding: 8px 28px 4px 28px; font-size: 14px; line-height: 1.7; color: #d2d2d2;">
                If useful, just reply and we can take it from there.
              </td>
            </tr>

            <tr>
              <td style="padding: 14px 28px 20px 28px;">
                <p
                  style="
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    line-height: 1.7;
                    color: #d2d2d2;
                  "
                >
                  {{closing_paragraph}}
                </p>
                <p
                  style="
                    margin: 0;
                    font-size: 13px;
                    line-height: 1.7;
                    color: #9f9f9f;
                  "
                >
                  {{sender_name}}<br />
                  {{sender_role}}<br />
                  Stackfuse
                </p>
              </td>
            </tr>

            <tr>
              <td
                style="
                  padding: 14px 24px 18px 24px;
                  border-top: 1px solid rgba(255, 255, 255, 0.08);
                  background: rgba(255, 255, 255, 0.02);
                "
              >
                <table width="100%" cellpadding="0" cellspacing="0" role="presentation">
                  <tr>
                    <td
                      style="
                        font-size: 11px;
                        line-height: 1.6;
                        color: #777777;
                      "
                    >
                      {{footer_note}}
                    </td>
                    <td
                      align="right"
                      style="
                        font-size: 11px;
                        line-height: 1.6;
                        color: #6c6c6c;
                      "
                    >
                      <a
                        href="https://stackfuse.pro/"
                        style="
                          color: #c8c8c8;
                          text-decoration: none;
                          letter-spacing: 0.1em;
                          text-transform: uppercase;
                          font-family: 'IBM Plex Mono', 'SFMono-Regular', Consolas, monospace;
                        "
                      >
                        stackfuse.pro
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
`;

const START_MESSAGE =
  "Send me the rough text or notes for an email.\n\n" +
  "Include who it’s for (for example start with TO: client@company.com or say send to john@acme.com) and I’ll set the recipient in the .eml. " +
  "This Cloudflare version returns a ready-to-send .eml file through Telegram.";

export default {
  async fetch(request, env = {}, ctx) {
    try {
      return await handleRequest(request, env, ctx);
    } catch (error) {
      logJson("unhandled_request_error", {
        message: getErrorMessage(error),
        stack: error instanceof Error ? error.stack : undefined,
      });
      return jsonResponse(
        {
          ok: false,
          error: "internal_error",
        },
        500,
      );
    }
  },
};

async function handleRequest(request, env, ctx) {
  const url = new URL(request.url);

  if (request.method === "GET" && url.pathname === "/") {
    return jsonResponse({
      ok: true,
      service: "stackfuse-email-maker",
      mode: "telegram-webhook",
      webhook_path: TELEGRAM_WEBHOOK_PATH,
      openai_model: getOpenAIModel(env),
      send_now_supported: false,
    });
  }

  if (request.method === "GET" && url.pathname === "/health") {
    return jsonResponse({
      ok: true,
      service: "stackfuse-email-maker",
      version: "cloudflare-worker",
    });
  }

  if (request.method === "POST" && url.pathname === TELEGRAM_WEBHOOK_PATH) {
    try {
      await verifyTelegramWebhookSecret(request, env);
    } catch (error) {
      logJson("webhook_rejected", {
        message: getErrorMessage(error),
      });
      return new Response("Forbidden", { status: 403 });
    }
    const update = await request.json();
    ctx.waitUntil(processTelegramUpdate(update, env));
    return new Response("ok", { status: 200 });
  }

  return new Response("Not found", { status: 404 });
}

async function processTelegramUpdate(update, env) {
  try {
    const messageText = update?.message?.text;
    if (typeof messageText !== "string") {
      return;
    }

    const chatId = update.message.chat?.id;
    if (!chatId) {
      return;
    }

    if (messageText.trim().startsWith("/start")) {
      await sendTelegramTextMessage(env, chatId, START_MESSAGE);
      return;
    }

    await sendTelegramChatAction(env, chatId, "typing");

    const { cleanedText, toAddress: explicitToAddress } = extractAddresses(messageText);
    const sourceText = cleanedText || messageText;
    const structured = await callOpenAIForEmailStructuring(sourceText, env);
    const toAddress = looksLikeEmail(explicitToAddress)
      ? explicitToAddress
      : looksLikeEmail(structured.to_address)
        ? structured.to_address
        : "recipient@example.com";

    const htmlBody = fillTemplate(structured);
    const plainBody = buildPlainBody(structured);
    const emlBytes = buildEmailMessage({
      structured,
      htmlBody,
      plainBody,
      toAddress,
      fromAddress: getDefaultFrom(env),
    });

    await sendTelegramDocument(env, {
      chatId,
      filename: "stackfuse-email.eml",
      bytes: emlBytes,
      caption:
        "Use the attached .eml file in your mail client.\n\n" +
        `Subject: ${structured.subject}\nTo: ${toAddress}`,
    });

    logJson("email_generated", {
      chat_id: chatId,
      subject: structured.subject,
      to_address: toAddress,
    });
  } catch (error) {
    const chatId = update?.message?.chat?.id;
    if (chatId) {
      await sendTelegramTextMessage(
        env,
        chatId,
        "Something went wrong while generating the email.\n\n" +
          `${getErrorMessage(error)}\n\n` +
          "Please try again or simplify the input.",
      ).catch(() => undefined);
    }

    logJson("update_error", {
      update_id: update?.update_id,
      message: getErrorMessage(error),
      stack: error instanceof Error ? error.stack : undefined,
    });
  }
}

async function verifyTelegramWebhookSecret(request, env) {
  const expected = (env.TELEGRAM_WEBHOOK_SECRET || "").trim();
  if (!expected) {
    throw new Error("TELEGRAM_WEBHOOK_SECRET is not configured");
  }

  const actual = request.headers.get("X-Telegram-Bot-Api-Secret-Token") || "";
  if (!timingSafeEqual(actual, expected)) {
    throw new Error("Invalid Telegram webhook secret");
  }
}

async function callOpenAIForEmailStructuring(rawText, env) {
  const apiKey = (env.OPENAI_API_KEY || "").trim();
  if (!apiKey) {
    throw new Error("OPENAI_API_KEY is not configured");
  }

  const systemPrompt =
    "You are an expert email copy architect for Stackfuse, an AI automation agency " +
    "(https://stackfuse.pro/). Your job is to turn rough email notes into structured content " +
    "that will be inserted into a fixed HTML email template.\n\n" +
    "Below is the exact HTML template used for the email. It contains placeholders in double " +
    "curly braces (for example {{subject}}, {{intro_paragraph}}). You must produce a JSON object that, when " +
    "these placeholders are filled and sections are rendered as HTML blocks, results in a complete, client-ready email.\n\n" +
    "Placeholders you must fill via JSON:\n" +
    "- subject, preheader, company_name, tagline, hero_title, hero_subtitle\n" +
    "- intro_paragraph\n" +
    "- sections: array of { title, body, metric_label (optional), metric_value (optional) }\n" +
    "- cta_text, cta_url, closing_paragraph, sender_name, sender_role, footer_note\n" +
    "- to_address: if the user specifies a recipient email anywhere in the message, extract it; otherwise null.\n\n" +
    "Rules:\n" +
    "- Use plain text only in JSON string values.\n" +
    "- Tone: practical, concrete B2B outreach.\n" +
    "- Treat the user's text as the source of truth. Preserve structure, voice, and key sentences.\n" +
    "- Preserve at least 85-90% of the original wording unless a small cleanup materially improves readability.\n" +
    "- Allowed edits: grammar fixes, typo fixes, paragraph splitting, light repetition trimming.\n" +
    "- intro_paragraph should usually contain the greeting and the first one or two paragraphs.\n" +
    "- sections should be empty by default. Only use sections if the user clearly gave a list that should remain a list.\n" +
    "- Do not add new claims, buzzwords, fluff, or invented details.\n" +
    "- Do not add labels like To:, Brief:, Next step:, or similar markers.\n" +
    "- Output valid JSON only.\n\n" +
    "=== HTML TEMPLATE ===\n" +
    TEMPLATE_HTML +
    "\n=== END HTML TEMPLATE ===";

  const userPrompt =
    "Here is the raw email text or notes from the user. Structure it into the template " +
    "placeholders and return one JSON object with the schema described above.\n\n" +
    "=== USER EMAIL INPUT ===\n" +
    rawText.trim() +
    "\n=== END USER INPUT ===";

  const response = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: getOpenAIModel(env),
      store: false,
      response_format: { type: "json_object" },
      max_completion_tokens: 8192,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
    }),
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(
      `OpenAI request failed (${response.status}): ${payload?.error?.message || "unknown error"}`,
    );
  }

  const content = payload?.choices?.[0]?.message?.content;
  if (typeof content !== "string" || !content.trim()) {
    throw new Error("OpenAI returned empty content");
  }

  return normalizeStructuredEmail(JSON.parse(content));
}

function normalizeStructuredEmail(data) {
  const sections = Array.isArray(data?.sections)
    ? data.sections
        .map((item) => ({
          title: safeString(item?.title),
          body: safeString(item?.body),
          metric_label: optionalString(item?.metric_label),
          metric_value: optionalString(item?.metric_value),
        }))
        .filter((item) => item.title || item.body)
    : [];

  return {
    subject: safeString(data?.subject) || "Stackfuse update",
    preheader: safeString(data?.preheader),
    company_name: safeString(data?.company_name) || "Your Team",
    tagline: safeString(data?.tagline) || "Production AI Engineering",
    hero_title: safeString(data?.hero_title),
    hero_subtitle: safeString(data?.hero_subtitle),
    intro_paragraph: safeString(data?.intro_paragraph),
    sections,
    cta_text: safeString(data?.cta_text) || "Choose Your Path",
    cta_url: safeString(data?.cta_url) || "https://stackfuse.pro/start",
    closing_paragraph: safeString(data?.closing_paragraph),
    sender_name: safeString(data?.sender_name) || "Stackfuse Team",
    sender_role: safeString(data?.sender_role) || "Production AI Engineering",
    footer_note:
      safeString(data?.footer_note) ||
      "You’re receiving this because you asked about AI systems, automation, or workflow design with Stackfuse.",
    to_address: optionalString(data?.to_address),
  };
}

function fillTemplate(structured) {
  const replacements = {
    "{{subject}}": escapeHtml(structured.subject),
    "{{preheader}}": escapeHtml(structured.preheader),
    "{{company_name}}": escapeHtml(structured.company_name),
    "{{tagline}}": escapeHtml(structured.tagline),
    "{{hero_title}}": escapeHtml(structured.hero_title),
    "{{hero_subtitle}}": escapeHtml(structured.hero_subtitle),
    "{{intro_paragraph}}": renderMultilineText(structured.intro_paragraph),
    "{{sections_html}}": renderSectionsHtml(structured.sections),
    "{{cta_text}}": escapeHtml(structured.cta_text),
    "{{cta_url}}": escapeHtml(structured.cta_url),
    "{{closing_paragraph}}": renderMultilineText(structured.closing_paragraph),
    "{{sender_name}}": escapeHtml(structured.sender_name),
    "{{sender_role}}": escapeHtml(structured.sender_role),
    "{{footer_note}}": renderMultilineText(structured.footer_note),
  };

  let html = TEMPLATE_HTML;
  for (const [key, value] of Object.entries(replacements)) {
    html = html.replaceAll(key, value);
  }
  return html;
}

function renderSectionsHtml(sections) {
  if (!sections.length) {
    return "";
  }

  return sections
    .map((section) => {
      const metricSuffix =
        section.metric_label && section.metric_value
          ? ` (${escapeHtml(section.metric_label)}: ${escapeHtml(section.metric_value)})`
          : "";

      return (
        '<p style="margin: 0 0 14px 0; font-size: 14px; line-height: 1.7; color: #d2d2d2;">' +
        `<strong style="color: #f5f5f5;">${escapeHtml(section.title)}</strong><br />` +
        `${renderMultilineText(section.body)}${metricSuffix}` +
        "</p>"
      );
    })
    .join("\n");
}

function renderMultilineText(value) {
  return escapeHtml(value).replaceAll("\n", "<br />");
}

function buildPlainBody(structured) {
  let body = structured.intro_paragraph.trim();
  if (structured.sections.length) {
    const sectionLines = structured.sections.map((section) => {
      let line = `- ${section.title}: ${section.body}`;
      if (section.metric_label && section.metric_value) {
        line += ` (${section.metric_label}: ${section.metric_value})`;
      }
      return line;
    });
    body += `\n\nKey points:\n${sectionLines.join("\n")}`;
  }
  return body.trim();
}

function buildEmailMessage({ structured, htmlBody, plainBody, toAddress, fromAddress }) {
  const boundary = `cf-email-maker-${crypto.randomUUID()}`;
  const lines = [
    `Subject: ${encodeMimeHeader(structured.subject)}`,
    `To: ${toAddress}`,
    `From: ${fromAddress}`,
    `Date: ${formatRfc2822Date(new Date())}`,
    `Message-ID: <${crypto.randomUUID()}@stackfuse.pro>`,
    "MIME-Version: 1.0",
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    "",
    `--${boundary}`,
    "Content-Type: text/plain; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrapBase64(utf8Base64(plainBody)),
    `--${boundary}`,
    "Content-Type: text/html; charset=UTF-8",
    "Content-Transfer-Encoding: base64",
    "",
    wrapBase64(utf8Base64(htmlBody)),
    `--${boundary}--`,
    "",
  ];

  return new TextEncoder().encode(lines.join("\r\n"));
}

async function sendTelegramChatAction(env, chatId, action) {
  await callTelegramApi(env, "sendChatAction", {
    chat_id: String(chatId),
    action,
  });
}

async function sendTelegramTextMessage(env, chatId, text) {
  await callTelegramApi(env, "sendMessage", {
    chat_id: String(chatId),
    text,
  });
}

async function sendTelegramDocument(env, { chatId, filename, bytes, caption }) {
  const formData = new FormData();
  formData.set("chat_id", String(chatId));
  formData.set("caption", caption.slice(0, 1024));
  formData.set("document", new Blob([bytes], { type: "message/rfc822" }), filename);

  await callTelegramApi(env, "sendDocument", formData, true);
}

async function callTelegramApi(env, method, payload, isFormData = false) {
  const token = (env.TELEGRAM_BOT_TOKEN || "").trim();
  if (!token) {
    throw new Error("TELEGRAM_BOT_TOKEN is not configured");
  }

  const response = await fetch(`https://api.telegram.org/bot${token}/${method}`, {
    method: "POST",
    headers: isFormData ? undefined : { "Content-Type": "application/json" },
    body: isFormData ? payload : JSON.stringify(payload),
  });

  const result = await response.json();
  if (!response.ok || result?.ok === false) {
    throw new Error(`Telegram ${method} failed: ${result?.description || response.status}`);
  }
  return result;
}

function extractAddresses(rawText) {
  const lines = rawText.split(/\r?\n/);
  let toAddress = null;
  const remainingLines = [];

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.toUpperCase().startsWith("TO:")) {
      const maybe = stripped.slice(3).trim();
      if (looksLikeEmail(maybe)) {
        toAddress = maybe;
      }
      continue;
    }
    remainingLines.push(line);
  }

  return {
    cleanedText: remainingLines.join("\n").trim(),
    toAddress,
  };
}

function looksLikeEmail(value) {
  return typeof value === "string" && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length < 256;
}

function safeString(value) {
  return typeof value === "string" ? value.trim() : "";
}

function optionalString(value) {
  const normalized = safeString(value);
  return normalized || null;
}

function escapeHtml(value) {
  return safeString(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function encodeMimeHeader(value) {
  if (/^[\x20-\x7E]*$/.test(value)) {
    return value;
  }
  return `=?UTF-8?B?${utf8Base64(value)}?=`;
}

function utf8Base64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) {
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  }
  return btoa(binary);
}

function wrapBase64(value, width = 76) {
  const lines = [];
  for (let index = 0; index < value.length; index += width) {
    lines.push(value.slice(index, index + width));
  }
  return lines.join("\r\n");
}

function timingSafeEqual(left, right) {
  const encoder = new TextEncoder();
  const leftBytes = encoder.encode(left);
  const rightBytes = encoder.encode(right);
  const maxLength = Math.max(leftBytes.length, rightBytes.length);
  let mismatch = leftBytes.length ^ rightBytes.length;

  for (let index = 0; index < maxLength; index += 1) {
    mismatch |= (leftBytes[index] || 0) ^ (rightBytes[index] || 0);
  }

  return mismatch === 0;
}

function formatRfc2822Date(date) {
  return date.toUTCString().replace("GMT", "+0000");
}

function getOpenAIModel(env = {}) {
  return (env.OPENAI_MODEL || "").trim() || DEFAULT_OPENAI_MODEL;
}

function getDefaultFrom(env = {}) {
  return (env.DEFAULT_FROM || "").trim() || DEFAULT_FROM;
}

function getErrorMessage(error) {
  if (error instanceof Error && error.message) {
    return error.message;
  }
  if (typeof error === "string") {
    return error;
  }
  return "Unknown error";
}

function logJson(event, data) {
  console.log(JSON.stringify({ event, ...data }));
}

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload, null, 2), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
    },
  });
}

export {
  TELEGRAM_WEBHOOK_PATH,
  buildEmailMessage,
  buildPlainBody,
  escapeHtml,
  extractAddresses,
  fillTemplate,
  formatRfc2822Date,
  looksLikeEmail,
  normalizeStructuredEmail,
  renderSectionsHtml,
  timingSafeEqual,
};
