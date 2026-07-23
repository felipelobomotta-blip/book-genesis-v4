import { chromium } from "playwright";

const tweets = [
  `I used AI agents to push 10+ book projects in under 30 days.\n\nThen I open-sourced the pipeline.\n\nHere is what actually broke along the way 🧵`,
  `The first version was enormous:\n\n17 phases. 19 skills. Continuity tracking. Reader simulations. Scoring loops. Revision agents. Packaging. The works.\n\nIt caught a LOT of errors.`,
  `But it also made the books worse.\n\nThe writer learned it was being judged on 19 dimensions at once, so it stopped writing like a writer and started writing like a compliance engine.\n\nMore orchestration ≠ better prose.`,
  `So I rebuilt it as a smaller, file-backed core:\n\n• One active phase at a time\n• PROJECT_STATE.yaml + ASSUMPTIONS.md\n• Draft first, judge after\n• Adversarial audit before final score\n• Editorial package only after the manuscript survives critique`,
  `The result:\n\n10+ book projects with covers, case studies, scoring artifacts, and outlines.\n\nThe manuscripts are private.\n\nThe pipeline, proof layer, and portable skill are open-source.`,
  `It runs as a file-backed workflow in:\n\n• Claude Code\n• Codex\n• Antigravity\n• Kimi\n• Any agent that can read/write project files\n\nNo lock-in. No proprietary format. Just durable state files and phase prompts.`,
  `If you're building long-form agent workflows, I'm curious:\n\nHave you seen the same tradeoff — more live constraints improving consistency but hurting voice?\n\nRepo + proof gallery:\nhttps://github.com/felipelobomotta-blip/book-genesis-v4`,
  `The lesson that took me 10 books to learn:\n\nA pipeline beats a prompt.\n\nBut a smaller pipeline beats a bigger one.`
];

const userDataDir = "C:/Users/felip/AppData/Local/Google/Chrome/User Data";

console.log("Launching Chromium with main profile for X/Twitter...");

const context = await chromium.launchPersistentContext(userDataDir, {
  headless: false,
  viewport: { width: 1280, height: 800 },
  args: ["--no-sandbox", "--disable-setuid-sandbox", "--profile-directory=Default"],
});

const page = context.pages()[0] ?? await context.newPage();

// Navigate to X compose
await page.goto("https://x.com/compose/post", { waitUntil: "domcontentloaded" });
await page.waitForTimeout(3000);

// Check if logged in
const loginCheck = await page.locator('a[href="/login"]').count();
if (loginCheck > 0) {
  console.log("\nX/Twitter does not look logged in.");
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

console.log("\nLogged in. Posting thread...");

// Find the compose box
const composeBox = page.locator('[data-testid="tweetTextarea_0"], div[contenteditable="true"][role="textbox"]').first();
await composeBox.waitFor({ state: "visible", timeout: 10000 });

// Post first tweet
await composeBox.fill(tweets[0]);
await page.waitForTimeout(500);

// Add remaining tweets as replies
for (let i = 1; i < tweets.length; i++) {
  const addBtn = page.locator('[data-testid="addButton"]').first();
  if (await addBtn.count() > 0) {
    await addBtn.click();
    await page.waitForTimeout(500);
  }

  const boxes = page.locator('[data-testid="tweetTextarea_0"], div[contenteditable="true"][role="textbox"]');
  const count = await boxes.count();
  if (count > i) {
    await boxes.nth(i).fill(tweets[i]);
    await page.waitForTimeout(500);
  }
}

// Post the thread
const postBtn = page.locator('[data-testid="tweetButton"]').first();
await postBtn.click();

console.log("Thread submitted! Waiting...");
await page.waitForTimeout(5000);

const currentUrl = page.url();
console.log("Current URL:", currentUrl);
console.log("\nDone. Browser is open for review. Press Ctrl+C to close.");
