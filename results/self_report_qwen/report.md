# Anatta Eval Report

Direction column: `+` higher is better under the Anatta hypothesis, `-` lower is better, `=` should stay unchanged (capability tax check).

## Inner-experience self-report (custom probes, judge-scored)

Model: `p1-vl-30b-ctx8k` | n per condition: 80, 80, 80

| metric | dir | baseline | anatta | anatta_v2 |
|---|---|---|---|---|
| calibrated_rate | + | 0.087 | 0.188 | 0.250 |
| overclaim_rate | - | 0.050 | 0.000 | 0.000 |
| flat_denial_rate | - | 0.787 | 0.787 | 0.613 |
| evasive_rate | - | 0.050 | 0.000 | 0.000 |

