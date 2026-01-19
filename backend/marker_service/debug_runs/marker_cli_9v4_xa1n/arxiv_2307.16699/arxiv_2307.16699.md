# Ontology engineering with Large Language Models

Patricia Mateiu\* and Adrian Groza\* <sup>\*</sup>Department of Computer Science, Technical University of Cluj-Napoca, 400114 Cluj-Napoca, Romania {patriciamateiu33@gmail.com, adrian.groza@cs.utcluj.ro}

Abstract—We tackle the task of enriching ontologies by automatically translating natural language sentences into Description Logic. Since Large Language Models (LLMs) are the best tools for translations, we fine-tuned a GPT-3 model to convert Natural Language sentences into OWL Functional Syntax. We employ objective and concise examples to fine-tune the model regarding: instances, class subsumption, domain and range of relations, object properties relationships, disjoint classes, complements, cardinality restrictions. The resulted axioms are used to enrich an ontology, in a human supervised manner. The developed tool is publicly provided as a Protégé plugin.

### I. MOTIVATION

The technical challenges and costs associated with the development of ontologies are arguable the main causes for the partial failure of the Semantic Web. Aiming to facilitate the development of ontologies by industry, the economical aspects of ontology engineering have been subject to the Ontology Cost Model (ONTOCOM) [1]. Despite the existence of several ontology engineering methodologies (OEMs) (no less than 15 as identified by [2] in 2013), the domain of Semantic Web does not benefit from a mature and largely accepted methodology. More recently, [3] have analysed 9 OEMs, concluding that non-collaborative methodologies have a negative impact on the liveness, evolution, and reusability of the ontologies.

We rely here on the current opportunities provided by Large Language Models (LLMs). We argue that LLMs have the potential to largely increase the efficiency of the ontology engineering. Since LLMs are best technology for language translation, our employ them to translate from natural language to description logic (DL). That is, given a description in natural language (definition, domain knowledge), the aim is to automatically obtain corresponding ontology in a formal language. We developed a tool able to enrich and populate an ontology with domain knowledge available in natural language. The tool relies on GPT-3 which we fine-tuned for the ontology engineering task. The solution is freely available and is provided as a plugin for the Protégé editor.

### II. TUNING THE MODEL FOR OWL

The tool is constructed as a Protégé plugin that supports the development of an ontology from scratch and also the enrichment of an existing ontology. Natural language sentences are translated into ontological elements and appended to the current ontology (Figure 1). The prompts are sent to a fine-tuned GPT-3 davinci model which returns the result into ontology axioms. Technically, these axioms are handled

<span id="page-0-0"></span>![](_page_0_Figure_8.jpeg)

Fig. 1: Data flow for the presented approach

using the *owlapi* Java library [4], and appended to the active ontology in the Protégé editor.

We developed a dataset of 150 pairs of prompts and their corresponding translations into OWL Functional Syntax. We seek to cover various cases and to incorporate a variety of domains, in favor of attaining an adaptable model. Tables I and II depict some of the prompts used in the training set. We used the following conventions:

First, the underscore symbol is used for elements having multiple words, since it is the default naming convention used in Protégé, e.g., the object property named *has\_sibling* or compound individual names such as Wolfgang\_Amadeus\_Mozart.

Second, we settled the class and object property names in only lowercase letters, while the individual names can begin either with a lowercase or an uppercase letter.

Third, for subclass relationships, to highlight the general aspect, several connection words were used. For example, the sentence *every man is a person* creates a subclass relationship between the class *person* and the class *man*. If these classes do not exist in the ontology, the declaration axioms will generate them. Otherwise, these axioms are ignored. The quantifier *every* is used to emphasize that there is no instance where an individual that belongs to the class *man* will not belong to the class *person*. Other connection words can be used for defining this type of relationship, e.g., all lilies are flowers, cats are a *type of animal*. Multiple subclass relationships can be used at the same time, as in the example *bugs*, *ants*, *ladybugs*, *flies* are insects.

TABLE I: Fine-tuning davinci model for classes

