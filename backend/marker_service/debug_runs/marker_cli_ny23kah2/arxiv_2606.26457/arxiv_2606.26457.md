# A probabilistic framework for online test-time adaptation

Daniel Corrales<sup>a, b</sup> and David Ríos Insua <sup>a</sup>

<sup>a</sup>Institute of Mathematical Sciences, ICMAT-CSIC, 28049 Madrid, Spain <sup>b</sup>Escuela de Doctorado, Universidad Autónoma de Madrid, 28049 Madrid, Spain

#### Abstract

This paper presents a probabilistic framework for online test-time adaptation problems. In them, a model is trained on labeled data but must adapt to unlabeled data at test time under the assumption that training and test distributions potentially differ, that is, there might have been a distributional shift. The framework is based on a state-space modelling architecture from which parameter learning, parameter time evolution, prior tuning, and prediction can be characterized.

## 1 Introduction and prior work

One limitation of standard supervised discriminative learning [2] is that it assumes the environment is static after learning and, once the learning stage is over, the new incoming data is identically distributed, so the model will perform as well as it did in the learning phase. However, this is not always the case [26]. Some examples include recommender systems affected by changes in user behaviour, disease-monitoring models deployed in different hospitals on patients with different characteristics, or automatic driving systems as they circulate on roads under different atmospheric conditions [15], not to mention cases in which adversaries alter data with malicious purposes [1]. To solve this issue, we may need to collect labeled data from the new environment and update and redo, at least, part of the learning process. Yet, both label collection and retraining are expensive tasks in terms of time and money. Thus, developing techniques to reduce such costs is desirable for the practical deployment of discriminative models in real-world scenarios.

Although standard supervised discriminative learning is generally framed in such a way that it cannot leverage unlabelled data, several structural assumptions can be imposed in the learning process of a discriminative model to account for both labeled and unlabeled data simultaneously, resulting in the field of semi-supervised learning [29]. Some of these structural assumptions include smoothness (if two data points in a high-density region are close, then so should be their corresponding labels); the manifold assumption (high-dimensional data lie roughly on a low-dimensional manifold); or low-density separation (for classification problems, decision boundaries should lie in low-density regions). Although these properties naturally arise in statistical learning, they actually become a design choice in semi-supervised learning.

Test-time adaptation [30] deals with the situation in which we have a pretrained parametric model,  $p(\mathbf{y}^S|\mathbf{x}^S,\Theta)$ , parameterized by  $\Theta$ , trained using source labeled data  $\mathcal{D}_S = \{(\mathbf{x}_n^S,\mathbf{y}_n^S)\}_{n=1}^N$ , and used for multi-class classification, together with an unlabeled dataset  $\mathcal{X}^T = \{\mathbf{x}_m^T\}_{m=1}^M$ , with potential distributional shift from the data used in training. If this pretrained model could correctly predict over the whole data space, then a change in  $p(\mathbf{x})$  would not affect the predictions in any way. However, data is usually scarce, and predictive models are accurate only in parts of the input space close to the training data. Therefore, they can be

affected by covariate shift, that is, situations in which  $p(\mathbf{x}^S) \neq p(\mathbf{x}^T)$ . The main motivation of TTA is to adapt the parameters of a pretrained model to improve its predictive performance on the target domain, or on both source and target domains. Online TTA (OTTA) deals with the situation in which there is a temporal covariate shift, for which adaptation shall be done sequentially [21, 34].

The vast majority of works on TTA [24, 27, 31, 35] employ entropy minimization [9] to leverage unlabeled data. This entails a low-density assumption that relies on the premise that all inputs X should have a corresponding unique labelling Y, and thus the data aleatoric uncertainty should be low. Usually employed in the form of a loss function, entropy minimization separates clusters of features and forces the classification boundary to be as far from the clusters as possible. Using this unsupervised loss naively on any random parameter initialization will most likely not result in good predictive results. However, recall that, in TTA, this loss is used on a pretrained model. Therefore, the decision boundary is already a good fit, and, given similar but shifted data, this loss will find low-density separation regions to improve predictive capabilities in the new data. In modelling terms, most of these works deal with pretrained deep neural networks and, during adaptation, only a few of their parameters are adapted while the rest remain frozen. In particular, within the image domain, these unfrozen parameters usually include batch normalization and layer normalization parameters, but last-layer methods are also popular, as they greatly simplify inference.

Although much of the TTA literature focuses on deterministic methods, such as [24, 31], some works on TTA exist within a probabilistic setting. For example, Zhou and Levine [36] characterize the data-generating process graphically and employ entropy minimization in the construction of a prior distribution. More recent works focus on a Bayesian filter for the noisy parameter updates resulting from using entropy minimization as a proxy loss [17, 18, 19]. Other relevant works involve using generative models to model cluster prototypes [28]. However, there is still a significant literature gap on general probabilistic modelling of TTA problems, as most works bypass the full specification of the modelling decisions without many arguments.

This work develops a probabilistic OTTA methodology for sequential data that provides uncertainty estimates on predictions, in a similar fashion to previous work on probabilistic online learning [6]. Our main contributions are the following. First, we propose a fully probabilistic setting for classification OTTA classification, in which uncertainty can be quantified at all steps of the pipeline. Second, we characterize each of the building blocks leveraging concepts from dynamic linear models [33] and Gibbs posteriors [3]. Finally, we approximate these posteriors using Gaussian distributions for real-time sequential Bayesian filtering and decision-support [7, 12]. We argue that this probabilistic approach serves as an umbrella for a vast collection of state-of-the-art TTA methods as special cases and design choices of structural elements of this framework, while also proposing novel competitive TTA techniques.

# 2 OTTA problem set up

Let  $\mathcal{D}_S = \{(x_n^S, y_n^S)\}_{n=1}^N$  denote the source dataset used to pretrain a model with parameter  $\boldsymbol{\theta}_S \in \Theta_S$ , and let  $\boldsymbol{\theta}_t \in \Theta_t$ , with  $t \in \mathbb{N}$ , denote the parameters that are adapted sequentially based on test data at time t. Both parameter sets,  $\Theta_S$  and  $\Theta_t$ , may coincide (e.g., the parameters of a logistic regression model), one may be a subset of the other (e.g., adapt the last layer of a pretrained neural network), or they might be independent from each other, each set representing different types of parameters (e.g., prototype based model that uses source neural features). We do assume for simplicity that the parameter set at test-time  $\Theta_t$  is constant for all t. At test time, we observe an unlabeled sequence  $\{\mathcal{X}_t\}_{t\in\mathbb{N}}$  drawn from target

distributions that may differ from the source, while the corresponding label sequence {Yt}t∈<sup>N</sup> is never observed.

