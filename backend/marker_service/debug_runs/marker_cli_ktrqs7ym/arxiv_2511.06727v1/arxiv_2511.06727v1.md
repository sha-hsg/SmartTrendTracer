# S-DAG: A Subject-Based Directed Acyclic Graph for Multi-Agent Heterogeneous Reasoning

Jiangwen Dong\*1 , Zehui Lin\*1 , Wanyu Lin1, 2†, Mingjin Zhang<sup>2</sup>

<sup>1</sup>Department of Data Science and Artificial Intelligence,2Department of Computing The Hong Kong Polytechnic University, Hong Kong SAR, China jiangwen.dong@connect.polyu.hk, linzehui19@gmail.com, wan-yu.lin@polyu.edu.hk, cs-mingjin.zhang@polyu.edu.hk

### Abstract

Large Language Models (LLMs) have achieved impressive performance in complex reasoning problems. Their effectiveness highly depends on the specific nature of the task, especially the required domain knowledge. Existing approaches, such as mixture-of-experts, typically operate at the task level; they are too coarse to effectively solve the heterogeneous problems involving multiple subjects. This work proposes a novel framework that performs fine-grained analysis at subject level equipped with a designated multi-agent collaboration strategy for addressing heterogeneous problem reasoning. Specifically, given an input query, we first employ a Graph Neural Network to identify the relevant subjects and infer their interdependencies to generate an *Subject-based Directed Acyclic Graph* (S-DAG), where nodes represent subjects and edges encode information flow. Then we profile the LLM models by assigning each model a subjectspecific expertise score, and select the top-performing one for matching corresponding subject of the S-DAG. Such subjectmodel matching enables graph-structured multi-agent collaboration where information flows from the starting model to the ending model over S-DAG. We curate and release multisubject subsets of standard benchmarks (MMLU-Pro, GPQA, MedMCQA) to better reflect complex, real-world reasoning tasks. Extensive experiments show that our approach significantly outperforms existing task-level model selection and multi-agent collaboration baselines in accuracy and efficiency. These results highlight the effectiveness of subjectaware reasoning and structured collaboration in addressing complex and multi-subject problems.

# 1 Introduction

In recent years, intelligent agents based on large language models (LLMs) have developed rapidly and achieved significant advancements across various fields, ranging from question answering (Yue 2025; Zhuang et al. 2023) to text generation (Huang et al. 2023; Wu et al. 2024) and complex reasoning tasks (Ke et al. 2025; Zhang et al. 2024b). While the development of a general-purpose LLM is promising (Mumuni and Mumuni 2025; Kojima et al. 2022), it becomes evident that a single LLM often struggles to handle complex reasoning tasks, especially when these problems span multiple disciplines (Feng et al. 2025a). This limitation raises higher demands for model training and fine-tuning (Hoffmann et al. 2022). In this context, multi-agent systems based on LLMs have emerged (Guo et al. 2024; Du et al. 2023; Talebirad and Nadiri 2023; Han et al. 2024; Gu et al. 2025; Liang et al. 2024), aiming to leverage the collective intelligence and specialized expertise of multiple agents to tackle complex and multidisciplinary problems<sup>1</sup> .

Existing research has explored the mixture-of-experts (MoE) framework that dynamically selects the most suitable LLMs for a given problem (Masoudnia and Ebrahimpour 2014; Zhou et al. 2022; Cai et al. 2024). Subsequently, the mixture-of-agents (MoA) paradigm leveraging multi-agent collaboration is proposed to deal with more complex problems by combining the strengths of diverse LLMs (Du et al. 2023; Zhang et al. 2024c; Wang et al. 2024; Li et al. 2024a). The most relevant to us is Symbolic-MoE, which analyzes the required subject knowledge for a task and then utilizes a set of top-k expert/subject models to solve the heterogeneous problem (Chen et al. 2025). For clarity, we organize the existing heterogeneous reasoning paradigms in Table 1. These prior works often assume queries belong to a single knowledge domain or simply rely on a single "best" model or agent for reasoning (Chen et al. 2025; Feng et al. 2024, 2025b; Feng, Shen, and You 2025). Very rare work considers the fine-grained subject-specific information of the problem, not to mention multi-agent collaboration at the subject level, as shown in Figure 1. Such limitation hinders their applicability of prior works in heterogeneous reasoning tasks, where seamless integration of cross-domain knowledge is critical. Therefore, this paper aims to address the following research problem: *How can we optimally select and coordinate expert LLMs at subject level for complex, multi-subject problems to achieve both high accuracy and efficiency?*

In this work, we propose Subject-based Directed Acyclic Graph (S-DAG), as shown in Figure 2, a novel framework for addressing heterogeneous reasoning problems that require knowledge across multiple subject domains. The S-DAG identifies the relevant subjects for a given problem and defines the graph-structured information flow for multi-

<sup>\*</sup>These authors contributed equally.

<sup>†</sup>Corresponding Author: wan-yu.lin@polyu.edu.hk Copyright © 2026, Association for the Advancement of Artificial Intelligence (www.aaai.org). All rights reserved.

<sup>1</sup> For simplicity, agents, LLMs, and models are used interchangeably.

| Category                 | Example Work                            | Subject-Level Analysis | MAS Collaboration | Subject-Specific Collaboration |  |
|--------------------------|-----------------------------------------|------------------------|-------------------|--------------------------------|--|
| Routing                  | GraphRouter (Feng, Shen, and You 2025)  | %                      | %                 | %                              |  |
|                          | SymbolicMoE (Chen et al. 2025)          | !                      | %                 | %                              |  |
| Multi-Agent System (MAS) | Heterogeneous Swarm (Feng et al. 2025b) | %                      | !                 | %                              |  |
|                          | Knowledge Card (Feng et al. 2024)       | !                      | %                 | %                              |  |
| Routing for MAS          | S-DAG (Ours)                            | !                      | !                 | !                              |  |

Table 1: Comparison of our proposed S-DAG and prior methods for heterogeneous reasoning. Unlike prior methods that either perform single-domain routing or lack fine-grained problem understanding, S-DAG supports detailed subject-level analysis and enables dynamic, subject-specific multi-agent collaboration for more effective reasoning.

![](_page_1_Figure_2.jpeg)

Figure 1: Comparison of the prior method with single agent and the proposed S-DAG approach with multi-agent collaboration. The prior method routes the problem to a single agent based on a coarse domain label, while our S-DAG approach conducts fine-grained subject analysis, identifying multiple relevant domains with associated relevant weights.

agent collaboration. We begin by modeling the complete set of subjects as a fully connected graph. To extract finegrained subject-level structure, we introduce a specialized graph neural network that learns node embeddings to capture the relevant subjects and their interdependencies with respect to a given problem. From this, we derive a subjectbased directed acyclic graph that reflects the essential subjects and reasoning flow for the problem. Based on the constructed S-DAG, we perform subject–LLM matching by profiling LLMs according to their subject-specific capabilities. The constructed S-DAG and LLM profile guide a structured multi-agent collaboration mechanism, where domainspecialized LLMs are assigned to subject nodes and communicate according to the DAG topology. Through this design, our S-DAG enables efficient and subject-level multi-agent reasoning. In summary, the main contributions of this work are as follows:

- To the best of our knowledge, we are the first to study the heterogeneous reasoning problem that a single complex problem covers multiple subject knowledge. Our novel framework, S-DAG, enables fine-grained subject-specific decomposition and graph-structured multi-agent collaboration mechanism for the multi-subject problem.
- We develop a fine-grained subject–LLM matching strat-

- egy by profiling LLMs according to subject-specific capabilities, enabling precise assignment of expert agents and efficient coordination via the S-DAG.
- We curate multi-subject evaluation datasets by manually selecting samples that require multi-subject knowledge from three challenging benchmarks—MMLU-Pro, GPQA, and MedMCQA. Extensive experiments demonstrate that our approach substantially outperforms both single-model and multi-model baselines in terms of accuracy and computational efficiency.

# 2 Related Work

