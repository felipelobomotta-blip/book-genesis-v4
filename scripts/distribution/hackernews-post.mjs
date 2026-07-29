import { chromium } from "playwright";

const postTitle = "Show HN: Book Genesis – an agent-agnostic AI book pipeline";

const postBody = `I built this after using AI coding agents across 10+ book projects in under 30 days.

The surprising part was that the larger version of the system — 17 phases, 19 skills, mid-draft gates, revision loops — caught more errors but often hurt the writing. The writer started optimizing for the evaluator.

The current version is smaller and agent-agnostic: durable project files, one active phase prompt at a time, adversarial audit before scoring, and an editorial package after the manuscript survives critique.

It runs in Claude Code, Codex, Antigravity, Kimi, or any agent that can read and write files. No proprietary format, no lock-in.

Repo:
https://github.com/felipelobomotta-blip/book-genesis-v4

Useful files:
- docs/book-gallery.md (10-book proof gallery)
- skills/book-genesis-codex/ (portable skill)
- docs/portability.md (agent-specific notes)
- docs/book-genesis-codex.md (pipeline documentation)
- SHOWCASE.md

Interested in feedback from people building long-form agent workflows.`;

const firstComment = `Quick context for anyone who wants to try it:

The easiest path is to open the repo in your agent of choice and read AGENTS.md. The pipeline is a file-backed workflow, not a CLI tool — it expects the agent to read phase prompts and write artifacts.

If you want to see what the system produced before trying it, docs/book-gallery.md has the cover wall, case studies, and scoring artifacts.

The manuscripts themselves are private. The repo publishes the pipeline, proof layer, and portable skill.

Happy to answer technical questions about the file-backed architecture, the adversarial audit, or the Genesis Score.`;

const userDataDir = "C:/Users/felip/AppData/Local/Google/Chrome/User Data";

console.log("Launching Chromium with main profile for Hacker News...");

const context = await chromium.launchPersistentContext(userDataDir, {
  headless: false,
  viewport: { width: 1280, height: 800 },
  args: ["--no-sandbox", "--disable-setuid-sandbox", "--profile-directory=Default"],
});

const page = context.pages()[0] ?? await context.newPage();

// Navigate to HN submit
await page.goto("https://news.ycombinator.com/submit", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2000);

// Check login
const loginCheck = await page.locator('a[href="/login"]').count();
if (loginCheck > 0) {
  console.log("\nHacker News does not look logged in.");
  console.log("Please log in manually in the browser window. Waiting up to 5 minutes...");
  const deadline = Date.now() + 5 * 60 * 1000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(3000);
    const stillLogin = await page.locator('a[href="/login"]').count();
    if (stillLogin === 0) break;
  }
}

if (await page.locator('a[href="/login"]').count() > 0) {
  console.log("Still not logged in. Exiting.");
  await context.close();
  process.exit(2);
}

console.log("\nLogged in. Posting...");

// Fill title
const titleInput = page.locator('input[name="title"]');
await titleInput.waitFor({ state: "visible", timeout: 10000 });
await titleInput.fill(postTitle);

// Fill URL
const urlInput = page.locator('input[name="url"]');
await urlInput.fill("https://github.com/felipelobomotta-blip/book-genesis-v4");

// HN text area (may not be visible if URL is filled)
const textInput = page.locator('textarea[name="text"]');
if (await textInput.count() > 0 && await textInput.isVisible()) {
  await textInput.fill(postBody);
}

console.log("\nPost prepared. Title:", postTitle);

// Submit
const submitBtn = page.locator('input[type="submit"]').first();
await submitBtn.click();

console.log("Submitted! Waiting...");
await page.waitForTimeout(5000);

const currentUrl = page.url();
console.log("Current URL:", currentUrl);

// If on post page, add first comment
if (currentUrl.includes("/item?id=")) {
  console.log("Post successful! Adding first comment...");

  const commentBox = page.locator('textarea[name="text"]').first();
  await commentBox.waitFor({ state: "visible", timeout: 10000 });
  await commentBox.fill(firstComment);

  const commentSubmit = page.locator('input[type="submit"]').filter({ hasText: /add comment/i }).first();
  await commentSubmit.click();
  await page.waitForTimeout(3000);
  console.log("First comment added.");
}

console.log("\nDone. Browser is open for review. Stay online for 4-6 hours to reply to comments. Press Ctrl+C to close.");