The objective in OTTA is to predict y<sup>T</sup> ∈ Y<sup>T</sup> at any time T for each x<sup>T</sup> ∈ X<sup>T</sup> using information accumulated up to time τ (T), where τ (T) ∈ {1, ..., T} is a function specifying which test observations are used to adapt the parameters before predicting at time t. The predictive choice τ (T) = T − 1, in which the output at any time depends only on past inputs, is the standard in online learning but discards the distributional information that x<sup>T</sup> carries about the current state of θ<sup>T</sup> . Under covariate shift, x<sup>T</sup> carries information about the current parameter state θ<sup>T</sup> but is conditionally independent of y<sup>T</sup> given θ<sup>T</sup> in the measurement model, so introducing it into the filtering posterior before predicting may be justified as it adds information with no label leakage. This is the main argument behind filter choice τ (T) = T in TTA, where the output at any time depends on the current and past inputs. This is implicitly assumed in most of the methods in the literature and has connections with transductive learning [\[4\]](#page-15-7).

<span id="page-2-0"></span>![](_page_2_Picture_2.jpeg)

Figure 1: TTA probabilistic model. Grey nodes represent observed variables. White nodes, unobserved ones. Circled nodes are random variables, while squared nodes are deterministic for TTA. Rounded boxes imply that data may be coming in batches. Solid arcs represent true conditionals. Dashed arcs represent the Gibbs observation model.

Figure [1](#page-2-0) represents the graphical model defining our probabilistic OTTA framework. Proceeding temporally, the first nodes define a conditional distribution p(θS|DS), which is the pretrained model posterior on θ<sup>S</sup> after observing source labeled data DS. After that, adaptation parameters θ<sup>t</sup> are initialized at t = 0 based on their architectural relationship with θS. At any time t, we have a classifier with joint form p(X<sup>t</sup> ,Y<sup>t</sup> |θt). As Y<sup>t</sup> is not available, our observation model will be p(X<sup>t</sup> |θt), which will be characterized either by a latent variable model or by a loss-based model. Importantly, even though Y<sup>t</sup> is not available at time t, we will be interested in prediction and thus a predictive model p(Y<sup>t</sup> |X<sup>t</sup> , θt) will also need to be specified. As a last step, as we are in a sequential setting, we will also need to characterize a transition for the parameters of the form p(θ<sup>t</sup> |θt−1). Table [1](#page-3-0) provides a summary of the necessary building blocks for this framework, which will be characterized in the following section. Observe that at time T, the joint parameter posterior will be factorized as

$$p(\boldsymbol{\theta}_S, \boldsymbol{\theta}_{0:T}|\mathcal{X}_{1:T}, \mathcal{D}_S) \propto p(\boldsymbol{\theta}_S|\mathcal{D}_S) \cdot p(\boldsymbol{\theta}_0|\boldsymbol{\theta}_S) \cdot \prod_{t=1}^T p(\boldsymbol{\theta}_t|\boldsymbol{\theta}_{t-1}) \cdot p(\mathcal{X}_t|\boldsymbol{\theta}_t)$$
(1)

We may also define the propagation, updating, and predicting schemes at each time step. Proceeding temporally, we propagate the prior uncertainty at t−1, denoted by p(θt−1|X1:t−1, DS), using the transition function p(θ<sup>t</sup> |θt−1) to obtain a prior distribution at time t

$$p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S) = \int p(\boldsymbol{\theta}_t | \boldsymbol{\theta}_{t-1}) \cdot p(\boldsymbol{\theta}_{t-1} | \mathcal{X}_{1:t-1}, \mathcal{D}_S) \ d\boldsymbol{\theta}_{t-1}$$
(2)

At this time step, we only observe X<sup>t</sup> (and not Yt). The updated posterior for θ<sup>t</sup> will then be

$$p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t}, \mathcal{D}_S) \propto p(\mathcal{X}_t | \boldsymbol{\theta}_t) \cdot p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S)$$
 (3)

We shall be interested in doing same-step prediction, as we have not observed any Y<sup>t</sup> ; therefore, we predict labels through

$$p(\mathcal{Y}_t|\mathcal{X}_{1:t}, \mathcal{D}_S) = \int p(\mathcal{Y}_t|\mathcal{X}_t, \boldsymbol{\theta}_t) \cdot p(\boldsymbol{\theta}_t|\mathcal{X}_{1:t}, \mathcal{D}_S) d\boldsymbol{\theta}_t$$
 (4)

