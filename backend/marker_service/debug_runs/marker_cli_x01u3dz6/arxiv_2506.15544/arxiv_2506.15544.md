# **Stable Gradients for Stable Learning at Scale in Deep Reinforcement Learning**

Roger Creus Castanyer1,2<sup>∗</sup> Johan Obando-Ceron1,2<sup>∗</sup> Lu Li1,2 Pierre-Luc Bacon1,2 Glen Berseth1,2 Aaron Courville1,2 Pablo Samuel Castro1,2,3

<sup>1</sup> Mila - Québec AI Institute <sup>2</sup> Université de Montréal <sup>3</sup> Google DeepMind

#### **Abstract**

Scaling deep reinforcement learning networks is challenging and often results in degraded performance, yet the root causes of this failure mode remain poorly understood. Several recent works have proposed mechanisms to address this, but they are often complex and fail to highlight the causes underlying this difficulty. In this work, we conduct a series of empirical analyses which suggest that the combination of non-stationarity with gradient pathologies, due to suboptimal architectural choices, underlie the challenges of scale. We propose a series of direct interventions that stabilize gradient flow, enabling robust performance across a range of network depths and widths. Our interventions are simple to implement and compatible with well-established algorithms, and result in an effective mechanism that enables strong performance even at large scales. We validate our findings on a variety of agents and suites of environments. **[We make our code](https://github.com/roger-creus/stable-deep-rl-at-scale) [publicly available.](https://github.com/roger-creus/stable-deep-rl-at-scale)**

*"We must be able to look at the world and see it as a dynamic process, not a static picture." — David Bohm*

### **1 Introduction**

Recent advances in deep reinforcement learning (deep RL) have demonstrated the ability of deep neural networks to solve complex decision-making tasks from robotics to game play and resource optimization [\(Bellemare et al.,](#page-11-0) [2020,](#page-11-0) [Fawzi et al.,](#page-12-0) [2022,](#page-12-0) [Mnih et al.,](#page-15-0) [2015,](#page-15-0) [Vinyals et al.,](#page-16-0) [2019\)](#page-16-0). Motivated by successes in supervised and generative learning, recent works have explored scaling architectures in deep RL, showing gains in representation quality and generalization across tasks [\(Farebrother et al.,](#page-12-1) [2023,](#page-12-1) [Taiga et al.,](#page-16-1) [2023\)](#page-16-1). However, scaling neural networks in deep RL remains fundamentally challenging [\(Ceron et al.,](#page-11-1) [2024a](#page-11-1)[,b\)](#page-12-2).

A central cause of this instability lies in the unique optimization challenges of RL. Unlike supervised learning, where data distributions are fixed, deep RL involves policy-dependent data that constantly change during training [\(Lyle et al.,](#page-14-0) [2022\)](#page-14-0). Each update of the policy π<sup>θ</sup> alters future states and rewards, making the training objective inherently *non-stationary.* Value-based methods exacerbate these issues via bootstrapping, recursively using predicted values as targets. Estimation errors compound over time [\(Fujimoto et al.,](#page-12-3) [2018\)](#page-12-3), especially under sparse or delayed rewards [\(Zheng et al.,](#page-16-2) [2018\)](#page-16-2), leading to unstable updates, policy collapse, or value divergence [\(Lyle](#page-14-1) [et al.,](#page-14-1) [2023,](#page-14-1) [2024,](#page-14-2) [Van Hasselt et al.,](#page-16-3) [2016\)](#page-16-3). These dynamics are tightly coupled with architectural vulnerabilities. Deep networks face well known pathologies such as vanishing/exploding gradients

<sup>∗</sup>Equal contribution

(Pascanu et al., 2013), ill-conditioned Jacobians (Pennington et al., 2017), and activation saturation (Glorot and Bengio, 2010). In deep RL, these are magnified by the "deadly triad" (Sutton and Barto, 2018, Van Hasselt et al., 2018), off-policy corrections, and changing targets. As networks scale, the risk of signal distortion and misalignment increases, resulting in underutilized capacity and brittle learning (Ceron et al., 2024a, Obando Ceron et al., 2023).

One overlooked source of these failures lies in how gradients propagate through the network. Specifically, the gradient decomposition, the layer-wise structure of backpropagation as a chain of Jacobians and weights determine how information flows during learning (Lee et al., 2020). While gradient signal preservation has been studied in supervised learning (Jacot et al., 2018, Schoenholz et al., 2017), its role in deep RL, where both inputs and targets shift continually, remains poorly understood.

In this work, we investigate how gradient decomposition interacts with non-stationarity and network scaling in deep RL. We demonstrate that in non-stationary settings like RL – where targets are bootstrapped, policies evolve continually, and data distributions shift – gradient signals progressively degrade across depth. This motivates the need for methods that explicitly preserve the structure of gradient information across layers. We explore this through a series of controlled experiments and ablations across multiple algorithms and environments, demonstrating that actively encouraging gradient propagation significantly improves stability and performance, even with large networks. Our work offers a promising approach for scaling deep RL architectures, yielding substantial performance gains across a variety of agents and training regimes.

#### <span id="page-1-2"></span>2 Preliminaries

Deep Reinforcement Learning A deep reinforcement learning agent interacts with an environment through sequences of actions  $(a \in \mathcal{A})$ , which produce corresponding sequences of observations  $(s \in \mathcal{S})$  and rewards  $(r \in \mathbb{R})$ , resulting in trajectories of the form  $\tau := \{s_0, a_0, r_0, s_1, a_1, r_2, \ldots\}$ . The agent's behavior is often represented by a neural network with parameters  $\theta$ , composed of convolutional layers  $\{\phi_1, \phi_2, \ldots, \phi_{L_c}\}$  and dense (fully connected) layers  $\{\psi_1, \psi_2, \ldots, \psi_{L_d}\}$ , where  $\psi_{L_d}$  has an output dimensionality of  $|\mathcal{A}|$ . At every timestep t, an observation  $s_t \in \mathcal{S}$  is fed through the network to obtain an estimate of the long-term value of each action:  $Q_{\theta}(s_t, \cdot) = \psi_{L_d}(\psi_{L_d-1}(\ldots(\phi_{L_c}(\ldots(\phi_1(s_t))\ldots))\ldots))$ . The agent's policy  $\pi_{\theta}(\cdot \mid s_t)$  specifies the probability of selecting each action, for instance by taking the softmax over the estimated values as in Equation 1. The training objective is typically defined as the maximization of expected cumulative reward as in Equation 2,

<span id="page-1-0"></span>
$$\pi_{\theta}(a_t \mid s_t) = \frac{e^{Q_{\theta}(s_t, a_t)}}{\sum_{a \in \mathcal{A}} e^{Q_{\theta}(s_t, a)}} \tag{1}$$

$$J(\theta) = \mathbb{E}_{\tau \sim \pi_{\theta}} \left[ \sum_{t=0}^{\infty} \gamma^t r_t \right]$$

where  $\gamma \in [0,1)$  is a discount factor and  $\tau$  denotes a trajectory generated by following policy  $\pi_{\theta}$ . Optimization proceeds by minimizing a surrogate loss  $\mathcal{L}(\theta)$ , which may be derived from temporal-difference (TD) errors, policy gradients, or actor-critic estimators (Sutton and Barto, 2018). In TD-based methods, the TD error at timestep t is defined as:

<span id="page-1-1"></span>
$$\delta_t = r_t + \gamma V_{\theta}(s_{t+1}) - V_{\theta}(s_t),$$

where  $V_{\theta}(s) = \mathbb{E}_{a \sim \pi_{\theta}(a|s)} Q_{\theta}(s,a)$ . The recurrent nature of  $\delta_t$  introduces dependencies on both current estimates and future rewards, making  $\mathcal{L}(\theta)$  inherently non-stationary. As the policy  $\pi_{\theta}$  evolves, the data distribution used for training shifts, further complicating optimization. Training

is performed by collecting trajectories, computing gradients  $\nabla \mathcal{L}(\theta)$ , and updating parameters via  $\theta \leftarrow \theta - \eta \nabla \mathcal{L}(\theta)$ , where  $\eta > 0$  is the learning rate. Following conventions from supervised learning, deep RL algorithms often use adaptive variants of stochastic gradient descent, such as Adam (Kingma and Ba, 2014) or RMSprop (Hinton, 2012), which adjust learning rates based on running estimates of gradient statistics. The gradients with respect to each layer are denoted by;

$$\nabla \phi_i = \frac{\partial \mathcal{L}}{\partial \phi_i}, \quad \nabla \psi_j = \frac{\partial \mathcal{L}}{\partial \psi_j},$$

where  $\phi_i$  and  $\psi_j$  represent the parameters (i.e., weight matrices or bias vectors) of layer i and j respectively. The structure and magnitude of these gradients ( $\nabla \phi_i$  and  $\nabla \psi_j$ ) are influenced by the loss function, data distribution collected from the environment, and the architecture itself. These per-layer gradients determine how effectively different parts of the network adapt during training.

While training large models in supervised learning settings present challenges, advances in initialization, normalization, and scaling strategies have enabled relatively stable optimization (Ba et al., 2016, Glorot and Bengio, 2010, Ioffe and Szegedy, 2015). Scaling up model size has been a central driver of progress across domains, improving generalization, enhancing representation learning, and boosting downstream performance (Kaplan et al., 2020).

Deep RL differs substantially from supervised learning. First, the data distribution is non-stationary, continually shifting as  $\pi_{\theta}$  updates. Second, learning signals are often sparse, delayed, or noisy, which introduces variance in the estimated gradients (Fujimoto et al., 2018, Han et al., 2022). These factors destabilize optimization and lead to loss surfaces with sharp curvature and complex local structure (Achiam et al., 2019, Ilyas et al., 2020). Moreover, increasing model capacity often degrades performance unless regularization or architectural interventions are applied (Bjorck et al., 2021, Gogianu et al., 2021, Schwarzer et al., 2023, Wang et al., 2025).

These challenges are further compounded by both architectural and environmental factors. Network depth, width, initialization, and nonlinearity affect how gradients are propagated across layers. Meanwhile, reward sparsity, exploration dificulty, and transition stochasticity impose additional structure on the optimization landscape. The resulting geometry reflects the joint dynamics of policy, environment, and architecture, making deep RL optimization uniquely complex.

**Gradient Propagation** Training deep networks poses fundamental challenges for effective gradient propagation (Glorot and Bengio, 2010). As network depth increases, gradients may either vanish or explode as they are backpropagated through multiple layers, impeding the optimization of early layers and destabilizing learning dynamics (Ba et al., 2016). These issues arise from repeated applications of the chain rule. For a network with intermediate hidden representations  $\{h_0, h_1, \ldots, h_L\}$ , where  $h_k \in \mathbb{R}^{d_k}$ , the gradient of the loss  $\mathcal L$  with respect to a hidden layer  $h_\ell$  is:

$$\frac{\partial \mathcal{L}}{\partial h_{\ell}} = \left( \prod_{k=\ell+1}^{L} \frac{\partial h_{k}}{\partial h_{k-1}} \right) \frac{\partial \mathcal{L}}{\partial h_{L}},$$

where each  $\frac{\partial h_k}{\partial h_{k-1}} \in \mathbb{R}^{d_k \times d_{k-1}}$  is the Jacobian. If the singular values of these Jacobians are not properly controlled, their repeated multiplication can cause the norm of the gradient to shrink or grow exponentially with  $\mathcal{L}$ . This severely impairs convergence, as earlier layers receive little to no useful gradient signal or become numerically unstable (He et al., 2016, Ioffe and Szegedy, 2015).

In addition to depth, the width of the network also influences gradient propagation. Consider a fully connected layer with weight matrix  $W \in \mathbb{R}^{m \times n}$  and input vector  $h \in \mathbb{R}^n$ . The output is

W h ∈ R <sup>m</sup>, and under the assumption that W and h have i.i.d. zero-mean entries with finite variance σ<sup>W</sup> and σh, respectively, the variance of the output is given by Var[W h] = n σ<sup>W</sup> σh. Thus, scaling the width n without adjusting σ<sup>W</sup> and σ<sup>h</sup> leads to instability in forward and backward signal propagation affecting gradient norms and optimization trajectories.

Beyond depth and width, the choice of nonlinearity also plays a central role in determining how gradients propagate . In a typical feedforward network, hidden activations evolve as h<sup>k</sup> = ζ(Wkhk−1), where ζ(·) is a nonlinear activation function (e.g., ReLU, tanh, sigmoid), and W<sup>k</sup> is the weight matrix at layer k. During backpropagation, the gradient with respect to a hidden layer includes the product of the Jacobian of the linear transformation and the derivative of the nonlinearity:

$$\frac{\partial \mathcal{L}}{\partial h_{k-1}} = W_k^{\top} \left( \zeta'(W_k h_{k-1}) \odot \frac{\partial \mathcal{L}}{\partial h_k} \right),$$

where ζ ′ (·) denotes the elementwise derivative of the activation function, and ⊙ represents elementwise multiplication. For ReLU, ζ ′ (x) = 1x>0, so the gradient is entirely blocked wherever the neuron is inactive. This leads to the well-known *dying ReLU* problem, where a significant portion of the network ceases to update and becomes untrainable [\(Lu et al.,](#page-14-4) [2019,](#page-14-4) [Shin and Karniadakis,](#page-15-6) [2020\)](#page-15-6).

# <span id="page-3-0"></span>**3 Diagnosis: Gradients Under Non-stationarity and Scale**

A fundamental premise of modern deep learning is that scaling model capacity yields consistent gains in performance [\(Chowdhery et al.,](#page-12-6) [2023,](#page-12-6) [Kaplan et al.,](#page-13-4) [2020\)](#page-13-4). This has held true in largescale supervised learning, where training data distributions are stationary and i.i.d., and gradient descent operates under relatively stable conditions. However, in non-stationary settings, such as RL, gradient-based optimization faces severe challenges that scaling alone may exacerbate [\(Ceron](#page-11-1) [et al.,](#page-11-1) [2024a,](#page-11-1)[b\)](#page-12-2). In this section, we diagnose how gradient pathologies emerge and intensify across different settings, with a focus on architectural scaling in width and depth (network scales used specified in Table [1\)](#page-17-0).

#### **3.1 Gradient Pathologies**

We train neural networks of varying depths and widths and analyze their training dynamics.

**Supervised Learning (Stationary and Non-Stationary)** We use the CIFAR-10 image classification benchmark [\(Krizhevsky et al.,](#page-14-5) [2009\)](#page-14-5), where the input-output mapping remains fixed over time. Models consist of standard 6-layer convolutional neural networks (CNN) followed by a multi-layer perceptron (MLP). We vary the depth and width of the MLP to explore how model scale influences learning behavior. To introduce non-stationarity, we periodically shuffle the training labels during training, following the setup by [Sokar et al.](#page-15-7) [\(2023\)](#page-15-7). This creates a loss landscape that changes over time, echoing the challenges of deep RL. [Figure 1](#page-4-0) illustrates the contrast in training behavior and gradient flow between stationary and non-stationary supervised learning. Under non-stationarity, deep networks fail to recover accuracy, which aligns with a marked degradation in gradient magnitudes.

**Reinforcement Learning** As discussed in [section 2,](#page-1-2) RL introduces fundamentally different sources of non-stationarity due to the policy-dependent data distribution and moving target estimates. To study gradient dynamics, we use PQN [\(Gallici et al.,](#page-12-7) [2025\)](#page-12-7), a recent value-based algorithm that achieves strong performance without relying on a target network or replay buffer. PQN ensures

<span id="page-4-0"></span>![](_page_4_Figure_0.jpeg)

Figure 1: **Training dynamics under stationary and non-stationary supervised learning.** (Left) In the stationary setting, both shallow and deep models fit the data effectively across widths. Under non-stationarity only shallow networks partially recover during training, while deeper ones collapse. (Right) This collapse correlates with degraded gradient flow. In stationary settings, gradient norms remains stable across all network scales (shaded boxes) while in non-stationary settings (solid-colored boxes), gradient magnitudes diminish with depth and width, suggesting poor adaptability.

<span id="page-4-1"></span>![](_page_4_Figure_2.jpeg)

Figure 2: **Mean episode returns and gradient norms across increasing MLP depths and widths** on two ALE games using PQN. (Left) Only shallow networks achieve high episode returns; performance collapses for deeper networks. (Right) The collapse correlates with vanishing gradient norms, suggesting that deeper models fail to adapt to non-stationarity in deep RL.

stability and convergence using Layer Normalization (Ba et al., 2016) and supports GPU-based training through vectorized environments for online parallel data collection. In subsection C.1 we extend our investigation to DQN (Mnih et al., 2015) and Rainbow (Hessel et al., 2018), demonstrating the generality of our observations. As shown in Figure 2, deeper networks trained with PQN exhibit a collapse in both episode returns and gradient norms<sup>1</sup>, highlighting the fragility of deep models under non-stationarity.

#### 3.2 Training Degradation

In Figure 3 we evaluate diagnostic metrics capturing expressivity and training dynamics, revealing that deeper networks exhibit pronounced training pathologies and degraded performance. We first measure the fraction of *dormant neurons*, defined as units with near-zero activations over a batch of trajectories (Sokar et al., 2023), and find that dormant neurons grow with depth, signaling

<span id="page-4-2"></span><sup>&</sup>lt;sup>1</sup>Unless otherwise specified, all ALE results are averaged over three seeds.

<span id="page-5-0"></span>![](_page_5_Figure_0.jpeg)

Figure 3: **Training pathologies emerge as MLP depth increases.** Deeper networks exhibit a higher fraction of inactive neurons, reduced representation rank (SRank), vanishing Hessian trace (loss curvature), and degraded learning performance (mean Q-values and episode returns). These trends indicate that scaling depth limits expressivity and plasticity, impairing policy quality.

underutilized capacity. Next, we assess representational expressivity using *SRank*, the effective rank of penultimate-layer activations (Kumar et al., 2020), observing that deeper networks tend to collapse state representations into lower-dimensional, and less expressive (as evidenced by declining returns) subspaces. To study loss curvature, we compute the Hessian trace of the temporal-difference loss. This metric serves as a proxy for sharpness or smoothness in optimization (Ghorbani et al., 2019), similarly to tracking the largest eigenvalue. Figure 3 shows that only shallow networks exhibit high Hessian trace values, suggesting access to sharper regions of the loss surface with pronounced directions of improvement. In contrast, deeper architectures consistently show near-zero trace, indicating poorly conditioned geometry that hinders effective gradient-based updates. These findings suggest a breakdown in representation, plasticity, and optimization as networks scale, ultimately impeding learning.

#### Key observations on gradients under non-stationarity and scale:

- Non-stationarity amplifies gradient degradation in deeper and wider networks.
- In deep RL, deeper models suffer from vanishing gradients, reduced activations, and loss of representational expressivity.
- The flat loss curvature intensifies with depth, correlating with poor learning.

### <span id="page-5-1"></span>4 Stabilizing Gradients

Having identified the pathologies that emerge in non-stationary regimes, particularly under large-scale architectures, we investigate strategies to mitigate these instabilities. We focus on two complementary interventions: skip connections (He et al., 2016) and optimizers (Martens and Grosse, 2015), as these directly improve gradient flow. We continue to use PQN as our base RL algorithm and evaluate on the Atari-10 suite (Aitchison et al., 2023). In section 5, we demonstrate that the effectiveness of our proposed gradient interventions generalize beyond this specific algorithm and environment suite

#### 4.1 **Intervention 1**: Multi-Skip Residuals for Gradient Stability

Gradient instability in deep networks is often aggravated by increasing depth, non-linear activations, and misaligned curvature across layers. While standard residual connections offer some relief by introducing shortcut paths for gradient flow (He et al., 2016), they typically span only one

![](_page_6_Figure_0.jpeg)

Figure 4: (Left) MLP architectures and (right) scaling strategies studied.

<span id="page-6-0"></span>![](_page_6_Figure_2.jpeg)

Figure 5: **Gradient-stabilizing interventions improve scalability in deep RL.** (Left) Standard fully connected networks trained with PQN collapse at greater depths due to vanishing gradients. In contrast, multi-skip architectures maintain gradient flow and scale effectively. (Right) The default RAdam optimizer leads to instability in deep networks, while switching to the Kron optimizer preserves gradient signal and enables stable learning without architectural changes.

or two layers, which can be insufficient in the presence of severe gradient disruption due to non-stationarity. We introduce *multi-skip residual connections*, in which the flattened convolutional features are broadcast directly to all subsequent MLP layers. This design ensures that gradients can propagate from any depth back to the shared encoder without obstruction.

We compare our network architecture against the standard fully connected baseline across varying depths. As shown in Figure 5 (left), performance collapses with increased depth in the baseline, while the multi-skip architecture maintains stable learning and continues to improve across widths. This improvement is accompanied by consistently higher gradient magnitudes. Complete results across all network depths and widths are presented in section C.3.

#### 4.2 **Intervention 2:** Second-Order Optimizers for Non-Stationarity

First-order optimizers such as SGD and Adam rely on local gradient estimates and fixed heuristics (e.g., momentum, adaptive step sizes) (Kingma and Ba, 2014), which are agnostic to curvature and often brittle under shifting data distributions. In contrast, second-order methods adjust parameter updates using curvature information, enabling more informed and stable adaptation.

Let  $\mathcal{L}(\theta)$  denote the loss function, and  $g = \nabla \mathcal{L}(\theta)$  its gradient. A second-order update takes the form  $\theta_{t+1} = \theta_t - \eta H^{-1}g$ , where H is the curvature matrix, typically the Hessian or the Fisher Information Matrix (FIM) (Martens, 2020). Directly inverting H is computationally infeasible in deep neural networks so Kronecker-factored approximations, such as K-FAC (Martens and Grosse, 2015), address this challenge by approximating H using low-rank Kronecker products.

Kronecker-factored optimizer (Kron for short) approximates the FIM and applies structured preconditioning that captures inter-parameter dependencies, unlike Adam's diagonal scaling. This yields directionally aware preconditioning that better aligns with the curvature of the loss surface (Martens, 2020). In non-stationary settings, such as deep RL, where both the data distribution and curvature evolve over time, curvature-aware updates can help preserve gradient signal by maintaining stable update magnitudes and directions. As shown in Figure 5 (right), replacing RAdam with Kron prevents performance collapse at greater depths, even in standard MLP architectures. Complete results across all network depths and widths are presented in section C.3.

#### <span id="page-7-2"></span>4.3 Combining Gradient Interventions

We combine both gradient interventions to PQN and evaluate it on the full ALE suite (57 games), across 3 seeds and 200M frames. Figure 6 shows that our augmented agent outperforms the baseline in 90% of the environments, achieving a median relative improvement of 83.27%. Notably, the baseline PQN is itself competitive with strong agents such as Rainbow (Gallici et al., 2025), highlighting the effectiveness of our interventions. Detailed per-environment learning curves can be found in subsection C.4.

In Figure 7 we validate the effectiveness of the combined gradient interventions in the non-stationary SL setting we used as motivation in section 3. The results verify that these interventions enable high accuracy and sustained adaptability across depths and widths, even under dynamic label reshuffling.

<span id="page-7-1"></span>![](_page_7_Figure_5.jpeg)

Figure 6: **Gradient-stabilized PQN achieves superior scalability.** (Left) On Atari-10, the combined interventions lead to high HNS even at greater depths, outperforming either intervention alone (see Figure 5) and increased gradient gradient flow. (Right) On the full ALE suite, our agent outperforms the baseline in 90% of the games with a median performance improvement of 83.27%.

### <span id="page-7-0"></span>5 Beyond the ALE and PQN

To evaluate the generality of our findings, we extend our analyses. Specifically, we: (*i*) apply our proposed methods to PPO (Schulman et al., 2017) on the full ALE and on continuous control tasks in Isaac Gym (Makoviychuk et al., 2021); (*ii*) assess the impact of richer convolutional encoders by replacing the standard CNN backbone used in the ALE with the Impala CNN architecture (Espeholt

<span id="page-8-0"></span>![](_page_8_Figure_0.jpeg)

Figure 7: **Gradient interventions enable rapid recovery in non-stationary SL.** (Left) Models with combined gradient interventions rapidly recover accuracy after label reshuffling, demonstrating robust adaptation in non-stationary settings. (Right) This is supported by stable gradient flow across depth. Dashed curves and shaded boxes indicate MLP baselines.

<span id="page-8-1"></span>![](_page_8_Figure_2.jpeg)

Figure 8: **PPO with gradient interventions.** Left: On the full ALE suite, applying the combined gradient interventions to PPO yields a median performance improvement of 31.40% and outperforms the baseline in 83.64% of the games. Right: In the Cartpole and Anymal tasks from IsaacGym, only the augmented PPO maintains stable performance across depths and widths.

et al., 2018); and (iii) augment Simba (Lee et al., 2025) with our proposed techniques and evaluate performance on the DeepMind Control Suite (DMC) (Tassa et al., 2018).

**PPO with Gradient Interventions.** Figure 8 (left) shows that augmenting PPO with the same strategies as in PQN (Layer Normalization by default on PQN, multi-skip residual connections, and Kronecker-factored optimization) significantly boots performance. On the ALE benchmark, the augmented PPO outperforms the baseline in 83.64% of the environments, achieving a median relative improvement of 31.40%. In Isaac Gym's continuous control tasks, including Cartpole and Anymal (Figure 8, right), the baseline PPO collapses as model size increases, while the augmented variant remains stable and achieves superior performance at all depths and widths.

Gradient Interventions in Scaled Encoder Variants The Impala CNN is a scalable convolutional architecture that has demonstrated strong performance gains in agents such as Impala (Espeholt et al., 2018) and Rainbow (Hessel et al., 2018). We investigate whether, given its capacity to extract richer representations from visual input, combining Impala CNN with our gradient flow interventions enables effective scaling of the MLP component. As shown in Figure 9, PPO and PQN benefit

<span id="page-9-0"></span>![](_page_9_Figure_0.jpeg)

Figure 9: **Scaling performance with standard vs. Impala CNN encoders** on PQN (left) and PPO (right). Each agent is evaluated using both the Atari CNN (left sub-panels) and the Impala CNN (right sub-panels) as the encoder. Gradient interventions enable successful scaling in both cases.

significantly from replacing the standard CNN with the Impala CNN. For PQN, the Impala encoder enables successful scaling of the MLP, in contrast to the performance collapse seen without our interventions. These results suggest that the expressivity of richer visual encoders is more effectively leveraged by deeper networks when gradient flow is preserved.

**Simba with Kron Optimizer.** Simba (Lee et al., 2025) is a scalable actor-critic framework that integrates normalization, residual connections, and LayerNorm. We augment Simba by replacing its default AdamW optimizer with Kron while keeping all other hyperparameters fixed. We evaluate SAC (Haarnoja et al., 2018) and DDPG (Lillicrap et al., 2015) on challenging DMC tasks, using the Simba architectures of varying depth and width. Despite its design for scalability, default Simba collapses across all tasks as networks grow as shown in Figure 10 (additional results in subsection C.5). In contrast, the Kron-augmented version successfully scales in both depth and width, achieving consistent and stable performance gains. These findings underscore the generality of our approach as effectively enabling parameter scaling in deep RL agents.

<span id="page-9-1"></span>![](_page_9_Figure_4.jpeg)

Figure 10: Performance comparison between AdamW (dashed lines) and Kron (solid lines) optimizers using the SimBa architecture with SAC and DDPG, averaged over 5 random seeds. As model size increases, AdamW leads to consistent performance degradation, while Kron enables stable and improved learning with larger networks.

### **6 Related Work**

A central challenge in scaling deep RL lies in the inefficient use of model capacity. Increasing parameter counts often fails to yield proportional gains due to under-utilization. [Sokar et al.](#page-15-7) [\(2023\)](#page-15-7) show that online RL induces a growing fraction of inactive neurons, a phenomenon also observed in offline settings. [Ceron et al.](#page-11-1) [\(2024a\)](#page-11-1) report that up to 95% of parameters can be pruned post-training with negligible performance drop, underscoring substantial redundancy. These findings have motivated techniques such as weight resetting [\(Schwarzer et al.,](#page-15-5) [2023\)](#page-15-5), tokenized computation [\(Sokar](#page-16-8) [et al.,](#page-16-8) [2025\)](#page-16-8), and sparse architectures [\(Ceron et al.,](#page-12-2) [2024b,](#page-12-2) [Liu et al.,](#page-14-12) [2025,](#page-14-12) [Willi et al.,](#page-16-9) [2024\)](#page-16-9), along with auxiliary objectives to promote capacity utilization [\(Farebrother et al.,](#page-12-1) [2023\)](#page-12-1). While scaling model size offers greater expressivity, its benefits depend on appropriate training strategies [\(Ota](#page-15-9) [et al.,](#page-15-9) [2021\)](#page-15-9). Architectural interventions such as SimBa [\(Lee et al.,](#page-14-10) [2025\)](#page-14-10) improve robustness by regularizing signal propagation through components such as observation normalization, residual feedforward blocks, and layer normalization. Complementarily, BRO [\(Nauman et al.,](#page-15-10) [2024\)](#page-15-10) shows that scaling the critic network yields substantial gains in sample and compute efficiency, provided it is paired with strong regularization and optimistic exploration strategies.

Gradient flow, however, remains a central bottleneck. We complement prior efforts by explicitly targeting vanishing gradients as a mechanism for improving scalability. Our approach builds on the role of LayerNorm in stabilizing training and enhancing plasticity [\(Lyle et al.,](#page-14-2) [2024\)](#page-14-2), and leverages its theoretical effect on gradient preservation as formalized in PQN [\(Gallici et al.,](#page-12-7) [2025\)](#page-12-7). Optimizationlevel interventions such as second-order methods [\(Martens and Grosse,](#page-14-7) [2015,](#page-14-7) [Muppidi et al.,](#page-15-11) [2024\)](#page-15-11) and adaptive optimizers [\(Bengio et al.,](#page-11-6) [2021,](#page-11-6) [Ellis et al.,](#page-12-10) [2024,](#page-12-10) [Wu et al.,](#page-16-10) [2017\)](#page-16-10) also address instability under non-stationarity. Our approach integrates architectural and optimizer-level interventions to enable stable gradient flow and unlock parameter scaling in deep RL agents.

### **7 Discussion**

Our analyses in [section 3](#page-3-0) suggest that the difficulty in scaling networks in deep RL stems from the interaction between inherent non-stationarity and gradient pathologies that worsen with network size. In [section 4,](#page-5-1) we introduced targeted interventions to address these challenges, and in [subsection 4.3,](#page-7-2) we demonstrated their effectiveness. We validated the generality of our approach across agents and environment suites, consistently observing similar trends. These findings reaffirm the critical role of network design and optimization dynamics in training scalable RL agents. While our proposed solutions may not be optimal, they establish a strong baseline and provide a foundation for future work on gradient stabilization in deep RL. More broadly, our findings suggest that scaling limitations in deep RL are not solely attributable to algorithmic instability or insufficient exploration, but also stem from gradient pathologies amplified by architectural and optimization choices. Addressing these issues directly, without altering the learning algorithm, yields substantial gains in scalability and performance. This suggests that ensuring stable gradient flow is a necessary precondition for effective parameter scaling in deep RL.

**Limitations.** Our study is constrained by computational resources, which limited our ability to explore architectures beyond a certain size. While our interventions show consistent improvements across agents and environments, further scaling remains an open question. While using second order optimizers introduced additional computational overhead (see [Table 10\)](#page-31-0), this cost is mitigated by leveraging vectorized environments and efficient deep RL algorithms, narrowing the gap relative to standard methods. These limitations highlight promising directions for future work, including the development of more computationally efficient gradient stabilization strategies and scalable optimization techniques.

# **8 Acknowledgment**

The authors would like to thank João Guilherme Madeira Araújo, Evan Walters, Olya Mastikhina, Dhruv Sreenivas, Ali Saheb Pasand, Ayoub Echchahed and Gandharv Patil for valuable discussions during the preparation of this work. João Araújo deserves a special mention for providing us valuable feed-back on an early draft of the paper. We want to acknowledge funding support from Google, CIFAR AI and compute support from Digital Research Alliance of Canada and Mila IDT. We would also like to thank the Python community [\(Oliphant,](#page-15-12) [2007,](#page-15-12) [Van Rossum and Drake Jr,](#page-16-11) [1995\)](#page-16-11) for developing tools that enabled this work, including NumPy [Harris et al.](#page-13-10) [\(2020\)](#page-13-10), Matplotlib [\(Hunter,](#page-13-11) [2007\)](#page-13-11), Jupyter [\(Kluyver et al.,](#page-13-12) [2016\)](#page-13-12), and Pandas [\(McKinney,](#page-14-13) [2013\)](#page-14-13).

# **References**

- <span id="page-11-3"></span>Joshua Achiam, Ethan Knight, and Pieter Abbeel. Towards characterizing divergence in deep q-learning. *arXiv preprint arXiv:1903.08894*, 2019.
- <span id="page-11-8"></span>Rishabh Agarwal, Max Schwarzer, Pablo Samuel Castro, Aaron C Courville, and Marc Bellemare. Deep reinforcement learning at the edge of the statistical precipice. *Advances in neural information processing systems*, 34:29304–29320, 2021.
- <span id="page-11-5"></span>Matthew Aitchison, Penny Sweetser, and Marcus Hutter. Atari-5: Distilling the arcade learning environment down to five games. In *International Conference on Machine Learning*, pages 421–438. PMLR, 2023.
- <span id="page-11-9"></span>Kavosh Asadi, Rasool Fakoor, and Shoham Sabach. Resetting the optimizer in deep rl: An empirical study. *Advances in Neural Information Processing Systems*, 36:72284–72324, 2023.
- <span id="page-11-2"></span>Jimmy Lei Ba, Jamie Ryan Kiros, and Geoffrey E Hinton. Layer normalization. *arXiv preprint arXiv:1607.06450*, 2016.
- <span id="page-11-7"></span>Marc G Bellemare, Yavar Naddaf, Joel Veness, and Michael Bowling. The arcade learning environment: An evaluation platform for general agents. *Journal of Artificial Intelligence Research*, 47: 253–279, 2013.
- <span id="page-11-0"></span>Marc G. Bellemare, Salvatore Candido, Pablo Samuel Castro, Jun Gong, Marlos C. Machado, Subhodeep Moitra, Sameera S. Ponda, and Ziyun Wang. Autonomous navigation of stratospheric balloons using reinforcement learning. *Nature*, 588:77 – 82, 2020.
- <span id="page-11-6"></span>Emmanuel Bengio, Joelle Pineau, and Doina Precup. Correcting momentum in temporal difference learning. *arXiv preprint arXiv:2106.03955*, 2021.
- <span id="page-11-4"></span>Nils Bjorck, Carla P Gomes, and Kilian Q Weinberger. Towards deeper deep reinforcement learning with spectral normalization. *Advances in neural information processing systems*, 34:8242–8255, 2021.
- <span id="page-11-10"></span>Johan Samir Obando Ceron and Pablo Samuel Castro. Revisiting rainbow: Promoting more insightful and inclusive deep reinforcement learning research. In *International Conference on Machine Learning*, pages 1373–1383. PMLR, 2021.
- <span id="page-11-1"></span>Johan Samir Obando Ceron, Aaron Courville, and Pablo Samuel Castro. In value-based deep reinforcement learning, a pruned network is a good network. In *International Conference on Machine Learning*, pages 38495–38519. PMLR, 2024a.

- <span id="page-12-2"></span>Johan Samir Obando Ceron, Ghada Sokar, Timon Willi, Clare Lyle, Jesse Farebrother, Jakob Nicolaus Foerster, Gintare Karolina Dziugaite, Doina Precup, and Pablo Samuel Castro. Mixtures of experts unlock parameter scaling for deep rl. In *International Conference on Machine Learning*, pages 38520–38540. PMLR, 2024b.
- <span id="page-12-6"></span>Aakanksha Chowdhery, Sharan Narang, Jacob Devlin, Maarten Bosma, Gaurav Mishra, Adam Roberts, Paul Barham, Hyung Won Chung, Charles Sutton, Sebastian Gehrmann, et al. Palm: Scaling language modeling with pathways. *Journal of Machine Learning Research*, 24(240):1–113, 2023.
- <span id="page-12-10"></span>Benjamin Ellis, Matthew T Jackson, Andrei Lupu, Alexander D Goldie, Mattie Fellows, Shimon Whiteson, and Jakob Foerster. Adam on local time: Addressing nonstationarity in rl with relative adam timesteps. *Advances in Neural Information Processing Systems*, 37:134567–134590, 2024.
- <span id="page-12-9"></span>Lasse Espeholt, Hubert Soyer, Remi Munos, Karen Simonyan, Vlad Mnih, Tom Ward, Yotam Doron, Vlad Firoiu, Tim Harley, Iain Dunning, et al. Impala: Scalable distributed deep-rl with importance weighted actor-learner architectures. In *International conference on machine learning*, pages 1407–1416. PMLR, 2018.
- <span id="page-12-1"></span>Jesse Farebrother, Joshua Greaves, Rishabh Agarwal, Charline Le Lan, Ross Goroshin, Pablo Samuel Castro, and Marc G Bellemare. Proto-value networks: Scaling representation learning with auxiliary tasks. In *The Eleventh International Conference on Learning Representations*, 2023. URL <https://openreview.net/forum?id=oGDKSt9JrZi>.
- <span id="page-12-0"></span>Alhussein Fawzi, Matej Balog, Aja Huang, Thomas Hubert, Bernardino Romera-Paredes, Mohammadamin Barekatain, Alexander Novikov, Francisco J R Ruiz, Julian Schrittwieser, Grzegorz Swirszcz, et al. Discovering faster matrix multiplication algorithms with reinforcement learning. *Nature*, 610(7930):47–53, 2022.
- <span id="page-12-3"></span>Scott Fujimoto, Herke Hoof, and David Meger. Addressing function approximation error in actorcritic methods. In *International conference on machine learning*, pages 1587–1596. PMLR, 2018.
- <span id="page-12-7"></span>Matteo Gallici, Mattie Fellows, Benjamin Ellis, Bartomeu Pou, Ivan Masmitja, Jakob Nicolaus Foerster, and Mario Martin. Simplifying deep temporal difference learning. In *The Thirteenth International Conference on Learning Representations*, 2025. URL <https://openreview.net/forum?id=7IzeL0kflu>.
- <span id="page-12-8"></span>Behrooz Ghorbani, Shankar Krishnan, and Ying Xiao. An investigation into neural net optimization via hessian eigenvalue density. In *International Conference on Machine Learning*, pages 2232–2241. PMLR, 2019.
- <span id="page-12-4"></span>Xavier Glorot and Yoshua Bengio. Understanding the difficulty of training deep feedforward neural networks. In *Proceedings of the thirteenth international conference on artificial intelligence and statistics*, pages 249–256. JMLR Workshop and Conference Proceedings, 2010.
- <span id="page-12-5"></span>Florin Gogianu, Tudor Berariu, Mihaela C Rosca, Claudia Clopath, Lucian Busoniu, and Razvan Pascanu. Spectral normalisation for deep reinforcement learning: an optimisation perspective. In *International Conference on Machine Learning*, pages 3734–3744. PMLR, 2021.
- <span id="page-12-11"></span>Vineet Gupta, Tomer Koren, and Yoram Singer. Shampoo: Preconditioned stochastic tensor optimization. In *International Conference on Machine Learning*, pages 1842–1850. PMLR, 2018.

- <span id="page-13-9"></span>Tuomas Haarnoja, Aurick Zhou, Pieter Abbeel, and Sergey Levine. Soft actor-critic: Off-policy maximum entropy deep reinforcement learning with a stochastic actor. In *International conference on machine learning*, pages 1861–1870. PMLR, 2018.
- <span id="page-13-5"></span>Beining Han, Zhizhou Ren, Zuofan Wu, Yuan Zhou, and Jian Peng. Off-policy reinforcement learning with delayed rewards. In *International conference on machine learning*, pages 8280–8303. PMLR, 2022.
- <span id="page-13-10"></span>Charles R Harris, K Jarrod Millman, Stéfan J Van Der Walt, Ralf Gommers, Pauli Virtanen, David Cournapeau, Eric Wieser, Julian Taylor, Sebastian Berg, Nathaniel J Smith, et al. Array programming with numpy. *Nature*, 585(7825):357–362, 2020.
- <span id="page-13-7"></span>Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition. In *Proceedings of the IEEE conference on computer vision and pattern recognition*, pages 770–778, 2016.
- <span id="page-13-8"></span>Matteo Hessel, Joseph Modayil, Hado Van Hasselt, Tom Schaul, Georg Ostrovski, Will Dabney, Dan Horgan, Bilal Piot, Mohammad Azar, and David Silver. Rainbow: Combining improvements in deep reinforcement learning. In *Proceedings of the AAAI conference on artificial intelligence*, volume 32, 2018.
- <span id="page-13-2"></span>Geoffrey Hinton. Lecture 6.5-rmsprop: Divide the gradient by a running average of its recent magnitude. *COURSERA: Neural networks for machine learning*, 4(2):26, 2012.
- <span id="page-13-13"></span>Gao Huang, Zhuang Liu, Laurens Van Der Maaten, and Kilian Q Weinberger. Densely connected convolutional networks. In *Proceedings of the IEEE conference on computer vision and pattern recognition*, pages 4700–4708, 2017.
- <span id="page-13-11"></span>John D Hunter. Matplotlib: A 2d graphics environment. *Computing in science & engineering*, 9(03): 90–95, 2007.
- <span id="page-13-6"></span>Andrew Ilyas, Logan Engstrom, Shibani Santurkar, Dimitris Tsipras, Firdaus Janoos, Larry Rudolph, and Aleksander Madry. A closer look at deep policy gradients. In *International Conference on Learning Representations*, 2020. URL <https://openreview.net/forum?id=ryxdEkHtPS>.
- <span id="page-13-3"></span>Sergey Ioffe and Christian Szegedy. Batch normalization: Accelerating deep network training by reducing internal covariate shift. In *International conference on machine learning*, pages 448–456. pmlr, 2015.
- <span id="page-13-0"></span>Arthur Jacot, Franck Gabriel, and Clément Hongler. Neural tangent kernel: Convergence and generalization in neural networks. *Advances in neural information processing systems*, 31, 2018.
- <span id="page-13-4"></span>Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models. *arXiv preprint arXiv:2001.08361*, 2020.
- <span id="page-13-1"></span>Diederik P Kingma and Jimmy Ba. Adam: A method for stochastic optimization. *arXiv preprint arXiv:1412.6980*, 2014.
- <span id="page-13-12"></span>Thomas Kluyver, Benjain Ragan-Kelley, Fernando Pérez, Brian Granger, Matthias Bussonnier, Jonathan Frederic, Kyle Kelley, Jessica Hamrick, Jason Grout, Sylvain Corlay, Paul Ivanov, Damián Avila, Safia Abdalla, Carol Willing, and Jupyter Development Team. Jupyter Notebooks—a publishing format for reproducible computational workflows. In *IOS Press*, pages 87–90. 2016. doi: 10.3233/978-1-61499-649-1-87.

- <span id="page-14-5"></span>Alex Krizhevsky et al. Learning multiple layers of features from tiny images. 2009.
- <span id="page-14-6"></span>Aviral Kumar, Rishabh Agarwal, Dibya Ghosh, and Sergey Levine. Implicit under-parameterization inhibits data-efficient deep reinforcement learning. *arXiv preprint arXiv:2010.14498*, 2020.
- <span id="page-14-10"></span>Hojoon Lee, Dongyoon Hwang, Donghu Kim, Hyunseung Kim, Jun Jet Tai, Kaushik Subramanian, Peter R. Wurman, Jaegul Choo, Peter Stone, and Takuma Seno. Simba: Simplicity bias for scaling up parameters in deep reinforcement learning. In *The Thirteenth International Conference on Learning Representations*, 2025. URL <https://openreview.net/forum?id=jXLiDKsuDo>.
- <span id="page-14-3"></span>Namhoon Lee, Thalaiyasingam Ajanthan, Stephen Gould, and Philip H. S. Torr. A signal propagation perspective for pruning neural networks at initialization. In *International Conference on Learning Representations*, 2020. URL <https://openreview.net/forum?id=HJeTo2VFwH>.
- <span id="page-14-11"></span>Timothy P Lillicrap, Jonathan J Hunt, Alexander Pritzel, Nicolas Heess, Tom Erez, Yuval Tassa, David Silver, and Daan Wierstra. Continuous control with deep reinforcement learning. *arXiv preprint arXiv:1509.02971*, 2015.
- <span id="page-14-12"></span>Jiashun Liu, Johan Samir Obando Ceron, Aaron Courville, and Ling Pan. Neuroplastic expansion in deep reinforcement learning. In *The Thirteenth International Conference on Learning Representations*, 2025. URL <https://openreview.net/forum?id=20qZK2T7fa>.
- <span id="page-14-4"></span>Lu Lu, Yeonjong Shin, Yanhui Su, and George Em Karniadakis. Dying relu and initialization: Theory and numerical examples. *arXiv preprint arXiv:1903.06733*, 2019.
- <span id="page-14-0"></span>Clare Lyle, Mark Rowland, and Will Dabney. Understanding and preventing capacity loss in reinforcement learning. In *International Conference on Learning Representations*, 2022. URL [https:](https://openreview.net/forum?id=ZkC8wKoLbQ7) [//openreview.net/forum?id=ZkC8wKoLbQ7](https://openreview.net/forum?id=ZkC8wKoLbQ7).
- <span id="page-14-1"></span>Clare Lyle, Zeyu Zheng, Evgenii Nikishin, Bernardo Avila Pires, Razvan Pascanu, and Will Dabney. Understanding plasticity in neural networks. In *International Conference on Machine Learning*, pages 23190–23211. PMLR, 2023.
- <span id="page-14-2"></span>Clare Lyle, Zeyu Zheng, Khimya Khetarpal, James Martens, Hado P van Hasselt, Razvan Pascanu, and Will Dabney. Normalization and effective learning rates in reinforcement learning. *Advances in Neural Information Processing Systems*, 37:106440–106473, 2024.
- <span id="page-14-14"></span>Xuezhe Ma. Apollo: An adaptive parameter-wise diagonal quasi-newton method for nonconvex stochastic optimization. *arXiv preprint arXiv:2009.13586*, 2020.
- <span id="page-14-9"></span>Viktor Makoviychuk, Lukasz Wawrzyniak, Yunrong Guo, Michelle Lu, Kier Storey, Miles Macklin, David Hoeller, Nikita Rudin, Arthur Allshire, Ankur Handa, et al. Isaac gym: High performance gpu-based physics simulation for robot learning. *arXiv preprint arXiv:2108.10470*, 2021.
- <span id="page-14-8"></span>James Martens. New insights and perspectives on the natural gradient method. *Journal of Machine Learning Research*, 21(146):1–76, 2020.
- <span id="page-14-7"></span>James Martens and Roger Grosse. Optimizing neural networks with kronecker-factored approximate curvature. In *International conference on machine learning*, pages 2408–2417. PMLR, 2015.
- <span id="page-14-13"></span>Wes McKinney. *Python for Data Analysis: Data Wrangling with Pandas, NumPy, and IPython*. O'Reilly Media, 1 edition, February 2013. ISBN 9789351100065. URL [http://www.amazon.com/exec/obidos/](http://www.amazon.com/exec/obidos/redirect?tag=citeulike07-20&path=ASIN/1449319793) [redirect?tag=citeulike07-20&path=ASIN/1449319793](http://www.amazon.com/exec/obidos/redirect?tag=citeulike07-20&path=ASIN/1449319793).

- <span id="page-15-0"></span>Volodymyr Mnih, Koray Kavukcuoglu, David Silver, Andrei A. Rusu, Joel Veness, Marc G. Bellemare, Alex Graves, Martin Riedmiller, Andreas K. Fidjeland, Georg Ostrovski, Stig Petersen, Charles Beattie, Amir Sadik, Ioannis Antonoglou, Helen King, Dharshan Kumaran, Daan Wierstra, Shane Legg, and Demis Hassabis. Human-level control through deep reinforcement learning. *Nature*, 518(7540):529–533, February 2015.
- <span id="page-15-11"></span>Aneesh Muppidi, Zhiyu Zhang, and Heng Yang. Fast trac: A parameter-free optimizer for lifelong reinforcement learning. *Advances in Neural Information Processing Systems*, 37:51169–51195, 2024.
- <span id="page-15-10"></span>Michal Nauman, Mateusz Ostaszewski, Krzysztof Jankowski, Piotr Miło´s, and Marek Cygan. Bigger, regularized, optimistic: scaling for compute and sample efficient continuous control. In *The Thirty-eighth Annual Conference on Neural Information Processing Systems*, 2024.
- <span id="page-15-3"></span>Johan Obando Ceron, Marc Bellemare, and Pablo Samuel Castro. Small batch deep reinforcement learning. *Advances in Neural Information Processing Systems*, 36:26003–26024, 2023.
- <span id="page-15-12"></span>Travis E. Oliphant. Python for scientific computing. *Computing in Science & Engineering*, 9(3):10–20, 2007. doi: 10.1109/MCSE.2007.58.
- <span id="page-15-9"></span>Kei Ota, Devesh K Jha, and Asako Kanezaki. Training larger networks for deep reinforcement learning. *arXiv preprint arXiv:2102.07920*, 2021.
- <span id="page-15-13"></span>Kei Ota, Devesh K Jha, and Asako Kanezaki. A framework for training larger networks for deep reinforcement learning. *Machine Learning*, 113(9):6115–6139, 2024.
- <span id="page-15-1"></span>Razvan Pascanu, Tomas Mikolov, and Yoshua Bengio. On the difficulty of training recurrent neural networks. In *International conference on machine learning*, pages 1310–1318. Pmlr, 2013.
- <span id="page-15-2"></span>Jeffrey Pennington, Samuel Schoenholz, and Surya Ganguli. Resurrecting the sigmoid in deep learning through dynamical isometry: theory and practice. *Advances in neural information processing systems*, 30, 2017.
- <span id="page-15-4"></span>Samuel S Schoenholz, Justin Gilmer, Surya Ganguli, and Jascha Sohl-Dickstein. Deep information propagation. In *International Conference on Learning Representations*, 2017.
- <span id="page-15-8"></span>John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. Proximal policy optimization algorithms. *arXiv preprint arXiv:1707.06347*, 2017.
- <span id="page-15-5"></span>Max Schwarzer, Johan Samir Obando Ceron, Aaron Courville, Marc G Bellemare, Rishabh Agarwal, and Pablo Samuel Castro. Bigger, better, faster: Human-level Atari with human-level efficiency. In Andreas Krause, Emma Brunskill, Kyunghyun Cho, Barbara Engelhardt, Sivan Sabato, and Jonathan Scarlett, editors, *Proceedings of the 40th International Conference on Machine Learning*, volume 202 of *Proceedings of Machine Learning Research*, pages 30365–30380. PMLR, 23–29 Jul 2023. URL <https://proceedings.mlr.press/v202/schwarzer23a.html>.
- <span id="page-15-6"></span>Yeonjong Shin and George Em Karniadakis. Trainability of relu networks and data-dependent initialization. *Journal of Machine Learning for Modeling and Computing*, 1(1), 2020.
- <span id="page-15-7"></span>Ghada Sokar, Rishabh Agarwal, Pablo Samuel Castro, and Utku Evci. The dormant neuron phenomenon in deep reinforcement learning. In *International Conference on Machine Learning*, pages 32145–32168. PMLR, 2023.

- <span id="page-16-8"></span>Ghada Sokar, Johan Samir Obando Ceron, Aaron Courville, Hugo Larochelle, and Pablo Samuel Castro. Don't flatten, tokenize! unlocking the key to softmoe's efficacy in deep RL. In *The Thirteenth International Conference on Learning Representations*, 2025. URL [https://openreview.net/forum?](https://openreview.net/forum?id=8oCrlOaYcc) [id=8oCrlOaYcc](https://openreview.net/forum?id=8oCrlOaYcc).
- <span id="page-16-4"></span>Richard S. Sutton and Andrew G. Barto. *Reinforcement Learning: An Introduction*. A Bradford Book, Cambridge, MA, USA, 2018. ISBN 0262039249.
- <span id="page-16-1"></span>Adrien Ali Taiga, Rishabh Agarwal, Jesse Farebrother, Aaron Courville, and Marc G Bellemare. Investigating multi-task pretraining and generalization in reinforcement learning. In *The Eleventh International Conference on Learning Representations*, 2023. URL [https://openreview.net/forum?](https://openreview.net/forum?id=sSt9fROSZRO) [id=sSt9fROSZRO](https://openreview.net/forum?id=sSt9fROSZRO).
- <span id="page-16-7"></span>Yuval Tassa, Yotam Doron, Alistair Muldal, Tom Erez, Yazhe Li, Diego de Las Casas, David Budden, Abbas Abdolmaleki, Josh Merel, Andrew Lefrancq, et al. Deepmind control suite. *arXiv preprint arXiv:1801.00690*, 2018.
- <span id="page-16-3"></span>Hado Van Hasselt, Arthur Guez, and David Silver. Deep reinforcement learning with double q-learning. In *Proceedings of the AAAI conference on artificial intelligence*, volume 30, 2016.
- <span id="page-16-5"></span>Hado Van Hasselt, Yotam Doron, Florian Strub, Matteo Hessel, Nicolas Sonnerat, and Joseph Modayil. Deep reinforcement learning and the deadly triad. *arXiv preprint arXiv:1812.02648*, 2018.
- <span id="page-16-11"></span>Guido Van Rossum and Fred L Drake Jr. *Python reference manual*. Centrum voor Wiskunde en Informatica Amsterdam, 1995.
- <span id="page-16-0"></span>Oriol Vinyals, Igor Babuschkin, Wojciech M Czarnecki, Michaël Mathieu, Andrew Dudzik, Junyoung Chung, David H Choi, Richard Powell, Timo Ewalds, Petko Georgiev, et al. Grandmaster level in starcraft ii using multi-agent reinforcement learning. *Nature*, 575(7782):350–354, 2019.
- <span id="page-16-6"></span>Kevin Wang, Ishaan Javali, Micha´L Bortkiewicz, Benjamin Eysenbach, et al. 1000 layer networks for self-supervised rl: Scaling depth can enable new goal-reaching capabilities. *arXiv preprint arXiv:2503.14858*, 2025.
- <span id="page-16-9"></span>Timon Willi, Johan Obando-Ceron, Jakob Foerster, Karolina Dziugaite, and Pablo Samuel Castro. Mixture of experts in a mixture of rl settings. *arXiv preprint arXiv:2406.18420*, 2024.
- <span id="page-16-10"></span>Yuhuai Wu, Elman Mansimov, Roger B Grosse, Shun Liao, and Jimmy Ba. Scalable trust-region method for deep reinforcement learning using kronecker-factored approximation. *Advances in neural information processing systems*, 30, 2017.
- <span id="page-16-2"></span>Zeyu Zheng, Junhyuk Oh, and Satinder Singh. On learning intrinsic rewards for policy gradient methods. *Advances in neural information processing systems*, 31, 2018.
- <span id="page-16-12"></span>Juntang Zhuang, Tommy Tang, Yifan Ding, Sekhar C Tatikonda, Nicha Dvornek, Xenophon Papademetris, and James Duncan. Adabelief optimizer: Adapting stepsizes by the belief in observed gradients. *Advances in neural information processing systems*, 33:18795–18806, 2020.

# **A Environment Details**

Throughout the paper, we evaluate the deep reinforcement learning agents' performance on the Atari-10 suite [\(Aitchison et al.,](#page-11-5) [2023\)](#page-11-5), a curated subset of games from the Arcade Learning Environment (ALE) [\(Bellemare et al.,](#page-11-7) [2013\)](#page-11-7). Atari-10 consists of 10 games selected to capture the maximum variance in algorithm performance, achieving over 90% correlation with results on the full ALE benchmark. This makes it a computationally efficient yet representative testbed for deep reinforcement learning. We follow the experimental protocol of [Agarwal et al.](#page-11-8) [\(2021\)](#page-11-8), [Ceron et al.](#page-12-2) [\(2024b\)](#page-12-2), [Obando Ceron et al.](#page-15-3) [\(2023\)](#page-15-3), running each experiment with three random seeds and reporting the aggregate human-normalized score across games.

The games in Atari-10 are:

• Amidar, Battle Zone, Bowling, Double Dunk, Frostbite, Kung Fu Master, Name This Game, Phoenix, Q\*Bert and River Raid.

Additionally, to further support the generality of our findings, we evaluate the proposed combined gradient interventions on the full ALE benchmark. We also assess their effectiveness on continuous control tasks from the IsaacGym simulator [\(Makoviychuk et al.,](#page-14-9) [2021\)](#page-14-9) and the DeepMind Control Suite (DMC) [\(Tassa et al.,](#page-16-7) [2018\)](#page-16-7), extending our analysis to robotics-based environments. We conduct experiments on the 4 challenging tasks of DMC:

• Humanoid Walk, Humanoid Run, Dog Trot and Dog Run.

# **B Network Sizes**

Throughout the paper, we experiment with models of varying depths and widths. Unless stated otherwise (e.g. in [section 5,](#page-7-0) where we evaluate the Impala CNN), the convolutional feature extractors are kept fixed. Consequently, our experiments focus primarily on scaling strategies and architectural variations in the MLP components of the networks.

To enable meaningful comparisons across different learning regimes, the MLP architectures are kept consistent across supervised learning (SL), non-stationary SL, and reinforcement learning (RL) experiments. This consistency ensures that observed differences in gradient behavior arise from the learning setting itself, rather than confounding factors due to domain-specific architectures.

<span id="page-17-0"></span>Table [1](#page-17-0) provides detailed information on the number of parameters for each depth–width configuration, categorized as small, medium, or large, as used throughout the paper.

| Depth / Width | Small | Medium | Large |
|---------------|-------|--------|-------|
| Small         | 2.39  | 11.90  | 27.70 |
| Medium        | 3.45  | 21.35  | 53.93 |

**Large** 4.50 30.79 80.15

Table 1: Number of parameters (in millions) for different MLP architectures.

# **C Additional Experiments**

### <span id="page-18-0"></span>**C.1 Scaling with DQN and Rainbow**

To further support our hypothesis on the emergence of gradient pathologies in deep reinforcement learning, we investigate whether similar issues arise in algorithms beyond PQN and PPO, as discussed in the main paper. Specifically, we study the effects of architectural scaling on two widely used value-based algorithms: DQN [\(Mnih et al.,](#page-15-0) [2015\)](#page-15-0) and Rainbow [\(Hessel et al.,](#page-13-8) [2018\)](#page-13-8).

DQN is a foundational deep RL algorithm that learns action-value functions using temporal difference updates and experience replay, serving as a standard baseline for value-based methods. Rainbow extends DQN by integrating several enhancements, such as double Q-learning, prioritized experience replay, dueling networks, multi-step learning, distributional value functions, and noisy exploration, to achieve improved sample efficiency and stability.

In [Figure 11,](#page-18-1) we report the performance of DQN and Rainbow as we scale the depth and width of their networks. As with PQN and PPO, we observe consistent degradation in performance at larger scales. In [Figure 12,](#page-19-0) we present the corresponding gradient behavior, which reveals the same vanishing and destabilization phenomena discussed in this work. These findings reinforce the generality of the identified gradient pathologies across both policy-based and value-based deep RL algorithms.

<span id="page-18-1"></span>![](_page_18_Figure_5.jpeg)

Figure 11: **Median human normalized scores for DQN (left) and Rainbow (right) as a function of total network parameters.** Lines of different colors denote varying network depths, while marker shapes indicate different widths. For both agents, performance consistently declines as network size increases, highlighting the adverse effects of scaling.

#### **C.2 Combining Gradient Interventions in Non-stationary Supervised Learning**

Building on our findings in [subsection 4.3,](#page-7-2) we extend our analysis by applying the proposed combined gradient interventions to the same image classification models used in [section 3.](#page-3-0) Specifically, we train the models in the non-stationary supervised learning setup, where the CIFAR-10 labels are iteratively shuffled, following the experimental design from [Sokar et al.](#page-15-7) [\(2023\)](#page-15-7). As demonstrated in [section 3,](#page-3-0) while models in standard supervised learning settings are able to scale effectively and maintain high performance, introducing non-stationarity leads to failure in adaptation for baselines that use fully connected layers and the Adam optimizer. This issue is exacerbated as model scale increases.

Our results, presented in [Figure 7,](#page-8-0) show that combining the multi-skip architecture for the MLP component with the Kronecker-factored optimizer and Layer Normalization enables near-perfect

<span id="page-19-0"></span>![](_page_19_Figure_0.jpeg)

Figure 12: **Gradient magnitudes during training for DQN (top) and Rainbow (bottom).** As network depth increases, gradient flow systematically diminishes, ultimately collapsing to near-zero values. This consistent decay mirrors the performance degradation observed at larger scales.

continuous adaptation. The models quickly adapt to the changing optimization problem following label reshuffling, with gradient magnitudes remaining stable throughout the process.

#### C.3 Architecture and Optimizer Ablations

In this work, we introduce the multi-skip architecture, an extension of the standard residual MLP design, and propose the use of the Kronecker-factored optimizer for online deep RL. While these techniques form the basis of our primary interventions, our broader goal is not to prescribe a fixed set of methods, but rather to motivate a general class of architectural and optimization interventions that promote healthy gradient flow in deep networks. To this end, we expand the scope of our evaluation by incorporating a wider range of baselines. Specifically, we compare various optimizer choices, including Adam and AdaBelief (Zhuang et al., 2020), alongside MLP architectures such as the standard residuapl MLP (He et al., 2016) and DenseNet (Huang et al., 2017). These architectures have been previously explored in the context of scaling networks in online deep RL (Lee et al., 2025, Ota et al., 2024), providing a relevant basis for comparison.

We also evaluated state-of-the-art optimizers that have demonstrated success in training large-scale models such as transformers in supervised learning. Specifically, we tested Shampoo (Gupta et al., 2018), a second-order optimizer that maintains and preconditions gradients using full-matrix statistics per layer, and Apollo (Ma, 2020), an adaptive optimizer that leverages curvature information without explicitly computing or storing second-order matrices.

Despite extensive hyperparameter tuning for both methods, we were unable to achieve strong performance in the online deep RL setting. This suggests that further investigation is needed to understand the key properties required for these optimizers to be effective in this regime. Asadi et al. (2023), Ceron and Castro (2021) demonstrate that optimizer behavior plays a critical role in the training dynamics of online deep RL methods, with Asadi et al. (2023) showing that stale optimizer states can hinder learning, and Ceron and Castro (2021) revealing that optimizer sensitivity interacts with the choice of loss function, particularly when comparing Huber and MSE losses.

We present the results for PPO and PQN across all tested optimizers in [Figure 13.](#page-20-3)

<span id="page-20-3"></span>![](_page_20_Figure_1.jpeg)

Figure 13: **Median human normalized scores on Atari-10 for PPO (top row) and PQN (bottom row), comparing a range of optimizers including RAdam, AdaBelief, Shampoo, Apollo, and Kron (shown in the main curves).** While adaptive optimizers like AdaBelief show some robustness, only Kron consistently enables stable and performant training as models scale. Each curve represents the mean performance across three random seeds per algorithm, with shaded areas indicating 95% bootstrap confidence intervals.

<span id="page-20-0"></span>**Results with the Multi-Skip Architecture.** We present the full learning curves comparing the proposed multi-skip architecture to the baseline fully connected architecture across all depths and widths studied in the paper. We follow the experimental protocol of [Agarwal et al.](#page-11-8) [\(2021\)](#page-11-8), [Ceron](#page-12-2) [et al.](#page-12-2) [\(2024b\)](#page-12-2), [Obando Ceron et al.](#page-15-3) [\(2023\)](#page-15-3), running each experiment with three random seeds.

<span id="page-20-1"></span>**Results with the Kron Optimizer.** We present the full learning curves comparing the Kron optimizer to the baseline RAdam optimizer originally used in PQN [\(Gallici et al.,](#page-12-7) [2025\)](#page-12-7), across all depths and widths studied in the paper. We follow the experimental protocol of [Agarwal et al.](#page-11-8) [\(2021\)](#page-11-8), [Ceron et al.](#page-12-2) [\(2024b\)](#page-12-2), [Obando Ceron et al.](#page-15-3) [\(2023\)](#page-15-3), running each experiment with three random seeds.

### <span id="page-20-2"></span>**C.4 Results on the Full ALE**

In this section, we provide the full training curves corresponding to the aggregated results shown in [subsection 4.3,](#page-7-2) where we evaluate the performance of the PQN and PPO agents on the full set of environments from the ALE after applying our two proposed gradient interventions. The per-environment learning curves are presented in [Figure 16](#page-22-0) for PQN and [Figure 17](#page-23-0) for PPO. We

![](_page_21_Figure_0.jpeg)

Figure 14: **Median human-normalized scores with PQN on the Atari-10 benchmark, comparing the baseline agent and the proposed multi-skip architecture across varying depths and widths.** The multi-skip architecture not only improves performance at shallow depths, but also enables PQN to remain trainable across all scales considered, whereas the baseline MLP rapidly collapses as depth and width increase. Each curve represents the mean performance across three random seeds per algorithm, with shaded areas indicating 95% bootstrap confidence intervals.

![](_page_21_Figure_2.jpeg)

Figure 15: **Median human-normalized scores with PQN on the Atari-10 benchmark, comparing the Kron optimizer to the baseline RAdam optimizer across varying depths and widths.** Similar to the multi-skip architecture, Kron not only improves performance at shallow depths, but also enables PQN to remain trainable across all scales considered. In contrast, performance with RAdam rapidly collapses as depth and width increase. Each curve represents the mean performance across thee random seeds per algorithm, with shaded areas indicating 95% bootstrap confidence intervals.

follow the experimental protocol of [Agarwal et al.](#page-11-8) [\(2021\)](#page-11-8), [Ceron et al.](#page-12-2) [\(2024b\)](#page-12-2), [Obando Ceron et al.](#page-15-3) [\(2023\)](#page-15-3), running each experiment with three random seeds.

<span id="page-22-0"></span>![](_page_22_Figure_0.jpeg)

Figure 16: Mean human-normalized score on the full ALE suite, comparing the baseline PQN agent (light curves) with the augmented agent using our combined gradient interventions (dark curves).

<span id="page-23-0"></span>![](_page_23_Figure_0.jpeg)

Figure 17: Mean human-normalized score on the full ALE suite, comparing the baseline PPO agent (light curves) with the augmented agent using our combined gradient interventions (dark curves).

#### <span id="page-24-0"></span>C.5 Simba on DMC

In this section, we present the full results accompanying the experiments combining Simba (Lee et al., 2025) with our proposed gradient interventions, as introduced in subsection 4.3. For these experiments, we retain Simba's original architectural choices but replace the AdamW optimizer with Kron.

We compare Simba using both SAC and DDPG as the underlying RL algorithms. While SAC generally outperforms DDPG, we consistently observe that scaling depth and width, either independently or jointly, leads to a degradation in performance with Simba. However, this degradation is mitigated, and in many cases reversed, when using the Kron optimizer, resulting in improved performance as model capacity increases.

The following figures illustrate these findings:

![](_page_24_Figure_4.jpeg)

Figure 18: SAC scaling depth

![](_page_24_Figure_6.jpeg)

Figure 19: SAC scaling width

![](_page_24_Figure_8.jpeg)

Figure 20: SAC scaling both depth and width

![](_page_25_Figure_0.jpeg)

Figure 21: DDPG scaling depth

![](_page_25_Figure_2.jpeg)

Figure 22: DDPG scaling width

![](_page_25_Figure_4.jpeg)

Figure 23: DDPG scaling both depth and width

# D Hyper-parameters

Below, we provide details of the hyperparameters used throughout the paper for each algorithm. In general, they match those proposed in the corresponding original papers.

Table 2: PQN Hyperparameters

| Hyperparameter       | Value / Description                    |  |
|----------------------|----------------------------------------|--|
| Learning rate        | 2.5e-4                                 |  |
| Anneal lr            | False (no learning rate annealing)     |  |
| Num envs             | 128 (parallel environments)            |  |
| Num steps            | 32 (steps per rollout per environment) |  |
| Gamma                | 0.99 (discount factor)                 |  |
| Num minibatches      | 32                                     |  |
| Update epochs        | 2 (policy update epochs)               |  |
| Max grad norm        | 10.0 (gradient clipping)               |  |
| Start e              | 1.0 (initial exploration rate)         |  |
| End e                | 0.005 (final exploration rate)         |  |
| Exploration fraction | 0.10 (exploration annealing fraction)  |  |
| Q lambda             | 0.65 (Q(λ) parameter)                  |  |
| Use ln               | True (use layer normalization)         |  |
| Activation fn        | relu (activation function)             |  |

Table 3: PPO Hyperparameters

| Hyperparameter  | Value / Description                                 |
|-----------------|-----------------------------------------------------|
| Learning rate   | 2.5e-4                                              |
| Num envs        | 8                                                   |
| Num steps       | 128 (steps per rollout per environment)             |
| Anneal lr       | True (learning rate annealing enabled)              |
| Gamma           | 0.99 (discount factor)                              |
| Gae lambda      | 0.95 (GAE parameter)                                |
| Num minibatches | 4                                                   |
| Update epochs   | 4                                                   |
| Norm adv        | True (normalize advantages)                         |
| Clip coef       | 0.1 (PPO clipping coefficient)                      |
| Clip vloss      | True (clip value loss)                              |
| Ent coef        | 0.01 (entropy regularization coefficient)           |
| Vf coef         | 0.5 (value function loss coefficient)               |
| Max grad norm   | 0.5 (gradient clipping threshold)                   |
| Use ln          | False (no layer normalization)                      |
| Activation fn   | relu (activation function)                          |
| Shared cnn      | True (shared CNN between policy and value networks) |

Table 4: PPO Hyperparameters for IsaacGym

| Hyperparameter  | Value / Description                     |
|-----------------|-----------------------------------------|
| Total timesteps | 30,000,000                              |
| Learning rate   | 0.0026                                  |
| Num envs        | 4096 (parallel environments)            |
| Num steps       | 16 (steps per rollout)                  |
| Anneal lr       | False (disable learning rate annealing) |
| Gamma           | 0.99 (discount factor)                  |
| Gae lambda      | 0.95 (GAE lambda)                       |
| Num minibatches | 2                                       |
| Update epochs   | 4 (update epochs per PPO iteration)     |
| Norm adv        | True (normalize advantages)             |
| Clip coef       | 0.2 (policy clipping coefficient)       |
| Clip vloss      | False (disable value function clipping) |
| Ent coef        | 0.0 (entropy coefficient)               |
| Vf coef         | 2.0 (value function loss coefficient)   |
| Max grad norm   | 1.0 (max gradient norm)                 |
| Use ln          | False (no layer normalization)          |
| Activation fn   | relu (activation function)              |

Table 5: DQN Hyperparameters

| Hyperparameter           | Value / Description                          |
|--------------------------|----------------------------------------------|
| Learning rate            | 1e-4                                         |
| Num envs                 | 1                                            |
| Buffer size              | 1,000,000 (replay memory size)               |
| Gamma                    | 0.99 (discount factor)                       |
| Tau                      | 1.0 (target network update rate)             |
| Target network frequency | 1000 (timesteps per target update)           |
| Batch size               | 32                                           |
| Start e                  | 1.0 (initial exploration epsilon)            |
| End e                    | 0.01 (final exploration epsilon)             |
| Exploration fraction     | 0.10 (fraction of total timesteps for decay) |
| Learning starts          | 80,000 (timesteps before training starts)    |
| Train frequency          | 4 (training frequency)                       |
| Use ln                   | False (no layer normalization)               |
| Activation fn            | relu (activation function)                   |

Table 6: Rainbow Hyperparameters

| Hyperparameter<br>Value / Description |                                              |
|---------------------------------------|----------------------------------------------|
| Learning rate                         | 6.25e-5                                      |
| Num envs                              | 1                                            |
| Buffer size                           | 1,000,000 (replay memory size)               |
| Gamma                                 | 0.99 (discount factor)                       |
| Tau                                   | 1.0 (target network update rate)             |
| Target network frequency              | 8000 (timesteps per target update)           |
| Batch size                            | 32                                           |
| Start e                               | 1.0 (initial exploration epsilon)            |
| End e                                 | 0.01 (final exploration epsilon)             |
| Exploration fraction                  | 0.10 (fraction of total timesteps for decay) |
| Learning starts                       | 80,000 (timesteps before training starts)    |
| Train frequency                       | 4 (training frequency)                       |
| N step                                | 3 (n-step Q-learning horizon)                |
| Prioritized replay alpha              | 0.5                                          |
| Prioritized replay beta               | 0.4                                          |
| Prioritized replay eps                | 1e-6                                         |
| N atoms                               | 51 (number of atoms in distributional RL)    |
| V min                                 | -10 (value distribution lower bound)         |
| V max                                 | 10 (value distribution upper bound)          |
| Use ln                                | False (no layer normalization)               |
| Activation fn                         | relu (activation function)                   |

Table 7: Image Classification Hyperparameters (CIFAR-10)

| Hyperparameter | Value   |
|----------------|---------|
| Batch size     | 256     |
| Epochs         | 100     |
| Learning rate  | 0.00025 |

Table 8: SAC Hyperparameters

| Hyperparameter                 | Value / Description     |
|--------------------------------|-------------------------|
| Critic block type              | SimBa                   |
| Critic num blocks              | {2, 4, 6, 8}            |
| Critic hidden dim              | {512, 1024, 1536, 2048} |
| Target critic momentum (τ<br>) | 5e-3                    |
| Actor block type               | SimBa                   |
| Actor num blocks               | {1, 2, 3, 4}            |
| Actor hidden dim               | {128, 256, 384, 512}    |
| Initial temperature (α0)       | 1e-2                    |
| Temperature learning rate      | 1e-4                    |
| Target entropy (H∗<br>)        | A /2                    |
| Batch size                     | 256                     |
| Optimizer                      | {AdamW, Kron}           |
| AdamW's learning rate          | 1e-4                    |
| Kron's learning rate           | 5e-5                    |
| Optimizer momentum (β1,<br>β2) | (0.9, 0.999)            |
| Weight decay (λ)               | 1e-2                    |
| Discount (γ)                   | Heuristic               |
| Replay ratio                   | 2                       |
| Clipped Double Q               | False                   |

Table 9: DDPG Hyperparameters

| Table 9: DDPG Hyperparameters  |                           |  |  |
|--------------------------------|---------------------------|--|--|
| Hyperparameter                 | Value / Description       |  |  |
| Critic block type              | SimBa                     |  |  |
| Critic num blocks              | {2, 4, 6, 8}              |  |  |
| Critic hidden dim              | {512, 1024, 1536, 2048}   |  |  |
| Critic learning rate           | 1e-4                      |  |  |
| Target critic momentum (τ<br>) | 5e-3                      |  |  |
| Actor block type               | SimBa                     |  |  |
| Actor num blocks               | {1, 2, 3, 4}              |  |  |
| Actor hidden dim               | {128, 256, 384, 512}      |  |  |
| Actor learning rate            | 1e-4                      |  |  |
| Exploration noise              | 2<br>N<br>(0,<br>0.1<br>) |  |  |
| Batch size                     | 256                       |  |  |
| Optimizer                      | {AdamW, Kron}             |  |  |
| AdamW's learning rate          | 1e-4                      |  |  |
| Kron's learning rate           | 5e-5                      |  |  |
| Optimizer momentum (β1,<br>β2) | (0.9, 0.999)              |  |  |
| Weight decay (λ)               | 1e-2                      |  |  |
| Discount (γ)                   | Heuristic                 |  |  |
| Replay ratio                   | 2                         |  |  |
| Clipped Double Q               | False                     |  |  |

# **E Compute Details**

All experiments were conducted on a single-GPU setup using an NVIDIA RTX 8000, 12 CPU workers, and 50GB of RAM.

<span id="page-31-0"></span>Table 10: **Training times across model scales for two optimizers** K-FAC shows increased cost as depth and width grow.

| Depth  | Width  | Optimizer | Time   |
|--------|--------|-----------|--------|
| RAdam  |        |           |        |
| Small  | Small  | Adam      | 51m    |
| Small  | Medium | Adam      | 53m    |
| Small  | Large  | Adam      | 57m    |
| Medium | Small  | Adam      | 1h 4m  |
| Medium | Medium | Adam      | 1h 10m |
| Medium | Large  | Adam      | 1h 11m |
| Large  | Small  | Adam      | 1h 18m |
| Large  | Medium | Adam      | 1h 18m |
| Large  | Large  | Adam      | 1h 27m |
| Kron   |        |           |        |
| Small  | Small  | Kron      | 1h 59m |
| Small  | Medium | Kron      | 2h 27m |
| Small  | Large  | Kron      | 3h 38m |
| Medium | Small  | Kron      | 2h 44m |
| Medium | Medium | Kron      | 3h 32m |
| Medium | Large  | Kron      | 5h 59m |
| Large  | Small  | Kron      | 3h 27m |
| Large  | Medium | Kron      | 4h 36m |
| Large  | Large  | Kron      | 7h 42m |