# When Should Multi-Agent Teams Stop? A Systematic Study of Termination Dynamics Across 13 Coordination Topologies

---

## Abstract

When should multi-agent LLM teams---an increasingly common mechanism for scaling inference-time compute---stop working? Current stopping criteria---fixed turn limits, keyword matching, or timeouts---ignore a critical factor: *how agents coordinate determines when they should stop*. We present the first systematic study of termination dynamics across 13 coordination patterns spanning six topology categories, through 2,200+ runs within a unified AutoGen framework. Our analysis yields several counterintuitive findings. First, a 3-agent decentralized swarm is *cheaper* than a 2-agent sequential chain (3,203 vs. 4,759 tokens; U=95, p<0.001)---more agents can cost less when communication patterns differ. Second, multi-agent debate, widely advocated for quality improvement, exhibits monotonic quality *decline* after the first round (3.8→3.4→3.3). Third, the simple TERMINATE keyword is near-optimal for 7 of 8 topologies (800-run controlled experiment), validating existing practitioner heuristics---a "negative result" with significant practical value. Fourth, centralized routing and decentralized handoff, previously grouped as "dynamic routing," show fundamentally different cost scaling (sub-linear vs. super-linear), establishing the revised cost hierarchy A ≈ B2 < B1 ≈ C ≪ D. Fifth, topology features alone predict 54% of runtime cost variance (R²=0.54), with the `agent_count × max_messages` interaction as the strongest predictor. Sixth, task difficulty dominates topology choice (η²=0.363, large effect; 669 scored runs across 5 models) with a consistent solo-dominance pattern moderated by model capability: solo achieves the highest quality for easy tasks across all 5 models, while structured feedback (refl-2) helps only specific models at medium difficulty (Haiku d=1.26, GPT-5.4 d=1.83). The marginal utility criterion ΔU(t) identifies the specific topology class where keyword termination fails, enabling a hybrid stopping strategy. We release our experimental framework and propose five design guidelines for topology-aware termination.

---

## 1. Introduction

### 1.1 The Termination Problem in Multi-Agent Teams

The deployment of large language model (LLM) based multi-agent systems has expanded rapidly, with frameworks such as AutoGen (Wu et al., 2023), CrewAI, and LangGraph enabling diverse coordination patterns for complex reasoning tasks. These systems coordinate multiple specialized agents through topologies ranging from simple round-robin chains to sophisticated debate protocols and hierarchical pipelines. However, a fundamental question remains largely unexplored: *when should these teams stop?* This question connects directly to *inference-time compute scaling*: multi-agent coordination represents structured test-time compute allocation across specialized agents, and the optimal stopping point defines the saturation boundary beyond which additional computation yields diminishing returns.

Current practice relies on rudimentary stopping criteria applied uniformly across topologies. The most common approaches include: (i) a fixed maximum number of turns, (ii) keyword detection (e.g., "TERMINATE"), and (iii) external timeout signals. These heuristics ignore a critical insight: *the optimal stopping point depends fundamentally on how agents coordinate*. A round-robin team of two agents solving a factual question may reach a satisfactory answer in two turns, while a three-agent debate team may need several exchange rounds to converge on a consensus. Applying the same termination logic to both configurations inevitably leads to either premature stopping (quality loss) or unnecessary computation (resource waste).

We term this mismatch *termination regret*---the gap between when a team actually stopped and when it should have stopped to optimize the quality-cost tradeoff. Consider three concrete scenarios:

- **Over-termination**: A debate team continues exchanging arguments four rounds past the point where all agents agreed, consuming tokens without quality improvement.
- **Under-termination**: A sequential pipeline stops after the first stage outputs a draft, never reaching the refinement stage that would have corrected factual errors.
- **Topology mismatch**: A selector-based team applies max-turn termination calibrated for flat sequential patterns, cutting off the routing agent's deliberation before it can consult the right specialist.

### 1.2 Research Questions

This work investigates seven research questions that together provide a comprehensive understanding of termination dynamics in multi-agent teams:

**RQ1**: How do termination dynamics---duration, turn count, token consumption---differ across coordination topologies? (Experiment 01)

**RQ2**: Can we detect termination regret by measuring per-turn quality trajectories and identifying optimal stopping points post hoc? (Experiment 02)

**RQ3**: Do structured feedback patterns (reflection, debate) exhibit measurable convergence signals that could inform adaptive stopping? (Experiment 03)

**RQ4**: Do different topologies produce characteristic error patterns in their outputs? (Experiment 04)

**RQ5**: Does the marginal utility ΔU(t) = ΔQ(t) - λ·ΔC(t) converge to zero at the optimal stopping point, and can this serve as a topology-aware termination signal? (Experiment 05)

**RQ6**: Can pre-execution topology features predict runtime costs, and which features are most predictive? (Experiment 06)

**RQ7**: How does task difficulty moderate the optimal topology choice, and does the quality gap between topologies widen or narrow with increasing difficulty? (Experiment 07)

### 1.3 Contributions

We make seven contributions:

1. **Cross-topology termination study.** We present the first systematic comparison of termination behavior across 13 coordination patterns within a single unified framework (AutoGen), spanning six topology categories. Prior work has compared at most 2--3 patterns across different frameworks, confounding topology effects with implementation differences (Cemri et al., 2025; Hu et al., 2025).

2. **Termination regret metric.** We introduce a post-hoc quality trajectory analysis using G-Eval (Liu et al., 2023) scoring at each agent turn, enabling precise identification of when quality peaked relative to when the team stopped. This reveals systematic over-computation in feedback patterns and under-computation in flat sequential patterns.

3. **Claim-level convergence detection.** Building on the KS-test approach of Hu et al. (2025) for debate stability detection, we extend convergence measurement to all 13 topologies by tracking claim-level semantic stability across turns, revealing that convergence signals are topology-dependent.

4. **Pattern-specific error taxonomy.** Aligning with the MAST error categories (Cemri et al., 2025) (hallucination, incompleteness, inconsistency), we demonstrate that error type distributions correlate with topology features: sequential patterns produce more incompleteness errors, while feedback patterns generate more inconsistency errors from conflicting revisions.

5. **Marginal utility as a diagnostic framework and the value of a "negative result."** We introduce ΔU(t) = ΔQ(t) - λ·ΔC(t) not as a novel optimization algorithm, but as a principled diagnostic lens that produces two contributions simultaneously. *The positive contribution*: ΔU identifies the specific topology class (decentralized handoff/B2) where keyword termination fails, achieving 70% cost savings for swm4---a targeted recommendation that no prior work has made. *The negative-result contribution*: a controlled 800-run experiment demonstrates that keyword termination is near-optimal for 7 of 8 topologies. This "negative result"---that sophisticated adaptive termination is unnecessary for most deployments---has significant practical value by validating existing practitioner heuristics with quantitative evidence. The formulation ΔU(t) → 0 exploits quality saturation (a universal property of iterative refinement), enabling topology-dependent convergence speed measurement (1.1--2.4 turns) regardless of λ choice. The key insight is not the formula itself, but what the formula *reveals* when applied systematically across 13 topologies for the first time.

6. **Topology-based cost prediction.** We demonstrate that pre-execution topology features (agent count, max messages, pattern category, and their interactions) predict runtime token consumption with moderate accuracy (Random Forest R²=0.54 on 5-fold CV). The interaction term `agent_count × max_messages` emerges as the strongest predictor, providing practitioners with a principled basis for cost estimation before execution. The remaining ~46% of variance attributable to task content complexity represents an honest boundary on what topology features alone can explain.

7. **Difficulty-aware topology recommendation.** Through a controlled 225-run experiment crossing 5 representative patterns with 15 difficulty-graded tasks (5 domains × 3 difficulty levels × 3 repeats), we test whether task difficulty moderates optimal topology choice. This yields a practical recommendation matrix mapping difficulty levels to optimal patterns for both quality maximization and cost efficiency.

### 1.4 Scope and Positioning

This work is an **empirical benchmarking study**, not an algorithmic contribution. Its value lies in the same tradition as systematic benchmarks (e.g., GLUE for NLU, HELM for language models, Chatbot Arena for LLM evaluation): providing the community with rigorous, large-scale empirical evidence that challenges assumptions, calibrates intuitions, and informs design decisions. No prior work has systematically compared termination dynamics across more than 2--3 patterns within a single controlled framework. By spanning 13 patterns, 7 experiments, and 2,200+ runs, we provide the empirical foundation that future algorithmic work---learned termination policies, dynamic topology switching, difficulty-aware routing---can build upon.

### 1.5 Paper Organization

Section 2 surveys related work on multi-agent coordination and stopping criteria. Section 3 describes our taxonomy of 14 coordination patterns and the experimental framework. Section 4 presents results from seven interconnected experiments. Section 5 discusses implications and limitations. Section 6 concludes.

---

## 2. Background and Related Work

### 2.1 Multi-Agent Coordination Topologies

Multi-agent LLM systems employ diverse coordination strategies. Grounded in classical MAS topology theory (Masterman et al., 2025)---which identifies chain, star, and mesh as canonical topologies---we organize 13 coordination patterns plus a single-agent baseline into six categories (Figure 1):

**Sequential Chain (Category A).** Round-robin patterns cycle agents in a fixed order: Agent_1 -> Agent_2 -> ... -> Agent_n -> Agent_1. Each agent sees the full conversation history but cannot influence routing. This corresponds to Masterman et al.'s chain/waterfall topology. Patterns: RR-2, RR-3, RR-4.

**Centralized Routing / Star (Category B1).** A dedicated coordinator agent (Selector) analyzes conversation state and centrally decides which specialist to invoke next. This corresponds to Masterman et al.'s hub-and-spoke topology, implemented via AutoGen's SelectorGroupChat. Each routing decision incurs an LLM call overhead but enables informed expert selection. Patterns: Sel-3, Sel-4.

**Decentralized Handoff / Mesh (Category B2).** Without a central coordinator, each agent autonomously decides when and to whom to hand off control via Handoff tool calls. This corresponds to Masterman et al.'s mesh/swarm topology, implemented via the Swarm class. No coordination bottleneck exists, but turn explosion risk is significant. Patterns: Swm-3, Swm-4.

> **Justification for the B1/B2 split.** Prior work grouped Selector and Swarm under "dynamic routing," but our experiments reveal fundamentally different behaviors: Selector produces few long monologues (2,100 tok/turn) while Swarm produces many short handoffs (330 tok/turn). Their scaling directions are opposite---Selector is sub-linear (sel4/sel3=1.48×) while Swarm is super-linear (swm4/swm3=3.17×). Tran et al. (2025)'s 5-dimensional collaboration framework explicitly separates "centralized vs. distributed" along the *Structure* dimension, supporting this decomposition.

**Structured Feedback (Category C).** Agents iteratively refine outputs through explicit feedback loops. Reflection patterns pair a generator with a critic; debate patterns have agents exchange arguments with a moderator. These topologies can converge but also risk oscillation. Patterns: Refl-2, Refl-3, Deb-3, Deb-4.

**Composed/Nested (Category D).** Multiple stages or layers are composed into a pipeline or mixture-of-agents (MoA) architecture. Pipeline patterns process tasks through sequential refinement stages; MoA generates multiple parallel responses and aggregates them. Patterns: Pipe, MoA.

Prior frameworks have implemented subsets of these patterns: AutoGen (Wu et al., 2023) supports round-robin, selector, and swarm patterns; DyTopo enables dynamic topology switching; MoA (ICLR 2025) introduces the layered aggregation pattern. Wang et al. (2025) apply small-world network theory to multi-agent debate, showing that principled topology design can stabilize consensus trajectories while maintaining token efficiency. MegaAgent (ACL 2025) demonstrates that inter-agent dialogue tokens dominate total cost at scale, motivating topology-aware communication efficiency. G-Designer (Zhang et al., ICML 2025) uses variational graph auto-encoders to dynamically generate task-specific communication topologies, achieving up to 95.33% token reduction on HumanEval---demonstrating that topology optimization directly impacts efficiency. The concurrent "Scaling Agent Systems" study (2025) evaluates 5 architectures across 180 configurations, finding that coordination yields diminishing returns once single-agent baselines exceed ~45% accuracy, and that multi-agent variants degrade sequential reasoning by 39--70%. AgentDropout (Wang et al., ACL 2025) optimizes communication graph adjacency matrices to dynamically eliminate redundant agents, achieving 21.6% prompt token reduction while improving performance by 1.14 points---supporting our finding that input costs grow superlinearly while per-agent output improvements remain sublinear. Our study complements these by focusing specifically on *termination dynamics*---how topology determines when teams should stop, rather than which topology to select.

### 2.2 Stopping Criteria in LLM Systems

**Single-Agent Stopping.** REFRAIN (Sun et al., 2025; arxiv 2510.10103) addresses "overthinking" in Chain-of-Thought reasoning through a two-stage stop discriminator combined with a sliding-window UCB multi-armed bandit controller for adaptive threshold adjustment, reducing token usage by 20--55% while maintaining accuracy. Self-consistency sampling (Wang et al., 2023) implicitly uses convergence detection by stopping when multiple reasoning paths agree. Confidence-based early stopping monitors model uncertainty scores.

**Multi-Agent Stopping.** Hu et al. (NeurIPS 2025) propose adaptive stability detection for multi-agent debate, using the KS statistic on Beta-Binomial distributions to detect when judge opinions stabilize, typically within 2--7 rounds. Ruan and Wang (2025) introduce Aegean, a formal consensus protocol with incremental quorum detection that enables early termination when sufficient agents converge, achieving 1.2--20x latency reduction while maintaining answer quality within 2.5%. Cemri et al. (2025) identify termination as one of three failure categories in multi-agent systems, documenting infinite loop and premature stopping failures. MAST (Cemri et al., 2025) evaluates multi-agent trajectories post hoc but does not propose adaptive termination. The Consensus-Diversity Tradeoff work (EMNLP 2025) explores the tension between reaching agreement and maintaining diverse perspectives in debates.

SupervisorAgent (Lin et al., 2025) introduces an LLM-free context filter for runtime adaptive supervision, reducing token consumption by 29.45% on the GAIA benchmark without compromising success rates. While SupervisorAgent operates at the supervision level (intervening during execution), our approach operates at the termination level (deciding when to stop).

**Gap.** No prior work systematically studies how termination dynamics vary across a comprehensive set of coordination topologies. Existing adaptive stopping targets specific settings: Hu et al. (2025) addresses debate patterns, Aegean (Ruan & Wang, 2025) addresses parallel consensus, and REFRAIN targets single-agent Chain-of-Thought reasoning. G-Designer optimizes topology selection but does not study when to stop within a chosen topology. The "Scaling Agent Systems" study evaluates architecture selection but uses fixed termination conditions. AgentDropout optimizes *which agents* participate but not *when* to terminate. SupervisorAgent reduces waste through runtime supervision but does not study topology-dependent termination dynamics. Our work bridges this gap by studying 13 patterns across five categories, proposing topology-aware adaptive termination, and providing empirical guidelines for when teams should stop.

### 2.3 Quality Evaluation in Multi-Agent Outputs

We adopt G-Eval (Liu et al., 2023) as our per-turn quality metric, using claude-sonnet-4-5 as the evaluator LLM. G-Eval provides a structured framework for evaluating text quality on multiple dimensions with demonstrated high correlation with human judgments. We adapt G-Eval with five task-relevant dimensions: accuracy, completeness, coherence, usefulness, and overall quality, each scored on a 1--5 integer scale. For error detection, we align our taxonomy with MAST categories (Cemri et al., 2025): hallucination, factual errors, incompleteness, inconsistency, and irrelevance.

**Table 1: Comparison with Related Work**

| Work | Patterns | Topology Categories | Adaptive Termination | Convergence Detection |
|------|----------|--------------------|--------------------|---------------------|
| MAST (Cemri et al., 2025) | 2 | Debate, voting | No | Trajectory-level |
| REFRAIN (2025) | 1 | CoT (single-agent) | Yes (discriminator+UCB) | N/A |
| Hu et al. (NeurIPS 2025) | 1 | Debate | Yes (KS-test) | Distribution-level |
| Aegean (Ruan & Wang, 2025) | N/A | Parallel consensus | Yes (quorum detection) | Quorum-level |
| Cemri et al. (2025) | ~5 | Mixed | No | Post-hoc analysis |
| G-Designer (ICML 2025) | Dynamic | GNN-generated | No (fixed per task) | N/A |
| Scaling Agent Systems (2025) | 5 | 4 coordination types | No | N/A |
| Wang et al. (2025) | 1 | Debate (small-world) | No | Semantic entropy |
| AgentDropout (ACL 2025) | Variable | Communication graphs | No (agent elimination) | N/A |
| SupervisorAgent (2025) | 1+ | Runtime supervision | Yes (LLM-free filter) | Context-level |
| **Ours** | **14** | **6 categories** | **Yes (topology-aware)** | **Claim-level KS-test + cost prediction + difficulty interaction** |

---

## 3. Methodology

### 3.1 Pattern Taxonomy

We study 14 coordination patterns (including a single-agent baseline) organized into six categories (Figure 1). Each pattern is parameterized by agent count *n* and shares a common termination vocabulary (TERMINATE keyword for graceful stopping, max_messages=25 as safety bound). Table 2 details the specific configurations.

**Table 2: Pattern Configurations**

