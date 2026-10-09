# DocILE Benchmark for Document Information Localization and Extraction

Štěpán Šimsa¹©, Milan Šulc¹©, Michal Uřičář¹©, Yash Patel²©, Ahmed Hamdi³©, Matěj Kocián¹©, Matyáš Skalický¹©, Jiří Matas²©, Antoine Doucet³©, Mickaël Coustaty³©, and Dimosthenis Karatzas⁴©

- Rossum.ai, https://rossum.ai, {name.surname}@rossum.ai
- <sup>2</sup> Visual Recognition Group, Czech Technical University in Prague <sup>3</sup> University of La Rochelle, France

**Abstract.** This paper introduces the DocILE benchmark with the largest dataset of business documents for the tasks of Key Information Localization and Extraction and Line Item Recognition. It contains 6.7k annotated business documents, 100k synthetically generated documents, and nearly 1M unlabeled documents for unsupervised pre-training. The dataset has been built with knowledge of domain- and task-specific aspects, resulting in the following key features: (i) annotations in 55 classes, which surpasses the granularity of previously published key information extraction datasets by a large margin; (ii) Line Item Recognition represents a highly practical information extraction task, where key information has to be assigned to items in a table; (iii) documents come from numerous layouts and the test set includes zero- and few-shot cases as well as layouts commonly seen in the training set. The benchmark comes with several baselines, including RoBERTa, LayoutLMv3 and DETRbased Table Transformer; applied to both tasks of the DocILE benchmark, with results shared in this paper, offering a quick starting point for future work. The dataset, baselines and supplementary material are available at https://github.com/rossumai/docile.

**Keywords:** Document AI · Information Extraction · Line Item Recognition · Business Documents · Intelligent Document Processing

#### 1 Introduction

Automating information extraction from business documents has the potential to streamline repetitive human labour and allow data entry workers to focus on more strategic tasks. Despite the recent shift towards business digitalization, the majority of Business-to-Business (B2B) communication still happens through the interchange of semi-structured business documents such as invoices, tax forms, orders, etc. The layouts of these documents were designed for human

<sup>&</sup>lt;sup>4</sup> Computer Vision Center, Universitat Autónoma de Barcelona, Spain

<span id="page-0-0"></span><sup>&</sup>lt;sup>1</sup> We use the term *semi-structured documents* as [62,69]; visual structure is strongly related to the document semantics, but the layout is variable.

readability, yet the downstream applications (i.e. accounting software) depend on data in a structured, computer-readable format. Traditionally, this has been solved by manual data entry, requiring substantial time to process each document. The automated process of data extraction from such documents goes far beyond Optical Character Recognition (OCR) as it requires understanding of semantics, layout and context of the information within the document. The machine learning field dealing with this is called Document Information Extraction (IE), a sub-category of Document Understanding (DU).

