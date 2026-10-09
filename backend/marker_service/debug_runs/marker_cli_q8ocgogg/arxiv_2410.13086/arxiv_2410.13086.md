# Reverse-Engineering the Reader

# Samuel Kiegeland\*1 Ethan Gotlieb Wilcox\*1 Afra Amini<sup>1</sup> David Robert Reich2,3 Ryan Cotterell<sup>1</sup>

<sup>1</sup>ETH Zürich <sup>2</sup>University of Potsdam <sup>3</sup>University of Zürich [skiegeland@ethz.ch](mailto:skiegeland@ethz.ch) [{ethan.wilcox,](mailto:ethan.wilcox@inf.ethz.ch ) [afra.amini,](mailto:afra.amini@inf.ethz.ch ) [ryan.cotterell}](mailto:afra.amini@inf.ethz.ch )@inf.ethz.ch [reich@cl.uzh.ch](mailto:david.reich@@uni-potsdam.de)

# Abstract

Numerous previous studies have sought to determine to what extent language models, pretrained on natural language text, can serve as useful models of human cognition. In this paper, we are interested in the opposite question: whether we can directly optimize a language model to be a useful cognitive model by aligning it to human psychometric data. To achieve this, we introduce a novel alignment technique in which we fine-tune a language model to implicitly optimize the parameters of a linear regressor that directly predicts humans' reading times of in-context linguistic units, e.g., phonemes, morphemes, or words, using surprisal estimates derived from the language model. Using words as a test case, we evaluate our technique across multiple model sizes and datasets and find that it improves language models' psychometric predictive power. However, we find an inverse relationship between psychometric power and a model's performance on downstream NLP tasks as well as its perplexity on held-out test data. While this latter trend has been observed before [\(Oh et al.,](#page-10-0) [2022;](#page-10-0) [Shain et al.,](#page-11-0) [2024\)](#page-11-0), we are the first to induce it by manipulating a model's alignment to psychometric data.

# 1 Introduction

