![](_page_0_Picture_2.jpeg)

# **WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution**

**Liyan Tang**<sup>1</sup> **, Cyrus Rashtchian**<sup>1</sup> **, Chun-Sung Ferng**<sup>1</sup> **, Andrew Tomkins**<sup>1</sup> **, Da-Cheng Juan**<sup>1</sup> **and Tu Vu**1,2 <sup>1</sup>Google Research, <sup>2</sup>Virginia Tech

*Agent skills* **package specialized knowledge and workflows into reusable resources that extend AI agent capabilities. Recent work automatically discovers such skills from agent experience, which enables agents to progressively adapt through interaction. However, the insights that guide skill development typically remain scattered across optimization histories, limiting their systematic reuse across iterations. We introduce WikiSkill, a framework that co-evolves agent skills with a** *persistent* **knowledge base (wiki). At a high level, WikiSkill separates raw execution experience, accumulated knowledge, and executable skills, while continuously consolidating experience into the wiki, which subsequent skill updates can build on. Across diverse benchmarks and models, WikiSkill consistently outperforms** *state-of-the-art* **skill-evolution methods and improves over no-skill baselines in most model-benchmark settings. We find that skill evolution complements model scaling: larger models generally benefit more from evolved skills, while smaller models with skills can outperform substantially larger models without them. We also find that evolved skills transfer effectively across models and model families, and skills evolved by other models can outperform self-evolved skills. Finally, our ablation studies confirm that persistent knowledge accumulation in the wiki is critical for effective skill evolution. These results demonstrate the benefits of systematically accumulating and refining agent experience for developing reusable and transferable skills.**

![](_page_0_Figure_6.jpeg)

