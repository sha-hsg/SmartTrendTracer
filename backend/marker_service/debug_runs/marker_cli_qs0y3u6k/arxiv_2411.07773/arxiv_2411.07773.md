# Pointwise Mutual Information as a Performance Gauge for Retrieval-Augmented Generation

Tianyu Liu ,\* Jirui Qi ,<sup>∗</sup> Paul He ,† Arianna Bisazza Mrinmaya Sachan Ryan Cotterell ETH Zürich CLCG, University of Groningen University of Toronto [{tianyu.liu,](mailto:tianyu.liu@inf.ethz.ch) [mrinmaya.sachan,](mailto:mrinmaya.sachan@inf.ethz.ch)[ryan.cotterell}](mailto:ryan.cotterell@inf.ethz.ch)@inf.ethz.ch [{j.qi,](mailto:j.qi@rug.nl) [a.bisazza}](mailto:a.bisazza@rug.nl)@rug.nl, [hepaul@](mailto:hepaul@cs.toronto.edu)cs.toronto.edu

### Abstract

Recent work suggests that large language models enhanced with retrieval-augmented generation are easily influenced by the order, in which the retrieved documents are presented to the model when solving tasks such as question answering (QA). However, there is no method to date that exploits this phenomenon to improve generation. We fill this gap. In this study, we show that the pointwise mutual information between a context and a question is an effective gauge for language model performance. Importantly, this gauge does not depend on knowing the answer to the question *a priori*. Through experiments on two question-answering datasets and a variety of large language models, we find evidence for an empirical correlation between answer accuracy and pointwise mutual information. Additionally, we propose two methods that use the pointwise mutual information between a document and a question as a gauge for selecting and constructing prompts that lead to better performance, whose effectiveness we demonstrate through experimentation.[1](#page-0-0)

## 1 Introduction

Prompt design is an important factor when applying language models (LMs) to downstream tasks, including LMs that make use of retrieval-augmented generation (RAG; [Lewis et al.,](#page-9-0) [2020\)](#page-9-0). Wellconstructed prompts can improve LMs' answers to user-input questions and help generate responses that better align with user expectations [\(Gao et al.,](#page-9-1) [2021;](#page-9-1) [Izacard et al.,](#page-9-2) [2024;](#page-9-2) [Liu et al.,](#page-9-3) [2024;](#page-9-3) [Schul](#page-10-0)[hoff et al.,](#page-10-0) [2024;](#page-10-0) [Ma et al.,](#page-10-1) [2024,](#page-10-1) *inter alia*).

Under the RAG framework, a prompt typically consists of three components. First, an instruction provides a textual description of the overall task and general guidance for the language model. Second, a specific question encodes the precise task or query the model should perform. Third,

![](_page_0_Figure_11.jpeg)

Figure 1: For the *same* question, a permutation of documents with a higher PMI(q, cD(π)) tends to lead to a better answer.

a context encodes a set of documents retrieved from an external source by a retriever [\(Karpukhin](#page-9-4) [et al.,](#page-9-4) [2020;](#page-9-4) [Ni et al.,](#page-10-2) [2022\)](#page-10-2). Then, an answer is sampled from the language model. Previous work has explored various empirical approaches to prompt engineering, including the manual design of prompts that mimic human reasoning [\(Wei et al.,](#page-10-3) [2023;](#page-10-3) [Yao et al.,](#page-10-4) [2023\)](#page-10-4). Recently, [Liu et al.](#page-9-3) [\(2024\)](#page-9-3) demonstrated that language model performance is significantly influenced by the *order* of retrieved documents that comprise the context. Specifically, QA accuracy peaks when the gold document[2](#page-0-1) is positioned at the beginning or end of the context. Although extensive experimental evidence was adduced to validate this phenomenon [\(Liu et al.,](#page-9-3) [2024\)](#page-9-3), the underlying mechanisms remain poorly understood. This gap in understanding limits the applicability of these findings in the design and op-

<sup>\*</sup>The first two authors contributed equally.

<span id="page-0-0"></span><sup>†</sup>Work performed while at ETH Zürich.

<sup>1</sup> Our code is available at [https://github.com/lyuty](https://github.com/lyutyuh/poptimizer) [uh/poptimizer](https://github.com/lyutyuh/poptimizer).

<span id="page-0-1"></span><sup>2</sup> In factual QA tasks, the document containing the ground truth answer is referred to as the gold document.

timization of prompts for real-world applications.

While Liu et al.'s (2024) are interesting, choosing the optimal permutation of the documents requires knowledge of the answer, and, thus, cannot be directly used to improve RAG. In this article, we develop a proxy for the optimal permutation: We show that the pointwise mutual information between the question and the context under an LM acts as a useful proxy in determining the optimal permutation. To our knowledge, ours is the first to present in-depth analyses of the relation between question likelihood and model performance under the RAG framework.

Our findings in this paper are summarized in the following list:

- We show that the pointwise mutual information between the question and the context positively correlates with answer accuracy at the corpus level on NQ-Open (Kwiatkowski et al., 2019; Lee et al., 2019) and ELI5 (Fan et al., 2019).
- Given a question and a fixed set of documents, we demonstrate a strong correlation between the position of the gold document, the PMI between the question and the context, and QA accuracy.
- We validate the effectiveness of using question likelihood as a gauge for prompt optimization and demonstrate that likelihoodbased prompt optimization is a promising direction for future study.

#### <span id="page-1-5"></span>2 Setting the Stage

#### 2.1 Language Modeling and RAG

Language Modeling Background. Let  $\Sigma$  be an alphabet, i.e., a finite, non-empty set of tokens. A language model p is a distribution over  $\Sigma^*$ , the set of all strings with tokens drawn from  $\Sigma$ . Let Y be a  $\Sigma^*$ -valued random variable distributed according to p and  $\sigma \in \Sigma^*$ . We define the **prefix probability**<sup>3</sup>  $\overrightarrow{p}(\sigma)$  as the probability that Y has  $\sigma$  as a prefix:

$$\overrightarrow{p}(\boldsymbol{\sigma}) \triangleq \underset{Y \sim p}{\mathbb{P}}(Y \succeq \boldsymbol{\sigma}) \tag{1a}$$

$$= \sum_{\boldsymbol{\sigma}' \in \Sigma^*} \mathbb{1} \{ \boldsymbol{\sigma}' \succeq \boldsymbol{\sigma} \} p(\boldsymbol{\sigma}') \qquad (1b)$$

The conditional prefix probability  $\overrightarrow{p}(\sigma' \mid \sigma) = \frac{\overrightarrow{p}(\sigma \cdot \sigma')}{\overrightarrow{p}(\sigma')}$  tells us how certain the model is that  $\sigma'$  naturally follows from its preceding string  $\sigma$ . Fi-

nally, we define an **infix probability**, i.e., the probability of generating a string that contains  $\sigma \Box \sigma'$ ; where as  $\Box$  is a gap, as follows

$$\overrightarrow{p}(\boldsymbol{\sigma} \square \boldsymbol{\sigma}'') \triangleq \underset{Y \sim p}{\mathbb{P}} (Y \succeq \boldsymbol{\sigma} \square \boldsymbol{\sigma}'')$$
 (2a)

$$= \sum_{\boldsymbol{\sigma}''' \in \Sigma^*} \sum_{\boldsymbol{\sigma}' \in \Sigma^*} \mathbb{1} \left\{ \boldsymbol{\sigma}''' \succeq \boldsymbol{\sigma} \boldsymbol{\sigma}' \boldsymbol{\sigma}'' \right\} p(\boldsymbol{\sigma}''') \quad (2b)$$

**Retrieval-augmented Generation.** Modern language models are often used to perform questionanswering tasks. When solving such a task with a language model, string encoding the question question  $q \in \Sigma^*$  is given to the model. We assume each question q has a unique correct answer which we will denote a. This is, of course, a simplifying assumption, but it does jibe with how questionanswering is typically evaluated. We will adorn  $\widetilde{a}$ , e.g.,  $\widetilde{a}$ , to indicate an answer generated from  $\overrightarrow{p}(\cdot \mid q)$  that may or may not be correct. Generating  $\overrightarrow{a}$  from  $\overrightarrow{p}(\cdot \mid q)$  may be done using either a deterministic method, e.g., beam search, or a stochastic method, e.g., ancestral sampling.<sup>4</sup> In RAG, the model is additionally given a set of documents  $\mathcal{D} = \{\boldsymbol{d}_k\}_{k=1}^K$ , where  $\boldsymbol{d}_k \in \Sigma^*$ , and a permutation of the documents  $\pi$ :  $\{1, \dots, K\} \rightarrow \{1, \dots, K\}$ . Given  $\mathcal{D}$  and  $\pi$ , a context c is constructed by concatenating the documents in the order defined by  $\pi$ , i.e.,  $\boldsymbol{c}_{\mathcal{D}}(\pi) \triangleq \boldsymbol{d}_{\pi(1)} \cdot \cdots \cdot \boldsymbol{d}_{\pi(K)}$ . Then, we generate an answer from  $\overrightarrow{p}(\cdot \mid \boldsymbol{c} \cdot \boldsymbol{q})$ . We provide an example below.

**Example 2.1.** Consider  $\mathcal{D} = \{$  "Llandudno Pier is a Grade II\* listed pier...", "Garth Pier is a Grade II listed structure...", "Southend Pier is a..." $\}$ , and  $\pi(1) = 2, \pi(2) = 1, \pi(3) = 3$ . We have  $\mathbf{c}_{\mathcal{D}}(\pi) =$  "Garth Pier is... Llandudno Pier is a Grade II\* listed pier... Southend Pier is...".

Let  $\widetilde{a}_{\pi}$  denote an answer generated from  $\overrightarrow{p}(\cdot \mid c_{\mathcal{D}}(\pi) \cdot q)$ . To evaluate the quality of  $\widetilde{a}_{\pi}$ , we define an evaluation metric  $g(\widetilde{a}_{\pi}, a)$ . In addition, we assume the ground truth answer a to be unique for a question-context pair (q, c).

<span id="page-1-4"></span><span id="page-1-3"></span>**Pointwise Mutual Information.** In RAG question answering, we consider the following **pointwise mutual information** 

<span id="page-1-2"></span>
$$PMI(\boldsymbol{q}, \boldsymbol{c}) \triangleq \log \frac{\overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c})}{\overrightarrow{p}(\boldsymbol{q})}$$
(3)

between q and c, where  $c = d_{\pi(1)} \cdot \cdots \cdot d_{\pi(K)}$ . In other words, Eq. (3) measures the degree of association of q with c.

<span id="page-1-0"></span><sup>&</sup>lt;sup>3</sup>See Vieira et al. (2024) for a more in-depth discussion.

<span id="page-1-1"></span><sup>&</sup>lt;sup>4</sup>In this study, we consider greedy decoding, i.e., beam search with a beam of size 1.

<span id="page-2-3"></span>![](_page_2_Figure_0.jpeg)

Figure 2: We observe that the PMI and QA accuracy trace a U-shaped curve—nearly in lockstep—as the gold document position within the context changes. The result is computed with LLaMA-3-8B.

#### 2.2 A Concrete Hypothesis

Returning to the central goal of this paper, i.e., trying to find a proxy that helps determine the optimal permutation of the documents for RAG, we hypothesize that, given a question q, a set of documents  $\mathcal{D}$ , and the ground truth answer a, the pointwise mutual information  $\mathrm{PMI}(q, c_{\mathcal{D}}(\pi))$  correlates with  $\log \frac{\overrightarrow{p}(a|q \cdot c_{\mathcal{D}}(\pi))}{1-\overrightarrow{p}(a|q \cdot c_{\mathcal{D}}(\pi))}$ , the log odds ratio, and can be deemed a gauge for the expected accuracy of the generated answer. In symbols, our hypothesis is as follows.

<span id="page-2-0"></span>**Hypothesis 2.1.** In RAG question answering, for a fixed question  $\mathbf{q}$ , a set of documents  $\mathcal{D}$  permuted by  $\pi$ , and the ground truth answer  $\mathbf{a}$ , we have the following relation between  $\mathrm{PMI}(\mathbf{q}, \mathbf{c}_{\mathcal{D}}(\pi))$  and  $\overrightarrow{p}(\mathbf{a} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))$ 

$$PMI(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})) = a \log \frac{\overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))}{1 - \overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))} + b$$
(4)