Information Extraction from business documents lacks practical large-scale benchmarks, as noted in [\[11,](#page-15-0)[35,](#page-16-0)[56,](#page-17-0)[69,](#page-18-1)[75\]](#page-18-2). While there are several public datasets for document understanding, as reviewed in Section [2.2,](#page-2-0) only a few of them focus on information extraction from business documents. They are typically smallscale [\[49,](#page-17-1) [74,](#page-18-3) [79\]](#page-18-4), focusing solely on receipts [\[58,](#page-17-2) [74\]](#page-18-3), or limit the task, e.g., to Named Entity Recognition (NER), missing location annotation [\[5,](#page-15-1) [29,](#page-16-1) [72,](#page-18-5) [73\]](#page-18-6). Many results in the field are therefore published on private datasets [\[9,](#page-15-2) [21,](#page-16-2) [26,](#page-16-3) [33,](#page-16-4) [56\]](#page-17-0), limiting the reproducibility and hindering further research. Digital semistructured documents often contain sensitive information, such as names and addresses, which hampers the creation of sufficiently-large public datasets and benchmarks.

The standard problem of Key Information Extraction (KIE) should be distinguished [\[69\]](#page-18-1) from Key Information Localization and Extraction (KILE) as the former lacks the positional information, required for effective human-in-the loop verification of the extracted data.

Business documents often come with a list of items, e.g. a table of invoiced goods and services, where each item is represented by a set of key information, such as name, quantity and price. Extraction of such items is the target of the Line Item Recognition (LIR) [\[69\]](#page-18-1), which was not explicitly targeted by existing benchmarks.

In this work, we present the DocILE (Document Information Localization and Extraction) dataset and benchmark with the following contributions:

(i) the largest dataset for KILE and LIR from semi-structured business documents both in terms of the number of labeled documents and categories; (ii) rich set of document layouts, including layout cluster annotations for all labeled documents; (iii) the synthetic subset being the first large synthetic dataset with KILE and LIR labels; (iv) detailed information about the document selection, processing and annotations, which took around 2, 500 hours of annotation time; (v) baseline evaluations of popular architectures for language modelling, visually-rich document understanding and computer vision; (vi) is used both for a research competition, as well as a long-term benchmark of key information extraction and localization, and line item recognition systems; (vii) can serve other areas of research thanks to the rich annotations (table structure, layout clusters, metadata, and the HTML sources for synthetic documents).

The paper is structured as follows: Section [2](#page-2-1) reviews the related work. The DocILE dataset is introduced and its characteristics and its collection are described in Section [3.](#page-5-0) Section [4](#page-9-0) follows with the tasks and evaluation metrics. Baseline methods are described and experimented in Section [5.](#page-11-0) Finally, conclusions are drawn in Section [6.](#page-14-0)

# <span id="page-2-1"></span>2 Related Work

To address the related work, we first introduce general approaches to document understanding, before specifically focusing on information extraction tasks and existing datasets.

## 2.1 Methods for Document Understanding

Approaches to document understanding have used various combinations of input modalities (text, spatial layout, image) to extract information from structurally rich documents. Such approaches have been successfully applied to understanding of forms [\[8,](#page-15-3) [22,](#page-16-5) [90\]](#page-19-0), receipts [\[27,](#page-16-6) [29\]](#page-16-1), tables [\[24,](#page-16-7) [64,](#page-18-7) [89\]](#page-19-1), or invoices [\[45,](#page-17-3) [46,](#page-17-4) [62\]](#page-18-0).

Convolutional neural networks based approaches such as [\[33,](#page-16-4) [42\]](#page-17-5) use character or word vector-based representations to make a grid-style prediction similar to semantic segmentation. The pixels are classified into the field types for invoice documents. LayoutLM [\[84\]](#page-19-2) modifies the BERT [\[10\]](#page-15-4) language model to incorporate document layout information and visual features. The layout information is passed in the form of 2D spatial coordinate embeddings, and the visual features for each word token are obtained via Faster-RCNN [\[61\]](#page-18-8). LayoutLMv2 [\[83\]](#page-19-3) treats visual tokens separately, instead of adding them to the text tokens, and incorporates additional pre-training tasks. LayoutLMv3 [\[28\]](#page-16-8) introduces more pre-training tasks such as masked image modeling, or word-patch alignment. BROS [\[27\]](#page-16-6) also uses a BERT-based text encoder equipped with SPADE [\[30\]](#page-16-9) based graph classifier to predict the entity relations between the text tokens. Document understanding has also been approached from a question-answering perspective [\[47,](#page-17-6) [48\]](#page-17-7). Layout-T5 [\[76\]](#page-18-9) uses the layout information with the generative T5 [\[60\]](#page-17-8) language model, and TILT [\[59\]](#page-17-9) uses convolutional features with the T5 model. In UDOP [\[77\]](#page-18-10), several document understanding tasks are formulated as sequence-to-sequence modelling in a unified framework. Recently, GraphDoc [\[86\]](#page-19-4), a model based on graph attention networks pre-trained only on 320k documents, has been introduced for document understanding tasks, showing satisfactory results.

Transformer-based approaches typically rely on large-scale pre-training on unlabeled documents while the fine-tuning of a specific downstream task is sufficient with much smaller annotated datasets. Noticeable amount of papers have focused on the pre-training aspect of document understanding [\[1,](#page-15-5) [15,](#page-15-6) [17,](#page-15-7) [18,](#page-15-8) [27,](#page-16-6) [36,](#page-16-10) [38,](#page-16-11) [40,](#page-17-10) [59\]](#page-17-9). In this paper we use the popular methods [\[7,](#page-15-9) [28,](#page-16-8) [44\]](#page-17-11) to provide the baselines for KILE and LIR on the proposed DocILE dataset.

# <span id="page-2-0"></span>2.2 Information Extraction Tasks and Datasets

Extraction of information from documents includes many tasks and problems from basic OCR [\[13,](#page-15-10)[20,](#page-16-12)[31,](#page-16-13)[50,](#page-17-12)[54,](#page-17-13)[70\]](#page-18-11) up to visual question answering (VQA) [\[47,](#page-17-6)

| documents.       |              |         |           |          |       |       |                            |
|------------------|--------------|---------|-----------|----------|-------|-------|----------------------------|
| name             | document     | # docs  | classes   | source   | multi | lang. | task                       |
|                  | type         | labeled |           |          | page  |       |                            |
| DocILE (ours)    | invoice-like | 106680  | 55        | digital, | yes   | en    | KILE,                      |
|                  |              |         |           | scan     |       |       | LIR                        |
| CORD [58]        | receipts     | 11000   | $30-42^2$ | photo    | no    | id    | ≈KILE,                     |
|                  |              |         |           |          |       |       | $\approx$ LIR <sup>3</sup> |
| WildReceipt [74] | receipts     | 1740    | 25        | photo    | no    | en    | KILE                       |
| EPHOIE [79]      | chinese      | 1494    | 10        | scan     | no    | zh    | KILE                       |
|                  | forms        |         |           |          |       |       |                            |
| Ghega [49]       | patents,     | 246     | 11/8      | scan     | yes   | en    | KILE                       |
|                  | datasheets   |         |           |          |       |       |                            |

<span id="page-3-2"></span>Table 1: Datasets with KILE and LIR annotations for semi-structured business documents.

48]. The landscape of IE problems and datasets was recently reviewed by Borchmann et al. [5], building the DUE Benchmark for a wide range of document understanding tasks, and by Skalický et al. [69], who argue that the crucial problems for automating B2B document communication are Key Information Localization and Extraction and Line Item Recognition.

**Key Information Extraction** (KIE) [15,29,72] aims to extract pre-defined key information (categories of "fields" – name, email, the amount due, etc.) from a document. A number of datasets for KIE are publicly available [29,49,72,73,74,74,79]. However, as noted by [69], most of them are relatively small and contain only a few annotated field categories.

Key Information Localization and Extraction (KILE) [69] additionally requires precise localization of the extracted information in the input image or PDF, which is crucial for human-in-the-loop interactions, auditing, and other processing of the documents. However, many of the existing KIE datasets miss the localization annotations [5, 29, 72]. Publicly available KILE datasets on business documents [49, 58, 74, 79] and their sizes are listed in Table 1. Due to the lack of large-scale datasets for KILE from business documents, noted by several authors [11, 35, 56, 69, 75], many research publications use private datasets [9, 26, 33, 43, 55, 56, 65, 87].

Line Item Recognition (LIR) [69] is a part of table extraction [3,9,25,46,56] that aims at finding Line Items (LI), localizing and extracting key information for each item. The task is related to Table Structure Recognition [64,71,78], which typically aims at detecting table rows, columns and cells. However, sole table structure recognition is not sufficient for LIR: an enumerated item may span

<span id="page-3-0"></span><sup>&</sup>lt;sup>2</sup> 54 classes mentioned in [58], but the repository https://github.com/clovaai/cord only considers 30 out of 42 listed classes, as of January 2023.

<span id="page-3-1"></span><sup>&</sup>lt;sup>3</sup> COORD annotations contain classification of word tokens (as in NER) but with the additional information which tokens are grouped together into fields or menu items, effectively upgrading the annotations to KILE/LIR field annotations.

<span id="page-4-0"></span>![](_page_4_Figure_2.jpeg)

Fig. 1: DocILE: a document with KILE and LIR annotations (left) and the Line Item areas emphasized (right) by alternating blue and green for odd and even items, respectively. Bottom: color legend for the KILE and LIR classes.

several rows in a table; and columns are often not sufficient to distinguish all semantic information. There are several datasets [\[14,](#page-15-12) [52,](#page-17-16) [66,](#page-18-15) [71,](#page-18-13) [88,](#page-19-6) [89\]](#page-19-1) for Table Detection and/or Structure Recognition, PubTables-1M [\[71\]](#page-18-13) being the largest with a million tables from scientific articles. The domain of scientific articles is prevailing among the datasets [\[14,](#page-15-12) [66,](#page-18-15) [71,](#page-18-13) [89\]](#page-19-1), due to easily obtainable annotations from the LATEX source codes. However, there is a non-trivial domain shift introduced by the difference in the Tables from scientific papers and business documents. FinTabNet [\[88\]](#page-19-6) and SynthTabNet [\[52\]](#page-17-16) are closer to our domain, covering table structure recognition of complex financial tables. These datasets, however, only contain annotations of the table grid/cells. From the available datasets, CORD [\[58\]](#page-17-2) is the closest to the task of Line Item Recognition with its annotation of sub-menu items. The documents in CORD are all receipts, which generally have simpler structure than other typical business documents, which makes the task too simple as previously mentioned in [\[5\]](#page-15-1).

Named Entity Recognition (NER) [\[39\]](#page-16-15) is the task of assigning one of the pre-defined categories to entities (usually words or word-pieces in the document) which makes it strongly related to KILE and LIR, especially when these entities have a known location. Note that the task of NER is less general as it only operates on word/token level, and using it to solve KILE is not straightforward, as the classified tokens have to be correctly aggregated into fields and fields do not necessarily have to contain whole word-tokens.

# <span id="page-5-0"></span>3 The DocILE Dataset

In this section, we describe the DocILE dataset content and creation.

## 3.1 The Annotated, the Unlabeled, and the Synthetic

The DocILE dataset and benchmark is composed of three subsets:

- 1. an annotated set of 6, 680 real business documents from publicly available sources which were annotated as described in Section [3.3.](#page-6-0)
- 2. an unlabeled set of 932k real business documents from publicly available sources, which can be used for unsupervised (pre-)training.
- 3. a synthetic set of 100k documents with full task labels generated with a proprietary document generator using layouts inspired by 100 fully annotated real business documents from the annotated set.

The labeled (i.e., annotated and synthetic) subsets contain annotations for the tasks of Key Information Localization and Extraction and Line Item Recognition, described below in Sections [4.1](#page-9-1) and [4.2,](#page-10-0) respectively. An example document with such annotations is shown in Figure [1.](#page-4-0) Table [2](#page-5-1) shows the size of the dataset.

## 3.2 Data Sources

Documents in the DocILE dataset come from two public data sources: UCSF Industry Documents Library [\[80\]](#page-18-16) and Public Inspection Files (PIF) [\[82\]](#page-19-7). The UCSF Industry Documents Library contains documents from industries that influence public health, such as tobacco companies. This source has been used to create the following document datasets: RVL-CDIP [\[23\]](#page-16-16), IIT-CDIP [\[37\]](#page-16-17), FUNSD [\[32\]](#page-16-18), DocVQA [\[48\]](#page-17-7) and OCR-IDL [\[4\]](#page-15-13). PIF contains a variety of information about American broadcast stations. We specifically use the "political files" with documents (invoices, orders, "contracts") from TV and radio stations for political campaign ads, previously used to create the Deepform [\[73\]](#page-18-6). Documents from both sources were retrieved in the PDF format.

Table 2: DocILE dataset — the three subsets.

<span id="page-5-1"></span>

|                 | annotated | synthetic | unlabeled |
|-----------------|-----------|-----------|-----------|
| documents       | 6 680     | 100 000   | 932 467   |
| pages           | 8 715     | 100 000   | 3.4M      |
| layout clusters | 1 152     | 100       | Unknown   |
| pages per doc.  | 1–3       | 1         | 1–884     |

Documents for DocILE were selected from the two sources as follows. For UCSF IDL, we used the public API [81] to retrieve only publicly available documents of type invoice. For documents from PIF, we retrieved all "political files" from tv, fm and am broadcasts. We discarded documents with broken PDFs, duplicates<sup>4</sup>, and documents not classified as *invoice-like*<sup>5</sup>. Other types of documents, such as budgets or financial reports, were discarded as they typically contain different key information. We refer to the selected documents from the two sources as *PIF* and *UCSF* documents.

#### <span id="page-6-0"></span>3.3 Document Selection and Annotation

To capture a rich distribution of documents and make the dataset easy to work with, expensive manual annotations were only done for documents which are:

- 1. short (1-3 pages), to annotate many different documents rather than a few long ones:
- 2. written in English, for consistency and because the language distribution in the selected data sources is insufficient to consider multilingual analysis:
- 3. dated<sup>6</sup> 1999 or later in *UCSF*, as older documents differ from the more recent ones (typewritten, etc.);
- 4. representing a rich distribution of layout clusters, as shown in Figure 3.

We clustered the document layouts<sup>7</sup> based on the location of fields detected by a proprietary model for KILE.

<span id="page-6-4"></span>We loosely define layout as the positioning of fields of each type in a document. We allow, e.g., different length of values, missing values, and resulting translations of whole sections.

![](_page_6_Figure_14.jpeg)

Fig. 2: Distribution of the number of document pages in the training, validation and unlabeled sets. The numbers of documents are displayed above the bars.

<span id="page-6-1"></span><sup>&</sup>lt;sup>4</sup> Using hash of page images to capture duplicates differing only in PDF metadata.

<span id="page-6-2"></span><sup>&</sup>lt;sup>5</sup> Invoice-like documents are tax invoice, order, purchase order, receipt, sales order, proforma invoice, credit note, utility bill and debit note. We used a proprietary document-type classifier provided by Rossum.ai.

<span id="page-6-3"></span><sup>&</sup>lt;sup>6</sup> The document date was retrieved from the UCSF IDL metadata. Note that the majority of the documents in this source are from the 20th century.

<span id="page-7-0"></span>![](_page_7_Figure_2.jpeg)

Fig. 3: The number of documents of each layout cluster in the training, validation and unlabeled sets, on a logarithmic scale. While some clusters have up to 100k documents, the largest cluster in train. + val. contains only 90 documents.

The clustering was manually corrected for the annotated set. More details about the clustering can be found in the Supplementary Material.

In the annotation process, documents were skipped if they were not *invoice-like*, if they contained handwritten or redacted key information or if they listed more than one set of line items (e.g. several tables listing unrelated types of items).

Additionally, PDF files composed of several documents (e.g., a different invoice on each page) were split and annotated separately.

For KILE and LIR, fields are annotated as a triplet of location (bounding box and page), field type (class) and text. LIR fields additionally contain the line item ID, assigning the line item they belong to. If the same content is listed in several tables with different granularity (but summing to the same total amount), the less detailed set of line items is annotated.

Notice that the fields can overlap, sometimes completely. A field can be multiline or contain only parts of words. There can be multiple fields with the same field type on the same page, either having the same value in multiple locations or even having different values as well as multiple fields with the same field type in the same line item. The full list of field types and their description are in the Supplementary Material.

Additional annotations, not necessary for the benchmark evaluation, are available and can be used in the training or for other research purposes. Table structure annotations include: 1) line item headers, representing the headers of columns corresponding to one field type in the table, and 2) the table grid, containing information about rows, their position and classification into header, data, gap, etc., and columns, their position and field type when the values in the column correspond to this field type. Additionally, metadata contain: docu-

ment type, currency, layout cluster ID, source and original filename (linking the document to the source), page count and page image sizes.

Annotating the 6, 680 documents took approx. 2, 500 hours of annotators' time including the verification. Of the annotated documents, 53.7% originate from PIF and the remaining 46.3% from UCSF IDL. The annotated documents underwent the image pre-processing described in the Supplementary Material. All remaining documents from PIF and UCSF form the unlabeled set.

#### <span id="page-8-3"></span>3.4 Dataset Splits

The annotated documents in the DocILE dataset are split into training (5, 180), validation (500), and test (1, 000) sets. The synthetic set with 100k documents and unlabeled set with 932k documents are provided as an optional extension to the training set, as unsupervised pre-training [\[85\]](#page-19-8) and synthetic training data [\[6,](#page-15-14) [12,](#page-15-15) [19,](#page-16-19) [52,](#page-17-16) [53\]](#page-17-17) have been demonstrated to improve results of machine learning models in different domains.

The training, validation and test splitting was done so that the validation and test sets contain 25% of zero-shot samples (from layouts unseen during training[8](#page-8-0) ), 25% of few-shot samples (from layouts with ≤ 3 documents seen during training) and 50% of many-shot samples (from layouts with more examples seen during training). This allows to measure both the generalization of the evaluated methods and the advantage of observing documents of known layouts.

The test set annotations are not public and the test set predictions will be evaluated through the RRC website[9](#page-8-1) , where the benchmark and competition is hosted. The validation set can be used when access to annotations and metadata is needed for experiments in different tasks.

As inputs to the document synthesis described in Section [3.5,](#page-8-2) 100 one-page documents were chosen from the training set, each from a different layout cluster. In the test, resp. validation sets, roughly half of the few-shot samples are from layouts for which synthetic documents were generated. There are no synthetic documents generated for zero-shot samples. For many-shot samples, 35 − 40% of documents are from layouts with synthetic documents.

#### <span id="page-8-2"></span>3.5 Synthetic Documents Generation

To generate synthetic documents with realistic appearance and content, we used the following procedure: First, a set of template documents from different layout clusters was selected, as described in Section [3.4.](#page-8-3) All elements in the selected documents, including all present keys and values, notes, sections, borders, etc., were annotated with layout (bounding box), semantic (category) and text

<span id="page-8-0"></span><sup>8</sup> For the test set, documents in both training and validation sets are considered as seen during training. Note that some test set layouts may be present in the validation set, not the training set.

<span id="page-8-1"></span><sup>9</sup> <https://rrc.cvc.uab.es/>

(where applicable) annotations. Such full annotations were the input to a rulebased document synthesizer, which uses a rich set of content generators[10](#page-9-2) to fill semantically relevant information in the annotated areas. Additionally, a style generator controls and enriches the look of the resulting documents (via font family and size, border styles, shifts of the document contents, etc.). The documents are first generated as HTML files and then rendered to PDF. The HTML source code of all generated documents is shared with the dataset and can be used for future work, e.g., for generative methods for conversion of document images into a markup language.

#### 3.6 Format

The dataset is shared in the form of pre-processed[11](#page-9-3) document PDFs with task annotations in JSON. Additionally, each document comes with DocTR [\[51\]](#page-17-18) OCR predictions with word-level text and location[12](#page-9-4) .

A python library docile[13](#page-9-5) is provided to ease the work with the dataset.

# <span id="page-9-0"></span>4 Benchmark Tasks and Evaluation Metrics

Sections [4.1](#page-9-1) and [4.2](#page-10-0) describe the two benchmark tasks as introduced in the teaser [\[67\]](#page-18-18) along with the challenge evaluation metrics used for the leaderboard ranking. Additional evaluation metrics are described in the Supplementary Material.

#### <span id="page-9-1"></span>4.1 Track 1: Key Information Localization and Extraction

The goal of the first track is to localize key information of pre-defined categories (field types) in the document. It is derived from the task of Key Information Localization and Extraction, as defined in [\[69\]](#page-18-1) and motivated in Section [2.2.](#page-2-0)

We focus the challenge on detecting semantically important values corresponding to tens of different field types rather than fine-tuning the underlying text recognition. Towards this focus, we provide word-level text detections for each document, we choose an evaluation metric (below) that does not pay attention to the text recognition part, and we simplify the task in the challenge by only requiring correct localization of the values in the documents in the primary metric. Text extractions are checked, besides the locations and field types, in a separate evaluation — the leaderboard ranking does not depend on it. Any post-processing of values — deduplication, converting dates to a standardized

<span id="page-9-2"></span><sup>10</sup> Such as generators of names, emails, addresses, bank account numbers, etc. Some utilize the Mimesis library [\[16\]](#page-15-16). Some content, such as keys, is copied from the annotated document.

<span id="page-9-3"></span><sup>11</sup> Pre-processing consists of correcting page orientation, de-skewing scanned documents and normalizing them to 150 DPI.

<span id="page-9-4"></span><sup>12</sup> Axis-aligned bounding boxes, optionally with additional snapping to reduce white space around word predictions, described in the Supplementary Material.

<span id="page-9-5"></span><sup>13</sup> <https://github.com/rossumai/docile>

<span id="page-10-2"></span>![](_page_10_Figure_2.jpeg)

Fig. 4: Each word is split uniformly into pseudo-character boxes based on the number of characters. Pseudo-Character Centers are the centers of these boxes.

<span id="page-10-1"></span>

| Contact Details:        | Contact Details:        |  |  |
|-------------------------|-------------------------|--|--|
| Phone: +420 233 232 344 | Phone: +420 233 232 344 |  |  |
| E–mail: bob@website.com | E–mail: bob@website.com |  |  |

(a) Correct extraction examples.

(b) Incorrect extraction examples.

Fig. 5: Visualization of correct and incorrect bounding box predictions to capture the phone number. Bounding box must include exactly the Pseudo-Character Centers that lie within the ground truth annotation. Note: in [5a,](#page-10-1) only one of the predictions would be considered correct if all three boxes were predicted.

format etc., despite being needed in practice, is not performed. With the simplifications, the main task can also be viewed as a detection problem. Note that when several instances of the same field type are present, all of them should be detected.

The Challenge Evaluation Metric. Since the task is framed as a detection problem, the standard Average Precision metric is used as the main evaluation metric. Unlike the common practice in object detection, where true positives are determined by thresholding the Intersection-over-Union, we use a different criterion tailored to evaluate the usefulness of detections for text read-out. Inspired by the CLEval metric [\[2\]](#page-15-17) used in text detection, we measure whether the predicted area contains nothing but the related character centers. Since character-level annotations are hard to obtain, we use CLEval definition of Pseudo-Character Center (PCC), visualized in Figure [4.](#page-10-2) Examples of correct and incorrect detections are depicted in Figure [5.](#page-10-1)

#### <span id="page-10-0"></span>4.2 Track 2: Line Item Recognition

The goal of the second track is to localize key information of pre-defined categories (field types) and group it into line items [\[3,](#page-15-11) [9,](#page-15-2) [25,](#page-16-14) [46,](#page-17-4) [56\]](#page-17-0). A Line Item (LI) is a tuple of fields (e.g., description, quantity, and price) describing a single object instance to be extracted, e.g., a row in a table, as visualized in Figure [1](#page-4-0) and explained in Section [2.2.](#page-2-0)

The Challenge Evaluation Metric. The main evaluation metric is the micro F1 score over all line item fields. A predicted line item field is correct if it fulfills the requirements from Track 1 (on field type and location) and if it is assigned to the correct line item. Since the matching of ground truth (GT) and predicted line items may not be straightforward due to errors in the prediction, our evaluation metric chooses the best matching in two steps:

- 1. for each pair of predicted and GT line items, the predicted fields are evaluated as in Track 1,
- 2. the maximum matching is found between predicted and GT line items, maximizing the overall recall.

#### 4.3 Benchmark Dataset Rules

The use of external document datasets (and models pre-trained on such datasets) is prohibited in the benchmark in order to focus on clear comparative evaluation of methods that use the provided collection of labeled and unlabeled documents. Usage of datasets and pre-trained models from other domains, such as images from ImageNet [\[63\]](#page-18-19) or texts from BooksCorpus [\[91\]](#page-19-9), is allowed.

# <span id="page-11-0"></span>5 Baseline Methods

We provide as baselines several popular state-of-the-art transformer architectures, covering text-only (RoBERTa), image-only (DETR) and multi-modal (LayoutLMv3) document representations. The code and model checkpoints for all baseline methods are distributed with the dataset.

## <span id="page-11-1"></span>5.1 Multi-label NER Formulation for KILE & LIR Tasks

The baselines described in Sections [5.2](#page-12-0) and [5.3](#page-12-1) use a joint multi-label NER formulation for both KILE and LIR tasks. The LIR task requires not only to correctly classify tokens into one of the LIR classes, but also the assignment of tokens to individual Line Items. For this purpose, we add classes <B-LI>, <I-LI>, <O-LI> and <E-LI>, representing the beginning of the line item, inside and outside tokens and end token of the line item. We found it is crucial to re-order the OCR tokens in top-down, left-to-right order for each predicted text line of the document. We provide a detailed description of the OCR tokens reordering in the Supplementary Material. For the LIR and KILE classification, we use the standard BIO tagging scheme. We use the binary cross entropy loss to train the model.

The final KILE and LIR predictions are formed by the merging strategy as follows. We group the predicted tokens based on the membership to the predicted line item (note that we can assign the tokens which do not belong to any line item to a special group ∅), then we use the predicted OCR text lines to perform the horizontal merging of tokens assigned to the same class. Next, we construct a graph from the horizontally merged text blocks, based on the thresholded x and y distances of the text block pairs (as a threshold we use the height of the text block with a 25% margin). The final predictions are given by merging the graph components. By merging, we mean taking the union of the individual bounding boxes of tokens/text blocks and for the text value, if the horizontal merging is applied, we join the text values with space, and with the new line character when vertical merging is applied.

Note that this merging strategy is rather simplistic and its proper redefinition might be of interest for the participants who cannot afford training of big models as we publish also the baselines model checkpoints.

## <span id="page-12-0"></span>5.2 RoBERTa

RoBERTa [\[44\]](#page-17-11) is a modification of the BERT [\[10\]](#page-15-4) model which uses improved training scheme and minor tweaks of the architecture (different tokenizer). It can be used for NER task simply by adding a classification head after the RoBERTa embedding layer. Our first baseline is purely text based and uses RoBERTaBASE as the backbone of the joint multi-label NER model described in Section [5.1.](#page-11-1)

### <span id="page-12-1"></span>5.3 LayoutLMv3

While the RoBERTa-based baseline only operates on the text input, LayoutLMv3 [\[28\]](#page-16-8) is multi-modal transformer architecture that incorporates image, text, and layout information jointly. The images are encoded by splitting into non-overlapping patches and feeding the patches to a linear projection layer, after which they are combined with positional embeddings. The text tokens are combined with one-dimensional and two-dimensional positional embeddings, where the former accounts for the position in the sequence of tokens, and the latter specifies the spatial location of the token in the document. The two-dimensional positional embedding incorporates the layout information. All these tokens are then fed to the transformer model. We use the LayoutLMv3BASE architecture as our second baseline, also using the multi-label NER formulation from Section [5.1.](#page-11-1) Since LayoutLMv3BASE was pre-trained on an external document dataset, prohibited in the benchmark, we pre-train a checkpoint from scratch in Section [5.4.](#page-12-2)

#### <span id="page-12-2"></span>5.4 Pre-training for RoBERTa and LayoutLMv3

We use the standard masked language modeling [\[10\]](#page-15-4) as the unsupervised pretraining objective to pre-train RoBERTaOURS and LayoutLMv3OURS [14](#page-12-3) models. The pre-training is performed from scratch using the 932k unlabeled samples introduced in Section [3.](#page-5-0) Note that the pre-training uses the OCR predictions provided with the dataset (with reading order re-ordering).

Additionally, RoBERTaBASE/OURS+SYNTH and LayoutLMv3OURS+SYNTH baselines use supervised pre-training on the DocILE synthetic data.

<span id="page-12-3"></span><sup>14</sup> Note that LayoutLMv3BASE [\[28\]](#page-16-8) used two additional pre-training objectives, namely masked image modelling and word-patch alignment. Since pre-training code is not publicly available and some of the implementation details are missing, LayoutLMv3OURS used only masked language modelling.

<span id="page-13-1"></span>Table 3: Baseline results for KILE & LIR. LayoutLMv3<sub>BASE</sub>, achieving the best results, was pre-trained on another document dataset – IIT-CDIP [37], which is prohibited in the official benchmark. The best results among permitted models are <u>underlined</u>. The primary metric for each task is shown in **bold**.

|                                             | KILE  |               |       | LIR    |       |       |       |        |
|---------------------------------------------|-------|---------------|-------|--------|-------|-------|-------|--------|
| Model                                       | F1    | $\mathbf{AP}$ | Prec. | Recall | F1    | AP    | Prec. | Recall |
| RoBERTa <sub>BASE</sub>                     | 0.664 | 0.534         | 0.658 | 0.671  | 0.686 | 0.576 | 0.695 | 0.678  |
| $RoBERTa_{OURS}$                            | 0.645 | 0.515         | 0.634 | 0.656  | 0.686 | 0.570 | 0.693 | 0.678  |
| LayoutLMv3 <sub>BASE</sub> (prohibited)     | 0.698 | 0.553         | 0.701 | 0.694  | 0.721 | 0.586 | 0.746 | 0.699  |
| LayoutLMv3 <sub>OURS</sub>                  | 0.639 | 0.507         | 0.636 | 0.641  | 0.661 | 0.531 | 0.682 | 0.641  |
| RoBERTa <sub>BASE+SYNTH</sub>               | 0.664 | 0.539         | 0.659 | 0.669  | 0.698 | 0.583 | 0.710 | 0.687  |
| Roberta <sub>Ours+synth</sub>               | 0.652 | 0.527         | 0.648 | 0.656  | 0.675 | 0.559 | 0.696 | 0.655  |
| LayoutLMv3 <sub>OURS+SYNTH</sub>            | 0.655 | 0.512         | 0.662 | 0.648  | 0.691 | 0.582 | 0.709 | 0.673  |
| NER upper bound                             | 0.946 | 0.897         | 1.000 | 0.897  | 0.961 | 0.926 | 1.000 | 0.926  |
| $DETR^{table} + RoBERTa_{BASE}$             | -     | -             | -     | -      | 0.682 | 0.560 | 0.706 | 0.660  |
| $DETR^{table} + DETR^{LI} + RoBERTa_{BASE}$ | -     | -             | -     | -      | 0.594 | 0.407 | 0.632 | 0.560  |

#### 5.5 Line Item Detection via DETR

As an alternative approach to detecting Line Items, we use the DETR [7] object detector, as proposed for table structure recognition on the PubTables-1M dataset [71]. Since pretraining on other document datasets is prohibited in the DocILE benchmark, we initialize DETR from a checkpoint<sup>15</sup> pretrained on COCO [41], not from [71].

Two types of detectors are fine-tuned independently. DETR<sup>table</sup> for table detection and DETR<sup>LI</sup> for line item detection given a table crop — which in our preliminary experiments lead to better results than one-stage detection of line items from the full page.

#### 5.6 Upper Bound for NER-based Solutions

All our baselines use NER models with the provided OCR on input. This comes with limitations as a field does not have to correspond to a set of word tokens — a field can contain just a part of some word and some words covering the field might be missing in the text detections. A theoretical upper bound for NER-based methods that classify the provided OCR words is included in Table 3. The upper bound constructs a prediction for each ground truth field by finding all words whose PCCs are covered by the field and replacing its bounding box with a union of bounding boxes of these words. Predicted fields that do not match their originating ground truth fields are discarded.

#### 5.7 Results

The baselines described above were evaluated on the DocILE test set, the results are in Table 3. Interestingly, from our pre-trained models (marked <sub>OURS</sub>),

<span id="page-13-0"></span><sup>15</sup> https://huggingface.co/facebook/detr-resnet-50

the RoBERTa baseline outperforms the LayoutLMv3 baseline utilizing the same RoBERTa model in its backbone. We attribute this mainly to differences in the LayoutLMv3 pre-training: 1) our pre-training used only the masked language modelling loss, as explained in Section [5.4,](#page-12-2) 2) we did not perform a full hyperparameter search, and 3) our pre-training performs image augmentations not used in the original LayoutLMv3 pre-training, these are described in the Supplementary Material.

Models pre-trained on the synthetic training data are marked with SYNTH. Synthetic pre-training improved the results for both KILE and LIR in all cases except for LIR with RoBERTaOURS+SYNTH, validating the usefulness of the synthetic subset.

The best results among the models permitted in the benchmark – i.e. not utilizing additional document datasets – were achieved by RoBERTaBASE+SYNTH.

# <span id="page-14-0"></span>6 Conclusions

The DocILE benchmark includes the largest research dataset of business documents labeled with fine-grained targets for the tasks of Key Information Localization and Extraction and Line Item Recognition. The motivation is to provide a practical benchmark for evaluation of information extraction methods in a domain where future advancements can considerably save time that people and businesses spend on document processing. The baselines described and evaluated in Section [5,](#page-11-0) based on state-of-the-art transformer architectures, demonstrate that the benchmark presents very challenging tasks. The code and model checkpoints for the baselines are provided to the research community allowing quick start for the future work.

The benchmark is used for a research competition hosted at ICDAR 2023 and CLEF 2023 and will stay open for post-competition submission for longterm evaluation. We are looking forward to contributions from different machine learning communities to compare solutions inspired by document layout modelling, language modelling and question answering, computer vision, information retrieval, and other approaches.

Areas for future contributions to the benchmark include different training objective statements — such as different variants of NER, object detection, or sequence-to-sequence modelling [\[77\]](#page-18-10), or graph reasoning [\[74\]](#page-18-3); different model architectures, unsupervised pre-training [\[28,](#page-16-8) [77\]](#page-18-10), utilization of table structure e.g., explicitly modelling regularity in table columns to improve in LIR; addressing dataset shifts [\[57,](#page-17-20) [68\]](#page-18-20); or zero-shot learning [\[34\]](#page-16-20).

Acknowledgements We acknowledge the funding and support from Rossum and the intensive work of its annotation team, particularly Petra Hrdliˇckov´a and Kateˇrina Veˇcerkov´a. YP and JM were supported by Research Center for Informatics (project CZ.02.1.01/0.0/0.0/16 019/0000765 funded by OP VVV), by the Grant Agency of the Czech Technical University in Prague, grant No. SGS20/171/OHK3 /3T/13, by Project StratDL in the realm of COMET K1 center Software Competence Center Hagenberg, and Amazon Research Award. DK was supported by grant PID2020-116298GB-I00 funded by MCIN/AE/NextGenerationEU and ELSA (GA 101070617) funded by EU.

# References

- <span id="page-15-5"></span>1. Appalaraju, S., Jasani, B., Kota, B.U., Xie, Y., Manmatha, R.: Docformer: Endto-end transformer for document understanding. In: ICCV (2021)
- <span id="page-15-17"></span>2. Baek, Y., Nam, D., Park, S., Lee, J., Shin, S., Baek, J., Lee, C.Y., Lee, H.: Cleval: Character-level evaluation for text detection and recognition tasks. In: CVPR workshops (2020)
- <span id="page-15-11"></span>3. Bensch, O., Popa, M., Spille, C.: Key information extraction from documents: Evaluation and generator. In: Abb`es, S.B., Hantach, R., Calvez, P., Buscaldi, D., Dess`ı, D., Dragoni, M., Recupero, D.R., Sack, H. (eds.) Proceedings of DeepOntoNLP and X-SENTIMENT (2021)
- <span id="page-15-13"></span>4. Biten, A.F., Tito, R., Gomez, L., Valveny, E., Karatzas, D.: Ocr-idl: Ocr annotations for industry document library dataset. ECCV workshops (2022)
- <span id="page-15-1"></span>5. Borchmann, L., Pietruszka, M., Stanislawek, T., Jurkiewicz, D., Turski, M., Szyndler, K., Grali´nski, F.: DUE: End-to-end document understanding benchmark. In: NeurIPS (2021)
- <span id="page-15-14"></span>6. Buˇsta, M., Patel, Y., Matas, J.: E2E-MLT - an unconstrained end-to-end method for multi-language scene text. In: ACCV workshops (2019)
- <span id="page-15-9"></span>7. Carion, N., Massa, F., Synnaeve, G., Usunier, N., Kirillov, A., Zagoruyko, S.: Endto-end object detection with transformers. In: ECCV (2020)
- <span id="page-15-3"></span>8. Davis, B., Morse, B., Cohen, S., Price, B., Tensmeyer, C.: Deep visual template-free form parsing. In: ICDAR (2019)
- <span id="page-15-2"></span>9. Denk, T.I., Reisswig, C.: Bertgrid: Contextualized embedding for 2d document representation and understanding. arXiv (2019)
- <span id="page-15-4"></span>10. Devlin, J., Chang, M.W., Lee, K., Toutanova, K.: Bert: Pre-training of deep bidirectional transformers for language understanding. arXiv (2018)
- <span id="page-15-0"></span>11. Dhakal, P., Munikar, M., Dahal, B.: One-shot template matching for automatic document data capture. In: Artificial Intelligence for Transforming Business and Society (AITB) (2019)
- <span id="page-15-15"></span>12. Dosovitskiy, A., Fischer, P., Ilg, E., Hausser, P., Hazirbas, C., Golkov, V., Van Der Smagt, P., Cremers, D., Brox, T.: Flownet: Learning optical flow with convolutional networks. In: ICCV (2015)
- <span id="page-15-10"></span>13. Du, Y., Li, C., Guo, R., Yin, X., Liu, W., Zhou, J., Bai, Y., Yu, Z., Yang, Y., Dang, Q., Wang, H.: PP-OCR: A practical ultra lightweight OCR system. arXiv (2020)
- <span id="page-15-12"></span>14. Fang, J., Tao, X., Tang, Z., Qiu, R., Liu, Y.: Dataset, ground-truth and performance metrics for table detection evaluation. In: Blumenstein, M., Pal, U., Uchida, S. (eds.) DAS (2012)
- <span id="page-15-6"></span>15. Garncarek, L., Powalski, R., Stanis lawek, T., Topolski, B., Halama, P., Turski, M., Grali´nski, F.: Lambert: layout-aware language modeling for information extraction. In: ICDAR (2021)
- <span id="page-15-16"></span>16. Geimfari, L.: Mimesis: The fake data generator. [https://github.com/](https://github.com/lk-geimfari/mimesis) [lk-geimfari/mimesis](https://github.com/lk-geimfari/mimesis) (2022)
- <span id="page-15-7"></span>17. Gu, J., Kuen, J., Morariu, V.I., Zhao, H., Jain, R., Barmpalios, N., Nenkova, A., Sun, T.: Unidoc: Unified pretraining framework for document understanding. In: NeurIPS (2021)
- <span id="page-15-8"></span>18. Gu, Z., Meng, C., Wang, K., Lan, J., Wang, W., Gu, M., Zhang, L.: Xylayoutlm: Towards layout-aware multimodal networks for visually-rich document understanding. In: CVPR (2022)

- <span id="page-16-19"></span>19. Gupta, A., Vedaldi, A., Zisserman, A.: Synthetic data for text localisation in natural images. In: CVPR (2016)
- <span id="page-16-12"></span>20. Hamad, K.A., Mehmet, K.: A detailed analysis of optical character recognition technology. International Journal of Applied Mathematics Electronics and Computers (2016)
- <span id="page-16-2"></span>21. Hamdi, A., Carel, E., Joseph, A., Coustaty, M., Doucet, A.: Information extraction from invoices. In: ICDAR (2021)
- <span id="page-16-5"></span>22. Hammami, M., H´eroux, P., Adam, S., d'Andecy, V.P.: One-shot field spotting on colored forms using subgraph isomorphism. In: ICDAR (2015)
- <span id="page-16-16"></span>23. Harley, A.W., Ufkes, A., Derpanis, K.G.: Evaluation of deep convolutional nets for document image classification and retrieval. In: ICDAR (2015)
- <span id="page-16-7"></span>24. Herzig, J., Nowak, P.K., M¨uller, T., Piccinno, F., Eisenschlos, J.M.: Tapas: Weakly supervised table parsing via pre-training. arXiv (2020)
- <span id="page-16-14"></span>25. Holeˇcek, M., Hoskovec, A., Baudiˇs, P., Klinger, P.: Table understanding in structured documents. In: ICDAR workshops (2019)
- <span id="page-16-3"></span>26. Holt, X., Chisholm, A.: Extracting structured data from invoices. In: Proceedings of the Australasian Language Technology Association Workshop 2018. pp. 53–59 (2018)
- <span id="page-16-6"></span>27. Hong, T., Kim, D., Ji, M., Hwang, W., Nam, D., Park, S.: Bros: A pre-trained language model focusing on text and layout for better key information extraction from documents. In: AAAI (2022)
- <span id="page-16-8"></span>28. Huang, Y., Lv, T., Cui, L., Lu, Y., Wei, F.: Layoutlmv3: Pre-training for document ai with unified text and image masking. In: ACM-MM (2022)
- <span id="page-16-1"></span>29. Huang, Z., Chen, K., He, J., Bai, X., Karatzas, D., Lu, S., Jawahar, C.V.: IC-DAR2019 competition on scanned receipt OCR and information extraction. In: ICDAR (2019)
- <span id="page-16-9"></span>30. Hwang, W., Yim, J., Park, S., Yang, S., Seo, M.: Spatial dependency parsing for semi-structured document information extraction. arXiv (2020)
- <span id="page-16-13"></span>31. Islam, N., Islam, Z., Noor, N.: A survey on optical character recognition system. arXiv (2017)
- <span id="page-16-18"></span>32. Jaume, G., Ekenel, H.K., Thiran, J.P.: FUNSD: A dataset for form understanding in noisy scanned documents. In: ICDAR (2019)
- <span id="page-16-4"></span>33. Katti, A.R., Reisswig, C., Guder, C., Brarda, S., Bickel, S., H¨ohne, J., Faddoul, J.B.: Chargrid: Towards understanding 2d documents. In: EMNLP (2018)
- <span id="page-16-20"></span>34. Kil, J., Chao, W.L.: Revisiting document representations for large-scale zero-shot learning. arXiv (2021)
- <span id="page-16-0"></span>35. Krieger, F., Drews, P., Funk, B., Wobbe, T.: Information extraction from invoices: a graph neural network approach for datasets with high layout variety. In: Innovation Through Information Systems: Volume II: A Collection of Latest Research on Technology Issues (2021)
- <span id="page-16-10"></span>36. Lee, C.Y., Li, C.L., Dozat, T., Perot, V., Su, G., Hua, N., Ainslie, J., Wang, R., Fujii, Y., Pfister, T.: Formnet: Structural encoding beyond sequential modeling in form document information extraction. In: ACL (2022)
- <span id="page-16-17"></span>37. Lewis, D., Agam, G., Argamon, S., Frieder, O., Grossman, D., Heard, J.: Building a test collection for complex document information processing. In: SIGIR (2006)
- <span id="page-16-11"></span>38. Li, C., Bi, B., Yan, M., Wang, W., Huang, S., Huang, F., Si, L.: Structurallm: Structural pre-training for form understanding. In: ACL (2021)
- <span id="page-16-15"></span>39. Li, J., Sun, A., Han, J., Li, C.: A survey on deep learning for named entity recognition. IEEE Transactions on Knowledge and Data Engineering (2020)

- <span id="page-17-10"></span>40. Li, Y., Qian, Y., Yu, Y., Qin, X., Zhang, C., Liu, Y., Yao, K., Han, J., Liu, J., Ding, E.: Structext: Structured text understanding with multi-modal transformers. In: ACM-MM (2021)
- <span id="page-17-19"></span>41. Lin, T.Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Doll´ar, P., Zitnick, C.L.: Microsoft coco: Common objects in context. In: ECCV (2014)
- <span id="page-17-5"></span>42. Lin, W., Gao, Q., Sun, L., Zhong, Z., Hu, K., Ren, Q., Huo, Q.: Vibertgrid: a jointly trained multi-modal 2d document representation for key information extraction from documents. In: ICDAR (2021)
- <span id="page-17-14"></span>43. Liu, W., Zhang, Y., Wan, B.: Unstructured document recognition on business invoice. Technical Report (2016)
- <span id="page-17-11"></span>44. Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M., Zettlemoyer, L., Stoyanov, V.: RoBERTa: A Robustly Optimized BERT Pretraining Approach. arXiv (2019)
- <span id="page-17-3"></span>45. Lohani, D., Bela¨ıd, A., Bela¨ıd, Y.: An invoice reading system using a graph convolutional network. In: ACCV workshops (2018)
- <span id="page-17-4"></span>46. Majumder, B.P., Potti, N., Tata, S., Wendt, J.B., Zhao, Q., Najork, M.: Representation learning for information extraction from form-like documents. In: ACL (2020)
- <span id="page-17-6"></span>47. Mathew, M., Bagal, V., Tito, R., Karatzas, D., Valveny, E., Jawahar, C.: InfographicVQA. In: WACV (2022)
- <span id="page-17-7"></span>48. Mathew, M., Karatzas, D., Jawahar, C.: DocVQA: A dataset for vqa on document images. In: WACV (2021)
- <span id="page-17-1"></span>49. Medvet, E., Bartoli, A., Davanzo, G.: A probabilistic approach to printed document understanding. In: ICDAR (2011)
- <span id="page-17-12"></span>50. Memon, J., Sami, M., Khan, R.A., Uddin, M.: Handwritten optical character recognition (ocr): A comprehensive systematic literature review (slr). IEEE Access (2020)
- <span id="page-17-18"></span>51. Mindee: doctr: Document text recognition. <https://github.com/mindee/doctr> (2021)
- <span id="page-17-16"></span>52. Nassar, A., Livathinos, N., Lysak, M., Staar, P.W.J.: Tableformer: Table structure understanding with transformers. arXiv (2022)
- <span id="page-17-17"></span>53. Nayef, N., Patel, Y., Busta, M., Chowdhury, P.N., Karatzas, D., Khlif, W., Matas, J., Pal, U., Burie, J.C., Liu, C.l., et al.: ICDAR 2019 robust reading challenge on multi-lingual scene text detection and recognition—rrc-mlt-2019. In: ICDAR (2019)
- <span id="page-17-13"></span>54. Olejniczak, K., Sulc, M.: Text detection forgot about document ocr. In: CVWW ˇ (2023)
- <span id="page-17-15"></span>55. Palm, R.B., Laws, F., Winther, O.: Attend, copy, parse end-to-end information extraction from documents. In: ICDAR (2019)
- <span id="page-17-0"></span>56. Palm, R.B., Winther, O., Laws, F.: Cloudscan - A configuration-free invoice analysis system using recurrent neural networks. In: ICDAR (2017)
- <span id="page-17-20"></span>57. Pampari, A., Ermon, S.: Unsupervised calibration under covariate shift. arXiv (2020)
- <span id="page-17-2"></span>58. Park, S., Shin, S., Lee, B., Lee, J., Surh, J., Seo, M., Lee, H.: Cord: A consolidated receipt dataset for post-ocr parsing. In: NeurIPS workshops (2019)
- <span id="page-17-9"></span>59. Powalski, R., Borchmann, L., Jurkiewicz, D., Dwojak, T., Pietruszka, M., Pa lka, G.: Going full-tilt boogie on document understanding with text-image-layout transformer. In: ICDAR (2021)
- <span id="page-17-8"></span>60. Raffel, C., Shazeer, N., Roberts, A., Lee, K., Narang, S., Matena, M., Zhou, Y., Li, W., Liu, P.J., et al.: Exploring the limits of transfer learning with a unified text-to-text transformer. JMLR (2020)

- <span id="page-18-8"></span>61. Ren, S., He, K., Girshick, R., Sun, J.: Faster r-cnn: Towards real-time object detection with region proposal networks. In: NeurIPS (2015)
- <span id="page-18-0"></span>62. Riba, P., Dutta, A., Goldmann, L., Forn´es, A., Ramos, O., Llad´os, J.: Table detection in invoice documents by graph neural networks. In: ICDAR (2019)
- <span id="page-18-19"></span>63. Russakovsky, O., Deng, J., Su, H., Krause, J., Satheesh, S., Ma, S., Huang, Z., Karpathy, A., Khosla, A., Bernstein, M., et al.: Imagenet large scale visual recognition challenge. IJCV (2015)
- <span id="page-18-7"></span>64. Schreiber, S., Agne, S., Wolf, I., Dengel, A., Ahmed, S.: Deepdesrt: Deep learning for detection and structure recognition of tables in document images. In: ICDAR (2017)
- <span id="page-18-12"></span>65. Schuster, D., Muthmann, K., Esser, D., Schill, A., Berger, M., Weidling, C., Aliyev, K., Hofmeier, A.: Intellix–end-user trained information extraction for document archiving. In: ICDAR (2013)
- <span id="page-18-15"></span>66. Siegel, N., Lourie, N., Power, R., Ammar, W.: Extracting scientific figures with distantly supervised neural networks. In: Chen, J., Gon¸calves, M.A., Allen, J.M., Fox, E.A., Kan, M., Petras, V. (eds.) Proceedings of the 18th ACM/IEEE on Joint Conference on Digital Libraries, JCDL (2018)
- <span id="page-18-18"></span>67. Simsa, ˇ S., ˇ Sulc, M., Skalick`y, M., Patel, Y., Hamdi, A.: Docile 2023 teaser: Docu- ˇ ment information localization and extraction. In: ECIR (2023)
- <span id="page-18-20"></span>68. Sipka, T., ˇ Sulc, M., Matas, J.: The hitchhiker's guide to prior-shift adaptation. In: ˇ WACV (2022)
- <span id="page-18-1"></span>69. Skalick´y, M., Simsa, ˇ S., Uˇriˇc´aˇr, M., ˇ Sulc, M.: Business document information ex- ˇ traction: Towards practical benchmarks. In: CLEF (2022)
- <span id="page-18-11"></span>70. Smith, R.: An overview of the tesseract ocr engine. In: ICDAR (2007)
- <span id="page-18-13"></span>71. Smock, B., Pesala, R., Abraham, R.: Pubtables-1m: Towards comprehensive table extraction from unstructured documents. In: CVPR (2022)
- <span id="page-18-5"></span>72. Stanis lawek, T., Grali´nski, F., Wr´oblewska, A., Lipi´nski, D., Kaliska, A., Rosalska, P., Topolski, B., Biecek, P.: Kleister: key information extraction datasets involving long documents with complex layouts. In: ICDAR (2021)
- <span id="page-18-6"></span>73. Stray, J., Svetlichnaya, S.: Deepform: Extract information from documents (2020), <https://wandb.ai/deepform/political-ad-extraction>, benchmark
- <span id="page-18-3"></span>74. Sun, H., Kuang, Z., Yue, X., Lin, C., Zhang, W.: Spatial dual-modality graph reasoning for key information extraction. arXiv (2021)
- <span id="page-18-2"></span>75. Sunder, V., Srinivasan, A., Vig, L., Shroff, G., Rahul, R.: One-shot information extraction from document images using neuro-deductive program synthesis. arXiv (2019)
- <span id="page-18-9"></span>76. Tanaka, R., Nishida, K., Yoshida, S.: Visualmrc: Machine reading comprehension on document images. In: AAAI (2021)
- <span id="page-18-10"></span>77. Tang, Z., Yang, Z., Wang, G., Fang, Y., Liu, Y., Zhu, C., Zeng, M., Zhang, C., Bansal, M.: Unifying vision, text, and layout for universal document processing. arXiv (2022)
- <span id="page-18-14"></span>78. Tensmeyer, C., Morariu, V.I., Price, B., Cohen, S., Martinez, T.: Deep splitting and merging for table structure decomposition. In: ICDAR (2019)
- <span id="page-18-4"></span>79. Wang, J., Liu, C., Jin, L., Tang, G., Zhang, J., Zhang, S., Wang, Q., Wu, Y., Cai, M.: Towards robust visual information extraction in real world: New dataset and novel solution. In: AAAI (2021)
- <span id="page-18-16"></span>80. Web: Industry Documents Library. <https://www.industrydocuments.ucsf.edu/>, accessed: 2022-10-20
- <span id="page-18-17"></span>81. Web: Industry Documents Library API. [https://www.industrydocuments.ucsf.](https://www.industrydocuments.ucsf.edu/research-tools/api/) [edu/research-tools/api/](https://www.industrydocuments.ucsf.edu/research-tools/api/), accessed: 2022-10-20

- <span id="page-19-7"></span>82. Web: Public Inspection Files. <https://publicfiles.fcc.gov/>, accessed: 2022-10- 20
- <span id="page-19-3"></span>83. Xu, Y., Xu, Y., Lv, T., Cui, L., Wei, F., Wang, G., Lu, Y., Florencio, D., Zhang, C., Che, W., et al.: Layoutlmv2: Multi-modal pre-training for visually-rich document understanding. ACL (2021)
- <span id="page-19-2"></span>84. Xu, Y., Li, M., Cui, L., Huang, S., Wei, F., Zhou, M.: Layoutlm: Pre-training of text and layout for document image understanding. In: KDD (2020)
- <span id="page-19-8"></span>85. Xu, Y., Lv, T., Cui, L., Wang, G., Lu, Y., Florˆencio, D., Zhang, C., Wei, F.: LayoutXLM: Multimodal Pre-training for Multilingual Visually-rich Document Understanding. arXiv (2021)
- <span id="page-19-4"></span>86. Zhang, Z., Ma, J., Du, J., Wang, L., Zhang, J.: Multimodal pre-training based on graph attention network for document understanding. IEEE Transactions on Multimedia (2022)
- <span id="page-19-5"></span>87. Zhao, X., Wu, Z., Wang, X.: CUTIE: learning to understand documents with convolutional universal text information extractor. arXiv (2019)
- <span id="page-19-6"></span>88. Zheng, X., Burdick, D., Popa, L., Zhong, X., Wang, N.X.R.: Global table extractor (GTE): A framework for joint table identification and cell structure recognition using visual context. In: WACV (2021)
- <span id="page-19-1"></span>89. Zhong, X., Tang, J., Jimeno-Yepes, A.: Publaynet: Largest dataset ever for document layout analysis. In: ICDAR (2019)
- <span id="page-19-0"></span>90. Zhou, J., Yu, H., Xie, C., Cai, H., Jiang, L.: irmp: From printed forms to relational data model. In: HPCC (2016)
- <span id="page-19-9"></span>91. Zhu, Y., Kiros, R., Zemel, R., Salakhutdinov, R., Urtasun, R., Torralba, A., Fidler, S.: Aligning books and movies: Towards story-like visual explanations by watching movies and reading books. In: ICCV (2015)

# Supplementary Material DocILE Benchmark for Document Information Localization and Extraction

# 1 Dataset Details

#### 1.1 Document Preprocessing

The following pre-processing was applied to documents from the annotated set:

- (UCSF only) PDFs from UCSF contain a text "Source: [URL in UCSF]" on the bottom of the page. As this text would affect the competition tasks, it was removed from the PDFs. Instead, the original document ID is recorded in the dataset metadata.
- Skewed pages were detected in PDFs and images rendered from the PDF pages were deskewed automatically<sup>1</sup> . New PDFs were generated from the deskewed images<sup>2</sup> , each rendered to have the longer dimension equal to 842 pixels (this corresponds to the longer side of A4 at 72 DPI).

#### 1.2 Pre-computed OCR

To facilitate a quick start with the dataset, we provide pre-computed OCR. We used the DocTR [7] library with the DBNet[3] detector and the CRNN [9] recognition model, which showed good results in Document OCR in [8]. The predictions are for word-level tokens and include the geometry (bounding box), value (recognized text) and confidence. The words are grouped into blocks. For each word we also provide the snapped geometry, computed by binarizing the word image crop and removing rows/columns from the sides that contain mostly the background color. The implementation is available in the repository. The use of the provided OCR predictions by benchmark submissions is optional. The Pseudo-Character Centers from the snapped bounding boxes are used in the benchmark evaluation.

# 1.3 Document Layout Clustering

Documents in the DocILE dataset are assigned to different layout clusters, see Figure 1 for an example of a layout cluster. To find the layout clustering for the

<sup>1</sup> Using Leptonica: https://tpgit.github.io/Leptonica/skew\_8c\_source.html

<sup>2</sup> Using pdf2image: https://pypi.org/project/pdf2image/

annotated and unlabeled sets<sup>3</sup> , layout clusters were first detected with the algorithm described in this section and then manually corrected<sup>4</sup> for the annotated set.

The clustering algorithm takes KILE and LIR fields on input. These fields were predicted by a proprietary model. Then, the following two distance functions were used to detect which clusters should be merged together.

- 1. Following our definition of layouts, each cluster is represented as a set of fields that can occur in the layout along its possible x-axis positions<sup>5</sup> .The distance between two clusters is then based on the number of field types in common (weighted by the abundance of the field type in the cluster) and the distance between the positions of the same field type. Positions are first normalized to align the left-most and right-most positions (accounting for different translation and scale which is especially important for scanned documents).
- 2. The second distance function uses values of a selected set of field types that are usually equal among documents of the same layout. Specifically information about the sender (name, address, registration ID and tax ID), payment terms and text in table headers. A cluster is then a collection of all possible values for these field types. Distance between two clusters is based on the edit distance between values of the same field type.

By combining the above distance functions, layout clusters were found in the following steps:

- 1. Starting with single document clusters for all documents, clusters were iteratively merged if their distance was under a selected threshold. At most 50 documents per cluster were sent for annotation.
- 2. After annotation, predicted fields were replaced with ground truth fields and the clustering was re-run. The result was then manually corrected.
- 3. To cluster the unlabeled set, field predictions were used and each document was assigned independently to the closest cluster in the annotated set when the distance was lower than a threshold. When the distance exceeded the threshold, it was assigned cluster id −1, representing that a corresponding cluster was not found – which happened for 18.8% of the unlabeled documents. On a random sample of 100 unlabeled documents, 72 documents were assigned to some cluster with a precision of 86%. Determining whether the 28 documents were correctly unassigned was not checked as it would require much more effort.

<sup>3</sup> For the synthetic set the clustering is implicit from the selection of the template documents

<sup>4</sup> Notice that full manual check was infeasible, as that would involve checking over half of million of cluster pairs for a potential merge. Instead, potential cluster merges and splits were generated using the two distance metrics described in Section 1.3.

<sup>5</sup> The y-axis is ignored as it often varies even for documents of the same layout, e.g., based on the length of the table.

![](_page_22_Figure_2.jpeg)

Fig. 1: First page of 10 documents belonging to the same cluster.

## 1.4 Dataset Splitting

The following rules and parameters were used to split the dataset into training, validation and test split and to select the templates for synthetic documents.

- The target number of documents in the test set and validation set is 1, 000 and 500, respectively. Test set is selected first and then validation set is selected from the remaining documents with the same algorithm. The remaining documents form the training set. With respect to the test set, we consider the documents from both training and validation sets as available for training. Below we describe the selection of the test set.
- The target number of synthetic templates (documents from the training set whose annotations are used for generation of synthetic documents) is set to 100.
- The target ratio of documents from PIF and UCSF sources in the selected set is 55%:45%, which is similar to the ratio in the full annotated dataset. Without this constraint the distribution would be significantly different as the two sources have different distribution of cluster sizes, which affects further selection of the documents.
- Let us call a cluster X-shot with respect to the test set if it has X documents available for training. The cluster is called zero-shot if X = 0, few-shot if 0 < X < 4 and many-shot if X ≥ 4. The target proportion of test documents belonging to 0, 1, 2, 3-shot clusters is set to approximately 1/4, 1/12, 1/12, 1/12, respectively, for each source. I.e., 1/2 of the test documents belong to zero-shot or few-shot clusters and 1/2 of the documents belong to many-shot clusters.
- To ensure diversity of test samples belonging to zero-shot and few-shot clusters, we allow at most 20 samples from each zero-shot or few-shot cluster in the test set.
- When selecting few-shot samples, approximately half of the documents should belong to clusters containing a synthetic template, e.g., 1/24 · 1000 ≈ 42 of the documents in the test set should belong to clusters that contain a synthetic template and that have two documents available for training. The remaining synthetic templates are from many-shot clusters or clusters not contained in the test set.

### 1.5 Description of Annotations

Field Types for KILE and LIR are described in Tables 1 and 2, respectively. Note that some rather rare fields are not represented in the validation set: iban, bic, customer\_tax\_id and line\_item\_tax\_rate. Their counts in the training set are 5, 31, 40 and 96 respectively. With the micro-averaged evaluation metric their impact on the evaluation is only minor.

The number of documents and clusters containing individual fieldtypes are displayed in Figures 2 and 3 respectively.

![](_page_23_Figure_4.jpeg)

Fig. 2: The number of documents containing individual KILE (left) and LIR (right) fieldtypes, out of 5580 documents in the training and validation sets.

Table 1: Description of all KILE field types.

| field type                | description                                                                |
|---------------------------|----------------------------------------------------------------------------|
| account num               | Bank account number                                                        |
| amount due                | Total amount to be payed                                                   |
| amount paid               | Total amount already paid                                                  |
| amount total gross        | Total amount with tax                                                      |
| amount total net          | Total amount without tax                                                   |
| amount total tax          | Total sum of tax amounts                                                   |
| bank num                  | Bank number                                                                |
| bic                       | Bank Identifier Code (SWIFT)                                               |
|                           | currency code amount due Currency code or symbol found near the amount due |
| customer billing address  | Address of the company that is being invoiced                              |
| customer billing name     | Name of the company that is being invoiced                                 |
| customer delivery address | Address of the company for delivery of goods/services                      |
| customer delivery name    | Name of the company for delivery of goods/services                         |
| customer id               | Customer account number                                                    |
| customer order id         | Any customer order reference                                               |
| customer other address    | Any other name and address of the purchasing company                       |
| customer other name       | Any other name of the purchasing company                                   |
| customer registration id  | Purchaser registration identifier number                                   |
| customer tax id           | Purchaser tax identification number                                        |
| date due                  | Due date for payment                                                       |
| date issue                | Date the document was issued                                               |
| document id               | Main document number                                                       |
| iban                      | International Bank Account Number                                          |
| order id                  | Any order number                                                           |
| payment reference         | Payment reference number                                                   |
| payment terms             | Conditions for the payment time window                                     |
| tax detail gross          | Tak breakdown line amount with tax                                         |
| tax detail net            | Tax breakdown line amount without tax                                      |
| tax detail rate           | Tax breakdown line tax rate                                                |
| tax detail tax            | Tax breakdown line tax amount                                              |
| vendor address            | Address of the supplier company                                            |
| vendor email              | Any supplier e-mail address                                                |
| vendor name               | Name of the supplier company                                               |
| vendor order id           | Any vendor order reference                                                 |
| vendor registration id    | Supplier registration identification number                                |
| vendor tax id             | Supplier tax identification number                                         |
|                           |                                                                            |

Table 2: Description of all LIR field types.

| field type                     | description                                  |
|--------------------------------|----------------------------------------------|
| line_item_amount_gross         | Total amount with tax for item               |
| $line\_item\_amount\_net$      | Total amount without tax for item            |
| $line\_item\_code$             | Item article number                          |
| line_item_currency             | Line currency (if standalone)                |
| $line\_item\_date$             | Date (e.g. item delivery date)               |
| $line\_item\_description$      | Goods and services description               |
| $line\_item\_discount\_amount$ | Total discount amount                        |
| $line\_item\_discount\_rate$   | Discount rate                                |
| line_item_hts_number           | Harmonized Tariff Schedule number            |
| line_item_order_id             | Related order reference number               |
| line_item_person_name          | Person name (e.g. who performed the service) |
| line_item_position             | Line index, order of items                   |
| line_item_quantity             | Quantity                                     |
| line_item_tax                  | Line tax amount                              |
| line_item_tax_rate             | Tax rate (percentage, verbal)                |
| line_item_unit_price_gross     | Price with tax per unit                      |
| line_item_unit_price_net       | Price without tax per unit                   |
| line_item_units_of_measure     | Unit of measure                              |
| line_item_weight               | Item(s) weight (net, gross)                  |

![](_page_25_Figure_3.jpeg)

Fig. 3: The number of clusters containing individual KILE (left) and LIR (right) fieldtypes, out of 1063 clusters in the training and validation sets.

Table 3: Evaluation on zero/few/many-shot subsets of the test set for the RoBERTaBASE baseline for KILE and LIR based on the number of documents of the same layout cluster available for training (in train.+val. set).

| Task<br>Model      | Training size F1 | AP |                         | Prec. Recall |
|--------------------|------------------|----|-------------------------|--------------|
| KILE RoBERTaBASE   | 0                |    | 0.524 0.394 0.504 0.547 |              |
| KILE RoBERTaBASE   | 1-3              |    | 0.620 0.483 0.621 0.619 |              |
| KILE RoBERTaBASE   | 4+               |    | 0.742 0.609 0.742 0.742 |              |
| LIR<br>RoBERTaBASE | 0                |    | 0.598 0.504 0.568 0.630 |              |
| LIR<br>RoBERTaBASE | 1-3              |    | 0.568 0.406 0.575 0.560 |              |
| LIR<br>RoBERTaBASE | 4+               |    | 0.756 0.643 0.789 0.726 |              |

# 2 Evaluation Details

## 2.1 Additional Evaluation Metrics

Although the two benchmark tasks use different primary metrics, the evaluation of both tasks includes AP, F1, precision and recall. Predictions can use an optional flag use only for ap to indicate the prediction does not have big enough confidence and should not be counted towards F1, precision and recall but it should still be used for AP<sup>6</sup> . When AP is computed for LIR, only the "confident" predictions (with use only for ap=False) are used to find the perfect matching between line items.

Additionally, we set up a secondary evaluation benchmark for end-to-end KILE and LIR, where a correctly recognized field also needs to exactly read out the text.

The benchmark also computes results on the test subsets to compare the performance on the 0-shot, few-shot and many-shot samples (based on how many documents from the same layout cluster are available for training) as shown in Table 3. Furthermore, it is possible to evaluate separately on samples belonging to clusters for which synthetic documents were generated, to study the influence of using synthetic data. The provided evaluation code supports evaluation on any dataset subset, e.g., based on the source of the document (UCSF vs PIF).

## 2.2 AP Implementation Details

In Average Precision, predictions are sorted by score (confidence) from the highest to the lowest and added iteratively. This ordering is not well defined if several predictions have the same score or if the scores are not provided. Taking into account the use only for ap flag, effectively marking some predictions as less confident, the predictions are sorted by the following criteria:

<sup>6</sup> Note that when computing AP, adding predictions with lower score than all other predictions can never decrease the metric, no matter how low is the precision among these extra predictions.

- 1. Predictions with use only for ap=False go first.
- 2. Predictions with higher score go first.
- 3. Predictions are added in the provided order (prediction document rank), i.e., start with the first prediction for each document, then take the second prediction for each document, etc.
- 4. To break the tie for predictions with the same score and prediction document rank, the document id is hashed along the prediction document rank. This ensures a deterministic but different ordering of documents for each prediction document rank, preventing some documents to have higher influence on the final result.

Other implementation details for AP have been done in the same way as in the standard COCO[4] evaluation. Namely:

- When the Precision-Recall curve has a zig-zag pattern (precision increases for higher recall), the gaps are filled to the left.
- For two consecutive (recall, precision) pairs (r1, p1), (r2, p2) where r<sup>2</sup> > r<sup>1</sup> we use the precision p<sup>2</sup> for the interval [r1, r2] when computing the Average Precision.

This can be also explained as computing the area under a function (for recall between 0 to 1) precision(r) defined as:

$$precision(r) \coloneqq \max\{p' | \text{there exists } (p', r') \text{ with } r' \ge r\}$$

#### 2.3 Updated Results

We note that the results in the main paper and in the supplementary material were updated after the first version of this arXiv pre-print, to reflect updates in the published code (Section 4).

# 3 Baseline Details

Unsupervised Pre-training: The RoBERTaOURS[5] model was pre-trained for 50k training steps with a batch size of 64. The LayoutLMv3OURS[1] was pre-trained using AdamW optimizer [6] for 30 epochs using a batch size of 16. Both trainings use a cosine decay for the learning rate with a linear warmup. Note that LayoutLMv3 [1] uses three training objectives: masked language modeling, masked image modeling, and word-patch alignment loss. Whereas our pre-training only uses masked language modeling. Furthermore, LayoutLMv3 pre-trains without any data augmentations on the IIT-CDIP [2] dataset. Our setup uses random horizontal flipping of the images and trains on the unlabeled subset of the introduced DocILE dataset.

Supervised Pre-training on Synthetic Documents: We run 30 epochs of supervised pre-training on DocILE synthetic dataset for RoBERTaBASE, RoBERTaOURS, and LayoutLMv3OURS backbones of the joint multi-label NER model, with the following parameters: learning rate 2e−5, weight decay 0.001, batch size 16.

#### Algorithm 1 OCR re-ordering algorithm

```
Require: b
                                                                             ▷ OCR word bboxes
function GET_CENTER_LINE_CLUSTERS(b)
     compute histograms of heights and centroids
     create clusters based on the centroids and height histograms
end function
function SPLIT_FIELDS_BY_TEXT_LINES(b)
    c = get\_center\_line\_clusters(b)
    for b \in \mathbf{b} do
         b_{\text{line\_id}} \leftarrow \arg\min_{c \in \mathbf{c}} |b_y - c_y|
                                                                           ▶ Assign line numbers
    end for
end function
function GET_SORTED_FIELD_CANDIDATES(b)
    b \leftarrow split\_fields\_by\_text\_lines(b)
    sort(b)
                                                               ▷ Sort by assigned line numbers
    l \leftarrow \mathbf{group}(\mathbf{b}_{\mathrm{line\_id}})
    \forall l \in \mathbf{l} : \mathbf{sort}(l_x)
                                                                          \triangleright Sort by x-coordinate
end function
```

Supervised Training on Annotated Documents: All RoBERTa and LayoutLMv3 were trained for 750 epochs with learning rate 2e-5, weight decay 0.001 and batch size<sup>7</sup> 16.

For DETR, we train the model using the Adam optimizer with learning rate  $3 \cdot 10^{-5}$  for the transformer and  $3 \cdot 10^{-7}$  for the convolutional backbone (ResNet-50), weight decay 1e-4, FP16 precision, batch size 32 and early stopping on the validation loss.

**OCR Re-ordering** We observed that for the Line Item separation task, it is crucial to provide the text tokens in per-line reading order (i.e., from top to bottom, each text line from left to right). The pseudocode of the used re-ordering algorithm is in Algorithm 1. Since we use a joint multi-label model for both KILE and LIR, the re-ordering was applied for every training and inference.

#### 4 Code and Dataset Download

For the dataset download instructions, baseline implementations and checkpoints, we refer the reader to the https://github.com/rossumai/docile repository.

<sup>&</sup>lt;sup>7</sup> Since we used multiple GPUs that had different memory sizes, for some trainings we had to decrease the batch size. In these cases we appropriately increased the gradient accumulation step.

# References

- 1. Huang, Y., Lv, T., Cui, L., Lu, Y., Wei, F.: Layoutlmv3: Pre-training for document ai with unified text and image masking. In: ACM-MM (2022)
- 2. Lewis, D., Agam, G., Argamon, S., Frieder, O., Grossman, D., Heard, J.: Building a test collection for complex document information processing. In: SIGIR (2006)
- 3. Liao, M., Wan, Z., Yao, C., Chen, K., Bai, X.: Real-time scene text detection with differentiable binarization. In: Proceedings of the AAAI conference on artificial intelligence. vol. 34, pp. 11474–11481 (2020)
- 4. Lin, T.Y., Maire, M., Belongie, S., Hays, J., Perona, P., Ramanan, D., Doll´ar, P., Zitnick, C.L.: Microsoft coco: Common objects in context. In: ECCV (2014)
- 5. Liu, Y., Ott, M., Goyal, N., Du, J., Joshi, M., Chen, D., Levy, O., Lewis, M., Zettlemoyer, L., Stoyanov, V.: RoBERTa: A Robustly Optimized BERT Pretraining Approach. arXiv (2019)
- 6. Loshchilov, I., Hutter, F.: Decoupled weight decay regularization. In: ICLR (2019)
- 7. Mindee: doctr: Document text recognition. https://github.com/mindee/doctr (2021)
- 8. Olejniczak, K., Sulc, M.: Text detection forgot about document ocr. In: CVWW ˇ (2023)
- 9. Shi, B., Bai, X., Yao, C.: An end-to-end trainable neural network for image-based sequence recognition and its application to scene text recognition. PAMI (2016)