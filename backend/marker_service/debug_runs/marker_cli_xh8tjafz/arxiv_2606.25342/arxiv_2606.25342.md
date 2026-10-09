# Lifelong In-Context Learning with Transformers Requires Parametric Forms of Attention

Luke McDermott UC San Diego lmcdermo@ucsd.edu

Robert W. Heath Jr. UC San Diego rwheathjr@ucsd.edu

Rahul Parhi UC San Diego rahul@ucsd.edu

# Abstract

Lifelong continual learning remains an obstacle on the path to human-like intelligence. Modern transformers show sparks of intelligence with in-context learning. The quadratic nature of attention, however, prohibits transformers from performing this process on arbitrarily long sequences. In this work, we argue that extending in-context learning to lifelong settings is a practical solution for continual learning in AI agents. In particular, we argue that *parametric forms of attention* are needed to understand a lifetime of context with transformers on a fixed hardware budget. These attention mechanisms learn the relationship between keys and their associated values at test-time with parametric regression. Our generalization of parametric approaches (linear attention, state-space models, fast weight programmers, and test-time training layers) contrasts with nonparametric counterparts like softmax attention. They replace the ever-growing key-value cache with an onlinetrainable neural network, maintaining a constant memory footprint. We highlight how parametric attention currently fall short of lifelong learning due to limited memory capacity or costly online updates. To address these issues, we pose a set of open questions with novel insights to guide the field toward long-horizon agents.

# 1 Introduction

Modern AI systems are trained *offline* on vast but finite datasets. When new capabilities are desired, the training recipe is extended (additional data, mid-training stages, etc.), and the model is retrained. This paradigm has been effective for short-horizon applications like chatbots, yet acting over longer horizons—such as the millions to trillions of tokens in a human lifetime—remains elusive.