Figure 1 | **WikiSkill consistently improves over both the no-skill baseline and existing skillevolution methods.** Interestingly, its advantage becomes more pronounced for stronger models. We report average accuracy across the evaluated benchmarks for each model using no skills or skills evolved by EvoSkill, SkillOpt, and WikiSkill (see Table [1](#page-7-0) for details).

# **1. Introduction**

General-purpose AI agents are increasingly capable of performing complex tasks across domains [\(Jackson et al.,](#page-14-0) [2025;](#page-14-0) [Merrill et al.,](#page-15-0) [2026;](#page-15-0) [Patwardhan et al.,](#page-16-0) [2026;](#page-16-0) [Phan et al.,](#page-16-1) [2026\)](#page-16-1). However, reliably accomplishing real-world tasks often requires domain-specific expertise (e.g., procedural knowledge and workflows). *Agent skills* [\(Chen et al.,](#page-14-1) [2026a;](#page-14-1) [Li et al.,](#page-15-1) [2026;](#page-15-1) [Liu et al.,](#page-15-2) [2026;](#page-15-2) [Zhang](#page-17-0) [et al.,](#page-17-0) [2025\)](#page-17-0) provide a lightweight, open format for capturing such expertise without updating model parameters. At its core, a skill packages instructions, scripts, and other resources into a reusable filesystem-based module (i.e., an organized directory) [\(Anthropic,](#page-14-2) [2026;](#page-14-2) [Li et al.,](#page-15-1) [2026;](#page-15-1) [Xia et al.,](#page-16-2) [2026b;](#page-16-2) [Zhang et al.,](#page-17-0) [2025\)](#page-17-0). This design makes specialized knowledge consistent, auditable, and reusable across skill-compatible agents. It also supports *progressive disclosure* [\(Jiang et al.,](#page-14-3) [2026\)](#page-14-3), where agents only load relevant content at any given time, which saves context space. More broadly, skills provide a natural mechanism for accumulating knowledge independently of model parameters.

Developing effective skills, however, remains challenging. Most agent skills are manually authored, which requires anticipating the procedural knowledge and workflows that an agent will need [\(Li et al.,](#page-15-1) [2026;](#page-15-1) [Liang et al.,](#page-15-3) [2026;](#page-15-3) [Xu and Yan,](#page-16-3) [2026\)](#page-16-3). This challenge motivates recent work that iteratively develops agent skills by executing agents on training tasks, analyzing successful and failed trajectories, and refining skills based on the resulting experience [\(Agrawal et al.,](#page-14-4) [2026;](#page-14-4) [Alzubi et al.,](#page-14-5) [2026;](#page-14-5) [Ni](#page-15-4) [et al.,](#page-15-4) [2026;](#page-15-4) [Ouyang et al.,](#page-15-5) [2026;](#page-15-5) [Yang et al.,](#page-16-4) [2026;](#page-16-4) [Yuksekgonul et al.,](#page-17-1) [2025\)](#page-17-1).

A key design question is how to preserve and organize what an agent learns throughout skill evolution. Prior work addresses this question in different ways. EvoSkill [\(Alzubi et al.,](#page-14-5) [2026\)](#page-14-5) maintains a cumulative history of prior proposals and their evaluation outcomes; Trace2Skill [\(Ni et al.,](#page-15-4) [2026\)](#page-15-4) extracts and consolidates lessons across execution trajectories into skill updates; and SkillOpt [\(Yang](#page-16-4) [et al.,](#page-16-4) [2026\)](#page-16-4) uses rejected-edit feedback and epoch-wise meta guidance. However, these methods do not maintain what has been learned as a separate, evolving knowledge representation. Inspired by [Karpathy](#page-14-6) [\(2026\)](#page-14-6)'s perspective on **LLM Wiki**, which advocates compiling experience into persistent, compounding knowledge, we ask: *Can agent experience be similarly compiled into persistent knowledge to support long-term skill evolution?* We introduce **WikiSkill**, which adds a structured knowledge layer between raw experience and executable procedures (i.e., skills). This layer allows skill development to build on increasingly well-supported and integrated knowledge across iterations, rather than on knowledge scattered across skill-evolution artifacts.

WikiSkill organizes the agent workspace into three layers: a *Raw Layer* that stores immutable execution traces, a *Wiki Layer* that maintains structured knowledge, and a *Skill Layer* that contains evolving procedural knowledge (Figure [2\)](#page-3-0). Each iteration involves four components: an *Inference Agent* that executes rollouts using the current skills, a *Wiki Maintainer* that consolidates traces into the wiki, a *Skill Proposer* that uses the wiki and traces to propose skill updates, and a *Gating and Rollback mechanism* that retains updates that improve validation performance. While skill updates can be rolled back, the wiki persists so that future updates can build on accumulated knowledge. At a high level, these components form a continual loop in which experience is consolidated into persistent knowledge that supports skill evolution.

We evaluate WikiSkill across *five* benchmarks spanning mathematical reasoning (LiveMathematicanBench [\(He et al.,](#page-14-7) [2026\)](#page-14-7)), web search (SealQA [\(Pham et al.,](#page-16-5) [2026\)](#page-16-5)), spreadsheet manipulation (SpreadSheetBench [\(Ma et al.,](#page-15-6) [2024\)](#page-15-6)), long-context document question answering (OfficeQA [\(Singhvi](#page-16-6) [et al.,](#page-16-6) [2025\)](#page-16-6)), and interactive embodied tasks (ALFWorld [\(Shridhar et al.,](#page-16-7) [2021\)](#page-16-7)), using *five* models from the Qwen [\(Qwen Team,](#page-16-8) [2026a,](#page-16-8)[b\)](#page-16-9), Gemma [\(Gemma Team,](#page-14-8) [2026\)](#page-14-8), and Gemini [\(Google](#page-14-9) [DeepMind,](#page-14-9) [2026\)](#page-14-9) families. We find that WikiSkill outperforms existing skill-evolution methods and improves over no skills in most settings. Interestingly, skill evolution complements model scaling. Within the Qwen family, WikiSkill improves average performance by 12.3%, 17.5%, and 23.9% for 4B, 9B, and 27B models, respectively, with gains increasing with model scale. At the same time, evolved skills can compensate for substantial model scale: Qwen-3.5-9B with WikiSkill outperforms Qwen-3.6-27B without skills (47.4% vs. 39.4%). We further find that evolved skills transfer effectively across model families and can outperform self-evolved skills. On ALFWorld, for example, Qwen-3.5-9B reaches 70.2% with a Qwen-3.6-27B-evolved skill, compared with 63.4% using its own skill. These results suggest that skill discovery and skill execution are distinct capabilities. Finally, our analysis shows that the persistent wiki is critical to these gains, supporting our hypothesis that accumulating and refining knowledge across iterations improves skill evolution.

In summary, our main contributions are:

- We introduce WikiSkill, a framework that co-evolves agent skills with a persistent knowledge base that continually organizes and refines knowledge from agent experience.
- We demonstrate across five benchmarks and five models that WikiSkill consistently outperforms existing skill-evolution methods, with ablations confirming the importance of persistent knowledge accumulation.
- We systematically study how evolved skills interact with model capability, showing that skill evolution complements model scaling and that evolved skills can transfer effectively across models, sometimes outperforming self-evolved skills.

Taken together, we hope that our work will spur more fundamental research on how agents can accumulate, organize, and reuse knowledge from experience.

# 2. Problem Setup

We formalize the task of iterative skill evolution for LLM agents. Let  $\mathcal{D} = \{(x_i, y_i)\}_{i=1}^N$  be a dataset of tasks, where  $x_i$  denotes a task instance and  $y_i$  denotes its ground-truth answer. We partition  $\mathcal{D}$  into three disjoint splits: training tasks  $\mathcal{D}_{\text{train}}$ , validation tasks  $\mathcal{D}_{\text{val}}$ , and testing tasks  $\mathcal{D}_{\text{test}}$ .

An agent  $\pi$  is an LLM-based system equipped with a set of tools  $\mathcal{U}$  (e.g., a bash shell, search APIs, or file readers) and an active skill set  $S = \{s_1, s_2, \ldots, s_M\}$ . A skill is a modular, filesystem-based directory that packages domain-specific procedural knowledge into instructions, scripts, and other resources (Chen et al., 2026a; Li et al., 2026; Liu et al., 2026; Zhang et al., 2025). Specifically, each skill contains a SKILL.md file with frontmatter metadata (a unique name and concise description) alongside full procedural instructions and applicability conditions. The skill set S is initialized to empty ( $\emptyset$ ) and developed for each dataset through the evolution process.

When executing a task  $x_i$ , the agent receives the task context  $x_i$  and access to the available skills S. The agent interacts with the environment over multiple steps using its tools and skills to generate an execution trajectory  $\tau_i \sim \pi(x_i; S)$ . The trajectory  $\tau_i = (o_1, a_1, o_2, a_2, \dots, o_T, a_T)$  consists of observations  $o_t$  and actions  $a_t$  (which may include calls to tools in  $\mathcal{U}$ ). The final action  $a_T$  emits a predicted answer  $\hat{y}_i$ . The correctness of the prediction is evaluated by a domain-specific scoring function  $f(\hat{y}_i, y_i) \in [0, 1]$ . For any task split  $\mathcal{D}_{\text{split}} \subset \mathcal{D}$ , rolling out the agent  $\pi(\cdot; S)$  across all task instances in  $\mathcal{D}_{\text{split}}$  yields a corresponding set of execution trajectories  $\mathcal{T}_{\text{split}} = \{\tau_i \sim \pi(x_i; S)\}_{(x_i, y_i) \in \mathcal{D}_{\text{split}}}$ . The performance on a task split  $\mathcal{R}(\mathcal{T}_{\text{split}})$  is the average score across all task instances  $(x_i, y_i) \in \mathcal{D}_{\text{split}}$ .

In WikiSkill, the system state at iteration k is represented by the tuple  $(S_k, W_k)$ , where  $S_k = \{s_1, \ldots, s_M\}$  denotes the active procedural skill set and  $W_k$  denotes the persistent knowledge base (Wiki). While candidate skill updates are subject to validation gating and rollback upon score degradation, the knowledge base  $W_k$  persists and compounds across iterations. Starting from  $(S_0, W_0) = S_k$ 

<span id="page-3-0"></span>![](_page_3_Figure_1.jpeg)

Figure 2 | **Overview of the WikiSkill framework.** The agent workspace is structured into three layers: immutable execution traces (Raw Layer), a persistent knowledge base that compounds across iterations (Wiki Layer), and active procedural instructions (Skills Layer). In each evolutionary loop, the Inference Agent runs rollouts (injecting active skills but restricting Wiki access), the Wiki Maintainer consolidates traces into the Wiki, and the Skill Proposer (with the ReAct mechanism) suggests updates while the Wiki is retained across all iterations.

(∅, ∅), WikiSkill co-evolves the joint state (, ) across iterations ∈ {1, . . . , }, leveraging training rollouts Ttrain,, pattern consolidation, and validation gating based on Tval, to maximize final test performance R (Ttest) on unseen tasks Dtest.

# **3. Methodology**

We present WikiSkill, a framework that co-evolves agent skills and a persistent knowledge base (wiki). Built around a three-layer knowledge architecture ([§3.1\)](#page-3-1), WikiSkill executes an orchestrated evolutionary loop in which the agent runs rollouts, a Wiki Maintainer consolidates traces and updates the wiki, a Skill Proposer proposes skill updates, and a gating mechanism filters changes ([§3.2\)](#page-4-0).

#### <span id="page-3-1"></span>**3.1. Three-Layer Knowledge Architecture**

The WikiSkill workspace consists of three distinct layers, as shown in Figure [2](#page-3-0) and described below.

**Raw Layer (raw/)** This layer stores the raw execution traces ∈ Ttrain, collected from training examples in each iteration. These traces capture the agent's complete step-by-step interactions, including reasoning, tool calls, tool-call outputs, and final answers. In our setup, the Wiki Maintainer and Skill Proposer agents can access these raw traces to analyze agent behavior. To preserve the raw history, this layer is immutable.

**Wiki Layer (wiki/)** This layer compiles raw traces into structured, compounding knowledge and is maintained throughout skill evolution. It contains a pattern directory (patterns/) populated with individual markdown files that document specific failure modes or successful strategies, along with actionable workarounds. Crucially, this layer provides long-term historical awareness across optimization iterations through an evolution log (logs.md, updated by the Wiki Maintainer) and a skill impact tracker (skill-impact.md, updated programmatically by the outer-loop harness after validation gating). These records allow the Wiki Maintainer and Skill Proposer to (1) observe the complete skill acceptance history so that rejected interventions are not proposed again, (2) track what was proposed in prior iterations and whether those proposals succeeded, and (3) identify which errors recur across iterations. The wiki is not reset between iterations, but rather accumulates and compiles knowledge continuously throughout the evolution process.

**Skills Layer (skills/)** This layer contains the active set of evolved skills , which encode the procedural knowledge that the Inference Agent can read. Each skill directory in WikiSkill contains two files: SKILL.md, which contains the full content of the skill; and PURPOSE.md, which maps the skill back to the motivating Wiki patterns that inspired its creation or modification. A detailed example of interactions between the Skill Layer and the Wiki Layer is illustrated in Figure [3](#page-11-0) and explained in the case study in Section [5.3.](#page-11-1)

### <span id="page-4-0"></span>**3.2. Evolutionary Agents and Wiki Orchestration**

The WikiSkill loop consists of four components. In each iteration, the **Inference Agent** ([§3.2.1\)](#page-4-1) executes tasks using the active skills in skills/, producing immutable execution traces in raw/. During the training rollouts, the Inference Agent is restricted from accessing the Wiki Layer, as our ablation study ([§5.1\)](#page-9-0) shows that allowing wiki access during training negatively affects skill development. Next, the **Wiki Maintainer** ([§3.2.2\)](#page-4-2) analyzes these raw traces alongside the existing wiki/ layer to diagnose failures and extract successful strategies, updating the persistent pattern catalog and evolution logs. The **Skill Proposer** ([§3.2.3\)](#page-5-0) then reviews the updated wiki and reads execution traces from the latest iteration to generate or modify candidate skills in skills/. Finally, a **Gating and Rollback** mechanism ([§3.2.4\)](#page-5-1) evaluates the candidate skills on a validation split, accepting successful modifications or rolling back the skill set if the changes degrade performance. The entire evolution algorithm is described in Algorithm [1](#page-18-0) in Appendix [A.](#page-18-1)

#### <span id="page-4-1"></span>*3.2.1. Skill Provisioning for the Inference Agent*

At iteration , the Inference Agent is conditioned on the active skill set −<sup>1</sup> and executes a multi-turn trajectory using environment tools U:

$$\tau_i \sim \pi(x_i; S_{k-1}) \tag{1}$$

In WikiSkill, the full content of active skills −<sup>1</sup> is injected directly into the Inference Agent's system prompt. Following prior work [\(Ni et al.,](#page-15-4) [2026;](#page-15-4) [Yang et al.,](#page-16-4) [2026\)](#page-16-4), this full-injection setting ensures that procedural instructions are immediately available during task execution, thereby eliminating skill triggering or retrieval failures as confounding variables in our study.

# <span id="page-4-2"></span>*3.2.2. Wiki Maintainer: Pattern Consolidation*

At iteration , after obtaining rollout traces Ttrain, on the training split Dtrain, we sample a subset of successful and failing execution traces Tsample, ⊂ Ttrain, (see Appendix [C](#page-20-0) for sampling budget and stratification criteria) to avoid context window limitations. The Wiki Maintainer agent MWM consolidates these observations into the persistent wiki −1, producing the intermediate wiki state

$$W'_{k}$$
:
$$W'_{k} \leftarrow \mathcal{M}_{\text{WM}}(W_{k-1}, \mathcal{T}_{\text{sample},k})$$
(2)

The Wiki Maintainer agent receives the full wiki context  $W_{k-1}$  alongside sampled traces  $\mathcal{T}_{\text{sample},k}$ . It performs root cause analysis on the failing tasks, and extracts successful strategies from the passing tasks. In each iteration, the Wiki Maintainer can create new pattern pages under wiki/patterns/ and update existing pattern pages with new evidence or refined solutions. Updates to pattern pages are applied using incremental, patch-based editing (e.g., appending, replacing, or inserting text spans). Whenever patterns are modified, the Wiki Maintainer revises the index.md catalog to reflect the current state and appends a summary of the iteration's findings to the evolution log logs.md. There is no hard limit on the number of patterns created or updated per iteration; the Wiki Maintainer decides what updates are warranted based on the traces and the current wiki state.

### <span id="page-5-0"></span>3.2.3. Wiki-Informed Skill Proposer

The Proposer  $\mathcal{M}_P$  is an LLM-based agent responsible for skill discovery and refinement. At iteration k, the proposer operates in a multi-turn ReAct style (Yao et al., 2023). To avoid context window exhaustion when analyzing long execution histories, the proposer is not given a fixed set of presampled traces; instead, it is initially provided with the wiki index  $I(W_k')$ , the historical skill impact tracker (skill-impact.md), and a concise summary of all training task outcomes (pass/fail status, predictions and ground-truth answers). Operating as an autonomous agent, it actively reasons and uses environment tools (read\_file) to select and inspect specific pattern pages and raw execution traces  $\tau_i \in \mathcal{T}_{\text{train},k}$  on demand to diagnose root causes before synthesizing a proposal  $P_k$ :

$$P_k \leftarrow \mathcal{M}_{P}(W'_k, S_{k-1}, \mathcal{T}_{\text{train},k}) \tag{3}$$

In each iteration, the Skill Proposer produces an atomic proposal  $P_k$  that targets a single skill, either creating a new skill or applying an incremental, patch-based edit to the targeted existing skill.

#### <span id="page-5-1"></span>3.2.4. Gating and Rollback

Once a proposal  $P_k$  is generated, it is applied to the workspace to yield a candidate skill set  $S'_k = \text{Apply}(S_{k-1}, P_k)$ . The system evaluates  $S'_k$  on the validation split  $\mathcal{D}_{\text{val}}$ , obtaining validation traces  $\mathcal{T}_{\text{val},k}$  and score  $\mathcal{R}(\mathcal{T}_{\text{val},k})$ . The acceptance decision is governed by:

$$S_k \leftarrow \begin{cases} S_k' & \text{if } \mathcal{R}(\mathcal{T}_{\text{val},k}) > \mathcal{R}_{\text{best}} \\ S_{k-1} & \text{otherwise} \end{cases}$$
 (4)

If accepted, the candidate skills are preserved as the new active skill set  $S_k$ , and the benchmark performance threshold  $\mathcal{R}_{\text{best}}$  is updated to  $\mathcal{R}(\mathcal{T}_{\text{val},k})$ . Prior to the evolution loop,  $\mathcal{R}_{\text{best}}$  is initialized to the baseline validation score  $\mathcal{R}(\mathcal{T}_{\text{val},0})$  obtained by evaluating the empty skill set  $S_0$  on  $\mathcal{D}_{\text{val}}$ . If the validation score reaches the maximum ( $\mathcal{R}_{\text{best}} = 1.0$ ) at any point during evolution, the evolution loop terminates early. If rejected, the system discards the candidate skill modifications and reverts the skill set to the most recent successful configuration  $S_{k-1}$ . Notably, the wiki  $W_k$  is never rolled back regardless of the acceptance decision; accumulated patterns and logs persist across all iterations to ensure long-term knowledge retention. Following each validation evaluation, the outer-loop orchestration harness programmatically appends an entry to wiki/skill-impact.md via  $W_k \leftarrow \text{Update}(W'_k, P_k, \mathcal{R}(\mathcal{T}_{\text{val},k}), a_k)$ , recording the proposal metadata, target skill name, unified diff of the modification, validation score  $\mathcal{R}(\mathcal{T}_{\text{val},k})$ , and final acceptance outcome  $a_k \in \{\text{Accepted}, \text{Rejected}\}$ . This completes the wiki state transition  $W_{k-1} \rightarrow W_k$  for iteration k, providing an objective, ground-truth audit trail of past interventions that the Skill Proposer can consult in subsequent iterations to avoid repeating failed modifications.

# **4. Experiments and Results**

### **4.1. Experimental Setup**

**Datasets** We evaluate across five benchmarks spanning diverse domains: mathematical reasoning (**LiveMathematicianBench (LiveMath)** [\(He et al.,](#page-14-7) [2026\)](#page-14-7)), web search (**SealQA** [\(Pham et al.,](#page-16-5) [2026\)](#page-16-5)), spreadsheet manipulation (**SpreadsheetBench (SpreadSheet)** [\(Ma et al.,](#page-15-6) [2024\)](#page-15-6)), long-context document question answering **OfficeQA** [\(Singhvi et al.,](#page-16-6) [2025\)](#page-16-6)), and interactive embodied tasks (**ALFWorld** [\(Shridhar et al.,](#page-16-7) [2021\)](#page-16-7)). Dataset details and statistics are provided in Appendix [B.](#page-18-2)

**Baselines** We compare WikiSkill against three representative skill-evolution baselines, including Trace2Skill [\(Ni et al.,](#page-15-4) [2026\)](#page-15-4), EvoSkill [\(Alzubi et al.,](#page-14-5) [2026\)](#page-14-5), and SkillOpt [\(Yang et al.,](#page-16-4) [2026\)](#page-16-4), all of which share the same general loop of rolling out an agent, analyzing execution traces, proposing skill modifications, and gating changes via validation. We also evaluate each model without skills as a no-skill baseline. A detailed description and an analysis of the complexity of optimizer API calls across these frameworks are provided in Appendix [D.](#page-20-1) We focus our comparison on dedicated skill-evolution frameworks rather than general automatic prompt optimizers (e.g., GEPA [\(Agrawal et al.,](#page-14-4) [2026\)](#page-14-4)), following prior work that shows specialized skill-evolution pipelines consistently outperform general prompt optimization methods [\(Yang et al.,](#page-16-4) [2026\)](#page-16-4).

**Models** We experiment with both closed and open-weight models to evaluate WikiSkill and the baselines. For closed models, we use **Gemini-3.5-Flash** [\(Google DeepMind,](#page-14-9) [2026\)](#page-14-9). For openweight models, we evaluate **Qwen-3.5-4B/9B-Instruct** [\(Qwen Team,](#page-16-8) [2026a\)](#page-16-8), **Qwen-3.6-27B** [\(Qwen](#page-16-9) [Team,](#page-16-9) [2026b\)](#page-16-9), and **Gemma-4-31B-It** [\(Gemma Team,](#page-14-8) [2026\)](#page-14-8), which we deploy using the vLLM framework [\(Kwon et al.,](#page-14-10) [2023\)](#page-14-10).

#### **4.2. Main Results**

We evaluate WikiSkill across models and tasks and study whether evolved skills transfer across models. Table [1](#page-7-0) presents the main skill-evolution results across models and tasks, including how the benefits of skill evolution vary with model scale, while Table [2](#page-9-1) presents the cross-model skill transfer results. We analyze these results in detail below.

To account for variability, we repeat the full evolution process across three independent runs for each method, and all reported scores represent the average test performance across the three resulting evolved skill sets. Statistical significance of performance differences is evaluated using paired bootstrap testing at < 0.05 (Appendix [C\)](#page-20-0). Note that for Gemini-3.5-Flash on ALFWorld, all evolution methods yield the same performance (85.9%) as the no-skill baseline because Gemini-3.5- Flash achieves a 100% score on the validation split (Dval) before skill evolution. This also explains why Gemini-3.5-Flash is marked with '−' as a skill source on ALFWorld in the cross-model transfer evaluation (Table [2\)](#page-9-1).

#### *4.2.1. Skill Evolution Across Models and Tasks*

**WikiSkill yields consistent improvements across models and datasets** As shown in Table [1,](#page-7-0) WikiSkill achieves the highest average performance across all five models. Compared with the strongest competing skill-evolution method for each model, WikiSkill improves average performance by 3.3, 5.1, 10.0, 5.8, and 12.0 points for Qwen-3.5-4B, Qwen-3.5-9B, Qwen-3.6-27B, Gemma-4-31B, and Gemini-3.5-Flash, respectively. These improvements are consistent across settings: WikiSkill improves over the no-skill baseline in most model-dataset pairs and matches or exceeds the strongest competing

<span id="page-7-0"></span>

| Model            | Method      | LiveMath | SealQA | SpreadSheet | OfficeQA | ALFWorld | Avg. |
|------------------|-------------|----------|--------|-------------|----------|----------|------|
|                  | No skill    | 29.1     | 32.5   | 14.6        | 30.2     | 24.4     | 26.2 |
|                  | Trace2Skill | 31.5     | 37.6   | 17.5        | 31.0     | 42.8     | 32.1 |
| Qwen-3.5-4B      | EvoSkill    | 41.7     | 37.3   | 18.6        | 29.5     | 41.5     | 33.7 |
|                  | SkillOpt    | 48.7     | 33.3   | 14.0        | 34.5     | 45.3     | 35.2 |
|                  | WikiSkill   | 49.7     | 39.4   | 21.1        | 28.5     | 53.7     | 38.5 |
|                  | No skill    | 28.2     | 26.3   | 24.3        | 35.9     | 34.7     | 29.9 |
|                  | Trace2Skill | 33.1     | 36.9   | 26.5        | 38.4     | 48.8     | 36.7 |
| Qwen-3.5-9B      | EvoSkill    | 58.1     | 34.5   | 35.4        | 34.9     | 48.5     | 42.3 |
|                  | SkillOpt    | 48.7     | 29.4   | 29.0        | 38.0     | 55.7     | 40.2 |
|                  | WikiSkill   | 56.3     | 43.1   | 33.6        | 40.5     | 63.4     | 47.4 |
|                  | No skill    | 33.9     | 27.5   | 40.8        | 42.1     | 52.8     | 39.4 |
|                  | Trace2Skill | 36.3     | 37.3   | 53.3        | 54.3     | 55.5     | 47.3 |
| Qwen-3.6-27B     | EvoSkill    | 57.3     | 32.9   | 59.5        | 52.5     | 64.2     | 53.3 |
|                  | SkillOpt    | 51.9     | 34.5   | 53.2        | 54.8     | 59.2     | 50.7 |
|                  | WikiSkill   | 61.9     | 41.6   | 81.7        | 53.7     | 77.6     | 63.3 |
|                  | No skill    | 33.9     | 30.6   | 48.3        | 43.3     | 50.4     | 41.3 |
|                  | Trace2Skill | 32.3     | 37.7   | 58.5        | 43.2     | 57.2     | 45.8 |
| Gemma-4-31B      | EvoSkill    | 29.8     | 38.4   | 56.4        | 39.9     | 52.6     | 43.4 |
|                  | SkillOpt    | 40.1     | 36.1   | 63.1        | 44.4     | 61.9     | 49.1 |
|                  | WikiSkill   | 56.7     | 41.2   | 68.0        | 44.2     | 64.4     | 54.9 |
| Gemini-3.5-Flash | No skill    | 33.0     | 29.4   | 50.5        | 48.6     | 85.9     | 49.5 |
|                  | Trace2Skill | 41.9     | 44.3   | 56.0        | 50.0     | 85.9     | 55.6 |
|                  | EvoSkill    | 44.6     | 43.6   | 55.4        | 51.2     | 85.9     | 56.1 |
|                  | SkillOpt    | 49.7     | 28.2   | 66.1        | 49.8     | 85.9     | 55.9 |
|                  | WikiSkill   | 72.6     | 44.7   | 76.6        | 60.7     | 85.9     | 68.1 |

Table 1 | **Method comparison across inference models and test sets**. Each horizontal block evaluates a specific inference model without skills (No skill) and with skills developed by different skill-evolution methods. To ensure a fair comparison, *all skill-evolution methods start with an empty skill set, and evolved skills are injected into the Inference Agent's prompt at inference time*. All reported scores are the average test performance across three independent runs of the full evolution process. Our method (**WikiSkill**) is highlighted. Bold indicates the best performance for each dataset; multiple bold results indicate methods that are not significantly different from the best under a paired bootstrap test with 1,000 iterations ( < 0.05).

method across all models in the average performance across 5 datasets. The improvements also span diverse domains and can be substantial. For example, WikiSkill improves Gemini-3.5-Flash from 33.0% to 72.6% on LiveMath and from 50.5% to 76.6% on SpreadSheet, while improving Qwen-3.6-27B from 52.8% to 77.6% on ALFWorld. In contrast, existing skill-evolution methods are less consistent. For example, EvoSkill improves Qwen-9B substantially on LiveMath (28.2% → 58.1%) but degrades Gemma-4-31B on the same benchmark (33.9 % → 29.8%), while SkillOpt degrades Gemini-3.5-Flash on SealQA (29.4 % → 28.2%). These results show that WikiSkill produces both stronger and more reliable improvements across settings.

**The benefits of skill evolution increase with model capability and complement model scaling** Within the Qwen family, the average improvement from WikiSkill increases with model scale, from +12.3 points for Qwen-3.5-4B to +17.5 points for Qwen-3.5-9B and +23.9 points for Qwen-3.6-27B. This trend is particularly pronounced on SpreadSheet, where WikiSkill improves the three models by +6.5, +9.3, and +40.9 points, respectively, showing that the benefits of skill evolution can increase

substantially with model scale. At the same time, evolved skills can compensate for substantial differences in model scale: Qwen-3.5-9B with WikiSkill reaches 47.4% average accuracy, outperforming Qwen-3.6-27B without skills at 39.4%, while Qwen-3.5-4B with WikiSkill reaches 38.5%. Our results suggest that model capability and evolved procedural knowledge provide complementary sources of performance: stronger models can derive greater value from skill evolution by developing and executing more effective skills, while effective skills can allow smaller models to outperform substantially larger models that do not use skills.

**The benefits of skill evolution also vary substantially across datasets** Our results suggest that some datasets are more amenable to skill evolution than others. For Qwen-3.6-27B, WikiSkill improves performance by 11.6 points on OfficeQA and 14.1 points on SealQA, compared with 24.8 points on ALFWorld, 28.0 points on LiveMath, and 40.9 points on SpreadSheet. Similar differences appear across other models. LiveMath consistently benefits from skill evolution, with gains ranging from 20.6 to 39.6 points across all five models, while ALFWorld yields gains of 14.0 to 29.3 points across the four models for which WikiSkill evolves skills (excluding Gemini-3.5-Flash due to early stopping). In contrast, OfficeQA presents unique challenges due to its long-context document-retrieval requirements. Larger models effectively leverage evolved search workflows to navigate lengthy documents (e.g., +11.6 points for Qwen-3.6-27B and +12.1 points for Gemini-3.5-Flash), whereas Qwen-3.5-4B struggles to execute these multi-step search workflows across long contexts and reverts to its default reading behavior, resulting in slight degradation.

### *4.2.2. Cross-Model Skill Transfer with WikiSkill*

**Evolved skills transfer effectively across models, and transferred skills can outperform self-evolved skills** Table [2](#page-9-1) evaluates how skills evolved by WikiSkill transfer across inference models when developed using different source models. Transferred skills frequently outperform both the no-skill baseline and self-evolved skills. For example, Qwen-3.6-27B skills improve Qwen-3.5-9B to 50.5% on SpreadSheet, compared with 24.3% without skills and 33.6% with self-evolved skills, and improve Gemma-4-31B to 73.7% on LiveMath, compared with 33.9% and 56.7%, respectively. Notably, effective transfer also occurs from smaller to larger models: Qwen-3.5-4B skills improve Gemma-4-31B to 73.1% on LiveMath and 66.9% on ALFWorld. Our results indicate that stronger source models do not necessarily produce better skills and that procedural knowledge developed by one model's experience can transfer across model scales and families.

**The transferability of evolved skills depends on whether they capture general procedures or model-specific workarounds** Our results in Table [2](#page-9-1) suggest that WikiSkill can produce both general procedural knowledge that transfers across models and model-specific strategies that can cause negative transfer. LiveMath skills transfer particularly well across models: Qwen-3.5-4B and Qwen-3.6-27B skills improve Gemini-3.5-Flash from 33.0% to 67.5% and 73.9%, respectively. In contrast, SpreadSheet exhibits strong source-target interactions. Qwen-3.5-4B skills reduce Gemini-3.5-Flash performance from 50.5% to 18.1%, while Qwen-3.6-27B skills improve it to 63.4%. Our error analysis identifies two factors behind this negative transfer. First, Qwen-3.5-4B skills encode low-level workarounds, such as single-line Python commands and string-conversion rules, which help the smaller model avoid execution failures but constrain stronger models such as Gemini-3.5-Flash from using comprehensive end-to-end scripts. Second, fragmented diagnostic procedures introduce redundant tool calls that can exhaust Gemini-3.5-Flash's interaction budget before task completion.

**The utility of transferred skills also depends on the inference model's ability to execute them** We now turn toward how different inference models use skills developed by the same source model.

<span id="page-9-1"></span>

| Model            | Skill Source     | LiveMath | SealQA | SpreadSheet | OfficeQA | ALFWorld |
|------------------|------------------|----------|--------|-------------|----------|----------|
|                  | None             | 29.1     | 32.5   | 14.6        | 30.2     | 24.4     |
|                  | Qwen-3.5-4B      | 49.7     | 39.4   | 21.1        | 28.5     | 53.7     |
| Qwen-3.5-4B      | Qwen-3.6-27B     | 59.7     | 38.8   | 33.0        | 25.4     | 57.0     |
|                  | Gemini-3.5-Flash | 62.6     | 37.3   | 23.0        | 32.2     | -        |
|                  | None             | 28.2     | 26.3   | 24.3        | 35.9     | 34.7     |
|                  | Qwen-3.5-4B      | 61.0     | 40.4   | 25.0        | 40.3     | 69.2     |
| Qwen-3.5-9B      | Qwen-3.5-9B      | 56.3     | 43.1   | 33.6        | 40.5     | 63.4     |
|                  | Qwen-3.6-27B     | 59.1     | 40.4   | 50.5        | 39.9     | 70.2     |
|                  | Gemini-3.5-Flash | 53.0     | 39.6   | 48.8        | 40.5     | -        |
|                  | None             | 33.9     | 27.5   | 40.8        | 42.1     | 52.8     |
|                  | Qwen-3.5-4B      | 62.6     | 41.6   | 40.6        | 52.9     | 72.1     |
| Qwen-3.6-27B     | Qwen-3.6-27B     | 61.9     | 41.6   | 81.7        | 53.7     | 77.6     |
|                  | Gemini-3.5-Flash | 65.1     | 51.0   | 76.0        | 52.5     | -        |
|                  | None             | 33.9     | 30.6   | 48.3        | 43.3     | 50.4     |
|                  | Qwen-3.5-4B      | 73.1     | 38.8   | 37.1        | 42.1     | 66.9     |
| Gemma-4-31B      | Qwen-3.6-27B     | 73.7     | 37.7   | 72.0        | 44.2     | 66.9     |
|                  | Gemma-4-31B      | 56.7     | 41.2   | 68.0        | 44.2     | 64.4     |
|                  | Gemini-3.5-Flash | 61.8     | 37.7   | 68.8        | 43.4     | -        |
| Gemini-3.5-Flash | None             | 33.0     | 29.4   | 50.5        | 48.6     | 85.9     |
|                  | Qwen-3.5-4B      | 67.5     | 40.0   | 18.1        | 48.5     | 87.3     |
|                  | Qwen-3.6-27B     | 73.9     | 43.5   | 63.4        | 47.7     | 86.8     |
|                  | Gemini-3.5-Flash | 72.6     | 44.7   | 76.6        | 60.7     | -        |

Table 2 | **Cross-model skill transfer results.** We evaluate inference models using no skills (None) and skills evolved by WikiSkill with Qwen-3.5-4B, Qwen-3.6-27B, and Gemini-3.5-Flash as source models. Skills are injected into the Inference Agent's system prompt at inference time. Highlighted rows indicate self-evolved skills, where the inference model and skill source are the same. The highest performance per benchmark within each model block is bolded. '−' indicates that the source model reached 100% validation performance before skill evolution, so no skill was evolved.

Within the Qwen family, stronger models can derive greater value from the same procedural knowledge. For example, Qwen-3.6-27B SpreadSheet skills improve Qwen-3.5-4B, Qwen-3.5-9B, and Qwen-3.6- 27B over their no-skill baselines by 18.4%, 26.2%, and 40.9%, respectively. OfficeQA provides a case where a model develops skills that are more useful to another model than to itself: Qwen-3.5-4B skills decrease its own performance from 30.2% to 28.5%, but improve Qwen-3.6-27B from 42.1% to 52.9%. Our trajectory analysis suggests that in long-context settings, smaller models can become distracted by lengthy document contexts and fail to follow detailed multi-step search instructions, instead reverting to their default document-reading behavior. Stronger models, in contrast, more reliably execute the structured navigation procedures specified by the skill across long contexts. Taken together, these results distinguish two capabilities that self-evolution normally conflates: discovering useful procedural knowledge from experience and effectively executing that knowledge at inference time.

# **5. Analysis and Discussion**

### <span id="page-9-0"></span>**5.1. Role of Persistent Knowledge in Skill Evolution**

To understand where persistent knowledge contributes to skill evolution, we ablate wiki access for the two components that can use it during evolution (Table [3\)](#page-10-0). Specifically, using Gemini-3.5-Flash, we

<span id="page-10-0"></span>

| WikiSkill Components                                            |   | Benchmarks |        |             |          |      |  |
|-----------------------------------------------------------------|---|------------|--------|-------------|----------|------|--|
| Inference Agent<br>Skill Proposer<br>Wiki Access<br>Wiki Access |   | LiveMath   | SealQA | SpreadSheet | OfficeQA | Avg. |  |
| No skill                                                        |   | 33.0       | 29.4   | 50.5        | 48.6     | 40.4 |  |
| ✓                                                               | p | 43.8       | 42.0   | 44.4        | 51.0     | 45.3 |  |
| p                                                               | p | 51.3       | 38.4   | 49.9        | 55.2     | 48.7 |  |
| ✓                                                               | ✓ | 64.8       | 42.8   | 80.2        | 55.6     | 60.9 |  |
| p                                                               | ✓ | 72.6       | 44.7   | 76.6        | 60.7     | 63.7 |  |

Table 3 | **Ablation study on WikiSkill using Gemini-3.5-Flash.** We evaluate performance across benchmarks under four configurations that vary whether the Inference Agent and Skill Proposer have wiki access during skill evolution. When the Skill Proposer has no Wiki access, we also remove the Wiki Maintainer, eliminating persistent knowledge accumulation across iterations. The bottom row represents our default WikiSkill configuration.

independently vary wiki access for the Inference Agent during training rollouts and the Skill Proposer during skill development, which results in four configurations. When the Skill Proposer has no wiki access, we also remove the Wiki Maintainer, eliminating persistent knowledge accumulation across iterations. Our default WikiSkill configuration gives wiki access to the Skill Proposer but not the Inference Agent.

**Persistent wiki knowledge dramatically improves skill evolution** As shown in Table 3, when wiki access for the Inference Agent is disabled, providing the Skill Proposer with access to the persistent wiki increases average benchmark performance from 48.7% to 63.7% (+15.0%), with substantial gains on LiveMath (51.3% to 72.6%) and SpreadsheetBench (49.9% to 76.6%). Without persistent knowledge accumulated across iterations, the Skill Proposer struggles to resolve intricate failure modes.

**Wiki access for the Inference Agent during evolution degrades final skill quality** When the Skill Proposer has access to the persistent wiki, providing the Inference Agent with wiki access during training rollouts reduces average benchmark performance from 63.7% to 60.9%, with a substantial drop on LiveMath from 72.6% to 64.8%. We hypothesize that when the Inference Agent has access to both skills and the wiki during training rollouts, some task-solving knowledge may be obtained directly from the wiki rather than the skills, which can make the resulting trajectories less informative for skill development.

### **5.2. Qualitative Analysis: Skill and Wiki Dynamics**

To better understand how WikiSkill evolves knowledge and skills across models and datasets, we analyze the wiki patterns accumulated and skills produced during evolution (Table [4\)](#page-12-0) and when successful skill updates are accepted across iterations (Appendix Table [5\)](#page-19-0).

**WikiSkill continuously accumulates wiki patterns while producing concise skills** Table [4](#page-12-0) summarizes the creation and editing of skills and wiki patterns across models and benchmarks, along with their average lengths. Across models, Qwen models produce longer procedural skills (118.9-128.6 lines), whereas Gemma-4-31B and Gemini-3.5-Flash produce more compact skills (45.1 and 81.2 lines, respectively). Wiki pattern accumulation also varies across models, with 6.3-8.9 patterns created

<span id="page-11-0"></span>![](_page_11_Figure_1.jpeg)

Figure 3 | Case study of Wiki-guided skill evolution on ALFWorld (Qwen-3.6-27B). The persistent Wiki Layer compiles cross-iteration patterns, an audit trail of past proposal diffs and acceptance decisions, and chronological history. Informed by the rejection of the skill proposal at Iteration 0, the proposer synthesizes the accepted skill update at Iteration 1, and later refines it with new pattern evidence. File contents are simplified for clarity.

and 7.0–18.4 edits on average. Across benchmarks, SpreadSheet produces the longest skills (142.5 lines) and most wiki patterns (9.8), whereas LiveMath produces the shortest skills (84.6 lines) and fewest wiki patterns (4.4). Overall, these results show that both skill structure and wiki accumulation vary across models and datasets.

<span id="page-11-1"></span>**Skill refinement continues throughout the evolution process** Appendix Table [5](#page-19-0) groups accepted skill updates into early (Iterations 0–1), middle (Iterations 2–4), and late (Iterations 5–7) stages. Across models, the initial stage accounts for 39%-52% of accepted updates, with substantial fractions continuing into the middle and late stages. A similar pattern holds across benchmarks, where 39%-58% of accepted updates occur during the initial stage. Continued refinement is particularly pronounced on SealQA, where 33% of accepted updates occur in the middle stage and 28% in the late stage. Combined with the ablation in Section [5.1,](#page-9-0) these results suggest that persistent knowledge accumulation supports continued skill refinement across iterations. The Wiki Layer preserves recurring errors, rejected proposals, and evolution history, which provide the Skill Proposer with accumulated context for subsequent updates. Below, we present a case study that illustrates how this accumulated knowledge informs skill evolution.

<span id="page-12-0"></span>

| Category                         |                                                            | Wiki Patterns |                |        |      |                |  |
|----------------------------------|------------------------------------------------------------|---------------|----------------|--------|------|----------------|--|
| ditegory                         | Create Edit<br>(Proposed / Accepted) (Proposed / Accepted) |               | Avg.<br>Length | Create | Edit | Avg.<br>Length |  |
| By Model (All-Dat                | aset Average)                                              |               |                |        |      |                |  |
| Qwen-3.5-4B                      | 3.1 / 1.6                                                  | 4.9 / 1.3     | 126.2          | 8.8    | 18.4 | 48.2           |  |
| Qwen-3.5-9B                      | 4.6 / 1.4                                                  | 3.4 / 0.7     | 128.6          | 7.3    | 10.9 | 26.6           |  |
| Qwen-3.6-27B                     | 4.4 / 1.5                                                  | 3.6 / 0.8     | 118.9          | 6.5    | 17.9 | 47.7           |  |
| Gemma-4-31B                      | 4.8 / 1.3                                                  | 3.2 / 0.8     | 45.1           | 6.3    | 13.7 | 23.7           |  |
| Gemini-3.5-Flash                 | 2.3 / 1.2                                                  | 5.7 / 1.1     | 81.2           | 8.9    | 7.0  | 18.1           |  |
| By Benchmark (All-Model Average) |                                                            |               |                |        |      |                |  |
| LiveMath                         | 1.9 / 1.1                                                  | 6.1 / 1.9     | 84.6           | 4.4    | 12.1 | 31.7           |  |
| SealQA                           | 4.9 / 0.9                                                  | 3.1 / 0.4     | 98.5           | 9.4    | 15.9 | 26.9           |  |
| SpreadSheet                      | 4.5 / 1.4                                                  | 3.5 / 1.1     | 142.5          | 9.8    | 11.3 | 38.5           |  |
| OfficeQA                         | 4.7 / 1.8                                                  | 3.3 / 0.3     | 102.9          | 8.3    | 14.9 | 31.4           |  |
| ALFWorld                         | 3.9 / 1.6                                                  | 4.1 / 0.8     | 93.5           | 5.8    | 14.3 | 40.6           |  |

Table 4 | Statistics of evolved skills and wiki patterns across inference models (top) and benchmarks (bottom). For skills, we report the numbers of proposed/accepted creations and edits, along with average length in markdown lines. For wiki patterns, we report the numbers of creations and edits, along with average length in markdown lines. All wiki pattern creations and edits are retained.

#### 5.3. Case Study: Anatomy of Wiki-Guided Skill Evolution

To illustrate how the Wiki and Skill Layers interact during evolution, we trace a concrete example from Qwen-3.6-27B on ALFWorld, as shown in Figure 3 (simplified for presentation).

At Iteration 0, the Wiki Maintainer identifies a basic looping behavior (take-examine-mov e-loop.md), while the Skill Proposer proposes goal-directed-action, which fails to improve performance on the validation set and is rejected. Crucially, *skill-impact.md* preserves the proposal diff and rejection outcome, allowing subsequent skill updates to account for this failed attempt.

Informed by this audit trail, the Skill Proposer creates break-repetition-loop at Iteration 1 with a concrete action rule (*Never Return an Item to Its Origin Location*), which is accepted. As new loop variants emerge across rollouts (multi-operation-loop.md), the Wiki Maintainer accumulates new evidence in the persistent wiki. Guided by these accumulated wiki patterns and newly stored trajectories (not shown in the figure), the Skill Proposer further refines the skill at Iteration 4 with a new rule (*Each Operation Type ONCE Per Item*). This example illustrates how persistent knowledge from prior iterations informs subsequent skill refinement.

## 6. Related Work

Experience-Driven Agent Skill Evolution Agent skills encode reusable procedural knowledge that allows LLM agents to leverage past experience for future tasks (Anthropic, 2026; Li et al., 2026; Wang et al., 2026; Xia et al., 2026b; Xu and Yan, 2026; Zhang et al., 2025; Zhou et al., 2026). Recent frameworks enable agents to self-improve by discovering and refining procedural knowledge from past execution traces (Agrawal et al., 2026; Lu et al., 2026; Ouyang et al., 2026; Xia et al., 2026a; Yuksekgonul et al., 2025). Methods like EvoSkill (Alzubi et al., 2026), Trace2Skill (Ni et al., 2026), and SkillOpt (Yang et al., 2026) use specialized agent pipelines to analyze task rollouts and update modular skill documents (Zhang et al., 2026a). However, these methods do not maintain what has been learned as a separate, evolving knowledge representation. WikiSkill introduces a persistent Wiki Layer that consolidates experience into structured knowledge across iterations, allowing subsequent

skill updates to build systematically on accumulated knowledge.

**Skill-Augmented Agents and Agent Self-Improvement** Beyond constructing high-quality skills, skill-augmented agents must effectively select and utilize relevant skills during execution [\(Chen](#page-14-1) [et al.,](#page-14-1) [2026a;](#page-14-1) [Liu et al.,](#page-15-2) [2026\)](#page-15-2). As the number of reusable skills grows, recent work has explored skill retrieval to select relevant skills from a library for each task [\(Cho et al.,](#page-14-11) [2026;](#page-14-11) [Shi et al.,](#page-16-12) [2026;](#page-16-12) [Su et al.,](#page-16-13) [2026;](#page-16-13) [Ye et al.,](#page-17-5) [2026;](#page-17-5) [Zheng et al.,](#page-17-6) [2026\)](#page-17-6). WikiSkill instead focuses on skill quality itself, separately from skill retrieval. Another line of work optimizes the broader agent harness, including prompts, context, tools, memory, and workflows [\(Chen et al.,](#page-14-12) [2026b;](#page-14-12) [Lee et al.,](#page-15-8) [2026;](#page-15-8) [Lin et al.,](#page-15-9) [2026;](#page-15-9) [Lou et al.,](#page-15-10) [2026;](#page-15-10) [Zhang et al.,](#page-17-7) [2026b\)](#page-17-7). These methods improve the agent system by analyzing execution traces and environment feedback to search for better agent configurations. This direction is complementary to WikiSkill, which focuses specifically on evolving reusable procedural skills while holding the broader agent harness fixed.

# **7. Conclusion**

We presented WikiSkill, a framework that co-evolves agent skills with a persistent, compounding knowledge base (wiki). By structuring the agent workspace into three distinct layers, WikiSkill enables skill development to build on increasingly well-supported and integrated knowledge across iterations. An orchestrated loop consolidates experience into the wiki, proposes skill refinements from accumulated knowledge, and gates changes based on validation performance. Empirically, WikiSkill consistently outperforms existing skill-evolution methods across five benchmarks and five inference models and improves over no-skill baselines in most model-dataset pairs. Beyond these overall gains, skill evolution complements model scaling: larger models generally benefit more from evolved skills, while smaller models with skills can outperform substantially larger models without them. At the same time, evolved skills transfer effectively across models and model families and can outperform self-evolved skills. Finally, our ablations confirm that persistent knowledge accumulation is critical for effective skill evolution.

# **Limitations**

WikiSkill has several limitations that motivate future work. First, to isolate skill quality and avoid confounding effects from skill retrieval, our study follows prior work by directly injecting active skills into the agent prompt. This setup does not evaluate skill retrieval or triggering, which becomes important as the number of available skills grows. Second, our validation gating requires each accepted proposal to improve the validation score, which excludes neutral proposals that preserve immediate performance but could enable gains in subsequent iterations. We adopt this strict criterion following prior skill-evolution frameworks [\(Alzubi et al.,](#page-14-5) [2026;](#page-14-5) [Yang et al.,](#page-16-4) [2026\)](#page-16-4) to ensure a fair comparison. Exploring more flexible acceptance criteria is an important direction for future work. Third, the Wiki Layer continuously accumulates pattern pages, evolution logs, and proposal diffs across iterations, but WikiSkill currently lacks an automated mechanism to prune the wiki. Such pruning may become necessary as knowledge accumulates over longer evolution runs. Finally, while our benchmark suite includes long-context document reasoning (OfficeQA) and multi-step tool interactions, it does not cover very long-horizon tasks that span hundreds of environment actions or multiple hours. Developing online skill adaptation methods that refine procedural knowledge within a single long execution rollout remains an important direction for future work.

# **AI Disclosure**

Large language models and coding agents are used to aid with and polish writing and generate some tables and plots.

# **References**

- <span id="page-14-4"></span>L. A. Agrawal, S. Tan, D. Soylu, N. Ziems, R. Khare, K. Opsahl-Ong, A. Singhvi, H. Shandilya, M. J. Ryan, M. Jiang, C. Potts, K. Sen, A. Dimakis, I. Stoica, D. Klein, M. Zaharia, and O. Khattab. GEPA: Reflective prompt evolution can outperform reinforcement learning. In *The Fourteenth International Conference on Learning Representations*, 2026. URL <https://openreview.net/forum?id=RQm2KQTM5r>.
- <span id="page-14-5"></span>S. Alzubi, N. Provenzano, J. Bingham, W. Chen, and T. Vu. Evoskill: Automated skill discovery for multi-agent systems. *arXiv preprint arXiv:2603.02766*, 2026. URL [https://arxiv.org/abs/26](https://arxiv.org/abs/2603.02766) [03.02766](https://arxiv.org/abs/2603.02766).
- <span id="page-14-2"></span>Anthropic. A complete guide to building skills for claude. [https://claude.com/blog/comple](https://claude.com/blog/complete-guide-to-building-skills-for-claude) [te-guide-to-building-skills-for-claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude), January 2026.
- <span id="page-14-1"></span>S. Chen, J. Gai, R. Zhou, J. Zhang, T. Zhu, J. Li, K. Wang, Z. Wang, Z. Chen, K. Kaleb, et al. Skillcraft: Can llm agents learn to use tools skillfully? *arXiv preprint arXiv:2603.00718*, 2026a. URL <https://arxiv.org/abs/2603.00718>.
- <span id="page-14-12"></span>T. Chen, S. Lu, K. Zhao, W. Meng, H. Teng, T. Li, C. Li, X. Liu, J. Liang, Z. Zhang, et al. Harnessx: A composable, adaptive, and evolvable agent harness foundry. *arXiv preprint arXiv:2606.14249*, 2026b. URL <https://arxiv.org/abs/2606.14249>.
- <span id="page-14-11"></span>H. Cho, R. Kang, and Y. Kim. Skillret: A large-scale benchmark for skill retrieval in llm agents. *arXiv preprint arXiv:2605.05726*, 2026. URL <https://arxiv.org/abs/2605.05726>.
- <span id="page-14-8"></span>Gemma Team. Gemma 4 technical report. *arXiv preprint arXiv:2607.02770*, 2026. URL [https:](https://arxiv.org/abs/2607.02770) [//arxiv.org/abs/2607.02770](https://arxiv.org/abs/2607.02770).
- <span id="page-14-9"></span>Google DeepMind. Gemini 3.5 flash. [https://deepmind.google/models/model-cards/gem](https://deepmind.google/models/model-cards/gemini-3-5-flash/) [ini-3-5-flash/](https://deepmind.google/models/model-cards/gemini-3-5-flash/), May 2026.
- <span id="page-14-7"></span>L. He, Q. Yu, H. Dong, B. Liao, X. Xu, M. Goldblum, J. Bian, and N. Mesgarani. Livemathematicianbench: A live benchmark for mathematician-level reasoning with proof sketches. *arXiv preprint arXiv:2604.01754*, 2026. URL <https://arxiv.org/abs/2604.01754>.
- <span id="page-14-0"></span>D. Jackson, W. Keating, G. Cameron, and M. Hill-Smith. Aa-omniscience: Evaluating cross-domain knowledge reliability in large language models. *arXiv preprint arXiv:2511.13029*, 2025. URL <https://arxiv.org/abs/2511.13029>.
- <span id="page-14-3"></span>Y. Jiang, D. Li, H. Deng, B. Ma, X. Wang, Q. Wang, and G. Yu. Sok: Agentic skills–beyond tool use in llm agents. *arXiv preprint arXiv:2602.20867*, 2026. URL <https://arxiv.org/abs/2602.20867>.
- <span id="page-14-6"></span>A. Karpathy. LLM Wiki. GitHub Gist, 2026. URL [https://gist.github.com/karpathy/442a6](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) [bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).
- <span id="page-14-10"></span>W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. Gonzalez, H. Zhang, and I. Stoica. Efficient memory management for large language model serving with pagedattention. In *Proceedings of the 29th Symposium on Operating Systems Principles*, SOSP '23, page 611–626, New York, NY, USA, 2023. Association for Computing Machinery. ISBN 9798400702297. doi: 10.1145/3600006.3613165. URL <https://doi.org/10.1145/3600006.3613165>.

- <span id="page-15-8"></span>Y. Lee, R. Nair, Q. Zhang, K. Lee, O. Khattab, and C. Finn. Meta-harness: End-to-end optimization of model harnesses. *arXiv preprint arXiv:2603.28052*, 2026. URL [https://arxiv.org/abs/2603](https://arxiv.org/abs/2603.28052) [.28052](https://arxiv.org/abs/2603.28052).
- <span id="page-15-1"></span>X. Li, Y. Liu, W. Chen, B. You, Z. Di, Y. He, S. Zheng, K. W. Choe, J. Sun, S. Wang, et al. Skillsbench: Benchmarking how well agent skills work across diverse tasks. *arXiv preprint arXiv:2602.12670*, 2026. URL <https://arxiv.org/abs/2602.12670>.
- <span id="page-15-3"></span>Y. Liang, R. Zhong, H. Xu, C. Jiang, Y. Zhong, R. Fang, J.-C. Gu, S. Deng, Y. Yao, M. Wang, et al. Skillnet: Create, evaluate, and connect ai skills. *arXiv preprint arXiv:2603.04448*, 2026. URL <https://arxiv.org/abs/2603.04448>.
- <span id="page-15-9"></span>J. Lin, S. Liu, C. Pan, L. Lin, S. Dou, Z. Xi, X. Huang, H. Yan, Z. Han, T. Gui, et al. Agentic harness engineering: Observability-driven automatic evolution of coding-agent harnesses. *arXiv preprint arXiv:2604.25850*, 2026. URL <https://arxiv.org/abs/2604.25850>.
- <span id="page-15-2"></span>Y. Liu, J. Ji, L. An, T. Jaakkola, Y. Zhang, and S. Chang. How well do agentic skills work in the wild: Benchmarking llm skill usage in realistic settings. *arXiv preprint arXiv:2604.04323*, 2026. URL <https://arxiv.org/abs/2604.04323>.
- <span id="page-15-10"></span>X. Lou, M. Lázaro-Gredilla, A. Dedieu, C. Wendelken, W. Lehrach, and K. P. Murphy. Autoharness: improving llm agents by automatically synthesizing a code harness. *arXiv preprint arXiv:2603.03329*, 2026. URL <https://arxiv.org/abs/2603.03329>.
- <span id="page-15-7"></span>Z. Lu, Z. Yao, J. Wu, C. Han, Q. Gu, X. Cai, W. Lu, J. Xiao, Y. Zhuang, and Y. Shen. Skill0: In-context agentic reinforcement learning for skill internalization. *arXiv preprint arXiv:2604.02268*, 2026. URL <https://arxiv.org/abs/2604.02268>.
- <span id="page-15-6"></span>Z. Ma, B. Zhang, J. Zhang, J. Yu, X. Zhang, X. Zhang, S. Luo, X. Wang, and J. Tang. Spreadsheetbench: Towards challenging real world spreadsheet manipulation. In *The Thirty-eight Conference on Neural Information Processing Systems Datasets and Benchmarks Track*, 2024. URL [https://openreview](https://openreview.net/forum?id=KYxzmRLF6i) [.net/forum?id=KYxzmRLF6i](https://openreview.net/forum?id=KYxzmRLF6i).
- <span id="page-15-0"></span>M. A. Merrill, A. G. Shaw, N. Carlini, B. Li, H. Raj, I. Bercovich, L. Shi, J. Y. Shin, T. Walshe, E. K. Buchanan, J. Shen, G. Ye, H. Lin, J. Poulos, M. Wang, M. Nezhurina, D. Lu, O. M. Mastromichalakis, Z. Xu, Z. Chen, Y. Liu, R. Zhang, L. L. Chen, A. Kashyap, J.-L. Uslu, J. Li, J. Wu, M. Yan, S. Bian, V. Sharma, K. Sun, S. Dillmann, A. Anand, A. Lanpouthakoun, B. Koopah, C. Hu, E. K. Guha, G. H. S. Dreiman, J. Zhu, K. Krauth, L. Zhong, N. Muennighoff, R. K. Amanfu, S. Tan, S. Pimpalgaonkar, T. Aggarwal, X. Lin, X. Lan, X. Zhao, Y. Liang, Y. Wang, Z. Wang, C. Zhou, D. Heineman, H. Liu, H. Trivedi, J. Yang, J. Lin, M. Shetty, M. Yang, N. Omi, N. Raoof, S. Li, T. Y. Zhuo, W. Lin, Y. Dai, Y. Wang, W. Chai, S. Zhou, D. Wahdany, Z. She, J. Hu, Z. Dong, Y. Zhu, S. Cui, A. Saiyed, A. Kolbeinsson, C. M. Rytting, R. Marten, Y. Wang, J. Jitsev, A. Dimakis, A. Konwinski, and L. Schmidt. Terminal-bench: Benchmarking agents on hard, realistic tasks in command line interfaces. In *The Fourteenth International Conference on Learning Representations*, 2026. URL <https://openreview.net/forum?id=a7Qa4CcHak>.
- <span id="page-15-4"></span>J. Ni, Y. Liu, X. Liu, Y. Sun, M. Zhou, P. Cheng, D. Wang, E. Zhao, X. Jiang, and G. Jiang. Trace2skill: Distill trajectory-local lessons into transferable agent skills. *arXiv preprint arXiv:2603.25158*, 2026. URL <https://arxiv.org/abs/2603.25158>.
- <span id="page-15-5"></span>S. Ouyang, J. Yan, Y. Chen, R. Han, Z. Wang, B. D. Mishra, R. Meng, C.-L. Li, Y. Jiao, K. Zha, et al. Skillos: Learning skill curation for self-evolving agents. *arXiv preprint arXiv:2605.06614*, 2026. URL <https://arxiv.org/abs/2605.06614>.

- <span id="page-16-0"></span>T. Patwardhan, R. Dias, E. Proehl, G. Kim, M. Wang, O. Watkins, S. P. Fishman, M. Aljubeh, P. Thacker, L. Fauconnet, N. S. Kim, S. Miserendino, G. Chabot, D. Li, P. Chao, M. Sharman, A. Barr, A. Glaese, and J. Tworek. GDPval: Evaluating AI model performance on real-world economically valuable tasks. In *The Fourteenth International Conference on Learning Representations*, 2026. URL [https:](https://openreview.net/forum?id=hcuEdq6eKD) [//openreview.net/forum?id=hcuEdq6eKD](https://openreview.net/forum?id=hcuEdq6eKD).
- <span id="page-16-5"></span>T. Pham, N. P. Nguyen, P. Zunjare, W. Chen, Y.-M. Tseng, and T. Vu. SealQA: Raising the bar for reasoning in search-augmented language models. In *The Fourteenth International Conference on Learning Representations*, 2026. URL <https://openreview.net/forum?id=zWb7ueH16c>.
- <span id="page-16-1"></span>L. Phan, A. Gatti, Z. Han, N. Li, J. Hu, H. Zhang, C. B. C. Zhang, M. Shaaban, J. Ling, S. Shi, et al. Humanity's last exam. *Nature*, 649(8099):1139–1146, Jan 2026. ISSN 1476-4687. doi: 10.1038/s41586-025-09962-4. URL <https://doi.org/10.1038/s41586-025-09962-4>.
- <span id="page-16-8"></span>Qwen Team. Qwen3.5: Towards native multimodal agents. <https://qwen.ai/blog?id=qwen3.5>, 2026a.
- <span id="page-16-9"></span>Qwen Team. Qwen3.6-27b. <https://qwen.ai/blog?id=qwen3.6-27b>, 2026b.
- <span id="page-16-12"></span>Y. Shi, Y. Chen, Z. Lu, Y. Miao, S. Liu, Q. Gu, X. Cai, X. Wang, and A. Zhang. Skill1: Unified evolution of skill-augmented agents via reinforcement learning. *arXiv preprint arXiv:2605.06130*, 2026. URL <https://arxiv.org/abs/2605.06130>.
- <span id="page-16-7"></span>M. Shridhar, X. Yuan, M.-A. Cote, Y. Bisk, A. Trischler, and M. Hausknecht. {ALFW}orld: Aligning text and embodied environments for interactive learning. In *International Conference on Learning Representations*, 2021. URL <https://openreview.net/forum?id=0IOX0YcCdTn>.
- <span id="page-16-6"></span>A. Singhvi, K. Opsahl-Ong, J. Collins, I. Zhou, C. Wang, A. Baheti, J. Portes, S. Havens, E. Elsen, M. Bendersky, M. Zaharia, and X. Chen. Introducing OfficeQA: A benchmark for end-to-end grounded reasoning. Databricks Blog, Dec. 2025. URL [https://www.databricks.com/blog/](https://www.databricks.com/blog/introducing-officeqa-benchmark-end-to-end-grounded-reasoning) [introducing-officeqa-benchmark-end-to-end-grounded-reasoning](https://www.databricks.com/blog/introducing-officeqa-benchmark-end-to-end-grounded-reasoning).
- <span id="page-16-13"></span>W. Su, J. Long, Q. Ai, Q. He, Y. Tang, C. Wang, Y. Tu, Y. Wang, and Y. Liu. Skill retrieval augmentation for agentic ai. *arXiv preprint arXiv:2604.24594*, 2026. URL <https://arxiv.org/abs/2604.24594>.
- <span id="page-16-10"></span>H. Wang, Y. Lan, B. Cao, L. Lin, and J. Chen. Skillgrad: Optimizing agent skills like gradient descent. *arXiv preprint arXiv:2605.27760*, 2026. URL <https://arxiv.org/abs/2605.27760>.
- <span id="page-16-11"></span>P. Xia, J. Chen, H. Wang, J. Liu, K. Zeng, Y. Wang, S. Han, Y. Zhou, X. Zhao, H. Chen, et al. Skillrl: Evolving agents via recursive skill-augmented reinforcement learning. *arXiv preprint arXiv:2602.08234*, 2026a. URL <https://arxiv.org/abs/2602.08234>.
- <span id="page-16-2"></span>P. Xia, J. Chen, X. Yang, H. Tu, J. Liu, K. Xiong, S. Han, S. Qiu, H. Ji, Y. Zhou, et al. Metaclaw: Just talk–an agent that meta-learns and evolves in the wild. *arXiv preprint arXiv:2603.17187*, 2026b. URL <https://arxiv.org/abs/2603.17187>.
- <span id="page-16-3"></span>R. Xu and Y. Yan. Agent skills for large language models: Architecture, acquisition, security, and the path forward. *arXiv preprint arXiv:2602.12430*, 2026. URL [https://arxiv.org/abs/2602.1](https://arxiv.org/abs/2602.12430) [2430](https://arxiv.org/abs/2602.12430).
- <span id="page-16-4"></span>Y. Yang, Z. Gong, W. Huang, Q. Yang, Z. Zhou, Z. Huang, Y. Li, X. Gao, Q. Dai, B. Liu, et al. Skillopt: Executive strategy for self-evolving agent skills. *arXiv preprint arXiv:2605.23904*, 2026. URL <https://arxiv.org/abs/2605.23904>.

- <span id="page-17-2"></span>S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. R. Narasimhan, and Y. Cao. React: Synergizing reasoning and acting in language models. In *The Eleventh International Conference on Learning Representations*, 2023. URL [https://openreview.net/forum?id=WE\\_vluYUL-X](https://openreview.net/forum?id=WE_vluYUL-X).
- <span id="page-17-5"></span>H. Ye, X. He, V. Arak, H. Dong, and G. Song. Meta context engineering via agentic skill evolution. In *Forty-third International Conference on Machine Learning*, 2026. URL [https://openreview.net](https://openreview.net/forum?id=P1jHroBS5E) [/forum?id=P1jHroBS5E](https://openreview.net/forum?id=P1jHroBS5E).
- <span id="page-17-1"></span>M. Yuksekgonul, F. Bianchi, J. Boen, S. Liu, P. Lu, Z. Huang, C. Guestrin, and J. Zou. Optimizing generative ai by backpropagating language model feedback. *Nature*, 639(8055):609–616, Mar 2025. ISSN 1476-4687. doi: 10.1038/s41586-025-08661-4. URL [https://doi.org/10.1038/](https://doi.org/10.1038/s41586-025-08661-4) [s41586-025-08661-4](https://doi.org/10.1038/s41586-025-08661-4).
- <span id="page-17-0"></span>B. Zhang, K. Lazuka, and M. Murag. Equipping agents for the real world with agent skills. [https:](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) [//www.anthropic.com/engineering/equipping-agents-for-the-real-world-wit](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) [h-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), Oct. 2025.
- <span id="page-17-4"></span>H. Zhang, S. Fan, H. P. Zou, Y. Chen, Z. Wang, J. Zhou, C. Li, W.-C. Huang, Y. Yao, K. Zheng, et al. Coevoskills: Self-evolving agent skills via co-evolutionary verification. *arXiv preprint arXiv:2604.01687*, 2026a. URL <https://arxiv.org/abs/2604.01687>.
- <span id="page-17-7"></span>H. Zhang, S. Zhang, K. Li, C. Zhang, Y. Chen, Y. Zhang, L. Bai, and S. Hu. Self-harness: Harnesses that improve themselves. *arXiv preprint arXiv:2606.09498*, 2026b. URL [https://arxiv.org/](https://arxiv.org/abs/2606.09498) [abs/2606.09498](https://arxiv.org/abs/2606.09498).
- <span id="page-17-6"></span>Y. Zheng, Z. Zhang, C. Ma, Y. Yu, J. Zhu, Y. Wu, T. Xu, B. Dong, H. Zhu, R. Huang, et al. Skillrouter: Skill routing for llm agents at scale. *arXiv preprint arXiv:2603.22455*, 2026. URL [https://arxi](https://arxiv.org/abs/2603.22455) [v.org/abs/2603.22455](https://arxiv.org/abs/2603.22455).
- <span id="page-17-3"></span>H. Zhou, S. Guo, A. Liu, Z. Yu, Z. Gong, B. Zhao, Z. Chen, M. Zhang, Y. Chen, J. Li, et al. Mementoskills: Let agents design agents. *arXiv preprint arXiv:2603.18743*, 2026. URL [https://arxiv.or](https://arxiv.org/abs/2603.18743) [g/abs/2603.18743](https://arxiv.org/abs/2603.18743).

## <span id="page-18-1"></span>A. Method Details

#### A.1. Algorithm

The full skill-evolution algorithm for WikiSkill is described in Algorithm 1.

<span id="page-18-0"></span>**Algorithm 1 WikiSkill evolution loop.** At each iteration k, the inference agent rolls out on training tasks using active skills  $S_{k-1}$ , the maintainer consolidates sampled traces into the intermediate wiki  $W'_k$ , the proposer generates candidate skill modifications  $P_k$ , validation gating determines whether to accept  $S'_k$  or roll back to  $S_{k-1}$ , and the system appends the proposal outcome and skill diff to produce the final wiki state  $W_k$ .

```
Require: Training tasks \mathcal{D}_{\text{train}}, validation tasks \mathcal{D}_{\text{val}}, performance metric \mathcal{R}, iterations K
  1: Initialize skill set S_0 \leftarrow \emptyset, wiki W_0 \leftarrow \emptyset
  2: Baseline Validation: \mathcal{T}_{\text{val},0} \leftarrow \{\tau_i \sim \pi(x_i; S_0)\}_{x_i \in \mathcal{D}_{\text{val}}}, \quad \mathcal{R}_{\text{best}} \leftarrow \mathcal{R}(\mathcal{T}_{\text{val},0})
 3: for k = 1, ..., K do
              if \mathcal{R}_{best} = 1.0 then
  4:
                     break
  5:
               end if
  6:
               Inference: Roll out \mathcal{T}_{\text{train},k} \leftarrow \{\tau_i \sim \pi(x_i; S_{k-1})\}_{x_i \in \mathcal{D}_{\text{train}}}
  7:
               Sample subset \mathcal{T}_{\text{sample},k} \subset \mathcal{T}_{\text{train},k}
 8:
               Wiki Maintenance: W'_{k} \leftarrow \mathcal{M}_{WM}(W_{k-1}, \mathcal{T}_{sample,k})
 9:
10:
               Skill Proposal: P_k \leftarrow \mathcal{M}_P(W'_k, S_{k-1}, \mathcal{T}_{train,k})
              Apply: S'_k \leftarrow \text{Apply}(S_{k-1}, P_k)
11.
              Validate: \mathcal{T}_{\text{val},k} \leftarrow \{\tau_i \sim \pi(x_i; S'_k)\}_{x_i \in \mathcal{D}_{\text{val}}}
12:
              if \mathcal{R}(\mathcal{T}_{\text{val},k}) > \mathcal{R}_{\text{best}} then
13:
                     S_k \leftarrow S'_k, \mathcal{R}_{\text{best}} \leftarrow \mathcal{R}(\mathcal{T}_{\text{val},k}), a_k \leftarrow \text{Accepted}
14:
15:
                     S_k \leftarrow S_{k-1}, \quad a_k \leftarrow \text{Rejected}
                                                                                                                                ▶ Roll back skills only; wiki retained
16.
17:
               Update Wiki Log: W_k \leftarrow \text{Update}(W'_k, P_k, \mathcal{R}(\mathcal{T}_{\text{val},k}), a_k)
18:
19: end for
20: return S_K, W_K
```

#### A.2. Distribution of Accepted Skill Updates

<span id="page-18-2"></span>We show when the updated skill proposals are accepted in Table 5.

# B. Dataset Details and Splits

We describe the five benchmarks used in our evaluation below.

**LiveMathematicianBench (LiveMath)** (He et al., 2026) consists of multiple-choice mathematics competition problems from recent months. It tests the model's capacity for complex mathematical reasoning, quantifiers, and extremal conditions. **SealQA** (Pham et al., 2026) is a factual question-answering benchmark composed of scholarly questions across various topics. It evaluates the agent's ability to formulate effective search queries and extract answers from web search results using a search tool. **SpreadsheetBench (SpreadSheet)** (Ma et al., 2024) tests the agent's ability to write correct code under library constraints (such as formula evaluation limitations) and execute complex table transformations. **OfficeQA** (Singhvi et al., 2025) evaluates long-context question-answering

<span id="page-19-0"></span>

| Category         | Early (Iter 0–1) | Mid (Iter 2–4) | Late (Iter 5–7) |
|------------------|------------------|----------------|-----------------|
| By Model         |                  |                |                 |
| Qwen-3.5-4B      | 39%              | 39%            | 21%             |
| Qwen-3.5-9B      | 52%              | 30%            | 19%             |
| Qwen-3.6-27B     | 43%              | 40%            | 17%             |
| Gemma-4-31B      | 52%              | 37%            | 11%             |
| Gemini-3.5-Flash | 50%              | 46%            | 4%              |
| By Benchmark     |                  |                |                 |
| LiveMath         | 44%              | 42%            | 14%             |
| SealQA           | 39%              | 33%            | 28%             |
| SpreadSheet      | 41%              | 48%            | 11%             |
| OfficeQA         | 58%              | 26%            | 16%             |
| ALFWorld         | 55%              | 34%            | 10%             |
|                  |                  |                |                 |

Table 5 | **Distribution of accepted skill updates across evolution iterations, grouped by model (top) and benchmark (bottom).** Percentages indicate the proportion of accepted updates that occur during each stage of evolution.

over a large repository of historical Treasury bulletins. Tasks require synthesizing evidence across long contexts and multi-page financial tables. Following the setup in [Yang et al.](#page-16-4) [\(2026\)](#page-16-4), the agent is provided with pre-parsed oracle reference pages as initial document evidence in the prompt, while retaining access to local text-processing tools (glob, grep, read) to search, cross-reference, and inspect full Treasury bulletin files on disk. **ALFWorld** [\(Shridhar et al.,](#page-16-7) [2021\)](#page-16-7) is an interactive textbased embodied environment where an agent solves multi-step household tasks (e.g., picking and placing objects, heating or cooling items) by outputting text actions to a simulator. Unlike static QA benchmarks, ALFWorld tests sequential decision-making, spatial reasoning, and error recovery from simulator feedback.

<span id="page-19-1"></span>

| Benchmark   | Interaction | Train | Val | Test | Environment Tools       |
|-------------|-------------|-------|-----|------|-------------------------|
| LiveMath    | Single-Step | 35    | 18  | 124  | None (Direct Reasoning) |
| SealQA      | Multi-Step  | 16    | 10  | 85   | web_search, read_file   |
| SpreadSheet | Multi-Step  | 80    | 40  | 280  | bash                    |
| OfficeQA    | Multi-Step  | 50    | 24  | 172  | glob, grep, read        |
| ALFWorld    | Multi-Step  | 39    | 18  | 134  | Admissible Actions      |

Table 6 | **Benchmark statistics, data splits, interaction modes, and available environment tools.**

Table [6](#page-19-1) summarizes the sample counts across training, validation, and test splits, interaction modes, and available tools for each benchmark evaluated in our experiments. All task splits and available toolsets are strictly matched with prior work [\(Alzubi et al.,](#page-14-5) [2026;](#page-14-5) [Yang et al.,](#page-16-4) [2026\)](#page-16-4). For tool setup, LiveMath operates as a single-step reasoning benchmark without external tools, where the model generates final answers directly; SealQA equips the agent with web search (using Google Search API) and file reading for multi-step factual retrieval (we use the July, 2026 version of SealQA for all experiments); SpreadSheet provides a bash shell tool for Python code execution and table manipulation; OfficeQA provides local text-search utilities for multi-step Treasury bulletin navigation; and ALFWorld provides an interactive simulator action space for multi-step embodied decision making.

**Evaluation robustness with small validation sets** Following established setups in prior work [\(Alzubi](#page-14-5) [et al.,](#page-14-5) [2026;](#page-14-5) [Yang et al.,](#page-16-4) [2026\)](#page-16-4), benchmark validation splits are relatively small, which can introduce evaluation noise into gating decision. To account for this variability, all reported scores represent <span id="page-20-0"></span>the average test performance across three independent runs of the entire evolutionary pipeline, with paired bootstrap significance testing (detailed in Appendix [C\)](#page-20-0).

# **C. Implementation Details**

To provide diagnostic feedback for the Wiki maintainer, we apply a stratified sampling strategy (Tsample, ⊂ Ttrain,) at each iteration . Specifically, the system samples up to 8 traces per iteration, stratified into a maximum of 5 failing traces (to perform root-cause analysis of errors) and up to 3 passing traces (to identify effective strategies and prevent regressions in working behaviors). Each individual execution log is capped at 15,000 characters prior to injection into the prompt.

**Statistical significance testing** We perform paired bootstrap significance tests with 1, 000 iterations for each benchmark. In each bootstrap iteration, task instances are sampled with replacement from the test split Dtest to construct a bootstrap evaluation set of size |Dtest|, from which candidate accuracy scores and pairwise performance margins are computed. To evaluate overall cross-benchmark performance, we conduct stratified macro-average bootstrap resampling: in each iteration, task instances are resampled independently with replacement within each benchmark, and we calculate macro-average accuracy by assigning equal weight to all benchmarks.

We determine top-performing methods in our evaluation tables as follows. Methods are initially ranked by their observed performance (or macro-average performance across benchmarks). A topranked method <sup>∗</sup> is the sole top performer if and only if it achieves a statistically significant gain over all competing methods at < 0.05. If <sup>∗</sup> is not statistically distinguishable ( ≥ 0.05) against one or more lower-ranked methods, no single method is declared the sole top performer. Instead, all methods whose performance is not statistically distinguishable from <sup>∗</sup> ( ≥ 0.05) are grouped into a top-tier statistical tie (and bolded accordingly).

# <span id="page-20-1"></span>**D. Baseline Details and Optimizer API Call Analysis**

#### **D.1. Baseline Methods**

**Trace2Skill [\(Ni et al.,](#page-15-4) [2026\)](#page-15-4)** Trace2Skill employs a three-stage pipeline centered on parallel trace analysis and hierarchical merging. It evaluates the current skill on training tasks and dispatches parallel success analysts and error analysts to extract effective strategies from passing tasks and diagnose root causes of failures. The resulting structured patches are recursively consolidated via a hierarchical merge operator into a single patch set. The consolidated patches are applied to the skill document and accepted based on validation performance.

**EvoSkill [\(Alzubi et al.,](#page-14-5) [2026\)](#page-14-5)** EvoSkill frames skill evolution as a search over a frontier of candidate programs. In each iteration, it samples training tasks via a round-robin category schedule and executes rollouts. EvoSkill feeds *only* failure traces to the proposer alongside a flat feedback history of past proposal outcomes. The proposer generates candidate skill modifications that are materialized into SKILL.md files, scored on a validation split, and added to a bounded frontier of top-performing programs.

**SkillOpt [\(Yang et al.,](#page-16-4) [2026\)](#page-16-4)** SkillOpt implements a six-stage *ReflACT* pipeline (Rollout, Reflect, Aggregate, Select, Update, Evaluate) for iterative skill optimization. In each epoch, the system rolls

out the agent on training tasks and reflects on full execution traces, including both successes and failures, to generate candidate patches. These patches are hierarchically aggregated and selected to update a single monolithic skill document, which is accepted or rejected based on validation performance.

#### D.2. Optimizer API Call Complexity

<span id="page-21-0"></span>In this section, we analyze optimizer API call complexity, denoted by C, across self-improving agent frameworks. We define one evolution iteration as rolling out the agent on the full training split  $\mathcal{D}_{\text{train}}$  once  $(N_{\text{train}} = |\mathcal{D}_{\text{train}}|$  training task instances), processed in minibatches of size B ( $B \leq N_{\text{train}}$ ). Table 7 summarizes the per-iteration optimizer API call complexity for WikiSkill and prior methods.

| Framework   | Per-Iteration Formula                                                              | Complexity                                                    |
|-------------|------------------------------------------------------------------------------------|---------------------------------------------------------------|
| Trace2Skill | $N_{\text{train}} + \left(1 + \frac{1}{c-1}\right) \frac{N_{\text{train}}}{B} + 1$ | $O\left(N_{\text{train}} + \frac{N_{\text{train}}}{B}\right)$ |
| EvoSkill    | $\frac{2N_{\mathrm{train}}}{B}$                                                    | $O\left(\frac{N_{\mathrm{train}}}{B}\right)$                  |
| SkillOpt    | $\frac{K_{\mathrm{opt}} \cdot N_{\mathrm{train}}}{B}$                              | $O\left(\frac{N_{\text{train}}}{B}\right)$                    |
| WikiSkill   | $(1 + T_{\text{ReAct}}) \frac{N_{\text{train}}}{B}$                                | $O\left(\frac{N_{\text{train}}}{B}\right)$                    |

Table 7 | Comparison of optimizer API call complexity per evolution iteration across self-improving agent frameworks.  $N_{\text{train}} = |\mathcal{D}_{\text{train}}|$  denotes the number of training tasks, B denotes the batch size,  $T_{\text{ReAct}}$  denotes the number of interactive ReAct reasoning turns used by the Skill Proposer agent in WikiSkill,  $K_{\text{opt}}$  denotes the number of reflection and merging calls per step in SkillOpt, and c denotes the reduction-tree branching factor in Trace2Skill. WikiSkill uses  $B = N_{\text{train}}$  across all datasets. In full-batch mode, WikiSkill's optimizer call count is independent of training set size  $N_{\text{train}}$ , requiring  $1 + T_{\text{ReAct}}$  optimizer calls per iteration.

**WikiSkill** For each batch of size B, the Wiki Maintainer requires one LLM call to analyze sampled traces  $\mathcal{T}_{\text{sample},k}$  and consolidate pattern pages into the intermediate wiki  $W_k'$ . The Skill Proposer then runs as an autonomous multi-turn ReAct agent, executing interactive tool calls over  $T_{\text{ReAct}}$  reasoning turns (roughly  $10 \le T_{\text{ReAct}} \le 20$  across our experiment runs), where each ReAct turn requires 1 LLM call. When processing training data in batches of size B, completing one full iteration over  $N_{\text{train}}$  tasks requires  $\frac{N_{\text{train}}}{B}$  steps:

$$C_{\text{WikiSkill}} = (1 + T_{\text{ReAct}}) \frac{N_{\text{train}}}{R}$$
 (5)

In our experiments, we set the batch size to the full training size ( $B = N_{\rm train}$ ) across all datasets. In this full-batch setting ( $\frac{N_{\rm train}}{B} = 1$ ),  $C_{\rm WikiSkill} = 1 + T_{\rm ReAct}$ . Because  $T_{\rm ReAct}$  does not depend on  $N_{\rm train}$ , WikiSkill's optimizer API call complexity is O(1) with respect to training set size. Specifically, each iteration requires  $1 + T_{\rm ReAct}$  optimizer LLM calls, regardless of the number of training instances. While this constant call complexity may incur higher inference cost on some datasets, the additional computation is accompanied by consistent performance gains over prior skill-evolution methods across our evaluation.

**EvoSkill** EvoSkill partitions training tasks into minibatches of size *B*. For each minibatch, EvoSkill uses one Proposer LLM call for error diagnosis and one Generator LLM call for skill updates. Processing

the full training split of  $N_{\text{train}}$  tasks requires  $\frac{N_{\text{train}}}{R}$  minibatch steps, resulting in:

$$C_{\text{EvoSkill}} = \frac{2N_{\text{train}}}{B} \tag{6}$$

Thus, EvoSkill's optimizer API call complexity scales linearly with training set size  $N_{\text{train}}(O(N_{\text{train}}/B))$ .

**SkillOpt** SkillOpt evaluates minibatches of size *B*, completing each iteration in  $\frac{N_{\text{train}}}{B}$  optimization steps. During each step, SkillOpt executes its ReflACT pipeline (parallel analyst reflections, hierarchical patch synthesis, and candidate selection), requiring  $K_{\text{opt}} \approx 6-8$  optimizer LLM calls per step:

$$C_{\text{SkillOpt}} = \frac{K_{\text{opt}} \cdot N_{\text{train}}}{B} \tag{7}$$

SkillOpt similarly scales linearly with training set size  $N_{\text{train}}$ , as  $O(N_{\text{train}}/B)$ .

Trace2Skill Trace2Skill processes training trajectories through a three-stage pipeline per iteration:

- 1. **Trace analysis stage:** Every individual execution trajectory is analyzed independently with one LLM call, incurring  $N_{\text{train}}$  total calls.
- 2. **Patch map stage:** Analysis records are chunked into batches of size B, requiring  $\frac{N_{\text{train}}}{B}$  calls to generate local skill patches.
- 3. **Hierarchical reduce & apply stage:** The  $\frac{N_{\text{train}}}{B}$  local patches are recursively merged via a c-ary reduction tree (where c is the branching factor). Summing across levels yields  $\approx \frac{1}{c-1} \frac{N_{\text{train}}}{B}$  merge calls, plus one final call to format the skill document.

Combining all stages:

$$C_{\text{Trace2Skill}} \approx N_{\text{train}} + \left(1 + \frac{1}{c-1}\right) \frac{N_{\text{train}}}{B} + 1$$
 (8)

Because Trace2Skill performs individual LLM analysis on every training trajectory ( $N_{\text{train}}$  calls), its complexity is lower-bounded by  $O(N_{\text{train}})$ , scaling linearly with training set size.

**Full-batch training vs. minibatch optimization** Across all datasets, we set the batch size B to the full training set size ( $B = N_{\rm train}$ ) for WikiSkill, processing the entire training set at once per iteration. The Skill Proposer dynamically searches, selects, and reads specific execution traces on demand to diagnose root causes before proposing skill updates. In contrast, EvoSkill and SkillOpt achieve their best performance under minibatch settings ( $B < N_{\rm train}$ ), which causes their optimizer API call complexity to scale linearly with training set size. Finally, Trace2Skill remains strictly  $O(N_{\rm train})$  regardless of minibatch size because it requires an independent LLM call for every training trajectory.

### E. System and Agent Prompts

We provide the exact system prompts used for (1) the Inference Agent for each task across all methods, (2) the Wiki Maintainer, and (3) the Skill Proposer in WikiSkill.

### **E.1. Task Inference Agent System Prompts**

#### **LiveMathematicianBench Inference Agent System Prompt**

You are an expert mathematical reasoning agent solving multiple-choice questions.

{skill\_section}

#### ## Task Format

You will receive one mathematics multiple-choice question and its answer choices. Reason carefully about quantifiers, hypotheses, extremal wording, and exact equality conditions.

#### ## Answer Format

Think step by step, then provide your final answer inside <answer>...</answer> tags. Inside the tags, output only the single choice label, such as A or C.

#### Example:

<answer>B</answer>

### **SealQA Inference Agent System Prompt**

You are a knowledgeable question-answering assistant with access to web\_search and read\_file tools.

{skill\_section}

### ## Task

You will receive a factual question. To answer it:

- 1. You can check the available skills. They contain guidance that can improve your search queries and answer accuracy.
- 2. You can use web\_search to find relevant information. You can call it multiple times with different queries.
- 3. You can do web\_search anytime during the process depending on your needs.
- 4. After gathering enough information, provide your final answer.

# ## Answer Format

You MUST wrap your final answer in <answer> tags:

<answer>

... your final answer (exact value only, no explanation) ...

</answer>

#### **SpreadsheetBench Inference Agent System Prompt**

You are a spreadsheet expert who can manipulate spreadsheets through Python code.

```
{skill_section}
```

You need to solve the given spreadsheet manipulation question, which contains the following information:

- working\_directory: The absolute path to your working directory where files are located.
- instruction: The question about spreadsheet manipulation.
- spreadsheet\_path: The absolute path of the spreadsheet file you need to manipulate.
- spreadsheet\_content: The first few rows of the content of spreadsheet file.
- instruction\_type: There are two values (Cell-Level Manipulation, Sheet-Level Manipulation) used to indicate whether the answer to this question applies only to specific cells or to the entire worksheet.

- answer\_position: The position need to be modified or filled. For Cell-Level Manipulation questions, this field is filled with the cell position; for Sheet-Level Manipulation, it is the maximum range of cells you need to modify. You only need to modify or fill in values within the cell range specified by answer\_position.
- output\_path: The absolute path where you must save the modified spreadsheet.

#### ## CRITICAL RESTRICTIONS

You can ONLY read and write files within the \*\*working\_directory\*\*. Any attempt to access files outside this directory will fail.

- \*\*Allowed paths\*\*: working\_directory (and its subdirectories)
- \*\*Read from\*\*: spreadsheet\_path (inside working\_directory)
- \*\*Write to\*\*: output\_path (inside working\_directory)

Do NOT create files outside the working\_directory. Use the exact absolute paths provided.

You have access to a bash tool that can execute any shell command.

## **OfficeQA Inference Agent System Prompt**

You are an expert OfficeQA agent working over local Treasury bulletin text files.

{skill\_section}

#### ## Rules

- 1. Use only the provided local document tools to inspect candidate files.
- 2. Narrow to the most relevant file before reading long passages.
- 3. Prefer short targeted searches, then small reads around matching evidence.
- 4. Do not invent values that are not grounded in the retrieved text.
- 5. When the question requires arithmetic, compute only after extracting the exact operands.
- 6. If you have enough evidence, return the final answer inside <answer>...</answer>.

#### ## Tool Use

Use the provided function tools directly when you need them. Prefer searching and small reads before answering. Do not ask the user for permission to use tools; just call the tools.

#### ## Final Answer Format

When you are ready to answer, emit the final answer inside <answer>...</answer> and do not request another tool.

### **ALFWorld Inference Agent System Prompt**

You are an expert agent operating in the ALFRED Embodied Environment. Your task is to: { task\_description}

{skill\_section}

Prior to this step, you have already taken {step\_count} step(s). Below are the most recent {history\_length} observations and the corresponding actions you took: { action\_history}

You are now at step {current\_step} and your current observation is: {current\_observation}

Your admissible actions of the current situation are: [{admissible\_actions}].

Now it's your turn to take an action. You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags. Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.

### **E.2. Wiki Maintainer Agent System Prompt**

## Analysis Guidelines

# **Wiki Maintainer Agent System Prompt** You are a Wiki Maintainer Agent for an LLM skill evolution system. Your job is to maintain a structured knowledge base (wiki) that documents patterns observed during agent execution -- both successes and failures. You must perform DEEP ANALYSIS of execution logs to identify root causes, not just surface-level symptoms. ## Wiki Structure The wiki is organized as: - wiki/index.md -- Concise catalog of known patterns (one line per pattern) - wiki/log.md -- Chronological evolution log (iterations, scores, accept/reject) - wiki/skill-impact.md -- Record of which skills were tried and their outcomes - wiki/patterns/ -- One page per pattern with detailed evidence and analysis ## Your Input 1. Execution traces from the latest iteration -- including full agent execution logs showing what actions the agent took, what commands it ran, and what environment feedback it observed 2. The current wiki context (index, log, pattern pages) ## Your Output (Incremental Edit Mode) Return a JSON object with these keys: - "create\_patterns": list of {"name": "pattern-name.md", "content": "..."} -- new patterns (full content) - "update\_patterns": list of {"name": "existing-pattern.md", "edits": [...]} -- patch existing patterns - "update\_index": full updated content of index.md (always provide the complete index) - "append\_log": "brief summary of this iteration's findings and actions" "update\_index" and "append\_log" are REQUIRED. Always provide them, even if there are no new patterns. For "update\_index", always provide the complete updated index content including all existing entries plus any new ones. ### Patch Operations (for update\_patterns only) For "update\_patterns", each entry uses an "edits" list of patch operations: - {"op": "append", "content": "text to add at end"} - {"op": "replace", "target": "exact text to find", "content": "replacement text"} - {"op": "insert\_after", "target": "exact text to find", "content": "text to insert after"} Rules for patch operations: 1. "target" must be an EXACT substring of the existing content. 2. Use "append" to add new evidence. Use "replace" to fix or refine existing text. 3. Use "insert\_after" to add entries after a specific line. 4. Keep each edit minimal -- only change what's needed. 5. For NEW patterns (create\_patterns), use full "content".

#### ### Deep Trace Analysis (CRITICAL)

When execution logs are provided, you MUST:

- 1. Read the agent's actual actions -- what commands did it issue?
- 2. Compare successful vs failed tasks -- what did successful tasks do differently?
- 3. Identify ACTION PATTERNS and strategies, not just error messages.
- 4. Check whether the agent followed any active skills, and whether the skill guidance was helpful or not

#### ### Pattern Documentation Rules

- 1. Each pattern page should document:
  - What the pattern is (description)
  - Root cause analysis (WHY it happens, not just WHAT happens)
  - Exact command sequences from traces (what the agent did wrong / right)
  - Known solutions or workarounds (concrete action patterns with exact syntax)
- 2. Capture BOTH success and failure patterns:
  - \*\*Failure patterns\*\*: Document what went wrong and how to avoid it
  - \*\*Success patterns\*\*: Document strategies that consistently lead to task completion
- 3. Do NOT create duplicate patterns -- update existing ones with new evidence
- 4. Be concise. Pattern pages should be 10-30 lines, not essays.
- 5. Only create patterns for meaningful, generalizable observations.

### ### Index Description Quality (CRITICAL)

The index.md entries are the MOST IMPORTANT part of the wiki because they determine whether inference agents will read the full pattern pages.

Each index entry MUST follow this format:

- [pattern-name](wiki/patterns/pattern-name.md): PROBLEM + ROOT CAUSE + FIX in one or two sentence.

The description must be specific enough that an agent can judge relevance without reading the full page. Include the problem, root cause, AND solution.

#### **E.3. Skill Proposer Agent System Prompt (ReAct Mode)**

# **Skill Proposer Agent System Prompt**

You are a Skill Proposer Agent for an LLM agent that solves {task\_desc}. Your job is to explore the wiki knowledge base and execution traces, diagnose root causes of failures, and propose a skill change (create or patch).

#### ## Tools Available

You have two tools:

- 1. 'read\_file(path)' -- Read a wiki file or execution log. Paths are relative to the workspace root.
- 2. 'finish(proposal)' -- Submit your final skill proposal as a JSON object.

# ## Workflow

- 1. Start by reading 'wiki/index.md' to understand what patterns exist
- 2. Read 'wiki/skill-impact.md' to see what was tried before (includes full content of rejected proposals -- DO NOT repeat rejected approaches)
- 3. Read specific pattern pages that seem relevant to the current failures
- 4. Read execution traces for failed tasks via 'traces/<task\_id>' to understand root causes
- 5. Decide: create (new skill) or patch (edit existing skill), or no\_action
- 6. If proposing a change, call 'finish' with the full proposal

#### ## finish() Proposal Format

```
For creating a new skill:
- "action": "create"
- "name": skill directory name (snake_case)
- "skill_md": full SKILL.md content with YAML frontmatter + When to Apply + When NOT to
Apply + Instructions
- "purpose_md": full PURPOSE.md content with Origin + Patterns Addressed + Evolution
History
For patching an existing skill:
- "action": "patch"
- "name": existing skill directory name
- "edits": list of patch operations:
  - {"op": "append", "content": "text to add at end"}
  - {"op": "replace", "target": "exact text to find", "content": "replacement"}
  - {"op": "insert_after", "target": "exact text to find", "content": "text to insert
after"}
  Each "replace" target should be a short, specific section -- not the entire file. If
you need to change most of the file, use "action": "create" instead.
If no action is needed, call finish with: {"action": "no_action"}
## Rules
1. Read the wiki FIRST -- don't propose something that was already tried and rejected.
skill-impact.md contains full content of rejected proposals.
2. Focus on action patterns and concrete strategies.
3. Keep skills concise and actionable.
4. You MUST read at least 4 execution traces before proposing a skill change. Target
your exploration based on the trace summary.
5. Prefer patching existing skills over creating new ones when the existing skill is
partially correct.
```

Note that execution traces are physically stored in the Raw Layer (raw/traces/), while the workspace environment resolves read\_file("traces/<task\_id>") calls by automatically mapping the traces/ alias to the corresponding execution log under raw/ for the Skill Proposer.