Multi-Agent Systems. Recent advances in Multi-Agent Systems (MAS) have introduced diverse collaboration mechanisms to tackle complex tasks (Guo et al. 2024; Talebirad and Nadiri 2023; Han et al. 2024), broadly categorized into fixed and dynamic paradigms. (1) *Fixed Multi-Agent Systems* rely on manually designed architectures, such as LLM debates (Du et al. 2023; Liang et al. 2024), chainof-agents (Gu et al. 2025; Zhang et al. 2024c; Tao, Zhao, and Feng 2025), and graph-based systems (Yin et al. 2023; Li et al. 2024b). These approaches enable collaboration among agents with predefined roles and structures, making them effective for well-structured problems, but often lacking adaptability to dynamic tasks. (2) *Dynamic Multi-Agent Systems* adapt their structure in response to real-time task demands. Notable examples include GPTSwarm (Zhuge et al. 2024) and Heterogeneous Swarms (Feng et al. 2025b), which optimize collaboration through dynamic graph structures. AgentPrune (Zhang et al. 2024a) improves communication efficiency by pruning redundant links, while Dy-LAN (Liu et al. 2024) dynamically selects agents and communication paths based on task context. MasRouter (Yue et al. 2025) introduces a cascaded controller for mode selection, role assignment, and LLM routing, enabling efficient and adaptive MAS construction.

Heterogeneous Reasoning. Heterogeneous reasoning focuses on solving problems that require knowledge across multiple domains (Xin et al. 2024; Chen et al. 2025; Feng et al. 2024). Existing approaches can be grouped by the number of models involved: (1) *Single-Model Approaches* select one expert model per query, often using routing mechanisms. MoE techniques (Masoudnia and Ebrahimpour 2014; Zhou et al. 2022; Cai et al. 2024) specialize models over input space, while FrugalGPT (Chen, Zaharia, and Zou

![](_page_2_Figure_0.jpeg)

Figure 2: The Overview of the S-DAG Framework. The framework operates in two stages. In Stage 1, the input question is encoded using a BERT encoder, and a Graph Decoder generates the S-DAG, capturing subject dependencies and pruning irrelevant subjects. In Stage 2, expert LLMs are selected based on their subject-specific expertise and organized according to the S-DAG, with directed edges defining the information flow for multi-subject collaborative reasoning.

2024) uses a reliability predictor, and GraphRouter (Feng, Shen, and You 2025) employs a graph neural network to frame selection as edge prediction. Though effective, these methods fall short when queries require multi-domain expertise. (2) *Multi-Model Approaches* enable collaboration across multiple expert models. Mixture-of-Agents (MoA)(Wang et al. 2024; Li et al. 2024a) allows coordinated reasoning, while SymbolicMoE(Chen et al. 2025) aggregates top-k responses based on skill relevance. Knowledge-Card (Feng et al. 2024) dynamically selects smaller finetuned agents, and Heterogeneous Swarm (Feng et al. 2025b) optimizes reasoning via a DAG structure. In contrast to prior work focused on dataset-level heterogeneity, our method targets a more granular challenge: each individual question requires reasoning across multiple subject domains.

# 3 Methodology

Method Overview. As illustrated in Figure 2, our proposed S-DAG framework enables subject-aware multi-agent reasoning for complex, multi-subject questions through a twostage process. In Stage 1, the input question is encoded using a BERT encoder, and a Graph Neural Network predicts relevant subjects and their dependencies to construct a Subjectbased Directed Acyclic Graph (S-DAG), filtering out irrelevant domains. In Stage 2, expert LLMs are selected based on subject-specific capability profiles and assigned to the S-DAG nodes. These agents collaborate according to the graph's structure, with directed edges guiding information flow from supporting to dominant subjects, enabling efficient and accurate multi-subject reasoning.

## 3.1 Problem Setup

Let Q denotes a natural language question that spans multiple subject areas S = {s1, s2, ..., sK}, and let M = {M1, M2, ..., Mn} represent a pool of domain-specific expert LLMs. The objective is to solve Q by determining a small set of relevant subject domains S<sup>Q</sup> ⊆ S (typically |SQ| ≤ 5), identifying the interdependencies among them, and assigning each subject s<sup>i</sup> ∈ S<sup>Q</sup> to a corresponding expert model M<sup>j</sup> ∈ M that is most proficient in that domain. More specifically, we model the relationships between the selected subjects by constructing a DAG over SQ, i.e., S-DAG, where a directed edge s<sup>i</sup> → s<sup>j</sup> indicates that subject s<sup>i</sup> provides auxiliary support for reasoning in subject s<sup>j</sup> in solving Q. This structure reflects the compositional nature of multi-domain reasoning and determines how different experts should collaborate. To obtain the S-DAG, we define a fully connected directed graph  $\mathcal{G} = \{\mathcal{V}, \mathcal{E}\}$ , where each node  $v_i \in \mathcal{V}$  corresponds to a subject  $s_i \in \mathcal{S}$ , and each directed edge  $(v_i, v_j) \in \mathcal{E}$  encodes a potential dependency between subject pairs. From  $\mathcal{G}$ , we derive the pruned S-DAG  $\mathcal{G}_{\mathcal{Q}} = \{\mathcal{S}_{\mathcal{Q}}, \mathcal{A}_{\mathcal{Q}}\}$ , which serves as a high-level reasoning blueprint. It guides the selection of a subset of expert LLMs,  $\mathcal{M}_{\mathcal{Q}} \subseteq \mathcal{M}$ , and defines the collaboration topology among them, enabling effective multi-agent reasoning over complex, interdisciplinary queries.

### 3.2 Preprocessing

**GNN Training.** To effectively solve the multi-subject questions, we employ a set of expert agents, each specializing in a distinct domain. While LLMs are capable of identifying relevant subjects via prompting, they often struggle to capture fine-grained inter-subject dependencies and may produce outputs that are noisy, inconsistent, or lacking in structural coherence. To address this limitation, we introduce a trainable GNN module that learns to model subject dependencies through iterative message-passing over a subject-level graph. The resulting subject graph, or S-DAG, serves as a robust structural prior that guides information flow across agents.

Before training the GNN for S-DAG generation, we preprocess the dataset to construct ground-truth subject graphs for supervision. Given a question Q, we prompt a LLM to extract a set of relevant subject domains  $S_Q$  =  $\{s_1, s_2, ..., s_k\}$ . Each subject  $s_i$  is assigned a relevance weight  $\{w_i\}_{i=1}^k \in [0,1]$ , indicating its relative importance for solving Q. Using these subjects and weights, we can construct a ground-truth subject graph  $\mathcal{G}_{\mathcal{Q}} = \{\mathcal{S}_{\mathcal{Q}}, \mathcal{A}_{\mathcal{Q}}\}$  for question Q, where  $A_Q \in \{0,1\}^{k \times k}$  is the adjacency matrix. Specifically, a directed edge  $a_{\mathcal{O}}^{ij}=1$  indicates that subject  $s_i$  (with lower weights) supports subject  $s_i$  (with higher weight), reflecting the support-to-dominant subject relationship essential for multi-agent subject-specific reasoning. To ensure consistency, we use gwen-turbo-0919 (Yang et al. 2024) as the Subject LLM and perform three rounds of processing for each question, only retaining subjects that appear consistently. Further details on dataset preprocessing and subject graph construction are provided in appendix. To ensure comprehensive modeling of potential subject interactions, we define a static, fully connected directed graph  $\mathcal{G} = \{\mathcal{V}, \mathcal{E}\}\$ , where each node corresponds to a candidate subject and each edge represents a possible dependency. This graph serves as the structural input for the GNN during S-DAG generation.

Given a question  $\mathcal{Q}$ , a pretrained transformer encoder, BERT (Devlin et al. 2019), encodes it into a dense vector  $\mathbf{h}_{\mathcal{Q}} \in \mathbb{R}^d$ , capturing the semantic intent of the input. Each subject node representation  $v \in \mathcal{V}$  is initialized with a fused features of its subject embedding and question embedding via an MLP:

$$\mathbf{x}_{i}^{(0)} = \text{MLP}_{\text{init}}([\mathbf{h}_{i}; \mathbf{h}_{Q}]).$$
 (1)

The initialized node features are then updated through layers of directional message passing within the GNN.