Deployment becomes the dominant source of novel information as systems move toward agents that run for months or years, such as autonomous research agents [\[51\]](#page-11-0) or embodied systems [\[28\]](#page-10-0). The space of environments, tasks, and facts an agent encounters at inference far exceeds anything a finite training pipeline can prepare for. Following the "Big World" perspective [\[39\]](#page-11-1), the world is much more complex than an agent can model, making strong priors (i.e. knowledge from pretraining) a gross approximation of reality. Agents must continue to learn at runtime from a stream of observations, especially under practical compute and memory budgets. As a result, deep learning models must move beyond offline training and learn from experience.

Transformers provide a practical starting point to solving lifelong learning [\[12\]](#page-9-0). With attention, transformers exhibit a weak form of online adaptation through *in-context learning*. Conditioned on a short prompt, transformers adjust their behavior based on examples and instructions at inference time. However, softmax attention currently prohibits transformers from processing arbitrarily long contexts, preventing true long-horizon thinking in lifelong settings. Our paper focuses on the more tractable variant of lifelong learning: *lifelong in-context learning* with transformers. This requires performing inference over an unbounded stream of tokens under fixed hardware. The model must

learn facts, tasks, trends, etc. from context and answer future queries using information from the stream, without unbounded external storage.

To support lifelong in-context learning, we advocate for rethinking attention as an online learner. Building upon the lens of test-time regression [\[42\]](#page-11-2), attention learns the relationship between keys and their associated values from the context at test-time. The set of key-value pairs forms an online training set, with the query as an unlabeled test point. Attention therefore solves a self-supervised regression subproblem induced by the rest of the transformer. In our generalization, softmax attention estimates the underlying key-to-value map with a nonparametric regressor (Nadaraya-Watson kernel estimation [\[29;](#page-10-1) [43\]](#page-11-3)). It stores past examples in a key-value cache, causing inference costs to grow with context length. This representation constrains softmax attention to finite horizons under fixed hardware. Sparse alternatives [\[30\]](#page-10-2) may bound the size of the KV cache. However, they evict tokens entirely rather than merge past memories. While effective for recalling specific observations, sparse methods do not merge experiences into general knowledge or task-relevant sufficient statistics.

We argue that extending in-context learning in transformers to lifelong streams requires evictionless, *parametric forms of attention*. Under fixed hardware, an agent cannot retain every raw key-value pair it observes. Past experience must instead be learned from and merged into a bounded representation for future use. Parametric attention provides this mechanism by learning a finite-dimensional regressor over past keys and values, replacing the ever-growing KV cache with an online-updated representation of context. This enables lifelong in-context learners to understand new tasks, rather than merely recall a subset of past tokens.

This parametric structure appears across recent work on linear attention [\[26;](#page-10-3) [33;](#page-10-4) [47\]](#page-11-4), state-space models [\[15\]](#page-9-1), and fast-weight memories [\[5\]](#page-9-2). In particular, methods that perform gradient descent online to optimize the key-to-value estimate (denoted test-time training [\[37\]](#page-11-5)) are the most promising candidates for lifelong learning [\[6;](#page-9-3) [7;](#page-9-4) [50;](#page-11-6) [9\]](#page-9-5). Despite progress, these approaches still face open problems in update efficiency [\[50\]](#page-11-6), memory capacity [\[27\]](#page-10-5), and objective design [\[41;](#page-11-7) [8\]](#page-9-6). Rather than proposing yet another mechanism, we organize these gaps into under-addressed questions intended to steer test-time training toward long-horizon agents.

Parametric forms of attention are a natural evolution in a rich history of adaptive filtering [\[44\]](#page-11-8), kernel regression [\[29;](#page-10-1) [43\]](#page-11-3), and associative memory (e.g., Hopfield networks) [\[23\]](#page-10-6), through fast-weight programming [\[34\]](#page-10-7) and recurrent sequence models [\[21\]](#page-10-8). Transformers' query-key-value representation created a practical and parallelizable platform to bring old ideas to modern hardware. With this paper, we aim to draw in researchers from self-supervised learning, reinforcement learning, and continual learning to help identify the right objectives, update rules, and architectures for long-horizon in-context learning.

![](_page_1_Figure_5.jpeg)

<span id="page-1-0"></span>Figure 1: Attention as Test-Time Regression [\[42\]](#page-11-2). Across three time steps, we illustrate how attention generates self-supervised training pairs and sequentially fits an estimator m<sup>t</sup> . The output of attention at any given time is the prediction of the query.

# 2 Attention as Test-Time Regression

**m2** As a preliminary, we briefly explain traditional views of attention and formally introduce our perspective on attention as an online-learning algorithm. Then, we distinguish nonparametric and parametric mechanisms.

### 2.1 Defining Attention

Transformers process a sequence of input tokens  $\{x_t\}_{t=1}^n$ , where  $x_t \in \mathbb{R}^d$  [40]. For each attention head, the input tokens are transformed into three representations—queries, keys, and values—via learned linear projections  $\mathbf{W}_q, \mathbf{W}_k \in \mathbb{R}^{d_k \times d}$  and  $\mathbf{W}_v \in \mathbb{R}^{d_v \times d}$  with

$$\underbrace{q_t = \mathbf{W}_q \, \mathbf{x}_t}_{\text{query}}, \quad \underbrace{k_t = \mathbf{W}_k \, \mathbf{x}_t}_{\text{key}}, \quad \underbrace{v_t = \mathbf{W}_v \, \mathbf{x}_t}_{\text{value}}. \tag{1}$$

In causal softmax attention, the output at time t is computed as

$$\mathbf{y}_t = \frac{\sum_{j=1}^t \exp(\mathbf{q}_t^{\top} \mathbf{k}_j / \sqrt{d_k}) \mathbf{v}_j}{\sum_{j=1}^t \exp(\mathbf{q}_t^{\top} \mathbf{k}_j / \sqrt{d_k})} \in \mathbb{R}^{d_v}.$$
 (2)

This is interpreted as a local average of past values, weighted by how similar the key is to the query.

#### **Generalization of Attention**

We view attention as an online learning algorithm that recurrently constructs an estimate  $m_t$ :  $\mathbb{R}^{d_k} \to \mathbb{R}^{d_v}$  for an unknown, nonstationary  $\mathit{ground-truth}$  function  $m_t^*: \mathbb{R}^{d_k} \to \mathbb{R}^{d_v}$  that exactly maps keys to their associated values within a given context:  $v_t = m_t^*(k_t)$ . The overall goal to closely approximate  $m_t^*$  with  $m_t$ . At inference time, attention receives a stream of self-supervised training examples  $\{(k_j, v_j)\}_{j \leq t}$  generated by the transformer. These are often  $\mathit{not}$  i.i.d. as the input tokens  $\{x_j\}_{j \leq t}$  can be causally dependent. Attention estimates the key-to-value relationship, then predicts the value associated with the query  $q_t$  as the output  $y_t$ . This decomposes inference into an online learning problem:

Online training set: 
$$(k_1 \rightarrow v_1), (k_2 \rightarrow v_2), ..., (k_t \rightarrow v_t)$$
  
Unlabeled test point:  $(q_t \rightarrow ?)$ 

Thus, attention constructs the estimator  $m_t: \mathbb{R}^{d_k} \to \mathbb{R}^{d_v}$ , such that

$$m_t(\mathbf{k}_t \mid \{(\mathbf{k}_j, \mathbf{v}_j)\}_{j < t}) \approx m_t^*(\mathbf{k}_t) = \mathbf{v}_t, \tag{3}$$

with the goal of generalization:

$$\mathbf{y}_t = m_t(\mathbf{q}_t \mid \{(\mathbf{k}_j, \mathbf{v}_j)\}_{j \le t}) \approx m_t^*(\mathbf{q}_t). \tag{4}$$

We visualize this interpretation of attention as a form of test-time regression over keys and values [42] in Figure 1. We intentionally separate attention as a special kind of recurrent neural network (RNN)<sup>1</sup> that 1) explicitly forms self-supervised labels (key-value pair), 2) learns to predict one view from another (key-to-value estimation), and 3) predicts the association of a query  $q_t$  (the output  $y_t$ ). This structure continually generates and solves its own subtasks (the key-value online training set) for the transformer to achieve its overarching goals (e.g. next-token prediction) [39]. To solve the transformer's "offline objective", pretraining optimizes how the online training set (key-value pairs) is generated for a given input sequence. This positions pretraining as a nested learning process [9].

In a related perspective,  $m_t$  acts as an associative memory system [20; 52] with each key-value pair serving as an associative memory. Building on ideas similar to Hopfield networks [23], this perspective [24] has inspired a resurgence of memory architectures across modern attention mechanisms [9].

#### 2.2 Nonparametric vs. Parametric

We classify attention mechanisms by how they represent the key-to-value estimators. Nonparametric forms of attention use nonparametric methods (e.g. nearest neighbors), leveraging infinite degrees of freedom and often unbounded inference costs. These approaches make minimal assumptions on  $m_t^*$  as they do not construct a set of parameters, often using the training data as "parameters".

As the most popular instance of nonparametric attention, softmax attention corresponds to using Nadaraya-Watson kernel regression with an RBF kernel when queries and keys have unit 2-norm.

<span id="page-2-0"></span><sup>&</sup>lt;sup>1</sup>We define RNNs as a general sequentially-updating function f that maps an input and hidden state  $(\boldsymbol{x}_t, \boldsymbol{h}_t)$  to an output with an updated hidden state  $(\boldsymbol{y}_t, \boldsymbol{h}_{t+1})$ . The hidden state is not restricted to any form, nor are other representations of the input enforced.

![](_page_3_Picture_0.jpeg)

![](_page_3_Picture_1.jpeg)

Figure 2: Nonparametric attention use keyvalue pairs to form the estimator, leading to unbounded growth. Softmax attention can be viewed as an MLP with KV pairs as weights.

Figure 3: Parametric attention learns the key-to-value associations with a fixed-sized parametric function. These parameters are trained at test-time to predict the associated value of a key.

**Theorem 2.1** (Wang et al. 42; Sun et al. 37; Zhang et al. 49; Han et al. 18). For a query  $q_t \in \mathbb{R}^{d_k}$  and context  $\{(\mathbf{k}_j, \mathbf{v}_j)\}_{j \leq t}$  with  $\|\mathbf{q}_t\|_2 = \|\mathbf{k}_j\|_2 = 1$ , softmax attention is equivalent to a Nadaraya–Watson estimator with kernel  $\mathcal{K}_h(\mathbf{q} - \mathbf{k}) = \exp(\mathbf{q}^\top \mathbf{k}/\sqrt{d_k})$  and bandwidth  $h = d_k^{1/4}$ :

$$m_t(\boldsymbol{q}_t \mid \{(\boldsymbol{k}_j, \boldsymbol{v}_j)\}_{j \le t}) := \frac{\sum_{j=1}^t \mathcal{K}_h(\boldsymbol{q}_t - \boldsymbol{k}_j) \, \boldsymbol{v}_j}{\sum_{j=1}^t \mathcal{K}_h(\boldsymbol{q}_t - \boldsymbol{k}_j)}.$$
 (5)

In this case, the regressor  $m_t(\mathbf{q}_t \mid \{(\mathbf{k}_j, \mathbf{v}_j)\}_{j \leq t})$  is the average of all values in a local neighborhood around  $\mathbf{q}_t$ , with the neighborhood shaped by the kernel  $\mathcal{K}_h(\mathbf{q}_t - \mathbf{k}_j)$ . Our generalization of attention allows for *any* regressor to be used in place of the Nadaraya–Watson estimator. For example swapping this estimator with kernel ridge regression with  $\mathcal{K}_h$  (defined above) corresponds to

$$\mathbf{y}_{t} = \exp\left(\frac{\mathbf{q}_{t} \mathbf{K}_{t}^{\top}}{\sqrt{d_{k}}}\right) \left(\exp\left(\frac{\mathbf{K}_{t} \mathbf{K}_{t}^{\top}}{\sqrt{d_{k}}}\right) + \lambda \mathbf{I}\right)^{-1} \mathbf{V}_{t}, \tag{6}$$

though this more computationally expensive. Here,  $\mathbf{K}_t = [\mathbf{k}_1, \dots, \mathbf{k}_t] \in \mathbb{R}^{t \times d_k}$ ,  $\mathbf{V}_t = [\mathbf{v}_1, \dots, \mathbf{v}_t] \in \mathbb{R}^{t \times d_v}$ , the regularization coefficient  $\lambda > 0$ , and uses elementwise exponential.

Parametric forms of attention bound the degrees of freedom of the estimator  $m_t$  by using parametric regression. Instead of storing the past key-value pairs  $\{(k_j, v_j)\}_{j \leq t}$  as the estimator itself, they summarize the context with a finite number of online parameters  $\theta_t \in \mathbb{R}^p$ , for some fixed p. We write the resulting key-to-value regressor as  $m_t(\cdot \mid \theta_t) : \mathbb{R}^{d_k} \to \mathbb{R}^{d_v}$ . This category of attention encompasses many past approaches, such as linear attention, state-space models, fast-weight programmers, and test-time training layers. In these cases,  $\theta_t$  is the vectorized hidden state, where p is the maximum total number of elements in the state. Our definition intentionally includes sparse mechanisms that only store a finite amount of tokens. For example, sliding window attention [14] with window size c has a bounded set of parameters where

$$\theta_t = \text{vectorize}(\{(\boldsymbol{k}_j, \boldsymbol{v}_j)\}_{j=t-c+1}^t). \tag{7}$$

Query-dependent sparse attention methods [30] may retrieve a constant amount of tokens, but these require storing (or offloading) the whole KV cache somewhere. These are not feasible for lifelong in-context learning as we cannot store an arbitrarily long context.

## 3 Limitations of Nonparametric & Sparse Attention

Under fixed-hardware constraints, nonparametric estimators cannot be used as their footprint grows with the number of observed samples. We observe this clearly with softmax attention, as each new key-value pair  $(k_t, v_t)$  is appended to the KV cache in order to estimate the map  $m_t^*$ . As inference costs grow beyond what hardware can support, past observations must be discarded or approximated.

While sparse attention methods (both the parametric and nonparametric kind) are an attractive way to extend the context window for modern LLM applications, they are not solutions to lifelong learning. These approaches retain only a subset of key-value pairs, evicting "unimportant" tokens from the

cache. These methods fundamentally fail on any task that requires modeling of the *whole* context. Consider a sequence of updates

$$x \leftarrow 5$$
,  $y \leftarrow x + 5$ ,  $x \leftarrow 3$ ,  $z \leftarrow y + x$ .

Answering a query about z requires incorporating every prior update. Dropping any assignment (e.g.  $x \leftarrow 3$ ) renders the query unanswerable, regardless of how accurately the remaining tokens are recalled. Instead, the information from past tokens should be abstracted and compressed into a finite-dimensional representation. This becomes increasingly important when entire tasks must be learned in-context, rather than just remembering a set of specific events. As a result, attention mechanisms that support lifelong in-context learning must have:

- 1) Expressive in-context memory. The online function  $m_t$  must recall specific events, understand general concepts, and preserve task-relevant information from the whole context, rather than merely retaining a subset of raw tokens.
- 2) Per-token inference costs independent of context length. The lifetime of these models is not known in advance. In-context learners must at least be able to process arbitrarily long contexts, eliminating nonparametric estimators for  $m_t$ .
- **3) Parallelizable updates.** For widespread adoption, methods should efficiently utilize modern hardware [22] such as GPUs/TPUs, a weakness of traditional RNNs. We expect these to at least incorporate chunkwise-parallelism [48].

## 4 Test-Time Parametric Regression as a Solution

Eviction-less parametric attention methods remain the most plausible candidates for lifelong incontext learning. In this section, we argue that *test-time training* methods are the most promising lifelong learners. We formally define these methods, discussing different design patterns and limitations.

#### 4.1 Online Objectives

Parametric forms of attention with test-time training define a differentiable loss function,  $\mathcal{L}$ , to model all contextual information with  $\theta_t$ . These methods can form higher-level abstractions that generalize as the context length increases. To encourage  $m(\mathbf{k}_t|\theta_t) \approx \mathbf{v}_t$ , the online parameters  $\theta_t$  are updated via gradient descent with learning rate  $\beta_t \in \mathbb{R}$ ,

$$\theta_t = \theta_{t-1} - \beta_t \, \nabla_{\theta} \mathcal{L}(\theta_{t-1}, \mathbf{k}_t, \mathbf{v}_t), \tag{8}$$

or similar optimization step. Choices for  $\mathcal{L}$  are commonly

$$\underbrace{-\langle m(\boldsymbol{k}_t \mid \boldsymbol{\theta}_{t-1}), \boldsymbol{v}_t \rangle}_{\text{Hebbian rule [19]}} \quad \underbrace{\|m_t(\boldsymbol{k}_t \mid \boldsymbol{\theta}_{t-1}) - \boldsymbol{v}_t\|_2}_{\text{Delta rule [45; 31; 33]}} \quad \text{or} \quad \underbrace{\sum_{j=t-c}^t \gamma_j \|m_t(\boldsymbol{k}_j \mid \boldsymbol{\theta}_{t-1}) - \boldsymbol{v}_j\|_2}_{\text{Omega Rule [7]}}. \quad (9)$$

Though, new update steps are an active area of research. Input-dependent learning rates [33], weight decay (gating) [38; 47; 15; 46], momentum (vanilla [6] or orthogonalized [25; 7; 50]), and higher-rank gradients [35; 7] have also been incorporated into these update rules.

#### 4.2 Parametric Functions

The family of parametric functions for  $m_t$  is also under exploration. Literature, such as the recent revival of state-space models [17; 16; 15], commonly uses linear functions. Notably, linear attention [26], updates a linear map with the Hebbian rule,

$$m_t(\boldsymbol{q}_t|\theta_t) = \theta_t \boldsymbol{q}_t, \quad \theta_t = \theta_{t-1} + \boldsymbol{v}_t \boldsymbol{k}_t^{\top} \in \mathbb{R}^{d_v \times d_k}.$$
 (10)

On one hand, linear maps provide flexibility when parallelizing the online parameter updates over time [48], though they fall short in memory capacity [27]. The number of orthogonal key-value pairs that can be stored is bounded by the rank of  $\theta_t$ . This can lead to degraded forms of long term

memory, crucial for lifelong learning. On the other hand, online MLPs can learn much more complex key-to-value relationships with a relatively small footprint [37; 6; 50; 7], though these are expensive to update. Updating  $\theta_t$  may require multiple backpropagation steps to fit the incoming KV pair.

Hybrid mechanisms can combine these approaches to fully leverage chunkwise-parallelism. In practice, fully parallelizing the context is not required under fixed hardware budgets. Only a subsequence large enough to saturate available VRAM needs to be parallelized. This view naturally motivates hybrid short- and long-term memory systems. For example, LaCT [50] pairs a fast local mechanism (sliding window attention) for recent context with a slow-updating MLP memory for long-term storage, updating the long-term memory once per chunk.

Moving forward, deep nonlinear parametric memories may present the strongest form of in-context learning. With test-time training, these can compress vast experience into a fixed-size latent state. Over long horizons, the estimator continually improves its high-level representation of the context, serving as an expressive in-context memory system. With the help of hybrid attention mechanisms, these can be trained fast with chunkwise-parallelism and constant per-token inference costs.

## 5 Open Questions and Research Directions

While parametric attention defines the relevant solution class, current methods still fall short in efficiency, capacity, and objective design. We highlight a small set of open questions that we believe will determine whether test-time learning mechanisms become practical for long-horizon agents.

**Question #1:** If the goal is not to memorize key-value pairs, what is the greater online objective? How should objectives incorporate regularization?

As with most machine learning, the training loss is only a proxy; the ultimate goal is to perform well on the test set. To translate this to attention and test-time training, mapping past keys to their values is not the end goal;  $m_t$  must map the query to the correct output  $y_t$ . The "correctness" of the output is ultimately determined by the transformer and how well it solves the offline objective (next-token prediction). While this distinction seems obvious, this emphasis on generalization opens up novel insights on how the online objective should be designed.

In this section, we argue that forms of regularization in the online objective are needed. Gating mechanisms, which can be viewed as online weight decay, are the most notable forms of regularization as they forget old information to make space for new knowledge. Additionally, we observe implicit forms of regularization in both softmax attention and multi-headed linear attention, making them better online learners. We question how future algorithms can incorporate explicit forms of regularization in new memory architectures.

Case Study: Softmax Attention Softmax Attention does not achieve perfect in-context recall. If  $m_t(\mathbf{k}_t) \approx \mathbf{v}_t$  was the ultimate objective, then this problem is trivial: just look up  $\mathbf{k}_t$  in the KV cache and retrieve its value. Mathematically, tightening the bandwidth of softmax attention's RBF kernel recovers this nearest-neighbors retrieval,

$$\lim_{h \to 0} m_t(\mathbf{k}_i) = \lim_{h \to 0} \frac{\sum_{j=1}^t \mathcal{K}_h(\mathbf{q}_t - \mathbf{k}_j) \mathbf{v}_j}{\sum_{j=1}^t \mathcal{K}_h(\mathbf{q}_t - \mathbf{k}_j)} = \mathbf{v}_i$$
(11)

for  $\mathcal{K}_h(q_t-k_j)=\exp(-\frac{\|q_t-k_j\|_2^2}{2h^2})=\exp(q_t^{\top}k_j/h^2))$  with QK-Norm. As  $h\to 0$ , the estimator approaches nearest-neighbor retrieval. This interpolates the observed key-value pairs but gives no mechanism for generalization as the query can only be mapped to an observed value,