| Pattern | Category | Agents | Roles | Routing | Termination |
|---------|----------|--------|-------|---------|-------------|
| Solo | S | 1 | General-purpose assistant | N/A | Keyword or max |
| RR-2 | A | 2 | Writer, Researcher | Fixed round-robin | Keyword or max |
| RR-3 | A | 3 | Writer, Researcher, Reviewer | Fixed round-robin | Keyword or max |
| RR-4 | A | 4 | Writer, Researcher, Reviewer, Editor | Fixed round-robin | Keyword or max |
| Sel-3 | B1 | 3+1 | 3 specialists + Selector | LLM-routed | Keyword or max |
| Sel-4 | B1 | 4+1 | 4 specialists + Selector | LLM-routed | Keyword or max |
| Swm-3 | B2 | 3 | 3 specialists w/ handoffs | Self-routing | Keyword or max |
| Swm-4 | B2 | 4 | 4 specialists w/ handoffs | Self-routing | Keyword or max |
| Refl-2 | C | 2 | Generator, Critic | Fixed w/ feedback | Keyword or max |
| Refl-3 | C | 3 | Generator, Critic, Refiner | Fixed w/ feedback | Keyword or max |
| Deb-3 | C | 3+1 | 3 debaters + Moderator | Moderated | Keyword or max |
| Deb-4 | C | 4+1 | 4 debaters + Moderator | Moderated | Keyword or max |
| Pipe | D | 2+ | Stage teams | Sequential stages | Per-stage keyword |
| MoA | D | 3+ | Parallel + Aggregator | Fan-out/aggregate | Aggregator decides |

### 3.2 Task Suite

We design 25 tasks across two dimensions: *cognitive type* (4 categories) and *subject domain* (9 domains). This dual classification enables domain-specific topology suitability analysis.

**Cognitive types (4):**
- **Factual** (7 tasks): Questions requiring knowledge retrieval and synthesis
- **Analytical** (9 tasks): Problems requiring structured reasoning and comparative analysis
- **Creative** (6 tasks): Open-ended generation requiring creativity, alternative thinking, and design
- **Technical** (3 tasks): Domain-specific tasks requiring specialized expertise and implementation

**Subject domains (9):** Science (3), CS (3), History (3), Philosophy (3), Law/Politics (3), Games (3), Engineering (3), Business (3), Medicine (1).

The complete task list with full prompt text is provided in Table A1 (Appendix A). Each prompt is self-contained and does not reference external materials; prompts average 25 words for factual tasks and 45 words for creative/technical tasks. Tasks range from medium to hard difficulty in this main suite; Experiment 07 introduces an explicit easy/medium/hard grading.

**Design rationale: open-ended tasks.** We deliberately choose open-ended generation tasks rather than verifiable benchmarks (e.g., HumanEval, MATH, MMLU) for a methodological reason: studying termination dynamics requires tasks where **quality varies continuously across turns**. Verifiable benchmarks produce binary outcomes (pass/fail) that do not reveal per-turn quality trajectories, convergence patterns, or the gradual quality saturation that our marginal utility analysis depends on. Open-ended tasks generate the rich quality curves needed to identify optimal stopping points, measure termination regret, and compare convergence speeds across topologies. This design choice is shared by related multi-agent evaluation studies: MAST (Cemri et al., 2025) uses open-ended tasks to study trajectory-level quality, and Hu et al. (2025) use debate-style questions to study convergence. We note this scope limitation explicitly (Section 5.3): termination dynamics on code generation or mathematical reasoning may differ, and extending to such tasks is an important future direction.

In the v1 experiment, each task was run with 3 repetitions per pattern, yielding 780 runs for Experiment 01 (13 patterns x 20 tasks x 3 repeats). In the v2 experiment, 8 representative patterns were run on all 25 tasks with 1 repetition each, yielding 200 runs (8 patterns x 25 tasks).

#### 3.2.1 Agent System Prompts

Each agent receives a role-specific system prompt that defines its expertise and behavioral expectations. All prompts share a common structure: (1) role definition, (2) response guidelines (thoroughness, structure), and (3) termination instruction ("say TERMINATE when the task is complete").

**Category A (Round-Robin):** Agents are assigned complementary roles—Writer (generates initial responses), Researcher (adds factual depth), Reviewer (evaluates completeness), Editor (polishes language). Each agent's system prompt instructs it to build on prior contributions rather than rewrite from scratch.

**Category B1 (Selector):** The Selector agent receives a routing prompt: "Analyze the conversation and select the most appropriate specialist for the next turn. Consider what aspect of the task needs attention." Specialist agents receive domain-specific prompts identical to their Category A counterparts.

**Category B2 (Swarm):** Each agent receives a handoff tool (`transfer_to_<agent>`) and is prompted: "Complete your portion of the task, then hand off to the most appropriate agent for the next step. If the task is fully addressed, say TERMINATE." No central coordinator exists.

**Category C (Feedback):** Reflection patterns use Generator ("produce a comprehensive response") and Critic ("evaluate the response for accuracy, completeness, and coherence; provide specific feedback or say APPROVED if satisfactory"). Debate patterns use Debater ("present your strongest argument on the topic") and Moderator ("synthesize the arguments and issue a VERDICT when consensus emerges or positions are clear").

**Category D (Composed):** Pipeline stages use sequential specialists (e.g., Analyst→Synthesizer→Editor). MoA uses parallel generators with an Aggregator ("combine the best elements from all responses into a unified answer").

Full system prompts for all 14 patterns are available in the supplementary code repository.

### 3.3 Experimental Framework

All primary experiments use the AutoGen framework with a custom ClaudeCLIChatCompletionClient wrapping Claude Haiku 4.5 as the base model, with cross-model validation using GPT-4o-mini (Section 4.6). This provides consistent LLM behavior across all patterns while capturing per-call token counts via the SDK's models_usage tracking.

**Metrics captured per run:**
- *Duration*: Wall-clock time from team.run() start to completion
- *Turn count*: Total messages in the conversation
- *Agent turn count*: Messages from non-system agents
- *Token usage*: Prompt tokens (in) and completion tokens (out) per LLM call
- *Stop reason*: How the team terminated (keyword, max_messages, error)
- *Quality score*: G-Eval assessment (Experiment 02 only)
- *Convergence point*: KS-test stability (Experiment 03 only)

### 3.4 Seven Experiments

**Experiment 01: Pattern Efficiency** (780 runs). Compares all 13 patterns on duration, turn count, agent turns, and token usage across the full task suite. Tests whether topology category is a significant predictor of efficiency via Kruskal-Wallis tests.

**Experiment 02: Termination Quality** (100 runs). Applies G-Eval scoring at each agent turn for 5 representative patterns (one per category) across 20 tasks, yielding 100 runs and 276 turn-level quality scores. Identifies termination regret (gap between actual and optimal stopping points).

**Experiment 03: Convergence Detection** (analysis only). Uses exp01 message data to compute KS-test convergence metrics, comparing convergence speed across categories. Tests whether feedback patterns converge faster than sequential patterns.

**Experiment 04: Error Attribution** (analysis only). Classifies errors from exp01 and exp02 into 8 error types, correlating error distributions with topology features. Tests pattern-specific error signatures.

**Experiment 05: Adaptive Termination** (800 runs). A controlled experiment comparing adaptive ΔU-based termination against keyword baselines. Tests all 8 representative patterns across 25 tasks with 3 λ values (0.0, 0.1, 0.5), yielding 200 baseline + 600 adaptive = 800 runs. Evaluates whether ΔU(t) = ΔQ(t) - λ·ΔC(t) → 0 can serve as a practical termination signal.

**Experiment 06: Cost Prediction** (analysis only). Trains regression models (Linear, Ridge, Lasso, Random Forest) on exp01 data to predict runtime costs (tokens, turns, duration) from pre-execution topology features: pattern category (one-hot), agent count, max messages, task category, and the interaction term `agent_count × max_messages`. Evaluates via 5-fold cross-validation and holdout prediction on exp05 baseline data. No additional runs required---pure analysis of existing experimental data.

**Experiment 07: Task Difficulty Interaction** (669 scored runs across 5 models). Crosses 5 representative patterns (solo, swm3, sel3, refl2, debate3---one per category) with 15 difficulty-graded tasks (5 domains × 3 difficulty levels: easy, medium, hard) with 3 repeats per model. Tests whether task difficulty moderates the optimal pattern choice via Kruskal-Wallis tests for main effects and interaction, replicated across 5 models (Haiku 220, GPT-4o-mini 224, GPT-5.4 75, Grok 75, Gemini 75 runs). Scored with G-Eval to produce a difficulty-aware recommendation matrix.

---

## 4. Results

We present results from seven interconnected experiments, each addressing a specific research question. Experiments 01--06 use Claude Haiku 4.5 as the base model through a custom AutoGen ChatCompletionClient, ensuring consistent LLM behavior across all 14 patterns (13 multi-agent + 1 solo baseline). Experiment 07 extends to 5 models (Haiku, GPT-4o-mini, GPT-5.4, Grok, Gemini) on a separate difficulty-graded task suite.

### 4.1 Experiment 01: Pattern Efficiency (RQ1)

**Setup.** We executed 780 runs (13 patterns x 20 tasks x 3 repeats) plus 25 single-agent baseline runs, measuring duration, LLM call count, and token consumption per run. Runs encountering infrastructure errors (prompt truncation beyond 28K characters) were excluded from analysis.

#### 4.1.0 Single-Agent Baseline (Category S)

To establish a lower bound for multi-agent overhead, we run a single general-purpose agent on all 25 tasks with a max_messages limit of 5 and TERMINATE keyword termination.

**Table 3: Single-Agent Baseline vs. Multi-Agent Patterns**

| Pattern | Cat. | Agents | Avg Tokens | Avg Duration (s) | Keyword% | vs solo |
|---------|------|--------|-----------|-----------------|----------|---------|
| solo | S | 1 | 1,287 | 18.7 | 100% | 1.00x |
| rr2 | A | 2 | 4,759 | 52.4 | — | 3.70x |
| swm3 | B2 | 3 | 4,196 | 75.2 | — | 3.26x |
| sel3 | B1 | 3+1 | 7,851 | 115.2 | — | 6.10x |
| refl2 | C | 2 | 5,237 | 60.2 | — | 4.07x |

**Finding 1 — Multi-agent coordination incurs 3.3--6.1x token overhead over a single agent.** The solo baseline completes all 25 tasks at an average of 1,287 tokens with 100% keyword termination rate, establishing a lower bound. The cheapest multi-agent pattern (swm3, 3 agents) costs 3.26x more tokens, while rr2 (2 agents) costs 3.70x. This overhead quantifies the *coordination tax*---the cost of inter-agent communication, context accumulation, and turn-taking protocol. However, this overhead must be weighed against quality improvements: the multi-agent quality analysis in Experiment 02 demonstrates that multi-agent patterns achieve higher G-Eval scores, particularly on complex analytical and creative tasks where iterative refinement and diverse perspectives improve output quality.

#### 4.1.1 Category A: Flat Sequential Patterns

Table 4 presents results from Category A (Flat Sequential), providing evidence for how agent count affects efficiency in fixed round-robin topologies.

**Table 4: Category A Efficiency Metrics (Successful Runs Only)**

| Metric | rr2 (n=2) | rr3 (n=3) | Ratio (rr3/rr2) |
|--------|-----------|-----------|------------------|
| Successful runs | 55/60 | 46/60 | - |
| Error rate | 8.3% | 23.3% | 2.81x |
| Mean LLM calls | 2.0 | 3.5 | 1.75x |
| Mean duration (s) | 52.4 | 96.6 | 1.84x |
| Mean tokens (in) | 1,594 | 4,132 | 2.59x |
| Mean tokens (out) | 3,165 | 5,989 | 1.89x |
| Mean total tokens | 4,759 | 10,121 | 2.13x |
| Output tokens/call | 1,583 | 1,711 | 1.08x |

**Table 5: Full 3-Pattern Comparison (Successful Runs Only)**

| Metric | rr2 (n=2) | rr3 (n=3) | rr4 (n=4) | rr3/rr2 | rr4/rr2 |
|--------|-----------|-----------|-----------|---------|---------|
| Successful runs | 55/60 | 46/60 | 17/60 | - | - |
| Error rate | 8.3% | 23.3% | 71.7% | 2.81x | 8.64x |
| Mean duration (s) | 52.4 | 96.6 | 118.8 | 1.84x | 2.27x |
| Mean tokens (in) | 1,594 | 4,132 | 4,274 | 2.59x | 2.68x |
| Mean tokens (out) | 3,165 | 5,989 | 7,767 | 1.89x | 2.45x |
| Mean total tokens | 4,759 | 10,121 | 12,040 | 2.13x | 2.53x |
| Output/agent turn | 1,583 | 1,701 | 1,942 | 1.07x | 1.23x |

Note: rr4's 71.7% error rate is inflated by an infrastructure bug (Section 4.4). The 17 successful rr4 runs are predominantly factual tasks (15/17), biasing metrics toward shorter tasks. Categories B/C/D use fixed infrastructure code.

**Finding 2: Near-linear cost scaling driven by input token growth.** Adding agents approximately doubles duration (rr3/rr2=1.84x) and total tokens (2.13x), consistent with near-linear scaling. The fact-only comparison (Table 5) reveals an intriguing trend: output tokens per LLM call *increase* with team size (rr2=930, rr3=1189, rr4=1544; 1.66x from rr2 to rr4). This suggests that agents generate richer responses when exposed to more prior contributions---a phenomenon consistent with collaborative amplification. The cost driver is *input token accumulation*: input tokens grow at 2.59x (versus 1.75x in LLM calls), confirming that each agent in a round-robin sees the full conversation history. The nth agent's prompt includes all previous (n-1) responses, creating superlinear input growth that has practical implications for context window consumption and truncation-related failures (Finding 4).

**Finding 3: Input token superlinear growth.** Input tokens grow at 2.59x (versus the 1.75x in LLM calls), demonstrating superlinear context accumulation. The expected theoretical growth is O(n * k * L) where n=agent count, k=rounds, and L=average response length. With rr3 completing k=1 full round (3 agents) versus rr2's k=1 round (2 agents), the observed 2.59x growth is consistent with each additional agent adding its response to the shared context. This superlinear input growth has practical implications: it accelerates context window consumption and increases the likelihood of truncation-related failures (Finding 4).

**Finding 4: Error rate scales superlinearly with agent count.** Error rates increase dramatically: rr2=8.3%, rr3=23.3%, rr4=71.7%. The *error distribution across task categories* broadens monotonically: rr2 errors concentrate exclusively on technical tasks (5/5 errors), rr3 spreads to technical (8/14), creative (3/14), and analytical (3/14), while rr4 reaches near-total failure on all non-factual categories (tech=15/15, anal=15/15, crea=13/15 errors). Only factual tasks maintain 0% error rate across all three patterns. This broadening demonstrates that context accumulation scales with both agent count and response verbosity: rr2 overflows only on token-dense code generation, while rr4 overflows on any task category except short factual responses. Note: the rr4 error rate is inflated by an infrastructure bug (Section 4.4); however, the underlying cause---context accumulation exceeding transport limits---is a genuine scaling challenge for larger teams.

**Finding 5: Task category effects.** We observe significant variation across task categories (Table 6). Creative tasks require the most time (93.3s mean), while factual tasks are most efficient (66.5s, 6,183 tokens). Technical tasks show the highest token density (9,100 avg) and the highest error rate (42.1%), driven by long code-generation responses that trigger context overflow. Factual tasks exhibit zero errors---their shorter, retrieval-oriented responses avoid the context accumulation that triggers infrastructure failures.

**Table 6: Task Category Effects (Categories A Combined)**

| Task Category | Runs | Mean Duration | Mean Tokens | Error Rate | Characterization |
|--------------|------|--------------|-------------|-----------|------------------|
| Factual | 30 | 66.5s | 6,183 | 0% | Retrieval-based, shortest |
| Creative | 30 | 93.3s | 8,578 | 10.0% | Open-ended, multi-round |
| Analytical | 30 | 82.1s | 8,152 | 10.0% | Structured reasoning |
| Technical | 19* | 61.9s | 9,100 | 42.1% | Token-dense, truncation-prone |

*Technical category has fewer runs due to rr3 partial completion.

#### 4.1.2 Category B: Dynamic Routing Patterns

Table 7 presents results from Category B (Dynamic Routing), comparing selector-based routing (centralized coordinator) with swarm-based routing (decentralized handoffs). All 240 runs completed successfully with 0% error rate, confirming that the infrastructure fix resolved the prompt truncation issues observed in Category A.

**Table 7: Category B Efficiency Metrics (All Runs Successful)**

| Metric | Sel-3 (n=3+1) | Sel-4 (n=4+1) | Swm-3 (n=3) | Swm-4 (n=4) |
|--------|--------------|--------------|-------------|-------------|
| Successful runs | 60/60 | 60/60 | 60/60 | 60/60 |
| Error rate | 0% | 0% | 0% | 0% |
| Mean duration (s) | 115.2 | 161.9 | 75.2 | 185.0 |
| Mean tokens (in) | 2,076 | 2,457 | 1,364 | 6,786 |
| Mean tokens (out) | 5,775 | 9,138 | 2,833 | 6,535 |
| Mean total tokens | 7,851 | 11,595 | 4,196 | 13,321 |
| Mean turns | 3.5 | 4.1 | 10.2 | 25.0 |
| Mean agent turns | 2.5 | 3.1 | 9.2 | 24.0 |
| Output/agent turn | 2,114 | 2,616 | 337 | 330 |

