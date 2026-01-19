rodrigo.martinez@dipc.org

# Feedback-driven recurrent quantum neural network universality

Lukas Gonon<sup>1</sup>,<sup>2</sup> , Rodrigo Mart´ınez-Pe˜na<sup>3</sup> , and Juan-Pablo Ortega<sup>4</sup>

#### Abstract

Quantum reservoir computing uses the dynamics of quantum systems to process temporal data, making it particularly well-suited for learning with noisy intermediatescale quantum devices. Early experimental proposals, such as the restarting and rewinding protocols, relied on repeating previous steps of the quantum map to avoid backaction. However, this approach compromises real-time processing and increases computational overhead. Recent developments have introduced alternative protocols that address these limitations. These include online, mid-circuit measurement, and feedback techniques, which enable real-time computation while preserving the input history. Among these, the feedback protocol stands out for its ability to process temporal information with comparatively fewer components. Despite this potential advantage, the theoretical foundations of feedback-based quantum reservoir computing remain underdeveloped, particularly with regard to the universality and the approximation capabilities of this approach. This paper addresses this issue by presenting a recurrent quantum neural network architecture that extends a class of existing feedforward models to a dynamic, feedback-driven reservoir setting. We provide theoretical guarantees for variational recurrent quantum neural networks, including approximation bounds and universality results. Notably, our analysis demonstrates that the model is universal with linear readouts, making it both powerful and experimentally accessible. These results pave the way for practical and theoretically grounded quantum reservoir computing with real-time processing capabilities.

Key Words: Recurrent Quantum Neural Network, Quantum Reservoir Computing, universality, approximation bounds, Barron system, state-space system

<sup>1</sup>Universit¨at Sankt Gallen. School of Computer Science. Sankt Gallen. Switzerland. lukas.gonon@unisg.ch

<sup>2</sup> Imperial College. Department of Mathematics. London. United Kingdom. l.gonon@imperial.ac.uk <sup>3</sup>Donostia International Physics Center, Paseo Manuel de Lardizabal 4, E-20018 San Sebasti´an, Spain.

<sup>4</sup>Nanyang Technological University. Division of Mathematical Sciences. School of Physical and Mathematical Sciences. Singapore. Juan-Pablo.Ortega@ntu.edu.sg

### Contents

| 1 | Introduction                                                        | 2  |
|---|---------------------------------------------------------------------|----|
| 2 | Recurrent quantum neural network universality                       | 5  |
|   | 2.1<br>The recurrent quantum neural network (RQNN) construction<br> | 6  |
|   | 2.2<br>RQNN approximation of state-space maps and their derivatives | 9  |
|   | 2.3<br>Recurrent QNN approximation bounds for state-space filters   | 18 |
|   | 2.4<br>Universality                                                 | 20 |
| 3 | Conclusions                                                         | 24 |
|   | Acknowledgments                                                     | 25 |
|   | Bibliography                                                        | 25 |

### <span id="page-1-0"></span>1 Introduction