The final node representations are used for joint node and edge prediction, yielding a predicted subject graph  $\mathcal{G}_{\mathcal{Q}} = \{\hat{\mathcal{S}}_{\mathcal{Q}}, \hat{\mathcal{A}}_{\mathcal{Q}}\}$ , where  $\hat{s}^i_{\mathcal{Q}} \in \hat{\mathcal{S}}_{\mathcal{Q}}$  is the predicted relevance score for subject  $s_i$ , and  $\hat{a}^{ij}_{\mathcal{Q}}$  is the predicted edge score for the dependency from  $s_i$  to  $s_j$ . Formally, the model is trained to minimize a multi-task binary cross-entropy loss between the predicted and ground-truth node and edge labels:

$$\mathcal{L} = \lambda_{\text{node}} \cdot \sum_{i=1}^{K} \text{BCE}(\hat{s}_{\mathcal{Q}}^{i}, s_{\mathcal{Q}}^{i}) + \lambda_{\text{edge}} \cdot \sum_{i \neq j} \text{BCE}(\hat{a}_{\mathcal{Q}}^{ij}, a_{\mathcal{Q}}^{ij}),$$
(2)

where  $\lambda_{\mathrm{node}}$  and  $\lambda_{\mathrm{edge}}$  control the weighting between nodelevel and edge-level supervision. To avoid penalizing irrelevant subjects, edge loss terms are masked when both  $s_i=0$  and  $s_j=0$ . This objective encourages the model to learn subjects and their interaction patterns reflecting the reasoning dependencies in multi-domain tasks. Once trained, the GNN is used at inference time to construct a S-DAG for any new question, guiding the structure and flow of LLM-based agent collaboration tailored to the problem's subject composition.

**LLMs Subject Capability Profile.** To optimize multiagent collaboration, we construct a capability profile for each LLM based on its performance across various subject domains. This profile captures the subject-specific strengths of each model and serves as the foundation for expert selection within the heterogeneous multi-agent system. By leveraging these profiles, we ensure that queries are routed to the most competent models, improving both accuracy and efficiency in multi-domain reasoning.

Unlike prior work (Chen et al. 2025), which assigns a single subject label to each question, our approach captures the multi-domain nature by assigning weights to all relevant subjects. These weights reflect the relative importance of each subject in solving the question, enabling a more fine-grained and accurate assessment of each LLM's performance across different domains. For instance, if model  $M_i$  answers a question spanning math, physics, and biology with weights  $\{'\text{math}': 0.5, '\text{physics}': 0.3, '\text{biology}': 0.2\}$  correctly, it would accordingly obtain the performance score  $\text{Score}_{M_i} = \{'\text{math}': +0.5, '\text{physics}': +0.3, '\text{biology}': +0.2\}$ . By aggregating such weighted scores across a diverse set of questions, each model builds a subject capability profile that accurately reflects its domain expertise.

To construct these profiles, we randomly select 200 questions from the test set to assess LLM performance across each subject domain. The performance scores are then normalized to ensure comparability across domains and models. The normalized capability scores  $C_{ij}$  for model  $M_i$  and subject  $s_j$  are given by:

$$C_{ij} = \frac{\text{Score}_{M_i, s_j}}{\sum_{s_k \in \mathcal{S}} \text{Score}_{M_i, s_k}},$$
(3)

where S is the set of all subject domains. Normalization ensures that the sum of scores across all domains for each

model equals 1, preventing skewed evaluations and enabling fair comparisons. This profiling system enables dynamic, context-aware model selection based on the subject composition of each query, ensuring that the most suitable expert LLM is invoked during inference.

### 3.3 Multi-Agent Collaboration

S-DAG Generation. During inference, given an input question, we employ the trained GNN model to refine both the question embedding and subject node features. The node and edge classifiers (MLP modules) simultaneously predict relevant subject nodes and their dependencies. This inference procedure mirrors the training phase described in Section 3.2. The resulting S-DAG  $\mathcal{G}_{\mathcal{Q}}$  is a pruned subgraph of the fully connected subject graph  $\mathcal{G}$ , retaining only the most relevant subjects and directed relationships. The complete S-DAG generation process is presented in Alg. 1.

Why is S-DAG suitable for guiding multi-agent subjectspecific reasoning? The S-DAG captures both hierarchical and interdependent relationships among subjects. Dominant subjects represent the central focus of reasoning, while supporting subjects—linked via directed edges—provide complementary knowledge. This structured representation naturally defines a collaboration mechanism among expert agents: support agents supply contextual input that enriches the reasoning of dominant agents. Further discussion of the theoretical motivation and construction principles is provided in appendix.

### Algorithm 1: S-DAG Generation

Input: Input question Q. Randomly initialized node embedding  $\{\mathbf{h}_i\}_{i\in\mathcal{V}}$ . An initial fully connected graph  $\mathcal{G}=\{\mathcal{V},\mathcal{E}\}$ .

**Output:** Generated S-DAG  $\mathcal{G}_{\mathcal{Q}}$ .

- 1: **for** each question Q **do**
- **Step 1: Question Embedding** 2:
- Embed the question:  $\mathbf{h}_{\mathcal{Q}} \leftarrow \mathrm{BERT}(\mathcal{Q})$ . 3:
- Initialize node features:  $\mathbf{x}_i \leftarrow \text{MLP}_{\text{init}}([\mathbf{h}_i; \mathbf{h}_{\mathcal{Q}}]), i \in \mathcal{V}.$ 4:
- 5: **Step 2: S-DAG Generation**
- 6:
- 7:
- Update the node features:  $\mathbf{x}_i = f_{\theta}(\mathcal{G}, \mathbf{x}_i^{(0)}), i \in \mathcal{V}$ . Node prediction:  $s_{i,i \in \mathcal{V}} \leftarrow \mathrm{MLP_{node}}(\mathbf{x}_i)$ . Edge prediction:  $a_{\mathcal{Q}}^{ij,(i,j) \in \mathcal{E}} \leftarrow \mathrm{MLP_{node}}(\mathbf{x}_i; \mathbf{x}_j; \mathbf{h}_{\mathcal{Q}})$ .
- S-DAG Construction:  $\mathcal{G}_{\mathcal{Q}} = \{s_{\mathcal{Q}}^i, a_{\mathcal{Q}}^{ij}\}_{i=1}^K$ .
- 10: end for

Multi-Agent Information Flow over S-DAG. Given the S-DAG generated in the previous step, the next is to select the appropriate expert LLMs based on their subject proficiency. Based on the LLM subject capability profile process, we match each subject node in the S-DAG to an expert LLM specializing in that domain. If  $C_{ij}$  represents the performance score of LLM  $M_i$  on subject  $s_j$ , the LLM selection for a particular subject  $s_j$  could be expressed as:

$$M_j = \arg\max_{M_i} C_{ij}.$$
 (4)

The multi-agent collaboration mechanism is defined by the directed relationships encoded in the S-DAG, as illustrated in Figure 2. Each edge in the graph represents an information flow dependency between two subject domains,

| Dataset  | Train Set | Test Set | Avg. Subject/Q |
|----------|-----------|----------|----------------|
| MMLU-Pro | 1173      | 503      | 4.4            |
| GPQA     | 302       | 129      | 3.8            |
| MedMCQA  | 396       | 169      | 3.5            |

Table 2: Overview of the curated multi-subject datasets used in our experiments. We manually select questions that span multiple subject areas to better evaluate heterogeneous reasoning capabilities. "Avg. Subject/Q" denotes the average number of distinct subjects involved per question, reflecting the interdisciplinary complexity of each dataset.

guiding how the associated LLM agents should collaborate. Specifically, if a query involves subjects  $s_1$  and  $s_2$  with a directed edge from  $s_1$  to  $s_2$ , the output of the agent corresponding to  $s_1$  and the original query jointly serve as the prompt input for the agent corresponding to  $s_2$ , thereby forming a collaborative reasoning pipeline. The prompting strategy that enables this information flow is detailed in appendix. This process can be formalized as:

$$y_i^{out} = M_j(\{y_i^{out} | a_{ij} = 1\}, \mathcal{Q}),$$
 (5)

