import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEmailMessage,
  buildPlainBody,
  extractAddresses,
  fillTemplate,
  looksLikeEmail,
  normalizeStructuredEmail,
  renderSectionsHtml,
  timingSafeEqual,
} from "../src/worker.mjs";

test("extractAddresses strips a TO header", () => {
  const result = extractAddresses("TO: client@example.com\n\nHello there");
  assert.equal(result.toAddress, "client@example.com");
  assert.equal(result.cleanedText, "Hello there");
});

test("looksLikeEmail validates basic addresses", () => {
  assert.equal(looksLikeEmail("person@example.com"), true);
  assert.equal(looksLikeEmail("not-an-email"), false);
});

test("normalizeStructuredEmail applies defaults", () => {
  const structured = normalizeStructuredEmail({
    subject: "Test",
    intro_paragraph: "Hi",
    sections: [{ title: "One", body: "Body" }],
  });

  assert.equal(structured.subject, "Test");
  assert.equal(structured.sender_name, "Stackfuse Team");
  assert.equal(structured.sections.length, 1);
});

test("buildPlainBody includes sections when present", () => {
  const body = buildPlainBody({
    intro_paragraph: "Hi",
    sections: [{ title: "One", body: "Body", metric_label: "ETA", metric_value: "2d" }],
  });

  assert.match(body, /Key points:/);
  assert.match(body, /One: Body \(ETA: 2d\)/);
});

test("renderSectionsHtml escapes content", () => {
  const html = renderSectionsHtml([{ title: "<One>", body: "Body & more" }]);
  assert.match(html, /&lt;One&gt;/);
  assert.match(html, /Body &amp; more/);
});

test("fillTemplate injects escaped structured content", () => {
  const html = fillTemplate(
    normalizeStructuredEmail({
      subject: "Subject",
      company_name: "ACME <Corp>",
      intro_paragraph: "Hi\nthere",
      closing_paragraph: "Thanks",
    }),
  );

  assert.match(html, /ACME &lt;Corp&gt;/);
  assert.match(html, /Hi<br \/>there/);
});

test("buildEmailMessage emits an RFC822 multipart message", () => {
  const bytes = buildEmailMessage({
    structured: normalizeStructuredEmail({
      subject: "Hello",
      intro_paragraph: "Hi",
      closing_paragraph: "Thanks",
    }),
    htmlBody: "<p>Hi</p>",
    plainBody: "Hi",
    toAddress: "client@example.com",
    fromAddress: "Stackfuse <contact@stackfuse.pro>",
  });

  const text = new TextDecoder().decode(bytes);
  assert.match(text, /Content-Type: multipart\/alternative;/);
  assert.match(text, /Subject: Hello/);
  assert.match(text, /To: client@example.com/);
});

test("timingSafeEqual matches equal strings and rejects different ones", () => {
  assert.equal(timingSafeEqual("abc", "abc"), true);
  assert.equal(timingSafeEqual("abc", "abd"), false);
});
