# Finetuning Generative Large Language Models with Discrimination Instructions for Knowledge Graph Completion

Yang Liu 1 [,](https://orcid.org/0000-0002-4663-2439) Xiaobin Tian 1 [,](https://orcid.org/0000-0001-6570-6424) Zequn Sun1( ) [,](https://orcid.org/0000-0003-4177-9199) and Wei Hu 1 , [2](https://orcid.org/0000-0003-3635-6335)

> <sup>1</sup> State Key Laboratory for Novel Software Technology, Nanjing University, Nanjing 210023, China

<sup>2</sup> National Institute of Healthcare Data Science, Nanjing University, Nanjing 210093, China

{yliu20, xbtian}.nju@gmail.com, {sunzq, whu}@nju.edu.cn

Abstract. Traditional knowledge graph (KG) completion models learn embeddings to predict missing facts. Recent works attempt to complete KGs in a text-generation manner with large language models (LLMs). However, they need to ground the output of LLMs to KG entities, which inevitably brings errors. In this paper, we present a finetuning framework, DIFT, aiming to unleash the KG completion ability of LLMs and avoid grounding errors. Given an incomplete fact, DIFT employs a lightweight model to obtain candidate entities and finetunes an LLM with discrimination instructions to select the correct one from the given candidates. To improve performance while reducing instruction data, DIFT uses a truncated sampling method to select useful facts for finetuning and injects KG embeddings into the LLM. Extensive experiments on benchmark datasets demonstrate the effectiveness of our proposed framework.

Keywords: Knowledge graph completion · Large language model · Instruction tuning.

### 1 Introduction

Knowledge graphs (KGs) store real-world facts in multi-relational structures, where nodes represent entities and edges are labeled with relations to describe facts in the form of triplets like (head entity , relation , tail entity). KGs often face the incompleteness problem [\[12\]](#page-16-0), which adversely affects the performance of downstream knowledge-intensive applications such as question answering [\[11](#page-16-1) [,24](#page-17-0) ] and recommender systems [\[13\]](#page-16-2). KG completion models are designed to resolve the incompleteness issue by inferring the missing facts based on the facts already in KGs. Conventional KG completion models are based on KG embeddings. Given an incomplete fact where either the head or tail entity is missing and requires prediction, embedding-based models first compute the plausibility for candidate entities using an embedding function of entities and relations and then rank them to obtain predictions. Entity and relation embeddings can be learned based on either graph structures [\[1,](#page-16-3)[3](#page-16-4)[,35,](#page-17-1)[39\]](#page-17-2) or text attributes [\[17,](#page-16-5)[20,](#page-16-6)[29,](#page-17-3)[30,](#page-17-4)[36\]](#page-17-5).

In recent years, motivated by the impressive performance of generative pretrained language models (PLMs) such as T5 [\[22\]](#page-17-6) and BART [\[16\]](#page-16-7), some models convert KG completion to a sequence-to-sequence generation task [\[4,](#page-16-8)[23,](#page-17-7)[33\]](#page-17-8). Given an incomplete fact, generation-based models first construct a natural language query with text attributes of the given entity and relation, and then ask a generative PLM to generate an answer directly. Finally, they ground the answer to the entities in the KG, which, however, inevitably brings errors.

More recently, some work attempts to conduct KG completion using large language models (LLMs), such as ChatGPT and LLaMA [\[27\]](#page-17-9). Given an incomplete fact, KICGPT [\[31\]](#page-17-10) first constructs query prompts with demonstration facts and the top-m candidate entities predicted by a pre-trained KG completion model. Then, it engages in a multi-round online interaction with ChatGPT using these query prompts. Finally, it rearranges these candidates according to the response of ChatGPT. This method may not make full use of the reasoning ability of LLMs because the LLMs (e.g., ChatGPT) may not fit the KG well. Besides, the multi-round interaction costs too much. In contrast, KG-LLM [\[37\]](#page-17-11) converts KG completion queries to natural language questions and finetunes LLMs (e.g., LLaMA-7B) to generate answers. It then uses a heuristic method to ground the output of LLMs to KG entities: if the output text contains an entity name, then this entity is selected as the answer. The errors in such a grounding process cause KG-LLM to lag behind the state-of-the-art KG completion models. Besides, generation-based models obtain multiple output texts and rank them by the generation probabilities, which is time-consuming and unsuitable for LLMs.

To address the above issues and fully exploit the reasoning ability of LLMs, we propose DIFT that finetunes LLMs with discrimination instructions for KG completion. To avoid the grounding errors in generation-based models, DIFT constructs discrimination instructions that require LLMs to select an entity from the given candidates as the answer. Specifically, it first employs a lightweight embedding-based model to provide the top-m candidate entities for each incomplete fact, and adds the names of these entities to the prompts as candidate answers to the KG completion query. Then, it finetunes an LLM with parameter-efficient finetuning methods like LoRA [\[14\]](#page-16-9) to select one entity name from the prompt as the output. In this way, the LLM gets enhanced by finetuning and can always generate entities in the KG instead of unconstrained generation.

However, training the LLM with parameter-efficient finetuning methods is still costly. To further reduce the computation cost of finetuning, we design a truncated sampling method that can select useful samples from the KG for instruction construction. Let us assume that we get an example for finetuning with the query q = (h, r, ?) and the answer entity t. We use the pre-trained embedding-based model to compute the score of the fact (h, r, t) and the rank of t. Then, the truncated sampling method decides whether to discard the example based on the score of the fact and the rank of the answer entity. To unleash the graph reasoning ability of the LLM on KGs, we inject the embedded knowledge of queries and candidate entities into the LLM to further enhance it.

In summary, our main contributions are threefold:

- We propose a new KG completion framework, namely DIFT, which leverages discrimination instructions to finetune generative LLMs. DIFT does not require grounding the output of LLMs to entities in KGs.
- We propose a truncated sampling method to select useful KG samples for instruction construction to improve finetuning efficiency. We also inject KG embeddings into LLMs to improve finetuning effectiveness.
- Experiments show that DIFT advances the state-of-the-art KG completion results, with 0.364 Hits@1 on FB15K-237 and 0.616 on WN18RR.

The remaining sections of this paper are structured as follows. In Section [2,](#page-2-0) we delve into the existing research on knowledge graph completion. Section [3](#page-3-0) provides a detailed exposition of our proposed framework. We then present our experimental results and analyses in Section [4.](#page-7-0) Finally, in Section [5,](#page-15-0) we conclude this paper and outline potential avenues for future research.

### <span id="page-2-0"></span>2 Related Work

Related studies can be divided into embedding- and generation-based models.

### 2.1 Embedding-based KG Completion

Embedding-based KG completion methods compute prediction probability with entity and relation embeddings learned from either structural or textual features. We divide existing embedding-based models into two categories: structure-based models and PLM-based models.

Structure-based Models. These models learn embeddings using structural features such as edges (i.e., triplets), paths or neighborhood subgraphs. Therefore, they can be categorized into three groups. The first group comprises tripletbased embedding models to preserve the local relational structures of KGs. They interpret relations as geometric transformations [\[3](#page-16-4)[,25\]](#page-17-12) or utilize semantic matching methods for scoring triplets [\[1,](#page-16-3)[19\]](#page-16-10). The second group contains path-based models [\[6,](#page-16-11)[34\]](#page-17-13), which predominantly learn probabilistic logical rules from relation paths to facilitate reasoning and infer missing entities. The models in the third group use various deep neural networks to encode the subgraph structures of KGs. CompGCN [\[28\]](#page-17-14) captures the semantics of multi-relational graphs of KGs based on the graph convolutional networks (GCN) framework. Instead, HittER [\[5\]](#page-16-12) uses Transformer to aggregate relational neighbor information. Recently, NBFNet [\[39\]](#page-17-2) employs a flexible and general framework to learn the representation of entity pairs, demonstrating strong performance among structure-based models.

PLM-based Models. PLM-based models employ PLMs (e.g., BERT [\[10\]](#page-16-13)) to encode the text attributes of entities and relations in facts, and compute prediction probabilities using the output embeddings. KG-BERT [\[36\]](#page-17-5) is the first PLM-based KG completion model, which verifies that PLMs are capable of capturing the factual knowledge in KGs. It turns a fact into a natural language

sentence by concatenating entity and relation names, and then predicts whether this sentence is correct or not. Following KG-BERT, some subsequent works make improvements in different aspects. StAR [\[29\]](#page-17-3) divides each fact into two asymmetric parts and encodes them separately with a Siamese-style encoder. SimKGC [\[30\]](#page-17-4) introduces three types of negatives for efficient contrastive learning. CoLE [\[17\]](#page-16-5) promotes structure-based models and PLM-based models mutually through a co-distillation learning framework. These works are all embedding-based models. They obtain query embeddings and entity embeddings with encoder-only PLMs like BERT.

### 2.2 Generation-based KG Completion

Different from embedding-based models that need to learn entity, relation or fact embeddings, generation-based models convert KG completion as a text generation task. These models first translate a KG completion query into a natural language question and then ask a generative language model (e.g., T5 [\[22\]](#page-17-6) and BART [\[16\]](#page-16-7)) to give an answer. Finally, they ground answers to entities in KGs using some matching methods. To compare with traditional KG completion models that rank entities based on their scores, generation-based models generate multiple entities with beam search or sampling and rank them by the generation probabilities. GenKGC [\[33\]](#page-17-8) converts KG completion to sequence-to-sequence generation task to achieve fast inference speed. KGT5 [\[23\]](#page-17-7) designs a unified framework for KG completion and question answering, but discards the pre-trained weights and trains T5 from scratch. KG-S2S [\[4\]](#page-16-8) proposes to employ a generative language model to solve different forms of KG completion tasks including static KG completion, temporal KG completion, and few-shot KG completion [\[15\]](#page-16-14). Although these works provide some insight into how to conduct KG completion with LLMs, simply replacing PLMs with current LLMs is infeasible as finetuning LLMs on KGs is time-consuming and takes many computational resources.

With the emergence of LLMs, several works attempt to adapt LLMs for KG completion. KG-LLM [\[37\]](#page-17-11) performs instruction tuning on KG completion tasks with relatively smaller LLMs (e.g., LLaMA-7B, ChatGLM-6B) and surpasses ChatGPT and GPT-4, but it still lags behind state-of-the-art KG completion models. KICGPT [\[31\]](#page-17-10) employs an embedding-based model as the retriever to generate an ordered candidate entity list and designs an in-context learning strategy to prompt ChatGPT to re-rank the entities with a multi-round interaction. KICGPT is the most similar work to our proposed method DIFT, because we also employ an embedding-based model to obtain candidate entities and provide them to LLMs. However, accessing closed-source LLMs like ChatGPT is costly as the inference cost grows linearly with the number of missing facts. In contrast, we propose an effective and efficient method to finetune open-source LLMs.

## <span id="page-3-0"></span>3 The DIFT Framework

In this section, we describe the proposed DIFT framework for KG completion.

![](_page_4_Figure_1.jpeg)

<span id="page-4-0"></span>Fig. 1. Illustration of the proposed DIFT framework.

### 3.1 Notations

We start by introducing the definitions and notations used in this paper.

Knowledge graph. A KG is denoted as G = (E, R, T ). E is the set of entities, and R is the set of relations. T = {(h, r, t)|h, t ∈ E, r ∈ R} is the set of facts. We denote a fact as (h, r, t), in which h is the head entity, t is the tail entity, and r is the relation between h and t. Furthermore, the available text attributes of G encompass entity names, relation names, and entity descriptions.

Knowledge graph completion. KG completion (a.k.a. link prediction) aims to predict the missing entity given an incomplete fact. To be more specific, given an incomplete fact (h, r, ?) or (?, r, t), the purpose of KG completion is to find the missing entity t or h from the entity set E.

### 3.2 Framework Overview

Fig. [1](#page-4-0) shows the overall framework of the proposed DIFT. In general, DIFT finetunes an LLM M on a given KG G with the help of an embedding-based model M<sup>E</sup> which has been trained on G in advance. To elaborate, take a tail prediction query q = (h, r, ?) as an example, we feed q into M<sup>E</sup> to get the top-m predicted entities C = [e1, e2, . . . , em] where m is a predefined hyperparameter. Subsequently, we construct a discrimination instruction P(q) based on the query q and the candidate entities C. Finally, P(q) is fed into M to select the most plausible entity. In this way, we ensure that M always predicts an entity in E as the answer, avoiding grounding the unconstrained output texts from M to entities. For efficient finetuning, we employ M<sup>E</sup> to score the instruction samples and only keep samples with high confidence. Additionally, to enhance the graph reasoning ability of M, we design a knowledge adaption module to inject the embeddings of q and candidate entities in C obtained from M<sup>E</sup> into M.

### 3.3 Instruction Construction

For a query q = (h, r, ?), we construct the prompt P by integrating four pieces of information: Query Q, Description D, Neighbor facts N and Candidate entities C, which can be represented as:

$$\mathcal{P}(q) = [\mathcal{Q}; \mathcal{D}; \mathcal{N}; \mathcal{C}], \tag{1}$$

where ";" is the concatenation operation between texts. We give an example of querying (Titanic, film language, ?), as illustrated in Fig. [1.](#page-4-0)

Query refers to a natural language sentence containing the incomplete fact (h, r, ?). Instead of designing a complex natural language question to prompt off-the-shelf LLMs, we simply concatenate the entity and relation names in the form of a triplet and indicate which entity is missing. During the finetuning process, the LLM M will be trained to fit our prompt format.

Description is the descriptive text of h, which contains abundant information about the entity. This additional information helps the LLM M get a better understand of the entity h. For instance, we depict Titanic in Fig. [1](#page-4-0) as a 1997 American epic romantic disaster film directed by James Cameron.

Neighbor facts are obtained by sampling facts related to the entity h. As there may be numerous facts associated with h, we devise a straightforward yet effective sampling mechanism, namely relation co-occurrence (RC ) sampling. It is rooted in relation co-occurrence, and streamlines the number of facts while ensuring the inclusion of relevant information. The intuition behind RC sampling lies in the observation that the relations frequently co-occurring with r are considered to be crucial to complete (h, r, ?). For example, the relations film language and film country in Fig. [1](#page-4-0) often co-occur, because the language of a film is closely related to the country where it is released. Therefore, we can infer that the language of Titanic is highly likely to be English from the fact that it is an American film. Drawing on the above observation, we sort the neighboring relations of h based on their frequency of co-occurrences with r and subsequently select facts containing these relations until a preset threshold γ is reached.

Candidate entities are the names of top-m entities ranked by the KG embedding model ME. We retain the order of candidate entities since the order reflects the confidence of each entity from ME. We instruct the LLM M to select an entity from the given candidates, thereby avoiding the grounding errors.

### <span id="page-5-0"></span>3.4 Truncated Sampling

We design a sampling method to select representative samples to reduce instruction data. The main idea is to opt for high-confidence samples indicated by ME, thereby empowering M to acquire intrinsic semantic knowledge of M<sup>E</sup> efficiently. By finetuning  $\mathcal{M}$  on these selected instruction samples, we effectively mitigate the computational burden associated with training.

We take the sample fact  $(h, r, t)$  with query  $(h, r, ?)$  and answer entity t as an example. We denote the sample fact as  $s$ . Specifically, we assess the confidence of s from both global and local perspectives. The global confidence  $Conf_{\text{global}}(s)$ is computed as  $\frac{1}{R(h,r,t)}$ , where  $R(h,r,t)$  is the ranking of t for the query  $(h,r,?)$ . We name it as the global confidence because it measures the ranking of  $t$  among all candidates in the  $KG$ .

Considering that the global confidence ignores the differences between two queries whose answer entities are in the same rank, inspired by  $|32|$ , we present the local confidence to measure the score of a fact itself. The local confidence  $Conf_{\text{local}}(s)$  is computed as  $f(h, r, t)$ , i.e., the score of s obtained from  $\mathcal{M}_E$ . It is worth noting that  $Conf_{local}(s)$  is assigned as 0 if t is not ranked within the  $\text{top-}m$ . Finally, the confidence of s is determined by the weighted sum of global and local confidence, expressed as follows:

$$Conf(s) = Conf_{\text{global}}(s) + \alpha \times Conf_{\text{local}}(s), \tag{2}$$

where  $\alpha$  serves as a hyperparameter to balance the global and local confidence. Subsequently, we introduce a threshold  $\beta$  and keep the samples with confidence greater than  $\beta$  as the final instruction data.

#### Instruction Tuning with Knowledge Adaption $3.5$

Given the prompt  $\mathcal{P}(q)$ , we finetune the LLM  $\mathcal{M}$  to generate the entity name of  $t$ . The loss of instruction tuning is a re-construction loss:

$$\mathcal{L}_{\mathcal{M}} = -\sum_{i=1}^{N} \log p(y_i \,|\, y_{\langle i}, \mathcal{P}(q)), \tag{3}$$

where N denotes the number of tokens in the entity name of  $t, y_i$   $(i = 1, 2, \ldots, N)$ represents the *i*-th token, and  $p(y_i | y_{\leq i}, \mathcal{P}(q))$  signifies the probability of generating  $y_i$  with  $\mathcal{M}$  given the prompt  $\mathcal{P}(q)$  and tokens that have been generated.

The facts provided in  $\mathcal{P}(q)$  are presented in the text format, losing the global structure information of KGs. Therefore, we propose to inject the embeddings learned from KG structure into  $\mathcal{M}$  to further improve its graph reasoning ability. We align the embeddings from  $\mathcal{M}_E$  with the semantic space of  $\mathcal{M}$ , to get the knowledge representations:

$$\hat{\mathbf{e}} = \mathbf{W}_2 \big( \text{SwiGLU}(\mathbf{W}_1 \cdot \mathbf{e} + \mathbf{b}_1) \big) + \mathbf{b}_2, \tag{4}$$

where  $\hat{\mathbf{e}}$  denotes the knowledge representation obtained based on the embeddings **e.**  $\mathbf{W}_1 \in \mathbb{R}^{d_1 \times d_0}$ ,  $\mathbf{b}_1 \in \mathbb{R}^{d_1}$ ,  $\mathbf{W}_2 \in \mathbb{R}^{d_2 \times d_1}$ , and  $\mathbf{b}_2 \in \mathbb{R}^{d_2}$  are trainable weights.  $d_0$  is the embedding dimension of  $\mathcal{M}_E$ ,  $d_2$  is the hidden size of  $\mathcal{M}$ , and  $d_1$  is a hyperparameter. SwiGLU is a common activation function used in LLaMA  $[27]$ .

Considering that  $\mathcal{M}_E$  scores a fact based on the embeddings of the query q and the candidate entity  $t$ , we inject the knowledge representations of  $q$  and all

<span id="page-7-1"></span>

|  | Table 1. The statistics of datasets. |  |
|--|--------------------------------------|--|
|  |                                      |  |

| Datasets  |        |     |         | #Entities #Relations #Training #Validation #Testing |        |
|-----------|--------|-----|---------|-----------------------------------------------------|--------|
| FB15K-237 | 14,541 | 237 | 272,115 | 17,535                                              | 20,466 |
| WN18RR    | 40,943 | 11  | 86,835  | 3,034                                               | 3,134  |

candidate entities in C into M. We add two special placeholders "[QUERY]" and "[ENTITY]" to indicate that there will be a knowledge representation from ME, as shown in Fig. [1.](#page-4-0) Specifically, we place a "[QUERY]" after the missing entity in Q and an "[ENTITY]" after each entity name in C.

### <span id="page-7-0"></span>4 Experiments

### 4.1 Experiment Setup

Datasets. In the experiments, we use two benchmark datasets, FB15K-237 [\[26\]](#page-17-16) and WN18RR [\[8\]](#page-16-15), to evaluate our proposed framework. FB15K-237 consists of real-world named entities and their relations, constructed based on Freebase [\[2\]](#page-16-16). On the other hand, WN18RR contains English phrases and the semantic relations between them, constructed based on WordNet [\[18\]](#page-16-17). Notably, these two datasets are updated from their previous versions (i.e., FB15K and WN18 [\[3\]](#page-16-4)) respectively, they both removed some inverse edges to prevent data leakage. For a detailed overview, the statistics of these two datasets are shown in Table [1.](#page-7-1)

Evaluation protocol. For each test fact, we conduct both head entity prediction and tail entity prediction by masking the corresponding entities, respectively. The conventional metrics are ranking evaluation metrics, i.e., Hits@k (k = 1, 3, 10) and mean reciprocal rank (MRR). Hits@k is the percentage of queries whose correct entities are ranked within the top-k, and MRR measures the average reciprocal ranks of correct entities. In our framework, the finetuned LLM selects an entity as the answer from the ranking list of candidates. To assess its performance and make the results comparable to existing work, we move the selected entity to the top of the ranking list, and other candidates remain unchanged. We then use Hits@k and MRR to assess the reranked candidate list. We report the averaged results of head and tail entity prediction under the filtered ranking setting [\[3\]](#page-16-4).

Implementation details. We run our experiments on two Intel Xeon Gold CPUs, an NVIDIA RTX A6000 GPU, and Ubuntu 18.04 LTS. Text attributes are taken from KG-BERT [\[36\]](#page-17-5). We select three representative embedding-based models to experiment with DIFT, namely, TransE, SimKGC, and CoLE. Each embedding-based model is pre-trained on the training set. We obtain the top 20 predicted entities for each query in the validation set and test set. We also obtain the embeddings of all queries and entities for knowledge adaption.

As for the instruction tuning, we select LLaMA-2-7B[3](#page-7-2) as the LLM. We employ LoRA [\[14\]](#page-16-9) for parameter-efficient finetuning. The hyperparameters of LoRA are

<span id="page-7-2"></span><sup>3</sup> <https://huggingface.co/meta-llama/Llama-2-7b-chat-hf>

set to r = 64, alpha = 16, and dropout = 0.1. We introduce LoRA for all query and value projection matrices in the self-attention module of Transformer. To further speed up the finetuning process, we quantize the LLM by QLoRA [\[9\]](#page-16-18), which quantizes the LLM parameters to 4 bits by introducing Double Quantization with 4-bit NormalFloat data type. Inspired by KICGPT [\[31\]](#page-17-10), we partition the validation set into two parts according to 9:1. The first part is used to finetune the LLM to follow the instructions, and the second part is used for hyperparameter selection. Note that we do not use the training data of each benchmark to construct instructions. Since the embedding-based model has learned the training data, it would rank the correct entity at the first in the candidate list for most training facts. If we use these candidate lists to construct instructions, the LLM would learn a tricky solution to pick the first candidate as an answer, which is not the goal of our finetuning.

### 4.2 Baselines

Embedding-based models. We choose eight structure-based models as baselines. Three triplet-based models are selected, including TransE [\[3\]](#page-16-4), RotatE [\[25\]](#page-17-12), and TuckER [\[1\]](#page-16-3). We also choose two path-based models. Neural-LP [\[34\]](#page-17-13) is the first model that learns logic rules from relation paths and NCLR [\[6\]](#page-16-11) is the state-ofthe-art path-based model. The remaining models are all graph-based. CompGCN [\[28\]](#page-17-14) employs GCNs to encode the multi-relational graph structure of the KG, while HittER [\[5\]](#page-16-12) leverages the Transformer architecture. NBFNet [\[39\]](#page-17-2) currently performs best among the structure-based models. We also select five PLM-based models as the competitors, namely KG-BERT [\[36\]](#page-17-5), StAR [\[29\]](#page-17-3), MEM-KGC [\[7\]](#page-16-19), SimKGC [\[30\]](#page-17-4), and CoLE [\[17\]](#page-16-5). Note that, SimKGC stands the state-of-the-art link prediction model on WN18RR, which benefits from efficient contrastive learning. CoLE promotes PLMs and structure-based models mutually to achieve the best performance on FB15K-237 among PLM-based models. To ensure a fair comparison, we present results derived solely from N-BERT, the PLM-based KG embedding module within CoLE, rather than the entire CoLE framework.

Generation-based models. We select three generation-based KG completion models, all of which are either based on BART or T5, namely, GenKGC [\[33\]](#page-17-8), KGT5 [\[23\]](#page-17-7), and KG-S2S [\[4\]](#page-16-8). Further, we select two recent models based on LLMs as baselines. ChatGPTone-shot is a baseline proposed by AutoKG [\[38\]](#page-17-17), and KICGPT evaluates it on the whole test sets of FB15K-237 and WN18RR for comparison. KICGPT is the most competitive KG completion model, which employs RotatE to provide the top-m predicted entities for each query and reranks these candidates with ChatGPT through multi-round interactions. We also report the performance of DIFT without finetuning, denoted by LLaMA+TransE, LLaMA+SimKGC, and LLaMA+CoLE, respectively.

### <span id="page-8-0"></span>4.3 Main Results

We report the link prediction results on FB15K-237 and WN18RR in Table [2.](#page-9-0) Generally speaking, our proposed framework DIFT achieves the best performance

<span id="page-9-0"></span>Table 2. Link prediction Results. We mark the best scores in terms of each metric in bold and the second-best scores are underlined. We reproduce the results of TransE, SimKGC and CoLE using their source code and hyperparameters. The results of Neural-LP are obtained from [\[21\]](#page-17-18). The results of GenKGC, KGT5 and KG-S2S are obtained from [\[4\]](#page-16-8). The results of other baselines are taken from their respective original papers.

| Models    |       |       | FB15K-237 |                       |       | WN18RR |       |                       |  |
|-----------|-------|-------|-----------|-----------------------|-------|--------|-------|-----------------------|--|
|           | MRR   |       |           | Hits@1 Hits@3 Hits@10 | MRR   |        |       | Hits@1 Hits@3 Hits@10 |  |
|           |       |       |           | Embedding-based       |       |        |       |                       |  |
| TransE    | 0.312 | 0.212 | 0.354     | 0.510                 | 0.225 | 0.016  | 0.403 | 0.521                 |  |
| RotatE    | 0.338 | 0.241 | 0.375     | 0.533                 | 0.476 | 0.428  | 0.492 | 0.571                 |  |
| TuckER    | 0.358 | 0.266 | 0.394     | 0.544                 | 0.470 | 0.443  | 0.482 | 0.526                 |  |
| Neural-LP | 0.237 | 0.173 | 0.259     | 0.361                 | 0.381 | 0.368  | 0.386 | 0.408                 |  |
| NCRL      | 0.300 | 0.209 | -         | 0.473                 | 0.670 | 0.563  | -     | 0.850                 |  |
| CompGCN   | 0.355 | 0.264 | 0.390     | 0.535                 | 0.479 | 0.443  | 0.494 | 0.546                 |  |
| HittER    | 0.373 | 0.279 | 0.409     | 0.558                 | 0.503 | 0.462  | 0.516 | 0.584                 |  |
| NBFNet    | 0.415 | 0.321 | 0.454     | 0.599                 | 0.551 | 0.497  | 0.573 | 0.666                 |  |
| KG-BERT   | -     | -     | -         | 0.420                 | 0.216 | 0.041  | 0.302 | 0.524                 |  |
| StAR      | 0.365 | 0.266 | 0.404     | 0.562                 | 0.551 | 0.459  | 0.594 | 0.732                 |  |
| MEM-KGC   | 0.346 | 0.253 | 0.381     | 0.531                 | 0.557 | 0.475  | 0.604 | 0.704                 |  |
| SimKGC    | 0.338 | 0.252 | 0.364     | 0.511                 | 0.671 | 0.595  | 0.719 | 0.802                 |  |
| CoLE      | 0.389 | 0.294 | 0.429     | 0.572                 | 0.593 | 0.538  | 0.616 | 0.701                 |  |
|           |       |       |           | Generation-based      |       |        |       |                       |  |
|           |       |       |           |                       |       |        |       |                       |  |

| Generation-based |       |       |       |       |       |       |       |       |  |
|------------------|-------|-------|-------|-------|-------|-------|-------|-------|--|
| GenKGC           | -     | 0.192 | 0.355 | 0.439 | -     | 0.287 | 0.403 | 0.535 |  |
| KGT5             | 0.276 | 0.210 | -     | 0.414 | 0.508 | 0.487 | -     | 0.544 |  |
| KG-S2S           | 0.336 | 0.257 | 0.373 | 0.498 | 0.574 | 0.531 | 0.595 | 0.661 |  |
| ChatGPTone-shot  | -     | 0.267 | -     | -     | -     | 0.212 | -     | -     |  |
| KICGPT           | 0.412 | 0.327 | 0.448 | 0.581 | 0.564 | 0.478 | 0.612 | 0.677 |  |
| LLaMA + TransE   | 0.232 | 0.080 | 0.321 | 0.502 | 0.202 | 0.037 | 0.360 | 0.516 |  |
| LLaMA + SimKGC   | 0.236 | 0.074 | 0.335 | 0.503 | 0.391 | 0.065 | 0.695 | 0.798 |  |
| LLaMA + CoLE     | 0.238 | 0.033 | 0.387 | 0.561 | 0.374 | 0.117 | 0.602 | 0.697 |  |
| DIFT + TransE    | 0.389 | 0.322 | 0.408 | 0.525 | 0.491 | 0.462 | 0.496 | 0.560 |  |
| DIFT + SimKGC    | 0.402 | 0.338 | 0.418 | 0.528 | 0.686 | 0.616 | 0.730 | 0.806 |  |
| DIFT + CoLE      | 0.439 | 0.364 | 0.468 | 0.586 | 0.617 | 0.569 | 0.638 | 0.708 |  |

<span id="page-9-1"></span>Table 3. Results of ablation study

| Models                 |       |       | FB15K-237 |                       | WN18RR |       |       |                       |
|------------------------|-------|-------|-----------|-----------------------|--------|-------|-------|-----------------------|
|                        | MRR   |       |           | Hits@1 Hits@3 Hits@10 | MRR    |       |       | Hits@1 Hits@3 Hits@10 |
| DIFT                   | 0.439 | 0.364 | 0.468     | 0.586                 | 0.617  | 0.569 | 0.638 | 0.708                 |
| w/o truncated sampling | 0.423 | 0.338 | 0.459     | 0.587                 | 0.600  | 0.537 | 0.638 | 0.712                 |
| w/o RC sampling        | 0.434 | 0.354 | 0.468     | 0.588                 | 0.614  | 0.564 | 0.636 | 0.708                 |
| w/o description        | 0.436 | 0.358 | 0.467     | 0.586                 | 0.603  | 0.548 | 0.630 | 0.705                 |
| w/o neighbors          | 0.438 | 0.360 | 0.469     | 0.588                 | 0.610  | 0.558 | 0.637 | 0.708                 |
| w/o knowledge adaption | 0.437 | 0.358 | 0.468     | 0.587                 | 0.612  | 0.560 | 0.637 | 0.708                 |

in most metrics on two datasets. Compared with the selected embedding-based models TransE, SimKGC, and CoLE, DIFT improves the performance of these models on both datasets, significantly in terms of Hits@1. Without finetuning, the performance of DIFT drops dramatically, which demonstrates that it is necessary to finetune the LLM for KG completion task.

Compared with the LLM-based model ChatGPTone-shot, DIFT consistently outperforms it in terms of Hits@1, regardless of the integration with any of the embedding-based models. This indicates that prompting ChatGPT with in-context learning is less effective than finetuning a smaller LLM with the help of existing embedding-based models for link prediction. Compared with the most competitive baseline model KICGPT which also provides the LLM with candidate entities, the relative improvement brought by DIFT is less. However, KICGPT needs multi-round interactions with ChatGPT, which has 175B parameters. In contrast, DIFT finetunes a small LLaMA with only 7B parameters.

Comparing different metrics, we find that the performance improvement is more significant on Hits@1 while less significant on Hits@10. In DIFT, we ask the LLM to select the plausible entity from the given candidate list. Given that the correct entity is more likely to be ranked in the top 10 entities rather than outside the top 10, the LLM is more likely to select an entity in the top 10 as the answer. Thus, the improvement is more obvious on Hits@1 rather than Hits@10.

We also find that the performance improvement on FB15K-237 is more significant than that on WN18RR. This discrepancy can be attributed to the stark disparity in density between the two datasets: FB15K-237 is considerably denser than WN18RR, implying a richer reservoir of knowledge. More knowledge leads to better improvement since the knowledge is provided for the LLM to comprehend in the form of prompts and embeddings.

### 4.4 Ablation Study

For the ablation study, we select CoLE as the embedding-based model to provide candidate entities since DIFT with CoLE performs best overall on both datasets. We evaluate the effectiveness of two kinds of sampling mechanisms, i.e., truncated sampling and RC sampling, as well as three kinds of support information, i.e., description, neighbors, and embeddings used in knowledge adaption.

From the results presented in Table [3,](#page-9-1) it is evident that all components contribute a lot to DIFT. Among all these components, truncated sampling has the most substantial impact on performance. The Hits@1 score experiences a degradation of at least 5.6% in the absence of truncated sampling. This shows that this mechanism can effectively select useful instruction data for the LLM to learn intrinsic semantic knowledge of the embedding-based model.

We can also observe that the impact of description, neighbors, and RC sampling differs significantly between the two datasets. Without description, the Hits@1 will drop more on WN18RR. This is attributed to WN18RR being a sparse KG with less structural information compared with FB15K-237. Therefore, it needs additional description to enrich entity information, aiding in the differentiation between similar entities. In addition, neighbor information is also

![](_page_11_Figure_0.jpeg)

<span id="page-11-0"></span>Fig. 2. Hits@1 results and training time of DIFT on FB15K-237 and WN18RR along with the numbers of candidate entities.

more important for WN18RR. This is because many correct entities will directly appear in the neighbor facts of WN18RR, facilitating the LLM in making accurate predictions. Instead, the improvement of Hits@1 is more significant on FB15K-237 than WN18RR for RC sampling. We posit that this is attributed to FB15K-237 being highly dense, with each entity having numerous neighbor facts. Many of these facts are irrelevant to the query, leading to interference. Hence, RC sampling can minimize irrelevant facts and enhance effectiveness.

As for knowledge adaption, we observe consistent performance improvements across the two datasets, indicating good generality and robustness.

### 4.5 Further Analyses

Effect of the number of candidates. In Section [4.3,](#page-8-0) we set the number of candidate entities m provided by the embedding-based model to 20. Here we investigate the effect of m on the performance and the training time of DIFT. The results are shown in Fig. [2.](#page-11-0) First, for the training time, we find that it grows linearly when we increase m. It is intuitive since increasing m leads to longer prompts. Second, as for the performance of DIFT, we find that the performance is best when m is set to 30 on FB15K-237, and there is a slight drop when m is set to 40. The same observation can be found on WN18RR if we continue to increase m after 20. This indicates that blindly increasing the number of candidate entities cannot improve performance. Third, we find that the performance is best when m is set to 30 on FB15K-237 and 20 on WN18RR. That is to say, to achieve the best performance, DIFT needs more candidate entities on FB15K-237 than WN18RR. We think that this discrepancy arises from the generally inferior performance of models on FB15K-237 compared to WN18RR. Consequently, to ensure the presence of answer entities within the prompts, a larger m is advisable on FB15K-237 than on WN18RR.

Effect of truncated sampling thresholds. In Section [3.4,](#page-5-0) we use a threshold β to control the quantity of instruction data. To investigate the impact of β on the performance and the training time of DIFT, we conduct an experiment by setting

![](_page_12_Figure_1.jpeg)

<span id="page-12-0"></span>Fig. 3. Hits@1 results and training time of DIFT on FB15K-237 and WN18RR along with the threshold for truncated sampling.

![](_page_12_Figure_3.jpeg)

<span id="page-12-1"></span>Fig. 4. Correct predictions of DIFT and CoLE on FB15K-237 and WN18RR. The light blue area represents the accurate triplets predicted by DIFT, excluding those that can also be predicted by CoLE. The dark green area illustrates the overlapping triplets predicted accurately by DIFT and CoLE. The light green area represents the accurate triplets predicted by CoLE, excluding those that can also be predicted by DIFT.

different values for β. In particular, we change β from 0.05 in the main experiments to 0, 0.5, and 1.0 respectively. The results are shown in Fig. [3.](#page-12-0) We have the following observations. First, with β increasing, the quantity of instruction data decreases, and therefore the training time also decreases accordingly. Second, the performance drops when we set β to 0 on both datasets, which indicates that increasing the quantity of instruction data does not necessarily improve the performance, and its quality also affects the performance. Third, if we strictly ensure that the quality of the instruction data is high enough, i.e., we set β to 0.5 or 1.0, the performance of DIFT also drops. We think there are mainly two reasons: (1) When β is set to 0.5 or 1.0, the limited instruction data is not enough to finetune the LLM sufficiently. (2) Instruction data with high confidence usually places the answer entity among the first few in the candidate list. Therefore, finetuning the LLM with this data will cause the LLM to always choose the top-ranked entities, regardless of whether they are correct.

Comparison of DIFT and basic embedding models. We further investigate the predictions of DIFT in comparison with those of the selected embedding-based

| Models                                        |                         |                         | FB15K-237               |                                                     | WN18RR                  |                         |                         |                         |  |  |
|-----------------------------------------------|-------------------------|-------------------------|-------------------------|-----------------------------------------------------|-------------------------|-------------------------|-------------------------|-------------------------|--|--|
|                                               |                         |                         |                         | MRR Hits@1 Hits@3 Hits@10 MRR Hits@1 Hits@3 Hits@10 |                         |                         |                         |                         |  |  |
| LLaMA-2-7B-Chat                               |                         |                         |                         |                                                     |                         |                         |                         |                         |  |  |
| DIFT + TransE                                 | 0.389                   | 0.322                   | 0.408                   | 0.525                                               | 0.491                   | 0.462                   | 0.496                   | 0.560                   |  |  |
| DIFT + SimKGC<br>DIFT + CoLE                  | 0.402<br>0.439          | 0.338<br>0.364          | 0.418<br>0.468          | 0.528<br>0.586                                      | 0.686<br>0.617          | 0.616<br>0.569          | 0.730<br>0.638          | 0.806<br>0.708          |  |  |
| LLaMA-2-7B-Foundation                         |                         |                         |                         |                                                     |                         |                         |                         |                         |  |  |
| DIFT + TransE<br>DIFT + SimKGC<br>DIFT + CoLE | 0.393<br>0.405<br>0.439 | 0.328<br>0.341<br>0.363 | 0.409<br>0.420<br>0.468 | 0.525<br>0.530<br>0.587                             | 0.481<br>0.682<br>0.619 | 0.450<br>0.608<br>0.571 | 0.486<br>0.731<br>0.641 | 0.552<br>0.806<br>0.710 |  |  |

<span id="page-13-0"></span>Table 4. Link prediction Results of different versions of LLaMA-2-7B.

model. For this analysis, we continue to employ CoLE as the embedding-based model to analyze the results. We draw Venn diagrams to highlight both their shared and individual correct predictions, as illustrated in Fig. [4.](#page-12-1) It is obvious that in addition to the shared correct predictions, DIFT can also get some correct predictions by itself. Conversely, we observe instances where CoLE makes correct inferences that DIFT fails to replicate. Based on the divergence between the correct predictions of DIFT and CoLE, we can conclude that the LLM does not repeat the predicted entities by CoLE blindly, instead, it can reason the missing facts based on its knowledge obtained in the pre-training stage.

Comparison of different versions of the LLM. In the main experiment, we employ LLaMA-2-7B-Chat as the LLM for DIFT. In order to investigate the influence of different versions of the LLM on the performance of DIFT, we experiment with the foundation version, denoted as LLaMA-2-7B-Foundation. The results are shown in Table [4.](#page-13-0) DIFT with LLaMA-2-7B-Foundation performs slightly better than that with LLaMA-2-7B-Chat on FB15K-237, but the observation is the opposite on WN18RR. Generally speaking, DIFT achieves a similar performance no matter which version of the LLM are employed. It demonstrates the robustness and generalization of DIFT for different LLM versions.

### 4.6 The Finetuning Learns What?

In this section, we investigate what the LLM learns during our finetuning process. DIFT employs a lightweight embedding-based model to provide candidate entities for both finetuning and inference. A natural question arises: Does the LLM learn the preference of the embedding-based model predictions or the knowledge in the KG? To answer this question, we design the following experiment to evaluate the effect of the candidate order in both the finetuning and inference stages.

Effect of the order of candidates. DIFT takes the top-m predicted entities from the embedding-based model as the candidates for the LLM. We retain the order of candidates because we assume that the order reflects the knowledge

| Ordered<br>finetuning | Ordered<br>inference | FB15K-237 |        |        |         | WN18RR |        |        |         |
|-----------------------|----------------------|-----------|--------|--------|---------|--------|--------|--------|---------|
|                       |                      | MRR       | Hits@1 | Hits@3 | Hits@10 | MRR    | Hits@1 | Hits@3 | Hits@10 |
| !                     | !                    | 0.439     | 0.364  | 0.468  | 0.586   | 0.686  | 0.616  | 0.730  | 0.806   |
| !                     | %                    | 0.328     | 0.168  | 0.441  | 0.584   | 0.484  | 0.233  | 0.712  | 0.806   |
| %                     | !                    | 0.423     | 0.333  | 0.466  | 0.589   | 0.627  | 0.500  | 0.731  | 0.809   |
| %                     | %                    | 0.417     | 0.324  | 0.464  | 0.591   | 0.625  | 0.493  | 0.736  | 0.808   |

<span id="page-14-0"></span>Table 5. Influence of the order of candidates

learned by the embedding-based model. Here, to investigate the influence of the order of candidates, we shuffle the candidates in the finetuning or inference stages to ask the LLM to select an entity from the shuffled candidate list. Remember that the shuffled candidate list is only used for entity selection, we move the selected entity to the top of the ranking list from the embedding-based model for evaluation. Results are shown in Table [5,](#page-14-0) and we have the following observations.

On FB15K-237, we employ CoLE as the embedding-based model. We can find that the performance drops dramatically if we finetune the LLM with ordered candidates but shuffle the candidates during inference. We think the reason is that ordered candidates instruct the LLM to select within the top few entities as they are more plausible. Therefore, the LLM still focus on the top few candidates during inference, even though the candidates are shuffled. When we finetune the LLM with shuffled candidates, we find that the performance changes slightly whether the candidates are shuffled or not during inference. The reason is that the LLM has no idea about the preference that the top few candidates are more plausible, so it can not benefit from the order of candidates.

On WN18RR, we use SimKGC as the embedding-based model and similar observations can be found. However, we find that the performance of DIFT is even worse than SimKGC when we finetune the LLM with shuffled candidates. This demonstrates that the LLM can not outperform SimKGC solely based on its inherent knowledge without prediction preferences.

Based on the above analyses, it appears that our DIFT not only captures prediction preferences but also primarily acquires knowledge from the KG.

Case study. To explore how DIFT improves performance compared with the selected embedding-based models, we conduct a case study on DIFT (integrating CoLE), TransE, SimKGC, and CoLE. Table [6](#page-15-1) presents the Hits@1 results of the four models on three queries from FB15K-237, in which the entities marked with horizontal lines at the bottom are the answers. In the first two cases, DIFT consistently performs accurately while the other models all predict wrong entities.

– In Case 1, the contextual description of the head entity, "It tells the story of an aspiring actress named Betty Elms, newly arrived in Los Angeles ...", offers ample support to determine the answer "Los Angeles", and our DIFT generates the correct entity name, indicating that DIFT has improved contextual inference capability compared with the embedding-based models.

|             | Case 1                  | Case 2        | Case 3                    |
|-------------|-------------------------|---------------|---------------------------|
| Head entity | Mulholland Drive        | Shonda Rhimes | ?                         |
| Relation    | featured film locations | gender        | film language             |
| Tail entity | ?                       | ?             | English language          |
| DIFT        | Los Angeles             | Female        | The Last King of Scotland |
| TransE      | Paris                   | Male          | Pan's Labyrinth           |
| SimKGC      | Berkeley                | Male          | The Illusionist           |
| CoLE        | New York City           | Male          | The Illusionist           |

<span id="page-15-1"></span>Table 6. Case study on three queries from FB15K-237. Correct answers are underlined.

- In Case 2, neither the description nor the neighbor information provides clues to Shonda Rhimes' gender. It is difficult for embedding-based models to infer the correct entity based on such incomplete knowledge. Instead, DIFT has open knowledge and powerful commonsense reasoning ability, allowing it to overcome this limitation and predict the correct answers. This case shows the complementarity of embedding-based models and LLMs in our framework.
- In Case 3, despite DIFT inferring an "incorrect" entity "The Last King of Scotland", it is crucial to highlight that the underlying issue is associated with the dataset, not DIFT itself. This is because the language of "The Last King of Scotland" is also English, but FB15K-237 lacks this specific knowledge. This case demonstrates that DIFT is capable of leveraging open knowledge in LLMs, surpassing the constraints of closed knowledge in KGs.

### <span id="page-15-0"></span>5 Conclusion and Future Work

In this paper, we propose a novel KG completion framework DIFT. It finetunes generative LLMs with discrimination instructions using LoRA, which does not involve grounding the output of LLMs to entities in KGs. To further reduce the computation cost and make DIFT more efficient, we propose a truncated sampling method to select facts with high confidence for finetuning. KG embeddings are also added into the LLMs to improve the finetuning effectiveness. Experiments show that DIFT achieves state-of-the-art results on KG completion. In future work, we plan to support other KG tasks such as KGQA and entity alignment.

Acknowledgments This work was funded by National Natural Science Foundation of China (No. 62272219), Postdoctoral Fellowship Program of CPSF (No. GZC20240685), and CCF-Tencent Rhino-Bird Open Research Fund.

Supplemental Material Statement: Source code and datasets are available on GitHub: <https://github.com/nju-websoft/DIFT>.

### References

- <span id="page-16-3"></span>1. Balazevic, I., Allen, C., Hospedales, T.M.: TuckER: Tensor factorization for knowledge graph completion. In: EMNLP-IJCNLP. pp. 5185–5194 (2019)
- <span id="page-16-16"></span>2. Bollacker, K.D., Evans, C., Paritosh, P.K., Sturge, T., Taylor, J.: Freebase: A collaboratively created graph database for structuring human knowledge. In: SIGMOD. pp. 1247–1250 (2008)
- <span id="page-16-4"></span>3. Bordes, A., Usunier, N., García-Durán, A., Weston, J., Yakhnenko, O.: Translating embeddings for modeling multi-relational data. In: NIPS. pp. 2787–2795 (2013)
- <span id="page-16-8"></span>4. Chen, C., Wang, Y., Li, B., Lam, K.: Knowledge is flat: A seq2seq generative framework for various knowledge graph completion. In: COLING. pp. 4005–4017 (2022)
- <span id="page-16-12"></span>5. Chen, S., Liu, X., Gao, J., Jiao, J., Zhang, R., Ji, Y.: HittER: Hierarchical transformers for knowledge graph embeddings. In: EMNLP. pp. 10395–10407 (2021)
- <span id="page-16-11"></span>6. Cheng, K., Ahmed, N.K., Sun, Y.: Neural compositional rule learning for knowledge graph reasoning. In: ICLR (2023)
- <span id="page-16-19"></span>7. Choi, B., Jang, D., Ko, Y.: MEM-KGC: Masked entity model for knowledge graph completion with pre-trained language model. IEEE Access 9, 132025–132032 (2021)
- <span id="page-16-15"></span>8. Dettmers, T., Minervini, P., Stenetorp, P., Riedel, S.: Convolutional 2D knowledge graph embeddings. In: AAAI. pp. 1811–1818 (2018)
- <span id="page-16-18"></span>9. Dettmers, T., Pagnoni, A., Holtzman, A., Zettlemoyer, L.: QLoRA: Efficient finetuning of quantized LLMs. arXiv 2305.14314 (2023)
- <span id="page-16-13"></span>10. Devlin, J., Chang, M., Lee, K., Toutanova, K.: BERT: Pre-training of deep bidirectional transformers for language understanding. In: NAACL. pp. 4171–4186 (2019)
- <span id="page-16-1"></span>11. Du, H., Le, Z., Wang, H., Chen, Y., Yu, J.: COKG-QA: Multi-hop question answering over COVID-19 knowledge graphs. Data Intell. 4, 471–492 (2022)
- <span id="page-16-0"></span>12. Galárraga, L., Razniewski, S., Amarilli, A., Suchanek, F.M.: Predicting completeness in knowledge bases. In: WSDM. pp. 375–383 (2017)
- <span id="page-16-2"></span>13. Guo, Q., Zhuang, F., Qin, C., Zhu, H., Xie, X., Xiong, H., He, Q.: A survey on knowledge graph-based recommender systems. IEEE Trans. Knowl. Data Eng. 34, 3549–3568 (2022)
- <span id="page-16-9"></span>14. Hu, E.J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W.: LoRA: Low-rank adaptation of large language models. In: ICLR (2022)
- <span id="page-16-14"></span>15. Ji, S., Pan, S., Cambria, E., Marttinen, P., Yu, P.S.: A survey on knowledge graphs: Representation, acquisition, and applications. IEEE Trans. Neural Netw. Learn. Syst. 33, 494–514 (2022)
- <span id="page-16-7"></span>16. Lewis, M., Liu, Y., Goyal, N., Ghazvininejad, M., Mohamed, A., Levy, O., Stoyanov, V., Zettlemoyer, L.: BART: Denoising sequence-to-sequence pre-training for natural language generation, translation, and comprehension. In: ACL. pp. 7871–7880 (2020)
- <span id="page-16-5"></span>17. Liu, Y., Sun, Z., Li, G., Hu, W.: I know what you do not know: Knowledge graph embedding via co-distillation learning. In: CIKM. pp. 1329–1338 (2022)
- <span id="page-16-17"></span>18. Miller, G.A.: WordNet: A lexical database for English. Commun. ACM 38, 39–41 (1995)
- <span id="page-16-10"></span>19. Nayyeri, M., Vahdati, S., Khan, M.T., Alam, M.M., Wenige, L., Behrend, A., Lehmann, J.: Dihedron algebraic embeddings for spatio-temporal knowledge graph completion. In: ESWC (2022)
- <span id="page-16-6"></span>20. Omeliyanenko, J., Zehe, A., Hotho, A., Schlör, D.: CapsKG: Enabling continual knowledge integration in language models for automatic knowledge graph completion. In: ISWC (2023)

- 18 Y. Liu et al.
- <span id="page-17-18"></span>21. Qu, M., Chen, J., Xhonneux, L.A.C., Bengio, Y., Tang, J.: RNNLogic: Learning logic rules for reasoning on knowledge graphs. In: ICLR (2021)
- <span id="page-17-6"></span>22. Raffel, C., Shazeer, N., Roberts, A., Lee, K., Narang, S., Matena, M., Zhou, Y., Li, W., Liu, P.J.: Exploring the limits of transfer learning with a unified text-to-text transformer. J. Mach. Learn. Res. 21, 1–67 (2020)
- <span id="page-17-7"></span>23. Saxena, A., Kochsiek, A., Gemulla, R.: Sequence-to-sequence knowledge graph completion and question answering. In: ACL. pp. 2814–2828 (2022)
- <span id="page-17-0"></span>24. Saxena, A., Tripathi, A., Talukdar, P.P.: Improving multi-hop question answering over knowledge graphs using knowledge base embeddings. In: ACL. pp. 4498–4507 (2020)
- <span id="page-17-12"></span>25. Sun, Z., Deng, Z., Nie, J., Tang, J.: RotatE: Knowledge graph embedding by relational rotation in complex space. In: ICLR (2019)
- <span id="page-17-16"></span>26. Toutanova, K., Chen, D., Pantel, P., Poon, H., Choudhury, P., Gamon, M.: Representing text for joint embedding of text and knowledge bases. In: EMNLP. pp. 1499–1509 (2015)
- <span id="page-17-9"></span>27. Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M., Lacroix, T., Rozière, B., Goyal, N., Hambro, E., Azhar, F., Rodriguez, A., Joulin, A., Grave, E., Lample, G.: LLaMA: Open and efficient foundation language models. arXiv 2302.13971 (2023)
- <span id="page-17-14"></span>28. Vashishth, S., Sanyal, S., Nitin, V., Talukdar, P.P.: Composition-based multirelational graph convolutional networks. In: ICLR (2020)
- <span id="page-17-3"></span>29. Wang, B., Shen, T., Long, G., Zhou, T., Wang, Y., Chang, Y.: Structure-augmented text representation learning for efficient knowledge graph completion. In: WWW. pp. 1737–1748 (2021)
- <span id="page-17-4"></span>30. Wang, L., Zhao, W., Wei, Z., Liu, J.: SimKGC: Simple contrastive knowledge graph completion with pre-trained language models. In: ACL. pp. 4281–4294 (2022)
- <span id="page-17-10"></span>31. Wei, Y., Huang, Q., Zhang, Y., Kwok, J.T.: KICGPT: Large language model with knowledge in context for knowledge graph completion. In: EMNLP-Findings. pp. 8667–8683 (2023)
- <span id="page-17-15"></span>32. Xie, R., Liu, Z., Lin, F., Lin, L.: Does William Shakespeare really write Hamlet? Knowledge representation learning with confidence. In: AAAI. pp. 4954–4961 (2018)
- <span id="page-17-8"></span>33. Xie, X., Zhang, N., Li, Z., Deng, S., Chen, H., Xiong, F., Chen, M., Chen, H.: From discrimination to generation: Knowledge graph completion with generative transformer. In: WWW. pp. 162–165 (2022)
- <span id="page-17-13"></span>34. Yang, F., Yang, Z., Cohen, W.W.: Differentiable learning of logical rules for knowledge base reasoning. In: NeurPS (2017)
- <span id="page-17-1"></span>35. Yang, Y., Ye, Z., Zhao, H., Meng, L.: A novel link prediction framework based on gravitational field. Data Sci. Eng. 8, 47–60 (2023)
- <span id="page-17-5"></span>36. Yao, L., Mao, C., Luo, Y.: KG-BERT: BERT for knowledge graph completion. arXiv 1909.03193 (2019)
- <span id="page-17-11"></span>37. Yao, L., Peng, J., Mao, C., Luo, Y.: Exploring large language models for knowledge graph completion. arXiv 2308.13916 (2023)
- <span id="page-17-17"></span>38. Zhu, Y., Wang, X., Chen, J., Qiao, S., Ou, Y., Yao, Y., Deng, S., Chen, H., Zhang, N.: LLMs for knowledge graph construction and reasoning: Recent capabilities and future opportunities. arXiv 2305.13168 (2023)
- <span id="page-17-2"></span>39. Zhu, Z., Zhang, Z., Xhonneux, L.A.C., Tang, J.: Neural Bellman-Ford networks: A general graph neural network framework for link prediction. In: NeurIPS. pp. 29476–29490 (2021)