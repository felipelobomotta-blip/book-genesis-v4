import { chromium } from "playwright";

const repoUrl = "https://github.com/felipelobomotta-blip/book-genesis-v4";
const subreddit = "ClaudeAI";
const postTitle = `I stress-tested AI agents on 10+ book projects in under 30 days. The 19-skill version was worse.`;

const postBody = `I spent the last month building and stress-testing an AI-assisted book pipeline.

The first version got huge: 17 phases, 19 skills, continuity tracking, reader simulations, scoring loops, revision agents, packaging, etc.

It caught a lot of errors.

It also started making the books worse.

The writer learned it was being judged on too many dimensions at once, so it stopped writing like a writer and started writing like a compliance engine.

So I rebuilt the system as a smaller, file-backed core that can run in Claude Code, Codex, Antigravity, Kimi, or basically any capable agent that can read/write files:

- one active phase prompt at a time
- PROJECT_STATE.yaml and ASSUMPTIONS.md
- durable artifacts instead of chat-only output
- draft before judgment
- adversarial audit before final score
- 10-dimension Genesis Score
- editorial package at the end

The repo now includes:

- the portable Book Genesis core
- the legacy V4/V5 Claude Code system
- a 10-book proof gallery with covers/cover concepts
- case studies explaining what each project taught the system
- portability notes for Claude Code, Codex, Antigravity, Kimi, and generic agents

Repo:
${repoUrl}

The most interesting files:
- docs/book-gallery.md
- skills/book-genesis-codex/
- docs/portability.md
- docs/book-genesis-codex.md
- SHOWCASE.md

The manuscripts are private. The repo publishes the pipeline, proof layer, cover wall, case studies, scoring artifacts, outlines/synopses where safe, and the actual portable skill.

I am curious if anyone else building long-form agent workflows has seen the same tradeoff: more orchestration improves consistency, but too many live constraints hurt voice.`;

const firstComment = `Small clarification because "10+ books" can sound like a fake flex:

The repo does not publish the private manuscripts. It publishes the system: pipeline, cover wall, case studies, score artifacts, outlines/synopses where safe, and the portable skill folder.

The point is not "download my books." The point is "here is the workflow that produced them, and here is what broke while testing it."`;

const userDataDir = "C:/Users/felip/.playwright-chrome-reddit-profile";

console.log("Launching Chromium with Reddit profile...");

const context = await chromium.launchPersistentContext(userDataDir, {
  headless: false,
  viewport: { width: 1280, height: 800 },
  args: ["--no-sandbox", "--disable-setuid-sandbox"],
});

const page = context.pages()[0] ?? await context.newPage();

async function isLoggedIn() {
  const loginCount = await page.locator('a[href*="/login"], input[name="user"], input[name="passwd"]').count();
  const logoutCount = await page.locator('form.logout, a[href*="/logout"]').count();
  return logoutCount > 0 && loginCount === 0;
}

if (!(await isLoggedIn())) {
  console.log("\nReddit does not look logged in.");
  console.log("Please log in manually in the browser window. Waiting up to 5 minutes...");
  await page.goto("https://old.reddit.com/login", { waitUntil: "domcontentloaded" });
  const deadline = Date.now() + 5 * 60 * 1000;
  while (Date.now() < deadline) {
    await page.waitForTimeout(3000);
    try {
      if (await isLoggedIn()) break;
    } catch {}
  }
}

if (!(await isLoggedIn())) {
  console.log("Still not logged in after waiting. Exiting.");
  await context.close();
  process.exit(2);
}

console.log("\nLogged in. Navigating to submit page...");

await page.goto(`https://old.reddit.com/r/${subreddit}/submit`, { waitUntil: "domcontentloaded" });
await page.waitForTimeout(2000);

// Fill title
const titleInput = page.locator('textarea[name="title"], input[name="title"]');
await titleInput.waitFor({ state: "visible", timeout: 10000 });
await titleInput.fill(postTitle);

// Fill body
const bodyInput = page.locator('textarea[name="text"]');
await bodyInput.waitFor({ state: "visible", timeout: 10000 });
await bodyInput.fill(postBody);

console.log("\nPost prepared. Title:", postTitle.substring(0, 60) + "...");

// Submit
const submitBtn = page.locator('button[type="submit"]').filter({ hasText: /submit/i }).first();
await submitBtn.click();

console.log("Submitted post. Waiting for redirect...");
await page.waitForTimeout(5000);

// Check if we're on the post page
const currentUrl = page.url();
if (currentUrl.includes("/comments/")) {
  console.log("Post successful! URL:", currentUrl);

  // Add first comment
  console.log("Adding first comment...");
  const commentBox = page.locator('textarea[name="text"], .usertext-edit textarea').first();
  await commentBox.waitFor({ state: "visible", timeout: 10000 });
  await commentBox.fill(firstComment);

  const saveBtn = page.locator('button[type="submit"]').filter({ hasText: /save/i }).first();
  await saveBtn.click();
  await page.waitForTimeout(3000);
  console.log("First comment added.");
} else {
  console.log("Current URL after submit:", currentUrl);
  console.log("Please verify the post manually.");
}

console.log("\nDone. Browser is open for review. Press Ctrl+C to close.");