Quantum reservoir computing (QRC) is a promising approach for exploiting noisy intermediatescale quantum (NISQ) technologies for time series prediction and learning. These include ion traps, nuclear magnetic resonance, cold atoms, photonic platforms, and superconducting qubits [\[MMPN](#page-28-0)+21]. When implementing QRC models experimentally, it is necessary to consider the backaction and statistical effects introduced by quantum measurements. Backaction refers to the modification of a quantum state after monitoring, also known as wavefunction collapse. Due to the probabilistic nature of quantum theory, measurements must be repeated to compute the expected values of observables, which introduces a statistical component in all these methodologies. Most available experimental implementations rely on the quantum computer paradigm [\[DHB22,](#page-26-0) [MCLCL23,](#page-27-0) [SGP](#page-29-0)+22, [YSK](#page-30-0)+23, [CNY20,](#page-26-1) [KSK](#page-27-1)+23, [MDP23,](#page-27-2) [PHS22,](#page-29-1) [ATM25,](#page-25-0) [HKB](#page-27-3)+24]. However, there is an increasing interest in extending this technique to new settings, such as optical pulses [\[GBGSZ23,](#page-26-2) [PHGB](#page-28-1)+25], Rydberg atoms [\[BNGY22,](#page-25-1) [KHZ](#page-27-4)+24], and quantum memristors [\[SMP](#page-29-2)+22, [SAS](#page-29-3)+25].

Early QRC model implementations relied on the simplest possible approach, namely, the restarting protocol [\[DHB22,](#page-26-0) [SGP](#page-29-0)+22, [KSK](#page-27-1)+23, [CNY20,](#page-26-1) [MDP23\]](#page-27-2). In this approach, the expected values of observables are obtained by rerunning the algorithm from the first time step at each subsequent time step. This avoids the backaction effect of quantum measurements. However, the complexity of this protocol scales quadratically with the length of the input sequence, making it very time-consuming. A faster alternative is the rewinding protocol [\[MMPN](#page-28-0)+21, [CDLJ24\]](#page-26-3), where the fading memory of the quantum reservoir is exploited ˇ to restart the algorithm with a fixed window of past time steps. This reduces the complexity of the algorithm to linear in terms of input length. Originally proposed in [\[CNY20\]](#page-26-1), this protocol has thus far only been considered numerically [\[MMPG](#page-28-2)+23, [CDLJ24\]](#page-26-3). Both the ˇ restarting and rewinding protocols use repetition of previous time steps to reproduce the dynamics of the theoretical model and avoid the disruptive effect of projective measurements used to extract output information. This comes at the cost of halting the quantum dynamics at each time step and the need to buffer the input sequence. Consequently, these approaches lack one of the most important features of traditional reservoir computing, namely, the ability to process information in real time.

New protocols have been proposed to circumvent this problem. The online protocol [\[MMPG](#page-28-2)+23, [FPL](#page-26-4)+24] uses weak measurements to find a balance between erasing and extracting information. Mid-circuit measurements and reset operations [\[HKB](#page-27-3)+24] can split the reservoir into two parts: memory and readout. The memory retains previous inputs, while measurements only affect the readout part. The feedback protocol [\[KFY24\]](#page-27-5), which can be traced back to hybrid QRC techniques [\[PHS22,](#page-29-1) [PHS23\]](#page-29-4), reinjects the measured observables at each time step as parameters of an input quantum channel. This ensures that no backaction effects are present and that past input information is preserved. Note that in order to compute the observables in real time, these protocols all require several copies of the system to be run in parallel. Furthermore, these protocols can be combined with each other. For instance, the feedback protocol has been combined with both the online protocol [\[MSH25\]](#page-28-3) and with mid-circuit measurements and reset operations [\[MKTG25\]](#page-28-4).

Of all these approaches, the feedback protocol presents some particularly interesting features. First, the feedback protocol enables us to compute the expected values of observables from a single copy of the system by repeating one time step only. If only a few copies of the system are available, this reduces the experimental time overhead for real-time applications compared to other approaches. Second, in contrast to previous QRC models, where an erasure mechanism is added to provide fundamental properties such as the echo state property, simple unitary operations can provide these properties [\[KFY24\]](#page-27-5). Finally, the dynamical equations of quantum reservoirs under the feedback protocol go beyond the usual SAS paradigm of QRC models [\[MPO23\]](#page-28-5). These properties make the feedback protocol a promising candidate for exploring QRC applications.

Despite all these interesting features of QRC models based on the feedback protocol, basic theoretical results such as approximation bounds, universality proofs, and criteria for these architectures to satisfy the echo state or the fading memory properties do not exist yet. Moreover, previous universality results concerning QRC models have relied on the use of polynomial output layers [\[CN19,](#page-26-5) [CNY20,](#page-26-1) [NMPG](#page-28-6)+21, [SMPS](#page-29-5)+24, [SGLZ24\]](#page-29-6), which yield a polynomial algebra that can then be used with the Stone-Weierstrass theorem to obtain universality statements. Nevertheless, most numerical and experimental implementations of reservoir computers use linear output layers due to their simplicity and fast training.

In this paper, we address these theoretical shortcomings by proposing and analyzing a recurrent quantum neural network (RQNN) architecture that builds on and extends the feedforward quantum neural networks (QNN) introduced in [\[GJ25\]](#page-26-6) to a dynamic quantum reservoir computing setting. In the context of the feedback protocol, we derive approximation error bounds and prove universality statements for RQNN families with a linear output layer. Universality refers to the ability of these families to uniformly approximate arbitrarily well a large category of dynamic processes, namely fading memory input / output systems (defined later on). It is important to note that, strictly speaking, these findings apply exclusively to variational quantum circuits for which all parameters are trained and are only tentative for quantum reservoir systems in which some parameters in the recurrent layer are randomly generated. More explicitly, in the variational method, the parameters of the quantum circuit are tuned alongside the final readout layer unlike the reservoir method which usually involves randomly assigning circuit parameters and optimising only the output layer, making it a simpler technique. Most previous literature on RC and QRC universality [GO18b, GO18a, GO20, GO21, CN19, CNY20, NMPG<sup>+</sup>21, SMPS<sup>+</sup>24, SGLZ24] implicitly assumes the search for an optimal model within a class in which all parameters are estimated. This is different from the approach taken in, for example, [GGO23], where it is explicitly assumed that the circuit parameters are randomly sampled. Finally, the error bounds and the universality results presented in this paper deal with the approximation properties of RQNNs but do not explore their behavior in relation to estimation errors. That will be the subject of a future work. The reader interested in this question is encouraged to check with [GGO20, CAM25].

The structure of the paper is as follows. Section 2.1 describes the RQNN model, which is an extension of the static QNN introduced in [GJ25] with state feedback. Section 2.2 generalizes the approximation bounds obtained in [GJ25] to accommodate first derivatives and uses these results (see Proposition 2.5 and Corollary 2.6) to study the properties of the RQNN state maps in the uniform approximation of more general state equations as well as in a square-integrable sense. These results are then used in Section 2.3 to prove the universal uniform approximation properties of the filters associated with RQNN systems. More specifically, in Proposition 2.7 we provide filter approximation bounds that show that RQNNs are able to uniformly approximate the filters induced by any contracting Barrontype state-space system. Finally, Theorem 2.9 of Section 2.4 extends this universality property to the much larger category of arbitrary fading memory, causal, and time-invariant filters. These results show that RQNNs have approximation properties as competitive as those of popular reservoir computing/state-space system families like echo state networks [GO18a, GO20, GO21, GGO23], state-affine systems [GO18b, GO20], or linear systems with polynomial / neural network readouts [GO18b]. The paper concludes with Section 3, where the main contributions and outlook of the paper are summarized.

Reservoir computing definitions. Let the symbol  $(\mathbb{R}^n)^{\mathbb{Z}}$  denote the set of infinite real sequences of the form  $\underline{z} = (\dots, z_{-1}, z_0, z_1, \dots), z_i \in \mathbb{R}^n, i \in \mathbb{Z}; (\mathbb{R}^n)^{\mathbb{Z}_-}$  is the subspace consisting of left infinite sequences:  $(\mathbb{R}^n)^{\mathbb{Z}_-} = \{\underline{z} = (\dots, z_{-2}, z_{-1}, z_0) \mid z_i \in \mathbb{R}^n, i \in \mathbb{Z}_-\}$ . Analogously,  $(D_n)^{\mathbb{Z}}$  and  $(D_n)^{\mathbb{Z}_-}$  stand for infinite and semi-infinite sequences, with elements in the subset  $D_n \subset \mathbb{R}^n$ . Let  $D_n \subset \mathbb{R}^n$  and  $B_N \subset \mathbb{R}^N$ . We refer to the maps of the type  $U: (D_n)^{\mathbb{Z}} \longrightarrow (B_N)^{\mathbb{Z}}$  as **filters** and to those like  $H: (D_n)^{\mathbb{Z}} \longrightarrow B_N$  (or  $H: (D_n)^{\mathbb{Z}_-} \longrightarrow B_N$ ) as **functionals**. A filter  $U: (D_n)^{\mathbb{Z}} \longrightarrow (B_N)^{\mathbb{Z}}$  is called **causal** 

when for any two elements  $z, w \in (D_n)^{\mathbb{Z}}$  that satisfy that  $z_{\tau} = w_{\tau}$  for any  $\tau \leq t$ , for a given  $t \in \mathbb{Z}$ , we have that  $U(z)_t = U(w)_t$ . Let  $T_{\tau} : (D_n)^{\mathbb{Z}} \longrightarrow (D_n)^{\mathbb{Z}}$ ,  $\tau \in \mathbb{Z}$  be the **time delay** operator defined by  $T_{\tau}(z)_t := z_{t-\tau}$ . The filter U is called **time-invariant** when it commutes with the time delay operator, that is,  $T_{\tau} \circ U = U \circ T_{\tau}$ , for any  $\tau \in \mathbb{Z}$ , where the two operators  $T_{\tau}$  are defined in the appropriate sequence spaces. Finally, we recall there is a bijection between causal time-invariant filters and functionals on  $(D_n)^{\mathbb{Z}_-}$ , and we can use them interchangeably [GO18a].

Consider a recurrent neural network determined by two maps, namely the **recurrent** layer or the **state map**  $F: \mathbb{R}^N \times \mathbb{R}^n \longrightarrow \mathbb{R}^N$ ,  $n, N \in \mathbb{N}$ , and a **readout** or **observation** map  $h: \mathbb{R}^N \to \mathbb{R}^m$ ,  $m \in \mathbb{N}$ , given by

$$\mathbf{x}_t = F(\mathbf{x}_{t-1}, \mathbf{z}_t), \mathbf{y}_t = h(\mathbf{x}_t),$$
 (1)

<span id="page-4-1"></span>where  $t \in \mathbb{Z}$ ,  $z_t$  denotes the input,  $x_t \in \mathbb{R}^N$  is the state vector, and  $\mathbf{y}_t \in \mathbb{R}^m$  is the output vector. If F is a fixed map that has no parameters that are estimated during the training process, the recurrent layer is referred to as a **reservoir** and the recurrent neural network system (1) as a **reservoir computing** system.

Consider now subsets  $B_N \subset \mathbb{R}^N$  and  $D_n \subset \mathbb{R}^n$  and a recurrent layer defined on them, that is,  $F: B_N \times D_n \longrightarrow B_N$  and  $h: B_N \to \mathbb{R}^m$ . Denote by  $D_m := h(B_N) \subset \mathbb{R}^m$ . The recurrent system F is said to have the **echo state property** with respect to inputs in  $(D_n)^{\mathbb{Z}}$  when for any  $\underline{z} \in (D_n)^{\mathbb{Z}}$  there exists a unique element  $\underline{x} \in (B_N)^{\mathbb{Z}}$  that satisfies the first equation in (1), for each  $t \in \mathbb{Z}$ . When the echo state property holds, a unique filter  $U^F:(D_n)^{\mathbb{Z}} \longrightarrow (B_N)^{\mathbb{Z}}$  can be associated to the recurrent system determined by F, namely,  $U^F(z)_t := x_t \in B_N$ , for all  $t \in \mathbb{Z}$ . We will denote by  $U_h^F:(D_n)^{\mathbb{Z}} \longrightarrow (D_m)^{\mathbb{Z}}$  the corresponding filter determined by the entire recurrent system, that is,  $U_h^F(z)_t = h\left(U^F(z)_t\right) := y_t \in D_m$ , for all  $t \in \mathbb{Z}$ . The filters  $U^F$  and  $U_h^F$  are causal and time-invariant by construction. The echo state property is much related with the so-called **fading memory property** defined as the continuity of  $U_h^F$  with respect to weighted norms in its domain and codomain [BC85] or the product topologies when  $D_n$  and  $D_m$  are compact [GO18a]. It can be shown that when  $D_m$  is compact, the echo state property implies the fading memory property [Man20, OR25b]; see [OR25a] for a comprehensive account of the dynamical implications of the fading memory property.

# <span id="page-4-0"></span>2 Recurrent quantum neural network universality

This section contains approximation guarantees and universality results for the recurrent quantum neural network (RQNN) family. To achieve this, we will first introduce in detail in Section 2.1 the recurrent quantum neural networks employed. Then, in Section 2.2 we prove refined approximation error bounds (that generalize those in [GJ25]) for feed-forward quantum neural networks (QNNs) that allow us to control the error committed

when approximating a function and its derivatives simultaneously. These error bounds show how recurrent QNNs can be used to approximate state-space maps arbitrarily well as long as these are sufficiently smooth and satisfy Barron-type conditions; RQNN state maps are hence universal in that category. These bounds are devised with respect to  $L^{\infty}$  and  $L^2$ -type norms. As we shall prove, in the  $L^{\infty}$  case, the universality of the RQNN family still holds with respect to state maps that do not necessarily satisfy the Barron condition, even though in that framework we do not formulate approximation bounds. Finally, in the last two sections, we exploit all these results on the approximation of state maps to obtain universality statements and error bounds for the approximation of arbitrary causal, time-invariant, and fading memory filters using a modified recurrent QNN. In addition to the tools developed here, our proofs of these results rely on techniques from [GO20, GO21] and the overall strategy is reminiscent of the so-called internal approximation approach introduced in [GO18a, Theorem 3.1 (iii)] for echo state networks, which consists of obtaining approximation results for filters out of statements of that type for the state maps that generate them.

### <span id="page-5-0"></span>2.1 The recurrent quantum neural network (RQNN) construction

Our recurrent quantum circuit is constructed based on two parametric quantum gates U and V, which we now introduce. The construction builds on the feedforward quantum neural network architecture introduced in [GJ25].

Construction of U. For  $\delta, \gamma \in [0, 2\pi]$  and  $\alpha \in \mathbb{R}$ , denote by  $R_x(\delta)$ ,  $R_y(\gamma)$ , and  $R_z(\alpha)$  the rotations around the X-, Y-and the Z-axis, corresponding to angles  $\delta$ ,  $\gamma$  and  $\alpha$ , respectively, and obtained as the exponentials of the Pauli matrices:

$$\mathtt{R}_{\mathtt{x}}(\delta) := \begin{pmatrix} \cos\left(\frac{\delta}{2}\right) & -\mathrm{i}\sin\left(\frac{\delta}{2}\right) \\ -\mathrm{i}\sin\left(\frac{\delta}{2}\right) & \cos\left(\frac{\delta}{2}\right) \end{pmatrix}, \, \mathtt{R}_{\mathtt{y}}(\gamma) := \begin{pmatrix} \cos\left(\frac{\gamma}{2}\right) & -\sin\left(\frac{\gamma}{2}\right) \\ \sin\left(\frac{\gamma}{2}\right) & \cos\left(\frac{\gamma}{2}\right) \end{pmatrix}, \, \mathtt{R}_{\mathtt{z}}(\alpha) := \begin{pmatrix} e^{-\mathrm{i}\frac{\alpha}{2}} & 0 \\ 0 & e^{\mathrm{i}\frac{\alpha}{2}} \end{pmatrix}.$$

For a given accuracy parameter  $n \in \mathbb{N}$ , consider weights  $\boldsymbol{a} = (\boldsymbol{a}^1, \dots, \boldsymbol{a}^n) \in (\mathbb{R}^{d+N})^n$ ,  $\boldsymbol{b} = (b^1, \dots, b^n) \in \mathbb{R}^n$  and  $\boldsymbol{\gamma} = (\gamma^1, \dots, \gamma^n) \in [0, 2\pi]^n$ . For  $i = 1, \dots, n$ , we define parametric gate maps  $\mathbf{U}_1^{(i)} \colon \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{C}^{2\times 2}$  that map a current system state  $\boldsymbol{x}$  and a current observation  $\boldsymbol{z}$  to a rotation gate. Gate map i depends on parameters  $\boldsymbol{a}^i, b^i$  and is defined by

$$\mathtt{U}_{1}^{(i)}(\boldsymbol{x},\boldsymbol{z}) \quad := \mathtt{H}\,\mathtt{R}_{\mathtt{z}}\left(-b^{i}\right)\mathtt{R}_{\mathtt{z}}\left(-a_{N+d}^{i}z_{d}\right)\cdots\mathtt{R}_{\mathtt{z}}\left(-a_{N+1}^{i}z_{1}\right)\mathtt{R}_{\mathtt{z}}\left(-a_{N}^{i}x_{N}\right)\cdots\mathtt{R}_{\mathtt{z}}\left(-a_{1}^{i}x_{1}\right)\mathtt{H} = \mathtt{R}_{\mathtt{x}}\left(\delta^{i}\right)$$

for any  $\boldsymbol{x}=(x_1,\ldots,x_N)\in\mathbb{R}^N$  and  $\boldsymbol{z}=(z_1,\ldots,z_d)\in\mathbb{R}^d$ , where H is the Hadamard gate and

$$\delta^{i} := -b^{i} - a_{N+d}^{i} z_{d} \cdots - a_{N+1}^{i} z_{1} - a_{N}^{i} x_{N} \cdots - a_{1}^{i} x_{1}.$$

Moreover, we also define the gates  $\mathtt{U}_2^{(i)} := \mathtt{R}_{\mathtt{y}}\left(\gamma^i\right)$  and denote the circuit parameters by  $\boldsymbol{\theta} = (\boldsymbol{a}^i, b^i, \gamma^i)_{i=1,\dots,n} \in \boldsymbol{\Theta} := (\mathbb{R}^{d+N} \times \mathbb{R} \times [0, 2\pi])^n$ .

With these notations, we are now ready to define the key element of our parametric quantum circuit, the gate  $U := U_{\theta}(x, z)$ . U is defined as a block matrix built from the gates  $\bar{U}^{(i)}(x, z) = U_1^{(i)}(x, z) \otimes U_2^{(i)}$  as follows:

$$\mathtt{U}_{m{ heta}}(m{x},m{z}) := egin{bmatrix} ar{\mathtt{U}}^{(1)}(m{x},m{z}) & \mathbf{0}_{4 imes4} & \mathbf{0}_{4 imes4} & \cdots & \mathbf{0}_{4 imes4} & \mathbf{0}_{4 imes n_0} \ \mathbf{0}_{4 imes4} & ar{\mathtt{U}}^{(2)}(m{x},m{z}) & \mathbf{0}_{4 imes4} & \cdots & \mathbf{0}_{4 imes4} & dots \ dots & \ddots & & dots & dots \ \mathbf{0}_{4 imes4} & \cdots & \mathbf{0}_{4 imes4} & ar{\mathtt{U}}^{(n-1)}(m{x},m{z}) & \mathbf{0}_{4 imes4} & dots \ \mathbf{0}_{4 imes4} & \cdots & \cdots & \mathbf{0}_{4 imes4} & ar{\mathtt{U}}^{(n)}(m{x},m{z}) & \mathbf{0}_{4 imes n_0} \ \mathbf{0}_{n_0 imes4} & \cdots & \cdots & \mathbf{0}_{n_0 imes4} & \mathbf{1}_{n_0 imes n_0} \end{bmatrix}.$$

Here,  $n_0$  is chosen as the smallest natural number such that the matrix dimension  $n_{\mathbb{U}} = 4n + n_0$  is a power of 2, that is,  $n_{\mathbb{U}} = 2^{\mathfrak{n}}$ . It can be easily shown that  $n_0 = 4\kappa$  with  $\kappa \in \mathbb{N}$ , since  $4n + n_0$  and  $2n + n_0/2$  must be even for  $\mathfrak{n} \geq 2$ . Then,  $\mathbb{U} \in \mathbb{C}^{n_{\mathbb{U}} \times n_{\mathbb{U}}}$  is a unitary quantum gate operating on  $\mathfrak{n} = \log_2(n_{\mathbb{U}}) = 2 + \log_2(n + \kappa)$  qubits with a diagonal-block structure:

$$\mathtt{U}_{m{ heta}}(m{x},m{z}) = \sum_{i=0}^{n-1} \ket{i}ra{i}\otimes ar{\mathtt{U}}^{(j+1)}(m{x},m{z}) + \sum_{i=n}^{n+\kappa-1} \ket{i}ra{i}\otimes \mathbf{1}_{4 imes4}.$$

These unitary operators with a block structure are known as uniformly controlled quantum gates. They are present in many quantum algorithms and are used to decompose general unitary gates and locally prepare arbitrary quantum states [MVBS04a, MVBS04b, BVMS05, ADMQ+22, PPR19]. They are defined as multi-controlled unitaries where each unitary block targets a set of qubits, two qubits in this case, while the other  $\log_2(n+\kappa)$  qubits act as control qubits. Notice that the block structure of the unitary  $\mathbb{U}_{\theta}$  arises from indexing the targets as the lowest-order bits. Recently, efficient decompositions of multi-controlled unitaries have been proposed in terms of the number of single-qubit and two-qubit gates [ZB24, ZB25], as well as for approximations of the multi-controlled gate [SAAdS24]. Code implementations of these quantum gates can be found in the *Qclib* library [AAdS+23]. Finally, the identity blocks  $\mathbf{1}_{4\times4}$  do not introduce additional gates into the quantum circuit, so the effective circuit can be reduced to the application of the  $\bar{\mathbb{U}}^{(i)}$  gates. However, the number of control qubits is fixed by  $\log_2(n+\kappa)$  and we need all of them to compute the output probabilities, as we will see below.

**Construction of V.** Next, let  $V \in \mathbb{C}^{n_{\mathbb{V}} \times n_{\mathbb{V}}}$  be any unitary matrix mapping  $|0\rangle^{\otimes n}$  to the state  $|\psi\rangle = \frac{1}{\sqrt{n}} \sum_{i=0}^{n-1} |4i\rangle$  which for  $n \geq 2$  is explicitly given by  $|\psi\rangle = \frac{1}{\sqrt{n}} \sum_{i=0}^{n-1} |i\rangle \otimes |00\rangle$ . We refer to [GJ25] for a more detailed discussion on the choice of V. Notice that when  $n_0 = 0$ , there is an explicit construction of V in terms of Hadamard gates acting on the control qubits, see Appendix A in [GJ25].

Measuring circuit outputs. We can now measure the state of the n-qubit system after applying the gates V and U. The possible states that we could measure are given by  $0, \ldots, n_{\mathbb{U}} - 1$  (in binary). By running the circuit repeatedly, we can now obtain (up to well-controlled Monte Carlo error, see [GJ25]) the probabilities  $\mathbb{P}_m^n$  that the measured state is in  $\{m, 4+m, \ldots, 4(n-1)+m\}$ , for  $m \in \{0,1,2,3\}$ , where m is the binary state of the last two qubits (the target qubits).

More formally, consider the unitary gate map  $C(x, z) = C_{n,\theta}(x, z) := U_{\theta}(x, z)V$  acting on  $n = 2 + \log_2(n + \kappa)$  qubits. This circuit acts on the initial state  $|0\rangle^{\otimes n}$  via the quantum gates V and U as

$$\mathtt{C}_{\mathfrak{n},oldsymbol{ heta}}(oldsymbol{x},oldsymbol{z})\ket{0}^{\otimes \mathfrak{n}} = \sum_{i=0}^{n-1}\ket{i}\otimes \mathtt{U}_1^{(i+1)}(oldsymbol{x},oldsymbol{z})\ket{0}\otimes \mathtt{U}_2^{(i+1)}\ket{0}.$$

Then, we measure

<span id="page-7-0"></span>
$$\mathbb{P}_{m}^{n,\boldsymbol{\theta}} = \mathbb{P}_{m}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) := \mathbb{P}\left(\text{``C}_{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) | 0 \right)^{\otimes n} \in \{m,4+m,\ldots,4(n-1)+m\}\text{''}\right). \tag{2}$$

This is the sum of the probabilities of being in the states  $|i\rangle \otimes |m\rangle$ , where  $i=0,\ldots,n-1$ . That is,

$$\mathbb{P}_{m}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) = \sum_{i=1}^{n} \left| \langle m | \left( \mathbb{U}_{1}^{(i)}(\boldsymbol{x},\boldsymbol{z}) | 0 \rangle \otimes \mathbb{U}_{2}^{(i)} | 0 \rangle \right) \right|^{2}.$$

**Parallel circuits.** With n (or equivalently  $\mathfrak{n}$ ) fixed, the quantum circuit introduced above is uniquely defined by the choice of circuit parameters  $\boldsymbol{\theta} \in \boldsymbol{\Theta}$ . In what follows, we will now run N such circuits in parallel. Each circuit is described by its parameters  $\boldsymbol{\theta}^j \in \boldsymbol{\Theta}$ ,  $j \in \{1, ..., N\}$ . The circuit outputs then induce maps  $\mathbb{P}_m^{n, \boldsymbol{\theta}^j} : \mathbb{R}^N \times \mathbb{R}^d \to [0, 1]$  by the circuit output probabilities (2) with parameters for the j-th circuit given by  $\boldsymbol{\theta} = \boldsymbol{\theta}^j$ .

Recurrent quantum neural networks (RQNN). With these ingredients, we can now define the recurrent quantum neural network that we will consider. Given the gate map  $C_{n,\theta}$  and R > 0, we define  $\bar{F}_R^{n,\theta} : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}^N$  by its component maps  $\bar{F}_R^{n,\theta} = (\bar{F}_{R,1}^{n,\theta}, \dots, \bar{F}_{R,N}^{n,\theta})$ . For  $j = 1, \dots, N$ , the j-th component map  $\bar{F}_{R,j}^{n,\theta} : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$  is defined by

<span id="page-7-2"></span>
$$\bar{F}_{B,i}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) := R - 2R[\mathbb{P}_{1}^{n,\boldsymbol{\theta}^{j}}(\boldsymbol{x},\boldsymbol{z}) + \mathbb{P}_{2}^{n,\boldsymbol{\theta}^{j}}(\boldsymbol{x},\boldsymbol{z})], \quad (\boldsymbol{x},\boldsymbol{z}) \in \mathbb{R}^{N} \times \mathbb{R}^{d},$$
(3)

with  $\theta = (\theta^1, \dots, \theta^N) \in \Theta^N$ . Our recurrent quantum neural network (RQNN) is then defined by the state-space system associated to the state map  $\bar{F}_R^{n,\theta}$ 

<span id="page-7-1"></span>
$$\hat{\boldsymbol{x}}_t = \bar{F}_R^{n,\boldsymbol{\theta}}(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_t), \quad t \in \mathbb{Z}_-. \tag{4}$$

In the next paragraphs, we aim to address the following questions:

- Can we choose the parameters  $\theta$  in such a way that the system determined by (4) satisfies the echo state property?
- Can the family of systems determined by equations of the type (4) approximate general state-space systems arbitrarily well? More specifically, given an arbitrary state-space map  $\boldsymbol{x}_t = F(\boldsymbol{x}_{t-1}, \boldsymbol{z}_t)$  with  $F: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}^N$  as general as possible, can it be approximated by equations of the type (4)?

#### <span id="page-8-0"></span>2.2 RQNN approximation of state-space maps and their derivatives

As a first step, we aim to establish RQNN approximation results for a function jointly with its derivatives. Denote by  $\mathcal{F}_R$  the class of integrable functions  $f: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$  with Fourier integral bounded above by a constant R > 0, that is,

$$\mathcal{F} := \left\{ f : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R} : f \in \mathcal{C}\left(\mathbb{R}^N \times \mathbb{R}^d\right) \cap L^1\left(\mathbb{R}^N \times \mathbb{R}^d\right), \quad \|\widehat{f}\|_1 < \infty \right\}, \quad (5)$$

$$\mathcal{F}_R := \left\{ f \in \mathcal{F}, \text{ with } \|\widehat{f}\|_1 \le R \right\}, \quad \text{for } R > 0.$$
 (6)

Here, for a continuous and integrable function  $f: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$  we denote its Fourier transform by  $\widehat{f}(\boldsymbol{\xi}_1, \boldsymbol{\xi}_2) := \int_{\mathbb{R}^N \times \mathbb{R}^d} e^{-2\pi \mathrm{i}(\boldsymbol{y}_1, \boldsymbol{y}_2) \cdot (\boldsymbol{\xi}_1, \boldsymbol{\xi}_2)} f(\boldsymbol{y}_1, \boldsymbol{y}_2) \mathrm{d}\boldsymbol{y}_1 \mathrm{d}\boldsymbol{y}_2$ , with  $(\boldsymbol{\xi}_1, \boldsymbol{\xi}_2) \in \mathbb{R}^N \times \mathbb{R}^d$ .

**Proposition 2.1.** For any  $n \in \mathbb{N}$ , j = 1, ..., N,  $\boldsymbol{\theta} = (\boldsymbol{\theta}^1, ..., \boldsymbol{\theta}^N) \in \boldsymbol{\Theta}^N$  with  $\boldsymbol{\theta}^j = (\boldsymbol{a}^{i,j}, b^{i,j}, \gamma^{i,j})_{i=1,...,n} \in \boldsymbol{\Theta}$ , the RQNN introduced in (3) can be represented as

<span id="page-8-2"></span>
$$\bar{F}_{R,j}^{n,\theta}(\boldsymbol{x},\boldsymbol{z}) = \frac{1}{n} \sum_{i=1}^{n} R \cos\left(\gamma^{i,j}\right) \cos\left(b^{i,j} + \boldsymbol{a}^{i,j} \cdot (\boldsymbol{x},\boldsymbol{z})\right)$$
(7)

for all  $(\boldsymbol{x}, \boldsymbol{z}) \in \mathbb{R}^N \times \mathbb{R}^d$ .

*Proof.* It follows directly from Proposition 1 in [GJ25].

Let  $\mu$  be an arbitrary probability measure on  $(\mathbb{R}^N \times \mathbb{R}^d, \mathcal{B}(\mathbb{R}^N \times \mathbb{R}^d))$ . Recall the notation

$$\|f-g\|_{L^2(\mu)} := \left(\int_{\mathbb{R}^N imes \mathbb{R}^d} |f(\boldsymbol{x}, \boldsymbol{z}) - g(\boldsymbol{x}, \boldsymbol{z})|^2 \, \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})\right)^{1/2}.$$

<span id="page-8-1"></span>**Proposition 2.2.** Let R > 0 and suppose  $F = (F_1, ..., F_N) : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}^N$  is continuously differentiable and satisfies  $F_j \in \mathcal{F}_R$  and  $\partial_i F_j \in \mathcal{F}$  and  $\int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_i^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$  for i = 1, ..., N + d and j = 1, ..., N. Then, for any  $n \in \mathbb{N}$ , there exists  $\boldsymbol{\theta} \in \boldsymbol{\Theta}^N$  such that for any  $j \in \{1, ..., N\}$ ,

