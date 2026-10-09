## Universal versus system-specific features of punctuation usage patterns in major Western languages

Tomasz Stanisz<sup>1</sup> , Stanisław Drożdż<sup>1</sup>*,*<sup>2</sup> , Jarosław Kwapień<sup>1</sup>

#### **Abstract**

The celebrated proverb that "speech is silver, silence is golden" has a long multinational history and multiple specific meanings. In written texts punctuation can in fact be considered one of its manifestations. Indeed, the virtue of effectively speaking and writing involves - often decisively - the capacity to apply the properly placed breaks. In the present study, based on a large corpus of world-famous and representative literary texts in seven major Western languages, it is shown that the distribution of intervals between consecutive punctuation marks in almost all texts can universally be characterised by only two parameters of the discrete Weibull distribution which can be given an intuitive interpretation in terms of the so-called hazard function. The values of these two parameters tend to be language-specific, however, and even appear to navigate translations. The properties of the computed hazard functions indicate that among the studied languages, English turns out to be the least constrained by the necessity to place a consecutive punctuation mark to partition a sequence of words. This may suggest that when compared to other studied languages, English is more flexible, in the sense of allowing longer uninterrupted sequences of words. Spanish reveals similar tendency to only a bit lesser extent.

*Keywords:* Natural language, Punctuation, Survival analysis, Complexity, Quantitative linguistics

## **1. Introduction**

