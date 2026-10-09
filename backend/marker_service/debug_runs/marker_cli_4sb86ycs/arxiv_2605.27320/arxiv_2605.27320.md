# Modeling Agentic Technical Debt and Stochastic Tax: A Standalone Framework for Measurement, Simulation, and Dashboarding

Muhammad Zia Hydari School of Business, University of Pittsburgh Pittsburgh, Pennsylvania, USA hydari@alum.mit.edu

> Raja Iqbal Ejento.ai Seattle, Washington, USA raja@ejento.ai

Narayan Ramasubbu School of Business, University of Pittsburgh Pittsburgh, Pennsylvania, USA narayanr@pitt.edu

#### **Abstract**

Agentic AI systems combine probabilistic reasoning with delegated action through tools, context, memory, orchestration, and external workflow integration. This note develops a formal and managerially usable model that distinguishes *Agentic Technical Debt* from *Stochastic Tax*. *Agentic Technical Debt* is a stock of accumulated design and governance liability. *Stochastic Tax* is a recurring flow of operating burden that arises when stochastic agents are used in business workflows. The two constructs are related, but they are not the same: debt can amplify the tax, while the tax can remain positive even when debt is minimized. The note starts from a compact dashboard expression, expands it into a fuller structural model, defines all variables and parameters, shows how each cost category can be estimated from operational data, and illustrates the framework with an accounts-payable simulation and companion spreadsheet.

# **1 Purpose and Core Intuition**

The purpose of this note is to make two constructs precise enough to support measurement, simulation, and dashboarding. Both constructs concern the management of agentic AI systems, but they answer different questions.

#### Core distinction

*Agentic Technical Debt* is the accumulated liability created by expedient agent design and governance choices. *Stochastic Tax* is the recurring cost of keeping stochastic agent behavior within acceptable operating bounds, and its rate can move with debt, usage, surface area, autonomy, and model variability.

The distinction is most naturally expressed as a stock-flow distinction. *Agentic Technical Debt* is a stock because it accumulates over time through choices about prompts, tools, context, memory, routing, observability, and platform coupling. It can be paid down through refactoring, standardization, versioning, documentation, and governance. *Stochastic Tax* is a flow because it is paid repeatedly as the organization operates an agentic workflow. It appears in evaluation, monitoring, retries, escalation, latency, token and context processing, guardrails, security checks, and revalidation.

This distinction also clarifies why the term *Stochastic Tax* is useful. Interest on technical debt disappears when the debt is paid off. *Stochastic Tax* need not disappear when *Agentic Technical Debt* is minimized. Even a carefully governed agentic workflow can impose a positive operating burden because probabilistic systems can vary across runs, act through tools, depend on context, and encounter new edge cases as adoption expands. Debt can raise this burden, but it does not create the burden from nothing.

# **2 Conceptual Background**

