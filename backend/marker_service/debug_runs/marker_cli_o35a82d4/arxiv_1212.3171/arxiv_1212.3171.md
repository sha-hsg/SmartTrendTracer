# **Multifractal analysis of sentence lengths in English literary texts**

Iwona Grabska-Gradzińska <sup>a</sup> , Andrzej Kulig <sup>b</sup> , Jarosław Kwapień <sup>b</sup> , Paweł Oświęcimka <sup>b</sup> , Stanisław Drożdż b, c

a Faculty of Physics, Astronomy and Applied Computer Science, Jagiellonian University, ul. Reymonta 4, 30-059 Kraków, Poland Institute of Nuclear Physics, Polish Academy of Sciences, ul. Radzikowskiego 152, 31-342 Kraków, Poland c Faculty of Physics, Mathematics and Computer Science, Cracow University of Technology, ul. Warszawska 24, 31-155 Kraków, Poland

#### **Abstract**

This paper presents analysis of 30 literary texts written in English by different authors. For each text, there were created time series representing length of sentences in words and analyzed its fractal properties using two methods of multifractal analysis: MFDFA and WTMM. Both methods showed that there are texts which can be considered multifractal in this representation but a majority of texts are not multifractal or even not fractal at all. Out of 30 books, only a few have so-correlated lengths of consecutive sentences that the analyzed signals can be interpreted as real multifractals. An interesting direction for future investigations would be identifying what are the specific features which cause certain texts to be multifractal and other to be monofractal or even not fractal at all.

Keywords: Time series, multifractals, long-range correlations, natural language

#### **1. Introduction**

Natural language is a highly complicated result of human evolution on both the biological and the social level. According to a recent hypothesis, it developed into a selforganized structure such that human brain can easily and spontaneously learn it during a few years of early childhood [1]. This means that, to a significant degree, the structure of natural language reflects the brain's inner organization. This connection is among the issues that make studying natural language especially interesting even outside the field of linguistics.

Indeed, over recent years the natural language has drawn attention of the researchers whose primary field of interest is information science, physics, and science of complex systems [2]. They attempt to explain certain fundamental properties of language like the Zipf law [3, 4, 5], which can be viewed as scale invariance [6, 7, 8], or to identify other properties which are typical for complex systems, like hierarchical structure [9] or long-range correlations [10]. Especially the latter seems to be interesting as reflecting the principles of brain function which is known to be long-range temporally correlated at least in its certain aspects [11,12,13,14]. As regards the correlation structure of natural language, Ebeling and Pöschel [10] showed that pairs of letters can be correlated over distances of a few hundred letters. Ebeling and Neiman [16] refined this analysis and by using as the Hölder exponents and the Fourier power spectra, they proved that such correlations extend over paragraphs and chapters. Hřebiček [17] considered the variability of sentence lengths and found that their Hurst exponent H≈0.6 which means they are positively linearly correlated over long distances. The Hurst R/S analysis was also applied by Montemurro and Pury [18] to time series of words mapped onto numbers according to the words' frequency ranks. As a result, a convincing evidence was given that word usage by the authors of literary works is long-range correlated even over the corpora consisting of many texts of the same author joined together. This means that the correlations of this type are independent of a given text's information content and are due to an author's style of writing or way of thinking. This result, presented in Ref. [18] only for English texts, was later confirmed for other languages with different grammar and semantics by Bhan et al. [21].

Differences in correlation structure between languages were reported by Şahin et al. [20] who unambiguously mapped letters onto numbers, summed up these numbers for each word separately, and the so-preprocessed texts were then a subject to the detrended fluctuation analysis (DFA) [22], which revealed various scaling regimes in the fluctuations that were different for different languages. Melnyk et al. [19] reduced various text samples to coarsegrained symbolic sequences consisting of 0's (the letters am) and 1's (n-z) and communicated that even in this case the language exhibits correlations that can be either negative for short, intra-sequence ranges, or positive for long ranges.