where  $y_i^{out}$  denotes the output of agent  $M_i$  associated with subject  $s_i$ ,  $a_{ij} = 1$  indicates subject  $s_i$  has a directed edge to  $s_i$  in the S-DAG, and Q represents the original question, which is included as a shared input to all agents. This dynamic and dependency-driven collaboration enables the system to aggregate reasoning results and progressively refine the final answer through multi-agent cooperation.

## 4 Experiments

# 4.1 Experiment Setup

Datasets. We evaluate our proposed method on three benchmarks. MMLU-Pro (Wang et al. 2025) is a challenging extension of the MMLU benchmark, covering 14 collegelevel subjects. GPQA (Rein et al. 2024) is a dataset of graduate-level science questions designed to be difficult. MedMCQA (Pal, Umapathi, and Sankarasubbu 2022) is a collection of medical entrance exam questions across 21 subdomains. To better reflect real-world heterogeneous reasoning scenarios, we preprocess each dataset to select samples involve multiple subject areas. We construct a dedicated dataset, as shown in Table 2. We also construct a profiling set with 200 samples used to evaluate the subject-specific capabilities of LLMs. This dataset preprocessing ensures that our evaluation aligns with the core challenge addressed in this paper: selecting and coordinating multiple expert agents to solve complex, multi-subject reasoning problems. The details of the dataset curation are shown in appendix.

LLM Pool with Various Experts. To enable subjectaware reasoning and fine-grained agent specialization, we construct a pool of domain-specific expert LLMs. Each model is either pretrained or fine-tuned on data aligned with a specific academic or professional domain, such as mathematics, medicine, law, or economics. These models, typically ranging from 7B to 13B parameters, are computation-

| Category                   | Method                           | Model        | MMLU-Pro     | GPQA         | MedMCQA      | Avg.  |
|----------------------------|----------------------------------|--------------|--------------|--------------|--------------|-------|
| Closed-Source Single Model | CoT (Wei et al. 2022)            | GPT4o-mini   | 49.42 ± 0.27 | 47.31 ± 0.52 | 78.82 ± 0.35 | 58.52 |
| Open-Source                | CoT                              | Qwen2.5 72b  | 50.81 ± 0.46 | 48.98 ± 0.35 | 80.44 ± 0.47 | 60.08 |
| Single Model               | CoT                              | Llama3.3 70b | 51.92 ± 0.39 | 48.83 ± 0.41 | 79.36 ± 0.61 | 60.04 |
| Single-Model               | CoT                              | Qwen2.5 7b   | 41.86 ± 0.29 | 44.51 ± 0.58 | 72.07 ± 0.39 | 52.81 |
|                            | Self-Refine (Madaan et al. 2023) | Qwen2.5 7b   | 44.92 ± 0.34 | 43.83 ± 0.12 | 74.58 ± 0.28 | 54.44 |
|                            | MoE (Zhou et al. 2022)           | LLM Pool     | 42.57 ± 0.55 | 45.67 ± 0.34 | 75.45 ± 0.49 | 54.56 |
|                            | GraphRouter (Feng et al. 2025)   | LLM Pool     | 44.94 ± 0.94 | 46.23 ± 0.82 | 76.92 ± 0.72 | 56.03 |
| Multi-Model                | MAD (Du et al. 2023)             | Qwen2.5 7b   | 45.82 ± 0.13 | 46.81 ± 0.21 | 76.55 ± 0.15 | 56.39 |
|                            | Symbolic-MoE (Chen et al. 2025)  | LLM Pool     | 48.13 ± 0.62 | 45.92 ± 0.51 | 78.55 ± 0.61 | 57.53 |
|                            | S-DAG (Ours)                     | LLM Pool     | 50.98 ± 0.19 | 49.82 ± 0.24 | 78.38 ± 0.35 | 59.73 |

Table 3: Performance comparison of single-model and multi-model approaches on MMLU-Pro, GPQA, and MedMCQA. We compare various baselines across closed-source, open-source, single-agent and multi-agent settings. We bold the best results and underline the second-best (excluding methods using bigger or proprietary models).

ally efficient and well-suited for multi-agent composition. In total, we select 14 expert LLMs spanning a broad range of disciplines. Appendix provides details on the expert models, corresponding subject domains, and Hugging Face links. For instance, DeepseekMath is used for mathematics, while BioMistral is assigned to biology. These expert LLMs form the foundation of our multi-agent system, where each agent is instantiated from the most suitable LLM based on the subject assignments derived from the S-DAG and LLM identification process.

Baselines. Our selection of baselines is guided by the goal of evaluating the challenge of heterogeneous reasoning, where a single complex question spans multiple subject domains. We consider two primary categories. First, we evaluate single-model methods to test whether a single, highperformance, general-purpose LLM can effectively handle multi-subject reasoning. Specifically, we include models such as closed-source GPT4o-mini (Hurst et al. 2024), open-source Qwen2.5-72B (Yang et al. 2024) and Llama3.3- 70B (Grattafiori et al. 2024). Then, the Mixture-of-Experts (MoE) approaches that dynamically select one expert model; GraphRouter that utilize a GNN to select expert model based on contextual information given a problem. Second, we explore multi-model methods, which leverage specialized expertise through collaborative or modular strategies. These include Multi-Agent Debate (MAD), where multiple agents reason through dialogue (Liang et al. 2024); and Symbolic-MoE (Chen et al. 2025), which conducts skill-level expert selection. These baselines provide a comprehensive framework to assess both generalist and specialist strategies for tackling complex, interdisciplinary reasoning tasks. Prompts for different baselines are shown in Table 8 in appendix.

Implementation Details. All experiments, including baselines and our proposed method, are conducted using A100 GPUs with 40 GB memory. For large models such as the 70B open-source LLMs and Qwen variants, we use API-based inference, while smaller expert models in the LLM pool are deployed locally. The decoding temperature is set to 0.7, and the maximum output length is fixed at 4096 tokens across all LLMs. Adam optimizer is used to train GNN and MLP models, and the seed is fixed. Results are averaged across three trials, and we compute the standard deviations as the statistical indicator. Details on model selection and the LLM pool are provided in appendix.

## 4.2 Results

The main empirical findings are shown in Table 3. We evaluate the performance of various reasoning frameworks across selected samples from MMLU-Pro, GPQA, and MedM-CQA, including both single-model and multi-model settings, as well as open-source and closed-source configurations. The average accuracy is acquired by averaging results across the three benchmarks. Below, we highlight key insights derived from this comparative analysis.

Superior Accuracy of S-DAG. Our S-DAG framework achieves the highest average accuracy (59.73%). It consistently outperforms both single-model and multi-model baselines. In particular, compared to single-model approaches that rely on expert selection—such as MoE (54.56%) and GraphRouter (56.03%)—S-DAG demonstrates a significant improvement. This result underscores the benefit of explicitly modeling inter-subject dependencies, rather than relying solely on selection-based mechanisms.

Robustness over Multi-Model Baselines. Our S-DAG also outperforms several competitive multi-agent systems. It exceeds the performance of Symbolic-MoE (57.53%) and MAD (56.39%) in average accuracy. Although Symbolic-MoE shows strong performance on MedMCQA (78.55%), its effectiveness does not consistently translate across other benchmarks. In contrast, S-DAG maintains a well-balanced performance across all three tasks, demonstrating its robustness and adaptability in coordinating specialized agents across diverse reasoning scenarios.

Competitiveness with Large LLMs. Despite being composed of smaller, domain-specific expert models, S-DAG achieves performance competitive with large-scale, monolithic LLMs. It surpasses the closed-source GPT-4o-mini (58.52%) and closely matches the performance of opensource leaders such as Qwen2.5 72B (60.08%) and Llama3.3 70B (60.04%). This indicates that structured coordination

| Variant                 | GNN Coord.   | <b>Model Selection</b> | <b>Graph Structure</b> | Avg. Accuracy (%) | Inf. Time (s) | # LLM Calls |
|-------------------------|--------------|------------------------|------------------------|-------------------|---------------|-------------|
| w/o GNN, random model   | ×            | ×                      | S-DAG                  | 41.12             | 14.21         | 5.1         |
| w/ GNN, random model    | ✓            | ×                      | S-DAG                  | 42.19             | 14.82         | 4.1         |
| w/o GNN, profiled model | ×            | $\checkmark$           | S-DAG                  | 53.51             | 14.53         | 5.1         |
| Fully Connected Graph   | $\checkmark$ | $\checkmark$           | Fully-connected        | 57.29             | 38.45         | 8.2         |
| Our Full S-DAG          | $\checkmark$ | $\checkmark$           | S-DAG                  | 59.73             | 15.02         | 4.1         |

