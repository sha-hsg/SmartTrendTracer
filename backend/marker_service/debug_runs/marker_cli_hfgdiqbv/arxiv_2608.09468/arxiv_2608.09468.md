# MIXFORMER: LINEAR TRANSFORMER WITH MIXTURE OF MEMORY EXPERTS

# Yu Guo

School of Computer Science, Sichuan University Chengdu, China gyguoyugy@gmail.com

# Lei Duan<sup>∗</sup>

School of Artificial Intelligence, Sichuan University Chengdu, China leiduan@scu.edu.cn

# ABSTRACT

State Space Models (SSMs), as a mainstream research direction of linear Transformers, aim to achieve higher efficiency than standard Transformers in long-context modeling. However, existing SSMs suffer from limited input adaptivity and constrained memory capacity, leading to information loss when modeling ultra-long sequences. To address these limitations, we propose MixFormer, a novel linear Transformer that integrates a Mixture-of-Memory-Experts (MoE) mechanism. Specifically, the model maintains differentiated memory states through multiple collaborating memory experts and employs a novel Time-Aware Linear Attention (TALA) mechanism, which leverages learnable exponential decay functions and positional biases to dynamically update memory. This design enables the model to selectively reinforce important historical information while effectively mitigating memory dilution, substantially improving long-range dependency modeling. Experiments on long-sequence text and image generation tasks demonstrate that MixFormer not only achieves significant performance gains but also provides a more sustainable computational backbone for the next generation of web infrastructure.

*K*eywords Transformer · Large Language Model · Linear Attention · State Space Model · Mixture of Experts

# 1 Introduction

