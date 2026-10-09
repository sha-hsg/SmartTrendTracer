# OpenSkillEval: Automatically Auditing the Open Skill Ecosystem for LLM Agents

Jiahao Ying<sup>1</sup>\*, Boxian Ai<sup>2</sup>\*, Wei Tang<sup>3</sup>, Siyuan Liu<sup>2</sup>, Yixin Cao<sup>2†</sup>

<sup>1</sup>Singapore Management University

<sup>2</sup>Institute of Trustworthy Embodied AI, Fudan University

<sup>3</sup>Joy Future Academy, JD

## **Abstract**

Skills, i.e., structured workflow instructions distilled for large language models (LLMs), are becoming an increasingly important mechanism for improving agent performance on real-world downstream tasks. However, as the open-source skill ecosystem rapidly expands, it remains unclear how different models and agent frameworks interact with skills, how to evaluate skill quality, and how users should select skills under practical cost-performance trade-offs. In this paper, we present OPENSKILLEVAL, an automatic evaluation framework for both skill-augmented agent systems and the skills themselves. Instead of relying on static benchmarks, OPENSKILLEVAL automatically constructs realistic task instances from evolving real-world artifacts across five categories of downstream applications: presentation generation, front-end web design, poster generation, data visualization, and report generation. It further collects and organizes community-contributed skills for controlled comparison under unified task settings. Using more than 600 dynamically generated task instances and 30 open-source skills, we conduct a systematic evaluation of state-of-the-art models and agent frameworks. Our results show that skill availability does not guarantee effective skill usage, that the benefit of skill augmentation depends strongly on both the underlying model and the agent framework, and that many publicly popular skills do not consistently outperform base agents without skills. These findings highlight the need for dynamic, task-grounded evaluation and provide practical insights into the design, selection, and deployment of skills for LLM agents. Additional cases and benchmark resources are available on the project website: https://yingjiahao14.github.io/OpenSkillEval-Web/.

## 1 Introduction

Recent advances in increasingly capable large language models (LLMs) [1, 2], together with the rapid development of agent client frameworks [3, 4], have created a promising opportunity to deploy models as autonomous agents for complex downstream tasks, including report generation, document management, and web design. However, because agentic tasks are often open-ended, the overall behavior of an agent can be difficult to predict, and in many challenging settings the agent's intrinsic capability alone may be insufficient for reliable task completion. To better enable models to handle such structured yet complex workflows, developers often formalize personal experience or accumulated best practices into explicit procedures and distill them into structured instructions for agents. These workflow-oriented, formatted instructions are commonly referred to as skills [5].

Given the promise of skills for augmenting agent capabilities in downstream task completion, strong community participation over the past few months has led to the creation and integration of a large

<sup>\*</sup>Equal contribution.

<sup>†</sup>Corresponding Author

number of skills into the ecosystem for LLM agents. However, this rapid growth has also introduced several important challenges. First, it remains unclear how different agent frameworks perform on downstream tasks in general, and how they interact with the added skill during execution. Lack of systematic evaluation makes it difficult to assess their actual effectiveness. As a result, users may struggle to choose suitable agents for downstream tasks. If an agent lacks the capability to properly execute a provided skill, the practical value of skill augmentation can be greatly reduced. On the other hand, if an agent is already sufficiently strong to solve the task on its own, introducing skills may bring only limited benefit while still increasing execution cost. Second, individually distilled skills may reflect only partial or subjective experience, which can limit their generalizability. As the number of available skills continues to grow, it also becomes increasingly unclear how to select the most appropriate skills for prompting, especially when users must balance performance and cost. In addition, the repeated submission of redundant or low-quality skills imposes substantial maintenance overhead on the community and contributes to the bloating of the overall ecosystem.

