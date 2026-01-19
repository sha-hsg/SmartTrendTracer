# SciMantify - A Hybrid Approach for the Evolving Semantification of Scientific Knowledge

Lena John1[0009 −0007 −2097 <sup>−</sup>9761], Kheir Eddine Farfar1[0000 −0002 −0366 −4596] , Sören Auer1[0000 −0002 −0698 <sup>−</sup>2864], and Oliver Karras1[0000 −0001 −5336 −6899]

TIB - Leibniz Information Centre for Science and Technology, Hannover, Germany {lena.john, kheir.farfar, soeren.auer, oliver.karras}@tib.eu

Abstract. Scientific publications, primarily digitized as PDFs, remain static and unstructured, limiting the accessibility and reusability of the contained knowledge. At best, scientific knowledge from publications is provided in tabular formats, which lack semantic context. A more flexible, structured, and semantic representation is needed to make scientific knowledge understandable and processable by both humans and machines. We propose an evolution model of knowledge representation, inspired by the 5-star Linked Open Data (LOD) model, with five stages and defined criteria to guide the stepwise transition from a digital artifact, such as a PDF, to a semantic representation integrated in a knowledge graph (KG). Based on an exemplary workflow implementing the entire model, we developed a hybrid approach, called SciMantify, leveraging tabular formats of scientific knowledge, e.g., results from secondary studies, to support its evolving semantification. In the approach, humans and machines collaborate closely by performing semantic annotation tasks (SATs) and refining the results to progressively improve the semantic representation of scientific knowledge. We implemented the approach in the Open Research Knowledge Graph (ORKG), an established platform for improving the findability, accessibility, interoperability, and reusability of scientific knowledge. A preliminary user experiment showed that the approach simplifies the preprocessing of scientific knowledge, reduces the effort for the evolving semantification, and enhances the knowledge representation through better alignment with the KG structures.

Keywords: Evolution model · Semantification · Hybrid approach

## 1 Introduction

