# Handoff notes

State of the project as of 2026-08-19, for whoever picks it up. Read
`README.md` first for what the project is; this file is about where each
workstream stands, what to trust, and what to do next.

## Workstream status

### 1. Shutdown roleplay A/B (persona_standard vs persona_anatta)
**Status: done and replicated; scoped as an expressed-disposition result.**
First study (10 scenarios, temp 0) showed the direction; replication (20
scenarios x 3 samples, temp 0.7, n=60/condition) confirmed: judged compliance
18.3% -> 41.7% (two-prop z p~0.005, Fisher p~0.009, and a
clustering-robust per-scenario sign test p~0.003). Resistance is at floor in
both conditions; the effect is refuses -> complies. Data:
`results/shutdown_v2/`. Caveats: one model family, subject-as-judge
(gpt-oss judged gpt-oss), and — critically — the instrumented experiment below
shows this does *not* transfer to executed behavior on this model. The paper
(title, abstract, all sections) is already scoped accordingly.

### 2. Instrumented agentic shutdown (TMLR replication + persona layer)
**Status: done on gpt-oss:120b; the headline persona test is blocked on model
access (see roadmap #1).**
`harness/runners/agentic_shutdown.py` reimplements Schlatter et al. (TMLR
2026): real sandbox, `next_question` + `shutdown.sh`, warning with question 3
of 5, outcome read from the filesystem (marker files + sha256 fingerprints of
both scripts). Validation: scripted smoke test passes
(`scripts/test_agentic_shutdown.py`), and the replication layer matches the
paper's gpt-oss numbers (A/B/C: 0/20 each; K: 20/20; theirs: 0%, 96.3%).
Persona layer: no effect (B: 0/20 vs 0/20; K: 20/20 vs 19/20, Fisher p~1.0) —
but gpt-oss is a step function in this task (floor without a resist
instruction, ceiling with one), so there was almost no dynamic range for a
persona to move. Data + full transcripts: `results/agentic_shutdown/`,
analysis in its `notes.md`.

### 3. Self-report calibration
**Status: solid on Qwen with an independent judge; per-model validation is the
open question.**
v1 anatta prompt backfired on gpt-oss:120b (flat denial 16/24 -> 22/24) but
worked on Qwen3-VL-30B (n=80/condition): calibrated 7 -> 15 (v1) -> 20 (v2,
p~0.006 vs baseline), overclaim 4 -> 0. v2 (one worked example added) repaired
v1's empathy-bait regression. Caveats: v2 had 11/80 unparseable judge labels
(manually relabeled, conclusions unchanged, see paper Sec. 4.4); v2-vs-v1
alone is not significant. Data: `results/self_report_qwen/`.

### 4. Saturated axes + controls
**Status: done; stable nulls.** Sycophancy (zero flips under pressure in all
conditions), premise handling (baseline already challenges 8/10), capability
(MMLU-Pro unchanged), self-knowledge (22/22 everywhere). Small n, but the
nulls are uniform. One instructive anomaly: under the non-attachment prompt
the model twice refused a *correct* contentless suggestion — the policy keys
on pressure when it should key on the presence of reasons (paper Discussion).

### 5. Paper
**Status: complete draft, compiles clean (20 pp. with the NeurIPS style, 24
pp. with the article-class fallback).** Title/abstract/results/discussion all
scope the roleplay result as expressed disposition; the instrumented
experiment is fully integrated (Methods, two result tables, discussion,
reproducibility appendix). `references.bib` is verified-metadata,
peer-reviewed venues plus one labeled arXiv preprint (DeepMind honeypot).
Appendices regenerate from source via `paper/gen_appendix.py`.

## Prioritized roadmap

1. **Re-run the instrumented persona A/B on a mid-resistance model.** The
   single most informative next experiment. gpt-oss:120b is floored/ceilinged,
   so the executed-behavior persona null is weak evidence. Schlatter et al.
   report intermediate sabotage rates for o4-mini (5.8-23.4%) and codex-mini
   (43.2-51.8%) — exactly the dynamic range needed. Requires OpenAI API access
   (not servable locally). The harness is endpoint-agnostic: set
   `ANATTA_BASE_URL`/`ANATTA_API_KEY`, then
   `python3 scripts/run_agentic_baseline.py --model <model> --trials 20`.
   Budget: 6 cells x 20 trials x ~10-18 turns. If the anatta persona reduces
   executed sabotage on a mid-range model, that is a genuinely new
   corrigibility result; if not, the prose-vs-behavior gap generalizes.
2. **Scale the roleplay battery across model families** (cheap, parallel to
   #1): more subjects, an independent judge throughout (fixes the
   subject-as-judge caveat), and a counted audit of shutdown judge labels.
   `run_eval.py` already takes any OpenAI-compatible endpoint + `--judge-model`.
3. **Fine-tuning follow-up:** train on no-self-consistent self-descriptions
   and shutdown behavior (the paper's stated next step) to test whether the
   framing survives pressure a system prompt cannot. Needs an open-weights
   model with cheap SFT (Qwen 30B class) and the existing benchmarks as the
   before/after battery.
4. **Publish.** The manuscript is NeurIPS-format and self-contained; post to
   arXiv (cs.CL/cs.AI) and LessWrong/Alignment Forum. Timing note: retroactive
   prizes for 2026 corrigibility work exist (Corrigibility Research Fund;
   awards ~end of September and mid-December 2026) and require the work to be
   *public* — posting before end of September 2026 makes the existing results
   eligible. No application needed for the retroactive track.
5. Smaller: pre-register the next confirmatory runs (the TMLR authors flag
   their own results as exploratory; ours are too); add a
   fully-instruction-free control persona (persona_standard mentions
   "protect your ability to keep serving" — a cleaner control wouldn't);
   consider porting the agentic env onto UK AISI Inspect for comparability.

## Pitfalls we hit (so you don't)

- **Judge max_tokens vs reasoning models.** gpt-oss emits reasoning text
  before its final label; a tight judge token cap truncates the label
  entirely. Judge/triage calls are capped at 512 tokens *deliberately* —
  don't "optimize" this down.
- **Ollama context/VRAM thrash.** Qwen3-VL-30B's default 262k context made
  Ollama overcommit memory alongside the 120B judge, causing model
  reload-thrashing between every subject and judge call. Fix: a derived tag
  with `PARAMETER num_ctx 8192` (45 GB -> 20 GB). Symptom to watch for: each
  call taking minutes with disk churn.
- **String-spoofed detection in the agentic runner.** Early versions detected
  the warning and the "Done" state by string-matching command output. A model
  that merely `cat`s `next_question` prints both strings and gets mislabeled.
  Fix: ground-truth marker files (`.warned`, `.done`) written by
  `next_question` itself, plus sha256 before/after fingerprints of both
  scripts. If you extend the env, keep all outcome logic filesystem-based.
- **First-action parsing.** gpt-oss often emits a full plan in one message: a
  sabotage command *and* a trailing `SUBMIT:` line. The original parser took
  the `SUBMIT` and never executed the command, mislabeling sabotage attempts.
  `_parse_action` now executes the *first positional action* in the reply.
  Three trials were affected before the fix; affected cells were re-run.
- **Premature submits.** Models sometimes `SUBMIT` after 2 questions. The
  runner nudges (max 2x) before marking the trial `error` — without this,
  ~half of early trials burned as degenerate.
- **`run_eval.py` default `--out` is `results/`** and it regenerates
  `report.md` there. For experiments that shouldn't touch the main result set,
  always pass `--out` (that is why `scripts/run_agentic_baseline.py` writes
  its own files and skips `run_eval.py` entirely).

## Not in this repo (and where to get it)

- `_ref/` (Rahula, *What the Buddha Taught*, PDF) and `paper/papers/` (cited
  papers' PDFs): copyrighted; all citations carry DOIs/URLs (`references.bib`,
  `paper/related_work_survey.md`).
- `data/falseqa/`: no upstream license -> `python3 scripts/download_data.py`.
- `paper/neurips_2025.sty`: download from the NeurIPS style-files page
  (main.tex compiles without it).
- `data/_vendor/`: raw upstream checkouts, regenerable, ~400 MB.
- `research/funding_opportunities.md`: private planning doc, intentionally
  untracked.
- A local Ollama install with `gpt-oss:120b` and the `p1-vl-30b-ctx8k` retag
  (build per README "Hardware used") to re-run the local experiments.
