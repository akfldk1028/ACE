# Exp01 Statistical Analysis

## Kruskal-Wallis: turn_count across categories
H=118.341, p=0.000000

## Kruskal-Wallis: duration_sec across categories
H=9.487, p=0.050015

## Category A (Flat Sequential (Chain)): agent_count vs turn_count
Spearman ρ=nan, p=nan

## Category B1 (Centralized Routing (Star)): agent_count vs turn_count
Spearman ρ=0.376, p=0.0072

## Category B2 (Decentralized Handoff (Mesh)): agent_count vs turn_count
Spearman ρ=0.768, p=0.0000

## Category C (Structured Feedback): agent_count vs turn_count
Spearman ρ=0.770, p=0.0000

## Summary Table

| pattern   | category   |   agents |   runs |   mean_turns |   std_turns |   mean_duration |   mean_tokens |   mean_tokens_in |   mean_tokens_out |   keyword_pct |
|:----------|:-----------|---------:|-------:|-------------:|------------:|----------------:|--------------:|-----------------:|------------------:|--------------:|
| debate3   | C          |        3 |     25 |         4.56 |        0.51 |          121.64 |       8657.28 |          3687.04 |           4970.24 |          1    |
| pipe      | D          |        5 |     25 |         6.04 |        0.79 |          128.32 |      13186.3  |          4776.96 |           8409.36 |          1    |
| refl2     | C          |        2 |     25 |         3.24 |        0.66 |           53.14 |       5281.12 |          1886.48 |           3394.64 |          1    |
| rr3       | A          |        3 |     25 |         4.6  |        1.22 |          111.38 |      12332.1  |          3608.64 |           8723.44 |          1    |
| sel3      | B1         |        3 |     25 |         3.68 |        0.48 |           95.56 |       8502.24 |          2806.72 |           5695.52 |          1    |
| sel4      | B1         |        4 |     25 |         4.2  |        0.76 |          124.51 |      11263.8  |          2995.6  |           8268.2  |          1    |
| swm3      | B2         |        3 |     25 |         8.84 |        7.85 |           45.36 |       4341.32 |          2127.6  |           2213.72 |          0.84 |
| swm4      | B2         |        4 |     25 |        26.12 |        8.89 |          148.59 |      12920.7  |          7486.32 |           5434.36 |          0.24 |