Most of the above studies were largely restricted to linear correlations because of the limitations of the applied methods. However, the scaling properties of different representations of literary texts and their hierarchical organization suggest that they can possess fractal structure. Going a step further one can ask whether this structure is completely homogeneous or rather it comprises nonhomogeneous, multifractal features. Pavlov et al. [23] mapped a text into a point process defined by the intervals between the successive occurrences of specific combination of letters and found that the corresponding sequence is multifractal and presents nonlinear long-range correlations. Similar results for the word-frequency and the word-length time series constructed for L. Carroll texts were communicated by Gillet and Ausloos [15]. An interesting feature of that study is comparison of a natural (English) and an artificial (Esperanto) language which have different multifractal properties.

#### **2. Methods**

Here we consider a different type of text representation: the sentence lengths as measured by the number of words. We choose this particular representation because due to the fact that single sentence often comprises a welldistinguished piece of information, it may somehow reflect the process of thinking. Technically, each sentence in a text is identified by the standard punctuation marks: full-stop, colon, semicolon, interrogation mark and exclamation mark. We neglect commas as in many circumstances they do not distinguish minimum pieces of information (for instance, when they are auxiliary used to separate listed elements or to avoid ambiguity of a message). We count words that appear between consecutive sentence-closing marks and form a time series consisting of the corresponding numbers in a preserved order. We investigate possible nonlinear statistical dependences in such data by considering fractal properties of its structure.

Our principal method of numerical study is the multifractal detrended fluctuation analysis (MFDFA) [24]. We also apply the wavelet transform modulus maxima (WTMM) method [25] as an auxiliary tool which can make the results of MFDFA more trustful (the use of WTMM as a basic tool is not recommended due to its lesser reliability for short signals [26]).

### *2.1. MFDFA*

Let assume that we have a time series of numbers ( ) where denotes the consecutive sentences. For this time series, one needs to estimate the signal profile [24]:

$$Y(i) = \sum_{k=1}^{i} (x(i) - \langle x \rangle), \tag{1}$$

where 〈...〉 denotes the mean of ( ) taken over the whole series. ( ) can now be divided into *M* disjoint segments of length *n* starting from the beginning of the time series { } For each segment , one calculates a local trend by least-squares fitting the polynomial ( ) of order to the signal segment. Then the variance:

$$F^{2}(v,n) = \frac{1}{n} \sum_{j=1}^{n} \left\{ Y[(v-1)n+j] - P_{v}^{(l)}(j) \right\}^{2}.$$
 (2)

has to be derived. In order to avoid neglecting the data points at the end of { } that do not fall into any segment, the same procedure is repeated for *M* segments starting from the end of the signal. In result, one obtains 2*M* segments total and the same number of values of . The polynomial order *l* can be equal to 1 (DFA1), 2 (DFA2). Finally, the variances (2) have to be averaged over all the segments , which leads to the order fluctuation function:

$$F_q(n) = \left\{ \frac{1}{2M} \sum_{v=1}^{2M} [F^2(v, n)]^{q/2} \right\}^{1/q}, q \in \mathbb{R}$$
 (3)

The key step is now to determine the statistical dependence of on *n*, which can be done after calculating ( ) for many different segment lengths *n*. The rationale behind this procedure is that if the analysed time series has fractal properties, the fluctuation function reveals the power-law scaling ( ) () ( ) for large *n*. The family of the scaling exponents ( ) can be obtained in this way by using different values of *q*. The exponents ( ) can be considered a generalization of the Hurst exponent *H* with the special case of ( ) Multifractals can be distinguished from monofractals by looking at ( ) : if ( ) for all *q*, then the signal under study is monofractal; it is multifractal otherwise.

From ( ) , one can calculate the Hölder exponents and the singularity spectrum ( ) using the following relationss(e.g. [22]):

 ( ) ( ) ( ) [ ( )] ( ) where ( ) denotes the derivative of ( ) with respect to *q*.

## 2.2 WTMM

WTMM method exploits the existence of scaling properties of wavelet transform coefficients for fractal signals [23]. The wavelet transform is defined by the following relation:

$$T_{\psi}(n,s) = \frac{1}{s} \sum_{i=1}^{N} \psi\left(\frac{i-n}{s}\right) x(i)$$
 (6)

where is a wavelet kernel shifted by *n* and *s* is scale. It decomposes a signal in time-scale plane. In principle, a mother wavelet can be chosen arbitrarily, but in practice it should well reproduce the features of a studied signal. The family of wavelets which is used most frequently in the context of time series is the derivative of a Gaussian:

