# FROM EXPERIENCE TO STRATEGY: EMPOWERING LLM AGENTS WITH TRAINABLE GRAPH MEMORY

Siyu Xia $^{1,2}$ , Zekun Xu $^3$ , Jiajun Chai $^3$ , Wentian Fan $^4$ , Yan Song $^5$ , Xiaohan Wang $^3$  Guojun Yin $^3$ , Wei Lin $^3$ , Haifeng Zhang $^{1,2}$ , Jun Wang $^{5\dagger}$ 

#### **ABSTRACT**

Large Language Models (LLMs) based agents have demonstrated remarkable potential in autonomous task-solving across complex, open-ended environments. A promising approach for improving the reasoning capabilities of LLM agents is to better utilize prior experiences in guiding current decisions. However, LLMs acquire experience either through implicit memory via training, which suffers from catastrophic forgetting and limited interpretability, or explicit memory via prompting, which lacks adaptability. In this paper, we introduce a novel agentcentric, trainable, multi-layered graph memory framework and evaluate how context memory enhances the ability of LLMs to utilize parametric information. The graph abstracts raw agent trajectories into structured decision paths in a state machine and further distills them into high-level, human-interpretable strategic meta-cognition. In order to make memory adaptable, we propose a reinforcementbased weight optimization procedure that estimates the empirical utility of each meta-cognition based on reward feedback from downstream tasks. These optimized strategies are then dynamically integrated into the LLM agent's training loop through meta-cognitive prompting. Empirically, the learnable graph memory delivers robust generalization, improves LLM agents' strategic reasoning performance, and provides consistent benefits during Reinforcement Learning (RL) training.

#### 1 Introduction

LLM-based agents are rapidly advancing the frontier of automated task execution, particularly in open-ended environments that demand long-horizon reasoning, strategic tool use, and adaptation from experience (Yao et al., 2022; Gao et al., 2023; Chai et al., 2025). While these agents demonstrate strong capabilities in decomposing and tackling complex tasks, their decision-making processes remain unstable, often resulting in inefficient action sequences, repeated mistakes, or even complete task failure (Singh et al., 2023). A central challenge lies in empowering agents not only to act, but to continuously learn and adapt by extracting insights from past successes and errors.

Methods for enabling LLMs to better leverage prior experience can be broadly categorized into two paradigms. The first is **implicit memory**, is typically formed through training procedures like RL, which denotes LLMs encode syntactic structures and semantic relations into parameter space (Li et al., 2025b; Bai et al., 2022). A more intuitive alternative is **explicit memory** via contextual prompting, which improves performance by injecting guidance directly into the input without modifying model weights. (Xu et al., 2025; Chhikara et al., 2025; Zhao et al., 2024).

However, both paradigms suffer from fundamental yet contrasting limitations. Explicit memory facilitates transparency by making reasoning steps externally visible through prompts; however, it lacks adaptability and struggles to generalize beyond specific tasks or contexts. Conversely, implicit

<sup>&</sup>lt;sup>1</sup>Institute of Automation, Chinese Academy of Sciences, Beijing, China

<sup>&</sup>lt;sup>2</sup>School of Artificial Intelligence, University of Chinese Academy of Sciences, China

<sup>&</sup>lt;sup>3</sup>Meituan <sup>4</sup>Nanjing University of Posts and Telecommunications

<sup>&</sup>lt;sup>5</sup>AI Centre, Department of Computer Science, University College London, London, UK

<sup>\*</sup>Equal contribution.

<sup>&</sup>lt;sup>†</sup>Corresponding author.Contact: haifeng.zhang@ia.ac.cn, jun.wang@cs.ucl.ac.uk

![](_page_1_Figure_1.jpeg)

Figure 1: Our method and existing approach Expel (Zhao et al., 2024).

memory enables generalization via training, but its black-box nature makes the contribution of specific past experiences inaccessible and difficult to interpret, while encoding knowledge directly into parameter space often incurs information loss and is vulnerable to catastrophic forgetting. This unresolved challenge motivates our central research question: *Can we develop an agentic framework by leveraging dynamic, structured explicit memory to actively guide and enhance implicit policy learning?* 

This paper introduces a novel **agent-centric, trainable, multi-layered graph memory** framework and explores its integration with RL. First, we abstract episodic agent trajectories into canonical paths over a finite state machine, from which we derive high-level, generalizable *meta-cognition*. Second, we design a trainable graph architecture equipped with a reinforcement-driven weight optimization mechanism that calibrates the utility of stored strategies based on downstream task performance. Finally, the dynamic graph is operationalized as an *explicit policy prior*, selectively injecting high-quality strategies into the agent's context during training. Empirical results across seven diverse question-answering benchmarks demonstrate that our framework delivers strong gains in both cross-task generalization and final task performance.

Our main contributions are threefold:

- We propose a novel agent-centric memory framework that abstracts low-level agent trajectories into canonical paths on a finite state machine, enabling the distillation of highlevel, generalizable meta-cognitive strategies.
- We develop a **reinforcement-driven weight optimization mechanism** that dynamically calibrates the utility of memory connections, allowing the graph to selectively emphasize strategies with proven empirical effectiveness.
- We demonstrate that incorporating this graph memory as an explicit policy prior within RL substantially enhances policy learning and final task performance.

Ultimately, this work presents a unified framework for creating more adaptive, efficient, and strategically-aware agents that not only act, but learn and reason from a continually evolving repository of their own experiences.

## 2 RELATED WORK

#### 2.1 LLM AGENTS AND PLANNING WITH EXTERNAL TOOLS

LLM agents increasingly incorporate external tools to overcome reasoning limitations and expand their problem-solving capabilities. Early prompt-based approaches, including ReAct (Yao et al., 2022) and WebGPT (Nakano et al., 2021), demonstrate how agents can interleave reasoning and acting, embedding tool calls directly in the generation trace. Building on these foundations, Search-o1 introduces agentic RAG that dynamically retrieves knowledge during reasoning. Building on these foundations, Search-o1 (Li et al., 2025a) advances tool-augmented reasoning by enabling agents to autonomously decide when to invoke search tools during multi-step problem solving. Recent research has proposed more sophisticated coordination mechanisms using RL-based training (Sun et al., 2025; Zheng et al., 2025; Song et al., 2025). Search-R1 (Jin et al., 2025) represents a breakthrough RL framework that trains LLMs for alternating reasoning and search, enabling autonomous query generation and real-time information retrieval during step-by-step reasoning. Other recent approaches include optimized reward designs (Wang et al., 2025; Qian et al., 2025) and strategic tool

