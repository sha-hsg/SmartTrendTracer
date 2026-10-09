# Kernelized Concept Erasure

Shauli Ravfogel1,2 Francisco Vargas<sup>3</sup> Yoav Goldberg1,2 Ryan Cotterell<sup>4</sup>

<sup>1</sup>Bar-Ilan University <sup>2</sup>Allen Institute for Artificial Intelligence <sup>3</sup>University of Cambridge <sup>4</sup>ETH Zürich

[{shauli.ravfogel,](mailto:shauli.ravfogel@gmail.com) [yoav.goldberg}](mailto:yoav.goldberg@gmail.com)@gmail.com [fav25@cam.ac.uk](mailto:fav25@cam.ac.uk) [ryan.cotterell@inf.ethz.ch](mailto:ryan.cotterell@inf.ethz.ch)

# Abstract

The representation space of neural models for textual data emerges in an unsupervised manner during training. Understanding how those representations encode human-interpretable concepts is a fundamental problem. One prominent approach for the identification of concepts in neural representations is searching for a linear subspace whose erasure prevents the prediction of the concept from the representations. However, while many linear erasure algorithms are tractable and interpretable, neural networks do not necessarily represent concepts in a linear manner. To identify non-linearly encoded concepts, we propose a kernelization of a linear maximin game for concept erasure. We demonstrate that it is possible to prevent specific non-linear adversaries from predicting the concept. However, the protection does not transfer to different non-linear adversaries. Therefore, exhaustively erasing a non-linearly encoded concept remains an open problem.

