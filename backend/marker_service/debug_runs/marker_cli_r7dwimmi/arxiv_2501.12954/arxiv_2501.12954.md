![](_page_0_Picture_1.jpeg)

![](_page_0_Picture_2.jpeg)

# Punctuation patterns in Finnegans Wake by James Joyce are largely translation-invariant

Krzysztof Bartnicki <sup>1</sup>, Stanisław Drożdż <sup>2,3,\*</sup>, Jarosław Kwapień <sup>2</sup> and Tomasz Stanisz <sup>2</sup>

- Independent researcher, Poland; gimcbart@gmail.com (K.B.)
- Complex Systems Theory Department, Institute of Nuclear Physics, Polish Academy of Sciences, 31-342 Kraków, Poland; jaroslaw.kwapien@ifj.edu.pl (J.K.); tomasz.stanisz@ifj.edu.pl (T.S.)
- Faculty of Computer Science and Telecommunications, Cracow University of Technology, 31-155 Kraków, Poland;
- Correspondence: stanislaw.drozdz@ifj.edu.pl (S.D.)

Abstract: The complexity characteristics of texts written in natural languages are significantly related to the rules of punctuation. In particular, the distances between punctuation marks measured by the number of words quite universally follow the family of Weibull distributions known from survival analyses. However, the values of two parameters marking specific forms of these distributions distinguish specific languages. This is such a strong constraint that the punctuation distributions of texts translated from the original language into another adopt quantitative characteristics of the target language. All these changes take place within Weibull distributions such that the corresponding hazard functions are always increasing. Recent previous research shows that James Joyce's famous Finnegans Wake is subject to such extreme distribution from the Weibull family that the corresponding hazard function is clearly decreasing. At the same time, the distances of sentence ending punctuation marks, determining the variability of sentence length, have an almost perfect multifractal organization, so far to such an extent found nowhere else in the literature. In the present contribution based on several available translations (Dutch, French, German, Polish, Russian) of Finnegans Wake, it is shown that the punctuation characteristics of this work remain largely translation invariant, contrary to the common cases. These observations may constitute further evidence that Finnegans Wake is a translinguistic work in this respect as well, in line with Joyce's original intention.

**Keywords:** complex systems, natural language; multiscaling: punctuation; sentence length variability; discrete Weibull distribution

# 1. Introduction

A complexity science perspective offers valuable insights into the study of natural language, as multiple traits identify it as a complex system [1,2]. Methods widely employed in analyzing complex systems — rooted in concepts from information theory [3-5], time series analysis [6–10], network science [11–19], and power-law probability distributions [20– 23] — have been utilized to explore the quantitative characteristics of natural language. Understanding the mechanisms underlying these characteristics can significantly enhance natural language processing (NLP) and generation techniques, a particularly pertinent goal in the era of large language models (LLMs) [24,25], which are foundational to generative AI systems such as OpenAI's ChatGPT, Microsoft's Bing Chat, and Google's Bard.

One language property recently analyzed using statistical approaches is punctuation usage in written texts. Research demonstrates that the distribution of word counts between consecutive punctuation marks in literary texts generally follows a discrete Weibull distribution [26–28]. Remarkably, the two parameters of this Weibull distribution are largely language-specific, reflecting the distinctive punctuation characteristics of different languages. Moreover, translations of texts into another language in general retain the Weibull distribution, but with parameter values corresponding to the target language [26,27].

![](_page_0_Picture_15.jpeg)

Joyce are largely translation-invariant.

Received: Accepted: Published

![](_page_0_Picture_18.jpeg)

Copyright: © 2024 by the authors Licensee MDPI, Basel, Switzerland This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https:// creativecommons.org/licenses/by/ 4.0/).

*Entropy* **2024**, *1*, 0 2 of 14

Sentence-ending punctuation, such as periods, deviates from this rigidity, however. The intervals thus defined, representing sentence lengths, exhibit greater variability and are not as strictly bound by the Weibull distribution, allowing for a more diverse range of patterns.

In this context *Finnegans Wake* by James Joyce is a challenging object for quantitative scientific analyses as it constitutes one of the most complex and enigmatic works of literature in the English language, known for its experimental style, inventive language that convolutes English with dozens of other languages, and it thus induces intricate, layered meanings. Many words have here multiple meanings, inviting readers to find several interpretations for each word, phrase and sentence. *Finnegans Wake* is structured to reflect the logic of a dream rather than a conventional narrative. The book begins and ends mid-sentence, creating a circular structure where the last line connects back to the first, symbolizing an endless cycle. There is no clear plot or sequence; instead, the narrative spirals, looping back on itself with characters, symbols, and themes that morph and shift. It is supposed to explore how language mirrors human consciousness and the complexity of memory, experience, and culture. Already from this perspective, it is natural to anticipate the appearance of various types of long-range correlations in the text of this book, which do not exist in traditional written texts.

Indeed, *Finnegans Wake*'s punctuation patterns, which reflect mutual arrangement in the organization of phrases and sentences, contain correlations incomparably more amazing than in any other work that has ever been subjected to this type of analysis. The most spectacular dimension of *Finnegans Wake* manifests itself in the full glory multifractality in the patterns of sentence lengths variability, largely paralleling the model mathematical cascades. The second unusual property of this work is that the longer the sequence of words uninterrupted by punctuation, the less likely it is that a punctuation mark will appear after the next word, which is a unique property among books. In the formal language of probabilistic survival analysis, this means that the hazard function expressing the need for a punctuation mark to appear if it has not been present in the sequence of words is decreasing. It is as if for a living organism the probability of surviving subsequent years increases with the age of that organism even at its age of maturity.

