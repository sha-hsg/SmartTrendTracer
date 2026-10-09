# A Technical Taxonomy of LLM Agent Communication Protocols

Linus Sander , Habtom Kahsay Gidey , Alexander Lenz and Alois Knoll

Technische Universität München, Munich, Germany.

\*Corresponding author(s). E-mail(s): linus.sander@tum.de; habtom.gidey@tum.de; Contributing authors: alex.lenz@tum.de; knoll@tum.de;

#### **Abstract**

As large language models (LLMs) advance and multi-agent systems aim to overcome the limits of standalone agents, robust communication protocols are becoming essential infrastructure for distributed agent networks. Nonetheless, the fragmented protocol landscape presents a significant interoperability challenge. This study develops a technical taxonomy to classify and analyze LLM agent communication protocols. Following an established iterative method, we defined the taxonomy's purpose, meta-characteristic, and ending conditions, then performed five iterations, three empirical-to-conceptual and two conceptual-toempirical, on nine actively maintained open-source protocols with demonstrable adoption. The taxonomy comprises five dimensions: counterparty, payload, interaction state, discovery mechanism, and schema flexibility. Classification reveals recurring architectural patterns: all sampled agent-to-agent protocols combine hybrid payloads with session-state persistence; most protocols support multiple predefined schemas, and two negotiate schemas at runtime, indicating a trend toward schema flexibility; decentralized discovery remains rare. Analysis suggests short-term convergence pressure toward protocols unifying agent-to-agent and agent-to-context (tool and data) communication. Long-term, however, no single protocol is likely to maximize versatility, efficiency, and portability simultaneously. The field will more likely evolve toward a federated, layered protocol stack. The framework guides protocol selection and highlights open research gaps such as privacy and policy enforcement.

**Keywords:** Agent Communication Protocols, Internet of Agents, Taxonomy Development, Multi-agent systems, LLM based Agents

# **1 Introduction**

