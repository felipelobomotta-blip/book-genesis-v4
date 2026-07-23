import { chromium } from "playwright";

const postBody = `I spent the last month stress-testing AI agents on book production.

The result: 10+ book projects completed in under 30 days.

The surprise: the bigger system was not the better one.

---

Version 1 had everything — 17 phases, 19 specialized skills, mid-draft scoring, continuity tracking, reader simulations.

It was impressive on paper.

But the writer started optimizing for the evaluator instead of the reader. The prose got competent and forgettable.

So I rebuilt the whole thing around a simpler principle: draft first, judge after.

---

The new system is a file-backed pipeline that works across AI agents — Claude Code, Codex, Antigravity, Kimi, or anything that can read and write project files.

One phase at a time. Explicit assumptions. Adversarial audit before scoring. Editorial package only after the manuscript survives critique.

The manuscripts stay private. The pipeline, cover gallery, case studies, and portable skill are open-source.

---

The lesson that stuck with me:

More agents caught more errors, but too many simultaneous constraints made the writing worse.

If you're building with AI agents — whether books, code, or operations — the real optimization is knowing what NOT to orchestrate.

Repo and proof layer in the comments.`;

const commentBody = `Link to the repository with the pipeline, cover gallery, case studies, and portable skill:
https://github.com/felipelobomotta-blip/book-genesis-v4

Key docs:
- docs/book-gallery.md (10+ project proof)
- docs/book-genesis-codex.md (pipeline documentation)
- skills/book-genesis-codex/ (portable skill)`;

const userDataDir = "C:/Users/felip/AppData/Local/Google/Chrome/User Data";

console.log("Launching Chromium with main profile for LinkedIn...");

const context = await chromium.launchPersistentContext(userDataDir, {
  headless: false,
  viewport: { width: 1280, height: 800 },
  args: ["--no-sandbox", "--disable-setuid-sandbox", "--profile-directory=Default"],
});

const page = context.pages()[0] ?? await context.newPage();

// Navigate to LinkedIn compose
await page.goto("https://www.linkedin.com/post/new/", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);

// Check login
const loginCheck = await page.locator('a[href*="/login"], input#username').count();
if (loginCheck > 0) {
  console.log("\nLinkedIn does not look logged in.");
  console.log("Please log in manually in the browser window. Waiting up to 5 minutes...");
  const deadline = Date.now() + 5 * 60 * 1000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(3000);
    const stillLogin = await page.locator('a[href*="/login"], input#username').count();
    if (stillLogin === 0) break;
  }
}

if (await page.locator('a[href*="/login"], input#username').count() > 0) {
  console.log("Still not logged in. Exiting.");
  await context.close();
  process.exit(2);
}

console.log("\nLogged in. Posting...");

// Find editor
const editor = page.locator('[data-testid="linkedin-editor"], div[contenteditable="true"][role="textbox"], .ql-editor').first();
await editor.waitFor({ state: "visible", timeout: 10000 });
await editor.fill(postBody);
await page.waitForTimeout(500);

// Post
const postBtn = page.locator('button').filter({ hasText: /Post/i }).first();
await postBtn.click();

console.log("Post submitted! Waiting for redirect...");
await page.waitForTimeout(5000);

const currentUrl = page.url();
console.log("Current URL:", currentUrl);

// If post successful, add comment
if (currentUrl.includes("/feed/update/") || currentUrl.includes("/posts/")) {
  console.log("Adding comment with links...");
  await page.waitForTimeout(2000);

  const commentBox = page.locator('[data-testid="social-actions__commentBtn"]').first();
  if (await commentBox.count() > 0) {
    await commentBox.click();
    await page.waitForTimeout(500);

    const commentEditor = page.locator('div[contenteditable="true"][role="textbox"]').first();
    await commentEditor.fill(commentBody);
    await page.waitForTimeout(500);

    const commentSubmit = page.locator('button').filter({ hasText: /Post/i }).first();
    await commentSubmit.click();
    console.log("Comment added.");
  }
}

console.log("\nDone. Browser is open for review. Press Ctrl+C to close.");