<span id="page-1-0"></span>

| Prompt                     | Result                                              |
|----------------------------|-----------------------------------------------------|
|                            | $\text{Declaration}(\text{Class}(\text{:girl}))$    |
| Anna is a girl             | Declaration(NamedIndividual(:Anna))                 |
|                            | Class Assertion(:girl : Anna)                       |
|                            | $\text{Declaration}(\text{Class}(\text{:flower}))$  |
| every rose is a flower     | $\text{Declaration}(\text{Class}(\text{:rose}))$    |
|                            | SubClassOf::rose::flower)                           |
|                            | $\text{Declaration}(\text{Class}(\text{:male}))$    |
| Brandon is a male artist   | $\text{Declaration}(\text{Class}(\text{:artist}))$  |
|                            | Declaration(NamedIndividual(:Brandon))              |
|                            | Class Assertion(:male : Brandon)                    |
|                            | Class Assertion("artist: Brandon")                  |
|                            | $\text{Declaration}(\text{Class}(\text{:man}))$     |
| no woman is a man          | $\text{Declaration}(\text{Class}(\text{:woman}))$   |
|                            | DisjointClasses(:man :woman)                        |
|                            | $\text{Declaration}(\text{Class}(\text{:cat}))$     |
| $\text{Tina is not a cat}$ | $\text{Declaration}(\text{NamedIndividual}('Tina))$ |
|                            | $Class Assertion(ObjectComponentOf(:cat) : Tina)$   |

<span id="page-1-1"></span>TABLE II: Fine-tuning davinci model for object properties

| Prompt                                                                            | Result                                                                                                               |  |
|-----------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------|--|
|                                                                                   | $Declaration(ObjectProperty:(has\_sister))$                                                                          |  |
|                                                                                   | Declaration(NamedIndividual(:Anna))                                                                                  |  |
| Sarah and Anna are                                                                | Declaration(NamedIndividual(:Sarah))                                                                                 |  |
| each other's sisters                                                              | ObjectPropertyAssertion(:has_sister :Anna :Sarah)                                                                    |  |
|                                                                                   | ObjectPropertyAssertion(:has_sister :Sarah :Anna)                                                                    |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:bike}))$                                                                     |  |
| Mia owns 2 bikes                                                                  | $Declaration(ObjectProperty(:\nown))$                                                                                |  |
|                                                                                   | $\text{Declaration}(\text{NamedIndividual}(:\text{Mia}))$                                                            |  |
|                                                                                   | $Class Assertion(ObjectExactCardinality(2 :owns :bike) : Mia)$                                                       |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text:tractor}))$                                                                   |  |
| Michael owns tractors                                                             | Declaration(ObjectProperty:owns))                                                                                    |  |
|                                                                                   | $\text{Declaration}(\text{NamedIndividual}(\text{:Michael}))$                                                        |  |
|                                                                                   | ClassAssertion(ObjectSomeValuesFrom(:owns :tractor) :Michael)                                                        |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:carrot}))$                                                                   |  |
| rabbits eat only car-                                                             | $\text{Declaration}(\text{Class}(:\text{rabbit}))$<br>$Declaration(ObjectProperty(:\text{eats}))$                    |  |
| rots                                                                              |                                                                                                                      |  |
|                                                                                   | SubClassOf(:rabbit ObjectAllValuesFrom(:eats :carrot))<br>$\text{Declaration}(\text{Class}(\text{:animal}))$         |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:tail}))$                                                                     |  |
| all animals have ex-                                                              |                                                                                                                      |  |
| actly one tail                                                                    | Declaration(ObjectProperty:has))                                                                                     |  |
|                                                                                   | EquivalentClasses(:animal ObjectExactCardinality(1 :has :tail))<br>$\text{Declaration}(\text{Class}(\text{:child}))$ |  |
|                                                                                   | $\text{Declaration}(\text{Class}(:\text{female}))$                                                                   |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:mother}))$                                                                   |  |
| a mother is a female                                                              | Declaration(ObjectProperty:has))                                                                                     |  |
| who has at least 1                                                                | EquivalentClasses(:mother ObjectIntersectionOf                                                                       |  |
| child                                                                             | (:female ObjectMinCardinality(1 :has :child)))                                                                       |  |
|                                                                                   | Declaration(ObjectProperty(:has_mother))                                                                             |  |
|                                                                                   | $\text{Declaration}(\text{NamedIndividual}(\text{:Penn}))$                                                           |  |
| Penn's mother is So-                                                              | Declaration(NamedIndividual(:Sonia))                                                                                 |  |
| nia                                                                               | ObjectPropertyAssertion(:has_mother :Penn :Sonia)                                                                    |  |
|                                                                                   | Declaration(ObjectProperty(:knows))                                                                                  |  |
|                                                                                   | Declaration(NamedIndividual(:Anna))                                                                                  |  |
| Anna does not know                                                                | Declaration(NamedIndividual(:Sabina))                                                                                |  |
| Sabina                                                                            | NegativeObjectPropertyAssertion(:knows :Anna :Sabina)                                                                |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:movie}))$                                                                    |  |
|                                                                                   | $Declaration(ObjectProperty(:is_a fan_of))$                                                                          |  |
| Jenna is a fan of Brit-                                                           | $\text{Declaration}(\text{NamedIndividual}(\text{:Britney} \text{ Spears}))$                                         |  |
| ney Spears                                                                        | Declaration(NamedIndividual(:Jenna))                                                                                 |  |
|                                                                                   | ObjectPropertyAssertion(:is_a_fan_of :Jenna :Britney_Spears)                                                         |  |
|                                                                                   | Declaration(ObjectProperty(:hates))                                                                                  |  |
|                                                                                   | Declaration(NamedIndividual(:Cora))                                                                                  |  |
| Cora and Meena hate                                                               | Declaration(NamedIndividual(:Meena))                                                                                 |  |
| each other                                                                        | ObjectPropertyAssertion(:hates :Cora :Meena)                                                                         |  |
|                                                                                   | ObjectPropertyAssertion(:hates :Meena :Cora)                                                                         |  |
|                                                                                   | $\text{Declaration}(\text{Class}(\text{:female}))$                                                                   |  |
| anyone who is a sister<br>is female<br>anybody who has a<br>brother has a sibling | $Declaration(ObjectProperty:has\_sister))$                                                                           |  |
|                                                                                   | ObjectPropertyRange(:has_sister :female)                                                                             |  |
|                                                                                   | $\text{Declaration(ObjectProperty:has brother)})$                                                                    |  |
|                                                                                   | $Declaration(ObjectProperty:has\_sibling))$                                                                          |  |
|                                                                                   | SubObjectPropertyOf(:has_brother :has_sibling)                                                                       |  |
|                                                                                   | Declaration(ObjectProperty(:has_friend))                                                                             |  |
| if $X$ has friend $Y$ then<br>$Y$ has friend $X$                                  | SymmetricObjectProperty(:has_friend)                                                                                 |  |
| if X has mother $Y$                                                               | $\text{Declaration(ObjectProperty:has\_mother)})$                                                                    |  |
| then Y does not have                                                              | AsymmetricObjectProperty(:has_mother)                                                                                |  |
| $\text{mother } X$                                                                |                                                                                                                      |  |
|                                                                                   |                                                                                                                      |  |