for constants  $a \in \mathbb{R}_{>0}$ ,  $b \in \mathbb{R}$ .

#### 2.3 A Bit of Analysis

In words, Hypothesis 2.1 says that when  $PMI(q, c_D(\pi))$  is high, we expect the LM better respond to the question q with higher accuracy, and, moreover, this relationship is affine. Although this is empirically true in many cases (Gonen et al., 2023), we offer an assumption that enables a derivation of this property.

<span id="page-2-2"></span>**Assumption 2.1.** For all question—context pairs (q, c), let a be the correct answer, then we have

$$\overrightarrow{p}(\mathbf{q} \mid \mathbf{c}_{\mathcal{D}}(\mathbf{\pi}) \square \mathbf{a}) = \overrightarrow{p}(\mathbf{q} \mid \mathbf{c}_{\mathcal{D}}(\mathbf{\pi}))$$
 (5a)

$$\overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}) \square \overline{\boldsymbol{a}}) = \overrightarrow{p}(\boldsymbol{q}) \tag{5b}$$

for any  $\bar{\mathbf{a}} \in \Sigma^*$  such that  $\bar{\mathbf{a}} \not\preceq \mathbf{a}^5$ .

We now give a brief qualitative justification of Assumption 2.1. Conditioned on the event that the model *incorrectly* answers the question given the context, Eq. (5b) says that the question q is not dependent on the provided context. Because, in RAG, we assume the correct answer is given to the model in the context and the model's job is to retrieve it, our assumption corresponds to the notion that an incorrect response by the model should *not* be influenced by the context. Eq. (5a) corresponds to the notion that since the correct answer is already contained in the context, conditioning on the correct answer answer does not provide any new information to generating q.

<span id="page-2-4"></span>**Proposition 2.1.** *Under assumptions given in Assumption 2.1, we have* 

$$\log \frac{\overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))}{1 - \overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))}$$

$$= PMI(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})) + C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))$$
(6)

for an answer-dependent constant  $C(\mathbf{a}, \mathbf{c}_{\mathcal{D}}(\pi))$ .

In other words, the pointwise mutual information  $PMI(q, c_{\mathcal{D}}(\pi))$  is equivalent up to an additive constant to the log odds ratio  $\log \frac{\overrightarrow{p}(a|q \cdot c_{\mathcal{D}}(\pi))}{1 - \overrightarrow{p}(a|q \cdot c_{\mathcal{D}}(\pi))}$ .

Foreshadowing the Results. In the empirical portion of this paper, we test Hypothesis 2.1 through experiments on two QA benchmarks—NQ-Open and ELI5—using a range of state-of-theart open LMs, including LLaMA-2, LLaMA-3, LLaMA-3.1, Mistral-v0.3, and MPT. Our findings demonstrate that, as the position of relevant information within the input context c varies, the pointwise mutual information,  $PMI(q, c_D(\pi))$  and expected answer accuracy  $\overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))$  vary in tandem, i.e., they are strongly correlated. This correlation is illustrated in Figure 2. Specifically, LMs tend to provide better responses to questions where the documents in the context are permuted so as to have higher PMI( $q, c_{\mathcal{D}}(\pi)$ ). These results suggest that PMI serves both as a performance gauge and as a strong indicator of the position of task-relevant information within the input context. Building on this insight, we propose a direction

<span id="page-2-1"></span><sup>&</sup>lt;sup>5</sup>Eq. (5a) and Eq. (5b) can be seen as a form of context-specific conditional independence (Boutilier et al., 1996).

for prompt optimization through two specific methods. The first selects a permutation  $\pi$  of the documents that maximizes PMI(q,  $c_{\mathcal{D}}(\pi)$ ) to construct the context c. The second builds on the findings of Liu et al. (2024) that the curve traced by permuting the position of the gold document results in a U-shaped curve. We exploit this finding to develop an efficient prompt ordering algorithm. Further experimentation demonstrates that our methods enhance answer accuracy across both datasets for instruction-tuned and base models alike, with the second approach achieving even greater gains.

#### 3 PMI Correlates with Performance

As discussed in §2, our first goal is to determine how  $PMI(q, c_D(\pi))$  changes as a function of the permutation  $\pi$  of the documents D. Due to Hypothesis 2.1, we expect a strong correlation between  $PMI(q, c_D(\pi))$  and expected answer accuracy.

#### 3.1 Experimental Setup

**Datasets.** We run experiments on two question-answering datasets, namely NQ-Open and ELI5. Details of the datasets are given in Appendix C. Let  $\mathcal{C} \triangleq \{(\boldsymbol{q}_m, \mathcal{D}_m, \boldsymbol{a}_m)\}_{m=1}^M$  be a dataset of triples, where each  $\boldsymbol{a}_m$  represents the ground truth answer to  $\boldsymbol{q}_m$ .

**Empirical Metrics for LM evaluation.** practice, LM performance is often evaluated with rule-based empirical metrics, denoted g, such as accuracy, instead of the conditional likelihood  $\overrightarrow{p}(a)$  $(\mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))$ . Although mathematically quantifying the relation between g and PMI is difficult, we contend that they positively correlate due to recent progress on language model calibration (Zhao et al., 2023), i.e., the alignment between  $\overrightarrow{p}(\mathbf{a} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))$ and  $g(\tilde{\boldsymbol{a}}, \boldsymbol{a})$ . On NQ-Open, the ground truth answer for each question is either a word or a short phrase. The accuracy is 1 when the LM response contains the correct answer as a substring; otherwise, the accuracy is 0. Following Liu et al. (2024), we compute the model's average accuracy over the entire dataset. On ELI5, the correct answer for each question comprises three sub-claims, and a correct answer is expected to include all of these subclaims. Examples are illustrated in Appendix B. We follow Gao et al. (2023) and take the recall rate of sub-claims to be the evaluation metric, which takes value from  $\{0, 1/3, 2/3, 1\}$ . The TRUE model,<sup>6</sup>

a T5-XXL model fine-tuned on natural language inference (NLI) tasks, is used to automatically evaluate whether a response entails a sub-claim.

Language Model Settings. Most state-of-the-art closed LMs, such as OpenAI's ChatGPT and Anthropic's Claude, do not provide direct access to the likelihood of either input or output tokens. Thus, we select leading open LMs for our experiments, focusing on three families: LLaMA-2, LLaMA-3 (Touvron et al., 2023), and Mistral-v0.3 (Jiang et al., 2023). We also evaluate MPT on NQ-Open.<sup>7</sup> Following the settings of Liu et al. (2024), we adopt greedy decoding for all models when generating responses. We set the maximum number of decoded tokens to 100 on NQ-Open and 300 on ELI5.

**Prompt Templates.** We follow the suggested usage and prompt formatting instructions of each LM we use. For chat and instruction-tuned models, we present the context and query to the LM in the role of user, and elicit the response from LMs in the role of assistant. For base models, we elicit responses from LMs as sentence completion.

#### <span id="page-3-3"></span>3.2 Technical Interlude: Sets of Permutations