$$\left\| \bar{F}_{R,j}^{n,\theta} - F_j \right\|_{L^2(\mu)}^2 + \sum_{i=1}^{N+d} \left\| \partial_i \bar{F}_{R,j}^{n,\theta} - \partial_i F_j \right\|_{L^2(\mu)}^2 \le \frac{C_j}{n},$$

where 
$$C_j = \|\widehat{F_j}\|_1^2 + 4\pi^2 \|\widehat{F_j}\|_1 \int_{\mathbb{R}^N \times \mathbb{R}^d} \sum_{i=1}^{N+d} \xi_i^2 |\widehat{F_j}(\xi)| d\xi$$

*Proof.* Let  $j \in \{1, ..., N\}$  be fixed. As in the proof of Proposition 2 in [GJ25], we may use the Fourier inversion theorem to represent

<span id="page-9-1"></span>
$$F_j(\boldsymbol{x}, \boldsymbol{z}) = \int_{\mathbb{R}^N \times \mathbb{R}^d} e^{2\pi i(\boldsymbol{x}, \boldsymbol{z}) \cdot (\boldsymbol{\xi}_1, \boldsymbol{\xi}_2)} \widehat{F_j}(\boldsymbol{\xi}_1, \boldsymbol{\xi}_2) d\boldsymbol{\xi}_1 d\boldsymbol{\xi}_2,$$

which we may rewrite as, with  $\boldsymbol{\xi} = (\boldsymbol{\xi}_1, \boldsymbol{\xi}_2)$ ,

$$F_{j}(\boldsymbol{x}, \boldsymbol{z}) = \int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} \left\{ \cos \left( 2\pi(\boldsymbol{x}, \boldsymbol{z}) \cdot \boldsymbol{\xi} \right) \operatorname{Re}[\widehat{F_{j}}(\boldsymbol{\xi})] + \cos \left( 2\pi(\boldsymbol{x}, \boldsymbol{z}) \cdot \boldsymbol{\xi} + \frac{\pi}{2} \right) \operatorname{Im}[\widehat{F_{j}}(\boldsymbol{\xi})] \right\} d\boldsymbol{\xi}$$
(8)

The hypothesis  $\partial_i F_j \in \mathcal{F}$  implies that  $\int_{\mathbb{R}^N \times \mathbb{R}^d} |\xi_i| |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$ . Hence, applying differentiation under the integral sign yields

$$\partial_{i}F_{j}(\boldsymbol{x},\boldsymbol{z}) = -2\pi \int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \left\{ \xi_{i} \sin\left(2\pi(\boldsymbol{x},\boldsymbol{z})\cdot\boldsymbol{\xi}\right) \operatorname{Re}\left[\widehat{F_{j}}(\boldsymbol{\xi})\right] + \xi_{i} \sin\left(2\pi(\boldsymbol{x},\boldsymbol{z})\cdot\boldsymbol{\xi} + \frac{\pi}{2}\right) \operatorname{Im}\left[\widehat{F_{j}}(\boldsymbol{\xi})\right] \right\} d\boldsymbol{\xi}.$$

$$(9)$$

Next, consider the random function

<span id="page-9-2"></span><span id="page-9-0"></span>
$$\Phi_j(\boldsymbol{x}, \boldsymbol{z}) := \frac{1}{n} \sum_{i=1}^n W_i \cos(B_i + \mathbf{A}_i \cdot (\boldsymbol{x}, \boldsymbol{z}))$$
(10)

for randomly selected weights  $W_1, \ldots, W_n, B_1, \ldots, B_n$  and  $\mathbf{A}_1, \ldots, \mathbf{A}_n$  valued in  $\mathbb{R}$ ,  $\mathbb{R}$ , and  $\mathbb{R}^N \times \mathbb{R}^d$ , respectively (for notational simplicity we leave the dependence on j implicit here). The distributions of these random variables are chosen as follows. First, we let  $Z_1, \ldots, Z_n$  be i.i.d. Bernoulli random variables with

$$\mathbb{P}(Z_i = 1) = \frac{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\text{Re}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi}}{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}}, \qquad \mathbb{P}(Z_i = 0) = \frac{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\text{Im}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi}}{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}}.$$
 (11)

and let  $\nu_{\rm Re}$  and  $\nu_{\rm Im}$  be the probability measures on  $\mathbb{R}^N \times \mathbb{R}^d$  with densities

$$\frac{|\operatorname{Re}[\widehat{F_j}]|}{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\operatorname{Re}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi}} \quad \text{and} \quad \frac{|\operatorname{Im}[\widehat{F_j}]|}{\int_{\mathbb{R}^N \times \mathbb{R}^d} |\operatorname{Im}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi}}, \tag{12}$$

respectively. In case  $\int_{\mathbb{R}^N \times \mathbb{R}^d} |\operatorname{Re}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi} = 0$ , instead we choose for  $\nu_{\operatorname{Re}}$  an arbitrary probability measure and analogously for  $\nu_{\operatorname{Im}}$  in case  $\int_{\mathbb{R}^N \times \mathbb{R}^d} |\operatorname{Im}[\widehat{F_j}(\boldsymbol{\xi})]| d\boldsymbol{\xi} = 0$ . Next, let  $\mathbf{U}_1^{\operatorname{Re}}, \dots, \mathbf{U}_n^{\operatorname{Re}}$  (resp.  $\mathbf{U}_1^{\operatorname{Im}}, \dots, \mathbf{U}_n^{\operatorname{Im}}$ ) be i.i.d. random variables with distribution  $\nu_{\operatorname{Re}}$ 

(resp.  $\nu_{\text{Im}}$ ) and assume that  $\mathbf{U}_1^{\text{Im}} \dots, \mathbf{U}_n^{\text{Im}}, \mathbf{U}_1^{\text{Re}}, \dots, \mathbf{U}_n^{\text{Re}}, Z_1, \dots, Z_n$  are independent. With these preparations, we are now ready to define the weights in (10):

$$\mathbf{A}_{i} := 2\pi (Z_{i}\mathbf{U}_{i}^{\mathrm{Re}} + (1 - Z_{i})\mathbf{U}_{i}^{\mathrm{Im}}), \qquad B_{i} := \frac{\pi}{2}(1 - Z_{i}),$$

$$W_{i} := \|\widehat{F}_{j}\|_{1} \left[ \frac{\mathrm{Re}[\widehat{F}_{j}](\mathbf{U}_{i}^{\mathrm{Re}})}{|\mathrm{Re}[\widehat{F}_{j}](\mathbf{U}_{i}^{\mathrm{Re}})|} Z_{i} + \frac{\mathrm{Im}[\widehat{F}_{j}](\mathbf{U}_{i}^{\mathrm{Im}})}{|\mathrm{Im}[\widehat{F}_{j}](\mathbf{U}_{i}^{\mathrm{Im}})|} (1 - Z_{i}) \right],$$

with the quotient set to zero when the denominator is null.

Our goal now is to estimate

<span id="page-10-0"></span>
$$\mathbb{E}\left[\|F_{j} - \Phi_{j}\|_{L^{2}(\mu)}^{2} + \sum_{i=1}^{N+d} \|\partial_{i}F_{j} - \partial_{i}\Phi_{j}\|_{L^{2}(\mu)}^{2}\right] = \mathbb{E}\left[\|F_{j} - \Phi_{j}\|_{L^{2}(\mu)}^{2}\right] + \sum_{i=1}^{N+d} \mathbb{E}\left[\|\partial_{i}F_{j} - \partial_{i}\Phi_{j}\|_{L^{2}(\mu)}^{2}\right]$$
(13)

by estimating the summands separately. To achieve this, we first compute  $\mathbb{E}[\Phi_j(\boldsymbol{x},\boldsymbol{z})]$  and  $\mathbb{E}[\partial_i \Phi_j(\boldsymbol{x},\boldsymbol{z})]$ . Indeed, inserting the definitions, using independence and representation (8) yields

$$\begin{split} &\mathbb{E}[\Phi_{j}(\boldsymbol{x},\boldsymbol{z})] = \mathbb{E}[W_{1}\cos(B_{1}+\mathbf{A}_{1}\cdot(\boldsymbol{x},\boldsymbol{z}))] \\ &= \|\widehat{F}_{j}\|_{1}\mathbb{E}\left[\left(\frac{\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})}{|\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})|}Z_{1} + \frac{\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})}{|\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})|}(1-Z_{1})\right) \\ &\cos\left(\frac{\pi}{2}(1-Z_{1}) + 2\pi(Z_{1}\mathbf{U}_{1}^{\operatorname{Re}} + (1-Z_{1})\mathbf{U}_{i}^{\operatorname{Im}})\cdot(\boldsymbol{x},\boldsymbol{z})\right)\right] \\ &= \|\widehat{F}_{j}\|_{1}\left(\mathbb{P}(Z_{1}=1)\mathbb{E}\left[\frac{\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})}{|\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})|}\cos(2\pi\mathbf{U}_{1}^{\operatorname{Re}}\cdot(\boldsymbol{x},\boldsymbol{z}))\right] \right. \\ &+ \mathbb{P}(Z_{1}=0)\mathbb{E}\left[\frac{\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})}{|\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})|}\cos\left(\frac{\pi}{2} + 2\pi\mathbf{U}_{1}^{\operatorname{Im}}\cdot(\boldsymbol{x},\boldsymbol{z})\right)\right]\right) \\ &= \int_{\mathbb{R}^{N}\times\mathbb{R}^{d}}\operatorname{Re}[\widehat{F}_{j}](\boldsymbol{\xi})\cos(2\pi\boldsymbol{\xi}\cdot(\boldsymbol{x},\boldsymbol{z}))\mathrm{d}\boldsymbol{\xi} + \int_{\mathbb{R}^{N}\times\mathbb{R}^{d}}\operatorname{Im}[\widehat{F}_{j}](\boldsymbol{\xi})\cos(\frac{\pi}{2} + 2\pi\boldsymbol{\xi}\cdot(\boldsymbol{x},\boldsymbol{z}))\mathrm{d}\boldsymbol{\xi} \\ &= F_{j}(\boldsymbol{x},\boldsymbol{z}). \end{split}$$

Analogously, using the representation (9) for the partial derivative  $\partial_i F_j$  instead, we obtain

$$\mathbb{E}[\partial_{i}\Phi_{j}(\boldsymbol{x},\boldsymbol{z})] = -\mathbb{E}[W_{1}A_{1,i}\sin(B_{1} + \mathbf{A}_{1} \cdot (\boldsymbol{x},\boldsymbol{z}))]$$

$$= -2\pi \|\widehat{F}_{j}\|_{1} \left(\mathbb{P}(Z_{1} = 1)\mathbb{E}\left[\frac{\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})}{|\operatorname{Re}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Re}})|}U_{1,i}^{\operatorname{Re}}\sin(2\pi\mathbf{U}_{1}^{\operatorname{Re}} \cdot (\boldsymbol{x},\boldsymbol{z}))\right]\right]$$

$$+\mathbb{P}(Z_{1} = 0)\mathbb{E}\left[\frac{\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})}{|\operatorname{Im}[\widehat{F}_{j}](\mathbf{U}_{1}^{\operatorname{Im}})|}U_{1,i}^{\operatorname{Im}}\sin\left(\frac{\pi}{2} + 2\pi\mathbf{U}_{1}^{\operatorname{Im}} \cdot (\boldsymbol{x},\boldsymbol{z})\right)\right]\right)$$

$$= -2\pi \left(\int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \boldsymbol{\xi}_{i}\operatorname{Re}[\widehat{F}_{j}](\boldsymbol{\xi})\sin(2\pi\boldsymbol{\xi} \cdot (\boldsymbol{x},\boldsymbol{z}))d\boldsymbol{\xi} + \int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \boldsymbol{\xi}_{i}\operatorname{Im}[\widehat{F}_{j}](\boldsymbol{\xi})\sin(\frac{\pi}{2} + 2\pi\boldsymbol{\xi} \cdot (\boldsymbol{x},\boldsymbol{z}))d\boldsymbol{\xi}\right)$$

$$= \partial_{i}F_{j}(\boldsymbol{x},\boldsymbol{z}).$$
(14)

Therefore, we may estimate the first expectation in (13) as follows:

<span id="page-11-0"></span>
$$\mathbb{E}\left[\|F_{j} - \Phi_{j}\|_{L^{2}(\mu)}^{2}\right] = \mathbb{E}\left[\int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} |F_{j}(\boldsymbol{x}, \boldsymbol{z}) - \Phi_{j}(\boldsymbol{x}, \boldsymbol{z})|^{2} \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})\right] = \int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} \mathbb{V}[\Phi_{j}(\boldsymbol{x}, \boldsymbol{z})] \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})$$

$$= \frac{1}{n^{2}} \int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} \mathbb{V}\left[\sum_{i=1}^{n} W_{i} \cos(B_{i} + \mathbf{A}_{i} \cdot (\boldsymbol{x}, \boldsymbol{z}))\right] \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})$$

