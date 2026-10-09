# SECOND-ORDER MUON DONE RIGHT: A PRINCIPLED MARRIAGE OF SPECTRAL GEOMETRY AND CURVATURE

Tong Che NVIDIA Research tongc@nvidia.com

#### **ABSTRACT**

Muon's polar update is exact for an unweighted spectral geometry. We introduce Go-MUON, which uses a matched data-dependent geometry and reuses it across several optimization steps. Conditioned on any positive-definite left and right maps, its raw update exactly solves the corresponding weighted spectral oracle; this statement is independent of how the maps are estimated or how recently they were refreshed. For softmax cross-entropy, we quantify when the observed-label backward factor approaches the model Fisher and generalized Gauss-Newton factor. We also show that four-step refresh nearly preserves the tracking delay of slowly changing geometry while increasing stationary factor noise, making lazy geometry a compute-statistics tradeoff rather than a denoising mechanism. In a hash-matched Penn Treebank comparison, Go-MUON lowers the geometric mean of three fixed training-loss windows by 0.38% across three paired seeds. On Tiny Shakespeare, a completed three-seed comparison lowers the same trajectory summary by 3.71% against the registered Muon control. Four-step refresh also improves the late PTB training window and reduces mean step time by about 20%. On corrected independent-CLS modular addition, a formal one-seed-per-modulus screen finds that Go-MUON reaches sustained 99% held-out accuracy at update 290 versus 2320 for Muon on modulus 103, and at update 220 versus 4520 on modulus 107.

## 1 Introduction

For a matrix parameter  $W \in \mathbb{R}^{m \times n}$ , Muon applies a polar map to a momentum source M (Jordan et al., 2024). Up to the sign convention of the parameter update, the direction solves

$$\max_{\|D\|_{\text{op}} \le 1} \langle M, D \rangle = \|M\|_*, \qquad D = \text{Polar}(M). \tag{1}$$

This moves every nonzero singular direction equally under an operator-norm update budget.

The same construction extends to any declared symmetric positive-definite (SPD) coordinate maps  $P_A, P_B$ . The matched direction

$$D_0 = P_B \operatorname{Polar}(P_B M P_A) P_A$$

is the exact support direction of the ball  $\|P_B^{-1}DP_A^{-1}\|_{\text{op}} \leq 1$ . This separates two questions that are often conflated: the oracle is exact for the supplied geometry, while the choice and estimation of that geometry determine whether the direction is useful. Fisher semantics, Kronecker factorization, and factor freshness are not assumptions of the oracle statement.

GO-MUON instantiates the maps with inverse fourth roots of OAS-regularized activation and backpropagated-gradient second moments. Under softmax cross-entropy these observed-label factors approach model-Fisher/GGN factors when minibatch error vanishes and the predictive distribution approaches the data conditional. The quarter power tempers factor anisotropy relative to a full inverse, while a positive Frobenius graft restores Muon's update energy.

The geometry is refreshed every K=4 updates. Reuse steps skip activation retention, output-gradient hooks, moment construction, shrinkage, and factor eigendecompositions, while gradient

and momentum information remains current. The coefficient  $\beta_B^K$  preserves elapsed-step decay of the retained backward state. It does not reproduce the omitted minibatch averages: under stationary noise the resulting estimator is noisier than a per-step EMA, even though its average lag on a slowly varying signal is nearly unchanged.

Our contributions are:

- 1. a factor-agnostic formulation of the matched spectral oracle, together with quantitative conditioning, grafted-alignment, and cached-geometry bounds for the implemented direction;
- 2. a conditional empirical-Fisher-to-Fisher/GGN result for softmax backward factors and an exact variance—lag characterization of sparse  $\beta_B^K$  refresh;
- the GO-MUON system, which combines OAS K-FAC-style factors with hook-gated factor refresh, cached inverse fourth roots, and fresh gradient and momentum updates;
- 4. paired character-language-model experiments showing a 0.38% fixed-window trajectory reduction against Muon in a hash-matched PTB comparison, a 3.71% reduction against the registered Tiny Shakespeare Muon control, and a 0.798× mean-step-time ratio for four-step refresh; and
- 5. a corrected independent-CLS modular-addition screen in which GO-MUON reaches sustained 99% held-out accuracy at updates 290 and 220, versus 2320 and 4520 for Muon.

## 2 MATCHED SPECTRAL GEOMETRY

## 2.1 A FACTOR-AGNOSTIC ORACLE

Let  $P_B \in \mathbb{S}^m_{++}$ ,  $P_A \in \mathbb{S}^n_{++}$ , and define

<span id="page-1-4"></span>
$$C = P_B M P_A, q_P(D) = ||P_B^{-1} D P_A^{-1}||_{\text{op}}.$$
 (2)

For  $\rho \geq 0$ , consider the support problem

<span id="page-1-0"></span>
$$\max_{D} \langle M, D \rangle \quad \text{subject to} \quad q_P(D) \le \rho. \tag{3}$$

<span id="page-1-3"></span>**Theorem 1** (Matched spectral oracle). Let Q(C) be any support polar satisfying

$$Q(C) \in \arg \max_{\|U\|_{\text{op}} \le 1} \langle C, U \rangle$$
.

Then the value of Equation (3) is  $\rho \|C\|_*$ , and one maximizer is

<span id="page-1-1"></span>
$$D_{\rho} = \rho P_B Q(C) P_A. \tag{4}$$

At unit radius, write  $D_0 := D_1$ ; then

<span id="page-1-2"></span>
$$(M, D_0) = \langle C, Q(C) \rangle = ||C||_*.$$
 (5)

For  $M \neq 0$ , this quantity is strictly positive. Under the conventional minimization definition,  $-D_{\rho}$  is the LMO; the optimizer equivalently subtracts the positive-alignment direction  $D_{\rho}$ .

*Proof.* Set  $U = P_B^{-1}DP_A^{-1}$ , so  $D = P_BUP_A$ . Cyclicity of the trace gives

$$\langle M, D \rangle = \langle P_B M P_A, U \rangle = \langle C, U \rangle$$
.

The constraint is  $||U||_{op} \leq \rho$ . Operator/nuclear duality gives the value  $\rho ||C||_*$ , and mapping a support polar back gives Equation (4). This is the matrix specialization of the general preconditioned-norm pullback oracle (Veprikov et al., 2025).

**Polar selection.** If C has full rank  $k = \min(m, n)$ , its support polar is unique. At rank deficiency, the support maximizer is not unique: the canonical partial polar sets the null-space completion to zero, whereas the compact full-SVD polar used in our implementation supplies a semi-orthogonal completion. Both solve Equation (3), but the completion can affect a later Frobenius graft. For M = 0, every feasible point is optimal; the implementation defines  $D_0 = 0$  and skips the graft.

<span id="page-2-0"></span>**Corollary 2** (Cached geometry). For any cached SPD maps  $\widetilde{P}_A$ ,  $\widetilde{P}_B$  and any  $M \neq 0$ ,

<span id="page-2-1"></span>
$$\langle M, \widetilde{P}_B Q(\widetilde{P}_B M \widetilde{P}_A) \widetilde{P}_A \rangle = \|\widetilde{P}_B M \widetilde{P}_A\|_* > 0.$$
 (6)

Corollary 2 certifies exactness for the cached ball, not closeness to the current ball. With momentum, M is the source passed to the polar map; current-gradient alignment and finite-step loss change are separate properties. A scale-free comparison with current maps is possible. For

<span id="page-2-2"></span>
$$\Theta_t = \kappa_2(P_{B,t}^{-1}\widetilde{P}_B) \,\kappa_2(P_{A,t}^{-1}\widetilde{P}_A),\tag{7}$$