$$\psi^{(m)}(x) = \frac{d^m}{dx^m} \left( e^{\frac{-x^2}{2}} \right) \tag{7}$$

working well in removing the signal trends approximated by polynomials up to ( ) order [25].

A singularity present in data leads to a power-law behaviour of the coefficients :

$$T_{\psi}(n_0, s) \sim s^{\alpha(n_0)}. \tag{8}$$

Since this relation might be not stable in the case of densely packed singularities, it is suggested to identify the local maxima of and then calculate the partition function from their moduli:

$$Z(q,s) = \sum_{l \in L(s)} \left| T_{\psi}(n_l(s), s) \right|^q. \tag{9}$$

Here, () is the set of all maxima for scale *s* and () is the position of a particular maximum. Monotonicity of ( ) on *s*' can be preserved by adding a supremum condition:

$$Z(q,s) = \sum_{l \in L(s)} \left( \sup_{S' \le S} \left| T_{\psi}(n_l(s'), s') \right| \right)^q. \tag{10}$$

For a fractal signal, ( ) () .

The singularity spectrum ( ) can be calculated according to the following formulas [27]:

$$\alpha = \tau'(q)$$
 and  $f(\alpha) = q\alpha - \tau(q)$ . (11)

Similar to the above ( ) functions, if ( ) is linear, it indicates a monofractal signal, while its nonlinear behaviour suggests a multifractal one.

#### **3. Results**

We apply the both above methods to time series representing the sentence lengths of 30 randomly selected English literary texts taken from the Gutenberg Project page (5 books by C. Dickens, 4 by J. Austen, 3 books by each of J. Joyce, A. Conan Doyle, and M. Twain, and 1 book by each of O. Wilde, A. Christie, H. Melville, L. Carroll, E.R. Borroughs, C. Darwin, U. Sinclair, J. Swift, M. Shelley, and B. Stoker). In order to obtain statistically significant results, each text consists of at least sentences ("Adventures of Alice in Wonderland" by L. Carroll) with the longest signals reaching ("Ulysses" by J. Joyce and "Bleak House" by C. Dickens).

Interpretation of the fluctuation function behaviour is a delicate matter [28]. The family ( ) can be considered representing multifractal data without any doubt only when the range of n for which ( ) is power-law extends over almost whole possible values of n. For real signals, however, this criterion is typically not met and a scaling range is much shorter. A typical case in this respect is such that the multifractal scaling of ( ) is seen for some <sup>0</sup> and there is only monofractal scaling for <sup>0</sup> with <sup>0</sup> . If this is the case, the interpretation of scaling has to be done with care, based on the results of model data with known fractal properties and

one's own experience [28]. There are two possible interpretations of such result depending on <sup>0</sup> . First, if <sup>0</sup> and surrogate data (for example, consisting of randomized original signals) show also a trace of multifractal scaling below the even smaller threshold <sup>0</sup> , it means that the data under study is in fact monofractal (a single point in a graph of ( ) ) or bifractal (two points) but highly nonstationary, and this nonstationarity together with possible "fat tails" of the corresponding pdf give the apparent multifractal behavior of ( ) . Second, if the range of scaling is long enough (more than one decade long) and <sup>0</sup> is a significant fraction of N, as well as the surrogate data produces a substantially less multifractal behavior of ( ) . (i.e., ( ) is much less nonlinear and the ( ) parabola is narrower) than in the case of the original signals, one may infer that the analysed data is indeed multifractal. Sometimes, the multifractal character of data is accompanied by a long power-law relaxation of the autocorrelation function, but this connection is not always observed.

Fig. 1 shows examples of the fluctuation function ( ) (Eq. (3)) for four texts with different fractal properties: a text without any clear fractal structure (no scaling range of ( ) , (a)), a text with an evident monofractal structure (b), a text with rather spurious multifractal-like structure for small scales n (c), and a text which can be considered real multifractal (d). Each of the 30 texts considered in our study can be assigned to one of these classes. Fig. 2 presents the family of fluctuation functions calculated for real texts (the same as in Figure 1(c) and 1(d)) together with their counterparts for the respective randomized signals. Fig. 3 shows the singularity spectra ( ) for those texts for which this was possible. A comparison of the results obtained with MFDFA and WTMM for an exemplary text is shown in Fig. 4. It should be noted that the more convincing is the multifractality of the data, the closer results are obtained by means of the two methods. Finally, Fig. 5 shows the autocorrelation function for the same four texts as in Fig. 1. As one can clearly see, only in the last example (Fig. 3(d)), the function is power law for some range of n. This confirms our conclusion about multifractality of the underlying text.

Out of 30 books, only a few have so-correlated lengths of consecutive sentences that the analysed signals can be interpreted as real multifractals. Although we observe that for some authors (Twain, Conan Doyle) the calculated fractal properties are roughly invariant under a change of texts. For others, different texts can have different properties (Austen). An interesting direction for future investigations would be identifying what are the specific features that cause certain texts to be multifractal and other to be monofractal or even not fractal at all.

### **4. Conclusions**

We analysed 30 literary texts written in English by 17 different authors. For each text, we created a time series representing length of sentences in words and analysed its fractal properties using two methods of multifractal analysis: MFDFA and WTMM. Both methods showed that there are texts which can be considered multifractal in this representation, but a majority of texts are not multifractal. We obtained no indication what is the origin of multifractality in natural language samples, but there is at least some evidence that, in some cases, the fractal properties can be similar for different works of the same author. Our results suggest that the fractal properties of natural language are a subtle problem which requires much more study in future.

![](_page_3_Figure_2.jpeg)

*FIGURE 1: Fluctuation function Fq(n) calculated for time series of sentence lengths (in words) for 4 representative texts. Since such time series can be leptokurtic, the Rényi parameter was restricted to −3≤q≤3. While no fractal structure can be observed in (a), plot in (d) is convincingly multifractal.*

![](_page_3_Figure_4.jpeg)

*FIGURE 2: Comparison of fluctuation functions Fq(n) for real (left column) and shuffled data (right column) for a text with rather spurious multifractality and a text with real multifractality.*

![](_page_3_Figure_6.jpeg)

*FIGURE 3: Singularity spectra f(α) for different texts. The broader the spectrum, the richer is the fractal structure of data. The texts for which the width of f(α) substantially exceeds 0.1 can be considered multifractal (a criterion based on the authors' own experience).* 

![](_page_3_Figure_8.jpeg)

*FIGURE 4: Comparison of results obtained for the same text of "David Copperfield" by C. Dickens with two different methods of multifractal analysis: MFDFA (left) and WTMM (right).*

![](_page_3_Figure_10.jpeg)

*FIGURE 5: Autocorrelation function for the same texts as in Fig. 1 plotted in log-log scale.*

# **References**

- [1] M.H. Christiansen, N. Chater, Language as shaped by the brain, *Behav. Brain Sci.* vol. 31, pp. 489-509 (2008)
- [2] J. Kwapień, S. Drożdż, Physical approach to complex systems, *Phys. Rep. v*ol. 515, pp. 115-226 (2012)
- [3] R. Ferrer-i-Cancho, R.V. Solé, Two regimes in the frequency of words and the origins of complex lexicons: Zipf's law revisited, J. *Quant. Ling.* vol. 8, pp. 165-173 (2001)
- [4] L. Lü, Z.-K. Zhang, T. Zhou, Scaling laws in human language, preprint arXiv:1202.2903 (2012)
- [5] B. Corominas-Murtra, J. Fortuny, R.V. Solé, Emergence of Zipfs law in the evolution of communication, *Phys. Rev. E* vol. 83, no. 036115 (2011)
- [6] M.E.J. Newman, Power laws, Pareto distributions and Zipf's law, *Cont. Phys*. vol. 45, pp. 323-351 (2005)
- [7] S.K. Baek, S. Bernhardsson, P. Minnhagen, Zipf's law unzipped, *New J. Phys.* vol. 4, no. 043004 (2011)
- [8] I. Grabska-Gradzińska, A. Kulig, J. Kwapień, S. Drożdż, Complex network analysis of literary and scientific texts, *Int. J. Mod. Phys.* Vol. 23, no. 7 (2012)
- [9] C.G. Nevill-Manning, I.H. Witten, Identifying hierarchical structure in sequences: a linear-time algorithm, *J. Artif. Intell. Res.* vol. 7, pp. 67-82 (1997)
- [10] W. Ebeling, T. Pöschel, Entropy and long range correlations in literary English, *Europhys. Lett*. vol.26, pp.241-246 (1994)
- [11] J.M. Hausdorff, P.L. Purdon, C.-K. Peng, Z. Ladin, J.Y. Wei, A.L. Goldberger, Fractal dynamics of human gait: stability of long-range correlations in stride interval fluctuations, J. *Appl. Physiol*. vol. 80, pp. 1448- 1457 (1996)
- [12] M.P. Paulus, M.A. Geyer, D.L. Braff, Long-range correlations in choice sequences of schizophrenic patients, *Schi. Res.* vol. 35, pp. 69-75 (1999)
- [13] K. Linkenkaer-Hansen, V.V. Nikouline, J.M. Palva, R.J. Ilmoniemi, Long-range temporal correlations and scaling behavior in human brain oscillations, *J. Neurosci*. vol. 21, pp. 1370-1377 (2001)
- [14] K. Torre, R. Balasubramaniam, N. Rheaume, L. Lemoine, H.N. Zelaznik, Long-range correlation properties in motor timing are individual and task specific, *Psychon. Bull. Rev*. vol. 18, pp. 339-346 (2011)
- [15] J. Gillet, M. Ausloos, A comparison of natural (English) and artificial (esperanto) languages. A multifractal method based analysis, preprint arXiv:0801.2510 (2008)
- [16] W. Ebeling, A. Neiman, Long-range correlations between letters and sentences in texts, *Physica A* vol. 215, pp. 233-241 (1995)
- [17] L. Hřebiček, Persistence and other aspects of sentence-length series*, J. Quant. Ling.* vol. 4, pp. 105- 109 (1997)

- [18] M.A. Montemurro, P.A. Pury, Long-range correlations in literary corpora, *Fractals* vol. 10, pp. 451-461 (2002)
- [19] S.S. Melnyk, O.V. Usatenko, V.A. Yampol'skii, Competition between two kinds of correlations in literary texts, *Phys. Rev. E* vol. 72, no. 026140 (2005)
- [20] G. Sahin, M. Erentürk, A. Hacinliyan, Detrended fluctuation analysis in natural languages using noncorpus parametrization, *Chaos Solit. Fract*. vol. 41, pp. 198-205 (2009)
- [21] J. Bhan, S. Kim, J. Kim, Y. Kwon, S. Yang, K. Lee, "Longrange correlations in Korean literary corpora, *Chaos Solit. Fract.* vol. 29, pp. 69-81 (2006)
- [22] C.-K. Peng, S.V. Buldyrev, S. Havlin, M. Simons, H.E. Stanley, A.L. Goldberger, Mosaic organization of DNA nucleotides, *Phys. Rev. E* vol. 49, pp. 1685-1689 (1994)
- [23] A.N. Pavlov, W. Ebeling, L. Molgedey, A.R. Ziganshin, V.S. Anishchenko, Scaling features of texts, images and time series, *Physica A* vol. 300, pp. 310-324 (2001)
- [24] J.W. Kantelhardt, S.A. Zschiegner, E. Koscielny-Bunde, S. Havlin, A. Bunde, H.E. Stanley, Multifractal detrended fluctuation analysis of nonstationary time series, *Physica A* vol. 316, pp. 87-114 (2002)
- [25] A. Arneodo, E. Bacry, J.F. Muzy, The thermodynamics of fractals revisited with wavelets, *Physica A* vol. 213-275, pp. 232 (1995)
- [26] P. Oświęcimka, J. Kwapień, S. Drożdż, Wavelet versus detrended fluctuation analysis of multifractal structures, *Phys. Rev. E* vol. 74, no. 016103 (2006)
- [27] T.C. Halsey, M.H. Jensen, L.P. Kadanoff, I. Procaccia, B.I. Shraiman, Fractal measures and their singularities: the characterization of strange sets, *Phys. Rev. A* vol. 33, pp. 1141-1151 (1986)
- [28] S. Drożdż, J. Kwapień, P. Oświęcimka, R. Rak, Quantitative features of multifractal subtleties in time series, *EPL* vol. 88, no. 60003 (2009)