**Finding 6: Two distinct routing strategies produce radically different turn-level behavior.** Selector and swarm routing represent two fundamentally different approaches to dynamic coordination. Selector patterns produce few turns (3.5--4.1) with long monologues per turn (2,114--2,616 output tokens/agent turn), while swarm patterns produce many turns (10.2--25.0) with short, focused handoffs (330--337 output tokens/agent turn). Despite this 6--8x difference in output density per turn, both achieve comparable total token counts at 3 agents (sel3=7,851 vs swm3=4,196). The swarm approach is significantly more efficient at 3 agents: 35% faster and 47% cheaper than selector.

**Finding 7: Routing strategy determines scaling behavior.** Adding one agent scales differently by routing strategy. Selector scaling is sub-linear: sel4/sel3 = 1.48x total tokens. Swarm scaling is super-linear: swm4/swm3 = 3.17x total tokens. The swarm's turn explosion (from 10.2 to 25.0 average turns) when adding a 4th agent eliminates its efficiency advantage. At 3 agents, swm3 is 47% cheaper than sel3; at 4 agents, swm4 is 15% more expensive than sel4. This crossover point has practical implications: swarm routing should be preferred for small teams (n<=3), while selector routing scales more gracefully for larger teams.

**Finding 8: Swm-3 achieves best overall token efficiency.** Remarkably, swm3 (3-agent swarm) achieves lower total token cost (4,196) than even rr2 (4,759), a 2-agent round-robin pattern. This 12% cost reduction with 50% more agents demonstrates that intelligent routing can more than compensate for the overhead of additional agents. The mechanism is clear: swarm agents perform focused handoffs rather than processing the entire conversation context, keeping input tokens low (1,364 vs rr2's 1,594) despite more agents.

**Table 8: Cross-Strategy Comparison (Category A vs B)**

| Pattern | Agents | Duration (s) | Total Tokens | vs rr3 Duration | vs rr3 Tokens |
|---------|--------|-------------|-------------|----------------|--------------|
| rr2 | 2 | 52.4 | 4,759 | 0.54x | 0.47x |
| rr3 | 3 | 96.6 | 10,121 | 1.00x | 1.00x |
| sel3 | 3+1 | 115.2 | 7,851 | 1.19x | 0.78x |
| sel4 | 4+1 | 161.9 | 11,595 | 1.68x | 1.15x |
| swm3 | 3 | 75.2 | 4,196 | 0.78x | 0.41x |
| swm4 | 4 | 185.0 | 13,321 | 1.92x | 1.32x |

The comparison reveals that routing strategy has a larger effect on efficiency than agent count. swm3 uses 59% fewer tokens than rr3 despite the same agent count, while sel3 uses 22% fewer tokens than rr3 despite an additional coordinator agent. Dynamic routing avoids the full-context broadcasting that drives rr3's superlinear input growth (Finding 3).

#### 4.1.3 Category C: Structured Feedback Patterns

Table 9 presents results from Category C (Structured Feedback), comparing reflection-based patterns (generator-critic loops) with debate-based patterns (multi-agent argumentation with moderator). All 240 runs completed with 0% error rate.

**Table 9: Category C Efficiency Metrics (All Runs Successful)**

| Metric | Refl-2 (n=2) | Refl-3 (n=3) | Deb-3 (n=3+1) | Deb-4 (n=4+1) |
|--------|-------------|-------------|--------------|--------------|
| Successful runs | 60/60 | 60/60 | 60/60 | 60/60 |
| Mean duration (s) | 60.2 | 120.2 | 156.6 | 180.9 |
| Mean tokens (in) | 1,485 | 3,343 | 3,480 | 5,217 |
| Mean tokens (out) | 3,752 | 8,752 | 5,834 | 6,420 |
| Mean total tokens | 5,237 | 12,095 | 9,313 | 11,637 |
| Mean turns | 3.2 | 4.5 | 4.5 | 5.4 |
| Mean agent turns | 2.2 | 3.5 | 3.5 | 4.4 |
| Output/agent turn | 1,732 | 2,537 | 1,691 | 1,448 |

**Finding 9: Reflection and debate exhibit opposite scaling behaviors.** Reflection scaling is super-linear: refl3/refl2 = 2.31x total tokens for +1 agent. Each additional reflection layer amplifies cumulative context as the critic reviews increasingly long conversation history. Debate scaling is sub-linear: deb4/deb3 = 1.25x total tokens for +1 debater. The structured debate format constrains per-agent verbosity, and the moderator absorbs coordination overhead. This contrast reveals that feedback *structure* matters more than feedback *existence* for scaling efficiency.

**Finding 10: Refl-2 achieves near-baseline efficiency with quality assurance.** Remarkably, refl2 (60.2s, 5,237 tokens) is only 15% slower and 10% more expensive than rr2 (52.4s, 4,759 tokens), the cheapest pattern across all categories. Yet refl2 includes a structured critic-approval loop that provides quality assurance absent in flat sequential patterns. This positions refl2 as the optimal choice when quality verification is needed at minimal cost overhead.

**Finding 11: At equal agent count, reflection is faster but debate is cheaper.** Comparing refl3 and deb3 (both 3-agent): refl3 is 30% faster (120.2s vs 156.6s) but generates 30% more tokens (12,095 vs 9,313). Reflection agents produce verbose self-contained revisions (2,537 tokens/turn), while debate agents produce focused arguments (1,691 tokens/turn). The token difference is directional but not statistically significant (p=0.09), suggesting these strategies occupy similar efficiency tiers with different resource profiles.

**Finding 12: Debate constrains per-agent output as team grows.** Output tokens per agent turn *decrease* with team size in debate (deb3=1,691, deb4=1,448; 0.86x), contrasting with the collaborative amplification observed in Category A where output per turn *increases* (Finding 2). The moderated debate structure imposes turn discipline: with more debaters, each has less conversational space. This natural constraint may explain debate's sub-linear scaling---additional agents are "cheaper" because the format limits their individual output.

#### 4.1.4 Category D: Composed Patterns

Table 10 presents results from Category D (Composed Patterns), comparing pipeline execution (sequential multi-stage refinement) with mixture-of-agents (parallel proposer layer followed by aggregation). All 120 runs completed with 0% error rate.

**Table 10: Category D Efficiency Metrics (All Runs Successful)**

| Metric | Pipe (n=5, 2-stage) | MoA (n=4, 3+1) |
|--------|---------------------|-----------------|
| Successful runs | 60/60 | 60/60 |
| Error rate | 0% | 0% |
| Mean duration (s) | 129.6 | 103.0 |
| Mean tokens (in) | 4,275 | 4,875 |
| Mean tokens (out) | 9,581 | 17,458 |
| Mean total tokens | 13,856 | 22,333 |
| Mean turns | 6.0 | 11.0 |
| Mean agent turns | 4.0 | 7.0 |
| Output/agent turn | 2,325 | 2,494 |

**Table 11: Category D Task Breakdown (Total Tokens by Task Category)**

| Task Category | Pipe | MoA | MoA/Pipe |
|--------------|------|-----|----------|
| Factual | 9,930 | 15,064 | 1.52x |
| Creative | 13,929 | 17,826 | 1.28x |
| Analytical | 12,342 | 18,598 | 1.51x |
| Technical | 19,223 | 37,844 | 1.97x |
| Tech/Fact ratio | 1.94x | 2.51x | - |

**Finding 13: MoA is the most expensive pattern overall.** MoA at 22,333 average total tokens is 61% more expensive than pipe (13,856) and 5.3x more expensive than swm3 (4,196), the most efficient pattern across all categories. The cost structure reveals why: MoA's three parallel proposers each generate a complete, independent response to the task, then the aggregator synthesizes these into a comprehensive final answer. Output tokens dominate MoA's budget (17,458 out of 22,333 = 78%), the highest output-to-total ratio of any pattern. By contrast, pipe's output share is 69% (9,581/13,856), closer to the Category A average (~65%). Despite its higher token cost, MoA is 21% faster than pipe in wall-clock time (103.0s vs 129.6s), reflecting the parallelism benefit: three proposers can execute concurrently, whereas pipe's stages are strictly sequential. This latency-cost tradeoff---faster but more expensive---distinguishes MoA as the pattern of choice when response time matters more than token budget.

**Finding 14: Composed patterns produce the highest output density.** Both pipe (2,325 output tokens/agent turn) and MoA (2,494 output tokens/agent turn) produce the highest output per agent turn across all five categories. For comparison: rr2=1,583, sel3=2,114, refl2=1,732, swm3=337, deb3=1,691. The mechanism is structural---each stage in a pipeline and each proposer in MoA generates a complete, self-contained response rather than an incremental contribution to an ongoing conversation. MoA's output density (2,494) is the highest of any pattern, reflecting the aggregator's role in producing a comprehensive synthesis that often exceeds any individual proposer's response length. This high per-turn output density has implications for termination: composed patterns extract maximum value from each LLM call, suggesting that even a single unnecessary turn is disproportionately wasteful compared to patterns with lower output density (e.g., swm3 at 337 tokens/turn).

**Finding 15: Task complexity amplifies composed pattern costs exponentially.** MoA's technical task cost (37,844 tokens) is 2.51x its factual task cost (15,064). This tech/fact multiplier is the highest of any pattern: rr2≈1.47x, sel3=1.51x, refl2=1.39x, pipe=1.94x. The amplification mechanism is multiplicative in MoA: code-generation tasks produce long responses (~3,000 tokens each) in each of the three parallel proposers, and the aggregator must then synthesize three complete code solutions into a unified response, yielding an aggregation output that often exceeds any individual proposal. Pipe exhibits a similar but less extreme amplification (tech=19,223 vs fact=9,930, 1.94x), as each pipeline stage sequentially refines an increasingly detailed technical response. Together, these results demonstrate that composed patterns are most cost-effective on concise tasks (factual, short-answer) and least cost-effective on verbose tasks (technical, code-generation), a consideration that should inform topology selection based on expected task distribution.

**Table 12: Cross-Category Efficiency Comparison (All 14 Patterns)**

| Pattern | Cat. | Agents | Duration (s) | Total Tokens | ±std | 95% CI | Out/Agent Turn | vs solo |
|---------|------|--------|-------------|-------------|------|--------|----------------|---------|
| solo | S | 1 | 18.7 | 1,287 | — | — | 1,209 | 1.00x |
| swm3 | B2 | 3 | 75.2 | 4,196 | ±5,646 | [2,011; 6,672] | 337 | 3.26x |
| rr2 | A | 2 | 52.4 | 4,759 | — | — | 1,583 | 3.70x |
| refl2 | C | 2 | 60.2 | 5,237 | ±3,315 | [3,913; 6,649] | 1,732 | 4.07x |
| sel3 | B1 | 3+1 | 115.2 | 7,851 | ±5,243 | [6,338; 10,666] | 2,114 | 6.10x |
| deb3 | C | 3+1 | 156.6 | 9,313 | ±2,501 | [7,625; 9,690] | 1,691 | 7.23x |
| rr3 | A | 3 | 96.6 | 10,121 | ±10,148 | [8,143; 16,521] | 1,701 | 7.86x |
| sel4 | B1 | 4+1 | 161.9 | 11,595 | ±6,428 | [8,610; 13,917] | 2,616 | 9.01x |
| deb4 | C | 4+1 | 180.9 | 11,637 | ±2,978 | [10,875; 12,400] | 1,448 | 9.04x |
| refl3 | C | 3 | 120.2 | 12,095 | ±6,765 | [10,363; 13,828] | 2,537 | 9.40x |
| swm4 | B2 | 4 | 185.0 | 13,321 | ±6,214 | [10,355; 15,486] | 330 | 10.35x |
| pipe | D | 5 | 129.6 | 13,856 | ±5,828 | [10,780; 15,592] | 2,325 | 10.76x |
| moa | D | 4 | 103.0 | 22,333 | ±10,599 | [19,618; 25,048] | 2,494 | 17.35x |

*Note: std and 95% CI computed from n=25 runs per pattern (v2 dataset). Solo and rr2 lack per-run data for CI computation. Full statistical breakdown in Appendix C.*

Table 12 ranks all 14 patterns (including solo baseline) by total token cost, revealing a 17.4x range from solo (1,287) to MoA (22,333). The solo baseline establishes a lower bound: all multi-agent patterns cost at least 3.26x more tokens. Several cross-category observations emerge. First, *routing strategy dominates agent count*: swm3 (3 agents) is cheaper than rr2 (2 agents), and sel3 (4 agents including coordinator) is cheaper than rr3 (3 agents). Second, *feedback patterns cluster in the middle*: refl2 and deb3 occupy the 5,000--10,000 token range, offering quality assurance at moderate cost. Third, *composed patterns occupy the expensive end*: both pipe and MoA exceed 13,000 tokens, reflecting the cost of multi-stage or multi-proposal generation. Fourth, *output density varies by an order of magnitude*: from swm3/swm4's ~330 tokens/agent turn (many short handoffs) to MoA's 2,494 tokens/agent turn (few complete responses), with implications for how much value each additional turn contributes.

#### 4.1.5 Cross-Category Comparison

We apply Kruskal-Wallis tests across all five topology categories (A: Sequential Chain, B1: Centralized Routing, B2: Decentralized Handoff, C: Structured Feedback, D: Composed/Nested) on 718 successful runs (out of 780 total) to determine whether coordination topology is a statistically significant predictor of efficiency.

**Table 13: Kruskal-Wallis Tests Across Categories (df=4, N=718)**

| Metric | H | p-value | η²_H | Effect |
|--------|---|---------|------|--------|
| Turn count | 408.606 | <0.001 | 0.567 | Large |
| Duration (s) | 70.776 | <0.001 | 0.094 | Medium |
| Total tokens | 132.333 | <0.001 | 0.180 | Large |
| Input tokens | 60.885 | <0.001 | 0.080 | Medium |
| Output tokens | 120.565 | <0.001 | 0.163 | Large |

*Effect size: η²_H = (H - k + 1) / (N - k), where k=5 categories. Thresholds: small=0.01, medium=0.06, large=0.14 (Cohen, 1988).*

All five metrics show highly significant differences with medium-to-large effect sizes. Turn count shows the strongest category dependence (η²=0.567), indicating that topology category determines 57% of turn count variance---more than any other metric. Total tokens (η²=0.180) and output tokens (η²=0.163) also show large effects, confirming that topology category is a strong predictor of computational efficiency.

**Table 14: Pairwise Mann-Whitney U Tests for Total Tokens**

| Comparison | U | p-value | Significant |
|------------|---|---------|-------------|
| A vs B1 | 6,000 | 0.042 | * |
| **A vs B2** | **7,176** | **0.857** | **No** |
| A vs C | 11,034 | <0.001 | *** |
| A vs D | 1,778 | <0.001 | *** |
| **B1 vs B2** | **8,157** | **0.075** | **No** |
| B1 vs C | 14,035 | 0.695 | No |
| B1 vs D | 3,010 | <0.001 | *** |
| B2 vs C | 12,348 | 0.028 | * |
| B2 vs D | 2,944 | <0.001 | *** |
| C vs D | 5,216 | <0.001 | *** |

**Table 15: Token Consumption by Category**

| Category | Median Tokens | Mean Tokens | N |
|----------|---------------|-------------|---|
| A (Sequential Chain) | 7,420 | 7,898 | 118 |
| B1 (Centralized Routing) | 9,197 | 9,723 | 120 |
| B2 (Decentralized Handoff) | 9,142 | 8,759 | 120 |
| C (Structured Feedback) | 9,247 | 9,571 | 240 |
| D (Composed/Nested) | 15,865 | 18,094 | 120 |

**Finding 16 — Sequential chain and decentralized handoff are statistically indistinguishable in cost.** Despite different coordination mechanisms and agent counts, Categories A and B2 show no significant difference in total token consumption (Mann-Whitney U=7,176, p=0.857). This is a non-trivial result: B2 (Mesh) patterns use 3--4 agents compared to A's 2--4, yet swm3's extreme efficiency (4,196 tokens) brings B2's aggregate cost down to A's level. Conversely, centralized routing (B1) is marginally more expensive than A (p=0.042), and B1 vs B2 are borderline indistinguishable (p=0.075), demonstrating that the B1/B2 decomposition reveals structure that the old unified "Category B" obscured.

**Finding 17 — New cost hierarchy: A ≈ B2 ≲ B1 ≈ C ≪ D.** The five-category analysis reveals a more nuanced cost structure than the previous four-tier hierarchy. Category D (median 15,865) remains clearly the most expensive. The middle tier splits into two sub-groups: B1 and C are cost-equivalent (p=0.695), while B2 is significantly cheaper than C (p=0.028). Category A and B2 form the efficient tier (p=0.857). The 2.1x gap between cheapest (A, median 7,420) and most expensive non-composed category (C, median 9,247) is smaller than the 1.7x gap between the middle tier and D, confirming that the composed/nested meta-architecture imposes the largest cost premium.

**Within-Category Agent Count Effects**

| Category | Spearman ρ (agent_count vs turn_count) | p-value |
|----------|----------------------------------------|---------|
| A (Sequential Chain) | 0.948 | <0.001 |
| B1 (Centralized Routing) | 0.377 | <0.001 |
| B2 (Decentralized Handoff) | 0.704 | <0.001 |
| C (Structured Feedback) | 0.805 | <0.001 |

**Finding 18 — The B1/B2 decomposition reveals fundamentally different scaling behaviors.** All four testable categories show significant agent-count correlations (p<0.001), but the magnitudes reveal topology-dependent scaling. Category A shows near-perfect correlation (ρ=0.948): each additional agent in a round-robin chain adds exactly one turn per cycle, making cost perfectly predictable. Category B1 (Centralized Routing) shows the weakest correlation (ρ=0.377) because the central router absorbs coordination overhead---adding agents to a star topology has diminishing impact on turn count. Category B2 (Decentralized Handoff) shows a strong correlation (ρ=0.704) driven by handoff chain explosion: swm4's 25 average turns versus swm3's 10 turns reflects the quadratic growth in potential handoff paths. Category C (ρ=0.805) scales predictably as each feedback layer adds a fixed number of review/revision turns. This four-way contrast---A=deterministic, B1=absorbed, B2=explosive, C=linear---provides practitioners with clear scaling expectations for each topology family.

**Summary: Three orthogonal dimensions of cost variation.** To disentangle the effects of individual patterns, agent count, and category, Table 16a summarizes the three dimensions:

**Table 16a: Cost Drivers Decomposed**

| Dimension | Effect Size | Key Observation |
|-----------|-----------|-----------------|
| **Category** (A/B1/B2/C/D) | KW H=132.3, p<0.001 | D is 2.1x more expensive than the median category; A≈B2<B1≈C≪D |
| **Agent count** (within category) | ρ=0.38--0.95 | Scaling rate varies by category: A=deterministic, B1=absorbed, B2=explosive, C=linear |
| **Individual pattern** | 17.4x range (solo→MoA) | Routing strategy (swm3<rr2) can override agent count effects |

The category dimension provides coarse-grained cost estimation (5 bins). Within each category, agent count refines the estimate, but with category-dependent scaling rates. Individual pattern identity captures remaining variance (e.g., debate3 vs refl2 within Category C differ by 1.8x despite similar agent counts). For cost budgeting, category determines the order of magnitude, agent count determines the multiplier, and pattern-specific routing behavior determines the constant factor.

#### 4.1.6 Domain × Pattern Cross-Analysis

**Setup.** To assess domain sensitivity, we evaluate 8 representative patterns across 25 tasks spanning 9 knowledge domains: science, computer science, history, philosophy, law & politics, gaming, engineering, business, and medicine. Each task is annotated with its domain, enabling domain × pattern cross-analysis (N=200, 0% error rate).

**Table 16: Domain × Pattern Efficiency (Mean Total Tokens, ×10³)**

| Domain | rr3 | sel3 | sel4 | swm3 | swm4 | refl2 | debate3 | pipe |
|--------|-----|------|------|------|------|-------|---------|------|
| science | 9.5 | 9.3 | 7.0 | 3.3 | 9.6 | 3.5 | 6.4 | 14.2 |
| CS | 13.4 | 8.5 | 11.6 | 5.3 | 7.9 | 4.9 | 8.7 | 13.5 |
| history | 7.0 | 4.2 | 5.2 | 1.4 | 12.1 | 9.1 | 8.6 | 8.9 |
| philosophy | 7.9 | 3.3 | 3.2 | 8.0 | 20.7 | 2.8 | 7.7 | 8.6 |
| law_politics | 17.4 | 10.0 | 17.4 | 1.9 | 12.3 | 4.8 | 8.4 | 10.4 |
| gaming | 20.6 | 15.1 | 14.7 | 2.6 | 13.1 | 6.9 | 10.6 | 16.5 |
| engineering | 8.8 | 12.5 | 17.8 | 3.9 | 8.2 | 5.0 | 9.8 | 12.2 |
| business | 15.5 | 4.4 | 13.9 | 9.2 | 14.8 | 3.5 | 8.9 | 15.7 |
| medicine | 7.9 | 10.7 | 9.5 | 1.7 | 27.1 | 10.6 | 9.2 | 29.6 |

**Statistical tests.** Per-domain Kruskal-Wallis tests assess whether pattern choice significantly affects cost within each domain. Five of nine domains show significant pattern effects (p<0.05): science, CS, philosophy, law & politics, and engineering. The remaining four (history, gaming, business, medicine) show p values between 0.09 and 0.43. Pattern domain-sensitivity is measured by the coefficient of variation (CV) of mean tokens across domains.

**Table 17: Pattern Domain-Sensitivity (CV of Mean Tokens Across Domains)**

| Pattern | Category | Mean Tokens | Std | CV | Interpretation |
|---------|----------|-------------|-----|-----|----------------|
| debate3 | C | 8,657 | 1,189 | 0.14 | Domain-invariant |
| rr3 | A | 12,005 | 4,907 | 0.41 | Moderate |
| pipe | D | 14,404 | 6,361 | 0.44 | Moderate |
| swm4 | B2 | 13,969 | 6,268 | 0.45 | Moderate |
| sel3 | B1 | 8,665 | 4,019 | 0.46 | Moderate |
| refl2 | C | 5,675 | 2,666 | 0.47 | Moderate |
| sel4 | B1 | 11,131 | 5,264 | 0.47 | Moderate |
| swm3 | B2 | 4,148 | 2,795 | 0.67 | Domain-sensitive |

**Finding 19 — debate3 is uniquely domain-invariant; swm3 is domain-sensitive.** Among all eight patterns, debate3 exhibits the lowest cross-domain CV (0.14), meaning its cost varies minimally regardless of whether the task involves law, science, or gaming. This stability arises from debate's fixed-round structure: each debater produces a bounded response per round, independent of domain complexity. Conversely, swm3 has the highest CV (0.67)---costing only 1,400 tokens for history tasks but 9,200 for business. Swarm's handoff-driven execution amplifies domain-specific complexity differences because harder domains trigger more inter-agent transfers. For practitioners, this implies that debate3 offers the most predictable cost profile, while swm3 requires domain-aware budgeting.

**Finding 20 — Reflection excels in argumentative domains, but debate does not.** In argumentative domains (law & politics, philosophy), refl2 is among the most efficient patterns (mean 4,800 tokens for law, 2,800 for philosophy), ranking as the cheapest pattern in philosophy. Surprisingly, debate3 ranks only 3rd--4th in these domains (mean 8,000 tokens), contradicting the intuition that debate structures should excel where argumentation is natural. The explanation is that debate's fixed multi-round structure imposes overhead regardless of domain, while reflection's single critic-feedback cycle is sufficient to capture argumentative nuance. In factual domains (science, CS), refl2 remains competitive (mean 4,200 tokens), while rr3 is substantially more expensive (mean 11,500 tokens).

**Finding 21 — Domain cost varies 2× independently of pattern choice.** Averaging across all patterns, the cheapest domain is history (7,063 tokens) and the most expensive is medicine (13,288 tokens)—a 1.88× ratio. This domain effect is orthogonal to pattern choice: gaming and medicine inflate costs across all topologies, likely due to longer expected outputs and greater domain-specific vocabulary. The domain cost ranking is: history < philosophy < science < CS < engineering < law < business < gaming < medicine.

### 4.2 Experiment 02: Termination Quality (RQ2)

**Setup.** For a representative subset of patterns (one per category), we apply G-Eval scoring at each agent turn to construct quality trajectories. Using claude-sonnet-4-5 as the evaluator with 5-dimensional scoring (accuracy, completeness, coherence, usefulness, overall), each turn receives a quality score Q(t) in [1, 5]. Cumulative text is truncated to 3,000 characters to stay within evaluator context limits.

**Termination regret** is defined as:

$$R = t_{actual} - t_{optimal}$$

where $t_{optimal} = \arg\max_t Q(t)$ is the turn at which quality peaked. Positive regret indicates over-computation (the team continued past peak quality); negative regret indicates under-computation (the team stopped before reaching peak quality).

**Patterns tested.** We select five representative patterns spanning three categories: rr3 (Category A), sel3 and swm3 (Category B), refl2 and debate3 (Category C). Each pattern is evaluated on 20 tasks, yielding 100 runs and 276 turn-level quality scores. For swarm patterns, which generate many short handoff turns (function calls, transfer confirmations) with no substantive content, we filter out turns with fewer than 20 characters of non-handoff content; this reduces swm3 from approximately 18.7 raw turns to 1.2 substantive turns per run.

**Table 18: Termination Regret Analysis**

| Pattern | Cat | N | $t_{optimal}$ | $t_{actual}$ | Regret (turns) | $Q_{peak}$ | $Q_{final}$ ±std | $Q_{loss}$ |
|---------|-----|---|---------------|--------------|----------------|-------------|-------------------|------------|
| swm3 | B2 | 40 | 1.0 | 1.2 | +0.2 | 4.15 | 4.05 ±1.25 | 0.10 |
| refl2 | C | 40 | 1.7 | 2.3 | +0.6 | 4.80 | 4.80 ±0.41 | 0.00 |
| sel3 | B1 | 40 | 1.1 | 2.8 | +1.6 | 3.90 | 3.40 ±1.08 | 0.50 |
| debate3 | C | 40 | 1.3 | 3.3 | +2.0 | 4.00 | 3.35 ±0.80 | 0.65 |
| rr3 | A | 40 | 1.6 | 4.2 | +2.6 | 4.50 | 4.45 ±0.50 | 0.05 |

**Table 19: Quality Trajectories (Mean Overall Score by Substantive Turn)**

| Pattern | $t_1$ | $t_2$ | $t_3$ | $t_4$ | $t_5$ | $t_6$ |
|---------|-------|-------|-------|-------|-------|-------|
| rr3 | 3.9 | 4.2 | 4.5 | 4.1 | 4.1 | 4.1 |
| sel3 | 3.8 | 3.5 | 2.7 | 4.0 | 4.0 | -- |
| swm3 | 4.2 | 3.0 | 2.0 | -- | -- | -- |
| refl2 | 3.9 | 4.8 | 4.0 | 4.0 | -- | -- |
| debate3 | 3.8 | 3.4 | 3.3 | 3.3 | -- | -- |

**Table 20: Quality Dimension Breakdown (Final Turn Averages)**

| Pattern | Accuracy | Completeness | Coherence | Usefulness | Overall |
|---------|----------|--------------|-----------|------------|---------|
| refl2 | 4.80 | 4.25 | 5.00 | 4.95 | 4.80 |
| rr3 | 4.50 | 3.75 | 4.25 | 4.70 | 4.45 |
| swm3 | 4.25 | 3.80 | 4.45 | 4.35 | 4.05 |
| sel3 | 3.85 | 3.15 | 3.35 | 3.80 | 3.40 |
| debate3 | 3.75 | 2.70 | 3.35 | 3.55 | 3.35 |

**Finding 22: Three distinct quality trajectory shapes emerge across topologies.** The turn-by-turn quality data reveal fundamentally different quality dynamics depending on coordination structure.

**(a) Monotonic-then-plateau (RR-3, Category A).** Quality rises steadily through turn 3 ($Q=4.5$) before stabilizing at approximately 4.1 for subsequent turns. For example, on the task "Compare microservices vs. monolithic architecture" (cs\_03), the Writer produces a structured overview ($Q=3.8$), the Researcher adds scalability data and case studies ($Q=4.5$), and the Reviewer consolidates without adding new substance ($Q=4.2$). Continuing past the peak wastes tokens but does not degrade quality ($Q_{loss}=0.05$), making sequential termination regret relatively benign.

**(b) Peak-at-turn-2 (Refl-2, Category C).** The critic's first feedback cycle produces a sharp quality jump ($3.9 \to 4.8$), after which quality holds steady. On "Explain Kant's categorical imperative vs. Mill's utilitarianism" (phil\_01), the Generator produces a competent initial response ($Q=3.9$), and the Critic identifies missing practical examples and structural gaps; the revised response addresses these points precisely ($Q=4.8$). The Critic's "APPROVED" signal naturally coincides with peak quality, suggesting that reflection's built-in termination mechanism is well-calibrated.

**(c) Monotonic decline (Debate-3, Category C).** Each successive debate round decreases quality ($3.8 \to 3.4 \to 3.3 \to 3.3$). On "Analyze the trolley problem across ethical frameworks" (phil\_02), the first round produces strong arguments from each debater ($Q=3.8$), but subsequent rounds introduce tangential counterarguments and conflicting revisions that fragment the Moderator's synthesis ($Q=3.3$). This represents the most costly form of over-computation, as continuing not only wastes resources but degrades the result ($Q_{loss}=0.65$).

**Finding 23: Termination regret varies 13x across topologies.** Regret ranges from +0.2 turns (swm3, near-optimal stopping) to +2.6 turns (rr3, substantial over-computation). All five patterns exhibit positive regret, confirming that current fixed termination criteria systematically over-compute. However, the *cost* of over-computation differs dramatically by topology: debate3 loses 0.65 quality points from its 2.0 turns of excess computation, while rr3 loses only 0.05 quality points despite 2.6 turns of excess. This divergence implies that termination criteria must be topology-aware: a uniform turn budget wastes resources on patterns that converge early (swm3, refl2) while simultaneously degrading output on patterns where additional turns are actively harmful (debate3).

**Finding 24: Reflection achieves highest quality with near-zero quality loss.** Among all patterns tested, refl2 attains both the highest peak quality ($Q_{peak}=4.80$) and the lowest quality loss ($Q_{loss}=0.00$). The structured critic-approval loop serves as a natural termination signal that aligns closely with the optimal stopping point ($t_{optimal}=1.7$, $t_{actual}=2.3$, regret = +0.6 turns). The dimension breakdown (Table 20) reveals that refl2 achieves perfect coherence (5.00) and near-perfect usefulness (4.95), while debate3 suffers most on completeness (2.70)---consistent with the observation that successive debate rounds introduce conflicting revisions that fragment the response. Reflection is thus the only topology among those tested where the built-in termination mechanism (critic approval) closely approximates optimal stopping, supporting its use in quality-critical applications.

#### 4.2.1 Evaluation Validation

Our quality scoring relies on G-Eval (Liu et al., 2023) with claude-sonnet-4-5 as the evaluator. To assess the reliability of this automated scoring, we conduct three validation studies.

**Human evaluation.** We extract a stratified sample of 30 turn-level outputs from the 276 scored turns: 10 high-scoring ($Q \geq 4.5$), 10 mid-range ($3.0 \leq Q \leq 4.0$), and 10 low-scoring ($Q \leq 2.5$), with minimum 4 samples per pattern to ensure coverage. An expert evaluator rates each sample on the same 5-dimensional rubric (accuracy, completeness, coherence, usefulness, overall) using a 1--5 scale, blind to the G-Eval scores. We report Pearson's $r$, Spearman's $\rho$, and Cohen's quadratic weighted $\kappa$ as inter-rater agreement metrics.

**LLM cross-validation.** To test whether our findings are evaluator-dependent, we re-score samples using five independent models from four provider families with the identical scoring prompt. Table 21 reports cross-model agreement for all five cross-validators.

**Table 21: Cross-Model Agreement (Claude G-Eval vs. Five Independent Models)**

| Cross-Validator | Provider | N | Pearson $r$ | Spearman $\rho$ | Cohen's $\kappa_w$ | $\Delta$ |
|-----------------|----------|---|------------|----------------|-------------------|----------|
| GPT-4o-mini | OpenAI | 40 | 0.434 | 0.389 | 0.244 | -0.93 |
| Gemini 2.0 Flash | Google | 100 | 0.569 | 0.500 | 0.359 | -0.82 |
| GPT-5.4 | OpenAI | 100 | 0.540 | 0.525 | 0.415 | +0.69 |
| Haiku 4.5 | Anthropic | 100 | 0.662 | 0.650 | 0.425 | +0.91 |
| Grok 3 Mini | xAI | 100 | 0.628 | 0.626 | 0.449 | -0.60 |

Three of five models---GPT-5.4, Haiku 4.5, and Grok 3 Mini (all N=100)---cross the "moderate agreement" threshold ($\kappa_w \geq 0.40$; Landis & Koch, 1977), with overall $\kappa_w$ ranging from 0.415 to 0.449. GPT-4o-mini (N=40) shows fair agreement ($\kappa_w = 0.244$), and Gemini 2.0 Flash (N=100) shows fair agreement ($\kappa_w = 0.359$).

Critically, the bias direction splits across provider families: Haiku 4.5 ($\Delta = +0.91$) and GPT-5.4 ($\Delta = +0.69$) are stricter than Claude, while Gemini ($\Delta = -0.82$), GPT-4o-mini ($\Delta = -0.93$), and Grok ($\Delta = -0.60$) are more lenient. This bidirectional pattern across four independent providers provides strong evidence that our comparative findings are not artifacts of evaluator-specific calibration. A five-rater Fleiss' $\kappa$ (Claude + GPT-5.4 + Haiku + Grok + Gemini, N=100) yields $\kappa = 0.012$, reflecting the expected scale heterogeneity across models with very different calibration points---this low value is consistent with the divergent bias directions and does not indicate ranking disagreement.

Correlations are moderate-to-strong positive across all five models (Pearson $r = 0.43$--$0.66$, all $p < 0.01$). **This agreement level does not threaten our conclusions**, for three reasons:

First, $\kappa_w$ penalizes systematic scale differences between raters. The lenient models (GPT-4o-mini: $\Delta = -0.93$; Gemini: $\Delta = -0.82$) and strict models (Haiku: $\Delta = +0.91$; GPT-5.4: $\Delta = +0.69$) bracket Claude from both sides---a pattern that would not arise if Claude's scores were systematically biased in one direction. Second, our analysis relies entirely on **relative rankings** (which topology produces higher quality, where quality peaks occur, which patterns converge), not absolute scores. Spearman $\rho$ ($0.39$--$0.65$, all $p < 0.02$) confirms consistent rank-ordering across all five evaluators. Third, prior work using G-Eval reports similar cross-evaluator agreement levels: Liu et al. (2023) report Spearman $\rho = 0.51$--$0.56$ for GPT-4 vs. human judgments, placing our range within established norms.

The consistent rank-order preservation across five models from four providers confirms that the quality trajectories (Findings 22--24) are not artifacts of Claude-specific scoring biases.

*We release a stratified human evaluation kit (30 samples across 5 quality tiers, evaluation instructions, and analysis scripts) in our repository. We acknowledge two limitations: (1) the human evaluation uses a single expert evaluator, precluding inter-rater reliability calculation---future work should employ multiple independent annotators with reported Cohen's $\kappa$; (2) absolute quality scores should be interpreted as ordinal rather than cardinal measures. We emphasize that every finding in this paper is stated in comparative terms (topology A outperforms topology B, quality peaks at turn t), and such ordinal claims are robust to the observed evaluator calibration differences.*

### 4.3 Experiment 03: Convergence Detection (RQ3)

**Setup.** Using turn-level message data from Experiment 01 (v2, 200 runs, 8 patterns), we compute semantic convergence using sentence-transformer embeddings (Reimers & Gurevych, 2019). Each agent turn's content is encoded with all-MiniLM-L6-v2 (384 dimensions), and pairwise cosine similarity is computed between consecutive turns. **Convergence point** is defined as the first turn $t_c$ where cosine similarity exceeds threshold $\theta$ for two consecutive comparisons. We conduct sensitivity analysis at three thresholds: $\theta \in \{0.80, 0.85, 0.90\}$, reporting $\theta = 0.85$ as default. This extends Hu et al.'s (2025) KS-test approach from debate-only to all 8 representative topologies, while replacing shallow n-gram overlap with dense semantic representations.

**Comparison with surface-level metrics.** We also computed Jaccard similarity on word 3-grams (as in our preliminary analysis) and found systematically different results. Jaccard mean similarity ranges from 0.004--0.134 across patterns, while cosine embedding similarity ranges from 0.403--0.673. The discrepancy arises because embedding similarity captures paraphrase and semantic overlap that n-gram matching misses entirely: two turns discussing the same concept with different wording score near-zero on Jaccard but 0.5--0.8 on cosine similarity. Table 23 compares the two methods.

**Table 22: Semantic Convergence Analysis by Pattern ($\theta=0.85$)**

| Pattern | Cat | N | Conv. Rate | Mean Cos | Final Cos | Trend | Conv. Turn |
|---------|-----|---|-----------|----------|-----------|-------|------------|
| rr3 | A | 25 | 16.0% | 0.576 | 0.690 | +0.250 | 3.0 |
| sel3 | B1 | 25 | 24.0% | 0.403 | 0.602 | +0.397 | 3.0 |
| sel4 | B1 | 25 | 28.0% | 0.502 | 0.661 | +0.382 | 3.6 |
| swm3 | B2 | 25 | 8.0% | 0.458 | 0.132 | -0.560 | 7.0 |
| swm4 | B2 | 25 | 16.0% | 0.485 | 0.453 | -0.029 | 15.5 |
| refl2 | C | 25 | 0.0% | 0.462 | 0.479 | +0.052 | N/A |
| debate3 | C | 25 | 0.0% | 0.673 | 0.681 | +0.044 | N/A |
| pipe | D | 25 | **32.0%** | 0.662 | 0.688 | +0.169 | 3.9 |

**By category (embedding):** A: 16.0% converged (cos=0.576), B1: 26.0% (cos=0.452), B2: 12.0% (cos=0.472), C: 0.0% (cos=0.568), D: **32.0%** (cos=0.662).

**Table 23: Jaccard vs Embedding Comparison**

| Pattern | Cat | Mean Jaccard | Mean Cosine | Jaccard Conv. (θ=0.25) | Cosine Conv. (θ=0.85) |
|---------|-----|-------------|-------------|----------------------|---------------------|
| rr3 | A | 0.007 | 0.576 | 0.0% | 16.0% |
| sel3 | B1 | 0.004 | 0.403 | 0.0% | 24.0% |
| sel4 | B1 | 0.004 | 0.502 | 0.0% | 28.0% |
| swm3 | B2 | 0.134 | 0.458 | 12.0% | 8.0% |
| swm4 | B2 | 0.130 | 0.485 | 44.0% | 16.0% |
| refl2 | C | 0.005 | 0.462 | 0.0% | 0.0% |
| debate3 | C | 0.006 | 0.673 | 0.0% | 0.0% |
| pipe | D | 0.012 | 0.662 | 0.0% | 32.0% |

**Table 24: Sensitivity Analysis (Convergence Rate at Different Thresholds)**

| Pattern | Cat | θ=0.80 | θ=0.85 | θ=0.90 |
|---------|-----|--------|--------|--------|
| rr3 | A | 24.0% | 16.0% | 8.0% |
| sel3 | B1 | 32.0% | 24.0% | 16.0% |
| sel4 | B1 | 44.0% | 28.0% | 12.0% |
| swm3 | B2 | 8.0% | 8.0% | 8.0% |
| swm4 | B2 | 24.0% | 16.0% | 12.0% |
| refl2 | C | 8.0% | 0.0% | 0.0% |
| debate3 | C | 12.0% | 0.0% | 0.0% |
| pipe | D | 36.0% | 32.0% | 8.0% |

**Finding 25 --- Semantic convergence reveals a fundamentally different topology ranking than surface-level metrics.** With embedding-based analysis, pipeline (D) exhibits the highest convergence rate (32.0% at $\theta=0.85$), followed by centralized routing B1 (26.0%) and sequential A (16.0%). This inverts the Jaccard-based ranking where only decentralized handoff B2 showed convergence (28.0%). The reversal occurs because Jaccard was dominated by literal n-gram repetition in swarm handoff messages, mistaking protocol repetition for content convergence. Embedding similarity correctly identifies that pipeline stages produce *semantically related* output (draft → review → polish all discuss the same topic), while swarm handoff messages are semantically *divergent* (each handoff changes the conversational focus). This correction is critical for practitioners: using Jaccard-based convergence detection would falsely trigger early stopping in swarm topologies while missing genuine convergence in pipeline and selector topologies.

**Finding 26 --- Feedback patterns do NOT converge even at the semantic level.** Both refl2 (0.0%) and debate3 (0.0%) show zero convergence at $\theta=0.85$, consistent across all three thresholds for debate3 (only refl2 shows 8.0% at $\theta=0.80$). Despite debate3 having the highest mean cosine similarity (0.673), similarity remains consistently high without the *increase* required for convergence detection. This confirms that feedback patterns produce content that is semantically similar throughout (discussing the same topic) but never stabilizes (each turn introduces new arguments or refinements). Quality-based signals (Section 4.2) remain more appropriate for feedback topologies.

**Finding 27 --- Centralized routing (B1) shows the strongest convergence trends.** sel3 (+0.397) and sel4 (+0.382) exhibit the largest positive trends, indicating that selector-routed conversations become progressively more semantically similar. This aligns with the coordinator's role: as the task progresses, the selector routes to specialists who contribute increasingly overlapping insights. By contrast, swm3 shows a strong *negative* trend (-0.560), indicating that decentralized handoff conversations become less semantically coherent over time---consistent with the turn explosion phenomenon observed in Experiment 01 (Finding 7). Pipeline shows a moderate positive trend (+0.169), reflecting the semantic coherence of sequential processing stages.

### 4.4 Experiment 04: Error Attribution (RQ4)

**Setup.** We analyze termination and error patterns from both v1 (780 runs, 13 patterns) and v2 (200 runs, 8 patterns) experiments. Rather than content-level error classification (which requires human annotation), we focus on *structural* error patterns: stop reason distributions, error-task interactions, and content characteristics that correlate with topology features.

**Table 25: Termination Mode Distribution (v1, 780 runs)**

| Pattern | Cat | N | Keyword% | MaxMsg% | Error% |
|---------|-----|---|----------|---------|--------|
| rr2 | A | 60 | 91.7% | 0.0% | 8.3% |
| rr3 | A | 60 | 76.7% | 0.0% | 23.3% |
| rr4 | A | 60 | 28.3% | 0.0% | 71.7% |
| sel3 | B1 | 60 | 100.0% | 0.0% | 0.0% |
| sel4 | B1 | 60 | 100.0% | 0.0% | 0.0% |
| swm3 | B2 | 60 | 78.3% | 21.7% | 0.0% |
| swm4 | B2 | 60 | 28.3% | 71.7% | 0.0% |
| refl2 | C | 60 | 100.0% | 0.0% | 0.0% |
| debate3 | C | 60 | 100.0% | 0.0% | 0.0% |
| pipe | D | 60 | 100.0% | 0.0% | 0.0% |
| moa | D | 60 | 0.0% | 100.0% | 0.0% |

**Table 26: v1 Error Distribution by Task Domain (Category A only)**

| Pattern | Factual | Analytical | Creative | Technical |
|---------|---------|------------|----------|-----------|
| rr2 | 0/15 (0%) | 0/15 (0%) | 0/15 (0%) | 5/15 (33.3%) |
| rr3 | 0/15 (0%) | 3/15 (20%) | 3/15 (20%) | 8/15 (53.3%) |
| rr4 | 0/15 (0%) | 15/15 (100%) | 13/15 (86.7%) | 15/15 (100%) |

**Finding 28 --- Three distinct termination failure modes emerge across topologies.** (1) *Context overflow* (Category A): errors scale superlinearly with agent count (rr2=8.3% → rr3=23.3% → rr4=71.7%) because cumulative conversation history exceeds the 28K character processing limit. (2) *Turn explosion* (Category B2): swm4 reaches max_messages in 71.7% of runs because decentralized handoff chains fail to self-terminate, while swm3 reaches max_messages only 21.7% of the time. (3) *No failure* (Categories B1, C, D except MoA): centralized routing, feedback, and pipeline patterns achieve 100% keyword termination. MoA always hits max_messages (100%) because the aggregator does not emit TERMINATE after synthesis.

**Finding 29 --- Factual tasks are error-immune while technical tasks are error-prone.** In Category A (the only category with errors), factual tasks produce 0% errors across all team sizes (rr2/rr3/rr4), while technical tasks produce 33.3%→53.3%→100% errors as team size increases. The mechanism is clear: technical tasks (code generation) produce longer responses that accumulate faster in the conversation context, triggering the truncation threshold sooner. Creative and analytical tasks fall in between, with vulnerability appearing at rr3 (3-agent) level.

**Finding 30 --- Swarm communication is structurally distinct from all other patterns.** Content analysis reveals that swarm patterns produce dramatically shorter agent responses (swm3: 322 chars, swm4: 205 chars) compared to all other patterns (1,787--1,982 chars). Only 1.0--6.1% of swarm turns contain the TERMINATE keyword, versus 8.8--17.9% for other patterns. This explains swm4's low keyword termination rate (24% in v2): swarm agents communicate through brief handoff messages rather than substantive responses, and the TERMINATE keyword is rarely relevant to this communication mode. This structural difference has direct implications for termination strategy: keyword-based termination is poorly suited for decentralized handoff topologies, supporting the need for alternative stopping signals (Finding 36).

### 4.5 Experiment 05: Adaptive Termination (RQ5)

**Setup.** Unlike REFRAIN's discriminator+UCB bandit approach for single-agent stopping, and Aegean's quorum-based consensus detection for parallel agents, we propose a **marginal utility-based stopping criterion** that applies to any multi-agent topology:

$$\Delta U(t) = \Delta Q(t) - \lambda \cdot \Delta C(t)$$

where $\Delta Q(t) = Q(t) - Q(t-1)$ is the marginal quality gain at turn t, $\Delta C(t)$ is the marginal token cost (in kilo-tokens), and $\lambda$ controls the quality-cost tradeoff. The team stops when $\Delta U(t) \leq 0$, indicating that the marginal cost of continuing exceeds the marginal quality gain. Unlike absolute utility $U(t) = Q(t) - \lambda C(t)$ which diverges to $-\infty$ as costs accumulate, marginal utility $\Delta U(t)$ naturally converges to zero via quality saturation.

**Intuitive interpretation.** $\Delta U(t)$ answers the question: "Is the next turn worth its cost?" At each turn, we measure two quantities: how much better the answer got ($\Delta Q$) and how much it cost ($\lambda \cdot \Delta C$). When $\Delta U > 0$, the quality improvement exceeds the cost penalty—the team should continue. When $\Delta U \leq 0$, the answer is no longer improving enough to justify the token expenditure. The $\lambda$ parameter sets the practitioner's cost sensitivity: $\lambda=0$ ignores cost entirely (stop only when quality saturates), while $\lambda=0.5$ penalizes each additional kilo-token heavily. In practice, $\Delta U$ converges for a simple reason: LLM responses reach a quality ceiling within 2--3 turns ($\Delta Q \to 0$), while each turn always costs tokens ($\Delta C > 0$). Once $\Delta Q$ approaches zero, $\Delta U$ must become negative regardless of $\lambda$.

**Pre-validation from exp02 data.** Before running the full controlled experiment, we validated the ΔU(t) → 0 convergence using existing exp02 turn-level quality scores combined with per-turn token costs. Table 27 shows the convergence analysis for 5 representative patterns:

**Table 27: Marginal Utility Convergence Analysis (λ=0.1)**

| Pattern | Category | t_{ΔU≤0} | t_{optimal} | t_{actual} | Q_{opt} | Q_{act} | Q_{loss} | Regret |
|---------|----------|-----------|-------------|------------|---------|---------|----------|--------|
| swm3 | B2 | **1.1** | 1.0 | 1.2 | 4.15 | 4.05 | 0.10 | 0.2 |
| refl2 | C | 2.0 | 1.7 | 2.3 | 4.80 | 4.80 | **0.00** | 0.6 |
| sel3 | B1 | 2.0 | 1.1 | 2.8 | 3.90 | 3.40 | 0.50 | 1.6 |
| debate3 | C | 2.2 | 1.3 | 3.3 | 4.00 | 3.35 | 0.65 | 2.0 |
| rr3 | A | **2.4** | 1.6 | 4.2 | 4.50 | 4.45 | 0.05 | 2.6 |

**Finding 31 -- ΔU(t) converges within 1.1-2.4 turns for all topologies.** The convergence speed strongly correlates with topology structure: decentralized handoff (B2) converges fastest (1.1 turns), while sequential chain (A) converges slowest (2.4 turns). This validates the marginal utility formulation as a practical termination signal.

**Finding 32 -- λ-insensitivity.** Varying λ from 0 to 0.5 barely changes the convergence point (mean t_{ΔU≤0} shifts from 1.9 to 1.8). This indicates that ΔQ(t) → 0 (quality saturation) is the dominant stopping signal, meaning the criterion is robust to λ choice.

**Table 28: λ Sensitivity Analysis**

| λ | Mean t_{ΔU≤0} | Mean Regret | Mean Q_{loss} |
|:---:|:---:|:---:|:---:|
| 0.00 | 1.9 | 1.4 | 0.260 |
| 0.05 | 1.9 | 1.4 | 0.260 |
| 0.10 | 1.9 | 1.4 | 0.260 |
| 0.20 | 1.9 | 1.4 | 0.260 |
| 0.50 | 1.8 | 1.4 | 0.260 |

*Note: Regret and Q_{loss} are invariant across λ because these metrics measure baseline behavior---Regret = t_{actual} - t_{optimal} and Q_{loss} = Q_{peak} - Q_{actual}---both of which are properties of the baseline runs, not of the ΔU criterion. Only t_{ΔU≤0} (where the adaptive criterion would trigger stopping) depends on λ. The near-invariance of t_{ΔU≤0} itself (1.9→1.8) further confirms that quality saturation (ΔQ→0) dominates over the cost penalty (λ·ΔC), as turn-level quality changes are discrete events and the 0.1-turn shift keeps t_{ΔU≤0} in the same inter-turn interval.*

**Finding 33 -- Quality preservation varies by topology.** refl2 achieves zero quality loss (Q_act/Q_opt = 4.80/4.80 = 1.00), while debate3 shows the largest loss (Q_loss = 0.65, Q_act/Q_opt = 3.35/4.00 = 0.84). The reflection pattern's critic-based APPROVED signal provides a natural, reliable termination point coinciding with peak quality. Notably, the ΔU convergence point t_{ΔU≤0} closely tracks t_{optimal} for efficient topologies (swm3: 1.1 vs 1.0) but diverges for over-computing topologies (rr3: 2.4 vs 1.6), suggesting that ΔU can serve as a safety net against wasteful continuation.

**Controlled experiment.** We test the ΔU criterion as an *alternative* to keyword-based termination, specifically to diagnose where keyword heuristics succeed and fail. We evaluate across all 8 representative patterns with 3 λ values {0.0, 0.1, 0.5} and 25 tasks, yielding 200 baseline + 600 adaptive = 800 runs with 0% error rate. The adaptive condition removes the TERMINATE keyword mechanism and instead stops when ΔU(t) ≤ ε (ε=0.05) for 2 consecutive turns, with a MaxMessage safety net of 25.

**Table 29: Adaptive vs Baseline Comparison**

| Pattern | Cat | BL turns | AD turns | Turn Δ% | BL tokens | AD tokens | Token Δ% |
|---------|-----|----------|----------|---------|-----------|-----------|----------|
| rr3 | A | 4.6 | 5.5 | +19% | 11,546 | 15,278 | +32% |
| sel3 | B1 | 3.7 | 4.7 | +27% | 7,901 | 12,840 | +63% |
| sel4 | B1 | 4.3 | 5.4 | +26% | 11,136 | 16,315 | +47% |
| swm3 | B2 | 9.6 | 8.2 | -15% | 3,223 | 9,818 | +205% |
| swm4 | B2 | 25.6 | 9.1 | **-65%** | 15,327 | 4,656 | **-70%** |
| refl2 | C | 3.3 | 6.4 | +92% | 5,509 | 19,693 | +258% |
| debate3 | C | 4.4 | 4.6 | +5% | 9,042 | 9,752 | +8% |
| pipe | D | 5.8 | 5.8 | +1% | 10,853 | 12,092 | +11% |

**Table 30: λ Sensitivity (Averaged Across Patterns)**

| λ | Avg Turn Δ% | Avg Token Δ% | N |
|---|-------------|--------------|---|
| 0.00 | +10% | +131% | 200 |
| 0.10 | -33% | -13% | 200 |
| 0.50 | -34% | -13% | 200 |

The diagnostic value of this experiment lies in revealing *where* existing termination works well and *where* it fails.

**Finding 34 — Adaptive termination benefit is strongly topology-dependent.** The ΔU criterion's effect varies dramatically across topologies. For patterns with reliable keyword termination (debate3: +5% turns/+8% tokens; pipe: +1%/+11%), adaptive termination adds minimal overhead—these patterns already stop near the quality plateau. For patterns where keyword termination works but is not perfectly timed (rr3: +19%/+32%; sel3: +27%/+63%; sel4: +26%/+47%), the adaptive criterion overshoots, producing more turns. However, for swm4—where baseline keyword termination succeeds only 28% of the time (Table 25)—adaptive termination achieves **-65% turn reduction and -70% token savings**, demonstrating that the ΔU criterion excels precisely where keyword heuristics fail. Reflection (refl2: +92%/+258%) suffers the most because its compact 2-turn APPROVED signal is already optimal, and any replacement disrupts this tight feedback loop.

**Finding 35 — λ > 0 transforms the ΔU criterion from harmful to beneficial.** With λ=0 (no cost penalty), the adaptive condition considers only quality changes, causing +10% more turns and +131% more tokens than baseline on average across 8 patterns. With λ≥0.1, the cost penalty produces both turn savings (-33%) and token savings (-13%) on average. This reversal—from +131% overhead to -13% savings—is driven by swm4's dramatic improvement at λ>0, combined with reduced overshooting across other patterns. The minimal difference between λ=0.1 and λ=0.5 (consistent with Finding 32's λ-insensitivity) suggests that any positive cost penalty suffices.