## **2. Materials and Methods**

## *2.1. Finnegans Wake*

James Joyce's *Finnegans Wake* is a unique and challenging work of modernist literature, known for its complex structure, innovative use of language, and unconventional narrative techniques. The opening sentence is a continuation of the final sentence, creating a loop that reflects the cyclical themes in the book. Influenced by Giambattista Vico's theory of historical cycles, the book explores patterns of rise, fall, and renewal across human history. The narrative mimics the structure of a dream, delving into subconscious associations and symbolic imagery. Central to the story is the Earwicker family, representing archetypes of father, mother, and children. The work draws on mythological, biblical, and literary sources, embedding archetypes like the trickster, the hero, and the everyman. The text eschews traditional plot for a fragmented, cyclical approach, mirroring the logic of dreams [].

The book is divided into four parts. Part I (8 chapters) introduces the central characters and themes. It sets the stage for the dreamlike narrative, blending personal and universal histories. Part II (4 chapters) focuses on the Earwicker family, including explorations of their interpersonal dynamics and symbolic representations of societal archetypes. Part III (4 chapters) contrasts rationality and structure versus creativity and chaos of the two brothers. Finally, Part IV (1 chapter) acts as a coda, bringing together the cyclical motifs of renewal and closure as ALP's (Anna Livia Plurabelle) monologue leads back to the beginning.

*Finnegans Wake* is often described as one of the most difficult works of literature due to its linguistic density and abstract narrative. It has been interpreted as a "universal dream," capturing the collective unconscious and human experience across time and space. The text is rich with references to world literature, history, philosophy, and folklore. Sentences often break grammatical rules, defying conventional readability but inviting interpretive *Entropy* **2024**, *1*, 0 3 of 14

exploration. For all these reasons *Finnegans Wake* is often described as one of the most difficult works of literature due to its linguistic density and abstract narrative.

Translating James Joyce's *Finnegans Wake* into other languages presents thus an array of unique challenges due to its experimental nature and narrative full of obscurities, ambiguities, and polyglot infusions. The text often prioritizes sound and rhythm over conventional grammar, creating a musicality that is integral to its meaning. Translating this musical quality into another language, while maintaining the sense of the text, is a delicate balancing act. Translators face the challenge of balancing fidelity to Joyce's complexity with readability for their audience. While *Finnegans Wake* is intentionally opaque, readers in the target language may lack the cultural or linguistic tools that English-speaking readers can rely on. Joyce's narrative incorporates multiple voices, tones, and registers, often blending them seamlessly. Translating this heteroglossia is difficult, especially in languages with less flexibility in tonal or dialectal variation. These are the reasons why available complete translations of this book into other languages are not very numerous but exist for several European languages. In addition to the original, five such widely recognized translations are used in the quantitative analysis presented here. They include translation into Dutch [\[29\]](#page-12-8), French [\[30\]](#page-12-9), German [\[31\]](#page-12-10), Polish [\[32\]](#page-12-11) and Russian [\[33\]](#page-12-12).

### *2.2. Discrete Weibull distribution*

