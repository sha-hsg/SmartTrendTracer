# Distilling Event Sequence Knowledge From Large Language Models

Somin Wadhwa 1 , 2 , Oktie Hassanzadeh 1 , Debarun Bhattacharjya 1 , Ken Barker 1 , and Jian Ni 1

1 IBM Research, USA <sup>2</sup> Northeastern University, USA wadhwa.s@northeastern.edu,{hassanzadeh, debarunb, kjbarker}@us.ibm.com

Abstract. Event sequence models have been found to be highly effective in the analysis and prediction of events. Building such models requires availability of abundant high-quality event sequence data. In certain applications, however, clean structured event sequences are not available, and automated sequence extraction results in data that is too noisy and incomplete. In this work, we explore the use of Large Language Models (LLMs) to generate event sequences that can effectively be used for probabilistic event model construction. This can be viewed as a mechanism of distilling event sequence knowledge from LLMs. Our approach relies on a Knowledge Graph (KG) of event concepts with partial causal relations to guide the generative language model for causal event sequence generation. We show that our approach can generate high-quality event sequences, filling a knowledge gap in the input KG. Furthermore, we explore how the generated sequences can be leveraged to discover useful and more complex structured knowledge from pattern mining and probabilistic event models. We release our sequence generation code and evaluation framework, as well as corpus of event sequence data.

Keywords: Knowledge Graphs, Large Language Models, Knowledge Distillation

## 1 Introduction

