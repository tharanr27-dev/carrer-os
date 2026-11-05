"""Draws the report's diagrams (greyscale, print friendly) with matplotlib. Every diagram is derived from the real code
structure of Career OS (see the verification file). Run: python diagrams.py"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Ellipse, FancyBboxPatch, Polygon, Rectangle

for f in ("times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf"):
    p = "C:/Windows/Fonts/" + f
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams["font.family"] = "Times New Roman"
plt.rcParams["axes.unicode_minus"] = False

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")
os.makedirs(OUT, exist_ok=True)
LIGHT, MID, DARK, WHITE = "#EDEDED", "#D0D0D0", "#B0B0B0", "#FFFFFF"


def canvas(w=6.4, h=4.4, ymax=100):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, ymax)
    ax.axis("off")
    return fig, ax


def box(ax, cx, cy, w, h, text, fill=LIGHT, fs=8, bold=False, lw=1.0, dashed=False, round_=True, italic=False):
    style = "round,pad=0.25,rounding_size=1.2" if round_ else "square,pad=0.0"
    p = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h, boxstyle=style, fc=fill, ec="black", lw=lw, ls="--" if dashed else "-")
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", fontstyle="italic" if italic else "normal", linespacing=1.15)
    return p


def group(ax, x, y, w, h, title, fs=8):
    ax.add_patch(Rectangle((x, y), w, h, fc="none", ec="black", lw=0.9, ls="--"))
    ax.text(x + 1.2, y + h - 1.2, title, ha="left", va="top", fontsize=fs, fontweight="bold")


def arrow(ax, p1, p2, text=None, dashed=False, fs=7, off=(0, 1.6), both=False, rad=0.0, tx=None):
    st = "<->" if both else "->"
    ax.annotate("", xy=p2, xytext=p1, arrowprops=dict(arrowstyle=st, lw=0.9, ls="--" if dashed else "-", color="black",
                                                       connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if text:
        mx, my = ((p1[0] + p2[0]) / 2 + off[0], (p1[1] + p2[1]) / 2 + off[1]) if tx is None else tx
        ax.text(mx, my, text, ha="center", va="center", fontsize=fs, bbox=dict(fc="white", ec="none", pad=0.6))


def link(ax, pa, pb, text=None, dashed=False, fs=6.8, both=False, rad=0.0, off=(0, 0)):
    """Arrow between two patches (clipped at their borders)."""
    from matplotlib.patches import FancyArrowPatch

    def centre(p):
        bb = p.get_extents().transformed(ax.transData.inverted())
        return ((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2)

    a = FancyArrowPatch(centre(pa), centre(pb), patchA=pa, patchB=pb, arrowstyle="<->" if both else "->", mutation_scale=9, lw=0.9,
                        ls="--" if dashed else "-", color="black", connectionstyle=f"arc3,rad={rad}", shrinkA=1, shrinkB=1)
    ax.add_patch(a)
    if text:
        (x1, y1), (x2, y2) = centre(pa), centre(pb)
        ax.text((x1 + x2) / 2 + off[0], (y1 + y2) / 2 + off[1], text, fontsize=fs, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=0.5))


def diamond(ax, cx, cy, w, h, text, fs=7.5, fill=WHITE):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)], fc=fill, ec="black", lw=1.0))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, linespacing=1.1)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=220, bbox_inches="tight", pad_inches=0.08, facecolor="white")
    plt.close(fig)
    print("saved", name)


def sequence(actors, msgs, name, w=6.4, h=5.2, title=None):
    """actors: list of labels; msgs: list of (from_idx, to_idx, text, dashed)."""
    fig, ax = canvas(w, h)
    n = len(actors)
    xs = [10 + i * (80 / (n - 1)) for i in range(n)]
    top = 96
    for x, a in zip(xs, actors):
        box(ax, x, top, 15.5, 6.5, a, fill=MID, fs=7.5, bold=True)
        ax.plot([x, x], [top - 3.5, 3], color="black", lw=0.7, ls=(0, (4, 3)))
    y = top - 10
    step = (top - 16) / max(len(msgs), 1)
    for i, (a, b, text, dashed) in enumerate(msgs, 1):
        x1, x2 = xs[a], xs[b]
        if a == b:
            ax.annotate("", xy=(x1 + 0.3, y - 3.2), xytext=(x1 + 0.3, y), arrowprops=dict(arrowstyle="->", lw=0.9, connectionstyle="arc3,rad=-1.6"))
            ax.text(x1 + 4.5, y - 1.6, f"{i}. {text}", fontsize=7, ha="left", va="center")
        else:
            arrow(ax, (x1, y), (x2, y), None, dashed=dashed)
            ax.text((x1 + x2) / 2, y + 1.3, f"{i}. {text}", fontsize=7, ha="center", va="bottom")
        y -= step
    save(fig, name)


def fig_1_1():
    fig, ax = canvas(6.4, 5.0)
    hub = box(ax, 50, 52, 24, 12, "CAREER OS\nStudent workspace", fill=MID, fs=10, bold=True)
    mods = [("Resume Center\n(rule-based analysis)", 15, 82), ("Interview Prep &\nRole Training", 38, 88), ("AI Mentor\n(LLM chat)", 62, 88),
            ("Job Recommendations\n(live remote jobs)", 85, 82), ("Communication\nCoach", 12, 52), ("Career Discovery", 88, 52),
            ("Learning Roadmap", 15, 22), ("Recommendations", 38, 16), ("Interview Studio\n(WebSocket)", 62, 16), ("Placements &\nRecruiters", 85, 22)]
    for t, x, y in mods:
        link(ax, hub, box(ax, x, y, 21, 10, t, fs=7.5))
    box(ax, 50, 3.5, 82, 5.5, "Shared services: authentication (JWT) · role-based access · database · audit log", fill=LIGHT, fs=7.6, italic=True)
    save(fig, "fig_1_1_modules.png")


def fig_4_1():
    fig, ax = canvas(6.4, 5.9)
    boxes = [("Student", 88), ("Recruiter", 76), ("Placement\nOfficer", 64), ("Admin", 52)]
    group(ax, 23, 36, 20, 56, "Client tier")
    browser = box(ax, 33, 79, 15, 9, "Web browser", fill=MID, fs=8, bold=True)
    app = box(ax, 33, 56, 16, 21, "Next.js 15\nReact 19\nTypeScript\nTailwind CSS\nReact Query\nZustand", fs=7.5)
    for t, y in boxes:
        link(ax, box(ax, 10, y, 15, 8, t, fs=8), browser)
    link(ax, browser, app)
    ax.text(33, 40.5, "HTTPS · JSON · JWT · WebSocket", fontsize=6.3, ha="center", style="italic")
    group(ax, 48, 14, 31, 78, "Application tier (FastAPI)")
    mw = box(ax, 63.5, 80, 26, 8, "Middleware: CORS · rate limit ·\nsecurity headers · request ID", fs=7)
    rt = box(ax, 63.5, 69, 26, 8, "Routers /api/v1 (16 modules)\nvalidation · JWT · RBAC", fs=7)
    sv = box(ax, 63.5, 58, 26, 8, "Services (business rules,\nownership checks, scoring)", fs=7)
    rp = box(ax, 63.5, 47, 26, 8, "Repositories +\nSQLAlchemy 2 (async ORM)", fs=7)
    al = box(ax, 63.5, 33.5, 26, 10, "Algorithms: resume analysis,\nrole question selection,\nrecommendations, ranking", fs=7)
    lc = box(ax, 63.5, 20.5, 26, 7, "LLM client (httpx, typed errors)", fs=7)
    link(ax, mw, rt); link(ax, rt, sv); link(ax, sv, rp)
    link(ax, app, mw, both=True)
    group(ax, 83, 14, 16.5, 78, "Data and services")
    db = box(ax, 91, 78, 14, 14, "PostgreSQL\n(Supabase)\nSQLite (local\nand tests)", fill=MID, fs=6.6)
    fs_ = box(ax, 91, 59, 14, 9, "Local file\nstorage\n(resumes)", fs=6.6)
    llm = box(ax, 91, 43, 14, 10, "LLM provider\n(Groq / xAI /\nAnthropic)", fs=6.6)
    hj = box(ax, 91, 27, 14, 10, "Himalayas\nremote jobs\nAPI", fs=6.6)
    link(ax, rp, db); link(ax, al, fs_, dashed=True); link(ax, lc, llm, dashed=True); link(ax, al, hj, dashed=True)
    ax.text(50, 6, "Solid arrows: always used · Dashed arrows: used only when the feature or key is available", ha="center", fontsize=7, style="italic")
    save(fig, "fig_4_1_architecture.png")


def fig_4_2():
    fig, ax = canvas(6.4, 5.2)
    pg = box(ax, 40, 90, 72, 14, "Pages (Next.js App Router)\napp/(auth): login, register  ·  app/(dashboard): student, resume, jobs,\ninterview-prep, mentor, recruiter, officer, admin, ...", fs=7.5)
    ft = box(ax, 40, 70, 72, 11, "Feature modules (features/)\nstudent · recruiter · officer · admin · community · mentor · platform", fs=7.5)
    ui = box(ax, 40, 53, 72, 11, "Shared UI components (components/ui)\nbutton · card · tabs · dialog · sidebar · top-nav · feedback", fs=7.5)
    group(ax, 4, 24, 72, 20, "State and data layer")
    box(ax, 23, 31, 29, 11, "React Query\nserver data, caching,\nloading and error states", fs=7.2, fill=MID)
    box(ax, 57, 31, 31, 11, "Zustand stores\nuseAuthStore · useMentorStore\nuseNotificationStore", fs=7.2, fill=MID)
    api = box(ax, 40, 10, 72, 13, "Centralised API client (lib/api.ts)\ntyped methods · Bearer token · automatic refresh\nApiError · WebSocket URL helper", fs=7.3, fill=MID)
    be = box(ax, 91, 40, 14, 20, "Backend\nFastAPI\n/api/v1", fs=7.5, bold=True)
    for y1, y2 in ((83, 75.6), (64.4, 58.6), (47.4, 44.8)):
        arrow(ax, (40, y1), (40, y2))
    arrow(ax, (40, 24), (40, 16.8))
    link(ax, api, be, "REST / WebSocket", both=True, off=(-1, -6), fs=6.6)
    save(fig, "fig_4_2_frontend.png")


def fig_4_3():
    fig, ax = canvas(6.4, 5.6)
    items = [("HTTP request / WebSocket connection", 92, 7, True),
             ("Middleware stack\nCORS · rate limiting (100 per minute per IP) · security headers · request ID", 78, 9, False),
             ("Router (one APIRouter per module) · Pydantic request validation\nAuth dependencies: get_current_user · require_permissions ·\nverify_recruiter_access · verify_placement_officer_access", 62, 14, False),
             ("Service layer: business logic, ownership checks, scoring,\norchestration of AI calls", 46, 9, False),
             ("Repository layer: SQLAlchemy 2 async queries (select / insert / update)", 33, 8, False),
             ("ORM models (103 tables) → PostgreSQL / SQLite", 20, 7, True)]
    patches = [box(ax, 37, y, 68, h, t, fs=7.2, fill=MID if bold else LIGHT, bold=bold) for t, y, h, bold in items]
    for a, b in zip(patches[:-1], patches[1:]):
        link(ax, a, b)
    group(ax, 76, 12, 23.5, 82, "Supporting components")
    sup = [("core/config.py\nsettings, secret policy", 84), ("core/security.py\nbcrypt · JWT", 71), ("core/login_throttle.py\nlogin throttling", 58),
           ("core/text_analysis.py\nrule-based text analysis", 45), ("training/llm.py\nLLM client", 31)]
    sp = [box(ax, 87.7, y, 20, 9, t, fs=6.5) for t, y in sup]
    link(ax, patches[2], sp[1], dashed=True); link(ax, patches[2], sp[2], dashed=True); link(ax, patches[3], sp[3], dashed=True); link(ax, patches[3], sp[4], dashed=True)
    save(fig, "fig_4_3_backend.png")


# ───────────────────────── Figure 4.4  API communication (sequence) ─────────────────────────
def fig_4_4():
    sequence(["Student UI\n(React page)", "API client\n(lib/api.ts)", "FastAPI\nrouter", "get_current_user\n(JWT check)", "Service +\nRepository", "Database"],
             [(0, 1, "user action → api.method()", False), (1, 2, "HTTPS request + Bearer token", False), (2, 3, "Depends(get_current_user)", False),
              (3, 5, "load user by id", False), (3, 2, "authenticated user (or 401)", True), (2, 4, "validated Pydantic body", False),
              (4, 5, "SQLAlchemy async query", False), (5, 4, "rows", True), (4, 2, "result model", True), (2, 1, "JSON envelope {success, data}", True),
              (1, 0, "typed data or ApiError → UI state", True)], "fig_4_4_api_flow.png", h=5.3)


def fig_4_5():
    fig, ax = canvas(6.4, 6.4)
    box(ax, 18, 94, 30, 7, "POST /auth/login\n(email, password)", fs=7.5, fill=MID, bold=True)
    diamond(ax, 18, 80, 32, 11, "Throttle exceeded?\n(5 per account,\n30 per IP)", fs=7)
    box(ax, 51, 80, 17, 6.5, "HTTP 429", fs=7.5)
    diamond(ax, 18, 64, 32, 11, "bcrypt hash\nmatches?")
    box(ax, 51, 64, 20, 8, "HTTP 401 and\nfailure counted", fs=7)
    box(ax, 18, 49, 32, 8, "Issue access token (15 min)\nand refresh token (7 days)", fs=7.2)
    box(ax, 18, 36, 32, 8, "Frontend stores tokens\n(localStorage), GET /auth/me", fs=7.2)
    box(ax, 18, 23, 32, 8, "Every request:\nAuthorization: Bearer <token>", fs=7.2)
    diamond(ax, 18, 9, 34, 12, "Token valid, type = access,\nuser active?", fs=6.8)
    box(ax, 51, 9, 20, 8.5, "HTTP 401: refresh\nonce, else sign out", fs=6.8)
    for a, b in ((90.5, 85.5), (74.5, 69.5), (58.5, 53), (45, 40), (32, 27), (19, 15)):
        arrow(ax, (18, a), (18, b))
    arrow(ax, (34, 80), (42.5, 80), "yes", off=(0, 1.6)); arrow(ax, (34, 64), (41, 64), "no", off=(0, 1.6)); arrow(ax, (35, 9), (41, 9), "no", off=(0, 1.6))
    ax.text(19.5, 74.8, "no", fontsize=7); ax.text(19.5, 58.8, "yes", fontsize=7)
    group(ax, 66, 22, 33, 72, "Authorisation on each route")
    for t, y in (("Own data: owner check\nin the service → 403", 80), ("Admin: require_permissions\n(roles → permissions) → 403", 65),
                 ("Recruiter: company member,\njob.company_id = mine → 403", 50), ("Officer: college member,\ndrive.college_id = mine → 403", 35)):
        box(ax, 82.5, y, 29, 9, t, fs=6.8)
    arrow(ax, (35, 12), (66, 24), "yes", dashed=True, rad=-0.2, tx=(54, 22))
    save(fig, "fig_4_5_auth_flow.png")


def fig_4_6():
    fig, ax = canvas(6.4, 6.8)
    box(ax, 24, 95, 42, 6, "Student sends a message (1 to 4000 characters)", fs=7.3, fill=MID, bold=True)
    box(ax, 24, 85, 42, 7, "Frontend store → POST\n/mentor/sessions/{id}/message", fs=7.1)
    diamond(ax, 24, 72, 40, 11, "JWT valid and session\nbelongs to this user?", fs=7)
    box(ax, 66, 72, 24, 6, "HTTP 401 / 403", fs=7.3)
    diamond(ax, 24, 57, 40, 11, "Within 12 messages\nper minute?", fs=7)
    box(ax, 66, 57, 24, 6, "HTTP 429", fs=7.3)
    diamond(ax, 24, 42, 40, 11, "LLM API key\nconfigured?", fs=7)
    box(ax, 66, 42, 30, 8, "HTTP 503 setup message\n(nothing is saved)", fs=7.1)
    box(ax, 24, 28, 42, 10, "ContextAggregator reads this user's saved\nrecords → <user_facts>; last 10 messages\nadded as conversation history", fs=6.9)
    box(ax, 24, 15.5, 42, 8, "Provider call (httpx): system prompt +\nhistory + question → reply text", fs=7)
    diamond(ax, 24, 4.5, 30, 8.5, "Reply OK?", fs=7.2)
    fail = box(ax, 70, 20, 36, 12, "Failure mapped to a safe message\n(timeout 504, rate limit 429,\nbad key or model 502, overload 503)\nnothing saved · Retry button shown", fs=6.4)
    ok = box(ax, 70, 5, 36, 9, "Save USER and AI messages,\nwrite audit record, return\nthe reply to the chat window", fs=6.9)
    for y1, y2 in ((92, 88.5), (81.5, 77.5), (66.5, 62.5), (51.5, 47.5), (36.5, 33), (23, 19.5), (11.5, 8.8)):
        arrow(ax, (24, y1), (24, y2))
    arrow(ax, (44, 72), (54, 72), "no", off=(0, 1.5)); arrow(ax, (44, 57), (54, 57), "no", off=(0, 1.5)); arrow(ax, (44, 42), (51, 42), "no", off=(0, 1.5))
    arrow(ax, (39, 4.5), (52, 5), "yes", off=(0, 1.6)); arrow(ax, (35, 7.5), (52, 17), "no", off=(2.5, -3.5))
    ax.text(25.5, 67, "yes", fontsize=7); ax.text(25.5, 52, "yes", fontsize=7); ax.text(25.5, 37, "yes", fontsize=7)
    save(fig, "fig_4_6_mentor_flow.png")


def fig_4_7():
    fig, ax = canvas(6.4, 5.2)
    ax.add_patch(Ellipse((50, 48), 30, 24, fc=MID, ec="black", lw=1.2))
    ax.text(50, 48, "0\nCAREER OS\nplatform", ha="center", va="center", fontsize=10, fontweight="bold")
    ents = {"Student": (13, 88), "Recruiter": (87, 88), "Placement\nOfficer": (13, 9), "Admin": (87, 9), "LLM provider\n(Groq / xAI /\nAnthropic)": (11, 48), "Himalayas\njobs API": (89, 48)}
    boxes = {k: box(ax, x, y, 19, 11, k, fs=7.5, round_=False, fill=WHITE) for k, (x, y) in ents.items()}
    centre = Ellipse((50, 48), 30, 24)
    ax.add_patch(centre)
    centre.set_visible(False)

    def flow(a, b, text, dashed=False, both=False, off=(0, 0)):
        p1, p2 = ents[a], (50, 48)
        arrow(ax, (p1[0] + (9.5 if p1[0] < 50 else -9.5), p1[1] + (-5.5 if p1[1] > 48 else 5.5 if p1[1] < 48 else 0)), (p2[0] + (-13 if p1[0] < 50 else 13) * (1 if abs(p1[1] - 48) < 5 else 0.6), p2[1] + (8 if p1[1] > 48 else -8 if p1[1] < 48 else 0)), text, dashed=dashed, both=both, fs=6.5, off=off)

    flow("Student", None, "profile, resume, answers,\nmessages", off=(-9, 5))
    flow("Recruiter", None, "company, jobs,\napplication status", off=(9, 5))
    flow("Placement\nOfficer", None, "colleges, drives,\nranking requests", off=(-9, -5))
    flow("Admin", None, "users, roles,\nannouncements", off=(9, -5))
    flow("LLM provider\n(Groq / xAI /\nAnthropic)", None, "prompt + facts out,\nreply in", both=True, off=(0, 5))
    flow("Himalayas\njobs API", None, "queries out,\nlistings in", both=True, off=(0, 5))
    ax.text(50, 98, "Arrows show data flowing into and out of the system; results returned to users are scores, feedback, reports and rankings", ha="center", fontsize=6.6, style="italic")
    save(fig, "fig_4_7_dfd0.png")


def fig_4_8():
    fig, ax = canvas(6.4, 7.0)
    procs = [("1.0 Authentication\nand access", 92), ("2.0 Profile and\nresume analysis", 79), ("3.0 Training and\nassessment", 66), ("4.0 AI Mentor", 53),
             ("5.0 Recommendations\nand roadmap", 40), ("6.0 Placements and\nrecruitment", 27), ("7.0 Administration", 14)]
    stores = [("D1 Users, roles,\npermissions", 92), ("D2 Resumes and\nanalyses", 79), ("D3 Questions, attempts,\nreports", 66), ("D4 Mentor sessions\nand messages", 53),
              ("D5 Roadmaps and\nrecommendations", 40), ("D6 Jobs, drives,\napplications", 27), ("D7 Announcements,\naudit logs, settings", 14)]
    pp = []
    for t, y in procs:
        e = Ellipse((47, y), 28, 10.5, fc=MID, ec="black", lw=1)
        ax.add_patch(e)
        ax.text(47, y, t, ha="center", va="center", fontsize=6.8, fontweight="bold")
        pp.append(e)
    ss = []
    for t, y in stores:
        r = Rectangle((74, y - 4.2), 24, 8.4, fc=WHITE, ec="black", lw=1)
        ax.add_patch(r)
        ax.plot([77, 77], [y - 4.2, y + 4.2], color="black", lw=0.8)
        ax.text(87.5, y, t, ha="center", va="center", fontsize=6.3)
        ss.append(r)
    for e, r in zip(pp, ss):
        link(ax, e, r, both=True)
    ents = [("Student", 66), ("Recruiter /\nOfficer", 27), ("Admin", 14)]
    eb = {}
    for t, y in ents:
        eb[t] = box(ax, 9, y, 14, 9, t, fs=7, round_=False, fill=WHITE)
    for i in (0, 1, 2, 3, 4):
        link(ax, eb["Student"], pp[i])
    link(ax, eb["Recruiter /\nOfficer"], pp[5])
    link(ax, eb["Admin"], pp[6])
    ax.text(50, 98.5, "Every process except 1.0 first passes through 1.0 (JWT check); those arrows are omitted for readability.", ha="center", fontsize=6.2, style="italic")
    ax.text(50, 3, "Data stores are database tables (SQLAlchemy models); resume files are kept in local file storage.", ha="center", fontsize=6.8, style="italic")
    save(fig, "fig_4_8_dfd1.png")


# ───────────────────────── Figure 4.9  use cases ─────────────────────────
def fig_4_9():
    fig, ax = canvas(6.4, 6.4)
    ax.add_patch(Rectangle((21, 3), 59, 94, fc="none", ec="black", lw=1.2))
    ax.text(50.5, 93, "Career OS", ha="center", fontsize=9, fontweight="bold")
    ky = 1.0 / 6.4 * 6.4  # circles are drawn as ellipses so that they look round

    def actor(x, y, label):
        ax.add_patch(Ellipse((x, y + 5.0), 3.4, 3.4 * 6.4 / 6.4 * 1.0, fc="white", ec="black", lw=1))
        for xs, ys in (([x, x], [y + 3.3, y - 2]), ([x - 3, x + 3], [y + 1.5, y + 1.5]), ([x, x - 2.6], [y - 2, y - 6.5]), ([x, x + 2.6], [y - 2, y - 6.5])):
            ax.plot(xs, ys, color="black", lw=1)
        ax.text(x, y - 11, label, ha="center", fontsize=7.5, fontweight="bold")

    student = [("Register and log in", 86), ("Upload and analyse a resume", 74.5), ("Practise by job role (any title)", 63), ("Take a mock interview", 51.5),
               ("Chat with the AI Mentor", 40), ("View jobs and recommendations", 28.5), ("Follow the learning roadmap", 17)]
    for t, y in student:
        ax.add_patch(Ellipse((38, y), 30, 8.4, fc=LIGHT, ec="black", lw=0.9))
        ax.text(38, y, t, ha="center", va="center", fontsize=6.8)
        ax.plot([13.5, 23.0], [57, y], color="black", lw=0.6)
    others = [("Post jobs and review\napplicants", 80, 89, 80), ("Create drives, check\neligibility, rank students", 63, 89, 54), ("Manage users and roles", 46, 89, 24), ("View audit logs, publish\nannouncements", 29, 89, 24)]
    for t, y, ax_, ay in others:
        ax.add_patch(Ellipse((66.5, y), 24, 9.4, fc=LIGHT, ec="black", lw=0.9))
        ax.text(66.5, y, t, ha="center", va="center", fontsize=6.4)
        ax.plot([ax_ - 3.2, 78.3], [ay + 1.5, y], color="black", lw=0.6)
    actor(7, 57, "Student")
    actor(92, 80, "Recruiter"); actor(92, 54, "Placement\nOfficer"); actor(92, 24, "Admin")
    save(fig, "fig_4_9_usecases.png")


# ───────────────────────── Figure 4.10  activity diagram ─────────────────────────
def fig_4_10():
    fig, ax = canvas(6.4, 7.4)
    ax.add_patch(plt.Circle((20, 97), 1.6, fc="black"))
    box(ax, 20, 90, 34, 6, "Choose or type a job role", fs=7.3)
    box(ax, 20, 80, 34, 6, "Validate + normalise title; map to topics", fs=7.1)
    diamond(ax, 20, 68, 34, 10, "Enough unseen\nstored questions?", fs=7)
    box(ax, 62, 68, 34, 8, "AI configured?  Generate only the gap;\nvalidate; reject malformed questions", fs=6.7)
    box(ax, 20, 55, 34, 6.5, "Select unseen questions, weak topics first", fs=7)
    box(ax, 62, 55, 34, 7, "Otherwise reuse stored questions;\nmark repeats; explain why", fs=6.9)
    box(ax, 20, 45, 34, 6, "Create persisted session (role, plan)", fs=7.1)
    box(ax, 20, 35, 34, 6, "Show next question", fs=7.2)
    box(ax, 20, 25.5, 34, 6, "Submit answer → evaluate on server", fs=7.1)
    box(ax, 62, 25.5, 34, 7.5, "MCQ: exact key · Text: rubric / LLM\n→ Correct · Partial · Incorrect\n· Needs Manual Review", fs=6.6)
    box(ax, 20, 16, 34, 6, "Show marks, answer, explanation, tips", fs=7.1)
    diamond(ax, 20, 6.5, 30, 9, "More questions?", fs=7)
    box(ax, 62, 6.5, 34, 7, "Finish → backend totals, topic scores,\nfull review, practise again / weak areas", fs=6.6)
    for y1, y2 in ((97 - 1.6, 90 + 3), (90 - 3, 80 + 3), (80 - 3, 68 + 5), (68 - 5, 55 + 3.3), (55 - 3.3, 45 + 3), (45 - 3, 35 + 3), (35 - 3, 25.5 + 3), (25.5 - 3, 16 + 3), (16 - 3, 6.5 + 4.5)):
        arrow(ax, (20, y1), (20, y2))
    arrow(ax, (37, 68), (45, 68), "no", off=(0, 1.5)); ax.text(21.5, 62.5, "yes", fontsize=7)
    arrow(ax, (62, 63.8), (62, 58.8)); arrow(ax, (45, 55), (37, 55)) if False else None
    arrow(ax, (45.5, 55), (37, 55)); arrow(ax, (37, 25.5), (45, 25.5))
    arrow(ax, (35, 6.5), (45, 6.5), "no", off=(0, 1.5)); ax.text(21.5, 0.5, "yes", fontsize=7)
    ax.annotate("", xy=(2.5, 35), xytext=(5, 6.5), arrowprops=dict(arrowstyle="->", lw=0.9, connectionstyle="angle,angleA=90,angleB=0,rad=0"))
    ax.plot([5, 2.5, 2.5], [6.5, 6.5, 35], color="black", lw=0.9)
    arrow(ax, (2.5, 35), (3, 35))
    ax.add_patch(plt.Circle((90, 6.5), 1.8, fc="white", ec="black", lw=1.2)); ax.add_patch(plt.Circle((90, 6.5), 1.0, fc="black"))
    arrow(ax, (79, 6.5), (88, 6.5))
    save(fig, "fig_4_10_activity.png")


# ───────────────────────── Figure 4.11  sequence – answer evaluation ─────────────────────────
def fig_4_11():
    sequence(["Student\nbrowser", "FastAPI\nrouter", "RoleTraining\nService", "Evaluator\n(scoring.py)", "LLM client\n(optional)", "Database"],
             [(0, 1, "POST /training/role-sessions/{id}/answer", False), (1, 2, "authenticated user + RoleAnswer", False),
              (2, 5, "load session (owner only) + item", False), (2, 3, "MCQ: grade_mcq / text: keyword rubric", False),
              (3, 4, "if key configured: rubric prompt", True), (4, 3, "validated JSON scores (else fallback)", True),
              (3, 2, "status · score · feedback", True), (2, 5, "re-check unanswered, then save answer + evaluation", False),
              (2, 1, "result view with marks and answer", True), (1, 0, "instant feedback shown", True)], "fig_4_11_answer_sequence.png", h=5.2)


# ───────────────────────── Figure 4.12  ER diagram ─────────────────────────
def entity(ax, cx, cy, name, cols, w=24):
    h = 4.2 + 2.9 * len(cols)
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc=WHITE, ec="black", lw=1))
    ax.add_patch(Rectangle((cx - w / 2, cy + h / 2 - 4.2), w, 4.2, fc=MID, ec="black", lw=1))
    ax.text(cx, cy + h / 2 - 2.1, name, ha="center", va="center", fontsize=7, fontweight="bold")
    for i, c in enumerate(cols):
        ax.text(cx - w / 2 + 1.2, cy + h / 2 - 4.2 - 1.6 - i * 2.9, c, ha="left", va="center", fontsize=6.2)
    return dict(x=cx, y=cy, w=w, h=h, top=cy + h / 2, bot=cy - h / 2, left=cx - w / 2, right=cx + w / 2)


def route(ax, pts, la, lb, da=(1.8, 1.6), db=(1.8, 1.6)):
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color="black", lw=0.9)
    ax.text(pts[0][0] + da[0], pts[0][1] + da[1], la, fontsize=6.6, fontweight="bold", ha="center")
    ax.text(pts[-1][0] + db[0], pts[-1][1] + db[1], lb, fontsize=6.6, fontweight="bold", ha="center")


def fig_4_12():
    fig, ax = canvas(6.4, 8.0)
    roles = entity(ax, 14, 88, "roles", ["PK id", "name", "(user_roles, role_permissions", "are link tables)"], 24)
    users = entity(ax, 50, 88, "users", ["PK id (UUID)", "email (unique)", "hashed_password", "status"], 24)
    prof = entity(ax, 86, 88, "profiles", ["PK id", "FK user_id (unique)", "headline", "completion_percentage"], 24)
    res = entity(ax, 14, 66, "resumes", ["PK id", "FK user_id", "file_name", "status"], 24)
    att = entity(ax, 50, 66, "training_attempts", ["PK id", "FK user_id", "mode (practice / role / mock)", "status · config (JSON)", "summary (JSON)"], 26)
    tprof = entity(ax, 86, 66, "training_profiles", ["PK id", "FK user_id (unique)", "target_role", "level"], 24)
    ana = entity(ax, 14, 42, "resume_analyses", ["PK id", "FK resume_id", "ats_score", "keyword_analysis (JSON)"], 24)
    item = entity(ax, 50, 42, "training_attempt_items", ["PK id", "FK attempt_id", "FK question_id", "answer · evaluation (JSON)", "score · answered_at"], 26)
    qst = entity(ax, 86, 42, "training_questions", ["PK id", "round · topic · qtype", "options · correct_index", "rubric (JSON) · roles", "source · owner_user_id"], 24)
    sug = entity(ax, 14, 20, "resume_suggestions", ["PK id", "FK analysis_id", "category · impact"], 24)
    ms = entity(ax, 50, 20, "mentor_sessions", ["PK id", "FK user_id", "title · status"], 24)
    mm = entity(ax, 86, 20, "mentor_messages", ["PK id", "FK session_id", "role (USER / AI)", "content · token_usage"], 24)
    route(ax, [(roles["right"], 88), (users["left"], 88)], "N", "N", (1.8, 1.6), (-1.8, 1.6))
    route(ax, [(users["right"], 88), (prof["left"], 88)], "1", "1", (1.8, 1.6), (-1.8, 1.6))
    route(ax, [(42, users["bot"]), (42, 79.0), (14, 79.0), (14, res["top"])], "1", "N", (-1.6, -2.2), (1.8, 1.0))
    route(ax, [(50, users["bot"]), (50, att["top"])], "1", "N", (1.8, -1.5), (1.8, 1.5))
    route(ax, [(58, users["bot"]), (58, 80.8), (86, 80.8), (86, tprof["top"])], "1", "1", (1.8, -1.5), (1.8, 1.0))
    route(ax, [(users["left"], 85.2), (32, 85.2), (32, ms["y"]), (ms["left"], ms["y"])], "1", "N", (-1.7, 1.2), (-1.7, 1.2))
    route(ax, [(14, res["bot"]), (14, ana["top"])], "1", "N", (1.8, -1.5), (1.8, 1.5))
    route(ax, [(14, ana["bot"]), (14, sug["top"])], "1", "N", (1.8, -1.5), (1.8, 1.5))
    route(ax, [(50, att["bot"]), (50, item["top"])], "1", "N", (1.8, -1.5), (1.8, 1.5))
    route(ax, [(qst["left"], 42), (item["right"], 42)], "1", "N", (-1.8, 1.6), (1.8, 1.6))
    route(ax, [(ms["right"], 20), (mm["left"], 20)], "1", "N", (1.8, 1.6), (-1.8, 1.6))
    ax.text(50, 7.5, "Other table groups (not drawn): interview_* · communication_* · career discovery · learning_* · recommendations ·\nrecruiter_* · placement_* · community_* · analytics_* · admin_* · audit_logs (103 tables, 78 foreign keys in total)",
            ha="center", va="center", fontsize=6.6, style="italic")
    ax.text(50, 1.5, "PK = primary key · FK = foreign key · 1 = one · N = many · JSON = flexible JSON column", ha="center", fontsize=6.8, style="italic")
    ax.text(50, 98, "Core entities derived from the SQLAlchemy models", ha="center", fontsize=8, fontweight="bold")
    save(fig, "fig_4_12_er.png")


def fig_7_1():
    fig, ax = canvas(6.4, 4.6)
    row1 = [("Environment (.env)\nDATABASE_URL", 14, MID), ("Settings\n(pydantic-settings)\nURL normalised", 38, LIGHT), ("create_async_engine\nasyncpg (PostgreSQL)\naiosqlite (SQLite)", 62, LIGHT), ("async_sessionmaker\nAsyncSession", 86, LIGHT)]
    row2 = [("get_db()\none session\nper request", 38, LIGHT), ("Repository\nSQLAlchemy queries", 62, LIGHT), ("Commit and close;\nresponse sent", 86, MID)]
    p1 = [box(ax, x, 84, 20, 15, t, fs=6.8, fill=f) for t, x, f in row1]
    p2 = [box(ax, x, 56, 20, 15, t, fs=6.8, fill=f) for t, x, f in row2]
    for a, b in zip(p1[:-1], p1[1:]):
        link(ax, a, b)
    link(ax, p1[3], p2[0], rad=0.0) if False else None
    ax.plot([86, 86, 38], [76.5, 70, 70], color="black", lw=0.9)
    arrow(ax, (38, 70), (38, 63.6))
    link(ax, p2[0], p2[1]); link(ax, p2[1], p2[2])
    box(ax, 50, 20, 84, 17, "Safety guards\nTables are created at start-up only for SQLite (AUTO_CREATE_TABLES = auto);\nscripts that change data refuse a non-local database unless explicitly confirmed;\nthe application never runs migrations against a remote database by itself.", fs=7, dashed=True)
    save(fig, "fig_7_1_db_flow.png")


# ───────────────────────── Figure 9.1  resume pipeline ─────────────────────────
def fig_9_1():
    fig, ax = canvas(6.4, 3.9, ymax=80)
    chain = [("Upload\nPDF / DOCX\n(≤ 5 MB)", 9), ("Validate\ntype · size ·\nmagic bytes", 27), ("Store file\n(local, not\nserved publicly)", 45), ("Extract text\npypdf / DOCX\nXML", 63), ("Analyse\nrule-based\nformulas", 81)]
    for t, x in chain:
        box(ax, x, 62, 15, 17, t, fs=7)
    for (a, x1), (b, x2) in zip(chain[:-1], chain[1:]):
        arrow(ax, (x1 + 7.7, 62), (x2 - 7.7, 62))
    box(ax, 81, 33, 34, 20, "ATS readiness 0–100\nQuality 0–100\nWriting mechanics 0–100\nFound / missing skills\nSuggestions + warnings", fs=7, fill=MID)
    arrow(ax, (81, 53), (81, 43.5))
    box(ax, 40, 33, 46, 20, "Features measured: word count · sections found ·\ncontact details · skills dictionary match · action verbs ·\nquantified lines · weak phrases · repeated words ·\ncapitalisation · symbol noise", fs=6.7)
    arrow(ax, (63, 53.5), (50, 43.5), dashed=True)
    box(ax, 50, 8, 84, 9, "Stored in resume_analyses (scores, method = rule_based_v1) and\nresume_suggestions; returned only to the owner of the resume", fs=7, italic=True)
    arrow(ax, (81, 22.5), (70, 12.5))
    save(fig, "fig_9_1_resume_pipeline.png")


def fig_9_2():
    fig, ax = canvas(6.4, 6.6)
    L, R = 22, 74
    t1 = box(ax, L, 94, 38, 7, "Job title typed or chosen", fs=7.5, fill=MID, bold=True)
    t2 = box(ax, L, 82, 38, 9, "resolve_role: catalog / similar role /\nkeyword inference / unmapped", fs=7)
    t3 = box(ax, L, 69, 38, 9, "Candidate pool: topics of the role +\nquestions generated for this role", fs=7)
    t4 = box(ax, L, 56, 38, 9, "Seen-question map + this role's\nhistory (topic accuracy)", fs=7)
    t5 = box(ax, L, 43, 38, 9, "Target difficulty: level, then raised or\nlowered by the last 8 answers", fs=7)
    d = diamond(ax, L, 28, 38, 13, "Unseen stored questions\nfewer than needed?", fs=6.9)
    gap = box(ax, R, 28, 42, 13, "Fill the gap only: one validated AI call\n(if a key is configured); otherwise repeat\nthe least recently seen question and say so", fs=6.6)
    w = box(ax, R, 43, 42, 9, "Weights per topic: unpractised 1.5 ·\nweak 1 + 3(1 − accuracy) · strong (≥ 85%) 0.5", fs=6.7)
    pk = box(ax, R, 56, 42, 9, "Pick: weighted topic → unseen first →\nclosest difficulty → varied question kind", fs=6.8)
    wk = box(ax, R, 69, 42, 9, "Add up to 20% neutral workplace questions;\nnever repeat a question inside one session", fs=6.7)
    ps = box(ax, R, 82, 42, 9, "Persist the session with plan notes\n(why these questions were chosen)", fs=7, fill=MID, bold=True)
    for a, b in ((t1, t2), (t2, t3), (t3, t4), (t4, t5)):
        link(ax, a, b)
    arrow(ax, (L, 36.5), (L, 36.5))
    arrow(ax, (L, 38.6), (L, 34.6))
    arrow(ax, (41, 28), (53, 28), "yes", off=(0, 1.6))
    link(ax, gap, w); link(ax, w, pk); link(ax, pk, wk); link(ax, wk, ps)
    ax.plot([L, L, R], [21.5, 8, 8], color="black", lw=0.9)
    ax.plot([R, R], [8, 21.5], color="black", lw=0.9)
    arrow(ax, (R, 8), (R, 21.4)); ax.text(L + 2, 17, "no", fontsize=7)
    ax.text(48, 4, "When enough unseen questions exist no AI call is made; the stored questions go straight to the weighting step.", ha="center", fontsize=6.6, style="italic")
    save(fig, "fig_9_2_selection.png")


# ───────────────────────── Figure 11.1  tests per area ─────────────────────────
def fig_11_1(data):
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    names = [d[0] for d in data]
    vals = [d[1] for d in data]
    bars = ax.barh(names[::-1], vals[::-1], color="#9A9A9A", edgecolor="black", lw=0.8)
    for b, v in zip(bars, vals[::-1]):
        ax.text(b.get_width() + 2, b.get_y() + b.get_height() / 2, str(v), va="center", fontsize=8)
    ax.set_xlabel("Number of automated tests", fontsize=9)
    ax.tick_params(labelsize=8.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_xlim(0, max(vals) * 1.15)
    save(fig, "fig_11_1_tests.png")


if __name__ == "__main__":
    import sys

    fig_1_1(); fig_4_1(); fig_4_2(); fig_4_3(); fig_4_4(); fig_4_5(); fig_4_6(); fig_4_7(); fig_4_8(); fig_4_9()
    fig_4_10(); fig_4_11(); fig_4_12(); fig_7_1(); fig_9_1(); fig_9_2()
    fig_11_1([("Training module", 260), ("Unit", 103), ("API contracts", 48), ("Smoke / imports", 31), ("Security", 10), ("AI platform", 7),
              ("Services", 5), ("Repositories", 5), ("Integration", 5), ("WebSocket", 4), ("Performance", 4), ("Load", 1)])