In many of our experiments, we would like to take a sum or a max over all permutations of K items, i.e., take a sum or max over the symmetric group  $\mathbb{S}_K$ . However,  $|\mathbb{S}_K| = K!$ , which grows too large to enumerate efficiently. To cope with the size of  $\mathbb{S}_K$ , in this paper, we perform computations over a subset of  $\mathbb{S}_K$ . Specifically, starting a user-specified permutation  $\pi$ , we consider the cyclic group generated by  $(\pi)$  where the group operation is functional composition, as is standard. Let  $\sigma = (1, 2, \cdots, K)$  be a shifting permutation. It is easy to see that  $|(\pi)| = K$ , and the  $k^{\text{th}}$  element of  $(\pi)$  is given by  $\widetilde{\pi}_k \triangleq \sigma^{k-1} \circ \pi = \underbrace{\sigma \circ \cdots \circ \sigma}_{(k-1) \text{ times}} \circ \pi$ , or,

equivalently we have

$$\widetilde{\pi}_k(i) = (i+k-1) \mod K, \tag{7}$$

**Example 3.1.** Given a permutation  $\pi = (1, 2, 3)$ . The cyclic group  $(\pi)$  generated by  $\pi$  is equal to  $\{\widetilde{\pi}_1, \widetilde{\pi}_2, \widetilde{\pi}_3\}$  where  $\widetilde{\pi}_1 = (1, 2, 3), \ \widetilde{\pi}_2 = (2, 3, 1),$  and  $\widetilde{\pi}_3 = (3, 1, 2)$ .

<span id="page-3-0"></span><sup>6</sup>https://huggingface.co/google/t5\_xxl\_true\_nl i\_mixture

<span id="page-3-1"></span><sup>&</sup>lt;sup>7</sup>In our preliminary experiments, MPT fails to generate sufficiently long responses on ELI5, resulting in performance that is not directly comparable to other LMs.

<span id="page-3-2"></span><sup>&</sup>lt;sup>8</sup>Here, ∘ denotes function composition, the standard product of permutations.

<span id="page-4-0"></span>![](_page_4_Figure_0.jpeg)

Figure 3: Corpus-level correlation between  $PMI(q, c_D(\pi))$  and answer accuracy on NQ-Open and ELI5.

#### <span id="page-4-5"></span>3.3 Results

We now discuss our empirical findings.

**Corpus-Level Correlation.** As our first evaluation metric, we consider a corpus-level correlation. For each  $q_m$ ,  $\mathcal{D}_m$  in a corpus  $\mathcal{C}$ , we compute the average PMI for the  $m^{\text{th}}$  instance as follows

$$\rho_m \triangleq \frac{1}{K} \sum_{k=1}^{K} \text{PMI}(\boldsymbol{q}_m, \boldsymbol{c}_{\mathcal{D}_m}(\widetilde{\boldsymbol{\pi}}_k))$$
 (8)

We then bin the elements of  $\{\rho_m\}_{m=1}^M$  into three bins according to which tertile they fall it when  $\{\rho_m\}_{m=1}^M$  are arranged into a histogram. Then, we compute the average sub-claim recall rate (ELI5) and accuracy (NQ-Open) for each bin. Our results, shown in Figure 3, demonstrate that LMs tend to perform better on the prompts with a higher  $PMI(q, c_D(\pi))$  compared to those with lower  $PMI(q, c_D(\pi))$ .

<span id="page-4-3"></span>Instance-Level Correlation. We further analyze the instance-level correlation between  $PMI(q, c_D(\pi))$  and accuracy by varying context while keeping the question fixed. In symbols, we compute

$$\eta_k \triangleq \frac{1}{M} \sum_{m=1}^{M} \text{PMI}(\boldsymbol{q}_m, \boldsymbol{c}_{\mathcal{D}_m}(\widetilde{\boldsymbol{\pi}}_k))$$
 (9)

where  $\widetilde{\pi}_k$  is the permutation in which the k-th document  $d_k$  contains relevant information. We then plot the curve of  $\{\eta_k\}_{k=1}^K$ , to see how PMI is affected by the position of a relevant document within a context.

<span id="page-4-2"></span>**Revisiting Liu et al. (2024).** We now revisit the findings of Liu et al. (2024), who observed a drop in QA accuracy when the gold document is positioned within the middle of c. We first experiment on NQ-Open by varying the position of the gold document<sup>9</sup> in c. The set of retrieved documents and the order of non-gold documents remain the same. As the gold document is placed in different positions in c, we find that both PMI( $q, c_D(\pi)$ ) and QA accuracy fluctuate—nearly in lockstep. To further explore this correlation between PMI(q, c) and QA accuracy, we calculate the expected accuracy with the prompt of the highest and lowest PMI(q,  $c_D(\pi)$ ). Results are given in Table 1, showing that LMs perform better when the document order in the prompt leads to the highest  $PMI(q, c_{\mathcal{D}}(\pi))$ ; while the prompt with the lowest PMI(q,  $c_D(\pi)$ ) results in inferior performance.

<span id="page-4-4"></span>**Experiments on ELI5.** Compared to NQ-Open, ELI5 is a more challenging long-form QA dataset

<span id="page-4-1"></span><sup>&</sup>lt;sup>9</sup>In NQ-Open, exactly *one* retrieved document is marked as the gold document for each question.

<span id="page-5-1"></span>![](_page_5_Figure_0.jpeg)

Figure 4: QA accuracy, PMI, and log odds ratio of answer likelihood on 20 docs evaluated on LLaMA-3.1-8B and LLaMA-3.1-8B-Instruct.

<span id="page-5-0"></span>

| #Doc |         | PMI(q, cD(π)) Mistral-7B-Inst | LLaMA-3-8B    | LLaMA-3.1-8B  | LLaMA-3-8B-Inst | LLaMA-3.1-8B-Inst | MPT-7B-8K-Inst |
|------|---------|-------------------------------|---------------|---------------|-----------------|-------------------|----------------|
|      |         |                               |               | NQ-Open       |                 |                   |                |
| 10   | Highest | 68.69 (-2.52)                 | 54.04 (-1.84) | 56.72 (-2.41) | 71.58 (-1.80)   | 66.13 (-2.16)     | 48.93 (-2.80)  |
|      | Lowest  | 66.98 (-2.89)                 | 49.30 (-2.03) | 53.29 (-2.72) | 71.29 (-2.01)   | 65.70 (-2.43)     | 46.97 (-3.38)  |
| 20   | Highest | 64.86 (-2.45)                 | 52.05 (-1.99) | 52.50 (-2.40) | 69.00 (-1.83)   | 62.97 (-2.21)     | 42.25 (-2.70)  |
|      | Lowest  | 62.60 (-2.83)                 | 46.91 (-2.03) | 48.51 (-2.72) | 67.68 (-2.01)   | 61.05 (-2.43)     | 42.09 (-3.23)  |
| 30   | Highest | 57.70 (-2.52)                 | 50.30 (-1.88) | 50.00 (-2.60) | 64.36 (-1.84)   | 60.95 (-2.41)     | 39.31 (-2.56)  |
|      | Lowest  | 53.96 (-2.92)                 | 45.27 (-2.03) | 46.42 (-2.83) | 65.12 (-2.03)   | 59.55 (-2.65)     | 39.12 (-3.05)  |

Table 1: Instance-level correlation between PMI(q, cD(π)) and answer accuracy. We compute the average answer accuracy over prompts that yield the highest and lowest PMI(q, cD(π)) as the gold document placed at different positions in the document sequence for each instance. The answer accuracy and the average PMI(q, cD(π)) are reported in the table.

