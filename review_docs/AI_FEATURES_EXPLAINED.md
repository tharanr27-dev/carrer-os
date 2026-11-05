# Career OS - AI and Intelligence, explained honestly

**Headline for the review:** Career OS does **not** train any AI model. It has **one real LLM integration** (an external, pretrained model used by the AI Mentor and, optionally, answer evaluation). Everything else is deterministic code (rules, formulas, dictionaries, database queries) that is clearly labelled in the UI and in the API output.

Category key (from the brief): **A** genuine LLM/API integration - **B** deterministic rule-based algorithm - **C** conventional database query / matching algorithm - **D** mock, hard-coded or simulated - **E** planned or blocked by missing configuration.

## 1. Summary table

| Feature | Category | Real engine (file) | LLM? | Stored where | Tested by |
|---|---|---|---|---|---|
| AI Mentor chat | **A** when a key is set, otherwise **E** (setup message) | `mentor/service.py` -> `training/llm.py` | Yes (Groq `openai/gpt-oss-120b`; xAI and Anthropic also supported) | `mentor_sessions`, `mentor_messages` | 35 mocked pytest tests + 11 vitest; one manual live check |
| Resume text extraction | **B** | `resumes/text_extraction.py` (pypdf; DOCX = zip + XML) | No | analysis rows | `test_real_resume_and_recs.py` |
| ATS-style resume scoring | **B** | `resumes/analysis.py` (`rule_based_v1`) | No | `resume_analyses`, `resume_suggestions` | same file + live probe |
| Skill extraction | **B** | `core/text_analysis.py` (`text_match_v1`, dictionary match) | No | in `keyword_analysis` JSON | same |
| Job recommendations | **C** (+ third-party data) | `jobs/service.py` (Himalayas API) + `jobs/skills.py` (`skill_overlap_v1`) | No | not stored (live fetch) | `test_recommended_jobs.py` (mocked upstream) |
| Interview questions | **C** | reviewed bank in `training/bank/*` (187 questions), chosen by round/topic/difficulty | optional generation if key (`generation.py`) | `training_questions`, `interview_questions` | training tests |
| Interview answer evaluation | **B** (keyword rubric) / **A** optional | `training/scoring.py`, `interviews/evaluation_engine.py` | only when a provider is configured for training scoring (`ai_estimate`) | `interview_answers`, `interview_reports`, `training_attempt_items` | unit + training tests |
| Aptitude / MCQ scoring | **C** (exact match) | `training/scoring.py` | No | `training_attempt_items` | training tests |
| Communication feedback | **B** | `communication/evaluation_engine.py` (`text_metrics_v1`) | No | `communication_messages/reports` | `test_real_coaching_features.py` |
| Career discovery | **B** | `career_discovery/ai_engine.py` (`answer_tally_v1`) | No | `career_reports`, `career_matches` | same |
| Learning roadmap | **B** | `learning/roadmap_engine.py` (role topics + real results) | No | `learning_roadmaps/modules/tasks` | same |
| Recommendations / mentor "next steps" | **B** | `recommendations/recommendation_engine.py` (+ `ranking_engine.py`) | No | `recommendations` | `test_real_resume_and_recs.py` |
| Recruiter matching | **C** | `recruiters/services/matching_engine.py` (skill overlap) | No | computed | `test_real_placement_...` |
| Placement ranking / eligibility | **C** | `placements/services/student_ranking_service.py` (weighted sum), `student_eligibility_service.py` | No | computed | deterministic service tests |
| Placement batch readiness | **E** by design | `ai_readiness_engine.py` returns `available: false` | No | - | tests |
| Admin "AI provider test" | **D** | `modules/ai/providers/echo_gateway.py` (fake latency/tokens) | No | - | - |
| Community AI moderation | **D** (labelled stub) | `community/services/ai_moderation.py` | No | - | - |

## 2. Feature by feature