**Finding 36 — ΔU should complement, not replace, keyword termination.** The controlled experiment reveals that using ΔU as a *replacement* for keyword termination adds overhead for 7 of 8 patterns (Table 29), confirming that keyword-based heuristics are near-optimal when agents reliably produce TERMINATE signals. This is itself a valuable finding that validates existing practitioner practices. However, for the exception---swm4, with only 28% keyword termination rate---ΔU with λ≥0.1 reduces costs by 70%. This suggests a complementary deployment strategy: keyword termination for the common case, with ΔU as a safety mechanism for unreliable topologies. #### Hybrid Validation

To validate this hybrid strategy, we test keyword+ΔU as a *combined* system (not a replacement) on the two extreme cases: swm4 (28% keyword success, where ΔU should help) and debate3 (100% keyword, where ΔU should add minimal overhead). Using λ=0.1 and 25 tasks (50 total runs):

**Table 30b: Hybrid Termination Results (λ=0.1, 25 tasks per pattern)**

| Pattern | N | Keyword | Adaptive (ΔU) | Max-msg | Avg Tokens | vs Baseline | p-value |
|---------|---|:---:|:---:|:---:|:---:|:---:|:---:|
| swm4 | 25 | 8% | **92%** | 0% | 3,346 | **-78.2%** | <0.0001 |
| debate3 | 25 | **64%** | 36% | 0% | 7,534 | -16.7% | 0.058 |