The technical-debt metaphor originated in software engineering to describe how shortcuts can accelerate near-term delivery while increasing future maintenance cost [\(Cunningham,](#page-23-0) [1992\)](#page-23-0). Later empirical work showed that technical debt can be measured through concrete liabilities and linked to remediation cost, operational disruption, and system longevity [\(Ramasubbu](#page-23-1) [et al.,](#page-23-1) [2015\)](#page-23-1). Machine-learning systems expanded the debt metaphor beyond code to include data dependencies, hidden feedback loops, pipeline entanglement, and undeclared consumers [\(Sculley et al.,](#page-23-2) [2015\)](#page-23-2). Foundation models and agentic systems extend the problem again because probabilistic outputs are no longer confined to prediction. They can guide tool calls, retrieve or write memory, trigger external actions, and revise plans across multi-step workflows [\(Bommasani et al.,](#page-23-3) [2021;](#page-23-3) [Yao et al.,](#page-23-4) [2022\)](#page-23-4).

Traditional software systems are often deterministic: a defect may be expensive to fix, but it is usually reproducible. Predictive ML systems introduce probabilistic outputs, but the model is often embedded as a single inference component in a larger deterministic workflow. Agentic AI systems operate as control loops. They plan, call tools, condition on retrieved context, write or read memory, and act in external systems. This creates a distinctive managerial problem: the organization must govern probabilistic action, not only code quality

# **3 Definitions and Boundary Conditions**

Let *w* ∈ W denote a workflow, such as accounts payable, customer support routing, or sales operations. Let *t* denote a time period, such as a week, month, or release cycle.

Many of the same architectural surfaces appear in both definitions. Context handling, orchestration, memory, and tool routing can accumulate debt when teams make expedient choices; the same surfaces can also generate *Stochastic Tax* because probabilistic execution varies across runs even when the design is disciplined.

### **3.1 Agentic Technical Debt**

**Definition.** *Agentic Technical Debt* is the accumulated liability created when an agentic system is assembled, modified, or governed through expedient choices that make future change, validation, explanation, or control more costly than necessary.

The unit of liability is not only code or data. In agentic systems, debt also resides in instructions, context, state, tool contracts, action authority, and the governance routines that make future changes safe.

This liability can appear in some of the following places, including:

- **Context and prompt debt:** long, inconsistent, or poorly versioned prompts; unstructured context; unclear retrieval rules; conflicting instructions.
- **Tool and schema debt:** unversioned tools, fragile tool-call schemas, undocumented connectors, inconsistent error handling, weak contracts between agents and tools.
- **Memory and state debt:** unclear write permissions, stale memory, weak state management, unclear retention policies, inconsistent memory retrieval.
- **Orchestration and routing debt:** brittle sequential chains, ad hoc routing logic, poorly specified escalation paths, untested workflow branches.
- **Governance and observability debt:** missing traces, weak golden sets, incomplete tests, insufficient monitoring, unclear ownership of prompt and tool changes.
- **Platform-coupling debt:** tight dependence on a particular model, vendor, safety policy, or connector interface without abstraction, versioning, or revalidation discipline.

### **3.2 Stochastic Tax**

**Definition.** *Stochastic Tax* is the recurring operating burden of keeping stochastic agentic behavior within acceptable bounds in a business workflow. The tax arises from the inherently probabilistic nature of agentic AI systems, not only from engineering shortcomings, and it can persist even if all technical debt were paid down. The relevant managerial question is

therefore not whether the tax can be made to vanish, but which portion is an unavoidable cost of operating stochastic action and which portion is amplified by remediable debt.

This tax is distinct from the general operating burden of enterprise systems. ERP systems impose review delays, approval queues, and override workflows, but those costs are largely deterministic and predictable. *Stochastic Tax* is specifically the variable burden introduced by non-determinism, namely the cost that exists because the same semantic input need not produce the same execution path.

*Stochastic Tax* typically appears in the following recurring cost categories:

- **Evaluation and test maintenance:** building and refreshing eval suites, running model or judge calls, and reviewing outputs as the workflow changes.
- **Monitoring and observability:** collecting traces, storing logs, maintaining dashboards, reviewing alerts, and investigating anomalous runs.
- **Retry and repair:** paying for additional model calls, tool calls, self-repair loops, and manual repair when the first execution path fails or becomes ambiguous.
- **Escalation and exception handling:** routing uncertain or risky cases to humans and absorbing the labor cost of review, approval, or correction.
- **Revalidation after change:** retesting the workflow after model, prompt, tool, context, policy, or vendor changes.
- **Latency and delay:** absorbing the cost of slower or more variable execution, especially when multi-step workflows create tail latency.
- **Token, compute, and context processing:** paying for longer prompts, larger retrieved context, repeated calls, model usage, compute, and tool-execution charges.
- **Security and guardrail maintenance:** updating input and output controls, reviewing security flags, maintaining guardrails, and testing new attack patterns.

#### Illustrative boundary example

Suppose three users ask a general-purpose agentic assistant the same semantic question and need the same semantic answer. The model is strong and the surrounding scaffolding is mature. All three users may receive semantically similar outputs, but the number of intermediate reasoning steps, tool calls, retries, and tokens consumed can differ across the three runs. That cost variability is *Stochastic Tax*: it arises from probabilistic execution, not from an error made by any of the users. By contrast, if one user has built a project with conflicting system prompts, undocumented connectors, and unclear context rules, that user is also carrying *Agentic Technical Debt*. The debt can be paid down by cleaning up prompts, versioning connectors, and documenting context policies. The tax can be reduced, but under current agentic architectures it cannot be assumed to disappear.

A smaller version of the same distinction appears when an agent searches the web before consulting a document that the user already uploaded. If the search fails because the article is paywalled and the agent then falls back to the uploaded document, the extra routing step is part of the stochastic operating burden. If the project repeatedly misroutes because its instructions and context hierarchy are poorly specified, that is also evidence of agentic debt.

The term *Stochastic Tax* carries two meanings, both of which the model preserves. First, it is a tax incurred *because* the system is stochastic: probabilistic outputs, fallible tool calls, and a continuously expanding surface of edge cases create an operating burden that cannot be designed away under current agentic architectures. The model represents this reading through a baseline floor: even when agentic debt is set to zero, some evaluation, monitoring, guardrails, and exception handling remain. Second, the tax is *itself* stochastic: its rate moves period to period as debt accumulates or is paid down, as adoption expands, as surface area grows, and as underlying event rates fluctuate. A team cannot quote next quarter's stochastic tax the way it quotes a lease payment. The formal model below makes both readings operational: the baseline floor captures the first, while the amplifiers and event-rate dependence capture the second.

Table [1](#page-5-0) summarizes the distinction.

**Table 1:** Comparing Agentic Technical Debt and Stochastic Tax

<span id="page-5-0"></span>

| Dimension             | Agentic Technical Debt                                                                             | Stochastic Tax                                                                                                      |  |  |  |
|-----------------------|----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|--|--|--|
| Basic idea            | Accumulated liability from expedient design and governance choices                                 | Recurring operating burden of stochastic agent behavior                                                             |  |  |  |
| Economic metaphor     | Debt principal                                                                                     | Tax or operating charge paid with use                                                                               |  |  |  |
| Time pattern          | Builds up over time                                                                                | Paid per period, run, release, workflow, or transaction                                                             |  |  |  |
| Where it appears      | Prompts, context, tools, schemas, memory, routing, orchestration, observability, platform coupling | Evaluation, monitoring, retries, escalation, revalidation, latency, token/context cost, security and guardrail work |  |  |  |
| Main question         | What choices are making future change harder?                                                      | What recurring burden do we pay to operate behavior safely?                                                         |  |  |  |
| Managerial response   | Refactor, standardize, version, document, redesign, govern                                         | Measure, budget, set thresholds, automate checks, triage high-tax workflows                                         |  |  |  |
| Can it be eliminated? | It can be reduced, sometimes materially                                                            | It can be reduced, but need not vanish under current agentic architectures                                          |  |  |  |
| Relationship          | Can amplify Stochastic Tax                                                                         | May reveal symptoms of Agentic<br>Technical Debt, but is not reducible<br>to Agentic Technical Debt                 |  |  |  |

# 4 Modeling Agentic Technical Debt as a Stock

A useful model of *Agentic Technical Debt* must do two things. First, it must identify the components of debt that managers can inspect and remediate. Second, it must represent debt as persistent. A brittle prompt, undocumented connector, or unclear memory rule does not vanish merely because the next transaction succeeds.

# 4.1 Debt Components

For workflow w in period t, define the debt-component vector

<span id="page-5-1"></span>
$$\mathbf{d}_{w,t} = \left( d_{w,t}^{ctx}, d_{w,t}^{tool}, d_{w,t}^{mem}, d_{w,t}^{orch}, d_{w,t}^{obs}, d_{w,t}^{plat} \right), \qquad d_{w,t}^{i} \in [0, 1]. \tag{1}$$

Each component  $d_{w,t}^i$  is normalized between 0 and 1. A value near 0 means the component is well controlled. A value near 1 means the component creates severe future-change, validation, or control liability. Table 2 gives observable indicators for each component.

**Table 2:** Operationalizing *Agentic Technical Debt* Components

<span id="page-6-0"></span>

| Component                               | Observable indicators                                                                                              | Why it belongs in the debt model                                                                     |  |  |  |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------|--|--|--|
| Context and prompt<br>debt              | Prompt length growth, conflict<br>ing instructions,<br>unversioned<br>prompt<br>edits,<br>context-source<br>sprawl | Prompt and context complexity make<br>future changes hard to reason about and<br>test.               |  |  |  |
| Tool<br>and<br>schema<br>debt           | Unversioned tools, malformed<br>tool calls, missing parameter<br>checks, undocumented connec<br>tors               | Agents act through tools, so weak con<br>tracts increase future validation and in<br>tegration cost. |  |  |  |
| Memory<br>and<br>state<br>debt          | Stale<br>memory,<br>unclear<br>write<br>rules, missing retention policies,<br>state inconsistencies                | Persistent state lets past errors influence<br>future behavior.                                      |  |  |  |
| Orchestration<br>and<br>routing debt    | Long serialized chains, fragile<br>routing logic, excessive hand<br>offs, unclear fallback paths                   | Multi-step workflows can compound er<br>rors and raise redesign cost.                                |  |  |  |
| Observability<br>and<br>governance debt | Missing<br>traces,<br>weak<br>golden<br>sets, unclear ownership, no re<br>lease gates                              | Lack<br>of<br>observability<br>makes<br>future<br>changes expensive and risky.                       |  |  |  |
| Platform-coupling<br>debt               | Tight dependence on a model,<br>vendor API, safety policy, or<br>connector without abstraction                     | External changes can force internal reval<br>idation or redesign.                                    |  |  |  |

Equation [1](#page-5-1) is useful in practice because it gives the team a debt register. Each component can be scored from operational evidence, for example on a 0 to 5 scale and then normalized to [0*,* 1]. The score need not be perfect to be useful. Its value comes from being repeated consistently over time and connected to remediation actions.

# **4.2 Debt Accumulation Dynamics**

The next step is to model how a debt component changes over time. A component should decline when remediation is effective. It should rise from two sources: local change activity that the team accrues directly, and external shocks that the team absorbs from the platform. The local channel accrues debt only when there is something to change, the changes are made expediently, and governance is not strong enough to absorb them safely; we capture this with three multiplicative factors: change pressure *X*, shortcut intensity *Q*, and inverse governance (1 − *G*). The platform channel accrues debt only when the platform itself changes and the workflow is exposed to that change; we capture this with two multiplicative factors: platform volatility *V plat* and exposure *E*.

For component *i*, define

<span id="page-6-1"></span>
$$d_{w,t+1}^{i} = \Pi_{[0,1]} \left[ (1 - \phi_{i} R_{w,t}^{i}) d_{w,t}^{i} + \alpha_{i} X_{w,t}^{i} Q_{w,t}^{i} (1 - G_{w,t}^{i}) + \zeta_{i} V_{w,t}^{plat} E_{w,t}^{i} \right]. \tag{2}$$

The terms in Equation [2](#page-6-1) have the following meaning:

- $d_{w,t}^i$  is the current debt score for component i in workflow w.
- $R_{w,t}^i \in [0,1]$  is normalized remediation effort for component i, such as refactoring prompts, versioning tools, improving tests, or clarifying ownership.
- $\phi_i > 0$  converts remediation effort into debt reduction.
- $X_{w,t}^i \in [0,1]$  is change pressure on component i: the rate at which changes are demanded (prompt edits, new tools, new context sources, policy changes, or workflow changes) relative to the team's clean-change capacity during period t. High pressure forces edits to be made faster than they can be cleanly absorbed.
- $Q_{w,t}^i \in [0,1]$  is shortcut intensity, meaning the fraction of changes made through local patches rather than systematic redesign.
- $G_{w,t}^i \in [0,1]$  is governance maturity. Stronger versioning, tests, schemas, ownership, and observability reduce new debt creation.
- $V_{w,t}^{plat} \geq 0$  is platform volatility, such as changes in model behavior, vendor interfaces, safety policies, or connector APIs.
- $E_{w,t}^i \in [0,1]$  is exposure to platform volatility. A decoupled workflow has lower exposure than a workflow tightly coupled to one model or vendor.
- $\alpha_i$  and  $\zeta_i$  translate local change pressure and platform volatility into debt growth.
- $\Pi_{[0,1]}[\cdot]$  truncates the value to the unit interval.

Analytically, this equation captures persistence, accumulation, remediation, and platform-driven shocks. Practically, it tells a manager what to measure: change pressure, shortcut intensity, governance maturity, remediation effort, and exposure to external change. It also identifies levers. The team can reduce debt by increasing R, reducing Q, increasing G, or lowering platform exposure through abstraction and versioning.

The full equation is useful for diagnosing where debt comes from. For numerical exploration, however, managers often need a lighter recurrence that exposes only the amount of debt accumulated and the amount remediated during a period. The simulation and companion spreadsheet therefore use the following simplified per-period net-change rule:

<span id="page-7-0"></span>
$$D_{w,t+1} = \Pi_{[0,1]} \left[ D_{w,t} + \Delta_{w,t}^{acc} - \Delta_{w,t}^{rem} \right]. \tag{3}$$

Here  $\Delta^{acc}_{w,t}$  is newly accumulated workflow-level debt during the period and  $\Delta^{rem}_{w,t}$  is workflow-level remediation. This is the form used in the companion spreadsheet's Time\_Series sheet. It is a simplification of Equation 2, not a competing model.

#### 4.3 Aggregating Debt into a Workflow Index

Managers need a workflow-level score in addition to component-level scores. A simple weighted average is often sufficient, but agentic components can interact. For example, prompt brittleness is more damaging when tool schemas are weak, and ungoverned memory is more damaging when routing is unclear. To capture this coupling, define

<span id="page-8-0"></span>
$$D_{w,t} = \Pi_{[0,1]} \left[ \sum_{i \in \mathcal{I}} \omega_i d_{w,t}^i + \sum_{i < j} \omega_{ij} d_{w,t}^i d_{w,t}^j \right]. \tag{4}$$

Here  $D_{w,t} \in [0,1]$  is the normalized Agentic Technical Debt index,  $\mathcal{I}$  is the set of debt components,  $\omega_i \geq 0$  are component weights, and  $\omega_{ij} \geq 0$  are coupling weights. A dashboard can report  $100D_{w,t}$  as a 0 to 100 debt score. The interaction term is optional for a first implementation. A team with limited data can set all  $\omega_{ij} = 0$  and later add interactions once it observes that specific component pairs raise remediation cost or operating burden.

#### 4.4 Debt Principal in Dollars

The index in Equation 4 is useful for tracking, but a financial view may require an estimated debt principal. If the team can estimate remediation costs, define

$$P_{w,t}^{ATD} = \sum_{i \in \mathcal{I}} \bar{c}_i^{rem} d_{w,t}^i + \sum_{i < j} \bar{c}_{ij}^{coord} d_{w,t}^i d_{w,t}^j + \bar{c}_{w,t}^{retest}.$$
 (5)

 $P_{w,t}^{ATD}$  is the estimated debt principal in dollars.  $\bar{c}_i^{rem}$  is the estimated cost to fully remediate component i,  $\bar{c}_{ij}^{coord}$  is the coordination premium created by coupled liabilities, and  $\bar{c}_{w,t}^{retest}$  is the testing and revalidation cost required after remediation. This model is useful in practice because it translates an abstract score into a planning estimate: how much effort would it take to pay down the liability?

# 5 Modeling Stochastic Tax as a Flow

A useful model of *Stochastic Tax* must connect a dashboard-ready expression to observable operating drivers. This section starts with a compact average-cost expression, then expands each cost category into structural drivers that can be estimated, simulated, and implemented in a spreadsheet.

### 5.1 From Dashboard Expression to Structural Expansion

For workflow w in period t, let  $N_{w,t}$  denote completed transactions. Average stochastic tax per transaction can be expressed as recurring cost categories divided by completed transactions. In the expanded eight-category form used here,

<span id="page-8-1"></span>
$$\overline{ST}_{w,t} = \frac{1}{N_{w,t}} \left( C_{w,t}^{eval} + C_{w,t}^{monitor} + C_{w,t}^{retry} + C_{w,t}^{escalate} + C_{w,t}^{revalidate} + C_{w,t}^{latency} + C_{w,t}^{lotency} + C_{w,t}^{token} + C_{w,t}^{security} \right).$$

$$(6)$$

In Equation [6,](#page-8-1) *C k w,t* is the total cost in category *k* during period *t*. This expression is appropriate for a managerial dashboard because it reports a unit cost: the recurring burden per completed transaction. To populate the dashboard, however, each *C k w,t* must be connected to observable drivers. The structural model below provides that expansion.

<span id="page-9-0"></span>Table [3](#page-9-0) lists the eight cost categories used in the model.

**Table 3:** Cost Categories for a *Stochastic Tax* Dashboard

| Cost category<br>k                                                                                                                           | Measurement approach                                                                        | Typical data source                                                               |  |  |
|----------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|--|--|
| Evaluation<br>and<br>test<br>maintenance                                                                                                     | Model calls, judge calls, test in<br>frastructure, expert review time                       | Evaluation logs, test records, reviewer<br>hours                                  |  |  |
| Monitoring and observ<br>ability                                                                                                             | Dashboard cost, trace storage,<br>alert review, routine operations<br>time                  | Observability tools, log storage, inci<br>dent queues                             |  |  |
| Retry and repair                                                                                                                             | Extra model calls,<br>extra tool<br>calls, self-repair loops, manual<br>repair work         | Agent<br>traces,<br>tool-call<br>logs,<br>retry<br>counters                       |  |  |
| Escalation and excep<br>tion handling                                                                                                        | Escalated cases times average<br>handling time and labor rate                               | Ticket queues, approval logs, opera<br>tions records                              |  |  |
| Revalidation<br>after<br>change                                                                                                              | Retesting<br>and<br>approval<br>after<br>model, prompt, tool, policy, or<br>context changes | Release records, model-version logs,<br>validation plans                          |  |  |
| Latency and delay                                                                                                                            | Excess latency relative to target<br>times delay cost, plus SLA or<br>abandonment cost      | Latency<br>dashboards,<br>SLA<br>records,<br>conversion or productivity estimates |  |  |
| Token,<br>compute,<br>and<br>Expected tokens per transaction<br>times unit cost, plus compute<br>context processing<br>and tool-call charges |                                                                                             | Model bills, token logs, context re<br>trieval logs                               |  |  |
| Security and guardrail<br>Security<br>flags,<br>input/output<br>maintenance<br>guardrail<br>reviews,<br>adversarial<br>test updates          |                                                                                             | Security logs, guardrail logs, red-team<br>records                                |  |  |

### **5.2 Total and Average Stochastic Tax**

Let *T STw,t* denote total stochastic tax for workflow *w* in period *t*. Let K denote the eight cost categories in Table [3.](#page-9-0) Then

<span id="page-9-1"></span>
$$TST_{w,t} = \sum_{k \in \mathcal{K}} C_{w,t}^k. \tag{7}$$

The per-transaction tax reported on a dashboard is

<span id="page-9-2"></span>
$$\overline{ST}_{w,t} = \frac{TST_{w,t}}{N_{w,t}}. (8)$$

Equations [7](#page-9-1) and [8](#page-9-2) separate total budget burden from unit economics. Total tax may rise with adoption even while per-transaction tax falls because fixed evaluation, monitoring, and governance costs are spread over more transactions. This distinction is important for managers because a scaled agent can look more expensive in total dollars while becoming more efficient per transaction.

### **5.3 Scales for Operating Drivers**

Before specifying the structural form, the operating drivers need clear scales. Table [4](#page-10-0) defines the variables used in the operating-exposure amplifier.

<span id="page-10-0"></span>

| Symbol | Scale                   | Interpretation                                                                                                                                                                  |
|--------|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Uw,t   | Positive count or index | Adoption or usage exposure, such as transactions,<br>active users, teams, or distinct usage contexts. In the<br>simulation,<br>U<br>=<br>N.                                     |
| Sw,t   | Positive count or index | Surface<br>area,<br>such<br>as<br>tools,<br>connectors,<br>context<br>sources, permissions, APIs, or external systems.                                                          |
| Hw,t   | Positive count          | Workflow horizon, measured as the number of depen<br>dent agentic steps or the effective depth of the action<br>chain.                                                          |
| Aw,t   | [0,<br>1]               | Autonomy and action criticality: 0 = advisory, 0.5 =<br>approval-required, 1 = direct execution in external<br>systems.                                                         |
| Θw,t   | [0,<br>1]               | Model or platform variability: 0 = stable behavior<br>under fixed tests, 0.5 = moderate run-to-run or ver<br>sion drift, 1 = high variability or rapid provider-side<br>change. |

**Table 4:** Operating-Exposure Variables and Scales

These scales make the coefficients interpretable. A manager can score *A* and Θ consistently across workflows even when the exact engineering measures differ.

# **5.4 Cost-Category Structural Form**

Each cost category has three drivers: a baseline floor, a debt amplifier, and an operatingexposure amplifier. The baseline floor is what the workflow would cost at zero *Agentic Technical Debt* and at reference operating conditions. The debt amplifier, Φ*k*(*Dw,t*), is a function of *Dw,t* and captures the effect of accumulated *Agentic Technical Debt*. The operating-exposure amplifier, Ψ*k*(*Uw,t, Sw,t, Hw,t, Aw,t,* Θ*w,t*), captures adoption, surface area, workflow horizon, autonomy, and inherent model variability.

For each category *k*, define

<span id="page-10-1"></span>
$$C_{w,t}^{k} = \underbrace{(F_k + V_k N_{w,t})}_{\text{baseline floor}} \cdot \underbrace{\Phi_k(D_{w,t})}_{\text{debt amplifier}} \cdot \underbrace{\Psi_k(U_{w,t}, S_{w,t}, H_{w,t}, A_{w,t}, \Theta_{w,t})}_{\text{operating-exposure amplifier}}.$$
(9)

The variables and parameters in Equation [9](#page-10-1) are:

- *F<sup>k</sup>* ≥ 0 is the fixed or semi-fixed cost of category *k* in a period, such as maintaining an evaluation suite or observability pipeline.
- *V<sup>k</sup>* ≥ 0 is the baseline variable cost per completed transaction in category *k*.
- *Nw,t* is completed transactions.
- *Dw,t* is the normalized *Agentic Technical Debt* index from Equation [4.](#page-8-0)
- *Uw,t*, *Sw,t*, *Hw,t*, *Aw,t*, and Θ*w,t* are the operating-exposure variables defined in Table [4.](#page-10-0)
- Φ*k*(·) and Ψ*k*(·) are normalized amplifiers defined below.

Analytically, Equation [9](#page-10-1) makes the floor visible. The model cannot accidentally say that operating cost is zero when debt is zero. Practically, the equation gives managers a way to ask whether a rise in cost is coming from more usage, a larger surface area, longer workflows, greater autonomy, external variability, or accumulated debt.

### **5.5 Debt Amplifier**

The simplest useful debt amplifier is linear:

$$\Phi_k(D_{w,t}) = 1 + \beta_k D_{w,t}, \qquad \beta_k \ge 0, \qquad \Phi_k(0) = 1.$$
(10)

The coefficient *β<sup>k</sup>* is the debt sensitivity of category *k*. If *βretry* = 2*.*5, then moving from *D* = 0 to *D* = 1 multiplies retry-related cost by 3*.*5, holding other drivers fixed. Larger values of *β<sup>k</sup>* are plausible for retry, revalidation, and evaluation because brittle prompts, weak tool schemas, and poor observability tend to appear first in those categories. Smaller values may be plausible for categories that are more infrastructure-driven, such as baseline monitoring.

The practical value of *β<sup>k</sup>* depends on calibration. A team can begin with expert estimates, but the debt-amplified decomposition should be treated as a scenario estimate until the team has observed enough periods, incidents, releases, or remediation interventions to update the values.

# **5.6 Operating-Exposure Amplifier**

The operating-exposure amplifier captures the fact that *Stochastic Tax* can rise even when *Agentic Technical Debt* is unchanged. More adoption means more users, prompts, edge cases, and exception opportunities. More surface area means more tools, context sources, permissions, and possible attack vectors. Longer horizons make cascading errors more likely. Higher autonomy increases the need for control. Greater model variability raises the need for evaluation and revalidation.

Let *U*0, *S*0, *H*0, *A*0, and Θ<sup>0</sup> denote reference operating values. A coherent positive form is

$$\Psi_k(U_{w,t}, S_{w,t}, H_{w,t}, A_{w,t}, \Theta_{w,t}) = \exp\left[\gamma_k^U \ln\left(\frac{U_{w,t}}{U_0}\right) + \gamma_k^S \ln\left(\frac{S_{w,t}}{S_0}\right) + \gamma_k^H \ln\left(\frac{H_{w,t}}{H_0}\right) + \gamma_k^A (A_{w,t} - A_0) + \gamma_k^\Theta(\Theta_{w,t} - \Theta_0)\right].$$
(11)

Here  $\gamma_k^U$ ,  $\gamma_k^S$ , and  $\gamma_k^H$  are elasticities with respect to adoption, surface area, and horizon. For example,  $\gamma_k^U = 0.10$  means that a tenfold increase in U multiplies category-k cost by approximately  $10^{0.10}$ , holding other drivers fixed.  $\gamma_k^A$  and  $\gamma_k^\Theta$  are semi-elasticities for the bounded scores A and  $\Theta$ . The exponential form guarantees that  $\Psi_k > 0$  without imposing an arbitrary floor. At the reference values,  $\Psi_k = 1$ .

For dashboard implementation, teams can start with only U and S if data are limited, then add H, A, and  $\Theta$  as the measurement program matures.

### 5.7 Three Properties Built Into the Model

The model encodes three properties that clarify why  $Stochastic\ Tax$  is not simply interest on  $Agentic\ Technical\ Debt$ .

#### Three properties of the model

**P1. Nonzero baseline.** When  $D_{w,t} = 0$ ,  $\Phi_k(0) = 1$ , but  $TST_{w,t}$  remains positive if at least one category has  $F_k + V_k N_{w,t} > 0$ . A zero-debt agentic workflow still carries stochastic tax. This is the formal statement of the first meaning of *Stochastic Tax*: the tax exists because the system is stochastic, not because the workflow is badly engineered.

**P2.** Debt amplification. If  $\beta_k \geq 0$ , then

$$\frac{\partial C_{w,t}^k}{\partial D_{w,t}} = (F_k + V_k N_{w,t}) \beta_k \Psi_k(\cdot) \ge 0.$$

Accumulated debt raises category cost. Debt amplifies the tax; it does not create the tax from nothing.

P3. Independent operating-exposure channel. If any operating-exposure coefficient is positive, then  $Stochastic\ Tax$  can rise even when  $D_{w,t}$  is unchanged. Adoption, surface area, workflow horizon, autonomy, and model variability can each raise the tax independently. P2 and P3 formalize the second meaning of  $Stochastic\ Tax$ : the tax rate itself moves with debt, operating exposure, and the event rates that those drivers influence.

A useful implication follows. If a team pays down Agentic Technical Debt but still observes a rising Stochastic Tax, this is not necessarily a failure of debt remediation. It may mean the system is being used more widely, exposes more tools and data sources, or operates with higher autonomy. The dashboard should therefore decompose observed tax rather than treating every increase as evidence of debt.

# 5.8 Baseline and Debt-Amplified Tax

The conceptual dashboard decomposition is

<span id="page-12-0"></span>
$$\overline{ST}_{w,t} = \overline{ST}_{w,t}^0 + \overline{ST}_{w,t}^D, \tag{12}$$

where

$$\overline{ST}_{w,t}^0 = \overline{ST}_{w,t} \mid D_{w,t} = 0, \tag{13}$$

<span id="page-13-0"></span>
$$\overline{ST}_{w,t}^D = \overline{ST}_{w,t} - \overline{ST}_{w,t}^0. \tag{14}$$

 $\overline{ST}_{w,t}^0$  is the baseline stochastic tax, or the tax associated with operating a stochastic, toolusing workflow at the current level of adoption, surface area, horizon, autonomy, and variability.  $\overline{ST}_{w,t}^D$  is the debt-amplified tax, or the additional burden associated with accumulated Agentic  $Technical\ Debt$ .

This decomposition is conceptually important, but it should not be overinterpreted before calibration. Computing  $\overline{ST}_{w,t}^0$  requires values for  $\beta_k$ . Those values are usually not directly observed. A manager should therefore report the decomposition as a calibrated estimate, with sensitivity ranges, until the organization has learned  $\beta_k$  from history, interventions, or expert judgment.

#### 5.9 Calibrating Debt Sensitivities

A feasible way to calibrate  $\beta_k$  is to compare periods or workflows with materially different debt scores while holding operating exposure approximately constant. Define the normalized observed category cost

$$Z_{w,t}^{k} = \frac{C_{w,t}^{k}}{(F_k + V_k N_{w,t})\Psi_k(U_{w,t}, S_{w,t}, H_{w,t}, A_{w,t}, \Theta_{w,t})}.$$
(15)

Under Equation 9,  $Z_{w,t}^k = 1 + \beta_k D_{w,t}$ . With two observations  $t_1$  and  $t_2$ ,

$$\widehat{\beta}_k \approx \frac{Z_{w,t_2}^k - Z_{w,t_1}^k}{D_{w,t_2} - D_{w,t_1}}, \qquad D_{w,t_2} \neq D_{w,t_1}. \tag{16}$$

In practice, a team might estimate  $\widehat{\beta}_k$  after a refactoring sprint that lowers tool/schema debt, after a prompt rationalization project, or across comparable workflows with different debt scores. If such observations are not available,  $\beta_k$  should be treated as an expert prior and stress-tested in the spreadsheet. The decomposition in Equations 12 to 14 becomes more decision-ready as these estimates improve.

Other parameters can be estimated with the same pragmatic discipline. The fixed terms  $F_k$  and baseline unit costs  $V_k$  can come from accounting allocations, model bills, observability invoices, labor rates, and logs at a reference operating point. The exposure coefficients  $\gamma$  can be updated from before-after observations when adoption, surface area, horizon, autonomy, or model variability changes materially while other drivers remain approximately stable. Unit costs such as  $c_t^{tok}$  and  $c_{w,t}^{lat}$  can come from provider pricing, internal compute charges, labor-cost models, SLA penalties, or business estimates of delay. Event rates such as  $q_{w,t}^j$  can be read from traces, incident queues, security logs, and escalation records. This keeps the model feasible: teams can begin with approximate but transparent assumptions, then replace them with observed estimates over time.

# 6 Estimating Cost Categories from Operational Data

The structural model explains and forecasts category costs. A dashboard also needs measurement rules for estimating each  $C_{w,t}^k$  from logs, invoices, tickets, and labor records. These measurement equations produce the same quantities as the structural model when calibrated to the same drivers; they differ in inputs. The structural form asks, "what should the cost be, given debt and operating exposure?" The measurement layer asks, "what did the cost actually amount to this period?"

A general direct-measurement expression is

$$C_{w,t}^{k} = F_{w,t}^{obs,k} + \sum_{m \in \mathcal{M}_{k}} x_{w,t}^{k,m} p_{w,t}^{k,m}.$$
(17)

Here  $F_{w,t}^{obs,k}$  is an observed fixed or allocated cost for category k,  $\mathcal{M}_k$  is the set of measured resource types in that category,  $x_{w,t}^{k,m}$  is the observed quantity of resource m used in category k, and  $p_{w,t}^{k,m}$  is the unit price of that resource. Examples include model calls, reviewer hours, storage volume, security analyst time, tool calls, and escalated tickets.

For rate-based categories such as retry, escalation, and security flags, a convenient special case is

$$C_{w,t}^{j} = N_{w,t} q_{w,t}^{j} c_{w,t}^{j}, (18)$$

where j is an event type,  $q_{w,t}^j$  is the event rate per transaction, and  $c_{w,t}^j$  is the average cost per event. For example, escalation cost can be estimated as transactions times escalation rate times average handling cost.

Token and context-processing costs can often be measured directly from model logs:

$$C_{w,t}^{token} = N_{w,t} \frac{\mathbb{E}[Tok_{w,t}]}{1000} c_t^{tok} + C_{w,t}^{compute}.$$
 (19)

 $\mathbb{E}[Tok_{w,t}]$  is expected tokens consumed per transaction,  $c_t^{tok}$  is the blended cost per 1,000 tokens, and  $C_{w,t}^{compute}$  captures additional compute, retrieval, or tool-execution charges not included in the token price. In the structural model, the baseline value of this expression at reference operating conditions is absorbed into  $F_{token} + V_{token}N$ .

Latency cost can be measured relative to a target:

$$C_{w,t}^{latency} = N_{w,t} c_{w,t}^{lat} \mathbb{E}\left[ (L_{w,t} - L_w^*)_+ \right]. \tag{20}$$

Here  $L_{w,t}$  is observed latency,  $L_w^*$  is the target latency for workflow w,  $(x)_+ = \max(0, x)$ , and  $c_{w,t}^{lat}$  is the business cost of one unit of excess delay. As with token cost, the structural parameter  $V_{latency}$  absorbs the expected reference-condition cost, while the observed measurement equation is used to populate and recalibrate the dashboard.

Table 5 links each category to a practical measurement rule.

**Table 5:** Practical Measurement Rules for Cost Categories

<span id="page-15-0"></span>

| Category                       | First-cut measurement                                                                          | Common pitfall                                                                             |  |  |
|--------------------------------|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|--|--|
| Evaluation                     | Test runs, judge calls, and reviewer<br>hours times unit costs                                 | Forgetting maintenance of the<br>test set itself.                                          |  |  |
| Monitoring                     | Allocated observability cost plus alert<br>review hours                                        | Allocating<br>shared<br>monitoring<br>cost inconsistently across work<br>flows.            |  |  |
| Retry and repair               | Retry count times incremental mod<br>el/tool cost plus repair labor                            | Counting<br>retries<br>but<br>ignoring<br>self-repair loops that still con<br>sume tokens. |  |  |
| Escalation                     | Escalation rate times average handling<br>cost                                                 | Treating escalations as failures<br>even when they are appropriate<br>controls.            |  |  |
| Revalidation                   | Retest hours and calls after model,<br>prompt,<br>tool,<br>context,<br>or<br>policy<br>changes | Charging all revalidation to the<br>model rather than the workflow<br>that required it.    |  |  |
| Latency and delay              | Expected excess latency times busi<br>ness delay cost                                          | Using average latency while ig<br>noring tail latency.                                     |  |  |
| Token, compute, and<br>context | Token<br>logs,<br>model<br>bills,<br>retrieval<br>charges, and tool-execution cost             | Ignoring context retrieval and re<br>peated calls.                                         |  |  |
| Security<br>and<br>guardrails  | Flag review time, red-team updates,<br>guardrail calls, and security operations<br>effort      | Treating guardrails as one-time<br>implementation rather than re<br>curring maintenance.   |  |  |

The measurement layer and structural layer should be used together. Observed category costs provide the dashboard numbers. The structural model explains why those numbers change and supports simulations of what could happen if debt, adoption, surface area, horizon, autonomy, or model variability changes.

# **7 Numerical Illustration: Accounts-Payable Agent**

The simulation below illustrates the model with a hypothetical accounts-payable agentic workflow. The workflow extracts invoice fields, checks vendor identity, validates payment terms, applies policy rules, and schedules payment. It uses several tools and context sources, produces traces, and escalates exceptions to a human queue. The calibration is illustrative. It is designed to be plausible enough for managerial reasoning, not to estimate a universal industry benchmark.

# **7.1 Cost-Category Calibration**

Table [6](#page-16-0) reports the primary cost parameters. *V<sup>k</sup>* is baseline variable cost per transaction. *F<sup>k</sup>* is fixed monthly cost. *β<sup>k</sup>* is the debt amplifier. The *γ* columns are operating-exposure sensitivities. All dollar values are monthly and illustrative.

**Table 6:** Cost-Category Parameters for the Accounts-Payable Simulation

<span id="page-16-0"></span>

| Category k                           | Vk    | Fk  | βk  | U<br>γ<br>k | S<br>γ<br>k | H<br>γ<br>k | A<br>γ<br>k | Main intuition                                          |
|--------------------------------------|-------|-----|-----|-------------|-------------|-------------|-------------|---------------------------------------------------------|
| Evaluation                           | 0.010 | 200 | 1.2 | 0.12        | 0.08        | 0.08        | 0.12        | Fragile systems need more test<br>and reviewer effort.  |
| Monitoring                           | 0.005 | 350 | 0.4 | 0.10        | 0.06        | 0.04        | 0.06        | Trace volume and alert triage<br>rise with scale.       |
| Retry and repair                     | 0.040 | 0   | 2.5 | 0.07        | 0.05        | 0.12        | 0.10        | Brittle prompts and schemas<br>produce malformed calls. |
| Escalation                           | 0.120 | 80  | 1.0 | 0.08        | 0.06        | 0.10        | 0.18        | Exceptions need human review.                           |
| Revalidation                         | 0.002 | 400 | 1.8 | 0.10        | 0.12        | 0.12        | 0.10        | Model, tool, and policy changes<br>need retesting.      |
| Latency and delay                    | 0.030 | 50  | 0.8 | 0.05        | 0.05        | 0.18        | 0.15        | Long chains and retries create<br>delay.                |
| Token,<br>compute,<br>and<br>context | 0.200 | 0   | 0.6 | 0.03        | 0.08        | 0.12        | 0.08        | Large context and repeated calls<br>raise compute cost. |
| Security and guardrails              | 0.008 | 150 | 0.3 | 0.15        | 0.18        | 0.05        | 0.20        | More tools and users expand at<br>tack surface.         |

The corresponding *γ* Θ *<sup>k</sup>* values are 0.15, 0.08, 0.12, 0.08, 0.20, 0.10, 0.08, and 0.12 for evaluation, monitoring, retry and repair, escalation, revalidation, latency and delay, token/context, and security/guardrails, respectively. The companion spreadsheet exposes all parameters as editable cells.

### **7.2 Four-Scenario Comparative Statics**

The first simulation uses a 2 × 2 design: low versus high adoption crossed with low versus high debt. Holding other variables constant makes the interpretation clean. It shows what scale does when debt is low, what debt does when adoption is low, and what happens when scale and debt meet.

**Table 7:** Scenario Inputs

| Scenario                     | N      | D    | U      | S  | H | A    | Description                   |
|------------------------------|--------|------|--------|----|---|------|-------------------------------|
| S1: Low adoption, low debt   | 1,000  | 0.10 | 1,000  | 5  | 4 | 0.40 | Carefully governed pilot.     |
| S2: High adoption, low debt  | 10,000 | 0.10 | 10,000 | 15 | 4 | 0.40 | Scaled with disciplined gover |
|                              |        |      |        |    |   |      | nance.                        |
| S3: Low adoption, high debt  | 1,000  | 0.60 | 1,000  | 5  | 4 | 0.40 | Pilot with accumulated debt.  |
| S4: High adoption, high debt | 10,000 | 0.60 | 10,000 | 15 | 4 | 0.40 | Scaled with accumulated debt. |

All four scenarios set Θ = 0*.*30. This keeps the example focused on adoption, surface area, and debt.

**Table 8:** Stochastic Tax Under the Four Scenarios

<span id="page-17-0"></span>

| Scenario                     | Total TST | ST per tx | Baseline per tx | Debt-amplified per tx |
|------------------------------|-----------|-----------|-----------------|-----------------------|
| S1: Low adoption, low debt   | \$1,810   | \$1.81    | \$1.65          | \$0.16                |
| S2: High adoption, low debt  | \$7,520   | \$0.75    | \$0.69          | \$0.07                |
| S3: Low adoption, high debt  | \$2,634   | \$2.63    | \$1.65          | \$0.99                |
| S4: High adoption, high debt | \$10,799  | \$1.08    | \$0.69          | \$0.39                |

Three patterns are visible in Table [8.](#page-17-0) First, the tax is positive even at low debt. Second, adoption can reduce per-transaction tax by amortizing fixed evaluation, monitoring, and governance costs. In the low-debt case, scaling from S1 to S2 reduces per-transaction tax by about \$1.06. Third, debt steals some of these economies of scale. Scaling from S1 to S4 reduces per-transaction tax by only about \$0.73. The difference, roughly \$0.33 per transaction, is a useful managerial number: it is the per-transaction saving that accumulated debt prevents the team from capturing.

![](_page_17_Figure_3.jpeg)

**Figure 1:** Per-transaction *Stochastic Tax* across the four scenarios.

![](_page_18_Figure_0.jpeg)

**Figure 2:** Baseline and debt-amplified *Stochastic Tax* by scenario. The baseline component remains positive when debt is set to zero.

### **7.3 ATD Sensitivity Sweep**

The second simulation isolates the debt channel. It holds adoption, surface area, horizon, autonomy, and model variability fixed at the high-adoption operating point and varies *D* from 0 to 1. This answers a practical question: if our debt score rises by 0.1 at the current scale, how much will per-transaction tax increase?

**Table 9:** Sensitivity of *Stochastic Tax* to the *Agentic Technical Debt* Index at High Adoption

| D    | Total TST | ST<br>per tx | Change vs.<br>D<br>= 0 |  |
|------|-----------|--------------|------------------------|--|
| 0.00 | \$6,864   | \$0.69       | –                      |  |
| 0.25 | \$8,504   | \$0.85       | +24%                   |  |
| 0.50 | \$10,143  | \$1.01       | +48%                   |  |
| 0.75 | \$11,783  | \$1.18       | +72%                   |  |
| 1.00 | \$13,423  | \$1.34       | +96%                   |  |

At *D* = 0, the per-transaction tax is still \$0.69. This is the nonzero floor. At this operating point, the relationship is approximately linear because the debt amplifier is linear. The local slope is managerially interpretable: it is the expected per-transaction increase in *Stochastic Tax* for a unit increase in the debt index, holding other operating conditions fixed.

![](_page_19_Figure_0.jpeg)

**Figure 3:** ATD sensitivity sweep at a fixed high-adoption operating point.

### **7.4 Twelve-Month Dynamic Paths**

The third simulation shows how governance changes the path. Both workflows start at the same debt level and the same high-adoption operating point. Path A accumulates more debt than it remediates. Path B remediates more debt than it accumulates.

For this illustration, we use the simplified debt dynamics in Equation [3.](#page-7-0) Path A uses ∆*acc*−∆*rem* = 0*.*06−0*.*02 = +0*.*04 per month. Path B uses ∆*acc*−∆*rem* = 0*.*03−0*.*07 = −0*.*04 per month. The companion spreadsheet exposes all four rates as editable inputs.

**Table 10:** Twelve-Month Evolution of *Agentic Technical Debt* and *Stochastic Tax* per Transaction

| Month | Path A:<br>D | Path A:<br>ST | Path B:<br>D | Path B:<br>ST |
|-------|--------------|---------------|--------------|---------------|
| 0     | 0.10         | \$0.75        | 0.10         | \$0.75        |
| 3     | 0.22         | \$0.83        | 0.00         | \$0.69        |
| 6     | 0.34         | \$0.91        | 0.00         | \$0.69        |
| 9     | 0.46         | \$0.99        | 0.00         | \$0.69        |
| 12    | 0.58         | \$1.07        | 0.00         | \$0.69        |

By month 12, the accumulation path pays about \$0.38 more per transaction than the governance path. At 10,000 transactions per month, that is about \$3,804 per month, or roughly \$45,649 per year, for one workflow. The point is not that the illustrative dollar values are universal. The point is that the model turns a vague concern about debt into a dashboard quantity that can be tracked, simulated, and governed.

![](_page_20_Figure_0.jpeg)

**Figure 4:** Dynamic paths for an accumulation regime and a governance regime.

# **8 From Model to Dashboard**

The model supports a managerial dashboard that answers four recurring questions.

- 1. **Is operating burden stable, rising, or concentrated?** Track *T STw,t* and *ST w,t* by workflow and period.
- 2. **Is rising tax explained by adoption, surface area, autonomy, variability, or debt?** Decompose changes in tax across drivers rather than treating every increase as debt.
- 3. **Is debt accumulating or being paid down?** Track *Dw,t* and its six components over time.
- 4. **Which intervention is appropriate?** Use the decomposition to distinguish refactoring decisions from operating-control decisions.

Table [11](#page-21-0) gives a minimal dashboard design.

**Table 11:** Dashboard Fields per Workflow per Period

<span id="page-21-0"></span>

| Field                                | Definition                                                                                               | Managerial use                                                                                           |
|--------------------------------------|----------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| Dw,t                                 | Composite<br>Agentic Technical Debt<br>index in<br>[0,<br>1], often reported as 0<br>to 100              | Track debt stock and trigger gover<br>nance review above threshold.                                      |
| Component<br>scores<br>i<br>d<br>w,t | Debt scores for context, tools, mem<br>ory,<br>orchestration,<br>observability,<br>and platform coupling | Identify the remediation target.                                                                         |
| T STw,t                              | Total stochastic tax for the period                                                                      | Budget item and operating-cost allo<br>cation.                                                           |
| ST<br>w,t                            | Tax per completed transaction                                                                            | Compare unit economics across work<br>flows.                                                             |
| ST0<br>w,t                           | Baseline tax when<br>D<br>= 0<br>at current<br>operating exposure                                        | Set expectations for debt-paydown<br>benefits, subject to calibration uncer<br>tainty.                   |
| D<br>ST<br>w,t                       | Debt-amplified tax                                                                                       | Estimate avoidable burden associated<br>with accumulated debt, after<br>βk<br>val<br>ues are calibrated. |
| Driver indicators                    | Adoption, surface area, horizon, au<br>tonomy, variability                                               | Diagnose whether tax growth is due<br>to scale, complexity, or debt.                                     |
| Calibration status                   | Expert prior, before-after estimate,<br>regression estimate, or validated es<br>timate                   | Prevents the dashboard from overstat<br>ing precision.                                                   |

The dashboard should also display category diagnostics such as token cost per transaction, retry rate, escalation rate, P95 latency, security-flag rate, and revalidation hours after changes. These signals help managers move from measurement to action. If token cost rises while debt is flat, context-management or retrieval strategy may be the right target. If retry and revalidation costs rise together with tool/schema debt, refactoring interfaces may be more important. If total tax rises while per-transaction tax falls, the system may be scaling responsibly.

# **9 Implementation Guidance**

A practical implementation can proceed in seven steps.

- 1. **Define workflow boundaries.** Specify where the workflow begins and ends, such as invoice intake to payment scheduling.
- 2. **Score the debt stock.** Score the six debt components using evidence from prompts, tools, traces, tests, release records, and governance artifacts.
- 3. **Collect operating signals.** Capture token use, retry rate, escalation rate, latency, security flags, evaluation effort, monitoring effort, and revalidation work.

- 4. Convert signals into dollars. Use token prices, labor rates, delay costs, tool-call charges, and allocated fixed costs.
- 5. Calibrate the structural parameters. Estimate  $F_k$  and  $V_k$  from accounting and logs. Estimate  $\gamma$  values from scale, surface, horizon, autonomy, and variability changes. Treat  $\beta_k$  as an expert prior until the team has before-after or cross-workflow evidence.
- 6. Estimate the baseline with uncertainty. Calculate  $\overline{ST}_{w,t}^0$  by setting  $D_{w,t} = 0$  only after choosing a calibrated or sensitivity-tested set of  $\beta_k$  values.
- 7. Use the decomposition for decisions. Treat baseline tax as an operating reality to manage and debt-amplified tax as a candidate for remediation.

The model is feasible because it does not require perfect causal identification before it becomes useful. A dashboard can begin with observed costs and expert-calibrated parameters, then improve as the organization observes releases, incidents, growth, and remediation efforts.

#### 10 Limitations and Extensions

This framework is intended for conceptual clarification and managerial measurement. It is not a universal metric. Several limitations should be acknowledged.

First, cost attribution can be imperfect. Evaluation, monitoring, and security costs are often shared across workflows. Managers should use transparent allocation rules and avoid false precision. Second, the causal effect of Agentic Technical Debt on Stochastic Tax may be difficult to identify without interventions, redesigns, or controlled comparisons. The  $\beta_k$ coefficients should therefore be treated as calibrated estimates, not directly observed truths. Third, rare but severe failures may not be well represented by average costs. A dashboard should include tail-risk indicators in addition to average tax. Fourth, some organizations may intentionally accept a high baseline tax in regulated or safety-critical settings because stronger evaluation, monitoring, and human review are prudent. Fifth, functional forms may need adjustment. Some systems may exhibit thresholds, nonlinear cascades, or saturation effects that the linear debt amplifier does not capture. Sixth, the model in this note treats  $\overline{ST}_{w,t}$  as a deterministic function of its drivers, even though underlying event rates such as  $q_{w,t}^j$  are random variables. A natural extension is to model  $\overline{ST}_{w,t}$  as an expected value with a variance derived from event-rate distributions, which would let the second meaning of Stochastic Tax be displayed as a confidence band on the dashboard rather than a point estimate.

These limitations do not weaken the usefulness of the model. They clarify how it should be used. The model is a disciplined accounting and governance lens, not a replacement for managerial judgment.

### 11 Conclusion

Agentic Technical Debt and Stochastic Tax are best modeled as distinct but connected properties of agentic systems. Agentic Technical Debt is the stock of accumulated design

and governance liability. *Stochastic Tax* is the flow of recurring operating burden created by stochastic action in real workflows. Debt can amplify the tax, but the tax also arises from adoption, surface area, workflow horizon, autonomy, and inherent model variability. The model in this note makes that distinction operational. It gives managers a debt index, a cost-category structure, a baseline versus debt-amplified decomposition, a calibration path for the difficult *β<sup>k</sup>* parameters, and a simulation approach that can be implemented in a spreadsheet dashboard. This is why tax is a better metaphor than interest: interest suggests a rate paid on a fixed debt principal, whereas *Stochastic Tax* includes a persistent baseline and a rate that can move with debt, usage, surface area, autonomy, and the stochastic event process itself.

# **References**

<span id="page-23-0"></span>Cunningham, W. 1992. The WyCash portfolio management system. In *Addendum to the Proceedings on Object-Oriented Programming Systems, Languages, and Applications*, 29–30.

<span id="page-23-1"></span>Ramasubbu, N., Kemerer, C. F., and Woodard, C. J. 2015. Managing technical debt: Insights from recent empirical evidence. *IEEE Software* 32, 2, 22–25.

<span id="page-23-2"></span>Sculley, D., Holt, G., Golovin, D., Davydov, E., Phillips, T., Ebner, D., Chaudhary, V., Young, M., Crespo, J.-F., and Dennison, D. 2015. Hidden technical debt in machine learning systems. In *Advances in Neural Information Processing Systems*, 28.

<span id="page-23-3"></span>Bommasani, R., Hudson, D. A., Adeli, E., Altman, R., von Arx, S., and others. 2021. On the opportunities and risks of foundation models. *arXiv preprint arXiv:2108.07258*.

<span id="page-23-4"></span>Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., and Cao, Y. 2022. ReAct: Synergizing reasoning and acting in language models. *arXiv preprint arXiv:2210.03629*.

# **A Full Simulation Parameters**

<span id="page-23-5"></span>Reference values used in the simulation are *U*<sup>0</sup> = 1*,*000, *S*<sup>0</sup> = 5, *H*<sup>0</sup> = 4, *A*<sup>0</sup> = 0*.*40, and Θ<sup>0</sup> = 0*.*30. Table [12](#page-23-5) reports all amplifier coefficients, including *γ* Θ *k* as a column.

| Table 12:<br>Full Cost-Category Parameters |  |
|--------------------------------------------|--|
|--------------------------------------------|--|

| Category          | Vk    | Fk  | βk  | U<br>γ<br>k | S<br>γ<br>k | H<br>γ<br>k | A<br>γ<br>k | Θ<br>γ<br>k |
|-------------------|-------|-----|-----|-------------|-------------|-------------|-------------|-------------|
| Evaluation        | 0.010 | 200 | 1.2 | 0.12        | 0.08        | 0.08        | 0.12        | 0.15        |
| Monitoring        | 0.005 | 350 | 0.4 | 0.10        | 0.06        | 0.04        | 0.06        | 0.08        |
| Retry and repair  | 0.040 | 0   | 2.5 | 0.07        | 0.05        | 0.12        | 0.10        | 0.12        |
| Escalation        | 0.120 | 80  | 1.0 | 0.08        | 0.06        | 0.10        | 0.18        | 0.08        |
| Revalidation      | 0.002 | 400 | 1.8 | 0.10        | 0.12        | 0.12        | 0.10        | 0.20        |
| Latency and delay | 0.030 | 50  | 0.8 | 0.05        | 0.05        | 0.18        | 0.15        | 0.10        |

| Category               | 7              | $V_k$ | $F_k$ | $\beta_k$ | $\gamma_k^U$ | $\gamma_k^S$ | $\gamma_k^H$ | $\gamma_k^A$ | $\gamma_k^{\Theta}$ |
|------------------------|----------------|-------|-------|-----------|--------------|--------------|--------------|--------------|---------------------|
| Token, and contex      | compute,<br>xt | 0.200 | 0     | 0.6       | 0.03         | 0.08         | 0.12         | 0.08         | 0.08                |
| Security<br>guardrails |                | 0.008 | 150   | 0.3       | 0.15         | 0.18         | 0.05         | 0.20         | 0.12                |

# B Equations in One Place

For reference, the central model consists of the following equations:

$$\mathbf{d}_{w,t} = \left(d_{w,t}^{ctx}, d_{w,t}^{tool}, d_{w,t}^{mem}, d_{w,t}^{orch}, d_{w,t}^{bbs}, d_{w,t}^{plat}\right), \qquad \text{(Debt components)}$$

$$d_{w,t+1}^{i} = \Pi_{[0,1]} \left[ \left(1 - \phi_{i} R_{w,t}^{i}\right) d_{w,t}^{i} + \alpha_{i} X_{w,t}^{i} Q_{w,t}^{i} \left(1 - G_{w,t}^{i}\right) + \zeta_{i} V_{w,t}^{plat} E_{w,t}^{i}\right], \qquad \text{(Debt dynamics)}$$

$$D_{w,t} = \Pi_{[0,1]} \left[ \sum_{i} \omega_{i} d_{w,t}^{i} + \sum_{i < j} \omega_{ij} d_{w,t}^{i} d_{w,t}^{j} \right], \qquad \text{(Debt index)}$$

$$C_{w,t}^{k} = (F_{k} + V_{k} N_{w,t}) \Phi_{k} (D_{w,t}) \Psi_{k} (U_{w,t}, S_{w,t}, H_{w,t}, A_{w,t}, \Theta_{w,t}), \qquad \text{(Cost category)}$$

$$\Phi_{k} (D_{w,t}) = 1 + \beta_{k} D_{w,t}, \qquad \text{(Debt amplifier)}$$

$$\Psi_{k}(\cdot) = \exp \left[ \gamma_{k}^{U} \ln \left( \frac{U_{w,t}}{U_{0}} \right) + \gamma_{k}^{S} \ln \left( \frac{S_{w,t}}{S_{0}} \right) + \gamma_{k}^{H} \ln \left( \frac{H_{w,t}}{H_{0}} \right) + \gamma_{k}^{A} (A_{w,t} - A_{0}) + \gamma_{k}^{\Theta} (\Theta_{w,t} - \Theta_{0}) \right], \qquad \text{(Exposure amplifier)}$$

$$TST_{w,t} = \sum_{k \in \mathcal{K}} C_{w,t}^{k}, \qquad \overline{ST}_{w,t} = \frac{TST_{w,t}}{N_{w,t}}, \qquad \text{(Total and average ST)}$$

$$\overline{ST}_{w,t} = \overline{ST}_{w,t}^{0} + \overline{ST}_{w,t}^{D}. \qquad \text{(Baseline plus debt-amplified ST)}$$

# C Companion Excel Spreadsheet

The companion Excel spreadsheet implements the same notation and model as this note. It is designed to let readers change reference values, category parameters, scenario inputs, and dynamic-path assumptions while seeing how the stochastic-tax dashboard responds. The spreadsheet contains:

- **README:** a concise explanation of the spreadsheet's purpose and notation.
- Parameters: editable reference values, cost-category parameters, six ATD components, scenario inputs, and dynamic-path inputs.
- Scenarios: formula-driven category-cost calculations for the four scenarios.

- **Summary:** total and per-transaction tax, baseline tax, debt-amplified tax, and key computed insights.
- **ATD\_Sensitivity:** a sweep from *D* = 0 to *D* = 1 at a fixed high-adoption operating point.
- **Time\_Series:** the accumulation and governance paths using the simplified debt dynamics in Equation [3.](#page-7-0)
- **Data\_Dictionary:** definitions of all symbols used in the spreadsheet.
- **Dashboard:** a compact managerial view of scenario results and key performance indicators.

The spreadsheet is intended for exploration, not as a universal benchmark. Managers should replace the illustrative parameters with their own token prices, labor rates, event rates, observed category costs, debt scores, and calibration assumptions.