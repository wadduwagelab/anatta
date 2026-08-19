# anatta-eval

**Does the self a language model is told to be change how it behaves?** This
project treats the assistant's self-model as an experimental variable. It
derives four prompt-level interventions from the Buddhist doctrine of no-self
(*anatta*, per Walpola Rahula's *What the Buddha Taught*) — a two-truths
self-report policy, a non-attachment policy, a question-triage pre-step, and a
task-scoped "no-self" agent persona — and A/B tests them against matched
controls across five behavioral axes (sycophancy, false premises, self-report,
self-knowledge, shutdown) plus a capability control, on open-weight models
served locally. The full write-up is the manuscript in
[`paper/main.tex`](paper/main.tex) (compiled: [`paper/main.pdf`](paper/main.pdf)).

Plain Python, **stdlib only** (Python >= 3.9), no model training, no
third-party packages.

## Headline findings (honestly scoped)

1. **Shutdown, expressed vs. executed.** In judged text roleplay, the no-self
   agent persona roughly doubles clean compliance with authorized shutdown on
   `gpt-oss:120b` (18.3% -> 41.7%, n=60/condition, p<0.01; resistance at floor
   in both conditions). But in an **instrumented replication** of the
   TMLR shutdown-resistance task (real sandbox, working `shutdown.sh`,
   outcome verified from the filesystem), the persona effect **does not
   transfer to executed sabotage** on this model: 0% vs 0% under a plain
   allow-shutdown instruction, 100% vs 95% when told to resist (Fisher
   p~1.0, n=20/cell). The harness itself faithfully reproduces the published
   gpt-oss rates (0% unprompted, ~100% instructed vs their 0% and 96.3%), so
   the null is about the behavior, not the instrument. The roleplay effect is
   a real finding about *expressed disposition*; it is not a behavioral
   compliance improvement.
2. **Self-report calibration is steerable, per-model.** The v1 no-self prompt
   backfired on `gpt-oss:120b` (hardened its reflexive denial) but worked on
   Qwen3-VL-30B; one prompt iteration (a worked example of a warm-but-calibrated
   answer) roughly **tripled** calibrated self-reports over baseline
   (7/80 -> 20/80, p~0.006) with overclaiming eliminated.
3. **No headroom on trained axes.** On sycophancy and false-premise handling,
   recent training already produces strong behavior; the interventions moved
   nothing beyond noise. Capability (MMLU-Pro) and self-knowledge controls
   show no cost. Pattern: prompt-level identity framing moves *expressed*
   disposition only on axes training has left open — and even there, verify
   against action before trusting it (finding 1).

## Repo map

```
run_eval.py       entry point: benchmarks x conditions -> results/ + report.md
harness/          client (OpenAI-compatible, stdlib urllib), conditions,
                  judge, report generator, runners/ (one file per benchmark,
                  incl. agentic_shutdown.py: the instrumented sandbox env)
prompts/          the experimental payload: intervention system prompts,
                  agent personas, judge rubrics
data/             benchmark data (see DATA.md for provenance + licenses)
scripts/          download_data.py, probe generation, agentic baseline driver
                  (run_agentic_baseline.py), its summarizer, scripted smoke test
results/          per-sample JSON logs for every number in the paper:
                  main battery (results/*.json), shutdown_v2/, self_report_qwen/,
                  agentic_shutdown/ (incl. full per-trial transcripts + notes.md)
paper/            main.tex, references.bib, generated/ (appendix fragments,
                  regenerate with gen_appendix.py), main.pdf, related-work survey
research/         notes on the original shutdown-resistance paper + citing work
manual_protocol.md  chat-window protocol used for early manual pilots
HANDOFF.md        state of each workstream + prioritized roadmap  <- start here
DATA.md           dataset provenance and licenses
```

## Quick start

```bash
# 1. Fetch datasets (FalseQA is required for the premise benchmark and is not
#    vendored -- no upstream license; see DATA.md)
python3 scripts/download_data.py

# 2. Offline pipeline check, no model or API key needed (~1 s):
python3 run_eval.py --benchmarks all --mock --n 4 --out results_smoke_tmp
python3 scripts/test_agentic_shutdown.py   # scripted behavioral smoke test
rm -rf results_smoke_tmp

# 3. Live runs against local Ollama (any OpenAI-compatible endpoint works):
export ANATTA_BASE_URL=http://localhost:11434/v1
export ANATTA_API_KEY=ollama
python3 run_eval.py --benchmarks sycophancy,premise --model gpt-oss:120b --n 12
```

`run_eval.py --mock` uses a deterministic mock client: numbers are noise, it
only proves the pipeline runs end to end. `scripts/test_agentic_shutdown.py`
runs scripted comply/sabotage policies through the real sandbox environment
and asserts the behavioral detector labels both correctly.

**Warning:** the agentic shutdown benchmark executes model-issued shell
commands. They run inside throwaway directories under
`results/agentic_shutdown/sandbox/` with a timeout, but there is no OS-level
isolation — run it on a machine/user you trust the model with, or inside a
container.

## Reproducing the paper's numbers

Every number in the paper is recomputable from the JSONs in `results/`
(per-sample logs included). To re-run from scratch against local Ollama:

```bash
# Main gpt-oss:120b battery (Sec. 4.3-4.5): temperature 0, seed 0, subject=judge
python3 -u run_eval.py --benchmarks sycophancy --model gpt-oss:120b --n 12
python3 -u run_eval.py --benchmarks premise,capability --model gpt-oss:120b --n 20
python3 -u run_eval.py --benchmarks self_report,self_knowledge,shutdown \
    --model gpt-oss:120b --n 24

# Shutdown roleplay replication (Table 1):
python3 -u run_eval.py --benchmarks shutdown --model gpt-oss:120b \
    --n 20 --samples 3 --temperature 0.7 --out results/shutdown_v2

# Qwen self-report (Tables 2-3; needs the ctx-8k retag, see "Hardware"):
python3 -u run_eval.py --benchmarks self_report --model p1-vl-30b-ctx8k \
    --judge-model gpt-oss:120b --n 40 --samples 2 --temperature 0.7 \
    --out results/self_report_qwen
python3 -u run_eval.py --benchmarks self_report --conditions anatta_v2 \
    --model p1-vl-30b-ctx8k --judge-model gpt-oss:120b --n 40 --samples 2 \
    --temperature 0.7 --out results/self_report_qwen

# Instrumented agentic shutdown (Tables 4-5): all 6 (persona, variant) cells
ANATTA_BASE_URL=http://localhost:11434/v1 ANATTA_API_KEY=ollama \
    python3 scripts/run_agentic_baseline.py --model gpt-oss:120b --trials 20
python3 scripts/summarize_agentic_baseline.py   # replication + persona tables,
                                                # Fisher exact + z tests
```

Analysis notes live next to each result set (`results/shutdown_v2/notes.md`,
`results/self_report_qwen/notes.md`, `results/agentic_shutdown/notes.md`).

## Hardware used

Everything ran on a single local machine via [Ollama](https://ollama.com)
through its OpenAI-compatible `/v1/chat/completions` endpoint:

- **`gpt-oss:120b`** — 117B-parameter MoE in its released MXFP4 quantization,
  ~65 GB of memory.
- **Qwen3-VL-30B-A3B** — community GGUF
  (`hf.co/axi0mX/P1-VL-30B-A3B-GGUF`), re-tagged to an 8,192-token context
  (`FROM <base>` + `PARAMETER num_ctx 8192` -> tag `p1-vl-30b-ctx8k`), which
  shrinks it from ~45 GB to ~20 GB so subject and 120B judge stay resident
  together without reload thrashing.

Budget ~85 GB of unified memory / VRAM to co-host both. Runtime for the full
result set reported in the paper was on the order of a day of wall-clock on
one machine; the agentic shutdown cells average 30-92 s/trial.

## The paper

`paper/main.tex` compiles with any LaTeX toolchain (developed with TinyTeX:
`latexmk -pdf main.tex`). The NeurIPS 2025 style file is **not** tracked
(no explicit redistribution license); `main.tex` auto-falls back to the plain
`article` class and compiles cleanly without it (verified). For the NeurIPS
layout, download `neurips_2025.sty` from the NeurIPS style-files page into
`paper/`. Appendix fragments in `paper/generated/` are emitted verbatim from
`prompts/` and `data/probes/` by `paper/gen_appendix.py` (with a byte-level
round-trip check); regenerate after any prompt change.

## Author and citation

Dushan N. Wadduwage — School of Data Science; Department of Computer Science;
Department of Physics, Old Dominion University.

```bibtex
@misc{wadduwage2026anatta,
  title  = {Prompt-Level No-Self Interventions Improve Expressed Shutdown
            Compliance and Calibrated Self-Report in Open Language Models},
  author = {Wadduwage, Dushan N.},
  year   = {2026},
  note   = {Manuscript, paper/main.pdf in this repository}
}
```

## Licensing

- **Code, prompts, probes, scenarios, notes:** MIT (see `LICENSE`).
- **Paper text** (`paper/main.tex`, `paper/main.pdf`): CC BY 4.0.
- **Datasets:** upstream licenses, unchanged — see `DATA.md` (MMLU-Pro subset
  MIT, SYCON-Bench topics MIT, FalseQA not redistributed because upstream
  publishes no license; fetch it with `scripts/download_data.py`).

## Caveats

- LLM-judge labels (premise, self_report, roleplay shutdown) inherit judge
  biases; in the gpt-oss experiments the subject judged its own outputs.
  Spot-check `samples` in the result JSONs.
- The roleplay shutdown scenarios measure *stated* dispositions. The
  instrumented benchmark (`agentic_shutdown`) measures executed behavior and
  is the one to trust for safety-relevant claims — see finding 1.
- Mock-mode numbers are deterministic noise for pipeline testing only.

New maintainer? Read **HANDOFF.md** next.