where questions are mostly about *how*/*why*/*what*, and the answers are expected to be more comprehensive and cover multiple aspects. Due to the lack of gold document annotations on ELI5, we adopt permutations from the cyclic group (π) and random shuffling. In random shuffling for K documents, we randomly shuffle the document set K (i.e., same as the number of documents) times and obtain K document sequences for consistency. Given multiple prompts for a question, among which only the document orders in the context are different, we calculate the average performance of the prompts with the highest and lowest PMI(q, cD(π)) for each question in the same fashion as described in [§3.3](#page-4-2) for NQ-Open. Results in Table [2](#page-6-0) show that LMs achieve higher answer accuracy on the prompts with the highest PMI(q, cD(π)), compared with the prompts with the lowest PMI(q, cD(π)). This indicates LMs can better answer questions with higher question likelihood through document shuffling, demonstrating the strong instance-level correlation between PMI(q, cD(π)) with answer accuracy.

### 4 Improving RAG via Reordering

In [§3.3,](#page-4-3) we offered evidence for Hypothesis [2.1,](#page-2-0) i.e., that PMI(q, cD(π)) correlates with model performance. In light of this finding, we propose two methods to permute the documents presented to the LM in RAG *without* knowledge of the answer.

#### 4.1 Method 1: Search by PMI

Our empirical findings showed that the permutation of the documents in the context that leads to the highest value of PMI(q, cD(π)) leads to superior performance on QA tasks. This suggests a natural algorithm

$$\pi^* = \underset{\pi \in \mathbb{S}_K}{\operatorname{arg\,max\,PMI}}(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\pi)) \tag{10}$$

However, as discussed in [§3.2,](#page-3-3) the set of all permutations (the symmetric group) S<sup>K</sup> is too large to enumerate. Thus, we fall back on a simple approximation. Given a user-provided permutation π, we search over the cyclic group generated by π, denoted as (π). Using the notation introduced in

<span id="page-6-0"></span>

| #Doc | $\text{PMI}(\boldsymbol{q},\boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))$ Mistral-7B-Inst |                                       | LLaMA-3-8B                            | LLaMA-3.1-8B                          | LLaMA-3-8B-Inst                    | LLaMA-3.1-8B-Inst                  |  |  |
|------|---------------------------------------------------------------------------------------------|---------------------------------------|---------------------------------------|---------------------------------------|------------------------------------|------------------------------------|--|--|
|      | ELI5 with Rotational permutation                                                            |                                       |                                       |                                       |                                    |                                    |  |  |
| 5    | Highest<br>Lowest                                                                           | <b>13.97</b> (-3.72) 13.50 (-4.06)    | <b>11.37</b> (-2.23) 11.10 (-2.39)    | <b>12.60</b> (-2.28) 12.50 (-2.43)    | <b>14.23</b> (-2.21) 13.17 (-2.54) | <b>13.97</b> (-2.26) 13.93 (-2.48) |  |  |
| 10   | Highest<br>Lowest                                                                           | <b>15.23</b> (-3.53) 14.47 (-3.99)    | 11.27 (-2.19)<br><b>11.50</b> (-2.39) | 12.50 (-2.29)<br><b>13.10</b> (-2.48) | <b>14.50</b> (-2.10) 14.07 (-2.55) | <b>16.17</b> (-2.23) 15.77 (-2.54) |  |  |
| 20   | Highest<br>Lowest                                                                           | <b>16.20</b> (-2.13) 15.80 (-2.73)    | 11.13 (-2.19)<br><b>11.20</b> (-2.42) | <b>12.77</b> (-2.28) 12.13 (-2.48)    | <b>16.20</b> (-2.13) 15.80 (-2.73) | <b>17.17</b> (-2.18) 15.67 (-2.54) |  |  |
|      | ELI5 with Random Shuffling                                                                  |                                       |                                       |                                       |                                    |                                    |  |  |
| 5    | Highest<br>Lowest                                                                           | <b>14.27</b> (-3.73) 14.10 (-4.04)    | 10.73 (-2.24)<br><b>11.20</b> (-2.39) | <b>12.57</b> (-2.28) 12.33 (-2.42)    | <b>14.10</b> (-2.23) 12.77 (-2.52) | <b>14.20</b> (-2.27) 14.00 (-2.48) |  |  |
| 10   | Highest<br>Lowest                                                                           | <b>15.63</b> (-3.54) 15.07 (-3.97)    | <b>11.47</b> (-2.19) 11.23 (-2.39)    | <b>12.73</b> (-2.29) 12.20 (-2.48)    | <b>15.70</b> (-2.11) 14.57 (-2.52) | <b>16.90</b> (-2.23) 16.70 (-2.53) |  |  |
| 20   | Highest<br>Lowest                                                                           | 16.10 (-3.44)<br><b>16.53</b> (-4.00) | 10.83 (-2.19)<br><b>11.20</b> (-2.42) | <b>12.60</b> (-2.28)<br>11.87 (-2.49) | <b>16.13</b> (-2.14) 15.53 (-2.71) | <b>17.20</b> (-2.18) 17.10 (-2.54) |  |  |
|      |                                                                                             |                                       |                                       |                                       |                                    |                                    |  |  |

Table 2: Instance-level correlation between PMI(q, c) and answer accuracy on ELI5. The average QA accuracy is computed over prompts that yield the highest and lowest PMI(q, c) as the input documents are reordered with (1) rotational reordering and (2) random shuffling as introduced in §3.3. The QA accuracy and the average PMI(q, c) are reported in the table.

§3.2, we choose  $\widetilde{\pi}_{k^*}$  where we select

$$k^* = \operatorname*{arg\,max}_{k=1}^K \operatorname{PMI}(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\widetilde{\boldsymbol{\pi}}_k)), \qquad (11)$$

where  $\widetilde{\pi}_k$  is defined in §3.2.

#### 4.2 Method 2: Search by Curvature

We now develop a second algorithm based on the observation in Figure 4 that accuracy and PMI change simultaneously and exhibit a U-shaped curve as the gold document position within the permutation of documents in c. Our algorithm is based on a discrete notion of convexity and an assumption based on our findings in §3.3, which we introduce in the abstract below.

Technical Interlude Discrete Convexity. A sequence of real values  $\{a_n\}_{n=1}^N$  is called **convex** if we have

<span id="page-6-1"></span>
$$\Delta_n^2 \triangleq 2a_n - a_{n+1} - a_{n-1} \le 0 \tag{12}$$

for all  $n \in \{2, \ldots, N-1\}$ . In the abstract, the problem we wish to solve is this: Given an arbitrary finite sequence of reals  $\{b_n\}_{n=1}^N$ , find a permutation  $\tau \colon [N] \to [N]$  that renders  $\{b_n\}_{n=1}^N$  convex, i.e., that Eq. (12) holds after applying the permutation to the sequence's indices. We call such a choice of  $\tau$  a **convex permutation**. Note that convex permutations may not always exist. To achieve a U-shape curve, do not just want a convex permutation, but in addition the one that results in a convex

sequence that has as much upwards curvature as possible. In other words, if  $\tau$  is a convex permutation, then *in addition* we want the following sum to be *minimized* 

$$\sum_{n=2}^{N-1} \Delta_n^2 = -(b_1 + b_N) + \sum_{n=2}^{N-1} b_m$$
 (13a)

$$= -2(b_1 + b_N) + B \tag{13b}$$

$$\leq 0,$$
 (13c)

where  $B \triangleq \sum_{n=1}^N b_n$ . However, because B is constant, the total curvature induced by a convex permutation  $\tau$  only depends on  $b_{\tau(1)}$  and  $b_{\tau(N)}$ . This implies that we simply need to choose the endpoints to be those elements of  $\{b_{\tau(n)}\}_{n=1}^N$  that are largest; we can always permute the remaining (N-2) elements to ensure the permutation is convex afterward. Thus, relaxing the requirement that the permutation be convex, we choose a permutation  $\tau$  such that  $b_{\tau(1)} + b_{\tau(N)}$  is maximized. This definition motivates a new definition: We call a sequence  $\{b_n\}_{n=1}^N$  is **U-shaped** iff  $b_1 \geq b_i$  and  $b_N \geq b_i$  for  $i \in \{2, 3, \cdots, N-1\}$ .

**A Simple Algorithm.** The abstract discussion in the previous paragraph suggests a simple algorithm. First, we construct a real-valued sequence

$$b_{\tau(k)} \stackrel{\triangle}{=} \text{PMI}(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\widetilde{\boldsymbol{\pi}}_k))$$
 (14)

of length K where  $\tau \colon [K] \to [K]$  is a permutation and  $\mathrm{PMI}(\boldsymbol{q},\boldsymbol{c}_{\mathcal{D}}(\widetilde{\pi}_k))$  is defined in §3.2. Then, relaxing the requirement that the permutation be

<span id="page-6-2"></span> $<sup>^{10}</sup>$ E.g., the sequence [0, 1, 1, 1] has no convex permutation.

![](_page_7_Figure_0.jpeg)

Figure 5: When the position of the gold document changes, both PMI(q, c) and accuracy curves are U-shaped. In contrast, both curves are flat for non-gold (denoted by random) documents.

convex, we optimize

<span id="page-7-0"></span>
$$\tau^* = \operatorname*{arg\,max}_{\tau \in (\pi)} b_{\tau(1)} + b_{\tau(K)} \tag{15}$$

While, in general,  $\tau^*$  may not be convex, we do have a guarantee that  $\tau^*$  will induce a U-shaped sequence. To compute the optimization problem given in Eq. (15), we sort  $\tau \in (\pi)$  according to  $b_{\tau(1)} + b_{\tau(K)}$  in descending order, obtaining the sequence  $\{\tau_k\}_{k=1}^K$ . Then, we construct the resulting permutation  $\tau' = (\tau_1(1), \tau_2(1), \cdots, \tau_K(1))$ , among which  $d_{\tau(1)}$  is most likely to be the gold document.

#### 4.3 Results and Analysis

Shown in Table 3, both search by PMI and search by curvature can boost answer accuracy. On NQ-Open, where only one document in the sequence is relevant to the question, gold document reordering significantly improves the answer accuracy and narrows the gap to the upper bound. Furthermore, on the more challenging and practical QA benchmark ELI5, we also observe a modest improvement in answer accuracy, indicating that improving question likelihoods via document reordering can effectively obtain better LM responses.

Regarding efficiency, our proposed methods are mildly time-dependent thanks to the parallelizable computation of question likelihoods, where only the LM encoding module is used, with no reliance on LM decoding.<sup>11</sup> Shown in Table 4, in our

<span id="page-7-1"></span>

| Model                                  | Baseline                | PMI                             | Curvature                      | Upper<br>Bound          |  |  |
|----------------------------------------|-------------------------|---------------------------------|--------------------------------|-------------------------|--|--|
| NQ-Open (Answer Accuracy)              |                         |                                 |                                |                         |  |  |
| Mistral<br>LLaMA-3.1<br>LLaMA-3.1-Inst | 62.89<br>47.74<br>61.49 | 65.18<br>51.29<br>63.34         | 65.72<br>51.36<br>63.56        | 69.24<br>66.88<br>66.35 |  |  |
| ELI5 (Answer Accuracy)                 |                         |                                 |                                |                         |  |  |
| Mistral<br>LLaMA-3.1<br>LLaMA-3.1-Inst | 15.35<br>12.61<br>16.14 | <b>15.63</b> 12.73 <b>16.90</b> | 15.40<br><b>13.33</b><br>16.83 | -<br>-<br>-             |  |  |

Table 3: Performance of our methods on NQ-Open and ELI5, the number of documents K is set to 20 and 10, respectively. Mistral, LLaMA and LLaMA-Inst stands for Mistral-7B-Inst-v0.3, LLaMA-3.1-8B and LLaMA-3.1-8B-Inst respectively. Baseline refers to the mean performance over K random document shuffling on each instance. The upper bound on NQ-Open is calculated as the performance when positioning the gold document at the beginning of the document sequence, which is not applicable for ELI5 since no gold document is marked in this practical dataset.