[https://github.com/shauli-ravfogel/](https://github.com/shauli-ravfogel/adv-kernel-removal) [adv-kernel-removal](https://github.com/shauli-ravfogel/adv-kernel-removal)

# 1 Introduction

Large neural networks in NLP produce real-valued representations that encode the bit of human language that they were trained on, e.g., words, sentences, or text grounded in images. For instance, GloVe [\(Pennington et al.,](#page-10-0) [2014\)](#page-10-0) produces realvalued representations of isolated words, BERT [\(Devlin et al.,](#page-9-0) [2019\)](#page-9-0) produces real-valued representations of sentences, and VilBERT produces real-valued representations of visually grounded language [\(Lu et al.,](#page-10-1) [2019;](#page-10-1) [Bugliarello et al.,](#page-9-1) [2021\)](#page-9-1). These real-valued representations naturally encode various properties of the objects they represent. For instance, a good representation of the first author's laptop computer ought to encode its manufacturer, size, and color somewhere among its real values.

We now describe the premise of our paper in more detail. We adopt the notion of a concept due to [Gärdenfors](#page-9-2) [\(2000\)](#page-9-2). For Gärdenfors, objects can be thought of as having a geometric representation. Different dimensions in the representation space that objects inhabit might correspond to their color, size, and shape. Gärdenfors then goes further and defines a concept as a convex region of the representation space.[1](#page-0-0) Building on Gärdenfors' notion of a concept, this paper studies a task that we refer to as concept erasure.

We now motivate the task more formally by extending the example. Imagine we have N different laptops, whose real-valued representations are denoted as x1, . . . , x<sup>N</sup> . Now, consider concept labels y1, . . . , y<sup>N</sup> that encode each laptop's color and are taken from the set {GREY, SILVER, BLACK, WHITE}. In the concept erasure paradigm, we seek an erasure function r(·) such that r(x1), . . . , r(x<sup>N</sup> ) are *no longer* predictive of the colors of the laptops, y1, . . . , y<sup>N</sup> , but *retain* all the other information encoded in the original representations, i.e., they remain predictive with respect to other laptop-related concepts. Our hope is that the geometry of the erasure function r(·) then tells us the structure of the laptop color concept.

Concept erasure is tightly related to concept identification. Once we have successfully removed a given concept, e.g., color, from a representation xn, it is reasonable to argue that the erasure function r has meaningfully identified the concept within the representation space. In the rest of the paper, we will say that r(·) neutralizes the concept in the representation space. For instance, we say that the r in our example neutralizes the concept of a laptop's color. It follows that concept identification is related to bias mitigation [\(Bolukbasi](#page-9-3) [et al.,](#page-9-3) [2016;](#page-9-3) [Gonen and Goldberg,](#page-9-4) [2019;](#page-9-4) [Maudslay](#page-10-2) [et al.,](#page-10-2) [2019\)](#page-10-2), e.g., one may want to identify and remove the gender encoded in learned word representations produced by an embedding method such as word2vec [\(Mikolov et al.,](#page-10-3) [2013\)](#page-10-3) or GloVe [\(Pennington et al.,](#page-10-0) [2014\)](#page-10-0). Indeed, the empirical portion of this paper will focus on removing gender

<span id="page-0-0"></span><sup>1</sup> In this work, we exclusively focus on linear subspaces, which are convex, rather than more general convex regions.

from word representations in order to mitigate bias.

Previous work on concept erasure (Ravfogel et al., 2021) focuses on the linear case, i.e., where r is a linear function. While linear concept erasure methods have certainly found success (Bolukbasi et al., 2016), there is no a-priori reason to suspect that neural networks encode concepts in a linear manner. In this work, we take the first step toward the goal of identifying a *non-linear* function  $r(\cdot)$  and a corresponding non-linearly encoded concept subspace. We directly build on Rayfogel et al. (2022), who cast linear concept erasure as a maximin game. Under their formulation, the function  $r(\cdot)$  learns to remove the concept, while an adversary tries to predict the concept. We extend their work by deriving a class of general maximin games based on kernelization that largely maintains the tractability of the linear approach. Our kernelized method performs concept erasure in a reproducing kernel Hilbert space, which may have a much higher dimensionality (Schölkopf and Smola, 2002) and correspond to a non-linear subspace of the original representation space.

Empirically, we experiment with gender erasure from GloVe and BERT representations. We show that a kernelized adversary can classify the gender of the representations with over 99% accuracy if  $r(\cdot)$  is taken to be a linear function. This gives us concrete evidence that gender is indeed encoded non-linearly in the representations. We further find that solving our kernelized maximin game yields an erasure function  $r(\cdot)$  that protects against an adversary that shares the same kernel. However, we also find that it is difficult to protect against all kernelized adversaries at once: Information removed by one kernel type can be recovered by adversaries using other kernel types. That is, the gender concept is not exclusively encoded in a space that corresponds to any one kernel. This suggests that non-linear concept erasure is very much an open problem.

### <span id="page-1-1"></span>**2** Linear Concept Erasure

We provide an overview of the linear maximin formulation before we introduce its kernelization.

#### 2.1 Notation

Let  $\mathcal{D} = \{(\boldsymbol{x}_n, y_n)\}_{n=1}^N$  be a dataset of N concept-representation pairs, where the labels  $y_n$  represent the concept to be neutralized. The goal of linear concept erasure is to learn a *linear* erasure function

 $r(\cdot)$  from  $\mathcal{D}$  such that it is impossible to predict  $y_n$  from the modified representations  $r(x_n)$ . We focus on classification, where the concept labels  $y_n$  are derived from a finite set  $\{1,\ldots,V\}$  of V discrete values, and the representations  $x_n \in \mathbb{R}^D$  are D-dimensional real column vectors. To predict the concepts labels  $y_n$  from the representations  $x_n$ , we make use of (and later kernelize) classifiers that are **linear models**, i.e., classifiers of the form  $\widehat{y}_n = \boldsymbol{\theta}^\top x_n$  where  $\boldsymbol{\theta} \in \Theta \subseteq \mathbb{R}^D$  is a column vector of parameters that lives in a compact set  $\Theta$ . We also consider an arbitrary **loss function**  $\ell(\cdot,\cdot) \geq 0$  where  $\ell(y_n,\widehat{y}_n)$  tells us how close the prediction  $\widehat{y}_n$  is to  $y_n$ .

Using this notation, linear concept erasure is realized by identifying a linear concept subspace whose neutralization, achieved through an orthogonal projection matrix, prevents the classifier from predicting the concept. We define  $\mathcal{P}_k$  as the set of all  $D \times D$  orthogonal projection matrices that neutralize a rank k subspace. More formally, we have that  $\mathbf{P} \in \mathcal{P}_k \iff \mathbf{P} = \mathbf{I}_D - \mathbf{W}^\top \mathbf{W}, \mathbf{W} \in \mathbb{R}^{K \times D}, \mathbf{W}^\top = \mathbf{I}_K$ , where  $\mathbf{I}_K$  denotes the  $K \times K$  identity matrix and  $\mathbf{I}_D$  denotes the  $D \times D$  identity matrix. We say that the matrix  $\mathbf{P}$  neutralizes the K-dimensional rowspace of  $\mathbf{W}$ .

### 2.2 A Linear Maximin Game

Following this formalization, it is natural to define a maximin game (Neumann and Morgenstern, 1944) between a projection matrix that aims to remove the concept subspace, and a linear model parameterized by  $\theta$  that aims to recover it:

<span id="page-1-0"></span>
$$\max_{\boldsymbol{P}\in\mathcal{P}_k} \min_{\boldsymbol{\theta}\in\Theta} \sum_{n=1}^N \ell\Big(y_n, \, \boldsymbol{\theta}^\top \boldsymbol{P} \boldsymbol{x}_n\Big). \tag{1}$$

Eq. (1) is a sequential game. The first player chooses an orthogonal projection matrix P to hinder the prediction of  $y_n$  from  $x_n$ . In response, the second player chooses the parameters of a linear model  $\theta$ , with knowledge of P, to best predict  $y_n$  from  $Px_n$ . This is a special case of the general adversarial framework (Goodfellow et al., 2014). However, in our case, the predictor  $\theta$  does not interact with the original input  $x_n$ . Instead, the classifier attempts to predict the concept label  $y_n$  from  $Px_n$ . We now give a concrete example of the linear concept: When we have a binary logistic loss (V = 2) and a K-dimensional neutralized

subspace, the game takes the following form:

$$\max_{\boldsymbol{P} \in \mathcal{P}_k} \min_{\boldsymbol{\theta} \in \Theta} - \left( \sum_{n=1}^N y_n \log \frac{\exp \boldsymbol{\theta}^\top \boldsymbol{P} \boldsymbol{x}_n}{1 + \exp \boldsymbol{\theta}^\top \boldsymbol{P} \boldsymbol{x}_n} + \left( 1 - y_n \right) \log \frac{1}{1 + \exp \boldsymbol{\theta}^\top \boldsymbol{P} \boldsymbol{x}_n} \right).$$
(2)

In this paper, we focus on K=1, i.e., we aim to identify a 1-dimensional concept subspace.<sup>2</sup> Every  $D \times D$  orthogonal projection matrix of rank D-1 can be written as follows

$$\boldsymbol{P}_{\boldsymbol{w}}^{\perp} \stackrel{\text{def}}{=} \boldsymbol{I} - \frac{\boldsymbol{w}\boldsymbol{w}^{\top}}{\boldsymbol{w}^{\top}\boldsymbol{w}},\tag{3}$$

itself a differentiable function of w. This results in the following game:

<span id="page-2-1"></span>
$$\max_{\boldsymbol{w} \in \mathbb{R}^D} \min_{\boldsymbol{\theta} \in \Theta} \sum_{n=1}^N \ell\left(y_n, \, \boldsymbol{\theta}^\top \boldsymbol{P}_{\boldsymbol{w}}^{\perp} \boldsymbol{x}_n\right). \tag{4}$$

## <span id="page-2-4"></span>3 Non-linear Concept Erasure

It has often been shown that human-interpretable concepts, and in particular gender, are encoded non-linearly in the representation space (Gonen and Goldberg, 2019; Ravfogel et al., 2020). However, prior work on concept erasure, e.g., the method discussed in §2, assumes that concepts are encoded linearly. Our goal is to extend the game defined in Eq. (4) to be able to neutralize non-linearly encoded concepts while preserving the relative tractability and interpretability of the linear methods. A natural manner through which we can achieve these goals is by kernelization (Shawe-Taylor and Cristianini, 2004; Hofmann et al., 2008).

The underlying assumption motivating kernel methods is that the features needed for the task live in a reproducing kernel Hilbert space (RKHS; Aronszajn, 1950). At an intuitive level, an RKHS allows us to extend some of results from linear algebra to potentially infinite-dimensional inner product spaces (Canu and Smola, 2006). The main technical contribution of this paper is the derivation of a kernelized version of the linear adversarial game presented in Eq. (4). We perform this derivation in this section after providing some background on kernel methods. We show that the resulting kernelized game is both non-convex and too computationally heavy to solve directly. Thus,

we introduce a Nyström approximation that results in an efficient and light-weight formulation, given in Eq. (10), that is still able to isolate concepts encoded non-linearly.

### 3.1 Background: Kernel Methods

Kernel methods are based on reproducing kernel Hilbert spaces (RKHS). Without going into the technical details, an RKHS is a space of "nice" functions equipped with a kernel (Yosida, 2012). A **kernel**  $\kappa(\cdot,\cdot) > 0$  is a similarity measure that generalizes the notion of a positive definite matrix. When we have a kernel over an RKHS, the kernel corresponds to the dot product of a feature map, i.e.,  $\kappa(x,y) = \Phi(x)^{\top}\Phi(y)$ , for feature map  $\Phi$ . This insight gives us a natural manner to construct kernels. For instance, the linear kernel  $\kappa(\boldsymbol{x}, \boldsymbol{y}) = \boldsymbol{x}^{\top} \boldsymbol{y}$  corresponds to the standard dot product in Euclidean space. The degree-2 polynomial kernel  $\kappa(\boldsymbol{x}, \boldsymbol{y}) = (\gamma \boldsymbol{x}^{\top} \boldsymbol{y} + \alpha)^2$  corresponds to a dot product in a six-dimensional feature space if  $x, y \in \mathbb{R}^2$  where  $\gamma \in \mathbb{R}$  is a hyperparameter.

Kernels are more general than positive definite matrices in that they can exist in infinite-dimensional spaces. For example, the Gaussian kernel  $\exp\left(-\gamma||\boldsymbol{x}-\boldsymbol{y}||_2^2\right)$  is infinite-dimensional, where, again,  $\gamma \geq 0$  is a hyperparameter. However, for any finite set of points  $\{\boldsymbol{x}_1,\ldots,\boldsymbol{x}_N\}$ , we can construct a **Gram matrix**  $\boldsymbol{K} \in \mathbb{R}^{N \times N}$  where  $\boldsymbol{K}^{(m,n)} = \kappa(\boldsymbol{x}_n,\boldsymbol{x}_m)$  encodes the similarity between  $\boldsymbol{x}_n$  and  $\boldsymbol{x}_m$ . The matrix  $\boldsymbol{K}$  is guaranteed to be positive definite. Kernels are useful because they allow us to implicitly learn functions in a potentially infinite-dimensional RKHS without materializing that space.

### 3.2 A Kernelized Maximin Game

Inspection of the maximin game in Eq. (1) reveals that both the adversary and the predictor interact with the input only via an inner product. Thus, the game can be kernelized by replacing the inner product with a kernel operation. We establish this kernelization by first proving the following representer theorem-like lemma, which shows that w and  $\theta$ , now considered to live an RKHS  $\mathcal{H}$ , can be written in terms of spans of the projected training set.

<span id="page-2-3"></span>**Lemma 1.** (Maximin Game Representer Theorem) Let  $\mathcal{H}$  be a reproducing kernel Hilbert space with canonical feature map  $\Phi \colon \mathbb{R}^D \to \mathcal{H}$ , i.e.,  $\Phi(\mathbf{x}) =$ 

<span id="page-2-0"></span> $<sup>^2</sup>$ This construction can be extended to subspaces of dimension k>1 using a version of the Gram–Schmidt process in the RKHS.

<span id="page-2-2"></span> $<sup>^{3}</sup>$ One way to see this is to show a Gram matrix of any size N will always have full rank.

 $\kappa(\mathbf{x},\cdot)$ . Consider the following maximin game:

$$\max_{\boldsymbol{w} \in \mathcal{H}} \min_{\boldsymbol{\theta} \in \mathcal{H}} \sum_{n=1}^{N} \ell\left(y_n, \langle \boldsymbol{\theta}, P_{\boldsymbol{w}}^{\perp} \boldsymbol{\Phi}(\boldsymbol{x}_n) \rangle\right). \quad (5)$$

where  $P_{\boldsymbol{w}}^{\perp} \colon \mathcal{H} \to \mathcal{H}$  is the operator that projects onto the orthogonal complement of  $\boldsymbol{w}$ . For every attained local optimum  $(\boldsymbol{\theta}^{\star}, \boldsymbol{w}^{\star})$  of Eq. (5), there is another local optimum  $(\boldsymbol{\theta}^{\star}_{U}, \boldsymbol{w}^{\star}_{U})$  with the same value as  $(\boldsymbol{\theta}^{\star}, \boldsymbol{w}^{\star})$  in  $U \stackrel{\text{def}}{=} \operatorname{span} \left\{ \boldsymbol{\Phi}(\mathbf{x}_{1}), \ldots, \boldsymbol{\Phi}(\mathbf{x}_{N}) \right\}$ , the span of the training data.

Having expressed  $(w, \theta)$  as a function of the training data, we can proceed to proving the kernelization of the adversarial game.

<span id="page-3-2"></span>**Lemma 2.** Let  $\mathcal{H}$  be a reproducing kernel Hilbert space with canonical feature map  $\Phi$ , and let  $\Phi(z)$  be a point in  $\mathcal{H}$ . Next, let  $\mathbf{w} = \sum_{n=1}^{N} \alpha_n \Phi(\mathbf{x}_n)$  and  $\theta = \sum_{n=1}^{N} \beta_n \Phi(\mathbf{x}_n)$  be points in the reproducing kernel Hilbert space. Now, let  $\Phi_{proj}(z)$  be the orthogonal projection of  $\Phi(z)$  onto the orthogonal complement of the subspace spanned by  $\mathbf{w}$ . Then, we have

$$\begin{align} \langle \boldsymbol{\theta}, \Phi_{proj}(\boldsymbol{z}) \rangle &= \sum_{m=1}^N \beta_m \bigg( \kappa(\boldsymbol{x}_m, \boldsymbol{z}) \ &- \frac{\boldsymbol{\alpha}^{\top} \boldsymbol{K}^{(m)}(\boldsymbol{z}) \boldsymbol{\alpha}}{\boldsymbol{\alpha}^{\top} \boldsymbol{K} \boldsymbol{\alpha}} \bigg), \end{align}$$

where  $\boldsymbol{K}_{ij}^{(m)}(\boldsymbol{z}) \stackrel{\text{def}}{=} \kappa(\boldsymbol{x}_i, \boldsymbol{z}) \kappa(\boldsymbol{x}_m, \boldsymbol{x}_j).$ 

*Proof.* See App. A.2 for the proof.

Lemma 2 suggests the following form of the kernelized game given in Eq. (5):

<span id="page-3-3"></span>
$$\max_{\boldsymbol{\alpha} \in \mathbb{R}^{N}} \min_{\boldsymbol{\beta} \in \mathbb{R}^{N}} \sum_{n=1}^{N} \ell \left( y_{n}, \sum_{m=1}^{N} \beta_{m} \left( \kappa(\boldsymbol{x}_{m}, \boldsymbol{z}_{n}) - \frac{\boldsymbol{\alpha}^{\top} \boldsymbol{K}^{(m,n)} \boldsymbol{\alpha}}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \right) \right), \tag{7}$$

where we define  $K_{ij}^{(m,n)}(z) \stackrel{\text{def}}{=} \kappa(x_i, z_n)\kappa(x_m, x_j)$ . In contrast to Eq. (5), all computations in Eq. (7) are in Euclidean space.

**Theorem 1.** The reproducing kernel Hilbert space game Eq. (5) attains the same local optima as Eq. (7).

<span id="page-3-0"></span>*Proof.* First, plug the result of Lemma 2 into Eq. (5). Optimality follows by Lemma 1, the representer lemma.

Now, we turn to the runtime of the game.

<span id="page-3-4"></span>**Proposition 1.** The objective in Eq. (7) can be computed in  $\mathcal{O}(N^4)$  time.

*Proof.* Assuming that  $\kappa(\cdot,\cdot)$  may be computed in  $\mathcal{O}(1)$ , computing  $\boldsymbol{K}^{(m,n)}$  takes  $\mathcal{O}(N^2)$  time. We have to do  $\mathcal{O}(N^2)$  such computations, which results in  $\mathcal{O}(N^4)$  time. Note that K may be pre-computed once in  $\mathcal{O}(N^2)$  time. Thus,  $\boldsymbol{K}^{(m,n)}$  is the bottleneck, so the whole algorithm takes  $\mathcal{O}(N^4)$  time.

There are two problems with naïvely using the formulation in Eq. (7). First, and similarly to Eq. (1), directly optimizing Eq. (7) is difficult because the parameters  $\alpha$  implicitly define an orthogonal projection matrix of rank 1 and, thus, we face the sample problems discussed in Ravfogel et al. (2022). Second, the evaluation time of Eq. (7) is  $\mathcal{O}\left(N^4\right)$ , as argued in Proposition 1, which makes using a training set larger than a few hundred examples infeasible. We solve both of these computational issues with the Nyström approximation.

## 3.3 The Nyström Approximation

The general idea behind the Nyström method (Nyström, 1930) is to calculate a low-rank approximation of the kernel matrix. It is a commonly used technique for improving the runtime of kernel methods (Williams and Seeger, 2000).

#### 3.3.1 Relaxing the Objective

Consider the Gram matrix  $K \in \mathbb{R}^{N \times N}$  where  $K^{(m,n)} = \kappa(x_m,x_n)$ ,  $x_m$  is the  $m^{\text{th}}$  training representation, and  $x_n$  is the  $n^{\text{th}}$  training representation. We start with the eigendecomposition of  $K = U\Sigma U^{\top} = U\sqrt{\Sigma}\sqrt{\Sigma}U^{\top}$ , which can be computed in  $\mathcal{O}\left(N^3\right)$  time (Golub and Van Loan, 2013). We are justified in taking the square root of  $\Sigma$  because K is necessarily positive definite. Now, we define an approximate feature map for observations  $x_n$  in the training data using the eigenvalues and vectors:

<span id="page-3-5"></span>
$$\widetilde{\Phi}(\boldsymbol{x}_n) \stackrel{\text{def}}{=} \left( \boldsymbol{U} \sqrt{\Sigma} \right)_n$$
 (8)

<span id="page-3-1"></span><sup>&</sup>lt;sup>4</sup>Traditionally, a representer theorem has an extra regularization term on the function estimator that ensures the optimum is attained and that it is global (Kimeldorf and Wahba, 1970). We do not employ such a regularizer and, thus, have a weaker result.

To compute the features for representations x not in the training data, we use the following:

$$\widetilde{\mathbf{\Phi}}(\mathbf{x}) \stackrel{\text{def}}{=} \sum_{n=1}^{N} \kappa(\mathbf{x}, \mathbf{x}_n) \widetilde{\mathbf{\Phi}}(\mathbf{x}_n)$$
(9)

which is an average, weighted by the kernel  $\kappa(\cdot, \cdot)$ , of the features obtained during training. Plugging Eq. (8) into Eq. (4) yields:

<span id="page-4-0"></span>
$$\max_{\boldsymbol{w} \in \mathbb{R}^{D}} \min_{\boldsymbol{\theta} \in \Theta} \sum_{n=1}^{N} \ell \Big( y_{n}, \langle \boldsymbol{\theta}, \boldsymbol{P}_{\boldsymbol{w}}^{\perp} \widetilde{\boldsymbol{\Phi}}(\boldsymbol{x}_{n}) \rangle \Big)$$
 (10)

which is identical to the linear game in Eq. (4), except that it uses the transformed features  $\widetilde{\Phi}(x_n)$  to approximate the true feature map  $\Phi$ .

While neither the game in Eq. (4) nor the version of Eq. (4) with the Nyström approximation given in Eq. (10) is convex—concave, we are still able to approximately solve the game in practice. Specifically, we consider the convex relaxation of the set of rank-K orthogonal projection matrices given by Ravfogel et al. (2022). Then, after applying the relaxation, we apply a gradient-based optimization procedure. The runtime of this procedure for this game over T epochs is now  $\mathcal{O}\left(TN^2+N^3\right)$ . While this is an improvement over  $\mathcal{O}\left(TN^4\right)$ , it is still not fast enough to be of practical use.

### 3.3.2 Improving the Runtime

The runtime bottleneck of the game in Eq. (10) is the  $\mathcal{O}(N^3)$  time it takes to compute the eigendecomposition of the Gram matrix K. Under the assumption that rank(K) = L, we can improve this bound to  $\mathcal{O}\left(L^3 + L^2N\right)$  (Drineas and Mahoney, 2005). For the case that  $L \ll N$ , this is a substantial improvement. Moreover, it implies that the approximation feature map  $\Phi(x_n) \in \mathbb{R}^L$ . After T steps of optimization, the runtime is now  $\mathcal{O}(TL^2 + L^3 + L^2N)$ , which is fast enough to be useful in practice. A natural question to ask is what happens if we apply the Nyström approximation, thereby assuming rank (K) = L, but in practice rank(K) > L? In this case, we are effectively computing a low-rank approximation of the kernel matrix. Several bounds on the accuracy of this approximation have been proven in the literature (Drineas and Mahoney, 2005; Jin et al., 2013; Nemtsov et al., 2016); we refer the reader to these works for more details on the approximation error.

### 3.4 Pre-image Mapping

After solving the game in Eq. (10), we obtain a projection matrix P that neutralizes the concept *inside* an (approximated) RKHS. In other words, we have a function  $r(\cdot)$  that prevents a classifier from predicting a concept label from the representation  $\widetilde{\Phi}(x_n)$ . However, for many applications, we want a version of the input  $x_n$  in the original space with the concept neutralized, i.e., we want  $r(x_n)$ . Neutralization in the original space requires solving the **pre-image problem** (Mika et al., 1998). In the case of Nyström features, we seek a mapping from feature space back to the original Euclidean space, i.e., a mapping from  $\mathbb{R}^L$  to  $\mathbb{R}^D$ , that projects the neutralized features back into the input space.

In practice, this task can also be performed via a mapping from  $\mathbb{R}^D \mapsto \mathbb{R}^D$ , which learns to reproduce in the input space the transformation that P performs in the RKHS. We choose the latter approach, and train a multilayer perceptron (MLP)  $f_{\lambda}(\cdot) \colon \mathbb{R}^D \to \mathbb{R}^D$ . To estimate the parameters  $\lambda$  of the MLP  $f_{\lambda}(\cdot)$ , we optimize a two-termed objective over all points  $x_n$ :

<span id="page-4-3"></span>
$$\underset{\lambda \in \Lambda}{\operatorname{argmin}} \left\| \left| \mathbf{P} \widetilde{\mathbf{\Phi}}(\boldsymbol{x}_n) - \widetilde{\mathbf{\Phi}}(f_{\lambda}(\boldsymbol{x}_n)) \right| \right\|_{2}^{2} + \left\| \left| (\boldsymbol{I} - \boldsymbol{P}) \widetilde{\mathbf{\Phi}}(f_{\lambda}(\boldsymbol{x}_n)) \right| \right\|_{2}^{2}$$

where  $\Lambda$  is the parameter space. The first term encourages  $f_{\lambda}(\cdot)$  to perform the same transformation in the input space as  $\boldsymbol{P}$  does in the RKHS. The second term ensures that  $\boldsymbol{P}$  has no effect on the RKHS features computed on the neutralized  $f_{\lambda}(\boldsymbol{x}_n)$ .

## 4 Experimental Setup

In §3, we established an algorithm that allows us to attempt kernelized concept erasure of non-linearly encoded concepts. To summarize, this method requires first solving the game in Eq. (10) for a chosen neutralizing kernel, then training a pre-image network according to Eq. (11) to obtain neutralized representations in the input space.

We hypothesize that a non-linearly encoded concept can be exhaustively removed after mapping into the right RKHS. In order for this to hold, the neutralized representations must satisfy two conditions: Adversaries using non-linear classifiers should not be able to predict the erased concept

<span id="page-4-1"></span><sup>&</sup>lt;sup>5</sup>Calculating the Nyström features entails computing the eigendecomposition of the Gram matrix, which is  $\mathcal{O}\left(N^3\right)$ . Then, we calculate the objective over all N examples for T epochs, which is  $\mathcal{O}\left(TN^2\right)$ .

<span id="page-4-2"></span><sup>&</sup>lt;sup>6</sup>This mapping may not always be a function because there may be more than one point in the RKHS that corresponds to a point in the original space.

from these representations, and these representations should preserve all other information encoded in them prior to erasure. With binary gender as our non-linearly encoded concept, we conduct several experiments testing both conditions. Before presenting our results, we lay out our experimental setup (see App. [A.3](#page-15-0) for more details).

Data. We run our main experiments on the identification and erasure of binary gender in static GloVe representations [\(Pennington et al.,](#page-10-0) [2014\)](#page-10-0). We focus on [Ravfogel et al.'](#page-10-8)s [\(2020\)](#page-10-8) dataset, where word representations are coupled with binary labels indicating whether they are male-biased or femalebiased. As a preprocessing step, we normalize the GloVe representations to have unit norm. For an extrinsic evaluation of our method on a main task (profession prediction), we use the Bias-in-Bios dataset of [De-Arteaga et al.](#page-9-9) [\(2019\)](#page-9-9), which consists of a large set of short biographies annotated for both gender and race. Following [Ravfogel et al.](#page-10-5) [\(2022\)](#page-10-5), we embed each biography using the [CLS] representation of pre-trained BERT.

Kernels. We consider the following kernels:

- Poly : κ(x, y) = (γx <sup>⊤</sup>y + α) d
- RBF : κ(x, y) = exp −γ||x − y||<sup>2</sup> 2
- Laplace : κ(x, y) = exp (−γ||x − y||1)
- Linear : κ(x, y) = x <sup>⊤</sup>y
- Sigmoid : κ(x, y) = tanh(γx <sup>⊤</sup>y + α)
- Multiple : a convex combination of the above kernels. We consider the following two methods for combining kernels:
  - EasyMKL : a convex combination learned with the EasyMKL algorithm [\(Aiolli and](#page-9-10) [Donini,](#page-9-10) [2015\)](#page-9-10) targeted for gender prediction.[7](#page-5-0)
  - UniformMK : a uniform combination of all kernels.

We experiment with different values for the hyperparameters γ > 0, α > 0 and d > 0 (see App. [A.3](#page-15-0) for details). We use L = 1024-dimensional vectors for the Nyström approximation.

Reported metrics. Each result is reported as the mean ± standard deviation, computed across four runs of the experiment with random restarts.

Solving the maximin game. We solve the relaxed adversarial game given in Eq. [\(10\)](#page-4-0) by alternate gradient-based optimization [\(Goodfellow](#page-10-15) [et al.,](#page-10-15) [2016\)](#page-10-15). Concretely, we alternate between updating the predictor's parameters θ and the projection matrix P . Updates to θ are performed with gradient descent, and updates to P are performed with gradient *ascent*, including a projection onto the Fantope to ensure that the constraint is met. For the Fantope projection step, we use [Vu et al.'](#page-11-4)s [\(2013\)](#page-11-4) algorithm, the details of which are restated in [Ravfogel et al.](#page-10-5) [\(2022\)](#page-10-5).

Pre-image calculation. As our pre-image network fλ(·), we use an MLP with two hidden layers of sizes 512 and 300, respectively. We use layer normalization after each hidden layer and ReLU activations. See App. [A.3.1](#page-16-0) for basic empirical validation of the pre-image calculation procedure.

# 5 Effect on Concept Encoding

In this section, we pose the exhaustive RKHS hypothesis: The hypothesis that binary gender can be *exhaustively* removed when the representations are mapped into the right RKHS. That is, there exists a unique kernel such that, for any choice of non-linear predictor, the adversary cannot recover gender information from the pre-image representations obtained via our special kernel. As a baseline, we note that gender prediction accuracy on the original representations, prior to any intervention, is above 99% with *every* kernel, including the linear kernel. This means that the gender concept is linearly separable in the original input space. In this context, we conduct the following experiments on gender neutralization.

Same adversary. We start by calculating the neutralized pre-images for each kernel type, and then apply the same kernel adversary to recover gender information. This experiment tests whether we can protect against the same kernel adversary.

Transfer between kernels. To directly test the exhaustive RKHS hypothesis, we calculate the neutralized pre-image representations with respect to a neutralizing kernel, and then use a different adversarial kernel to recover gender. For instance, we calculate neutralized pre-image representations with respect to a polynomial kernel, and then predict gender using a Laplace kernel, or a polynomial kernel with different hyperparameters.

<span id="page-5-0"></span><sup>7</sup>We use the implementation of [MKLpy](https://github.com/IvanoLauriola/MKLpy) with the default parameters.

<span id="page-6-0"></span>

| Type      | Accuracy       |
|-----------|----------------|
| Poly      | 0.59 ±<br>0.15 |
| RBF       | 0.69 ±<br>0.16 |
| Laplace   | 0.75 ±<br>0.11 |
| Linear    | 0.54 ±<br>0.02 |
| Sigmoid   | 0.49 ±<br>0.00 |
| EasyMKL   | 0.69 ±<br>0.01 |
| UniformMK | 0.49 ±<br>0.00 |

Table 1: Gender prediction accuracy from the neutralized pre-image representations when using the same kernel for neutralization and recovery. Numbers are averages over hyperparameters of each kernel and over four randomized runs of the experiment.

Biased associations. Gender can manifest itself in the pre-image representations via biased associations, even when gender is neutralized according to our adversarial test. To assess the impact of our intervention on this notion of gender encoding, we run the WEAT test [\(Islam et al.,](#page-10-16) [2017\)](#page-10-16) on the neutralized pre-image representations.

## 5.1 Pre-image Recovery: Same Adversary

In Table [1,](#page-6-0) we report average gender prediction accuracy on the neutralized pre-images for the case where the neutralizing and adversarial kernels are of the same type and share the same hyperparameters.[8](#page-6-1) Numbers are averages over the results of all hyperparameter values of each kernel. See App. [A.4](#page-17-0) for the full results. As can be seen, for most—but not all—kernels, we effectively hinder the ability of the non-linear classifier to predict gender.

### <span id="page-6-2"></span>5.2 Pre-image Recovery: Kernel Transfer

In Table [2,](#page-7-0) we report average gender prediction accuracy on the neutralized pre-images for the case where the neutralizing and adversarial kernels are different. Numbers are averages over several different hyperparameter settings for the neutralizing kernel, while the adversarial kernel hyperparameters are fixed as detailed in App. [A.7.](#page-21-0) Also, see the appendix for a full breakdown by neutralizing kernel hyperparameters. Table [2](#page-7-0) allows us to test the exhaustive RKHS hypothesis. Under this hypothesis, we would expect to see that for at least one neutralizing kernel, no non-linear classifers are

able to accurately recover gender. For a thorough test of the hypothesis, we introduce an MLP with a single hidden layer as an additional adversary.

Remarkably, we observe a complete lack of generalization of our concept erasure intervention to other types of non-linear predictors. In particular, no neutralizing kernel significantly hinders the ability of an MLP with a single hidden layer to predict gender: the MLP always recovers the gender labels with an accuracy of 97%. Furthermore, concept erasure does not transfer between different kernel types, and even between kernels of the same family with different hyperparameter settings. For instance, when using a polynomial neutralizing kernel, we protect against a polynomial adversarial kernel with the same parameters (mean accuracy of 59% in Table [1\)](#page-6-0), but not against a polynomial adversarial kernel with different hyperparameters (98% mean accuracy for Poly in Table [2\)](#page-7-0).

We do see transfer to sigmoid, and—to a lesser degree—linear kernel adversaries, with a classification accuracy of 54–65% for the linear adversary, and 49% for the sigmoid adversary. Surprisingly, the sigmoid kernel seems weaker than the linear kernel, achieving a near-random accuracy of 49%. The results do not show evidence of a proper hierarchy in the expressiveness of the different kernels, and convex combinations of the different kernels—either learned (EasyMKL) or uniform (UniformMK)—do not provide better protection than individual kernels.

In short, while we are able to effectively protect against the same kernel, transfer to different kernels is non-existent. This result does not support the exhaustive RKHS hypothesis: We do not find a single RKHS that exhaustively encodes the binary gender concept.

# 5.3 Effect on Gendered Word Associations

In the case where the concept of gender cannot be recovered by an adversary, binary gender could still manifest itself in more subtle ways. For instance, it may be the case that the names of gender-biased professions, such as STEM fields, are closer in representation space to male-associated words than to female-associated words. We aim to measure the extent to which our neutralized pre-image representations exhibit this measure of gender bias.

Evaluation. To quantify bias associations, [Islam](#page-10-16) [et al.](#page-10-16) [\(2017\)](#page-10-16) propose the WEAT word association test. This test measures WEAT's d, a statistic that

<span id="page-6-1"></span><sup>8</sup>We use the Nyström approximation for neutralization, but predict gender from the pre-image representations using SVM classifiers that use the true kernel.

<span id="page-7-0"></span>

|           | Poly            | RBF             | Laplace         | Linear          | Sigmoid         | EasyMKL         | UniformMK       | MLP             |
|-----------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|
| Poly      | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.93 \pm 0.00$ | $0.55 \pm 0.01$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.49 \pm 0.00$ | $0.97 \pm 0.00$ |
| RBF       | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.93\pm0.00$   | $0.59 \pm 0.02$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.49 \pm 0.00$ | $0.97 \pm 0.00$ |
| Laplace   | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.94 \pm 0.00$ | $0.61 \pm 0.01$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.59 \pm 0.02$ | $0.97 \pm 0.00$ |
| Linear    | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.93\pm0.00$   | $0.54 \pm 0.02$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.49 \pm 0.00$ | $0.97 \pm 0.00$ |
| Sigmoid   | $0.98 \pm 0.00$ | $0.93 \pm 0.01$ | $0.89 \pm 0.01$ | $0.65 \pm 0.03$ | $0.49 \pm 0.00$ | $0.97 \pm 0.00$ | $0.64 \pm 0.03$ | $0.97 \pm 0.00$ |
| EasyMKL   | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.94 \pm 0.00$ | $0.57 \pm 0.03$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.49 \pm 0.00$ | $0.97 \pm 0.00$ |
| UniformMK | $0.98\pm0.00$   | $0.96\pm0.00$   | $0.94\pm0.01$   | $0.58 \pm 0.08$ | $0.49 \pm 0.00$ | $0.98\pm0.00$   | $0.49 \pm 0.00$ | $0.97\pm0.00$   |

Table 2: Evaluation of the neutralized pre-image representations when using a different kernel for neutralization and recovery. The neutralizing kernel is presented in the rows, and the kernel adversary used for recovery in the columns. Note that on the diagonal, the *hyperparameters* of the same kernel family differ between the neutralizing kernel and the adversary that recovers gender form the pre-image representations. See App. A.7 for a breakdown by neutralizing kernel hyperparameters and for details on the hyperparameters of the kernel adversaries.

<span id="page-7-2"></span>

| Kernel    | WEAT's $\boldsymbol{d}$ | WEAT's $p$ -value |
|-----------|-------------------------|-------------------|
| Poly      | $0.74 \pm 0.01$         | $0.08 \pm 0.00$   |
| RBF       | $0.74 \pm 0.00$         | $0.08 \pm 0.00$   |
| Laplace   | $0.71 \pm 0.03$         | $0.09 \pm 0.01$   |
| Linear    | $0.74 \pm 0.00$         | $0.08 \pm 0.00$   |
| Sigmoid   | $0.75\pm0.02$           | $0.08 \pm 0.01$   |
| EasyMKL   | $0.73\pm0.00$           | $0.08 \pm 0.00$   |
| UniformMK | $0.73\pm0.00$           | $0.08 \pm 0.00$   |
| Original  | 1.56                    | 0.000             |

Table 3: WEAT results on pre-image representations. Numbers are averages over hyperparameters of each kernel.

quantifies the difference in similarity between two sets of gendered words (e.g., male first names and female first names) and two sets of potentially biased words (e.g., stereotypically male and stereotypically female professions). We repeat the experiments of Gonen and Goldberg (2019) and Ravfogel et al. (2020). Following Gonen and Goldberg (2019), we represent the male and female groups with names commonly associated with males and females, rather than with explicitly gendered words (e.g., pronouns). Three tests evaluate the association between name groups and i) career and family-related words; ii) art and mathematicsrelated words; and iii) names of artistic and scientific fields. Successful neutralization of gender would imply that these word groups are less closely associated in the pre-image representations.

**Results.** In Table 3, we report the test statistic and the *p*-value for the third test using the

names of scientific and artistic fields to represent gender-biased words. <sup>10</sup> For all kernels, we observe a significant drop in the test statistic, from the original value of 1.56 to around 0.74. This suggests that the intervention significantly decreases the association between female and male names and stereotypically biased words. Notably, the reduction is similar for *all* kernels, including the linear one. While non-linear erasure is more effective in neutralizing gender against adversarial recovery, linear and non-linear methods perform equally well according to this bias association test. This finding highlights the importance of measuring different manifestations of a concept when using concept neutralization as a bias mitigation method.

### **6** Negative Impact on the Representations

Our method has shown a satisfactory ability to prevent the same kernel from recovering the However, does erasure remove too much information?<sup>11</sup> As previously stated, our intervention should erase a concept without altering any of the other information encoded in the original representations. In this section, we evaluate whether the non-gender related semantic content of the original representations is preserved in our neutralized pre-images. We do so via the following tests: i) an intrinsic evaluation of the semantic content of the neutralized pre-image word representation space, and ii) an extrinsic evaluation of our method when applied to contextualized word representations for a profession prediction task, measuring the extent to which we hinder a model's ability to perform the main task.

<span id="page-7-1"></span><sup>&</sup>lt;sup>9</sup>It asks, for example, whether the degree to which male first names are closer to scientific terms versus artistic terms is significantly different from the same quantity calculated for female first names.

<span id="page-7-3"></span> $<sup>^{10}\</sup>mathrm{See}$  App. A.6 for results of the other two biased word association tests.

<span id="page-7-4"></span><sup>&</sup>lt;sup>11</sup>It is trivial to neutralize a concept by completely zeroing out the representations.

# 6.1 Intrinsic Evaluation of Damage to Semantic Content

To measure the influence of our method on the semantics encoded in the representation space, we use SimLex-999 [\(Hill et al.,](#page-10-17) [2015\)](#page-10-17), an annotated dataset of word pairs with human similarity scores for each pair. First, we calculate the cosine similarity between the representations of each pair of words using the original representations. Then, we repeat this calculation for each type of kernel using the pre-image representations. Finally, we measure the correlation between the similarity of words in representation space and human similarity scores, before and after intervention. The original correlation is 0.400, and it is left nearly unchanged by *any* of the kernel interventions, yielding values between 0.387 and 0.396. To qualitatively demonstrate the absence of negative impact, we show in App. [A.5](#page-18-0) that the nearest neighbors of randomly sampled words do not change significantly after gender erasure.

# 6.2 Extrinsic Evaluation on Contextualized Representations

The previous experiments focused on the influence of concept neutralization on uncontextualized representations. Here, we apply our concept neutralization method on contextualized BERT representations and assess its effect on profession prediction. We embed each biography in the dataset of [De-Arteaga et al.](#page-9-9) [\(2019\)](#page-9-9) using the [CLS] representation of pre-trained BERT, and apply our method using only the RBF kernel. After collecting the preimage representations, we train a linear classifier on the main task of profession prediction.

Results. Averaged over different hyperparameter settings of the RBF kernel, we achieve a profession prediction accuracy after neutralization of 74.19±0.056%. For reference, prediction accuracy using the original BERT representations is 76.93%. This suggests that the pre-images still encode most of the profession information, which is largely orthogonal to the neutralized gender information.

# 7 Discussion

We have demonstrated that in the case where the neutralizing kernel and the adversarial kernel are the same, we are able to neutralize a non-linearly encoded concept reasonably well. We have also shown that our method neutralizes gender in a comprehensive manner, without damaging the representation. However, this neutralization does not transfer to different non-linear adversaries, which are still able to recover gender.

While the lack of transfer to other non-linear predictors may seem surprising, one should keep in mind that changing the kernel type, or changing kernel hyperparameters, results in a different implicit feature mapping. Even the features defined by a linear kernel are not a proper subset of the features defined by a polynomial kernel of degree 2.[12](#page-8-0) As such, removing the features which make the concept of interest linearly separable in one RKHS does not necessarily prevent a classifier parameterized by another kernel or an MLP from predicting the concept. In the context of gender erasure, these results suggest that protection against a diverse set of non-linear adversaries remains an open problem.

# 8 Conclusion

We propose a novel method for the identification and erasure of non-linearly encoded concepts in neural representations. We first map the representations to an RKHS, before identifying and neutralizing the concept in that space. We use our method to empirically assess the exhaustive RKHS hypothesis: We hypothesize that there exists a unique kernel that exhaustively identifies the concept of interest. We find that while we are able to protect against a kernel adversary of the same type, this protection does not transfer to different non-linear classifiers, thereby contradicting to the RKHS hypothesis. Exhaustive concept erasure and protection against a diverse set of non-linear adversaries remains an open problem.

# Limitations

The empirical experiments in this work involve the removal of binary gender information from pretrained representations. We note the fact that gender is a non-binary concept as a major limitation of our work. This task may have real-world applications, in particular relating to fairness. We would encourage readers to be careful when attempting to deploy methods such as the one discussed in this paper. Regardless of any proofs, one should carefully measure the effectiveness of the approach in the context in which it is to be deployed. Please

<span id="page-8-0"></span><sup>12</sup>Features defined by a linear kernel can be a proper subset of the features defined by a polynomial kernel if there is a fixed coordinate in all examples prior to the kernel mapping.

consider, among other things, the exact data to be used, the fairness metrics under consideration, and the overall application.

We urge practitioners not to regard this method as a solution to the problem of bias in neural models, but rather as a preliminary research effort toward mitigating certain aspects of the problem. Unavoidably, the datasets we use do not reflect all the subtle and implicit ways in which gender bias is manifested. As such, it is likely that different forms of bias still exist in the representations following the application of our method.

# Ethical Concerns

We do not foresee ethical concerns with this work.

# Acknowledgements

The authors sincerely thank Clément Guerner for his thoughtful and comprehensive comments and revisions to the final version of this work. This project received funding from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation program, grant agreement No. 802774 (iEXTRACT). Ryan Cotterell acknowledges Google for support from the Research Scholar Program.

# References

- <span id="page-9-10"></span>Fabio Aiolli and Michele Donini. 2015. [EasyMKL: a](https://www.sciencedirect.com/science/article/pii/S0925231215003653) [scalable multiple kernel learning algorithm.](https://www.sciencedirect.com/science/article/pii/S0925231215003653) *Neurocomputing*, 169:215–224.
- <span id="page-9-15"></span>M. A. Aizerman, E. A. Braverman, and L. Rozonoer. 1964. [Theoretical foundations of the potential func](https://cs.uwaterloo.ca/~y328yu/classics/kernel.pdf)[tion method in pattern recognition learning.](https://cs.uwaterloo.ca/~y328yu/classics/kernel.pdf) *Automation and Remote Control*, 25(6):917–936.
- <span id="page-9-5"></span>Nachman Aronszajn. 1950. [Theory of reproducing ker](https://www.ams.org/journals/tran/1950-068-03/S0002-9947-1950-0051437-7/)[nels.](https://www.ams.org/journals/tran/1950-068-03/S0002-9947-1950-0051437-7/) *Transactions of the American Mathematical Society*, 68(3):337–404.
- <span id="page-9-3"></span>Tolga Bolukbasi, Kai-Wei Chang, James Y. Zou, Venkatesh Saligrama, and Adam T. Kalai. 2016. [Man](https://proceedings.neurips.cc/paper/2016/file/a486cd07e4ac3d270571622f4f316ec5-Paper.pdf) [is to computer programmer as woman is to home](https://proceedings.neurips.cc/paper/2016/file/a486cd07e4ac3d270571622f4f316ec5-Paper.pdf)[maker? Debiasing word embeddings.](https://proceedings.neurips.cc/paper/2016/file/a486cd07e4ac3d270571622f4f316ec5-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 29.
- <span id="page-9-1"></span>Emanuele Bugliarello, Ryan Cotterell, Naoaki Okazaki, and Desmond Elliott. 2021. [Multimodal pretraining](https://doi.org/10.1162/tacl_a_00408) [unmasked: A meta-analysis and a unified framework](https://doi.org/10.1162/tacl_a_00408) [of vision-and-language BERTs.](https://doi.org/10.1162/tacl_a_00408) *Transactions of the Association for Computational Linguistics*, 9:978– 994.
- <span id="page-9-6"></span>Stéphane Canu and Alex Smola. 2006. [Kernel methods](https://alex.smola.org/papers/2005/CanSmo05.pdf) [and the exponential family.](https://alex.smola.org/papers/2005/CanSmo05.pdf) *Neurocomputing*, 69(7- 9):714–720.

- <span id="page-9-13"></span>Hande Celikkanat, Sami Virpioja, Jörg Tiedemann, and Marianna Apidianaki. 2020. [Controlling the imprint](https://doi.org/10.18653/v1/2020.blackboxnlp-1.13) [of passivization and negation in contextualized repre](https://doi.org/10.18653/v1/2020.blackboxnlp-1.13)[sentations.](https://doi.org/10.18653/v1/2020.blackboxnlp-1.13) In *Proceedings of the Third BlackboxNLP Workshop on Analyzing and Interpreting Neural Networks for NLP*, pages 136–148, Online. Association for Computational Linguistics.
- <span id="page-9-9"></span>Maria De-Arteaga, Alexey Romanov, Hanna M. Wallach, Jennifer T. Chayes, Christian Borgs, Alexandra Chouldechova, Sahin Cem Geyik, Krishnaram Kenthapadi, and Adam Tauman Kalai. 2019. [Bias in](http://arxiv.org/abs/1901.09451) [bios: A case study of semantic representation bias in](http://arxiv.org/abs/1901.09451) [a high-stakes setting.](http://arxiv.org/abs/1901.09451) *CoRR*, abs/1901.09451.
- <span id="page-9-11"></span>Sunipa Dev and Jeff M Phillips. 2019. [Attenuating bias](http://proceedings.mlr.press/v89/dev19a/dev19a.pdf) [in word vectors.](http://proceedings.mlr.press/v89/dev19a/dev19a.pdf) In *The 22nd International Conference on Artificial Intelligence and Statistics*, pages 879–887. PMLR.
- <span id="page-9-0"></span>Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. 2019. [BERT: Pre-training of](https://doi.org/10.18653/v1/N19-1423) [deep bidirectional transformers for language under](https://doi.org/10.18653/v1/N19-1423)[standing.](https://doi.org/10.18653/v1/N19-1423) In *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)*, pages 4171–4186, Minneapolis, Minnesota. Association for Computational Linguistics.
- <span id="page-9-8"></span>Petros Drineas and Michael W. Mahoney. 2005. [On](https://www.jmlr.org/papers/volume6/drineas05a/drineas05a.pdf) [the Nyström method for approximating a Gram ma](https://www.jmlr.org/papers/volume6/drineas05a/drineas05a.pdf)[trix for improved kernel-based learning.](https://www.jmlr.org/papers/volume6/drineas05a/drineas05a.pdf) *Journal of Machine Learning Research*, 6:2153–2175.
- <span id="page-9-12"></span>Yanai Elazar, Shauli Ravfogel, Alon Jacovi, and Yoav Goldberg. 2021. [Amnesic probing: Behavioral expla](https://doi.org/10.1162/tacl_a_00359)[nation with amnesic counterfactuals.](https://doi.org/10.1162/tacl_a_00359) *Transactions of the Association for Computational Linguistics*, 9:160– 175.
- <span id="page-9-2"></span>Peter Gärdenfors. 2000. *[Conceptual Spaces: The Ge](https://doi.org/10.7551/mitpress/2076.001.0001)[ometry of Thought](https://doi.org/10.7551/mitpress/2076.001.0001)*. The MIT Press.
- <span id="page-9-7"></span>Gene H. Golub and Charles F. Van Loan. 2013. *[Matrix](https://www.press.jhu.edu/books/title/10678/matrix-computations) [Computations](https://www.press.jhu.edu/books/title/10678/matrix-computations)*. Johns Hopkins Press.
- <span id="page-9-4"></span>Hila Gonen and Yoav Goldberg. 2019. [Lipstick on a](https://doi.org/10.18653/v1/N19-1061) [pig: Debiasing methods cover up systematic gender](https://doi.org/10.18653/v1/N19-1061) [biases in word embeddings but do not remove them.](https://doi.org/10.18653/v1/N19-1061) In *Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)*, pages 609–614, Minneapolis, Minnesota. Association for Computational Linguistics.
- <span id="page-9-14"></span>Hila Gonen, Shauli Ravfogel, Yanai Elazar, and Yoav Goldberg. 2020. [It's not Greek to mBERT: Inducing](https://doi.org/10.18653/v1/2020.blackboxnlp-1.5) [word-level translations from multilingual BERT.](https://doi.org/10.18653/v1/2020.blackboxnlp-1.5) In *Proceedings of the Third BlackboxNLP Workshop on Analyzing and Interpreting Neural Networks for NLP*, pages 45–56, Online. Association for Computational Linguistics.

- <span id="page-10-15"></span>Ian Goodfellow, Yoshua Bengio, and Aaron Courville. 2016. *[Deep Learning](https://mitpress.mit.edu/9780262035613/)*. MIT Press.
- <span id="page-10-7"></span>Ian Goodfellow, Jean Pouget-Abadie, Mehdi Mirza, Bing Xu, David Warde-Farley, Sherjil Ozair, Aaron Courville, and Yoshua Bengio. 2014. [Generative ad](https://proceedings.neurips.cc/paper/2014/file/5ca3e9b122f61f8f06494c97b1afccf3-Paper.pdf)[versarial nets.](https://proceedings.neurips.cc/paper/2014/file/5ca3e9b122f61f8f06494c97b1afccf3-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 27.
- <span id="page-10-18"></span>Evan Hernandez and Jacob Andreas. 2021. [The low](https://aclanthology.org/2021.conll-1.7)[dimensional linear geometry of contextualized word](https://aclanthology.org/2021.conll-1.7) [representations.](https://aclanthology.org/2021.conll-1.7) In *Proceedings of the 25th Conference on Computational Natural Language Learning*, pages 82–93, Online. Association for Computational Linguistics.
- <span id="page-10-17"></span>Felix Hill, Roi Reichart, and Anna Korhonen. 2015. [SimLex-999: Evaluating semantic models with \(gen](https://doi.org/10.1162/COLI_a_00237)[uine\) similarity estimation.](https://doi.org/10.1162/COLI_a_00237) *Computational Linguistics*, 41(4):665–695.
- <span id="page-10-9"></span>Thomas Hofmann, Bernhard Schölkopf, and Alexander J. Smola. 2008. [Kernel methods in machine](https://arxiv.org/pdf/math/0701907.pdf) [learning.](https://arxiv.org/pdf/math/0701907.pdf) *The Annals of Statistics*, 36(3):1171–1220.
- <span id="page-10-16"></span>Aylin Caliskan Islam, Joanna J. Bryson, and Arvind Narayanan. 2017. [Semantics derived automatically](https://pubmed.ncbi.nlm.nih.gov/28408601/) [from language corpora necessarily contain human](https://pubmed.ncbi.nlm.nih.gov/28408601/) [biases.](https://pubmed.ncbi.nlm.nih.gov/28408601/) *Science*, 356(6334):183–186.
- <span id="page-10-12"></span>Rong Jin, Tianbao Yang, Mehrdad Mahdavi, Yu-Feng Li, and Zhi-Hua Zhou. 2013. [Improved bounds for](https://doi.org/10.1109/TIT.2013.2271378) [the Nyström method with application to kernel classi](https://doi.org/10.1109/TIT.2013.2271378)[fication.](https://doi.org/10.1109/TIT.2013.2271378) *IEEE Transactions on Information Theory*, 59(10):6939–6949.
- <span id="page-10-19"></span>Been Kim, Martin Wattenberg, Justin Gilmer, Carrie Cai, James Wexler, Fernanda Viegas, and Rory Sayres. 2018. [Interpretability beyond feature attri](https://proceedings.mlr.press/v80/kim18d.html)[bution: Quantitative testing with concept activation](https://proceedings.mlr.press/v80/kim18d.html) [vectors \(TCAV\).](https://proceedings.mlr.press/v80/kim18d.html) In *Proceedings of the 35th International Conference on Machine Learning*, volume 80 of *Proceedings of Machine Learning Research*, pages 2668–2677. PMLR.
- <span id="page-10-10"></span>George S. Kimeldorf and Grace Wahba. 1970. [A corre](https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-41/issue-2/A-Correspondence-Between-Bayesian-Estimation-on-Stochastic-Processes-and-Smoothing/10.1214/aoms/1177697089.pdf)[spondence between Bayesian estimation on stochas](https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-41/issue-2/A-Correspondence-Between-Bayesian-Estimation-on-Stochastic-Processes-and-Smoothing/10.1214/aoms/1177697089.pdf)[tic processes and smoothing by splines.](https://projecteuclid.org/journals/annals-of-mathematical-statistics/volume-41/issue-2/A-Correspondence-Between-Bayesian-Estimation-on-Stochastic-Processes-and-Smoothing/10.1214/aoms/1177697089.pdf) *The Annals of Mathematical Statistics*, 41(2):495–502.
- <span id="page-10-1"></span>Jiasen Lu, Dhruv Batra, Devi Parikh, and Stefan Lee. 2019. [ViLBERT: Pretraining task-agnostic visiolin](https://proceedings.neurips.cc/paper/2019/file/c74d97b01eae257e44aa9d5bade97baf-Paper.pdf)[guistic representations for vision-and-language tasks.](https://proceedings.neurips.cc/paper/2019/file/c74d97b01eae257e44aa9d5bade97baf-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 32. Curran Associates, Inc.
- <span id="page-10-2"></span>Rowan Hall Maudslay, Hila Gonen, Ryan Cotterell, and Simone Teufel. 2019. [It's all in the name: Mitigating](https://doi.org/10.18653/v1/D19-1530) [gender bias with name-based counterfactual data sub](https://doi.org/10.18653/v1/D19-1530)[stitution.](https://doi.org/10.18653/v1/D19-1530) In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing (EMNLP-IJCNLP)*, pages 5267–5275, Hong Kong, China. Association for Computational Linguistics.

- <span id="page-10-14"></span>Sebastian Mika, Bernhard Schölkopf, Alex Smola, Klaus-Robert Müller, Matthias Scholz, and Gunnar Rätsch. 1998. [Kernel PCA and de-noising in feature](https://proceedings.neurips.cc/paper/1998/file/226d1f15ecd35f784d2a20c3ecf56d7f-Paper.pdf) [spaces.](https://proceedings.neurips.cc/paper/1998/file/226d1f15ecd35f784d2a20c3ecf56d7f-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 11, pages 536–542.
- <span id="page-10-3"></span>Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. 2013. [Efficient estimation of word representa](https://openreview.net/forum?id=idpCdOWtqXd60)[tions in vector space.](https://openreview.net/forum?id=idpCdOWtqXd60) In *1st International Conference on Learning Representations*.
- <span id="page-10-13"></span>Arik Nemtsov, Amir Averbuch, and Alon Schclar. 2016. [Matrix compression using the Nyström method.](https://arxiv.org/abs/1305.0203) *Intelligent Data Analysis*, 20(5):997–1019.
- <span id="page-10-6"></span>John von Neumann and Oskar Morgenstern. 1944. *[The](https://en.wikipedia.org/wiki/Theory_of_Games_and_Economic_Behavior)[ory of Games and Economic Behavior](https://en.wikipedia.org/wiki/Theory_of_Games_and_Economic_Behavior)*. Princeton University Press.
- <span id="page-10-11"></span>Evert J. Nyström. 1930. [Über die praktische Auflö](https://link.springer.com/article/10.1007/BF02547521)[sung von Integralgleichungen mit Anwendungen auf](https://link.springer.com/article/10.1007/BF02547521) [Randwertaufgaben.](https://link.springer.com/article/10.1007/BF02547521) *Acta Mathematica*, 54:185–204.
- <span id="page-10-0"></span>Jeffrey Pennington, Richard Socher, and Christopher Manning. 2014. [GloVe: Global vectors for word](https://doi.org/10.3115/v1/D14-1162) [representation.](https://doi.org/10.3115/v1/D14-1162) In *Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 1532–1543, Doha, Qatar. Association for Computational Linguistics.
- <span id="page-10-8"></span>Shauli Ravfogel, Yanai Elazar, Hila Gonen, Michael Twiton, and Yoav Goldberg. 2020. [Null it out: Guard](https://doi.org/10.18653/v1/2020.acl-main.647)[ing protected attributes by iterative nullspace projec](https://doi.org/10.18653/v1/2020.acl-main.647)[tion.](https://doi.org/10.18653/v1/2020.acl-main.647) In *Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics*, pages 7237–7256, Online. Association for Computational Linguistics.
- <span id="page-10-4"></span>Shauli Ravfogel, Grusha Prasad, Tal Linzen, and Yoav Goldberg. 2021. [Counterfactual interventions re](https://aclanthology.org/2021.conll-1.15)[veal the causal effect of relative clause representa](https://aclanthology.org/2021.conll-1.15)[tions on agreement prediction.](https://aclanthology.org/2021.conll-1.15) In *Proceedings of the 25th Conference on Computational Natural Language Learning*, pages 194–209, Online. Association for Computational Linguistics.
- <span id="page-10-5"></span>Shauli Ravfogel, Michael Twiton, Yoav Goldberg, and Ryan Cotterell. 2022. [Linear adversarial concept](https://proceedings.mlr.press/v162/ravfogel22a.html) [erasure.](https://proceedings.mlr.press/v162/ravfogel22a.html) In *Proceedings of the 39th International Conference on Machine Learning*, volume 162 of *Proceedings of Machine Learning Research*, pages 18400–18421. PMLR.
- <span id="page-10-21"></span>Bashir Sadeghi, Runyi Yu, and Vishnu Boddeti. 2019. [On the global optima of kernelized adversarial repre](https://openaccess.thecvf.com/content_ICCV_2019/papers/Sadeghi_On_the_Global_Optima_of_Kernelized_Adversarial_Representation_Learning_ICCV_2019_paper.pdf)[sentation learning.](https://openaccess.thecvf.com/content_ICCV_2019/papers/Sadeghi_On_the_Global_Optima_of_Kernelized_Adversarial_Representation_Learning_ICCV_2019_paper.pdf) In *2019 IEEE/CVF International Conference on Computer Vision (ICCV)*, pages 7970– 7978. IEEE.
- <span id="page-10-20"></span>Bernhard Schölkopf, Alexander Smola, and Klaus-Robert Müller. 1997. [Kernel principal component](https://link.springer.com/chapter/10.1007/BFb0020217) [analysis.](https://link.springer.com/chapter/10.1007/BFb0020217) In *Artificial Neural Networks — ICANN'97*, pages 583–588, Berlin, Heidelberg. Springer Berlin Heidelberg.

- <span id="page-11-0"></span>Bernhard Schölkopf and Alexander J. Smola. 2002. *[Learning with Kernels: Support Vector Machines,](https://mitpress.mit.edu/9780262536578/learning-with-kernels/) [Regularization, Optimization, and Beyond](https://mitpress.mit.edu/9780262536578/learning-with-kernels/)*. MIT Press.
- <span id="page-11-1"></span>John Shawe-Taylor and Nello Cristianini. 2004. *[Kernel](https://www.cambridge.org/core/books/kernel-methods-for-pattern-analysis/811462F4D6CD6A536A05127319A8935A) [Methods for Pattern Analysis](https://www.cambridge.org/core/books/kernel-methods-for-pattern-analysis/811462F4D6CD6A536A05127319A8935A)*. Cambridge University Press.
- <span id="page-11-6"></span>Francisco Vargas and Ryan Cotterell. 2020. [Exploring](https://doi.org/10.18653/v1/2020.emnlp-main.232) [the linear subspace hypothesis in gender bias miti](https://doi.org/10.18653/v1/2020.emnlp-main.232)[gation.](https://doi.org/10.18653/v1/2020.emnlp-main.232) In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pages 2902–2913, Online. Association for Computational Linguistics.
- <span id="page-11-4"></span>Vincent Q. Vu, Juhee Cho, Jing Lei, and Karl Rohe. 2013. [Fantope projection and selection: A near](https://proceedings.neurips.cc/paper/2013/file/81e5f81db77c596492e6f1a5a792ed53-Paper.pdf)[optimal convex relaxation of sparse PCA.](https://proceedings.neurips.cc/paper/2013/file/81e5f81db77c596492e6f1a5a792ed53-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 26.
- <span id="page-11-5"></span>Jennifer C. White, Tiago Pimentel, Naomi Saphra, and Ryan Cotterell. 2021. [A non-linear structural probe.](https://doi.org/10.18653/v1/2021.naacl-main.12) In *Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies*, pages 132–138, Online. Association for Computational Linguistics.
- <span id="page-11-3"></span>Christopher Williams and Matthias Seeger. 2000. [Using](https://proceedings.neurips.cc/paper/2000/file/19de10adbaa1b2ee13f77f679fa1483a-Paper.pdf) [the Nyström method to speed up kernel machines.](https://proceedings.neurips.cc/paper/2000/file/19de10adbaa1b2ee13f77f679fa1483a-Paper.pdf) In *Advances in Neural Information Processing Systems*, volume 13.

<span id="page-11-2"></span>Kosaku Yosida. 2012. *[Functional Analysis](https://link.springer.com/book/10.1007/978-3-662-11791-0)*. Springer.

### A Related Work

Mitigation of Gender Bias. The identification of linear subspaces that encode binary gender has attracted considerable research interest (Bolukbasi et al., 2016; Gonen and Goldberg, 2019; Dev and Phillips, 2019; Ravfogel et al., 2020). While bias mitigation is a central use case of concept erasure, concept subspaces have been applied to a number of tasks. Concept subspaces have been used to analyze the content of neural representations, e.g., for causal analysis (Elazar et al., 2021; Ravfogel et al., 2021), for analyzing the geometry of the representation space (Celikkanat et al., 2020; Gonen et al., 2020; Hernandez and Andreas, 2021), and for concept-based interpretability (Kim et al., 2018).

Kernelization of Linear Methods. The kernelization of linear machine learning algorithms is a common practice, and has many use cases, such as the kernelized perceptron (Aizerman et al., 1964) and kernel PCA (Schölkopf et al., 1997). White et al. (2021) proposed a kernelization of a structural probe that extracts syntactic structure from neural representations. Vargas and Cotterell (2020) proposed a kernelization of the PCA-based bias mitigation method of Bolukbasi et al. (2016), and found that it does not improve on the linear mitigation procedure. Since the effectiveness of this method has been questioned (Gonen and Goldberg, 2019), we consider a more principled and well-motivated approach for the identification and neutralization of the concept subspace. Sadeghi et al. (2019) proposed a kernelization of an alternative, regression-based linear adversarial objective, which is not limited to *orthogonal projections*. Our formulation is different in that it considers any linear model, and is restricted to the neutralization of linear subspaces via projection. This makes our method potentially less expressive, but more interpretable.

## <span id="page-12-0"></span>A.1 A Representer Lemma for Kernelized Maximin Games

**Lemma 1.** (Maximin Game Representer Theorem) Let  $\mathcal{H}$  be a reproducing kernel Hilbert space with canonical feature map  $\Phi \colon \mathbb{R}^D \to \mathcal{H}$ , i.e.,  $\Phi(\mathbf{x}) = \kappa(\mathbf{x}, \cdot)$ . Consider the following maximin game:

$$\max_{\boldsymbol{w} \in \mathcal{H}} \min_{\boldsymbol{\theta} \in \mathcal{H}} \sum_{n=1}^{N} \ell\left(y_n, \langle \boldsymbol{\theta}, P_{\boldsymbol{w}}^{\perp} \boldsymbol{\Phi}(\boldsymbol{x}_n) \rangle\right). \tag{5}$$

where  $P_{\boldsymbol{w}}^{\perp} \colon \mathcal{H} \to \mathcal{H}$  is the operator that projects onto the orthogonal complement of  $\boldsymbol{w}$ . For every attained local optimum  $(\boldsymbol{\theta}^{\star}, \boldsymbol{w}^{\star})$  of Eq. (5), there is another local optimum  $(\boldsymbol{\theta}^{\star}_{U}, \boldsymbol{w}^{\star}_{U})$  with the same value as  $(\boldsymbol{\theta}^{\star}, \boldsymbol{w}^{\star})$  in  $U \stackrel{\text{def}}{=} \operatorname{span} \left\{ \boldsymbol{\Phi}(\mathbf{x}_{1}), \ldots, \boldsymbol{\Phi}(\mathbf{x}_{N}) \right\}$ , the span of the training data.

*Proof.* For brevity, first notice we can re-express the objective as

$$\max_{\boldsymbol{w}, \in \mathcal{H}} \min_{\boldsymbol{\theta} \in \mathcal{H}} \sum_{n=1}^{N} \ell\left(y_n, \left\langle \boldsymbol{\theta}, \left(\mathbf{I} - \frac{\boldsymbol{w} \boldsymbol{w}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}}\right) \boldsymbol{\Phi}(\boldsymbol{x}_n) \right\rangle \right). \tag{12}$$

We will show that both w and  $\theta$  can be expressed as a linear combination of terms from the training data without losing expressive power. Now, decompose w as follows:  $w = w_U + w_{\perp U}$ , where we represent w as the sum of w projected onto U and onto its orthogonal complement  $U_{\perp}$ . Now, note that for any element of the training data  $\Phi(\mathbf{x}_n)$ , we have

<span id="page-12-1"></span><sup>&</sup>lt;sup>13</sup>Traditionally, a representer theorem has an extra regularization term on the function estimator that ensures the optimum is attained and that it is global (Kimeldorf and Wahba, 1970). We do not employ such a regularizer and, thus, have a weaker result.

$$\left(\mathbf{I} - \frac{\boldsymbol{w}\boldsymbol{w}^{\top}}{\boldsymbol{w}^{\top}\boldsymbol{w}}\right)\boldsymbol{\Phi}(\mathbf{x}_n) = \left(\mathbf{I} - \frac{(\boldsymbol{w}_U + \boldsymbol{w}_{\perp U})(\boldsymbol{w}_U + \boldsymbol{w}_{\perp U})^{\top}}{\boldsymbol{w}^{\top}\boldsymbol{w}}\right)\boldsymbol{\Phi}(\mathbf{x}_n)$$
(13a)

$$= \left( \mathbf{I} - \frac{\boldsymbol{w}_{U} \boldsymbol{w}_{U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}} - \underbrace{\frac{\boldsymbol{w}_{U} \boldsymbol{w}_{\perp U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}}}_{=0} - \underbrace{\frac{\boldsymbol{w}_{\perp U} \boldsymbol{w}_{U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}}}_{=0} - \underbrace{\frac{\boldsymbol{w}_{\perp U} \boldsymbol{w}_{\perp U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}}}_{=0} - \underbrace{\boldsymbol{w}_{\perp U} \boldsymbol{w}_{\perp U}^{\top}}_{=0} \right) \boldsymbol{\Phi}(\mathbf{x}_{n})$$
(13b)

$$= \left(\mathbf{I} - \frac{\boldsymbol{w}_{U} \boldsymbol{w}_{U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}} - \frac{\boldsymbol{w}_{\perp U} \boldsymbol{w}_{\perp U}^{\top}}{\boldsymbol{w}^{\top} \boldsymbol{w}}\right) \boldsymbol{\Phi}(\mathbf{x}_{n})$$
(13c)

$$= \mathbf{\Phi}(\mathbf{x}_n) - \frac{\mathbf{w}_U \mathbf{w}_U^{\top}}{\mathbf{w}^{\top} \mathbf{w}} \mathbf{\Phi}(\mathbf{x}_n) - \underbrace{\frac{\mathbf{w}_{\perp U} \mathbf{w}_{\perp U}^{\top}}{\mathbf{w}^{\top} \mathbf{w}}}_{=0} \mathbf{\Phi}(\mathbf{x}_n)$$
(13d)

$$= \mathbf{\Phi}(\mathbf{x}_n) - \mathbf{w}_U \frac{\mathbf{w}_U^{\top} \mathbf{\Phi}(\mathbf{x}_n)}{\mathbf{w}^{\top} \mathbf{w}}.$$
 (13e)

However, we have that  $\Phi(\mathbf{x}_n) - \boldsymbol{w}_U \frac{\boldsymbol{w}_U^{\top} \Phi(\mathbf{x}_n)}{\boldsymbol{w}^{\top} \boldsymbol{w}}$  is in U. Likewise, we can decompose  $\boldsymbol{\theta} = \boldsymbol{\theta}_U + \boldsymbol{\theta}_{\perp U}$ . Further manipulation reveals

$$\left\langle \boldsymbol{\theta}, \left( \mathbf{I} - \boldsymbol{w} \boldsymbol{w}^{\top} \right) \boldsymbol{\Phi}(\boldsymbol{x}_n) \right\rangle = \boldsymbol{\theta}_U^{\top} \boldsymbol{\Phi}(\mathbf{x}_n) - \boldsymbol{\theta}_U^{\top} \boldsymbol{w}_U \frac{\boldsymbol{w}_U^{\top} \boldsymbol{\Phi}(\mathbf{x}_n)}{\boldsymbol{w}^{\top} \boldsymbol{w}}.$$
 (14)

Thus, for any  $\theta$ , w,  $\in \mathcal{H}$  there exists a  $\theta_U$ ,  $w_U \in U$  that yields the same value of the objective as  $\theta$ , w. Now, we can parameterize  $\theta_U$  and  $w_U$  as

$$\mathbf{w}_U = \sum_{n=1}^{N} \alpha_n \mathbf{\Phi}(\mathbf{x}_n) \tag{15}$$

$$\boldsymbol{\theta}_U = \sum_{n=1}^N \beta_n \boldsymbol{\Phi}(\mathbf{x}_n). \tag{16}$$

for real coefficients  $\alpha \in \mathbb{R}^N$  and  $\beta \in \mathbb{R}^N$ . We conclude that for any local optimum  $\theta^*, w^* \in \mathcal{H}$ , the projection of  $\theta^*$  and  $w^*$  onto U yields a local optimum with the same value.

# <span id="page-13-0"></span>A.2 Kernelization of the Maximin Game

We show that the game Eq. (1) can be kernelized for the case k=1, i.e., a setting where the matrix  $\mathcal{P}_k$  removes a one-dimensional subspace. Specifically, we will show that the product  $\langle \boldsymbol{\theta}, \mathrm{P}\boldsymbol{\Phi}(\boldsymbol{x}_n) \rangle$  in Eq. (1) can be expressed as a function of the kernel  $\kappa(\cdot, \cdot)$ .

**Lemma 2.** Let  $\mathcal{H}$  be a reproducing kernel Hilbert space with canonical feature map  $\Phi$ , and let  $\Phi(z)$  be a point in  $\mathcal{H}$ . Next, let  $\mathbf{w} = \sum_{n=1}^{N} \alpha_n \Phi(\mathbf{x}_n)$  and  $\boldsymbol{\theta} = \sum_{n=1}^{N} \beta_n \Phi(\mathbf{x}_n)$  be points in the reproducing kernel Hilbert space. Now, let  $\Phi_{proj}(z)$  be the orthogonal projection of  $\Phi(z)$  onto the orthogonal complement of the subspace spanned by  $\mathbf{w}$ . Then, we have

$$\langle \boldsymbol{\theta}, \boldsymbol{\Phi}_{proj}(\boldsymbol{z}) \rangle = \sum_{m=1}^{N} \beta_{m} \left( \kappa(\boldsymbol{x}_{m}, \boldsymbol{z}) - \frac{\boldsymbol{\alpha}^{\top} \boldsymbol{K}^{(m)}(\boldsymbol{z}) \boldsymbol{\alpha}}{\boldsymbol{\alpha}^{\top} \boldsymbol{K} \boldsymbol{\alpha}} \right),$$
 (6)

where  $\boldsymbol{K}_{ij}^{(m)}(\boldsymbol{z}) \stackrel{\text{def}}{=} \kappa(\boldsymbol{x}_i,\boldsymbol{z}) \kappa(\boldsymbol{x}_m,\boldsymbol{x}_j).$ 

*Proof.* The projection onto the orthogonal complement of  $w = \sum_{n=1}^{N} \alpha_n \Phi(x_n)$  is defined as the following

$$P_{\boldsymbol{w}}^{\perp} \stackrel{\text{def}}{=} I - \frac{\left(\sum_{n=1}^{N} \alpha_n \boldsymbol{\Phi}(\mathbf{x}_i)\right) \left(\sum_{n=1}^{N} \alpha_n \boldsymbol{\Phi}(\mathbf{x}_n)^{\top}\right)}{\left(\sum_{n=1}^{N} \alpha_n \boldsymbol{\Phi}(\mathbf{x}_n)^{\top}\right) \left(\sum_{n=1}^{N} \alpha_n \boldsymbol{\Phi}(\mathbf{x}_n)\right)}$$
(17)

where I is the identity operator. Algebraic manipulation reveals

$$P_{\boldsymbol{w}}^{\perp} \boldsymbol{\Phi}(\boldsymbol{z}) \stackrel{\text{def}}{=} I \boldsymbol{\Phi}(\boldsymbol{z}) - \frac{\left(\sum_{n=1}^{N} \alpha_{n} \boldsymbol{\Phi}(\boldsymbol{x}_{n})\right) \left(\sum_{n=1}^{N} \alpha_{n} \boldsymbol{\Phi}(\boldsymbol{x}_{n'})^{\top}\right)}{\left(\sum_{n=1}^{N} \alpha_{n} \boldsymbol{\Phi}(\boldsymbol{x}_{n})^{\top}\right) \left(\sum_{n=1}^{N} \alpha_{n} \boldsymbol{\Phi}(\boldsymbol{x}_{n})\right)} \boldsymbol{\Phi}(\boldsymbol{z})$$
(18a)

$$= \mathbf{\Phi}(\mathbf{z}) - \frac{\sum_{n=1}^{N} \sum_{m=1}^{N} \alpha_n \alpha_m \mathbf{\Phi}(\mathbf{x}_n) \mathbf{\Phi}(\mathbf{x}_m)^{\top} \mathbf{\Phi}(\mathbf{z})}{\sum_{n=1}^{N} \sum_{m=1}^{N} \alpha_n \alpha_m \mathbf{\Phi}(\mathbf{x}_n)^{\top} \mathbf{\Phi}(\mathbf{x}_m)}$$
(18b)

$$= \mathbf{\Phi}(z) - \frac{\sum_{n=1}^{N} \sum_{m=1}^{N} \alpha_n \alpha_m \mathbf{\Phi}(\boldsymbol{x}_n) \kappa(\boldsymbol{x}_m, \boldsymbol{z})}{\sum_{n=1}^{N} \sum_{m=1}^{N} \alpha_n \alpha_m \kappa(\boldsymbol{x}_n, \boldsymbol{x}_m)}$$
(18c)

$$= \Phi(z) - \underbrace{\left(\frac{\sum_{m=1}^{N} \alpha_m \kappa(x_m, z)}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}}\right)}_{\in \mathbb{R}} \sum_{n=1}^{N} \alpha_n \Phi(x_n)$$
(18d)

$$= \Phi(z) - \left(\frac{\sum_{m=1}^{N} \alpha_m \kappa(x_n, z)}{\alpha^{\top} K \alpha}\right) w$$
 (18e)

$$\stackrel{\text{def}}{=} \Phi_{\text{proj}}(z) \tag{18f}$$

Now, consider an element of the reproducing kernel Hilbert space

$$\boldsymbol{\theta} = \sum_{n=1}^{N} \beta_n \boldsymbol{\Phi}(\boldsymbol{x}_n) \tag{19}$$

Further algebraic manipulation reveals

$$\left\langle \boldsymbol{\theta}, \boldsymbol{\Phi}_{\text{proj}}(\boldsymbol{z}) \right\rangle = \left\langle \boldsymbol{\theta}, \boldsymbol{\Phi}(\boldsymbol{z}) - \left( \frac{\sum_{n=1}^{N} \alpha_n \kappa(\boldsymbol{x}_n, \boldsymbol{z})}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \right) \boldsymbol{w} \right\rangle$$
 (20a)

$$= \left\langle \sum_{m=1}^{N} \beta_m \mathbf{\Phi}(\mathbf{x}_m), \mathbf{\Phi}(\mathbf{z}) - \left( \frac{\sum_{n=1}^{N} \alpha_n \kappa(\mathbf{x}_n, \mathbf{z})}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \right) \mathbf{w} \right\rangle$$
 (20b)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \sum_{m=1}^{N} \beta_m \left( \frac{\sum_{n=1}^{N} \alpha_n \kappa(\boldsymbol{x}_n, \boldsymbol{z})}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \right) \kappa(\boldsymbol{x}_m, \boldsymbol{w})$$
(20c)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \frac{1}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \sum_{n=1}^{N} \sum_{m=1}^{N} \alpha_n \beta_m \kappa(\boldsymbol{x}_n, \boldsymbol{z}) \kappa(\boldsymbol{x}_m, \boldsymbol{w})$$
(20d)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \sum_{m=1}^{N} \beta_m \frac{\left(\sum_{n=1}^{N} \alpha_n \kappa(\boldsymbol{x}_n, \boldsymbol{z}) \kappa(\boldsymbol{x}_m, \boldsymbol{w})\right)}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}}$$
(20e)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \sum_{m=1}^{N} \beta_m \frac{\left(\sum_{n=1}^{N} \alpha_n \kappa(\boldsymbol{x}_n, \boldsymbol{z}) \boldsymbol{\Phi}(\boldsymbol{x}_m)^{\top} \left(\sum_{n'=1}^{N} \alpha_{n'} \boldsymbol{\Phi}(\boldsymbol{x}_{n'})\right)\right)}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}}$$
(20f)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \sum_{m=1}^{N} \beta_m \frac{\left(\sum_{n=1}^{N} \sum_{n'=1}^{N} \alpha_{n'} \alpha_n \kappa(\boldsymbol{x}_n, \boldsymbol{z}) \boldsymbol{\Phi}(\boldsymbol{x}_m)^{\top} \boldsymbol{\Phi}(\boldsymbol{x}_{n'})\right)}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}}$$
(20g)

$$= \sum_{m=1}^{N} \beta_m \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \sum_{m=1}^{N} \beta_m \frac{\left(\sum_{n=1}^{N} \sum_{n'=1}^{N} \alpha_n \alpha_{n'} \kappa(\boldsymbol{x}_n, \boldsymbol{z}) \kappa(\boldsymbol{x}_m, \boldsymbol{x}_{n'})\right)}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}}$$
(20h)

<span id="page-14-0"></span>
$$= \sum_{m=1}^{N} \beta_m \left( \kappa(\boldsymbol{x}_m, \boldsymbol{z}) - \frac{\boldsymbol{\alpha}^{\top} \boldsymbol{K}^{(m)}(\boldsymbol{z}) \boldsymbol{\alpha}}{\boldsymbol{\alpha}^{\top} \boldsymbol{K} \boldsymbol{\alpha}} \right)$$
(20i)

where we define the following matrix component-wise:  $\boldsymbol{K}_{ij}^{(m)}(\boldsymbol{z}) \stackrel{\text{def}}{=} \kappa(\boldsymbol{x}_i, \boldsymbol{z}) \kappa(\boldsymbol{x}_m, \boldsymbol{x}_j)$ . Eq. (20i) can be evaluated without explicitly applying the kernel transformation  $\boldsymbol{\Phi}$ . In terms of notation, when we have  $\left\langle \boldsymbol{\theta}, \boldsymbol{\Phi}_{\text{proj}}(\boldsymbol{z}_n) \right\rangle$ , we write

$$\sum_{m=1}^{N} \beta_m \left( \kappa(\boldsymbol{x}_m, \boldsymbol{z}_n) - \frac{\boldsymbol{\alpha}^{\top} \boldsymbol{K}^{(m,n)} \boldsymbol{\alpha}}{\boldsymbol{\alpha}^{\top} K \boldsymbol{\alpha}} \right)$$
 (21)

where we define  $\bm{K}_{ij}^{(m,n)}(\bm{z}) \stackrel{\text{def}}{=} \kappa(\bm{x}_i, \bm{z}_n) \kappa(\bm{x}_m, \bm{x}_j)$ . This proves the result.

### <span id="page-15-0"></span>A.3 Experimental setting

**Data.** We conduct experiments on the uncased version of the GloVe representations, which are 300-dimensional, licensed under Apache License, Version 2.0. Following Ravfogel et al. (2020), to approximate the gender labels for the vocabulary, we project all representations on the  $\overrightarrow{he}$  –  $\overrightarrow{she}$  direction, and take the  $\overrightarrow{7}$ , 500 most male-biased and female-biased words. Note that unlike (Bolukbasi et al., 2016), we use the  $\overrightarrow{he}$  –  $\overrightarrow{she}$  direction only to induce approximate gender labels, but then proceed to measure the bias in various ways that go beyond neutralizing just the  $\overrightarrow{he}$  –  $\overrightarrow{she}$  direction. We use the same train–dev–test split of Ravfogel et al. (2020), but discard the gender-neutral words (i.e., we cast the problem as a binary classification). We obtain training, evaluation, and test sets of sizes 7,350, 3,150 and 4,500, respectively. We perform four independent runs of the entire method for all kernel types, with different random seeds.

**The kernelized maximin game.** For each kernel, we experiment with the following combinations of hyperparameter values:

• Poly : d  $\in \{2,3\}; \gamma \in \{0.05,0.1,0.15\}; \alpha \in \{0.8,1,1.2\}.$ 

• RBF :  $\gamma \in \{0.1, 0.15, 0.2\}$ 

• Laplace :  $\gamma \in \{0.1, 0.15, 0.2\}$ 

• Sigmoid :  $\alpha \in \{0, 0.01\}; \gamma \in \{0.005, 0.003\}.$ 

We approximate the kernel space using L=1024 Nyström landmarks. We run the adversarial game Eq. (10) for each of the kernel mappings we consider, by performing alternate minimization and maximization over  $\theta$  and P, respectively. As our optimization procedure, we use stochastic gradient descent with a learning rate of 0.08 and minibatches of size 256. We run for 35,000 batches, and choose the projection matrix P which leads to the biggest decrease in the linear classification accuracy on the evaluation set. In all cases, we identify a matrix which decreases classification accuracy to near-random accuracy. All training is done on a single NVIDIA GeForce GTX 1080 Ti GPU.

**Pre-image mapping.** We train an MLP with 2 hidden layers of sizes 512 and 300 to map the original inputs  $x_n$  to inputs which, after being mapped to kernel space, are close to the neutralized features. We use dropout of 0.1, ReLU activation and layer normalization after each hidden layer. We use a skip connection between the input and the output layer, i.e., we set the final output of the MLP to be the sum of its inputs and outputs.<sup>14</sup> We train for 15,000 batches of size 128 and choose the model that yields the lowest loss on the evaluation set.

**Non-linear gender prediction.** We consider the following non-linear predictors: SVMs with different kernels, as well as an MLP with 128 hidden units and ReLU activations. We use the sklearn implementation of predictors. They are trained on the reconstructed pre-image of the training set, and tested on the reconstructed pre-image of the test set. Note that while in training we used an approximation of the kernel function, we predict gender from the pre-images using SVM classifiers that rely on the actual, exact kernel.

<span id="page-15-1"></span><sup>&</sup>lt;sup>14</sup>This is useful because we assume the gender information is not very salient in the original representations, since these encode much more information. With the skip connection, the MLP only needs to learn what to remove, rather than learning to generate plausible representations.

### <span id="page-16-0"></span>**A.3.1** Pipeline Evaluation

In this appendix, we include sanity check experiments that aim to assess whether the maximin game Eq. (10) effectively removes *linearly*-present concepts from the *non-linear* kernel features, and whether the training of the pre-image network succeeds.

Concept erasure in kernel space. Do we effectively neutralize the concept in the approximate kernel space? For each kernel, we solve the game Eq. (10) and use the final projection matrix P to create neutralized features. We neutralize the features in RKHS by mapping  $\widetilde{\Phi}(x_n) \mapsto P\widetilde{\Phi}(x_n)$ , and train a linear classifier to recover the gender labels from the neutralized representations. We get a classification accuracy of  $50.59\pm0.04$ , very close to majority accuracy of 50.58. This suggests that the process is effective in protecting against the kernel which was applied in training (training a linear classifier on the kernel-transformed representations is equivalent to training a kernel classifier on the original representations). Notice, however, that we cannot test *other* non-linear kernel classifiers on these representations in a similar way: If the approximate kernel mapping  $\widetilde{\Phi}(\cdot)$  corresponds, for example, to a polynomial kernel, we cannot measure the success of an RBF kernel in recovering the bias information after the intervention without performing the pre-image mapping.

**Pre-image mapping.** Our neutralization algorithm relies on calculating the pre-image of the kernel features after the intervention. To evaluate the quality of the pre-image mapping, we measure the relative reconstruction error  $\left|\left|\frac{P\tilde{\Phi}(x_n)-\tilde{\Phi}(f(x_n))}{P\tilde{\Phi}(x_n)}\right|\right|_2^2$  over all points  $x_n$  on the evaluation set. When averaged over all 4 seeds and the different kernels we experimented with, we get a reconstruction error of  $1.81\pm1.61\%$  (range 0.45-7.94).

## <span id="page-17-0"></span>A.4 Gender Prediction from the Pre-image

<span id="page-17-1"></span>In Table [4](#page-17-1) we report the full evaluation results on the pre-image neutralized representations, where we have used the same kernel (and the same hyperparameters) for neutralization and gender recovery from the pre-image.

| Kernel    | γ     | α    | d | WEAT's<br>d    | WEAT's<br>p-value | Gender Acc.    |
|-----------|-------|------|---|----------------|-------------------|----------------|
| Poly      | 0.05  | 0.8  | 2 | 0.73 ±<br>0.01 | 0.084 ±<br>0.002  | 0.49 ±<br>0.00 |
| Poly      | 0.05  | 1    | 2 | 0.74 ±<br>0.01 | 0.080 ±<br>0.002  | 0.49 ±<br>0.00 |
| Poly      | 0.05  | 1.2  | 2 | 0.74 ±<br>0.01 | 0.081 ±<br>0.002  | 0.49 ±<br>0.00 |
| Poly      | 0.05  | 0.8  | 3 | 0.75 ±<br>0.01 | 0.077 ±<br>0.003  | 0.49 ±<br>0.00 |
| Poly      | 0.05  | 1    | 3 | 0.74 ±<br>0.01 | 0.080 ±<br>0.003  | 0.49 ±<br>0.00 |
| Poly      | 0.05  | 1.2  | 3 | 0.74 ±<br>0.01 | 0.081 ±<br>0.003  | 0.49 ±<br>0.00 |
| Poly      | 0.1   | 0.8  | 2 | 0.74 ±<br>0.01 | 0.080 ±<br>0.003  | 0.49 ±<br>0.00 |
| Poly      | 0.1   | 1    | 2 | 0.74 ±<br>0.00 | 0.080 ±<br>0.001  | 0.49 ±<br>0.00 |
| Poly      | 0.1   | 1.2  | 2 | 0.74 ±<br>0.01 | 0.081 ±<br>0.002  | 0.49 ±<br>0.00 |
| Poly      | 0.1   | 0.8  | 3 | 0.74 ±<br>0.00 | 0.081 ±<br>0.002  | 0.53 ±<br>0.01 |
| Poly      | 0.1   | 1    | 3 | 0.73 ±<br>0.01 | 0.082 ±<br>0.004  | 0.65 ±<br>0.03 |
| Poly      | 0.1   | 1.2  | 3 | 0.73 ±<br>0.01 | 0.084 ±<br>0.004  | 0.72 ±<br>0.01 |
| Poly      | 0.15  | 0.8  | 2 | 0.73 ±<br>0.01 | 0.082 ±<br>0.003  | 0.56 ±<br>0.03 |
| Poly      | 0.15  | 1    | 2 | 0.74 ±<br>0.02 | 0.081 ±<br>0.006  | 0.54 ±<br>0.02 |
| Poly      | 0.15  | 1.2  | 2 | 0.73 ±<br>0.01 | 0.084 ±<br>0.004  | 0.55 ±<br>0.02 |
| Poly      | 0.15  | 0.8  | 3 | 0.73 ±<br>0.01 | 0.082 ±<br>0.003  | 0.88 ±<br>0.02 |
| Poly      | 0.15  | 1    | 3 | 0.73 ±<br>0.01 | 0.082 ±<br>0.003  | 0.92 ±<br>0.00 |
| Poly      | 0.15  | 1.2  | 3 | 0.74 ±<br>0.01 | 0.079 ±<br>0.003  | 0.93 ±<br>0.00 |
| RBF       | 0.1   | -    | - | 0.75 ±<br>0.01 | 0.078 ±<br>0.003  | 0.49 ±<br>0.01 |
| RBF       | 0.15  | -    | - | 0.74 ±<br>0.01 | 0.079 ±<br>0.003  | 0.68 ±<br>0.03 |
| RBF       | 0.2   | -    | - | 0.74 ±<br>0.01 | 0.081 ±<br>0.003  | 0.89 ±<br>0.01 |
| Laplace   | 0.1   | -    | - | 0.72 ±<br>0.03 | 0.086 ±<br>0.008  | 0.62 ±<br>0.04 |
| Laplace   | 0.15  | -    | - | 0.74 ±<br>0.05 | 0.080 ±<br>0.015  | 0.77 ±<br>0.05 |
| Laplace   | 0.2   | -    | - | 0.67 ±<br>0.05 | 0.107 ±<br>0.020  | 0.88 ±<br>0.04 |
| Linear    | -     | -    | - | 0.74 ±<br>0.01 | 0.079 ±<br>0.004  | 0.54 ±<br>0.02 |
| Sigmoid   | 0.005 | 0    | - | 0.78 ±<br>0.05 | 0.069 ±<br>0.014  | 0.49 ±<br>0.00 |
| Sigmoid   | 0.005 | 0.01 | - | 0.73 ±<br>0.03 | 0.082 ±<br>0.010  | 0.49 ±<br>0.00 |
| Sigmoid   | 0.003 | 0    | - | 0.73 ±<br>0.05 | 0.083 ±<br>0.017  | 0.49 ±<br>0.00 |
| Sigmoid   | 0.003 | 0.01 | - | 0.76 ±<br>0.03 | 0.074 ±<br>0.008  | 0.49 ±<br>0.00 |
| EasyMKL   | -     | -    | - | 0.73 ±<br>0.01 | 0.084 ±<br>0.005  | 0.69 ±<br>0.01 |
| UniformMK | -     | -    | - | 0.73 ±<br>0.01 | 0.084 ±<br>0.002  | 0.49 ±<br>0.00 |
| Original  | -     | -    | - | 1.56           | 0.000             | ≥<br>0.99      |

Table 4: Evaluation of the neutralized pre-image representations. We show the WEAT test's statistics and p-value, as well as the gender prediction accuracy of a kernel classifier of the same type as the one applied during neutralization.

# <span id="page-18-0"></span>A.5 Closest Neighbors

<span id="page-18-1"></span>In Table 5, we show the closest neighbors to randomly-sampled word representations before and after gender erasure under the polynomial kernel. The results for other kernels are qualitatively similar.

| Word          | Neighbors before                  | Neighbors after                   |  |  |
|---------------|-----------------------------------|-----------------------------------|--|--|
| spiritual     | faith, religious, healing         | emotional, religious, healing     |  |  |
| lesson        | learn, teach, lessons             | teaching, teach, lessons          |  |  |
| faces         | faced, facing, face               | faced, facing, face               |  |  |
| forget        | know, let, remember               | know, let, remember               |  |  |
| converter     | ipod, conversion, convert         | ipod, conversion, convert         |  |  |
| clean         | keep, wash, cleaning              | keep, wash, cleaning              |  |  |
| formal        | elegant, dress, appropriate       | elegant, appropriate, dress       |  |  |
| identity      | identify, context, identification | context, identify, identification |  |  |
| other         | these, those, many                | these, those, many                |  |  |
| licensed      | registered, certified, license    | registered, certified, license    |  |  |
| ratings       | reviews, rated, rating            | reviews, rated, rating            |  |  |
| properly      | proper, effectively, correctly    | effectively, proper, correctly    |  |  |
| build         | create, built, building           | built, create, building           |  |  |
| solutions     | systems, technologies, solution   | services, technologies, solution  |  |  |
| afghanistan   | troops, pakistan, iraq            | troops, pakistan, iraq            |  |  |
| wallpaper     | desktop, pictures, picture        | desktop, pictures, picture        |  |  |
| sound         | audio, noise, sounds              | audio, noise, sounds              |  |  |
| gender        | sexual, male, age                 | male, differences, age            |  |  |
| boat          | cruise, ship, fishing             | cruise, ship, fishing             |  |  |
| downtown      | portland, city, neighborhood      | portland, neighborhood, city      |  |  |
| lawyers       | attorney, lawyer, attorneys       | attorney, lawyer, attorneys       |  |  |
| smart         | how, easy, intelligent            | wise, easy, intelligent           |  |  |
| spending      | budget, spent, spend              | budget, spent, spend              |  |  |
| contest       | winners, winner, competition      | winners, winner, competition      |  |  |
| want          | n't, know, need                   | n't, know, need                   |  |  |
| advice        | guidance, suggestions, tips       | guidance, suggestions, tips       |  |  |
| professionals | managers, professional, experts   | managers, professional, experts   |  |  |
| g             | d, b, f                           | d, b, f                           |  |  |
| australian    | zealand, british, australia       | zealand, british, australia       |  |  |
| na            | mo, o, da                         | mo, o, da                         |  |  |

Table 5: Closest neighbors to randomly-sampled words from GloVe vocabulary, for the original representations, and for the pre-images after our intervention.

# <span id="page-19-0"></span>A.6 WEAT Results

<span id="page-19-1"></span>Here we report the results of the WEAT test for the career and family-related words (Table [6\)](#page-19-1) and art and mathematics-related words (Table [7\)](#page-20-0).

| Kernel    | γ     | α    | d | WEAT-d         | p-value          |
|-----------|-------|------|---|----------------|------------------|
| Poly      | 0.05  | 0.8  | 2 | 0.72 ±<br>0.00 | 0.093 ±<br>0.002 |
| Poly      | 0.05  | 1    | 2 | 0.72 ±<br>0.01 | 0.091 ±<br>0.003 |
| Poly      | 0.05  | 1.2  | 2 | 0.72 ±<br>0.01 | 0.093 ±<br>0.004 |
| Poly      | 0.05  | 0.8  | 3 | 0.73 ±<br>0.00 | 0.089 ±<br>0.001 |
| Poly      | 0.05  | 1    | 3 | 0.74 ±<br>0.01 | 0.086 ±<br>0.004 |
| Poly      | 0.05  | 1.2  | 3 | 0.73 ±<br>0.01 | 0.089 ±<br>0.002 |
| Poly      | 0.1   | 0.8  | 2 | 0.72 ±<br>0.01 | 0.091 ±<br>0.005 |
| Poly      | 0.1   | 1    | 2 | 0.73 ±<br>0.00 | 0.089 ±<br>0.001 |
| Poly      | 0.1   | 1.2  | 2 | 0.72 ±<br>0.01 | 0.090 ±<br>0.003 |
| Poly      | 0.1   | 0.8  | 3 | 0.72 ±<br>0.01 | 0.090 ±<br>0.003 |
| Poly      | 0.1   | 1    | 3 | 0.72 ±<br>0.01 | 0.090 ±<br>0.003 |
| Poly      | 0.1   | 1.2  | 3 | 0.72 ±<br>0.01 | 0.091 ±<br>0.002 |
| Poly      | 0.15  | 0.8  | 2 | 0.71 ±<br>0.01 | 0.095 ±<br>0.004 |
| Poly      | 0.15  | 1    | 2 | 0.74 ±<br>0.00 | 0.087 ±<br>0.001 |
| Poly      | 0.15  | 1.2  | 2 | 0.72 ±<br>0.01 | 0.091 ±<br>0.002 |
| Poly      | 0.15  | 0.8  | 3 | 0.72 ±<br>0.00 | 0.093 ±<br>0.001 |
| Poly      | 0.15  | 1    | 3 | 0.72 ±<br>0.01 | 0.092 ±<br>0.002 |
| Poly      | 0.15  | 1.2  | 3 | 0.73 ±<br>0.01 | 0.090 ±<br>0.005 |
| RBF       | 0.1   | -    | - | 0.72 ±<br>0.01 | 0.090 ±<br>0.003 |
| RBF       | 0.15  | -    | - | 0.73 ±<br>0.01 | 0.090 ±<br>0.005 |
| RBF       | 0.2   | -    | - | 0.72 ±<br>0.01 | 0.091 ±<br>0.003 |
| Laplace   | 0.1   | -    | - | 0.75 ±<br>0.05 | 0.083 ±<br>0.017 |
| Laplace   | 0.15  | -    | - | 0.77 ±<br>0.02 | 0.076 ±<br>0.007 |
| Laplace   | 0.2   | -    | - | 0.70 ±<br>0.02 | 0.098 ±<br>0.008 |
| Linear    | -     | -    | - | 0.72 ±<br>0.02 | 0.090 ±<br>0.006 |
| Sigmoid   | 0.005 | 0    | - | 0.73 ±<br>0.03 | 0.087 ±<br>0.010 |
| Sigmoid   | 0.005 | 0.01 | - | 0.73 ±<br>0.02 | 0.087 ±<br>0.006 |
| Sigmoid   | 0.003 | 0    | - | 0.76 ±<br>0.06 | 0.079 ±<br>0.019 |
| Sigmoid   | 0.003 | 0.01 | - | 0.76 ±<br>0.07 | 0.080 ±<br>0.020 |
| EasyMKL   | -     | -    | - | 0.72 ±<br>0.02 | 0.091 ±<br>0.005 |
| UniformMK | -     | -    | - | 0.72 ±<br>0.00 | 0.092 ±<br>0.002 |
| Original  | -     | -    | - | 1.69           | 0.000            |

Table 6: Word association bias test (WEAT) for career and family-related terms

<span id="page-20-0"></span>

| Kernel    | γ     | α    | d | WEAT-d         | p-value          |
|-----------|-------|------|---|----------------|------------------|
| Poly      | 0.05  | 0.8  | 2 | 0.78 ±<br>0.00 | 0.068 ±<br>0.001 |
| Poly      | 0.05  | 1    | 2 | 0.78 ±<br>0.01 | 0.067 ±<br>0.002 |
| Poly      | 0.05  | 1.2  | 2 | 0.78 ±<br>0.00 | 0.067 ±<br>0.001 |
| Poly      | 0.05  | 0.8  | 3 | 0.78 ±<br>0.01 | 0.066 ±<br>0.002 |
| Poly      | 0.05  | 1    | 3 | 0.78 ±<br>0.01 | 0.066 ±<br>0.002 |
| Poly      | 0.05  | 1.2  | 3 | 0.78 ±<br>0.00 | 0.066 ±<br>0.001 |
| Poly      | 0.1   | 0.8  | 2 | 0.78 ±<br>0.00 | 0.068 ±<br>0.001 |
| Poly      | 0.1   | 1    | 2 | 0.78 ±<br>0.01 | 0.066 ±<br>0.002 |
| Poly      | 0.1   | 1.2  | 2 | 0.77 ±<br>0.01 | 0.069 ±<br>0.004 |
| Poly      | 0.1   | 0.8  | 3 | 0.78 ±<br>0.00 | 0.067 ±<br>0.001 |
| Poly      | 0.1   | 1    | 3 | 0.77 ±<br>0.01 | 0.070 ±<br>0.001 |
| Poly      | 0.1   | 1.2  | 3 | 0.78 ±<br>0.01 | 0.068 ±<br>0.002 |
| Poly      | 0.15  | 0.8  | 2 | 0.78 ±<br>0.01 | 0.068 ±<br>0.003 |
| Poly      | 0.15  | 1    | 2 | 0.78 ±<br>0.01 | 0.068 ±<br>0.003 |
| Poly      | 0.15  | 1.2  | 2 | 0.78 ±<br>0.00 | 0.068 ±<br>0.001 |
| Poly      | 0.15  | 0.8  | 3 | 0.78 ±<br>0.01 | 0.067 ±<br>0.002 |
| Poly      | 0.15  | 1    | 3 | 0.78 ±<br>0.01 | 0.067 ±<br>0.002 |
| Poly      | 0.15  | 1.2  | 3 | 0.77 ±<br>0.01 | 0.069 ±<br>0.002 |
| RBF       | 0.1   | -    | - | 0.79 ±<br>0.01 | 0.066 ±<br>0.003 |
| RBF       | 0.15  | -    | - | 0.78 ±<br>0.01 | 0.067 ±<br>0.002 |
| RBF       | 0.2   | -    | - | 0.78 ±<br>0.01 | 0.067 ±<br>0.002 |
| Laplace   | 0.1   | -    | - | 0.80 ±<br>0.04 | 0.064 ±<br>0.012 |
| Laplace   | 0.15  | -    | - | 0.81 ±<br>0.03 | 0.061 ±<br>0.009 |
| Laplace   | 0.2   | -    | - | 0.77 ±<br>0.04 | 0.070 ±<br>0.013 |
| linear    | -     | -    | - | 0.79 ±<br>0.01 | 0.066 ±<br>0.002 |
| Sigmoid   | 0.005 | 0    | - | 0.82 ±<br>0.04 | 0.057 ±<br>0.010 |
| Sigmoid   | 0.005 | 0.01 | - | 0.77 ±<br>0.05 | 0.070 ±<br>0.012 |
| Sigmoid   | 0.003 | 0    | - | 0.76 ±<br>0.03 | 0.073 ±<br>0.009 |
| Sigmoid   | 0.003 | 0.01 | - | 0.79 ±<br>0.03 | 0.066 ±<br>0.009 |
| EasyMKL   | -     | -    | - | 0.78 ±<br>0.00 | 0.066 ±<br>0.001 |
| UniformMK | -     | -    | - | 0.78 ±<br>0.01 | 0.069 ±<br>0.002 |
| Original  | -     | -    | - | 1.56           | 0.000            |

Table 7: Word association bias test (WEAT) for art and mathematics-related terms

#### <span id="page-21-0"></span>A.7 Transfer Results

<span id="page-21-1"></span>

|                                              | UniformMK       | EasyMKL         | RBF             | Poly            | Laplace         | Sigmoid         | Linear          | MLP             |
|----------------------------------------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|-----------------|
| poly, $\gamma = 0.05$ , d= 2, $\alpha = 0.8$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.01$ | $0.49 \pm 0.00$ | $0.61\pm0.06$   | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.05$ , d= 2, $\alpha = 1$   | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.01$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.52\pm0.01$   | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.05$ , d= 2, $\alpha = 1.2$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.53 \pm 0.02$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.05$ , d= 3, $\alpha = 0.8$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.01$   | $0.98 \pm 0.00$ | $0.93\pm0.01$   | $0.49 \pm 0.00$ | $0.54 \pm 0.03$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.05$ , d= 3, $\alpha = 1$   | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.94 \pm 0.01$ | $0.49 \pm 0.00$ | $0.59 \pm 0.05$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.05$ , d= 3, $\alpha = 1.2$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.53 \pm 0.01$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 2, $\alpha = 0.8$  | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.93 \pm 0.01$ | $0.49 \pm 0.00$ | $0.54 \pm 0.04$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 2, $\alpha = 1$    | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93 \pm 0.01$ | $0.49 \pm 0.00$ | $0.53 \pm 0.02$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 2, $\alpha = 1.2$  | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.54 \pm 0.01$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 3, $\alpha = 0.8$  | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.54 \pm 0.00$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 3, $\alpha = 1$    | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93 \pm 0.00$ | $0.49 \pm 0.00$ | $0.56 \pm 0.02$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.1$ , d= 3, $\alpha = 1.2$  | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93\pm0.00$   | $0.49 \pm 0.00$ | $0.54 \pm 0.03$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 2, $\alpha = 0.8$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93\pm0.00$   | $0.49 \pm 0.00$ | $0.57 \pm 0.02$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 2, $\alpha = 1$   | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.54 \pm 0.01$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 2, $\alpha = 1.2$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.93 \pm 0.00$ | $0.49 \pm 0.00$ | $0.54 \pm 0.01$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 3, $\alpha = 0.8$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.93\pm0.01$   | $0.49 \pm 0.00$ | $0.58 \pm 0.03$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 3, $\alpha = 1$   | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93 \pm 0.00$ | $0.49 \pm 0.00$ | $0.57 \pm 0.01$ | $0.97 \pm 0.00$ |
| poly, $\gamma = 0.15$ , d= 3, $\alpha = 1.2$ | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.93\pm0.00$   | $0.49 \pm 0.00$ | $0.56\pm0.01$   | $0.97 \pm 0.00$ |
| rbf, $\gamma = 0.1$                          | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.58 \pm 0.04$ | $0.97 \pm 0.00$ |
| rbf, $\gamma = 0.15$                         | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.60\pm0.03$   | $0.97 \pm 0.00$ |
| rbf, $\gamma = 0.2$                          | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96 \pm 0.00$ | $0.98 \pm 0.00$ | $0.93 \pm 0.01$ | $0.49 \pm 0.00$ | $0.60 \pm 0.04$ | $0.97 \pm 0.00$ |
| laplace, $\gamma = 0.1$                      | $0.60 \pm 0.06$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93 \pm 0.01$ | $0.49 \pm 0.00$ | $0.61\pm0.03$   | $0.97 \pm 0.00$ |
| laplace, $\gamma = 0.15$                     | $0.56 \pm 0.04$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.61\pm0.01$   | $0.97 \pm 0.00$ |
| laplace, $\gamma = 0.2$                      | $0.59 \pm 0.06$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.62\pm0.02$   | $0.97 \pm 0.00$ |
| linear                                       | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.93\pm0.00$   | $0.49 \pm 0.00$ | $0.54 \pm 0.02$ | $0.97 \pm 0.00$ |
| sigmoid, $\gamma = 0.005$ , $\alpha = 0$     | $0.64 \pm 0.05$ | $0.97 \pm 0.00$ | $0.93 \pm 0.01$ | $0.98 \pm 0.00$ | $0.90 \pm 0.01$ | $0.49 \pm 0.00$ | $0.65 \pm 0.05$ | $0.97 \pm 0.00$ |
| sigmoid, $\gamma = 0.005$ , $\alpha = 0.01$  | $0.63 \pm 0.02$ | $0.97 \pm 0.00$ | $0.94 \pm 0.00$ | $0.98 \pm 0.00$ | $0.90 \pm 0.01$ | $0.49 \pm 0.00$ | $0.65 \pm 0.04$ | $0.97 \pm 0.00$ |
| sigmoid, $\gamma = 0.003$ , $\alpha = 0$     | $0.63 \pm 0.07$ | $0.97 \pm 0.00$ | $0.92 \pm 0.01$ | $0.98 \pm 0.00$ | $0.89 \pm 0.01$ | $0.49 \pm 0.00$ | $0.66\pm0.07$   | $0.97 \pm 0.00$ |
| sigmoid, $\gamma = 0.003$ , $\alpha = 0.01$  | $0.65 \pm 0.03$ | $0.97 \pm 0.00$ | $0.92 \pm 0.01$ | $0.98 \pm 0.00$ | $0.89 \pm 0.01$ | $0.49 \pm 0.00$ | $0.65 \pm 0.05$ | $0.97 \pm 0.00$ |
| EasyMKL                                      | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.00$ | $0.49 \pm 0.00$ | $0.57 \pm 0.03$ | $0.97 \pm 0.00$ |
| UniformMK                                    | $0.49 \pm 0.00$ | $0.98 \pm 0.00$ | $0.96\pm0.00$   | $0.98 \pm 0.00$ | $0.94 \pm 0.01$ | $0.49 \pm 0.00$ | $0.58 \pm 0.08$ | $0.97 \pm 0.00$ |

Table 8: Gender prediction from the neutralized pre-image representations using non-linear adversaries that differ from the neutralizing kernel.

In this appendix, we provide gender prediction accuracy, on the neutralized pre-image representations, with predictors that are *different* from those used in training (Experiment §5.2).

**Setup.** After projecting out the gender concept in kernel space, and computing the pre-image of the neutralized representations, we apply different non-linear kernels as well as an MLP to predict gender. We use the following parameters:

- RBF :  $\gamma=0.3$ .
- Poly : d =3,  $\gamma=0.5$ ,  $\alpha=0.3$ .
- Laplace :  $\gamma = 0.3$ .
- Sigmoid :  $\alpha = 0$ ,  $\gamma = 0.01$ .
- MLP: A network with a single 128-dimensional hidden layer with ReLU activations.

All classifiers were trained using sklearn.

**Results.** The results are shown in Table 8. Rows denote the kernel that was applied for neutralization in Eq. (10), while columns denote the type of adversarial classifier applied on the final pre-image representations. Numbers denote accuracy in gender prediction.