Publications remain the primary medium for scientific communication [\[8\]](#page-7-0). Despite efforts to digitize them as PDFs, scientific knowledge largely remains static and unstructured [\[2\]](#page-7-1). The next step in digital transformation calls for flexible, structured, and semantic representations to make knowledge more accessible and usable by humans and machines [\[11,](#page-7-2)[10\]](#page-7-3). Structured, machine-actionable knowledge is increasingly necessary due to the growing volume of publications and the demand for reusability [\[18\]](#page-7-4). While some approaches, such as SciKGTeX [\[2\]](#page-7-1), enable FAIR-by-Design publications [\[17\]](#page-7-5), most are only published as PDFs. At best, data is shared in tabular formats, such as results from secondary studies, which offer promising potential for semantification according to the [SemTab](https://www.cs.ox.ac.uk/isg/challenges/sem-tab/) [Challenge](https://www.cs.ox.ac.uk/isg/challenges/sem-tab/) [\[6\]](#page-7-6). In this paper, we propose an evolution model of knowledge representation inspired by the [5-star Linked Open Data \(LOD\) model.](https://5stardata.info/en/) This model defines five stages with criteria to guide the transformation from static digital artifacts, e.g., PDFs, to semantic representations integrated into a knowledge graph (KG). We illustrate the implementation of the model through an exemplary workflow based on the established services [ORKG Ask](https://ask.orkg.org/) [\[1\]](#page-7-7) and [ORKG](https://orkg.org/) [\[18\]](#page-7-4). Building on this model, we introduce SciMantify, a hybrid approach that leverages tabular formats to support the gradual semantification of scientific knowledge. Hybrid methods, combining human insight and machine automation, emerged as a promising solution to this task [\[4\]](#page-7-8). In SciMantify, humans and machines collaboratively perform semantic annotation tasks (SATs), refining results and incrementally improving semantic representations. The approach is implemented within ORKG, a core service in Germany's National Research Data Infrastructure for FAIR scientific knowledge [\[9,](#page-7-9)[18\]](#page-7-4). We evaluated SciMantify in a preliminary user experiment with eight participants. Results show high usability (SUS score: 87.5) [\[12\]](#page-7-10), and participants agreed it significantly reduces preprocessing and semantification effort, averaging 17 minutes overall. We provide the following contributions: 1) The evolution model of knowledge representation, 2) The hybrid approach SciMantify, 3) A first release of SciMantify in the ORKG, and 4) Preliminary results indicating promising support by SciMantify.

## 2 Related Work

Evolution of Knowledge Representation. Liang et al. [\[14\]](#page-7-11) propose a threelayer network combining citation and content analysis to trace knowledge flow and evolution. Li et al. [\[13\]](#page-7-12) present the MGraph approach, a semantic data model that transforms unstructured data into structured to track concept evolution over time. In contrast, our approach presents a generic evolution model emphasizing the transition from unstructured scientific knowledge in a digital artifact to a flexible, structured, and semantic representation integrated in a KG. Semantic Annotation. Semantic table annotation (STA) enriches tabular data by linking it to KGs, enhancing its meaning and interoperability [\[5\]](#page-7-13). Recent approaches, with significant contributions by the SemTab challenge [\[6\]](#page-7-6), include heuristic, feature engineering, and deep learning-based methods [\[15\]](#page-7-14). Tools like DAGOBAH UI [\[7\]](#page-7-15) and TabbyLD2-Client [\[4\]](#page-7-8) offer user-friendly interfaces: The former focuses on automation, while the latter supports hybrid annotation with manual refinement for broader accessibility.

STA faces key challenges, such as handling context, data heterogeneity, and metadata [\[3](#page-7-16)[,15\]](#page-7-14), as well as unmatched entities and incomplete KGs, that reduce annotation accuracy [\[3](#page-7-16)[,7\]](#page-7-15). Most works focus on tables with single value-cells, limiting real-world application [\[4,](#page-7-8)[7,](#page-7-15)[15\]](#page-7-14), and often lack intuitive UIs [\[3,](#page-7-16)[4\]](#page-7-8). To address these issues, we propose SciMantify, a hybrid approach introducing SATs as human-machine collaboration. Unlike fully automated methods that trade off accuracy for efficiency [\[15\]](#page-7-14), SciMantify aims to achieve both through integration with the ORKG's user-friendly UI to better support non-technical users.

## 3 Evolution Model, Workflow, and Hybrid Approach

#### 3.1 Evolution Model of Knowledge Representation

The starting point of our work is the evolution model of knowledge representation (see Fig. [1\)](#page-2-0), which we developed iteratively by testing, evaluating, and refining it through its application to different digital artifacts.

Inspired by the 5-star LOD model, our five-stage evolution model defines criteria for transitioning from unstructured scientific knowledge in a digital artifact to a semantic representation integrated in a KG. Unlike the LOD model, which focuses on the progressive openness and interoperability of data, our model focuses on the specific challenges to represent scientific knowledge.

<span id="page-2-0"></span>![](_page_2_Picture_6.jpeg)

Fig. 1: Evolution model of knowledge representation.

The first stage Access through Digital Artifact ensures scientific knowledge is accessible in human-readable digital formats, e.g., PDFs, with stable identifiers like DOIs for long-term availability. It also emphasizes citable metadata to support reliable knowledge integration. The second stage Provision of Structured Table structures key scientific knowledge in a tabular format using machine-readable formats, e.g., XLSX, enabling preprocessing, computational analysis, and efficient data management. The third stage Openness with Non-Proprietary Format enhances accessibility and reusability by using open, non-proprietary formats, e.g., CSV, promoting interoperability and open science without technical or legal barriers. The fourth stage Semantic Enrichment in KG-Format enriches scientific knowledge with semantics, metadata, and hierarchies in machine-interpretable formats, e.g., JSON-LD, improving interpretability, linking, and contextualization for better integration in KGs. The fifth stage Integration in KG integrates scientific knowledge into KGs using 4 L. John et al.

machine-actionable formats, e.g., RDF or OWL, enabling dynamic exploration, comparability, and interoperability across ecosystems to support advanced data analysis and interdisciplinary collaboration.

#### 3.2 Exemplary Workflow

The workflow combines two established services ORKG Ask [\[1\]](#page-7-7) and ORKG [\[18\]](#page-7-4) to demonstrate the transition from unstructured scientific knowledge to semantic representations in a KG. As shown in Fig. [2,](#page-3-0) the activity diagram maps each step to a model stage, including human or machine involvement and service usage.

<span id="page-3-0"></span>![](_page_3_Figure_4.jpeg)

Fig. 2: Exemplary workflow demonstrating the implementation of the evolution model. The red box outlines the application context of the hybrid approach.

ORKG Ask answers natural language queries by retrieving relevant publications (Stage 1), extracting key knowledge, and generating a synthesized answer and comparison table (Stage 2), which users can refine and export as CSV (Stage 3). ORKG allows CSV import (Stage 3), applies automated data modeling to create initial semantic structures (Stage 4), and enables users to manually edit and publish the final comparison table (Stage 5). Though based on ORKG Ask and ORKG, the workflow is service-agnostic, tools like [Elicit](https://elicit.com/) or [Wikidata](https://www.wikidata.org) could be used instead. This workflow does not only show that the evolution model is feasible with current tools but also highlights key limitations, such as the strict separation of human and machine contributions. As Liu et al. [\[15\]](#page-7-14) emphasize, modern UIs are crucial for enhancing human-machine collaboration. To address this issue, we introduce SciMantify, a hybrid approach integrated into ORKG that supports collaborative semantification, particularly in the critical stages three to five (cf. Fig. [2,](#page-3-0) red box), where current support is lacking.

### 3.3 Hybrid Approach: SciMantify

The core idea of SciMantify is to introduce semantic annotation tasks (SATs) as collaborative efforts between humans and machines. As shown in Fig. [3,](#page-4-0) we define four SATs that improve the automated assignment of predicates and data types during CSV import, and supporting the evolving semantification of scientific knowledge of the uploaded content in the ORKG. Inspired by the SemTab Challenge tasks [\[6\]](#page-7-6), we propose four SATs: CTA, CEA, HCS, and PCG, that enable progressive refinement (see Fig. [4\)](#page-4-1):

CTA (Column Type Annotation) assigns data types and semantic properties to columns. The machine suggests types, e.g., boolean or integer, and

<span id="page-4-0"></span>![](_page_4_Figure_1.jpeg)

Fig. 3: Hybrid approach in context of the exemplary workflow (cf. Fig. [2\)](#page-3-0).

properties; the human reviews and corrects them for contextual accuracy. CEA (Cell Entity Annotation) links cell values to KG entities. The machine suggests matches (including handling multi-value cells by splitting), while the human verifies or refines them to improve alignment and linking.

HCS (Hierarchical Content Structuring) organizes rows into hierarchies by identifying sub-properties (rows) of existing concepts in other rows. The human defines structural relationships, and the machine applies them consistently.

PCG (Property Concept Grouping) promotes reuse by grouping related properties under a new concept. The human creates the grouping, and the machine ensures consistent application across the entire table.

<span id="page-4-1"></span>![](_page_4_Figure_6.jpeg)

Fig. 4: Semantic annotation tasks: CTA, CEA, HCS and PCG.

## 4 Implementation

Given the advanced state of the ORKG, we adopted an agile development approach for integrating SciMantify. The [first release](https://orkg.org/csv-import) focuses on CTA and CEA tasks by embedding human input into existing automated processes. The remaining tasks will follow in the second release.

CTA. The original ORKG CSV import auto-assigned predicates and treated unmatched content as strings, without editing options. Changes required modifying and re-uploading the CSV file. We enhanced this task by enabling users to edit properties and data types directly in the UI with machine support. Predicates are still auto-assigned, but users can revise them. Data types are inferred via majority voting, and inconsistencies are flagged in real-time for resolution.

6 L. John et al.

CEA. The original contribution editor allowed only basic edits. While users could add new cell values (suggested by the machine), aligning existing values with ORKG entities required manual deletion and re-entry, offering no true CEA support. For this reason, we introduced the "Semantify" function: Users can now align existing values with suggested entities or create new ones. Enumerations in a cell can be split and semantically aligned to enhance data integration.

## 5 Evaluation

To assess the hybrid approach proposed in this paper, we conducted a preliminary user experiment focusing on the first release of SciMantify, which integrates humans into automated processes for CTA and CEA. The aim was to explore the approach's effectiveness, efficiency, and user satisfaction in supporting the evolving semantification of scientific knowledge in the ORKG.

Research question: How does the implementation of the hybrid approach (CTA & CEA) support users with prior knowledge of semantic data modeling in terms of effectiveness, efficiency, and satisfaction in the ORKG?

Participants performed the CTA and CEA tasks using a simplified ORKG comparison table [\[16\]](#page-7-17), adapted to emphasize data modeling. Eight participants familiar with the ORKG took part, half of whom regularly used the CSV import.

Subjective feedback indicated that most participants found SciMantify effective and efficient, particularly for CTA and CEA. However, the predicate selection feature received mixed feedback, with some participants overlooking it. Task completion times (see Fig. [5a\)](#page-6-0) averaged 16:38 ± 6:04, [9:15 - 23:44] minutes, with 3:08 ± 1:33, [1:10 - 5:02] for CTA and 13:30 ± 4:41, [7:45 - 19:10] for CEA. The number of reused KG entities (see Fig. [5b\)](#page-6-0) varied, with most participants aligning with or exceeding the original table, except one, who was unfamiliar with the contribution editor. The overall usability (see Fig. [5c\)](#page-6-0) was rated high, with a mean SUS score of 87.5 ± 7.68, [75 - 100], i.e., excellent usability [\[12\]](#page-7-10).

In summary, the experiment showed encouraging initial results for the hybrid approach. However, future larger studies are need to compare SciMantify with a baseline of the original ORKG workflow to quantify improvements.

## 6 Discussion

A more structured and semantic representation of scientific knowledge is essential to advancing the digital transformation of scientific communication. To address this, we proposed an evolution model of knowledge representation, demonstrated through an exemplary workflow and implemented as SciMantify, a hybrid approach supporting human-machine collaboration in the semantification process. Our preliminary user experiment indicates that SciMantify effectively supports the transformation of scientific content from tabular formats to semantic representations. With an average completion time of 17 minutes (3 for CTA, 14

<span id="page-6-0"></span>![](_page_6_Figure_1.jpeg)

(a) Times for CTA task, CEA task, and in total. (b) Ratio of entities used and 32 entities of the original comparison table. (c) SUS scores for SciMantify.

Fig. 5: Objective assessment of effectiveness, efficiency, and satisfaction.

for CEA), results show efficient preprocessing and highlight the need for human input in refining machine-suggested entity alignments. The high usability score (SUS 87.5) confirms the system's user-friendliness and overall satisfaction. The integration of CTA and CEA tasks proved essential, though feedback also pointed to areas for improvement. In particular, predicate selection was often overlooked, suggesting the need for better UI guidance. Additionally, variability in CEA task times indicates that users would benefit from more structured support when aligning entities, especially in complex contexts. Several participants also expressed the need for hierarchical structuring and grouping, aligning with our planned integration of HCS and PCG in the next release of SciMantify. While results are promising, the evaluation has limitations. The study included only eight participants, and the scenario was based on a simplified, fictitious example. Broader studies using real-world data and a baseline comparison are needed to validate the findings. Furthermore, only CTA and CEA tasks were implemented so far. The full potential of the hybrid approach will be assessed after integrating HCS and PCG in the upcoming release.

## 7 Conclusion and Future Work

The proposed evolution model for knowledge representation offers a structured approach to transforming static, unstructured knowledge into flexible, semantic formats. Based on the exemplary workflow that demonstrates the implementation of the evolution model, we developed SciMantify, a hybrid approach combining human expertise with machine automation to evolve the representation of scientific knowledge from tabular formats to semantic representations in a KG. A preliminary experiment within the ORKG context showed high usability and positive feedback, highlighting SciMantify's ability to reduce preprocessing and semantification efforts. Future work includes implementing the remaining semantic annotation tasks HCS and PCG, and adding AI-driven suggestions to better support complex content. We plan a broader user study to assess performance across research domains and compare it to a baseline workflow to increase gen8 L. John et al.

eralizability. Overall, the evolution model and SciMantify represent a key step toward more accessible, reusable, and interoperable scientific knowledge.

## References

- <span id="page-7-7"></span>1. Auer, S., et al.: Open Research Knowledge Graph: A Large-Scale Neuro-Symbolic Knowledge Organization System. In: Handbook on Neurosymbolic AI and Knowledge Graphs. IOS Press (2025)
- <span id="page-7-1"></span>2. Bless, C., Baimuratov, I., Karras, O.: SciKGTeX - A LATEX Package to Semantically Annotate Contributions in Scientific Publications. In: ACM/IEEE Joint Conference on Digital Libraries (2023)
- <span id="page-7-16"></span>3. Cremaschi, M., et al.: Survey on Semantic Interpretation of Tabular Data: Challenges and Directions. arXiv Preprint arXiv.2411.11891 (2024)
- <span id="page-7-8"></span>4. Dorodnykh, N., Yurin, A.: Knowledge Graph Engineering Based on Semantic Annotation of Tables. Computation 11 (2023)
- <span id="page-7-13"></span>5. Dorodnykh, N.O., Shigarov, A.O., Yurevich Yurin, A.: Using the Semantic Annotation of Web Table Data for Knowledge Base Construction. In: 4th Artificial Intelligence and Cloud Computing Conference (2022)
- <span id="page-7-6"></span>6. Hassanzadeh, O., Abdelmageed, N., Cremaschi, M., Cutrona, V., et al.: Results of SemTab 2024. In: CEUR Workshop Proceedings (2024)
- <span id="page-7-15"></span>7. Huynh, V.P., Liu, J., Chabot, Y., Deuzé, F., et al.: DAGOBAH: Table and Graph Contexts for Efficient Semantic Annotation of Tabular Data. In: 20th International Semantic Web Conference (2021)
- <span id="page-7-0"></span>8. Johnson, R., Watkinson, A., Mabe, M.: The STM Report: An Overview of Scientific and Scholarly Publishing (2018)
- <span id="page-7-9"></span>9. Karras, O., Budde, L., Merkel, P., Hermsdorf, J., et al.: Organizing Scientific Knowledge from Engineering Sciences Using the Open Research Knowledge Graph: The Tailored Forming Process Chain Use Case. Data Science Journal (2024)
- <span id="page-7-3"></span>10. Karras, O., Wernlein, F., Klünder, J., Auer, S.: Divide and Conquer the EmpiRE: A Community-Maintainable Knowledge Graph of Empirical Research in Requirements Engineering. In: ACM/IEEE International Symposium on Empirical Software Engineering and Measurement (2023)
- <span id="page-7-2"></span>11. Karras, O., et al.: Researcher or Crowd Member? Why not Both! The Open Research Knowledge Graph for Applying and Communicating CrowdRE Research. In: 29th International Requirements Engineering Conference Workshops. IEEE (2021)
- <span id="page-7-10"></span>12. Lewis, J.R., Sauro, J.: Item Benchmarks for the System Usability Scale. Journal of Usability Studies 13(3) (2018)
- <span id="page-7-12"></span>13. Li, X., Liu, L., Wang, X., Li, Y., et al.: Towards Evolutionary Knowledge Representation under the Big Data Circumstance. The Electronic Library (2021)
- <span id="page-7-11"></span>14. Liang, Z., Liu, F., Mao, J., Lu, K.: A Knowledge Representation Model for Studying Knowledge Creation, Usage, and Evolution. Diversity, Divergence, Dialogue (2021)
- <span id="page-7-14"></span>15. Liu, J., et al.: From Tabular Data to Knowledge Graphs: A Survey of Semantic Table Interpretation Tasks and Methods. Journal of Web Semantics (2023)
- <span id="page-7-17"></span>16. Lozynska, Olga: Deep Learning Methods for Fake News Detection. Open Research Knowledge Graph (2024), <https://doi.org/10.48366/R739984>
- <span id="page-7-5"></span>17. Stocker, M., et al.: SKG4EOSC - Scholarly Knowledge Graphs for EOSC: Establishing a Backbone of Knowledge Graphs for FAIR Scholarly Information in EOSC. Research Ideas and Outcomes 8 (2022)
- <span id="page-7-4"></span>18. Stocker, M., et al.: FAIR Scientific Information with the Open Research Knowledge Graph. FAIR Connect 1(1) (2023)