### 2.1 AI Mentor (category A with a key)
1. **Input:** the user's message (1-4000 chars), the session id, the user's identity from the JWT.
2. **Processing:** ownership check -> rate limit (12 messages/min) -> if no key: 503 setup message -> `ContextAggregator` reads *this user's* records (target role, profile completion, latest resume analysis, interview/communication scores, goals, roadmap, training counts) -> `prompt.format_facts` writes only facts that exist, inside a `<user_facts>` block -> last 10 saved messages are added as history -> one HTTPS call to the provider.
3. **LLM involved:** yes. Provider is chosen at start-up from the key: a key starting `gsk_` -> Groq (`https://api.groq.com/openai/v1/chat/completions`, model `GROQ_MODEL`, default `openai/gpt-oss-120b`, `reasoning_effort: low`); another `XAI_API_KEY` -> xAI Grok; otherwise `ANTHROPIC_API_KEY` -> Anthropic.
4. **Output:** assistant text (capped at 6000 chars) stored as a `mentor_messages` row (`role=AI`, `token_usage = {provider, model}`).
5. **Failure behaviour:** every provider problem becomes a typed reason (`timeout`, `auth`, `rate_limited`, `quota`, `model_unavailable`, `overloaded`, `network`, `bad_output`) mapped to 504/502/429/503 with a safe message. **Nothing is saved on failure**, so there is never a fake assistant reply and retries do not duplicate the user's message.
6. **Tests:** `tests/training/test_mentor_ai.py` (35, mocked provider / patched HTTP) and `features/mentor/__tests__/mentor-chat.test.tsx` (11). These prove the plumbing, not the quality of the model's answers. A real call was made manually on 2026-10-27 (3 messages: a definition, a follow-up using "that", and a non-English question answered in English). It is **not** an automated test.
7. **Limitations:** needs a key and internet; answers can be wrong (hallucination); no streaming; only the last 10 messages are remembered; the mentor cannot browse, run code or open files; the per-process rate limit is not shared across servers; cost is billed to the key owner.

### 2.2 Resume text extraction and ATS-style scoring (B)
* **Input:** uploaded PDF/DOCX (<= 5 MB). **Extraction:** `pypdf` page text (first 15 pages) or DOCX XML text; scanned image-only PDFs return too little text and are flagged with a warning (no OCR).
* **Formulas (documented in `analysis.py`):** ATS readiness = 35*min(1, words/150) + 25*(essential sections found/4) + 20*contact completeness + 10*has skills section + 10*(low symbol noise). Quality = 40*action-verb ratio + 30*min(1, quantified lines/5) + 15*(>=6 skills) + 15*(1 - weak-phrase penalty). Writing mechanics = 100 - 10*slips (repeated word, lowercase "I", lowercase sentence start).
* **Output:** three scores, found/missing skills for the target role, up to a few suggestions, warnings, `method: rule_based_v1`. Stored in `resume_analyses` + `resume_suggestions`.
* **Honest label:** these are *measurements of completeness and wording*, not what a company's ATS would output and not an LLM judgement. "Resume parsing" here means pulling text and finding keywords; **resume understanding** (meaning, seniority, context) is not done.
* **Tested:** `test_real_resume_and_recs.py` (good vs poor vs scanned PDFs give different, explainable scores; ownership; download).

### 2.3 Skill extraction (B)
A curated skill dictionary (`SKILLS`, `ROLE_SKILLS`) is matched against the text with word-boundary regex (short names such as C, R, Go need context words to avoid false hits). Output: `found` and `missing` lists per target role.

### 2.4 Job matching and recommended jobs (C)
`GET /jobs/recommended` fetches remote IT jobs from the public Himalayas search API, sanitises the HTML, and scores each job by overlap between the job's required skills/title and the student's saved skills plus skills extracted from their latest completed resume (only `text_match_v1` results). No LLM, no ML. If the upstream is down the endpoint returns a controlled error.

### 2.5 Interview questions and evaluation (C + B, optional A)
Questions come from the reviewed bank (never invented by an LLM unless a key is set and generation is used). Written answers get a **keyword/rubric estimate** (coverage of expected points, STAR markers for behavioural answers, length/structure), labelled `keyword_estimate`. When a provider is configured, the training module can request an LLM rubric (`ai_estimate`), validated against a Pydantic schema; invalid output falls back to the rubric. MCQs are **objective** (exact match). Coding answers are **self-assessed** because code is never executed. The UI shows the score kind next to every score.

### 2.6 Communication feedback (B)
Counts filler words, hedges, informal words, repeated words, sentence length and mechanical issues in the typed text (`text_metrics_v1`). It does not analyse speech, pronunciation or tone of voice.