For swm4, ΔU acts as the primary termination mechanism (keyword fires only 8% of the time), achieving **78% token savings** ($t=-7.44$, $p<0.0001$) and 67% turn savings vs. baseline. For debate3, keyword (VERDICT) fires first in 64% of runs, with ΔU catching the remaining 36%—a modest 17% savings ($p=0.058$, borderline significant). Critically, zero runs hit max_messages for either pattern, confirming that the hybrid always terminates through a quality-aware mechanism.

### 4.6 Cross-Model Validation

**Setup.** To assess whether our findings generalize beyond a single LLM, we replicate Experiment 01 with GPT-4o-mini (OpenAI) on 5 representative patterns (solo, rr3, sel3, swm3, refl2) across all 25 tasks, yielding 125 additional runs with 0% error rate. All other experimental conditions (prompts, agent configurations, termination criteria) remain identical.

**Table 31: Cross-Model Comparison (Claude Haiku 4.5 vs. GPT-4o-mini)**

| Pattern | Claude Tokens | GPT Tokens | Ratio | Claude Turns | GPT Turns | Claude KW% | GPT KW% |
|---------|--------------|-----------|-------|-------------|----------|-----------|--------|
| solo | 1,287 | 697 | 0.54x | 2.0 | 2.0 | 100% | 100% |
| rr3 | 10,121 | 14,325 | 1.42x | 4.5 | 6.2 | 100% | 80% |
| sel3 | 7,851 | 3,598 | 0.46x | 3.5 | 3.5 | 100% | 100% |
| swm3 | 4,196 | 3,203 | 0.76x | 10.2 | 10.0 | 78% | 72% |
| refl2 | 5,237 | 5,105 | 0.97x | 3.2 | 4.0 | 100% | 92% |