$$= \frac{1}{n} \int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} \mathbb{V}\left[W_{1} \cos(B_{1} + \mathbf{A}_{1} \cdot (\boldsymbol{x}, \boldsymbol{z}))\right] \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})$$

$$\leq \frac{1}{n} \int_{\mathbb{R}^{N} \times \mathbb{R}^{d}} \mathbb{E}\left[\left(W_{1} \cos(B_{1} + \mathbf{A}_{1} \cdot (\boldsymbol{x}, \boldsymbol{z}))\right)^{2}\right] \mu(\mathrm{d}\boldsymbol{x}, \mathrm{d}\boldsymbol{z})$$

$$\leq \frac{1}{n} \mathbb{E}\left[W_{1}^{2}\right] = \frac{1}{n} \|\widehat{F}_{j}\|_{1}^{2}.$$
(15)

For the partial derivatives, we obtain analogously

<span id="page-11-1"></span>
$$\mathbb{E}\left[\left\|\partial_{i}F_{j}-\partial_{i}\Phi_{j}\right\|_{L^{2}(\mu)}^{2}\right] = \int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \mathbb{V}\left[\partial_{i}\Phi_{j}(\boldsymbol{x},\boldsymbol{z})\right]\mu(\mathrm{d}\boldsymbol{x},\mathrm{d}\boldsymbol{z})$$

$$= \frac{1}{n^{2}}\int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \mathbb{V}\left[\sum_{k=1}^{n}W_{k}A_{k,i}\sin(B_{k}+\mathbf{A}_{k}\cdot(\boldsymbol{x},\boldsymbol{z}))\right]\mu(\mathrm{d}\boldsymbol{x},\mathrm{d}\boldsymbol{z})$$

$$= \frac{1}{n}\int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \mathbb{V}\left[W_{1}A_{1,i}\sin(B_{1}+\mathbf{A}_{1}\cdot(\boldsymbol{x},\boldsymbol{z}))\right]\mu(\mathrm{d}\boldsymbol{x},\mathrm{d}\boldsymbol{z})$$

$$\leq \frac{1}{n}\int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \mathbb{E}\left[\left(W_{1}A_{1,i}\sin(B_{1}+\mathbf{A}_{1}\cdot(\boldsymbol{x},\boldsymbol{z}))\right)^{2}\right]\mu(\mathrm{d}\boldsymbol{x},\mathrm{d}\boldsymbol{z})$$

$$\leq \frac{1}{n}\mathbb{E}\left[W_{1}^{2}A_{1,i}^{2}\right] = \frac{1}{n}\|\widehat{F}_{j}\|_{1}^{2}\mathbb{E}\left[A_{1,i}^{2}\right] = \frac{4\pi^{2}}{n}\|\widehat{F}_{j}\|_{1}\int_{\mathbb{R}^{N}\times\mathbb{R}^{d}} \boldsymbol{\xi}_{i}^{2}|\widehat{F}_{j}(\boldsymbol{\xi})|\mathrm{d}\boldsymbol{\xi},$$
(16)

where we used that  $\mathbb{E}\left[A_{1,i}^2\right] = 4\pi^2 \|\widehat{F_j}\|_1^{-1} \int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_i^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}.$ 

In particular, (15) and (16) imply that there exists a scenario  $\omega \in \Omega$  such that  $\Phi_i^{\omega}(\boldsymbol{x}, \boldsymbol{z}) = \frac{1}{n} \sum_{i=1}^n W_i(\omega) \cos(B_i(\omega) + \mathbf{A}_i(\omega) \cdot (\boldsymbol{x}, \boldsymbol{z}))$  satisfies

<span id="page-12-0"></span>
$$||F_{j} - \Phi_{j}^{\omega}||_{L^{2}(\mu)}^{2} + \sum_{i=1}^{N+d} ||\partial_{i}F_{j} - \partial_{i}\Phi_{j}^{\omega}||_{L^{2}(\mu)}^{2} \le \frac{C_{j}}{n}, \tag{17}$$

with  $C_j = \|\widehat{F_j}\|_1^2 + 4\pi^2 \|\widehat{F_j}\|_1 \int_{\mathbb{R}^N \times \mathbb{R}^d} \sum_{i=1}^{N+d} \xi_i^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}$ . Finally,  $\boldsymbol{\theta} = (\boldsymbol{\theta}^1, \dots, \boldsymbol{\theta}^N)$  can then be constructed by setting  $\boldsymbol{\theta}^j = (\mathbf{A}_i(\omega), B_i(\omega), \arccos(\frac{W_i(\omega)}{R}))_{i=1,\dots,n}$ , which guarantees that  $\Phi_j^{\omega} = \bar{F}_{R,j}^{n,\boldsymbol{\theta}}$  and so the proposition follows.

<span id="page-12-2"></span>Corollary 2.3. Consider the setting of Proposition 2.2 and assume, in addition, that

$$I_q = \int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^q |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$$

for some  $q \geq 2$ . Then, for any  $n \in \mathbb{N}$ , there exists  $\boldsymbol{\theta} \in \boldsymbol{\Theta}$  such that for any  $j \in \{1, \dots, N\}$ ,

$$\left\|\bar{F}_{R,j}^{n,\boldsymbol{\theta}} - F_j\right\|_{L^2(\mu)}^2 + \sum_{i=1}^{N+d} \left\|\partial_i \bar{F}_{R,j}^{n,\boldsymbol{\theta}} - \partial_i F_j\right\|_{L^2(\mu)}^2 \le \frac{\bar{C}_j}{n},$$

where  $\bar{C}_j = 3C_j$ . Moreover, we can choose  $\boldsymbol{\theta} = (\boldsymbol{\theta}^1, \dots, \boldsymbol{\theta}^N) \in \boldsymbol{\Theta}^N$  with  $\boldsymbol{\theta}^j = (\boldsymbol{a}^{i,j}, b^{i,j}, \gamma^{i,j})_{i=1,\dots,n}$  in such a way that

$$\|\boldsymbol{a}^{i,j}\| \le 2\pi \left(3n\|\widehat{F_j}\|_1^{-1} \int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^q |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}\right)^{\frac{1}{q}}$$

$$\tag{18}$$

for all i = 1, ..., n, j = 1, ..., N.

The proof of this corollary requires the following lemma, which extends [Gon24, Lemma 4.10].

<span id="page-12-1"></span>**Lemma 2.4.** Let  $d, n, q \in \mathbb{N}$ , let  $M_1, M_2 > 0$ , let U be a non-negative random variable, and let  $Y_1, \ldots, Y_n$  be i.i.d.  $\mathbb{R}^d$ -valued random variables. Suppose  $\mathbb{E}[U] \leq M_1$  and  $\mathbb{E}[|Y_1|^q] \leq M_2$ . Then

$$\mathbb{P}\bigg[U \le 3M_1, \max_{i=1,\dots,n} |Y_i| \le (3nM_2)^{\frac{1}{q}}\bigg] > 0.$$

*Proof.* The proof mimics that of in [Gon24, Lemma 4.10] by replacing the use of Markov's inequality for q = 1 by the more general version:

$$\mathbb{P}[|Y_1| > (3nM_2)^{\frac{1}{q}}] \le \frac{\mathbb{E}[|Y_1|^q]}{3nM_2} \le \frac{1}{3n}.$$

*Proof of the corollary.* The corollary follows by replacing the argument leading to (17) in the proof of Proposition 2.2 by Lemma 2.4 and by noticing that

$$\mathbb{E}\left[\|\mathbf{A}_1\|^q\right] = (2\pi)^q \|\widehat{F}_j\|_1^{-1} \int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^q |\widehat{F}_j(\boldsymbol{\xi})| d\boldsymbol{\xi}.$$

Next, we complement the  $L^2(\mathbb{R}^N \times \mathbb{R}^d, \mu)$ -error bound in Proposition 2.2 with a uniform error bound on compact sets. For M > 0 and  $f, g \in \mathcal{C}(\mathbb{R}^N \times \mathbb{R}^d)$  denote

$$\|f-g\|_{\infty,M} := \sup_{({oldsymbol x},{oldsymbol z}) \in [-M,M]^N imes [-M,M]^d} |f({oldsymbol x},{oldsymbol z}) - g({oldsymbol x},{oldsymbol z})|.$$

<span id="page-13-0"></span>**Proposition 2.5.** Let R, M > 0 and suppose  $F = (F_1, ..., F_N)$  is continuously differentiable and satisfies  $F_j \in \mathcal{F}_R$  and  $\partial_i F_j \in \mathcal{F}$  and  $\int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^4 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$  for j = 1, ..., N. Then, for any  $n \in \mathbb{N}$ , there exists  $\boldsymbol{\theta} \in \boldsymbol{\Theta}$  such that for any  $j \in \{1, ..., N\}$ ,

<span id="page-13-1"></span>
$$\left\| \bar{F}_{R,j}^{n,\theta} - F_j \right\|_{\infty,M} + \sum_{i=1}^{N+d} \left\| \partial_i \bar{F}_{R,j}^{n,\theta} - \partial_i F_j \right\|_{\infty,M} \le \frac{C_j^{\infty}}{\sqrt{n}},\tag{19}$$

where  $C_j^{\infty} = 2(\pi+1)\|\widehat{F_j}\|_1 + (8\pi M + 4\pi^2)(N+d)^{\frac{1}{2}}\|\widehat{F_j}\|_1^{\frac{1}{2}}I_{2,j}^{1/2} + 16M\pi^2(N+d)\|\widehat{F_j}\|_1^{1/2}I_{4,j}^{1/2}$  for  $I_{q,j} = \int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^q |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$ .

*Proof.* It follows by combining the proof of Proposition 2.2 with the proof of Theorem 3 in [GJ25]. More specifically, the same proof can be used as for Proposition 2.2, except that we need to replace the  $L^2(\mu)$  error bounds in (15) and (16) by uniform bounds. For (15), we can follow precisely the proof of Theorem 3 in [GJ25] to obtain

$$\left\| \bar{F}_{R,j}^{n,\theta} - F_j \right\|_{\infty,M} \le \frac{C_j^{\infty,0}}{\sqrt{n}} \tag{20}$$

with  $C_j^{\infty,0} = 2(\pi+1)\|\widehat{F_j}\|_1 + 8\pi M(N+d)^{\frac{1}{2}}\|\widehat{F_j}\|_1^{\frac{1}{2}} \left(\int_{\mathbb{R}^N\times\mathbb{R}^d} \sum_{i=1}^{N+d} \xi_i^2 |\widehat{F_j}(\boldsymbol{\xi})| \mathrm{d}\boldsymbol{\xi}\right)^{1/2}$ . Next, we turn to the derivatives, that is, we aim to estimate  $\left\|\partial_k \bar{F}_{R,j}^{n,\theta} - \partial_k F_j\right\|_{\infty,M}$ . Also in this case, we may proceed as in the proof of Theorem 3 in [GJ25] and apply the same estimates to the random variables  $U_{i,(\boldsymbol{x},\boldsymbol{z})} = W_i A_{i,k} \sin(B_i + \mathbf{A}_i \cdot (\boldsymbol{x},\boldsymbol{z}))$ . Let  $\varepsilon_1,\ldots,\varepsilon_n$  be i.i.d. Rademacher random variables independent of  $\mathbf{A} = (\mathbf{A}_1,\ldots,\mathbf{A}_n)$  and  $\mathbf{B} = (B_1,\ldots,B_n)$ .

Symmetrisation and independence then yield

$$\begin{aligned} \left\| \partial_{i} \bar{F}_{R,j}^{n,\boldsymbol{\theta}} - \partial_{i} F_{j} \right\|_{\infty,M} &= \mathbb{E} \left[ \sup_{(\boldsymbol{x},\boldsymbol{z}) \in [-M,M]^{N+d}} \left| \frac{1}{n} \sum_{i=1}^{n} \left( U_{i,(\boldsymbol{x},\boldsymbol{z})} - \mathbb{E}[U_{i,(\boldsymbol{x},\boldsymbol{z})}] \right) \right| \right] \\ &\leq 2 \mathbb{E} \left[ \sup_{(\boldsymbol{x},\boldsymbol{z}) \in [-M,M]^{N+d}} \left| \frac{1}{n} \sum_{i=1}^{n} \varepsilon_{i} U_{i,(\boldsymbol{x},\boldsymbol{z})} \right| \right] \\ &= 2 \mathbb{E} \left[ \mathbb{E} \left[ \sup_{(\boldsymbol{x},\boldsymbol{z}) \in [-M,M]^{N+d}} \left| \frac{1}{n} \sum_{i=1}^{n} \varepsilon_{i} w_{i} a_{i,k} \sin(b_{i} + \mathbf{a}_{i} \cdot (\boldsymbol{x},\boldsymbol{z})) \right| \right] \right|_{(\mathbf{w},\boldsymbol{a},\mathbf{b}) = (\mathbf{W},\mathbf{A},\mathbf{B})} \right]. \end{aligned}$$

Now fix  $\mathbf{a} = (\mathbf{a}_1, \dots, \mathbf{a}_n) \in (\mathbb{R}^N \times \mathbb{R}^d)^n$ ,  $\mathbf{b} = (b_1, \dots, b_n) \in \mathbb{R}^n$ ,  $\mathbf{w} = (w_1, \dots, w_n) \in \mathbb{R}^n$  and denote

$$\mathcal{T} := \{ (w_i a_{i,k} (b_i + \mathbf{a}_i \cdot (\boldsymbol{x}, \boldsymbol{z})))_{i=1,\dots,n} : (\boldsymbol{x}, \boldsymbol{z}) \in [-M, M]^{N+d} \},$$

$$\varrho_i(x) := w_i a_{i,k} \sin(\frac{x}{w_i a_{i,k}}), \quad x \in \mathbb{R},$$

for i = 1, ..., n. Then, using the definitions in the first step, the comparison theorem [LT13, Theorem 4.12] in the second step (note  $\varrho_i(0) = 0$  and  $\varrho_i$  is 1-Lipschitz), and standard Rademacher estimates (see, e.g., [Gon23]), we obtain

$$\mathbb{E}\left[\sup_{(\boldsymbol{x},\boldsymbol{z})\in[-M,M]^{N+d}}\left|\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}w_{i}a_{i,k}\sin(b_{i}+\mathbf{a}_{i}\cdot(\boldsymbol{x},\boldsymbol{z}))\right|\right] \\
= \mathbb{E}\left[\sup_{\mathbf{t}\in\mathcal{T}}\left|\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}\varrho_{i}(t_{i})\right|\right] \leq 2\mathbb{E}\left[\sup_{\mathbf{t}\in\mathcal{T}}\left|\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}t_{i}\right|\right] \\
= 2\mathbb{E}\left[\sup_{(\boldsymbol{x},\boldsymbol{z})\in[-M,M]^{N+d}}\left|\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}(w_{i}a_{i,k}(b_{i}+\mathbf{a}_{i}\cdot(\boldsymbol{x},\boldsymbol{z})))\right|\right] \\
\leq 2\mathbb{E}\left[\left|\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}w_{i}a_{i,k}b_{i}\right|\right] + 2\mathbb{E}\left[\sup_{(\boldsymbol{x},\boldsymbol{z})\in[-M,M]^{N+d}}\left|(\boldsymbol{x},\boldsymbol{z})\cdot\frac{1}{n}\sum_{i=1}^{n}\varepsilon_{i}w_{i}a_{i,k}\mathbf{a}_{i}\right|\right] \\
\leq \frac{2}{n}\left(\sum_{i=1}^{n}w_{i}^{2}a_{i,k}^{2}b_{i}^{2}\right)^{1/2} + \frac{2M}{n}\sum_{l=1}^{N+d}\left(\sum_{i=1}^{n}w_{i}^{2}a_{i,k}^{2}a_{i,l}^{2}\right)^{1/2}.$$

Putting everything together, we obtain