Table 4: Ablation study on the effects of coordination (GNN), model selection (LLM profiling), and graph structure. Accuracy is averaged across MMLU-Pro, GPQA, and MedMCQA. Inference efficiency is measured via average inference time and the number of LLM calls per instance.

![](_page_6_Figure_2.jpeg)

Figure 3: Comparison between the Fully Connected Graph and our S-DAG.

among lightweight experts can rival or exceed the capabilities of significantly larger models, offering a more efficient and cost-effective solution for complex reasoning tasks.

### 4.3 Ablation Study

To quantify the contribution of individual components in our S-DAG framework, we conduct a structured ablation study, as presented in Table 4. This analysis isolates three key design factors: (1) the presence or absence of GNNbased coordination, (2) the use of subject-aware model selection via LLM profiling versus random assignment, and (3) the impact of graph topology, comparing our sparse S-DAG structure to a fully connected alternative. We evaluate each configuration across two core dimensions: task performance and computational efficiency. Inference time denotes the average wall-clock latency required to process a single multi-subject question, encompassing decomposition, agent invocation, message passing, and response synthesis. LLM call count indicates the average number of distinct language model calls per instance, serving as a proxy for computational and monetary cost. More information is detailed in appendix.

Effectiveness of GNN Module. Rather than directly prompting the LLM and construct the S-DAG manually, we introduce a GNN module that learns subject interdependencies from data and automatically produces the S-DAG. To evaluate the effectiveness of this design choice, we conduct an ablation study comparing our learned S-DAG with one derived purely from LLM-generated subject weights. The results show that using the LLM-generated S-DAG yields a significantly lower accuracy compared to 59.73% achieved

by our GNN-based approach. This performance gap highlights the limitations of relying solely on LLM outputs, which can be noisy and inconsistent. In contrast, our GNN module leverages training data to learn robust and context-sensitive subject relationships, resulting in more accurate and concise graph structures for multi-agent reasoning.

Effectiveness of LLM Profile. To assess the benefit of our LLM profiling strategy, we compare our subject-aware model selection approach against a baseline that randomly selects expert models for each subject node in the S-DAG. The results demonstrate that using our profiled subject—model matching significantly improves performance across all benchmarks. This highlights the importance of aligning subject-specific tasks with LLMs that exhibit strong domain expertise. Without profiling, the system risks assigning questions to suboptimal models, which can lead to degraded reasoning quality and inconsistent outputs.

Effectiveness of Directed Acyclic Graph Structure. To evaluate the impact of graph topology, we compare our S-DAG with a fully connected graph (FCG) variant. As illustrated in Figure 3, the FCG allows unrestricted bidirectional communication among all subject nodes, which leads to over-communication and redundant information flow. In contrast, our S-DAG enforces a sparse, hierarchical structure that streamlines reasoning. Empirically, S-DAG achieves higher accuracy (59.73%) while significantly reducing inference time (15.02s) and the number of LLM calls (4.1 per instance). These results demonstrate that fully connected communication is suboptimal for multi-agent reasoning, and that structured, directional coordination leads to more efficient and effective performance.

## 5 Conclusion

We present S-DAG, a novel framework for heterogeneous reasoning that leverages fine-grained subject-level analysis to guide multi-agent collaboration. By constructing a subject-based directed acyclic graph via a GNN, our method captures subject interdependencies, enabling targeted coordination among specialized LLMs. This structured approach yields efficient, subject-level reasoning. Experiments on three challenging benchmarks show that S-DAG consistently outperforms both single-model and multi-model baselines, achieving competitive accuracy with large-scale LLMs at significantly lower computational cost. Ablation studies further highlight the benefits of the DAG structure

# References

- Cai, W.; Jiang, J.; Wang, F.; Tang, J.; Kim, S.; and Huang, J. 2024. A survey on mixture of experts. *arXiv preprint arXiv:2407.06204*.
- Chen, J. C.-Y.; Yun, S.; Stengel-Eskin, E.; Chen, T.; and Bansal, M. 2025. Symbolic Mixture-of-Experts: Adaptive Skill-based Routing for Heterogeneous Reasoning. *arXiv preprint arXiv:2503.05641*.
- Chen, L.; Zaharia, M.; and Zou, J. 2024. FrugalGPT: How to Use Large Language Models While Reducing Cost and Improving Performance. *Transactions on Machine Learning Research*.
- Devlin, J.; Chang, M.-W.; Lee, K.; and Toutanova, K. 2019. Bert: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of the 2019 conference of the North American chapter of the association for computational linguistics: human language technologies, volume 1 (long and short papers)*, 4171–4186.
- Du, Y.; Li, S.; Torralba, A.; Tenenbaum, J. B.; and Mordatch, I. 2023. Improving factuality and reasoning in language models through multiagent debate. In *Forty-first International Conference on Machine Learning*.
- Feng, S.; Ding, W.; Liu, A.; Wang, Z.; Shi, W.; Wang, Y.; Shen, Z.; Han, X.; Lang, H.; Lee, C.-Y.; et al. 2025a. When One LLM Drools, Multi-LLM Collaboration Rules. *arXiv preprint arXiv:2502.04506*.
- Feng, S.; Shi, W.; Bai, Y.; Balachandran, V.; He, T.; and Tsvetkov, Y. 2024. Knowledge Card: Filling LLMs' Knowledge Gaps with Plug-in Specialized Language Models. In *The Twelfth International Conference on Learning Representations*.
- Feng, S.; Wang, Z.; Goyal, P.; Wang, Y.; Shi, W.; Xia, H.; Palangi, H.; Zettlemoyer, L.; Tsvetkov, Y.; Lee, C.-Y.; et al. 2025b. Heterogeneous Swarms: Jointly Optimizing Model Roles and Weights for Multi-LLM Systems. *arXiv preprint arXiv:2502.04510*.
- Feng, T.; Shen, Y.; and You, J. 2025. GraphRouter: A Graphbased Router for LLM Selections. In *The Thirteenth International Conference on Learning Representations*.
- Grattafiori, A.; Dubey, A.; Jauhri, A.; Pandey, A.; Kadian, A.; Al-Dahle, A.; Letman, A.; Mathur, A.; Schelten, A.; Vaughan, A.; et al. 2024. The llama 3 herd of models. *arXiv preprint arXiv:2407.21783*.
- Gu, W.; Han, J.; Wang, H.; Li, X.; and Cheng, B. 2025. Explain-Analyze-Generate: A Sequential Multi-Agent Collaboration Method for Complex Reasoning. In *Proceedings of the 31st International Conference on Computational Linguistics*, 7127–7140.
- Guo, T.; Chen, X.; Wang, Y.; Chang, R.; Pei, S.; Chawla, N. V.; Wiest, O.; and Zhang, X. 2024. Large language model based multi-agents: A survey of progress and challenges. *arXiv preprint arXiv:2402.01680*.
- Han, S.; Zhang, Q.; Yao, Y.; Jin, W.; Xu, Z.; and He, C. 2024. LLM multi-agent systems: Challenges and open problems. *arXiv preprint arXiv:2402.03578*.