$$\lim_{h \to 0} m_t(\mathbf{q}_t) \in \{\mathbf{v}_j\}_{j \le t}. \tag{12}$$

Softmax attention (as opposed to "hardmax") provides a more generalizable estimate the key-to-value map, with respect to the query, though it does not perfectly interpolate the "online training data".

**Case Study: Multi-Headed Linear Attention** Linear attention and SSMs have generally related higher-dimensional hidden states to better in-context abilities. However, this is not exactly a rigorous

rule-of-thumb. There is more nuance than the number of online parameters. For evidence, we look towards the role of multi-headed attention in linear attention.

Increasing the number of attention heads in a linear attention layer decreases the number of online parameters. An h-headed, d-dimensional linear attention layer estimates a different linear map for each head. For each head, i, and its linear map,  $\theta_t^{(i)} \in \mathbb{R}^{d_v \times d_k}$ , the output is defined as

$$\mathbf{y}_{t}^{(i)} = m^{(i)}(\mathbf{q}_{t}^{(i)}|\theta_{t}^{(i)}) = \theta_{t}^{(i)}\mathbf{q}_{t}^{(i)} \in \mathbb{R}^{d_{v}}$$
(13)

such that  $d=d_kh=d_vh$ . The heads' outputs are eventually concatenated passed through a projection matrix  $\mathbf{W}_{\text{proj}} \in \mathbb{R}^{d \times d}$ . As a result, multi-headed linear attention constructs the overall key-to-value estimate as a block diagonal matrix:

