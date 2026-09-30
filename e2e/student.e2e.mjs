import { chromium } from "playwright-core";
import fs from "node:fs";
import path from "node:path";

const FRONT = process.env.FRONTEND_URL ?? "http://localhost:3000";
const API = process.env.API_URL ?? "http://127.0.0.1:8000/api/v1";
const tag = Math.random().toString(36).slice(2, 8);
const results = [];
const only = process.argv[2]; // optional: run one section

function check(name, ok, detail = "") {
  results.push([ok, name]);
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${!ok && detail ? "  -> " + detail : ""}`);
}

const browser = await chromium.launch({
  executablePath: process.env.BROWSER_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  headless: true,
});

async function newUser(label) {
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await ctx.newPage();
  const calls = [];
  const errors = [];
  page.on("request", (r) => {
    if (r.url().startsWith(API)) calls.push(`${r.method()} ${r.url().replace(API, "")}`);
  });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error" && !/Failed to load resource|favicon/.test(m.text())) errors.push(m.text());
  });
  return { ctx, page, calls, errors, label };
}

const called = (u, re) => u.calls.some((c) => re.test(c));

async function registerUi(u, name, email, role = "student") {
  const { page } = u;
  await go(page, `${FRONT}/register`);
  await page.getByPlaceholder("Alex Morgan").fill(name);
  await page.getByPlaceholder("alex.morgan@university.edu").fill(email);
  await page.locator("select").selectOption(role);
  const pw = page.locator('input[type="password"]');
  await pw.nth(0).fill("Passw0rd!x");
  await pw.nth(1).fill("Passw0rd!x");
  await page.getByRole("button", { name: "Create Account" }).click();
}

async function loginUi(u, email, password) {
  const { page } = u;
  await go(page, `${FRONT}/login`);
  await page.getByPlaceholder("alex.morgan@university.edu").fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.getByRole("button", { name: /Sign In to CareerOS/ }).click();
}

async function go(page, url) {
  await page.goto(url);
  await page.waitForLoadState("networkidle").catch(() => {});
}

const student = await newUser("student");
const recruiter = await newUser("recruiter");
const officer = await newUser("officer");
const admin = await newUser("admin");

try {
  // ───────────────────────── auth gate + register + login ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/student`);
    await page.waitForURL("**/login", { timeout: 15000 }).catch(() => {});
    check("unauthenticated /student redirects to /login (no mock session)", page.url().endsWith("/login"), page.url());

    await page.getByPlaceholder("alex.morgan@university.edu").fill("nobody@test.com");
    await page.locator('input[type="password"]').fill("wrongwrong");
    await page.getByRole("button", { name: /Sign In to CareerOS/ }).click();
    const err = page.getByText(/Incorrect email or password/);
    check("wrong credentials show the backend error", await err.waitFor({ state: "visible", timeout: 8000 }).then(() => true).catch(() => false));
    check("failed login does not create a session", (await page.evaluate(() => localStorage.getItem("careeros_auth_tokens"))) === null);

    // client-side validation (no API call)
    await go(page, `${FRONT}/login`);
    const before = student.calls.length;
    await page.getByRole("button", { name: /Sign In to CareerOS/ }).click();
    check("empty login form is validated client-side", await page.getByText("Invalid email address").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false) && student.calls.length === before);

    // register (student)
    await registerUi(student, "Ada Lovelace", `ada_${tag}@test.com`, "student");
    await page.waitForURL("**/student", { timeout: 20000 }).catch(() => {});
    check("register -> lands on /student", page.url().endsWith("/student"), page.url());
    check("register called POST /auth/register, /auth/login, PUT profile, GET /auth/me", called(student, /POST \/auth\/register/) && called(student, /POST \/auth\/login/) && called(student, /PUT \/users\/me\/profile/) && called(student, /GET \/auth\/me/));
    check("welcome banner shows real registered name", await page.getByText("Welcome back, Ada!").waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    check("student dashboard calls analytics/roadmap/feed/jobs APIs", called(student, /GET \/analytics\/dashboard\/student/) && called(student, /GET \/learning\/roadmaps\/active/) && called(student, /GET \/recommendations\/feed/) && called(student, /GET \/recruiters\/jobs\/open/));
    check("no fake 'Alex Morgan' persona rendered", !(await page.content()).includes("Alex Morgan"));

    // duplicate registration shows the backend error
    const dup = await newUser("dup");
    await registerUi(dup, "Ada Again", `ada_${tag}@test.com`, "student");
    check("duplicate registration shows 'Email already registered'", await dup.page.getByText(/Email already registered/).waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    await dup.ctx.close();

    // session restore on reload
    await page.reload();
    check("session survives reload (auth/me restore)", await page.getByText("Welcome back, Ada!").waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));

    // role gating
    await go(page, `${FRONT}/admin`);
    await page.waitForURL("**/student", { timeout: 10000 }).catch(() => {});
    check("student opening /admin is redirected to /student", page.url().endsWith("/student"), page.url());
  }

  // ───────────────────────── profile ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/profile`);
    await page.getByRole("button", { name: "Edit" }).click();
    const inputs = page.locator("input");
    await page.getByText("First Name").locator("..").locator("input").fill("Augusta");
    await page.getByText("Headline").locator("..").locator("input").fill("Analytical Engineer");
    await page.getByRole("button", { name: "Save" }).first().click();
    check("profile save shows confirmation", await page.getByText("Profile saved.").waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    await page.reload();
    check("profile edits persisted in backend (visible after reload)", await page.getByText("Augusta Lovelace").waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false) && await page.getByText("Analytical Engineer").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("Add skill...").fill("Rust");
    await page.getByRole("button", { name: "Add", exact: true }).click();
    await page.getByText("Rust").first().waitFor({ timeout: 10000 }).catch(() => {});
    await page.reload();
    check("skill persisted via role_specific_data", await page.getByText("Rust").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    // the selected role must survive the merge
    const prof = await page.evaluate(async (api) => {
      const t = JSON.parse(localStorage.getItem("careeros_auth_tokens")).accessToken;
      return (await fetch(`${api}/users/me/profile`, { headers: { Authorization: `Bearer ${t}` } })).json();
    }, API);
    check("saving skills preserved selected_role", prof.data.role_specific_data.selected_role === "student");
  }

  // ───────────────────────── resume ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=resume`);
    const pdf = path.join(process.env.TEMP, "cv_e2e.pdf");
    fs.writeFileSync(pdf, "%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF");
    const txt = path.join(process.env.TEMP, "cv_e2e.txt");
    fs.writeFileSync(txt, "not a pdf");
    await page.locator('input[type="file"]').setInputFiles(txt);
    check("invalid file type rejected client-side", await page.getByText(/Unsupported file type/).waitFor({ state: "visible", timeout: 5000 }).then(() => true).catch(() => false));
    check("invalid upload made no API call", !called(student, /POST \/resumes\/upload/));
    await page.locator('input[type="file"]').setInputFiles(pdf);
    check("upload shows accepted notice", await page.getByText(/uploaded\. AI analysis is running/).waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    check("analysis result appears (polled)", await page.getByText("ATS Analysis").waitFor({ state: "visible", timeout: 25000 }).then(() => true).catch(() => false));
    check("resume upload + list + analysis APIs called", called(student, /POST \/resumes\/upload/) && called(student, /GET \/resumes$/) && called(student, /GET \/resumes\/[0-9a-f-]+\/analysis/));
    await page.reload();
    check("resume + analysis persist after reload", await page.getByText("cv_e2e.pdf").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false) && await page.getByText("ATS Analysis").waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));
  }

  // ───────────────────────── career discovery ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=discovery`);
    await page.getByText("Question 1 of 4").waitFor({ timeout: 15000 }).catch(() => {});
    check("assessment questions come from the backend template", await page.getByText("Question 1 of 4").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.getByRole("button", { name: /Next/ }).click();
    check("empty answer is blocked with validation", await page.getByText("Please provide an answer to continue.").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("Type your answer…").fill("Python and TypeScript");
    await page.getByRole("button", { name: /Next/ }).click();
    await page.getByRole("button", { name: "Building products" }).click(); // multiple choice
    await page.getByPlaceholder("Type your answer…").fill("A realtime chat app");
    await page.getByRole("button", { name: /Next/ }).click();
    await page.getByRole("button", { name: "In a small team" }).click();
    check("career report rendered after submit (polled)", await page.getByText("Your Career Report").waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false) && await page.getByText("Personality").waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false));
    check("submit + report APIs called", called(student, /POST \/discovery\/assessments\/[0-9a-f-]+\/submit/) && called(student, /GET \/discovery\/reports\//));
  }

  // ───────────────────────── mentor (floating widget + page) ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=mentor`);
    await page.getByPlaceholder("Ask your mentor…").fill("How do I improve my resume?");
    await page.getByRole("button", { name: "Send message" }).click();
    check("mentor reply from backend appears", await page.locator("div.self-start").first().waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));
    check("mentor session + message APIs called", called(student, /POST \/mentor\/sessions$/) && called(student, /POST \/mentor\/sessions\/[0-9a-f-]+\/message/));
    await page.reload();
    await page.getByText("How do I improve my resume?").first().waitFor({ timeout: 15000 }).catch(() => {});
    check("mentor history restored after reload", await page.getByText("How do I improve my resume?").first().waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false) && called(student, /GET \/mentor\/sessions\/latest/));
  }

  // ───────────────────────── career journey goals ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=careers`);
    await page.getByRole("button", { name: "Create goal" }).click();
    check("goal without title is blocked", await page.getByText("Give your goal a title.").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("e.g. Land a backend internship").fill("Land a backend internship");
    await page.getByPlaceholder("Add a milestone").fill("Finish roadmap");
    await page.getByRole("button", { name: "Add milestone" }).click();
    await page.getByRole("button", { name: "Create goal" }).click();
    check("goal appears in list after create", await page.getByText("Land a backend internship").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false) && await page.getByText("Finish roadmap").first().waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.reload();
    check("goal persisted after reload (GET /mentor/goals)", await page.getByText("Land a backend internship").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
  }

  // ───────────────────────── learning roadmap ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=academy`);
    await page.getByPlaceholder("Target role (e.g. Backend Engineer)").fill("Backend Engineer");
    await page.getByRole("button", { name: "Generate" }).click();
    check("generated roadmap renders modules/tasks (polled)", await page.getByText("Python & Async Backend Fundamentals").waitFor({ state: "visible", timeout: 25000 }).then(() => true).catch(() => false));
    const done = page.getByRole("button", { name: "Mark done" }).first();
    await done.click();
    check("marking a task done updates progress", await page.getByText(/1 of 3 tasks complete/).waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    await go(page, `${FRONT}/student`);
    const dash = await page.evaluate(async (api) => {
      const tk = JSON.parse(localStorage.getItem("careeros_auth_tokens")).accessToken;
      return (await fetch(`${api}/analytics/dashboard/student`, { headers: { Authorization: `Bearer ${tk}` } })).json();
    }, API);
    check("dashboard ATS card shows the real analysed resume score (> 0)", dash.resume_score > 0 && (await page.locator("main").innerText()).includes(`${Math.round(dash.resume_score)}/100`), JSON.stringify(dash));
    check("dashboard learning progress reflects completion", await page.getByText("33%").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
  }

  // ───────────────────────── interview (websocket) ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=interviews`);
    await page.getByRole("button", { name: "Start interview" }).click();
    check("interview first question streamed over WebSocket", await page.getByText(/Could you please introduce yourself/).waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("Type your answer…").fill("I am a backend engineer who loves APIs.");
    await page.getByRole("button", { name: "Submit answer" }).click();
    check("next question arrives after evaluation", await page.getByText(/shard that PostgreSQL/).waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));
    await page.getByRole("button", { name: /Finish & get report/ }).click();
    check("interview report rendered (polled)", await page.getByText("Interview report").waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false) && await page.getByText("Technical", { exact: true }).waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false));
    check("interview session + report APIs called", called(student, /POST \/interviews\/sessions$/) && called(student, /GET \/interviews\/sessions\/[0-9a-f-]+\/report/));
  }

  // ───────────────────────── communication (websocket) ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/workspace?tab=communication`);
    await page.getByRole("button", { name: "Start session" }).click();
    await page.getByPlaceholder("Type what you would say…").fill("I has a idea for the project.");
    await page.getByRole("button", { name: "Analyse message" }).click();
    check("live grammar feedback arrives over WebSocket", await page.getByText(/Grammar score:/).waitFor({ state: "visible", timeout: 15000 }).then(() => true).catch(() => false));
    await page.getByRole("button", { name: /Finish & get report/ }).click();
    check("communication report rendered (polled)", await page.getByText("Session report").waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false) && await page.getByText("Fluency", { exact: true }).waitFor({ state: "visible", timeout: 20000 }).then(() => true).catch(() => false));
  }

  // ───────────────────────── community ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/community`);
    await page.getByRole("button", { name: "Publish post" }).click();
    check("post without title/content is blocked", await page.getByText("A post needs a title and some content.").waitFor({ state: "visible", timeout: 4000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("Title").fill("Interview tips " + tag);
    await page.getByPlaceholder("What would you like to discuss?").fill("Practise aloud daily.");
    await page.getByPlaceholder("Tags (comma separated)").fill("tips, interviews");
    await page.getByRole("button", { name: "Publish post" }).click();
    check("new post shows in the latest feed", await page.getByText("Interview tips " + tag).first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    await page.getByRole("button", { name: "Show comments" }).first().click();
    check("opening a post loads its detail (GET /community/posts/{id}) and shows views", await page.getByText(/\d+ views/).waitFor({ state: "visible", timeout: 8000 }).then(() => true).catch(() => false) && called(student, /GET \/community\/posts\/[0-9a-f-]+$/));
    await page.getByPlaceholder("Add a comment…").fill("Great advice");
    await page.getByRole("button", { name: "Post", exact: true }).click();
    check("comment appears under the post", await page.getByText("Great advice").first().waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false));
    await page.getByPlaceholder("Search posts…").fill("Interview tips");
    await page.getByRole("button", { name: "Search", exact: true }).click();
    check("search finds the post", await page.getByText("Results for “Interview tips”").waitFor({ state: "visible", timeout: 10000 }).then(() => true).catch(() => false) && called(student, /GET \/community\/search\?q=Interview/));
  }
} catch (e) {
  check("student flow aborted by exception", false, String(e).slice(0, 300));
}

const failed = results.filter(([ok]) => !ok);
console.log(`\n${results.length - failed.length}/${results.length} browser checks passed (student section)`);
for (const u of [student]) if (u.errors.length) console.log(`console/page errors [${u.label}]:`, [...new Set(u.errors)].slice(0, 8));

await browser.close();
process.exit(failed.length ? 1 : 0);