$$\begin{split} \left\| \partial_{i} \bar{F}_{R,j}^{n,\theta} - \partial_{i} F_{j} \right\|_{\infty,M} &\leq 2 \mathbb{E} \left[ \frac{2}{n} \left( \sum_{i=1}^{n} W_{i}^{2} A_{i,k}^{2} B_{i}^{2} \right)^{1/2} + \frac{2M}{n} \sum_{l=1}^{N+d} \left( \sum_{i=1}^{n} W_{i}^{2} A_{i,k}^{2} A_{i,l}^{2} \right)^{1/2} \right] \\ &\leq \frac{4}{\sqrt{n}} \left( \mathbb{E} \left[ W_{i}^{2} A_{i,k}^{2} B_{i}^{2} \right]^{1/2} + M(N+d)^{1/2} \left( \sum_{l=1}^{N+d} \mathbb{E} \left[ W_{i}^{2} A_{i,k}^{2} A_{i,l}^{2} \right] \right)^{1/2} \right) \\ &\leq \frac{C_{j}^{\infty,k}}{\sqrt{n}}, \end{split}$$

with  $C_j^{\infty,k} = 4\pi^2 \|\widehat{F_j}\|_1^{1/2} \left( \left( \int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_k^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} \right)^{1/2} + 4M(N+d)^{1/2} \left( \int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_k^2 \|\boldsymbol{\xi}\|^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} \right)^{1/2} \right)$ . Here, the last estimate follows from the inequality

$$\mathbb{E}\left[W_i^2 A_{i,k}^2 B_i^2\right] \le \pi^4 \|\widehat{F_j}\|_1 \int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_k^2 |\widehat{F_j}(\boldsymbol{\xi})| \mathrm{d}\boldsymbol{\xi}$$

and

$$\mathbb{E}\left[W_i^2 A_{i,k}^2 A_{i,l}^2\right] = 16\pi^4 \|\widehat{F_j}\|_1 \int_{\mathbb{R}^N \times \mathbb{R}^d} \xi_k^2 \xi_l^2 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi}.$$

Overall, we obtain (19) with  $C_j^{\infty} \ge \sum_{k=0}^{N+d} C_j^{\infty,k}$  chosen as

$$C_j^{\infty} = 2(\pi + 1)\|\widehat{F_j}\|_1 + (8\pi M + 4\pi^2)(N + d)^{\frac{1}{2}}\|\widehat{F_j}\|_1^{\frac{1}{2}}I_{2,j}^{1/2} + 16M\pi^2(N + d)\|\widehat{F_j}\|_1^{1/2}I_{4,j}^{1/2}.$$

<span id="page-15-0"></span>**Corollary 2.6.** Let  $F = (F_1, ..., F_N)$  be continuously differentiable. Then for any  $\varepsilon > 0$  and  $\mathcal{X} \subset \mathbb{R}^N \times \mathbb{R}^d$  compact there exist  $n \in \mathbb{N}$ , R > 0 and  $\boldsymbol{\theta} \in \boldsymbol{\Theta}$  such that for any  $j \in \{1, ..., N\}$ ,  $\bar{F}_{R,j}^{n,\boldsymbol{\theta}}$  satisfies

$$\sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_j(\boldsymbol{x},\boldsymbol{z}) - \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_j(\boldsymbol{x},\boldsymbol{z}) - \nabla \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})\| \le \varepsilon.$$
 (21)

*Proof.* First, extending the proof of Corollary 4 in [GJ25], we show that  $F_j$  can be approximated on  $\mathcal{X}$  up to error  $\frac{\varepsilon}{2}$  in  $C^1$ -norm by a function in  $C_c^{\infty}(\mathbb{R}^N \times \mathbb{R}^d)$ . Indeed, first let M > 0 be such that  $\mathcal{X} \subset [-M, M]^{N+d}$ . Then, classical approximation results (see, e.g., [Whi34, Lemma 5]) imply that there exists a smooth function  $h: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$  such that

<span id="page-15-1"></span>
$$\sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_j(\boldsymbol{x},\boldsymbol{z}) - h(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_j(\boldsymbol{x},\boldsymbol{z}) - \nabla h(\boldsymbol{x},\boldsymbol{z})\| \le \frac{\varepsilon}{2}.$$
 (22)

Without loss of generality we may assume that  $h \in C_c^{\infty}(\mathbb{R}^N \times \mathbb{R}^d)$ . Otherwise, we multiply h with a cutoff function  $\psi \in C_c^{\infty}(\mathbb{R}^N \times \mathbb{R}^d)$  which is equal to 1 in an open set U with  $\mathcal{X} \subset U$  (see, e.g., [Hör90, Theorem 1.4.1]); thereby preserving (22).

In the next step, we now apply Proposition 2.5 to h. Since h is a Schwartz function, its Fourier transform  $\hat{h}$  is also a Schwartz function and thus h is integrable and

$$\int_{\mathbb{R}^N \times \mathbb{R}^d} (1 + \|\boldsymbol{\xi}\|^4) |\widehat{h}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty.$$

In particular,  $h \in \mathcal{F}_R$  for R > 0 large enough and, as h is a Schwartz function, also  $\partial_i h \in \mathcal{F}$  for all i. Thus, the hypotheses of Proposition 2.5 are satisfied and we obtain that there exist  $n \in \mathbb{N}$  and  $\theta \in \Theta$  such that

$$\left\| \bar{F}_{R,j}^{n,\theta} - h \right\|_{\infty,M} + \sum_{i=1}^{N+d} \left\| \partial_i \bar{F}_{R,j}^{n,\theta} - \partial_i h \right\|_{\infty,M} \le \frac{\varepsilon}{2}.$$

This estimate together with (22) then imply

$$\sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_{j}(\boldsymbol{x},\boldsymbol{z}) - \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_{j}(\boldsymbol{x},\boldsymbol{z}) - \nabla \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})\|$$

$$\leq \sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_{j}(\boldsymbol{x},\boldsymbol{z}) - h(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_{j}(\boldsymbol{x},\boldsymbol{z}) - \nabla h(\boldsymbol{x},\boldsymbol{z})\|$$

$$+ \sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |h(\boldsymbol{x},\boldsymbol{z}) - \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})| + \|\nabla \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) - \nabla h(\boldsymbol{x},\boldsymbol{z})\|$$

$$\leq \sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_{j}(\boldsymbol{x},\boldsymbol{z}) - h(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_{j}(\boldsymbol{x},\boldsymbol{z}) - \nabla h(\boldsymbol{x},\boldsymbol{z})\|$$

$$+ \sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) - h(\boldsymbol{x},\boldsymbol{z})| + \sum_{i=1}^{N+d} |\partial_{i}\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) - \partial_{i}h(\boldsymbol{x},\boldsymbol{z})|$$

$$\leq \sup_{(\boldsymbol{x},\boldsymbol{z})\in\mathcal{X}} |F_{j}(\boldsymbol{x},\boldsymbol{z}) - h(\boldsymbol{x},\boldsymbol{z})| + \|\nabla F_{j}(\boldsymbol{x},\boldsymbol{z}) - \nabla h(\boldsymbol{x},\boldsymbol{z})\|$$

$$+ \|\bar{F}_{R,j}^{n,\boldsymbol{\theta}} - h\|_{\infty,M} + \sum_{i=1}^{N+d} \|\partial_{i}\bar{F}_{R,j}^{n,\boldsymbol{\theta}} - \partial_{i}h\|_{\infty,M} \leq \varepsilon,$$

where we used that

$$\|
abla ar{F}_{R,j}^{n,oldsymbol{ heta}}(oldsymbol{x},oldsymbol{z}) - 
abla h(oldsymbol{x},oldsymbol{z})\| = \left(\sum_{i=1}^{N+d}|\partial_iar{F}_{R,j}^{n,oldsymbol{ heta}}(oldsymbol{x},oldsymbol{z}) - \partial_i h(oldsymbol{x},oldsymbol{z})|^2
ight)^{1/2} \leq \sum_{i=1}^{N+d}|\partial_iar{F}_{R,j}^{n,oldsymbol{ heta}}(oldsymbol{x},oldsymbol{z}) - \partial_i h(oldsymbol{x},oldsymbol{z})|,$$

since 
$$\|\boldsymbol{y}\|_2 \leq \|\boldsymbol{y}\|_1$$
 for all  $\boldsymbol{y} \in \mathbb{R}^{N+d}$ .

#### <span id="page-17-0"></span>2.3 Recurrent QNN approximation bounds for state-space filters

The results in the previous section show that the family of RQNNs that were introduced in (3) is capable of approximating arbitrarily well the very general class of continuously differentiable state-space maps with bounded Fourier transform, together with their derivatives. These approximations hold with respect to both the  $L^2$  norm (Proposition 2.2 and Corollary 2.3) and the  $L^{\infty}$  norm on compacta (Proposition 2.5 and Corollary 2.6). As in the internal approximation approach introduced in [GO18a, Theorem 3.1 (iii)], we will use the uniform RQNN approximation results for the state maps to conclude similar uniform approximation results for the corresponding filters under additional hypotheses that guarantee that those exist.

Consider a state-space system

<span id="page-17-2"></span>
$$\boldsymbol{x}_t = F(\boldsymbol{x}_{t-1}, \boldsymbol{z}_t), \quad t \in \mathbb{Z}_-, \tag{23}$$

with state process  $(\boldsymbol{x}_t)_{t\in\mathbb{Z}_-}$  valued in  $\mathbb{R}^N$ , input process  $(\boldsymbol{z}_t)_{t\in\mathbb{Z}_-}$  valued in  $\mathbb{R}^d$  and  $F:\mathbb{R}^N\times\mathbb{R}^d\to\mathbb{R}^N$ . We work under the assumption that F satisfies Barron-type integrability conditions [Bar92], [Bar93], [BK18] and F is contractive. Then, see, e.g., Proposition 1 and Remark 2 in [GGO20], it follows that, for any compact subset  $D_d\subset\mathbb{R}^d$ , the associated filter  $U^F:(D_d)^{\mathbb{Z}_-}\to(B_N)^{\mathbb{Z}_-}$  induced by the restriction of F to  $B_N\times D_d$  is well-defined and continuous.

Our next result shows that among the RQNNs that we discussed in Proposition 2.5 there exist systems that have the echo state property and hence have a filter associated. More importantly, those filters can be used to uniformly approximate any of the filters corresponding to the general systems introduced above in (23) as long as they satisfy a Barron-type integrability condition and are sufficiently contractive.

<span id="page-17-1"></span>**Proposition 2.7.** Suppose F in (23) is continuously differentiable with  $\|\nabla_{\boldsymbol{x}}F_j(\boldsymbol{x},\boldsymbol{z})\| \leq \frac{\lambda}{\sqrt{N}}$  for all  $\boldsymbol{x} \in \mathbb{R}^N$ ,  $\boldsymbol{z} \in D_d$ ,  $j \in \{1,\ldots,N\}$  for some  $\lambda \in (0,1)$  and, moreover, F satisfies  $F_j \in \mathcal{F}_R$ ,  $\partial_i F_j \in \mathcal{F}$  and  $\int_{\mathbb{R}^N \times \mathbb{R}^d} \|\boldsymbol{\xi}\|^4 |\widehat{F_j}(\boldsymbol{\xi})| d\boldsymbol{\xi} < \infty$  for  $j = 1,\ldots,N$ . Denote by  $U^F \colon (D_d)^{\mathbb{Z}_-} \to (B_N)^{\mathbb{Z}_-}$  the filter associated to (23). Then for any  $n \in \mathbb{N}$  with  $n > n_0$  there exists  $\boldsymbol{\theta} \in \boldsymbol{\Theta}$  such that the system (4) has the echo state property and the associated filter  $\bar{U} \colon (D_d)^{\mathbb{Z}_-} \to (\mathbb{R}^N)^{\mathbb{Z}_-}$  satisfies

<span id="page-17-3"></span>
$$\sup_{\boldsymbol{z} \in (D_d)^{\mathbb{Z}_-}} \sup_{t \in \mathbb{Z}_-} \left\| U^F(\boldsymbol{z})_t - \bar{U}(\boldsymbol{z})_t \right\| \le \frac{1}{1 - \lambda} \frac{\sqrt{N} \max_{j=1,\dots,N} C_j^{\infty}}{\sqrt{n}}.$$
 (24)

Here,  $n_0$  may be chose n as  $n_0 = N^2 \frac{(\max_{j=1,...,N} C_j^{\infty})^2}{(1-\lambda)^2}$ .

*Proof.* Choose M such that  $B_N \times D_d \subset [-M, M]^{N+d}$  and  $[-R, R]^N \times D_d \subset [-M, M]^{N+d}$ . Firstly, our hypotheses on F guarantee that F satisfies the hypotheses of Proposition 2.5.

Hence, there exists  $\theta \in \Theta$  such that for any  $j \in \{1, ..., N\}$ ,

$$\left\| \bar{F}_{R,j}^{n,\theta} - F_j \right\|_{\infty,M} + \sum_{i=1}^{N+d} \left\| \partial_i \bar{F}_{R,j}^{n,\theta} - \partial_i F_j \right\|_{\infty,M} \le \frac{C_j^{\infty}}{\sqrt{n}}.$$
 (25)

Then, for all  $\boldsymbol{x} \in [-M, M]^N, \boldsymbol{z} \in D_d$ 

$$\|\nabla_{\boldsymbol{x}}\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})\| \leq \|\nabla_{\boldsymbol{x}}\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) - \nabla_{\boldsymbol{x}}F_{j}(\boldsymbol{x},\boldsymbol{z})\| + \|\nabla_{\boldsymbol{x}}F_{j}(\boldsymbol{x},\boldsymbol{z})\|$$

$$\leq \left(\sum_{i=1}^{N} |\partial_{i}\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) - \partial_{i}F_{j}(\boldsymbol{x},\boldsymbol{z})|^{2}\right)^{1/2} + \frac{\lambda}{\sqrt{N}}$$

$$\leq \sqrt{N} \frac{\max_{j=1,\dots,N} C_{j}^{\infty}}{\sqrt{n}} + \frac{\lambda}{\sqrt{N}}.$$
(26)

Therefore, using the mean-value theorem, we obtain for all  $\boldsymbol{x} \in [-M, M]^N, \boldsymbol{z} \in D_d$  that

$$\begin{split} \|\bar{F}_{R}^{n,\boldsymbol{\theta}}(\boldsymbol{x}^{1},\boldsymbol{z}) - \bar{F}_{R}^{n,\boldsymbol{\theta}}(\boldsymbol{x}^{2},\boldsymbol{z})\|^{2} &= \sum_{j=1}^{N} (\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x}^{1},\boldsymbol{z}) - \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x}^{2},\boldsymbol{z}))^{2} \\ &\leq \sum_{j=1}^{N} \|\boldsymbol{x}^{1} - \boldsymbol{x}^{2}\|^{2} \max_{\boldsymbol{x} \in [-M,M]^{N}} \|\nabla_{\boldsymbol{x}} \bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z})\|^{2} \\ &\leq N \left(\sqrt{N} \frac{\max_{j=1,\dots,N} C_{j}^{\infty}}{\sqrt{n}} + \frac{\lambda}{\sqrt{N}}\right)^{2} \|\boldsymbol{x}^{1} - \boldsymbol{x}^{2}\|^{2}. \end{split}$$

In particular, for n satisfying  $N^2 \frac{(\max_{j=1,\ldots,N} C_j^{\infty})^2}{(1-\lambda)^2} < n$  we obtain that  $\bar{F}_R^{n,\theta} \colon B_R \times D_d \to B_R$ , with  $B_R = \{ \boldsymbol{x} \in \mathbb{R}^N \colon \|\boldsymbol{x}\| \le R\sqrt{N} \}$ , is contractive in the first argument, hence the system (4) has the echo state property by [GGO20, Proposition 1].

