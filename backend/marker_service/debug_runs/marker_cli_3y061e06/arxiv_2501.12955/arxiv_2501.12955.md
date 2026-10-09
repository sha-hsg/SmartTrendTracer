![](_page_0_Picture_1.jpeg)

![](_page_0_Picture_2.jpeg)

Article

# Multifractal Hopscotch in *Hopscotch* by Julio Cortázar

Jakub Dec 10, Michał Dolina 10, Stanisław Drożdż 1,2,\*0, Jarosław Kwapień 2,\*0 and Tomasz Stanisz 20

- Faculty of Computer Science and Telecommunications, Cracow University of Technology, 31-155 Kraków, Poland; jakub.dec@pk.edu.pl (J.D.); michal.dolina@pk.edu.pl (M.D.)
- Complex Systems Theory Department, Institute of Nuclear Physics, Polish Academy of Sciences, 31-342 Kraków, Poland: tomasz.stanisz@ifi.edu.pl
- Correspondence: stanislaw.drozdz@ifj.edu.pl (S.D.); jaroslaw.kwapien@ifj.edu.pl (J.K.)

Abstract: Punctuation is the main factor introducing correlations in natural language written texts and it crucially impacts their overall effectiveness, expressiveness, and readability. Punctuation marks at the end of sentences are of particular importance as their distribution can determine various complexity features of written natural language. Here, the sentence length variability (SLV) time series representing *Hopscotch* by Julio Cortázar are subjected to quantitative analysis with an attempt to identify their distribution type, long-memory effects, and potential multiscale patterns. The analyzed novel is an important and innovative piece of literature whose essential property is freedom of movement between its building blocks given to a reader by the author. The statistical consequences of this freedom are closely investigated in both the original, Spanish version of the novel, and its translations into English and Polish. Clear evidence of rich multifractality in the SLV dynamics, with a left-sided asymmetry, however, is observed in all three language versions as well as in the versions with differently ordered chapters.

**Keywords:** natural language; punctuation; sentence length variability; multiscaling; discrete Weibull distribution

#### 1. Introduction

One of the perspectives on research on natural language is the one derived from complexity science [1,2]—as multiple traits identify natural language as a complex system [3]. Numerous methods widely used in studying complex systems, based on concepts originating in information theory [4–6], time series analysis [7–11], network science [12–18] and the theory of power-law probability distributions [19–22], have been used to grasp the various quantitative characteristics of natural language. Understanding the mechanisms behind such characteristics has the potential to improve the methods of natural language processing and generation. This is especially relevant today, given the heightened focus on large language models (LLMs) [23,24], incorporated in generative AI systems like OpenAI's ChatGPT, Microsoft's Bing Chat, and Google's Bard. One of the language properties recently investigated with statistical methods is the usage of punctuation in written language—it has been demonstrated that the distribution of word counts between consecutive punctuation marks in literary texts generally follows a discrete Weibull distribution [3,25,26]. What is interesting and significant, however, is the fact that for different languages the two parameters of this Weibull distribution are, to a large extent, selectively different and specific to a given language. Consistent with this fact, the punctuation distributions of texts after translation into another language are still governed by the Weibull distribution but with the parameters of the target language [3,25]. Interestingly, the patterns of sentence-ending punctuation marks, such as periods, exhibit much more flexibility and are less strictly bound by this distribution. These intervals, equivalent to sentence lengths, can therefore display a more diverse range of patterns.

Among the works considered important in the world literature, a book interesting from the aforementioned quantitative perspective is Hopscotch by Julio Cortázar. At its core,

![](_page_0_Picture_14.jpeg)

Check for updates

Citation: Dec, J.; Dolina, M.; Drożdż,
S.; Kwapień, J.; Stanisz, T. Multifractal
Hopscotch in Hopscotch by Julio
Cortázar. Entropy 2024, 1, 0.
https://doi.org/ https://doi.org/

Academic Editor: Ernestina Menasalvas

Received: 29 June 2024 Revised: 7 August 2024 Accepted: 20 August 2024 Published:

![](_page_0_Picture_18.jpeg)

Copyright: © 2024 by the authors Licensee MDPI, Basel, Switzerland This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https:// creativecommons.org/licenses/by/ 4.0/).

*Entropy* **2024**, *1*, 0 2 of 15

