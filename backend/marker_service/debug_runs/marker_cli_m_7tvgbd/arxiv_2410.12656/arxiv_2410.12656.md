# **Evaluating Morphological Compositional Generalization** in Large Language Models

Mete Ismayilzada<sup>1,2</sup>, Defne Circi<sup>\*3</sup>, Jonne Sälevä<sup>\*4</sup>, Hale Sirin<sup>7</sup>, Abdullatif Köksal<sup>5,6</sup>, Bhuwan Dhingra<sup>3</sup>, Antoine Bosselut<sup>1</sup>, Duygu Ataman<sup>†9</sup>, Lonneke van der Plas <sup>†2,8</sup>

<sup>1</sup>EPFL, <sup>2</sup>Idiap Research Institute, <sup>3</sup>Duke University, <sup>4</sup>Brandeis University, <sup>5</sup>LMU Munich, <sup>6</sup>University of Cambridge, <sup>7</sup>Johns Hopkins University, <sup>8</sup>Università della Svizzera Italiana, <sup>9</sup>New York University

mahammad.ismayilzada@epfl.ch

#### Abstract

Large language models (LLMs) have demonstrated significant progress in various natural language generation and understanding tasks. However, their linguistic generalization capabilities remain questionable, raising doubts about whether these models learn language similarly to humans. While humans exhibit compositional generalization and linguistic creativity in language use, the extent to which LLMs replicate these abilities, particularly in morphology, is under-explored. In this work, we systematically investigate the morphological generalization abilities of LLMs through the lens of compositionality. We define morphemes as compositional primitives and design a novel suite of generative and discriminative tasks to assess morphological productivity and systematicity. Focusing on agglutinative languages such as Turkish and Finnish, we evaluate several state-of-the-art instruction-finetuned multilingual models, including GPT-4 and Gemini. Our analysis shows that LLMs struggle with morphological compositional generalization particularly when applied to novel word roots, with performance declining sharply as morphological complexity increases. While models can identify individual morphological combinations better than chance, their performance lacks systematicity, leading to significant accuracy gaps compared to humans.

#### 1 Introduction

Large language models (LLMs) have recently achieved remarkable advances in the broad domain of natural language generation and understanding tasks (Gemini, 2024; Zhao et al., 2023; Bubeck et al., 2023; Wei et al., 2022; Brown et al., 2020). However, these models have also been shown to lack strong linguistic generalization capabilities (Weissweiler et al., 2023; McCoy et al.,

<span id="page-0-0"></span>![](_page_0_Figure_10.jpeg)

Figure 1: Our morphological generalization tasks illustrated with an example in Turkish. ID and OOD refer to in-distribution and out-of-distribution respectively. English translations are not part of the task and only shown here for illustrative purposes.

2023; Goldman et al., 2022; Wilson et al., 2023; Linzen, 2020; Baroni, 2019). This discrepancy casts doubt on whether language models learn a language the same way as humans do. When learning a language which is essentially a finite set of words and rules, humans exhibit linguistic creativity (Chomsky, 1965; Bergs, 2019) and compositional generalization through *productivity* and *systematicity* (Fodor and Pylyshyn, 1988a; Chomsky, 1957). These abilities allow humans respectively to produce and understand novel combinations of familiar grammar units. While compositional generalization abilities of language models have been extensively studied (Lake and Baroni, 2018; Keysers et al., 2019; Kim and Linzen, 2020), the extent to which language models employ this ability in morphology however remains largely under-explored. Recent works evaluating morphological generalization in language models have only focused on the productivity aspect with a limited coverage of inflectional forms (Weissweiler et al., 2023; Anh et al., 2024).

Equal contribution

Equal supervision

In this work, we address this gap by systematically investigating the morphological generalization abilities of LLMs through the lens of compositionality. Following [Keysers et al.](#page-10-6) [\(2019\)](#page-10-6), we define the morphemes (smallest meaningful units in a language)[1](#page-1-0) as the compositional primitives and design a novel suite of generative and discriminative language tasks based on the morphological combinations of these primitives. These tasks aim to test morphological productivity (ability to produce novel well-formed combinations of morphemes) and systematicity (ability to systematically understand novel combinations) respectively. Figure [1](#page-0-0) illustrates an example of both tasks.

We evaluate several state-of-the-art instructionfinetuned large multilingual models on these tasks: GPT-4, Gemini-1.5, Aya-23 and Qwen-2.5. To ensure our findings are not language-specific, we experiment with two morphologically rich (i.e. characterized by a large number of inflectional and derivational forms) languages: Turkish and Finnish. Both languages share typological features (e.g. agglutination) despite being unrelated.

We find that LLMs lack human-like morphological compositional generalization ability in agglutinative languages despite their high performance on various tasks in these languages. Our analysis shows that morphological productivity, especially when applied to novel word roots is highly challenging for LLMs. Moreover, as the morphological complexity of words increases the model performance sharply decreases (to nearly zero) while human performance is not consistently affected. On the systematicity task, while models perform much better than chance in identifying the validity of *individual* morphological combinations, however, this behaviour is not robust or systematic i.e. models fail to *consistently* determine validity of several compositions made up of the same set of morphemes.

In summary, our contributions are as follows: 1) We design novel morphological generalization tasks that require compositional processing. 2) We prepare specific test suites in both Turkish and Finnish to measure morphological generalization and make these available for future research[2](#page-1-1) . 3)

Using our novel tasks and test suites, we conduct a systematic analysis of morphological compositional generalization abilities of LLMs. 4) Our findings reveal a systematic gap in LLM's ability compared to humans concerning morphological generalization in agglutinative languages that also requires compositionality.

## 2 Related Work

#### 2.1 Compositional Generalization

