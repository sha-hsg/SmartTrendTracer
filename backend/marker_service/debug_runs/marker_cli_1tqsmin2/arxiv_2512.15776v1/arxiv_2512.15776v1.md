## Emergence: Overcoming Privileged Information Bias in Asymmetric Embodied Agents via Active Querying

## Shaun Baek and Sam Liu and Joseph Ukpong

Emory University

## Abstract

Large Language Models (LLMs) act as powerful reasoning engines but struggle with "symbol grounding" in embodied environments, particularly when information is asymmetrically distributed. We investigate the *Privileged Information Bias* (or "Curse of Knowledge"), where a knowledgeable "Leader" agent fails to guide a sensor-limited "Follower" due to a lack of Theory of Mind. To quantify this phenomenon, we propose a novel Asymmetric Assistive Reasoning framework within AI2-THOR. Our experiments reveal a significant "Success Gap": while the Leader successfully perceives the target in 35.0% of episodes, the collaborative team succeeds only 17.0% of the time, implying that nearly 50% of feasible plans fail solely due to communicative grounding errors. We demonstrate that a "Pull-based" protocol (active querying) is significantly more robust than standard "Push-based" instruction, with successful episodes featuring 2x the frequency of clarification requests. This research isolates the mechanism of *active uncertainty reduction* as a prerequisite for safe human-AI and robot-robot collaboration.

## 1 Introduction

