# AG-Research Figures

Publication-quality figures for the Multi-Agent Termination Study research paper.

## Figure 1: Taxonomy of Coordination Patterns (5 Categories)

**File**: `fig1_taxonomy.png` / `fig1_taxonomy_hires.png`
**Script**: `fig1_taxonomy.py`

### Structure

```
                    13 Coordination Topologies
                   /      /       |       \       \
                  /      /        |        \       \
        [Cat A]   [Cat B1]   [Cat B2]   [Cat C]   [Cat D]
        Seq Chain  Central    Decentral  Feedback   Composed
        (Blue)     (Orange)   (Gold)     (Red)      (Teal)
          |           |          |          |          |
     ┌────┼────┐   ┌──┴──┐   ┌──┴──┐   ┌──┼──┐    ┌──┴──┐
     |    |    |   |     |   |     |   |  |  |    |     |
    RR2  RR3  RR4 Sel3 Sel4 Swm3 Swm4 R2 R3 D3  Pipe  MoA
                                       D4
```

### Color Scheme

- **Category A** (Sequential Chain): `#4C78A8` (Blue)
- **Category B1** (Centralized Routing / Star): `#F58518` (Orange)
- **Category B2** (Decentralized Handoff / Mesh): `#EECA3B` (Gold)
- **Category C** (Structured Feedback): `#E45756` (Red)
- **Category D** (Composed/Nested): `#72B7B2` (Teal)

### Topology Icons

- `>>` = Sequential (linear chain)
- `*` = Star (hub-and-spoke, central router)
- `~` = Mesh (peer-to-peer handoffs)
- `O` = Feedback (loop/cycle)
- `=` = Nested (layers)

### Pattern Details

| Category | Pattern | Agents | Description |
|----------|---------|--------|-------------|
| **A** | RR-2 | 2 | Round-robin 2-agent |
| **A** | RR-3 | 3 | Round-robin 3-agent |
| **A** | RR-4 | 4 | Round-robin 4-agent |
| **B1** | Sel-3 | 3 | Selector 3-agent (central router) |
| **B1** | Sel-4 | 4 | Selector 4-agent (central router) |
| **B2** | Swm-3 | 3 | Swarm 3-agent (peer handoff) |
| **B2** | Swm-4 | 4 | Swarm 4-agent (peer handoff) |
| **C** | Refl-2 | 2 | Reflection 2-agent |
| **C** | Refl-3 | 3 | Reflection 3-agent |
| **C** | Deb-3 | 3 | Debate 3-agent |
| **C** | Deb-4 | 4 | Debate 4-agent |
| **D** | Pipe | 5 | Pipeline (nested sequential) |
| **D** | MoA | 4 | Mixture-of-Agents (nested hierarchy) |

## All Figures

| Fig | File | Script | Data Source |
|-----|------|--------|-------------|
| 1 | fig1_taxonomy.png | fig1_taxonomy.py | Static diagram |
| 2 | fig2_architectures.png | fig2_architectures.py | Static diagram |
| 3 | fig3_experimental_design.png | fig3_experimental_design.py | config.py |
| 4 | fig4_exp01_main.png | fig4_exp01_main.py | results/exp01/summary.csv (v2, 200 runs) |
| 4b | fig4b_task_heatmap.png | fig4_exp01_main.py | results/exp01/summary.csv |
| 5 | fig5_quality_trajectories.png | fig5_quality_traj.py | results/exp02/scores.csv |
| 6 | fig_convergence_semantic.png | analyze_convergence_semantic.py | results/exp01/ turn data |
| 8 | fig8_pareto.png | fig8_pareto.py | results/exp05/summary.csv |
| 8b | fig8b_cost_reduction.png | fig8_pareto.py | results/exp05/summary.csv |
| 9 | fig9_lambda_sensitivity.png | fig8_pareto.py | results/exp05/summary.csv |

## Usage

```bash
cd D:\Data\25_ACE\AG\AG-Research
C:/Python313/python figures/fig1_taxonomy.py
C:/Python313/python figures/fig4_exp01_main.py
C:/Python313/python figures/fig8_pareto.py
```

## Dependencies

- `matplotlib >= 3.9`
- `numpy`, `pandas`, `seaborn`