Transformer [\[1\]](#page-14-0) has become the foundational architecture for large language models (LLMs) [\[2,](#page-14-1) [3\]](#page-14-2) and multimodal models [\[4](#page-14-3)[–6\]](#page-14-4), having been successfully applied in fields such as Natural Language Processing (NLP) and Computer Vision (CV). The powerful representation learning capability of Transformers stems from the self-attention mechanism, which leverages the softmax function to capture full pairwise token interactions. This results in quadratic time and space complexity (O(L 2 )) with respect to the context length, making it unsuitable for very long-range sequence modeling. In the World Wide Web (WWW), the Transformer architecture has deeply penetrated a wide range of core applications from semantic understanding in search engines and personalized generation in recommendation systems to real-time interactive processing in web browsers. Its self-attention–based parallel computation offers highly efficient sequence modeling capabilities for massive web-scale data.

Recently, efficient Transformer models [\[7](#page-14-5)[–10\]](#page-14-6) have attracted increasing research interest, with a primary focus on reducing the computational cost of the self-attention mechanism. Among these efforts, linear Transformers have emerged as one of the mainstream solutions for building efficient Transformers. The core module of linear Transformers lies in constructing linear attention mechanisms that approximate the behavior of the softmax function through carefully designed kernel functions, thereby reducing the computational cost from O(N<sup>2</sup> ) to O(N), where N is the context length.

In addition, other linear Transformers further extend linear attention into a recursive formulation, allowing each token at a given time step to inherit the computation results from the previous step. Such methods are typically categorized as State Space Models (SSMs) [\[11](#page-14-7)[–15\]](#page-15-0). Unlike the self-attention mechanism, which requires computing an explicit attention score matrix, SSMs do not maintain the correspondence between each query and historical tokens when

<sup>∗</sup>Corresponding author.

handling variable-length contexts. Instead, an SSM preserves a fixed-size intermediate feature map as a global historical memory state matrix, which encodes and compresses information from all previous time steps while discarding their explicit temporal indices. Specifically, during the recursive process at each time step, the SSM's linear attention updates the memory state matrix through additive operations. This update strategy discards the positional indexing of the original queries, making it impossible to retrieve information from specific time steps.

Existing approaches primarily enhance the memory capability of SSM to capture historical information by introducing RNN-style gating mechanisms. These methods employ either fixed decay coefficients (e.g., the constant parameter proposed by [\[16\]](#page-15-1)) or learnable weight matrices (e.g., the work of [\[17\]](#page-15-2)), enabling the model to retain past states to some extent. However, although such methods can marginally increase the capacity of the SSM's memory state, they still suffer from the following inherent limitations: (1) Existing approaches typically update the memory state using fixed coefficients or a limited number of learnable parameters, resulting in insufficient input adaptivity. The model should dynamically decide, at each time step, which information to preserve over the long term and which to gradually decay based on its contextual importance. (2) Most current SSMs employ a single memory state matrix to store historical information. Under ultra-long context inputs, this single-state architecture inherently limits storage capacity, making it difficult to prevent early critical information from being overwritten or diluted by subsequent inputs, thereby leading to irreversible information loss in long-range dependency modeling.

To bridge these gaps, we propose a novel linear Transformer with Mixture of Memory Experts (MixFormer). The proposed architecture is built upon the linear Transformer, supporting both parallel training and recurrent inference modes. Specifically, MixFormer introduces the Mixture-of-Experts (MoE) into state memory modeling for the first time, where multiple memory experts collaboratively construct the final memory state through weighted fusion. Within each expert, we design a novel Time-Aware Linear Attention (TALA) to replace the conventional multi-head attention layer. By integrating exponential decay with learnable parameters, TALA dynamically adjusts the memory update strategy according to the current input, enabling the model to reinforce important historical information while progressively attenuating less relevant content. Furthermore, the multi-expert parallel architecture breaks the capacity limitation of a single memory state by forming a distributed memory storage. Each expert employs a differentiated memory strategy via the TALA mechanism, focusing on distinct temporal patterns such as long-range dependencies or short-term dynamics. Through a content-adaptive expert activation mechanism, MixFormer selectively strengthens the preservation of salient information and suppresses redundant signals. After multi-layer stacking, the model achieves a robust capability for ultra-long context modeling.

We conduct extensive experiments on both image generation (including conditional and unconditional generation) and long-sequence text modeling tasks. The results demonstrate that the proposed MixFormer consistently achieves significant performance gains across all tasks. Furthermore, the effectiveness of MixFormer is validated through an in-depth analysis of its causal masking mechanism and the collaborative division of multiple memory experts. Finally, with the growing demand for web applications that support long-text understanding and multimodal content processing, MixFormer is expected to provide a more sustainable computational backbone for the next generation of web infrastructure. The main contributions are as follows:

- We propose a novel linear Transformer with mixture-of-memory-experts (MixFormer). To the best of our knowledge, this is the first work to incorporate multi-memory-experts into State Space Models (SSMs). Maintaining multiple differentiated memory states in parallel enhances global perception over ultra-long sequences.
- We propose a Time-Aware Linear Attention (TALA) mechanism based on linear attention, which integrates an exponential decay function with learnable pair-wise position biases to significantly enhance the model's capability for long-range dependency modeling.
- Experimental results on both text and image tasks demonstrate that MixFormer achieves strong performance while supporting efficient parallel training and fast autoregressive inference, providing a promising solution for building efficient Transformer models.

# <span id="page-1-0"></span>2 Preliminaries

To better understand the working details of our proposed MixFormer, we provide a detailed review of various forms of dot-product and linear attention.

# 2.1 Dot-product Attention

Figure [3](#page-2-0) (a) illustrates the dot-product attention mechanism in the Vanilla Transformer [\[1\]](#page-14-0). Given the input X, it is mapped into three different semantic space matrices: Q, K, and V , where Q, K, V ∈ R<sup>L</sup>×<sup>d</sup> , L denotes the context

![](_page_2_Picture_2.jpeg)

Figure 1: Linear Attention vs SSMs. (a) is the workflow of the Linear Attention, and (b) is the State Space Models.

<span id="page-2-2"></span>![](_page_2_Picture_4.jpeg)

Figure 2: (a) is the overall architecture of our proposed MixFormer, (b) is the Time-Aware Linear Attention (TALA) layer, and (c) is the Mixture of Memory Experts (MoME) layer.

<span id="page-2-3"></span>length, and d is the hidden state dimension. Next, the attention weight matrix between Q and K is computed using the softmax function. Finally, this matrix is used to compute the weighted sum with V, the final result, as follows:

<span id="page-2-1"></span>
$$Q = XW_q,$$

$$K = XW_k,$$

$$V = XW_v$$

$$Attention(Q, K, V) = Softmax(\frac{QK^T}{\sqrt{d_k}})V,$$
(1)

<span id="page-2-0"></span>![](_page_2_Picture_8.jpeg)

Figure 3: **Dot-product Attention vs Linear Attention.** (a) is the illustration of the Dot-product Attention, and (b) is the Linear Attention.

where Wq, Wk, and W<sup>v</sup> are the trainable matrix, d<sup>k</sup> is hidden layer dimensional number. Generally, we refer to the attention mechanism as Dot-Product Attention or Softmax Attention. Its time and space complexity are both quadratic with respect to the sequence length (L).

# 2.2 Generalization of Attention

According to Equation [\(1\)](#page-2-1), the attention vector for the i-th token is calculated as follows:

<span id="page-3-0"></span>
$$Attention(Q, K, V)_{i} = \sum_{j=1}^{n} \frac{e^{q_{i}^{T} k_{j}}}{\sum_{j=1}^{n} e^{q_{i}^{T} k_{j}}} v_{j},$$
 (2)

where q, k, and v are column vectors. The e q ⊤ <sup>i</sup> k<sup>j</sup> is used as a similarity function between two vectors. Let the similarity function be denoted as sim(q<sup>i</sup> , k<sup>j</sup> ). This generalizes Equation [\(2\)](#page-3-0) to Equation [\(3\)](#page-3-1), following:

<span id="page-3-1"></span>
$$Attention(Q, K, V)_i = \sum_{j=1}^n \frac{sim(q_i, k_j)}{\sum_{j=1}^n sim(q_i, k_j)} v_j,$$
(3)

where sim(q<sup>i</sup> , k<sup>j</sup> ) >= 0, following previous work [\[18,](#page-15-3) [19\]](#page-15-4), the similarity function must ensure the non-negativity of the attention map.

# 2.3 Linear Attention

The dot-product attention uses the softmax function to compute the similarity between Q and K, resulting in a time and space complexity of O(N<sup>2</sup> ). Therefore, reducing the similarity function's time and space complexity is key to achieving an efficient transformer. Figure [3](#page-2-0) (b) illustrates linear attention, which uses a carefully designed similarity function, reducing the time and space complexity from O(N<sup>2</sup> ) to O(N). Many previous works further extend sim(·, ·) to kernel-based methods [\[20–](#page-15-5)[22\]](#page-15-6), which approximate the softmax operation. The formula is as follows:

$$sim(q_i, k_j) = \phi(q_i)^T \phi(k_j), \tag{4}$$

where ϕ(·) can be seen as kernel smoother.

By substituting the kernel similarity function into Equation [\(3\)](#page-3-1), we obtain:

$$Attention(Q, K, V)_i = \sum_{j=1}^n \frac{\phi(q_i)^T \phi(k_j)}{\sum_{j=1}^n \phi(q_i)^T \phi(k_j)} v_j$$
 (5)

Then, by exploiting the associativity of matrix multiplication, the computation order of q, k, and v is altered. It can be simplified to:

$$Attention(Q, K, V)_{i} = \frac{\phi(q_{i})^{T} \sum_{j=1}^{n} (\phi(k_{j})v_{j})}{\phi(q_{i})^{T} \sum_{j=1}^{n} \phi(k_{j})}$$
(6)

The intermediate results are reduced from an L × L matrix to a d × d matrix, and the overall computational complexity becomes O(d <sup>2</sup>L), which scales linearly with the sequence length L.

# 2.4 Autoregressive Generation

In the inference process of Linear Transformers, the prediction of the current token depends solely on the previously generated token sequence and is not influenced by any subsequent tokens. Following the autoregressive generation formulation of language models in [\[18\]](#page-15-3), we reformulate Equation [\(3\)](#page-3-1) into an autoregressive computation paradigm:

$$Attention(Q, K, V)_i = \frac{\phi(q_i)^T S_i}{\phi(q_i)^T Z_i},\tag{7}$$

where S<sup>i</sup> and Z<sup>i</sup> are two newly defined variables, as follows:

$$S_{i} = \sum_{j=1}^{i} (\phi(k_{j})v_{j}), Z_{i} = \sum_{j=1}^{i} \phi(k_{j})$$

$$S_{i} = S_{i-1} + \phi(k_{j})v_{j}^{T}$$

$$Z_{i} = Z_{i-1} + \phi(k_{j}),$$
(8)

where S<sup>0</sup> = 0 and Z<sup>0</sup> = 0. Therefore, the linear attention mechanism enables efficient autoregressive inference with both linear time complexity and constant memory usage.

# 3 Related Work

# 3.1 Linear Transformers

Linear Transformers represent one of the main directions in the development of efficient Transformers. As shown in Figure [1](#page-2-2) (a), many studies aim to approximate dot-product attention through carefully designed kernel function variants, thereby changing the computation order of QKV and reducing the cost complexity from O(L 2 ) to O(L). Such designs enable linear Transformers to achieve performance comparable to that of vanilla Transformers [\[1\]](#page-14-0). Li et al.[\[23\]](#page-15-7) proposed a Taylor approximation-based linear attention mechanism. This method approximates the softmax function using the first-order Taylor expansion of the e x term in the softmax function. Katharopoulos et al. [\[18\]](#page-15-3) proposed replacing kernel methods with non-negative activation functions, achieving up to 4000× faster autoregressive prediction on very long sequences. Shen et al. [\[19\]](#page-15-4) proposed a method that ingeniously applies the softmax function separately to the rows of Q and the columns of K. Peng et al. [\[24\]](#page-15-8) proposed random feature methods that offer a straightforward way of learning with recency bias through an optional gating mechanism to approximate the softmax function. Choromanski et al. [\[25\]](#page-15-9) introduced Performers, which employ a novel fast attention via positive orthogonal random characteristics (FAVOR) approach to go beyond the limitations of softmax-based attention. Han et al. [\[21\]](#page-15-10) proposed a novel focusing function that makes similar vectors more concentrated and dissimilar vectors more dispersed. Meng et al. [\[22\]](#page-15-6) proposed POLAFormer, which improves the focusing function by making its focusing capability learnable, thereby further enhancing model performance.

These efforts have advanced the development of linear Transformers. However, kernel-based approximation methods often yield attention maps that fail to adequately focus on important features. On the other hand, these methods fail to account for the recursive formulation of linear attention, thereby overlooking the update mechanism of the state memory matrix during inference. In contrast, our proposed MixFormer integrates both the parallel and recurrent forms of linear attention, while further enhancing the dynamic temporal awareness of the state memory matrix.

# 3.2 State Space Models

Another line of research reformulates the computation paradigm of linear Transformers into an iterative process, enabling parallel modeling while maintaining autoregressive inference. As shown in Figure [1](#page-2-2) (b), these methods draw inspiration from the autoregressive nature of recurrent neural nets (RNNs) and can be regarded as RNN-style Transformers. Such architectures are typically categorized as State Space Models (SSMs) [\[11,](#page-14-7) [26,](#page-15-11) [27\]](#page-15-12). Existing studies have proposed various algorithmic improvements to SSMs, aiming to optimize the update mechanism of their historical information feature matrices. Han et al. [\[16\]](#page-15-1) proposed the Retentive Network (RetNet), which uses a fixed parameter γ ∈ [0, 1] as a computational factor to update historical information in the SSM. Han et al. [\[16\]](#page-15-1) proposed the Retentive Network (RetNet), which introduces a fixed parameter γ ∈ [0, 1] as a computational factor to update historical information in the SSM. RetNet demonstrates the advantage of SSMs over kernel-based linear Transformers, enabling both Parallel training and sequential inference. Meanwhile, it employs chunkwise Parallelism to model ultra-long sequences, where inputs are processed in Parallel within chunks and sequentially across chunks. Yang et al. [\[17\]](#page-15-2) further extended this idea with Gated Linear Attention (GLA), where a learnable weight matrix (W) is employed to control the update of historical information at each time step. GLA uses an input-dependent forgetting gate and dynamically adjusts the update weights of the sequence. Others of the SSM focus on dynamically updating the memory state at each time step through an exponential decay mechanism. Zhai et al. [\[28\]](#page-15-13) proposed a learned pair-wise positional bias based on exponential decay, enabling SSMs to achieve dynamic temporal awareness. Peng et al. [\[29\]](#page-15-14) introduced RWKV, which leverages token-shifted weighted exponential decay to further optimize the memory modeling mechanism. As the model depth increases, RWKV empowers SSMs with long-range temporal dependency modeling capabilities. Gu and Dao [\[26\]](#page-15-11) proposed the Mamba model, which designs the parameters of the SSM as functions of the input, thereby enabling dynamic control of information flow. Subsequently, Dao and Gu [\[27\]](#page-15-12) introduced Mamba-2, an improved version of Mamba based on the State Space Duality (SSD) framework, which enhances inference efficiency.

However, merely enhancing the representational capacity of the memory state in SSMs is insufficient to address the problem of knowledge forgetting in long sequences. Our proposed MixFormer introduces a Mixture-of-Memory-Experts mechanism, deploying multiple functionally specialized memory experts to capture different types and scales of temporal knowledge. This multi-expert collaborative architecture significantly improves the model's ability to retain information over long-range dependencies, effectively mitigating progressive knowledge decay in long-sequence tasks.

# 4 Methodology

#### 4.1 Problem Definition

As shown in Figure 2 (a), based on the Transformer architecture [1], our proposed MixFormer adopts a similar multiblock stacking structure. Each MixFormer block consists of a Time-Aware Linear Attention (TALA) and a Feed-Forward Network (FFN) layer, each followed by a Group Norm (GN) layer. Given an input sequence  $X=(x_1,\ldots,x_n)$ , where n denotes the context length, MixFormer employs parallel encoding during training and autoregressive generation during inference. The input vectors X are first encoded through an embedding layer into the initial representations  $X^0=(x_1^0,\ldots,x_n^0)\in R^{n\times d}$ , where d denotes the hidden dimension. These representations are then iteratively refined through L stacked MixFormer blocks as follows:

<span id="page-5-2"></span>
$$X^{l} = MixFormer\_Block_{l}(X^{l-1}), \quad l \in [1, L]$$

$$(9)$$

where l denotes the index of the current block layer, and L is the total number of layers in the model. Each block progressively enhances the contextual representations.  $MixFormer\_Block(\cdot)$  denotes the mapping process of the current input within this module.

MixFormer adopts a pre-norm strategy to enhance the training stability during deep stacking, ensuring effective gradient flow across multiple layers. Meanwhile, Group Norm (GN) [30] is introduced to address potential statistical biases arising from chunkwise computation, further improving the model's training stability and convergence performance. The TALA module incorporates time-aware linear attention to effectively capture long-range temporal dependencies among tokens, while supporting both parallel training and recursive inference modes. The notation used throughout the methodology is summarized in Table 1.

### 4.2 Symbol Definition

| Symbol          | Description                               |  |  |  |
|-----------------|-------------------------------------------|--|--|--|
| $\overline{X}$  | Model inputs                              |  |  |  |
| $X^l$           | Input to the <i>l</i> -th MixFormer block |  |  |  |
| Q               | Query projection matrix                   |  |  |  |
| K               | Key projection matrix                     |  |  |  |
| V               | Value projection matrix                   |  |  |  |
| $W_Q, W_K, W_V$ | Learnable parameter matrices              |  |  |  |
| $\omega$        | Exponentially decayed weighting           |  |  |  |
| G               | Learnable pair-wise positional bias       |  |  |  |
| $S_n$           | Intermediate memory state matrix          |  |  |  |
| O               | Model output                              |  |  |  |
| B               | Chunk length                              |  |  |  |

<span id="page-5-0"></span>Table 1: Illustration of mathematical symbols.

#### 4.3 Time-Aware Linear Attention

<span id="page-5-1"></span>![](_page_5_Picture_12.jpeg)

Figure 4: The recurrence of the Time-Aware Linear Attention.

To enhance the memory state perception of long sequences in the state space model, we propose a novel Time-Aware Linear Attention (TALA) layer to replace the standard multi-head self-attention layer. Built upon the principles of linear attention and SSM design, this layer supports both parallel training and sequential inference. The parallel computation structure is illustrated in Figure [2](#page-2-3) (b), while the recursive computation process is shown in Figure [4.](#page-5-1)

In the TALA layer, given an input sequence X, it is first projected into three vector spaces of the same dimension, as follows:

$$Q = XW_Q, K = XW_K, V = XW_V, \tag{10}$$

where W<sup>Q</sup> ∈ Rd×<sup>d</sup> , W<sup>K</sup> ∈ Rd×<sup>d</sup> , and W<sup>V</sup> ∈ Rd×<sup>d</sup> are learnable parameter matrices used to generate the query, key, and value vectors, respectively. d is the hidden dimension.

As shown in Section [2,](#page-1-0) linear attention changes the computation order of QKV and requires the non-negativity of Q and K. Following previous studies [\[31–](#page-15-16)[33\]](#page-15-17), TALA applies a kernel function transformation to ensure the non-negativity of Q and K, which is defined as follows:

<span id="page-6-2"></span>
$$\phi(Q) = e^{\frac{Q}{||Q||}}, \phi(K) = e^{\frac{K}{||K||}}, \tag{11}$$

where || · || denotes the L<sup>2</sup> normalization applied to the row vectors of Q and the column vectors of K.

Meanwhile, we design a hybrid mechanism that integrates positional awareness with dimension-wise adaptability to enhance the temporal awareness of key–value (KV) pairs. This mechanism applies exponentially decayed weighting based on relative positions to emphasize recent information, and employs a learnable parameter matrix to achieve adaptive calibration across feature dimensions. While ensuring the non-negativity of K, it significantly improves the model's ability to capture temporal dependencies in long sequences. The detailed computation process is as follows:

<span id="page-6-0"></span>
$$TALAtt(Q_t, K_t, V_t) = \phi(Q_t) \odot \frac{\sum_{i=1}^t \phi(K_i)(\omega G_i)^{t-i} V_i}{\sum_{i=1}^t \phi(K_i)(\omega G_i)^{t-i}},$$
(12)

where ⊙ denotes element-wise multiplication, ω represents exponentially decayed weighting, and G ∈ RT∗<sup>T</sup> is a learnable pair-wise positional bias. T ALAtt(·) denotes the time-aware linear attention.

In addition, TALA can be extended to a multi-head attention mechanism to enhance its feature extraction capability. By splitting the hidden dimension d into multiple head dimensions dhead and assigning independent decay parameters ω to each attention head, the model can capture temporal dynamics across multiple scales. Based on this, Equation [12](#page-6-0) can be extended to the following multi-head time-aware linear attention formulation:

$$\omega = 1 - e^{-h}, h \in [1, \dots, d/d_{head}]$$

$$head_i = TALAtt(Q_t, K_t, V_t, \omega_i),$$

$$Y = GroupNorm_h(Concat(head_1, \dots, head_h)),$$
(13)

where d is hidden dimension, dhead is head dimension. The GroupNorm is applied to the output of each head.

The Parallel Representation of TALA. During training, MixFormer can leverage parallel matrix operations. The parallel computation architecture of TALA is illustrated in Figure [2](#page-2-3) (b), and its computations are defined as follows:

<span id="page-6-1"></span>
$$Q = \phi(XW_Q), K = \phi(XW_K), V = XW_V,$$

$$TALAtt(Q, K, V) = Q \odot (K^T \odot D)V,$$

$$D = \begin{cases} \omega^{n-m}G_{nm}, n \ge m \\ 0, n < m, \end{cases}$$
(14)

where W<sup>Q</sup> ∈ R<sup>d</sup>×<sup>d</sup> , W<sup>K</sup> ∈ R<sup>d</sup>×<sup>d</sup> , and W<sup>V</sup> ∈ R<sup>d</sup>×<sup>d</sup> are learnable parameter matrices, D is a causal masking matrix, and Gnm is a learnable pair-wise positional bias.

It can be seen that the proposed MoFormer reduces computational complexity by leveraging a linear attention mechanism, while also enabling efficient Parallel training on GPUs.

The Recurrent Representation of TALA. During inference, MixFormer can reformulate TALA as a recurrent computation, enabling autoregressive inference. This allows GPU memory consumption to remain constant, rather than growing with sequence length. The recurrent computation structure of TALA is illustrated in Figure [4,](#page-5-1) at the i-th time step, the computation proceeds through the following process:

$$S_0 = 0,$$

$$S_n = \omega G \odot S_{n-1} + K_n^T V_n,$$

$$O_n = Q_n S_n,$$
(15)

where G is the same as in Equation [\(14\)](#page-6-1). The TALA maintains linear-time complexity during inference.

The Chunkwise Recurrent Representation of TALA. Chunkwise computation, an efficient training paradigm for long sequences, achieves significant acceleration by combining the advantages of parallel and sequential computation [\[16,](#page-15-1) [17\]](#page-15-2). In this approach, the input sequence is divided into consecutive chunks. For each chunk, fully parallelized computation is performed to leverage hardware acceleration, while a recurrent state propagation mechanism is established across chunks to preserve long-range dependencies. Under the linear attention framework, this hybrid computation structure not only enables faster training compared to conventional methods but also exhibits notable I/O-aware benefits through optimized memory access. Specifically, let B denote the chunk length. The computation of the i-th chunk in TALA is defined as follows:

$$R_{i} = (\omega G)^{B} \odot R_{n-1} + K_{[i]}^{T} V_{[i]},$$

$$TALAtt(X_{[i]}) = \underbrace{Q_{[i]} \odot (K_{[i]}^{T} \odot D) V_{[i]}}_{inner-chunk} + \underbrace{Q_{[i]} R_{i-1}}_{cross-chunk},$$

$$(16)$$

where [i] is the i-th chunk.

# 4.4 Mixture of Memory Experts

In State Space Models (SSMs), a single memory state architecture suffers from inherent limitations in long-sequence reasoning: as the sequence length increases, information from early inputs inevitably decays. While increasing the memory state dimension can partially mitigate this issue, it fundamentally fails to address the challenge of information forgetting under long-range dependencies. We propose a Mixture-of-Memory-Experts (MoME) mechanism based on the Mixture-of-Experts (MoE) framework [\[34,](#page-15-18) [35\]](#page-16-0) to overcome this problem. This mechanism deploys multiple functionally heterogeneous memory expert networks, endowing the model with dynamic and differentiated memory capabilities: each expert specializes in memory patterns of varying temporal spans and information importance, and the system adaptively activates the most relevant subset of experts according to the current contextual state. This design not only significantly enhances the model's ability to recall historical information but also achieves long-term retention of critical information through a multi-granularity memory preservation strategy.

The MoME mechanism in TALA extends the memory state by maintaining multiple memory experts. As shown in Figure [2](#page-2-3) (c), at each time step, the system dynamically activates a subset of experts based on the current input and constructs the current memory state by weighted aggregation of their outputs. This mechanism significantly enhances the model's ability to capture temporal features and salient information. The computation is formally defined as follows:

$$Y_{ms} = \sum_{i=1}^{n} E_i M S_i, \tag{17}$$

where Yms denotes the weighted output of multiple memory experts, MS<sup>i</sup> represents the i-th memory expert, E<sup>i</sup> is a router weight vector that determines the contribution of each memory state expert, as follows:

$$E_i = Softmax(K_n V_n W_g),$$

$$\sum_{j=1}^{k_e} E_i^j = 1,$$
(18)

where wg ∈ R 1×k<sup>e</sup> is a learnable parameter matrix, and k<sup>e</sup> is the number of experts. The current time step's K<sup>n</sup> is processed through the kernel transformation defined in Equation [\(11\)](#page-6-2).

Meanwhile, TALA enables the memory update at each time step to dynamically emphasize salient information while suppressing less relevant content. With the stacking of multiple layers and the collaborative effect of the MoME mechanism, the model can effectively retain and utilize information from early tokens even after processing ultra-long sequences.

#### 4.5 Overall Architecture of MixFormer

The proposed MixFormer consists of N stacked MixFormer blocks (Equation (9)). The input to the first block is the embedding of X, comprising both token and positional representations, while each subsequent block receives the output of the previous block as its input. The computation is defined as follows:

$$Y^{l} = TALA(GN(X^{l})) + X^{l},$$

$$X^{l+1} = FFN(GN(Y^{l})) + Y^{l},$$
(19)

where  $GN(\cdot)$  denotes the Group Normalization operation (GN). MixFormer adopts a structure similar to that of mainstream Transformers and employs a Feed-Forward Network (FFN) to enable the modeling of complex nonlinear transformations. The computation is defined as follows:

$$FFN(X) = max(0, XW_1)W_2, \tag{20}$$

where  $W_1$  and  $W_2$  are learnable weight matrices.

#### 4.6 Complexity Analysis

To verify the linear-time complexity of MixFormer, we conduct a detailed complexity analysis as follows. Let N denote the sequence length (context length), d the hidden state dimension, d' the expansion dimension of the feed-forward network (FFN), where d'>d, and k the number of memory experts. The total computational cost of MixFormer comprises four main components: projections (Proj), the time-aware linear attention (TALA), mixture-of-memory experts (MoME), and the feed-forward network (FFN). As shown in Equation 21, the Projection cost (Query, Key, Value, and Output projections) is  $4Nd^2$ , the time-aware linear attention cost is  $Nd^2$ , the MoME cost is Nk, and the FFN cost is 2dd'. Under the long-context setting  $(N\gg d)$ , the total computational complexity of MixFormer converges to O(N).

<span id="page-8-0"></span>
$$\underbrace{4Nd^2}_{Proj} + \underbrace{Nd^2}_{TALA} + \underbrace{Nk}_{MoME} + \underbrace{2dd'}_{FFN} \tag{21}$$

### 4.7 Differences from Previous Methods

To compare MixFormer with other efficient Linear Transformers, we conduct a comparative analysis across four key dimensions, as shown in Table 2. For training parallelism, MixFormer, like the standard Transformer, supports fully parallelized training. In contrast, Recurrent Neural Networks (RNNs) and RWKV [29] suffer from sequential training bottlenecks. MixFormer achieves performance comparable to that of standard Transformers, while significantly outperforming Linear Transformers—whose kernel approximations often lead to degraded attention focus—as well as traditional RNN-based models. For inference efficiency, MixFormer and linear Transformers both achieve O(1)inference time per token, significantly outperforming the  $O(N^2)$  complexity of standard Transformers. For memory consumption, MixFormer maintains linear O(N) memory usage with respect to sequence length, in contrast to the quadratic memory growth of standard Transformers. MixFormer demonstrates significant advantages in its memory state mechanism. Unlike conventional Transformers that rely on explicit attention score matrices and lack an inherent memory design, existing linear Transformers and SSMs typically maintain a single static memory state, which limits their ability to model complex dependencies over long sequences. In contrast, MixFormer uses a mixture-of-expert memory mechanism, where a dynamic routing strategy assigns input features to multiple specialized memory modules, enabling the model to adaptively activate historical information across different dimensions. This multi-granularity collaborative memory architecture allows MixFormer to capture fine-grained temporal patterns and retain information more effectively in long-sequence tasks. Finally, compared to S4 [11] and RetNet [16], MixFormer achieves stronger overall performance while preserving both training Parallelism and linear time and memory complexity. In summary, the proposed MixFormer effectively integrates the advantages of existing efficient Transformers and achieves significant performance improvements.

### 5 Experiments

# 5.1 Experimental Setups

The main hyperparameter settings of MixFormer are summarized in Table 4. In this experiment, MixFormer was configured with two parameter variants: A0.3B-2B and A1B-7B. The A0.3B-2B model uses a hidden dimension of

<span id="page-9-0"></span>Table 2: Comparison between MixFormer and other efficient linear Transformer models from multiple perspectives. Including training parallelism, inference cost, memory consumption on long sequences, and the number of memory states.

| Architectures      | Training Parallelization | Inference Cost | Long-Sequence Memory Complexity | Memory State |
|--------------------|--------------------------|----------------|---------------------------------|--------------|
| Transformer        | Y                        | O(N)           | O(N2<br>)                       | N/a          |
| Linear Transformer | Y                        | O(1)           | O(N)                            | Singe        |
| Recurrent NN       | N                        | O(1)           | O(N)                            | Singe        |
| RWKV               | N                        | O(1)           | O(N)                            | Singe        |
| S4                 | Y                        | O(1)           | O(NlogN)                        | Singe        |
| RetNet             | Y                        | O(1)           | O(N)                            | Singe        |
| MixFormer (Ours)   | Y                        | O(1)           | O(N)                            | Multiple     |

<span id="page-9-2"></span>Table 3: Comparison of MixFormer with other efficient Transformers on the LRA benchmark (%). The best results are highlighted in bold, and the second-best results are underlined. The results of other models follow [\[36\]](#page-16-1).

| Model            | ListOps | Text  | Retrieval | Image | Pathfinder | Avg   |
|------------------|---------|-------|-----------|-------|------------|-------|
| Transformer      | 36.37   | 64.27 | 57.46     | 42.44 | 71.40      | 54.39 |
| Local Attention  | 15.82   | 52.98 | 53.39     | 41.46 | 66.63      | 46.06 |
| Sparse Trans.    | 17.07   | 63.58 | 59.59     | 44.24 | 71.71      | 51.24 |
| Longformer       | 35.63   | 62.85 | 56.89     | 42.22 | 69.71      | 53.46 |
| Linformer        | 35.70   | 53.94 | 52.27     | 38.56 | 76.34      | 51.36 |
| Reformer         | 37.27   | 56.10 | 53.40     | 38.07 | 68.50      | 50.67 |
| Sinkhorn Trans.  | 33.67   | 61.20 | 53.83     | 41.23 | 67.45      | 51.39 |
| Synthesizer      | 36.99   | 61.68 | 54.67     | 41.61 | 69.45      | 52.88 |
| BigBird          | 36.05   | 64.02 | 59.29     | 40.83 | 74.87      | 55.01 |
| Linear Trans.    | 16.13   | 65.90 | 53.09     | 42.34 | 75.30      | 50.55 |
| Performer        | 18.01   | 65.40 | 53.82     | 42.77 | 77.05      | 51.41 |
| MixFormer (Ours) | 37.35   | 66.56 | 60.50     | 42.65 | 76.55      | 56.72 |

1024 for the Q/K/V/O projections, a feed-forward network dimension of 896, 8 attention heads, 64 memory state experts, and 12 stacked MixFormer blocks. For training, we adopt a learning rate of 1 × 10<sup>−</sup><sup>4</sup> with the Adam optimizer, and train the model on a corpus containing 15 billion tokens. The total number of parameters is 2B, of which 0.3B are active parameters. The A1B-7B model uses a hidden dimension of 2048 for the Q/K/V/O projections, a feed-forward network dimension of 1024, 16 attention heads, 64 memory state experts, and 16 stacked MixFormer blocks. For training, we adopt a learning rate of 1 × 10<sup>−</sup><sup>5</sup> with the Adam optimizer, and train the model on a corpus containing 15 billion tokens. The total number of parameters is 7B, of which 1B is an active parameter. All experiments are conducted on four NVIDIA RTX 4090 GPUs.

<span id="page-9-1"></span>Table 4: Experimental Setups.

| HyperParameters       | A0.3B-2B | A1B-7B |
|-----------------------|----------|--------|
| Hidden Dimension      | 1024     | 2048   |
| FFN Dimension         | 896      | 1024   |
| Num of Heads          | 8        | 16     |
| Num of Layers         | 12       | 16     |
| Num of Memory Experts | 64       | 64     |
| LR                    | 1e-4     | 1e-5   |
| Training Tokens       | 15B      | 30B    |

# 5.2 Long Context Ability

To evaluate the effectiveness of MixFormer in long-context scenarios, we conduct experiments on the Long-Range Arena (LRA) benchmark [\[36\]](#page-16-1), a standard suite for long-sequence modeling. The Long Range Arena (LRA) benchmark systematically integrates five core tasks characterized by pronounced long-sequence dependencies. In the mathematical expression parsing task ListOps [\[37\]](#page-16-2), models are required to parse deeply nested operator structures, posing a significant challenge to their hierarchical reasoning ability. The text classification task based on IMDb movie reviews [\[38\]](#page-16-3) demands that models extract key sentiment features from lengthy reviews, testing their capacity for semantic filtering under noisy conditions. The AAN document retrieval task [\[39\]](#page-16-4) evaluates how effectively models capture semantic associations across long academic documents through citation-based matching. The Pathfinder task [\[40\]](#page-16-5), a synthetic visual challenge, requires the establishment of long-range spatial dependencies across pixel sequences. Finally, the CIFAR-10 image classification task [\[41\]](#page-16-6), which flattens images into sequences, innovatively examines a model's ability to preserve visual features in the absence of two-dimensional structural priors.

The experimental results, as shown in Table [3,](#page-9-2) demonstrate that MixFormer outperforms all compared efficient Transformer models in terms of overall average accuracy. Specifically, it achieves the best performance on ListOps, text classification, and document retrieval tasks, and ranks second on CIFAR-10 and Pathfinder. This can be attributed to MixFormer's use of linear attention as the backbone, which enables longer sequence outputs under limited memory consumption, thereby enhancing contextual representation learning. In addition, the MoME mechanism significantly broadens the model's perceptual scope, enabling it to continuously focus on critical information in long-context scenarios. By coordinating multiple specialized experts, this mechanism ensures that important content is effectively preserved and reinforced throughout long-sequence propagation, thereby enhancing the model's ability to capture long-range dependencies. Overall, MixFormer exhibits strong capability in modeling long-range dependencies across diverse domains.

# 5.3 Image Generation

To evaluate the effectiveness of MixFormer in image generation tasks, we conduct both conditional and unconditional generation experiments on the MNIST dataset [\[42\]](#page-16-7). Figure [5](#page-11-0) (top row) is the result of unconditional generation. While standard Transformers can be directly applied to image generation, they suffer from substantial memory overhead when modeling long sequences in pixel-by-pixel generation. In contrast, MixFormer not only significantly reduces memory consumption and generation time but also produces high-quality samples with sharp boundaries and minimal noise. Figure [5](#page-11-0) (bottom row) presents an image completion task, where the input consists of occluded images and MixFormer is responsible for generating the complete outputs. We observe that MixFormer demonstrates strong long-range dependency modeling capabilities, accurately replicating the stroke style and width characteristics of the original images. These advantages highlight the potential of MixFormer as an efficient and effective solution for long-sequence image generation tasks. In summary, the proposed MixFormer performs remarkably well in both unconditional and conditional image generation tasks, demonstrating its effectiveness in modeling long-range pixel dependencies.

# 5.4 CIFAR 10

To evaluate the performance of MixFormer on multi-channel image tasks, we conduct an image completion experiment on the CIFAR-10 [\[41\]](#page-16-6). Compared with single-channel inputs, the serialized representation of multi-channel images results in substantially longer sequences, imposing greater demands on the model's ability to capture long-range dependencies. As shown in Figure [6,](#page-12-0) when 50% of image pixels are randomly masked, MixFormer successfully reconstructs visually coherent images with well-preserved structural integrity, clear boundaries, and minimal noise—significantly outperforming baseline models in texture continuity and detail preservation. Within the MoME architecture, different memory experts specialize in capturing local texture features and global structural information. When parts of an image are occluded, the model adaptively activates the corresponding structural experts to recover the overall layout while engaging texture experts to refine fine-grained details. In summary, the synergistic interaction between the MoME and the TALA mechanisms endows MixFormer with distinct advantages in multi-channel image completion tasks.

# 5.5 Interpretability Analysis

We conduct an interpretability analysis by visualizing intermediate outputs between the standard dot-product attention and reflection attention. Figure [7](#page-12-1) (a) shows the intermediate result of the standard softmax attention: the matrix QK<sup>T</sup> after softmax normalization. Softmax attention not only strengthens the connections between important tokens but also suppresses irrelevant ones. Moreover, it preserves full pairwise interactions among all tokens, ensuring comprehensive global information exchange. Any given token can retrieve interaction information with all other tokens through the attention map. In contrast, Figure [7](#page-12-1) (b) presents the K<sup>T</sup> V output in the reflection attention, which forms a fixed-size d × d matrix known as the State Space Model (SSM). This matrix serves as a compressed global memory of historical information. Due to its fixed dimensionality, the SSM does not retain explicit step-wise positional indices. At each time step, the token updates the SSM by accumulating information from all previous steps. At each time step, token representations are selectively written into the SSM based on the current input, and the output is generated using the updated global memory.

![](_page_11_Figure_2.jpeg)

<span id="page-11-0"></span>Figure 5: Experimental results on image generation tasks. The top row is the result of unconditional generation, while the bottom row is conditional generation. (a) is the occluded input image, (b) is the output generated by MixFormer, and (c) is the corresponding ground-truth image.

In other words, softmax attention produces explicit token-pair attention scores, while linear attention constructs an implicit global attention matrix. During autoregressive inference, MixFormer enforces causal masking through the matrix D (Equation [14\)](#page-6-1). As illustrated in Figure [8,](#page-13-0) the visualization of the D matrix clearly reveals the temporal evolution of memory attention values—an effect that arises from our exponential decay mechanism and learnable pairwise interaction biases. In summary, the causal mask analysis demonstrates that MixFormer effectively balances strict causal constraints with global information flow. Meanwhile, the multi-expert case study reveals a natural functional differentiation among memory experts—where some focus on short-term feature extraction while others specialize in long-term dependency preservation—offering a mechanistic explanation for MixFormer's superior performance on long-sequence tasks.

# 5.6 Mixture-of-Memory-Experts Analysis

To examine the activation behavior of the MoME mechanism, we conduct a visualization analysis. As shown in Figure [9,](#page-13-1) when the current token is "Paris" and the context is "The Eiffel Tower is located in the city of", the MoME mechanism exhibits significantly stronger expert activations for the tokens "Eiffel", "Tower", and "city". Through the collaboration of multiple memory experts, the model effectively identifies the strong semantic association between the landmark entity "Eiffel Tower" and "Paris". Meanwhile, the expert system captures the spatial hierarchical relationship between "city" and the target location "Paris". In particular, the long-term memory experts successfully preserve information about distant core entities, ensuring accurate contextual recall during generation. This observation confirms that the MoME mechanism achieves dynamic selection and persistent retention of crucial historical information through functional specialization among experts.

![](_page_12_Picture_2.jpeg)

Figure 6: Experimental results on CIFAR 10. (a) is the occluded input image, and (b) is the output generated by MixFormer.

<span id="page-12-0"></span>![](_page_12_Figure_4.jpeg)

<span id="page-12-1"></span>Figure 7: Visualized intermediate outputs of (a) standard dot-product attention and (b) reflection attention.

![](_page_13_Figure_2.jpeg)

<span id="page-13-0"></span>Figure 8: Visualization of the causal mask used by MixFormer.

![](_page_13_Figure_4.jpeg)

<span id="page-13-1"></span>Figure 9: Visualization of memory-expert activations.

# 6 Conclusion

In this work, we proposed MixFormer, a novel linear Transformer architecture incorporating the MoE to address the limitations of existing SSMs in ultra-long sequence modeling. By maintaining multiple differentiated memory states in parallel and introducing the Time-Aware Linear Attention (TALA) mechanism, MixFormer dynamically updates memory with input-adaptive exponential decay and learnable positional biases. This enables the model to selectively retain important historical information while mitigating memory dilution, effectively enhancing its capacity for longrange dependency modeling. Extensive experiments on both long-sequence text and image generation tasks demonstrate that MixFormer consistently outperforms prior approaches, achieving robust performance under both parallel training and recurrent inference modes. Finally, MixFormer provides a promising solution for efficient Transformer design with strong modeling capabilities for ultra-long contexts. In future work, we plan to improve MixFormer in two directions. First, we aim to scale up the model parameters to further enhance its performance. Second, we will extend the application of MixFormer to a broader range of tasks and domains.

# References

- <span id="page-14-0"></span>[1] Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. *Proceedings of the 2017 Advances in Neural Information Processing Systems, NeuraIPS*, pages 5998–6008, 2017.
- <span id="page-14-1"></span>[2] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothee Lacroix, ´ Baptiste Roziere, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: open and efficient foundation language ` models. *arXiv preprint arXiv:2302.13971*, 2023.
- <span id="page-14-2"></span>[3] Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. Llama 2: open foundation and fine-tuned chat models. *arXiv preprint arXiv:2307.09288*, 2023.
- <span id="page-14-3"></span>[4] Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. *arXiv e-prints*, pages arXiv–2407, 2024.
- [5] Matt Deitke, Christopher Clark, Sangho Lee, Rohun Tripathi, Yue Yang, Jae Sung Park, Mohammadreza Salehi, Niklas Muennighoff, Kyle Lo, Luca Soldaini, et al. Molmo and pixmo: open weights and open data for state-of-the-art multimodal models. *arXiv e-prints*, pages arXiv–2409, 2024.
- <span id="page-14-4"></span>[6] Wenliang Dai, Nayeon Lee, Boxin Wang, Zhuolin Yang, Zihan Liu, Jon Barker, Tuomas Rintamaki, Mohammad Shoeybi, Bryan Catanzaro, and Wei Ping. Nvlm: open frontier-class multimodal llms. *arXiv preprint arXiv:2409.11402*, 2024.
- <span id="page-14-5"></span>[7] Yi Tay, Mostafa Dehghani, Dara Bahri, and Donald Metzler. Efficient transformers: a survey. *ACM Computing Survey*, 55(6), 2022.
- [8] Bohan Zhuang, Jing Liu, Zizheng Pan, Haoyu He, Yuetian Weng, and Chunhua Shen. A survey on efficient training of transformers. In *Proceedings of the 2023 International Joint Conference on Artificial Intelligence, IJCAI*, pages 6823–6831, 2023.
- [9] Lorenzo Papa, Paolo Russo, Irene Amerini, and Luping Zhou. A survey on efficient vision transformers: algorithms, techniques, and performance benchmarking. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 46(12):7682–7700, 2024.
- <span id="page-14-6"></span>[10] Kai Han, Yunhe Wang, Hanting Chen, Xinghao Chen, Jianyuan Guo, Zhenhua Liu, Yehui Tang, An Xiao, Chunjing Xu, Yixing Xu, et al. A survey on vision transformer. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 45(1):87–110, 2022.
- <span id="page-14-7"></span>[11] Albert Gu, Karan Goel, and Christopher Re. Efficiently modeling long sequences with structured state spaces. In *Proceedings of the 2022 International Conference on Learning Representations, ICLR*, 2022.
- [12] Ankit Gupta, Albert Gu, and Jonathan Berant. Diagonal state spaces are as effective as structured state spaces. *Proceedings of the 2022 Advances in Neural Information Processing Systems, NeuraIPS*, 35:22982–22994, 2022.
- [13] Albert Gu, Isys Johnson, Karan Goel, Khaled Saab, Tri Dao, Atri Rudra, and Christopher Re. Combining recurrent, ´ convolutional, and continuous-time models with linear state space layers. *Proceedings of the 2021 Advances in Neural Information Processing Systems, NeuraIPS*, 34:572–585, 2021.
- [14] Ramin Hasani, Mathias Lechner, Tsun-Hsuan Wang, Makram Chahine, Alexander Amini, and Daniela Rus. Liquid structural state-space models. In *Proceedings of the 2023 International Conference on Learning Representations, ICLR*, 2023.

- <span id="page-15-0"></span>[15] Jimmy TH Smith, Andrew Warrington, and Scott W Linderman. Simplified state space layers for sequence modeling. In *Proceedings of the 2023 International Conference on Learning Representations, ICLR*, 2023.
- <span id="page-15-1"></span>[16] Yutao Sun, Li Dong, Shaohan Huang, Shuming Ma, Yuqing Xia, Jilong Xue, Jianyong Wang, and Furu Wei. Retentive network: a successor to transformer for large language models. *arXiv preprint arXiv:2307.08621*, 2023.
- <span id="page-15-2"></span>[17] Songlin Yang, Bailin Wang, Yikang Shen, Rameswar Panda, and Yoon Kim. Gated linear attention transformers with hardware-efficient training. In *Proceedings of the 2024 International Conference on Machine Learning, ICML*, pages 56501–56523, 2024.
- <span id="page-15-3"></span>[18] Angelos Katharopoulos, Apoorv Vyas, Nikolaos Pappas, and Franc¸ois Fleuret. Transformers are rnns: fast autoregressive transformers with linear attention. In *Proceedings of the 2020 International Conference on Machine Learning, ICML*, pages 5156–5165, 2020.
- <span id="page-15-4"></span>[19] Zhuoran Shen, Mingyuan Zhang, Haiyu Zhao, Shuai Yi, and Hongsheng Li. Efficient attention: attention with linear complexities. In *Proceedings of the 2021 International Conference on Computer Vision, ICCV*, pages 3531–3539, 2021.
- <span id="page-15-5"></span>[20] Imanol Schlag, Kazuki Irie, and Jurgen Schmidhuber. Linear transformers are secretly fast weight programmers. ¨ In *Proceedings of the 2021 International Conference on Machine Learning, ICML*, pages 9355–9366, 2021.
- <span id="page-15-10"></span>[21] Dongchen Han, Xuran Pan, Yizeng Han, Shiji Song, and Gao Huang. Flatten transformer: vision transformer using focused linear attention. In *Proceedings of the 2023 International Conference on Computer Vision, ICCV*, pages 5961–5971, 2023.
- <span id="page-15-6"></span>[22] Weikang Meng, Yadan Luo, Xin Li, Dongmei Jiang, and Zheng Zhang. Polaformer: polarity-aware linear attention for vision transformers. In *Proceedings of the 2025 International Conference on Learning Representations, ICLR*, 2025.
- <span id="page-15-7"></span>[23] R Li, J Su, C Duan, and S Zheng. Linear attention mechanism: an efficient attention for semantic segmentation. *arXiv preprint arXiv:2007.14902*, 2020.
- <span id="page-15-8"></span>[24] H Peng, N Pappas, D Yogatama, R Schwartz, N Smith, and L Kong. Random feature attention. In *Proceedings of the 2021 International Conference on Learning Representations, ICLR*, 2021.
- <span id="page-15-9"></span>[25] Krzysztof Marcin Choromanski, Valerii Likhosherstov, David Dohan, Xingyou Song, Andreea Gane, Tamas Sarlos, Peter Hawkins, Jared Quincy Davis, Afroz Mohiuddin, Lukasz Kaiser, et al. Rethinking attention with performers. In *Proceedings of the 2021 International Conference on Learning Representations, ICLR*, 2021.
- <span id="page-15-11"></span>[26] Albert Gu and Tri Dao. Mamba: linear-time sequence modeling with selective state spaces. In *Proceedings of the 2024 International First Conference on Language Modeling, CoLM*, 2024.
- <span id="page-15-12"></span>[27] Tri Dao and Albert Gu. Transformers are ssms: generalized models and efficient algorithms through structured state space duality. In *Proceedings of the 2024 International Conference on Machine Learning, ICML*, pages 10041–10071, 2024.
- <span id="page-15-13"></span>[28] Shuangfei Zhai, Walter Talbott, Nitish Srivastava, Chen Huang, Hanlin Goh, Ruixiang Zhang, and Josh Susskind. An attention free transformer. *arXiv preprint arXiv:2105.14103*, 2021.
- <span id="page-15-14"></span>[29] Bo Peng, Eric Alcaide, Quentin Anthony, Alon Albalak, Samuel Arcadinho, Stella Biderman, Huanqi Cao, Xin Cheng, Michael Chung, Leon Derczynski, et al. Rwkv: Reinventing rnns for the transformer era. In *Findings of the Association for Computational Linguistics: EMNLP 2023*, pages 14048–14077, 2023.
- <span id="page-15-15"></span>[30] Yuxin Wu and Kaiming He. Group normalization. In *Proceedings of the European conference on computer vision (ECCV)*, pages 3–19, 2018.
- <span id="page-15-16"></span>[31] Han Cai, Chuang Gan, and Song Han. Efficientvit: enhanced linear attention for high-resolution low-computation visual recognition. *arXiv preprint arXiv:2205.14756*, 3(1), 2022.
- [32] Jiachen Lu, Jinghan Yao, Junge Zhang, Xiatian Zhu, Hang Xu, Weiguo Gao, Chunjing Xu, Tao Xiang, and Li Zhang. Soft: softmax-free transformer with linear complexity. *Proceedings of the 2021 Advances in Neural Information Processing Systems, NeuraIPS*, 34:21297–21309, 2021.
- <span id="page-15-17"></span>[33] Yunyang Xiong, Zhanpeng Zeng, Rudrasis Chakraborty, Mingxing Tan, Glenn Fung, Yin Li, and Vikas Singh. Nystromformer: a nystr ¨ om-based algorithm for approximating self-attention. In ¨ *Proceedings of the 2021 Conference on Artificial Intelligence, AAAI*, number 16, pages 14138–14148, 2021.
- <span id="page-15-18"></span>[34] Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean. Outrageously large neural networks: the sparsely-gated mixture-of-experts layer. In *Proceedings of the 2017 International Conference on Learning Representations, ICLR*, 2017.

- <span id="page-16-0"></span>[35] Shashi Narayan, Shay B Cohen, and Mirella Lapata. Don't give me the details, just the summary! topic-aware convolutional neural networks for extreme summarization. In *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing, EMNLP*, pages 1797–1807, 2018.
- <span id="page-16-1"></span>[36] Yi Tay, Mostafa Dehghani, Samira Abnar, Yikang Shen, Dara Bahri, Philip Pham, Jinfeng Rao, Liu Yang, Sebastian Ruder, and Donald Metzler. Long range arena: a benchmark for efficient transformers. In *Proceedings of the 2020 International Conference on Learning Representations, ICLR*, 2020.
- <span id="page-16-2"></span>[37] Nikita Nangia and Samuel Bowman. Listops: a diagnostic dataset for latent tree learning. In *Proceedings of the 2018 Annual Meeting of the Association for Computational Linguistics: Human Language Technologies, ACL*, pages 92–99, 2018.
- <span id="page-16-3"></span>[38] Andrew Maas, Raymond E Daly, Peter T Pham, Dan Huang, Andrew Y Ng, and Christopher Potts. Learning word vectors for sentiment analysis. In *Proceedings of the 2011 Annual Meeting of the Association for Computational Linguistics: Human Language Technologies, ACL*, pages 142–150, 2011.
- <span id="page-16-4"></span>[39] Dragomir R Radev, Pradeep Muthukrishnan, Vahed Qazvinian, and Amjad Abu-Jbara. The acl anthology network corpus. *Language Resources and Evaluation*, 47(4):919–944, 2013.
- <span id="page-16-5"></span>[40] Drew Linsley, Junkyung Kim, Vijay Veerabadran, Charles Windolf, and Thomas Serre. Learning long-range spatial dependencies with horizontal gated recurrent units. *Proceedings of the 2018 Advances in Neural Information Processing Systems, NeuraIPS*, 31, 2018.
- <span id="page-16-6"></span>[41] Alex Krizhevsky, Geoffrey Hinton, et al. Learning multiple layers of features from tiny images. 2009.
- <span id="page-16-7"></span>[42] Gregory Cohen, Saeed Afshar, Jonathan Tapson, and Andre Van Schaik. Emnist: Extending mnist to handwritten letters. In *2017 international joint conference on neural networks (IJCNN)*, pages 2921–2926. IEEE, 2017.