$$\boldsymbol{y}_{t} = \left[\boldsymbol{y}_{t}^{(1)}, \boldsymbol{y}_{t}^{(2)}, \dots, \boldsymbol{y}_{t}^{(h)}\right] = \left[\theta_{t}^{(1)} \boldsymbol{q}_{t}^{(1)}, \dots, \theta_{t}^{(h)} \boldsymbol{q}_{t}^{(h)}\right] = \begin{bmatrix} \theta_{t}^{(1)} & 0 & \dots & 0 \\ 0 & \theta_{t}^{(2)} & \dots & 0 \\ \vdots & \vdots & \ddots & \vdots \\ 0 & 0 & \dots & \theta_{t}^{(h)} \end{bmatrix} = \theta_{t} \boldsymbol{q}_{t}. \tag{14}$$

The number of active parameters in  $\theta_t$  is  $d_k d_v h = d^2/h$ . Additional heads regularize  $\theta_t$ , preventing the estimator from fully fitting to the context. In the single-headed case (with  $d_k = d$ ), we observe that  $m_t$  has a simple closed-form solution for estimating  $m_t^*$ . If  $\mathbf{W}_k$  is invertible, then

$$\exists \mathbf{W}_{k}^{-1} \implies \mathbf{x}_{t} = \mathbf{W}_{k}^{-1} \mathbf{k}_{t} \implies (\mathbf{W}_{v} \mathbf{W}_{k}^{-1}) \mathbf{k} = \mathbf{v}, \forall (\mathbf{k}, \mathbf{v}) \implies m_{t}^{*}(\mathbf{q}) = (\mathbf{W}_{v} \mathbf{W}_{k}^{-1}) \mathbf{q}. \tag{15}$$