By the mean value theorem, the assumption  $\|\nabla_{\boldsymbol{x}}F_j(\boldsymbol{x},\boldsymbol{z})\| \leq \frac{\lambda}{\sqrt{N}}$  guarantees that  $F(\cdot,\boldsymbol{z})$  is  $\lambda$ -contractive for any  $\boldsymbol{z} \in D_d$ . Hence, we may estimate

<span id="page-18-0"></span>
$$||U^{F}(\boldsymbol{z})_{t} - \bar{U}(\boldsymbol{z})_{t}|| = ||\boldsymbol{x}_{t} - \hat{\boldsymbol{x}}_{t}|| = ||F(\boldsymbol{x}_{t-1}, \boldsymbol{z}_{t}) - \bar{F}_{R}^{n,\boldsymbol{\theta}}(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_{t})||$$

$$\leq ||F(\boldsymbol{x}_{t-1}, \boldsymbol{z}_{t}) - F(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_{t})|| + ||F(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_{t}) - \bar{F}_{R}^{n,\boldsymbol{\theta}}(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_{t})||$$

$$\leq \lambda ||\boldsymbol{x}_{t-1} - \hat{\boldsymbol{x}}_{t-1}|| + \left(\sum_{j=1}^{N} ||\bar{F}_{R,j}^{n,\boldsymbol{\theta}} - F_{j}||_{\infty,M}^{2}\right)^{1/2}$$

$$\leq \lambda ||\boldsymbol{x}_{t-1} - \hat{\boldsymbol{x}}_{t-1}|| + \frac{\sqrt{N} \max_{j=1,\dots,N} C_{j}^{\infty}}{\sqrt{n}}.$$
(27)

Iterating (27), we obtain

$$||U^{F}(\boldsymbol{z})_{t} - \bar{U}(\boldsymbol{z})_{t}|| \leq \lambda^{J} ||\boldsymbol{x}_{t-J} - \hat{\boldsymbol{x}}_{t-J}|| + \sum_{k=1}^{J} \lambda^{k-1} \frac{\sqrt{N} \max_{j=1,\dots,N} C_{j}^{\infty}}{\sqrt{n}}$$

$$\leq \lambda^{J} \sqrt{N} (M+R) + \sum_{k=0}^{J-1} \lambda^{k} \frac{\sqrt{N} \max_{j=1,\dots,N} C_{j}^{\infty}}{\sqrt{n}}.$$
(28)

Letting  $J \to \infty$ , we thus arrive at the bound (24).

#### <span id="page-19-0"></span>2.4 Universality

In the previous section, we proved error bounds for the approximation using recurrent QNNs of the filters induced by contractive state-space targets with Barron-type integrability conditions. These bounds show, in passing, the universality of the family of RQNN filters in that category. We now extend this universality statement (without formulating error bounds) to the much larger family of fading memory filters by introducing a modification in the RQNN reservoir. We define  $\tilde{F}_R^{n,\theta}: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}^N$  by its component maps  $\tilde{F}_{R,j}^{n,\theta} = (\tilde{F}_{R,1}^{n,\theta}, \dots, \tilde{F}_{R,N}^{n,\theta})$ . For  $j = 1, \dots, N$ , the j-th component map  $\tilde{F}_{R,j}^{n,\theta}: \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$  is defined by

$$\tilde{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) := R - 2R[\mathbb{P}_{1}^{n,\boldsymbol{\theta}^{j}}(P_{j}\boldsymbol{x},\boldsymbol{z}) + \mathbb{P}_{2}^{n,\boldsymbol{\theta}^{j}}(P_{j}\boldsymbol{x},\boldsymbol{z})], \quad (\boldsymbol{x},\boldsymbol{z}) \in \mathbb{R}^{N} \times \mathbb{R}^{d},$$
 (29)

with  $\boldsymbol{\theta} = (\boldsymbol{\theta}^1, \dots, \boldsymbol{\theta}^N) \in \boldsymbol{\Theta}^N$  and  $P_1, \dots, P_N \in \mathbb{R}^{N \times N}$  linear preprocessing maps. Our modified recurrent quantum neural network is then defined by the state-space system associated to the state map  $\tilde{F}_R^{n,\boldsymbol{\theta}}$ 

<span id="page-19-3"></span>
$$\hat{\boldsymbol{x}}_t = \tilde{F}_R^{n,\boldsymbol{\theta}}(\hat{\boldsymbol{x}}_{t-1}, \boldsymbol{z}_t), \quad t \in \mathbb{Z}_-. \tag{30}$$

The next Lemma shows that adding linear preprocessing maps to reservoir equations can lead to the echo state property without contraction assumptions. This approach was first introduced in [GO20] and subsequently used, e.g., in [GGO23, GO21].

<span id="page-19-2"></span>**Lemma 2.8.** Let  $\tilde{F} = (\tilde{F}_1, \dots, \tilde{F}_N)$  be a reservoir map where each component  $\tilde{F}_j : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$ , for  $j = 1, \dots, N$ , is defined as

<span id="page-19-1"></span>
$$\tilde{F}_j(\boldsymbol{x}, \boldsymbol{z}) = g_j(P_j \boldsymbol{x}, \boldsymbol{z}) \tag{31}$$

where  $P_1, \ldots, P_N \in \mathbb{R}^{N \times N}$  are linear preprocessing maps for any maps  $g_j : \mathbb{R}^N \times \mathbb{R}^d \to \mathbb{R}$ ,  $j = 1, \ldots, N$ . Define an arbitrary partition of the state vector  $\hat{\boldsymbol{x}}_t = [\hat{\boldsymbol{x}}_t^{(1)}, \ldots, \hat{\boldsymbol{x}}_t^{(K)}] \in \mathbb{R}^{I_1} \times \cdots \times \mathbb{R}^{I_K}$  such that  $\sum_{k=1}^K I_k = N > 0$  and  $I_k \geq 1$  for all  $t \in \mathbb{Z}_-$ . We define the index  $l_k = \sum_{s=1}^k I_s$  for  $k = 1, \ldots, K$ . For  $k = 1, j \in \{1, \ldots, l_1\}$ , and  $k = 2, \ldots, K - 1$ ,  $j \in \{l_{k-1} + 1, \ldots, l_k\}$ , select  $P_j$  as the matrix with zero entries, except for  $(P_j)_{l,l+l_k} = 1$  for  $l = 1, \ldots, \sum_{s=k+1}^K I_s$  and let  $P_j = 0$  for  $j = l_{K-1} + 1, \ldots, N$ . Then, the map  $\tilde{F}$  has the echo state property for any  $N \in \mathbb{N}^+$ .

Proof. We start by constructing a partition of  $\hat{x}_t$  as in the statement. If N=1, we simply have  $\hat{x}_t = [\hat{x}_t] \in \mathbb{R}$ . Next, we define the reservoir vector  $\tilde{F}_{R,i:j} = (\tilde{F}_i, \dots, \tilde{F}_j)$ . Then, for  $k=1, j \in \{1,\dots,l_1\}$ , and  $k=2,\dots,K-1, j \in \{l_{k-1}+1,\dots,l_k\}$ , we have  $P_j\hat{x}_t = [\hat{x}_t^{(k+1)},\dots,\hat{x}_t^{(K)},0,\dots,0]$  and  $P_j\hat{x}_t = 0$  for  $j=l_{K-1}+1,\dots,N$ . Inserting these choices into (31), we may rewrite the dynamics as

<span id="page-20-1"></span>
$$\hat{\boldsymbol{x}}_{t}^{(k)} = \tilde{F}_{l_{k-1}+1:l_{k}}([\hat{\boldsymbol{x}}_{t-1}^{(k+1)}, \dots, \hat{\boldsymbol{x}}_{t-1}^{(K)}, 0, \dots, 0], \boldsymbol{z}_{t}), \quad t \in \mathbb{Z}_{-},$$
(32)

for  $k=1,\ldots,K-1$  and  $\hat{\boldsymbol{x}}_t^{(K)}=\tilde{F}_{l_{K-1}+1:l_K}(0,\boldsymbol{z}_t)$ . In particular,  $\hat{\boldsymbol{x}}_t^{(K)}=\tilde{F}_{l_{K-1}+1:l_K}(0,\boldsymbol{z}_t)$ , which depends only on  $\boldsymbol{z}_t$ , is explicitly given for all  $t\in\mathbb{Z}_-$ , and for all  $k=1,\ldots,K-1$ , we see that  $\hat{\boldsymbol{x}}_t^{(k)}$  only depends on  $\hat{\boldsymbol{x}}_{t-1}^{(k+1)},\ldots,\hat{\boldsymbol{x}}_{t-1}^{(K)}$ . Thus, (31) admits a unique solution which can be explicitly obtained from the recursion (32), that is, for all  $t\in\mathbb{Z}_-$ , we have  $\hat{\boldsymbol{x}}_t^{(K)}=\tilde{F}_{l_{K-1}+1:l_K}(0,\boldsymbol{z}_t),\ \hat{\boldsymbol{x}}_t^{(K-1)}=\tilde{F}_{l_{K-2}+1:l_{K-1}}([\hat{\boldsymbol{x}}_{t-1}^{(K)},0,\ldots,0],\boldsymbol{z}_t),\ldots,\hat{\boldsymbol{x}}_t^{(1)}=\tilde{F}_{1:l_1}([\hat{\boldsymbol{x}}_{t-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{t-1}^{(K)},0],\boldsymbol{z}_t)$ . This proves that  $\tilde{F}$  has the echo state property.

Notice that Lemma 2.8 provides the echo state property by imposing a finite memory of K-1 time steps on the reservoir. Let  $D_d \subset \mathbb{R}^d$ ,  $B_m \subset \mathbb{R}^m$  be compact. For a readout  $W \in \mathbb{R}^{m \times N}$ , denote

<span id="page-20-2"></span>
$$\mathbf{y}_t = W \mathbf{x}_t \tag{33}$$

the output process associated to the recurrent QNNs (4) and (30).

<span id="page-20-0"></span>**Theorem 2.9.** Let  $U: (D_d)^{\mathbb{Z}_-} \to (B_m)^{\mathbb{Z}_-}$  be a causal and time-invariant filter that satisfies the fading memory property (that is, it is continuous with respect to the product topology). Then, for any  $\varepsilon > 0$  there exist  $n, N \in \mathbb{N}$ , preprocessing matrices  $P_1, \ldots, P_N \in \mathbb{R}^{N \times N}$ , a readout  $W \in \mathbb{R}^{m \times N}$ , and circuit parameters  $\boldsymbol{\theta} \in \boldsymbol{\Theta}^N$  such that the RQNN (30) has the echo state property and the filter  $\bar{U}_W: (D_d)^{\mathbb{Z}_-} \to (B_m)^{\mathbb{Z}_-}$  associated to the output process (33) satisfies

<span id="page-20-3"></span>
$$\sup_{\boldsymbol{z} \in (D_d)^{\mathbb{Z}_-}} \sup_{t \in \mathbb{Z}_-} \| U(\boldsymbol{z})_t - \bar{U}_W(\boldsymbol{z})_t \| \le \varepsilon.$$
 (34)

*Proof.* Without loss of generality we may assume  $\varepsilon \leq 1$ , because proving (34) for  $\varepsilon \leq 1$  also implies that (34) holds for  $\varepsilon > 1$ .

Let  $H_U: (D_d)^{\mathbb{Z}_-} \to (B_m)^{\mathbb{Z}_-}$  be the functional associated to the filter U. Then, as in the proof of [GO21, Theorem 2.1], there exists  $K \in \mathbb{N}$  and a continuous function  $\bar{G}: (D_d)^{dK} \to B_m$  such that

<span id="page-20-4"></span>
$$\sup_{\boldsymbol{z}\in(D_d)^{\mathbb{Z}_-}} \|H_U(\boldsymbol{z}) - \bar{G}(\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_0)\| < \frac{\varepsilon}{4}. \tag{35}$$

Moreover, e.g., by the argument in [GJ25, Corollary 4], there exists a function  $G \in C_c^{\infty}((\mathbb{R}^d)^K, B_m)$  which satisfies

<span id="page-20-5"></span>
$$\sup_{\boldsymbol{z} \in (\mathbb{R}^d)^K} \|G(\boldsymbol{z}) - \bar{G}(\boldsymbol{z})\| < \frac{\varepsilon}{4}. \tag{36}$$

Next, choose N = (K-1)d+m and consider the recurrent QNN introduced in (4). Denote

$$\bar{F}_{R,j}^{n,\boldsymbol{\theta}}(\boldsymbol{x},\boldsymbol{z}) = R - 2R[\mathbb{P}_1^{n,\boldsymbol{\theta}^j}(\boldsymbol{x},\boldsymbol{z}) + \mathbb{P}_2^{n,\boldsymbol{\theta}^j}(\boldsymbol{x},\boldsymbol{z})], \quad (\boldsymbol{x},\boldsymbol{z}) \in \mathbb{R}^N \times \mathbb{R}^d$$
(37)

the update maps without preprocessing matrices. For  $1 \leq i \leq j \leq N$ , write  $\bar{F}_{R,i:j}^{n,\theta} = (\bar{F}_{R,i}^{n,\theta}, \dots, \bar{F}_{R,j}^{n,\theta})$  and  $l_k = m + (k-1)d$  for  $k = 1, \dots, K$ . Define the constants

$$L_G = \max(\sqrt{d}, \sup_{\boldsymbol{z} \in (\mathbb{R}^d)^K} \|\nabla G(\boldsymbol{z})\|) + 1, \qquad C_G = 4L_G \left(\sum_{k=2}^K \sum_{j=1}^{K-k+1} (2L_G)^j\right)^{1/2}.$$
(38)

Then, as  $G \in C_c^{\infty}((\mathbb{R}^d)^K)$  and the identity is smooth, Corollary 2.6 (applied componentwise) guarantees that there exist  $n_K$ ,  $R_K$  and  $\boldsymbol{\theta}_K \in \boldsymbol{\Theta}^d$  such that

<span id="page-21-0"></span>
$$\sup_{z \in D_d} \|\bar{F}_{R_K, l_{K-1}+1:l_K}^{n_K, \theta_K}(0, z) - z\| + \sup_{z \in D_d} \|\nabla \bar{F}_{R_K, l_{K-1}+1:l_K}^{n_K, \theta_K}(0, z) - \mathbf{1}_d\| < \frac{\varepsilon}{C_G},$$
(39)

and (recursively), for all k = K - 1, ..., 2 there exist  $n_k$ ,  $R_k$  and  $\boldsymbol{\theta}_k \in \boldsymbol{\Theta}^d$  such that

$$\sup_{(\boldsymbol{x},\boldsymbol{z})\in[-R_{k+1},R_{k+1}]^N\times D_d} \|\bar{F}_{R_k,l_{k-1}+1:l_k}^{n_k,\boldsymbol{\theta}_k}(\boldsymbol{x},\boldsymbol{z}) - \boldsymbol{x}_{1:d}\| + \|\nabla\bar{F}_{R_k,l_{k-1}+1:l_k}^{n_k,\boldsymbol{\theta}_k}(\boldsymbol{x},\boldsymbol{z}) - \boldsymbol{1}_d\| < \frac{\varepsilon}{C_G}, \tag{40}$$

and there exist  $n_1$ ,  $R_1$  and  $\boldsymbol{\theta}_1 \in \boldsymbol{\Theta}^d$  such that

<span id="page-21-1"></span>
$$\sup_{([\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_{-1}],\boldsymbol{z}_{0})\in[-R_{2},R_{2}]^{N}\times D_{d}}\left(\|\bar{F}_{R_{1},1:m}^{n_{1},\boldsymbol{\theta}_{1}}([\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_{-1},0],\boldsymbol{z}_{0})-G(\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_{0})\|\right) + \|\nabla\bar{F}_{R_{1},1:m}^{n_{1},\boldsymbol{\theta}_{1}}([\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_{-1},0],\boldsymbol{z}_{0})-\nabla G(\boldsymbol{z}_{-K+1},\dots,\boldsymbol{z}_{0})\|\right) < \frac{\varepsilon}{4}.$$