Language comprehension is thought to be predictive and incremental. Research on reaction times [\(Fischler and Bloom,](#page-9-0) [1979\)](#page-9-0), fixation patterns [\(Ehrlich and Rayner,](#page-9-1) [1981\)](#page-9-1), and brain activations [\(Kutas and Hillyard,](#page-10-1) [1984;](#page-10-1) [DeLong et al.,](#page-9-2) [2005\)](#page-9-2) suggests that comprehenders anticipate upcoming linguistic units based on the context in which they occur [\(Kuperberg and Jaeger,](#page-10-2) [2016\)](#page-10-2).[1](#page-0-0) In addition, a large body of evidence shows that when linguistic units are unexpected, they require more cognitive effort to process [\(Miller and McKean,](#page-10-3) [1964;](#page-10-3) [Ehrlich and Rayner,](#page-9-1) [1981;](#page-9-1) [Balota et al.,](#page-9-3) [1985,](#page-9-3) *inter*

*alia*). E.g., reading times of units, e.g., morphemes, words, and sentences, are taken as a measure of cognitive effort, i.e., the less likely the unit is in context, the longer it takes to read [\(Smith and Levy,](#page-11-1) [2013\)](#page-11-1).

In this study, we are interested in reverseengineering the part of the language processing system responsible for predicting abstract linguistic units and testing it by measuring its ability to predict reading times.[2](#page-0-1) To do so, we need, first, to establish a theoretical link between predictability and reading times. For this, we draw on surprisal theory [\(Hale,](#page-10-4) [2001;](#page-10-4) [Levy,](#page-10-5) [2008\)](#page-10-5), which posits that the cognitive effort to process a unit is proportional to its surprisal—the unit's negative log probability given the preceding context. Implicitly, surprisal theory assumes that a comprehender maintains a probability distribution over upcoming units, i.e., it assumes a *human* language model. However, this human language model is a theoretical construct, and cannot be observed directly. Thus, most previous work that tests surprisal theory has done so using probability estimates derived from a language model trained on large swathes of human-written text. Under this paradigm, it has been observed that surprisal estimates derived from language models, fit with regularized maximumlikelihood estimation on large corpora, do yield significant predictors although these findings vary based on the quality [\(Goodkind and Bicknell,](#page-10-6) [2018;](#page-10-6) [Wilcox et al.,](#page-12-0) [2020,](#page-12-0) [2023b\)](#page-11-2), size, and training-data set size [\(Oh et al.,](#page-10-0) [2022;](#page-10-0) [Shain et al.,](#page-11-0) [2024\)](#page-11-0) of the model. One current line of research therefore seeks to uncover what characteristics of pretrained LMs produce better predictors of human reading times, and what this tells us about the human language processing system.

Our paper asks a simple question: Instead of assessing the ability of pretrained LMs to serve as psycholinguistic predictors, can we directly esti-

<span id="page-0-0"></span><sup>\*</sup>Equal contribution.

<sup>1</sup>Our code is available at [https://github.com/samuki/](https://github.com/samuki/reverse-engineering-the-reader) [reverse-engineering-the-reader](https://github.com/samuki/reverse-engineering-the-reader).

<span id="page-0-1"></span><sup>2</sup> In our experiments, we predict abstract units that correspond to words. However, in order to frame our discussion more generally and to align it with our mathematical framework, we use the term units instead.

mate (or fine-tune) a language model so that its surprisal estimates become better predictors of processing effort for linguistic units? We frame this problem as one of aligning the language model to human data [\(Christiano et al.,](#page-9-4) [2017;](#page-9-4) [Schulman](#page-11-3) [et al.,](#page-11-3) [2017;](#page-11-3) [Ouyang et al.,](#page-11-4) [2022;](#page-11-4) [Ziegler et al.,](#page-12-1) [2020;](#page-12-1) [Rafailov et al.,](#page-11-5) [2023\)](#page-11-5). However, in contrast to much previous work, which uses human–model alignment to obtain improvement on natural language processing tasks, e.g., summarizing text [\(Sti](#page-11-6)[ennon et al.,](#page-11-6) [2020\)](#page-11-6) or producing non-toxic outputs [\(Li et al.,](#page-10-7) [2024\)](#page-10-7), we seek to align LMs to be better psychometric predictors. Particularly, we aim to directly align models to human *reading* data by optimizing the parameters of the statistical models typically used to evaluate the psychometric fit. While recent approaches like direct preference optimization (DPO; [Rafailov et al.,](#page-11-5) [2023\)](#page-11-5) are designed to optimize a model's parameters based on human preferences, they rely on pairwise preference data, which is not applicable to real-valued psychometric data. Thus, we propose a novel alignment technique that allows us to directly optimize the language model's parameters in such a way that it serves as a better predictor of real-valued psychometric data. Specifically, we fine-tune the language model to implicitly optimize the coefficients of a linear regression that predicts the reading time of an individual unit.

We test our technique on three English-language reading datasets and find that it increases the statistical fit of a linear regressor in terms of the likelihood it assigns to reading times on a held-out test set. We also observe a positive relationship between a model's psychological predictive power and its perplexity. While it has been observed that better LMs are better psychological models of reading up to a point [\(Goodkind and Bicknell,](#page-10-6) [2018;](#page-10-6) [Wilcox et al.,](#page-12-0) [2020,](#page-12-0) [2023a\)](#page-11-7), after a certain model size, their fit to human reading times decreases [\(Oh](#page-10-0) [et al.,](#page-10-0) [2022;](#page-10-0) [Shain et al.,](#page-11-0) [2024\)](#page-11-0). In other words, beyond an inflection point, better LMs are *worse* predictors of human reading times. Through our alignment procedure, we are able to demonstrate the contrapositive, namely that as we causally make our language models' outputs more aligned with reading, they become worse at predicting the next word.

# 2 Psycholinguistics Background

Put concisely, the goal of this paper is to reverse-engineer pH, a person's internal language model from psychometric data collected through

experimentation. Our reasoning is as follows: if we can align an existing language model p<sup>θ</sup> to more accurately predict such psychometric data, p<sup>θ</sup> will also more closely resemble pH.

# 2.1 Language Models

Let Σ be an alphabet, i.e., a finite, non-empty set, and let Σ def = Σ ∪ {EOS} be the alphabet augmented with a distinguished end-of-string symbol not in Σ. A language model p<sup>θ</sup> is a probability distribution over Σ ∗ , which is the set of all strings over Σ. Further, following [Opedal et al.](#page-11-8) [\(2024\)](#page-11-8), we define the normalized prefix probability

<span id="page-1-0"></span>
$$\pi_{\boldsymbol{\theta}}(\boldsymbol{c}) \stackrel{\text{def}}{=} \frac{1}{Z_{\pi_{\boldsymbol{\theta}}}} \sum_{\boldsymbol{u} \in \Sigma^*} p_{\boldsymbol{\theta}}(\boldsymbol{c}\boldsymbol{u}),$$
 (1)

which is a probability distribution over prefixes c ∈ Σ ∗ , where cu is the concatenation of c and P u. The normalization constant Zπ<sup>θ</sup> = 1 + <sup>u</sup>∈Σ<sup>∗</sup> pθ(u)|u| ensures that all probabilities sum to one. Here |u| denotes the length, i.e., the number of units in a string u. Note that Eq. [\(1\)](#page-1-0) is only well-defined in an LM with finite expected length.

# 2.2 Psychometric Measurements

Let ψ(u, c) ∈ R denote a measurement for a unit u ∈ Σ appearing in context c ∈ Σ ∗ . In this paper, ψ(u, c) represents various reading time measurements for a given unit, such as gaze duration, first fixation duration, and total fixation duration, which are standard approximations to the processing effort of a linguistic unit in context [\(Miller and](#page-10-3) [McKean,](#page-10-3) [1964;](#page-10-3) [Just and Carpenter,](#page-10-8) [1980;](#page-10-8) [Frazier](#page-9-5) [and Rayner,](#page-9-5) [1982;](#page-9-5) [Rayner,](#page-11-9) [1998,](#page-11-9) *inter alia*).

## 2.3 Surprisal Theory

Surprisal theory furnishes us with an easy-tocompute predictor of processing effort that is derived from a pretrained language model. Formally, surprisal theory predicts that the time it takes to process a linguistic unit u ∈ Σ in context c ∈ Σ ∗ is an affine[3](#page-1-1) function of the unit's contextual surprisal under the human language model pH, defined as

$$\iota_{\mathrm{H}}(u \mid \boldsymbol{c}) \stackrel{\mathrm{def}}{=} -\log_2 p_{\mathrm{H}}(u \mid \boldsymbol{c}).$$
 (2)

Surprisal theory has been supported by numerous empirical studies, which have found that surprisal is predictive of reading times across multiple datasets

<span id="page-1-1"></span><sup>3</sup> Previous work has often described the relationship as linear. However, we use affine here due to the additive constant required to link the two.

(Smith and Levy, 2013; Wilcox et al., 2020; Shain et al., 2024), types of reading time measurements (Pimentel et al., 2023), and languages (Kuribayashi et al., 2021; Meister et al., 2021; Wilcox et al., 2023b). Typically,  $p_{\rm H}$  is approximated using a LM estimated from corpus data, i.e., we substitute

$$\iota_{\boldsymbol{\theta}}(u \mid \boldsymbol{c}) \stackrel{\text{def}}{=} -\log_2 p_{\boldsymbol{\theta}}(u \mid \boldsymbol{c}) \tag{3}$$

in for  $\iota_H$  when predicting processing effort.

### <span id="page-2-3"></span>2.4 Linear Modeling

We now discuss how empirical support for surprisal theory is typically adduced. Following previous work, we assume an affine function links a linguistic unit's contextual surprisal and that unit's reading time<sup>4</sup> (Smith and Levy, 2013; Wilcox et al., 2023b; Shain et al., 2024) and apply linear regression to predict reading times based on contextual surprisal. In mathematical jargon, both the psychometric measurements  $\psi(u, c) \colon \overline{\Sigma} \times \Sigma^* \to \mathbb{R}$  and our predictors  $\mathbf{x}_{\theta}(u, c) \colon \overline{\Sigma} \times \Sigma^* \to \mathbb{R}^D$  are real-valued random variables. In the case of the predictor, given a unit  $u \in \overline{\Sigma}$  and a context  $c \in \Sigma^*$ , we define the predictor as a D-dimensional real column vector

<span id="page-2-1"></span>
$$\mathbf{x}_{\boldsymbol{\theta}}(u, \boldsymbol{c}) = [\iota_{\boldsymbol{\theta}}(u \mid \boldsymbol{c}), x^2, \dots, x^D]^\top, \quad (4)$$

which, as depicted, includes our surprisal estimate  $\iota_{\theta}(u \mid c)$ ; the additional variables  $x^2, \ldots, x^D$  are considered to be baseline predictors and are chosen at the modeler's discretion depending on what they seek to test. Given a parameter (column) vector  $\boldsymbol{\beta}_{\theta} \in \mathbb{R}^D$ , we define the following linear model

$$\psi(u, \mathbf{c}) \sim f_{\beta_{\theta}}(\cdot \mid \mathbf{x}_{\theta}(u, \mathbf{c}))$$
 (5a)

$$= \mathcal{N}(\widehat{\psi}_{\beta_{\mathbf{g}}}(u, \mathbf{c}), \sigma^2), \tag{5b}$$

where the linear function

<span id="page-2-4"></span>
$$\widehat{\psi}_{\boldsymbol{\beta}_{\boldsymbol{\theta}}}(u, \boldsymbol{c}) = \mathbf{x}_{\boldsymbol{\theta}}(u, \boldsymbol{c})^{\top} \boldsymbol{\beta}_{\boldsymbol{\theta}}$$
 (6)

constitutes the mean and  $\sigma^2$  is the variance.

We evaluate the predictive power of our model by fitting  $f_{\beta_{\theta}}$  on a training set and measuring the log-likelihood of the test set; higher log-likelihood indicates greater predictive power of the model. To assess how much surprisal contributes to the predictive power, we fit two regression models based on two predictors. The baseline predictor  $\mathbf{x}_{b}(u,c)$ , defined identically to Eq. (4), but with the

estimated surprisal zeroed out, typically consists of a unit's unigram surprisal, i.e., its negative log unigram probability<sup>5</sup> and a unit's length (in characters). The target predictor, denoted by  $\mathbf{x}_{\theta}(u, c)$ , includes the same set of baseline predictors together with the estimated surprisal of the unit u.

To quantify the predictive power of contextual surprisal, we compute the delta log-likelihood  $\Delta_{llh}$  between the two models, which is the average unit-level difference in log-likelihood assigned by the two predictors to the reading time measurements. For a single unit–context pair, we compute:

<span id="page-2-6"></span>
$$\Delta_{\text{llh}}(u, \mathbf{c}) = \log f_{\beta_{\theta}}(\psi(u, \mathbf{c}) \mid \mathbf{x}_{\theta}(u, \mathbf{c})) - \log f_{\beta_{h}}(\psi(u, \mathbf{c}) \mid \mathbf{x}_{b}(u, \mathbf{c})),$$
(7)

where  $\beta_b$  and  $\beta_\theta$  are the coefficients for the baseline and target models, respectively, and are estimated separately. Intuitively, a higher  $\Delta_{llh}$  indicates that the estimated surprisals contribute more to the predictive power or psychometric accuracy of the model over reading times, compared to the baseline predictors (Frank and Bod, 2011).

Having established a metric, delta log-likelihood, to measure how much contextual surprisal contributes to predicting reading times, we are now ready to answer the question we posed at the beginning: Can we fine-tune a language model such that surprisal estimates derived from it become better predictors of reading times?

# 3 Aligning LMs to Psychometric Data

<span id="page-2-5"></span>As discussed in §2.4, the psychometric predictive power of a language model is typically evaluated by assessing the predictive power of surprisal estimates  $\iota_{\theta}(u \mid c)$  of a linguistic unit u in a context c with respect to human reading times. Rather than *evaluating* a language model's psychometric predictive power, in this study, we ask whether we can fine-tune language models to *increase* their psychometric predictive power.

We treat this as an alignment problem (Christiano et al., 2017; Schulman et al., 2017; Ouyang et al., 2022; Ziegler et al., 2020; Rafailov et al., 2023). Let  $p_{\rm ref}$  denote a pretrained language model that will serve as a reference. Further, let  $p_{\theta}$  denote the language model we seek to fine-tune, generally initialized to  $p_{\rm ref}$ . Our goal is to align  $p_{\theta}$  such that its surprisal estimates are more directly correlated with psychometric data in comparison

<span id="page-2-0"></span><sup>&</sup>lt;sup>4</sup>Although, see Hoover et al. (2023) for a different perspective on the shape of the linking function.

<span id="page-2-2"></span><sup>&</sup>lt;sup>5</sup>See Opedal et al. (2024) for a detailed explanation of this predictor variable.

to  $p_{\text{ref}}$ . By means of implicit differentiation, we derive an objective that allows us to perform such psychometric alignment.

## 3.1 Deriving an Objective

**Reward Function.** We draw inspiration from direct preference optimization, which implicitly optimizes the parameters of a reward model for predicting the outcomes of pairwise comparisons between items. However, rather than implicitly fitting a Bradley-Terry model (Bradley and Terry, 1952) to model pairwise preferences given by human annotators, we implicitly fit a linear regressor  $f_{\beta_{\alpha}}$  to model psychometric measurements. Following the notation developed in §2.4, let  $\mathbf{x}_{\theta}(u, c)$  denote the predictor vector, which includes the contextual surprisal derived from the model  $p_{\theta}$ . To optimize the parameters of  $f_{\beta_{\theta}}$ , we define our reward function as the *negative*<sup>6</sup> minimum of the expected mean squared error (MSE) between the observed psychometric data  $\psi(u, c)$  and the predicted values  $\widehat{\psi}_{\beta_{\theta}}(u, c) = \mathbf{x}_{\theta}(u, c)^{\top} \boldsymbol{\beta}_{\theta}$  as defined in Eq. (6). The reward is then given by

<span id="page-3-2"></span>
$$\mathbf{r}(\boldsymbol{\theta}) \stackrel{\text{def}}{=} - \min_{\boldsymbol{\beta}_{\boldsymbol{\theta}} \in \mathbb{R}^{D}(u, \boldsymbol{c}) \sim \pi_{\text{ref}}} \mathbb{E} \left( \psi(u, \boldsymbol{c}) - \widehat{\psi}_{\boldsymbol{\beta}_{\boldsymbol{\theta}}}(u, \boldsymbol{c}) \right)^{2},$$
(8)

where  $\pi_{\rm ref}$ , as defined in Eq. (1), is the normalized prefix probability. Note that under our linear model specified in Eq. (5), maximizing  $r(\theta)$  is equivalent to maximizing the  $\Delta_{\rm llh}$  in Eq. (7).<sup>7</sup>

**Regularization with KL Divergence.** To prevent the fine-tuned model  $p_{\theta}$  from diverging excessively from the pretrained reference model  $p_{\text{ref}}$ , we regularize our objective with the Kullback–Leibler (KL) divergence, as is typically done in RLHF (Schulman et al., 2017; Ziegler et al., 2020; Stiennon et al., 2020; Ouyang et al., 2022). More specifically, the regularization term is defined as:

$$\varphi(\boldsymbol{\theta}) \stackrel{\text{def}}{=} \underset{\boldsymbol{c} \sim \pi_{\text{ref}}}{\mathbb{E}} \text{KL} \big( p_{\text{ref}}(\cdot \mid \boldsymbol{c}) \mid\mid p_{\boldsymbol{\theta}}(\cdot \mid \boldsymbol{c}) \big)$$
(9a)

$$= \underset{\boldsymbol{c} \sim \pi_{\text{ref}}}{\mathbb{E}} \sum_{u \in \overline{\Sigma}} p_{\text{ref}}(u \mid \boldsymbol{c}) \log \frac{p_{\text{ref}}(u \mid \boldsymbol{c})}{p_{\boldsymbol{\theta}}(u \mid \boldsymbol{c})}.$$
(9b)

where  $\pi_{\text{ref}}$  is the normalized prefix probability of the reference distribution  $p_{\text{ref}}$ .

**Putting it All Together.** We now combine the reward and the KL regularization to define an objective for aligning LMs to psychometric data as

<span id="page-3-5"></span>
$$\mathcal{J}(\boldsymbol{\theta}) \stackrel{\text{def}}{=} \underbrace{\mathbf{r}(\boldsymbol{\theta})}_{\text{reward}} - \underbrace{\lambda \cdot \varphi(\boldsymbol{\theta})}_{\text{KL reg.}}, \tag{10}$$

where  $\lambda \geq 0$  is a hyperparameter, which determines the strength of the KL regularization. Because optimizing  $r(\theta)$  corresponds to optimizing  $\Delta_{\text{Ilh}}$ ,  $\mathcal{J}(\theta)$  trades off better alignment with human psychometric data against the KL divergence from the pretrained model  $p_{\text{ref}}$ .

### <span id="page-3-8"></span>3.2 Approximation of the Reward Function

In practice, we use a Monte Carlo estimate of N unit–context pairs  $(u_n, \boldsymbol{c}_n) \sim \pi_{\text{ref}}$  to approximate the expectation in Eq. (8). Let  $\psi = [\psi(u_1, \boldsymbol{c}_1), \dots, \psi(u_N, \boldsymbol{c}_N)]^{\top} \in \mathbb{R}^N$  denote the real column vector of N reading time observations. Then we define the approximate reward as

$$\widetilde{\mathbf{r}}(\boldsymbol{\theta}) \stackrel{\text{def}}{=} -\min_{\boldsymbol{\beta}_{\boldsymbol{\theta}} \in \mathbb{R}^D} \frac{1}{N} \sum_{n=1}^{N} (\psi(u_n, \boldsymbol{c}_n) - \widehat{\psi}_{\boldsymbol{\beta}_{\boldsymbol{\theta}}}(u_n, \boldsymbol{c}_n))^2$$
(11a)

$$= -\min_{\boldsymbol{\beta}_{\boldsymbol{\theta}} \in \mathbb{R}^{D}} \frac{1}{N} ||\boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}||^{2}, \tag{11b}$$

where  $\mathbf{X}_{\theta}$  is an  $N \times D$  real matrix, with each row corresponding to a predictor vector, as defined in Eq. (4). Leveraging a well-known closed-form solution (see App. A.1), we directly compute Eq. (11b). To ensure that  $\mathbf{X}_{\theta}^{\top}\mathbf{X}_{\theta}$  is invertible, we add a small regularization term  $\rho \mathbf{I}$  with  $\rho > 0$ , leading to the following coefficients

<span id="page-3-6"></span>
$$\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \left(\underbrace{\mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} + \rho \mathbf{I}}_{\text{always invertible}}\right)^{-1} \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}. \tag{12}$$

This results in the simple reward term:

<span id="page-3-7"></span>
$$\widetilde{\mathbf{r}}(\boldsymbol{\theta}) = -\frac{1}{N} ||\boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star}||^2.$$
 (13)

<span id="page-3-3"></span>Notably, the optimal coefficients are now parameterized by the language model's parameters  $\theta$ .<sup>8</sup>

# 4 Experimental Design

In this section, we discuss how we experiment with fine-tuning a language model using the objective defined in Eq. (10) and the reward approximation

<span id="page-3-0"></span><sup>&</sup>lt;sup>6</sup>We use a negative sign to ensure that maximizing the reward corresponds to minimizing the prediction error.

<span id="page-3-1"></span><sup>&</sup>lt;sup>7</sup>This is equivalent to maximum likelihood estimation. We omit  $f_{\beta_h}$  since it does not depend on  $\theta$ .

<span id="page-3-4"></span><sup>&</sup>lt;sup>8</sup>To compute the optimal coefficients  $\beta_{\theta}^{\star}$  in Eq. (12) efficiently, we use the Cholesky decomposition; see App. A.2.

<span id="page-4-0"></span>![](_page_4_Figure_0.jpeg)

Figure 1: Learning curves for the MSE (top) and  $\Delta_{\text{Ilh}}$  ( $10^{-2}$  nats, bottom) on the test datasets throughout fine-tuning. Bands show the standard error across random seeds. MSE tends to decrease, while  $\Delta_{\text{Ilh}}$  increases, showing better prediction of reading times.

given in Eq. (13). Specifically, we design experiments to evaluate the effectiveness of our objective for improving a model's psychometric accuracy, i.e., how well it predicts human reading times. Additionally, we assess the impact of our objective on a model's quality, as measured through its perplexity on test data and its performance on downstream NLP tasks.

#### 4.1 Models

We use the GPT-2 family of models (Radford et al., 2019) and conduct experiments on the small, medium, and large versions of the model available on the HuggingFace hub (Wolf et al., 2020).

### 4.2 Data

While our objective given in Eq. (10) assumes unit-context pairs sampled from  $p_{ref}$ , we lack psychometric data for LM-generated text.we take to be However, future work should investigate this assumption more thoroughly. We fine-tune and evaluate models on three widely used eye-tracking corpora: The Dundee Corpus (Kennedy et al., 2003), which includes eye-movement data from 10 English-speaking participants reading 2368 sentences of newspaper articles from *The Indepen*dent, the **Provo Corpus** (Luke and Christianson, 2018), which contains eye-tracking data from 84 participants who read 55 paragraphs of texts from various sources, including fiction and non-fiction, and the **ZuCo Corpora** (ZuCo 1.0 (Hollenstein et al., 2018) and ZuCo 2.0 (Hollenstein et al., 2020)), which contain data from 12 and 18 participants, respectively, reading sentences from Wikipedia articles and movie reviews.

Similar to previous work (Wilcox et al., 2020, 2023b), we focus on the gaze duration, defined

as the total time of a reader's first pass fixations on a unit u before they fixate on a different unit; see App. B.1 for details. In addition, we conduct experiments using the total reading duration and first fixation duration (App. D.1). We further verify that our results are not due to random effects through additional experiments with random reading times (App. D.2). We create test sets by sampling 40% of the data from each corpus. Then, to construct various test sets, we randomly sample 70% of the remaining 60% of the data according to 3 random seeds. We can view this procedure as a simple bootstrapping procedure, from which we can approximate error bars (Efron, 1979). We fine-tune and evaluate models on all pairs of eye-tracking corpora, resulting in 9 unique data splits as shown in Tab. 4.

# 4.3 Fine-Tuning

We compute the contextual surprisal of each unit in a sentence, excluding units with zero reading times and zero frequencies, during fine-tuning. It is common practice in psycholinguistics literature to drop words that were skipped on the first pass during reading and, therefore, have a first pass reading time of zero (Smith and Levy, 2013; Oh and Schuler, 2023b). Across all experiments, the predictor  $X_{\theta}$  consists of a unit's contextual surprisal, its unigram surprisal, estimated using Speer's (2022) toolkit, and its length. We opt not to include coefficients for spillover. We do so because reading times in eye-tracking studies have been observed to be less susceptible to spillover than other reading modalities, for example, self-paced reading (Shain and Schuler, 2021). Although, we acknowledge that this is a limitation of our study. For all configurations, we fine-tune models for 5k steps and repeat

| Configuration           | Train Size | Test Size |
|-------------------------|------------|-----------|
| Dundee (D) → Provo (P)  | 20894.7    | 1114      |
| Dundee (D) → Dundee (D) | 20894.7    | 20207     |
| Dundee (D) → ZuCo (Z)   | 20894.7    | 7715      |
| ZuCo (Z) → Provo (P)    | 7761       | 1114      |
| ZuCo (Z) → Dundee (D)   | 7761       | 20207     |
| ZuCo (Z) → ZuCo (Z)     | 7761       | 7715      |
| Provo (P) → Provo (P)   | 1113.7     | 1114      |
| Provo (P) → Dundee (D)  | 1113.7     | 20207     |
| Provo (P) → ZuCo (Z)    | 1113.7     | 7715      |

Table 1: Data splits and configurations for fine-tuning and evaluation. Numbers indicate the mean number of tokens in each split across our random seeds.

each run using three different random seeds. For an overview of all hyperparameters, see App. [B.3.](#page-14-2)

## 4.4 Evaluation

We evaluate the predictive power of the estimated surprisal values for predicting reading times every 50 steps using our test data splits. During each evaluation phase, we first obtain surprisal estimates on the test data from the aligned language model. Using these estimates, we perform a 5-fold crossvalidation on the test data, where we fit baseline and target linear regressors using ordinary least squares and use them to compute the unit-level mean ∆llh.

# 5 Results

We now return to our main question: Does our objective align language models more closely to human reading times compared to pretrained models? We first analyze the effect of maximizing the unregularized reward and later, in [§5.4,](#page-6-0) extend our analysis to the KL-regularized objective.

## <span id="page-5-1"></span>5.1 Predicting Reading Times

Are fine-tuned models p<sup>θ</sup> better predictors of reading times compared to pretrained models pref? To answer this question, we examine both the mean square error (MSE) and the delta log-likelihood ∆llh computed at each evaluation step on the test data using cross-validation. While the ∆llh is our main metric for measuring a model's psychometric accuracy, we use the MSE to compare the magnitude of prediction errors. The MSE is computed similarly to the unregularized objective, given in Eq. [\(10\)](#page-3-5), except we calculate the MSE through cross-validation on the entire test set using linear regression to evaluate the predictive power of surprisal estimates.

As visualized in Fig. [1,](#page-4-0) the MSE values are relatively high because our reading times are in mil-

<span id="page-5-0"></span>

| Model | GPT2-L | GPT2-M | GPT2-S |
|-------|--------|--------|--------|
| D → D | 55.291 | 32.822 | 42.880 |
| P → D | 23.294 | 24.233 | 29.898 |
| Z → D | 9.084  | 11.077 | 16.598 |
| D → P | 31.356 | 4.928  | 17.780 |
| P → P | 45.273 | 15.621 | 24.769 |
| Z → P | 2.116  | 6.460  | 1.999  |
| D → Z | 36.577 | 11.950 | 24.502 |
| P → Z | 15.012 | 5.730  | 20.094 |
| Z → Z | 81.390 | 41.801 | 61.196 |

Table 2: Percentage increase between the initial and maximum ∆llh for each model. For exact start and maximum ∆llh values, see Tab. [7.](#page-16-0)

liseconds; an MSE of 4,000 corresponds to a prediction that is off by only about 1/20th of a second. We observe that the MSE decreases for all models across all held-out datasets over the course of fine-tuning. An exception to this is the MSE for the data splits Dundee → Provo and ZuCo → Provo, where we do not observe consistent decreases in MSE, potentially due to the small size of the test set. Models evaluated on the ZuCo dataset have the lowest MSE, followed by Provo and Dundee. Further, in Fig. [1,](#page-4-0) we visualize the ∆llh of regressors evaluated on our test dataset over the course of fine-tuning. In line with our observed decreases in MSE, we find that ∆llh increases on most data splits, with the exception of models fine-tuned on Dundee or ZuCo and evaluated on Provo. Smaller models start with higher ∆llh, which is consistent with previous literature [\(Oh and Schuler,](#page-11-12) [2023b\)](#page-11-12). In Tab. [2,](#page-5-0) we compare the percentage increase from each model's start ∆llh to the maximum ∆llh it achieves over the course of the fine-tuning, averaged over three random seeds. Interestingly, GPT2-S shows higher percentage increases compared to GPT2-M, suggesting that model size alone does not fully account for these differences.

## 5.2 Coefficient Estimates

Additionally, we want to know what the fine-tuned models have implicitly learned about the role of surprisal, as well as the baseline features, over the course of fine-tuning. To examine this, in Fig. [3,](#page-6-1) we visualize the regressor coefficients β<sup>θ</sup> from cross-validation on the whole test set. We observe the following tendencies: The coefficients for a unit's contextual surprisal and length are positive, indicating that, as units become less predictable and longer, they take more time to read.

The positive coefficient for unigram surprisal means more frequent units take less time to read.

<span id="page-6-2"></span>![](_page_6_Figure_0.jpeg)

Figure 2: **Perplexity vs.**  $\Delta_{\text{Ilh}}$ . We compare model perplexity at the start of fine-tuning to the point where they achieve the highest mean  $\Delta_{\text{Ilh}}$ . Optimizing models using  $\mathcal J$  increases perplexity. See Fig. 6 for all data splits.

These results align with the previous literature, e.g., those from Wilcox et al., 2023b. Interestingly, we observe that over the course of fine-tuning, the coefficient for surprisal tends to *increase*, while the coefficient for length *decreases*. For unigram surprisal and our bias term, i.e., the intercept of the regression, we observe mixed results, with coefficients for unigram surprisal decreasing for models evaluated on the Dundee and ZuCo datasets and increasing for models evaluated on Provo. Overall, the coefficient's trajectories suggest that the predictive power of surprisal for predicting reading times increases throughout fine-tuning. For coefficients across data splits, as well as coefficients for the regularized objective, see App. E.

#### **5.3** Perplexity vs. Quality

Several recent papers have found that, above a certain size, as a language model's perplexity decreases, its predictive power increases (Oh et al., 2022; Shain et al., 2024). Follow-up work has suggested that this is due to the super-human predictive abilities of the models, especially for lowfrequency nouns such as named entities (Oh and Schuler, 2023b). An open question remains regarding the causal factors behind these dynamics. So far, studies have tested the relationship by manipulating a language model's quality either by choosing different sizes of pretrained models as in Oh and Schuler (2023b) or by training successively smaller and smaller models as in Wilcox et al. (2023a). However, our fine-tuning methods allow us to flip the causal arrow. As we make a language model more closely aligned with human reading times, what happens to its quality? To investigate this question, in Fig. 2, we show the perplexity and  $\Delta_{\rm llh}$  both at the start of fine-tuning and when the model achieves its maximum  $\Delta_{llh}$ , which is typi-

<span id="page-6-1"></span>![](_page_6_Figure_5.jpeg)

Figure 3: **Mean Coefficients of unit-level features over fine-tuning.** Smoothed values (window size 5) are shown, with unsmoothed values in a pale version of the color. Coefficients corresponding to surprisal tend to increase over the course of fine-tuning.

cally near the end of fine-tuning. We find that increases in  $\Delta_{\text{llh}}$  generally correspond to increases in perplexity. These results indicate that as we make a language model's predictions more aligned with reading times, it becomes worse at modeling text.

# <span id="page-6-0"></span>5.4 Kullback-Leibler Regularization

Next, we analyze the effect of adding KL regularization to our objective in Eq. (10). Specifically, we compare the trajectories of  $\Delta_{\text{llh}}$ , KL divergence and log perplexity for KL coefficients  $\lambda \in$  $\{0, 5, 50, 500\}$ . The coefficients used in this paper are larger than the ones normally used in RLHF studies (Schulman et al., 2017; Ziegler et al., 2020; Stiennon et al., 2020; Ouyang et al., 2022) because of the large magnitude of our reward in Eq. (13), which is the negative mean squared error. Fig. 4 shows a clear trend: Higher coefficients lead to lower increases in perplexity and KL divergence, as well as lower increases in  $\Delta_{llh}$ . We observe higher coefficients reduce the divergence of  $p_{\theta}$  from their initial distribution  $p_{ref}$ . While higher coefficient come at the cost of lower  $\Delta_{llh}$  increases, we still observe consistent increases over the baseline; see Fig. 9 for results on all data splits with  $\lambda = 500$ .

### 6 Additional Analyses

Previous work has found that language models fine-tuned on cognitive data, such as eye tracking (Yang and Hollenstein, 2023; Deng et al., 2023) and brain data (Toneva and Wehbe, 2019) can improve performance on downstream NLP tasks. In this section, we evaluate our fine-tuned language models—based on the lowest loss on the test dataset—on sev-

<span id="page-7-0"></span>![](_page_7_Figure_0.jpeg)

Figure 4: Trajectories of  $\Delta_{\rm llh}$ , KL divergence and log perplexity for KL coefficients  $\lambda \in \{0, 5, 50, 500\}$ . Higher coefficients lead to lower perplexity increases as well as lower  $\Delta_{\rm llh}$  increases, showing that the KL regularization constrains  $p_{\theta}$  from diverging too much from  $p_{\rm ref}$ .

eral such tasks. We observe no such improvement.

#### 6.1 Targeted Syntactic Evaluation

We evaluate models on the Benchmark of Linguistically Minimal Pairs (BLiMP; Warstadt et al., 2020). BLiMP assesses whether language models' behavior is consistent with human preferences for grammatical sentences across a range of grammatical phenomena. In BLiMP, items come in grammatical and ungrammatical variants; we report model accuracy for assigning a higher probability to the grammatical version. Models' scores on BLiMP are visualized in Fig. 5. Even though KL regularization helps mitigate the drop in accuracy, we observe that our fine-tuned models generally exhibit slightly lower accuracy than their non-finetuned counterparts, indicating that our fine-tuning procedure does not lead to a better generalization about English grammatical rules in our models.

#### <span id="page-7-2"></span>**6.2** Text Generation

Additionally, we analyze how our objective affects the ability of fine-tuned models to generate text and focus on two aspects: the uniformity of information and the diversity of the generations. To assess uniformity, we draw on the uniform information density (UID) hypothesis (Fenk and Fenk, 1980; Levy and Jaeger, 2006), which posits that language users prefer information to be evenly distributed throughout an utterance. A recent study by Meister et al. (2021) provides empirical support for the UID hypothesis in naturally occurring corpora and shows a link between linguistic acceptability and information uniformity. Here, we ask whether aligning models to human reading

times encourages them to generate text with greater uniformity of information.

We test this by generating completions for prefixes from the CNN/DailyMail dataset (Hermann et al., 2015; See et al., 2017). In Tab. 3, we report the mean surprisal variance  $(UID_v)$  and unique unigram ratio (1-Gram%) across all completions; see App. F for more details. Models without regularization ( $\lambda = 0$ ) show higher surprisal variance compared to the pretrained models, indicating less uniformly distributed information in the generations. However, under regularization ( $\lambda = 500$ ), this trend is reversed, and we observe lower variance with the exception of GPT2-L: Dundee → Dundee. We further observe a decrease in the unique unigram ratio, indicating that fine-tuned models generate more repetitive text. Overall, these findings suggest that aligning models to human reading times might promote a more uniform information distribution, though further research is needed to explore the connection between the UID hypothesis and alignment with reading times.

#### 7 Discussion

We now discuss the broader implications of our results with respect to both cognitive modeling and natural language processing. One recurring theme in this paper is the relationship between  $p_{\theta}$ , a probability distribution over strings estimated from large corpora, and  $p_{\rm H}$ , the distribution implicated during cognitive tasks. In terms of cognitive modeling, it is widely accepted that it is useful to obtain a  $p_{\theta}$  that is as close as possible to  $p_{\rm H}$  in order to test and refine psychological theories. While previous work has proposed alignment procedures between LMs and brain data (Toneva and Wehbe, 2019),

<span id="page-7-1"></span><sup>&</sup>lt;sup>9</sup>We use the LM Evaluation Harness (Gao et al., 2024).

<span id="page-8-0"></span>![](_page_8_Figure_0.jpeg)

Figure 5: **Results for BLiMP.** Non-fine-tuned models are shown with hatching. Error bars are standard errors across random seeds. Fine-tuning leads to a decrease in accuracy. For results on all data splits, see Fig. 7.

within the realm of psycholinguistics, researchers have generally opted for whatever model is the current state of the art. Only recently have contributions started to search for which combinations of training data, model size, and model architecture produce the best cognitive alignment (Oh and Schuler, 2023a; Steuer et al., 2023). Our results suggest an alternative to this search by directly aligning language models to psychometric data. We are optimistic that such aligned models will enable a more precise evaluation of psycholinguistic theories. Of course, it remains an open question to what extent alignment on reading generalizes to other cognitive tasks. We have discussed  $p_{\rm H}$  in terms of a single hypothesized construct, but it is likely that people's predictions change with task demands, e.g., when skimming versus proofreading a text. Testing whether our results hold for other types of psychometric predictive tasks is an important question for future research.

The main technical contribution of this work is a technique that aligns language models more closely to human psychometric data. Inspired by the implicit parameter optimization in DPO, our approach goes beyond the original Bradley-Terry assumption and demonstrates that it is possible to fine-tune under other implicit statistical models. Exploring a wider range of such models goes hand in hand with exploring new sources of human psychometric data, as we have done here with reading times. Psychologists have devised methods for collecting a diverse array of cognitive signals, including EEG, fMRI, mouse-tracking, and self-paced reading, to name a few. Aligning models, using the method proposed here, on such data or combinations thereof, will be an important next step in this research.

Finally, what do our results say about the relationship between cognitive modeling and other domains in NLP? At first glance, they seem to

<span id="page-8-1"></span>

| Model                               | λ                           | $\lambda = 0$   |                           | $\lambda = 500$ |  |
|-------------------------------------|-----------------------------|-----------------|---------------------------|-----------------|--|
|                                     | $\downarrow \mathrm{UID}_v$ | ↑ 1-Gram%       | $\downarrow \text{UID}_v$ | ↑1-Gram%        |  |
| GPT2-L                              | 6.69                        | 84.84           | 6.69                      | 84.84           |  |
| $\mathrm{D} \to \mathrm{D}$         | $10.17_{2.93}$              | $67.07_{14.68}$ | $8.05_{0.77}$             | $82.38_{0.18}$  |  |
| $\mathrm{P} \rightarrow \mathrm{P}$ | $11.27_{1.74}$              | $68.91_{1.76}$  | $5.14_{0.35}$             | $76.75_{0.79}$  |  |
| $Z {\to} Z$                         | $13.85_{0.98}$              | $84.60_{1.91}$  | $5.61_{0.09}$             | $81.12_{0.20}$  |  |
| GPT2-M                              | 7.67                        | 84.39           | 7.67                      | 84.39           |  |
| $\mathrm{D} \to \mathrm{D}$         | $8.94_{0.25}$               | $80.82_{0.35}$  | $6.63_{0.35}$             | $83.22_{1.08}$  |  |
| $\mathrm{P} \rightarrow \mathrm{P}$ | $7.81_{0.46}$               | $67.51_{0.78}$  | $4.54_{0.17}$             | $75.91_{0.85}$  |  |
| $Z {\to} Z$                         | $12.12_{1.42}$              | $84.95_{0.86}$  | $5.88_{0.05}$             | $81.94_{0.91}$  |  |
| GPT2-S                              | 5.70                        | 82.53           | 5.70                      | 82.53           |  |
| $\mathrm{D}\to\mathrm{D}$           | $6.27_{0.52}$               | $81.14_{0.95}$  | $4.50_{0.11}$             | $76.56_{2.02}$  |  |
| $\mathrm{P} \rightarrow \mathrm{P}$ | $6.91_{0.25}$               | $72.17_{1.99}$  | $4.11_{0.10}$             | $69.54_{0.43}$  |  |
| $Z \to Z$                           | $7.79_{1.02}$               | $79.61_{1.94}$  | $4.97_{0.18}$             | $75.92_{0.68}$  |  |

Table 3: Surprisal variance (UID $_v$ ), and unique unigram ratios (1-Gram%) of model generated completions. See Tab. 11 for results on all data splits.

suggest that alignment with reading times is not an effective strategy to broadly boost performance on NLP tasks. Although KL regularization reduces the increase of the language model's perplexity on heldout data, we still observe decreased performance on downstream NLP tasks. However, given the lack of reading time data for LM-generated text, we relied on pre-existing eye-tracking datasets. Future studies could experiment with text generated by language models, particularly as new eye-tracking datasets for LM-generated text are being developed (Bolliger et al., 2024). Furthermore, Rafailov et al. (2023) derive the optimal solution to the KL regularized RL objective in DPO, while our study excluded the KL term when deriving optimal coefficients. Future work could investigate approaches closer to DPO to compute the optimal coefficients.

# 8 Conclusion

We have presented a novel technique to align language models with human reading data by implicitly optimizing the parameters of a linear regression model. Our experiments on held-out test sets show our method reliably improves the predictive power of language models with various parameter counts on human reading times. Furthermore, our findings confirm previous research on the inverse relationship between perplexity and psychometric predictive power. We believe our results pave the way for better assessment of psychological theories using more cognitively aligned language models.

#### Limitations

Our study has several limitations. First, we only include predictors for the current unit. Future

research could explore the impact of adding previous units' predictors as well as additional predictors, such as contextual entropy, as suggested in [Pimentel et al.](#page-11-10) [\(2023\)](#page-11-10), to the objective. Second, our study only tests and evaluates English language data. Expanding these studies to a wider variety of languages is an important next step in establishing the generalizability of our methods. Third, we estimate surprisal based on individual sentences, whereas surprisal estimated for whole paragraphs may yield more accurate estimates due to the additional context.

# Ethics Statement

Our study introduces a technique for aligning language models to human psychometric data. When working with human psychometric data, specifically eye-tracking data, it is important to consider potential privacy risks [\(Jäger et al.,](#page-10-18) [2020;](#page-10-18) [Lohr and](#page-10-19) [Komogortsev,](#page-10-19) [2022\)](#page-10-19). In this study, we used wellestablished datasets [\(Kennedy et al.,](#page-10-12) [2003;](#page-10-12) [Luke](#page-10-13) [and Christianson,](#page-10-13) [2018;](#page-10-13) [Hollenstein et al.,](#page-10-14) [2018,](#page-10-14) [2020\)](#page-10-15), where personal identifying information had been anonymized prior to our access. Additionally, we are aware of the potential biases inherent in language models and human reading data. Our goal is to ensure that our models and evaluations do not propagate or amplify existing biases.

# Acknowledgments

We would like to thank the ARR reviewers and area chair for their valuable feedback and comments. Afra Amini is supported by ETH AI Center doctoral fellowship. David Robert Reich is supported by the Swiss National Science Foundation (SNSF) under grant IZCOZ0\_220330/1 (EyeNLG).

# References

- <span id="page-9-3"></span>David A. Balota, Alexander Pollatsek, and Keith Rayner. 1985. [The interaction of contextual constraints and](https://doi.org/10.1016/0010-0285(85)90013-1) [parafoveal visual information in reading.](https://doi.org/10.1016/0010-0285(85)90013-1) *Cognitive Psychology*, 17(3).
- <span id="page-9-13"></span>Stella Biderman, Hailey Schoelkopf, Quentin Gregory Anthony, Herbie Bradley, Kyle O'Brien, Eric Hallahan, Mohammad Aflah Khan, Shivanshu Purohit, Usvsn Sai Prashanth, Edward Raff, Aviya Skowron, Lintang Sutawika, and Oskar Van Der Wal. 2023. [Pythia: A suite for analyzing large language models](https://proceedings.mlr.press/v202/biderman23a.html) [across training and scaling.](https://proceedings.mlr.press/v202/biderman23a.html) In *Proceedings of the 40th International Conference on Machine Learning*, volume 202 of *Proceedings of Machine Learning Research*. PMLR.

- <span id="page-9-12"></span>Lena Sophia Bolliger, Patrick Haller, Isabelle Caroline Rose Cretton, David Robert Reich, Tannon Kew, and Lena Ann Jäger. 2024. [Emtec: A corpus of eye](https://arxiv.org/abs/2408.04289) [movements on machine-generated texts.](https://arxiv.org/abs/2408.04289) *Preprint*, arXiv:2408.04289.
- <span id="page-9-7"></span>Ralph Allan Bradley and Milton E. Terry. 1952. [Rank](http://www.jstor.org/stable/2334029) [analysis of incomplete block designs: I. the method](http://www.jstor.org/stable/2334029) [of paired comparisons.](http://www.jstor.org/stable/2334029) *Biometrika*, 39(3/4).
- <span id="page-9-4"></span>Paul F. Christiano, Jan Leike, Tom Brown, Miljan Martic, Shane Legg, and Dario Amodei. 2017. [Deep](https://proceedings.neurips.cc/paper_files/paper/2017/file/d5e2c0adad503c91f91df240d0cd4e49-Paper.pdf) [reinforcement learning from human preferences.](https://proceedings.neurips.cc/paper_files/paper/2017/file/d5e2c0adad503c91f91df240d0cd4e49-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 30.
- <span id="page-9-14"></span>Thomas Hikaru Clark, Clara Meister, Tiago Pimentel, Michael Hahn, Ryan Cotterell, Richard Futrell, and Roger Levy. 2023. [A cross-linguistic pressure for](https://doi.org/10.1162/tacl_a_00589) [Uniform Information Density in word order.](https://doi.org/10.1162/tacl_a_00589) *Transactions of the Association for Computational Linguistics*, 11.
- <span id="page-9-2"></span>Katherine A. DeLong, Thomas P. Urbach, and Marta Kutas. 2005. [Probabilistic word pre-activation dur](https://www.nature.com/articles/nn1504)[ing language comprehension inferred from electrical](https://www.nature.com/articles/nn1504) [brain activity.](https://www.nature.com/articles/nn1504) *Nature Neuroscience*, 8.
- <span id="page-9-9"></span>Shuwen Deng, Paul Prasse, David Reich, Tobias Scheffer, and Lena Jäger. 2023. [Pre-trained language mod](https://aclanthology.org/2023.emnlp-main.400)[els augmented with synthetic scanpaths for natural](https://aclanthology.org/2023.emnlp-main.400) [language understanding.](https://aclanthology.org/2023.emnlp-main.400) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, Singapore. Association for Computational Linguistics.
- <span id="page-9-8"></span>B. Efron. 1979. [Bootstrap Methods: Another Look at](https://doi.org/10.1214/aos/1176344552) [the Jackknife.](https://doi.org/10.1214/aos/1176344552) *The Annals of Statistics*, 7(1).
- <span id="page-9-1"></span>Susan F. Ehrlich and Keith Rayner. 1981. [Contextual](https://doi.org/10.1016/S0022-5371(81)90220-6) [effects on word perception and eye movements dur](https://doi.org/10.1016/S0022-5371(81)90220-6)[ing reading.](https://doi.org/10.1016/S0022-5371(81)90220-6) *Journal of Verbal Learning and Verbal Behavior*, 20(6).
- <span id="page-9-10"></span>August Fenk and Gertraud Fenk. 1980. [Konstanz im](https://pubmed.ncbi.nlm.nih.gov/7434825/) [Kurzzeitgedächtnis - Konstanz im sprachlichen In](https://pubmed.ncbi.nlm.nih.gov/7434825/)[formationsfluß?](https://pubmed.ncbi.nlm.nih.gov/7434825/) *Zeitschrift für experimentelle und angewandte Psychologie*, 27(3).
- <span id="page-9-0"></span>Ira Fischler and Paul A. Bloom. 1979. [Automatic and at](https://doi.org/10.1016/S0022-5371(79)90534-6)[tentional processes in the effects of sentence contexts](https://doi.org/10.1016/S0022-5371(79)90534-6) [on word recognition.](https://doi.org/10.1016/S0022-5371(79)90534-6) *Journal of Verbal Learning and Verbal Behavior*, 18(1).
- <span id="page-9-6"></span>Stefan L. Frank and Rens Bod. 2011. [Insensitivity of the](https://doi.org/10.1177/0956797611409589) [human sentence-processing system to hierarchical](https://doi.org/10.1177/0956797611409589) [structure.](https://doi.org/10.1177/0956797611409589) *Psychological Science*, 22(6).
- <span id="page-9-5"></span>Lyn Frazier and Keith Rayner. 1982. [Making and cor](https://doi.org/10.1016/0010-0285(82)90008-1)[recting errors during sentence comprehension: Eye](https://doi.org/10.1016/0010-0285(82)90008-1) [movements in the analysis of structurally ambiguous](https://doi.org/10.1016/0010-0285(82)90008-1) [sentences.](https://doi.org/10.1016/0010-0285(82)90008-1) *Cognitive Psychology*, 14(2).
- <span id="page-9-11"></span>Leo Gao, Jonathan Tow, Baber Abbasi, Stella Biderman, Sid Black, Anthony DiPofi, Charles Foster, Laurence Golding, Jeffrey Hsu, Alain Le Noac'h, Haonan Li,

- Kyle McDonell, Niklas Muennighoff, Chris Ociepa, Jason Phang, Laria Reynolds, Hailey Schoelkopf, Aviya Skowron, Lintang Sutawika, Eric Tang, Anish Thite, Ben Wang, Kevin Wang, and Andy Zou. 2024. [A framework for few-shot language model](https://zenodo.org/records/12608602) [evaluation.](https://zenodo.org/records/12608602)
- <span id="page-10-23"></span>Mario Giulianelli, Luca Malagutti, Juan Luis Gastaldi, Brian DuSell, Tim Vieira, and Ryan Cotterell. 2024. [On the proper treatment of tokenization in psycholin](https://arxiv.org/abs/2410.02691)[guistics.](https://arxiv.org/abs/2410.02691) *Preprint*, arXiv:2410.02691.
- <span id="page-10-6"></span>Adam Goodkind and Klinton Bicknell. 2018. [Predic](https://doi.org/10.18653/v1/W18-0102)[tive power of word surprisal for reading times is a](https://doi.org/10.18653/v1/W18-0102) [linear function of language model quality.](https://doi.org/10.18653/v1/W18-0102) In *Proceedings of the 8th Workshop on Cognitive Modeling and Computational Linguistics*, Salt Lake City, Utah. Association for Computational Linguistics.
- <span id="page-10-4"></span>John Hale. 2001. [A probabilistic Earley parser as a psy](https://aclanthology.org/N01-1021)[cholinguistic model.](https://aclanthology.org/N01-1021) In *Second Meeting of the North American Chapter of the Association for Computational Linguistics*.
- <span id="page-10-17"></span>Karl Moritz Hermann, Tomas Kocisky, Edward Grefenstette, Lasse Espeholt, Will Kay, Mustafa Suleyman, and Phil Blunsom. 2015. [Teaching machines to read](https://proceedings.neurips.cc/paper_files/paper/2015/file/afdec7005cc9f14302cd0474fd0f3c96-Paper.pdf) [and comprehend.](https://proceedings.neurips.cc/paper_files/paper/2015/file/afdec7005cc9f14302cd0474fd0f3c96-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 28.
- <span id="page-10-20"></span>Arthur E. Hoerl and Robert W. Kennard. 1970. [Ridge re](http://www.jstor.org/stable/1267351)[gression: Biased estimation for nonorthogonal prob](http://www.jstor.org/stable/1267351)[lems.](http://www.jstor.org/stable/1267351) *Technometrics*, 12(1).
- <span id="page-10-21"></span>Nora Hollenstein, Federico Pirovano, Ce Zhang, Lena Jäger, and Lisa Beinborn. 2021. [Multilingual lan](https://doi.org/10.18653/v1/2021.naacl-main.10)[guage models predict human reading behavior.](https://doi.org/10.18653/v1/2021.naacl-main.10) In *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, Online. Association for Computational Linguistics.
- <span id="page-10-14"></span>Nora Hollenstein, Jonathan Rotsztejn, Marius Troendle, Andreas Pedroni, Ce Zhang, and Nicolas Langer. 2018. [ZuCo, a simultaneous EEG and eye-tracking](https://doi.org/10.1038/sdata.2018.291) [resource for natural sentence reading.](https://doi.org/10.1038/sdata.2018.291) *Scientific Data*, 5.
- <span id="page-10-15"></span>Nora Hollenstein, Marius Troendle, Ce Zhang, and Nicolas Langer. 2020. [ZuCo 2.0: A dataset of phys](https://aclanthology.org/2020.lrec-1.18)[iological recordings during natural reading and an](https://aclanthology.org/2020.lrec-1.18)[notation.](https://aclanthology.org/2020.lrec-1.18) In *Proceedings of the Twelfth Language Resources and Evaluation Conference*, Marseille, France. European Language Resources Association.
- <span id="page-10-11"></span>Jacob Louis Hoover, Morgan Sonderegger, Steven T. Piantadosi, and Timothy J. O'Donnell. 2023. [The](https://doi.org/10.1162/opmi_a_00086) [Plausibility of Sampling as an Algorithmic Theory](https://doi.org/10.1162/opmi_a_00086) [of Sentence Processing.](https://doi.org/10.1162/opmi_a_00086) *Open Mind*, 7.
- <span id="page-10-18"></span>Lena A. Jäger, Silvia Makowski, Paul Prasse, Sascha Liehr, Maximilian Seidler, and Tobias Scheffer. 2020. [Deep Eyedentification: biometric identification using](https://link.springer.com/chapter/10.1007/978-3-030-46147-8_18) [micro-movements of the eye.](https://link.springer.com/chapter/10.1007/978-3-030-46147-8_18) In *Machine Learning and Knowledge Discovery in Databases*, Cham. Springer International Publishing.

- <span id="page-10-8"></span>Marcel A. Just and Patricia A. Carpenter. 1980. [A the](https://doi.org/10.1037/0033-295x.87.4.329)[ory of reading: From eye fixations to comprehension.](https://doi.org/10.1037/0033-295x.87.4.329) *Psychological Review*, 87(4).
- <span id="page-10-12"></span>Alan Kennedy, Robin Hill, and Joël Pynte. 2003. The Dundee corpus. In *In Proceedings of the 12th European Conference on Eye Movement*.
- <span id="page-10-2"></span>Gina R. Kuperberg and T. Florian Jaeger. 2016. [What do](https://doi.org/10.1080/23273798.2015.1102299) [we mean by prediction in language comprehension?](https://doi.org/10.1080/23273798.2015.1102299) *Language, Cognition and Neuroscience*, 31(1).
- <span id="page-10-9"></span>Tatsuki Kuribayashi, Yohei Oseki, Takumi Ito, Ryo Yoshida, Masayuki Asahara, and Kentaro Inui. 2021. [Lower perplexity is not always human-like.](https://doi.org/10.18653/v1/2021.acl-long.405) In *Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 1: Long Papers)*, Online. Association for Computational Linguistics.
- <span id="page-10-1"></span>Marta Kutas and Steven A. Hillyard. 1984. [Brain po](https://www.nature.com/articles/307161a0)[tentials during reading reflect word expectancy and](https://www.nature.com/articles/307161a0) [semantic association.](https://www.nature.com/articles/307161a0) *Nature*, 307.
- <span id="page-10-5"></span>Roger Levy. 2008. [Expectation-based syntactic compre](https://doi.org/10.1016/j.cognition.2007.05.006)[hension.](https://doi.org/10.1016/j.cognition.2007.05.006) *Cognition*, 106(3).
- <span id="page-10-16"></span>Roger Levy and T. Florian Jaeger. 2006. [Speakers opti](https://proceedings.neurips.cc/paper_files/paper/2006/file/c6a01432c8138d46ba39957a8250e027-Paper.pdf)[mize information density through syntactic reduction.](https://proceedings.neurips.cc/paper_files/paper/2006/file/c6a01432c8138d46ba39957a8250e027-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 19, Cambridge, MA, USA. MIT Press.
- <span id="page-10-7"></span>Xiaochen Li, Zheng-Xin Yong, and Stephen H. Bach. 2024. [Preference tuning for toxicity mitigation gener](https://arxiv.org/abs/2406.16235)[alizes across languages.](https://arxiv.org/abs/2406.16235) *Preprint*, arXiv:2406.16235.
- <span id="page-10-19"></span>Dillon Lohr and Oleg V. Komogortsev. 2022. [Eye know](https://doi.org/10.1109/TIFS.2022.3201369) [you too: Toward viable end-to-end eye movement](https://doi.org/10.1109/TIFS.2022.3201369) [biometrics for user authentication.](https://doi.org/10.1109/TIFS.2022.3201369) *IEEE Transactions on Information Forensics and Security*, 17.
- <span id="page-10-22"></span>Ilya Loshchilov and Frank Hutter. 2017. [SGDR:](https://openreview.net/forum?id=Skq89Scxx) [Stochastic gradient descent with warm restarts.](https://openreview.net/forum?id=Skq89Scxx) In *International Conference on Learning Representations*.
- <span id="page-10-13"></span>Steven G. Luke and Kiel Christianson. 2018. [The provo](https://link.springer.com/article/10.3758/s13428-017-0908-4) [corpus: A large eye-tracking corpus with predictabil](https://link.springer.com/article/10.3758/s13428-017-0908-4)[ity norms.](https://link.springer.com/article/10.3758/s13428-017-0908-4) *Behavior Research Methods*, 50.
- <span id="page-10-10"></span>Clara Meister, Tiago Pimentel, Patrick Haller, Lena Jäger, Ryan Cotterell, and Roger Levy. 2021. [Revis](https://arxiv.org/abs/2109.11635)[iting the uniform information density hypothesis.](https://arxiv.org/abs/2109.11635) In *Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing*, Online. Association for Computational Linguistics.
- <span id="page-10-3"></span>George A. Miller and Kathryn Ojemann McKean. 1964. [A chronometric study of some relations between sen](https://doi.org/10.1080/17470216408416385)[tences.](https://doi.org/10.1080/17470216408416385) *Quarterly Journal of Experimental Psychology*, 16(4).
- <span id="page-10-0"></span>Byung-Doh Oh, Christian Clark, and William Schuler. 2022. [Comparison of structural parsers and neural](https://doi.org/10.3389/frai.2022.777963) [language models as surprisal estimators.](https://doi.org/10.3389/frai.2022.777963) *Frontiers in Artificial Intelligence*, 5.

- <span id="page-11-18"></span>Byung-Doh Oh and William Schuler. 2023a. [Transformer-based language model surprisal](https://doi.org/10.18653/v1/2023.findings-emnlp.128) [predicts human reading times best with about](https://doi.org/10.18653/v1/2023.findings-emnlp.128) [two billion training tokens.](https://doi.org/10.18653/v1/2023.findings-emnlp.128) In *Findings of the Association for Computational Linguistics: EMNLP 2023*, Singapore. Association for Computational Linguistics.
- <span id="page-11-12"></span>Byung-Doh Oh and William Schuler. 2023b. [Why](https://doi.org/10.1162/tacl_a_00548) [does surprisal from larger transformer-based lan](https://doi.org/10.1162/tacl_a_00548)[guage models provide a poorer fit to human reading](https://doi.org/10.1162/tacl_a_00548) [times?](https://doi.org/10.1162/tacl_a_00548) *Transactions of the Association for Computational Linguistics*, 11.
- <span id="page-11-22"></span>Byung-Doh Oh and William Schuler. 2024. [Leading](https://arxiv.org/abs/2406.10851) [whitespaces of language models' subword vocabulary](https://arxiv.org/abs/2406.10851) [poses a confound for calculating word probabilities.](https://arxiv.org/abs/2406.10851) *Preprint*, arXiv:2406.10851.
- <span id="page-11-8"></span>Andreas Opedal, Eleanor Chodroff, Ryan Cotterell, and Ethan Gotlieb Wilcox. 2024. [On the role of context in](https://arxiv.org/abs/2409.08160) [reading time prediction.](https://arxiv.org/abs/2409.08160) *Preprint*, arXiv:2409.08160.
- <span id="page-11-4"></span>Long Ouyang, Jeffrey Wu, Xu Jiang, Diogo Almeida, Carroll Wainwright, Pamela Mishkin, Chong Zhang, Sandhini Agarwal, Katarina Slama, Alex Ray, John Schulman, Jacob Hilton, Fraser Kelton, Luke Miller, Maddie Simens, Amanda Askell, Peter Welinder, Paul F. Christiano, Jan Leike, and Ryan Lowe. 2022. [Training language models to follow instructions with](https://proceedings.neurips.cc/paper_files/paper/2022/file/b1efde53be364a73914f58805a001731-Paper-Conference.pdf) [human feedback.](https://proceedings.neurips.cc/paper_files/paper/2022/file/b1efde53be364a73914f58805a001731-Paper-Conference.pdf) In *Advances in Neural Information Processing Systems*, volume 35.
- <span id="page-11-20"></span>Denis Paperno, Germán Kruszewski, Angeliki Lazaridou, Ngoc Quan Pham, Raffaella Bernardi, Sandro Pezzelle, Marco Baroni, Gemma Boleda, and Raquel Fernández. 2016. [The LAMBADA dataset: Word](https://doi.org/10.18653/v1/P16-1144) [prediction requiring a broad discourse context.](https://doi.org/10.18653/v1/P16-1144) In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, Berlin, Germany. Association for Computational Linguistics.
- <span id="page-11-21"></span>Tiago Pimentel and Clara Meister. 2024. [How to](https://arxiv.org/abs/2406.14561) [compute the probability of a word.](https://arxiv.org/abs/2406.14561) *Preprint*, arXiv:2406.14561.
- <span id="page-11-10"></span>Tiago Pimentel, Clara Meister, Ethan G. Wilcox, Roger P. Levy, and Ryan Cotterell. 2023. [On the Ef](https://doi.org/10.1162/tacl_a_00603)[fect of Anticipation on Reading Times.](https://doi.org/10.1162/tacl_a_00603) *Transactions of the Association for Computational Linguistics*, 11.
- <span id="page-11-11"></span>Alec Radford, Jeff Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. 2019. [Language](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) [models are unsupervised multitask learners.](https://cdn.openai.com/better-language-models/language_models_are_unsupervised_multitask_learners.pdf) *OpenAI blog*, 1(8).
- <span id="page-11-5"></span>Rafael Rafailov, Archit Sharma, Eric Mitchell, Christopher D Manning, Stefano Ermon, and Chelsea Finn. 2023. [Direct preference optimization: Your language](https://proceedings.neurips.cc/paper_files/paper/2023/file/a85b405ed65c6477a4fe8302b5e06ce7-Paper-Conference.pdf) [model is secretly a reward model.](https://proceedings.neurips.cc/paper_files/paper/2023/file/a85b405ed65c6477a4fe8302b5e06ce7-Paper-Conference.pdf) In *Advances in Neural Information Processing Systems*, volume 36.
- <span id="page-11-9"></span>Keith Rayner. 1998. [Eye movements in reading and](https://doi.org/10.1037/0033-2909.124.3.372) [information processing: 20 years of research.](https://doi.org/10.1037/0033-2909.124.3.372) *Psychological Bulletin*, 124(3).

- <span id="page-11-3"></span>John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, and Oleg Klimov. 2017. [Prox](https://arxiv.org/abs/1707.06347)[imal policy optimization algorithms.](https://arxiv.org/abs/1707.06347) *Preprint*, arXiv:1707.06347.
- <span id="page-11-17"></span>Abigail See, Peter J. Liu, and Christopher D. Manning. 2017. [Get to the point: Summarization with pointer](https://doi.org/10.18653/v1/P17-1099)[generator networks.](https://doi.org/10.18653/v1/P17-1099) In *Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, Vancouver, Canada. Association for Computational Linguistics.
- <span id="page-11-0"></span>Cory Shain, Clara Meister, Tiago Pimentel, Ryan Cotterell, and Roger Levy. 2024. [Large-scale evidence](https://doi.org/10.1073/pnas.2307876121) [for logarithmic effects of word predictability on read](https://doi.org/10.1073/pnas.2307876121)[ing time.](https://doi.org/10.1073/pnas.2307876121) *Proceedings of the National Academy of Sciences*, 121(10).
- <span id="page-11-14"></span>Cory Shain and William Schuler. 2021. [Continuous](https://doi.org/10.1016/j.cognition.2021.104735)[time deconvolutional regression for psycholinguistic](https://doi.org/10.1016/j.cognition.2021.104735) [modeling.](https://doi.org/10.1016/j.cognition.2021.104735) *Cognition*, 215.
- <span id="page-11-1"></span>Nathaniel J. Smith and Roger Levy. 2013. [The effect](https://doi.org/10.1016/j.cognition.2013.02.013) [of word predictability on reading time is logarithmic.](https://doi.org/10.1016/j.cognition.2013.02.013) *Cognition*, 128(3).
- <span id="page-11-13"></span>Robyn Speer. 2022. [rspeer/wordfreq: v3.0.](https://doi.org/10.5281/zenodo.7199437)
- <span id="page-11-19"></span>Julius Steuer, Marius Mosbach, and Dietrich Klakow. 2023. [Large GPT-like models are bad babies: A](https://doi.org/10.18653/v1/2023.conll-babylm.12) [closer look at the relationship between linguistic com](https://doi.org/10.18653/v1/2023.conll-babylm.12)[petence and psycholinguistic measures.](https://doi.org/10.18653/v1/2023.conll-babylm.12) In *Proceedings of the BabyLM Challenge at the 27th Conference on Computational Natural Language Learning*, Singapore. Association for Computational Linguistics.
- <span id="page-11-6"></span>Nisan Stiennon, Long Ouyang, Jeffrey Wu, Daniel Ziegler, Ryan Lowe, Chelsea Voss, Alec Radford, Dario Amodei, and Paul F Christiano. 2020. [Learn](https://proceedings.neurips.cc/paper_files/paper/2020/file/1f89885d556929e98d3ef9b86448f951-Paper.pdf)[ing to summarize with human feedback.](https://proceedings.neurips.cc/paper_files/paper/2020/file/1f89885d556929e98d3ef9b86448f951-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 33.
- <span id="page-11-15"></span>Mariya Toneva and Leila Wehbe. 2019. [Interpreting and](https://api.semanticscholar.org/CorpusID:167217728) [improving natural-language processing \(in machines\)](https://api.semanticscholar.org/CorpusID:167217728) [with natural language-processing \(in the brain\).](https://api.semanticscholar.org/CorpusID:167217728) In *Neural Information Processing Systems*.
- <span id="page-11-16"></span>Alex Warstadt, Alicia Parrish, Haokun Liu, Anhad Mohananey, Wei Peng, Sheng-Fu Wang, and Samuel R. Bowman. 2020. [BLiMP: The benchmark of linguis](https://doi.org/10.1162/tacl_a_00321)[tic minimal pairs for English.](https://doi.org/10.1162/tacl_a_00321) *Transactions of the Association for Computational Linguistics*, 8.
- <span id="page-11-7"></span>Ethan Wilcox, Clara Meister, Ryan Cotterell, and Tiago Pimentel. 2023a. [Language model quality correlates](https://doi.org/10.18653/v1/2023.emnlp-main.466) [with psychometric predictive power in multiple lan](https://doi.org/10.18653/v1/2023.emnlp-main.466)[guages.](https://doi.org/10.18653/v1/2023.emnlp-main.466) In *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, Singapore. Association for Computational Linguistics.
- <span id="page-11-2"></span>Ethan G. Wilcox, Tiago Pimentel, Clara Meister, Ryan Cotterell, and Roger P. Levy. 2023b. [Testing the pre](https://doi.org/10.1162/tacl_a_00612)[dictions of surprisal theory in 11 languages.](https://doi.org/10.1162/tacl_a_00612) *Transactions of the Association for Computational Linguistics*, 11.

- <span id="page-12-0"></span>Ethan Gotlieb Wilcox, Jon Gauthier, Jennifer Hu, Peng Qian, and Roger Levy. 2020. [On the predictive power](https://arxiv.org/abs/2006.01912) [of neural language models for human real-time com](https://arxiv.org/abs/2006.01912)[prehension behavior.](https://arxiv.org/abs/2006.01912) In *Proceedings of the Cognitive Science Society*.
- <span id="page-12-2"></span>Thomas Wolf, Lysandre Debut, Victor Sanh, Julien Chaumond, Clement Delangue, Anthony Moi, Pierric Cistac, Tim Rault, Remi Louf, Morgan Funtowicz, Joe Davison, Sam Shleifer, Patrick von Platen, Clara Ma, Yacine Jernite, Julien Plu, Canwen Xu, Teven Le Scao, Sylvain Gugger, Mariama Drame, Quentin Lhoest, and Alexander Rush. 2020. [Trans](https://doi.org/10.18653/v1/2020.emnlp-demos.6)[formers: State-of-the-art natural language processing.](https://doi.org/10.18653/v1/2020.emnlp-demos.6) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations*, Online. Association for Computational Linguistics.
- <span id="page-12-3"></span>Duo Yang and Nora Hollenstein. 2023. [Plm-as: Pre](https://septentrio.uit.no/index.php/nldl/article/view/6797/7021)[trained language models augmented with scanpaths](https://septentrio.uit.no/index.php/nldl/article/view/6797/7021) [for sentiment classification.](https://septentrio.uit.no/index.php/nldl/article/view/6797/7021) *Proceedings of the Northern Lights Deep Learning Workshop*.
- <span id="page-12-1"></span>Daniel M. Ziegler, Nisan Stiennon, Jeffrey Wu, Tom B. Brown, Alec Radford, Dario Amodei, Paul Christiano, and Geoffrey Irving. 2020. [Fine-tuning lan](https://arxiv.org/abs/1909.08593)[guage models from human preferences.](https://arxiv.org/abs/1909.08593) *Preprint*, arXiv:1909.08593.

#### **Derivations**

## <span id="page-13-0"></span>A.1 Deriving Optimal Coefficients

We now discuss how we estimate the optimal coefficient  $\beta^*$  to approximate the reward, as described in §3.2. We start with finding the optimal coefficients

$$\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \underset{\boldsymbol{\beta} \in \mathbb{R}^{D}}{\operatorname{argmin}} \frac{1}{N} \| \boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}} \|^{2}. \tag{14}$$

Assuming  $(\mathbf{X}_{\theta}^{\top}\mathbf{X}_{\theta})^{-1}$  is invertible, we take the derivative with respect to  $\boldsymbol{\beta}_{\theta}$ , set it to 0 and solve for  $\boldsymbol{\beta}_{\theta}^{\star}$ :

$$-\frac{2}{N}\mathbf{X}_{\boldsymbol{\theta}}^{\top}(\boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}}\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star}) = 0$$
 (15a)

$$\Leftrightarrow -\mathbf{X}_{\boldsymbol{\theta}}^{\top}\boldsymbol{\psi} + \mathbf{X}_{\boldsymbol{\theta}}^{\top}\mathbf{X}_{\boldsymbol{\theta}}\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = 0$$
 (15b)

$$\Leftrightarrow \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi} \tag{15c}$$

$$\Leftrightarrow -\mathbf{X}_{\theta}^{\top} \boldsymbol{\psi} + \mathbf{X}_{\theta}^{\top} \mathbf{X}_{\theta} \boldsymbol{\beta}_{\theta}^{\star} = 0$$

$$\Leftrightarrow \mathbf{X}_{\theta}^{\top} \mathbf{X}_{\theta} \boldsymbol{\beta}_{\theta}^{\star} = \mathbf{X}_{\theta}^{\top} \boldsymbol{\psi}$$

$$\Leftrightarrow \boldsymbol{\beta}_{\theta}^{\star} = (\mathbf{X}_{\theta}^{\top} \mathbf{X}_{\theta})^{-1} \mathbf{X}_{\theta}^{\top} \boldsymbol{\psi}.$$
(15b)
$$\Leftrightarrow \boldsymbol{\beta}_{\theta}^{\star} = (\mathbf{X}_{\theta}^{\top} \mathbf{X}_{\theta})^{-1} \mathbf{X}_{\theta}^{\top} \boldsymbol{\psi}.$$
(15d)

In theory,  $(\mathbf{X}_{\theta}^{\top}\mathbf{X}_{\theta})^{-1}$  may not always be invertible, which is why we add a regularization term  $\rho \mathbf{I}$ , where I is the identity matrix and  $\rho > 0$  is a parameter determining the strength of the regularization. The resulting estimator  $\beta_{\theta}^{\star} = (\mathbf{X}_{\theta}^{\top} \mathbf{X}_{\theta} + \rho \mathbf{I})^{-1} \mathbf{X}_{\theta}^{\top} \psi$  is known as the ridge regression estimator (Hoerl and Kennard, 1970) and presents the solution to the following problem:

<span id="page-13-2"></span>
$$\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \underset{\boldsymbol{\beta}_{\boldsymbol{\theta}} \in \mathbb{R}^{D}}{\operatorname{argmin}} \frac{1}{N} \|\boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}\|^{2} + \gamma \|\boldsymbol{\beta}_{\boldsymbol{\theta}}\|^{2}, \tag{16}$$

where  $\gamma > 0$ . We define  $\rho = N\gamma$ . Then setting the derivative of Eq. (16) to zero leads to

$$-\frac{2}{N}\mathbf{X}_{\boldsymbol{\theta}}^{\top}(\boldsymbol{\psi} - \mathbf{X}_{\boldsymbol{\theta}}\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star}) + 2\gamma\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = 0$$
 (17a)

$$\Leftrightarrow \frac{2}{N} \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} + 2\gamma \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \frac{2}{N} \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}$$
 (17b)

$$\Leftrightarrow \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} + N \gamma \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}$$

$$\Leftrightarrow \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} + \rho \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}$$

$$(17c)$$

$$\Leftrightarrow \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} + \rho \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}$$

$$(17d)$$

$$\Leftrightarrow \mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} + \rho \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} \qquad = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}$$
 (17d)

$$\Leftrightarrow \quad \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} \qquad \qquad = \quad \left(\mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} + \rho \mathbf{I}\right)^{-1} \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}. \tag{17e}$$

# <span id="page-13-1"></span>A.2 Solving for Optimal Coefficients

To compute the regression coefficients efficiently, we use the Cholesky decomposition to solve for  $\beta_{R}^{\star}$ given as

$$\boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = (\mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} + \rho \mathbf{I})^{-1} \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi}, \tag{18}$$

where  $\rho$  is the regularization parameter, which we set  $\rho = 1e - 5$  and I is the identity matrix. Since  $\mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} + \rho \mathbf{I}$  is symmetric and positive definite, we compute the Cholesky decomposition

$$\mathbf{X}_{\boldsymbol{\theta}}^{\top} \mathbf{X}_{\boldsymbol{\theta}} + \rho \mathbf{I} = \mathbf{L} \mathbf{L}^{\top}, \tag{19}$$

where  $\mathbf{L} \in \mathbb{R}^{D \times D}$  is a lower triangular matrix. To solve for  $\boldsymbol{\beta}^{\star}_{\boldsymbol{\theta}}$ , we first solve for an intermediate vector  $\mathbf{z}$ 

$$\mathbf{L}\mathbf{z} = \mathbf{X}_{\boldsymbol{\theta}}^{\top} \boldsymbol{\psi} \tag{20}$$

We then solve for  $\beta_{\theta}^{\star}$ 

$$\mathbf{L}^{\top} \boldsymbol{\beta}_{\boldsymbol{\theta}}^{\star} = \mathbf{z}. \tag{21}$$

# B Datasets, Reading Times & Parameters

# <span id="page-14-0"></span>B.1 Datasets

Here, we provide additional details on the datasets and reading time measurements used during our analysis. We fine-tune and evaluate models on the Dundee [\(Kennedy et al.,](#page-10-12) [2003\)](#page-10-12), Provo [\(Luke and](#page-10-13) [Christianson,](#page-10-13) [2018\)](#page-10-13), and ZuCo corpora. For the ZuCo corpus, we use data from tasks 1 and 2 from the ZuCo 1.0 corpus [\(Hollenstein et al.,](#page-10-14) [2018\)](#page-10-14) and task 1 from the ZuCo 2.0 corpus [\(Hollenstein et al.,](#page-10-15) [2020\)](#page-10-15). All data used in our analysis is publicly available. For the Dundee and ZuCo corpora, we process the data used by [Hollenstein et al.](#page-10-21) [\(2021\)](#page-10-21), which contains word-level means for fixation counts and reading durations, averaged over all participants, and split into individual sentences.[10](#page-14-3) For the Provo corpus, we compute the mean reading times from the official repository. [11](#page-14-4) From all datasets, we remove duplicate sentences and short sentences with less than four words. The mean number of sentences and words for train and test sets are given in Tab. [4.](#page-14-1)

<span id="page-14-1"></span>

| Configuration           | Train Tokens | Train Sents | Test Tokens | Test Sents |
|-------------------------|--------------|-------------|-------------|------------|
| Dundee (D) → Provo (P)  | 20894.7      | 980         | 1144        | 54         |
| Dundee (D) → Dundee (D) | 20894.7      | 980         | 20207       | 931        |
| Dundee (D) → ZuCo (Z)   | 20894.7      | 980         | 7715        | 424        |
| ZuCo (Z) → Provo (P)    | 7761         | 451         | 1144        | 54         |
| ZuCo (Z) → Dundee (D)   | 7761         | 451         | 20207       | 931        |
| ZuCo (Z) → ZuCo (Z)     | 7761         | 451         | 7715        | 424        |
| Provo (P) → Provo (P)   | 1113.7       | 56          | 1144        | 54         |
| Provo (P) → Dundee (D)  | 1113.7       | 56          | 20207       | 931        |
| Provo (P) → ZuCo (Z)    | 1113.7       | 56          | 7715        | 424        |

Table 4: Data splits and configurations for fine-tuning and evaluation. Numbers indicate the mean number of tokens and sentences in each train and test split across random seeds.

# B.2 Reading Times

For Dundee and ZuCo, we extract the mean first pass duration over the participants, which is defined as "the sum of all fixations on w from the first time a subject fixates w to the first time the subject fixates another token"[\(Hollenstein et al.,](#page-10-21) [2021,](#page-10-21) p.109). Similarly, for Provo, we compute the mean gaze duration defined as the "Dwell time (i.e., summation of the duration across all fixations) of the first run within the current interest area" [\(Luke and Christianson,](#page-10-13) [2018,](#page-10-13) Tab. 2). While these two definitions are very similar, they may not be exactly identical. In Tab. [5,](#page-14-5) we compare the mean and standard deviation of reading times as well as the number of zero reading times. We observe that while Dundee and Provo exhibit relatively similar means and standard deviations, ZuCo shows overall lower mean reading times. Unlike Dundee and ZuCo, Provo contains no instances of words with zero reading times, likely due to the high number of participants.

| Dataset         | Mean Reading Times | STD Reading Times | Zero Count |
|-----------------|--------------------|-------------------|------------|
| Dundee<br>Provo | 140.59<br>164.16   | 88.49<br>77.77    | 854<br>0   |
| ZuCo            | 92.28              | 52.21             | 176        |

<span id="page-14-5"></span>Table 5: Mean, standard deviation, and zeros count for the reading times from Dundee, Provo, and ZuCo.

## <span id="page-14-2"></span>B.3 Fine-Tuning Parameters

For all runs, we use the parameter configurations in Tab. [6](#page-15-0) and repeat each experiment 3 times with random seeds (42, 8, and 64). We fine-tune and evaluate three GPT-2 models: GPT-2 Small with 117 million parameters, GPT-2 Medium with 345 million parameters, and GPT-2 Large with 762 million

<span id="page-14-3"></span><sup>10</sup><https://github.com/DS3Lab/multilingual-gaze>

<span id="page-14-4"></span><sup>11</sup><https://osf.io/sjefs/>

parameters. All models are fine-tuned for 5k data steps using a batch size of 1 and gradient accumulation of 2, leading to a total of 2.5k optimization steps. To adjust the learning rate during fine-tuning, we use a cosine annealing learning rate schedule[12](#page-15-1) [\(Loshchilov and Hutter,](#page-10-22) [2017\)](#page-10-22) with a maximum learning rate of 1.5e-5, minimum learning rate of 2e-7. During each cycle, we decrease the learning by a factor of 0.8 and increase the cycle length by a factor of 1.8. For all experiments, we use NVIDIA GeForce RTX 3090, RTX 4090, and RTX 2080 Ti GPUs. The GPU times vary depending on the model's parameter counts and the size of the data splits, taking a minimum of approximately 12 minutes for GPT-2 Small fine-tuned on Provo and evaluated on Provo and a maximum of 4 hours for GPT-2 Large fine-tuned on Dundee and evaluated on Dundee.

<span id="page-15-0"></span>

| Parameter                          | Setting                             |
|------------------------------------|-------------------------------------|
| Optimizer                          | AdamW                               |
| Scheduler                          | Cosine Annealing With Warm Restarts |
| Batch Size                         | 1                                   |
| Grad. Accumulation                 | 2                                   |
| Total Steps                        | 5000                                |
| Optimizer Steps                    | 2500                                |
| Max Learning Rate                  | 1.5e-5                              |
| Min Learning Rate                  | 2.0e-7                              |
| Decrease Rate of Max Learning Rate | 0.8                                 |
| Cycle Steps Magnification          | 1.8                                 |
| Warm Up Steps                      | 100                                 |

Table 6: Fine-tuning parameters used consistently across different runs.

## B.4 Evaluation

We perform evaluation every 50 steps on the held-out test splits in Tab. [4,](#page-14-1) during which we compute the surprisal estimates, the regressors' coefficients, and the language model's perplexity for each batch. Using the surprisal estimates we compute the ∆llh by performing a 5-fold cross-validation on the test data, where we fit baseline and target linear regressors using ordinary least squares.[13](#page-15-2) Note that we do not scale the predictor variables to maintain consistency between the linear regression and the calculation of our reward in Eq. [\(13\)](#page-3-7), where batch-level surprisal estimates prevent global scaling.

<span id="page-15-1"></span><sup>12</sup><https://github.com/katsura-jp/pytorch-cosine-annealing-with-warmup>

<span id="page-15-2"></span><sup>13</sup>[https://www.statsmodels.org/stable/generated/statsmodels.regression.linear\\_model.OLS.html](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html)

### C Detailed Results

## C.1 $\Delta_{\text{Ilh}}$ Change

<span id="page-16-0"></span>

| GPT2-L                              |                                |                              |            | GPT2-M                         |                              | GPT2-S     |                                |                              |            |
|-------------------------------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|
| Data                                | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase |
| $\mathrm{D} \rightarrow \mathrm{D}$ | 0.63                           | $0.98 \pm 0.09$              | 55.29      | 0.68                           | $0.90 \pm 0.06$              | 32.82      | 0.78                           | $1.11 \pm 0.01$              | 42.88      |
| $\mathrm{P} \to \mathrm{D}$         | 0.63                           | $0.78 \pm 0.04$              | 23.29      | 0.68                           | $0.84 \pm 0.00$              | 24.23      | 0.78                           | $1.01 \pm 0.02$              | 29.90      |
| $Z \rightarrow D$                   | 0.63                           | $0.69 \pm 0.01$              | 9.08       | 0.68                           | $0.75 \pm 0.03$              | 11.08      | 0.78                           | $0.91 \pm 0.04$              | 16.60      |
| $\mathrm{D} \to \mathrm{P}$         | 1.67                           | $2.19 \pm 0.37$              | 31.36      | 2.04                           | $2.14 \pm 0.05$              | 4.93       | 2.14                           | $2.52 \pm 0.09$              | 17.78      |
| $\mathrm{P} \rightarrow \mathrm{P}$ | 1.67                           | $2.43 \pm 0.14$              | 45.27      | 2.04                           | $2.36 \pm 0.10$              | 15.62      | 2.14                           | $2.67 \pm 0.15$              | 24.77      |
| $\mathbf{Z} \to \mathbf{P}$         | 1.67                           | $1.71 \pm 0.03$              | 2.12       | 2.04                           | $2.18 \pm 0.03$              | 6.46       | 2.14                           | $2.18 \pm 0.01$              | 2.00       |
| $\mathrm{D} \rightarrow \mathrm{Z}$ | 1.17                           | $1.59 \pm 0.15$              | 36.58      | 1.37                           | $1.53 \pm 0.06$              | 11.95      | 1.41                           | $1.75 \pm 0.06$              | 24.50      |
| $\mathrm{P} \to \mathrm{Z}$         | 1.17                           | $1.34 \pm 0.09$              | 15.01      | 1.37                           | $1.45 \pm 0.08$              | 5.73       | 1.41                           | $1.69 \pm 0.07$              | 20.09      |
| $Z {\to} Z$                         | 1.17                           | $2.12 \pm 0.10$              | 81.39      | 1.37                           | $1.94 \pm 0.04$              | 41.80      | 1.41                           | $2.26 \pm 0.14$              | 61.20      |

Table 7: Mean start and maximum  $\Delta_{llh}(10^{-2} \text{ nats})$  for Tab. 2, including standard errors across random seeds, rounded to two decimal places.

## C.2 Perplexity and $\Delta_{\text{Ilh}}$

<span id="page-16-1"></span>![](_page_16_Figure_5.jpeg)

Figure 6: Relationship between log perplexity and  $\Delta_{\rm llh}(10^{-2}~{\rm nats})$  for all models and data splits. Increases in  $\Delta_{\rm llh}$  correspond to increases in perplexity.

#### C.3 BLiMP

<span id="page-16-2"></span>![](_page_16_Figure_8.jpeg)

Figure 7: Results for all models on BLiMP. Baseline (i.e., non-fine-tuned) models are shown with hatching. Error bars are standard errors across the three random seeds. We observe a drop in accuracy as a result of fine-tuning.

## **C.4** Narrative Understanding

To measure models' abilities to track entities and produce text that is consistent with narrative structure, we evaluate them on LAMBADA (Paperno et al., 2016). This dataset requires that models produce the final word of a narrative. People can easily achieve higher performance on this task if they are given the full narrative context, but not if they are only given the previous sentence. Thus, performing well requires an understanding of broader contexts. The performance of our models is visualized in Fig. 8. As with BLiMP, we find that fine-tuned models perform slightly worse at this task compared to non-fine-tuned baselines.

## C.5 Results for the Regularized Objective

In this section, we present additional results for fine-tuning models using the KL regularized objective with a regularization coefficient of  $\lambda = 500$ . As shown in Tab. 8, the maximum  $\Delta_{\text{Ilh}}$  values and percentage

<span id="page-17-1"></span>![](_page_17_Figure_0.jpeg)

Figure 8: **Results for LAMBADA.** Baseline (i.e., non-fine-tuned) models are shown with hatching. Error bars are standard errors across the three random seeds. As with BLiMP, performance tends to decrease with fine-tuning.

increases tend to be lower compared to those for the unregularized objective in Tab. 7. However, standard errors for the maximum  $\Delta_{llh}$  are consistently lower, suggesting that fine-tuning is more stable across random seeds when regularizing the reward. Additionally, when visualizing the MSE and  $\Delta_{llh}$  throughout fine-tuning (Fig. 9), we observe more consistent improvements for Dundee  $\rightarrow$  Provo and ZuCo  $\rightarrow$  Provo compared to the trajectories for the unregularized objective in Fig. 1.

<span id="page-17-2"></span>

| GPT2-L                              |                                |                              | GPT2-M     |                                |                              |            | GPT2-S                         |                              |            |
|-------------------------------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|
| Data                                | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase |
| $D \rightarrow D$                   | 0.63                           | $0.81 \pm 0.00$              | 28.27      | 0.68                           | $0.85 \pm 0.03$              | 25.49      | 0.78                           | $1.02 \pm 0.01$              | 30.72      |
| $\mathbf{P} \to \mathbf{D}$         | 0.63                           | $0.71 \pm 0.01$              | 12.69      | 0.68                           | $0.71 \pm 0.00$              | 5.62       | 0.78                           | $0.93 \pm 0.01$              | 19.34      |
| $Z \rightarrow D$                   | 0.63                           | $0.69 \pm 0.00$              | 8.63       | 0.68                           | $0.71 \pm 0.02$              | 5.24       | 0.78                           | $0.88 \pm 0.00$              | 13.22      |
| $\mathrm{D} \to \mathrm{P}$         | 1.67                           | $2.09 \pm 0.03$              | 24.91      | 2.04                           | $2.18 \pm 0.03$              | 6.87       | 2.14                           | $2.36 \pm 0.03$              | 10.47      |
| $\mathrm{P} \rightarrow \mathrm{P}$ | 1.67                           | $1.98 \pm 0.04$              | 18.70      | 2.04                           | $2.25 \pm 0.07$              | 10.00      | 2.14                           | $2.37 \pm 0.02$              | 10.95      |
| $Z \rightarrow P$                   | 1.67                           | $1.86 \pm 0.03$              | 11.13      | 2.04                           | $2.19 \pm 0.00$              | 7.38       | 2.14                           | $2.19 \pm 0.01$              | 2.58       |
| $\mathrm{D} \to \mathrm{Z}$         | 1.17                           | $1.36 \pm 0.03$              | 16.86      | 1.37                           | $1.50 \pm 0.07$              | 9.52       | 1.40                           | $1.69 \pm 0.02$              | 20.01      |
| $P \to Z$                           | 1.17                           | $1.35 \pm 0.04$              | 16.14      | 1.37                           | $1.52 \pm 0.01$              | 11.24      | 1.40                           | $1.76 \pm 0.03$              | 25.34      |
| $Z \to Z$                           | 1.17                           | $1.58 \pm 0.07$              | 35.24      | 1.37                           | $1.78 \pm 0.01$              | 29.88      | 1.40                           | $1.98 \pm 0.06$              | 41.12      |

Table 8: Mean start and maximum  $\Delta_{\rm llh}(10^{-2} {\rm nats})$  values using the **KL regularized objective** with  $\lambda=500$ , including standard errors across random seeds, rounded to two decimal places.

<span id="page-17-0"></span>![](_page_17_Figure_5.jpeg)

Figure 9: MSE and  $\Delta_{\rm llh}(10^{-2} {\rm nats})$  changes for all data splits using the **KL regularized objective** with  $\lambda=500$ . Bands show the standard error across seeds. Compared to the results for the unregularized objective in §5.1, we observe smaller but consistent decreases in MSE and increases in  $\Delta_{\rm llh}$  for almost all configurations.

### **D** Reading Times

### <span id="page-18-0"></span>D.1 Total Reading Duration & First Fixation Duration

Throughout this work, we have focused on predicting gaze durations. Here, we extend our analysis by fine-tuning models to predict total reading durations—which are the summed durations of all fixations on a unit u—and first fixation durations, which are the durations of the first fixation on a unit u. As shown in Tab. 9, models predicting total reading durations start at higher  $\Delta_{\text{llh}}$  values, while models predicting first fixation durations start with lower  $\Delta_{\text{llh}}$  values compared to those predicting gaze durations. On average, we observe lower percentage increases for total reading durations and lower increases for first fixation durations. Similar to the trajectories for gaze duration in Fig. 1, the trajectories for total reading durations in Fig. 10 show decreasing MSE and increasing  $\Delta_{\text{llh}}$  for most configurations. The trajectories for the first fixation durations (Fig. 11) are less consistent, particularly for models fine-tuned on the ZuCo corpus, where the MSE tends to increase throughout fine-tuning.

<span id="page-18-2"></span>

|                                     |                                | GPT2-L                       |            |                                | GPT2-M                       |            | GPT2-S                         |                              |            |  |  |
|-------------------------------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|--|--|
| Data                                | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase |  |  |
|                                     | Total Reading Duration         |                              |            |                                |                              |            |                                |                              |            |  |  |
| $D \to D$                           | 1.11                           | $1.93 \pm 0.33$              | 73.20      | 1.18                           | $1.62 \pm 0.07$              | 37.48      | 1.35                           | $1.83 \pm 0.07$              | 35.41      |  |  |
| $\mathrm{P} \rightarrow \mathrm{D}$ | 1.11                           | $1.22 \pm 0.04$              | 9.20       | 1.18                           | $1.38 \pm 0.03$              | 17.26      | 1.35                           | $1.60 \pm 0.01$              | 18.62      |  |  |
| $Z \rightarrow D$                   | 1.11                           | $1.28 \pm 0.07$              | 15.01      | 1.18                           | $1.27 \pm 0.01$              | 7.83       | 1.35                           | $1.54 \pm 0.04$              | 14.47      |  |  |
| $\mathrm{D} \to \mathrm{P}$         | 3.11                           | $3.79 \pm 0.20$              | 21.90      | 3.45                           | $3.63 \pm 0.06$              | 5.29       | 3.86                           | $4.27 \pm 0.05$              | 10.61      |  |  |
| $\mathbf{P} \to \mathbf{P}$         | 3.11                           | $4.16 \pm 0.16$              | 33.64      | 3.45                           | $4.29 \pm 0.11$              | 24.43      | 3.86                           | $4.59 \pm 0.16$              | 18.70      |  |  |
| $Z \rightarrow P$                   | 3.11                           | $3.89 \pm 0.33$              | 24.95      | 3.45                           | $3.50 \pm 0.02$              | 1.42       | 3.86                           | $3.91 \pm 0.00$              | 1.33       |  |  |
| $\mathrm{D} \to \mathrm{Z}$         | 2.82                           | $3.38 \pm 0.54$              | 19.93      | 2.98                           | $2.99 \pm 0.02$              | 0.19       | 2.89                           | $3.25 \pm 0.19$              | 12.47      |  |  |
| $\mathrm{P} \rightarrow \mathrm{Z}$ | 2.82                           | $2.85 \pm 0.01$              | 1.31       | 2.98                           | $3.03 \pm 0.01$              | 1.64       | 2.89                           | $2.98 \pm 0.01$              | 3.10       |  |  |
| $Z {\to} Z$                         | 2.82                           | $5.28 \pm 0.79$              | 87.40      | 2.98                           | $3.92 \pm 0.14$              | 31.35      | 2.89                           | $4.23\pm0.23$                | 46.37      |  |  |
|                                     |                                |                              |            | First I                        | Fixation Duratio             | n          |                                |                              |            |  |  |
| $D \to D$                           | 0.08                           | $1.21 \pm 0.47$              | 1397.26    | 0.07                           | $0.12 \pm 0.02$              | 64.10      | 0.09                           | $0.14 \pm 0.01$              | 52.02      |  |  |
| $\mathrm{P} \to \mathrm{D}$         | 0.08                           | $0.11 \pm 0.02$              | 35.25      | 0.07                           | $0.13 \pm 0.01$              | 81.56      | 0.09                           | $0.20 \pm 0.04$              | 121.22     |  |  |
| $Z \rightarrow D$                   | 0.08                           | $0.10 \pm 0.02$              | 25.05      | 0.07                           | $0.07 \pm 0.00$              | 1.10       | 0.09                           | $0.10 \pm 0.01$              | 9.49       |  |  |
| $\mathrm{D} \to \mathrm{P}$         | 1.29                           | $5.07 \pm 1.77$              | 292.36     | 1.51                           | $1.57 \pm 0.13$              | 3.87       | 1.37                           | $1.55 \pm 0.20$              | 13.46      |  |  |
| $\mathbf{P} \to \mathbf{P}$         | 1.29                           | $2.13 \pm 0.08$              | 64.61      | 1.51                           | $2.50 \pm 0.05$              | 66.19      | 1.37                           | $2.55 \pm 0.31$              | 86.55      |  |  |
| $\mathbf{Z} \to \mathbf{P}$         | 1.29                           | $1.44 \pm 0.41$              | 11.26      | 1.51                           | $1.51 \pm 0.01$              | 0.33       | 1.37                           | $1.38 \pm 0.02$              | 1.01       |  |  |
| $\mathrm{D} \to \mathrm{Z}$         | 0.20                           | $1.37 \pm 0.46$              | 591.38     | 0.21                           | $0.31 \pm 0.01$              | 51.38      | 0.18                           | $0.25 \pm 0.02$              | 40.97      |  |  |
| $\mathrm{P} \to \mathrm{Z}$         | 0.20                           | $0.21 \pm 0.01$              | 8.20       | 0.21                           | $0.23 \pm 0.01$              | 13.14      | 0.18                           | $0.32 \pm 0.06$              | 75.49      |  |  |
| $Z \rightarrow Z$                   | 0.20                           | $0.55 \pm 0.37$              | 175.48     | 0.21                           | $0.25 \pm 0.08$              | 21.36      | 0.18                           | $0.28 \pm 0.04$              | 52.88      |  |  |

Table 9: Mean start and maximum  $\Delta_{\text{llh}}(10^{-2} \text{ nats})$  values using **total reading durations and first fixation durations**, including standard errors across random seeds, rounded to two decimal places.

<span id="page-18-3"></span>![](_page_18_Figure_5.jpeg)

Figure 10: MSE and  $\Delta_{\text{llh}}$  changes for **total reading durations**. Bands show standard errors across seeds.

## <span id="page-18-1"></span>**D.2** Random Reading Times

Here we conduct additional experiments using random reading times to verify that the observed decreases in MSE and increases in  $\Delta_{llh}$  are due to aligning language models with human reading times and not

<span id="page-19-0"></span>![](_page_19_Figure_0.jpeg)

Figure 11: MSE and  $\Delta_{\text{Ilh}}$  changes for **first fixation durations**. Bands show standard errors across seeds.

due to random noise or other confounding factors. Instead of fitting coefficients based on the reading times from the respective training dataset  $\mathcal{D}$ , we sample reading times from a Gaussian distribution, where the mean and standard deviation match those of the training dataset  $\mathcal{D}$ . The results in Fig. 12 show that fine-tuning on random reading times tends to have the opposite effect compared to fine-tuning on real reading times, leading to increasing MSE and decreasing  $\Delta_{llh}$  throughout fine-tuning. Additionally, as in Tab. 7, we compare the start and maximum  $\Delta_{llh}$  values, as well as the percentage increases. Tab. 10 shows that fine-tuning with random reading times only leads to minimal or no increases. These results show that random reading times do not improve language models at predicting reading times and confirm the effectiveness of our technique for aligning models to human reading times.

<span id="page-19-1"></span>![](_page_19_Figure_3.jpeg)

Figure 12: MSE and  $\Delta_{\rm llh}(10^{-2} {\rm nats})$  changes using **random reading times** sampled according to a normal distribution. Bands show the standard error across seeds. MSE increases, and  $\Delta_{\rm llh}$  decreases for most configurations, indicating that models become worse at predicting reading times throughout fine-tuning.

<span id="page-19-2"></span>

| GPT2-L                      |                                |                              | GPT2-M     |                                |                              |            | GPT2-S                         |                              |            |
|-----------------------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|--------------------------------|------------------------------|------------|
| Data                        | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase | $\Delta_{\rm llh}^{\rm start}$ | $\Delta_{\rm llh}^{\rm max}$ | % Increase |
| $D \rightarrow D$           | 0.63                           | $0.67 \pm 0.23$              | 6.31       | 0.68                           | $0.68 \pm 0.00$              | 0.00       | 0.78                           | $0.83 \pm 0.03$              | 6.42       |
| $P \rightarrow D$           | 0.63                           | $0.66 \pm 0.00$              | 3.84       | 0.68                           | $0.68 \pm 0.00$              | 0.00       | 0.78                           | $0.82 \pm 0.03$              | 5.67       |
| $Z \rightarrow D$           | 0.63                           | $0.64 \pm 0.01$              | 0.88       | 0.68                           | $0.68 \pm 0.01$              | 1.30       | 0.78                           | $0.78 \pm 0.00$              | 0.00       |
| $\mathrm{D} \to \mathrm{P}$ | 1.67                           | $1.67 \pm 0.00$              | 0.00       | 2.04                           | $2.06 \pm 0.01$              | 0.56       | 2.14                           | $2.14 \pm 0.00$              | 0.00       |
| $\mathbf{P} \to \mathbf{P}$ | 1.67                           | $1.74 \pm 0.01$              | 4.06       | 2.04                           | $2.04 \pm 0.00$              | 0.00       | 2.14                           | $2.22 \pm 0.02$              | 3.87       |
| $Z \rightarrow P$           | 1.67                           | $1.71 \pm 0.02$              | 2.44       | 2.04                           | $2.08 \pm 0.01$              | 1.66       | 2.14                           | $2.14 \pm 0.01$              | 0.03       |
| $\mathrm{D} \to \mathrm{Z}$ | 1.17                           | $1.17 \pm 0.00$              | 0.00       | 1.37                           | $1.37 \pm 0.00$              | 0.17       | 1.41                           | $1.50 \pm 0.04$              | 6.48       |
| $\mathrm{P} \to \mathrm{Z}$ | 1.17                           | $1.20 \pm 0.02$              | 3.20       | 1.37                           | $1.37 \pm 0.00$              | 0.00       | 1.41                           | $1.53 \pm 0.01$              | 9.14       |
| $Z \to Z$                   | 1.17                           | $1.20\pm0.01$                | 2.98       | 1.37                           | $1.42\pm0.03$                | 3.40       | 1.41                           | $1.45\pm0.04$                | 2.86       |

Table 10: Mean start and maximum  $\Delta_{\text{llh}}(10^{-2} \text{ nats})$  values for **random reading times**, including standard errors across random seeds, rounded to two decimal places.

# <span id="page-20-0"></span>E Coefficients

Fig. [13a](#page-20-1) shows the trajectory of coefficients for all data splits during fine-tuning using the unregularized objective. While the results for unigram surprisal and bias coefficients are mixed, the coefficients for surprisal tend to increase during fine-tuning, and those for length tend to decrease. These trends are more consistent in experiments with the largest increases in ∆llh, i.e., where the training and test splits come from the same datasets. In contrast, the coefficients in experiments involving domain shift (where the training and test splits come from different datasets) do not have such a clear pattern, particularly those without consistent increases in ∆llh (Dundee → Provo and ZuCo → Provo).

Additionally, we visualize all coefficients from models trained with the regularized objective (λ = 500). As shown in Fig. [9,](#page-17-0) regularization leads to lower ∆llh increases but more consistent trajectories across configurations, which is why we also hypothesize more consistent trajectories of the coefficients. As shown in Fig. [13b,](#page-20-1) the coefficients for surprisal and bias show a clear upward trend throughout fine-tuning, while the coefficients for unigram surprisal show a clear downward trend.

<span id="page-20-1"></span>![](_page_20_Figure_3.jpeg)

Figure 13: Mean coefficients of unit-level features over fine-tuning for all data splits. Smoothed values (window size 5) are shown, with unsmoothed values in a pale version of the color.

# <span id="page-21-0"></span>F Text-Generation

Here we expand on the text-generation experiments described in [§6.2.](#page-7-2) We sample 500 prefixes c, each consisting of the first three words from the CNN/DailyMail dataset [\(Hermann et al.,](#page-10-17) [2015;](#page-10-17) [See et al.,](#page-11-17) [2017\)](#page-11-17), and generate completions u ∼ pθ(· | c) of up to 50 tokens using our fine-tuned language models. For a completion u of length N, we write u<sup>n</sup> to denote the n th unit of u. Further, let c<sup>n</sup> be the context of u<sup>n</sup> in u, including the prefix c. We exclude short completions with |u| < 3 and estimate surprisal with a separate language model, Pythia-70m [\(Biderman et al.,](#page-9-13) [2023\)](#page-9-13) using the code from [Pimentel and](#page-11-21) [Meister](#page-11-21) [\(2024\)](#page-11-21).[14](#page-21-1) Recently, [Oh and Schuler](#page-11-22) [\(2024\)](#page-11-22); [Pimentel and Meister](#page-11-21) [\(2024\)](#page-11-21) have argued that leading whitespaces from tokenization pose a confound to surprisal calculations and that the probability of trailing whitespaces should be included instead. However, we do not include a unit's trailing whitespace in our surprisal calculation; see [Giulianelli et al.](#page-10-23) [\(2024\)](#page-10-23). Then, following previous work [\(Meister et al.,](#page-10-10) [2021;](#page-10-10) [Clark et al.,](#page-9-14) [2023\)](#page-9-14), we measure the uniformity of information of a generated completion u given the prefix c using the mean surprisal variance

$$UID_{v}(\boldsymbol{u} \mid \boldsymbol{c}) = \frac{1}{N} \sum_{n=1}^{N} (\iota_{\boldsymbol{\theta}}(u_{n} \mid \boldsymbol{c}_{n}) - \mu_{\iota_{\boldsymbol{\theta}}}(\boldsymbol{u} \mid \boldsymbol{c}))^{2},$$
(22)

where the mean surprisal µι<sup>θ</sup> (u | c) is given by

$$\mu_{\iota_{\boldsymbol{\theta}}}(\boldsymbol{u} \mid \boldsymbol{c}) = \frac{1}{N} \sum_{n=1}^{N} \iota_{\boldsymbol{\theta}}(u_n \mid \boldsymbol{c}_n).$$
 (23)

Additionally, we calculate the mean local surprisal variance:

$$UID_{lv}(\boldsymbol{u} \mid \boldsymbol{c}) = \frac{1}{N-1} \sum_{n=2}^{N} \left( \iota_{\boldsymbol{\theta}}(u_n \mid \boldsymbol{c}_n) - \iota_{\boldsymbol{\theta}}(u_{n-1} \mid \boldsymbol{c}_{n-1}) \right)^2.$$
 (24)

To evaluate the diversity of the generations, we calculate the mean unique n-gram ratio (n-Gram%) over completions u. In Tab. [11,](#page-22-0) we report the mean surprisal, surprisal variance, local surprisal variance, and unique n-gram ratios across all data splits. For models fine-tuned without regularization (λ = 0), surprisal variance and local variance tend to increase compared to the pretrained models, with a few exceptions, particularly for GPT2-M, where the variance and local variance remain close to the pretrained models. Overall, this indicates that information becomes less uniformly distributed. However, under KL regularization (λ = 500), this trend is reversed, and we observe more uniform information in the generated text with the exception being GPT2-L: Dundee → Dundee. Additionally, we observe a decline in the ratio of unique unigrams compared to the pretrained models, indicating that fine-tuned models generate more repetitive text. However, diversity and uniformity of information are not necessarily linked, as models fine-tuned without regularization tend to generate less diverse and less uniform text.

<span id="page-21-1"></span><sup>14</sup><https://github.com/tpimentelms/probability-of-a-word>

<span id="page-22-0"></span>

| Model                        |                      | ↓ UIDv               | ↓ UIDlv               | ↑1-Gram%               | ↑2-Gram%               | ↑3-Gram%               |
|------------------------------|----------------------|----------------------|-----------------------|------------------------|------------------------|------------------------|
|                              | ↓ µιθ<br>3.00        | 6.69                 | 14.25                 | 84.84                  | 94.16                  | 95.86                  |
| GPT2-L                       |                      |                      |                       |                        |                        |                        |
| GPT2-M                       | 2.94                 | 7.67                 | 16.62                 | 84.39                  | 93.07                  | 94.83                  |
| GPT2-S                       | 2.62                 | 5.70                 | 11.65                 | 82.53                  | 91.63                  | 93.35                  |
|                              |                      |                      | λ = 0                 |                        |                        |                        |
| GPT2-L D → D                 | 3.380.35             | 10.172.93            | 20.586.94             | 67.0714.68             | 74.7916.37             | 76.7116.32             |
| GPT2-L P → D                 | 2.960.03             | 11.291.74            | 23.764.66             | 68.881.50              | 79.781.48              | 82.791.53              |
| GPT2-L Z → D                 | 3.490.21             | 9.711.35             | 20.153.03             | 78.024.05              | 92.402.04              | 95.481.26              |
| GPT2-L D → P                 | 3.030.45             | 9.402.49             | 19.264.80             | 76.413.92              | 85.804.50              | 88.174.39              |
| GPT2-L P → P                 | 2.970.04             | 11.271.74            | 23.814.64             | 68.911.76              | 79.911.66              | 82.881.65              |
| GPT2-L Z → P                 | 3.710.27             | 11.222.87            | 23.385.82             | 86.740.79              | 96.360.42              | 97.980.49              |
| GPT2-L D → Z                 | 3.240.20             | 7.721.57             | 14.484.86             | 61.6519.46             | 68.3821.10             | 70.1621.20             |
| GPT2-L P → Z                 | 2.970.03             | 6.600.08             | 14.060.19             | 82.931.91              | 92.891.27              | 95.000.86              |
| GPT2-L Z → Z                 | 3.990.12             | 13.850.98            | 27.722.46             | 84.601.91              | 94.712.05              | 96.391.68              |
| GPT2-M D → D                 | 3.270.03             | 8.940.25             | 18.220.71             | 80.820.35              | 91.370.63              | 93.820.73              |
| GPT2-M P → D                 | 3.040.07             | 7.810.47             | 15.851.21             | 75.820.24              | 87.770.17              | 90.910.26              |
| GPT2-M Z → D                 | 3.270.24             | 7.950.92             | 16.701.74             | 83.371.59              | 93.871.44              | 95.811.15              |
| GPT2-M D → P                 | 2.830.09             | 6.961.02             | 14.732.40             | 81.051.78              | 90.151.62              | 92.251.45              |
| GPT2-M P → P                 | 2.990.04             | 7.810.46             | 14.521.42             | 67.510.78              | 78.710.55              | 82.190.68              |
| GPT2-M Z → P                 | 3.080.09             | 7.250.60             | 15.181.32             | 84.680.70              | 93.700.89              | 95.370.81              |
| GPT2-M D → Z                 | 2.890.02             | 7.610.80             | 15.621.20             | 81.180.69              | 91.210.98              | 93.461.00              |
| GPT2-M P → Z                 | 2.920.03             | 7.450.45             | 15.530.79             | 76.634.35              | 87.133.91              | 89.823.52              |
| GPT2-M Z → Z                 | 3.780.13             | 12.121.42            | 24.122.59             | 84.950.86              | 94.300.85              | 96.000.80              |
| GPT2-S D → D                 | 2.720.13             | 6.270.52             | 13.091.52             | 81.140.95              | 89.131.19              | 91.021.22              |
| GPT2-S P → D                 | 2.940.05             | 7.030.31             | 13.920.58             | 71.912.60              | 83.592.19              | 86.611.83              |
| GPT2-S Z → D                 | 2.890.13             | 7.240.79             | 14.021.19             | 79.212.10              | 89.311.04              | 91.610.73              |
| GPT2-S D → P                 | 2.720.10             | 6.540.27             | 13.050.59             | 77.083.04              | 85.982.90              | 88.302.66              |
| GPT2-S P → P                 | 2.950.07             | 6.910.25             | 13.790.93             | 72.171.99              | 83.911.42              | 86.871.19              |
| GPT2-S Z → P                 | 2.620.04             | 5.490.32             | 11.210.49             | 81.921.03              | 90.860.94              | 92.630.76              |
| GPT2-S D → Z                 | 2.540.07             | 5.810.25             | 11.250.30             | 76.732.73              | 85.562.60              | 87.842.33              |
| GPT2-S P → Z                 | 2.580.01             | 5.230.27             | 10.590.73             | 77.172.97              | 87.902.13              | 90.461.60              |
| GPT2-S Z → Z                 | 2.960.13             | 7.791.02             | 15.402.02             | 79.611.94              | 89.082.34              | 91.212.32              |
|                              |                      |                      | λ = 500               |                        |                        |                        |
| GPT2-L D → D                 | 3.010.04             | 8.050.77             | 16.541.34             | 82.380.18              | 92.390.40              | 94.260.43              |
| GPT2-L P → D                 | 2.480.03             | 5.230.40             | 10.350.65             | 76.240.66              | 86.370.62              | 88.850.60              |
| GPT2-L Z → D                 | 2.700.02             | 5.640.01             | 12.000.10             | 80.910.63              | 91.110.39              | 93.150.33              |
| GPT2-L D → P                 | 2.850.01             | 5.970.07             | 12.620.16             | 83.480.60              | 92.490.63              | 94.230.63              |
| GPT2-L P → P                 | 2.460.03             | 5.140.35             | 9.950.55              | 76.750.79              | 86.680.50              | 89.010.38              |
| GPT2-L Z → P                 | 2.820.05             | 6.120.31             | 13.060.72             | 83.110.83              | 92.960.61              | 94.750.52              |
| GPT2-L D → Z                 | 2.880.03             | 6.370.19             | 13.640.41             | 83.040.71              | 91.950.71              | 93.690.63              |
| GPT2-L P → Z                 | 2.340.01             | 4.460.07             | 8.840.09              | 73.860.99              | 84.260.90              | 86.960.84              |
| GPT2-L Z → Z                 | 2.750.02             | 5.610.09             | 11.960.30             | 81.120.20              | 91.510.42              | 93.630.48              |
| GPT2-M D → D                 | 2.850.02             | 6.630.35             | 13.980.78             | 83.221.08              | 92.170.33              | 94.090.14              |
| GPT2-M P → D                 | 2.700.03             | 5.730.54             | 11.741.14             | 79.410.88              | 90.140.48              | 92.640.31              |
| GPT2-M Z → D                 | 2.720.04             | 6.070.17             | 12.760.30             | 81.520.78              | 91.550.64              | 93.720.56              |
| GPT2-M D → P                 | 2.800.07             | 6.790.83             | 14.412.03             | 83.001.39              | 91.461.04              | 93.410.91              |
| GPT2-M P → P                 | 2.460.03             | 4.540.17             | 9.160.42              | 75.910.85              | 86.710.59              | 89.650.56              |
| GPT2-M Z → P                 | 2.720.03             | 6.000.04             | 12.590.10             | 81.541.14              | 91.270.78              | 93.280.76              |
| GPT2-M D → Z                 | 2.800.06             | 6.750.14             | 14.050.34             | 81.901.04              | 91.210.82              | 93.180.80              |
| GPT2-M P → Z                 | 2.570.09             | 5.320.46             | 10.820.98             | 77.081.73              | 88.041.19              | 90.780.98              |
| GPT2-M Z → Z                 | 2.720.03             | 5.880.05             | 12.170.21             | 81.940.91              | 91.530.55              | 93.520.51              |
| GPT2-S D → D                 | 2.370.09             | 4.500.11             | 9.300.17              | 76.562.02              | 85.952.28              | 87.902.23              |
| GPT2-S P → D                 | 2.130.08             | 4.300.28             | 8.620.70              | 68.972.33              | 78.382.49              | 81.412.41              |
| GPT2-S Z → D                 | 2.340.02             | 4.370.05             | 8.840.13              | 74.311.18              | 85.190.79              | 87.660.66              |
|                              |                      |                      |                       | 79.172.12              | 87.651.83              | 89.281.69              |
| GPT2-S D → P                 | 2.400.08             | 4.600.23             | 9.690.43              |                        |                        |                        |
| GPT2-S P → P                 | 2.150.04             | 4.110.10             | 8.340.19              | 69.540.43              | 79.130.51              | 82.080.50              |
| GPT2-S Z → P                 | 2.450.05             | 5.070.36             | 10.470.57             | 79.420.94              | 88.600.93              | 90.520.79              |
| GPT2-S D → Z                 | 2.360.05             | 4.520.12             | 9.360.29              | 77.731.12              | 86.731.04              | 88.581.02              |
| GPT2-S P → Z<br>GPT2-S Z → Z | 2.170.11<br>2.350.03 | 4.220.20<br>4.970.18 | 8.650.46<br>10.250.47 | 70.472.41<br>75.920.68 | 79.942.76<br>85.660.77 | 82.952.69<br>87.760.88 |

Table 11: Full evaluation results for completions generated on prefixes sampled from CNN/Dailymail.