import test from "node:test";
import assert from "node:assert/strict";

import {
  buildEmailMessage,
  buildPreservedEmail,
  buildPlainBody,
  extractAddresses,
  extractHeuristicMetadata,
  fillTemplate,
  inferCompanyNameFromText,
  looksLikeEmail,
  parseBodyBlocks,
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

test("inferCompanyNameFromText strips team suffix from greeting", () => {
  assert.equal(inferCompanyNameFromText("Hi X-Hunter team,\n\nBody"), "X-Hunter");
});

test("extractHeuristicMetadata finds company and email", () => {
  const metadata = extractHeuristicMetadata("TO: test@example.com\n\nHi X-Hunter team,\n\nBody");
  assert.equal(metadata.company_name, "X-Hunter");
  assert.equal(metadata.to_address, "test@example.com");
});

test("extractHeuristicMetadata infers company from a domain mention in the body", () => {
  const metadata = extractHeuristicMetadata(
    "Hello team,\n\nPavegen already looks interesting.\n\nPavegen also mentions analytics publicly. ([pavegen.com][1])",
  );
  assert.equal(metadata.company_name, "Pavegen");
});

test("parseBodyBlocks preserves heading and following paragraph as a section", () => {
  const blocks = parseBodyBlocks("Hi X-Hunter team,\n\nBuild a free prototype\n\nCreate product videos.");
  assert.deepEqual(blocks[0], { type: "paragraph", text: "Hi X-Hunter team," });
  assert.deepEqual(blocks[1], {
    type: "section",
    title: "Build a free prototype",
    body: "Create product videos.",
  });
});

test("buildPreservedEmail keeps the original body text unchanged", () => {
  const rawText = "Hi X-Hunter team,\n\nParagraph one.\n\nBuild a free prototype\n\nCreate product videos.";
  const structured = buildPreservedEmail(rawText, { company_name: "X-Hunter" });
  assert.equal(structured.body_text, rawText);
  assert.equal(structured.company_name, "X-Hunter");
  assert.equal(structured.subject, "For X-Hunter");
});

test("buildPlainBody returns the exact preserved body text", () => {
  const rawText = "Hi X-Hunter team,\n\nParagraph one.";
  const structured = buildPreservedEmail(rawText, { company_name: "X-Hunter" });
  assert.equal(buildPlainBody(structured), rawText);
});

test("fillTemplate injects escaped company name and preserved body html", () => {
  const html = fillTemplate(buildPreservedEmail("Hi\nthere", { company_name: "ACME <Corp>" }));

  assert.match(html, /ACME &lt;Corp&gt;/);
  assert.match(html, /Hi<br \/>there/);
});

test("buildEmailMessage emits an RFC822 multipart message", () => {
  const bytes = buildEmailMessage({
    structured: buildPreservedEmail("Hi", { company_name: "X-Hunter" }),
    htmlBody: "<p>Hi</p>",
    plainBody: "Hi",
    toAddress: "client@example.com",
    fromAddress: "Stackfuse <contact@stackfuse.pro>",
  });

  const text = new TextDecoder().decode(bytes);
  assert.match(text, /Content-Type: multipart\/alternative;/);
  assert.match(text, /Subject: For X-Hunter/);
  assert.match(text, /To: client@example.com/);
});

test("timingSafeEqual matches equal strings and rejects different ones", () => {
  assert.equal(timingSafeEqual("abc", "abc"), true);
  assert.equal(timingSafeEqual("abc", "abd"), false);
});