this novel challenges traditional narrative structures and invites readers to engage with the text in a non-linear manner. The novel presents multiple reading options: one can either follow the conventional order of chapters or choose to explore the narrative via a suggested "hopscotch" order, jumping between chapters in a non-sequential fashion [\[27,](#page-13-9)[28\]](#page-13-10). This experimental approach allows readers to experience the story in a unique, personalised way reflecting the author's desire to break away from the conventional storytelling. As a consequence of this free-form structure of the novel, the order of sentences and smaller textual constituents depends on a chosen sequence of chapters, which implies a strong impact on long-range correlations, both the linear and nonlinear ones. Since the novel comprises an eclectic mix of styles, including passages of stream-of-consciousness and experimental language play, the overall richness and depth of the narrative results in a convoluted, multilevel linguistic construct that, if transformed into numbers, is expected to reveal substantial complexity with self-similarity being one of its likely manifestations.

## **2. Materials and Methods**

In its original Spanish version [\[29\]](#page-13-11), *Hopscotch* consists of 155 chapters that can be read in the printed order, the "hopscotch" order recommended by the author, in which the number of the subsequent chapter is explicitly given at the end of the previous one, or in any other order formed by permutating the chapters that is chosen by a reader. Because of such alternatives, all foreign-language translations preserve the structure of the novel and the author recommendations. To illustrate this point, along with the Spanish text, there are two translations considered as well: the English one [\[30\]](#page-13-12) and the Polish one [\[31\]](#page-13-13). We transform the text in each language version into a sentence length variability (SLV) time series by counting words between each two consecutive sentence-ending punctuation marks (these can be periods, interrogation marks, exclamation marks, and other equivalent marks). The related statistical data are collected in Table [1.](#page-1-0) The SLV data reflect the evolution of the size of the main functional building blocks throughout the whole novel, which has been shown to be substantially informative [\[25](#page-13-7)[,32\]](#page-13-14).

<span id="page-1-0"></span>

| Table 1. Essential statistics on the SLV data considered in this study. |
|-------------------------------------------------------------------------|
|-------------------------------------------------------------------------|

|                                      | Spanish | English | Polish |
|--------------------------------------|---------|---------|--------|
| Minimum sentence length (words)      | 1       | 1       | 1      |
| Maximum sentence length (words)      | 850     | 860     | 681    |
| Average sentence length (words)      | 16.6    | 17.4    | 13.9   |
| Minimum sentence length (characters) | 1       | 1       | 1      |
| Maximum sentence length (characters) | 4037    | 4058    | 3730   |
| Average sentence length (characters) | 77.3    | 77.7    | 74.9   |
| Minimum chapter length (sentences)   | 4       | 3       | 3      |
| Maximum chapter length (sentences)   | 1710    | 1720    | 1873   |
| Average chapter length (sentences)   | 108.0   | 109.3   | 125.5  |

Punctuation may be viewed as a process of interrupting an otherwise ceaseless stream of words that improves understanding of the message and allows a reader to have necessary breaks. These functions make occurrences of the punctuation marks suitable for the survival analysis [\[33\]](#page-13-15). It has already been documented in the literature that the inter-mark distances develop distributions that can be modelled by the discrete Weibull distribution [\[3](#page-12-2)[,25\]](#page-13-7). This distribution is given by the following probability mass function [\[34\]](#page-13-16):

<span id="page-1-1"></span>
$$f(k) = (1-p)^{k\beta} - (1-p)^{(k+1)\beta}, \quad p \in (0,1), \quad \beta > 0$$
(1)

Entropy 2024, 1, 0 3 of 15

and the following cumulative distribution function:

$$\mathcal{F}(k) = 1 - (1 - p)^{k^{\beta}}. (2)$$

The latter describes the probability that the random variable takes on a value greater than k. The discrete Weibull distribution can be considered as a generalisation of the geometric distribution with probability p to which it conforms if  $\beta = 1$ , i.e., if the probability  $\mathcal{F}(k)$  is constant in time. If  $\beta > 1$ , the probability increases with time while the opposite is true for  $\beta < 1$ . The discrete Weibull distribution is used in various fields, including survival analysis, weather forecasting, and study of textual data [33,35,36]. In the case of punctuation, f(k) is the probability that a mark will occur exactly after k words.

Self-similarity or a lack of characteristics scale is among the most significant properties of natural complex systems. From an empirical perspective, this property can manifest itself in a non-trivial temporal organisation of measurement outcomes formed as a time series. In particular, complexity is often associated with a cascade-like hierarchy of data points that reveal multiscaling, which makes practical methods of identifying this sort of organisation a valuable tool in complex systems research [37]. Our experience so far allows us to consider the multifractal detrended fluctuation analysis (MFDFA) as the most reliable method in this respect [38,39]. This method constitutes a multiscale generalisation of an earlier, commonly used detrended fluctuation analysis (DFA) [40].

Here, the essential steps of the MFDFA algorithm are briefly sketched. Let  $U = \{u_i\}_{i=1}^T$  be a time series of T consecutive measurements of some observable u. We partition it into  $M_s$  non-overlapping windows of length s starting from both ends of U, which gives us  $2M_s$  such windows. In each window, we eliminate potential non-stationarity of the signal by applying a detrending procedure to an integrated signal (the so-called profile)  $X = \{x_i\}_{i=1}^s$  whose elements have the following form:

$$x_i = \sum_{i=1}^i u_j. (3)$$

The detrending is carried out with the help of a polynomial  $P^{(m)}$  of order m (we use m=2 throughout this study) that is best-fitted to X in each window  $v=0,\ldots,2M_s-1$  and the variance of the resulting detrended signal is then calculated:

$$f^{2}(\nu,s) = \frac{1}{s} \sum_{i=1}^{s} (x_{i} - P^{(m)}(i))^{2}.$$
 (4)

A family of fluctuation functions of order q is defined in the next step based on the average variance across all the windows:

$$F_q(s) = \left\{ \frac{1}{2M_s} \sum_{\nu=0}^{2M_s - 1} \left[ f^2(\nu, s) \right]^{q/2} \right\}^{1/q},\tag{5}$$

where q is a real number. The functions  $F_q(s)$  have to be calculated for a number of different values of scale s and index q. Typically, minimum s is chosen above the length of the longest sequence of constant values of U and maximum s is T/5. In contrast, there is no typical range of q. This index can be viewed as being related to the moments of the signal, so the extreme values cannot be chosen as too large for a time series with heavy tails.

If the fluctuation functions depend on *s* as power laws:

<span id="page-2-0"></span>
$$F_q(s) \sim s^{h(q)} \tag{6}$$

for a number of different choices of q, it indicates that the time series under study is either monofractal (when h(q) is constant in q) or multifractal otherwise. The function h(q) is called the generalised Hurst exponent, because for q = 2, h(q) = H, where H is the

*Entropy* **2024**, *1*, 0 4 of 15

standard Hurst exponent [\[41](#page-13-23)[,42\]](#page-13-24). In terms of visualisation, fractal *Fq*(*s*) form linear plots on double logarithmic plots. A convenient way of presenting the multifractal property of data is singularity spectrum *f*(*α*). It can be derived from *h*(*q*) by the following formulae:

<span id="page-3-0"></span>
$$\alpha = h(q) + qh'(q),$$
  

$$f(\alpha) = q[\alpha - h(q)] + 1,$$
(7)

where *α* is a measure of data-point singularity equivalent to the Hölder exponent and *f*(*α*) is the Legendre transform of *h*(*q*). The function *f*(*α*) can be interpreted geometrically as a fractal dimension of the subset of the whole data set with the Hölder exponent equal to *α* [\[43\]](#page-14-0). For a monofractal time series the pair (*α*, *f*(*α*)) is a single point, while for a multifractal one it is a parabola with shoulders pointing down. The usefulness of this representation comes from a fact that the broader the singularity spectrum is, the richer is the multifractality of the time series, which can be viewed as a measure of time series complexity. Sometimes the parabola of *f*(*α*) is distorted and asymmetric, which indicates that the data points of different amplitude have different scaling properties [\[44](#page-14-1)[–47\]](#page-14-2). Alternatively, the scaling type may be expressed in terms of the multifractal spectrum *τ*(*q*) defined by

$$\tau(q) = qh(q) - 1. \tag{8}$$

For monofractal time series, *τ*(*q*) depends linearly on *q* (because *h*(*q*) is constant then), while it is nonlinear for multifractal ones, which allows one for an easy detection of multiscaling.

## **3. Results and Discussion**

## *3.1. Linear Correlations*

It is instructive to look into data structure before any further step is made. In the left column of Figure [1,](#page-4-0) time series of SLV in three different language versions of the text are shown, each of them representing an unsigned process with a heavy tail. The SLV time series representing the text with two alternative chapter orders, the one recommended by the author and a completely random one, are shown in the right column (top and middle panels) of the same figure. In both cases, there is a clear data clustering observed (long sentences tend to group with the long ones, while small sentences tend to group with the small ones), the time series are characterised by memory. This by no means differs from other pieces of literature where temporal memory is naturally present. It stems from the fact that sentence lengths are often connected with writing style and certain features of narrative, which usually last for some paragraphs or pages (for instance, longer sentences are often used in descriptions and slow-paced parts of texts, while short sentences are more typical for fast-paced parts and dialogues). This property vanishes if the sentences are shuffled instead of the chapters.

Plots of the Pearson autocorrelation function (ACF) for the two authorial chapter orders are presented in Figure [2.](#page-4-1) ACF shows statistically meaningful values over a range of up to 200–400 consecutive sentences, after which it reaches noise level in both chapter orders. A trace of power-law decay of ACF can be noticed because of the double-log scale of the plots. Roughly the same picture is obtained if a random permutation of chapters is considered. This means that there is no difference between the proposed chapter orders and any other order that can be preferred by a reader (it must be noted, however, that it is impossible to consider all possible orderings as we deal with 155! ≈ 10<sup>273</sup> possible permutations here). As it might be expected, the sentence-level randomisation kills any genuine structure of SLV.

*Entropy* **2024**, *1*, 0 5 of 15

<span id="page-4-0"></span>![](_page_4_Figure_1.jpeg)

**Figure 1.** Time series of sentence length variability (SLV) measured in words for the original Spanish text of *Hopscotch* (**top**) and its translations into English (**middle**) and Polish (**bottom**). In order to ensure sufficient readability and preserve the vertical scale in all panels, the bars representing a few sentences with excessive length in each text have been rescaled by a factor of 1/3 (black arrows). Time series of SLV are presented in alternative orders of chapters: the printed order (**left**) and the order recommended by the author (**right**).

<span id="page-4-1"></span>![](_page_4_Figure_3.jpeg)

**Figure 2.** Autocorrelation function for SLV time series for two chapter orders: the printed order ("-p", **left**) and the recommended order ("-r", **right**), and for three languages: Spanish (ES, **top**), English (EN, **middle**), and Polish (PL, **bottom**). Noise level is indicated by a red dashed line in each panel. Note the double logarithmic scale of the plots.

### *3.2. The Weibull Analysis*

For all three language versions of *Hopscotch*, histograms for the respective SLV time series have been calculated; they are shown in Figure [3](#page-5-0) (dark colours) together with the best-fitted discrete Weibull distribution defined by Equation [\(1\)](#page-1-1). It is evident that there is no agreement between theory and the empirical distribution in each case—the result that matches results of similar analyses of different texts already reported in the literature [\[3](#page-12-2)[,25\]](#page-13-7). A much better agreement between the two can be seen for a different type of time series (punctuation mark distance variability, PMDV), in which distances between consecutive punctuation marks have been considered without restricting the analysis to sentence

*Entropy* **2024**, *1*, 0 6 of 15

endings. Thus, if also such marks as comma, colon, semicolon, dash, etc. are included in the study, the discrete Weibull distribution becomes a better model for the data (see light-colour histograms in Figure [3\)](#page-5-0). For all the language versions, the values of *β* for the PMDV time series exceed 1, which can be viewed as the normal case for written language, in which the probability of using a punctuation mark after a given number of words since the previous instance of writing a mark (the hazard function) increases with this number. It distinguishes *Hopscotch* from *Finnegans Wake* by James Joyce, where an abnormal value *β* < 1 has been found [\[48\]](#page-14-3). In contrast, for the SLV data, *β* ≈ 1 has been obtained for two out of three languages; it corresponds to the exponential distribution of such data. This is better seen if the plots are semi-logarithmic (see the insets in Figure [3\)](#page-5-0), where the exponential decay of the histogram tails and the corresponding fits are represented by straight lines.

<span id="page-5-0"></span>![](_page_5_Figure_2.jpeg)

**Figure 3.** Histograms of the SLV time series (dark colour) for three different language versions of *Hopscotch*: Spanish (**top left**), English (**top right**), and Polish (**bottom**) together with the histograms of the distances (in words) between any two consecutive punctuation marks (both the sentence-ending ones and the intra-sentence ones, light colour). Discrete Weibull distributions that have been leastsquare fitted to the histograms of both types are also shown in each panel (dashed and solid lines, respectively). In each case, values of the *p* and *β* parameters of the fits are explicitly given in legend boxes. (Insets) Histogram of the SLV time series with the fitted discrete Weibull distribution presented on the half-logarithmic scale.

### *3.3. Generalised Hurst Exponents*

The classic Hurst analysis of time series allows one to quantify linear autocorrelation, as it expresses how the observed value span depends on the length of observation [\[41\]](#page-13-23). In its generalised version *h*(*q*), it allows to detect differences in memory effects between fluctuations of different magnitudes [\[49\]](#page-14-4). It naturally enters the multiscale analysis through Equation [\(6\)](#page-2-0). *h*(*q*) is a non-increasing function of its argument with the special case being a constant function *h*(*q*) = *H* for all *q*s. In a practical situation, the range of considered values of *q* must be limited and dependent on the probability distribution function of the underlying stochastic process. Typically, the reference is that the *q*th moment of this distribution has to exist. In the present case, the related probability mass function is close to exponential, therefore no specific theoretical limit for *q* has to be applied. Because of this freedom, the parameter *q* has been limited to −7 ≤ *q* ≤ 7, which is a reasonable compromise between the range width, which should be as large as possible, and the available sample size. Figure [4](#page-6-0) shows the generalised Hurst exponents for the three languages and the two authorial chapter orders. In each case *h*(*q*) is a decreasing function which indicates that the time series are heterogeneous in their scaling behaviour for different *q*s. The larger the

*Entropy* **2024**, *1*, 0 7 of 15

variability of ∆*h* = *h*(*q*max) − *h*(*q*min) is, the more heterogeneous they are. However, as 0.37 ≤ ∆*h* ≤ 0.47 the difference between the cases is more quantitative than qualitative. It is not surprising, because, on the one hand, by changing the order of chapters, one effectively preserves the autocorrelation range up to the average number of sentences per chapter and, on the other hand, good translations into foreign languages are expected to preserve the structure of the original language version as closely as possible.

<span id="page-6-0"></span>![](_page_6_Figure_2.jpeg)

**Figure 4.** The generalised Hurst exponent *h*(*q*) for the SLV time series representing *Hopscotch* in different languages: Spanish (**top**), English (**middle**), and Polish (**bottom**). The printed order (**left**) and the recommended order (**right**) of chapters are shown separately. The difference between extreme values of *h*(*q*) for −7 ≤ *q* ≤ 7 is given by ∆*h* in each case.

## *3.4. Multifractal Analysis*

The family of the generalised Hurst exponents *h*(*q*) is closely related to the Hölder exponents *α* and the singularity spectrum *f*(*α*) via Equation [\(7\)](#page-3-0). From the perspective of the amount of information that one can extract from the data, the *f*(*α*) representation is more natural and convenient than *h*(*q*), especially if a fractal analysis is carried out. However, both *h*(*q*) and *f*(*α*) are of little use without inspecting of the fluctuation functions *Fq*(*s*) first. This is because they carry information about the possible existence of fractal scaling over a sufficient range of scales *s*, which is a crucial characteristic of the data. Therefore, Figures [5–](#page-7-0)[7](#page-9-0) show the family of *Fq*(*s*) calculated in the range −7 ≤ *q* ≤ 7 for different languages and different chapter orders.

*Entropy* **2024**, *1*, 0 8 of 15

<span id="page-7-0"></span>![](_page_7_Figure_1.jpeg)

**Figure 5.** (Main) *q*-dependent fluctuation functions *Fq*(*s*) calculated for time series of SLV in the Spanish original text of *Hopscotch* (**top**) and its two translations into English (**middle**) and Polish (**bottom**). The printed order of chapters is considered. The plots of *Fq*(*s*) for particular values of *q* are indicated by arrows. (Side) Singularity spectra *f*(*α*) associated with the exponents *h*(*q*) calculated from the scaling regions of the respective functions *Fq*(*s*) for three intervals: *q* ∈ [−2, 2] (**top right**), *q* ∈ [−4, 4] (**middle right**), and *q* ∈ [−7, 7] (**bottom right**). In each case the asymmetry coefficient *A<sup>α</sup>* and the singularity spectrum width ∆*α* are also given.

*Entropy* **2024**, *1*, 0 9 of 15

<span id="page-8-0"></span>![](_page_8_Figure_1.jpeg)

**Figure 6.** The same functions as in Figure [5](#page-7-0) for the recommended order of chapters.

*Entropy* **2024**, *1*, 0 10 of 15

<span id="page-9-0"></span>![](_page_9_Figure_1.jpeg)

**Figure 7.** The same functions as in Figure [5](#page-7-0) for the Spanish version of *Hopscotch* with two random permutations of chapters (**top** and **middle**) and the average taken over a set of 1000 sample permutations (**bottom**).

*Entropy* **2024**, *1*, 0 11 of 15

Let one start with the printed order of chapters; the corresponding fluctuation functions for different values of *q* are displayed in Figure [5](#page-7-0) (main panels) for the three languages considered in this work. All the functions show a power-law dependence (approximately straight lines on double logarithmic plots) over some range of scales, whose right limit reaches typically 300–400 consecutive sentences for both positive and negative *q*s. The singularity spectra derived from the scaling exponents *h*(*q*) for different intervals of *q* are shown in the side panels of each main panel of Figure [5.](#page-7-0) The spectra have their maximum at *α* ≈ 0.8, which points out to a strong persistence in SLV. By going through these side panels from top to bottom, the range of the values of *q* gradually extends from −2 ≤ *q* ≤ 2 to −7 ≤ *q* ≤ 7. The rationale behind considering different spans of *q* is that there is a certain degree of asymmetry in the density of the lines related to the functions *Fq*(*s*) between positive and negative *q*s in the main panels. Indeed, if one looks at the values of the asymmetry index *A<sup>α</sup>* for the *f*(*α*) spectra, it assumes a minimum value for the most narrow range of *q* and it increases with the increasing |*q*|. This observation is valid for all the three languages even though particular values of *A<sup>α</sup>* can differ from each other for the equivalent intervals of *q* in different languages. The asymmetry is left-sided, which means that the multiscaling comes predominantly from large fluctuations in SLV. This type of asymmetry is more often seen in empirical data than their opposite counterpart [\[46\]](#page-14-5). As regards the widths ∆*α* of the *f*(*α*) spectra, they increase with |*q*|, which is a normal behaviour in such a context, but their value indicates that the SLV time series under study show the multifractal scaling even for the most narrow range of *q*. This result has been expected, since one of our past studies focused on books with a stream-of-consciousness narrative [\[32\]](#page-13-14).

Now, the order of chapters can be altered to agree with the one recommended by Cortázar. This is his "hopscotch" order, which allows a reader for viewing the book's plot from a different perspective. The respective results in terms of *Fq*(*s*) and *f*(*α*) are documented in Figure [6,](#page-8-0) whose structure is the same as the structure of Figure [5.](#page-7-0) By altering the order, one destroys the temporal structure of the SLV time series for scales above the average length of a chapter expressed in the number of sentences, while the structure on shorter time scales remains largely unaltered. This leads to a visible significant distortion of the behaviour of *Fq*(*s*) for the scales *s* ≈ 10<sup>3</sup> with respect to the printed order of chapters, which tends to be inclining towards monofractality there (a narrow beam of almost parallel lines). In contrast, for the scales inside the chapters, the changes are less evident. By looking at the singularity spectra obtained for the recommended order, one observes a systematic increase in both the asymmetry *A<sup>α</sup>* and the width ∆*α* if compared to the results for the printed order. This effect suggests an existence of a richer variety of the singularity strengths expressed by the Hölder exponents *α* in the considered time series. The origin of this behaviour remains unclear at the present stage of research, however. Together with the increased left–right asymmetry of the spectra, a slight shift of the maximum of *f*(*α*) in the direction of larger values of *α* can be identified for the recommended order (*α* ≈ 0.85). This seems to be a systematic effect for the three languages. Finally, the change in *A<sup>α</sup>* is related to this shift, because together with the unchanged value of *α*min they cause the elongation of the left branch of *f*(*α*), while the length of the right branch remains roughly the same in both situations despite the fact that *α*max is larger for the recommended order than it is for the printed order.

It is interesting to investigate whether such effects can also be observed for any random permutation of chapters. Figure [7](#page-9-0) shows the results of the multifractal analysis of the SLV data corresponding to such permutations. The results for two individual permutations are shown there together with the average results for 1000 different random permutations. Only the results for the original Spanish version of the text are shown; the remaining two language versions are characterised by quantitatively similar results. Randomisation of the chapter order brings results that do not differ much from the results for the recommended order: for both individual permutations, the spectrum width ∆*α* is elevated with respect to its value for the printed order (0.65 and 0.70 vs. 0.56) but it is comparable to the value for

*Entropy* **2024**, *1*, 0 12 of 15

the recommended order (0.65 and 0.70 vs. 0.65). Regarding the asymmetry index *Aα*, the situation is not so evident as in the case of ∆*α*, because the results for one of the random permutations and for the printed order are close to each other (0.49 vs. 0.46), even though a larger discrepancy is also possible (0.61 vs. 0.46). These numbers refer to the maximum span of *q* (−7 ≤ *q* ≤ 7). It is also instructive to compare the results for individual chapter orders with the average over many random permutations (see Figure [7](#page-9-0) (bottom)).

The significance of the results reported above has also been tested against the null hypothesis of no correlation. This has been performed by a conventional surrogate testing [\[50\]](#page-14-6), in which the SLV time series are randomised at the individual sentence level, which destroys memory. Results show that in this case the singularity spectra are shifted to smaller values of *α* and the maximum of *f*(*α*) is located near *α* = 0.5. Even though ∆*α* for such surrogate data remains as high as 0.2, the inherent properties of the MFDFA procedure suggest that *f*(*α*) has been broadened spuriously by the finite-size effects related to the heavy-tailed probability distribution functions of the SLV data [\[51,](#page-14-7)[52\]](#page-14-8). Another surrogate testing based on the Fourier-phase randomisation of time series, which destroys all nonlinear correlations [\[53\]](#page-14-9), brings the expected results, i.e., the singularity spectra become point-like and located exactly at *α* ≈ 0.5. Both types of surrogate tests confirm the statistical validity of the presented outcomes.

## **4. Summary**

The time series of SLV representing Julio Cortázar's novel *Hopscotch* in its original Spanish version and in two foreign-language translations were analysed by means of the autocorrelation function, the Weibull analysis, and the MFDFA. Long-range memory effects were observed in terms of a power-law decay of ACF that extended beyond the scales defined by the average chapter length for the printed order of chapters and for other possible chapter orders, including the one recommended by the author. The fluctuations of the SLV time series were distributed in agreement with an exponential distribution, at least to a certain extent (small fluctuations somehow deviated from this pattern). For a comparison, the time series of PMDV, where all punctuation marks were considered, were modelled by the discrete Weibull distribution with *β* > 1—the value that did not differ from its standard values for written texts. Finally, by using the MFDFA formalism, the fractal properties of the SLV time series were studied. They happened to be multifractal for both the printed and recommended orders, as well as for all the considered random orders. The main difference between the results obtained for different chapter orderings was the observation that all the conceptual orders (i.e., the non-printed ones) showed an enhanced variety of singularities (i.e., broader singularity spectra) present in the time series and expressed by the Hölder exponents. They also developed stronger left-sided asymmetry as compared with their counterparts for the printed order of chapters, the effect produced by a subtle but noticeable shift of the maxima of the spectra towards larger values of the Hölder exponent. It has to be stressed that multifractal structures in literary works are a rare property that have been identified only in a small fraction of texts [\[3](#page-12-2)[,32\]](#page-13-14). Interestingly, this and the other considered properties seem to be invariant under translation into foreign languages if a translator pays sufficient attention to the structure of the original (see also [\[21](#page-13-25)[,25,](#page-13-7)[26\]](#page-13-8)).

The results obtained in this analysis indicate that the printed order of chapters in *Hopscotch* cannot be distinguished statistically if compared to either the recommended order or a generic order obtained via a random permutation of chapters. Also, we do not observe any qualitative difference between the recommended order and generic orders, which leads us to a conclusion that neither the printed order nor the recommended order introduce significant temporal correlations on scales above the average number of sentences in a chapter, at least such correlations that could be identified with the methodology applied here. From this perspective, each chapter constitutes a largely independent block whose position in the narrative can be arbitrarily changed without changing the statistical properties of SLV.

*Entropy* **2024**, *1*, 0 13 of 15

If the results of this study are compared with the earlier results for *Finnegans Wake* by J. Joyce, one observes that *Hopscotch* is more conventional not only in terms of literary style but also in terms of the statistical properties [\[3](#page-12-2)[,32](#page-13-14)[,48\]](#page-14-3). Its role in the world's literature stems from its innovative construction including the nonlinear and reader-engaging narrative rather than the structural and lingual complexity that is so striking in *Finnegans Wake* or *Ulysses*. Nevertheless, the results of this work provide an inspiration for more systematic research of the most prominent and unique literary works, as these are the ones that are potent to catalyze opening new perspectives in linguistics, including those in the field of large language models. In the latter context, it is important that the methodology presented here allows for the identification and quantification of various types of correlations in written texts, including long-range ones. In the terminology of nonlinear dynamics this means a reduction in the effective dimensionality of the corresponding 'phase space' and therefore a reduction in the actual number of parameters involved. In LLMs, nowadays commonly based on neural networks, such facts can be exploited to significantly, and perhaps even crucially, reduce the number of applied parameters and thus increase their efficiency in terms of time and energy consumption.

A related prospective direction of future research, somehow parallel yet substantially distinct from the multifractal approach discussed here, is a dynamically oriented analysis of SLV, in which one looks for low-dimensional attractors in a reconstructed phase-space of "text-writing dynamics". Apart from some early attempts [\[11](#page-13-0)[,54\]](#page-14-10), this direction still remains largely unexplored.

**Author Contributions:** Conceptualization, J.D., M.D., S.D. and T.S.; Methodology, S.D. and J.K.; Software, J.D., M.D., J.K. and T.S.; Validation, J.D., M.D., S.D., J.K. and T.S.; Formal analysis, J.D., M.D., S.D. and J.K.; Investigation, J.D., M.D., S.D., J.K. and T.S.; Resources, J.D., M.D. and T.S.; Data curation, J.D., M.D. and T.S.; Writing—original draft, J.K.; Writing—review & editing, S.D., J.K. and T.S.; Visualization, J.D. and M.D.; Supervision, S.D.

**Funding:** This research received no external funding.

**Institutional Review Board Statement:** Not applicable.

**Data Availability Statement:** The data presented in this study are available on request from the corresponding author. The data are not publicly available due to copyright.

**Conflicts of Interest:** The authors declare no conflicts of interest.

## **References**

- <span id="page-12-0"></span>1. Hébert-Dufresne, L.; Allard, A.; Garland, J.; Hobson, E.A.; Zaman, L. The path of complexity. *NPJ Complex.* **2024**, *1*, 4. [https://doi.org/10.1038/s44260-024-00004-0.](https://doi.org/10.1038/s44260-024-00004-0)
- <span id="page-12-1"></span>2. Kwapie ´n, J.; Drozd˙ z, S. Physical approach to complex systems. ˙ *Phys. Rep.* **2012**, *515*, 115–226. [https://doi.org/10.1016/j.physrep.](https://doi.org/10.1016/j.physrep.2012.01.007) [2012.01.007.](https://doi.org/10.1016/j.physrep.2012.01.007)
- <span id="page-12-2"></span>3. Stanisz, T.; Drozd˙ z, S.; Kwapie´n, J. Complex systems approach to natural language. ˙ *Phys. Rep.* **2024**, *1053*, 1–84. [https:](https://doi.org/10.1016/j.physrep.2023.12.002) [//doi.org/10.1016/j.physrep.2023.12.002.](https://doi.org/10.1016/j.physrep.2023.12.002)
- <span id="page-12-3"></span>4. D˛ebowski, L. *Information Theory Meets Power Laws: Stochastic Processes and Language Models*; Wiley: Hoboken, NJ, USA, 2020. [https://doi.org/10.1002/9781119625384.](https://doi.org/10.1002/9781119625384)
- 5. Takahira, R.; Tanaka-Ishii, K.; D˛ebowski, L. Entropy Rate Estimates for Natural Language—A New Extrapolation of Compressed Large-Scale Corpora. *Entropy* **2016**, *18*, 364. [https://doi.org/10.3390/e18100364.](https://doi.org/10.3390/e18100364)
- <span id="page-12-4"></span>6. Montemurro, M.A.; Zanette, D.H. Universal Entropy of Word Ordering Across Linguistic Families. *PLoS ONE* **2011**, *6*, e19875. [https://doi.org/10.1371/journal.pone.0019875.](https://doi.org/10.1371/journal.pone.0019875)
- <span id="page-12-5"></span>7. Alvarez-Lacalle, E.; Dorow, B.; Eckmann, J.P.; Moses, E. Hierarchical structures induce long-range dynamical correlations in written texts. *Proc. Natl. Acad. Sci. USA* **2006**, *103*, 7956–7961. [https://doi.org/10.1073/pnas.0510673103.](https://doi.org/10.1073/pnas.0510673103)
- 8. Liu, J.; Gunn, E.; Youssef, F.; Tharayil, J.; Lansford, W.; Zeng, Y. Fractality in Chinese prose. *Digit. Scholarsh. Humanit.* **2023**, *38*, 604–620. [https://doi.org/10.1093/llc/fqac062.](https://doi.org/10.1093/llc/fqac062)
- 9. Sánchez, D.; Zunino, L.; Gregorio, J.D.; Toral, R.; Mirasso, C. Ordinal analysis of lexical patterns. *Chaos* **2023**, *33*, 033121. [https://doi.org/10.1063/5.0139852.](https://doi.org/10.1063/5.0139852)
- 10. Pawłowski, A. Time-Series analysis in linguistics: Application of the ARIMA method to cases of spoken Polish. *J. Quant. Linguist.* **1997**, *4*, 203–221. [https://doi.org/10.1080/09296179708590097.](https://doi.org/10.1080/09296179708590097)

*Entropy* **2024**, *1*, 0 14 of 15

<span id="page-13-0"></span>11. Kosmidis, K.; Kalampokis, A.; Argyrakis, P. Language time series analysis. *Physica A* **2006**, *370*, 808–816. [https://doi.org/10.101](https://doi.org/10.1016/j.physa.2006.02.042) [6/j.physa.2006.02.042.](https://doi.org/10.1016/j.physa.2006.02.042)

- <span id="page-13-1"></span>12. Cancho, R.F.I.; Solé, R.V. The small world of human language. *Proc. R. Soc. Lond. Ser. B Biol. Sci.* **2001**, *268*, 2261–2265. [https://doi.org/10.1098/rspb.2001.1800.](https://doi.org/10.1098/rspb.2001.1800)
- 13. Liu, H.; Xu, C. Can syntactic networks indicate morphological complexity of a language? *Europhys. Lett.* **2011**, *93*, 28005. [https://doi.org/10.1209/0295-5075/93/28005.](https://doi.org/10.1209/0295-5075/93/28005)
- 14. Cong, J.; Liu, H. Approaching human language with complex networks. *Phys. Life Rev.* **2014**, *11*, 598–618. [https://doi.org/10.101](https://doi.org/10.1016/j.plrev.2014.04.004) [6/j.plrev.2014.04.004.](https://doi.org/10.1016/j.plrev.2014.04.004)
- 15. Wachs-Lopes, G.A.; Rodrigues, P.S. Analyzing natural human language from the point of view of dynamic of a complex network. *Expert Syst. Appl.* **2016**, *45*, 8–22. [https://doi.org/10.1016/j.eswa.2015.09.020.](https://doi.org/10.1016/j.eswa.2015.09.020)
- 16. Kulig, A.; Kwapie´n, J.; Stanisz, T.; Drozd˙ z, S. In narrative texts punctuation marks obey the same statistics as words. ˙ *Inf. Sci.* **2017**, *375*, 98–113. [https://doi.org/10.1016/j.ins.2016.09.051.](https://doi.org/10.1016/j.ins.2016.09.051)
- 17. Stanisz, T.; Kwapie´n, J.; Drozd˙ z, S. Linguistic data mining with complex networks: A stylometric-oriented approach. ˙ *Inf. Sci.* **2019**, *482*, 301–320. [https://doi.org/10.1016/j.ins.2019.01.040.](https://doi.org/10.1016/j.ins.2019.01.040)
- <span id="page-13-2"></span>18. Raducha, T.; Gubiec, T. Predicting language diversity with complex networks. *PLoS ONE* **2018**, *13*, e0196593. [https://doi.org/10](https://doi.org/10.1371/journal.pone.0196593) [.1371/journal.pone.0196593.](https://doi.org/10.1371/journal.pone.0196593)
- <span id="page-13-3"></span>19. Naranan, S.; Balasubrahmanyan, V. Models for power law relations in linguistics and information science. *J. Quant. Linguist.* **1998**, *5*, 35–61. [https://doi.org/10.1080/09296179808590110.](https://doi.org/10.1080/09296179808590110)
- 20. Newman, M. Power laws, Pareto distributions and Zipf's law. *Contemp. Phys.* **2005**, *46*, 323–351. [https://doi.org/10.1080/001075](https://doi.org/10.1080/00107510500052444) [10500052444.](https://doi.org/10.1080/00107510500052444)
- <span id="page-13-25"></span>21. Ausloos, M. Punctuation effects in english and esperanto texts. *Physica A* **2010**, *389*, 2835–2840. [https://doi.org/10.1016/j.physa.](https://doi.org/10.1016/j.physa.2010.02.038) [2010.02.038.](https://doi.org/10.1016/j.physa.2010.02.038)
- <span id="page-13-4"></span>22. Piantadosi, S.T. Zipf's word frequency law in natural language: A critical review and future directions. *Psychon. Bull. Rev.* **2014**, *21*, 1112–1130. [https://doi.org/10.3758/s13423-014-0585-6.](https://doi.org/10.3758/s13423-014-0585-6)
- <span id="page-13-5"></span>23. Shanahan, M.; McDonell, K.; Reynolds, L. Role play with large language models. *Nature* **2023**, *623*, 493–498. [https://doi.org/10.1](https://doi.org/10.1038/s41586-023-06647-8) [038/s41586-023-06647-8.](https://doi.org/10.1038/s41586-023-06647-8)
- <span id="page-13-6"></span>24. Zhao, W.X.; Zhou, K.; Li, J.; Tang, T.; Wang, X.; Hou, Y.; Min, Y.; Zhang, B.; Zhang, J.; Dong, Z.; et al. A Survey of Large Language Models. *arXiv* **2023**, arXiv:2303.18223v13.
- <span id="page-13-7"></span>25. Stanisz, T.; Drozd˙ z, S.; Kwapie´n, J. Universal versus system-specific features of punctuation usage patterns in major Western ˙ languages. *Chaos, Solitons Fractals* **2023**, *168*, 113183. [https://doi.org/10.1016/j.chaos.2023.113183.](https://doi.org/10.1016/j.chaos.2023.113183)
- <span id="page-13-8"></span>26. Dec, J.; Dolina, M.; Drozd˙ z, S.; Kwapie ´n, J.; Liu, J.; Stanisz, T. Quantifying patterns of punctuation in modern Chinese prose. 2024, ˙ *submitted*.
- <span id="page-13-9"></span>27. Bernstein, J. Rayuela, Chapter 34: A structural reading. *Hispanófila* **1974**, *52*, 61–70. [https://doi.org/https://www.jstor.org/](https://doi.org/https://www.jstor.org/stable/43807575) [stable/43807575.](https://doi.org/https://www.jstor.org/stable/43807575)
- <span id="page-13-10"></span>28. Simpkins, S. "The Infinite Game": Cortázar's "Hopscotch". *J. Midwest Mod. Lang. Assoc.* **1990**, *23*, 61–74. [https://doi.org/http:](https://doi.org/http://www.jstor.org/stable/1315037) [//www.jstor.org/stable/1315037.](https://doi.org/http://www.jstor.org/stable/1315037)
- <span id="page-13-11"></span>29. Cortázar, J. *Rayuela*; Sudamericana: Buenos Aires, Argentina, 1963.
- <span id="page-13-12"></span>30. Cortázar, J. *Hopscotch*; Rabassa, G., Trans.; Pantheon Books: New York, NY, USA, 1966.
- <span id="page-13-13"></span>31. Cortázar, J. *Gra w klasy*; Ch ˛adzy ´nska, Z., Trans.; Wydawnictwo Literackie: Kraków. Poland, 1985.
- <span id="page-13-14"></span>32. Drozd˙ z, S.; O´swi˛ecimka, P.; Kulig, A.; Kwapie´n, J.; Bazarnik, K.; Grabska-Gradzi ´nska, I.; Rybicki, J.; Stanuszek, M. Quantifying ˙ origin and character of long-range correlations in narrative texts. *Inf. Sci.* **2016**, *331*, 32–44. [https://doi.org/10.1016/j.ins.2015.10.](https://doi.org/10.1016/j.ins.2015.10.023) [023.](https://doi.org/10.1016/j.ins.2015.10.023)
- <span id="page-13-15"></span>33. Miller, R. *Survival Analysis*; John Wiley & Sons: Hoboken, NJ, USA, 1997.
- <span id="page-13-16"></span>34. Nakagawa, T.; Osaki, S. The discrete Weibull distribution. *IEEE Trans. Reliab.* **1975**, *R-24*, 300–301. [https://doi.org/10.1109/tr.19](https://doi.org/10.1109/tr.1975.5214915) [75.5214915.](https://doi.org/10.1109/tr.1975.5214915)
- <span id="page-13-17"></span>35. Johnson, N.L.; Kotz, S.; Balakrishnan, N. *Continuous Univariate Distributions*; Wiley-Interscience: Hoboken, NJ, USA, 1994.
- <span id="page-13-18"></span>36. Altmann, E.G.; Pierrehumbert, J.B.; Motter, A.E. Beyond Word Frequency: Bursts, Lulls, and Scaling in the Temporal Distributions of Words. *PLoS ONE* **2009**, *4*, e7678. [https://doi.org/10.1371/journal.pone.0007678.](https://doi.org/10.1371/journal.pone.0007678)
- <span id="page-13-19"></span>37. Jimenez, J. Intermittency and cascades. *J. Fluid Mech.* **2000**, *409*, 99–120.
- <span id="page-13-20"></span>38. Kantelhardt, J.W.; Zschiegner, S.A.; Koscielny-Bunde, E.; Havlin, S.; Bunde, A.; Stanley, H. Multifractal detrended fluctuation analysis of nonstationary time series. *Physica A* **2002**, *316*, 87–114. [https://doi.org/10.1016/s0378-4371\(02\)01383-3.](https://doi.org/10.1016/s0378-4371(02)01383-3)
- <span id="page-13-21"></span>39. O´swi˛ecimka, P.; Kwapie´n, J.; Drozd˙ z, S. Wavelet versus detrended fluctuation analysis of multifractal structures. ˙ *Phys. Rev. E* **2006**, *74*, 016103. [https://doi.org/10.1103/PhysRevE.74.016103.](https://doi.org/10.1103/PhysRevE.74.016103)
- <span id="page-13-22"></span>40. Peng, C.K.; Buldyrev, S.V.; Havlin, S.; Simons, M.; Stanley, H.E.; Goldberger, A.L. Mosaic organization of DNA nucleotides. *Phys. Rev. E* **1994**, *49*, 1685. [https://doi.org/10.1103/physreve.49.1685.](https://doi.org/10.1103/physreve.49.1685)
- <span id="page-13-23"></span>41. Hurst, H.E. The long-term storage capacity of reservoir. *Trans. Am. Soc. Civ. Eng.* **1951**, *116*, 2447. [https://doi.org/10.1061/](https://doi.org/10.1061/TACEAT.000651) [TACEAT.000651.](https://doi.org/10.1061/TACEAT.000651)
- <span id="page-13-24"></span>42. Heneghan, C.; McDarby, G. Establishing the relation between detrended fluctuation analysis and power spectral density analysis for stochastic processes. *Phys. Rev. E* **2000**, *62*, 6103–6110.

*Entropy* **2024**, *1*, 0 15 of 15

<span id="page-14-0"></span>43. Halsey, T.C.; Jensen, M.H.; Kadanoff, L.P.; Procaccia, I.; Shraimant, B.I. Fractal measures and their singularities: The characterization of strange sets. *Phys. Rev. A* **1986**, *33*, 1141–1151.

- <span id="page-14-1"></span>44. Ohashi, K.; Amaral, L.A.; Natelson, B.H.; Yamamoto, Y. Asymmetrical singularities in real-world signals. *Phys. Rev. E* **2003**, *68*, 065204. [https://doi.org/10.1103/PhysRevE.68.065204.](https://doi.org/10.1103/PhysRevE.68.065204)
- 45. Cao, G.; Cao, J.; Xu, L. Asymmetric multifractal scaling behavior in the Chinese stock market: Based on asymmetric MF-DFA. *Physica A* **2013**, *392*, 797–807. [https://doi.org/https://doi.org/10.1016/j.physa.2012.10.042.](https://doi.org/https://doi.org/10.1016/j.physa.2012.10.042)
- <span id="page-14-5"></span>46. Drozd˙ z, S.; O´swi˛ecimka, P. Detecting and interpreting distortions in hierarchical organization of complex time series. ˙ *Phys. Rev. E* **2015**, *91*, 030902. [https://doi.org/10.1103/PhysRevE.91.030902.](https://doi.org/10.1103/PhysRevE.91.030902)
- <span id="page-14-2"></span>47. Gómez-Gómez, J.; Carmona-Cabezas, R.; Ariza-Villaverde, A.B.; Gutiérrez de Ravé, E.; Jiménez-Hornero, F.J. Multifractal detrended fluctuation analysis of temperature in Spain (1960–2019). *Physica A* **2021**, *578*, 126118. [https://doi.org/https:](https://doi.org/https://doi.org/10.1016/j.physa.2021.126118) [//doi.org/10.1016/j.physa.2021.126118.](https://doi.org/https://doi.org/10.1016/j.physa.2021.126118)
- <span id="page-14-3"></span>48. Stanisz, T.; Drozd˙ z, S.; Kwapie ´n, J. Statistics of punctuation in experimental literature—The remarkable case of ˙ *Finnegans Wake* by James Joyce. *Chaos* **2024**, 34, 083124. [https://doi.org/10.1063/5.0203530.](https://doi.org/10.1063/5.0203530)
- <span id="page-14-4"></span>49. Monjo, R.; Meseguer-Ruiz, O. Review: Fractal Geometry in Precipitation. *Atmosphere* **2024**, *15*, 135. [https://doi.org/10.3390/](https://doi.org/10.3390/atmos15010135) [atmos15010135.](https://doi.org/10.3390/atmos15010135)
- <span id="page-14-6"></span>50. Theiler, J.; Prichard, D. Constrained-realization Monte-Carlo method for hypothesis testing. *Physica D* **1996**, *94*, 221–235.
- <span id="page-14-7"></span>51. Drozd˙ z, S.; Kwapie´n, J.; O´swi˛ecimka, P.; Rak, R. Quantitative features of multifractal subtleties in time series. ˙ *Europhys. Lett.* **2009**, *88*, 60003. [https://doi.org/10.1209/0295-5075/88/60003.](https://doi.org/10.1209/0295-5075/88/60003)
- <span id="page-14-8"></span>52. Kwapie´n, J.; Blasiak, P.; Drozd˙ z, S.; O´swi˛ecimka, P. Genuine multifractality in time series is due to temporal correlations. ˙ *Phys. Rev. E* **2023**, *107*, 034139. [https://doi.org/10.1103/PhysRevE.107.034139.](https://doi.org/10.1103/PhysRevE.107.034139)
- <span id="page-14-9"></span>53. Schreiber, T.; Schmitz, A. Improved Surrogate Data for Nonlinearity Tests. *Phys. Rev. Lett.* **1996**, *77*, 635–638.
- <span id="page-14-10"></span>54. Ausloos, M. Measuring complexity with multifractals in texts. Translation effects. *Chaos Solitons Fractals* **2012**, *45*, 1349–1357. [https://doi.org/10.1016/j.chaos.2012.06.016.](https://doi.org/10.1016/j.chaos.2012.06.016)

**Disclaimer/Publisher's Note:** The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.