While Large Language Models (LLMs) demonstrate remarkable symbolic reasoning, they effectively operate as "brains in a jar." Trained on vast static datasets—a paradigm often termed "Internet AI" [\(Duan et al.,](#page-9-0) [2022\)](#page-9-0)—these models lack the proprioceptive feedback loops required to understand physical constraints. They can describe a kitchen, but they cannot inherently reason about who can see the fridge and who cannot [\(Ahn et al.,](#page-8-0) [2022;](#page-8-0) [Khan and Waheed,](#page-9-1) [2025\)](#page-9-1).

This limitation is not merely physical; it is social. In collaborative environments, this disembodiment creates a critical failure mode: the inability to model a partner's perspective. When a knowledgeable agent assumes its partner shares

its global view, it succumbs to *Privileged Information Bias*, or the "Curse of Knowledge" [\(Camerer](#page-9-2) [et al.,](#page-9-2) [1989\)](#page-9-2). Despite the push toward Embodied AI [\(Ramrakhya et al.,](#page-10-0) [2025;](#page-10-0) [Mecattaf et al.,](#page-9-3) [2025\)](#page-9-3), current frameworks often assume homogeneous agents with shared perception, neglecting the friction that arises when agents must negotiate distinct realities [\(Du et al.,](#page-9-4) [2025\)](#page-9-4).

We address this gap by embedding a pre-trained LLM into a Leader-Follower dyad within the AI2- THOR simulation environment [\(Kolve et al.,](#page-9-5) [2017\)](#page-9-5). We introduce an Asymmetric Assistive Reasoning task where a "Leader" with full vision must guide a "Follower" with severe visual impairments. This asymmetry forces the LLM to negotiate information gaps rather than simply plan actions. To measure the impact of communication protocols, we contrast a standard "Push-based" instruction model against a "Pull-based" active querying protocol.

Our experiments reveal a stark "Success Gap." While the Leader agent successfully perceives and navigates to targets in 35.0% of episodes, the collaborative team succeeds only 17.0% of the time. This 18-point drop indicates that nearly half of all feasible plans fail solely due to communicative grounding errors. We demonstrate that these failures stem from open-loop instruction, where the Leader issues commands based on an egocentric view (e.g., "turn left" relative to itself). By shifting to a "Pull-based" protocol, where the Follower actively flags ambiguities, the team mitigates the Curse of Knowledge and restores performance.

This work makes the following contributions:

- Quantifying the Gap: We identify a quantitative "Success Gap," establishing that 50% of feasible navigation plans fail due to grounding errors rather than execution capability.
- Protocol Evaluation: We demonstrate that a "Pull-based" active querying protocol signif-

icantly outperforms open-loop instruction in resolving Privileged Information Bias.

• Framework: We provide a reproducible Asymmetric Assistive Reasoning framework for evaluating Theory of Mind and perspective-taking in embodied LLMs.

Broader Impacts: Beyond simulation, this research highlights a necessary evolution for assistive robotics. For autonomous systems to safely collaborate with human users—who possess distinct perceptual and physical constraints—they must move beyond blind obedience and develop the capacity to recognize and resolve information asymmetry.

## 2 Related Work

Research related to this work addresses the convergence of Embodied AI, Multi-Agent Collaboration, and the specific cognitive failures of Large Language Models (LLMs) when grounded in asymmetric physical realities.

#### 2.1 The Grounding Problem in AI

The inability of LLMs to robustly reason about physical dynamics is classically framed as the symbol grounding problem [\(Harnad,](#page-9-6) [1990\)](#page-9-6). While LLMs excel in processing symbolic sequences, their reliance on static datasets leaves them fundamentally disembodied [\(Ahn et al.,](#page-8-0) [2022;](#page-8-0) [Khan](#page-9-1) [and Waheed,](#page-9-1) [2025\)](#page-9-1). This limitation prevents them from intrinsically connecting linguistic tokens with physical actions or understanding cause-and-effect relationships.

Recent critiques suggest that this disembodiment leads to a "superficial" Theory of Mind, where models match behavioral patterns without maintaining a coherent internal world model [\(Hu et al.,](#page-9-7) [2025\)](#page-9-7). To bridge this, recent efforts have attempted to augment LLMs with grounding mechanisms that connect abstract language to sensorimotor experiences [\(Lake et al.,](#page-9-8) [2017\)](#page-9-8), yet these approaches often treat grounding as a single-agent perception task rather than a social negotiation.

## 2.2 Embodied AI and 3D Simulation Platforms

To address the shortcomings of "Internet AI" [\(Duan](#page-9-0) [et al.,](#page-9-0) [2022\)](#page-9-0), the embodied paradigm emphasizes evaluation within interactive environments. Platforms such as AI2-THOR [\(Kolve et al.,](#page-9-5) [2017\)](#page-9-5), Habitat [\(Savva et al.,](#page-10-1) [2019\)](#page-10-1), and VirtualHome [\(Puig](#page-10-2)

[et al.,](#page-10-2) [2018\)](#page-10-2) enable agents to practice navigation and manipulation.

However, these platforms traditionally focus on single-agent physics. While recent World Foundation Models (WFMs) like Google's Genie [\(Bruce](#page-9-9) [et al.,](#page-9-9) [2024\)](#page-9-9) and Meta's V-JEPA 2 [\(Assran et al.,](#page-9-10) [2025\)](#page-9-10) allow agents to predict temporal dynamics, they predominantly model physical causality (e.g., "if I drop this, it falls") rather than social causality (e.g., "if I say this, will my partner understand?"). Our work specifically targets this communication layer, evaluating how agents resolve ambiguity when their physical world models diverge.

## 2.3 Multi-Agent Collaboration and Asymmetry

LLMs have increasingly served as the cognitive core for Multi-Agent Systems (MAS) [\(Ferrag et al.,](#page-9-11) [2025;](#page-9-11) [Wang et al.,](#page-10-3) [2024\)](#page-10-3). Recent frameworks like CoELA [\(Zhang et al.,](#page-10-4) [2024\)](#page-10-4) and ProAgent [\(Zhang](#page-10-5) [et al.,](#page-10-5) [2025\)](#page-10-5) have demonstrated that LLMs can coordinate decentralized control in complex environments. Similarly, Sun et al. [\(Sun et al.,](#page-10-6) [2025\)](#page-10-6) benchmarked LLMs in *Overcooked-AI*, identifying significant deficits in active collaboration.

A critical limitation in frameworks such as CaPo [\(Liu et al.,](#page-9-12) [2025\)](#page-9-12) and AdaTAMP [\(Baijal et al.,](#page-9-13) [2025\)](#page-9-13) is the assumption of homogeneous agents with shared global views. In contrast, our work addresses *asymmetric* collaboration, where agents must resolve "Belief State Divergence" arising from unequal sensor horizons. This creates a risk of "Bias Reinforcement," where unchecked dialogue amplifies errors rather than correcting them [\(Oh](#page-10-7) [et al.,](#page-10-7) [2025\)](#page-10-7). While Patania et al. [\(Patania et al.,](#page-10-8) [2025\)](#page-10-8) recently emphasized "Pull-based" interaction to resolve such ambiguities, we extend this by operationalizing it within a strictly sensor-limited dyad to quantify the exact "Success Gap" caused by the Curse of Knowledge.

## 2.4 Theory of Mind in Robotics

Effective communication requires simulating the perspective of less-informed partners—a capability often absent in LLMs [\(Li et al.,](#page-9-14) [2023\)](#page-9-14). In robotics, this manifests as the "Curse of Knowledge," where a planner assumes its instructions are universally grounded [\(Camerer et al.,](#page-9-2) [1989\)](#page-9-2).

Recent studies attempt to minimize this bias via "Devil's Advocate" agents [\(Lee et al.,](#page-9-15) [2025\)](#page-9-15) or diverse agent personalities [\(Hsu et al.,](#page-9-16) [2025\)](#page-9-16). However, [Li et al.](#page-9-14) [\(2023\)](#page-9-14) note that LLMs frequently

![](_page_2_Figure_0.jpeg)

Figure 1: The Leader-Follower Architecture. The Leader utilizes global perception (SL) to "push" instructions, while the Follower utilizes local verification (S<sup>F</sup> ) to "pull" clarification. The shared LLM core iteratively generates the internal monologue for both roles.

"hallucinate" shared knowledge in long-horizon tasks. Our framework applies these theories to embodied spatial reasoning. Rather than relying on abstract personalities, we utilize an Advocate-Critic loop to mechanically force uncertainty reduction through active querying, converting the abstract theory of mind failure into a measurable navigation cost.

## <span id="page-2-0"></span>3 Approach

We formalize the problem of asymmetric collaboration as a partially observable multi-agent pathfinding task where communication is the only bridge between a global planner and a local executor. Unlike standard multi-agent reinforcement learning (MARL) setups that rely on shared reward gradients, our framework utilizes a centralized Large Language Model (LLM) to simulate two distinct cognitive processes—a "Leader" and a "Follower"—within a shared context window.

## 3.1 Problem Formulation

We define a dyad consisting of two agents, A<sup>L</sup> (Leader) and A<sup>F</sup> (Follower), operating in a shared environment E. The agents share a high-level goal G (e.g., "Find the Apple"), but possess distinct observability constraints:

- Leader State (SL): The Leader has access to the ground-truth state of the environment. This includes a semantic map of all objects O = {o1, o2, ..., on} and their exact global coordinates (x, y, z). The Leader acts as the *Global Planner*, generating high-level waypoints based on SL.
- Follower State (S<sup>F</sup> ): The Follower operates

under severe perceptual constraints. Its observation is limited to an egocentric subset Olocal ⊂ O, containing only objects within a radius dview ≤ 2.0m and a field-of-view θ = 90◦ . The Follower acts as the *Local Verifier*, executing motor commands (Mstep, Mrotate) and validating plan feasibility against S<sup>F</sup> .

## 3.2 Architecture: Single-Core, Dual-Persona

To simulate the interaction without the latency of multi-model orchestration, we employ a Single-Core, Dual-Persona architecture. We utilize a single Gemini 2.5 Flash kernel that iteratively generates the internal monologue and external dialogue for both agents. The system prompt enforces a strict separation of knowledge: the model is explicitly forbidden from allowing the Follower persona to access the Leader's global state SL.

At each timestep t, the system constructs the context as:

$$C_t = [P_{sys}, H_{dial}, S_L^{(t)}, S_F^{(t)}]$$
 (1)

Where Psys is the role-defining system prompt and Hdial is the shared conversation history. The model then outputs a tuple (IL, A<sup>F</sup> ), where I<sup>L</sup> is the Leader's natural language instruction and A<sup>F</sup> is the Follower's response (either a physical action or a text query).

#### 3.3 Interaction Protocols: Push vs. Pull

We explicitly contrast two interaction modalities to measure the impact of active uncertainty reduction.

#### 3.3.1 The Push Protocol (Open-Loop)

In the "Push" condition (Method A), the interaction is unidirectional. The Leader broadcasts an instruction Ipush based on its global state SL. The Follower attempts to map Ipush directly to a physical action a ∈ A.

$$S_L \to I_{push} \to A_F(execute)$$
 (2)

This mimics standard instruction-following baselines where the agent suffers from *Egocentric Bias* [\(Camerer et al.,](#page-9-2) [1989\)](#page-9-2), assuming the instructor's perspective is universally valid.

#### 3.3.2 The Pull Protocol (Closed-Loop)

In the "Pull" condition (Method B), the Follower utilizes a Verification Module to check Ipush against its local constraints S<sup>F</sup> . If the instruction references an ungrounded landmark (e.g., "Go to the sofa" when no sofa is visible in S<sup>F</sup> ), the Follower triggers a "Pull" query Qpull.

$$S_L \to I_{push} \to \text{Verify}(S_F)$$

$$\xrightarrow{fail} Q_{pull} \to S_L(\text{Re-Ground})$$
(3)

This closes the loop, forcing the Leader to translate global coordinates into local, relative cues (e.g., "Turn right 90 degrees").

#### 3.4 Experimental Testbed

The framework is implemented in AI2-THOR [\(Kolve et al.,](#page-9-5) [2017\)](#page-9-5) using the ManipulaTHOR [\(Ehsani et al.,](#page-9-17) [2021\)](#page-9-17) asset subset. We enforce the asymmetry by ray-casting from the Follower's camera and filtering the returned object list to exclude any entity beyond the 2.0m horizon.

## 3.5 Algorithm

Algorithm [1](#page-3-0) formalizes this interaction. In the default "Push" state, the Leader broadcasts plans based on global perception (eglobal). The critical deviation occurs when the Follower's local verification fails (vcheck is ungrounded). This triggers the "Pull" branch, where a query Q is fed back into the Leader's planner (Madv).

## 4 Experiments

We designed an experiment to isolate the specific benefits of shared perception and guided instruction, comparing our Asymmetric Leader-Follower model against single-agent baselines in a controlled, replicable environment.

#### 4.1 Testbed and Task Design

We utilize the AI2-THOR simulation platform [\(Kolve et al.,](#page-9-5) [2017\)](#page-9-5), specifically the ManipulaTHOR subset [\(Ehsani et al.,](#page-9-17) [2021\)](#page-9-17), chosen for its high-fidelity physics and complex indoor clutter.

The task is Object-Goal Navigation: The agent must navigate from a random spawn point Pstart to a target object Otarget (e.g., "Find the Apple").

#### 4.1.1 Data Generation Pipeline

To ensure task validity (addressing the "impossible target" problem), we implemented a rigorous preprocessing pipeline using the environment's 'GetReachablePositions' API. We generated 1,320 candidate episodes and filtered them to enforce two constraints:

```
Algorithm 1: Asymmetric Leader-
Follower Framework
```

```
Input: Global state eglobal, Local state
       elocal, goal g
Output: Executed actions A
while Goal g is not achieved do
   Leader: Perceive global state eglobal
     and "Push" initial plan
     Ipush = Madv(eglobal, g);
   Follower: Verify Ipush against local
     constraints elocal
     vcheck = Mcrit(Ipush, elocal);
   if vcheck is grounded then
       Execution: Translate instruction for
         execution A = Mexec(Ipush);
   else
       Pull Protocol: Generate query Q to
         communicate local constraints
         Q = Mquery(Ipush, elocal);
       Re-Grounding: Leader revises plan
         based on Q
         Ipush = Madv(eglobal, g, Q);
   end
end
return A
```

- 1. Reachability: A valid nav-mesh path must exist between Pstart and Otarget.
- 2. Non-Triviality: The geodesic distance must be d > 1.5m to prevent the agent from spawning immediately in front of the goal.

From this filtered set, we randomly sampled a fixed Benchmark Set of 100 tasks across 4 room types (Kitchen, Bathroom, Living Room, Bedroom).

#### 4.2 Model Conditions

We evaluate three distinct policy conditions to quantify the "Collaboration Boost":

- 1. Baseline Agent (Egocentric Control): A single agent with full sensory perception (Ofull). This represents the *Performance Ceiling*.
- 2. Handicapped Agent (Sensory Control): A single agent operating under the Follower's constraints (Opartial, max view distance 2.0m). This establishes the *Zero-Shot Performance Floor*.
- 3. Two-Agent Dyad (Ours): The Leader-Follower framework described in Section [3.](#page-2-0)

![](_page_4_Figure_0.jpeg)

Leader View (Full Visibility)
12 objects visible

\* Target 'Apple' not visible

Follower View (Limited Visibility: 1.5m) 0 objects visible X Target 'Apple' not visible

![](_page_4_Picture_3.jpeg)

Privileged Agent 12 visible objects Handicapped Agent 0 visible objects

Figure 2: **Visualizing the Information Asymmetry (Task 23).** The **Leader** (left) perceives the full scene geometry (12 objects visible), identifying the target "Apple" relative to the room layout. The **Follower** (right) operates under a 2.0m visibility handicap (0 objects visible), seeing only a blank wall. This discrepancy creates the "Curse of Knowledge," where the Leader must infer the Follower's blindness to provide effective guidance.

#### 4.2.1 Model Development & Optimization

During preliminary development, we observed that larger models (e.g., Gemini Pro) frequently hallucinated object positions in the "Follower" role. We resolved this by switching to the 'gemini-2.5-flash' variant and enforcing a temperature of 0.0, which stabilized the coordinate-to-action mapping.

#### 4.3 Evaluation Metrics

We report results using standard Embodied AI metrics:

- Success Rate (SR): The percentage of episodes where the agent reaches  $d \leq 1.0$ m from the target. We selected the 1.0m threshold to align with the standard ALFRED benchmark success criteria (Shridhar et al., 2020).
- Average Steps to Success (STS): The average number of simulation steps (movement + rotation) taken to reach the goal. Note: This metric is calculated only over successful episodes to prevent maximum-length failures (T<sub>max</sub>) from artificially inflating the average, which would obscure efficiency gains.
- Success weighted by Path Length (SPL): A strict measure of path efficiency:  $\frac{1}{N} \sum_{i=1}^{N} S_i \frac{L_i}{\max(P_i, L_i)}$ , where  $L_i$  is the optimal path and  $P_i$  is the observed path.

• Collaboration Metrics: The volume of "Push" instructions (Leader) versus "Pull" queries (Follower).

#### 4.4 Quantitative Performance

We executed the full 100-task benchmark across all three conditions. The aggregate performance is summarized in Table 1, and the communication dynamics are detailed in Table 2.

<span id="page-4-0"></span>Table 1: Aggregate Performance. SPL represents path efficiency (higher is better). STS represents temporal cost (lower is better).

| <b>Policy Condition</b>   | Success Rate (SR) | Avg. STS | SPL  |
|---------------------------|-------------------|----------|------|
| Baseline Agent (Solo)     | 16.0%             | 4.44     | 0.14 |
| Handicapped Agent (Solo)  | 11.0%             | 4.36     | 0.09 |
| Two-Agent (Leader View)   | 35.0%             | 12.23    | -    |
| Two-Agent (Follower View) | 17.0%             | 7.24     | 0.15 |

<span id="page-4-1"></span>Table 2: Communication Analysis: The "Pull" protocol (active querying) is the primary driver of success, appearing 2x more frequently in successful episodes.

| Metric                                | Count / Episode |
|---------------------------------------|-----------------|
| Avg. Leader Instructions (on Success) | 24.41           |
| Avg. Leader Instructions (on Failure) | 25.99           |
| Avg. Follower Queries (on Success)    | 2.00            |
| Avg. Follower Queries (on Failure)    | 0.99            |
|                                       |                 |

#### 4.5 Diagnostic Analysis

#### 4.5.1 The Success Gap

Our results reveal a critical "Success Gap." While the Leader agent successfully perceives the target in 35.0% of episodes, the collaborative team succeeds only 17.0% of the time. This 18-point drop implies that nearly 50% of feasible plans fail during transmission. The Leader "knows" the path but fails to translate it into a grounded instruction the Follower can verify.

#### 4.5.2 Mechanism of Success: Push vs. Pull

Table [2](#page-4-1) isolates the mechanism of success. In successful episodes, the Follower issued 2.00 active queries per episode, compared to just 0.99 in failed episodes. Crucially, the volume of Leader instructions ("Push") remained constant (≈ 25) regardless of outcome. This confirms that success is not driven by *more* instructions, but by *more verification*.

#### 4.5.3 Qualitative Error Analysis

To investigate the root cause of the Success Gap, we audited failure trajectories. A representative failure occurred in Task 38 (Find the Apple):

- Leader State: Perceives the Apple on a table 5m away. Issues command: "Move Forward."
- Follower State: Facing a blank wall (distance 1.5m).
- Failure Mode: The Follower obeyed the "Move Forward" command blindly (Push protocol), colliding with the wall. In successful runs of similar tasks, the Follower utilized the Pull protocol to ask: "I see a wall. Which way is the table?" prompting the Leader to correct with "Turn Right 90 degrees."

This confirms that failures are rarely due to disobedience, but rather due to *ungrounded obedience* to egocentric instructions.

## <span id="page-5-0"></span>5 Analysis

The experimental evaluation of the "Emergence" framework isolates the specific friction points where the symbolic reasoning of Large Language Models (LLMs) conflicts with the hard constraints of a physics-rich environment. By embedding the Gemini-2.5-flash model in the AI2Thor environment, ManipulaTHOR, we move beyond measuring abstract reasoning to measuring grounded efficacy. The following analysis deconstructs the performance data stratified across the Baseline, Handicapped, and Two-Agent conditions, diagnosing the specific cognitive and communicative pathologies that persist in collaborative spatial reasoning.

#### 5.1 Performance Landscape

Our results establish a clear hierarchy of competence that quantifies both the "Sensory Tax" of the handicap and the "Collaboration Boost" of the Leader-Follower architecture.

![](_page_5_Figure_16.jpeg)

Figure 3: The baseline agent's performance (16.0% SR) illustrates the "Zero-Shot Ceiling," where success is largely determined by favorable spawn locations rather than systematic search.

![](_page_5_Figure_18.jpeg)

Figure 4: The handicapped agent's performance drop (to 11.0% SR) quantifies the "Sensory Tax," confirming that semantic reasoning cannot compensate for a lack of distal visual cues.

## 5.1.1 The Zero-Shot Ceiling and Semantic-Spatial Dissonance

The Baseline Agent, equipped with full visual acuity, achieved a Task Success Rate (SR) of 16.0%. To contextualize this figure, it must be weighed against the broader landscape of Embodied AI. State-of-the-art agents trained through Reinforcement Learning (RL) or Imitation Learning (IL) on AI2-THOR typically achieve a success rate ranging from 26% to over 70%, depending on training volume and pre-mapping capabilities [\(Ma et al.,](#page-9-18) [2024\)](#page-9-18). The disparity between our Baseline (16.0%) and these specialized agents highlights the "Zero-Shot Penalty." Unlike RL agents that build implicit collision policies through millions of trialand-error steps, the LLM agent relies entirely on semantic reasoning. The data suggest a Semantic-Spatial Dissonance: the agent possesses the semantic knowledge to identify a "refrigerator" but lacks the procedural "proprioception" to navigate the coordinate-level sequence required to reach it. The agent effectively operates as a "brain in a jar," translating high-level intent into low-level motor commands without a learned intuition for the environment's geometry.

#### 5.1.2 Quantifying the Sensory Tax

The Handicapped Agent condition simulated "reduced perception" by restricting visibility to 2.0 meters. This handicap induced a measurable performance degradation, dropping the SR from 16.0% to 11.0%. This 31.3% relative decline represents the "Sensory Tax"—the quantifiable cost of losing distal visual cues. Without the ability to spot landmarks, like couches or counters across the room, the agent was reduced to a stochastic local search, confirming that semantic intent cannot fully compensate for perceptual blindness.

![](_page_6_Figure_3.jpeg)

Figure 5: The impact of active querying: Successful episodes (Green) feature 2x the frequency of "Pull" requests compared to failed episodes (Red), validating the "Push-Pull" hypothesis.

## 5.1.3 The Collaboration Boost

The primary hypothesis was validated: the Two-Agent system successfully mitigated the sensory handicap. The Assisted Handicapped agent achieved an SR of 17.0%, recovering and slightly exceeding the performance of the fully sighted Baseline (16.0%). This 54.5% improvement over the solo handicapped condition confirms that the Leader successfully transferred spatial knowledge to the Follower, effectively acting as a remote sensory organ. However, the fact that the pair only matched the solo baseline suggests that collaboration is *restorative* rather than *additive*: it heals the disability but does not yet yield super-human performance.

## 5.2 Error Analysis

While the aggregate metrics show success, a deeper dive into the dyadic performance reveals a critical failure mode, which we term the "Success Gap."

## 5.2.1 The Leader-Follower Disconnect

A stark discrepancy exists between the Leader's perception and the Follower's execution:

• Leader Success Rate: 35.0%

• Follower (Assisted) Success Rate: 17.0%

• The Gap: 18.0 percentage points

In 35.0% of the episodes, the Leader agent successfully identified the target and navigated to it. Yet, in more than half of those successful instances, it failed to guide the Handicapped partner to the same destination. The 18-point gap signifies a failure in Theory of Mind (ToM). The Leader suffers from the "Curse of Knowledge"; it perceives the target (e.g., "Red Mug, 5m") and fails to simulate the belief state of the Follower, who perceives only "Wall, 1.5m." Consequently, the Leader issues instructions that are accurately grounded in its own reality but referentially ambiguous in the partner's reality [\(Patania et al.,](#page-10-8) [2025\)](#page-10-8).

## 5.2.2 The Push-Pull Hypothesis and the Price of Passivity

The communication logs provide the causal mechanism for this gap. We observed a constant volume of "Push" communication from the Leader (≈25 instructions/episode) across both success and failure cases. "Pushing" more instructions did not correlate with success.

Instead, success was entirely dependent on the "Pull" mechanism:

- Help Requests (Successful Episodes): 2.00 per episode
- Help Requests (Failed Episodes): 0.99 per episode

The 18.0% gap represents the "Price of Passivity." The 2:1 ratio in help requests indicates that the "Local Verifier" (Follower) is the linchpin of the architecture. In failed episodes, the low querying rate suggests the Follower failed to recognize its own divergence from the plan, treating the Leader's instructions as absolute truths rather than hypotheses requiring local verification. When the "Pull" mechanism is dormant, the dyad reverts to a naive "Blind

Leading the Blind" topology, where the Follower executes instructions that are physically impossible in its local frame.

# **5.2.3 Qualitative Analysis: The Anatomy of Miscommunication**

To determine if the 18.0% Success Gap resulted from the Follower ignoring commands or the Leader issuing ungrounded commands, we audited the conversation logs of failed episodes. We found that "Compliance Failure" (Follower ignoring a valid command) was rare. The predominant failure mode was "Blind Obedience to Hallucinated Relativity."

As illustrated in Table 3, the Leader frequently provides relative directions (e.g., "to your left") based on its *own* camera orientation, which differs from the Follower's. Without an active "Pull" query from the Follower to verify the reference frame, the Follower executes the command faithfully but incorrectly.

Root Cause Analysis (Task 38): In a representative failure case, the Leader perceived the Apple at coordinates (1.5, 0.5, 3.0) and issued the command "Move Left." The Follower, located at (1.5, 0.5, 1.5) and facing a wall, interpreted "Left" relative to its own orientation. This resulted in a collision. In contrast, successful dyads utilized the Pull mechanism to ask: "Which way is the Apple relative to the wall?" This query forced the Leader to perform **Frame Switching**, translating the egocentric instruction into an allocentric or landmarkbased cue (e.g., "Turn 90 degrees right away from the wall"). This confirms that the "Pull" mechanism enables success not just by re-grounding, but by forcing the Leader to abandon its egocentric reference frame.

<span id="page-7-0"></span>

| Metric             | Log Entry Example                                  |
|--------------------|----------------------------------------------------|
| Step               | 12                                                 |
| Leader View        | Target (Apple) visible at [x: 1.5, y: 0.5, z: 3.0] |
| Follower View      | Obstructed (Wall)                                  |
| Leader Instruction | "The apple is directly to your left. Move Left."   |
| Analysis           | Incorrect Grounding. The 'Left' is relative to     |
| •                  | the Leader's start position, not the Follower's    |
|                    | current orientation.                               |
| Follower Response  | "Moving Left."                                     |
| Result             | Collision with Wall (Episode Fail)                 |

Table 3: An example of "Privileged Information Bias" leading to Navigation Failure. The Follower obeys the command, but the command is ungrounded in the Follower's frame of reference.

# 5.3 Ablation Study: Temporal Horizon and Stability

To rigorously test the hypothesis that the 30-step limit ( $T_{max}=30$ ) artificially constrained performance, we conducted an ablation study by rerunning 91 failed tasks with the horizon extended to  $T_{max}=60$ .

<span id="page-7-1"></span>

| Agent       | 30-Step SR | 60-Step SR | Relative Imp. |
|-------------|------------|------------|---------------|
| Leader      | 28.6%      | 34.1%      | +19.2%        |
| Handicapped | 8.8%       | 14.3%      | +62.5%        |

Table 4: Results of the 60-step Ablation Study showing performance recovery.

As shown in Table 4, relaxing the temporal constraint resulted in a significant relative improvement, particularly for the Handicapped agent (+62.5%). This confirms that a subset of "failed" plans were viable but required longer horizons to converge.

However, a granular analysis of the recovered tasks reveals that simple "horizon truncation" is not the sole factor. Among the 7 newly successful Handicapped episodes, only 1 (14.3%) actually required more than 30 steps. The remaining 6 succeeded in < 30 steps during the re-run. This indicates that the performance boost is largely attributable to stochastic robustness. The extended horizon allows the agent more opportunities to recover from initial "lucky stumbles" or bad random seeds, effectively smoothing out the variance inherent in zero-shot LLM navigation.

#### 5.4 Discussion

#### 5.4.1 Limitations and Feasibility Analysis

The Leader agent achieved a success rate of 35.0%. However, attributing the remaining 65% solely to reasoning failures is a mischaracterization of the results due to two critical factors:

Undefined Feasibility Ceiling: Unlike standard benchmarks that utilize human baselines to establish a "perfect play" ceiling (100%), this study relies on zero-shot LLM performance. Given the complexity of the ManipulaTHOR environments, it is statistically probable that a subset of targets are unreachable within 30 steps regardless of intelligence (due to spawn distance). Without a human baseline to establish that 100% of these tasks are solvable in < 30 steps, the Leader's 35% success rate should be viewed as a lower bound of capability, not an absolute ceiling.

Semantic Random Walks: Current "post-hoc embodiment" relies on the LLM's context window to store history. The text-based serialization results in perception loss, flattening 3D geometry into a list of items. The agent struggles to build a coherent "mental map," leading to "semantic random walks" where it revisits invalid locations. As evidenced by our ablation study, while extending the episode length improves success, it does not fundamentally resolve the lack of spatial memory.

### 5.4.2 Future Direction

The analysis of the Push-Pull dynamic suggests multi-agent architectures should move beyond "cooperation" to "incentivized uncertainty reduction." The current prompt likely biased agents toward agreeableness. To bridge the gap, the "Follower" agent should be explicitly incentivized to reject ambiguous instructions. We propose a "Devil's Advocate" reward function for future experiments, where the Follower is rewarded not just for reaching the goal, but for identifying and flagging uncertainties in the Leader's plan [\(Lee et al.,](#page-9-15) [2025\)](#page-9-15). True embodied intelligence emerges not when agents agree, but when they successfully resolve their disagreement.

## 6 Conclusion

#### 6.1 Summary of Contributions

This work systematically evaluated the "Grounding Gap" in asymmetric collaboration. By introducing a reproducible Asymmetric Assistive Reasoning testbed, we quantified the specific cost of the *Privileged Information Bias* in LLM-driven agents. Our experiments demonstrated that raw semantic intelligence does not guarantee collaborative success: despite the Leader identifying targets in 35.0% of episodes, the team failed to execute plans nearly half the time (17.0% success).

Our analysis attributes this failure to a lack of Theory of Mind, specifically the inability of the Leader to simulate the Follower's sensory constraints. Crucially, we identified the causal mechanism for resolution: "Push-based" broadcasting fails to resolve ambiguity, whereas "Pull-based" active querying restores performance. Successful episodes were characterized by a 2:1 ratio of Follower queries to failures, confirming that embodied intelligence emerges not from blind obedience, but from the active negotiation of belief states.

#### 6.2 Real World Implications

These findings have direct implications for Assistive and Task-Oriented Robotics. Real-world systems invariably function under asymmetric perception—whether due to sensor occlusion, latency, or distinct physical vantage points. Our results suggest that current "instruction-following" paradigms are insufficient for safety-critical tasks. To mitigate dangerous collisions or execution failures, autonomous systems must be designed with *Epistemic Anxiety*—the ability to recognize when an instruction is ungrounded and the agency to pause and query the human or supervisor before acting.

#### 6.3 Future Work

These findings motivate three specific shifts in multi-agent system design:

The "Devil's Advocate" Objective: To formalize the "Pull" mechanism, future training objectives should explicitly reward agents for questioning ambiguous instructions rather than maximizing agreeableness. This moves active querying from an emergent behavior to a learned policy.

Dynamic State Synchronization: We intend to expand this framework to dynamic environments with moving obstacles. In such settings, the "Success Gap" will likely exacerbate, requiring real-time belief synchronization beyond static navigation.

Visual-Language Integration: Finally, we aim to reduce the "Sensory Tax" by integrating Vision-Language Models (VLMs) capable of sharing image patches. This would allow the Leader to transmit a "visual imagination" to the blind follower, bridging the gap between semantic description and sensorimotor reality.

## Acknowledgments

We extend our gratitude to our course instructor, Professor Jinho Choi, and our teaching assistant, Grace Byun. Their guidance on the experimental design and their feedback on the framing of the "Success Gap" were instrumental in shaping this research.

## References

<span id="page-8-0"></span>Michael Ahn, Anthony Brohan, Noah Brown, Yevgen Chebotar, Omar Cortes, Byron David, Chelsea

- Finn, Chuyuan Fu, Keerthana Gopalakrishnan, Karol Hausman, Alex Herzog, Daniel Ho, Jasmine Hsu, Julian Ibarz, Brian Ichter, Alex Irpan, Eric Jang, Rosario Jauregui Ruano, Kyle Jeffrey, Sally Jesmonth, Nikhil J Joshi, Ryan Julian, Dmitry Kalashnikov, Yuheng Kuang, Kuang-Huei Lee, Sergey Levine, Yao Lu, Linda Luu, Carolina Parada, Peter Pastor, Jornell Quiambao, Kanishka Rao, Jarek Rettinghouse, Diego Reyes, Pierre Sermanet, Nicolas Sievers, Clayton Tan, Alexander Toshev, Vincent Vanhoucke, Fei Xia, Ted Xiao, Peng Xu, Sichun Xu, Mengyuan Yan, and Andy Zeng. 2022. [Do as i can,](https://arxiv.org/abs/2204.01691) [not as i say: Grounding language in robotic affor](https://arxiv.org/abs/2204.01691)[dances.](https://arxiv.org/abs/2204.01691) *Preprint*, arXiv:2204.01691.
- <span id="page-9-10"></span>Mido Assran, Adrien Bardes, David Fan, Quentin Garrido, Russell Howes, Mojtaba Komeili, Matthew J. Muckley, Ammar Rizvi, Claire Roberts, Koustuv Sinha, Artem Zholus, Sergio Arnaud, Abha Gejji, Ada Martin, Francois Robert Hogan, Daniel Dugas, Piotr Bojanowski, Vasil Khalidov, Patrick Labatut, Francisco Massa, Marc Szafraniec, Kapil Krishnakumar, Yong Li, Xiaodong Ma, Sarath Chandar, Franziska Meier, and Yann LeCun. 2025. [V](https://arxiv.org/abs/2506.09985)[jepa 2: Self-supervised video models enable un](https://arxiv.org/abs/2506.09985)[derstanding, prediction and planning.](https://arxiv.org/abs/2506.09985) *Preprint*, arXiv:2506.09985.
- <span id="page-9-13"></span>Karan Baijal, Zhiwen Qiu, and Jennifer Sun. 2025. [AdaTAMP: Adaptive task and motion planning with](https://dyalab.mines.edu/2025/icra-workshop/12.pdf) [LLM-based embodied agents.](https://dyalab.mines.edu/2025/icra-workshop/12.pdf) In *ICRA Workshop on Language and Semantics of Task and Motion Planning*.
- <span id="page-9-9"></span>Jake Bruce, Michael Dennis, Ashley Edwards, Jack Parker-Holder, Yuge Shi, Edward Hughes, Matthew Lai, Aditi Mavalankar, Richie Steigerwald, Chris Apps, Yusuf Aytar, Sarah Bechtle, Feryal Behbahani, Stephanie Chan, Nicolas Heess, Lucy Gonzalez, Simon Osindero, Sherjil Ozair, Scott Reed, Jingwei Zhang, Konrad Zolna, Jeff Dean, and Nando de Freitas. 2024. [Genie: Generative interactive environ](https://arxiv.org/abs/2402.15391)[ments.](https://arxiv.org/abs/2402.15391) *Preprint*, arXiv:2402.15391.
- <span id="page-9-2"></span>Colin Camerer, George Loewenstein, and Martin Weber. 1989. The curse of knowledge in economic settings: An experimental analysis. *Journal of Political Economy*, 97(5):1232–1254.
- <span id="page-9-4"></span>Weihua Du, Qiushi Lyu, Jiaming Shan, Zhenting Qi, Hongxin Zhang, Sunli Chen, Andi Peng, Tianmin Shu, Kwonjoon Lee, Behzad Dariush, and Chuang Gan. 2025. [Constrained human-ai cooperation: An](https://arxiv.org/abs/2411.01796) [inclusive embodied social intelligence challenge.](https://arxiv.org/abs/2411.01796) *Preprint*, arXiv:2411.01796.
- <span id="page-9-0"></span>Jiafei Duan, Samson Yu, Hui Li Tan, Hongyuan Zhu, and Cheston Tan. 2022. [A survey of embodied](https://arxiv.org/abs/2103.04918) [ai: From simulators to research tasks.](https://arxiv.org/abs/2103.04918) *Preprint*, arXiv:2103.04918.
- <span id="page-9-17"></span>Kiana Ehsani, Winson Han, Alvaro Herrasti, Eli VanderBilt, Luca Weihs, Eric Kolve, Aniruddha Kembhavi, and Roozbeh Mottaghi. 2021. [Manipulathor: A](https://arxiv.org/abs/2104.11213) [framework for visual object manipulation.](https://arxiv.org/abs/2104.11213) *Preprint*, arXiv:2104.11213.

- <span id="page-9-11"></span>Mohamed Amine Ferrag, Norbert Tihanyi, and Merouane Debbah. 2025. [From llm reasoning to](https://arxiv.org/abs/2504.19678) [autonomous ai agents: A comprehensive review.](https://arxiv.org/abs/2504.19678) *Preprint*, arXiv:2504.19678.
- <span id="page-9-6"></span>Stevan Harnad. 1990. The symbol grounding problem. *Physica D: Nonlinear Phenomena*, 42(1–3):335–346.
- <span id="page-9-16"></span>Chan-Jan Hsu, Davide Buffelli, Jamie McGowan, Feng-Ting Liao, Yi-Chang Chen, Sattar Vakili, and Da shan Shiu. 2025. [Group think: Multiple concurrent rea](https://arxiv.org/abs/2505.11107)[soning agents collaborating at token level granularity.](https://arxiv.org/abs/2505.11107) *Preprint*, arXiv:2505.11107.
- <span id="page-9-7"></span>Jennifer Hu, Felix Sosa, and Tomer Ullman. 2025. [Re](https://doi.org/10.1098/rstb.2023.0499)[evaluating theory of mind evaluation in large lan](https://doi.org/10.1098/rstb.2023.0499)[guage models.](https://doi.org/10.1098/rstb.2023.0499) *Philosophical Transactions of the Royal Society B*, 380(1932).
- <span id="page-9-1"></span>Muhammad Tayyab Khan and Ammar Waheed. 2025. [Foundation model driven robotics: A comprehensive](https://arxiv.org/abs/2507.10087) [review.](https://arxiv.org/abs/2507.10087) *arXiv preprint arXiv:2507.10087*.
- <span id="page-9-5"></span>Eric Kolve, Roozbeh Mottaghi, Winson Han, Eli VanderBilt, Luca Weihs, Alvaro Herrasti, Daniel Gordon, Yuke Zhu, Abhinav Gupta, and Ali Farhadi. 2017. [AI2-THOR: An interactive 3D environment for vi](https://arxiv.org/abs/1712.05474)[sual AI.](https://arxiv.org/abs/1712.05474) *Preprint*, arXiv:1712.05474.
- <span id="page-9-8"></span>Brenden M. Lake, Tomer D. Ullman, Joshua B. Tenenbaum, and Samuel J. Gershman. 2017. [Building ma](https://doi.org/10.1017/S0140525X16001837)[chines that learn and think like people.](https://doi.org/10.1017/S0140525X16001837) *Behavioral and Brain Sciences*, 40:e253.
- <span id="page-9-15"></span>Soohwan Lee, Seoyeong Hwang, Dajung Kim, and Kyungho Lee. 2025. [Conversational agents as cat](https://arxiv.org/html/2503.14263v1)[alysts for critical thinking: Challenging social in](https://arxiv.org/html/2503.14263v1)[fluence in group decision-making.](https://arxiv.org/html/2503.14263v1) *arXiv preprint arXiv:2503.14263*.
- <span id="page-9-14"></span>Huao Li, Yu Chong, Simon Stepputtis, Joseph Campbell, Dana Hughes, Charles Lewis, and Katia Sycara. 2023. [Theory of mind for multi-agent collabora](https://doi.org/10.18653/v1/2023.emnlp-main.13)[tion via large language models.](https://doi.org/10.18653/v1/2023.emnlp-main.13) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pages 180–192, Singapore. Association for Computational Linguistics.
- <span id="page-9-12"></span>Jie Liu, Pan Zhou, Yingjun Du, Ah-Hwee Tan, Cees G. M. Snoek, Jan-Jakob Sonke, and Efstratios Gavves. 2025. [Capo: Cooperative plan optimiza](https://arxiv.org/abs/2411.04679)[tion for efficient embodied multi-agent cooperation.](https://arxiv.org/abs/2411.04679) *Preprint*, arXiv:2411.04679.
- <span id="page-9-18"></span>Ji Ma, Hongming Dai, Xinyu Sun, Zifan Wang, Yiqing Xu, Rong Xiong, and Yue Wang. 2024. [DOZE: A](https://arxiv.org/abs/2402.19007) [dataset for zero-shot object navigation with dynamic](https://arxiv.org/abs/2402.19007) [obstacles.](https://arxiv.org/abs/2402.19007) *Preprint*, arXiv:2402.19007.
- <span id="page-9-3"></span>Matteo G. Mecattaf, Ben Slater, Marko Tešic, Jonathan ´ Prunty, Konstantinos Voudouris, and Lucy G. Cheke. 2025. [A little less conversation, a little more action,](https://arxiv.org/abs/2410.23242) [please: Investigating the physical common-sense](https://arxiv.org/abs/2410.23242) [of llms in a 3d embodied environment.](https://arxiv.org/abs/2410.23242) *Preprint*, arXiv:2410.23242.

- <span id="page-10-7"></span>Jihwan Oh, Minchan Jeong, Jongwoo Ko, and Se-Young Yun. 2025. [Understanding bias reinforcement in llm](https://arxiv.org/abs/2503.16814) [agents debate.](https://arxiv.org/abs/2503.16814) *Preprint*, arXiv:2503.16814.
- <span id="page-10-8"></span>Sabrina Patania, Luca Annese, Anita Pellegrini, Silvia Serino, Anna Lambiase, Luca Pallonetto, Silvia Rossi, Simone Colombani, Tom Foulsham, Azzurra Ruggeri, and Dimitri Ognibene. 2025. [Perspact:](https://arxiv.org/abs/2511.08098) [Enhancing llm situated collaboration skills through](https://arxiv.org/abs/2511.08098) [perspective taking and active vision.](https://arxiv.org/abs/2511.08098) *Preprint*, arXiv:2511.08098. Accepted at IAS-19.
- <span id="page-10-2"></span>Xavier Puig, Kevin Kyunghwan Ra, Marko Boben, Jiaman Li, Tingwu Wang, Sanja Fidler, and Antonio Torralba. 2018. [Virtualhome: Simulating household](https://api.semanticscholar.org/CorpusID:49317780) [activities via programs.](https://api.semanticscholar.org/CorpusID:49317780) *2018 IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pages 8494–8502.
- <span id="page-10-0"></span>Ram Ramrakhya, Matthew Chang, Xavier Puig, Ruta Desai, Zsolt Kira, and Roozbeh Mottaghi. 2025. [Grounding multimodal llms to embodied agents that](https://arxiv.org/abs/2504.00907) [ask for help with reinforcement learning.](https://arxiv.org/abs/2504.00907) *Preprint*, arXiv:2504.00907.
- <span id="page-10-1"></span>Manolis Savva, Abhishek Kadian, Oleksandr Maksymets, Yili Zhao, Erik Wijmans, Bhavana Jain, Julian Straub, Jia Liu, Vladlen Koltun, Jitendra Malik, Devi Parikh, and Dhruv Batra. 2019. [Habi](https://api.semanticscholar.org/CorpusID:91184540)[tat: A platform for embodied ai research.](https://api.semanticscholar.org/CorpusID:91184540) *2019 IEEE/CVF International Conference on Computer Vision (ICCV)*, pages 9338–9346.
- <span id="page-10-9"></span>Mohit Shridhar, Jesse Thomason, Daniel Gordon, Yonatan Bisk, Winson Han, Roozbeh Mottaghi, Luke Zettlemoyer, and Dieter Fox. 2020. [Alfred: A bench](https://arxiv.org/abs/1912.01734)[mark for interpreting grounded instructions for every](https://arxiv.org/abs/1912.01734)[day tasks.](https://arxiv.org/abs/1912.01734) *Preprint*, arXiv:1912.01734.
- <span id="page-10-6"></span>Zeyu Sun, Han Zhang, Cheng Wang, Chenyang Xu, and Yizhou Wang. 2025. [Collab-overcooked: Bench](https://arxiv.org/abs/2502.20073)[marking and evaluating large language models as col](https://arxiv.org/abs/2502.20073)[laborative agents.](https://arxiv.org/abs/2502.20073) *arXiv preprint arXiv:2502.20073*.
- <span id="page-10-3"></span>Lei Wang, Chen Ma, Xueyang Feng, Zeyu Zhang, Hao Yang, Jingsen Zhang, Zhiyuan Chen, Jiakai Tang, Xu Chen, Yankai Lin, et al. 2024. [A survey on large](https://doi.org/10.1007/s11704-024-40231-1) [language model based autonomous agents.](https://doi.org/10.1007/s11704-024-40231-1) *Frontiers of Computer Science*, 18(6):186345.
- <span id="page-10-5"></span>Guibin Zhang, Yanwei Yue, Zhixun Li, Sukwon Yun, Guancheng Wan, Kun Wang, Dawei Cheng, Jeffrey Xu Yu, and Tianlong Chen. 2025. [Cut the crap:](https://openreview.net/forum?id=LkzuPorQ5L) [An economical communication pipeline for LLM](https://openreview.net/forum?id=LkzuPorQ5L)[based multi-agent systems.](https://openreview.net/forum?id=LkzuPorQ5L) In *Proceedings of the International Conference on Learning Representations (ICLR)*.
- <span id="page-10-4"></span>Hongxin Zhang, Weihua Du, Jiaming Shan, Qinhong Zhou, Yilun Du, Joshua B. Tenenbaum, Tianmin Shu, and Chuang Gan. 2024. [Building cooperative em](https://proceedings.iclr.cc/paper_files/paper/2024/file/54b8b4e0b4ba4aad112e84f32e3b5dbb-Paper-Conference.pdf)[bodied agents modularly with large language models.](https://proceedings.iclr.cc/paper_files/paper/2024/file/54b8b4e0b4ba4aad112e84f32e3b5dbb-Paper-Conference.pdf) In *International Conference on Learning Representations (ICLR)*. ArXiv preprint arXiv:2307.02485.

## A Sample Interaction Logs

To illustrate the "Push-Pull" dynamics described in Section [5,](#page-5-0) we provide raw transcripts from the agent dyads. These logs highlight the contrast between successful active querying and failed passive obedience.

## A.1 Successful Episode: The "Pull" Mechanism

In this episode, the Follower (Handicapped) actively queries the Leader when the initial instruction is ambiguous relative to its local view. This "Pull" forces the Leader to re-ground the instruction, leading to success.

| Agent    | Message / Action                                      |  |
|----------|-------------------------------------------------------|--|
| Leader   | Instruction: "I see the Apple on the dining table.    |  |
|          | Move forward 3 steps."                                |  |
| Follower | Observation: "I see a wall and a sofa. I do not see a |  |
|          | dining table."                                        |  |
| Follower | Query (Pull): "Which direction is the dining table    |  |
|          | from the sofa?"                                       |  |
| Leader   | "My previous instruction assumed<br>Reasoning:        |  |
|          | global visibility. Correcting for sofa landmark."     |  |
| Leader   | Instruction: "Turn 90 degrees right. The table is     |  |
|          | behind the sofa."                                     |  |
| Follower | Action: Rotates Right.                                |  |
| Follower | Observation: "I see the table now."                   |  |

Table 5: A successful "Pull" interaction. The Follower's query prevents a potential navigation error.

## A.2 Failed Episode: Privileged Information Bias

In this failed episode, the Leader relies on its own egocentric frame of reference ("to your left"). The Follower fails to "Pull" (verify) and executes the action blindly, resulting in a collision.

| Agent    | Message / Action                                   |
|----------|----------------------------------------------------|
| Leader   | State: Target (Mug) is at (x = 1.5, z = 3.0).      |
| Leader   | Instruction: "The mug is just to your left. Move   |
|          | Left."                                             |
| Follower | Observation: "I see a cabinet to my left."         |
| Follower | Response (No Pull): "Moving Left."                 |
| System   | Event: Collision with Cabinet.                     |
| Leader   | Instruction: "You hit something. Move Left again." |
| System   | Event: Collision with Cabinet. (Episode Fail)      |

Table 6: A failed "Push" interaction. The Leader assumes its "Left" is the Follower's "Left," and the Follower fails to verify.

#### A.3 System Prompting (Context)

The dyadic interaction is governed by a shared LLM core that alternates roles. The "Privileged Information Bias" is induced by explicitly injecting different state descriptions into the system prompt:

- Leader Context: Receives full object list Ofull containing all objects in the scene with exact coordinates.
- Follower Context: Receives filtered object list Opartial containing only objects within 2.0m and within a 90◦ field of view.