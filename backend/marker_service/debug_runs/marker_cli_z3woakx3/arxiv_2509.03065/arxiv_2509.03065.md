# Mathematical research with GPT-5: a Malliavin-Stein experiment

Charles-Philippe Diez<sup>∗</sup> Luís da Maia<sup>∗</sup> Ivan Nourdin<sup>∗</sup>

#### Abstract

On August 20, 2025, GPT-5 was reported to have solved an open problem in convex optimization. Motivated by this episode, we conducted a controlled experiment in the Malliavin–Stein framework for central limit theorems. Our objective was to assess whether GPT-5 could go beyond known results by extending a qualitative fourth-moment theorem to a quantitative formulation with explicit convergence rates, both in the Gaussian and in the Poisson settings. To the best of our knowledge, the derivation of such quantitative rates had remained an open problem, in the sense that it had never been addressed in the existing literature. The present paper documents this experiment, presents the results obtained, and discusses their broader implications.

Keywords: Gaussian analysis, Poisson approximation, Malliavin calculus, Probability theory, Stochastic processes, Artificial intelligence in research AMS 2010 Subject Classification: 60G15, 60G55, 60H07, 60F05, 68T50

# 1 Introduction

The starting point of this study is a post by Sébastien Bubeck [\[2\]](#page-11-0) on X (Aug. 20, 2025), reporting that GPT-5 Pro had solved an open problem in convex optimization by improving a known bound from 1/L to 1.5/L within minutes. Beyond the claim and two screenshots (one showing the prompt, the other the AI-generated proof), no further details were provided regarding the methodology.

Bubeck's post attracted considerable attention, particularly on social media. Many non-specialists perceived it as a historic moment, even a striking demonstration of the power of AI, now seemingly able to compete with mathematicians. The reaction of mathematicians and researchers in the field was, however, more nuanced. Among the most notable comments was that of Ernest Ryu [\[10\]](#page-11-1), an expert in convex optimization, who placed the experiment back into context. According to him, the demonstration proposed by GPT-5 relied mainly on a well-known ingredient, Nesterov's Theorem, already familiar to specialists. In his view, an experienced researcher could have obtained an equivalent result within a few hours of work.

Motivated by this episode, we designed a small and controlled experiment in an area we know very well: the Malliavin–Stein method [\[6\]](#page-11-2), a powerful tool in

<sup>∗</sup>University of Luxembourg

probability theory to study convergence towards the normal distribution. This method was introduced almost twenty years ago by the fourth-named author together with Giovanni Peccati. It combines two complementary ideas. The Stein method makes it possible to test whether a random object converges to the normal law and, importantly, to measure the speed of this convergence. The Malliavin calculus, on the other hand, provides a kind of differential framework for random variables in stochastic analysis, especially on Gaussian and Poisson spaces. By bringing these two tools together, the Malliavin–Stein method not only shows that convergence takes place, but also gives explicit rates of convergence in settings where Malliavin calculus can be applied.

Concretely, we started from a recent theorem by Basse-O'Connor, Kramer-Bang, and Svendsen [\[1\]](#page-11-3), which established a qualitative result (proving that a certain sequence of probabilistic objects converges) but without specifying the speed of convergence. We then asked GPT-5 to go further and transform this qualitative result into a quantitative one, that is, to provide an explicit convergence rate. To the best of our knowledge, no published solution to this precise problem existed until today.

After this very rough description of the mathematical content, aimed mainly at non-mathematicians, we invite readers who are not specialists (or who are not primarily concerned with the mathematical results) to proceed directly to Section [4.](#page-7-0) For the others, we now briefly recall the context of our study and outline the results we obtained, with more precision.

The classical fourth moment theorem of Nualart and Peccati [\[8\]](#page-11-4) states that, for a sequence of normalized multiple Wiener–Itô integrals of fixed order, convergence of the fourth moment to three is equivalent to convergence in distribution to N (0, 1). This principle underlies numerous applications, most notably in establishing central limit theorems for functionals of infinite-dimensional Gaussian fields. Within the Malliavin–Stein framework, quantitative refinements can be expressed as bounds on the distance to Gaussianity in terms of the fourth cumulant; see [\[6\]](#page-11-2).

Building on [\[1\]](#page-11-3), in which the authors established a qualitative fourth moment theorem for sums of two multiple Wiener–Itô integrals of orders p and q such that p + q is odd, we make use of GPT-5 to obtain a quantitative counterpart in total variation. We also provide a Poisson analogue. In the Poisson setting, mixed odd moments such as E[X3Y ] need not vanish when X and Y are multiple Wiener–Itô integrals of different parities, so we identify sufficient conditions to establish a similar type of result. The theorem still holds, and we exhibit a counterexample showing these conditions are essentially sharp. It is important to note that, to the best of our knowledge, neither the Gaussian refinement nor the Poisson analogue had previously appeared in the literature.

Before turning to broader reflections on this unusual and somewhat disorienting AI-assisted workflow for mathematicians, we first present our mathematical contributions in a self-contained and usual manner, disregarding how they were obtained. The discussion of our GPT-5 protocol and what we believe to be its implications for research and doctoral training is deferred to Section [4.](#page-7-0)

Reading guide. Section [2](#page-2-0) recalls the necessary background and states the main quantitative result we have obtained in the Gaussian setting. Section [3](#page-5-0) is devoted to the Poisson extension and its limitations. Section [4](#page-7-0) documents the

GPT-5 experiment, and Section 5 offers ethical and educational reflections. The paper concludes with two appendices, reproducing the discussions we had with  $GPT-5$  in the Gaussian and Poisson cases.

#### <span id="page-2-0"></span>2 Gaussian analysis and Wiener chaos

This section presents the results we obtained in the Gaussian setting.

#### $2.1$ Preliminaries

Here, we recall the main tools and results concerning Gaussian analysis and Wiener chaos that will be needed later in the paper. Our aim is not to be exhaustive but to provide the essential background. For further details and complete proofs, we refer the reader to  $[6, 9]$ .

#### $2.1.1$ Wiener space and multiple integrals

Let  $(E,\mathcal{E},\mu)$  be a measurable space and  $H=L^2(E,\mu)$  the associated Hilbert space. Let  $W = \{W(h) : h \in H\}$  be an isonormal Gaussian process. For  $m \ge 1$ , the *m*-th multiple Wiener-Itô integral of a kernel  $f \in L^2_s(\mu^m)$  (square integrable and symmetric in its arguments) is denoted  $I_m(f)$  and satisfies the isometry

$$E[I_m(f)I_m(g)] = m! \langle f, g \rangle_{L^2(\mu^m)}.$$

The construction of  $I_m$  starts by defining it on simple tensors  $f = \mathbf{1}_{A_1} \otimes \cdots \otimes \mathbf{1}_{A_m}$ with disjoint sets  $A_i$ , extends linearly, and finally proceeds by  $L^2$ -density and symmetrization. The collection of all such integrals spans the  $m$ -th Wiener  $\text{chaos.}$ 

#### $2.1.2$ Orthogonality, contractions and product formula

The Wiener chaoses are mutually orthogonal: if  $F = I_p(f)$  and  $G = I_q(g)$ <br>with  $p \neq q$ , then  $E[FG] = 0$ . For  $f \in L^2_s(\mu^p)$  and  $g \in L^2_s(\mu^q)$  and an integer  $0 \leq r \leq \min(p,q)$ , the r-th contraction  $f \otimes_r g$  belongs to  $L^2(\mu^{p+q-2r})$  and is defined by contracting  $r$  coordinates:

$$(f \otimes_r g)(x_1, \dots, x_{p-r}, y_1, \dots, y_{q-r}) = \int_{E^r} f(x_1, \dots, x_{p-r}, z_1, \dots, z_r) \times g(y_1, \dots, y_{q-r}, z_1, \dots, z_r) d\mu(z_1) \cdots d\mu(z_r).$$
(1)

The symmetrized version is denoted  $f \widetilde{\otimes}_r g$ . The product formula states

<span id="page-2-1"></span>
$$I_p(f) I_q(g) = \sum_{r=0}^{\min(p,q)} r! \binom{p}{r} \binom{q}{r} I_{p+q-2r}(f \widetilde{\otimes}_r g). \tag{2}$$

#### Malliavin-Stein bound in total variation $2.1.3$

Let  $\mathbb{D}^{1,2}$  be the domain of the Malliavin derivative D and L be the associated Ornstein-Uhlenbeck generator (with pseudo-inverse  $L^{-1}$ ). For any centered,

unit-variance  $F \in \mathbb{D}^{1,2}$ ,

<span id="page-3-0"></span>
$$d_{\text{TV}}(F, \mathcal{N}(0, 1)) \le 2E \left| 1 - \left\langle DF, -DL^{-1}F \right\rangle_H \right| \le 2\sqrt{\text{Var}\left(\left\langle DF, -DL^{-1}F \right\rangle_H\right)}.$$
(3)

This is standard in the Malliavin–Stein method; see, e.g., [5, Th. 5.2]. Furthermore, if  $F = I_m(f)$  then

<span id="page-3-2"></span>
$$D_t F = m I_{m-1}(f(\cdot, t)), \qquad E[F^2] = m! \|f\|_{H^{\otimes m}}^2, \tag{4}$$

and  $-DL^{-1}F = \frac{1}{m}DF$  by the chaos action of  $L^{-1}$ .

#### $2.2$ Our main result

<span id="page-3-5"></span>**Theorem 2.1** (Quantitative two-chaos fourth moment theorem). For integers  $p \neq q$ , with p odd, q even, let

$$X = I_p(f), \qquad Y = I_q(g), \qquad Z = X + Y,\tag{5}$$

satisfying  $E[Z^2] = 1$ . Write  $\kappa_4(Z) = \mathbb{E}[Z^4] - 3$ . Then, we have

$$d_{\text{TV}}(Z, N(0, 1)) \leq \sqrt{6 \kappa_4(Z)}, \tag{6}$$

with  $d_{\text{TV}}$  the total variation distance. In particular, if  $Z_n = I_p(f_n) + I_q(g_n)$ with  $E[Z_n^2] = 1$  and  $\kappa_4(Z_n) \to 0$ , then

$$d_{\text{TV}}(Z_n, N(0, 1)) \longrightarrow 0.$$

**Proof.** We split the argument into four steps. Throughout, set  $\sigma_p^2 = E[Y^2]$ ,  $\sigma_q^2 = E[Z^2]$ ; then  $\sigma_p^2 + \sigma_q^2 = 1$ .

Step 1: Malliavin–Stein reduction. Applying (3) with  $F = Z = X + Y$  and using  $-DL^{-1}I_m(f) = \frac{1}{m}DI_m(f)$ ,

$$\left\langle DZ, -DL^{-1}Z \right\rangle = \frac{1}{p} \left\| DX \right\|^2 + \frac{1}{q} \left\| DY \right\|^2 + \left(\frac{1}{p} + \frac{1}{q}\right) \left\langle DX, DY \right\rangle. \tag{7}$$

Define the centered pieces

<span id="page-3-3"></span>
$$A_p := \sigma_p^2 - \frac{1}{p} \|DX\|^2 \,, \qquad A_q := \sigma_q^2 - \frac{1}{q} \|DY\|^2 \,, \qquad T := \left(\frac{1}{p} + \frac{1}{q}\right) \langle DX, DY\rangle \,. \tag{8}$$

Since  $\sigma_p^2 + \sigma_q^2 = 1$  and  $E \langle DX, DY \rangle = 0$  (orthogonality of different chaoses),

$$1 - \langle DZ, -DL^{-1}Z \rangle = A_p + A_q - T,$$

and hence

<span id="page-3-4"></span>
$$\operatorname{Var}(\langle DZ, -DL^{-1}Z \rangle) = E[(A_p + A_q - T)^2] \le 3\Big(E[A_p^2] + E[A_q^2] + E[T^2]\Big). \tag{9}$$

Step 2: Single-chaos control of  $A_p$  and  $A_q$ . For a fixed chaos  $F = I_m(f)$  with variance  $\sigma^2$ , the identity

<span id="page-3-1"></span>
$$E\left(\sigma^2 - \frac{1}{m} \left\|DF\right\|^2\right)^2 \le \frac{1}{3} \left(E[F^4] - 3\sigma^4\right) = \frac{1}{3} \kappa_4(F) \tag{10}$$

is classical (see, e.g., [\[5,](#page-11-6) (5.61)]). Applying [\(10\)](#page-3-1) with F = X and F = Y gives

<span id="page-4-1"></span>
$$E[A_p^2] \le \frac{1}{3} \kappa_4(X), \qquad E[A_q^2] \le \frac{1}{3} \kappa_4(Y).$$
 (11)

Step 3: Exact expansion of E ⟨DX, DY ⟩ 2 and comparison with Cov(X<sup>2</sup> , Y <sup>2</sup> ). Write m := min{p, q}. Using [\(4\)](#page-3-2) and [\(1\)](#page-2-1) for each t, and integrating over t,

$$\langle DX, DY \rangle = pq \sum_{s=1}^{m} (s-1)! \binom{p-1}{s-1} \binom{q-1}{s-1} I_{p+q-2s} \left(f \widetilde{\otimes}_s g\right). \tag{12}$$

By isometry and orthogonality of chaoses,

$$E\langle DX, DY\rangle^{2} = p^{2}q^{2} \sum_{s=1}^{m} \left[ (s-1)! \binom{p-1}{s-1} \binom{q-1}{s-1} \right]^{2} (p+q-2s)! \left\| f \widetilde{\otimes}_{s} g \right\|^{2}. \tag{13}$$

On the other hand, by [\[7,](#page-11-7) (3.5)],

<span id="page-4-0"></span>
$$\operatorname{Cov}(X^{2}, Y^{2}) = \sum_{s=1}^{m} \underbrace{\left[s! \binom{p}{s} \binom{q}{s}\right]^{2} (p+q-2s)! \left\|f \widetilde{\otimes}_{s} g\right\|^{2}}_{=:W_{s}} + \underbrace{p! \, q! \sum_{s=1}^{m} \binom{p}{s} \binom{q}{s} \left\|f \otimes_{s} g\right\|^{2}}_{\geq 0}.$$

Binomial identities yield

$$\left[pq\left(s-1\right)!\binom{p-1}{s-1}\binom{q-1}{s-1}\right]^2(p+q-2s)!\left\|f\widetilde{\otimes}_s g\right\|^2 = s^2 W_s.$$

Summing over s gives the exact identity

$$E\langle DX, DY\rangle^{2} = \sum_{s=1}^{m} s^{2} W_{s}, \quad \text{with} \quad W_{s} \text{ as in (14).}$$
 (15)

Since W<sup>s</sup> ≥ 0, we immediately obtain the universal comparison

$$E\langle DX, DY\rangle^{2} \leq m^{2} \sum_{s=1}^{m} W_{s} \leq m^{2} \operatorname{Cov}(X^{2}, Y^{2}). \tag{16}$$

Consequently, from [\(8\)](#page-3-3),

<span id="page-4-2"></span>
$$E[T^{2}] = \left(\frac{1}{p} + \frac{1}{q}\right)^{2} E \langle DX, DY \rangle^{2} \le 4 \operatorname{Cov}(X^{2}, Y^{2}). \tag{17}$$

Step 4: Parity-driven fourth-cumulant decomposition and conclusion. For general square-integrable U, V , one has

$$\kappa_4(U+V) = \kappa_4(U) + \kappa_4(V) + 6 \operatorname{Cov}(U^2, V^2) + 4 E[U^3 V] + 4 E[UV^3].$$

If U = X = Ip(f) with p odd and V = Y = Iq(g) with q even, then the mixed odd terms vanish:

$$E[X3Y] = E[XY3] = 0,$$
(18)

because in the product formula for (say) X3Y no zero-th chaos can appear (parity mismatch prevents total order from being zero). Hence

$$\kappa_4(Z) = \kappa_4(X) + \kappa_4(Y) + 6 \operatorname{Cov}(X^2, Y^2), \tag{19}$$

with all three terms on the right nonnegative (fixed-chaos fourth cumulants are nonnegative, and each summand in [\(14\)](#page-4-0) is nonnegative). In particular,

<span id="page-5-1"></span>
$$\operatorname{Cov}(X^2, Y^2) \leq \frac{\kappa_4(Z)}{6} \quad \text{and} \quad \kappa_4(X) + \kappa_4(Y) \leq \kappa_4(Z). \tag{20}$$

Now combining [\(9\)](#page-3-4), [\(11\)](#page-4-1), [\(17\)](#page-4-2) and [\(20\)](#page-5-1) yields

$$\operatorname{Var}(\langle DZ, -DL^{-1}Z \rangle) \leq \frac{3}{2} \kappa_4(Z).$$

Plugging this into [\(3\)](#page-3-0) implies the desired conclusion.

# <span id="page-5-0"></span>3 Poisson framework

In this section, we aim to establish the main results in the Poisson framework, in close analogy with the Gaussian case.

## 3.1 Preliminaries

First, we briefly recall the basic setup and notations in the Poisson space.

#### 3.1.1 Multiple Poisson–Itô integrals

Let η be a Poisson random measure on (E, E) with control µ, and let ηˆ = η − µ be its compensated version. For m ≥ 1 and f ∈ L 2 s (µ <sup>m</sup>), the multiple Poisson integral I η <sup>m</sup>(f) is defined by

$$I_m^{\eta}(f) = \int_{E^m} f(x_1,\ldots,x_m) \,\hat{\eta}(dx_1)\cdots\hat{\eta}(dx_m).$$

The collection of all such integrals spans the m-th Poisson chaos, denoted Cm. As in the Gaussian case, one has the isometry

$$E[I_m^{\eta}(f)I_m^{\eta}(g)] = m! \langle f, g \rangle_{L^2(\mu^m)},$$

and Poisson chaoses are mutually orthogonal: if F = I η p (f) and G = I η q (g) with p ̸= q, then E[F G] = 0.

#### <span id="page-5-2"></span>3.1.2 Fourth cumulant and positivity

For F = I η p (f), the fourth cumulant satisfies κ4(F) = E[F 4 ] − 3E[F 2 ] <sup>2</sup> ≥ 0, see [\[3,](#page-11-8) (2.5)]. Moreover, if F ∈ C<sup>p</sup> and G ∈ Cq, then Cov(F 2 , G<sup>2</sup> ) ≥ 0 as a consequence of [\[3,](#page-11-8) (2.4)]. These positivity properties play a crucial role in fourth-moment theorems on the Poisson space.

#### $3.2$ A Poisson counterpart of Theorem $2.1$

We now present the result we obtained as a Poisson analogue of Theorem  $2.1$ .

For two given integers  $p \neq q$ , let

<span id="page-6-0"></span>
$$X_n = I_p^{\eta}(f_n), \qquad Y_n = I_q^{\eta}(g_n), \qquad Z_n = X_n + Y_n, \qquad E[Z_n^2] = 1. \tag{21}$$

By orthogonality,  $E[X_n Y_n] = 0$ .

<span id="page-6-3"></span>**Theorem 3.1** (Fourth moment theorem under vanishing odd moments). In  $addition\ to\ (21),\ assume\ that$ 

<span id="page-6-1"></span>
$$E[X_n^3 Y_n] \to 0, \qquad E[X_n Y_n^3] \to 0.$$
 (22)

 $Then$ 

$$E[Z_n^4] \to 3 \quad \Longrightarrow \quad Z_n \Rightarrow \mathcal{N}(0,1)$$

*Proof.* We compute the fourth cumulant:

$$\kappa_4(Z_n) = \kappa_4(X_n) + \kappa_4(Y_n) + 6 \operatorname{Cov}(X_n^2, Y_n^2) + 4E[X_n^3 Y_n] + 4E[X_n Y_n^3].$$

On the Poisson space, each individual fourth cumulant is nonnegative and  $\text{Cov}(X_n^2, Y_n^2) \geq 0$ , see Section 3.1.2. By assumption, the mixed odd terms vanish in the limit. Therefore, if  $E[Z_n^4] \to 3$ , we obtain  $\kappa_4(Z_n) \to 0$ , which forces  $\kappa_4(X_n) \to 0$  and  $\kappa_4(Y_n) \to 0$ .

The fourth moment theorem on the Poisson chaos (see [3, Corollary 1.3])<br>then yields  $X_n \Rightarrow \mathcal{N}(0, \sigma_p^2)$  and  $Y_n \Rightarrow \mathcal{N}(0, \sigma_q^2)$  with  $\sigma_p^2 + \sigma_q^2 = 1$  (possibly<br>along a subsequence). Since  $E[X_n Y_n] = 0$ , the Peccati–Tudor Poisson chaoses (see [3, Corollary 1.8]) implies  $(X_n, Y_n) \Rightarrow (G_p, G_q)$  with  $G_p, G_q$ independent Gaussian variables. Hence  $Z_n = X_n + Y_n \Rightarrow \mathcal{N}(0,1)$ .  $\Box$ 

#### $3.3$ A counterexample when $(22)$ is not satisfied

Consider the following particular case: take a measurable set A with  $\mu(A) = 1$ ,  $\text{and set}$ 

$$U := I_1^{\eta}(\mathbf{1}_A) = N_A - 1$$

where  $N_A$  is Poisson distributed with mean 1, and

$$V := I_2^{\eta}(\mathbf{1}_A^{\otimes 2}) = (N_A - 1)^2 - N_A$$

Clearly,  $U \in C_1$  and  $V \in C_2$ , with  $E[U] = E[V] = 0$ ,  $Var(U) = 1$ ,  $Var(V) = 2$ , and  $E[UV] = 0$ .

For  $\alpha \in \mathbb{R}$ , define

$$S_{\alpha} := c(\alpha)(U + \alpha V), \qquad c(\alpha) := \frac{1}{\sqrt{1 + 2\alpha^2}},$$

so that  $\text{Var}(S_{\alpha}) = 1$ .

<span id="page-6-2"></span>**Proposition 3.2.** There exists  $\alpha_* \in \mathbb{R}$  such that the random variable  $S_{\alpha_*}$  $satisfies$ 

$$E[S_{\alpha_*}^2] = 1, \qquad E[S_{\alpha_*}^4] = 3,$$

while  $S_{\alpha_{*}}$  is not Gaussian. In fact,  $E[S_{\alpha_{*}}^{3}] \neq 0$ .

Proof of Proposition  $3.2$ . It is divided into three steps.

*Moments of U and V.* Recall  $U = N_A - 1$  with  $N_A \sim \text{Poi}(1)$ . Then the centered moments of  $U$  are

$$E[U^2] = 1, \quad E[U^3] = 1, \quad E[U^4] = 4.$$

Similarly,  $V = (N_A - 1)^2 - N_A$ . A straightforward computation yields

$$E[V^2] = 2, \quad E[UV] = 0.$$

Further mixed moments can be obtained by direct expansion in terms of  $N_A$  (or via the explicit Charlier polynomial representation). One finds

$$E[U^2V] = 6,$$
  $E[UV^3V] = 6,$   $E[UV^2] = 12,$   
 $E[U^2V^2] = 18,$   $E[UV^3] = 56,$   $E[V^3] = 12,$   
 $E[V^4] = 212.$ 

Fourth moment of  $S_{\alpha}$ . We expand

$$E[S_{\alpha}^{4}] = c(\alpha)^{4} E[(U + \alpha V)^{4}].$$

Using the values above,

$$E[S_{\alpha}^{4}] = \frac{4 + 24\alpha + 108\alpha^{2} + 224\alpha^{3} + 212\alpha^{4}}{(1 + 2\alpha^{2})^{2}}.$$

Setting  $E[S^4_{\alpha}] = 3$  yields the quartic equation

$$200\alpha^4 + 224\alpha^3 + 96\alpha^2 + 24\alpha + 1 = 0.$$

This equation has a real solution  $\alpha_* \approx -0.050832$ . For this value, we have

$$E[S_{\alpha_*}^2] = 1, \qquad E[S_{\alpha_*}^4] = 3.$$

Third moment of  $S_{\alpha_{*}}$ . Expanding and Inserting the values of the mixed moments gives

$$E[S_{\alpha}^{3}] = c(\alpha)^{3}(1 + 6\alpha + 12\alpha^{2} + 12\alpha^{3}).$$

At  $\alpha = \alpha_*$  this equals approximately  $0.719 \neq 0$ . Thus  $S_{\alpha_*}$  has variance one, fourth moment equal to three, and nonzero third moment. Consequently, its distribution cannot be Gaussian.  $\Box$ 

As a consequence, the conclusion of Theorem 3.1 may fail without assumption  $(22)$ .

#### <span id="page-7-0"></span>4 $GPT-5$ as a research assistant

As mentioned in the introduction, we asked GPT-5 to turn the limit theorem proved in [1] into a quantitative one, by deriving explicit bounds on the total variation distance to the Gaussian law. To the best of our knowledge, this problem was open. Not in the sense of being particularly difficult, but simply because it had not previously been investigated.

We now describe the process we followed in detail.

#### $4.1$ Protocol followed

#### $4.1.1$ Gaussian framework

We started with the following initial prompt:

Paper 2502.03596v1 establishes a qualitative fourth moment theorem for the sum of two Wiener-Itô integrals of orders  $p$  and  $q$ , where  $p$  and  $q$  have different parities. Building on the Malliavin-Stein method (see 1203.4147v3 for details). could vou derive a quantitative version for the total variation distance, with a convergence rate depending solely on the fourth cumulant of this sum?

The first interaction (see Annex  $A.1$  for the entire discussion) was strikingly effective. GPT-5 produced a generally correct statement, using the right tools and approach. However, it made a reasoning error (leading to a wrong expression for  $\text{Cov}(Y^2, Z^2)$ ) that could have invalidated the whole proof if left unchecked. Noticing this, we then asked:

Can you check your formula for  $\mathrm{Cov}(Y^2,Z^2)$  and provide me with the details?

It complied, giving the requested details. However, the formula was still incorrect, and the accompanying explanation was also wrong. We then pointed out the error more precisely:

```
I think you are mistaken in claiming that (p+q)! \|u \widetilde{\otimes} v\|^2 =p!q!||u||^2||v||^2. Why should that be the case?
```

It eventually admitted (which is not surprising, since by alignment it usually agrees with us) that the statement was false, but more importantly, it understood where the mistake came from. This was followed by a reasoning and a formula that, this time, were correct.

Then, at our request, GPT-5 reformatted the result in the style of a research article, including an introduction, the presentation of our main theorem, its proof with all the details (correct this time!), and a bibliography. The exact  $prompt$  was:

Turn this into a research paper ready for submission. Follow my style (see attached paper 0705.0570v4): - start with an introduction giving some context, - then present the main result, followed by a very detailed proof where no step is left out, - finish with a complete bibliography. The final document should be a LaTeX file that I can compile.

Finally, we asked it to add a concluding section containing possible extensions of the result that could be envisaged in future work.

Can you add a "Concluding Remarks" section, where you summarize the main points and propose possible directions or extensions for future work?.

It complied and proposed a Concluding remarks section, which ended with the following lines:

Finally, one might ask whether the same approach can be adapted to other Gaussian settings (e.g., Gaussian subordinated fields, Breuer–Majortype theorems) or even to non-Gaussian frameworks where the Malliavin–Stein method has been successfully applied.

Building on this last suggestion (which is nothing extraordinary by the way, such extensions being quite natural in this context), we decided to continue our investigations and to explore an extension to the Poisson setting.

#### 4.1.2 Poisson framework

Since we found that the context window was already rather long and that this might possibly alter its performance (as an overload of information may reduce effectiveness), we opened a new session (see Annex [A.2\)](#page-29-0) with the following short prompt:

Here is a paper (2502.03596v1) proving a fourth-moment theorem for the sum of two Wiener–Itô integrals with different parities. I would like you to extend it to the Poisson case, using the ideas contained in 1707.01889v2.

In this new session, GPT-5 quickly identified the structural difference with the Gaussian case: the mixed expectation E[X3Y ] does not necessarily vanish when X and Y are multiple Poisson integrals of different orders. On the other hand, it completely missed the fact that, just as in the Gaussian case, one still has Cov(X<sup>2</sup> , Y <sup>2</sup> ) ≥ 0 in the Poisson case. We then tried to put it on track by asking:

In paper 1707.01889v2, isn't there anything that could show that Cov(X<sup>2</sup> , Y <sup>2</sup> ) is always positive?

But since the question we asked was open-ended, this was not enough to trigger the right idea. With great confidence, it replied: "short answer: no" and then gave an unconvincing explanation as to why.

However, once we pointed out where to look:

What about (2.4)?

it immediately understood how (2.4) indeed implied that Cov(X<sup>2</sup> , Y <sup>2</sup> ) ≥ 0. It then reformulated its theorem to take this positivity into account, after we asked:

So, could you give the new statement of the theorem that this implies?

Finally, at our request, it also produced a counterexample showing that, without the assumptions imposed in the theorem, the conclusion may fail.

#### 4.1.3 Role of the AI

To summarize, we can say that the role played by the AI was essentially that of an executor, responding to our successive prompts. Without us, it would have made a damaging error in the Gaussian case, and it would not have provided the most interesting result in the Poisson case, overlooking an essential property of covariance, which was in fact easily deducible from the results contained in the document we had provided.

# <span id="page-10-0"></span>5 Some personal reflections

Overall, the experience of doing mathematics with GPT-5 was mixed. It felt very similar to working with a junior assistant at the beginning of a new project: exploring directions, formulating hypotheses, searching for counterexamples, and progressively adjusting statements. The AI showed a genuine ability to follow guided reasoning, to recognize its mistakes when pointed out, to propose new research directions, and to never take on the task. However, this only seems to support incremental research, that is, producing new results that do not require genuinely new ideas but rather the ability to combine ideas coming from different sources. At first glance, this might appear useful for an exploratory phase, helping us save time. In practice, however, it was quite the opposite: we had to carefully verify everything produced by the AI and constantly guide it so that it could correct its mistakes.

The main risk we see with this technology, in its current state, is that it will almost certainly lead to a proliferation of incremental results produced with AI. This could saturate the scientific landscape with technically correct but only moderately interesting contributions, making it harder for truly original work to stand out. The situation is reminiscent of other cultural domains already transformed by mass generative technologies: a flood of technically competent but uninspired outputs that dilutes attention and raises the noise level.

We also foresee a second, more specific negative effect, concerning PhD students. Traditionally, when PhD students begin their dissertation, they are given a problem that is accessible but rich enough to help them become familiar with the tools, develop intuition, and learn to recognize what works and what does not. They typically read several papers, explore how a theory could be adapted, make mistakes, and eventually find their own path. This process, with all its difficulties, is part of what makes them independent researchers. If students rely too heavily on AI systems that can immediately generate technically correct but shallow arguments, they may lose essential opportunities to develop these fundamental skills. The danger is not only a loss of originality, but also a weakening of the very process of becoming a mathematician.

In conclusion, we are still far from sharing the unreserved enthusiasm sparked by Bubeck's post. Nevertheless, this development deserves close monitoring. The improvement over GPT-3.5/4 has been significant and achieved in a remarkably short time, which suggests that further advances are to be expected. Whether such progress could one day substantially displace the role of mathematicians remains an open question that only the future will tell.

# Acknowledgements

We gratefully acknowledge support from the Luxembourg National Research Fund (Grant O22/17372844/FraMStA).

# References

- <span id="page-11-3"></span>[1] Basse-O'Connor, Kramer-Bang and Svendsen (2025). Fourth-Moment Theorems for Sums of Multiple Integrals. arXiv:2502.03596.
- <span id="page-11-0"></span>[2] <https://x.com/SebastienBubeck/status/1958198661139009862>
- <span id="page-11-8"></span>[3] C. Döbler, A. Vidotto and G. Zheng (2018): Fourth moment theorems on the Poisson space in any dimension. Electron. J. Probab. 23: 1–27. arXiv:1707.01889
- [4] I. Nourdin (2008): Asymptotic behavior of weighted quadratic and cubic variations of fractional Brownian motion. Ann. Probab. 36(6), 2159–2175. arXiv:0705.0570
- <span id="page-11-6"></span>[5] I. Nourdin (2012): Lectures on Gaussian approximations with Malliavin calculus. Sém. Probab. XLV, 3–89. arXiv:1203.4147.
- <span id="page-11-2"></span>[6] I. Nourdin and G. Peccati (2012). Normal Approximations with Malliavin Calculus: From Stein's Method to Universality. Cambridge Univ. Press.
- <span id="page-11-7"></span>[7] I. Nourdin and J. Rosinski (2014). Asymptotic independence of multiple Wiener-Itô integrals and the resulting limit laws. Ann. Probab. 42(2), 497– 526
- <span id="page-11-4"></span>[8] D. Nualart and G. Peccati (2005). Central limit theorems for sequences of multiple stochastic integrals. Ann. Probab. 33(1), 177–193.
- <span id="page-11-5"></span>[9] D. Nualart (2006). The Malliavin Calculus and Related Topics, 2nd ed. Springer.
- <span id="page-11-1"></span>[10] <https://nitter.net/ErnestRyu/status/1958408925864403068>

# A Annexes

This appendix gathers supplementary material that illustrates the interaction protocol and the intermediate outputs produced during our experiment. The goal is to document the process in a transparent way and to offer visual evidence supporting the descriptions given in the main text.

## <span id="page-11-9"></span>A.1 Screenshots in the Gaussian case

The following screenshots relate to the Gaussian framework discussed in Section [2.](#page-2-0)

ChatGPT  $5 \vee$ 

![](_page_12_Picture_1.jpeg)

Paper 2502.03596v1 establishes a qualitative fourth moment theorem for the sum of two Wiener–Itô integrals of orders p and q, where  $\mathsf p$  and  $\mathsf q$  have different parities. Building on the Malliavin–Stein method (see 1203.4147v3 for details), could you derive a quantitative version for the total variation distance, with a convergence rate depending solely on the fourth cumulant of this sum?

Réflexion durant 3m 2s

Yes. Let  $X = Y + Z$  with

$$Y=I_p(u),\qquad Z=I_q(v),\qquad \mathbb{E}[X]=0,\quad \mathbb{E}[X^2]=1,$$

where  $p$  is odd and  $q$  is even (so  $p \neq q$ ). Write  $N \sim \mathcal{N}(0,1).$ 

# Step 1 — Malliavin-Stein starting point

For any  $F\in \mathbb{D}^{1,2}$  with  $\mathbb{E} F=0$ ,

$$d_{\text{TV}}(F, N) \ \leq \ 2 \, \mathbb{E} \left| 1 - \langle DF, -DL^{-1}F \rangle_H \right| \ \leq \ 2 \sqrt{\text{Var} \big( \langle DF, -DL^{-1}F \rangle_H \big)}$$

Here we used Cauchy–Schwarz for the second inequality.  $\Box$ 

# Step 2 — Decompose the Stein factor for $X=Y+Z$

Since  $-L^{-1}I_p=\frac{1}{p}I_p,$  we have

$$\langle DX, -DL^{-1}X\rangle = \frac{1}{p}\|DY\|^2 + \frac{1}{q}\|DZ\|^2 + \Big(\frac{1}{p} + \frac{1}{q}\Big)\langle DY, DZ\rangle.$$

Set  $\sigma_p^2 = \mathbb{E}[Y^2]$ ,  $\sigma_q^2 = \mathbb{E}[Z^2] = 1 - \sigma_p^2$ , and define

$$A_p = \sigma_p^2 - \frac{1}{p} \|D Y\|^2, \qquad A_q = \sigma_q^2 - \frac{1}{q} \|D Z\|^2.$$

Then

$$1 - \langle DX, -DL^{-1}X \rangle \; = \; A_p + A_q - \Big(\frac{1}{p} + \frac{1}{q}\Big) \langle DY, DZ \rangle$$

Hence

$$\text{Var}\big(\langle DX, -DL^{-1}X\rangle\big) = \mathbb{E}\Big(1-\langle DX, -DL^{-1}X\rangle\Big)^2 \ \leq \ 3\Big(\mathbb{E} A_p^2 + \mathbb{E} A_q^2 + \Big(\tfrac{1}{p} + \tfrac{1}{q}\Big)^2\mathbb{E}\langle DY, DZ\rangle^2\Big).$$

# Step 3 – Control each term by the fourth cumulant pieces

For a single chaos, the Malliavin identity (Lemma 5.3) yields, for any  $q\geq 1$  and  $\sigma^2=\mathbb{E}[F^2]$ ,

$$\mathbb{E}\Big(\sigma^2-\frac{1}{q}\|DF\|^2\Big)^2 \ \leq \ \frac{q-1}{3q}\left(\mathbb{E}[F^4]-3\sigma^4\right) = \frac{q-1}{3q}\,\kappa_4(F).$$

Applying this to  $Y$  and  $Z$  gives

$$\mathbb{E} A_p^2 \leq \frac{p-1}{3p} \, \kappa_4(Y), \qquad \mathbb{E} A_q^2 \leq \frac{q-1}{3q} \, \kappa_4(Z). \quad \text{:contentReference}[\text{oaicite:1}] \text{index=}1$$

For the cross term, expand  $\langle DY, DZ \rangle$  with the product formula; comparing the resulting chaos-bychaos coefficients with those of  $Y^2Z^2$  shows

$$\mathbb{E}\langle DY, DZ\rangle^2 \ \leq \ \big(\min(p,q)!\big)^2 \operatorname{Cov}(Y^2, Z^2),$$

(standard contraction calculus from the product formula). We will only use that  $\mathrm{Cov}(Y^2,Z^2)\geq 0$  for  $p\neq q$ .  $\hbox{\hbox{\LARGE$\circ$}}$ 

Finally, for different parities (odd  $p$ , even  $q$ ), the fourth cumulant of the sum splits as

$$\kappa_4(X)=\kappa_4(Y)+\kappa_4(Z)+6\operatorname{Cov}(Y^2,Z^2),$$

because the "odd mixed" fourth moments vanish in that case; in particular each term on the right is nonnegative. 🗅

# Step 4 — Put together a quantitative bound depending only on $\kappa_4(X)$

Combine the bounds above:

$$\begin{split} \operatorname{Var}\bigl(\langle DX, -DL^{-1}X\rangle\bigr) &\leq \frac{p-1}{p}\,\kappa_4(Y) + \frac{q-1}{q}\,\kappa_4(Z) \ + \ \frac{1}{2}\Bigl(\frac{1}{p} + \frac{1}{q}\Bigr)^2 \bigl(\min(p,q)!\bigr)^2\,\kappa_4(X) \ &\leq \Bigl[\frac{p-1}{p} + \frac{q-1}{q} + \frac{1}{2}\Bigl(\frac{1}{p} + \frac{1}{q}\Bigr)^2 \bigl(\min(p,q)!\bigr)^2\Bigr]\,\kappa_4(X), \end{split}$$

since  $\kappa_4(Y)+\kappa_4(Z) < \kappa_4(X)$  by the decomposition above.

Therefore.

$$d_{\text{TV}}(X, N) \ \leq \ 2 \, \sqrt{C_{p,q} \, \kappa_4(X)} \, , \qquad C_{p,q} := \frac{p-1}{p} + \frac{q-1}{q} + \frac{1}{2} \Big( \frac{1}{p} + \frac{1}{q} \Big)^2 \big( \min(p,q)! \big)^2 .$$

This is a fully quantitative "fourth-moment theorem" for the sum of two Wiener-Itô integrals of different parities: as soon as  $\kappa_4(X_n)\to 0$ , one gets the rate

$$d_{\text{TV}}(X_n, N) = O\!\big(\sqrt{\kappa_4(X_n)}\big),$$

with a constant depending **only** on the orders  $p, q$  (not on the kernels  $u, v$ ). It reduces to the classical single-chaos bound when the other term vanishes; compare Theorem 5.4 in the lectures.

References used above. Malliavin-Stein bound in total variation and the single-chaos moment identity/bound: 🗅 , 🗅 , 🗅 . Parity-based fourth cumulant decomposition and positivity of the mixed square covariance for different orders: 🕒 , 🗅 . The parity framework (two-chaos fourth-moment theorem) is from 2502.03596v1.  $\downarrow$ 

*Notes.* The constant  $C_{p,q}$  above is explicit but not sharp; improving the coefficient in the cross term only requires a finer comparison between  $\mathbb{E}\langle DY, DZ\rangle^2$  and  $\mathrm{Cov}(Y^2, Z^2)$  via the contraction formula (2.1). The dependence on  $\sqrt{\kappa_4(X)}$  matches the optimal order known on fixed chaoses.  $\Box$ 

Sources

0 0 0 0 1 C

Give me ALL the details so that I can carefully review them and directly integrate them into my research paper

Réflexion durant 3m 5s

Here is a complete, line-by-line derivation of a quantitative fourth-moment theorem—in total variation—for  $p\neq q,\;\;p\text{ odd},\;q\text{ even},\;\;\mathbb{E}[X^2]=1,$  $X = Y + Z = I_p(u) + I_q(v),$ whose rate depends only on the fourth cumulant  $\kappa_4(X) = \mathbb{E}[X^4] - 3.$  I keep all constants explicit in terms of  $p,q$ , and I cite every ingredient.

## Theorem (Quantitative two-chaos fourth-moment theorem, TV metric)

Let  $Y=I_p(u)\in \mathcal{H}_p$  and  $Z=I_q(v)\in \mathcal{H}_q$  be multiple Wiener–Itô integrals of orders  $p$  and  $q$  (over an isonormal Gaussian process), with  $p$  odd and  $q$  even, and assume  $\mathbb{E}[X^2] = \mathbb{E}[(Y+Z)^2] = 1.$  Then

$$d_{\text{TV}}(X,N) \ \leq \ 2 \sqrt{\,C_{p,q}\,\kappa_4(X)} \,\, ,$$

where  $N \sim \mathcal{N}(0,1)$  and

$$C_{p,q} \ := \ \frac{p-1}{p} \ + \ \frac{q-1}{q} \ + \ \frac{1}{2} \Big( \min\{p,q\} \Big)^2 \Big( \tfrac{1}{p} + \tfrac{1}{q} \Big)^2.$$

Consequently,  $\kappa_4(X_n)\to 0$  implies  $d_{\text{TV}}(X_n,N)\to 0$  with the quantitative rate  $O(\sqrt{\kappa_4(X_n)})$ .

#### Ingredients and preliminaries (with sources)

Chaoses, contractions, product formula. Multiple Wiener–Itô integrals  $I_r(\cdot)$  decompose  $L^2(\Omega)$  into orthogonal chaoses; the contraction  $f \otimes_r g$  and product formula

$$I_p(f)I_q(g) = \sum_{r=0}^{p\wedge q} r! \binom{p}{r} \binom{q}{r} \, I_{p+q-2r}(\widetilde{f\otimes_r g})$$

are standard, and will be used repeatedly. 🕒 🕒 🗅

Malliavin operators and chaos-action of  $L^{-1}.$  If  $F=\sum_{r\geq 1}I_r(f_r)$ , then  $D_tF=\sum_{r\geq 1}r\,I_{r-1}(f_r(\cdot,t))$ and  $L^{-1}F=-\sum_{r\geq 1}\frac{1}{r}I_r(f_r).$  In particular, for a single chaos component  $F=I_m(f)\cdot -DL^{-1}F=$  $\frac{1}{m} DF.$   $\Box$ 

Malliavin–Stein TV bound. For centered, unit-variance  $F\in\mathbb{D}^{1,2}$ ,

$$d_{\text{TV}}(F, N) \ \leq \ 2 \, \mathbb{E} \big| 1 - \langle DF, -DL^{-1}F \rangle \big| \ \leq \ 2 \sqrt{\text{Var} \big( \langle DF, -DL^{-1}F \rangle \big)}$$

(Second inequality by Cauchy–Schwarz.)

Fourth-cumulant decomposition for a mixed-parity sum. With  $X=Y+Z$  and  $p$  odd,  $q$  even, one has

$$\kappa_4(X) \ = \ \kappa_4(Y) \ + \ \kappa_4(Z) \ + \ 6 \, {\rm Cov}\big(Y^2, Z^2\big)$$

because the odd mixed moments vanish by parity (via the product formula). Moreover  $\text{Cov}(Y^2,Z^2)\geq 0.$ 0 0 0

Sharp chaos-wise fourth-moment control of the Stein factor. If  $F=I_m(f)$  with variance  $\sigma^2$ ,

$$\mathbb{E}\Big(\sigma^2 - \frac{1}{m}\|DF\|^2\Big)^2 \ \leq \ \frac{m-1}{3m}\Big(\mathbb{E}[F^4] - 3\sigma^4\Big)$$

(we will apply this with  $F=Y,Z$ ).  $\quad \Box$ 

# Proof

## Step 1: Expand the Stein factor for $X=Y+Z.$

Using  $-DL^{-1}Y=\frac{1}{p}DY$  and  $-DL^{-1}Z=\frac{1}{q}DZ$ , we have

$$\langle DX, -DL^{-1}X\rangle = \left\langle DY + DZ, \; \frac{1}{p}DY + \frac{1}{q}DZ \right\rangle = \frac{1}{p}\|DY\|^2 + \frac{1}{q}\|DZ\|^2 + \Big(\frac{1}{p} + \frac{1}{q}\Big)\langle DY, DZ\rangle.$$

By orthogonality of different chaoses,  $\mathbb{E}\langle DY,DZ\rangle=0$  (since  $DY\in$  chaos  $p-1$  and  $DZ\in$  chaos  $q-1$ , which are different when  $p\neq q$ ).  $\Box$ 

Define the centered pieces

$$A_p:=\mathbb{E}[Y^2]-\frac{1}{p}\|DY\|^2,\qquad A_q:=\mathbb{E}[Z^2]-\frac{1}{q}\|DZ\|^2,\qquad T:=\Big(\frac{1}{p}+\frac{1}{q}\Big)\langle DY,DZ\rangle.$$

Then, since  $\mathbb{E}[Y^2] + \mathbb{E}[Z^2] = \mathbb{E}[X^2] = 1$ , we have

$$1-\langle DX, -DL^{-1}X\rangle = A_p+A_q-T,$$

and  $\mathbb{E}[A_p] = \mathbb{E}[A_q] = \mathbb{E}[T] = 0.$ 

Therefore,

$$\begin{split} \operatorname{Var}\bigl(\langle DX, -DL^{-1}X\rangle\bigr) &= \mathbb{E}\bigl[(A_p+A_q-T)^2\bigr] \ \leq \ 3\Bigl(\mathbb{E}[A_p^2]+\mathbb{E}[A_q^2]+\mathbb{E}[T^2]\Bigr) \end{split}$$

 $\bigcap$ 

by  $(a+b+c)^2 \leq 3(a^2+b^2+c^2).$ 

Step 2: Control of  $\mathbb{E}[A_p^2], \mathbb{E}[A_q^2]$  by fourth cumulants.

Apply the single-chaos inequality to  $Y$  and  $Z$  (with  $\sigma^2=\mathbb{E}[Y^2],\mathbb{E}[Z^2]$  respectively):

$$\mathbb{E}[A_p^2] \ \leq \ \frac{p-1}{3p} \, \kappa_4(Y), \qquad \mathbb{E}[A_q^2] \ \leq \ \frac{q-1}{3q} \, \kappa_4(Z).$$

# Step 3: An exact contraction-level identity for $\mathbb{E}\langle DY,DZ\rangle^2$ and comparison with $\mathrm{Cov}(Y^2,Z^2).$

Write  $DY(t)=p\,I_{p-1}(u(\cdot,t))$  and  $DZ(t)=q\,I_{q-1}(v(\cdot,t)).$  Using the product formula on each  $t$  and integrating (one more contraction arises from the  $t$ -integration), we get the **chaos expansion** 

$$\langle DY, DZ \rangle = pq \sum_{r=1}^m (r-1)! \binom{p-1}{r-1} \binom{q-1}{r-1} I_{p+q-2r} \hspace{-0.1cm} \left( \widetilde{u \otimes_r v} \right) \hspace{-0.1cm}, \quad m := \min \{p,q\}.$$

(Here we used  $D_t I_p(u) = p I_{p-1}(u(\cdot,t))$  and the product formula; orthogonality of different orders ensures the chaotic decomposition.)

Squaring and taking expectations (orthogonality across distinct chaos orders),

$$\mathbb{E}\langle DY, DZ\rangle^{2} = p^{2}q^{2}\sum_{r=1}^{m}\left[(r-1)!\binom{p-1}{r-1}\binom{q-1}{r-1}\right]^{2}(p+q-2r)!\left\|\widetilde{u\otimes_{r}v}\right\|^{2}.\qquad(\bigstar)$$

Likewise, by the product formula applied to  $Y^2$  and  $Z^2$ ,

$$\operatorname{Cov}(Y^{2},Z^{2}) = \sum_{r=1}^{m} \left[ r! \binom{p}{r} \binom{q}{r} \right]^{2} (p+q-2r)! \left\| \widetilde{u \otimes_{r} v} \right\|^{2}, \qquad \qquad (\bigstar \bigstar)$$

and each summand is nonnegative (indeed  $\mathrm{Cov}(Y^2,Z^2)\geq 0$ ).  $\Box$ 

**Coefficient ratio.** Compare the coefficients in  $(\bigstar)$  and  $(\bigstar \bigstar)$ . For every  $r > 1$ ,

$$\frac{\left[pq\left(r-1\right)!\binom{p-1}{r-1}\binom{q-1}{r-1}\right]^2}{\left[r!\binom{p}{r}\binom{q}{r}\right]^2}=\frac{p^2q^2}{r^2}\cdot\left(\frac{r}{p}\right)^2\cdot\left(\frac{r}{q}\right)^2=r^2,$$

since  $\binom{p-1}{r-1}/\binom{p}{r}=r/p$  and  $(r-1)!/r!=1/r.$  Therefore,

$$\mathbb{E}\langle DY, DZ\rangle^2 \ = \ \sum_{r=1}^m r^2 \, \Big\{ \big[ r! \binom{p}{r} \binom{q}{r} \big]^2 (p+q-2r)! \, \|\widetilde{u\otimes_r v}\|^2 \Big\}.$$

Because each bracket is nonnegative, we immediately obtain the comparison

$$\boxed{\mathbb{E}\langle DY, DZ\rangle^2 \ \leq \ m^2 \operatorname{Cov}(Y^2, Z^2)} \ , \qquad m = \min\{p, q\}.$$

#### Step 4: Put the bounds together.

Recall  $T=(\frac{1}{n}+\frac{1}{q})\langle DY,DZ\rangle.$  Then

$$\mathbb{E}[T^2] \ \leq \ \left(\tfrac{1}{p} + \tfrac{1}{q}\right)^2 m^2 \operatorname{Cov}(Y^2, Z^2).$$

Collecting Step 1 and Step 2,

$$\text{Var}\big(\langle DX, -DL^{-1}X\rangle\big) \leq 3\Big(\tfrac{p-1}{3p}\kappa_4(Y) + \tfrac{q-1}{3q}\kappa_4(Z) + \Big(\tfrac{1}{p} + \tfrac{1}{q}\Big)^2m^2\operatorname{Cov}(Y^2, Z^2)\Big).$$

So

$$\textup{Var}\big(\langle DX, -DL^{-1}X\rangle\big) \leq \Big(\tfrac{p-1}{p} + \tfrac{q-1}{q}\Big)\kappa_4(Y) + \Big(\tfrac{p-1}{p} + \tfrac{q-1}{q}\Big)\kappa_4(Z) + \tfrac{1}{2}\Big(\tfrac{1}{p} + \tfrac{1}{q}\Big)^2m^2 \cdot 6\operatorname{Cov}(Y^2, Z^2).$$

Because  $\kappa_4(X)=\kappa_4(Y)+\kappa_4(Z)+6\text{Cov}(Y^2,Z^2)$  and all three pieces are nonnegative, we can bound the RHS by

$$\left(\frac{p-1}{p}+\frac{q-1}{q}+\frac{1}{2}\,m^2\big(\frac{1}{p}+\frac{1}{q}\big)^2\right)\kappa_4(X)=C_{p,q}\,\kappa_4(X),$$

with  $m=\min\{p,q\}.$  Combining this with the Malliavin–Stein TV bound finishes the proof:

$$d_{\text{TV}}(X, N) \ \leq \ 2 \sqrt{\text{Var}(\langle DX, -DL^{-1}X \rangle)} \ \leq \ 2 \sqrt{C_{p,q} \, \kappa_4(X)}.$$

(The first inequality is Theorem 5.2 in the survey, applied with  $F=X;$  the second is the variance bound we just proved.)  $\downarrow$ 

## **Remarks and refinements**

1. Tightness within a single chaos. If one of the components is zero (say  $Z\equiv 0$ ), the argument reduces to

$$d_{\text{TV}}(Y, N) \ \leq \ 2 \sqrt{\frac{p-1}{3p} \, \kappa_4(Y)},$$

which is the standard fourth-moment/Stein estimate on a fixed chaos (no extra factor  $3$  appears), directly from the single-chaos inequality.  $\Box$ 

- 2. Sharper cross-term constant (optional). The worst-case bound  $\mathbb{E}\langle DY,DZ\rangle^2\leq$  $m^2\text{Cov}(Y^2,Z^2)$  replaced  $r^2$  by  $m^2$  inside the sum. If one keeps the exact expansion  $\sum_r r^2(\cdots)$ and compares to  $\sum_r 1 \cdot (\cdots)$  , the effective multiplicative factor is the weighted average  $\sum_r r^2 w_r/\sum_r w_r$  with weights  $w_r:=[r!{p\choose r}{q\choose r}]^2(p+q-2r)!\,\widetilde{\|u\otimes_r v\|^2}.$  In specific models where contractions concentrate at small  $r$ , this strictly improves  $m^2$ .
- 3. Why parity matters. The equality  $\kappa_4(X) = \kappa_4(Y) + \kappa_4(Z) + 6\text{Cov}(Y^2, Z^2)$  relies on the mixed odd moments vanishing when  $p$  is odd and  $q$  is even—this is proved in Paper 2502 via repeated use of the product formula—and quarantees all terms are nonnegative (fourth cumulants on a fixed chaos are  $\geq 0$ ; the square-covariance is  $\geq 0$ ).  $\Box$

## References to the uploaded papers (where each cited fact appears)

- Malliavin–Stein TV bound  $d_{\text{TV}}(F,N) \leq 2\mathbb{E}|1-\langle DF, -DL^{-1}F\rangle|$ : Theorem 5.2.  $\Box$
- Single-chaos fourth-moment control  $\mathbb{E}(\sigma^2-\|DF\|^2/m)^2\leq \frac{m-1}{3m}(\mathbb{E}[F^4]-3\sigma^4)$ : inequality (5.61).
- Chaos expansion & product formula (definitions, contractions, orthogonality).
- Derivative identity  $D_t I_m(f) = m \, I_{m-1}(f(\cdot,t)).$
- **Pseudo-inverse**  $L^{-1}$  and its action on chaoses.  $\Box$
- Fourth-cumulant decomposition for mixed parity and positivity of  $\text{Cov}(Y^2, Z^2)$ .

## Copy-paste statement for your paper

**Theorem.** Let  $Y=I_p(u)\in \mathcal{H}_p$  and  $Z=I_q(v)\in \mathcal{H}_q$  with  $p$  odd and  $q$  even, and set  $X=Y+Z$ with  $\mathbb{E}[X^2] = 1.$  Then

$$d_{\text{TV}}(X, \mathcal{N}(0, 1)) \ \leq \ 2 \sqrt{\, C_{p,q} \, \kappa_4(X)} \, , \qquad C_{p,q} = \frac{p-1}{p} + \frac{q-1}{q} + \frac{1}{2} \Big( \min\{p,q\} \Big)^2 \Big( \frac{1}{p} + \frac{1}{q} \Big)^2.$$

In particular,  $d_{\text{TV}}(X, \mathcal{N}(0, 1)) = O(\sqrt{\kappa_4(X)})$  as  $\kappa_4(X) \downarrow 0$ .

**Proof.** Using the Malliavin–Stein bound  $d_{\text{TV}}(F,N) \leq 2\sqrt{\text{Var}(\langle DF, -DL^{-1}F\rangle)}$  for unit-variance  $F$  ,apply it to  $X=Y+Z$  and expand  $\begin{array}{l} \langle DX, -DL^{-1}X \rangle = \frac{1}{p} \|DY\|^2 + \frac{1}{q} \|DZ\|^2 + (\frac{1}{p} + \frac{1}{q}) \langle DY, DZ \rangle. \\ \text{Writing } A_p = \mathbb{E}[Y^2] - \|DY\|^2/p, A_q = \mathbb{E}[Z^2] - \|DZ\|^2/q, \text{ and } T = (\frac{1}{p} + \frac{1}{q}) \langle DY, DZ \rangle, \text{ one} \end{array}$  $\begin{array}{l} \mathsf{has} \operatorname{Var}(\langle DX, -DL^{-1}X \rangle) \leq 3(\mathbb{E}[A_p^2] + \mathbb{E}[A_q^2] + \mathbb{E}[T^2]). \end{array}$  $\text{Cov}(Y^2,Z^2)=\sum_{r=1}^mW_r$  with nonnegative weights  $W_r$ ; hence  $\mathbb{E}\langle DY,DZ\rangle^2\leq m^2\text{Cov}(Y^2,Z^2)$ ,  $m = \min\{p, q\}.$ Finally, since  $\kappa_4(X)=\kappa_4(Y)+\kappa_4(Z)+6\text{Cov}(Y^2,Z^2)$  in the mixed-parity case and all three addends are nonnegative, we arrive at  $\mathrm{Var}(\langle DX, -DL^{-1}X\rangle) \leq C_{p,q}\kappa_4(X)$  and conclude.  $\blacksquare$ 

All cited steps correspond to: Malliavin-Stein TV bound and the single-chaos fourth-moment control (survey 1203.4147v3, Thm 5.2 and (5.61)), the product formula and Malliavin derivative identities (survey §4), and the parity-based cumulant identity plus positivity (paper 2502.03596v1, §3). 🗅 🗅 🗅 0 0 0  $\downarrow$ 

If you'd like, I can also add a short appendix with the explicit coefficient-matching calculation turning  $(\bigstar)$ and  $(\bigstar\bigstar)$  into the  $r^2$  factor, so you can drop it straight into your manuscript.

Sources

0 0 0 0 1 C

Can you check your formula for  $Cov(Y^2, Z^2)$  and provide me with the details?

Réflexion durant 59s

Great question — yes, let's check it carefully and derive  $\mathrm{Cov}(Y^2,Z^2)$  from first principles, keeping every coefficient explicit.

Let  $Y=I_p(u)$  and  $Z=I_q(v)$  with symmetric kernels  $u\in L^2(\mathbb{R}^p_+), v\in L^2(\mathbb{R}^q_+)$ . Write  $\tilde{\cdot}$  for symmetrization and  $\otimes_r$  for the  $r$ -th contraction.

# 1) Start from the product formula for one product $YZ$

By the multiplication formula for multiple Wiener-Itô integrals,

$$YZ = \sum_{r=0}^m r! \binom{p}{r} \binom{q}{r} \ I_{p+q-2r}\! \left(\widetilde{u \otimes_r v}\, \right), \qquad m := \min\{p,q\}. \text{ (product formula)}$$

This is (4.43) in the survey.

# 2) Square and take expectation

Because different Wiener chaoses are orthogonal, only equal orders survive when we take expectations. Hence

$$\mathbb{E}\big[(YZ)^2\big] = \sum_{r=0}^m \Big(r! \binom{p}{r}\binom{q}{r}\Big)^2 \underbrace{\mathbb{E}\Big[I_{p+q-2r}(\widetilde{u\otimes_r v})^2\Big]}_{=(p+q-2r)!\,\|\widetilde{u\otimes_r v}\|^2}.$$

The isometry  $\mathbb{E}[I_k(f)^2] = k! \, \|f\|^2$  and orthogonality are stated around (4.37)–(4.39).  $\Box$ 

Therefore,

$$\mathbb{E}\big[Y^2Z^2\big] = \sum_{r=0}^m \Big(r! \binom{p}{r}\binom{q}{r}\Big)^2 \left(p+q-2r\right)! \, \left\|\widetilde{u\otimes_r v}\right\|^2. \tag{A}$$

## 3) Subtract the product of variances

We also know

$$\mathbb{E}[Y^2] = p! \, \|u\|^2, \qquad \mathbb{E}[Z^2] = q! \, \|v\|^2,$$

by the same isometry.  $\Box$ 

To pass from  $\mathbb{E}[(YZ)^2]$  to the covariance  $\mathrm{Cov}(Y^2,Z^2)$ , we must check that the  $r=0$  term in (A) equals  $\mathbb{E}[Y^2] \, \mathbb{E}[Z^2].$  Using symmetrization of the tensor product,

$$\|(p+q)\text{-}\mathrm{sym}(u\otimes v)\|^2 = \frac{p!\,q!}{(p+q)!}\,\|u\|^2\|v\|^2,$$

so that

$$\underbrace{(p+q)!\left\|\widetilde{u\otimes v}\right\|^2}_{\text{the }r=0\text{ summand in (A)}}=p!\,q!\,\|u\|^2\|v\|^2=\mathbb{E}[Y^2]\,\mathbb{E}[Z^2].$$

(Notation and use of symmetrization appear explicitly in the two-chaos paper; see the definition line "  $u \setminus \text{textlbrackbraccright} \ v$  denotes the symmetrization of the  $r\text{-contraction''}$  and surrounding discussion.)

## 4) Final covariance formula

Since the  $r=0$  summand cancels exactly with  $\mathbb{E}[Y^2]\,\mathbb{E}[Z^2]$  , we obtain:

$$\operatorname{Cov}(Y^{2},Z^{2}) = \sum_{r=1}^{\min(p,q)} \left(r! \binom{p}{r} \binom{q}{r}\right)^{2} (p+q-2r)! \left\|\widetilde{u \otimes_{r} v}\right\|^{2}. \tag{B}$$

Each term is nonnegative, hence  $\mathrm{Cov}(Y^2,Z^2)\geq 0$  (a fact also noted in the mixed-chaos paper via Üstünel–Zakai).

# Cross-check with the route via $Y^2$ and $Z^2$ separately (optional)

One could also expand  $Y^2$  and  $Z^2$  individually using (4.43) with  $f=g$ ; see equation (5.64) in the survey for  $F^2$  when  $F=I_q(f)\mathpunct{:}$ 

$$I_q(f)^2 = \sum_{s=0}^q s! \binom{q}{s}^2 \ I_{2q-2s}\big(\widetilde{f\otimes_s f}\big).$$

Then  $\mathbb{E}[Y^2Z^2]$  collects only pairs  $(s,t)$  with  $2p-2s=2q-2t$ ; arranging the combinatorics reproduces (B). 🗅 🗅

## What this fixes/clarifies

- The **exact** covariance is the sum over  $r=1,\ldots,\min(p,q)$  with coefficient  $(r! \binom{p}{r} \binom{q}{r})^2 (p+q-1)$  $2r)!$  multiplying  $\|\widetilde{u \otimes_r v}\|^2$ .
- The  $r=0$  term equals  $\mathbb{E}[Y^2]\mathbb{E}[Z^2]$  and therefore **drops out** in the covariance.
- ٠ This confirms the formula I used implicitly earlier and justifies comparing  $\mathbb{E}\langle DY,DZ\rangle^2$  to  $\mathrm{Cov}(Y^2,Z^2)$  by mapping both to sums over the **same contractions**. (The symmetrization notation and positivity are the precise bridge.)

If you want, I can also give a two-line "manuscript-ready" lemma stating (B) with a short proof via "square of the product" (Steps 1-3).

Sources

0 0 V 0 1 C

I think you are mistaken in claiming that  $(p+q)!|u\widetilde{p+q}|v|^2 = p!q!|u|^2.$  Why should that be the case?

Réflexion durant 2m 35s

You're absolutely right — that identity is **not** true in general. I mistakenly wrote

 $(p+q)!\left\|\widetilde{u\otimes v}\right\|^{2} \stackrel{\text{(wrong)}}{=} p!\,q!\,\|u\|^{2}\|v\|^{2},$ 

but, except in special cases, there are extra terms coming from **mixed contractions** between  $u$  and  $v$ .

Here is the correct statement (and why).

# The correct identity for $\|\widetilde{u\otimes v}\|^2$

Let  $u\in H^{\odot p}$  ,  $v\in H^{\odot q}$  (symmetric kernels). Write  $\otimes_r$  for the usual  $r$  -contraction (NP Def. 4.6) and  $\widetilde{\cdot}$  for symmetrization. Then

$$(p+q)! \left\|\widetilde{u\otimes v}\right\|^2 = p!\, q! \sum_{r=0}^m \binom{p}{r} \binom{q}{r} \left\|\, u\otimes_r v\,\right\|^2, \qquad m:=p\wedge q\ .$$

Sketch of proof: write the symmetrization explicitly as the average over  $S_{p+q\prime}$  square it, integrate and group pairs of permutations by the number  $r$  of indices shared between the two  $p$ -blocks. The integral attached to a given  $r$  reduces to  $\|u\otimes_r v\|^2$  (exactly the same counting used for  $f\otimes f$  in NP, eqs. (5.64)–(5.65), now with two different kernels), and the number of such pairs yields the binomial coefficients above. See the product/contract-ion framework in NP Thm. 4.7 and the permutation counting in (5.64)–(5.65) for the identical-kernel case; the mixed-kernel computation proceeds verbatim. 0 0

Two immediate consequences:

In general,

$$(p+q)! \left\| \widetilde{u \otimes v} \right\|^2 = p! \, q! \, \|u\|^2 \|v\|^2 \ + \ p! \, q! \sum_{r=1}^m \binom{p}{r} \binom{q}{r} \, \|u \otimes_r v\|^2,$$

so the equality I wrote earlier holds iff all mixed contractions vanish, i.e.  $u\otimes_r v=0$  for every  $1\leq$  $r \leq m.$  This occurs, for instance, if  $u$  and  $v$  are supported on orthogonal subspaces (no coordinates in common).

Counterexample (the simplest one):  $p=q=1, u, v \in H.$ Here  $\widetilde{u\otimes v}=\frac{1}{2}(u\otimes v+v\otimes u)$  and

$$2! \, \|\widetilde{u\otimes v}\|^2 = \|u\|^2 \|v\|^2 + \langle u,v\rangle^2,$$

which equals  $\|u\|^2\|v\|^2$  only when  $\langle u,v\rangle=0.$ 

# Why this matters for $\mathrm{Cov}(Y^2, Z^2)$

Let  $Y=I_p(u)$ ,  $Z=I_q(v).$  Using the product formula (NP Thm. 4.7),

$$YZ=\sum_{r=0}^m r! \binom{p}{r} \binom{q}{r} \ I_{p+q-2r} \widetilde{(u\otimes_r v)},$$

so

$$E[Y^2Z^2] = \sum_{r=0}^m \big(r! \binom{p}{r} \binom{q}{r} \big)^2 \, (p+q-2r)! \, \big\| \widetilde{u \otimes_r v} \big\|^2. \quad \text{(isometry)}$$

Subtracting  $E[Y^2]E[Z^2]=p!\|u\|^2\,q!\|v\|^2$  and using the correct identity for the  $r=0$  term gives the clean decomposition

$$\operatorname{Cov}(Y^2,Z^2) = p!\, q! \sum_{r=1}^m \binom{p}{r} \binom{q}{r} \Vert u \otimes_r v \Vert^2 \ + \ \sum_{r=1}^m \big(r! \binom{p}{r} \binom{q}{r} \big)^2 \, (p+q-2r)! \, \big\Vert \widetilde{u \otimes_r v} \big\Vert^2.$$

For  $p=q=1$  this yields  $\mathrm{Cov}(Y^2,Z^2)=2\langle u,v\rangle^2$ , as it should.

In particular, keeping just the  $r=1$  piece recovers the classical nonnegativity lower bound

$$\mathrm{Cov}(Y^2, Z^2) \ \ge \ p! \ q! \ pq \ \| u \otimes_1 v \|^2,$$

as cited in 2502.03596 (from Üstünel–Zakai).

All ingredients used above — contractions, product formula, square-expansion and the permutation counting behind symmetrization — are exactly those in NP §4–5.

Thanks for flagging this  $-$  I've corrected the step and, downstream, any place where I had implicitly canceled the  $r=0$  term. The right way is to use the identity with mixed contractions; only when all  $u\otimes_r$  $v~(r\geq 1)$  vanish does the "naïve" equality hold.

Sources

0 0 0 0 1 C

So in the end, how do you prove the inequality in step 3 of your proof?

Réflexion durant 50s

You're asking about the key comparison used in **Step 3**, i.e.

$$\mathbb{E}\!\langle DY, DZ \big\rangle^2 \ \leq \ m^2 \operatorname{Cov}(Y^2, Z^2), \qquad m := \min\{p, q\},$$

for  $Y=I_p(u)$ ,  $Z=I_q(v)$  with symmetric kernels  $u\in H^{\odot p}$  ,  $v\in H^{\odot q}.$ Here is a fully explicit derivation.

# 1) Chaotic expansion of $\langle DY, DZ \rangle$

Write  $D_tY=p\,I_{p-1}(u(\cdot,t))$  and  $D_tZ=q\,I_{q-1}(v(\cdot,t)).$  Then

$$\langle DY, DZ \rangle = \int D_t Y \, D_t Z \, dt = p q \int I_{p-1}(u_t) \, I_{q-1}(v_t) \, dt, \quad u_t := u(\cdot, t), \ v_t := v(\cdot, t).$$

Apply the product formula to the integrand (for each fixed  $t$ ):

$$I_{p-1}(u_t)\,I_{q-1}(v_t) = \sum_{r=0}^{m-1} r! \binom{p-1}{r} \binom{q-1}{r}\,I_{p+q-2-2r}\!\big(\,\widetilde{\,u_t\otimes_r\,v_t}\,\big).$$

Integrate in  $t$  and use Fubini. The map  $t\mapsto u_t\otimes_r v_t$  integrates to the  $(r+1)$ -contraction of  $u$  and  $v$ :

$$\int \widetilde{u_t \otimes_r v_t} \, dt \; = \; \widetilde{\; u \otimes_{r+1} v} \, .$$

Hence, after reindexing  $s=r+1\in\{1,\ldots,m\}$  ,

$$\langle DY, DZ \rangle = \sum_{s=1}^{m} pq\left(s-1\right)! \binom{p-1}{s-1} \binom{q-1}{s-1} I_{p+q-2s}\!\!\left(\widetilde{u \otimes_s v}\right)\!. \tag{1}$$

Taking  $L^2$ -norms and using orthogonality of different chaoses,

$$\mathbb{E}\langle DY, DZ \rangle^{2} = \sum_{s=1}^{m} \left[ pq\left(s-1\right)! \binom{p-1}{s-1} \binom{q-1}{s-1} \right]^{2} (p+q-2s)! \left\| \widetilde{u \otimes_{s} v} \right\|^{2}. \tag{2}$$

# 2) Chaotic expansion of $\mathrm{Cov}(Y^2,Z^2)$

From the product formula for  $YZ$  and the isometry,

$$\mathbb{E}\big[Y^2Z^2\big] = \sum_{s=0}^m \Big[s! \binom{p}{s}\binom{q}{s}\Big]^2 \left(p{+}q{-}2s\right)! \ \big\|\widetilde{u\otimes_s v}\big\|^2.$$

Subtract  $\mathbb{E}[Y^2]\,\mathbb{E}[Z^2] = p!\|u\|^2\,q!\|v\|^2.$  Using the identity

$$(p+q)! \left\|\widetilde{u\otimes v}\right\|^2 = p!\, q! \sum_{r=0}^m \binom{p}{r} \binom{q}{r} \left\|u\otimes_r v\right\|^2,$$

the  $s=0$  term splits as the product of variances plus a **nonnegative** remainder. Thus

$$\operatorname{Cov}(Y^{2},Z^{2}) = \sum_{s=1}^{m} \underbrace{\left[s! \binom{p}{s} \binom{q}{s}\right]^{2} (p+q-2s)! \, \left\|\widetilde{u \otimes_{s} v}\right\|^{2}}_{=:W_{s}} \ + \ \underbrace{p! \, q! \sum_{s=1}^{m} \binom{p}{s} \binom{q}{s} \left\|u \otimes_{s} v\right\|^{2}}_{\geq 0}.(3)$$

In particular,

$$\operatorname{Cov}(Y^2,Z^2) \ \geq \ \sum_{s=1}^m W_s. \tag{4}$$

# 3) Coefficient-by-coefficient comparison

Compare the coefficients in (2) and the  $W_s$ -part of (3). Use

$$\binom{p-1}{s-1}=\frac{s}{p}\binom{p}{s}, \qquad \binom{q-1}{s-1}=\frac{s}{q}\binom{q}{s}, \qquad (s-1)!=\frac{s!}{s}.$$

Therefore

$$pq\,(s-1)!\binom{p-1}{s-1}\binom{q-1}{s-1} = pq\cdot\frac{s!}{s}\cdot\frac{s}{p}\binom{p}{s}\cdot\frac{s}{q}\binom{q}{s} = s\cdot s!\binom{p}{s}\binom{q}{s}.$$

Squaring and comparing to  $W_s$  gives, termwise,

$$\left[ pq\left( s-1\right) !\binom{p-1}{s-1}\binom{q-1}{s-1}\right] ^{2}\left( p+q-2s\right) !\left\Vert \widetilde{u\otimes_{s}v}\right\Vert ^{2}=s^{2}\,W_{s}.$$

Hence, from (2),

$$\mathbb{E}\!\!\left\langle DY, DZ \right\rangle^2 = \sum_{s=1}^m s^2 \, W_s. \tag{5}$$

# 4) Conclude the inequality

Combine (5) with (4):

$$\mathbb{E}\!\!\left\langle DY, DZ \right\rangle^2 = \sum_{s=1}^m s^2 W_s \ \leq \ \Big( \max_{1 \leq s \leq m} s^2 \Big) \sum_{s=1}^m W_s \ \leq \ m^2 \sum_{s=1}^m W_s \ \leq \ m^2 \operatorname{Cov}(Y^2, Z^2).$$

This proves the claimed comparison, with no parity assumption needed.

Finally, the exact term used in the TV bound is

$$\mathbb{E}\!\big[T^2\big] = \left(\tfrac{1}{p} + \tfrac{1}{q}\right)^2 \mathbb{E}\!\big\langle DY, DZ\big\rangle^2 \ \leq \ \Big(\tfrac{1}{p} + \tfrac{1}{q}\Big)^2 m^2 \operatorname{Cov}(Y^2, Z^2).$$

## Optional sharpening (if you want a tighter constant)

From (5) and (4),

$$\mathbb{E}\!\!\left\langle DY, DZ \right\rangle^2 = \Big(\sum_{s=1}^m s^2 W_s\Big) \leq \Big(\frac{\sum_{s=1}^m s^2 W_s}{\sum_{s=1}^m W_s}\Big) \operatorname{Cov}(Y^2, Z^2),$$

so the optimal multiplicative factor is the **weighted average**  $\sum s^2W_s/\sum W_s\in[1,m^2]$  (weights  $W_s$ ). In concrete models where contractions concentrate on small  $s$ , this improves the universal  $m^2$ .

![](_page_27_Picture_0.jpeg)

Turn our discussion into a research paper prepared for journal submission.

Follow my writing style (see the attached paper 0705.0570v4 as a reference).

The paper must include:

- Introduction: provide background and context for the work.
- Main result: clearly state the central contribution.
- Detailed proof: give a step-by-step proof with no steps omitted.
- Bibliography: include a complete and properly formatted list of references.

The final output should be a LaTeX file that compiles without errors.

Réflexion durant 1m 28s

🗇 Copier le code latex \documentclass[11pt]{article} \usepackage[a4paper,margin=1in]{geometry} \usepackage{amsmath,amssymb,amsthm,mathtools} \usepackage{bm} \usepackage{hyperref}  $\downarrow$ 

\newblock \emph{Lectures on Gaussian approximations with Malliavin calcu $\overset{\cdot\cdot\cdot\cdot}{\bigcirc}$ Copier $\text{le code}$ \newblock arXiv:1203.4147v3, 2012.

### \bibitem{Parity-Paper}

{[Mixed-parity two-chaos fourth-moment theorem]} \newblock \emph{A qualitative fourth-moment theorem for sums of two Wiener---It\^o integ \newblock arXiv:2502.03596v1, 2025.

\bibitem{Nourdin-AOP-Style}

I.~Nourdin,

\newblock Asymptotic behavior of weighted quadratic and cubic variations of fractional \newblock \emph{Ann.\ Probab.} \textbf{36} (2008), no.\ 6, 2159--2175. % Style referenc

#### \end{thebibliography}

% The manuscript is inspired in presentation by \cite{Nourdin-AOP-Style}. <pre>% CITATION ANCHOR FOR ATTACHED STYLE PDF (ignored by LaTeX compiler):</pre>

<pre>% :contentReference[oaicite:0]{index=0}</pre>

#### \end{document}

Sources

0 0 V 0 1 C

Can you add a "Concluding Remarks" section, where you summarize the main points and propose possible directions or extensions for future work?

latex

Copier le code

\section{Concluding Remarks}

In this work we established a quantitative fourth-moment theorem in total variation dis The proof relies crucially on two key ingredients: (i) a sharp single-chaos control of Several natural directions emerge for further investigation. First, one could study whe We hope that the techniques introduced here will serve as a stepping stone toward a bro

0 0 V 0 1 C

#### <span id="page-29-0"></span>Screenshots in the Poisson case $\mathbf{A.2}$

This second series of screenshots corresponds to the Poisson framework of Sec- $\text{tion } 3.$ 

ChatGPT 5 ~

![](_page_29_Picture_3.jpeg)

Here is a paper (2502.03596v1) proving a fourth moment theorem for the sum of two multiple Wiener-Itô integrals with different parities. I would like you to extend it to the Poisson case, using the ideas contained in 1707.01889v2.

Réflexion durant 3m 10s

Here's a clean Poisson-chaos analogue of Theorem 1.1 in 2502.03596. phrased so the proof can be done with the Döbler-Vidotto-Zheng (DVZ) exchangeable-pairs/spectral method (1707.01889).

# Theorem (Poisson two-chaos fourth-moment theorem, different orders)

Fix integers  $p\neq q$  and let  $\{X_n\}$  be real random variables on a Poisson space with chaos decompositions

$$X_n = Y_n + Z_n, \qquad Y_n = I^p_\eta(f_n), \ Z_n = I^q_\eta(g_n),$$

where  $f_n\in L^2_s(\mu^p),\;g_n\in L^2_s(\mu^q).$  Assume  $\mathbb{E}[X_n^2]=1$  for all  $n$  and  $\mathbb{E}[X_n^4]\to 3.$ 

Suppose, in addition, that the **mixed-terms are asymptotically negligible** in the following sense:

$$\mathbb{E}[Y_n^3 Z_n] \rightarrow 0, \quad \mathbb{E}[Y_n Z_n^3] \rightarrow 0, \quad \text{and} \quad \text{Cov}(Y_n^2, Z_n^2) \rightarrow 0. \tag{A}$$

(Concrete sufficient kernel conditions for (A) are listed just below.)

Then 
$$X_n \Rightarrow N(0,1).$$

#### Sufficient kernel-level conditions for (A)

A convenient way to guarantee (A) is to impose that all "odd total" cross star-contractions vanish:

$$\|f_n\star^{\ell}_r g_n\|_{L^2(\mu^{p+q-r-\ell})}\equiv 0 \quad \text{for every } 1\leq r\leq p\wedge q,\ 0\leq \ell\leq r,\ r+\ell\text{ odd}, \tag{B1}$$

and, moreover, that all cross-contractions vanish in  $L^2$ :

$$\|f_n \otimes_r g_n\|_2 \to 0 \quad \text{for each } 1 \leq r \leq p \wedge q. \tag{B2}$$

(Heuristically: (B1) kills the odd mixed moments  $\mathbb{E}[Y_n^3Z_n]$ ,  $\mathbb{E}[Y_nZ_n^3]$ , while (B2) kills the residual energy in  $\mathrm{Cov}(Y_n^2, Z_n^2).$ 

#### Why this works (sketch, with the exact points where DVZ is used)

- 1. **Set-up on the Poisson space.** DVZ recall the chaos projections  $J_r$ , the Ornstein–Uhlenbeck generator  $L$ , and the carré du champ  $\Gamma$  (our workhorse objects) for the Poisson setting, together with the basic orthogonal decomposition and the Mehler/semigroup calculus; see (2.2)–(2.3) and surroundings.
- 2. Product/mixed expansions live on finitely many chaoses. For  $F=I^p_n(f), G=I^q_n(g),$  the product  $FG$  has a finite chaos expansion  $FG=\sum_{r=0}^{p+q}J_r(FG)$  with explicit top kernel  $h_{p+q}=f\widetilde{\otimes}g.$  This formalizes how mixed moments are built out of contractions/star-contractions.
- 3. Fourth-cumulant decomposition for a sum. For centered, orthogonal  $Y_n, Z_n$  (automatically orthogonal because they sit in distinct chaoses), one has the algebraic identity

$$\kappa_4(X_n) = \kappa_4(Y_n) + \kappa_4(Z_n) + 6 \ \mathrm{Cov}(Y_n^2, Z_n^2) + 4 \mathbb{E}[Y_n^3 Z_n] + 4 \mathbb{E}[Y_n Z_n^3]. \tag{*}$$

In the Wiener case, 2502.03596 shows that the two odd mixed moments vanish by parity, yielding their equation (3.1) with only the  $6\operatorname{Cov}(Y_n^2,Z_n^2)$  correction.  $\Box$ 

On the Poisson space, parity no longer kills the odd terms, so we **assume** (A) to suppress them.

Since  $\mathbb{E}[X_n^4]\to 3$  and  $\mathbb{E}[X_n^2]=1$ , we have  $\kappa_4(X_n)\to 0.$  With (A),  $(*)$  yields

$$\kappa_4(Y_n) + \kappa_4(Z_n) \longrightarrow 0. \tag{**}$$

#### 4. Turning $\kappa_4 \rightarrow 0$ into normal approximation in fixed Poisson chaoses.

DVZ give quantitative fourth-moment bounds on the Poisson space for a **fixed** chaos: for  $F=I_n^q(f)$ ,

 $\text{(e.g.)} \quad \left\|\mathcal{L}(F) - \mathcal{L}(N)\right\| \;\lesssim\; \sqrt{\mathbb{E}[F^4] - 3\mathbb{E}[F^2]^2},$ 

for smooth test functions (and even  $d_{TV}$  in the single-chaos case; see Remark 4.3). Hence,  $\kappa_4(F)\to 0$ implies  $F$  is asymptotically Gaussian. Apply this to  $F = Y_n$  and  $F = Z_n$ .  $\hfill \Box$ 

### 5. Joint (vector) normality, then the sum.

The DVZ multivariate Peccati–Tudor theorem shows that, once each coordinate  $Y_n$  and  $Z_n$  is asymptotically Gaussian and the covariance matrix converges, the vector  $(Y_n, Z_n)$  is asymptotically Gaussian as a whole; apply Corollary 1.8/ Theorem 1.7. Since  $Y_n$  and  $Z_n$  live in different chaoses they are uncorrelated, so the limiting covariance is diagonal and their sum  $X_n$  converges to  $N(0,1).$   $\quad \Box$ 6. Why (B1)-(B2) imply (A).

Using the finite chaos expansion of  $FG$  and the structure of contractions/star-contractions (step 2), (B1) forces the 0-th chaos component of  $Y_n^3Z_n$  and  $Y_nZ_n^3$  to be absent, giving  $\mathbb{E}[Y_n^3Z_n] =$  $\mathbb{E}[Y_n Z_n^3] = 0.$  Condition (B2), together with DVZ's spectral estimates for  $\Gamma$  and the variance of projections, kills the residual covariances:

$$\mathrm{Cov}(Y_n^2,Z_n^2) \leq \sqrt{\mathbb{E}[Y_n^4]} \, \sqrt{\mathbb{E}[Z_n^4]-3\mathbb{E}[Z_n^2]^2} \, \xrightarrow[n \to \infty]{} \, 0,$$

whenever cross-contractions vanish (see Lemma 2.3, case  $p < q$ ).  $\Box$ 

(If  $p=q$  , use the corresponding bound (2.8); our theorem assumes  $p\neq q$  , matching the "two different orders" setup.)

#### 7. How DVZ's exchangeable pairs enter the machinery.

Behind the quantitative bounds sits the thinning-based exchangeable pair  $(F,F_t)$  built from the Mehler semigroup on the Poisson space; the key identities (Prop. 3.2) link  $L,\Gamma$ , and a fourth-moment remainder, all controlled by  $\kappa_4$ . This is the reason the whole argument can be reduced to fourth cumulants on Poisson chaoses, analogously to the Gaussian case but via a different tool. 🕒

#### Remarks and variants

Why we don't claim a Poisson analogue of Theorem 1.2 (strict non-Gaussianity).

In the Wiener case, squares of different chaoses are positively correlated (Üstünel–Zakai), yielding  $\kappa_4(Y+Z)>0$  for odd/even parities.  $\Box$ 

On the Poisson space such unconditional positivity is not available; DVZ provide *upper* (not sign) controls for  $\mathrm{Cov}(F^2,G^2)$  via contractions. Hence we refrain from asserting  $\mathbb{E}[X^4]>3$  in full generality.

Minimal assumptions.

If you prefer to avoid (B1)–(B2), it suffices to assume (A) directly. In many applications (e.g., disjoint supports of  $f_n$  and  $g_n$ ; or vanishing cross-contractions by construction), (A) is automatic by the product decomposition of step 2.

Independence-style corollary.

If  $Y_n$  and  $Z_n$  are independent (e.g., built from independent Poisson measures), then (A) holds and the result follows immediately via the same route.

#### Quick pointer map

- Gaussian parity method and the identity for  $\kappa_4(Y+Z)$  (equations (3.1), (3.4) in 2502.03596).  $\hfill \Box$ . 0
- Poisson chaos calculus & projections  $J_r$ ; product  $FG=\sum_{r=0}^{p+q}J_r(FG)$ .  $\Box$
- DVZ quantitative fourth-moment bounds on Poisson chaos; single-coordinate fourth cumulant controls distance to Gaussian.
- DVZ multivariate Peccati–Tudor on the Poisson space.  $\bullet$
- DVZ bounds for  $\text{Var }\Gamma$  and  $\text{Cov}(F^2,G^2)$  in terms of fourth cumulants/contractions.  $\Box$
- Thinning / exchangeable pairs identities (Prop. 3.2).

If you'd like, I can turn this into a full paper-style write-up: statement + preliminaries on the Poisson space, a short section proving that  $(B1)-(B2) \Rightarrow (A)$  via contractions, and then a self-contained proof leveraging DVZ's bounds and their multivariate PT theorem.

Sources

 $\mathcal{O}$   $\mathcal{O}$   $\mathcal{O}$   $\mathcal{O}$   $\mathcal{O}$ 

In paper 1707.01889v2, isn't there anything that could show that  $Cov(X^2,Y^2)$  is always positive?

#### Réflexion durant 27s

Short answer: no—DVZ don't prove a general non-negativity result for  $\mathrm{Cov}(F^2,G^2)$  on the Poisson space.

What they *do* give is an upper-bound control (via chaos projections and Cauchy–Schwarz). In Lemma 2.3 they expand  $G^2 = \sum_k J_k(G^2)$  and, for  $p < q$ , deduce

$$\text{Cov}(F^2,G^2) = \mathbb{E}\Bigg[F^2\sum_{k=1}^{2q-1}J_k(G^2)\Bigg] \ \leq \ \sqrt{\mathbb{E}[F^4]}\ \Big(\sum_{k=1}^{2q-1}\text{Var}\,J_k(G^2)\Big)^{1/2},$$

then use their variance bound

 $\sum_{k=1}^{2p-1} \operatorname{Var} J_k(F^2) \leq \mathbb{E}[F^4] - 3\mathbb{E}[F^2]^2.$ This yields a *magnitude* estimate in terms of fourth cumulants, but no sign information.

By contrast, in the Gaussian/Wiener case there is a positivity theorem: squares of different chaoses are positively correlated (Üstünel-Zakai), which is exactly what 2502.03596 relies on to argue strict positivity of the fourth cumulant in that setting.

DVZ also note a strict inequality  $\mathbb{E}[F^4] > 3\mathbb{E}[F^2]^2$  for any non-degenerate single Poisson chaos (their Remark 5.2(1)), but again that concerns one coordinate's fourth cumulant—not the sign of  $\mathrm{Cov}(F^2,G^2).$ ٥  $\downarrow$ 

So: in DVZ there's no analogue of Üstünel–Zakai's positivity; only quantitative *upper* bounds for  $|\mathrm{Cov}(F^2, G^2)|$ .

Sources

000000

Réflexion durant 2m 5s

You're right to point at  $(2.4)$  — it *does* force a sign.

DVZ's Lemma 2.2 states

$$\textup{Var}\left(\Gamma(F,G)\right) \ \leq \ \frac{(p+q-1)^2}{4} \Big(\mathbb{E}[F^2G^2] - 2\,\mathbb{E}[FG]^2 - \textup{Var}(F)\,\textup{Var}(G)\Big),$$

for  $F\in C_p\cap L^4$  ,  $G\in C_q\cap L^4.$  Since the left-hand side is  $\geq 0$  and the prefactor is  $>0,$  the bracket must be  $\geq 0.$  Hence

 $\boxed{\ \operatorname{Cov}(F^2,G^2)\ \geq\ 2\,\mathbb{E}[FG]^2\ \geq 0\ \ }.$ 

In particular, if  $p\neq q$  then  $\mathbb{E}[FG]=0$  by chaos orthogonality, so  $\mathrm{Cov}(F^2,G^2)\geq 0.$   $\Box$ 

This is exactly the inequality DVZ use later when summing over coordinates (their  $(4.2)$ – $(4.3)$ ), yielding  $\sum_{i,j} \text{Var}(\Gamma(F_i,F_j)) \leq \frac{(2q_d-1)^2}{4} \big(\mathbb{E}\|F\|_4^4 - \mathbb{E}\|N\|_4^4\big),$  which again relies on the bracket being nonnegative.

So yes: within the Poisson-chaos setting of DVZ, (2.4) gives a universal lower bound (and in particular nonnegativity) for  $\mathrm{Cov}(F^2,G^2)$ .

Sources

0 0 0 0 ± C

So, could you give the new statement of the theorem that this implies?

*ନ* ⊘

Réflexion durant 2m 19s

Great question—(2.4) lets you strengthen the "sum of two chaoses" statements on the Poisson space. Here's a crisp version you can drop into your write-up.

# Theorem (Poisson, two different orders; non-Gaussianity under vanishing odd mixed terms)

Let  $Y=I^p_\eta(f)\in C_p$  and  $Z=I^q_\eta(g)\in C_q$  with  $p\neq q$  and  $\mathbb{E}Y=\mathbb{E}Z=0.$  Assume  $\mathbb{E}[Y^3Z]=$  $\mathbb{E}[YZ^3]=0.$  Then

$$\kappa_4(Y+Z) = \kappa_4(Y) + \kappa_4(Z) + 6 \operatorname{Cov}(Y^2,Z^2) \ \geq \ \kappa_4(Y) + \kappa_4(Z) \ \geq \ 0$$

where the inequality  $\text{Cov}(Y^2, Z^2) \geq 0$  uses Lemma 2.2, eq. (2.4) of Döbler–Vidotto–Zheng (DVZ) together with  $\mathbb{E}[YZ]=0$  for  $p\neq q.$  Hence, if at least one of  $Y,Z$  is non-degenerate, then  $\kappa_4(Y)+$  $\kappa_4(Z)>0$  (DVZ Remark 5.2(1)), so  $\mathbb{E}[(Y+Z)^4]>3$ ; in particular  $Y+Z$  is not Gaussian.  $\Box$   $\Box$ 

(Identity used: when the odd mixed terms vanish, the fourth cumulant of a sum decomposes as above; cf. the same computation in the Wiener case, eq. (3.1) of 2502.03596.)

# Theorem (Poisson, fourth-moment theorem for a sum of two different orders)

Let  $(X_n)$  be given by  $X_n=Y_n+Z_n$  with  $Y_n\in C_p$  ,  $Z_n\in C_q$  ,  $p\neq q$  , and  $\mathbb{E}X_n^2=1.$  Assume

$$\mathbb{E}[X_n^4] \to 3, \qquad \mathbb{E}[Y_n^3 Z_n] \to 0, \qquad \mathbb{E}[Y_n Z_n^3] \to 0.$$

Then  $X_n \Rightarrow N(0,1).$ 

Why: write

$$\kappa_4(X_n)=\kappa_4(Y_n)+\kappa_4(Z_n)+6\operatorname{Cov}(Y_n^2,Z_n^2)+4\mathbb{E}[Y_n^3Z_n]+4\mathbb{E}[Y_nZ_n^3]$$

By (2.4) of DVZ,  $\mathrm{Cov}(Y_n^2,Z_n^2)\geq 0$  because  $\mathbb{E}[Y_nZ_n]=0$  for  $p\neq q.$  Hence the assumptions force  $\kappa_4(Y_n)\to 0$ ,  $\kappa_4(Z_n)\to 0$  and  $\text{Cov}(Y_n^2,Z_n^2)\to 0.$  Applying DVZ's (qualitative) multivariate fourthmoment criterion coordinate-wise (Cor. 1.8) to  $(Y_n,Z_n)$  yields joint Gaussian convergence with independent components and therefore  $X_n \Rightarrow N(0,1).$ 

#### Remarks

- Compared to the Wiener case in 2502.03596, the only extra hypothesis you need on the Poisson space is the vanishing (or negligible) *odd* mixed fourth moments; parity alone does not kill them on Poisson. Once those are controlled, (2.4) removes any need to assume  $\mathrm{Cov}(Y_n^2,Z_n^2)\rightarrow 0$ —it becomes a consequence of  $\kappa_4(X_n) \to 0$ .  $\Box$
- The strict positivity of  $\kappa_4(F)$  for any non-degenerate single Poisson chaos  $F$  (DVZ Remark 5.2(1)) is ٠ what gives the "strictly  $>3$ " part in the first theorem.  $\Box$

If you'd like, I can also phrase kernel-level sufficient conditions (in terms of star-contractions) that ensure  $\mathbb{E}[Y^3Z] = \mathbb{E}[YZ^3] = 0$  in your Poisson setting.

Sources

 $\cap$   $\land$   $\varphi$   $\land$   $\varphi$ 

To compare with the Gaussian result, and to explain why we cannot avoid the assumption  $E[Y_n^3 Z_n] \to 0\$  and  $E[Y_n Z_n^3] \to 0\$ 0\$, can you find a simple counterexample showing that we can have multiple integrals \$Y\_n\$ and \$Z\_n\$ with different parities, where  $E[(Y_n + Z_n)^2] = 1$ ,  $E[(Y_n + Z_n)^4]$  to 3, but  $X_n + Y_n$ does not converge to a Gaussian?

Réflexion durant 3m 24s

Yes - here's a very concrete Poisson-chaos counterexample that does exactly that.

Take a Poisson random measure  $\eta$  on a space  $(\mathcal{X},\mu)$  and fix a measurable set  $A\subset\mathcal{X}$  with  $\mu(A)=1.$ Write  $\hat{\eta} = \eta - \mu$  and  $N := \eta(A) \sim \text{Poisson}(1).$ 

Define first- and second-chaos integrals (different parities):

- \*  $Y:=I_1(\mathbf{1}_A)~=~\int \mathbf{1}_A\,d\hat{\eta}~=~N-1$  (so  $\mathbb{E} Y=0,$   $\text{Var}(Y)=1$ ).
- $\bullet \quad Z:=I_2(g)$  with  $g(x,y)=\frac{1}{\sqrt{2}}\mathbf{1}_A(x)\mathbf{1}_A(y)\mathbf{1}_{\{x\neq y\}}.$  For this choice one checks (standard Charlier polynomial identity)

$$Z \; = \; \frac{(N-1)^2 - (N-1) - 1}{\sqrt{2}}.$$

Then  $\mathbb{E}Z=0, \operatorname{Var}(Z)=1,$  and  $\mathbb{E}[YZ]=0$  (orthogonality of different chaoses).

Now form the *unit-variance* sum

$$X \; = \; a \, Y + b \, Z, \qquad a^2 + b^2 = 1.$$

A direct (one-line) expansion gives

$$\mathbb{E}[X^4] = a^4 \mathbb{E}[Y^4] + 6a^2b^2 \mathbb{E}[Y^2Z^2] + b^4 \mathbb{E}[Z^4] + 4a^3b\,\mathbb{E}[Y^3Z] + 4ab^3\,\mathbb{E}[YZ^3].$$

For  $N \sim \text{Poisson}(1)$  the needed mixed moments are explicit:

$$\mathbb{E}[Y^4] = 4, \quad \mathbb{E}[Z^4] = 53, \quad \mathbb{E}[Y^2Z^2] = 9, \quad \mathbb{E}[Y^3Z] = 3\sqrt{2}, \quad \mathbb{E}[YZ^3] = 14\sqrt{2}.$$

Choose, for instance,

$$a = -0.9974260808, \qquad b = 0.0717022544 \quad (\text{so } a^2 + b^2 = 1).$$

Plugging these into the formula above yields

$$\mathbb{E}[X^4] = 3.0000000000$$
 (to machine precision),

while of course  $\mathbb{E}[X^2] = 1.$ 

Crucially,  $X$  is *not* Gaussian: it is a degree-2 polynomial in the integer-valued  $N$ , hence has a purely discrete law with atoms (a Gaussian is absolutely continuous). Thus we have a sequence  $X_n\equiv X$  (take the same  $Y,Z,a,b$  for all  $n)$  such that

$$\mathbb{E}[(Y_n+Z_n)^2]=1, \qquad \mathbb{E}[(Y_n+Z_n)^4]\to 3,$$

but  $Y_n+Z_n$  does not converge to a Gaussian (it is already non-Gaussian for every  $n$ ).

This shows exactly why, on the Poisson space, you cannot drop the assumptions  $\mathbb{E}[Y_n^3Z_n]\rightarrow 0$  and  $\mathbb{E}[Y_nZ_n^3]\rightarrow 0.$ 

In the Gaussian case those "odd" mixed terms vanish by parity, but here they do not—and they can be tuned to cancel the positive contributions from  $\kappa_4(Y)$ ,  $\kappa_4(Z)$ , and  $6\operatorname{Cov}(Y^2,Z^2)$ , forcing  $\mathbb{E}[(Y+Y^2,Z^2)]$  $|Z|^4| = 3$  while the sum remains manifestly non-Gaussian.

000000