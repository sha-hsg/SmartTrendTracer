# Alternatives To Next Token Prediction In Text Generation - A Survey

Charlie Wyatt1\*, Aditya Joshi<sup>1</sup> and Flora Salim<sup>1</sup> <sup>1</sup>School of Computer Science and Engineering, UNSW Sydney, Sydney, Australia.

\*Corresponding author(s). E-mail(s): charles.wyatt@student.unsw.edu.au; Contributing authors: aditya.joshi@unsw.edu.au; flora.salim@unsw.edu.au;

he paradigm of Next Token Prediction (NTP) has driven the unprecedented success of Large Language Models (LLMs), but is also the source of their most persistent weaknesses such as poor long-term planning, error accumulation, and computational inefficiency. Acknowledging the growing interest in exploring alternatives to NTP, the survey describes the emerging ecosystem of alternatives to NTP. We categorise these approaches into five main families: (1) Multi-Token Prediction, which targets a block of future tokens instead of a single one; (2) Plan-then-Generate, where a global, high-level plan is created upfront to guide token-level decoding; (3) Latent Reasoning, which shifts the autoregressive process itself into a continuous latent space; (4) Continuous Generation Approaches, which replace sequential generation with iterative, parallel refinement through diffusion, flow matching, or energy-based methods; and (5) Non-Transformer Architectures, which sidestep NTP through their inherent model structure. By synthesizing insights across these methods, this survey offers a taxonomy to guide research into models that address the known limitations of token-level generation to develop new transformative models for natural language processing.

## 1 Introduction