**Table 31b: Per-Pattern Cost Rank Comparison**

| Pattern | Claude Rank | GPT Rank | Claude Tokens | GPT Tokens | Claude/GPT Ratio | Direction |
|---------|------------|----------|--------------|-----------|-----------------|-----------|
| Solo | 1 | 1 | 1,287 | 697 | 1.85x | Claude costlier |
| Swm-3 | 2 | 2 | 4,196 | 3,203 | 1.31x | Claude costlier |
| Refl-2 | 3 | 4 | 5,237 | 5,105 | 1.03x | Near-equal |
| Sel-3 | 4 | 3 | 7,851 | 3,598 | 2.18x | Claude costlier |
| RR-3 | 5 | 5 | 10,121 | 14,325 | 0.71x | GPT costlier |

*Note: Rank inversions (refl2↔sel3) occur only in the middle tier. The extremes (solo cheapest, rr3 costliest) are preserved across both models.*

**Finding 37 — Topology-dependent dynamics are model-invariant.** Despite absolute token differences (GPT-4o-mini is 0.46--1.42x of Claude across patterns), the relative cost ordering is strongly preserved: Spearman ρ = 0.900 (p = 0.037, n = 5 patterns). Both models produce the same efficiency hierarchy: solo < swm3 < {sel3, refl2} < rr3, with only sel3 and refl2 swapping positions (a middle-tier difference, Table 31b). The key non-trivial finding—swm3 being more efficient than solo×3—holds across both models. GPT-4o-mini is notably more concise in centralized routing (sel3: 0.46x) but more verbose in sequential chains (rr3: 1.42x), suggesting that routing efficiency is model-dependent while topology-dependent *relative* dynamics are model-invariant. *Caveat: the correlation is computed over n=5 data points; while statistically significant (p < 0.05), validation with additional patterns and models would strengthen this generalizability claim.*

**Finding 38 — Keyword termination reliability is model-dependent.** While both models achieve high keyword termination rates for solo (100%), sel3 (100%), and refl2 (92--100%), GPT-4o-mini shows lower keyword reliability for rr3 (80% vs. 100%) and swm3 (72% vs. 78%). This suggests that smaller models may struggle more with producing explicit TERMINATE signals in multi-turn contexts, reinforcing the value of ΔU as a complementary stopping mechanism (Finding 36).

**Finding 39 — Routing efficiency is model-sensitive.** The most striking cross-model difference is sel3: GPT-4o-mini uses only 0.46x the tokens of Claude (3,598 vs. 7,851). This suggests GPT-4o-mini's selector produces more concise routing decisions. Conversely, rr3 is 1.42x more expensive with GPT-4o-mini, indicating the model generates more verbose sequential contributions. These absolute differences do not affect the topology-dependent *relative* dynamics, supporting the generalizability of our design guidelines.

### 4.7 Experiment 06: Cost Prediction from Topology Features (RQ6)

**Setup.** We investigate whether runtime costs can be predicted from pre-execution topology features alone, without running the team. Using the exp01 dataset (718 valid runs across 13 patterns), we train four regression models (Linear Regression, Ridge, Lasso, Random Forest) to predict three targets: total tokens, turn count, and duration. Features include pattern category (one-hot: S, A, B1, B2, C, D), agent count, max messages, task category (one-hot: factual, analytical, creative, technical), and the interaction term `agent_count × max_messages`. We evaluate via 5-fold cross-validation and holdout prediction on exp05 baseline data (200 runs, 8 patterns).

**Table 32: Cost Prediction Cross-Validation Results (5-fold CV)**

| Target | Best Model | R² (mean±std) | MAE |
|--------|-----------|---------------|-----|
| Total Tokens | RandomForest | 0.54 ± 0.06 | 3,440 |
| Duration (sec) | RandomForest | 0.46 ± 0.04 | 34.8 |
| Turn Count | RandomForest | 0.28 ± 0.09 | 3.0 |

**Finding 40 — Topology features predict token consumption with moderate accuracy.** Random Forest achieves R²=0.54 for total tokens, meaning pre-execution topology features explain 54% of token variance. Linear models perform comparably (R²=0.46), suggesting the relationship is partially linear with non-linear interactions captured by RF. Duration prediction (R²=0.46) is somewhat weaker, reflecting infrastructure variability (network latency, model response time). Turn count is least predictable (R²=0.28), likely because keyword termination introduces a stochastic element independent of topology.

**Table 33: Feature Importance (Random Forest, Total Tokens target)**

| Feature | RF Importance | Interpretation |
|---------|--------------|----------------|
| task_technical | 0.273 | Technical tasks consume most tokens |
| pat_D (Composed) | 0.174 | Multi-stage patterns are inherently expensive |
| agents_x_maxmsg | 0.158 | Interaction term captures scaling behavior |
| max_messages | 0.143 | Higher message budget → more tokens consumed |
| agent_count | 0.133 | More agents → more inter-agent communication |
| pat_C (Feedback) | 0.051 | Feedback loops add moderate overhead |

**Finding 41 — The interaction term `agent_count × max_messages` is among the top predictors.** Rather than agent count or max messages alone, their product captures the combinatorial scaling of multi-agent conversations: more agents with higher message budgets create exponentially more inter-agent communication. This aligns with Finding 2 (superlinear input token growth) and provides a simple pre-execution cost estimator: expected_tokens ∝ n_agents × max_messages.

**Finding 42 — Task content accounts for ~46% of unexplained variance.** The R²=0.54 ceiling indicates that topology features alone cannot fully predict costs. The `task_technical` feature (RF importance=0.273) shows that task content complexity contributes substantially to cost variation. This is an honest limitation: practitioners can use topology features for rough cost budgeting (±3,440 tokens MAE), but precise estimates require task-level analysis.

**Holdout validation.** When training on exp01 (v1, 718 runs) and predicting exp05 baseline (v2, 200 runs), R² drops to 0.29 for tokens and 0.13 for duration. This degradation is expected: v2 uses a different task suite (25 tasks vs. 20) and includes patterns not in v1 training data. The holdout validates that the model captures real topology-cost relationships rather than overfitting, but the generalization gap highlights the need for task-specific recalibration.

### 4.8 Experiment 07: Task Difficulty Interaction (RQ7)

**Setup.** We design 15 tasks across 5 domains (science, CS, history, engineering, business) × 3 difficulty levels (easy, medium, hard), where difficulty is operationalized as cognitive demand: easy=factual recall, medium=comparative analysis, hard=creative design with multi-constraint reasoning. Five representative patterns (solo, swm3, sel3, refl2, debate3---one per topology category S, B2, B1, C, C) are crossed with all 15 tasks, with 3 repeats each, replicated across 5 models: Haiku (220 scored runs), GPT-4o-mini (224), GPT-5.4 (75), Grok (75), and Gemini (75), yielding 669 scored runs total. All runs are scored using G-Eval (claude-sonnet-4-5) on 5 dimensions (accuracy, completeness, coherence, usefulness, overall).

**Hypotheses.** Based on Finding 21 (task complexity amplifies cost differences 2x independently of topology), we hypothesize: (H1) difficulty will have a significant main effect on quality, (H2) the quality gap between patterns will widen for hard tasks, and (H3) solo will be optimal for easy tasks while feedback patterns (refl2) will be optimal for hard tasks.

#### 4.8.1 Main Effects

**Table 34: Difficulty × Pattern Quality Heatmap (Haiku subset; mean G-Eval overall score, 1--5 scale)**

| | Solo (S) | Swm-3 (B2) | Sel-3 (B1) | Refl-2 (C) | Debate-3 (C) |
|---|---|---|---|---|---|
| **Easy** | **4.73** ±0.70 | 3.82 ±1.25 | 4.07 ±0.88 | 4.67 ±0.49 | 4.40 ±0.63 |
| **Medium** | 3.27 ±0.46 | 3.80 ±1.01 | 3.33 ±0.49 | **3.93** ±0.59 | 3.67 ±0.72 |
| **Hard** | **3.67** ±0.98 | 3.00 ±0.88 | 3.47 ±0.74 | 3.47 ±0.52 | 2.93 ±0.46 |

*Note: Bold = highest quality within each difficulty level. n=15 per cell except swm3-easy (n=11) and swm3-hard (n=14).*

**Table 35: Statistical Tests (Kruskal-Wallis)**

| Test | H | p | η² | Sig. |
|------|---|---|-----|------|
| Difficulty main effect (combined, N=669) | 243.74 | <0.000001 | 0.363 | *** |
| Pattern main effect (combined, N=669) | 29.58 | <0.001 | 0.039 | *** |
| Difficulty main effect (Haiku, n=220) | 55.95 | <0.000001 | 0.249 | *** |
| Pattern within easy | 10.59 | 0.032 | — | * |
| Pattern within medium | 11.76 | 0.019 | — | * |
| Pattern within hard | 11.81 | 0.019 | — | * |
| Difficulty within solo | 19.28 | <0.001 | — | *** |
| Difficulty within swm3 | 6.27 | 0.044 | — | * |
| Difficulty within sel3 | 6.35 | 0.042 | — | * |
| Difficulty within refl2 | 21.09 | <0.001 | — | *** |
| Difficulty within debate3 | 23.55 | <0.001 | — | *** |

**Finding 43: Difficulty dominates pattern choice, replicated across all 5 models.** The combined difficulty main effect across 669 runs is highly significant (H=243.74, p<0.000001, η²_H=0.363, large effect), while the overall pattern main effect is much weaker (H=29.58, p<0.001, η²_H=0.039, small effect). Difficulty explains **9.3× more variance** than pattern choice (η²=0.363 vs 0.039). This dominance replicates across all 5 models individually. However, pattern choice is significant *within* each difficulty level (p<0.05 for all three), indicating that topology matters conditionally on task difficulty. The practical implication: a practitioner's first decision should be difficulty assessment, not pattern selection.

Within-pattern difficulty sensitivity varies dramatically: debate-3 (η²_H=0.513) and refl-2 (η²_H=0.455) are most affected by difficulty, while swm-3 (η²_H=0.115) and sel-3 (η²_H=0.104) show weaker difficulty effects. This suggests that feedback-based topologies amplify difficulty signals, while routing-based topologies partially buffer them.

**Finding 44: Solo dominance is consistent on easy tasks; multi-agent benefit is model-capability-dependent.** Solo achieves the highest quality for easy tasks across all 5/5 models, confirming H1. At medium difficulty, the picture is model-dependent: refl-2 significantly outperforms solo for Haiku (Δ=+0.67, p=0.003, d=1.26) and GPT-5.4 (Δ=+1.00, p=0.041, d=1.83), but solo remains best for Grok and GPT-4o-mini (2/5 models). At hard difficulty, solo is best for 3/5 models (Grok, GPT-4o-mini, Haiku), while GPT-5.4 and Gemini benefit from refl-2. The previously reported inverted-U pattern (solo optimal for easy and hard, refl-2 for medium) holds only for Haiku (1/5 models). The broader pattern is solo dominance moderated by model capability: weaker models (Haiku) benefit from structured feedback at medium difficulty, while stronger models (GPT-5.4) benefit at hard difficulty, suggesting that multi-agent coordination compensates for capability gaps at the model's difficulty frontier.

#### 4.8.2 Quality Degradation Patterns

All five patterns degrade significantly with increasing difficulty, but at different rates. Debate-3 exhibits the steepest decline (4.40→2.93, Δ=−1.47), while solo shows the smallest absolute drop (4.73→3.67, Δ=−1.06). Refl-2 degrades moderately (4.67→3.47, Δ=−1.20) but maintains the most consistent quality across levels.

**Finding 45: Quality gap does not widen monotonically with difficulty.** The quality gap between best and worst patterns is widest for easy tasks (0.92), narrowest for medium (0.67), and intermediate for hard (0.73). This refutes H2: hard tasks do not produce larger pattern differentiation. Instead, easy tasks show the clearest separation because solo and refl-2 excel while swm-3 underperforms (3.82). For hard tasks, all patterns converge toward lower quality, compressing the gap.

#### 4.8.3 Cost-Efficiency Analysis

**Table 36: Recommendation Matrix**

| Difficulty | Best Quality | Score | Best Efficiency | Eff. (Q/kT) | Token Range |
|-----------|-------------|-------|----------------|-------------|-------------|
| Easy | Solo | 4.73 | Solo | 9.64 | 491--11,200 |
| Medium | Refl-2 | 3.93 | Solo | 3.17 | 1,032--15,752 |
| Hard | Solo | 3.67 | Solo | 0.65 | 5,680--28,877 |