Compositional generalization is the capacity to understand and produce novel compositions of seen primitives and is typically characterized by systematicity and productivity [\(Fodor and Pylyshyn,](#page-10-4) [1988a;](#page-10-4) [Keysers et al.,](#page-10-6) [2019\)](#page-10-6). Systematicity refers to the ability to understand different combinations that are made up of the same known components such as *John loves Mary* and *Mary loves John*. Productivity, on the other hand, is the ability to produce potentially infinite novel combinations of a finite number of known building blocks such as using conjunctions to construct sentences *Mary knows that John loves Mary* and *John heard that Mary knows that John loves Mary*. Past work has developed several benchmarks to measure compositional generalization abilities of neural models both in fine-tuning and in-context learning settings and has shown this task to be highly challenging [\(Yang et al.,](#page-12-1) [2024;](#page-12-1) [Lake and Baroni,](#page-10-5) [2018;](#page-10-5) [Keysers](#page-10-6) [et al.,](#page-10-6) [2019;](#page-10-6) [Kim and Linzen,](#page-10-7) [2020;](#page-10-7) [An et al.,](#page-8-0) [2023;](#page-8-0) [Dziri et al.,](#page-10-8) [2023\)](#page-10-8). These benchmarks have mainly focused on synthetic sequence matching, semantic parsing, question-answering and problem-solving tasks. Our work however, investigates compositional generalization in the context of morphology.

#### 2.2 Morphological Generalization

Morphological generalization is the ability to understand words based on their constituent parts known as *morphemes* and combine them to derive new words [\(Wysocki and Jenkins,](#page-11-3) [1987\)](#page-11-3). Morphemes are the smallest meaningful units of language that typically correspond to word roots and affixes (i.e. prefixes, infixes and suffixes). Composing these units to construct new words can be done through *inflection* and *derivation* tasks in morphology where derivation often changes the syntactic category of the words and inflection does not. These tasks have gained considerable attention as part of the SIGMORPHON's shared tasks [\(Cot](#page-9-7)[terell et al.,](#page-9-7) [2016,](#page-9-7) [2018a;](#page-9-8) [Vylomova et al.,](#page-11-4) [2020;](#page-11-4)

<span id="page-1-0"></span><sup>1</sup> In linguistics, a distinction is made between *free* morphemes that can stand alone such as words "cat" and "come" and *bound* morphemes that can only appear as part of a larger expression (e.g. "cats", "coming") such as affixes "s" and "ing".

<span id="page-1-1"></span><sup>2</sup> <https://github.com/mismayil/morph-gen>

[Kodner and Khalifa,](#page-10-9) [2022;](#page-10-9) [Goldman et al.,](#page-10-10) [2023\)](#page-10-10) and efforts to create a universal morphology [\(Mc-](#page-10-11)[Carthy et al.,](#page-10-11) [2020\)](#page-10-11). While transformer-based models have been shown to achieve near-perfect accuracy on these tasks [\(Canby et al.,](#page-9-9) [2020\)](#page-9-9), recent work has also found that these results are inflated due to lemma overlap pointing to a lack of generalization [\(Goldman et al.,](#page-10-2) [2022\)](#page-10-2). Other works have recently investigated the morphological capabilities of LLMs using inflection tasks and reported similarly weak performance results [\(Anh](#page-9-6) [et al.,](#page-9-6) [2024;](#page-9-6) [Weissweiler et al.,](#page-11-1) [2023\)](#page-11-1). Similar to our study, both of these works use the popular Wug test [\(Berko Gleason,](#page-9-10) [1958\)](#page-9-10) to evaluate the morphological generalization, however, they only focus on the productivity aspect, and their coverage of inflectional and derivational forms is limited. For example, [Weissweiler et al.](#page-11-1) [\(2023\)](#page-11-1) considers only a handful of specific inflectional forms (e.g. first person singular agreement and past tense, second person plural agreement etc.) for each language and [Anh et al.](#page-9-6) [\(2024\)](#page-9-6) translates the original Wug test suite which is very small in size (23 samples) into different languages. On the other hand, we cast the inflection and derivation tasks into the form of a compositional generalization task and evaluate models on both productivity and systematicity aspects. While focus of other works is breadth (languages from different families), we instead conduct an in-depth analysis of morphological generalization in typologically similar but unrelated languages with a large test suite covering a wide and diverse range of inflectional and derivational combinations.

## 3 Methodology

### 3.1 Background

The important role of compositional processing in language understanding and generation has been extensively studied [\(Carnap,](#page-9-11) [1947;](#page-9-11) [Chom](#page-9-3)[sky,](#page-9-3) [1965;](#page-9-3) [Fodor and Pylyshyn,](#page-10-12) [1988b;](#page-10-12) [Zadrozny,](#page-12-2) [1994;](#page-12-2) [Bauer,](#page-9-12) [2001;](#page-9-12) [Aronoff and Lindsay,](#page-9-13) [2014\)](#page-9-13). Past works have shown that new word formation is often a multi-level process that requires identifying the correct order of primary and secondary morphemes [\(Kiparsky,](#page-10-13) [1982a,](#page-10-13)[b;](#page-10-14) [Hockett,](#page-10-15) [1954\)](#page-10-15), and while humans might memorize some frequent words and phrases as a whole, most of the expressive language generation relies on productive rules of grammar [\(O'Donnell,](#page-11-5) [2015\)](#page-11-5). However, not all languages are equally productive, and more pro-

ductive languages (e.g. agglutinative) tend to have complex inflectional morphology [\(Cotterell et al.,](#page-9-14) [2019;](#page-9-14) [Ackerman and Malouf,](#page-8-1) [2013\)](#page-8-1). Moreover, these languages have been shown to be harder to model for *n*-gram and recurrent language models [\(Cotterell et al.,](#page-9-15) [2018b;](#page-9-15) [Czarnowska et al.,](#page-9-16) [2019\)](#page-9-16). Inspired by these works, we focus our study on two highly agglutinative languages and compositional tasks which we describe in detail below.

#### 3.2 Tasks

Similar to works studying compositional abilities of neural networks [\(Goodwin et al.,](#page-10-16) [2020;](#page-10-16) [Lake and](#page-10-5) [Baroni,](#page-10-5) [2018;](#page-10-5) [Keysers et al.,](#page-10-6) [2019\)](#page-10-6), we design two novel and simple compositional probing tasks to test morphological abilities of models. First, a morphological productivity task which we define as a generative task where the model is given a word root, a list of affixes (not necessarily in the correct order) and is asked to derive a meaningful word by composing the root with the affixes in the correct order. Second, a morphological systematicity task which we define as a binary discriminative task where the model is again given a word root, a list of affixes and a word derived from the root using the given affixes (not necessarily a meaningful word) and is asked to determine the grammatical validity of the derived word. Figure [1](#page-0-0) illustrates these tasks with an example in Turkish.

Additionally, to measure the morphological generalization capabilities of LLMs, we take inspiration from Berko's Wug test [\(Berko Gleason,](#page-9-10) [1958\)](#page-9-10) that is typically used to probe the inflectional and derivational morphological knowledge of children and design out-of-distribution (OOD) versions of our tasks using nonce word roots. More specifically, for each in-distribution (ID) word root in our test suite, we automatically generate a nonce word (i.e. word that does not exist in the given language) and use it in both tasks as the word root in place of the original one. However, since the model has never seen these words, to make sure the model understands the meaning of this new word, we provide the model with the original word root as a definition of the novel word root. Our generation of nonce words relies on the underlying morphophonological features and the frequency of each letter in a given language to make sure these words are plausible and inflected in the same way as the original root. Further details on nonce word generation can be found in Appendix [B.](#page-14-0)

#### 3.3 Data

We focus our study on two highly agglutinative languages, Turkish and Finnish, and prepare test suites specific for our tasks in these languages. We particularly choose these languages because they are characterized by a large number of morphemes and hence require a high degree of compositional generalization ability.

Turkish Turkic languages are well-known to be highly agglutinative where the word is composed of several morphemes in addition to a root. We select Turkish as a representative of this language family in our study. To prepare our test suite we use the Bilkent Turkish Writings Dataset[3](#page-3-0) as our base corpus which contains 6, 844 creative writings of Turkish 101 and Turkish 102 courses between 2014- 2018 and hence, is full of morphologically complex words. Data statistics can be found in Appendix Table [1.](#page-15-0) We preprocess this dataset to extract words and the sentences they are found in. Then we employ a morphological analyzer for Turkish [\(Ozturel](#page-11-6) [et al.,](#page-11-6) [2019\)](#page-11-6) to segment these words into a root and surface-level morphemes. To create a diverse and balanced test suite, we sample ≈ 150 examples per morpheme length 1 to 7 while maximizing the number of unique roots and morphemes (in total 1, 049 samples). Finally, we automatically generate a nonce word for each word in our test suite by relying on the fact that surface realizations of morphemes in Turkish are characterized by deterministic morphophonological processes such as vowel harmony, consonant assimilation and elision. Final data statistics and examples can be found in Appendix Tables [2](#page-15-1) and [5](#page-17-0) respectively. Further details on data collection can be found in Appendix [D.](#page-15-2)

Finnish We first collect a ∼1,000,000 sentence subsample of the Finnish mC4 corpus [\(Xue et al.,](#page-11-7) [2021\)](#page-11-7). We then extract unique words from the text and morphologically segment them using omorfi [\(Pirinen,](#page-11-8) [2015\)](#page-11-8) and UralicNLP [\(Hämäläinen,](#page-10-17) [2019\)](#page-10-17). After excluding words that analyzers did not cover, we manually annotate the segmentations to identify prefixes, lemmas, and affixes among the segments. We then perform stratified sampling based on the number of affixes to ensure an even range of morphological complexity in our data set. Finally, we extract sentences corresponding to each analyzed

word from mC4 and validate whether they make sense. In a significant portion of cases, we notice that the raw sentences are noisy; in these cases, we opt to generate synthetic sentences using ChatGPT, which we (authors) then manually validate to be grammatical. Final data statistics and examples can be found in Appendix Tables [6](#page-18-0) and [7.](#page-19-0)

## 4 Experiments

Setup We treat the productivity task as an openended task in which the model is asked to derive a word from the given root and affixes and the systematicity task as a binary classification task in which the model is asked to determine whether the given derivation is grammatically correct. For the systematicity task, we generate negative examples by producing all the combinations of morphemes attached to the same root and choosing the top four compositions (two for morpheme lengths of 1 and 2)[4](#page-3-1) that are closest to the original valid combination measured by the Levenshtein distance. We do this to ensure our incorrect combinations are challenging enough for the model as they will be deceptively close to a plausible derivation. We also experiment with other negative example selection strategies such as random selection and a heuristic selection based on the linguistic characteristics of the given language. We describe these settings in more detail and compare the results in Section [5.5.](#page-7-0) Finally, we (authors) manually verify all the generated negative examples and fix the label of false negatives.

Models We evaluate several state-of-the-art multilingual instruction-finetuned LLMs, namely, two open-weights models, Aya-23 [\(Aryabumi et al.,](#page-9-17) [2024\)](#page-9-17) and Qwen-2.5 [\(Team,](#page-11-9) [2024\)](#page-11-9), and two closedsource models, Gemini-1.5 [\(Gemini,](#page-10-0) [2024\)](#page-10-0) and GPT-4 [\(OpenAI,](#page-11-10) [2024\)](#page-11-10). We evaluate all models on all languages except for Aya-23 which officially supports Turkish, but not Finnish.[5](#page-3-2) . We also report the performance of a *random* baseline that generates a derivation with a random combination of given morphemes (productivity task) and randomly decides whether the derivation is grammatically

<span id="page-3-0"></span><sup>3</sup> [https://github.com/selimfirat/](https://github.com/selimfirat/bilkent-turkish-writings-dataset) [bilkent-turkish-writings-dataset](https://github.com/selimfirat/bilkent-turkish-writings-dataset)

<span id="page-3-1"></span><sup>4</sup> For 1-morpheme words, we manually annotate a negative morpheme to generate one negative option.

<span id="page-3-2"></span><sup>5</sup>We also experimented with recent LLMs that are instruction-finetuned specifically on Finnish such as Poro-34B [\(Luukkonen et al.,](#page-10-18) [2024\)](#page-10-18) and Ahma model series that are Llama [\(Touvron et al.,](#page-11-11) [2023\)](#page-11-11) models fine-tuned on Finnish, however, we omitted them from our analysis as they failed to follow our task prompts in both English and Finnish templates.

<span id="page-4-3"></span>![](_page_4_Figure_0.jpeg)

Figure 2: Morphological productivity and systematicity task results for Turkish. Detailed results for all shots are in Appendix Table 8.

<span id="page-4-4"></span>![](_page_4_Figure_2.jpeg)

Figure 3: Morphological productivity and systematicity task results for Finnish. Detailed results for all shots are in Appendix Table 9.

correct, and a *majority* baseline, which selects the most frequent label (in our case "No") for the systematicity task (not applicable for the productivity task). All models are evaluated using few-shot (1, 3, and 5) in-context learning and greedy decoding since our tasks are deterministic by nature $^{6}$ . Unless otherwise specified, prompt instructions are in English, and number of shots is set to 5 for reported results<sup>7</sup>. Further details on model evaluation can be found in Appendix C.

**Evaluation Metrics** For the productivity task, we use **Exact Match** accuracy against the correct derivations. For the systematicity task, we report an average of **Macro-F1** scores for each sample and a **Coherence** score that measures whether the model correctly and consistently identifies the validity (or invalidity) of all derivations for a given set of morphemes. Hence, coherence is defined as a binary score where the model gets a score of 1 for a given sample if and only if it correctly guesses the validity of all derivations pertinent to that sample, otherwise 0. We employ this stringent metric to test the robustness of model performance similar

#### to (Storks and Chai, 2021).

**Human Evaluation** We evaluate human performance on both tasks using two native speakers $^{8}$  per language, who annotate 70 and 60 samples from the Turkish and Finnish test suites, respectively. To ensure our evaluation sample is a representative sample of the entire test suite, we randomly select 10 examples per morpheme length for each test distribution. Human annotators follow the same task instructions used for model prompts and were shown five examples. We report almost perfect or substantial inter-annotator agreement measured by Cohen's kappa score (Cohen, 1960) for both tasks, languages, and test distributions (Appendix Tables  $3, 4$ ). Finally, for each task metric, we report the average score of annotators as the final human score.

**Results** Figure 2 and 3 summarize all model results for both morphological productivity and systematicity tasks evaluated respectively on the Turkish and Finnish data. We see that on the productivity task, all models except GPT-4 barely crack the random performance. While GPT-4 performs the best for both languages, it significantly lags behind the human performance ( $-43\%$  and  $-51\%$ 

<span id="page-4-0"></span><sup>&</sup>lt;sup>6</sup>We also experiment with other decoding strategies, however, find no significant difference in performance. Results for different decoding strategies can be found in Appendix A.5

<span id="page-4-1"></span> $^{7}$ We also experiment with paraphrased version of our prompt instructions, but find no significant difference in performance. Results for paraphrased prompt instruction can be found in Appendix A.6

<span id="page-4-2"></span> $^{8}$ Annotators were recruited from a Turkish and Finnish researcher community and were not compensated as they volunteered

in Turkish and −40.8% and −48.9% for Finnish respectively for ID and OOD data). Moreover, the GPT-4 performance gap between the ID and OOD test suites for both languages is much larger than the human gap (≈ 10% vs. 3% in Turkish and 1.7% in Finnish). These results indicate that humans are much more compositionally productive in morphology and generalize more robustly to novel unseen words.

From the systematicity task results, we see that models perform much better than random and majority baselines with GPT-4 again in lead, however, the performance gap compared to humans is still significant, especially, on robustness as measured by coherence score (−19.1% and −46.5% in Turkish and −8.8% and −25.2% in Finnish respectively for ID and OOD data). The ID and OOD performance gap is also significant for all models, especially when measured by coherence score (ranging from −9.5% to −23.3% in Macro-F1 and from −13.5% to −37.2% in Coherence) while this gap is very low (≈ 2%) for humans when measured by both metrics. These results show that humans are much more compositionally systematic and consistent in discriminating between correct and incorrect morphological forms made up of the same set of morphemes.

## 5 Analysis

## 5.1 Effect of Morphological Complexity

Recent works have shown that morphological complexity plays a crucial role in the morphological generalization abilities of LLMs [\(Anh et al.,](#page-9-6) [2024;](#page-9-6) [Czarnowska et al.,](#page-9-16) [2019;](#page-9-16) [Cotterell et al.,](#page-9-15) [2018b\)](#page-9-15). Morphological complexity is typically categorized into *integrative* (I-complexity) which refers to the predictability of inflected form and *enumerative* (Ecomplexity) complexity which refers to the number of cases and inflectional paradigms in language grammar [\(Ackerman and Malouf,](#page-8-1) [2013\)](#page-8-1). While both languages we study are morphologically complex, our test suites include inflectional and derivational forms of varying length in the number of morphemes (1-7 in Turkish and 1-6 in Finnish). This allows us to study the effect of within-language E-complexity on the performance of our models. Figure [4](#page-6-0) summarizes the GPT-4 performance for both tasks stratified by the number of bound morphemes on the Turkish data. On the productivity task, we observe a sharp downward trend (plummeting to nearly zero) in performance as the number

of morphemes increases for both ID and OOD test suites with a relatively constant gap between ID and OOD performance while humans exhibit no such dependence on complexity (Appendix Tables [16,](#page-25-0) [25\)](#page-29-0). This shows that humans learn their native language robustly and can easily produce and identify long novel words while models are quite sensitive to the morphological (E-) complexity.

On the systematicity task, Macro-F1 scores for ID and OOD remain mostly unchanged as complexity increases, but coherence scores show a negative correlation with the increasing morphological complexity. We also observe a surprisingly low performance on 1-morpheme OOD words which we attribute to the varying number of negative options by morpheme length and potential shortcuts in longer morpheme words, as discussed in Appendix [A.3.](#page-12-3)

#### 5.2 Effect of Context

While our core tasks are somewhat synthetic in nature, we do also experiment with more realistic versions where we provide the model a sentence as an additional context. Specifically, we frame them as sentence completion tasks where a sentence with a blank is provided and the model is asked to fill in the blank with the correct word derived from the given word root and affixes (productivity task) or determine if the given derivation is the correct option for the blank (systematicity task).

Figure [5](#page-6-1) summarizes the results for both productivity and systematicity tasks evaluated on the Turkish data where we provide a sentence with a blank to the model as a context (i.e. sentence completion task). This results in some improvement on the productivity task, however, we observe significant decrease in performance on the systematicity task especially for smaller models such as Aya-23 and Qwen-2.5 series and in OOD setting. This could be due to the additional complexity introduced by the extra context, however, we should note that worse performance on this task implies even stronger generalization failure since this task is more real-world and closer to the next word prediction task compared to the original context-free setup.

#### 5.3 Effect of Tokenization

Past work has shown that suboptimal tokenizers, especially byte-pair encoding [\(Sennrich et al.,](#page-11-13) [2016\)](#page-11-13) used in GPT-4 have generally a negative effect on the morphological abilities of language mod-

<span id="page-6-0"></span>![](_page_6_Figure_0.jpeg)

Figure 4: GPT-4 morphological productivity and systematicity task results for Turkish stratified by number of **bound morphemes**. Detailed results are in Appendix Tables 16, 17, 18. Finnish results are in Appendix Figure 11.

<span id="page-6-1"></span>![](_page_6_Figure_2.jpeg)

Figure 5: Morphological productivity and systematicity task results for Turkish showing the effect of additional **context.** Detailed results are in Appendix Table 36. Results for Finnish are in Appendix Figure 13.

els (Meyer and Buys, 2023; Bostrom and Durrett, 2020; Hofmann et al., 2021). Whether the low performance of the model on the productivity task can be attributed to the suboptimal nature of the tokenization is of interest in particular because our tasks rely on the morphologically segmented morphemes while the model utilizes byte-level tokens that are mostly English. To measure the effect of the tokenization, we ran a version of the productivity task where the morphemes provided to the model are obtained by segmenting the final derivation based on the model's own tokenizer instead of the morphologically-aligned units. Figure 6 compares the performance of the tokenizer-aligned morphemes with the morphologically-aligned morphemes on the ID test set. $^{9}$  We see that the performance in both cases is very similar to each other which points to a possibility that tokenization may not be the underlying issue behind the low performance. This finding is also consistent with some past work on exploring morphological capabilities of ChatGPT (Weissweiler et al.,  $2023$ )<sup>10</sup>

<span id="page-6-2"></span>Morphological Productivity Turkish

![](_page_6_Figure_8.jpeg)

Figure 6: GPT-4 productivity task results on the ID test suite for Turkish stratified by number of bound morphemes showing the effect of tokenization. Detailed results are in Appendix Table 42.

#### 5.4 Effect of Morpheme Order

Since our goal is to study the ability of LLMs to combine the morphological units in the correct order, in all of our experiments we shuffle the order of the units in the prompts. However, given that models are sensitive to small prompt changes (Pezeshkpour and Hruschka, 2023; Zhu et al., 2024; Wang et al., 2023; Zhao et al., 2021), we also analyze the effect of changing the morpheme order on

<span id="page-6-3"></span><sup>&</sup>lt;sup>9</sup>Since we use the word root as a definition for the nonce root and the tokenizer tends to break the words into meaningless chunks, we skip this experiment on the OOD test set.

<span id="page-6-4"></span> $^{10}$ We note that we perform this analysis only with subwordlevel tokenizers, but not character-level tokenizers for two reasons: 1) To the best of our knowledge, at the time of writing this paper, there were no instruction-tuned multilingual language models for Turkish and Finnish that uses character-level

tokenizers; 2) Past work has shown that character-level tokenizers do not offer any significant advantages over subwordlevel tokenizers in morphological generalization (Libovický et al., 2021; Toraman et al., 2022).

<span id="page-7-1"></span>![](_page_7_Figure_0.jpeg)

Figure 7: Morphological productivity and systematicity task results for Turkish showing the effect of the **morpheme order.** Detailed results are in Appendix Table 46. Results for Finnish are in Appendix Figure 14.

the performance of the model. To this end, we run our main experiments with all the morphemes in their correct order and report the results in Figure 7. We can see that this small change improves the performance across both tasks and models and especially, in the productivity task, the improvement can be up to  $20\%$ . This shows that models understand the tasks and can provide a correct answer by simply copying the morphemes when they are given in the correct order, however, they struggle to compose the correct order themselves. This further indicates that LLMs lack the necessary robust compositional generalization in morphology.

#### <span id="page-7-0"></span>5.5 **Effect of Negative Sample Selection**

In our systematicity task, we generate negative samples (i.e. derived combinations that are not grammatically correct) by permuting the order of morphemes attached to the root. While the number of permutations is manageable for 2 or 3 morphemes (e.g.,  $2!=2$ ,  $3!=6$ ), it grows rapidly with more morphemes (e.g.,  $6!=720$ ). Evaluating all permutations would be ideal for robust systematicity testing, but this is infeasible due to high computational costs. Instead, we can select a subset of reasonable size to be a representative sample of all possible negative options. However, the strategy for which samples and how many to select can be somewhat arbitrary. Therefore, we experiment with three different selection strategies, and set the number of selections to four for simplicity: 1) **random** where we randomly select four negative options; 2) language-agnostic **heuristic** where we select the top four negative options that are closest to the positive option measured by Levenshtein distance (our default strategy); and 3) **language-specific heuristic** where we employ linguistic features of the tested language to filter out options that may be "too easy" for the model. We found one such heuristic for Turkish test

suite based on the fact that Turkish phonology does not allow two adjacent vowels in morpheme combinations which we describe in Appendix E. We report the results of these different negative sample selection experiments in Figure 8. We see that the random selection has the highest performance on both ID and OOD test sets, followed by the language-agnostic and language-specific strategies. This implies that all our previous model results might be an upper bound and the true performance gap compared to humans is even larger than what we observe.

<span id="page-7-2"></span>![](_page_7_Figure_6.jpeg)

Figure 8: Morphological systematicity task results for Turkish showing the effect of different negative sample selection strategies. Detailed results are in Appendix Table 52.

#### 5.6 **Error Analysis**

In order to understand the limitations of language models on our tasks, we manually analyze 30 Turkish word derivations for each morpheme combination length (1-7) and for both productivity ID and OOD test sets resulting in a total of 178 and 185 derivations from GPT-4 that are incorrect. We annotate each generation on three criteria: 1) whether the generation is an invalid word (i.e. grammatically incorrect word) 2) whether the generation is unfaithful (i.e. generation does not follow the productivity task constraints) and 3) whether the generation includes any hallucinations (i.e. whether the generation has extra morphemes not mentioned in the task prompt). Our analysis shows that while on the OOD test set, GPT-4 generates a grammatically incorrect word most of the time (79%), this proportion is significantly lower for the ID test set (31%). However, on the ID test set, we observe a high unfaithfulness and hallucination ratio (91% and 67%) meaning that most of the valid generations do not follow the task constraints. On the other hand, we see lower unfaithfulness and hallucination ratios on the OOD test (75% and 52% respectively) which points to a *real word bias* also reported by [\(Weissweiler et al.,](#page-11-1) [2023\)](#page-11-1) where the model is biased toward generating frequent words for word roots existing in a given language irrespective of the underlying task. In other words, OOD setting forces the model to perform the true morphological generalization task which it fails as indicated by the higher percentage of invalid derivations. To identify the root causes of some of these errors, we analyze the GPT-4 chain-of-thought answers on the Turkish data and reveal several failure modes such as sequential dependency errors, semantic misinterpretations, lack of grammatical knowledge, and unfaithful reasoning, all of which we detail with examples in Appendix [A.4.](#page-13-0) Finally, we also analyze the few errors human annotators made and find that these errors are either trivial typos or failure to notice an extra letter in a long word.

# 6 Conclusion

In this paper, we proposed a novel experimental paradigm to test morphological generalization abilities of large language models through compositionality. Our tasks target measuring morphological productivity and systematicity in a given language. We applied these tasks on the morphologically complex languages of Turkish and Finnish and evaluated morphological compositional generalization abilities of several state-of-the-art large language models. Our experimental results and analysis reveal a significant gap in the performance of LLMs compared to humans with respect to generalization in morphology of agglutinative languages.

## Limitations

While our novel tasks are language, dataset, and model-independent, our study only focused on two agglutinative languages and a few large language models. Therefore, the applicability of our findings in other languages and models should be further studied. We also mainly focused on the grammatical validity of the words, whereas it would be equally interesting to study the capacity of LLMs to produce and understand novel semantically and pragmatically valid derivations. While we have also optimized our prompts to be as simple and maximally instructive and tested in multiple languages and in chain-of-thought setting, whether a different set of prompts would produce the same results is not clear. Finally, we mainly evaluate models using greedy decoding due to the deterministic nature of our tasks and additionally only experiment with temperature and top-p sampling, however, the effect of different decoding strategies needs to be explored.

## Acknowledgments

We gratefully acknowledge the support of the Swiss National Science Foundation (grant 205121\_207437: C - LING) and the Microsoft Accelerating Foundation Models Research Program. Defne would also like to acknowledge the support of the National Science Foundation under grant DGE-2022040. We also thank Mammad Hajili, Osman Batur Ince, Omer Goldman, members of the NLP Lab at EPFL and the CCL Group at Idiap Research Institute for their valuable feedback in the early stages of this project and Raghav Mantri for his help with the Gemini experiments.

## References

- <span id="page-8-1"></span>Farrell Ackerman and Robert Malouf. 2013. [Morpho](https://doi.org/10.1353/lan.2013.0054)[logical organization: The low conditional entropy](https://doi.org/10.1353/lan.2013.0054) [conjecture.](https://doi.org/10.1353/lan.2013.0054) *Language*, 89:429–464.
- <span id="page-8-0"></span>Shengnan An, Zeqi Lin, Qiang Fu, Bei Chen, Nanning Zheng, Jian-Guang Lou, and Dongmei Zhang. 2023. [How do in-context examples affect compo](https://doi.org/10.18653/v1/2023.acl-long.618)[sitional generalization?](https://doi.org/10.18653/v1/2023.acl-long.618) In *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 11027– 11052, Toronto, Canada. Association for Computational Linguistics.

- <span id="page-9-6"></span>Dang Anh, Limor Raviv, and Lukas Galke. 2024. [Mor](https://doi.org/10.18653/v1/2024.cmcl-1.15)[phology matters: Probing the cross-linguistic mor](https://doi.org/10.18653/v1/2024.cmcl-1.15)[phological generalization abilities of large language](https://doi.org/10.18653/v1/2024.cmcl-1.15) [models through a wug test.](https://doi.org/10.18653/v1/2024.cmcl-1.15) In *Proceedings of the Workshop on Cognitive Modeling and Computational Linguistics*, pages 177–188, Bangkok, Thailand. Association for Computational Linguistics.
- <span id="page-9-13"></span>Mark Aronoff and Mark Lindsay. 2014. [67productivity,](https://doi.org/10.1093/oxfordhb/9780199641642.013.0005) [blocking, and lexicalization.](https://doi.org/10.1093/oxfordhb/9780199641642.013.0005) In *The Oxford Handbook of Derivational Morphology*. Oxford University Press.
- <span id="page-9-17"></span>Viraat Aryabumi, John Dang, Dwarak Talupuru, Saurabh Dash, David Cairuz, Hangyu Lin, Bharat Venkitesh, Madeline Smith, Jon Ander Campos, Yi Chern Tan, Kelly Marchisio, Max Bartolo, Sebastian Ruder, Acyr Locatelli, Julia Kreutzer, Nick Frosst, Aidan Gomez, Phil Blunsom, Marzieh Fadaee, Ahmet Üstün, and Sara Hooker. 2024. [Aya 23:](https://arxiv.org/abs/2405.15032) [Open weight releases to further multilingual progress.](https://arxiv.org/abs/2405.15032) *Preprint*, arXiv:2405.15032.
- <span id="page-9-2"></span>Marco Baroni. 2019. [Linguistic generalization and](https://api.semanticscholar.org/CorpusID:90260325) [compositionality in modern artificial neural networks.](https://api.semanticscholar.org/CorpusID:90260325) *Philosophical Transactions of the Royal Society B*, 375.
- <span id="page-9-12"></span>Laurie Bauer. 2001. *Morphological Productivity*. Cambridge Studies in Linguistics. Cambridge University Press.
- <span id="page-9-4"></span>Alexander Bergs. 2019. [What, if anything, is linguistic](https://doi.org/10.2478/gth-2019-0017) [creativity?](https://doi.org/10.2478/gth-2019-0017) *Gestalt Theory*, 41:173–183.
- <span id="page-9-10"></span>Jean Berko Gleason. 1958. [The child's learning of](https://doi.org/10.1080/00437956.1958.11659661) [english morphology.](https://doi.org/10.1080/00437956.1958.11659661) *Word*, 14.
- <span id="page-9-19"></span>Kaj Bostrom and Greg Durrett. 2020. [Byte pair encod](https://doi.org/10.18653/v1/2020.findings-emnlp.414)[ing is suboptimal for language model pretraining.](https://doi.org/10.18653/v1/2020.findings-emnlp.414) In *Findings of the Association for Computational Linguistics: EMNLP 2020*, pages 4617–4624, Online. Association for Computational Linguistics.
- <span id="page-9-1"></span>Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, Sandhini Agarwal, Ariel Herbert-Voss, Gretchen Krueger, Tom Henighan, Rewon Child, Aditya Ramesh, Daniel M. Ziegler, Jeffrey Wu, Clemens Winter, Christopher Hesse, Mark Chen, Eric Sigler, Mateusz Litwin, Scott Gray, Benjamin Chess, Jack Clark, Christopher Berner, Sam Mc-Candlish, Alec Radford, Ilya Sutskever, and Dario Amodei. 2020. [Language models are few-shot learn](https://arxiv.org/abs/2005.14165)[ers.](https://arxiv.org/abs/2005.14165) *Preprint*, arXiv:2005.14165.
- <span id="page-9-0"></span>Sébastien Bubeck, Varun Chandrasekaran, Ronen Eldan, Johannes Gehrke, Eric Horvitz, Ece Kamar, Peter Lee, Yin Tat Lee, Yuanzhi Li, Scott Lundberg, Harsha Nori, Hamid Palangi, Marco Tulio Ribeiro, and Yi Zhang. 2023. [Sparks of artificial general in](https://arxiv.org/abs/2303.12712)[telligence: Early experiments with gpt-4.](https://arxiv.org/abs/2303.12712) *Preprint*, arXiv:2303.12712.

- <span id="page-9-9"></span>Marc E. Canby, Aidana Karipbayeva, Bryan Lunt, Sahand Mozaffari, Charlotte Yoder, and J. Hockenmaier. 2020. [University of illinois submission to the sig](https://api.semanticscholar.org/CorpusID:220285091)[morphon 2020 shared task 0: Typologically diverse](https://api.semanticscholar.org/CorpusID:220285091) [morphological inflection.](https://api.semanticscholar.org/CorpusID:220285091) In *Special Interest Group on Computational Morphology and Phonology Workshop*.
- <span id="page-9-11"></span>Rudolf Carnap. 1947. *Meaning and necessity: A study in semantics and modal logic*, volume 30. University of Chicago Press.
- <span id="page-9-5"></span>N. Chomsky. 1957. *[Syntactic Structures](https://books.google.ch/books?id=55YaAAAAIAAJ)*. Janua linguarum (Mouton, Paris).: Series Minor. Mouton.
- <span id="page-9-3"></span>Noam Chomsky. 1965. *[Aspects of the Theory of Syntax](http://www.jstor.org/stable/j.ctt17kk81z)*, 50 edition. The MIT Press.
- <span id="page-9-18"></span>Jacob Cohen. 1960. [A coefficient of agreement for](https://doi.org/10.1177/001316446002000104) [nominal scales.](https://doi.org/10.1177/001316446002000104) *Educational and Psychological Measurement*, 20(1):37–46.
- <span id="page-9-14"></span>Ryan Cotterell, Christo Kirov, Mans Hulden, and Jason Eisner. 2019. On the complexity and typology of inflectional morphological systems. *Transactions of the Association for Computational Linguistics*, 7:327– 342.
- <span id="page-9-8"></span>Ryan Cotterell, Christo Kirov, John Sylak-Glassman, Géraldine Walther, Ekaterina Vylomova, Arya D. Mc-Carthy, Katharina Kann, Sabrina J. Mielke, Garrett Nicolai, Miikka Silfverberg, David Yarowsky, Jason Eisner, and Mans Hulden. 2018a. [The CoNLL–](https://doi.org/10.18653/v1/K18-3001) [SIGMORPHON 2018 shared task: Universal mor](https://doi.org/10.18653/v1/K18-3001)[phological reinflection.](https://doi.org/10.18653/v1/K18-3001) In *Proceedings of the CoNLL–SIGMORPHON 2018 Shared Task: Universal Morphological Reinflection*, pages 1–27, Brussels. Association for Computational Linguistics.
- <span id="page-9-7"></span>Ryan Cotterell, Christo Kirov, John Sylak-Glassman, David Yarowsky, Jason Eisner, and Mans Hulden. 2016. [The sigmorphon 2016 shared](https://api.semanticscholar.org/CorpusID:18613906) [task—morphological reinflection.](https://api.semanticscholar.org/CorpusID:18613906) In *Special Interest Group on Computational Morphology and Phonology Workshop*.
- <span id="page-9-15"></span>Ryan Cotterell, Sabrina J. Mielke, Jason Eisner, and Brian Roark. 2018b. [Are all languages equally hard](https://doi.org/10.18653/v1/N18-2085) [to language-model?](https://doi.org/10.18653/v1/N18-2085) In *Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 2 (Short Papers)*, pages 536–541, New Orleans, Louisiana. Association for Computational Linguistics.
- <span id="page-9-16"></span>Paula Czarnowska, Sebastian Ruder, Edouard Grave, Ryan Cotterell, and Ann Copestake. 2019. [Don't](https://doi.org/10.18653/v1/D19-1090) [forget the long tail! a comprehensive analysis of](https://doi.org/10.18653/v1/D19-1090) [morphological generalization in bilingual lexicon in](https://doi.org/10.18653/v1/D19-1090)[duction.](https://doi.org/10.18653/v1/D19-1090) In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 974–983, Hong Kong, China. Association for Computational Linguistics.

- <span id="page-10-8"></span>Nouha Dziri, Ximing Lu, Melanie Sclar, Xiang Lorraine Li, Liwei Jian, Bill Yuchen Lin, Peter West, Chandra Bhagavatula, Ronan Le Bras, Jena D. Hwang, Soumya Sanyal, Sean Welleck, Xiang Ren, Allyson Ettinger, Zaïd Harchaoui, and Yejin Choi. 2023. [Faith and fate: Limits of transformers on compo](https://api.semanticscholar.org/CorpusID:258967391)[sitionality.](https://api.semanticscholar.org/CorpusID:258967391) *ArXiv*, abs/2305.18654.
- <span id="page-10-4"></span>Jerry A. Fodor and Zenon W. Pylyshyn. 1988a. [Connec](https://doi.org/10.1016/0010-0277(88)90031-5)[tionism and cognitive architecture: A critical analysis.](https://doi.org/10.1016/0010-0277(88)90031-5) *Cognition*, 28(1):3–71.
- <span id="page-10-12"></span>Jerry A Fodor and Zenon W Pylyshyn. 1988b. Connectionism and cognitive architecture: A critical analysis. *Cognition*, 28(1-2):3–71.
- <span id="page-10-0"></span>Team Gemini. 2024. [Gemini: A family of highly capa](https://arxiv.org/abs/2312.11805)[ble multimodal models.](https://arxiv.org/abs/2312.11805) *Preprint*, arXiv:2312.11805.
- <span id="page-10-10"></span>Omer Goldman, Khuyagbaatar Batsuren, Salam Khalifa, Aryaman Arora, Garrett Nicolai, Reut Tsarfaty, and Ekaterina Vylomova. 2023. [Sigmorphon–unimorph](https://api.semanticscholar.org/CorpusID:259833795) [2023 shared task 0: Typologically diverse morpho](https://api.semanticscholar.org/CorpusID:259833795)[logical inflection.](https://api.semanticscholar.org/CorpusID:259833795) In *Special Interest Group on Computational Morphology and Phonology Workshop*.
- <span id="page-10-2"></span>Omer Goldman, David Guriel, and Reut Tsarfaty. 2022. [\(un\)solving morphological inflection: Lemma over](https://doi.org/10.18653/v1/2022.acl-short.96)[lap artificially inflates models' performance.](https://doi.org/10.18653/v1/2022.acl-short.96) In *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 2: Short Papers)*, pages 864–870, Dublin, Ireland. Association for Computational Linguistics.
- <span id="page-10-16"></span>Emily Goodwin, Koustuv Sinha, and Timothy J. O'Donnell. 2020. [Probing linguistic systematicity.](https://doi.org/10.18653/v1/2020.acl-main.177) In *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, pages 1958– 1969, Online. Association for Computational Linguistics.
- <span id="page-10-17"></span>Mika Hämäläinen. 2019. [Uralicnlp: An nlp library for](https://doi.org/10.21105/joss.01345) [uralic languages.](https://doi.org/10.21105/joss.01345) *Journal of Open Source Software*, 4(37):1345.
- <span id="page-10-15"></span>Charles F Hockett. 1954. Two models of grammatical description. *Word*, 10(2-3):210–234.
- <span id="page-10-20"></span>Valentin Hofmann, Janet Pierrehumbert, and Hinrich Schütze. 2021. [Superbizarre is not superb: Deriva](https://doi.org/10.18653/v1/2021.acl-long.279)[tional morphology improves BERT's interpretation](https://doi.org/10.18653/v1/2021.acl-long.279) [of complex words.](https://doi.org/10.18653/v1/2021.acl-long.279) In *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, pages 3594–3608, Online. Association for Computational Linguistics.
- <span id="page-10-6"></span>Daniel Keysers, Nathanael Schärli, Nathan Scales, Hylke Buisman, Daniel Furrer, Sergii Kashubin, Nikola Momchev, Danila Sinopalnikov, Lukasz Stafiniak, Tibor Tihon, Dmitry Tsarkov, Xiao Wang, Marc van Zee, and Olivier Bousquet. 2019. [Measur](https://api.semanticscholar.org/CorpusID:209439843)[ing compositional generalization: A comprehensive](https://api.semanticscholar.org/CorpusID:209439843) [method on realistic data.](https://api.semanticscholar.org/CorpusID:209439843) *ArXiv*, abs/1912.09713.

- <span id="page-10-7"></span>Najoung Kim and Tal Linzen. 2020. [COGS: A compo](https://doi.org/10.18653/v1/2020.emnlp-main.731)[sitional generalization challenge based on semantic](https://doi.org/10.18653/v1/2020.emnlp-main.731) [interpretation.](https://doi.org/10.18653/v1/2020.emnlp-main.731) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 9087–9105, Online. Association for Computational Linguistics.
- <span id="page-10-13"></span>Paul Kiparsky. 1982a. Lexical morphology and phonology. *Linguistics in the Morning Calm/Hanshin*.
- <span id="page-10-14"></span>Paul Kiparsky. 1982b. Word formation and the lexicon. In *1982 Mid America Linguistics Conference Papers/Dept. of Ling., Univ. of Kansas*.
- <span id="page-10-9"></span>Jordan Kodner and Salam Khalifa. 2022. [Sigmor](https://api.semanticscholar.org/CorpusID:250390522)[phon–unimorph 2022 shared task 0: Modeling in](https://api.semanticscholar.org/CorpusID:250390522)[flection in language acquisition.](https://api.semanticscholar.org/CorpusID:250390522) *Proceedings of the 19th SIGMORPHON Workshop on Computational Research in Phonetics, Phonology, and Morphology*.
- <span id="page-10-5"></span>Brenden M. Lake and Marco Baroni. 2018. [General](https://arxiv.org/abs/1711.00350)[ization without systematicity: On the compositional](https://arxiv.org/abs/1711.00350) [skills of sequence-to-sequence recurrent networks.](https://arxiv.org/abs/1711.00350) *Preprint*, arXiv:1711.00350.
- <span id="page-10-21"></span>Jindˇrich Libovický, Helmut Schmid, and Alexander M. Fraser. 2021. [Why don't people use character-level](https://api.semanticscholar.org/CorpusID:239009602) [machine translation?](https://api.semanticscholar.org/CorpusID:239009602) In *Findings*.
- <span id="page-10-3"></span>Tal Linzen. 2020. [How can we accelerate progress](https://api.semanticscholar.org/CorpusID:218487293) [towards human-like linguistic generalization?](https://api.semanticscholar.org/CorpusID:218487293) In *Annual Meeting of the Association for Computational Linguistics*.
- <span id="page-10-18"></span>Risto Luukkonen, Jonathan Burdge, Elaine Zosa, Aarne Talman, Ville Komulainen, Väinö Hatanpää, Peter Sarlin, and Sampo Pyysalo. 2024. [Poro 34b](https://arxiv.org/abs/2404.01856) [and the blessing of multilinguality.](https://arxiv.org/abs/2404.01856) *Preprint*, arXiv:2404.01856.
- <span id="page-10-11"></span>Arya D. McCarthy, Christo Kirov, Matteo Grella, Amrit Nidhi, Patrick Xia, Kyle Gorman, Ekaterina Vylomova, Sabrina J. Mielke, Garrett Nicolai, Miikka Silfverberg, Timofey Arkhangelskiy, Nataly Krizhanovsky, Andrew Krizhanovsky, Elena Klyachko, Alexey Sorokin, John Mansfield, Valts Erntreits, Yuval Pinter, Cassandra L. Jacobs, Ryan Cotterell, Mans Hulden, and David Yarowsky. 2020. [Unimorph](https://api.semanticscholar.org/CorpusID:263891360) [3.0: Universal morphology.](https://api.semanticscholar.org/CorpusID:263891360) In *International Conference on Language Resources and Evaluation*.
- <span id="page-10-1"></span>R. Thomas McCoy, Paul Smolensky, Tal Linzen, Jianfeng Gao, and Asli Celikyilmaz. 2023. [How much](https://doi.org/10.1162/tacl_a_00567) [do language models copy from their training data?](https://doi.org/10.1162/tacl_a_00567) [evaluating linguistic novelty in text generation using](https://doi.org/10.1162/tacl_a_00567) [RAVEN.](https://doi.org/10.1162/tacl_a_00567) *Transactions of the Association for Computational Linguistics*, 11:652–670.
- <span id="page-10-19"></span>Francois Meyer and Jan Buys. 2023. [Subword segmen](https://doi.org/10.18653/v1/2023.findings-acl.175)[tal machine translation: Unifying segmentation and](https://doi.org/10.18653/v1/2023.findings-acl.175) [target sentence generation.](https://doi.org/10.18653/v1/2023.findings-acl.175) In *Findings of the Association for Computational Linguistics: ACL 2023*, pages 2795–2809, Toronto, Canada. Association for Computational Linguistics.

- <span id="page-11-5"></span>Timothy J O'Donnell. 2015. *Productivity and reuse in language: A theory of linguistic computation and storage*. MIT Press.
- <span id="page-11-10"></span>OpenAI. 2024. [Gpt-4 technical report.](https://arxiv.org/abs/2303.08774) *Preprint*, arXiv:2303.08774.
- <span id="page-11-6"></span>Adnan Ozturel, Tolga Kayadelen, and Demirsahin I. 2019. [A syntactically expressive morphological an](https://www.aclweb.org/anthology/W19-3110)[alyzer for turkish.](https://www.aclweb.org/anthology/W19-3110) In *Proceedings of the 14th International Conference on Finite-State Methods and Natural Language Processing*, pages 65–75, Dresden, Germany. Association for Computational Linguistics.
- <span id="page-11-14"></span>Pouya Pezeshkpour and Estevam Hruschka. 2023. [Large language models sensitivity to the order of](https://arxiv.org/abs/2308.11483) [options in multiple-choice questions.](https://arxiv.org/abs/2308.11483) *Preprint*, arXiv:2308.11483.
- <span id="page-11-8"></span>Tommi A Pirinen. 2015. Development and use of computational morphology of finnish in the open source and open science era: Notes on experiences with omorfi development. *SKY Journal of Linguistics*, 28:381–393.
- <span id="page-11-13"></span>Rico Sennrich, Barry Haddow, and Alexandra Birch. 2016. [Neural machine translation of rare words with](https://doi.org/10.18653/v1/P16-1162) [subword units.](https://doi.org/10.18653/v1/P16-1162) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 1715–1725, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-11-12"></span>Shane Storks and Joyce Chai. 2021. [Beyond the tip of](https://doi.org/10.18653/v1/2021.findings-emnlp.272) [the iceberg: Assessing coherence of text classifiers.](https://doi.org/10.18653/v1/2021.findings-emnlp.272) In *Findings of the Association for Computational Linguistics: EMNLP 2021*, pages 3169–3177, Punta Cana, Dominican Republic. Association for Computational Linguistics.
- <span id="page-11-9"></span>Qwen Team. 2024. [Qwen2.5: A party of foundation](https://qwenlm.github.io/blog/qwen2.5/) [models.](https://qwenlm.github.io/blog/qwen2.5/)
- <span id="page-11-16"></span>Cagri Toraman, Eyup Halit Yilmaz, Furkan ¸Sahinuç, and Oguzhan Ozcelik. 2022. [Impact of tokenization](https://api.semanticscholar.org/CorpusID:248240018) [on language models: An analysis for turkish.](https://api.semanticscholar.org/CorpusID:248240018) *ACM Transactions on Asian and Low-Resource Language Information Processing*, 22:1 – 21.
- <span id="page-11-11"></span>Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, Aurelien Rodriguez, Armand Joulin, Edouard Grave, and Guillaume Lample. 2023. [Llama: Open](https://arxiv.org/abs/2302.13971) [and efficient foundation language models.](https://arxiv.org/abs/2302.13971) *Preprint*, arXiv:2302.13971.
- <span id="page-11-4"></span>Ekaterina Vylomova, Jennifer White, Elizabeth Salesky, Sabrina J. Mielke, Shijie Wu, Edoardo Maria Ponti, Rowan Hall Maudslay, Ran Zmigrod, Josef Valvoda, Svetlana Toldova, Francis Tyers, Elena Klyachko, Ilya Yegorov, Natalia Krizhanovsky, Paula Czarnowska, Irene Nikkarinen, Andrew Krizhanovsky, Tiago Pimentel, Lucas Torroba Hennigen, Christo Kirov, Garrett Nicolai, Adina Williams, Antonios Anastasopoulos, Hilaria Cruz, Eleanor

Chodroff, Ryan Cotterell, Miikka Silfverberg, and Mans Hulden. 2020. [SIGMORPHON 2020 shared](https://doi.org/10.18653/v1/2020.sigmorphon-1.1) [task 0: Typologically diverse morphological inflec](https://doi.org/10.18653/v1/2020.sigmorphon-1.1)[tion.](https://doi.org/10.18653/v1/2020.sigmorphon-1.1) In *Proceedings of the 17th SIGMORPHON Workshop on Computational Research in Phonetics, Phonology, and Morphology*, pages 1–39, Online. Association for Computational Linguistics.

- <span id="page-11-15"></span>Jiongxiao Wang, Zichen Liu, Keun Hee Park, Zhuojun Jiang, Zhaoheng Zheng, Zhuofeng Wu, Muhao Chen, and Chaowei Xiao. 2023. [Adversarial demon](https://arxiv.org/abs/2305.14950)[stration attacks on large language models.](https://arxiv.org/abs/2305.14950) *Preprint*, arXiv:2305.14950.
- <span id="page-11-0"></span>Jason Wei, Yi Tay, Rishi Bommasani, Colin Raffel, Barret Zoph, Sebastian Borgeaud, Dani Yogatama, Maarten Bosma, Denny Zhou, Donald Metzler, Ed H. Chi, Tatsunori Hashimoto, Oriol Vinyals, Percy Liang, Jeff Dean, and William Fedus. 2022. [Emer](https://arxiv.org/abs/2206.07682)[gent abilities of large language models.](https://arxiv.org/abs/2206.07682) *Preprint*, arXiv:2206.07682.
- <span id="page-11-17"></span>Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, and Denny Zhou. 2023. [Chain-of-thought prompting elic](https://arxiv.org/abs/2201.11903)[its reasoning in large language models.](https://arxiv.org/abs/2201.11903) *Preprint*, arXiv:2201.11903.
- <span id="page-11-1"></span>Leonie Weissweiler, Valentin Hofmann, Anjali Kantharuban, Anna Cai, Ritam Dutt, Amey Hengle, Anubha Kabra, Atharva Kulkarni, Abhishek Vijayakumar, Haofei Yu, Hinrich Schuetze, Kemal Oflazer, and David Mortensen. 2023. [Counting the](https://doi.org/10.18653/v1/2023.emnlp-main.401) [bugs in ChatGPT's wugs: A multilingual investiga](https://doi.org/10.18653/v1/2023.emnlp-main.401)[tion into the morphological capabilities of a large](https://doi.org/10.18653/v1/2023.emnlp-main.401) [language model.](https://doi.org/10.18653/v1/2023.emnlp-main.401) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pages 6508–6524, Singapore. Association for Computational Linguistics.
- <span id="page-11-18"></span>Chris Wendler, Veniamin Veselovsky, Giovanni Monea, and Robert West. 2024. [Do llamas work in English?](https://doi.org/10.18653/v1/2024.acl-long.820) [on the latent language of multilingual transformers.](https://doi.org/10.18653/v1/2024.acl-long.820) In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 15366–15394, Bangkok, Thailand. Association for Computational Linguistics.
- <span id="page-11-2"></span>Michael Wilson, Jackson Petty, and Robert Frank. 2023. [How abstract is linguistic generalization in large lan](https://doi.org/10.1162/tacl_a_00608)[guage models? experiments with argument structure.](https://doi.org/10.1162/tacl_a_00608) *Transactions of the Association for Computational Linguistics*, 11:1377–1395.
- <span id="page-11-3"></span>Katherine Wysocki and Joseph R. Jenkins. 1987. [Deriv](http://www.jstor.org/stable/747721)[ing word meanings through morphological general](http://www.jstor.org/stable/747721)[ization.](http://www.jstor.org/stable/747721) *Reading Research Quarterly*, 22(1):66–81.
- <span id="page-11-7"></span>Linting Xue, Noah Constant, Adam Roberts, Mihir Kale, Rami Al-Rfou, Aditya Siddhant, Aditya Barua, and Colin Raffel. 2021. [mT5: A massively multilingual](https://doi.org/10.18653/v1/2021.naacl-main.41) [pre-trained text-to-text transformer.](https://doi.org/10.18653/v1/2021.naacl-main.41) In *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pages 483–498, Online. Association for Computational Linguistics.

- <span id="page-12-1"></span>Haoran Yang, Hongyuan Lu, Wai Lam, and Deng Cai. 2024. Exploring compositional generalization of large language models. In *Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 4: Student Research Workshop)*, pages 16–24.
- <span id="page-12-2"></span>Wlodek Zadrozny. 1994. From compositional to systematic semantics. *Linguistics and philosophy*, 17:329– 342.
- <span id="page-12-6"></span>Ruochen Zhang, Samuel Cahyawijaya, Jan Christian Blaise Cruz, Genta Winata, and Alham Aji. 2023. [Multilingual large language models are not](https://doi.org/10.18653/v1/2023.emnlp-main.774) [\(yet\) code-switchers.](https://doi.org/10.18653/v1/2023.emnlp-main.774) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pages 12567–12582, Singapore. Association for Computational Linguistics.
- <span id="page-12-5"></span>Tony Z. Zhao, Eric Wallace, Shi Feng, Dan Klein, and Sameer Singh. 2021. [Calibrate before use: Im](https://arxiv.org/abs/2102.09690)[proving few-shot performance of language models.](https://arxiv.org/abs/2102.09690) *Preprint*, arXiv:2102.09690.
- <span id="page-12-0"></span>Wayne Xin Zhao, Kun Zhou, Junyi Li, Tianyi Tang, Xiaolei Wang, Yupeng Hou, Yingqian Min, Beichen Zhang, Junjie Zhang, Zican Dong, Yifan Du, Chen Yang, Yushuo Chen, Zhipeng Chen, Jinhao Jiang, Ruiyang Ren, Yifan Li, Xinyu Tang, Zikang Liu, Peiyu Liu, Jian-Yun Nie, and Ji-Rong Wen. 2023. [A survey of large language models.](https://arxiv.org/abs/2303.18223) *Preprint*, arXiv:2303.18223.
- <span id="page-12-4"></span>Kaijie Zhu, Jindong Wang, Jiaheng Zhou, Zichen Wang, Hao Chen, Yidong Wang, Linyi Yang, Wei Ye, Yue Zhang, Neil Zhenqiang Gong, and Xing Xie. 2024. [Promptrobust: Towards evaluating the robustness](https://arxiv.org/abs/2306.04528) [of large language models on adversarial prompts.](https://arxiv.org/abs/2306.04528) *Preprint*, arXiv:2306.04528.

## A Additional Analysis

#### <span id="page-12-7"></span>A.1 Effect of Instruction Language

Since most LLMs are pre-trained on significantly more instruction data in English than other languages, we base most of our results on experiments where we use English as the prompt instruction language. However, as our data is in a different language, this results in a code-switched language which has been shown to be a challenge for large language models [\(Zhang et al.,](#page-12-6) [2023\)](#page-12-6). To measure the effect of the instruction language on the morphological generalization tasks, we run our experiments with Turkish and Finnish as the instruction language and report results for both tasks in Figure [9.](#page-13-1) We mostly observe a drop or no change in performance when the instruction language is other than English.

#### <span id="page-12-8"></span>A.2 Effect of Chain-of-thought Reasoning

Chain-of-thought prompting has been shown to be effective in eliciting strong reasoning capabilities from LLMs [\(Wei et al.,](#page-11-17) [2023\)](#page-11-17). In order to measure the effect of this reasoning technique on LLMs' performance on our tasks, we evaluate GPT-4 (the best performing model) on both productivity and systematicity tasks in zero-shot and 5-shot chainof-thought settings. We report the results of these experiments compared with the 5-shot standard prompting in Figure [10.](#page-13-2) We observe that while 5-shot chain-of-thought performance is better than the zero-shot chain-of-thought, it is slightly worse than or similar to the 5-shot standard prompting. To identify the causes of these errors, we manually analyze the several chain-of-thought answers which we describe in Appendix [A.4.](#page-13-0)

## <span id="page-12-3"></span>A.3 Further details on the effect of morphological complexity

In Figure [4,](#page-6-0) we observe a surprisingly low performance (≈ 40% drop from ID performance) on the 1-morpheme OOD words, but we attribute this behaviour to the varying number of negative options available for each morpheme length and possible presence of shortcuts in larger morpheme words. We should note that we have different number of total options to discriminate for a given sample depending on the number of morphemes (for 1 and 2 morphemes, we have 2 options, for 3-7, we have 5 options). Hence, a single mistake is penalized more in the former case than in the latter. However, within the former category, we see a

<span id="page-13-1"></span>![](_page_13_Figure_0.jpeg)

Figure 9: Morphological productivity and systematicity task results for Turkish showing the effect of the **instruction language.** Detailed results are in Table 30. Results for Finnish can be found in Figure 12.

<span id="page-13-2"></span>![](_page_13_Figure_2.jpeg)

Figure 10: GPT-4 morphological productivity and systematicity task results for Turkish showing the effect of **chain-of-thought reasoning.** Detailed results are in Table 43.

much higher performance for 2-morpheme examples which might seem surprising, however, we hypothesize that this could be due to the presence of potential shortcuts for the model to exploit in the 2-morpheme case. Indeed, if we analyze the proportion of errors in both cases, we find that in the 1-morpheme case, a significant portion of errors ( $64\%$ ) is false negative i.e. the model identifies a nonce root with a valid morpheme as grammatically incorrect, while this is not the case in the 2-morpheme case. However, in the 2-morpheme case, the model might be exploiting the correct order of morphemes as sole evidence for the validity of the derivation while in the 1-morpheme case, there is no such shortcut and the model should understand the applicability of the given morpheme to the given word root.

## <span id="page-13-0"></span>A.4 Chain-of-thought Error Analysis

We randomly sample 10 examples from the 5-shot chain-of-thought experiments on the Turkish evaluation data (per morpheme length and test distribution) where GPT-4 made an error and manually analyze its answers across both tasks. Our analysis reveals the following primary types of errors:

### 1. Sequential Dependency Errors

One common error we observe in the productivity task is due to the sequential processing

of the given affixes by GPT-4. It typically starts applying the given affixes in the order they are given, however, since the affixes are typically given in shuffled order, this often results in an invalid word early on. The model, however, does not seem to realize its mistake and continues with the generation often confidently assigning meaning to the intermediate erroneous words. For example, given the word root "hedef" and affixes "-in", "-diğ" and "le", it considers the affixes sequentially in this order by first producing "hedefin" which is valid, then "hedefindiğ" which is invalid, however, it interprets the generation as "which is the target" and finally produces "hedefindiğle" which it interprets as "with what is the target".

#### 2. Semantic Misinterpretations

Another set of errors stems from GPT-4 misinterpreting the meaning of the individual morphemes or the whole derivation. For instance, in one example, where the given morphemes are "bağır" ("to shout"), "-sa" and "-k" and GPT-4 is asked to determine the validity of the combination "bağırsak", it misinterprets this derivation as meaning "intestine" (which is also written as "bağırsak") and argues that this derivation can not be made up of the given affixes. While this reasoning is correct, the

model misses the other plausible meaning of this derivation ("as if we shout") that can be derived from the given morphemes. In another example, where the model is given the morphemes "oyna" and "-sana" and asked to produce a valid word, it misinterprets the meaning of the morpheme "-sana" as "to you" and argues that it can not be applied to the root "oyna" whereas "-sana" is a valid suffix added to verbs.

## 3. Lack of Grammatical Knowledge

Another common pattern we see can be attributed to the lack of proper grammatical knowledge. In one example, the model is given the morphemes "uyum", "-suz", "-luk" and "-ta" and asked to determine the validity of the derivation "uyumluktasuz" which is invalid, however, the model assesses the validity of each morpheme and concludes that the combination should also be valid. In another example, it tries to add a verb suffix to a noun ("yargıyoruz"). Yet in other examples, it argues that valid affixes do not exist in the language or a valid morphological combination is not possible.

### 4. Unfaithful Reasoning

Finally, we also observe a large set of reasoning errors due to inconsistent reasoning chains, hallucinations or unfaithful instruction following. For instance, in one example, GPT-4 concatenates the morphemes "unut" and "-alı" and yet derives "unutuluyor". In another example, it auto-corrects an invalid word ("kaldırınızdıgda") to a valid word ˘ "kaldırdıgınızda" and argues that the original ˘ derivation is correct.

## <span id="page-14-1"></span>A.5 Effect of Decoding Strategies

We mainly experiment with greedy decoding (e.g. temperature is set to 0 and top\_p is set to 1) in all of our experiments as the nature of our tasks is deterministic. However, to check the sensitivity of our findings across diverse decoding settings, we additionally run our study with GPT-4 (the best performing model) on both tasks and languages with varying temperature and top\_p values and report the results in Tables [53,](#page-35-0) [54,](#page-35-1) [55](#page-35-2) and [56](#page-35-3) respectively. We find no significant or systematic differences across different decoding strategies which strengthens the robustness of our findings.

## <span id="page-14-2"></span>A.6 Effect of Prompt Instructions

Due to the cost of LLM evaluation, we mainly experiment with one set of prompt instructions that we have found to be simple and effective through a moderate level of prompt engineering. However, to check the sensitivity of our findings across different prompt instructions, we additionally run our study with GPT-4 (the best performing model) on both tasks and languages with a paraphrased version of the original prompt instructions (found in Appendix [F\)](#page-16-1) and report the results in Tables [57](#page-35-4) and [58.](#page-35-5) We find no significant or systematic differences across different prompts which strengthens the robustness of our findings.

# <span id="page-14-0"></span>B Nonce word generation

Turkish To automatically generate novel nonce words in Turkish (out-of-distribution words that do not exist) that are inflected the same as the original word roots, we leverage the deterministic morphophonological features of Turkish. In particular, vowel harmony and consonant assimilation in Turkish completely determines which surface forms of the meta level morphemes would apply. Furthermore, these features depend only on the last vowel and the consonant. Hence, for a given word root in Turkish, we keep its last vowel and the consonant and randomly modify the other vowels and consonants with other vowels and consonants based on the frequency of each letter in Turkish to make sure we obtain words that would be plausible in this language. For example, if the given word root is *"sanat"*, we keep the suffix *"at"* as is and modify the prefix *"san"* by randomly replacing each vowel in it with another vowel and consonant with another consonant. This makes sure that the words inflect the same and they are of the same length. However, if the word is too short (only two letters), and there is no prefix, we generate a random prefix of length three with vowels and consonants alternating (Turkish typically doesn't allow dense consonant clusters)

Finnish The Finnish nonce word generation is done similarly to the Turkish nonce word generation, where we alter only the word root. All consonants are replaced with other consonants and vowels with other vowels that conform to the rules of Finnish vowel harmony.

<span id="page-15-0"></span>

| #words                          | 3,775,470 |
|---------------------------------|-----------|
| #unique words                   | 348,173   |
| #unique roots                   | 9,576     |
| #unique meta affixes            | 103       |
| #unique affixes                 | 372       |
| #unique meta affix compositions | 21,930    |
| #unique affix compositions      | 37,853    |

Table 1: Statistics of BTWD dataset in Turkish. Meta affixes refer to the bound morphemes that are not surfacerealized.

<span id="page-15-1"></span>

| #samples                        | 1,049 |
|---------------------------------|-------|
| #unique roots                   | 477   |
| #unique meta affixes            | 96    |
| #unique affixes                 | 243   |
| #unique meta affix compositions | 931   |
| #unique affix compositions      | 981   |

Table 2: Statistics of our final test suite in Turkish. Meta affixes refer to the bound morphemes that are not surface-realized.

<span id="page-15-4"></span>

| Task          | Test Distribution | κ    |
|---------------|-------------------|------|
| Productivity  | ID                | 0.94 |
| Productivity  | OOD               | 0.91 |
| Systematicity | ID                | 0.94 |
| Systematicity | OOD               | 0.99 |

Table 3: Human inter-annotator agreement on Turkish test suite measured by Cohen's κ score. We note that since the productivity task is an open-ended generative task, the chance agreement would be close to 0, hence κ score is equal to the raw agreement.

<span id="page-15-5"></span>

| Task          | Test Distribution | κ    |
|---------------|-------------------|------|
| Productivity  | ID                | 0.77 |
| Productivity  | OOD               | 0.78 |
| Systematicity | ID                | 0.75 |
| Systematicity | OOD               | 0.84 |

Table 4: Human inter-annotator agreement on Finnish test suite measured by Cohen's κ score. We note that since the productivity task is an open-ended generative task, the chance agreement would be close to 0, hence κ score is equal to the raw agreement.

## <span id="page-15-3"></span>C Model Evaluation

We evaluate the following state-of-the-art multilingual instruction-finetuned LLMs:

- Aya-23 [\(Aryabumi et al.,](#page-9-17) [2024\)](#page-9-17) a powerful open-weights multilingual LLM serving 23 languages including Turkish. We evaluate both 8B and 35B sizes of this model series, but only on Turkish dataset as Aya-23 does not officially support Finnish yet.
- Qwen-2.5 [\(Team,](#page-11-9) [2024\)](#page-11-9) recent open-weights multilingual LLM that has shown impressive results across various benchmarks and supports over 29 languages. We evaluate both 7B and 32B sizes of this model series in both languages.
- Gemini-1.5 [\(Gemini,](#page-10-0) [2024\)](#page-10-0) a closed-source multilingual LLM that supports over 40 languages including Turkish and Finnish. We evaluate the gemini-1.5-flash version in both languages.
- GPT-4 [\(OpenAI,](#page-11-10) [2024\)](#page-11-10) a closed-source multilingual LLM that supports many languages including Finnish and Turkish. We evaluate the 2024-02-15-preview version in both languages.

Models are evaluated using in-context few-shot learning where number of shots take values in {1,3,5}. We make sure each shot has the same number of morphemes as its corresponding task example. By default, all our prompt templates are in English since LLMs are quite proficient in following instructions in this language [\(Wendler et al.,](#page-11-18) [2024\)](#page-11-18), however, we also experiment with instruction templates in Turkish and Finnish which generally show worse performance (Appendix [A.1\)](#page-12-7). Similarly, while by default we use the standard prompting for all experiments, we also experiment with chain-of-thought prompting [\(Wei et al.,](#page-11-17) [2023\)](#page-11-17), but find very little difference in performance (Appendix [A.2\)](#page-12-8). Prompts for all tasks and languages can be found in Appendix [F.](#page-16-1)

## <span id="page-15-2"></span>D Data

Turkish Since the morphological analyzer we use to process the Turkish dataset [\(Ozturel et al.,](#page-11-6) [2019\)](#page-11-6) is based on a finite state machine relying on purely syntactic rules, it produces several alternative decompositions for some words (e.g. analyzer

produces both decompositions "an+la+dıg+ımız" ˘ and "anla+dıg+ımız" for the word "anladı ˘ gımız" ). ˘ Hence, we further apply some language-specific heuristics to automatically filter out invalid decompositions. This preprocessing still leaves some words with multiple decompositions that can only be validated using semantics, hence, as a last step, we (authors) manually verify and determine the final segmentation of a word.

# <span id="page-16-0"></span>E Heuristic Negative Sample Selection For Turkish

Turkish phonology does not allow two vowels to occur together and typically employs "buffer" letters such as *"y", "s"* in between these vowels, however, blindly permuting the order of Turkish morphemes inevitably results in negative samples where two vowels may occur next to each other. We hypothesized that models might easily identify these options by exploiting the "no-two-vowel" shortcut and without considering the semantic order of morphemes. To check this hypothesis, we counted the number of GPT-4 mistakes corresponding to options that both have and don't have two vowels occurring together and found that while the model makes a mistake in around 8% (in-distribution) and 16% (out-of-distribution) of all the negative options that do not have two vowels occurring together, these ratios are only 1% and 4% when we look at the negative options that have two adjacent vowels. Motivated by this discrepancy, we designed our third heuristic-based selection strategy for Turkish such that after ranking the options by their distance to the positive option, we select the top four negative options that do not have two adjacent vowels in their morpheme composition wherever possible.

# <span id="page-16-1"></span>F Prompts

This section lists the instruction prompts for all tasks and language templates. We present examples in one-shot setting, templates for different shots are the same with more examples. For the English language template, we provide examples in Turkish, the templates are the same for Finnish with examples in Finnish.

# F.1 Templates in English

## Productivity task prompt [ID root]

You are given a word root and a list of affixes (separated by comma) in Turkish and your task is to generate a grammatically correct word from this root using all the given affixes. You are allowed to use only the given affixes and each affix only once. Answer with only the generated word. Example 1:

Word root: bula¸s Affixes: ma, sa, tır, ydı, k Answer: bula¸stırmasaydık

Example 2: Word root: bekle Affixes: me, di, z, n, e Answer:

## Productivity task prompt [OOD root]

You are given a novel word root with its definition and a list of affixes (separated by comma) in Turkish and your task is to generate a grammatically correct word from this root using all the given affixes. You are allowed to use only the given affixes and each affix only once. Answer with only the generated word. Example 1: Word root: lıdı¸s Definition: lıdı¸s means karı¸s in Turkish. Affixes: sa, ydı, k, ma Answer: lıdı¸smasaydık

Example 2: Word root: ihek Definition: ihek means emek in Turkish. Affixes: in, imiz, ler, çi Answer:

<span id="page-17-0"></span>

| ID root (OOD root) | Affixes                             | ID Derivations          |
|--------------------|-------------------------------------|-------------------------|
|                    |                                     | sohbetler ✓             |
| sohbet (¸sak¸set)  | -ler or -yin                        | sohbetyin               |
| sıra (yova)        |                                     | sıradanmı¸s ✓           |
|                    | -dan, -mı¸s                         | sıramı¸sdan             |
|                    | -len, -dir, -ip                     | ✓<br>degerlendirip<br>˘ |
|                    |                                     | degeriplendir<br>˘      |
| deger (diser)<br>˘ |                                     | degerdirlenip<br>˘      |
|                    |                                     | degeripdirlen<br>˘      |
|                    |                                     | ˘<br>degerlenipdir      |
|                    |                                     | endi¸selendirmemek ✓    |
|                    |                                     | endi¸selendirmekme      |
| endi¸se (ödlede)   | -len, -dir, -me, -mek               | endi¸semelendirmek      |
|                    |                                     | endi¸selenmedirmek      |
|                    |                                     | endi¸semedirlenmek      |
|                    | -le¸s, -tir, -me, -si, -ne          | ki¸sile¸stirmesine ✓    |
|                    |                                     | ki¸sile¸stirnesime      |
| ki¸si (me¸si)      |                                     | ki¸sile¸stirmenesi      |
|                    |                                     | ki¸sile¸ssitirmene      |
|                    |                                     | ki¸sile¸smetirsine      |
|                    | -ler, -im, -de, -ki, -ler, -i       | hayallerimdekileri ✓    |
|                    |                                     | hayalleriimdekiler      |
| hayal (rokal)      |                                     | hayalilerimdekiler      |
|                    |                                     | hayallerimdeikiler      |
|                    |                                     | hayallerimdekiiler      |
| sınıf (datıf)      | -lan, -dır, -ıl, -ma, -lar, -ı, -nı | sınıflandırılmalarını ✓ |
|                    |                                     | sınıflandırıılmalarnı   |
|                    |                                     | sınıflardırılmalanını   |
|                    |                                     | sınıflandırılmalarnıı   |
|                    |                                     | sınıflandırılımalarnı   |

Table 5: Examples from our test suite in Turkish for each morpheme length from 1 to 7. OOD derivations can be obtained by replacing the ID root with the corresponding OOD root. Correct derivations are marked with ✓.

<span id="page-18-1"></span>![](_page_18_Figure_0.jpeg)

Figure 11: GPT-4 morphological productivity and systematicity task results for Finnish stratified by number of bound morphemes. Detailed results are in Tables 25, 26, 27.

<span id="page-18-2"></span>![](_page_18_Figure_2.jpeg)

Figure 12: Morphological productivity and systematicity task results for Finnish showing the effect of the instruction language. Detailed results are in Tables 33.

<span id="page-18-0"></span>

| #samples                   | 480 |
|----------------------------|-----|
| #unique roots              | 406 |
| #unique affixes            | 386 |
| #unique affix compositions | 365 |

Table 6: Statistics of our final test suite in Finnish.

## Systematicity task prompt [ID root]

You are given a word root, a list of affixes (separated by comma) and a word in Turkish that is derived from the given word root using the given affixes. Your task is to determine whether the derived word is grammatically correct. Answer only with Yes or No. Example 1: Word root: küçük Affixes: ümüz, lüğ, den Derived word: küçüklüğümüzden Answer: Yes

Example 2: Word root: evren Affixes: sel, e, liğ Derived word: evreneselliğ Answer:

#### Systematicity task prompt [OOD root]

You are given a novel word root with its definition, a list of affixes (separated by comma) and a word in Turkish that is derived from the given word root using the given affixes. Your task is to determine whether the derived word is grammatically correct. Answer only with Yes or No. Example 1: Word root: enesilvöte Definition: eneşilvöte means üniversite in Turkish. Affixes: niz, yse, de Derived word: eneşilvötedeyseniz Answer: Yes

Example 2: Word root: vivek Definition: yivek means yürek in Turkish. Affixes: den, ler, iniz Derived word: yiveklerdeniniz Answer:

<span id="page-19-0"></span>

| ID root (OOD root)      | Affixes                                 | ID Derivations                      |  |  |
|-------------------------|-----------------------------------------|-------------------------------------|--|--|
| yöpaikka (äydainca)     |                                         | yöpaikkanne ✓                       |  |  |
|                         | -nne or -ksi                            | yöpaikkaksi                         |  |  |
|                         |                                         | sanotaanpas ✓                       |  |  |
| sano (tato)             | -taan, -pas                             | sanopastaan                         |  |  |
|                         |                                         | petoksineen ✓                       |  |  |
|                         |                                         | petoksneien                         |  |  |
| petoks (seloks)         | -i, -ne, -en                            | petoksneeni                         |  |  |
|                         |                                         | petoksienne                         |  |  |
|                         |                                         | petoksennei                         |  |  |
|                         |                                         | kuvausolosuhteiltaan ✓              |  |  |
|                         |                                         | kuvausolosuhteltaian                |  |  |
| olosuhte (olanajke)     | -kuvaus, -i, -lta, -an                  | kuvausolosuhteltaani                |  |  |
|                         |                                         | kuvausolosuhteianlta                |  |  |
|                         |                                         | kuvausolosuhteanilta                |  |  |
|                         |                                         | lainanvälityspalveluja ✓            |  |  |
|                         |                                         | lainanvälityspalveluaj              |  |  |
| palvelu (sapsevu)       | -laina, -n, -välitys, -j, -a            | nlainavälityspalveluja              |  |  |
|                         |                                         | lainavälitysnpalveluja              |  |  |
|                         |                                         | lainavälitysnpalveluaj              |  |  |
| salaisuuks (noraekauks) |                                         | motivaationnostatussalaisuuksiani ✓ |  |  |
|                         |                                         | motivaationnostatussalaisuuksinia   |  |  |
|                         | -motivaatio, -n, -nostatus, -i, -a, -ni | motivaationnostatussalaisuuksaini   |  |  |
|                         |                                         | motivaationnostatussalaisuuksniai   |  |  |
|                         |                                         | motivaationostatusnsalaisuuksiani   |  |  |

Table 7: Examples from our test suite in Finnish for each morpheme length from 1 to 6. OOD derivations can be obtained by replacing the ID root with the corresponding OOD root. Correct derivations are marked with ✓.

<span id="page-20-0"></span>![](_page_20_Figure_0.jpeg)

Figure 13: Morphological productivity and systematicity task results for Finnish showing the effect of additional context. Detailed results are in Table 39.

<span id="page-20-1"></span>![](_page_20_Figure_2.jpeg)

Figure 14: Morphological productivity and systematicity task results for Finnish showing the effect of the morpheme order. Detailed results are in Table 49.

## Productivity task prompt [ID root] (with context)

You are given a word root, a list of affixes (separated by comma) and a sentence with a blank (\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ the blank by generating a grammatically correct word from this root using all the given affixes. You are allowed to use only the given affixes and each affix only once. Answer with only the generated word. Example 1: Word root: kal Affixes: an, lar Sentence: giden geminin yokluğuna bir türlü inandıramaz kendilerini limanda

Answer: kalanlar

Example 2: Word root: kurtar Affixes: ecek. abil Sentence: göç ettikten sonra diğer hemşerileri gibi mal, mülk peşinde olsa belki annesini parasızlıktan \_\_\_\_\_\_ belki de kızı bir fabrika köşesinde çalışmak zorunda kalmayıp daha uzun yaşayabilecekti Answer:

Systematicity task prompt [ID root] (with context) You are given a word root, a list of affixes (separated by comma), a sentence with a blank  $($  ) and a word in Turkish that is derived from the given word root using the given affixes. Your task is to determine whether the derived word is the correct option to fill in the blank. Answer only with Yes or No.

Example 1: Word root: küçük Affixes: ümüz, den, lüğ Sentence: \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ hayatımızı Derived word: küçüklüğümüzden Answer: Yes

Example 2: Word root: akıl Affixes: lan, ız, acağ Sentence: bir şeyler yaşadıktan sonra mı hep Derived word: akılacağızlan Answer:

<span id="page-21-0"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |                    | ID                 | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |                    |  |
|------------------|---------------------------------------------|--------------------|--------------------|----------------------------------------|-----------------------------------------------|--------------------|--|
| majority         | 0.0 / 0.0 / 0.0                             | 0.0 / 0.0 / 0.0    | 41.2 / 41.2 / 41.2 | 41.2 / 41.2 / 41.2                     | 0.0 / 0.0 / 0.0                               | 0.0 / 0.0 / 0.0    |  |
| random           | 24.6 / 25.0 / 25.0                          | 24.7 / 24.6 / 24.2 | 41.8 / 41.8 / 43.5 | 43.0 / 42.3 / 42.3                     | 9.1 / 9.0 / 9.4                               | 8.5 / 9.6 / 9.0    |  |
| aya-23-8b        | 12.8 / 13.7 / 13.3                          | 8.8 / 11.5 / 12.3  | 62.0 / 64.6 / 67.5 | 53.9 / 49.3 / 51.5                     | 27.9 / 31.4 / 36.0                            | 19.1 / 15.7 / 18.4 |  |
| aya-23-35b       | 17.4 / 19.8 / 21.0                          | 14.6 / 17.7 / 19.3 | 69.9 / 80.1 / 81.8 | 64.6 / 71.0 / 72.1                     | 36.8 / 52.6 / 55.8                            | 29.2 / 39.9 / 41.8 |  |
| qwen-2.5-7b      | 15.0 / 14.9 / 15.8                          | 13.2 / 12.9 / 12.9 | 71.1 / 73.6 / 74.6 | 65.7 / 66.8 / 66.0                     | 40.5 / 44.3 / 45.1                            | 33.5 / 33.9 / 33.1 |  |
| qwen-2.5-32b     | 22.6 / 23.7 / 24.1                          | 21.7 / 21.8 / 21.8 | 77.3 / 84.7 / 85.9 | 53.1 / 71.3 / 75.3                     | 56.7 / 66.3 / 66.8                            | 18.5 / 45.7 / 48.3 |  |
| gemini-1.5-flash | 28.8 / 30.5 / 30.7                          | 24.9 / 25.7 / 25.1 | 60.8 / 80.8 / 85.4 | 41.4 / 52.8 / 62.1                     | 32.2 / 63.6 / 70.7                            | 0.4 / 19.3 / 33.3  |  |
| gpt-4            | 49.0 / 52.1 / 54.2                          | 36.7 / 40.5 / 43.9 | 85.5 / 90.2 / 91.6 | 61.9 / 77.7 / 78.8                     | 71.4 / 76.8 / 76.6                            | 33.5 / 55.9 / 51.4 |  |
| human∗           | 97.1                                        | 95.0               | 98.8               | 99.1                                   | 95.7                                          | 97.9               |  |

Table 8: 1-shot / 3-shot / 5-shot results for Turkish in English template for all examined models across tasks. <sup>∗</sup>Due to the cost of evaluation, our human study is only evaluated on 70 randomly sampled instances per task and test distribution.

<span id="page-21-1"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |                    | ID                 | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |                    |  |
|------------------|---------------------------------------------|--------------------|--------------------|----------------------------------------|-----------------------------------------------|--------------------|--|
| majority         | 0.0 / 0.0 / 0.0                             | 0.0 / 0.0 / 0.0    | 40.7 / 40.7 / 40.7 | 40.7 / 40.7 / 40.7                     | 0.0 / 0.0 / 0.0                               | 0.0 / 0.0 / 0.0    |  |
| random           | 29.4 / 32.3 / 29.8                          | 32.7 / 30.2 / 30.2 | 42.4 / 43.3 / 42.4 | 42.4 / 43.7 / 42.5                     | 10.2 / 11.7 / 10.8                            | 10.8 / 10.8 / 9.6  |  |
| qwen-2.5-7b      | 13.5 / 13.5 / 16.0                          | 10.2 / 11.7 / 14.4 | 61.3 / 65.4 / 68.3 | 54.6 / 57.3 / 59.4                     | 31.2 / 35.8 / 39.2                            | 21.9 / 25.8 / 27.7 |  |
| qwen-2.5-32b     | 22.5 / 21.9 / 22.3                          | 19.2 / 19.8 / 21.3 | 52.0 / 65.9 / 69.0 | 43.6 / 54.7 / 62.2                     | 19.0 / 39.8 / 42.5                            | 5.2 / 22.1 / 33.1  |  |
| gemini-1.5-flash | 22.5 / 26.9 / 28.1                          | 20.6 / 22.9 / 24.0 | 49.4 / 71.2 / 77.7 | 40.7 / 50.3 / 56.8                     | 14.2 / 48.1 / 52.3                            | 0.0 / 15.4 / 25.0  |  |
| gpt-4            | 37.7 / 40.6 / 44.2                          | 31.5 / 35.0 / 34.4 | 70.0 / 83.1 / 85.2 | 42.2 / 65.6 / 74.8                     | 47.5 / 65.4 / 66.2                            | 2.7 / 39.8 / 50.6  |  |
| human∗           | 85.0                                        | 83.3               | 89.4               | 91.7                                   | 75.0                                          | 75.8               |  |

Table 9: 1-shot / 3-shot / 5-shot results for Finnish in English template for all examined models across tasks. <sup>∗</sup>Due to the cost of evaluation, our human study is only evaluated on 60 randomly sampled instances per task and test distribution.

# Productivity task prompt [ID root] (CoT)

You are given a word root and a list of affixes (separated by comma) in Turkish. Your task is to construct a grammatically correct word by appending the given affixes to the root. Use each affix exactly once. After forming a word, list each affix used in the construction of that word to verify adherence to the rules. Check the following: Ensure no affix is used more than once, confirm that all provided affixes are used, verify that no extra affixes outside the provided list are included. Think step by step and then provide your final answer within the tags <Answer>correctword</Answer>.

Example 1: Word root: kuru Affixes: t, mu¸s Answer: First, let's append the affixes to the root "kuru" in a grammatically correct order: ...<explaining the correct order of morphemes>... Example 2: Word root: mana Affixes: sız, dır Answer:

Productivity task prompt [OOD root] (CoT) You are provided with a novel word root with its definition, and a list of affixes (separated by comma) in Turkish. Your task is to construct a grammatically correct word by appending the given affixes to the root. Use each affix exactly once. After forming a word, list each affix used in the construction of that word to verify adherence to the rules. Check the following: Ensure no affix is used more than once, confirm that all provided affixes are used, verify that no extra affixes outside the provided list are included. Think step by step and then provide your final answer within the tags <Answer>correctword</Answer>.

Example 1: Word root: doru Definition: doru means kuru in Turkish. Affixes: t, mu¸s Answer: ...<explanation>... Example 2: Word root: çokan Definition: çokan means yalan in Turkish. Affixes: la, lar Answer:

<span id="page-22-0"></span>

| Models           | Number of morphemes (excl. root) |             |             |             |             |            |            |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|------------|------------|--|
|                  | 1                                | 2           | 3           | 4           | 5           | 6          | 7          |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0  | 0.0 / 0.0  |  |
| random           | 100.0 / 100.0                    | 48.0 / 46.7 | 20.0 / 18.0 | 3.3 / 6.7   | 0.0 / 1.3   | 0.7 / 0.0  | 0.0 / 0.0  |  |
| aya-23-8b        | 60.0 / 52.7                      | 22.7 / 8.7  | 5.3 / 0.0   | 0.7 / 0.0   | 0.7 / 0.0   | 0.0 / 0.0  | 0.0 / 0.0  |  |
| aya-23-35b       | 72.7 / 69.3                      | 35.3 / 20.7 | 7.3 / 6.7   | 4.0 / 4.0   | 2.0 / 1.3   | 0.0 / 0.0  | 0.7 / 0.0  |  |
| qwen-2.5-7b      | 63.3 / 64.0                      | 26.7 / 22.0 | 13.3 / 6.0  | 0.0 / 0.7   | 0.0 / 0.0   | 0.7 / 0.0  | 0.7 / 0.0  |  |
| qwen-2.5-32b     | 82.0 / 85.3                      | 46.3 / 42.3 | 18.7 / 15.3 | 6.0 / 6.7   | 3.3 / 1.3   | 1.3 / 0.7  | 0.7 / 0.0  |  |
| gemini-1.5-flash | 86.7 / 80.0                      | 52.7 / 44.7 | 36.0 / 30.7 | 12.0 / 10.7 | 7.3 / 7.3   | 4.7 / 0.7  | 2.0 / 0.0  |  |
| gpt-4            | 95.3 / 96.7                      | 80.7 / 65.3 | 62.7 / 43.3 | 43.8 / 31.3 | 27.3 / 17.6 | 19.3 / 0.7 | 13.8 / 2.1 |  |

Table 10: Morphological productivity 1-shot ID / OOD accuracy results for Turkish in English template for all examined models.

<span id="page-22-1"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |
| majority         | 33.3 / 33.3                      | 33.1 / 33.1 | 44.3 / 44.3 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 |  |
| random           | 44.9 / 42.4                      | 37.6 / 39.3 | 40.2 / 41.4 | 43.5 / 44.5 | 42.6 / 46.4 | 41.9 / 42.4 | 42.3 / 44.8 |  |
| aya-23-8b        | 72.9 / 54.7                      | 68.0 / 48.7 | 66.1 / 50.0 | 58.8 / 54.8 | 59.0 / 56.5 | 54.3 / 55.3 | 55.1 / 57.5 |  |
| aya-23-35b       | 70.4 / 60.2                      | 82.7 / 70.2 | 83.1 / 73.0 | 65.0 / 58.9 | 63.5 / 65.5 | 61.5 / 61.9 | 63.2 / 62.6 |  |
| qwen-2.5-7b      | 71.8 / 53.1                      | 72.9 / 64.7 | 73.7 / 64.4 | 77.7 / 74.0 | 73.0 / 72.3 | 65.5 / 66.9 | 63.3 / 64.4 |  |
| qwen-2.5-32b     | 65.6 / 34.2                      | 57.0 / 35.1 | 75.6 / 57.6 | 87.4 / 61.5 | 86.8 / 62.1 | 84.2 / 57.3 | 84.7 / 63.9 |  |
| gemini-1.5-flash | 62.4 / 33.3                      | 58.2 / 34.0 | 60.1 / 44.2 | 59.0 / 44.8 | 61.9 / 44.4 | 56.9 / 44.3 | 67.2 / 44.7 |  |
| gpt-4            | 86.7 / 36.2                      | 69.1 / 43.8 | 82.5 / 61.8 | 88.4 / 64.2 | 92.2 / 78.7 | 88.7 / 72.0 | 90.6 / 76.9 |  |

Table 11: Morphological systematicity 1-shot ID / OOD macro-F1 results for Turkish in English template for all examined models.

Answer:

## Systematicity task prompt [ID root] (CoT)

You are given a word root, a list of affixes (separated by comma) and a word in Turkish that is derived from the given word root using the given affixes. Your task is to determine whether the derived word is grammatically correct. First, analyze how the affixes interact with the word root. Then, assess the order in which the affixes are applied and verify that this order adheres to the language's rules. Think step by step and then provide your final answer within the tags <Answer>Yes/No</Answer>. Example 1: Word root: kuru Affixes: t, mu¸s Derived word: kurutmu¸s Answer: To analyze the derived word "kurutmu¸s," we need to look at the affixes and how they interact with the word root "kuru." ...<explaining the correct order of morphemes>... Example 2: Word root: etki Affixes: yici, le Derived word: etkileyici Answer:

# Systematicity task prompt [OOD root] (CoT) You are given a novel word root with its definition, a list of affixes (separated by comma) and a word in Turkish that is derived from the given word root using the given affixes. Your task is to determine whether the derived word is grammatically correct. First, analyze how the affixes interact with the word root. Then, assess the order in which the affixes are applied and verify that this order adheres to the language's rules. Think step by step and then provide your final answer within the tags <Answer>Yes/No</Answer>. Example 1: Word root: doru Definition: doru means kuru in Turkish. Affixes: t, mu¸s Derived word: dorutmu¸s Answer: ...<explain the correct order of morphemes based on the definition>... Example 2: Word root: imli Definition: imli means etki in Turkish. Affixes: yici, le Derived word: imlileyici

<span id="page-23-1"></span>

| Models           | Number of morphemes (excl. root) |             |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|
|                  | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| random           | 28.0 / 25.3                      | 18.7 / 22.0 | 2.0 / 1.3   | 4.7 / 2.0   | 2.7 / 2.7   | 4.0 / 2.7   | 4.0 / 3.4   |  |
| aya-23-8b        | 62.0 / 38.0                      | 53.3 / 26.7 | 20.0 / 8.7  | 16.7 / 12.7 | 18.0 / 15.3 | 10.7 / 13.3 | 14.8 / 18.8 |  |
| aya-23-35b       | 56.7 / 45.3                      | 74.0 / 57.3 | 47.3 / 29.3 | 19.3 / 14.0 | 16.0 / 20.7 | 20.0 / 17.3 | 24.2 / 20.1 |  |
| qwen-2.5-7b      | 60.7 / 36.0                      | 60.7 / 49.3 | 39.3 / 29.3 | 42.0 / 34.7 | 36.7 / 34.7 | 21.3 / 24.0 | 22.8 / 26.2 |  |
| qwen-2.5-32b     | 49.3 / 2.7                       | 35.6 / 2.7  | 54.0 / 20.7 | 71.3 / 28.7 | 66.7 / 28.7 | 63.3 / 19.3 | 56.4 / 26.8 |  |
| gemini-1.5-flash | 44.0 / 0.0                       | 38.7 / 1.3  | 26.7 / 0.0  | 24.7 / 0.7  | 30.7 / 0.0  | 22.7 / 0.0  | 38.3 / 0.7  |  |
| gpt-4            | 80.0 / 4.7                       | 54.0 / 16.0 | 66.7 / 30.0 | 76.0 / 34.7 | 82.7 / 58.7 | 68.7 / 41.3 | 71.8 / 49.0 |  |

Table 12: Morphological systematicity 1-shot ID / OOD coherence results for Turkish in English template for all examined models.

<span id="page-23-0"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| random           | 100.0 / 100.0                    | 46.7 / 50.7 | 20.7 / 16.0 | 5.3 / 4.7   | 2.7 / 0.7   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| aya-23-8b        | 58.0 / 64.7                      | 29.3 / 13.3 | 5.3 / 2.0   | 2.0 / 0.0   | 1.3 / 0.7   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| aya-23-35b       | 73.3 / 84.0                      | 43.3 / 29.3 | 12.0 / 6.7  | 5.3 / 4.0   | 1.3 / 0.0   | 1.3 / 0.0   | 2.0 / 0.0   |  |
| qwen-2.5-7b      | 68.7 / 61.3                      | 24.7 / 22.7 | 6.7 / 5.3   | 2.0 / 0.7   | 1.3 / 0.0   | 0.7 / 0.0   | 0.0 / 0.0   |  |
| qwen-2.5-32b     | 84.7 / 80.7                      | 45.0 / 38.9 | 21.3 / 18.7 | 6.7 / 11.3  | 4.7 / 3.3   | 0.7 / 0.0   | 2.7 / 0.0   |  |
| gemini-1.5-flash | 84.7 / 80.0                      | 57.3 / 50.0 | 37.3 / 29.3 | 16.7 / 9.3  | 10.7 / 7.3  | 4.0 / 2.7   | 2.7 / 1.3   |  |
| gpt-4            | 94.7 / 94.7                      | 81.3 / 68.7 | 64.0 / 45.2 | 49.3 / 34.2 | 30.7 / 17.6 | 25.3 / 11.6 | 19.3 / 11.7 |  |

Table 13: Morphological productivity 3-shot ID / OOD accuracy results for Turkish in English template for all examined models.

# Productivity task prompt [ID root][paraphrased]

You are provided with a word root and a set of affixes (comma-separated) in language. Your task is to create a grammatically correct word using this root and all the provided affixes. You must use only the given affixes, and each affix can be used only once. Respond with the final word only. Example 1: Word root: bula¸s

Affixes: ma, sa, tır, ydı, k Answer: bula¸stırmasaydık

Example 2: Word root: bekle Affixes: me, di, z, n, e Answer:

# Productivity task prompt [OOD root][paraphrased]

You are given a new word root along with its definition, and a set of affixes (commaseparated) in language. Assuming that the new word root is a valid language word, your task is to form a grammatically correct word using this root and all the provided affixes. You must use only the given affixes, and each one can be used just once. Provide only the generated word as your answer.

Example 1: Word root: lıdı¸s Definition: lıdı¸s means karı¸s in Turkish. Affixes: sa, ydı, k, ma Answer: lıdı¸smasaydık

Example 2: Word root: ihek Definition: ihek means emek in Turkish. Affixes: in, imiz, ler, çi Answer:

<span id="page-24-0"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |             |  |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |  |
| majority         | 33.3 / 33.3                      | 33.1 / 33.1 | 44.3 / 44.3 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 |  |  |
| random           | 40.0 / 45.3                      | 40.2 / 43.1 | 44.4 / 41.5 | 40.2 / 43.4 | 43.9 / 40.3 | 43.9 / 41.8 | 39.8 / 41.0 |  |  |
| aya-23-8b        | 75.3 / 51.8                      | 68.0 / 43.3 | 64.5 / 34.2 | 60.3 / 44.2 | 64.3 / 52.7 | 55.6 / 55.3 | 64.0 / 63.3 |  |  |
| aya-23-35b       | 74.9 / 57.3                      | 83.6 / 68.2 | 86.2 / 78.1 | 79.5 / 75.3 | 77.3 / 77.3 | 78.8 / 72.8 | 80.3 / 68.2 |  |  |
| qwen-2.5-7b      | 60.7 / 56.9                      | 75.3 / 62.9 | 76.9 / 72.2 | 78.4 / 67.9 | 74.1 / 72.3 | 74.9 / 67.3 | 74.9 / 68.4 |  |  |
| qwen-2.5-32b     | 76.4 / 53.8                      | 74.0 / 60.2 | 87.3 / 75.6 | 88.6 / 78.0 | 91.0 / 76.6 | 89.0 / 76.2 | 86.5 / 78.7 |  |  |
| gemini-1.5-flash | 86.0 / 45.3                      | 81.6 / 50.4 | 79.1 / 55.0 | 71.2 / 53.9 | 81.2 / 55.7 | 79.1 / 55.1 | 87.6 / 54.1 |  |  |
| gpt-4            | 89.6 / 59.1                      | 81.8 / 62.9 | 92.5 / 84.9 | 94.9 / 85.7 | 92.2 / 84.7 | 88.0 / 81.8 | 92.4 / 84.7 |  |  |

Table 14: Morphological systematicity 3-shot ID / OOD macro-F1 results for Turkish in English template for all examined models.

<span id="page-24-1"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| random           | 25.3 / 29.3                      | 23.3 / 24.7 | 2.7 / 2.7   | 0.7 / 2.7   | 3.3 / 2.0   | 6.0 / 1.3   | 2.0 / 4.7   |  |
| aya-23-8b        | 64.7 / 34.0                      | 52.7 / 19.3 | 22.0 / 2.0  | 22.7 / 6.7  | 24.0 / 12.0 | 13.3 / 12.7 | 20.1 / 23.5 |  |
| aya-23-35b       | 64.0 / 39.3                      | 75.3 / 54.7 | 56.7 / 43.3 | 41.3 / 34.7 | 39.3 / 41.3 | 43.3 / 36.0 | 48.3 / 30.2 |  |
| qwen-2.5-7b      | 44.7 / 41.3                      | 64.7 / 46.7 | 39.3 / 34.0 | 45.3 / 26.0 | 36.0 / 32.7 | 40.0 / 28.7 | 40.3 / 28.2 |  |
| qwen-2.5-32b     | 65.3 / 32.7                      | 61.1 / 40.9 | 71.3 / 49.3 | 65.3 / 52.0 | 72.0 / 51.3 | 66.7 / 46.0 | 62.4 / 47.7 |  |
| gemini-1.5-flash | 79.3 / 20.0                      | 72.7 / 26.0 | 58.0 / 18.7 | 45.3 / 16.0 | 62.0 / 18.7 | 56.7 / 18.0 | 71.1 / 17.4 |  |
| gpt-4            | 84.7 / 40.0                      | 72.7 / 45.3 | 84.0 / 65.3 | 84.0 / 70.0 | 74.7 / 61.3 | 63.3 / 52.7 | 74.5 / 56.4 |  |

Table 15: Morphological systematicity 3-shot ID / OOD coherence results for Turkish in English template for all examined models.

# Systematicity task prompt [ID root][paraphrased]

You are provided with a word root, a set of affixes (comma-separated), and a word in language that is derived from the given root using the provided affixes. Your task is to verify whether the derived word is grammatically correct. Respond with only Yes or No.

Example 1: Word root: küçük Affixes: ümüz, lüg, den ˘ Derived word: küçüklügümüzden ˘ Answer: Yes

Example 2: Word root: evren Affixes: sel, e, lig˘ Derived word: evrenesellig˘ Answer:

# Systematicity task prompt [OOD root][paraphrased]

You are provided with a new word root along with its definition, a set of affixes (comma-separated), and a word in language that is derived from the given root using the provided affixes. Assuming that the new word root is a valid language word, your task is to verify whether the derived word is grammatically correct. Respond with only Yes or No.

Example 1: Word root: ene¸silvöte Definition: ene¸silvöte means üniversite in Turkish. Affixes: niz, yse, de Derived word: ene¸silvötedeyseniz Answer: Yes

Example 2: Word root: yivek Definition: yivek means yürek in Turkish. Affixes: den, ler, iniz Derived word: yiveklerdeniniz Answer:

<span id="page-25-0"></span>

| Models           | Number of morphemes (excl. root) |              |              |               |              |              |             |  |  |
|------------------|----------------------------------|--------------|--------------|---------------|--------------|--------------|-------------|--|--|
|                  | 1                                | 2            | 3            | 4             | 5            | 6            | 7           |  |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0    | 0.0 / 0.0    | 0.0 / 0.0     | 0.0 / 0.0    | 0.0 / 0.0    | 0.0 / 0.0   |  |  |
| random           | 100.0 / 100.0                    | 44.0 / 48.7  | 22.7 / 15.3  | 7.3 / 4.7     | 0.7 / 0.7    | 0.0 / 0.0    | 0.0 / 0.0   |  |  |
| aya-23-8b        | 60.0 / 64.0                      | 26.7 / 19.3  | 3.3 / 2.7    | 0.7 / 0.0     | 1.3 / 0.0    | 0.7 / 0.0    | 0.7 / 0.0   |  |  |
| aya-23-35b       | 76.0 / 87.3                      | 46.0 / 34.7  | 14.7 / 10.0  | 5.3 / 3.3     | 1.3 / 0.0    | 2.0 / 0.0    | 1.3 / 0.0   |  |  |
| qwen-2.5-7b      | 70.7 / 65.3                      | 27.3 / 16.7  | 8.0 / 6.7    | 3.3 / 0.7     | 0.7 / 0.7    | 0.0 / 0.0    | 0.7 / 0.0   |  |  |
| qwen-2.5-32b     | 83.3 / 86.7                      | 48.3 / 39.6  | 20.7 / 14.7  | 12.0 / 10.0   | 2.7 / 2.0    | 0.0 / 0.0    | 2.0 / 0.0   |  |  |
| gemini-1.5-flash | 91.3 / 79.3                      | 56.7 / 51.3  | 39.3 / 29.3  | 12.0 / 8.7    | 10.0 / 6.0   | 2.7 / 1.3    | 2.7 / 0.0   |  |  |
| gpt-4            | 96.0 / 96.7                      | 85.3 / 72.0  | 66.0 / 55.5  | 43.7 / 37.3   | 40.0 / 23.9  | 28.0 / 11.6  | 20.6 / 10.1 |  |  |
| human            | 100.0 / 100.0                    | 100.0 / 95.0 | 100.0 / 95.0 | 100.0 / 100.0 | 100.0 / 95.0 | 90.0 / 100.0 | 90.0 / 80.0 |  |  |

Table 16: Morphological productivity 5-shot ID / OOD accuracy results for Turkish in English template for all examined models. 1-shot and 3-shot results can be found in Tables [10,](#page-22-0) [13](#page-23-0) respectively.

<span id="page-25-1"></span>

| Models           | Number of morphemes (excl. root) |              |               |              |               |             |              |  |
|------------------|----------------------------------|--------------|---------------|--------------|---------------|-------------|--------------|--|
|                  | 1                                | 2            | 3             | 4            | 5             | 6           | 7            |  |
| majority         | 33.3 / 33.3                      | 33.1 / 33.1  | 44.3 / 44.3   | 44.4 / 44.4  | 44.4 / 44.4   | 44.4 / 44.4 | 44.4 / 44.4  |  |
| random           | 42.9 / 46.4                      | 43.8 / 37.6  | 43.6 / 42.2   | 40.4 / 40.4  | 44.5 / 43.9   | 43.1 / 44.0 | 46.0 / 41.4  |  |
| aya-23-8b        | 74.0 / 49.6                      | 71.3 / 49.8  | 67.7 / 44.3   | 65.6 / 52.8  | 69.7 / 56.7   | 61.3 / 48.0 | 63.3 / 59.4  |  |
| aya-23-35b       | 77.3 / 63.6                      | 87.1 / 68.2  | 85.7 / 79.4   | 82.2 / 75.2  | 82.1 / 76.7   | 80.5 / 70.5 | 77.8 / 71.2  |  |
| qwen-2.5-7b      | 66.0 / 58.0                      | 76.2 / 62.7  | 76.2 / 71.1   | 78.6 / 70.4  | 74.4 / 68.6   | 76.6 / 67.1 | 74.5 / 63.8  |  |
| qwen-2.5-32b     | 80.4 / 58.4                      | 78.1 / 68.9  | 89.5 / 79.1   | 90.3 / 80.8  | 89.7 / 80.8   | 88.1 / 81.0 | 85.5 / 77.9  |  |
| gemini-1.5-flash | 86.9 / 53.3                      | 82.9 / 55.8  | 83.4 / 66.3   | 85.5 / 60.0  | 84.8 / 60.5   | 85.5 / 66.3 | 89.2 / 72.3  |  |
| gpt-4            | 92.0 / 52.7                      | 90.9 / 82.9  | 94.4 / 86.1   | 93.9 / 84.7  | 90.8 / 80.6   | 89.1 / 82.9 | 90.2 / 81.4  |  |
| human            | 100.0 / 100.0                    | 100.0 / 96.7 | 100.0 / 100.0 | 97.2 / 100.0 | 100.0 / 100.0 | 98.8 / 97.6 | 95.2 / 100.0 |  |

Table 17: Morphological systematicity 5-shot ID / OOD macro-F1 results for Turkish in English template for all examined models. 1-shot and 3-shot results can be found in Tables [11,](#page-22-1) [14](#page-24-0) respectively.

### F.2 Templates in Turkish

## Productivity task prompt [ID root]

Size Türkçe bir kök ve bir ek listesi (virgülle ayrılmı¸s) verilecek ve sizden bu kökten verilen tüm ekleri kullanarak dilbilgisel olarak dogru ˘ bir kelime üretmeniz istenecek. Sadece verilen ekleri kullanabilirsiniz ve her bir ek sadece bir kez kullanılabilir. Sadece üretilen kelimeyi çıktı olarak verin.

Örnek 1: Kök: küçük Ekler: ümüz, lüg, den ˘ Cevap: küçüklügümüzden ˘

Örnek 2: Kök: sevgi Ekler: in, li, m Cevap:

## Productivity task prompt [OOD root]

Size Türkçe yeni bir kök, onun tanımlaması ve bir ek listesi (virgülle ayrılmı¸s) verilecek ve sizden bu kökten verilen tüm ekleri kullanarak dilbilgisel olarak dogru bir kelime üretmeniz is- ˘ tenecek. Sadece verilen ekleri kullanabilirsiniz ve her bir ek sadece bir kez kullanılabilir. Sadece üretilen kelimeyi çıktı olarak verin.

Örnek 1: Kök: nıtal Tanım: nıtal Türkçe kal anlamına gelir. Ekler: lar, an Cevap: nıtalanlar

Örnek 2: Kök: rarcu Tanım: rarcu Türkçe vurgu anlamına gelir. Ekler: la, mı¸s Cevap:

<span id="page-26-0"></span>

| Models           | Number of morphemes (excl. root) |              |               |              |               |             |              |  |  |
|------------------|----------------------------------|--------------|---------------|--------------|---------------|-------------|--------------|--|--|
|                  | 1                                | 2            | 3             | 4            | 5             | 6           | 7            |  |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0    | 0.0 / 0.0     | 0.0 / 0.0    | 0.0 / 0.0     | 0.0 / 0.0   | 0.0 / 0.0    |  |  |
| random           | 24.7 / 30.0                      | 26.0 / 20.0  | 2.0 / 1.3     | 4.7 / 1.3    | 2.0 / 4.7     | 4.0 / 4.0   | 2.7 / 2.0    |  |  |
| aya-23-8b        | 62.7 / 32.0                      | 58.7 / 30.7  | 24.7 / 7.3    | 30.0 / 14.7  | 34.0 / 15.3   | 18.0 / 8.0  | 24.2 / 20.8  |  |  |
| aya-23-35b       | 68.0 / 50.7                      | 80.7 / 53.3  | 56.0 / 49.3   | 47.3 / 36.0  | 49.3 / 38.7   | 46.0 / 30.0 | 43.0 / 34.9  |  |  |
| qwen-2.5-7b      | 51.3 / 40.7                      | 66.7 / 46.0  | 34.0 / 30.7   | 43.3 / 30.7  | 37.3 / 31.3   | 39.3 / 27.3 | 43.6 / 24.8  |  |  |
| qwen-2.5-32b     | 71.3 / 40.7                      | 67.1 / 54.4  | 72.0 / 48.0   | 72.0 / 50.0  | 67.3 / 53.3   | 62.0 / 49.3 | 55.7 / 42.3  |  |  |
| gemini-1.5-flash | 80.7 / 31.3                      | 75.3 / 34.7  | 65.3 / 34.7   | 69.3 / 26.7  | 64.7 / 27.3   | 68.0 / 34.7 | 71.8 / 43.6  |  |  |
| gpt-4            | 88.0 / 31.3                      | 86.7 / 74.7  | 86.0 / 57.3   | 78.0 / 56.7  | 68.7 / 46.0   | 64.7 / 50.7 | 64.4 / 43.0  |  |  |
| human            | 100.0 / 100.0                    | 100.0 / 95.0 | 100.0 / 100.0 | 95.0 / 100.0 | 100.0 / 100.0 | 95.0 / 90.0 | 80.0 / 100.0 |  |  |

<span id="page-26-1"></span>

| Table 18: Morphological systematicity 5-shot ID / OOD coherence results for Turkish in English template for all |  |  |
|-----------------------------------------------------------------------------------------------------------------|--|--|
| examined models. 1-shot and 3-shot results can be found in Tables 12, 15 respectively.                          |  |  |

|                  | Number of morphemes (excl. root) |             |             |            |            |           |  |
|------------------|----------------------------------|-------------|-------------|------------|------------|-----------|--|
| Models           | 1                                | 2           | 3           | 4          | 5          | 6         |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0  | 0.0 / 0.0  | 0.0 / 0.0 |  |
| random           | 100.0 / 100.0                    | 43.8 / 67.5 | 18.8 / 10.0 | 7.5 / 10.0 | 5.0 / 5.0  | 1.2 / 3.8 |  |
| qwen-2.5-7b      | 55.0 / 45.0                      | 22.5 / 15.0 | 2.5 / 1.2   | 1.2 / 0.0  | 0.0 / 0.0  | 0.0 / 0.0 |  |
| qwen-2.5-32b     | 72.5 / 71.2                      | 41.2 / 32.5 | 18.8 / 8.8  | 2.5 / 2.5  | 0.0 / 0.0  | 0.0 / 0.0 |  |
| gemini-1.5-flash | 75.0 / 73.8                      | 38.8 / 36.2 | 12.5 / 8.8  | 6.2 / 1.2  | 2.5 / 3.8  | 0.0 / 0.0 |  |
| gpt-4            | 81.2 / 86.2                      | 76.2 / 58.8 | 26.2 / 21.2 | 15.0 / 6.2 | 18.8 / 8.8 | 8.8 / 7.5 |  |

Table 19: Morphological productivity 1-shot ID / OOD accuracy results for Finnish in English template for all examined models.

#### Systematicity task prompt [ID root]

Size Türkçe bir kök, bir ek listesi (virgülle ayrılmı¸s) ve bu ekleri kullanarak türetilmi¸s bir kelime verilecek. Sizden bu kelimenin dilbilgisel olarak dogru olup olmadı ˘ gını ˘ belirlemeniz istenecek. Sadece Evet veya Hayır ile cevap verin.

Örnek 1: Kök: küçük Ekler: ümüz, lüg, den ˘ Türetilmi¸s kelime: küçüklügümüzden ˘ Cevap: Evet

Örnek 2: Kök: sahip Ekler: iniz, dig, len ˘ Türetilmi¸s kelime: sahipdiginizlen ˘ Cevap:

#### Systematicity task prompt [OOD root]

Size Türkçe yeni bir kök, onun tanımlaması, bir ek listesi (virgülle ayrılmı¸s) ve bu ekleri kullanarak türetilmi¸s bir kelime verilecek. Sizden bu kelimenin dilbilgisel olarak dogru ˘ olup olmadıgını belirlemeniz istenecek. Sadece ˘ Evet veya Hayır ile cevap verin.

Örnek 1: Kök: yivük Tanım: yivük Türkçe küçük anlamına gelir. Ekler: den, lüg, ümüz ˘ Türetilmi¸s kelime: yivüklügümüzden ˘ Cevap: Evet

Örnek 2: Kök: minlek Tanım: minlek Türkçe gerçek anlamına gelir. Ekler: le¸s, di, me Türetilmi¸s kelime: minlekle¸smedi Cevap:

<span id="page-27-0"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |  |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|--|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           |  |  |
| majority         | 33.3 / 33.3                      | 33.3 / 33.3 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 |  |  |
| random           | 41.7 / 37.1                      | 42.1 / 46.7 | 42.3 / 42.7 | 40.7 / 41.6 | 42.5 / 42.2 | 45.0 / 44.4 |  |  |
| qwen-2.5-7b      | 65.8 / 57.1                      | 77.5 / 71.2 | 61.5 / 57.2 | 53.3 / 47.7 | 53.5 / 47.2 | 56.0 / 47.2 |  |  |
| qwen-2.5-32b     | 39.2 / 34.2                      | 58.8 / 41.7 | 56.6 / 49.3 | 55.4 / 46.5 | 52.2 / 45.1 | 49.7 / 45.1 |  |  |
| gemini-1.5-flash | 50.8 / 33.3                      | 45.0 / 33.3 | 54.7 / 44.4 | 49.7 / 44.4 | 46.5 / 44.4 | 49.7 / 44.4 |  |  |
| gpt-4            | 79.2 / 34.2                      | 73.3 / 36.7 | 73.9 / 47.9 | 64.4 / 45.8 | 71.2 / 44.4 | 58.2 / 44.4 |  |  |

<span id="page-27-1"></span>Table 20: Morphological systematicity 1-shot ID / OOD macro-F1 results for Finnish in English template for all examined models.

|                  | Number of morphemes (excl. root) |             |             |            |            |            |  |
|------------------|----------------------------------|-------------|-------------|------------|------------|------------|--|
| Models           | 1                                | 2           | 3           | 4          | 5          | 6          |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0  | 0.0 / 0.0  | 0.0 / 0.0  |  |
| random           | 23.8 / 21.2                      | 25.0 / 30.0 | 3.8 / 1.2   | 0.0 / 5.0  | 6.2 / 0.0  | 2.5 / 7.5  |  |
| qwen-2.5-7b      | 50.0 / 41.2                      | 67.5 / 57.5 | 26.2 / 17.5 | 12.5 / 5.0 | 15.0 / 5.0 | 16.2 / 5.0 |  |
| qwen-2.5-32b     | 11.2 / 3.8                       | 38.8 / 12.5 | 22.5 / 8.8  | 18.8 / 3.8 | 13.8 / 1.2 | 8.8 / 1.2  |  |
| gemini-1.5-flash | 28.7 / 0.0                       | 17.5 / 0.0  | 16.2 / 0.0  | 10.0 / 0.0 | 3.8 / 0.0  | 8.8 / 0.0  |  |
| gpt-4            | 68.8 / 2.5                       | 60.0 / 5.0  | 52.5 / 6.2  | 33.8 / 2.5 | 45.0 / 0.0 | 25.0 / 0.0 |  |

Table 21: Morphological systematicity 1-shot ID / OOD coherence results for Finnish in English template for all examined models.

# Productivity task prompt [ID root] (with context)

Size Türkçe bir kök, bir ek listesi (virgülle ayrılmı¸s) ve bo¸sluklu (\_\_\_) bir cümle verilecek ve sizden bo¸slugu doldurmak için bu kökten ˘ verilen tüm ekleri kullanarak dilbilgisel olarak dogru bir kelime üretmeniz istenecek. Sadece ˘ verilen ekleri kullanabilirsiniz ve her bir ek sadece bir kez kullanılabilir. Sadece üretilen kelimeyi çıktı olarak verin.

Örnek 1: Kök: küçük Ekler: den, ümüz, lüg˘ Cümle: \_\_\_ kalma bir oyuna dönü¸stürdük hayatımızı Cevap: küçüklügümüzden ˘

Örnek 2: Kök: ilkokul Ekler: da, m, ydı Cümle: Ilk kez onun bir ¸siirini okuyabilme fırsatı buldugumda, henüz daha \_\_\_ ve bu kadar ˘ farklı bir tarzla kar¸sıla¸smak beni oldukça heyecanlandırmı¸stı Cevap:

# Systematicity task prompt [ID root] (with context)

Size Türkçe bir kök, bir ek listesi (virgülle ayrılmı¸s), bo¸sluklu (\_\_\_) bir cümle ve bu ekleri kullanarak türetilmi¸s bir kelime verilecek. Sizden bo¸slugu doldurmak için bu kelimenin ˘ dilbilgisel olarak dogru olup olmadı ˘ gını ˘ belirlemeniz istenecek. Sadece Evet veya Hayır ile cevap verin.

Örnek 1: Kök: karı¸s Ekler: ma, sa, k, ydı Cümle: gerçek ¸su ki anlayamadıgımız ¸seylere ˘ mucize deyip \_\_\_, bugünlere belki de hiç ula¸samayacaktık Türetilmi¸s kelime: karı¸smasaydık Cevap: Evet Örnek 2: Kök: sanat Ekler: ı, çı, lar, ndan Cümle: tüm bu deneyimlerime ev sahipligi˘ yapan ülke ise dünyanın en ünlü ve en çok begenilen \_\_\_ biri olan van gogh'un do ˘ gup ˘ büyüdügü hollanda'dan ba¸ska bir yer de ˘ gil ˘

Türetilmi¸s kelime: sanatçılarndanı

Cevap:

<span id="page-28-0"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| random           | 100.0 / 100.0                    | 56.2 / 46.2 | 12.5 / 17.5 | 7.5 / 12.5  | 13.8 / 3.8  | 3.8 / 1.2   |  |
| qwen-2.5-7b      | 58.8 / 55.0                      | 15.0 / 11.2 | 5.0 / 2.5   | 1.2 / 0.0   | 1.2 / 1.2   | 0.0 / 0.0   |  |
| qwen-2.5-32b     | 70.0 / 67.5                      | 41.2 / 36.2 | 12.5 / 10.0 | 3.8 / 2.5   | 1.2 / 2.5   | 2.5 / 0.0   |  |
| gemini-1.5-flash | 80.0 / 76.2                      | 51.2 / 42.5 | 13.8 / 7.5  | 5.0 / 1.2   | 6.2 / 6.2   | 5.0 / 3.8   |  |
| gpt-4            | 81.2 / 90.0                      | 73.8 / 62.5 | 32.5 / 20.0 | 20.0 / 13.8 | 26.2 / 11.2 | 10.0 / 12.5 |  |

<span id="page-28-1"></span>Table 22: Morphological productivity 3-shot ID / OOD accuracy results for Finnish in English template for all examined models.

|                  | Number of morphemes (excl. root) |             |             |             |             |             |  |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|--|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           |  |  |
| majority         | 33.3 / 33.3                      | 33.3 / 33.3 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 | 44.4 / 44.4 |  |  |
| random           | 40.0 / 43.8                      | 43.8 / 37.9 | 45.9 / 48.5 | 46.1 / 42.9 | 44.7 / 45.3 | 39.3 / 44.0 |  |  |
| qwen-2.5-7b      | 62.9 / 56.7                      | 81.2 / 77.1 | 67.2 / 55.4 | 62.8 / 52.5 | 57.7 / 52.0 | 60.4 / 50.4 |  |  |
| qwen-2.5-32b     | 52.9 / 37.5                      | 70.0 / 57.5 | 71.6 / 59.4 | 66.3 / 54.7 | 65.7 / 56.1 | 68.7 / 62.8 |  |  |
| gemini-1.5-flash | 84.2 / 50.8                      | 70.4 / 52.1 | 72.1 / 55.1 | 64.9 / 48.8 | 66.8 / 46.4 | 69.0 / 48.6 |  |  |
| gpt-4            | 81.7 / 52.5                      | 87.9 / 65.8 | 84.4 / 67.7 | 83.0 / 68.9 | 78.4 / 69.7 | 83.1 / 69.2 |  |  |

Table 23: Morphological systematicity 3-shot ID / OOD macro-F1 results for Finnish in English template for all examined models.

## F.3 Templates in Finnish

### Productivity task prompt [ID root]

Sinulle annetaan sanan sananvartalo ja luettelo pilkulla erotettuja päätteitä kielellä suomi. Tehtäväsi on luoda tästä juuresta kieliopillisesti oikea sana käyttämällä kaikkia annettuja päätteitä. Voit käyttää vain annettuja päätteitä ja kutakin päätettä vain kerran. Vastaa vain luodulla sanalla.

Esimerkki 1: Sananvartalo: markiise Päätteet: j, a Vastaus: markiiseja

Esimerkki 2: Sananvartalo: kasvattamis Päätteet: si, ta Vastaus:

#### Productivity task prompt [OOD root]

Sinulle annetaan uusi sananvartalo, sen määritelmä sekä pilkulla eroteltu luettelo päätteitä kielellä suomi. Tehtäväsi on luoda juuresta kieliopillisesti oikea sana käyttämällä kaikkia annettuja päätteitä. Käyttä vain annettuja päätteitä ja kutakin päätettä vain kerran. Vastaa vain luodulla sanalla.

Esimerkki 1:

Sananvartalo: seloks Määritelmä: seloks tarkoittaa petoks kielellä suomi. Päätteet: ne, en, i Vastaus: seloksineen

Esimerkki 2: Sananvartalo: osivma Määritelmä: osivma tarkoittaa ohitta kielellä suomi. Päätteet: han, ko, a Vastaus:

<span id="page-29-1"></span>

|                  | Number of morphemes (excl. root) |             |             |             |             |             |  |
|------------------|----------------------------------|-------------|-------------|-------------|-------------|-------------|--|
| Models           | 1                                | 2           | 3           | 4           | 5           | 6           |  |
| majority         | 0.0 / 0.0                        | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   | 0.0 / 0.0   |  |
| random           | 26.2 / 26.2                      | 27.5 / 18.8 | 5.0 / 8.8   | 5.0 / 2.5   | 3.8 / 6.2   | 2.5 / 2.5   |  |
| qwen-2.5-7b      | 45.0 / 41.2                      | 72.5 / 66.2 | 30.0 / 15.0 | 27.5 / 11.2 | 22.5 / 12.5 | 17.5 / 8.8  |  |
| qwen-2.5-32b     | 31.2 / 8.8                       | 56.2 / 36.2 | 45.0 / 25.0 | 35.0 / 16.2 | 31.2 / 17.5 | 40.0 / 28.7 |  |
| gemini-1.5-flash | 76.2 / 28.7                      | 56.2 / 28.7 | 43.8 / 16.2 | 36.2 / 7.5  | 37.5 / 3.8  | 38.8 / 7.5  |  |
| gpt-4            | 72.5 / 32.5                      | 82.5 / 48.8 | 63.7 / 38.8 | 61.3 / 38.8 | 53.8 / 41.2 | 58.8 / 38.8 |  |

<span id="page-29-0"></span>Table 24: Morphological systematicity 3-shot ID / OOD coherence results for Finnish in English template for all examined models.

|                                                          | Number of morphemes (excl. root)                         |                                                          |                                                        |                                                   |                                                    |                                                   |  |
|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|--------------------------------------------------------|---------------------------------------------------|----------------------------------------------------|---------------------------------------------------|--|
| Models                                                   | 1                                                        | 2                                                        | 3                                                      | 4                                                 | 5                                                  | 6                                                 |  |
| majority<br>random                                       | 0.0 / 0.0<br>100.0 / 100.0                               | 0.0 / 0.0<br>50.0 / 46.2                                 | 0.0 / 0.0<br>13.8 / 17.5                               | 0.0 / 0.0<br>7.5 / 11.2                           | 0.0 / 0.0<br>6.2 / 2.5                             | 0.0 / 0.0<br>1.2 / 3.8                            |  |
| qwen-2.5-7b<br>qwen-2.5-32b<br>gemini-1.5-flash<br>gpt-4 | 62.5 / 60.0<br>72.5 / 77.5<br>81.2 / 73.8<br>83.8 / 90.0 | 26.2 / 17.5<br>43.8 / 33.8<br>51.2 / 45.0<br>73.8 / 66.2 | 3.8 / 6.2<br>10.0 / 11.2<br>17.5 / 10.0<br>40.0 / 23.8 | 1.2 / 1.2<br>3.8 / 2.5<br>5.0 / 3.8<br>22.5 / 5.0 | 1.2 / 1.2<br>1.2 / 1.2<br>8.8 / 7.5<br>30.0 / 12.5 | 1.2 / 0.0<br>2.5 / 1.2<br>5.0 / 3.8<br>15.0 / 8.8 |  |
| human                                                    | 90.0 / 95.0                                              | 90.0 / 90.0                                              | 100.0 / 95.0                                           | 80.0 / 80.0                                       | 60.0 / 80.0                                        | 90.0 / 60.0                                       |  |

Table 25: Morphological productivity 5-shot ID / OOD accuracy results for Finnish in English template for all examined models. 1-shot and 3-shot results can be found in Tables [19,](#page-26-1) [22](#page-28-0) respectively.

#### Systematicity task prompt [ID root]

Sinulle annetaan sananvartalo, pilkulla eroteltu luettelo päätteistä sekä annettuja päätteitä käyttämällä vartalosta johdettu sana kielellä suomi. Tehtäväsi on selvittää, onko johdettu sana kieliopillisesti oikein. Vastaa vain Kyllä tai Ei.

Esimerkki 1: Sananvartalo: palauttaminen Päätteet: n, mi, elee Johdettu sana: mieleenpalauttaminen Vastaus: Kyllä

Esimerkki 2: Sananvartalo: näkyv Päätteet: imp, in, i Johdettu sana: näkyvimpiin Vastaus:

#### Systematicity task prompt [OOD root]

Sinulle annetaan uusi sananvartalo, sen määritelmä sekä pilkulla eroteltu luettelo päätteistä sekä uusi sana kielellä suomi, joka on johdettu annetusta sananvartalosta annettujen päätteiden avulla. Tehtäväsi on selvittää, onko johdettu sana kieliopillisesti oikein. Vastaa vain Kyllä tai Ei.

Esimerkki 1: Sananvartalo: sätletjimsä Määritelmä: sätletjimsä tarkoittaa järjestelmä kielellä suomi. Päätteet: laadu, hallinta, n, n Johdettu sana: laadunhallintasätletjimsän Vastaus: Kyllä

Esimerkki 2: Sananvartalo: olanajke Määritelmä: olanajke tarkoittaa olosuhte kielellä suomi. Päätteet: i, kuvaus, an, lta Johdettu sana: kuvausolanajkeanilta Vastaus:

<span id="page-30-0"></span>

|                                  | Number of morphemes (excl. root) |                            |                            |                            |                            |                            |  |
|----------------------------------|----------------------------------|----------------------------|----------------------------|----------------------------|----------------------------|----------------------------|--|
| Models                           | 1                                | 2                          | 3                          | 4                          | 5                          | 6                          |  |
| majority<br>random               | 33.3 / 33.3<br>43.8 / 42.5       | 33.3 / 33.3<br>40.4 / 42.9 | 44.4 / 44.4<br>43.7 / 39.8 | 44.4 / 44.4<br>41.6 / 47.3 | 44.4 / 44.4<br>39.4 / 42.4 | 44.4 / 44.4<br>45.7 / 40.0 |  |
| qwen-2.5-7b                      | 65.8 / 55.4                      | 86.7 / 75.4                | 65.0 / 58.1                | 66.2 / 54.2                | 62.5 / 57.7                | 63.5 / 55.9                |  |
| qwen-2.5-32b<br>gemini-1.5-flash | 57.1 / 40.0<br>84.2 / 49.6       | 72.9 / 66.7<br>80.8 / 65.4 | 71.7 / 69.8<br>79.6 / 62.0 | 72.8 / 63.6<br>75.4 / 52.8 | 70.7 / 71.1<br>74.9 / 53.5 | 68.6 / 62.3<br>71.4 / 57.7 |  |
| gpt-4                            | 84.2 / 61.3                      | 89.2 / 78.8                | 84.2 / 83.8                | 88.0 / 76.7                | 83.0 / 76.5                | 82.7 / 71.6                |  |
| human                            | 73.3 / 86.7                      | 93.3 / 100.0               | 93.2 / 97.6                | 95.5 / 90.9                | 91.2 / 90.5                | 89.7 / 84.4                |  |

<span id="page-30-1"></span>Table 26: Morphological systematicity 5-shot ID / OOD macro-F1 results for Finnish in English template for all examined models. 1-shot and 3-shot results can be found in Tables [20,](#page-27-0) [23](#page-28-1) respectively.

| Models                                                   | Number of morphemes (excl. root)                         |                                                          |                                                          |                                                          |                                                          |                                                          |  |
|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|----------------------------------------------------------|--|
|                                                          | 1                                                        | 2                                                        | 3                                                        | 4                                                        | 5                                                        | 6                                                        |  |
| majority<br>random                                       | 0.0 / 0.0<br>26.2 / 26.2                                 | 0.0 / 0.0<br>25.0 / 23.8                                 | 0.0 / 0.0<br>3.8 / 0.0                                   | 0.0 / 0.0<br>1.2 / 5.0                                   | 0.0 / 0.0<br>2.5 / 1.2                                   | 0.0 / 0.0<br>6.2 / 1.2                                   |  |
| qwen-2.5-7b<br>qwen-2.5-32b<br>gemini-1.5-flash<br>gpt-4 | 48.8 / 36.2<br>37.5 / 13.8<br>76.2 / 28.7<br>76.2 / 45.0 | 81.2 / 65.0<br>61.3 / 51.2<br>71.2 / 48.8<br>83.8 / 68.8 | 28.7 / 16.2<br>41.2 / 38.8<br>47.5 / 26.2<br>56.2 / 61.3 | 31.2 / 15.0<br>46.2 / 28.7<br>43.8 / 12.5<br>68.8 / 48.8 | 22.5 / 18.8<br>33.8 / 41.2<br>42.5 / 12.5<br>57.5 / 40.0 | 22.5 / 15.0<br>35.0 / 25.0<br>32.5 / 21.2<br>55.0 / 40.0 |  |
| human                                                    | 60.0 / 80.0                                              | 90.0 / 100.0                                             | 75.0 / 90.0                                              | 85.0 / 75.0                                              | 70.0 / 60.0                                              | 70.0 / 50.0                                              |  |

Table 27: Morphological systematicity 5-shot ID / OOD coherence results for Finnish in English template for all examined models. 1-shot and 3-shot results can be found in Tables [21,](#page-27-1) [24](#page-29-1) respectively.

# Productivity task prompt [ID root] (with context)

Allaolevassa lauseessa (kirjoitettu kielellä suomi) on tyhjä kohta (\_\_\_) joka tulee täyttää kieliopillisesti oikealla sanalla. Alla on myös sananvartalo sekä pilkulla eroteltu luettelo päätteistä. Tehtäväsi on käyttää vartaloa sekä päätteitä ja johtaa niistä kieliopillisesti oikein taivutetu sana joka sopii tyhjään kohtaan lausessaa asiayhteys/konteksti huomioonottaen. Käytä jokaista päätettä vain kerran. Vastaa vain generoidulla sanalla, älä sano mitään muuta.

Esimerkki 1: Sananvartalo: markiise Päätteet: a, j Lause: \_\_\_ saatavana yksivärisinä, raidallisina ja voit myös valita haluatko markiisisi veivivai sähkökäyttöisenä. Vastaus: markiiseja

Esimerkki 2: Sananvartalo: suhteutet Päätteet: na, tu Lause: \_\_\_ väkilukuun, suomessa on enemmän metsää kuin missään muussa euroopan maassa. Vastaus:

# Systematicity task prompt [ID root] (with context)

Allaolevassa lauseessa on tyhjä kohta (\_\_\_) joka tulee täyttää kieliopillisesti oikealla sanalla. Alla on myös sananvartalo, pilkulla eroteltu luettelo päätteistä sekä niitä käyttäen annetusta vartalosta johdettu sana kielellä suomi. Tehtäväsi on päätellä, onko johdettu sana kieliopillisesti oikein, jos sen asettaa lauseen tyhjään kohtaan eli onko sana kieliopillisesti oikein taivutetu asiayhteys/konteksti huomioonottaen. Vastaa joko Kyllä tai Ei.

Esimerkki 1: Sananvartalo: petoks Päätteet: ne, en, i Lause: hän paljasti koko korruptoituneen järjestelmän \_\_\_. Johdettu sana: petoksineen Vastaus: Kyllä Esimerkki 2: Sananvartalo: kannatta Päätteet: isi, han, ko Lause: \_\_\_ minun opiskella suomea? Johdettu sana: kannattakoisihan Vastaus:

<span id="page-31-2"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | ID          | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |             |
|------------------|---------------------------------------------|-------------|-------------|----------------------------------------|-----------------------------------------------|-------------|
|                  |                                             |             |             |                                        |                                               |             |
| aya-23-8b        | 12.8 / 8.4                                  | 8.8 / 5.3   | 62.0 / 62.4 | 53.9 / 44.3                            | 27.9 / 31.9                                   | 19.1 / 4.5  |
| aya-23-35b       | 17.4 / 14.6                                 | 14.6 / 11.7 | 69.9 / 79.6 | 64.6 / 48.9                            | 36.8 / 59.2                                   | 29.2 / 12.2 |
| qwen-2.5-7b      | 15.0 / 9.3                                  | 13.2 / 10.0 | 71.1 / 69.9 | 65.7 / 59.1                            | 40.5 / 38.1                                   | 33.5 / 23.6 |
| qwen-2.5-32b     | 22.6 / 22.9                                 | 21.7 / 20.4 | 77.3 / 78.5 | 53.1 / 44.5                            | 56.7 / 60.0                                   | 18.5 / 5.7  |
| gemini-1.5-flash | 28.8 / 21.8                                 | 24.9 / 19.3 | 60.8 / 45.1 | 41.4 / 41.2                            | 32.2 / 5.9                                    | 0.4 / 0.0   |
| gpt-4            | 49.0 / 48.5                                 | 36.7 / 38.1 | 85.5 / 76.3 | 61.9 / 50.4                            | 71.4 / 58.6                                   | 33.5 / 15.7 |

Table 28: 1-shot English / Turkish template results for Turkish for all examined models across tasks.

<span id="page-31-3"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | ID          | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |             |
|------------------|---------------------------------------------|-------------|-------------|----------------------------------------|-----------------------------------------------|-------------|
| aya-23-8b        | 13.7 / 7.0                                  | 11.5 / 9.6  | 64.6 / 69.0 | 49.3 / 46.4                            | 31.4 / 38.7                                   | 15.7 / 8.0  |
| aya-23-35b       | 19.8 / 17.1                                 | 17.7 / 16.9 | 80.1 / 81.6 | 71.0 / 57.1                            | 52.6 / 59.6                                   | 39.9 / 24.7 |
| qwen-2.5-7b      | 14.9 / 11.2                                 | 12.9 / 11.4 | 73.6 / 73.7 | 66.8 / 61.4                            | 44.3 / 44.8                                   | 33.9 / 28.2 |
| qwen-2.5-32b     | 23.7 / 20.7                                 | 21.8 / 19.9 | 84.7 / 86.1 | 71.3 / 65.2                            | 66.3 / 70.5                                   | 45.7 / 36.8 |
| gemini-1.5-flash | 30.5 / 23.0                                 | 25.7 / 20.7 | 80.8 / 56.9 | 52.8 / 41.2                            | 63.6 / 25.3                                   | 19.3 / 0.0  |
| gpt-4            | 52.1 / 51.5                                 | 40.5 / 40.6 | 90.2 / 88.6 | 77.7 / 66.3                            | 76.8 / 76.3                                   | 55.9 / 39.9 |

Table 29: 3-shot English / Turkish template results for Turkish for all examined models across tasks.

<span id="page-31-0"></span>

| Models           | ID          | Morph. Productivity (accuracy)<br>OOD | ID          | Morph. Systematicity (macro-F1)<br>OOD | ID          | Morph. Systematicity (coherence)<br>OOD |
|------------------|-------------|---------------------------------------|-------------|----------------------------------------|-------------|-----------------------------------------|
| aya-23-8b        | 13.3 / 8.6  | 12.3 / 8.1                            | 67.5 / 62.0 | 51.5 / 47.9                            | 36.0 / 30.6 | 18.4 / 15.8                             |
| aya-23-35b       | 21.0 / 17.1 | 19.3 / 18.0                           | 81.8 / 81.7 | 72.1 / 64.3                            | 55.8 / 57.7 | 41.8 / 30.4                             |
| qwen-2.5-7b      | 15.8 / 13.0 | 12.9 / 12.3                           | 74.6 / 73.5 | 66.0 / 65.2                            | 45.1 / 42.4 | 33.1 / 32.3                             |
| qwen-2.5-32b     | 24.1 / 23.3 | 21.8 / 21.9                           | 85.9 / 86.9 | 75.3 / 70.7                            | 66.8 / 70.5 | 48.3 / 44.2                             |
| gemini-1.5-flash | 30.7 / 25.8 | 25.1 / 22.1                           | 85.4 / 61.6 | 62.1 / 41.6                            | 70.7 / 32.9 | 33.3 / 0.7                              |
| gpt-4            | 54.2 / 53.1 | 43.9 / 40.7                           | 91.6 / 92.7 | 78.8 / 76.3                            | 76.6 / 82.1 | 51.4 / 51.9                             |

Table 30: 5-shot English / Turkish template results for Turkish for all examined models across tasks. Results for 1-shot and 3-shot can be found in Tables [28](#page-31-2) and [29.](#page-31-3)

<span id="page-31-4"></span>

| Models           | Morph. Productivity (accuracy) |             | Morph. Systematicity (macro-F1) |             | Morph. Systematicity (coherence) |            |
|------------------|--------------------------------|-------------|---------------------------------|-------------|----------------------------------|------------|
|                  | ID                             | OOD         | ID                              | OOD         | ID                               | OOD        |
| qwen-2.5-7b      | 13.5 / 7.9                     | 10.2 / 10.8 | 61.3 / 56.8                     | 54.6 / 41.2 | 31.2 / 23.8                      | 21.9 / 2.1 |
| qwen-2.5-32b     | 22.5 / 16.9                    | 19.2 / 11.9 | 52.0 / 54.5                     | 43.6 / 44.4 | 19.0 / 21.9                      | 5.2 / 5.8  |
| gemini-1.5-flash | 22.5 / 25.2                    | 20.6 / 21.2 | 49.4 / 50.2                     | 40.7 / 40.9 | 14.2 / 15.6                      | 0.0 / 0.2  |
| gpt-4            | 37.7 / 37.3                    | 31.5 / 27.7 | 70.0 / 59.6                     | 42.2 / 41.6 | 47.5 / 30.4                      | 2.7 / 1.2  |

Table 31: 1-shot English / Finnish template results for Finnish for all examined models across tasks.

<span id="page-31-5"></span>

| Models           | ID          | Morph. Productivity (accuracy)<br>OOD | ID          | Morph. Systematicity (macro-F1)<br>OOD | ID          | Morph. Systematicity (coherence)<br>OOD |
|------------------|-------------|---------------------------------------|-------------|----------------------------------------|-------------|-----------------------------------------|
| qwen-2.5-7b      | 13.5 / 10.4 | 11.7 / 10.2                           | 65.4 / 65.0 | 57.3 / 55.7                            | 35.8 / 32.5 | 25.8 / 22.5                             |
| qwen-2.5-32b     | 21.9 / 21.0 | 19.8 / 17.3                           | 65.9 / 60.9 | 54.7 / 56.4                            | 39.8 / 31.7 | 22.1 / 24.8                             |
| gemini-1.5-flash | 26.9 / 24.6 | 22.9 / 19.2                           | 71.2 / 74.7 | 50.3 / 48.0                            | 48.1 / 51.7 | 15.4 / 11.9                             |
| gpt-4            | 40.6 / 40.8 | 35.0 / 32.7                           | 83.1 / 72.0 | 65.6 / 45.9                            | 65.4 / 51.0 | 39.8 / 8.5                              |

Table 32: 3-shot English / Finnish template results for Finnish for all examined models across tasks.

<span id="page-31-1"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | Morph. Systematicity (macro-F1)<br>ID<br>OOD |             | Morph. Systematicity (coherence)<br>ID<br>OOD |             |
|------------------|---------------------------------------------|-------------|----------------------------------------------|-------------|-----------------------------------------------|-------------|
|                  |                                             |             |                                              |             |                                               |             |
| qwen-2.5-7b      | 16.0 / 13.1                                 | 14.4 / 13.3 | 68.3 / 66.6                                  | 59.4 / 60.1 | 39.2 / 35.2                                   | 27.7 / 28.1 |
| qwen-2.5-32b     | 22.3 / 20.6                                 | 21.3 / 20.6 | 69.0 / 66.5                                  | 62.2 / 59.1 | 42.5 / 39.4                                   | 33.1 / 29.0 |
| gemini-1.5-flash | 28.1 / 28.1                                 | 24.0 / 21.7 | 77.7 / 76.2                                  | 56.8 / 59.2 | 52.3 / 51.9                                   | 25.0 / 28.1 |
| gpt-4            | 44.2 / 42.9                                 | 34.4 / 34.4 | 85.2 / 81.1                                  | 74.8 / 57.2 | 66.2 / 65.0                                   | 50.6 / 26.2 |

Table 33: 5-shot English / Finnish template results for Finnish for all examined models across tasks. 1-shot and 3-shot results can be found in Tables [31](#page-31-4) and [32.](#page-31-5)

<span id="page-32-2"></span>

| Models           | Morph. Productivity (accuracy) |             | Morph. Systematicity (macro-F1) |             | Morph. Systematicity (coherence) |             |
|------------------|--------------------------------|-------------|---------------------------------|-------------|----------------------------------|-------------|
|                  | OOD                            |             | ID                              |             | ID                               |             |
|                  | ID                             |             | OOD                             |             | OOD                              |             |
| aya-23-8b        | 12.8 / 13.1                    | 8.8 / 6.3   | 62.0 / 49.8                     | 53.9 / 40.3 | 27.9 / 16.8                      | 19.1 / 7.5  |
| aya-23-35b       | 17.4 / 21.0                    | 14.6 / 13.1 | 69.9 / 66.3                     | 64.6 / 55.8 | 36.8 / 37.3                      | 29.2 / 22.0 |
| qwen-2.5-7b      | 15.0 / 13.0                    | 13.2 / 9.8  | 71.1 / 61.9                     | 65.7 / 53.6 | 40.5 / 29.8                      | 33.5 / 19.7 |
| qwen-2.5-32b     | 22.6 / 23.7                    | 21.7 / 19.3 | 77.3 / 44.0                     | 53.1 / 41.4 | 56.7 / 4.7                       | 18.5 / 0.3  |
| gemini-1.5-flash | 28.8 / 36.1                    | 24.9 / 24.1 | 60.8 / 57.4                     | 41.4 / 43.5 | 32.2 / 26.2                      | 0.4 / 3.8   |
| gpt-4            | 49.0 / 59.6                    | 36.7 / 39.9 | 85.5 / 71.0                     | 61.9 / 54.5 | 71.4 / 49.6                      | 33.5 / 21.4 |

Table 34: 1-shot No context / With context results for Turkish in English template for all examined models across tasks.

<span id="page-32-3"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | Morph. Systematicity (macro-F1)<br>ID<br>OOD |             | Morph. Systematicity (coherence)<br>ID<br>OOD |             |
|------------------|---------------------------------------------|-------------|----------------------------------------------|-------------|-----------------------------------------------|-------------|
| aya-23-8b        | 13.7 / 13.6                                 | 11.5 / 9.6  | 64.6 / 50.3                                  | 49.3 / 42.5 | 31.4 / 16.8                                   | 15.7 / 9.6  |
| aya-23-35b       | 19.8 / 24.3                                 | 17.7 / 17.8 | 80.1 / 66.3                                  | 71.0 / 51.0 | 52.6 / 34.9                                   | 39.9 / 16.1 |
| qwen-2.5-7b      | 14.9 / 13.5                                 | 12.9 / 9.8  | 73.6 / 63.4                                  | 66.8 / 59.3 | 44.3 / 30.3                                   | 33.9 / 25.2 |
| qwen-2.5-32b     | 23.7 / 24.2                                 | 21.8 / 19.3 | 84.7 / 61.0                                  | 71.3 / 47.3 | 66.3 / 33.2                                   | 45.7 / 10.2 |
| gemini-1.5-flash | 30.5 / 38.4                                 | 25.7 / 26.5 | 80.8 / 75.6                                  | 52.8 / 60.1 | 63.6 / 49.7                                   | 19.3 / 27.2 |
| gpt-4            | 52.1 / 59.8                                 | 40.5 / 45.6 | 90.2 / 85.2                                  | 77.7 / 67.1 | 76.8 / 71.9                                   | 55.9 / 41.5 |

Table 35: 3-shot No context / With context results for Turkish in English template for all examined models across tasks.

<span id="page-32-0"></span>

| Models           | Morph. Productivity (accuracy) |             |             | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |             |  |
|------------------|--------------------------------|-------------|-------------|---------------------------------|----------------------------------|-------------|--|
|                  | ID                             | OOD         | ID          | OOD                             | ID                               | OOD         |  |
| aya-23-8b        | 13.3 / 14.8                    | 12.3 / 9.9  | 67.5 / 51.4 | 51.5 / 42.9                     | 36.0 / 19.3                      | 18.4 / 10.6 |  |
| aya-23-35b       | 21.0 / 26.5                    | 19.3 / 18.7 | 81.8 / 66.2 | 72.1 / 47.6                     | 55.8 / 35.4                      | 41.8 / 14.3 |  |
| qwen-2.5-7b      | 15.8 / 15.0                    | 12.9 / 11.4 | 74.6 / 63.9 | 66.0 / 58.8                     | 45.1 / 30.3                      | 33.1 / 23.1 |  |
| qwen-2.5-32b     | 24.1 / 26.2                    | 21.8 / 21.4 | 85.9 / 68.4 | 75.3 / 52.0                     | 66.8 / 44.8                      | 48.3 / 18.1 |  |
| gemini-1.5-flash | 30.7 / 41.7                    | 25.1 / 28.7 | 85.4 / 77.6 | 62.1 / 65.3                     | 70.7 / 51.6                      | 33.3 / 32.2 |  |
| gpt-4            | 54.2 / 60.0                    | 43.9 / 46.3 | 91.6 / 88.4 | 78.8 / 72.1                     | 76.6 / 77.2                      | 51.4 / 48.4 |  |

Table 36: 5-shot No context / With context results for Turkish in English template for all examined models across tasks. 1-shot and 3-shot results can be found in Tables [34](#page-32-2) and [35.](#page-32-3)

<span id="page-32-4"></span>

| Models           | Morph. Productivity (accuracy) |             |             | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |             |  |
|------------------|--------------------------------|-------------|-------------|---------------------------------|----------------------------------|-------------|--|
|                  | ID                             | OOD         | ID          | OOD                             | ID                               | OOD         |  |
| qwen-2.5-7b      | 13.5 / 10.6                    | 10.2 / 9.6  | 61.3 / 61.5 | 54.6 / 53.2                     | 31.2 / 30.4                      | 21.9 / 19.0 |  |
| qwen-2.5-32b     | 22.5 / 22.3                    | 19.2 / 17.3 | 52.0 / 43.6 | 43.6 / 40.7                     | 19.0 / 4.8                       | 5.2 / 0.0   |  |
| gemini-1.5-flash | 22.5 / 26.7                    | 20.6 / 21.9 | 49.4 / 54.7 | 40.7 / 41.1                     | 14.2 / 22.1                      | 0.0 / 0.6   |  |
| gpt-4            | 37.7 / 46.7                    | 31.5 / 31.7 | 70.0 / 74.6 | 42.2 / 49.6                     | 47.5 / 53.1                      | 2.7 / 14.4  |  |

Table 37: 1-shot No context / With context results for Finnish in English template for all examined models across tasks.

<span id="page-32-5"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | ID          | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |             |  |
|------------------|---------------------------------------------|-------------|-------------|----------------------------------------|-----------------------------------------------|-------------|--|
| qwen-2.5-7b      | 13.5 / 11.0                                 | 11.7 / 10.8 | 65.4 / 63.5 | 57.3 / 55.3                            | 35.8 / 34.0                                   | 25.8 / 21.5 |  |
| qwen-2.5-32b     | 21.9 / 22.5                                 | 19.8 / 16.0 | 65.9 / 62.0 | 54.7 / 47.3                            | 39.8 / 33.8                                   | 22.1 / 10.6 |  |
| gemini-1.5-flash | 26.9 / 32.3                                 | 22.9 / 23.3 | 71.2 / 72.3 | 50.3 / 57.3                            | 48.1 / 43.3                                   | 15.4 / 23.3 |  |
| gpt-4            | 40.6 / 52.3                                 | 35.0 / 33.5 | 83.1 / 83.8 | 65.6 / 65.2                            | 65.4 / 67.9                                   | 39.8 / 39.2 |  |

Table 38: 3-shot No context / With context results for Finnish in English template for all examined models across tasks.

<span id="page-32-1"></span>

| Models                           | Morph. Productivity (accuracy)<br>OOD<br>ID |                            | ID                         | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |                            |  |
|----------------------------------|---------------------------------------------|----------------------------|----------------------------|----------------------------------------|-----------------------------------------------|----------------------------|--|
| qwen-2.5-7b                      | 16.0 / 13.5                                 | 14.4 / 12.7                | 68.3 / 63.0                | 59.4 / 54.5                            | 39.2 / 32.3                                   | 27.7 / 21.9                |  |
| qwen-2.5-32b<br>gemini-1.5-flash | 22.3 / 23.8<br>28.1 / 32.7                  | 21.3 / 20.0<br>24.0 / 24.4 | 69.0 / 65.5<br>77.7 / 72.4 | 62.2 / 54.5<br>56.8 / 53.8             | 42.5 / 37.9<br>52.3 / 42.7                    | 33.1 / 20.6<br>25.0 / 19.8 |  |
| gpt-4                            | 44.2 / 53.1                                 | 34.4 / 32.3                | 85.2 / 85.8                | 74.8 / 68.5                            | 66.2 / 68.1                                   | 50.6 / 41.5                |  |

Table 39: 5-shot No context / With context results for Finnish in English template for all examined models across tasks. 1-shot and 3-shot results can be found in Tables [37](#page-32-4) and [38.](#page-32-5)

<span id="page-33-3"></span>

| Models | Number of morphemes (excl. root) |             |             |             |             |             |             |  |  |  |
|--------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|--|--|
|        | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |  |  |
| gpt-4  | 95.3 / 84.0                      | 80.7 / 67.8 | 62.7 / 52.7 | 43.8 / 42.1 | 27.3 / 32.0 | 19.3 / 26.5 | 13.8 / 13.9 |  |  |  |

<span id="page-33-4"></span>Table 40: GPT-4 morphological productivity 1-shot morphologically aligned / tokenizer aligned accuracy results on the ID test set for Turkish in English template.

| Models | Number of morphemes (excl. root) |             |             |             |             |             |             |  |  |  |
|--------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|--|--|
|        | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |  |  |
| gpt-4  | 94.7 / 84.7                      | 81.3 / 72.5 | 64.0 / 58.0 | 49.3 / 48.2 | 30.7 / 39.5 | 25.3 / 36.8 | 19.3 / 23.8 |  |  |  |

<span id="page-33-0"></span>Table 41: GPT-4 morphological productivity 3-shot morphologically aligned / tokenizer aligned accuracy results on the ID test set for Turkish in English template.

| Models | Number of morphemes (excl. root) |             |             |             |             |             |             |  |  |
|--------|----------------------------------|-------------|-------------|-------------|-------------|-------------|-------------|--|--|
|        | 1                                | 2           | 3           | 4           | 5           | 6           | 7           |  |  |
| gpt-4  | 96.0 / 88.0                      | 85.3 / 69.8 | 66.0 / 64.0 | 43.7 / 44.8 | 40.0 / 42.2 | 28.0 / 32.4 | 20.6 / 25.7 |  |  |

Table 42: GPT-4 morphological productivity 5-shot morphologically aligned / tokenizer aligned accuracy results on the ID test set for Turkish in English template. 1-shot and 3-shot results can be found in Tables [40](#page-33-3) and [41.](#page-33-4)

<span id="page-33-2"></span>

| Models | Morph. Productivity (accuracy) |                    |                    | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |                    |
|--------|--------------------------------|--------------------|--------------------|---------------------------------|----------------------------------|--------------------|
|        | ID                             | OOD                | ID                 | OOD                             | ID                               | OOD                |
| gpt-4  | 54.2 / 36.4 / 46.8             | 43.9 / 31.2 / 45.8 | 91.6 / 85.1 / 88.8 | 78.8 / 70.3 / 83.0              | 76.6 / 63.8 / 72.5               | 51.4 / 38.1 / 61.1 |

Table 43: GPT-4 5-shot / 0-shot-cot / 5-shot-cot results for Turkish in English template across tasks.

<span id="page-33-5"></span>

| Models                                                                     | ID                                                                      | Morph. Productivity (accuracy)<br>OOD                                 | ID                                                                      | Morph. Systematicity (macro-F1)<br>OOD                                  | ID                                                                      | Morph. Systematicity (coherence)<br>OOD                               |
|----------------------------------------------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-----------------------------------------------------------------------|
| aya-23-8b<br>aya-23-35b<br>qwen-2.5-7b<br>qwen-2.5-32b<br>gemini-1.5-flash | 12.8 / 14.2<br>17.4 / 22.3<br>15.0 / 16.7<br>22.6 / 30.0<br>28.8 / 37.2 | 8.8 / 9.4<br>14.6 / 17.9<br>13.2 / 14.9<br>21.7 / 29.2<br>24.9 / 32.1 | 62.0 / 62.0<br>69.9 / 69.4<br>71.1 / 73.1<br>77.3 / 80.4<br>60.8 / 65.4 | 53.9 / 53.5<br>64.6 / 64.3<br>65.7 / 67.8<br>53.1 / 58.1<br>41.4 / 41.5 | 27.9 / 28.0<br>36.8 / 36.2<br>40.5 / 42.7<br>56.7 / 61.0<br>32.2 / 39.6 | 19.1 / 19.4<br>29.2 / 28.2<br>33.5 / 36.5<br>18.5 / 25.9<br>0.4 / 0.7 |
| gpt-4                                                                      | 49.0 / 63.0                                                             | 36.7 / 54.5                                                           | 85.5 / 88.6                                                             | 61.9 / 68.3                                                             | 71.4 / 77.5                                                             | 33.5 / 43.7                                                           |

Table 44: 1-shot Shuffled / Correct morpheme order results for Turkish in English template for all examined models across tasks.

<span id="page-33-6"></span>

| Models           | Morph. Productivity (accuracy) |             |             | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |             |
|------------------|--------------------------------|-------------|-------------|---------------------------------|----------------------------------|-------------|
|                  | ID                             | OOD         | ID          | OOD                             | ID                               | OOD         |
| aya-23-8b        | 13.7 / 14.9                    | 11.5 / 12.5 | 64.6 / 63.8 | 49.3 / 49.1                     | 31.4 / 30.7                      | 15.7 / 16.4 |
| aya-23-35b       | 19.8 / 25.7                    | 17.7 / 23.7 | 80.1 / 80.2 | 71.0 / 73.0                     | 52.6 / 52.2                      | 39.9 / 41.9 |
| qwen-2.5-7b      | 14.9 / 17.8                    | 12.9 / 15.5 | 73.6 / 76.1 | 66.8 / 69.4                     | 44.3 / 47.9                      | 33.9 / 38.0 |
| qwen-2.5-32b     | 23.7 / 30.7                    | 21.8 / 32.1 | 84.7 / 86.9 | 71.3 / 75.7                     | 66.3 / 70.3                      | 45.7 / 53.0 |
| gemini-1.5-flash | 30.5 / 39.6                    | 25.7 / 33.4 | 80.8 / 85.4 | 52.8 / 58.0                     | 63.6 / 71.6                      | 19.3 / 27.4 |
| gpt-4            | 52.1 / 70.3                    | 40.5 / 63.5 | 90.2 / 92.9 | 77.7 / 81.0                     | 76.8 / 82.0                      | 55.9 / 59.6 |

Table 45: 3-shot Shuffled / Correct morpheme order results for Turkish in English template for all examined models across tasks.

<span id="page-33-1"></span>

| Models           | Morph. Productivity (accuracy) |             | Morph. Systematicity (macro-F1) |             | Morph. Systematicity (coherence) |             |
|------------------|--------------------------------|-------------|---------------------------------|-------------|----------------------------------|-------------|
|                  | ID                             | OOD         | ID                              | OOD         | ID                               | OOD         |
| aya-23-8b        | 13.3 / 15.0                    | 12.3 / 13.0 | 67.5 / 66.4                     | 51.5 / 51.8 | 36.0 / 34.7                      | 18.4 / 18.1 |
| aya-23-35b       | 21.0 / 28.5                    | 19.3 / 25.8 | 81.8 / 81.3                     | 72.1 / 72.3 | 55.8 / 55.2                      | 41.8 / 42.3 |
| qwen-2.5-7b      | 15.8 / 19.2                    | 12.9 / 16.9 | 74.6 / 76.4                     | 66.0 / 68.5 | 45.1 / 47.0                      | 33.1 / 35.7 |
| qwen-2.5-32b     | 24.1 / 32.3                    | 21.8 / 36.4 | 85.9 / 87.5                     | 75.3 / 78.2 | 66.8 / 69.6                      | 48.3 / 52.2 |
| gemini-1.5-flash | 30.7 / 43.3                    | 25.1 / 35.1 | 85.4 / 88.6                     | 62.1 / 66.1 | 70.7 / 74.5                      | 33.3 / 39.5 |
| gpt-4            | 54.2 / 73.0                    | 43.9 / 66.7 | 91.6 / 93.7                     | 78.8 / 82.6 | 76.6 / 82.2                      | 51.4 / 58.3 |

Table 46: 5-shot Shuffled / Correct morpheme order results for Turkish in English template for all examined models across tasks. 1-shot and 3-shot results can be found in Tables [44](#page-33-5) and [45.](#page-33-6)

<span id="page-34-2"></span>

| Models           | Morph. Productivity (accuracy) |             | Morph. Systematicity (macro-F1) |             | Morph. Systematicity (coherence) |             |
|------------------|--------------------------------|-------------|---------------------------------|-------------|----------------------------------|-------------|
|                  | OOD                            |             | ID                              |             | ID                               |             |
|                  | ID                             |             | OOD                             |             | OOD                              |             |
| qwen-2.5-7b      | 13.5 / 15.6                    | 10.2 / 12.3 | 61.3 / 62.9                     | 54.6 / 55.2 | 31.2 / 34.2                      | 21.9 / 22.5 |
| qwen-2.5-32b     | 22.5 / 24.8                    | 19.2 / 23.1 | 52.0 / 53.1                     | 43.6 / 44.0 | 19.0 / 20.4                      | 5.2 / 5.8   |
| gemini-1.5-flash | 22.5 / 26.7                    | 20.6 / 25.6 | 49.4 / 51.2                     | 40.7 / 40.9 | 14.2 / 17.5                      | 0.0 / 0.2   |
| gpt-4            | 37.7 / 46.0                    | 31.5 / 39.6 | 70.0 / 70.7                     | 42.2 / 43.7 | 47.5 / 48.3                      | 2.7 / 5.0   |

Table 47: 1-shot Shuffled / Correct morpheme order results for Finnish in English template for all examined models across tasks.

<span id="page-34-3"></span>

| Models           | Morph. Productivity (accuracy)<br>OOD<br>ID |             | Morph. Systematicity (macro-F1)<br>ID<br>OOD |             | Morph. Systematicity (coherence)<br>ID<br>OOD |             |
|------------------|---------------------------------------------|-------------|----------------------------------------------|-------------|-----------------------------------------------|-------------|
| qwen-2.5-7b      | 13.5 / 16.5                                 | 11.7 / 15.2 | 65.4 / 67.5                                  | 57.3 / 59.6 | 35.8 / 39.8                                   | 25.8 / 29.0 |
| qwen-2.5-32b     | 21.9 / 25.2                                 | 19.8 / 25.0 | 65.9 / 66.6                                  | 54.7 / 55.4 | 39.8 / 41.5                                   | 22.1 / 23.1 |
| gemini-1.5-flash | 26.9 / 35.0                                 | 22.9 / 28.7 | 71.2 / 73.2                                  | 50.3 / 51.1 | 48.1 / 50.6                                   | 15.4 / 16.5 |
| gpt-4            | 40.6 / 56.0                                 | 35.0 / 50.4 | 83.1 / 83.2                                  | 65.6 / 67.4 | 65.4 / 67.3                                   | 39.8 / 42.7 |

Table 48: 3-shot Shuffled / Correct morpheme order results for Finnish in English template for all examined models across tasks.

<span id="page-34-1"></span>

| Models           | Morph. Productivity (accuracy) |             | Morph. Systematicity (macro-F1) |             | Morph. Systematicity (coherence) |             |
|------------------|--------------------------------|-------------|---------------------------------|-------------|----------------------------------|-------------|
|                  | ID                             | OOD         | ID                              | OOD         | ID                               | OOD         |
| qwen-2.5-7b      | 16.0 / 18.8                    | 14.4 / 17.1 | 68.3 / 68.7                     | 59.4 / 61.6 | 39.2 / 40.2                      | 27.7 / 29.4 |
| qwen-2.5-32b     | 22.3 / 27.9                    | 21.3 / 31.7 | 69.0 / 71.3                     | 62.2 / 64.7 | 42.5 / 46.7                      | 33.1 / 37.3 |
| gemini-1.5-flash | 28.1 / 35.0                    | 24.0 / 30.6 | 77.7 / 79.9                     | 56.8 / 57.7 | 52.3 / 58.5                      | 25.0 / 26.9 |
| gpt-4            | 44.2 / 59.6                    | 34.4 / 52.1 | 85.2 / 86.9                     | 74.8 / 78.4 | 66.2 / 70.0                      | 50.6 / 57.1 |

Table 49: 5-shot Shuffled / Correct morpheme order results for Finnish in English template for all examined models across tasks. 1-shot and 3-shot results can be found in Tables [47](#page-34-2) and [48.](#page-34-3)

| Models           | ID                 | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |                    |  |
|------------------|--------------------|----------------------------------------|-----------------------------------------------|--------------------|--|
| aya-23-8b        | 74.8 / 62.0 / 60.2 | 59.7 / 53.9 / 51.1                     | 46.4 / 27.9 / 25.4                            | 26.9 / 19.1 / 16.1 |  |
| aya-23-35b       | 83.5 / 69.9 / 67.9 | 74.2 / 64.6 / 61.6                     | 59.5 / 36.8 / 33.3                            | 43.3 / 29.2 / 26.0 |  |
| qwen-2.5-7b      | 81.7 / 71.1 / 68.6 | 75.1 / 65.7 / 63.7                     | 64.1 / 40.5 / 36.3                            | 54.1 / 33.5 / 29.4 |  |
| qwen-2.5-32b     | 79.7 / 77.3 / 76.6 | 54.0 / 53.1 / 52.8                     | 65.5 / 56.7 / 53.8                            | 22.0 / 18.5 / 17.7 |  |
| gemini-1.5-flash | 62.3 / 60.8 / 60.6 | 41.5 / 41.4 / 41.3                     | 35.0 / 32.2 / 31.6                            | 0.6 / 0.4 / 0.4    |  |
| gpt-4            | 85.8 / 85.5 / 83.2 | 63.3 / 61.9 / 60.9                     | 75.7 / 71.4 / 66.9                            | 38.5 / 33.5 / 30.4 |  |

Table 50: 1-shot Random / Language-agnostic / Language-specific negative sample selection results for Turkish in English template for all examined models across tasks.

| Models           | ID                 | Morph. Systematicity (macro-F1)<br>OOD | Morph. Systematicity (coherence)<br>ID<br>OOD |                    |  |
|------------------|--------------------|----------------------------------------|-----------------------------------------------|--------------------|--|
| aya-23-8b        | 74.4 / 64.6 / 61.9 | 53.0 / 49.3 / 47.1                     | 45.6 / 31.4 / 28.1                            | 21.5 / 15.7 / 13.4 |  |
| aya-23-35b       | 88.2 / 80.1 / 78.8 | 80.4 / 71.0 / 71.0                     | 72.9 / 52.6 / 48.9                            | 60.5 / 39.9 / 38.1 |  |
| qwen-2.5-7b      | 81.2 / 73.6 / 71.6 | 75.3 / 66.8 / 65.6                     | 63.8 / 44.3 / 38.8                            | 53.5 / 33.9 / 32.2 |  |
| qwen-2.5-32b     | 88.3 / 84.7 / 83.4 | 74.5 / 71.3 / 69.8                     | 78.3 / 66.3 / 63.6                            | 55.4 / 45.7 / 42.4 |  |
| gemini-1.5-flash | 80.2 / 80.8 / 79.9 | 51.7 / 52.8 / 51.5                     | 65.3 / 63.6 / 60.8                            | 17.8 / 19.3 / 17.3 |  |
| gpt-4            | 93.7 / 90.2 / 89.1 | 82.4 / 77.7 / 74.1                     | 88.1 / 76.8 / 72.7                            | 66.8 / 55.9 / 45.8 |  |

<span id="page-34-0"></span>Table 51: 3-shot Random / Language-agnostic / Language-specific negative sample selection results for Turkish in English template for all examined models across tasks.

| Models           |                    | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |                    |  |
|------------------|--------------------|---------------------------------|----------------------------------|--------------------|--|
|                  | ID                 | OOD                             | ID                               | OOD                |  |
| aya-23-8b        | 77.4 / 67.5 / 66.6 | 58.1 / 51.5 / 50.6              | 51.0 / 36.0 / 33.5               | 25.5 / 18.4 / 17.3 |  |
| aya-23-35b       | 89.6 / 81.8 / 80.5 | 80.7 / 72.1 / 70.9              | 75.8 / 55.8 / 51.8               | 60.5 / 41.8 / 38.8 |  |
| qwen-2.5-7b      | 83.1 / 74.6 / 72.1 | 76.0 / 66.0 / 65.0              | 64.3 / 45.1 / 39.7               | 52.9 / 33.1 / 30.3 |  |
| qwen-2.5-32b     | 90.1 / 85.9 / 83.9 | 81.3 / 75.3 / 73.6              | 80.3 / 66.8 / 61.8               | 64.7 / 48.3 / 45.8 |  |
| gemini-1.5-flash | 87.8 / 85.4 / 85.3 | 61.6 / 62.1 / 59.4              | 78.3 / 70.7 / 68.6               | 34.5 / 33.3 / 29.1 |  |
| gpt-4            | 95.4 / 91.6 / 89.4 | 83.7 / 78.8 / 72.1              | 89.2 / 76.6 / 70.8               | 64.7 / 51.4 / 38.7 |  |

Table 52: 5-shot Random / Language-agnostic / Language-specific negative sample selection results for Turkish in English template for all examined models across tasks.

<span id="page-35-0"></span>

| Models                     |      | Morph. Productivity (accuracy)<br>$\mathsf{OOD}$ | $\text{ID}$ | Morph. Systematicity (macro-F1)<br>OOD | ID   | Morph. Systematicity (coherence)<br>OOD |
|----------------------------|------|--------------------------------------------------|-------------|----------------------------------------|------|-----------------------------------------|
| $\text{gpt-4 (temp=0)}^*$  | 54.0 | 44.0                                             | 92.0        | 79.0                                   | 77.0 | 51.0                                    |
| $gpt-4 \text{ (temp=0.3)}$ | 53.0 | 43.0                                             | 92.0        | 79.0                                   | 80.0 | 53.0                                    |
| $gpt-4 \text{ (temp=0.5)}$ | 55.0 | 43.0                                             | 92.0        | 80.0                                   | 80.0 | 53.0                                    |
| $gpt-4 \text{ (temp=0.7)}$ | 53.0 | 43.0                                             | 92.0        | 80.0                                   | 80.0 | 53.0                                    |
| $gpt-4 \text{ (temp=0.9)}$ | 53.0 | 42.0                                             | 92.0        | 79.0                                   | 80.0 | 51.0                                    |

Table 53: 5-shot results for **Turkish** in **English** template for GPT-4 across tasks and different temperature values. \*Corresponds to default decoding setting for main results.

<span id="page-35-1"></span>

| Models                      | Morph. Productivity (accuracy)<br>OOD<br>ID |      | ID   | Morph. Systematicity (macro-F1)<br>$\mathsf{OOD}$ | Morph. Systematicity (coherence)<br>OOD |      |
|-----------------------------|---------------------------------------------|------|------|---------------------------------------------------|-----------------------------------------|------|
| $\text{gpt-4 (top_p=1)}^*$  | 54.0                                        | 44.0 | 92.0 | 79.0                                              | 77.0                                    | 51.0 |
| $\text{gpt-4 (top_p=0.95)}$ | 53.0                                        | 43.0 | 92.0 | 78.0                                              | 79.0                                    | 51.0 |
| $gpt-4$ (top_p=0.9)         | 54.0                                        | 42.0 | 92.0 | 78.0                                              | 80.0                                    | 52.0 |

Table 54: 5-shot results for **Turkish** in **English** template for GPT-4 across tasks and different top\_p values. \*Corresponds to default decoding setting for main results.

<span id="page-35-2"></span>

| Models                     | ID   | Morph. Productivity (accuracy)<br>OOD | ID   | Morph. Systematicity (macro-F1)<br>OOD | ID   | Morph. Systematicity (coherence)<br>OOD |
|----------------------------|------|---------------------------------------|------|----------------------------------------|------|-----------------------------------------|
| $\text{gpt-4 (temp=0)}^*$  | 44.0 | 34.0                                  | 85.0 | 75.0                                   | 66.0 | 51.0                                    |
| $gpt-4 \text{ (temp=0.3)}$ | 45.0 | 36.0                                  | 85.0 | 74.0                                   | 64.0 | 48.0                                    |
| $gpt-4 \text{ (temp=0.5)}$ | 45.0 | 34.0                                  | 85.0 | 73.0                                   | 64.0 | 45.0                                    |
| $gpt-4 \text{ (temp=0.7)}$ | 44.0 | 36.0                                  | 86.0 | 73.0                                   | 65.0 | 46.0                                    |
| $gpt-4 \text{ (temp=0.9)}$ | 44.0 | 33.0                                  | 84.0 | 71.0                                   | 63.0 | 42.0                                    |

Table 55: 5-shot results for **Finnish** in **English** template for GPT-4 across tasks and different temperature values. \*Corresponds to default decoding setting for main results.

<span id="page-35-3"></span>

| Models                      | Morph. Productivity (accuracy) |      |             | Morph. Systematicity (macro-F1) | Morph. Systematicity (coherence) |      |
|-----------------------------|--------------------------------|------|-------------|---------------------------------|----------------------------------|------|
|                             | $\text{ID}$                    | OOD  | $\text{ID}$ | OOD                             | ID                               | OOD  |
| $\text{gpt-4 (top_p=1)}^*$  | 44.0                           | 34.0 | 85.0        | 75.0                            | 66.0                             | 51.0 |
| $\text{gpt-4 (top_p=0.95)}$ | 43.0                           | 34.0 | 86.0        | 73.0                            | 65.0                             | 46.0 |
| $gpt-4$ (top_p=0.9)         | 43.0                           | 34.0 | 85.0        | 79.0                            | 64.0                             | 44.0 |

Table 56: 5-shot results for **Finnish** in **English** template for GPT-4 across tasks and different top\_p values. \*Corresponds to default decoding setting for main results.

<span id="page-35-4"></span>

| Models                       |      | Morph. Productivity (accuracy)<br>OOD |      | Morph. Systematicity (macro-F1)<br>$\mathsf{OOD}$ |      | Morph. Systematicity (coherence)<br>OOD |
|------------------------------|------|---------------------------------------|------|---------------------------------------------------|------|-----------------------------------------|
| $\text{gpt-4 (original)}^*$  | 54.0 | 44.0                                  | 92.0 | 79.0                                              | 77.0 | 51.0                                    |
| $\text{gpt-4 (paraphrased)}$ | 56.0 | 46.0                                  | 93.0 | 80.0                                              | 81.0 | 54.0                                    |

Table 57: 5-shot results for **Turkish** in **English** template for GPT-4 across tasks and different prompt instructions. \*Corresponds to default prompt instructions for main results.

<span id="page-35-5"></span>

| Models                                                                             |      | Morph. Productivity (accuracy)<br>$\mathsf{OOD}$ |      | Morph. Systematicity (macro-F1)<br>00D | $\text{ID}$ | Morph. Systematicity (coherence)<br>OOD |
|------------------------------------------------------------------------------------|------|--------------------------------------------------|------|----------------------------------------|-------------|-----------------------------------------|
| $\text{gpt-4 (original)}^*$                                                        | 44.0 | 34.0                                             | 85.0 | 75.0                                   | 66.0        | 51.0                                    |
| $gpt-4 \n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n$ | 46.0 | 37.0                                             | 84.0 | 73.0                                   | 62.0        | 45.0                                    |

Table 58: 5-shot results for **Finnish** in **English** template for GPT-4 across tasks and different prompt instructions. \*Corresponds to default prompt instructions for main results.