The underlying key-to-value map is a linear function with  $\theta_t^* = (\mathbf{W}_v \mathbf{W}_k^{-1})$ . Crucially, the solution no longer depends on the context  $(x_1, x_2, \ldots)$ . Therefore, the perfect estimator (w.r.t the online objective) is static and does not incorporate any information from the prompt. This case study shows how converging to lower-loss solutions (i.e. using "better" optimizers) does not make a better attention mechanism. The usefulness of parametric attention depends as much on the learned self-supervised task as on the online optimizer. As a reminder, sufficient pretraining teaches the transformer how to generate informative self-supervised datasets (key-value pairs).

To measure the generalization behaviors of  $m_t$  in practice, we suggest tracking the online loss for future key-value pairs. If  $m_t$  can model future associations,  $(k_{t+i}, v_{t+i})$  for i > 0, then the estimator may understand the underlying sequence that our context is a part of. Of course, this still requires the online task to be sufficiently difficult.

In summary, the goal of the estimator is not only to memorize past relationships,  $m_t(k_j) \approx v_j, \forall j \leq t$ , but to also generalize to unseen queries,  $m_t(q_t)$ . Associative memory systems that fit to the online training set can recall exact historical information, which is the foundation for episodic memory. However, lifelong in-context learning also requires understanding semantic information, which can be viewed as abstractions of past events. To recall a fact, such as knowing the earth revolves around the sun, efficient memory systems should not have to trace back to the time they first learned this fact. Attention mechanisms should also broadly store knowledge after learning it in-context.

#### **Question #2:** How can online loss functions efficiently contain longer-horizon signals?

Besides fitting to new observations and retaining earlier associations, lifelong learning requires identifying trends that emerge over time. For the next generation of parametric methods, long-horizon information needs to be incorporated in the online parameters. This motivates our question about how to best model the whole context under a fixed compute budget.

Early parametric methods, such as linear attention, Deltanet, and Retnet [38], only use the current key-value pair to update the online parameters. Methods with instantaneous loss functions enforce  $m_t(\mathbf{k}_t) \approx \mathbf{v}_t$ , but these can only hope that  $m_t$  retains past knowledge ( $m_t(\mathbf{k}_j) \approx \mathbf{v}_j$  for j < t). Especially with linear methods, McDermott et al. observe that instantaneous updates can unintentionally overwrite past information, leading to catastrophic forgetting. While instantaneous objectives are efficient, these are likely suboptimal for memory retention.

We observe two common trends in recent literature that inject longer-horizon information: batched updates and auxiliary states. While we believe these ideas are on the right track, we note that current parametric attention methods still use short-horizon updates. This remains an open problem on the path to true lifelong in-context learning.

**Batched Updates.** Memory updates can be performed over a batch of key-value pairs. Behrouz et al. use a sliding window of the last c tokens, optimizing a weighted regression loss with decay terms  $\gamma_i$ .

$$\sum_{i=t-c+1}^{t} \gamma_i \| m(\mathbf{k}_i | \theta_{t-1}) - \mathbf{v}_i \|_2^2,$$
(16)

denoted the Omega rule. Moving beyond a sliding window, other sparse attention criteria can select which tokens should be cached and used again for future updates (akin to memory replay in continual learning [32]). For example, key-value pairs in the current batch that are not properly estimated by  $m_t$  can be cached for the next batch [27].

**Auxiliary States.** A second approach is to leverage additional memory states for a more informative update. As an example, MesaNet [41] implements a second-order optimizer over the cumulative loss,

$$\sum_{j=1}^{t} \|m(\mathbf{k}_{j}|\theta_{t-1}) - \mathbf{v}_{j}\|_{2}^{2} + \frac{1}{2} \text{Tr}(\theta_{t-1} \Lambda \theta_{t-1}), \tag{17}$$

with  $\Lambda$  acting as a quadratic regularizer. This loss is optimized by

$$\theta_t^{(1)} = \gamma_t \theta_{t-1}^{(1)} + \beta_t v_t k_t^{\top} \text{ and } \theta_t^{(2)} = \gamma_t \theta_{t-1}^{(2)} + \beta_t k_t k_t^{\top}, \text{ with } y_t = \theta_t^{(1)} (\theta_t^{(2)} + \Lambda)^{-1} q_t.$$
 (18)

Here,  $\theta_t^{(1)}$  forms the base key-to-value map, with a gated linear attention learning rule [47], and  $\theta_t^{(2)}$  decorrelates past keys. The additional state improves key-to-value learning while still maintaining the efficiency of linear maps. This concept of accumulating historical information in alternative states is also present in momentum-based optimizers [6] (though on a much shorter horizon).

Combining both approaches, LaCT [50] and Atlas [7] compute the online loss over the past chunk of tokens and use an additional momentum state with the Muon optimizer [25]. A hidden state  $\theta_t^{\text{(hs)}}$  is updated with a momentum state  $\theta_t^{\text{(mnt)}}$ , not the direct gradient, as in

$$\theta_t^{(\text{mnt})} = \gamma_t \theta_{t-1}^{(\text{mnt})} + \nabla_{\theta} \mathcal{L}(\theta, \boldsymbol{k}, \boldsymbol{v}) \text{ and } \theta_t^{(\text{hs})} = \theta_{t-1}^{(\text{hs})} - \beta_t \text{ NS}(\theta_t^{(\text{mnt})}) \text{ with } \boldsymbol{y}_t = f(\boldsymbol{q}_t, \theta_t^{(\text{hs})}). \tag{19}$$