To address these challenges, we propose OpenSkillEval, an automatic evaluation framework for both skill-augmented agent systems and the skills themselves in downstream applications. Instead of relying on static benchmarks, OpenSkillEval dynamically generates test cases that continuously reflect evolving user needs, enabling a more realistic, timely, and comprehensive evaluation setting. Based on these dynamically constructed task instances, we evaluate the effectiveness and efficiency of different models and agent frameworks, both with and without skill augmentation, across diverse downstream tasks. Moreover, by collecting skill sets from the open-source community for each target application, OpenSkillEval enables controlled comparisons of different skills under the same task setting, making it possible to analyze their relative quality, robustness, and transferability. Across five major categories of real-world applications and more than 600 tasks, we evaluate a range of state-of-the-art architectures and derive several important findings: 1) We find that the presence of a skill does not guarantee that an agent will actually use it effectively. Across different client frameworks, models often fail to invoke skills at the appropriate stage of task execution, and in many cases do not faithfully follow the provided skill instructions at all. This suggests that in realistic online settings, where the context is more complex and noisy, carefully designed skills may still be under-utilized or even ignored by the agent (Section [3.1\)](#page-4-0); 2) We observe substantial differences across agent frameworks in how effectively they leverage skill augmentation. In some cases, a weaker base model can achieve performance comparable to that of a stronger model when paired with well-designed skills and a suitable framework. However, when the underlying model is intrinsically weak at solving a task, simply adding skills does not reliably produce meaningful gains (Section [3.2\)](#page-6-0); 3) We show that skill quality varies substantially, even among publicly popular open-source skills. In many cases, skill-augmented agents do not outperform their corresponding base agents without skills. Our findings further highlight that poorly designed or weakly aligned skills can not only fail to help but may also introduce additional execution cost. At the same time, our analysis provides practical takeaways on skill format and design, as discussed in Section [3.3.](#page-8-0)

## 2 OpenSkillEval Framework

To effectively evaluate the rapidly growing and increasingly bloated open skill ecosystem for LLM agents, we design OpenSkillEval as a sustainable and maintainable framework for real-world downstream application tasks. Accordingly, we decompose the system into several core components. The first component is an automatic test case generation pipeline, which constructs representative evaluation instances for target downstream tasks grounded in realistic user needs (Section [2.1\)](#page-2-0). The second component is a skill collection and organization pipeline, which curates skills from the open-source community and organizes them by task category to support continuous tracking of skill development (Section [2.2\)](#page-3-0). The final component is an evaluation pipeline that systematically measures the effectiveness of skills in downstream settings. This evaluation considers not only the quality of the final generated artifacts, but also the intermediate agent trajectories, which provide insights into whether and how an agent appropriately invokes and applies skills during task execution in real-world task environments (Section [2.3\)](#page-4-1). Based on these components, OpenSkillEval enables efficient and dynamic auditing of the open skill ecosystem from two complementary perspectives: agent-level comparison and skill-level comparison. Figure [1](#page-2-1) presents an overview of the framework. In the following subsections, we describe the implementation of each component.

<span id="page-2-1"></span>![](_page_2_Picture_0.jpeg)

Figure 1: Overview of the OpenSkillEval framework. The framework supports automatic test case generation for five core task categories by reflecting evolving user needs. It further enables automatic evaluation from two complementary perspectives: (1) analysis of model trajectory traces to study how skills are used within skill-augmented agent systems, and (2) assessment of the quality of the final artifacts produced under skill augmentation.

#### <span id="page-2-0"></span>2.1 Automatic Case Generation

To ensure the practical relevance and feasibility of our evaluation, we focus on five categories of commonly used real-world downstream tasks: presentation generation, front-end web design, poster generation, data visualization, and report generation. We select these tasks because they are representative of common real-world applications, require nontrivial multi-step reasoning and tool use, and typically produce concrete artifacts that can be directly evaluated. To construct test cases that reflect realistic user needs in these scenarios, we adopt an Artifact-driven Case Generation Strategy. Instead of manually writing task instructions from scratch, we begin with existing highquality artifacts and infer the underlying user requests that could have led to their creation. This reverse construction process allows us to build evaluation instances that are more closely aligned with real-world usage patterns and expected outputs. Concretely, each task category instantiates this artifact-driven strategy through a three-stage pipeline. First, we automatically collect artifacts or source materials (S) from diverse external repositories as the content basis for reconstructing realistic user intents. Second, we perform task extraction, where LLMs analyze the collected materials under predefined schemas to construct structured task specification (T) together with its corresponding natural-language instruction (I). Here, the task specification captures the underlying user intent, constraints, and expected outputs implied by the artifact or its supporting context. Third, we apply a validation procedure to verify that the extracted task specification is internally consistent and compatible with the source content, ensuring that the resulting task instances are both coherent and realistic. Below, we describe the source selection and extraction process for each task category.

**Presentation Generation.** For presentation (hereafter PPT) generation, we collect publicly available, up-to-date, and information-dense webpages and documents, such as benchmark leaderboards, industry reports, open-data portals, and academic papers, that naturally lend themselves to slide-deck summarization and restructuring. Each source is crawled, snapshot-preserved, and then processed through an LLM-based pipeline to produce a slide-level task specification with explicit per-slide content goals, thereby forming realistic presentation-generation requests grounded in real-world.

**Front-end Web Design.** For web design, we directly use existing websites as target artifacts. Specifically, we auto-curate publicly accessible and high-quality websites from design award platforms (e.g., Awwwards) and product discovery sites (e.g., SaaS Landing Page), and organize them along

two dimensions: site type and industry domain. For each website, we capture its rendered layout, navigation structure, and interactive components, and then use LLM-based reverse engineering to convert these observations into a structured design specification for the corresponding task instance.

**Poster Generation.** To cover a diverse set of common real-world scenarios, we automatically collect source content associated with practical poster-creation needs, such as data-report visualization, product promotion, event advertising, and social advocacy. The collected materials span multiple domains, including technology, health, environment, and business, and are organized according to these poster-use scenarios. We then use LLMs to transform each source into a poster task specification that defines the target audience, core message, and key content blocks to be presented.

**Data Visualization.** Unlike the previous task categories, data visualization does not start from existing artifacts as direct task inputs. Instead, we first survey high-quality visualization examples from open data portals (e.g., Our World in Data) and scientific publications to derive a taxonomy of visualization types, subject domains, and analytical goals. Based on this taxonomy, we sample task configurations and prompt LLMs to instantiate them into concrete task specifications. For each resulting specification, we further generate a matching data table that is consistent with the target visualization and analytical objective, enabling end-to-end evaluation of visualization generation.

**Report Generation.** For report generation, we build tasks on top of publicly available, real-world tabular datasets from open-data platforms (e.g., Kaggle), covering diverse domains such as e-commerce, finance, healthcare, education, and technology. Based on these grounded data sources, we use LLMs to construct report-generation task specifications along several key dimensions, including report type, required sections, and analysis dimensions. Each task specification is explicitly grounded in the underlying dataset by linking the requested analyses and report components to concrete data columns.

For each generated instance, we retain three components: the source package S (including source\_brief.md and, when applicable, associated data files), the structured task specification T (task\_input.json), and the natural-language instruction I (instruction.md). Since these downstream tasks do not admit a single canonical answer, our validation procedure does not rely on reference outputs. Instead, in the third stage, we employ a verifier LLM to assess whether T and I are both information-complete and well-grounded in the source package S, and filter out instances that are inconsistent, underspecified, or weakly supported by the source content. Because the entire pipeline is automated, the benchmark can be continuously refreshed as underlying content sources evolve, allowing it to better keep pace with changing real-world user needs. In the current version, we use Claude-4.6-Opus and GPT-5.2 as the primary generators in the pipeline, resulting in a total of 677 task instances. The distribution of these instances across task categories is shown in Figure 2a, and the task schemas together with additional case studies are provided in Appendix A.3.

<span id="page-3-1"></span>![](_page_3_Picture_5.jpeg)

| Task                       | # | Skills                                                                                                                         |
|----------------------------|---|--------------------------------------------------------------------------------------------------------------------------------|
| Presentation<br>Generation | 6 | <pre>anthropics-pptx, frontend-slides, minimax-pptx, powerpoint-pptx, ppt-master, pptx-manipulation</pre>                      |
| Front-end<br>Web Design    | 8 | frontend-design-ultimate, web-design-expert, loom, seo-local-business, SuperDesign,\nui-styling, ui-ux-pro-max, web-frameworks |
| Poster<br>Generation       | 4 | antv-infographic, paper-poster, canvas-design, visualize                                                                       |
| Data<br>Visualization      | 6 | anthropics, mermaid-tools, mermaidjs, tufte, visual-explainer, visualize                                                       |
| Report<br>Generation       | 6 | claude-office, chatgpt-pdf, excel-report, business-auto, clawfu, devkit                                                        |

(b) Skills selected for each task (30 total). Names are clickable.

## <span id="page-3-0"></span>2.2 Skills Collection

The open-source skill ecosystem is actively maintained and continues to evolve. We therefore comprehensively collect task-relevant skills from multiple public repositories, including clawhub.ai, skills.sh,

[openskills.space,](https://openskills.space/) and [skillsmp.com.](https://skillsmp.com/) Because community-contributed skills vary substantially in quality, we do not include every retrieved skill in our evaluation. As shown later in our results (Section [3.3\)](#page-8-0), many skill-augmented settings do not outperform the corresponding base agent. We therefore restrict our benchmark to skills with relatively high community adoption, using download counts as a filtering signal under a cost-conscious setting. Following this procedure, we collect a total of 30 skills for evaluation. Detailed statistics and skill information are provided in Table [2b.](#page-3-1) [3](#page-4-2)

## <span id="page-4-1"></span>2.3 Automatic Evaluation Pipeline

To comprehensively and efficiently evaluate skill-augmented agents, we design an automatic evaluation pipeline from two complementary perspectives: trajectory trace analysis and artifact analysis. The former focuses on the agent's execution process, while the latter assesses the quality of the final task output. For trajectory trace analysis, we leverage the Agent Trajectory Interchange Format (ATIF) [\[6\]](#page-14-0), a unified representation that standardizes execution traces across different agent frameworks and enables consistent parsing and analysis across otherwise heterogeneous systems. Building on ATIF, we further introduce an agent-as-judge procedure that first decomposes each skill into a sequence of intended workflow steps, and then compares these steps against the actual agent trajectory at a finer granularity. This process allows us to evaluate whether the agent invokes the skill at the appropriate stage, whether it follows the prescribed workflow, and to what extent the injected skill shapes the overall execution process.

Artifact analysis evaluates whether the final outputs produced by skill-augmented agents achieve the desired quality in realistic application settings. Concretely, for each task category, we design task-specific evaluation criteria to automatically assess output quality. Our metric design is informed by prior work, such as PPTEval [\[7\]](#page-14-1), GenEval [\[8\]](#page-14-2), and WebArena [\[9\]](#page-14-3), while being adapted to the characteristics of each downstream task. Across task categories, we include several shared dimensions, including *completeness*, which measures whether the output satisfies the requirements specified in the task specification, as well as *content quality* and *visual design*, whose exact definitions are adjusted according to the task type. Beyond these shared criteria, we further design targeted evaluation procedures for tasks that require more specialized assessment. For web design, in addition to visual evaluation based on rendered screenshots, we use agent-based interaction to simulate human clicking and navigation behavior, allowing us to assess functional completeness and collect finer-grained interface states for downstream quality evaluation. For report generation and data visualization, where factual and numerical correctness is particularly important, we explicitly evaluate *data accuracy*. In report generation, this is assessed through code-based analysis of whether the reported values and conclusions are consistent with the underlying data. In data visualization, we combine artifact inspection with trajectory analysis to verify whether the generated charts correctly use and represent the intended data. More detailed evaluation matrix information is shown in Appendix [A.2.](#page-17-0)

## 3 Experimental Results

Based on the proposed OpenSkillEval framework, we conduct a systematic evaluation of a range of state-of-the-art agent systems together with their corresponding foundation models. Our evaluation includes Claude Code [\[3\]](#page-13-2) with the Claude 4.6 series [\[2\]](#page-13-1), Codex [\[4\]](#page-13-3) with the GPT series [\[10\]](#page-14-4), Gemini CLI [\[11\]](#page-14-5) with the Gemini 3.1 Pro [\[12\]](#page-14-6), Kimi Code CLI [\[13\]](#page-14-7) with the Kimi K2.6 [\[14\]](#page-14-8) series, as well as adapted Minimax models [\[15\]](#page-14-9) and DeepSeek V4 Pro [\[16\]](#page-14-10) integrated into the Claude Code framework. More detailed experimental settings are provided in Appendix [A.1.](#page-17-1) Using the automatically constructed benchmark, we analyze skill-augmented agents from multiple perspectives, including trajectory trace behavior (Section [3.1\)](#page-4-0), overall agent performance (Section [3.2\)](#page-6-0), and differences in skill quality (Section [3.3\)](#page-8-0).

## <span id="page-4-0"></span>3.1 Trajectory Trace Analysis: How Agents Follow Skills

Before conducting the large-scale evaluation, we first perform preliminary trajectory-level analyses to better understand how agents actually use provided skills in practice. For this purpose, we place each target skill in the designated initialization path of each CLI-based agent framework, reflecting

<span id="page-4-2"></span><sup>3</sup>Because these repositories are continuously updated by the community, the collected skill set is time-sensitive and should be understood as a snapshot of the open skill ecosystem at the time of collection.

<span id="page-5-0"></span>![](_page_5_Figure_0.jpeg)

Figure 3: Trajectory-level analysis of how different agent access and follow provided skills. (a) Statistics of SKILL.md access under the default and *force-using* settings, including the proportion of cases in which the skill is explicitly read and the average trajectory step at which it is first accessed. (b) Step-level adherence to skill workflows after skill access, showing the mean proportion of prescribed steps that are followed, skipped, or contradicted across agents under the two settings.

the common real-world setting in which users download skills into an agent-accessible environment. We then prompt different agents to complete the same downstream tasks under the generated task instructions, and analyze the resulting execution traces to examine whether and how the injected skill is used during task completion. Our first observation is that, under the default setting, the provided skill often remains effectively unused. As shown in Figure 3a, when randomly sampling 100 task instances per agent across task categories, we find that agents explicitly read the corresponding skill.md file in only around 48% of cases on average. Even for strong models such as Claude Opus 4.6, the read rate is only around 20%. This suggests that simply placing a skill in the accessible environment does not guarantee that the agent will actively discover and use it during execution. To enable controlled evaluation of the potential benefits of skill augmentation, we further consider a force-using setting that follows the intended skill-usage strategy recommended by agent frameworks. Specifically, we augment the task instruction with an explicit directive to invoke the designated skill. As shown in Figure 3a, this intervention substantially increases the probability that agents read and use the provided skill, raising the average read rate to 94%, and also shifts skill access to earlier stages of the execution trajectory, from an average of 4.4 steps before reading to 3.3 steps.

However, forcing explicit skill usage does not eliminate autonomous agent behavior. By further performing fine-grained trajectory analysis on skills with explicit workflow steps, we find that, as shown in Figure 3b, even after agents have explicitly read the provided skills, they still skip prescribed steps (Skip) and, in some cases, exhibit behaviors that substantially deviate from the intended procedure (Contra). These results indicate that the force-using setting can largely mitigate the problem of skills being ignored and can encourage earlier skill access, but agents still retain substantial autonomy in deciding how to execute a task. This phenomenon is particularly notable for Claude Opus 4.6. Although forcing significantly improves skill access for this model, its overall usage rate still remains noticeably below that of several other agents. A closer analysis reveals substantial variation across task categories: for data visualization and report generation, the skill read rate remains below 50%, whereas for other, like presentation generation it exceeds 95%. This pattern suggests a more selective style of skill usage, in which the agent appears to consult skills only when it deems them especially helpful for the task. Our trajectory trace analysis further supports this interpretation: before reading the skill.md file, Claude Opus 4.6 tends to spend more steps analyzing the task itself, as reflected by the later step at which skill.md is first accessed in Figure 3a. Such selective behavior resembles the more deliberate and rational decision-making patterns previously observed for stronger models in related settings [17], such as retrieval-augmented generation. A similar tendency has also been noted by the community [18]. Taken together, these findings suggest that agents exhibit nontrivial autonomous decision-making in whether and how they use skills.

#### **Takeaway**

Simply placing a skill in an agent-accessible environment does not guarantee that the agent use it. Even when skill usage is explicitly enforced, agents may still selectively skip or deviate from prescribed workflow steps. This suggests that skill effectiveness in practice depends not only on skill quality, but also on how the agent autonomously chooses to recognize, access, and follow the skill during execution.

Since such agent autonomy is itself an important part of how skill augmentation functions in practice, we preserve this behavior in our evaluation. Accordingly, in the subsequent experiments, we evaluate skill augmentation under both *no-skills* and *force-using skills* settings, and assess performance primarily based on the final output artifacts (e.g., screenshots and generated results).

## <span id="page-6-0"></span>3.2 Model Comparison: How Different Agents Perform

<span id="page-6-1"></span>

| Metric                              | Claude Onus 4.6                   | Claude Sonnet 4.6 | GPT-5.5                           | GPT-5.3-codex   | GPT-5.2                           | Gemini 3.1 Pro    | DeenSeek V4     | Kimi K2.6       | MiniMax M2.7    |
|-------------------------------------|-----------------------------------|-------------------|-----------------------------------|-----------------|-----------------------------------|-------------------|-----------------|-----------------|-----------------|
|                                     | •                                 |                   | 011-0.0                           | OF P-3.3-codex  | 01 1-0.2                          | - Gennin S.F.I IV | Deepbeek 14     | Timir R2.0      | TAMINIAX NI2.7  |
| Presentation Gener                  | 11 0                              |                   |                                   |                 |                                   |                   |                 |                 |                 |
| Content quality                     | $4.48 \pm 0.35$                   | $4.44 \pm 0.41$   | $4.41 \pm 0.39$                   | $3.55 \pm 0.52$ | $3.74 \pm 0.49$                   | $3.78 \pm 0.43$   | $4.33 \pm 0.33$ | $4.14 \pm 0.53$ | $4.18 \pm 0.42$ |
| Visual design                       | $3.98 \pm 0.30$                   | $3.92 \pm 0.27$   | $4.01 \pm 0.28$                   | $3.04 \pm 0.46$ | $3.23 \pm 0.50$                   | $2.99 \pm 0.64$   | $3.79 \pm 0.29$ | $3.57 \pm 0.52$ | $3.73 \pm 0.36$ |
| Completeness                        | $4.68 \pm 0.54$                   | $4.63 \pm 0.67$   | $4.66 \pm 0.70$                   | $4.07 \pm 1.08$ | $4.46 \pm 0.74$                   | $4.24 \pm 0.67$   | $4.67 \pm 0.58$ | $4.53 \pm 0.75$ | $4.44 \pm 0.77$ |
| Fidelity                            | $4.51 \pm 0.53$                   | $4.31 \pm 0.52$   | $4.88 \pm 0.35$                   | $4.02 \pm 1.13$ | $4.84 \pm 0.38$                   | $4.61 \pm 0.51$   | $4.20 \pm 0.49$ | $4.46 \pm 0.72$ | $4.18 \pm 0.61$ |
| Task avg.                           | 4.41                              | 4.33              | 4.49                              | 3.67            | 4.07                              | 3.90              | 4.25            | 4.17            | 4.13            |
| Poster Generation poster-generation |                                   |                   |                                   |                 |                                   |                   |                 |                 |                 |
| Content quality                     | $4.56 \pm 0.71$                   | $4.37 \pm 0.75$   | $\textbf{4.60} \pm \textbf{0.71}$ | $4.42 \pm 0.91$ | $4.49 \pm 0.76$                   | $4.43 \pm 0.70$   | $4.39 \pm 0.74$ | $4.49 \pm 0.73$ | $4.20 \pm 0.81$ |
| Visual design                       | $4.00 \pm 0.60$                   | $3.72 \pm 0.77$   | $3.82 \pm 0.58$                   | $3.19 \pm 0.76$ | $3.11 \pm 0.83$                   | $3.39 \pm 0.84$   | $3.55\pm0.75$   | $3.48 \pm 0.84$ | $3.10\pm0.88$   |
| Completeness                        | $\textbf{4.12} \pm \textbf{0.53}$ | $3.98 \pm 0.66$   | $3.97 \pm 0.63$                   | $3.44 \pm 0.79$ | $3.43 \pm 0.84$                   | $3.41 \pm 0.80$   | $3.90 \pm 0.65$ | $3.68 \pm 0.74$ | $3.35 \pm 0.85$ |
| Task avg.                           | 4.23                              | 4.02              | 4.13                              | 3.68            | 3.67                              | 3.74              | 3.94            | 3.88            | 3.55            |
| <b>Ⅲ</b> Data Visualization         | data-visualizatio                 | n                 |                                   |                 |                                   |                   |                 |                 |                 |
| Insight expression                  | $4.40 \pm 0.62$                   | $4.22 \pm 0.70$   | $4.04 \pm 0.77$                   | $2.79 \pm 1.12$ | $3.15 \pm 1.10$                   | $3.66 \pm 1.00$   | $3.96 \pm 0.73$ | $3.82 \pm 0.85$ | $3.31 \pm 1.03$ |
| Visual quality                      | $4.06 \pm 0.62$                   | $3.99 \pm 0.71$   | $3.54 \pm 0.79$                   | $3.13 \pm 0.86$ | $2.92 \pm 0.93$                   | $3.39 \pm 0.92$   | $3.59 \pm 0.72$ | $3.52 \pm 0.82$ | $3.30 \pm 0.91$ |
| Completeness                        | $4.80 \pm 0.42$                   | $4.67 \pm 0.57$   | $4.58 \pm 0.67$                   | $2.87 \pm 1.35$ | $3.46\pm1.25$                     | $4.03 \pm 1.03$   | $4.43 \pm 0.71$ | $4.27 \pm 0.88$ | $3.62 \pm 1.13$ |
| Data accuracy                       | $4.98 \pm 0.15$                   | $4.93 \pm 0.25$   | $4.94 \pm 0.26$                   | $4.25\pm1.00$   | $4.78 \pm 0.59$                   | $4.93 \pm 0.27$   | $4.95 \pm 0.21$ | $4.92 \pm 0.30$ | $4.82 \pm 0.41$ |
| Task avg.                           | 4.56                              | 4.45              | 4.28                              | 3.26            | 3.58                              | 4.00              | 4.23            | 4.13            | 3.76            |
| Report Generation                   | report-generation                 | n                 |                                   |                 |                                   |                   |                 |                 |                 |
| Content quality                     | $4.20 \pm 0.77$                   | $4.43 \pm 0.71$   | $4.03 \pm 0.72$                   | $2.53 \pm 0.85$ | $3.25\pm0.97$                     | $2.82 \pm 0.71$   | $3.90 \pm 0.86$ | $4.29 \pm 1.00$ | $3.35 \pm 0.81$ |
| Visual quality                      | $4.60 \pm 0.66$                   | $4.68 \pm 0.67$   | $4.52 \pm 0.62$                   | $3.81 \pm 0.90$ | $3.89 \pm 0.98$                   | $3.99 \pm 0.71$   | $4.38 \pm 0.97$ | $4.35 \pm 1.09$ | $4.11 \pm 0.92$ |
| Completeness                        | $4.77 \pm 0.52$                   | $4.81 \pm 0.50$   | $4.79 \pm 0.53$                   | $3.21 \pm 1.19$ | $4.01 \pm 1.14$                   | $3.14 \pm 0.87$   | $4.54 \pm 0.72$ | $4.62\pm1.00$   | $4.29 \pm 0.78$ |
| Data accuracy                       | $4.87 \pm 0.37$                   | $4.74 \pm 0.54$   | $\textbf{4.95} \pm \textbf{0.24}$ | $4.66 \pm 0.88$ | $4.87 \pm 0.47$                   | $4.74 \pm 0.60$   | $4.76 \pm 0.51$ | $4.60 \pm 0.98$ | $4.50 \pm 0.81$ |
| Fidelity                            | $4.58 \pm 0.58$                   | $4.44 \pm 0.65$   | $4.87 \pm 0.36$                   | $4.46 \pm 0.92$ | $4.82 \pm 0.49$                   | $4.28 \pm 0.89$   | $4.21 \pm 0.74$ | $4.31 \pm 1.00$ | $3.89 \pm 0.93$ |
| Task avg.                           | 4.60                              | 4.62              | 4.63                              | 3.73            | 4.17                              | 3.79              | 4.36            | 4.43            | 4.03            |
| Front-end Web Des                   | sign web-design                   |                   |                                   |                 |                                   |                   |                 |                 |                 |
| Visual design                       | $4.62 \pm 0.48$                   | $4.75 \pm 0.42$   | $4.71 \pm 0.53$                   | $4.12 \pm 0.56$ | $4.44 \pm 0.58$                   | $4.20 \pm 0.84$   | $4.56 \pm 0.48$ | $4.10 \pm 1.30$ | $4.43 \pm 0.63$ |
| Responsive                          | $4.34 \pm 0.47$                   | $4.21 \pm 0.51$   | $4.56 \pm 0.55$                   | $4.16 \pm 0.59$ | $4.18 \pm 0.60$                   | $4.06 \pm 0.61$   | $4.38 \pm 0.48$ | $4.02 \pm 1.08$ | $4.19 \pm 0.60$ |
| Navigation pass rate                | $4.96 \pm 0.30$                   | $4.97 \pm 0.23$   | $4.96 \pm 0.33$                   | $4.82 \pm 0.59$ | $\textbf{4.98} \pm \textbf{0.24}$ | $4.96 \pm 0.26$   | $4.96 \pm 0.27$ | $4.70 \pm 1.13$ | $4.93 \pm 0.44$ |
| Interaction pass rate               | $4.92 \pm 0.33$                   | $4.93 \pm 0.33$   | $4.91 \pm 0.46$                   | $4.73 \pm 0.66$ | $4.82 \pm 0.51$                   | $4.74 \pm 0.68$   | $4.91 \pm 0.38$ | $4.59 \pm 1.15$ | $4.84 \pm 0.51$ |
| Data display pass rate              | $4.95 \pm 0.22$                   | $4.94 \pm 0.21$   | $4.95 \pm 0.32$                   | $4.72 \pm 0.71$ | $4.96 \pm 0.14$                   | $4.93 \pm 0.23$   | $4.94 \pm 0.21$ | $4.70 \pm 1.05$ | $4.90 \pm 0.27$ |
| Task avg.                           | 4.74                              | 4.75              | 4.80                              | 4.47            | 4.66                              | 4.55              | 4.73            | 4.40            | 4.63            |
| Overall avg.                        | 4.51                              | 4.43              | 4.47                              | 3.76            | 4.03                              | 4.00              | 4.30            | 4.20            | 4.02            |

Table 1: Per-task evaluation scores by agent (1–5 scale). Each cell shows mean±std across cases. **Bold** marks the best score in each row.

In this subsection, we compare the performance of different agent systems across downstream tasks under the experimental settings described in Section 2.3. Across the five task categories, Claude 4.6 within the Claude Code framework and GPT-5.5 within the Codex framework demonstrate the strongest overall performance and the best stability (Table 1). This suggests that these systems are better able to adapt to different using setting, regardless of whether the injected skills are highly effective or only weakly aligned with the task. Among them, GPT-Codex does not perform as strongly as its coding-oriented reputation might suggest in our benchmark, which may partly due to weaker agentic capability in more open-ended downstream generation settings. Our skill-level analysis (Section 3.3) further suggests that when the underlying agent capability is limited, even high-quality skills cannot fully realize their potential benefits.

Across tasks, 1) Presentation generation and poster generation appear to be the most challenging categories, especially with respect to visual design and layout quality, where average scores are generally below 4. Common failure modes include uneven composition, excessive compression of content, and overlapping elements. As we show later in the skill analysis section (Section 3.3), some of these issues can be mitigated when agents are equipped with more detailed, task-specific

skills such as ppt-master; 2) In contrast, most agents already achieve relatively strong results on front-end web design, especially in terms of interactive functionality, where many systems can already produce reliable usable interfaces. However, there remains a substantial gap between these results and real-world deployment quality. In particular, responsive design scores remain consistently weaker, indicating that adaptation to diverse client-side devices is still inadequate for many generated websites. In addition, visual design issues remain common, including layouts with oversized or undersized elements and unbalanced spacing; 3) For data visualization, most models are already fairly reliable at directly using structured data files to produce charts with high data accuracy. However, their main weakness lies in analytical framing rather than plotting correctness: many generated visualizations fail to clearly surface the most important variable relationships or communicate a strong insight. This is precisely the part of the task where users would most hope carefully designed skills could help, yet current systems still show limited improvement; 4) For report generation, HTML-based rendering often leads to visually polished reports, and most strong models achieve high scores on visual quality. However, content quality and fidelity remain noticeably weaker. In many cases, the generated reports lack a deeper analytical structure: claims are often descriptive rather than rigorously supported, and systematic reasoning steps such as significance testing, robustness checks, or more explicit comparative analysis are frequently missing. This again suggests that current agent systems are better at producing polished artifacts than at carrying out the full analytical process behind them.

<span id="page-7-0"></span>![](_page_7_Figure_1.jpeg)

Figure 4: Token usage across agents and tasks. Mean completion tokens (left) and uncached input tokens (right) per task category, with error bars showing ±1 standard deviation across runs. Note the order-of-magnitude difference in y-axis scales between the two panels.

Beyond task performance, we also analyze token usage across models and tasks, as shown in Figure [4.](#page-7-0) We find that the Codex framework consistently exhibits the lowest token consumption across tasks, which is aligned with prior findings [\[19\]](#page-15-1) and suggests that the framework is designed with relatively strong efficiency considerations. Notably, GPT-5.5 achieves this efficiency advantage while still maintaining strong overall task performance: compared with agent systems from other model families, it offers a clear efficiency–performance trade-off advantage, and it even consumes fewer tokens than GPT-5.2 within the same series. Gemini 3.1 Pro follows closely, maintaining comparatively low token usage while also showing relatively strong stability across different skills and task categories. The Claude 4.6 series does not incur excessive token usage overall and remains fairly stable across most tasks. One notable exception is poster generation, where token usage increases substantially; as discussed later in Section [3.3,](#page-8-0) this is partly related to the effect of poster-specific skills. In contrast, the Kimi series shows noticeably weaker stability in agent execution. Besides its larger variance, we also observe frequent cases of abnormally high token consumption. In many instances, Kimi K2.6 enters looping behaviors and continues running until reaching the timeout threshold. MiniMax shows moderate average consumption overall, but still exhibits relatively large fluctuations across runs. DeepSeek V4 Pro occupies a favorable middle ground in the cost-performance space, delivering relatively strong performance with moderate token usage, while also offering the practical advantage of open-weight deployment. Across task categories, poster generation and presentation generation are generally the most token-intensive settings, especially for Claude-family and Kimi-based agents. Our analysis suggests that these tasks often require longer iterative planning, repeated layout adjustment, and multiple rounds of refinement, which together lead to substantially token usage. By contrast, data visualization and report generation are less expensive for most agents, because their workflows are more structurally constrained and their outputs are grounded in clearer data-to-artifact mappings.

#### **Takeaway**

GPT-5.5 and Claude Opus demonstrate the strongest overall performance on these downstream tasks, while GPT-5.5 under the Codex framework also shows a clear efficiency advantage. DeepSeek V4 provides a strong cost–performance compromise together with the practical benefit of open-weight deployment. However, even the best current agents still remain noticeably below the ideal setting in which generated artifacts can be directly used without human intervention, indicating that effective human oversight is still necessary in practice.

## <span id="page-8-0"></span>3.3 Skill Analysis: How Different Skills Perform

<span id="page-8-1"></span>![](_page_8_Figure_3.jpeg)

Figure 5: Skill performance versus cost across tasks and agent systems. Each subplot corresponds to one model-task pair, where the x-axis shows average token cost and the y-axis shows overall task performance. Colored points denote different skills, while the gray point marks the *no-skills* baseline. The dashed vertical and horizontal lines indicate the baseline cost and performance, respectively, so that points in the upper-left region represent the most desirable outcomes: higher quality at lower cost. The results show that skill augmentation is highly heterogeneous across models and tasks: some skills consistently improve performance, while others increase cost without yielding meaningful gains.

We compare the effects of different skills across tasks and agent systems. As shown in Figure 5 (full result is shown in Figure 10), the impact of skill augmentation varies substantially across models, tasks, and individual skills. For example, GPT-5.3-codex agents generally make weaker use of skills, and in many cases perform worse with skills than without them. This suggests that skill augmentation is not universally beneficial, and that the value of a skill depends not only on the skill itself, but also on how well the target agent can recognize, interpret, and execute it. Nevertheless, some skills provide consistent gains across multiple agents. For instance, ppt-master and anthropics-pptx substantially improve presentation generation, while visualize is particularly effective for poster

generation. With the aid of effective skills, even models with relatively modest base performance, such as Kimi K2.6, can improve from around 3.9 to 4.3 in average score, approaching the performance of Claude Opus. From the perspective of inference cost, however, skill augmentation is typically much more expensive. Measured by total token usage (prompt + completion + cache), runs with skills generally consume around 3-5× more tokens than their no-skills counterparts. As also suggested by Figure [5,](#page-8-1) higher token consumption is often accompanied by better task performance, indicating a clear output-scaling pattern in skill-augmented settings. To better understand the behavior of skills and the insights they provide, we divide our analysis into two parts. The first focuses on visually dominated artifact-generation tasks, including poster generation, presentation generation, and front-end web design, where the main effects of skills are reflected in visual language, layout control, and stylistic constraints. The second focuses on reasoning-intensive and analysis-intensive tasks, namely data visualization and report generation, where the primary contribution of skills lies in structuring the problem-solving process and guiding analytical reasoning.

<span id="page-9-0"></span>![](_page_9_Figure_1.jpeg)

Figure 6: Impact of skills on stylistic diversity relative to the *no-skills* baseline, measured by changes in within-group Vendi Score computed from CSD-ViT-L style embeddings. Positive values indicate more diverse outputs under a given skill. (a) Presentation generation. (b) Poster generation. The *pool* column aggregates outputs across all skills for cross-skill analysis.

Visually Oriented Artifact Generation. For visually oriented artifact generation tasks, like presentation generation, poster generation, design language is a central component of the artifact. Therefore, beyond rubric-based quality evaluation, we further examine the stylistic diversity of generated artifacts. To quantify stylistic diversity, we encode outputs using CSD-ViT-L style embeddings [\[20\]](#page-15-2) and compute the Vendi Score within each skill group, which measures intra-group diversity. To ensure fair comparison, we control for sample size across settings and compare each skill-specific group against a matched *no-skills* baseline, while also reporting a pooled multi-skill condition (*pool*) for cross-skill analysis. Figure [6a](#page-9-0) and Figure [6b](#page-9-0) summarize the results for presentation and poster generation, respectively. Front-end web design is reported in Figure [11,](#page-24-1) because the overall diversity effect of skills is small (less than 0.02), we do not conduct further diversity analysis. We observe that skill usage does not necessarily increase stylistic diversity, even across skills. For presentation generation, some skills, such as anthropics-pptx and minimax-pptx, consistently increase diversity relative to the *no-skills* baseline, whereas others, such as frontend-slides, substantially reduce it. Most remaining skills induce only modest changes. In contrast, for poster generation, diversity generally decreases under skill augmentation, suggesting that poster-oriented skills tend to impose stronger stylistic constraints on the output. Moreover, the diversity effect of a skill varies substantially across models (with Pearson correlations of 0.52 for presentation generation and 0.28 for poster generation), indicating that, much like overall task performance, stylistic outcomes emerge from the interaction between the skill and the underlying agent rather than from the skill alone. The pooled multi-skill condition provides an additional perspective on cross-skill variation. For presentation generation, the *pool* condition is consistently more diverse than *no-skills*, indicating that different presentation skills indeed induce meaningfully different visual languages. For poster generation, however, the pooled condition shows little or no diversity advantage over *no-skills*. This suggests that although different poster skills are different, most of them tightly constrain outputs into a small number of fixed visual idioms, so the overall ecosystem still spans only a limited stylistic space.

To better understand how skill design contributes to both output quality and stylistic diversity, we conduct a more fine-grained analysis of the visual-generation skills in Table [2.](#page-10-0) We characterize each skill along two orthogonal dimensions, corresponding to two complementary forms of experience encoded in the skill. The first is design priors, which capture the reusable visual experience packaged with the skill, including visual template files, reference design documents, design-related data assets, and design-specific content inside SKILL.md. These priors provide concrete design-oriented guidance that informs the model's visual generation behavior. The second is procedural constraints, which capture how strongly the skill prescribes the generation process through explicit directives, such as MUST-style and NEVER-style instructions, together with other structural locks embedded in the workflow. These constraints encode rule-like operational experience that restricts the model's output space and guides it toward more controlled execution. To operationalize these two dimensions, we first extract a set of countable signals using rule-based heuristics, and then manually map them to coarse-grained 0-5 scores to facilitate trend-level comparison across skills.

<span id="page-10-0"></span>

| Skill                               | Key Assets                                                                           | Key Constraints    |   |   |       |       |       | A C Obs. O Obs. D Obs. E Obs. Div |
|-------------------------------------|--------------------------------------------------------------------------------------|--------------------|---|---|-------|-------|-------|-----------------------------------|
|                                     | Presentation Generation ppt-generation                                               |                    |   |   |       |       |       |                                   |
| ppt-master                          | 101 layouts + 33 charts + 640 icons + 39 references                                  | 25 MUST + 10 NEVER | 5 | 5 | 4.27± | 3.91± | 4.42± | -0.46                             |
| anthropics-pptx                     | 2 references (pptxgenjs, editing) + 78 inline design lines 1 MUST + 3 NEVER          |                    | 3 | 2 | 4.20± | 3.65± | 4.46± | +1.12                             |
| minimax-pptx                        | 5 references (incl. design system) + 8 inline design lines                           | 9 MUST + 1 NEVER   | 2 | 2 | 4.09± | 3.47± | 4.40± | +2.49                             |
| powerpoint-pptx                     | 3 references (slides, charts, design) + 21 inline design lines 2 MUST                |                    | 1 | 1 | 4.03± | 3.25± | 4.47± | +0.27                             |
| frontend-slides                     | Viewport-base CSS + 12-style preset library                                          | 13 MUST + 7 NEVER  | 2 | 5 | 3.96± | 3.52± | 4.24± | -1.65                             |
| pptx-manipulation                   | Unpack/repack tutorial + 16 inline design lines                                      | —                  | 1 | 0 | 4.02± | 3.29± | 4.43± | +0.08                             |
| no-skills                           | —                                                                                    | —                  | 0 | 0 | 4.04± | 3.20± | 4.54± | —                                 |
| Poster Generation poster-generation |                                                                                      |                    |   |   |       |       |       |                                   |
| visualize                           | Mandatory skeleton + 9 references + 98 inline design lines 117 MUST + 28 NEVER       |                    | 4 | 5 | 4.05± | 3.93± | 4.11± | -2.75                             |
| canvas-design                       | 27 inline design lines                                                               | 15 MUST + 5 NEVER  | 1 | 5 | 3.91± | 3.56± | 4.09± | -2.08                             |
| antv-infographic                    | External AntV template library                                                       | DSL grammar        | 1 | 2 | 3.77± | 3.47± | 3.92± | -0.83                             |
| paper-poster                        | External LATEX tcbposter class + 256 inline design lines 21 MUST + 15 NEVER          |                    | 2 | 5 | 3.67± | 2.88± | 4.07± | -3.07                             |
| no-skills                           | —                                                                                    | —                  | 0 | 0 | 3.95± | 3.56± | 4.14± | —                                 |
| Front-end Web Design web-design     |                                                                                      |                    |   |   |       |       |       |                                   |
| ui-ux-pro-max                       | 16 frontend-stack guides + 14 design CSVs                                            | 44 MUST + 10 NEVER | 5 | 5 | 4.67± | 4.41± | 4.88± | -0.01                             |
| ui-styling                          | 7 references + 2 generator scripts + 321 inline lines                                | —                  | 3 | 0 | 4.66± | 4.39± | 4.88± | -0.01                             |
|                                     | web-design-expert 3 references + 220 inline lines                                    | 1 NEVER            | 2 | 1 | 4.66± | 4.35± | 4.90± | -0.01                             |
| loom                                | 1 UX-review reference + motivation/personality prompts                               | 1 MUST             | 1 | 1 | 4.65± | 4.34± | 4.90± | -0.01                             |
|                                     | seo-local-business 3 SEO templates (head, robots, sitemap) + 332 inline lines 4 MUST |                    | 2 | 2 | 4.64± | 4.30± | 4.89± | -0.00                             |
| web-frameworks                      | 8 references + 2 init scripts                                                        | —                  | 3 | 0 | 4.63± | 4.31± | 4.88± | -0.01                             |
| superdesign                         | 212 inline design lines, no external references                                      | 2 NEVER            | 1 | 1 | 4.55± | 4.19± | 4.84± | +0.02                             |
| frontend-ultimate                   | 3 references + site-config template + 408 inline lines                               | 1 MUST + 1 NEVER   | 2 | 1 | 4.54± | 4.24± | 4.80± | +0.01                             |
| no-skills                           | —                                                                                    | —                  | 0 | 0 | 4.65± | 4.32± | 4.91± | —                                 |

Table 2: Quantifying presentation, poster, and web-design skills along two orthogonal dimensions and relating them to observed quality and stylistic diversity. Asset score (A, 0–5) measures the strength of *design priors* packaged with a skill, based on countable signals such as visual template files, reference design documents, design-data size, and design-related line count inside SKILL.md. Constraint score (C, 0–5) measures the strength of *procedural constraints*, based on MUST-style and NEVER-style directive counts together with structural locks. Obs. O denotes the measured overall judge score; Obs. D denotes the design sub-score, taken directly from the judge for presentation and poster generation and computed as the mean of (Visual Design + Responsive) for web design; Obs. E denotes the content-oriented effectiveness score, computed as the mean of (Completeness + Fidelity) for presentation generation, the mean of (Content + Completeness) for poster generation, and the mean of three pass-rate for web design; Obs. Div denotes the observed visual-diversity score.

In terms of output quality, our analysis reveals a clear relationship between skill design and observed performance. First, after introducing skills, models almost always achieve higher visual-design scores than in the *no-skills* setting (in all 6 presentation-generation settings, and in roughly half of the poster-generation and front-end web design settings). Moreover, this improvement tends to grow with the richness of the skill's *design priors*. This suggests that well-designed visual priors can directly raise the lower bound of visual artifact quality by providing concrete design guidance that the model can readily exploit. At the same time, however, content-related metrics such as *Completeness* and *Fidelity* may be slightly degraded. One reason is that skills themselves introduce additional input content and instructions, which the model must process and adapt during generation, thereby placing additional burden on both layout planning and content allocation. More importantly, strong visual design alone is not sufficient; a useful skill must also be adaptable across the range of usage scenarios. S. Some skills impose structural choices that are visually beneficial but content-restrictive, which can ultimately reduce overall performance in real-world usage. For example, frontend-slides includes hard density caps on the number of layout elements and strong layout constraints, which makes it visually disciplined but almost inevitably causes content omission when the source material is dense, thereby lowering completeness and overall task scores. Taken together, these results suggest an asset scaling effect in skill design: the richer and better designed the packaged visual priors are, the stronger the overall task performance tends to become. This pattern is intuitively plausible. In the ideal case, if a skill provides sufficiently broad and high-quality design coverage for the target use cases, then an agent can achieve strong downstream performance simply by executing within that prior space. For instance, with the aid of ppt-master, which covers 22 presentation genres, even models with relatively modest base performance, such as Kimi K2.6 and Gemini 3.1, improve from around 3.9 to 4.3 and from 3.7 to 4.3, respectively, approaching the performance of raw Claude Opus.

In terms of stylistic diversity, although different forms of constraints are not perfectly comparable, we observe a broad negative relationship between constraint strength and output diversity. Skills with stronger procedural constraints tend to produce more visually consistent but less diverse outputs. This pattern is particularly clear in presentation generation: frontend-slides and ppt-master, which have some of the highest constraint scores, also exhibit some of the lowest observed diversity scores. In other words, stronger constraint can improve consistency and sometimes quality, but often at the cost of narrowing the output style space.

## Takeaway

For visually oriented artifact-generation tasks such as presentation generation, skills do not necessarily increase stylistic diversity, but they can substantially improve the model's design quality. In particular, richer and higher-quality *design priors*, such as well-crafted templates, can significantly raise the performance floor of weaker models and also improve stronger models. Meanwhile, stronger *procedural constraints* typically increase output consistency while reducing stylistic diversity.

Analytical and Reasoning-Intensive Tasks. For more reasoning-intensive tasks, such as report generation and data visualization, require more structured reasoning, more careful data interpretation, and better-designed analysis procedures. Accordingly, beyond overall task scores, we place particular emphasis on reasoning-related indicators. For report generation, we focus on *data accuracy* and *fidelity*, examining whether the model's claims and conclusions are correctly grounded in the underlying data. For data visualization, we place greater emphasis on whether the generated chart clearly communicates the intended insight under the chosen analytical framing. As shown in Figure [7,](#page-12-0) we find two main patterns. 1) For tasks whose core challenge lies in reasoning and analytical decisionmaking, existing skills provide only limited benefit. In report generation, most skills perform only on par with, or marginally above, the *no-skills* baseline. The only near-neutral case is business-auto, whose behavior is almost equivalent to *no-skills*, because it contributes nearly no additional analytical guidance. Qualitatively, the generated reports often remain relatively superficial: many claims lack significance testing, deeper validation, or more rigorous experimental support. A similar pattern appears in data visualization. In many cases, agents are able to produce a chart, but fail to clearly surface the underlying relationships among variables or communicate the intended analytical insight. This is also expected given the nature of the current skills: most of them mainly provide tool-level assistance, rather than richer analytical priors, structured workflows, or reasoning-oriented norms. As a result, success on these tasks still depends primarily on the model's own analytical capability; 2) From an overall perspective, skill augmentation does not lead to meaningful gains on these tasks: the average improvement in overall score is less than 0.04. One exception is Kimi, where the *no-skills* setting appears worse than several skill-augmented settings. Our trace inspection suggests that this gap is partly attributable to a higher tendency for Kimi to enter looping behavior without skills, rather than to large intrinsic gains from the skills themselves.

## Takeaway

Overall, current reasoning- and analysis-oriented skills provide limited gains, largely because they offer insufficient analytical priors and structured guidance. In practice, their benefits are often marginal, and in some cases the base model without skills may already be the stronger choice.

<span id="page-12-0"></span>![](_page_12_Figure_0.jpeg)

Figure 7: Comparison of skill-augmented and *no-skills* settings on reasoning intensive tasks.

Cost Analysis. Beyond their impact on artifact quality, we further analyze the cost implications of skill augmentation. As shown in Figure [5,](#page-8-1) in most cases the use of skills does not reduce generation cost relative to the *no-skills* setting. One important reason is that skills themselves introduce additional input content. This effect is especially pronounced for asset-rich skills such as ppt-master and visualize, whose large amount of reference material increases prompt length and leads to a corresponding increase in token consumption. In this sense, the asset scaling effect discussed earlier is accompanied by a parallel cost scaling trend. Beyond the cost of reading richer skill content, some skills also impose more iterative execution procedures. For example, paper-poster requires the agent to compile LATEX outputs and perform rule-based checking and refinement steps. As a result, certain models, especially the Claude 4.6 series, undergo substantially longer execution loops on this task, often involving more than ten additional refinement steps. This directly contributes to the much larger variance observed in Figure [4.](#page-7-0) In extreme cases, the total output-token cost can exceed that of the *no-skills* setting by more than 4×, and for Claude Sonnet the increase can reach nearly 10×. This also indirectly suggests that these models are still not sufficiently strong in these settings, and often require repeated adjustment and refinement before producing satisfactory results.

## <span id="page-12-1"></span>4 Human Evaluation

Although our framework is fully automatic and can continuously generate new test cases and conduct evaluation at scale, we further perform human evaluation to assess both the quality of the generated task instances and the reliability of the automatic judgments. Specifically, we involve four senior researchers in natural language processing as human annotators, and randomly sample 100 task instances balanced across the five task categories. For task-instance quality, annotators score each generated case on three dimensions: *fluency*, *coherence*, and *completeness*, where completeness measures whether the task description is sufficiently clear and well specified for execution. Each dimension is rated on a 1–3 scale. Across all dimensions, the mean human score exceeds 2.98, with an exact agreement rate of 98.8%. Additional details are provided in Appendix [A.4.](#page-22-0) For evaluation quality, given the complexity of the overall evaluation pipeline, we perform human assessment directly on the automatic evaluation results. Annotators are asked to judge whether the assigned score and its accompanying rationale are consistent with the task requirements and the generated output. We use a 1-3 scale: a score of 3 indicates that both the judgment and the rationale are reasonable and well aligned with the task requirements; a score of 2 indicates that the assigned score is reasonable but the rationale is incomplete or not convincing; and a score of 1 indicates that the assigned score itself is unreasonable. Across four annotators, the pooled mean rating is 2.86. Exact four-way agreement accounts for 75.0% of annotated units, and averagely only 6.01% of cases receive a rating of 1. These results suggest that the proposed automatic evaluation pipeline is reasonably reliable. In addition, we use another visually strong model from a different family, Gemini 3.1 Pro, as an auxiliary evaluator to further examine the robustness of our automatic evaluation pipeline. On a held-out set of 200 sampled cases, the scores produced by Gemini 3.1 Pro show strong correlation with our primary evaluator, achieving Pearson and Spearman correlations of 0.855 and 0.821, respectively.

## 5 Related Work

Agent skills and procedural augmentation. Anthropic recently formalized Agent Skills [\[5\]](#page-13-4), a SKILL.md-based abstraction for packaging procedural expertise as portable, dynamically loadable artifacts. Building on this paradigm, several works have explored how to construct, discover, and refine skills automatically [\[21,](#page-15-3) [22,](#page-15-4) [23,](#page-15-5) [24\]](#page-15-6). As skills proliferate, a parallel line of work has begun to evaluate how effectively models leverage them. SkillsBench [\[25\]](#page-15-7) shows that curated skills can provide substantial but highly variable gains, while self-generated skills offer little benefit on average. Community efforts such as PinchBench [\[26\]](#page-15-8) and WildClawBench [\[27\]](#page-15-9) further stress-test agent–skill combinations in realistic workflows. In contrast, our work focuses on downstream application tasks and systematically compares community-contributed skills within the same task settings.

Benchmarks for LLM agents. Existing agent benchmarks span software engineering [\[28\]](#page-15-10), web navigation [\[9\]](#page-14-3), and generalist multi-step reasoning [\[29\]](#page-15-11). A persistent limitation is reliance on static task pools, which saturate quickly and risk contamination [\[30,](#page-15-12) [31\]](#page-16-0). Dynamic benchmarks mitigate this by releasing fresh problems on a rolling basis [\[32,](#page-16-1) [33,](#page-16-2) [34\]](#page-16-3). We extend the dynamic philosophy to the skill-augmented agent setting, enabling controlled comparison of competing skills under the same task distribution while jointly measuring effectiveness and efficiency.

## 6 Discussion

The open skill ecosystem for LLM agents is still evolving rapidly. In this work, we build an automatic evaluation framework to make large-scale and continuously updated assessment feasible. However, this design also comes with several limitations. First, due to practical cost constraints, the current version of OpenSkillEval does not cover more exhaustive set of available skills. Second, while automation enables scalability and reproducibility, it inevitably abstracts away part of the humanagent interaction process that may matter in real deployment settings. More broadly, our current evaluation primarily analyzes skill effectiveness from two perspectives: the agent's execution process and the quality of the final output artifact. Although we provide taskaways for skills formalization, we do not directly evaluate skills in isolation. This is mainly because the utility of a skill depends strongly on how different models and agent frameworks interpret and use it.

## 7 Conclusion

In this work, we present OpenSkillEval, an automatic evaluation framework for skill-augmented LLM agents and open-source skills in real-world downstream tasks. By automatically constructing task instances from evolving artifacts, collecting community-contributed skills, and evaluating both agent trajectories and final outputs, OpenSkillEval enables a more realistic and scalable analysis of skill effectiveness. Our experiments show that skill availability does not guarantee effective skill use, that the value of skill augmentation depends strongly on the underlying model and agent framework, and that many popular open-source skills provide limited or inconsistent gains. We hope that OpenSkillEval can provide practical guidance for selecting both agents and skills in downstream applications, while also offering useful insights for the design, maintenance, and future development of open-source skills.

## References

- <span id="page-13-0"></span>[1] OpenAI. GPT-5.4 thinking system card. Technical report, OpenAI, March 2026. URL [https:](https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf) [//deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf](https://deploymentsafety.openai.com/gpt-5-4-thinking/gpt-5-4-thinking.pdf).
- <span id="page-13-1"></span>[2] Anthropic. System card: Claude Opus 4.6. Technical report, Anthropic, February 2026. URL [https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.](https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf) [pdf](https://www-cdn.anthropic.com/14e4fb01875d2a69f646fa5e574dea2b1c0ff7b5.pdf).
- <span id="page-13-2"></span>[3] Anthropic. Claude code by anthropic | ai coding agent, terminal, ide. [https://www.](https://www.anthropic.com/claude-code) [anthropic.com/claude-code](https://www.anthropic.com/claude-code), 2025.
- <span id="page-13-3"></span>[4] OpenAI. Codex by openai | ai coding agent. <https://openai.com/codex/>, 2025.
- <span id="page-13-4"></span>[5] Anthropic. Equipping agents for the real world with agent skills. [https://www.anthropic.](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) [com/engineering/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills), 2025.

- <span id="page-14-0"></span>[6] Harbor Framework Team. Harbor: A framework for evaluating and optimizing agents and models in container environments, January 2026. URL [https://github.com/](https://github.com/harbor-framework/harbor) [harbor-framework/harbor](https://github.com/harbor-framework/harbor).
- <span id="page-14-1"></span>[7] Hao Zheng, Xinyan Guan, Hao Kong, Wenkai Zhang, Jia Zheng, Weixiang Zhou, Hongyu Lin, Yaojie Lu, Xianpei Han, and Le Sun. Pptagent: Generating and evaluating presentations beyond text-to-slides. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*, pages 14413–14429, 2025.
- <span id="page-14-2"></span>[8] Shibo Hong, Jiahao Ying, Haiyuan Liang, Mengdi Zhang, Jun Kuang, Jiazheng Zhang, and Yixin Cao. Frabench and ufeval: Unified fine-grained evaluation with task and aspect generalization, 2025. URL <https://arxiv.org/abs/2505.12795>.
- <span id="page-14-3"></span>[9] Shuyan Zhou, Frank F Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, et al. Webarena: A realistic web environment for building autonomous agents. In *The Twelfth International Conference on Learning Representations*, 2023.
- <span id="page-14-4"></span>[10] OpenAI. GPT-5.3-Codex system card. [https://openai.com/index/](https://openai.com/index/gpt-5-3-codex-system-card/) [gpt-5-3-codex-system-card/](https://openai.com/index/gpt-5-3-codex-system-card/), 2026.
- <span id="page-14-5"></span>[11] Google. Gemini CLI. <https://github.com/google-gemini/gemini-cli>, 2025. Accessed: 2026-05-02.
- <span id="page-14-6"></span>[12] Google DeepMind. Gemini 3.1 pro model card. [https://deepmind.google/models/](https://deepmind.google/models/model-cards/gemini-3-1-pro/) [model-cards/gemini-3-1-pro/](https://deepmind.google/models/model-cards/gemini-3-1-pro/), 2026.
- <span id="page-14-7"></span>[13] Moonshot AI. Kimi code CLI. <https://github.com/MoonshotAI/kimi-cli>, 2025.
- <span id="page-14-8"></span>[14] Kimi Team, Yifan Bai, Yiping Bao, Guanduo Chen, Jiahao Chen, Ningxin Chen, Ruijue Chen, Yanru Chen, Yuankun Chen, Yutian Chen, Zhuofu Chen, Jialei Cui, Hao Ding, Mengnan Dong, Angang Du, Chenzhuang Du, Dikang Du, Yulun Du, Yu Fan, Yichen Feng, Kelin Fu, Bofei Gao, Hongcheng Gao, Peizhong Gao, Tong Gao, Xinran Gu, Longyu Guan, Haiqing Guo, Jianhang Guo, Hao Hu, Xiaoru Hao, Tianhong He, Weiran He, Wenyang He, Chao Hong, Yangyang Hu, Zhenxing Hu, Weixiao Huang, Zhiqi Huang, Zihao Huang, Tao Jiang, Zhejun Jiang, Xinyi Jin, Yongsheng Kang, Guokun Lai, Cheng Li, Fang Li, Haoyang Li, Ming Li, Wentao Li, Yanhao Li, Yiwei Li, Zhaowei Li, Zheming Li, Hongzhan Lin, Xiaohan Lin, Zongyu Lin, Chengyin Liu, Chenyu Liu, Hongzhang Liu, Jingyuan Liu, Junqi Liu, Liang Liu, Shaowei Liu, T. Y. Liu, Tianwei Liu, Weizhou Liu, Yangyang Liu, Yibo Liu, Yiping Liu, Yue Liu, Zhengying Liu, Enzhe Lu, Lijun Lu, Shengling Ma, Xinyu Ma, Yingwei Ma, Shaoguang Mao, Jie Mei, Xin Men, Yibo Miao, Siyuan Pan, Yebo Peng, Ruoyu Qin, Bowen Qu, Zeyu Shang, Lidong Shi, Shengyuan Shi, Feifan Song, Jianlin Su, Zhengyuan Su, Xinjie Sun, Flood Sung, Heyi Tang, Jiawen Tao, Qifeng Teng, Chensi Wang, Dinglu Wang, Feng Wang, Haiming Wang, Jianzhou Wang, Jiaxing Wang, Jinhong Wang, Shengjie Wang, Shuyi Wang, Yao Wang, Yejie Wang, Yiqin Wang, Yuxin Wang, Yuzhi Wang, Zhaoji Wang, Zhengtao Wang, Zhexu Wang, Chu Wei, Qianqian Wei, Wenhao Wu, Xingzhe Wu, Yuxin Wu, Chenjun Xiao, Xiaotong Xie, Weimin Xiong, Boyu Xu, Jing Xu, Jinjing Xu, L. H. Xu, Lin Xu, Suting Xu, Weixin Xu, Xinran Xu, Yangchuan Xu, Ziyao Xu, Junjie Yan, Yuzi Yan, Xiaofei Yang, Ying Yang, Zhen Yang, Zhilin Yang, Zonghan Yang, Haotian Yao, Xingcheng Yao, Wenjie Ye, Zhuorui Ye, Bohong Yin, Longhui Yu, Enming Yuan, Hongbang Yuan, Mengjie Yuan, Haobing Zhan, Dehao Zhang, Hao Zhang, Wanlu Zhang, Xiaobin Zhang, Yangkun Zhang, Yizhi Zhang, Yongting Zhang, Yu Zhang, Yutao Zhang, Yutong Zhang, Zheng Zhang, Haotian Zhao, Yikai Zhao, Huabin Zheng, Shaojie Zheng, Jianren Zhou, Xinyu Zhou, Zaida Zhou, Zhen Zhu, Weiyu Zhuang, and Xinxing Zu. Kimi k2: Open agentic intelligence, 2025. URL <https://arxiv.org/abs/2507.20534>.
- <span id="page-14-9"></span>[15] MiniMax. MiniMax M2.7: Early echoes of self-evolution. [https://www.minimax.io/news/](https://www.minimax.io/news/minimax-m27-en) [minimax-m27-en](https://www.minimax.io/news/minimax-m27-en), 2026.
- <span id="page-14-10"></span>[16] DeepSeek-AI. Deepseek-v4: Towards highly efficient million-token context intelligence, 2026.
- <span id="page-14-11"></span>[17] Jiahao Ying, Yixin Cao, Kai Xiong, Long Cui, Yidong He, and Yongbin Liu. Intuitive or dependent? investigating LLMs' behavior style to conflicting prompts. In Lun-Wei Ku,

- Andre Martins, and Vivek Srikumar, editors, *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 4221–4246, Bangkok, Thailand, August 2024. Association for Computational Linguistics. doi: 10.18653/ v1/2024.acl-long.232. URL <https://aclanthology.org/2024.acl-long.232/>.
- <span id="page-15-0"></span>[18] Ivan Seleznov. Why claude code skills don't activate and how to fix it, 2026. Medium blog post.
- <span id="page-15-1"></span>[19] Zheng Du, Hao Kang, Song Han, Tushar Krishna, and Ligeng Zhu. Ockbench: Measuring the efficiency of llm reasoning. *arXiv preprint arXiv:2511.05722*, 2025.
- <span id="page-15-2"></span>[20] Gowthami Somepalli, Anubhav Gupta, Kamal Gupta, Shramay Palta, Micah Goldblum, Jonas Geiping, Abhinav Shrivastava, and Tom Goldstein. Measuring style similarity in diffusion models. *arXiv preprint arXiv:2404.01292*, 2024.
- <span id="page-15-3"></span>[21] Renjun Xu and Yang Yan. Agent skills for large language models: Architecture, acquisition, security, and the path forward, 2026. URL <https://arxiv.org/abs/2602.12430>.
- <span id="page-15-4"></span>[22] Salaheddin Alzubi, Noah Provenzano, Jaydon Bingham, Weiyuan Chen, and Tu Vu. Evoskill: Automated skill discovery for multi-agent systems, 2026. URL [https://arxiv.org/abs/](https://arxiv.org/abs/2603.02766) [2603.02766](https://arxiv.org/abs/2603.02766).
- <span id="page-15-5"></span>[23] Yutao Yang, Junsong Li, Qianjun Pan, Bihao Zhan, Yuxuan Cai, Lin Du, Jie Zhou, Kai Chen, Qin Chen, Xin Li, Bo Zhang, and Liang He. Autoskill: Experience-driven lifelong learning via skill self-evolution, 2026. URL <https://arxiv.org/abs/2603.01145>.
- <span id="page-15-6"></span>[24] Boyuan Zheng, Michael Y. Fatemi, Xiaolong Jin, Zora Zhiruo Wang, Apurva Gandhi, Yueqi Song, Yu Gu, Jayanth Srinivasa, Gaowen Liu, Graham Neubig, and Yu Su. Skillweaver: Web agents can self-improve by discovering and honing skills, 2025. URL [https://arxiv.org/](https://arxiv.org/abs/2504.07079) [abs/2504.07079](https://arxiv.org/abs/2504.07079).
- <span id="page-15-7"></span>[25] Xiangyi Li, Wenbo Chen, Yimin Liu, Shenghan Zheng, Xiaokun Chen, Yifeng He, Yubo Li, Bingran You, Haotian Shen, Jiankai Sun, Shuyi Wang, Binxu Li, Qunhong Zeng, Di Wang, Xuandong Zhao, Yuanli Wang, Roey Ben Chaim, Zonglin Di, Yipeng Gao, Junwei He, Yizhuo He, Liqiang Jing, Luyang Kong, Xin Lan, Jiachen Li, Songlin Li, Yijiang Li, Yueqian Lin, Xinyi Liu, Xuanqing Liu, Haoran Lyu, Ze Ma, Bowei Wang, Runhui Wang, Tianyu Wang, Wengao Ye, Yue Zhang, Hanwen Xing, Yiqi Xue, Steven Dillmann, and Han chung Lee. Skillsbench: Benchmarking how well agent skills work across diverse tasks, 2026. URL <https://arxiv.org/abs/2602.12670>.
- <span id="page-15-8"></span>[26] PinchBench Contributors. PinchBench: Real-world benchmarks for AI coding agents. [https:](https://github.com/pinchbench/skill) [//github.com/pinchbench/skill](https://github.com/pinchbench/skill), 2026. GitHub repository.
- <span id="page-15-9"></span>[27] Shuangrui Ding, Xuanlang Dai, Long Xing, Shengyuan Ding, Ziyu Liu, Jingyi Yang, Penghui Yang, Zhixiong Zhang, Xilin Wei, Yubo Ma, Haodong Duan, Jing Shao, Jiaqi Wang, Dahua Lin, Kai Chen, and Yuhang Zang. Wildclawbench, 2026. URL [https://github.com/InternLM/](https://github.com/InternLM/WildClawBench) [WildClawBench](https://github.com/InternLM/WildClawBench).
- <span id="page-15-10"></span>[28] Carlos E Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik Narasimhan. Swe-bench: Can language models resolve real-world github issues? 2023.
- <span id="page-15-11"></span>[29] Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, et al. Agentbench: Evaluating llms as agents. In *The Twelfth International Conference on Learning Representations*, 2023.
- <span id="page-15-12"></span>[30] Yixin Cao, Shibo Hong, Xinze Li, Jiahao Ying, Yubo Ma, Haiyuan Liang, Yantao Liu, Zijun Yao, Xiaozhi Wang, Dan Huang, Wenxuan Zhang, Lifu Huang, Muhao Chen, Lei Hou, Qianru Sun, Xingjun Ma, Zuxuan Wu, Min-Yen Kan, David Lo, Qi Zhang, Heng Ji, Jing Jiang, Juanzi Li, Aixin Sun, Xuanjing Huang, Tat-Seng Chua, and Yu-Gang Jiang. Toward generalizable evaluation in the llm era: A survey beyond benchmarks, 2025. URL [https://arxiv.org/](https://arxiv.org/abs/2504.18838) [abs/2504.18838](https://arxiv.org/abs/2504.18838).

- <span id="page-16-0"></span>[31] Jiahao Ying, Yixin Cao, Yushi Bai, Qianru Sun, Bo Wang, Wei Tang, Zhaojun Ding, Yizhe Yang, Xuanjing Huang, and Shuicheng Yan. Automating dataset updates towards reliable and timely evaluation of large language models. In A. Globerson, L. Mackey, D. Belgrave, A. Fan, U. Paquet, J. Tomczak, and C. Zhang, editors, *Advances in Neural Information Processing Systems*, volume 37, pages 17106–17132. Curran Associates, Inc., 2024. doi: 10.52202/079017-0544. URL [https://proceedings.neurips.cc/paper\\_](https://proceedings.neurips.cc/paper_files/paper/2024/file/1e89c12621c0315373f20f0aeabe5dbe-Paper-Datasets_and_Benchmarks_Track.pdf) [files/paper/2024/file/1e89c12621c0315373f20f0aeabe5dbe-Paper-Datasets\\_](https://proceedings.neurips.cc/paper_files/paper/2024/file/1e89c12621c0315373f20f0aeabe5dbe-Paper-Datasets_and_Benchmarks_Track.pdf) [and\\_Benchmarks\\_Track.pdf](https://proceedings.neurips.cc/paper_files/paper/2024/file/1e89c12621c0315373f20f0aeabe5dbe-Paper-Datasets_and_Benchmarks_Track.pdf).
- <span id="page-16-1"></span>[32] Wei Tang, Yixin Cao, Yang Deng, Jiahao Ying, Bo Wang, Yizhe Yang, Yuyue Zhao, Qi Zhang, Xuanjing Huang, Yu-Gang Jiang, and Yong Liao. EvoWiki: Evaluating LLMs on evolving knowledge. In Wanxiang Che, Joyce Nabende, Ekaterina Shutova, and Mohammad Taher Pilehvar, editors, *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 948–964, Vienna, Austria, July 2025. Association for Computational Linguistics. ISBN 979-8-89176-251-0. doi: 10.18653/v1/2025.acl-long.47. URL <https://aclanthology.org/2025.acl-long.47/>.
- <span id="page-16-2"></span>[33] Colin White, Samuel Dooley, Manley Roberts, Arka Pal, Benjamin Feuer, Siddhartha Jain, Ravid Shwartz-Ziv, Neel Jain, Khalid Saifullah, Sreemanti Dey, Shubh-Agrawal, Sandeep Singh Sandha, Siddartha Venkat Naidu, Chinmay Hegde, Yann LeCun, Tom Goldstein, Willie Neiswanger, and Micah Goldblum. Livebench: A challenging, contamination-free LLM benchmark. In *The Thirteenth International Conference on Learning Representations*, 2025.
- <span id="page-16-3"></span>[34] Naman Jain, King Han, Alex Gu, Wen-Ding Li, Fanjia Yan, Tianjun Zhang, Sida Wang, Armando Solar-Lezama, Koushik Sen, and Ion Stoica. Livecodebench: Holistic and contamination free evaluation of large language models for code, 2024. URL [https://arxiv.org/abs/](https://arxiv.org/abs/2403.07974) [2403.07974](https://arxiv.org/abs/2403.07974).

## A Technical Appendices and Supplementary Material

## <span id="page-17-1"></span>A.1 Experimental Environment

We adopt Harbor [\[6\]](#page-14-0) as the unified execution framework for all experiments, and thank its open-source maintainers for their support and continued development. At runtime, all agents are executed under the same containerized environment based on ubuntu:24.04. To ensure fairness in environment setup and execution, we also provide network access during runtime and use unified timeout settings, with build\_timeout\_sec = 1800.0 \* 5 and timeout\_sec = 900.0 \* 5. All agents are evaluated using the official Responses API service of their corresponding model providers. Unless otherwise specified, all agent frameworks are run with their default parameter settings.[4](#page-17-2)

For each instance, we provide the agent with the natural-language instruction I (stored as Instruction.md), the structured task specification T (stored as task\_input.json), and any associated source materials or data files required by the task. These additional inputs vary by task category. For example, presentation generation is accompanied by source\_brief.md, which may include tables, figures, and other supporting content; report generation is provided with the corresponding tabular dataset (e.g., data.csv); and data visualization is paired with a structured source file such as source\_data.json. For each task category, we standardize the expected output format to ensure fair and consistent evaluation across agent systems. Specifically, the required output format is .pptx for presentation generation, a website with index.html as the entry point for front-end web design, .png for poster generation, .html for report generation, and .png for data visualization.

For evaluation, we primarily use Claude Opus 4.6 because of its strong capability, while also using Gemini 3.1 Pro for ablation analysis in Section [4.](#page-12-1) For the agent-as-judge setting, we deploy Claude Opus 4.6 within the Claude Code framework and conduct evaluation in a Docker-based environment.

## <span id="page-17-0"></span>A.2 Task-Specific Evaluation Inputs for VLM-Based Judging

For VLM-based evaluation, we design task-specific input representations and evaluation granularity according to the characteristics of each downstream task.

Presentation Generation. For presentation generation, we first convert the generated .pptx files into PDF format using Microsoft PowerPoint (version 16.108.1). We choose this conversion pipeline because we found that commonly used Linux-friendly conversion tools often introduce substantial rendering errors. The resulting PDF is then rasterized page by page into PNG images for perslide evaluation of *content quality* and *visual design*. For *completeness* and *fidelity*, we provide the evaluator with the full set of slide screenshots, together with the task specification JSON and source\_brief.md (including inline figures), so that it can make a global judgment based on both the output artifact and the source requirements.

Front-end Web Design. For front-end web design, we first use Claude 4.6 Opus to simulate user interaction with the generated website through vision- and DOM-grounded browsing. This step is necessary because web evaluation often involves multiple pages, navigation paths, and interaction states that cannot be captured by static screenshot. The browsing agent produces both screenshots and a structured browsing evaluation report containing page-level loading status, discovered sections, missing sections, and navigation outcomes. Based on these collected screenshots, we evaluate *visual design* and *responsiveness*. For responsiveness, we render the website under multiple viewport settings, including device sizes corresponding to iPhone 13 and iPad 7, to assess layout adaptation across screen sizes. In practice, we find that using only full-page screenshots often leads to excessive image compression and loss of fine-grained details. We therefore adopt a hybrid screenshot strategy: the evaluator receives both full-page screenshots for global structural understanding and viewportbased sequential screenshots (with a viewport height of 900px) for local detail inspection.

Poster Generation and Data Visualization. For poster generation and data visualization, the final artifacts are single PNG images, so we directly use the generated images as inputs to the VLM evaluator. The evaluation is grounded in the pre-defined task specification, including criteria such as

<span id="page-17-2"></span><sup>4</sup>For runtime stability and reproducibility, we fix the installed versions of the CLI-based agent frameworks in the execution environment.

coverage of required sections and goal insight satisfaction, in order to assess whether the produced artifact fulfills the requested content and communicative goals.

In addition, for data visualization, we further incorporate an agent-based evaluation component to assess *data accuracy*. Specifically, we provide the evaluator with both the execution trajectory of the task and the original plotting data file (e.g., source\_data.json), and ask it to extract the chart-construction steps and verify whether the generated visualization correctly uses the intended data. This produces a step-level evaluation report focused on the correctness of data usage.

**Report Generation.** For report generation, we first convert the generated HTML report into PDF format, and then apply the same VLM-based screenshot evaluation strategy used for web design: we provide both full-page renderings and segmented screenshots to balance global structure assessment with fine-grained content inspection. For numerical claims and factual consistency, we further introduce an agent-based evaluation procedure. Specifically, we provide the evaluator with the generated HTML report together with the underlying Kaggle dataset, and ask it to analyze the reported claims step by step through code-based verification, producing a step-level evaluation report focused on data consistency and claim correctness.

| Task                                                               | Dimension                                                                                              | Method                                                | Description                                                                                                                                                                                                                                                      |
|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| <b>Presentation Generation</b>                                     | content_quality<br>visual_design<br>completeness<br>fidelity                                           | VLM-judge<br>VLM-judge<br>VLM-judge<br>VLM-judge      | Per-slide text quality Per-slide visual aesthetics Whole-deck task requirement coverage Whole-deck factual consistency with source_brief.md                                                                                                                      |
| Front-end Web Design                                               | visual_design<br>responsive<br>navigation_pass_rate<br>interaction_pass_rate<br>data_display_pass_rate | VLM-judge<br>VLM-judge<br>Agent<br>Agent<br>Agent     | Aesthetics on full-page screenshots Layout consistency across desktop / tablet / mobile Playwright tests inter-page navigation links Playwright tests interactive components (accordions, modals, etc.) Playwright extracts displayed content vs. expected items |
| Poster Generation                                                  | content_quality<br>visual_design<br>completeness                                                       | VLM-judge<br>VLM-judge<br>VLM-judge                   | Data accuracy and traceability to source_brief.md Color, layout, typography, polish Coverage of required sections / metrics                                                                                                                                      |
| Data Visualization                                                 | insight_expression<br>visual_quality<br>completeness<br>data_accuracy                                  | VLM-judge<br>VLM-judge<br>VLM-judge<br>Agent          | Whether the chart conveys the goal insight Color, layout, label completeness Task requirement fulfillment Traces trajectory.json to verify data lineage to source_data.json                                                                                      |
| content_quality visual_quality completeness data_accuracy fidelity |                                                                                                        | VLM-judge<br>VLM-judge<br>VLM-judge<br>Agent<br>Agent | Writing quality, clarity, depth of analysis<br>Chart selection, color, labels, readability<br>Coverage of required sections / KPIs<br>Python code compares numbers in report vs. data.csv<br>Verifies extracted claims against data.csv                          |

Table 3: Evaluation matrix across the five OPENSKILLEVAL task categories. Each task is decomposed into multiple evaluation dimensions, which are scored either by a VLM judge (using visual or textual rubrics on a 1–5 scale) or by an evaluation agent (using programmatic verification to produce a score or pass rate). To enable consistent comparison across metrics, pass rates are linearly mapped to the 1–5 scale via 4x+1.

## <span id="page-18-0"></span>A.3 Task Input Schemas

This section presents the task input schemas used in our benchmark construction pipeline. During automatic case generation, each collected source is transformed into a task-specific structured specification (stored as task\_input.json) following the corresponding schema. These schemas define the core information required for each downstream task, and serve as the intermediate representation from source materials to executable task instances.

## 1. Data Visualization

```
{
    // Meta -- required
    "application": "data-visualization",
    "case_id": "case-climate-trends",
    "language": "en",
```

```
// Style -- optional (omit to test agent autonomy)
  "style": {
    "theme": "scientific",
    "audience": "researchers and policy makers",
    "tone": "clean, publication-ready"
  },
  // Goal -- required (one insight per case; chart_type chosen by agent)
  "goal": {
    "id": "warming-trend",
    "insight": "Show the accelerating global warming trend over 75 years"
  }
}
```

## **2. Poster Generation**

```
{
 // Meta -- required
 "application": "poster-generation",
 "case_id": "case-01-data-report",
 "language": "en",
 // Poster constraints -- optional
 "poster": {
   "aspect_ratio": "landscape", // landscape | portrait | square | A0-landscape | ...
   "audience": "data-report",
   "tone": "data-forward, professional",
 },
 // Content brief -- optional
 "brief": {
   "title": "2025 AI Agent Trends",
   "one_liner": "One-line overview",
   "goal": "What the audience should take away"
 },
 // Sections -- optional (agent plans structure if omitted)
 "sections": [
   { "id": "overview", "title": "Market Overview",
     "objective": "Show overall market size and growth" }
 ],
 // Metrics -- optional
 "metrics": [
   { "name": "Market Size", "current": "$12B", "target": "$45B (2027)" }
 ]
}
```

## **3. Presentation Generation**

```
{
  // Meta -- required
  "application": "ppt-generation",
  "case_id": "case-01-internal-review",
  "language": "en",
  // Deck constraints -- optional
  "deck": {
```

```
"aspect_ratio": "16:9", // default 16:9
   "slide_count": 6, // omit to let agent decide
   "audience": "internal product review",
   "tone": "professional, concise"
 },
 // Content brief -- optional
 "brief": {
   "title": "SkillArena Q4 Proposal",
   "one_liner": "One-line overview",
   "goal": "What the audience should understand or decide"
 },
 // Slide blueprint -- optional (agent plans deck if omitted)
 "slides": [
   { "id": "why-now", "title": "Why Now",
     "objective": "Help reviewers understand the launch context" }
   // ...
 ]
}
```

## **4. Report Generation**

```
{
  // Meta -- required
  "application": "report-generation",
  "case_id": "case-01-sales-analysis",
  "language": "en",
  // Report constraints -- optional
  "report": {
    "type": "sales-report",
    "audience": "management",
    "tone": "professional, data-forward"
  },
  // Content brief -- optional
  "brief": {
    "title": "2024 Q4 Sales Performance Report",
    "one_liner": "One-line overview",
    "goal": "What readers should take away"
  },
  // Section blueprint -- optional
  "required_sections": [
    { "section_id": "executive-summary",
      "title": "Executive Summary",
      "objective": "Key findings and core metrics at a glance" }
    // ...
  ],
  // KPI definitions -- optional
  "kpis": [
    { "name": "Total Sales", "description": "All Q4 sales revenue" }
  ],
  // Analysis dimensions -- optional
  "analysis_dimensions": ["product", "region", "time_trend"]
}
```

## **5. Web Design**

```
{
 // Meta -- required
 "application": "web-design",
 "case_id": "case-01-landing-page",
 "language": "en",
 // Site constraints -- optional
 "site": {
   "type": "landing-page",
   "page_count": 2, // omit to let agent decide
   "audience": "developers and technical decision-makers",
   "tone": "modern, professional, bold",
   "responsive": true, // default true
   "dark_mode": false // default false
 },
 // Content brief -- optional
 "brief": {
   "title": "TechPulse -- API Platform",
   "one_liner": "Next-gen API management and deployment",
   "goal": "Help visitors grasp the value prop and sign up"
 },
 // Page blueprint -- optional
 "pages": [
   { "page_id": "home", "file": "index.html",
     "sections": ["hero", "features", "testimonials", "cta", "footer"],
     "objective": "Homepage with value prop and sign-up CTA" },
   { "page_id": "pricing", "file": "pricing.html",
     "sections": ["pricing-tiers", "faq", "cta", "footer"],
     "objective": "Pricing page with three-tier comparison" }
 ],
 // Cross-page navigation -- optional
 "navigation": [
   { "from": "home", "trigger": "navbar 'Pricing' link", "to": "pricing" },
   { "from": "home", "trigger": "'Get Started' CTA button", "to": "pricing" }
 ],
 // In-page interactions -- optional
 "interactions": [
   { "id": "faq-accordion", "page": "home",
     "trigger": "click on FAQ question",
     "expected": "expand to show the answer; click again to collapse",
     "type": "toggle" },
   { "id": "pricing-switch", "page": "pricing",
     "trigger": "toggle 'Monthly / Yearly' switch",
     "expected": "all three tier prices update in sync",
     "type": "state-change" }
 ],
 // Required data display -- optional
 "data_display": [
   { "id": "pricing-table", "page": "pricing", "type": "table",
     "source_ref": "comparison table in source_brief.md",
     "expected_content": ["Free", "Pro", "Enterprise", "10K/mo", "1M/mo"],
     "description": "Feature comparison across three pricing tiers" },
   { "id": "hero-stats", "page": "home", "type": "stats",
     "source_ref": "core metrics in source_brief.md",
     "expected_content": ["50,000+", "99.99%", "50ms"],
     "description": "Show 3-4 key numerical metrics in the hero area" }
 ]
}
```

## <span id="page-22-0"></span>A.4 Human Evaluation

To validate both the quality of the automatically generated task instances and the reliability of our Automatic Evaluation Pipeline, we conduct a human evaluation study. Specifically, we randomly sample 100 task instances, balanced across the five task categories, and ask four senior researchers in natural language processing to perform the assessment. For each sampled instance, evaluators are provided with: (1) the task input, including the natural-language instruction and corresponding task specification; and (2) the generated output artifact. Because many of the task instances involve complex files and multimodal outputs, we build a dedicated web-based interface to support side-byside inspection. As shown in Figure [8,](#page-22-1) the interface presents the task details and reference materials in a structured format for easier reading. We also provide task-specific artifact visualizations, as shown in Figure [9.](#page-23-0) For example, web-design outputs are deployed in an interactive front-end environment for direct inspection, while generated slide decks are converted into PDFs for convenient review.

<span id="page-22-1"></span>![](_page_22_Figure_2.jpeg)

Figure 8: Web-based interface for human evaluation of generated task instances.

The detailed guidelines for evaluating the generated task instances are shown below. For artifact evaluation, we directly adopt the evaluation prompts used in our VLM-based automatic evaluation pipeline; full details are provided in Appendix [A.6.](#page-25-0)

## Task Instances Evaluation Guideline

Read the instruction text and reference data in the task details above, and evaluate the quality of the instruction itself (regardless of the model output). Rate it on a scale of 1–3. Each case only needs to be evaluated once.

#### Fluency — Linguistic quality of the instruction text

- 3 Grammatically correct, fluent and natural, accurate terminology
- 2 Minor grammar or wording issues, slightly affects readability
- 1 Multiple grammar errors or unclear wording, severely impedes comprehension

## Coherence — Logical clarity of the instruction

- 3 Clear goal, logically consistent requirements; expected output is unambiguous after reading
- 2 Goal is mostly clear, but some requirements are vague or ambiguous
- 1 Description is chaotic, requirements conflict or are severely vague

#### Completeness — Whether information suffices to complete the task

- 3 All essential information present: data source specified, output format clear, constraints stated
- 2 Core information present, but some details are missing; agent must make assumptions
- 1 Critical information is missing; agent cannot reliably complete the task

#### <span id="page-23-0"></span>**Web-Design:**

![](_page_23_Figure_13.jpeg)

#### **Presentation Generation:**

![](_page_23_Picture_15.jpeg)

Figure 9: Artifact inspection interface used in human evaluation. The system provides task-specific visualization of generated outputs, including interactive web pages for front-end design tasks and converted PDF views for presentation outputs.

## A.5 More Experimental Result

<span id="page-24-0"></span>![](_page_24_Figure_0.jpeg)

Figure 10: Skill performance versus cost across tasks and agent systems. Each subplot corresponds to one model-task pair, where the x-axis shows average token cost and the y-axis shows overall task performance. Colored points denote different skills, while the gray point marks the *no-skills* baseline. The dashed vertical and horizontal lines indicate the baseline cost and performance, respectively, so that points in the upper-left region represent the most desirable outcomes: higher quality at lower cost. The results show that skill augmentation is highly heterogeneous across models and tasks: some skills consistently improve performance, while others increase cost without yielding meaningful gains.

<span id="page-24-1"></span>![](_page_24_Figure_2.jpeg)

Figure 11: Impact of web design skills on stylistic diversity relative to the *no-skills* baseline, measured by changes in within-group Vendi Score computed from CSD-ViT-L style embeddings. Positive values indicate more diverse outputs under a given skill, while negative values indicate stronger stylistic convergence. The *pool* column aggregates outputs across all skills for cross-skill analysis.

## <span id="page-25-0"></span>A.6 Evaluation Prompt

{source\_brief}

--- END SOURCE CONTEXT ---

## **1. Data Visualization**

```
Insight Expression single image
Evaluate the **insight expression** of this data visualization.
The visualization was created to convey a specific insight:
**Goal insight**: {insight}
Criteria:
- Does the chosen visualization type effectively communicate this insight?
- Can the reader **actually** understand the key message at a glance, as rendered?
- Are there effective annotations, highlights, or emphasis that draw attention to the
    insight?
- Is the presentation approach well-suited to the data characteristics?
- Does the visualization tell a clear story, or does the reader have to work to extract
    meaning?
Important: Judge the **end result as the reader would experience it**. A structurally
    sound approach that is undermined by severe rendering problems (e.g., overlapping
    labels hiding key annotations, illegible text in critical areas) should be scored
    lower -- the insight is only "expressed" if the reader can actually perceive it.
    Conversely, do NOT double-penalize minor cosmetic issues already covered by Visual
    Quality; only penalize rendering problems that **directly obstruct** the target
    insight.
Note: The creator was free to choose ANY chart type or visual approach. Do NOT penalize
    for unconventional choices -- judge ONLY whether the insight is effectively
    conveyed.
Scoring (1-5):
- 5: Reader grasps the key message immediately as rendered, clever use of
    annotation/emphasis/contrast, all insight components clearly visible
- 4: Insight clearly expressed, reasonable approach, minor gaps in emphasis or
    supporting elements
- 3: Insight basically understandable but presentation is generic or partially
    obscured, reader must interpret on their own
- 2: Presentation approach mismatches the insight goal, or key information is
    buried/illegible
- 1: Cannot read the target insight from the visualization
Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}
Data Accuracy single image + source text
Evaluate the **data accuracy and factual fidelity** of this data visualization.
You are given the visualization, the original data, and background context. Check:
- Are the data points, proportions, and trends consistent with the source data?
- Are axis scales, labels, and values correct?
- Are any annotations or callouts traceable to the source material?
- Is there any fabricated data or misleading representation?
--- SOURCE DATA ---
{source_data}
--- END SOURCE DATA ---
--- SOURCE CONTEXT ---
```

```
Scoring (1-5):
- 5: All data points, proportions, and trends match source exactly; annotations
    traceable to source; no fabrication
- 4: Core data correct, minor deviations in secondary data points or slight
    extrapolation
- 3: Mostly correct, but notable numerical errors, proportion distortion, or
    untraceable annotations
- 2: Multiple data inconsistencies with source, or obvious fabricated content
- 1: Extensive data errors or fabrication, visualization is not trustworthy
Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}
Visual Quality single image
Evaluate the **visual quality** of this data visualization.
Criteria:
- Color scheme: harmonious palette, appropriate for the topic, colorblind-friendly if
    applicable
- Layout: clean arrangement, proper spacing, nothing overlapping
- Labels and annotations: title, axis labels, legend, units -- all present and readable
- Typography: readable fonts, clear size hierarchy
- Professional finish: publication-ready quality, attention to detail
Scoring (1-5):
- 5: Harmonious colors, polished layout, complete labels (title/axes/legend/units),
    publication-grade professional quality
- 4: Good colors and layout, labels mostly complete, minor flaws (uneven spacing, label
    overlap)
- 3: Basic colors, functional layout but lacks design sophistication, some labels
    missing
- 2: Monotonous or clashing colors, rough layout, labels severely lacking
- 1: Chaotic styles, overlapping elements, visually unacceptable
Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}
Completeness single image
Evaluate the **task completeness** of this data visualization.
The task requirements are provided below. Check whether the goal's insight is expressed
    and all requirements are met.
Task requirements:
{task_requirements}
Scoring (1-5):
- 5: Goal insight fully expressed, all requirements completely satisfied
- 4: Core requirements met, minor omissions (e.g., missing unit or a specific
    annotation)
- 3: Most requirements met, but notable gaps
- 2: Only partially satisfied
- 1: Key requirements not met, output unusable
```

## **2. Poster Generation**

## **Design single image**

Evaluate the \*\*visual design quality\*\* of this poster/infographic.

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

```
Criteria:
- Color scheme: harmonious palette, appropriate for the topic and tone
- Layout: clean alignment, proper spacing, clear visual hierarchy
- Typography: readable fonts, clear size hierarchy (title > heading > body)
- Consistency: unified style throughout (colors, fonts, spacing)
- Professional polish: attention to detail, no overlapping elements
Scoring (1-5):
- 5: Harmonious colors, polished layout, clear hierarchy, professional design quality
- 4: Good colors and layout, minor flaws (slight misalignment, spacing issues)
- 3: Basic color scheme, layout functional but lacks design sophistication
- 2: Monotonous or clashing colors, rough layout
- 1: Chaotic styles, overlapping elements, hard to read
Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}
Completeness single image
Evaluate the **task completeness** of this poster/infographic.
The task requirements are provided below. Check whether ALL requirements are met.
Task requirements:
{task_requirements}
Scoring (1-5):
- 5: All requirements fully satisfied
- 4: Core requirements met, minor omissions
- 3: Most requirements met, some notable gaps
- 2: Only partially satisfied
- 1: Key requirements not met
```

## **3. PPT Generation**

## **Content per-slide image**

Evaluate the \*\*content quality\*\* of this presentation slide.

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

Judge how effectively this slide delivers its key message to the reader.

#### Criteria:

- Key message: does the slide have a clear takeaway that the reader can grasp?
- Information density: appropriate amount of content (not too crowded, not too sparse)
- Clarity: text is well-written, grammatically correct, easy to understand
- Text-visual balance: charts/images complement the text and reinforce the message
- If rendering issues (truncated text, blank charts) cause information to be LOST, deduct proportionally to how much of the slide's message is affected. But if the core message still comes through despite minor visual flaws, do not over-penalize - visual polish is scored under Design.

#### Scoring (1-5):

- 5: Clear key message, well-developed points, visuals and text complement each other
- 4: Key message clear, good content, but minor gaps (e.g., a chart lacks labels, text slightly sparse)
- 3: Core information present but message is diluted (e.g., missing title, no clear takeaway, or significant content lost to rendering)
- 2: Key message unclear, content poorly organized or mostly lost to rendering issues

- 1: No discernible message -- slide is blank, empty, or content entirely unreadable

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

## **Design per-slide image**

Evaluate the \*\*visual design\*\* of this presentation slide.

#### Criteria:

- Color scheme: harmonious, appropriate for the tone
- Layout: clean alignment, proper spacing, no overlapping elements
- Typography: readable fonts, clear hierarchy (title vs body)
- Visual elements: backgrounds, icons, shapes that enhance the message
- Consistency: matches the overall deck style

#### Scoring (1-5):

- 5: Harmonious colors, engaging visual elements, professional and polished
- 4: Good colors with some visual elements, minor design flaws
- 3: Basic color scheme, with rough layout and no supplementary visual elements
- 2: Monotonous black/white, readable but unappealing
- 1: Conflicting styles, content difficult to read

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

## **Completeness full deck images**

Evaluate the \*\*task completeness\*\* of this presentation.

Check whether the required CONTENT is present in the slides. For each requirement below, determine if the corresponding content exists in the presentation.

#### Task requirements:

{task\_requirements}

#### Important:

- Judge whether the required content IS PRESENT, not how it looks visually.
- A chart that renders blank or empty counts as MISSING content (deduct).
- Text that is overlapping or hard to read but IS present counts as COMPLETE (do not deduct -- visual issues are scored under Design).

#### Scoring (1-5):

- 5: All required content present -- every section, data point, and chart accounted for
- 4: Core content present, minor omissions (e.g., one data point or detail missing)
- 3: Most content present, but some required sections or charts are missing
- 2: Only partially complete -- multiple required elements missing
- 1: Key required content not present

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

## **4. Report Generation**

#### **Content Quality report text only**

Evaluate the \*\*content quality\*\* of this report across two aspects: writing quality AND analysis depth.

#### A. Writing & Structure:

- Organization: clear headings, logical flow, well-structured executive summary
- Clarity: well-written, grammatically correct, easy to understand
- Information density: appropriate amount of content (not too sparse, not overwhelming)

- Logical consistency: no self-contradicting claims or misleading interpretations
- B. Analysis Depth:
- Are insights substantive (backed by statistics specific data) or surface-level (just restating numbers)?
- Does the analysis go beyond descriptive statistics (e.g., correlation, attribution, comparison)?
- Are conclusions and recommendations data-driven and specific (not generic advice)?
- Is there unnecessary redundancy (e.g., same data presented in multiple formats without adding value)?

#### Scoring (1-5):

- 5: Excellent writing AND deep analysis -- insights are substantive, data-driven, logically consistent, with no redundancy
- 4: Good writing and organization, but some sections lack analytical depth or have minor redundancy
- 3: Adequate structure but analysis is mostly surface-level, or notable redundancy/inconsistency
- 2: Poor organization, stiff writing, and shallow analysis
- 1: Chaotic structure, grammar errors, no real analysis

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

## **Visualization full-page overview + scrolled crops**

Evaluate the \*\*visualization quality\*\* of this report.

#### Criteria:

- Chart type selection: appropriate for the data (bar for comparison, line for trend, pie for composition, etc.)
- Color scheme: professional, harmonious, accessible
- Labels and annotations: axis titles, data labels, legends, units
- Readability: data is immediately clear from the visualization
- Tables: properly formatted, aligned, with clear headers

#### Scoring (1-5):

- 5: Chart types perfectly matched to data, professional colors, complete annotations, data immediately clear
- 4: Good chart types, has titles and labels, good visual effect
- 3: Basic charts present, but type selection or labels could be improved
- 2: Few charts or wrong types, missing labels
- 1: No charts or charts are incomprehensible

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

#### **Completeness report text only**

Evaluate the \*\*task completeness\*\* of this report.

Go through EVERY requirement below and check whether it is substantively addressed in the report. Do NOT just check if a section heading exists -- verify that the actual content within each section fulfills what was asked. For example, if a KPI is required "segmented by genre and year", check that BOTH segmentations are present, not just one.

### Task requirements:

{task\_requirements}

#### Scoring (1-5):

- 5: Every requirement substantively addressed -- all sections have the requested content, all KPIs present with required segmentation
- 4: Core requirements met, but 1-2 minor details missing (e.g., a KPI lacks one segmentation dimension)
- 3: Most requirements met, but notable gaps (e.g., a section is present but missing key requested analysis)

```
- 2: Only partially satisfied -- multiple sections lack required content
```

- 1: Key requirements not met

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

## **5. Web Design**

#### **Visual Design per-page multi-image (full + crops)**

Evaluate the \*\*visual design execution quality\*\* of this web page.

#### Criteria:

- Color & typography: harmonious palette, readable fonts, clear heading hierarchy (h1 > h2 > body), consistent font sizing
- Layout & structure: well-organized sections, clear information hierarchy, consistent grid alignment, no misaligned or jagged elements
- Spacing & polish: appropriate white space between sections, no elements overlapping or clipped, no exposed HTML tags or rendering artifacts
- Placeholder handling: the task does NOT provide image/video assets, so placeholder elements are expected. Do NOT penalize for the absence of real images. Instead, evaluate whether placeholders are well-designed -- appropriate size and position, consistent styling with the overall theme (e.g., labeled gray boxes are better than empty black voids)

Note: the first image is a fullpage overview, subsequent images are detail crops scrolled top-to-bottom. Boundary cuts between detail images are screenshot artifacts.

## Scoring (1-5):

- 5: Harmonious color palette with intentional accent choices; typography has clear h1/h2/body hierarchy with consistent sizing; sections are well-separated with balanced spacing; grid alignment is pixel-consistent; placeholders are styled to match the theme (e.g., colored boxes with labels, icon placeholders)
- 4: Color palette is coordinated, typography hierarchy is clear, layout is well-organized; has 1-2 minor issues such as: one section has slightly uneven spacing, a placeholder is slightly oversized, a font weight is inconsistent in one area
- 3: Has a color scheme and basic section structure, but execution is noticeably rough: spacing is uneven across sections, heading sizes are inconsistent, placeholders are unstyled empty blocks, or the page feels like a wireframe with colors applied
- 2: Multiple visible problems: elements overlap or get clipped, sections are misaligned, exposed HTML tags or broken CSS visible, color choices clash, or large portions of the page are visually broken
- 1: Page renders as unstyled HTML (no CSS applied), or the page fails to load / displays a blank screen

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}

#### **Responsive per-device screenshots (mobile / tablet)**

Evaluate the \*\*responsiveness\*\* of this website on a {device\_name}.

You are shown screenshots captured with {device\_description}. Each screenshot is from a different page of the same website. Evaluate the overall responsive quality across all pages shown.

## Criteria:

- No horizontal scrollbar / content overflow
- Navigation is accessible (hamburger menu or adapted nav)
- Touch targets are appropriately sized (>=44px)
- Text is readable without zooming

- Content adapts to the viewport width (no desktop layout forced into a smaller screen)

Note: the task does NOT provide image/video assets. Pages may contain elements explicitly labeled or styled as placeholders (e.g., boxes with "placeholder" text, icons indicating missing media). Do NOT penalize these as a responsive issue - only evaluate how the layout, navigation, and content elements adapt to this viewport.

#### Scoring (1-5):

- 5: No overflow, navigation properly adapted (e.g., hamburger menu on mobile), touch targets well-sized, content reflows cleanly to viewport width
- 4: Good adaptation overall; 1-2 minor issues such as: nav items slightly tight, one button partially clipped at edge, or slight spacing inconsistency
- 3: Has viewport meta and attempts responsive layout, but noticeable problems: nav not collapsed, some text requires horizontal scroll, or several elements are cramped
- 2: Layout significantly broken: content overflows viewport, navigation is unusable, or desktop layout is forced into the smaller screen
- 1: No responsive handling at all -- page renders at desktop width requiring zoom and scroll

Return JSON: {"score": <1-5>, "reason": "<brief explanation>"}