Note that doing prediction in this way is not strictly double-counting the data, as the observation model does not depend on Y<sup>t</sup> , which is unobserved. This approach has the taste of transductive learning [\[4\]](#page-15-7), as the posterior of θ<sup>t</sup> is conditioned on X<sup>t</sup> , and then used to predict Yt , implying that the goal might not necessarily be to find a general mapping between any X and Y , but a specific mapping between X<sup>t</sup> and Y<sup>t</sup> . However, as we repeat this procedure in an online fashion for different X<sup>t</sup> , we assume that the posterior of θ<sup>t</sup> accumulates information about all the previous steps and therefore may generalize well over all X. As we will see, this is not guaranteed and can lead to instabilities or catastrophic forgetting issues, so we will need to find ways to control for this.

<span id="page-3-0"></span>

| Building block          | Description                         |  |  |
|-------------------------|-------------------------------------|--|--|
| p(θS DS)                | Source posterior                    |  |  |
| p(θ0 θS)                | Adaptation parameter initialization |  |  |
| p(Yt<br> Xt<br>,<br>θt) | Predictive model                    |  |  |
| p(Xt<br> θt)            | Observation model                   |  |  |
| p(θt<br> θt−1)          | Parameter transition                |  |  |

Table 1: Building blocks for OTTA characterization

## 3 Model characterization

As Table [1,](#page-3-0) the model gets fully characterized by choosing how the design of the source posterior, the adaptation parameter initialization, the predictive model, the observation model, and the parameter transition.

## <span id="page-3-1"></span>3.1 Source posterior p(θS|DS)

In the standard TTA literature, fundamentally based on point-wise optimization methods, the source posterior is approximated via a single optimal parameter <sup>θ</sup>b, which translates to using a point-mass distribution

$$p(\boldsymbol{\theta}_S | \mathcal{D}_S) = \delta(\boldsymbol{\theta}_S - \boldsymbol{\theta}_S^*). \tag{5}$$

This is straightforward as θ ∗ S corresponds to the optimal parameter after training a pointestimate model, and is computationally free beyond training, as it does not require any additional computation to estimate uncertainty. Many of the state-of-the-art works on image classification via neural networks (NNs) [\[18,](#page-16-8) [24,](#page-16-5) [27,](#page-16-6) [31\]](#page-17-1) make this assumption.

However, a better approximation of the source posterior could be used, even for complex intractable distributions, as when using NNs. A principled tractable choice for approximating the source posterior, valid even for deterministic models, is the Laplace approximation [23]. Here, the source posterior is approximated by a Gaussian

<span id="page-4-0"></span>
$$p(\boldsymbol{\theta}_S | \mathcal{D}_S) \approx \mathcal{N}(\boldsymbol{\theta}_S^*, \Lambda_S^{-1})$$
 (6)

where  $\theta_S^*$  is the maximum a posteriori (MAP) solution and  $\Lambda_S^{-1}$  is the Hessian of the negative log posterior evaluated at the MAP, which may be approximated to ensure its positive definiteness [5]. This source posterior approximation is relatively standard in the continual learning literature. It connects directly with Elastic Weight Consolidation [13], a technique to avoid catastrophic forgetting in continual problems with NNs, essentially regularizing learning through the source posterior.

If the pretrained model is a probabilistic model itself, then we would already have an approximation of the actual source posterior that we could use for adaptation, and we would not require post-hoc methods such as the Laplace approximation. This is the case, for example, of Bayesian logistic regression, Bayesian kernel methods, or Bayesian NNs.

### 3.2 OTTA parameter initialization $p(\theta_0|\theta_S)$

Given a choice of source posterior, the initialization  $p(\theta_0|\theta_S)$  specifies the distribution over adaptable parameters before any test observation arrives. Its specification first requires establishing the structural relationship between  $\theta_S$  and  $\theta_t$ , for which two main scenarios arise.

When  $\Theta_t \subseteq \Theta_S$ , the adaptable parameters are a subset of the source ones. The extreme case where  $\Theta_t = \Theta_S$  adapts the entire model, thus maximising adaptation flexibility. Restricting to a strict subset  $\Theta_t \subset \Theta_S$  trades adaptation flexibility for computational tractability and is the approach followed by most TTA works, which may adapt only batch/layer normalization parameters [31] or last layer parameters [11, 28] of a neural network. The initialization is then the marginal of the source posterior of Section 3.1 over  $\Theta_t$ ,

$$p(\boldsymbol{\theta}_0 \mid \boldsymbol{\theta}_S) = \int p(\boldsymbol{\theta}_S \mid \mathcal{D}_S) d\boldsymbol{\theta}_{S \setminus \boldsymbol{\theta}_0}, \tag{7}$$

where  $\boldsymbol{\theta}_{S\backslash 0}$  denotes the non-adaptable source parameters. For a deterministic source, this marginal is a point mass at  $\boldsymbol{\theta}_{S|\boldsymbol{\theta}_0}^*$ , the components of the source MAP belonging to the adaptable subspace. For a Laplace or otherwise Gaussian source, it is the Gaussian block  $\mathcal{N}(\boldsymbol{\theta}_{S|\boldsymbol{\theta}_0}, \Lambda_{S|\boldsymbol{\theta}_0}^{-1})$ , with  $\boldsymbol{\theta}_{S|\boldsymbol{\theta}_0}$  and  $\Lambda_{S|\boldsymbol{\theta}_0}^{-1}$  the corresponding blocks of Equation (6), restricted to the adaptable subspace.

When  $\Theta_t \cap \Theta_S = \emptyset$ , the adaptable parameters are introduced at test time with no source counterpart. This is the case for last-layer methods based on mixture models [28], where parameters model class-prototype dynamics, and for low-rank adaptation (LoRA) techniques [10, 16], where auxiliary parameters are added to frozen source parameters via low-rank coupling. With no source posterior to marginalise,  $p(\theta_0 \mid \theta_S)$  must be specified independently—typically as a point mass at a chosen initial value (e.g., zero for LoRA adapters) or a broad Gaussian prior.

### 3.3 Predictive model $p(y_t|x_t, \boldsymbol{\theta}_t)$

The predictive model  $p(y_t|x_t, \boldsymbol{\theta}_t)$  specifies how predictions are formed from the current parameter state. For classification with K classes, it adopts the general form

<span id="page-4-1"></span>
$$p(Y|\mathcal{X}_t, \boldsymbol{\theta}_t) = \text{Categorical}(\text{Softmax}(f(\mathcal{X}_t; \boldsymbol{\theta}_t))),$$
 (8)

<span id="page-5-0"></span>![](_page_5_Figure_0.jpeg)

Figure 2: Structural relationships between source parameters θ<sup>S</sup> and adaptable parameters θt . Top: two cases distinguished by the set-theoretic relation between Θ<sup>S</sup> and Θ<sup>t</sup> , with the corresponding initialisation p(θ<sup>0</sup> | θS) shown beneath each. Bottom: sub-cases distinguished by which component of the predictive model carries θ<sup>t</sup> . In (b), disjointness refers to parameter structure, that is, the auxiliary parameters are not in θS. However, they are not functional independent, as the dashed coupling arrows indicate.

where f : X × Θ<sup>t</sup> → R <sup>K</sup> is a differentiable scoring function whose dependence on θ<sup>t</sup> is determined by which parameters are adapted at test time. The simplest case is when f is linear in θ<sup>t</sup> . That is the case, for example, of Bayesian logistic regression or methods that adapt only a linear classification head on top of a frozen feature extractor [\[28\]](#page-16-10). More commonly in modern TTA, f is nonlinear in θ<sup>t</sup> . Examples of this include adapting internal parameters of a neural feature map, such as normalization statistics [\[31,](#page-17-1) [35\]](#page-17-2), and injecting auxiliary parameters into a frozen feature map via low-rank coupling [\[16\]](#page-16-12). Figure [2](#page-5-0) summarizes the predictive model possibilities together with the adaptation parameter initialization.

#### 3.4 Observation model p(X<sup>t</sup> |θt)

As mentioned earlier, due to the absence of labels, most of the works on TTA focus on optimizing the model's parameters based on a loss function of choice, generally relying on entropy minimization and its variants [\[9,](#page-15-2) [24,](#page-16-5) [36\]](#page-17-3). Modelling the observation model using a loss-based component as a pseudo-likelihood is well justified in the Gibbs posterior literature [\[3,](#page-15-4) [14\]](#page-15-12). We follow this approach and define the observation model as

$$p(\mathcal{X}_t|\boldsymbol{\theta}_t) = \exp\left(-\beta_t \ell(\mathcal{X}_t, \boldsymbol{\theta}_t)\right) \tag{9}$$

where β<sup>t</sup> > 0 is a temperature parameter that controls the trade-off between trusting the prior and fitting the new data. Note that this expression is, in general, not a joint generative model due to the absence of the label sequence {Yt}t∈N. It can be thought of as a scoring function that assigns a posterior weight to any parameter configuration given the observed test sequence. The standard supervised likelihood of the strictly Bayesian approach is replaced with an exponentiated loss while preserving the consistency of the update. This leaves the loss as a modelling choice that determines, in a decision theoretic approach, how each unlabeled test point x<sup>t</sup> ∈ X<sup>t</sup> provides information about θ<sup>t</sup> according to a specific measure of fit, as justified in the generalized Bayesian framework [\[3,](#page-15-4) [14\]](#page-15-12).

The choice of the loss function for the Gibbs posterior is a central modelling decision, as it determines what information each unlabeled test point x<sup>t</sup> provides about θ<sup>t</sup> . Different choices correspond to different structural assumptions in the feature space and different probabilistic interpretations. Table [2](#page-6-0) shows several types of losses that serve as a basis for most TTA works in the field. Note that for all of them, ℓ(X<sup>t</sup> ; θt) = <sup>1</sup> Nt P xt∈X<sup>t</sup> ℓ(x<sup>t</sup> ; θt)

<span id="page-6-0"></span>

| ℓ(xt; θt)                                                                        | Description                      |  |
|----------------------------------------------------------------------------------|----------------------------------|--|
| P<br>−<br>p(yt<br>= k xt, θt) · log p(yt<br>= k xt, θt)<br>k                     | Entropy minimization [9, 31, 36] |  |
| = k xt, θt) · log<br><br>p(yt=k xt,θt)<br>−<br>P<br>p(yt<br>k<br>1−p(yt=k xt,θt) | Soft-likelihood ratio [18, 24]   |  |
| − log p(ˆyt xt, θt), ˆyt<br>= arg maxk<br>p(yt<br>= k xt, θt)                    | Pseudo-label [8]                 |  |
| ℓSS(xt; θt)                                                                      | Self-supervised [22, 30]         |  |

Table 2: Basic losses in TTA

In the case in which the loss is the negative log marginal likelihood, and β<sup>t</sup> = 1, we recover the proper Bayesian posterior with target y<sup>t</sup> . This, of course, would require the specification of a class-conditional generative model characterized by θ<sup>t</sup> , as in the prototype-based case [\[11,](#page-15-10) [28\]](#page-16-10). In other cases, the loss will be a surrogate that does not correspond with a proper likelihood, with β controlling for the strength of the data term relative to the prior. Entropy minimization and soft-likelihood ratio are based on the low-density separation assumption, the latter being more robust as it maintains non-vanishing gradients for confident predictions, preventing the frequent convergence collapse in entropy minimization. The pseudo-label loss uses predictions as true labels, while the self-supervised loss uses data augmentation techniques to enforce robustness, e.g, image transformations or adversarial perturbations []. Note that losses can be classified based on whether they are self-referential or not, that is, whether they use the model's current output p(y<sup>t</sup> |x<sup>t</sup> , θt) or not. These kinds of losses may lead to instabilities or collapse due to the moving-target problem, in which as θ<sup>t</sup> evolves, so does the loss landscape.

Choice of β<sup>t</sup> As mentioned earlier, β<sup>t</sup> calibrates how much data information is meant to update the prior. A straightforward choice for this parameter is to set it to a constant scalar, that is, β<sup>t</sup> = β, which can be selected as a hyperparameter of the model. However, this assumes that all samples carry equal information about θ<sup>t</sup> , which is rarely the case in TTA.

A more adaptive choice is to modulate βt,i, a weight parameter per sample i in the batch at time t, based on the model's current predictive confidence. Under reliability weighting, we define the complement of the normalised predictive entropy wt,i = 1−H p(y i t |x i t , θt) / log C ∈ [0, 1], with C the number of classes, and set βt,i = β · wt,i. The motivation is that samples on which the model is already uncertain yield noisier pseudo-targets, and should arguably contribute less precision to the update. With this scheme, β acts as a ceiling on the persample observation precision, and the total information injected in a step decreases naturally when the batch is collectively uncertain.

#### 3.5 Transition model p(θ<sup>t</sup> |θt−1)

Once we have characterized the measurement function and the learning procedure, we will carry on to characterize the parameter transition model, which is the last element needed for computing the parameter prior and posterior at each time step t.

The transition function may be written as a Gaussian over the parameters of the previous step posterior, having the expression

$$\boldsymbol{\theta}_t = \mathbf{G}_t \boldsymbol{\theta}_{t-1} + \mathbf{c}_t + w_t \qquad w_t \sim \mathcal{N}(0, \mathbf{W}_t)$$
 (10)

for some state matrix G<sup>t</sup> , vector c<sup>t</sup> , and covariance matrix W<sup>t</sup> . This construction of the transition function is standard in the dynamic linear model (DLM) literature [\[33\]](#page-17-4), in which G<sup>t</sup> encodes structural assumptions about the deterministic component of parameter dynamics. When the feature space has a direct physical interpretation, the addition of structural components through G<sup>t</sup> is very meaningful. For example, a local linear trend model can encode acceleration drift, or a seasonal component can encode periodicity or oscillatory dynamics. If θ<sup>t</sup> parametrizes quantities with a direct relationship to the data-generating process, then these interpretations are fully justified.

Example 1. Figure [3](#page-7-0) shows the effect on 1D linear regression that different structural components of G have on the parameter prior. We plot the parameter dynamics only — no data are observed — and fix an initial intercept θ<sup>0</sup> = 0 and an initial slope θ<sup>1</sup> = 1 2 . The random walk causes the intercept to drift unboundedly due to accumulated noise. The polynomial trend does likewise, but with momentum from the hidden velocity state. The seasonal component oscillates periodically around the initial value. The Ornstein Uhlenbeck process confines both parameters to a stationary distribution centered at their initial values, with the degree of confinement controlled by ρ.

<span id="page-7-0"></span>![](_page_7_Figure_4.jpeg)

Figure 3: Prior parameter dynamics induced by four choices of transition matrix G. Top row: sample paths and prior mean in (θ0, θ1) parameter space, coloured by time. Middle row: marginal time series of each parameter. Bottom row: induced prior over regression lines η = θ1x<sup>1</sup> + θ0.

When  $\theta_t$  are general discriminative parameters in a complex representation space without direct physical intuition, a structured  $\mathbf{G}_t$  would be difficult to justify. The random walk  $\mathbf{G}_t = I$  does not assume the direction of drift and is the default when the nature of the distribution shift is unknown. Source mean reversion, where  $\mathbf{G}_t = \rho I$  and  $\mathbf{c}_t = (1 - \rho)\boldsymbol{\mu}_0$  with  $\rho \in [0, 1]$ , encodes the belief that adaptation should decay without sustained evidence towards the source mean  $\boldsymbol{\mu}_0$ , preventing unbounded drift from the source parameter distribution.

The matrix  $\mathbf{W}_t$  controls the speed and geometry of the stochastic parameter drift and is the more consequential design choice, with three main structural options. The first one is discounting [33], in which  $\mathbf{W}_t = \frac{\delta - 1}{\delta} \mathbf{\Sigma}_{t-1}$ , with  $\delta \in (0,1]$  is a hyperparameter and where  $\mathbf{\Sigma}_{t-1}$  is the covariance matrix of the previous-step posterior. Notice that this choice reduces computations of a new matrix while inflating the accumulated posterior by  $1/\delta$  before seeing the data, becoming less confident before the next temporal step. Another option is the full specification of a matrix  $\mathbf{W}_t$ , the simplest example being isotropic noise  $\mathbf{W}_t = \sigma^2 I$ , which corresponds to uniform adaptation across all parameter directions, and is equivalent to the implicit process noise of a fixed learning rate in point-wise optimization methods. Finally, we could also consider dropping the covariance  $\mathbf{\Sigma}_{t-1}$  completely, that is  $\mathbf{W}_t = \mathbf{\widehat{W}}_t - \mathbf{\Sigma}_{t-1}$ , and letting  $\mathbf{\widehat{W}}_t = \sigma^2 I$  be the only curvature component. This option discards any previous curvature information and may deal better with large covariate shifts. The scale  $\sigma^2$  is not directly identifiable from unlabeled test data alone and, thus, is left as a hyperparameter.

### 4 Inference

After building and exemplifying the necessary blocks, we focus on inference methods that estimate the posterior density of the parameters. We introduce two methods that assume Gaussian posteriors: linear-Gaussian approximations via linearization, and variational inference.

For full inference, we require computing the current-step prior distribution, which involves the previous-step posterior  $p(\boldsymbol{\theta}_{t-1}|\mathcal{X}_{1:t-1}, \mathcal{D}_S)$  and the transition function  $p(\boldsymbol{\theta}_t|\boldsymbol{\theta}_{t-1})$ ,

$$p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S) = \int p(\boldsymbol{\theta}_t | \boldsymbol{\theta}_{t-1}) \times p(\boldsymbol{\theta}_{t-1} | \mathcal{X}_{1:t-1}, \mathcal{D}_S) \ d\boldsymbol{\theta}_{t-1}$$
(11)

To simplify inference and retain conjugacy, we may approximate the previous-step posterior by a Gaussian  $p(\boldsymbol{\theta}_{t-1}|\mathcal{X}_{1:t-1}, \mathcal{D}_S) \approx \mathcal{N}(\boldsymbol{\mu}_{t-1}, \boldsymbol{\Sigma}_{t-1})$ . Then, as the transition function has been defined also as a Gaussian  $p(\boldsymbol{\theta}_t|\boldsymbol{\theta}_{t-1}) = \mathcal{N}(\mathbf{G}_t\boldsymbol{\theta}_{t-1} + \mathbf{c}_t, \mathbf{W}_t)$ , the current-step prior will have the expression

<span id="page-8-0"></span>
$$p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S) = \mathcal{N}(\boldsymbol{\mu}_{t|t-1}, \boldsymbol{\Sigma}_{t|t-1}), \tag{12}$$

where  $\mu_{t|t-1} = \mathbf{G}_t \mu_{t-1} + c_t$  and  $\Sigma_{t|t-1} = \Sigma_{t-1} + \mathbf{W}_t$ . Thus, the current-step prior will also be Gaussian, and this property will be leveraged by the following inference methods.

### 4.1 Linear-Gaussian approximation via Taylor expansion of the loss

Given that 12 is Gaussian, the Gibbs posterior [3] at any time-step will have the expression

$$p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t}, \mathcal{D}_S) \propto p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S) \exp(-\beta_t \ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t))$$
 (13)

$$\propto \exp\left(-\frac{1}{2}(\boldsymbol{\theta}_t - \boldsymbol{\mu}_{t|t-1})^T \boldsymbol{\Sigma}_{t-1}^T (\boldsymbol{\theta}_t - \boldsymbol{\mu}_{t|t-1}) - \beta_t \ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t)\right). \tag{14}$$

To get closed-form posterior, we can complete the square in the exponent by approximating the loss functions via a second-order Taylor expansion around the prior mean, that is,

$$\ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t) \approx \ell_t(\mathcal{X}_t, \boldsymbol{\mu}_{t|t-1}) + g_t^T(\boldsymbol{\theta}_t - \boldsymbol{\mu}_{t|t-1}) + \frac{1}{2}(\boldsymbol{\theta}_t - \boldsymbol{\mu}_{t|t-1})^T \mathbf{H}_t(\boldsymbol{\theta}_t - \boldsymbol{\mu}_{t|t-1})$$
(15)

where  $g_t = \nabla \ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t)|_{\boldsymbol{\theta}_t = \boldsymbol{\mu}_{t|t-1}}$  and  $H_t = \nabla^2 \ell_t^T(\mathcal{X}_t, \boldsymbol{\theta}_t)|_{\boldsymbol{\theta}_t = \boldsymbol{\mu}_{t|t-1}}$ . This results in a Gaussian with parameters

<span id="page-9-0"></span>
$$\begin{cases} \boldsymbol{\mu}_t &= \boldsymbol{\mu}_{t|t-1} - \beta_t \boldsymbol{\Sigma}_t g_t \\ \boldsymbol{\Sigma}_t^{-1} &= \boldsymbol{\Sigma}_{t|t-1}^{-1} + \beta_t \mathbf{H}_t \end{cases}$$
(16)

Notice that this approach is equivalent to adopting a Newton-Raphson optimization step. The precision matrix accumulates the local curvature of the loss, and the mean moves based on the local gradient pre-conditioned by that curvature.

One limitation of this approximation is that it evaluates the gradient and the Hessian only at a single point, the mean  $\mu_{t|t-1}$ , which for highly non-convex parameter spaces may lead to overconfident updates.

### 4.2 Variational Bayes

The above issue leads to an alternative method for approximating the parameter posterior distribution through Variational Bayes (VB) [2], which transforms an estimation problem into an optimization problem. The idea is to approximate the posterior using a candidate parametric distribution (usually a Gaussian), chosen by minimizing the Kullback-Leibler divergence between the candidate distribution and the true posterior. The problem involves finding  $q(\theta_t^*) \sim (\mu_t^*, \Sigma_t^*)$  such that

$$(\boldsymbol{\mu}_t^*, \boldsymbol{\Sigma}_t^*) = \arg\min_{\boldsymbol{\mu}_t, \boldsymbol{\Sigma}_t} D_{KL} \left( \mathcal{N}(\boldsymbol{\mu}_t, \boldsymbol{\Sigma}_t) || \exp(-\beta_t \ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t)) p(\boldsymbol{\theta}_t | \mathcal{X}_{1:t-1}, \mathcal{D}_S) \right)$$
(17)

Note that the normalization constant of the posterior may be ignored, a huge computational benefit of VB. Further, VB does not require linearization by construction.

However, VB also has some drawbacks, as it requires an iterative optimization loop to converge to a solution and does not benefit from the sequentiality of the problem, necessitating the execution of a different optimization loop at each time step.

#### 4.3 Bayesian online natural gradient

We leverage the work by Jones et al. [12], which solves the VB computation issue by using one-step Natural Gradient Descent on the variational parameters for sequential variational Bayes, proving that it yields exact Bayesian inference when models are conjugate and serves as a relaxation of the Bayesian update for the non-conjugate variational case. The method, which assumes the variational family is Gaussian, leads to the following update:

<span id="page-9-1"></span>
$$\begin{cases} \boldsymbol{\mu}_{t} &= \boldsymbol{\mu}_{t|t-1} - \beta_{t} \boldsymbol{\Sigma}_{t} \mathbb{E}_{q(\boldsymbol{\theta}_{t})} [\nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t})] \\ \boldsymbol{\Sigma}_{t}^{-1} &= \boldsymbol{\Sigma}_{t|t-1}^{-1} + \beta_{t} \mathbb{E}_{q(\boldsymbol{\theta}_{t})} [\nabla_{\boldsymbol{\theta}_{t}}^{2} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t})] \end{cases}$$
(18)