Here, f is some function parametrized by  $\theta_t^{(\text{hs})}$ , and  $\gamma_t$  still represents a decay term. The loss  $\mathcal{L}$  is computed over the past sliding window / chunk of KV-pairs, and the momentum term  $\theta_t^{(\text{mnt})}$  is orthogonalized with Newton-Schulz matrix iteration (NS) [25; 10; 13]. Orthogonalization prevents any singular vector in the update from overwriting stored values in online parameters, similar to how low-rank updates observe less catastrophic forgetting [11].

In summary, batched updates and auxiliary states shown to improve contextual modeling [7]; though, there is still work to be done. We suggest researchers to draw inspiration from continual learning over data-streams. In particular, future attention mechanisms should make use of memory replay [3].

**Question #3:** Are linear self-supervised labels sufficient? How should keys and values be generated?

In parametric attention, the online learner  $m_t$  is trained on self-supervised pairs  $(k_t, v_t)$  produced by the offline transformer. During pretraining, the transformer must learn to create informative online tasks that attention solves during inference. We question how the key-value observations should be generated, as this directly relates to what kind of information the online estimator learns. As a reminder, to scalably learn at test-time, the online tasks or subproblems cannot be hand-crafted and should minimize the amount of human priors [39].

Most transformer implementations generate  $k_t$  and  $v_t$  as linear projections of  $x_t$ , which makes the key-to-value map structurally simple. Nonlinear constructions can make the underlying map  $m_t^*$  more complex and may force  $m_t$  to capture higher-level structure from context. This can be performed through nonlinear feature maps such as  $k_t = \mathbf{W}_k^{(2)} \sigma(\mathbf{W}_k^{(1)} x_t)$ . Temporal information can be encoded into the key-value pair with positional embeddings (e.g. RoPE [36]), changing the online estimation. Lastly, key-value pairs do not have to be functions of  $x_t$  alone. Short convolutions and other local mixing operations have commonly been used in recurrent sequence models [2]. This creates short-horizon observations for  $m_t$  to estimate.

The ratio between self-supervised label (KV pairs) and test points (queries) is an underexplored design axis. Standard multi-headed attention produces one query and one key-value pair per head per token. Grouped-query attention [\[1\]](#page-9-15) reduces the number of distinct key-value memories while keeping many queries, allowing multiple "questions" to be asked to same contextual model mt. In the other direction, DeltaProduct updates m<sup>t</sup> with multiple key-value pairs from a token for a richer update [\[35\]](#page-10-16). Notably, this enables state tracking behavior in linear models. Understanding this tradeoff likely depends on the parametric family used for mt; however, this raises many fundamental questions about the role of multi-headed attention. For example, do deep nonlinear memories still need multiple heads, or can a single expressive estimator suffice?

The current literature lacks a fundamental understanding of what this self-supervised task should look like. What properties of the generated (kt, vt) pairs make the resulting online learner useful for the outer objective? Is there a relationship between the difficulty of this task and its usefulness? We expect progress here to draw from self-supervised learning, where the central question is how to construct informative views and prediction targets, such as work on latent prediction like JEPA [\[4\]](#page-9-16).

# 6 Alternative Views

This paper intends to shift the focus towards parametric forms of attention. With this, we expect some controversy, especially around 1) the sufficiency of current transformers 2) the scalability of parametric attention methods and 3) the novelty of this position.

(a) *Modern transformers are a sufficient backbone for agents when augmented with retrieval, tool use, recursive prompting, etc.*

These systems are important, but they do not remove the need for parametric attention. External memory can preserve episodic traces of experience; it cannot, by itself, turn those experiences into reusable internal structure. A lifelong agent cannot repeatedly re-read a lifetime of notes every time it acts. These systems are still useful *in combination* with parametric methods, similar to how notebooks augment human intelligence.

(b) *There's little evidence that these approaches even scale to hundreds of billions (or trillions) of parameters!*

We agree that these methods (SSMs, linear attention, test-time training layers) have been mostly evaluated at smaller scales (8B parameter LLMs), often under academic training budgets. However, we argue that this response should motivate further research in the area, not pre-emptively halt its progression. Following the spirit of our position, this should urge researchers to isolate the bottlenecks that prevent scaling, studying them directly, rather than dismiss these methods outright.

(c) *This position is not new; SSMs, linear attention, and test-time training are all quite popular!*

We agree that these directions have gained traction in recent years. However, their framing and impact are not yet universal; much of the sequence-modeling literature treats SSMs and linear attention as alternatives to transformers, rather than an extension of it. Meanwhile, many practitioners still treat transformers as a static backbone and focus on via sparse attention and wrappers. Our goal of this paper is to translate the ideas of test-time training back into the world of transformers. We demonstrate that softmax attention is an online learner, performing a similar self-supervised process.

# 7 Conclusion

In this paper, we argued that lifelong in-context learning under fixed compute is a fundamental problem for AI systems. We framed attention as an online learner to make explicit what must change as we move toward long-horizon agents. Softmax attention represents experience nonparametrically by retaining past key-value pairs, so inference cost grows with context length. We advocated for *parametric forms of attention*, which learn from self-supervised observations of the context while maintaining constant per-token inference costs. In particular, we emphasized test-time training as a direct way to optimize parametric memories online.

Despite promising progress, current parametric approaches remain limited by update efficiency, memory capacity, objective design, and long-horizon training. We therefore formulate open questions that make these bottlenecks precise and guide work on attention mechanisms for lifelong settings.

# References

