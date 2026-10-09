# <span id="page-0-1"></span>Autoregressive Structured Prediction with Language Models

Tianyu Liu<sup>ζ</sup> Yuchen Eleanor Jiang<sup>ζ</sup> Nicholas Monath<sup>γ</sup> Ryan Cotterell<sup>ζ</sup> Mrinmaya Sachan<sup>ζ</sup>

<sup>ζ</sup>ETH Zürich <sup>γ</sup>Google Research

{[tianyu.liu,](mailto:tianyu.liu@inf.ethz.ch) [yuchen.jiang](mailto:yuchen.jiang@inf.ethz.ch)}@inf.ethz.ch

[nmonath@google.com](mailto:nmonath@google.com) {[ryan.cotterell,](mailto:ryan.cotterell@inf.ethz.ch) [mrinmaya.sachan](mailto:mrinmaya.sachan@inf.ethz.ch)}@inf.ethz.ch

# Abstract

In recent years, NLP has moved towards the application of language models to a more diverse set of tasks. However, applying language models to structured prediction, e.g., predicting parse trees, taggings, and coreference chains, is not straightforward. Prior work on language model-based structured prediction typically flattens the target structure into a string to easily fit it into the language modeling framework. Such flattening limits the accessibility of structural information and can lead to inferior performance compared to approaches that overtly model the structure. In this work, we propose to construct a conditional language model over sequences of structure-building actions, rather than over strings in a way that makes it easier for the model to pick up on intra-structure dependencies. Our method sets the new state of the art on named entity recognition, end-to-end relation extraction, and coreference resolution.

<https://github.com/lyutyuh/ASP>

# 1 Introduction