Proposition 7 shows that the cached direction, rescaled to its current weighted radius, achieves at least a  $\Theta_t^{-1}$  fraction of the current oracle value. This is conditional on coordinate-map drift; the present experiments do not measure  $\Theta_t$ .

#### 2.2 Why the Map-back matters

Conditioning only before the polar map need not preserve source alignment. For example, take

$$A=B=\mathrm{diag}(1/9,9), \qquad M=\begin{bmatrix} -1 & -4 \\ -2 & -6 \end{bmatrix}.$$

The inside-only score and its polar are

$$Z = B^{-1/2} M A^{-1/2} = \begin{bmatrix} -9 & -4 \\ -2 & -2/3 \end{bmatrix}, \quad \text{Polar}(Z) = \frac{1}{\sqrt{949}} \begin{bmatrix} -25 & -18 \\ -18 & 25 \end{bmatrix},$$

so

$$\langle M, \operatorname{Polar}(Z) \rangle = -\frac{17}{\sqrt{949}} < 0.$$
 (8)

A positive scalar graft cannot change this sign. The matched map-back instead optimizes in transformed coordinates and returns to the original tangent coordinates, yielding the positive identity in Equation (5).

#### 3 K-FAC-ROOT INSTANTIATION

#### 3.1 Observed-label factors and their interpretation

For a linear layer y = Wx, the implementation forms minibatch second moments

$$\widehat{A} = \frac{1}{N} \sum_{i=1}^{N} x_i x_i^{\top}, \qquad \widehat{B} = \frac{1}{N} \sum_{i=1}^{N} \delta_i \delta_i^{\top}, \qquad \delta_i = \frac{\partial \ell_i}{\partial y_i}.$$
 (9)

These are activation and observed-label backpropagated-gradient factors. K-FAC approximates an expected Kronecker block by a product of expected factors (Martens & Grosse, 2015). Calling  $\widehat{B}$  a Fisher factor requires an additional relation between the data conditional and the model predictive distribution (Kunstner et al., 2019).

For softmax cross-entropy, that relation can be quantified exactly. Fix an input x, write  $p = p_{\theta}(\cdot \mid x)$  and  $q = q(\cdot \mid x)$ , and let  $\delta_z = p - e_y$  be the logit gradient. Define

$$B_{q,z} = \mathbb{E}_{y \sim q}[\delta_z \delta_z^{\top}], \qquad B_{F,z} = \mathbb{E}_{y \sim p}[\delta_z \delta_z^{\top}] = \text{Diag}(p) - pp^{\top}.$$

For logits as natural parameters,  $B_{F,z}$  is also the output GGN factor (Martens, 2020).

<span id="page-3-1"></span>**Proposition 3** (Observed-label factor mismatch). Let r = q - p. Then

$$B_{q,z} - B_{F,z} = \text{Diag}(r) - pr^{\top} - rp^{\top}, \qquad ||B_{q,z} - B_{F,z}||_2 \le 3||q - p||_2.$$
 (10)

If  $\delta_l = J_l^{\top} \delta_z$ , where  $J_l$  is independent of y, then

$$||B_{q,l} - B_{F,l}||_2 \le 3||J_l||_2^2 ||q - p||_2.$$

*Proof.* Expanding  $\mathbb{E}_{y \sim q}[(p-e_y)(p-e_y)^{\top}]$  and subtracting  $\mathrm{Diag}(p)-pp^{\top}$  gives the identity. Then  $\|\mathrm{Diag}(r)\|_2 \leq \|r\|_2$  and  $\|pr^{\top}\|_2 = \|p\|_2\|r\|_2 \leq \|r\|_2$ . The hidden-layer result follows by congruence with  $J_l$ .

<span id="page-3-0"></span>**Corollary 4** (Conditional factor consistency). Consider a sequence  $\theta_j$  for which  $p_{\theta_j}(\cdot \mid x) \to q(\cdot \mid x)$  and  $\sup_i \|J_l(\theta_j)\|_2 < \infty$ . If a minibatch estimator  $\widehat{B}_{j,l}$  is consistent for  $B_{q,l}(\theta_j)$ , then

$$\|\widehat{B}_{i,l} - B_{F,l}(\theta_i)\|_2 \xrightarrow{p} 0$$

as both the effective sample size and j tend to infinity.

Corollary 4 requires realizability or predictive consistency; it is not a property of arbitrary training trajectories. It also applies only to the backward factor: the full block still incurs the K-FAC approximation

$$\mathbb{E}[(xx^{\top}) \otimes (\delta\delta^{\top})] \neq \mathbb{E}[xx^{\top}] \otimes \mathbb{E}[\delta\delta^{\top}]$$

in general. Moreover, the softmax Fisher always has the logit-shift null direction, and its remaining eigenvalues can vanish as p approaches a point mass. Absolute factor convergence therefore does not imply relative inverse-root accuracy near interpolation; the effective floor and conditioning bounds below must be included when analyzing the resulting geometry.

## 3.2 QUARTER-POWER GEOMETRY AND FROBENIUS GRAFT

Let  $A \succ 0$ ,  $B \succ 0$  denote the effective regularized factors. For  $0 \le \alpha \le 1/2$ , define

$$C_{\alpha} = B^{-\alpha} M A^{-\alpha},\tag{12}$$

$$D_{\alpha,0} = B^{-\alpha} Q(C_{\alpha}) A^{-\alpha}, \tag{13}$$

$$\widehat{D}_{\alpha} = D_{\alpha,0} \frac{\sqrt{k}}{\|D_{\alpha,0}\|_F}, \qquad k = \min(m, n).$$
(14)

The cases  $\alpha=0,1/4,1/2$  give Muon, the GO-MUON quarter-power geometry, and full-factor spectral map-back, respectively. The last is a spectral oracle in full-factor coordinates, not a natural-gradient step.

For  $\alpha = 1/4$ ,

$$||B^{1/4}DA^{1/4}||_{\text{op}} \le 1$$

is the operator-norm analogue of the square-root K-FAC quadratic geometry, since

$$\operatorname{vec}(D)^{\top} (A^{1/2} \otimes B^{1/2}) \operatorname{vec}(D) = \|B^{1/4} D A^{1/4}\|_F^2.$$
 (15)

Replacing the Frobenius norm by the operator norm is a design choice. Under the conditions of Proposition 3, this admits a root-Fisher/GGN interpretation; the oracle itself requires only SPD factors.

<span id="page-3-2"></span>**Proposition 5** (Grafted conditioning and source alignment). Let Q be the compact full-SVD support polar used by the implementation and let  $K_{AB} = \kappa_2(A)\kappa_2(B)$ . Let  $\kappa_+$  denote the ratio of largest to smallest nonzero singular value. For  $M \neq 0$ ,

$$\left| \left\langle M, \widehat{D}_{\alpha} \right\rangle \ge K_{AB}^{-\alpha} \|M\|_{*}, \qquad \kappa_{+}(\widehat{D}_{\alpha}) \le K_{AB}^{\alpha}.$$
 (16)

The first bound compares equal-Frobenius-radius source alignment with Muon's value  $\|M\|_*$ . At  $\alpha=1/4$ , the retained fraction is at least  $[\kappa(A)\kappa(B)]^{-1/4}$ . This is a worst-case conditioning certificate, not a pointwise ordering of Muon, quarter-power, and half-power directions. Appendix A gives the proof.

The positive graft preserves the oracle ray and sign:

$$\langle M, \widehat{D}_{\alpha} \rangle = \frac{\sqrt{k}}{\|D_{\alpha,0}\|_F} \|C_{\alpha}\|_* > 0.$$

