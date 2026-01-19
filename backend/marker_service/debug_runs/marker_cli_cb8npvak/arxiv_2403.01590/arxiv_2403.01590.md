# <span id="page-0-1"></span>The Hidden Attention of Mamba Models

Ameen Ali ∗ , Itamar Zimerman ∗ , and Lior Wolf

School of Computer Science, Tel Aviv University

Abstract. The Mamba layer offers an efficient selective state space model (SSM) that is highly effective in modeling multiple domains, including NLP, long-range sequence processing, and computer vision. Selective SSMs are viewed as dual models, in which one trains in parallel on the entire sequence via an IO-aware parallel scan, and deploys in an autoregressive manner. We add a third view and show that such models can be viewed as attention-driven models. This new perspective enables us to empirically and theoretically compare the underlying mechanisms to that of the self-attention layers in transformers and allows us to peer inside the inner workings of the Mamba model with explainability methods. Our code is publicly available[1](#page-0-0).

## 1 Introduction

Recently, Selective State Space Layers [\[30\]](#page-15-0), also known as Mamba models, have shown remarkable performance in diverse applications including language modeling [\[5,](#page-14-0)[30,](#page-15-0)[58,](#page-17-0)[73\]](#page-18-0), image processing [\[44,](#page-16-0)[82\]](#page-18-1), video processing [\[80\]](#page-18-2), medical imaging [\[28,](#page-15-1)[43,](#page-16-1)[48,](#page-16-2)[62,](#page-17-1)[75,](#page-18-3)[76,](#page-18-4)[78\]](#page-18-5), tabular data [\[2\]](#page-14-1), point-cloud analysis [\[42\]](#page-16-3), graphs [\[10,](#page-14-2) [71\]](#page-18-6), N-dimensional sequence modeling [\[41\]](#page-16-4) and more. Characterized by their linear complexity in sequence length during training and fast RNN-like computation during inference (left and middle panels of Fig. [1\)](#page-1-0), Mamba models offer a 5x increase in the throughput of Transformers for auto-regressive generation and the ability to efficiently handle long-range dependencies.

Despite their growing success, the information-flow dynamics between tokens in Mamba models and the way they learn remain largely unexplored. Critical questions about their learning mechanisms, particularly how they capture dependencies and their resemblance to other established layers, such as RNNs, CNNs, or attention mechanisms, remain unanswered. Additionally, the lack of interoperability methods for these models may pose a significant hurdle to debugging them and may also reduce their applicability in socially sensitive domains in which explainability is required.

Motivated by these gaps, our research aims to provide insights into the dynamics of Mamba models and develop methodologies for their interpretation. While the traditional views of state-space models are through the lens of convolutional or recurrent layers [\[32\]](#page-15-2), we show that selective state-space layers are a form

<sup>\*</sup> These authors contributed equally to this work.

<span id="page-0-0"></span><sup>1</sup> <https://github.com/AmeenAli/HiddenMambaAttn>

<span id="page-1-1"></span><span id="page-1-0"></span>![](_page_1_Figure_1.jpeg)

Fig. 1: Three Perspectives of the Selective State-Space Layer:(Left) Selective State-Space Models (SSMs) can be efficiently computed with linear complexity using parallel scans, allowing for effective parallelization on modern hardware, such as GPUs. (Middle) Similar to SSMs, the selective state-space layer can be computed via a time-variant recurrent rule. (Right) A new view of the selective SSM layer, showing that it uses attention similarly to transformers (see Eq. [11\)](#page-4-0). Our view enables the generation of attention maps, offering valuable applications in areas such as XAI.

of attention models. This is achieved through a novel reformulation of Mamba computation using a data-control linear operator, unveiling hidden attention matrices within the Mamba layer. This enables us to employ well-established interpretability and explainability techniques, commonly used in transformer realms, to devise the first set of tools for interpreting Mamba models. Furthermore, our analysis of implicit attention matrices offers a direct framework for comparing the properties and inner representations of transformers [\[70\]](#page-18-7) and Mamba models.

Our main contributions encompass the following main aspects: (i) We shed light on the fundamental nature of Mamba models, by showing that they rely on implicit attention, which is implemented by a unique data-control linear operator, as illustrated in Fig. [1](#page-1-0) (right). (ii) Our analysis reveals that Mamba models give rise to three orders of magnitude more attention matrices than transformers. (iii) We provide a set of explainability and interpretability tools based on these hidden attention matrices. (iv) For comparable model sizes, Mamba model-based attention shows comparable explainability metrics results to that of transformers. (v) We present a theoretical analysis of the evolution of attention capabilities in state-space models and their expressiveness, offering a deeper understanding of the factors that contribute to Mamba's effectiveness.

## 2 Background

Transformers The Transformer architecture [\[70\]](#page-18-7) is the dominant architecture in the recent NLP and Computer Vision literature. It relies on self-attention to capture dependencies between different tokens. Self-attention allows these models to dynamically focus on different parts of the input sequence, calculating <span id="page-2-4"></span>the relevance of each part to others. It can be computed as follows:

<span id="page-2-3"></span>
$$Self - Attention(Q, K, V) = \alpha V, \quad \alpha = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)$$
(1)

where  $Q, K$ , and V represent queries, keys, and values, respectively, and  $d_k$  is the dimension of the keys. Additionally, the Transformer utilizes  $H$  attention heads to process information in parallel, allowing the model to capture various dependencies. The attention matrix  $\alpha$  enables the models to weigh the importance of tokens based on their contribution to the context, and they can also used for interpretability [8], explainability [15], and improved classification [16, 69].

**State-Space Layers** State-Space Layers were first introduced in [32] and have seen significant improvements through the seminal work in  $[31]$ . These layers have demonstrated promising results across several domains, including NLP  $[24, 51]$ , audio generation  $[26]$ , image processing  $[9, 54, 79]$ , long video understanding  $[72]$ , RL  $[18, 45]$ , speech recognition  $[63]$ , and more. Given one channel of the input sequence  $x := (x_1, \dots, x_L)$  such that  $x_i \in \mathbb{R}$ , these layers can be implemented using either recurrence or convolution. The recurrent formulation, which relies on the recurrent state  $h_t \in \mathbb{R}^N$  where N is the state size, is defined as follows: given the discretization functions  $f_A, f_B$ , and parameters A, B, C and  $\Delta$ , the recurrent rule for the SSM is:

<span id="page-2-2"></span><span id="page-2-0"></span>
$$A = f_A(A, \Delta), \quad B = f_B(A, B, \Delta), \quad h_t = Ah_{t-1} + Bx_t, \quad y_t = Ch_t \quad (2)$$

This recurrent rule can be expanded as:

$$h_t = \bar{A}^t \bar{B}x_0 + \bar{A}^{t-1} \bar{B}x_1 + \dots + \bar{B}x_t, \quad y_t = C\bar{A}^t \bar{B}x_0 + C\bar{A}^{t-1} \bar{B}x_1 + \dots + C\bar{B}x_t \tag{3}$$

Since the recurrence is linear, Eq.  $3$  can also be expressed as a convolution, via a convolution kernel  $K := (k_1, \cdots, k_L)$ , where  $k_i = C\bar{A}^{i-1}\bar{B}$ , thus allowing sub-quadratic complexity in sequence length. The equivalence between the recurrence and the convolution provides a versatile framework that enables parallel and efficient training with sub-quadratic complexity with the convolution view, alongside a faster recurrent view, facilitating the acceleration of autoregressive generation by decoupling step complexity from sequence length. As the layer defined as a map from  $\mathbb{R}^{\mathbb{L}}$  to  $\mathbb{R}^{\mathbb{L}}$ , to process D channels the layer employs D independent copies of itself.

<span id="page-2-1"></span> $S6$  Lavers A recent development in state space layers is selective SSMs [30]  $(S6)$ , which show outstanding performance in NLP [5,58,73], vision [44,82], graph classification  $[10, 71]$ , and more. These models rely on time-variant SSMs, namely, the discrete matrices  $\bar{A}, \bar{B}$ , and C of each channel are modified over the L time steps depending on the input sequence. As opposed to traditional state-space layers, which operate individually on each channel, selective state-space layers compute the SSM matrices  $\bar{A}_i, \bar{B}_i, C_i$  for all  $i \leq L$  based on all the channels, and then apply the time-variant recurrent rule individually for each channel. Hence, we denote the entire input sequence by  $\hat{x} := (\hat{x}_1, \dots, \hat{x}_L) \in \mathbb{R}^{L \times D}$  where  $\hat{x}_i \in \mathbb{R}^D$ . The per-time discrete matrices  $\bar{A}_i, \bar{B}_i$ , and  $C_i$  are defined as follows:

<span id="page-3-3"></span><span id="page-3-1"></span>
$$B_i = S_B(\hat{x}_i), \quad C_i = S_C(\hat{x}_i), \quad \Delta_i = \text{softplus}(S_\Delta(\hat{x}_i)) \tag{4}$$

$$f_A(\Delta_i, A) = \exp(\Delta_i A), \quad f_B(\Delta_i, A, B_i) = \Delta_i B_i, \tag{5}$$

$$\bar{A}_i = f_A(\Delta_i, A), \quad \bar{B}_i = f_B(\Delta_i, A, B_i) \tag{6}$$

<span id="page-3-0"></span>where fA, f<sup>B</sup> represents the discretization rule, SB, S<sup>C</sup> , S<sup>∆</sup> are linear projection layers, and SoftPlus is an elementwise function that is a smooth approximation of ReLU. While previous state-space layers employ complex-valued SSMs and non-diagonal matrices, Mamba employs real-diagonal parametrization.

The motivation for input-dependent time-variant layers is to make those recurrent layers more expressive and flexible, allowing them to capture more complex dependencies. While other input-dependent time-variant mechanisms have been proposed in previous works through gated RNNs, the S5 layer [\[66\]](#page-17-5), or adaptive filtering via input-dependent IIR filters [\[47\]](#page-16-7), Mamba significantly improves on these layers by presenting a flexible, yet still efficient, approach. This efficiency was achieved via the IO-aware implementation of associative scans, which can be parallelized on modern hardware via work-efficient parallel scanners [\[12,](#page-14-5) [50\]](#page-16-8).

Mamba The Mamba block is built on top of the selective state-space layer, Conv1D and other elementwise operators. Inspired by the architecure of Gated MLP and H3 [\[24\]](#page-15-6), and given an input xˆ ′ := (ˆx ′ 1 , · · · xˆ ′ L ) it is defined as follows:

$$\hat{x} = \text{SiLU}(\text{Conv1D}(\text{Linear}(\hat{x}'))), \quad \hat{z} = \text{SiLU}(\text{Linear}(\hat{x}')) \tag{7}$$

$$\hat{y}' = \text{Linear}(\text{Selective SSM}(\hat{x}) \otimes \hat{z})), \quad \hat{y} = \text{LayerNorm}(\hat{y}' + \hat{x}') \tag{8}$$

<span id="page-3-2"></span>where ⊗ is elementwise multiplication. Mamba models contain Λ stacked mamba blocks and D channels per block, and we denote the tensors in the i-th block and j-th channel with a superscript, where the first index refers to the block number.

Inspired by the vision transformer ViT [\[19\]](#page-15-9), both [\[44,](#page-16-0)[82\]](#page-18-1) replace the standard self-attention mechanism by two Mamba layers, where each layer is applied in a bidirectional manner. The resulting model achieves favorable results compared to the standard ViT in terms of both accuracy and efficiency, when comparing models with the same number of parameters.

Explainability Explainability methods have been extensively explored in the context of deep neural networks, particularly in domains such as natural language processing (NLP) [\[1,](#page-14-6) [4,](#page-14-7) [6,](#page-14-8) [14,](#page-14-9) [15,](#page-15-3) [81\]](#page-18-10), computer vision [\[7,](#page-14-10) [36,](#page-16-9) [53,](#page-17-6) [64,](#page-17-7) [68\]](#page-17-8), and attention-based models [\[4,](#page-14-7) [14,](#page-14-9) [15,](#page-15-3) [81\]](#page-18-10).

The contributions most closely aligned with ours are those specifically tailored for transformer explainability. Abnar and Zuidema [\[1\]](#page-14-6) introduce the Attention-Rollout method, which aggregates the attention matrices across different layers by analyzing the paths in the inter-layer pairwise attention graph. Chefer et al. [\[14,](#page-14-9) [15\]](#page-15-3) combine LRP scores [\[7\]](#page-14-10) with the attention gradients to obtain classspecific relevance scores. Ali et al. [\[4\]](#page-14-7) enhanced attributions by treating the

<span id="page-4-4"></span>non-linear Softmax and LayerNorm operators as a constant, thereby attributing relevance exclusively through the value path, disregarding these operators. Yuan et al. [\[81\]](#page-18-10) treats the output token representations as states in a Markov chain in which the transition matrix is built using attention weights.

Our work performs similar attention-based analysis for Mamba and we derive versions of [\[1,](#page-14-6) [15\]](#page-15-3) that are suitable for such SSM models.

## 3 Method

In this section, we detail our methodology. First, in section [3.1,](#page-4-1) we reformulate selective state-space (S6) layers as self-attention, enabling the extraction of attention matrices from S6 layers. Subsequently, in sections [3.2](#page-6-0) and [3.3,](#page-7-0) we demonstrate how these hidden attention matrices can be leveraged to develop class-agnostic and class-specific tools for explainable AI of Mamba models.

### <span id="page-4-1"></span>3.1 Hidden Attention Matrices In Selective State Spaces Layers

Given the per-channel time-variant system matrices A¯ <sup>1</sup>, · · · , A¯L, B¯ <sup>1</sup>, · · · , B¯L, and C1, · · · , C<sup>L</sup> from Eq. [4](#page-2-1) and [6,](#page-3-0) each channel within the selective state-space layers can be processed independently. Thus, for simplicity, the formulation presented in this section will proceed under the assumption that the input sequence x consists of a single channel.

By considering the initial conditions h<sup>0</sup> = 0, unrolling Eq. [2](#page-2-2) yields:

$$h_1 = \bar{B}_1 x_1, \quad y_1 = C_1 \bar{B}_1 x_1, \quad h_2 = \bar{A}_2 \bar{B}_1 x_1 + \bar{B}_2 x_2, \quad y_2 = C_2 \bar{A}_2 \bar{B}_1 x_1 + C_2 \bar{B}_2 x_2 \tag{9}$$

<span id="page-4-2"></span>and in general:

$$h_t = \sum_{j=1}^t \left( \Pi_{k=j+1}^t \bar{A}_k \right) \bar{B}_j x_j, \quad y_t = C_t \sum_{j=1}^t \left( \Pi_{k=j+1}^t \bar{A}_k \right) \bar{B}_j x_j \tag{10}$$

<span id="page-4-0"></span>By converting Eq. [10](#page-4-2) into a matrix form we get:

$$y = \tilde{\alpha}x, \begin{bmatrix} y_1 \\ y_2 \\ \vdots \\ y_L \end{bmatrix} = \begin{bmatrix} C_1\bar{B}_1 & 0 & \cdots & 0 \\ C_2\bar{A}_2\bar{B}_1 & C_2\bar{B}_2 & \cdots & 0 \\ \vdots & \vdots & \ddots & 0 \\ C_L\Pi_{k=2}^L\bar{A}_k\bar{B}_1 & C_L\Pi_{k=3}^L\bar{A}_k\bar{B}_2 & \cdots & C_L\bar{B}_L \end{bmatrix} \begin{bmatrix} x_1 \\ x_2 \\ \vdots \\ x_L \end{bmatrix} \tag{11}$$

Hence, the S6 layer can be viewed as a data-controlled linear operator [\[59\]](#page-17-9), where the matrix α˜ ∈ R <sup>L</sup>×<sup>L</sup> is a function of the input and the parameters A, SB, S<sup>C</sup> , S∆. The element at row i and column j captures how x<sup>j</sup> influences yi , and is computed by:

<span id="page-4-3"></span>
$$\tilde{\alpha}_{i,j} = C_i \Big( \Pi_{k=j+1}^i \bar{A}_k \Big) \bar{B}_j \tag{12}$$

Eq. 11 and 12 link  $\tilde{\alpha}$  to the conventional standard attention matrix (Eq. 1), and highlight that S6 can be considered a variant of causal self-attention.

Simplifying and Interpreting the Hidden Matrices Since  $\bar{A}_t$  is a diagonal matrix, the different N coordinates of the state  $h_t$  in Eq. 10 do not interact when computing  $h_{t+1}$ . Thus, Eq. 10 (left) can be computed independently for each coordinate  $m \in \{1, 2, \ldots, N\}$ :

<span id="page-5-0"></span>
$$h_t[m] = \sum_{j=1}^t \left( \Pi_{k=j+1}^t \bar{A}_k[m,m] \right) \bar{B}_j[m] x_j, \quad y_t = \sum_{m=1}^N C_t[m] h_t[m] \tag{13}$$

<span id="page-5-1"></span>where  $C_i[m], A_k[m,m], B_i[m] \in \mathbb{R}$ , plugging it into Eq. 12 yields:

$$\tilde{\alpha}_{i,j} = C_i \Big( \Pi_{k=j+1}^i \bar{A}_k \Big) \bar{B}_j = \sum_{m=1}^N C_i[m] \Big( \Pi_{k=j+1}^i \bar{A}_k[m,m] \Big) \bar{B}_j[m] \tag{14}$$

Note that while equations  $10$  and  $12$  contain matrix multiplication, Eq.  $13$ relies on elementwise multiplication.

An interesting observation arising from Eq.  $14$  is that a single channel of S6 produces N inner attention matrices  $C_i[m] \left( \prod_{k=j+1}^i \bar{A}_k[m,m] \right) \bar{B}_j[m]$ , which are summed up over m to obtain  $\tilde{\alpha}$ . In contrast, in the Transformer, a single attention matrix is produced by each of the  $H$  attention heads. Given that the number of channels in Mamba models  $D$  is typically a hundred times greater than the number of heads in a transformer (for example, Vision-Mamba-Tiny has  $D = 384$  channels, compared to  $H = 3$  heads in DeiT-Tiny), the Mamba layer generates approximately  $\frac{DN}{H} \approx 100N$  more attention matrices than the original self-attention layer.

To further understand the structure and characterization of these attention matrices, we will express the hidden attention matrices  $\tilde{\alpha}$  for each channel d as a direct function of the input  $\hat{x}$ . To do so, we first substitute Eq.4, 5 and Eq.6 into Eq.  $12$ , and obtain:

<span id="page-5-2"></span>
$$\tilde{\alpha}_{i,j} = S_C(\hat{x}_i) \Big( \Pi_{k=j+1}^i \exp\left( \text{softplus}(S_\Delta(\hat{x}_k)) A \right) \Big) \text{softplus}(S_\Delta(\hat{x}_j)) S_B(\hat{x}_j) = \n$$
(15)

$$S_C(\hat{x}_i) \Big( \exp \Big( \sum_{k=j+1}^i \text{softplus}(S_\Delta(\hat{x}_k)) \Big) A \Big) \text{softplus}(S_\Delta(\hat{x}_j)) S_B(\hat{x}_j) \tag{16}$$

<span id="page-5-3"></span>For simplicitly, we propose a simplification of Eq.  $16$  by substituting the softplus function with the ReLU function, and summing only over positive elements:

$$\tilde{\alpha}_{i,j} \approx S_C(\hat{x}_i) \left( \exp \left( \sum_{\substack{k=j+1\\S_\Delta(\hat{x}_k)>0}}^i S_\Delta(\hat{x}_k) \right) A \right) \text{ReLU}(S_\Delta(\hat{x}_j)) S_B(\hat{x}_j) \tag{17}$$

<span id="page-6-4"></span>Consider the following  $query/key/value notation$ :

$$\tilde{Q}_{i} := S_{C}(\hat{x}_{i}), \ \tilde{K}_{j} := \text{ReLU}(S_{\Delta}(\hat{x}_{j})S_{B}(\hat{x}_{j}), \ \tilde{H}_{i,j} := \exp\Big(\sum_{\substack{k=j+1\\S_{\Delta}(\hat{x}_{k})>0}}^{i} S_{\Delta}(\hat{x}_{k})\Big) A\n$$
(18)

Eq.  $17$  can be further simplified to:

<span id="page-6-2"></span><span id="page-6-1"></span>
$$\tilde{\alpha}_{i,j} \approx \tilde{Q}_i \tilde{H}_{i,j} \tilde{K}_j \tag{19}$$

This formulation enhances our understanding of the Mamba's attention mechanism. Whereas traditional self-attention captures the influence of  $x_i$  on  $x_i$ through the dot products between  $Q_i$  and  $K_j$ , Mamba's approach correlates this influence with  $Q_i$  and  $K_i$ , respectively. Additionally,  $H_{i,j}$  controls the significance of the recent  $i-j$  tokens, encapsulating the continuous aggregated historical context spanning from  $x_j$  to  $x_i$ .

This distinction between self-attention and Mamba, captured by  $H_{i,j}$  could be a key factor in enabling Mamba models to understand and utilize continuous historical context within sequences more efficiently than attention.

Furthermore, Eq.  $19$ , and  $18$  offer further insights into the characterization of the hidden attention matrices by demonstrating that the only terms modified across channels are A and  $\Delta_i$ , which influence the values of  $\ddot{H}_{i,j}$  and  $\ddot{K}_j$  through the discretization rule in Eq.  $5$ . Hence, all the hidden attention matrices follow a common pattern, distinguished by the keys  $K_j$  via  $\Delta_i$  and the significance of the history  $H_{i,j}$  via  $A$  and  $\Delta_i$ .

A distinct divergence between Mamba's attention mechanism and traditional self-attention lies in the latter's utilization of a per-row softmax function. It is essential to recognize that various attention models have either omitted the softmax  $[46]$  or substituted it with elementwise neural activations  $[38, 49, 77, 83]$ , achieving comparable outcomes to the original framework.

The softmax operator is known to lead to oversmoothing  $[3, 74]$ . As we show in the Appendix A, Mamba attention layers have lower inter-token smoothing than Transformer attention.

#### <span id="page-6-0"></span> $3.2$ Application to Attention Rollout

As our class-agnostic explainability teachnique for Mamba models, we built our method on top of the Attention-Rollout  $[1]$  method. For simplicity, we assume that we are dealing with a vision mamba model, which operates on sequences of size  $L+1$ , where L is the sequence length obtained from the  $\sqrt{L} \times \sqrt{L}$  image patches, with a classification (CLS) token appended to the end of the sequence.

To do so, for each sample, we first extract the hidden attention matrix  $\tilde{\alpha}^{\lambda,d}$  for any channel  $d \in [D]$  and layer  $\lambda \in [A]$  according to the formulation in section 3.1 (Eq. 11), such that  $\tilde{\alpha}^{\lambda,d} \in \mathbb{R}^{(L+1)\times(L+1)}$ 

Attention-Rollout is then applied as follows:

<span id="page-6-3"></span>
$$\forall \lambda \in [\Lambda]: \quad \tilde{\alpha}^{\lambda} = \mathbb{I}_{L+1} + \underset{d \in [D]}{\mathbb{E}} (\tilde{\alpha}^{\lambda, d}), \quad \tilde{\alpha}^{\lambda} \in \mathbb{R}^{(L+1) \times (L+1)} \tag{20}$$

<span id="page-7-3"></span>where  $\mathbb{I}_{L+1} \in \mathbb{R}^{(L+1)\times(L+1)}$  is an identity matrix utilized to incorporate the influence of skip connections along the layers.

Now, the per-layer global attention matrices  $\tilde{\alpha}^{\lambda}$  for all  $\lambda \in [\Lambda]$  are aggregated into the final map  $\rho$  by:

<span id="page-7-1"></span>
$$\rho = \Pi_{\lambda=1}^{\Lambda} \tilde{\alpha}^{\lambda}, \quad \rho \in \mathbb{R}^{(L+1)\times(L+1)} \tag{21}$$

Note that each row of  $\rho$  corresponds to a relevance map for each token, given the other tokens. In the context of this study, which concentrates on classification models, our attention analysis directs attention exclusively to the CLS token. Thus, we derive the final relevance map from the row associated with the CLS token in the output matrix, denoted by  $\rho_{\text{CLS}} \in \mathbb{R}^L$ , which contains the relevance scores evaluating each token's influence on the classification token. Finally, to obtain the final explanation heatmap we reshape  $\rho_{\text{CLS}} \in \mathbb{R}^L$  to  $\sqrt{L} \times \sqrt{L}$  and upsample it back to the size of the original image using bilinear interpolation.

Although Mamba models are causal by definition, resulting in causal hidden attention matrices, our method can be extended to a bidirectional setting in a straightforward manner. This adaptation involves modifying Eq. 20 so that  $\tilde{\alpha}^{\lambda,d}$ becomes the outcome of summing the (two) per-direction matrices of the  $\lambda$ -layer and the  $d$ -channel.

#### <span id="page-7-0"></span> $3.3$ Application to Attention-based Attribution

As our class-specific explainability technique for Mamba models, we have tailored the Transformer-Attribution [15] explainability method, which is specifically designed for transformers, to suit Mamba models. This method relies on a combination of LRP scores and attention gradients to generate the relevance scores. Since each Mamba block includes several peripheral layers that are not included in transformers, such as Conv1D, additional gating mechanisms, and multiple linear projection layers, a robust mechanism must be designed carefully. For simplicity, we focus on vision Mamba, with a grid of  $\sqrt{L}$  patches in each row and column, as in Sec.  $3.2$ .

The Transformer-Attribution method encompasses two stages: (i) generating a relevance map for each attention layer, followed by (ii) the aggregation of these relevance maps across all layers, using the aggregation rule specified in  $21$ , to produce the final map  $\rho$ .

The difference from the attention rollout method therefore lies in how step (i) is applied to each Mamba layer  $\lambda \in [A]$ . For the  $\hat{h} \in [H]$  attention head at layer  $\lambda$ , the transformer method [15] computes the following two maps: (1) LRP [7] relevance scores map  $R^{\lambda,\hat{h}}$ , and (2) the gradients  $\nabla \tilde{\alpha}^{\lambda,\hat{h}}$  with respect to a target class of interest. Then, these two are fused by a Hadamard product:

<span id="page-7-2"></span>
$$\beta^{\lambda} = \mathbb{I}_{L} + \underset{\hat{h}\in[\hat{H}]}{\mathbb{E}} (\nabla \alpha^{\lambda,\hat{h}} \odot R^{\lambda,\hat{h}})^{+}, \quad \mathbb{I}_{L+1} \in \mathbb{R}^{(L+1)\times(L+1)}$$
(22)

Our method, Mamba-Attribution, depicted in Fig. 2, deviates from this method by modifying Eq.  $22$  in the following aspects: (i) Instead of computing the

<span id="page-8-2"></span><span id="page-8-0"></span>![](_page_8_Figure_1.jpeg)

Fig. 2: Comperative Visualization of Transformer-Attribution and our Mamba-Attribution, both class specific methods.

Fig. 3: Average attention maps for CLS token in the middle (a,b,c) and as the first (d,e,f).

gradients on the per-head attention matrices ∇α λ,hˆ , we compute the gradients of ∇yˆ ′λ,d. The motivation for these modifications is to exploit the gradients of both the S6 mixer and the gating mechanism in Eq. [8](#page-3-2) (left), to obtain strong classspecific maps. (ii) We simply replace Rλ,h<sup>ˆ</sup> with the attention matrices α˜ λ,d at layer λ and channel d, since we empirically observe that those attention matrices produce better relevance maps. Both of these modifications are manifested by the following form, which defines our method:

$$\tilde{\beta}^{\lambda} = \mathbb{I}_{L} + \left( \underset{d \in D}{\mathbb{E}} (\nabla \hat{y}^{\prime \lambda, d}) \odot \underset{d \in D}{\mathbb{E}} (\tilde{\alpha}^{\lambda, d}) \right)^{+} \tag{23}$$

## 4 Experiments

In this section, we present an in-depth analysis of the hidden attention mechanism embedded within Mamba models, focusing on its semantic diversity and applicability in explainable AI frameworks. We start by visualizing the hidden attention matrices for both NLP and vision models in Sec. [4.1,](#page-8-1) followed by assessing our explainable AI techniques empirically, via perturbation and segmentation tests in Sec. [4.2.](#page-10-0)

### <span id="page-8-1"></span>4.1 Visualization of Attention Matrices

The Visual Mamba (ViM) comes in two versions: in one, the CLS token is last and in the other, the CLS token is placed in the middle. Fig. [3](#page-8-0) shows how this positioning influences the impact of the patches on the CLS, by averaging over the entire test set. Evidently, the patches near the CLS token are more influential. This phenomenon may suggest that a better strategy is to have a non-spatial/global CLS token [\[22,](#page-15-10) [37\]](#page-16-13).

Fig. [4](#page-9-0) compares the attention matrices in Mamba and Transformer on both vision and NLP tasks. For clearer visualization, we apply the Softmax function to each row of the attention matrices obtained from transformers and perform minmax normalization on the absolute values of the Mamba matrices. In all cases, we

<span id="page-9-1"></span><span id="page-9-0"></span>![](_page_9_Figure_1.jpeg)

Fig. 4: Hidden Attention Matrices: Attention matrices in vision and NLP Models.Each row represents a different layer within the models, showcasing the evolution of the attention matrices at 25% (top), 50%, and 75% (bottom) of the layer depth.

limit our focus to the first 64 tokens. In vision, we compare Vision-Mamba (ViM) and ViT (DeiT), for models of a tiny size, trained on ImageNet-1K. The attention maps are extracted using examples from the test set. Each Mamba attention matrix is obtained by combining the two maps of the bidirectional channel. In NLP, we compare attention matrices extracted from Mamba (130m) and Transformer (Pythia-160m [\[11\]](#page-14-12)) language models, trained on the Pile [\[25\]](#page-15-11) dataset for next token prediction. The attention maps are extracted using examples from the Lambada dataset (preprocessed by OpenAI).

As can be seen, the hidden attention matrices of Mamba appear to be similar to the attention matrices extracted from transformers In both models, the dependencies between distant tokens are captured in the deeper layers of the model, as depicted in the lower rows.

Some of the attention matrices demonstrate the ability of selective SSM models and transformers to focus on parts of the input. In those cases, instead of the diagonal patterns, some columns seem to miss the diagonal element and the attention is more diffused (recall that we normalized the Mamba attention maps for visualization purposes. In practice, these columns have little activity).

Evidently, both the Mamba attention matrices and the transformer attention matrices possess similar properties and depict the two-dimensional structure within the data as bands with an offset of <sup>√</sup> L.

<span id="page-10-2"></span><span id="page-10-1"></span>![](_page_10_Figure_1.jpeg)

Fig. 5: Qualitative results for the different explanation methods for the ViT-small and the Mamba-small models. (a) the original image, (b) the aggregated Raw-Attention of ViT-Small, (c) Attention Rollout for ViT-Small, (d) Transformer-Attribution for ViT-Small, (e) the Raw-Attention of Mamba-Small, (f) Attention-Rollout of Mamba-Small and (g) the Mamba-Attribution method for the Mamba-Small model.

### <span id="page-10-0"></span>4.2 Explainability Metrics

The explainable AI experiments include three types of explainability methods: (1) Raw-Attention, which employs raw attention scores as relevancies. Our findings indicate that averaging the attention maps across layers yields optimal results. (2) Attn-Rollout [\[1\]](#page-14-6) for Transformers, and its Mamba version, as depicted in Sec. [3.2.](#page-6-0) Finally, (3) The Transformer Attribution of Chefer et al. [\[14\]](#page-14-9) and its Mamba Attribution counterpart, detailed in Sec. [3.3.](#page-7-0)

Fig. [5](#page-10-1) depicts the results of the six attribution methods on typical samples from the ImageNet test set. As can be seen, the Mamba-based heatmaps are often more complete than their transformer-based counterparts. The raw attention of Mamba stands out from the other five heatmaps, since it depicts activity across the entire image. However, the relevant object is highlighted.

Next, we apply explainability evaluation metrics. These metrics allow one to compare different explainability methods that are applied to the same model. Applying them to compare different models is not meant to say that model X is more explainable than model Y. The main purpose is to show that the attention maps of Mamba we introduce are as useful as the attention maps of Transformers <span id="page-11-0"></span>in terms of providing explainability. A secondary aim is to validate the feasibility of potential use for weakly supervised downstream tasks that require spatial location. Perturbation

Perturbation Tests In this evaluation framework, we employ an input perturbation scheme to assess the efficacy of various explanation methods, following the approach outlined by [\[14,](#page-14-9) [15\]](#page-15-3).

These experiments are conducted under two distinct settings. In the positive perturbation scenario, a quality explanation involves an ordered list of pixels, arranged most-to-least relevant. Consequently, when gradually masking out the pixels of the input image, starting from the highest relevance to the lowest, and measuring the mean top-1 accuracy of the network, one anticipates a notable decrease in performance.

Conversely, in the negative perturbation setup, a robust explanation is expected to uphold the accuracy of the model while systematically removing pixels, starting from the lowest relevance to the highest.

In both cases, the evaluation metrics consider the area-under-curve (AUC) focusing on the erasure of 10% to 90% of the pixels.

The results of the perturbations are presented in Tab. [1,](#page-12-0) depicting the performance of different explanation methods under both positive and negative perturbation scenarios across the two models. In the positive perturbation scenario, where lower AUC values are indicative of better performance, we notice that for Raw-Attention, Mamba shows a better AUC compared to the Vision Transformer (ViT). For the Attn-Rollout method, Mamba outperforms the ViT, while the latter shows a better AUC under the Attribution method. In the negative perturbation scenario, where higher AUC values are better, the Transformerbased methods consistently outperform Mammba across all three methods. The tendency for lower AUC in both positive (where it is desirable) and negative perturbation (where it is undesirable) may indicate that the Mamba model is more sensitive to blacking out patches, and it would be interesting to add experiments in which the patches are blurred instead [\[23\]](#page-15-12). For perturbation tests in the NLP domain, please refer to the Appendices [B](#page-20-0) and [C.](#page-23-0)

Segmentation Tests It is expected that an effective explainability method would produce reasonable foreground segmentation maps. This is assessed for ImageNet classifiers by comparing the obtained heatmap against the ground truth segmentation maps available in the ImageNet-Segmentation dataset [\[33\]](#page-16-14).

Evaluation is conducted based on pixel accuracy, mean-intersection-overunion (mIoU) and mean average precision (mAP) metrics, aligning with established benchmarks in the literature for explainability [\[14,](#page-14-9) [15,](#page-15-3) [36,](#page-16-9) [53\]](#page-17-6).

The results are outlined in Tab. [2.](#page-12-0) For Raw-Attention, Mamba demonstrates significantly higher pixel accuracy and mean Intersection over Union compared to Vision Transformer, while the latter performs better in mean Average Precision. Under the Attn-Rollout method, Mamba outperforms Vision Transformer in mean Average Precision, pixel accuracy and mean Intersection over Union. Finally, Transformer-Attribution consistently surpasses Mamba-Attribution, achiev-

|               | Positive Perturbation |             | Negative Perturbation |             |
|---------------|-----------------------|-------------|-----------------------|-------------|
|               | Mamba                 | Transformer | Mamba                 | Transformer |
| Raw-Attention | 17.268                | 20.687      | 34.025                | 40.766      |
| Attn-Rollout  | 18.806                | 20.594      | 41.864                | 43.525      |
| Attribution   | 16.619                | 15.351      | 39.632                | 48.089      |

<span id="page-12-1"></span><span id="page-12-0"></span>Table 1: Positive and Negative perturbation AUC results (percentages) for the predicted class on the ImageNet validation set. For positive perturbation lower is better, and for negative perturbation higher is better.

Table 2: Segmentation performance on the ImageNet-Segmentation [\[33\]](#page-16-14) dataset (percent). Higher is better. The upper part depicts the results for Vision Mamba-small while the lower part contains the results for Vision Transformer-Small

| Model       | Method                  | pixel accuracy | mAP   | mIoU  |
|-------------|-------------------------|----------------|-------|-------|
| Transformer | Raw-Attention           | 59.69          | 77.25 | 36.94 |
| Mamba       | Raw-Attention           | 67.64          | 74.88 | 45.09 |
| Transformer | Attn-Rollout [1]        | 66.84          | 80.34 | 47.85 |
| Mamba       | Attn-Rollout (Sec. 3.2) | 71.01          | 80.78 | 51.51 |
| Transformer | Transformer-Attr [15]   | 79.26          | 84.85 | 60.63 |
| Mamba       | Mamba-Attr (Sec. 3.3)   | 74.72          | 81.70 | 54.24 |

ing the highest scores in pixel accuracy, mean Average Precision, and mean Intersection over Union, respectively.

These results underscore the potential of Mamba's attention mechanism as approaching and sometimes surpassing the interoperability level of Transformer models, especially when the attention maps are taken as is. It also highlights the applicability of Mamba models for downstream tasks such as weakly supervised segmentation. It seems, however, that the Mamba-based attribution model, which is modeled closely after the transformer method of Chefer et al. [\[15\]](#page-15-3) may benefit from further adjustments.

## 5 Discussion: The Evolution of Attention in SSMs

A natural question to ask is whether the attention perspective we exposed is unique to Selective SSM (the building block of Mamba), separating it from other SSMs. The answer is that Selective SSM, similar to transformers, contains a type of layer we call data-dependent non-diagonal mixer, which previous layers do not.

In their seminal work, Poli et al. [\[59\]](#page-17-9) claim that a crucial aspect of transformers is the existence of an expressive, data-controlled linear operator. Here, we focus on a more specific component, which is an expressive data-controlled linear non-diagonal mixer operator. This distinguishes between elementwise operators that act on the data associated with specific tokens (including MLP,

<span id="page-13-0"></span>gating mechanisms, and GLU activations [\[65\]](#page-17-10)) and mixer operations that pool information from multiple tokens.

The mixer components can further be divided into fixed, e.g., using pooling operators with fixed structure and coefficients, or data-dependent, in which the interactions between tokens are controlled by their input-dependent representations, e.g., self-attention. In appendix [E](#page-26-0) we prove the following result, which sheds light on the gradual evolution of attention in SSM models.

Theorem 1. (i) S4 [\[31\]](#page-15-5), DSS [\[34\]](#page-16-15), S5 [\[66\]](#page-17-5) have fixed mixing elements. (ii) GSS [\[52\]](#page-17-11),and Hyena [\[59\]](#page-17-9) have fixed mixing elements with diagonal data-control mechanism. (iii) Selective SSM have data-controlled non-diagonal mixers.

Transformers are recognized for their superior in-context learning (ICL) capabilities, where the model adapts its function according to the input provided [\[13\]](#page-14-13). Empirical evidence has demonstrated that Mamba models are the first SSMs to exhibit ICL capabilities on par with those of transformers [\[29,](#page-15-13)[56\]](#page-17-12). Based on the intuition that the capacity to focus on specific inputs is required for ICL, we hypothesize that the presence of data-controlled non-diagonal mixers in both transformers and Mamba models is crucial for achieving a high level of ICL.

A question then arises: which model is more expressive, transformers or selective SSM? While previous work has shown that Transformers are more expressive than traditional state-space layers [\[85\]](#page-18-14), we show in Appendix [D](#page-23-1) that the situation is reversed for selective SSMs, as follows:

Theorem 2. One channel of the selective state-space layer can express all functions that a single transformer head can express. Conversely, a single Transformer layer cannot express all functions that a single selective SSM layer can.

## 6 Conclusions

In this work, we have established a significant link between Mamba and selfattention layers, illustrating that the Mamba layer can be reformulated as an implicit form of causal self-attention mechanism. This links the highly effective Mamba layers directly with the transformer layers.

The parallel perspective plays a crucial role in efficient training and the recurrent perspective is essential for effective causal generation. The attention perspective plays a role in understanding the inner representation of the Mamba model. While "Attention is not Explanation" [\[39\]](#page-16-16), attention layers have been widely used for transformer explainability. By leveraging the obtained attention matrices, we introduce the first (as far as we can ascertain) explainability techniques for Mamba models, for both task-specific and task-agnostic regimes. This contribution equips the research community with novel tools for examining the performance, fairness, robustness, and weaknesses of Mamba models, thereby paving the way for future improvements, and it also enables weakly supervised downstream tasks. Looking ahead, we plan to delve into the relationships between Mamba, Self-Attention and other recent layers, such as RWKV [\[57\]](#page-17-13), Retention [\[67\]](#page-17-14) and Hyena [\[59\]](#page-17-9), and develop XAI methods for LLMs relying on these layers and their corresponding vision variants [\[21,](#page-15-14) [84\]](#page-18-15).

## 7 Acknowledgments

This work was supported by a grant from the Tel Aviv University Center for AI and Data Science (TAD). This research was also supported by the Ministry of Innovation, Science & Technology ,Israel (1001576154) and the Michael J. Fox Foundation (MJFF-022407). The contribution of the first author is part of a PhD thesis research conducted at Tel Aviv University.

## References

- <span id="page-14-6"></span>1. Abnar, S., Zuidema, W.: Quantifying attention flow in transformers. In: Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. pp. 4190–4197 (2020) [4,](#page-3-3) [5,](#page-4-4) [7,](#page-6-4) [11,](#page-10-2) [13](#page-12-1)
- <span id="page-14-1"></span>2. Ahamed, M.A., Cheng, Q.: Mambatab: A simple yet effective approach for handling tabular data. arXiv preprint arXiv:2401.08867 (2024) [1](#page-0-1)
- <span id="page-14-11"></span>3. Ali, A., Galanti, T., Wolf, L.: Centered self-attention layers. arXiv preprint arXiv:2306.01610 (2023) [7,](#page-6-4) [20,](#page-19-1) [21](#page-20-1)
- <span id="page-14-7"></span>4. Ali, A., Schnake, T., Eberle, O., Montavon, G., Müller, K.R., Wolf, L.: Xai for transformers: Better explanations through conservative propagation. In: International Conference on Machine Learning. pp. 435–451. PMLR (2022) [4,](#page-3-3) [21](#page-20-1)
- <span id="page-14-0"></span>5. Anthony, Q., Tokpanov, Y., Glorioso, P., Millidge, B.: Blackmamba: Mixture of experts for state-space models. arXiv preprint arXiv:2402.01771 (2024) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-14-8"></span>6. Arras, L., Montavon, G., Müller, K.R., Samek, W.: Explaining recurrent neural network predictions in sentiment analysis. In: Proceedings of the 8th Workshop on Computational Approaches to Subjectivity, Sentiment and Social Media Analysis. pp. 159–168 (2017) [4](#page-3-3)
- <span id="page-14-10"></span>7. Bach, S., Binder, A., Montavon, G., Klauschen, F., Müller, K.R., Samek, W.: On pixel-wise explanations for non-linear classifier decisions by layer-wise relevance propagation. PloS one 10(7), e0130140 (2015) [4,](#page-3-3) [8](#page-7-3)
- <span id="page-14-3"></span>8. Bahdanau, D., Cho, K., Bengio, Y.: Neural machine translation by jointly learning to align and translate. arXiv preprint arXiv:1409.0473 (2014) [3](#page-2-4)
- <span id="page-14-4"></span>9. Baron, E., Zimerman, I., Wolf, L.: 2-d ssm: A general spatial layer for visual transformers. arXiv preprint arXiv:2306.06635 (2023) [3](#page-2-4)
- <span id="page-14-2"></span>10. Behrouz, A., Hashemi, F.: Graph mamba: Towards learning on graphs with state space models. arXiv preprint arXiv:2402.08678 (2024) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-14-12"></span>11. Biderman, S., Schoelkopf, H., Anthony, Q.G., Bradley, H., O'Brien, K., Hallahan, E., Khan, M.A., Purohit, S., Prashanth, U.S., Raff, E., et al.: Pythia: A suite for analyzing large language models across training and scaling. In: International Conference on Machine Learning. pp. 2397–2430. PMLR (2023) [10](#page-9-1)
- <span id="page-14-5"></span>12. Blelloch, G.E.: Prefix sums and their applications. Technical Report (1990) [4](#page-3-3)
- <span id="page-14-13"></span>13. Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J.D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., et al.: Language models are few-shot learners. Advances in neural information processing systems 33, 1877–1901 (2020) [14](#page-13-0)
- <span id="page-14-9"></span>14. Chefer, H., Gur, S., Wolf, L.: Generic attention-model explainability for interpreting bi-modal and encoder-decoder transformers. In: Proceedings of the IEEE/CVF International Conference on Computer Vision. pp. 397–406 (2021) [4,](#page-3-3) [11,](#page-10-2) [12](#page-11-0)

- 16 Ali, Zimerman, Wolf
- <span id="page-15-3"></span>15. Chefer, H., Gur, S., Wolf, L.: Transformer interpretability beyond attention visualization. In: Proceedings of the IEEE/CVF conference on computer vision and pattern recognition. pp. 782–791 (2021) [3,](#page-2-4) [4,](#page-3-3) [5,](#page-4-4) [8,](#page-7-3) [12,](#page-11-0) [13,](#page-12-1) [21](#page-20-1)
- <span id="page-15-4"></span>16. Chefer, H., Schwartz, I., Wolf, L.: Optimizing relevance maps of vision transformers improves robustness. Advances in Neural Information Processing Systems 35, 33618–33632 (2022) [3](#page-2-4)
- <span id="page-15-17"></span>17. Chen, N., Shou, L., Pei, J., Gong, M., Cao, B., Chang, J., Li, J., Jiang, D.: Alleviating over-smoothing for unsupervised sentence representation. In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 3552–3566 (Jul 2023) [20](#page-19-1)
- <span id="page-15-8"></span>18. David, S.B., Zimerman, I., Nachmani, E., Wolf, L.: Decision s4: Efficient sequencebased rl via state spaces layers. In: The Eleventh International Conference on Learning Representations (2022) [3](#page-2-4)
- <span id="page-15-9"></span>19. Dosovitskiy, A., Beyer, L., Kolesnikov, A., Weissenborn, D., Zhai, X., Unterthiner, T., Dehghani, M., Minderer, M., Heigold, G., Gelly, S., et al.: An image is worth 16x16 words: Transformers for image recognition at scale. arXiv preprint arXiv:2010.11929 (2020) [4](#page-3-3)
- <span id="page-15-15"></span>20. Dovonon, G.J., Bronstein, M.M., Kusner, M.J.: Setting the record straight on transformer oversmoothing. arXiv preprint arXiv:2401.04301 (2024) [20](#page-19-1)
- <span id="page-15-14"></span>21. Fan, Q., Huang, H., Chen, M., Liu, H., He, R.: Rmt: Retentive networks meet vision transformers. arXiv preprint arXiv:2309.11523 (2023) [14](#page-13-0)
- <span id="page-15-10"></span>22. Farooq, A., Awais, M., Ahmed, S., Kittler, J.: Global interaction modelling in vision transformer via super tokens. arXiv preprint arXiv:2111.13156 (2021) [9](#page-8-2)
- <span id="page-15-12"></span>23. Fong, R.C., Vedaldi, A.: Interpretable explanations of black boxes by meaningful perturbation. In: Proceedings of the IEEE international conference on computer vision. pp. 3429–3437 (2017) [12](#page-11-0)
- <span id="page-15-6"></span>24. Fu, D.Y., Dao, T., Saab, K.K., Thomas, A.W., Rudra, A., Ré, C.: Hungry hungry hippos: Towards language modeling with state space models. arXiv preprint arXiv:2212.14052 (2022) [3,](#page-2-4) [4](#page-3-3)
- <span id="page-15-11"></span>25. Gao, L., Biderman, S., Black, S., Golding, L., Hoppe, T., Foster, C., Phang, J., He, H., Thite, A., Nabeshima, N., et al.: The pile: An 800gb dataset of diverse text for language modeling. arXiv preprint arXiv:2101.00027 (2020) [10](#page-9-1)
- <span id="page-15-7"></span>26. Goel, K., Gu, A., Donahue, C., Ré, C.: It's raw! audio generation with state-space models. In: International Conference on Machine Learning. pp. 7616–7633. PMLR (2022) [3](#page-2-4)
- <span id="page-15-16"></span>27. Gong, C., Wang, D., Li, M., Chandra, V., Liu, Q.: Vision transformers with patch diversification. arXiv preprint arXiv:2104.12753 (2021) [20](#page-19-1)
- <span id="page-15-1"></span>28. Gong, H., Kang, L., Wang, Y., Wan, X., Li, H.: nnmamba: 3d biomedical image segmentation, classification and landmark detection with state space model. arXiv preprint arXiv:2402.03526 (2024) [1](#page-0-1)
- <span id="page-15-13"></span>29. Grazzi, R., Siems, J., Schrodi, S., Brox, T., Hutter, F.: Is mamba capable of incontext learning? arXiv preprint arXiv:2402.03170 (2024) [14](#page-13-0)
- <span id="page-15-0"></span>30. Gu, A., Dao, T.: Mamba: Linear-time sequence modeling with selective state spaces. arXiv preprint arXiv:2312.00752 (2023) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-15-5"></span>31. Gu, A., Goel, K., Ré, C.: Efficiently modeling long sequences with structured state spaces. arXiv preprint arXiv:2111.00396 (2021) [3,](#page-2-4) [14,](#page-13-0) [27](#page-26-1)
- <span id="page-15-2"></span>32. Gu, A., Johnson, I., Goel, K., Saab, K., Dao, T., Rudra, A., Ré, C.: Combining recurrent, convolutional, and continuous-time models with linear state space layers. Advances in neural information processing systems 34, 572–585 (2021) [1,](#page-0-1) [3](#page-2-4)

- <span id="page-16-14"></span>33. Guillaumin, M., Küttel, D., Ferrari, V.: Imagenet auto-annotation with segmentation propagation. International Journal of Computer Vision 110, 328–348 (2014) [12,](#page-11-0) [13](#page-12-1)
- <span id="page-16-15"></span>34. Gupta, A., Gu, A., Berant, J.: Diagonal state spaces are as effective as structured state spaces. Advances in Neural Information Processing Systems 35, 22982–22994 (2022) [14,](#page-13-0) [27](#page-26-1)
- <span id="page-16-18"></span>35. Gupta, A., Mehta, H., Berant, J.: Simplifying and understanding state space models with diagonal linear rnns. arXiv preprint arXiv:2212.00768 (2022) [25](#page-24-0)
- <span id="page-16-9"></span>36. Gur, S., Ali, A., Wolf, L.: Visualization of supervised and self-supervised neural networks via attribution guided factorization. In: Proceedings of the AAAI conference on artificial intelligence. vol. 35, pp. 11545–11554 (2021) [4,](#page-3-3) [12](#page-11-0)
- <span id="page-16-13"></span>37. Hatamizadeh, A., Yin, H., Heinrich, G., Kautz, J., Molchanov, P.: Global context vision transformers. In: International Conference on Machine Learning. pp. 12633– 12646. PMLR (2023) [9](#page-8-2)
- <span id="page-16-11"></span>38. Hua, W., Dai, Z., Liu, H., Le, Q.: Transformer quality in linear time. In: International Conference on Machine Learning. pp. 9099–9117. PMLR (2022) [7](#page-6-4)
- <span id="page-16-16"></span>39. Jain, S., Wallace, B.C.: Attention is not explanation. In: Proceedings of NAACL-HLT. pp. 3543–3556 (2019) [14](#page-13-0)
- <span id="page-16-17"></span>40. Kulikov, I., Eremeev, M., Cho, K.: Characterizing and addressing the issue of oversmoothing in neural autoregressive sequence modeling. In: Proceedings of the 2nd Conference of the Asia-Pacific Chapter of the Association for Computational Linguistics and the 12th International Joint Conference on Natural Language Processing (Volume 1: Long Papers). pp. 1115–1124. Association for Computational Linguistics, Online only (Nov 2022) [20](#page-19-1)
- <span id="page-16-4"></span>41. Li, S., Singh, H., Grover, A.: Mamba-nd: Selective state space modeling for multidimensional data. arXiv preprint arXiv:2402.05892 (2024) [1](#page-0-1)
- <span id="page-16-3"></span>42. Liang, D., Zhou, X., Wang, X., Zhu, X., Xu, W., Zou, Z., Ye, X., Bai, X.: Pointmamba: A simple state space model for point cloud analysis. arXiv preprint arXiv:2402.10739 (2024) [1](#page-0-1)
- <span id="page-16-1"></span>43. Liu, J., Yang, H., Zhou, H.Y., Xi, Y., Yu, L., Yu, Y., Liang, Y., Shi, G., Zhang, S., Zheng, H., et al.: Swin-umamba: Mamba-based unet with imagenet-based pretraining. arXiv preprint arXiv:2402.03302 (2024) [1](#page-0-1)
- <span id="page-16-0"></span>44. Liu, Y., Tian, Y., Zhao, Y., Yu, H., Xie, L., Wang, Y., Ye, Q., Liu, Y.: Vmamba: Visual state space model. arXiv preprint arXiv:2401.10166 (2024) [1,](#page-0-1) [3,](#page-2-4) [4](#page-3-3)
- <span id="page-16-6"></span>45. Lu, C., Schroecker, Y., Gu, A., Parisotto, E., Foerster, J., Singh, S., Behbahani, F.: Structured state space models for in-context reinforcement learning. Advances in Neural Information Processing Systems 36 (2024) [3](#page-2-4)
- <span id="page-16-10"></span>46. Lu, J., Yao, J., Zhang, J., Zhu, X., Xu, H., Gao, W., Xu, C., Xiang, T., Zhang, L.: Soft: Softmax-free transformer with linear complexity. Advances in Neural Information Processing Systems 34, 21297–21309 (2021) [7](#page-6-4)
- <span id="page-16-7"></span>47. Lutati, S., Zimerman, I., Wolf, L.: Focus your attention (with adaptive iir filters). arXiv preprint arXiv:2305.14952 (2023) [4](#page-3-3)
- <span id="page-16-2"></span>48. Ma, J., Li, F., Wang, B.: U-mamba: Enhancing long-range dependency for biomedical image segmentation. arXiv preprint arXiv:2401.04722 (2024) [1](#page-0-1)
- <span id="page-16-12"></span>49. Ma, X., Zhou, C., Kong, X., He, J., Gui, L., Neubig, G., May, J., Zettlemoyer, L.: Mega: moving average equipped gated attention. arXiv preprint arXiv:2209.10655 (2022) [7](#page-6-4)
- <span id="page-16-8"></span>50. Martin, E., Cundy, C.: Parallelizing linear recurrent neural nets over sequence length. arXiv preprint arXiv:1709.04057 (2017) [4](#page-3-3)
- <span id="page-16-5"></span>51. Mehta, H., Gupta, A., Cutkosky, A., Neyshabur, B.: Long range language modeling via gated state spaces. arXiv preprint arXiv:2206.13947 (2022) [3](#page-2-4)

- 18 Ali, Zimerman, Wolf
- <span id="page-17-11"></span>52. Mehta, H., Gupta, A., Cutkosky, A., Neyshabur, B.: Long range language modeling via gated state spaces. arXiv preprint arXiv:2206.13947 (2022) [14,](#page-13-0) [27](#page-26-1)
- <span id="page-17-6"></span>53. Nam, W.J., Gur, S., Choi, J., Wolf, L., Lee, S.W.: Relative attributing propagation: Interpreting the comparative contributions of individual units in deep neural networks. In: Proceedings of the AAAI conference on artificial intelligence. vol. 34, pp. 2501–2508 (2020) [4,](#page-3-3) [12](#page-11-0)
- <span id="page-17-3"></span>54. Nguyen, E., Goel, K., Gu, A., Downs, G., Shah, P., Dao, T., Baccus, S., Ré, C.: S4nd: Modeling images and videos as multidimensional signals with state spaces. Advances in neural information processing systems 35, 2846–2861 (2022) [3](#page-2-4)
- <span id="page-17-15"></span>55. Nguyen, T., Nguyen, T., Baraniuk, R.: Mitigating over-smoothing in transformers via regularized nonlocal functionals. Advances in Neural Information Processing Systems 36 (2024) [20](#page-19-1)
- <span id="page-17-12"></span>56. Park, J., Park, J., Xiong, Z., Lee, N., Cho, J., Oymak, S., Lee, K., Papailiopoulos, D.: Can mamba learn how to learn? a comparative study on in-context learning tasks. arXiv preprint arXiv:2402.04248 (2024) [14](#page-13-0)
- <span id="page-17-13"></span>57. Peng, B., Alcaide, E., Anthony, Q., Albalak, A., Arcadinho, S., Cao, H., Cheng, X., Chung, M., Grella, M., GV, K.K., et al.: Rwkv: Reinventing rnns for the transformer era. arXiv preprint arXiv:2305.13048 (2023) [14](#page-13-0)
- <span id="page-17-0"></span>58. Pióro, M., Ciebiera, K., Król, K., Ludziejewski, J., Jaszczur, S.: Moe-mamba: Efficient selective state space models with mixture of experts. arXiv preprint arXiv:2401.04081 (2024) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-17-9"></span>59. Poli, M., Massaroli, S., Nguyen, E., Fu, D.Y., Dao, T., Baccus, S., Bengio, Y., Ermon, S., Ré, C.: Hyena hierarchy: Towards larger convolutional language models. arXiv preprint arXiv:2302.10866 (2023) [5,](#page-4-4) [13,](#page-12-1) [14,](#page-13-0) [27](#page-26-1)
- <span id="page-17-17"></span>60. Romero, D.W., Kuzina, A., Bekkers, E.J., Tomczak, J.M., Hoogendoorn, M.: Ckconv: Continuous kernel convolution for sequential data. arXiv preprint arXiv:2102.02611 (2021) [27](#page-26-1)
- <span id="page-17-16"></span>61. Ru, L., Zheng, H., Zhan, Y., Du, B.: Token contrast for weakly-supervised semantic segmentation. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. pp. 3093–3102 (2023) [20](#page-19-1)
- <span id="page-17-1"></span>62. Ruan, J., Xiang, S.: Vm-unet: Vision mamba unet for medical image segmentation. arXiv preprint arXiv:2402.02491 (2024) [1](#page-0-1)
- <span id="page-17-4"></span>63. Saon, G., Gupta, A., Cui, X.: Diagonal state space augmented transformers for speech recognition. In: ICASSP 2023-2023 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP). pp. 1–5. IEEE (2023) [3](#page-2-4)
- <span id="page-17-7"></span>64. Selvaraju, R.R., Cogswell, M., Das, A., Vedantam, R., Parikh, D., Batra, D.: Gradcam: Visual explanations from deep networks via gradient-based localization. In: Proceedings of the IEEE international conference on computer vision. pp. 618–626 (2017) [4](#page-3-3)
- <span id="page-17-10"></span>65. Shazeer, N.: Glu variants improve transformer. arXiv preprint arXiv:2002.05202 (2020) [14](#page-13-0)
- <span id="page-17-5"></span>66. Smith, J.T., Warrington, A., Linderman, S.W.: Simplified state space layers for sequence modeling. arXiv preprint arXiv:2208.04933 (2022) [4,](#page-3-3) [14,](#page-13-0) [27](#page-26-1)
- <span id="page-17-14"></span>67. Sun, Y., Dong, L., Huang, S., Ma, S., Xia, Y., Xue, J., Wang, J., Wei, F.: Retentive network: A successor to transformer for large language models. arXiv preprint arXiv:2307.08621 (2023) [14](#page-13-0)
- <span id="page-17-8"></span>68. Sundararajan, M., Taly, A., Yan, Q.: Axiomatic attribution for deep networks. In: International conference on machine learning. pp. 3319–3328. PMLR (2017) [4](#page-3-3)
- <span id="page-17-2"></span>69. Touvron, H., Cord, M., Douze, M., Massa, F., Sablayrolles, A., Jégou, H.: Training data-efficient image transformers & distillation through attention. In: International conference on machine learning. pp. 10347–10357. PMLR (2021) [3](#page-2-4)

- <span id="page-18-7"></span>70. Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., Kaiser, L.u., Polosukhin, I.: Attention is all you need. In: Advances in Neural Information Processing Systems. vol. 30 (2017) [2](#page-1-1)
- <span id="page-18-6"></span>71. Wang, C., Tsepa, O., Ma, J., Wang, B.: Graph-mamba: Towards long-range graph sequence modeling with selective state spaces. arXiv preprint arXiv:2402.00789 (2024) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-18-9"></span>72. Wang, J., Zhu, W., Wang, P., Yu, X., Liu, L., Omar, M., Hamid, R.: Selective structured state-spaces for long-form video understanding. In: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition. pp. 6387– 6397 (2023) [3](#page-2-4)
- <span id="page-18-0"></span>73. Wang, J., Gangavarapu, T., Yan, J.N., Rush, A.M.: Mambabyte: Token-free selective state space model. arXiv preprint arXiv:2401.13660 (2024) [1,](#page-0-1) [3](#page-2-4)
- <span id="page-18-13"></span>74. Wang, P., Zheng, W., Chen, T., Wang, Z.: Anti-oversmoothing in deep vision transformers via the fourier domain analysis: From theory to practice. arXiv preprint arXiv:2203.05962 (2022) [7,](#page-6-4) [20,](#page-19-1) [21](#page-20-1)
- <span id="page-18-3"></span>75. Wang, Z., Ma, C.: Semi-mamba-unet: Pixel-level contrastive cross-supervised visual mamba-based unet for semi-supervised medical image segmentation. arXiv preprint arXiv:2402.07245 (2024) [1](#page-0-1)
- <span id="page-18-4"></span>76. Wang, Z., Zheng, J.Q., Zhang, Y., Cui, G., Li, L.: Mamba-unet: Unet-like pure visual mamba for medical image segmentation. arXiv preprint arXiv:2402.05079 (2024) [1](#page-0-1)
- <span id="page-18-11"></span>77. Wortsman, M., Lee, J., Gilmer, J., Kornblith, S.: Replacing softmax with relu in vision transformers. arXiv preprint arXiv:2309.08586 (2023) [7](#page-6-4)
- <span id="page-18-5"></span>78. Xing, Z., Ye, T., Yang, Y., Liu, G., Zhu, L.: Segmamba: Long-range sequential modeling mamba for 3d medical image segmentation. arXiv preprint arXiv:2401.13560 (2024) [1](#page-0-1)
- <span id="page-18-8"></span>79. Yan, J.N., Gu, J., Rush, A.M.: Diffusion models without attention. arXiv preprint arXiv:2311.18257 (2023) [3](#page-2-4)
- <span id="page-18-2"></span>80. Yang, Y., Xing, Z., Zhu, L.: Vivim: a video vision mamba for medical video object segmentation. arXiv preprint arXiv:2401.14168 (2024) [1](#page-0-1)
- <span id="page-18-10"></span>81. Yuan, T., Li, X., Xiong, H., Cao, H., Dou, D.: Explaining information flow inside vision transformers using markov chain. In: eXplainable AI approaches for debugging and diagnosis. (2021) [4,](#page-3-3) [5](#page-4-4)
- <span id="page-18-1"></span>82. Zhu, L., Liao, B., Zhang, Q., Wang, X., Liu, W., Wang, X.: Vision mamba: Efficient visual representation learning with bidirectional state space model. arXiv preprint arXiv:2401.09417 (2024) [1,](#page-0-1) [3,](#page-2-4) [4](#page-3-3)
- <span id="page-18-12"></span>83. Zimerman, I., Baruch, M., Drucker, N., Ezov, G., Soceanu, O., Wolf, L.: Converting transformers to polynomial form for secure inference over homomorphic encryption. arXiv preprint arXiv:2311.08610 (2023) [7](#page-6-4)
- <span id="page-18-15"></span>84. Zimerman, I., Wolf, L.: Multi-dimensional hyena for spatial inductive bias. arXiv preprint arXiv:2309.13600 (2023) [14](#page-13-0)
- <span id="page-18-14"></span>85. Zimerman, I., Wolf, L.: On the long range abilities of transformers. arXiv preprint arXiv:2311.16620 (2023) [14](#page-13-0)

#### <span id="page-19-1"></span><span id="page-19-0"></span>Oversmoothing $\mathbf{A}$

Oversmoothing poses a significant challenge for Transformer-based models  $[3,3,$  $[20, 27, 55, 61, 74]$ , affecting their ability to accurately capture and represent intricate features and relationships. In Transformer-based models, oversmoothing impacts tasks such as natural language processing  $[17, 40]$  and vision  $[3, 27, 61]$ , where it blurs fine-grained details essential for understanding and localization [3, 61.

<span id="page-19-2"></span>![](_page_19_Figure_3.jpeg)

Fig. 6: The inter cosine-similarity across the tokens for both DeiT and Vision-Mamba small models across the layers, results are averaged across the whole validation set of  $ImageNet.$ 

Recent transformer-based contributions  $[3, 74]$  on over-smoothing have developed various tools for measuring it, which we utilize when comparing transformers to Mamba-based architectures. Following Wang et al  $[74]$  we employ the cosine similarity metric, which operates on a layer index  $l$  and its corresponding feature map  $\mathbf{X}^{l} \in \mathbb{R}^{L+1 \times d}$ , such that L is the sequence length excluding the CLS token and  $d$  is the feature dimensionality. The cosine similarity for  $\boldsymbol{X}^{l}$  is then defined as:

$$\boldsymbol{M}_{\text{feat}}^{l} = \frac{2}{n(n-1)} \sum_{i=1}^{n} \sum_{j=i+1}^{n} \frac{\boldsymbol{X}_{i,:}^{(l)T} \boldsymbol{X}_{j,:}^{(l)}}{\|\boldsymbol{X}_{i,:}^{(l)}\|_{2} \|\boldsymbol{X}_{j,:}^{(l)}\|_{2}}, \tag{24}$$

where  $\boldsymbol{X}_{i,:}^{(l)}$  represents the *i*-th row (token) of  $\boldsymbol{X}^{(l)}$ . In words, this measure calculates the average similarity between all token pairs except for self-similarity.

21

<span id="page-20-1"></span>The results are averaged across the entire ImageNet validation set. For further details, refer to  $[74]$ .

Fig. 6 compares  $M_{\text{feat}}^l$  between transformers' attention and Mamba attention for different layers, where the layer index is normalized by the total number of layers. Evidently, there is a clear reduction in the inter-cosine similarity among tokens for all layers in the Mamba model (with 24 layers) compared to the Vision Transformer (12 layers). This variation can be attributed to the use of the softmax operator within the self-attention layer, a factor recognized as contributing to the oversmoothing problem  $[3, 74]$ .

#### <span id="page-20-0"></span>NLP Experiments $\mathbf{B}$

In this experiment, our aim is to extend the utilization of the proposed methods to the domain of Natural Language Processing (NLP). To achieve this, we conduct a comparative analysis between the Mamba-160M model and BERT-large, drawing upon established literature in the field  $[4, 15]$ . Two settings are consid- $\text{ered}$ : (1) activation task, in this task, a good explanation involves listing tokens in order of their relevance, from most to least. When these tokens are added to an initially empty sentence, they should activate the network output as much and as quickly as possible. We evaluate the quality of explanations by observing the output probability  $p_c(x)$  for the ground-truth class c. (2) pruning task, the pruning task involves removing tokens from the original sentence, starting with those deemed least relevant and progressing to the most relevant. We assess the impact of this pruning, by measuring the difference between the unpruned model's output logits  $y_0$  and  $y_{mt}$  of the pruned output. In the activation task, we begin with a sentence containing  $\ll$ UNK $>$ " tokens and gradually replace them with the original tokens in order of highest to lowest relevance. Conversely, in the pruning task, we remove tokens from lowest to highest relevance by replacing them with  $\text{"<}UNK \text{>}$  tokens.

The dataset employed in our study is the IMDb movie review sentiment classification dataset, consisting of  $25,000$  samples for training and an equal number for testing, with binary labels indicating sentiment polarity. We utilize the Mamba- $130M^2$  and BERT<sup>3</sup> models fine-tuned on the IMDB dataset for classification. BERT stands out as our baseline choice, benefiting from a readily available implementation of the Transformer-Attr method<sup> $4$ </sup>. Notably, both models exhibit comparable accuracy levels on the downstream task of IMDB movie review sentiment classification. The results, depicted in Fig. 7, illustrate that in both the pruning and activation tasks, Mamba-Attr exhibits comparable or occasionally superior performance to the Transformer-Attr method. We present the results of each method in separate graphs, as the two models are not directly comparable due to differences in the logit scale and the behavior on random changes to the prompt.

<span id="page-20-2"></span><sup>&</sup>lt;sup>2</sup> https://huggingface.co/trinhxuankhai/mamba\_text\_classification

<span id="page-20-3"></span><sup>&</sup>lt;sup>3</sup> https://huggingface.co/textattack/bert-base-uncased-imdb

<span id="page-20-4"></span><sup>&</sup>lt;sup>4</sup> https://github.com/hila-chefer/Transformer-Explainability

<span id="page-21-0"></span>![](_page_21_Figure_1.jpeg)

Fig. 7: Evaluation of explanations using input perturbations for the IMDb dataset, top row shows the results for the pruning task in which the words of least absolute relevance are replaced with  $\langle \text{UNK} \rangle$  first and the bottom row shows the results for the activation task in which the most relevant words are added first, in both tasks we show the results for Mamba-Attr and Transformer-Attr separately.

In Sec  $\mathbf{C}$  we provide qualitative results for the different explanation methods (Mamba-Attr and Transformer-Attr) on the IMDb dataset, for both positive (green) and negative (red) sentiments. Evidently, Mamba-Attr tends to generate more sparse explanations in comparison to its Transformer-Attr counterpart.

For instance, in the analysis of the first negative sample, our method emphasizes the rating of "1" as the most salient feature along with other negative terms. Conversely, the transformer attribution method yields a less sparse explanation, focusing primarily on the relevant word while also encompassing other nonrelevant terms. Similarly, in the assessment of the third negative example, our method exhibits a comparable behavior, placing emphasis on the ratings alongside other relevant negative terms. Conversely, while the salient words identified by the transformer attribution method remain valid, its explanation is comparatively less sparse. We observe a similar trend across positive sentiments as well (depicted in green). For instance, in the final positive review, Mamba-Attr distinctly highlights the phrase "Greatest Movie which ever made, " serving as clear evidence of a positive sentiment. In contrast, the explanation provided by Trans-Attr appears more broad and encompassing.

## <span id="page-23-0"></span>C NLP Qualitative Results

| Mamba-Attr | Transformer-Attr |
|------------|------------------|
|            |                  |
|            |                  |
|            |                  |
|            |                  |
|            |                  |
|            |                  |
|            |                  |
|            |                  |

## <span id="page-23-1"></span>D Expressiveness of Mamba Models

Theorem 3. One channel of the selective state-space layer can express all functions that a single transformer head can express. Conversely, a single Transformer layer cannot express all functions that a single selective SSM layer can.

Motivation and Intuition: The motivation for this proof relies on H˜ i,j in Eq. 19, which enables Mamba to utilize continuous historical context within <span id="page-24-0"></span>sequences more efficiently than traditional attention mechanisms. To exploit this capability, we focus on a problem involving input-dependent control over the entire input, a task that cannot be captured by relying solely on pairwise interactions at single layer, which constitute the foundation of self-attention. Assumptions:

- 1. For simplicity, we will disregard the discretization, as it has been shown to be unnecessary in previous work [\[35\]](#page-16-18).
- 2. As our regime focuses on real elements (x<sup>i</sup> ∈ R), the hidden dimension of the transformer is 1. Hence, the parameters of both the self-attention mechanism and the Mamba are scalars, namely A<sup>i</sup> , B<sup>i</sup> , C<sup>i</sup> , WQ, W<sup>V</sup> , W <sup>K</sup> ∈ R

Proof. Based on the definition of the count in row function, our proof straightforwardly arises from the following three lemmas:

Definition 1. The count in row problem: Given a binary sequence x1, x2, . . . , x<sup>L</sup> such that x<sup>i</sup> ∈ {0, 1} for all i ≤ L, the "count in row" function f is defined to produce an output sequence y1, y2, . . . , yL, where each y<sup>i</sup> is determined based on the contiguous subsequence of 1s to which x<sup>i</sup> belongs. Formally:

$$y_i = f(x_1, \dots, x_i) = \max_{0 \le j \le i} \left( \{ i - j + 1 \mid \prod_{k=j}^i [x_k > 0] = 1 \} \cup \{ 0 \} \right) \tag{25}$$

where [x<sup>k</sup> > 0] is the Iverson bracket, equaling 1 if x<sup>k</sup> > 0 and 0 otherwise.

Lemma 1. One channel of Mamba can express the count in row function for sequences of any length.

Proof. Assumption 1 defines the following recurrence rule:

$$\bar{B}_i = S_B(\hat{x}_i), \quad C_i = S_C(\hat{x}_i), \quad \bar{A}_i = S_A(\hat{x}_i) + A \tag{26}$$

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t, \quad y_t = C_t h_t \tag{27}$$

<span id="page-24-1"></span>By substituting SB, S<sup>C</sup> , S<sup>A</sup> = 1, A = 0 into Eq. [27,](#page-24-1) we obtain the following results:

$$h_t = h_{t-1} + x_t, \quad y_t = h_t \tag{28}$$

Now, there are two cases: (i) If x<sup>i</sup> = 0, it's clear that both the state h<sup>t</sup> and the output y<sup>t</sup> receive zero values. (ii) Otherwise (if x<sup>i</sup> = 1), we see that both h<sup>t</sup> and y<sup>t</sup> increase by one, clearly demonstrating that the entire mechanism exactly solves the count in row problem.

Lemma 2. One transformer head cannot express the count in row function for sequences with more than two elements.

Proof. The self-attention mechanism computes the output as follows

<span id="page-25-0"></span>
$$O = \text{softmax}\left(\frac{(XW^{Q})(XW^{K})^{T}}{\sqrt{d_{k}}}\right) \cdot (XW^{V}) \tag{29}$$

Consider the count in row problem for a binary sequence of length 3, the i-th coordinate in the output can be computed by:

$$O_{i} = \sum_{j=1}^{3} \left( \frac{\exp\left( (W^{Q} \cdot x_{i}) \cdot (W^{K} \cdot x_{j}) \right)}{\sum_{k=1}^{3} \exp\left( (W^{Q} \cdot x_{i}) \cdot (W^{K} \cdot x_{k}) \right)} \right) \cdot (W^{V} \cdot x_{j}) \tag{30}$$

where we omitted the scale factor <sup>√</sup> d<sup>k</sup> (which can be incorporated into the W<sup>Q</sup> matrix).

For the sake of contradiction, we will assume that there are weights for the key, query, and value matrices that solve this problem. Furthermore, recall that W<sup>Q</sup>, W <sup>K</sup>, W<sup>V</sup> ∈ R, according to Assumption 2. Hence:

<span id="page-25-1"></span>1. For (x1, x2, x3) = (0, 1, 1), the output y<sup>3</sup> = 2. Plugging it into Eq. [30](#page-25-0) yields:

$$O_3 = W^V \Big(\frac{2\exp(W^Q W^K)}{1 + 2\exp(W^Q W^K)}\Big) = 2 \tag{31}$$

<span id="page-25-2"></span>2. For (x1, x2, x3) = (0, 0, 1), the output y<sup>3</sup> = 1. Plugging it into Eq. [30](#page-25-0) yields:

$$O_3 = W^V \left(\frac{\exp(W^Q W^K)}{2 + \exp(W^Q W^K)}\right) = 1 \tag{32}$$

Dividing Eq[.31](#page-25-1) by Eq[.32](#page-25-2) results in the following:

$$2\frac{2 + \exp(W^Q W^K)}{1 + 2\exp(W^Q W^K)} = 2 \quad \rightarrow \quad \exp(W^Q W^K) = 1$$

Upon plugging it into the eq. [31,](#page-25-1) we obtained:

$$O_3 = W^V \frac{2}{3} = 2 \quad \to \quad W^V = 3$$

However, for (x1, x2, x3) = (1, 0, 1), the output y<sup>3</sup> is 1, by plugging it to eq. [30,](#page-25-0) and substituting the values of W<sup>V</sup> and exp(WQW <sup>K</sup>), we obtain:

$$O_3 = 3 \frac{2 \exp(W^Q W^K)}{1 + 2 \exp(W^Q W^K)} = 2 \neq 1$$

As requested. Please note that the same technique also works when omitting the softmax function.

Lemma 3. One channel of the selective state-space layer can express all functions that a single transformer head can express.

Proof. For simplicity, we consider a causal attention variant without softmax, as the softmax is designed to normalize values rather than improve expressiveness. According to Assumption 1, we omit the discretization. Thus, we can simply set the value of A<sup>i</sup> to I which is the identity, by substitute A = I and S<sup>A</sup> = 0. Hence, it is clear that Eq. 11 and Eq. 12 become identical to causal attention, except for the softmax function.

#### <span id="page-26-1"></span><span id="page-26-0"></span> $\mathbf{E}$ Expressiveness of SSMs and Long-Convolution Layers

**Theorem 4.** (i)  $S4$  [31],  $DSS$  [34],  $S5$  [66] have fixed mixing elements. (ii)  $GSS$  [52], and Hyena [59] have fixed mixing elements with diagonal data-control mechanism. (iii) Selective SSM have data-controlled non-diagonal mixers.

 $Proof.$  We will prove this theorem separately per each layer:

 $S4$ ,  $DSS$ : Both layers implicitly parametrize a convolution kernel  $K$  via the  $A, \bar{B}$  and  $\bar{C}$  matrices as follows:

$$\bar{K} = (C\bar{B}, C\bar{A}\bar{B}, \cdots, C\bar{A}^{L-1}\bar{B})$$

This kernel does not depend on the input, and it is the only operation that captures interactions between tokens. Therefore, both layers have fixed elements. **S5:** The S5 layer extend S4 such that it map multi-input to multi-output rather than mapping single-input to single-output. It use the following recurrent  $rule:$ 

$$h_t = \bar{A}h_{t-1} + \bar{B}x_t, \quad y_t = Ch_t, \quad \bar{A} \in \mathbb{R}^{P \times P}, \quad \bar{B} \in \mathbb{R}^{P \times H}, C \in \mathbb{R}^{H \times P}, x_t, y_t \in \mathbb{R}^{H}$$
(33)

which can be computed by

$$y_t = C \sum_{i=1}^t \bar{A}^{t-i} \bar{B} x_t \tag{34}$$

However, in contrast to S4 and DSS, now  $C\bar{A}^i\bar{B}$  in  $\mathbb{R}^{H\times H}$  instead of in  $\mathbb{R}$ . Hence, we can conclude that the mechanism mixes tokens in a fixed pattern, which is captured by  $C \sum_{i=1}^{t} \bar{A}^{t-i} \bar{B} x_t$ .

GSS enhances the DSS framework, which utilizes fixed mixing elements,  $\mathbf{GSS:}$ by incorporating an elementwise gating mechanism. Hence, the entire layer can be viewed as a composition of two operators, a mixer that isn't data-dependent (DSS), and an elementwise data-dependent gating, which is equivalent to a diagonal data-control linear operator.

Hyena: The Hyena layer is defined by the recurrence of two components: long implicit convolution and elementwise gating. For simplicity, we consider single recurrence steps to constitute the entire layer, since any layer can benefit from such a recurrent-based extension. Additionally, single recurrence is the most common application of the Hyena layer. Hence, similar to GSS, the layer can be viewed as a composition of a mixer that isn't data-dependent (based on  $CKConv$  [60]) and a diagonal data-control operator, which is implemented through elementwise data-dependent gating.

Selective SSM: As can be seen in Eq.  $10$  and  $19$ , the selective SSM can be represented by:

$$y = \tilde{\alpha}x, \quad \tilde{\alpha}_{i,j} = \tilde{Q}_i \tilde{H}_{i,j} \tilde{K}_j \tag{35}$$

Thus, it's clear that the linear operator, which relies on  $\tilde{\alpha}$ , is a data-controlled, non-diagonal mixer.