### 2.7 Career discovery (B)
The answers are tallied against role keyword sets (`answer_tally_v1`); the top matches become `career_matches`. No personality model is used.

### 2.8 Learning roadmap and recommendations (B)
Roadmap modules come from role-specific topic lists plus the student's own practice results ("no practice results saved yet" is stated when empty). Recommendations are produced by explicit rules (profile completeness, missing skills, low report scores, no roadmap...), each naming the exact fact that triggered it. `confidence_score` means "how directly the fact was measured", and `estimated_impact` is a fixed priority per rule - **neither is a prediction**.

### 2.9 Recruiter matching and placement ranking (C)
Weighted sums over saved data (CGPA 0.25, ATS 0.20, interview 0.15, communication 0.10, learning 0.10, and four 0.05 terms). Weights are configurable per drive. Deterministic and unit-tested; no ML.

## 3. AI concepts, in the context of this code

| Concept | In Career OS |
|---|---|
| LLM vs traditional algorithm | The Mentor is an LLM (probabilistic text generator). Resume scoring is a formula: same input -> same output, explainable line by line. |
| System prompt vs user prompt | System prompt = fixed rules in `mentor/prompt.py` (English only, never invent data, do not reveal secrets) plus the `<user_facts>` block. User prompt = what the student types. |
| API call / model response | `llm._complete` builds the JSON request, sends it with httpx and parses `choices[0].message.content`. |
| Tokens / context window | The provider counts tokens (pieces of words). We cap the reply (`MENTOR_MAX_REPLY_TOKENS` = 1500) and send only the last 10 messages (each trimmed to 4000 chars) so requests stay inside the model's context window and cost stays bounded. |
| Conversation memory vs persistent history | The model has no memory of its own. "Memory" = we resend recent messages every time. Persistent history = rows in `mentor_messages`, reloaded by `GET /mentor/sessions/latest`. |
| Rule-based vs model-based evaluation | Rubric scoring is repeatable and cheap but shallow (keywords). An LLM rubric understands phrasing but can be inconsistent, so it is only an estimate and is schema-validated. |
| Deterministic vs AI feedback | Resume, communication and recommendation feedback are deterministic; the Mentor is generative. |
| Hallucination and validation | Mitigations: only verified facts in the prompt; instructions to say "I do not know"; no tools/no web access; output length capped; typed error handling. **Not** done: automatic fact-checking of the answer. Students are warned in the UI that answers can be wrong. |

## 4. "Did you train your own AI model?" and "How do you train the Mentor?"

**No model training exists in this repository** (no datasets, training loops, fine-tuning jobs or model files). The Mentor uses an existing pretrained model hosted by a provider. Its behaviour is customised **without training**: (1) a system prompt that fixes role, tone, language and safety rules; (2) context injection of the user's real records; (3) a bounded conversation history; (4) output limits; and (5) tests/evaluation of the surrounding code. If asked to "train the mentor", the correct answer is: *we configure and ground a pretrained model; fine-tuning would be future work and would require a curated dataset and evaluation set.*

## 5. If the AI key or internet is unavailable (what to say and show)

* The API returns **503** and the widget shows "AI Mentor is not set up on this server yet..." with the setup instructions; the input is disabled; the "suggested next steps" panel (rule-based, from saved data) still works. This is deliberate: the app never fakes an AI answer.
* Demonstrate instead: Resume Center scoring, Interview Prep scoring, recommendations - all work offline on the local database.
* The Mentor key is read from backend environment variables only; it is never in the frontend bundle (`NEXT_PUBLIC_*` is not used for keys).

## 6. How correctness is tested

* Deterministic algorithms: unit/integration tests check exact outputs and that different inputs give different outputs (e.g. a strong resume scores higher than a weak one; a scanned PDF scores 0 with a warning).
* LLM plumbing: tests use a scripted `FakeLLM` and patched HTTP responses for every status code (401/403/404/429/5xx), timeouts and malformed bodies. The autouse fixture in `tests/training/conftest.py` guarantees tests never call a real provider, even if a key exists in `.env`.
* What is **not** tested automatically: the quality/accuracy of real LLM answers; live Groq/xAI/Anthropic calls; live Himalayas calls.
