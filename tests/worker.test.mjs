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
  renderBodyHtml,
  resolveToAddress,
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
  assert.deepEqual(blocks[0], { type: "greeting", text: "Hi X-Hunter team," });
  assert.deepEqual(blocks[1], {
    type: "section",
    title: "Build a free prototype",
    body: "Create product videos.",
  });
});

test("parseBodyBlocks detects a closing signature block", () => {
  const blocks = parseBodyBlocks("Hello team,\n\nBody paragraph.\n\nBest,\nAlex Rivera\nProduct & AI Strategist\nStackfuse");
  assert.deepEqual(blocks[2], {
    type: "signature",
    lines: ["Best,", "Alex Rivera", "Product & AI Strategist", "Stackfuse"],
  });
});

test("parseBodyBlocks separates greeting and list-style lines from telegram-style input", () => {
  const blocks = parseBodyBlocks(
    "Hi Standert team,\nLooking at your site, I noticed a clear opportunity.\nImagine AI-generated videos.\n\nTo make it concrete, we can:\n\nBuild a free prototype with product videos and 360° views\nSet up an AI assistant tailored to your catalog\nRun a free automation audit to streamline operations\nEven a rough prototype makes it easy to see the impact.\n—Alex",
  );

  assert.deepEqual(blocks[0], { type: "greeting", text: "Hi Standert team," });
  assert.deepEqual(blocks[1], { type: "paragraph", text: "Looking at your site, I noticed a clear opportunity." });
  assert.deepEqual(blocks[2], { type: "paragraph", text: "Imagine AI-generated videos." });
  assert.deepEqual(blocks[3], { type: "paragraph", text: "To make it concrete, we can:" });
  assert.deepEqual(blocks[4], {
    type: "paragraph",
    text:
      "Build a free prototype with product videos and 360° views\nSet up an AI assistant tailored to your catalog\nRun a free automation audit to streamline operations",
  });
  assert.deepEqual(blocks[5], {
    type: "paragraph",
    text: "Even a rough prototype makes it easy to see the impact.",
  });
  assert.deepEqual(blocks[6], {
    type: "signature",
    lines: ["—Alex"],
  });
});

test("buildPreservedEmail keeps the original body text unchanged", () => {
  const rawText = "Hi X-Hunter team,\n\nParagraph one.\n\nBuild a free prototype\n\nCreate product videos.";
  const structured = buildPreservedEmail(rawText, { company_name: "X-Hunter" });
  assert.equal(structured.body_text, rawText);
  assert.equal(structured.company_name, "X-Hunter");
  assert.equal(structured.subject, "For X-Hunter");
});

test("resolveToAddress prefers explicit valid email, then structured fallback", () => {
  assert.equal(resolveToAddress("client@example.com", "other@example.com"), "client@example.com");
  assert.equal(resolveToAddress(null, "other@example.com"), "other@example.com");
  assert.equal(resolveToAddress("not-an-email", null), "recipient@example.com");
});

test("buildPlainBody returns the exact preserved body text", () => {
  const rawText = "Hi X-Hunter team,\n\nParagraph one.";
  const structured = buildPreservedEmail(rawText, { company_name: "X-Hunter" });
  assert.equal(buildPlainBody(structured), rawText);
});

test("fillTemplate injects escaped company name and preserved body html", () => {
  const html = fillTemplate(buildPreservedEmail("Line one\nline two", { company_name: "ACME <Corp>" }));

  assert.match(html, /ACME &lt;Corp&gt;/);
  assert.match(html, /Line one<br \/>line two/);
});

test("renderBodyHtml adds light structure for greeting, sections, and signature", () => {
  const html = renderBodyHtml(
    "Hello team,\n\nBuild a free prototype\n\nCreate product videos.\n\nBest,\nAlex Rivera\nStackfuse",
  );

  assert.match(html, /border-bottom: 1px solid rgba\(255, 255, 255, 0.08\)/);
  assert.match(html, /border-top: 1px solid rgba\(255, 255, 255, 0.06\)/);
  assert.match(html, /font-weight: 700;[^>]*>Alex Rivera<\/p>/);
});

test("renderBodyHtml turns bullet-style lines into an unordered list", () => {
  const html = renderBodyHtml("Hello team,\n\n- First point\n- Second point\n- Third point");

  assert.match(html, /<ul style=/);
  assert.match(html, /<li[^>]*>First point<\/li>/);
  assert.doesNotMatch(html, /- First point/);
});

test("renderBodyHtml turns numbered section bodies into an ordered list", () => {
  const html = renderBodyHtml(
    "Hello team,\n\nNext steps\n\n1. Review the prototype\n2. Pick a direction\n3. Schedule the call",
  );

  assert.match(html, /<ol style=/);
  assert.match(html, /<li[^>]*>Review the prototype<\/li>/);
  assert.match(html, /<p style=\"margin: 0 0 10px 0; font-size: 13px;/);
});

test("renderBodyHtml turns stacked action lines into light bullets and bolds greeting", () => {
  const html = renderBodyHtml(
    "Hi Standert team,\nLooking at your site, I noticed a clear opportunity.\n\nTo make it concrete, we can:\n\nBuild a free prototype with product videos and 360° views\nSet up an AI assistant tailored to your catalog\nRun a free automation audit to streamline operations\nEven a rough prototype makes it easy to see the impact.\n—Alex",
  );

  assert.match(html, /font-size: 15px; line-height: 1.75; color: #f6f6f6; font-weight: 700/);
  assert.match(html, /<strong style="color: #ededed;">To make it concrete, we can:<\/strong>/);
  assert.match(html, /<ul style=/);
  assert.match(html, /<li[^>]*>Build a free prototype with product videos and 360° views<\/li>/);
  assert.match(html, /Even a rough prototype makes it easy to see the impact\./);
  assert.match(html, /Alex Rivera<\/p>/);
  assert.match(html, /Product &amp; AI Strategist<br \/>Stackfuse/);
});

test("renderBodyHtml expands Alex signatures but leaves other names alone", () => {
  const alexHtml = renderBodyHtml("Hello team,\n\nBody.\n\nBest,\nAlex");
  const otherHtml = renderBodyHtml("Hello team,\n\nBody.\n\nBest,\nMatthew");

  assert.match(alexHtml, /Best,<\/p>/);
  assert.match(alexHtml, /Alex Rivera<\/p>/);
  assert.match(alexHtml, /Product &amp; AI Strategist<br \/>Stackfuse/);
  assert.match(otherHtml, /Matthew<\/p>/);
  assert.doesNotMatch(otherHtml, /Alex Rivera/);
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