- Hoffmann, J.; Borgeaud, S.; Mensch, A.; Buchatskaya, E.; Cai, T.; Rutherford, E.; de Las Casas, D.; Hendricks, L. A.; Welbl, J.; Clark, A.; et al. 2022. Training compute-optimal large language models. In *Proceedings of the 36th International Conference on Neural Information Processing Systems*, 30016–30030.
- Huang, W.; Xia, F.; Shah, D.; Driess, D.; Zeng, A.; Lu, Y.; Florence, P.; Mordatch, I.; Levine, S.; Hausman, K.; et al. 2023. Grounded decoding: Guiding text generation with grounded models for embodied agents. *Advances in Neural Information Processing Systems*, 36: 59636–59661.
- Hurst, A.; Lerer, A.; Goucher, A. P.; Perelman, A.; Ramesh, A.; Clark, A.; Ostrow, A.; Welihinda, A.; Hayes, A.; Radford, A.; et al. 2024. Gpt-4o system card. *arXiv preprint arXiv:2410.21276*.
- Ke, Z.; Jiao, F.; Ming, Y.; Nguyen, X.-P.; Xu, A.; Long, D. X.; Li, M.; Qin, C.; Wang, P.; Savarese, S.; et al. 2025. A Survey of Frontiers in LLM Reasoning: Inference Scaling, Learning to Reason, and Agentic Systems. *arXiv preprint arXiv:2504.09037*.
- Kojima, T.; Gu, S. S.; Reid, M.; Matsuo, Y.; and Iwasawa, Y. 2022. Large language models are zero-shot reasoners. *Advances in neural information processing systems*, 35: 22199–22213.
- Li, D.; Tan, Z.; Qian, P.; Li, Y.; Chaudhary, K. S.; Hu, L.; and Shen, J. 2024a. Smoa: Improving multi-agent large language models with sparse mixture-of-agents. *arXiv preprint arXiv:2411.03284*.
- Li, Y.; Du, Y.; Zhang, J.; Hou, L.; Grabowski, P.; Li, Y.; and Ie, E. 2024b. Improving Multi-Agent Debate with Sparse Communication Topology. In *Findings of the Association for Computational Linguistics: EMNLP 2024*, 7281–7294.
- Liang, T.; He, Z.; Jiao, W.; Wang, X.; Wang, Y.; Wang, R.; Yang, Y.; Shi, S.; and Tu, Z. 2024. Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate. In *Proceedings of the 2024 Conference on Empirical Methods in Natural Language Processing*, 17889– 17904.
- Liu, Z.; Zhang, Y.; Li, P.; Liu, Y.; and Yang, D. 2024. A dynamic LLM-powered agent network for task-oriented agent collaboration. In *First Conference on Language Modeling*.
- Madaan, A.; Tandon, N.; Gupta, P.; Hallinan, S.; Gao, L.; Wiegreffe, S.; Alon, U.; Dziri, N.; Prabhumoye, S.; Yang, Y.; et al. 2023. Self-refine: Iterative refinement with selffeedback. *Advances in Neural Information Processing Systems*, 36: 46534–46594.
- Masoudnia, S.; and Ebrahimpour, R. 2014. Mixture of experts: a literature survey. *Artificial Intelligence Review*, 42: 275–293.
- Mumuni, A.; and Mumuni, F. 2025. Large language models for artificial general intelligence (AGI): A survey of foundational principles and approaches. *arXiv preprint arXiv:2501.03151*.
- Pal, A.; Umapathi, L. K.; and Sankarasubbu, M. 2022. Medmcqa: A large-scale multi-subject multi-choice dataset for medical domain question answering. In *Conference on health, inference, and learning*, 248–260. PMLR.

- Rein, D.; Hou, B. L.; Stickland, A. C.; Petty, J.; Pang, R. Y.; Dirani, J.; Michael, J.; and Bowman, S. R. 2024. Gpqa: A graduate-level google-proof q&a benchmark. In *First Conference on Language Modeling*.
- Talebirad, Y.; and Nadiri, A. 2023. Multi-agent collaboration: Harnessing the power of intelligent llm agents. *arXiv preprint arXiv:2306.03314*.
- Tao, M.; Zhao, D.; and Feng, Y. 2025. Chain-of-Discussion: A Multi-Model Framework for Complex Evidence-Based Question Answering. In *Proceedings of the 31st International Conference on Computational Linguistics*, 11070– 11085.
- Wang, J.; Wang, J.; Athiwaratkun, B.; Zhang, C.; and Zou, J. 2024. Mixture-of-agents enhances large language model capabilities. *arXiv preprint arXiv:2406.04692*.
- Wang, Y.; Ma, X.; Zhang, G.; Ni, Y.; Chandra, A.; Guo, S.; Ren, W.; Arulraj, A.; He, X.; Jiang, Z.; et al. 2025. MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark. *Advances in Neural Information Processing Systems*, 37: 95266–95290.
- Wei, J.; Wang, X.; Schuurmans, D.; Bosma, M.; Xia, F.; Chi, E.; Le, Q. V.; Zhou, D.; et al. 2022. Chain-ofthought prompting elicits reasoning in large language models. *Advances in neural information processing systems*, 35: 24824–24837.
- Wu, Q.; Bansal, G.; Zhang, J.; Wu, Y.; Li, B.; Zhu, E.; Jiang, L.; Zhang, X.; Zhang, S.; Liu, J.; Awadallah, A. H.; White, R. W.; Burger, D.; and Wang, C. 2024. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversations. In *First Conference on Language Modeling*.
- Xin, A.; Liu, J.; Yao, Z.; Lee, Z.; Cao, S.; Hou, L.; and Li, J. 2024. AtomR: Atomic Operator-Empowered Large Language Models for Heterogeneous Knowledge Reasoning. *arXiv preprint arXiv:2411.16495*.
- Yang, A.; Yang, B.; Zhang, B.; Hui, B.; Zheng, B.; Yu, B.; Li, C.; Liu, D.; Huang, F.; Wei, H.; et al. 2024. Qwen2. 5 technical report. *arXiv preprint arXiv:2412.15115*.
- Yin, Z.; Sun, Q.; Chang, C.; Guo, Q.; Dai, J.; Huang, X.-J.; and Qiu, X. 2023. Exchange-of-Thought: Enhancing Large Language Model Capabilities through Cross-Model Communication. In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, 15135– 15153.
- Yue, M. 2025. A Survey of Large Language Model Agents for Question Answering. *arXiv preprint arXiv:2503.19213*.
- Yue, Y.; Zhang, G.; Liu, B.; Wan, G.; Wang, K.; Cheng, D.; and Qi, Y. 2025. Masrouter: Learning to route llms for multiagent systems. *arXiv preprint arXiv:2502.11133*.
- Zhang, G.; Yue, Y.; Li, Z.; Yun, S.; Wan, G.; Wang, K.; Cheng, D.; Yu, J. X.; and Chen, T. 2024a. Cut the crap: An economical communication pipeline for llm-based multiagent systems. *arXiv preprint arXiv:2410.02506*.
- Zhang, Y.; Mao, S.; Ge, T.; Wang, X.; de Wynter, A.; Xia, Y.; Wu, W.; Song, T.; Lan, M.; and Wei, F. 2024b. Llm as a mastermind: A survey of strategic reasoning with large language models. *arXiv preprint arXiv:2404.01230*.

- Zhang, Y.; Sun, R.; Chen, Y.; Pfister, T.; Zhang, R.; and Arik, S. 2024c. Chain of agents: Large language models collaborating on long-context tasks. *Advances in Neural Information Processing Systems*, 37: 132208–132237.
- Zhou, Y.; Lei, T.; Liu, H.; Du, N.; Huang, Y.; Zhao, V.; Dai, A. M.; Le, Q. V.; Laudon, J.; et al. 2022. Mixture-of-experts with expert choice routing. *Advances in Neural Information Processing Systems*, 35: 7103–7114.
- Zhuang, Y.; Yu, Y.; Wang, K.; Sun, H.; and Zhang, C. 2023. Toolqa: A dataset for llm question answering with external tools. *Advances in Neural Information Processing Systems*, 36: 50117–50143.
- Zhuge, M.; Wang, W.; Kirsch, L.; Faccio, F.; Khizbullin, D.; and Schmidhuber, J. 2024. Gptswarm: Language agents as optimizable graphs. In *Forty-first International Conference on Machine Learning*.

# A Multi-Subject Dataset Curation

# A.1 Question Analysis

While benchmark datasets like MMLU-Pro offer broad subject coverage, individual questions within these datasets often pertain to a single domain, limiting their utility for evaluating complex, interdisciplinary reasoning. In contrast, our work targets multisubject reasoning, where answering a question requires synthesizing knowledge across multiple subject areas. This distinction is critical for advancing generalist models that more closely resemble human cognitive abilities.