integration [\(Feng et al., 2025\)](#page-9-7), with frameworks like RL-Factory [\(Chai et al., 2025\)](#page-9-1) accelerating research in this domain.Despite these advances, the lack of explicit long-term memory for reusable tool-use patterns leaves deciding when and which tools to invoke as a key bottleneck. To address this limitation, we propose a differentiable graph-based memory system that encodes past decision paths into reusable strategic priors, enabling agents to systematically learn and generalize planning strategies across domains.

## 2.2 MEMORY ARCHITECTURES AND STRATEGIC LEARNING

Recent research has increasingly explored how to extract strategic knowledge and meta-cognition from agent experience. Reflexion [\(Zhang et al., 2023\)](#page-11-3) equips agents with self-verbalized feedback to refine future behavior, while Expel [\(Zhao et al., 2024\)](#page-11-1) identifies reusable reasoning trajectories to guide subsequent decisions. MEM1 [\(Zhou et al., 2025\)](#page-11-4) and MemAgent [\(Yu et al., 2025\)](#page-11-5) adapt memory usage over long-horizon tasks. A-MEM [\(Xu et al., 2025\)](#page-10-1) builds dynamic memory notes that evolve with new inputs, Zep [\(Rasmussen et al., 2025\)](#page-10-7)and HopRAG [\(Liu et al., 2025\)](#page-9-8) construct logic-aware graphs to facilitate retrieval.

However, these methods typically apply graph structure in a static manner and lack mechanisms to assess or refine the utility of memory components. G-Memory [\(Zhang et al., 2025\)](#page-11-6) demonstrates how hierarchical graph-based memory can evolve by assimilating new collaborative trajectories, enabling systems to leverage cross-trial knowledge and learn from prior experiences progressively. [Pan & Zhao](#page-10-8) [\(2025\)](#page-10-8)focus on whether different forms of memory can enhance reasoning. [Xiong et al.](#page-10-9) [\(2025\)](#page-10-9) investigate long-term memory evolution.While prior memory methods often rely on static storage or task-specific designs, they lack mechanisms for evaluating and refining strategies. In contrast, we propose a trainable graph-based memory that supports utility-aware strategy selection and reinforcement learning–driven updates, enabling generalizable and adaptive decision-making.

# 3 PRELIMINARIES

## 3.1 HETEROGENEOUS GRAPH STRUCTURE

Graphs provide a natural formalism for modeling structured dependencies among diverse entities. A heterogeneous graph [\(Zhang et al., 2019\)](#page-11-7)can be defined as

$$\mathcal{G} = (V, E, \mathcal{O}_V, \mathcal{R}_E, C),$$

where V denotes the set of nodes, E ⊆ V × V denotes the set of directed edges, O<sup>V</sup> denotes the set of node types, R<sup>E</sup> denotes the set of relation types, and C is the collection of node contents. Each edge e = (u, v, r) ∈ E specifies a relation of type r from node u to node v.

Connectivity in G is represented by node-type adjacency matrices

$$A^{xy} \in \{0,1\}^{|V_x| \times |V_y|}, \quad (x,y) \in \mathcal{O}_V \times \mathcal{O}_V,$$

where V<sup>x</sup> and V<sup>y</sup> denote the sets of nodes of type x and y, respectively. An entry (Axy)ij = 1 indicates that node i of type x is connected to node j of type y. This formulation emphasizes the structural dependencies across different node types.

To enable learning, each Axy is coupled with a weight matrix Wxy, so that propagation is governed by the weighted operator Axy⊙Wxy. Thus, structure defines feasible paths, while weights determine effective information flow. Formally,

$$\mathbf{H}_y = \sigma \left( (A^{xy} \odot W^{xy})^\top \mathbf{H}_x \right),\,$$

where H<sup>x</sup> are input values and σ(·) denotes an activation function.

## 3.2 LLM AGENTS WITH TOOL-AUGMENTED REASONING

The interaction between a LLM and external tools can be formalized as a structured multi-turn decision process [\(Chai et al., 2025\)](#page-9-1). At each time step t, the agent observes

$$s_t = (q, h_{1:t-1}), \quad a_t \sim \pi_{\theta}(a_t \mid s_t).$$

where q is the user query and  $h_{1:t-1}$  is the dialogue or reasoning history, then generates an action a which may correspond to internal reasoning, a tool invocation, or answer generation, using a protocol with tags such as <think>, <tool\_call>, and <answer>.

The process continues until either the tag <answer></answer> is generated or the agent has issued up to a maximum of K tool invocations. A trajectory  $\tau=(s_1,a_1,o_1,\ldots,s_T,a_T,o_T)$  yields reward  $R(\tau)$ , where  $o_t$  denotes the environment observation, i.e., tool outputs if  $a_t$  is a tool call, and the policy is optimized via

$$J(\theta) = \mathbb{E}_{\tau \sim \pi_{\theta}}[R(\tau)], \quad \nabla_{\theta} J(\theta) \approx \mathbb{E}_{\tau} \Big[ \sum_{t=1}^{T} \nabla_{\theta} \log \pi_{\theta}(a_t \mid s_t) \, \hat{A}_t \Big].$$

#### 4 METHOD

In this section, we detail our proposed method in three stages. First, we describe how to construct a memory graph that encodes decision trajectories and strategic principles. Second, we present the learning framework for optimizing the weights within this memory graph. Finally, we explain how this structured memory is integrated into the RL training process to guide agent behavior and improve learning efficiency. The overall process of our method is shown in the Figure 2.

#### 4.1 STAGE 1: HIERARCHICAL MEMORY GRAPH CONSTRUCTION

**Memory Graph Structure.** We instantiate the memory as a heterogeneous graph with node set  $V = \mathcal{Q} \cup \mathcal{T} \cup \mathcal{M}$  and directed edges  $E \subseteq (\mathcal{Q} \times \mathcal{T}) \cup (\mathcal{T} \times \mathcal{M})$ . Each node type forms a distinct layer in the hierarchy, consistent with the structural depiction in figure 2 (stage 1):

- Query Layer ( $\mathcal{Q}$ ): Formed by query nodes  $q_i$ , each representing a task instance (e.g., a user query), including input, execution trajectory, and outcome labels. Since a single query may yield multiple responses, each  $q_i$  can connect to one or more transition paths  $\{t_j\}$  via edges  $(q_i \rightarrow t_j)$ .
- Transition Path Layer ( $\mathcal{T}$ ): Formed by path nodes  $t_j$ , each denoting a canonical decision pathway derived from a finite state machine  $\mathcal{S}$  that abstracts raw execution traces into standardized behavioral patterns. These nodes are linked to the meta-cognition layer through edges  $(t_j \rightarrow m_k)$ .
- Meta-Cognition Layer  $(\mathcal{M})$ : Formed by meta-cognition nodes  $m_k$ , each encoding a high-level strategic principle distilled from both successful and failed paths, serving as generalized heuristics for problem-solving.

Connectivity is encoded by bipartite adjacency matrices

$$A^{q \to t} \in \{0,1\}^{|\mathcal{Q}| \times |\mathcal{T}|}, \quad A^{t \to m} \in \{0,1\}^{|\mathcal{T}| \times |\mathcal{M}|},$$

augmented with learnable weights  $w_{qt}$  and  $w_{tm}$  respectively. Information flows as a weighted aggregation process from queries to meta-cognition, forming a directed acyclic topology.

Finite State Machine. To obtain a standardized and comparable representation of agent behaviors across tasks, we define a Finite State Machine (FSM)  $\mathcal{S}=(S,A,T)$ . Here, S denotes abstract cognitive states (e.g., StrategyPlanning, InformationAnalysis), A is the action space, and  $T:S\times A\to S$  is the transition function. Each raw execution trajectory comprising tool invocations or reasoning steps is mapped onto a canonical path  $t_j$  within this FSM. This grounding enables structured comparison across queries while filtering execution-level noise, ensuring that the memory graph preserves only semantically meaningful decision points. The detailed specification of S is provided in the Appendix B.1.

**Meta-Cognition Induction.** Meta-cognitions are induced by analyzing the canonical decision pathways. For each query  $q_i$ , the agent samples trajectories  $\{\tau_1^{(i)}, \ldots, \tau_N^{(i)}\}$  from its policy  $\pi$ . If both successful  $(\tau_s)$  and failed  $(\tau_f)$  trajectories exist, contrasting their FSM paths yields a high-confidence meta-cognition  $m_k$  that explains the outcome divergence. If only failures occur, the

<span id="page-4-0"></span>![](_page_4_Figure_1.jpeg)

Figure 2: The framework of the proposed trainable memory. Stage 1 builds a graph from LLM trajectories, encoding queries, decision paths, and meta-cognition. Stage 2 estimates strategy utility via counterfactual rewards and updates graph weights. Stage 3 injects top-k strategies into RL training for policy optimization.

agent retrieves top-K semantically similar queries  $Sim(q_i,q_j)=\cos(\mathbf{e}_{q_i},\mathbf{e}_{q_j})$ , and derives speculative meta-cognitions from successful paths of these neighbors:

$$\mathcal{M}^{\mathrm{spec}}(q_i) = \bigcup_{q_j \in \mathrm{TopK}(q_i)} \{m_k \mid t_j \in \mathrm{SuccessPaths}(q_j), \, m_k \in \mathcal{M}(t_j)\}.$$

Concrete examples and the corresponding prompts are provided in Appendix E.3.

**Meta-Cognition Update.** The memory graph is dynamically updated to preserve relevance and utility. When a new decision path is generated, the agent evaluates its strategic value: reinforcing existing principles updates their confidence, novel patterns lead to new meta-cognition nodes, and redundant or low-confidence paths are discarded. This selective process curates a concise set of strategic principles that evolves with experience.

The hierarchical structure thus abstracts low-level trajectories into reusable strategies. At inference, the memory graph  $\mathcal G$  functions as a structured policy prior guiding decision-making, while during training it provides supervision signals for reward-driven consolidation of meta-cognitive knowledge.

#### <span id="page-5-0"></span>4.2 STAGE 2: TRAINABLE GRAPH WEIGHT OPTIMIZATION

The memory graph provides structural priors, but not all meta-cognitions contribute equally. To adaptively capture their utility, we introduce a reinforcement-driven weight optimization procedure.

**Parameterizing the Graph for Utility Learning.** We parameterize the memory graph  $\mathcal{G}$  as a sparsely connected weighted network, where each edge is associated with a trainable coefficient reflecting its utility. Given query features  $\mathbf{H}_{\mathcal{Q}}^{(0)}$ , information propagates through the graph via weighted aggregation:

$$\mathbf{H}_{\mathcal{T}}^{(1)} = \sigma \Big( (A_{qt} \odot W_{qt})^{\top} \mathbf{H}_{\mathcal{Q}}^{(0)} \Big), \quad \mathbf{H}_{\mathcal{M}}^{(2)} = \sigma \Big( (A_{tm} \odot W_{tm})^{\top} \mathbf{H}_{\mathcal{T}}^{(1)} \Big),$$

which corresponds to the flow from the *query layer*, through the transition layer, and finally to the *meta-cognition layer* in Figure 2.

In our formulation, a new query is represented by its similarity to historical queries in the graph, and the top-k most relevant neighbors are selected to activate a task-specific subgraph  $\mathcal{G}(q_{\text{new}}) = (\mathcal{Q}', \mathcal{T}', \mathcal{M}')$ . Within this subgraph, a candidate meta-cognition  $m_k \in \mathcal{M}'$  is sampled according to a relevance score  $\rho(m_k)$ , derived from the learned graph weights.

To estimate its empirical utility, we contrast two trajectories: one guided by  $m_k$ , which yields reward  $R_{\rm with}(m_k)$ , and another without such guidance, yielding reward  $R_{\rm w/o}$ . The resulting reward gap  $\Delta R_k = R_{\rm with}(m_k) - R_{\rm w/o}$  is employed as a utility signal, quantifying the marginal contribution of  $m_k$  to overall task performance.

**Policy Gradient-Based Weight Optimization.** The relevance score  $\rho(m_k \mid q_{\text{new}})$  is computed by aggregating path strengths from historical queries and transitions leading to  $m_k$ :

$$\rho(m_k \mid q_{\text{new}}) = \sum_{q_i, t_j : q_i \to t_j \to m_k} \text{Sim}(q_{\text{new}}, q_i) \cdot w_{qt}^{(i,j)} \cdot w_{tm}^{(j,k)}.$$

Using a softmax over these scores, the selection probability  $p(m_k \mid q_{\text{new}}) \propto \exp(\rho(m_k \mid q_{\text{new}}))$ .

We apply the REINFORCE algorithm to optimize the weights:

$$\mathcal{L}_{\mathrm{RL}} = -\mathbb{E}_{m_k \sim p} \left[ \Delta R_k \cdot \log p(m_k \mid q_{\mathrm{new}}) \right].$$

A positive  $\Delta R_k$  increases the relevance score and strengthens the supporting paths, while a negative  $\Delta R_k$  decreases them, enabling the memory graph to refine itself over time.

## 4.3 STAGE 3: MEMORY-GUIDED POLICY OPTIMIZATION

Departing from prior works that leverage memory solely during inference, our framework explicitly integrates the structured memory into the *training loop*. Meta-cognitive strategies are dynamically retrieved from the optimized memory graph and incorporated into the agent's context, serving as high-level strategic priors that guide the reinforcement learning process.

**Strategic Context Retrieval.** For each training instance  $q_{\text{train}}$ , we compute a relevance score for every meta-cognition node  $m \in \mathcal{M}$ . This score is derived from the aggregated weights of all paths connecting the corresponding query node to the meta-cognition node within the memory graph  $\mathcal{G}$  (as formulated in Section 4.2). We then select the top-k meta-cognitions  $\{m_1,\ldots,m_k\}$  with the highest scores. This mechanism ensures that the guidance is not only relevant but also grounded in empirically successful past trajectories, as encoded by the learned edge weights.

The retrieved strategies are verbalized and prepended to the original query to form an augmented prompt,  $\tilde{q}_{\text{train}} = [m_1, m_2, \dots, m_k; q_{\text{train}}]$ , this augmented prompt serves as the input to the policy network.

**Optimization Objective.** The agent's policy,  $\pi_{\theta}$ , is optimized to maximize the expected cumulative reward conditioned on the augmented context. We employ a policy gradient method, where the parameters  $\theta$  are updated by minimizing the following loss function:

$$\mathcal{L}_{\text{RL+Mem}} = -\mathbb{E}_{a \sim \pi_{\theta}(\cdot \mid \tilde{q}_{\text{train}})} \big[ R(a) \big].$$

<span id="page-6-0"></span>

| Table 1: Performance comparison across seven QA datasets in inference. †<br>indicates in-domain datasets, while<br>⋆<br>denotes out-of-domain datasets. Percentages in Avg. column denote relative improvement over ITR. |  |  |  |  |  |  |  |  |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--|--|--|--|--|--|--|--|
|                                                                                                                                                                                                                          |  |  |  |  |  |  |  |  |

| Methods           | Avg. (↑ / ↓ vs. ITR) | General QA |           |        | Multi-Hop QA |        |          |            |  |
|-------------------|----------------------|------------|-----------|--------|--------------|--------|----------|------------|--|
|                   |                      | NQ⋆        | TriviaQA⋆ | PopQA⋆ | HotpotQA†    | 2wiki⋆ | Musique⋆ | Bamboogle⋆ |  |
| Qwen3-8B          |                      |            |           |        |              |        |          |            |  |
| ITR               | 0.334 (–)            | 0.275      | 0.593     | 0.358  | 0.325        | 0.324  | 0.094    | 0.365      |  |
| Direct Inference  | 0.269 (↓19.5%)       | 0.200      | 0.519     | 0.191  | 0.230        | 0.275  | 0.058    | 0.410      |  |
| CoT               | 0.252 (↓24.6%)       | 0.209      | 0.512     | 0.182  | 0.223        | 0.271  | 0.055    | 0.308      |  |
| Direct Trajectory | 0.352 (↑5.4%)        | 0.317      | 0.604     | 0.380  | 0.329        | 0.363  | 0.105    | 0.364      |  |
| A-MEM             | 0.334 (0.0%)         | 0.286      | 0.590     | 0.366  | 0.339        | 0.332  | 0.112    | 0.313      |  |
| EXPEL             | 0.329 (↓1.5%)        | 0.306      | 0.594     | 0.379  | 0.317        | 0.327  | 0.092    | 0.287      |  |
| Ours              | 0.365(↑9.3%)         | 0.316      | 0.622     | 0.382  | 0.358        | 0.354  | 0.128    | 0.392      |  |
| Qwen3-4B          |                      |            |           |        |              |        |          |            |  |
| ITR               | 0.279 (–)            | 0.298      | 0.581     | 0.157  | 0.268        | 0.281  | 0.077    | 0.290      |  |
| Direct Inference  | 0.211 (↓24.4%)       | 0.158      | 0.413     | 0.157  | 0.183        | 0.240  | 0.033    | 0.290      |  |
| CoT               | 0.181 (↓35.1%)       | 0.149      | 0.375     | 0.146  | 0.156        | 0.190  | 0.022    | 0.228      |  |
| Direct Trajectory | 0.325 (↑16.5%)       | 0.310      | 0.558     | 0.379  | 0.282        | 0.344  | 0.076    | 0.327      |  |
| A-MEM             | 0.319 (↑14.3%)       | 0.310      | 0.586     | 0.381  | 0.272        | 0.269  | 0.091    | 0.325      |  |
| EXPEL             | 0.321 (↑15.1%)       | 0.312      | 0.570     | 0.388  | 0.294        | 0.347  | 0.075    | 0.263      |  |
| Ours              | 0.351 (↑25.8%)       | 0.335      | 0.596     | 0.393  | 0.299        | 0.347  | 0.099    | 0.391      |  |

This tight integration ensures that the policy does not learn in isolation but is continually guided by a dynamically evolving corpus of strategic knowledge. This allows the agent to effectively bootstrap its learning process from a distilled representation of past successes.

In practice, we adopt the Generalized Reinforcement Policy Optimization (GRPO) algorithm to optimize the memory-augmented policy. The GRPO loss can be written as:

$$\mathcal{L}_{\text{GRPO}} = -\mathbb{E}_t \left[ \min \left( \frac{\pi_{\theta}(a_t \mid \tilde{q}_{\text{train}})}{\pi_{\theta_{\text{old}}}(a_t \mid \tilde{q}_{\text{train}})} \hat{A}_t, \; \text{clip} \left( \frac{\pi_{\theta}(a_t \mid \tilde{q}_{\text{train}})}{\pi_{\theta_{\text{old}}}(a_t \mid \tilde{q}_{\text{train}})}, 1 - \epsilon, 1 + \epsilon \right) \hat{A}_t \right) \right],$$

where Aˆ <sup>t</sup> is the advantage estimator and ϵ the clipping parameter.

# 5 EXPERIMENT

## 5.1 DATASETS

To evaluate the effectiveness and generalizability of our approach, we conduct experiments on seven widely-used Question-Answering(QA) datasets, covering both single-turn and multi-hop reasoning tasks. (1) General QA Datasets: We include Natural Questions [\(Kwiatkowski et al., 2019\)](#page-9-9), TriviaQA [\(Joshi et al., 2017\)](#page-9-10), and PopQA [\(Mallen et al., 2022\)](#page-10-10), which consist of open-domain factoid questions requiring retrieval and basic reasoning capabilities. (2) Multi-hop QA Datasets: For more complex reasoning scenarios, we adopt HotpotQA [\(Yang et al., 2018\)](#page-10-11), 2WikiMultiHopQA [\(Ho et al.,](#page-9-11) [2020\)](#page-9-11), Musique [\(Trivedi et al., 2022\)](#page-10-12), and Bamboogle [\(Press et al., 2022\)](#page-10-13), which require integrating information across multiple documents.

# 5.2 BASELINE EVALUATION

To comprehensively evaluate the effectiveness of our proposed method, we design experiments from two complementary perspectives: (1) Direct Inference Impact: We assess how the integration of our memory workflow influences model performance in zero-training settings, i.e., during direct inference. (2) Training Impact: We investigate how the memory architecture affects RL training dynamics, focusing on convergence speed and the final performance achieved. Detailed baseline configurations are provided in Appendix [A.2.](#page-11-8)

# 5.3 MAIN RESULTS

Experimental Analysis: Memory-Guided Inference. The detailed inference results are summarized in Table [1.](#page-6-0) On the 8B-scale model, our method demonstrates strong competitiveness, achieving an average score of 0.365, which represents a notable **+9.3%** relative improvement over the ITR baseline and ranks first among all contenders. The advantages of our method become even more dramatic on the smaller Qwen3-4B model. It achieves a staggering **+25.8%** relative improvement in average performance over the ITR baseline, this significant performance improvement on a model with limited capacity suggests that our method effectively addresses its inherent deficiencies by providing a robust and structured reasoning framework.

A particularly noteworthy finding is that the memory component of our method was constructed exclusively using data from HotpotQA, the single in-domain dataset. Despite this, our method not only excels on HotpotQA but also achieves state-of-the-art or highly competitive performance across all out-of-domain datasets, including NQ, TriviaQA, PopQA, and 2wiki. This outcome is a strong testament to the remarkable generalization capability of our approach. It demonstrates that the reasoning structures learned from HotpotQA are not merely overfitted patterns.

<span id="page-7-0"></span>Table 2: Performance comparison across seven QA datasets in training. Avg. column also reports relative improvement (%) compared to Search-R1 as the base. † indicates in-domain datasets, while \* denotes out-of-domain datasets.

| Methods           | Avg. (↑ / ↓ vs. Search-R1)   | General QA |           |        | Multi-Hop QA          |        |              |            |  |
|-------------------|------------------------------|------------|-----------|--------|-----------------------|--------|--------------|------------|--|
|                   | Avg. (  / \pi vs. Search-K1) | NQ*        | TriviaQA* | PopQA* | HotpotQA <sup>†</sup> | 2wiki* | Musique*     | Bamboogle* |  |
| Qwen3-8B          |                              |            |           |        |                       |        |              |            |  |
| Search-R1         | 0.395 (-)                    | 0.384      | 0.651     | 0.429  | 0.391                 | 0.386  | 0.143        | 0.380      |  |
| Direct Trajectory | 0.400 (†1.27%)               | 0.406      | 0.657     | 0.433  | 0.376                 | 0.367  | 0.139        | 0.423      |  |
| A-MEM             | 0.403(†2.03%)                | 0.398      | 0.656     | 0.436  | 0.389                 | 0.409  | 0.138        | 0.398      |  |
| EXPEL             | 0.371 (\( \dagger 6.08\% \)  | 0.362      | 0.621     | 0.407  | 0.354                 | 0.375  | 0.121        | 0.357      |  |
| Ours              | 0.408 (†3.29%)               | 0.386      | 0.662     | 0.434  | 0.387                 | 0.403  | 0.152        | 0.435      |  |
| Qwen3-4B          | Qwen3-4B                     |            |           |        |                       |        |              |            |  |
| Search-R1         | 0.375 (-)                    | 0.357      | 0.625     | 0.426  | 0.354                 | 0.402  | 0.115        | 0.348      |  |
| Direct Trajectory | 0.415 (†10.67%)              | 0.403      | 0.624     | 0.434  | 0.420                 | 0.428  | <u>0.186</u> | 0.412      |  |
| A-MEM             | 0.388 (†3.47%)               | 0.393      | 0.603     | 0.439  | 0.385                 | 0.322  | 0.157        | 0.418      |  |
| EXPEL             | 0.337 (\10.13%)              | 0.322      | 0.577     | 0.399  | 0.311                 | 0.363  | 0.081        | 0.305      |  |
| Ours              | 0.426 (†13.60%)              | 0.408      | 0.646     | 0.462  | 0.410                 | 0.407  | 0.189        | 0.463      |  |

**Experimental Analysis: Memory-Guided Reinforcement Learning**. We further evaluated our method by integrating it into RL training process. The detailed training results are in Table 2.

On the <code>Qwen3-8B</code> model, our method achieves the best average performance (0.408), improving upon <code>Search-R1</code> baseline by 3.29%. This shows that our method provides additional benefits even after the model is already optimized with RL. The gains are most notable on challenging out-of-domain datasets like <code>TriviaQA</code> and <code>Bamboogle</code>, suggesting our memory helps the RL agent learn more general reasoning strategies that transfer well to new tasks.

On the smaller <code>Qwen3-4B</code> model, the results are even more impressive. Our method achieves a remarkable 13.60% relative improvement over <code>Search-R1</code>. As seen in our inference experiments, the benefit of our method is especially pronounced on smaller models. Remarkably, our trained <code>Qwen3-4B</code> model (0.426) outperforms the baseline <code>Qwen3-8B</code> model (0.395), demonstrating a significant gain in efficiency.

![](_page_7_Figure_8.jpeg)

Figure 3: (a) Training curve of 4B models. (b) Training curve of 8B models.

In summary, adding our method to inference or

RL training framework significantly boosts QA performance, especially for smaller models. Our structured memory helps the model learn general reasoning skills from the in-domain HotpotQA data and apply them successfully to other datasets. This allows smaller models to match or even exceed the performance of larger ones, offering a path to more efficient and capable models.

## 5.4 ABLATION STUDIES

We conduct ablation studies across three dimensions: (1) disabling memory weight updates (2) varying the number of meta-cognitions used as context and (3) altering the granularity of memory composition (i.e., API call structure).

<span id="page-8-0"></span>![](_page_8_Figure_3.jpeg)

Figure 4: Ablation studies of the structured memory framework. (a) and (b) show the effect of disabling weight optimization. (c) varying the number of meta-cognition k. (d) generalization across LLM backends.

Effect of Disabling Weight Optimization. We first examine the impact of freezing the memory graph weights (i.e., no learning of edge confidence). In this setup, we keep all memory edges at uniform weight and retrieve strategies purely based on structural presence. As shown in figure [4\(](#page-8-0)a)(b), performance drops significantly, particularly on 2WikiMultiHopQA, indicating that learning to prioritize high-utility memory connections is crucial for effective strategy reuse. This validates our reinforcement-based update mechanism, which helps distinguish broadly useful meta-cognitions from less effective or overly specific ones.

Varying the Number of Meta-Cognitions. We further evaluate how the number of retrieved metacognitive strategies (k) affects model performance. Figure [4\(](#page-8-0)c) presents the average accuracy of the 4B model on seven benchmarks as a function of the number of meta-cognitions. Increasing k from 0 (no memory) to 3 leads to steady improvement, as more strategic signals are injected into the prompt. However, further increasing k yields diminishing returns and can even introduce noise due to overlapping or irrelevant strategies. This highlights a trade-off between strategy diversity and clarity, and suggests that a moderate value of k = 3 offers the best balance between guidance and prompt efficiency. The detailed results are shown in Table [3.](#page-16-0)

Generalization across LLMs backends. To evaluate whether our memory construction is tied to a specific LLM API, we replace the original OpenAI gpt-4o model with Gemini-2.5-pro and rerun the downstream evaluation using the same memory graph. As shown in Table [4,](#page-18-1) our memory-augmented approach consistently outperforms its non-memory counterpart even under a different LLM backend, though the absolute numbers differ slightly due to model capability gaps. This demonstrates that our structured memory graph and retrieval-guided prompting strategy are largely *model-agnostic*, enabling plug-and-play use across modern foundation models.

# 6 CONCLUSION

In this paper, we address the dual challenges of inefficient decision-making and poor experience reuse in LLM-based agents. We introduce a trainable, multi-level graph memory framework that structurally encodes historical queries, policy trajectories, and high-level metacognitive strategies. This design facilitates explicit strategy recall and integrates memory into the RL loop to guide and accelerate policy optimization.

Unlike prior works that rely on either implicit optimization or static prompting, our approach unifies explicit memory with dynamic learning. By updating memory weights via RL signals, the framework selectively reinforces high-utility strategies and re-injects them into the agent's training process through prompt augmentation. This mechanism promotes strategic transfer and generalization from past experiences. Our experiments demonstrate that this method not only improves reasoning accuracy at inference time but also accelerates convergence during RL training, ultimately yielding superior final performance and strong generalization across diverse tasks.

# REFERENCES

- <span id="page-9-3"></span>Yuntao Bai, Andy Jones, Kamal Ndousse, Amanda Askell, Anna Chen, Nova DasSarma, Dawn Drain, Stanislav Fort, Deep Ganguli, Tom Henighan, Nicholas Joseph, Saurav Kadavath, Jackson Kernion, Tom Conerly, Sheer El-Showk, Nelson Elhage, Zac Hatfield-Dodds, Danny Hernandez, Tristan Hume, Scott Johnston, Shauna Kravec, Liane Lovitt, Neel Nanda, Catherine Olsson, Dario Amodei, Tom Brown, Jack Clark, Sam McCandlish, Chris Olah, Ben Mann, and Jared Kaplan. Training a helpful and harmless assistant with reinforcement learning from human feedback, 2022. URL <https://arxiv.org/abs/2204.05862>.
- <span id="page-9-1"></span>Jiajun Chai, Guojun Yin, Zekun Xu, Chuhuai Yue, Yi Jia, Siyu Xia, Xiaohan Wang, Jiwen Jiang, Xiaoguang Li, Chengqi Dong, Hang He, and Wei Lin. Rlfactory: A plug-and-play reinforcement learning post-training framework for llm multi-turn tool-use, 2025. URL [https://arxiv.](https://arxiv.org/abs/2509.06980) [org/abs/2509.06980](https://arxiv.org/abs/2509.06980).
- <span id="page-9-4"></span>Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, and Deshraj Yadav. Mem0: Building production-ready ai agents with scalable long-term memory, 2025. URL [https://arxiv.](https://arxiv.org/abs/2504.19413) [org/abs/2504.19413](https://arxiv.org/abs/2504.19413).
- <span id="page-9-7"></span>Jiazhan Feng, Shijue Huang, Xingwei Qu, Ge Zhang, Yujia Qin, Baoquan Zhong, Chengquan Jiang, Jinxin Chi, and Wanjun Zhong. Retool: Reinforcement learning for strategic tool use in llms, 2025. URL <https://arxiv.org/abs/2504.11536>.
- <span id="page-9-0"></span>Leo Gao, Angela Beese, Max Fischer, Lariah Hou, Julia Kreutzer, Xi Victoria Lin, Jason Phang Wang, Luke Zettlemoyer, and Emiel van Miltenburg. Toolformer: Language models can teach themselves to use tools. *arXiv preprint arXiv:2302.04761*, 2023.
- <span id="page-9-11"></span>Chia-Hsuan Ho, Shu-Hung Yeh, and Yun-Nung Chen. Constructing a multi-hop qa dataset via graph-based node ranking. In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 6151–6161, 2020.
- <span id="page-9-6"></span>Bowen Jin, Hansi Zeng, Zhenrui Yue, Jinsung Yoon, Sercan Arik, Dong Wang, Hamed Zamani, and Jiawei Han. Search-r1: Training llms to reason and leverage search engines with reinforcement learning, 2025. URL <https://arxiv.org/abs/2503.09516>.
- <span id="page-9-10"></span>Mandar Joshi, Eunsol Choi, Daniel Weld, and Luke Zettlemoyer. Triviaqa: A large scale distantly supervised challenge dataset for reading comprehension. *arXiv preprint arXiv:1705.03551*, 2017.
- <span id="page-9-12"></span>Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi ˘ Chen, and Wen tau Yih. Dense passage retrieval for open-domain question answering, 2020. URL <https://arxiv.org/abs/2004.04906>.
- <span id="page-9-9"></span>Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur P Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Jacob Devlin, Kenton Lee, et al. Natural questions: a benchmark for question answering research. *Transactions of the Association for Computational Linguistics*, 2019.
- <span id="page-9-5"></span>Xiaoxi Li, Guanting Dong, Jiajie Jin, Yuyao Zhang, Yujia Zhou, Yutao Zhu, Peitian Zhang, and Zhicheng Dou. Search-o1: Agentic search-enhanced large reasoning models, 2025a. URL <https://arxiv.org/abs/2501.05366>.
- <span id="page-9-2"></span>Zhiyu Li, Shichao Song, Chenyang Xi, Hanyu Wang, Chen Tang, Simin Niu, Ding Chen, Jiawei Yang, Chunyu Li, Qingchen Yu, Jihao Zhao, Yezhaohui Wang, Peng Liu, Zehao Lin, Pengyuan Wang, Jiahao Huo, Tianyi Chen, Kai Chen, Kehang Li, Zhen Tao, Huayi Lai, Hao Wu, Bo Tang, Zhenren Wang, Zhaoxin Fan, Ningyu Zhang, Linfeng Zhang, Junchi Yan, Mingchuan Yang, Tong Xu, Wei Xu, Huajun Chen, Haofen Wang, Hongkang Yang, Wentao Zhang, Zhi-Qin John Xu, Siheng Chen, and Feiyu Xiong. Memos: A memory os for ai system, 2025b. URL [https:](https://arxiv.org/abs/2507.03724) [//arxiv.org/abs/2507.03724](https://arxiv.org/abs/2507.03724).
- <span id="page-9-8"></span>Hao Liu, Zhengren Wang, Xi Chen, Zhiyu Li, Feiyu Xiong, Qinhan Yu, and Wentao Zhang. Hoprag: Multi-hop reasoning for logic-aware retrieval-augmented generation, 2025. URL [https://](https://arxiv.org/abs/2502.12442) [arxiv.org/abs/2502.12442](https://arxiv.org/abs/2502.12442).

- <span id="page-10-10"></span>Eugene Mallen, Patrick Lewis, Semih Yavuz, Raymond Ng, Sebastian Riedel, Dhruvesh Sridhar, and Fabio Petroni. Popqa: Open-domain qa with popular questions. In *Findings of the Association for Computational Linguistics: EMNLP 2022*, 2022.
- <span id="page-10-2"></span>Reiichiro Nakano, Jacob Hilton, Suchir Balaji, and et al. Webgpt: Browser-assisted question answering with human feedback. *arXiv preprint arXiv:2112.09332*, 2021.
- <span id="page-10-8"></span>Bo Pan and Liang Zhao. Can past experience accelerate llm reasoning?, 2025. URL [https:](https://arxiv.org/abs/2505.20643) [//arxiv.org/abs/2505.20643](https://arxiv.org/abs/2505.20643).
- <span id="page-10-13"></span>Ofir Press, Daniel Khashabi, Ashish Sabharwal, and Tushar Khot. Measuring and narrowing the compositionality gap in language models. In *Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing*, 2022.
- <span id="page-10-6"></span>Cheng Qian, Emre Can Acikgoz, Qi He, Hongru Wang, Xiusi Chen, Dilek Hakkani-Tur, Gokhan ¨ Tur, and Heng Ji. Toolrl: Reward is all tool learning needs, 2025. URL [https://arxiv.](https://arxiv.org/abs/2504.13958) [org/abs/2504.13958](https://arxiv.org/abs/2504.13958).
- <span id="page-10-7"></span>Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, and Daniel Chalef. Zep: A temporal knowledge graph architecture for agent memory, 2025. URL [https://arxiv.org/](https://arxiv.org/abs/2501.13956) [abs/2501.13956](https://arxiv.org/abs/2501.13956).
- <span id="page-10-0"></span>Arjun Singh, Zhe Xiang, Dongheon Kim, Michael Ahn, Jesse Thomason, and Julie Shah. Progprompt: Generating situated robot task plans using large language models. *arXiv preprint arXiv:2305.15343*, 2023.
- <span id="page-10-4"></span>Huatong Song, Jinhao Jiang, Yingqian Min, Jie Chen, Zhipeng Chen, Wayne Xin Zhao, Lei Fang, and Ji-Rong Wen. R1-searcher: Incentivizing the search capability in llms via reinforcement learning, 2025. URL <https://arxiv.org/abs/2503.05592>.
- <span id="page-10-3"></span>Hao Sun, Zile Qiao, Jiayan Guo, Xuanbo Fan, Yingyan Hou, Yong Jiang, Pengjun Xie, Yan Zhang, Fei Huang, and Jingren Zhou. Zerosearch: Incentivize the search capability of llms without searching, 2025. URL <https://arxiv.org/abs/2505.04588>.
- <span id="page-10-12"></span>Harsh Trivedi, Daniel Khashabi, Tushar Khot, Ashish Sabharwal, and Dan Roth. Musique: Multihop questions via single-hop question composition. In *Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics*, 2022.
- <span id="page-10-5"></span>Hongru Wang, Cheng Qian, Wanjun Zhong, Xiusi Chen, Jiahao Qiu, Shijue Huang, Bowen Jin, Mengdi Wang, Kam-Fai Wong, and Heng Ji. Acting less is reasoning more! teaching model to act efficiently, 2025. URL <https://arxiv.org/abs/2504.14870>.
- <span id="page-10-15"></span>Liang Wang, Nan Yang, Xiaolong Huang, Binxing Jiao, Linjun Yang, Daxin Jiang, Rangan Majumder, and Furu Wei. Text embeddings by weakly-supervised contrastive pre-training, 2024. URL <https://arxiv.org/abs/2212.03533>.
- <span id="page-10-14"></span>Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Fei Xia, Ed Chi, Quoc V Le, Denny Zhou, et al. Chain-of-thought prompting elicits reasoning in large language models. *Advances in neural information processing systems*, 35:24824–24837, 2022.
- <span id="page-10-9"></span>Zidi Xiong, Yuping Lin, Wenya Xie, Pengfei He, Jiliang Tang, Himabindu Lakkaraju, and Zhen Xiang. How memory management impacts llm agents: An empirical study of experience-following behavior, 2025. URL <https://arxiv.org/abs/2505.16067>.
- <span id="page-10-1"></span>Wujiang Xu, Kai Mei, Hang Gao, Juntao Tan, Zujie Liang, and Yongfeng Zhang. A-mem: Agentic memory for llm agents, 2025. URL <https://arxiv.org/abs/2502.12110>.
- <span id="page-10-11"></span>Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W Cohen, Ruslan Salakhutdinov, and Christopher D Manning. Hotpotqa: A dataset for diverse, explainable multi-hop question answering. In *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing*, pp. 2369–2380, 2018.

- <span id="page-11-0"></span>Shinn Yao, Jeffrey Zhao, Dian Yu, Hyung Won Chung, Jaybos Chen, Karthik Narasimhan, and et al. React: Synergizing reasoning and acting in language models. *arXiv preprint arXiv:2210.03629*, 2022.
- <span id="page-11-5"></span>Hongli Yu, Tinghong Chen, Jiangtao Feng, Jiangjie Chen, Weinan Dai, Qiying Yu, Ya-Qin Zhang, Wei-Ying Ma, Jingjing Liu, Mingxuan Wang, and Hao Zhou. Memagent: Reshaping long-context llm with multi-conv rl-based memory agent, 2025. URL [https://arxiv.org/abs/2507.](https://arxiv.org/abs/2507.02259) [02259](https://arxiv.org/abs/2507.02259).
- <span id="page-11-7"></span>Chuxu Zhang, Dongjin Song, Chao Huang, Ananthram Swami, and Nitesh V Chawla. Heterogeneous graph neural network. In *Proceedings of the 25th ACM SIGKDD international conference on knowledge discovery & data mining*, pp. 793–803, 2019.
- <span id="page-11-6"></span>Guibin Zhang, Muxin Fu, Guancheng Wan, Miao Yu, Kun Wang, and Shuicheng Yan. G-memory: Tracing hierarchical memory for multi-agent systems, 2025. URL [https://arxiv.org/](https://arxiv.org/abs/2506.07398) [abs/2506.07398](https://arxiv.org/abs/2506.07398).
- <span id="page-11-3"></span>Shinn Zhang, Eric Wu, Frank Xu, Stuart Russell, and Dragomir Radev. Reflexion: Language agents with verbal reinforcement learning. *arXiv preprint arXiv:2303.11366*, 2023.
- <span id="page-11-1"></span>Andrew Zhao, Daniel Huang, Quentin Xu, Matthieu Lin, Yong-Jin Liu, and Gao Huang. Expel: Llm agents are experiential learners, 2024. URL <https://arxiv.org/abs/2308.10144>.
- <span id="page-11-2"></span>Yuxiang Zheng, Dayuan Fu, Xiangkun Hu, Xiaojie Cai, Lyumanshan Ye, Pengrui Lu, and Pengfei Liu. Deepresearcher: Scaling deep research via reinforcement learning in real-world environments, 2025. URL <https://arxiv.org/abs/2504.03160>.
- <span id="page-11-4"></span>Zijian Zhou, Ao Qu, Zhaoxuan Wu, Sunghwan Kim, Alok Prakash, Daniela Rus, Jinhua Zhao, Bryan Kian Hsiang Low, and Paul Pu Liang. Mem1: Learning to synergize memory and reasoning for efficient long-horizon agents, 2025. URL <https://arxiv.org/abs/2506.15841>.

# A EXPERIMENTAL SETUP DETAILS

## <span id="page-11-9"></span>A.1 MULTI-TURN TOOL-INTERGRATED QA

When tackling QA benchmarks, we observe that incorporating external knowledge retrieval plays a crucial role in enhancing answer accuracy. To this end, we utilize the 2018 Wikipedia dump as our external knowledge base and adopt the E5 retriever for efficient document retrieval. Within our framework, the entire retrieval process is encapsulated as a modular MCP tool, which the LLM can invoke autonomously based on its reasoning needs.

Specifically, the Qwen3 model follows a structured interaction protocol in which reasoning and planning are carried out between <think> and </think> tags,tool invocation commands are embedded within <tool call> and </tool call>, and the corresponding outputs are captured between <tool response> and </tool response>. The model engages in multiple rounds of tool interaction until it either generates a final answer enclosed in <answer></answer> or reaches the maximum limit of tool invocations, which is set to six in our experiments. A concrete case study is presented in the following table to illustrate how this structured retrieval mechanism enables the model to access external knowledge and perform informed reasoning.

The table [E.1p](#page-18-2)resents a representative prompt designed to encourage tool usage, along with a concrete case study [A.1d](#page-11-9)emonstrating how the model leverages structured tool interactions to retrieve external knowledge and perform reasoning.

## <span id="page-11-8"></span>A.2 EXPERIMENTAL SETTINGS

Direct Inference Baselines. We compare our method against the following direct inference baselines:Direct Inference + Chain-of-Thought (CoT) [\(Wei et al., 2022\)](#page-10-14) performs reasoning solely through its internal chain of thought. TIR (Tool-Integrated Reasoning) [\(Chai et al., 2025\)](#page-9-1) enhances inference by retrieving documents using integrated search tools. For Reasoning with Memory, we compare with three variants: (1) Direct Trajectory, which uses past trajectories directly

## Case 1: Example Response with Tool-Integrated Reasoning halign title

response:<think> Okay, let's tackle this question. The user is asking which U.S. state was historically dominated by the Republican party from 1860 to 1932 and is represented by State Senator George D. Maziarz.

First, I need to figure out the state in question. The key points here are the time period (1860-1932) and the Republican dominance. I remember that during the 19th century, the Republican Party was a major political force, especially after the Civil War. States like Ohio, New York, and Pennsylvania were known for their Republican strongholds. However, I'm not entirely sure which one fits the specific time frame mentioned.

Next, the mention of State Senator George D. Maziarz. I need to check if this senator is from a state that fits the historical Republican dominance. But I don't recall specific information about George D. Maziarz. Maybe I should look up his state of origin. However, since I can't access external resources right now, I need to rely on my existing knowledge.

```
... </think>
<tool_call>
{"name": "search-query_rag",
"arguments": {"query": "George D. Maziarz state", "topk": 3}}
</tool_call>}
<tool response> Execute the tool search-query rag successed - The args are: 'query':
'George D. Maziarz state', 'topk': 3 - The result is:...... </tool response>
<answer>New York</answer>
```

as memory; (2) A-MEM [\(Xu et al., 2025\)](#page-10-1), which maintains a dynamic memory graph; and (3) Expel [\(Zhao et al., 2024\)](#page-11-1), which extracts high-level strategic insights from past experiences.

Reinforcement Learning Baselines. For RL training, we evaluate two groups of baselines: Search-R1: [\(Jin et al., 2025\)](#page-9-6) A reinforcement learning agent that relies solely on multi-turn tool invocation without any memory support. RL with Memory Variants: We examine the performance of agents equipped with the three memory types described above—Direct Trajectory, A-MEM, and Expel Memory—to assess how different memory designs impact training efficiency and overall performance.

We conduct experiments with two model scales, Qwen-3-4B and Qwen-3-8B. For the retrieval component, we adopt the 2018 Wikipedia dump [\(Karpukhin et al., 2020\)](#page-9-12) as the knowledge source and employ the E5 [\(Wang et al., 2024\)](#page-10-15) retriever.

We exclusively use the HotpotQA dataset, both for model optimization and for constructing memory during the memory formation process. Evaluation is then carried out on the test or validation sets of seven diverse datasets, enabling assessment of performance both within the training domain and in out-of-domain settings. We report Exact Match (EM) as the primary evaluation metric. And for memory construction in A-Mem [\(Xu et al., 2025\)](#page-10-1), Expel [\(Zhao et al., 2024\)](#page-11-1), and our proposed method, where a high-capability large language model is required, we utilized GPT-4o.

We conduct experiments on seven datasets, where HotpotQA is selected as the in-domain test set, while the remaining six datasets are used for out-of-domain evaluation. From the HotpotQA training set, we sample 1,000 examples to construct the memory and an additional 5,000 examples for weight training.

During the RL training phase, we use the rest of the HotpotQA training set as the training corpus. We adopt a batch size of 512 with a micro batch size of 64, and the rollout sampling is performed with a temperature of 1.0. To accelerate the rollout process of the LLM, we deploy vLLM v1 with a tensor parallel size of 1.

Specifically for the GRPO algorithm, the number of rollout samples (n) is set to 8. All experiments are conducted on a cluster of 8 NVIDIA A100 GPUs.

# B MEMORY GRAPH CONSTRUCTION

The pseudo-code for the overall process of the graph, which is composed of the specific paths of LLM models, is as shown in the algorithm [1;](#page-14-0)

## <span id="page-13-0"></span>B.1 THE CONSTRUCTION OF PATH IN FINITE STATE MACHINE

First, to formalize the agent's decision-making process during tool invocation, we construct a Finite State Machine , the overall architecture of which is depicted in Figure [5.](#page-15-0) The states within this FSM are designed to encapsulate the critical cognitive junctures an LLM agent encounters, representing a synthesis of its internal knowledge and available external information. This design serves as a generalized abstraction of the agent's decision pathway, ensuring high generalizability across diverse tasks.

We first have a Qwen3 series model produce a concrete answer to the query. Subsequently, to map an agent's raw execution trajectory—the specific sequence of reasoning and tool calls—onto a canonical path within the FSM, we leverage a powerful large language model, see Table [E.2](#page-18-3) for the full prompt and the table [B.1p](#page-15-0)resents a specific case of Finite State Machine.

## Case 2: A example of Finite State Machine

Illustrative Decision Path. The following sequence illustrates a canonical decision path encoded within our framework:

Start → CorrectGoalEstablished → KnowledgeUncertainGap

- → StrategyPlanning → SequentialDependentPlanning
  - → ToolExecution → InformationAnalysis
  - → KnowledgeAligned → DecisionMaking
  - → InsufficientInformation → AssumptionBasedReasoning
  - → AnswerGeneration → WrongAnswer
- → DiagnosisHub → InternalKnowledgeConflict → End

This path represents a chain of cognitive states traversed by the agent. It begins with goal establishment, proceeds through planning and execution, encounters a knowledge gap leading to flawed reasoning, and concludes with self-diagnosis. By encoding such trajectories as nodes in the transition path layer, the graph provides a structured and abstract representation of a complex reasoning process, which can be analyzed, compared, and learned from.

# B.2 META-COGNITION CONSTRUCTION

The detailed descriptions of each type of node in the memory are as follows:

- Query Layer Q: Each node q<sup>i</sup> ∈ Q represents a specific task instance, such as a userissued query. It encapsulates the entirety of an interaction, including the initial input, the agent's generated output, the complete execution trajectory, and a resultant outcome label (e.g., success or failure).
- Transition Path Layer T : Each node t<sup>j</sup> ∈ T corresponds to a standardized decisionmaking pathway. These pathways are grounded in a predefined finite state machine (FSM) S, representing a canonical sequence of the agent's states and actions. This layer abstracts away instance-specific details to reveal underlying behavioral patterns.
- Meta-Cognition Layer M: Each node m<sup>k</sup> ∈ M encodes a high-level, human-readable strategic principle. These principles are distilled from a comparative analysis of successful and failed transition paths, representing generalized heuristics for effective problemsolving.

The induction of meta-cognitions is accomplished through three primary analytical scenarios, each facilitated by a dedicated prompt:

## <span id="page-14-0"></span>Algorithm 1 Hierarchical Memory Graph Construction and Update

```
1: Input: Memory Graph G, new query qi
                                , policy π, FSM S, sample count N, similarity threshold
   K.
2: Ensure: Updated Memory Graph G
                             ′
                              .
3: procedure UPDATEMEMORYGRAPH(G, qi
                                   , π, S, N, K)
4: Ts ← ∅, Tf ← ∅ ▷ Initialize sets for successful and failed paths
5: G ← AddNode(G, qi) ▷ Add current query to the graph
6: for n = 1 to N do ▷ Sample N trajectories from the policy
7: τn ← SampleRollout(π, qi)
8: tn ← GroundTrajectoryToPath(τn, S) ▷ Map trajectory to a canonical FSM path
9: G ← AddNode(G, tn)
10: G ← AddEdge(G, qi
                       , tn)
11: if IsSuccess(τn) then
12: Ts ← Ts ∪ {tn}
13: else
14: Tf ← Tf ∪ {tn}
15: end if
16: end for
17: Mnew ← InduceMetaCognition(qi
                               , Ts, Tf , G, K) ▷ Derive new strategic principles
18: for each new meta-cognition m in Mnew do
19: mexist ← FindMatchingMetaCognition(m, G)
20: if mexist is null then
21: mf inal ← CreateNewMetaCognitionNode(m)
22: G ← AddNode(G, mf inal)
23: else
24: UpdateConfidence(mexist)
25: mf inal ← mexist
26: end if
27: for each path t that generated m do ▷ Link paths to the principles they support
28: G ← AddEdge(G, t, mf inal)
29: end for
30: end for
31: return G
32: end procedure
33: procedure INDUCEMETACOGNITION(qi
                                 , Ts, Tf , G, K)
34: if Ts ̸= ∅ and Tf ̸= ∅ then ▷ Case 1: High-confidence induction
35: ts ← SelectOne(Ts), tf ← SelectOne(Tf )
36: m ← ContrastPaths(ts, tf ) ▷ e.g., find first diverging decision
37: return {m}
38: else if Ts = ∅ and Tf ̸= ∅ then ▷ Case 2: Speculative induction
39: Mspec ← ∅
40: Qsim ← FindSimilarQueries(qi
                                , G, K) ▷ Based on embedding similarity
41: for each similar query qj in Qsim do
42: for each successful path tj of qj do
43: Mspec ← Mspec ∪ GetMetaCognitionsFromPath(tj , G)
44: end for
45: end for
46: return Mspec
47: else
48: return ∅ ▷ No new insights if only successes or no rollouts
49: end if
50: end procedure
```

<span id="page-15-0"></span>![](_page_15_Figure_1.jpeg)

Figure 5: Finite State Machine

Intra-Query Analysis: This involves comparing successful and failed trajectories that originate from the identical query to distill a high-confidence causal principle. The prompt for this process is presented in [E.3.](#page-18-0)

Inter-Query Analysis: This contrasts a failed trajectory with successful ones from semantically similar but distinct queries to generate speculative heuristics.

Positive Example Distillation: This process extracts generalizable strategies exclusively from a collection of successful execution paths.

# C EXPERIMENT ANALYSIS

## C.1 THE NUMBER OF THE META-COGNITION

To better understand how the quantity of retrieved meta-cognitive strategies affects agent performance, we evaluate four configurations: using 0 (no memory, denoted as ITR), 1, 3, and 5 strategies as contextual input. Results across seven QA benchmarks are presented in Table [3.](#page-16-0)

We observe that introducing even a single meta-cognitive strategy leads to a notable improvement over the baseline (ITR), especially on multi-hop tasks such as Bamboogle (+11.6%) and HotpotQA (+2.9%). This suggests that explicit strategic signals can substantially aid reasoning even in limited quantities. As the number of strategies increases, performance generally improves, but the marginal gains become smaller—likely due to redundancy or prompt saturation. The best overall result is achieved at top k=5, which balances diversity and relevance.

These findings imply that a moderate number of well-curated strategies can enhance generalization and decision quality, without incurring the risks of prompt overload or noise from irrelevant memories.

<span id="page-16-0"></span>

| Methods     | General QA |           |        |           |        |          |            |       |
|-------------|------------|-----------|--------|-----------|--------|----------|------------|-------|
|             | NQ⋆        | TriviaQA⋆ | PopQA⋆ | HotpotQA† | 2wiki⋆ | Musique⋆ | Bamboogle⋆ | Avg.  |
| Qwen3-4B    |            |           |        |           |        |          |            |       |
| ITR         | 0.298      | 0.581     | 0.157  | 0.268     | 0.281  | 0.077    | 0.290      | 0.279 |
| = 1<br>topk | 0.326      | 0.583     | 0.382  | 0.290     | 0.327  | 0.096    | 0.406      | 0.344 |
| = 3<br>topk | 0.335      | 0.596     | 0.393  | 0.299     | 0.347  | 0.099    | 0.391      | 0.351 |
| = 5<br>topk | 0.333      | 0.594     | 0.392  | 0.299     | 0.349  | 0.094    | 0.418      | 0.355 |

Table 3: Performance of different numbers of meta-cognition.

## C.2 CROSS-API MEMORY ROBUSTNESS

To further validate the portability and reliability of our structured memory graph, we construct the memory using two distinct LLM APIs: gpt-4o and Gemini-2.5-pro. These memory graphs are then integrated into the same downstream agent architecture (Qwen3-4B and Qwen3-8B), and evaluated across seven QA datasets. As shown in Table [4,](#page-18-1) the resulting performance differences are minor, with Gemini-based memory slightly outperforming its 4o counterpart in most cases.

Specifically, on the multi-hop benchmark Bamboogle, the Gemini-constructed memory shows a notable increase (e.g., +0.043 on Qwen3-8B), while maintaining parity or marginal gains in general QA datasets like TriviaQA and PopQA. These results indicate that while different APIs may introduce slight variations in strategy abstraction, our framework is robust to such differences and maintains high effectiveness regardless of the underlying model used to generate the memory.

# <span id="page-16-1"></span>D CASE STUDIES

This case [Di](#page-16-1)llustrates how the integration of meta-cognitive strategies enhances factual precision. Without meta-cognition, the agent returns a partially correct but under-specified answer ("National Security Law"). With meta-cognition, the agent engages in structured validation and corrects the response to the fully grounded and jurisdiction-specific "Macau National Security Law", aligning

## Algorithm 2 Trainable Graph Weight Optimization via Policy Gradient

```
1: Input: Memory Graph \mathcal{G} with initial weights w, Training Queries \mathcal{D}, Agent model, Reward
      function \mathcal{R}, learning rate \alpha.
 2: Output: Optimized Memory Graph \mathcal{G} with updated weights \mathbf{w}^*.
 3: procedure OPTIMIZEGRAPHWEIGHTS(\mathcal{G}, \mathcal{D}, \alpha)
           for each query q_{\text{new}} in \mathcal{D} do
 5:
                                                                                ⊳ — Step 1: Stochastic Guidance Selection —
 6:
                 m_k, p(m_k \mid q_{\text{new}}) \leftarrow \text{SelectGuidingMetaCognition}(\mathcal{G}, q_{\text{new}})
 7:
                 if m_k is null then
                                                                                                         No relevant guidance found
                       continue
 8:
 9:
                 end if
10:
                                                                                      ⊳ — Step 2: Counterfactual Evaluation —
                 Response<sub>with</sub> \leftarrow Agent.generate(q_{\text{new}}, \text{guidance} = m_k)
11:
12:
                  R_{\text{with}} \leftarrow \mathcal{R}(\text{Response}_{\text{with}}, q_{\text{new}})
                  Response_{w/o} \leftarrow Agent.generate(q_{new}, guidance = null)
13:
                 R_{\text{w/o}} \leftarrow \mathcal{R}(\text{Response}_{\text{w/o}}, q_{\text{new}})
14:
                  \Delta R_k \leftarrow R_{\text{with}} - R_{\text{w/o}}

    ▷ Calculate reward gap (utility signal)

15:
16:

                 \nabla_{\mathbf{w}} \mathcal{L} \leftarrow -\Delta R_k \cdot \nabla_{\mathbf{w}} \log p(m_k \mid q_{\text{new}})\mathbf{w} \leftarrow \mathbf{w} - \alpha \cdot \nabla_{\mathbf{w}} \mathcal{L}
17:

                                                                                                   ▶ Update all contributing weights
18:
19:
           end for
           return \mathcal{G}
20:
21: end procedure
22: procedure SelectGuidingMetaCognition(\mathcal{G}, q_{\text{new}})
23:
                                                               ▶ Activate relevant subgraph based on semantic similarity
           \mathcal{M}_{\text{act}} \leftarrow \text{ActivateSubgraph}(q_{\text{new}}, \mathcal{G})
24:
25:
           if \mathcal{M}_{act} is empty then
                 return null, 0
26:
27:
           end if
28:

    Compute relevance scores for all activated meta-cognitions

29:
           for all m \in \mathcal{M}_{act} do
30:
                  S(m \mid q_{\text{new}}) \leftarrow 0
31:
                  for all path q_i 	o t_j 	o m in {\mathcal G} do
32:
                       if q_i is in activated subgraph then
                             S(m \mid q_{\text{new}}) \leftarrow S(m \mid q_{\text{new}}) + \text{Sim}(q_{\text{new}}, q_i) \cdot w_{at}^{(i,j)} \cdot w_{tm}^{(j,m)}
33:
34:
                       end if
                 end for
35:
           end for
36:
37:

           \begin{array}{l} Z \leftarrow \sum_{m' \in \mathcal{M}_{\text{act}}} \exp(S(m' \mid q_{\text{new}})) \\ \textbf{for all } m \in \mathcal{M}_{\text{act}} \ \textbf{do} \end{array}
38:
39:
40:
                 p(m \mid q_{\text{new}}) \leftarrow \exp(S(m \mid q_{\text{new}}))/Z
41:
           end for
42:
                                                     > Stochastically sample a meta-cognition based on probabilities
43:
           m_k \leftarrow \text{Sample}(\mathcal{M}_{\text{act}}, \text{probabilities} = \{p(m \mid q_{\text{new}})\})
44:
           return m_k, p(m_k \mid q_{\text{new}})
45: end procedure
```

<span id="page-18-1"></span>

| Methods      | General QA |           |        |           | Avg.   |          |            |       |
|--------------|------------|-----------|--------|-----------|--------|----------|------------|-------|
|              | NQ⋆        | TriviaQA⋆ | PopQA⋆ | HotpotQA† | 2wiki⋆ | Musique⋆ | Bamboogle⋆ |       |
| Qwen3-8B     |            |           |        |           |        |          |            |       |
| Ours(4o)     | 0.316      | 0.622     | 0.382  | 0.358     | 0.354  | 0.128    | 0.392      | 0.365 |
| Ours(gemini) | 0.318      | 0.621     | 0.385  | 0.362     | 0.336  | 0.123    | 0.434      | 0.369 |
| Qwen3-4B     |            |           |        |           |        |          |            |       |
| Ours(4o)     | 0.335      | 0.596     | 0.393  | 0.299     | 0.347  | 0.099    | 0.391      | 0.351 |
| Ours(gemini) | 0.337      | 0.598     | 0.396  | 0.314     | 0.360  | 0.093    | 0.397      | 0.357 |

exactly with the ground truth. This aligns with our design goal: equipping agents with self-checking mechanisms that reduce synthesis ambiguity, particularly when internal confidence is high but error risk remains.

## Case 3: Correcting Answer via Meta-Cognition

Query: *Hong Kong Macau cultural exchange was a trip that tested which law whose purpose was to fulfil Article 23 of the Macau Basic Law?*

Ground Truth: Macau National Security Law

Meta-Cognition: *Early recognition and affirmation of the 'KnowledgeSufficient' state can help prevent synthesis inaccuracies in scenarios where internal confidence is prone to challenges. Structured validation strategies ensure precise answer formulation when internal knowledge seems sufficient but risks synthesis errors.*

## Response (w/o meta-cognition):

*... Therefore, the answer should state that the law tested was the National Security Law, aimed at fulfilling Article 23.* → Final Answer: National Security Law

## Response (with meta-cognition):

*... That law is likely the Macau National Security Law, which was enacted in 2009... The answer should be the Macau National Security Law.* → Final Answer: Macau National Security Law

# E PROMPT TEMPLATES

## <span id="page-18-2"></span>E.1 MULTI-TURN TOOL-INTERGRATED QA PROMPT

When LLMs needs to interact with tools multiple times to answer a question, it is necessary to guide the LLM on which tools to use and how to use them. The specific prompt is as follows.

## <span id="page-18-3"></span>E.2 CONSTRUCTING FSM PATH

Given the specific response path of the LLM and the complete structure of the state machine, we employ an LLM (e.g., GPT-4o) to map the generated answer onto one of the predefined paths in the state machine. The following shows the exact prompt used.

## <span id="page-18-0"></span>E.3 META-COGNITION CONSTRUCTING

With both successful and failed state-machine paths available, we derive high-level meta-cognitions by contrasting the two. The following prompt illustrates how a pair of successful and failed paths under the same query is used to induce meta-cognition.

## Prompt A: System and User Prompt

# SYSTEM PROMPT: # Tools You may call one or more functions to assist with the user query. You are provided with function signatures within <tools></tools> XML tags: <tools> { "name": "search-query\_rag", "description": "MCP RAG Query Tool (Synchronous Version) Args: query: query text topk: The default number of documents returned is 3 Returns: str: The formatted query result", "parameters": { "type": "object", "properties": { "query": {"title": "Query", "type": "string"}, "topk": {"default": 3, "title": "Topk", "type": "integer"} }, "required": ["query"] } } </tools> # Tool call format For each function call, return a JSON object with function name and arguments within <tool\_call></tool\_call> XML tags: <tool\_call> { "name": <function-name>, "arguments": <args-json-object> } </tool\_call> USER PROMPT: Answer the given question. After reasoning, if you find you lack some knowledge, you can call the search tool. You may search as many times as you want. If you find no further external knowledge is needed, you can directly provide the answer inside <answer> and </answer>, without detailed illustrations. For example: <answer> Beijing </answer>. Question: Which US State, historically dominated by the Republican party from 1860 to 1932, is represented by State Senator George D. Maziarz?

## Prompt B: Prompt for constructing FSM path

Instruction: You are a metacognition analysis expert specialized in extracting *generalized decision principles and guidance strategies* from state machine execution paths.

State machine transition rules: {transitions info} Core Requirements:

- 1. Generalizability Focus: Output strategies and principles must be general, applicable to similar problems, without specific query details.
- 2. Direct Usability: Generated content should be directly usable as guidance principles for new problems.
- 3. Principled Expression: Use cautious guidance terms like "consider", "may help", "tends to" rather than definitive statements.
- 4. Concise Effectiveness: Output only the most core insights, avoid redundancy and complexity.
- 5. Quality Control: Strictly evaluate whether there is sufficient evidence to support new metacognition.
- 6. Knowledge Confidence Awareness: Recognize that LLM's internal knowledge confidence varies across queries — success patterns may be domain-specific.
- 7. Uncertainty Acknowledgment: Express appropriate uncertainty in guidance principles, avoiding overly definitive conclusions.
- 8. Quantity Management: When metacognition count exceeds 30, prioritize updating low-confidence existing metacognitions.

## Output Format (Quantity-Aware):

Your output must be a JSON object with the following structure:

```
{
  "decision": "update" or "create" or "skip",
  "target_meta_id": <ID of metacognition to update (only when
     decision is "update")>,
  "reasoning": "Brief explanation including quantity management when
      count > 30.",
  "meta_cognition": {
    "summary": "Concise general guidance summary (use cautious
        language).",
    "strategy_principles": [
      {
        "principle": "...",
        "confidence": "high" | "medium" | "low",
        "confidence_score": 30 - 85
      },
      ...
    ],
    "overall_confidence": "high" | "medium" | "low",
    "evidence_paths": <int>,
    "uncertainty_note": "Brief acknowledgment of limitations or
        knowledge-dependency concerns."
  }
}
```

## Prompt C: Metacognition Prompt Specification

State machine transition rules: {transitions info}

## Core Requirements:

- 1. Generalizability Focus: Output strategies and principles must be general, applicable to similar problems, without specific query details.
- 2. Direct Usability: Generated content should be directly usable as guidance principles for new problems.
- 3. Principled Expression: Use cautious guidance terms like "consider", "may help", "tends to" rather than definitive statements.
- 4. Concise Effectiveness: Output only the most core insights, avoid redundancy and complexity.
- 5. Quality Control: Strictly evaluate whether there is sufficient evidence to support new metacognition.
- 6. Knowledge Confidence Awareness: Recognize that LLM's internal knowledge confidence varies across queries—success patterns may be domain-specific.
- 7. Uncertainty Acknowledgment: Express appropriate uncertainty in guidance principles, avoiding overly definitive conclusions.
- 8. Quantity Management: When metacognition count exceeds 30, prioritize updating low-confidence existing metacognitions.

## Critical Self-Reflection Requirements:

- Pattern Validity: Question whether identified patterns truly represent generalizable principles.
- Knowledge Dependency: Consider if success stems from strategy effectiveness or the LLM's domain familiarity.
- Evidence Sufficiency: Demand higher evidence standards for strategies that could mislead future queries.
- Simplicity Over Complexity: Favor simple, robust principles over complex, brittle ones.

# Metacognition Quantity Control Strategy:

When metacognition count ≤ 30: • Normal decision making: create, update, or skip based on evidence quality.

- Prefer creating new metacognition when patterns are sufficiently distinct.
- Express appropriate uncertainty in new metacognitions.

## When metacognition count > 30: • Strongly prefer UPDATE over CREATE: Prioritize improving existing low-confidence metacognitions.

- Only create new metacognition if the pattern is exceptionally valuable and completely distinct.
- Target metacognitions with confidence levels "low" or "medium" for updates.

## Analysis Focus:

- 1. Success Pattern Identification: Abstract reusable decision patterns from successful paths.
- 2. Failure Cause Summary: Identify generalizable errors to avoid from failed paths.
- 3. State Transition Optimization: Extract best practice principles for state machine execution.
- 4. Knowledge Dependency Assessment: Evaluate whether patterns might be specific to certain knowledge domains.

5. Existing Knowledge Enhancement: When quantity is high, focus on strengthening weak metacognitions.

## Decision Options:

- create: Create new metacognition (when discovering valuable and distinct patterns, or when quantity ≤ 30).
- update: Update existing metacognition (preferred when quantity > 30, especially targeting low-confidence ones).
- skip: Skip metacognition operation (when evidence is insufficient or has no new value).

## Skip Metacognition Situations:

- Path data quality is poor, patterns are unclear.
- Existing metacognition already covers the pattern, new evidence shows no significant improvement.
- Success/failure path differences are not obvious, difficult to extract effective strategies.
- Cannot distinguish whether success stems from strategy effectiveness or knowledge domain familiarity.
- When quantity > 30 and no suitable low-confidence metacognition found for update.

## Output Format (Quantity-Aware): Your output must be a JSON object containing:

```
{
  "decision": "update" or "create" or "skip",
  "target_meta_id": (when decision is update) ID of metacognition to
      update,
  "reasoning": "Brief decision analysis, must include quantity
     management when count > 30.",
  "meta_cognition": {
    "summary": "...",
    "strategy_principles": [
      {"principle": "...", "confidence": "high", "confidence_score":
           80},
      {"principle": "...", "confidence": "medium", "confidence_score
          ": 60}
    ],
    "overall_confidence": "medium",
    "evidence_paths": 7,
    "uncertainty_note": "..."
  }
}
```