# A Multidimensional Framework for Evaluating Lexical Semantic Change with Social Science Applications

#### Naomi Baes\* Nick Haslam\* Ekaterina Vylomova\*\*

\* Melbourne School of Psychological Sciences \*\* School of Computing and Information Systems The University of Melbourne {n.baes, nhaslam, vylomovae}@unimelb.edu.au

# Abstract

Historical linguists have identified multiple forms of lexical semantic change. We present a three-dimensional framework for integrating these forms and a unified computational methodology for evaluating them concurrently. The dimensions represent increases or decreases in semantic 1) sentiment (valence of a target word's collocates), 2) breadth (diversity of contexts in which the target word appears), and 3) intensity (emotional arousal of collocates or the frequency of intensifiers). These dimensions can be complemented by the evaluation of shifts in the frequency of the target words and the thematic content of its collocates. This framework enables lexical semantic change to be mapped economically and systematically and has applications in computational social science. We present an illustrative analysis of semantic shifts in *mental health* and *mental illness* in two corpora, demonstrating patterns of semantic change that illuminate contemporary concerns about pathologization, stigma, and concept creep.

# 1. Introduction

Lexical semantic change is defined by historical linguists as innovations that alter the meaning, but not the grammatical function, of a form [\(Campbell,](#page-10-0) [1999\)](#page-10-0). For instance, "awesome" once denoted the capacity to inspire awe, but its meaning has since been bleached to a general expression of approval. Computational linguists have made strides in developing distributional semantic methods [\(Boleda,](#page-10-1) [2020\)](#page-10-1) to detect semantic change [\(Kutuzov et al.,](#page-12-0) [2018;](#page-12-0) [Tahmasebi et al.,](#page-13-0) [2021;](#page-13-0) [Tang,](#page-13-1) [2018\)](#page-13-1) and its laws [\(Hamilton et al.,](#page-11-0) [2016b\)](#page-11-0) as distinct from cultural shifts [\(Hamilton et al.,](#page-11-1) [2016a\)](#page-11-1).

Advances in deep learning since 2018 [\(Manning,](#page-12-1) [2022\)](#page-12-1) afford new ways to model semantic change processes. These innovations have facilitated the development of language models with sophisticated word embeddings or vector representations. As a result, word embeddings have evolved from count-based models [\(Jurafsky and Martin,](#page-12-2) [2023\)](#page-12-2), where words are represented by their co-occurrence frequency with other words, to prediction-based representations [\(Mikolov et al.,](#page-12-3) [2013;](#page-12-3) [Pennington](#page-13-2) [et al.,](#page-13-2) [2014\)](#page-13-2), where word vectors are iteratively learned as part of a language modelling task objective. The granularity of these representations shifted from *type-level*, where each word has a single vector despite its usages, to *token-based*, or contextualized representations [\(Montanelli and Per](#page-12-4)[iti,](#page-12-4) [2023;](#page-12-4) [Kutuzov et al.,](#page-12-5) [2022\)](#page-12-5), where each word instance (token) has a vector, dynamically capturing shifts in meaning based on context. Lexical semantic relations can be detected by type- [\(Shwartz](#page-13-3) [et al.,](#page-13-3) [2016;](#page-13-3) [Vylomova et al.,](#page-14-0) [2016\)](#page-14-0) and token-level [\(Rogers et al.,](#page-13-4) [2020\)](#page-13-4) embeddings.

Other work has started addressing the challenge of formalizing and understanding kinds of semantic change [\(Hengchen et al.,](#page-12-6) [2021\)](#page-12-6). Processes such as broadening [\(Vylomova et al.,](#page-13-5) [2019;](#page-13-5) [Yüksel et al.,](#page-14-1) [2021\)](#page-14-1), metaphorization [\(Maudslay](#page-12-7) [and Teufel,](#page-12-7) [2022\)](#page-12-7), and pejoration/amelioration [\(Fonteyn and Manjavacas,](#page-11-2) [2021\)](#page-11-2) have been modelled. Researchers have created methods to automatically disambiguate a word's pejorative usage from its non-pejorative use [\(Dinu et al.,](#page-11-3) [2021\)](#page-11-3). Attempts have also been made to evaluate understudied classes of semantic change. Sentence representations from neural language models were used for hyperbole detection [\(Schneidermann et al.,](#page-13-6) [2023\)](#page-13-6). Exaggerated language can be generated [\(Tian et al.,](#page-13-7) [2021\)](#page-13-7) and detected [\(Kong et al.,](#page-12-8) [2020\)](#page-12-8), alongside metaphor [\(Badathala et al.,](#page-10-2) [2023\)](#page-10-2). Researchers have also evaluated semantic bleaching, whereby words lose elements of their meaning [\(Luo et al.,](#page-12-9) [2019\)](#page-12-9), and found it to be triggered in contexts where an adverb premodifies a semantically similar adjective (e.g., "insanely jealous"). Nevertheless, there are a dearth of diachronic methods for evaluating lexical semantic change [\(de Sá et al.,](#page-11-4) [2024\)](#page-11-4).

Despite advances in detecting and modelling lexical semantic change, there is a need for a unifying framework to integrate multiple dimensions of change. The present study addresses this gap by proposing a framework which synthesizes the theoretical insights of historical linguists about the many distinct forms of diachronic lexical semantic change (e.g., [Bloomfield,](#page-10-3) [1933\)](#page-10-3) and aligns them with the methodological sophistication of natural language processing. The comprehensive computational framework for evaluating lexical semantic change that emerges should be valuable for computational social scientists seeking to understand and model social and cultural change.

### 2. Related Work

### 2.1 Forms of Lexical Semantic Change

Historical linguists have developed several taxonomies of the forms of lexical semantic change [\(Blank,](#page-10-4) [1999;](#page-10-4) [Bréal,](#page-10-5) [1897;](#page-10-5) [Ullmann,](#page-13-8) [1962\)](#page-13-8), but [Bloomfield'](#page-10-3)s [\(1933\)](#page-10-3) is one of the most wellestablished. Bloomfield described nine forms identified by earlier scholars: (1) narrowing: superordinate to subordinate, or when a meaning becomes more restricted (Old English *mete* 'all food' > *meat* 'edible flesh'); (2) widening: subordinate to superordinate, or specific to general expansion of meaning (Middle English *dogge* 'dog of a specific breed' > dog); (3) metaphor: the transfer of a name based on the associations of similarity or hidden comparison (Primitive Germanic *bitraz* 'biting', derivative of 'I bite' > *bitter* 'harsh of taste'), (4) metonymy: change based on the meanings' proximity in space or time (Old English *ceace* 'jaw' > *cheek*); (5) synecdoche: the meanings are related as whole and part (pre-English *stobo* 'heated room' > stove), (6) hyperbole: stronger to weaker meaning by overstatement (pre-French *extonare* 'to strike with thunder' > to astonish; English borrowed *astound*, *astonish* from Old French); (7) meiosis:[1](#page-1-0) weaker to stronger meaning by understatement (pre-English *kwalljan* 'to torment' > Old English *cwellan* 'to kill'); (8) degeneration: positive to negative connotation (Old English *cnafa* 'boy servant' > *knave*); (9) elevation: negative to positive connotation (Old English *cniht* 'boy, servant' > *knight*).

Bloomfield's classes align closely with the forms of change identified in studies of denotational and connotational meaning [\(Geeraerts,](#page-11-5) [2010\)](#page-11-5). For de-

notational (referential) meaning, Geeraerts identifies (1) specialization, (2) generalization, (3) metonymy, and (4) metaphor. Specialization (semantic 'restriction' and 'narrowing') implies that the new meaning covers a subset of the old meaning's range; for generalization (or 'expansion', 'extension', 'schematization', 'broadening'), the new range includes the old meaning. Metonymy (here including synecdoche) is a "link between two readings of a lexical item based on a relationship of contiguity between the referents of the expression in each of those readings" [\(Geeraerts,](#page-11-5) [2010,](#page-11-5) p. 27). Conversely, metaphor is based on similarity. Geeraerts also identifies two forms of connotational meaning (i.e., the aspects of a word's meaning that are related to the writer or reader's emotions, sentiment, opinions, or evaluations): (1) pejorative and (2) ameliorative change (i.e., shift towards a more negative/positive emotive meaning). An example of pejoration is 'silly', which formerly meant 'deserving sympathy, helpless', but has come to mean 'showing a lack of common sense'. Amelioration is shown by 'knight' once meaning 'boy, servant'.

# 2.2 Expanding Concepts of Harm and Pathology

Semantic change processes such as these may partly reflect cultural, social, and political shifts, and are of interest to social science researchers. One example is social psychological research on concept creep, the semantic expansion of harmrelated concepts (e.g., abuse, bullying, mental illness, prejudice, trauma, violence; [Haslam,](#page-11-6) [2016\)](#page-11-6). Concept creep takes two forms: harm-related concepts have expanded 'horizontally' to cover a wider range of harms and 'vertically' to encompass less intense harms. It is theorized to be driven by rising cultural sensitivity to harm [\(Furedi,](#page-11-7) [2016;](#page-11-7) [Wheeler et al.,](#page-14-2) [2019\)](#page-14-2), falling societal prevalence of harm [\(Levari et al.,](#page-12-10) [2018;](#page-12-10) [Pinker,](#page-13-9) [2011\)](#page-13-9), and deliberate conceptual expansion by "opprobrium entrepreneurs" [\(Sunstein,](#page-13-10) [2018\)](#page-13-10). Concept creep is theorized to have mixed blessings [\(Haslam et al.,](#page-11-8) [2020\)](#page-11-8), trivializing harms on one hand [\(Dakin et al.,](#page-11-9) [2023\)](#page-11-9) and enhancing the recognition and redress of major harms on the other [\(Tse and Haslam,](#page-13-11) [2021\)](#page-13-11).

Prior empirical work has evaluated concept creep in historical text corpora. Studies assessing horizontal expansion as increases in the broadening of harm concepts found that some concepts (e.g., addiction, bullying, trauma) have broadened within academic psychology [\(Haslam et al.,](#page-12-11) [2021;](#page-12-11) [Vylo-](#page-13-5)

<span id="page-1-0"></span><sup>1</sup>Bloomfield (1933) refers to this class as litotes, but we use meiosis to reflect general understatement.

[mova et al.,](#page-13-5) [2019;](#page-13-5) [Vylomova and Haslam,](#page-13-12) [2021\)](#page-13-12). Recent work evaluated the vertical form of concept creep, defined as the concept's use in contexts of declining emotional intensity, and yielded mixed findings for anxiety, depression, grief, stress, and trauma [\(Baes et al.,](#page-10-6) [2023a,](#page-10-6)[b;](#page-10-7) [Xiao et al.,](#page-14-3) [2023\)](#page-14-3).

Mental illness has become an increasingly salient term in society [\(Haslam and Baes,](#page-11-10) [2024\)](#page-11-10), partly due to the recent prioritization of mental health in global health policy [\(WHO,](#page-14-4) [2021\)](#page-14-4). Critics have raised concerns that the rising prominence of mental health discourse is instigating problematic changes in how people conceptualize mental ill health. Some contend that concepts of mental illness have broadened so that everyday life is increasingly pathologized [\(Brinkmann,](#page-10-8) [2016;](#page-10-8) [Horwitz and Wakefield,](#page-12-12) [2007,](#page-12-12) [2012\)](#page-12-13). Experiences that were once considered normal are now given diagnostic labels, such as using 'depression' to reference ordinary sadness [\(Bröer and Besseling,](#page-10-9) [2017\)](#page-10-9). Alternatively, it has been argued that terms like "mental health problems" are being normalized and broadened [\(Sartorius,](#page-13-13) [2007\)](#page-13-13), alongside increasing prevalence of mental illnesses. Some argue that concepts of mental illness are becoming less stigmatizing, although this question has only been addressed in surveys of public attitudes (e.g., [Schomerus et al.,](#page-13-14) [2022\)](#page-13-14), rather than in changes in word connotations. In view of the widespread speculation on the ways in which concepts of mental illness have changed historically and the lack of scientific evidence of these shifts, a systematic study of conceptual change in this domain is a priority.

### 2.3 Our Original Contribution

The present study aims to make three main contributions: (1) it proposes a multidimensional framework for evaluating lexical semantic change that economically integrates forms identified by historical linguists; (2) it develops a set of computational methodologies for evaluating change on these dimensions; and 3) it illustrates this computational framework by examining semantic shifts in concepts of mental health and mental illness to address cultural concerns about pathologization, normalization, and stigmatization. The study will therefore test if the framework can thoroughly illuminate how *mental health* and *mental illness* have changed their meanings in two corpora representing academic psychology and general US English text.[2](#page-2-0)

# 3. Method

### 3.1 Framework

The proposed framework, illustrated in Figure [1,](#page-2-1) economically reduces classes of lexical semantic change identified by historical linguists (excluding metaphor and metonymy; [Geeraerts,](#page-11-5) [2010\)](#page-11-5) to three dimensions. It recognizes that these classes represent opposed pairs of change types, each member corresponding to a pole on a single dimension. In essence, the framework reformulates six classes as three dimensions, allowing lexical semantic change to be quantified on three axes simultaneously rather than categorized into exclusive types. A recent survey paper [\(de Sá et al.,](#page-11-4) [2024\)](#page-11-4) has also classified semantic change as having three classes of characterizations related to a word's meaning becoming used in a more (1) pejorative or ameliorated sense (orientation), (2) metaphoric or metonymic context (relation), (3) abstract/general or more specific/narrow context (dimension). However, their theoretical framework does not consider hyperbole/litotes.

<span id="page-2-1"></span>![](_page_2_Picture_8.jpeg)

Figure 1: Three Major Dimensions of Semantic Change.

In our proposed framework, the *Sentiment* dimension relates to whether the word acquires a more positive ('elevation', 'amelioration') or negative ('degeneration', 'pejoration') connotation. The *Breadth* dimension relates to whether a word expands ('widening', 'generalization') or contracts ('narrowing', 'specialization') its semantic range. The *Intensity* dimension relates to whether a word changes to refer to more emotionally or referentially intense phenomena ('meiosis') or less intense phenomena ('hyperbole'). Table [1](#page-3-0) summarizes how the three dimensions map onto the classes of lexical semantic change as well as the two proposed forms of concept creep.

<span id="page-2-0"></span><sup>2</sup>The source code is available here: [https://github.](https://github.com/naomibaes/lexical_semantic_change_framework) [com/naomibaes/lexical\\_semantic\\_change\\_framework](https://github.com/naomibaes/lexical_semantic_change_framework)

<span id="page-3-0"></span>

| Dimension | Rising                                                                                                                               | Falling                                                                                          |
|-----------|--------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------|
| Sentiment | Elevation (Bloomfield,<br>1933); Ameliora<br>tion (Ullmann, 1962)                                                                    | Degeneration (Bloomfield,<br>1933); Pejora<br>tion (Ullmann, 1962)                               |
| Breadth   | Widening<br>(Bloomfield,<br>1933;<br>Ullmann,<br>1962); Generalization of meaning (Blank,<br>1999); Horizontal Creep (Haslam, 2016)* | Narrowing (Bloomfield,<br>1933;<br>Ullmann,<br>1962); Specialization of meaning (Blank,<br>1999) |
| Intensity | Meiosis (Bloomfield, 1933)                                                                                                           | Hyperbole (Bloomfield,<br>1933);<br>Vertical<br>Creep (Haslam, 2016)*                            |

Table 1: Dimensions of Lexical Semantic Change and their associated forms. \* = specific to harm-related concepts.

The three proposed dimensions align with established dimensions in other domains. For example, Sentiment and Intensity resemble the two primary dimensions of human emotion, Valence and Arousal [\(Russell,](#page-13-15) [2003\)](#page-13-15), and two primary dimensions of connotational meaning, Evaluation (e.g., "good/bad") and Potency (e.g., "strong/weak") [\(Os](#page-12-14)[good et al.,](#page-12-14) [1975\)](#page-12-14), both of which have been shown to have cross-cultural validity. Although our dimensions capture the primary forms of lexical change, we argue that they can be complemented by evaluation of changes in a word's salience (i.e., relative frequency of use) and its *thematic content* (i.e., shifts in the specific contexts in which the word is used). These dimensions may reflect psychological, sociocultural, or cultural forces that contribute to or result from semantic change [\(Blank,](#page-10-4) [1999\)](#page-10-4). Our case study of *mental health* and *mental illness* illustrates how attention to salience and thematic content enrich the characterization of semantic change that the three primary dimensions provide. We now turn to the details of that case study, including the computational methodologies for evaluating these dimensions. Future implementations of our threedimensional framework are likely to include technical refinements of these methodologies. Those employed in the case study simply demonstrate one way to implement it using interpretable techniques.

### <span id="page-3-2"></span>3.2 Sentiment

The sentiment of the target concepts (*mental health* and *mental illness* and the control concept *perception*) was evaluated using valence norms from [War](#page-14-5)[riner et al.](#page-14-5) [\(2013\)](#page-14-5), which provide valence ratings for 13,915 English lemmas collected from 1,827 United States residents, ranging from low valence (1: feeling extremely "unhappy", "despaired") to high valence (9: feeling extremely "happy", "hopeful"). See Appendix [A](#page-14-6) for more information regarding the valence ratings. Collocates of each

target concept were extracted within a ± 5-word context window [\(Agirre et al.,](#page-10-10) [2009\)](#page-10-10) and matched to the Warriner et al. norms which showed adequate coverage for the psychology corpus but poorer coverage for the general corpus ("mental\_health": psychology = 84%; general = 50%; "mental\_illness": psychology = 83%;general = 48%; "perception": psychology = 84%; general = 39%). Annual counts of Warriner-matched collocates for each target concept were then extracted from the lemmatized corpora, which showed few occurrences due to few appearances of texts containing targets before 1990 in the general corpus (see Appendix [B\)](#page-15-0). Therefore, analyses excluded general texts before 1990. The annual sentiment score for each concept was computed by weighting the valence rating for each collocate by its annual appearances, standardized by the total number of (matched) collocates in the respective year. The index represents the mean valence of terms [1,9] collocating with target concepts, where higher scores indicate higher valence.

# <span id="page-3-1"></span>3.3 Breadth

The semantic broadening of the target concept was evaluated as the average inverse cosine similarity between the sentence level embeddings containing the target term. Our method adapts previous work [\(Vylomova et al.,](#page-13-5) [2019;](#page-13-5) [Vylomova and](#page-13-12) [Haslam,](#page-13-12) [2021\)](#page-13-12) by replacing type-level word embeddings with contextualized sentence-level embeddings. Given that this breadth measure resembles the Semantic Textual Similarity (STS) task [\(Cer et al.,](#page-10-11) [2017,](#page-10-11) the degree to which two sentences are semantically equivalent to each other), to select the optimal model we compared the sentence similarity scores, from corpus samples, of models that have shown good performance for encoding sentences. Many of the original Sentence-BERT models [\(Reimers and Gurevych,](#page-13-16) [2019\)](#page-13-16) with good scores on semantic textual similarity benchmarks

[\(Tsukagoshi et al.,](#page-13-17) [2022;](#page-13-17) [Reimers and Gurevych,](#page-13-16) [2019\)](#page-13-16) are deprecated, therefore we examined and compared three public pre-trained models that currently excel in encoding sentences,[3](#page-4-0) from the sentence transformers library. See Appendix [C](#page-15-1) for more information regarding model selection [\(C\)](#page-15-1), comparison [\(C\)](#page-16-0) and results [\(C\)](#page-18-0). The pre-trained model used in the present study[4](#page-4-1) performed best on detecting *semantic* information and encoding sentences for 14 diverse tasks from different domains.

To compute the breadth score, relevant texts were extracted from our corpora. Inspecting their frequencies showed that it was acceptable to sample 50 texts from each five-year interval.[5](#page-4-2) Thus, we randomly and uniformly sampled up to 50 sentences per interval and repeated the procedure 10 times to reduce sampling noise. These sentences were then passed to the sentence transformer model, "all-mpnet-base-v2" (where MPNET means Masked Permuted Language Modeling Network), to be tokenized and to encode embeddings representing their semantic characteristics. Cosine distance was computed for each pair of sentence vectors by inverting the similarity scores (1 - cosine similarity). The final breadth metric [0,1] was calculated by averaging scores across samples in each interval. Higher scores indicate greater breadth (*dis*similarity) between sentence vectors.

### <span id="page-4-4"></span>3.4 Intensity

Changes in the intensity of the concepts were evaluated in two ways. First, we computed an arousal index, adapting a previously established procedure [\(Baes et al.,](#page-10-6) [2023a](#page-10-6)[,b;](#page-10-7) [Xiao et al.,](#page-14-3) [2023\)](#page-14-3). In an equivalent manner to the sentiment analysis, we examined the collocates of each concept and computed a weighted average annual ratings, using Warriner et al.'s arousal norms that range from low arousal (1: feeling "calm", "unaroused" while reading the lemma) to high arousal (9: feeling "agitated", "aroused"). See Appendix [A](#page-14-6) for more information regarding arousal ratings. The annual arousal score for each concept was calculated by weighting the arousal rating for each collocate by its total number of appearances in each year and normalizing it by the total (matched) collocate count for the respective year. The index represents the mean arousal of

terms [1,9] collocating with target concepts, where higher scores indicate higher arousal.

Second, we developed a new index to directly capture shifts in a concept's intensity. Instead of examining the arousal of its collocates (regardless of their order), it examined the occurrence of intensifying expressions that directly modify it. If a concept increasingly appears with an intensifying modifier, it can be inferred that its unmodified meaning has become less intense. We developed a new "intensifier index" which evaluates the relative frequency with which 11 adjectival modifiers ("great", "intense", "severe", "harsh", "major", "extreme", "powerful", "serious", "devastating", "destructive", "debilitating") preceded "mental health" and "mental illness". De-adjectival adverbs from [Luo et al.](#page-12-9) [\(2019\)](#page-12-9) were considered but most were not sufficiently general (e.g., "devastating", "excruciating", "vicarious"). We used the dependencyparsed corpora (see Section [4.2\)](#page-5-0) to compute the proportion of instances of each target concept that has any of the 11 terms as its adjective modifier.

### <span id="page-4-5"></span>3.5 Thematic content

Thematic content was evaluated using a top-down approach. The theme of interest was pathology given concerns raised by critics about the pathologization of *mental health* and *mental illness* [\(Brinkmann,](#page-10-8) [2016;](#page-10-8) [Horwitz and Wakefield,](#page-12-12) [2007,](#page-12-12) [2012\)](#page-12-13). We used a pathologization dictionary developed by [Baes et al.](#page-10-6) [\(2023a\)](#page-10-6) to compute the pathologization index. This approach can be used to construct dictionaries for other themes of interest. First, we generated unambiguously disease-related words with restricted range in meaning: "clinical", "disorder", "symptom", "illness", "pathology", and "disease". Next, their forward word associations (participant responses to each disease-related word) drawn from the English Small World of Words project [\(De Deyne et al.,](#page-11-11) [2019\)](#page-11-11) were listed and duplicates were removed. We filtered the list for terms reflecting pathologization (i.e., to view or characterize as medically or psychologically abnormal), leaving 17 terms: "ailment", "clinical", "clinic", "cure", "diagnosis", "disease", "disorder", "ill", "illness", "medical", "medicine", "pathology", "prognosis", "sick", "sickness", "symptom", "treatment". Following [Baes et al.](#page-10-6) [\(2023a\)](#page-10-6), we computed the pathologization index by dividing appearances of the 17 terms in the target concept's collocates (±5-word context window) in a specific year by the total number of collocates in that year.

<span id="page-4-0"></span><sup>3</sup> [https://www.sbert.net/docs/pretrained\\_models.](https://www.sbert.net/docs/pretrained_models.html) [html](https://www.sbert.net/docs/pretrained_models.html)

<span id="page-4-1"></span><sup>4</sup> "all-mpnet-base-v2" from Hugging Face, sentence-transformers: [https://huggingface.co/](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)

<span id="page-4-3"></span><span id="page-4-2"></span><sup>5</sup>Appendix [C](#page-17-0) explains interval selection.

# 3.6 Salience

Salience was computed as the concept's annual relative frequency, using the raw corpora versions.

### 4. Materials

# 4.1 Corpora

Two corpora were chosen for their historical length, their magnitude, and their texts. The psychology corpus contained 143,575,773 tokens from 871,344 abstracts from 875 (Scimago indexed) psychology journals, ranging from 1930 to 2019, sourced from E-Research and PubMed databases [\(Vylo](#page-13-5)[mova et al.,](#page-13-5) [2019\)](#page-13-5). The journal set was distributed across all subdisciplines of psychology. The final corpus of psychology abstracts was limited to 1970- 2016 due to the relatively small number of abstracts outside this period [\(Vylomova et al.,](#page-13-5) [2019\)](#page-13-5), yielding 129,980,596 tokens from 793,942 abstracts.

The second corpus is a combination of two related corpora: the Corpus of Historical American English [\(Davies,](#page-11-12) [2010,](#page-11-12) 1810-2009) and the Corpus of Contemporary American English [\(Davies,](#page-11-13) [2008,](#page-11-13) 1990-2019). Academic texts were excluded to avoid any potential overlap with psychology articles. After merging the two corpora, containing 115,000 everyday publications and >500,000 contemporary texts, the combined corpus was processed following recommendations from [Alatrash](#page-10-12) [et al.](#page-10-12) [\(2020\)](#page-10-12) to maintain data integrity.[6](#page-5-1) The current study restricted the corpus period from 1970 to 2016, using 501,415,577 tokens from 244,552 texts (books: 23,855 fiction, 1,498 non-fiction; 88,641 magazines; 73,557 newspapers; 40,036 spoken language; 16,965 TV shows).

### <span id="page-5-0"></span>4.2 Preprocessing

Analyses required three versions of the corpora: (1) a raw cleaned version transforming target concepts to single noun tokens (Section [3.6](#page-4-3) and [3.3](#page-3-1) and [3.4\)](#page-4-4); (2) a lemmatized version (Section [3.2,](#page-3-2) [3.4,](#page-4-4) and [3.5\)](#page-4-5); and (3) a dependency parsed version (Section [3.4\)](#page-4-4). The first version, including punctuation, uppercasing, and numbers, was used for all analyses after transforming multiword target concepts into single tokens (e.g., "mental health" > "mental\_health") using case sensitive matching. The lemmatization pipeline included tokenization, part-of-speech tagging (skipping tokens with uninformative tags: punctuation, symbols, spaces, numbers), removing stop words (uninformative words

like "the"), and lemmatization using spaCy.[7](#page-5-2) For dependency parsing we used the raw corpora to provide more contextual information for the model to better understand relationships between words. The English Transformer model[8](#page-5-3) was used to preprocess the corpus with a high performance computing system [\(Lafayette et al.,](#page-12-15) [2016\)](#page-12-15).

### 4.3 Target Concepts

Two terms were chosen to analyze levels of semantic change [\(Hamilton et al.,](#page-11-1) [2016a\)](#page-11-1): *mental\_health* and *mental\_illness*. We also ran control analyses using the neutral term, *perception*, for which a fixed rate of change was expected and which demonstrated a steady rise in relative frequency starting around 1945 in the Google Ngram Viewer.[9](#page-5-4)

## 4.4 Statistical Analysis

Linear regression analyses were performed to test the statistical significance of historical trends in the semantic indices [\(Jebb et al.,](#page-12-16) [2015\)](#page-12-16). Ordinary least squares served as the primary estimator, the secondary one being a generalized least squares estimator to account for auto-correlated residuals (Durbin-Watson test: *p* < .05). Coefficients, standard errors and confidence intervals were standardized using the betaSandwich package [\(Pesigan et al.,](#page-13-18) [2023\)](#page-13-18), employing Dudgeon's [\(2017\)](#page-11-14) heteroskedasticity-consistent estimator approach (HC3), ideal for extracting estimates for nonnormal data and small sample sizes [\(Dudgeon,](#page-11-14) [2017\)](#page-11-14). The code is publicly available.[10](#page-5-5)

# 5. Results

Sentiment: The linear regression models mostly show decreasing trends for the valence index. Figure [2](#page-6-0) shows a significant declining trend in the valence of words used in the context of *mental health* in the psychology corpus and the general corpus. For *mental illness*, the valence index shows a decreasing trend in psychology, and an increase in the general corpus. The valence of *perception* only shows a decreasing trend in the general corpus.

Breadth: The linear regression models testing the trend for the cosine distance of sentential contexts containing targets show significant increas-

<span id="page-5-4"></span>9

<span id="page-5-1"></span><sup>6</sup> See Appendix [D](#page-20-0) for a comprehensive explanation.

<span id="page-5-3"></span><span id="page-5-2"></span><sup>7</sup> <https://spacy.io/>

<sup>8</sup> "en\_core\_web\_trf" (roberta-base) from Spacy was used as it demonstrates the highest accuracy on 13 evaluation tasks: [https://spacy.io/models/en#en\\_core\\_web\\_trf.](https://spacy.io/models/en#en_core_web_trf.)

<span id="page-5-5"></span><https://books.google.com/ngrams/info>

<sup>10</sup><https://osf.io/4d7ur/>

<span id="page-6-0"></span>![](_page_6_Figure_0.jpeg)

Figure 2: Valence index over the study period (1970- 2016).

ing trends for *mental health*, *mental illness* and *perception* in the psychology corpus, reflecting greater sentence diversity, with a decrease for *mental health* and an increase for *perception* in the general corpus, as shown in Figure [3.](#page-6-1)

Intensity: Figure [4](#page-7-0) shows the significant rise and fall in the use of intensifiers to modify *mental illness* in the psychology corpus, but no trend in the general corpus. Examining the top ranked adjective modifiers in each decade (Table [4](#page-21-0) and Table [7](#page-21-1) in Appendix [E\)](#page-21-2) reveals that "severe", "serious", "major", "chronic" come to be more associated with *mental illness* from the 1990s onwards. Although *mental health* is not frequently modified by intensifiers, as expected, "poor" and "positive" remain closely associated with it across the decades, with "maternal" becoming more associated with *mental health* from the 1990s onwards. Despite demonstrating a significant increase in its intensifier index in the psychology corpus, *perception* does not display intensifiers among its top adjective modifiers.

Figure [5](#page-7-1) shows a significant increasing trend in the intensity (arousal index) of *mental health*related words in both corpora. For *mental illness* and *perception*, the index increases significantly for the psychology corpus and only shows an increasing trend for *perception* in the general corpus.

<span id="page-6-1"></span>![](_page_6_Figure_5.jpeg)

Figure 3: Breadth score over five-year intervals (1970- 2014).

Thematic content: The target concepts, *mental health* and *mental illness*, and the control *perception*, become significantly more associated with pathology-related terms in the psychology corpus, and for all targets except for *mental health* in the general corpus, as shown in Figure [6.](#page-8-0) Inspecting the top ten ranked collocates for the main target terms (see Appendix [F\)](#page-22-0) shows the presence of only two of the 17 pathology-related terms in psychology and the general corpus ("disorder" and "treatment"), and no pathology-related terms among the top ranked collocates for the control. The diversity of terms among the top ranked collocates for *mental health* and *mental illness* indicate that more themes are present in the semantic space.

Salience: Figure [7](#page-8-1) illustrates that the relative frequencies rise significantly for both target concepts, *mental health* and *mental illness*, in both corpora. The relative frequency of *perception* increases significantly in the psychology corpus and shows relatively stability in the general corpus.

The significance of the trends was determined by examining standardized beta coefficients and their associated standard errors (see Table [17\)](#page-25-0). As shown in Appendix [G,](#page-23-0) the strongest effect sizes can be observed for the two target terms with breadth (both

<span id="page-7-0"></span>![](_page_7_Figure_0.jpeg)

Figure 4: Intensifier index for *mental illness* over the study period (1970-2016).

corpora), valence (decreasing for psychology and increasing for the general corpus), and for *mental illness* with intensity (both corpora). According to the Adjusted R<sup>2</sup> values in Tables [15](#page-23-1) and [16,](#page-24-0) with a few exceptions year has more explanatory power predicting the semantic indices for the target concepts than for the control concept.

### 6. Discussion

The present study implemented, for the first time, a new framework for evaluating lexical semantic change. Rather than assessing a single dimension of change or classifying it into a specific taxonomic category, the framework enables the concurrent evaluation of multiple dimensions of semantic change, each corresponding to a well-established dimension of referential or affective meaning. Evaluating semantic change along these dimensions simultaneously allows complex patterns of change to be disentangled and characterized, with possible applications in social science research.

The case study demonstrated a suite of computational methodologies for evaluating the framework's dimensions of change in an examination of *mental health* and *mental illness* motivated by social scientific research questions. Theorists working in sociology, psychology, psychiatry, and related fields have speculated on recent cultural shifts in these concepts, relying on overlapping and sometimes ill-defined notions of medicalization [\(Bröer](#page-10-9) [and Besseling,](#page-10-9) [2017;](#page-10-9) [Hofmann,](#page-12-17) [2016\)](#page-12-17), pathologiza-

<span id="page-7-1"></span>![](_page_7_Figure_6.jpeg)

Figure 5: Arousal index over the study period (1970- 2016).

tion [\(Brinkmann,](#page-10-8) [2016;](#page-10-8) [Frances,](#page-11-15) [2013\)](#page-11-15), psychiatrization [\(Beeker et al.,](#page-10-13) [2021;](#page-10-13) [Paris,](#page-12-18) [2020\)](#page-12-18), and stigmatization [\(Sartorius,](#page-13-13) [2007;](#page-13-13) [Schomerus et al.,](#page-13-14) [2022\)](#page-13-14). Little research has investigated these proposed trends or attempted to characterize them systematically. Our case study documents how a rigorous characterization of these conceptual changes might be conducted. Its findings point to the complexity of these changes, which would remain hidden had they been evaluated on a single dimension.

Regarding sentiment, we found paradoxical trends. Sentiment toward *mental illness* became more positive in the general corpus, supporting suggestions of destigmatization in the culture at large (e.g., [Schomerus et al.](#page-13-14) [2022\)](#page-13-14), while sentiment toward *mental health* and *mental illness* became more negative in the psychology corpus and for *mental health* in the general corpus. In the general corpus, *mental health* came to be used in narrower contexts. Nevertheless, the consistent rising trends for semantic breadth in the psychology corpus support previous claims of expanding meanings or horizontal concept creep [\(Brinkmann,](#page-10-8) [2016;](#page-10-8) [Horwitz and](#page-12-12) [Wakefield,](#page-12-12) [2007,](#page-12-12) [2012\)](#page-12-13) in academic psychology.

Furthermore, the analysis of intensity yielded clear patterns of change. The target concepts rose

<span id="page-8-0"></span>![](_page_8_Figure_0.jpeg)

Figure 6: Pathologization index over the study period (1970-2016).

on the arousal index in psychology, indicating that although only the semantic contexts for *mental health* increased in valence, both *mental health* and *mental illness* have become more emotionally animated or agitated. Only *mental health* showed no arousal trend in the general corpus. There was also evidence that *mental illness* has increasingly become more and then less modified by intensifier adjectives, in the psychology corpus, possibly in response to vertical concept creep, where the concept's meaning is stretched to refer to less severe phenomena [\(Haslam,](#page-11-6) [2016\)](#page-11-6) which may lead people to intensify the target concept (e.g., where *mental illness* comes to be modified as "serious" or "severe") to distinguish it from more expansive usages. This increase in severity modifiers and arousal may both reflect the same rising concern with and problematization of mental illness and health.

Finally, the tendency for the target concepts to become more associated with pathology-related terms (apart from for *mental health* in the general corpus) supports claims of rising pathologization [\(Brinkmann,](#page-10-8) [2016\)](#page-10-8). Notably, *mental illness* was most pathologized. Furthermore, the increase in relative frequency of the target concepts in both corpora is evidence of their rising cultural salience in

<span id="page-8-1"></span>![](_page_8_Figure_4.jpeg)

Figure 7: Normalized term frequencies for the general and psychology corpora (1970-2016).

psychology and the general domain. All indices for the control target, *perception*, showed significant trends in at least one corpus.

In sum, the multi-dimensional analysis suggests that in recent decades, as discourse on mental health and illness has become more prominent (supported by our salience index), concepts of mental health and illness have not so much de-stigmatized (sentiment) but have instead inflated (breadth) and become a growing focus of social concern and problematization (intensity) and increasingly seen through a medical lens (pathologization).

# 7. Conclusion

The current study presented a new computational framework that can be applied in the social sciences. Our contributions lie in (1) proposing a multidimensional framework to evaluate lexical semantic change in a way that economically integrates forms identified by historical linguists; (2), developing a set of computational methodologies to evaluate change on the newly proposed semantic dimensions; and (3) illustrating the computational framework by examining how *mental health* and *mental illness* have changed their meanings in two corpora, implying that the concepts are increasingly inflated, problematized and pathologized. The investigation illuminates the complexity of semantic and cultural change and provides new tools for studying them.

# 8. Limitations

Limitations inspire future directions. The procedures employed in the present study are simply a first implementation of the framework. Future research should refine its computational methodology by enhancing or replacing procedures with more robust or sensitive alterations. While the Warriner norms data we used (i) follows a rigorous and reliable rating procedure, (ii) are highly interpretable and (iii) have high face validity, future work might consider alternative methods in addition to closedvocabulary approaches [\(Eichstaedt et al.,](#page-11-16) [2021\)](#page-11-16). The current method could be compared against publicly-available BERT-based models fine-tuned for sentiment analysis [\(Goworek and Dubossarsky,](#page-11-17) [2024\)](#page-11-17), the VADER (a rule-based sentiment analysis tool; [Hutto and Gilbert,](#page-12-19) [2014\)](#page-12-19), or other sentimentemotion lexica [\(Boyd-Graber et al.,](#page-10-14) [2022;](#page-10-14) [Moham](#page-12-20)[mad,](#page-12-20) [2018\)](#page-12-20). Ideally, the approach will capture the nuanced sentiment contributions of the target word, which averaging the sentiment of contexts fails to capture [\(Goworek and Dubossarsky,](#page-11-17) [2024\)](#page-11-17). Robustness checks should be conducted on new methods by comparing its convergent validity against the existing one to evaluate the extent to which the alternative method correlates when applied to the same dataset. In addition, because the target term's semantic broadening is operationalized as the cosine *dis*similarity of the target's sentential contextual usages, it only differentiates between quantitatively (not qualitatively) different meanings. Future work should introduce more finegrained follow-up analyses by, for example, identifying hypernymy or using state-of-the-art word in context (WiC) models, like XL-LEXEME [\(Cas](#page-10-15)[sotti et al.,](#page-10-15) [2023\)](#page-10-15), which beats GPT-4 on the WiC task and BERT, mBERT, XLM-R on the graded change detection task [\(Periti and Tahmasebi,](#page-13-19) [2024\)](#page-13-19). It should also introduce a diachronic analysis to examine if the target's prototypical meaning has been diluted/intensified.

Additionally, while the present study includes a neutral control term, future work should evaluate how to (semi)automatically identify baseline semantic change in the global corpus (a stability axis), to normalize the semantic change of the target concepts against. A control condition where no change of meaning is expected could also be set up [\(Du](#page-11-18)[bossarsky et al.,](#page-11-18) [2017\)](#page-11-18) using a chronologically shuffled corpus so that the assumed changes become uniform and any change is an artefact (reflects ran-

dom "noise", not variation in time). To better capture themes, future work should develop a bottomup, not a top-down dictionary-based, approach by using topic modeling or clustering contextualized word embeddings [\(Montariol et al.,](#page-12-21) [2021\)](#page-12-21) and evaluating the target's proximity to the centroid of the semantic category cluster. These methods might reveal senses or domains without imposing a dictionary on the semantic space. It will also be crucial to consider LLM approaches for lexical semantic change [\(Wang and Choi,](#page-14-7) [2023\)](#page-14-7).

With regard to substantive studies, it will be important to make a general case for the framework by, ideally, finding an existing data set that includes annotated examples of semantic change for evaluation and estimation of the recall/coverage of the methods. In addition, our findings should be extended by applying the framework to a wider assortment of mental health-related concepts such as diagnostic terms (e.g., anxiety, depression, autism, obsessive-compulsive disorder, schizophrenia, attention-deficit hyperactivity disorder). Characterizing how specific diagnoses have altered their meanings in a differentiated, multi-dimensional manner will illuminate historical changes that have only been the focus of theoretical speculation and qualitative research to date (e.g., [Brinkmann,](#page-10-8) [2016;](#page-10-8) [Horwitz and Wakefield,](#page-12-12) [2007,](#page-12-12) [2012;](#page-12-13) [Parrott,](#page-13-20) [2023\)](#page-13-20). Future research can also capitalize on the new framework to explore possible causal relationships between dimensions, such as whether rising salience drives conceptual broadening [\(Haslam et al.,](#page-12-11) [2021\)](#page-12-11), whether rising breadth of mental illness-related concepts drives improvements in sentiment (a destigmatization process), and whether trade-offs exist (e.g., rising breadth may lead to shifts in intensity). Studies already point to related laws of semantic change, finding that sentiment change is associated with semantic change [\(Goworek and Dubossarsky,](#page-11-17) [2024\)](#page-11-17). Future studies should conduct fine-grained analyses on semantic shifts in discourse around mental health to examine how online group dynamics and macro social and cultural shifts (e.g., prevailing stereotypes and stigma towards social groups; see [Garg et al.,](#page-11-19) [2018;](#page-11-19) [Charlesworth and Hatzenbuehler,](#page-11-20) [2024;](#page-11-20) [Durrheim et al.,](#page-11-21) [2023\)](#page-11-21) contribute to observed semantic shifts and possibly the social transmission of mental disorders, shown in adolescent peer networks; [Alho et al.](#page-10-16) [\(2024\)](#page-10-16). Ideally studies will be conducted with many corpora (e.g., news, social media) with high frequencies of the target terms.

# 9. Ethics Statement

We do not identify any foreseeable risks or potential for harmful use of our work. Analyses use licensed data that are openly accessible for academic purposes, ensuring transparency and accountability.

### Acknowledgements

We thank the three anonymous ACL reviewers for their valuable feedback which substantially improved the paper. Our gratitude also extends to Professor Charles Kemp and Professor Yoshihisa Kashima for their guidance and feedback on earlier versions of the framework at PhD committee meetings and to Lea Frermann, Filip Miletic and Andrey ´ Kutuzov for indirect recommendations which benefited the work, and to Zheng Wei Lim for helping me troubleshoot this airXiv submission. This research is supported by Australian Research Council Discovery Project DP210103984 and by an Australian Government Research Training Program Scholarship.

### References

- <span id="page-10-10"></span>Eneko Agirre, Enrique Alfonseca, Keith Hall, Janyce Kravalova, Marius Pa¸sca, and Aitor Soroa. 2009. [A](https://doi.org/10.3115/1620754.1620758) [study on similarity and relatedness using distribu](https://doi.org/10.3115/1620754.1620758)[tional and wordnet-based approaches.](https://doi.org/10.3115/1620754.1620758) In *Proceedings of Human Language Technologies: The 2009 Annual Conference of the North American Chapter of the Association for Computational Linguistics*, page 19.
- <span id="page-10-12"></span>Reem Alatrash, Dominik Schlechtweg, Jonas Kuhn, and Sabine Schulte im Walde. 2020. [CCOHA: Clean cor](https://aclanthology.org/2020.lrec-1.859)[pus of historical American English.](https://aclanthology.org/2020.lrec-1.859) In *Proceedings of the Twelfth Language Resources and Evaluation Conference*, pages 6958–6966, Marseille, France. European Language Resources Association.
- <span id="page-10-16"></span>Jussi Alho, Mai Gutvilig, Ripsa Niemi, Kaisla Komulainen, Petri Böckerman, Roger T Webb, Marko Elovainio, and Christian Hakulinen. 2024. [Transmis](https://doi.org/10.1001/jamapsychiatry.2024.1126)[sion of mental disorders in adolescent peer networks.](https://doi.org/10.1001/jamapsychiatry.2024.1126) *JAMA psychiatry*.
- <span id="page-10-2"></span>Naveen Badathala, Abisek Rajakumar Kalarani, Tejpalsingh Siledar, and Pushpak Bhattacharyya. 2023. [A](https://doi.org/10.18653/v1/2023.findings-acl.26) [match made in heaven: A multi-task framework for](https://doi.org/10.18653/v1/2023.findings-acl.26) [hyperbole and metaphor detection.](https://doi.org/10.18653/v1/2023.findings-acl.26) In *Findings of the Association for Computational Linguistics: ACL 2023*, pages 388–401, Toronto, Canada. Association for Computational Linguistics.
- <span id="page-10-6"></span>Naomi Baes, Nick Haslam, and Ekaterina Vylomova. 2023a. [Semantic shifts in mental health-related con](https://doi.org/10.18653/v1/2023.lchange-1.13)[cepts.](https://doi.org/10.18653/v1/2023.lchange-1.13) In *Proceedings of the 4th Workshop on Computational Approaches to Historical Language Change*,

- pages 119–128, Singapore. Association for Computational Linguistics.
- <span id="page-10-7"></span>Naomi Baes, Ekaterina Vylomova, Michael J. Zyphur, and Nick Haslam. 2023b. [The semantic inflation of](https://doi.org/10.58734/plc-2023-0002) ["trauma" in psychology.](https://doi.org/10.58734/plc-2023-0002) *Psychology of Language and Communication*, 27(1):23–45.
- <span id="page-10-13"></span>Timo Beeker, China Mills, Dinesh Bhugra, Sanne te Meerman, Samuel Thoma, Martin Heinze, and Sebastian von Peter. 2021. [Psychiatrization of society:](https://doi.org/10.3389/fpsyt.2021.645556) [A conceptual framework and call for transdisciplinary](https://doi.org/10.3389/fpsyt.2021.645556) [research.](https://doi.org/10.3389/fpsyt.2021.645556) *Frontiers in Psychiatry*, 12:645556.
- <span id="page-10-4"></span>Andreas Blank. 1999. Why do new meanings occur? a cognitive typology of the motivations for lexical semantic change. In Andreas Blank and Peter Koch, editors, *Historical semantics and cognition*, pages 61–90. Mouton de Gruter.
- <span id="page-10-3"></span>Leonard Bloomfield. 1933. *Language*. Compton Printing Works Ltd.
- <span id="page-10-1"></span>Gemma Boleda. 2020. [Distributional semantics and lin](https://doi.org/10.1146/annurev-linguistics-011619-030303)[guistic theory.](https://doi.org/10.1146/annurev-linguistics-011619-030303) *Annual Review of Linguistics*, 6:213– 234.
- <span id="page-10-14"></span>Jordan Boyd-Graber, Samuel Carton, Shi Feng, Q. Vera Liao, Tania Lombrozo, Alison Smith-Renner, and Chenhao Tan. 2022. [Human-centered evaluation of](https://doi.org/10.18653/v1/2022.naacl-tutorials.4) [explanations.](https://doi.org/10.18653/v1/2022.naacl-tutorials.4) In *Proceedings of the 2022 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies: Tutorial Abstracts*, pages 26–32, Seattle, United States. Association for Computational Linguistics.
- <span id="page-10-8"></span>Svend Brinkmann. 2016. *Diagnostic Cultures: A Cultural Approach to the Pathologization of Modern Life*. Routledge.
- <span id="page-10-5"></span>Michel Bréal. 1897. *Essai de sémantique*. Hachette.
- <span id="page-10-9"></span>Christian Bröer and Broos Besseling. 2017. [Sadness](https://doi.org/10.1016/j.socscimed.2017.04.025) [or depression: Making sense of low mood and the](https://doi.org/10.1016/j.socscimed.2017.04.025) [medicalization of everyday life.](https://doi.org/10.1016/j.socscimed.2017.04.025) *Social Science & Medicine*, 183:28–36.
- <span id="page-10-0"></span>Lyle Campbell. 1999. *Historical linguistics: An introduction*, 1st mit press ed edition. MIT Press. Available online at [http://tscheer.free.](http://tscheer.free.fr/scan/Campbell%2098%20-%20Historical%20Linguistics.%20An%20Introduction.pdf) [fr/scan/Campbell%2098%20-%20Historical%](http://tscheer.free.fr/scan/Campbell%2098%20-%20Historical%20Linguistics.%20An%20Introduction.pdf) [20Linguistics.%20An%20Introduction.pdf](http://tscheer.free.fr/scan/Campbell%2098%20-%20Historical%20Linguistics.%20An%20Introduction.pdf).
- <span id="page-10-15"></span>Pierluigi Cassotti, Lucia Siciliani, Marco DeGemmis, Giovanni Semeraro, and Pierpaolo Basile. 2023. [XL-](https://aclanthology.org/2023.acl-short.135)[LEXEME: WiC pretrained model for cross-lingual](https://aclanthology.org/2023.acl-short.135) [LEXical sEMantic changE.](https://aclanthology.org/2023.acl-short.135) In *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)*, pages 1577–1585, Toronto, Canada. Association for Computational Linguistics.
- <span id="page-10-11"></span>Daniel Cer, Mona Diab, Eneko Agirre, Iñigo Lopez-Gazpio, and Lucia Specia. 2017. [SemEval-2017](https://doi.org/10.18653/v1/S17-2001) [task 1: Semantic textual similarity multilingual and](https://doi.org/10.18653/v1/S17-2001)

- [crosslingual focused evaluation.](https://doi.org/10.18653/v1/S17-2001) In *Proceedings of the 11th International Workshop on Semantic Evaluation (SemEval-2017)*, pages 1–14, Vancouver, Canada. Association for Computational Linguistics.
- <span id="page-11-20"></span>Tessa ES Charlesworth and Mark L Hatzenbuehler. 2024. [Mechanisms upholding the persistence of](https://doi.org/10.1038/s41598-024-61044-z) [stigma across 100 years of historical text.](https://doi.org/10.1038/s41598-024-61044-z) *Scientific Reports*, 14(1):11069.
- <span id="page-11-9"></span>Brodie C Dakin, Melanie J McGrath, Joshua J Rhee, and Nick Haslam. 2023. [Broadened concepts of harm](https://doi.org/10.1177/19485506221076692) [appear less serious.](https://doi.org/10.1177/19485506221076692) *Social Psychological and Personality Science*, 14(1):72–83.
- <span id="page-11-13"></span>Mark Davies. 2008. The corpus of contemporary american english (COCA). [https://www.](https://www.english-corpora.org/coca/) [english-corpora.org/coca/](https://www.english-corpora.org/coca/).
- <span id="page-11-12"></span>Mark Davies. 2010. The corpus of historical american english (coha). Available online at [https://www.](https://www.english-corpora.org/coha/) [english-corpora.org/coha/](https://www.english-corpora.org/coha/).
- <span id="page-11-11"></span>Simon De Deyne, Daniel J. Navarro, Amy Perfors, Marc Brysbaert, and Gert Storms. 2019. [The "small](https://doi.org/10.3758/s13428-018-1115-7) [world of words" english word association norms for](https://doi.org/10.3758/s13428-018-1115-7) [over 12,000 cue words.](https://doi.org/10.3758/s13428-018-1115-7) *Behavior Research Methods*, 51(3):987–1006.
- <span id="page-11-4"></span>Jader Martins Camboim de Sá, Marcos Da Silveira, and Cédric Pruski. 2024. [Survey in characterization of](https://doi.org/10.48550/arXiv.2402.19088) [semantic change.](https://doi.org/10.48550/arXiv.2402.19088) *arXiv preprint arXiv:2402.19088*.
- <span id="page-11-22"></span>Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. Bert: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long Papers)*, pages 4171–4186.
- <span id="page-11-3"></span>Liviu P. Dinu, Ioan-Bogdan Iordache, Ana Sabina Uban, and Marcos Zampieri. 2021. [A computational ex](https://doi.org/10.18653/v1/2021.findings-emnlp.296)[ploration of pejorative language in social media.](https://doi.org/10.18653/v1/2021.findings-emnlp.296) In *Findings of the Association for Computational Linguistics: EMNLP 2021*, pages 3493–3498, Punta Cana, Dominican Republic. Association for Computational Linguistics.
- <span id="page-11-18"></span>Haim Dubossarsky, Daphna Weinshall, and Eitan Grossman. 2017. [Outta control: Laws of semantic change](https://doi.org/10.18653/v1/D17-1118) [and inherent biases in word representation models.](https://doi.org/10.18653/v1/D17-1118) In *Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing*, pages 1136–1145, Copenhagen, Denmark. Association for Computational Linguistics.
- <span id="page-11-14"></span>Paul Dudgeon. 2017. [Some improvements in confi](https://link.springer.com/article/10.1007/s11336-017-9563-z#auth-Paul-Dudgeon-Aff1)[dence intervals for standardized regression coeffi](https://link.springer.com/article/10.1007/s11336-017-9563-z#auth-Paul-Dudgeon-Aff1)[cients.](https://link.springer.com/article/10.1007/s11336-017-9563-z#auth-Paul-Dudgeon-Aff1) *Psychometrika*, 82:928–951.
- <span id="page-11-21"></span>Kevin Durrheim, Maria Schuld, Martin Mafunda, and Sindisiwe Mazibuko. 2023. [Using word embeddings](https://doi.org/10.1111/bjso.12560) [to investigate cultural biases.](https://doi.org/10.1111/bjso.12560) *British Journal of Social Psychology*, 62(1):617–629.

- <span id="page-11-16"></span>Johannes C Eichstaedt, Margaret L Kern, David B Yaden, H Andrew Schwartz, Salvatore Giorgi, Gregory Park, Courtney A Hagan, Victoria A Tobolsky, Laura K Smith, Anneke Buffone, et al. 2021. [Closed](https://doi.org/10.1037/met0000349)[and open-vocabulary approaches to text analysis: A](https://doi.org/10.1037/met0000349) [review, quantitative comparison, and recommenda](https://doi.org/10.1037/met0000349)[tions.](https://doi.org/10.1037/met0000349) *Psychological Methods*, 26(4):398.
- <span id="page-11-2"></span>Lauren Fonteyn and Enrique Manjavacas. 2021. [Adjust](https://ceur-ws.org/Vol-2989/long_paper26.pdf)[ing scope: A computational approach to case-driven](https://ceur-ws.org/Vol-2989/long_paper26.pdf) [research on semantic change.](https://ceur-ws.org/Vol-2989/long_paper26.pdf) In *CHR*, pages 280– 298.
- <span id="page-11-15"></span>Allen Frances. 2013. *Saving Normal: An Insider's Revolt Against Out-of-Control Psychiatric Diagnosis, DSM-5, Big Pharma, and the Medicalization of Ordinary Life*. HarperCollins Publishers (Australia) Pty. Ltd., Level 13, 201 Elizabeth Street, Sydney, NSW 2000, Australia.
- <span id="page-11-7"></span>Frank Furedi. 2016. [The cultural underpinning of con](https://doi.org/10.1080/1047840X.2016.1111120)[cept creep.](https://doi.org/10.1080/1047840X.2016.1111120) *Psychological Inquiry*, 27(1):34–39.
- <span id="page-11-19"></span>Nikhil Garg, Londa Schiebinger, Dan Jurafsky, and James Zou. 2018. [Word embeddings quantify 100](https://doi.org/10.1073/pnas.172034711) [years of gender and ethnic stereotypes.](https://doi.org/10.1073/pnas.172034711) *Proceedings of the National Academy of Sciences*, 115(16):E3635– E3644.
- <span id="page-11-5"></span>Dirk Geeraerts. 2010. *Theories of lexical semantics*. Oxford University Press.
- <span id="page-11-17"></span>Roksana Goworek and Haim Dubossarsky. 2024. [To](https://aclanthology.org/2024.eacl-srw.28)[ward sentiment aware semantic change analysis.](https://aclanthology.org/2024.eacl-srw.28) In *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics: Student Research Workshop*, pages 350– 357.
- <span id="page-11-1"></span>William L Hamilton, Jure Leskovec, and Dan Jurafsky. 2016a. [Cultural shift or linguistic drift? comparing](https://aclanthology.org/D16-1229) [two computational measures of semantic change.](https://aclanthology.org/D16-1229) In *Proceedings of the conference on empirical methods in natural language processing. Conference on empirical methods in natural language processing*, volume 2016, page 2116. NIH Public Access.
- <span id="page-11-0"></span>William L. Hamilton, Jure Leskovec, and Dan Jurafsky. 2016b. [Diachronic word embeddings reveal statisti](https://doi.org/10.18653/v1/P16-1141)[cal laws of semantic change.](https://doi.org/10.18653/v1/P16-1141) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 1489–1501, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-11-6"></span>Nick Haslam. 2016. [Concept creep: Psychology's ex](https://doi.org/10.1080/1047840X.2016.1082418)[panding concepts of harm and pathology.](https://doi.org/10.1080/1047840X.2016.1082418) *Psychological Inquiry*, 27(1):1–17.
- <span id="page-11-10"></span>Nick Haslam and Naomi Baes. 2024. [What should we](https://doi.org/10.1371/journal.pmen.0000032) [call mental ill health? historical shifts in the popular](https://doi.org/10.1371/journal.pmen.0000032)[ity of generic terms.](https://doi.org/10.1371/journal.pmen.0000032) *PLOS Ment Health*, 1(1).
- <span id="page-11-8"></span>Nick Haslam, Brodie C Dakin, Fabian Fabiano, Melanie J McGrath, Joshua Rhee, Ekaterina Vylomova, Morgan Weaving, and Melissa A Wheeler.

- 2020. [Harm inflation: Making sense of concept creep.](https://doi.org/10.1080/10463283.2020.1796080) *European Review of Social Psychology*, 31(1):254– 286.
- <span id="page-12-11"></span>Nick Haslam, Ekaterina Vylomova, Michael J. Zyphur, and Yoshihisa Kashima. 2021. [The cultural](https://doi.org/10.1037/amp0000847) [dynamics of concept creep.](https://doi.org/10.1037/amp0000847) *American Psychologist*, 76(6):1013–1026.
- <span id="page-12-6"></span>Simon Hengchen, Nina Tahmasebi, Dominik Schlechtweg, and Haim Dubossarsky. 2021. [Chal](https://doi.org/10.5281/zenodo.5040322)[lenges for computational lexical semantic change.](https://doi.org/10.5281/zenodo.5040322) In Nina Tahmasebi, Lars Borin, Adam Jatowt, Yang Xu, and Simon Hengchen, editors, *Computational approaches to semantic change*, pages 341–372. Language Science Press, Berlin.
- <span id="page-12-17"></span>Bjørn Hofmann. 2016. [Medicalization and overdiagno](https://doi.org/10.1007/s11019-016-9693-6)[sis: Different but alike.](https://doi.org/10.1007/s11019-016-9693-6) *Medicine, Health Care and Philosophy*, 19(2):253–264.
- <span id="page-12-12"></span>Allan V. Horwitz and Jerome C. Wakefield. 2007. *The loss of sadness: How psychiatry transformed normal sorrow into depressive disorder*. Oxford University Press.
- <span id="page-12-13"></span>Allan V. Horwitz and Jerome C. Wakefield. 2012. *All we have to fear: Psychiatry's transformation of natural anxieties into mental disorders*. Oxford University Press.
- <span id="page-12-19"></span>Clayton Hutto and Eric Gilbert. 2014. [Vader: A parsi](https://doi.org/10.1609/icwsm.v8i1.14550)[monious rule-based model for sentiment analysis of](https://doi.org/10.1609/icwsm.v8i1.14550) [social media text.](https://doi.org/10.1609/icwsm.v8i1.14550) In *Proceedings of the International AAAI Conference on Web and Social Media*, pages 216–225.
- <span id="page-12-16"></span>Andrew T. Jebb, Louis Tay, Wei Wang, and Qiming Huang. 2015. [Time series analysis for psychological](https://doi.org/10.3389/fpsyg.2015.00727) [research: Examining and forecasting change.](https://doi.org/10.3389/fpsyg.2015.00727) *Frontiers in Psychology*, 6.
- <span id="page-12-2"></span>Daniel Jurafsky and James H. Martin. 2023. *[Vector](https://web.stanford.edu/~jurafsky/slp3/6.pdf) [Semantics and Embeddings](https://web.stanford.edu/~jurafsky/slp3/6.pdf)*. Draft of February 3, 2024. Draft chapters available online: [https://web.](https://web.stanford.edu/~jurafsky/slp3/) [stanford.edu/~jurafsky/slp3/](https://web.stanford.edu/~jurafsky/slp3/).
- <span id="page-12-8"></span>Li Kong, Chuanyi Li, Jidong Ge, Bin Luo, and Vincent Ng. 2020. [Identifying exaggerated language.](https://doi.org/10.18653/v1/2020.emnlp-main.571) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 7024–7034, Online. Association for Computational Linguistics.
- <span id="page-12-0"></span>Andrey Kutuzov, Lilja Øvrelid, Terrence Szymanski, and Erik Velldal. 2018. [Diachronic word embeddings](https://aclanthology.org/C18-1117) [and semantic shifts: a survey.](https://aclanthology.org/C18-1117) In *Proceedings of the 27th International Conference on Computational Linguistics*, pages 1384–1397, Santa Fe, New Mexico, USA. Association for Computational Linguistics.
- <span id="page-12-5"></span>Andrey Kutuzov, Erik Velldal, and Lilja Øvrelid. 2022. [Contextualized embeddings for semantic change de](https://doi.org/https://doi.org/10.3384/nejlt.2000-1533.2022.3478)[tection: Lessons learned.](https://doi.org/https://doi.org/10.3384/nejlt.2000-1533.2022.3478) In *Northern European Journal of Language Technology, Volume 8*, Copenhagen, Denmark. Northern European Association of Language Technology.

- <span id="page-12-15"></span>Lev Lafayette, Greg Sauter, Linh Vu, and Bernard Meade. 2016. Spartan performance and flexibility: An hpc-cloud chimera. *OpenStack Summit, Barcelona*, 27:6.
- <span id="page-12-10"></span>David E. Levari, Daniel T. Gilbert, Timothy D. Wilson, Baruch Sievers, David M. Amodio, and Thalia Wheatley. 2018. [Prevalence-induced concept change](https://doi.org/10.1126/science.aap8731) [in human judgment.](https://doi.org/10.1126/science.aap8731) *Science*, 360(6396):1465–1467.
- <span id="page-12-22"></span>Xiaodong Liu, Pengcheng He, Weizhu Chen, and Jianfeng Gao. 2019. [Multi-task deep neural networks for](https://doi.org/10.18653/v1/P19-1441) [natural language understanding.](https://doi.org/10.18653/v1/P19-1441) In *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics*, pages 4487–4496, Florence, Italy. Association for Computational Linguistics.
- <span id="page-12-9"></span>Yu Luo, Dan Jurafsky, and Beth Levin. 2019. [From in](https://doi.org/10.18653/v1/W19-4701)[sanely jealous to insanely delicious: Computational](https://doi.org/10.18653/v1/W19-4701) [models for the semantic bleaching of english intensi](https://doi.org/10.18653/v1/W19-4701)[fiers.](https://doi.org/10.18653/v1/W19-4701) In *Proceedings of the 1st International Workshop on Computational Approaches to Historical Language Change*, pages 1–13.
- <span id="page-12-1"></span>Christopher D Manning. 2022. Human language understanding & reasoning. *Daedalus*, 151(2):127–138.
- <span id="page-12-7"></span>Rowan Hall Maudslay and Simone Teufel. 2022. [Metaphorical polysemy detection: Conventional](https://aclanthology.org/2022.coling-1.7) [metaphor meets word sense disambiguation.](https://aclanthology.org/2022.coling-1.7) In *Proceedings of the 29th International Conference on Computational Linguistics*, pages 65–77, Gyeongju, Republic of Korea. International Committee on Computational Linguistics.
- <span id="page-12-3"></span>Tomas Mikolov, Kai Chen, Gregory S. Corrado, and Jeffrey Dean. 2013. [Efficient estimation of word](https://api.semanticscholar.org/CorpusID:5959482) [representations in vector space.](https://api.semanticscholar.org/CorpusID:5959482) In *International Conference on Learning Representations*.
- <span id="page-12-20"></span>Saif Mohammad. 2018. [Obtaining reliable human rat](https://doi.org/10.18653/v1/P18-1017)[ings of valence, arousal, and dominance for 20,000](https://doi.org/10.18653/v1/P18-1017) [English words.](https://doi.org/10.18653/v1/P18-1017) In *Proceedings of the 56th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 174–184, Melbourne, Australia. Association for Computational Linguistics.
- <span id="page-12-4"></span>Stefano Montanelli and Fabio Periti. 2023. [A survey](http://arxiv.org/abs/2304.01666) [on contextualised semantic shift detection.](http://arxiv.org/abs/2304.01666) *arXiv*, arXiv:2304.01666.
- <span id="page-12-21"></span>Syrielle Montariol, Matej Martinc, and Lidia Pivovarova. 2021. [Scalable and interpretable semantic change](https://doi.org/10.18653/v1/2021.naacl-main.369) [detection.](https://doi.org/10.18653/v1/2021.naacl-main.369) In *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pages 4642–4652.
- <span id="page-12-14"></span>Charles Egerton Osgood, William H May, and Murray S Miron. 1975. *Cross-Cultural Universals of Affective Meaning*. University of Illionois Press.
- <span id="page-12-18"></span>Joel Paris. 2020. *Overdiagnosis in Psychiatry: How Modern Psychiatry Lost Its Way While Creating a Diagnosis for Almost All of Life's Misfortunes*. Oxford University Press.

- <span id="page-13-20"></span>Scott Parrott. 2023. [PTSD in the news: Media framing,](https://doi.org/10.1177/19312431221146757) [stigma, and myths about mental illness.](https://doi.org/10.1177/19312431221146757) *Electronic News*, 17(3):181–197.
- <span id="page-13-2"></span>Jeffrey Pennington, Richard Socher, and Christopher D Manning. 2014. [Glove: Global vectors for word rep](https://aclanthology.org/D14-1162)[resentation.](https://aclanthology.org/D14-1162) In *Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP)*, pages 1532–1543.
- <span id="page-13-19"></span>Francesco Periti and Nina Tahmasebi. 2024. [A sys](https://doi.org/10.48550/arXiv.2402.12011)[tematic comparison of contextualized word embed](https://doi.org/10.48550/arXiv.2402.12011)[dings for lexical semantic change.](https://doi.org/10.48550/arXiv.2402.12011) *arXiv preprint arXiv:2402.12011*.
- <span id="page-13-18"></span>Ivan Jacob Agaloos Pesigan, Rong Wei Sun, and Shu Fai Cheung. 2023. [betadelta and betasandwich: Con](https://doi.org/10.1080/00273171.2023.2201277)[fidence intervals for standardized regression coef](https://doi.org/10.1080/00273171.2023.2201277)[ficients in r.](https://doi.org/10.1080/00273171.2023.2201277) *Multivariate Behavioral Research*, 58(6):1183–1186.
- <span id="page-13-9"></span>Steven Pinker. 2011. *The Better Angels of Our Nature: Why Violence Has Declined*. Viking Books.
- <span id="page-13-16"></span>Nils Reimers and Iryna Gurevych. 2019. [Sentence-](https://doi.org/10.18653/v1/D19-1410)[BERT: Sentence embeddings using Siamese BERT](https://doi.org/10.18653/v1/D19-1410)[networks.](https://doi.org/10.18653/v1/D19-1410) In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 3982–3992, Hong Kong, China. Association for Computational Linguistics.
- <span id="page-13-4"></span>Anna Rogers, Olga Kovaleva, and Anna Rumshisky. 2020. [A primer in BERTology: What we know about](https://doi.org/10.1162/tacl_a_00349) [how BERT works.](https://doi.org/10.1162/tacl_a_00349) *Transactions of the Association for Computational Linguistics*, 8:842–866.
- <span id="page-13-15"></span>James A. Russell. 2003. [Core affect and the psychologi](https://doi.org/10.1037/0033-295X.110.1.145)[cal construction of emotion.](https://doi.org/10.1037/0033-295X.110.1.145) *Psychological Review*, 110(1):145–172.
- <span id="page-13-22"></span>Victor Sanh, Lysandre Debut, Julien Chaumond, and Thomas Wolf. 2019. [Distilbert, a distilled version](https://arxiv.org/abs/1910.01108) [of bert: smaller, faster, cheaper and lighter.](https://arxiv.org/abs/1910.01108) *ArXiv*, abs/1910.01108.
- <span id="page-13-13"></span>Norman Sartorius. 2007. [Stigma and mental health.](https://doi.org/10.1016/S0140-6736(07)61245-8) *The Lancet*, 370(9590):810–811.
- <span id="page-13-6"></span>Nina Schneidermann, Daniel Hershcovich, and Bolette Pedersen. 2023. [Probing for hyperbole in pre-trained](https://doi.org/https://doi.org/10.18653/v1/2023.acl-srw.30) [language models.](https://doi.org/https://doi.org/10.18653/v1/2023.acl-srw.30) In *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 4: Student Research Workshop)*, pages 200–211, Toronto, Canada. Association for Computational Linguistics.
- <span id="page-13-14"></span>Georg Schomerus, Stephanie Schindler, Christian Sander, Eva Baumann, and Matthias C Angermeyer. 2022. [Changes in mental illness stigma over 30 years–](https://doi.org/10.1192/j.eurpsy.2022.2337) [improvement, persistence, or deterioration?](https://doi.org/10.1192/j.eurpsy.2022.2337) *European Psychiatry*, 65(1):e78.

- <span id="page-13-3"></span>Vered Shwartz, Yoav Goldberg, and Ido Dagan. 2016. [Improving hypernymy detection with an integrated](https://doi.org/10.18653/v1/P16-1226) [path-based and distributional method.](https://doi.org/10.18653/v1/P16-1226) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 2389–2398, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-13-21"></span>Kaitao Song, Xu Tan, Tao Qin, Jianfeng Lu, and Tie-Yan Liu. 2020. [MPNet: Masked and permuted pre](https://arxiv.org/abs/2004.09297)[training for language understanding.](https://arxiv.org/abs/2004.09297) *Advances in neural information processing systems*, 33:16857– 16867.
- <span id="page-13-10"></span>Cass R. Sunstein. 2018. The power of the normal. *SSRN*. SSRN Scholarly Paper ID 3239204. Social Science Research Network. [https://doi.org/10.](https://doi.org/10.2139/ssrn.3239204) [2139/ssrn.3239204](https://doi.org/10.2139/ssrn.3239204).
- <span id="page-13-0"></span>Nina Tahmasebi, Lars Borin, and Adam Jatowt. 2021. [Survey of computational approaches to lexical seman](https://doi.org/10.5281/zenodo.5040302)[tic change detection.](https://doi.org/10.5281/zenodo.5040302) In Nina Tahmasebi, Lars Borin, Adam Jatowt, Yang Xu, and Simon Hengchen, editors, *Computational approaches to semantic change*, pages 1–91. Language Science Press, Berlin.
- <span id="page-13-1"></span>Xuri Tang. 2018. [A state-of-the-art of semantic](https://doi.org/10.1017/S1351324918000220) [change computation.](https://doi.org/10.1017/S1351324918000220) *Natural Language Engineering*, 24(5):649–676.
- <span id="page-13-7"></span>Yufei Tian, Arvind Krishna Sridhar, and Nanyun Peng. 2021. [Hypogen: Hyperbole generation with com](https://doi.org/10.18653/v1/2021.findings-emnlp.136)[monsense and counterfactual knowledge.](https://doi.org/10.18653/v1/2021.findings-emnlp.136) In *Findings of the Association for Computational Linguistics: EMNLP 2021*, pages 1583–1593.
- <span id="page-13-11"></span>Jesse S. Y. Tse and Nick Haslam. 2021. Inclusiveness of the concept of mental disorder and differences in help-seeking between asian and white americans. *Frontiers in Psychology*, 12. [https://www.frontiersin.org/articles/](https://www.frontiersin.org/articles/10.3389/fpsyg.2021.699750) [10.3389/fpsyg.2021.699750](https://www.frontiersin.org/articles/10.3389/fpsyg.2021.699750).
- <span id="page-13-17"></span>Hayato Tsukagoshi, Ryohei Sasano, and Koichi Takeda. 2022. [Comparison and combination of sentence em](https://doi.org/10.18653/v1/2022.starsem-1.12)[beddings derived from different supervision signals.](https://doi.org/10.18653/v1/2022.starsem-1.12) In *Proceedings of the 11th Joint Conference on Lexical and Computational Semantics*, pages 139–150, Seattle, Washington. Association for Computational Linguistics.
- <span id="page-13-8"></span>Stephen Ullmann. 1962. *Semantics: An Introduction to the Science of Meaning*. Blackwell.
- <span id="page-13-12"></span>Ekaterina Vylomova and Nick Haslam. 2021. [Semantic](https://doi.org/10.5281/zenodo.5040304) [changes in harm-related concepts in english.](https://doi.org/10.5281/zenodo.5040304) In Nina Tahmasebi, Lars Borin, Adam Jatowt, Yue Xu, and Simon Hengchen, editors, *Computational Approaches to Semantic Change*. Language Science Press.
- <span id="page-13-5"></span>Ekaterina Vylomova, Sean Murphy, and Nick Haslam. 2019. [Evaluation of semantic change of harm-related](https://doi.org/10.18653/v1/W19-4704) [concepts in psychology.](https://doi.org/10.18653/v1/W19-4704) In *Proceedings of the 1st International Workshop on Computational Approaches to Historical Language Change*, pages 29–34.

- <span id="page-14-0"></span>Ekaterina Vylomova, Laura Rimell, Trevor Cohn, and Timothy Baldwin. 2016. [Take and took, gaggle and](https://doi.org/10.18653/v1/P16-1158) [goose, book and read: Evaluating the utility of vector](https://doi.org/10.18653/v1/P16-1158) [differences for lexical relation learning.](https://doi.org/10.18653/v1/P16-1158) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 1671–1682, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-14-7"></span>Ruiyu Wang and Matthew Choi. 2023. [Large language](https://doi.org/10.48550/arXiv.2312.06002) [models on lexical semantic change detection: An](https://doi.org/10.48550/arXiv.2312.06002) [evaluation.](https://doi.org/10.48550/arXiv.2312.06002) *arXiv preprint arXiv:2312.06002*.
- <span id="page-14-8"></span>Wenhui Wang, Furu Wei, Li Dong, Hangbo Bao, Nan Yang, and Ming Zhou. 2020. Minilm: Deep selfattention distillation for task-agnostic compression of pre-trained transformers. *Advances in Neural Information Processing Systems*, 33:5776–5788.
- <span id="page-14-5"></span>Amy Beth Warriner, Victor Kuperman, and Marc Brysbaert. 2013. [Norms of valence, arousal, and domi](https://doi.org/10.3758/s13428-012-0314-x)[nance for 13,915 english lemmas.](https://doi.org/10.3758/s13428-012-0314-x) *Behavior Research Methods*, 45(4):1191–1207.
- <span id="page-14-2"></span>Melissa A Wheeler, Melanie J McGrath, and Nick Haslam. 2019. [Twentieth century morality: The rise](https://doi.org/10.1371/journal.pone.0212267) [and fall of moral concepts from 1900 to 2007.](https://doi.org/10.1371/journal.pone.0212267) *PLOS ONE*, 14(2):e0212267.
- <span id="page-14-4"></span>WHO. 2021. [Comprehensive mental health action plan](https://iris.who.int/bitstream/handle/10665/345301/9789240031029-eng.pdf) [2013–2030.](https://iris.who.int/bitstream/handle/10665/345301/9789240031029-eng.pdf)
- <span id="page-14-3"></span>Yu Xiao, Naomi Baes, Ekaterina Vylomova, and Nick Haslam. 2023. [Have the concepts of 'anxiety' and](https://doi.org/10.1371/journal.pone.0288027) ['depression' been normalized or pathologized? a cor](https://doi.org/10.1371/journal.pone.0288027)[pus study of historical semantic change.](https://doi.org/10.1371/journal.pone.0288027) *PLOS ONE*, 18(6):e0288027.
- <span id="page-14-1"></span>Arda Yüksel, Berke Ugurlu, and Aykut Koç. 2021. ˘ [Se](https://ieeexplore.ieee.org/document/9581306)[mantic change detection with gaussian word embed](https://ieeexplore.ieee.org/document/9581306)[dings.](https://ieeexplore.ieee.org/document/9581306) *IEEE/ACM Transactions on Audio, Speech, and Language Processing*, 29:3349–3361.

### A. Appendix A

<span id="page-14-6"></span>To elaborate on what a word being low or high "arousal" or "valence" means, [Warriner et al.](#page-14-5) [\(2013\)](#page-14-5) defined them in the following way when (valid) participants made direct judgements of the large sample of words on the measured attributes (*n* = 419: valence; *n* = 448: arousal; 16-87 years; majority were female (60%), English native language speakers, held a college degree):

- Valence: *"You are invited to take part in the study that [...] concerns how people respond to different types of words. You will use a scale to rate how you felt while reading each word. [...] The scale ranges from 1 (happy) to 9 (unhappy). At one extreme of this scale, you are happy, pleased, satisfied, contented, hopeful. When you feel completely happy you should indicate this by choosing rating 1. The other end of the scale is when you feel completely unhappy, annoyed, unsatisfied, melancholic, despaired, or bored. You can indicate feeling completely unhappy by selecting 9. The numbers also allow you to describe intermediate feelings of pleasure, by selecting any of the other feelings. If you feel completely neutral, neither happy nor sad, select the middle of the scale (rating 5)."*
- Arousal: *"You are invited to take part in the study that [...] concerns how people respond to different types of words. You will use a scale to rate how you felt while reading each word. [...] The scale ranges from 1 (excited) to 9 (calm). At one extreme of this scale, you are stimulated, excited, frenzied, jittery, wideawake, or aroused. When you feel completely aroused you should indicate this by choosing rating 1. The other end of the scale is when you feel completely relaxed, calm, sluggish, dull, sleepy, or unaroused. You can indicate feeling completely calm by selecting 9. The numbers also allow you to describe intermediate feelings of calmness/arousal, by selecting any of the other feelings. If you feel completely neutral, not excited nor at all calm, select the middle of the scale (rating 5)."*

### B. Appendix B

<span id="page-15-0"></span>Total lines where target term appears in the text for both corpora (1970-2016): for the General corpus: mental\_health = 3,233; mental\_illness = 1,559, perception = 9,440; for the Psychology corpus (1970- 2016): mental\_health = 26,482; mental\_illness = 4,219, perception = 54,694.

![](_page_15_Figure_2.jpeg)

Figure 8: Annual counts of articles where target terms appear in the main text (1970-2016). *Note:* Top three panels = Psychology corpus; bottom three panels = General corpus.

### C. Appendix C

### <span id="page-15-1"></span>Breadth Model Selection

The top three (pre-trained) sentence transformer models were chosen, ranked by their performance in embedding sentences.[11](#page-15-2) The best-performing model on the semantic textual similarity benchmark,[12](#page-15-3) Multi-Task Deep Neural Network [\(Liu](#page-12-22) [et al.,](#page-12-22) [2019\)](#page-12-22), was unavailable.[13](#page-15-4) See Table [2](#page-16-0) for descriptive statistics of models.

- "all-mpnet-base-v2" [14](#page-15-5) is maintained by the SentenceTransformers community and excels in encoding sentences across 14 diverse tasks from different domains using the MPNet (Masked and Permuted Pre-training for Language Understanding) [\(Song et al.,](#page-13-21) [2020\)](#page-13-21) architecture.
- "all-distilroberta-v1" [15](#page-15-6) uses a distilled version of "distilroberta-base" [\(Sanh et al.,](#page-13-22) [2019\)](#page-13-22), based on BERT architecture, employing knowledge distillation during pre-training and a triple loss (language modeling, distillation and cosine-distance losses) to leverage the inductive biases of LLMs during pre-training.
- "all-MiniLM-L6-v2" [16](#page-15-7) uses the MiniLM architecture [\(Wang et al.,](#page-14-8) [2020\)](#page-14-8) employing deep self-attention distillation (using self-attention relation distillation for task-agnostic compression of pre-trained Transformers).
- Additionally, "bert-base-uncased" [17](#page-15-8) [\(Devlin](#page-11-22) [et al.,](#page-11-22) [2019\)](#page-11-22) was included for comparison, although its network structure prohibits the direct comparison of sentence embeddings, and BERT maps sentences to a vector space that is unsuitable for use with common similarity measures and performs below average GloVe embeddings on STS tasks [\(Reimers](#page-13-16) [and Gurevych,](#page-13-16) [2019\)](#page-13-16).

<span id="page-15-2"></span><sup>11</sup>[https://www.sbert.net/docs/pretrained\\_models.](https://www.sbert.net/docs/pretrained_models.html) [html](https://www.sbert.net/docs/pretrained_models.html)

<span id="page-15-3"></span><sup>12</sup>[https://paperswithcode.com/sota/](https://paperswithcode.com/sota/semantic-textual-similarity-on-sts-benchmark) [semantic-textual-similarity-on-sts-benchmark](https://paperswithcode.com/sota/semantic-textual-similarity-on-sts-benchmark)

<span id="page-15-5"></span><span id="page-15-4"></span><sup>13</sup>See <https://github.com/namisan/mt-dnn>

<sup>14</sup>"all-mpnet-base-v2" from Hugging Face, sentence-transformers: [https://huggingface.co/](https://huggingface.co/sentence-transformers/all-mpnet-base-v2) [sentence-transformers/all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)

<span id="page-15-6"></span><sup>15</sup>"all-distilroberta-v1" from Hugging Face, sentence-transformers: [https://huggingface.co/](https://huggingface.co/sentence-transformers/all-distilroberta-v1) [sentence-transformers/all-distilroberta-v1](https://huggingface.co/sentence-transformers/all-distilroberta-v1)

<span id="page-15-7"></span><sup>16</sup>"all-MiniLM-L6-v2": [https://huggingface.co/](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

<span id="page-15-8"></span><sup>17</sup>"bert-base-uncased": [https://huggingface.co/](https://huggingface.co/google-bert/bert-base-uncased) [google-bert/bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased)

<span id="page-16-0"></span>

| Model Info                | all-mpnet-base<br>v2*                                                                                                                                                                                                                                                                          | all-distilroberta<br>v1*                                                                                                                                                                                    | all-MiniLM-L6-<br>v2*                                                                                       | bert-base-uncased                                                                                                                                                        |  |  |
|---------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--|--|
| Accuracy+                 | 69.57                                                                                                                                                                                                                                                                                          | 68.73                                                                                                                                                                                                       | 68.06                                                                                                       | NA                                                                                                                                                                       |  |  |
| Size                      | 420 MB                                                                                                                                                                                                                                                                                         | 290 MB                                                                                                                                                                                                      | 80 MB                                                                                                       | 80 MB                                                                                                                                                                    |  |  |
| Case<br>Sensi<br>tive     | Yes                                                                                                                                                                                                                                                                                            | Yes                                                                                                                                                                                                         | Yes                                                                                                         | Yes                                                                                                                                                                      |  |  |
| Vocabulary                | 30,527                                                                                                                                                                                                                                                                                         | 50,264                                                                                                                                                                                                      | 30,522                                                                                                      | 30,522                                                                                                                                                                   |  |  |
| Max<br>Seq<br>Length      | 384                                                                                                                                                                                                                                                                                            | 512                                                                                                                                                                                                         | 256                                                                                                         | 512                                                                                                                                                                      |  |  |
|                           | Mean Pooling (Tokens)                                                                                                                                                                                                                                                                          |                                                                                                                                                                                                             |                                                                                                             | CLS pooling                                                                                                                                                              |  |  |
| Pooling<br>Dimensions     | 768                                                                                                                                                                                                                                                                                            | 768                                                                                                                                                                                                         | 384                                                                                                         | 768                                                                                                                                                                      |  |  |
| Layers                    | 12                                                                                                                                                                                                                                                                                             | 6                                                                                                                                                                                                           | 6                                                                                                           | 12                                                                                                                                                                       |  |  |
| Heads                     | 12                                                                                                                                                                                                                                                                                             | 12                                                                                                                                                                                                          | 12                                                                                                          | 12                                                                                                                                                                       |  |  |
| Parameters                | 33M                                                                                                                                                                                                                                                                                            | 82.1M                                                                                                                                                                                                       | 33M                                                                                                         | 110M                                                                                                                                                                     |  |  |
| Training<br>Data          | _net, ms_marco)                                                                                                                                                                                                                                                                                | >1B training pairs, sent. (3 data sets: wikihow, code_search<br>NA                                                                                                                                          |                                                                                                             |                                                                                                                                                                          |  |  |
| Fine-tuning               | NA<br>sentence pair, the model is trained to predict which out of a<br>set of randomly sampled other sentences, is paired with it<br>in the dataset. It computes the cosine similarity from each<br>possible sentence pair and applies the cross-entropy loss by<br>comparing with true pairs. |                                                                                                                                                                                                             |                                                                                                             |                                                                                                                                                                          |  |  |
| Base Model                | mpnet-base                                                                                                                                                                                                                                                                                     | distilroberta-base                                                                                                                                                                                          | MiniLM-L12-<br>H384-uncased                                                                                 | bert-base-uncased                                                                                                                                                        |  |  |
| Pre-training<br>Corpora   | BooksCorpus,<br>CC-News, English<br>Wikipedia,<br>Open<br>WebText, Stories                                                                                                                                                                                                                     | BooksCorpus,<br>CC-News, English<br>Wikipedia,<br>Open<br>WebText, Stories                                                                                                                                  | Unknown (Corpora<br>for<br>the<br>original<br>model used for dis<br>tillation, UniLMv2,<br>is also unknown) | Unknown (Likely a<br>large code and text<br>dataset)                                                                                                                     |  |  |
| Pre-training<br>Technique | (1)<br>Permuted<br>lan<br>guage modeling; (2)<br>Incorporate<br>auxil<br>iary<br>positional<br>in<br>formation                                                                                                                                                                                 | (1)<br>Knowledge<br>Distillation,<br>build<br>ing<br>on<br>the<br>robust<br>training techniques<br>of<br>RoBERTa<br>(dy<br>namic<br>masking,<br>large<br>batch<br>sizes,<br>longer<br>training<br>duration) | (1)<br>Distillation<br>(deep self-attention<br>distillation)<br>likely<br>from UniLMv2                      | (1)<br>Masked<br>lan<br>guage<br>modeling;<br>(2)<br>Next<br>sentence<br>prediction;<br>(3)<br>Tokenization<br>with<br>WordPiece;<br>(4)<br>Positional<br>embed<br>dings |  |  |

Table 2: Summary of language models sampled in the present study. *Note:* \* = embeddings are normalized. + = Average performance on encoding sentence over 14 tasks over 14 diverse tasks from different domains (14 datasets). SNL = 570k sentence pairs annotated with labels. Multi-Genre NLI = 430k sentence pairs covering spoken and written text. BookCorpus = 11,038 unpublished books scraped from the Internet.

### Model Comparison: Test Sample

First, we compared similarity scores for sentence embedding pairs for each sentence transformer model to get a qualitative understanding of the captured dimensions. After feeding seven sample sentences through each sentence transformer model for encoding, similarity arrays of each sentence embedding pair were compared. Tokenization and preprocessing is handled as part of the sentence transformers library.

- 0 = "*She has been seen at a mental\_health facility since 1983.*"
- 1 = "*I didn't want to believe I had any mental\_health issues and went into denial.*"
- 2 = "*The burden of mental\_illness concentrates in 5-10 of the adolescent population.*"
- 3 = "*Their rates of mental\_illness are almost twice that of religious adolescents raised in religious households.*"
- 4 = "*Stigma against people with mental\_illness is a very complex public health problem.*"
- 5 = "*Stigma associated with mental\_illness is one of the major impediments in evolving effective treatment interventions to address the burden associated with these disorders.*"
- 6 = "*Anorexia is a killer it has the highest mortality rate of any mental\_illness, including depression .*"

<span id="page-17-1"></span>![](_page_17_Figure_9.jpeg)

Figure 9: Cosine similarity matrix for sentence embeddings using the "all-mpnet-base-v2" model.

<span id="page-17-2"></span>![](_page_17_Figure_11.jpeg)

Figure 10: Cosine similarity matrix for sentence embeddings using the "all-distilroberta-v1" model.

<span id="page-17-0"></span>![](_page_17_Figure_13.jpeg)

Figure 11: Cosine similarity matrix for sentence embeddings using the "all-MiniLM-L6-v2" model.

Our analysis demonstrated that "all-mpnet-basev2" (the best model on various encoding tasks, as shown in the first row of Table [2\)](#page-16-0) had the highest similarity for semantically equivalent sentences (see Figure [9\)](#page-17-1). For this task, its superior performance might be attributed to its architecture. MPNet leverages token dependencies through permuted language modeling, which involves scrambling sentential word order and training the model to predict the original order, forcing MPNet to learn the relationships and dependencies between words. It also incorporates auxiliary positional information, allowing the model to perceive entire sentences, enhancing its ability to capture semantic nuances. "all-distilroberta-v1" (Figure [10\)](#page-17-2) and "all-MiniLM-L6-v2" (Figure [11\)](#page-17-0) do not capture this semantic depth, underscoring the strengths of MPNet in semantic understanding and syntactic sensitivity.

# Breadth Measure

To analyze semantic differences among sentences containing target concepts, we first extracted texts and then sentences containing target terms from our corpora. The frequency of these sentences over five-year intervals dictated the minimum acceptable number of sentences to sample.

Next, we engaged in a randomized sampling process. In the 1975-1979 interval, there were more than 50 texts in total, apart from for "mental\_health", in the general corpus. From these texts, we randomly sampled up to 50 sentences per interval across 10 sets of samples (we sampled all available sentences when there were fewer texts), resulting in up to 500 sentences for every five-year interval, shown in Figure [12.](#page-18-0)

Following data acquisition, we encoded sentence embeddings using state-of-the-art approaches. Using sentence transformers (except for "bert-baseuncased" which tokenized and passed sentences through PyTorch tensors), we derived embeddings that encapsulated the semantic essence of each sentence. These embeddings were averaged along dimension one in the last hidden state layer, creating a single vector representation for each sentence that achieves a nuanced representation of the sentence's semantic content.

Finally, dissimilarity scores were computed. Leveraging the inverse cosine distance metric, we estimated the similarity between every pair of sentence representations using pairwise distances within the range [-1,1]. To ensure unbiased results, we excluded self-similarity and symmetric elements, focusing solely on the upper half of the matrix (49x25). During analysis, the matrix was flattened to extract a 1D array (a stacked half-matrix) of line-by-line similarity scores. Next, we inverted the similarity scores by subtracting them from 1 to obtain absolute values within the range of [0,1], signifying the dissimilarity between corresponding sentence vectors. The final dissimilarity metric was computed by averaging scores within each of the ten samples per interval (getting the sum of cosine distance scores divided by the total number of sentence pairs), followed by an additional averaging across each five-year period within the 1970-2014 range. Higher scores on the cosine distance metric, ranging from 0 to 1, correspond to greater dissimilarity between sentence vectors.

<span id="page-18-0"></span>![](_page_18_Figure_5.jpeg)

Figure 12: Counts of lines containing target terms grouped by 5-year intervals (horizontal line represents maximum sampling threshold). *Note:* Top three panels = Psychology corpus; bottom three = General corpus.

### Model Comparison: Results

After computing breadth scores across five-year intervals, we compared trends using sentence transformer models and bert-base-uncased. As shown in Figure [13,](#page-19-0) most models showed an upward trend in cosine distance (i.e., inverse similarity), indicating a broader semantic usage of the target concepts. However, "bert-base-uncased" showed lower and flatter similarity scores, possibly due to its pretraining on tasks less directly related to semantic textual similarity. "all-mpnet-base-v2," chosen for the main analysis, performed similarly to the other models but excelled in capturing semantic nuances, as described in Section [C.](#page-16-0)

<span id="page-19-0"></span>![](_page_19_Figure_0.jpeg)

Figure 13: Breadth score over five-year intervals for each model (1970- 2014). *Note:* Model order demonstrates rank of cosine distance score at the final data point (2010-2014) from highest to lowest.

### D. Appendix D

<span id="page-20-0"></span>To create the general corpus, a rigorous procedure was followed. We first combined two related corpora: the Corpus of Historical American English (CoHA; Davies, 2008) and the Corpus of Contemporary American English (CoCA; Davies, 2008). CoHA contains 400 million words from 1810- 2009, drawn from 115,000 texts distributed across everyday publications (fiction, magazines, newspapers, and non-fiction books). CoCA contains 560 million words from 1990-2019 drawn from 500,000 texts (from spoken language, TV shows, academic journals, fiction, magazines, newspapers, and blogs). After merging the two corpora, the combined corpus spanning 1810-2019 was processed following recommendations from Alatrash et al. (2020) to clean it without compromising the qualitative and distributional properties of the data. This process included first excluding the special token "@", which appears in 5% of the CoHA corpus (introduced for legal reasons), malformed tokens that are possible artifacts of the digitization process or the data processing, and clean-up performed using the web interface ("&c?;", "q!", "|p130", "NUL"), and removing escaped HTML characters (" ( STAR ) ", "<p>", "<>"). Other symbols were excluded after manual inspection of the corpus (e.g., " // ", " | ", " – ", "\*", "..", "PHOTO", "( COLOR )", " ILLUSTRATION ", "/"). Blogs were also excluded (89,054 web articles; 98,788 blogs) for not containing associated year data, and 25,418 academic texts were removed. Forty-one lines were removed for missing text data (3 fiction, 11 news, 25 magazines, 2 spoken text) and 32 lines were removed for column misalignment (15 mag, 15 news, 1 fiction, 1 tv). The cleaned corpus was then lowercased and punctuation (commas, periods, question marks), function words, numerals and academic texts were removed. The final combined corpus contained 822,620,111 words from 344,634 texts: 30,496 fiction books, 136,476 magazines, 113,421 newspapers, 2,635 non-fiction books, 43,209 spoken language and 18,397 TV shows. The current study restricted the corpus period from 1970 to 2016 using 501,415,577 tokens from 244,552 articles (23,855 fiction; 88,641 magazines; 73,557 news; 1,498 non-fiction; 40,036 spoken; 16,965 TV).

### E. Appendix E

<span id="page-21-2"></span>

| 1970       | 1980       | 1990       | 2000       | 2010       |
|------------|------------|------------|------------|------------|
| positive   | poor       | poor       | poor       | poor       |
| poor       | general    | maternal   | maternal   | positive   |
| adolescent | well       | positive   | well       | maternal   |
| female     | positive   | well       | positive   | well       |
| improved   | preventive | adolescent | general    | adolescent |
| overall    | good       | general    | adolescent | parental   |
| preventive | adolescent | good       | parental   | general    |
| public     | maternal   | bad        | bad        | bad        |
| recent     | own        | optimal    | good       | good       |
| robust     | individual | own        | overall    | overall    |

Table 3: Top 10 adjective modifiers of *mental health* in the psychology corpus (terms are ranked by their relative count for the respective decade)

<span id="page-21-0"></span>

| 1970     | 1980       | 1990       | 2000       | 2010     |
|----------|------------|------------|------------|----------|
| past     | chronic    | severe     | severe     | severe   |
| chronic  | major      | serious    | serious    | serious  |
| excess   | severe     | chronic    | major      | chronic  |
| feminine | familial   | major      | chronic    | parental |
| formal   | malingered | common     | parental   | major    |
| more     | acute      | maternal   | other      | common   |
| obvious  | aggressive | parental   | common     | other    |
| other    | disabling  | comorbid   | maternal   | co       |
| partum   | few        | persistent | comorbid   | maternal |
| severe   | less       | other      | persistent | comorbid |

Table 4: Top 10 adjective modifiers of *mental illness* in the psychology corpus (terms are ranked by their relative count for the respective decade)

| 1970         | 1980         | 1990        | 2000        | 2010       |
|--------------|--------------|-------------|-------------|------------|
| visual       | visual       | visual      | visual      | visual     |
| interpersona | lsocial      | social      | positive    | social     |
| auditory     | maternal     | positive    | negative    | negative   |
| differential | positive     | negative    | social      | positive   |
| social       | parental     | subjective  | subjective  | conscious  |
| subliminal   | negative     | parental    | conscious   | subjective |
| pictorial    | interpersona | al maternal | parental    | high       |
| binocular    | human        | auditory    | high        | auditory   |
| favorable    | subjective   | accurate    | categorical | low        |
| high         | auditory     | interperson | allow       | parental   |

Table 5: Top 10 adjective modifiers of *perception* in the psychology corpus (terms are ranked by their relative count for the respective decade)

| 1970       | 1980        | 1990       | 2000              | 2010           |
|------------|-------------|------------|-------------------|----------------|
| collective | everincreas | singgood   | good              | poor           |
| diminished | vibrant     | own        | well              | good           |
| necessary  | NA          | positive   | own               | well           |
| normal     | NA          | rural      | collective        | abysmal        |
| NA         | NA          | sound      | optimal           | additional     |
| NA         | NA          | subsequent | poor              | comprehensive  |
| NA         | NA          | bad        | postpartum        | lessthanoptima |
| NA         | NA          | dubious    | collegestudentnew |                |
| NA         | NA          | geriatric  | confident         | own            |
| NA         | NA          | maternal   | fragile           | pediatric      |

Table 6: Top 10 adjective modifiers of *mental health* in the general corpus (terms are ranked by their relative count for the respective decade)

<span id="page-21-1"></span>

| 1970      | 1980       | 1990      | 2000       | 2010        |
|-----------|------------|-----------|------------|-------------|
| serious   | acute      | severe    | severe     | serious     |
| certain   | hereditary | serious   | serious    | severe      |
| incipient | severe     | major     | major      | other       |
| socalled  | socalled   | chronic   | other      | acute       |
| NA        | underlying | untreated | most       | chronic     |
| NA        | NA         | common    | adolescent | common      |
| NA        | NA         | other     | bipolar    | diagnosable |
| NA        | NA         | classic   | common     | major       |
| NA        | NA         | more      | many       | deep        |
| NA        | NA         | severe    | new        | difficult   |

Table 7: Top 10 adjective modifiers of *mental illness* in the general corpus (terms are ranked by their relative count for the respective decade)

| 1970         | 1980      | 1990         | 2000         | 2010         |
|--------------|-----------|--------------|--------------|--------------|
| extrasensory | public    | public       | public       | public       |
| visual       | different | widespread   | common       | common       |
| own          | common    | visual       | popular      | popular      |
| aesthetic    | general   | common       | wrong        | general      |
| direct       | innate    | popular      | human        | own          |
| single       | own       | general      | general      | sensory      |
| keen         | popular   | own          | own          | veridical    |
| new          | psychic   | new          | extrasensory | extrasensory |
| practical    | clear     | extrasensory | acute        | negative     |
| present      | human     | human        | visual       | parental     |

Table 8: Top 10 adjective modifiers of *perception* in the general corpus (terms are ranked by their relative count for the respective decade)

#### F. Appendix F

<span id="page-22-0"></span>

| 1970         | 1980         | 1990         | 2000         | 2010      |
|--------------|--------------|--------------|--------------|-----------|
| community    | service      | service      | service      | service   |
| center       | community    | child        | problem      | problem   |
| service      | professional | professional | child        | child     |
| program      | center       | use          | use          | study     |
| professional | problem      | problem      | care         | use       |
| child        | use          | care         | study        | care      |
| school       | study        | study        | treatment    | treatment |
| problem      | social       | treatment    | professional | need      |
| group        | child        | need         | need         | outcome   |
| worker       | program      | community    | health       | physical  |

Table 9: Top 10 Warriner-matched collocates of *mental health* in the psychology corpus (terms are ranked by their relative count for the respective decade)

| 1970        | 1980     | 1990      | 2000       | 2010       |
|-------------|----------|-----------|------------|------------|
| attitude    | attitude | severe    | severe     | people     |
| scale       | study    | person    | people     | severe     |
| patient     | patient  | patient   | use        | study      |
| study       | high     | treatment | patient    | stigma     |
| group       | person   | substance | study      | use        |
| psychiatric | problem  | study     | person     | individual |
| opinion     | scale    | use       | disorder   | treatment  |
| factor      | child    | people    | treatment  | disorder   |
| find        | use      | disorder  | individual | family     |
| student     | major    | family    | substance  | experience |

Table 10: Top 10 Warriner-matched collocates of *mental illness* in the psychology corpus (terms are ranked by their relative count for the respective decade)

| 1970       | 1980         | 1990         | 2000         | 2010         |
|------------|--------------|--------------|--------------|--------------|
| self       | study        | study        | study        | study        |
| study      | child        | self         | self         | self         |
| result     | self         | child        | child        | social       |
| test       | result       | social       | examine      | relationship |
| visual     | subject      | result       | relationship | use          |
| child      | difference   | examine      | use          | examine      |
| subject    | social       | use          | social       | influence    |
| group      | relationship | relationship | result       | effect       |
| difference | effect       | difference   | relate       | result       |
| use        | group        | behavior     | influence    | child        |

Table 11: Top 10 Warriner-matched collocates of *perception* in the psychology corpus (terms are ranked by their relative count for the respective decade)

| 1970       | 1980       | 1990         | 2000      | 2010         |
|------------|------------|--------------|-----------|--------------|
| department | center     | have         | say       | have         |
| state      | institute  | national     | have      | say          |
| center     | service    | institute    | national  | issue        |
| health     | fund       | care         | institute | care         |
| city       | have       | service      | child     | problem      |
| director   | national   | professional | care      | system       |
| institute  | allow      | abuse        | community | service      |
| national   | commission | extate       | need      | health       |
| new        | department | center       | service   | physical     |
| program    | oak        | department   | problem   | professional |

Table 12: Top 10 Warriner-matched collocates of *mental health* in the general corpus (terms are ranked by their relative count for the respective decade)

| 1970    | 1980       | 1990       | 2000     | 2010     |
|---------|------------|------------|----------|----------|
| drug    | suffer     | have       | have     | have     |
| history | alcoholisr | npeople    | people   | people   |
| treat   | have       | severe     | family   | family   |
| acute   | time       | depression | n do     | say      |
| appoint | acute      | family     | suffer   | alliance |
| bill    | argue      | say        | disorder | history  |
| can     | ask        | can        | say      | national |
| cancer  | basement   | drug       | severe   | severe   |
| cause   | bout       | history    | child    | suffer   |
| center  | cite       | know       | drug     | member   |

Table 13: Top 10 Warriner-matched collocates of *mental illness* in the general corpus (terms are ranked by their relative count for the respective decade)

| 1970      | 1980    | 1990    | 2000    | 2010      |
|-----------|---------|---------|---------|-----------|
| people    | public  | public  | change  | change    |
| public    | change  | change  | public  | public    |
| alter     | reality | can     | people  | people    |
| change    | base    | people  | can     | can       |
| president | black   | other   | reality | time      |
| study     | member  | reality | other   | shift     |
| associate | new     | world   | go      | affect    |
| can       | people  | may     | depth   | alter     |
| cause     | popular | go      | know    | challenge |
| child     | side    | thing   | will    | pain      |

Table 14: Top 10 Warriner-matched collocates of *perception* in the general corpus (terms are ranked by their relative count for the respective decade)

### G. Appendix G

<span id="page-23-0"></span>![](_page_23_Figure_1.jpeg)

Year effect sizes for indices operationalizing major dimensions of lexical semantic change in the psychology corpus (filled circles) and general corpus (empty circles). *Note:* First degree = Linear; Second degree = Quadratic. Vertical dotted line = Standardized beta coefficient of 0; Standard errors (SE) that overlap line indicate that the null hypothesis can be rejected at the 5% significance level.

<span id="page-23-1"></span>

| Index (Concept)              | Corpus     | Model               | B             | SE           | t             | p              | 2<br>F (DF); Adj. R   |
|------------------------------|------------|---------------------|---------------|--------------|---------------|----------------|-----------------------|
| Intensifier (Mental Illness) | Psychology | Linear<br>Quadratic | 0.74<br>-0.33 | 0.09<br>0.10 | 8.18<br>-3.26 | <.001<br>0.002 | 38.76 (1, 44); 0.62*  |
|                              | General    | Linear<br>Quadratic | -0.09<br>0.30 | 0.20<br>0.22 | -0.45<br>1.34 | .657<br>0.194  | 0.99 (2, 24); -0.0005 |
| Intensifier (Perception)     | Psychology | Linear<br>Quadratic | 0.60<br>-0.08 | 0.12<br>0.14 | 5.00<br>-0.62 | <.001<br>0.541 | 12.71 (2,44); 0.34*   |
|                              | General    | Linear<br>Quadratic | 0.05<br>-0.07 | 0.20<br>0.23 | 0.27<br>-0.32 | 0.793<br>0.752 | 0.08 (2, 24); -0.08   |

Table 15: Regression Coefficients (Scaled) and Fit Statistics Predicting Intensifier Indices as a Function of Year. *Note*: \* = *p*-value for the overall model = <.001. Regression coefficients are unstandardized. For mental\_illness in psychology, residuals were autocorrelated, and outcome variable was re-fit with Generalized Least Squares approach, yielding: B = 0.74; SE = 0.09; *p* < .001; RSE(DF) = 0.62(47,44); BIC = 108.52.

<span id="page-24-0"></span>

| Index    | Concept        | Corpus     | B               | SE             | p     | F (DF)                  | 2<br>Adj. R |
|----------|----------------|------------|-----------------|----------------|-------|-------------------------|-------------|
| Valence  | Mental Health  | Psychology | -0.003          | 10−4<br>3<br>× | <.001 | 122.65 (1,45)           | 0.73        |
|          |                | General    | -0.005          | 0.003          | .071  | 3.55 (1,25)             | 0.09        |
|          | Mental Illness | Psychology | -0.002          | 10−4<br>9<br>× | .057  | 3.82 (1,45)             | 0.058       |
|          |                | General    | 0.01            | 0.005          | .011  | 7.62 (1,25)             | 0.20        |
|          | Perception     | Psychology | 10−5<br>−1<br>× | 10−4<br>2<br>× | .949  | 0.004 (1,45)            | -0.02       |
|          |                | General    | -0.002          | 0.002          | .188  | 1.84 (1,25)             | 0.03        |
|          | Mental Health  | Psychology | 0.001           | 10−4<br>3<br>× | 0.001 | 28.19 (1,7)             | 0.77        |
|          |                | General    | -0.001          | 10−4<br>×<br>7 | .213  | 2.49 (1,3)              | 0.27        |
| Breadth  | Mental Illness | Psychology | 0.002           | 10−4<br>4<br>× | .006  | 14.99 (1,7)             | 0.64        |
|          |                | General    | 10−6<br>−6<br>× | 10−4<br>6<br>× | .992  | 10−4<br>1<br>×<br>(1,3) | -0.33       |
|          | Perception     | Psychology | 0.001           | 10−4<br>×<br>3 | 0.006 | 15.12 (1,7)             | 0.64        |
|          |                | General    | 10−4<br>7<br>×  | 10−4<br>3<br>× | .076  | 7.13 (1,3)              | 0.61        |
|          | Mental Health  | Psychology | 0.003           | 10−4<br>3<br>× | <.001 | 89.38 (1,45)            | 0.66        |
|          |                | General    | 0.005           | 0.002          | <.001 | 7.83 (1,25)             | 0.21        |
| Arousal  | Mental Illness | Psychology | 0.003           | 10−4<br>9<br>× | <.001 | 7.51 (1,45)             | 0.12        |
|          |                | General    | 0.002           | 0.003          | .462  | 0.56 (1,25)             | -0.02       |
|          | Perception     | Psychology | 0.001           | 10−4<br>×<br>2 | <.001 | 23.65 (1,45)            | 0.33        |
|          |                | General    | 0.002           | 0.001          | .148  | 2.22 (1,25)             | 0.05        |
|          | Mental Health  | Psychology | 10−4<br>4<br>×  | 10−5<br>3<br>× | <.001 | 163.34 (1,45)           | 0.78        |
|          |                | General    | 10−4<br>3<br>×  | 10−4<br>2<br>× | .130  | 2.48 (1,21)             | 0.06        |
| Path.    | Mental Illness | Psychology | 10−4<br>2<br>×  | 10−4<br>1<br>× | .049  | 4.12 (1,43)             | 0.07        |
|          |                | General    | 10−4<br>−1<br>× | 10−4<br>×<br>2 | .552  | 0.36 (1,23)             | -0.03       |
|          |                | Psychology | 10−3<br>2<br>×  | 10−2<br>4<br>× | <.001 | 118.42 (1,44)           | 0.72        |
|          | Perception     | General    | 10−5<br>5<br>×  | 10−5<br>2<br>× | .051  | 5.95 (1,6)              | 0.41        |
| Salience | Mental Health  | Psychology | 10−6<br>7<br>×  | 10−7<br>4<br>× | <.001 | 292.52 (1,45)           | 0.86        |
|          |                | General    | 10−7<br>×<br>2  | 10−8<br>×<br>4 | <.001 | 18.17 (1,45)            | 0.27        |
|          | Mental Illness | Psychology | 10−7<br>3<br>×  | 10−8<br>9<br>× | <.001 | 13.21 (1,45)            | 0.21        |
|          |                | General    | 10−7<br>×<br>1  | 10−8<br>×<br>2 | <.001 | 42.21 (1,45)            | 0.47        |
|          |                | Psychology | 10−7<br>5<br>×  | 10−7<br>3<br>× | .160  | 2.04 (1,45)             | 0.02        |
|          | Perception     | General    | 10−8<br>−3<br>× | 10−8<br>6<br>× | .568  | 0.33 (1,45)             | -0.01       |

Table 16: Unstandardized Regression Coefficients and Fit Statistics Predicting Indices as a Function of Year. *Note*: The midrule separates the main dimensions (above) and the exploratory dimensions (below). Path. = Pathologization. Generalized Least Squares approach also used for models with autocorrelated residuals.

<sup>•</sup> Arousal: *mental\_health* (P): B = 0.003; SE = 3 × 10<sup>−</sup><sup>4</sup> ; *p* < .001; RSE(DF) = 0.03(47,45); BIC = -172.07

<sup>•</sup> Salience: *mental\_health* (P): B = 7 × 10<sup>−</sup><sup>6</sup> ; SE = 4 × 10<sup>−</sup><sup>7</sup> ; *p* <.001; RSE(DF) = 4 × 10<sup>−</sup><sup>5</sup> (47,45); BIC = -767.87; *mental\_illness* (P): B = 3×10<sup>−</sup><sup>7</sup> ; SE = 9×10<sup>−</sup><sup>7</sup> ; *p* < .001; RSE(DF) = 9×10<sup>−</sup><sup>6</sup> (47,45); BIC = -895.27; *perception* (P): B = 5 × 10<sup>−</sup><sup>7</sup> ; SE = 3 × 10<sup>−</sup><sup>7</sup> ; *p* = .160; RSE(DF) = 3 × 10<sup>−</sup><sup>5</sup> (47,45); BIC = -785.60; *mental\_illness* (G): B = 1 × 10<sup>−</sup><sup>7</sup> ; SE = 2 × 10<sup>−</sup><sup>8</sup> ; *p* < .001; RSE(DF) = 2 × 10<sup>−</sup><sup>6</sup> (47,45); BIC = -1048.85

<span id="page-25-0"></span>

| Index           | Concept        | Corpus                         | β               | SE           | 95% CI                         |
|-----------------|----------------|--------------------------------|-----------------|--------------|--------------------------------|
| Valence         | Mental Health  | Psychology                     | -0.86*          | 0.04         | (-0.94, -0.77)                 |
|                 |                | General                        | -0.35           | 0.17         | (-0.71, 0.004)                 |
|                 | Mental Illness | Psychology                     | -0.28*          | 0.12         | (-0.53, -0.03)                 |
|                 |                | General                        | 0.48*           | 0.13         | (0.21, 0.76)                   |
|                 | Perception     | Psychology                     | -0.01           | 0.18         | (-0.37, 0.35)                  |
|                 |                | General                        | -0.26           | 0.15         | (-0.57, 0.05)                  |
|                 |                | Psychology                     | 0.90*           | 0.04         | (0.80, 0.99)                   |
|                 | Mental Health  | General                        | -0.67*          | 0.09         | (-0.95, -0.40)                 |
| Breadth         | Mental Illness | Psychology                     | 0.83*           | 0.14         | (0.50, 1.15)                   |
|                 |                | General                        | -0.01           | 0.69         | (-2.19, 2.18)                  |
|                 | Perception     | Psychology                     | 0.83*           | 0.11         | (0.57, 1.09)                   |
|                 |                | General                        | 0.84*           | 0.22         | (0.13, 1.54)                   |
|                 |                | Psychology(1)<br>Psychology(2) | 0.74*<br>-0.30* | 0.05<br>0.10 | (0.64, 0.85)<br>(-0.50, -0.09) |
| Intensifier     | Mental illness | General(1)<br>General(2)       | -0.09<br>0.26   | 0.23<br>0.15 | (-0.56, 0.38)<br>(-0.05, 0.57) |
|                 | Perception     | Psychology(1)<br>Psychology(2) | 0.60*<br>-0.07  | 0.08<br>0.10 | (0.44, 0.76)<br>(-0.28, 0.13)  |
|                 |                | General(1)<br>General(2)       | 0.05<br>-0.06   | 0.17<br>0.21 | (-0.30, 0.41)<br>(-0.50, 0.37) |
|                 | Mental Health  | Psychology                     | 0.82*           | 0.08         | (0.66, 0.97)                   |
|                 |                | General                        | 0.49            | 0.15         | (0.19, 0.79)                   |
| Arousal         | Mental Illness | Psychology                     | 0.38*           | 0.17         | (0.05, 0.71)                   |
|                 |                | General                        | 0.15            | 0.20         | (-0.27, 0.57)                  |
|                 | Perception     | Psychology                     | 0.59*           | 0.08         | (0.44, 0.74)                   |
|                 |                | General                        | 0.29            | 0.22         | (-0.17, 0.74)                  |
|                 | Mental Health  | Psychology                     | 0.30*           | 0.12         | (0.06, 0.53)                   |
|                 |                | General                        | -0.12           | 0.23         | (-0.61, 0.36)                  |
| Pathologization | Mental Illness | Psychology                     | 0.89*           | 0.02         | (0.85, 0.92)                   |
|                 |                | General                        | 0.32            | 0.20         | (-0.09, 0.74)                  |
|                 | Perception     | Psychology                     | 0.85*           | 0.30         | (0.79, 0.92)                   |
|                 |                | General                        | 0.71            | 0.30         | (-0.03, 1.45)                  |
|                 | Mental Health  | Psychology                     | 0.93*           | 0.02         | (0.89, 0.97)                   |
|                 |                | General                        | 0.54*           | 0.10         | (0.34, 0.73)                   |
| Salience        |                | Psychology                     | 0.48*           | 0.13         | (0.21, 0.74)                   |
|                 | Mental Illness | General                        | 0.70*           | 0.07         | (0.56, 0.83)                   |
|                 |                | Psychology                     | 0.21            | 0.15         | (-0.10, 0.52)                  |
|                 | Perception     | General<br>26                  | -0.09           | 0.15         | (-0.38, 0.21)                  |

Table 17: Standardized Regression Coefficients (β) predicting Semantic Change Indices by Year. *Note*: Midrule separates main dimensions of semantic change (above). \* = *p*: < .05. (1) = First degree. (2) = Second degree.