Building probabilistic models from event sequence data has numerous practical applications across different domains when plentiful high-quality event data is available. For example, in Finance, event models can be used to predict stock market trends and make informed investment decisions. In Healthcare, event models can help identify patterns and correlations in patient data to improve diagnoses and treatment plans. In the field of Cybersecurity, these models can be used to detect and prevent potential cyber attacks by analyzing the sequence of events leading up to a breach. A common characteristic of the data in these domains is that sequences are clearly associated with an entity (e.g., a company, a person, or a device). There are however other domains where such a clean association between events and entities may not be possible. One such application is news event analysis [\[8,](#page-15-0)[13,](#page-16-0)[18](#page-16-1)[,30\]](#page-17-0). While various news sources record

and describe newsworthy events, it is often not possible to automatically put together coherent sequences of events, because each event may involve multiple topics and actors, and many correlated and unrelated events may be occurring simultaneously or in close proximity

Prior work has addressed this challenge by devising automated mechanisms for extracting narratives [\[29,](#page-17-1)[33\]](#page-17-2), topic detection and tracking [\[2\]](#page-15-1), and timeline summarization [\[16\]](#page-16-2). While these different categories of solutions have been successful in a range of applications, the outcome is inherently noisy and not in the form of structured event sequences useful for the construction of event models. Prior work has shown little success in automatically turning narratives into structured sequences. In this paper, we explore a novel mechanism for creating structured event sequences in such domains, using generative language models.

Large Language Models [\[7,](#page-15-2)[31](#page-17-3)[,38\]](#page-18-0) have recently become the dominant paradigm in a range of natural language processing (NLP) tasks [\[11\]](#page-15-3) and often beat traditional approaches on a number of challenging tasks, including complex arithmetic reasoning [\[22\]](#page-16-3) and open-domain question answering [\[23\]](#page-17-4). In this paper, our goal is to examine the capability of LLMs to generate structured event sequences useful for event analysis. Our aim is to use LLMs directly for generation of event sequences, as opposed to improving prior extraction methods that would rely on high-quality and comprehensive sources describing detailed event sequences for a wide variety of events. Our hypothesis is that LLMs trained on large corpora have already gathered the required knowledge of plausible event sequences and therefore can be suitably guided to produce diverse and high-quality event sequences. To effectively distill this knowledge, we use event-related concepts in Wikidata [\[36\]](#page-18-1), a comprehensive general-domain knowledge graph, to guide the sequence generation. This can be viewed as a novel mechanism for knowledge-guided text generation [\[42\]](#page-18-2) and symbolic knowledge distillation [\[39\]](#page-18-3). We then use these generated sequences for pattern mining and learning probabilistic event models, as a way of further structuring the underlying knowledge. Figure [1](#page-2-0) shows our overall framework along with examples from our experiments of patterns mined from an LLM-generated event sequence collection, as a well as a simple model learned from the collection.

In summary, we make the following contributions:

- 1. We devise a new iterative in-context prompting strategy for generating highquality event sequences using LLMs. To the best of our knowledge, we are the first to use LLMs to generate structured event sequences for the purpose of analyzing various event models.
- 2. We compile high-quality event sequences using our generation mechanism, based on a curated set of high-level event concepts (classes) from Wikidata that represent newsworthy events.
- 3. We develop an evaluation framework and conduct experiments to show the value of LLM-powered event sequence generation on replicating and augmenting knowledge in structured representations such as knowledge graphs.
- 4. We further demonstrate the practical usefulness of our approach by leveraging downstream pattern mining and probabilistic event models.

![](_page_2_Figure_0.jpeg)

Distilling Event Sequence Knowledge From Large Language Models 3

Fig. 1. An overview of our framework for distilling event sequence knowledge from LLMs, along with examples portraying potential use cases. We show that by (1) starting with a sparse knowledge graph such as Wikidata, we can generate targeted event sequences. Owing to the inherent sparsity in the underlying KG, we can (2) use LLMs to carry out a portion of the evaluation (i.e. precision) to select an optimal model. On this new generated sequence dataset, we then (3) apply classical pattern-mining algorithms (e.g., GSP) to identify potentially interesting has\_cause and has\_effect event sequence chains, and (4) learn summary Markov models (SuMMs) to identify potential influencing events for particular event types of interest; these are both illustrations of extracting complex structured knowledge from the generated sequences.

*P*(refugee crisis | mass migration, AND famine) = 0.91

<span id="page-2-0"></span>*P*(mass migration | famine) = 0.21

Our code and generated sequence data are included in the supplementary material, and will be made publicly available for future research.

## 2 Related Work

News Event Analysis The primary applications of our work are around news event analysis and forecasting. Liang [\[45\]](#page-18-4) presents a taxonomy of different flavors of event prediction in the literature. Our target event prediction applications fall under the "Semantic Prediction" category, with time and location details not being of interest, and the primary goal being the prediction of "event profiles" such as event types. Seminal work in this area is the work of Radinsky et al. [\[30\]](#page-17-0) where causal relations between past events are extracted from text and then a

knowledge graph is utilized to generalize the extracted relations in order to make predictions. More recent work has explored the use of graph sequence mining over a graph structure representation of events extracted from text [\[8\]](#page-15-0), with graph mining used as a mechanism of extracting useful relations from large and noisy outputs of extraction. The application of building event sequence models over such outputs has not been explored. Our paper explores an alternative approach of event sequence generation that is capable of generating longer and potentially higher-quality sequences.

Event Sequence Extraction from Text There is a wealth of literature on different methods of extracting sequences from textual corpora. Norambuena et al. [\[29\]](#page-17-1) present a comprehensive survey of automated methods of narrative extraction. Narratives contain several elements including events, participants (actors/protagonists), time, and space. The task of event detection itself is a highly challenging task and the topic of extensive research [\[9,](#page-15-4)[41,](#page-18-5)[24\]](#page-17-5), which has its root in the Topic Detection and Tracking (TDT) task [\[33\]](#page-17-2). This line of work started out as a DARPA-sponsored initiative with the same name [\[3\]](#page-15-5). Another closely related task is news timeline summarization [\[16\]](#page-16-2). While pattern mining algorithms have been applied to the output of such extractions, e.g. for creation of "domain templates" [\[14\]](#page-16-4), we are not aware of any attempts to use the extractions to construct event models for analysis or prediction. This is mainly due to the fact that the output of such methods often result in very short and noisy sequences, not suitable for the majority of event sequence models.

Sequential Pattern Mining and Event Sequence Models Sequential pattern mining and related approaches have been the subject of extensive research [\[27,](#page-17-6)[26,](#page-17-7)[28](#page-17-8)[,15\]](#page-16-5). These algorithms take in a set of sequences (or "sequential records") with a set of unique events (or "items") and often a "minimum support" threshold, and return as output a ranked set of all frequent sequences in a given sequence collection (or database) meeting the minimum support threshold. There is also a long line of work on statistical and probabilistic models for analysis of different kinds of event sequences. Our focus in this paper is on multivariate event sequences, i.e., sequences of various event types without timestamps. Markov models for sequences [\[32,](#page-17-9)[5\]](#page-15-6) and long short-term memory (LSTM) [\[20\]](#page-16-6) models are examples of prediction models. We leverage a more recent family of models – Summary Markov models [\[6\]](#page-15-7) – for some of the experiments in this paper that involve analyzing generated event sequences.

## 3 Knowledge-Guided Event Sequence Generation

Through utilizing LLMs, we model event prediction as a conditional generation task under zero and iterative few-shot settings. Our targets are linearized sequences of event concepts. We begin by prompting a large language model (with in-context exemplars) with an event trigger y<sup>1</sup> to generate the next concept from a defined set of labels, and repeat this process until we get a sequence of desired length. Formally, given an event trigger T , we model the probability of generating linearized string y of length T containing N unique event concepts that follow T in sequence:

$$p_{\text{LM}}(y|\mathcal{T}) = \prod_{t=2}^{T} p(y_t|\mathcal{T}, y_{\leq t-1}) \tag{1}$$

This is the standard conditional language modeling objective. We try multiple prompting techniques and qualitatively observe optimal results with an iterative in-context few-shot prompting strategy (Figure [2\)](#page-5-0). Specifically, we start with a set of six randomly selected examples of the form – "What usually follows event X?". This approach follows the incremental prompting procedure from [\[25\]](#page-17-10). Based on the model output (Y ) from a pre-specified vocabulary, we append this same example to the original prompt in conjunction (i.e. "What usually follows event X and Y ?") with ICL examples of the same form. As shown in Figure [2,](#page-5-0) our iterative technique serves dual purposes: (i) it leverages in-context learning; and (ii) eliminates the need for implementing complex resolvers to post-process model outputs. We repeat this process until a sequence of a desired minimum length m is achieved (in our experiments, m = 3) or we've exhausted a maximum number of tries (k = 10 in our experiments) to generate an in-domain event type.

Identifying Event Concepts With incremental prompting we curate a new dataset of high-level event concepts (classes) from Wikidata that represent newsworthy events. To do so, we query Wikidata for event concepts that have links to Wikinews articles and are instances of classes that are a subclass of the occurrence class, i.e., indicating they are newsworthy event classes. We gathered 50 top-level classes for these event concepts, each having multiple labels (e.g. conflict → conflict (psychological), dispute, disagreement, etc.). This yielded a total of 202 unique event labels for the 50 top-level classes. Most of these event concepts have some causal relations (i.e. has\_cause or has\_effect). We use these relation pairs as in-context exemplars to create our prompts. We then generate event sequences through iterative in-context prompting (Figure [2\)](#page-5-0). Full length prompts used in all our experiments are provided in the Appendix.

To generate new event sequences in a zero-shot setting, we start with an event trigger (e.g. a concept like workplace accident), create a prompt with instructions describing desired relationships and a few in-context exemplars (ICL prompt), and constrained the model output to the original 50 event concept labels to generate the next event in the sequence (full text of the prompt is provided in the supplementary material). We append the model output to another ICL prompt with conjunctive event examples (i.e. questions of the form "What happens after X, Y, and Z"). We repeat this process until we reach a pre-defined maximum sequence length (in this case, 10) or until the model fails to generate an in-vocabulary response in k maximum attempts (in this case, k = 3). In this process, we test the following two ablations –

![](_page_5_Figure_1.jpeg)

<span id="page-5-0"></span>Fig. 2. Illustration of our approach to elicit event sequence knowledge given a label of interest. Use of instructional in-context exemplars substantially reduces the need for post-processing LLM output in addition to constraining the output label space.

Number of exemplars We varied the number of in-context exemplars between 1- 12. This is in addition to the zero-shot experiments described in the main paper. We evaluated recall (i.e. proportion of references captured by the resulting output sequences) for all generated outputs in an automated way through matching lexical alignment with Wikidata references. We observed none to marginal improvements by varying the number of exemplars beyond 3 in the initial trigger prompt, and beyond 5 in the second iterative prompt.

Selection of specific exemplars Selecting in-context examples is an incredibly noisy process [\[44\]](#page-18-6). We started with a static set of randomly selected examples, however owing to Wikidata's inherent label imbalance (political and economic events dominate newsworthy concepts), this led to erratic results, i.e. high recall on similar concepts but not otherwise.

We then tested a dynamic selection method where every instance of the prompt would contain examples similar to target\_label. To achieve this, we used BERT embeddings [\[12\]](#page-16-7) to retrieve (using cosine distance) examples from the reference set. This approach however led to a lower macro-recall and, upon manual inspection of outputs, we observed a high degree of redundancy, i.e. generated outputs were copied from the ICL exemplars.

To solve for these issues, we reverted to the static prompt examples but manually selected a mix of event topics to be included in the prompt. Our current selection of the prompt yields higher macro-recall than both of the aforementioned techniques tested. While we believe there may be better techniques to select ideal candidates for ICL exemplars [\[4,](#page-15-8)[1\]](#page-15-9) and understand how their compositionality affects specific outputs, we consider such an analysis to be beyond the scope of our work.

We repeat this sequence generation procedure on all 202 event concepts, generating 2, 276 event sequences with an average length of 5.7 labels per sequence.

## 4 Assessing the Quality of LLM-Generated Event Sequences

Open-ended text generation in a task like event sequencing, with extremely sparse reference data, poses unique challenges to the evaluation of model outputs [\[37\]](#page-18-7). The traditional scheme to evaluate discrete model outputs has been to calculate precision and recall for the generated outputs against a predefined reference test set. However, under open-world settings and particularly when a sparse KG like Wikidata is used as reference data, a missing causal relation between two event classes in a sequence may very well be a valid relation. Therefore, it is not possible to automatically derive an accurate measure of precision and recall purely using Wikidata as reference data. We take a multi-pronged evaluation approach to assess the quality and usefulness of the generated event sequences across multiple tasks. This section presents our approach in evaluating the quality of generated event sequences, along with the results of this evaluation. An evaluation of the usefulness of the generated event sequences is presented in Section [5.](#page-9-0)

### 4.1 Human Evaluation of Cause-Effect Prediction Accuracy of LLMs

To quantify how well model outputs correlate with human assessments, we first conduct a small-scale human evaluation on a different, independent eventcommonsense reasoning dataset: ATOMIC [\[21\]](#page-16-8). ATOMIC consists of eventcentered pairs of instances of the form IsAfter (Y comes after X) and Causes (X causes Y). We use these instances as input prompts to the model and then ask human annotators to evaluate model outputs. Specifically, we show human annotators anonymized model outputs and true references and elicit their preferences given a trigger event.

To generate outputs, we follow the same strategy as above for a set of 200 randomly selected event-centered input instances (100 each of the type 'X Causes

Y ' and 'Y IsAfter X')[3](#page-7-0) . We then present the model output and the true reference from ATOMIC to three human annotators. For example, a typical instance presented to human evaluators was of the form:

```
Input Instance: PersonX drops out of high school
Response 1: PersonX gets a job
Response 2: PersonX turns PersonX's life around
Type: IsAfter
```

One of the responses above is the LLM output, while the other is the true reference. The human evaluators are then asked to answer the following questions–

- Are both responses functionally similar?
- Which response do you prefer?
- Which response, if any, is completely irrelevant?

We find that in an overwhelming majority of the cases, the models generate output that is semantically equivalent to the reference (even though there is no direct lexical alignment), or output that the humans prefer over the true reference. Based on the responses from human evaluators[4](#page-7-1) , we observe that humans found 65.82% of response pairs functionally equivalent. That is, even though not lexically aligned, they meant the same thing. In 27.64% of the instances the humans preferred the model-generated event instance over the true reference. In only 6.55% of instances did the humans prefer the true reference over the model-generated output.[5](#page-7-2) These results reinforce our underlying assertion that LLMs are capable of event-centered reasoning, and therefore could produce high-quality event sequence collections.

### 4.2 Evaluation of Recall

Despite the sparsity of causal relations in Wikidata, one can still reasonably estimate recall through pairwise comparisons of generated event classes to the existing causal relations in Wikidata. We build a reference set of causal relations in Wikidata by curating a list of all the pairs of event concepts that have any of the several causal relations[6](#page-7-3) in Wikidata in any direction, including has\_cause (P828), has\_immediate\_cause (P1478), has\_contributing\_factor (P1479), and has\_effect(P1542). Our results show that this is an effective mechanism of comparing recall across methods, as larger models that are expected to have better accuracy yield higher recall scores.

<span id="page-7-0"></span><sup>3</sup> Complete details about ATOMIC are available in Table 1 in [\[21\]](#page-16-8).

<span id="page-7-1"></span><sup>4</sup> We observe strong inter-rater agreement with a Fleiss kappa, κ = 0.81; conflicting response labels were aggregated through majority vote.

<span id="page-7-2"></span><sup>5</sup> Additional details on these experiments are available in the supplementary material (Appendix).

<span id="page-7-3"></span><sup>6</sup> [www.wikidata.org/wiki/Wikidata:List\\_of\\_properties/causality](www.wikidata.org/wiki/Wikidata:List_of_properties/causality)

### 4.3 Evaluation of Precision

To overcome sparsity in reference data, prior work has generally relied on human evaluations [\[10\]](#page-15-10) for estimating precision, which entails looking at pairs of events and asking annotators whether or not the events in question have a causal relationship. Such a process for potentially thousands of event pairs (like in our case) can be very cost prohibitive. Furthermore, recent research [\[46,](#page-18-8)[19,](#page-16-9)[47\]](#page-19-0) indicates that pre-trained language models themselves might outperform lay human annotators such as those found on Amazon Mechanical Turk. For instance, [\[19\]](#page-16-9) demonstrated that labeling data under a few-shot chain-of-thought prompt ("explain-then-annotate" setting) surpasses crowdworker annotations on relevance assessments. Following these results, we use LLMs for evaluating precision and for selecting the most optimal model. We propose evaluating precision for model selection as a binary classification task. Given two events e1, e2, an evaluator model must evaluate whether e<sup>1</sup> reasonably leads to e<sup>2</sup> under a has\_cause or has\_effect relationship. To do this, we start with a large instruction-tuned model (in our case, Flan-T5-XXL (11B) [\[11\]](#page-15-3)) and adopt instructional in-context few shot prompting to classify whether or not e<sup>1</sup> reasonably leads to e2, and for the model to provide a justification for its results. While we hypothesize that such an approach may yield noisy results, a small manual assessment as well as our results comparing different models with different evaluator models indicate that this approach yields reliable results for comparing different models, and a reasonable estimate of the overall precision of the model. Note that the evaluator performs only a simple binary classification task that has a very high accuracy even in smaller models.

### 4.4 Settings

We performed all our model inference related experiments on two NVIDIA V100 GPUs. We used the Huggingface library v4.26.1 [\[40\]](#page-18-9) and publicly available model checkpoints.[7](#page-8-0) Classical pattern mining algorithms (GSP, SPADE) were implemented in Python through the use of spmf[8](#page-8-1) library v1.4. For event sequence generation, we use in-context learning under zero shot settings for all LLMs, with top-k sampling (k = 50, in conjunction with top-p, where p = 0.95). To identify influencing events from Summary Markov Models (SuMMs), we use implementations from [\[6\]](#page-15-7) and split the dataset (generated from LLMs) into train/dev/test sets (70%/15%/15%) to generate results reported in Table [2.](#page-12-0) BSuMMs and OSuMMs were learned with hyperparameters of α = 0.1, γ = 0.5 and a look-back (κ) window of 4.

### 4.5 Results

Table [1](#page-9-1) summarizes our results from these experiments. While prior work as proven the concept of LLM-as-a-judge [\[47\]](#page-19-0) when much larger LLMs like GPT-4 are used, here we use less resource-intensive LLMs not for evaluation of the

<span id="page-8-0"></span><sup>7</sup> [huggingface.co/docs/transformers/model\\_doc/flan-t5](huggingface.co/docs/transformers/model_doc/flan-t5)

<span id="page-8-1"></span><sup>8</sup> pypi.org/project/spmf/

|                               | Precision Evaluator Model (P)        |      |  | R              | F-1 |
|-------------------------------|--------------------------------------|------|--|----------------|-----|
|                               | Flan-T5-Large Flan-T5-XL Flan-T5-XXL |      |  |                |     |
| Flan-T5-Large (783M) [11]     | 0.73                                 | 0.72 |  | 0.72 0.47 0.57 |     |
| Flan-T5-XL (3B)               | 0.75                                 | 0.75 |  | 0.78 0.49 0.60 |     |
| Open-Research LLaMA (3B) [35] | 0.70                                 | 0.69 |  | 0.72 0.45 0.55 |     |
| Flan-T5-XXL (11B)             | 0.79                                 | 0.79 |  | 0.81 0.54 0.65 |     |

<span id="page-9-1"></span>Table 1. Evaluation of LLM-generated sequences. For the purpose of evaluating recall (R), we count event pairs (e1, e2) if such a pair exists in Wikidata. For evaluating precision (P), we treat correctness of all generated event pairs (e1, e2) as a standard classification task. Best-performing model scores are in bold.

absolute quality of the generated sequences, but for comparison of the relative performance of models

Since we use our models for dual purposes – for generating and evaluating event sequences, owing to this inherent conflict we find it prudent to independently assess these evaluator models. To ensure robustness of our results, we use multiple evaluator models and find no significant difference between evaluated precision across different models used as evaluators with the largest model performing marginally better as a precision evaluator.

### 4.6 Discussion

We observed in our analysis that some event triggers did not produce any sequences. Out of the 202 unique input event triggers in our data, 8 event triggers yielded sequences of length 1, i.e., no sequences. This means that the underlying model could not select a relevant event concept from the provided vocabulary that might follow the given trigger.

## <span id="page-9-0"></span>5 Knowledge Distillation Through Event Sequence Analysis

Given a high-quality collection of event sequences generated by utilizing LLMs, we use pattern mining to discover high-support sequence patterns not directly derivable from the knowledge graph, and learn probabilistic models to discover complex event sequence rules.

### 5.1 Mining New Patterns

In order to derive new, unseen relationships (has\_cause or has\_effect) between the extracted event classes, we use the generated event sequence collection followed by classical frequent itemset mining algorithms like GSP [\[34\]](#page-17-11) and SPADE [\[43\]](#page-18-11) to derive new high support patterns. This aspect of the overall workflow is illustrated in the middle section of Figure [1,](#page-2-0) where high-support patterns are mined from event sequences.

The classical pattern mining algorithms we use to mine for new event patterns are both Apriori-based approaches. Under both methods, given two sequences of the same event concept class

$$\alpha = < a_1, a_2, \dots, a_n > \text{ and } \beta = < b_1, b_2, \dots, b_n > \tag{2}$$

α is a subsequence of β denoted as α ⊆ β iff there exists a set of values 1 ≤ j<sup>1</sup> < j<sup>2</sup> < ... < j<sup>n</sup> ≤ m such that a<sup>1</sup> ⊆ bj1, a<sup>2</sup> ⊆ bj2, ..., a<sup>n</sup> ⊆ bjn,; then β is a supersequence of α. Given multiple such sequences and a support threshold, the task here is to find a set of frequent event subsequences. GSP is depicted in Algorithm [1\)](#page-10-0). SPADE uses a "vertical database format", which stores sequences as lists of itemsets associated with their IDs (referred to as "id-lists"), which allows faster support counting. The algorithm organizes the search space into equivalence classes, and avoids multiple scans of the sequences.

Algorithm 1 Generalized Sequential Pattern (GSP) Mining Algorithm

<span id="page-10-0"></span>1: Input: Database of sequences D, minimum support threshold min\_sup 2: Output: Set of all sequential patterns SP 3: SP ← ∅ 4: C<sup>1</sup> ← set of all individual items in D that meet min\_sup 5: L<sup>1</sup> ← filter candidates in C<sup>1</sup> by min\_sup 6: k ← 2 7: while Lk−<sup>1</sup> ̸= ∅ do 8: C<sup>k</sup> ← generate\_candidates(Lk−1) 9: for each sequence s ∈ D do 10: for each candidate c ∈ C<sup>k</sup> do 11: if c is contained in s then 12: increment support count of c 13: end if 14: end for 15: end for 16: L<sup>k</sup> ← filter candidates in C<sup>k</sup> by min\_sup 17: SP ← SP ∪ L<sup>k</sup> 18: k ← k + 1 19: end while 20: return SP

Examples of Mined Patterns Following are example outputs from application of GSP on LLM outputs.

Mined Pattern Example 1

```
Pattern: Civil Disorder (Q686984) → Democratization (Q1064441)
→ Energy Crises (Q8413663) Support: 5
```

The pattern above occurs with a support value of 5 i.e. at least supported by 5 super-sequences. Empirically, we can find support for such a pattern in history.[9](#page-11-0) In 1994, the country of South Africa democratized post civil disorder. This led to an increased energy demand over the following decade, eventually culminating in a full blown energy crises starting 2003.

### Mined Pattern Example 2

Pattern: Famine (Q168247) → Refugee Crises (Q20898283) → Post Traumatic Stress Disorder(Q202387) Support: 5

The pattern above again occurs with a support value of 5 i.e. at least supported by 5 super-sequences. Similar to the previous example, evidence supporting such an event tranisiton can be found in real life.[10](#page-11-1) During the Great Irish Famine people were forced to relocate and flee Ireland causing a refugee crises. A great number of these individuals suffered from mental health crises (e.g. PTSD) due to the events directly associated with the famine.

### 5.2 Identifying Influencing Sets through Summary Markov Models

Learning about potential influencing events that lead to a given event type in a large set of event sequences is an important aspect of analyzing multivariate event sequences, i.e. events without time stamps, like the ones generated by our models. Classic kth order Markov chains capture these dynamics by modeling the probability of observing a particular event type given the preceding k events insequence. The recent family of summary Markov models (SuMMs) [\[6\]](#page-15-7) generalize other well known Markov models for event sequences by leveraging a function that summarizes historical event occurrences, and identifying the subset of event types that affect the probability of occurrence of event types of interest; this forms the influencing set.

We use the LLM-generated sequences to learn two types of SuMMs: binary SuMMs (BSuMMs) and ordinal SuMMs (OSuMMs). In BSuMMs, it is only the presence or absence of an event in the relevant history that has an effect on the occurrence of other events, while in OSuMMs the order of the events is also taken into account. We refer the reader to Sections 3.3 and 3.4 in [\[6\]](#page-15-7) for complete formal definitions and methods for learning SuMMs over event sequence collections. Briefly, given a subset of event labels of interest X ∈ L and a set of parameters Θ<sup>X</sup> = {θx|h}, where θx|<sup>h</sup> is the probability of a given event label x ∈ X occurring at any position in the sequence given the historical event occurrences h, influencing and non-influencing event sets can be formally defined as label sets U = L\ U are influencing sets for event labels X such that they minimally determine the probability of observing any particular label of interest x<sup>i</sup> for a given position i in the sequence.

<span id="page-11-0"></span><sup>9</sup> [wikipedia.org/wiki/South\\_African\\_energy\\_crisis](wikipedia.org/wiki/South_African_energy_crisis)

<span id="page-11-1"></span><sup>10</sup> [wikipedia.org/wiki/Great\\_Famine\\_\(Ireland\)](wikipedia.org/wiki/Great_Famine_(Ireland))

Evaluation: SuMMs vs LSTMs Following the evaluation strategy implemented in [\[6\]](#page-15-7), we focus on individual labels of interest and conduct an evaluation around probabilistic prediction. Consequently, we select negative log loss as the evaluation metric. Table [2](#page-12-0) summarizes our results on the test set for both BSuMMs and OSuMMs, along with a simple LSTM baseline. We observe that models trained on event sequences generated from larger models (e.g. Flan-T5-XXL) fare better than the ones generated from their smaller counterparts (e.g. Flan-T5-Large). We treat this observation as a proxy for generated event sequence quality. That is, better quality sequences lead to better predictive models.

<span id="page-12-0"></span>

| (↓) Data Generator Model      |         | BSuMMs OSuMMs LSTM |                |
|-------------------------------|---------|--------------------|----------------|
| Flan-T5-Large (783M) [11]     | -63.49  | -84.29             | -109.28        |
| Flan-T5-XL (3B)               | -63.20  | -92.65             | -121.23        |
| Open-Research LLaMA (3B) [35] | -110.57 | -101.29            | -190.68        |
| Flan-T5-XXL (11B)             | -57.99  |                    | -78.64 -108.89 |

Table 2. Negative log likelihood (lower magnitude is better ) averaged over interest labels from LLM-generated (Flan-T5-XXL) event sequences. Lookback window (k) for LSTM was fixed to 5. Best-performing data generator model scores are in bold.

Qualitative Assessment Figure [1](#page-2-0) shows examples of learned influencing sets using BSuMMs for refugee crisis and mass migration events. Two events mass migration and famine are identified as influencing events for refugee crisis. The model indicates that the occurrence of both mass migration and famine together has a 0.91 probability of resulting in refugee crisis as a part of a sequence of events. On the other hand the occurrence of mass migration in the absence of famine has a 0.31 probability of resulting in refugee crisis. BSuMMs and OSuMMs deploy a greedy score-based forward and backward search strategy to efficiently discover the minimal influencing sets. Overall, the discovery of influencing sets from LLM-generated data provides a mechanism of distilling complex symbolic knowledge from the output of LLMs.

We provide two more examples below of influencing sets derived from the application of SuMMs. For each example, we show evidence supporting the accuracy of the extracted knowledge. Overall, these results show the high quality and usefulness of the distilled event sequence knowledge.

Influencing Set Example 1 The following example identifies "Hate Crimes" as a predecessor to the occurrence of "Civil Disorder" related events.

X: Civil Disorder (Q686984) Parent: Hate Crime (Q459409)

– P(Civil Disorder|NO Hate Crime) = 0.12

```
– P(Civil Disorder|Hate Crime) = 0.55
```

In the example above, we see that the likelihood of a civil disorder is greatly influenced by the occurrence of a hate crime.

Influencing Set Example 2 The following example identifies "Disease Outbreaks" and "Lockdowns" as precursors to the institution of "Travel Restrictions".

```
X:Travel Restriction (Q87745167)
Parents: Disease Outbreak (Q3241045), Lockdown (Q6665312)
 – P(TR|NO Outbreak, NO Lockdown) = 0.0.0001
 – P(TR|Lockdown, NO Outbreak) = 0.0.29
```

– P(TR|NO Lockdown, Outbreak) = 0.26

Quite intuitively, we see here the likelihood of Travel Restrictions directly correlate with the institution of Disease Outbreaks and Lockdowns (since the latter have been lately associated with the former).

Error Analysis We observed that in some cases, the identified influencing setsfor some event concepts were not correct or, at times, illogical. Qualitatively, we observe that this occurs with rare event types that do not appear often either in the underlying knowledge graph, or in the LLM-generated set of event sequences. Consequently, SuMMs fail to identify logical influencing sets. For example, for the event type United States Presidential Impeachment, BSuMM model identified unequal treaty as the influencing event.

## 6 Conclusions and Future Work

In this paper, we presented methods of distilling event sequence knowledge from large language models. We first presented an approach of generating high-quality event sequences through knowledge-guided generation using LLMs. We then conducted a three-pronged quantitative and qualitative evaluation of our results. First, we evaluated LLM-generated event sequences in absolute terms through manual evaluation and automated evaluation using standard accuracy metrics. Second, we looked at some qualitative examples of newly identified high support sequences not already present in our base knowledge graph i.e. Wikidata. Finally, we gauge how probabilistic models like SuMMs fare when trained on LLM-generated data. We found that through our carefully-designed elicitation procedure, LLMs are capable of producing high-quality event sequences that can be used for the downstream tasks of pattern mining and the construction of probabilistic event models such as SuMMs.

This work demonstrates the utility of large language models for extracting event-related information and helps researchers better navigate the complex interaction between event-related entities. While we have demonstrated some usecases for the resulting dataset of event sequences – mining logical rules/patterns and extracting influencing event types – the resulting datasets in this work and those from other domains could themselves be a useful resource for researchers, as one may leverage them suitably to inform or justify decision-making. We make our code and datasets publicly available for future research. Here, we outline a number of directions for future work:

- In this paper, we used Wikidata as our base source of knowledge. The event concepts found on Wikidata often appear in the pre-training datasets of large language models. We did not consider more complex, domain-specific datasets of non-timestamped events (e.g. Healthcare, Finance). Applying LLMs to generate domain-specific events may require considerable amounts of data to fine-tune these models, and collecting such supervision to train these models at scale may be prohibitively expensive.
- A key element of our evaluation strategy (precision) involves the use of the same language models that were used to generate the sequences being evaluated in the first place. Through qualitative examples and past research on using LLMs as annotators, we observe that such a strategy yields a noisy but useful signal for evaluating model performance. However, an ideal and accurate evaluation of model outputs should involve the use of human annotators and a validation of the use of larger LLMs as a part of LLMs-as-a-judge [\[47\]](#page-19-0) evaluation strategy. Furthermore, our use of smaller models was justified in part due to the simplicity of the precision evaluation task, which can be posed as a binary classification task. It will be interesting to evaluate the correctness of post-hoc explanations generated by models for their corresponding output during precision evaluation, as such explanations are key to the usefulness of the distilled knowledge, particularly in critical decision support applications.
- In the context of our domain of interest in this paper (news event analysis), an exciting avenue for future research is to study the effect of utilizing structured knowledge distilled from LLMs in a pipeline for future event prediction, and a comparison with the performance of human forecasters. Recent work [\[17\]](#page-16-10) claims that LLMs, without symbolic knowledge elicitation, come close and in some cases surpass the ability of a "crowd aggregate of competitive forecasters" in making accurate forecasts in the form of answering forecast questions on online platforms such as the Good Judgment Open ([\(https://www.gjopen.com\)]((https://www.gjopen.com))). Two research questions arise: 1) Could a neurosymbolic approach utilizing distilled symbolic knowledge complement or outperform a purely LLM-based solution? 2) Would distilled high-quality structured knowledge provide better explainability and therefore be a more reliable tool as a part of a human-AI collaboration mechanism for event forecasting?

Supplemental Material Statement: Our supplementary material (included as a zip file in our submission) includes code and the prompts used for event sequence generation and benchmarking, as well as the base KG, and sample output files. README.md has all the details. Appendix.pdf contains our prompts and human evaluation details.

## References

- <span id="page-15-9"></span>1. Agrawal, S., Zhou, C., Lewis, M., Zettlemoyer, L., Ghazvininejad, M.: In-context examples selection for machine translation. In: Findings of the Association for Computational Linguistics: ACL 2023. pp. 8857–8873. Association for Computational Linguistics, Toronto, Canada (Jul 2023). [https://doi.org/10.18653/v1/](https://doi.org/10.18653/v1/2023.findings-acl.564) [2023.findings-acl.564](https://doi.org/10.18653/v1/2023.findings-acl.564), <https://aclanthology.org/2023.findings-acl.564>
- <span id="page-15-1"></span>2. Allan, J.: Topic Detection and Tracking: Event-Based Information Organization. Springer Publishing Company, Incorporated (2012)
- <span id="page-15-5"></span>3. Allan, J., Carbonell, J.G., Doddington, G., Yamron, J., Yang, Y.: Topic Detection and Tracking Pilot Study Final Report. In: Proceedings of the DARPA Broadcast News Transcription and Understanding Workshop, February, 1998. (1 1998). <https://doi.org/10.1184/R1/6626252.v1>
- <span id="page-15-8"></span>4. An, S., Lin, Z., Fu, Q., Chen, B., Zheng, N., Lou, J.G., Zhang, D.: How do incontext examples affect compositional generalization? In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 11027–11052. Association for Computational Linguistics, Toronto, Canada (Jul 2023). <https://doi.org/10.18653/v1/2023.acl-long.618>, [https:](https://aclanthology.org/2023.acl-long.618) [//aclanthology.org/2023.acl-long.618](https://aclanthology.org/2023.acl-long.618)
- <span id="page-15-6"></span>5. Begleiter, R., El-Yaniv, R., Yona, G.: On prediction using variable order markov models. J. Artif. Intell. Res. 22, 385–421 (2004). [https://doi.org/10.1613/jair.](https://doi.org/10.1613/jair.1491) [1491](https://doi.org/10.1613/jair.1491), <https://doi.org/10.1613/jair.1491>
- <span id="page-15-7"></span>6. Bhattacharjya, D., Sihag, S., Hassanzadeh, O., Bialik, L.: Summary markov models for event sequences. In: Raedt, L.D. (ed.) Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence, IJCAI-22. pp. 4836–4842. International Joint Conferences on Artificial Intelligence Organization (7 2022). <https://doi.org/10.24963/ijcai.2022/670>, [https://doi.org/](https://doi.org/10.24963/ijcai.2022/670) [10.24963/ijcai.2022/670](https://doi.org/10.24963/ijcai.2022/670), main Track
- <span id="page-15-2"></span>7. Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J.D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., Agarwal, S., Herbert-Voss, A., Krueger, G., Henighan, T., Child, R., Ramesh, A., Ziegler, D., Wu, J., Winter, C., Hesse, C., Chen, M., Sigler, E., Litwin, M., Gray, S., Chess, B., Clark, J., Berner, C., McCandlish, S., Radford, A., Sutskever, I., Amodei, D.: Language models are few-shot learners. In: Larochelle, H., Ranzato, M., Hadsell, R., Balcan, M., Lin, H. (eds.) Advances in Neural Information Processing Systems. vol. 33, pp. 1877–1901. Curran Associates, Inc. (2020), [https://proceedings.neurips.cc/paper\\_files/](https://proceedings.neurips.cc/paper_files/paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf) [paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf](https://proceedings.neurips.cc/paper_files/paper/2020/file/1457c0d6bfcb4967418bfb8ac142f64a-Paper.pdf)
- <span id="page-15-0"></span>8. Cekinel, R.F., Karagoz, P.: Event prediction from news text using subgraph embedding and graph sequence mining. World Wide Web 25(6), 2403–2428 (2022), <https://doi.org/10.1007/s11280-021-01002-1>
- <span id="page-15-4"></span>9. Chen, M., Zhang, H., Ning, Q., Li, M., Ji, H., McKeown, K., Roth, D.: Eventcentric natural language processing. In: ACL (2021)
- <span id="page-15-10"></span>10. Chiang, C.H., Lee, H.y.: Can large language models be an alternative to human evaluations? In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 15607–15631. Association for Computational Linguistics, Toronto, Canada (Jul 2023). [https://doi.org/10.](https://doi.org/10.18653/v1/2023.acl-long.870) [18653/v1/2023.acl-long.870](https://doi.org/10.18653/v1/2023.acl-long.870), <https://aclanthology.org/2023.acl-long.870>
- <span id="page-15-3"></span>11. Chung, H.W., Hou, L., Longpre, S., Zoph, B., Tay, Y., Fedus, W., Li, Y., Wang, X., Dehghani, M., Brahma, S., Webson, A., Gu, S.S., Dai, Z., Suzgun, M., Chen, X., Chowdhery, A., Castro-Ros, A., Pellat, M., Robinson, K., Valter, D., Narang,

S., Mishra, G., Yu, A., Zhao, V., Huang, Y., Dai, A., Yu, H., Petrov, S., Chi, E.H., Dean, J., Devlin, J., Roberts, A., Zhou, D., Le, Q.V., Wei, J.: Scaling instructionfinetuned language models (2022)

- <span id="page-16-7"></span>12. Devlin, J., Chang, M.W., Lee, K., Toutanova, K.: BERT: Pre-training of deep bidirectional transformers for language understanding. In: Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers). pp. 4171–4186. Association for Computational Linguistics, Minneapolis, Minnesota (Jun 2019). <https://doi.org/10.18653/v1/N19-1423>, [https://aclanthology.](https://aclanthology.org/N19-1423) [org/N19-1423](https://aclanthology.org/N19-1423)
- <span id="page-16-0"></span>13. Du, X., Zhang, Z., Li, S., Yu, P., Wang, H., Lai, T., Lin, X., Wang, Z., Liu, I., Zhou, B., Wen, H., Li, M., Hannan, D., Lei, J., Kim, H., Dror, R., Wang, H., Regan, M., Zeng, Q., Lyu, Q., Yu, C., Edwards, C., Jin, X., Jiao, Y., Kazeminejad, G., Wang, Z., Callison-Burch, C., Bansal, M., Vondrick, C., Han, J., Roth, D., Chang, S.F., Palmer, M., Ji, H.: RESIN-11: Schema-guided event prediction for 11 newsworthy scenarios. In: Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies: System Demonstrations. pp. 54–63. Association for Computational Linguistics, Hybrid: Seattle, Washington + Online (Jul 2022). [https://doi.org/10.18653/v1/](https://doi.org/10.18653/v1/2022.naacl-demo.7) [2022.naacl-demo.7](https://doi.org/10.18653/v1/2022.naacl-demo.7), <https://aclanthology.org/2022.naacl-demo.7>
- <span id="page-16-4"></span>14. Filatova, E., Hatzivassiloglou, V., McKeown, K.: Automatic creation of domain templates. In: Proceedings of the COLING/ACL 2006 Main Conference Poster Sessions. pp. 207–214. Association for Computational Linguistics, Sydney, Australia (Jul 2006), <https://aclanthology.org/P06-2027>
- <span id="page-16-5"></span>15. Fournier-Viger, P., Lin, J.C.W., Kiran, R.U., Koh, Y.S.: A survey of sequential pattern mining. Data Science and Pattern Recognition 1(1), 54–77 (2017)
- <span id="page-16-2"></span>16. Gholipour Ghalandari, D., Ifrim, G.: Examining the state-of-the-art in news timeline summarization. In: Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics. pp. 1322–1334. Association for Computational Linguistics, Online (Jul 2020). <https://doi.org/10.18653/v1/2020.acl-main.122>, <https://aclanthology.org/2020.acl-main.122>
- <span id="page-16-10"></span>17. Halawi, D., Zhang, F., Yueh-Han, C., Steinhardt, J.: Approaching human-level forecasting with language models (2024)
- <span id="page-16-1"></span>18. Hassanzadeh, O., Awasthy, P., Barker, K., Bhardwaj, O., Bhattacharjya, D., Feblowitz, M., Martie, L., Ni, J., Srinivas, K., Yip, L.: Knowledge-based news event analysis and forecasting toolkit. In: Proceedings of the Thirty-First International Joint Conference on Artificial Intelligence, IJCAI 2022, Vienna, Austria, 23- 29 July 2022. pp. 5904–5907. ijcai.org (2022), [https://doi.org/10.24963/ijcai.](https://doi.org/10.24963/ijcai.2022/850) [2022/850](https://doi.org/10.24963/ijcai.2022/850)
- <span id="page-16-9"></span>19. He, X., Lin, Z., Gong, Y., Jin, A.L., Zhang, H., Lin, C., Jiao, J., Yiu, S.M., Duan, N., Chen, W.: Annollm: Making large language models to be better crowdsourced annotators (2023)
- <span id="page-16-6"></span>20. Hochreiter, S., Schmidhuber, J.: Long short-term memory. Neural Comput. 9(8), 1735–1780 (nov 1997). <https://doi.org/10.1162/neco.1997.9.8.1735>, [https:](https://doi.org/10.1162/neco.1997.9.8.1735) [//doi.org/10.1162/neco.1997.9.8.1735](https://doi.org/10.1162/neco.1997.9.8.1735)
- <span id="page-16-8"></span>21. Hwang, J.D., Bhagavatula, C., Le Bras, R., Da, J., Sakaguchi, K., Bosselut, A., Choi, Y.: Comet-atomic 2020: On symbolic and neural commonsense knowledge graphs. In: AAAI (2021)
- <span id="page-16-3"></span>22. Imani, S., Du, L., Shrivastava, H.: MathPrompter: Mathematical reasoning using large language models. In: Proceedings of the 61st Annual Meeting of the

Association for Computational Linguistics (Volume 5: Industry Track). pp. 37– 42. Association for Computational Linguistics, Toronto, Canada (Jul 2023). <https://doi.org/10.18653/v1/2023.acl-industry.4>, [https://aclanthology.](https://aclanthology.org/2023.acl-industry.4) [org/2023.acl-industry.4](https://aclanthology.org/2023.acl-industry.4)

- <span id="page-17-4"></span>23. Kamalloo, E., Dziri, N., Clarke, C., Rafiei, D.: Evaluating open-domain question answering in the era of large language models. In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 5591–5606. Association for Computational Linguistics, Toronto, Canada (Jul 2023). <https://doi.org/10.18653/v1/2023.acl-long.307>, [https:](https://aclanthology.org/2023.acl-long.307) [//aclanthology.org/2023.acl-long.307](https://aclanthology.org/2023.acl-long.307)
- <span id="page-17-5"></span>24. Li, M., Zeng, Q., Lin, Y., Cho, K., Ji, H., May, J., Chambers, N., Voss, C.: Connecting the dots: Event graph schema induction with path language modeling. In: Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP). pp. 684–695. Association for Computational Linguistics, Online (Nov 2020). <https://doi.org/10.18653/v1/2020.emnlp-main.50>, <https://aclanthology.org/2020.emnlp-main.50>
- <span id="page-17-10"></span>25. Li, S., Zhao, R., Li, M., Ji, H., Callison-Burch, C., Han, J.: Open-domain hierarchical event schema induction by incremental prompting and verification. In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 5677–5697. Association for Computational Linguistics, Toronto, Canada (Jul 2023). [https://doi.org/10.18653/v1/2023.](https://doi.org/10.18653/v1/2023.acl-long.312) [acl-long.312](https://doi.org/10.18653/v1/2023.acl-long.312), <https://aclanthology.org/2023.acl-long.312>
- <span id="page-17-7"></span>26. Mabroukeh, N.R., Ezeife, C.I.: A taxonomy of sequential pattern mining algorithms. ACM Comput. Surv. 43(1) (dec 2010). [https://doi.org/10.1145/](https://doi.org/10.1145/1824795.1824798) [1824795.1824798](https://doi.org/10.1145/1824795.1824798), <https://doi.org/10.1145/1824795.1824798>
- <span id="page-17-6"></span>27. Mannila, H., Toivonen, H., Verkamo, A.I.: Discovery of frequent episodes in event sequences. Data Mining and Knowledge Discovery 1, 259–289 (1997)
- <span id="page-17-8"></span>28. Mooney, C.H., Roddick, J.F.: Sequential pattern mining – approaches and algorithms. ACM Comput. Surv. 45(2) (mar 2013), [https://doi.org/10.1145/](https://doi.org/10.1145/2431211.2431218) [2431211.2431218](https://doi.org/10.1145/2431211.2431218)
- <span id="page-17-1"></span>29. Norambuena, B.K., Mitra, T., North, C.: A survey on event-based news narrative extraction. ACM Comput. Surv. 55(14s) (jul 2023). [https://doi.org/10.1145/](https://doi.org/10.1145/3584741) [3584741](https://doi.org/10.1145/3584741)
- <span id="page-17-0"></span>30. Radinsky, K., Davidovich, S., Markovitch, S.: Learning causality for news events prediction. In: Proceedings of the 21st World Wide Web Conference 2012, WWW 2012, Lyon, France, April 16-20, 2012. pp. 909–918. ACM (2012), [https://doi.](https://doi.org/10.1145/2187836.2187958) [org/10.1145/2187836.2187958](https://doi.org/10.1145/2187836.2187958)
- <span id="page-17-3"></span>31. Raffel, C., Shazeer, N., Roberts, A., Lee, K., Narang, S., Matena, M., Zhou, Y., Li, W., Liu, P.J.: Exploring the limits of transfer learning with a unified text-to-text transformer. J. Mach. Learn. Res. 21(1) (jan 2020)
- <span id="page-17-9"></span>32. Raftery, A.: A model for high-order Markov chains. Journal of the Royal Statistical Society, Series B 47(3), 528–539 (1985)
- <span id="page-17-2"></span>33. Santana, B.S., Campos, R., Amorim, E., Jorge, A., Silvano, P., Nunes, S.: A survey on narrative extraction from textual data. Artif. Intell. Rev. 56(8), 8393–8435 (2023). <https://doi.org/10.1007/s10462-022-10338-7>
- <span id="page-17-11"></span>34. Srikant, R., Agrawal, R.: Mining sequential patterns: Generalizations and performance improvements. In: Apers, P., Bouzeghoub, M., Gardarin, G. (eds.) Advances in Database Technology — EDBT '96. pp. 1–17. Springer Berlin Heidelberg, Berlin, Heidelberg (1996)

- <span id="page-18-10"></span>35. Touvron, H., Lavril, T., Izacard, G., Martinet, X., Lachaux, M.A., Lacroix, T., Rozière, B., Goyal, N., Hambro, E., Azhar, F., et al.: Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971 (2023)
- <span id="page-18-1"></span>36. Vrandečić, D., Krötzsch, M.: Wikidata: A free collaborative knowledgebase. Commun. ACM 57(10), 78–85 (sep 2014). <https://doi.org/10.1145/2629489>, [https:](https://doi.org/10.1145/2629489) [//doi.org/10.1145/2629489](https://doi.org/10.1145/2629489)
- <span id="page-18-7"></span>37. Wadhwa, S., Amir, S., Wallace, B.: Revisiting relation extraction in the era of large language models. In: Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers). pp. 15566–15589. Association for Computational Linguistics, Toronto, Canada (Jul 2023). [https://doi.org/10.](https://doi.org/10.18653/v1/2023.acl-long.868) [18653/v1/2023.acl-long.868](https://doi.org/10.18653/v1/2023.acl-long.868), <https://aclanthology.org/2023.acl-long.868>
- <span id="page-18-0"></span>38. Wei, J., Bosma, M., Zhao, V., Guu, K., Yu, A.W., Lester, B., Du, N., Dai, A.M., Le, Q.V.: Finetuned language models are zero-shot learners. In: International Conference on Learning Representations (2022), [https://openreview.net/forum?id=](https://openreview.net/forum?id=gEZrGCozdqR) [gEZrGCozdqR](https://openreview.net/forum?id=gEZrGCozdqR)
- <span id="page-18-3"></span>39. West, P., Bhagavatula, C., Hessel, J., Hwang, J., Jiang, L., Le Bras, R., Lu, X., Welleck, S., Choi, Y.: Symbolic knowledge distillation: from general language models to commonsense models. In: Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies. pp. 4602–4625. Association for Computational Linguistics, Seattle, United States (Jul 2022). [https://doi.org/10.18653/v1/2022.](https://doi.org/10.18653/v1/2022.naacl-main.341) [naacl-main.341](https://doi.org/10.18653/v1/2022.naacl-main.341), <https://aclanthology.org/2022.naacl-main.341>
- <span id="page-18-9"></span>40. Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., Cistac, P., Rault, T., Louf, R., Funtowicz, M., Davison, J., Shleifer, S., von Platen, P., Ma, C., Jernite, Y., Plu, J., Xu, C., Le Scao, T., Gugger, S., Drame, M., Lhoest, Q., Rush, A.: Transformers: State-of-the-art natural language processing. In: Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations. pp. 38–45. Association for Computational Linguistics, Online (Oct 2020). <https://doi.org/10.18653/v1/2020.emnlp-demos.6>, [https:](https://aclanthology.org/2020.emnlp-demos.6) [//aclanthology.org/2020.emnlp-demos.6](https://aclanthology.org/2020.emnlp-demos.6)
- <span id="page-18-5"></span>41. Xiang, W., Wang, B.: A survey of event extraction from text. IEEE Access 7, 173111–173137 (2019). <https://doi.org/10.1109/ACCESS.2019.2956831>
- <span id="page-18-2"></span>42. Yu, W., Zhu, C., Li, Z., Hu, Z., Wang, Q., Ji, H., Jiang, M.: A survey of knowledgeenhanced text generation. ACM Comput. Surv. 54(11s) (nov 2022). [https://doi.](https://doi.org/10.1145/3512467) [org/10.1145/3512467](https://doi.org/10.1145/3512467), <https://doi.org/10.1145/3512467>
- <span id="page-18-11"></span>43. Zaki, M.J.: Spade: An efficient algorithm for mining frequent sequences. Machine Learning 42, 31–60 (2004), [https://api.semanticscholar.org/CorpusID:](https://api.semanticscholar.org/CorpusID:5387869) [5387869](https://api.semanticscholar.org/CorpusID:5387869)
- <span id="page-18-6"></span>44. Zhang, Y., Feng, S., Tan, C.: Active example selection for in-context learning. In: Proceedings of the 2022 Conference on Empirical Methods in Natural Language Processing. pp. 9134–9148. Association for Computational Linguistics, Abu Dhabi, United Arab Emirates (Dec 2022). [https://doi.org/10.18653/v1/2022.](https://doi.org/10.18653/v1/2022.emnlp-main.622) [emnlp-main.622](https://doi.org/10.18653/v1/2022.emnlp-main.622), <https://aclanthology.org/2022.emnlp-main.622>
- <span id="page-18-4"></span>45. Zhao, L.: Event prediction in the big data era: A systematic survey. ACM Comput. Surv. 54(5) (may 2021). <https://doi.org/10.1145/3450287>, [https://doi.org/](https://doi.org/10.1145/3450287) [10.1145/3450287](https://doi.org/10.1145/3450287)
- <span id="page-18-8"></span>46. Zhao, M., Mi, F., Wang, Y., Li, M., Jiang, X., Liu, Q., Schuetze, H.: LMTurk: Fewshot learners as crowdsourcing workers in a language-model-as-a-service framework. In: Findings of the Association for Computational Linguistics: NAACL 2022. pp. 675–692. Association for Computational Linguistics, Seattle, United States

(Jul 2022). <https://doi.org/10.18653/v1/2022.findings-naacl.51>, [https://](https://aclanthology.org/2022.findings-naacl.51) [aclanthology.org/2022.findings-naacl.51](https://aclanthology.org/2022.findings-naacl.51)

<span id="page-19-0"></span>47. Zheng, L., Chiang, W.L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E., Stoica, I.: Judging llm-as-a-judge with mt-bench and chatbot arena (2023)

## Appendix

This section constitutes technical appendix (i.e. supplementary material) for the submission titled "Distilling Event Sequences from Large Language Models".

## 7 Event Sequence Prompts

We now describe the specific prompt-types used (including pseudo-code for their use) to generate event sequences given individual Wikidata event concepts. We start a Wikidata event concept label and feed it into the following prompt with 3 ICL exemplars. The prompt also includes a label space of other Wikidata concepts from which we i nstruct the model to choose a concept. In case of an outof-domain generated output (≈ 15% of total outputs), we discard those outputs.

```
1 def build_prompt1 ( vocab , target_label ) :
2 prompt = "Use the following vocabulary to respond to the
     questions : " + \
3 f"{ ' '. join ( label_space )}\n" + \
4 f" Question : what usually happens after earthquake
     ?\n" +\
5 f" Answer : tsunami \n" + \
6
7 f" Question : what usually happens after economic
     crises ?\n" +\
8 f" Answer : unemployment \n" + \
9
10 f" Question : what usually happens after bomb attack
     ?\n" +\
11 f" Answer : injury \n" + \
12
13 f" Question : what usually happens after {
     target_label }?\n" +\
14 f" Answer :"
15
16 return prompt
```

#### Listing 1.1. Initial Trigger Prompt

Following the output from the above prompt trigger, we feed the in-domain outputs to the following ICL iterative prompt with conjunctive event exemplars (i.e. X and Y). We then successively use this prompt by feeding model generated outputs as new event concepts. Restricting the generated vocabulary to existing Wikidata concepts allows for a reasonable recall evaluation even from a sparse reference set. We illustrate this approach in Figure [2](#page-5-0) in the main paper.

```
1 def build_prompt2 ( vocab , target_labels ) :
```

2

```
22 Wadhwa et al.
```

```
3 prompt = "Use the following vocabulary to respond to the
     questions : " + \
4 f"{ ' '. join ( label_space )}\n" + \
5 f" Question : what usually happens after earthquake
     ?\n" +\
6 f" Answer : tsunami \n" + \
7
8 f" Question : what usually happens after earthquake
     and tsunami ?\n" +\
9 f" Answer : nuclear disaster \n" + \
10
11 f" Question : what usually happens after economic
     crises and wage decline and unemployment ?\n" +\
12 f" Answer : legislation \n" + \
13
14 f" Question : what usually happens after military
     conflict ?\n" +\
15 f" Answer : war \n" + \
16
17 f" Question : what usually happens after military
     conflict and war ?\n" +\
18 f" Answer : peace treaty \n" + \
19
20 f" Question : what usually happens after { ' and '.
     join ( target_labels )}?\n" +\
21 f" Answer :"
22
23 return prompt
```

Listing 1.2. Iterative ICL Prompt with Conjunctive Examples

## 8 Evaluator Models (Example Outputs and Prompts)

For a model generated event sequence α = a1, a2, .., an, we consider all possible pairs of events (a<sup>i</sup> , ai+1) as (trigger, consequence) pairs where a<sup>0</sup> is the initial trigger sequence and i ∈ 1, .., n are all events generated by the model that follow a0. Then we use the following prompt to evaluate correctness of all such possible pairs and use this as proxy for a true precision evaluation of the generated sequences.

```
1 def build_precision_eval ( trigger , consequence ) :
2 prompt = " Respond to the questions below with a ( YES/NO)
     with a historical example :" + \
3 f" Question : Can economic crises cause a landslide
     ?\n" +\
4 f" Answer : NO. There is no historical example of
     an economic crisis causing a landslide , which is natural
     disaster .\n" + \
```

Distilling Event Sequence Knowledge From Large Language Models 23

| r<br>о<br>ı |  |
|-------------|--|
|             |  |
|             |  |

<span id="page-22-0"></span>Fig. 3. Annotation interface for classifying model generated response vs reference (anonymized) for the ATOMIC event descriptions.

| 5  | f" Question :<br>Can<br>earthquake<br>cause<br>a<br>tsunami ?\n"<br>+\                |
|----|---------------------------------------------------------------------------------------|
| 6  | f" Answer :<br>YES.<br>In<br>2011 ,<br>Japan<br>experienced<br>an                     |
|    | earthquake<br>in<br>tohoku<br>that<br>caused<br>a<br>tsunami .<br>\n"<br>+<br>\       |
| 7  | f" Question :<br>Can<br>mass<br>shooting<br>cause<br>a                                |
|    | condensation<br>cloud ?\n"<br>+\                                                      |
| 8  | f" Answer :<br>NO.<br>A<br>condensation<br>cloud<br>is<br>a<br>weather                |
|    | phenomenon ,<br>not<br>a<br>mass<br>shooting .\n"<br>+<br>\                           |
| 9  | f" Question :<br>Can<br>accident<br>cause<br>a<br>stock<br>market                     |
|    | crash ?\n"<br>+\                                                                      |
| 10 | f" Answer :<br>NO.<br>The<br>stock<br>market<br>crash<br>of<br>1929<br>was            |
|    | caused<br>by<br>a<br>series<br>of<br>events ,<br>not<br>an<br>accident .\n"<br>+<br>\ |
| 11 | f" Question :<br>Can<br>disease<br>outbreak<br>cause<br>a                             |
|    | inventory<br>shrinkage ?\n"<br>+\                                                     |
| 12 | f" Answer :<br>YES.<br>The<br>bubonic<br>plague<br>outbreak<br>in                     |
|    | Europe<br>in<br>1348<br>caused<br>a<br>massive<br>inventory<br>shrinkage .\n"<br>+    |
|    | \                                                                                     |
| 13 | f" Question :<br>Can<br>fraud<br>cause<br>a<br>travel<br>ban ?\n"<br>+\               |
| 14 | f" Answer :<br>YES.<br>Travel<br>bans<br>are<br>a<br>form<br>of                       |
|    | punishment<br>for<br>immigration<br>fraud .\n"<br>+<br>\                              |
| 15 | f" Question :<br>Can<br>{ trigger }<br>cause<br>a<br>{ consequence }?\                |
|    | n"<br>+<br>" Answer :<br>"                                                            |
| 16 | return<br>prompt                                                                      |
|    |                                                                                       |

Listing 1.3. Prompt used to evaluate correctness of a given event pair

As mentioned in the limitations section, a key shortcoming of our approach here is that we do not evaluate the correctness of the post-hoc explanations

generated by the model for it's classification label. We leave that analysis for future work.

## 9 ATOMIC Human Evaluations

Amazon Mechanical Turk (AMT) is a platform for non-expert works to perform microtasks, in our case – human annotations. Three authors with graduate degrees in computer science carried out these human evaluations. Figure [3](#page-22-0) shows the interface provided to these human annotators. As described in the main paper, human evaluators were asked to answer the following questions–

- Are both responses functionally similar?
- Which response do you prefer?
- Which response, if any, is completely irrelevant?

Functionally Similar Responses For responses to be functionally similar, they must convey the same meaning even if there is major lexical mismatch between the actual tokens.

Human Preferences The preferences elicited here are based on a humans degree of reasonableness given an event trigger. We observed a high Fleiss κ = 0.81 indiciating a high degree of agreement between the annotators.

Irrelevant Responses Here, again the annotators were asked to exercise judgment in what they may find a completely unreasonable response to a given event trigger.

We release the results from these human annotations for a comprehensive analysis and any additional findings that readers may infer.