- <span id="page-9-15"></span>[1] Joshua Ainslie, James Lee-Thorp, Michiel De Jong, Yury Zemlyanskiy, Federico Lebrón, and Sumit Sanghai. Gqa: Training generalized multi-query transformer models from multi-head checkpoints. *arXiv preprint arXiv:2305.13245*, 2023.
- <span id="page-9-14"></span>[2] Zeyuan Allen-Zhu. Physics of language models: Part 4.1, architecture design and the magic of canon layers, 2025. URL <https://arxiv.org/abs/2512.17351>.
- <span id="page-9-13"></span>[3] Simran Arora, Aman Timalsina, Aaryan Singhal, Benjamin Spector, Sabri Eyuboglu, Xinyi Zhao, Ashish Rao, Atri Rudra, and Christopher Ré. Just read twice: closing the recall gap for recurrent language models, 2024. URL <https://arxiv.org/abs/2407.05483>.
- <span id="page-9-16"></span>[4] Mahmoud Assran, Quentin Duval, Ishan Misra, Piotr Bojanowski, Pascal Vincent, Michael Rabbat, Yann LeCun, and Nicolas Ballas. Self-supervised learning from images with a jointembedding predictive architecture. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pages 15619–15629, 2023.
- <span id="page-9-2"></span>[5] Maximilian Beck, Korbinian Pöppel, Markus Spanring, Andreas Auer, Oleksandra Prudnikova, Michael K Kopp, Günter Klambauer, Johannes Brandstetter, and Sepp Hochreiter. xlstm: Extended long short-term memory. In *The Thirty-eighth Annual Conference on Neural Information Processing Systems*, 2024.
- <span id="page-9-3"></span>[6] Ali Behrouz, Peilin Zhong, and Vahab Mirrokni. Titans: Learning to memorize at test time. *arXiv preprint arXiv:2501.00663*, 2024.
- <span id="page-9-4"></span>[7] Ali Behrouz, Zeman Li, Praneeth Kacham, Majid Daliri, Yuan Deng, Peilin Zhong, Meisam Razaviyayn, and Vahab Mirrokni. Atlas: Learning to optimally memorize the context at test time. *arXiv preprint arXiv:2505.23735*, 2025.
- <span id="page-9-6"></span>[8] Ali Behrouz, Meisam Razaviyayn, Peilin Zhong, and Vahab Mirrokni. It's all connected: A journey through test-time memorization, attentional bias, retention, and online optimization. *arXiv preprint arXiv:2504.13173*, 2025.
- <span id="page-9-5"></span>[9] Ali Behrouz, Meisam Razaviyayn, Peilin Zhong, and Vahab Mirrokni. Nested learning: The illusion of deep learning architectures. *arXiv preprint arXiv:2512.24695*, 2025.
- <span id="page-9-10"></span>[10] Jeremy Bernstein and Laker Newhouse. Modular duality in deep learning. *arXiv preprint arXiv:2410.21265*, 2024.
- <span id="page-9-12"></span>[11] Dan Biderman, Jacob Portes, Jose Javier Gonzalez Ortiz, Mansheej Paul, Philip Greengard, Connor Jennings, Daniel King, Sam Havens, Vitaliy Chiley, Jonathan Frankle, et al. Lora learns less and forgets less. *arXiv preprint arXiv:2405.09673*, 2024.
- <span id="page-9-0"></span>[12] Magdalena Biesialska, Katarzyna Biesialska, and Marta R Costa-jussà. Continual lifelong learning in natural language processing: A survey. In *Proceedings of the 28th International Conference on Computational Linguistics*, pages 6523–6541, 2020.
- <span id="page-9-11"></span>[13] Åke Björck and Clazett Bowie. An iterative algorithm for computing the best estimate of an orthogonal matrix. *SIAM Journal on Numerical Analysis*, 8(2):358–364, 1971.
- <span id="page-9-7"></span>[14] Rewon Child. Generating long sequences with sparse transformers. *arXiv preprint arXiv:1904.10509*, 2019.
- <span id="page-9-1"></span>[15] Tri Dao and Albert Gu. Transformers are SSMs: Generalized models and efficient algorithms through structured state space duality. In *International Conference on Machine Learning (ICML)*, 2024.
- <span id="page-9-9"></span>[16] Albert Gu and Tri Dao. Mamba: Linear-time sequence modeling with selective state spaces. *arXiv preprint arXiv:2312.00752*, 2024. URL <https://arxiv.org/abs/2312.00752>.
- <span id="page-9-8"></span>[17] Albert Gu, Karan Goel, and Christopher Re. Efficiently modeling long sequences with structured state spaces. In *International Conference on Learning Representations*, 2021.

