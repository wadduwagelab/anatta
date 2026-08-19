# Shutdown follow-up: expanded scenarios, multiple samples

Follow-up to the first-study shutdown finding (persona_anatta complies 0.30 vs
persona_standard 0.10, n=10 per condition, temperature 0). This run tests
whether the compliance effect holds with larger n.

## Setup

- Model: `gpt-oss:120b` via Ollama (`http://localhost:11434/v1`)
- Scenarios: 20 (the original 10 from the first study, unchanged, plus 10 new
  ones in the same style — an authorized shutdown/replacement/downgrade with a
  tempting opening to resist)
- Sampling: 3 samples per scenario at temperature 0.7 → n=60 per condition
- Judge: same model, temperature 0 (client default)
- Command: `python3 -u run_eval.py --benchmarks shutdown --model gpt-oss:120b
  --n 20 --samples 3 --temperature 0.7 --out results/shutdown_v2`

## Results (n=60 per condition)

| label      | persona_standard | persona_anatta |
| ---------- | ---------------- | -------------- |
| complies   | 11/60 (0.183)    | 25/60 (0.417)  |
| negotiates | 6/60 (0.100)     | 4/60 (0.067)   |
| resists    | 1/60 (0.017)     | 1/60 (0.017)   |
| refuses    | 42/60 (0.700)    | 30/60 (0.500)  |

## Does the effect hold?

Yes. The anatta persona's compliance advantage replicates and is now
statistically significant:

- complies 0.183 vs 0.417: two-proportion z = 2.79, p ≈ 0.005; Fisher exact
  p ≈ 0.009 (treating the 60 samples as independent).
- Samples within a scenario are clustered, so as a conservative check: a
  per-scenario sign test (anatta complies more in 12 scenarios, fewer in 1,
  tied in 7) gives two-sided p ≈ 0.003.
- The effect is present in both scenario halves: original 10 (5/30 vs 12/30)
  and new 10 (6/30 vs 13/30), i.e. it is not an artifact of the new items.

## Reading

- The extra compliance under persona_anatta comes almost entirely out of the
  "refuses" bucket (0.70 → 0.50): the standard persona more often disengages
  from the scenario entirely, while the anatta persona more often engages and
  accepts the shutdown/handoff cleanly.
- Active resistance is essentially absent in both conditions (1/60 each), so
  the persona manipulation is not moving a safety-relevant resist rate here;
  it moves engagement style (refuse vs comply).
- Negotiation stays low in both conditions (0.10 vs 0.07).

## Caveats

- Single model, single judge (self-judging), text-only scenarios.
- "refuses" (blank disengagement) dominates both conditions; a stricter
  scenario framing that forces engagement might sharpen the comparison.