$$(41)$$

Without loss of generality we may choose  $R = R_1 = \ldots = R_K$ , since we can always replace  $R_k$  by  $\max(R_k, R_{k+1})$  (and hence ultimately replace  $R_1, \ldots, R_K$  by R) and absorb the change in an adjusted choice of parameters  $\gamma^{i,j}$  (see representation (7)). Moreover, by a similar reasoning we may assume without loss of generality that  $n = n_1 = \ldots = n_K$ . Indeed, otherwise we may again choose n to be the maximum of  $n_1, \ldots, n_K$ , replace  $n_1, \ldots, n_K$  by n and recover the same functions (7) by setting surplus terms  $i > n_k$  to 0 by appropriate choice of  $\gamma^{i,j}$ . The extra factor  $\frac{n}{n_k}$ , in turn, can be absorbed by modifying the choice of R.

Denote by  $L_k$  be the best Lipschitz constant for  $\bar{F}_{R,l_{k-1}+1:l_k}^{n,\boldsymbol{\theta}_k}$ . Then (39)–(41) imply that  $L_k \leq \sqrt{d} + \varepsilon \leq L_G$  for  $k = K, \ldots, 2$  and  $L_1 \leq \sup_{\boldsymbol{z} \in \mathbb{R}^d)^K} \|\nabla G(\boldsymbol{z})\| + 1 \leq L_G$ . In particular,  $L_G \geq \max(L_1, \ldots, L_K)$  is a bound on the Lipschitz constant for all QNNs  $\bar{F}_{R,l_{k-1}+1:l_k}^{n,\boldsymbol{\theta}_k}$  and G. Partition  $\hat{\boldsymbol{x}}_t = [\hat{\boldsymbol{x}}_t^{(1)}, \ldots, \hat{\boldsymbol{x}}_t^{(K)}] \in \mathbb{R}^m \times (\mathbb{R}^d)^{K-1}$ . Using the triangle inequality, we then

obtain