Punctuation can be understood as a mechanism for interrupting the continuous flow of words, enhancing the clarity of the message and providing necessary pauses for the reader. These functions align well with the framework of survival analysis [\[34\]](#page-12-13). Prior studies have established that distances between punctuation marks follow distributions that can be modeled using the discrete Weibull distribution [\[26](#page-12-5)[,27\]](#page-12-7). This distribution is defined by the following probability mass function [\[35\]](#page-12-14):

<span id="page-2-0"></span>
$$f(k) = (1-p)^{k^{\beta}} - (1-p)^{(k+1)^{\beta}}, \quad p \in (0,1), \quad \beta > 0$$
 (1)

and its cumulative distribution function:

$$\mathcal{F}(k) = 1 - (1 - p)^{k^{\beta}}.\tag{2}$$

The cumulative distribution function represents the probability that the random variable exceeds the value *k*. The discrete Weibull distribution generalizes the geometric distribution, which is recovered when *β* = 1, resulting in a constant probability F(*k*) over time. When *β* > 1, the probability increases with time, while for *β* < 1, it decreases. This distribution has broad applications in fields such as survival analysis, weather prediction, and textual data analysis [\[34](#page-12-13)[,36](#page-12-15)[,37\]](#page-12-16). In the context of punctuation, *f*(*k*) denotes the probability that a punctuation mark will appear precisely after *k* words.

A complementary approach to the above generalization can be readily and transparently formulated in terms of the hazard function *λ*(*k*) expressing the conditional probability that the *k*th trial will result in a success provided that no success has occurred in the preceding *k* − 1 trials:

<span id="page-2-1"></span>
$$\lambda(k) = \frac{f(k)}{1 - \mathcal{F}(k-1)}. (3)$$

In the case of the discrete Weibull distribution it becomes [\[38\]](#page-12-17):

$$\lambda(k) = 1 - (1 - p)^{k^{\beta} - (k - 1)^{\beta}}. (4)$$

For data that exactly follows a Weibull distribution *β* > 1 corresponds to *λ*(*k*) which is an increasing function of *k*. In other words the probability of success increases with the number of preceding unsuccessful trials. The opposite applies to *β* < 1. In the *memoryless* case of *β* = 1, the hazard function is constant. Since *p* = *λ*(1) the parameter *p* reflects the probability of putting a punctuation mark right after the first word following the last punctuation mark.

Entropy 2024, 1, 0 4 of 14

## 2.3. Multifractal detrended fluctuation analysis (MFDFA)

Self-similarity, or the absence of a characteristic scale, is a defining feature of natural complex systems. Empirically, this property often manifests as a non-trivial temporal organization in measurement outcomes, represented as a time series. Specifically, complexity is frequently linked to a cascade-like hierarchy of data points exhibiting multiscaling, underscoring the importance of practical methods for identifying such structures in complex systems research [39]. Drawing on current research, multifractal detrended fluctuation analysis (MFDFA) has proven to be a highly reliable method for analyzing multiscaling structures [40,41]. This technique builds upon the widely adopted detrended fluctuation analysis (DFA) [42], offering a multiscale approach to studying hierarchical and multiscaling patterns. Below, we provide a concise outline of the key steps involved in the MFDFA algorithm.

Consider a time series  $U = \{u_i\}_{i=1}^T$ , consisting of T consecutive measurements of an observable u. This series is divided into  $M_s$  non-overlapping windows, each of length s, starting from both ends of U, resulting in a total of  $2M_s$  windows. To address potential non-stationarity in the signal, a detrending procedure is applied within each window to an integrated signal (referred to as the profile)  $X = \{x_i\}_{i=1}^s$ , with elements defined as:

$$x_i = \sum_{j=1}^i u_j. (5)$$

The detrending process involves fitting a polynomial  $P^{(m)}$  of order m (with m=2 used throughout this study) to the data X within each window  $v=0,\ldots,2M_s-1$ . The variance of the detrended signal obtained after subtracting the fitted polynomial is then computed:

$$f^{2}(\nu,s) = \frac{1}{s} \sum_{i=1}^{s} (x_{i} - P^{(m)}(i))^{2}.$$
 (6)

In the next step, a family of fluctuation functions of order q is defined using the average variance computed across all windows:

<span id="page-3-0"></span>
$$F_q(s) = \left\{ \frac{1}{2M_s} \sum_{\nu=0}^{2M_s - 1} \left[ f^2(\nu, s) \right]^{q/2} \right\}^{1/q}. \tag{7}$$

Here, q is a real number. The fluctuation functions  $F_q(s)$  are computed for various values of the scale s and the index q. Typically, the minimum s is selected to exceed the length of the longest sequence of constant values in U, while the maximum s is set to T/5. Unlike s, there is no standard range for q. Since q is associated with the moments of the signal, extreme values should be avoided for time series with heavy tails to ensure meaningful results. If the fluctuation functions depend on s as power laws:

<span id="page-3-1"></span>
$$F_q(s) \sim s^{h(q)} \tag{8}$$

for a number of different choices of q, it indicates that the time series under study is either monofractal (when h(q) is constant in q) or multifractal otherwise. The function h(q) is called the generalized Hurst exponent, because for q=2, h(q)=H, where H is the standard Hurst exponent [43,44]. From a visual perspective, fractal  $F_q(s)$  organizations result in straight lines on double logarithmic plots.

A practical representation of the multifractal characteristics of data is the singularity spectrum  $f(\alpha)$ , which can be derived from h(q) by the Legendre transform:

<span id="page-3-2"></span>
$$\alpha = h(q) + qh'(q),$$
  

$$f(\alpha) = q[\alpha - h(q)] + 1,$$
(9)

*Entropy* **2024**, *1*, 0 5 of 14

Here, *α* represents the measure of data-point singularity, equivalent to the Hölder exponent. Geometrically, *f*(*α*) can be interpreted as the fractal dimension of the subset of the data characterized by a specific Hölder exponent *α* [\[45\]](#page-12-24). For a monofractal time series, the pair (*α*, *f*(*α*)) reduces to a single point. In contrast, for a multifractal time series, it typically forms a downward-pointing parabola. The broader the singularity spectrum *f*(*α*), the greater the richness of multifractality in the time series, which serves as an indicator of its complexity content. In some cases, the *f*(*α*) parabola may appear distorted or asymmetric, suggesting that data points of varying amplitudes exhibit different scaling behaviors [\[46–](#page-12-25) [50\]](#page-13-0).

### **3. Results and Discussion**

#### *3.1. Inter-punctuation intervals (IPI)*

The results illustrating the characteristics of the distributions of distances between all consecutive punctuation marks for *Finnegans Wake* in the original and its five abovementioned translations are shown in Fig. [1.](#page-5-0) The panels in the left column show the corresponding normalized counts for increasing values of the distance *k* measured by the number of words between consecutive punctuation marks. These empirical distributions are then fitted by the formula of Eq. [\(1\)](#page-2-0) and the parameters *p* and *β* of the best fits are explicitly given in the corresponding panels. For *Finnegans Wake* in the original, it is a good fit, which was already presented in ref. [\[51\]](#page-13-1), but, remarkably, the parameter *β* here is less than 1 in contrast to the multiplicity of all other literary texts studied [\[26\]](#page-12-5) written in the major European languages, even those classified as belonging to experimental literature [\[51\]](#page-13-1). In general, the Weibull functional form describes well the distributions of distances between consecutive punctuation marks, but the corresponding parameters are somewhat different and on average are language-specific, so that they even undergo appropriate transformations in translations. The special case of *Finnegans Wake* analyzed here, in its uniqueness, turns out to be much less susceptible to changing the values of these parameters. For translations into Dutch and French they even remain almost exactly unchanged. For the translation into Polish *β* approaches the limit of 1 but does not exceed it, while for typical texts in this language ⟨*β*⟩ ≈ 1.4. For the two remaining translations, German and Russian, *β* exceeds the value of 1, especially clearly for the Russian translation considered here, although in both of these cases it remains below the average value characteristic for these languages [\[26\]](#page-12-5). In this context, it should be noted here at the same time that the quality of the fit is slightly worse in these two cases, especially for small values of *k*.

A complementary insight into the specificity of the punctuation distribution is obtained through the hazard function *λ*(*k*) defined by Eq. [\(3\)](#page-2-1). It gives a better perspective on the asymptotics of the distribution at larger values of *k*. These functions calculated directly from empirical data (not from the *p* and *β* fit parameters using the Weibull distribution) are presented in parallel on the right side of Fig. [1.](#page-5-0) As it can be seen from this perspective, all translations have a similar, decreasing asymptotics, with the Dutch and French translations having almost the same course as the English original. Apart from an initial slightly larger increase, the Polish translation behaves similarly. Such initial increases in *λ*(*k*) are more pronounced for German and Russian translations, but for larger *k* the decreases start to prevail even in these cases.

#### *3.2. Long-range correlations in IPI*

The distributions of fluctuations are one of the important characteristics of time series. With the same distributions, however, such series may differ in the arrangement of successive values in the series relative to each other. The MFDFA formalism presented above is well suited to quantifying possible long-range correlations of this type and is therefore applied to the time series of successive IPI's analyzed here, proceeding through the entire text of the book.

*Entropy* **2024**, *1*, 0 6 of 14

<span id="page-5-0"></span>![](_page_5_Figure_1.jpeg)

**Figure 1.** The distributions of the distances between consecutive punctuation marks (left column) and the corresponding hazard functions (right column) in *Finnegans Wake* and its translations.

*Entropy* **2024**, *1*, 0 7 of 14

The series of distances measured in word counts between all consecutive punctuation marks for the original *Finnegans Wake* and its five translations are visualized in the left panels of Fig. [2.](#page-7-0) The same scale is used on the vertical axis to make the relative values directly visible. As it can be seen immediately, these series for the Dutch and French translations have strongly similar values and courses to those for the English original. The Polish translation is also quite consistent with these values. For the German translation some correspondence is also noticeable, but there are clearly more small numbers here and so the series is longer than in the above cases. An extreme case is the Russian translation, where the values are on average even significantly smaller, so their number in the series is even greater than for the German translation.

The nature of the long-range correlations encoded in these series is quantified within MFDFA in terms of the fluctuations functions *Fq*(*s*) expressed by the formula Eq. [\(7\)](#page-3-0). These functions, calculated for −4 ≤ *q* ≤ 4 and plotted in the right-hand panels of Fig. [2,](#page-7-0) respectively, show clear scaling (straight line on the log-log scale) but this is not a convincing multifractal scaling because the dependence of these functions on *q* is weak. These dependencies are rather close to monofractal. The slope of *Fq*(*s*) lines is, however, clearly larger than 0.5 and such are in particular the Hurst exponents *H* = *h*(*q* = 2), red line in this Figure) determined by Eq. [\(8\)](#page-3-1) and they are found to lie in the range 0.65 ≤ *H* ≤ 0.75. This indicates clear long-range correlations of a persistent nature. The Polish translation, which is at the upper end of the *H*-value range, is the most extreme in this respect.

The illustration that complements this section, shown in Fig. [3,](#page-8-0) explicitly demonstrates one of the extreme examples of differences in the distribution of punctuation in some translations of *Finnegans Wake*. The plot presents the relative arrangement of punctuation marks in a sample two-paragraph excerpt from the book. The discussed excerpt starts at the beginning of the last paragraph on page 579 and ends at the end of page 580 in the original, English version. Clearly, consistent with the previous observations, the first three cases (English, Dutch, and French) differ least while the Russian translation differs most by generating many much shorter IPI's.

# *3.3. Multifractal sentence length variability (SLV)*

The distribution of distances between all punctuation marks clearly follows certain fairly universal rigors, which have already been shown by previous recent studies and which are confirmed to a large extent even for such an exceptional work as the one examined here, *Finnegans Wake*. At the same time, however, the distribution of the punctuation marks ending sentences (such as periods, question marks, and exclamation marks) have much more freedom in this respect. The distances between them are precisely the lengths of sentences. It has already been shown [\[52\]](#page-13-2) that *Finnegans Wake* develops a self-similar cascade of SLV with exceptionally richly developed multifractal properties. Such patterns appear only in literary works written using the narrative technique of stream of consciousness, and *Finnegans Wake* is the most spectacular in this respect, both in terms of an almost ideal symmetry of the resulting singularity spectrum (Eq. [\(9\)](#page-3-2)) as well as in the sense of the width of this spectrum. The main goal of the present study is to examine to what extent these properties are preserved in the translations available here.

The results collected in multi-panel Fig. [4](#page-9-0) clearly indicate that, in this respect, the translations largely faithfully preserve the multifractal characteristics of the original, and in the two cases of French and Polish this mapping is almost perfect. The patterns of variation of successive sentence lengths are strikingly similar here, and this applies even to their absolute values, as can be seen on the vertical scales of the upper panels of this figure. Consequently, the total number of sentences is also similar, as it can be seen on the horizontal scales of these panels. This applies even to the Russian translation, which showed greater discrepancies in the case of full punctuation. The functions *Fq*(*s*) show very good scaling strongly dependent on *q*, comparably in all cases. As a consequence, the multifractal spectra *f*(*α*) are alike, broad (∆*α* ≈ 1), and vary only slightly. Minor asymmetries in the spectra can also be observed. For Dutch and Russian, they are right*Entropy* **2024**, *1*, 0 8 of 14

<span id="page-7-0"></span>![](_page_7_Figure_1.jpeg)

**Figure 2.** Time series representing the distances between consecutive punctuation marks (left column) and the corresponding fluctuation functions (right column) in *Finnegans Wake* and its translations. In each of the fluctuation functions plot, the function for *q* = 2 is marked in red and the Hurst exponent *H* is given in the bottom-right corner.

*Entropy* **2024**, *1*, 0 9 of 14

<span id="page-8-0"></span>![](_page_8_Figure_1.jpeg)

**Figure 3.** The relative arrangement of punctuation marks corresponding to the six considered cases of the original *Finnegans Wake* and its Dutch, French, German, Polish, and Russian translations, in a two-paragraph excerpt from the book (starting at the beginning of the last paragraph on page 579 and ending at the end of page 580 in the original, English version).

sided and for German they are left-sided. This indicates [\[48\]](#page-12-26) that, in the first two cases, the hierarchy of multifractal correlations is somewhat more developed towards variability of shorter sentence lengths than longer ones, while in the third case (German) it is the other way around. The multifractal spectra of the French and Polish translations are almost exactly symmetrical, similarly to the English original. All these spectra are also significantly shifted to the right with respect to *α* = 0.5, which signals a clear persistent trend in sentence length variability. This property is also confirmed in terms of the corresponding Hurst exponents *H*, which are calculated as scaling exponents for *Fq*=2(*s*), marked in red in these Figures. Their corresponding values turn out to be even slightly higher than those when considering the variation of distances between all successive punctuation marks, which has been marked in Fig. [2.](#page-7-0)

# **4. Summary and conclusions**

This study explored the intricate punctuation patterns and sentence length variability within James Joyce's *Finnegans Wake* and its translations into five languages: Dutch, French, German, Polish, and Russian. Through a combination of statistical methods, including the discrete Weibull distribution and multifractal detrended fluctuation analysis (MFDFA), it is identified that punctuation usage in *Finnegans Wake* defies conventional linguistic norms. Unlike typical texts, its punctuation patterns remain largely translation-invariant, reflecting Joyce's intentional crafting of a translinguistic narrative.

The findings highlight two distinct characteristics. The text exhibits a rare decreasing hazard function in its punctuation intervals, a trait only observed in *Finnegans Wake* among analyzed works. This uniqueness persists across most translations, with minor variations reflecting linguistic differences, or, what cannot be excluded, some bias related to the translation fidelity. The multifractal properties of sentence lengths in *Finnegans Wake* demonstrate an extraordinary degree of self-similarity and complexity. This trait is preserved remarkably well in translations, particularly in French and Polish versions, underscoring the robustness of the text's structural organization. These results contribute to a deeper understanding of the interplay between linguistic structure and translation fidelity, affirming the universal complexity embedded in Joyce's work.

*Entropy* **2024**, *1*, 0 10 of 14

<span id="page-9-0"></span>![](_page_9_Figure_1.jpeg)

**Figure 4.** Time series representing sentence lengths, the corresponding fluctuation functions *Fq*(*s*), and singularity spectra *f*(*α*) in *Finnegans Wake* and its translations. In each of the fluctuation function plots, *Fq*(*s*) for *q* = 2 is marked in red and the Hurst exponent *H* value is given in the bottom-right corner.

*Entropy* **2024**, *1*, 0 11 of 14

![](_page_10_Figure_1.jpeg)

**Figure 4.** (continued) Time series representing sentence lengths, the corresponding fluctuation functions *Fq*(*s*), and singularity spectra *f*(*α*) in *Finnegans Wake* and its translations. In each of the fluctuation function plots, *Fq*(*s*) for *q* = 2 is marked in red and the Hurst exponent *H* value is given in the bottom-right corner.

*Entropy* **2024**, *1*, 0 12 of 14

The study confirms that *Finnegans Wake* exemplifies a rare literary phenomenon where structural properties transcend linguistic boundaries, maintaining coherence in complexity across translations. This underscores the text's suitability for cross-disciplinary analysis, superimposing linguistics, literature, and complexity science. By demonstrating that punctuation and sentence organization are integral to the text's identity, this research highlights the intricate balance between translation and preservation of artistic intent.

Future research could extend these methods to other experimental literary works to further explore the universality of such translinguistic traits. Additionally, integrating advanced computational techniques and larger datasets might provide new insights into the quantitative characteristics of experimental literature, which explores the deeper layers and possibilities of natural language.

**Author Contributions:** Conceptualization, K.B., S.D., J.K. and T.S.; Methodology, S.D., J.K. and T.S.; Software, J.K. and T.S.; Validation, K.B., S.D., J.K. and T.S.; Formal analysis, S.D., J.K. and T.S.; Investigation, S.D., J.K. and T.S.; Resources, K.B. and T.S.; Data curation, K.B. and T.S.; Writing original draft, S.D.; Writing—review & editing, K.B., S.D., J.K. and T.S.; Visualization, J.K. and T.S.; Supervision, S.D.

**Funding:** This research received no external funding.

**Institutional Review Board Statement:** Not applicable.

**Data Availability Statement:** The data presented in this study are available on request from the corresponding author. The data are not publicly available due to copyright.

**Conflicts of Interest:** The authors declare no conflicts of interest.

#### **References**

- <span id="page-11-0"></span>1. Hébert-Dufresne, L.; Allard, A.; Garland, J.; Hobson, E.A.; Zaman, L. The path of complexity. *npj Complexity* **2024**, *1*. [https://doi.org/10.1038/s44260-024-00004-0.](https://doi.org/10.1038/s44260-024-00004-0)
- <span id="page-11-1"></span>2. Kwapie´n, J.; Drozd˙ z, S. Physical approach to complex systems. ˙ *Physics Reports* **2012**, *515*, 115–226. [https://doi.org/10.1016/j.](https://doi.org/10.1016/j.physrep.2012.01.007) [physrep.2012.01.007.](https://doi.org/10.1016/j.physrep.2012.01.007)
- <span id="page-11-2"></span>3. D˛ebowski, L. *Information Theory Meets Power Laws: Stochastic Processes and Language Models*; Wiley, 2020. [https://doi.org/10.1002/](https://doi.org/10.1002/9781119625384) [9781119625384.](https://doi.org/10.1002/9781119625384)
- 4. Takahira, R.; Tanaka-Ishii, K.; D˛ebowski, L. Entropy Rate Estimates for Natural Language—A New Extrapolation of Compressed Large-Scale Corpora. *Entropy* **2016**, *18*, 364. [https://doi.org/10.3390/e18100364.](https://doi.org/10.3390/e18100364)
- <span id="page-11-3"></span>5. Montemurro, M.A.; Zanette, D.H. Universal Entropy of Word Ordering Across Linguistic Families. *PLoS ONE* **2011**, *6*, e19875. [https://doi.org/10.1371/journal.pone.0019875.](https://doi.org/10.1371/journal.pone.0019875)
- <span id="page-11-4"></span>6. Alvarez-Lacalle, E.; Dorow, B.; Eckmann, J.P.; Moses, E. Hierarchical structures induce long-range dynamical correlations in written texts. *PNAS* **2006**, *103*, 7956–7961. [https://doi.org/10.1073/pnas.0510673103.](https://doi.org/10.1073/pnas.0510673103)
- 7. Liu, J.; Gunn, E.; Youssef, F.; Tharayil, J.; Lansford, W.; Zeng, Y. Fractality in Chinese prose. *Digital Scholarship in the Humanities* **2023**, *38*, 604–620. [https://doi.org/10.1093/llc/fqac062.](https://doi.org/10.1093/llc/fqac062)
- 8. Sánchez, D.; Zunino, L.; Gregorio, J.D.; Toral, R.; Mirasso, C. Ordinal analysis of lexical patterns. *Chaos* **2023**, *33*, 033121. [https://doi.org/10.1063/5.0139852.](https://doi.org/10.1063/5.0139852)
- 9. Pawłowski, A. Time-Series analysis in linguistics: Application of the ARIMA method to cases of spoken Polish. *Journal of Quantitative Linguistics* **1997**, *4*, 203–221. [https://doi.org/10.1080/09296179708590097.](https://doi.org/10.1080/09296179708590097)
- <span id="page-11-5"></span>10. Kosmidis, K.; Kalampokis, A.; Argyrakis, P. Language time series analysis. *Physica A* **2006**, *370*, 808–816. [https://doi.org/10.101](https://doi.org/10.1016/j.physa.2006.02.042) [6/j.physa.2006.02.042.](https://doi.org/10.1016/j.physa.2006.02.042)
- <span id="page-11-6"></span>11. Cancho, R.F.i.; Solé, R.V. The small world of human language. *Proceedings of the Royal Society of London. Series B: Biological Sciences* **2001**, *268*, 2261–2265. [https://doi.org/10.1098/rspb.2001.1800.](https://doi.org/10.1098/rspb.2001.1800)
- 12. Amancio, D.R.; Antiqueira, L.; Pardo, T.A.S.; Da, L.; Costa, F.; Oliveira, O.N.; Nunes, M.G.V. Complex networks analysis of manual and machine translations. *International Journal of Modern Physics C* **2008**, *19*, 583–598.
- 13. Liu, H.; Xu, C. Can syntactic networks indicate morphological complexity of a language? *Europhysics Letters* **2011**, *93*, 28005. [https://doi.org/10.1209/0295-5075/93/28005.](https://doi.org/10.1209/0295-5075/93/28005)
- 14. Cong, J.; Liu, H. Approaching human language with complex networks. *Physics of Life Reviews* **2014**, *11*, 598–618. [https:](https://doi.org/10.1016/j.plrev.2014.04.004) [//doi.org/10.1016/j.plrev.2014.04.004.](https://doi.org/10.1016/j.plrev.2014.04.004)
- 15. Wachs-Lopes, G.A.; Rodrigues, P.S. Analyzing natural human language from the point of view of dynamic of a complex network. *Expert Systems with Applications* **2016**, *45*, 8–22. [https://doi.org/10.1016/j.eswa.2015.09.020.](https://doi.org/10.1016/j.eswa.2015.09.020)
- 16. Kulig, A.; Kwapie ´n, J.; Stanisz, T.; Drozd˙ z, S. In narrative texts punctuation marks obey the same statistics as words. ˙ *Information Sciences* **2017**, *375*, 98–113. [https://doi.org/10.1016/j.ins.2016.09.051.](https://doi.org/10.1016/j.ins.2016.09.051)

*Entropy* **2024**, *1*, 0 13 of 14

17. Akimushkin, C.; Amancio, D.R.; Oliveira, O.N. Text authorship identified using the dynamics of word co-occurrence networks. *PLoS ONE* **2017**, *12*, 0170527. [https://doi.org/10.1371/journal.pone.0170527.](https://doi.org/10.1371/journal.pone.0170527)

- 18. Stanisz, T.; Kwapie ´n, J.; Drozd˙ z, S. Linguistic data mining with complex networks: A stylometric-oriented approach. ˙ *Information Sciences* **2019**, *482*, 301–320. [https://doi.org/10.1016/j.ins.2019.01.040.](https://doi.org/10.1016/j.ins.2019.01.040)
- <span id="page-12-0"></span>19. Raducha, T.; Gubiec, T. Predicting language diversity with complex networks. *PLOS ONE* **2018**, *13*, e0196593. [https:](https://doi.org/10.1371/journal.pone.0196593) [//doi.org/10.1371/journal.pone.0196593.](https://doi.org/10.1371/journal.pone.0196593)
- <span id="page-12-1"></span>20. Naranan, S.; Balasubrahmanyan, V. Models for power law relations in linguistics and information science. *Journal of Quantitative Linguistics* **1998**, *5*, 35–61. [https://doi.org/10.1080/09296179808590110.](https://doi.org/10.1080/09296179808590110)
- 21. Newman, M. Power laws, Pareto distributions and Zipf's law. *Contemporary Physics* **2005**, *46*, 323–351. [https://doi.org/10.1080/](https://doi.org/10.1080/00107510500052444) [00107510500052444.](https://doi.org/10.1080/00107510500052444)
- 22. Ausloos, M. Punctuation effects in english and esperanto texts. *Physica A* **2010**, *389*, 2835–2840. [https://doi.org/10.1016/j.physa.](https://doi.org/10.1016/j.physa.2010.02.038) [2010.02.038.](https://doi.org/10.1016/j.physa.2010.02.038)
- <span id="page-12-2"></span>23. Piantadosi, S.T. Zipf's word frequency law in natural language: A critical review and future directions. *Psychonomic Bulletin & Review* **2014**, *21*, 1112–1130. [https://doi.org/10.3758/s13423-014-0585-6.](https://doi.org/10.3758/s13423-014-0585-6)
- <span id="page-12-3"></span>24. Shanahan, M.; McDonell, K.; Reynolds, L. Role play with large language models. *Nature* **2023**, *623*, 493–498. [https://doi.org/10.1](https://doi.org/10.1038/s41586-023-06647-8) [038/s41586-023-06647-8.](https://doi.org/10.1038/s41586-023-06647-8)
- <span id="page-12-4"></span>25. Zhao, W.X.; Zhou, K.; Li, J.; Tang, T.; Wang, X.; Hou, Y.; Min, Y.; Zhang, B.; Zhang, J.; Dong, Z.; et al. A Survey of Large Language Models. Preprint arXiv:2303.18223v13 (2023).
- <span id="page-12-5"></span>26. Stanisz, T.; Drozd˙ z, S.; Kwapie´n, J. Universal versus system-specific features of punctuation usage patterns in major Western ˙ languages. *Chaos, Solitons & Fractals* **2023**, *168*, 113183. [https://doi.org/10.1016/j.chaos.2023.113183.](https://doi.org/10.1016/j.chaos.2023.113183)
- <span id="page-12-7"></span>27. Stanisz, T.; Drozd˙ z, S.; Kwapie´n, J. Complex systems approach to natural language. ˙ *Physics Reports* **2024**, *1053*, 1–84. [https:](https://doi.org/10.1016/j.physrep.2023.12.002) [//doi.org/10.1016/j.physrep.2023.12.002.](https://doi.org/10.1016/j.physrep.2023.12.002)
- <span id="page-12-6"></span>28. Dec, J.; Dolina, M.; Drozd˙ z, S.; Kwapie ´n, J.; Stanisz, T. Multifractal Hopscotch in ˙ *Hopscotch* by Julio Cortázar. *Entropy* **2024**, *26*, 716. [https://doi.org/10.3390/e26080716.](https://doi.org/10.3390/e26080716)
- <span id="page-12-8"></span>29. Joyce, J. Finnegans Wake [Dutch: Finnegans Wake]. Transl. Erik Bindervoet; Robbert-Jan Henkes. Amsterdam, 2002.
- <span id="page-12-9"></span>30. Joyce, J. Finnegans Wake [French: Veillée Pinouilles]. Transl. Hervé Michel. Online, 2014.
- <span id="page-12-10"></span>31. Joyce, J. Finnegans Wake [German: Finnegans Wehg]. Transl. Dieter H. Stündel. Frankfurt am Main, 1993.
- <span id="page-12-11"></span>32. Joyce, J. Finnegans Wake [Polish: Finneganów tren]. Transl. Krzysztof Bartnicki. Cracow, 2012.
- <span id="page-12-12"></span>33. Joyce, J. Finnegans Wake [Russian: Na pomine Finneganov]. Transl. Andrey Rene. Moscow, 2021.
- <span id="page-12-13"></span>34. Miller, R. *Survival Analysis*; John Wiley & Sons, 1997.
- <span id="page-12-14"></span>35. Nakagawa, T.; Osaki, S. The discrete Weibull distribution. *IEEE Transactions on Reliability* **1975**, *R-24*, 300–301. [https://doi.org/10](https://doi.org/10.1109/tr.1975.5214915) [.1109/tr.1975.5214915.](https://doi.org/10.1109/tr.1975.5214915)
- <span id="page-12-15"></span>36. Johnson, N.L.; Kotz, S.; Balakrishnan, N. *Continuous Univariate Distributions*; Wiley-Interscience, 1994.
- <span id="page-12-16"></span>37. Altmann, E.G.; Pierrehumbert, J.B.; Motter, A.E. Beyond Word Frequency: Bursts, Lulls, and Scaling in the Temporal Distributions of Words. *PLoS ONE* **2009**, *4*, e7678. [https://doi.org/10.1371/journal.pone.0007678.](https://doi.org/10.1371/journal.pone.0007678)
- <span id="page-12-17"></span>38. Padgett, W.J.; Spurrier, J.D. On discrete failure models. *IEEE Transactions on Reliability* **1985**, *34*, 253–256.
- <span id="page-12-18"></span>39. Jimenez, J. Intermittency and cascades. *Journal of Fluid Mechanics* **2000**, *409*, 99–120.
- <span id="page-12-19"></span>40. Kantelhardt, J.W.; Zschiegner, S.A.; Koscielny-Bunde, E.; Havlin, S.; Bunde, A.; Stanley, H. Multifractal detrended fluctuation analysis of nonstationary time series. *Physica A* **2002**, *316*. [https://doi.org/10.1016/s0378-4371\(02\)01383-3.](https://doi.org/10.1016/s0378-4371(02)01383-3)
- <span id="page-12-20"></span>41. O´swi˛ecimka, P.; Kwapie ´n, J.; Drozd˙ z, S. Wavelet versus detrended fluctuation analysis of multifractal structures. ˙ *Physical Review E* **2006**, *74*, 016103. [https://doi.org/10.1103/PhysRevE.74.016103.](https://doi.org/10.1103/PhysRevE.74.016103)
- <span id="page-12-21"></span>42. Peng, C.K.; Buldyrev, S.V.; Havlin, S.; Simons, M.; Stanley, H.E.; Goldberger, A.L. Mosaic organization of DNA nucleotides. *Physical Review E* **1994**, *49*. [https://doi.org/10.1103/physreve.49.1685.](https://doi.org/10.1103/physreve.49.1685)
- <span id="page-12-22"></span>43. Hurst, H.E. The long-term storage capacity of reservoir. *Transactions of the American Society of Civil Engineers* **1951**, *116*, 2447. [https://doi.org/10.1061/TACEAT.000651.](https://doi.org/10.1061/TACEAT.000651)
- <span id="page-12-23"></span>44. Heneghan, C.; McDarby, G. Establishing the relation between detrended fluctuation analysis and power spectral density analysis for stochastic processes. *Physical Review E* **2000**, *62*, 6103–6110.
- <span id="page-12-24"></span>45. Halsey, T.C.; Jensen, M.H.; Kadanoff, L.P.; Procaccia, I.; Shraimant, B.I. Fractal measures and their singularities: The characterization of strange sets. *Physical Review A* **1986**, *33*, 1141–1151.
- <span id="page-12-25"></span>46. Ohashi, K.; Amaral, L.A.; Natelson, B.H.; Yamamoto, Y. Asymmetrical singularities in real-world signals. *Physical Review E* **2003**, *68*. [https://doi.org/10.1103/PhysRevE.68.065204.](https://doi.org/10.1103/PhysRevE.68.065204)
- 47. Cao, G.; Cao, J.; Xu, L. Asymmetric multifractal scaling behavior in the Chinese stock market: Based on asymmetric MF-DFA. *Physica A* **2013**, *392*, 797–807. [https://doi.org/https://doi.org/10.1016/j.physa.2012.10.042.](https://doi.org/https://doi.org/10.1016/j.physa.2012.10.042)
- <span id="page-12-26"></span>48. Drozd˙ z, S.; O´swi˛ecimka, P. Detecting and interpreting distortions in hierarchical organization of complex time series. ˙ *Physical Review E* **2015**, *91*, 030902(R). [https://doi.org/10.1103/PhysRevE.91.030902.](https://doi.org/10.1103/PhysRevE.91.030902)
- 49. Gómez-Gómez, J.; Carmona-Cabezas, R.; Ariza-Villaverde, A.B.; Gutiérrez de Ravé, E.; Jiménez-Hornero, F.J. Multifractal detrended fluctuation analysis of temperature in Spain (1960–2019). *Physica A* **2021**, *578*, 126118. [https://doi.org/https:](https://doi.org/https://doi.org/10.1016/j.physa.2021.126118) [//doi.org/10.1016/j.physa.2021.126118.](https://doi.org/https://doi.org/10.1016/j.physa.2021.126118)

*Entropy* **2024**, *1*, 0 14 of 14

<span id="page-13-0"></span>50. Kwapie´n, J.; Watorek, M.; Bezbradica, M.; Crane, M.; Mai, T.T.; Drozdz, S. Analysis of inter-transaction time fluctuations in the cryptocurrency market. *Chaos* **2022**, *32*, 083142. [https://doi.org/10.1063/5.0104707.](https://doi.org/10.1063/5.0104707)

- <span id="page-13-1"></span>51. Stanisz, T.; Drozd˙ z, S.; Kwapie ´n, J. Statistics of punctuation in experimental literature – the remarkable case of ˙ *Finnegans Wake* by James Joyce. Chaos: An Interdisciplinary Journal of Nonlinear Science, 2024, in print.
- <span id="page-13-2"></span>52. Drozd˙ z, S.; O´swi˛ecimka, P.; Kulig, A.; Kwapie´n, J.; Bazarnik, K.; Grabska-Gradzi ´nska, I.; Rybicki, J.; Stanuszek, M. Quantifying ˙ origin and character of long-range correlations in narrative texts. *Information Sciences* **2016**, *331*, 32–44. [https://doi.org/10.1016/j.](https://doi.org/10.1016/j.ins.2015.10.023) [ins.2015.10.023.](https://doi.org/10.1016/j.ins.2015.10.023)

**Disclaimer/Publisher's Note:** The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.