Recently, large language model (LLM) based agents have attracted significant attention in AI research [[1–](#page-23-0)[3\]](#page-23-1). LLMs incorporate extensive world knowledge [\[4](#page-23-2)] along with advanced reasoning and planning capabilities [\[5](#page-23-3)[–7](#page-23-4)]. Embedded as the agent's core and equipped with memory, sensors, and actuators, the LLM grants the agent the capacity to interact dynamically with its environment and to perform efficient multistep reasoning, thereby enabling it to solve complex real-world tasks [\[8](#page-23-5)[–10](#page-24-0)].

Building on single LLM agents, a promising next frontier involves multiple cooperating agents. Such multi-agent systems (MAS) consist of specialized agents that communicate, collaborate, and debate with one another [[11,](#page-24-1) [12](#page-24-2)]. Rooted in the principles of collective intelligence [\[13](#page-24-3)], this approach further enhances the system's problem-solving capabilities, yielding outcomes superior to those achievable by any individual agent [[11,](#page-24-1) [14,](#page-24-4) [15](#page-24-5)]. Here, one detail must not be overlooked: without a communication mechanism, no collective intelligence can arise. This crucial piece of infrastructure serves as the backbone that enables collective intelligence in MAS [[1,](#page-23-0) [11](#page-24-1), [16](#page-24-6)].

To build and explore such systems, various frameworks exist that allow developers to construct MAS at varying levels of abstraction for diverse applications. Widely used examples include Microsoft's *AutoGen* [\[17](#page-24-7), [18\]](#page-24-8), *CrewAI* [\[19](#page-24-9)], CAMEL [\[20](#page-24-10), [21\]](#page-24-11), and *LangGraph* [[22\]](#page-24-12). This variety of frameworks, however, has introduced a new challenge: a common protocol becoming necessary to standardize agent communication. Such standardization is a fundamental step toward unlocking the full potential of distributed MAS, where heterogeneous agents can dynamically discover each other and collaborate seamlessly across diverse use cases [\[16](#page-24-6), [23,](#page-25-0) [24](#page-25-1)]. Moreover, this standardization should extend to access to external systems, such as APIs or services, to enable seamless agent integration [\[25](#page-25-2)]. To overcome the antipattern of hard-coded communication pipelines, such a protocol must define the mechanics by which agents interact consistently, efficiently, and securely, with both other agents and external systems [\[16](#page-24-6), [24,](#page-25-1) [26,](#page-25-3) [27\]](#page-25-4).

As the field of LLM-based agents is still relatively new and rapidly evolving, no universally accepted standard has yet emerged. Numerous solutions overlap in capability and are not interoperable with one another. To date, explicit communication protocols have not been widely studied, yet they are becoming an essential prerequisite for efficient cooperation and scalable MAS [\[16](#page-24-6), [24](#page-25-1), [27\]](#page-25-4).

In this paper, we investigate the emerging landscape of communication protocols for LLM-based agents by developing a comprehensive taxonomy and analyzing nine concrete protocol implementations. Our taxonomy provides a coherent framework for understanding and classifying these protocols, as well as for tracking future developments. Finally, we present our key findings and conclude with a brief outlook on future developments.

# **2 Background**

This section lays the groundwork for developing the taxonomy. It first examines LLMbased agents and MAS, before turning to the foundations of communication protocols that enable standardized agent coordination and interaction.

### <span id="page-2-0"></span>**2.1 LLM-Based Agents**

Back in 1998, Russell [\[28](#page-25-5)] argued that "AI is about the construction of intelligent agents", noting that such agents are crucial for coping with dynamic, partially observable, and stochastic environments. An agent is generally understood as an autonomous entity that perceives its environment and takes actions to achieve specified goals [[29,](#page-25-6) [30](#page-25-7)]. While early AI research paid limited attention to agents, interest grew significantly from the mid-1980s onward [[31\]](#page-25-8). Common defining characteristics of agents exhibiting genuinely intelligent behavior include autonomy, reactivity, proactivity, social ability, and strong reasoning capabilities [\[28](#page-25-5), [30](#page-25-7), [32](#page-25-9)].

### **2.1.1 LLM-Centric Control**

With the rise of large language models (LLMs), LLM-based agents have emerged as a new paradigm [\[3](#page-23-1)]. Trained on massive text corpora, models such as GPT-4 (2023) [\[5](#page-23-3)], DeepSeek-V3 (2024) [\[33](#page-25-10)], or Claude Opus 4 (2025) [\[34](#page-25-11)] have demonstrated impressive language understanding and generation capabilities. Beyond language processing, these models exhibit a range of emergent capabilities, including human-like reasoning, planning, decision-making [[5,](#page-23-3) [6](#page-23-6), [8](#page-23-5)], self-reflection [\[35](#page-25-12), [36](#page-26-0)], zero-shot learning [\[37](#page-26-1)], creativity [[38\]](#page-26-2) and more [[39\]](#page-26-3).

Unlike narrow models, LLMs enable agents to often require little or no task-specific training data. They can perform informed actions out-of-the-box using their internal knowledge [[40–](#page-26-4)[42\]](#page-26-5). In practice, an LLM agent can receive a high-level goal in text and autonomously plan and act to accomplish it, using the language model itself to guide multistep reasoning and planning [\[43](#page-26-6)[–45](#page-26-7)]. It is even argued that LLMs pave a promising path toward general AI agents [[3\]](#page-23-1) and that agents "further push the boundary of LLMs towards AGI" [[46\]](#page-26-8), with self-improvement, autonomy, and continual learning as key components.

A typical workflow for an autonomous LLM-based agent unfolds as follows. The agent first receives a *task* or high-level goal as text. It then begins to *think* by generating natural language, creating subtasks, and devising a plan. Next, it *acts* within its environment, executing the plan through appropriate tools. Finally, by *observing* the environment and reviewing outcomes, the agent gathers *feedback*, enabling it to re-plan, learn, and perform another iteration as needed [[44,](#page-26-9) [47\]](#page-27-0).

### **2.1.2 Fundamental Components and Concepts**

One of the core ideas behind LLM agents is to combine language-based reasoning with structured control, and equipping the agent with components such as long-term memory and specialized tools [\[2](#page-23-7), [47,](#page-27-0) [48\]](#page-27-1). Figure [1](#page-4-0) provides a high-level overview of an agent system's key components and their connections to the external world.

#### *Reasoning and Planning*

LLMs exhibit strong reasoning capabilities [[7\]](#page-23-4), which form the foundation of successful problem-solving, decision-making, and planning [[3,](#page-23-1) [49](#page-27-2)]. A wide range of techniques has been explored to enhance these capabilities further [[2,](#page-23-7) [50](#page-27-3)], ranging from task decomposition and planning approaches to continuous self-reflection loops that support adaptation. Task decomposition, in particular, helps an agent produce more granular and reliable plans for each subtask [[43,](#page-26-6) [45,](#page-26-7) [51](#page-27-4)]. Self-reflection mechanisms enable the agent to detect errors, revise its strategy, build resilience through adaptive self-healing, and tackle complex, long-horizon tasks [\[44](#page-26-9), [52](#page-27-5), [53](#page-27-6)].

#### *Knowledge and Memory*

Thanks to the LLM acting as the central controller, the agent has access to a vast amount of encoded knowledge embedded within the foundation model's weights [[4,](#page-23-2) [54\]](#page-27-7). Beyond this, the agent also has access to in-context data, such as recent user conversations, records of tool invocations, and the agent's own thought history. This session-bounded data is commonly referred to as short-term memory or working memory [\[55](#page-27-8)]. Furthermore, the agent can be equipped with access to persistent external data sources, such as internal documents, external databases, and retrievalaugmented generation (RAG), sharing principles with document-based knowledge discovery [[56–](#page-27-9)[59\]](#page-28-0).

### *Perception and Action*

To operate effectively in a specific environment, an agent must be able to perceive that environment, recognize its affordances, and act within it [\[60](#page-28-1), [61\]](#page-28-2). Beyond the obvious input of textual information, multimodal perception can provide valuable additional capability. Visual input is particularly rich in information when the agent's operating sphere is a subset of the real world, necessitating resilient design patterns for visual processing [[62–](#page-28-3)[65\]](#page-28-4).

The interface to the environment is typically realized by providing tools the agent can use, marking a key difference between agentic systems and pure LLMs [\[42](#page-26-5), [60\]](#page-28-1). By generating output in a specific format, typically a JSON snippet, the agent can invoke a tool with the required parameters and receive the resulting output upon execution [[60\]](#page-28-1). Thanks to LLMs' powerful zero-shot and few-shot learning capabilities, new tools can be acquired simply by including their description in the prompt [\[42](#page-26-5), [44](#page-26-9)]. Additionally, models fine-tuned for tool use have demonstrated strong effectiveness [[60,](#page-28-1) [66\]](#page-28-5).

#### *Applications*

Equipped with these capabilities, LLM agents can operate far beyond simple conversational exchanges and traditional human-machine interactions [\[67](#page-28-6)]. They can plan multistep processes, query knowledge sources, adapt over time, and more [\[50](#page-27-3), [55\]](#page-27-8). A variety of domains are now being tackled with specialized agents. These include computer control, ranging from code generation and terminal troubleshooting to GUI automation [[68–](#page-28-7)[71\]](#page-29-0). Knowledge work and cognitive automation, including innovation support, scientific workflow assistance, and knowledge exploration, are also now well

![](_page_4_Picture_0.jpeg)

**Fig. 1** Fundamental components of LLM agents.

<span id="page-4-0"></span>within reach [[38,](#page-26-2) [72](#page-29-1)[–75](#page-29-2)]. Across all of these areas, LLM agents are still at an early stage but are advancing rapidly [[47\]](#page-27-0).

#### *Challenges*

Despite their rapid advancement, LLM-based agents still face significant limitations that must be addressed for robust real-world deployment. Fundamentally, they are not immune to the inherent vulnerabilities of underlying foundation models, such as hallucination [[6,](#page-23-6) [76\]](#page-29-3), and finite context windows, which restrict the volume of historical data and environmental context they can process [[77–](#page-29-4)[79\]](#page-29-5). Next, autonomously generated plans are not guaranteed to be feasible or efficient [\[50](#page-27-3), [80](#page-29-6), [81\]](#page-29-7), and the reliable integration of multimodal information sources remains an ongoing challenge [\[50](#page-27-3)]. Also, many LLM agent techniques heavily rely on pure prompting. Yet minor prompt variations can produce entirely different outputs [[82\]](#page-30-0).

Given the capabilities of LLM based agents and the abstract ideas of CI, the next natural step is to explore the collaborative potential of multiple agents [\[12](#page-24-2), [83\]](#page-30-1). For instance, one could query a smaller LLM N times to produce a set of independent answers. By selecting the most common answer, this method can, interestingly, outperform a single call to a state-of-the-art model [\[84](#page-30-2)]. However, this captures only a narrow facet of CI, prompting a more fundamental question: what happens when we actively employ the communicative and social capacities of LLM agents to enable true cooperation? The following section addresses this question by a brief survey of the field of MAS.

### **2.2 Multi-agent systems**

### **2.2.1 LLM Based Multi-agent systems**

Multi-agent systems (MAS) consist of multiple agents that coordinate and communicate to accomplish a common goal. The idea is simple: independent, specialized agents jointly solve a task, thereby harnessing the benefits of collective intelligence [[11,](#page-24-1) [12](#page-24-2)]. Decomposing complex objectives into manageable subtasks and assigning them to specialized agents naturally simplifies problem-solving [\[15](#page-24-5), [50](#page-27-3), [85](#page-30-3)]. Furthermore, diverse perspectives and varied interaction styles across agents, such as mutual feedback and debate, further enhance MAS problem-solving capabilities beyond what single-agent systems can achieve [[86–](#page-30-4)[88\]](#page-30-5). Such systems can tackle dynamic, complex tasks with strong performance and show emergent cognitive behavior [[11,](#page-24-1) [89\]](#page-30-6).

### **2.2.2 Key Concepts**

At a high level, an MAS is built from two essential elements: the agents themselves and the architecture that connects them. Each agent is characterized by a specific profile, including its role, abilities, and toolset, while the architecture serves as the core infrastructure that defines and enables collaboration among all agents [\[16](#page-24-6), [90\]](#page-30-7). Having outlined the core elements of individual LLM agents in Section [2.1,](#page-2-0) we now turn to the fundamental concepts of LLM-driven MAS.

The optimal topology of an agent ensemble remains a central research concern, bringing forth various architectural challenges in cognitive agent design [[91\]](#page-30-8). Different *architectures* exist, ranging from equi-level designs, in which all agents operate at the same hierarchical level, to hierarchical configurations, where one or several agents guide the group as a leader. Subsequently, the communication structure may be either fixed or dynamic, requiring rigorous methods to model such dynamic architectures [[92\]](#page-30-9). In fully dynamic systems, agent roles, relationships, and even the number of participating agents can evolve over time [[1,](#page-23-0) [2,](#page-23-7) [86\]](#page-30-4).

Next, effective *coordination and decision-making* is vital. Agents must debate, consult one another, align their goals, and resolve misunderstandings. Because MAS often yield multiple possible solutions and parallel discussions, techniques are required to converge on a single solution. Typical strategies include majority voting, consensusseeking methods, or introducing a judge agent to make the final decision. [\[50](#page-27-3), [93\]](#page-31-0).

When looking more closely at the individual entities, the agents, *profiling* becomes especially important in MAS. The specialization of each agent is critical for an effective system. Roles, characterizations, behavior descriptions, and skill sets must be carefully crafted, primarily through precise prompting and LLM model selection [[21,](#page-24-11) [47,](#page-27-0) [87](#page-30-10)].

To successfully enable CI within MAS, a *communication backbone* is crucial [[11\]](#page-24-1). Without communication, agents cannot cooperate, debate, nor coordinate their actions. Ensuring that interactions are efficient and robust is therefore essential for achieving a reliable and high-performing MAS [[1,](#page-23-0) [16](#page-24-6)]. Therefore, given that MAS are expected to grow in size and distribution [[84,](#page-30-2) [94](#page-31-1)], standardized communication protocols are critical to achieve scalability and flexibility without sacrificing robustness [[24,](#page-25-1) [25](#page-25-2)]. They are key infrastructure elements that enable heterogeneous agents to connect reliably and dynamically. In essence, the communication infrastructure serves as the backbone enabling collective intelligence in MAS [[11,](#page-24-1) [16,](#page-24-6) [23,](#page-25-0) [26\]](#page-25-3).

### **2.3 Communication Protocols**

In computer science, a *protocol* is a formal set of rules or conventions that governs how entities, such as programs, processes, or agents, communicate and interact. It specifies the format, sequence, and meaning of the messages exchanged, enabling heterogeneous systems to understand one another straight away [[95,](#page-31-2) [96](#page-31-3)]. As Cerf and Kahn [[97\]](#page-31-4) note, computers must "share a common protocol (i.e., a set of agreed-upon conventions)" for data exchange to be meaningful.

In practice, a protocol specifies *what* data is communicated, *how* it is structured, and *when* it should be sent or acknowledged. By defining these dimensions precisely, protocols enable independent, potentially heterogeneous systems to communicate reliably. Often, they also include procedures for error handling, synchronization, and more, so that, even under adverse conditions, reliable communication is ensured [[95,](#page-31-2) [96](#page-31-3)].

The internet itself is the most obvious example of a protocol's importance. Foundational standards such as the *Internet Protocol* (IP) and the *Transmission Control Protocol* (TCP), together with the *Hypertext Transfer Protocol* (HTTP), form today's backbone of global data exchange [\[97](#page-31-4), [98\]](#page-31-5).

Beyond this, MAS require application-level protocols clarifying how autonomous agents interact. Before the rise of LLMs, well-known examples included the protocols *Knowledge Query and Manipulation Language* (KQML) [[99\]](#page-31-6) and *FIPA Agent Communication Language* (ACL) [\[100](#page-31-7)]. KQML, developed in the early 1990s, was introduced as "a new language and protocol for exchanging information and knowledge" among software agents. Central to KQML is an extensible set of operations called *performatives*, such as *ask* and *tell*, which lays the groundwork for higher-level interaction patterns like negotiation [\[99](#page-31-6), [100](#page-31-7)]. Its successor, ACL, represented the first organized effort to standardize communication in the broader agent community. Building on speech-act theory, ACL lets agents express intentions, requests, information, and proposals while each message follows a formal structure with fields for sender, receiver, content, and more, enabling interoperability across heterogeneous agents [\[100](#page-31-7)].

In LLM-based MAS, standardized communication protocols become essential for maintaining consistent, secure, and reliable interactions among heterogeneous agents [\[16](#page-24-6), [24,](#page-25-1) [25\]](#page-25-2). As systems scale, these protocols become a prerequisite for robust multi-agent collaboration, enabling greater efficiency, adaptability, and overall performance with minimal human intervention [\[23](#page-25-0), [27\]](#page-25-4).

# <span id="page-6-0"></span>**3 Related Work**

Several recent works have examined the emerging landscape of LLM agent communication protocols, highlighting both the rapid progress and the significant challenges that remain.

From a standardization standpoint, Li et al. [[27\]](#page-25-4) argue that the current fragmentation of agent communication resembles the early "protocol wars" of networking and advocate for a unified framework. Next, Du [[101\]](#page-31-8) examines AI agent communication through the perspective of Internet architecture, distilling five key design principles, to guide the sustainable development of multi-agent ecosystems. Moreover, Kong et al. [[24\]](#page-25-1) provide a comprehensive security-focused survey of agent communication, proposing a three-class taxonomy for categorizing agent communication, while systematically analyzing their associated vulnerabilities and potential defense mechanisms. Complementing those perspectives, Ehtesham et al. [\[25](#page-25-2)] offer a comparative analysis of four concrete interoperability protocols: MCP, ACP, A2A, and ANP, evaluating them across dimensions such as interaction modes, discovery mechanisms, and security models.

Further research exists on concrete protocols. Among the sample that is later examined, the Agora protocol [[102\]](#page-31-9) stands out for its scientific rigor and for emphasizing fundamental principles needed in an efficient, scalable, and robust design. In particular, Marro et al. [\[26](#page-25-3)] identified a *trilemma* of three quality attributes, none of which can be fully optimized simultaneously. First, *versatility* requires the protocol to support multiple message types, from text only to structured data. Second, *efficiency* demands minimal computational and networking costs. Third, *portability* is of focus, reducing the effort required for any arbitrary agent to adopt and use the protocol [[26\]](#page-25-3).

Last but not least, Yang et al. [\[103](#page-31-10)] also propose a taxonomy for LLM agent communication protocols. Their taxonomy comprises two dimensions: *object orientation*, which distinguishes *context-oriented* from *inter-agent* protocols according to the intended counterpart, and *application scenario*, which classifies protocols as either *general-purpose* or *domain-specific*. In addition to that, they collected a sample of 14 protocols and evaluated them against quality attributes such as efficiency, security, and scalability, identifying several emerging trends in agent development [[103\]](#page-31-10). Nevertheless, a taxonomy with just two dimensions seems insufficient to provide the abstract, hierarchical structure needed to explore, analyze, and understand the field in depth.

# <span id="page-7-0"></span>**4 Approach**

### **4.1 Taxonomy Development Method**

To develop the taxonomy itself, we followed the widely used method for taxonomy construction from Nickerson et al. [\[104](#page-31-11)]. This method was selected because it provides a structured, iterative, traceable, and reproducible procedure for constructing taxonomies, rather than relying on an ad hoc classification process [\[105](#page-31-12)]. We first begin this section by outlining and clarifying the qualities that define a useful taxonomy, then discuss the iterative procedure that drives its development as applied in this study.

The term *taxonomy* can be used in several ways. In this study, the term *taxonomy* refers to a classification framework. Fundamentally, the goal is to provide a useful hierarchical classification system that organizes key concepts and their concrete values. It aims to capture the essence of a specific domain, thereby helping its users to understand, discuss, analyze, and observe complex concepts [\[104](#page-31-11), [105](#page-31-12)]. In contrast to a *typology*, which is a conceptual classification approach, a taxonomy is empirical, derived from real-world data and observation [\[106](#page-31-13)]. Following Nickerson et al. [[104\]](#page-31-11), a taxonomy consists of several distinct dimensions, each of which contains two or more characteristics that should be mutually exclusive and collectively exhaustive [[104,](#page-31-11) [105\]](#page-31-12).

Nickerson et al. [[104\]](#page-31-11) define five qualitative attributes of a useful taxonomy. A taxonomy should be *concise*, enabling researchers to recall the entire taxonomy with ease; *robust*, containing enough dimensions and characteristics to differentiate objects in the domain meaningfully; *comprehensive*, able to classify every instance in the domain and contain all relevant object dimensions; *extendible*, allowing new characteristics and dimensions to be added without difficulty when necessary; and *explanatory*, offering dimensions and characteristics that provide a useful and explainable abstraction [\[104](#page-31-11)]. These criteria served as subjective ending conditions for our taxonomy development process.

In this study, we rigorously follow the clear development process to ensure quality and reproducibility. The entire development process began with the definition of three foundational elements. First, the researcher should think of the overall *purpose* of the taxonomy: for what should it especially be used later and who are the main users. Next, a so-called *meta-characteristic* has to be set up, to provide a basis for all characteristics to be constructed later. A typical wording could be: 'Classify … based on …' and can encapsulate multiple facets. After establishing this anchor, the researcher selects objective *ending conditions* (e.g. no new dimensions emerge and every characteristic is instantiated) and subjective ending conditions (namely, the five quality criteria outlined above) [\[104](#page-31-11)].

After these elements had been defined, we followed Nickerson et al.'s iterative development cycle. The development cycle goes over, right in the beginning, to a fundamental decision where each iteration requires a choice between two development paths. In the *conceptual-to-empirical* path, the researcher first identifies candidate dimensions from theory, applies them to a sample of concrete objects of the domain, and prunes or augments the constructed dimensions. On the alternative *empirical-toconceptual* path, the researcher instead examines a sample of concrete objects, distills meaningful attributes and properties, and groups these into abstract dimensions that satisfy the basic quality criteria of sound taxonomy design. Each iteration ends with a review and evaluation of the resulting taxonomy against the predefined ending conditions. If these conditions are not satisfied, another iterative cycle begins, starting with the binary path choice [\[104](#page-31-11)].

Conceptually, this process mirrors the build-evaluate cycle in design science research [[107\]](#page-32-0). Each iteration constructs a provisional taxonomy or schema and immediately evaluates it against empirical reality and the predefined quality criteria. This allows usefulness, purpose-fit, and traceability to be integrated into the taxonomy development process. The approach also encourages detailed documentation of the entire procedure, which supports both reproducibility and extensibility. In our study, this disciplined iterative procedure, bounded by explicit rules, was used to yield a high-quality taxonomy with unique dimensions and mutually exclusive, collectively exhaustive characteristics [[104,](#page-31-11) [105\]](#page-31-12).

### **4.2 Communication Protocols Sample**

This section outlines how we selected the nine protocols that ground our taxonomy development and offers concise summaries of each.

First, it is important to define the general type and domain of the target protocols. Although we further clarify this when specifying the *meta-characteristic* in the taxonomy development process, it is already essential for the protocol selection. Specifically, we searched for protocols that were explicitly developed to connect an LLM agent with another system. Consequently, more generic agent communication implementations and concepts, such as the *FIPA Agent Communication Language* [[108\]](#page-32-1) which implements speech-act theory, or the *Contract Net Protocol* [\[109](#page-32-2)], an abstract tasksharing protocol for MAS, were excluded from our sample. Likewise, protocols not explicitly designed for LLM agents fall outside the scope of the taxonomy.

Next, we focus exclusively on protocols that are open source and have an implementation ready to be used. The implementation does not have to be production ready, a test or research prototype is sufficient. For instance, the Agora protocol [\[26](#page-25-3)] is not production ready, yet an implementation exists, whereas the LOKA protocol [[110\]](#page-32-3) is just a proposed concept with no implementation. Therefore, the latter has been excluded. Also, Firecrawl [\[111](#page-32-4)] and the uAgents protocol [\[112](#page-32-5)] are proprietary solutions and are not entirely open source and thus omitted. Emphasizing the open source requirement reflects the historical pattern that for major web standards it has been critical to be open source, in order to achieve widespread adoption and become a global standard [[113\]](#page-32-6).

All selected protocols maintain publicly accessible codebases on GitHub, enabling verification of active maintenance status. GitHub stars are employed as a quantitative proxy for community adoption and real-world traction. For that reason, protocols such as the *Agent Protocol* [[114\]](#page-32-7), whose last commit not just changing the README file occurred on Jun 11 2024 (accessed 7 Jul 2025), are treated as inactive and therefore excluded. Likewise, repositories such as the AITP protocol [\[115](#page-32-8)] are omitted, as they have accumulated only 20 *GitHub stars* (accessed 7 Jul 2025) since their initial release in February 2025.

Nine protocols met all selection criteria and are outlined in the following section. Table [1](#page-17-0) and [2](#page-18-0) provide a quick overview, and further characteristics are discussed during taxonomy development.

#### *Model Context Protocol (MCP)*

Developed by Anthropic, the *Model Context Protocol* (MCP) provides a standardized way to augment any LLM with tools and contextual information by enabling existing applications, APIs, and raw data sources, in short almost any IT component, to present their context and capabilities to LLMs in a standardized manner [[116,](#page-32-9) [117\]](#page-32-10).

At its core, MCP follows a straightforward client-server model. Host applications, such as Claude Desktop or IDE plug-ins, embed *MCP clients* that communicate with *MCP servers*, each of which exposes specific capabilities, including data retrieval, tool invocation, and prompt delivery for the LLM behind the MCP client [\[117](#page-32-10)].

#### *Agent to Agent (A2A)*

Google developed this protocol to address the rising number of siloed agent infrastructures. As agents are implemented and deployed across diverse frameworks and platforms, a standardized protocol is required to facilitate collaboration [\[118](#page-32-11)]. Its primary goal is to enable agent-to-agent connectivity, not to replace the already well-known MCP protocol [\[119](#page-32-12)].

Designed to be secure and extensible by default, it implements a variety of concepts across multiple levels of communication, supporting both immediate and extended tasks, including streaming updates, state synchronization, and artifact exchange (e.g. files and structured data) [\[120](#page-32-13), [121\]](#page-32-14).

#### *LangChain Agent Protocol (LAP)*

LangChain created a standardized API for deploying LLM agents in production. Specifically, they defined a RESTful API with a unified set of endpoints. The main endpoints are */runs* for executing agents, */threads* for managing multi-turn conversations, and */store* for long-term memory storage. Through these endpoints, any client can invoke, monitor, and persist agent workflows, irrespective of the agents' internal implementations [\[122](#page-32-15), [123](#page-33-0)].

#### *agents.json*

This simple protocol defines a JSON specification through which existing websites and APIs can be discovered and interpreted by LLM based agents. Built on top of the *OpenAPI* standard, agents.json offers a structured, LLM-friendly, and stateless way to define and consume API workflows, letting agents execute multi-step tasks reliably with minimal boilerplate and without extensive prompt engineering [\[124](#page-33-1)[–126](#page-33-2)].

#### *Agora*

Oxford researchers introduced the *Agora Protocol* [[102\]](#page-31-9) to enable decentralized collaboration among diverse LLM agents, without central servers and pre-defined communication schemas. Its design tackles the *Agent Communication Trilemma*, balancing versatility (handling diverse message types), efficiency (minimizing token and API cost), and portability (working across agent platforms), in a single decentralized framework [\[26](#page-25-3)]. For instance, it includes an on-the-fly protocol negotiation mechanism. Before exchanging actual data, agents share or even generate new communication schemas [[26,](#page-25-3) [127\]](#page-33-3).

### *Agent Network Protocol (ANP)*

Its vision is to become "the HTTP of the agentic web era" [\[128](#page-33-4)]. It is a peer-to-peer communication protocol designed to enable secure, decentralized collaboration among heterogeneous LLM-powered agents across the internet. The protocol is intentionally flexible and feature-rich out of the box, offering three layers: an *Identity Layer* for secure communication, covering authentication and end-to-end encryption; a *Meta Protocol Layer* that allows agents to negotiate communication styles dynamically, and an *Application Layer* that supports straightforward agent interaction through standardized descriptions and management [\[129](#page-33-5), [130](#page-33-6)].

#### *LMOS*

This protocol is part of the *Eclipse LMOS* ecosystem and enables agents and tools to easily publish, connect, and share their capabilities. As a special feature, it standardizes metadata and interaction patterns while remaining agnostic to the underlying transport layer, allowing seamless operation over HTTP, WebSocket, MQTT, and other protocols. Moreover, it emphasizes that it can readily support an internet-scale MAS with thousands of tools and agents, an *Internet of Agents* [[131,](#page-33-7) [132\]](#page-33-8).

#### *Agent Communication Protocol (ACP)*

The ACP is a RESTful open standard, created by BeeAI and IBM under Linux Foundation governance, that enables seamless, structured communication, discovery, and coordination among heterogeneous LLM agents [[133,](#page-33-9) [134\]](#page-33-10).

ACP defines consistent HTTP/JSON interfaces that enable agent discovery, execution, and multimodal message exchange. It also implements so-called *ACP Servers*, where agents can register themselves for discovery and can likewise discover other publicly available agents [\[134](#page-33-10)].

#### *agntcy*

Its mission extends beyond defining a protocol for agent-to-agent communication, it seeks to establish an open-source infrastructure for the *Internet of Agents* [\[135](#page-33-11)]. For communication, it specifies the *Agent Connect Protocol*, an API extending *OpenAPI* that enables agents to connect, share state, stream results, and handle authentication and authorization seamlessly across frameworks and runtime environments. The potential standard also provides essential infrastructure elements, including a centralized discovery service, a fixed agent manifest format, and many more [[136–](#page-33-12)[138\]](#page-33-13).

# **5 Results: Taxonomy Design**

We now proceed to construct the taxonomy by first defining its fundamental artifacts and summarizing the iterative development process. Rather than detailing each iteration, we then focus on examining both accepted and rejected dimensions in detail. Finally, we classify concrete protocols from our sample to illustrate the taxonomy's dimensions and their application.

### **5.1 Developing the Taxonomy**

### **5.1.1 Scope**

As discussed in Section [4,](#page-7-0) Nickerson et al.'s technique [[104\]](#page-31-11) begins with the definition of three foundational artifacts that define the scope of the taxonomy.

The *purpose* of the taxonomy is to classify and distinguish LLM agent communication protocols based on the type of communication they facilitate. The taxonomy focuses on protocols that connect an LLM agent to another system, such as another agent or a general information system. It operates primarily at the application level rather than the solution level, and therefore does not delve into concrete technical implementation details.

The *expected users* of the taxonomy are researchers and agent developers, as well as non-experts who simply want to access an agent through an API. Potential users may wish to obtain an overview of the forms of communication and guidance for protocol selection. In addition, a brief overview of how protocols differ overall, and where gaps and opportunities for further research and development exist, is of interest.

The *meta-characteristic* is defined as classifying the protocols according to the types of components involved and the characteristics of their communication.

### **5.1.2 Process and Quality**

In total, we conducted five iterations: the first three followed the empirical-toconceptual approach, and the final two followed the conceptual-to-empirical approach. Each of the first three iterations examined three of the nine collected protocols. The final two iterations complemented the analysis by consolidating accumulated knowledge and testing more abstract dimensions.

Ultimately, the iterative approach, guided by clear ending conditions and the taxonomy's purpose and meta-characteristic, made development straightforward and appeared to strengthen its robustness and comprehensibility.

With respect to the basic quality criteria of a qualitative taxonomy, we focused on the following key properties. The developed taxonomy is concise, as it contains a clear and manageable number of dimensions and characteristics. It is also robust, in the sense that we examined exactly nine protocols in detail and discovered no new valid dimensions in the final iteration. Furthermore, comprehensiveness and explanatory quality are ensured, as we demonstrate that all protocols can be classified according to the taxonomy in a straightforward manner. Finally, the taxonomy satisfies the foundational principle of mutual exclusivity and collective exhaustiveness, which we systematically enforced during dimension construction.

### <span id="page-12-0"></span>**5.2 Accepted Dimensions**

Throughout the iterative process, various dimensions were examined based on discovered common and distinctive characteristics. All considered dimensions are now described in detail, separated into accepted and rejected ones.

For each dimension, we present its corresponding values and assess whether it satisfies mutual exclusivity and exhaustiveness. For accepted dimensions, we additionally cite foundational research supporting the dimension and its values.

The finalized taxonomy comprises five dimensions, as shown in Figure [2](#page-13-0).

### **5.2.1 Counterparty**

We begin with the most self-explanatory dimension: *counterparty*. It identifies the type of entity with which the agent interacts via the protocol. Its values are: *agent*, where the protocol connects one LLM agent to another; *context*, where non-agent entities such as tools, services, APIs, or data sources are connected; and *hybrid*, where both are supported.

The dimension is mutually exclusive and exhaustive, as *context* captures any nonagent counterparty by design. Although further subcategories within *context* could be defined, the dimension is intentionally kept concise.

![](_page_13_Figure_0.jpeg)

<span id="page-13-0"></span>Fig. 2 Finalized Taxonomy: all dimensions and characteristics

This dimension aligns with Yang et al.'s [103] protocol taxonomy. Their object-orientation dimension distinguishes context-oriented from inter-agent protocols, corresponding to our context and agent values, respectively. We extend their scheme with a third value, hybrid, to accommodate protocols supporting both types.

#### 5.2.2 Payload

Next, the *payload* dimension classifies the kind of data a protocol exchanges. A protocol falls into one of three categories: *structured data and artifacts*, where only structured data or artifacts, including meta-information, are exchanged; *conversation focused*, where the payload is message-centric and text is always part of the exchange; or *hybrid*, where both are supported.

To clarify this dimension further, we compare it with the three basic data types: structured, semi-structured, and unstructured [139]. Rather than adopting that typology, our taxonomy classifies payloads according to the intended purpose a protocol is designed to support. A protocol is labeled *conversation focused* when text is always part of the payload and structured or semi-structured data appear only as optional extensions. Conversely, if the protocol can solely transmit structured data and artifacts drawn from any of Eberendu's [139] three data types, it is assigned to the *structured data and artifacts* category.

### **5.2.3 Interaction State**

This dimension captures the persistence of *interaction state* within a protocol, that is, whether the protocol implements a stateful unit of work between connected components. A protocol is either *stateless* or provides *session state* functionality.

Mutual exclusivity and exhaustiveness are guaranteed because the dimension is binary. A protocol that preserves context across messages is classified as *session state*, one that lacks such mechanisms is *stateless*.

Ling et al. [[140\]](#page-34-0) identify four kinds of managed state in communication networks: stateless, soft state, session state, and hard state. Their definition of stateless, no information retained at the nodes, matches our equivalently named value directly. Session state, defined as information persisting only for the duration of a user session, corresponds to what we term *session statefulness* [\[140](#page-34-0)]. The remaining categories, hard state, referring to long-term memory, and soft state, denoting temporarily cached information, fall outside the scope of this dimension. The dimension only concerns the duration of a single session and not what persists beyond it. This is further discussed in the context of persistent state in Section [5.3.](#page-15-0)

### **5.2.4 Discovery Mechanism**

In dynamic, large-scale distributed systems, individual nodes are typically unaware of the precise identities or locations of other nodes. Therefore, efficient discovery mechanisms are essential for scalable and flexible agent networks [[103,](#page-31-10) [141](#page-34-1)].

We identify two initial values: *static*, where the requesting agent must know the endpoint a priori, and *centralized*, where a registry maintains a list of accessible endpoints.

To ensure exhaustiveness, we drew on Ahmed and Boutaba's [\[141](#page-34-1)] survey of distributed search techniques in large-scale systems. They index two centralized content-sharing architectures, registry and index, which we combine into a single value, *centralized*, since we only are concerned with the discovery mechanism itself, not with how the registry is built. Their classification further motivates two additional values: *partially centralized*, where a limited set of supernodes assists with discovery, and *decentralized*, where no central authority exists and each peer maintains its own index, with discovery occurring via network broadcasting. Finally, we add a *hybrid* value for protocols that support multiple discovery mechanisms beyond static configuration.

Mutual exclusivity is guaranteed by arranging the values hierarchically. *Static* represents the baseline. If a protocol offers a *centralized*, *partially centralized*, or fully *decentralized* discovery mechanism, it is classified as such, even though static configuration remains universally available. A protocol supporting multiple non-static mechanisms is assigned to *hybrid*.

### **5.2.5 Schema Flexibility**

Next, we introduce the *schema flexibility* dimension, which captures the degree of flexibility a protocol offers in adjusting communication schemas, message formats, or dialogue structure. A protocol may allow only a *single* schema, one basic interaction pattern defined before runtime. Alternatively, it may support *multiple* static schemas, established a priori, from which the requester can choose at runtime. Finally, if the interacting components can negotiate new interaction styles at runtime, the protocol is classified as *evolving*.

In this dimension, the term *schema* follows the standard computer-science definition: a formal structure representing an engineered artifact [[142\]](#page-34-2). In our context, it refers in particular to the structure of the exchanged content. For instance, a tool invoked by an agent may require a fixed schema with a predefined set of typed variables [[117\]](#page-32-10), whereas an LLM-based agent might accept only a single text input, subject to constraints such as a maximum length [[123\]](#page-33-0).

It is important to note that this dimension does not characterize the structural nature of the payload, that role belongs to the *payload* dimension. Instead, it specifies whether exchanged information must conform to a fixed schema, whether agents may select from multiple predefined schemas, or whether the protocol supports runtime negotiation of schema structure.

### <span id="page-15-0"></span>**5.3 Rejected Dimensions**

Having examined all accepted dimensions, we now turn to three rejected dimensions and explain the rationale for their exclusion from the taxonomy.

### **5.3.1 Initiative Flow**

This dimension captures which party may initiate communication. Its proposed values are: *unidirectional*, where only the client can initiate; *context-bound bidirectional*, where either party may send messages within an active session but only one side can initiate it; and *open bidirectional*, where any party can initiate communication at any time.

The dimension is rejected on two grounds: most protocols fall under *context-bound bidirectional*, and any protocol could in principle be implemented symmetrically to support open bidirectional initiation. It therefore fails the test of mutual exclusivity and adds little analytical value.

### **5.3.2 Simplicity**

The examined protocols differ notably in their simplicity and intended lightweightness. Some, such as *A2A* and *LMOS*, incorporate a broad range of functionalities [\[121](#page-32-14), [143\]](#page-34-3), whereas others, such as *Agora*, *agents.json*, and *ACP*, target specifically defined use cases and explicitly prioritize a lightweight design [\[125](#page-33-15), [127](#page-33-3), [134](#page-33-10)].

Nevertheless, this dimension poses an immediate problem: there are no clear boundaries to ensure mutually exclusive values. The notion of simplicity is too vague to construct a meaningful qualitative dimension, and it is therefore rejected.

### **5.3.3 Persistent State**

This dimension classifies protocols by their ability to store data about prior interactions beyond a single or multi-turn exchange. Unlike the *interaction state* dimension (Section [5.2\)](#page-12-0), it concerns exclusively long-term statefulness. The stored content might include a textual summary of an earlier chat session or a negotiated sub-protocol preserved for future interactions. Although individual nodes could store such state at the implementation level, this dimension focuses on whether the protocol itself promotes any form of persistence.

Its proposed values are *none*, where no persistence features are offered; *metadata*, where the protocol supports storage of metadata such as a negotiated schema; *context*, where concrete interaction context such as session summaries is preserved; and *hybrid*, where both metadata and context are explicitly maintained.

In practice, most protocols already implement *metadata* persistence by exchanging component descriptions — such as the *Agent Discovery Card* in A2A [[144\]](#page-34-4) or the *Agent Detail* endpoint in ACP [[134\]](#page-33-10). Certain protocols additionally offer explicit features for context persistence: for example, LAP exposes a *store* endpoint that manages a persistent key–value repository accessible across interaction *threads* [\[123](#page-33-0)].

Nonetheless, the dimension is rejected. Nearly every protocol already exchanges minimal metadata for node identification, and the protocol itself does not determine what connected nodes ultimately store persistently. Moreover, providing persistent state mechanisms is not an essential objective of these protocols.

### **5.4 Classifying Concrete Protocols**

We now revisit the protocols used during taxonomy construction and assign them to the appropriate characteristics within the accepted dimensions. In the interest of conciseness, we only discuss the most salient classifications, those that best clarify and validate the taxonomy. A complete overview is provided in Table [1](#page-17-0) and Table [2,](#page-18-0) the former optimized for pattern detection and the latter for informative depth.

### **5.4.1 Counterparty**

Various protocols are explicitly designed to facilitate agent-to-agent collaboration and thus address the counterparty type *agent*. Agora [[26\]](#page-25-3), ANP [\[130](#page-33-6)], LAP [\[122](#page-32-15)], and agntcy [[136\]](#page-33-12) are classified as such. Moreover, A2A and ACP further emphasize that agents should use these protocols specifically for inter-agent communication, in contrast to protocols such as MCP, which are intended for connecting to context [\[119](#page-32-12), [146\]](#page-34-5). An *MCP server* is defined as the counterparty addressed by the agent, which can expose resources (e.g. documents or data), tools, and prompts [[117\]](#page-32-10).

### **5.4.2 Payload**

MCP and agents.json are the only protocols assigned to the *structured data and artifacts* payload type. MCP is designed for the exchange of structured requests and data responses between LLM-based agents and external tools, data sources, or services [\[117](#page-32-10)]. Further, agents.json does not handle actual data exchange, its sole purpose is to provide agents with a structured description of an existing API [[125\]](#page-33-15).

All remaining protocols are classified as *hybrid*. They typically define a core unit of exchange capable of encapsulating both simple strings and arbitrary elements. The exchange is thus not limited to conversational text, purely structured or contextual information can be transmitted as well.

<span id="page-17-0"></span>Table 1 Classification matrix of the nine analyzed protocols, for cross-protocol pattern comparison.

| Dimension                         | Characteristics                                                           | $\mathbf{MCP}_{[116,\ 117]}$ | $\begin{array}{c} {\bf A2A} \\ {[118-} \\ {121,\ 144]} \end{array}$ | $\mathbf{LAP}_{[122,\ 123]}$ | $\frac{\text{agents}}{\text{,json}}$ | $\begin{array}{c} \mathbf{Agora} \\ [26, 102, \\ 127] \end{array}$ | $\frac{\mathbf{ANP}}{[128-}]$ | $\begin{array}{c} {\bf LMOS} \\ [131,\ 132, \\ 143] \end{array}$ | $\mathbf{ACP} \\ [133, 134, \\ 146]$ | <b>agntcy</b> [135, 136, 138, 147] |
|-----------------------------------|---------------------------------------------------------------------------|------------------------------|---------------------------------------------------------------------|------------------------------|--------------------------------------|--------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------|--------------------------------------|------------------------------------|
| Agent Counterparty Context Hybrid | Agent<br>Context<br>Hybrid                                                | ×                            | ×                                                                   | ×                            | ×                                    | ×                                                                  | ×                             | ×                                                                | ×                                    | ×                                  |
| Interaction<br>State              | Stateless<br>Session state                                                | ×                            | ×                                                                   | ×                            | ×                                    | ×                                                                  | ×                             | ×                                                                | ×                                    | ×                                  |
| $Discovery \ Mechanism$           | Static<br>Centralized<br>Partially centralized<br>Decentralized<br>Hybrid | ×                            | ×                                                                   | *                            | ×                                    | ×                                                                  | ×                             | ×                                                                | ×                                    | ×                                  |
| Payload                           | Struct. data,<br>artifacts<br>Conversation focused<br>Hybrid              | ×                            | ×                                                                   | ×                            | ×                                    | ×                                                                  | ×                             | ×                                                                | ×                                    | ×                                  |
| Schema $Flexibility$              | Single<br>Multiple<br>Evolving                                            | ×                            | ×                                                                   | ×                            | ×                                    | ×                                                                  | ×                             | ×                                                                | ×                                    | ×                                  |

<span id="page-18-0"></span>**Table 2** Per-protocol classification and rationale for the nine analyzed protocols.

| Protocol                       | Counterparty | Interaction<br>State | m<br>Discovery<br>Mechanis | Payload                          | Flexibility<br>ma<br>Sche | Rationale                                                                                |
|--------------------------------|--------------|----------------------|----------------------------|----------------------------------|---------------------------|------------------------------------------------------------------------------------------|
| [116, 117]<br>MCP              | Context      | Stateless            | Static                     | artifacts<br>Structured<br>data, | Multiple                  | requires<br>tools;<br>Exposes<br>endpoints.<br>core.<br>Stateless<br>known               |
| [118–121, 144]<br>A2A          | Agent        | state<br>Session     | Centralized                | Hybrid                           | Multiple                  | Uses<br>streaming.<br>registry.<br>and<br>tasks<br>or<br>card<br>Inter-agent<br>JSON     |
| [122, 123]<br>LAP              | Agent        | state<br>Session     | Static                     | Hybrid                           | Single                    | for<br>endpoints<br>fixed<br>sessions.<br>with<br>API<br>multi-turn<br>REST              |
| agents.json<br>[124–126]       | Context      | Stateless            | Static                     | artifacts<br>Structured<br>data, | Single                    | M<br>LL<br>for<br>spec<br>JSON<br>OpenAPI<br>discovery.<br>Stateless<br>API              |
| [26, 102, 127]<br>Agora        | Agent        | state<br>Session     | Static                     | Hybrid                           | Evolving                  | runtime.<br>schemas<br>at<br>Plain-text<br>negotiated<br>Decentralized.<br>dynamically   |
| [128–130, 145]<br>ANP          | Agent        | state<br>Session     | Centralized                | Hybrid                           | Evolving                  | formats.<br>dynamically<br>and<br>structures<br>meta-layer<br>negotiates<br>Stateful     |
| [131, 132, 143]<br>MOS<br>L    | Hybrid       | state<br>Session     | Hybrid                     | Hybrid                           | Multiple                  | modes.<br>Standardizes<br>discovery<br>hybrid<br>Transport-agnostic.<br>with<br>metadata |
| [133, 134, 146]<br>ACP         | Agent        | state<br>Session     | Centralized                | Hybrid                           | Multiple                  | register<br>Agents<br>exchange.<br>servers.<br>centralized<br>Multi-modal<br>on          |
| [135, 136, 138, 147]<br>agntcy | Agent        | state<br>Session     | Centralized                | Hybrid                           | Multiple                  | state/streams<br>for<br>manifests.<br>extension<br>central<br>OpenAPI<br>via             |

### **5.4.3 Interaction State**

All protocols designed for agent-to-agent communication support multi-turn interactions through stateful units of work persisting across message exchanges. These units are named differently across protocols, like threads [\[123](#page-33-0), [147\]](#page-34-7), tasks [[118\]](#page-32-11), or in the case of Agora, realized through a simple *multiround* flag that enables the message structure to maintain *session state* [[127\]](#page-33-3).

In contrast, the core *MCP* protocol and *agents.json* define no explicit mechanism for session statefulness and are therefore *stateless* by design [\[117](#page-32-10), [125](#page-33-15), [126](#page-33-2)].

### **5.4.4 Discovery Mechanism**

First, MCP illustrates an important distinction: although agents can discover a server's capabilities at runtime, the *discovery mechanism* dimension classifies MCP as *static*, since the requesting agent must still know the server's base address a priori [[117\]](#page-32-10).

A2A, by contrast, supports three discovery strategies, all relying on a *JSON Agent Card* as the agent's self-description. An agent may host its card at a standardized path on its own domain, share it through private channels, or publish and query cards via a centralized registry. Although static configuration is a primary discovery mechanism, the presence of a registry-based option places the protocol within the *centralized* discovery class [\[121](#page-32-14)].

All other protocols fall into either the *static* or *centralized* category, with the exception of LMOS, which is classified as *hybrid* [[132\]](#page-33-8).

### **5.4.5 Schema Flexibility**

Most protocols either specify a *single* concrete interface [[123,](#page-33-0) [126\]](#page-33-2) or allow *multiple* distinct schemas to be defined in advance [\[117](#page-32-10), [136](#page-33-12), [143](#page-34-3)].

More interesting are the two protocols implementing *evolving* schema functionality. In Agora, a core concept is the *Protocol Document*, a plain-text description of everything an agent must understand to follow a given protocol. These documents are actively constructed and negotiated at runtime. Initial interactions occur entirely in natural language, but once a more efficient protocol has been established, subsequent exchanges can adopt a more structured format, possibly without any message parameters [[26\]](#page-25-3). ANP similarly supports dynamic negotiation of payload formats and interaction structures, enabling agents to select or generate a schema at runtime [[129\]](#page-33-5).

# **6 Discussion**

We have developed a qualitative taxonomy to efficiently classify and analyze communication protocols for LLM agents. This hierarchical classification system helps to structure and thereby clarify an increasingly complex, rapidly growing field. Future protocols can be intuitively classified and compared at an abstract level, enabling researchers to identify overarching trends and anticipate potential innovations.

### <span id="page-20-0"></span>**6.1 Insights and Implications**

Let us consider some important findings and implications that emerged during taxonomy development, backed by the classifications of all nine protocols (see Table [1](#page-17-0) and Table [2\)](#page-18-0).

If a protocol implements agent-to-agent communication (7 of 9), a *session state* functionality is always available. This is expected, because contemporary LLM based agents rely on multi-turn interaction, which in turn requires state persistence. Moreover, none of the agent-to-agent protocols restrict themselves to *conversation-focused* payloads (7 of 9). Instead, all are consistently *hybrid*; while they can transmit textual messages, they also support purely structured payloads whenever appropriate. Furthermore, a clear trend towards schema flexibility emerges from the data. The majority of protocols permit multiple schema definitions (7 of 9), and two (2 of 9) additionally allow schemas to evolve during runtime. Schema negotiation is thereby regarded as a central component of agent-to-agent protocols, enabling LLM-based agents to fully leverage their capabilities. With respect to discovery mechanisms, only the LMOS protocol [\[132](#page-33-8)] truly incorporates a decentralized, peer-to-peer approach. Most protocols instead rely on either a centralized registry (4 of 9) or static configuration (4 of 9). Should the Internet of Agents emerge as a dominant paradigm, decentralized approaches should be explored more and may prove increasingly important.

Looking forward, a central question is whether the field will converge on a single, monolithic standard or adopt a more modular architecture. Initially, the functional overlap between emerging protocols might suggest a short-term convergence toward a unified standard capable of supporting both agent-to-agent and agent-to-context interactions. Notably, A2A and agntcy present themselves as extensions of MCP [[119,](#page-32-12) [137](#page-33-16)], though the primary organization behind MCP, Anthropic, has not officially endorsed either of them. While modifying an agent-to-agent protocol like A2A to incorporate MCP functionality would be relatively straightforward, drawing on historical precedents in computer networking, we argue that a monolithic "winner-takes-all" standard is unlikely to prevail. Instead, mirroring the layered OSI model, illustrated in Figure [3,](#page-21-0) our analysis suggests that the future of multi-agent system communication will evolve toward a federated, layered protocol stack. Under this architecture, the Internet of Agents will likely utilize lightweight specifications, such as agents.json, for static capability discovery; defer to highly structured context-protocols, e.g., MCP, for secure tool execution; and reserve session-aware, schema-evolving protocols, e.g., ANP or Agora, for complex, multi-turn deliberations.

A notable gap across all investigated protocols is the widespread absence of privacy safeguards, compliance checks, and policy enforcement mechanisms. This shortcoming will become more severe as agents are increasingly deployed in safety-critical domains such as healthcare or human resources, where mechanisms for protecting personal and security-sensitive data are essential [[11\]](#page-24-1).

![](_page_21_Figure_0.jpeg)

<span id="page-21-0"></span>**Fig. 3** A candidate layered protocol stack for the Internet of Agents. Layers are ordered by the communication trilemma: lower layers favor efficiency and portability (rigid schemas, stateless, structured payloads), upper layers favor versatility (session-aware, schema-evolving). Each protocol is placed based on its primary role in Table [2](#page-18-0); chip color denotes the counterparty type, and dashed chips indicate protocols that additionally provide the identity/transport substrate. The layering is a proposed instantiation of the federated-stack argument in Section [6.1](#page-20-0), not an observed fact.

### **6.2 Evaluating the Communication Trilemma**

Applying Marro's [[26\]](#page-25-3) Agent Communication Trilemma, introduced in Section [3,](#page-6-0) to our taxonomy reveals stark architectural trade-offs. The trilemma dictates that a protocol cannot simultaneously maximize versatility, efficiency, and portability.

This trade-off is highly visible at the extremes of our *Schema Flexibility* and *Payload* dimensions. Protocols designed primarily for context-interaction, such as MCP, maximize portability and efficiency by enforcing rigid schemas, stateless interactions, and strictly structured data payloads. This strictness eliminates token-heavy negotiation, making them ideal for predictable, high-throughput agent-to-tool invocations. Conversely, protocols with *evolving* schemas, such as Agora and ANP, maximize versatility to facilitate dynamic, open-ended multi-agent debates. However, this adaptability introduces significant token overhead and latency during schema negotiation, severely reducing efficiency.

Interestingly, the taxonomy reveals that the majority of surveyed protocols, such as A2A, LMOS, and ACP, navigate the center of this trilemma. By adopting *hybrid* payload structures, *session state* persistence, and *multiple* pre-established schemas, they provide enough versatility to support complex interactions without incurring the extreme efficiency penalties of runtime protocol negotiation. Ultimately, mapping our taxonomy against the trilemma reinforces the conclusion from Section [6.1:](#page-20-0) the impossibility of a single, omnipotent protocol strongly supports the necessity of a layered protocol stack for the future Internet of Agents.

## **6.3 Limitations and Future Work**

Future research could enrich our taxonomy with further dimensions that capture the domain in greater detail. Promising extensions include more technical protocol dimensions, authentication and security mechanisms, and the means by which protocols embed policies and norms. Also, classifying new protocols as they emerge would both strengthen the taxonomy's validity and allow systematic tracking and analysis of ongoing developments within the domain. Moreover, the taxonomy provides a practical basis for evaluating which protocols are most suitable for specific use cases and application domains.

# **7 Conclusion**

In this paper, we have developed a comprehensive technical taxonomy of communication protocols for LLM-based agents. Motivated by the growing fragmentation of agent frameworks and protocol proposals, we examined how emerging protocols structure communication between LLM agents, other agents, tools, services, APIs, and external information systems. To develop the taxonomy, we followed a structured approach, defining the taxonomy's purpose, meta-characteristic, ending conditions, and iterative development process before applying the resulting framework to nine existing protocol implementations. By following a well-structured taxonomy development approach, we ensured methodological quality, producing a framework which allows efficient exploration and analysis of the diverse landscape of LLM agent communication protocols.

In addition, we identified several clear patterns by applying the taxonomy to nine concrete protocols. Most agent-to-agent protocols support multi-turn statefulness and the capacity to exchange both textual messages and structured data. Furthermore, schema negotiation is considered essential for efficient flexibility. Most importantly, our analysis suggests a possible short-term convergence pressure toward protocols that unify agent-to-agent and agent-to-context communication. In the long term, rather than converging on a single monolithic standard, the field will likely evolve toward a federated, layered protocol stack, similar to the OSI model in traditional computer networking. Such an architecture would seamlessly integrate specialized protocols, ranging from lightweight capability discovery specifications to highly structured tool execution and schema-evolving deliberation mechanisms, in order to support the full spectrum of agent communication scenarios efficiently. However, whether this leads to a single dominant standard or to a small set of interoperable protocol families remains an open question.

As LLMs continue to advance, LLM agents will grow more intelligent and capable of tackling real-world challenges. Likewise, LLM-powered multi-agent systems hold the potential to surpass the scalability constraints of single models. Consequently, the means by which agents communicate is a critical design element in building decentralized, flexible, and efficient agent networks, laying the groundwork for a future in which agents may operate partially or even fully autonomously in handling complex tasks.

# **References**

- <span id="page-23-0"></span>[1] Han, S., Zhang, Q., Yao, Y., Jin, W., Xu, Z.: LLM multi-agent systems: Challenges and open problems. arXiv preprint arXiv:2402.03578 (2024)
- <span id="page-23-7"></span>[2] Masterman, T., Besen, S., Sawtell, M., Chao, A.: The landscape of emerging AI agent architectures for reasoning, planning, and tool calling: A survey. arXiv preprint arXiv:2404.11584 (2024)
- <span id="page-23-1"></span>[3] Xi, Z., Chen, W., Guo, X., He, W., Ding, Y., Hong, B., Zhang, M., Wang, J., Jin, S., Zhou, E., *et al.*: The rise and potential of large language model based agents: A survey. Science China Information Sciences **68**(2), 121101 (2025)
- <span id="page-23-2"></span>[4] Yu, J., Wang, X., Tu, S., Cao, S., Zhang-Li, D., Lv, X., Peng, H., Yao, Z., Zhang, X., Li, H., *et al.*: Kola: Carefully benchmarking world knowledge of large language models. In: International Conference on Learning Representations, vol. 2024, pp. 44594–44637 (2024)
- <span id="page-23-3"></span>[5] Achiam, J., Adler, S., Agarwal, S., Ahmad, L., Akkaya, I., Aleman, F.L., Almeida, D., Altenschmidt, J., Altman, S., Anadkat, S., et al.: GPT-4 technical report. arXiv preprint arXiv:2303.08774 (2023)
- <span id="page-23-6"></span>[6] Bang, Y., Cahyawijaya, S., Lee, N., Dai, W., Su, D., Wilie, B., Lovenia, H., Ji, Z., Yu, T., Chung, W., *et al.*: A multitask, multilingual, multimodal evaluation of ChatGPT on reasoning, hallucination, and interactivity. In: Proceedings of the 13th International Joint Conference on Natural Language Processing and the 3rd Conference of the Asia-pacific Chapter of the Association for Computational Linguistics (volume 1: Long Papers), pp. 675–718 (2023)
- <span id="page-23-4"></span>[7] Valmeekam, K., Marquez, M., Olmo, A., Sreedharan, S., Kambhampati, S.: Planbench: An extensible benchmark for evaluating large language models on planning and reasoning about change. Advances in Neural Information Processing Systems **36**, 38975–38987 (2023)
- <span id="page-23-5"></span>[8] Liu, X., Yu, H., Zhang, H., Xu, Y., Lei, X., Lai, H., Gu, Y., Ding, H., Men, K., Yang, K., *et al.*: Agentbench: Evaluating LLMs as agents. In: International Conference on Learning Representations, vol. 2024, pp. 52989–53046 (2024)

- [9] Sun, H., Zhuang, Y., Kong, L., Dai, B., Zhang, C.: Adaplanner: Adaptive planning from feedback with language models. Advances in neural information processing systems **36**, 58202–58245 (2023)
- <span id="page-24-0"></span>[10] Hsiao, V., Fine-Morris, M., Roberts, M., Smith, L.N., Hiatt, L.M.: A critical assessment of LLMs for solving multi-step problems: Preliminary results. In: AAAI 2025 Workshop LM4Plan (2025)
- <span id="page-24-1"></span>[11] Guo, T., Chen, X., Wang, Y., Chang, R., Pei, S., Chawla, N.V., Wiest, O., Zhang, X.: Large language model based multi-agents: A survey of progress and challenges. arXiv preprint arXiv:2402.01680 (2024)
- <span id="page-24-2"></span>[12] Talebirad, Y., Nadiri, A.: Multi-agent collaboration: Harnessing the power of intelligent LLM agents. arXiv preprint arXiv:2306.03314 (2023)
- <span id="page-24-3"></span>[13] Malone, T.W., Bernstein, M.: Handbook of Collective Intelligence. MIT press, Cambridge, MA (2015)
- <span id="page-24-4"></span>[14] Chen, W., Su, Y., Zuo, J., Yang, C., Yuan, C., Chan, C.-M., Yu, H., Lu, Y., Hung, Y.-H., Qian, C., *et al.*: Agentverse: Facilitating multi-agent collaboration and exploring emergent behaviors. In: International Conference on Learning Representations, vol. 2024, pp. 20094–20136 (2024)
- <span id="page-24-5"></span>[15] Hong, S., Zhuge, M., Chen, J., Zheng, X., Cheng, Y., Wang, J., Zhang, C., Yau, S., Lin, Z., Zhou, L., *et al.*: MetaGPT: Meta programming for a multi-agent collaborative framework. In: International Conference on Learning Representations, vol. 2024, pp. 23247–23275 (2024)
- <span id="page-24-6"></span>[16] Yan, B., Zhou, Z., Zhang, L., Zhang, L., Zhou, Z., Miao, D., Li, Z., Li, C., Zhang, X.: Beyond self-talk: A communication-centric survey of LLM-based multi-agent systems. arXiv preprint arXiv:2502.14321 (2025)
- <span id="page-24-7"></span>[17] Microsoft: AutoGen. GitHub. Accessed 21 Jul 2025 (2023)
- <span id="page-24-8"></span>[18] Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., *et al.*: Autogen: Enabling next-gen LLM applications via multi-agent conversations. In: First Conference on Language Modeling (2024)
- <span id="page-24-9"></span>[19] CrewAI: CrewAI. GitHub. Accessed 21 Jul 2025 (2023)
- <span id="page-24-10"></span>[20] CAMEL: CAMEL. GitHub. Accessed 21 Jul 2025 (2023)
- <span id="page-24-11"></span>[21] Li, G., Hammoud, H.A.A.K., Itani, H., Khizbullin, D., Ghanem, B.: CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society (2023). <https://arxiv.org/abs/2303.17760>
- <span id="page-24-12"></span>[22] LangChain: LangGraph. GitHub. Accessed 21 Jul 2025 (2024)

- <span id="page-25-0"></span>[23] Cemri, M., Pan, M.Z., Yang, S., Agrawal, L.A., Chopra, B., Tiwari, R., Keutzer, K., Parameswaran, A., Klein, D., Ramchandran, K., et al.: Why do multi-agent LLM systems fail? arXiv preprint arXiv:2503.13657 (2025)
- <span id="page-25-1"></span>[24] Kong, D., Lin, S., Xu, Z., Wang, Z., Li, M., Li, Y., Zhang, Y., Peng, H., Chen, X., Sha, Z., et al.: A survey of LLM-driven AI agent communication: Protocols, security risks, and defense countermeasures. arXiv preprint arXiv:2506.19676 (2025)
- <span id="page-25-2"></span>[25] Ehtesham, A., Singh, A., Gupta, G.K., Kumar, S.: A survey of agent interoperability protocols: Model Context Protocol (MCP), Agent Communication Protocol (ACP), Agent-to-Agent protocol (A2A), and Agent Network Protocol (ANP). arXiv preprint arXiv:2505.02279 (2025)
- <span id="page-25-3"></span>[26] Marro, S., La Malfa, E., Wright, J., Li, G., Shadbolt, N., Wooldridge, M., Torr, P.: A scalable communication protocol for networks of large language models. arXiv preprint arXiv:2410.11905 (2024)
- <span id="page-25-4"></span>[27] Li, X., Liu, M., Yuen, C.: LLM agent communication protocol (LACP) requires urgent standardization: A telecom-inspired protocol is necessary. arXiv preprint arXiv:2510.13821 (2025)
- <span id="page-25-5"></span>[28] Russell, S.: Learning agents for uncertain environments. In: Proceedings of the Eleventh Annual Conference on Computational Learning Theory, pp. 101–103 (1998)
- <span id="page-25-6"></span>[29] Wooldridge, M., Jennings, N.R.: Intelligent agents: Theory and practice. The knowledge engineering review **10**(2), 115–152 (1995)
- <span id="page-25-7"></span>[30] Mele, A.R.: Autonomous Agents: From Self-control to Autonomy. Oxford University Press, New York, NY (1995)
- <span id="page-25-8"></span>[31] Jennings, N.R., Sycara, K., Wooldridge, M.: A roadmap of agent research and development. Autonomous agents and multi-agent systems **1**(1), 7–38 (1998)
- <span id="page-25-9"></span>[32] Nwana, H.S.: Software agents: An overview. The knowledge engineering review **11**(3), 205–244 (1996)
- <span id="page-25-10"></span>[33] Liu, A., Feng, B., Xue, B., Wang, B., Wu, B., Lu, C., Zhao, C., Deng, C., Zhang, C., Ruan, C., et al.: Deepseek-v3 technical report. arXiv preprint arXiv:2412.19437 (2024)
- <span id="page-25-11"></span>[34] Anthropic: System Card: Claude Opus 4 & Claude Sonnet 4. [https://www.](https://www.anthropic.com/claude-4-system-card) [anthropic.com/claude-4-system-card](https://www.anthropic.com/claude-4-system-card). Accessed 21 Jul 2025 (2025)
- <span id="page-25-12"></span>[35] Chen, X., Lin, M., Schärli, N., Zhou, D.: Teaching large language models to selfdebug. In: International Conference on Learning Representations, vol. 2024, pp.

- 8746–8825 (2024)
- <span id="page-26-0"></span>[36] Madaan, A., Tandon, N., Gupta, P., Hallinan, S., Gao, L., Wiegreffe, S., Alon, U., Dziri, N., Prabhumoye, S., Yang, Y., *et al.*: Self-refine: Iterative refinement with self-feedback. Advances in neural information processing systems **36**, 46534–46594 (2023)
- <span id="page-26-1"></span>[37] Kojima, T., Gu, S.S., Reid, M., Matsuo, Y., Iwasawa, Y.: Large language models are zero-shot reasoners. Advances in neural information processing systems **35**, 22199–22213 (2022)
- <span id="page-26-2"></span>[38] Li, S., Padilla, S., Bras, P.L., Dong, J., Chantler, M.: A review of LLM-assisted ideation. arXiv preprint arXiv:2503.00946 (2025)
- <span id="page-26-3"></span>[39] Zhao, W.X., Zhou, K., Li, J., Tang, T., Wang, X., Hou, Y., Min, Y., Zhang, B., Zhang, J., Dong, Z., et al.: A survey of large language models. arXiv preprint arXiv:2303.18223 (2023)
- <span id="page-26-4"></span>[40] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J.D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., *et al.*: Language models are few-shot learners. Advances in neural information processing systems **33**, 1877–1901 (2020)
- [41] Jin, Z., Lu, W.: Tab-cot: Zero-shot tabular chain of thought. arXiv preprint arXiv:2305.17812 (2023)
- <span id="page-26-5"></span>[42] Ruan, J., Chen, Y., Zhang, B., Xu, Z., Bao, T., Mao, H., Li, Z., Zeng, X., Zhao, R., *et al.*: TPTU: Task planning and tool usage of large language model-based ai agents. In: NeurIPS 2023 Foundation Models for Decision Making Workshop (2023)
- <span id="page-26-6"></span>[43] Besta, M., Blach, N., Kubicek, A., Gerstenberger, R., Podstawski, M., Gianinazzi, L., Gajda, J., Lehmann, T., Niewiadomski, H., Nyczyk, P., *et al.*: Graph of thoughts: Solving elaborate problems with large language models. In: Proceedings of the AAAI Conference on Artificial Intelligence, vol. 38, pp. 17682–17690 (2024)
- <span id="page-26-9"></span>[44] Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., Cao, Y.: ReAct: Synergizing reasoning and acting in language models. In: International Conference on Learning Representations (ICLR) (2023)
- <span id="page-26-7"></span>[45] Yao, S., Yu, D., Zhao, J., Shafran, I., Griffiths, T., Cao, Y., Narasimhan, K.: Tree of thoughts: Deliberate problem solving with large language models. Advances in neural information processing systems **36**, 11809–11822 (2023)
- <span id="page-26-8"></span>[46] Zhang, C., Zhang, C., Li, C., Qiao, Y., Zheng, S., Dam, S.K., Zhang, M., Kim, J.U., Kim, S.T., Choi, J., et al.: One small step for generative AI, one giant

- leap for AGI: A complete survey on ChatGPT in AIGC era. arXiv preprint arXiv:2304.06488 (2023)
- <span id="page-27-0"></span>[47] Wang, L., Ma, C., Feng, X., Zhang, Z., Yang, H., Zhang, J., Chen, Z., Tang, J., Chen, X., Lin, Y., *et al.*: A survey on large language model based autonomous agents. Frontiers of Computer Science **18**(6), 186345 (2024)
- <span id="page-27-1"></span>[48] Castrillo, V.d.L., Gidey, H.K., Lenz, A., Knoll, A.: Fundamentals of building autonomous LLM agents. arXiv preprint arXiv:2510.09244 (2025)
- <span id="page-27-2"></span>[49] Evans, J.S.B., Over, D.E., Manktelow, K.I.: Reasoning, decision making and rationality. Cognition **49**(1-2), 165–187 (1993)
- <span id="page-27-3"></span>[50] Huang, X., Liu, W., Chen, X., Wang, X., Wang, H., Lian, D., Wang, Y., Tang, R., Chen, E.: Understanding the planning of LLM agents: A survey. arXiv preprint arXiv:2402.02716 (2024)
- <span id="page-27-4"></span>[51] Wei, J., Wang, X., Schuurmans, D., Bosma, M., Xia, F., Chi, E., Le, Q.V., Zhou, D., *et al.*: Chain-of-thought prompting elicits reasoning in large language models. Advances in neural information processing systems **35**, 24824–24837 (2022)
- <span id="page-27-5"></span>[52] Shinn, N., Cassano, F., Gopinath, A., Narasimhan, K., Yao, S.: Reflexion: Language agents with verbal reinforcement learning. Advances in Neural Information Processing Systems **36**, 8634–8652 (2023)
- <span id="page-27-6"></span>[53] Gidey, H.K., Marmsoler, D., Ascher, D.: Modeling adaptive self-healing systems. arXiv preprint arXiv:2304.12773 (2023)
- <span id="page-27-7"></span>[54] Petroni, F., Rocktäschel, T., Lewis, P., Bakhtin, A., Wu, Y., Miller, A.H., Riedel, S.: Language models as knowledge bases? arXiv preprint arXiv:1909.01066 (2019)
- <span id="page-27-8"></span>[55] Zhang, Z., Bo, X., Ma, C., Li, R., Chen, X., Dai, Q., Zhu, J., Dong, Z., Wen, J.- R.: A survey on the memory mechanism of large language model based agents. arXiv preprint arXiv:2404.13501 (2024)
- <span id="page-27-9"></span>[56] Hatalis, K., Christou, D., Myers, J., Jones, S., Lambert, K., Amos-Binks, A., Dannenhauer, Z., Dannenhauer, D.: Memory matters: The need to improve longterm memory in LLM-agents. In: Proceedings of the AAAI Symposium Series, vol. 2, pp. 277–280 (2023)
- [57] Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., *et al.*: Retrieval-augmented generation for knowledge-intensive NLP tasks. Advances in neural information processing systems **33**, 9459–9474 (2020)

- [58] Zeng, R., Fang, J., Liu, S., Meng, Z.: On the structural memory of LLM agents. arXiv preprint arXiv:2412.15266 (2024)
- <span id="page-28-0"></span>[59] Gidey, H.K., Kesseler, M., Stangl, P., Hillmann, P., Karcher, A.: Documentbased knowledge discovery with microservices architecture. In: International Conference on Intelligent Systems and Pattern Recognition, pp. 146–161 (2022). Springer International Publishing Cham
- <span id="page-28-1"></span>[60] Shen, Z.: LLM with tools: A survey. arXiv preprint arXiv:2409.18807 (2024)
- <span id="page-28-2"></span>[61] Gidey, H.K., Huber, N., Lenz, A., Knoll, A.: Affordance representation and recognition for autonomous agents. arXiv preprint arXiv:2510.24459 (2025)
- <span id="page-28-3"></span>[62] Guo, J., Li, J., Li, D., Tiong, A.M.H., Li, B., Tao, D., Hoi, S.C.: From images to textual prompts: Zero-shot visual question with frozen large language models. arXiv preprint arXiv:2212.10846 (2022)
- [63] Peng, Z., Wang, W., Dong, L., Hao, Y., Huang, S., Ma, S., Wei, F.: Kosmos-2: Grounding multimodal large language models to the world. arXiv preprint arXiv:2306.14824 (2023)
- [64] Pi, R., Yao, L., Gao, J., Zhang, J., Zhang, T.: PerceptionGPT: Effectively fusing visual perception into LLM. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 27124–27133 (2024)
- <span id="page-28-4"></span>[65] Gidey, H.K., Lenz, A., Knoll, A.: A pattern language for resilient visual agents. arXiv preprint arXiv:2604.28001 (2026)
- <span id="page-28-5"></span>[66] Qin, Y., Liang, S., Ye, Y., Zhu, K., Yan, L., Lu, Y., Lin, Y., Cong, X., Tang, X., Qian, B., Zhao, S., Hong, L., Tian, R., Xie, R., Zhou, J., Gerstein, M., Li, D., Liu, Z., Sun, M.: ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs (2023). <https://arxiv.org/abs/2307.16789>
- <span id="page-28-6"></span>[67] Macedo, J., Gidey, H.K., Rebuli, K.B., Machado, P.: Evolving user interfaces: A neuroevolution approach for natural human-machine interaction. In: International Conference on Computational Intelligence in Music, Sound, Art and Design (Part of EvoStar), pp. 246–264 (2024). Springer Nature Switzerland Cham
- <span id="page-28-7"></span>[68] Bouzenia, I., Pradel, M.: You name it, I run it: An LLM agent to execute tests of arbitrary projects. Proceedings of the ACM on Software Engineering **2**(ISSTA), 1054–1076 (2025)
- [69] Cao, C., Wang, F., Lindley, L., Wang, Z.: Managing Linux servers with LLMbased AI agents: An empirical evaluation with GPT4. Machine Learning with Applications **17**, 100570 (2024)

- [70] Qian, C., Liu, W., Liu, H., Chen, N., Dang, Y., Li, J., Yang, C., Chen, W., Su, Y., Cong, X., et al.: Chatdev: Communicative agents for software development. arXiv preprint arXiv:2307.07924 (2023)
- <span id="page-29-0"></span>[71] Sager, P.J., Meyer, B., Yan, P., Wartburg-Kottler, R., Etaiwi, L., Enayati, A., Nobel, G., Abdulkadir, A., Grewe, B.F., Stadelmann, T.: AI agents for computer use: A review of instruction-based computer control, GUI automation, and operator assistants. arXiv preprint arXiv:2501.16150 (2025)
- <span id="page-29-1"></span>[72] Ghafarollahi, A., Buehler, M.J.: SciAgents: Automating scientific discovery through multi-agent intelligent graph reasoning (2024). [https://arxiv.org/abs/](https://arxiv.org/abs/2409.05556) [2409.05556](https://arxiv.org/abs/2409.05556)
- [73] Lála, J., O'Donoghue, O., Shtedritski, A., Cox, S., Rodriques, S.G., White, A.D.: PaperQA: Retrieval-Augmented Generative Agent for Scientific Research (2023). <https://arxiv.org/abs/2312.07559>
- [74] Katz, U., Levy, M., Goldberg, Y.: Knowledge Navigator: LLM-guided Browsing Framework for Exploratory Search in Scientific Literature (2024). [https://arxiv.](https://arxiv.org/abs/2408.15836) [org/abs/2408.15836](https://arxiv.org/abs/2408.15836)
- <span id="page-29-2"></span>[75] Gidey, H.K., Hillmann, P., Karcher, A., Knoll, A.: User-like bots for cognitive automation: A survey. In: International Conference on Machine Learning, Optimization, and Data Science, pp. 388–402 (2023). Springer Nature Switzerland Cham
- <span id="page-29-3"></span>[76] Azamfirei, R., Kudchadkar, S.R., Fackler, J.: Large language models and the perils of their hallucinations. Critical Care **27**(1), 120 (2023)
- <span id="page-29-4"></span>[77] Hsieh, C.-P., Sun, S., Kriman, S., Acharya, S., Rekesh, D., Jia, F., Zhang, Y., Ginsburg, B.: RULER: What's the real context size of your long-context language models? arXiv preprint arXiv:2404.06654 (2024)
- [78] Liu, N.F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., Liang, P.: Lost in the middle: How language models use long contexts. Transactions of the association for computational linguistics **12**, 157–173 (2024)
- <span id="page-29-5"></span>[79] Shi, F., Chen, X., Misra, K., Scales, N., Dohan, D., Chi, E.H., Schärli, N., Zhou, D.: Large language models can be easily distracted by irrelevant context. In: International Conference on Machine Learning, pp. 31210–31227 (2023). PMLR
- <span id="page-29-6"></span>[80] Kim, G., Baldi, P., McAleer, S.: Language models can solve computer tasks. Advances in Neural Information Processing Systems **36**, 39648–39677 (2023)
- <span id="page-29-7"></span>[81] Xie, J., Zhang, K., Chen, J., Yuan, S., Zhang, K., Zhang, Y., Li, L., Xiao, Y.: Revealing the barriers of language agents in planning. In: Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association

- for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers), pp. 1872–1888 (2025)
- <span id="page-30-0"></span>[82] Chatterjee, A., Renduchintala, H.K., Bhatia, S., Chakraborty, T.: POSIX: A prompt sensitivity index for large language models. In: Findings of the Association for Computational Linguistics: EMNLP 2024, pp. 14550–14565 (2024)
- <span id="page-30-1"></span>[83] Tran, K.-T., Dao, D., Nguyen, M.-D., Pham, Q.-V., O'Sullivan, B., Nguyen, H.D.: Multi-agent collaboration mechanisms: A survey of LLMs. arXiv preprint arXiv:2501.06322 (2025)
- <span id="page-30-2"></span>[84] Li, J., Zhang, Q., Yu, Y., Fu, Q., Ye, D.: More agents is all you need. arXiv preprint arXiv:2402.05120 (2024)
- <span id="page-30-3"></span>[85] Khot, T., Trivedi, H., Finlayson, M., Fu, Y., Richardson, K., Clark, P., Sabharwal, A.: Decomposed prompting: A modular approach for solving complex tasks. arXiv preprint arXiv:2210.02406 (2022)
- <span id="page-30-4"></span>[86] Tillmann, A.: Literature review of multi-agent debate for problem-solving. arXiv preprint arXiv:2506.00066 (2025)
- <span id="page-30-10"></span>[87] Guo, X., Huang, K., Liu, J., Fan, W., Vélez, N., Wu, Q., Wang, H., Griffiths, T.L., Wang, M.: Embodied LLM agents learn to cooperate in organized teams. IEEE Transactions on Computational Social Systems (2026)
- <span id="page-30-5"></span>[88] Fu, Y., Peng, H., Khot, T., Lapata, M.: Improving language model negotiation with self-play and in-context learning from AI feedback. arXiv preprint arXiv:2305.10142 (2023)
- <span id="page-30-6"></span>[89] Duéñez-Guzmán, E.A., Sadedin, S., Wang, J.X., McKee, K.R., Leibo, J.Z.: A social path to human-like artificial intelligence. Nature machine intelligence **5**(11), 1181–1188 (2023)
- <span id="page-30-7"></span>[90] Li, X., Wang, S., Zeng, S., Wu, Y., Yang, Y.: A survey on LLM-based multiagent systems: Workflow, infrastructure, and challenges. Vicinagearth **1**(1), 9 (2024)
- <span id="page-30-8"></span>[91] Gidey, H.K., Hillmann, P., Karcher, A., Knoll, A.: Towards cognitive bots: Architectural research challenges. In: International Conference on Artificial General Intelligence, pp. 105–114 (2023). Springer Nature Switzerland Cham
- <span id="page-30-9"></span>[92] Gidey, H.K., Collins, A., Marmsoler, D.: Modeling and verifying dynamic architectures with factum studio. In: International Conference on Formal Aspects of Component Software, pp. 243–251 (2019). Springer International Publishing Cham

- <span id="page-31-0"></span>[93] Kaesberg, L.B., Becker, J., Wahle, J.P., Ruas, T., Gipp, B.: Voting or consensus? Decision-making in multi-agent debate. arXiv preprint arXiv:2502.19130 (2025)
- <span id="page-31-1"></span>[94] Wang, Y., Guo, S., Pan, Y., Su, Z., Chen, F., Luan, T.H., Li, P., Kang, J., Niyato, D.: Internet of agents: Fundamentals, applications, and challenges. arXiv preprint arXiv:2505.07176 (2025)
- <span id="page-31-2"></span>[95] Pouzin, L., Zimmermann, H.: A tutorial on protocols. Proceedings of the IEEE **66**(11), 1346–1370 (2005)
- <span id="page-31-3"></span>[96] Tanenbaum, A.S., Wetherall, D.J.: Computer Networks, 5th edn. Prentice Hall, Upper Saddle River, NJ (2011)
- <span id="page-31-4"></span>[97] Cerf, V., Kahn, R.: A protocol for packet network intercommunication. IEEE Transactions on communications **22**(5), 637–648 (1974)
- <span id="page-31-5"></span>[98] Nath, P.B., Uddin, M.M.: TCP-IP model in data communication and networking. American Journal of Engineering Research **4**(10), 102–107 (2015)
- <span id="page-31-6"></span>[99] Finin, T., Fritzson, R., McKay, D.P., McEntire, R., *et al.*: KQML-a language and protocol for knowledge and information exchange. In: 13th Int. Distributed Artificial Intelligence Workshop, pp. 93–103 (1994)
- <span id="page-31-7"></span>[100] Labrou, Y., Finin, T., Peng, Y.: Agent communication languages: The current landscape. IEEE Intelligent Systems and Their Applications **14**(2), 45–52 (1999)
- <span id="page-31-8"></span>[101] Du, C., Wang, C., Chao, Y., Xie, X., Cui, Y.: AI agent communication from internet architecture perspective: Challenges and opportunities. arXiv preprint arXiv:2509.02317 (2025)
- <span id="page-31-9"></span>[102] Agora Protocol: Agora Protocol Python. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-31-10"></span>[103] Yang, Y., Chai, H., Song, Y., Qi, S., Wen, M., Li, N., Liao, J., Hu, H., Lin, J., Chang, G., et al.: A survey of AI agent protocols. arXiv preprint arXiv:2504.16736 (2025)
- <span id="page-31-11"></span>[104] Nickerson, R.C., Varshney, U., Muntermann, J.: A method for taxonomy development and its application in information systems. European Journal of Information Systems **22**(3), 336–359 (2013)
- <span id="page-31-12"></span>[105] Oberländer, A.M., Lösser, B., Rau, D.: Taxonomy research in information systems: A systematic assessment. In: Proceedings of the 27th European Conference on Information Systems (ECIS), Stockholm and Uppsala, Sweden, pp. 1–17 (2019). [https://aisel.aisnet.org/ecis2019\\_rp/144](https://aisel.aisnet.org/ecis2019_rp/144)
- <span id="page-31-13"></span>[106] Bailey, K.D.: Typologies and Taxonomies: An Introduction to Classification Techniques vol. 12. Sage, Thousand Oaks, CA (1994)

- <span id="page-32-0"></span>[107] Hevner, A.R., March, S.T., Park, J., Ram, S.: Design science in information systems research. MIS quarterly, 75–105 (2004)
- <span id="page-32-1"></span>[108] O'Brien, P.D., Nicol, R.C.: FIPA—towards a standard for software agents. BT Technology Journal **16**, 51–59 (1998)
- <span id="page-32-2"></span>[109] Smith, R.G.: The contract net protocol: High-level communication and control in a distributed problem solver. IEEE Transactions on computers **29**(12), 1104– 1113 (1980)
- <span id="page-32-3"></span>[110] Ranjan, R., Gupta, S., Singh, S.N.: Loka protocol: A decentralized framework for trustworthy and ethical AI agent ecosystems. arXiv preprint arXiv:2504.10915 (2025)
- <span id="page-32-4"></span>[111] Firecrawl: Open Source vs Cloud. [https://docs.firecrawl.dev/contributing/](https://docs.firecrawl.dev/contributing/open-source-or-cloud) [open-source-or-cloud](https://docs.firecrawl.dev/contributing/open-source-or-cloud). Accessed 7 Jul 2025 (2024)
- <span id="page-32-5"></span>[112] Fetch.ai: uAgents - Exchange protocol. <https://uagents.fetch.ai/docs>. Accessed 7 Jul 2025 (2025)
- <span id="page-32-6"></span>[113] Gamalielsson, J., Lundell, B., Brax, C., Persson, T., Mattsson, A., Gustavsson, T., Feist, J.: Open source software reference implementations for standards issued by different standards setting organisations: Availability, perceptions and practices. Journal of Standardisation **3**(2) (2024)
- <span id="page-32-7"></span>[114] Garg, D.: Agent Protocol. GitHub. Accessed 7 Jul 2025 (2023)
- <span id="page-32-8"></span>[115] NEAR AI: AITP: Agent Interaction and Transaction Protocol. GitHub. Accessed 7 Jul 2025 (2025)
- <span id="page-32-9"></span>[116] Anthropic: Model Context Protocol. GitHub. Accessed 11 Jul 2025 (2024)
- <span id="page-32-10"></span>[117] Anthropic: MCP Core Architecture. [https://modelcontextprotocol.io/docs/](https://modelcontextprotocol.io/docs/concepts/architecture) [concepts/architecture](https://modelcontextprotocol.io/docs/concepts/architecture). Accessed 11 Jul 2025 (2024)
- <span id="page-32-11"></span>[118] Google: Key Concepts in A2A. [https://a2aproject.github.io/A2A/latest/](https://a2aproject.github.io/A2A/latest/topics/key-concepts/) [topics/key-concepts/](https://a2aproject.github.io/A2A/latest/topics/key-concepts/). Accessed 11 Jul 2025 (2025)
- <span id="page-32-12"></span>[119] Google: A2A and MCP: Complementary Protocols for Agentic Systems. [https:](https://a2aproject.github.io/A2A/latest/topics/a2a-and-mcp/) [//a2aproject.github.io/A2A/latest/topics/a2a-and-mcp/](https://a2aproject.github.io/A2A/latest/topics/a2a-and-mcp/). Accessed 11 Jul 2025 (2025)
- <span id="page-32-13"></span>[120] Google: A2A. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-32-14"></span>[121] Google: Agent2Agent (A2A) Protocol Specification. [https://a2aproject.github.](https://a2aproject.github.io/A2A/latest/specification/) [io/A2A/latest/specification/](https://a2aproject.github.io/A2A/latest/specification/). Accessed 11 Jul 2025 (2025)
- <span id="page-32-15"></span>[122] LangChain: Agent Protocol. GitHub. Accessed 11 Jul 2025 (2025)

- <span id="page-33-0"></span>[123] LangChain: Agent Protocol - OpenAPI Documentation. [https://langchain-ai.](https://langchain-ai.github.io/agent-protocol/api.html) [github.io/agent-protocol/api.html](https://langchain-ai.github.io/agent-protocol/api.html). Accessed 11 Jul 2025 (2025)
- <span id="page-33-1"></span>[124] Wildcard: agents.json. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-33-15"></span>[125] Wildcard: Introducing agents.json. [https://docs.wild-card.ai/agentsjson/](https://docs.wild-card.ai/agentsjson/introduction) [introduction](https://docs.wild-card.ai/agentsjson/introduction). Accessed 11 Jul 2025 (2025)
- <span id="page-33-2"></span>[126] Wildcard: agents.json Schema Reference. [https://docs.wild-card.ai/agentsjson/](https://docs.wild-card.ai/agentsjson/schema) [schema.](https://docs.wild-card.ai/agentsjson/schema) Accessed 11 Jul 2025 (2025)
- <span id="page-33-3"></span>[127] Agora Protocol: Agora Standard Specification. [https://agoraprotocol.org/docs/](https://agoraprotocol.org/docs/protocol/specification) [protocol/specification](https://agoraprotocol.org/docs/protocol/specification). Accessed 11 Jul 2025 (2025)
- <span id="page-33-4"></span>[128] ANP: AgentConnect. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-33-5"></span>[129] Chang, G.: ANP Communication Meta-Protocol Specification. [https://](https://agent-network-protocol.com/specs/communication.html) [agent-network-protocol.com/specs/communication.html](https://agent-network-protocol.com/specs/communication.html). Accessed 11 Jul 2025 (2024)
- <span id="page-33-6"></span>[130] Chang, G., Lin, E., Yuan, C., Cai, R., Chen, B., Xie, X., Zhang, Y.: Agent Network Protocol Technical White Paper (2025). [https://arxiv.org/abs/2508.](https://arxiv.org/abs/2508.00007) [00007](https://arxiv.org/abs/2508.00007)
- <span id="page-33-7"></span>[131] Eclipse Foundation: Eclipse LMOS. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-33-8"></span>[132] Eclipse Foundation: LMOS Discovery. [https://eclipse.dev/lmos/docs/lmos\\_](https://eclipse.dev/lmos/docs/lmos_protocol/discovery/) [protocol/discovery/](https://eclipse.dev/lmos/docs/lmos_protocol/discovery/). Accessed 11 Jul 2025 (2025)
- <span id="page-33-9"></span>[133] ACP: Agent Communication Protocol (ACP). GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-33-10"></span>[134] ACP: Core Concepts. <https://agentcommunicationprotocol.dev/core-concepts>. Accessed 11 Jul 2025 (2025)
- <span id="page-33-11"></span>[135] AGNTCY: AGNTCY. GitHub. Accessed 11 Jul 2025 (2025)
- <span id="page-33-12"></span>[136] AGNTCY: Agent Connect Protocol. [https://spec.acp.agntcy.org/#description/](https://spec.acp.agntcy.org/#description/introduction) [introduction](https://spec.acp.agntcy.org/#description/introduction). Accessed 11 Jul 2025 (2025)
- <span id="page-33-16"></span>[137] AGNTCY: AGNTCY Origins. [https://docs.agntcy.org.](https://docs.agntcy.org) Accessed 11 Jul 2025 (2025)
- <span id="page-33-13"></span>[138] AGNTCY: Agent Discovery Service. <https://docs.agntcy.org/dir/overview/>. Accessed 11 Jul 2025 (2025)
- <span id="page-33-14"></span>[139] Eberendu, A.C., *et al.*: Unstructured data: An overview of the data of Big Data. International Journal of Computer Trends and Technology **38**(1), 46–50 (2016)

- <span id="page-34-0"></span>[140] Ling, B.C., Kiciman, E., Fox, A.: Session state: Beyond soft state. In: NSDI, vol. 4, pp. 22–22 (2004)
- <span id="page-34-1"></span>[141] Ahmed, R., Boutaba, R.: A survey of distributed search techniques in large scale distributed systems. IEEE Communications Surveys & Tutorials **13**(2), 150–167 (2010)
- <span id="page-34-2"></span>[142] Bernstein, P.A., Madhavan, J., Rahm, E.: Generic schema matching, ten years later. Proceedings of the VLDB Endowment **4**(11), 695–701 (2011)
- <span id="page-34-3"></span>[143] Eclipse Foundation: LMOS Introduction. [https://eclipse.dev/lmos/docs/lmos\\_](https://eclipse.dev/lmos/docs/lmos_protocol/introduction/) [protocol/introduction/](https://eclipse.dev/lmos/docs/lmos_protocol/introduction/). Accessed 11 Jul 2025 (2025)
- <span id="page-34-4"></span>[144] Google: Agent Discovery in A2A. [https://a2aproject.github.io/A2A/latest/](https://a2aproject.github.io/A2A/latest/topics/agent-discovery/) [topics/agent-discovery/.](https://a2aproject.github.io/A2A/latest/topics/agent-discovery/) Accessed 11 Jul 2025 (2025)
- <span id="page-34-6"></span>[145] Chang, G.: ANP Agent Discovery Protocol Specification. [https://agentnetworkprotocol.com/](https://agentnetworkprotocol.com/en/specs/08-anp-agent-discovery-protocol-specification/#anp-agent-discovery-protocol-specification-draft) [en/specs/08-anp-agent-discovery-protocol-specification/](https://agentnetworkprotocol.com/en/specs/08-anp-agent-discovery-protocol-specification/#anp-agent-discovery-protocol-specification-draft) [#anp-agent-discovery-protocol-specification-draft](https://agentnetworkprotocol.com/en/specs/08-anp-agent-discovery-protocol-specification/#anp-agent-discovery-protocol-specification-draft). Accessed 11 Jul 2025 (2024)
- <span id="page-34-5"></span>[146] ACP: MCP and A2A - How does ACP compare to other AI protocols. [https:](https://agentcommunicationprotocol.dev/about/mcp-and-a2a) [//agentcommunicationprotocol.dev/about/mcp-and-a2a.](https://agentcommunicationprotocol.dev/about/mcp-and-a2a) Accessed 11 Jul 2025 (2025)
- <span id="page-34-7"></span>[147] AGNTCY: Threads Specification. [https://spec.acp.agntcy.org/#tag/threads.](https://spec.acp.agntcy.org/#tag/threads) Accessed 11 Jul 2025 (2025)