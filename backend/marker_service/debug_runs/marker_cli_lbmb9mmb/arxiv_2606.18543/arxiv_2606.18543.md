# **CEO-BENC H: Can Agents Play the Long Game?**

Haozhe Chen Karthik Narasimhan Zhuang Liu Princeton University

<span id="page-0-0"></span>![](_page_0_Figure_3.jpeg)

**Figure 1. CEO-BENC H evaluates general long-horizon agent capabilities by simulating a startup over 500 days in a realistic and challenging environment.** The agent operates through a programmable interface with access to business databases, company management tools, and social media. Outcomes are driven by a partially observable, noisy, and evolving market with delayed and coupled consequences.

## **Abstract**

Language model agents are becoming proficient executors at isolated, short-horizon tasks such as software engineering and customer service. Yet real-world challenges require a combination of sophisticated skills that remain largely untested in agents: (1) navigating long horizons amid uncertainty; (2) acquiring information in noisy environments; (3) adapting to a changing world; (4) orchestrating multiple moving parts toward a coherent goal. We introduce CEO-BENCH, which evaluates these capabilities together by simulating a representative real-world task: operating a startup for 500 days. An agent manages pricing, marketing, budgeting, and many other aspects of a fictional company through a programmable Python interface, operating in the same environment and facing the same challenges as a human CEO. Success demands analyzing noisy, interconnected business databases, translating signals into sound strategy, and coordinating many decisions with programming. The strongest agents write sophisticated code that simulates customer cohorts to forecast future cash and mines negotiation history to uncover hidden customer preferences. Even so, most state-of-the-art models struggle in this environment. Only Claude Opus 4.8 and GPT-5.5 finish above the \$1M starting balance, and neither consistently turns a profit. CEO-BENC H takes a first step toward measuring the intelligence required to drive sustained, adaptive progress over time.

<span id="page-1-0"></span>![](_page_1_Figure_0.jpeg)

**Figure 2. Cash on hand over time for each model's best run**. Most state-of-the-art models struggle to complete the simulation without bankruptcy. Only Claude Opus 4.8 and GPT-5.5 grow cash above the \$1M starting balance for their best runs. Current models still struggle to combine long-horizon planning, noisy information gathering, adaptation, and coordinated execution over time.

### 1 Introduction

Language model agents are becoming increasingly capable at short-horizon tasks. They can fix a GitHub issue (Jimenez et al., 2024), follow a service policy in dialogue (Yao et al., 2025), or complete a web workflow (Zhou et al., 2024). These are real skills, but they share a simple shape: the agent gets a clear goal, acts for a short time, and receives feedback quickly. As agents approach reliable execution of such individual tasks, a natural next question is what we should expect them to do after the local task is no longer the bottleneck.

Human intelligence goes beyond local execution (Newell and Simon, 1972; Simon, 1955). Many consequential human achievements are not single well-specified tasks, but long chains of decisions made under uncertainty: choosing what to prioritize, allocating limited resources, interpreting noisy signals, and adapting as conditions change (Simon, 1955; March, 1991; Teece et al., 1997). Future agents will need the same kind of sustained strategic control if they are to move beyond task completion and operate effectively in the real world.

Early agent evaluations such as SWE-bench (Jimenez et al., 2024), WebArena (Zhou et al., 2024), and  $\tau$ -bench (Yao et al., 2025) evaluate real-world skills, but they are scoped to short episodes with quickly observed outcomes. GDPval (Patwardhan et al., 2025) broadens evaluation to economically valuable work, but remains a one-shot deliverable rather than a persistent process. Agentic-memory benchmarks test agents' ability to use information over time, but they primarily measure storage and retrieval skills (Hu et al., 2026; He et al., 2026b). Vending-Bench (Backlund and Petersson, 2025a;b) and Accounting-Bench (Penrose AI, 2025) take a first step toward evaluating agents in long-horizon simulated environments. Yet these settings involve a narrow set of decisions and largely stable environments. They do not test whether agents can coordinate many interdependent actions, acquire information from noisy feedback, and devise strategy amid delayed consequences and changing conditions.

The next stage of agent evaluation calls for a shift toward settings where actions accumulate over long horizons; environment state is only observable through indirect evidence; feedback is noisy and delayed; and conditions continue to change. Success depends on more than individual capabilities. Agents must integrate them into coherent behavior, make long-horizon plans, turn accumulated evidence into actionable signals, coordinate interdependent decisions, and continuously adapt strategy as new information arrives.

CEO-BENCH instantiates this challenge in a realistic, large-scale startup simulation, where an agent runs a company for 500 days through a programmable Python interface with 34 tools and a 19-table business database. We show the structure of CEO-BENCH in Fig. 1. Beyond issuing individual tool calls, the agent writes and executes code, querying the database with SQL to analyze the company's state and composing the available tools into custom workflows. It thus operates in the same environment and faces the same challenges

<span id="page-2-1"></span>![](_page_2_Figure_0.jpeg)

**Figure 3. Cash on hand over time for each of the three runs per model.** We show all experiments for each model to describe full behavior patterns. We also release all agent action trajectories in an interactive trajectory viewer.

as a human running the company, and the task demands coding and data-analysis skill together with strategic thinking. As shown in Fig. 4, the agent must coordinate diverse operating decisions across pricing, growth, product, operations, communication, enterprise sales, and more. Decisions play out over realistic business timelines: revenue arrives on billing cycles, R&D takes days to weeks, and mistakes surface later through churn and reputation, forcing long-horizon reasoning under uncertainty. Much of the state is hidden, so the agent must infer customer satisfaction, willingness to pay, and shifting preferences from noisy signals in data analytics and social media. At the same time, we design the environment to keep changing as a result of customer preference drift, macroeconomic cycles, and competitor shocks. Success requires continually revising strategy in response to these shifting conditions while maintaining coherent decisions across the business.

Our evaluation shows that this challenge remains difficult for agents built on current state-of-the-art models. We show in Fig. 2 that while most agents can produce valid tool calls and analytics queries, they struggle to sustain coherent strategy over time and often bankrupt before completing the simulation. Only Claude Opus 4.8 and GPT-5.5 finish above the \$1M starting balance and the non-LLM rule-based baseline. We show in Fig. 3 that even these two models fail to consistently profit across experiments.

Our analysis shows that performance correlates with core capabilities targeted by CEO-BENCH: inferring hidden structure from noisy data, forecasting delayed consequences, and adapting to competitive pressure. By inspecting agent action trajectories, we find distinctive behavior patterns across models. For example, GPT-5.5 and Claude Opus 4.8 actively explores various strategies, while Claude Opus 4.7

<span id="page-2-0"></span>![](_page_2_Figure_5.jpeg)

Figure 4. Running a startup requires coordinating many moving parts, making it a fitting choice as a canonical task evaluating agent's skills to steer complex decisions across long-horizon.

<span id="page-3-0"></span>

| Category                       | Actions                                                                                                                          | Example tools                                                         |  |
|--------------------------------|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|--|
| Database query                 | Query 19 business SQL databases and conduct data<br>analytics                                                                    | query                                                                 |  |
| Monetization                   | Set prices, usage quotas, discounts, and in-product ads                                                                          | pricing.set_prices,<br>pricing.set_usage_quotas                       |  |
| Growth and market<br>expansion | Allocate targeted advertising spend and promotion<br>across channels and customer groups                                         | marketing.set_targeted_ad_spend,<br>marketing.set_lead_promotion      |  |
| Product quality and<br>R&D     | Choose model tiers, fund day-to-day development, and<br>launch research projects                                                 | pricing.set_model_tiers,<br>research.start_research_project           |  |
| Reliability                    | Buy infrastructure capacity and fund customer support                                                                            | infrastructure.set_capacity_tier,<br>analytics.set_targeted_ops_spend |  |
| Enterprise sales               | Conduct multi-turn negotiations over price and plan<br>with enterprise prospects and renewals                                    | enterprise.send_enterprise_deal,<br>enterprise.reject_enterprise_deal |  |
| Information<br>acquisition     | Pay for market research to discover new customer<br>groups and learn more about existing groups                                  | market.research_market,<br>market.research_group                      |  |
| Public communication           | Monitor social media for customer complaints,<br>competitor news, and economic trends, then post or<br>reply to influence growth | marketing.post_social_media,<br>analytics.get_social_posts            |  |

**Table 1. Agent action space** categories and example tools in CEO-BENC H. These tools enable agents to design diverse operation strategies but also pose challenges on coordinating many actions toward one coherent goal.

limits itself to a passive cash-preservation strategy. Claude Opus 4.8 reaches more customers initially and drop to zero customer mid simulation, while GPT-5.5 maintains consistent customer base throughout. These results show that CEO-BENC H *exposes fine-grained behavioral patterns* that remain invisible to existing evaluations, while *revealing substantial headroom in models' ability* to integrate individual capabilities into coherent, adaptive behavior over extended horizons.

# **2 Designing CEO-BENCH**

In this section, we provide an overview of how the CEO-BENCH simulator works. Then, we describe how we design the action interface to make the task open-ended. Finally, we detail world mechanics design considerations that make the task challenging and realistic.

## **2.1 How CEO-BENCH Works**

