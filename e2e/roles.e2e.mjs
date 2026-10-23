import { chromium } from "playwright-core";

const FRONT = process.env.FRONTEND_URL ?? "http://localhost:3000";
const API = process.env.API_URL ?? "http://127.0.0.1:8000/api/v1";
const tag = Math.random().toString(36).slice(2, 8);
const results = [];

function check(name, ok, detail = "") {
  results.push([ok, name]);
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${!ok && detail ? "  -> " + detail : ""}`);
}

const browser = await chromium.launch({
  executablePath: process.env.BROWSER_PATH ?? "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  headless: true,
});

async function go(page, url) {
  await page.goto(url);
  await page.waitForLoadState("networkidle").catch(() => {});
}
const vis = (loc, ms = 10000) => loc.waitFor({ state: "visible", timeout: ms }).then(() => true).catch(() => false);

async function newUser(label) {
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await ctx.newPage();
  const calls = [];
  page.on("request", (r) => {
    if (r.url().startsWith(API)) calls.push(`${r.method()} ${r.url().replace(API, "")}`);
  });
  return { ctx, page, calls, label };
}
const called = (u, re) => u.calls.some((c) => re.test(c));

async function registerUi(u, name, email, role) {
  const { page } = u;
  await go(page, `${FRONT}/register`);
  await page.getByPlaceholder("Alex Morgan").fill(name);
  await page.getByPlaceholder("alex.morgan@university.edu").fill(email);
  await page.locator("select").selectOption(role);
  const pw = page.locator('input[type="password"]');
  await pw.nth(0).fill("Passw0rd!x");
  await pw.nth(1).fill("Passw0rd!x");
  await page.getByRole("button", { name: "Create Account" }).click();
  await page.waitForURL(`**/${role}`, { timeout: 20000 }).catch(() => {});
  await page.waitForLoadState("networkidle").catch(() => {});
}

const recruiter = await newUser("recruiter");
const student = await newUser("student");
const officer = await newUser("officer");
const admin = await newUser("admin");
const jobTitle = `Platform Engineer ${tag}`;
const driveTitle = `Campus Drive ${tag}`;

try {
  // ───────────────────────── recruiter onboarding + job posting ─────────────────────────
  {
    const { page } = recruiter;
    await registerUi(recruiter, "Rita Recruiter", `rita_${tag}@test.com`, "recruiter");
    check("recruiter registers and lands on /recruiter", page.url().endsWith("/recruiter"), page.url());
    check("recruiter without a company sees the company setup step", await vis(page.getByText("Set up your company")));

    await page.getByRole("button", { name: "Create company" }).click();
    check("company form validates name", await vis(page.getByText("Company name is required.")));
    await page.getByPlaceholder("Company name").fill(`Acme ${tag}`);
    await page.getByPlaceholder("Domain (acme.com)").fill("not a domain");
    await page.getByRole("button", { name: "Create company" }).click();
    check("company form validates domain", await vis(page.getByText("Enter a valid company domain")));
    check("invalid company made no API call", !called(recruiter, /POST \/recruiters\/company/));
    await page.getByPlaceholder("Domain (acme.com)").fill(`acme-${tag}.com`);
    await page.getByRole("button", { name: "Create company" }).click();
    check("company created -> portal tabs appear", await vis(page.getByRole("button", { name: "Post Job" }).first()) || await vis(page.getByText("Post Job").first()));
    check("company create called POST /recruiters/company", called(recruiter, /POST \/recruiters\/company/));

    await page.getByText("Post Job").first().click();
    await page.getByRole("button", { name: "Publish job" }).click();
    check("job form validates required fields", await vis(page.getByText("Title and description are required.")));
    await page.getByPlaceholder("Job title").fill(jobTitle);
    await page.getByPlaceholder("Description", { exact: true }).fill("Build and run our platform.");
    await page.getByPlaceholder("Location").fill("Remote");
    await page.getByPlaceholder("Requirements (one per line)").fill("Python\nDocker");
    await page.getByRole("button", { name: "Publish job" }).click();
    check("job published and listed under Manage Jobs", await vis(page.getByText(jobTitle).first()));
    check("job create + list APIs called", called(recruiter, /POST \/recruiters\/jobs$/) && called(recruiter, /GET \/recruiters\/jobs$/));

    await go(page, `${FRONT}/officer`);
    await page.waitForURL("**/recruiter", { timeout: 10000 }).catch(() => {});
    check("recruiter opening /officer is redirected to /recruiter", page.url().endsWith("/recruiter"), page.url());
  }

  // ───────────────────────── student applies ─────────────────────────
  {
    const { page } = student;
    await registerUi(student, "Sam Student", `sam_${tag}@test.com`, "student");
    await go(page, `${FRONT}/jobs`);
    check("student sees recruiter's job on the board with company name", await vis(page.getByText(jobTitle).first()) && await vis(page.getByText(`Acme ${tag}`).first()));
    await page.getByPlaceholder("Search by title, company, or location…").fill("zzzz-no-match");
    check("job search shows empty state", await vis(page.getByText("No jobs match your search")));
    await page.getByPlaceholder("Search by title, company, or location…").fill(jobTitle);
    const card = page.locator("div.rounded-xl", { hasText: jobTitle }).first();
    await card.getByRole("button", { name: "Apply", exact: true }).click();
    check("Apply shows confirmation and button flips to Applied", await vis(page.getByText(`Applied to ${jobTitle}.`)) && await vis(card.getByRole("button", { name: "Applied" })));
    check("apply API called", called(student, /POST \/recruiters\/jobs\/[0-9a-f-]+\/apply/));
    await page.getByRole("tab", { name: "Application Tracker" }).click().catch(async () => page.getByText("Application Tracker").first().click());
    check("application appears in tracker with status Applied", await vis(page.getByText(jobTitle).first()) && await vis(page.getByText("Applied", { exact: true }).first()));
  }

  // ───────────────────────── recruiter moves candidate ─────────────────────────
  {
    const { page } = recruiter;
    await go(page, `${FRONT}/recruiter`);
    await page.getByText("Manage Jobs").first().click();
    await page.locator("div.rounded-xl", { hasText: jobTitle }).first().getByRole("button", { name: "Applicants" }).click();
    check("recruiter sees the candidate for the job", await vis(page.getByText(/Candidate [0-9a-f]{8}/)));
    await page.getByLabel("Pipeline stage").selectOption("Interview");
    await page.waitForTimeout(1500);
    check("stage change PATCH called", called(recruiter, /PATCH \/recruiters\/applications\//));
    await page.reload();
    await page.waitForLoadState("networkidle").catch(() => {});
    await page.getByText("Applicants").first().click();
    await page.getByLabel("Select job").selectOption({ label: jobTitle });
    check("new stage persisted after reload", (await page.getByLabel("Pipeline stage").inputValue().catch(() => "")) === "Interview");

    // student sees the change
    await go(student.page, `${FRONT}/jobs?tab=tracker`);
    check("student's tracker shows the recruiter's status change (Interview)", await vis(student.page.getByText("Interview", { exact: true }).first()));
  }

  // ───────────────────────── officer onboarding + drive ─────────────────────────
  {
    const { page } = officer;
    await registerUi(officer, "Olive Officer", `olive_${tag}@test.com`, "officer");
    check("officer lands on /officer with college setup", page.url().endsWith("/officer") && await vis(page.getByText("Register your college")));
    await page.getByPlaceholder("College name").fill(`Uni ${tag}`);
    await page.getByPlaceholder("Domain (university.edu)").fill("bad domain");
    await page.getByRole("button", { name: "Register college" }).click();
    check("college form validates domain", await vis(page.getByText("Enter a valid college domain")));
    await page.getByPlaceholder("Domain (university.edu)").fill(`uni-${tag}.edu`);
    await page.getByRole("button", { name: "Register college" }).click();
    check("college created -> drives UI shown", await vis(page.getByText("New Drive").first()));
    await page.getByText("New Drive").first().click();
    await page.getByRole("button", { name: "Create drive" }).click();
    check("drive form validates title", await vis(page.getByText("Give the drive a title.")));
    await page.getByPlaceholder("Title").fill(driveTitle);
    await page.getByPlaceholder("Minimum CGPA (optional)").fill("11");
    await page.getByRole("button", { name: "Create drive" }).click();
    check("drive form validates CGPA range", await vis(page.getByText("Minimum CGPA must be a number between 0 and 10.")));
    await page.getByPlaceholder("Minimum CGPA (optional)").fill("7");
    await page.getByRole("button", { name: "Create drive" }).click();
    check("drive created", await vis(page.getByText(`Drive "${driveTitle}" created.`)));
    check("college + drive APIs called", called(officer, /POST \/placements\/colleges/) && called(officer, /POST \/placements\/drives$/));
  }

  // ───────────────────────── student registers for drive ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/jobs?tab=drives`);
    const card = page.locator("div.rounded-xl", { hasText: driveTitle }).first();
    check("student sees officer's drive", await vis(card));
    await card.getByRole("button", { name: "Register" }).click();
    check("registration shows status Registered", await vis(card.getByText("Registered")));
    check("register API called", called(student, /POST \/placements\/drives\/[0-9a-f-]+\/register/));
    await page.reload();
    await page.waitForLoadState("networkidle").catch(() => {});
    check("registration persisted after reload", await vis(page.locator("div.rounded-xl", { hasText: driveTitle }).first().getByText("Registered")));
  }

  // ───────────────────────── officer manages registration + offer ─────────────────────────
  {
    const { page } = officer;
    await go(page, `${FRONT}/officer`);
    await page.getByLabel("Select drive").selectOption({ label: `${driveTitle} (Upcoming)` });
    check("drive detail panel shows requirements from GET /placements/drives/{id}", await vis(page.getByText(/Requirements: min cgpa: 7/)) && called(officer, /GET \/placements\/drives\/[0-9a-f-]+$/));
    check("officer sees the student's registration", await vis(page.getByText(/Student [0-9a-f]{8}/)));
    await page.getByLabel("Registration status").selectOption("Offered");
    await vis(page.getByPlaceholder("Package details, e.g. 12 LPA"));
    await page.getByRole("button", { name: "Release offer" }).click();
    check("offer without package details is blocked", await vis(page.getByText(/Enter the package details/)));
    await page.getByPlaceholder("Package details, e.g. 12 LPA").fill("12 LPA");
    await page.getByRole("button", { name: "Release offer" }).click();
    check("offer released", await vis(page.getByText("Offer released.")));
    await page.getByRole("button", { name: "Calculate eligibility" }).click();
    check("eligibility calculation accepted", await vis(page.getByText(/Eligibility calculation started/)));
    await page.getByRole("button", { name: "Rank students" }).click();
    check("ranking accepted", await vis(page.getByText(/ranking started/i)));
    check("registration/offer/eligibility/rank APIs called", called(officer, /PATCH \/placements\/registrations\//) && called(officer, /POST \/placements\/registrations\/[0-9a-f-]+\/offer/) && called(officer, /calculate-eligibility/) && called(officer, /\/rank/));
  }

  // ───────────────────────── admin console ─────────────────────────
  {
    const { page } = admin;
    await go(page, `${FRONT}/login`);
    await page.getByPlaceholder("alex.morgan@university.edu").fill(process.env.E2E_ADMIN_EMAIL ?? "");
    await page.locator('input[type="password"]').fill(process.env.E2E_ADMIN_PASSWORD ?? "");
    await page.getByRole("button", { name: /Sign In to CareerOS/ }).click();
    await page.waitForURL("**/admin", { timeout: 20000 }).catch(() => {});
    await page.waitForLoadState("networkidle").catch(() => {});
    check("admin login routes to /admin by RBAC (no persona picker)", page.url().endsWith("/admin"), page.url());
    check("admin overview shows live stats and health", await vis(page.getByText("Total users")) && await vis(page.getByText("System health").first()));
    await page.getByText("Users", { exact: true }).first().click();
    check("admin users list loads real users", await vis(page.getByText(`sam_${tag}@test.com`)));
    check("users tab lists the roles & permissions catalog", await vis(page.getByText("Roles & permissions").first()) && await vis(page.getByText(/admin:read/).first()));
    const row = page.locator("div.rounded-xl", { hasText: `sam_${tag}@test.com` }).first();
    await row.getByLabel(`Status for sam_${tag}@test.com`).selectOption("SUSPENDED");
    check("suspending a user confirms", await vis(page.getByText("User status updated.")));
    await row.getByLabel(`Status for sam_${tag}@test.com`).selectOption("ACTIVE");
    await page.waitForTimeout(800);

    await page.getByText("Flags & Settings").first().click();
    await page.getByPlaceholder("flag_key").fill(`beta_${tag}`);
    await page.getByRole("button", { name: "Add" }).first().click();
    check("feature flag created", await vis(page.getByText(`beta_${tag}`).first()));
    await page.getByRole("button", { name: "Disabled" }).first().click();
    check("feature flag toggled on", await vis(page.getByRole("button", { name: "Enabled" }).first()));

    await page.getByText("Announcements", { exact: true }).first().click();
    await page.getByPlaceholder("Title").first().fill(`Downtime ${tag}`);
    await page.getByPlaceholder("Content").first().fill("Maintenance tonight");
    await page.getByRole("button", { name: "Publish" }).click();
    check("announcement published", await vis(page.getByText("Announcement published.")));

    // announcement reaches a non-admin user's notification center
    await go(student.page, `${FRONT}/notification-center`);
    check("student notification center shows the admin announcement", await vis(student.page.getByText(`Downtime ${tag}`).first()));

    await page.getByText("Monitoring", { exact: true }).first().click();
    check("monitoring tab loads audit log with the admin actions", await vis(page.getByText("update_user_status").first()) || await vis(page.getByText(/create_flag|toggle|flag/i).first()));
  }

  // ───────────────────────── session refresh, expiry, network failure, logout ─────────────────────────
  {
    const { page } = student;
    await go(page, `${FRONT}/student`);
    // 1) expired access token but valid refresh token -> transparent refresh
    await page.evaluate(() => {
      const t = JSON.parse(localStorage.getItem("careeros_auth_tokens"));
      localStorage.setItem("careeros_auth_tokens", JSON.stringify({ ...t, accessToken: "expired.invalid.token" }));
    });
    student.calls.length = 0;
    await page.reload();
    await page.waitForLoadState("networkidle").catch(() => {});
    check("expired access token is refreshed transparently (POST /auth/refresh)", called(student, /POST \/auth\/refresh/) && await vis(page.getByText("Welcome back, Sam!")));

    // 2) network failure -> error banner with Retry -> recovers
    await page.route("**/recruiters/jobs/open", (route) => route.abort());
    await go(page, `${FRONT}/jobs`);
    check("network failure shows a friendly error with Retry", await vis(page.getByText(/Cannot reach the server/)) && await vis(page.getByRole("button", { name: "Retry" })));
    await page.unroute("**/recruiters/jobs/open");
    await page.getByRole("button", { name: "Retry" }).click();
    check("Retry recovers once the network is back", await vis(page.getByText(jobTitle).first()));

    // 3) both tokens invalid -> back to login
    await page.evaluate(() => localStorage.setItem("careeros_auth_tokens", JSON.stringify({ accessToken: "bad", refreshToken: "bad" })));
    await page.reload();
    await page.waitForURL("**/login", { timeout: 15000 }).catch(() => {});
    check("invalid tokens end the session and redirect to /login", page.url().endsWith("/login"), page.url());
    check("dead tokens are cleared", (await page.evaluate(() => localStorage.getItem("careeros_auth_tokens"))) === null);

    // 4) logout
    await go(page, `${FRONT}/login`);
    await page.getByPlaceholder("alex.morgan@university.edu").fill(`sam_${tag}@test.com`);
    await page.locator('input[type="password"]').fill("Passw0rd!x");
    await page.getByRole("button", { name: /Sign In to CareerOS/ }).click();
    await page.waitForURL("**/student", { timeout: 20000 }).catch(() => {});
    check("login as existing student routes to /student", page.url().endsWith("/student"), page.url());
    await page.getByTitle("Log Out").click();
    await page.waitForURL("**/login", { timeout: 10000 }).catch(() => {});
    check("logout clears tokens and returns to /login", page.url().endsWith("/login") && (await page.evaluate(() => localStorage.getItem("careeros_auth_tokens"))) === null);
    await go(page, `${FRONT}/student`);
    await page.waitForURL("**/login", { timeout: 10000 }).catch(() => {});
    check("after logout /student is protected", page.url().endsWith("/login"), page.url());
  }
} catch (e) {
  check("multi-role flow aborted by exception", false, String(e).slice(0, 400));
}

const failed = results.filter(([ok]) => !ok);
console.log(`\n${results.length - failed.length}/${results.length} browser checks passed (multi-role section)`);
await browser.close();
process.exit(failed.length ? 1 : 0);