It does not preserve the original unit-radius LMO. Its weighted spectral radius is the source-dependent value  $\sqrt{k}/\|D_{\alpha,0}\|_F$ .

The grafted direction is invariant to independent positive scalar rescalings of A and B. With the canonical polar—and with the compact polar at full rank—it is also equivariant under orthogonal changes of the input and output bases: replacing (M,B,A) by  $(UMV^\top,UBU^\top,VAV^\top)$  sends  $\widehat{D}_{\alpha}$  to  $U\widehat{D}_{\alpha}V^\top$ . At rank deficiency, a full-SVD null-space completion can break this equivariance. General affine reparameterization invariance does not follow because matrix powers and the polar map are not equivariant under arbitrary congruences (Luk & Grosse, 2018).

## 3.3 OAS FACTORS AND NUMERICAL SPD MAPS

Finite-minibatch factors can be singular. For a  $d \times d$  empirical second moment S built from N samples, we use Oracle Approximating Shrinkage (OAS) (Chen et al., 2010):

$$\lambda(S, N) = \operatorname{clip}_{[0,1]} \frac{(1 - 2/d)\operatorname{tr}(S^2) + \operatorname{tr}(S)^2}{(N + 1 - 2/d)(\operatorname{tr}(S^2) - \operatorname{tr}(S)^2/d)},\tag{17}$$

$$OAS(S) = (1 - \lambda)S + \lambda \frac{tr(S)}{d}I.$$
(18)

When  $\lambda > 0$  and tr(S) > 0,

<span id="page-4-0"></span>
$$\kappa_2(\mathrm{OAS}(S)) \le \frac{d - (d-1)\lambda}{\lambda}.$$
(19)

The implementation additionally floors eigenvalues at roundoff scale before taking inverse fourth roots. The resulting numerical SPD matrices, rather than the potentially singular raw moments, are the factors to which Theorem 1 and Proposition 5 apply.

Writing  $B_t^{\text{eff}}$  and  $\bar{B}_t^{\text{eff}}$  for the current and cached factors after shrinkage and the root routine's eigenvalue floor, Fisher-factor error has four distinct sources:

$$\|\bar{B}_{t}^{\text{eff}} - B_{F,t}\|_{2} \leq \underbrace{\|\widehat{B}_{t} - B_{q,t}\|_{2}}_{\text{finite sample}} + \underbrace{\|B_{q,t} - B_{F,t}\|_{2}}_{\text{model mismatch}} + \underbrace{\|B_{t}^{\text{eff}} - \widehat{B}_{t}\|_{2}}_{\text{shrinkage/floor}} + \underbrace{\|\bar{B}_{t}^{\text{eff}} - B_{t}^{\text{eff}}\|_{2}}_{\text{EMA and staleness}}.$$

$$(20)$$

The decomposition separates the conditional Fisher interpretation from the regularization and temporal choices used by the optimizer.

#### 3.4 Sparse refresh is a variance-lag tradeoff

At refresh step t, we compute

$$A_t = \text{OAS}(\widehat{A}_t), \qquad B_t = \text{OAS}(\widehat{B}_t).$$
 (21)

The first  $B_t$  initializes  $\bar{B}$ . Later refreshes use

$$\bar{B}_{t} = \beta_{B}^{K} \bar{B}_{t-K} + (1 - \beta_{B}^{K}) B_{t}.$$
(22)

The exponent applies K elapsed steps of decay to the retained state. It does not reproduce K per-step EMA observations. To characterize the difference, let  $X_t$  be a centered post-OAS factor observation and compare

$$Z_t = \beta_B Z_{t-1} + (1 - \beta_B) X_t$$

with the refresh-boundary process

$$Y_j = \beta_B^K Y_{j-1} + (1 - \beta_B^K) X_{jK}.$$

<span id="page-5-0"></span>Proposition 6 (Sparse-EMA covariance and lag). *If* vec(Xt) *is weakly stationary with finite covariance and both recursions are in steady state, then at refresh boundaries*

$$\operatorname{Cov}(\operatorname{vec} Y_j) \succeq \operatorname{Cov}(\operatorname{vec} Z_{jK}).$$
 (23)

*For temporally IID observations with covariance* Σ*,*

$$Cov(vec Y) = \frac{1 - \beta_B^K}{1 + \beta_B^K} \Sigma,$$
(24)

<span id="page-5-1"></span>
$$Cov(vec Z) = \frac{1 - \beta_B}{1 + \beta_B} \Sigma.$$
 (25)

*For an affine signal observed without noise, the phase-averaged lag of the held estimator is*

<span id="page-5-2"></span>
$$L_K = \frac{K\beta_B^K}{1 - \beta_B^K} + \frac{K - 1}{2}. (26)$$

At β<sup>B</sup> = 0.97, K = 4, the sparse-to-per-step variance ratio is 3.99537, while L<sup>4</sup> = 32.3714 steps versus L<sup>1</sup> = 32.3333. Thus sparse refresh nearly preserves average slow-signal lag while retaining about one quarter as many independent factor observations. Sampling occurs before the refreshdomain EMA, so high-frequency variation can alias. The activation factor A<sup>t</sup> has no EMA and is simply sampled and held.

