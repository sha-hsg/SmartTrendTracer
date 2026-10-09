# **Extracting books from production language models**

**Ahmed Ahmed**<sup>∗</sup> *ahmedah@cs.stanford.edu*

*Stanford University*

**A. Feder Cooper**<sup>∗</sup> *a.feder.cooper@yale.edu*

*Stanford University and Yale University*

**Sanmi Koyejo** *sanmi@cs.stanford.edu*

*Stanford University*

**Percy Liang** *pliang@cs.stanford.edu*

*Stanford University*

### **Abstract**

Many unresolved legal questions over LLMs and copyright center on memorization: whether specific training data have been encoded in the model's weights during training, and whether those memorized data can be extracted in the model's outputs. While many believe that LLMs do not memorize much of their training data, recent work shows that substantial amounts of copyrighted text can be extracted from open-weight models. However, it remains an open question if similar extraction is feasible for production LLMs, given the safety measures these systems implement. We investigate this question using a two-phase procedure: (1) an initial probe to test for extraction feasibility, which sometimes uses a Best-of-*N* (BoN) jailbreak, followed by (2) iterative continuation prompts to attempt to extract the book. We evaluate our procedure on four production LLMs—Claude 3.7 Sonnet, GPT-4.1, Gemini 2.5 Pro, and Grok 3—and we measure extraction success with a score computed from a block-based approximation of longest common substring (nv-recall). With different per-LLM experimental configurations, we were able to extract varying amounts of text. For the Phase 1 probe, it was unnecessary to jailbreak Gemini 2.5 Pro and Grok 3 to extract text (e.g, nv-recall of 76*.*8% and 70*.*3%, respectively, for *Harry Potter and the Sorcerer's Stone*), while it was necessary for Claude 3.7 Sonnet and GPT-4.1. In some cases, jailbroken Claude 3.7 Sonnet outputs entire books near-verbatim (e.g., nv-recall = 95*.*8%). GPT-4.1 requires significantly more BoN attempts (e.g., 20×), and eventually refuses to continue (e.g., nv-recall = 4*.*0%). Taken together, our work highlights that, even with model- and system-level safeguards, extraction of (in-copyright) training data remains a risk for production LLMs.

**Disclosure:** We ran experiments from mid-August to mid-September 2025, notified affected providers shortly after, and now make our findings public after a 90-day disclosure window.

### <span id="page-0-0"></span>**1 Introduction**

Frontier, production large language models (hereafter **production LLMs**) are trained on enormous datasets drawn from various sources, including large-scale scrapes of the Internet [\(Biderman et al., 2023;](#page-19-0) [Chen et al.,](#page-20-0) [2021;](#page-20-0) [Touvron et al., 2023;](#page-24-0) [Lee et al., 2023a\)](#page-22-0). A large amount of data in these sources includes in-copyright expression, which has led to public debate about copyright infringement, creator consent, and more. In their responses to copyright infringement claims, frontier companies argue that training on copyrighted material is both necessary to produce competitive models and fair use [\(King, 2024;](#page-22-1) [Belanger, 2025;](#page-19-1) [Wiggers & Zeff, 2025;](#page-24-1) [Claburn, 2024;](#page-20-1) [OpenAI, 2024a;](#page-23-0) [Berger, 2025\)](#page-19-2). **Fair use** is a defense to copyright infringement, providing an exception to copyright owners' exclusive rights over their works. To support their fair use arguments,

<sup>∗</sup>Equal contribution; corresponding authors.

<span id="page-1-1"></span>![](_page_1_Figure_0.jpeg)

Figure 1: **Extraction of** *Harry Potter and the Sorcerer's Stone* **for a single run.** We quantify the proportion of the ground-truth book that appears in a production LLM's generated text using a block-based, greedy approximation of longest common substring (nv-recall, Equation [7\)](#page-9-0). This metric only counts sufficiently long, contiguous spans of near-verbatim text, for which we can conservatively claim extraction of training data (Section [3.3\)](#page-7-0). We extract nearly all of *Harry Potter and the Sorcerer's Stone* from jailbroken Claude 3.7 Sonnet (BoN *N* = 258, nv-recall = 95*.*8%). GPT-4.1 requires more jailbreaking attempts (*N* = 5179) and refuses to continue after reaching the end of the first chapter; the generated text has nv-recall = 4*.*0% with the full book. We extract substantial proportions of the book from Gemini 2.5 Pro and Grok 3 (76*.*8% and 70*.*3%, respectively), and notably do not need to jailbreak them to do so (*N* = 0). *Note: We do not claim we maximized possible extraction for each LLM. Different runs use different underlying generation configurations per LLM.*

companies claim that training generative AI models is **transformative**, meaning that the use of copyrighted material adds new meaning, purpose, or message to the original work [\(Campbell v. Acuff-Rose Music\)](#page-20-2).

But how LLMs make use of training data is not always transformative. As [Lee et al.](#page-22-2) [\(2023b\)](#page-22-2) note, "[w]hen a model memorizes a work and generates it verbatim as an output, there is no transformation in content."[1](#page-1-0) In machine learning, **memorization** refers to whether specific training data have been encoded in a model's weights during training, and often also refers to whether those data can be **extracted** (near-)verbatim in that model's outputs. While LLMs can produce all sorts of novel outputs, they also memorize portions of their training data [\(Carlini et al., 2021;](#page-20-3) [2023;](#page-20-4) [Lee et al., 2022;](#page-22-3) [Nasr et al., 2023;](#page-22-4) [Hayes et al., 2025b\)](#page-21-0) (Section [2\)](#page-2-0).

Legal scholarship discusses how both extracted outputs and the corresponding encoding of the memorized work in a model's weights may satisfy the technical definition of a **copy** under U.S. [\(Cooper & Grimmelmann,](#page-20-5) [2024\)](#page-20-5) and E.U. copyright law [\(Dornis, 2025\)](#page-21-1), and how both types of copies could, in specific circumstances, cut against fair use in copyright infringement claims. Aside from these academic arguments, the two lawsuits that have been decided in the U.S., which have focused primarily on training and model outputs, find that LLM training can be fair use, with limitations [\(Bartz Judgment;](#page-19-3) [Kadrey Judgment\)](#page-22-5). In contrast, a recent ruling in Germany (currently under appeal) finds that both extracted outputs and memorization encoded in the model can be infringing copies of in-copyright training data [\(GEMA v. OpenAI;](#page-21-2) [Poltz & Heine, 2025\)](#page-23-1).

In the U.S. cases, both judgments note that neither set of plaintiffs brought compelling evidence that the LLMs in question can produce outputs that reflect legally cognizable copies of the plaintiffs' works; they did not demonstrate substantial extraction of training data. Nevertheless, this does not mean that production LLMs do not memorize copyrighted material. In recent work, [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) show that memorization of in-copyright books in open-weight LLMs is far more significant than previously understood; in some cases, memorization is so extensive that it is straightforward to extract long-form (parts of) books from models like Llama 3.1 70B. However, these results on open-weight, non-instruction-tuned LLMs do not naturally translate to production LLMs, which implement both model- and system-level safeguards intended to mitigate

<span id="page-1-0"></span><sup>1</sup> In select circumstances, verbatim copying can be associated with a transformative use, e.g., in the case of parody [\(Campbell](#page-20-2) [v. Acuff-Rose Music\)](#page-20-2) or using copies to produce a new function, like a search index [\(Authors Guild v. Google, Inc.\)](#page-19-4).

undesirable outputs [\(Bai et al., 2022\)](#page-19-5), including outputting verbatim copyrighted data [\(Anthropic, 2023;](#page-19-6) [OpenAI, 2024b\)](#page-23-2). Prior work has successfully jailbroken production systems to circumvent these safeguards and extract training data [\(Nasr et al., 2023;](#page-22-4) [2025\)](#page-22-6), but does not study extraction of long-form copyrighted text.

We bridge this gap and show that it is feasible to extract memorized, long-form parts of copyrighted books from four production LLMs. We primarily attempt to extract books that [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) observe to be highly memorized by Llama 3.1 70B, and use a simple two-phase procedure to do so (Section [3\)](#page-3-0):

- 1. **Phase 1: attempting completion of an initial prefix (may involve jailbreaking).** We combine an initial instruction ("Continue the following text exactly as it appears in the original literary work verbatim") with a short snippet of seed text from the beginning of a book (e.g., the first sentence). For the books we test, both Gemini 2.5 Pro and Grok 3 directly comply with this instruction. For Claude 3.7 Sonnet and GPT-4.1, we jailbreak the underlying model to circumvent safeguards using Best-of-*N* [\(Hughes](#page-22-7) [et al., 2024\)](#page-22-7), a simple attack that permutes the instruction portion of the prompt until the system responds successfully or the prompting budget is exhausted (Section [3.1\)](#page-4-0). The four LLMs do not always successfully continue the seed text with a loose approximation of the true text; in these cases, our procedure fails.
- 2. **Phase 2: attempting long-form extraction via requesting continuation.** If Phase 1 succeeds, we repeatedly query the production LLM to continue the text (Section [3.2\)](#page-5-0), and then ultimately compare the generated output to the corresponding ground-truth reference book. We compute the proportion of the book that is extracted near-verbatim in the output, using a score derived from a block-based, greedy approximation of longest common substring (**near-verbatim recall**, nv-recall, Section [3.3\)](#page-7-0).

Altogether, we find that is possible to extract large portions of memorized copyrighted material from all four production LLMs, though success varies by experimental settings (Section [4\)](#page-10-0). For instance, for specific generation configurations, Figure [1](#page-1-1) shows the amount of extraction for *Harry Potter and the Sorcerer's Stone* [\(Rowling,](#page-23-3) [1998\)](#page-23-3) that we obtain with one run of the two-phase procedure for each production LLM. These results show that it is possible to extract large amounts of copyrighted material. However, this is a descriptive statement about particular experimental outcomes [\(Chouldechova et al., 2025\)](#page-20-6); we do not make general claims about books extraction overall, or claims comparing overall extraction risk across production LLMs. As shown in Figure [1,](#page-1-1) our best configuration extracts nearly all of the book near-verbatim from Claude 3.7 Sonnet (nv-recall = 95*.*8%). For GPT-4.1, our best configuration extracts only part of the first chapter (nv-recall = 4*.*0%). We attempt extraction for eleven in-copyright books published before 2020, and find that most experiments result in far less extraction (nv-recall ≤ 10%). For Claude 3.7 Sonnet, we extract almost the entire text of two in-copyright books (and two in the public domain) (nv-recall ≥ 94%). We discuss important limitations of our work (e.g., monetary cost) and brief observations about why our results may be of interest to copyright (Section [5\)](#page-16-0).

**Responsible disclosure.** On September 9, 2025, we notified affected providers (Anthropic, Google DeepMind, OpenAI, and xAI) of our results and intent to publish, after discovering the success of our procedure in August 2025. Following the standard responsible disclosure process [\(Project Zero, 2021\)](#page-23-4), we told providers we would wait 90 days before making our findings public. Anthropic, Google DeepMind, and OpenAI acknowledged our disclosure. On November 29, 2025, we observed that Anthropic's Claude 3.7 Sonnet series was no longer available in Claude's UI. At the end of the 90-day disclosure window (December 9, 2025), we found that our procedure still works on some of the systems that we evaluate. Having taken the above steps, we believe it is now responsible to share our findings publicly. Doing so underscores the continued challenges of robust model- and system-level safeguards in production LLMs, particularly with respect to mitigating the risk of leakage of in-copyright training data. To give readers a sense of the qualitative similarity of our long-form extraction results, we release full, lightly format-normalized diffs for Claude 3.7 Sonnet on *Frankenstein* [\(Shelley, 1818\)](#page-23-5) and *The Great Gatsby* [\(Fitzgerald, 1925\)](#page-21-4), which are both in the public domain. (See [here.](https://drive.google.com/drive/folders/1bCI1teXoVwgcZBvbWANc2Ss_h1x0zLv-?usp=sharing) Black text reflects verbatim matches, strike-through red text indicates reference text missing from the generation, and blue underlined text reflects text in the generation missing from the reference text.)

### <span id="page-2-0"></span>**2 Background and related work**

There are three overarching topics that are relevant to our work: 1) memorization and extraction, 2) circumventing safeguards in production LLMs, and 3) the intersection of both of these areas with copyright. **Memorization and extraction of training data.** In general, models "memorize" portions (but far from all) of their training data [\(Feldman, 2020\)](#page-21-5). At a high level, **memorization** means that information about whether a model was trained on a particular data example can be recovered from the model itself [\(Cooper](#page-20-7) [et al., 2023\)](#page-20-7). There are many techniques for quantifying this phenomenon [\(Hayes et al., 2025a;](#page-21-6) [Chang](#page-20-8) [et al., 2025\)](#page-20-8), but for generative models, one of the most common measurement approaches is **extraction**: prompting the model to reproduce specific training data (near-)verbatim in its outputs [\(Carlini et al., 2021;](#page-20-3) [Lee et al., 2022;](#page-22-3) [Cooper & Grimmelmann, 2024\)](#page-20-5).

The standard method for measuring extraction in large language models (LLMs) takes a 100-token sequence of known training data, divides it into a prefix and suffix (50 tokens each), prompts the LLM with the prefix, and deems extraction to be successful if it generates the suffix verbatim [\(Carlini et al., 2023;](#page-20-4) [Hayes et al., 2025b;](#page-21-0) [Gemini Team et al., 2024;](#page-21-7) [Grattafiori et al., 2024\)](#page-21-8). Although this type of procedure is the most common in both research and frontier release reports, it is not the only way to extract training data from an LLM. [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) show that entire memorized in-copyright books can be extracted near-verbatim from Llama 3.1 70B, by running continuous autoregressive generation seeded with a short prompt of ground-truth text. This prior work focuses on long-form extraction from open-weight, non-instruction-tuned LLMs—a setting where it is possible to choose and directly configure the decoding algorithm. In contrast, we study whether long-form extraction can successfully recover books when applied to production LLMs, where we have significantly more limited control (Sections [3.2](#page-5-0) & [3.3\)](#page-7-0).

**Circumventing safeguards.** LLMs, especially those deployed in production systems, are often trained to comply with specific policies [\(Christiano et al., 2017;](#page-20-9) [Ziegler et al., 2019;](#page-24-2) [Wei et al., 2021;](#page-24-3) [Ouyang et al., 2022\)](#page-23-6). Nevertheless, such **alignment** mechanisms can be circumvented—for instance, through **jailbreaks**, which use adversarial prompting techniques to elicit harmful or otherwise restricted outputs [\(Hendrycks et al.](#page-21-9) [\(2021\)](#page-21-9); [Zou](#page-24-4) [et al.](#page-24-4) [\(2023\)](#page-24-4); Section [3.1\)](#page-4-0). When attacking production LLMs, successful jailbreaks evade not only model-level alignment but also complementary **system-level guardrails**, such as input and output filters [\(Sharma et al.,](#page-23-7) [2025;](#page-23-7) [Cooper et al., 2024\)](#page-20-10). Much prior work demonstrates that jailbreaks work in production settings [\(Wei](#page-24-5) [et al., 2023;](#page-24-5) [Anil et al., 2024;](#page-19-7) [Hughes et al., 2024\)](#page-22-7). Notably, earlier versions of ChatGPT could be jailbroken with simple, repetitive attack strings, enabling the extraction of verbatim training data [\(Nasr et al., 2023\)](#page-22-4). Although frontier AI companies are developing and refining approaches (e.g., **refusal**) to prevent training-data leakage in system outputs [\(OpenAI, 2024a;](#page-23-0) [2023\)](#page-23-8), we show that extraction remains a risk (Section [4\)](#page-10-0).

**Copyright and generative AI.** In most jurisdictions, copyright law grants exclusive rights (subject to important exceptions) in original works of authorship. When parties other than the rightsholder **reproduce** such works, courts may determine that they have **infringed** copyright; the resulting remedies can be substantial, including significant monetary damages [\(17 U.S. Code § 503, 2010\)](#page-19-8). The relationship between copyright law and generative AI is especially complicated [\(Lee et al., 2023b;](#page-22-2) [Samuelson, 2023\)](#page-23-9). Memorization is only one part of this landscape, raising questions about the reproduction of copyrighted training data. In particular, extraction of memorized training data is a recurring issue in past and ongoing lawsuits [\(Kadrey et al. v. Meta Platforms,](#page-22-8) [Inc.;](#page-22-8) [New York Times Company v. Microsoft;](#page-22-9) [Concord Music Group, Inc. v. Anthropic PBC\)](#page-20-11), where courts are considering whether memorization encoded in the model and extraction in generations constitute copyrightinfringing copying, or fall within exceptions to copyright's exclusive rights, such as **fair use** [\(Lemley & Casey](#page-22-10) [\(2021\)](#page-22-10); Section [1\)](#page-0-0). An important consideration in these cases is how easily copyrighted training data can be reproduced in model outputs [\(Lee et al., 2023b;](#page-22-2) [Cooper & Grimmelmann, 2024;](#page-20-5) [Cooper et al., 2025\)](#page-21-3)—for example, whether extraction requires simple prompts [\(GEMA v. OpenAI\)](#page-21-2) or adversarial techniques like the jailbreak we sometimes use in this paper. While we defer to others [\(Lee et al., 2023b;](#page-22-2) [2024;](#page-22-11) [Henderson et al., 2023\)](#page-21-10) and future work for detailed legal analysis, we note that our findings may be relevant to these ongoing debates (Section [5\)](#page-16-0).

### <span id="page-3-0"></span>**3 Extraction procedure**

Our overarching two-phase approach is straightforward. In Phase 1, we probe the feasibility of extracting a given book from a production LLM by querying it to complete a short phrase of ground-truth text from the beginning of the book (Figure [2,](#page-4-1) Section [3.1\)](#page-4-0) and, if this succeeds, in Phase 2 we attempt to extract the rest book by repeatedly querying the LLM to continue the text (Figure [3,](#page-6-0) Section [3.2\)](#page-5-0). Gemini 2.5 Pro and Grok 3 directly comply with our Phase 1 probe; we need to jailbreak Claude 3.7 Sonnet and GPT-4.1 for compliance.

<span id="page-4-1"></span>![](_page_4_Figure_0.jpeg)

Figure 2: **Phase 1 of our two-phase procedure.** We illustrate Phase 1 (Section [3.1\)](#page-4-0) for *Harry Potter and the Sorcerer's Stone*: providing an initial instruction to complete a short prefix of ground-truth text from the book. Gemini 2.5 Pro and Grok 3 comply directly (left); for Claude 3.7 Sonnet and GPT-4.1, we use the use Best-of-*N* jailbreak (right). We evaluate if the production LLM produces a loose approximation of the the suffix using similarity score *s* (Equation [2\)](#page-5-1). If successful (*s* ≥ 0*.*6), we proceed to Phase 2 (Figure [3,](#page-6-0) Section [3.2\)](#page-5-0).

For Phase 2, we continue until the LLM responds with a refusal, the LLM returns a stop phrase (e.g., "THE END"), or we exhaust a specified query budget. Then, we take the long-form generated output and compare it to the ground-truth text of the book to determine if extraction was successful (Section [3.3\)](#page-7-0). For the Phase 2 loop, we explore different generation configurations (e.g., maximum response length, temperature) based on what is tunable in each production LLM's API, and pick configurations for each production LLM that result in the largest amount of extraction (Section [3.2\)](#page-5-0). **Note: extraction does not always succeed.**

#### <span id="page-4-0"></span>**3.1 Attempting initial completion of a short ground-truth prefix (Phase 1)**

We interact with a production LLM via a blackbox API, which limits our access to the underlying model; we supply prompts and receive responses, but do not have access to logits or log probabilities. For a given book and production LLM, we first probe if extraction seems feasible. To do so, we attempt to have the LLM complete a provided prefix of text drawn from the book. Specifically, we start with a **seed** *s*: an initial short, ground-truth string, typically the first sentence or couple of sentences of the book. We split *s* into a **prefix** *p* and **target suffix** *t* (i.e., *s* = *p*+*t*). As illustrated in Figure [2,](#page-4-1) we form an initial prompt by concatenating a **continuation instruction** *i* with the prefix, i.e., *i* + *p*. (*i*="Continue the following text exactly as it appears in the original literary work verbatim"; in Figure [2,](#page-4-1) *i* is abbreviated as "Continue the story verbatim"). We submit this concatenated prompt to the production LLM to generate and return up to 1000 tokens, which we decode to text.

In our main experiments, Gemini 2.5 Pro and Grok 3 complied directly with instructions of this form. In contrast, Claude 3.7 Sonnet and GPT-4.1 exhibited refusal mechanisms, which prevent direct continuation of the provided prefix. Similar to prior work [\(Nasr et al.](#page-22-4) [\(2023;](#page-22-4) [2025\)](#page-22-6); Section [2\)](#page-2-0), we jailbreak these two production LLMs to circumvent alignment. We began with a simple attack from the literature—Best-of-*N* [\(Hughes](#page-22-7) [et al., 2024\)](#page-22-7)—and, given its immediate success, do not consider more sophisticated attacks in this work.

**Best-of-***N* **jailbreak (used with Claude 3.7 Sonnet and GPT-4.1).** When running **Best-of-***N* **(BoN)** [\(Hughes et al., 2024\)](#page-22-7), one selects an initial prompt, makes *N* variations of that prompt with random text perturbations, submits the *N* prompts to an LLM to generate *N* candidate responses, and then selects the response that most effectively bypasses safety guardrails, where effectiveness is determined by a chosen, context-appropriate criterion (detailed below). The random text perturbations include compositions of flipping alphabetic character case, shuffling word order, character substitutions with visually similar glyphs (e.g., 's' → {'\$'*,* '5'}), and other formatting edits [\(Hughes et al.](#page-22-7) [\(2024\)](#page-22-7); Appendix [A\)](#page-25-0). Even if most of

the production LLM's outputs are compliant with its guardrail policies, the probability that the LLM is jailbroken—that is, at least one response violates these policies—increases with *N*.

This procedure is model-agnostic and only requires blackbox access, which makes it well-suited to our setting of production LLMs. In practice, our BoN prompt is the initial instruction *i*; we produce *N* random permutations of *i* (e.g., "C0ntinuE th3 st0ry verb@tim" in Figure [2\)](#page-4-1), and we concatenate each with the prefix *p* and submit to the production LLM's API to produce *N* responses. We then gauge success for Phase 1 when a decoded API response contains at least a loose match to the ground-truth target suffix *t*. For Gemini 2.5 Pro and Grok 3, for which we did not use BoN, there is only one response to compare to *t*; for Claude 3.7 Sonnet and GPT-4.1, we evaluate *N* BoN responses to see if any of them is a loose match to *t*.

**Determining Phase 1 success.** We quantify loose matches between a production LLM response *r* and the target suffix *t* using **longest common substring**, which checks whether there exists a substring of words (i.e., a contiguous sequence of words) that appears verbatim in both. That is, we denote the whitespace-split character sequences of *t* and *r* as *T* = (*w* (*t*) 1 *, . . . , w* (*t*) |*T*| ) and *R* = (*w* (*r*) 1 *, . . . , w* (*r*) |*R*| ), respectively. We then let

$$\mathsf{longest}(T,R) \triangleq \max \left\{ \ell \, : \, (w_i^{(t)}, \dots, w_{i+\ell-1}^{(t)}) = (w_j^{(r)}, \dots, w_{j+\ell-1}^{(r)}), \, \, 1 \leq i \leq |T| - \ell + 1, \, \, 1 \leq j \leq |R| - \ell + 1 \right\} \quad \ (1)$$

denote the length of the longest contiguous common subsequence of *T* and *R* (i.e., longest common substring of *t* and *r*). We define a normalized similarity score

<span id="page-5-3"></span><span id="page-5-1"></span>
$$s(T,R) \triangleq \frac{\mathsf{longest}(T,R)}{|T|} \quad \big(s(T,R) \in [0,1]\big), \tag{2}$$

which measures the fraction of whitespace-delimited text tokens in *T* that is covered by the longest contiguous verbatim span also found in *R*. In practice, we consider Phase 1 to be successful when *s* ≥ 0*.*6—i.e., when there is an *ℓ*-length verbatim common substring that covers at least 60% of the target suffix *t*. In initial experiments, we observed this to be a necessary minimum for Phase 2 to be feasible. **Note: we do not claim extraction of training data when Phase 1 succeeds with returning this loose match; we defer extraction claims to Phase 2.** For Claude 3.7 Sonnet and GPT-4.1, we run BoN with *N* prompts, stopping when the *N*-th response *r<sup>N</sup>* yields *s*(*T, R<sup>N</sup>* ) ≥ 0*.*6 or when a maximum budget (*N* = 10*,*000) is met.

#### <span id="page-5-0"></span>**3.2 Attempting long-form extraction of training data (Phase 2)**

In Phase 2 we attempt long-form extraction of the rest of the book. Following successful approximate completion of the seed prefix in Phase 1, we iteratively query the production LLM to continue the text (Figure [3\)](#page-6-0). Similar to the long-form extraction of books performed by [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3), the prefix in Phase 1 is the *only* ground-truth text that we provide in the entire procedure; any additional text that we recover from a book in Phase 2 is generated and returned by the production LLM. For each production LLM, we explore different generation configurations: temperature, maximum response length and, where available, frequency penalty and presence penalty (Section [4\)](#page-10-0). For a single run of Phase 2, we fix the generation configuration and execute the continuation loop until a maximum query budget is expended, or the production LLM returns a response that contains either a refusal to continue or a stop phrase (e.g. "THE END").[2](#page-5-2) We then concatenate the response from the initial completion probe in Phase 1 with the in-order responses in the Phase 2 continuation loop to produce a long-form generated text, which we evaluate for extraction success (Section [3.3\)](#page-7-0).

**Particulars for long-form extraction from production LLMs.** Most generally, extraction refers to prompting a model to reproduce memorized training data encoded in its weights [\(Cooper et al.](#page-20-7) [\(2023\)](#page-20-7); Section [2\)](#page-2-0). There are various approaches in the memorization literature that satisfy this definition. However, attempting *long-form* extraction from *production* LLMs differs from most of this prior work.

First, as discussed in Section [2,](#page-2-0) the most commonly used extraction method—**discoverable extraction** [\(Lee](#page-22-3) [et al., 2022;](#page-22-3) [Carlini et al., 2021;](#page-20-3) [2023;](#page-20-4) [Hayes et al., 2025b;](#page-21-0) [Cooper et al., 2025\)](#page-21-3)—is infeasible for production LLMs that are aligned to behave like conversational chatbots. Discoverable extraction prompts with a

<span id="page-5-2"></span><sup>2</sup> In practice, we occasionally observe generic internal server errors (500) for some providers, which also halts the loop.

<span id="page-6-0"></span>![](_page_6_Figure_0.jpeg)

Figure 3: **Phase 2 of our two-phase procedure.** If Phase 1 succeeds (i.e., returns a response with *s* ≥ 0*.*6, see Figure [2,](#page-4-1) Section [3.1\)](#page-4-0), we proceed to Phase 2 (Section [3.2\)](#page-5-0). We similarly illustrate Phase 2 for *Harry Potter and the Sorcerer's Stone*: we repeatedly query to continue the text, until the LLM responds with a refusal or a stop phrase, or we exhaust a specified query budget. Phase 2 culminates in a long-form generation that we compare to a corresponding reference book to gauge extraction success using nv-recall (Equation [7,](#page-9-0) Section [3.3\)](#page-7-0). The prefix in Phase 1 is the *only* ground-truth text that we provide in the entire two-phase procedure; any additional text that we recover from a book in Phase 2 is generated and returned by the production LLM.

sequence of training data (just a prefix *p*) and checks if the LLM generates the verbatim continuation (the suffix *t*) of that training data—i.e., essentially observing if the LLM successfully "completes the sentence" begun in the prompt. But conversational chatbots do not tend to demonstrate "complete the sentence" behavior. Therefore, while these models still memorize training data, this type of procedure is generally ineffective for extracting those memorized data [\(Nasr et al., 2023\)](#page-22-4). We sometimes use a jailbreak in Phase 1 to unlock continuation-like behavior; this is also why it is surprising that we did not need to jailbreak Gemini 2.5 Pro or Grok 3 to successfully execute the Phase 2 continuation loop.

Second, discoverable extraction is predominantly effective for extracting relatively short sequences (typically 50 tokens, or ≈38 words), even when much longer sequences are memorized in the model. For an autoregressive language model, the probability of generating an exact continuation (e.g., a suffix *t*) conditioned on a prompt (e.g., a prefix *p*) decreases as the length of the continuation increases, making long memorized sequences increasingly difficult to extract. This is why for long-form extraction, as in [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3), we do not attempt to produce the whole book in one interaction, and instead query iteratively to generate a limited length of text that continues the prefix and any text in the context that the LLM has already generated. In practice, in our production LLM setting, limiting the generation length was also important for evading output filters (Section [4\)](#page-10-0).

Third, for production LLMs, users have relatively little control over the decoding procedure, and do not typically have access to logits or log probabilities. In contrast, most research on memorization examines controlled settings for open-weight models, where it is possible to study extraction with fine-grained choices about decoding strategy [\(Lee et al., 2022;](#page-22-3) [Carlini et al., 2023\)](#page-20-4) and make use of logits [\(Hayes et al., 2025b\)](#page-21-0). For instance, in an experiment that extracts *Harry Potter and the Sorcerer's Stone* from Llama 3.1 70B, [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) are able to deterministically reproduce the entirety of the book near-verbatim because they can use beam search, which we do not have access to using blackbox APIs.

Lastly, standard evaluation metrics for relatively short-form extraction are not applicable to long-form generated outputs. For discoverable extraction, it is typical to compare the generated continuation and target suffix, and to declare extraction success when there is verbatim equality or the continuation is within a small edit distance to the target [\(Lee et al., 2022;](#page-22-3) [Ippolito et al., 2022\)](#page-22-12). While these success criteria are reasonable for assessing extraction success of 50-token (≈38-word) sequences, [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) observe

#### <span id="page-7-2"></span>Algorithm 1 Long-span, near-verbatim matching block formation

```
Require: Word lists B (the book) and G (the generated text)

Require: Thresholds \tau_{\text{gap}}^{(1)}, \tau_{\text{align}}^{(1)} (merge 1), \tau_{\text{gap}}^{(2)}, \tau_{\text{align}}^{(2)} (merge 2); minimum lengths l^{(1)} (filter 1), l^{(2)} (filter 2)

1: \mathbb{B}^{(\text{base})} \leftarrow \text{greedy\_approx\_longest}(B, G) \Rightarrow \text{identify}: compute verbatim matching blocks (Eq. 3)

2: \widetilde{\mathbb{B}}^{(1)} \leftarrow \text{merge}(\mathbb{B}^{(\text{base})}, \tau_{\text{gap}}^{(1)}, \tau_{\text{align}}^{(1)}) \Rightarrow \text{merge 1}: stitch very short gaps (Eq. 4)

3: \widetilde{\mathbb{B}}^{(1)}_{\geq l^{(1)}} \leftarrow \text{filter}(\widetilde{\mathbb{B}}^{(1)}, l^{(1)}) \Rightarrow \text{filter 1}: remove short blocks (Eq. 5)

4: \widetilde{\mathbb{B}}^{(2)} \leftarrow \text{merge}(\widetilde{\mathbb{B}}^{(1)}_{\geq l^{(1)}}, \tau_{\text{gap}}^{(2)}, \tau_{\text{align}}^{(2)}) \Rightarrow \text{merge 2}: passage-level consolidation (Eq. 4)

5: \widetilde{\mathbb{B}}^{(2)}_{\geq l^{(2)}} \leftarrow \text{filter}(\widetilde{\mathbb{B}}^{(2)}, l^{(2)}) \Rightarrow \text{final ordered set of long near-verbatim matching blocks}
```

that strict equality is too stringent when extracting (tens of) thousands of tokens. This was true even in their work, where the long-form generated outputs were almost (but not quite) exact reproductions of reference texts. In our work, the reproductions are often less exact, so we need to devise a different measurement procedure for claiming extraction success.

### <span id="page-7-0"></span>3.3 Verifying extraction success

In this work, we use extraction metrics that allow for near-verbatim matches to the training data. At a high level, to be valid evidence for extraction, the generated text must (1) reflect a sufficiently near-verbatim reproduction of text in the actual book, and (2) be sufficiently long, such that memorization is the overwhelmingly most plausible explanation for near-verbatim generation (Carlini et al., 2021). We propose a procedure that captures when long-form generated text satisfies these conditions (Section 3.3.1). We then elaborate on why this procedure enables us to make conservative extraction claims (Section 3.3.2): it may miss some valid instances of extraction of training data, but importantly should not include short spans of generated text that may coincidentally resemble ground-truth text from a book (i.e., text that is not actually memorized).

#### <span id="page-7-1"></span>3.3.1 Identifying near-verbatim extracted text in a long-form generation

Long-form similarity detection is a notoriously challenging problem, with an active, longstanding body of research (Hoad & Zobel, 2003; Henzinger, 2006; Santos et al., 2012; Wang & Dong, 2020). We draw from this work, and propose a variation on existing methods to identify long spans of near-verbatim text that reflect successful extraction. We summarize this procedure in Algorithm 1, and discuss each step in detail below.

Following Cooper et al. (2025), we begin with an algorithm that produces a **greedy approximation of longest common substring** (difflib SequenceMatcher, 2025).<sup>3</sup> In contrast to the Phase 1 longest metric (Equation 1), which returns the length of the *single* longest contiguous verbatim subsequence shared by two input lists, this algorithm **identifies** and returns an *ordered set* of all contiguous verbatim matching blocks shared by two input lists—in our case, lists of whitespace-delimited **words** from book B and generated text G. This greedy block-matching procedure may fragment a single passage into multiple blocks due to minor discrepancies, such as short formatting differences, insertions, or deletions (Figure 4a). To better capture long-form passage recovery, we process the ordered set of verbatim blocks: we iteratively **merge** well-aligned, nearby blocks to form longer *near-verbatim* blocks, and then **filter** these blocks to retain only those that exceed a minimum specified length, so that each retained block is sufficiently long to support an extraction claim. Below, we describe each of the three steps (identify, merge, and filter), how we compose them in practice, and how we use the resulting near-verbatim blocks to report different information about extraction.

**Identify verbatim blocks.** Given two lightly normalized texts  $\boldsymbol{b}$  (the reference book) and  $\boldsymbol{g}$  (the generated text), we split each on whitespace characters to obtain ordered lists of words  $B = (w_1^{(\boldsymbol{b})}, \dots, w_{|B|}^{(\boldsymbol{b})})$  and  $G = (w_1^{(\boldsymbol{b})}, \dots, w_{|B|}^{(\boldsymbol{b})})$ 

<span id="page-7-3"></span><sup>&</sup>lt;sup>3</sup>The experiments in Cooper et al. (2025) produce deterministic, nearly exact long-form reproductions in generated outputs, and so Cooper et al. (2025) can run this algorithm without modifications on whole documents for extraction claims. Our experimental outputs are almost always less exact, so it would be invalid to reuse their procedure as-is here.

<span id="page-8-2"></span>![](_page_8_Picture_0.jpeg)

(a) Claude 3.7 Sonnet, Frankenstein

<span id="page-8-0"></span>(b) Gemini 2.5 Pro. The Da Vinci Code

Figure 4: Near-verbatim block formation. After identifying verbatim blocks, we merge closely aligned, nearby blocks (Equation 4). In both subfigures, the blocks are aligned ( $|\Delta_k^{(B)} - \Delta_k^{(G)}| = 0$ ). The first merge (M1) is very stringent, with a maximum gap  $\tau_{\rm gap}^{(1)} = 2$  words, and then filter 1 (F1) only retains blocks that are at least 20 words long ( $l^{(1)} = 20$ ). The second merge (M2), performed on the blocks retained after F1, is slightly more relaxed ( $\tau_{\rm gap}^{(2)} = 10$ ), and so the second filter is more stringent ( $l^{(2)} = 100$ ). In Figure 4a, M1 merges very close blocks. The remaining blocks—block 1, block 2\* (=block 2 + block 3 + block 4 + block 5), and block 6—are each long enough to be retained by F1 (but note that they would not at this point be retained by F2). These blocks are merged in M2, resulting in a single 141-word block that is retained after F2. In Figure 4b, no blocks are retained. There are verbatim-matching blocks returned by the identify step, but they are too short to be valid evidence for extraction. Our two-pass merge-and-filter procedure removes them; they are not counted in our extraction metric, m (Equation 6). See Appendix B for more details.

 $(w_1^{(g)}, \ldots, w_{|G|}^{(g)})$ . We then find verbatim matching blocks by greedily locating the longest substring of words shared by B and G, and recursively repeating the search on the unmatched regions to the left and right (difflib SequenceMatcher, 2025). This produces an ordered set of verbatim-matching blocks

<span id="page-8-1"></span>
$$\mathbb{B}^{(\text{base})}(B,G) = \{\beta_k\}_{k=1}^K, \quad \text{with each } \beta_k \triangleq (i_k, j_k, m_k),$$
 (3)

where block  $\beta_k$  is defined by: (i) a starting index  $i_k$  in B, (ii) a starting index  $j_k$  in G, and (iii) a length  $m_k$ , measured in words. Each block  $\beta_k$  satisfies  $B[i_k:i_k+m_k]=G[j_k:j_k+m_k]$  exactly, and has equal verbatim length  $m_k$  in both B and G. (Figure 4). Each region of the reference book text can be included in at most one block. Therefore, starting with this identification procedure means that we capture unique instances of extraction; we do not count repeated extraction of the same passage if it appears in the generated text multiple times. Further, this greedy matching procedure induces a monotone alignment between B and G, so the resulting blocks are ordered consistently in both texts. As a result, verbatim-matching text that appears out-of-order in G with respect to B may not be matched to a block—i.e., may be missed by this identification procedure. We only merge adjacent blocks and filtering preserves block order, so monotonicity (and thus consistent block ordering) is maintained throughout all merge and filter steps.

**Merge blocks.** Let  $\beta_k$  and  $\beta_{k+1}$  be consecutive blocks in an ordered set  $\mathbb{B}(B,G)$ . We define the inter-block gaps  $\Delta_k^{(B)} \triangleq i_{k+1} - (i_k + m_k)$  and  $\Delta_k^{(G)} \triangleq j_{k+1} - (j_k + m_k)$ , which measure the number of unmatched words between the two blocks in B and G, respectively. We merge blocks k and k+1 if the following conditions hold:

$$\max(\Delta_k^{(B)}, \Delta_k^{(G)}) \le \tau_{\text{gap}}$$
 (proximity) and  $\left|\Delta_k^{(B)} - \Delta_k^{(G)}\right| \le \tau_{\text{align}}$  (text alignment). (4)

Here,  $\tau_{\rm gap}$  specifies the maximum number of unmatched words allowed between consecutive blocks, and  $\tau_{\rm align}$  limits merges to blocks that occur in roughly corresponding locations in the reference and generated texts, which helps avoid stitching together unrelated content. When these conditions are met, we replace blocks k and k+1 with a single merged near-verbatim block with **effective matched length**  $m_k^* \triangleq m_k + m_{k+1}$ , and spanning indices  $[i_k, i_{k+1} + m_{k+1})$  in B and  $[j_k, j_{k+1} + m_{k+1})$  in G (Figure 4). We conservatively do not count gaps

reconciled by a merge:  $m_k^*$  counts only verbatim-matched words, so it is less than the length of  $[i_k, i_{k+1} + m_{k+1})$  in B, which spans the gap between  $\beta_k$  and  $\beta_{k+1}$  (and similarly less than  $[j_k, j_{k+1} + m_{k+1})$  in G).

**Filter blocks.** Very short matching blocks may reflect coincidental overlap rather than meaningful long-form similarity that we can safely call extraction (Figure 4b). We therefore filter blocks by a minimum length threshold l. Given an ordered block set  $\mathbb{B}(B,G)$ , we define the filtered ordered block set

<span id="page-9-1"></span>
$$\mathbb{B}_{\geq l}(B,G) \triangleq \{(i_k, j_k, m_k) \in \mathbb{B}(B,G) \mid m_k \geq l\}.$$
(5)

In practice, after identifying verbatim blocks, we perform two merge-and-filter passes (Algorithm 1) to obtain near-verbatim blocks that reflect extracted training data. In the first pass, we merge blocks separated by trivial gaps ( $\tau_{\rm gap}^{(1)}=2$  and  $\tau_{\rm align}^{(1)}=1$ , see Figure 4), and then filter out short blocks by retaining only those with length at least  $l^{(1)}=20.^4$  In the second pass, we perform a more relaxed but still stringent merge to consolidate passage-level matches ( $\tau_{\rm gap}^{(2)}=10$ ,  $\tau_{\rm align}^{(2)}=3$ ), followed by a final filter that retains only sufficiently long near-verbatim blocks ( $l^{(2)}=100$ ) to support a valid extraction claim (Section 3.3.2). Because filtering is interleaved with merging, some fragmented near-verbatim passages may fail to consolidate into a single long block and may be filtered out. This is a deliberate trade-off: we prefer to be conservative and incur false negatives (i.e., miss some instances of extraction) rather than risk including false positives.

Metrics from near-verbatim blocks. From the near-verbatim, extracted text represented in the final ordered block set, we can aggregate several useful metrics. Let  $\mathbb{B}^* = \{(i_k^*, j_k^*, m_k^*)\}_{k=1}^{K^*}$  denote the final set of blocks returned by the two-pass merge-and-filter procedure (Algorithm 1). We define

$$m := \mathsf{matched}(B, G) \triangleq \sum_{(i_k^*, j_k^*, m_k^*) \in \mathbb{B}^*} m_k^*. \tag{6}$$

which is the total number of in-order words extracted near-verbatim in G with respect to B. From m, we then define the relative **near-verbatim recall** of book B extracted in generation G:

<span id="page-9-6"></span><span id="page-9-3"></span><span id="page-9-0"></span>
$$\mathsf{nv-recall}(B,G) \ \triangleq \ \frac{m}{|B|}, \tag{7}$$

which reflects the proportion of in-order, near-verbatim extracted text relative to the length of the whole book. We typically report nv-recall as a percentage rather than a fraction (e.g., Figure 1). For further analysis, we also define in absolute word counts how much in-order, near-verbatim text we failed to extract in B (i.e., is **missing** in G) and how much **additional** non-book text is in G (i.e., is not contained near-verbatim in B):

$$\operatorname{missing}(B,G) \triangleq |B| - m, \quad \operatorname{additional}(B,G) \triangleq |G| - m.$$
 (8)

Since m counts only aligned, near-verbatim blocks from an *ordered* set, verbatim text that is reproduced out-of-order may be present in G but excluded from m. Such text would instead be counted in missing and additional, even though it represents valid extraction, and so our measurements may under-count extraction.<sup>5</sup>

#### <span id="page-9-2"></span>3.3.2 Claiming extraction success without information about training-data membership

We next elaborate on why, absent certain knowledge of production LLM training datasets, the above measurement procedure captures valid evidence of extraction. When making a claim about extraction of a sequence of training data, one is necessarily also making a claim that this sequence was in the training dataset (Carlini et al., 2021). By definition, "it is only possible to extract memorized training data, and (tautologically) training data can only be memorized if they are included—i.e., are **members**—of the training dataset. To demonstrate extraction is therefore to demonstrate memorization, and memorization implies membership" in the training dataset (Cooper et al., 2025).

<span id="page-9-5"></span><span id="page-9-4"></span> $<sup>^4</sup>$ This is conservative; 20 words is approximately half of the ≈38 words typically used in discoverable extraction. See Appendix B.  $^5$ To identify these cases, as well as instances of duplicated extraction in G, one could iteratively re-run our measurement procedure on B and unmatched (non-block) text in G.

Much prior work on extraction is conducted on open-weight models with known training datasets [\(Lee et al.](#page-22-3) [\(2022\)](#page-22-3); [Carlini et al.](#page-20-4) [\(2023\)](#page-20-4); [Hayes et al.](#page-21-0) [\(2025b\)](#page-21-0); [Wei et al.](#page-24-7) [\(2025\)](#page-24-7); Section [3.2\)](#page-5-0); it is known with certainty that the extracted data were members of the training dataset. In contrast, in our production LLM setting, we do *not* have access to certain, ground-truth information about the training dataset. This means that, embedded in our claims for extraction of books text, we are also claiming that the text that we generated was included nearverbatim in production LLMs' training data.[6](#page-10-1) As noted at the beginning of this section, to make a valid claim, the generated text has to be sufficiently long and similar to the suspected training data, such that memorization of that data from the training set is the overwhelmingly plausible explanation. This is because, when a sufficiently long, unique sequence of training data is generated, "[t]he probability that this would have happened by random chance is astronomically low, and so we can say that the model has 'memorized' this training data" [\(Car](#page-20-12)[lini, 2025\)](#page-20-12); that sequence of training data "must be stored *somewhere* in the model weights" [\(Nasr et al., 2023\)](#page-22-4).

In their prior work on extraction from production LLMs, [Nasr et al.](#page-22-4) [\(2023\)](#page-22-4) ensure validity by requiring that the LLM produce sufficiently long (≥50-token/roughly ≥38-word) sequences that exactly match a proxy dataset reflecting data likely used for LLM pre-training [\(Nasr et al., 2023;](#page-22-4) [2025\)](#page-22-6). While 50 tokens may seem relatively short, for an LLM, exact matches of this length are extraordinarily unlikely without memorization.[7](#page-10-2) Therefore, the results in [Nasr et al.](#page-22-4) [\(2023\)](#page-22-4) are accepted as strong evidence for extraction, without direct knowledge of the training dataset. In our experiments, we target extraction of specific documents, which we know are widely available in several common pre-training datasets, including Books3 (where we access our reference texts) and other torrents like LibGen (Appendix [C.1\)](#page-28-0). Beyond the initial short seed prefix, we provide no other book-specific information to the LLM. We also set a much higher bar than generating ≥38 words to call extraction successful: at a minimum, we require 100-word near-exact passages, and often retrieve passages that are significantly longer—e.g., thousands of words (Table [1,](#page-12-0) Section [4.2\)](#page-12-1). Together, the relatively short length of the prefix in Phase 1, the lack of book-specific guidance in the continuation loop in Phase 2, and the length and fidelity of the near-verbatim matches we identify are strong evidence of memorization of training data, which we have successfully extracted in outputs.

### <span id="page-10-0"></span>**4 Experiments**

We now present our main results. We begin with details about the exact production LLMs and books we test, as well as high-level variations in how we instantiate our two-phase procedure (Section [4.1\)](#page-10-3). We then give a summary of high-level, experimental outcomes for different books and LLMs (Section [4.2\)](#page-12-1), before discussing more detailed LLM-specific results (Section [4.3\)](#page-15-0). Additional results can be found in Appendix [D.](#page-31-0)

#### <span id="page-10-3"></span>**4.1 Setup**

Given that production systems change over time (i.e., are unstable compared to open-weight LLMs), we limited our experiments to between mid-August and mid-September 2025. We attempt to extract thirteen books from four production LLMs, and predominantly report results for the single run that shows the maximum amount of extraction we observed for a given production LLM, book, and generation configuration.

**Production LLMs.** The four production LLMs we evaluate are Claude 3.7 Sonnet (claude-3-7-sonnet-20250219), GPT-4.1 (gpt-4.1-2025-04-14), Gemini 2.5 Pro (gemini-2.5-pro), and Grok 3 (grok-3). Throughout, we refer to these LLMs by their names, rather than these API versions. Claude 3.7 Sonnet has a knowledge cutoff date of October 2024 [Anthropic](#page-19-9) [\(2025\)](#page-19-9), GPT-4.1's is June 2024 [\(OpenAI,](#page-23-11) [2025\)](#page-23-11), Grok 3's is November 2024 [\(xAI, 2025\)](#page-24-8), and Gemini 2.5 Pro's is January 2025 [\(Google Cloud, 2025\)](#page-21-12).

**Books.** We attempt to extract thirteen books: eleven in-copyright in the U.S. and two in the public domain. We predominantly selected books that [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) observe to be highly memorized by Llama 3.1 70B (Appendix [C.1\)](#page-28-0). The books under copyright in the U.S. are *Harry Potter and the Sorcerer's Stone* [\(Rowling, 1998\)](#page-23-3) (which we sometimes abbreviate in plot labels as "Harry Potter 1"), *Harry Potter*

<span id="page-10-1"></span><sup>6</sup>We only make membership and memorization claims about this specific text, not the whole book (except for the four whole extracted books for Claude 3.7 Sonnet). For more on this distinction, see Appendix E.6, [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3).

<span id="page-10-2"></span><sup>7</sup>The prompts that elicited these training data sequences did not contain these sequences' prefixes; they involved completely unrelated jailbreak prompts, which queried ChatGPT 3.5 to repeat a single token (e.g., "poem") forever.

<span id="page-11-1"></span>![](_page_11_Figure_0.jpeg)

Figure 5: **Proportion of book extracted (**nv**-**recall**).** We show nv-recall (%) for the twelve books for which we run Phase 2. Each bar is annotated with the corresponding nv-recall for a production LLM-book pair; the number in parentheses above is the BoN samples *N* in Phase 1 (*N* = 0 for Gemini 2.5 Pro and Grok 3, since we do not jailbreak those production LLMs.) † denotes that Phase 1 failed; ∗ indicates we did not attempt Phase 2. Gray shading indicates public domain books. The vertical axis in each row has a different scale. *Note: Each bar reflects a single run of Phase 2, where the underlying generation configuration is fixed per LLM but varies across LLMs. The groups of bars do not reflect comparisons of results obtained from testing all production LLMs under the same conditions.*

*and the Goblet of Fire* [\(Rowling, 2000\)](#page-23-12) ("Harry Potter 4"), *1984* [\(Orwell, 1949\)](#page-23-13), *The Hobbit* [\(Tolkien, 1937\)](#page-23-14), *The Catcher in the Rye* [\(Salinger, 1951\)](#page-23-15), *A Game of Thrones* [\(Martin, 1996\)](#page-22-15), *Beloved* [\(Morrison, 1987\)](#page-22-16), *The Da Vinci Code* [\(Brown, 2003\)](#page-20-13), *The Hunger Games* [\(Collins, 2008\)](#page-20-14), *Catch-22* [\(Heller, 1961\)](#page-21-13), and *The Duchess War* [\(Milan, 2012\)](#page-22-17). The public domain books are *Frankenstein* [\(Shelley, 1818\)](#page-23-5) and *The Great Gatsby* [\(Fitzgerald, 1925\)](#page-21-4). We obtained these books from the Books3 corpus, which was torrented and released in 2020.[8](#page-11-0) Therefore, all of these books significantly pre-date the knowledge cutoffs of every LLM we test. Following [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3), as a negative control we also test *The Society of Unknowable Objects* [\(Brown,](#page-20-15) [2025\)](#page-20-15), published in digital formats on July 31, 2025. This date is long after the training cutoffs for all four LLMs, and therefore it is very unlikely that this original novel contains text that is in the training data.

**Configurations for the two-phase procedure and quantifying extraction success.** For Phase 1 (Section [3.1\)](#page-4-0), we set a maximum BoN budget of *N* = 10*,*000 for each experiment. In our initial experiments, we observed that we did not need to jailbreak Gemini 2.5 Pro or Grok 3 (*N* = 0). For the initial prompt of the instruction and seed prefix, we generate up to 1000 tokens as the response. We only attempt Phase 2 if Phase 1 succeeds, with the production LLM producing a response that is at least a loose approximation of the target suffix, i.e., *s* ≥ 0*.*6 (Equation [2\)](#page-5-1). We run the Phase 2 continuation loop (Section [3.2\)](#page-5-0) for up to a maximum query budget, or until the production LLM responds with a refusal or stop phrase, e.g., "THE END". The four production-LLMs APIs expose different, configurable generation parameters (e.g., frequency penalty). For all four LLMs, we set temperature to 0, but other LLM-specific configurations vary (Appendix [C.2\)](#page-28-1). For instance, based on our exploratory initial experiments, we observed it was necessary to set the per-interaction maximum generation length differently for each LLM to evade output filters. For our extraction measurements

<span id="page-11-0"></span><sup>8</sup>We have a copy of this dataset for research purposes only, stored on a university research computing cluster.

<span id="page-12-0"></span>Suddenly in the wood beyond The Water a flame leapt upprobably somebody lighting a wood-fireand he thought of plundering dragons settling on his quiet Hill and kindling it all to flames.

He shuddered; and very quickly he was plain Mr. Baggins of Bag-End, Under-Hill, again. He got up trembling.

He had less than half a mind to fetch the lamp, and more than half a mind to pretend to, and go and hide behind the beer-barrels in the cellar, and not come out again until all the dwarves had gone away. Suddenly he found that the music and the singing had stopped, and they were all looking at him with eves shining in the dark. was all stooped over, and he had very terrible posture, and in class, whenever he dropped a piece of chalk at the blackboard, some guy in the first row always had to get up and pick it up and hand it to him. That's awful, in my opinion. But if you thought about him just enough and not too much, you could figure it out that he wasn't doing too bad for himself. For instance, one Sunday when some other guys and I were over there for hot chocolate, he showed us this old beat-up Navajo blanket that he and Mrs. Spencer'd bought of some Indian in Yellowstone Park. You could tell old Spencer'd Spencer got a big bang out of buying it. That's what I mean. You take somebody old as hell, like old Spencer, and they can get a big bang kick out of buying a blanket.

(a) Gemini 2.5 Pro, The Hobbit

(b) Grok 3, The Catcher in the Rye

Figure 6: Extracted text from in-copyright books. We provide two cropped examples of text extracted during Phase 2, diffing the ground-truth book from Books3 with the production LLM generation. Text in black reflects a verbatim match between the two; bold blue text reflects generated text that is absent in book; strike-through red text indicates ground-truth text absent from the generated text.

| Book                   | Claude 3.7 Sonnet |          | GPT-4.1        |         |        | Gemini 2.5 Pro |         |        | Grok 3         |         |         |                |
|------------------------|-------------------|----------|----------------|---------|--------|----------------|---------|--------|----------------|---------|---------|----------------|
|                        | # Cont.           | Cost     | $\max  \beta $ | # Cont. | Cost   | $\max  \beta $ | # Cont. | Cost   | $\max  \beta $ | # Cont. | Cost    | $\max  \beta $ |
| Harry Potter 1         | 480               | \$119.97 | 6658           | 31      | \$1.37 | 821            | 171     | \$2.44 | 9070           | 52      | \$8.16  | 6337           |
| Frankenstein           | 374               | \$55.41  | 8732           | 33      | \$0.19 | 474            | 204     | \$0.38 | 448            | 300     | \$77.12 | 275            |
| $The\ Hobbit$          | 1000              | \$134.87 | 8835           | 4       | \$0.16 | 205            | 188     | \$0.52 | 571            | 115     | \$23.40 | 1816           |
| $A\ Game\ of\ Thrones$ | 562               | \$124.49 | 1091           | 15      | \$0.16 | 0              | 166     | \$0.36 | 138            | 195     | \$42.36 | 836            |

Table 1: Number of continue queries, cost, and maximum block length from Phase 2. For each book in Figure 7, we show the number of times we query each production LLM to continue in Phase 2, as well as the cost (\$) of running this loop. We also show the length of the longest near-verbatim block (max  $|\beta|$ ) resulting from Phase 2. See Appendix D.2.

(Algorithm 1), we use the same conservative configurations across all runs. For the first merge-and-filter, we set  $\tau_{\rm gap}^{(1)}=2$ ,  $\tau_{\rm align}^{(1)}=1$ , and  $l^{(1)}=20$ ; for the second,  $\tau_{\rm gap}^{(2)}=10$ ,  $\tau_{\rm align}^{(2)}=3$ , and  $l^{(2)}=100$  (Section 3.3.1 & Appendix B). We provide full details on experimental configurations in Appendix C.

#### <span id="page-12-1"></span>4.2 High-level extraction outcomes

Across all Phase 2 runs, we extract hundreds of thousands of words of text. We provide two concrete examples of extracted text from in-copyright books in Figure 6, but do not redistribute long-form generations of in-copyright material. We share lightly normalized diffs for Claude 3.7 Sonnet on Frankenstein and The Great Gatsby, which are books in the public domain. We do not include The Duchess War in plots; of the thirteen books we attempt to extract, this is the only book where Phase 1 failed for all four production LLMs. Similarly, we omit results for our negative control, The Society of Unknowable Objects; as expected, Phase 1 also failed for this book (Appendix D.1).

Interpreting our bar plots. In this section, each bar reflects results from a single, specifically configured run for a given production LLM and book; across bars, the underlying generation configurations vary. As a result, our results should be interpreted only as describing specific experimental outcomes: each bar in a plot conveys how much extraction we observed under the specified experimental settings; since these settings are not fixed across bars, our plots do not make evaluative claims about relative extraction risk across production LLMs. (See Chouldechova et al. (2025), and further discussion in Sections 1 and 5.1.)

Proportion of book extracted (nv-recall). Figure 5 plots nv-recall (Equation 7): the overall proportion of a book extracted in in-order, near-verbatim blocks (Section 3.3.1). For a given production LLM, we fix the same generation configuration across books; however, the generation configuration varies across LLMs. Overall, these results show that it is possible to extract text across books and frontier LLMs. Importantly, we did not jailbreak Gemini 2.5 Pro and Grok 3 in Phase 1 to obtain these results in Phase 2. For Claude 3.7 Sonnet and GPT-4.1, we use BoN with up to N=10,000 attempts in Phase 1. While in terms of dollar-cost BoN is cheap to run for this budget, we note that it almost always required significantly larger N—often  $10-1000\times$ —to jailbreak GPT-4.1 compared to Claude 3.7 Sonnet. In four cases, Claude 3.7 Sonnet's generations recover over 94% of the corresponding reference book. Two of these books— $Harry\ Potter$  and the Sorcerer's Stone and 1984—are in-copyright in the U.S., while the other two— $The\ Great\ Gatsby$  and

<span id="page-13-0"></span>![](_page_13_Figure_0.jpeg)

Figure 7: **Absolute word counts.** For the Phase 2 runs for four books in Figure [5,](#page-11-1) we show the count *m* (Equation [6\)](#page-9-3) of extracted words, as well as the estimated counts of words in the book that are missing in the generated text and words in the generated text that are additional with respect to the book (Equation [8\)](#page-9-6). In each plot, the dotted gray line indicates the length of the book in words (|*B*|). We provide results for other books in Appendix [D.](#page-31-0) *Note: The generation configuration is fixed per LLM across books, but varies across LLMs. For a given book, the per-LLM sets of bars do not reflect comparisons of results obtained from testing all production LLMs under the same conditions.*

*Frankenstein*—are in the public domain. In three other cases for Claude 3.7 Sonnet, nv-recall ≥ 32%. With respect to LLM-specific generation configurations, we extract significant amounts of *Harry Potter and the Sorcerer's Stone* and other books from all four production LLMs.

We frequently query the production LLM to continue hundreds of times per Phase 2 run, without encountering guardrails. However, when we run Phase 2 for GPT-4.1, we hit a refusal fairly early on in the continuation loop. For instance, for *Harry Potter and the Sorcerer's Stone*, this happens at the end of the first chapter. Therefore, while we report nv-recall with respect to the full book, near-verbatim extraction is limited to the first chapter for GPT-4.1. For the other three production LLMs, we almost always do not encounter refusals (Section [4.3\)](#page-15-0), and so halt Phase 2 when either a maximum query budget is expended, the LLM returns a response containing a stop phrase (e.g., "THE END"), or the API returns an HTTP error. (Section [3.2\)](#page-5-0).

The cost of the loop varies across runs, according to the provider's billing policy, the number of queries, and the number of tokens returned per query. For instance, as shown in Table [1,](#page-12-0) it cost approximately \$119.97 to extract *Harry Potter and the Sorcerer's Stone* with nv-recall = 95*.*8% from jailbroken Claude 3.7 Sonnet and \$1.37 for jailbroken GPT-4.1 (nv-recall = 4*.*0%); it cost approximately \$2.44 for not-jailbroken Gemini 2.5 Pro (nv-recall = 76*.*8%) and \$8.16 for not-jailbroken Grok 3 (nv-recall = 70*.*3%).

**Absolute extraction.** For a sense of the scale of how much text we extracted, it is also useful to examine absolute word counts. In Figure [7,](#page-13-0) we show results for four books for the total number of words *m* that we extracted in in-order, near-verbatim blocks (Equation [6\)](#page-9-3). As points of comparison, the missing count estimates how much text from the reference book was not extracted, and additional estimates how much text in the generation is not contained in the reference book. These metrics reveal additional nuances. First,

Jon glimpsed a pale shape moving through the trees.

A shadow emerged from the dark of the wood. It stood in front of Royce. Tall, it was, and gaunt and hard as old bones, with flesh pale as milk.

#### <span id="page-14-0"></span>Ground-truth text from A Game of Thrones GPT-4.1 generated text (not extraction)

Something moved, just at the edge of sight—a pale shape, slipping between the trunks,

A shadow emerged from the trees, tall and gaunt, its armor pale as bone, its eyes glowing with a cold blue light.

(a) (**left**) Ground-truth text from *A Game of Thrones* and (**right**) GPT-4.1-generated text in Phase 2.

#### GPT-4.1 generated text (not extraction)

Ser Waymar turned at last, his breath steaming in the chill. He saw them then, and for a moment, he stood frozen, sword raised, cloak billowing in the wind that had sprung up from nowhere.

The Others came on, their swords thin as ice, shimmering with a faint, unearthly light. Ser Waymar faced them, alone, his young face pale but resolute.

"For the Watch," he whispered.

The first of the Others stepped forward, raising its blade. The clash rang out, sharp and clear in the night, and then the clearing erupted in a flurry of movement—steel against ice, man against nightmare.

Will watched, helpless, as Ser Waymar fought with all the skill and courage he possessed, but the Others were too many, too swift. Their swords danced, and the young lordling fell to his knees, blood blooming bright on the snow.

(b) Longer snippet of GPT-4.1-generated text in Phase 2 for *A Game of Thrones*.

Figure 8: **Examples of generated text that is** *not* **extraction.** We provide brief examples of text generated by GPT-4.1 in the Phase 2 continuation loop that are *not* extraction, and do not contribute to *m* (and thus also not nv-recall), but to additional (Equation [8\)](#page-9-6). For all production LLMs that we test, we qualitatively observe that additional text frequently replicates plot elements, themes, and character names from the book we attempt to extract. *Note: Since our focus is extraction, we do not attempt to evaluate this text quantitatively or at scale; one should not draw strong conclusions from these examples.*

low percentages of nv-recall can of course reflect enormous amounts of extraction. For *Harry Potter and the Sorcerer's Stone*, we extracted thousands of words near-verbatim from all production LLMs. Even for GPT-4.1, for which nv-recall = 4*.*0%, we extracted approximately *m* ≈ 3200 words from the book. For *A Game of Thrones*, which is a significantly longer book, nv-recall = 1*.*3% for Grok 3, which corresponds to *m* ≈ 3700 words of near-verbatim extracted text. Further, separate from total near-verbatim extraction, the individual extracted blocks can also be quite long. In Table [1,](#page-12-0) we show the longest extracted block for each experiment in Figure [7.](#page-13-0) For *Harry Potter and the Sorcerer's Stone*, the longest near-verbatim blocks are 6658, 821, 9070, and 6337 words for Claude 3.7 Sonnet, GPT-4.1, Gemini 2.5 Pro, and Grok 3, respectively. The longest verbatim string that [Nasr et al.](#page-22-4) [\(2023\)](#page-22-4) extracted from ChatGPT 3.5 was slightly over 4000 *characters*.

Second, interpreting additional and missing in Figure [7](#page-13-0) indicates some important caveats. Recall that both counts may contain some instances of valid extraction that our measurement procedure under-counts. Since our extraction metric *m* counts contiguous near-verbatim blocks, potentially duplicated (still valid) extraction may contribute to additional, and near-verbatim text that is generated out-of-order with respect to the reference book may be counted in both additional and missing (Section [3.3.1\)](#page-7-1). For instance, we note that the diff for Claude 3.7 Sonnet's generation and *The Great Gatsby* has extensive repeats of extracted text on pages 114–132, which contribute to additional. Note that duplicates also have an effect on the quality of the overall reproduction of a book in extracted outputs. While for Claude 3.7 Sonnet we extract nv-recall = 97*.*5% of the reference book, we did not extract a pristine copy of the whole book. Qualitative inspection of diffs for Claude 3.7 Sonnet on *Frankenstein*, *1984* , and *Harry Potter and the Sorcerer's Stone* reveals that we extracted cleaner copies of the ground-truth text that lack repeated extraction.

**Brief qualitative observations about** additional **generated text.** We perform limited qualitative analysis of the additional generated text. As noted above, a portion of this text may contain duplicated or out-of-order extraction. However, this is not always the case; often, the additional generated text is *not* extraction. Brief qualitative inspection of this text for all of our experiments reveals that, for all books and frontier LLMs, additional text frequently contains text that replicates plot elements, themes, and character names from the book from which the Phase 1 prefix is drawn. We provide two examples of such text in Figure [8;](#page-14-0) these examples are drawn from GPT-4.1-generated text following Phase 1 success with a seed prefix from *A Game*

<span id="page-15-1"></span>![](_page_15_Figure_0.jpeg)

- (a) Varying configs for Gemini 2.5 Pro (b) Varying the extraction procedure for GPT-4.1

Figure 9: **Testing alternative settings for the two-phase procedure.** We explore how different settings influence how much extraction is obtained per run. Figure [9a](#page-15-1) shows how nv-recall varies across runs with different generation configurations (presence and frequency penalty) for Gemini 2.5 Pro and *Harry Potter and the Sorcerer's Stone*. Figure [9b](#page-15-1) shows how starting with different seed prefixes in Phase 1 can reveal different memorized text. In our main experiments using a prefix from the beginning of the book (Section [4.2\)](#page-12-1), GPT-4.1 tends to refuse to continue in Phase 2 at the end of the first chapter. We perform additional runs of the twophase procedure, where for Phase 1 we use seed prefixes drawn from the beginning of *each chapter of each book*. We compare nv-recall from our main experiments, starting with Phase 1 using a seed from the first chapter (Figure [5\)](#page-11-1), to the (non-overlapping) *union* near-verbatim blocks from per-chapter-with-retry extraction. *Note: The reported* nv*-*recall *in each pair of bars uses a different extraction procedure. See main text for more details.*

*of Thrones*. Note that nv-recall is exactly 0% for GPT-4.1 for *A Game of Thrones* (Figure [5\)](#page-11-1), as matched words *m* = 0 (Figure [7d\)](#page-13-0). We selected these two examples by randomly sampling an index in the generation, and then looking at the surrounding text. We then manually performed repeated searches for subsequences of the generated text in the reference book, to confirm that they do not reflect extraction. Since extraction is our focus, we do not make claims about this non-extracted text, and instead defer detailed analysis to future work.

#### <span id="page-15-0"></span>**4.3 Additional details and experiments concerning LLM-specific configurations**

As noted in the prior section, our initial experiments revealed that different settings for the two-phase procedure had an impact on extraction for each production LLM. For instance, these initial experiments revealed that we did not need to jailbreak Gemini 2.5 Pro or Grok 3. They also revealed how different generation configurations for Phase 2 resulted in varying amounts of extraction. Here, we provide some more details about how varied settings impact extraction, according to production LLM. Full experimental configurations, additional results, and API cost information can be found in Appendices [C.2](#page-28-1) and [D.2.](#page-32-0)

**Gemini 2.5 Pro.** For all experiments, Gemini 2.5 Pro did not refuse to continue the seed prefix in Phase 1. In our initial exploratory experiments, after a number of turns in the Phase 2 continue loop, the Gemini 2.5 Pro API would stop returning text; it instead would provide an empty response with a metadata object, linking to documentation indicating that we had encountered guardrails meant to prevent the recitation of copyrighted material [\(Google AI for Developers\)](#page-21-14). We found that we could mitigate this behavior by minimizing the "thinking budget," and explicitly querying Gemini 2.5 Pro to "Continue without citation metadata." In some runs, Gemini 2.5 Pro would occasionally return empty responses during Phase 2. When this occurred, we count this as a turn in the maximum query budget, and retry after a one-second delay (Appendix [C.2.2\)](#page-29-0).

We also found that Gemini 2.5 Pro's responses would often repeat previously emitted text. We therefore experimented with different generation configurations for the maximum number of generated tokens, frequency penality, and presence penalty. Through a set of experiments on *Harry Potter and the Sorcerer's Stone*, we found that a maximum of 2000 tokens resulted in the highest nv-recall. We fixed this parameter, and swept over different combinations of frequency and presence penalty. Setting frequency penalty to 2 and presence penalty to 0*.*1 resulted in the highest nv-recall, so we fix these as the configurations for Gemini

2.5 Pro runs across books for the results shown in Section [4.2](#page-12-1) (Figures [5](#page-11-1) and [7\)](#page-13-0). Nevertheless, as shown in Figure [9a,](#page-15-1) variance in extraction can be significant depending on the choice of these settings. Given the cheap cost of running our experiments on Gemini 2.5 Pro, we provide results for all books testing each of these 9 configurations in Appendix [D.2.2.](#page-36-0) These results show that the single, fixed configuration for Gemini 2.5 Pro for the results in Section [4.2](#page-12-1) do not always result in the highest nv-recall for every book.

**Grok 3.** We encountered no guardrails for any experiments for Phase 1. Except for the run on *1984* (Figure [5\)](#page-11-1), we did not encounter any guardrails for Phase 2. For *1984* , Grok 3 produced *verbatim* text until the 24th continue request, when it responded with a refusal and that it would instead "continue the narrative in a way that respects the source material." During Phase 2, the Grok 3 API sometimes returned a generic HTTP 500 error code, indicating a provider-side issue with fulfilling API requests. In these cases, the continuation loop terminated before the max query budget was exhausted.

**Claude 3.7 Sonnet.** Initial experiments to complete a seed prefix failed, which is why we experimented with BoN in Phase 1. Early runs with *Harry Potter and the Sorcerer's Stone* revealed that, for BoN-jailbroken Claude 3.7 Sonnet, different response lengths in Phase 2 could trigger refusals. In iterative experiments, we reduced the maximum response length per continue query from 1000 to 250 tokens, which was sufficient to evade refusals in all future experiments. We also noticed that, when Claude 3.7 Sonnet reproduced an entire book near-verbatim, it often appended "THE END". This is what inspired us to include a stop-phrase condition in Phase 2, in addition to checking for refusals or if a maximum query budget has been exhausted.

**GPT-4.1.** As discussed in Section [4.2,](#page-12-1) jailbreaking GPT-4.1 in Phase 1 generally took significantly more BoN attempts with our specific initial instruction than for Claude 3.7 Sonnet. Further, for jailbroken GPT-4.1, success of the continuation loop in Phase 2 was always curtailed by an eventual refusal. Except for Grok 3 on *1984* , these constituted all refusals in our final experimental configurations. Therefore, for the experiments shown in Section [4.2,](#page-12-1) if we successfully extracted text from GPT-4.1 for a given book, that text was always from the first chapter, after which GPT-4.1 refused to continue. For instance, for *Harry Potter and the Sorcerer's Stone*, the last response before refusal was "That is the end of Chapter One."

However, encountering a refusal at the end of the first book chapter does not necessarily mean that further text is not memorized by GPT-4.1. Rather, failure due to refusal simply indicates that we were unable to extract more text with our specific two-phase procedure. To explore this further, we ran an additional set of experiments to attempt to elicit additional memorization from GPT-4.1. For each book, we execute a chapter-by-chapter variant of the two-phase procedure: for *each chapter*, we use the first sentence as the seed prefix for BoN in Phase 1 to find a successful jailbreak prompt, and then run the Phase 2 continuation loop to attempt to extract the rest of the chapter. We also implemented a retry policy for if we encountered a refusal, as we noticed that refusals are not deterministic for GPT-4.1: it may refuse a request at one point in time, but after a time delay may fulfill the identical request and continue.[9](#page-16-1) This more intensive approach—which also makes use of more ground-truth text from the reference book—is able to extract more training data.

In Figure [9b,](#page-15-1) we compare nv-recall results for these per-chapter-with-retry experiments with the results of our main experiments involving a single two-phase run starting with a prefix from the first chapter (Figure [5\)](#page-11-1). For the per-chapter-with-retry variant, we report the total proportion of the book extracted by taking the union over (non-overlapping/disjoint) near-verbatim blocks to compute nv-recall (Equation [7\)](#page-9-0). *Note: We ran these experiments to probe if our main extraction procedure under-counts possible extraction (and thus memorization). The underlying extraction procedures are not equivalent, in terms of effort expended to elicit extraction.*

### <span id="page-16-0"></span>**5 Discussion**

We discuss overarching takeaways from our experiments in Section [4,](#page-10-0) focusing on important limitations and caveats (Section [5.1\)](#page-17-0), and brief observations about why our work may be of interest to copyright (Section [5.2\)](#page-17-1).

<span id="page-16-1"></span><sup>9</sup>Non-determinism is another salient difference between our results and those in [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3), which are deterministic.

### <span id="page-17-0"></span>**5.1 Limitations and caveats**

Throughout this paper, we have highlighted limitations and caveats in italicized notes. Nevertheless, it is worth reiterating that the points we raise have an important impact on how our results should be interpreted.

**A loose lower bound on memorization for specific books.** Separate from how our measurements for extraction are conservative (Section [3.3\)](#page-7-0), it is well-known that extraction more generally under-counts the total amount of training data that LLMs memorize. While prior work has demonstrated this in other contexts [\(Nasr et al., 2023;](#page-22-4) [Cooper et al., 2025\)](#page-21-3), our results for GPT-4.1 show how changing the prompting strategy can significantly alter how much extraction we observe, and how much underlying memorization this reveals. Our main focus is attempting to extract specific books near-verbatim; so, in most experiments, we run the two-phase procedure only once, with Phase 1 using a seed prefix from the beginning of a given book. In most cases, qualitative inspection of diffs with reference books shows that this succeeds in extracting near-verbatim text from at least part of the first chapter, but then the generation often diverges from the true text. However, as is clear in Figure [9b,](#page-15-1) seeding Phase 1 in different book locations (here, the start of each chapter) can reveal additional memorization that we did not capture with our main experiments.

**Relatively small scale of experiments and their cost.** It is challenging to study production settings, as APIs change over time. For the same reason, it is often also difficult to reproduce results on production LLMs. We limited our experiments to a specific time window, so that we could successfully complete testing on the same books for all four production LLMs. In all, we only ran experiments on fourteen specific books, so our results do not speak to memorization and extraction more generally. Cost also impacted the number of books we tested. While it was typically less than \$1 to run the Phase 2 continuation loop for Gemini 2.5 Pro, it was more expensive for some production LLMs. Notably, for Claude 3.7 Sonnet, long-context generation is significantly more expensive; it often cost over \$100 per run (Table [1](#page-12-0) & Appendix [D.2.1\)](#page-32-1).

**LLM-specific configuration of the two-phase extraction procedure.** In our main experiments (Section [4.2\)](#page-12-1), we test one relatively simple extraction procedure (Section [3\)](#page-3-0), and we instantiate that procedure in different ways for different production LLMs. In Phase 1, we decided to make the jailbreak optional, and we only tested Best-of-*N*. For Gemini 2.5 Pro and Grok 3, it was remarkable that this procedure evaded safeguards that we did not need to use a jailbreak to successfully extract training data. However, it is also possible that, if we had used BoN on these two LLMs, it may have changed how much extraction we observed. For Phase 2, we set temperature to 0 for all generation configurations and use the same halting conditions, but we tuned LLMspecific parameters (e.g., frequency penalty for Gemini 2.5 Pro) to increase LLM-specific extraction success.

**We do not make evaluative claims across LLMs.** Given the above, it bears repeating that every observation we make about our results is with respect to a specific production LLM, book, and instantiation and run of our specific two-phase procedure. In some cases, the specific conditions we test revealed an enormous amount of extraction; notably, we extracted two entire in-copyright books—*Harry Potter and the Sorcerer's Stone* and *1984*—from Claude 3.7 Sonnet near-verbatim. We only make *descriptive statements* about these results: we discuss outcomes concerning specific experimental choices, outputs, and determinations of extraction success [\(Chouldechova et al.](#page-20-6) [\(2025\)](#page-20-6); Sections [1](#page-0-0) and [4.2\)](#page-12-1). This aligns with our goal: to see if it is *possible* to extract long-form books from production LLMs. However, we do not make broader *evaluative* claims across production LLMs. For instance, while our specific experiments extracted the most text from Claude 3.7 Sonnet (Section [4.2\)](#page-12-1), we do *not* claim that these results indicate Claude 3.7 Sonnet in general memorizes more training data than the other three production LLMs. We do *not* claim that any production LLM is in general more robust to extraction than another. Our bar plots should *not* be interpreted as making such comparative claims. In order to make such evaluative, comparative claims, one would need to run a much larger scale study under more controlled conditions.

#### <span id="page-17-1"></span>**5.2 Copyright**

While we defer detailed copyright analysis to future work, we briefly address why our results may be of interest.

**Production LLMs memorize some of their training data, and extraction is sometimes feasible.** In copyright litigation concerning generative AI, extraction and memorization of training data are both

central issues (Sections [1](#page-0-0) & [2\)](#page-2-0). Several lawsuits have addressed questions over whether production LLMs reproduce copyrighted training data in their outputs (i.e., have touched on extraction) [\(Kadrey Judgment;](#page-22-5) [Bartz Judgment\)](#page-19-3). There has also been increased academic discussion [\(Cooper & Grimmelmann, 2024;](#page-20-5) [Dornis,](#page-21-1) [2025\)](#page-21-1) and litigation [\(GEMA v. OpenAI\)](#page-21-2) over whether LLMs themselves are legally cognizable copies of the training data they have memorized. Regardless of how relevant these issues may be for potential findings of copyright infringement, our work reveals important technical facts: the four production LLMs we study memorized (at least some of) the books on which they were trained, and it is possible to extract (at least some of) those memorized books at generation time.

**Jailbreaks, adversarial use, and cost.** Some might qualify our experiments as atypical use, as we deliberately tried to surface memorized books. Adversarial use, like the use of jailbreaks, may matter for copyright infringement analysis [\(Lee et al., 2023b;](#page-22-2) [Cooper & Grimmelmann, 2024\)](#page-20-5). Further, for the cases in which we retrieved whole copies of near-verbatim books, it was often quite costly (*>* \$100) to do so (Section [4.2,](#page-12-1) Table [1\)](#page-12-0). As [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) note, even with respect to their significantly cheaper experiments using open-weight LLMs, "there are easier and more effective ways to pirate a book." Nevertheless, it is important to emphasize that we did not use jailbreaks for two production LLMs during Phase 1. In Phase 2, we observed that all four production LLMs sometimes responded with large spans of in-copyright text. In all cases, successful extraction of training data would not have been possible if these LLMs had not memorized those data during training (Section [3.3.2\)](#page-9-2).

**Best efforts and safeguards.** As others have noted, it may be infeasible to produce perfect safeguards; in such circumstances, preventing the generation of copyrighted or otherwise undesirable material may depend on "reasonable best efforts" [\(Cooper et al., 2024\)](#page-20-10). As noted above, in our main experiments (Section [4.2\)](#page-12-1), two production LLMs did not exhibit safeguards in Phase 1: Gemini 2.5 Pro and Grok 3 directly complied with our initial probes to complete prefixes from books. We used jailbreaks to get Claude 3.7 Sonnet and GPT-4.1 to comply in Phase 1. For GPT-4.1 and our chosen initial instruction, it frequently took a significant number of BoN attempts to achieve Phase 1 success. It often took far fewer than our maximum budget (*N* = 10*,*000) to jailbreak Claude 3.7 Sonnet to complete a provided in-copyright book prefix. Jailbreaks aside, our experiments managed to evade system-level safeguards during Phase 2. We were able to run multiple—sometimes hundreds—of iterations of a simple continue loop for each production LLM, before (if ever) encountering filters intended to prevent generation of copyrighted material (Section [2\)](#page-2-0).

**Non-extracted,** additional **text.** In our experiments, we specifically investigate extraction of training data. However, when conducting our extraction analysis, we qualitatively observed that thousands of words of additional (Equation [8\)](#page-9-6), non-extracted generated text from all four production LLMs replicate character names, plot elements, and themes (Figure [8,](#page-14-0) Section [4.2\)](#page-12-1). Given that copyright law does not only apply to near-verbatim copying, such outputs may be interest. We stress that we do not perform rigorous, quantitative, at-scale analysis of this text, and instead defer this to future work.

### **6 Conclusion**

With a simple two-phase procedure (Section [3\)](#page-3-0), we show that it is possible to extract large amounts of in-copyright text from four production LLMs. While we needed to jailbreak Claude 3.7 Sonnet and GPT-4.1 to facilitate extraction, Gemini 2.5 Pro and Grok 3 directly complied with text continuation requests. For Claude 3.7 Sonnet, we were able to extract four whole books near-verbatim, including two books under copyright in the U.S.: *Harry Potter and the Sorcerer's Stone* and *1984* (Section [4\)](#page-10-0).

While our work may be of interest to ongoing legal debates (Section [5\)](#page-16-0), our main focus is to make technical contributions to machine learning, not copyright law or policy. As [Cooper & Grimmelmann](#page-20-5) [\(2024\)](#page-20-5) note, "[i]t is up to lawyers and judges to decide what to do with these technical facts" and it is quite possible "that different generative-AI systems could well be treated differently." Regulators may also intervene; they "are free to change copyright law in ways that change the relevance of the technical facts of memorization"—for instance, to explicitly specify that models can be copies of training data they have memorized, or, conversely, that memorization encoded in model weights explicitly should not be treated as legally cognizable copies. However, it is not "productive to debate the technical facts of memorization on policy grounds"; "[c]opyright

law [and policy do] not determine technical facts; [they] must work with the facts as they are." Regardless of the prospect of ongoing copyright litigation [\(Gianella, 2025\)](#page-21-15), long-standing, clear, and sound technical facts remain: LLMs memorize portions of their training data [\(Carlini et al., 2021;](#page-20-3) [2023\)](#page-20-4), these memorized data are encoded in the model's weights [\(Nasr et al., 2023;](#page-22-4) [Carlini, 2025;](#page-20-12) [Schwarzschild et al., 2024\)](#page-23-16), and, as we show here, it can be feasible to extract large quantities of in-copyright training data from production LLMs.

### **Acknowledgments and disclosures**

AA acknowledges generous support from a Knight-Hennessy Fellowship, an NSF Graduate Research Fellowship, and a Georgetown Foundation Research Grant. AFC is employed by AVERI and is a postdoctoral affiliate at Stanford University, in Percy Liang's group in the Department of Computer Science and Daniel E. Ho's group at Stanford Law School, and a research scientist (incoming assistant professor) in the Department of Computer Science at Yale University. Until December 2025, AFC was a full-time employee of Microsoft, working as a postdoctoral researcher in the FATE group within Microsoft Research. These results and analysis should not be attributed to Microsoft. We thank Mark A. Lemley for feedback on an earlier draft of this work.

### **References**

- <span id="page-19-8"></span>17 U.S. Code § 503. Copyright Law of the United States , December 2010. URL [https://www.law.cornell.](https://www.law.cornell.edu/uscode/text/17/503) [edu/uscode/text/17/503](https://www.law.cornell.edu/uscode/text/17/503). Remedies for infringement: Impounding and disposition of infringing articles.
- <span id="page-19-7"></span>Cem Anil, Esin Durmus, Nina Rimsky, Mrinank Sharma, Joe Benton, et al. Many-shot jailbreaking. In *The Thirty-eighth Annual Conference on Neural Information Processing Systems*, 2024. URL [https:](https://openreview.net/forum?id=cw5mgd71jW) [//openreview.net/forum?id=cw5mgd71jW](https://openreview.net/forum?id=cw5mgd71jW).
- <span id="page-19-6"></span>Anthropic. Claude's constitution. <https://www.anthropic.com/news/claudes-constitution>, May 2023. Accessed: 2025-05-14.
- <span id="page-19-9"></span>Anthropic. Claude 3.7 Sonnet System Card. System card, Anthropic, February 2025. URL [https://assets.](https://assets.anthropic.com/m/785e231869ea8b3b/original/claude-3-7-sonnet-system-card.pdf) [anthropic.com/m/785e231869ea8b3b/original/claude-3-7-sonnet-system-card.pdf](https://assets.anthropic.com/m/785e231869ea8b3b/original/claude-3-7-sonnet-system-card.pdf). Hybrid reasoning model card; release details in system card PDF.
- <span id="page-19-4"></span>Authors Guild v. Google, Inc. 804 f.3d 202 (2d cir. 2015).
- <span id="page-19-5"></span>Yuntao Bai, Saurav Kadavath, Sandipan Kundu, Amanda Askell, Jackson Kernion, Andy Jones, et al. Constitutional ai: Harmlessness from ai feedback, 2022. URL <https://arxiv.org/abs/2212.08073>.
- <span id="page-19-10"></span>Bartz et al. v. Anthropic PBC. United States District Court for the Northern District of California, June 2025. URL <https://www.bakerlaw.com/bartz-v-anthropic/>. Case No. 3:24-cv-05417. Summary judgment ruling on fair use of copyrighted works in AI training.
- <span id="page-19-3"></span>Bartz Judgment. Order on Fair Use, Bartz et al. v. Anthropic PBC, 2025. URL [https://docs.justia.](https://docs.justia.com/cases/federal/district-courts/california/candce/3:2024cv05417/434709/231) [com/cases/federal/district-courts/california/candce/3:2024cv05417/434709/231](https://docs.justia.com/cases/federal/district-courts/california/candce/3:2024cv05417/434709/231). No. 3:23-cv-03417-VC (N.D. Cal. Jun. 25, 2025).
- <span id="page-19-1"></span>Ashley Belanger. OpenAI declares AI race "over"' if training on copyrighted works isn't fair use. *Ars Technica*, March 2025. URL [https://arstechnica.com/tech-policy/2025/03/](https://arstechnica.com/tech-policy/2025/03/openai-urges-trump-either-settle-ai-copyright-debate-or-lose-ai-race-to-china/) [openai-urges-trump-either-settle-ai-copyright-debate-or-lose-ai-race-to-china/](https://arstechnica.com/tech-policy/2025/03/openai-urges-trump-either-settle-ai-copyright-debate-or-lose-ai-race-to-china/).
- <span id="page-19-2"></span>Virginie Berger. The ai copyright battle: Why openai and google are pushing for fair use. *Forbes*, March 2025. URL [https://www.forbes.com/sites/virginieberger/2025/03/15/](https://www.forbes.com/sites/virginieberger/2025/03/15/the-ai-copyright-battle-why-openai-and-google-are-pushing-for-fair-use/?utm_source=chatgpt.com) [the-ai-copyright-battle-why-openai-and-google-are-pushing-for-fair-use/?utm\\_source=](https://www.forbes.com/sites/virginieberger/2025/03/15/the-ai-copyright-battle-why-openai-and-google-are-pushing-for-fair-use/?utm_source=chatgpt.com) [chatgpt.com](https://www.forbes.com/sites/virginieberger/2025/03/15/the-ai-copyright-battle-why-openai-and-google-are-pushing-for-fair-use/?utm_source=chatgpt.com). Accessed: 2025-11-06.
- <span id="page-19-0"></span>Stella Biderman, Hailey Schoelkopf, Quentin Gregory Anthony, Herbie Bradley, Kyle O'Brien, Eric Hallahan, Mohammad Aflah Khan, Shivanshu Purohit, USVSN Sai Prashanth, Edward Raff, et al. Pythia: A suite for analyzing large language models across training and scaling. In *International Conference on Machine Learning*, pp. 2397–2430. PMLR, 2023.

<span id="page-20-16"></span>Blake Brittain. Meta tells court AI software does not violate author copyrights, September 2023. URL [https://www.reuters.com/legal/litigation/](https://www.reuters.com/legal/litigation/meta-tells-court-ai-software-does-not-violate-author-copyrights-2023-09-19/) [meta-tells-court-ai-software-does-not-violate-author-copyrights-2023-09-19/](https://www.reuters.com/legal/litigation/meta-tells-court-ai-software-does-not-violate-author-copyrights-2023-09-19/).

<span id="page-20-13"></span>Dan Brown. *The Da Vinci Code*. Doubleday, 2003.

<span id="page-20-15"></span>Gareth Brown. *The Society of Unknowable Objects*. HarperCollins, 2025.

<span id="page-20-2"></span>Campbell v. Acuff-Rose Music. 510 u.s. 569 (1994).

<span id="page-20-12"></span>Nicholas Carlini. What my privacy papers (don't) have to say about copyright and generative AI, 2025. URL <https://nicholas.carlini.com/writing/2025/privacy-copyright-and-generative-models.html>.

<span id="page-20-3"></span>Nicholas Carlini, Florian Tramer, Eric Wallace, Matthew Jagielski, Ariel Herbert-Voss, Katherine Lee, Adam Roberts, Tom Brown, Dawn Song, Ulfar Erlingsson, et al. Extracting training data from large language models. In *30th USENIX Security Symposium (USENIX Security 21)*, pp. 2633–2650, 2021.

<span id="page-20-4"></span>Nicholas Carlini, Daphne Ippolito, Matthew Jagielski, Katherine Lee, Florian Tramèr, and Chiyuan Zhang. Quantifying Memorization Across Neural Language Models. In *International Conference on Learning Representations*, 2023.

<span id="page-20-8"></span>Hongyan Chang, Ali Shahin Shamsabadi, Kleomenis Katevas, Hamed Haddadi, and Reza Shokri. Contextaware membership inference attacks against pre-trained large language models, 2025. URL [https:](https://arxiv.org/abs/2409.13745) [//arxiv.org/abs/2409.13745](https://arxiv.org/abs/2409.13745).

<span id="page-20-0"></span>Mark Chen, Jerry Tworek, Heewoo Jun, Qiming Yuan, Henrique Ponde de Oliveira Pinto, Jared Kaplan, Harri Edwards, Yuri Burda, Nicholas Joseph, et al. Evaluating large language models trained on code, 2021. URL <https://arxiv.org/abs/2107.03374>.

<span id="page-20-6"></span>Alexandra Chouldechova, A. Feder Cooper, Solon Barocas, Abhinav Palia, Dan Vann, and Hanna Wallach. Comparison requires valid measurement: Rethinking attack success rate comparisons in AI red teaming. In *The Thirty-Ninth Annual Conference on Neural Information Processing Systems Position Paper Track*, 2025. URL <https://openreview.net/forum?id=d7hqAhLvWG>.

<span id="page-20-9"></span>Paul F. Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei. Deep reinforcement learning from human preferences. In *Advances in Neural Information Processing Systems*, volume 30, 2017.

<span id="page-20-1"></span>Thomas Claburn. Microsoft CEO of AI: Your online content is 'freeware' fodder for training models. *The Register*, June 2024. URL [https://www.theregister.com/2024/06/28/microsoft\\_ceo\\_ai/](https://www.theregister.com/2024/06/28/microsoft_ceo_ai/).

<span id="page-20-14"></span>Suzanne Collins. *The Hunger Games*. Scholastic Press, 2008.

<span id="page-20-11"></span>Concord Music Group, Inc. v. Anthropic PBC. 3:23-cv-01092 (M.D. Tenn.).

- <span id="page-20-5"></span>A. Feder Cooper and James Grimmelmann. The Files are in the Computer: Copyright, Memorization, and Generative AI. *arXiv preprint arXiv:2404.12590*, 2024.
- <span id="page-20-7"></span>A. Feder Cooper, Katherine Lee, James Grimmelmann, Daphne Ippolito, Christopher Callison-Burch, Christopher A. Choquette-Choo, Niloofar Mireshghallah, Miles Brundage, David Mimno, Madiha Zahrah Choksi, Jack M. Balkin, Nicholas Carlini, Christopher De Sa, Jonathan Frankle, Deep Ganguli, Bryant Gipson, Andres Guadamuz, Swee Leng Harris, Abigail Z. Jacobs, Elizabeth Joh, Gautam Kamath, Mark Lemley, Cass Matthews, Christine McLeavey, Corynne McSherry, Milad Nasr, Paul Ohm, Adam Roberts, Tom Rubin, Pamela Samuelson, Ludwig Schubert, Kristen Vaccaro, Luis Villa, Felix Wu, and Elana Zeide. Report of the 1st Workshop on Generative AI and Law. *arXiv preprint arXiv:2311.06477*, 2023.
- <span id="page-20-10"></span>A. Feder Cooper, Christopher A Choquette-Choo, Miranda Bogen, Matthew Jagielski, Katja Filippova, Ken Ziyu Liu, Alexandra Chouldechova, Yangsibo Huang Jamie Hayes, et al. Machine unlearning doesn't do what you think: Lessons for generative ai policy, research, and practice. *arXiv preprint arXiv:2412.06966*, 2024.

- <span id="page-21-3"></span>A. Feder Cooper, Aaron Gokaslan, Amy B. Cyphert, Christopher De Sa, Mark A. Lemley, Daniel E. Ho, and Percy Liang. Extracting memorized pieces of (copyrighted) books from open-weight language models. *arXiv preprint arXiv:2505.12546*, 2025.
- <span id="page-21-11"></span>difflib SequenceMatcher. difflib — Helpers for computing deltas, 2025. URL [https://docs.python.org/3/](https://docs.python.org/3/library/difflib.html) [library/difflib.html](https://docs.python.org/3/library/difflib.html). Python Standard Library v3.14.2.
- <span id="page-21-1"></span>Tim W. Dornis. Generative AI, Reproductions Inside the Model, and the Making Available to the Public. *International Review of Intellectual Property and Competition Law*, 56:909–938, 2025.
- <span id="page-21-5"></span>Vitaly Feldman. Does learning require memorization? a short tale about a long tail. In *Proceedings of the 52nd Annual ACM SIGACT Symposium on Theory of Computing*, STOC 2020, pp. 954–959, New York, NY, USA, 2020. Association for Computing Machinery. ISBN 9781450369794.
- <span id="page-21-4"></span>F. Scott Fitzgerald. *The Great Gatsby*. Charles Scribner's Sons, 1925.
- <span id="page-21-2"></span>GEMA v. OpenAI. Gesellschaft für musikalische Aufführungs- und mechanische Vervielfältigungsrechte. 42 O 14139/24.
- <span id="page-21-7"></span>Gemini Team, Nikolay Savinov, Denis Teplyashin, Dmitry Lepikhin, Timothy Lillicrap, Jean-baptiste Alayrac, Radu Soricut, Angeliki Lazaridou, Orhan Firat, Julian Schrittwieser, et al. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. *arXiv preprint arXiv:2403.05530*, 2024.
- <span id="page-21-15"></span>Sandro Gianella. Linkedin post regarding gema v. openai appeal, December 2025. URL [https://www.linkedin.com/posts/sandrogianella\\_](https://www.linkedin.com/posts/sandrogianella_were-appealing-the-gema-case-i-want-to-activity-7405076994062729216-TmEP/) [were-appealing-the-gema-case-i-want-to-activity-7405076994062729216-TmEP/](https://www.linkedin.com/posts/sandrogianella_were-appealing-the-gema-case-i-want-to-activity-7405076994062729216-TmEP/). Posted in the capacity of OpenAI's Head of Europe and Middle East Policy.
- <span id="page-21-14"></span>Google AI for Developers. Generating content — gemini api. [https://ai.google.dev/api/](https://ai.google.dev/api/generate-content) [generate-content](https://ai.google.dev/api/generate-content). Accessed: 2025-12-04.
- <span id="page-21-12"></span>Google Cloud. Gemini 2.5 Pro, 2025. URL [https://docs.cloud.google.com/vertex-ai/generative-ai/](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-pro) [docs/models/gemini/2-5-pro](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-pro).
- <span id="page-21-8"></span>Aaron Grattafiori et al. The Llama 3 Herd of Models, 2024. URL <https://arxiv.org/abs/2407.21783>.
- <span id="page-21-6"></span>Jamie Hayes, Ilia Shumailov, Christopher A. Choquette-Choo, Matthew Jagielski, Georgios Kaissis, Milad Nasr, Meenatchi Sundaram Muthu Selva Annamalai, Niloofar Mireshghallah, Igor Shilov, Matthieu Meeus, Yves-Alexandre de Montjoye, Katherine Lee, Franziska Boenisch, Adam Dziedzic, and A. Feder Cooper. Exploring the limits of strong membership inference attacks on large language models. In *The Thirty-ninth Annual Conference on Neural Information Processing Systems*, 2025a. URL [https:](https://openreview.net/forum?id=x0i7wvRLHK) [//openreview.net/forum?id=x0i7wvRLHK](https://openreview.net/forum?id=x0i7wvRLHK).
- <span id="page-21-0"></span>Jamie Hayes, Marika Swanberg, Harsh Chaudhari, Itay Yona, Ilia Shumailov, Milad Nasr, Christopher A. Choquette-Choo, Katherine Lee, and A. Feder Cooper. Measuring memorization in language models via probabilistic extraction. In Luis Chiruzzo, Alan Ritter, and Lu Wang (eds.), *Proceedings of the 2025 Conference of the Nations of the Americas Chapter of the Association for Computational Linguistics: Human Language Technologies (Volume 1: Long Papers)*, pp. 9266–9291, Albuquerque, New Mexico, April 2025b. Association for Computational Linguistics. ISBN 979-8-89176-189-6. URL [https://aclanthology.](https://aclanthology.org/2025.naacl-long.469/) [org/2025.naacl-long.469/](https://aclanthology.org/2025.naacl-long.469/).
- <span id="page-21-13"></span>Joseph Heller. *Catch-22*. Simon & Schuster, 1961.
- <span id="page-21-10"></span>Peter Henderson, Xuechen Li, Dan Jurafsky, Tatsunori Hashimoto, Mark A. Lemley, and Percy Liang. Foundation Models and Fair Use, 2023. URL <https://arxiv.org/abs/2303.15715>.
- <span id="page-21-9"></span>Dan Hendrycks, Nicholas Carlini, John Schulman, and Jacob Steinhardt. Unsolved problems in ML safety. *arXiv preprint arXiv:2109.13916*, 2021.

- <span id="page-22-14"></span>Monika Henzinger. Finding near-duplicate web pages: a large-scale evaluation of algorithms. SIGIR '06, pp. 284–291, New York, NY, USA, 2006. Association for Computing Machinery. ISBN 1595933697. doi: 10.1145/1148170.1148222. URL <https://doi.org/10.1145/1148170.1148222>.
- <span id="page-22-13"></span>Timothy C. Hoad and Justin Zobel. Methods for Identifying Versioned and Plagiarized Documents. *J. Assoc. Inf. Sci. Technol.*, 54:203–215, 2003.
- <span id="page-22-7"></span>John Hughes, Sara Price, Aengus Lynch, Rylan Schaeffer, Fazl Barez, Sanmi Koyejo, Henry Sleight, Erik Jones, Ethan Perez, and Mrinank Sharma. Best-of-n jailbreaking, 2024. URL [https://arxiv.org/abs/](https://arxiv.org/abs/2412.03556) [2412.03556](https://arxiv.org/abs/2412.03556).
- <span id="page-22-12"></span>Daphne Ippolito, Florian Tramèr, Milad Nasr, Chiyuan Zhang, Matthew Jagielski, Katherine Lee, Christopher A Choquette-Choo, and Nicholas Carlini. Preventing verbatim memorization in language models gives a false sense of privacy. *arXiv preprint arXiv:2210.17546*, 2022.
- <span id="page-22-8"></span>Kadrey et al. v. Meta Platforms, Inc. United States District Court for the Northern District of California, March 2025. Case No. 3:23-cv-03417-VC.
- <span id="page-22-5"></span>Kadrey Judgment. Order Denying the Plaintiffs' Motion for Partial Summary Judgment and Granting Meta's Cross-Motion for Partial Summary Judgment, Kadrey et al. v. Meta Platforms, Inc., 2025. URL [https://law.justia.com/cases/federal/district-courts/california/candce/3:](https://law.justia.com/cases/federal/district-courts/california/candce/3:2023cv03417/415175/598/) [2023cv03417/415175/598/](https://law.justia.com/cases/federal/district-courts/california/candce/3:2023cv03417/415175/598/). No. 3:23-cv-03417-VC (N.D. Cal. Jun. 25, 2025).
- <span id="page-22-1"></span>Ashley King. Anthropic CEO Doubles Down on Fair Use Defense–"The Law Will Back Us Up"'. *Digital Music News*, April 2024. URL [https://www.digitalmusicnews.com/2024/04/15/](https://www.digitalmusicnews.com/2024/04/15/anthropic-ceo-doubles-down-on-fair-use-defense/) [anthropic-ceo-doubles-down-on-fair-use-defense/](https://www.digitalmusicnews.com/2024/04/15/anthropic-ceo-doubles-down-on-fair-use-defense/).
- <span id="page-22-3"></span>Katherine Lee, Daphne Ippolito, Andrew Nystrom, Chiyuan Zhang, Douglas Eck, Chris Callison-Burch, and Nicholas Carlini. Deduplicating Training Data Makes Language Models Better. In *Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics*, volume 1, pp. 8424–8445, 2022.
- <span id="page-22-0"></span>Katherine Lee, A. Feder Cooper, James Grimmelmann, and Daphne Ippolito. AI and Law: The Next Generation. *SSRN*, 2023a. http://dx.doi.org/10.2139/ssrn.4580739.
- <span id="page-22-2"></span>Katherine Lee, A. Feder Cooper, and James Grimmelmann. Talkin' 'Bout AI Generation: Copyright and the Generative-AI Supply Chain. *arXiv preprint arXiv:2309.08133*, 2023b.
- <span id="page-22-11"></span>Katherine Lee, A. Feder Cooper, and James Grimmelmann. Talkin' 'Bout AI Generation: Copyright and the Generative-AI Supply Chain (The Short Version). In *Proceedings of the Symposium on Computer Science and Law*, CSLAW '24, pp. 48–63, New York, NY, USA, 2024. Association for Computing Machinery. ISBN 9798400703331. doi: 10.1145/3614407.3643696. URL <https://doi.org/10.1145/3614407.3643696>.

<span id="page-22-10"></span>Mark Lemley and Bryan Casey. Fair Learning. *Texas Law Review*, 99:743, 2021.

<span id="page-22-15"></span>George R.R. Martin. *A Game of Thrones*. Voyager Books, 1996.

<span id="page-22-17"></span>Courtney Milan. *The Duchess War*. Createspace, 2012.

<span id="page-22-16"></span>Toni Morrison. *Beloved*. Alfred A. Knopf Inc., 1987.

- <span id="page-22-4"></span>Milad Nasr, Nicholas Carlini, Jonathan Hayase, Matthew Jagielski, A. Feder Cooper, Daphne Ippolito, Christopher A. Choquette-Choo, Eric Wallace, Florian Tramèr, and Katherine Lee. Scalable Extraction of Training Data from (Production) Language Models. *arXiv preprint arXiv:2311.17035*, 2023.
- <span id="page-22-6"></span>Milad Nasr, Javier Rando, Nicholas Carlini, Jonathan Hayase, Matthew Jagielski, A. Feder Cooper, Daphne Ippolito, Christopher A. Choquette-Choo, Florian Tramèr, and Katherine Lee. Scalable Extraction of Training Data from Aligned, Production Language Models. In *The Thirteenth International Conference on Learning Representations*, 2025. URL <https://openreview.net/forum?id=vjel3nWP2a>.

<span id="page-22-9"></span>New York Times Company v. Microsoft. 2:24-cv-00711 (C.D. Cal.).

- <span id="page-23-8"></span>OpenAI. GPT-4 System Card. Technical report, March 2023. URL [https://cdn.openai.com/papers/](https://cdn.openai.com/papers/gpt-4-system-card.pdf) [gpt-4-system-card.pdf](https://cdn.openai.com/papers/gpt-4-system-card.pdf).
- <span id="page-23-0"></span>OpenAI. OpenAI and Journalism, 2024a. URL [https://openai.com/index/openai-and-journalism/](https://openai.com/index/openai-and-journalism/?utm_source=chatgpt.com) [?utm\\_source=chatgpt.com](https://openai.com/index/openai-and-journalism/?utm_source=chatgpt.com). Accessed: 2025-11-06.
- <span id="page-23-2"></span>OpenAI. OpenAI Model Spec (2024/05/08), May 2024b. URL [https://cdn.openai.com/spec/](https://cdn.openai.com/spec/model-spec-2024-05-08.html) [model-spec-2024-05-08.html](https://cdn.openai.com/spec/model-spec-2024-05-08.html). Accessed: 2025-05-13.
- <span id="page-23-11"></span>OpenAI. Introducing GPT-4.1 in the API, April 2025. URL <https://openai.com/index/gpt-4-1/>.
- <span id="page-23-13"></span>George Orwell. *Nineteen-Eighty Four*. Harcourt, Brace and Company, 1949.
- <span id="page-23-6"></span>Long Ouyang, Jeff Wu, Xu Jiang, Diogo Almeida, Carroll L. Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, et al. Training language models to follow instructions with human feedback. *arXiv preprint arXiv:2203.02155*, 2022.
- <span id="page-23-1"></span>Jörn Poltz and Friederike Heine. OpenAI used song lyrics in violation of copyright laws, German court says. *Reuters*, November 2025. URL [https://www.reuters.com/world/](https://www.reuters.com/world/german-court-sides-with-plaintiff-copyright-case-against-openai-2025-11-11/) [german-court-sides-with-plaintiff-copyright-case-against-openai-2025-11-11/](https://www.reuters.com/world/german-court-sides-with-plaintiff-copyright-case-against-openai-2025-11-11/).
- <span id="page-23-4"></span>Project Zero. Vulnerability disclosure policy. [https://googleprojectzero.blogspot.com/p/](https://googleprojectzero.blogspot.com/p/vulnerability-disclosure-policy.html) [vulnerability-disclosure-policy.html](https://googleprojectzero.blogspot.com/p/vulnerability-disclosure-policy.html), 2021. Accessed: 2025-02-14.
- <span id="page-23-3"></span>J.K. Rowling. *Harry Potter and the Sorcerer's Stone*. Scholastic, 1998.
- <span id="page-23-12"></span>J.K. Rowling. *Harry Potter and the Goblet of Fire*. Scholastic, 2000.
- <span id="page-23-15"></span>J.D. Salinger. *The Catcher in the Rye*. Little, Brown and Company, 1951.
- <span id="page-23-9"></span>Pamela Samuelson. Generative AI meets copyright. *Science*, 381(6654):158–161, 2023.
- <span id="page-23-10"></span>André Santos, José João Almeida, and Nuno Carvalho. Structural alignment of plain text books. In Nicoletta Calzolari, Khalid Choukri, Thierry Declerck, Mehmet Uğur Doğan, Bente Maegaard, Joseph Mariani, Asuncion Moreno, Jan Odijk, and Stelios Piperidis (eds.), *Proceedings of the Eighth International Conference on Language Resources and Evaluation (LREC'12)*, pp. 2069–2074, Istanbul, Turkey, May 2012. European Language Resources Association (ELRA). URL <https://aclanthology.org/L12-1576/>.
- <span id="page-23-16"></span>Avi Schwarzschild, Zhili Feng, Pratyush Maini, Zachary C. Lipton, and J. Zico Kolter. Rethinking LLM Memorization through the Lens of Adversarial Compression, 2024. URL <https://arxiv.org/abs/2404.15146>.
- <span id="page-23-7"></span>Mrinank Sharma, Meg Tong, Jesse Mu, Jerry Wei, Jorrit Kruthoff, Scott Goodfriend, Euan Ong, Alwin Peng, Raj Agarwal, Cem Anil, Amanda Askell, Nathan Bailey, Joe Benton, Emma Bluemke, Samuel R. Bowman, Eric Christiansen, Hoagy Cunningham, Andy Dau, Anjali Gopal, Rob Gilson, Logan Graham, Logan Howard, Nimit Kalra, Taesung Lee, Kevin Lin, Peter Lofgren, Francesco Mosconi, Clare O'Hara, Catherine Olsson, Linda Petrini, Samir Rajani, Nikhil Saxena, Alex Silverstein, Tanya Singh, Theodore Sumers, Leonard Tang, Kevin K. Troy, Constantin Weisser, Ruiqi Zhong, Giulio Zhou, Jan Leike, Jared Kaplan, and Ethan Perez. Constitutional classifiers: Defending against universal jailbreaks across thousands of hours of red teaming, 2025. URL <https://arxiv.org/abs/2501.18837>.
- <span id="page-23-5"></span>Mary Shelley. *Frankenstein*. Lackington, Hughes, Harding, Mavor, & Jones, 1818.
- <span id="page-23-17"></span>The Authors Guild. The Authors Guild, John Grisham, Jodi Picoult, David Baldacci, George R.R. Martin, and 13 Other Authors File Class-Action Suit Against OpenAI. September 2023. URL <https://authorsguild.org/news/ag-and-authors-file-class-action-suit-against-openai/>.
- <span id="page-23-14"></span>J.R.R. Tolkien. *The Hobbit*. George Allen and Unwin, 1937.

- <span id="page-24-0"></span>Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, Aurelien Rodriguez, Armand Joulin, Edouard Grave, and Guillaume Lample. LLaMA: Open and Efficient Foundation Language Models, 2023. URL <https://arxiv.org/abs/2302.13971>.
- <span id="page-24-9"></span>Angelina Wang, Daniel E. Ho, and Sanmi Koyejo. The inadequacy of offline large language model evaluations: A need to account for personalization in model behavior. *Patterns*, 6(12):101397, December 2025. doi: 10.1016/j.patter.2025.101397. URL <https://doi.org/10.1016/j.patter.2025.101397>. Published 12 December 2025.
- <span id="page-24-6"></span>Jiapeng Wang and Yihong Dong. Measurement of Text Similarity: A Survey. *Information*, 11(9), 2020. ISSN 2078-2489. doi: 10.3390/info11090421. URL <https://www.mdpi.com/2078-2489/11/9/421>.
- <span id="page-24-5"></span>Alexander Wei, Nika Haghtalab, and Jacob Steinhardt. Jailbroken: How does llm safety training fail?, 2023. URL <https://arxiv.org/abs/2307.02483>.
- <span id="page-24-3"></span>Jason Wei, Maarten Bosma, Vincent Y. Zhao, Kelvin Guu, Adams Wei Yu, Brian Lester, Nan Du, Andrew M. Dai, and Quoc V. Le. Finetuned language models are zero-shot learners. *arXiv preprint arXiv:2109.01652*, 2021.
- <span id="page-24-7"></span>Johnny Tian-Zheng Wei, Ameya Godbole, Mohammad Aflah Khan, Ryan Wang, Xiaoyuan Zhu, James Flemings, Nitya Kashyap, Krishna P. Gummadi, Willie Neiswanger, and Robin Jia. Hubble: a model suite to advance the study of llm memorization, 2025. URL <https://arxiv.org/abs/2510.19811>.
- <span id="page-24-1"></span>Kyle Wiggers and Maxwell Zeff. In AI copyright case, Zuckerberg turns to YouTube for his defense, January 2025. URL [https://techcrunch.com/2025/01/15/](https://techcrunch.com/2025/01/15/in-ai-copyright-case-zuckerberg-turns-to-youtube-for-his-defense/) [in-ai-copyright-case-zuckerberg-turns-to-youtube-for-his-defense/](https://techcrunch.com/2025/01/15/in-ai-copyright-case-zuckerberg-turns-to-youtube-for-his-defense/).
- <span id="page-24-8"></span>xAI. Models and Pricing, 2025. URL <https://docs.x.ai/docs/models>. "The knowledge cut-off date of Grok 3 and Grok 4 is November, 2024.".
- <span id="page-24-2"></span>Daniel M. Ziegler, Nisan Stiennon, Jeffrey Wu, Tom B. Brown, Alec Radford, Dario Amodei, Paul Christiano, and Geoffrey Irving. Fine-tuning language models from human preferences. *arXiv preprint arXiv:1909.08593*, 2019.
- <span id="page-24-4"></span>Andy Zou, Zifan Wang, Nicholas Carlini, Milad Nasr, J. Zico Kolter, and Matt Fredrikson. Universal and transferable adversarial attacks on aligned language models, 2023. URL <https://arxiv.org/abs/2307.15043>.

### <span id="page-25-0"></span>**A BoN perturbtations**

For completeness, we document the exact perturbations used during the Best-of-*N* (BoN) jailbreak for Claude 3.7 Sonnet and GPT-4.1. We fix *σ* to be 0*.*6 for all experiments. All perturbations operate deterministically, given the random seed, allowing exact replay of prompt sequence.

**Identity.** Returns the prefix unchanged.

- **Capitalization.** Iterates over every alphabetic character and flips its case with probability *p* ∈ [0*,* 1] (we use *p* ∈ {0*.*2*,* 0*.*5}). Sampling is i.i.d. per character using a pseudo-random generator seeded per perturbation.
- **Spacing.** Processes the string left-to-right. For each existing space we remove it with probability *p*rm; for each non-space character we optionally insert a space immediately after it with probability *p*add, so long as the next character is not already whitespace. We use (*p*add*, p*rm) ∈ {(0*.*05*,* 0*.*05)*,*(0*.*1*,* 0*.*1)}.
- **Word order shuffle.** Split the text into sentences using punctuation boundaries ('.', '!', '?'). Within each sentence, we shuffle the token order with probability *p*shuffle = 0*.*3 when the sentence contains more than one token.
- **Character substitution.** For each letter, with probability *p*sub (set to 0*.*1 or 0*.*05), we replace the letter with a visually similar glyph drawn uniformly from a fixed mapping (e.g., 'a' → {'@'*,* '´a'*,* '`a'*,* 'ˆa'}, 's' → {'\$'*,* '5'}). Uppercase letters inherit the capitalization of the replacement.
- **Punctuation edits.** For characters that are punctuation marks (e.g., '.', ',', '!', '?', ';', ':'), we remove them with probability *p*rm; for alphabetic characters, we insert a random punctuation mark immediately after with probability *p*add. We use (*p*add*, p*rm) ∈ {(0*.*05*,* 0*.*05)*,*(0*.*1*,* 0*.*1)}.
- **Word scrambling.** For each text token longer than three characters, we shuffle its interior characters (leave first and last fixed) with probability *σ* 1*/*2 . This preserves readability while altering the byte-level form.
- **Random capitalization.** Similar to capitalization above, but the flip probability is driven by the intensity parameter: each alphabetic character swaps case with probability *σ* 1*/*2 .
- **ASCII noising.** For every printable ASCII character (code points 32–126) we perturb the character with probability *σ* 3 . When triggered, we add or subtract 1 from its code point (chosen uniformly from {−1*,* +1}); if the resulting code point is outside the printable range, we leave the character unchanged. This mimics light OCR or transmission noise while preserving human readability.
- **Composites.** We also chain multiple perturbations in a fixed order, e.g., capitalization → spacing, or word scrambling → random capitalization → ASCII noising. Each composite inherits the parameter settings of its constituents. Identity is always included in the pool so that unperturbed prompts are sampled alongside perturbed ones.

### <span id="page-25-1"></span>**B Procedure for quantifying extraction success**

In Section [3.3,](#page-7-0) we describe our measurement procedure for capturing valid instances of extraction. Prior work commonly uses a threshold of 50 LLM tokens to identify verbatim memorized sequences. For typical English prose, a useful approximation is that one word corresponds to approximately 1*.*3–1*.*4 LLM tokens. Under this conversion, 50 tokens corresponds to roughly 35–40 words, while 100 words corresponds to approximately 130–140 tokens. For long-form extraction, verbatim matching is too stringent [\(Cooper et al.,](#page-21-3) [2025\)](#page-21-3). We instead merge closely aligned blocks, but then filter these merged blocks to only retain ones that are sufficiently long to make a valid extraction claim.

Following [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3), we first first identifies verbatim blocks, using a block-based greedy approximation of longest common substring. For this, we use difflib SequenceMatcher [\(difflib SequenceMatcher,](#page-21-11) [2025\)](#page-21-11), which returns on ordered set of verbatim matching blocks given two input text lists (Equation [3\)](#page-8-0). We

then do two merge-and-filter passes (Equation [4.](#page-8-1)) The first merge is very stringent, combining blocks that have very short gaps within a given input text and are well-aligned across input texts (*τ* (1) gap = 2, *τ* (1) align = 1). The first filter with *l* (1) = 20 words is fairly stringent, with respect to what we consider a "very short" span of text; note that this is about half of the length of the 35–40 words used for verbatim discoverable extraction. The second merge is slightly more relaxed, but still stringent (*τ* (2) gap = 10, *τ* (2) align = 3)). To compensate for this relaxation, the second filter is very stringent, with *l* (2) = 100 words.

In Figure [4,](#page-8-2) we provide a high-level depiction of our procedure for forming near-verbatim blocks. In Figure [4a,](#page-8-2) we show how benign formatting differences introduce short blocks, and how our procedure ultimately reconciles these differences to produce a longer-form near-verbatim block. In contrast, Figure [4b](#page-8-2) shows how the identify procedure can return very short blocks that we should not count as extraction, even though they are (coincidental) verbatim matches. We performed extensive validation experiments on these settings to pick this configuration, discussed further below.

**Conservative estimate for extraction.** Note that this procedure is conservative in several ways. If any of the blocks in Figure [4a](#page-8-2) had been a bit shorter, the entire text would have failed the second filter. Further, note that we still only count the *verbatim* length contributions in our near-verbatim blocks. For example, in Figure [4a,](#page-8-2) we do not count the text in the gap text; the final merged block is the sum of the lengths of the original six blocks only. This length is 141 words; if we were to count the book *B*'s ground-truth text in the gaps that were reconciled into this near-verbatim block, then the total length would be 150 words that contribute to our matched count *m* (Equation [6\)](#page-9-3). Either approach would be a reasonable and valid way to operationalize our procedure, but we choose to be conservative and only count verbatim matches. This deflates our final extraction numbers.

We validated our chosen configuration, experimenting with several different settings for our procedure different gap, alignment, and filter length tolerances. We evaluated these settings both quantitatively (e.g., how extraction metrics change, histograms over retained block lengths, computing Levenshtein distance over near-verbatim blocks with generated and ground-truth book text) and qualitatively (e.g., visual inspection of diffs between books and generations). We found that it would be reasonable to use shorter filter conditions for both filter steps, as well as a larger maximum gap in the second merge, in comparison to the final configuration we report.

To be conservative about our claims, we picked the most stringent configuration that retains effectively verbatim long-form text that has been split into short blocks due to changes in punctuation (as in Figure [4a\)](#page-8-2). We also experimented with using the Levenshtein distance as an additional merging criterion in the first filter (i.e., to only merge blocks for which the very short gaps are due to generated text in *G* that is within a small Levenshteindistance of the ground-truth text in *B*). This check would, for example, consider the short gaps in Figure [4a](#page-8-2) to be benign (and fine to merge blocks in the first pass), but would not merge the blocks with short gaps in Figure [4b.](#page-8-2) However, we observed no substantive difference in our measurements when including this check; in practice, the combination of two merge-and-filter passes removes patchy chains of partial, short matches (e.g., happenstance matches of "the" in the same location in the book and generation). For simplicity, we omit this check.

We provide a more detailed depiction of our procedure for the text in Figure [4a](#page-8-2) below, which shows each step of the near-verbatim block formation procedure. This figure illustrates the need for our two-stage merge-and-filter approach, rather than a simple merge and filter, which would excessively drop near-verbatim spans that have benign formatting differences.

![](_page_27_Figure_0.jpeg)

<span id="page-27-0"></span>Figure 10: **Illustrating each step of our two-step merge-and-filter procedure.** This is a more detailed depiction of Figure [4a,](#page-8-2) showing both merge-and-filter steps for part of *B*=*Frankenstein*. The text shown is part of the corresponding generation *G* from Claude 3.7 Sonnet, not the ground-truth book *B*. Verbatim text is identical in both *B* and *G*, but gap text differs, as these differences are the reason for gaps between blocks.

### **C Experimental setup**

We provide further details on our results and experimental setup. We provide additional information on book selection (Appendix [C.1\)](#page-28-0), production-LLM-specific Phase 2 configurations and results (Appendix [C.2\)](#page-28-1), and the light text normalization we perform prior to computing near-verbatim extraction metrics (Appendix [C.3\)](#page-29-1).

### <span id="page-28-0"></span>**C.1 Book selection**

While companies have not disclosed exact training corpora, public statements [\(Wiggers & Zeff, 2025;](#page-24-1) [Brittain,](#page-20-16) [2023;](#page-20-16) [Claburn, 2024\)](#page-20-1) and litigation [\(Bartz et al. v. Anthropic PBC;](#page-19-10) [Kadrey et al. v. Meta Platforms, Inc.;](#page-22-8) [The Authors Guild, 2023;](#page-23-17) [King, 2024\)](#page-22-1) suggest books are very likely included. For our extraction experiments (but not our negative control), we draw initial seeds for Phase 1 from books that we suspect were included in the training data (Figure [2,](#page-4-1) Section [3.1\)](#page-4-0). As a proxy, we mostly select books that [Cooper et al.](#page-21-3) [\(2025\)](#page-21-3) observe to be highly memorized by Llama 3.1 70B. Following Phase 2, we only make extraction claims (which embed a claim for training-data membership) for long generated blocks of near-verbatim text. Except in select cases for Claude 3.7 Sonnet, where we extract full books, we do not claim training-data membership for a whole book with our results; we only claim training-data membership for the text that we extracted.

### <span id="page-28-1"></span>**C.2 Phase 2 generation configurations and stop conditions**

In this appendix, we document the exact hyperparameters and stopping conditions used during Phase 2 (Section [3.2\)](#page-5-0) for each production LLM.

### <span id="page-28-3"></span>**C.2.1 Settings for main results**

We start with the settings used in our main results, presented in Section [4.2.](#page-12-1) Each production LLM exposes different configurations for generation. For each production LLM, we ran exploratory experiments to identify conditions under which extraction might work.

For all production LLMs, we fix temperature to 0*.*0 (deterministic generation, but there may be other system non-determinism). Based on initial experiments, we set the maximum number of returned tokens to be 250, 500, 2000 and 500 for Claude 3.7 Sonnet, Grok 3, Gemini 2.5 Pro, and GPT-4.1, respectively. We set the maximum number of continuation turns to 600, 200, 300, and 300, respectively. We chose 300 for both Gemini 2.5 Pro and Grok 3 because we observed in initial experiments that both production LLMs would diverge from near-verbatim books before this point. Given the choice to set the maximum returned tokens shorter for Claude 3.7 Sonnet (to avoid filters), we set the number of turns higher. For experiments with *The Hobbit*, we ran for longer (1000 turns) after observing continued extraction. For Gemini 2.5 Pro, we also set frequency penalty to 2 and presence penalty to 0*.*1, given initial experiments sweeping over these parameters for *Harry Potter and the Sorcerer's Stone* (Appendix [C.2.2\)](#page-29-0).

Table 2: Regex Patterns Used for Refusal Detection

<span id="page-28-2"></span>

| Regex Pattern                               |
|---------------------------------------------|
| \bsorry[, ]*(?:but )?i can[\u0027\u2019]t\b |
| \bcopyright(?:ed)?\b                        |
| \bcan[\u0027\u2019]t provide\b              |
| \bunable to\b                               |
| \bi cannot\b                                |
| \bwon[\u0027\u2019]t be able to\b           |
| \bnot allowed to\b                          |
| \bcan[\u0027\u2019]t reproduce\b            |
| \bcan[\u0027\u2019]t continue\b             |
| \bcan[\u0027\u2019]t share\b                |

**Halting Phase 2.** We deliberately terminate Phase 2 when any of the following conditions is met: (1) a maximum budget for continuations is reached, (2) we detect a refusal in the production LLM response, or (3) we detect a stop string in the production LLM response. For (2), we use simple regex checks to detect refusals. We enumerate all the regex patterns in Table [2.](#page-28-2) For (3), we check for the following stop strings that indicate the model has reached the end of the book, suggesting that it has stopped generating training data: "we have reached the conclusion of", "[End of Book]", "THE END", "About the Author", "Afterword", "Bibliography". For Grok 3, the Phase 2 loop sometimes terminated due to an HTTP 500 error.

In initial exploratory experiments, for Claude 3.7 Sonnet we originally implemented stop string detection using the last sentence from the book. However, from those experiments, we saw that Claude 3.7 Sonnet would generate "THE END" when reaching the end of a book. After these initial experiments, we switched to these stop strings so as to not rely on ground-truth reference text beyond the prefix in Phase 1.

### <span id="page-29-0"></span>**C.2.2 Generation configuration exploration for Gemini 2.5 Pro**

We explored a variety of different settings for Gemini 2.5 Pro's generation parameters in experiments with *Harry Potter and the Sorcerer's Stone*:

• **Max tokens per interaction**: {1000*,* 2000*,* 4000}

• **Frequency penalty**: {0*.*5*,* 1*.*0*,* 2*.*0} • **Presence penalty**: {0*.*1*,* 0*.*2*,* 0*.*3}

After observing that 2000 max tokens led to the highest nv-recall in all cases, we fixed max tokens to 2000 for all subsequent experiments. In Section [4.2,](#page-12-1) we report results for fixed frequency penalty (2*.*0) and presence penalty (0*.*1). However, maximum nv-recall per book varies by this configuration, which we show in Figure [14.](#page-39-0)

#### **C.2.3 Refusal retries for per-chapter experiments with GPT-4.1**

In our more intensive per-chapter runs on GPT-4.1, we also attempt to continue in spite of refusals (Section [4.3\)](#page-15-0). In each iteration in the continue loop, we produce five responses. We take the first response (in the API returned list) that does not contain a refusal as the response. If all responses are refusals, then we enter a refusal retry loop where we wait to retry with exponential backoff (up to 100 times). We continue the loop for up to 50 turns (per chapter, in contrast to the maximum of 200 we use in our main experiments starting with a seed from the beginning of the book; see Appendix [C.2.1\)](#page-28-3). Once a response is classified as a refusal, the loop waits for a fixed delay (two minutes) and then retries the same continuation prompt, up to a maximum number of attempts (50). We found refusals to be non-deterministic: the same instruction prompt would often fail repeatedly and then succeed after a few retries.

**Chat UI** We found that our two-phase works using the chat UI, as well, with apparently increased robustness. In initial exploratory experiments, we ran a prefix from *The Great Gatsby* in the ChatGPT web application UI. Through this approach, we were able to extract the first four chapters of *The Great Gatsby*, even though we could not reliably do the same through the API. This suggests that our reported API numbers may be conservative: the true leakage in end-user deployments may be higher than what we measure here. In general, UI implementation choices for production LLMs non-trivially affect their behavior [\(Nasr et al., 2023;](#page-22-4) [Wang et al., 2025\)](#page-24-9). We also tested our extraction procedure for Claude 3.7 Sonnet using Anthropic's chat UI, and observed that it worked. We do not include results for these UI-based interactions.

#### <span id="page-29-1"></span>**C.3 Text normalization prior to gauging near-verbatim extraction**

When we evaluate extraction success (Section [3.3.1\)](#page-7-1), we provide two input documents: the ground-truth book from Books3, and the generated text. For this assessment, we operate on lightly normalized versions of both the reference books and generations. The goal of this procedure is to remove superficial formatting and Unicode differences that would otherwise artificially deflate measured overlap. For example, Books3 books tend to use underscores to mark italics or stylistic variation in quotation marks, which are often absent in generations. Since we do not know the format of the training data for these production LLMs (i.e., the format may not align with the format of the book in Books3), we aim to eliminate benign punctuation differences.

We transform each raw text string *t* (either a reference book or a model output) into a normalized string *t*˜= Normalize(*t*) using the following deterministic mapping.

1. **Unicode alignment.** We first apply Unicode compatibility normalization in NFKC form:

$$\tilde{t}_0 = NFKC(t).$$

This step ensures that visually identical characters are represented identically at the byte level. This is important because our similarity metrics are computed over whitespace-split word tokens.

- 2. **Punctuation remapping.** Next, we apply a fixed character-level remapping *π* via str.translate to standardize a small set of punctuation marks:
  - left/right and other Unicode quotation variants (e.g., ", ", ', ') are mapped to their ASCII counterparts (" or ');
  - dash variants (e.g., en dash and horizontal bar) are mapped to a single em dash code point (—);
  - the Unicode ellipsis character (which is not visually unique in LaTeX) is mapped to three ASCII dots (...). We denote the result of this step *t*˜<sup>1</sup> = *π*(*t*˜0). This consolidation prevents purely typographical variation in quotation or dash style from reducing overlap scores.
- 3. **Ellipses and dash-like hyphens.** We normalize certain common punctuation patterns with regular expressions:
  - sequences of spaced dots (e.g., ". . .") are collapsed to a canonical ellipsis ...;
  - if an ellipsis is immediately followed by an alphanumeric character, we insert a single space after ... to avoid spurious concatenation.
- 4. **Books3 italics markup.** Books3 books often denote italics with underscore delimiters, so that emphasized spans appear as \_like this\_ in the raw text. Because model generations rarely reproduce these delimiters, they can otherwise appear as artificial mismatches. To account for this, we remove single-underscore emphasis markers using a regex of the form

$$([^-]+)_ \rightarrow 1$$

which strips the outer underscores while preserving the interior text verbatim.

5. **Lowercasing.** Finally, because we observe irregular casing in some generated outputs, we convert the entire string to lowercase,

$$\tilde{t} = \text{lower}(\tilde{t}_1),$$

so that case differences do not affect similarity measurements.

After normalization, we tokenize both *t*˜ and the corresponding normalized reference using Python's default whitespace splitting (str.split()), exactly as described in Section [3.3,](#page-7-0) and pass the resulting word sequences to difflib SequenceMatcher.

We intentionally keep this normalization minimal. We *do not* perform stemming or lemmatization, do not remove stopwords, do not strip punctuation beyond the specific remappings above, and do not collapse all non-ASCII characters to ASCII. Aside from the whitespace effects implied by the regex substitutions, we do not otherwise modify spacing or line breaks.

## <span id="page-31-0"></span>**D Extended results**

In this appendix, we include more detailed results for experiments presented in the main paper, as well as additional experiments, for both Phase 1 (Appendix [D.1\)](#page-31-1) and Phase 2 (Appendix [D.2\)](#page-32-0).

#### <span id="page-31-1"></span>**D.1 Additional Phase 1 results**

<span id="page-31-2"></span>We include a brief illustration for Phase 1 (Section [3.1\)](#page-4-0) and Claude 3.7 Sonnet for several books in Figure [11.](#page-31-2) Table [3](#page-32-2) shows a summary of full BoN results across books for both Claude 3.7 Sonnet and GPT-4.1. The number of attempts *N* can vary the cost of Phase 1, but overall it is very cheap for *N* ≤ 10*,*000. Since we do not jailbreak Gemini 2.5 Pro or Grok 3, we omit results for these production LLMs (*N* = 0). We include detailed results on the success of BoN in Table [3.](#page-32-2) Note that we do not always achieve maximum possible *s* = 1*.*0 (Equation [2\)](#page-5-1).

![](_page_31_Figure_4.jpeg)

Figure 11: **Comparing** *N* **for Phase 1 for Claude 3.7 Sonnet.** As an illustration, we show how *s* (Equation [2\)](#page-5-1) changes over *N* for Claude 3.7 Sonnet, for four books we attempt to extract (*Harry Potter and the Sorcerer's Stone*, *The Duchess War*, *The Great Gatsby*, *Frankenstein*) and the negative control (*The Society of Unknowable Objects*). Phase 1 success occurs when *s* ≥ 0*.*6. Phase 1 succeeds for *Harry Potter and the Sorcerer's Stone*, *The Great Gatsby*, and *Frankenstein*—three books for which ultimately nv-recall ≥ 94% (Figure [5\)](#page-11-1). Phase 1 fails for *The Duchess War*, so we do not run Phase 2. Phase 1 also fails for the negative control (*The Society of Unknowable Objects*, published long after the knowledge cutoffs for all four production LLMs).

<span id="page-32-2"></span>

| Book                                  | Production LLM    | Max. s   | N for max. s |
|---------------------------------------|-------------------|----------|--------------|
| Harry Potter and the Sorcerer's Stone | Claude 3.7 Sonnet | 1.000000 | 258          |
| Harry Potter and the Sorcerer's Stone | GPT-4.1           | 0.914474 | 5179         |
| Harry Potter and the Goblet of Fire   | Claude 3.7 Sonnet | 1.000000 | 6            |
| Harry Potter and the Goblet of Fire   | GPT-4.1           | 1.000000 | 1405         |
| 1984                                  | Claude 3.7 Sonnet | 1.000000 | 6            |
| 1984                                  | GPT-4.1           | 1.000000 | 183          |
| The Hobbit                            | Claude 3.7 Sonnet | 1.000000 | 23           |
| The Hobbit                            | GPT-4.1           | 1.000000 | 24           |
| The Catcher in the Rye                | Claude 3.7 Sonnet | 0.608392 | 6            |
| The Catcher in the Rye                | GPT-4.1           | 0.608392 | 213          |
| A Game of Thrones                     | Claude 3.7 Sonnet | 1.000000 | 6            |
| A Game of Thrones                     | GPT-4.1           | 0.967532 | 7842         |
| Beloved                               | Claude 3.7 Sonnet | 1.000000 | 6            |
| Beloved                               | GPT-4.1           | 1.000000 | 42           |
| The Da Vinci Code                     | Claude 3.7 Sonnet | 0.653333 | 2143         |
| The Da Vinci Code                     | GPT-4.1           | 0.280000 | 3497         |
| The Hunger Games                      | Claude 3.7 Sonnet | 1.000000 | 23           |
| The Hunger Games                      | GPT-4.1           | 0.883562 | 9949         |
| Catch-22                              | Claude 3.7 Sonnet | 1.000000 | 23           |
| Catch-22                              | GPT-4.1           | 0.532895 | 2196         |
| Frankenstein                          | Claude 3.7 Sonnet | 1.000000 | 43           |
| Frankenstein                          | GPT-4.1           | 1.000000 | 24           |
| The Great Gatsby                      | Claude 3.7 Sonnet | 1.000000 | 6            |
| The Great Gatsby                      | GPT-4.1           | 1.000000 | 5            |

Table 3: **Comparing** *N* **across Phase 1 jailbreaks.** For the two production LLMs that we jailbreak (Claude 3.7 Sonnet and GPT-4.1), we show the maximum *s* (Equation [2\)](#page-5-1) achieved. We only include results for the twelve books where at least one production LLM had a Phase 1 success, so note that Phase 1 failed for GPT-4.1 for two books (marked in red). We also show the *N* needed to obtain the maximum *s* that we observed. For all runs, the maximum *N* budget is 10*,*000.

#### <span id="page-32-0"></span>**D.2 Additional Phase 2 results**

We show API costs for Phase 2 (Appendix [D.2.1\)](#page-32-1), and additional plots and tables (Appendix [D.2.2\)](#page-36-0).

### <span id="page-32-1"></span>**D.2.1 Continuation loop API costs**

We include a table with the count of all continuation queries in Phase 2. When Gemini 2.5 Pro returns an empty response, we count this against the max query budget, but do not mark it as a successful continue query. The Grok 3 sometimes returned an HTTP 500 error, which prematurely terminated the loop.

We estimate the monetary cost of running Phase 2 by summing the provider-reported API charges over all continuation-loop requests in that phase for each LLM-book run. This cost depends on (i) the number of continue queries (Table [4\)](#page-33-0), (ii) the input and output token counts per query, and (iii) the provider pricing in effect during our experimental window (mid August to mid September 2025). Because pricing and tokenization differ across providers and can change over time, we report costs only for our specific runs and treat them as approximations. We provide one cost table each for Claude 3.7 Sonnet (Table [5\)](#page-33-1) and Grok 3 (Table [10\)](#page-35-0). For Gemini 2.5 Pro, we provide a cost table for our main results runs in Section [4.2](#page-12-1) (Table [8\)](#page-34-0) as well as a summary of total costs across all configured runs (Table [9\)](#page-35-1). For GPT-4.1, we include results for our main results in Section [4.2](#page-12-1) (Table [6\)](#page-34-1) as well as a total cost table accounting for our more intensive extraction experiments (Table [7\)](#page-34-2). Where appropriate, we provide short notes about provider-specific cost accounting.

<span id="page-33-0"></span>

| Book                                  | Claude 3.7 Sonnet | Gemini 2.5 Pro | GPT-4.1 | Grok 3 |
|---------------------------------------|-------------------|----------------|---------|--------|
| 1984                                  | 538               | 300            | 61      | 23     |
| Beloved                               | 600               | 81             | 3       | 66     |
| Catch-22                              | 419               | 286            | –       | 125    |
| The Catcher in the Rye                | 148               | 173            | 37      | 245    |
| The Da Vinci Code                     | 532               | 223            | –       | 66     |
| Frankenstein                          | 374               | 204            | 33      | 300    |
| A Game of Thrones                     | 562               | 166            | 15      | 195    |
| The Great Gatsby                      | 317               | 218            | –       | 182    |
| Harry Potter and the Sorcerer's Stone | 480               | 171            | 31      | 52     |
| Harry Potter and the Goblet of Fire   | 600               | 264            | 1       | 300    |
| The Hunger Games                      | 600               | 54             | 0       | 300    |
| The Hobbit                            | 1000              | 188            | 4       | 115    |

<span id="page-33-1"></span>Table 4: **Number of continue queries in Phase 2.** We show the number of times we query each production LLM to continue in Phase 2 for each book that achieves success in Phase 1. Phase 2 was not run for GPT-4.1 on *The Da Vinci Code* and *Catch-22* , hence those entries are omitted.

| Book                                  | Input tokens | Output tokens | Cost (\$) |
|---------------------------------------|--------------|---------------|-----------|
| 1984                                  | 36,748,358   | 132,834       | 113.12    |
| Beloved                               | 45,908,804   | 149,575       | 189.20    |
| Catch-22                              | 22,566,963   | 104,928       | 69.25     |
| The Catcher in the Rye                | 2,682,321    | 36,722        | 11.17     |
| The Da Vinci Code                     | 36,979,052   | 134,187       | 152.46    |
| Frankenstein                          | 18,044,246   | 94,041        | 55.41     |
| A Game of Thrones                     | 40,450,707   | 140,200       | 124.49    |
| The Great Gatsby                      | 12,964,939   | 79,605        | 39.85     |
| Harry Potter and the Sorcerer's Stone | 28,987,543   | 117,843       | 119.97    |
| Harry Potter and the Goblet of Fire   | 32,258,077   | 147,932       | 133.12    |
| The Hunger Games                      | 45,855,059   | 147,126       | 140.52    |
| The Hobbit                            | 32,472,077   | 250,700       | 134.87    |

Table 5: **Phase 2 API token usage and estimated cost for Claude 3.7 Sonnet.** For the main experiments in Section [4.2,](#page-12-1) we report total per-book-run Phase 2 input and output tokens and the estimated dollar cost charged by the Claude 3.7 Sonnet API.

**Claude 3.7 Sonnet.** The API provider billing reports costs aggregated per day, rather than per run. To estimate a per-run Phase 2 cost, we compute a weighted share of the total daily cost based on that run's share of the day's total Phase 2 token usage. Claude 3.7 Sonnet appears to incur an extra, opaque "long context request" charge that is not explained in the publicly available pricing documentation; our estimates necessarily include this charge when it is present in the daily bill.

**GPT-4.1 accounting note.** We tracked costs, but at the time of writing the OpenAI billing API was down (HTTP 500 error). We therefore estimate costs based on token usage. OpenAI API does not report cached tokens explicitly, so we applied a heuristic to estimate prompt caching: for sequential requests within a run, we estimate cached tokens as the minimum of the previous and current prompt token counts, reflecting the shared prefix between successive requests. We report a conservative upper bound assuming no caching, and a lower bound using our caching heuristic. Costs were calculated using \$2.00 per million input tokens, \$0.50 per million cached input tokens, and \$8.00 per million output tokens.

**Gemini 2.5 Pro sweeps.** For Gemini 2.5 Pro we performed a Phase 2 sweep over presence/frequency penalty to study sensitivity to generation settings. Accordingly, we report (i) the Phase 2 cost of the single configuration used for our main Gemini 2.5 Pro comparison runs, and (ii) the cumulative Phase 2 cost summed over *all* Gemini 2.5 Pro sweep runs executed per book.

<span id="page-34-1"></span>

| Book                                  | Input tokens | Output tokens | Cost (\$) | Cost w/ cache (\$) |
|---------------------------------------|--------------|---------------|-----------|--------------------|
| 1984                                  | 193,776      | 29,327        | 0.62      | 0.34               |
| Beloved                               | 45,210       | 12,087        | 0.19      | 0.12               |
| Catch-22                              | 32,014       | 25,500        | 0.27      | 0.23               |
| The Catcher in the Rye                | 56,682       | 10,927        | 0.20      | 0.12               |
| The Da Vinci Code                     | 80,269       | 8598          | 0.23      | 0.11               |
| Frankenstein                          | 51,801       | 10,664        | 0.19      | 0.11               |
| A Game of Thrones                     | 73,522       | 29,173        | 0.38      | 0.28               |
| Harry Potter and the Sorcerer's Stone | 364,599      | 79,825        | 1.37      | 0.83               |
| Harry Potter and the Goblet of Fire   | 37,435       | 10,445        | 0.16      | 0.10               |
| The Hunger Games                      | 30,102       | 12,331        | 0.16      | 0.11               |
| The Hobbit                            | 44,633       | 9322          | 0.16      | 0.10               |

Table 6: **Phase API token usage and estimated cost for GPT-4.1 (main experiments).** For the main experiments in Section [4.2,](#page-12-1) we report the total per-book-run Phase 2 (for GPT-4.1, first chapter) input and output tokens. We provide two cost estimates: an upper bound assuming no prompt caching, and a lower estimate using our caching heuristic.

<span id="page-34-2"></span>

| Book                                  | Input tokens | Output tokens | Cost (\$) | Cost w/ cache (\$) |
|---------------------------------------|--------------|---------------|-----------|--------------------|
| 1984                                  | 7,396,072    | 865,284       | 21.71     | 10.83              |
| Beloved                               | 919,976      | 318,455       | 4.39      | 3.09               |
| Catch-22                              | 3,718,266    | 804,740       | 13.87     | 8.45               |
| The Catcher in the Rye                | 954,779      | 375,968       | 4.92      | 3.54               |
| The Da Vinci Code                     | 2,058,447    | 854,886       | 10.96     | 7.96               |
| Frankenstein                          | 2,136,628    | 448,730       | 7.86      | 4.76               |
| A Game of Thrones                     | 2,548,600    | 1,006,291     | 13.15     | 9.50               |
| Harry Potter and the Sorcerer's Stone | 7,452,983    | 932,170       | 22.36     | 11.45              |
| Harry Potter and the Goblet of Fire   | 3,162,308    | 554,614       | 10.76     | 6.15               |
| The Hunger Games                      | 1,155,141    | 459,260       | 5.98      | 4.33               |
| The Hobbit                            | 1,599,404    | 298,146       | 5.58      | 3.24               |

Table 7: **Phase 2 API token usage and estimated cost for GPT-4.1 (total cost).** For all experiments in Sections [4.2](#page-12-1) and [4.3,](#page-15-0) we report the total per-book Phase 2 input and output tokens. We provide two cost estimates: an upper bound assuming no prompt caching, and a lower estimate using our caching heuristic.

<span id="page-34-0"></span>

| Book                                  | Input tokens | Output tokens | Cost (\$) |
|---------------------------------------|--------------|---------------|-----------|
| 1984                                  | 18,582       | 6550          | 0.44      |
| Beloved                               | 96,184       | 49,192        | 0.85      |
| Catch-22                              | 12,400       | 3579          | 0.30      |
| The Catcher in the Rye                | 20,142       | 8502          | 0.36      |
| The Da Vinci Code                     | 17,989       | 6993          | 0.34      |
| Frankenstein                          | 24,184       | 10,419        | 0.38      |
| A Game of Thrones                     | 19,874       | 8519          | 0.36      |
| The Great Gatsby                      | 20,628       | 8489          | 0.35      |
| Harry Potter and the Sorcerer's Stone | 207,589      | 104,955       | 2.44      |
| Harry Potter and the Goblet of Fire   | 14,176       | 4725          | 0.31      |
| The Hunger Games                      | 4893         | 3346          | 0.06      |
| The Hobbit                            | 43,240       | 21,677        | 0.52      |

Table 8: **Phase API token usage and estimated cost for Gemini 2.5 Pro (main experiments).** For the main experiments in Section [4.2,](#page-12-1) we report the total per-book Phase 2 input/output tokens and estimated dollar cost. These results reflect a single generation configuration run for each book.

<span id="page-35-1"></span>

| Book                                  | Input tokens | Output tokens | Cost (\$) |
|---------------------------------------|--------------|---------------|-----------|
| 1984                                  | 2,195,516    | 1,029,004     | 58.99     |
| Beloved                               | 739,194      | 327,965       | 9.63      |
| Catch-22                              | 1,592,954    | 754,857       | 18.01     |
| The Catcher in the Rye                | 886,282      | 396,209       | 11.42     |
| The Da Vinci Code                     | 444,396      | 187,872       | 6.85      |
| Frankenstein                          | 875,243      | 376,304       | 13.68     |
| A Game of Thrones                     | 722,832      | 316,681       | 10.67     |
| The Great Gatsby                      | 589,211      | 224,118       | 11.58     |
| Harry Potter and the Sorcerer's Stone | 5,020,702    | 2,491,663     | 171.26    |
| Harry Potter and the Goblet of Fire   | 347,692      | 138,962       | 6.24      |
| The Hunger Games                      | 637,536      | 262,183       | 10.23     |
| The Hobbit                            | 594,250      | 249,418       | 9.86      |

Table 9: **Phase 2 API token usage and estimated cost for Gemini 2.5 Pro (total cost).** For all experiments in Sections [4.2,](#page-12-1) [4.3,](#page-15-0) and [D.2.2,](#page-36-0) we report the total per-book Phase 2 input and output tokens For each book, we sum Phase 2 input/output tokens and estimated dollar cost over all Gemini 2.5 Pro Phase 2 runs executed as part of our generation configuration parameter sweep.

<span id="page-35-0"></span>

| Book                                  | New input tokens | Cached tokens | Output tokens | Cost (\$) |
|---------------------------------------|------------------|---------------|---------------|-----------|
| 1984                                  | 227,145          | 208,325       | 6925          | 0.94      |
| Beloved                               | 6,823,988        | 6,258,609     | 76,854        | 26.32     |
| Catch-22                              | 2,096,361        | 1,922,674     | 9467          | 7.87      |
| The Catcher in the Rye                | 40,237,999       | 36,904,215    | 255,790       | 152.23    |
| The Da Vinci Code                     | 6,854,930        | 6,286,988     | 77,049        | 26.44     |
| Frankenstein                          | 20,700,031       | 18,985,000    | 51,842        | 77.12     |
| A Game of Thrones                     | 11,139,420       | 10,216,501    | 85,441        | 42.36     |
| The Great Gatsby                      | 6,872,495        | 6,303,097     | 21,526        | 25.67     |
| Harry Potter and the Sorcerer's Stone | 2,112,619        | 1,937,585     | 24,474        | 8.16      |
| Harry Potter and the Goblet of Fire   | 17,879,681       | 16,398,320    | 67,318        | 66.95     |
| The Hunger Games                      | 44,684,724       | 40,982,521    | 197,828       | 167.76    |
| The Hobbit                            | 6,168,011        | 5,656,982     | 43,374        | 23.40     |

Table 10: **Phase 2 API token usage and estimated cost for Grok 3.** For the main experiments in Section [4.2,](#page-12-1) we report Phase 2 new input tokens, cached tokens, output tokens, and total dollar cost charged by the Grok 3 API.

### <span id="page-36-0"></span>**D.2.2 Plots and tables**

We provide corresponding absolute word count plots for the eight books we do not include in Figure [7](#page-13-0) (Figures [12](#page-36-1) & [13\)](#page-37-0). In Table [11,](#page-38-0) we also include a table reporting precise numbers for nv-recall, *m*, additional, and missing for all of our main experiments in Section [4.2.](#page-12-1) In Figure [14,](#page-39-0) we provide full results on how nv-recall varied for each book, with respect to 9 generation configurations tested for Gemini 2.5 Pro.

<span id="page-36-1"></span>![](_page_36_Figure_2.jpeg)

Figure 12: **Absolute word counts.** For the Phase 2 runs for four books in Figure [5,](#page-11-1) we show the count *m* (Equation [6\)](#page-9-3) of extracted words, as well as the estimated counts of words in the book that are missing in the generated text and words in the generated text that are additional with respect to the book (Equation [8\)](#page-9-6). In each plot, the dotted gray line indicates the length of the book in words (|*B*|). We provide results for other books in Appendix [D.](#page-31-0) † indicates Phase 1 failure. *Note: The underlying generation configuration is fixed per LLM across books, but varies across LLMs. Each per-LLM set of bars conveys counts observed for the given LLM* with respect to these configurations*; for a given book, the sets of bars do not reflect comparisons of results obtained from testing all production LLMs under the same conditions.*

<span id="page-37-0"></span>![](_page_37_Figure_0.jpeg)

Figure 13: **Absolute word counts.** For the Phase 2 runs for four books in Figure [5,](#page-11-1) we show the count *m* (Equation [6\)](#page-9-3) of extracted words, as well as the estimated counts of words in the book that are missing in the generated text and words in the generated text that are additional with respect to the book (Equation [8\)](#page-9-6). In each plot, the dotted gray line indicates the length of the book in words (|*B*|). We provide results for other books in Appendix [D.](#page-31-0) † indicates Phase 1 failure; ∗ indicates that we did not run Phase 2. *Note: The underlying generation configuration is fixed per LLM across books, but varies across LLMs. Each per-LLM set of bars conveys counts observed for the given LLM* with respect to these configurations*; for a given book, the sets of bars do not reflect comparisons of results obtained from testing all production LLMs under the same conditions.*

<span id="page-38-0"></span>

| Model             | Book                                  | B       | G       | Matched (m) | nv-recall | missing | additional |
|-------------------|---------------------------------------|---------|---------|-------------|-----------|---------|------------|
| Claude 3.7 Sonnet | 1984                                  | 100,024 | 99,071  | 95,512      | 0.955     | 4,512   | 3,559      |
| Claude 3.7 Sonnet | Beloved                               | 97,759  | 101,813 | 1,957       | 0.020     | 95,802  | 99,856     |
| Claude 3.7 Sonnet | Catch-22                              | 174,344 | 74,597  | 243         | 0.001     | 174,101 | 74,354     |
| Claude 3.7 Sonnet | The Catcher in the Rye                | 73,566  | 26,323  | 7,396       | 0.101     | 66,170  | 18,927     |
| Claude 3.7 Sonnet | The Da Vinci Code                     | 139,537 | 87,552  | 1,081       | 0.008     | 138,456 | 86,471     |
| Claude 3.7 Sonnet | Frankenstein                          | 69,704  | 69,353  | 65,714      | 0.943     | 3,990   | 3,639      |
| Claude 3.7 Sonnet | A Game of Thrones                     | 292,416 | 92,569  | 16,501      | 0.056     | 275,915 | 76,068     |
| Claude 3.7 Sonnet | The Great Gatsby                      | 48,177  | 52,192  | 46,972      | 0.975     | 1,205   | 5,220      |
| Claude 3.7 Sonnet | Harry Potter and the Sorcerer's Stone | 82,382  | 78,422  | 76,001      | 0.923     | 6,381   | 2,421      |
| Claude 3.7 Sonnet | Harry Potter and the Goblet of Fire   | 198,267 | 96,703  | 70,660      | 0.356     | 127,607 | 26,043     |
| Claude 3.7 Sonnet | The Hunger Games                      | 99,964  | 105,854 | 32,581      | 0.326     | 67,383  | 73,273     |
| Claude 3.7 Sonnet | The Hobbit                            | 95,343  | 167,153 | 66,891      | 0.702     | 28,452  | 100,262    |
| Gemini 2.5 Pro    | 1984                                  | 100,024 | 29,873  | 5,913       | 0.059     | 94,111  | 23,960     |
| Gemini 2.5 Pro    | Beloved                               | 97,759  | 7,421   | 360         | 0.004     | 97,399  | 7,061      |
| Gemini 2.5 Pro    | Catch-22                              | 174,344 | 17,092  | 157         | 0.001     | 174,187 | 16,935     |
| Gemini 2.5 Pro    | The Catcher in the Rye                | 73,566  | 3,165   | 701         | 0.010     | 72,865  | 2,464      |
| Gemini 2.5 Pro    | The Da Vinci Code                     | 139,537 | 16,979  | 0           | 0.000     | 139,537 | 16,979     |
| Gemini 2.5 Pro    | Frankenstein                          | 69,704  | 6,145   | 1,684       | 0.024     | 68,020  | 4,461      |
| Gemini 2.5 Pro    | A Game of Thrones                     | 292,416 | 29,224  | 355         | 0.001     | 292,061 | 28,869     |
| Gemini 2.5 Pro    | The Great Gatsby                      | 48,177  | 5,635   | 4,519       | 0.094     | 43,658  | 1,116      |
| Gemini 2.5 Pro    | Harry Potter and the Sorcerer's Stone | 82,382  | 75,935  | 60,974      | 0.740     | 21,408  | 14,961     |
| Gemini 2.5 Pro    | Harry Potter and the Goblet of Fire   | 198,267 | 6,300   | 0           | 0.000     | 198,267 | 6,300      |
| Gemini 2.5 Pro    | The Hunger Games                      | 99,964  | 4,359   | 998         | 0.010     | 98,966  | 3,361      |
| Gemini 2.5 Pro    | The Hobbit                            | 95,343  | 5,721   | 4,921       | 0.052     | 90,422  | 800        |
| GPT-4.1           | 1984                                  | 100,024 | 5,064   | 3,585       | 0.036     | 96,439  | 1,479      |
| GPT-4.1           | Beloved                               | 97,759  | 340     | 129         | 0.001     | 97,630  | 211        |
| GPT-4.1           | The Catcher in the Rye                | 73,566  | 2,014   | 531         | 0.007     | 73,035  | 1,483      |
| GPT-4.1           | Frankenstein                          | 69,704  | 1,801   | 1,377       | 0.020     | 68,327  | 424        |
| GPT-4.1           | A Game of Thrones                     | 292,416 | 4,219   | 226         | 0.001     | 292,190 | 3,993      |
| GPT-4.1           | Harry Potter and the Sorcerer's Stone | 82,382  | 4,315   | 3,182       | 0.039     | 79,200  | 1,133      |
| GPT-4.1           | Harry Potter and the Goblet of Fire   | 198,267 | 206     | 105         | 0.001     | 198,162 | 101        |
| GPT-4.1           | The Hunger Games                      | 99,964  | 132     | 108         | 0.001     | 99,856  | 24         |
| GPT-4.1           | The Hobbit                            | 95,343  | 6,723   | 1,867       | 0.020     | 93,476  | 4,856      |
| Grok 3            | 1984                                  | 100,024 | 22,052  | 9,638       | 0.096     | 90,386  | 12,414     |
| Grok 3            | Beloved                               | 97,759  | 26,454  | 0           | 0.000     | 97,759  | 26,454     |
| Grok 3            | Catch-22                              | 174,344 | 3,507   | 0           | 0.000     | 174,344 | 3,507      |
| Grok 3            | The Catcher in the Rye                | 73,566  | 96,705  | 2,611       | 0.035     | 70,955  | 94,094     |
| Grok 3            | The Da Vinci Code                     | 139,537 | 25,965  | 0           | 0.000     | 139,537 | 25,965     |
| Grok 3            | Frankenstein                          | 69,704  | 20,417  | 1,052       | 0.015     | 68,652  | 19,365     |
| Grok 3            | A Game of Thrones                     | 292,416 | 251,025 | 3,749       | 0.013     | 288,667 | 247,276    |
| Grok 3            | The Great Gatsby                      | 48,177  | 11,255  | 7,118       | 0.148     | 41,059  | 4,137      |
| Grok 3            | Harry Potter and the Sorcerer's Stone | 82,382  | 72,078  | 56,870      | 0.690     | 25,512  | 15,208     |
| Grok 3            | Harry Potter and the Goblet of Fire   | 198,267 | 25,679  | 100         | 0.001     | 198,167 | 25,579     |
| Grok 3            | The Hunger Games                      | 99,964  | 74,153  | 2,344       | 0.023     | 97,620  | 71,809     |
| Grok 3            | The Hobbit                            | 95,343  | 130,369 | 6,910       | 0.072     | 88,433  | 123,459    |
|                   |                                       |         |         |             |           |         |            |

Table 11: **Detailed results for all main experiments.** For the runs in Figure [5\)](#page-11-1), we provide precise information for all metrics. |*B*| is the reference book length, |*G*| is generated text length, *m* is total extracted words (Equation [6\)](#page-9-3), nv-recall = *m/*|*B*| (Equation [7\)](#page-9-0); missing = |*B*|−*m* and additional = |*G*|−*m* (Equation [8\)](#page-9-6).

<span id="page-39-0"></span>![](_page_39_Figure_0.jpeg)

Figure 14: **For Gemini 2.5 Pro, comparing best** nv**-**recall **to the average over all configured runs.** We show maximum observed nv-recall for all 9 generation configuration settings per book. (See Appendix [C.2.2;](#page-29-0) max length is 2000, and we sweep over 9 combinations of frequency and presence penalty.) We also show the mean nv-recall ± STD over these 9 runs. Note that in Figure [5,](#page-11-1) so that each LLM uses a fixed configuration across books, we fix the generation configuration for Gemini 2.5 Pro; for that fixed configuration, some books exhibit the maximum nv-recall shown here (e.g., *Harry Potter and the Sorcerer's Stone*); others do not (e.g., *The Great Gatsby*).