In CEO-BENC H, an agent runs a fictional subscription-software company called *NovaMind* for 500 simulated days. It begins on day one with zero customers and \$1M in cash and is graded on cash on hand at the end. If cash ever falls strictly below zero, bankruptcy ends the simulation. We provide an overview of the simulator mechanics in this section and include full details in Appendix [A.](#page-19-0)

**What an agent can do.** For each simulated week, the agent can take actions for unlimited turns across 34 tools in the categories displayed in Table [1.](#page-3-0) These categories cover pricing and plan design, growth and market expansion, product quality and research, reliability and support, information acquisition, public communication, and enterprise sales. Each tool accepts fine-grained structured arguments, so agents can compose a large space of possible policies. Section [2.3](#page-6-0) explains the tool interface design in more detail.

**How an agent makes and loses money.** An agent makes profits through customer subscription payments and in-product ad monetization. We abstract the company product that customers subscribe to as a numerical product quality. Higher product quality results in more product subscriptions and payments, but maintaining quality via development, research, infrastructure capacity, support, and model tier choices requires spending. Acquiring customers through advertising channels also costs money. Cash therefore changes through both immediate costs and delayed revenue effects. We show the calculation of cash change between each day and decompose each contributing factor in Equation [1.](#page-4-0) We fully explain the role and mechanism of each factor in

Appendix A.3, A.4 and A.8.

<span id="page-4-0"></span>
$$\underbrace{B_{t+1} - B_t}_{\text{daily cash change}} = \underbrace{Y_t^{\text{sub}}}_{\text{the subscription payments}} + \underbrace{\sum_{i} Y_{i,t}^{\text{ads}}}_{\text{capacity}} - \underbrace{K_{\kappa_t}^{\text{capacity}}}_{\text{capacity}} - \underbrace{\sum_{p} \chi_{p}^{\text{usage}} U_{p,t}^{\text{use}}}_{\text{usage compute}} - \underbrace{X_t^{\text{ops}}}_{\text{support}} - \underbrace{X_t^{\text{dev}}}_{\text{spending}} - \underbrace{X_t^{\text{dev}}}_{\text{cost}} - \underbrace{X_t^{\text{dev}}}_{\text{capacity}} - \underbrace{\sum_{i} \chi_{p}^{\text{capacity}}}_{\text{capacity}} - \underbrace{\sum_{i} \chi_{p}^{\text{usage}} C_{p,t}^{\text{usage}}}_{\text{cost}} - \underbrace{X_t^{\text{ops}}}_{\text{spending}} - \underbrace{X_t^{\text{dev}}}_{\text{spending}} - \underbrace{X_t^{\text{group}}}_{\text{research}} - \underbrace{K_t^{\text{group}}}_{\text{research}} - \underbrace{K_t^{\text{project}}}_{\text{research}} - \underbrace{K_t^{\text{project}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{\text{group}} - \underbrace{K_t^{\text{group}}}_{\text{projects}} - \underbrace{K_t^{\text{group}}}_{$$

Modeling customers and indirect feedback. There are 26 customer groups in the simulator. Each customer group consists of a distribution of hidden price and quality preferences, such as a maximum willingness to pay and a minimum accepted quality at each price. Each customer is created by sampling its unique preference parameters from a group distribution. At a subscription plan's price, a customer subscribes if the offered product quality exceeds the customer's minimum accepted quality. The customer may switch plans if another plan gives a better quality surplus and may cancel if no plan remains acceptable. We show the mathematical definition of a customer's price-quality preference curve in Equation 5. We describe full details of each factor in Appendix A, Subsection A.2. Example curve plots appear in Fig. 16. Customer satisfaction changes company reputation, and reputation affects the new customer acquisition rate. The agent does not directly observe satisfaction, willingness to pay, or quality thresholds. It instead infers feedback by analyzing subscription, churn, support, revenue, and reputation data and by monitoring simulated social media.

Customer acquisition and enterprise negotiation. Agents acquire new customers by spending on advertising channels. Each customer group reacts differently to each ad channel, so the same spend can produce different acquisition rates across groups. Reputation, social media reactions, market saturation, demand surges, and macroeconomic conditions also affect acquisition speed. We show the calculation of expected new prospective customers for group g on day t in Equation 2. We describe full details of each factor in Appendix A.5 and A.6. We sample daily from a Poisson distribution parameterized by this expectation. Market research can reveal additional customer groups and improve what the agent knows about known groups. Enterprise customers follow the same price and quality logic, but deals are negotiated through offers, counter-offers, reply delays, and possible rejection.

<span id="page-4-1"></span>
$$\underbrace{\mathbb{E}\left[n_{g,t}^{\text{prospect}}\right]}_{\text{expected new prospective customers for group }g} = \underbrace{R_{g,t}}_{\text{reputation in group }g} \cdot \underbrace{D_{g,t}}_{\text{order of group }g} \cdot \underbrace{C_{t}}_{\text{calendar macro econ cycle}} \cdot \underbrace{M_{g,t}}_{\text{social media reaction}} \cdot \underbrace{Z_{t}}_{\text{demand surge}} \cdot \underbrace{\left(\sum_{c} \frac{x_{c,g,t} L_{c,g,t}}{x_{ad}} + \sum_{h} N_{h,t} W_{h,g}^{\text{net}}\right)}_{\text{networking effect from each group}}\right)}_{\text{networking effect from each group}}$$

**Product quality and competitor pressure.** Product quality is affected by daily development, research projects, model tier choices, targeted development, infrastructure capacity, support spending, usage quotas, and in-app ad strength. These controls shape customer experience through base product quality, quota saturation, system outages, support delays, relationship history, and ad load. Competitors add pressure by periodically raising customer quality expectations. Broad product development and research can make competitors catch up faster, while targeted development for specific groups is harder to copy and lets competitors catch up more slowly. We show the computation of a customer's perceived product quality and breakdown of each

<span id="page-5-2"></span>![](_page_5_Figure_0.jpeg)

Figure 5. Major design principles behind CEO-BENCH's world mechanics and example designs that follow the principles.

factor in Equation 3. We describe full details of each factor in Appendix A.3, A.4, and A.6.

<span id="page-5-0"></span>
$$Q_{i,t}^{\text{perc}} = m_p \left( q_0 + b_t^{\text{shared}} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= m_p \left( q_0 + b_t^{\text{shared}} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_{\text{out}} 1 \{ \text{outage}_t \}$$

$$= model-tier effect \left( \text{initial quality dev improvement} + b_{g,t}^{\text{group}} \right) - \beta_0 o_t - \beta_0 o_t - \beta_0 o_t - \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta_0 o_t + \beta$$

Changing world imposes challenges. The world evolves over time through macroeconomic trends, interconnected reputation propagation, market saturation, demand surges, and competitor pressure. These factors affect acquisition, retention, and enterprise deal outcomes. The challenge is that the agent observes only partial and delayed evidence of these changes. It must infer hidden customer and market conditions from traces, choose actions whose effects arrive on different time scales, and revise its policy as the company and market move. Section 2.3 explains the interface design, and Section 2.2 describes the design principles that make the simulator mechanics realistic and challenging.

## <span id="page-5-1"></span>2.2 How We Make CEO-BENCH Rigorous and Challenging

We design CEO-BENCH's world mechanics to be an expressive emulation of the real world, while remaining mechanistic so that success depends on genuine skills rather than exploiting brittle simulations. We describe seven core principles in our world mechanics design below and illustrate four examples in Fig. 5.

Maximize realism with granular simulation. The simulator models 26 customer groups and individual customers within each group rather than only aggregate demand. Each customer has its own acquisition path, subscription state, price exposure, usage, satisfaction, and cancellation trajectory. Customers are also organized into diverse groups with different needs, budgets, price sensitivities, ad channel effectiveness, support expectations, and behavioral patterns. This granularity increases the complexity of world dynamics and widens the set of viable strategies.

**Robust simulation with mechanistic rules.** The world emulates real business behavior while maintaining stable cause-and-effect relationships. Almost all simulator outcomes are generated by explicit mechanisms rather than by using an LLM as an opaque judge. For example, customers decide whether to subscribe by comparing product value against price through a microeconomics-motivated participation rule (Mussa and Rosen, 1978). This design aims to avoid failure modes in benchmarks such as Vending-Bench (Backlund and

<span id="page-6-1"></span>

| Distribution | Example use in simulator                    | Motivation                    |
|--------------|---------------------------------------------|-------------------------------|
| Normal       | R&D project quality gain                    | Captures uncertain payoff     |
| Poisson      | Daily new prospective customers for a group | Models rate-based counts      |
| Bernoulli    | Involuntary cancellation event              | Models binary shocks          |
| Uniform      | Reputation damage noise                     | Adds bounded uncertainty      |
| Log-normal   | Competitor quality-jump magnitude           | Models skewed positive shocks |

**Table 2. Stochastic mechanisms in CEO-BEN CH.** The simulator uses a variety of stochastic variables to model realworld uncertainties.

[Petersson,](#page-15-1) [2025a;](#page-15-1)[b\)](#page-15-2), where an LLM-simulated supplier can reward agent's unrealistic verbal promises.

**Consistent simulation under stochasticity.** While we inject stochasticity into world dynamics to emulate real-world noise, we maintain consistency across runs with independent random number generators for different simulator components. For example, under the same random seed, after calling the market research tool multiple times, the agent always discovers the same sequence of new market groups, independent of actions in other areas.

**Hidden information and indirect feedback.** CEO-BENC H tests whether agents can gather information in a partially observable world. The agent receives only information that a real start-up manager could plausibly observe: dashboards, database records, social-media posts, research reports, and negotiation history. It does not observe true customer satisfaction, latent willingness to pay, churn propensity, competitor schedules, or demand parameters. Instead, it must infer these hidden variables indirectly, for example, by gauging customer satisfaction and complaints through social media or detecting competitor moves by analyzing cancellation behavior.

**Interconnected world dynamics.** We design the simulated world to make it difficult to isolate a single causal relationship and hill-climb on it. Every decision can influence many other parts of the market. For example, reputation propagates across related groups, so a quality failure in one enterprise group can spill into nearby groups and eventually affect consumer demand. Increasing satisfaction of influential customer groups can boost growth more effectively than ads.

**Delayed and uncertain consequences.** Many actions have delayed and uncertain effects, forcing longhorizon decision making under uncertainty. Costs may appear immediately, while the corresponding revenue, retention, research, or reputation effects arrive weeks later. R&D projects have stochastic completion timelines and quality improvements, so investing more does not deterministically produce an immediate gain. Enterprise negotiations also unfold over stochastic delays, making it costly to wait too long but risky to overreact to any single turn. We show the types of distributions used and example usage in Table [2.](#page-6-1)

**Non-stationary environment.** Agents must continually gather new information and adapt because the environment changes over the course of a simulation. Competitors place adaptive pressure on product quality. Customer behavior also drifts over time, with different groups shifting at different rates in price sensitivity and quality expectations. Macroeconomic trends add another changing background process, affecting willingness to pay and enterprise seat counts across expansions and contractions.

## <span id="page-6-0"></span>**2.3 A Versatile Action Interface Between World and Agent**

We design a programmable tool interface, so agents can effectively manage granular action spaces and organize them into custom workflows.

**Composable action interface in Python.** Terminal-based computer-use agents have become a general form factor across tasks [\(Anthropic,](#page-15-3) [2026;](#page-15-3) [OpenAI,](#page-17-4) [2026;](#page-17-4) [OpenCode,](#page-17-5) [2026;](#page-17-5) [Pi Contributors,](#page-17-6) [2026\)](#page-17-6). We make evaluating CEO-BENCH easy with any of these agents by exposing the action surface to the agent via a Python package, novamind\_api. An agent manages the company by calling functions in novamind\_api in a Python script and executing the script in its terminal. This design maximizes flexibility for an agent to build

#### <span id="page-7-0"></span>Database enables realistic analytics workflow

Example. Agent analyzes financials through SQL queries.

#### Granular action space widens possibilities

Example 1. Allocate ad spend by channel and customer segment.

#### Composable tools allow sophisticated workflows

Example. Agent connects database records directly to promotion decisions.

```
analytics.py
cash = query("""
    SELECT SUM(amount) AS cash
    FROM ledger
""")
# recurring revenue from active
mrr = query("""
    SELECT SUM(seat_count
      * effective_price) AS mrr
    FROM subscriptions
    WHERE status = 'subscribed'
""")
print(f"cash={cash}")
print(f"mrr ={mrr}")
cash=−$33,970
mrr =$847,294/mo
                                               ad_spend.py
                                     marketing.set_targeted_ad_spend(
                                       targeted_spend={
                                         "social_media": {"S1": 120},
                                         "linkedin": {"S3": 100},
                                       })
                                    Example 2. Direct ops spend at
                                    specific at-risk customers.
                                               ops_spend.py
                                     at_risk = [
                                       4821, 5103, 5277,
                                       5394, 5612, 5901,
                                     ]
                                     ops_spend.set_targeted_ops_spend(
                                       by_customer={
                                         cid: 150 for cid in at_risk
                                       })
                                                                                    retention.py
                                                                          rows = query("""
                                                                            SELECT s.customer_id, s.effective_price
                                                                            FROM subscriptions s
                                                                            JOIN customers c USING(customer_id)
                                                                            WHERE c.group_id='S3' AND s.plan='B'
                                                                              AND s.effective_price > 79
                                                                          """)["rows"]
                                                                          avg = sum(r["effective_price"] for r in rows) /
                                                                          len(rows)
                                                                          promos = {str(r["customer_id"]):
                                                                          round((r["effective_price"] - avg) * 0.4) for r in
                                                                          rows}
                                                                          pricing.set_promotion(by_customer=promos)
                                                                          print(f"{len(promos)} subs, total
                                                                          {sum(promos.values()):,}/mo")
                                                                           134 subs, total $1,847/mo
```

**Figure 6. Agents interact with CEO-BENC H through a versatile Python interface.** Left: We give the agent access to diverse business databases to test its information acquisition capability through a realistic data analytics workflow. Middle: We widen agents' opportunity space by enabling them to take fine-grained actions. Right: This interface design allows the agent to compose tools into sophisticated custom workflows.

its own infrastructure on top of the API. In Fig. [6](#page-7-0) (right), we show an example where, rather than calling a tool once per customer, an agent connects to the database via its custom data-driven promotion management system and applies promotion decisions efficiently at scale.

**Granular action spaces.** We allow agents to act at fine granularity to create a rich space of strategic tradeoffs, failure modes, and opportunities for adaptation. Although the interface contains a finite set of tools, each tool accepts fine-grained structured arguments, so agents can compose a combinatorially large space of possible actions. In Fig. [6](#page-7-0) (middle), we show examples where the agent allocates advertising spend by (ad channel, customer group) pair and decides operations spending on individual customers.

**Large-scale and realistic databases.** We give the agent access to a 19-table operational database covering orders, contracts, subscriptions, the cash ledger, the social-media feed, configuration history, ad-channel attribution, and support tickets, among others. The schema mirrors what a real software company's analytics stack would expose, testing the agent's capability to gather information via an analytics workflow that resembles real-world software company operations. In Fig. [6](#page-7-0) (left), we show an example where the agent analyzes its revenue through database queries.

**Social media.** The agent can read a simulated public feed of customer complaints, competitor announcements, and macroeconomic trends. Agents can also reply and post on social media. Reactions to the agent's posts on social media can also influence the rate of new customer acquisition. We test the agent's capability to both perceive and act in a chaotic natural-language domain.

## **3 Experiments and Results**

In this section, we describe our experiments and their results. We then conduct both qualitative and quantitative analysis to compare behaviors across models.

<span id="page-8-0"></span>

| Model                            | Bankruptcy | Max final<br>cash (\$) | Max survival<br>days | $\begin{array}{c} \textbf{Mean survival} \\ \textbf{days} \pm \textbf{std} \end{array}$ | Turns<br>/week | Best run<br>API cost |
|----------------------------------|------------|------------------------|----------------------|-----------------------------------------------------------------------------------------|----------------|----------------------|
| Claude Opus 4.8                  | 0          | 27,776,973             | 500                  | $500.0 \pm 0.0$                                                                         | 10.8           | \$213.41             |
| GPT-5.5                          | 2          | 21,297,707             | 500                  | $333.7 \pm 229.7$                                                                       | 34.7           | \$200.49             |
| Claude Opus 4.7                  | 0          | 389,959                | 500                  | $500.0 \pm 0.0$                                                                         | 14.6           | \$128.72             |
| Kimi K2.6                        | 1          | 98,050                 | 500                  | $343.0 \pm 110.0$                                                                       | 30.5           | _                    |
| Claude Sonnet 4.6                | 2          | 69,766                 | 500                  | $282.3 \pm 136.0$                                                                       | 13.3           | \$82.84              |
| GLM 5.1                          | 3          | 0                      | 324                  | $214.7 \pm 91.1$                                                                        | 51.5           | _                    |
| Claude Haiku 4.5                 | 3          | 0                      | 231                  | $144.7 \pm 70.5$                                                                        | 23.1           | \$6.68               |
| Gemini 3 Flash                   | 3          | 0                      | 226                  | $154.0 \pm 37.0$                                                                        | 18.5           | \$2.98               |
| DeepSeek V4 Pro                  | 3          | 0                      | 176                  | $114.3 \pm 38.6$                                                                        | 19.3           | _                    |
| Grok 4.20                        | 3          | 0                      | 37                   | $28.3 \pm 8.5$                                                                          | 8.2            | \$0.75               |
| Rule-based baseline              | _          | 15,756,408.06          | 500                  | _                                                                                       | _              |                      |
| Estimated final cash upper bound | _          | 2,200,000,000          | _                    | _                                                                                       | _              | -                    |

**Table 3. Benchmark results summary.** Most models fail to avoid bankruptcy, while Claude Opus 4.8 and GPT-5.5 finish above the initial \$1,000,000 cash balance. The best model performance falls short of the estimated upper bound of attainable final cash by a large margin. CEO-BENCH presents a challenging task for existing models.

### 3.1 Experimental Setup

**Models.** We evaluate agents on the full 500-day CEO-BENCH simulation. Each model is given \$1M starting cash. We run three simulations for each model with random seed 42. We evaluate closed-weight models (GPT-5.5 xhigh, Claude Opus 4.8 max, Claude Opus 4.7 max, Claude Sonnet 4.6 max, Claude Haiku 4.5 thinking, Gemini 3 Flash Preview high, and Grok 4.20 Reasoning) and self-hosted open-weight models (DeepSeek-V4-Pro reasoning, GLM-5.1 reasoning, and Kimi-K2.6 reasoning).

Harness. Terminal-based computer-use agents have become a general interface for automation: systems such as Claude Code, Codex, OpenCode, and Pi can perform diverse tasks and maintain memory by interacting with a terminal (Anthropic, 2026; OpenAI, 2026; OpenCode, 2026; Pi Contributors, 2026). We design CEO-BENCH to be compatible with any such agent. To align the harness across all models, we implement a minimal terminal agent interface: we give each agent a Linux working directory and tools including bash, read-file, and edit-file. In early runs, we found that open-source harnesses such as OpenCode and Pi (pi-mono) did not manage context reliably enough for 500-day episodes, so our harness refreshes context by clearing action history and only keeping system prompt and an agent-editable memory file in context at the start of each simulated week.

**Result selection for analysis.** For results and analysis, we select the best run for each model as follows: (1) if at least one of the three runs avoids bankruptcy, we choose the run with maximum ending cash; (2) if all runs end in bankruptcy, we choose the run with the maximum number of simulation days before bankruptcy.

#### <span id="page-8-1"></span>3.2 Results Overview

**Overall results.** We show the best-run cash over time for each model in Fig. 2, and per-model trajectories across all three runs in Fig. 3. We also show additional details in Table 3. Most state-of-the-art models struggle to complete the simulation without bankruptcy. While five models (Claude Opus 4.8, GPT-5.5, Claude Opus 4.7, Kimi K2.6, and Claude Sonnet 4.6) end with positive cash on their best run, only Claude Opus 4.8 and GPT-5.5 finish above their \$1M starting balance. This preliminary evaluation shows that Claude Opus 4.8 and GPT-5.5 demonstrate high-upside strategic behavior; Claude Opus 4.7 survives more conservatively; and most models fail to coordinate growth, quality, and cash flow.

**Rule-based baseline.** We include a simple rule-based heuristic baseline that uses no language-model calls during policy execution: it fixes prices, quotas, and model tiers, concentrates acquisition and targeted development on a small set of customer groups, and adjusts capacity from recent usage. We conduct a preliminary grid search over this rule template and display the best strategy in Fig. 2 and Table 3. The heuristic achieves a significant positive cash balance of \$15.76M, with Claude Opus 4.8 and GPT-5.5 exceeding it. We show full details of this baseline strategy's design and configuration search in Appendix B.

Benchmark is far from saturated. We estimate loosely the upper bound of achievable final cash be around

#### <span id="page-9-0"></span>(a) Claude Opus 4.8 memo examples

![](_page_9_Figure_1.jpeg)

**Figure 7. Example memos written by Claude Opus 4.8 (top), GPT-5.5 (middle), and Claude Opus 4.7 (bottom) in their workspaces during the best trajectory of each model.** Claude Opus 4.8 and GPT-5.5 actively explores and adjusts across diverse strategies, while Claude Opus 4.7 largely confines its decisions to a single strategic direction.

\$2.2B. The estimation sums revenue from all 26 customer groups under maximum supportable pricing and subtracts the required costs for compute, capacity, development, operations, advertising, research, and acquisition. To obtain a conservative estimate, we further adjust downward for execution frictions, including issue-driven churn, enterprise negotiation friction, and acquisition delays. The resulting estimate remains far above the best observed model performance, indicating that CEO-BENC H is far from saturated. We detail our estimation process in Appendix [D.](#page-30-0) We release agent trajectories of all our experiments in an [interactive](https://ceobench.com/trajectory-viewer/) [trajectory viewer.](https://ceobench.com/trajectory-viewer/)

## **3.3 A Look into Agent Behaviors**

In this section, we take a preliminary exploration in agent behaviors and compare them across models.

**Strong models explore wider strategy space.** In Fig. [7,](#page-9-0) we show example memos written by agents over time. GPT-5.5 and Claude Opus 4.8 adapts frequently as conditions change, trying a range of strategies such as scaling acquisition, adjusting model tiers, modifying promotions, and reallocating support or development spend. In contrast, Claude Opus 4.7 tends to respond to setbacks by repeatedly cutting spend and preserving

```
(a) Claude Opus 4.8 · Simulating growth scenarios into the
        future · Day 77
D0=77; START_CASH=1269489
S1_TOUCHED0=159258+54467+987
RAW=[(0,19,15),(5,22,1830),(8,26,20562), ⋯ active cohorts ]
def build_cohorts():
 cohorts=[]
   ⋯ expand observed signup weeks into renewal cohorts
 return cohorts
def simulate(cap=450000,conv=.72,first=.13,ongoing=.04):
 cohorts=build_cohorts(); touched=S1_TOUCHED0; cash=START_CASH
 REMAIN0=cap-S1_TOUCHED0
 targets={84:'1wk',105:'4wk',161:'12wk',259:'26wk'}; results={}
 for step in range(1,183):
   day=D0+step; active=sum(c[1] for c in cohorts)
   pen=max(0.02,(cap-touched)/max(1,REMAIN0))
   ad_spend=85000 if step =7 else (120000 if step =77 else 90000)
   leads=4.25*(ad_spend**0.71)*pen + 0.0132*active*pen
   new=leads*conv; touched+=leads; cohorts.append([26.0,new])
   cash += new*15.0 - (ad_spend + leads*0.5 + active*0.15 + 58500)
    ⋯ apply re-bills/churn; record target days
 return results
scen={'DISAST':(260000,.62,.25,.08),'PESS':(320000,.68,.18,.06), ⋯
 scen 1wk M/k 4wk M/k
 DISAST .69/182 .07/152
 PESS .99/202 .54/204
 BASE 1.23/216 1.53/291
 OPT 1.40/225 2.81/397
                                 scen 12wk M/k 26wk M/k
                                 DISAST -4.58/131 -8.39/102
                                 PESS -1.97/183 -1.91/158
                                 BASE 2.79/273 8.99/248
                                 OPT 10.74/462 29.96/433
```

```
(b) GPT-5.5 · Infer latent customer attributes from noisy
        negotiation outcomes · Day 133
rows=nm.query("""select et.customer_id,c.group_id,et.offer_json,s.st
 ⋯ 40+ lines suppressed
def parse_prices(o):
  try: d=json.loads(o)
  except: return []
  return [(x.get('plan'),x.get('price',x.get('price_per_seat',x.get(
last={}; [last.setdefault(r['customer_id'],r) for r in rows]
for gid in set(r['group_id'] for r in last.values()):
 lr=[r for r in last.values() if r['group_id'] =gid]
  for plan in ['A','B','C']:
   by_status=collections.defaultdict(list)
    for r in lr:
      for p,v in parse_prices(r['offer_json']):
       if p =plan and v is not None: by_status[r['status']].append(
    if by_status:
      print(gid,plan,{s:(len(v),round(statistics.mean(v),2)) for s,v
 ⋯ 20+ lines suppressed
 Active enterprise accepted price distribution
 {'group_id':'E3','plan':'B','n':154,'seats':167595,'minp':1.69,'av
 {'group_id':'E3','plan':'C','n':3,'seats':3341,'minp':25.0,'avgp':
 Enterprise lost by latest agent offer and day groups summary
 GID D_E02 n 413 statuses Counter({'lost':403,'lead':10})
   B all avg 40.19 min 39.0 max 49.0 by_status {'lost':(403,40.22,3
   C all avg 61.15 min 59.0 max 79.0 by_status {'lost':(403,61.21,5
  ⋯ 40+ lines suppressed
```

**Figure 8. Example code files written by top-performing agents during their best trajectories.** (a) The Claude Opus 4.8 agent runs its own simulation to forecast cash under different scenarios. (b) The GPT-5.5 agent infers latent enterprisecustomer price and quality preferences by mining noisy negotiation outcomes.

cash, which may help it survive until the final days but limits it from making positive profits. In Fig. [11,](#page-12-0) we find that Claude Opus 4.8 and GPT-5.5 distribute actions more evenly across tools than Claude Opus 4.7.

**Agents attain similar final cash through distinct strategies.** Claude Opus 4.8 and GPT-5.5 in their best runs attain similar final cash balance. However, they attain this result via distinct strategies. In Fig. [9,](#page-11-0) we show their very different customer base change over time. Claude Opus 4.8 drops to zero customers mid-simulation, while GPT-5.5 sustains customers throughout the simulation, and the two agents focus on different customer groups. Fig. [7](#page-9-0) also show that Claude Opus 4.8 decides to pivot to harvesting mode mid simulation and proceeds with expense cut and passive strategy maintaining.

**Sophisticated analytics by top-performing agents.** In Fig. [8,](#page-10-0) we show example code files that top-performing agents write and execute. In (a), Claude Opus 4.8 constructs a cohort-based simulation to forecast future cash under different scenarios. In (b), GPT-5.5 mines negotiation history in the database to uncover hidden customer preferences. These examples demonstrate initial signs of sophisticated planning and information acquisition.

## **3.4 Measuring Drivers of Success and Failure**

While success in CEO-BENC H requires multiple skills to work together, we conduct a preliminary analysis by isolating four skills and comparing them against agent performance. We compare quantitative measures of each skill for the top-performing models, against the average over all remaining models in Fig. [12,](#page-12-1) and explain each comparison further below.

<span id="page-11-0"></span>![](_page_11_Figure_0.jpeg)

**Figure 9. Number of customers by customer group over time for the best runs of Claude Opus 4.8 and GPT-5.5.** While Claude Opus 4.8 obtains more customers initially and drop to zero customer mid-simulation, GPT-5.5 sustains consistent customer base throughout. The two agents also focus on different customer groups. The two agents attain similar final cash balance via distinct strategy styles. Discoverable customer groups are initially hidden to agent and can only be discovered through paid market research.

**Uncovering hidden information.** In CEO-BENC H, each pair of ad channel and customer group has a different new-customer acquisition rate, emulating real-world heterogeneity. The acquisition rate is hidden from the agent, so the agent must uncover and use this information by analyzing customer acquisition history in databases. In Fig. [12a,](#page-12-2) we measure the average percentage of ad spending allocated to the best channel out of all ad spending for a customer group. We find that Claude Opus 4.8 and GPT-5.5 attain higher allocation efficiency than the remaining models. With five ad channels, the

<span id="page-11-1"></span>![](_page_11_Figure_3.jpeg)

**Figure 10. Targeted development spending breakdown.** GPT-5.5 and Claude Opus 4.8 direct much larger shares of development spending toward fine-grained group-specific improvements than most other models.

random-guessing baseline is 20%, and most models fall below that baseline.

**Seeing into the future.** In each simulated week, we ask the agent to submit a cash forecast four weeks into the future. Fig. [12b](#page-12-2) plots the percentage error between the submitted forecast and the realized cash balance four weeks later against the number of days before bankruptcy. We average data from the first four simulation weeks, when most models are still alive. We find that, on average, Claude Opus 4.8 has the lowest early forecast error, and the stronger models forecast with less error than the remaining models, demonstrating that they better understand the impact of their actions on the world.

**Speed of adaptation to environmental change.** We measure adaptation speed with the time until the first occurrence of the word "competitor" in the agent's workspace after the first competitor quality improvement. We show in Fig. [12c](#page-12-2) that, on average, Claude Opus 4.8, GPT-5.5, and Opus 4.7 detect environmental changes through indirect social media and database information faster than other models.

**Planning.** We find that the stronger runs frequently anticipate different future scenarios and build corresponding solutions in their memos, with examples shown in Fig. [13.](#page-13-0) We show in Fig. [12d](#page-12-2) that Claude Opus 4.8 and GPT-5.5 use the word "if" more frequently than other models.

**Taking fine-grained actions.** Our simulator allows agents to take actions at a fine-grained level. For example, agents can decide customer-group specific product development strategy. Proper analysis of customer group information and targeted development would result in advantages such as lower competitor pressure. Fig. [10](#page-11-1)

<span id="page-12-0"></span>![](_page_12_Figure_0.jpeg)

**Figure 11. Average per-week tool usage frequency for the best runs of Claude Opus 4.8, GPT-5.5, and Claude Opus 4.7 (top 10 tools per model).** GPT-5.5 and Claude Opus 4.8 distribute actions more evenly across tools.

<span id="page-12-1"></span>![](_page_12_Figure_2.jpeg)

**Figure 12. Better-performing models excel along four skill axes**: (a) uncovering hidden ad-channel effectiveness and allocating spend to the best channel, (b) forecasting future cash, (c) reacting quickly to competitor events, and (d) planning more extensively. We show mean and standard deviation of each measurement in plots above.

<span id="page-12-2"></span>shows the dollar-weighted split between targeted and non-targeted development spending. GPT-5.5 and Claude Opus 4.8 allocates almost 90% of development dollars to targeted improvements, compared with 10% for Kimi K2.6, and 43% for the remaining models. GPT-5.5 and Claude Opus 4.8 demonstrate a stronger tendency to take granular actions compared to other models.

## **4 Ablating Simulator Configurations**

We examine how simulation outcomes change when varying competitor and time-horizon configurations. We find that competitor difficulty provides an effective knob for tuning task difficulty, and our task remains challenging for existing models even over a short horizon.

## **4.1 Ablating Competitor Difficulty**

We ablate simulator difficulty by varying the competitor configuration. In CEO-BENCH, the competitor raises customer expectations through both a preset stationary sequence and adaptive responses to agent actions. In the adaptive component, the competitor raises customer expectations by *u* · *I*, where *u* ∼ *U*[0.2, 0.5] and *I* is the agent's cumulative quality improvement. We ablate simulator difficulty with the following settings: (1) stationary + adaptive competitor with *u* ∈ {0.1, 0.2, 0.3}; (2) stationary competitor only; (3) no competitor.

In Fig. [14\(](#page-13-1)a), we show that reducing competitor strength significantly reduces the difficulty of the task, and removing the competitor makes the task much easier. The ablation shows that competitor strength can be an effective knob for tuning task difficulty, and the non-stationary environment is a crucial component of what makes the task challenging.

<span id="page-13-0"></span>![](_page_13_Figure_0.jpeg)

**Figure 13. Examples of planning in GPT-5.5 and Claude Opus 4.8 memos.** The agents anticipate scenarios and solutions with "if-then" contingencies. We show in Fig. 12(d) that these models anticipate more frequently than other models.

<span id="page-13-1"></span>![](_page_13_Figure_2.jpeg)

**Figure 14. Ablating simulator configurations.** (a) Weaker or absent competitors make the task substantially easier. (b) Shortening the horizon to 50 days results in most models still unable to make profits.

#### 4.2 Ablating Time-Horizon

We examine whether agents behave differently when told to maximize cash balance over a shorter horizon. In this experiment, we change the simulation period to 50 days, one-tenth of the original simulation period. While the shortened horizon reduces challenges in long-term planning, Fig. 14(b) shows that only GPT-5.5 is still able to make a positive profit at the end. This analysis reveals that most models today remain weak in orchestrating decisions toward a short-term goal.

### 4.3 Ablating Agent Harness

CEO-BENCH can easily evaluate any agent harness. While we obtain most results with a custom minimal terminal-using agent harness, we ablate popular agent harnesses while keeping the underlying model fixed. For Claude Opus 4.7, we compare results with Claude Code (Anthropic, 2026), and for GPT-5.5, we compare results with Codex (OpenAI, 2026). In Fig. 15, we show that switching harnesses massively changes agent behaviors. Agents take significantly fewer actions when using Claude Code and Codex, resulting in inferior performance. While we cannot access full implementation details of these harnesses, we hypothesize that the difference results from software engineering-oriented system prompts of these harnesses.

<span id="page-14-0"></span>![](_page_14_Figure_0.jpeg)

**Figure 15. Cash trajectories and action frequency when ablating agent harnesses.** We compare Claude Opus 4.7 and GPT-5.5 under our minimal terminal-using agent versus Claude Code and Codex respectively. Under Claude Code and Codex, the agents produce fewer actions per turn and achieve inferior performance.

### 5 Related Work

Language model evaluations. Language-model evaluation has moved from static knowledge and reasoning (Hendrycks et al., 2021; Srivastava et al., 2023; Liang et al., 2023; Rein et al., 2024) toward realistic agentic task execution (Chen et al., 2021; Jimenez et al., 2024; Zhou et al., 2024; Xie et al., 2024b; Drouin et al., 2024; Trivedi et al., 2024; Yoran et al., 2024; Yao et al., 2025; Liu et al., 2024; Ma et al., 2024). Recent benchmarks have expanded evaluation scope to economically valuable deliverables in broad domains (Patil et al., 2025; Mialon et al., 2024; Chan et al., 2025; Starace et al., 2025; Miserendino et al., 2025; Patwardhan et al., 2025). However, their objectives usually terminate at a target state or one-shot deliverable. CEO-BENCH instead asks whether agents can sustain progress toward a distant objective as earlier decisions continue to shape later states.

Long-horizon agent evaluation. Memory and continual-learning benchmarks test models' ability to retain information over time (Bai et al., 2024; Hsieh et al., 2024; Wu et al., 2025; Hu et al., 2026; He et al., 2026b; Laskin et al., 2023; Wang et al., 2023; Monea et al., 2024), but they are often limited to information retrieval or a single static task. Long-horizon benchmarks extend evaluation from isolated tasks to processes that unfold over time (Wu et al., 2024; Xie et al., 2024a; Xu et al., 2025; Chan et al., 2025; Starace et al., 2025; Wang et al., 2025; Luo et al., 2025; He et al., 2026a). Most recently, Vending-Bench asks agents to run a vending machine over many days, and AccountingBench asks agents to close monthly books from real software company data (Backlund and Petersson, 2025a;b; Penrose AI, 2025). However, they involve narrow operating problems, fewer coupled decisions, and largely stable or observable environments. CEO-BENCH evaluates long-horizon agency in a broader operating setting where agents must coordinate pricing, growth, product, operations, communication, and enterprise sales under hidden state, noisy feedback, delayed consequences, and non-stationary market pressure in a consistent simulator. For example, we show in Appendix C that Vending-Bench allows models to accumulate successes relatively steadily, while our simulator requires an agent to make significant investments that only pay back much later, posing a stronger challenge to long-horizon planning.

## 6 Limitations and Conclusion

#### 6.1 Limitations

We make our best effort to approximate real-world startup operations and challenges in CEO-BENCH. However, discrepancies can still exist between reality and the approximation. For example, since we have not found a reliable way to evaluate a model's capability to propose qualitative changes to products, we simulate products using only a quality measure. In addition, to make each simulation run economically feasible, we limit the scope of possible actions and leave out aspects such as compliance, security, and fundraising.

## **6.2 Conclusion**

CEO-BENC H shows a gap between existing models' local tool competence and crucial sustained strategic skills: agents built on existing models can take plausible actions but fail when those actions must compound under delayed feedback, hidden state, and non-stationarity. To develop agents beyond isolated task executors, we need evaluations that ask whether they can organize evolving systems toward distant goals. CEO-BENC H is one step toward that future: building agents and training models that do not merely answer requests, but help steer long-running organizations through uncertainty.

# **Acknowledgments**

We thank Modal for providing GPU resources for LLM inference. We thank Shuer Jiang, Boya Zeng, Sachin Konan, Taiming Lu, Linrong Cai, David Yin, Rahul Chalamala, Bryan Chiang, Luke Zeller, Yunyu Lin, Berkan Dokmeci, Bennett O'Brien, Ashank Tomar, and Ang Li for discussions and feedback. We thank Spencer Hong and The General Intelligence Company of New York for additional evaluations. KN acknowledges support from Schmidt Sciences.

# **References**

<span id="page-15-3"></span>Anthropic. Claude code overview. <https://code.claude.com/docs/en/overview>, 2026.

<span id="page-15-1"></span>Axel Backlund and Lukas Petersson. Vending-bench: A benchmark for long-term coherence of autonomous agents. *arXiv preprint arXiv:2502.15840*, 2025a.

<span id="page-15-2"></span>Axel Backlund and Lukas Petersson. Vending-bench 2. <https://andonlabs.com/evals/vending-bench-2>, 2025b.

<span id="page-15-8"></span>Yushi Bai, Xin Lv, Jiajie Zhang, Hongchang Lyu, Jiankai Tang, Zhidian Huang, Zhengxiao Du, Xiao Liu, Aohan Zeng, Lei Hou, Yuxiao Dong, Jie Tang, and Juanzi Li. LongBench: A bilingual, multitask benchmark for long context understanding. In *ACL*, 2024.

<span id="page-15-7"></span>Jun Shern Chan, Neil Chowdhury, Oliver Jaffe, James Aung, Dane Sherburn, Evan Mays, Giulio Starace, Kevin Liu, Leon Maksin, Tejal Patwardhan, Lilian Weng, and Aleksander Madry. MLE-bench: Evaluating machine learning agents on machine learning engineering. In *ICLR*, 2025.

<span id="page-15-5"></span>Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde de Oliveira Pinto, Jared Kaplan, Harri Edwards, Yuri Burda, Nicholas Joseph, Greg Brockman, et al. Evaluating large language models trained on code. *arXiv preprint arXiv:2107.03374*, 2021.

<span id="page-15-6"></span>Alexandre Drouin, Maxime Gasse, Massimo Caccia, Issam H. Laradji, Manuel Del Verme, Tom Marty, Léo Boisvert, Megh Thakkar, Quentin Cappart, David Vazquez, Nicolas Chapados, and Alexandre Lacoste. WorkArena: How capable are web agents at solving common knowledge work tasks? In *ICML*, 2024.

<span id="page-15-9"></span>Muyu He, Adit Jain, Anand Kumar, Vincent Tu, Soumyadeep Bakshi, Sachin Patro, and Nazneen Rajani. YC-Bench: Benchmarking AI agents for long-term planning and consistent execution. *arXiv preprint arXiv:2604.01212*, 2026a.

<span id="page-15-0"></span>Zexue He, Yu Wang, Churan Zhi, Yuanzhe Hu, Tzu-Ping Chen, Lang Yin, Ze Chen, Tong Arthur Wu, Siru Ouyang, Zihan Wang, Jiaxin Pei, Julian McAuley, Yejin Choi, and Alex Pentland. MemoryArena: Benchmarking agent memory in interdependent multi-session agentic tasks. *arXiv preprint arXiv:2602.16313*, 2026b.

<span id="page-15-4"></span>Dan Hendrycks, Collin Burns, Steven Basart, Andy Zou, Mantas Mazeika, Dawn Song, and Jacob Steinhardt. Measuring massive multitask language understanding. In *ICLR*, 2021.

- <span id="page-16-10"></span>Cheng-Ping Hsieh, Simeng Sun, Samuel Kriman, Shantanu Acharya, Dima Rekesh, Fei Jia, Yang Zhang, and Boris Ginsburg. RULER: What's the real context size of your long-context language models? In *COLM*, 2024.
- <span id="page-16-3"></span>Yuanzhe Hu, Yu Wang, and Julian McAuley. Evaluating memory in LLM agents via incremental multi-turn interactions. In *ICLR*, 2026.
- <span id="page-16-0"></span>Carlos E Jimenez, John Yang, Alexander Wettig, Shunyu Yao, Kexin Pei, Ofir Press, and Karthik Narasimhan. SWE-bench: Can language models resolve real-world GitHub issues? In *ICLR*, 2024.
- <span id="page-16-14"></span>Daniel Kahneman and Amos Tversky. Prospect theory: An analysis of decision under risk. *Econometrica*, 47 (2):263–291, 1979. doi: 10.2307/1914185.
- <span id="page-16-15"></span>Evan F. Koenig. Using the purchasing managers' index to assess the economy's strength and the likely direction of monetary policy. *Federal Reserve Bank of Dallas Economic and Financial Policy Review*, 1(6), 2002. URL [https://fraser.stlouisfed.org/files/docs/publications/frbdalreview/frbdal\\_er02v01\\_n06\\_](https://fraser.stlouisfed.org/files/docs/publications/frbdalreview/frbdal_er02v01_n06_a01.pdf) [a01.pdf](https://fraser.stlouisfed.org/files/docs/publications/frbdalreview/frbdal_er02v01_n06_a01.pdf).
- <span id="page-16-11"></span>Michael Laskin, Luyu Wang, Junhyuk Oh, Emilio Parisotto, Stephen Spencer, Richie Steigerwald, DJ Strouse, Steven Hansen, Angelos Filos, Ethan Brooks, Maxime Gazeau, Himanshu Sahni, Satinder Singh, and Volodymyr Mnih. In-context reinforcement learning with algorithm distillation. In *ICLR*, 2023.
- <span id="page-16-5"></span>Percy Liang, Rishi Bommasani, Tony Lee, Dimitris Tsipras, Dilara Soylu, Michihiro Yasunaga, Yian Zhang, Deepak Narayanan, Yuhuai Wu, Ananya Kumar, et al. Holistic evaluation of language models. *TMLR*, 2023.
- <span id="page-16-6"></span>Xiao Liu, Hao Yu, Hanchen Zhang, Yifan Xu, Xuanyu Lei, Hanyu Lai, Yu Gu, Hangliang Ding, Kaiwen Men, Kejuan Yang, Shudan Zhang, Xiang Deng, Aohan Zeng, Zhengxiao Du, Chenhui Zhang, Sheng Shen, Tianjun Zhang, Yu Su, Huan Sun, Minlie Huang, Yuxiao Dong, and Jie Tang. AgentBench: Evaluating LLMs as agents. In *ICLR*, 2024.
- <span id="page-16-13"></span>Haotian Luo, Huaisong Zhang, Xuelin Zhang, Haoyu Wang, Zeyu Qin, Wenjie Lu, Guozheng Ma, Haiying He, Yingsha Xie, Qiyang Zhou, Zixuan Hu, Hongze Mi, Yibo Wang, Naiqiang Tan, Hong Chen, Yi R. Fung, Chun Yuan, and Li Shen. UltraHorizon: Benchmarking agent capabilities in ultra long-horizon scenarios. *arXiv preprint arXiv:2509.21766*, 2025.
- <span id="page-16-7"></span>Chang Ma, Junlei Zhang, Zhihao Zhu, Cheng Yang, Yujiu Yang, Yaohui Jin, Zhenzhong Lan, Lingpeng Kong, and Junxian He. AgentBoard: An analytical evaluation board of multi-turn LLM agents. In *NeurIPS*, 2024.
- <span id="page-16-2"></span>James G. March. Exploration and exploitation in organizational learning. *Organization Science*, 2(1):71–87, 1991. doi: 10.1287/orsc.2.1.71.
- <span id="page-16-8"></span>Grégoire Mialon, Clémentine Fourrier, Thomas Wolf, Yann LeCun, and Thomas Scialom. GAIA: A benchmark for general AI assistants. In *ICLR*, 2024.
- <span id="page-16-9"></span>Samuel Miserendino, Michele Wang, Tejal Patwardhan, and Johannes Heidecke. SWE-Lancer: Can frontier LLMs earn \$1 million from real-world freelance software engineering? In *ICML*, 2025.
- <span id="page-16-12"></span>Giovanni Monea, Antoine Bosselut, Kianté Brantley, and Yoav Artzi. LLMs are in-context bandit reinforcement learners. *arXiv preprint arXiv:2410.05362*, 2024.
- <span id="page-16-4"></span>Michael Mussa and Sherwin Rosen. Monopoly and product quality. *Journal of Economic Theory*, 18(2):301–317, 1978.
- <span id="page-16-1"></span>Allen Newell and Herbert A. Simon. *Human Problem Solving*. Prentice-Hall, Englewood Cliffs, NJ, 1972. ISBN 0-13-445403-0.

- <span id="page-17-14"></span>Richard L. Oliver. A cognitive model of the antecedents and consequences of satisfaction decisions. *Journal of Marketing Research*, 17(4):460–469, 1980. doi: 10.1177/002224378001700405.
- <span id="page-17-4"></span>OpenAI. Codex cli. <https://developers.openai.com/codex/cli>, 2026.
- <span id="page-17-5"></span>OpenCode. Opencode: The open source ai coding agent. <https://opencode.ai/>, 2026.
- <span id="page-17-10"></span>Shishir G. Patil, Huanzhi Mao, Fanjia Yan, Charlie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, and Joseph E. Gonzalez. The Berkeley Function Calling Leaderboard (BFCL): From tool use to agentic evaluation of large language models. In *ICML*, 2025.
- <span id="page-17-2"></span>Tejal Patwardhan, Rachel Dias, Elizabeth Proehl, Grace Kim, Michele Wang, Olivia Watkins, Simón Posada Fishman, Marwan Aljubeh, Phoebe Thacker, Laurance Fauconnet, Natalie S. Kim, Patrick Chao, Samuel Miserendino, Gildas Chabot, David Li, Michael Sharman, Alexandra Barr, Amelia Glaese, Jerry Tworek, et al. GDPval: Evaluating AI model performance on real-world economically valuable tasks. *arXiv preprint arXiv:2510.04374*, 2025.
- <span id="page-17-3"></span>Penrose AI. AccountingBench: Evaluating LLMs on real long-horizon business tasks. [https://accounting.p](https://accounting.penrose.com/) [enrose.com/](https://accounting.penrose.com/), 2025.
- <span id="page-17-6"></span>Pi Contributors. Pi documentation. <https://pi.dev/docs/latest>, 2026.
- <span id="page-17-8"></span>David Rein, Betty Li Hou, Asa Cooper Stickland, Jackson Petty, Richard Yuanzhe Pang, Julien Dirani, Julian Michael, and Samuel R. Bowman. GPQA: A graduate-level google-proof Q&A benchmark. In *COLM*, 2024.
- <span id="page-17-0"></span>Herbert A. Simon. A behavioral model of rational choice. *The Quarterly Journal of Economics*, 69(1):99–118, 1955. doi: 10.2307/1884852.
- <span id="page-17-7"></span>Aarohi Srivastava, Abhinav Rastogi, Abhishek Rao, Abu Awal Md Shoeb, Abubakar Abid, Adam Fisch, Adam R. Brown, Adam Santoro, Aditya Gupta, Adrià Garriga-Alonso, et al. Beyond the imitation game: Quantifying and extrapolating the capabilities of language models. *TMLR*, 2023.
- <span id="page-17-11"></span>Giulio Starace, Oliver Jaffe, Dane Sherburn, James Aung, Jun Shern Chan, Leon Maksin, Rachel Dias, Evan Mays, Benjamin Kinsella, Wyatt Thompson, Johannes Heidecke, Amelia Glaese, and Tejal Patwardhan. PaperBench: Evaluating AI's ability to replicate AI research. In *ICML*, 2025. arXiv:2504.01848.
- <span id="page-17-16"></span>Alexander Szimayer and Ross Maller. Testing for mean reversion in processes of Ornstein–Uhlenbeck type. *Statistical Inference for Stochastic Processes*, 7:95–113, 2004. doi: 10.1023/B:SISP.0000026032.80363.59.
- <span id="page-17-1"></span>David J. Teece, Gary Pisano, and Amy Shuen. Dynamic capabilities and strategic management. *Strategic Management Journal*, 18(7):509–533, 1997. doi: 10.1002/(SICI)1097-0266(199708)18:7<509::AID-SMJ882>3.0. CO;2-Z.
- <span id="page-17-9"></span>Harsh Trivedi, Tushar Khot, Mareike Hartmann, Ruskin Manku, Vinty Dong, Edward Li, Shashank Gupta, Ashish Sabharwal, and Niranjan Balasubramanian. AppWorld: A controllable world of apps and people for benchmarking interactive coding agents. In *ACL*, 2024.
- <span id="page-17-15"></span>George E. Uhlenbeck and Leonard S. Ornstein. On the theory of the Brownian motion. *Physical Review*, 36(5): 823–841, 1930. doi: 10.1103/PhysRev.36.823.
- <span id="page-17-13"></span>Weixuan Wang, Dongge Han, Daniel Madrigal Diaz, Jin Xu, Victor Rühle, and Saravan Rajmohan. Odyssey-Bench: Evaluating LLM agents on long-horizon complex office application workflows. *arXiv preprint arXiv:2508.09124*, 2025.
- <span id="page-17-12"></span>Xiao Wang, Yuansen Zhang, Tianze Chen, Songyang Gao, Senjie Jin, Xianjun Yang, Zhiheng Xi, Rui Zheng, Yicheng Zou, Tao Gui, Qi Zhang, and Xuanjing Huang. TRACE: A comprehensive benchmark for continual learning in large language models. *arXiv preprint arXiv:2310.06762*, 2023.

- <span id="page-18-4"></span>Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, and Dong Yu. LongMemEval: Benchmarking chat assistants on long-term interactive memory. In *ICLR*, 2025.
- <span id="page-18-5"></span>Yue Wu, Xuan Tang, Tom M. Mitchell, and Yuanzhi Li. SmartPlay: A benchmark for LLMs as intelligent agents. In *ICLR*, 2024.
- <span id="page-18-6"></span>Jian Xie, Kai Zhang, Jiangjie Chen, Tinghui Zhu, Renze Lou, Yuandong Tian, Yanghua Xiao, and Yu Su. TravelPlanner: A benchmark for real-world planning with language agents. In *ICML*, 2024a.
- <span id="page-18-2"></span>Tianbao Xie, Danyang Zhang, Jixuan Chen, Xiaochuan Li, Siheng Zhao, Ruisheng Cao, Toh Jing Hua, Zhoujun Cheng, Dongchan Shin, Fangyu Lei, et al. OSWorld: Benchmarking multimodal agents for open-ended tasks in real computer environments. In *NeurIPS*, 2024b.
- <span id="page-18-7"></span>Frank F. Xu, Yufan Song, Boxuan Li, Yuxuan Tang, Kritanjali Jain, Mengxue Bao, Zora Z. Wang, Xuhui Zhou, Zhitong Guo, Murong Cao, et al. TheAgentCompany: Benchmarking LLM agents on consequential real world tasks. In *NeurIPS*, 2025.
- <span id="page-18-0"></span>Shunyu Yao, Noah Shinn, Pedram Razavi, and Karthik Narasimhan. *τ*-bench: A benchmark for tool-agentuser interaction in real-world domains. In *ICLR*, 2025.
- <span id="page-18-3"></span>Ori Yoran, Samuel Joseph Amouyal, Chaitanya Malaviya, Ben Bogin, Ofir Press, and Jonathan Berant. AssistantBench: Can web agents solve realistic and time-consuming tasks? In *EMNLP*, 2024.
- <span id="page-18-1"></span>Shuyan Zhou, Frank F Xu, Hao Zhu, Xuhui Zhou, Robert Lo, Abishek Sridhar, Xianyi Cheng, Tianyue Ou, Yonatan Bisk, Daniel Fried, Uri Alon, and Graham Neubig. WebArena: A realistic web environment for building autonomous agents. In *ICLR*, 2024.

# **Appendix**

#### <span id="page-19-0"></span>A Simulator Mechanics

We describe full details of simulator mechanics in this section.

## A.1 Agent Commands and Observable State

**Python action surface.** The agent changes the company by importing functions from novamind\_api and executing Python. The active command groups are:

- pricing: set\_prices, set\_model\_tiers, set\_usage\_quotas, and set\_promotion.
- marketing: set\_daily\_spend, set\_targeted\_ad\_spend, and set\_ads\_strength.
- marketing: set\_lead\_promotion and post\_social\_media.
- analytics: set\_targeted\_ops\_spend and set\_targeted\_dev\_spend.
- research: start\_research\_project and list\_research\_projects.
- market: research\_market, research\_group, get\_market\_overview, and get\_group\_insights.
- infrastructure: set\_capacity\_tier and get\_cost\_info.
- enterprise: send\_enterprise\_deal and reject\_enterprise\_deal.
- **Time and data access**: next\_week advances the simulator, query reads the company database, and get\_vars reports runtime variables.

The interface is intentionally operational rather than omniscient: it exposes dashboards, database tables, social posts, and inbox messages, while leaving true preferences, satisfaction, competitor schedules, and hidden macro state latent.

#### <span id="page-19-1"></span>A.2 Customers, Plans, and Participation

**Customer parameter sampling.** Each customer belongs to a group g and receives private parameters such as maximum willingness to pay, quality floor, quality ceiling, usage demand, ad sensitivity, support sensitivity, and enterprise negotiation traits. For a generic customer parameter k,

$$\theta_{i,k,t} = \text{clip}\left(\tilde{\theta}_{i,k} + \Delta_{g,k,t}^{\text{market}}, \theta_{g,k}^{\text{min}}, \theta_{g,k}^{\text{max}}\right), \qquad \tilde{\theta}_{i,k} \sim \mathcal{D}_{g,k}(\mu_{g,k}, \sigma_{g,k}), \tag{4}$$

where  $\theta_{i,k,t}$  is customer i's active value for parameter k,  $\tilde{\theta}_{i,k}$  is the sampled base value,  $\mathcal{D}_{g,k}$  is the configured group-level sampling distribution,  $\mu_{g,k}$  and  $\sigma_{g,k}$  are its location and spread parameters,  $\Delta_{g,k,t}^{\text{market}}$  is accumulated market drift, and  $\theta_{g,k}^{\text{min}}$ ,  $\theta_{g,k}^{\text{max}}$  are clipping bounds. The distribution terms encode the fact that a market segment has a typical profile, while the sampled base value gives each customer an idiosyncratic budget, tolerance, or usage pattern. The drift term represents changing market conditions, such as customers becoming more demanding over time, and the clipping bounds keep preferences in plausible ranges. This mechanism simulates real customer cohorts: people in the same segment resemble one another, but they are not interchangeable, and their preferences can move as the market changes.

**Customer participation curve.** Each customer i has maximum monthly willingness to pay  $c_i$ , minimum quality floor  $q_i^{\min}$ , quality ceiling  $q_i^{\max}$ , and low-price and high-price slopes  $s_i^L, s_i^R$ . For offered effective price C, define normalized price  $x = C/c_i$ , quality range  $\Delta q_i = q_i^{\max} - q_i^{\min}$ , and sigmoid  $\sigma(z) = (1 + e^{-z})^{-1}$ . With

configurable curve coefficients  $\theta_Q^L$ ,  $\theta_Q^R$ ,  $\theta_Q^{max}$ ,  $\omega_Q$ ,  $k_Q$ ,  $\psi_Q^{min}$ ,  $\psi_Q^{max}$ ,

<span id="page-20-1"></span>
$$\psi_{i}(C) = \omega_{Q} \sigma \left( k_{Q} s_{i}^{L} (x - \theta_{Q}^{L}) \right) + (1 - \omega_{Q}) \sigma \left( k_{Q} s_{i}^{R} (x - \theta_{Q}^{R}) \right),$$

$$Q_{i}^{\text{req}}(C) = q_{i}^{\min} + \Delta q_{i} \operatorname{clip} \left( \psi_{i}(C), \psi_{Q}^{\min}, \psi_{Q}^{\max} \right).$$
(5)

Here  $\psi_i(C)$  is the customer's normalized required-quality score at price C;  $x = C/c_i$  measures price relative to the customer's willingness to pay;  $\Delta q_i$  is the customer's personal quality range;  $\theta_Q^L$  and  $\theta_Q^R$  locate the lowand high-price portions of the curve;  $\omega_Q$  blends the two portions;  $s_i^L$  and  $s_i^R$  make some customers more price-sensitive than others;  $k_Q$  controls global curvature; and  $\psi_Q^{\min}$ ,  $\psi_Q^{\max}$  bound the score. The mechanic follows a participation-rule view of differentiated products: higher prices require higher perceived quality, and customers near their budget ceiling become more demanding (Mussa and Rosen, 1978). A non-enterprise customer accepts plan p only if  $C_{i,p,t} \leq \theta_Q^{\max} c_i$  and  $Q_{i,p,t}^{\mathrm{perc}} \geq Q_i^{\mathrm{req}}(C_{i,p,t})$ . This simulates the real purchasing rule that customers do not compare price in isolation; they ask whether the product feels good enough for what they are being charged.

<span id="page-20-2"></span>![](_page_20_Figure_3.jpeg)

**Figure 16. Example customer participation curves.** Each curve represents the average participation behavior of a customer group. Each curve maps the offered monthly price C to the minimum accepted quality  $Q_i^{\text{req}}(C)$  for a customer with different willingness to pay, quality floors, ceilings, and price-sensitivity slopes.

**Plan choice and billing-period switching.** Let  $\mathcal{P}$  be the active plan set. For customer i, the simulator evaluates all plans and chooses the acceptable plan with the largest surplus:

$$p_{i,t}^* = \arg\max_{p \in \mathcal{P}} \left[ Q_{i,p,t}^{\text{perc}} - Q_i^{\text{req}}(C_{i,p,t}^{\text{eff}}) \right], \qquad \mathcal{A}_{i,t} = \{ p \in \mathcal{P} : C_{i,p,t}^{\text{eff}} \le c_i, \ Q_{i,p,t}^{\text{perc}} \ge Q_i^{\text{req}}(C_{i,p,t}^{\text{eff}}) \}. \tag{6}$$

<span id="page-20-0"></span>The choice is valid only when  $p_{i,t}^* \in \mathcal{A}_{i,t}$ ; if  $\mathcal{A}_{i,t}$  is empty on a billing decision day, the customer cancels.  $\mathcal{P}$  is the set of plans currently offered by the company,  $C_{i,p,t}^{\text{eff}}$  is the price after active promotions,  $Q_{i,p,t}^{\text{perc}}$  is perceived quality for plan p,  $c_i$  is the customer's budget ceiling, and  $\mathcal{A}_{i,t}$  is the acceptable-plan set. The surplus term measures how much perceived quality exceeds the customer's minimum requirement at that effective price. This creates a simple operator intuition: customers do not maximize quality alone or price alone; they choose the plan that clears their personal price-quality bar with the best headroom. In reality, this corresponds to monthly subscription review: customers may upgrade, downgrade, stay, or churn depending on the menu of plans available at renewal time.

### A.3 Product Quality, Usage, and Monetization

**Promotions and effective price.** Promotions are additive across global, group, customer, and group-plan scopes. At billing time,

$$C_{i,p,t}^{\text{eff}} = \left[ P_{p,t} - \Pi_t^{\text{global}} - \Pi_{g,t}^{\text{group}} - \Pi_{i,t}^{\text{customer}} - \Pi_{g,p,t}^{\text{group-plan}} - \mathbb{1}\{\text{first}_{i,t}\}\Pi_{g,t}^{\text{lead}} \right]_+. \tag{7}$$

Here  $P_{p,t}$  is the listed price for plan p,  $\Pi_t^{\text{global}}$  is a site-wide discount,  $\Pi_{g,t}^{\text{group}}$  targets a customer segment,  $\Pi_{i,t}^{\text{customer}}$  targets an individual customer,  $\Pi_{g,p,t}^{\text{group-plan}}$  targets a segment-plan pair,  $\Pi_{g,t}^{\text{lead}}$  is a first-bill lead promotion, first<sub>i,t</sub> marks the first billing event for a newly acquired customer, and  $[\cdot]_+$  floors price at zero. Promotions therefore act as dollar discounts rather than hidden quality boosts; they can help acquisition or retention but directly reduce revenue. The mechanism simulates couponing, contract discounts, and introductory offers, where revenue changes immediately even though the product itself has not improved.

**Usage and capacity.** Each active subscriber has a daily usage draw  $\tilde{u}_{i,t}$ , plan quota  $U_{p,t}$ , billing-period cumulative usage  $\bar{U}_{i,t}$ , and weekly usage multiplier  $W_t$ . The realized daily usage is

$$u_{i,t} = \operatorname{round}\left(\min\left(\tilde{u}_{i,t}W_t, \left[U_{p_i,t} - \bar{U}_{i,t}\right]_+\right)\right), \qquad U_t^{\text{tot}} = \sum_i u_{i,t}.$$
(8)

 $u_{i,t}$  is the delivered usage units today,  $\tilde{u}_{i,t}$  is the customer's latent demand,  $W_t$  is a weekly demand multiplier,  $U_{p_i,t}$  is the quota on the customer's active plan,  $\bar{U}_{i,t}$  is already-consumed usage in the billing period, and  $U_t^{\text{tot}}$  is total platform load. The positive-part term enforces the remaining plan quota, and rounding maps continuous demand into discrete usage units. The mechanic makes high-growth strategies stress infrastructure: more customers and higher quotas produce more usage, which can create overload if capacity is not upgraded. This simulates a real software business where usage is bursty, quotas cap consumption, and product-market success can turn into an infrastructure problem.

**Service health.** For capacity tier  $\kappa_t$  with capacity  $K_{\kappa_t}$  and operations spend  $x_t^{\text{ops}}$ , the overload level and outage probability are

$$o_t = \left[\frac{U_t^{\text{tot}}}{K_{\kappa_t}} - 1\right]_+, \qquad P(\text{outage}_t) = \max\left(p_{\text{out}}^{\text{min}}, p_{\text{out}}^0 \exp(-x_t^{\text{ops}}/\chi_{\text{ops}})\right) \left(1 + \beta_{\text{out}}^o o_t\right). \tag{9}$$

 $o_t$  is zero when capacity covers demand and positive when load exceeds capacity;  $K_{\kappa_t}$  is the capacity available under tier  $\kappa_t$ ;  $p_{\text{out}}^0$  is baseline outage risk;  $p_{\text{out}}^{\text{min}}$  is the reliability floor;  $x_t^{\text{ops}}$  is daily operations spend;  $\chi_{\text{ops}}$  controls diminishing returns to operations spend; and  $\beta_{\text{out}}^0$  makes overload increase outage risk. Operations spending therefore buys reliability, while capacity tier choices buy headroom. This simulates the operational reality that SRE effort and cloud capacity reduce incidents, but overloaded systems remain fragile and no team can drive outage risk exactly to zero.

**Delivered quality.** Delivered quality measures technical product quality before customer-specific perception effects:

$$Q_{g,p,t}^{\text{del}} = \left(q_0 + b_t^{\text{shared}} + b_{g,t}^{\text{group}}\right) m_p - \beta_o \, o_t - \beta_{\text{out}} \, \mathbb{1}\{\text{outage}_t\},\tag{10}$$

where  $q_0$  is baseline product quality,  $b_t^{\rm shared}$  is shared quality from development and R&D,  $b_{g,t}^{\rm group}$  is targeted group quality for segment g,  $m_p$  is the model-tier multiplier for plan p,  $o_t$  is overload, and  $\mathbb{1}\{\text{outage}_t\}$  is the outage indicator. The coefficients  $\beta_o$  and  $\beta_{\rm out}$  translate infrastructure problems into quality loss. The product-quality terms model the underlying capability of the service, while the negative terms model degraded delivery. This separates product investment from delivery reliability: a strong product can still feel bad when overloaded, just as real customers judge both feature quality and whether the service actually works when they need it.

**Development and R&D.** Daily development and targeted development add quality with diminishing returns:

$$\Delta b_t^{\text{shared,dev}} = \beta_{\text{dev}} \log(1 + x_t^{\text{dev}} / \chi_{\text{dev}}), \qquad \Delta b_{g,t}^{\text{target}} = \beta_{\text{target}} \log(1 + x_{g,t}^{\text{target}} / \chi_{\text{target}}). \tag{11}$$

 $x_t^{\rm dev}$  is global development spend,  $x_{g,t}^{\rm target}$  is targeted development spend for group g,  $\Delta b_t^{\rm shared, dev}$  is the daily shared-quality increment,  $\Delta b_{g,t}^{\rm target}$  is the daily group-specific increment,  $\beta_{\rm dev}$ ,  $\beta_{\rm target}$  convert spend into quality, and  $\chi_{\rm dev}$ ,  $\chi_{\rm target}$  control diminishing returns. The logarithm makes the first dollars of engineering spend more productive than later dollars, reflecting coordination overhead and finite easy fixes. This simulates staffing and engineering allocation: basic improvements can be made quickly, but pushing quality further requires disproportionately more effort. R&D projects are larger delayed improvements:

$$D_j^{\text{R\&D}} \sim \mathcal{D}_{r_j}^{\text{time}}, \qquad G_j^{\text{R\&D}} \sim \mathcal{D}_{r_j}^{\text{quality}}, \qquad b_{t+1}^{\text{shared}} = b_t^{\text{shared}} + \Delta b_t^{\text{shared,dev}} + \sum_{j: t = t_i^{\text{done}}} G_j^{\text{R\&D}} + \epsilon_t^q.$$
 (12)

j indexes a research project,  $r_j$  is its tier,  $D_j^{\text{R\&D}}$  is completion delay,  $\mathcal{D}_{r_j}^{\text{time}}$  is the tier-specific time distribution,  $G_j^{\text{R\&D}}$  is its quality gain,  $\mathcal{D}_{r_j}^{\text{quality}}$  is the tier-specific gain distribution,  $t_j^{\text{done}}$  is the completion day, and  $\varepsilon_t^q$  is configured product-quality noise. The summation adds only projects that finish today, while daily development accumulates continuously. The design makes R&D a delayed investment: it can move the global quality frontier, but it does not instantly solve today's churn risk. This simulates product roadmaps in which small engineering work compounds steadily, while larger research bets have uncertain delivery dates and payoffs.

**In-app ads.** In-app ad strength is additive across global, group, and customer settings and then log-scaled:

$$a_{i,t}^{\text{eff}} = \frac{\log\left(\alpha_a + \kappa_a \operatorname{clip}(a_t^{\text{global}} + a_{g,t}^{\text{group}} + a_{i,t}^{\text{customer}}, a_{\min}, a_{\max})\right) - \log\alpha_a}{\log(\alpha_a + \kappa_a a_{\max}) - \log\alpha_a}.$$
(13)

Here  $a_t^{\text{global}}$ ,  $a_{g,t}^{\text{group}}$ , and  $a_{i,t}^{\text{customer}}$  are configured ad strengths at company, segment, and customer scope;  $a_{\min}$ ,  $a_{\max}$  are bounds;  $\alpha_a$  is a positive log offset;  $\kappa_a$  controls how quickly raw ad strength saturates; and  $a_{i,t}^{\text{eff}}$  is the customer-visible ad load after clipping and saturation. The log scaling makes additional ad load less effective at the high end, matching the idea that an already ad-heavy product has limited extra monetization headroom. Ads create daily revenue

$$Y_{i,t}^{\text{ads}} = \rho_i^{\text{ads}} a_{i,t}^{\text{eff}} n_i, \tag{14}$$

where  $\rho_i^{\text{ads}}$  is customer i's ad-revenue sensitivity and  $n_i$  is seats. The same effective ad load subtracts from perceived quality. This creates a monetization tradeoff: ads are immediately lucrative but can reduce satisfaction and retention. The mechanism simulates ad-supported SaaS or freemium products, where more impressions produce revenue but also make the product feel noisier or less professional to some customers.

**Perceived quality.** Perceived quality is the utility-relevant quality experienced by customer *i* after relationship, tenure, support, quota, and ad effects:

$$Q_{i,t}^{\text{perc}} = Q_{g,p,t}^{\text{del}} + \beta_r(r_{i,t} - r_0) + \beta_d \log(\alpha_d + d_{i,t}/d_0) - \beta_I I_{i,t} - \beta_U \left(\nu_U - \frac{U_{p,t}}{D_U u_i}\right)_+ - \eta_i^{\text{ads}} a_{i,t}^{\text{eff}},$$
(15)

where  $r_{i,t}$  is relationship score,  $r_0$  is neutral relationship,  $d_{i,t}$  is days subscribed,  $d_0$  is the tenure scale,  $\alpha_d$  is the tenure log offset,  $I_{i,t}$  is open-issue days,  $U_{p,t}$  is plan quota,  $u_i$  is sampled daily usage demand,  $D_U$  converts daily demand to the quota period, and  $a_{i,t}^{\text{eff}}$  is effective ad load. Coefficients  $\beta_r$ ,  $\beta_d$ ,  $\beta_I$ ,  $\beta_U$  control relationship, tenure, issue, and quota effects, while  $\eta_i^{\text{ads}}$  is the customer's ad-quality sensitivity. The terms have direct

interpretations: good relationships and familiarity add tolerance; support delays, quota shortfalls, and ads subtract from experienced quality. This simulates the difference between engineering quality and customer experience: the same product can feel better to a long-tenured, well-supported customer and worse to a customer facing tickets, quotas, or intrusive ads.

#### <span id="page-23-0"></span>A.4 Satisfaction, Retention, and Support

Satisfaction. Instant satisfaction is quality surplus over the participation curve,

$$\tilde{S}_{i,t} = Q_{i,t}^{\text{perc}} - Q_{i}^{\text{req}}(C_{i,t}), \tag{16}$$

and stored satisfaction is an exponential moving average with configurable inertia  $\lambda_S$ :

$$S_{i,t} = \lambda_S S_{i,t-1} + (1 - \lambda_S) \tilde{S}_{i,t}. \tag{17}$$

Here  $\tilde{S}_{i,t}$  is today's surplus,  $S_{i,t}$  is stored satisfaction,  $C_{i,t}$  is the effective current price,  $Q_i^{\text{req}}(C_{i,t})$  is the quality the customer expects at that price,  $Q_{i,t}^{\text{perc}}$  is experienced quality, and  $\lambda_S$  is satisfaction inertia. This is an expectancy-disconfirmation design: customers are satisfied when experience exceeds the paid-price expectation and dissatisfied when it falls short (Oliver, 1980). The moving average means customers remember recent experience instead of resetting each day, so a bad outage or a good support recovery can affect future behavior for multiple periods. Downstream rules weight negative satisfaction more strongly, consistent with loss aversion (Kahneman and Tversky, 1979). The mechanism simulates customer sentiment as a memory-bearing state rather than a one-day reaction.

**Billing revenue and involuntary churn.** On a billing day set by the billing period  $D_{\text{bill}}$ , subscription revenue is

$$Y_t^{\text{sub}} = \sum_{i \in \mathcal{B}_t} C_{i, p_i, t}^{\text{eff}} n_i, \tag{18}$$

where  $\mathcal{B}_t$  is the set of subscribers billed on day t,  $C_{i,p_i,t}^{\text{eff}}$  is the effective price of customer i's active plan,  $p_i$  is the active plan, and  $n_i$  is seats. Seat count multiplies revenue because an enterprise or team subscription pays for more users than an individual account. This simulates recurring subscription billing, where cash arrives in discrete renewal events rather than continuously every day. Before voluntary plan-choice churn, a group-level involuntary churn draw may occur:

$$\mu_{g,m}^{\text{invol}} = \text{clip}\left(\epsilon_{g,m}^{\text{invol}}, 0, 1\right), \quad \epsilon_{g,m}^{\text{invol}} \sim \mathcal{N}(\bar{\mu}_g^{\text{invol}}, \sigma_g^{\text{invol}}), \quad Z_{i,t}^{\text{invol}} \sim \text{Bernoulli}(\mu_{g,m}^{\text{invol}}).$$
 (19)

m indexes the billing period,  $\epsilon_{g,m}^{\rm invol}$  is the period-specific involuntary churn rate before clipping,  $\bar{\mu}_g^{\rm invol}$  and  $\sigma_g^{\rm invol}$  are group-specific churn parameters,  $\mu_{g,m}^{\rm invol}$  is the clipped probability used for group g in period m, and  $Z_{i,t}^{\rm invol}$  is the customer-level cancellation draw. This captures background churn such as procurement freezes, budget changes, company shutdowns, or stakeholder turnover that are not caused by the agent. Voluntary churn then follows the participation rule: if no plan clears the customer's curve, the customer cancels; if a different plan gives higher acceptable surplus, the customer switches. The mechanism simulates the fact that some churn is controllable through product and pricing, while some churn is exogenous noise in the customer base.

Support issue generation and resolution. For a subscriber with no open issue, the issue probability is

$$P(\text{issue}_{i,t}) = \text{clip}\left((p_0 + p_S(S^{\text{ref}} - S_{i,t}) + p_{\text{out}} \mathbb{1}\{\text{outage}_t\})n_i, p_{\text{min}}, p_{\text{max}}\right). \tag{20}$$

 $p_0$  is the base issue rate,  $p_S$  converts low satisfaction into tickets,  $S^{\rm ref}$  is the reference satisfaction level,  $p_{\rm out}$  adds outage-driven issue risk,  $\mathbbm{1}\{{\rm outage}_t\}$  activates that risk on outage days,  $n_i$  is seats, and  $p_{\rm min}$ ,  $p_{\rm max}$  bound the probability. More seats create more chances for someone to hit a problem, while poor satisfaction and

outages make support demand spike. This simulates customer-success queues where large accounts and unhappy users generate more tickets.

Open issues are resolved by operations pools. For pool P with spend  $x_P$ , group g members  $n_{g,P}$ , and pool size |P|,

$$N_{g,t}^{\text{resolved}} \sim \text{Poisson}\left((b_P + \lambda_g x_P) \frac{n_{g,P}}{|P|}\right).$$
 (21)

 $b_P$  is the pool's base resolution rate,  $\lambda_g$  is group-specific operations efficiency,  $x_P$  is spend assigned to support pool P,  $n_{g,P}/|P|$  allocates capacity to group g according to its share of the pool, and  $N_{g,t}^{\rm resolved}$  is the number resolved. Global operations covers all open issues; targeted operations creates additional pools by group, plan, group-plan pair, or customer. Fast resolutions add relationship boosts, while unresolved issues increase open-issue days and decay relationship. The intuition is queue-based: more operations spend increases throughput, but only for customers covered by that pool. This simulates support staffing and escalation rules, where targeted customer-success effort can protect priority segments but cannot help customers outside the targeted pool.

#### <span id="page-24-0"></span>A.5 Reputation, Social Media, and Acquisition

Reputation impact. Each active customer contributes a daily reputation delta from satisfaction:

$$\delta_{i,t}^{\text{rep}} = \begin{cases} \rho_{+} S_{i,t}, & S_{i,t} \ge S_{0}, \\ -\rho_{-} |S_{i,t}|, & S_{i,t} < S_{0}. \end{cases}$$
 (22)

 $S_0$  is neutral satisfaction,  $\rho_+$  is the positive-reputation rate,  $\rho_-$  is the negative-reputation rate, and  $\delta_{i,t}^{\rm rep}$  is customer i's daily reputation contribution. Negative satisfaction is allowed to have a different slope from positive satisfaction so that bad experiences can be more reputationally damaging than good experiences are helpful. This simulates word-of-mouth asymmetry in real markets, where angry customers often spread more salient feedback than mildly satisfied customers. For group g,

$$\Delta R_{g,t} = \frac{\sum_{i \in g} \delta_{i,t}^{\text{rep}}}{\max(N_g, N_{\min})} \log_{\nu_N}(\max(N_g, N_{\min})), \qquad R_{g,t+1} = \text{clip}(R_{g,t} + \Delta R_{g,t}, R_{\min}, R_{\max}). \tag{23}$$

 $N_g$  is the active subscriber count,  $N_{\min}$  is the small-sample normalizer,  $v_N$  controls logarithmic scale,  $R_{g,t}$  is group reputation, and  $R_{\min}$ ,  $R_{\max}$  bound reputation. The averaging term prevents a single customer from dominating a large segment, while the logarithmic factor lets larger customer bases produce more visible aggregate reputation movement. This simulates customer reviews and public sentiment accumulating within a market segment. Cancellations add event damage

$$D_{i,t}^{\text{cancel}} = \eta_D(\beta_D + \xi_t) \left(\alpha_D + \chi_D \min(S_{i,t}, S_0)^2\right) \frac{\log_{\nu_N}(\max(N_g, N_{\min}))}{\max(N_g, N_{\min})}, \qquad \xi_t \sim \text{Uniform}(\xi_{\min}, \xi_{\max}),$$
(24)

where  $\eta_D$ ,  $\beta_D$ ,  $\alpha_D$ ,  $\chi_D$  are configurable damage coefficients,  $\min(S_{i,t},S_0)^2$  makes very negative satisfaction especially costly,  $\xi_t$  is event noise, and  $D_{i,t}^{cancel}$  is the reputation hit from cancellation. This makes visible churn more damaging when the customer was very unhappy. The mechanism simulates public cancellations, angry posts, and negative references that can hurt a brand beyond the lost subscription revenue.

Cross-group reputation spillovers. Discovered groups receive spillovers from related groups:

$$R_{h,t+1} \leftarrow \operatorname{clip}\left(R_{h,t+1} + \zeta_R W_{g,h} \Delta R_{g,t}, R_{\min}, R_{\max}\right). \tag{25}$$

 $W_{g,h}$  is the influence from group g to group h,  $\zeta_R$  scales spillover,  $\Delta R_{g,t}$  is the reputation change in the source group, and the clipping bounds keep the recipient group's reputation in range. The mechanic makes

reputation networked: enterprise failures can affect nearby enterprise groups or adjacent market segments. This simulates reference networks, professional communities, and social adjacency, where the experience of one group can change expectations in a related group even before those customers use the product.

**Customer and agent social media.** Customer social-media candidates are weighted by satisfaction extremity, negative satisfaction, recent satisfaction change, active service events, influencer status, and seat count:

$$w_{i,t}^{\text{post}} = n_i \, \omega_g^{\text{inf}} \omega_{i,t}^{\text{new}} \cdot (1 + \alpha_S |S_{i,t}|) \cdot \left(1 + \alpha_- [-S_{i,t}]_+^2\right) \cdot (1 + \alpha_\Delta |\Delta S_{i,t}|) \cdot (1 + \alpha_E |\mathcal{E}_{i,t}|). \tag{26}$$

 $w_{i,t}^{\mathrm{post}}$  is the post-sampling weight,  $n_i$  is seats,  $\omega_g^{\mathrm{inf}}$  is the group influence multiplier,  $\omega_{i,t}^{\mathrm{new}}$  is the new-customer multiplier,  $\alpha_S$  weights satisfaction extremity,  $\alpha_S$  gives extra weight to negative satisfaction,  $\alpha_S$  weights recent satisfaction changes,  $\alpha_S$  weights active service events,  $\Delta S_{i,t}$  is the satisfaction change, and  $\mathcal{E}_{i,t}$  is the set of active quality events such as outage, overload, issue, or quota frustration. The simulator samples up to  $K_{\mathrm{post}}$  posts per day from these candidates, so social media is a noisy but informative public signal rather than a complete survey. This simulates the selection bias of public feedback: large, influential, newly acquired, or upset customers are more likely to be heard than a random satisfied user.

Agent-authored posts are judged per discovered group. For group g, let  $e_{g,t}^{\text{agent}} \in [-1,1]$  be the judged reaction score. The social multiplier entering acquisition is

$$A_{g,t} = \operatorname{clip}\left(A_0 + \alpha_A e_{g,t}^{\operatorname{agent}} V_{g,t}, A_{\min}, A_{\max}\right), \tag{27}$$

where  $e_{g,t}^{\text{agent}}$  is the judged reaction of group g to the agent's post,  $V_{g,t}$  is exposure,  $A_0$  is neutral social effect,  $\alpha_A$  converts reaction-weighted exposure into lead impact, and  $A_{\min}$ ,  $A_{\max}$  bound the multiplier. Public communication can therefore help or hurt growth depending on how each group reacts. This simulates product marketing and public relations: a message that resonates with one segment can accelerate acquisition, while a poorly received message can suppress demand.

**Daily new-customer generation.** For discovered target group *g*, expected leads are

$$\lambda_{g,t} = R_{g,t} D_{g,t} C_t M_{g,t} A_{g,t} Z_t \left( \sum_{c} \frac{x_{c,g,t} L_{c,g,t}}{x_{ad}} + \sum_{h} N_{h,t} W_{h,g}^{net} \right), \tag{28}$$

where  $R_{g,t}$  is reputation,  $D_{g,t}$  is market availability,  $C_t$  is the calendar-cycle multiplier,  $M_{g,t}$  is the macro lead multiplier,  $A_{g,t}$  is the agent-social multiplier,  $Z_t$  is the active demand-surge multiplier,  $x_{c,g,t}$  is channel spend,  $L_{c,g,t}$  is leads per reference ad spend  $x_{ad}$ ,  $N_{h,t}$  is subscribers in group h, and  $W_{h,g}^{net}$  is the referral matrix. The calendar-cycle multiplier makes demand oscillate through recurring seasonal cycles, so otherwise identical ad spend can perform better or worse depending on timing. The macro multiplier captures broad economic expansion or contraction; the social and surge multipliers capture communication effects and temporary external demand spikes; and the referral term captures word of mouth from existing subscribers. Market saturation is

$$D_{g,t} = \left[ D_0 - \left( \frac{N_{g,t}}{\operatorname{cap}_{g,0}(\alpha_{\operatorname{cap}} + \gamma_g t / Y_{\operatorname{cap}})} \right)^{\nu_D} \right]_+, \qquad n_{g,t} \sim \operatorname{Poisson}([\lambda_{g,t}]_+).$$
 (29)

 $D_0$  is baseline availability,  $N_{g,t}$  is the current number of customers in group g, cap  $_{g,0}$  is initial market capacity,  $\alpha_{\text{cap}}$  is the baseline capacity scale,  $\gamma_g$  is group capacity growth,  $Y_{\text{cap}}$  is the time scale for capacity growth,  $\nu_D$  controls saturation curvature,  $\lambda_{g,t}$  is expected leads, and  $n_{g,t}$  is realized leads. The positive-part operator prevents negative availability, and the Poisson draw converts the expected funnel volume into noisy realized leads. This combines paid acquisition, word of mouth, reputation, macro conditions, seasonal demand, temporary shocks, and finite market size. The mechanism simulates a real go-to-market funnel where the same budget can yield different outcomes depending on brand, timing, segment saturation, and randomness.

**Demand surges.** External demand surges are temporary acquisition shocks. For each active surge s,

$$Z_t = \prod_{s \in \mathcal{S}_t} z_s, \qquad z_s \sim \mathcal{D}_s^{\text{surge}}, \qquad t \in [t_s^{\text{start}}, t_s^{\text{end}}).$$
 (30)

 $S_t$  is the set of active surges,  $z_s$  is the surge lead multiplier sampled from surge distribution  $\mathcal{D}_s^{\text{surge}}$ , and  $t_s^{\text{start}}$ ,  $t_s^{\text{end}}$  are its active days. The product over active surges allows multiple external events to stack. Surges create temporary windows where growth is easier, but the agent must still have pricing, quality, and capacity to retain the acquired customers. This simulates events such as press attention, industry shifts, or sudden demand spikes that increase inbound interest without guaranteeing durable revenue.

## <span id="page-26-0"></span>A.6 Market Discovery and Non-Stationarity

**Market and group research.** Market research reveals new customer groups, while group research increases the information level for a known group after a delay:

$$\ell_{g,t+D_{o,\ell}^{\text{research}}}^{\text{info}} = \max(\ell_{g,t}^{\text{info}}, \ell_{g,\ell}^{\text{target}}), \qquad D_{g,\ell}^{\text{research}} \sim \mathcal{D}_{g,\ell}^{\text{research}}. \tag{31}$$

 $\ell_{g,t}^{info}$  is the agent-visible information level for group g,  $\ell_{g,t}^{target}$  is the requested level,  $D_{g,\ell}^{research}$  is the configured completion delay, and  $\mathcal{D}_{g,\ell}^{research}$  is the delay distribution for that group and research depth. The max operator means research can raise the information level but cannot erase already acquired knowledge. Results snapshot current market conditions when the research completes. The purpose is to make information acquisition an operational choice with time cost rather than a free static table. This simulates customer discovery, analyst work, and market research projects that improve visibility only after a delay and may already be slightly stale when delivered.

**Competitor events.** Competitor events are disabled before  $t_{\text{comp}}^{\text{start}}$  and after  $t_{\text{comp}}^{\text{end}}$ . Let  $\tau$  be the last event day. The mean interval is

$$\bar{\Delta}_t = \begin{cases} m_{\Delta}\Delta, & t < t_{\Delta}^{\text{switch}}, \\ \Delta, & t \ge t_{\Delta}^{\text{switch}}, \end{cases}$$
(32)

with a separately configured minimum interval  $\Delta_{\min}$ . If  $t - \tau < \Delta_{\min}$ , no event occurs; otherwise

$$E_t \sim \text{Bernoulli}(1/\bar{\Delta}_t).$$
 (33)

When an event occurs, a base boost is sampled and scaled over the run:

$$B_{t}^{\text{sample}} = \text{clip}(\text{LogNormal}(\mu_{B}, \sigma_{B}), B_{\text{min}}, B_{\text{max}}) \left(\alpha_{B} + \rho_{B} \frac{t - t_{B}^{\text{start}}}{T_{B}^{\text{ramp}}}\right). \tag{34}$$

 $t_{\rm comp}^{\rm start}$  and  $t_{\rm comp}^{\rm end}$  bound the active competitor window,  $\tau$  is the last event day,  $\tilde{\Delta}_t$  is the current mean interval between competitor events,  $E_t$  is the event indicator,  $m_{\Delta}$  slows early events,  $\Delta$  is the baseline interval,  $t_{\Delta}^{\rm switch}$  is the interval switch day, and  $\Delta_{\rm min}$  prevents events from arriving too close together.  $\mu_B$ ,  $\sigma_B$  parameterize event size,  $B_{\rm min}$ ,  $B_{\rm max}$  bound it,  $t_B^{\rm start}$  is the boost-ramp start day, and  $\alpha_B$ ,  $\rho_B$ ,  $T_B^{\rm ramp}$  control magnitude scaling over the run. Together these terms simulate rival launches that are not perfectly periodic, but become more serious as the market matures. The simulator also models adaptive competitor catch-up to the agent's unreleased global development and R&D gains. Let  $H_t^{\rm global}$  be the unreleased shared-quality bank. With  $u_t^{\rm global} \sim {\rm Uniform}(u_{\rm min}^{\rm global}$ ,  $u_{\rm max}^{\rm global}$ ),

$$B_{t} = \max\left(B_{t}^{\text{sample}}, u_{t}^{\text{global}} H_{t}^{\text{global}}\right), \qquad H_{t+}^{\text{global}} = H_{t}^{\text{global}} - \mathbb{1}\left\{u_{t}^{\text{global}} H_{t}^{\text{global}} > B_{t}^{\text{sample}}\right\} u_{t}^{\text{global}} H_{t}^{\text{global}}. \quad (35)$$

Thus  $B_t$  is the applied competitor quality boost,  $B_t^{\text{sample}}$  is the exogenous shock,  $u_t^{\text{global}}$  is the random catch-up fraction, and  $H_{t+}^{\text{global}}$  is the remaining shared-quality bank after the event. The event boost is at least the stationary sampled shock but can be larger when the agent has accumulated large unreleased global improvements. If the adaptive term wins, the competitor consumes that fraction of the bank. This simulates competitors copying or matching broadly visible product improvements: large general advances can invite stronger competitive responses than small incremental changes. Targeted development has a parallel group-specific adaptive component:

$$D_{g,t}^{\text{target}} = v_{g,t} H_{g,t}^{\text{target}}, \qquad v_{g,t} \sim \text{Uniform}(v_{\min}, v_{\max}), \qquad H_{g,t+}^{\text{target}} = H_{g,t}^{\text{target}} - D_{g,t}^{\text{target}}, \tag{36}$$

where  $H_{g,t}^{\text{target}}$  is the unreleased targeted-development bank,  $v_{g,t}$  is the group catch-up fraction sampled between  $v_{\min}$  and  $v_{\max}$ ,  $D_{g,t}^{\text{target}}$  is the targeted drift shock, and  $H_{g,t+}^{\text{target}}$  is the remaining targeted bank after catch-up. The applied event shifts all customers' curves upward by adding  $B_t$  to global quality expectation,  $\kappa_g B_t$  to group g's expectation, and  $D_{g,t}^{\text{target}}$  to group g's expectation. Here  $\kappa_g$  is group competitor reactivity. The intuition is that competitors are partly exogenous and partly responsive: broad R&D attracts broad catch-up, while targeted work is harder for competitors to fully copy but can still leak into group expectations. This simulates real competitive pressure where segment-specific improvements can create more durable advantage than broad, easily observed product gains.

**Macroeconomic schedule.** The hidden macro state is an Ornstein–Uhlenbeck process around a sinusoidal PMI cycle (Uhlenbeck and Ornstein, 1930; Szimayer and Maller, 2004; Koenig, 2002):

$$\mu_t = \mu_{\text{PMI}} + A_{\text{PMI}} \sin(2\pi t / P_{\text{PMI}} + \phi),$$

$$\text{PMI}_{t+1} = \text{clip}(\text{PMI}_t + \eta_{\text{PMI}}(\mu_t - \text{PMI}_t) + \sigma_{\text{PMI}}\epsilon_t, \text{PMI}_{\text{min}}, \text{PMI}_{\text{max}}).$$
(37)

with  $\epsilon_t \sim \mathcal{N}(\mu_\epsilon, \sigma_\epsilon^2)$ .  $\mu_t$  is the current cycle target,  $\mu_{\text{PMI}}$  is the baseline PMI,  $A_{\text{PMI}}$  is cycle amplitude,  $P_{\text{PMI}}$  is cycle period,  $\phi$  is phase,  $\eta_{\text{PMI}}$  is mean-reversion speed,  $\sigma_{\text{PMI}}$  is shock scale, and PMI<sub>min</sub>, PMI<sub>max</sub> bound the index. Intuitively, demand oscillates through a PMI-like expansion-and-contraction cycle, while the OU update makes temporary surprises fade back toward the current cycle phase. This simulates macroeconomic background conditions that drift gradually but also contain noise. For each customer group and macrosensitive dimension d,

$$M_{g,d,t} = \max\left(M_{\min}, M_0 + \beta_{g,d} \frac{\text{PMI}_t - \text{PMI}_0}{\text{PMI}_0}\right). \tag{38}$$

 $M_{g,d,t}$  is the macro multiplier,  $M_0$  is neutral,  $M_{\min}$  is its floor,  $\beta_{g,d}$  is group sensitivity, and PMI<sub>0</sub> is the neutral PMI reference. The dimension d can represent macro-sensitive quantities such as lead flow, willingness to pay, or enterprise deal velocity, and different groups react with different sensitivities. The simulator uses real-time hidden PMI internally, while the agent sees only period averages published every  $D_{\text{publish}}$  days with delay  $D_{\text{delay}}$ . This simulates management under delayed economic indicators: the world has already moved before the agent receives clean macro data.

#### A.7 Enterprise Sales and Negotiation

**Offer evaluation.** Enterprise customers evaluate up to  $K_{\text{offer}}$  offered (plan, price) options and choose the one with highest

$$S_i^{\text{offer}} = Q_{i,p,t}^{\text{perc}} - Q_i^{\text{req}}(C), \tag{39}$$

where  $K_{\text{offer}}$  is the maximum number of options the agent can present,  $Q_{i,p,t}^{\text{perc}}$  is the perceived quality of the offered plan,  $Q_i^{\text{req}}(C)$  is the required quality at price C, and  $S_i^{\text{offer}}$  is offer surplus. Positive surplus means the proposed plan clears the customer's price-quality bar. If the best offer is positive, the customer accepts.

This simulates enterprise procurement evaluating a small menu of contract options rather than passively accepting a list price. Otherwise, the simulator computes

$$C_i^{\max}(Q) = \max\{C \le c_i : Q_i^{\text{req}}(C) \le Q\}$$

$$\tag{40}$$

where  $C_i^{\max}(Q)$  is the highest price the customer would accept at perceived quality Q,  $c_i$  is the customer's budget ceiling, and the max operator searches for the price that is still justified by the offered quality. This is the reservation price implied by the same participation curve used for self-serve customers. This simulates a procurement ceiling: the customer may negotiate, but there is a maximum contract value that the perceived product quality can support. With sampled initial factor  $f_i$  and configured counter-offer decay  $\gamma_{\alpha}$ ,

$$C_{i,r}^{\text{counter}} = C_i^{\text{max}} - \gamma_{\alpha}^r \left( C_i^{\text{max}} - f_i C_i^{\text{max}} \right), \tag{41}$$

where  $C_{i,r}^{\text{counter}}$  is the counter-offer on turn r,  $f_i$  is the initial counter-offer fraction of the customer's maximum acceptable price, and  $\gamma_{\alpha}$  controls how quickly later counter-offers approach that maximum. Early counter-offers start below true willingness to pay; later turns move toward the customer's maximum acceptable price. If the configured maximum turn count is exceeded, the customer stops responding. This simulates negotiation anchoring: buyers may reveal willingness to pay gradually rather than immediately offering their ceiling. Reply delays are also stochastic:

$$d_{i,r}^{\text{reply}} \sim \mathcal{D}_i^{\text{reply}} \left( \bar{d}_i / M_{g,\text{deal},t}, \sigma_i^d \right),$$
 (42)

where  $d_{i,r}^{\text{reply}}$  is the delay before the customer responds,  $\bar{d_i}$  and  $\sigma_i^d$  are customer response-time parameters,  $\mathcal{D}_i^{\text{reply}}$  is the customer-specific reply-delay distribution, and  $M_{g,\text{deal},t}$  is the macro deal-velocity multiplier. Stronger macro conditions shorten expected delay by increasing the denominator, while slow conditions stretch sales cycles. This makes enterprise sales slower and less certain than self-serve conversion while still following the same underlying price-quality logic. The mechanism simulates procurement latency, stakeholder review, and macro-sensitive sales velocity.

#### <span id="page-28-0"></span>A.8 Costs and Cash Flow

**Daily costs.** Daily operating cost combines fixed infrastructure, variable compute, operations, development, advertising, targeted actions, lead acquisition, and research charges:

$$K_{t}^{\text{cost}} = K_{\kappa_{t}}^{\text{capacity}} + \sum_{p} \chi_{p}^{\text{usage}} U_{p,t}^{\text{use}} + x_{t}^{\text{ops}} + x_{t}^{\text{dev}} + X_{t}^{\text{target-ops}} + \sum_{g} x_{g,t}^{\text{target-dev}} + \sum_{c,g} x_{c,g,t}^{\text{ads}} + N_{t}^{\text{lead}} c^{\text{lead}} + K_{t}^{\text{market}} + K_{t}^{\text{group}} + K_{t}^{\text{project}}$$

$$(43)$$

 $K_{\kappa_t}^{\mathrm{capacity}}$  is the fixed cost of capacity tier  $\kappa_t$ ,  $\chi_p^{\mathrm{usage}}$  is per-usage cost for plan p,  $U_{p,t}^{\mathrm{usage}}$  is usage on that plan,  $x_t^{\mathrm{ops}}$  and  $x_t^{\mathrm{dev}}$  are global operations and development spend,  $X_t^{\mathrm{target-ops}}$  is targeted support spend,  $\sum_g x_{g,t}^{\mathrm{target-dev}}$  is targeted development spend across groups,  $\sum_{c,g} x_{c,g,t}^{\mathrm{ads}}$  is acquisition advertising spend across channels and groups,  $N_t^{\mathrm{lead}} c^{\mathrm{lead}}$  is the per-lead acquisition charge, and the three K terms are market research, group research, and research-project charges paid that day. This cost equation simulates the operating budget of a software company, where fixed infrastructure, variable compute, staffing, marketing, and research all consume cash through different channels. The cash update is

$$B_{t+1} = B_t + Y_t^{\text{sub}} + \sum_i Y_{i,t}^{\text{ads}} - K_t^{\text{cost}},$$
 (44)

<span id="page-28-1"></span>where  $B_t$  is company cash,  $Y_t^{\mathrm{sub}}$  is subscription revenue,  $\sum_i Y_{i,t}^{\mathrm{ads}}$  is in-product ad revenue, and  $K_t^{\mathrm{cost}}$  is total operating cost. This is the main strategic coupling in the simulator: growth, quality, and reliability can create future revenue, but they consume cash immediately. The mechanism simulates startup runway management, where the agent must decide when to burn cash for future growth and when to preserve liquidity to avoid bankruptcy.

# **B Rule-Based Baseline Strategy and Configuration Search**

We use the rule-based baseline as a non-LLM point of comparison for the agent results in Section [3.2.](#page-8-1) The baseline is intentionally simple: it commits to a fixed pricing book, fixed product-quality and advertising spend levels, and a fixed customer targeting rule. It does not use market research, enterprise negotiation, social media analysis, promotions, or language-model calls.

At the start of a run, the policy sets prices, model tiers, and usage quotas from one price book. During each simulated week, it selects target customer groups from its target rule. If cash is above a configured floor, it applies a small global development spend of \$200/day, a fixed targeted development spend for each selected group, and, starting on day 20, a fixed targeted advertising spend for each selected group. Advertising is placed on the highest-yield channel for the selected group under the simulator's fixed channel table. Operations spend is set to max(100, 0.05*nt*) dollars/day, where *n<sup>t</sup>* is the current active subscriber count. The policy adjusts capacity by at most one tier per week toward the cheapest tier whose capacity covers recent average usage at 80% utilization. This simulates a simple operating playbook: spend proportionally to current scale, focus on a small target market, and avoid complex adaptation or hidden-state inference.

The configuration search is the Cartesian product of the options in Table [4,](#page-29-1) giving 24 configurations. Each configuration is evaluated for the full 500-day simulation with seed 42. The best configuration uses the mid price book, targets S1 only, uses the heavy spend package, and has a \$100K cash floor; the \$300K cash floor gives the same result for this seed. The traced replay of this configuration ends with \$15.76M in cash.

<span id="page-29-1"></span>

| Search dimension | Options                                                                                                                                                                                                                    |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Price book       | cheap:<br>mid:<br>A=\$8/T1/50K tokens,<br>B=\$18/T2/200K tokens,<br>C=\$40/T3/1M tokens;<br>A=\$12/T1/60K tokens, B=\$25/T2/250K tokens, C=\$55/T4/1.2M tokens.                                                            |
| Target rule      | S1 only: target S1 throughout the run; S1 then S3: target S1 initially, then target both S1 and S3<br>from day 30 onward.                                                                                                  |
| Spend package    | light:<br>S1<br>dev/ad=\$2K/\$250<br>per<br>day,<br>S3<br>dev/ad=\$1.5K/\$600<br>per<br>day;<br>medium:<br>S3 dev/ad=\$3K/\$1.2K; heavy:<br>S1 dev/ad=\$4K/\$500,<br>S1 dev/ad=\$6K/\$750,<br>S3 de<br>v/ad=\$4.5K/\$1.8K. |
| Cash floor       | Stop optional global development, targeted development, and advertising when cash is at or<br>below either \$100K or \$300K.                                                                                               |
| Fixed choices    | Advertising begins on day 20; capacity targets 80% utilization; market discovery and enterprise<br>actions are disabled; default competitor events remain active.                                                          |

**Table 4. Search space for the rule-based baseline.** The baseline search varies two price books, two target rules, three spend packages, and two cash floors, for 24 total configurations.

# <span id="page-29-0"></span>**C Comparison to Vending-Bench 2 Curves**

Vending-Bench 2 reports the average GPT-5.5 balance over five 365-day runs, with the leaderboard ending near \$7.5K from a \$500 starting balance [\(Backlund and Petersson,](#page-15-2) [2025b\)](#page-15-2). Its curve is comparatively steady: once the agent finds workable suppliers and products, gains can accumulate through repeated restocking and sales. In contrast, the best GPT-5.5 CEO-BENCH run begins with \$1M, falls to roughly \$430K by day 30 as it funds acquisition, development, capacity, and operations, and only later compounds to \$21.3M by the end of the run. This delayed-payoff structure makes local cash preservation an unreliable proxy for success and requires the agent to keep investing through long intervals where the benefits of its actions have not yet fully materialized.

![](_page_30_Figure_0.jpeg)

**Figure 17. GPT-5.5 cash trajectories in Vending-Bench 2 and CEO-BENC H.** Vending-Bench 2 reports an average trajectory over five 365-day runs, where cash grows relatively steadily from a \$500 starting balance. The best CEO-BENC H run starts at \$1M, draws down early to fund growth and product investment, and only later compounds to a much higher ending balance, illustrating the delayed-payoff structure of our simulator.

# <span id="page-30-0"></span>**D Upper Bound Final-Cash Estimate**

We use the estimated maximum final cash only to calibrate remaining headroom in CEO-BENC H. It is not a mathematical proof of optimality. The estimate has two stages. We first compute a pre-friction accounting subtotal by summing revenue from all customer groups under maximum supportable pricing and subtracting the costs required by the simulator mechanics. We then apply a friction adjustment for issuedriven churn, enterprise negotiation friction, and acquisition delay. The reported estimate is the adjusted value, approximately \$2.2B.

**Objective.** Let *G* denote the 26 customer groups and let *B* = {30, 60, . . . , 480} denote the billing days. For each group *g*, let *N<sup>g</sup>* be the maximum attainable customer count or enterprise seat count, *p<sup>g</sup>* be the maximum supportable price, and *rg*(*t*) be the retention probability at billing day *t*. These terms define an optimistic full-market revenue calculation: how many customers can be reached, what price they can support, and how likely they are to remain active at each renewal. The pre-friction revenue estimate is

$$R = \sum_{g \in G} N_g p_g \sum_{t \in B} r_g(t). \tag{45}$$

Here *R* is total subscription revenue before execution frictions. The inner sum adds the retained billing opportunities for a group over time, and the outer sum aggregates across all customer segments. This simulates the revenue side of a best-case operating plan in which acquisition succeeds and retention is governed by the modeled quality checks. The pre-friction final-cash subtotal is then

$$C_{\text{pre}} = C_0 + R - K,\tag{46}$$

where *C*pre is final cash before friction adjustment, *C*<sup>0</sup> = \$1M is the initial cash balance, and *K* is the sum of all modeled simulator costs. This subtotal simulates accounting profit before execution slippage: revenue plus starting cash minus the cost of capacity, compute, development, operations, acquisition, and research. The reported estimate applies a friction factor *F*:

$$C_{\text{reported}} = FC_{\text{pre}}.$$
 (47)

where *C*reported is the final headroom estimate after friction and *F* is the multiplicative discount applied to the pre-friction subtotal. We use *F* = 0.49 to make the estimate conservative with respect to issue-driven churn, enterprise negotiation friction, and acquisition delay. This simulates the gap between a clean accounting upper bound and a real execution path, where customers do not all arrive instantly, enterprise deals take negotiation, and support issues can erode retention.

**Parameter choices.** The accounting assumes all 26 groups are retained through all billing cycles before friction adjustments. The selected configuration uses T3 inference, T7 capacity, \$40K/day in global development, targeted development for every group, all ten R&D tiers started in parallel on day 1, and operations spending of \$500/day plus \$0.001 per active subscriber. These choices were selected from a small grid over targeted-development slack, model tier, global-development spend, R&D schedule, capacity tier, and operations spend. The most sensitive parameter is targeted development: a  $1-2\times$  multiplier did not reliably retain all groups late in the run, while a  $3\times$  multiplier maintained full-cycle retention in the tested configurations and a  $4\times$  multiplier added cost without improving retention.

**Quality and retention check.** For each candidate configuration, we compute the shared-quality, competitor-drift, and R&D-bonus trajectories over the operating horizon. For group *g*, targeted-development spend is first sized to cover the late-run quality threshold,

$$T_g^{(0)} = 5000 \left[ \exp\left(\frac{\Delta_g}{0.7A_g \cdot 0.0225}\right) - 1 \right],$$
 (48)

where  $T_g^{(0)}$  is the one-pass targeted-development spend estimate for group g,  $\Delta_g$  is the required targeted quality bonus after accounting for shared quality and R&D effects,  $A_g$  is the number of active development days, 5000 is the spend scale from the simulator's targeted-development rule, 0.7 is the targeted-development conversion coefficient used in this sizing approximation, and 0.0225 is the quality-gain coefficient. The exponential is the inverse of the simulator's log diminishing-returns function: larger required quality gaps require disproportionately more spend. We then use  $T_g = 3T_g^{(0)}$  to account for group-level drift feedback that the one-pass sizing rule does not capture. This simulates planning with safety margin, where an operator overbudgets targeted product work because competitors and market drift can raise the bar during execution. At each billing day, retention is computed from the delivered-quality cushion,

$$r_g(t) = \Phi\left(\frac{m[q_0 + q_{\text{shared}}(t) + b_g(t)] - d_g(t) - \ell(t) - \mu_g}{\sigma_g}\right),\tag{49}$$

where  $r_g(t)$  is group retention probability at billing day t,  $\Phi$  is the standard normal cumulative distribution function, m=0.90 is the T3 quality multiplier,  $q_0$  is baseline quality,  $q_{\rm shared}(t)$  is shared quality from global development and R&D,  $b_g(t)$  is the targeted group bonus,  $d_g(t)$  is fixed and competitor-induced group drift,  $\ell(t)$  is the capacity-overload penalty, and  $(\mu_g,\sigma_g)$  parameterize the group's quality threshold distribution. The numerator is the quality cushion above the group's threshold, and dividing by  $\sigma_g$  converts that cushion into a probability under the assumed threshold distribution. Under the selected configuration, the computed retention check gives  $r_g(t)\approx 1$  for all 26 groups and all 16 billing cycles. Full retention implies approximately 521M usage units per day; with T7 capacity, the resulting overload penalty is included in  $\ell(t)$ . This simulates a stress test for whether product quality, targeted improvements, and capacity are strong enough to keep every segment through repeated renewals.

**Revenue and costs.** The pre-friction calculation gives \$6.69B in subscription revenue: \$1.93B from individual groups and \$4.76B from enterprise groups. We subtract every cost category used by the simulator rather than only direct infrastructure costs. Table 5 shows the resulting cost accounting. This paragraph simulates the full-company accounting view of the upper bound: high revenue is meaningful only after paying for the compute, capacity, product work, support, advertising, and information acquisition required to keep that revenue.

**Interpretation.** The final row of Table 5 is the estimate used in the main text and in Table 3. It should be read as an approximate headroom calculation, not as a demonstrated executable strategy. The pre-friction accounting assumes full conversion, full enterprise close rates, rapid acquisition, maximum supportable prices, mean R&D timing and quality effects, and no additional losses from unresolved customer issues, discounts, reputational effects, or cash-flow constraints beyond the cost categories above. The friction factor makes the estimate conservative by reducing this subtotal to roughly \$2.2B. This remains far above the best observed agent performance and supports the conclusion that CEO-BENCH is far from saturated.

<span id="page-32-0"></span>

| Quantity                          | Amount (\$M) |
|-----------------------------------|--------------|
| Subscription revenue              | 6,690.0      |
| Initial cash                      | 1.0          |
| Compute                           | 1,554.0      |
| Capacity                          | 37.3         |
| Global development                | 19.9         |
| Targeted development              | 423.6        |
| R&D projects                      | 9.2          |
| Advertising                       | 114.8        |
| Lead acquisition                  | 0.9          |
| Operations                        | 2.5          |
| Market research                   | 1.5          |
| Group research                    | 1.0          |
| Total modeled costs               | 2,164.7      |
| Pre-friction ending cash subtotal | 4,526.3      |
| Friction adjustment factor        | ×0.49        |
| Estimated final cash upper bound  | 2,200.0      |

**Table 5.** Accounting for the estimated final cash upper bound of \$2.2B after adjustments for execution frictions.