The faculty of language [\[1\]](#page-10-0) establishes the organization of societies [\[2,](#page-10-1) [3,](#page-10-2) [4,](#page-10-3) [5\]](#page-10-4) and is commonly considered the principal trait of humanity [\[6,](#page-10-5) [7,](#page-10-6) [8\]](#page-10-7). Yet its evolutionary emergence [\[9,](#page-10-8) [10\]](#page-10-9), involving highly convoluted cognition and computation related processes [\[11,](#page-10-10) [12,](#page-10-11) [13,](#page-10-12) [14\]](#page-10-13) in the brain, still remains a subject of controversies [\[1,](#page-10-0) [15,](#page-10-14) [16,](#page-10-15) [17\]](#page-10-16). The externalization of these processes in terms of speech [\[18\]](#page-11-0), consecutively mapped by humans into writing [\[19\]](#page-11-1) - where punctuation plays a pivotal role - provides the most straightforward and quantifiable clue to the design principles of natural language, involving both neuronal and anatomical processes. This especially applies to its efficiency and expressiveness in communication. As one related element, the arrangement of full stops in a written text determines the resulting sentence length distribution while the arrangement of all the punctuation reveals characteristics of the basic constituents in the syntactic organization of a sentence [\[20\]](#page-11-2).

Even though the usage of punctuation is crucial for a faithful mapping of the spoken language into writing [\[21,](#page-11-3) [22,](#page-11-4) [23\]](#page-11-5), the history of its development is relatively young and recent [\[24,](#page-11-6) [25,](#page-11-7) [26\]](#page-11-8) as compared to the time horizons involved in the development of modern languages [\[27\]](#page-11-9). In its developed, contemporary Western form, by partitioning texts through several punctuation marks, it serves clarifying meaning, expressing the emotional content, facilitating perception, memorization and the cognitive processing, as dictated by perceptuo-motor factors, cognitive limitations, and pragmatics, both of a writer and of a reader. Interestingly, punctuation marks, accompanying words as the "building blocks" of written texts, share some specific quantitative characteristics with words, despite being clearly different in their nature and role in language. Recent statistical analysis shows [\[28\]](#page-11-10) that punctuation marks obey the same Zipf's law [\[29\]](#page-11-11) as words. Even more, their inclusion in word frequency analysis acts towards restoring the Zipf's power law from the more flat Zipf–Mandelbrot [\[30\]](#page-11-12) behaviour in the initial region of the most frequent items and thus improves an overall quality of scaling. A related practical result is that treating punctuation marks on the same terms as words appears to have a significant impact on the accuracy of stylometric analyses [\[31\]](#page-11-13).

<sup>1</sup>*Complex Systems Theory Department, Institute of Nuclear Physics, Polish Academy of Sciences, ul. Radzikowskiego 152, 31-342 Kraków, Poland*

<sup>2</sup>*Faculty of Computer Science and Telecommunications, Cracow University of Technology, ul. Warszawska 24, Kraków 31-155, Poland*

#### **2. Datasets and Methods**

### *2.1. Literary corpora studied*

The main set of studied texts consists of 240 literary works written in prose in 7 languages: English (denoted by EN in figures), German (DE), French (FR), Italian (IT), Spanish (ES), Polish (PL) and Russian (RU). In each language there are more than 30 texts, summing up to corpora of at least 3 million words in length. Each book contains no fewer than 1500 word sequences separated by punctuation marks. In terms of sentences, the lengths of the books are also typically on the order of thousands; there are only 8 texts shorter than 1000 sentences, with the shortest one having above 350 sentences. An additional book set consists of translated texts. This set is constructed as follows. In each of the studied languages, 2 books from the main set are selected. Then their translations into all the remaining languages are added into the set. One thus gets a collection of 14 books, each in 7 language versions. Two translations are missing in the set (due to unavailability), and thus 96 texts are obtained in total. Full list of all the books analysed is given in [Appendix C.](#page-14-0) The main criteria for the choice of texts are availability (the majority are in the public domain) and popularity - many of them are famous pieces of world literature having a significant impact on culture. The literature in each of the 7 languages included was awarded no fewer than 5 Nobel Prizes and each of them is spoken by more than 40 million people worldwide.

The texts are subjected to preprocessing, which includes removing foreword, annotations, additional information from the publisher, and punctuation marks that are not related to the structure of a sentence, for example hyphens, full stops used after abbreviations, dashes placed at the beginning of quotations in some languages, and inverted interrogation and exclamation marks in Spanish. Each text is transformed into a series *k<sup>i</sup>* representing the lengths of intervals *i* between consecutive punctuation marks, measured by the number of words (disregarding *k<sup>i</sup>* = 0, that is the cases where two punctuation marks are placed next to each other). Three variants of what is taken as punctuation are quantitatively considered: (i) punctuation marks indicating the ends of sentences, (ii) sentence-ending punctuation marks together with all the commas and (iii) all punctuation marks (after preprocessing these belong to the following list: full stop, question mark, exclamation mark, ellipsis, comma, dash, colon, semicolon, left and right bracket).

## *2.2. Discrete Weibull distribution*

Since the usage of punctuation is inherently related to the life processes, and thus also to their limitations and even exhaustion, some of their exposure characteristics are expected to reflect this fact and thus to be suitable to the survival analysis [\[32\]](#page-11-14). Indeed, the distribution of punctuation recurrence patterns can be considered the main factor reflecting the 'lifetime' of an uninterrupted sequence of words. A candidate functional form to describe the distribution of inter-punctuation distances *k* within a written text is a Weibull-like distribution [\[33,](#page-11-15) [34\]](#page-11-16) as it often appears to properly model the processes related to survival.

To understand the motivation behind introducing discrete Weibull distribution as a model of the distribution of distances between consecutive punctuation marks, one can consider the following line of reasoning.

Suppose that putting punctuation marks into the text is governed by a random process: after each word written, the writer places a punctuation mark with probability *p*, and puts no mark with probability 1 − *p*. Here no distinction between different types of punctuation marks is made; this is motivated by the fact that many punctuation marks, despite being clearly different, can be considered as serving roughly the same purpose - to break text into parts, in the way imposed by grammatical and logical constraints. Each decision whether to put a punctuation mark or not is a Bernoulli trial with *p* being the probability of success. The length of the interval between successive punctuation marks (the number of words between them) is the number *k* of trials required to obtain the first success, after the last one observed (*k* = 1*,* 2*,* 3*, ...*). The number of trials until the first success in Bernoulli process follows the geometric distribution.

This distribution, just as any other, can be fully characterised by its cumulative distribution function *F*(*k*), or equivalently, by giving the complementary cumulative distribution function 1 − *F*(*k*), also called the *survival function*, which describes the probability that the random variable takes on a value greater than *k*. The survival function of geometric distribution is:

$$1 - F(k) = (1 - p)^k. (1)$$

However, it is reasonable to anticipate that the probability of the punctuation mark occurrence after a word is not constant over the text, and therefore a distribution more general than the geometric distribution is required. One way of generalising the geometric distribution is introducing an exponent, *β >* 0, into its survival function:

<span id="page-1-0"></span>
$$1 - F(k) = (1 - p)^{k^{\beta}}. (2)$$

A distribution with survival function of the form given by Eq. [2](#page-1-0) is called the discrete Weibull distribution [\[35\]](#page-11-17). Its parameter *β* determines the deviation from the geometric distribution, which is recovered for *β* = 1. It describes how the probability of obtaining a success depends on how many trials have been performed since the last success observed. This dependence can be characterized by the so-called *hazard function h*(*k*). It can be defined as the conditional probability that a success occurs on the *k*-th trial, given that it has not occurred in the preceding *k*−1 trials. With *P*(*k*) denoting the probability mass function, the hazard function of the discrete Weibull distribution is given by:

<span id="page-2-0"></span>
$$h(k) = \frac{P(k)}{1 - F(k - 1)} = 1 - (1 - p)^{k^{\beta} - (k - 1)^{\beta}}.$$
 (3)

For *β <* 1, the hazard function is a decreasing function - the probability of observing an event of interest becomes smaller as the waiting time gets longer. For *β >* 1, it is increasing with time. For *β* = 1, the hazard function is a constant as for the geometric, *memoryless* distribution. The parameter *p* thus reflects the probability of observing an event occurrence already in the first trial. Exemplary plots of the discrete Weibull distribution and the corresponding hazard rates are shown in Fig. [1\(](#page-3-0)d).

## *2.3. Detrended Fluctuation Analysis (DFA)*

The above-presented mechanism of inserting punctuation into a text attempts to grasp the properties related solely to the probability distribution describing the distances between consecutive punctuation marks. It does not specify whether the processes generating word sequences between consecutive punctuation marks in different places in a text are mutually dependent or not. To investigate the possible presence of such dependencies in a text, one can study the correlations in a time series constructed from the lengths of word sequences between consecutive punctuation marks. In this work, such correlations are characterized with the use of the Hurst exponent [\[36\]](#page-11-18) - a tool commonly utilized in the description of long-range correlations in time series analysis. The value of the Hurst exponent *H* provides information about the strength and the character of the correlations in a time series, by measuring how fluctuations of the series behave in various time scales. For *H* = 1*/*2 the time series is uncorrelated. For *H <* 1*/*2 the series is *antipersistent*, that is, its values in consecutive time steps are negatively correlated; for *H >* 1*/*2 it is *persistent*, which means that its consecutive values are correlated positively; in this case, the series is said to have long-range correlations. At present, the detrended fluctuation analysis (DFA) [\[37\]](#page-11-19) is considered the most numerically stable method of computing the Hurst exponent from a real-valued time series; the details of the method are given in [Appendix B.](#page-13-0)

#### **3. Results**

## *3.1. Two books*

An explicit demonstration of how effectively the Weibull functional form performs in a typical text is illustrated using the examples of the two frequently addressed texts in the context of quantitative studies. These are *Alice's Adventures in Wonderland* by Lewis Carroll [\[38,](#page-11-20) [39,](#page-11-21) [40\]](#page-11-22) and *David Copperfield* by Charles Dickens [\[41,](#page-11-23) [42,](#page-12-0) [43\]](#page-12-1). The corresponding empirical distributions are fitted with the discrete Weibull distribution by finding numerically the maximum likelihood estimates of *p* and *β* parameters. Three cases are considered: (i) full stops, (ii) full stops and commas, (iii) all punctuation marks.

As the juxtaposition of these cases in the corresponding panels (a) and (b) of Fig. [1](#page-3-0) shows, such a representation for these texts appears particularly appropriate in terms of accuracy when all the punctuation marks are merged and considered equivalent - thus case (iii). The quality of such a fit somewhat worsens when the sentence-ending marks and commas (case (ii)) are taken into account and the remaining punctuation marks are ignored. In the extreme of case (i), when only the partition of text into sentences is considered, the quality of an analogous fit further degrades such that even its validity can here be questioned. In fact, in this last case the fitted parameter *β* becomes closest to unity which thus signals that the process of the entire sentence length formation is nearer to the uncorrelated geometric distribution. In some cases (e.g. the stream-of-consciousness narrative [\[44\]](#page-12-2)) the sentence formation may even depart towards a more 'bursty' dynamics with *β <* 1, similarly as in the recurrence patterns of some words [\[45\]](#page-12-3).

The more basic sentence constituents such as clauses, phrases or even single words, as highlighted by the recurrence patterns involving all the punctuation, already involve stronger correlations towards reducing the distribution tails and to make the Weibull distribution (here *β* = 1.38 and 1.34 correspondingly) very efficient in reproducing essentially all its relevant features. It is also interesting to notice that adding only commas (which are one of two most frequent punctuation marks, the other being full stops) to sentence-ending punctuation marks and ignoring all the remaining ones, thus case (ii), still reduces the values of *β* quite substantially and somewhat worsens the quality of fit in terms of the Weibull distribution. This may be taken as an indication that consistency arguments in this kind of study require merging all the punctuation marks.

According to Eq. [\(3\)](#page-2-0) the parameter *p* denotes the probability that the next punctuation mark follows the previous one already after one single word, thus for *k* = 1. When only the sentence-ending marks are taken into account

<span id="page-3-0"></span>![](_page_3_Figure_0.jpeg)

Figure 1: Histograms of the distances *k* between punctuation marks (the distances are measured by the number of words between consecutive punctuation marks), for *Alice's Adventures in Wonderland* by Lewis Carroll (a) and *David Copperfield* by Charles Dickens (b) are considered in the three following cases: In (a1) and (b1) all the sentence-ending marks are included, in (a2) and (b2) the commas are also included, in (a3) and (b3) all the punctuation marks are taken into account. The points on the blue curve represent the discrete Weibull distributions fitted to the data (note that the distributions are discrete, and the curves are plotted only as a guide to the eye). In each of the charts, the inset presents the rescaled Weibull plots (e*x,*e*y*) (defined in [Appendix A\)](#page-13-1), which allow to collectively assess the quality of fit to different discrete Weibull distributions; a straight line segment from (0*,* 0) to (1*,* 1) (red) corresponds to a perfect agreement between the empirical distribution and *some* discrete Weibull distribution. The parameters *p* and *β* of the fitted distribution and the value of the root mean squared error between the empirical and the fitted cumulative distribution function (F-F RMSE) are given next to each inset. (c) The rescaled Weibull plots of the distributions of distances between consecutive punctuation marks, for 240 books in 7 languages, plotted separately for each language. Each curve represents one book. The inset in the top left corner contains all the plots presented together (without the partition into individual languages). In the bottom right inset, the rescaled Weibull plots of the distributions of sentence lengths are presented, for all the texts in all the studied languages. (d) Exemplary probability mass functions *P*(*k*) of discrete Weibull distributions and of the corresponding hazard functions *h*(*k*). The parameter *p* is equal to 0.1 for all three distributions; the values of *β* are: *β* = 0*.*75 (red), *β* = 1 (green; this is the exponential distribution), and *β* = 1*.*25 (blue).

<span id="page-4-0"></span>![](_page_4_Figure_0.jpeg)

Figure 2: The parameters p and  $\beta$  of the discrete Weibull distributions fitted to the distances between punctuation marks. The upper left chart (ALL) pertains to all the studied languages collectively, the remaining ones present results for the individual languages. In each plot, a text is represented by a point  $(p, \beta)$ . All the plots are in the same scale. The dashed lines are isolines of constant expected value of the discrete Weibull distribution - all distributions with  $(p, \beta)$  along one such line have the same expected value. In each plot pertaining to a single language, the quantities  $\langle p \rangle$  and  $\langle \beta \rangle$ , the average values of p and  $\beta$ , are given, and the centroid of the point cloud,  $(\langle p \rangle, \langle \beta \rangle)$  is marked by "+". The ellipses characterize the distributions of points - the semi-axes of each ellipse are the principal components of the point set in the given language. The major semi-axis of the ellipse gives the direction of the greatest variance and its length is the square root of that variance. The length of the minor semi-axis is the square root of the variance in the perpendicular direction.

this probability is expected to assume the lowest values and the corresponding numbers listed in Fig. 1 confirm this. Including in addition the commas (case (ii)) significantly increases this probability which is also anticipated. However, including all the remaining punctuation (case (iii)) somewhat lowers p, which signals that it introduces an element of repulsion.

#### 3.2. Corpora in seven languages

The above observations appear largely universal as they apply through all the mainstream texts in seven major Western languages considered in the present study: English, French, German, Italian, Polish, Russian, and Spanish. The distributions of the inter-punctuation distances, when all the punctuation marks are taken into account, fit well with the Weibull distribution. For the cases corresponding to (ii), and especially to (i), the quality of such a fit systematically breaks down. For all the 240 books in the two extreme cases of (i) and (iii) this is illustrated in Fig. 1(c) in terms of the rescaled Weibull plots (see Appendix A). In such a representation an ideal fit is reflected by the diagonal straight line segment. Clearly, in case (iii) all the lines form a narrow band along such a diagonal, thus indicating a good quality fit, while the dispersion becomes significantly larger in case (i).

The specific pairs of parameters  $\beta$  and p corresponding to the best fits turn out, however, to be significantly varying for different texts as the global scatter plot in the upper left corner of Fig. 2 highlights it. A closer inspection of the distribution of points in this panel reveals a certain grouping tendency such that the centers of gravity of these groups

of points representing texts in different languages are shifted relative to each other. In more quantitative terms this can be read from the remaining seven panels where the group of points for each language is shown in separation with ellipses indicating the principal components of the corresponding points set. It is interesting to see that the points within a given set largely tend to be scattered in the *p* − *β* plane along the isolines of constant expected value of the discrete Weibull distribution. This points to the existence of a characteristic scale for each language considered but that this scale varies among languages.

### *3.3. Hurst exponents*

Examples illustrating the typical behaviour of fluctuation functions *F*(*s*) defined in [Appendix B](#page-13-0) and computed for the series of inter-punctuation distances in the studied books are shown in Fig. [3;](#page-6-0) two variants of time series are considered - one for all the punctuation included (all) and one for the sentence ending marks only (stop). Scaling appears to take place in essentially all the cases considered but in many of them at around the middle of scales there is a cross-over from one scaling region (I) to another (II), which thus results in two different Hurst exponents *H*<sup>I</sup> and *H*II with the latter being larger. This indicates that the effects of persistence are stronger at larger scales. In some of the books there is no such cross-over and one uniform scaling is developed with one Hurst exponent. It is also interesting to see that the quality of scaling is typically better when all the punctuation is taken into account (all) as compared to the sentence-ending marks (stop) only.

The scatter plot shown in Fig. [4](#page-7-0) collects pairs of Hurst exponents for a subset of texts that develop a unique scaling over the entire range of scales allowed by the length of text. For 44 such texts identified, the Hurst exponents are determined in two variants: one is for the series of sentence length (horizontal axis) and the other for the corresponding series of the consecutive intervals between all the punctuation (vertical axis). In all the cases the Hurst exponents appear larger than 0*.*5 which indicates the existence of correlations of the persistent character. In the sentence-ending case, however, these exponents, on average, are significantly larger. This suggests that word sequences between consecutive punctuation marks are more constrained than sentences - in the sense that more freedom is allowed in the arrangemnt of sentences and in correlations between their lengths [\[44\]](#page-12-2). This seems to be consistent with the results regarding probability distributions. As already discussed, the distances between consecutive punctuation marks can be described with one particular form of probability distribution (discrete Weibull distribution), while for sentence lengths such a description is significantly less accurate - therefore, sentence lengths can be said to have less constrained variability.

## *3.4. Hazard rates*

The distribution of punctuation patterns can succinctly and pictorially be comprised by the hazard functions of Eq. [\(3\)](#page-2-0). In the present context they provide information how "urgent" it is to place a punctuation mark in order to pause an uninterrupted word sequence, depending on the length of that sequence. As it is seen from Eq. [\(3\)](#page-2-0) the behaviour of *h*(*k*) at the intermediate values of *k* is determined by the interplay between the values of *p* and *β* parameters. It begins with *p* at *k* = 1 and its changes are governed by the value of *β* parameter. In all the studied cases, *β* is greater than 1, therefore *h*(*k*) is an increasing function - which seems to be an expected result, as it indicates that the "pressure" to terminate a word sequence increases with the length of that sequence. Hazard functions *h*(*k*) calculated from the average values of the parameters *p* and *β* for each corpus independently are displayed in Fig. [5](#page-7-1) within the range of recurrence intervals *k* between 1 and 15 (which corresponds to more than 80% of all observed interpunctuation intervals in each of the studied texts). This representation even more distinctly reveals the differences among the languages studied. In these average values by far the lowest hazard rate is revealed by the English texts and only slightly higher by the Spanish ones. This latter case is particularly striking in view of the fact that for the other two Romance languages [\[46\]](#page-12-4), French and Italian, *h*(*k*) develops values significantly larger and, in addition, is very similar for both of them. It may seem less surprising that in the upper extreme there are the two Slavic languages, Polish and Russian. They are more inclined towards short word sequences between consecutive punctuation marks – and, indeed, in the considered range of *k* they are seen to systematically develop the values of *h*(*k*) by about a factor of two larger than the ones in the lower extreme corresponding to English and Spanish. The averaged *h*(*k*) for German, having the lowest *p* and the highest *β*, behaves somewhat differently as a function of *k*. It starts from the lowest value but increases considerably faster and very quickly exceeds English, Spanish, French and Italian, and even tends to approach the two Slavic languages.

An issue that needs an extra test in this context is to what extent the shapes of *h*(*k*) in Fig. [5](#page-7-1) are forced by the functional form of Eq. [\(3\)](#page-2-0). In order to address this point the hazard rates for all the texts are calculated also directly from the definition and averaged within each corpus. For English and Spanish there appears almost no difference (Fig. [6\)](#page-8-0) between the two ways of evaluating the hazard rate for as large values as *k* ≈ 25 – which points to a large stability and an internal consistency of this result. For the other languages this agreement is seen to terminate somewhat sooner but still acceptable within the statistically significant ranges of *k*.

<span id="page-6-0"></span>![](_page_6_Figure_0.jpeg)

Figure 3: The DFA fluctuation functions F(s) in the log-log scale for the times series of inter-punctuation intervals in the books indicated. Figures (a) and (c) show the results with all the punctuation marks included, and figures (b) and (d) show the results for sentence-ending marks only. The books presented in (a) and (b) are examples of texts whose punctuation has one F(s) scaling regime with a single Hurst exponent H; in the books shown in (c) and (d) there is a crossover and two regimes with different Hurst exponents  $H^I$  and  $H^{II}$  are identified for the time series representing distances between consecutive punctuation marks. The values of H,  $H^I$ , and  $H^{II}$  are given below each plot. The straight dashed lines indicate the best fits from which the Hurst exponents are determined.

<span id="page-7-0"></span>![](_page_7_Figure_0.jpeg)

<span id="page-7-1"></span>Figure 4: The Hurst exponents calculated from the series of inter-punctuation intervals in the books indicated by the numbers from the list (see [Appendix B\)](#page-13-0). Detrended fluctuation analysis [\[37\]](#page-11-19) with the second order detrending polynomial is used for this purpose. Only these books are here included that develop a uniform unique scaling of the corresponding fluctuation functions over the entire range of scales allowed by the length of a book. Abscissa values reflect the Hurst exponents of the sentence-ending punctuation and ordinate for all the punctuation included. The straight line crossing the cloud of points represents the least-square fit.

![](_page_7_Figure_2.jpeg)

Figure 5: The hazard functions *h*(*k*) corresponding to the distributions of inter-punctuation intervals *k* for all the books in each language separately. *h*(*k*) are computed according to Eq. [\(3\)](#page-2-0) using the average values h*p*i and h*β*i of the best fitting parameters *p* and *β* of discrete Weibull distributions.

<span id="page-8-0"></span>![](_page_8_Figure_0.jpeg)

Figure 6: The hazard functions *h*(*k*) characterizing the distributions of the distances *k* between punctuation marks in different languages, with an illustration of two different methods of averaging. In each of the first 7 plots (EN, DE, FR, IT, ES, PL, RU), each of the colored lines represents an empirical hazard function (a hazard function determined from the empirical distribution of punctuation recurrence distances) of a single book in the given language. The solid black line represents the hazard function of the discrete Weibull distribution with parameters h*p*i (average *p* in the studied language) and h*β*i (average *β* in the studied language); this is the same function as presented in Fig. [5.](#page-7-1) The function represented by the dashed black line is obtained by averaging empirical hazard functions directly: the value of that function for a given *k* is equal to the arithmetic mean of the values that the hazard functions describing individual books have for that *k*. The dotted vertical line marks the upper bound of the range of *k* for which the results can be considered reliable. The bound is computed as the average value of the 95th percentile of the punctuation recurrence distance distribution (the 95th percentile of the distribution is determined for each of the books in a given language independently, and the obtained values are averaged). The large oscillations of the empirical hazard functions for large *k* (outside the range of statistical "reliability") are a consequence of poor estimation of probability, which is natural in the tail of the empirical distribution. The last plot (ALL) presents the averaged hazard functions for each of the studied languages, computed by the two described methods; the dashed and the dotted lines correspond to particular methods in the same manner as in the remaining plots, the colors correspond to languages.

<span id="page-9-0"></span>![](_page_9_Figure_0.jpeg)

Figure 7: The effect of text translation on the parameters  $p, \beta$  of the discrete Weibull distribution describing the distances between consecutive punctuation marks. The figure labeled with "(ALL)" presents all the studied languages collectively, the remaining ones show the results for translations into individual target languages. The set of texts consists of 14 books and their translations: 2 books in each of the 7 studied languages are translated into 6 remaining languages; with two translations missing, this gives 96 texts in total. In each of the figures, the dots on the lower plane mark the values of p and  $\beta$  of the texts in their original languages, and the squares on the upper plane give p and  $\beta$  for the same texts translated into the target language (except the texts whose original language is the target language). The correspondence between the original and translated texts is marked by dashed lines and arrows (with the exception of the "(ALL)" plot). Colors of dots and squares represent individual languages in the same way as in Figs. 2 and 5. The values of p and  $\beta$  of the original 14 books are labeled in the "(ALL)" figure - the numbers correspond to the numbers given in Appendix C (in the "translated texts" section). The ellipses on the upper plane are the same ellipses that are shown in Fig. 2.

#### 3.5. Text translation

The system-specific characteristics of languages regarding their inter-punctuation patterns, as identified above, give raise to the question on how the related features transform under translation from one language to another. The present collection of great-quality original texts and their translations allows to reliably approach an answer. Fig. 7 illustrates how the p and  $\beta$  parameters of 7 pairs (14 in total) of texts representing all the seven languages studied transform under translation into the other six languages. Quite impressively, the translations are seen to navigate the resulting p and  $\beta$  parameters towards the ellipsoids of Fig. 2 of the target languages. A more detailed information on the correspondence between the original and translated texts is given in Appendix C. Even though this demonstration is limited in the statistical terms, it nevertheless already provides a strong indication for the robustness of the correlations observed.

## 4. Summary and outlook

Even though punctuation is almost commonly recognized important, often even crucial in properly conveying the intended meaning and facilitating structuring and transmission of information, so far its quantitative analyses are seldom in the scientific literature, especially on the quantitative level. The results shown here indicate direction

and document that such a kind of study can be conducted and inspiring conclusions obtained, revealing both the universal as well as the system-specific aspects. Particularly intriguing is the result that among the major Western languages these are English and not much more Spanish that are the least demanding concerning the necessity to place the next punctuation mark. Still they both are definitely not less precise in formulating utterances than the other languages. Such observations may be taken as an indication that these two languages are better oriented towards optimizing communicative success and expressiveness by, at the same time, reducing the physical and cognitive effort involved. The fact that out of the languages here considered this appears to apply just to the two most global world languages [\[47,](#page-12-5) [48\]](#page-12-6) may not be accidental but points to some deeper foundation. In this context it is advisable to keep in mind that, whatever the mechanism of language is, its functioning is embedded in biological environment and is thus exposed to obey the related biological constraints and preferences [\[49,](#page-12-7) [50\]](#page-12-8). Concepts like generative grammar attempt to explain competence but not performance; some languages may facilitate performance. During their development languages have been gradually reshaping and adopting themselves under influence of other languages and dialects they have encountered. Especially English and Spanish experienced many of such encounters. Whether this made them as they are or they became global because they happen to possess some spontaneously acquired favorable intrinsic syntactic organization emerges an exciting issue for further interdisciplinary explorations.

#### **References**

- <span id="page-10-0"></span>[1] Hauser, M. D., Chomsky, N. & Fitch, W. T. The faculty of language: What is it, who has it, and how did it evolve? *Science* **298**, 1569–1579 (2002).
- <span id="page-10-1"></span>[2] Harris, R. Language as social interaction: Integrationalism versus segregationalism. *Language Sciences* **9**, 131–143 (1987).
- <span id="page-10-2"></span>[3] Pinker, S. *The Language Instinct* (HarperCollins, 2010).
- <span id="page-10-3"></span>[4] Pagel, M. *Wired for culture : the natural history of human cooperation* (Allen Lane, London, 2012).
- <span id="page-10-4"></span>[5] Gelman, S. A. & Roberts, S. O. How language shapes the cultural inheritance of categories. *Proceedings of the National Academy of Sciences USA* **114**, 7900–7907 (2017).
- <span id="page-10-5"></span>[6] Bloom, P. & Keil, F. C. Thinking through language. *Mind and Language* **16**, 351–367 (2001).
- <span id="page-10-6"></span>[7] Solé, R. V., Corominas-Murtra, B., Valverde, S. & Steels, L. Language networks: Their structure, function, and evolution. *Complexity* 20–26 (2010).
- <span id="page-10-7"></span>[8] Pagel, M. Language: Points, grunts and speaks. *Nature* **543**, 620–621 (2017).
- <span id="page-10-8"></span>[9] Darwin, C. *The descent of man, and selection in relation to sex* (John Murray, London, 1871).
- <span id="page-10-9"></span>[10] Bolhuis, J. J., Tattersall, I., Chomsky, N. & Berwick, R. C. How could language have evolved? *PLoS Biology* **12**, e1001934 (2014).
- <span id="page-10-10"></span>[11] Nowak, M. A., Komarova, N. L. & Niyogi, P. Computational and evolutionary aspects of language. *Nature* **417**, 611–617 (2002).
- <span id="page-10-11"></span>[12] Goldin-Meadow, S., Alibali, M. W. Gesture's role in speaking, learning, and creating language. *Annu. Rev. Psychol.* **64**, 257–283 (2013).
- <span id="page-10-12"></span>[13] Bouchard, K. E., Mesgarani, N. & Johnson, K. & Chang, E. F. Functional organization of human sensorimotor cortex for speech articulation. *Nature* **495**, 327–332 (2013).
- <span id="page-10-13"></span>[14] Rabinovich, M. I., Zaks, M. A. & Varona, P. Sequential dynamics of complex networks in mind: Consciousness and creativity. *Physics Reports* **883**, 1–32 (2020).
- <span id="page-10-14"></span>[15] Pinker, S. & Bloom, P. Natural language and natural selection. *Behavioral and Brain Sciences* **13**, 707–727 (1990).
- <span id="page-10-15"></span>[16] Christiansen, M. H. & Chater, N. Language as shaped by the brain. *Behavioral and Brain Sciences* **31**, 489–509 (2008).
- <span id="page-10-16"></span>[17] Christiansen, M. H. & Chater, N. *Creating Language: Integrating Evolution, Acquisition, and Processing* (MIT Press, 2016).

- <span id="page-11-0"></span>[18] Hockett, C. The origin of speech. *Scientific American* **203** (1960).
- <span id="page-11-1"></span>[19] Algeo, J. *The origins and development of the English language* (Wadsworth Cengage Learning, Boston, MA, 2010).
- <span id="page-11-2"></span>[20] Chomsky, N. *Aspects of the theory of syntax* (MIT Press, Cambridge, Massachusetts, 1965).
- <span id="page-11-3"></span>[21] Say, B. & Akman, V. Current approaches to punctuation in computational linguistics. *Computers and the Humanities* **30**, 457–469 (1997).
- <span id="page-11-4"></span>[22] Iyer, P. In praise of the humble comma. *Time* (2001).
- <span id="page-11-5"></span>[23] Baron, N. S. Commas and canaries: the role of punctuation in speech and writing. *Language Sciences* **23**, 15–67 (2001).
- <span id="page-11-6"></span>[24] Parkes, M. B. *Pause and effect : an introduction to the history of punctuation in the West* (University of California Press, Berkeley, 1993).
- <span id="page-11-7"></span>[25] Nunberg, G., Briscoe, E. & Huddleston, R. *Punctuation*, 1723–1764 (Cambridge University Press, Cambridge, 2002).
- <span id="page-11-8"></span>[26] Truss, L. *Eats, Shoots and Leaves: The Zero Tolerance Approach to Punctuation* (Profile Books, 2003).
- <span id="page-11-9"></span>[27] Gray, R. & Atkinson, Q. Language-tree divergence times support the anatolian theory of indo-europen origin. *Nature* **426**, 435–438 (2003).
- <span id="page-11-10"></span>[28] Kulig, A., Kwapień, J., Stanisz, T. & Drożdż, S. In narrative texts punctuation marks obey the same statistics as words. *Information Sciences* **375**, 98–113 (2017).
- <span id="page-11-11"></span>[29] Zipf, G. K. *Human Behavior and the Principle of Least Effort* (Addison-Wesley, Cambridge, 1949).
- <span id="page-11-12"></span>[30] Mandelbrot, B. *Information theory and psycholinguistics: a theory of words frequencies* (MIT Press, Cambridge, 1966).
- <span id="page-11-13"></span>[31] Stanisz, T., Kwapień, J. & Drożdż, S. Linguistic data mining with complex networks: A stylometric-oriented approach. *Information Sciences* **482**, 301–320 (2019).
- <span id="page-11-14"></span>[32] Miller, R. *Survival analysis* (John Wiley and Sons, 1997).
- <span id="page-11-15"></span>[33] Fréchet, M. Sur la loi de probabilité de l'écart maximum. *Annales de la Société Polonaise de Mathematique, Cracovie* **6**, 93–116 (1927).
- <span id="page-11-16"></span>[34] Weibull, W. A statistical distribution function of wide applicability. *Transactions of the American Society of Mechanical Engineers* **18**, 293–297 (1951).
- <span id="page-11-17"></span>[35] Nakagawa, T. & Osaki, S. The discrete weibull distribution. *IEEE Transactions on Reliability* **R-24**, 300–301 (1975).
- <span id="page-11-18"></span>[36] Hurst, H. Long-term storage capacity of reservoirs. *Transactions of American Society of Civil Engineers* **116**, 770–799 (1951).
- <span id="page-11-19"></span>[37] Peng, C.-K. *et al.* Mosaic organization of dna nucleotides. *Physical Review E* **49**, 1685–1689 (1994).
- <span id="page-11-20"></span>[38] Kello, C. T. *et al.* Scaling laws in cognitive sciences. *Trends in Cognitive Sciences* **14**, 223–232 (2010).
- <span id="page-11-21"></span>[39] Ausloos, M. Measuring complexity with multifractals in texts. translation effects. *Chaos, Solitons & Fractals* **45**, 1349–1357 (2012).
- <span id="page-11-22"></span>[40] Bian, C., Lin, R., Zhang, X., Ma, Q. D. Y. & Ivanov, P. C. Scaling laws and model of words organization in spoken and written language. *EPL (Europhysics Letters)* **113**, 18002 (2016).
- <span id="page-11-23"></span>[41] Newman, M. E. J. Finding community structure in networks using the eigenvectors of matrices. *Physical Review E* **74**, 036104 (2006).

- <span id="page-12-0"></span>[42] Goh, K.-I. & Barabási, A.-L. Burstiness and memory in complex systems. *EPL (Europhysics Letters)* **81**, 48002 (2008).
- <span id="page-12-1"></span>[43] Ferrer-i Cancho, R. & Elvevåg, B. Random texts do not exhibit the real zipf's law-like rank distribution. *PLoS ONE* **5**, e9411 (2010).
- <span id="page-12-2"></span>[44] Drożdż, S. &Oświęcimka, P. &Kulig, A. &Kwapień, J. &Bazarnik, K. &Grabska-Gradzińska, I. &Rybicki, J. &Stanuszek, M. Quantifying origin and character of long-range correlations in narrative texts. *Information Sciences* **331**, 32–44 (2016).
- <span id="page-12-3"></span>[45] Altmann, E. G. & Pierrehumbert, J. B. & Motter, A. E. Beyond world frquency: bulls, lulls, and scaling in the temporal distribution of words. *PLoS ONE* **4**, e7678 (2009).
- <span id="page-12-4"></span>[46] Posner, R. *The Romance Languages* (Cambridge University Press, 1996).
- <span id="page-12-5"></span>[47] Crystal, D. *English as a Global Language* (Cambridge University Press, 2003).
- <span id="page-12-6"></span>[48] Ronen, S. *et al.* Links that speak: The global language network and its association with global fame. *Proceedings of the National Academy of Sciences* **111**, E5616–E5622 (2014).
- <span id="page-12-7"></span>[49] Evans, N. & Levinson, S. C. The myth of language universals: Language diversity and its importance for cognitive science. *Behavioral and Brain Sciences* **32**, 429–448 (2009).
- <span id="page-12-8"></span>[50] Lupyan, G. & Dale, R. Why are there different languages? the role of adaptation in linguistic diversity. *Trends in Cognitive Sciences* **20**, 649–660 (2016).

# <span id="page-13-1"></span>**Appendix A. Weibull plots (***x, y***) and rescaled Weibull plots (***x,* <sup>e</sup> *<sup>y</sup>*e**)**

A practical way of assessing and visualizing how well a given data set fits to a Weibull distribution is constructing the so-called Weibull plot. For this purpose Eq. [\(2\)](#page-1-0) is rewritten in the form:

$$\log(-\log(1 - F(k))) = \beta \log k + \log(-\log(1 - p)). \tag{A.1}$$

Then, for the data originating from the discrete Weibull distribution with parameters (*p, β*), a plot of the empirical cumulative distribution function *Femp*(*k*) in coordinates (*x, y*), where

$$x = \log k, \qquad y = \log \left( -\log \left( 1 - F_{emp}(k) \right) \right),$$
 (A.2)

results in a straight line with slope *β* and intercept log (− log (1 − *p*)).

To obtain a rescaled plot, which fits in the square [0*,* 1]×[0*,* 1], and has the reference line with slope 1 and intercept 0, one applies the following transformation. Let *y* = *a* + *bx* denote the equation describing the line representing the assumed Weibull distribution in a considered Weibull plot. The boundaries of the rectangle enclosing the *y*(*x*) plot, denoted by *x*plot*.*min, *x*plot*.*max, *y*plot*.*min, *y*plot*.*max, are defined as:

$$x_{\text{plot.min}} = \min \left\{ x_{\text{min}}, \frac{y_{\text{min}} - a}{b} \right\}, \qquad x_{\text{plot.max}} = \max \left\{ x_{\text{max}}, \frac{y_{\text{max}} - a}{b} \right\},$$

$$y_{\text{plot.min}} = \min \left\{ y_{\text{min}}, a + b x_{\text{min}} \right\}, \qquad y_{\text{plot.max}} = \max \left\{ y_{\text{max}}, a + b x_{\text{max}} \right\}. \tag{A.3}$$

The transformation from the Weibull plot (*x, y*) to the rescaled Weibull plot (*x,* <sup>e</sup> *<sup>y</sup>*e) is then given by:

$$\widetilde{x} = \frac{x - x_{\text{plot.min}}}{x_{\text{plot.max}} - x_{\text{plot.min}}}, \qquad \widetilde{y} = \frac{y - y_{\text{plot.min}}}{y_{\text{plot.max}} - y_{\text{plot.min}}}. \tag{A.4}$$

#### <span id="page-13-0"></span>**Appendix B. Detrended Fluctuation Analysis (DFA)**

Computing the Hurst exponent of a real-valued time series *x*(1)*, x*(2)*, x*(3)*, ..., x*(*N*) with the use of DFA can be presented in the form of an algorithm consisting of the following steps.

1. Determine the *profile* of the series, that is, the cumulative series:

$$y(k) = \sum_{i=1}^{k} x(i).$$

- 2. Divide the series into *N<sup>s</sup>* = b*N/s*c non-overlapping segments *I<sup>ν</sup>* of equal length *s* (the notation b**·**c represents the floor function, and *I<sup>ν</sup>* denotes the set of time series' indices belonging to the *ν*-th segment; a segment of length *s* starting at some index *k* consists of indices *k, k* + 1*, k* + 2*, ..., k* + *s* − 1). To avoid disregarding any piece of the data, make two partitions - one starting from *k* = 1 and one starting from the opposite end of the series; this gives 2*N<sup>s</sup>* (overlapping) segments in total.
- 3. *Detrend* the cumulative series compute a local polynomial trend *p<sup>ν</sup>* for each segment *Iν*, using the least squares method and construct the detrended cumulative series *y*(*k*)−*pν*(*k*). The order of the chosen polynomial influences the shape of the trend that can be removed from the data; common choices are linear, quadratic, and cubic polynomials.
- 4. Compute the quantity *F* 2 (*ν, s*), called variance, for each segment *Iν*:

$$F^{2}(\nu, s) = \frac{1}{s} \sum_{k \in I_{\nu}} (y(k) - p_{\nu}(k))^{2}$$

*.*

5. Compute a single value of the *fluctuation function F*(*s*) (which characterizes the fluctuations at a given scale) for a given *s* as the square root of the mean of the variances *F* 2 (*ν, s*):

$$F(s) = \left(\frac{1}{2N_s} \sum_{\nu=1}^{2N_s} F^2(\nu, s)\right)^{1/2}.$$

- 6. Repeat the steps from 2 to 5 for different segment lengths *s* chosen from some range [*s*min; *s*max]; the choice depends on the studied data, but it is often suggested that *s*min should be not less than 10 and *s*max not greater than *N/*5. With that procedure, the set of values of *F*(*s*) for different *s* is obtained.
- 7. Investigate the scaling behavior of *F*(*s*); if within the studied range of *s* the fluctuation function is described by a power law of the form:

$$F(s) \approx Cs^H$$
,

where *C* is a constant, then *H* is the Hurst exponent characterizing the studied time series.

#### <span id="page-14-0"></span>**Appendix C. Books used in the study**

All the texts used in the analysis are given below; the list contains titles, authors' names, and the parameters *p* and *β* of the discrete Weibull distribution fitted to the intervals between merged punctuation marks. The texts used to study the effects of translation are listed below the main data set; these texts are assigned numbers, corresponding to the numbers labeling points in Figs. [4](#page-7-0) and [7.](#page-9-0)

## **The main data set**

## English

- 1. *Little Women* L. M. Alcott; *p*= 0*.*07, *β* = 1*.*37
- 2. *Pride and Prejudice* J. Austen; *p*= 0*.*06, *β* = 1*.*40
- 3. *Sense and Sensibility* J. Austen; *p*= 0*.*06, *β* = 1*.*43
- 4. *Jane Eyre: An Autobiography* C. Brontë; *p*= 0*.*10, *β* = 1*.*30
- 5. *The Thirty-Nine Steps* J. Buchan; *p*= 0*.*03, *β* = 1*.*58
- 6. *The Adventures of Tom Sawyer* S. L. Clemens; *p*= 0*.*13, *β* = 1*.*11
- 7. *The Prince and the Pauper* S. L. Clemens; *p*= 0*.*09, *β* = 1*.*27
- 8. *The Rotters' Club* J. Coe; *p*= 0*.*11, *β* = 1*.*16
- 9. *Heart of Darkness* J. Conrad; *p*= 0*.*10, *β* = 1*.*23
- 10. *The Last of the Mohicans* J. F. Cooper; *p*= 0*.*07, *β* = 1*.*33
- 11. *Robinson Crusoe* D. Defoe; *p*= 0*.*05, *β* = 1*.*55
- 12. *David Copperfield* C. Dickens; *p*= 0*.*09, *β* = 1*.*34
- 13. *Olivier Twist* C. Dickens; *p*= 0*.*12, *β* = 1*.*25
- 14. *The Pickwick Papers* C. Dickens; *p*= 0*.*14, *β* = 1*.*17
- 15. *Alice's Adventures in Wonderland* C. L. Dodgson; *p*= 0*.*09, *β* = 1*.*38
- 16. *The Adventures of Sherlock Holmes* A. C. Doyle; *p*= 0*.*10, *β* = 1*.*15
- 17. *Middlemarch* M. A. Evans; *p*= 0*.*07, *β* = 1*.*25
- 18. *Absalom, Absalom!* W. Faulkner; *p*= 0*.*11, *β* = 1*.*00
- 19. *The History of Tom Jones, a Foundling* H. Fielding; *p*= 0*.*09, *β* = 1*.*24
- 20. *The Great Gatsby* F. S. K. Fitzgerald; *p*= 0*.*09, *β* = 1*.*23
- 21. *A Room with a View* E. M. Forster; *p*= 0*.*10, *β* = 1*.*34
- 22. *Tess of the d'Urbervilles* T. Hardy; *p*= 0*.*09, *β* = 1*.*23
- 23. *The Scarlet Letter* N. Hawthorne; *p*= 0*.*09, *β* = 1*.*28
- 24. *The Old Man and the Sea* E. Hemingway; *p*= 0*.*07, *β* = 1*.*13
- 25. *Brave New World* A. Huxley; *p*= 0*.*12, *β* = 1*.*21

- 26. *The Portrait of a Lady* H. James; *p*= 0*.*07, *β* = 1*.*34
- 27. *Kim* J. R. Kipling; *p*= 0*.*09, *β* = 1*.*30
- 28. *Sons and Lovers* D. H. Lawrence; *p*= 0*.*09, *β* = 1*.*40
- 29. *The Lion, the Witch and the Wardrobe* C. S. Lewis; *p*= 0*.*12, *β* = 1*.*07
- 30. *Moby-Dick; or, The Whale* H. Melville; *p*= 0*.*11, *β* = 1*.*22
- 31. *Gone with the Wind* M. Mitchell; *p*= 0*.*10, *β* = 1*.*12
- 32. *Anne of Green Gables* L. M. Montgomery; *p*= 0*.*10, *β* = 1*.*13
- 33. *Animal Farm* G. Orwell; *p*= 0*.*06, *β* = 1*.*33
- 34. *Pointed Roofs* D. Richardson; *p*= 0*.*12, *β* = 1*.*11
- 35. *The Catcher in the Rye* J. D. Salinger; *p*= 0*.*11, *β* = 1*.*22
- 36. *Ivanhoe* W. Scott; *p*= 0*.*09, *β* = 1*.*29
- 37. *Old Mortality* W. Scott; *p*= 0*.*09, *β* = 1*.*24
- 38. *Frankenstein; or, The Modern Prometheus* M. Shelley; *p*= 0*.*06, *β* = 1*.*33
- 39. *Tristram Shandy* L. Sterne; *p*= 0*.*09, *β* = 1*.*35
- 40. *Treasure Island* R. L. Stevenson; *p*= 0*.*12, *β* = 1*.*18
- 41. *Gulliver's Travels* J. Swift; *p*= 0*.*04, *β* = 1*.*61
- 42. *Vanity Fair* W. M. Thackeray; *p*= 0*.*08, *β* = 1*.*29
- 43. *The Time Machine* H. G. Wells; *p*= 0*.*06, *β* = 1*.*43
- 44. *The Waves* A. V. Woolf; *p*= 0*.*10, *β* = 1*.*25

#### German

- 1. *Geschichte vom braven Kasperl und dem schönen Annerl* C. Brentano; *p*= 0*.*06, *β* = 1*.*55
- 2. *Wir Kinder vom Bahnhof Zoo* C. Felscherinow; *p*= 0*.*03, *β* = 1*.*84
- 3. *Der Stechlin* T. Fontane; *p*= 0*.*08, *β* = 1*.*45
- 4. *Effi Briest* T. Fontane; *p*= 0*.*08, *β* = 1*.*46
- 5. *Frau Jenny Treibel* T. Fontane; *p*= 0*.*09, *β* = 1*.*40
- 6. *Die Blechtrommel* G. Grass; *p*= 0*.*07, *β* = 1*.*50
- 7. *Klein Zaches genannt Zinnober* E. T. A. Hoffmann; *p*= 0*.*08, *β* = 1*.*40
- 8. *Lebens-Ansichten des Katers Murr* E. T. A. Hoffmann; *p*= 0*.*07, *β* = 1*.*52
- 9. *Das Schloss* F. Kafka; *p*= 0*.*06, *β* = 1*.*59
- 10. *Der Process* F. Kafka; *p*= 0*.*05, *β* = 1*.*64
- 11. *Emil und die Detektive* E. Kästner; *p*= 0*.*08, *β* = 1*.*51
- 12. *Der grüne Heinrich* G. Keller; *p*= 0*.*03, *β* = 1*.*67
- 13. *Die Leute von Seldwyla* G. Keller; *p*= 0*.*04, *β* = 1*.*62
- 14. *Der Untertan* H. Mann; *p*= 0*.*06, *β* = 1*.*65
- 15. *Professor Unrat oder Das Ende eines Tyrannen* H. Mann; *p*= 0*.*06, *β* = 1*.*60
- 16. *Buddenbrooks* T. Mann; *p*= 0*.*09, *β* = 1*.*37
- 17. *Der Zauberberg* T. Mann; *p*= 0*.*07, *β* = 1*.*47
- 18. *Doktor Faustus* T. Mann; *p*= 0*.*07, *β* = 1*.*47
- 19. *Winnetou* K. May; *p*= 0*.*06, *β* = 1*.*58
- 20. *Der Mann ohne Eigenschaften* R. Musil; *p*= 0*.*04, *β* = 1*.*67
- 21. *Also sprach Zarathustra* F. Nietzsche; *p*= 0*.*07, *β* = 1*.*56
- 22. *Die Chronik der Sperlingsgasse* W. Raabe; *p*= 0*.*10, *β* = 1*.*33
- 23. *Eulenpfingsten* W. Raabe; *p*= 0*.*09, *β* = 1*.*27
- 24. *Im Siegeskranze* W. Raabe; *p*= 0*.*04, *β* = 1*.*54
- 25. *Pfisters Mühle* W. Raabe; *p*= 0*.*10, *β* = 1*.*21
- 26. *Hiob* J. Roth; *p*= 0*.*06, *β* = 1*.*62
- 27. *Radetzkymarsch* J. Roth; *p*= 0*.*07, *β* = 1*.*54
- 28. *Der Schimmelreiter* T. Storm; *p*= 0*.*08, *β* = 1*.*38
- 29. *Immensee* T. Storm; *p*= 0*.*06, *β* = 1*.*56
- 30. *Peter Schlemihls wundersame Geschichte* A. von Chamisso; *p*= 0*.*05, *β* = 1*.*65
- 31. *Die Judenbuche Ein Sittengemälde aus dem gebirgichten Westfalen* A. von Droste-Hülshoff; *p*= 0*.*08, *β* = 1*.*42

- 32. *Die Leiden des jungen Werthers* J. W. von Goethe; *p*= 0*.*07, *β* = 1*.*57
- 33. *Wilhelm Meisters Lehrjahre* J. W. von Goethe; *p*= 0*.*05, *β* = 1*.*63
- 34. *Michael Kohlhaas* H. von Kleist; *p*= 0*.*10, *β* = 1*.*52

### French

- 1. *Candide* F. M. Arouet; *p*= 0*.*09, *β* = 1*.*31
- 2. *Le Rouge et le Noir, Chronique du XIXe siècle* H. Beyle; *p*= 0*.*06, *β* = 1*.*40
- 3. *La Chute* A. Camus; *p*= 0*.*13, *β* = 1*.*20
- 4. *La Peste* A. Camus; *p*= 0*.*10, *β* = 1*.*23
- 5. *Adolphe* B. Constant; *p*= 0*.*05, *β* = 1*.*51
- 6. *Atala, ou Les Amours de deux sauvages dans le désert* F. R. de Chateaubriand; *p*= 0*.*04, *β* = 1*.*65
- 7. *Germinie Lacerteux* J. & E. de Goncourt; *p*= 0*.*10, *β* = 1*.*25
- 8. *La Princesse de Clèves* M. M. de La Fayette; *p*= 0*.*05, *β* = 1*.*40
- 9. *Les Liaisons dangereuses* P. C. de Laclos; *p*= 0*.*06, *β* = 1*.*46
- 10. *Bel-Ami* G. de Maupassant; *p*= 0*.*13, *β* = 1*.*20
- 11. *Le Petit Prince* A. de Saint-Exupéry; *p*= 0*.*08, *β* = 1*.*47
- 12. *Vol de nuit* A. de Saint-Exupéry; *p*= 0*.*10, *β* = 1*.*44
- 13. *Artamène ou le Grand Cyrus* M. de Scudéry; *p*= 0*.*03, *β* = 1*.*78
- 14. *La Reine Margot* A. Dumas; *p*= 0*.*18, *β* = 1*.*02
- 15. *Le Comte de Monte-Cristo* A. Dumas; *p*= 0*.*14, *β* = 1*.*10
- 16. *Les Trois Mousquetaires* A. Dumas; *p*= 0*.*14, *β* = 1*.*11
- 17. *Jacques* A. A. L. Dupin; *p*= 0*.*06, *β* = 1*.*40
- 18. *La Petite Fadette* A. A. L. Dupin; *p*= 0*.*06, *β* = 1*.*35
- 19. *Valentine* A. A. L. Dupin; *p*= 0*.*08, *β* = 1*.*27
- 20. *L'Éducation sentimentale* G. Flaubert; *p*= 0*.*12, *β* = 1*.*34
- 21. *Madame Bovary* G. Flaubert; *p*= 0*.*12, *β* = 1*.*28
- 22. *Le Grand Meaulnes* H. A. Fournier; *p*= 0*.*09, *β* = 1*.*30
- 23. *Mademoiselle de Maupin* T. Gautier; *p*= 0*.*06, *β* = 1*.*36
- 24. *Les Misérables* V. Hugo; *p*= 0*.*10, *β* = 1*.*25
- 25. *Notre-Dame de Paris* V. Hugo; *p*= 0*.*12, *β* = 1*.*18
- 26. *Le Fantôme de l'Opéra* G. Leroux; *p*= 0*.*14, *β* = 1*.*08
- 27. *Histoire du chevalier Des Grieux et de Manon Lescaut* A. Prévost; *p*= 0*.*06, *β* = 1*.*40
- 28. *À la recherche du temps perdu* M. Proust; *p*= 0*.*08, *β* = 1*.*24
- 29. *Le Tour du monde en quatre-vingts jours* J. Verne; *p*= 0*.*11, *β* = 1*.*27
- 30. *Vingt Mille Lieues sous les mers* J. Verne; *p*= 0*.*10, *β* = 1*.*26
- 31. *Lourdes* É. Zola; *p*= 0*.*10, *β* = 1*.*42
- 32. *Nana* É. Zola; *p*= 0*.*13, *β* = 1*.*34

#### Italian

- 1. *Il marchese di Roccaverdina* L. Capuana; *p*= 0*.*14, *β* = 1*.*14
- 2. *Le avventure di Pinocchio* C. Collodi; *p*= 0*.*09, *β* = 1*.*37
- 3. *Il piacere* G. D'Annunzio; *p*= 0*.*13, *β* = 1*.*16
- 4. *Ettore Fieramosca* M. d'Azeglio; *p*= 0*.*06, *β* = 1*.*42
- 5. *Niccolò dei Lapi* M. d'Azeglio; *p*= 0*.*08, *β* = 1*.*34
- 6. *Cuore* E. De Amicis; *p*= 0*.*11, *β* = 1*.*33
- 7. *Il romanzo di un maestro* E. De Amicis; *p*= 0*.*08, *β* = 1*.*37
- 8. *I Viceré* F. De Roberto; *p*= 0*.*10, *β* = 1*.*31
- 9. *L'Illusione* F. De Roberto; *p*= 0*.*12, *β* = 1*.*34
- 10. *Canne al vento* G. Deledda; *p*= 0*.*14, *β* = 1*.*13
- 11. *Cenere* G. Deledda; *p*= 0*.*14, *β* = 1*.*20
- 12. *Il nome della rosa* U. Eco; *p*= 0*.*08, *β* = 1*.*28

- 13. *Malombra* A. Fogazzaro; *p*= 0*.*14, *β* = 1*.*13
- 14. *Piccolo mondo antico* A. Fogazzaro; *p*= 0*.*13, *β* = 1*.*12
- 15. *Dell'arte della guerra* N. Machiavelli; *p*= 0*.*06, *β* = 1*.*40
- 16. *Il principe* N. Machiavelli; *p*= 0*.*04, *β* = 1*.*70
- 17. *I promessi sposi* A. Manzoni; *p*= 0*.*11, *β* = 1*.*37
- 18. *Le confessioni d'un italiano* I. Nievo; *p*= 0*.*05, *β* = 1*.*48
- 19. *Le mie prigioni* S. Pellico; *p*= 0*.*07, *β* = 1*.*53
- 20. *Il fu Mattia Pascal* L. Pirandello; *p*= 0*.*20, *β* = 1*.*07
- 21. *Uno, nessuno e centomila* L. Pirandello; *p*= 0*.*16, *β* = 1*.*05
- 22. *Il Corsaro Nero* E. Salgari; *p*= 0*.*11, *β* = 1*.*20
- 23. *Le tigri di Mompracem* E. Salgari; *p*= 0*.*14, *β* = 1*.*11
- 24. *Addio, amore!* M. Serao; *p*= 0*.*14, *β* = 1*.*26
- 25. *Il romanzo della fanciulla* M. Serao; *p*= 0*.*12, *β* = 1*.*31
- 26. *La coscienza di Zeno* I. Svevo; *p*= 0*.*06, *β* = 1*.*28
- 27. *Una vita* I. Svevo; *p*= 0*.*06, *β* = 1*.*26
- 28. *Fosca* I. U. Tarchetti; *p*= 0*.*09, *β* = 1*.*35
- 29. *Con gli occhi chiusi* F. Tozzi; *p*= 0*.*10, *β* = 1*.*35
- 30. *Tre croci* F. Tozzi; *p*= 0*.*13, *β* = 1*.*28
- 31. *I Malavoglia* G. Verga; *p*= 0*.*04, *β* = 1*.*62
- 32. *Mastro Don Gesualdo* G. Verga; *p*= 0*.*13, *β* = 1*.*27

## Spanish

- 1. *La Regenta* L. Alas; *p*= 0*.*11, *β* = 1*.*21
- 2. *La vida de Lazarillo de Tormes* Anonymous; *p*= 0*.*06, *β* = 1*.*40
- 3. *La barraca* V. Blasco Ibánez; *p*= 0*.*06, *β* = 1*.*37
- 4. *Los cuatro jinetes del Apocalipsis* V. Blasco Ibánez; *p*= 0*.*06, *β* = 1*.*43
- 5. *Escenas andaluzas* S. E. Calderón; *p*= 0*.*08, *β* = 1*.*28
- 6. *Rayuela* J. Cortázar; *p*= 0*.*12, *β* = 1*.*12
- 7. *El sombrero de tres picos* P. A. de Alarcón; *p*= 0*.*12, *β* = 1*.*20
- 8. *Don Quijote de la Mancha* M. de Cervantes; *p*= 0*.*10, *β* = 1*.*22
- 9. *El Periquillo Sarniento* J. J. F. de Lizardi; *p*= 0*.*07, *β* = 1*.*33
- 10. *Penas arriba* J. M. de Pereda; *p*= 0*.*06, *β* = 1*.*32
- 11. *Sotileza* J. M. de Pereda; *p*= 0*.*09, *β* = 1*.*26
- 12. *La vida del Buscón* F. de Quevedo; *p*= 0*.*09, *β* = 1*.*30
- 13. *Abel Sánchez* M. de Unamuno; *p*= 0*.*18, *β* = 1*.*08
- 14. *Tirano Banderas* R. M. del Valle-Inclán; *p*= 0*.*10, *β* = 1*.*34
- 15. *Dona Bárbara* R. Gallegos; *p*= 0*.*10, *β* = 1*.*22
- 16. *Cien anos de soledad* G. García Márquez; *p*= 0*.*04, *β* = 1*.*42
- 17. *El Senor de Bembibre* E. Gil y Carrasco; *p*= 0*.*07, *β* = 1*.*26
- 18. *Sab* G. Gómez de Avellaneda; *p*= 0*.*06, *β* = 1*.*32
- 19. *El Criticón* B. Gracián; *p*= 0*.*08, *β* = 1*.*37
- 20. *Don Segundo Sombra* R. Güiraldes; *p*= 0*.*07, *β* = 1*.*43
- 21. *María* J. Isaacs; *p*= 0*.*08, *β* = 1*.*28
- 22. *A la costa* L. A. Martínez; *p*= 0*.*08, *β* = 1*.*27
- 23. *Amaya o los vascos en el siglo VIII* F. Navarro Villoslada; *p*= 0*.*08, *β* = 1*.*37
- 24. *Los pazos de Ulloa* E. Pardo Bazán; *p*= 0*.*09, *β* = 1*.*32
- 25. *Dona Perfecta* B. Pérez Galdós; *p*= 0*.*10, *β* = 1*.*23
- 26. *Fortunata y Jacinta* B. Pérez Galdós; *p*= 0*.*08, *β* = 1*.*31
- 27. *Misericordia* B. Pérez Galdós; *p*= 0*.*10, *β* = 1*.*31
- 28. *La vorágine* J. E. Rivera; *p*= 0*.*09, *β* = 1*.*33
- 29. *Pedro Páramo* J. Rulfo; *p*= 0*.*11, *β* = 1*.*25
- 30. *Facundo o civilización y barbarie en las pampas argentinas* D. F. Sarmiento; *p*= 0*.*08, *β* = 1*.*24

- 31. *Dona Luz* J. Valera; *p*= 0*.*06, *β* = 1*.*39
- 32. *Pepita Jiménez* J. Valera; *p*= 0*.*06, *β* = 1*.*41

## Polish

- 1. *Ozimina* W. Berent; *p*= 0*.*11, *β* = 1*.*33
- 2. *Próchno* W. Berent; *p*= 0*.*17, *β* = 1*.*23
- 3. *Kariera Nikodema Dyzmy* T. Dołęga-Mostowicz; *p*= 0*.*15, *β* = 1*.*31
- 4. *As* A. Dygański; *p*= 0*.*10, *β* = 1*.*40
- 5. *Faraon* A. Głowacki; *p*= 0*.*11, *β* = 1*.*40
- 6. *Lalka* A. Głowacki; *p*= 0*.*13, *β* = 1*.*34
- 7. *Ferdydurke* W. Gombrowicz; *p*= 0*.*20, *β* = 1*.*15
- 8. *Trans-Atlantyk* W. Gombrowicz; *p*= 0*.*19, *β* = 1*.*22
- 9. *Inny świat* G. Herling-Grudziński; *p*= 0*.*06, *β* = 1*.*47
- 10. *Kamienie na szaniec* A. Kamiński; *p*= 0*.*09, *β* = 1*.*41
- 11. *Imperium* R. Kapuściński; *p*= 0*.*12, *β* = 1*.*38
- 12. *Król Maciuś Pierwszy* J. Korczak; *p*= 0*.*08, *β* = 1*.*68
- 13. *Stara baśń* J. I. Kraszewski; *p*= 0*.*08, *β* = 1*.*60
- 14. *Cudzoziemka* M. Kuncewiczowa; *p*= 0*.*17, *β* = 1*.*28
- 15. *Koroniarz w Galicji* J. Lam; *p*= 0*.*09, *β* = 1*.*41
- 16. *Zaklęty dwór* W. Łoziński; *p*= 0*.*09, *β* = 1*.*37
- 17. *Szaleństwa panny Ewy* K. Makuszyński; *p*= 0*.*11, *β* = 1*.*41
- 18. *Szatan z siódmej klasy* K. Makuszyński; *p*= 0*.*11, *β* = 1*.*42
- 19. *Trędowata* H. Mniszek; *p*= 0*.*11, *β* = 1*.*50
- 20. *Nad Niemnem* E. Orzeszkowa; *p*= 0*.*13, *β* = 1*.*24
- 21. *Chłopi* W. Reymont; *p*= 0*.*10, *β* = 1*.*46
- 22. *Ziemia obiecana* W. Reymont; *p*= 0*.*11, *β* = 1*.*40
- 23. *Dewajtis* M. Rodziewiczówna; *p*= 0*.*15, *β* = 1*.*39
- 24. *Lato leśnych ludzi* M. Rodziewiczówna; *p*= 0*.*15, *β* = 1*.*34
- 25. *Sklepy cynamonowe* B. Schulz; *p*= 0*.*08, *β* = 1*.*52
- 26. *Ogniem i mieczem* H. Sienkiewicz; *p*= 0*.*10, *β* = 1*.*42
- 27. *Quo vadis* H. Sienkiewicz; *p*= 0*.*09, *β* = 1*.*44
- 28. *W pustyni i w puszczy* H. Sienkiewicz; *p*= 0*.*08, *β* = 1*.*45
- 29. *Nienasycenie* S. I. Witkiewicz; *p*= 0*.*10, *β* = 1*.*38
- 30. *Ludzie bezdomni* S. Żeromski; *p*= 0*.*11, *β* = 1*.*37
- 31. *Popioły* S. Żeromski; *p*= 0*.*11, *β* = 1*.*37
- 32. *Przedwiośnie* S. Żeromski; *p*= 0*.*13, *β* = 1*.*29
- 33. *Poganka* N. Żmichowska; *p*= 0*.*12, *β* = 1*.*34
- 34. *Na srebrnym globie. Rękopis z Księżyca* J. Żuławski; *p*= 0*.*08, *β* = 1*.*51

#### Russian

- 1. Петербург (Peterburg) Б. Н. Бугаев (B. N. Bugaev); *p*= 0*.*23, *β* = 1*.*13
- 2. Белая гвардия (Belaya gvardiya) М. А. Булгаков (M. A. Bulgakov); *p*= 0*.*22, *β* = 1*.*15
- 3. Мастер и Маргарита (Master i Margarita) М. А. Булгаков (M. A. Bulgakov); *p*= 0*.*16, *β* = 1*.*26
- 4. Театральный роман (Teatral'nyy roman) М. А. Булгаков (M. A. Bulgakov); *p*= 0*.*18, *β* = 1*.*27
- 5. Деревня (Der´evnya) И. А. Бунин (I. A. Bunin); *p*= 0*.*20, *β* = 1*.*27
- 6. Жизнь Арсеньева (Zhizn' Arsen'yeva) И. А. Бунин (I. A. Bunin); *p*= 0*.*14, *β* = 1*.*29
- 7. Мёртвые души (Mortvyye dushi) Н. В. Гоголь (N. V. Gogol'); *p*= 0*.*16, *β* = 1*.*28
- 8. Тарас Бульба (Taras bul'ba) Н. В. Гоголь (N. V. Gogol'); *p*= 0*.*13, *β* = 1*.*34
- 9. Обломов (Oblomov) И. А. Гончаров (I. A. Goncharov); *p*= 0*.*18, *β* = 1*.*30
- 10. Обрыв (Obryv) И. А. Гончаров (I. A. Goncharov); *p*= 0*.*18, *β* = 1*.*31
- 11. Бесы (Besy) Ф. М. Достоевский (F. M. Dostoyevskiy); *p*= 0*.*16, *β* = 1*.*26

- 12. Братья Карамазовы (Brat'ya Karamazovy) Ф. М. Достоевский (F. M. Dostoyevskiy); *p*= 0*.*16, *β* = 1*.*27
- 13. Преступление и наказание (Prestupleniye i nakazaniye) Ф. М. Достоевский (F. M. Dostoyevskiy); *p*= 0*.*19, *β* = 1*.*22
- 14. Поединок (Poyedinok) А. И. Куприн (A. I. Kuprin); *p*= 0*.*21, *β* = 1*.*16
- 15. Герой нашего времени (Geroy nashego vremeni) М. Ю. Лермонтов (M. Y. Lermontov); *p*= 0*.*15, *β* = 1*.*36
- 16. Доктор Живаго (Doktor Zhivago) Б. Л. Пастернак (B. L. Pasternak); *p*= 0*.*14, *β* = 1*.*30
- 17. Котлован (Kotlovan) А. П. Платонов (A. P. Platonov); *p*= 0*.*11, *β* = 1*.*38
- 18. Чевенгур (Chevengur) А. П. Платонов (A. P. Platonov); *p*= 0*.*10, *β* = 1*.*47
- 19. Капитанская дочка (Kapitanskaya dochka) А. С. Пушкин (A. S. Pushkin); *p*= 0*.*12, *β* = 1*.*45
- 20. Путешествие из Петербурга в Москву (Puteshestviye iz Peterburga v Moskvu) А. Н. Радищев (A. N. Radishchev); *p*= 0*.*10, *β* = 1*.*44
- 21. Архипелаг ГУЛАГ (Arkhipelag GULAG) А. И. Солженицын (A. I. Solzhenitsyn); *p*= 0*.*14, *β* = 1*.*30
- 22. Пикник на обочине (Piknik na obochine) А. Н. & Б. Н. Стругацкий (A. N. & B. N. Strugatsky); *p* = 0*.*20, *β* = 1*.*24
- 23. Анна Каренина (Anna Karenina) Л. Н. Толстой (L. N. Tolstoy); *p*= 0*.*14, *β* = 1*.*34
- 24. Война и мир (Voyna i mir) Л. Н. Толстой (L. N. Tolstoy); *p*= 0*.*14, *β* = 1*.*29
- 25. Воскресение (Voskreseniye) Л. Н. Толстой (L. N. Tolstoy); *p*= 0*.*14, *β* = 1*.*30
- 26. Дворянское гнездо (Dvoryanskoye gnezdo) И. С. Тургенев (I. S. Turgenev); *p*= 0*.*14, *β* = 1*.*39
- 27. Дым (Dym) И. С. Тургенев (I. S. Turgenev); *p*= 0*.*17, *β* = 1*.*29
- 28. Новь (Nov') И. С. Тургенев (I. S. Turgenev); *p*= 0*.*18, *β* = 1*.*30
- 29. Отцы и дети (Ottsy i deti) И. С. Тургенев (I. S. Turgenev); *p*= 0*.*16, *β* = 1*.*33
- 30. Палата № 6 (Palata № 6) А. П. Чехов (A. P. Chekhov); *p*= 0*.*15, *β* = 1*.*27
- 31. Три года (Tri goda) А. П. Чехов (A. P. Chekhov); *p*= 0*.*14, *β* = 1*.*33
- 32. Тихий Дон (Tikhiy Don) М. А. Шолохов (M. A. Sholokhov); *p*= 0*.*19, *β* = 1*.*26

## **Translated texts**

#### English

- (1) *David Copperfield*, *p*= 0*.*09, *β* = 1*.*34
  - *?* German translation: *p*= 0*.*07, *β* = 1*.*44
  - *?* French translation: *p*= 0*.*09, *β* = 1*.*28
  - *?* Italian translation: *p*= 0*.*11, *β* = 1*.*26
  - *?* Spanish translation: *p*= 0*.*10, *β* = 1*.*18
  - *?* Polish translation: *p*= 0*.*15, *β* = 1*.*27
  - *?* Russian translation: *p*= 0*.*12, *β* = 1*.*37
- (2) *Treasure Island*, *p*= 0*.*12, *β* = 1*.*18
  - *?* German translation: *p*= 0*.*07, *β* = 1*.*50
  - *?* French translation: *p*= 0*.*11, *β* = 1*.*26
  - *?* Italian translation: *p*= 0*.*12, *β* = 1*.*19
  - *?* Spanish translation: *p*= 0*.*11, *β* = 1*.*17
  - *?* Polish translation: *p*= 0*.*10, *β* = 1*.*39
  - *?* Russian translation: *p*= 0*.*13, *β* = 1*.*39

#### German

- (3) *Buddenbrooks*, *p*= 0*.*09, *β* = 1*.*37
  - *?* English translation: *p*= 0*.*11, *β* = 1*.*17
  - *?* Italian translation: *p*= 0*.*11, *β* = 1*.*19
  - *?* Spanish translation: *p*= 0*.*11, *β* = 1*.*12
  - *?* Polish translation: *p*= 0*.*11, *β* = 1*.*35

- *?* Russian translation: *p*= 0*.*15, *β* = 1*.*25
- (4) *Die Leiden des jungen Werthers*, *p*= 0*.*07, *β* = 1*.*57
  - *?* English translation: *p*= 0*.*07, *β* = 1*.*41
  - *?* French translation: *p*= 0*.*09, *β* = 1*.*35
  - *?* Italian translation: *p*= 0*.*09, *β* = 1*.*25
  - *?* Spanish translation: *p*= 0*.*09, *β* = 1*.*18
  - *?* Polish translation: *p*= 0*.*10, *β* = 1*.*47
  - *?* Russian translation: *p*= 0*.*11, *β* = 1*.*43

## French

- (5) *Le Tour du monde en quatre-vingts jours*, *p*= 0*.*11, *β* = 1*.*27
  - *?* English translation: *p*= 0*.*10, *β* = 1*.*28
  - *?* German translation: *p*= 0*.*07, *β* = 1*.*50
  - *?* Italian translation: *p*= 0*.*14, *β* = 1*.*17
  - *?* Spanish translation: *p*= 0*.*10, *β* = 1*.*28
  - *?* Polish translation: *p*= 0*.*10, *β* = 1*.*40
  - *?* Russian translation: *p*= 0*.*12, *β* = 1*.*32
- (6) *Les Misérables*, *p*= 0*.*10, *β* = 1*.*25
  - *?* English translation: *p*= 0*.*09, *β* = 1*.*33
  - *?* German translation: *p*= 0*.*06, *β* = 1*.*53
  - *?* Italian translation: *p*= 0*.*12, *β* = 1*.*23
  - *?* Spanish translation: *p*= 0*.*11, *β* = 1*.*17
  - *?* Polish translation: *p*= 0*.*11, *β* = 1*.*46
  - *?* Russian translation: *p*= 0*.*13, *β* = 1*.*37

## Italian

- (7) *Le avventure di Pinocchio*, *p*= 0*.*09, *β* = 1*.*37
  - *?* English translation: *p*= 0*.*11, *β* = 1*.*25
  - *?* German translation: *p*= 0*.*08, *β* = 1*.*47
  - *?* French translation: *p*= 0*.*13, *β* = 1*.*12
  - *?* Spanish translation: *p*= 0*.*13, *β* = 1*.*16
  - *?* Polish translation: *p*= 0*.*11, *β* = 1*.*44
  - *?* Russian translation: *p*= 0*.*14, *β* = 1*.*33
- (8) *I promessi sposi*, *p*= 0*.*11, *β* = 1*.*37
  - *?* English translation: *p*= 0*.*09, *β* = 1*.*33
  - *?* German translation: *p*= 0*.*06, *β* = 1*.*53
  - *?* French translation: *p*= 0*.*10, *β* = 1*.*21
  - *?* Spanish translation: *p*= 0*.*11, *β* = 1*.*33
  - *?* Polish translation: *p*= 0*.*11, *β* = 1*.*37
  - *?* Russian translation: *p*= 0*.*13, *β* = 1*.*35

## Spanish

- (9) *Don Quijote de la Mancha*, *p*= 0*.*10, *β* = 1*.*22
  - *?* English translation: *p*= 0*.*07, *β* = 1*.*25
  - *?* German translation: *p*= 0*.*05, *β* = 1*.*64
  - *?* French translation: *p*= 0*.*07, *β* = 1*.*28
  - *?* Italian translation: *p*= 0*.*07, *β* = 1*.*33
  - *?* Polish translation: *p*= 0*.*09, *β* = 1*.*49

- *?* Russian translation: *p*= 0*.*11, *β* = 1*.*37
- (10) *La vida de Lazarillo de Tormes*, *p*= 0*.*06, *β* = 1*.*40
  - *?* English translation: *p*= 0*.*05, *β* = 1*.*35
  - *?* German translation: *p*= 0*.*05, *β* = 1*.*67
  - *?* French translation: *p*= 0*.*09, *β* = 1*.*25
  - *?* Italian translation: *p*= 0*.*07, *β* = 1*.*25
  - *?* Polish translation: *p*= 0*.*08, *β* = 1*.*51
  - *?* Russian translation: *p*= 0*.*10, *β* = 1*.*44

## Polish

- (11) *Quo vadis*, *p*= 0*.*09, *β* = 1*.*44
  - *?* English translation: *p*= 0*.*08, *β* = 1*.*33
  - *?* German translation: *p*= 0*.*06, *β* = 1*.*57
  - *?* French translation: *p*= 0*.*11, *β* = 1*.*23
  - *?* Italian translation: *p*= 0*.*09, *β* = 1*.*25
  - *?* Spanish translation: *p*= 0*.*10, *β* = 1*.*16
  - *?* Russian translation: *p*= 0*.*12, *β* = 1*.*38
- (12) *Chłopi*, *p*= 0*.*10, *β* = 1*.*46
  - *?* English translation: *p*= 0*.*08, *β* = 1*.*42
  - *?* German translation: *p*= 0*.*05, *β* = 1*.*61
  - *?* French translation: *p*= 0*.*07, *β* = 1*.*38
  - *?* Spanish translation: *p*= 0*.*09, *β* = 1*.*23
  - *?* Russian translation: *p*= 0*.*13, *β* = 1*.*44

## Russian

- (13) Братья Карамазовы (Brat'ya Karamazovy), *p*= 0*.*16, *β* = 1*.*27
  - *?* English translation: *p*= 0*.*10, *β* = 1*.*27
  - *?* German translation: *p*= 0*.*07, *β* = 1*.*54
  - *?* French translation: *p*= 0*.*11, *β* = 1*.*31
  - *?* Italian translation: *p*= 0*.*11, *β* = 1*.*21
  - *?* Spanish translation: *p*= 0*.*10, *β* = 1*.*27
  - *?* Polish translation: *p*= 0*.*13, *β* = 1*.*39
- (14) Война и мир (Voyna i mir), *p*= 0*.*14, *β* = 1*.*29
  - *?* English translation: *p*= 0*.*10, *β* = 1*.*17
  - *?* German translation: *p*= 0*.*07, *β* = 1*.*46
  - *?* French translation: *p*= 0*.*09, *β* = 1*.*32
  - *?* Italian translation: *p*= 0*.*12, *β* = 1*.*24
  - *?* Spanish translation: *p*= 0*.*11, *β* = 1*.*18
  - *?* Polish translation: *p*= 0*.*06, *β* = 1*.*69