Notice how the update equations (16) and (18) look nearly identical. The difference is that Equation (18) evaluates an expected gradient and Hessian loss instead of point-estimates, thus leading to flatter and more robust minima compared to the linearization method. The integrals defined through these expectations are generally intractable, so they shall require an approximation. One option is using a Monte Carlo (MC) approximation, taking several

independent samples from q(θt) and estimating the expectation as the empirical mean of the inside terms evaluated at the selected samples. Another option is linearizing the loss over the previous step mean. This will exactly lead to Equation [\(16\)](#page-9-0), thus showing the connection between the two approaches.

As said, we will use a Gaussian variational family to approximate the posterior distribution. However, different assumptions can be made regarding the covariance matrix Σ<sup>t</sup> . We will show examples of mean-field, diagonal-plus-low-rank, and full VI in the experiments section.

### 4.4 Approximating the Hessian

Both inference approaches require calculating the Hessian H<sup>t</sup> , which, to avoid numerical issues, is generally approximated using the positive-semidefinite Fisher Information Matrix (FIM) [\[25\]](#page-16-14)

$$\mathbf{H}_{t} \approx \mathbb{E}[\nabla_{\boldsymbol{\theta}_{t}} \log p(\mathcal{X}_{t}|\boldsymbol{\theta}_{t}) \cdot \nabla_{\boldsymbol{\theta}_{t}} \log p(\mathcal{X}_{t}|\boldsymbol{\theta}_{t})^{T}]$$
(19)

$$= \lambda^{2} \mathbb{E}[(\nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t}) - \mathbb{E}[\nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t})) \cdot (\nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t}) - \mathbb{E}[\nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}, \boldsymbol{\theta}_{t}))^{T}]$$
(20)