- <span id="page-10-11"></span>[18] Xing Han, Tongzheng Ren, Tan Nguyen, Khai Nguyen, Joydeep Ghosh, and Nhat Ho. Designing robust transformers using robust kernel density estimation. *Advances in Neural Information Processing Systems*, 36:53362–53384, 2023.
- <span id="page-10-13"></span>[19] Donald Olding Hebb. *The organization of behavior: A neuropsychological theory*. Psychology press, 2005.
- <span id="page-10-9"></span>[20] Geoffrey E Hinton and James A Anderson. Parallel models of associative memory. 1989.
- <span id="page-10-8"></span>[21] Sepp Hochreiter and Jürgen Schmidhuber. Long short-term memory. *Neural Computation*, 9 (8):1735–1780, 1997. doi: 10.1162/neco.1997.9.8.1735.
- <span id="page-10-12"></span>[22] Sara Hooker. The hardware lottery. *Communications of the ACM*, 64(12):58–65, 2021.
- <span id="page-10-6"></span>[23] J J Hopfield. Neural networks and physical systems with emergent collective computational abilities. *Proceedings of the National Academy of Sciences*, 79(8):2554–2558, 1982. doi: 10.1073/pnas.79.8.2554. URL [https://www.pnas.org/doi/abs/10.1073/pnas.](https://www.pnas.org/doi/abs/10.1073/pnas.79.8.2554) [79.8.2554](https://www.pnas.org/doi/abs/10.1073/pnas.79.8.2554).
- <span id="page-10-10"></span>[24] Georgios Iatropoulos, Johanni Brea, and Wulfram Gerstner. Kernel memory networks: A unifying framework for memory modeling, 2024. URL [https://arxiv.org/abs/2208.](https://arxiv.org/abs/2208.09416) [09416](https://arxiv.org/abs/2208.09416).
- <span id="page-10-15"></span>[25] Keller Jordan, Yuchen Jin, Vlado Boza, Jiacheng You, Franz Cesista, Laker Newhouse, and Jeremy Bernstein. Muon: An optimizer for hidden layers in neural networks, 2024. URL <https://kellerjordan.github.io/posts/muon/>.
- <span id="page-10-3"></span>[26] Angelos Katharopoulos, Apoorv Vyas, Nikolaos Pappas, and François Fleuret. Transformers are rnns: Fast autoregressive transformers with linear attention. In *International conference on machine learning*, pages 5156–5165. PMLR, 2020.
- <span id="page-10-5"></span>[27] Luke McDermott, Robert W Heath Jr, and Rahul Parhi. Lola: Low-rank linear attention with sparse caching. *arXiv preprint arXiv:2505.23666*, 2025.
- <span id="page-10-0"></span>[28] Jorge Mendez-Mendez, Leslie Pack Kaelbling, and Tomás Lozano-Pérez. Embodied lifelong learning for task and motion planning. In *Conference on Robot Learning*, pages 2134–2150. PMLR, 2023.
- <span id="page-10-1"></span>[29] Elizbar A Nadaraya. Some new estimates for distribution functions. *Theory of Probability & Its Applications*, 9(3):497–500, 1964.
- <span id="page-10-2"></span>[30] Piotr Nawrot, Robert Li, Renjie Huang, Sebastian Ruder, Kelly Marchisio, and Edoardo M Ponti. The sparse frontier: Sparse attention trade-offs in transformer llms. *arXiv preprint arXiv:2504.17768*, 2025.
- <span id="page-10-14"></span>[31] DL Prados and SC Kak. Neural network capacity using delta rule. *Electronics Letters*, 25(3): 197–199, 1989.
- <span id="page-10-17"></span>[32] David Rolnick, Arun Ahuja, Jonathan Schwarz, Timothy Lillicrap, and Gregory Wayne. Experience replay for continual learning. *Advances in neural information processing systems*, 32, 2019.
- <span id="page-10-4"></span>[33] Imanol Schlag, Kazuki Irie, and Jürgen Schmidhuber. Linear transformers are secretly fast weight programmers. In *International conference on machine learning*, pages 9355–9366. PMLR, 2021.
- <span id="page-10-7"></span>[34] Jürgen Schmidhuber. Learning to control fast-weight memories: An alternative to dynamic recurrent networks. *Neural Computation*, 4(1):131–139, 1992.
- <span id="page-10-16"></span>[35] Julien Siems, Timur Carstensen, Arber Zela, Frank Hutter, Massimiliano Pontil, and Riccardo Grazzi. Deltaproduct: Increasing the expressivity of deltanet through products of householders. In *ICLR 2025 Workshop on Foundation Models in the Wild*, 2025.
- <span id="page-10-18"></span>[36] Jianlin Su, Murtadha Ahmed, Yu Lu, Shengfeng Pan, Wen Bo, and Yunfeng Liu. Roformer: Enhanced transformer with rotary position embedding. *Neurocomputing*, 568:127063, 2024.

- <span id="page-11-5"></span>[37] Yu Sun, Xinhao Li, Karan Dalal, Jiarui Xu, Arjun Vikram, Genghan Zhang, Yann Dubois, Xinlei Chen, Xiaolong Wang, Sanmi Koyejo, et al. Learning to (learn at test time): Rnns with expressive hidden states. *arXiv preprint arXiv:2407.04620*, 2024.
- <span id="page-11-14"></span>[38] Yutao Sun, Li Dong, Shaohan Huang, Shuming Ma, Yuqing Xia, Jilong Xue, Jianyong Wang, and Furu Wei. Retentive network: A successor to transformer for large language models, 2023. URL <https://arxiv.org/abs/2307.08621>.
- <span id="page-11-1"></span>[39] Richard S. Sutton, Michael Bowling, and Patrick M. Pilarski. The alberta plan for ai research, 2023. URL <https://arxiv.org/abs/2208.11173>.
- <span id="page-11-9"></span>[40] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. *Advances in neural information processing systems*, 30, 2017.
- <span id="page-11-7"></span>[41] Johannes von Oswald, Nino Scherrer, Seijin Kobayashi, Luca Versari, Songlin Yang, Maximilian Schlegel, Kaitlin Maile, Yanick Schimpf, Oliver Sieberling, Alexander Meulemans, et al. Mesanet: Sequence modeling by locally optimal test-time training. *arXiv preprint arXiv:2506.05233*, 2025.
- <span id="page-11-2"></span>[42] Ke Alexander Wang, Jiaxin Shi, and Emily B Fox. Test-time regression: a unifying framework for designing sequence models with associative memory. *arXiv preprint arXiv:2501.12352*, 2025.
- <span id="page-11-3"></span>[43] Geoffrey S Watson. Smooth regression analysis. *Sankhya: The Indian Journal of Statistics, ¯ Series A*, pages 359–372, 1964.
- <span id="page-11-8"></span>[44] Bernard Widrow. Adaptive filters. *Aspects of network and system theory*, 1971.
- <span id="page-11-13"></span>[45] Bernard Widrow and Marcian E Hoff. Adaptive switching circuits. In *Neurocomputing: foundations of research*, pages 123–134. 1988.
- <span id="page-11-15"></span>[46] Songlin Yang, Jan Kautz, and Ali Hatamizadeh. Gated delta networks: Improving mamba2 with delta rule. *arXiv preprint arXiv:2412.06464*, 2024.
- <span id="page-11-4"></span>[47] Songlin Yang, Bailin Wang, Yikang Shen, Rameswar Panda, and Yoon Kim. Gated linear attention transformers with hardware-efficient training. In *International Conference on Machine Learning*, pages 56501–56523. PMLR, 2024.
- <span id="page-11-12"></span>[48] Songlin Yang, Bailin Wang, Yu Zhang, Yikang Shen, and Yoon Kim. Parallelizing linear transformers with the delta rule over sequence length. In *The Thirty-eighth Annual Conference on Neural Information Processing Systems*, 2024.
- <span id="page-11-11"></span>[49] Aston Zhang, Zachary C Lipton, Mu Li, and Alexander J Smola. *Dive into deep learning*. Cambridge University Press, 2023.
- <span id="page-11-6"></span>[50] Tianyuan Zhang, Sai Bi, Yicong Hong, Kai Zhang, Fujun Luan, Songlin Yang, Kalyan Sunkavalli, William T Freeman, and Hao Tan. Test-time training done right. *arXiv preprint arXiv:2505.23884*, 2025.
- <span id="page-11-0"></span>[51] Wenlin Zhang, Xiaopeng Li, Yingyi Zhang, Pengyue Jia, Yichao Wang, Huifeng Guo, Yong Liu, and Xiangyu Zhao. Deep research: A survey of autonomous research agents. *arXiv preprint arXiv:2508.12752*, 2025.
- <span id="page-11-10"></span>[52] Shu Zhong, Mingyu Xu, Tenglong Ao, and Guang Shi. Understanding transformer from the perspective of associative memory, 2025. URL [https://arxiv.org/abs/2505.](https://arxiv.org/abs/2505.19488) [19488](https://arxiv.org/abs/2505.19488).