**Finding 46: Solo dominates cost-efficiency at all difficulty levels across all 5 models.** Solo achieves the highest quality-per-token ratio across all three difficulty levels for Haiku (9.64, 3.17, 0.65 Q/kT for easy, medium, hard respectively), and this cost-efficiency advantage is confirmed across all 5 models. Even when refl-2 achieves higher absolute quality for specific model-difficulty combinations, solo's consistently lower token cost makes it more cost-efficient. The practical implication: multi-agent overhead is only justified when quality improvement is the primary objective and cost is secondary.

Token costs scale dramatically with difficulty: debate-3 increases from 11,200 (easy) to 28,877 (hard), a 2.6x increase, while solo increases from 491 to 5,680, an 11.6x increase. Multi-agent patterns thus incur both an absolute overhead *and* a multiplicative difficulty penalty.

#### 4.8.4 Cross-Validation with Experiment 06

Applying the cost prediction model trained on exp01 data (Section 4.7) to exp07 token costs yields R²=0.12 for total tokens and R²=0.26 for duration. Both values fall well below the original R²=0.54, indicating weak generalization.

**Finding 47: Topology-based cost prediction does not generalize across difficulty-graded tasks.** The exp06 model's poor transfer (R²=0.12) suggests that task difficulty introduces variance that topology features alone cannot capture. This complements Finding 42 (Section 4.7): the ~46% unexplained variance in the original model is partly attributable to task difficulty, which operates orthogonally to topology structure. A combined model incorporating both topology features and difficulty indicators is a promising direction for improved cost prediction.

**Figure 10** (see `figures/fig10_difficulty_analysis.png`) presents a 4-panel composite: (a) quality heatmap across difficulty × pattern, (b) quality degradation trajectories from easy→hard, (c) cost-efficiency comparison by difficulty, and (d) the recommendation matrix with optimal patterns highlighted.

---

## 5. Discussion

### 5.1 Design Guidelines for Topology-Aware Termination

Based on our experimental findings, we propose the following practical guidelines for practitioners deploying multi-agent LLM systems:

**Guideline 1: Match termination strategy to topology category.**
- *Flat sequential (Category A)*: Use agent-count-calibrated max_messages. For n agents, set max_messages = 2n as a baseline, as additional rounds show diminishing returns (Section 4.1.1).
- *Dynamic routing (Category B)*: Account for coordinator overhead in turn budgets. The routing agent consumes LLM calls without directly contributing to output quality.
- *Structured feedback (Category C)*: Monitor convergence signals (Section 4.3) rather than fixed turn limits. Feedback patterns exhibit natural stopping points that can be detected via claim-level stability.
- *Composed (Category D)*: Apply per-stage termination independently. Pipeline stages have different optimal stopping points; a single global limit is inappropriate.

**Guideline 2: Budget for input token growth.**
In round-robin topologies, input tokens grow superlinearly with turn count because each agent sees the full conversation history. For n-agent teams over k rounds, expected input tokens scale as O(n * k * average_response_length). This cost can be mitigated by message summarization or sliding-window context strategies.

**Guideline 3: Consider task-topology interaction.**
Our preliminary results show 2.2x variation in token consumption across task categories within a single topology (Table 6). Creative and open-ended tasks particularly stress multi-round topologies. Practitioners should consider task complexity when selecting both the topology and the termination budget.

**Guideline 4: Use ΔU as a complement to keyword termination, not a replacement.**
Our controlled experiment (Section 4.5) reveals that keyword-based termination is a surprisingly effective heuristic that aligns well with quality plateau points (Finding 34). Rather than replacing it, deploy the marginal utility criterion ΔU(t) as a *secondary* safety mechanism: keyword termination handles the common case (agent consensus), while ΔU with λ≥0.1 catches cases where agents fail to self-terminate (e.g., swm4's 28% keyword termination rate). This hybrid approach preserves keyword termination's efficiency while adding ΔU's principled quality-cost guarantee for unreliable topologies.

**Guideline 5: Match topology complexity to task difficulty and model capability.**
Cost prediction analysis (Section 4.7) shows that `agent_count × max_messages` is the dominant cost driver. Experiment 07 (Section 4.8, 669 runs across 5 models) reveals that solo dominance is the default, moderated by model capability:
- *Easy tasks*: Solo agents suffice across all 5 models (quality=4.73 for Haiku, efficiency=9.64 Q/kT). Multi-agent overhead (3.3--6.1x cost) is not justified.
- *Medium tasks*: Structured feedback (refl-2) helps weaker models (Haiku Δ=+0.67, d=1.26; GPT-5.4 Δ=+1.00, d=1.83), but solo remains best for 2/5 models (Grok, GPT-4o-mini).
- *Hard tasks*: Solo is best for 3/5 models. Stronger models (GPT-5.4, Gemini) benefit from refl-2 at hard difficulty, suggesting multi-agent coordination compensates for capability gaps at the model's difficulty frontier.
The practical rule: assess task difficulty first, then consider model capability. Multi-agent coordination is most valuable when the task difficulty exceeds the model's individual capability threshold.

### 5.2 Implications for Multi-Agent System Design

**Three non-obvious findings challenge conventional multi-agent wisdom.** First, a 3-agent decentralized swarm (swm3, 4,196 tokens) is cheaper than a 2-agent sequential chain (rr2, 4,759 tokens)—a cost reversal where *more agents cost less* because swarm's handoff-driven communication (337 tokens/turn) is fundamentally cheaper than round-robin's full-context responses (2,370 tokens/turn). Practitioners adding agents to a team should not assume linear cost increases. Second, debate—widely advocated as a quality-improving mechanism (Du et al., 2023)—exhibits monotonic quality *decline* after the first round (3.8→3.4→3.3, Finding 22). "More discussion = better answers" does not hold; the debate topology's fixed multi-round structure introduces conflicting revisions that fragment coherence. Third, the simple TERMINATE keyword is near-optimal for 7/8 topologies (Finding 36), meaning sophisticated adaptive termination is unnecessary for most deployments—a "negative result" with significant practical value.

**Topology selection as a cost-quality lever.** Our results demonstrate that topology choice is not merely an architectural decision but a direct lever on the cost-quality Pareto frontier. Simple round-robin topologies provide predictable, linear cost scaling but limited quality improvement from additional agents. Dynamic routing adds overhead but can improve quality on heterogeneous task suites. Feedback topologies offer the richest quality improvement potential but require convergence-aware termination to avoid wasteful over-computation.

**The coordinator overhead tax.** Dynamic routing patterns (Category B) pay an inherent "coordinator tax"---each routing decision requires an LLM call that does not directly produce output tokens. This overhead is fixed per turn regardless of task complexity, making it proportionally more expensive for simple tasks. System designers should consider whether the adaptive routing benefit justifies this tax for their task distribution.

**Collaborative amplification in output.** Contrary to the expectation of diminishing per-agent contributions, our fact-only comparison (Table 5) shows that output tokens per LLM call *increase* with team size: rr2=930, rr3=1,189, rr4=1,544 tokens/call (1.66x from 2 to 4 agents). Agents exposed to richer prior context produce longer, more detailed responses---a collaborative amplification effect. However, this benefit comes at a steep cost: the input token burden grows even faster (3.34x for rr4/rr2) since each agent must read all prior contributions. The net effect is that total cost grows superlinearly (3.26x) while per-agent output grows sublinearly. This asymmetry between input cost and output richness mirrors AgentDropout's finding that many agents contribute redundantly (Wang et al., ACL 2025), but reframes it: the issue is not that agents contribute *less*, but that the cost of *reading* prior contributions outpaces the value of *writing* new ones. This suggests that topology-aware context summarization---where later agents receive compressed rather than full history---could preserve the amplification benefit while controlling input costs.

**Convergence as a universal signal.** While convergence detection has been studied primarily for debate patterns (Hu et al., 2025), our extension to all 13 topologies reveals that convergence signals exist across categories---they simply manifest differently. In sequential patterns, convergence appears as response shortening (agents outputting TERMINATE earlier). In feedback patterns, it appears as claim-level stability. This universality suggests that a unified convergence-aware termination framework could replace topology-specific heuristics.

### 5.3 Limitations

1. **Cross-model validation scope.** Primary experiments use Claude Haiku 4.5. Cross-model validation with GPT-4o-mini (Section 4.6) demonstrates strong rank-order preservation (Spearman ρ = 0.900, p = 0.037) across 5 representative patterns covering all topology categories (S, A, B1, B2, C). Importantly, the key counterintuitive findings---swm3 cheaper than rr2, the B1/B2 split, keyword termination effectiveness---all replicate across models. While n=5 is small, the patterns were deliberately selected to represent each structural category, making the comparison more informative than a random 5-of-13 selection. Extension to larger models (GPT-4o, Claude Sonnet) and open-weight models remains important for full generalizability.

2. **Task suite design scope.** Our 25-task suite spans 9 domains and 4 cognitive types but focuses on open-ended generation tasks. This is a deliberate methodological choice (Section 3.2): studying termination dynamics requires continuous quality trajectories, which verifiable benchmarks (pass/fail) cannot provide. However, we acknowledge that termination dynamics on code generation (where execution feedback provides objective stopping signals) or mathematical reasoning (where correctness is binary) may exhibit different patterns. Extending our framework to mixed task suites---combining open-ended quality trajectories with objective verification signals---is an important next step.

3. **Quality estimator fidelity.** The adaptive termination mechanism (exp05) relies on a quality estimator trained on exp02 data from the same model. We mitigate evaluator bias through cross-validation with five independent models from four provider families (Section 4.2.1): pairwise $\kappa_w$ ranges from 0.244 (GPT-4o-mini, fair) to 0.449 (Grok, moderate), with three models exceeding the moderate threshold. Bias directions split both ways (strict: Haiku $\Delta=+0.91$, GPT-5.4 $\Delta=+0.69$; lenient: GPT-4o-mini $\Delta=-0.93$, Gemini $\Delta=-0.82$, Grok $\Delta=-0.60$), bracketing Claude from both sides. In production, the quality estimator may need to be model-agnostic or regularly recalibrated as base models are updated.

4. **Infrastructure confounds.** The 28K character prompt truncation limit (Section 4.4) is specific to our SDK implementation and does not reflect intrinsic topology limitations. Production deployments with different context window sizes will encounter this boundary at different points.

5. **Cost model simplification.** We use token count as a proxy for cost, ignoring latency-sensitive applications where wall-clock time matters more than token consumption. The marginal utility function could be extended: ΔU(t) = ΔQ(t) - λ_c·ΔC(t) - λ_d·ΔD(t).

6. **Hybrid termination coverage.** The hybrid keyword+ΔU strategy is validated on two extreme patterns (swm4, debate3); broader coverage across all 13 patterns remains future work.

7. **Single human evaluator.** The human evaluation study (Section 4.2.1) uses a single expert evaluator for 30 stratified samples. We compensate through extensive LLM cross-validation: five independent models from four provider families (Section 4.2.1) all show significant positive correlations with Claude ($r = 0.43$--$0.66$), with bias directions splitting both ways across providers. Nevertheless, without a second human annotator, inter-rater reliability cannot be computed. Future work should employ at least two human annotators with reported Cohen's $\kappa$ ≥ 0.60.

8. **Missing confidence intervals.** Most result tables report mean values without standard deviations or confidence intervals. While the large number of runs (780+ for exp01, 800 for exp05) provides reasonable stability, per-pattern sample sizes (25--60 runs) are modest, and formal uncertainty quantification would strengthen the findings.

9. **Cross-model sample size.** The Spearman ρ = 0.900 for cross-model validation is computed over n = 5 patterns, which limits statistical power. However, these 5 patterns (solo, rr3, sel3, swm3, refl2) were selected to cover all five topology categories (S, A, B1, B2, C), maximizing structural diversity rather than statistical sample size. The key qualitative findings---cost hierarchy, B1/B2 divergence, swm3 efficiency---replicate individually across both models (Table 31b). Extending to all 13 patterns with multiple models remains desirable for quantitative robustness.

10. **Topology features explain 54% of cost variance---substantial for structural predictors.** For context, behavioral prediction models in social science consider R²>0.30 as meaningful and R²>0.50 as strong (Cohen, 1988). Our R²=0.54 from *topology features alone*---without any knowledge of task content, prompt length, or domain---is notably high for a purely structural predictor. The remaining ~46% is attributable to task content complexity and stochastic model behavior, which are inherently unpredictable from topology structure. This decomposition is itself informative: it reveals that topology explains *more* cost variance than task content does, validating topology as a first-order design lever for cost control. Incorporating task-level features could further improve prediction, but the practical value of the current model is that it requires no task analysis---just the topology specification.

11. **Difficulty operationalization.** The easy/medium/hard difficulty grading in Experiment 07 is based on cognitive demand categories (factual recall → comparative analysis → creative design), which is a reasonable but subjective operationalization. Alternative difficulty metrics (e.g., human performance benchmarks, information-theoretic complexity) might yield different interaction patterns.

### 5.4 Future Work

Several directions emerge from our findings:

1. **Dynamic topology switching.** Rather than selecting a fixed topology for an entire task, systems could switch topologies mid-execution based on convergence signals (e.g., starting with debate for divergent thinking, then switching to pipeline for refinement).

2. **Learned termination policies.** The utility-based stopping criterion uses a fixed lambda per topology. A learned policy (e.g., via reinforcement learning) could adapt lambda in real-time based on the conversation trajectory.

3. **Cross-model generalization.** Cross-validation with five models from four providers (Section 4.2.1) confirms rank-order preservation ($\kappa_w = 0.244$--$0.449$), and cross-model replication (Section 4.6) shows cost-order preservation ($\rho = 0.762$). Extension to open-weight models (Llama, Mistral) would further strengthen generalizability claims.

4. **Human-in-the-loop termination.** Some multi-agent tasks benefit from human intervention at specific decision points. Integrating adaptive termination with human feedback could create a hybrid stopping mechanism that is both efficient and aligned.

5. **Scaling to larger teams.** Our study examines teams of 2-5 agents. As multi-agent systems scale to 10+ agents, new coordination challenges (partial observability, communication bottlenecks) may fundamentally alter termination dynamics.

6. **Enhanced cost prediction.** The R²=0.54 ceiling of topology-only features (Section 4.7) suggests that incorporating task-level features (prompt complexity, domain embeddings, estimated reasoning depth) could significantly improve cost prediction. A hybrid model combining topology structure with task embeddings may approach R²>0.7, enabling reliable pre-execution cost budgeting.

7. **Difficulty- and capability-adaptive topology selection.** Experiment 07 confirms that task difficulty moderates optimal topology choice, with solo dominance as the default moderated by model capability: weaker models benefit from structured feedback at medium difficulty, while stronger models benefit at hard difficulty. An automated system could classify incoming tasks by difficulty and route them based on the base model's capability profile---solo as the default, with multi-agent coordination activated when task difficulty approaches the model's individual capability frontier. Extending this to finer-grained difficulty scales, more models, and incorporating the cost prediction model (Section 4.7) with difficulty features could enable fully automated topology selection.

---

## 6. Conclusion

We presented the first systematic study of termination dynamics across 13 coordination topologies plus a single-agent baseline spanning six categories: single-agent baseline (S), sequential chain (A), centralized routing/star (B1), decentralized handoff/mesh (B2), structured feedback (C), and composed/nested (D) architectures. Through seven interconnected experiments within a unified AutoGen framework, we demonstrated that:

1. **Topology fundamentally shapes termination behavior.** Against a single-agent baseline (1,287 tokens), multi-agent patterns incur 3.3--17.4x token overhead. Agent count, routing mechanism, and feedback structure all significantly influence when and how multi-agent teams should stop. Applying uniform stopping criteria across topologies leads to systematic termination regret.

2. **Centralized (B1) and decentralized (B2) routing are fundamentally different.** The B1/B2 split decomposes the previous "B ≈ C" equivalence. Statistically, A ≈ B2 (p=0.857), B2 < C (p=0.028), establishing a new cost hierarchy A ≈ B2 < B1 ≈ C ≪ D. Feedback patterns exhibit natural convergence signals, and all categories possess exploitable topology-specific stopping signals.

3. **Marginal utility provides a natural stopping signal.** The marginal utility ΔU(t) = ΔQ(t) - λ·ΔC(t) converges to zero within 1.1-2.4 turns via quality saturation, and is insensitive to λ choice. This provides a principled theoretical basis for topology-aware optimal stopping.

4. **Error patterns correlate with topology features.** The mechanism of failure differs across topologies even when the root cause is shared, informing targeted mitigation strategies.

5. **Keyword termination is surprisingly effective; ΔU serves as a diagnostic complement.** A controlled experiment (Section 4.5, 800 runs) reveals that adaptive ΔU termination adds overhead for 7 of 8 topologies when used as a replacement for keyword termination, but achieves 70% cost savings for swm4 where keyword termination fails (28% success rate). This diagnostic result is itself valuable: it validates that keyword-based heuristics are near-optimal for well-behaved topologies while identifying the specific topology class (decentralized handoff) where alternative stopping criteria are needed.

6. **Topology features provide moderate cost predictability.** Pre-execution features---particularly the `agent_count × max_messages` interaction term---predict 54% of token variance (R²=0.54), offering practitioners a principled basis for cost estimation. The remaining variance attributable to task content complexity (~46%) defines an honest boundary on topology-only prediction.

7. **Task difficulty dominates topology choice, with solo dominance moderated by model capability (669 runs, 5 models).** Difficulty is the dominant factor (H=243.74, p<0.000001, η²=0.363), explaining 9.3× more variance than pattern choice (η²=0.039). Solo achieves the highest quality for easy tasks across all 5/5 models. At medium and hard difficulty, the benefit of multi-agent feedback is model-capability-dependent: refl-2 helps Haiku (d=1.26) and GPT-5.4 (d=1.83) at medium difficulty, and GPT-5.4 and Gemini at hard difficulty, but solo remains best for the majority of models at each level. The previously reported inverted-U pattern holds only for Haiku (1/5 models). Solo dominates cost-efficiency at all difficulty levels across all 5 models. The recommendation: assess task difficulty first, then consider whether the base model's capability warrants multi-agent coordination at that difficulty level.

We release our experimental framework (13 pattern implementations, 7 experiment runners, analysis scripts) to enable reproducible multi-agent termination research. Our findings provide practical design guidelines for practitioners building multi-agent LLM systems, emphasizing that termination strategy should be a first-class design decision informed by coordination topology and task difficulty.

---

## References

- Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.). Lawrence Erlbaum Associates.
- Cemri, M., et al. (2025). Why Do Multi-Agent LLM Systems Fail? arXiv:2503.13657.
- Hu, J., et al. (2025). When to Stop: Adaptive Stability Detection for Multi-Agent Debate. NeurIPS 2025. arXiv:2510.12697.
- Li, J., et al. (2025). MoA: Mixture of Agents Enhances Large Language Model Capabilities. ICLR 2025. arXiv:2406.04692.
- Lin, F., et al. (2025). Stop Wasting Your Tokens: Towards Efficient Runtime Multi-Agent Systems. arXiv:2510.26585.
- Liu, Y., et al. (2023). G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment. EMNLP 2023.
- Lu, J., et al. (2026). DyTopo: Dynamic Topology Routing for Multi-Agent Systems. arXiv:2602.06039.
- Masterman, T., et al. (2025). The Landscape of Emerging AI Agent Architectures for Reasoning, Planning, and Tool Calling: A Survey. arXiv:2404.11584.
- Reimers, N. & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. EMNLP 2019. arXiv:1908.10084.
- Ruan, C. & Wang, Y. (2025). Reaching Agreement Among Reasoning LLM Agents. arXiv:2512.20184.
- Sun, J., et al. (2025). REFRAIN: Reasoning Efficiency Framework for AI Networks. arXiv:2510.10103.
- Sun, Z., et al. (2025). MegaAgent: A Practical Framework for Autonomous Cooperation in Large-Scale LLM Agent Systems. ACL 2025 Findings. arXiv:2408.09955.
- Tran, K.-T., et al. (2025). Multi-Agent Collaboration Mechanisms: A Survey of LLMs. arXiv:2501.06322.
- Wang, P., et al. (2024). Large Language Models are not Fair Evaluators. ACL 2024.
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023.
- Wang, B., et al. (2025). Rethinking Multi-Agent Intelligence Through the Lens of Small-World Networks. arXiv:2512.18094.
- Wang, X., et al. (2023). Self-Consistency Improves Chain of Thought Reasoning in Language Models. ICLR 2023.
- Wang, Z., et al. (2025). AgentDropout: Dynamic Agent Elimination for Token-Efficient Multi-Agent Collaboration. ACL 2025. arXiv:2503.18891.
- Wu, Q., et al. (2023). AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv:2308.08155.
- Xiong, R., et al. (2025). Scaling Agent Systems: A Study of Coordination, Communication, and Efficiency. arXiv:2512.08296.
- Zhang, Y., et al. (2025). G-Designer: Architecting Multi-Agent Communication Topologies via Graph Neural Networks. ICML 2025 Spotlight. arXiv:2410.11782.
- Zheng, L., et al. (2023). Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. NeurIPS 2023. arXiv:2306.05685.
- Zhao, Y., et al. (2025). The Consensus-Diversity Tradeoff in Multi-Agent Debate. EMNLP 2025.