Large Language Models (LLMs) have achieved remarkable performance across a wide range of natural language processing (NLP) tasks, from question answering and summarization to creative writing and coding [Hendrycks et al.](#page-19-0) [\(2021\)](#page-19-0); [Srivastava et al.](#page-21-0) [\(2023\)](#page-21-0); [Jiang et al.](#page-20-0) [\(2024\)](#page-20-0). At the heart of this success lies a simple yet powerful objective: Next Token Prediction (NTP) [Vaswani et al.](#page-23-0) [\(2023\)](#page-23-0). Defined as the task of predicting the next subword token given the previous tokens in a sequence, NTP has become the dominant training and decoding paradigm for modern Transformer models.

Yet, despite their fluency, LLMs often exhibit brittle behavior: they hallucinate facts, lose coherence in long outputs [\(Maharana et al.](#page-21-1) [2024\)](#page-21-1), and struggle with tasks that require long-term planning or structured reasoning [\(Hao et al.](#page-20-1) [2023\)](#page-20-1). These limitations persist even as model scale, context length, and training data continue to grow. A growing body of work suggests that these failures are not incidental but symptomatic of deeper structural problems with the next-token prediction framework itself. As [Bachmann and Nagarajan](#page-16-0) [\(2024\)](#page-16-0) argue, the token-level chain rule that NTP relies on can break down, as the probability of the next most likely token does not guarantee the start of the most probable *overall sequence*.

This survey *examines the emerging ecosystem of alternatives to next-token prediction*. We argue that many core weaknesses of LLMs - greedy decoding, error accumulation, misaligned supervision, granularity mismatches, and computational inefficiencies - are downstream of the NTP objective. As Figure [1](#page-1-0) illustrates, a diverse set of methods now reimagine the prediction target, shifting away from token-by-token generation (as in the case of NTP) toward richer and more global semantic representations. While we organize these into five main families for clarity, emerging variants like flow matching and energy-based models represent important extensions within these categories, particularly in continuous generation approaches.

![](_page_1_Picture_0.jpeg)

Fig. 1 An abstracted visualization of Next Token Prediction and its alternatives

## <span id="page-1-0"></span>2 Motivation

This section outlines the core limitations of NTP and motivates the need for alternative decoding and training paradigms. As is evident from the discussion, the use of NTP poses challenges in several aspects of language modeling itself.

### 2.1 Inference-Time Failures: Greedy Generation and Error Accumulation

NTP is an autoregressive generation strategy, *i.e.*, tokens are generated one at a time where the probability of the next token depends only on the existing context. Formally, given a sequence of tokens x = (x1, x2, . . . , x<sup>T</sup> ), the model is trained to maximize the likelihood:

$$P(x) = \prod_{t=1}^{T} P(x_t \mid x_{< t}), \tag{1}$$

where x<t denotes all tokens preceding the position t and x<sup>t</sup> denotes the token at the position t. While this enables fluent local continuations, it also encourages greedy generation—a process that myopically optimizes for short-term token likelihood rather than long-range coherence. This greediness can lead to error accumulation [Rohatgi et al.](#page-21-2) [\(2025\)](#page-21-2), where minor inaccuracies early in generation compound into significant incoherence or factual drift later in the sequence.

These issues are especially pronounced in long-form generation tasks such as summarization and storytelling. As observed in surveys on abstractive summarization [\(Nnadi and Bertini](#page-21-3) [2024\)](#page-21-3), even strong transformer models often struggle with maintaining global consistency and factual grounding across lengthy generations. Although retrieval-augmented generation and extended context windows mitigate some of these issues, they do not fundamentally address the underlying problem: generation proceeds *locally*, without a representation of, or commitment to, a global plan.

Indeed, despite near-perfect performance on "needle-in-a-haystack" retrieval tasks (e.g., GEMINI 1.5's > 99% accuracy [\(Gemini Team et al.](#page-17-0) [2024\)](#page-17-0)), LLMs still underperform at generating coherent long-document summaries. As shown by [Maharana et al.](#page-21-1) [\(2024\)](#page-21-1), LLMs struggle with long-context understanding and temporal grounding, even when equipped with large context windows. A similar phenomenon has been documented outside pure text generation, where the model's step-wise choices reveal a preference for short-term gains. Recent studies in decision-making have further characterized this failure mode as greediness in action selection, where LLMs prematurely commit to locally optimal continuations rather than exploring alternate trajectories [\(Schmied et al.](#page-21-4) [2025\)](#page-21-4). This behaviour reflects a broader limitation in NTP-based generation: the inability to revise earlier decisions in light of later ones, or to reason over long-term structure during decoding.

### 2.2 Granularity Mismatch: Tokens vs. Ideas

Another potential shortcoming of NTP is its mismatch in granularity: NTP operates over subword tokens, but human reasoning unfolds over ideas, sentences, and discourse structures. Modern LLMs typically rely on subword tokenization, most commonly the Byte-Pair Encoding (BPE) algorithm [\(Sennrich et al.](#page-21-5) [2016\)](#page-21-5). While effective for handling large vocabularies, BPE fragments text into units that are neither linguistically natural nor semantically meaningful. In contrast, human communication is organized around higher-level structures such as phrases, sentences, and discourse segments. As a result, tasks like summarization or dialogue understanding—which require reasoning over ideas and maintaining global coherence—are forced to operate on token sequences that fail to reflect these natural semantic boundaries.

This granularity misalignment also manifests in *unexpected and undesirable behaviors* at the token level, such as the well-documented handling of 'glitch tokens" like solidgoldmagikarp [\(Land and Bartolo](#page-20-2) [2024\)](#page-20-2), which arise from under-training or limited exposure in the corpus. Although recent work has proposed methods to detect and mitigate these under-trained tokens, the fact that such ad hoc fixes are needed suggests that sub-word tokens lack the right level of abstraction for language understanding. Beyond these outlier cases, it also leads to surprisingly poor performance on trivial character-level tasks. [Cosma et al.](#page-16-1) [\(2025\)](#page-16-1) and [Fu et al.](#page-17-1) [\(2024\)](#page-17-1) demonstrate that tokenized language models can stumble on rudimentary character-counting tasks such as answering the question *"How many r's are in strawberry?"*. Similarly, autoregressive models fail to plan ahead on even the simplest task: ask an LLM "*How many words are in your response?*" and it will almost always miscount. Since the model generates each word step-by-step, the model cannot see ahead and adjust its plan accordingly.

These failures collectively indicate a structural mismatch: subword tokens are too large for characterlevel reasoning, yet are also too fine-grained for sentence or discourse level abstraction. This problem is particularly acute for typologically rich languages such as Indic languages, where subword tokenizers demonstrate significantly degraded performance [\(Thakur et al.](#page-23-1) [2025\)](#page-23-1). This reinforces the idea that tokens are neither universally the right size nor flexibly compositional for every type of reasoning.

### 2.3 Compute Inefficiency: Quadratic Attention and the Cost of Token-Level Generation

Beyond the representation concerns of subword-by-subword generation, NTP is also computationally inefficient. Transformer-based LLMs compute attention over the full input sequence at each layer and timestep, incurring a time and memory complexity of O(n 2 ) for sequences of length n [\(Vaswani et al.](#page-23-0) [2023\)](#page-23-0). When language is modeled at the subword token level, even modest-length documents can require hundreds or thousands of decoding steps—each step involving full forward passes over all previous tokens. This results in expensive and often redundant computations, especially during generation. The environmental impact of these inefficiencies in modern NLP architectures has also been reported [Ansar et al.](#page-16-2) [\(2024\)](#page-16-2).

Recent work has explored architectural innovations like sparse attention [\(Roy et al.](#page-21-6) [2021;](#page-21-6) [Nguyen et al.](#page-21-7) [2025\)](#page-21-7), linear transformers [\(Beltagy et al.](#page-16-3) [2020\)](#page-16-3), and retrieval-based compression to reduce this overhead. A more principled solution lies in rethinking the granularity of representation itself. If models operated over higher-order units—such as phrases, sentences, or discourse segments—rather than atomic tokens, they could exploit the natural structure of language to reduce the input length into transformers and thereby reduce computational overhead.

Recent architectural innovations have attempted to address these inefficiencies through modified attention mechanisms. Grouped Query Attention (GQA) [\(Ainslie et al.](#page-16-4) [2023\)](#page-16-4) and Multi-Query Attention (MQA) [\(Shazeer](#page-21-8) [2019\)](#page-21-8) reduce memory requirements by sharing key-value heads across multiple query heads, though they still operate fundamentally at the token level. While these optimizations improve efficiency, they don't address the core granularity mismatch—models still process hundreds of tokens even for conceptually simple operations. The tight coupling between attention mechanisms and token-level processing suggests that moving beyond NTP may require rethinking attention itself.

Thus, alternatives to NTP are not only motivated by a desire for better reasoning and coherence, but also by the need for more efficient and scalable inference.

### 2.4 Training-Time Failures: Misaligned Supervision in Teacher-Forcing

A deeper issue arises during training. Models are typically trained using teacher-forcing, where they learn to predict the next token given the true previous tokens. As [Bachmann and Nagarajan](#page-16-0) [\(2024\)](#page-16-0) argue, this setup can cause models to learn spurious shortcuts, a phenomenon they call the "Clever Hans" effect. Instead of learning to plan, models exploit the revealed output prefix to guess plausible continuations without understanding the task. In lookahead tasks such as path-finding, this leads to in-distribution failures, where models trained to 100% accuracy fail completely at test time. Even for trivial tasks, teacher-forced models struggle to learn the correct planning mechanism when supervision is misaligned.

### 2.5 "Larger-than-token" representations exist inside Transformers

After outlining the numerous failures induced by NTP, it might be tempting to conclude that the Transformer architecture itself is fundamentally flawed. However, a compelling body of evidence suggests the opposite: the problem may not be the core model, but the constraints imposed by its own token-by-token decoding. While a Transformer's *output* is a simple, sequential stream of tokens, its *internal* latent states exhibit a remarkable degree of sophistication and foresight.

Researchers have found that internal embeddings in LLMs naturally form "larger-than-token" abstractions, with specific neurons or activation patterns corresponding to multi-token concepts, like people [\(Ghandeharioun et al.](#page-17-2) [2024\)](#page-17-2), places [\(Templeton et al.](#page-22-0) [2024\)](#page-22-0), or complex terms [\(Kaplan et al.](#page-20-3) [2025\)](#page-20-3). This suggests that transformers learn to reason with high-level semantic units, even when only trained to predict the next token.

Furthermore, Future Lens [\(Pal et al.](#page-21-9) [2023\)](#page-21-9), has shown that a single hidden state can anticipate multiple future tokens with surprising accuracy. Using linear probes on models like GPT-J-6B, they show that middlelayer activations can predict two or three tokens ahead, proving that transformers implicitly build multi-step plans long before they are decoded. The model isn't as myopic as its output suggests; it's actively planning ahead.

In short, the limitations of NTP may not stem from a model's inability to represent complex ideas, but from the constraint of having to express them one subword at a time. The following sections survey methods that explicitly try to break this bottleneck.

#### *Motivation Summary*

Together, these limitations point toward a fundamental inadequacy in NTP as a general-purpose generative paradigm. Consequently, this survey explores emerging alternatives—ranging from multi-token and latent-space decoding to non-autoregressive training—and outlines how they aim to bridge the gap between token-level generation and idea-level reasoning.

## 3 Scope

This survey was conducted through a systematic review of recent literature on alternatives to next-token prediction in language models. We searched major NLP venues including ACL, EMNLP, ICLR, NeurIPS, and ICML, as well as prominent preprint repositories (arXiv) covering the period from 2020 to 2025. We applied inclusion criteria focusing on methods that explicitly challenge or modify the standard next-token prediction paradigm—that is, approaches that move beyond predicting individual subword tokens to instead generate or predict "larger-than-token" units such as multiple tokens simultaneously, sentence-level representations, or global structural plans. We prioritized methods that fundamentally alter the generative process itself rather than optimizing within the existing token-by-token framework. We explicitly exclude attention mechanism variants such as Grouped Query Attention (GQA), Multi-Query Attention (MQA), and other architectural optimizations surveyed by [Brauwers and Frasincar](#page-16-5) [\(2023\)](#page-16-5) and [Roy et al.](#page-21-6) [\(2021\)](#page-21-6). While these innovations improve computational efficiency, they fundamentally operate within the NTP paradigm. Our focus is on methods that challenge the token-level generation paradigm itself, not those that optimize within it. Papers were excluded if they focused solely on computational efficiency improvements, retrieval augmentation or prompt engineering.

Based on our survey, we categorise the alternatives to NTP into five broad families:

- Multi-Token Prediction (MTP) changes the prediction target from a single token to a block of future tokens, typically using a shared context representation to feed multiple output heads.
- Plan-then-Generate (PtG) introduces a distinct, two-stage process where a global, high-level plan is generated upfront to guide the subsequent token-by-token generation.
- Latent Reasoning (LR) shifts the core autoregressive process into a continuous latent space, where the model's primary task is to generate an evolving sequence of latent states. These latent states are then used to predict the next sequence of tokens.
- Continuous Generation Approaches (CG) replace left-to-right autoregressive generation with parallel, iterative refinement processes over a *global representation* of the entire output, including diffusion, flow matching, and energy-based methods. Instead of autoregressive token prediction, tokens are produced through multiple rounds of simultaneous refinement across all positions in the output window.

| Category                               | Definition                                                                                                                                               | Representative Papers                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |  |
|----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--|
| Multi-Token<br>Prediction              | Generates several future tokens at<br>once from some shared latent space<br>("trunk").                                                                   | • Qi et al. (2020) — ProphetNet<br>• Gloeckle et al. (2024) — Better & Faster LLMs<br>via Multi-token Prediction<br>• Ahn et al. (2025) — Efficient Joint Prediction of<br>Multiple Future Tokens<br>• DeepSeek-AI et al. (2025) — DeepSeek-V3 Tech<br>nical Report                                                                                                                                                                                                                                                                                    |  |
| Plan-then-Generate                     | Introduces a distinct, two-stage<br>process where a global, high-level<br>plan is generated upfront to guide<br>subsequent token-by-token<br>generation. | • Su et al. (2021) — Plan-then-Generate<br>• Yin et al. (2024) — Semformer<br>• Lovelace et al. (2024) — DGLM<br>• Zhang et al. (2024) — PLANNER                                                                                                                                                                                                                                                                                                                                                                                                       |  |
| Latent Reasoning                       | Generates continuous latent vectors<br>instead of, or alongside, discrete<br>tokens.                                                                     | • Hao et al. (2024) — COCONUT<br>• Geiping et al. (2025) — Latent Reasoning<br>• LCM team et al. (2024) — Large Concept Models<br>• Tack et al. (2025) — CoCoMix                                                                                                                                                                                                                                                                                                                                                                                       |  |
| Continuous<br>Generation<br>Approaches | Denoises a noisy latent sequence<br>over multiple steps instead of<br>generating left-to-right.                                                          | • Li et al. (2022) — Diffusion-LM<br>• Ye et al. (2025) — Multi-Granularity Diffusion<br>Modeling<br>• Shabalin et al. (2025) — TEncDM<br>• Nie et al. (2025) — Scaling Masked Diffusion<br>• Arriola et al. (2025) — Block Diffusion<br>• Gemini<br>Diffusion<br>—<br>https://deepmind.google/<br>models/gemini-diffusion/<br>• LLaDA<br>—<br>https://ml-gsai.github.io/<br>LLaDA-demo/<br>• Lipman et al. (2023) — Flow Matching<br>• Hu et al. (2024) — Flow Matching for Text<br>• Xu et al. (2025) — EDLM<br>• Deng et al. (2020) — Residual EBMs |  |
| Non-Transformer<br>Architectures       | Models that inherently sidestep<br>token-by-token autoregression<br>through different core mechanics,<br>such as recurrent states or joint<br>embedding. | • Gu and Dao (2024) — Mamba<br>• Assran et al. (2023) — I-JEPA<br>• Recurrent Neural Networks (RNNs/LSTMs)<br>• Huang et al. (2025) — LLM-JEPA                                                                                                                                                                                                                                                                                                                                                                                                         |  |

Table 1 Taxonomy of alternatives to Next Token Prediction in transformers.

• Non-Transformer Architectures (NTA) employ alternative model backbones (e.g., State Space Models) whose inherent mechanics for sequence processing naturally sidestep the NTP paradigm by not requiring to generate tokens explicitly as a sequence.

Based on the families, we illustrate a taxonomy in Figure [2,](#page-5-0) and synthesizes insights from each method. Our goal is to provide a roadmap for researchers exploring how language models might move beyond tokenlevel generation—toward models that can plan, reason, and communicate more like humans.

While survey papers exist for each of these families, to our knowledge, no paper has explicitly unified these into a common taxonomy within the scope of alternatives to NTP. Table [2](#page-5-1) demonstrates that substantial prior work has examined individual categories—particularly Plan-then-Generate and Continuous Generation Approaches approaches—validating our taxonomic divisions while highlighting the gap in unified analysis across all five families. While these works validate the importance of individual approaches, they do not examine the common thread that unites them: the fundamental challenge to token-by-token generation that motivates our taxonomic framework.

| Paper Name                                                                                          | Category                                       |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------|
| Large Language Models for Planning: A Comprehensive and<br>Systematic Survey (Cao et al. 2025)      | Plan-then-Generate                             |
| PlanGenLLMs: A Modern Survey of LLM Planning Capabilities<br>(Wei et al. 2025)                      | Plan-then-Generate                             |
| A Survey of Diffusion Models in Natural Language Processing<br>(Zou et al. 2023)                    | Continuous Generation Approaches               |
| Diffusion Models for Non-autoregressive Text Generation: A<br>Survey (Li et al. 2023)               | Continuous Generation Approaches               |
| Energy-Based Models with Applications to Speech and Language<br>Processing (Ou 2024)                | Continuous Generation Approaches               |
| A Survey on Latent Reasoning (Zhu et al. 2025)                                                      | Latent Reasoning                               |
| Next Token Prediction Towards Multimodal Intelligence: A<br>Comprehensive Survey (Chen et al. 2024) | Multi-Token Prediction (sectional<br>coverage) |

<span id="page-5-1"></span>Table 2 Survey papers aligned with the families defined in this paper.

![](_page_5_Figure_2.jpeg)

<span id="page-5-0"></span>Fig. 2 Taxonomy of alternatives to next-token prediction (NTP)

## 4 Multi-token prediction

### 4.1 Definition

To accelerate inference and encourage short-term planning, Multi-Token Prediction (MTP) models change the prediction target from a single token to a block of *k* future tokens. This is typically achieved by using a shared context representation (a "trunk") to feed multiple parallel output heads, each predicting a different future token. This aims to improve computational efficiency and greedy generation. Figure [3](#page-5-2) illustrates this architecture.

![](_page_5_Figure_7.jpeg)

<span id="page-5-2"></span>Fig. 3 High-level architecture of a Multi-Token Prediction (MTP) model. A shared "trunk" processes the input context and feeds a representation to a decoder head, which generates multiple future tokens in parallel.

Formally, the probability is calculated as

$$P(x_{t+1:t+k} \mid x_{\leq t}) = \prod_{i=1}^{k} P(x_{t+i} \mid h_t)$$

where the shared trunk representation is h<sup>t</sup> = ftrunk(x<sup>≤</sup>t).

This setup breaks the strict chain rule of next-token prediction while also allowing for parallel decoding [\(Santilli et al.](#page-22-2) [2023\)](#page-22-2).

### 4.2 Key Approaches

Table [3\)](#page-6-0) compares the key approaches for MTP in terms of the trunk, MTP head and number of predicted tokens. We now present these approaches in detail. [Qi et al.](#page-21-10) [\(2020\)](#page-21-10) first popularized this strategy with Prophet-Net, which uses an n-stream self-attention mechanism to predict the next n tokens in parallel from a shared context stream (trunk). Each stream acts as an MTP head conditioned on the same internal state, enabling long-range planning while maintaining compatibility with standard inference.

[Gloeckle et al.](#page-19-1) [\(2024\)](#page-19-1) extend this idea from encoder-decoder models like ProphetNet to large-scale autoregressive LLMs by training a standard Transformer (trunk) with multiple output heads, each predicting a separate future token. Unlike ProphetNet, which uses offset attention streams, these heads are trained in parallel from a shared representation and used only during training unless speculative decoding is enabled. Despite its simplicity, this method improves sample efficiency and enables speculative decoding without architectural changes at inference. Notably, MTP heads are trained jointly, but only the next-token head is used at test time. Their 13B model achieves up to 17% higher accuracy on MBPP and a 3× speedup in decoding, while also fostering stronger induction capabilities and reasoning.

[Ahn et al.](#page-16-6) [\(2025\)](#page-16-6) propose Joint Token Prediction (JTP), which improves upon prior MTP variants by modeling the joint distribution of future tokens rather than treating them as conditionally independent. Like previous methods, JTP uses a shared Transformer trunk, but introduces a lightweight attention module ("Fetch") to process teacher-forced tokens and refine the trunk's output before feeding it to the MTP head. This bottleneck forces the trunk to encode richer multi-step planning signals. JTP outperforms other MTP methods on synthetic reasoning benchmarks with fewer parameters and minimal computational overhead.

MTP is commonly used as an auxiliary objective during training. [DeepSeek-AI et al.](#page-16-7) [\(2025\)](#page-16-7) show that adding MTP heads during training—and discarding them at inference—improves generalization across benchmarks, even in 200B+ models. Here, the shared Transformer trunk receives gradients from multiple future-token heads, encouraging broader temporal representations. When retained at inference, these heads enable speculative decoding: DeepSeek reports that 85–90% of the speculative proposed tokens are accepted, significantly accelerating generation with minimal degradation in quality.

| Model            | Trunk                                                     | MTP Head(s)                                                    | Number<br>of<br>Predicted<br>Tokens |
|------------------|-----------------------------------------------------------|----------------------------------------------------------------|-------------------------------------|
| ProphetNet       | Transformer encoder (seq2seq;<br>encoder is shared trunk) | Offset<br>decoder<br>streams<br>for<br>future token prediction | 1 - 3                               |
| Gloeckle et al.  | Transformer trunk                                         | Independent<br>heads<br>for<br>each<br>future token            | 1 - 32                              |
| JTP (Ahn et al.) | Transformer trunk                                         | Fetch module + joint head for<br>joint token prediction        | 1 - 8                               |
| DeepSeek-v3      | Transformer trunk                                         | MTP heads (discarded or used<br>for speculative decoding)      | 1 - 2                               |

<span id="page-6-0"></span>Table 3 Comparison of key MTP approaches in terms of the trunk structure, head design, and distinguishing features.

### 4.3 Failure Modes

MTP commonly fails at the following:

• Limited planning depth: Despite modeling multiple tokens, MTP often focuses on short-term future steps, lacking explicit mechanisms for deeper hierarchical or global planning.

- Architectural inflexibility: Integrating joint prediction heads (e.g., JTP's Fetch module) may complicate training and require additional tuning to balance losses across heads.
- Speculative decoding tradeoff: When used at inference, speculative decoding introduces a trade-off between speed, accuracy and cost.

### 4.4 Discussion

Multi-token prediction (MTP) offers a simple, compatible extension to next-token prediction by forecasting blocks of future tokens instead of one at a time. This enables short-term planning and partial parallelization, addressing NTP's sequential bottleneck without major architectural changes.

However, these models often only look 4-5 tokens into the future, and require new training setups that are not easily transferred to current models.

Overall, MTP improves efficiency and token-level foresight but lacks mechanisms for truly global planning or long-range structure.

## 5 Plan-then-Generate

### 5.1 Definition

While MTP retains NTP's original formulation of generating a sequence one token at a time, plan-thengenerate offers an alternative. Instead of generating text greedily from left to right, Plan-then-Generate (PtG) models introduce a high-level planning stage to guide subsequent token generation. This two-stage process is depicted in Figure [4.](#page-7-0) Broadly, PtG systems can be categorized as symbolic—which generate structured, interpretable plans—or latent, which learn abstract, continuous representations of global intent.

![](_page_7_Figure_9.jpeg)

<span id="page-7-0"></span>Fig. 4 The PtG framework. A high-level plan is created, which is then used alongside the original input to guide the generator in producing the final tokens.

The generation process has two stages:

- Planning: Generate a high-level abstract plan z from input context c
- Generation: Generate the output sequence y conditioned on c and z

Or, formally -

$$z \sim P_{\text{planner}}(z \mid c) \tag{2}$$

$$y \sim P_{\text{generator}}(y \mid z, c) = \prod_{i=1}^{N} P(y_i \mid y_{< i}, z, c)$$
 (3)

We categorize PtG systems along three key axes:

- Hierarchy Unit: What level of abstraction the plan operates on (e.g., slot, sentence, paragraph)
- Planner Module: How the plan is created (e.g., CRF, diffusion, variational autoencoder)
- Conditioning Strategy: How the plan influences decoding

#### *Conditioning Strategies.*

The *conditioning strategy* defines how the generated plan is used to steer generation:

- Prepending latent tokens: Learned embeddings are inserted as special tokens between prompt and output (e.g., Semformer).
- Cross-attention to plan: The decoder attends directly to the symbolic plan, allowing fine-grained alignment (e.g., PlanGen).

- Soft prompt from embedding: The plan is mapped into soft prompt vectors that bias decoding (e.g., DGLM).
- Adapter-based injection: Plan vectors are fed into lightweight adapter modules within a frozen decoder (e.g., Cornille et al.).
- Per-layer latent fusion: At each transformer layer, a fixed plan vector is projected and concatenated to every token's hidden state, providing persistent global conditioning throughout decoding (e.g., PLANNER).

### 5.2 Representative Papers

### Symbolic Planning Models

Early PtG work in structured data-to-text generation [\(Puduppully and Lapata](#page-21-14) [2021;](#page-21-14) [Chen et al.](#page-16-12) [2020;](#page-16-12) [Li](#page-20-12) [et al.](#page-20-12) [2023\)](#page-20-12) employed symbolic plans to select and order information before realization. PlanGen [\(Su et al.](#page-22-1) [2021\)](#page-22-1) predicts a sequence of content slots from RDF triples using a CRF, which a BART model then verbalizes. LLM+P [\(Liu et al.](#page-20-13) [2023\)](#page-20-13) generalizes this idea to classical planning: an LLM formalizes a task into a structured PDDL program, which an external planner solves before the LLM verbalizes the result.

These systems exemplify *neuro-symbolic* PtG: interpretable, modular, and structurally constrained, but limited by the need for symbolic input formats and task-specific schemas.

### Latent Planning Models

Recent PtG models replace symbolic plans with learned latent representations, *i.e.*, continuous vectors or discrete embeddings that encode global intentions without requiring hand-crafted structure.

#### *Semformer*

[\(Yin et al.](#page-23-2) [2024\)](#page-23-2) learns special tokens that reconstruct sentence embeddings, inserted between prompt and output to provide lightweight planning signals.

#### *DGLM*

[\(Lovelace et al.](#page-20-4) [2024\)](#page-20-4) samples an abstract intent vector from a diffusion model over Sentence-T5 latents, which is transformed into a soft prompt that conditions decoding.

### *PLANNER*

[\(Zhang et al.](#page-23-3) [2024\)](#page-23-3) encodes an entire paragraph into a latent vector using a VAE and denoises it via diffusion. The final plan conditions a decoder to improve structure and diversity.

### *Cornille et al.*

[\(Cornille et al.](#page-16-13) [2024\)](#page-16-13) cluster sentence embeddings into discrete writing actions. These serve as modular planning units and are injected into a frozen LLM via adapter layers. Externally trained planners outperform internal ones in structuring long-form outputs.

These methods retain the abstraction benefits of symbolic planning while improving scalability and flexibility.

#### *Broader Applications.*

While this survey focuses on PtG for text generation, similar strategies have been applied to multi-agent planning [\(Wang et al.](#page-23-10) [2024\)](#page-23-10) and retrieval-augmented generation [\(Lee et al.](#page-20-14) [2024;](#page-20-14) [Lyu et al.](#page-20-15) [2024\)](#page-20-15). These extensions are outside the scope of this review but demonstrate PtG's growing influence beyond generation.

These methods scale PtG to open-domain settings but often sacrifice interpretability and simplicity in exchange.

## 5.3 Failure Modes

Despite architectural elegance, the following vulnerabilities have been reported for current PtG methods:

| Model                                     | Hierarchy Unit                           | Planner Module                   | Conditioning Strategy        |
|-------------------------------------------|------------------------------------------|----------------------------------|------------------------------|
| PlanGen (Su et al. 2021)                  | Slot-level (symbolic)                    | CRF over RDF triples             | Cross-attention to plan      |
| Semformer (Yin et al.<br>2024)            | Sentence-level<br>(latent)               | Autoencoder (offline)            | Prepending latent tokens     |
| DGLM (Lovelace et al.<br>2024)            | Sentence-level<br>(latent)               | Diffusion over Sentence-T5       | Soft prompt from embedding   |
| PLANNER (Zhang et al.<br>2024)            | Paragraph-level<br>(latent)              | VAE + latent diffusion           | Decode conditioned on latent |
| Cornille et al. (Cornille<br>et al. 2024) | Sentence-level<br>(dis<br>crete actions) | Clustering + external classifier | Adapter-based plan injection |

Table 4 Comparison of Plan-then-Generate models by hierarchy unit, planning method, and conditioning strategy.

- Planner-Generator Misalignment: If the plan is poor or inconsistent with the generation objective, downstream outputs degrade significantly.
- Opaque Planning Representations: Latent planners are not easily interpretable or debuggable, making it difficult to identify errors.
- Rigidity of Symbolic Plans: Symbolic methods require structured inputs and fail to generalize across domains.
- Pipeline Complexity: Most PtG systems require multiple pretrained components (e.g., VAE, diffusion models, clustering pipelines), increasing training cost and brittleness.

### 5.4 Discussion

Plan-then-Generate offers a promising strategy to introduce global coherence and task structure into generation, mitigating the myopia of next-token decoding. However, current implementations introduce steep engineering and alignment costs. Symbolic planners lack scalability, while latent planners introduce interpretability and reliability challenges. To become practical, PtG must evolve toward lighter, robust planning modules with end-to-end trainability and alignment guarantees.

## 6 Latent Reasoning

### 6.1 Definition

Latent Reasoning (LR) models replace token-level generation with autoregression over latent states, shifting the core generative loop into a continuous space. This addresses the granularity mismatch between subword tokens and high-level semantics, allowing models to operate at the level of sentences, thoughts, or concepts.

We group LR methods into two categories.

#### <span id="page-9-0"></span>Latent Autoregression

These models generate a sequence of latent vectors and decode them into text afterward:

$$P(z \mid x) = \prod_{i=1}^{N'} P(z_i \mid z_{< i}, f_{\text{enc}}(x))$$
(4)

$$P(y \mid z) = \prod_{i=1}^{N'} P(y_i \mid z_i)$$
 (5)

SentenceVAE [\(An et al.](#page-16-14) [2024\)](#page-16-14) encodes each sentence into a latent vector and autoregressively predicts the next. A decoder reconstructs each latent into a sentence. Compared to token-level baselines, it improves inference speed (2–3×), perplexity (46–75%), and memory use (86–91% reduction).

Large Concept Models (LCMs) [\(LCM team et al.](#page-20-6) [2024\)](#page-20-6) scale this approach, generating one "concept" vector per sentence to enable long-range abstraction and reduce sequence length.

CoCoMix [\(Tack et al.](#page-23-4) [2025\)](#page-23-4) interleaves latent concept vectors (from a pretrained autoencoder) with token decoding, enriching each step with high-level semantic context. This improves sample efficiency and performance on reasoning tasks.

#### Latent Chain-Of-Thought

Here, the model refines a latent state over several internal steps before emitting a token. The steps indicate the chain of thought.

$$h_i^{(r)} = f_{\text{core}}(h_i^{(r-1)}, x) \tag{6}$$

$$P(y_i \mid y_{< i}, x) = f_{\text{out}}(h_i^{(R)})$$
(7)

Latent Reasoning [\(Geiping et al.](#page-19-2) [2025\)](#page-19-2) introduces an inner loop that applies a fixed "core" module multiple times before token generation. This allows more computation without increasing model size, scaling inference along a new axis: internal iteration.

Coconut [\(Hao et al.](#page-20-5) [2024\)](#page-20-5) performs latent reasoning between text segments, enabling breadth-first exploration of output trajectories before committing to a token sequence.

Together, these models move beyond discrete decoding, enabling generation over semantic units like sentences, thoughts, or concepts.

| Model                   | Mechanism                                           | Token Unit                | Key Distinction                                                 | Output Format               |
|-------------------------|-----------------------------------------------------|---------------------------|-----------------------------------------------------------------|-----------------------------|
| SentenceVAE             | Latent Autore<br>gression                           | Sentence<br>embed<br>ding | Autoregresses over sentence vec<br>tors with a base LLM decoder | Discrete<br>(sen<br>tences) |
| LCM                     | Latent Autore<br>gression                           | Sentence<br>embed<br>ding | Fully integrated latent autoregres<br>sive architecture         | Discrete<br>(sen<br>tences) |
| CoCoMix                 | Latent Autore<br>gression                           | Latent concept vec<br>tor | Predicts token and concept vector at<br>every step              | Discrete (tokens)           |
| Latent<br>Rea<br>soning | Latent<br>Chain<br>Continuous thought<br>of Thought |                           | Internal<br>loop<br>increases<br>compute<br>before each token   | Discrete (tokens)           |
| Coconut                 | Latent<br>Chain<br>of Thought                       | Continuous thought        | Latent<br>planning<br>between<br>text<br>chunks                 | Mixed                       |

Table 5 Comparison of Latent Reasoning Models.

### 6.2 Failure Modes

Despite enabling generation over higher-level abstractions, latent reasoning models face distinct limitations:

- Opaque Generation Process: Autoregression occurs in latent space, making it difficult to interpret, debug, or steer generation.
- Latent Misalignment: Poorly trained or misaligned latent encoders/decoders lead to degraded outputs or semantic drift during decoding.
- Training Complexity: Many models (e.g., SentenceVAE, LCM, CoCoMix) rely on complex multi-stage training involving external encoders, autoencoders, or diffusion priors.
- Evaluation Instability: Outputs often require post-decoding reconstruction, introducing noise that complicates evaluation and benchmarking.
- Limited Robustness: Out-of-distribution latent vectors (e.g., hallucinated concepts) may decode to nonsensical or unsafe outputs without explicit token-level grounding.

### 6.3 Discussion

Latent Reasoning offers a compelling departure from next-token prediction by shifting generation to a space of abstract semantic units. These methods achieve greater speed and generalization by reducing sequence length and operating at coarser granularity. However, they introduce new difficulties around interpretability, training complexity, and latent stability. Without token-level grounding, these systems can be fragile to errors in latent encoding, and their benefits are often offset by costly multi-stage pipelines. Future work should explore tighter integration between latent representations and discrete outputs, improving transparency and robustness while retaining semantic abstraction.

## 7 Continuous Generation Approaches

### 7.1 Definition

Continuous Generation approaches fundamentally depart from sequential token production by treating text generation as a global optimization problem. Rather than producing tokens one-by-one (whether in token space or latent space), these methods initialize the entire output simultaneously and refine it through iterative transformations. This paradigm shift from sequential to parallel generation enables three key advantages: (1) global planning and revision, (2) mitigation of error accumulation, and (3) bidirectional refinement where later context can influence earlier positions.

All continuous generation methods share a common framework: they define a trajectory from noise (or random initialization) to coherent text through multiple refinement steps. The specific mechanism varies—diffusion uses stochastic denoising, flow matching learns deterministic paths, and energy-based models follow gradient descent in an energy landscape—but the core principle remains: generate everything at once, then refine globally.

Note that while Latent Autoregression [6.1](#page-9-0) shifts generation to a continuous space, it maintains the sequential, left-to-right generation paradigm. This distinguishes it from the approaches in this section, which abandon sequential processing entirely in favor of parallel refinement.

### 7.2 Diffusion-Based Models

Diffusion represents the most established continuous generation approach, treating generation as an iterative denoising process. Instead of emitting one token at a time, these models start with a noisy version of the full output and refine it over multiple steps.

However, adapting diffusion to language is nontrivial due to the discrete nature of text. Figure [5](#page-11-0) provides a conceptual overview of the two main approaches:

- Continuous diffusion Operates in embedding or latent spaces.
- Discrete diffusion Operates over tokens or logits via masking and corruption.

![](_page_11_Figure_10.jpeg)

<span id="page-11-0"></span>Fig. 5 Comparison of text diffusion models. (a) A Discrete Text Diffusion Model starts with masked tokens and iteratively fills them in over N steps. (b) A Continuous Text Diffusion Model starts with random noise in an embedding space and iteratively denoises the latent vectors, which are then decoded into the final text.

A dedicated survey by [Li et al.](#page-20-11) [\(2023\)](#page-20-11) reviews the technical landscape of text diffusion models, covering noise schedules, conditioning, and integration with pretrained LMs.

Table [6](#page-13-0) categorizes recent Continuous Generation approaches along several dimensions.

### 7.3 Representative Papers

#### Continuous Diffusion Models

These models apply noise to continuous representations and train a denoiser to recover the original signal.

Diffusion-LM [\(Li et al.](#page-20-7) [2022\)](#page-20-7) generates word embeddings via iterative denoising, allowing fine-grained control over syntax and semantics.

TEncDM [\(Shabalin et al.](#page-21-11) [2025\)](#page-21-11) denoises in a frozen encoder's latent space (e.g., BERT), capturing sentence-level semantics more effectively with fewer steps.

### Discrete Diffusion Models

Discrete models operate directly on tokens or logits, generalizing masked language modeling into a multi-step refinement process.

MGDM [\(Ye et al.](#page-23-5) [2025\)](#page-23-5) improves symbolic reasoning by denoising from multiple noisy views, mitigating subgoal imbalance in AR models.

Block Diffusion[\(Arriola et al.](#page-16-8) [2025\)](#page-16-8) blends diffusion with autoregression by refining fixed-length blocks. This supports scalable, partially parallel decoding with token caching.

Mercury [\(Labs et al.](#page-20-16) [2025\)](#page-20-16) scales discrete diffusion to commercial deployment, achieving 1100 tokens/sec with latencies under 25ms. Its coarse-to-fine, parallel denoising rivals top AR models in quality, offering a viable alternative for real-time coding and FIM tasks.

#### Emerging Directions

Large-scale efforts like Gemini Diffusion[1](#page-12-0) and LLaDA[2](#page-12-1) signal growing industry investment in diffusionbased language modeling, especially for multimodal and instruction-tuned use cases.

### 7.4 Flow Matching Models

Flow matching [\(Lipman et al.](#page-20-8) [2023\)](#page-20-8) offers an alternative to diffusion that learns deterministic trajectories between noise and data distributions. Unlike diffusion's stochastic paths, flow matching constructs optimal transport maps that can be more sample-efficient. The framework has been successfully extended beyond its original formulation to simulation-based inference [\(Dax et al.](#page-17-5) [2023\)](#page-17-5) and structured data like graphs [\(Eijkel](#page-17-6)[boom et al.](#page-17-6) [2025\)](#page-17-6). Recent work has specifically adapted flow matching to text generation [\(Hu et al.](#page-20-9) [2024\)](#page-20-9), treating sentences as points in a continuous semantic space and learning smooth transformations between random initialization and meaningful text. This approach entirely sidesteps tokenization by operating in embedding space throughout the generation process.

### 7.5 Energy-Based Models

Energy-based models (EBMs) define generation through an energy landscape where valid outputs correspond to low-energy configurations, fundamentally departing from token-by-token generation. Originally developed in statistical physics and later adopted in machine learning for vision tasks, EBMs learn a scalar energy function that assigns compatibility scores to entire configurations. Recent adaptations to NLP demonstrate multiple pathways for incorporating energy functions into language generation. Energy-based Diffusion Language Models (EDLM) [\(Xu et al.](#page-23-6) [2025\)](#page-23-6) introduce EBM formulations within discrete diffusion models, enabling sequence-level energy modeling at each diffusion step while leveraging pretrained LLMs through noise contrastive estimation. Energy-Based Reward Models (EBRM) [\(Lochab and Zhang](#page-20-17) [2025\)](#page-20-17) enhance LLM alignment by replacing scalar rewards with energy functions that better capture distributional uncertainty in human preferences, integrating seamlessly with existing alignment pipelines. Energy-Based Transformers (EBT) [\(Gladstone et al.](#page-19-3) [2025\)](#page-19-3) reframe the transformer architecture itself as an EBM, learning energy functions to assess compatibility between context and generated text. Finally, autoregressive variants like Residual EBMs [\(Deng et al.](#page-17-3) [2020\)](#page-17-3) impose energy-based post-processing on pretrained LLM outputs through contrastive objectives. These approaches collectively demonstrate that holistic sequence scoring via energy functions offers a principled alternative to the local, incremental decisions of NTP.

### 7.6 Failure Modes

- Quality gap vs. AR models: Despite improvements, most continuous generation models underperform strong autoregressive baselines in terms of fluency and coherence. Diffusion models require heavy tuning or distillation; flow matching models like FlowSeq show competitive but not superior performance; and energy-based models often struggle with mode coverage and sampling quality.
- Inference cost and parallelism tradeoff: While continuous generation is inherently parallelizable, the iterative refinement process incurs significant costs. Diffusion models require dozens of denoising steps; flow matching needs multiple ODE solver steps despite being deterministic; and energy-based models require expensive MCMC sampling or gradient-based optimization. Without architectural optimizations, all are slower than autoregressive decoding.
- Fixed-length limitations: Most continuous generation models struggle with variable-length outputs. Diffusion models like Diffusion-LM and MGDM require padding or truncation; flow matching operates on fixed-dimensional embeddings; and energy-based models typically define energy over fixed-size configurations.

<span id="page-12-0"></span><https://deepmind.google/models/gemini-diffusion/>

<span id="page-12-1"></span><https://ml-gsai.github.io/LLaDA-demo/>

| Model           | Approach Type | Latent Space           | Granularity    | Update Mechanism             |
|-----------------|---------------|------------------------|----------------|------------------------------|
| Diffusion-LM    | Diffusion     | Word embeddings        | Token-level    | Stochastic<br>denois<br>ing  |
| TEncDM          | Diffusion     | Frozen encoder latents | Sentence-level | Stochastic<br>denois<br>ing  |
| MGDM            | Diffusion     | Token logits           | Token-level    | Discrete denoising           |
| Block Diffusion | Diffusion     | Token blocks           | Block-level    | Block-wise<br>refine<br>ment |
| Mercury         | Diffusion     | Token logits           | Token-level    | Parallel denoising           |
| FlowSeq         | Flow Matching | Text embeddings        | Sequence-level | Deterministic flow           |
| EDLM            | Energy-Based  | Token logits           | Token-level    | Energy<br>minimiza<br>tion   |
| EBRM            | Energy-Based  | Reward space           | Sequence-level | Gradient descent             |
| Residual EBMs   | Energy-Based  | Output logits          | Token-level    | Contrastive energy           |

<span id="page-13-0"></span>Table 6 Comparison of Continuous Generation Approaches by type, latent space, granularity, and update mechanism.

- Poor interpretability: Generation trajectories are opaque across all approaches—diffusion follows stochastic paths in embedding space, flow matching traces deterministic but uninterpretable curves, and energy-based models descend abstract energy landscapes with no clear reasoning traces.
- Complex training pipelines: These models require specialized components that increase implementation overhead. Diffusion needs noise schedulers and denoising objectives; flow matching requires ODE solvers and transport cost optimization; energy-based models need contrastive sampling strategies and careful initialization to avoid mode collapse.

### 7.7 Discussion

Continuous Generation approaches break from the rigidity of token-by-token autoregressive generation by enabling global, parallel reasoning and more flexible generation paths. Each approach offers distinct advantages: Diffusion-LM supports rich control signals, while discrete methods like Mercury scale to production-level throughput; flow matching offers deterministic, theoretically grounded trajectories that can be more sample-efficient than stochastic diffusion; and energy-based models provide a principled framework for incorporating global constraints and preferences through holistic sequence scoring. Yet the cost of these benefits is high: slow inference, interpretability challenges, and complex training procedures remain core obstacles.

## 8 Non-Transformer Architectures

## 8.1 Definition

While previous approaches modify the generative objective within Transformers, this category targets a deeper shift: changing the model architecture itself. Non-Transformer Architectures (NTA) bypass the limitations of NTP by adopting fundamentally different sequence modeling mechanisms.

### 8.2 Representative Papers

### Recurrent Neural Networks

Recurrent Neural Networks (RNNs) were the state-of-the-art NLP architecture before the Transformer [\(Mikolov et al.](#page-21-15) [2010\)](#page-21-15). These models — including LSTMs [\(Sundermeyer et al.](#page-22-3) [2012\)](#page-22-3) and GRUs [\(Chung et al.](#page-16-15) [2014\)](#page-16-15) — process input sequentially, maintaining a hidden state that summarizes prior context. Unlike transformers, which compute attention over the entire sequence, RNNs make predictions using only this evolving summary. This results in linear time complexity and an implicit latent-space abstraction over all observed inputs.

However, RNNs struggle with vanishing gradients and limited memory, making them hard to scale for long-range dependencies. Recent work revisits this paradigm with more scalable variants, such as state space models.

### State Space Models

State Space Models (SSMs) improve on RNNs by tracking sequence information using continuous signals instead of discrete steps. Modern implementations like Mamba [\(Gu and Dao](#page-17-4) [2024\)](#page-17-4) achieve linear-time inference while retaining strong modeling capacity.

SSMs address key Transformer NTP bottlenecks:

- Efficiency: Linear scaling with sequence length avoids O(n 2 ) attention cost.
- Abstraction: Continuous state evolution allows modeling over higher-level semantic units.

However, they remain underexplored in open-ended generation and bring their own challenges:

- Limited adoption: Few large-scale applications in general-purpose NLP.
- Opaque internals: Dynamics are difficult to inspect or interpret.
- Architectural fragility: Sensitive to hyperparameters and discretization schemes.

While SSMs rethink temporal modeling, the next category, JEPAs, rethinks prediction itself—moving away from token-level outputs entirely.

#### Joint Embedding Predictive Architectures

A more radical departure from NTP is offered by Joint Embedding Predictive Architectures (JEPAs), which model sequences via compatibility in a shared semantic space.

In vision, models like I-JEPA [\(Assran et al.](#page-16-9) [2023\)](#page-16-9) and V-JEPA [\(Bardes et al.](#page-16-16) [2024\)](#page-16-16) learn by reconstructing masked representations rather than raw inputs. This shifts supervision from low-level pixel-perfect reconstruction to high-level semantic consistency.

Data2vec [\(Baevski et al.](#page-16-17) [2022\)](#page-16-17) uses a similar approach across 3 separate domains of NLP, vision and audio by predicting contextual embeddings of masked inputs using a self-distillation loss. Without predicting tokens explicitly, it achieves competitive results across all 3 domains of language, vision, and speech.

LLM-JEPA [\(Huang et al.](#page-20-10) [2025\)](#page-20-10) extends JEPA principles directly to language model training by treating different modalities (text descriptions and code) as views of the same underlying knowledge. Unlike traditional NTP objectives, LLM-JEPA learns representations by ensuring that semantically equivalent text-code pairs can predict each other in embedding space, while preventing dimensional collapse. The primary limitation of LLM-JEPA is its reliance on naturally paired multi-view data (such as documentation-code pairs), which restricts its application compared to standard self-supervised objectives. Despite this constraint, the method achieves significant improvements over baseline finetuning across multiple benchmarks (NL-RX, GSM8K, Spider) and model families (Llama3, Gemma2), demonstrating that JEPA's success in vision can transfer to language when suitable multi-view datasets exist.

### 8.3 Failure Modes

But these benefits come with trade-offs:

- No explicit generation: Difficult to adapt to generative tasks without auxiliary decoders.
- Representation drift: Risk of collapse or over-smoothing during distillation.
- Evaluation mismatch: Embedding losses do not correlate cleanly with generative quality.

### 8.4 Discussion

Together, SSMs and JEPAs demonstrate two orthogonal routes away from NTP: one architectural, the other representational. While promising, both remain early-stage and face barriers in interpretability, generalization, and integration into practical generation systems.

## 9 Conclusion & Future Directions

Next-Token Prediction (NTP) has long been the foundational paradigm for large-scale language modeling based on Transformers. While it enables impressive fluency, a growing body of literature highlights that NTP is also a bottleneck, with its myopic, token-by-token nature contributing to failures in long-term planning, computational efficiency, and semantic abstraction. In response, a rich ecosystem of alternatives has emerged. This survey has categorized these approaches into five main families: Multi-Token Prediction (MTP), Plan-then-Generate (PtG), Latent Reasoning (LR), Continuous Generation Approaches (CG), and Non-Transformer Architectures (NTA).

### 9.1 Future Research Directions

#### *Multi-Token Prediction (MTP).*

Based on this survey, we see two opportunities in this context. First, *predict farther ahead*: study how performance changes as we increase k (the number of future tokens), using simple schedules (start small, grow k) and checks for when extra lookahead stops helping.

Secondly continue to *use MTP as an auxillary training method*: keep future-token heads during training to teach lookahead, even if only next-token decoding is used at test time.

However, it is important to note that a *fixed* k can never deliver truly global reasoning; longer documents and plans will always exceed any fixed horizon. Promising ideas include variable-length or adaptive horizons, and hierarchical heads that look ahead at different scales (phrases, sentences, sections).

#### *Plan-then-Generate (PtG).*

*Diverse planners*: move beyond generic embeddings to planners that capture discourse structure, key entities, or task steps, with evaluation focused on whether the generated text actually follows the plan. Secondly, further *hybrid architectures* of different planning modules should be explored, along with systematic studies of *adaptable time horizons*—plans that can flex between sentence-level, paragraph-level, or document-level guidance depending on task requirements.

#### *Latent Reasoning.*

*Diverse Architectures* that separate a small "reasoning core" from a lighter decoder, so we can add more internal thinking steps when needed. Secondly, improved *Encoders/decoders* that faithfully move between text and latent space, with simple checks that meaning is preserved. Thirdly, *non-Transformer models*, including state-space models and JEPA-style training, to predict in representation space rather than token space.

#### *Continuous Generation Approaches.*

*Compositional strategies*: combine diffusion with higher-level planning, for example by generating an outline of sections, entities, or steps and then refining the wording through a small number of denoising steps. This ensures the global structure is respected while keeping generation efficient.

Secondly, *memory-augmented diffusion*: pair diffusion with state-space memory to store long-context summaries in a recurrent module, while keeping attention over short windows. Diffusion can then refine current spans conditioned on this memory. Open questions include adaptive step counts, block-wise refinement with cache reuse, and training setups that balance global constraints (factuality, style) with local fluency.

## Limitations

This survey aims to provide a broad and structured overview of emerging alternatives to NTP in transformer models, despite some limitations. First, given the rapid pace of research in this area, our coverage may not include the most recent or unpublished advances, particularly those in proprietary or closed-source settings. Second, although we categorize alternatives along high-level axes (e.g., planning, token granularity, decoding strategy), the boundaries between categories are sometimes blurred. For example, some diffusion-based models also implement PtG, and some multi-token predictors incorporate latent semantic reasoning.

Moreover, our analysis focuses primarily on high-level paradigms that challenge the generative process of LLMs. Less emphasis is given to tokenization approaches, output head optimizations, or architectural innovations in the intermediate layers, which could meaningfully challenge the NTP paradigm. Finally, we do not present empirical benchmarking of these alternatives under controlled conditions; instead, we rely on results reported by the original authors.

## Acknowledgments

Portions of this manuscript were revised with the assistance of an AI-based editing tool (e.g., ChatGPT) for grammar and clarity. The authors are solely responsible for the content.

The visualizations used in this paper were created using Miro and Lucidchart.

## References

- <span id="page-16-14"></span>An, H., Chen, Y., Sun, Z., Li, X.: SentenceVAE: Enable Next-sentence Prediction for Large Language Models with Faster Speed, Higher Accuracy and Longer Context (2024). <https://arxiv.org/abs/2408.00655>
- <span id="page-16-9"></span>Assran, M., Duval, Q., Misra, I., Bojanowski, P., Vincent, P., Rabbat, M., LeCun, Y., Ballas, N.: Self-Supervised Learning from Images with a Joint-Embedding Predictive Architecture (2023). [https://arxiv.](https://arxiv.org/abs/2301.08243) [org/abs/2301.08243](https://arxiv.org/abs/2301.08243)
- <span id="page-16-2"></span>Ansar, W., Goswami, S., Chakrabarti, A.: A Survey on Transformers in NLP with Focus on Efficiency (2024). <https://arxiv.org/abs/2406.16893>
- <span id="page-16-8"></span>Arriola, M., Gokaslan, A., Chiu, J.T., Yang, Z., Qi, Z., Han, J., Sahoo, S.S., Kuleshov, V.: Block Diffusion: Interpolating Between Autoregressive and Diffusion Language Models (2025). [https://arxiv.org/abs/2503.](https://arxiv.org/abs/2503.09573) [09573](https://arxiv.org/abs/2503.09573)
- <span id="page-16-6"></span>Ahn, K., Lamb, A., Langford, J.: Efficient Joint Prediction of Multiple Future Tokens (2025). [https://arxiv.](https://arxiv.org/abs/2503.21801) [org/abs/2503.21801](https://arxiv.org/abs/2503.21801)
- <span id="page-16-4"></span>Ainslie, J., Lee-Thorp, J., Jong, M., Zemlyanskiy, Y., Lebrón, F., Sanghai, S.: GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints (2023). <https://arxiv.org/abs/2305.13245>
- <span id="page-16-5"></span>Brauwers, G., Frasincar, F.: A general survey on attention mechanisms in deep learning. IEEE Transactions on Knowledge and Data Engineering 35(4), 3279–3298 (2023) <https://doi.org/10.1109/tkde.2021.3126456>
- <span id="page-16-16"></span>Bardes, A., Garrido, Q., Ponce, J., Chen, X., Rabbat, M., LeCun, Y., Assran, M., Ballas, N.: Revisiting Feature Prediction for Learning Visual Representations from Video (2024). <https://arxiv.org/abs/2404.08471>
- <span id="page-16-17"></span>Baevski, A., Hsu, W.-N., Xu, Q., Babu, A., Gu, J., Auli, M.: data2vec: A General Framework for Selfsupervised Learning in Speech, Vision and Language (2022). <https://arxiv.org/abs/2202.03555>
- <span id="page-16-0"></span>Bachmann, G., Nagarajan, V.: The pitfalls of next-token prediction (2024). <https://arxiv.org/abs/2403.06963>
- <span id="page-16-3"></span>Beltagy, I., Peters, M.E., Cohan, A.: Longformer: The Long-Document Transformer (2020). [https://arxiv.org/](https://arxiv.org/abs/2004.05150) [abs/2004.05150](https://arxiv.org/abs/2004.05150)
- <span id="page-16-15"></span>Chung, J., Gulcehre, C., Cho, K., Bengio, Y.: Empirical Evaluation of Gated Recurrent Neural Networks on Sequence Modeling (2014). <https://arxiv.org/abs/1412.3555>
- <span id="page-16-12"></span>Chen, K., Li, F., Hu, B., Peng, W., Chen, Q., Yu, H.: Neural Data-to-Text Generation with Dynamic Content Planning (2020). <https://arxiv.org/abs/2004.07426>
- <span id="page-16-10"></span>Cao, P., Men, T., Liu, W., Zhang, J., Li, X., Lin, X., Sui, D., Cao, Y., Liu, K., Zhao, J.: Large Language Models for Planning: A Comprehensive and Systematic Survey (2025). <https://arxiv.org/abs/2505.19683>
- <span id="page-16-13"></span>Cornille, N., Moens, M.-F., Mai, F.: Learning to Plan for Language Modeling from Unlabeled Data (2024). <https://arxiv.org/abs/2404.00614>
- <span id="page-16-1"></span>Cosma, A., Ruseti, S., Radoi, E., Dascalu, M.: The Strawberry Problem: Emergence of Character-level Understanding in Tokenized Language Models (2025). <https://arxiv.org/abs/2505.14172>
- <span id="page-16-11"></span>Chen, L., Wang, Z., Ren, S., Li, L., Zhao, H., Li, Y., Cai, Z., Guo, H., Zhang, L., Xiong, Y., Zhang, Y., Wu, R., Dong, Q., Zhang, G., Yang, J., Meng, L., Hu, S., Chen, Y., Lin, J., Bai, S., Vlachos, A., Tan, X., Zhang, M., Xiao, W., Yee, A., Liu, T., Chang, B.: Next Token Prediction Towards Multimodal Intelligence: A Comprehensive Survey (2024). <https://arxiv.org/abs/2412.18619>
- <span id="page-16-7"></span>DeepSeek-AI, Liu, A., Feng, B., Xue, B., Wang, B., Wu, B., Lu, C., Zhao, C., Deng, C., Zhang, C., Ruan, C., Dai, D., Guo, D., Yang, D., Chen, D., Ji, D., Li, E., Lin, F., Dai, F., Luo, F., Hao, G., Chen, G., Li, G., Zhang, H., Bao, H., Xu, H., Wang, H., Zhang, H., Ding, H., Xin, H., Gao, H., Li, H., Qu, H., Cai, J.L., Liang, J., Guo, J., Ni, J., Li, J., Wang, J., Chen, J., Chen, J., Yuan, J., Qiu, J., Li, J., Song, J., Dong, K., Hu, K., Gao, K., Guan, K., Huang, K., Yu, K., Wang, L., Zhang, L., Xu, L., Xia, L., Zhao, L., Wang, L., Zhang,

- L., Li, M., Wang, M., Zhang, M., Zhang, M., Tang, M., Li, M., Tian, N., Huang, P., Wang, P., Zhang, P., Wang, Q., Zhu, Q., Chen, Q., Du, Q., Chen, R.J., Jin, R.L., Ge, R., Zhang, R., Pan, R., Wang, R., Xu, R., Zhang, R., Chen, R., Li, S.S., Lu, S., Zhou, S., Chen, S., Wu, S., Ye, S., Ye, S., Ma, S., Wang, S., Zhou, S., Yu, S., Zhou, S., Pan, S., Wang, T., Yun, T., Pei, T., Sun, T., Xiao, W.L., Zeng, W., Zhao, W., An, W., Liu, W., Liang, W., Gao, W., Yu, W., Zhang, W., Li, X.Q., Jin, X., Wang, X., Bi, X., Liu, X., Wang, X., Shen, X., Chen, X., Zhang, X., Chen, X., Nie, X., Sun, X., Wang, X., Cheng, X., Liu, X., Xie, X., Liu, X., Yu, X., Song, X., Shan, X., Zhou, X., Yang, X., Li, X., Su, X., Lin, X., Li, Y.K., Wang, Y.Q., Wei, Y.X., Zhu, Y.X., Zhang, Y., Xu, Y., Xu, Y., Huang, Y., Li, Y., Zhao, Y., Sun, Y., Li, Y., Wang, Y., Yu, Y., Zheng, Y., Zhang, Y., Shi, Y., Xiong, Y., He, Y., Tang, Y., Piao, Y., Wang, Y., Tan, Y., Ma, Y., Liu, Y., Guo, Y., Wu, Y., Ou, Y., Zhu, Y., Wang, Y., Gong, Y., Zou, Y., He, Y., Zha, Y., Xiong, Y., Ma, Y., Yan, Y., Luo, Y., You, Y., Liu, Y., Zhou, Y., Wu, Z.F., Ren, Z.Z., Ren, Z., Sha, Z., Fu, Z., Xu, Z., Huang, Z., Zhang, Z., Xie, Z., Zhang, Z., Hao, Z., Gou, Z., Ma, Z., Yan, Z., Shao, Z., Xu, Z., Wu, Z., Zhang, Z., Li, Z., Gu, Z., Zhu, Z., Liu, Z., Li, Z., Xie, Z., Song, Z., Gao, Z., Pan, Z.: DeepSeek-V3 Technical Report (2025). <https://arxiv.org/abs/2412.19437>
- <span id="page-17-3"></span>Deng, Y., Bakhtin, A., Ott, M., Szlam, A., Ranzato, M.: Residual Energy-Based Models for Text Generation (2020). <https://arxiv.org/abs/2004.11714>
- <span id="page-17-5"></span>Dax, M., Wildberger, J., Buchholz, S., Green, S.R., Macke, J.H., Schölkopf, B.: Flow Matching for Scalable Simulation-Based Inference (2023). <https://arxiv.org/abs/2305.17161>
- <span id="page-17-6"></span>Eijkelboom, F., Bartosh, G., Naesseth, C.A., Welling, M., Meent, J.-W.: Variational Flow Matching for Graph Generation (2025). <https://arxiv.org/abs/2406.04843>
- <span id="page-17-1"></span>Fu, T., Ferrando, R., Conde, J., Arriaga, C., Reviriego, P.: Why Do Large Language Models (LLMs) Struggle to Count Letters? (2024). <https://arxiv.org/abs/2412.18626>
- <span id="page-17-2"></span>Ghandeharioun, A., Caciularu, A., Pearce, A., Dixon, L., Geva, M.: Patchscopes: A Unifying Framework for Inspecting Hidden Representations of Language Models (2024). <https://arxiv.org/abs/2401.06102>
- <span id="page-17-4"></span>Gu, A., Dao, T.: Mamba: Linear-Time Sequence Modeling with Selective State Spaces (2024). [https://arxiv.](https://arxiv.org/abs/2312.00752) [org/abs/2312.00752](https://arxiv.org/abs/2312.00752)
- <span id="page-17-0"></span>Gemini Team, Georgiev, P., Lei, V.I., Burnell, R., Bai, L., Gulati, A., Tanzer, G., Vincent, D., Pan, Z., Wang, S., Mariooryad, S., Ding, Y., Geng, X., Alcober, F., Frostig, R., Omernick, M., Walker, L., Paduraru, C., Sorokin, C., Tacchetti, A., Gaffney, C., Daruki, S., Sercinoglu, O., Gleicher, Z., Love, J., Voigtlaender, P., Jain, R., Surita, G., Mohamed, K., Blevins, R., Ahn, J., Zhu, T., Kawintiranon, K., Firat, O., Gu, Y., Zhang, Y., Rahtz, M., Faruqui, M., Clay, N., Gilmer, J., Co-Reyes, J., Penchev, I., Zhu, R., Morioka, N., Hui, K., Haridasan, K., Campos, V., Mahdieh, M., Guo, M., Hassan, S., Kilgour, K., Vezer, A., Cheng, H.- T., Liedekerke, R., Goyal, S., Barham, P., Strouse, D., Noury, S., Adler, J., Sundararajan, M., Vikram, S., Lepikhin, D., Paganini, M., Garcia, X., Yang, F., Valter, D., Trebacz, M., Vodrahalli, K., Asawaroengchai, C., Ring, R., Kalb, N., Soares, L.B., Brahma, S., Steiner, D., Yu, T., Mentzer, F., He, A., Gonzalez, L., Xu, B., Kaufman, R.L., Shafey, L.E., Oh, J., Hennigan, T., Driessche, G., Odoom, S., Lucic, M., Roelofs, B., Lall, S., Marathe, A., Chan, B., Ontanon, S., He, L., Teplyashin, D., Lai, J., Crone, P., Damoc, B., Ho, L., Riedel, S., Lenc, K., Yeh, C.-K., Chowdhery, A., Xu, Y., Kazemi, M., Amid, E., Petrushkina, A., Swersky, K., Khodaei, A., Chen, G., Larkin, C., Pinto, M., Yan, G., Badia, A.P., Patil, P., Hansen, S., Orr, D., Arnold, S.M.R., Grimstad, J., Dai, A., Douglas, S., Sinha, R., Yadav, V., Chen, X., Gribovskaya, E., Austin, J., Zhao, J., Patel, K., Komarek, P., Austin, S., Borgeaud, S., Friso, L., Goyal, A., Caine, B., Cao, K., Chung, D.-W., Lamm, M., Barth-Maron, G., Kagohara, T., Olszewska, K., Chen, M., Shivakumar, K., Agarwal, R., Godhia, H., Rajwar, R., Snaider, J., Dotiwalla, X., Liu, Y., Barua, A., Ungureanu, V., Zhang, Y., Batsaikhan, B.-O., Wirth, M., Qin, J., Danihelka, I., Doshi, T., Chadwick, M., Chen, J., Jain, S., Le, Q., Kar, A., Gurumurthy, M., Li, C., Sang, R., Liu, F., Lamprou, L., Munoz, R., Lintz, N., Mehta, H., Howard, H., Reynolds, M., Aroyo, L., Wang, Q., Blanco, L., Cassirer, A., Griffith, J., Das, D., Lee, S., Sygnowski, J., Fisher, Z., Besley, J., Powell, R., Ahmed, Z., Paulus, D., Reitter, D., Borsos, Z., Joshi, R., Pope, A., Hand, S., Selo, V., Jain, V., Sethi, N., Goel, M., Makino, T., May, R., Yang, Z., Schalkwyk, J., Butterfield, C., Hauth, A., Goldin, A., Hawkins, W., Senter, E., Brin, S., Woodman, O., Ritter, M., Noland, E., Giang, M., Bolina, V., Lee, L., Blyth, T., Mackinnon, I., Reid, M., Sarvana, O., Silver, D., Chen, A., Wang, L., Maggiore, L., Chang, O., Attaluri, N., Thornton, G., Chiu, C.-C., Bunyan, O., Levine, N., Chung, T., Eltyshev, E., Si, X., Lillicrap, T., Brady, D., Aggarwal, V., Wu, B., Xu, Y., McIlroy, R., Badola, K., Sandhu, P., Moreira, E., Stokowiec, W., Hemsley, R., Li, D., Tudor, A., Shyam, P., Rahimtoroghi, E.,

Haykal, S., Sprechmann, P., Zhou, X., Mincu, D., Li, Y., Addanki, R., Krishna, K., Wu, X., Frechette, A., Eyal, M., Dafoe, A., Lacey, D., Whang, J., Avrahami, T., Zhang, Y., Taropa, E., Lin, H., Toyama, D., Rutherford, E., Sano, M., Choe, H., Tomala, A., Safranek-Shrader, C., Kassner, N., Pajarskas, M., Harvey, M., Sechrist, S., Fortunato, M., Lyu, C., Elsayed, G., Kuang, C., Lottes, J., Chu, E., Jia, C., Chen, C.- W., Humphreys, P., Baumli, K., Tao, C., Samuel, R., Santos, C.N., Andreassen, A., Rakicevi ´ c, N., Grewe, ´ D., Kumar, A., Winkler, S., Caton, J., Brock, A., Dalmia, S., Sheahan, H., Barr, I., Miao, Y., Natsev, P., Devlin, J., Behbahani, F., Prost, F., Sun, Y., Myaskovsky, A., Pillai, T.S., Hurt, D., Lazaridou, A., Xiong, X., Zheng, C., Pardo, F., Li, X., Horgan, D., Stanton, J., Ambar, M., Xia, F., Lince, A., Wang, M., Mustafa, B., Webson, A., Lee, H., Anil, R., Wicke, M., Dozat, T., Sinha, A., Piqueras, E., Dabir, E., Upadhyay, S., Boral, A., Hendricks, L.A., Fry, C., Djolonga, J., Su, Y., Walker, J., Labanowski, J., Huang, R., Misra, V., Chen, J., Skerry-Ryan, R., Singh, A., Rijhwani, S., Yu, D., Castro-Ros, A., Changpinyo, B., Datta, R., Bagri, S., Hrafnkelsson, A.M., Maggioni, M., Zheng, D., Sulsky, Y., Hou, S., Paine, T.L., Yang, A., Riesa, J., Rogozinska, D., Marcus, D., Badawy, D.E., Zhang, Q., Wang, L., Miller, H., Greer, J., Sjos, L.L., Nova, A., Zen, H., Chaabouni, R., Rosca, M., Jiang, J., Chen, C., Liu, R., Sainath, T., Krikun, M., Polozov, A., Lespiau, J.-B., Newlan, J., Cankara, Z., Kwak, S., Xu, Y., Chen, P., Coenen, A., Meyer, C., Tsihlas, K., Ma, A., Gottweis, J., Xing, J., Gu, C., Miao, J., Frank, C., Cankara, Z., Ganapathy, S., Dasgupta, I., Hughes-Fitt, S., Chen, H., Reid, D., Rong, K., Fan, H., Amersfoort, J., Zhuang, V., Cohen, A., Gu, S.S., Mohananey, A., Ilic, A., Tobin, T., Wieting, J., Bortsova, A., Thacker, P., Wang, E., Caveness, E., Chiu, J., Sezener, E., Kaskasoli, A., Baker, S., Millican, K., Elhawaty, M., Aisopos, K., Lebsack, C., Byrd, N., Dai, H., Jia, W., Wiethoff, M., Davoodi, E., Weston, A., Yagati, L., Ahuja, A., Gao, I., Pundak, G., Zhang, S., Azzam, M., Sim, K.C., Caelles, S., Keeling, J., Sharma, A., Swing, A., Li, Y., Liu, C., Bostock, C.G., Bansal, Y., Nado, Z., Anand, A., Lipschultz, J., Karmarkar, A., Proleev, L., Ittycheriah, A., Yeganeh, S.H., Polovets, G., Faust, A., Sun, J., Rrustemi, A., Li, P., Shivanna, R., Liu, J., Welty, C., Lebron, F., Baddepudi, A., Krause, S., Parisotto, E., Soricut, R., Xu, Z., Bloxwich, D., Johnson, M., Neyshabur, B., Mao-Jones, J., Wang, R., Ramasesh, V., Abbas, Z., Guez, A., Segal, C., Nguyen, D.D., Svensson, J., Hou, L., York, S., Milan, K., Bridgers, S., Gworek, W., Tagliasacchi, M., Lee-Thorp, J., Chang, M., Guseynov, A., Hartman, A.J., Kwong, M., Zhao, R., Kashem, S., Cole, E., Miech, A., Tanburn, R., Phuong, M., Pavetic, F., Cevey, S., Comanescu, R., Ives, R., Yang, S., Du, C., Li, B., Zhang, Z., Iinuma, M., Hu, C.H., Roy, A., Bijwadia, S., Zhu, Z., Martins, D., Saputro, R., Gergely, A., Zheng, S., Jia, D., Antonoglou, I., Sadovsky, A., Gu, S., Bi, Y., Andreev, A., Samangooei, S., Khan, M., Kocisky, T., Filos, A., Kumar, C., Bishop, C., Yu, A., Hodkinson, S., Mittal, S., Shah, P., Moufarek, A., Cheng, Y., Bloniarz, A., Lee, J., Pejman, P., Michel, P., Spencer, S., Feinberg, V., Xiong, X., Savinov, N., Smith, C., Shakeri, S., Tran, D., Chesus, M., Bohnet, B., Tucker, G., Glehn, T., Muir, C., Mao, Y., Kazawa, H., Slone, A., Soparkar, K., Shrivastava, D., Cobon-Kerr, J., Sharman, M., Pavagadhi, J., Araya, C., Misiunas, K., Ghelani, N., Laskin, M., Barker, D., Li, Q., Briukhov, A., Houlsby, N., Glaese, M., Lakshminarayanan, B., Schucher, N., Tang, Y., Collins, E., Lim, H., Feng, F., Recasens, A., Lai, G., Magni, A., Cao, N.D., Siddhant, A., Ashwood, Z., Orbay, J., Dehghani, M., Brennan, J., He, Y., Xu, K., Gao, Y., Saroufim, C., Molloy, J., Wu, X., Arnold, S., Chang, S., Schrittwieser, J., Buchatskaya, E., Radpour, S., Polacek, M., Giordano, S., Bapna, A., Tokumine, S., Hellendoorn, V., Sottiaux, T., Cogan, S., Severyn, A., Saleh, M., Thakoor, S., Shefey, L., Qiao, S., Gaba, M., Chang, S. y., Swanson, C., Zhang, B., Lee, B., Rubenstein, P.K., Song, G., Kwiatkowski, T., Koop, A., Kannan, A., Kao, D., Schuh, P., Stjerngren, A., Ghiasi, G., Gibson, G., Vilnis, L., Yuan, Y., Ferreira, F.T., Kamath, A., Klimenko, T., Franko, K., Xiao, K., Bhattacharya, I., Patel, M., Wang, R., Morris, A., Strudel, R., Sharma, V., Choy, P., Hashemi, S.H., Landon, J., Finkelstein, M., Jhakra, P., Frye, J., Barnes, M., Mauger, M., Daun, D., Baatarsukh, K., Tung, M., Farhan, W., Michalewski, H., Viola, F., Chaumont Quitry, F., Lan, C.L., Hudson, T., Wang, Q., Fischer, F., Zheng, I., White, E., Dragan, A., Alayrac, J.-b., Ni, E., Pritzel, A., Iwanicki, A., Isard, M., Bulanova, A., Zilka, L., Dyer, E., Sachan, D., Srinivasan, S., Muckenhirn, H., Cai, H., Mandhane, A., Tariq, M., Rae, J.W., Wang, G., Ayoub, K., FitzGerald, N., Zhao, Y., Han, W., Alberti, C., Garrette, D., Krishnakumar, K., Gimenez, M., Levskaya, A., Sohn, D., Matak, J., Iturrate, I., Chang, M.B., Xiang, J., Cao, Y., Ranka, N., Brown, G., Hutter, A., Mirrokni, V., Chen, N., Yao, K., Egyed, Z., Galilee, F., Liechty, T., Kallakuri, P., Palmer, E., Ghemawat, S., Liu, J., Tao, D., Thornton, C., Green, T., Jasarevic, M., Lin, S., Cotruta, V., Tan, Y.-X., Fiedel, N., Yu, H., Chi, E., Neitz, A., Heitkaemper, J., Sinha, A., Zhou, D., Sun, Y., Kaed, C., Hulse, B., Mishra, S., Georgaki, M., Kudugunta, S., Farabet, C., Shafran, I., Vlasic, D., Tsitsulin, A., Ananthanarayanan, R., Carin, A., Su, G., Sun, P., V, S., Carvajal, G., Broder, J., Comsa, I., Repina, A., Wong, W., Chen, W.W., Hawkins, P., Filonov, E., Loher, L., Hirnschall, C., Wang, W., Ye, J., Burns, A., Cate, H., Wright, D.G., Piccinini, F., Zhang, L., Lin, C.-C., Gog, I., Kulizhskaya, Y., Sreevatsa, A., Song, S., Cobo, L.C., Iyer, A., Tekur, C., Garrido, G., Xiao, Z., Kemp, R., Zheng, H.S., Li, H., Agarwal, A., Ngani, C., Goshvadi, K., Santamaria-Fernandez, R., Fica, W., Chen, X., Gorgolewski, C., Sun, S., Garg, R., Ye, X., Eslami, S.M.A., Hua, N., Simon, J., Joshi, P., Kim, Y., Tenney, I., Potluri, S., Thiet, L.N., Yuan, Q., Luisier, F., Chronopoulou, A., Scellato, S., Srinivasan, P., Chen, M., Koverkathu, V., Dalibard, V., Xu, Y., Saeta, B., Anderson, K., Sellam, T., Fernando, N., Huot, F., Jung, J., Varadarajan, M., Quinn, M., Raul, A., Le, M., Habalov, R., Clark, J., Jalan, K., Bullard, K., Singhal, A., Luong, T., Wang, B., Rajayogam, S., Eisenschlos, J., Jia, J., Finchelstein, D., Yakubovich, A., Balle, D., Fink, M., Agarwal, S., Li, J., Dvijotham, D., Pal, S., Kang, K., Konzelmann, J., Beattie, J., Dousse, O., Wu, D., Crocker, R., Elkind, C., Jonnalagadda, S.R., Lee, J., Holtmann-Rice, D., Kallarackal, K., Liu, R., Vnukov, D., Vats, N., Invernizzi, L., Jafari, M., Zhou, H., Taylor, L., Prendki, J., Wu, M., Eccles, T., Liu, T., Kopparapu, K., Beaufays, F., Angermueller, C., Marzoca, A., Sarcar, S., Dib, H., Stanway, J., Perbet, F., Trdin, N., Sterneck, R., Khorlin, A., Li, D., Wu, X., Goenka, S., Madras, D., Goldshtein, S., Gierke, W., Zhou, T., Liu, Y., Liang, Y., White, A., Li, Y., Singh, S., Bahargam, S., Epstein, M., Basu, S., Lao, L., Ozturel, A., Crous, C., Zhai, A., Lu, H., Tung, Z., Gaur, N., Walton, A., Dixon, L., Zhang, M., Globerson, A., Uy, G., Bolt, A., Wiles, O., Nasr, M., Shumailov, I., Selvi, M., Piccinno, F., Aguilar, R., McCarthy, S., Khalman, M., Shukla, M., Galic, V., Carpenter, J., Villela, K., Zhang, H., Richardson, H., Martens, J., Bosnjak, M., Belle, S.R., Seibert, J., Alnahlawi, M., McWilliams, B., Singh, S., Louis, A., Ding, W., Popovici, D., Simicich, L., Knight, L., Mehta, P., Gupta, N., Shi, C., Fatehi, S., Mitrovic, J., Grills, A., Pagadora, J., Munkhdalai, T., Petrova, D., Eisenbud, D., Zhang, Z., Yates, D., Mittal, B., Tripuraneni, N., Assael, Y., Brovelli, T., Jain, P., Velimirovic, M., Akbulut, C., Mu, J., Macherey, W., Kumar, R., Xu, J., Qureshi, H., Comanici, G., Wiesner, J., Gong, Z., Ruddock, A., Bauer, M., Felt, N., GP, A., Arnab, A., Zelle, D., Rothfuss, J., Rosgen, B., Shenoy, A., Seybold, B., Li, X., Mudigonda, J., Erdogan, G., Xia, J., Simsa, J., Michi, A., Yao, Y., Yew, C., Kan, S., Caswell, I., Radebaugh, C., Elisseeff, A., Valenzuela, P., McKinney, K., Paterson, K., Cui, A., Latorre-Chimoto, E., Kim, S., Zeng, W., Durden, K., Ponnapalli, P., Sosea, T., Choquette-Choo, C.A., Manyika, J., Robenek, B., Vashisht, H., Pereira, S., Lam, H., Velic, M., Owusu-Afriyie, D., Lee, K., Bolukbasi, T., Parrish, A., Lu, S., Park, J., Venkatraman, B., Talbert, A., Rosique, L., Cheng, Y., Sozanschi, A., Paszke, A., Kumar, P., Austin, J., Li, L., Salama, K., Perz, B., Kim, W., Dukkipati, N., Baryshnikov, A., Kaplanis, C., Sheng, X., Chervonyi, Y., Unlu, C., Las Casas, D., Askham, H., Tunyasuvunakool, K., Gimeno, F., Poder, S., Kwak, C., Miecnikowski, M., Mirrokni, V., Dimitriev, A., Parisi, A., Liu, D., Tsai, T., Shevlane, T., Kouridi, C., Garmon, D., Goedeckemeyer, A., Brown, A.R., Vijayakumar, A., Elqursh, A., Jazayeri, S., Huang, J., Carthy, S.M., Hoover, J., Kim, L., Kumar, S., Chen, W., Biles, C., Bingham, G., Rosen, E., Wang, L., Tan, Q., Engel, D., Pongetti, F., Cesare, D., Hwang, D., Yu, L., Pullman, J., Narayanan, S., Levin, K., Gopal, S., Li, M., Aharoni, A., Trinh, T., Lo, J., Casagrande, N., Vij, R., Matthey, L., Ramadhana, B., Matthews, A., Carey, C., Johnson, M., Goranova, K., Shah, R., Ashraf, S., Dasgupta, K., Larsen, R., Wang, Y., Vuyyuru, M.R., Jiang, C., Ijazi, J., Osawa, K., Smith, C., Boppana, R.S., Bilal, T., Koizumi, Y., Xu, Y., Altun, Y., Shabat, N., Bariach, B., Korchemniy, A., Choo, K., Ronneberger, O., Iwuanyanwu, C., Zhao, S., Soergel, D., Hsieh, C.-J., Cai, I., Iqbal, S., Sundermeyer, M., Chen, Z., Bursztein, E., Malaviya, C., Biadsy, F., Shroff, P., Dhillon, I., Latkar, T., Dyer, C., Forbes, H., Nicosia, M., Nikolaev, V., Greene, S., Georgiev, M., Wang, P., Martin, N., Sedghi, H., Zhang, J., Banzal, P., Fritz, D., Rao, V., Wang, X., Zhang, J., Patraucean, V., Du, D., Mordatch, I., Jurin, I., Liu, L., Dubey, A., Mohan, A., Nowakowski, J., Ion, V.-D., Wei, N., Tojo, R., Raad, M.A., Hudson, D.A., Keshava, V., Agrawal, S., Ramirez, K., Wu, Z., Nguyen, H., Liu, J., Sewak, M., Petrini, B., Choi, D., Philips, I., Wang, Z., Bica, I., Garg, A., Wilkiewicz, J., Agrawal, P., Li, X., Guo, D., Xue, E., Shaik, N., Leach, A., Khan, S.M., Wiesinger, J., Jerome, S., Chakladar, A., Wang, A.W., Ornduff, T., Abu, F., Ghaffarkhah, A., Wainwright, M., Cortes, M., Liu, F., Maynez, J., Terzis, A., Samangouei, P., Mansour, R., K˛epa, T., Aubet, F.-X., Algymr, A., Banica, D., Weisz, A., Orban, A., Senges, A., Andrejczuk, E., Geller, M., Santo, N.D., Anklin, V., Merey, M.A., Baeuml, M., Strohman, T., Bai, J., Petrov, S., Wu, Y., Hassabis, D., Kavukcuoglu, K., Dean, J., Vinyals, O.: Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context (2024). <https://arxiv.org/abs/2403.05530>

- <span id="page-19-1"></span>Gloeckle, F., Idrissi, B.Y., Rozière, B., Lopez-Paz, D., Synnaeve, G.: Better & Faster Large Language Models via Multi-token Prediction (2024). <https://arxiv.org/abs/2404.19737>
- <span id="page-19-2"></span>Geiping, J., McLeish, S., Jain, N., Kirchenbauer, J., Singh, S., Bartoldson, B.R., Kailkhura, B., Bhatele, A., Goldstein, T.: Scaling up Test-Time Compute with Latent Reasoning: A Recurrent Depth Approach (2025). <https://arxiv.org/abs/2502.05171>
- <span id="page-19-3"></span>Gladstone, A., Nanduru, G., Islam, M.M., Han, P., Ha, H., Chadha, A., Du, Y., Ji, H., Li, J., Iqbal, T.: Energy-Based Transformers are Scalable Learners and Thinkers (2025). <https://arxiv.org/abs/2507.02092>
- <span id="page-19-0"></span>Hendrycks, D., Burns, C., Basart, S., Zou, A., Mazeika, M., Song, D., Steinhardt, J.: Measuring Massive Multitask Language Understanding (2021). <https://arxiv.org/abs/2009.03300>

- <span id="page-20-1"></span>Hao, S., Gu, Y., Ma, H., Hong, J.J., Wang, Z., Wang, D.Z., Hu, Z.: Reasoning with Language Model is Planning with World Model (2023). <https://arxiv.org/abs/2305.14992>
- <span id="page-20-10"></span>Huang, H., LeCun, Y., Balestriero, R.: LLM-JEPA: Large Language Models Meet Joint Embedding Predictive Architectures (2025). <https://arxiv.org/abs/2509.14252>
- <span id="page-20-5"></span>Hao, S., Sukhbaatar, S., Su, D., Li, X., Hu, Z., Weston, J., Tian, Y.: Training Large Language Models to Reason in a Continuous Latent Space (2024). <https://arxiv.org/abs/2412.06769>
- <span id="page-20-9"></span>Hu, V., Wu, D., Asano, Y., Mettes, P., Fernando, B., Ommer, B., Snoek, C.: Flow matching for conditional text generation in a few sampling steps. In: Graham, Y., Purver, M. (eds.) Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 2: Short Papers), pp. 380–392. Association for Computational Linguistics, St. Julian's, Malta (2024). [https://doi.org/10.18653/](https://doi.org/10.18653/v1/2024.eacl-short.33) [v1/2024.eacl-short.33](https://doi.org/10.18653/v1/2024.eacl-short.33) . <https://aclanthology.org/2024.eacl-short.33/>
- <span id="page-20-0"></span>Jiang, J., Wang, F., Shen, J., Kim, S., Kim, S.: A Survey on Large Language Models for Code Generation (2024). <https://arxiv.org/abs/2406.00515>
- <span id="page-20-3"></span>Kaplan, G., Oren, M., Reif, Y., Schwartz, R.: From Tokens to Words: On the Inner Lexicon of LLMs (2025). <https://arxiv.org/abs/2410.05864>
- <span id="page-20-14"></span>Lee, M., An, S., Kim, M.-S.: PlanRAG: A Plan-then-Retrieval Augmented Generation for Generative Large Language Models as Decision Makers (2024). <https://arxiv.org/abs/2406.12430>
- <span id="page-20-2"></span>Land, S., Bartolo, M.: Fishing for Magikarp: Automatically Detecting Under-trained Tokens in Large Language Models (2024). <https://arxiv.org/abs/2405.05417>
- <span id="page-20-6"></span>LCM team, Barrault, L., Duquenne, P.-A., Elbayad, M., Kozhevnikov, A., Alastruey, B., Andrews, P., Coria, M., Couairon, G., Costa-jussà, M.R., Dale, D., Elsahar, H., Heffernan, K., Janeiro, J.M., Tran, T., Ropers, C., Sánchez, E., Roman, R.S., Mourachko, A., Saleem, S., Schwenk, H.: Large Concept Models: Language Modeling in a Sentence Representation Space (2024). <https://arxiv.org/abs/2412.08821>
- <span id="page-20-8"></span>Lipman, Y., Chen, R.T.Q., Ben-Hamu, H., Nickel, M., Le, M.: Flow Matching for Generative Modeling (2023). <https://arxiv.org/abs/2210.02747>
- <span id="page-20-12"></span>Li, L., Geng, R., Fang, C., Li, B., Ma, C., Li, B., Li, Y.: Plan-then-Seam: Towards Efficient Table-to-Text Generation (2023). <https://arxiv.org/abs/2302.05138>
- <span id="page-20-13"></span>Liu, B., Jiang, Y., Zhang, X., Liu, Q., Zhang, S., Biswas, J., Stone, P.: LLM+P: Empowering Large Language Models with Optimal Planning Proficiency (2023). <https://arxiv.org/abs/2304.11477>
- <span id="page-20-4"></span>Lovelace, J., Kishore, V., Chen, Y., Weinberger, K.Q.: Diffusion Guided Language Modeling (2024). [https:](https://arxiv.org/abs/2408.04220) [//arxiv.org/abs/2408.04220](https://arxiv.org/abs/2408.04220)
- <span id="page-20-16"></span>Labs, I., Khanna, S., Kharbanda, S., Li, S., Varma, H., Wang, E., Birnbaum, S., Luo, Z., Miraoui, Y., Palrecha, A., Ermon, S., Grover, A., Kuleshov, V.: Mercury: Ultra-Fast Language Models Based on Diffusion (2025). <https://arxiv.org/abs/2506.17298>
- <span id="page-20-15"></span>Lyu, Y., Niu, Z., Xie, Z., Zhang, C., Xu, T., Wang, Y., Chen, E.: Retrieve-Plan-Generation: An Iterative Planning and Answering Framework for Knowledge-Intensive LLM Generation (2024). [https://arxiv.org/](https://arxiv.org/abs/2406.14979) [abs/2406.14979](https://arxiv.org/abs/2406.14979)
- <span id="page-20-7"></span>Li, X.L., Thickstun, J., Gulrajani, I., Liang, P., Hashimoto, T.B.: Diffusion-LM Improves Controllable Text Generation (2022). <https://arxiv.org/abs/2205.14217>
- <span id="page-20-17"></span>Lochab, A., Zhang, R.: Energy-Based Reward Models for Robust Language Model Alignment (2025). [https:](https://arxiv.org/abs/2504.13134) [//arxiv.org/abs/2504.13134](https://arxiv.org/abs/2504.13134)
- <span id="page-20-11"></span>Li, Y., Zhou, K., Zhao, W.X., Wen, J.-R.: Diffusion Models for Non-autoregressive Text Generation: A Survey (2023). <https://arxiv.org/abs/2303.06574>

- <span id="page-21-15"></span>Mikolov, T., Karafiát, M., Burget, L., Cernocký, J., Khudanpur, S.: Recurrent neural network based language ˇ model. In: Interspeech 2010, pp. 1045–1048 (2010). <https://doi.org/10.21437/Interspeech.2010-343>
- <span id="page-21-1"></span>Maharana, A., Lee, D.-H., Tulyakov, S., Bansal, M., Barbieri, F., Fang, Y.: Evaluating Very Long-Term Conversational Memory of LLM Agents (2024). <https://arxiv.org/abs/2402.17753>
- <span id="page-21-3"></span>Nnadi, G.O., Bertini, F.: Survey on Abstractive Text Summarization: Dataset, Models, and Metrics (2024). <https://arxiv.org/abs/2412.17165>
- <span id="page-21-7"></span>Nguyen, D., Yin, D., Joshi, A., Salim, F.: Spectraformer: A unified random feature framework for transformer. ACM Transactions on Intelligent Systems and Technology (2025) <https://doi.org/10.1145/3768161>
- <span id="page-21-12"></span>Nie, S., Zhu, F., Du, C., Pang, T., Liu, Q., Zeng, G., Lin, M., Li, C.: Scaling up Masked Diffusion Models on Text (2025). <https://arxiv.org/abs/2410.18514>
- <span id="page-21-13"></span>Ou, Z.: Energy-based models with applications to speech and language processing. Foundations and Trends® in Signal Processing 18(1–2), 1–199 (2024) <https://doi.org/10.1561/2000000117>
- <span id="page-21-14"></span>Puduppully, R., Lapata, M.: Data-to-text Generation with Macro Planning (2021). [https://arxiv.org/abs/2102.](https://arxiv.org/abs/2102.02723) [02723](https://arxiv.org/abs/2102.02723)
- <span id="page-21-9"></span>Pal, K., Sun, J., Yuan, A., Wallace, B., Bau, D.: Future lens: Anticipating subsequent tokens from a single hidden state. In: Proceedings of the 27th Conference on Computational Natural Language Learning (CoNLL), pp. 548–560. Association for Computational Linguistics, ??? (2023). [https://doi.org/10.18653/](https://doi.org/10.18653/v1/2023.conll-1.37) [v1/2023.conll-1.37](https://doi.org/10.18653/v1/2023.conll-1.37) . <http://dx.doi.org/10.18653/v1/2023.conll-1.37>
- <span id="page-21-10"></span>Qi, W., Yan, Y., Gong, Y., Liu, D., Duan, N., Chen, J., Zhang, R., Zhou, M.: ProphetNet: Predicting Future N-gram for Sequence-to-Sequence Pre-training (2020). <https://arxiv.org/abs/2001.04063>
- <span id="page-21-2"></span>Rohatgi, D., Block, A., Huang, A., Krishnamurthy, A., Foster, D.J.: Computational-Statistical Tradeoffs at the Next-Token Prediction Barrier: Autoregressive and Imitation Learning under Misspecification (2025). <https://arxiv.org/abs/2502.12465>
- <span id="page-21-6"></span>Roy, A., Saffar, M., Vaswani, A., Grangier, D.: Efficient content-based sparse attention with routing transformers. Transactions of the Association for Computational Linguistics 9, 53–68 (2021) [https://doi.org/10.](https://doi.org/10.1162/tacl_a_00353) [1162/tacl\\_a\\_00353](https://doi.org/10.1162/tacl_a_00353)
- <span id="page-21-4"></span>Schmied, T., Bornschein, J., Grau-Moya, J., Wulfmeier, M., Pascanu, R.: LLMs are Greedy Agents: Effects of RL Fine-tuning on Decision-Making Abilities (2025). <https://arxiv.org/abs/2504.16078>
- <span id="page-21-8"></span>Shazeer, N.: Fast Transformer Decoding: One Write-Head is All You Need (2019). [https://arxiv.org/abs/1911.](https://arxiv.org/abs/1911.02150) [02150](https://arxiv.org/abs/1911.02150)
- <span id="page-21-5"></span>Sennrich, R., Haddow, B., Birch, A.: Neural Machine Translation of Rare Words with Subword Units (2016). <https://arxiv.org/abs/1508.07909>
- <span id="page-21-11"></span>Shabalin, A., Meshchaninov, V., Chimbulatov, E., Lapikov, V., Kim, R., Bartosh, G., Molchanov, D., Markov, S., Vetrov, D.: TEncDM: Understanding the Properties of the Diffusion Model in the Space of Language Model Encodings (2025). <https://arxiv.org/abs/2402.19097>
- <span id="page-21-0"></span>Srivastava, A., Rastogi, A., Rao, A., Shoeb, A.A.M., Abid, A., Fisch, A., Brown, A.R., Santoro, A., Gupta, A., Garriga-Alonso, A., Kluska, A., Lewkowycz, A., Agarwal, A., Power, A., Ray, A., Warstadt, A., Kocurek, A.W., Safaya, A., Tazarv, A., Xiang, A., Parrish, A., Nie, A., Hussain, A., Askell, A., Dsouza, A., Slone, A., Rahane, A., Iyer, A.S., Andreassen, A., Madotto, A., Santilli, A., Stuhlmüller, A., Dai, A., La, A., Lampinen, A., Zou, A., Jiang, A., Chen, A., Vuong, A., Gupta, A., Gottardi, A., Norelli, A., Venkatesh, A., Gholamidavoodi, A., Tabassum, A., Menezes, A., Kirubarajan, A., Mullokandov, A., Sabharwal, A., Herrick, A., Efrat, A., Erdem, A., Karaka¸s, A., Roberts, B.R., Loe, B.S., Zoph, B., Bojanowski, B., Özyurt, B., Hedayatnia, B., Neyshabur, B., Inden, B., Stein, B., Ekmekci, B., Lin, B.Y., Howald, B., Orinion, B., Diao, C., Dour, C., Stinson, C., Argueta, C., Ramírez, C.F., Singh, C., Rathkopf, C., Meng, C., Baral, C., Wu, C., Callison-Burch, C., Waites, C., Voigt, C., Manning, C.D., Potts, C., Ramirez, C., Rivera, C.E.,

Siro, C., Raffel, C., Ashcraft, C., Garbacea, C., Sileo, D., Garrette, D., Hendrycks, D., Kilman, D., Roth, D., Freeman, D., Khashabi, D., Levy, D., González, D.M., Perszyk, D., Hernandez, D., Chen, D., Ippolito, D., Gilboa, D., Dohan, D., Drakard, D., Jurgens, D., Datta, D., Ganguli, D., Emelin, D., Kleyko, D., Yuret, D., Chen, D., Tam, D., Hupkes, D., Misra, D., Buzan, D., Mollo, D.C., Yang, D., Lee, D.-H., Schrader, D., Shutova, E., Cubuk, E.D., Segal, E., Hagerman, E., Barnes, E., Donoway, E., Pavlick, E., Rodola, E., Lam, E., Chu, E., Tang, E., Erdem, E., Chang, E., Chi, E.A., Dyer, E., Jerzak, E., Kim, E., Manyasi, E.E., Zheltonozhskii, E., Xia, F., Siar, F., Martínez-Plumed, F., Happé, F., Chollet, F., Rong, F., Mishra, G., Winata, G.I., Melo, G., Kruszewski, G., Parascandolo, G., Mariani, G., Wang, G., Jaimovitch-López, G., Betz, G., Gur-Ari, G., Galijasevic, H., Kim, H., Rashkin, H., Hajishirzi, H., Mehta, H., Bogar, H., Shevlin, H., Schütze, H., Yakura, H., Zhang, H., Wong, H.M., Ng, I., Noble, I., Jumelet, J., Geissinger, J., Kernion, J., Hilton, J., Lee, J., Fisac, J.F., Simon, J.B., Koppel, J., Zheng, J., Zou, J., Kocon, J., Thompson, J., Wing- ´ field, J., Kaplan, J., Radom, J., Sohl-Dickstein, J., Phang, J., Wei, J., Yosinski, J., Novikova, J., Bosscher, J., Marsh, J., Kim, J., Taal, J., Engel, J., Alabi, J., Xu, J., Song, J., Tang, J., Waweru, J., Burden, J., Miller, J., Balis, J.U., Batchelder, J., Berant, J., Frohberg, J., Rozen, J., Hernandez-Orallo, J., Boudeman, J., Guerr, J., Jones, J., Tenenbaum, J.B., Rule, J.S., Chua, J., Kanclerz, K., Livescu, K., Krauth, K., Gopalakrishnan, K., Ignatyeva, K., Markert, K., Dhole, K.D., Gimpel, K., Omondi, K., Mathewson, K., Chiafullo, K., Shkaruta, K., Shridhar, K., McDonell, K., Richardson, K., Reynolds, L., Gao, L., Zhang, L., Dugan, L., Qin, L., Contreras-Ochando, L., Morency, L.-P., Moschella, L., Lam, L., Noble, L., Schmidt, L., He, L., Colón, L.O., Metz, L., ¸Senel, L.K., Bosma, M., Sap, M., Hoeve, M., Farooqi, M., Faruqui, M., Mazeika, M., Baturan, M., Marelli, M., Maru, M., Quintana, M.J.R., Tolkiehn, M., Giulianelli, M., Lewis, M., Potthast, M., Leavitt, M.L., Hagen, M., Schubert, M., Baitemirova, M.O., Arnaud, M., McElrath, M., Yee, M.A., Cohen, M., Gu, M., Ivanitskiy, M., Starritt, M., Strube, M., Sw˛edrowski, M., Bevilacqua, M., Yasunaga, M., Kale, M., Cain, M., Xu, M., Suzgun, M., Walker, M., Tiwari, M., Bansal, M., Aminnaseri, M., Geva, M., Gheini, M., T, M.V., Peng, N., Chi, N.A., Lee, N., Krakover, N.G.-A., Cameron, N., Roberts, N., Doiron, N., Martinez, N., Nangia, N., Deckers, N., Muennighoff, N., Keskar, N.S., Iyer, N.S., Constant, N., Fiedel, N., Wen, N., Zhang, O., Agha, O., Elbaghdadi, O., Levy, O., Evans, O., Casares, P.A.M., Doshi, P., Fung, P., Liang, P.P., Vicol, P., Alipoormolabashi, P., Liao, P., Liang, P., Chang, P., Eckersley, P., Htut, P.M., Hwang, P., Miłkowski, P., Patil, P., Pezeshkpour, P., Oli, P., Mei, Q., Lyu, Q., Chen, Q., Banjade, R., Rudolph, R.E., Gabriel, R., Habacker, R., Risco, R., Millière, R., Garg, R., Barnes, R., Saurous, R.A., Arakawa, R., Raymaekers, R., Frank, R., Sikand, R., Novak, R., Sitelew, R., LeBras, R., Liu, R., Jacobs, R., Zhang, R., Salakhutdinov, R., Chi, R., Lee, R., Stovall, R., Teehan, R., Yang, R., Singh, S., Mohammad, S.M., Anand, S., Dillavou, S., Shleifer, S., Wiseman, S., Gruetter, S., Bowman, S.R., Schoenholz, S.S., Han, S., Kwatra, S., Rous, S.A., Ghazarian, S., Ghosh, S., Casey, S., Bischoff, S., Gehrmann, S., Schuster, S., Sadeghi, S., Hamdan, S., Zhou, S., Srivastava, S., Shi, S., Singh, S., Asaadi, S., Gu, S.S., Pachchigar, S., Toshniwal, S., Upadhyay, S., Shyamolima, Debnath, Shakeri, S., Thormeyer, S., Melzi, S., Reddy, S., Makini, S.P., Lee, S.-H., Torene, S., Hatwar, S., Dehaene, S., Divic, S., Ermon, S., Biderman, S., Lin, S., Prasad, S., Piantadosi, S.T., Shieber, S.M., Misherghi, S., Kiritchenko, S., Mishra, S., Linzen, T., Schuster, T., Li, T., Yu, T., Ali, T., Hashimoto, T., Wu, T.-L., Desbordes, T., Rothschild, T., Phan, T., Wang, T., Nkinyili, T., Schick, T., Kornev, T., Tunduny, T., Gerstenberg, T., Chang, T., Neeraj, T., Khot, T., Shultz, T., Shaham, U., Misra, V., Demberg, V., Nyamai, V., Raunak, V., Ramasesh, V., Prabhu, V.U., Padmakumar, V., Srikumar, V., Fedus, W., Saunders, W., Zhang, W., Vossen, W., Ren, X., Tong, X., Zhao, X., Wu, X., Shen, X., Yaghoobzadeh, Y., Lakretz, Y., Song, Y., Bahri, Y., Choi, Y., Yang, Y., Hao, Y., Chen, Y., Belinkov, Y., Hou, Y., Hou, Y., Bai, Y., Seid, Z., Zhao, Z., Wang, Z., Wang, Z.J., Wang, Z., Wu, Z.: Beyond the Imitation Game: Quantifying and extrapolating the capabilities of language models (2023). <https://arxiv.org/abs/2206.04615>

<span id="page-22-3"></span>Sundermeyer, M., Schlüter, R., Ney, H.: Lstm neural networks for language modeling. In: Interspeech 2012, pp. 194–197 (2012). <https://doi.org/10.21437/Interspeech.2012-65>

<span id="page-22-2"></span>Santilli, A., Severino, S., Postolache, E., Maiorca, V., Mancusi, M., Marin, R., Rodola, E.: Accelerating transformer inference for translation via parallel decoding. In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). Association for Computational Linguistics, ??? (2023). <https://doi.org/10.18653/v1/2023.acl-long.689> . [http://dx.doi.org/10.18653/v1/2023.](http://dx.doi.org/10.18653/v1/2023.acl-long.689) [acl-long.689](http://dx.doi.org/10.18653/v1/2023.acl-long.689)

<span id="page-22-1"></span>Su, Y., Vandyke, D., Wang, S., Fang, Y., Collier, N.: Plan-then-Generate: Controlled Data-to-Text Generation via Planning (2021). <https://arxiv.org/abs/2108.13740>

<span id="page-22-0"></span>Templeton, A., Conerly, T., Marcus, J., Lindsey, J., Bricken, T., Chen, B., Pearce, A., Citro, C., Ameisen, E.,

- Jones, A., Cunningham, H., Turner, N.L., McDougall, C., MacDiarmid, M., Freeman, C.D., Sumers, T.R., Rees, E., Batson, J., Jermyn, A., Carter, S., Olah, C., Henighan, T.: Scaling monosemanticity: Extracting interpretable features from claude 3 sonnet. Transformer Circuits Thread (2024)
- <span id="page-23-4"></span>Tack, J., Lanchantin, J., Yu, J., Cohen, A., Kulikov, I., Lan, J., Hao, S., Tian, Y., Weston, J., Li, X.: LLM Pretraining with Continuous Concepts (2025). <https://arxiv.org/abs/2502.08524>
- <span id="page-23-1"></span>Thakur, A., Nagpal, A., Savarkar, A., Pundalik, K., Dosi, S., Sawarkar, P., Thakur, V., Saluja, R., Desarkar, M.S., Ramakrishnan, G.: The Art of Breaking Words: Rethinking Multilingual Tokenizer Design (2025). <https://arxiv.org/abs/2508.06533>
- <span id="page-23-0"></span>Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A.N., Kaiser, L., Polosukhin, I.: Attention Is All You Need (2023). <https://arxiv.org/abs/1706.03762>
- <span id="page-23-10"></span>Wang, D., Ye, Z., Fang, F., Li, L.: Cooperative Strategic Planning Enhances Reasoning Capabilities in Large Language Models (2024). <https://arxiv.org/abs/2410.20007>
- <span id="page-23-7"></span>Wei, H., Zhang, Z., He, S., Xia, T., Pan, S., Liu, F.: PlanGenLLMs: A Modern Survey of LLM Planning Capabilities (2025). <https://arxiv.org/abs/2502.11221>
- <span id="page-23-6"></span>Xu, M., Geffner, T., Kreis, K., Nie, W., Xu, Y., Leskovec, J., Ermon, S., Vahdat, A.: Energy-Based Diffusion Language Models for Text Generation (2025). <https://arxiv.org/abs/2410.21357>
- <span id="page-23-2"></span>Yin, Y., Ding, J., Song, K., Zhang, Y.: Semformer: Transformer Language Models with Semantic Planning (2024). <https://arxiv.org/abs/2409.11143>
- <span id="page-23-5"></span>Ye, J., Gao, J., Gong, S., Zheng, L., Jiang, X., Li, Z., Kong, L.: Beyond Autoregression: Discrete Diffusion for Complex Reasoning and Planning (2025). <https://arxiv.org/abs/2410.14157>
- <span id="page-23-3"></span>Zhang, Y., Gu, J., Wu, Z., Zhai, S., Susskind, J., Jaitly, N.: PLANNER: Generating Diversified Paragraph via Latent Language Diffusion Model (2024). <https://arxiv.org/abs/2306.02531>
- <span id="page-23-8"></span>Zou, H., Kim, Z.M., Kang, D.: A Survey of Diffusion Models in Natural Language Processing (2023). [https:](https://arxiv.org/abs/2305.14671) [//arxiv.org/abs/2305.14671](https://arxiv.org/abs/2305.14671)
- <span id="page-23-9"></span>Zhu, R.-J., Peng, T., Cheng, T., Qu, X., Huang, J., Zhu, D., Wang, H., Xue, K., Zhang, X., Shan, Y., Cai, T., Kergan, T., Kembay, A., Smith, A., Lin, C., Nguyen, B., Pan, Y., Chou, Y., Cai, Z., Wu, Z., Zhao, Y., Liu, T., Yang, J., Zhou, W., Zheng, C., Li, C., Zhou, Y., Li, Z., Zhang, Z., Liu, J., Zhang, G., Huang, W., Eshraghian, J.: A Survey on Latent Reasoning (2025). <https://arxiv.org/abs/2507.06203>