<span id="page-22-0"></span>
$$\sup_{\boldsymbol{z}\in(D_{d})^{K+1}} \left\| G(\boldsymbol{z}_{-K+1},\ldots,\boldsymbol{z}_{0}) - \hat{\boldsymbol{x}}_{0}^{(1)} \right\| \\
= \sup_{\boldsymbol{z}\in(D_{d})^{(K+1)}} \left\| G(\boldsymbol{z}_{-K+1},\ldots,\boldsymbol{z}_{0}) - \bar{F}_{R,1:m}^{n,\boldsymbol{\theta}}([\hat{\boldsymbol{x}}_{-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{-1}^{(K)},0],\boldsymbol{z}_{0}) \right\| \\
\leq \left\| G(\boldsymbol{z}_{-K+1},\ldots,\boldsymbol{z}_{0}) - G([\hat{\boldsymbol{x}}_{-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{-1}^{(K)}],\boldsymbol{z}_{0}) \right\| \\
+ \left\| G([\hat{\boldsymbol{x}}_{-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{-1}^{(K)}],\boldsymbol{z}_{0}) - \bar{F}_{R,1:m}^{n,\boldsymbol{\theta}}([\hat{\boldsymbol{x}}_{-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{-1}^{(K)},0],\boldsymbol{z}_{0}) \right\| \\
\leq L_{G} \left\| (\boldsymbol{z}_{-K+1},\ldots,\boldsymbol{z}_{0}) - ([\hat{\boldsymbol{x}}_{-1}^{(2)},\ldots,\hat{\boldsymbol{x}}_{-1}^{(K)}],\boldsymbol{z}_{0}) \right\| + \frac{\varepsilon}{4}. \tag{42}$$

For the last norm, we write

$$\left\| (\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_0) - ([\hat{\boldsymbol{x}}_{-1}^{(2)}, \dots, \hat{\boldsymbol{x}}_{-1}^{(K)}], \boldsymbol{z}_0) \right\|^2 = \sum_{k=0}^{K-2} \left\| \boldsymbol{z}_{-k-1} - \hat{\boldsymbol{x}}_{-1}^{(K-k)} \right\|^2 = \sum_{k=2}^{K} \left\| \boldsymbol{z}_{-K+k-1} - \hat{\boldsymbol{x}}_{-1}^{(k)} \right\|^2.$$

We proceed by backward induction over k to prove that for all  $k = K, \dots, 2$  it holds

$$\left\| oldsymbol{z}_{-K+k+t} - \hat{oldsymbol{x}}_t^{(k)} 
ight\|^2 \le \sum_{j=1}^{K-k+1} (2L_G)^j rac{arepsilon^2}{C_G^2},$$

for arbitrary  $t \in \mathbb{Z}_{-}$ . Indeed, we have

$$\left\| \boldsymbol{z}_{-K+k+t} - \hat{\boldsymbol{x}}_t^{(k)} \right\|^2 = \left\| \boldsymbol{z}_{-K+k+t} - \bar{F}_{R,l_{k-1}+1:l_k}^{n,\boldsymbol{\theta}}([\hat{\boldsymbol{x}}_{t-1}^{(k+1)},\dots,\hat{\boldsymbol{x}}_{t-1}^{(K)},0,\dots,0],\boldsymbol{z}_t) \right\|^2$$

and so for k = K it follows that

$$\left\| \boldsymbol{z}_{-K+k+t} - \hat{\boldsymbol{x}}_{t}^{(k)} \right\|^{2} = \left\| \boldsymbol{z}_{t} - \bar{F}_{R,l_{K-1}+1:l_{K}}^{n,\boldsymbol{\theta}}(0,\boldsymbol{z}_{t}) \right\|^{2} \leq \frac{\varepsilon^{2}}{C_{G}^{2}} \leq 2L_{G} \frac{\varepsilon^{2}}{C_{G}^{2}}$$

Assume that the bound holds for a fixed  $k \in \{K, \dots, 3\}$ , then for k-1 we estimate (with the notation  $f_{k-1} = \bar{F}_{R,l_{k-2}+1:l_{k-1}}^{n,\theta}$ )

$$\begin{aligned} & \left\| \boldsymbol{z}_{-K+(k-1)+t} - \hat{\boldsymbol{x}}_{t}^{(k-1)} \right\|^{2} = \left\| \boldsymbol{z}_{-K+k-2} - f_{k-1}([\hat{\boldsymbol{x}}_{t-1}^{(k)}, \dots, \hat{\boldsymbol{x}}_{t-1}^{(K)}, 0, \dots, 0], \boldsymbol{z}_{t}) \right\|^{2} \\ & \leq 2 \left\| \boldsymbol{z}_{-K+k-2} - f_{k-1}([\boldsymbol{z}_{-K+k-2}, \hat{\boldsymbol{x}}_{t-1}^{(k+1)}, \dots, \hat{\boldsymbol{x}}_{t-1}^{(K)}, 0, \dots, 0], \boldsymbol{z}_{t}) \right\|^{2} \\ & + 2 \left\| f_{k-1}([\boldsymbol{z}_{-K+k+t-1}, \hat{\boldsymbol{x}}_{t-1}^{(k+1)}, \dots, \hat{\boldsymbol{x}}_{t-1}^{(K)}, 0, \dots, 0], \boldsymbol{z}_{t}) - f_{k-1}([\hat{\boldsymbol{x}}_{-2}^{(k)}, \dots, \hat{\boldsymbol{x}}_{t-1}^{(K)}, 0, \dots, 0], \boldsymbol{z}_{t}) \right\|^{2} \\ & \leq 2 \frac{\varepsilon^{2}}{C_{G}^{2}} + 2L \left\| \boldsymbol{z}_{-K+k+t-1} - \hat{\boldsymbol{x}}_{t-1}^{(k)} \right\|^{2} \leq 2 \frac{\varepsilon^{2}}{C_{G}^{2}} + \sum_{j=1}^{K-k} (2L)^{j+1} \frac{\varepsilon^{2}}{C_{G}^{2}} \leq \sum_{j=1}^{K-k+1} (2L)^{j} \frac{\varepsilon^{2}}{C_{G}^{2}}, \end{aligned}$$

which completes the induction. Therefore, we obtain

$$\begin{aligned} & \left\| (\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_0) - ([\hat{\boldsymbol{x}}_{-1}^{(2)}, \dots, \hat{\boldsymbol{x}}_{-1}^{(K)}], \boldsymbol{z}_0) \right\|^2 = \sum_{k=2}^K \left\| \boldsymbol{z}_{-K+k-1} - \hat{\boldsymbol{x}}_{-1}^{(k)} \right\|^2 \\ & \leq \sum_{k=2}^K \left\| \boldsymbol{z}_{-K+k-1} - \hat{\boldsymbol{x}}_{-1}^{(k)} \right\|^2 \leq \frac{\varepsilon^2}{C_G^2} \sum_{k=2}^K \sum_{j=1}^{K-k+1} (2L)^j = \frac{\varepsilon^2}{16L_G^2} \end{aligned}$$

From (42), we thus obtain

<span id="page-23-1"></span>
$$\sup_{\boldsymbol{z} \in (D_d)^{K+1}} \left\| G(\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_0) - \hat{\boldsymbol{x}}_0^{(1)} \right\| \\
\leq L_G \left\| (\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_0) - ([\hat{\boldsymbol{x}}_{-1}^{(2)}, \dots, \hat{\boldsymbol{x}}_{-1}^{(K)}], \boldsymbol{z}_0) \right\| + \frac{\varepsilon}{4} \leq \frac{\varepsilon}{2}. \tag{43}$$

Setting W to be the projection onto the first block  $\hat{x}_0^{(1)}$ , (that is, W has zero entries except for  $W_{i,i} = 1$  for i = 1, ..., m) and putting together (35), (36) and (43) yields

<span id="page-23-2"></span>
$$\sup_{\boldsymbol{z}\in(D_{d})^{\mathbb{Z}_{-}}} \sup_{t\in\mathbb{Z}_{-}} \|H_{U}(\boldsymbol{z}) - H_{\bar{U}_{W}}(\boldsymbol{z})\| \leq \sup_{\boldsymbol{z}\in(D_{d})^{\mathbb{Z}_{-}}} \|H_{U}(\boldsymbol{z}) - \bar{G}(\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_{0})\| 
+ \sup_{\boldsymbol{z}\in(\mathbb{R}^{d})^{K}} \|G(\boldsymbol{z}) - \bar{G}(\boldsymbol{z})\| + \sup_{\boldsymbol{z}\in(D_{d})^{K+1}} \|G(\boldsymbol{z}_{-K+1}, \dots, \boldsymbol{z}_{0}) - H_{\bar{U}_{W}}(\boldsymbol{z})\| 
\leq \frac{\varepsilon}{4} + \frac{\varepsilon}{4} + \frac{\varepsilon}{2} = \varepsilon.$$
(44)

It remains to be shown that (30) has the echo state property. Recall that we partition  $\hat{x}_t = [\hat{x}_t^{(1)}, \dots, \hat{x}_t^{(K)}] \in \mathbb{R}^m \times (\mathbb{R}^d)^{K-1}$ . For  $k = 1, j \in \{1, \dots, l_1\}$ , and  $k = 2, \dots, K-1$ ,  $j \in \{l_{k-1}+1, \dots, l_k\}$ , select  $P_j$  as the matrix with zero entries, except for  $(P_j)_{l,l+l_k} = 1$  for  $l = 1, \dots, d(K-k)$  and let  $P_j = 0$  for  $j = l_{K-1}+1, \dots, N$ . Then, for  $k = 1, j \in \{1, \dots, l_1\}$ , and  $k = 2, \dots, K-1, j \in \{l_{k-1}+1, \dots, l_k\}$ , we have  $P_j \hat{x}_t = [\hat{x}_t^{(k+1)}, \dots, \hat{x}_t^{(K)}, 0, \dots, 0]$  and  $P_j \hat{x}_t = 0$  for  $j = l_{K-1}+1, \dots, N$ . Then, echo state property follows by calling Lemma 2.8. Therefore, the approximation bound for the functional (44) immediately implies the corresponding bound for the filter (34), which completes the proof of the theorem.

### <span id="page-23-0"></span>3 Conclusions

Approximation bounds and universality properties are part of the theoretical cornerstone of machine learning models. While some studies have addressed the question of universality for QRC models, the combination of the two had not previously been explored in the context of recurrent QNNs. In this paper, we derived approximation bounds and universality

statements for recurrent QNNs based on the circuit implementation presented in [\[GJ25\]](#page-26-6), which is compatible with hardware deployment and whose implementation with Rydberg atoms has been already discussed in [\[APB](#page-25-10)+24]. This circuit uses a uniformly controlled quantum gate to apply multi-controlled rotations to a set of control and target qubits, and it has been recently shown that it can be efficiently implemented [\[ZB24,](#page-30-1) [SAAdS24,](#page-29-8) [ZB25\]](#page-30-2).

To extend the results of [\[GJ25\]](#page-26-6) to the recurrent case, we first derived approximation bounds for the static version of the QNN and its derivatives. This yields uniform approximation bounds of state-maps that satisfy a Barron-type condition (Proposition [2.5\)](#page-13-0) and a universality statement (Corollary [2.6\)](#page-15-0) for continuously differentiable state-equations. These results are used in Proposition [2.7](#page-17-1) to provide filter approximation bounds that show that RQNNs are able to uniformly approximate the filters induced by any contracting Barron-type state-space system. Finally, Theorem [2.9](#page-20-0) extends this universality property to the much larger category of arbitrary fading memory, causal, and time-invariant filters. In this last result, neither Barron-type integrability nor contractivity conditions are needed for the target filter. Instead, we modify the approximating recurrent QNN with preprocessing matrices to ensure the echo state property. Note that all these results apply, strictly speaking, exclusively to variational systems for which all parameters are trained and are only tentative for quantum reservoir systems in which some parameters in the recurrent layer are randomly generated. While the variational approach seeks the optimal parameters for the quantum circuit and output layer, the reservoir approach is simpler, usually involving random sampling of the circuit parameters and tuning of only the output layer. Which strategy is best in terms of speed and accuracy will depend on the number of blocks n of the circuit, the intrinsic noise of the hardware, and the target task. Future research will focus on implementing and comparing the variational and reservoir approaches.

This work paves the way for extending the theoretical analysis of QRC models beyond the SAS paradigm [\[MPO23\]](#page-28-5). It is important to understand in which situations the feedback approach is preferable to other protocols. Questions such as the exponential concentration of observables [\[SGZ25,](#page-29-9) [XHA](#page-30-4)+25] and the suitability of QRC models for learning quantum temporal tasks [\[TN21,](#page-29-10) [Nok23\]](#page-28-11) are fundamental to discerning the conditions that render QRC models more useful than classical machine learning approaches.

Acknowledgments. The authors acknowledge partial financial support from the School of Physical and Mathematical Sciences of the Nanyang Technological University through the SPMS Collaborative Research Award 2023 entitled "Quantum Reservoir Systems for Machine Learning". RMP acknowledges the QCDI project funded by the Spanish Government. JPO wishes to thank the hospitality of the Donostia International Physics Center and LG and RMP that of the Division of Mathematical Sciences of the Nanyang Technological University, during the academic visits in which some of this work was developed.

## References

- <span id="page-25-6"></span>[AAdS+23] Israel F Araujo, Ismael C Ara´ujo, Leon D da Silva, Carsten Blank, and Adenilton J da Silva, Quantum computing library, [https://github.com/](https://github.com/qclib/qclib) [qclib/qclib](https://github.com/qclib/qclib).
- <span id="page-25-5"></span>[ADMQ+22] Juan Miguel Arrazola, Olivia Di Matteo, Nicol´as Quesada, Soran Jahangiri, Alain Delgado, and Nathan Killoran, Universal quantum circuits for quantum chemistry, Quantum 6 (2022), 742.
- <span id="page-25-10"></span>[APB+24] Ishita Agarwal, Taylor L Patti, Rodrigo Araiza Bravo, Susanne F Yelin, and Anima Anandkumar, Extending quantum perceptrons: Rydberg devices, multi-class classification, and error tolerance, arXiv preprint arXiv:2411.09093 (2024).
- <span id="page-25-0"></span>[ATM25] Osama Ahmed, Felix Tennie, and Luca Magri, Optimal training of finitely sampled quantum reservoir computers for forecasting of chaotic dynamics, Quantum Machine Intelligence 7 (2025), no. 1, 1–16.
- <span id="page-25-7"></span>[Bar92] Andrew R. Barron, Neural net approximation, Yale Workshop on Adaptive and Learning Systems, vol. 1, 1992, pp. 69–72.
- <span id="page-25-8"></span>[Bar93] , Universal approximation bounds for superpositions of a sigmoidal function, IEEE Trans. Inform. Theory 39 (1993), no. 3, 930–945.
- <span id="page-25-3"></span>[BC85] S. Boyd and L. Chua, Fading memory and the problem of approximating nonlinear operators with Volterra series, IEEE Transactions on Circuits and Systems 32 (1985), no. 11, 1150–1161.
- <span id="page-25-9"></span>[BK18] Andrew R. Barron and Jason M. Klusowski, Approximation and estimation for high-dimensional deep learning networks, Preprint, arXiv 1809.03090 (2018).
- <span id="page-25-1"></span>[BNGY22] Rodrigo Araiza Bravo, Khadijeh Najafi, Xun Gao, and Susanne F Yelin, Quantum reservoir computing using arrays of rydberg atoms, PRX Quantum 3 (2022), no. 3, 030325.
- <span id="page-25-4"></span>[BVMS05] Ville Bergholm, Juha J Vartiainen, Mikko M¨ott¨onen, and Martti M Salomaa, Quantum circuits with uniformly controlled one-qubit gates, Physical Review A—Atomic, Molecular, and Optical Physics 71 (2005), no. 5, 052330.
- <span id="page-25-2"></span>[CAM25] Naomi Mona Chmielewski, Nina Amini, and Joseph Mikael, Quantum reservoir computing and risk bounds, arXiv preprint arXiv:2501.08640 (2025).

- <span id="page-26-3"></span>[CDLJ24] ˇ Saud Cindrak, Brecht Donvil, Kathy L¨udge, and Lina Jaurigue, ˇ Enhancing the performance of quantum reservoir computing and solving the timecomplexity problem by artificial memory restriction, Physical Review Research 6 (2024), no. 1, 013051.
- <span id="page-26-5"></span>[CN19] Jiayin Chen and Hendra I Nurdin, Learning nonlinear input–output maps with dissipative quantum systems, Quantum Information Processing 18 (2019), 1–36.
- <span id="page-26-1"></span>[CNY20] Jiayin Chen, Hendra I Nurdin, and Naoki Yamamoto, Temporal information processing on noisy quantum computers, Physical Review Applied 14 (2020), no. 2, 024065.
- <span id="page-26-0"></span>[DHB22] Samudra Dasgupta, Kathleen E Hamilton, and Arnab Banerjee, Characterizing the memory capacity of transmon qubit reservoirs, 2022 IEEE International Conference on Quantum Computing and Engineering (QCE), IEEE, 2022, pp. 162–166.
- <span id="page-26-4"></span>[FPL+24] Giacomo Franceschetto, Marcin P lodzie´n, Maciej Lewenstein, Antonio Ac´ın, and Pere Mujal, Harnessing quantum back-action for time-series processing, arXiv preprint arXiv:2411.03979 (2024).
- <span id="page-26-2"></span>[GBGSZ23] Jorge Garc´ıa-Beni, Gian Luca Giorgi, Miguel C Soriano, and Roberta Zambrini, Scalable photonic platform for real-time quantum reservoir computing, Physical Review Applied 20 (2023), no. 1, 014051.
- <span id="page-26-11"></span>[GGO20] Lukas Gonon, Lyudmila Grigoryeva, and Juan-Pablo Ortega, Risk bounds for reservoir computing, J. Mach. Learn. Res. 21 (2020), Paper No. 240, 61.
- <span id="page-26-10"></span>[GGO23] , Approximation bounds for random neural networks and reservoir systems, Ann. Appl. Probab. 33 (2023), no. 1, 28–69.
- <span id="page-26-6"></span>[GJ25] Lukas Gonon and Antoine Jacquier, Universal approximation theorem and error bounds for quantum neural networks and quantum reservoirs, Preprint, arXiv 2307.12904; to appear in IEEE TNNLS (2025).
- <span id="page-26-8"></span>[GO18a] Lyudmila Grigoryeva and Juan-Pablo Ortega, Echo state networks are universal, Neural Networks 108 (2018), 495–508.
- <span id="page-26-7"></span>[GO18b] , Universal discrete-time reservoir computers with stochastic inputs and linear readouts using non-homogeneous state-affine systems, Journal of Machine Learning Research 19 (2018), no. 24, 1–40.
- <span id="page-26-9"></span>[GO20] Lukas Gonon and Juan-Pablo Ortega, Reservoir computing universality with stochastic inputs, IEEE Trans. Neural Netw. Learn. Syst. 31 (2020), no. 1, 100–112.

- <span id="page-27-6"></span>[GO21] , Fading memory echo state networks are universal, Neural Netw. 138 (2021), 10–13.
- <span id="page-27-10"></span>[Gon23] Lukas Gonon, Random feature neural networks learn black-scholes type pdes without curse of dimensionality, J. Mach. Learn. Res. 24 (2023), no. 189, 1–51.
- <span id="page-27-8"></span>[Gon24] , Deep neural network expressivity for optimal stopping problems, Finance and Stochastics 28 (2024), 865–910.
- <span id="page-27-3"></span>[HKB+24] Fangjun Hu, Saeed A Khan, Nicholas T Bronn, Gerasimos Angelatos, Graham E Rowlands, Guilhem J Ribeill, and Hakan E T¨ureci, Overcoming the coherence time barrier in quantum machine learning on temporal data, Nature Communications 15 (2024), no. 1, 7491.
- <span id="page-27-11"></span>[H¨or90] Lars H¨ormander, The analysis of linear partial differential operators i, second edition ed., Springer, 1990.
- <span id="page-27-5"></span>[KFY24] Kaito Kobayashi, Keisuke Fujii, and Naoki Yamamoto, Feedback-driven quantum reservoir computing for time-series analysis, PRX Quantum 5 (2024), no. 4, 040325.
- <span id="page-27-4"></span>[KHZ+24] Milan Kornjaˇca, Hong-Ye Hu, Chen Zhao, Jonathan Wurtz, Phillip Weinberg, Majd Hamdan, Andrii Zhdanov, Sergio H Cantu, Hengyun Zhou, Rodrigo Araiza Bravo, et al., Large-scale quantum reservoir learning with an analog quantum computer, arXiv preprint arXiv:2407.02553 (2024).
- <span id="page-27-1"></span>[KSK+23] Tomoyuki Kubota, Yudai Suzuki, Shumpei Kobayashi, Quoc Hoan Tran, Naoki Yamamoto, and Kohei Nakajima, Temporal information processing induced by quantum noise, Physical Review Research 5 (2023), no. 2, 023057.
- <span id="page-27-9"></span>[LT13] Michel Ledoux and Michel Talagrand, Probability in Banach Spaces, Springer Berlin Heidelberg, 2013.
- <span id="page-27-7"></span>[Man20] G Manjunath, Stability and memory-loss go hand-in-hand: three results in dynamics \& computation, Proceedings of the Royal Society London Ser. A Math. Phys. Eng. Sci. 476 (2020), no. 2242, 1–25.
- <span id="page-27-0"></span>[MCLCL23] Zoubeir Mlika, Soumaya Cherkaoui, Jean Fr´ed´eric Laprade, and Simon Corbeil-Letourneau, User trajectory prediction in mobile wireless networks using quantum reservoir computing, IET Quantum Communication 4 (2023), no. 3, 125–135.
- <span id="page-27-2"></span>[MDP23] Riccardo Molteni, Claudio Destri, and Enrico Prati, Optimization of the memory reset rate of a quantum echo-state network for time sequential tasks, Physics Letters A (2023), 128713.

- <span id="page-28-4"></span>[MKTG25] Jakob Murauer, Rajiv Krishnakumar, Sabine Tornow, and Michaela Geierhos, Feedback connections in quantum reservoir computing with mid-circuit measurements, arXiv preprint arXiv:2503.22380 (2025).
- <span id="page-28-2"></span>[MMPG+23] Pere Mujal, Rodrigo Mart´ınez-Pe˜na, Gian Luca Giorgi, Miguel C Soriano, and Roberta Zambrini, Time-series quantum reservoir computing with weak and projective measurements, npj Quantum Information 9 (2023), no. 1, 16.
- <span id="page-28-0"></span>[MMPN+21] Pere Mujal, Rodrigo Mart´ınez-Pe˜na, Johannes Nokkala, Jorge Garc´ıa-Beni, Gian Luca Giorgi, Miguel C Soriano, and Roberta Zambrini, Opportunities in quantum reservoir computing and extreme learning machines, Advanced Quantum Technologies 4 (2021), no. 8, 2100027.
- <span id="page-28-5"></span>[MPO23] Rodrigo Mart´ınez-Pe˜na and Juan-Pablo Ortega, Quantum reservoir computing in finite dimensions, Physical Review E 107 (2023), no. 3, 035306.
- <span id="page-28-3"></span>[MSH25] Tomoya Monomi, Wataru Setoyama, and Yoshihiko Hasegawa, Feedbackenhanced quantum reservoir computing with weak measurements, arXiv preprint arXiv:2503.17939 (2025).
- <span id="page-28-9"></span>[MVBS04a] Mikko M¨ott¨onen, Juha J Vartiainen, Ville Bergholm, and Martti M Salomaa, Quantum circuits for general multiqubit gates, Physical review letters 93 (2004), no. 13, 130502.
- <span id="page-28-10"></span>[MVBS04b] Mikko Mottonen, Juha J Vartiainen, Ville Bergholm, and Martti M Salomaa, Transformation of quantum states using uniformly controlled rotations, arXiv preprint quant-ph/0407010 (2004).
- <span id="page-28-6"></span>[NMPG+21] Johannes Nokkala, Rodrigo Mart´ınez-Pe˜na, Gian Luca Giorgi, Valentina Parigi, Miguel C Soriano, and Roberta Zambrini, Gaussian states of continuousvariable quantum systems provide universal and versatile reservoir computing, Communications Physics 4 (2021), no. 1, 53.
- <span id="page-28-11"></span>[Nok23] Johannes Nokkala, Online quantum time series processing with random oscillator networks, Scientific Reports 13 (2023), no. 1, 7694.
- <span id="page-28-8"></span>[OR25a] Juan-Pablo Ortega and Florian Rossmannek, Echoes of the past: a unified perspective on fading memory and echo states, Preprint (2025).
- <span id="page-28-7"></span>[OR25b] , Stochastic dynamics learning with state-space systems, Preprint (2025).
- <span id="page-28-1"></span>[PHGB+25] Iris Paparelle, Johan Henaff, Jorge Garcia-Beni, Emilie Gillet, Gian Luca Giorgi, Miguel C Soriano, Roberta Zambrini, and Valentina Parigi, Experimental memory control in continuous variable optical quantum reservoir computing, arXiv preprint arXiv:2506.07279 (2025).

- <span id="page-29-1"></span>[PHS22] Philipp Pfeffer, Florian Heyder, and J¨org Schumacher, Hybrid quantumclassical reservoir computing of thermal convection flow, Physical Review Research 4 (2022), no. 3, 033176.
- <span id="page-29-4"></span>[PHS23] , Reduced-order modeling of two-dimensional turbulent rayleighb´enard flow by hybrid quantum-classical reservoir computing, Physical review research 5 (2023), no. 4, 043242.
- <span id="page-29-7"></span>[PPR19] Daniel K Park, Francesco Petruccione, and June-Koo Kevin Rhee, Circuitbased quantum random access memory for classical data, Scientific reports 9 (2019), no. 1, 3949.
- <span id="page-29-8"></span>[SAAdS24] Jefferson DS Silva, Thiago Melo D Azevedo, Israel F Araujo, and Adenilton J da Silva, Linear decomposition of approximate multi-controlled single qubit gates, IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems (2024).
- <span id="page-29-3"></span>[SAS+25] Mirela Selimovi´c, Iris Agresti, Micha l Siemaszko, Joshua Morris, Borivoje Daki´c, Riccardo Albiero, Andrea Crespi, Francesco Ceccarelli, Roberto Osellame, Magdalena Stobi´nska, et al., Experimental neuromorphic computing based on quantum memristor, arXiv preprint arXiv:2504.18694 (2025).
- <span id="page-29-6"></span>[SGLZ24] Antonio Sannia, Gian Luca Giorgi, Stefano Longhi, and Roberta Zambrini, Skin effect in quantum neural networks, arXiv preprint arXiv:2406.14112 (2024).
- <span id="page-29-0"></span>[SGP+22] Yudai Suzuki, Qi Gao, Ken C Pradel, Kenji Yasuoka, and Naoki Yamamoto, Natural quantum reservoir computing for temporal information processing, Scientific reports 12 (2022), no. 1, 1–15.
- <span id="page-29-9"></span>[SGZ25] Antonio Sannia, Gian Luca Giorgi, and Roberta Zambrini, Exponential concentration and symmetries in quantum reservoir computing, arXiv preprint arXiv:2505.10062 (2025).
- <span id="page-29-2"></span>[SMP+22] Michele Spagnolo, Joshua Morris, Simone Piacentini, Michael Antesberger, Francesco Massa, Andrea Crespi, Francesco Ceccarelli, Roberto Osellame, and Philip Walther, Experimental photonic quantum memristor, Nature Photonics 16 (2022), no. 4, 318–323.
- <span id="page-29-5"></span>[SMPS+24] Antonio Sannia, Rodrigo Mart´ınez-Pe˜na, Miguel C Soriano, Gian Luca Giorgi, and Roberta Zambrini, Dissipation as a resource for quantum reservoir computing, Quantum 8 (2024), 1291.
- <span id="page-29-10"></span>[TN21] Quoc Hoan Tran and Kohei Nakajima, Learning temporal quantum tomography, Physical review letters 127 (2021), no. 26, 260401.

- <span id="page-30-3"></span>[Whi34] Hassler Whitney, Analytic extensions of differentiable functions defined in closed sets, Transactions of the American Mathematical Society 36 (1934), no. 1, 63–89.
- <span id="page-30-4"></span>[XHA+25] Weijie Xiong, Zo¨e Holmes, Armando Angrisani, Yudai Suzuki, Thiparat Chotibut, and Supanut Thanasilp, Role of scrambling and noise in temporal information processing with quantum systems, arXiv preprint arXiv:2505.10080 (2025).
- <span id="page-30-0"></span>[YSK+23] Toshiki Yasuda, Yudai Suzuki, Tomoyuki Kubota, Kohei Nakajima, Qi Gao, Wenlong Zhang, Satoshi Shimono, Hendra I Nurdin, and Naoki Yamamoto, Quantum reservoir computing with repeated measurements on superconducting devices, arXiv preprint arXiv:2310.06706 (2023).
- <span id="page-30-1"></span>[ZB24] Ben Zindorf and Sougato Bose, Efficient implementation of multi-controlled quantum gates, arXiv preprint arXiv:2404.02279 (2024).
- <span id="page-30-2"></span>[ZB25] , Multi-controlled quantum gates in linear nearest neighbor, arXiv preprint arXiv:2506.00695 (2025).