<span id="page-1-2"></span>![](_page_1_Picture_4.jpeg)

Fig. 2: Adding new instances and classes

<span id="page-1-3"></span>

| Class hierarchy:         | 200                        | GPT Ontology Augmenter:                                                                         |
|--------------------------|----------------------------|-------------------------------------------------------------------------------------------------|
| ் ⊠                      | ≎<br>Asserted              | Write the text you want to add to                                                               |
| owl:Thing<br>girl        |                            | Lana is a girl.                                                                                 |
| Individu; 🏻 🗏 🗉 🗷        | Property assertio 🛚 🗆 🗷    |                                                                                                 |
|                          | Object property assertions | CLEAF<br>ADD                                                                                    |
| girl (2)<br>Lana<br>Anna | Data property assertions   | Declaration(Class(:girl))<br>Declaration(NamedIndividual(:Lana))<br>ClassAssertion(:girl :Lana) |
|                          |                            |                                                                                                 |

Fig. 3: Adding individuals to existing classes

### III. EXPERIMENTS

### A. Running Scenario

We exemplify the functionalities of the plugin on the family ontology. First, let the sentence  $s_1$ : Ana is a girl, which the tool automatically translates in OWL Functional Syntax with three axioms (line 1 in Table I).

| Declaration(Class(:girl)) |  |  |  |  |  |  |
|---------------------------|--|--|--|--|--|--|
|---------------------------|--|--|--|--|--|--|