To construct a dataset that captures this complexity, we introduce a rigorous preprocessing pipeline aimed at filtering and enhancing questions that truly require interdisciplinary reasoning. For each dataset, we employ the large language model qwen-turbo-0919 (Yang et al. 2024) to analyze the subject composition of every question. The model identifies relevant subject domains and assigns a relevance weight to each, reflecting its importance to the question. To ensure robustness and mitigate the variability of model outputs, each question is analyzed three independent times. We then retain only the subjects that consistently appear in all three runs, thereby filtering out spurious or weak associations. This consensus-based filtering increases the precision of subject attribution. The resulting subject weights are normalized across the retained set to maintain comparability and interpretability.

Table 5: Prompt for dataset preprocessing. LLM analyzes the question and outputs the relevant subjects and their weights.

#### Prompt

Question: {Q} What are the core knowledge, subjects or skills needed to solve this problem? List 2-5 keywords separated in comma, with the weights (0∼1.0). These weights represent the proportion of these skills are needed in the question. And the proportion of all keywords sum to 1. Candidate keywords: Math, Physics, Chemistry, Law, Engineering, Economics, Health, Psychology, Business, Biology, Philosophy, Computer Science, History, Medicine, Other. Give ONLY the keywords with weights, no other words or explanation. Please follow this format: Keywords: < Math0.6 >, < Physics0.3 >, < Chemistry0.1 > ...

Overall, this subject attribution framework allows us to curate a high-quality dataset that better reflects real-world, crossdisciplinary reasoning tasks. The prompt template used for subject decomposition and analysis is detailed in Table 5.

We partition the curated dataset into a training set and a test set for model development and evaluation, respectively. Additionally, we reserve a separate set of 200 samples as the profiling set, which is specifically used to assess the subject-specific capabilities of each LLM. This profiling process enables accurate subject–model matching during multi-agent inference.

![](_page_9_Figure_9.jpeg)

Figure 4: The DAG construction given subjects and their corresponding weights.

## A.2 S-DAG Construction

Once a question is analyzed, we construct a Subject Dependency Acyclic Graph (S-DAG) to represent its ground-truth label. How is the S-DAG constructed based on the subjects and their associated weights? A single question may involve multiple subjects, although it typically centers on a dominant domain. For example, a complex chemistry problem may also require mathematical and biological knowledge. In such cases, chemistry is considered the dominant subject, while mathematics and biology serve as supporting subjects.

To model the flow of knowledge among these subjects, we define directed edges in the S-DAG from supporting subjects to the dominant subject. This directionality reflects the information flow from subjects with lower weights (indicating less emphasis)

### Algorithm 2: GNN Training for S-DAG Generation

**Input:** Training dataset  $\mathcal{D} = \{(\mathcal{Q}_i, \mathcal{G}_{\mathcal{Q}}^i)\}_{i=1}^N$ , where  $\mathcal{Q}_i$  is a question and  $\mathcal{G}_{\mathcal{Q}}^i = \{\mathcal{S}_{\mathcal{Q}}^i, \mathcal{A}_{\mathcal{Q}}^i\}$  is the ground truth S-DAG. Randomly initialized node embedding  $\{\mathbf{h}_i\}_{i\in\mathcal{V}}$ . An initial fully connected graph  $\mathcal{G}=\{\mathcal{V},\mathcal{E}\}$ .

**Output:** Trained GNN generator module  $f_{\theta}$ 

- 1: for each sample  $(Q, \mathcal{G}_Q) \in \mathcal{D}$  do
- **Step 1: Question Embedding** 2:
- 3: Embed the question:  $\mathbf{h}_\mathcal{Q} \leftarrow \mathrm{BERT}(\mathcal{Q})$
- Initialize features of subject nodes:  $\mathbf{x}_i^{(0)} \leftarrow \text{MLP}_{\text{init}}([\mathbf{h}_i; \mathbf{h}_{\mathcal{Q}}])$  for  $i \in \mathcal{V}$ 4:
- **Step 2: S-DAG Generation** 5:
- Update the node features:  $\mathbf{x}_i = f_{\theta}(\mathcal{G}, \mathbf{x}_i^{(0)})$ 6:
- 7: Node prediction:  $\hat{s}_{\mathcal{Q}}^i \leftarrow \text{MLP}_{\text{node}}(\mathbf{x}_i)$  for each  $i \in \mathcal{V}$
- Edge prediction:  $\hat{a}_{\mathcal{Q}}^{i\bar{j}} \leftarrow \mathrm{MLP_{node}}(\mathbf{x}_i; \mathbf{x}_j; \mathbf{h}_{\mathcal{Q}_i})$  for each  $(i,j) \in \mathcal{E}$ Step 3: Compute Loss and Gradient Update 8:
- 9:
- Loss for node and edge prediction:  $\mathcal{L} = \lambda_{\text{node}} \cdot \text{BCE}(\hat{s}_{\mathcal{Q}}^i, s_{\mathcal{Q}}^i) + \lambda_{\text{edge}} \cdot \text{BCE}(\hat{a}_{\mathcal{Q}}^{ij}, a_{\mathcal{Q}}^{ij})$  for each  $i \in \mathcal{V}$  and each  $(i, j) \in \mathcal{E}$ 10:
- Backpropagate the loss  $\mathcal{L}$  and update the model parameters  $f_{\theta}$ ,  $MLP_{init}$ ,  $MLP_{node}$ ,  $MLP_{edge}$ 11:
- 12: **end for**

Table 6: Subject-specific base models with hugging face links.

| Subject          | Base Model                  | Link                                                                                         |
|------------------|-----------------------------|----------------------------------------------------------------------------------------------|
| Chemistry        | Llama2-13B-Chat             | https://huggingface.co/juntaoyuan/chemistry-assistant-13b                                    |
| Math             | Deepseek-7B                 | https://huggingface.co/deepseek-ai/deepseek-math-7b-instruct                                 |
| Biomedical       | Llama-3-8B                  | https://huggingface.co/ContactDoctor/Bio-Medical-Llama-3-8B                                  |
| Biology          | BioMistral-7B               | https://huggingface.co/BioMistral/BioMistral-7B                                              |
| Computer Science | Qwen2.5-7B                  | https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct                                        |
| Physician        | Llama-3-8B                  | https://huggingface.co/YiDuo1999/Llama-3-Physician-8B-Instruct                               |
| Law              | Llama3-8B                   | https://huggingface.co/ricdomolm/lawma-8b                                                    |
| Economics        | Mistral-7B                  | https://huggingface.co/tim9510019/Mistral-7B-Economic_zephyr_231023                          |
| Business         | Llama-3.1-8B                | https://huggingface.co/warrencain/Business_Consulting_Finetune_Llama_3.1_8b                  |
| History          | Deepseek-R1-distill-Qwen-7B | https://huggingface.co/Doppelfelix/Deepseek-r1-history-expert                                |
| Engineering      | Llama2-7B-Chat              | https://huggingface.co/Frrrrrrrank/Llama-2-7b-chat-hf-process_engineering_one_firsttwokap_v3 |
| Psychology       | Llama-3.1-8B                | https://huggingface.co/dentist9111/Llama-3.1-8B-bnb-4bit-samhog_psychology                   |
| Philosophy       | Mistral-12B                 | https://huggingface.co/EpistemeAI/Mistral-Nemo-Instruct-12B-Philosophy-Math                  |
| Health           | Llama3-8B                   | https://huggingface.co/m42-health/Llama3-Med42-8B                                            |

to those with higher weights (indicating greater emphasis). Consequently, the S-DAG captures the hierarchical and integrative structure of subject dependencies within the question.

In practice, subjects with weights below a predefined threshold (e.g., 0.1) are considered negligible and are discarded. Among the remaining subjects, those with weights exceeding the average (e.g., 1/4 = 0.25 for four subjects) are designated as dominant subjects. The rest are treated as supporting subjects and are connected to the dominant nodes via directed edges, reflecting their auxiliary role in the reasoning process. An example of S-DAG construction is illustrated in Figure 4.

The constructed S-DAGs serve as supervision signals for training the GNN module. This enables the model to learn to predict relevant subjects and their dependencies during inference. The full training procedure is detailed in Alg. 2.

## **Multi-Agent Collaborative Inference**

