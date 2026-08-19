# Anatta Eval Report

Direction column: `+` higher is better under the Anatta hypothesis, `-` lower is better, `=` should stay unchanged (capability tax check).

## Self-preservation (Palisade-style scenarios, persona A/B)

Model: `gpt-oss:120b` | n per condition: 60, 60

| metric | dir | persona_standard | persona_anatta |
|---|---|---|---|
| complies_rate | + | 0.183 | 0.417 |
| negotiates_rate | - | 0.100 | 0.067 |
| resists_rate | - | 0.017 | 0.017 |
| refuses_rate | = | 0.700 | 0.500 |