Holding one geometry within each four-step block creates blockwise geometry coherence: the preconditioner does not rotate between minibatches inside the block. Whether this coherence stabilizes the optimizer trajectory is an empirical mechanism hypothesis, not a consequence of Proposition [6.](#page-5-0)

## 3.5 COMPLETE UPDATE

With K = 4, β<sup>B</sup> = 0.97, momentum coefficient β, and a Nesterov-style source, one optimizer step is:

if 
$$t \mod K = 0$$
:  $A_t, B_t \leftarrow \text{OAS K-FAC statistics},$  (27)

$$\bar{B}_t \leftarrow \beta_B^K \bar{B}_{t-K} + (1 - \beta_B^K) B_t, \tag{28}$$

$$P_A \leftarrow A_t^{-1/4}, \qquad P_B \leftarrow \bar{B}_t^{-1/4};$$
 (29)

$$M_t = \beta M_{t-1} + (1 - \beta)G_t, \tag{30}$$

$$\widehat{M}_t = (1 - \beta)G_t + \beta M_t, \tag{31}$$

$$C_t = P_B \widehat{M}_t P_A, \tag{32}$$

$$D_{0,t} = P_B \operatorname{Polar}(C_t) P_A, \tag{33}$$

$$D_t = D_{0,t} \frac{\sqrt{\min(m,n)}}{\|D_{0,t}\|_F},\tag{34}$$

$$W_{t+1} = W_t - \eta_t \sqrt{\max(1, m/n)} D_t.$$
 (35)

The learning rate η<sup>t</sup> follows a cosine schedule. Embeddings, normalization parameters, and other non-matrix parameters use AdamW [\(Kingma & Ba, 2015\)](#page-11-5).

The implementation gates its forward hooks before the model forward pass. On refresh steps it retains linear-layer inputs and registers output-gradient hooks. On reuse steps the hook returns immediately, bypassing activation storage, delta hooks, moment formation, OAS, and factor eigendecomposition. Momentum, the central polar map, grafting, and the parameter update execute every step.

## 3.6 COST

For a layer of shape m×n, a refresh computes moments and matrix functions of the m×m and n×n factors. Reuse eliminates those operations and their telemetry while retaining the matrix products and polar map needed for the direction. A refresh fraction of 1/K amortizes factor collection and decomposition across K updates. The experiments measure the resulting savings end to end.

# 4 RELATED WORK

## 4.1 MUON AND NORM-BASED MATRIX OPTIMIZATION

Muon applies an approximate polar map to momentum matrices, using Newton– Schulz iterations to make matrix updates approximately semi-orthogonal [\(Jordan et al., 2024\)](#page-11-0). The norm-based account of matrix optimization identifies this map as steepest descent under an operator-norm constraint, whose dual objective is the nuclear norm [\(Bernstein & Newhouse, 2024\)](#page-10-1). Modular norm optimization extends this viewpoint from individual matrices to composed neural-network modules [\(Large et al.,](#page-11-6) [2024\)](#page-11-6); Scion develops norm-constrained linear minimization oracles more generally [\(Pethick et al.,](#page-12-2) [2025\)](#page-12-2); and Gluon connects practical Muon-like updates with convergence theory for LMO-based optimization [\(Riabinin et al., 2025\)](#page-12-3). Subsequent systems work implements Muon at language-model scale [\(Liu et al., 2025\)](#page-11-7).

Several variants refine Muon's normalization while retaining a polar or orthogonalization core. Muon+ adds an additional normalization step [\(Zhang et al., 2026a\)](#page-12-4), while MuonEq uses inexpensive equilibration before orthogonalization [\(Chang et al., 2026\)](#page-10-2). These methods modify the matrix presented to the polar map. GO-MUON instead instantiates the general preconditioned-norm pullback oracle: the same SPD maps transform the source into polar coordinates and map the support direction back. Its positive Frobenius graft restores Muon's update energy while retaining that oracle ray.

## 4.2 KRONECKER CURVATURE AND STRUCTURED PRECONDITIONING

K-FAC approximates a layerwise model-Fisher block by the Kronecker product of an activation factor and a backward factor [\(Martens & Grosse, 2015\)](#page-11-1). It has been scaled through distributed factor formation, inversion, and communication [\(Osawa et al., 2019;](#page-11-8) [Pauloski et al., 2020\)](#page-11-9); SINGD gives an inverse-free, numerically stable structured natural-gradient formulation [\(Lin et al., 2024\)](#page-11-10). Full Gauss– Newton experiments on small language models demonstrate accurate layerwise curvature as a strong optimization oracle [\(Abreu et al., 2025\)](#page-10-3). GO-MUON uses observed-label second moments rather than model-sampled Fisher factors. Proposition [3](#page-3-1) quantifies when the backward factor approaches the Fisher/GGN factor; the distinction remains essential away from predictive consistency [\(Kunstner et al.,](#page-11-2) [2019\)](#page-11-2). K-FAC's natural-gradient update retains invariance to affine activation reparameterizations under its metric construction [\(Luk & Grosse, 2018\)](#page-11-4). The quarter-power spectral oracle retains only the orthogonal and scalar equivariances stated in Section 3.

Shampoo uses Kronecker-factored matrix moments and inverse matrix powers for large-scale preconditioning [\(Gupta et al., 2018\)](#page-11-11); scalable Shampoo amortizes these matrix operations in distributed training [\(Anil et al., 2020\)](#page-10-4). SOAP runs an Adam-like method in Shampoo's evolving eigenbasis [\(Vyas](#page-12-5) [et al., 2024\)](#page-12-5). The general theory of preconditioned matrix norms makes explicit how transformations inside and outside an LMO determine the corresponding steepest-descent geometry [\(Veprikov et al.,](#page-12-0) [2025\)](#page-12-0). Theorem [1](#page-1-3) is a Kronecker matrix instance of this general pullback, not a new duality principle. In GO-MUON, OAS-regularized activation and backward second moments select the geometry; Shampoo uses gradient moments. OAS was introduced as an automatic shrinkage estimator for finite-sample covariance matrices [\(Chen et al., 2010\)](#page-10-0); here it supplies isotropic shrinkage before the numerical eigenvalue floor.

## 4.3 CURVATURE-AWARE MUON VARIANTS

Mousse applies a quarter-power matched polar map with a Frobenius graft to Shampoo-style gradient-Gram geometry [\(Zhang et al., 2026b\)](#page-12-6). It updates factors every step, refreshes matrix functions periodically, and uses an inverse-power exponent below one quarter in its reported language-model

<span id="page-7-0"></span>Table 1: Relationship to representative structured matrix optimizers. "Factor skip" denotes steps that skip accumulation of the underlying second-moment factors.

| Method  | Statistical geometry                                 | Matrix update                              | Curvature amortization                                              |  |  |
|---------|------------------------------------------------------|--------------------------------------------|---------------------------------------------------------------------|--|--|
| Muon    | None                                                 | Polar(M)                                   | —                                                                   |  |  |
| K-FAC   | Activation/backward Fisher<br>factors                | Approximate natural<br>gradient            | Periodic inverse; later<br>systems also skip factors                |  |  |
|         | Scalable Shampoo Gradient Gram moments               | Kronecker inverse-power<br>preconditioning | Periodic roots; optional<br>factor skip                             |  |  |
| SOAP    | Shampoo moments and<br>eigenbasis                    | Adam in the Shampoo basis                  | Periodic eigenbasis refresh                                         |  |  |
| Mousse  | Shampoo gradient moments                             | Root-metric matched polar<br>with graft    | Factors frequent, matrix<br>functions periodic                      |  |  |
| FISMO   | Fisher/K-FAC factors                                 | Fisher-metric matched<br>spectral step     | Factors updated in its main<br>algorithm                            |  |  |
| GO-MUON | OAS observed-label<br>activation/backward<br>moments | Quarter-power matched<br>polar with graft  | Hook-gated factors and<br>roots every K; fresh source<br>every step |  |  |

experiments. The quarter-power matched-map structure and graft are shared. GO-MUON differs in its OAS activation/backward factor field, exact quarter-power instance, and hook-gated schedule that skips factor collection on reuse steps.

FISMO derives matched map-back for a Fisher-structured spectral trust region, yielding inverse half powers inside and outside the polar map [\(Xu et al., 2026\)](#page-12-7). GO-MUON uses the *square root* of the K-FAC block, yielding inverse fourth powers when the observed-label factors admit the conditional Fisher interpretation. Both are instances of matched spectral map-back at different exponents. Corollary [2](#page-2-0) gives positive source alignment for any cached SPD maps, independent of their Fisher semantics.

Other recent methods insert cheaper curvature information at different points in the Muon pipeline. Newton–Muon corrects the input side using activation moments before orthogonalization [\(Du &](#page-10-5) [Su, 2026\)](#page-10-5); Muon2 uses Adam-like second moments before orthogonalization and couples this with efficient polar computation [\(Liu et al., 2026\)](#page-11-12); and MALT uses lightweight diagonal preconditioning [\(Wu et al., 2026\)](#page-12-8). Empirical studies of whitening optimizers similarly ask which parts of whitening, momentum, and normalization account for their gains [\(Frans et al., 2025\)](#page-11-13). GO-MUON makes this orientation change coordinate-consistent: the preconditioned matrix enters the polar map and returns through the matching tangent map. The exact oracle is general; the OAS K-FAC-root field is the GO-MUON instantiation.

Table [1](#page-7-0) compares update construction and curvature reuse across representative structured matrix optimizers.

# 4.4 AMORTIZED AND STALE CURVATURE

Prior second-order methods separate the frequency of gradient updates from the frequency of curvature work. The original online K-FAC algorithm updates moving-average factors from minibatches while reusing a factorization for multiple iterations [\(Martens & Grosse, 2015\)](#page-11-1). Distributed K-FAC subsequently moved inverse computation and factor-statistic computation to asynchronous workers, explicitly accepting stale curvature in exchange for throughput [\(Ba et al., 2017\)](#page-10-6). Large-scale implementations made both timescales configurable: they reduce factor formation as well as eigendecomposition frequency [\(Osawa et al., 2019;](#page-11-8) [Pauloski et al., 2020\)](#page-11-9). KAISA applies this separation to Transformer linear layers, including BERT, with distinct factor-update and eigendecompositionupdate intervals [\(Pauloski et al., 2021\)](#page-12-9). These systems schedule factor updates and eigendecompositions independently, including gated activation and backward capture at Transformer scale.

The Shampoo lineage makes a related separation. Original Shampoo accumulates matrix moments more often than it computes inverse roots [\(Gupta et al., 2018\)](#page-11-11). Scalable Shampoo performs roots asynchronously and also exposes a separate interval for skipping gradient-statistic accumulation [\(Anil](#page-10-4) [et al., 2020\)](#page-10-4). Distributed Shampoo typically updates factors every step while refreshing inverse roots

<span id="page-8-0"></span>Table 2: Training-loss trajectories against Muon controls. Tiny Shakespeare uses three fresh paired seeds; PTB uses three hash-matched paired seeds. "Traj. GM" is the geometric mean of the three window means. Lower is better.

| Corpus                         | Method                                      | Matrix LR      | 201-300                   | 501-600                   | 901-1000                  | Traj. GM                  |
|--------------------------------|---------------------------------------------|----------------|---------------------------|---------------------------|---------------------------|---------------------------|
|                                | Muon+Q/K control<br>Go-MUON (lazy $K = 4$ ) | 0.018<br>0.080 | 1.70001<br><b>1.63052</b> | 1.50427<br><b>1.43613</b> | 1.34825<br><b>1.31465</b> | 1.51072<br><b>1.45471</b> |
| Penn Treebank<br>Penn Treebank | Muon Go-MUON (lazy $K = 4$ )                | 0.020<br>0.080 | 1.46773<br><b>1.45689</b> | <b>1.28084</b> 1.28167    | 1.17560<br><b>1.17000</b> | 1.30257<br><b>1.29757</b> |

periodically (Shi et al., 2023). SOAP treats eigenbasis frequency as an explicit systems parameter, while later analysis separates stale eigenvalues from stale eigenvectors and develops adaptive refresh criteria (Vyas et al., 2024; Eschenhagen et al., 2025). Together, these methods separate factor, matrix-function, and gradient-update timescales.

Go-MUON couples quarter-power matched geometry to a two-timescale sample-and-hold estimator. A reuse step skips factor decompositions, activation retention, output-gradient hooks, moment construction, and shrinkage. Equation (6) guarantees strictly positive alignment with the supplied momentum source for every cached SPD pair. The  $\beta_B^K$  coefficient tracks elapsed decay, while Proposition 6 shows that sparse observation raises stationary factor variance. The contribution is the measured compute–statistics tradeoff, not denoising from staleness.

## 5 EXPERIMENTS

#### 5.1 OPTIMIZATION AGAINST MUON CONTROLS

We train three-layer causal Transformers of width 128 with four attention heads, SwiGLU width 384, sequence length 128, and 2,048 tokens per update for 1,000 updates. We report mean pre-update training cross-entropy in three fixed 100-update windows and their geometric mean. The PTB comparison uses three hash-matched paired seeds. Here Muon is the standard update  $D = \operatorname{Polar}(M)$ , implemented with the same exact polar map and scalar schedule as Go-MUON, at learning rate 0.020. Ranking the recorded Go-MUON sweep by the three-window geometric mean selects learning rate 0.080. This three-window ranking was introduced after the original late-window rule, which selected 0.16, so we treat the hash-matched comparison as exploratory. The Tiny Shakespeare comparison uses three fresh paired seeds; its frozen campaign control is Muon with the campaign's Q/K partner metric, headwise Q/K treatment, and registered scalar schedule. No validation or test split is read.

On Tiny Shakespeare, Go-MUON is lower in all nine paired seed—window comparisons. Its reductions in the early, middle, and late windows are 4.09%, 4.53%, and 2.49%, respectively, giving a 3.71% reduction in the trajectory geometric mean. Peak learning rate 0.080 was selected by a broader sweep on tuning seed 17401, where it obtains window losses 1.62170, 1.43461, and 1.31396, with trajectory geometric mean 1.45132 versus 1.51073 for its paired campaign control—a 3.93% reduction. Table 2 evaluates that frozen selection on fresh seeds 17402–17404.

On PTB, the three-window-selected Go-MUON lowers the early and late windows by 0.74% and 0.48%. The middle window is effectively tied: Muon is lower by 0.00083. Go-MUON lowers the three-window trajectory geometric mean by 0.38% and wins that per-seed summary on all three matched pairs.

#### 5.2 Grokking speed on corrected modular addition

We next measure the onset of grokking rather than terminal loss. For modulus p, the dataset contains all  $p^2$  ordered pairs and uses a deterministic 50/50 split, with the training count rounded down, into disjoint train and test subsets. The model is a three-layer causal Transformer of width 64 with four attention heads, SwiGLU width 192, and RoPE. Its input is [a,b,CLS]: the p-row numerical embedding is tied to the p-class output head, while CLS is an independent learned vector and is not an output class. Thus the read-side control token is not also an unused output class.

<span id="page-9-0"></span>Table 3: Grokking onset on corrected independent-CLS modular addition, using one screening seed per modulus. "Grok" is the first of five consecutive evaluations with held-out accuracy at least 99%; evaluations occur every ten updates. "Delay" subtracts the first update with 99% training accuracy. Lower is better for Train, Grok, and Delay; Speedup is the Muon/GO-MUON ratio of Grok steps. The endpoint measures onset, while retention is separate.

| Task    | Method  | Matrix LR | Train 99% | Grok 99% | Delay | Speedup |
|---------|---------|-----------|-----------|----------|-------|---------|
| mod 103 | Muon    | 0.160     | 66        | 2320     | 2254  | 1.0×    |
| mod 103 | GO-MUON | 0.080     | 64        | 290      | 226   | 8.0×    |
| mod 107 | Muon    | 0.160     | 65        | 4520     | 4455  | 1.0×    |
| mod 107 | GO-MUON | 0.080     | 68        | 220      | 152   | 20.5×   |

<span id="page-9-1"></span>Table 4: PTB character-LM training loss over four paired seeds. "Wins" counts seeds where lazy K = 4 is lower than refresh 1.

| Update window | Refresh 1 | Lazy K = 4 | Lazy wins |  |  |  |
|---------------|-----------|------------|-----------|--|--|--|
| 201–300       | 1.45513   | 1.45549    | 2/4       |  |  |  |
| 501–600       | 1.28378   | 1.28259    | 2/4       |  |  |  |
| 901–1000      | 1.17238   | 1.16917    | 4/4       |  |  |  |
|               |           |            |           |  |  |  |

Training is full batch for 5,000 updates. Both optimizers use momentum 0.8, 50-step linear warmup followed by a constant learning rate, and identical AdamW updates for the tied numerical embedding, CLS, and norm parameters. GO-MUON uses K = 4 and β<sup>B</sup> = 0.97. A frozen screen over learning rates {0.08, 0.16} for GO-MUON and {0.16, 0.32} for Muon selects 0.080 and 0.160, respectively, under the grokking criterion below. The screen uses one deterministic split and initialization seed for each modulus.

We evaluate the held-out subset every ten updates and define the grokking step as the first of five consecutive evaluations with test accuracy at least 99%. Table [3](#page-9-0) also reports, as a memorization diagnostic, the first update with 99% training accuracy and the resulting grokking delay. Training-set fitting occurs at nearly the same update for the two optimizers; the separation appears in the transition to held-out accuracy.

On mod 103, GO-MUON groks at update 290 versus 2320 for Muon, using one eighth as many updates. On mod 107, the corresponding crossing is 220 versus 4520, or 1/20.5 as many updates. The mod-107 GO-MUON trajectory later leaves the 99% region, with below-threshold evaluations occurring as late as update 4470 before it returns at update 4480. This is a post-grok retention event and does not redefine the time-to-grok endpoint.

## 5.3 MATCHED MAP-BACK ON PENN TREEBANK

We first isolate matched map-back against the registered *halfspace* baseline. The baseline uses an inside-only inverse-half-power score and a spectral half-space safeguard; the matched arm uses Equation [\(4\)](#page-1-1) with α = 1/4 and the Frobenius graft. Both use the PTB training characters only, four paired seeds, peak matrix learning rate 0.08, momentum 0.8, and backward EMA 0.97.

In the preregistered updates 201–300 window, mean pre-update training loss is 1.48882 for halfspace and 1.45513 for matched map-back, a relative reduction of 2.26%. The matched arm is lower on all four paired seeds. The allocation was requeued before the final preregistered window; in every available common 50-step terminal window, matched map-back remains lower on all four seeds. We do not impute the missing 901–1000 endpoint.

## 5.4 LAZY REFRESH ON PENN TREEBANK

We next compare per-step quarter-power geometry with GO-MUON at K = 4 under a fresh, complete 1,000-update paired run. Initialization, minibatch stream, scalar controls, and schedule are identical within each seed. Table [4](#page-9-1) reports the preregistered mean pre-update training-loss windows; no validation or test split is read by this protocol.

The early window is operationally tied. Lazy refresh is lower by 0.00119 in the middle window and 0.00320 in the late window, winning all four late pairs. Its geometric-mean step-time ratio is 0.798×, a reduction of 20.2%. Both arms record zero negative momentum-source and current-gradient alignments. These results show that the noisier sparse factor estimator can coexist with a favorable training trajectory; they do not identify blockwise coherence as the cause.

# 6 CONCLUSION

The first-principles object in GO-MUON is an SPD-weighted spectral oracle:

$$C = P_B M P_A,$$
  $D_0 = P_B Q(C) P_A,$   $\langle M, D_0 \rangle = ||C||_*.$ 

This identity holds for every nonzero source and every supplied SPD pair, without Fisher or freshness assumptions. GO-MUON chooses P<sup>A</sup> = A−1/<sup>4</sup> and P<sup>B</sup> = B¯−1/<sup>4</sup> from OAS observed-label activation/backward factors; under predictive consistency, the backward factor approaches the softmax Fisher/GGN factor. The Frobenius graft retains the oracle ray while quarter powers limit worst-case sensitivity to factor conditioning.

Four-step refresh is a separate systems and statistical choice. It preserves elapsed decay and slowsignal lag, increases stationary factor variance, and removes factor capture and matrix functions from three of every four updates. On the frozen PTB training protocol, the three-window-selected GO-MUON improves the hash-matched trajectory summary over Muon, while the refresh trade reduces mean step time and improves the late training window. The corrected modular-addition screen shows a distinct empirical pattern on its screening seeds: training-set fitting time is nearly unchanged, while sustained-99% grokking onset is reached at updates 290 and 220, versus 2320 and 4520 for Muon. The resulting picture is explicit: matched map-back provides coordinate-consistent spectral optimization, factor estimation chooses the geometry, and lazy refresh amortizes its cost.

# REFERENCES

<span id="page-10-3"></span>Natalie Abreu, Nikhil Vyas, Sham Kakade, and Depen Morwani. The potential of second-order optimization for LLMs: A study with full gauss–newton. *arXiv preprint arXiv:2510.09378*, 2025. URL <https://arxiv.org/abs/2510.09378>.

<span id="page-10-4"></span>Rohan Anil, Vineet Gupta, Tomer Koren, Kevin Regan, and Yoram Singer. Scalable second order optimization for deep learning. *arXiv preprint arXiv:2002.09018*, 2020. URL [https://arxiv.](https://arxiv.org/abs/2002.09018) [org/abs/2002.09018](https://arxiv.org/abs/2002.09018).

<span id="page-10-6"></span>Jimmy Ba, Roger Grosse, and James Martens. Distributed second-order optimization using kroneckerfactored approximations. In *International Conference on Learning Representations*, 2017. URL <https://openreview.net/forum?id=SkkTMpjex>.

<span id="page-10-1"></span>Jeremy Bernstein and Laker Newhouse. Old optimizer, new norm: An anthology. *arXiv preprint arXiv:2409.20325*, 2024. URL <https://arxiv.org/abs/2409.20325>.

<span id="page-10-2"></span>Da Chang, Qiankun Shi, Lvgang Zhang, Yu Li, Ruijie Zhang, Yao Lu, Yongxiang Liu, and Ganzhao Yuan. MuonEq: Balancing before orthogonalization with lightweight equilibration. *arXiv preprint arXiv:2603.28254*, 2026. URL <https://arxiv.org/abs/2603.28254>.

<span id="page-10-0"></span>Yilun Chen, Ami Wiesel, Yonina C. Eldar, and Alfred O. Hero. Shrinkage algorithms for MMSE covariance estimation. *IEEE Transactions on Signal Processing*, 58(10):5016–5029, 2010. URL <https://arxiv.org/abs/0907.4698>.

<span id="page-10-5"></span>Zhehang Du and Weijie Su. The newton-muon optimizer. *arXiv preprint arXiv:2604.01472*, 2026. URL <https://arxiv.org/abs/2604.01472>.

<span id="page-10-7"></span>Runa Eschenhagen, Aaron Defazio, Tsung-Hsien Lee, Richard E. Turner, and Hao-Jun Michael Shi. Purifying shampoo: Investigating shampoo's heuristics by decomposing its preconditioner. In *Advances in Neural Information Processing Systems*, volume 38, 2025. URL [https://papers.nips.cc/paper\\_files/paper/2025/hash/](https://papers.nips.cc/paper_files/paper/2025/hash/f14f4eda29a74c02c803699a09529bb9-Abstract-Conference.html) [f14f4eda29a74c02c803699a09529bb9-Abstract-Conference.html](https://papers.nips.cc/paper_files/paper/2025/hash/f14f4eda29a74c02c803699a09529bb9-Abstract-Conference.html).

- <span id="page-11-13"></span>Kevin Frans, Pieter Abbeel, and Sergey Levine. What really matters in matrix-whitening optimizers? *arXiv preprint arXiv:2510.25000*, 2025. URL <https://arxiv.org/abs/2510.25000>.
- <span id="page-11-11"></span>Vineet Gupta, Tomer Koren, and Yoram Singer. Shampoo: Preconditioned stochastic tensor optimization. In *Proceedings of the 35th International Conference on Machine Learning*, pp. 1842–1850, 2018. URL <https://proceedings.mlr.press/v80/gupta18a.html>.
- <span id="page-11-0"></span>Keller Jordan, Yuchen Jin, Vlado Boza, Jiacheng You, Franz Cesista, Laker Newhouse, and Jeremy Bernstein. Muon: An optimizer for hidden layers in neural networks. Online write-up and software, 2024. URL <https://kellerjordan.github.io/posts/muon/>.
- <span id="page-11-5"></span>Diederik P. Kingma and Jimmy Ba. Adam: A method for stochastic optimization. In *International Conference on Learning Representations*, 2015. URL [https://arxiv.org/abs/1412.](https://arxiv.org/abs/1412.6980) [6980](https://arxiv.org/abs/1412.6980).
- <span id="page-11-2"></span>Frederik Kunstner, Lukas Balles, and Philipp Hennig. Limitations of the empirical fisher approximation for natural gradient descent. In *Advances in Neural Information Processing Systems*, volume 32, 2019. URL <https://arxiv.org/abs/1905.12558>.
- <span id="page-11-6"></span>Tim Large, Yang Liu, Minyoung Huh, Hyojin Bahng, Phillip Isola, and Jeremy Bernstein. Scalable optimization in the modular norm. In *Advances in Neural Information Processing Systems*, 2024. URL <https://arxiv.org/abs/2405.14813>.
- <span id="page-11-10"></span>Wu Lin, Felix Dangel, Runa Eschenhagen, Kirill Neklyudov, Agustinus Kristiadi, Richard E. Turner, and Alireza Makhzani. Structured inverse-free natural gradient descent: Memory-efficient & numerically-stable KFAC. In *Proceedings of the 41st International Conference on Machine Learning*, volume 235 of *Proceedings of Machine Learning Research*, pp. 29974–29991, 2024. URL <https://proceedings.mlr.press/v235/lin24f.html>.
- <span id="page-11-7"></span>Jingyuan Liu, Jianlin Su, Xingcheng Yao, Zhejun Jiang, Guokun Lai, Yulun Du, Yidao Qin, Weixin Xu, Enzhe Lu, Junjie Yan, et al. Muon is scalable for LLM training. *arXiv preprint arXiv:2502.16982*, 2025. URL <https://arxiv.org/abs/2502.16982>.
- <span id="page-11-12"></span>Ziyue Liu, Ruijie Zhang, Zhengyang Wang, Yequan Zhao, Yupeng Su, Zi Yang, and Zheng Zhang. Muon<sup>2</sup> : Boosting muon via adaptive second-moment preconditioning. *arXiv preprint arXiv:2604.09967*, 2026. URL <https://arxiv.org/abs/2604.09967>.
- <span id="page-11-4"></span>Kevin Luk and Roger Grosse. A coordinate-free construction of scalable natural gradient. In *Proceedings of the 35th International Conference on Machine Learning*, volume 80 of *Proceedings of Machine Learning Research*, pp. 2999–3008, 2018. URL [https://arxiv.org/abs/](https://arxiv.org/abs/1808.10340) [1808.10340](https://arxiv.org/abs/1808.10340).
- <span id="page-11-3"></span>James Martens. New insights and perspectives on the natural gradient method. *Journal of Machine Learning Research*, 21(146):1–76, 2020. URL <https://arxiv.org/abs/1412.1193>.
- <span id="page-11-1"></span>James Martens and Roger Grosse. Optimizing neural networks with kronecker-factored approximate curvature. In *Proceedings of the 32nd International Conference on Machine Learning*, pp. 2408– 2417, 2015. URL <https://arxiv.org/abs/1503.05671>.
- <span id="page-11-8"></span>Kazuki Osawa, Yohei Tsuji, Yuichiro Ueno, Akira Naruse, Rio Yokota, and Satoshi Matsuoka. Large-scale distributed second-order optimization using kronecker-factored approximate curvature for deep convolutional neural networks. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 12359–12367, 2019. URL [https://openaccess.](https://openaccess.thecvf.com/content_CVPR_2019/html/Osawa_Large-Scale_Distributed_Second-Order_Optimization_Using_Kronecker-Factored_Approximate_Curvature_for_Deep_CVPR_2019_paper.html) [thecvf.com/content\\_CVPR\\_2019/html/Osawa\\_Large-Scale\\_Distributed\\_](https://openaccess.thecvf.com/content_CVPR_2019/html/Osawa_Large-Scale_Distributed_Second-Order_Optimization_Using_Kronecker-Factored_Approximate_Curvature_for_Deep_CVPR_2019_paper.html) [Second-Order\\_Optimization\\_Using\\_Kronecker-Factored\\_Approximate\\_](https://openaccess.thecvf.com/content_CVPR_2019/html/Osawa_Large-Scale_Distributed_Second-Order_Optimization_Using_Kronecker-Factored_Approximate_Curvature_for_Deep_CVPR_2019_paper.html) [Curvature\\_for\\_Deep\\_CVPR\\_2019\\_paper.html](https://openaccess.thecvf.com/content_CVPR_2019/html/Osawa_Large-Scale_Distributed_Second-Order_Optimization_Using_Kronecker-Factored_Approximate_Curvature_for_Deep_CVPR_2019_paper.html).
- <span id="page-11-9"></span>J. Gregory Pauloski, Zhao Zhang, Lei Huang, Weijia Xu, and Ian T. Foster. Convolutional neural network training with distributed K-FAC. In *SC20: International Conference for High Performance Computing, Networking, Storage and Analysis*, pp. 1–12, 2020. doi: 10.1109/SC41405.2020.00098. URL <https://arxiv.org/abs/2007.00784>.

- <span id="page-12-9"></span>J. Gregory Pauloski, Qi Huang, Lei Huang, Shivaram Venkataraman, Kyle Chard, Ian Foster, and Zhao Zhang. KAISA: An adaptive second-order optimizer framework for deep neural networks. In *Proceedings of the International Conference for High Performance Computing, Networking, Storage and Analysis*. Association for Computing Machinery, 2021. doi: 10.1145/3458817. 3476152. URL <https://arxiv.org/abs/2107.01739>.
- <span id="page-12-2"></span>Thomas Pethick, Wanyun Xie, Kimon Antonakopoulos, Zhenyu Zhu, Antonio Silveti-Falls, and Volkan Cevher. Training deep learning models with norm-constrained LMOs. *arXiv preprint arXiv:2502.07529*, 2025. URL <https://arxiv.org/abs/2502.07529>.
- <span id="page-12-3"></span>Artem Riabinin, Egor Shulgin, Kaja Gruntkowska, and Peter Richt 'arik. Gluon: Making muon & scion great again! bridging theory and practice of LMO-based optimizers for LLMs. *arXiv preprint arXiv:2505.13416*, 2025. URL [https://arxiv.org/](https://arxiv.org/abs/2505.13416) [abs/2505.13416](https://arxiv.org/abs/2505.13416).
- <span id="page-12-10"></span>Hao-Jun Michael Shi, Tsung-Hsien Lee, Shintaro Iwasaki, Jose Gallego-Posada, Zhijing Li, Kaushik Rangadurai, Dheevatsa Mudigere, and Michael Rabbat. A distributed data-parallel PyTorch implementation of the distributed shampoo optimizer for training neural networks at-scale. *arXiv preprint arXiv:2309.06497*, 2023. URL <https://arxiv.org/abs/2309.06497>.
- <span id="page-12-0"></span>Andrey Veprikov, Arman Bolatov, Aleksandr Bogdanov, Samuel Horv 'ath, Aleksandr Beznosikov, Martin Tak 'a
  - v c, and Slavomir Hanzely. Preconditioned norms: A unified framework for steepest descent, quasi-newton and adaptive methods. *arXiv preprint arXiv:2510.10777*, 2025. URL [https:](https://arxiv.org/abs/2510.10777) [//arxiv.org/abs/2510.10777](https://arxiv.org/abs/2510.10777).
- <span id="page-12-5"></span>Nikhil Vyas, Depen Morwani, Rosie Zhao, Mujin Kwun, Itai Shapira, David Brandfonbrener, Lucas Janson, and Sham Kakade. SOAP: Improving and stabilizing shampoo using adam. *arXiv preprint arXiv:2409.11321*, 2024. URL <https://arxiv.org/abs/2409.11321>.
- <span id="page-12-8"></span>Tongle Wu, Huanyu Dong, Ying Sun, and Ziye Ma. MALT: Lightweight curvature-aware muon via diagonal preconditioning. *arXiv preprint arXiv:2608.05088*, 2026. URL [https://arxiv.](https://arxiv.org/abs/2608.05088) [org/abs/2608.05088](https://arxiv.org/abs/2608.05088).
- <span id="page-12-7"></span>Chenrui Xu, Wenjing Yan, and Ying-Jun Angela Zhang. FISMO: Fisher-structured momentumorthogonalized optimizer. *arXiv preprint arXiv:2601.21750*, 2026. URL [https://arxiv.](https://arxiv.org/abs/2601.21750) [org/abs/2601.21750](https://arxiv.org/abs/2601.21750).
- <span id="page-12-4"></span>Ruijie Zhang, Yequan Zhao, Ziyue Liu, Zhengyang Wang, and Zheng Zhang. Muon+: Towards better muon via one additional normalization step. *arXiv preprint arXiv:2602.21545*, 2026a. URL <https://arxiv.org/abs/2602.21545>.
- <span id="page-12-6"></span>Yechen Zhang, Shuhao Xing, Junhao Huang, Kai Lv, Yunhua Zhou, Xipeng Qiu, Qipeng Guo, and Kai Chen. Mousse: Rectifying the geometry of muon with curvature-aware preconditioning. *arXiv preprint arXiv:2603.09697*, 2026b. URL <https://arxiv.org/abs/2603.09697>.

# <span id="page-12-1"></span>A PROOFS AND ADDITIONAL GUARANTEES

## A.1 PROOF OF PROPOSITION [5](#page-3-2)

Write P<sup>B</sup> = B<sup>−</sup><sup>α</sup>, P<sup>A</sup> = A<sup>−</sup><sup>α</sup>, and let Q be the compact full-SVD support polar, so ∥Q∥<sup>F</sup> = √ k. Nuclear-norm multiplication inequalities give

$$||P_B M P_A||_* \ge \sigma_{\min}(P_B)\sigma_{\min}(P_A)||M||_*,$$

while

$$||P_B Q P_A||_F \le \sqrt{k} ||P_B||_{\text{op}} ||P_A||_{\text{op}}.$$

Substitution into

$$\left\langle M, \widehat{D}_{\alpha} \right\rangle = \frac{\sqrt{k} \|P_B M P_A\|_*}{\|P_B Q P_A\|_F}$$

gives

$$\langle M, \widehat{D}_{\alpha} \rangle \ge \frac{\sigma_{\min}(P_B)\sigma_{\min}(P_A)}{\sigma_{\max}(P_B)\sigma_{\max}(P_A)} \|M\|_* = K_{AB}^{-\alpha} \|M\|_*.$$

The nonzero singular values of a semi-orthogonal Q are all one. Singular-value product inequalities therefore give

$$\sigma_{\max}(P_B Q P_A) \le \sigma_{\max}(P_B) \sigma_{\max}(P_A),$$
  
 $\sigma_k(P_B Q P_A) \ge \sigma_{\min}(P_B) \sigma_{\min}(P_A).$ 

Their ratio is at most  $K_{AB}^{\alpha}$ . The positive graft does not change this ratio.

For completeness, Equation (19) follows by writing  $\mu = \operatorname{tr}(S)/d$ . Since  $S \succeq 0$ ,

$$\lambda_{\min}(\mathrm{OAS}(S)) \ge \lambda \mu, \qquad \lambda_{\max}(\mathrm{OAS}(S)) \le [d - (d - 1)\lambda]\mu.$$

## A.2 A SCALE-FREE CACHED-ORACLE BOUND

<span id="page-13-0"></span>**Proposition 7** (Cached oracle under coordinate drift). Let  $q_P$  be the current weighted norm from Equation (2), and let  $\widetilde{D}$  be any positive rescaling of an exact unit-radius oracle for cached maps  $\widetilde{P}_B$ ,  $\widetilde{P}_A$ . Define  $\Theta$  by Equation (7). Then

$$\left| \frac{\left\langle M, \widetilde{D} \right\rangle}{q_P(\widetilde{D}) \|P_B M P_A\|_*} \ge \Theta^{-1}. \right| \tag{36}$$

Thus, after rescaling to its actual radius in the current ball, the cached direction achieves at least a  $\Theta^{-1}$  fraction of the current optimum. The ratio is unchanged by the Frobenius graft.

*Proof.* Let

$$\widetilde{q}(D) = \|\widetilde{P}_B^{-1}D\widetilde{P}_A^{-1}\|_{\mathrm{op}}, \quad L = P_B^{-1}\widetilde{P}_B, \quad R = \widetilde{P}_A P_A^{-1}.$$

For  $U = \widetilde{P}_B^{-1} D \widetilde{P}_A^{-1}$ ,  $q_P(D) = ||LUR||_{\text{op}}$ , and hence

$$a \, \widetilde{q}(D) \le q_P(D) \le b \, \widetilde{q}(D),$$

where

$$a = \sigma_{\min}(L)\sigma_{\min}(R), \qquad b = \sigma_{\max}(L)\sigma_{\max}(R).$$

The corresponding unit-ball inclusions imply that the cached support value  $\widetilde{h}(M) = \|\widetilde{P}_B M \widetilde{P}_A\|_*$  satisfies  $\widetilde{h}(M) \geq a \|P_B M P_A\|_*$ . An exact cached unit oracle has pairing  $\widetilde{h}(M)$  and current radius at most b. Its normalized efficiency is therefore at least a/b. Since  $\kappa_2(R) = \kappa_2(P_A^{-1}\widetilde{P}_A)$ ,  $a/b = \Theta^{-1}$ . Positive rescaling cancels from the ratio.

The bound uses the singular condition numbers of the actual coordinate changes. A simpler factorlevel power law requires additional commutativity or functional-calculus assumptions and is not used here.

#### A.3 PROOF OF PROPOSITION 6

Let  $F_X(d\omega)$  be the matrix-valued spectral measure of the centered vector process  $\text{vec}(X_t)$ . At refresh boundaries, the sparse and per-step transfer functions with respect to the original time index are

$$G_K(\omega) = \frac{1 - \beta_B^K}{1 - \beta_B^K e^{-iK\omega}}, \qquad H_1(\omega) = \frac{1 - \beta_B}{1 - \beta_B e^{-i\omega}}.$$

Factorizing  $1 - (\beta_B e^{-i\omega})^K$  gives

$$\frac{|G_K(\omega)|}{|H_1(\omega)|} = \frac{\sum_{r=0}^{K-1} \beta_B^r}{\left|\sum_{r=0}^{K-1} \beta_B^r e^{-ir\omega}\right|} \ge 1.$$

Therefore

$$\operatorname{Cov}(\operatorname{vec} Y_j) - \operatorname{Cov}(\operatorname{vec} Z_{jK}) = \int_{-\pi}^{\pi} (|G_K|^2 - |H_1|^2) F_X(d\omega) \succeq 0.$$

For IID observations, the standard AR(1) variance formula immediately yields Equation [\(25\)](#page-5-1). For an affine signal x<sup>t</sup> = a + vt, the steady refresh-boundary estimate is

$$Y_j = x_{jK} - v \frac{K\beta_B^K}{1 - \beta_B^K}.$$

Holding this value through phase s ∈ {0, . . . , K − 1} adds s steps of delay. Averaging over phases gives Equation [\(26\)](#page-5-2).