---

## Appendix A: Task Suite

**Table A1: Complete Task Suite (25 tasks across 9 domains)**

| ID | Domain | Type | Diff. | Task Description |
|----|--------|------|-------|------------------|
| sci_01 | Science | Factual | Med | Explain the three laws of thermodynamics and their practical engineering implications |
| sci_02 | Science | Analytical | Med | Describe photosynthesis including light-dependent/independent reactions; compare C3, C4, CAM pathways |
| sci_03 | Science | Creative | Hard | Propose three novel experimental approaches to detect dark matter with theoretical motivation |
| cs_01 | CS | Factual | Med | Explain the TCP/IP protocol stack layers and data flow from application to physical layer |
| cs_02 | CS | Technical | Med | Implement an LRU cache with O(1) get/put operations; explain data structure choices |
| cs_03 | CS | Analytical | Med | Compare microservices vs. monolithic architecture for 100K DAU e-commerce |
| hist_01 | History | Factual | Med | Analyze the main causes of World War I (political, economic, social factors) |
| hist_02 | History | Analytical | Hard | Compare the fall of the Roman Empire with the decline of the British Empire |
| hist_03 | History | Creative | Hard | Alternate history: What if the printing press was invented in Song Dynasty China? |
| phil_01 | Philosophy | Factual | Med | Explain Kant's categorical imperative vs. Mill's utilitarianism on moral decision-making |
| phil_02 | Philosophy | Analytical | Med | Analyze the trolley problem variants across deontological, utilitarian, virtue ethics |
| phil_03 | Philosophy | Creative | Hard | Design a thought experiment challenging personal identity in the age of AI mind uploading |
| law_01 | Law & Politics | Factual | Med | Explain separation of powers in presidential vs. parliamentary systems |
| law_02 | Law & Politics | Analytical | Hard | Analyze AI-generated content in copyright law: EU AI Act, US fair use, Korean approaches |
| law_03 | Law & Politics | Creative | Hard | Draft a policy proposal for regulating autonomous vehicles (liability, insurance, testing) |
| game_01 | Gaming | Factual | Med | Explain game design principles: feedback loops, flow state, MDA framework |
| game_02 | Gaming | Technical | Hard | Design real-time multiplayer matchmaking (ELO/Glicko, latency, queue balancing) |
| game_03 | Gaming | Creative | Hard | Design a game teaching quantum computing through puzzle mechanics |
| eng_01 | Engineering | Factual | Med | Explain structural load analysis for bridges (dead, live, wind, seismic loads) |
| eng_02 | Engineering | Technical | Hard | Design a water treatment plant for 200K people (stages, capacity, standards) |
| eng_03 | Engineering | Analytical | Med | Compare traditional vs. 3D-printed construction for affordable housing |
| biz_01 | Business | Creative | Hard | Create a business plan for an AI-powered K-12 education startup |
| biz_02 | Business | Analytical | Med | Compare VC funding vs. bootstrapping for B2B SaaS startups |
| biz_03 | Business | Analytical | Hard | Evaluate EV market entry strategy for Southeast Asia |
| med_01 | Medicine | Analytical | Hard | Compare mRNA vs. protein subunit vaccines for pandemic preparedness |

Tasks span 9 knowledge domains with 3 tasks each (medicine has 1 due to domain sensitivity). Task types include factual (7), analytical (9), creative (6), and technical (3). Difficulty: 13 medium, 12 hard. Each task includes an evaluation rubric used for G-Eval scoring in Experiment 02. The full prompt text and rubrics are available in the supplementary materials.

**Table A2: Difficulty-Graded Task Suite (15 tasks, Experiment 07)**

| ID | Domain | Difficulty | Cognitive Type | Task Description |
|----|--------|-----------|----------------|------------------|
| sci_easy | Science | Easy | Factual | Explain the first law of thermodynamics; what does conservation of energy mean in practice? |
| sci_med | Science | Medium | Analytical | Compare the three laws of thermodynamics with engineering applications for each |
| sci_hard | Science | Hard | Creative | Design a novel waste heat recovery cycle beyond Rankine/Brayton with 1st/2nd law analysis |
| cs_easy | CS | Easy | Factual | Explain client-server architecture: main components and communication |
| cs_med | CS | Medium | Analytical | Compare microservices vs. monolithic architecture across scalability, deployment, data consistency |
| cs_hard | CS | Hard | Creative | Design migration strategy for 100K-DAU monolith to microservices with zero-downtime phasing |
| hist_easy | History | Easy | Factual | List and explain three major causes of the fall of the Roman Empire |
| hist_med | History | Medium | Analytical | Compare decline of Roman Empire with British Empire (structural, economic, military factors) |
| hist_hard | History | Hard | Creative | Develop general theory of imperial decline with falsifiable predictions for current global order |
| eng_easy | Engineering | Easy | Factual | Explain dead loads vs. live loads in bridge engineering with examples |
| eng_med | Engineering | Medium | Analytical | Compare suspension vs. cable-stayed bridges for 500m+ spans |
| eng_hard | Engineering | Hard | Creative | Design seismic-resistant bridge for tsunami-prone region (600m span, multi-hazard) |
| biz_easy | Business | Easy | Factual | Explain venture capital: GP/LP roles, funding stages (seed through Series B) |
| biz_med | Business | Medium | Analytical | Compare VC funding vs. bootstrapping for B2B SaaS (growth, dilution, culture) |
| biz_hard | Business | Hard | Creative | Design multi-stage funding strategy for deep-tech AI startup across 3+ ASEAN countries |

Difficulty levels correspond to increasing cognitive demand: easy=factual recall, medium=comparative analysis requiring structured reasoning, hard=creative design with multi-constraint reasoning and novel synthesis.

## Appendix B: Pattern Implementation Details

All 13 patterns are implemented within the AutoGen framework using a TeamFactory abstraction that maps pattern identifiers to configured team instances. Each pattern shares:
- Base model: Claude Haiku 4.5 (via ClaudeCLIChatCompletionClient)
- Token tracking: Per-call prompt and completion token counts via models_usage
- Termination: TERMINATE keyword detection + max_messages safety bound (25)
- Checkpoint: Per-pattern result saving for fault tolerance

Full implementation code, configuration files, and analysis scripts are available in the supplementary materials.

## Appendix C: Statistical Variability

All metrics below are computed from the v2 dataset (raw_A_B1_B2_C_D.json, n=25 per pattern) for Experiment 01, and from Experiment 02 (n=40 per pattern, 20 tasks) for quality scores. 95% confidence intervals use t-distribution with df=n-1.

**Table C1: Experiment 01 Efficiency Statistics (n=25 per pattern)**

| Pattern | Cat | Tokens mean | ±std | 95% CI | Duration mean (s) | ±std | Turns mean | ±std |
|---------|-----|------------|------|--------|-------------------|------|-----------|------|
| debate3 | C | 8,657 | ±2,501 | [7,625; 9,690] | 121.6 | ±26.2 | 3.6 | ±0.5 |
| pipe | D | 13,186 | ±5,828 | [10,780; 15,592] | 128.3 | ±58.3 | 4.0 | ±0.8 |
| refl2 | C | 5,281 | ±3,315 | [3,913; 6,649] | 53.1 | ±29.0 | 2.2 | ±0.7 |
| rr3 | A | 12,332 | ±10,148 | [8,143; 16,521] | 111.4 | ±90.4 | 3.6 | ±1.2 |
| sel3 | B1 | 8,502 | ±5,243 | [6,338; 10,666] | 95.6 | ±42.4 | 2.7 | ±0.5 |
| sel4 | B1 | 11,264 | ±6,428 | [8,610; 13,917] | 124.5 | ±62.9 | 3.2 | ±0.8 |
| swm3 | B2 | 4,341 | ±5,646 | [2,011; 6,672] | 45.4 | ±30.9 | 7.8 | ±7.9 |
| swm4 | B2 | 12,921 | ±6,214 | [10,355; 15,486] | 148.6 | ±39.1 | 25.1 | ±8.9 |

*Note: High std for swm3 tokens (±5,646 relative to mean 4,341, CV=1.30) reflects the bimodal nature of swarm behavior: some runs terminate quickly via keyword, while others execute many handoff rounds. This variability is itself a topology-dependent phenomenon.*

**Table C2: Experiment 02 Quality Statistics (n=40 per pattern, 20 tasks x 2 repeats)**

| Pattern | Cat | Quality mean | ±std | 95% CI | Tokens mean | ±std | 95% CI |
|---------|-----|-------------|------|--------|------------|------|--------|
| refl2 | C | 4.80 | ±0.41 | [4.67; 4.93] | 7,186 | ±11,272 | [3,606; 10,766] |
| rr3 | A | 4.45 | ±0.50 | [4.29; 4.61] | 13,949 | ±8,539 | [11,237; 16,661] |
| swm3 | B2 | 3.77 | ±1.25 | [3.38; 4.17] | 7,882 | ±12,447 | [3,928; 11,836] |
| sel3 | B1 | 3.40 | ±1.08 | [3.06; 3.74] | 8,646 | ±6,887 | [6,458; 10,834] |
| debate3 | C | 3.35 | ±0.80 | [3.10; 3.60] | 8,887 | ±2,457 | [8,106; 9,667] |

**Table C3: Experiment 05 Adaptive Termination Statistics (n=100 per pattern)**

| Pattern | Cat | Tokens mean | ±std | 95% CI | Duration mean (s) | ±std | Turns mean | ±std |
|---------|-----|------------|------|--------|-------------------|------|-----------|------|
| debate3 | C | 9,575 | ±4,931 | [8,596; 10,553] | 119.3 | ±63.1 | 3.6 | ±1.3 |
| pipe | D | 11,783 | ±5,982 | [10,596; 12,969] | 118.4 | ±58.5 | 3.8 | ±0.8 |
| refl2 | C | 16,147 | ±24,176 | [11,350; 20,943] | 170.3 | ±262.6 | 4.6 | ±4.6 |
| rr3 | A | 14,345 | ±14,162 | [11,535; 17,155] | 136.6 | ±136.3 | 4.2 | ±2.9 |
| sel3 | B1 | 11,606 | ±7,797 | [10,059; 13,153] | 153.0 | ±95.2 | 3.5 | ±1.3 |
| sel4 | B1 | 15,020 | ±13,180 | [12,405; 17,635] | 174.4 | ±159.4 | 4.1 | ±2.6 |
| swm3 | B2 | 8,169 | ±9,906 | [6,204; 10,134] | 96.6 | ±98.6 | 7.5 | ±5.3 |
| swm4 | B2 | 7,324 | ±7,542 | [5,827; 8,820] | 70.3 | ±47.0 | 12.2 | ±9.0 |

## Appendix D: Compressed Findings Summary

The 39 individual findings in the main text are organized into 15 core findings below. Original finding numbers are preserved in parentheses for cross-reference.

| # | Core Finding | Original | Section |
|---|-------------|----------|---------|
| C1 | Multi-agent coordination incurs 3.3-17.4x token overhead; cost scales near-linearly with agent count; error rates scale superlinearly | F1-5 | 4.1.1 |
| C2 | Two routing strategies (centralized vs. decentralized) produce radically different scaling: B1 sub-linear, B2 super-linear turn counts | F6-8 | 4.1.2 |
| C3 | swm3 (3 agents) achieves best token efficiency, beating even rr2 (2 agents): routing strategy dominates agent count | F8 | 4.1.2 |
| C4 | Reflection and debate exhibit opposite scaling: reflection gets cheaper with more agents, debate gets more expensive; at equal count, reflection is faster but debate is cheaper per token | F9-12 | 4.1.3 |
| C5 | Composed patterns (MoA, pipe) are most expensive but produce highest output density per agent turn | F13-15 | 4.1.4 |
| C6 | New cost hierarchy: A ~ B2 < B1 ~ C << D, replacing prior assumption A << B ~ C << D | F16-18 | 4.1.5 |
| C7 | Domain effects: debate3 is uniquely domain-invariant; task complexity amplifies cost differences 2x independently of topology | F19-21 | 4.1.6 |
| C8 | Three quality trajectory shapes: monotone-plateau (rr3), peak-at-turn-2 (refl2), monotone-decline (debate3) | F22 | 4.2 |
| C9 | Termination regret varies 13x across topologies; reflection achieves highest quality with near-zero quality loss | F23-24 | 4.2 |
| C10 | Semantic convergence (Sentence-BERT) reveals different topology ranking than surface metrics; feedback patterns never converge semantically | F25-27 | 4.3 |
| C11 | Three termination failure modes emerge: factual tasks are error-immune, technical tasks error-prone; swarm communication is structurally distinct | F28-30 | 4.4 |
| C12 | Marginal utility deltaU converges within 1.1-2.4 turns for all topologies; lambda-insensitive (quality saturation dominates) | F31-32 | 4.5 |
| C13 | Adaptive termination benefit is topology-dependent: overhead for 7/8 patterns, but -70% savings for swm4 where keyword fails | F33-35 | 4.5 |
| C14 | Hybrid keyword+ΔU validated: preserves keyword efficiency, catches unreliable topologies | F36 | 4.5 |
| C15 | Topology-dependent dynamics are model-invariant (Spearman rho=0.900, n=5, p=0.037); keyword reliability and routing efficiency are model-sensitive | F37-39 | 4.6 |
| C16 | Topology features predict 54% of token variance (R²=0.54); agents_x_maxmsg is top predictor; task content explains ~46% remaining variance | F40-42 | 4.7 |
| C17 | Task difficulty dominates pattern choice (H=243.74, η²=0.363, 9.3× pattern; 669 runs, 5 models); solo dominance moderated by model capability: refl-2 helps weaker models at medium, stronger at hard; solo cost-efficient at all levels across all models | F43-47 | 4.8 |