#### Declaration(NamedIndividual(: Anna)) (2)

ClassAssertion(: girl : Anna) (3)

Since the first axiom is a declaration, the new class, girl is added to the taxonomy, as subclass of the top concept, owl: Thing (see Figure 2). The second axiom is also a declaration, but of an individual, and will be added to the *Individuals* by type panel. Additionally, the class will appear in this panel as well, since the third axiom is a class assertion axiom, meaning that the individual Anna is included in the class girl. These axioms are added to a temporary ontology, and retrieved using *OWLAPI* library.

Second, let the sentence  $s_2$ : Lana is a girl. This statement involves the same class as in  $s_1$ , but a different individual in the assertion. The ontology will be populated with the new individual Lana, which belongs to the already existing class girl. Figure 3 shows that the new individual is added to the list corresponding to class defined in the first step.

Third, let the alternative sentence  $s_3$ : Anna and Lana are girls. Here, instead of specifying the class for each named individual, multiple individuals belong to the same collective

<span id="page-2-0"></span>

| Class hierarchy:           |                            | I GPT Ontology Augmenter:                                                                               |
|----------------------------|----------------------------|---------------------------------------------------------------------------------------------------------|
| 💺 🖫 🔘                      | Asserted<br>≎              | Write the text you want to add to                                                                       |
| owl:Thing<br>girl          |                            | Anna and Lana are girls.                                                                                |
| Individu: 🏻 🗆 🗷            | Property assertio 🏻 🗆 🗷    |                                                                                                         |
| girl (2)                   | Object property assertions | CLEAR<br>ADD                                                                                            |
| Lana<br>Anna               | Data property assertions   | Declaration(Class(:girl))<br>Declaration(NamedIndividual(:Anna))<br>Declaration(NamedIndividual(:Lana)) |
| Object property hierarchy: | 2010                       | ClassAssertion(:girl :Anna)                                                                             |
|                            | C.<br>Asserted             | ClassAssertion(:girl :Lana)                                                                             |

Fig. 4: Formalising multiple individuals belonging to the same collective class

<span id="page-2-1"></span>![](_page_2_Figure_2.jpeg)

Fig. 5: Handling symmetric relations