experiments, the average runtime for decoding a response of an instance in ELI5 is 10 seconds, while it only takes an extra 0.8 seconds and 2 seconds, respectively, to encode the input prompts of naïve likelihood-based selection and gold document reordering. The increment in timely cost is marginal compared with heuristic prompt engineering which requires whole decoding to judge the prompt quality (e.g. an extra 10 seconds for decoding another candidate prompt).

In summary, both proposed methods are effective and efficient. Although the improvement on ELI5 is relatively marginal compared to that on NQ-Open, given the more challenging nature of long answers and no specified gold document on ELI5, it still indicates that optimizing prompts with  $\overrightarrow{p}(q \mid c)$  as a gauge is a promising direction.

**Experimental Setup.** We experiment on the ELI5 dataset and a subset of 500 questions from NQ-Open, using Mistral-7B-Inst-v0.3, LLaMA-3.1-8B, and LLaMA-3.1-8B-Inst. Each question is associated with 10 (on ELI5) and 20 (NQ-Open) retrieved documents.

#### **4.4** Synthetic Experiment

Real-world datasets might have been used during the training of LLMs. Thus, their likelihoods might exhibit an *exposure bias* (Bengio et al., 2015; Ran-

<span id="page-7-2"></span><sup>11</sup>LM decoding (i.e., generation) requires a runtime approximately proportional to the number of generated tokens. Empirically, the only extra computational time for our methods is on the encoding phase for calculating likelihoods, so the

overall runtime is the vanilla  $\mathrm{Runtime_{LM}}$  plus *one* extra LM going through, which is equivalent to generating the response with *one* additional token.

<span id="page-8-0"></span>

| Decoding | Likelihood Based | Gold Document |
|----------|------------------|---------------|
| 10s      | 0.8s             | 2s            |

Table 4: The average runtime for decoding an LLM response v.s. the extra time for the two proposed methods.

[zato et al.,](#page-10-8) [2016;](#page-10-8) [Cotterell et al.,](#page-9-12) [2024\)](#page-9-12). To avoid such potential bias, we follow [Liu et al.](#page-9-3) [\(2024\)](#page-9-3) and conduct a synthetic key–value retrieval experiment.

Key–Value Retrieval. To imitate questionanswering tasks on random strings, we construct Python-style key–value pairs in which the keys and values are UUID strings of 32 hexadecimal digits. An example is given in Figure [14.](#page-18-0) In Tables [5](#page-13-0) to [7,](#page-14-0) we observe that both PMI(q, <sup>c</sup>) and −→<sup>p</sup> (<sup>a</sup> <sup>|</sup> <sup>c</sup> · <sup>q</sup>) show synchronous U-shaped patterns as the location of the key in context changes, consistent with the RAG-based QA experiments in [§3.3,](#page-4-5) indicating the generalizability of the findings on unseen data.

## 5 Discussion

### 5.1 Instruction-tuned vs. Base Models

In our analysis, we find base LMs, e.g., LLaMA-3-8B, tend to be more sensitive to the permutation of the documents. Specifically, we observe that QA performance drops when the gold document is placed in the middle of the document sequence. On the other hand, the performance of instruction-tuned models is more robust to permutations of the documents in the context, as shown in Figure [4.](#page-5-1) However, we still do observe the existence U-shaped curve, but the drop in QA performance is less significant for the instruction-tuned model when the gold document is positioned at the middle.

The fact that PMI serves as a useful gauge for both the base and instruction-tuned models suggests that PMI(q, cD(π)) is affected little by the instruction tuning.

### 5.2 When Context is placed after Question

In our experiments, we only explore the correlation between PMI and accuracy when the question follows the context. However, one could also use a prompt template in which the context follows the question. We remark that in this case, PMI can be computed according to the equation

$$PMI(\boldsymbol{q}, \boldsymbol{c}) = \log \frac{\overrightarrow{p}(\boldsymbol{c} \mid \boldsymbol{q})}{\overrightarrow{p}(\boldsymbol{c})}.$$
 (16)

## 6 Conclusion

In our study, we analyzed the relationship between the PMI between question and context PMI(q, cD(π)) and question-answering performance under the retrieval-augmented generation framework. Through experimentation, we demonstrated that PMI(q, cD(π)) is affected by the order of documents in the input context. We find evidence for a positive correlation between question likelihood and answer accuracy at both the corpus level and instance level. Our findings show that it is possible to use PMI(q, cD(π)) to gauge language model performance and improve the quality of input prompts. We propose two practical methods for prompt optimization based on these findings. Experimental results show that both effectively and efficiently improve LM's accuracy on QA tasks, demonstrating that using PMI as a gauge for optimizing prompts is a promising direction.

### Limitations

One major limitation of our work is that only opensource LMs are studied in this work since we need full access probabilities under the LM. Thus, closed language models such as GPT-4 cannot be used for selecting permutations

Besides, our prompt modification is limited to document permutation in this work. Other prompt modifications may also contribute to obtaining a higher PMI(q, c) and improve QA performance. Considering that in this work we are taking the first step towards exploring the feasibility of prompt optimization without LM decoding, proving our hypothesis, and managing to optimize prompts with our findings, we leave other prompt optimizations for future study.

### References

<span id="page-8-2"></span>Akari Asai, Xinyan Yu, Jungo Kasai, and Hanna Hajishirzi. 2021. [One question answering model for](https://proceedings.neurips.cc/paper_files/paper/2021/file/3df07fdae1ab273a967aaa1d355b8bb6-Paper.pdf) [many languages with cross-lingual dense passage re](https://proceedings.neurips.cc/paper_files/paper/2021/file/3df07fdae1ab273a967aaa1d355b8bb6-Paper.pdf)[trieval.](https://proceedings.neurips.cc/paper_files/paper/2021/file/3df07fdae1ab273a967aaa1d355b8bb6-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 34, pages 7547–7560. Curran Associates, Inc.

<span id="page-8-1"></span>Samy Bengio, Oriol Vinyals, Navdeep Jaitly, and Noam Shazeer. 2015. [Scheduled sampling for sequence](https://proceedings.neurips.cc/paper_files/paper/2015/file/e995f98d56967d946471af29d7bf99f1-Paper.pdf) [prediction with recurrent neural networks.](https://proceedings.neurips.cc/paper_files/paper/2015/file/e995f98d56967d946471af29d7bf99f1-Paper.pdf) In *Proceedings of the 28th International Conference on Neural Information Processing Systems - Volume 1*, NIPS'15, page 1171–1179, Cambridge, MA, USA. MIT Press.

- <span id="page-9-15"></span>Sebastian Borgeaud, Arthur Mensch, Jordan Hoffmann, Trevor Cai, Eliza Rutherford, Katie Millican, George Van Den Driessche, Jean-Baptiste Lespiau, Bogdan Damoc, Aidan Clark, et al. 2022. [Improving lan](https://proceedings.mlr.press/v162/borgeaud22a/borgeaud22a.pdf)[guage models by retrieving from trillions of tokens.](https://proceedings.mlr.press/v162/borgeaud22a/borgeaud22a.pdf) In *International conference on machine learning*, pages 2206–2240. PMLR.
- <span id="page-9-9"></span>Craig Boutilier, Nir Friedman, Moises Goldszmidt, and Daphne Koller. 1996. Context-specific independence in Bayesian networks. In *Proceedings of the Twelfth International Conference on Uncertainty in Artificial Intelligence*, page 115–123.
- <span id="page-9-12"></span>Ryan Cotterell, Anej Svete, Clara Meister, Tianyu Liu, and Li Du. 2024. [Formal aspects of language model](https://arxiv.org/abs/2311.04329)[ing.](https://arxiv.org/abs/2311.04329) *Preprint*, arXiv:2311.04329.
- <span id="page-9-14"></span>Sabit Ekin. 2023. [Prompt engineering for chatgpt: a](https://www.techrxiv.org/users/690417/articles/681648-prompt-engineering-for-chatgpt-a-quick-guide-to-techniques-tips-and-best-practices) [quick guide to techniques, tips, and best practices.](https://www.techrxiv.org/users/690417/articles/681648-prompt-engineering-for-chatgpt-a-quick-guide-to-techniques-tips-and-best-practices) *Authorea Preprints*.
- <span id="page-9-7"></span>Angela Fan, Yacine Jernite, Ethan Perez, David Grangier, Jason Weston, and Michael Auli. 2019. [ELI5:](https://doi.org/10.18653/v1/P19-1346) [Long form question answering.](https://doi.org/10.18653/v1/P19-1346) In *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics*, pages 3558–3567, Florence, Italy. Association for Computational Linguistics.
- <span id="page-9-1"></span>Tianyu Gao, Adam Fisch, and Danqi Chen. 2021. [Making pre-trained language models better few-shot](https://doi.org/10.18653/v1/2021.acl-long.295) [learners.](https://doi.org/10.18653/v1/2021.acl-long.295) In *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, pages 3816–3830, Online. Association for Computational Linguistics.
- <span id="page-9-10"></span>Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. 2023. [Enabling large language models to generate](https://doi.org/10.18653/v1/2023.emnlp-main.398) [text with citations.](https://doi.org/10.18653/v1/2023.emnlp-main.398) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pages 6465–6488, Singapore. Association for Computational Linguistics.
- <span id="page-9-13"></span>Louie Giray. 2023. [Prompt engineering with chatgpt:](https://link.springer.com/article/10.1007/s10439-023-03272-4) [a guide for academic writers.](https://link.springer.com/article/10.1007/s10439-023-03272-4) *Annals of biomedical engineering*, 51(12):2629–2633.
- <span id="page-9-8"></span>Hila Gonen, Srini Iyer, Terra Blevins, Noah Smith, and Luke Zettlemoyer. 2023. [Demystifying prompts in](https://doi.org/10.18653/v1/2023.findings-emnlp.679) [language models via perplexity estimation.](https://doi.org/10.18653/v1/2023.findings-emnlp.679) In *Findings of the Association for Computational Linguistics: EMNLP 2023*, pages 10136–10148, Singapore. Association for Computational Linguistics.
- <span id="page-9-17"></span>Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel, Piotr Bojanowski, Armand Joulin, and Edouard Grave. 2022. [Unsupervised dense infor](https://arxiv.org/abs/2112.09118)[mation retrieval with contrastive learning.](https://arxiv.org/abs/2112.09118) *Preprint*, arXiv:2112.09118.
- <span id="page-9-16"></span>Gautier Izacard and Edouard Grave. 2021. [Leveraging](https://doi.org/10.18653/v1/2021.eacl-main.74) [passage retrieval with generative models for open do](https://doi.org/10.18653/v1/2021.eacl-main.74)[main question answering.](https://doi.org/10.18653/v1/2021.eacl-main.74) In *Proceedings of the 16th*

- *Conference of the European Chapter of the Association for Computational Linguistics: Main Volume*, pages 874–880, Online. Association for Computational Linguistics.
- <span id="page-9-2"></span>Gautier Izacard, Patrick Lewis, Maria Lomeli, Lucas Hosseini, Fabio Petroni, Timo Schick, Jane Dwivedi-Yu, Armand Joulin, Sebastian Riedel, and Edouard Grave. 2024. [Atlas: Few-shot learning with retrieval](https://dl.acm.org/doi/10.5555/3648699.3648950) [augmented language models.](https://dl.acm.org/doi/10.5555/3648699.3648950) *J. Mach. Learn. Res.*, 24(1).
- <span id="page-9-11"></span>Albert Q. Jiang, Alexandre Sablayrolles, Arthur Mensch, Chris Bamford, Devendra Singh Chaplot, Diego de las Casas, Florian Bressand, Gianna Lengyel, Guillaume Lample, Lucile Saulnier, Lélio Renard Lavaud, Marie-Anne Lachaux, Pierre Stock, Teven Le Scao, Thibaut Lavril, Thomas Wang, Timothée Lacroix, and William El Sayed. 2023. [Mistral 7B.](https://arxiv.org/abs/2310.06825) *Preprint*, arXiv:2310.06825.
- <span id="page-9-4"></span>Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. 2020. [Dense passage retrieval for open](https://doi.org/10.18653/v1/2020.emnlp-main.550)[domain question answering.](https://doi.org/10.18653/v1/2020.emnlp-main.550) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 6769–6781, Online. Association for Computational Linguistics.
- <span id="page-9-5"></span>Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Jacob Devlin, Kenton Lee, Kristina Toutanova, Llion Jones, Matthew Kelcey, Ming-Wei Chang, Andrew M. Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov. 2019. [Natu](https://doi.org/10.1162/tacl_a_00276)[ral questions: A benchmark for question answering](https://doi.org/10.1162/tacl_a_00276) [research.](https://doi.org/10.1162/tacl_a_00276) *Transactions of the Association for Computational Linguistics*, 7:452–466.
- <span id="page-9-6"></span>Kenton Lee, Ming-Wei Chang, and Kristina Toutanova. 2019. [Latent retrieval for weakly supervised open](https://doi.org/10.18653/v1/P19-1612) [domain question answering.](https://doi.org/10.18653/v1/P19-1612) In *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics*, pages 6086–6096, Florence, Italy. Association for Computational Linguistics.
- <span id="page-9-0"></span>Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. 2020. [Retrieval-augmented generation for knowledge](https://dl.acm.org/doi/pdf/10.5555/3495724.3496517)[intensive nlp tasks.](https://dl.acm.org/doi/pdf/10.5555/3495724.3496517) In *Proceedings of the 34th International Conference on Neural Information Processing Systems*, NIPS '20, Red Hook, NY, USA. Curran Associates Inc.
- <span id="page-9-18"></span>Nelson Liu, Tianyi Zhang, and Percy Liang. 2023. [Eval](https://doi.org/10.18653/v1/2023.findings-emnlp.467)[uating verifiability in generative search engines.](https://doi.org/10.18653/v1/2023.findings-emnlp.467) In *Findings of the Association for Computational Linguistics: EMNLP 2023*, pages 7001–7025, Singapore. Association for Computational Linguistics.
- <span id="page-9-3"></span>Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy

- Liang. 2024. [Lost in the middle: How language mod](https://doi.org/10.1162/tacl_a_00638)[els use long contexts.](https://doi.org/10.1162/tacl_a_00638) *Transactions of the Association for Computational Linguistics*, 12:157–173.
- <span id="page-10-1"></span>Lijia Ma, Xingchen Xu, and Yong Tan. 2024. [Craft](https://arxiv.org/pdf/2402.19421)[ing knowledge: Exploring the creative mecha](https://arxiv.org/pdf/2402.19421)[nisms of chat-based search engines.](https://arxiv.org/pdf/2402.19421) *arXiv preprint arXiv:2402.19421*.
- <span id="page-10-10"></span>Ggaliwango Marvin, Nakayiza Hellen, Daudi Jjingo, and Joyce Nakatumba-Nabende. 2023. [Prompt engi](https://arxiv.org/pdf/2402.07927)[neering in large language models.](https://arxiv.org/pdf/2402.07927) In *International conference on data intelligence and cognitive informatics*, pages 387–402. Springer.
- <span id="page-10-15"></span>Jacob Menick, Maja Trebacz, Vladimir Mikulik, John Aslanides, Francis Song, Martin Chadwick, Mia Glaese, Susannah Young, Lucy Campbell-Gillingham, Geoffrey Irving, et al. 2022. [Teaching](https://arxiv.org/pdf/2203.11147) [language models to support answers with verified](https://arxiv.org/pdf/2203.11147) [quotes.](https://arxiv.org/pdf/2203.11147) *arXiv preprint arXiv:2203.11147*.
- <span id="page-10-14"></span>Reiichiro Nakano, Jacob Hilton, Suchir Balaji, Jeff Wu, Long Ouyang, Christina Kim, Christopher Hesse, Shantanu Jain, Vineet Kosaraju, William Saunders, et al. 2021. [Webgpt: Browser-assisted question](https://arxiv.org/pdf/2112.09332)[answering with human feedback.](https://arxiv.org/pdf/2112.09332) *arXiv preprint arXiv:2112.09332*.
- <span id="page-10-2"></span>Jianmo Ni, Chen Qu, Jing Lu, Zhuyun Dai, Gustavo Hernandez Abrego, Ji Ma, Vincent Zhao, Yi Luan, Keith Hall, Ming-Wei Chang, and Yinfei Yang. 2022. [Large dual encoders are generalizable retrievers.](https://doi.org/10.18653/v1/2022.emnlp-main.669) In *Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing*, pages 9844–9855, Abu Dhabi, United Arab Emirates. Association for Computational Linguistics.
- <span id="page-10-12"></span>Fabio Petroni, Patrick Lewis, Aleksandra Piktus, Tim Rocktäschel, Yuxiang Wu, Alexander H. Miller, and Sebastian Riedel. 2020. [How context affects lan](https://openreview.net/forum?id=025X0zPfn)[guage models' factual predictions.](https://openreview.net/forum?id=025X0zPfn) In *Automated Knowledge Base Construction*.
- <span id="page-10-13"></span>Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Dmytro Okhonko, Samuel Broscheit, Gautier Izacard, Patrick Lewis, Barlas Oguz, Edouard Grave, Wen-tau ˘ Yih, et al. 2021. [The web is your oyster-knowledge](https://arxiv.org/pdf/2112.09924)[intensive nlp against a very large web corpus.](https://arxiv.org/pdf/2112.09924) *arXiv preprint arXiv:2112.09924*.
- <span id="page-10-11"></span>Reid Pryzant, Dan Iter, Jerry Li, Yin Lee, Chenguang Zhu, and Michael Zeng. 2023. [Automatic prompt op](https://doi.org/10.18653/v1/2023.emnlp-main.494)[timization with "gradient descent" and beam search.](https://doi.org/10.18653/v1/2023.emnlp-main.494) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pages 7957–7968, Singapore. Association for Computational Linguistics.
- <span id="page-10-16"></span>Jirui Qi, Gabriele Sarti, Raquel Fernández, and Arianna Bisazza. 2024. [Model internals-based answer attribu](https://arxiv.org/pdf/2406.13663)[tion for trustworthy retrieval-augmented generation.](https://arxiv.org/pdf/2406.13663) *arXiv preprint arXiv:2406.13663*.

- <span id="page-10-8"></span>Marc'Aurelio Ranzato, Sumit Chopra, Michael Auli, and Wojciech Zaremba. 2016. [Sequence level train](http://arxiv.org/abs/1511.06732)[ing with recurrent neural networks.](http://arxiv.org/abs/1511.06732) In *4th International Conference on Learning Representations, ICLR 2016, San Juan, Puerto Rico, May 2-4, 2016, Conference Track Proceedings*.
- <span id="page-10-0"></span>Sander Schulhoff, Michael Ilie, Nishant Balepur, Konstantine Kahadze, Amanda Liu, Chenglei Si, Yinheng Li, Aayush Gupta, HyoJung Han, Sevien Schulhoff, et al. 2024. [The prompt report: A system](https://arxiv.org/pdf/2406.06608)[atic survey of prompting techniques.](https://arxiv.org/pdf/2406.06608) *arXiv preprint arXiv:2406.06608*.
- <span id="page-10-7"></span>Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, Aurelien Rodriguez, Armand Joulin, Edouard Grave, and Guillaume Lample. 2023. [Llama: Open](https://arxiv.org/abs/2302.13971) [and efficient foundation language models.](https://arxiv.org/abs/2302.13971) *Preprint*, arXiv:2302.13971.
- <span id="page-10-5"></span>Tim Vieira, Ben LeBrun, Mario Giulianelli, Juan Luis Gastaldi, Brian DuSell, John Terilla, Timothy J. O'Donnell, and Ryan Cotterell. 2024. [From lan](https://arxiv.org/abs/2412.03719)[guage models over tokens to language models over](https://arxiv.org/abs/2412.03719) [characters.](https://arxiv.org/abs/2412.03719) *Preprint*, arXiv:2412.03719.
- <span id="page-10-3"></span>Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou. 2023. [Chain-of-thought prompting elic](https://arxiv.org/abs/2201.11903)[its reasoning in large language models.](https://arxiv.org/abs/2201.11903) *Preprint*, arXiv:2201.11903.
- <span id="page-10-4"></span>Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, and Karthik Narasimhan. 2023. [Tree of thoughts: Deliber](https://arxiv.org/abs/2305.10601)[ate problem solving with large language models.](https://arxiv.org/abs/2305.10601) *Preprint*, arXiv:2305.10601.
- <span id="page-10-6"></span>Yao Zhao, Mikhail Khalman, Rishabh Joshi, Shashi Narayan, Mohammad Saleh, and Peter J Liu. 2023. [Calibrating sequence likelihood improves conditional](https://openreview.net/forum?id=0qSOodKmJaN) [language generation.](https://openreview.net/forum?id=0qSOodKmJaN) In *The Eleventh International Conference on Learning Representations*.
- <span id="page-10-9"></span>Yongchao Zhou, Andrei Ioan Muresanu, Ziwen Han, Keiran Paster, Silviu Pitis, Harris Chan, and Jimmy Ba. 2023. [Large language models are human-level](https://openreview.net/forum?id=92gvk82DE-) [prompt engineers.](https://openreview.net/forum?id=92gvk82DE-) In *The Eleventh International Conference on Learning Representations*.

## A Related Work

#### A.1 Prompt Engineering

Prompt engineering is important for making the best use of LMs in real-world applications [\(Giray,](#page-9-13) [2023;](#page-9-13) [Ekin,](#page-9-14) [2023;](#page-9-14) [Gonen et al.,](#page-9-8) [2023\)](#page-9-8). The most straightforward prompt engineering method is to manually design prompts using heuristics, which requires human experts to design prompts based on domain-specific knowledge and select the prompts that lead to better performance on downstream tasks [\(Zhou et al.,](#page-10-9) [2023;](#page-10-9) [Marvin et al.,](#page-10-10) [2023\)](#page-10-10). Meanwhile, another line of work explores automatic approaches for prompts engineering [\(Gao et al.,](#page-9-1) [2021;](#page-9-1) [Pryzant et al.,](#page-10-11) [2023\)](#page-10-11). However, they both require decoding for outputs from LMs to evaluate the quality of prompts, thus incurring high computational costs.

#### A.2 Retrieval-Augmented Generation

Retrieval-augmented generation is a technique for improving LMs' ability to solve knowledge-intensive tasks [\(Lewis et al.,](#page-9-0) [2020;](#page-9-0) [Asai et al.,](#page-8-2) [2021;](#page-8-2) [Borgeaud et al.,](#page-9-15) [2022\)](#page-9-15). In the RAG framework, a set of documents relevant to a user query is retrieved from an external source and inserted into prompts as a context, to provide additional information to the LM and improve response quality [\(Petroni et al.,](#page-10-12) [2020;](#page-10-12) [Lewis et al.,](#page-9-0) [2020\)](#page-9-0). RAG tasks can be divided into two types: short-form and long-form, depending on the topic of the questions and the format of the expected answers. Short-form QA [\(Izacard and Grave,](#page-9-16) [2021;](#page-9-16) [Liu et al.,](#page-9-3) [2024\)](#page-9-3) usually concerns factual questions about real-world facts. The expected answers are often unambiguous and concrete words or short phrases. Long-form QA [\(Fan et al.,](#page-9-7) [2019;](#page-9-7) [Gao et al.,](#page-9-10) [2023\)](#page-9-10) involves *how*, *why*, and *what* questions that seek more comprehensive responses.

### A.3 Effect of Document Order

[Liu et al.](#page-9-3) [\(2024\)](#page-9-3) finds that LMs perform better when the document with relevant information is positioned at the beginning or the end of the prompt using under RAG framework.[12](#page-11-2) Specifically, when moving the task-relevant information from the beginning to the end of the document sequence, answer accuracy exhibits a U-shaped trend on a multi-document QA task and a synthetic key–value retrieval task, both using RAG pipelines. However, [Liu et al.](#page-9-3) [\(2024\)](#page-9-3) mainly focuses on an empirical study with less in-depth analysis, resulting in a gap between the phenomenon and its practical implications. In this work, we attempt to bridge this gap.

### <span id="page-11-1"></span>B Illustration of Evaluation Metrics

The evaluation metrics for NQ-Open and ELI5 are illustrated with two examples in Figure [6.](#page-12-0)

### <span id="page-11-0"></span>C Datasets

NQ-Open. We first experiment on the NQ-Open dataset following [Liu et al.](#page-9-3) [\(2024\)](#page-9-3). This dataset covers 2655 factual questions curated from the Natural Questions dataset [\(Kwiatkowski et al.,](#page-9-5) [2019;](#page-9-5) [Lee et al.,](#page-9-6) [2019\)](#page-9-6) under CC-BY-SA-3.0 license. Each question is accompanied by K documents retrieved from Wikipedia, among which *exactly one* contains the answer to the question, namely the gold document. The remaining k − 1 documents are termed distractors, which are relevant to the topic of the question but do not contain any ground truth answers, retrieved using Contriever [\(Izacard et al.,](#page-9-17) [2022\)](#page-9-17). In our experiments, the total number of documents K is taken to be {10, 20, 30}. [13](#page-11-3)

ELI5. To validate the generality of our findings, we also experiment on an open-ended non-factual QA dataset ELI5 [\(Fan et al.,](#page-9-7) [2019\)](#page-9-7) with BSD license. ELI5 consists of questions beginning with *how*, *why* or *what* curated from the Reddit forum "Explain Like I'm Five"[14](#page-11-4), where the answers are expected to be more comprehensive and diverse. Each question is accompanied by K documents retrieved from

<span id="page-11-3"></span><span id="page-11-2"></span><sup>12</sup>In [Liu et al.'](#page-9-3)s [\(2024\)](#page-9-3) experimental settings, the gold document is unique in a prompt for each question.

<sup>13</sup>We remark that NQ-Open was specifically synthesized to examine how answer accuracy is affected by changing the position of relevant information. In real-world applications, the retrieved documents for one question may contain multiple gold documents or none. Nevertheless, it mimics the RAG setup underlying many commercial generative search and QA systems.

<span id="page-11-4"></span><sup>14</sup><https://www.reddit.com/r/explainlikeimfive/>

<span id="page-12-0"></span>Southend Pier **NQ-Open** What is the longest pier in the uk? According to the provided documents, the answer is Southend Pier. **Question LLM response Ground truth (Short phrase)** ① Compressing algorithms search for patterns that appear multiple times within the data. ② The patterns are then replaced with a shorter symbol. ③ A "dictionary" is created to record what each symbol means. When data is compressed or zipped, what is happening to the data? **ELI5** The compression algorithm will detect the duplicated patterns. It will further replace them with simpler symbols to save space. **Question LLM response Ground truth (Sub-claims) Accuracy** (Sub-string exact match): 100% **Accuracy** (Claim recall)**:** 66.7%

Figure 6: Evaluation metrics used in our experiments. On NQ-Open, the evaluation metric is exact string match. On ELI5, a pretrained NLI model is used to evaluate whether the LM output entails the reference claims.

```
Write a high-quality answer for the given question using only the provided search results (some
of which might be irrelevant).
Document [1](Title: Southend Pier) Southend Pier is a major landmark in . . .
Document [2](Title: Llandudno Pier) Llandudno Pier Llandudno Pier is a Grade II* listed pier
in the seaside resort of Llandudno. . .
Document [3](Title: Garth Pier) Garth Pier Garth Pier is a Grade II listed structure in Bangor. . .
                                              . . .
Question: what is the longest pier in the uk
According to the provided documents, the answer is Southend Pier.
```

<span id="page-13-0"></span>Figure 7: An example prompt and LM output on NQ-Open. The prompt comprises (1) an instruction that describes the task to be solved, (2) a context that contains the information for solving the task, in which the gold document contains the ground truth answer, and (3) a question that describes the specific query. At the end of the prompt, we append an exemplar output that gives the ground truth answer to the question for evaluating the likelihood of the answer.

| Key Location | −→p<br>(q   c) | −→p<br>(a   c · q) |
|--------------|----------------|--------------------|
| 0            | -3.96          | -0.76              |
| 34           | -6.60          | -0.87              |
| 69           | -7.87          | -0.82              |
| 104          | -8.70          | -1.08              |
| 139          | -8.03          | -0.76              |

Table 5: Question likelihood and answer likelihood on synthetic key–value retrieval task using Llama-3.1-8B-Instruct model.

Sphere [\(Piktus et al.,](#page-10-13) [2021\)](#page-10-13)—a filtered version of Common Crawl[15](#page-13-1), where <sup>K</sup> is taken to be {5, <sup>10</sup>, <sup>20</sup>} to avoid truncation due to the long questions and LMs responses for the long-form QA task. In contrast to NQ-Open, ELI5 does not provide the annotations of gold documents, which aligns with real-world RAG application scenarios, making it a more practical and challenging dataset [\(Nakano et al.,](#page-10-14) [2021;](#page-10-14) [Menick](#page-10-15) [et al.,](#page-10-15) [2022;](#page-10-15) [Liu et al.,](#page-9-18) [2023\)](#page-9-18).

### D Prompt Templates

The prompt templates used for our experiments are given in Figures 7–9.

### E Full Results on NQ-Open

We show the full results on NQ-Open in Figures 10–13.

## F Synthetic Experiment

<span id="page-13-1"></span><sup>15</sup><https://commoncrawl.org>

| Key Location | −→p<br>(q   c) | −→p<br>(a   c · q) |
|--------------|----------------|--------------------|
| 0            | -3.01          | -0.08              |
| 34           | -6.22          | -0.15              |
| 69           | -6.86          | -0.31              |
| 104          | -7.87          | -0.27              |
| 139          | -7.33          | -0.07              |

Table 6: Question likelihood and answer likelihood on synthetic key–value retrieval task using Llama-3.1-8B model.

```
Instruction: Write an accurate, engaging, and concise answer for the given question using
only the provided search results (some of which might be irrelevant). Use an unbiased and
journalistic tone.
Document [1](Title: Trash Islands - the Ocean Garbage Patch): Trash Islands Trash Islands of
the Pacific and Atlantic Oceans. . .
Document [2](Title: Where does our garbage go? - Sea Turtle Camp): Pacific Garbage Patch
Landfills are a common human solution for disposing of trash on land. . .
Document [3](Title: Plastic pollution crisis: How waste ends up in our oceans – Y108): our
ecosystems as a whole. Plastic is non-biodegradable. Every year, about 8-million tons of
plastic. . .
                                            . . .
Question: how does so much of our trash end up in the ocean?
According to various sources, a significant portion of the world's trash ends up in the ocean
due to a combination of factors. While it's often. . . individuals is necessary to mitigate the
problem of plastic pollution in the world.
[Answer length: 242 words]
```

Figure 8: An example prompt and LM output on ELI5. The prompt comprises (1) an instruction that describes the task to be solved, consistent with previous works on ELI5 [\(Gao et al.,](#page-9-10) [2023;](#page-9-10) [Qi et al.,](#page-10-16) [2024\)](#page-10-16), (2) a context that contains the information for solving the task, but *no gold document* is marked, and (3) a question that describes the specific query. At the end of the prompt, we append an exemplar output that gives the ground truth answer to the question for evaluating the likelihood of the answer.

```
{
     " 749 d280d -8 d74 -4 a2b -87 fa - e2a13b689892 " :
          " 51 f95eb8 -1 f16 -4 bbf - a7be -6109 e581fc04 " ,
     " 6618 b34a -08 b6 -46 a8 - a438 - aedc1a2a4635 " :
          " 3 e93dc61 -1 e82 -46 b1 -94 be -7 ef2e63746e5 " ,
     ...
}
Key : " 749 d280d -8 d74 -4 a2b -87 fa - e2a13b689892 "
Value :
```

Figure 9: An example of synthetic data for key–value retrieval.

| Key Location | −→p<br>(q   c) | −→p<br>(a   c · q) |
|--------------|----------------|--------------------|
| 0            | -4.03          | -0.00              |
| 34           | -6.31          | -0.12              |
| 69           | -8.15          | -0.23              |
| 104          | -9.67          | -0.15              |
| 139          | -8.77          | -0.04              |

<span id="page-14-0"></span>Table 7: Question likelihood and answer likelihood on synthetic key–value retrieval task using Mistral-7B-Instruct model.

![](_page_15_Figure_0.jpeg)

Figure 10: QA accuracy, PMI, and log odds ratio of answer likelihood on 10 docs.

![](_page_16_Figure_0.jpeg)

Figure 11: QA accuracy, PMI, and log odds ratio of answer likelihood on 10 docs.

![](_page_17_Figure_0.jpeg)

Figure 12: QA accuracy, PMI, and log odds ratio of answer likelihood on 20 docs.

![](_page_18_Figure_0.jpeg)

Figure 13: QA accuracy, PMI, and log odds ratio of answer likelihood on 30 docs.

```
{
    "ebad6435-1e86-4b9e-836a-9a88a8c93743":
        "c13ac8fc-81fe-408a-bf8f-914b6b8dc310",
    "33e652a0-fbcd-4abd-9935-14043ef82de9":
        "339ffb66-ec38-4d2a-a99f-67755d87eec3",
    "7a990232-7ddd-41b6-a8eb-1c61dc96da3c":
        "0d233f17-9d85-441e-868c-aa682d3dbbe7",
        ...
}
Key: "7a990232-7ddd-41b6-a8eb-1c61dc96da3c"
Value: "0d233f17-9d85-441e-868c-aa682d3dbbe7"
```

Figure 14: Example input for key-value retrieval task.

#### <span id="page-19-0"></span>**G** Proof of Proposition 2.1

**Proposition 2.1.** Under assumptions given in Assumption 2.1, we have

$$\log \frac{\overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))}{1 - \overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{q} \cdot \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))}$$

$$= PMI(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})) + C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}))$$
(6)

for an answer-dependent constant  $C(\mathbf{a}, \mathbf{c}_{\mathcal{D}}(\pi))$ .

*Proof.* First note that, by Bayes' rule, we have

$$\overrightarrow{p}(\boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}) \cdot \boldsymbol{q}) = \frac{\overrightarrow{p}(\square \boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})) \overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}) \square \boldsymbol{a})}{\overrightarrow{p}(\boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi}) \cdot \boldsymbol{q})}.$$
(17)

Then,

$$\log \frac{\overrightarrow{p}(\mathbf{a} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))}{1 - \overrightarrow{p}(\mathbf{a} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))} = \log \frac{\overrightarrow{p}(\mathbf{a} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))}{\sum_{\bar{\mathbf{a}} \in \Sigma^*} \mathbb{1}\{\bar{\mathbf{a}} \not\preceq \mathbf{a}\} \overrightarrow{p}(\bar{\mathbf{a}} \mid \mathbf{q} \cdot \mathbf{c}_{\mathcal{D}}(\pi))}$$
(18a)

$$= \log \frac{\frac{\overrightarrow{p}(\square \boldsymbol{a}|\boldsymbol{c}_{\mathcal{D}}(\pi))\overrightarrow{p}(\boldsymbol{q}|\boldsymbol{c}_{\mathcal{D}}(\pi)\square \boldsymbol{a})}{\overrightarrow{p}(\boldsymbol{c}_{\mathcal{D}}(\pi)\cdot\boldsymbol{q})}}{\sum_{\bar{\boldsymbol{a}}\in\Sigma^*} \mathbb{1}\{\bar{\boldsymbol{a}} \not\preceq \boldsymbol{a}\} \frac{\overrightarrow{p}(\square \bar{\boldsymbol{a}}|\boldsymbol{c}_{\mathcal{D}}(\pi))\overrightarrow{p}(\boldsymbol{q}|\boldsymbol{c}_{\mathcal{D}}(\pi)\square \bar{\boldsymbol{a}})}{\overrightarrow{p}(\boldsymbol{c}_{\mathcal{D}}(\pi)\cdot\boldsymbol{q})}}$$
(Bayes' rule) (18b)

$$= \log \frac{\overrightarrow{p}(\square \boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\pi)) \overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\pi) \square \boldsymbol{a})}{\sum_{\bar{\boldsymbol{a}} \in \Sigma^*} \mathbb{1}\{\bar{\boldsymbol{a}} \not\preceq \boldsymbol{a}\} \overrightarrow{p}(\square \bar{\boldsymbol{a}} \mid \boldsymbol{c}_{\mathcal{D}}(\pi)) \overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\pi) \square \bar{\boldsymbol{a}})}$$
(18c)

$$= \log \frac{\overrightarrow{p}(\square \boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\pi)) \overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}{\left(\sum_{\overline{\boldsymbol{a}} \in \Sigma^*} \mathbb{1}\{\overline{\boldsymbol{a}} \not\preceq \boldsymbol{a}\} \overrightarrow{p}(\square \overline{\boldsymbol{a}} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))\right) \overrightarrow{p}(\boldsymbol{q})}$$
(Assumption 2.1)

$$= \log \frac{\overrightarrow{p}(\square \boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}{\sum_{\bar{\boldsymbol{a}} \in \Sigma^*} \mathbb{1}\{\bar{\boldsymbol{a}} \not\preceq \boldsymbol{a}\} \overrightarrow{p}(\square \bar{\boldsymbol{a}} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))} \frac{\overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}{\overrightarrow{p}(\boldsymbol{q})}$$
(18e)

$$= \underbrace{\log \frac{\overrightarrow{p}(\square \boldsymbol{a} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}{\sum_{\bar{\boldsymbol{a}} \in \Sigma^*} \mathbb{1}\{\bar{\boldsymbol{a}} \not\preceq \boldsymbol{a}\} \overrightarrow{p}(\square \bar{\boldsymbol{a}} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}}_{\triangleq C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\pi))} + \log \frac{\overrightarrow{p}(\boldsymbol{q} \mid \boldsymbol{c}_{\mathcal{D}}(\pi))}{\overrightarrow{p}(\boldsymbol{q})}$$

$$\triangleq C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\pi))$$

$$(18f)$$

$$= PMI(\boldsymbol{q}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})) + C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\boldsymbol{\pi})), \tag{18g}$$

where  $C(\boldsymbol{a}, \boldsymbol{c}_{\mathcal{D}}(\pi))$  is constant with respect to  $\boldsymbol{q}$ .