$$= \lambda^2 \operatorname{Var}[\nabla_{\boldsymbol{\theta}_t} \ell_t(\mathcal{X}_t, \boldsymbol{\theta}_t)], \tag{21}$$

where expectations are calculated with respect to p(X<sup>t</sup> |θt). Since we cannot sample from this distribution directly, we may approximate the expectation via the empirical distribution, resulting in the empirical FIM

$$\hat{\mathbf{H}}_{t} = \frac{\lambda^{2}}{N_{t}} \sum_{i=1}^{N_{t}} \left( \nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}^{i}, \boldsymbol{\theta}_{t}) - \overline{\mathbf{g}}_{t} \right) \cdot \left( \nabla_{\boldsymbol{\theta}_{t}} \ell_{t}(\mathcal{X}_{t}^{i}, \boldsymbol{\theta}_{t}) - \overline{\mathbf{g}}_{t} \right)^{T},$$
(22)

where g<sup>t</sup> = Nt PN<sup>t</sup> <sup>i</sup>=1 ∇θ<sup>t</sup> ℓt(X i t , θt)

Even calculating the FIM becomes computationally involved when the number of parameters is large, as it is a matrix of size d × d, where d is the number of parameters. However, modern computational methods to approximate and reduce this burden exist, based on factor approximations of this matrix, such as diagonal factorization, Kronecker-factored approximate curvature methods and low-rank factorizations [\[5\]](#page-15-8).

## 5 Prediction

At each test step t, predictions are obtained by marginalising the generative model over the adapted posterior

$$p(Y|\mathcal{X}_{1:t}, \mathcal{D}_S) = \int p(Y|\mathcal{X}_t, \boldsymbol{\theta}_t) \cdot p(\boldsymbol{\theta}_t|\mathcal{X}_{1:t}, \mathcal{D}_S) d\boldsymbol{\theta}_t,$$
 (23)

where p(θ<sup>t</sup> |X1:<sup>t</sup> , DS) = N (µ<sup>t</sup> , Σt) is the Gaussian posterior over adaptation parameters after incorporating all past unlabelled test data and the source prior. This integral is intractable in general and needs to be approximated. Three main approximation methods exist:

- The MAP approximation substitutes the posterior mean for the full distribution, p(Y |X<sup>t</sup> , DS) ≈ p(Y |X<sup>t</sup> , µ<sup>t</sup> ), discarding all posterior uncertainty.
- The Monte Carlo approximation draws S samples θ (s) <sup>t</sup> ∼ N (µ<sup>t</sup> , Σt) and estimates the predictive as p(Y |X<sup>t</sup> , DS) ≈ 1 S P s p(Y | X<sup>t</sup> , θ (s) t ), an unbiased estimator that converges as S → ∞.

• The linearised approximation yields a deterministic, closed-form predictive that propagates the full posterior covariance at the cost of a single Jacobian-vector product per class. This is cheaper than Monte Carlo and, unlike the MAP estimate, is sensitive to posterior uncertainty. Let  $f(\mathcal{X}_t; \boldsymbol{\theta}_t)$  denote the logit function of Equation (8). A first-order Taylor expansion of f around the posterior mean  $\boldsymbol{\mu}_t$  gives

$$f(\mathcal{X}_t; \boldsymbol{\theta}_t) \approx f(\mathcal{X}_t; \boldsymbol{\mu}_t) + \mathbf{J}(\mathcal{X}_t)(\boldsymbol{\theta}_t - \boldsymbol{\mu}_t),$$
 (24)

where  $\mathbf{J}(\mathcal{X}_t) = \partial f/\partial \boldsymbol{\theta}_t|_{\boldsymbol{\theta}_t = \boldsymbol{\mu}_t}$  is the Jacobian of the logits with respect to the adaptation parameters. We write  $\mathbf{J}_c(\mathcal{X}_t) \in \mathbb{R}^{|\boldsymbol{\theta}_t|}$  for the (column) gradient of the c-th logit. Since  $\boldsymbol{\theta}_t \sim \mathcal{N}(\boldsymbol{\mu}_t, \boldsymbol{\Sigma}_t)$ , the linearisation induces a Gaussian distribution over  $f(\mathcal{X}_t; \boldsymbol{\theta}_t)$  with per-class predictive variance

$$\sigma_c^2 = \mathbf{J}_c(\mathcal{X}_t)^{\top} \mathbf{\Sigma}_t \mathbf{J}_c(\mathcal{X}_t). \tag{25}$$

The expected softmax under a Gaussian over logits has no closed form, so we apply the probit approximation [2] per class and renormalise, giving

$$p(Y|\mathcal{X}_{1:t}, \mathcal{D}_S) \approx \text{Categorical}\left(\text{Softmax}\left(\boldsymbol{\kappa} \odot f(\mathcal{X}_t; \boldsymbol{\mu}_t)\right)\right),$$
 (26)

where  $\kappa_c = \left(1 + \frac{\pi}{8}\sigma_c^2\right)^{-1/2} \in (0, 1].$ 

### 6 Experiments

#### 6.1 Linear model

**Example 2** (2D logistic regression with covariate shift under TTA). Consider a continuous stream of 2D data belonging to two classes and subject to a diagonal covariate shift. The drift is continuous, but its exact direction is unknown a priori. Hence, we decouple our parameter dynamics using a Dynamic Generalized Linear Model (DGLM) architecture.

For this, we define our state vector as  $\boldsymbol{\theta}_t = [\boldsymbol{\theta}_{t,poly}, \boldsymbol{\theta}_{t,reg}^T]^T \in \mathbb{R}^3$ , where  $\boldsymbol{\theta}_{t,poly} \in \mathbb{R}$  represents the model bias, and  $\boldsymbol{\theta}_{t,reg} \in \mathbb{R}^2$  represents the spatial regression weights. To encourage spatial stability while allowing the boundary to shift dynamically, we model the bias as a random walk (a zero-order polynomial trend) and the spatial weights as an Ornstein-Uhlenbeck (OU) process.

Using the prior precision (inverse of covariance) of the spatial weights  $\Lambda_{\theta_{t,reg}} = \Sigma_{0,\theta_{t,reg}}^{-1}$  and a mean-reversion rate  $\eta = 0.001$ , we assemble a time-constant block-diagonal state transition matrix G and affine drift vector c

$$\mathbf{G}_{t} = \begin{pmatrix} 1 & \mathbf{0}^{T} \\ \mathbf{0} & I_{2} - \eta \Lambda_{\boldsymbol{\theta}_{0, reg}} \end{pmatrix}, \qquad c = \begin{pmatrix} 0 \\ \eta \Lambda_{\boldsymbol{\theta}_{0, reg}} \boldsymbol{\mu}_{\boldsymbol{\theta}_{0, reg}} \end{pmatrix}$$
(27)

Following a standard supervised initialization to establish our prior  $\mathcal{N}(\boldsymbol{\mu}_0, \boldsymbol{\Sigma}_0)$ , we enter into the unsupervised Test-Time Adaptation (TTA) regime. At each time step t, we first project our beliefs forward. The mean transitions according to the affine DGLM dynamics, whereas the covariance expands by the block-diagonal system noise matrix W:

$$p(\boldsymbol{\theta}_t|\mathbf{x}_{0:t-1}) = \mathcal{N}(\boldsymbol{\mu}_{t|t-1}, \boldsymbol{\Sigma}_{t|t-1}) \qquad \begin{cases} \boldsymbol{\mu}_{t|t-1} &= \mathbf{G}_t \boldsymbol{\mu}_{t-1} + c \\ \boldsymbol{\Sigma}_{t|t-1} &= G \boldsymbol{\Sigma}_{t-1} G^T + \mathbf{W_t} \end{cases}$$
(28)

Upon receiving an unlabeled data point x<sup>t</sup> ∈ R 2 , we construct the design vector F<sup>t</sup> = [1, x T t T . We rely on entropy minimization to force the decision boundary to track the data drift. The exact gradient of the entropy loss g<sup>t</sup> = ∇θ<sup>t</sup> ℓ(x<sup>t</sup> , θt)|θt=µt|t−<sup>1</sup> evaluates to:

$$g_t = -\eta_t \big( \pi_t (1 - \pi_t) \big) \mathbf{F}_t, \tag{29}$$

where η<sup>t</sup> = F T <sup>t</sup> µt|t−<sup>1</sup> is the predicted logit and π<sup>t</sup> = σ(ηt) its corresponding probability.

By exponentiating this loss and performing a second-order Taylor expansion around the prior mean, we compute the Hessian H<sup>t</sup> (or its outer-product approximation). We update our Gaussian approximation using the standard Extended Kalman Filter (EKF) equations in information form:

$$p(\boldsymbol{\theta}_t|\mathbf{x}_{0:t}) \approx \mathcal{N}(\boldsymbol{\mu}_t, \boldsymbol{\Sigma}_t)$$
 
$$\begin{cases} \boldsymbol{\Sigma}_t^{-1} &= \boldsymbol{\Sigma}_{t|t-1}^{-1} + \mathbf{H}_t \\ \boldsymbol{\mu}_t &= \boldsymbol{\mu}_{t|t-1} - \boldsymbol{\Sigma}_t g_t \end{cases}$$
 (30)

We can observe how adaptation maintains predictive performance and detects the data sep-

![](_page_12_Figure_6.jpeg)

Figure 4: Classification boundary evolution

aration region correctly. As time evolves, the predictor becomes more certain of the data distribution and uncertainty shrinks.

△

### 6.2 Non-linear models

Example 3 (Two-moons shift dataset). Consider a stream of 2D two-moon data, in which more data accumulates at opposite ends of each moon. Using a simple 4th-degree polynomial feature transformation and using logistic regression on the transformed features, we get via BONG inference the resulting predictive distributions shown in Figure [5.](#page-13-0) It is easy to see how the unlabeled data moves the decision boundary, maintaining a predictive posterior with good predictive performance. Uncertainty seems to shrink as time evolves, but it stays high in regions far from the observed data. △

Example 4 (Three-class pinwheel shift dataset). Now consider a stream of 2D data with the shape of a pinwheel in which each of the blades belongs to a class. Using a 7th-degree polynomial feature transformation, and fitting the model using a Brier loss on Gaussian feature augmentations, we get via BONG inference the resulting predictive distributions shown in Figure [5.](#page-13-0) We can see how the unlabeled data moves the decision boundaries, while all predictions also become more certain as time evolves. △

## 6.3 Neural network TTA

### 6.3.1 Batch-norm adaptation

Example 5 (Online preconditioned gradient descent). As a particular case of our framework, we can define an online preconditioned gradient descent algorithm that leverages the

<span id="page-13-0"></span>![](_page_13_Figure_0.jpeg)

Figure 5: Classification boundary evolution

![](_page_13_Figure_2.jpeg)

Figure 6: Classification boundary evolution

loss curvature information of the current step and discards the curvatures of previous steps. We define the parameters, following the previously used notation, as  $\mu_t = \mu_{t|t-1} - \beta_t \Sigma_t g_t$  and  $\Sigma_t^{-1} = W_r^{-1} + \beta_t H_t$ . The covariance matrix does not use previous step information but uses noise-inflated curvature information of the current step. This approach may be seen as a curvature-informative point-based method for optimizing the parameters of the adapted model based on a degenerate distribution with point-mass at  $\mu_t$ .

Table 3 shows the results of applying the online preconditioned gradient descent, with information maximization as loss function and a constant  $\beta_t = 2$ , to the batch normalization parameters of a ResNet28-C pretrained on CIFAR10. The network is adapted independently to 15 different image corruptions as in the CIFAR10-C dataset, and Table 3 shows the average accuracy over the 15 corruptions. Additionally, it compares with other state-of-the-art methods solving the same problem.

| TTA Method   | Source | BN test | TENT | EATA | Ours |
|--------------|--------|---------|------|------|------|
| Avg Accuracy | 0.56   | 0.79    | 0.80 | 0.80 | 0.82 |

<span id="page-13-1"></span>Table 3: CIFAR10-C: Average accuracy comparison with SOTA methods on corrupted CI-FAR10 with 15 different corruptions, adapting batch normalization parameters of a ResNet-28.

 $\triangle$ 

## 7 Comparison with other TTA methods

Most existing TTA methods can be recovered as special cases of the MAP limit of the proposed framework, with specific instantiations of the remaining components. TENT [31] corresponds to an entropy loss with constant  $\beta$  and no source anchor; SHOT [20] to an information-maximization objective; and pseudo-label methods [8] to cross-entropy against hard argmax targets. Several methods additionally incorporate source regularization: EATA's [27] Fisher

penalty and CoTTA's [\[32\]](#page-17-5) stochastic parameter restore both serve to prevent unbounded drift from the source, playing an analogous role to the OU mean-reversion transition in our approach. In the MAP limit with a discount covariance propagation (Σt|t−<sup>1</sup> = Σt−1/δ), the framework further reduces to an exponential moving average over past gradient information, connecting to EMA-based adaptation schemes. In all these mentioned cases, however, the posterior covariance is discarded after each update, and no uncertainty is propagated across steps. The general probabilistic framework we propose extends beyond this family by maintaining a full posterior over θ<sup>t</sup> across steps and encoding non-stationary parameter dynamics via the DGLM transition, neither of which is representable within gradient-based TTA methods.

## 8 Conclusion

This work presents a probabilistic model for test-time adaptation, whose characterization is modular and structured in clear building blocks. We separate the possible design choices based on data geometry assumptions from the distributional approximations needed to accelerate inference. We motivate the necessity for probabilistic approaches to test-time adaptation by showing that these can leverage model averaging and uncertainty estimation naturally, two elements that are crucial for better performance in test-time data-shifted scenarios. Increased predictive performance is shown in the linear and nonlinear simple scenarios, as well as for the adaptation of a pretrained neural network for corrupted image classification.

## References

- <span id="page-15-1"></span>[1] P. G. Arce, R. Naveiro, and D. R. Insua. Evasion attacks against bayesian predictive models. In Proceedings of the Forty-First Conference on Uncertainty in Artificial Intelligence, pages 184–202, 2025.
- <span id="page-15-0"></span>[2] C. M. Bishop and N. M. Nasrabadi. Pattern recognition and machine learning, volume 4. Springer, 2006.
- <span id="page-15-4"></span>[3] P. G. Bissiri, C. C. Holmes, and S. G. Walker. A general framework for updating belief distributions. Journal of the Royal Statistical Society Series B: Statistical Methodology, 78(5):1103–1130, 2016.
- <span id="page-15-7"></span>[4] O. Chapelle, B. Sch¨olkopf, and A. Zien, editors. Semi-supervised learning. Adaptive computation and machine learning. MIT Press, Cambridge, Mass, 2006. ISBN 9780262033589.
- <span id="page-15-8"></span>[5] E. Daxberger, A. Kristiadi, A. Immer, R. Eschenhagen, M. Bauer, and P. Hennig. Laplace redux-effortless bayesian deep learning. Advances in neural information processing systems, 34:20089–20103, 2021.
- <span id="page-15-3"></span>[6] G. Duran-Martin, L. S´anchez-Betancourt, A. Y. Shestopaloff, and K. Murphy. A unifying framework for generalised bayesian online learning in non-stationary environments. arXiv preprint arXiv:2411.10153, 2024.
- <span id="page-15-5"></span>[7] G. Duran-Martin, L. S´anchez-Betancourt, A. Cartea, and K. Murphy. Martingale poste- ´ rior neural networks for fast sequential decision making. Advances in Neural Information Processing Systems, 38:87940–87988, 2026.
- <span id="page-15-13"></span>[8] S. Goyal, M. Sun, A. Raghunathan, and J. Z. Kolter. Test time adaptation via conjugate pseudo-labels. Advances in Neural Information Processing Systems, 35:6204–6218, 2022.
- <span id="page-15-2"></span>[9] Y. Grandvalet and Y. Bengio. Semi-supervised learning by entropy minimization. Advances in neural information processing systems, 17, 2004.
- <span id="page-15-11"></span>[10] E. J. Hu, Y. Shen, P. Wallis, Z. Allen-Zhu, Y. Li, S. Wang, L. Wang, W. Chen, et al. Lora: Low-rank adaptation of large language models. Iclr, 1(2):3, 2022.
- <span id="page-15-10"></span>[11] Y. Iwasawa and Y. Matsuo. Test-time classifier adjustment module for model-agnostic domain generalization. Advances in Neural Information Processing Systems, 34:2427– 2440, 2021.
- <span id="page-15-6"></span>[12] M. Jones, P. Chang, and K. Murphy. Bayesian online natural gradient (bong). Advances in Neural Information Processing Systems, 37:131104–131153, 2024.
- <span id="page-15-9"></span>[13] J. Kirkpatrick, R. Pascanu, N. Rabinowitz, J. Veness, G. Desjardins, A. A. Rusu, K. Milan, J. Quan, T. Ramalho, A. Grabska-Barwinska, et al. Overcoming catastrophic forgetting in neural networks. Proceedings of the national academy of sciences, 114(13): 3521–3526, 2017.
- <span id="page-15-12"></span>[14] J. Knoblauch, J. Jewson, and T. Damoulas. An optimization-centric view on bayes' rule: Reviewing and generalizing variational inference. Journal of Machine Learning Research, 23(132):1–109, 2022.

- <span id="page-16-1"></span>[15] P. W. Koh, S. Sagawa, H. Marklund, S. M. Xie, M. Zhang, A. Balsubramani, W. Hu, M. Yasunaga, R. L. Phillips, I. Gao, et al. Wilds: A benchmark of in-the-wild distribution shifts. In International conference on machine learning, pages 5637–5664. PMLR, 2021.
- <span id="page-16-12"></span>[16] Y. Kojima, J. Xu, X. Zou, and X. Wang. Lora-ttt: Low-rank test-time training for vision-language models. arXiv preprint arXiv:2502.02069, 2025.
- <span id="page-16-7"></span>[17] J.-H. Lee. Bayesian weight enhancement with steady-state adaptation for test-time adaptation in dynamic environments. In Forty-second International Conference on Machine Learning, 2025.
- <span id="page-16-8"></span>[18] J.-H. Lee and J.-H. Chang. Continual momentum filtering on parameter space for online test-time adaptation. In The Twelfth International Conference on Learning Representations, 2024.
- <span id="page-16-9"></span>[19] J.-H. Lee and J.-H. Chang. Stationary latent weight inference for unreliable observations from online test-time adaptation. In Forty-first International Conference on Machine Learning, 2024.
- <span id="page-16-15"></span>[20] J. Liang, D. Hu, and J. Feng. Do we really need to access the source data? source hypothesis transfer for unsupervised domain adaptation. In International conference on machine learning, pages 6028–6039. PMLR, 2020.
- <span id="page-16-4"></span>[21] J. Liang, R. He, and T. Tan. A comprehensive survey on test-time adaptation under distribution shifts. International Journal of Computer Vision, 133(1):31–64, 2025.
- <span id="page-16-13"></span>[22] Y. Liu, P. Kothari, B. Van Delft, B. Bellot-Gurlet, T. Mordan, and A. Alahi. Ttt++: When does self-supervised test-time training fail or thrive? Advances in Neural Information Processing Systems, 34:21808–21820, 2021.
- <span id="page-16-11"></span>[23] D. J. MacKay. A practical bayesian framework for backpropagation networks. Neural computation, 4(3):448–472, 1992.
- <span id="page-16-5"></span>[24] R. A. Marsden, M. D¨obler, and B. Yang. Universal test-time adaptation through weight ensembling, diversity weighting, and prior correction. In Proceedings of the IEEE/CVF Winter Conference on Applications of Computer Vision, pages 2555–2565, 2024.
- <span id="page-16-14"></span>[25] J. Martens. New insights and perspectives on the natural gradient method. Journal of Machine Learning Research, 21(146):1–76, 2020.
- <span id="page-16-0"></span>[26] K. P. Murphy. Probabilistic machine learning: Advanced topics. MIT press, 2023.
- <span id="page-16-6"></span>[27] S. Niu, J. Wu, Y. Zhang, Y. Chen, S. Zheng, P. Zhao, and M. Tan. Efficient test-time model adaptation without forgetting. In International conference on machine learning, pages 16888–16905. PMLR, 2022.
- <span id="page-16-10"></span>[28] M. Schirmer, D. Zhang, and E. Nalisnick. Temporal Test-Time Adaptation with State-Space Models, Nov. 2025. URL <http://arxiv.org/abs/2407.12492>. arXiv:2407.12492 [cs].
- <span id="page-16-2"></span>[29] M. Seeger. Learning with labeled and unlabeled data. Technical report, Institute for Adaptive and Neural Computation, University of Edinburgh, 2000.
- <span id="page-16-3"></span>[30] Y. Sun, X. Wang, Z. Liu, J. Miller, A. Efros, and M. Hardt. Test-time training with self-supervision for generalization under distribution shifts. In International conference on machine learning, pages 9229–9248. PMLR, 2020.

- <span id="page-17-1"></span>[31] D. Wang, E. Shelhamer, S. Liu, B. Olshausen, and T. Darrell. Tent: Fully test-time adaptation by entropy minimization. In International Conference on Learning Representations, 2021.
- <span id="page-17-5"></span>[32] Q. Wang, O. Fink, L. Van Gool, and D. Dai. Continual test-time domain adaptation. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition, pages 7201–7211, 2022.
- <span id="page-17-4"></span>[33] M. West and J. Harrison. Bayesian forecasting and dynamic models. Springer, 1997.
- <span id="page-17-0"></span>[34] Z. Xiao and C. G. Snoek. Beyond model adaptation at test time: A survey. arXiv preprint arXiv:2411.03687, 2024.
- <span id="page-17-2"></span>[35] M. Zhang, S. Levine, and C. Finn. Memo: Test time robustness via adaptation and augmentation. Advances in neural information processing systems, 35:38629–38642, 2022.
- <span id="page-17-3"></span>[36] A. Zhou and S. Levine. Bayesian adaptation for covariate shift. Advances in neural information processing systems, 34:914–927, 2021.