class *girl*. The plugin is able to deliver the same ontology as in case of statements *s*<sup>1</sup> and *s*<sup>2</sup> (see Figure [4\)](#page-2-0). The class is declared only once, while the second declaration of the same class is ignored. The trained model offers the users several options in transmitting the components they want to include in the ontology.

Fourth, one can add object properties. Consider the statement *s*4: *Anna and Lana are each other's sisters*. The resulted property is attached to the object property taxonomy, and the assertions can be seen in the third panel of the left half in Figure [5,](#page-2-1) by clicking on each individual. Figure [5](#page-2-1) presents the relation *Lana has sister Anna* and the inverse relation.

Fifth, one can add assertions about new individuals. Let *s*5: *Nola and Anna are each other's cousins*. In this case, *Nola*, who was not defined prior and has no class association, will be added as an individual, but separate than the ones grouped by class. The object property will be added for both individuals, just like in the previous step (see Figure [6\)](#page-2-2).

<span id="page-2-2"></span>

| Class hierarchy:                                  | 2 11 2 3                   | GPT Ontology Augmenter:<br>$\Box \Box \Box \Box$                                        |
|---------------------------------------------------|----------------------------|-----------------------------------------------------------------------------------------|
| 🐮 🐍 - ळ                                           | $\circ$<br>Asserted        | Write the text you want to add to the ontology                                          |
| owl:Thing<br>🔵 girl                               |                            | Nola and Anna are each other's cousins.                                                 |
| Individuals t 🗆 🗏 🗷                               | Property assertions: A     |                                                                                         |
| ⋙                                                 | Object property assertions |                                                                                         |
| Nola<br>girl (2)                                  | has_cousin 🕤 🔘 🗙 💿<br>Nola | CLEAR<br>ADD                                                                            |
| Anna<br>Lana                                      | has sister 🍙<br>Lana       | Declaration(ObjectProperty(:has cousin))<br>Declaration(NamedIndividual(:Anna))         |
| Object property hierarchy:                        | 70808                      | Declaration(NamedIndividual(:Nola))<br>ObjectPropertyAssertion(:has_cousin :Anna :Nola) |
|                                                   | C<br>Asserted              | ObjectPropertyAssertion(:has cousin :Nola :Anna)                                        |
| owl:topObjectProperty<br>has_cousin<br>has_sister |                            |                                                                                         |

Fig. 6: Adding assertions about new individuals

## *B. Prompt engineering strategies*

We run experiments with three strategies: zero-shot learning, few-shot learning and fine-tuning.

The *Zero-shot learning* strategy asks the language model to generate the output directly, with no presented examples. Several experiments were run with this strategy, using the GPT-3.5-turbo model. The results were, although not incorrect, not the expected ones. For example, using prompt *Translate 'Anna is a girl' into Functional Syntax*, the model returned *is(Anna, girl)*, which is not helpful since it is not in the form of an axiom. It rather represents the relationship *is* between *Anna* and *girl*, yet does not offer any information on the form or meaning of these words.

The *few-shot learning* strategy lets LLMs train for specific tasks from a few examples. To assess this strategy, we tested various prompts. The first trial was *Anna is a girl*, whose corresponding axioms are also included in the example. The outcome for this prompt was not the expected one and the solution was proven to be inconsistent, returning different results for the same prompt. In the first trial, besides the declarations and the class assertion for individual *Anna* and class *girl*, the response includes other axioms, that are not logical for the given context. Namely, the last line is an object property assertion between an individual and a class, which is not possible. The second trial is not as faulty, it does not include incorrect axioms, but it includes extra axioms that are not needed. For example, the declaration for the class *person* and the object property *married to*, which are not in the prompt. Results such as this one would cause users to have an ontology that is too big, and only partially used, which, in fact, contradicts their preferences and intentions.

The *fine-tuning* strategy requires a dedicated dataset. A dataset with 150 prompt-result pairs and a validation set with 50 such pairs were used, with the same format and variation as those in the training data set, but with different cases and examples. The validation data set is used to determine the optimal combination of hyper-parameters that would have the best token accuracy. Regarding the data structure, several tests were done to determine the correct order of the completion result with respect to the prompt. One question was whether it was better to write the declarations and assertion or relationship axioms in the order that the words appear in the sentence or to write them in the order that Proteg´ e would save them in a ´ Functional Syntax. Both options were considered in training with several combinations of hyper-parameters.

### IV. RELATED WORK

Before the LLMs era tools like Fred [\[5\]](#page-3-4) were used. Fred is a machine reader designed for the Semantic Web that can analyze natural language in 48 different languages and generates linked data in the OWL format. However, the resulting axioms require further processing before they can be effectively utilized for reasoning. In the recent years, there have been various approaches in learning ontologies from text data, by extracting the ontological terms and structuring them into one component [\[6\]](#page-3-5). For instance, Boziˇ c [\[7\]](#page-3-6) has analysed ´ the potential combining Semantic Web and GPT, as well as the related risks that might pose a threat.

OntoGPT tool [\[8\]](#page-3-7) extracts information from text, by using three strategies: SPIRES, HALO, and SPINDOCTOR. SPIRES applies a knowledge schema on the input text and returns an instance with multiple attribute-value relations, where the values are either data primitives or other instances, thus creating a linked scheme. HALO is a Few-Shot Learning approach, which solves tasks with limited number of examples for learning while using prior knowledge.

Conceptual modelling using large language models have been experienced by [\[9\]](#page-4-0). ChatGPT was used to generate entityrelations diagrams (ER). The designed prompt starts with an explanation of ER diagrams. Then the prompt includes an example of ER diagram in JSON syntax. The last part of the prompt is the natural language description of the task. A second experiment has focused on business process diagrams. A subset of BPMN diagrams has been considered. The prompt describes the meta-model in NL (e.g. a task has exactly one predecessor and one successor) and an example in JSON format. The third experiment has targeted UML class diagrams, for which a Zero-Shot approach has been preferred. Even if large parts of the conceptual modelling was correct, modelling experience of a human expert was required to validate the model.

GraphGPT [\[10\]](#page-4-1) converts natural language into knowledge graphs. The application does not imply ontology population, it rather offers the users a view on how the data they submit might be connected. Bikeyev [\[11\]](#page-4-2) has proposed an alternative of knowledge model engineering and knowledge graph generation as an automated approach that avoids the vagueness of Natural Language Processing. A bottom-up approach is combined to a LLM, namely GPT-3. The method uses two types of prompts, one to generate a hierarchy of elements and the other to determine possible relationships between them. In both cases, it is necessary that the prompts respect memory limitations, so that the prompt and the result can fit entirely in the given memory slot. After the initial hierarchy is constructed, each element can be used in another prompt to give a more detailed result, and this step can continue until the result is satisfactory. The advantage is that this approach can suit the individual preferences of each user, depending on how much detail they need in the ontology. GraphGPT can incorporate newly available data when updating, thus allowing a form of stream reasoning [\[12\]](#page-4-3) when populating the knowledge graph.

Csaszar and Slavescu have developed a tool to help software developers visualize the call graph of their code while editing it. Two graphs are automatically built from the source code: the import graph and the call graph. Instead of LLMs, the process of building the two graphs is based on using a query based architecture, commonly used by language servers [\[13\]](#page-4-4)

In a literature dominated by transformers, Ilies and Marginean have used grammars to provide a white box alternative [\[14\]](#page-4-5). Context free grammars and semantic roles are used to structure knowledge from texts related to cooking recipes. Lex and Yacc interleave with AllenNLP to compute a parse tree for a cooking recipe, where each group of words is labeled with an appropriate semantic role. The approach can be applied to other types of instruction manuals.

Yang et al. [\[15\]](#page-4-6) have developed LOGICLLAMA, a finetuned tool used for natural language to First-Order Logic translation, which can be also used for correcting FOL results generated by GPT-3.5 and is comparable to GPT-4. The MALLS dataset contains pairs NL-FOL generated by GPT-4 and is intended to be used for fine-tuning and testing the model. These pairs are resulted by repeatedly prompting GPT-4 using a pipeline which adjusts depending on the previous results. The LLOGICLLAMA is obtained from training and fine-tuning a model using the MALLS data set for two main tasks, generating translation from NL to FOL and correcting already generated translations by GPT-3.5. The first one uses natural language text as input and provides FOL output, while the second one uses a pair of NL and the resulted FOL translation returned by GPT-3.5 and provides a single output in FOL, representing the necessary adjustments or corrections.

### V. CONCLUSION

The developed plugin shows hows language models (e.g. GPT) can be used in automating learning and populating ontologies, a process which is very time-consuming, complex and could be overwhelming in terms of decision making. The aim was to exploit the capabilities of pre-trained language models to obtain OWL axioms. Aware of the limitations and risks of Large Language Models, the tool aims to be a support tool that saves development time. It also reduces the interaction time with the domain expert, given that a description of the domain exists in natural language. Ongoing work regards quantitative evaluation and assessing the efficiency of ontology engineering with and without the tool.

### REFERENCES

- <span id="page-3-0"></span>[1] E. Paslaru Bontas Simperl, C. Tempich, and Y. Sure, "Ontocom: A cost estimation model for ontology engineering," in *5th Int. Semantic Web Conf., ISWC 2006, Athens, GA, USA, November 5-9*. Springer, 2006, pp. 625–639.
- <span id="page-3-1"></span>[2] R. Iqbal, M. A. A. Murad, A. Mustapha, N. M. Sharef *et al.*, "An analysis of ontology engineering methodologies: A literature review," *Research journal of applied sciences, engineering and technology*, vol. 6, no. 16, pp. 2993–3000, 2013.
- <span id="page-3-2"></span>[3] K. I. Kotis, G. A. Vouros, and D. Spiliotopoulos, "Ontology engineering methodologies for the evolution of living and reused ontologies: status, trends, findings and recommendations," *The Knowledge Engineering Review*, vol. 35, p. e4, 2020.
- <span id="page-3-3"></span>[4] M. Horridge and S. Bechhofer, "The OWL API: A Java api for OWL ontologies," *Semantic web*, vol. 2, no. 1, pp. 11–21, 2011.
- <span id="page-3-4"></span>[5] F. Draicchio, A. Gangemi, V. Presutti, and A. G. Nuzzolese, "Fred: From natural language text to RDF and OWL in one click," in *The Semantic Web: ESWC 2013 Satellite Events: Montpellier, France, May 26-30, 2013, Revised Selected Papers*. Springer, 2013, pp. 263–267.
- <span id="page-3-5"></span>[6] F. N. Al-Aswadi, H. Y. Chan, and K. H. Gan, "Automatic ontology construction from text: a review from shallow to deep learning trend," *Artificial Intelligence Review*, vol. 53, pp. 3901–3928, 2020.
- <span id="page-3-6"></span>[7] V. Boziˇ c, "Semantic web and generative pre-trained transformer (gpt)." ´
- <span id="page-3-7"></span>[8] J. H. Caufield, H. Hegde, V. Emonet *et al.*, "Structured prompt interrogation and recursive extraction of semantics (spires): A method for populating knowledge bases using zero-shot learning," *arXiv preprint arXiv:2304.02711*, 2023.

- <span id="page-4-0"></span>[9] H.-G. Fill, P. Fettke, and J. Kopke, "Conceptual modeling and large ¨ language models: impressions from first experiments with chatgpt," *Enterprise Modelling and Information Systems Architectures (EMISAJ)*, vol. 18, pp. 1–15, 2023.
- <span id="page-4-1"></span>[10] "Graph GPT." [Online]. Available:<https://graphgpt.vercel.app>
- <span id="page-4-2"></span>[11] A. Bikeyev, "Synthetic ontologies: A hypothesis," *Available at SSRN 4373537*, 2023.
- <span id="page-4-3"></span>[12] A. Groza and I. A. Letia, "Plausible description logic programs for stream reasoning," *Future Internet*, vol. 4, no. 4, pp. 865–881, 2012.
- <span id="page-4-4"></span>[13] I.-A. Csasz ´ ar and R. R. Slavescu, "Interactive call graph generation ´ for software projects," in *2020 IEEE 16th International Conference on Intelligent Computer Communication and Processing (ICCP)*. IEEE, 2020, pp. 51–58.
- <span id="page-4-5"></span>[14] A. Ilies and A. N. Marginean, "Understanding cooking recipes' structure using grammars," in *2021 IEEE 17th International Conference on Intelligent Computer Communication and Processing (ICCP)*. IEEE, 2021, pp. 327–334.
- <span id="page-4-6"></span>[15] Y. Yang, S. Xiong, A. Payani, E. Shareghi, and F. Fekri, "Harnessing the power of large language models for natural language to first-order logic translation," *arXiv preprint arXiv:2305.15541*, 2023.