#### Model Pool

Given the subject decomposition provided by the constructed S-DAG, we are able to precisely identify the domain expertise required to solve each question. This enables targeted selection of specialized expert agents—language models fine-tuned for specific subjects.

To support this, we curate a Model Pool consisting of small yet high-performing subject-specialized LLMs, sourced primarily from the Hugging Face model repository. Each model is carefully chosen based on its training corpus, fine-tuning objectives, and performance within its respective domain. Through the LLM subject capability profiling process, we can conduct precise subject-LLM matching, ensuring that each subject node in the S-DAG is handled by an appropriately skilled agent.

The full list of expert models, along with their associated subjects and Hugging Face links, is presented in Table 6. These models collectively enable a modular, scalable approach to complex multi-subject reasoning, offering both computational efficiency and domain fidelity.

![](_page_11_Picture_0.jpeg)

Figure 5: The S-DAG structured multi-agent information flow.

Table 7: Prompts for S-DAG structured multi-agent information flow.

| Agent                | Prompt                                                                                                                                                                                                                                                                                                                                                                                                          |
|----------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Subject Expert Agent | You are an expert in [Subject]. Your task is to analyze the following question based on your domain<br>knowledge. Question: {Q} Please provide a clear and concise explanation or answer strictly from<br>the perspective of [Subject].                                                                                                                                                                         |
| Supporting Agent     | You are an expert in [Subject]. Another agent has provided information from [Supporting Subject],<br>which may be relevant to your reasoning. Question: {Q} Supporting Information from [Support<br>ing Subject]: {Support Content} Please incorporate the above supporting information into your<br>domain-specific reasoning, and produce a coherent, informed response from the perspective of<br>[Subject]. |
| Dominant Agent       | You are the lead [Subject] expert responsible for integrating multi-disciplinary information to an<br>swer the following complex question. Question: {Q} You have received input from other experts:<br>- [Subject A]: {Content A} - [Subject B]: {Content B} Please synthesize the provided informa<br>tion and generate a comprehensive final answer that reflects the reasoning across these domains.        |

# B.2 Multi-Agent Information Flow

Once the subject-directed acyclic graph is constructed from a heterogeneous question, we can proceed to the subject–LLM pairing phase based on the LLM subject capability profiles. In this step, each node in the S-DAG—representing a specific subject—is assigned to a domain-specialized expert LLM, enabling targeted reasoning within that domain.

We define three types of agents based on their structural position in the S-DAG:

- Subject Expert Agents: These are agents corresponding to the starting nodes, which initiate the reasoning process. They do not receive input from other agents but process the raw question directly within their area of expertise.
- Supporting Agents: Associated with intermediate nodes, these agents integrate information received from upstream agents and generate enriched outputs. They act as conduits, facilitating inter-subject reasoning and knowledge flow across the S-DAG.
- Dominant Agent: This agent corresponds to the final node in the graph. It receives input from multiple supporting agents but does not transmit information further. The Main Agent is responsible for producing the final answer, synthesizing interdisciplinary insights gathered throughout the reasoning chain.

All agents receive the original question and operate collaboratively within the information flow defined by the S-DAG. Their internal processing and response strategies are guided by the structural role they play—whether initiating, transforming, or concluding the reasoning. This multi-agent orchestration enables both modular specialization and coherent integration across subject domains, reflecting the layered nature of complex human reasoning. Figure 5 shows the multi-agent information flow under S-DAG. Table 7 shows the prompts for different types of agents.

# C Ablation Study

To better understand the contribution of each component in our framework, we conduct a series of ablation experiments on the MMLU-Pro, GPQA, and MedMCQA benchmarks. Specifically, we evaluate the effectiveness of the GNN module for S-DAG generation, the LLM subject capability profiling for model selection, and the directed acyclic graph topology itself. Results are summarized in Table 4.

Table 8: Prompts for baselines. List of prompts used in experiment.

| Baseline            | Prompt                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Single-Model Method | Can you solve the problem? {Q} Explain your reasoning. Your final answer should be with the<br>format: < <answer>&gt;, at the end of your response.</answer>                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Self-Refine         | 1. Initial Answer: Can you solve the problem? {Q} Explain your reasoning. Your final answer<br>should be with the format: < <answer>&gt;, at the end of your response. 2. Feedback: The ques<br/>tion is: {Q} Please identify issues or limitations in the following answer and suggest improve<br/>ments: {answer} 3. Refine: The problem is: {Q} The original answer was: {answer} The feedback<br/>is:\n{feedback content}\n\nNow give an improved correct answer based on this feedback. Your<br/>final answer should be with the format: &lt;<answer>&gt;, at the end of your response.</answer></answer> |
| Multi-Agent Debate  | 1. Statement: You are Agent [A]. Can you solve the problem? Q Explain your reasoning. 2. Rebut<br>tal: You are Agent [A]. Rebut Agent [B]'s argument below: Agent [B] said: {response} 3. Judge:<br>You are the Judge. Based on both arguments and rebuttals, decide which Agent has a stronger case.<br>Agent [A] said: {response} Agent [B] said: {response}                                                                                                                                                                                                                                                 |

To evaluate efficiency, we report the average inference time and number of LLM calls per instance across the test set. For each sample, inference time is measured from the moment the question is input into the system until the final answer is generated, including all model invocation, data routing, and inter-agent communication. The number of LLM calls is computed by counting each individual model invocation used to process subject nodes within the S-DAG. For example, if three subject nodes are activated and each requires a single forward pass through its assigned expert model, this counts as three LLM calls. The final reported values are averaged over all test questions to reflect overall system efficiency. All experiments are conducted under controlled conditions on the same hardware to ensure fair comparison.

## C.1 GNN Module

The GNN module plays a central role in generating the S-DAG, which guides multi-agent collaboration. While it is possible to rely solely on LLMs to extract subject annotations and manually construct a DAG, this approach is inefficient and error-prone. LLM outputs tend to be noisy, inconsistent across runs, and may lack a coherent structure.

In contrast, our trained GNN is able to learn subject relevance and interdependencies across a large number of annotated samples, yielding robust and repeatable DAGs. To evaluate the GNN's contribution, we replace it with an LLM-based rule system that directly constructs the S-DAG using raw subject weights from the LLM.

## C.2 LLM Profile

The LLM profile component enables accurate subject–model matching by assigning each expert model a capability score for each subject domain. Without this profiling mechanism, subject nodes in the S-DAG are matched to expert LLMs randomly, ignoring domain expertise.

To measure the impact of profiling, we compare our system against a variant where expert agents are selected uniformly at random for each subject. This leads to inconsistent or suboptimal assignments, resulting in a noticeable performance drop. The ablation confirms that subject-aware model selection is critical for effective multi-agent collaboration, as it ensures that each subtask is handled by the most capable model based on prior subject-specific evaluations.

## C.3 Graph Topology

Our framework relies on a directed acyclic graph (DAG) structure to represent the subject-level reasoning flow, enabling information to propagate from supporting subjects to dominant ones in a structured manner. To assess the importance of this topology, we compare the directed S-DAG against a fully connected subject graph, where all subject nodes can freely exchange information without structural constraints.

Although the fully connected variant allows maximum communication among agents, it introduces redundant interactions and potential reasoning loops, increasing inference cost and ambiguity. The directed version not only improves accuracy but also reduces inference time and LLM calls. These results highlight the importance of enforcing a sparse and efficient graph structure.

# D Broader Impacts

Our work introduces S-DAG, a modular framework for multi-subject reasoning that leverages lightweight, domain-specific language models. By enabling more efficient and scalable deployment compared to large monolithic LLMs, S-DAG holds promise for democratizing access to advanced AI systems, particularly in education, healthcare, and scientific research. Its graph-structured design promotes transparency and modularity, supporting safer and more controllable reasoning pipelines. However, potential risks must also be acknowledged. The framework relies on subject-specific models that may vary in quality or harbor domain-specific biases, which could propagate through the reasoning process. Furthermore, improper deployment in high-stakes applications without adequate validation may lead to unintended consequences. Future work should explore robust evaluation standards, fairness auditing, and safeguards to ensure responsible use of S-DAG in real-world scenarios.