Many common NLP tasks, e.g., named entity recognition, relation extraction, and coreference resolution are naturally taxonomized as structured prediction, the supervised machine-learning task of predicting a structure from a large[1](#page-0-0) set. To generalize well to held-out data in a structured prediction problem, the received wisdom has been that it is necessary to correctly model complex dependencies between different pieces of the structure. However, a recent trend in structured prediction for language has been to forgo explicitly modeling such dependencies [\(Ma and Hovy,](#page-7-0) [2016;](#page-7-0) [Lee et al.,](#page-6-0) [2017;](#page-6-0) [He et al.,](#page-6-1) [2017,](#page-6-1) *inter alia*), and, instead, to apply an expressive black-box model, e.g., a neural network, with the hope that the model picks up on the dependencies without explicit instruction.

Framing structured prediction as conditional language modeling is an increasingly common black-box technique for building structured predictors that has led to empirical success [\(Vinyals et al.,](#page-7-1) [2015;](#page-7-1) [Raffel et al.,](#page-7-2) [2020;](#page-7-2) [Athiwaratkun et al.,](#page-5-0) [2020;](#page-5-0) [De Cao et al.,](#page-5-1) [2021;](#page-5-1) [Paolini et al.,](#page-7-3) [2021,](#page-7-3) *inter alia*). The idea behind the framework is to encode the target structure as a string, flattening out the structure. Then, one uses a conditional language model to predict the flattened string encoding the structure. For instance, [Vinyals et al.](#page-7-1) [\(2015\)](#page-7-1) flatten parse trees into strings and predict the strings encoding the flattened trees from the sentence with a machine translation architecture. The hope is that the autoregressive nature of the language model allows it to *learn* to model the intra-structure dependencies and the necessary hard constraints that ensure the model even produces well-formed structures. Additionally, many modelers make use of pre-trained language models [\(Lewis et al.,](#page-6-2) [2020;](#page-6-2) [Raffel et al.,](#page-7-2) [2020\)](#page-7-2) to further improve the language models.

However, despite their empirical success, simply hoping that a black-box approach correctly models intricate intra-structure dependencies is often insufficient for highly structured tasks [\(Paolini](#page-7-3) [et al.,](#page-7-3) [2021,](#page-7-3) §1). Indeed, the act of flattening a structured object into a string makes properly modeling the intra-structure dependencies harder for many tasks, e.g., those that involve nested spans or long-distance dependencies. For instance, in coreference resolution, a conference link between two mentions can stretch across thousands of words, and a coreference chain can also contain over a hundred mentions [\(Pradhan et al.,](#page-7-4) [2012\)](#page-7-4). Flattening such a large amount of structured information into a string makes the task more difficult to model.

In this paper, we propose a simple framework that augments a conditional language model with explicit modeling of structure. Instead of modeling strings that encode a flattened representation of the target structure, we model a constrained set of actions that build the target structure step by step; see Fig. [1](#page-1-0) for an example of our proposed

<span id="page-0-0"></span><sup>1</sup>Typically, large means exponential in the size of the input.

<span id="page-1-0"></span>Figure 1: Illustration of the target outputs of our framework on coreference resolution (COREF) and end-to-end relation extraction (ERE). The lower part illustrates the decoding process of our model. The actions  $y_i$  are color-coded as  $\Box$ ,  $\Box$  and  $\Box$ ,  $\Box$  and  $\Box$ . The structure random variables  $z_i$  are presented along with coreference links or relation links. We present words in the  $\Box$  copy cells merely as an illustration.

framework. Training a conditional language model to predict structure-building actions exposes the structure in a way that allows the model to pick up on the intra-structure dependencies more easily while still allowing the modeler to leverage pretrained language models. We conduct experiments on three structured prediction tasks: named entity recognition, end-to-end relation extraction, and coreference resolution. On each task, we achieve state-of-the-art results *without* relying on data augmentation or task-specific feature engineering.

#### 2 Autoregressive Structured Prediction

In this section, we describe our proposed approach, which we refer to as **autoregressive structured prediction** (ASP). Unlike previous approaches for structured prediction based on conditional language modeling, we represent structures as sequences of **actions**, which build pieces of the target structure step by step. For instance, in the task of coreference resolution, the actions build spans as well as the relations between the spans, contiguous sequences of tokens. We give an example in Fig. 1.

#### 2.1 Representing Structures with Actions

While our approach to structured prediction, ASP, is quite general, our paper narrowly focuses on modeling structures that are expressible as a set of dependent spans, and we couch the technical exposition in terms of modeling spans and relationships among spans. Our goal is to predict an action sequence  $\mathbf{y} = y_1, \dots, y_N$ , where each action  $y_n$  is chosen from an **action space**  $\mathcal{Y}_n$ . In this work, we take  $\mathcal{Y}_n$  to be factored, i.e.,  $\mathcal{Y}_n \stackrel{\text{def}}{=} \mathcal{A} \times \mathcal{B}_n \times \mathcal{Z}_n$ , where  $\mathcal{A}$  is a set of structure-building actions,  $\mathcal{B}_n$  is the set of bracket-pairing actions, and  $\mathcal{Z}_n$  is a

set of span-labeling actions. Thus, each  $y_n$  may be expressed as a triple, i.e.,  $y_n = \langle a_n, b_n, z_n \rangle$ . We discuss each set in a separate paragraph below.

**Structure-Building** Actions. We first deset structure-building  $A = \{ 1, [*, copy] \}$  that allow us to encode the span structure of a text, e.g., [\* Delaware ] in Fig. 1 encodes that *Delaware* is a span of interest. More technically, the action 1 refers to a right bracket that marks the right-most part of a span. The action [\* refers to a left bracket that marks the left-most part of a span. The superscript \* on [\* is inspired by the Kleene star and indicates that it is a placeholder for 0 or more consecutive left brackets<sup>2</sup>. Finally, copy refers to copying a word from the input document. To see how these actions come together to form a span, consider the subsequence in Fig. 1, [\* Delaware], which is generated from a sequence of structure-building actions [\*, copy, and ].

**Bracket-Pairing Actions.** Next, we develop the set of actions that allow the model to match left and right brackets; we term these bracket-pairing actions. The set of bracket-pairing actions consists of all previously constructed left brackets, i.e.,

$$\mathcal{B}_n = \left\{ m \mid m < n \land a_m = \boxed{\complement^*} \right\} \tag{1}$$

Thus, in general,  $|\mathcal{B}_n|$  is  $\mathcal{O}(n)$ . However, it is often the case that domain-specific knowledge can

<span id="page-1-1"></span><sup>&</sup>lt;sup>2</sup>In our preliminary experiments, we observe unsatisfactory performance when the model has to generate consecutive left brackets. We leverage [↑ as an engineering workaround. We hypothesize that this phenomenon is due to the inability of transformers to recognize Dyck languages (Hahn, 2020; Hao et al., 2022).

be used to prune  $\mathcal{B}_n$ . For instance, coreference mentions and named entities rarely cross sentence boundaries, which yields a linguistically motivated pruning strategy (Liu et al., 2022). Thus, in some cases, the cardinality of  $\mathcal{B}_n$  can be significantly smaller. When we decode action sequences y into a structure, unpaired [ \* ] and [ ] can be removed ensuring that the output of the model will not contain unpaired brackets.

**Span-Labeling Actions.** Finally, we add additional symbols  $z_n$  associated with each  $y_n$  that encode a labeling of a single span or a relationship between two or more spans. For instance, see §2.3 for an example. We denote the set of all  $z_n$  as

$$\mathcal{Z}_n = \left\{ m \mid m < n \land a_m = 1 \right\} \times \mathcal{L} \qquad (2)$$

where  $\{m \mid m < n \land a_m = \square\}$  is the set of previous spans, which allows the model to capture intra-span relationships, and  $\mathcal{L}$  denotes the set of possible labelings of the current span and the relationship between the adjoined spans. In general, designing  $\mathcal{Z}_n$  requires some task-specific knowledge in order to specify the label space. However, we contend it requires less effort than designing a flattened string output where different levels of structures may be intertwined (Paolini et al., 2021).

#### 2.2 Model Parameterization

Let  $D = \boldsymbol{w}_1, \dots, \boldsymbol{w}_K$  be an input document of K sentences where  $\boldsymbol{w}_k$  denotes the  $k^{\text{th}}$  sentence in D. We first convert the structure to be built on top of D into an action sequence, which we denote as  $\boldsymbol{y}$  where  $y_n \in \mathcal{Y}_n$ . Now, we model the sequence of actions  $\boldsymbol{y}$  as a conditional language model

$$p_{\boldsymbol{\theta}}(\boldsymbol{y} \mid D) = \prod_{n=1}^{N} p_{\boldsymbol{\theta}}(y_n \mid \boldsymbol{y}_{< n}, D) \qquad (3)$$

The log-likelihood of the model is then given by  $\log p_{\theta}(\boldsymbol{y} \mid D) = \sum_{n=1}^{N} \log p_{\theta}(y_n \mid \boldsymbol{y}_{< n}, D)$ . We model the local conditional probabilities  $p(y_n \mid \boldsymbol{y}_{< n}, D)$  as a softmax over a *dynamic* set  $\mathcal{Y}_n$  that changes as a function of the history  $\boldsymbol{y}_{< n}$ , i.e.,

$$p_{\boldsymbol{\theta}}(y_n \mid \boldsymbol{y}_{< n}, D) = \frac{\exp s_{\boldsymbol{\theta}}(y_n)}{\sum_{y_n' \in \mathcal{Y}_n} \exp s_{\boldsymbol{\theta}}(y_n')}$$
(4)

where  $s_{\theta}$  is a parameterized score function; we discuss several specific instantiations of  $s_{\theta}$  in §2.3. Finally, we note that the use of a dynamic vocabulary stands in contrast to most conditional

language models where the vocabulary is held constant across time steps, e.g., Sutskever et al.'s (2014) approach to machine translation.

**Greedy Decoding.** We determine the approximate best sequence  $y^*$  using a greedy decoding strategy. At decoding step n, we compute

$$y_n^* = \operatorname*{argmax} p_{\boldsymbol{\theta}}(y_n' \mid \boldsymbol{y}_{< n}, D)$$
 (5)

<span id="page-2-2"></span>The chosen  $y_n^* = \langle a_n^*, b_n^*, z_n^* \rangle$  will then be verbalized as a token as follows: If  $a_n^* = \text{copy}$ , then we copy the next token from the input that is not present in the output. Otherwise, if  $y_n^* = \text{$\mathbb{I}$}$  or  $y_n^* = \text{$\mathbb{I}$}$ , we insert  $\text{$\mathbb{I}$}$  or  $\text{$\mathbb{I}$}$  into the output sequence, respectively. The verbalized token is then fed into the conditional language model at the next step. The decoding process terminates when the model copies a distinguished symbol EoS symbol from the input. The end of the procedure yields an approximate argmax  $y^*$ .

Computational Complexity. Eq. (4) can be computed quite efficiently using our framework, as the cardinalities of  $\mathcal{A}$  is  $\mathcal{O}(1)$ , and the size of  $\mathcal{B}_n$  and  $\mathcal{Z}_n$  are both  $\mathcal{O}(n)$ . A tighter analysis says the cardinalities of  $\mathcal{B}_n$  and  $\mathcal{Z}_n$  are roughly linear in the number of spans predicted. In practice, we have  $n \ll |V|$  where |V| is the size of vocabulary, which is the step-wise complexity of (Paolini et al., 2021). A quantitative analysis of the number of mentions in coreference can be found in App. B.

**Generality.** Despite our exposition's focus on tasks that involve assigning labels to span or span pairs, our method is quite general. Indeed, almost any structured prediction task can be encoded by a series of structure-building actions. For tasks that involve labeling tuples of spans, e.g., semantic role labeling makes use of tree-tuples that consist of the subject, predicate, and object, Eq. (2) can be easily extended with a new space of categorical variables  $\left\{m\mid m< n \land a_m= \right\}$  to model the extra item.

#### <span id="page-2-0"></span>2.3 Task-specific Parameterizations

<span id="page-2-1"></span>We now demonstrate how to apply ASP to three language structured prediction tasks: named entity recognition, coreference resolution, and end-to-end relation extraction.

**Named Entity Recognition.** Named entity recognition is the task of labeling all mention spans  $\mathcal{E} = \{e_n\}_{n=1}^{|\mathcal{E}|}$  in a document D that refers to named

entities. Since named entity recognition only requires labeling spans (and not linking them), we only need our task-specific  $z_n$  to encode the entity type, which is canonically taken from a set of pre-defined categories  $\mathcal{C}$ . The function  $s_{\theta}(y_n)$  in Eq. (4) is implemented by a feed-forward network

$$s_{\boldsymbol{\theta}}(y_n = \langle a_n, b_n, z_n \rangle)$$

$$\stackrel{\text{def}}{=} \begin{cases} FFN_{a_n}^{z_n}(\boldsymbol{m}_n) & \text{if } a_n = \\ FFN_{a_n}(\boldsymbol{h}_n) & \text{otherwise} \end{cases}$$

$$(6)$$

where  $h_n$  is the decoder hidden state at step n, a column vector, and  $m_n = [h_n^\top; h_{b_n}^\top]^\top$  represents the mention that corresponds to  $y_n$ . Note that each FFN $_{a_n}^{z_n}$  and FFN $_{a_n}$  represent independent feed-forward networks with no shared parameters.

End-to-End Relation Extraction. End-to-end relation extraction is the task of jointly extracting a set of entities alongside a set of relations between pairs of extracted entities. Formally, given a set of pre-defined entity categories  $\mathcal{C}$  and a set of pre-defined relations  $\mathcal{R}$ . The goal is (i) to identify all possible entities  $\mathcal{E} = \{e_n\}_{n=1}^{|\mathcal{E}|}$  in D that could be associated with one of the entity types c in  $\mathcal{C}$  and (ii) to identify all possible triples  $\mathcal{T} = \{(e_n, r_n, e'_n)\}_{n=1}^{|\mathcal{T}|}$  in D where  $e_n, e'_n \in \mathcal{E}$  are the head and tail entity and  $r_n \in \mathcal{R}$  is the relation between  $e_n$  and  $e'_n$ . Here, the support of  $z_n$  takes the form of Eq. (2), where  $\mathcal{L}$  is instantiated as  $\mathcal{C} \times \mathcal{R}$ . And  $s_{\theta}(y_n)$  kept the same as in Eq. (6).

Coreference Resolution. The task of coreference resolution involves identifying all mention spans  $\mathcal{E} = \{e_n\}_{n=1}^{|\mathcal{E}|}$  in D and then clustering them. However, in addition to identifying the mention spans, the task of coreference resolution requires us to assign an antecedent to every possible mention in D. To encode coreference resolution in our framework, we consider the task-specific  $z_n$  from the set

$$\mathcal{Z}_n = \left\{ m \mid m < n \land a_m = \square \right\} \cup \{\epsilon\} \qquad (7)$$

where we follow the convention set in Lee et al. (2017) that the antecedent of the first mention in each coreference chain is defined to be  $\epsilon$ . Again, we define  $s_{\theta}(y_n = \langle a_n, b_n, z_n \rangle)$  as in Eq. (6) with the exception that, when  $z_n = \epsilon$ , we define  $FFN_{a_n}(\boldsymbol{m}_n)_{\epsilon} = FFN_{a_n}(\boldsymbol{m}_n)$ .

#### 3 Experiments

We experiment on three NLP structured prediction tasks: named entity recognition, end-to-end relation extraction, and coreference resolution. We are

<span id="page-3-1"></span>

|                                 | Prec. | Rec. | F1   |
|---------------------------------|-------|------|------|
| Ma and Hovy (2016)              | 91.4  | 91.1 | 91.2 |
| Devlin et al.+BERT <sub>L</sub> | -     | -    | 92.8 |
| Ye et al.+ROBERTAL              | -     | -    | 94.0 |
| Athiwaratkun et al.             | -     | -    | 91.5 |
| Paolini et al.+T5 <sub>B</sub>  | -     | -    | 91.7 |
| ASP+T5 <sub>B</sub>             | 91.4  | 92.2 | 91.8 |
| $ASP+T5_L$                      | 92.1  | 93.4 | 92.8 |
| $ASP+T5_{3B}$                   | 93.8  | 94.4 | 94.1 |

<span id="page-3-0"></span>Table 1: Test F1 scores of named entity recognition on the CoNLL-03 test set.

primarily interested in understanding whether ASP provides advantages over two existing formalisms: (i) conditional language models (Athiwaratkun et al., 2020; Paolini et al., 2021) that flatten the structure into a string (augmented language models), and (ii) the classic discriminative models whose autoregressivity is bounded. We experiment with three pre-trained language models, T5 (Raffel et al., 2020), T0 (Sanh et al., 2021), and Flan-T5 (Chung et al., 2022) for the three tasks under consideration. Additional experimental details are given in App. A.1 and App. A.2.

#### 3.1 Named Entity Recognition

First, we evaluate our model on the CoNLL-03 English NER task. Following previous work, we report the micro precision, recall, and F1 score. As shown in Tab. 1, our model using T0-3B backbone outperforms all other models without data augmentation or ensembling.

#### 3.2 End-to-End Relation Extraction

We compare ASP on the CoNLL-04 and ACE-05 English end-to-end relation extraction datasets. The results are shown in Tab. 2 and Tab. 3. Our proposed approach achieves state-of-the-art results on both datasets using T5-3B as the backbone. In particular, it outperforms the flattened-string model of Paolini et al. (2021) by a large margin (> 0.9 F1). We hypothesize that this is due to relations requiring higher-order dependencies between spans.

<sup>&</sup>lt;sup>3</sup>Ye et al. (2022) counts symmetric relations twice for evaluation, which is inconsistent with previous work. We report the re-evaluated scores under the standard metric.

<span id="page-3-2"></span><sup>&</sup>lt;sup>4</sup>On ACE-05, we observe inferior performance using T0-3B instead of T5-3B. We suspect this is due to systematic deficiencies in dataset preprocessing, e.g., errors during sentencization and tokenization as well as inconsistent capitalization.

<span id="page-4-0"></span>

|                                                                                                    | Ent                          | Rel                          |
|----------------------------------------------------------------------------------------------------|------------------------------|------------------------------|
| Eberts and Ulges<br>(2020)<br>Zhao et al.<br>(2020)<br>Wang and Lu+ALBERTXXL<br>Paolini et al.+T5B | 88.9<br>88.9<br>90.1<br>89.4 | 71.5<br>71.9<br>73.8<br>71.4 |
| ASP+T5B<br>ASP+T03B                                                                                | 89.5<br>90.3                 | 73.2<br>76.3                 |

Table 2: Micro F1 scores of entity extraction and relation extraction on the CoNLL-04 joint entity relation extraction test set.

<span id="page-4-1"></span>

|                                                                                            | Ent                          | Rel                          | Rel+                      |
|--------------------------------------------------------------------------------------------|------------------------------|------------------------------|---------------------------|
| Wang and Lu+ALBXXL<br>Zhong and Chen+ALBXXL<br>3<br>Ye et al.+ALBXXL<br>Paolini et al.+T5B | 89.5<br>90.9<br>91.1<br>88.9 | 67.6<br>69.4<br>72.4<br>63.7 | 64.3<br>67.0<br>70.3<br>- |
| ASP+T5B<br>ASP+T5L<br>4<br>ASP+T53B                                                        | 90.7<br>91.3<br>91.3         | 71.1<br>71.9<br>72.7         | 68.6<br>69.4<br>70.5      |

Table 3: Test F1 scores of entity and relation extraction on the ACE-05 joint entity relation extraction task.

#### 3.3 Coreference Resolution

We then conduct experiments on the standard OntoNotes benchmark in the CoNLL-12 English shared task dataset [\(Pradhan et al.,](#page-7-4) [2012\)](#page-7-4). Tab. [4](#page-4-2) reports the results. Again, our model achieves stateof-the-art performance among systems without any data augmentation[5](#page-4-3) , outperforming the previous state of the art by 1.5 F1 score. We also observe that our ASP models substantially outperform discriminative models that make use of the same PLM. Further analysis is provided in App. [B.](#page-10-0)

### 4 Related Work

Most similar to our approach is the model of [\(Paolini et al.,](#page-7-3) [2021\)](#page-7-3), which also predicts structures in an iterative manner using conditional language models. Similar approaches exist for constituency parsing [\(Vinyals et al.,](#page-7-1) [2015;](#page-7-1) [Dyer et al.,](#page-6-7) [2016\)](#page-6-7), entity retrieval [\(De Cao et al.,](#page-5-1) [2021\)](#page-5-1), semantic parsing [\(Xiao et al.,](#page-7-9) [2016\)](#page-7-9), slot labeling, and intent classification [\(Athiwaratkun et al.,](#page-5-0) [2020\)](#page-5-0). Earlier work on search-based [\(Daumé et al.,](#page-5-4)

<span id="page-4-2"></span>

|                                                                              | MUC                          | B3                           | CEAFφ4                       | Avg. F1                      |
|------------------------------------------------------------------------------|------------------------------|------------------------------|------------------------------|------------------------------|
| Lee et al. (2017)<br>Joshi et al. (2020)<br>†<br>Joshi et al.+T5B            | 75.8<br>85.3<br>79.8         | 65.0<br>78.1<br>70.2         | 60.8<br>75.3<br>66.8         | 67.2<br>79.6<br>72.3         |
| †<br>Joshi et al.+T5L<br>Urbizu et al.<br>Paolini et al.+T5B<br>Dobrovolskii | 81.4<br>64.9<br>81.0<br>86.3 | 73.1<br>66.5<br>69.0<br>79.9 | 73.1<br>65.3<br>68.4<br>76.6 | 74.9<br>65.6<br>72.8<br>81.0 |
| ASP+T5B<br>ASP+T5L<br>ASP+T03B<br>ASP+FLAN-T5XXL                             | 82.3<br>84.7<br>86.9<br>87.2 | 75.1<br>77.7<br>81.5<br>81.7 | 72.5<br>75.2<br>78.4<br>78.6 | 76.6<br>79.3<br>82.3<br>82.5 |

Table 4: Results on the CoNLL-12 English test set. Avg. F1 denotes the average F1 of MUC, B<sup>3</sup> , and CEAFφ<sup>4</sup> . Models marked with † are our reimplementation. Other results are taken from their original papers. The full results are in Tab. [5.](#page-10-1)

[2009;](#page-5-4) [Doppa et al.,](#page-6-10) [2014;](#page-6-10) [Chang et al.,](#page-5-5) [2015\)](#page-5-5) and greedy-based approaches [\(Swayamdipta et al.,](#page-7-12) [2016\)](#page-7-12) applied to structured prediction also predict the structure in a sequential fashion as we do.Other work such as energy-based models [\(Belanger and](#page-5-6) [McCallum,](#page-5-6) [2016;](#page-5-6) [Tu and Gimpel,](#page-7-13) [2018,](#page-7-13) *inter alia*) and graphical models [\(Durrett and Klein,](#page-6-11) [2014;](#page-6-11) [Ganea and Hofmann,](#page-6-12) [2017\)](#page-6-12) predict structures more holistically.

### 5 Conclusion

In this paper, we propose a novel framework for structured prediction that encodes a structure as a series of structure-building actions that obtains state-of-the-art performance across three tasks. In contrast to past approaches for structured prediction, our approach is compatible with pre-trained large language models. This allows us to reduce structured prediction to the problem of fine-tuning pre-trained language models over an enlarged alphabet. We show empirically that ASP outperforms previous structured prediction models by a large margin. Indeed, we set the new state of the art on three tasks: named entity recognition, end-to-end relation extraction, and coreference resolution.

# Acknowledgements

We acknowledge support from an ETH Zürich Research grant (ETH-19 21-1) and a grant from the Swiss National Science Foundation (project #201009) for this work. We also thank Zeerak Talat and Peter Szemraj for their feedback on this manuscript.

<span id="page-4-3"></span><sup>5</sup>We achieve 82.9 F1 score on the development set, outperforming the result without pretraining on additional data reported by [Wu et al.](#page-7-10) [\(2020,](#page-7-10) Tab. 5). In addition, training our model does not require the usage of TPUs.

# Ethical Considerations

To consider the ethical implications of our work, we consider the tasks and models used and our proposed approach. The tasks considered, named entity recognition, relation extraction, and coreference resolution are often used in a pipeline of approaches (say for automatically building knowledge bases). Understanding the biases, errors, and failure cases of these tasks and their models and how they affect downstream use cases of the knowledge base would be important to consider. That said, to our knowledge the proposed approach does not exacerbate (or lessen) or introduce new considerations to the ones known about tasks/models more generally.

# Limitations

Autoregressive Modeling Assumption. The decoder model, which is autoregressive, introduces an inductive bias on the structured prediction approach. Specifically, the left-to-right approach requires the model to model dependencies in a specific order. This could account for some of the reduction in performance compared to task-specific discriminative models. Understanding the implications of the autoregressive decision is indeed an interesting question, but one that we felt was out of scope for this short paper.

Efficiency. In our experiments, we reduce the burden of finding many mention spans in two-stage approaches. On sentence-level tasks, e.g., entity and relation extraction, the number of decoding steps is relatively small. For instance, the average number of words in an input sentence is ≈20. Our system has a lighter memory trace as opposed to discriminative models. This extra time cost can be partially compensated with larger batch sizes. However, on document-level tasks, e.g., coreference resolution, the number of decoding steps is too large to be compensated with parallelism. More efficient methods for inference such as non-autoregressive decoding [\(Gu et al.,](#page-6-13) [2018\)](#page-6-13) remain to be explored in future work.

Decoding Algorithms. In this work, we use greedy decoding in all the experiments. Alternative decoding algorithms might further improve the quality of the generated sequences, e.g., beam search [\(Zhang and Clark,](#page-8-2) [2008;](#page-8-2) [Goldberg et al.,](#page-6-14) [2013\)](#page-6-14).

Choice of Pretrained Language Models. In this work, the choice of T5 and its variants as the conditional language model backbone of our model is largely motivated by their ability to handle arbitrarily long sequences. Unlike BART and GPT, T5 uses relative position encoding. On document-level tasks such as coreference resolution, the ability to process long sequences is extremely important. However, other pretrained conditional language models, either with encoder–decoder structures or decoder-only structures, can be used as a backbone. It might be interesting to explore techniques that generalize fixed-length position encoding to longer sequences.

### References

<span id="page-5-0"></span>Ben Athiwaratkun, Cicero Nogueira dos Santos, Jason Krone, and Bing Xiang. 2020. [Augmented natu](https://doi.org/10.18653/v1/2020.emnlp-main.27)[ral language for generative sequence labeling.](https://doi.org/10.18653/v1/2020.emnlp-main.27) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 375–385, Online. Association for Computational Linguistics.

<span id="page-5-6"></span>David Belanger and Andrew McCallum. 2016. [Struc](https://dl.acm.org/doi/10.5555/3045390.3045495)[tured prediction energy networks.](https://dl.acm.org/doi/10.5555/3045390.3045495) In *Proceedings of the 33rd International Conference on International Conference on Machine Learning*, page 983–992.

<span id="page-5-5"></span>Kai-Wei Chang, Akshay Krishnamurthy, Alekh Agarwal, Hal Daumé, and John Langford. 2015. [Learn](http://proceedings.mlr.press/v37/changb15.pdf)[ing to search better than your teacher.](http://proceedings.mlr.press/v37/changb15.pdf) In *Proceedings of the 32nd International Conference on International Conference on Machine Learning*, volume 37, pages 2058–2066.

<span id="page-5-3"></span>Hyung Won Chung, Le Hou, S. Longpre, Barret Zoph, Yi Tay, William Fedus, Eric Li, Xuezhi Wang, Mostafa Dehghani, Siddhartha Brahma, Albert Webson, Shixiang Shane Gu, Zhuyun Dai, Mirac Suzgun, Xinyun Chen, Aakanksha Chowdhery, Sharan Narang, Gaurav Mishra, Adams Wei Yu, Vincent Zhao, Yanping Huang, Andrew M. Dai, Hongkun Yu, Slav Petrov, Ed Chi, Jeff Dean, Jacob Devlin, Adam Roberts, Denny Zhou, Quoc Le, and Jason Wei. 2022. [Scaling instruction-finetuned language](https://arxiv.org/pdf/2210.11416.pdf) [models.](https://arxiv.org/pdf/2210.11416.pdf) *ArXiv*, abs/2210.11416.

<span id="page-5-4"></span>Hal Daumé, John Langford, and Daniel Marcu. 2009. [Search-based structured prediction.](https://link.springer.com/article/10.1007/s10994-009-5106-x) *Machine learning*, 75(3):297–325.

<span id="page-5-1"></span>Nicola De Cao, Gautier Izacard, Sebastian Riedel, and Fabio Petroni. 2021. [Autoregressive entity retrieval.](https://openreview.net/forum?id=5k8F6UU39V) In *International Conference on Learning Representations*.

<span id="page-5-2"></span>Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. [BERT: Pre-training of](https://doi.org/10.18653/v1/N19-1423)

- [deep bidirectional transformers for language under](https://doi.org/10.18653/v1/N19-1423)[standing.](https://doi.org/10.18653/v1/N19-1423) In *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)*, pages 4171–4186, Minneapolis, Minnesota. Association for Computational Linguistics.
- <span id="page-6-9"></span>Vladimir Dobrovolskii. 2021. [Word-level coreference](https://doi.org/10.18653/v1/2021.emnlp-main.605) [resolution.](https://doi.org/10.18653/v1/2021.emnlp-main.605) In *Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing*, pages 7670–7675, Online and Punta Cana, Dominican Republic. Association for Computational Linguistics.
- <span id="page-6-10"></span>Janardhan Rao Doppa, Alan Fern, and Prasad Tadepalli. 2014. [Structured prediction via output space](http://jmlr.org/papers/v15/doppa14a.html) [search.](http://jmlr.org/papers/v15/doppa14a.html) *Journal of Machine Learning Research*, 15(38):1317–1350.
- <span id="page-6-11"></span>Greg Durrett and Dan Klein. 2014. A joint model for entity analysis: Coreference, typing, and linking. *Transactions of the Association for Computational Linguistics*, 2.
- <span id="page-6-7"></span>Chris Dyer, Adhiguna Kuncoro, Miguel Ballesteros, and Noah A. Smith. 2016. [Recurrent neural network](https://doi.org/10.18653/v1/N16-1024) [grammars.](https://doi.org/10.18653/v1/N16-1024) In *Proceedings of the 2016 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pages 199–209, San Diego, California. Association for Computational Linguistics.
- <span id="page-6-6"></span>Markus Eberts and Adrian Ulges. 2020. [Span-based](https://ecai2020.eu/papers/1283_paper.pdf) [joint entity and relation extraction with transformer](https://ecai2020.eu/papers/1283_paper.pdf) [pre-training.](https://ecai2020.eu/papers/1283_paper.pdf) *24th European Conference on Artificial Intelligence*.
- <span id="page-6-12"></span>Octavian-Eugen Ganea and Thomas Hofmann. 2017. [Deep joint entity disambiguation with local neural](https://doi.org/10.18653/v1/D17-1277) [attention.](https://doi.org/10.18653/v1/D17-1277) In *Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing*, pages 2619–2629, Copenhagen, Denmark. Association for Computational Linguistics.
- <span id="page-6-14"></span>Yoav Goldberg, Kai Zhao, and Liang Huang. 2013. [Ef](https://aclanthology.org/P13-2111)[ficient implementation of beam-search incremental](https://aclanthology.org/P13-2111) [parsers.](https://aclanthology.org/P13-2111) In *Proceedings of the 51st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)*, pages 628–633, Sofia, Bulgaria. Association for Computational Linguistics.
- <span id="page-6-13"></span>Jiatao Gu, James Bradbury, Caiming Xiong, Victor O.K. Li, and Richard Socher. 2018. [Non](https://openreview.net/forum?id=B1l8BtlCb)[autoregressive neural machine translation.](https://openreview.net/forum?id=B1l8BtlCb) In *International Conference on Learning Representations*.
- <span id="page-6-3"></span>Michael Hahn. 2020. [Theoretical limitations of self](https://doi.org/10.1162/tacl_a_00306)[attention in neural sequence models.](https://doi.org/10.1162/tacl_a_00306) *Transactions of the Association for Computational Linguistics*, 8:156–171.
- <span id="page-6-4"></span>Yiding Hao, Dana Angluin, and Robert Frank. 2022. [Formal language recognition by hard attention](https://doi.org/10.1162/tacl_a_00490) [transformers: Perspectives from circuit complexity.](https://doi.org/10.1162/tacl_a_00490)

- *Transactions of the Association for Computational Linguistics*, 10:800–810.
- <span id="page-6-1"></span>Luheng He, Kenton Lee, Mike Lewis, and Luke Zettlemoyer. 2017. [Deep semantic role labeling: What](https://doi.org/10.18653/v1/P17-1044) [works and what's next.](https://doi.org/10.18653/v1/P17-1044) In *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 473–483, Vancouver, Canada. Association for Computational Linguistics.
- <span id="page-6-8"></span>Mandar Joshi, Danqi Chen, Yinhan Liu, Daniel S. Weld, Luke Zettlemoyer, and Omer Levy. 2020. [SpanBERT: Improving pre-training by representing](https://doi.org/10.1162/tacl_a_00300) [and predicting spans.](https://doi.org/10.1162/tacl_a_00300) *Transactions of the Association for Computational Linguistics*, 8:64–77.
- <span id="page-6-17"></span>Mandar Joshi, Omer Levy, Luke Zettlemoyer, and Daniel Weld. 2019. [BERT for coreference reso](https://doi.org/10.18653/v1/D19-1588)[lution: Baselines and analysis.](https://doi.org/10.18653/v1/D19-1588) In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 5803–5808, Hong Kong, China. Association for Computational Linguistics.
- <span id="page-6-15"></span>Diederik P. Kingma and Jimmy Ba. 2015. [Adam: A](https://arxiv.org/pdf/1412.6980.pdf) [method for stochastic optimization.](https://arxiv.org/pdf/1412.6980.pdf) In *Proceedings of the 3rd International Conference on Learning Representations (ICLR 2015)*.
- <span id="page-6-18"></span>Sandra Kübler, Ryan McDonald, and Joakim Nivre. 2009. [Dependency parsing.](https://doi.org/10.2200/S00169ED1V01Y200901HLT002) *Synthesis Lectures on Human Language Technologies*, 2(1):1–127.
- <span id="page-6-0"></span>Kenton Lee, Luheng He, Mike Lewis, and Luke Zettlemoyer. 2017. [End-to-end neural coreference reso](https://doi.org/10.18653/v1/D17-1018)[lution.](https://doi.org/10.18653/v1/D17-1018) In *Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing*, pages 188–197, Copenhagen, Denmark. Association for Computational Linguistics.
- <span id="page-6-16"></span>Kenton Lee, Luheng He, and Luke Zettlemoyer. 2018. [Higher-order coreference resolution with coarse-to](https://doi.org/10.18653/v1/N18-2108)[fine inference.](https://doi.org/10.18653/v1/N18-2108) In *Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 2 (Short Papers)*, pages 687–692, New Orleans, Louisiana. Association for Computational Linguistics.
- <span id="page-6-2"></span>Mike Lewis, Yinhan Liu, Naman Goyal, Marjan Ghazvininejad, Abdelrahman Mohamed, Omer Levy, Veselin Stoyanov, and Luke Zettlemoyer. 2020. [Bart: Denoising sequence-to-sequence pre](https://doi.org/10.18653/v1/2020.acl-main.703)[training for natural language generation, translation,](https://doi.org/10.18653/v1/2020.acl-main.703) [and comprehension.](https://doi.org/10.18653/v1/2020.acl-main.703) *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*.
- <span id="page-6-5"></span>Tianyu Liu, Yuchen Jiang, Ryan Cotterell, and Mrinmaya Sachan. 2022. [A structured span selector.](https://doi.org/10.18653/v1/2022.naacl-main.189) In *Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*,

- pages 2629–2641, Seattle, United States. Association for Computational Linguistics.
- <span id="page-7-16"></span>Yi Luan, Dave Wadden, Luheng He, Amy Shah, Mari Ostendorf, and Hannaneh Hajishirzi. 2019. [A gen](https://doi.org/10.18653/v1/N19-1308)[eral framework for information extraction using dy](https://doi.org/10.18653/v1/N19-1308)[namic span graphs.](https://doi.org/10.18653/v1/N19-1308) In *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)*, pages 3036–3046, Minneapolis, Minnesota. Association for Computational Linguistics.
- <span id="page-7-0"></span>Xuezhe Ma and Eduard Hovy. 2016. [End-to-end](https://doi.org/10.18653/v1/P16-1101) [sequence labeling via bi-directional LSTM-CNNs-](https://doi.org/10.18653/v1/P16-1101)[CRF.](https://doi.org/10.18653/v1/P16-1101) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 1064–1074, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-7-3"></span>Giovanni Paolini, Ben Athiwaratkun, Jason Krone, Jie Ma, Alessandro Achille, Rishita Anubhai, Cicero Nogueira dos Santos, Bing Xiang, and Stefano Soatto. 2021. [Structured prediction as translation be](https://openreview.net/pdf?id=US-TP-xnXI)[tween augmented natural languages.](https://openreview.net/pdf?id=US-TP-xnXI) In *9th International Conference on Learning Representations, ICLR 2021*.
- <span id="page-7-4"></span>Sameer Pradhan, Alessandro Moschitti, Nianwen Xue, Olga Uryupina, and Yuchen Zhang. 2012. [CoNLL-](https://www.aclweb.org/anthology/W12-4501)[2012 shared task: Modeling multilingual unre](https://www.aclweb.org/anthology/W12-4501)[stricted coreference in OntoNotes.](https://www.aclweb.org/anthology/W12-4501) In *Joint Conference on EMNLP and CoNLL - Shared Task*, pages 1–40, Jeju Island, Korea. Association for Computational Linguistics.
- <span id="page-7-2"></span>Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J. Liu. 2020. [Exploring](http://jmlr.org/papers/v21/20-074.html) [the limits of transfer learning with a unified text-to](http://jmlr.org/papers/v21/20-074.html)[text transformer.](http://jmlr.org/papers/v21/20-074.html) *Journal of Machine Learning Research*, 21(140):1–67.
- <span id="page-7-7"></span>Victor Sanh, Albert Webson, Colin Raffel, Stephen H. Bach, Lintang Sutawika, Zaid Alyafeai, Antoine Chaffin, Arnaud Stiegler, Teven Le Scao, Arun Raja, Manan Dey, M Saiful Bari, Canwen Xu, Urmish Thakker, Shanya Sharma Sharma, Eliza Szczechla, Taewoon Kim, Gunjan Chhablani, Nihal Nayak, Debajyoti Datta, Jonathan Chang, Mike Tian-Jian Jiang, Han Wang, Matteo Manica, Sheng Shen, Zheng Xin Yong, Harshit Pandey, Rachel Bawden, Thomas Wang, Trishala Neeraj, Jos Rozen, Abheesht Sharma, Andrea Santilli, Thibault Fevry, Jason Alan Fries, Ryan Teehan, Stella Biderman, Leo Gao, Tali Bers, Thomas Wolf, and Alexander M. Rush. 2021. [Multitask prompted training enables](http://arxiv.org/abs/2110.08207) [zero-shot task generalization.](http://arxiv.org/abs/2110.08207)
- <span id="page-7-5"></span>Ilya Sutskever, Oriol Vinyals, and Quoc V. Le. 2014. [Sequence to sequence learning with neural networks.](https://proceedings.neurips.cc/paper/2014/file/a14ac55a4f27472c5d894ec1c3c743d2-Paper.pdf) *Advances in neural information processing systems*, 27.

- <span id="page-7-12"></span>Swabha Swayamdipta, Miguel Ballesteros, Chris Dyer, and Noah A. Smith. 2016. [Greedy, joint syntactic](https://doi.org/10.18653/v1/K16-1019)[semantic parsing with stack LSTMs.](https://doi.org/10.18653/v1/K16-1019) In *Proceedings of the 20th SIGNLL Conference on Computational Natural Language Learning*, pages 187–197, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-7-14"></span>Erik F. Tjong Kim Sang and Fien De Meulder. 2003. [Introduction to the CoNLL-2003 shared task:](https://aclanthology.org/W03-0419) [Language-independent named entity recognition.](https://aclanthology.org/W03-0419) In *Proceedings of the Seventh Conference on Natural Language Learning at HLT-NAACL 2003*, pages 142–147.
- <span id="page-7-13"></span>Lifu Tu and Kevin Gimpel. 2018. [Learning approx](https://openreview.net/pdf?id=H1WgVz-AZ)[imate inference networks for structured prediction.](https://openreview.net/pdf?id=H1WgVz-AZ) In *International Conference on Learning Representations*.
- <span id="page-7-11"></span>Gorka Urbizu, Ander Soraluze, and Olatz Arregi. 2020. [Sequence to sequence coreference resolution.](https://aclanthology.org/2020.crac-1.5) In *Proceedings of the Third Workshop on Computational Models of Reference, Anaphora and Coreference*, pages 39–46, Barcelona, Spain (online). Association for Computational Linguistics.
- <span id="page-7-1"></span>Oriol Vinyals, Łukasz Kaiser, Terry Koo, Slav Petrov, Ilya Sutskever, and Geoffrey Hinton. 2015. [Gram](https://proceedings.neurips.cc/paper/2015/file/277281aada22045c03945dcb2ca6f2ec-Paper.pdf)[mar as a foreign language.](https://proceedings.neurips.cc/paper/2015/file/277281aada22045c03945dcb2ca6f2ec-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 28. Curran Associates, Inc.
- <span id="page-7-15"></span>C. Walker and Linguistic Data Consortium. 2005. *[ACE](https://books.google.ch/books?id=SbjjuQEACAAJ) [2005 Multilingual Training Corpus](https://books.google.ch/books?id=SbjjuQEACAAJ)*. LDC corpora. Linguistic Data Consortium.
- <span id="page-7-8"></span>Jue Wang and Wei Lu. 2020. [Two are better than](https://doi.org/10.18653/v1/2020.emnlp-main.133) [one: Joint entity and relation extraction with table](https://doi.org/10.18653/v1/2020.emnlp-main.133)[sequence encoders.](https://doi.org/10.18653/v1/2020.emnlp-main.133) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 1706–1721, Online. Association for Computational Linguistics.
- <span id="page-7-17"></span>Shuly Wintner. 2010. *[Formal Language Theory](https://doi.org/https://doi.org/10.1002/9781444324044.ch1)*, chapter 1. John Wiley & Sons, Ltd.
- <span id="page-7-10"></span>Wei Wu, Fei Wang, Arianna Yuan, Fei Wu, and Jiwei Li. 2020. [CorefQA: Coreference resolution as](https://doi.org/10.18653/v1/2020.acl-main.622) [query-based span prediction.](https://doi.org/10.18653/v1/2020.acl-main.622) In *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, pages 6953–6963, Online. Association for Computational Linguistics.
- <span id="page-7-9"></span>Chunyang Xiao, Marc Dymetman, and Claire Gardent. 2016. [Sequence-based structured prediction for se](https://doi.org/10.18653/v1/P16-1127)[mantic parsing.](https://doi.org/10.18653/v1/P16-1127) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 1341– 1350, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-7-6"></span>Deming Ye, Yankai Lin, Peng Li, and Maosong Sun. 2022. [Packed levitated marker for entity and relation](https://doi.org/10.18653/v1/2022.acl-long.337) [extraction.](https://doi.org/10.18653/v1/2022.acl-long.337) In *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics*

- *(Volume 1: Long Papers)*, pages 4904–4917, Dublin, Ireland. Association for Computational Linguistics.
- <span id="page-8-2"></span>Yue Zhang and Stephen Clark. 2008. [A tale of two](https://aclanthology.org/D08-1059) [parsers: Investigating and combining graph-based](https://aclanthology.org/D08-1059) [and transition-based dependency parsing.](https://aclanthology.org/D08-1059) In *Proceedings of the 2008 Conference on Empirical Methods in Natural Language Processing*, pages 562– 571, Honolulu, Hawaii. Association for Computational Linguistics.
- <span id="page-8-0"></span>Tianyang Zhao, Zhao Yan, Yunbo Cao, and Zhoujun Li. 2020. [Asking effective and diverse questions: A ma](https://doi.org/10.24963/ijcai.2020/546)[chine reading comprehension based framework for](https://doi.org/10.24963/ijcai.2020/546) [joint entity-relation extraction.](https://doi.org/10.24963/ijcai.2020/546) In *Proceedings of the Twenty-Ninth International Joint Conference on Artificial Intelligence, IJCAI-20*, pages 3948–3954. International Joint Conferences on Artificial Intelligence Organization. Main track.
- <span id="page-8-1"></span>Zexuan Zhong and Danqi Chen. 2021. [A frustratingly](https://doi.org/10.18653/v1/2021.naacl-main.5) [easy approach for entity and relation extraction.](https://doi.org/10.18653/v1/2021.naacl-main.5) In *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pages 50–61, Online. Association for Computational Linguistics.

### A Experimental Details

### <span id="page-9-0"></span>A.1 Experimental Settings

In our experiments, the {T5,T0,flan-T5}-base, {T5,T0,flan-T5}-large, {T5,T0,flan-T5}-{3B,XL}, {T5,T0,flan-T5}-{11B,XXL} have 220 million, 770 million, 3 billion, and 11 billion parameters respectively[6](#page-9-2) . The feedforward neural networks described in [§2.3](#page-2-0) have one hidden layer of size 150 for ACE-05, 4096 for CoNLL-03, CoNLL-04, and CoNLL-12.

We follow the same preprocessing procedure and train/dev/test split of previous work on all datasets. For all the experiments, we use the AdamW optimizer [\(Kingma and Ba,](#page-6-15) [2015\)](#page-6-15). We train 40 epochs on CoNLL-12 for coreference resolution with batch size 1. For end-to-end relation extraction on CoNLL-04 and ACE-05, we train 100 epochs with batch size 8. The initial learning rates are set to 5e-5 for {T5,T0,flan-T5} base and {T5,T0,flan-T5}-large models, 3e-5 for {T5,T0,flan-T5}-{3B,XL,11B,XXL} models.

We apply bfloat16 training in our experiments. One single A100-40GB GPU is used for training models that use {T5,T0,flan-T5}-base and {T5,T0,flan-T5}-large. Two A100-40GB GPUs are required to train models that use 3B or XL. Six A100-80GB GPUs are required to train models that use 11B or XXL models. It takes around 0.1 seconds for base-scale models and 1 second per updating step for {3B,11B,XXL} models.

# <span id="page-9-1"></span>A.2 Datasets

#### A.2.1 Named Entity Recognition

CoNLL-03. We use the CoNLL-03 dataset [\(Tjong Kim Sang and De Meulder,](#page-7-14) [2003\)](#page-7-14) to evaluate our model on named entity recognition. This dataset consists of 946 training articles, 216 development articles, and 231 test sentences. We evaluate under the document-level settings, which means we feed the entire document into the model instead of the individual sentences.

#### A.2.2 End-to-End Relation Extraction

CoNLL-04. The CoNLL-04 dataset contains four types of entities (location, organization, person, other) and five types of relations (work for, kill, organization based in, live in, located in). We split the dataset as the training (922 sentences), validation (231 sentences), and test (288 sentences) as in

<span id="page-9-2"></span>6 [https://github.com/google-research/](https://github.com/google-research/text-to-text-transfer-transformer) [text-to-text-transfer-transformer](https://github.com/google-research/text-to-text-transfer-transformer)

previous work. For the ACE-05 dataset, we follow the train/dev/test split of previous work [\(Zhong and](#page-8-1) [Chen,](#page-8-1) [2021\)](#page-8-1).

ACE-05. The ACE-05 dataset [\(Walker and Con](#page-7-15)[sortium,](#page-7-15) [2005\)](#page-7-15) contains 511 documents in total collected from multiple domains including newswire, broadcast, discussion forums, etc. We follow [Luan](#page-7-16) [et al.](#page-7-16) [\(2019\)](#page-7-16)'s preprocessing script[7](#page-9-3) and split the dataset into train/dev/test set. ACE-05 contains inconsistently capitalized data. The newswire portion collected from CNN are entirely lowercased, which involves around 20 documents. Previous works [\(Zhong and Chen,](#page-8-1) [2021;](#page-8-1) [Ye et al.,](#page-7-6) [2022\)](#page-7-6) that use case-insensitive encoders such as ALBERT are not affected by this deficiency. However, the T5 model and its variants are case-sensitive. We use the python truecase package[8](#page-9-4) to restore the correct capitalization during preprocessing.

# A.2.3 Coreference Resolution

CoNLL-12. The CoNLL-12 English shared task dataset for coreference resolution [\(Pradhan et al.,](#page-7-4) [2012\)](#page-7-4) contains 2802 documents for training, 343 for validation, and 348 for testing. During training, we chunk the documents into segments of 2048 maximum words. In total, there are 2830 segments for training. During the evaluation, we use the entire document as the input to the model.

<span id="page-9-5"></span>![](_page_9_Figure_15.jpeg)

Figure 2: Recall rate of gold mentions. The ratio on the x-axis refers to the number of predicted mentions divided by |D|. Joshi refers to the two-stage model of [\(Joshi et al.,](#page-6-8) [2020\)](#page-6-8).

<span id="page-9-4"></span><span id="page-9-3"></span><sup>7</sup> https://github.com/luanyi/DyGIE/tree/master/preprocessing 8 https://pypi.org/project/truecase/

<span id="page-10-1"></span>

|                       |      | MUC  |      |      | B3   |      |      | CEAFφ4 |      |         |
|-----------------------|------|------|------|------|------|------|------|--------|------|---------|
|                       | P    | R    | F    | P    | R    | F    | P    | R      | F    | Avg. F1 |
| Lee et al. (2017)     | 78.4 | 73.4 | 75.8 | 68.6 | 61.8 | 65.0 | 62.7 | 59.0   | 60.8 | 67.2    |
| Lee et al. (2018)     | 81.4 | 79.5 | 80.4 | 72.2 | 69.5 | 70.8 | 68.2 | 67.1   | 67.6 | 73.0    |
| Joshi et al. (2019)   | 84.7 | 82.4 | 83.5 | 76.5 | 74.0 | 75.3 | 74.1 | 69.8   | 71.9 | 76.9    |
| Joshi et al. (2020)   | 85.8 | 84.8 | 85.3 | 78.3 | 77.9 | 78.1 | 76.4 | 74.2   | 75.3 | 79.6    |
| †<br>Joshi et al.+T5B | 82.4 | 77.4 | 79.8 | 72.3 | 68.2 | 70.2 | 70.5 | 63.5   | 66.8 | 72.3    |
| †<br>Joshi et al.+T5L | 85.5 | 77.7 | 81.4 | 78.3 | 68.5 | 73.1 | 75.0 | 65.9   | 73.1 | 74.9    |
| Dobrovolskii          | 84.9 | 87.9 | 86.3 | 77.4 | 82.6 | 79.9 | 76.1 | 77.1   | 76.6 | 81.0    |
| Urbizu et al.         | -    | -    | 64.9 | -    | -    | 66.5 | -    | -      | 65.3 | 65.6    |
| Paolini et al.+T5B    | -    | -    | 81.0 | -    | -    | 69.0 | -    | -      | 68.4 | 72.8    |
| ASP+T5B               | 81.7 | 82.8 | 82.3 | 74.2 | 76.1 | 75.1 | 74.5 | 70.6   | 72.5 | 76.6    |
| ASP+T5L               | 83.3 | 86.2 | 84.7 | 75.9 | 79.5 | 77.7 | 75.8 | 74.5   | 75.2 | 79.3    |
| ASP+FLAN-T5L          | 83.5 | 87.6 | 85.5 | 76.3 | 81.8 | 79.0 | 76.0 | 76.2   | 76.1 | 80.2    |
| ASP+T03B              | 85.8 | 88.3 | 86.9 | 79.6 | 83.3 | 81.5 | 78.3 | 78.5   | 78.4 | 82.3    |
| ASP+FLAN-T5XL         | 84.9 | 88.7 | 86.7 | 78.5 | 83.8 | 81.1 | 78.4 | 78.5   | 78.4 | 82.2    |
| ASP+FLAN-T5XXL        | 86.1 | 88.4 | 87.2 | 80.2 | 83.2 | 81.7 | 78.9 | 78.3   | 78.6 | 82.5    |

Table 5: Full results on the CoNLL-12 English test set. Avg. F1 denotes the average F1 of MUC, B<sup>3</sup> , and CEAFφ<sup>4</sup> . Models marked with † are our re-implementation. Other results are taken from their original papers.

### <span id="page-10-0"></span>B Coreference Resolution

In this section, we analyze the performance of mention detection for coreference resolution of our model in Fig. [2.](#page-9-5) This analysis casts light on how our model *plans globally* in an autoregressive manner. In the task of coreference resolution, only the entities that are mentioned more than once in a document are annotated as mentions. This is to say, an utterance of an entity should only be labeled if that entity is referred to again afterward. Thus, in previous coreference resolution models, a dedicated mention detection module that enumerates candidate textual spans (e.g., noun phrases and pronouns) for mentions is indispensable. However, our model is able to directly predict the exact set of mentions that we require, even if the target sequence is generated from left to right. We conclude that this results from the cross-attention mechanism which enables the model to look at relevant parts in the input document during decoding. Given an input document of |D| words, our model predicts only 0.096 |D| mentions with a 89.6% recall rate of gold mentions. This refrained mention detection strategy imposes a limit on the cardinality of Z<sup>i</sup> in Eq. [\(2\)](#page-2-2). As a result, this relatively small constant factor (compared to 0.4 used in most previous work) keeps our model tractable without the need for pruning strategies as in the models based on [\(Lee et al.,](#page-6-0) [2017\)](#page-6-0).

### C Modeling More Restricted Structures

In this work, we tackled three tasks that are traditionally considered structured prediction problems. Named entity recognition and relation extraction consider labeling spans with a set of given types. Coreference resolution has long-range dependencies and has to model relationships between spans. However, there are structured prediction problems that require more restricted outputs. For instance, in dependency parsing, a spanning tree connecting every word in the input sentence is the desired output [\(Kübler et al.,](#page-6-18) [2009\)](#page-6-18). While in constituency parsing, a parse tree in Chomsky Normal Form is supposed to be a complete binary tree except for the leaf nodes [\(Wintner,](#page-7-17) [2010\)](#page-7-17). Modeling such types of structures requires a more specified definition of task-specific actions. In future work, we aim to explore the abilities and limitations of our method.

### D Experiments with Flan-T5

We conduct additional experiments with the latest pretrained language model Flan-T5 [\(Chung et al.,](#page-5-3) [2022\)](#page-5-3). Flan-T5 is pretrained on more supervised tasks and achieves better performance than the original T5 on multiple NLU tasks. The results are shown in Tab. [5,](#page-10-1) Tab. [6,](#page-11-0) and Tab. [7.](#page-11-1) We find that with the same size of the model, Flan-T5 performs better than T5 in general.

<span id="page-11-0"></span>

|              | Prec. | Rec. | F1   |
|--------------|-------|------|------|
| ASP+T5B      | 91.4  | 92.2 | 91.8 |
| ASP+FLAN-T5B | 92.7  | 93.8 | 93.3 |
| ASP+T5L      | 92.1  | 93.4 | 92.8 |
| ASP+FLAN-T5L | 93.3  | 94.3 | 93.8 |
| ASP+T53B     | 93.8  | 94.4 | 94.1 |

<span id="page-11-1"></span>Table 6: Test F1 scores of named entity recognition on the CoNLL-03 test set.

|              | Ent  | Rel  |
|--------------|------|------|
| ASP+T5B      | 89.5 | 73.2 |
| ASP+FLAN-T5B | 89.4 | 73.8 |
| ASP+FLAN-T5L | 90.5 | 76.2 |

Table 7: Test F1 scores of named entity recognition on the CoNLL-04 test set.

# E Decoding Examples

We provide decoding examples from the tasks we experiment on in Tab. [8.](#page-12-0) The copy actions are verbalized into tokens.

<span id="page-12-0"></span>![](_page_12_Figure_0.jpeg)

Table 8: Predicted sequences from CoNLL-03, ACE-05, and CoNLL-12 dataset.