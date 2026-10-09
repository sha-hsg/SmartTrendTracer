# QUANTIZATION OF LARGE LANGUAGE MODELS WITH AN OVERDETERMINED BASIS

#### A PREPRINT

# Daniil Merkulov<sup>∗</sup>

Moscow Institute of Physics and Technology, Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia d.merkulov@skoltech.ru

## Alexander Rudikov

Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia a.rudikov@skoltech.ru

#### Ekaterina Muravleva

Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia e.muravleva@skoltech.ru

## Daria Cherniuk\*

Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia daria.cherniuk@skoltech.ru

#### Ivan Oseledets

Artificial Intelligence Research Institute oseledets@airi.net, Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia i.oseledets@skoltech.ru

#### Aleksandr Mikhalev

Center for Artifical Intelligence Technology Skolkovo Institute of Science and Technology Moscow, Russia al.mikhalev@skoltech.ru

# Boris Kashin

Steklov Mathematical Institute of Russian Academy of Sciences Moscow, Russia kashin@mi-ras.ru

# ABSTRACT

In this paper, we introduce an algorithm for data quantization based on the principles of Kashin representation. This approach hinges on decomposing any given vector, matrix, or tensor into two factors. The first factor maintains a small infinity norm, while the second exhibits a similarly constrained norm when multiplied by an orthogonal matrix. Surprisingly, the entries of factors after decomposition are well-concentrated around several peaks, which allows us to efficiently replace them with corresponding centroids for quantization purposes. We study the theoretical properties of the proposed approach and rigorously evaluate our compression algorithm in the context of next-word prediction tasks and on a set of downstream tasks for text classification. Our findings demonstrate that Kashin Quantization achieves competitive or superior quality in model performance while ensuring data compression, marking a significant advancement in the field of data quantization.

*Keywords* Quantization · LLMs · Kashin representation

<sup>∗</sup>Equal contribution

#### 1 Introduction

The realm of data processing and machine learning is increasingly confronting challenges linked to the efficient storage and management of large volumes of data. Traditional methods frequently result in elevated storage costs and computational inefficiencies, particularly when handling modern Large Language Models (LLMs). The availability of open source LLMs, such as OPT Zhang et al. [2022], Llama 1 and 2 Touvron et al. [2023a,b], Falcon Almazrouei et al. [2023] stimulates the need to run them efficiently on local hardware.

In response, we introduce *Kashin Quantization*, a novel approach for data quantization that extends beyond the conventional use of the Kashin representation algorithm. We studied the algorithm for constructing Kashin representations Kashin and Romskii [2023], proposed a fast matrix version of the algorithm, and suggested an approach to use it for the quantization of large models.

The method re-imagines data representation by breaking down any data structure into two key factors. The first factor is optimized for a minimal infinity norm, while the second maintains a small infinity norm when post-multiplied by an orthogonal matrix. This strategy is not merely theoretical; its linear convergence makes it both effective and rapid in practical applications.

Addressing the challenge of working with resource-intensive orthogonal matrices, Kashin Quantization integrates structured matrix types, such as Householder, DCT, and Butterfly matrices. These matrices enable fast matvec operations, boosting memory efficiency and accelerating computation, thereby elevating the overall effectiveness of the algorithm.

A pivotal aspect of Kashin Quantization is its proficiency in concentrating data values around defined peaks (Figure 6), substantially reducing the need for expansive storage. By mapping these values to centroids of two-dimensional distributions (one dimension for each factor), it remarkably reduces data representation size, compressing traditional 32-bit floats to low-bit values. This technique is notably advantageous in large-scale machine learning models, where data size and efficiency are paramount.

Expanding its utility, Kashin Quantization is not only pertinent for quantizing Large Neural Networks but also for compressing exchange information, like gradients in Federated Learning Safaryan et al. [2022] and distributed computations. This extension illustrates the versatility of our approach in diverse machine learning environments.

Furthermore, we enhance Kashin Quantization by incorporating a matrix reformulation of the Kashin algorithm, which substantially accelerates computations. This advancement provides a more efficient methodology for handling large-scale data and complex computations in neural networks.

To validate our approach's efficacy, we apply Kashin Quantization to several common benchmarks in natural language processing. Employing language models like OPT, Bert, RoBerta we demonstrate that our method leads to competitive or superior predictive quality on both next token prediction and text classification tasks while maintaining level of quantization. This balance of efficiency and performance highlights Kashin Quantization's potential to transform data quantization practices in machine learning and allied fields.

This paper makes the following contributions:

- 1. We introduce the Matrix Decomposition Kashin Algorithm. The vanilla algorithm for building Kashin representation requires vectorization of input data and building an orthogonal matrix of possibly huge dimensions. For an  $m \times n$  matrix to decompose, we need a matrix of  $(mn)^2$  elements. Instead, we propose to use a Kronecker-factored matrix, which leads to the memory footprint of  $m^2 + n^2$ . We benchmark the proposed approach and study its limitations.
- 2. We explore the theoretical properties of the convergence rate of the algorithm we proposed. We observed, that the specific choice of basis vectors affects the convergence. We establish the connection between the convergence rate of the Vector Decomposition Kashin Algorithm and the Kolmogorov width, corresponding to the specific choice of basis.
- 3. We propose the Kashin Quantization algorithm for neural network weights quantization, that utilizes the properties of the Kashin representations. We benchmark the proposed approach empirically on the family of OPT models on the next token prediction problem and compare perplexity with the baselines, demonstrating the validity of the proposed approach. Additionally, we conduct experiments on the GLUE benchmark, quantizing Bert and RoBerta models finetuned on several downstream tasks and achieve superior results compared to common quantization methods.

#### 2 Method

Representing the vector in overdetermined basis. Suppose we have a vector  $x \in \mathbb{R}^n$ . Its elements may have different magnitudes (large 'spread') and that can prohibit efficient quantization (i.e., low-bit representation) of the elements. We aim to transform this vector into another vector, which can be represented with fewer number of bits. First, we introduce an overdetermined basis of size 2n: instead of n coefficients, we will represent the vector with m=2n coefficients, but with fewer bits per element. This basis will consist of the original standard basis and the basis given by the columns of the orthogonal matrix Q. In vector notation, this is equivalent to representing x as a sum

<span id="page-2-0"></span>
$$x \approx u + Qv,\tag{1}$$

which admits good low-bit approximation (we will discuss this in detail in Section 4). Fortunately, based on the results in Kashin [1977] and Kashin and Romskii [2023] this representation can be computed efficiently for an arbitrary Q except for the set of small measure:

**Theorem 1** (Kashin and Romskii [2023]). For  $\forall x \in B_2^N = \{x \in \mathbb{R}^N : ||x||_2 \le 1\}$  a greedy algorithm in k steps builds vectors  $u_k$  and  $v_k$  such that

$$||x - u_k - v_k||_2 \le \eta^k$$

$$||u_k||_{\infty} \le \frac{c}{\sqrt{N}}, \quad ||Qv_k||_{\infty} \le \frac{c}{\sqrt{N}}$$

where c > 0 is an absolute constant,  $Q \in O^N$ , where  $O^N$  is a set of orthogonal matrices in  $\mathbb{R}^N$  with Haar measure  $\mu_H$ .

Computing the representation using a greedy approach. Without loss of generality, we assume that the vector x has a unit Euclidean norm  $||x||_2 = 1$  (otherwise it can be scaled). Given x, we can find the closest vector  $\hat{x}$  with elements  $\hat{x}_i \in \{-1, 1\}$  as  $\hat{x}_i = \text{sign}(x_i)$ , note, that  $||\hat{x}||_2 = \sqrt{n}$ . The chosen vector serves as the direction for the first vector u in the relation (1). Which means, that the projection of x onto  $\hat{x}$  is

$$\pi_x(\hat{x}) = \lambda \hat{x} = \|x\|_2 \frac{\langle x, \hat{x} \rangle}{\|x\|_2 \|\hat{x}\|_2} \frac{\hat{x}}{\|\hat{x}\|_2} = \frac{\|x\|_1}{n} \hat{x}.$$

![](_page_2_Figure_11.jpeg)

Figure 1: We select the vector to project on in a greedy manner.

and since three vectors x,  $\lambda \hat{x}$  and  $x - \lambda \hat{x}$  will always form an orthogonal triangle by design the distance is given as

<span id="page-2-1"></span>
$$\|x - \lambda \hat{x}\|_{2}^{2} = \|x\|_{2}^{2} - \frac{\|x\|_{1}^{2}}{n^{2}} \|\hat{x}\|_{2}^{2} = \|x\|_{2}^{2} - \frac{\|x\|_{1}^{2}}{n}.$$
 (2)

The second component Qv from (1) will be formed similarly. Note, that multiplying the vector v with  $\pm 1$  components by matrix Q is equivalent to the rotation of the whole space with the matrix Q, which is also the same as the backward rotation of all vectors except v with the matrix  $Q^T$ . Indeed, from (1)  $Q^Tx \approx Q^Tu + v$ . Thus, the closest vector to x of the form Qv with  $v_i \in \{-1,1\}$  is given as

$$\hat{x} = \lambda Q \operatorname{sign}(Q^T x),$$

#### Algorithm 1 Vector Decomposition Kashin Algorithm

```
Input: Vector x \in \mathbb{R}^n, Orthogonal matrix Q, Tolerance \varepsilon > 0
Output: Vectors u, \hat{v} \in \mathbb{R}^n such that x \approx u + \hat{v} = u + Qv, and both u and v have small infinity norm. Initialize u \leftarrow 0^n, \hat{v} \leftarrow 0^n
Define projection \pi_x(y) \coloneqq \frac{x^\top y}{\|y\|_2^2} \cdot y
while \|x - u - \hat{v}\| \ge \varepsilon do\nif \|x\|_1 > \|Q^T x\|_1 then
\pi \leftarrow \pi_x(\mathrm{Sign}(x))
u \leftarrow u + \pi\nelse
\pi \leftarrow \pi_x(Q\mathrm{Sign}(Q^T x))
\hat{v} \leftarrow \hat{v} + \pi\nend if
x \leftarrow x - \pi\nend while
Return: x, u, \hat{v}
```

and the residual given by the Pythagorean theorem again is

<span id="page-3-2"></span>
$$||x - \hat{x}||_2^2 = ||x||_2^2 - \frac{||Q^T x||_1^2}{n}.$$
 (3)

In the greedy algorithm we start from  $x_0 = x$ , then for  $k = 0, \ldots$  we select a vector of form  $\lambda \hat{x_k}$  or  $\lambda Q \hat{x_k}$  (where  $\hat{x_k}$  has elements  $\pm 1$ ) that is the closest to the vector  $x_k$ , subtract the projection  $\pi_{x_k}(\operatorname{sign}(x_k))$  or  $\pi_{x_k}(\operatorname{sign}(Q^Tx_k))$ ) from it and repeat the procedure until convergence. Thus, we decompose the initial vector decreasing the norm of  $x_k$  each iteration and increasing the norm of factors  $u_k$  and  $\hat{v_k}$ . The idea is summarized in Algorithm 1.

<span id="page-3-1"></span>![](_page_3_Figure_7.jpeg)

Figure 2: Convergence criterion ( $||x_0 - u_k - \hat{v}_k||_2$ ) for randomly generated vector x of length 1000. The semi-transparent area shows the confidence interval.

Convergence of the algorithm The vector algorithm is guaranteed to converge for arbitrary orthogonal matrix Q except for a set of small measure Kashin [1977]. Our experiments demonstrate, that the convergence speed varies when choosing from the classes of structured orthogonal matrices. The demonstration is presented in Figure 2, where we took 5 different orthogonal matrices Q and generated 23 random vectors of the form  $x \in \mathbb{R}^{1000}$ . Householder reflection and Givens rotation perform poorly, whereas dct, random orthogonal and butterfly matrices perform on par.

Differences in convergence raise a natural question about the convergence properties of Algorithm 1. On each iteration we have a vector as an input x, from which we subtract a projection, resulting in a vector  $x - \hat{x}$ . Thus, we consider the

![](_page_4_Figure_2.jpeg)

<span id="page-4-1"></span>![](_page_4_Figure_3.jpeg)

Figure 3: Convergence criterion ( $\|x - \hat{x}\|_2$ ) of the matrix decomposition Kashin algorithm for different layers of OPT-125m model. Left: DCT matrix converges very slowly after several iterations. Right: DCT matrix converges well for another layer.

difference between them as a decreasing factor on the iteration and any constructive approach to bound its norm with respect to the matrix Q properties is of our interest.

Suppose on k-th iteration we have  $x_k$  and the squared norm after a single iteration of the algorithm  $||x_{k+1}||_2^2$  could be either  $||x||_2^2 - \frac{||x||_1^2}{n}$  or  $||x||_2^2 - \frac{||Q^Tx||_1^2}{n}$  from (2) and (3). Note also, that the choice is made in favor of maximum 1-norm  $\max(||x||_1, ||Q^Tx||_1)$ . Overall, we decrease the residual norm at each iteration, which ensures the convergence of the algorithm. One can consider starting iteration, where  $||x_0||_2 = ||x||_2 = 1$ , which leads to the

<span id="page-4-2"></span>
$$||x - \hat{x}||^2 \le 1 - \frac{1}{n} \left( \max(||x||_1, ||Q^T x||_1) \right)^2$$
(4)

Clearly, the specific choice of the matrix Q affects the quantity  $\max(\|x\|_1, \|Q^Tx\|_1)$ . Moreover, this simple estimation immediately poses another interesting question. How does the choice of an input vector x affect the convergence? The answer could be obtained from studying the following optimization problem, which is clearly related to the Kolmogorov width Temlyakov [1998] estimation:

<span id="page-4-0"></span>
$$\min_{\|x\|_2=1} \max(\|x\|_1, \|Q^T x\|_1)$$
 (5)

The problem (5) determines the worst-case convergence rate for a specific matrix Q. To address the problem we considered several classes of orthogonal matrices Q (see more details in section 3) and performed a search across all eigenvectors of the matrix  $Q^T$  ( $\|Q^Tx\|_1 = \|\lambda x\|_1$ ). The results are presented in Table 1.

Matrix version of the algorithm. As we delved into the nuances of matrix decomposition, leveraging the pioneering Kashin vector decomposition algorithm 1 initially seemed a straightforward extension: vectorize the matrices and proceed with the decomposition. Yet, this simplistic approach soon revealed its limitations, especially when faced with matrices of even moderate size, such as the  $768 \times 3072$  matrices encountered in the fully connected layers of the OPT-125m model. The challenge of managing large vectors soon made it clear that we needed a new approach. This led to the development of the Matrix Decomposition Kashin Algorithm (Algorithm 2), an improved version of the earlier method, specifically created to tackle the difficulties involved in breaking down matrices.

In the naive implementation in order to decompose a matrix of shape  $m \times n$  one needs to store matrix Q of shape  $mn \times mn$ , while the matrix version leads to memory reduction since we need to store  $m \times m + n \times n$  for  $Q_1$  and  $Q_2$ . The genesis of the proposed Algorithm 2 follows from the simple observation. Let's assume our orthogonal matrix Q can be represented as a Kronecker product of two smaller orthogonal matrices  $Q_1^T$  and  $Q_2^T$ :

$$Q = Q_2^T \otimes Q_1^T \tag{6}$$

From the properties of Kronker product, we get:

#### Algorithm 2 Matrix Decomposition Kashin Algorithm

```
Input: Matricx X \in \mathbb{R}^{m \times n}, Orthogonal matrices Q_1, Q_2, Tolerance \varepsilon > 0
Output: Matrices U, \hat{V} \in \mathbb{R}^{m \times n}, such that X \approx U + \hat{V} = U + Q_1 V Q_2^T and both \mathrm{Vec}(U) and \mathrm{Vec}(V) have small infinity norm.

Initialize U \leftarrow 0^{m \times n}, \hat{V} \leftarrow 0^{m \times n}
Define projection \pi_X(Y) := \frac{\mathrm{Vec}(X)^\top \mathrm{Vec}(Y)}{\|\mathrm{Vec}(Y)\|_2^2} \cdot Y
while \|X - U - \hat{V}\| \ge \varepsilon do Y \leftarrow Q_1^T X Q_2\nif \|\mathrm{Vec}(X)\|_1 > \|\mathrm{Vec}(Y)\|_1 then \pi \leftarrow \pi_X(\mathrm{Sign}(X))
U \leftarrow U + \pi\nelse
\pi \leftarrow \pi_X(Q_1 \mathrm{Sign}(Y) Q_2^\top)
\hat{V} \leftarrow \hat{V} + \pi\nend if X \leftarrow X - \pi\nend while
Return: X, U, \hat{V}
```

![](_page_5_Figure_4.jpeg)

Figure 4: Left: Matrix Decomposition Kashin Algorithm 2 performs significantly faster for matrices, than vectorization and applying Vector Decomposition Kashin Algorithm 1. Right: Time comparison of different orthogonal matrices for Matrix Decomposition Kashin Algorithm

<span id="page-5-2"></span>
$$(Q_2^T \otimes Q_1^T) \operatorname{vec}(X) = \operatorname{vec}(Q_1^T X Q_2)$$
(7)

However, by assuming the special structure of Q we might lose the robustness guaranteed for random orthogonal matrices (as proven in Kashin [1977], Lyubarskii and Vershynin [2010]). Indeed, as shown in Guedon et al. [2008], some discrete orthonormal systems produce slightly worse bounds.

Figure 4 illustrates that the time needed for the same computations is notably less for the matrix version of the algorithm than for the vector one.

#### <span id="page-5-0"></span>3 How orthogonal matrix Q affects the algorithm

The choice of orthogonal matrix Q in algorithms 1 and 2 can significantly impact convergence and execution time. Figure 3 demonstrates the different convergence properties of the algorithm for different input matrices.

In this work, we have tried several classes of orthogonal matrices:

![](_page_6_Figure_2.jpeg)

Figure 5: Butterfly factor matrices from left to right:  $B_8$ ,  $B_4$ ,  $B_2$ 

#### 3.1 Random Orthogonal Matrix

Random orthogonal matrix Q is obtained from the QR decomposition of a matrix generated from a normal distribution.

#### <span id="page-6-1"></span>3.2 Householder Reflection

The Householder matrix is an orthogonal matrix that describes a reflection across a hyperplane orthogonal to some unit vector *y*:

<span id="page-6-0"></span>
$$Q = I - 2yy^* \tag{8}$$

#### <span id="page-6-2"></span>3.3 Discrete Cosine Transform

Discrete Cosine Transform (DCT) is an orthogonal linear mapping similar to the discrete Fourier transform (DFT), but using only the cosine functions. We chose the most commonly used form, DCT-II:

$$Q[i,j] = \begin{cases} \frac{1}{\sqrt{n}}, & j = 0\\ \sqrt{\frac{2}{n}} \cos\left(\frac{\pi(2i+1)j}{2n}\right) \end{cases}$$
(9)

#### <span id="page-6-3"></span>3.4 Butterfly matrices

Butterfly matrices are a class of structured orthogonal matrices that allow fast vector-by-matrix multiplication.

A butterfly matrix Q of size  $n = 2^m$  can be represented as a product of m block diagonal matrices (called butterfly factor matrices). We denote each butterfly factor matrix as  $B_k$ , where k indicates block size:

$$Q = B_n B_{\frac{n}{2}} \dots B_2$$

$$B_k = \text{diag}(F_1, F_2, \dots, F_{\frac{n}{k}})$$
(10)

Each block  $F_i$  (a butterfly factor) of size k has a form  $\begin{bmatrix} D_1 & D_2 \\ D_3 & D_4 \end{bmatrix}$  where  $D_i$  is a  $\frac{k}{2} \times \frac{k}{2}$  diagonal matrix. Figure 5 shows an example of a butterfly matrix of size 16.

Matrices like Householder Reflection (3.2), Discrete Cosine Transform (3.3), and Butterfly matrices (3.4) support faster matvec multiplications (faster than  $O(n^2)$ ) due to their special structure. For example, Householder transformation boils down to a simple operation with two vectors:

$$(I - 2yy^*)x = x - 2\langle y, x \rangle y \tag{11}$$

while DCT and Butterfly matrices allow for  $O(n \log n)$  complexity of matrix-vector multiplication.

#### 3.5 Convergence properties

However, an obvious problem arises for Householder Reflexion considering the convergence bound (4): when  $\|x\|_1$  is small (for example, x is very sparse) and the dimension is high, vectors y and x might be orthogonal, thus  $Q^Tx$  will be equal to x (x will lie on the reflection plane and will be the eigenvector of  $Q^T$ ). This keeps  $\max(\|x\|_1, \|Q^Tx\|_1)$  small and, consequently, the convergence bound - high.

We try to estimate potential minimums of  $\max(\|x\|_1, \|Q^Tx\|_1)$  expression in Table 1 by taking the real part of eigenvalues (only the Householder matrix is symmetric and has real eigenvectors) of each orthogonal matrix. These results allow us to hypothesize that qr and butterfly matrices in the general case should converge best. These results coincide with the empirical convergence of the algorithm for randomly generated vectors (Figure 2).

<span id="page-7-2"></span>Table 1: Estimation for  $x = \text{Re}[y], y \in \text{eig}(Q)$ . Mean over 100 generated Q matrices (except for DCT). Matrix size is  $500 \times 500$ . All results are divided by  $\sqrt{n}$ .

| Q           | $\min_{\ x\ _2=1} \max\{\ x\ _1, \ Q^T x\ _1\}$ |
|-------------|-------------------------------------------------|
| RANDOM      | 0.548                                           |
| HOUSEHOLDER | 0.076                                           |
| DCT         | 0.330                                           |
| BUTTERFLY   | 0.547                                           |

Matrix Kashin representation of the random matrix of shape 500x200. Residual 7.14e-07 after 29 iterations

![](_page_7_Figure_5.jpeg)

<span id="page-7-0"></span>Figure 6: Factors U and V are well quantized after computing Kashin decomposition.

## <span id="page-7-1"></span>4 Quantization approach

As soon as we have the decomposition  $X = U + Q_1 V Q_2^T$ , where u and v have small infinity norm, we may hope, that the entries distribution of these vectors may be quantized well. The idea behind the quantization approach is fairly simple. We replace the values in the factors with the nearest centroids values, calculated with the clustering procedure. For illustration, we consider matrix  $X \in \mathbb{R}^{500 \times 200}$  with entries from standard distribution and apply Matrix Decomposition Kashin Algorithm 2 to it. Figure 6 clearly illustrates that values of factors U and V are well quantized.

The red lines and dots on the graph represent the centroids of corresponding clusters of values. The number of clusters is defined by the number of bits for quantization. Figure 6 contains 4 clusters per factor, which means, that we need to store the values of  $16 = 2^4$  points or 4 bits. From the same figure, one can conclude, that 16 clusters per factor leads to the  $16 \times 16 = 256 = 2^8$  possible pairs of clusters.

To measure the quality of the proposed quantization procedure we decided to consider weights of OPT models Zhang et al. [2022] and decompose all layers except the embedding layer in the model in a similar manner. So, we applied Algorithm 2 for each weight matrix  $X_i$  and recieved  $U_i$ ,  $\hat{V}_i$  for layer i. After that, we applied the clustering procedure to the set of 2-dimensional vectors obtained from stacking  $U_i$  values and  $V_i = Q_1^T \hat{V}_i Q_2$  values with a selected number of clusters (32 for 5 bits, 64 for 6 bits, etc.). After obtaining centroids, we replace each entry in the matrices  $U_i$ ,  $V_i$  with its closest centroid value. As a result, we have quantized factors  $U_i^q$  and  $V_i^q$  with relatively small infinity error. And all we have to do is to replace the old forward pass with matrix  $X_i(\cdot)$  with the new forward pass  $\left[U_i^q + Q_1V_i^qQ_2^T\right](\cdot)$ . It is important to highlight, that we do not need to store the matrices  $Q_1$  and  $Q_2$ , their action is replaced with effective DCT or Butterfly matvec procedures.

However, we observed, that not all layers could be compressed equally well with Algorithm 2. This is clearly distinguished either visually (see Figure 7) or from monitoring convergence speed. The reasons behind such behavior of the method are yet to be described. For practical reasons, we decided not to decompose such layers. The results are presented in Table 2.

#### <span id="page-7-3"></span>5 Experiments

To prove the efficacy of our method, we use the Open Pre-trained Transformers (OPT Zhang et al. [2022]) language models and the LAMBADA dataset Paperno et al. [2016].

![](_page_8_Figure_2.jpeg)

Figure 7: Left: Slow convergence of the Matrix Decomposition Kashin algorithm for a particular weight matrix from OPT-125m leads to poor concentration of values and high quantization error. Right: another layer weight matrix could be easily decomposed and quantized.

<span id="page-8-1"></span>Table 2: Perplexity for OPT family of models with different quantization schemes. Part of the transformer layers are quantized with Kashin M-bit quantization (those, for which Kashin decomposition has converged) and others are quantized with N-bit. The "Quantized Layers" column specifies how many layers were quantized with each method (first fraction for N-bit and second fraction for kM-bit).

<span id="page-8-0"></span>

| QUANTIZATION   | PERPLEXITY | QUANTIZED LAYERS |  |  |  |  |  |  |  |
|----------------|------------|------------------|--|--|--|--|--|--|--|
| OPT-125M       |            |                  |  |  |  |  |  |  |  |
| FP32           | 42.01      |                  |  |  |  |  |  |  |  |
|                |            |                  |  |  |  |  |  |  |  |
| 8-BIT          | 42.19      | 72/72            |  |  |  |  |  |  |  |
| 8-BIT + K6-BIT | 43.38      | 15/72 + 57/72    |  |  |  |  |  |  |  |
| 8-BIT + K5-BIT | 45.74      | 15/72 + 57/72    |  |  |  |  |  |  |  |
| 4-BIT          | 48.92      | 72/72            |  |  |  |  |  |  |  |
| 4-BIT + K6-BIT | 44.88      | 15/72 + 57/72    |  |  |  |  |  |  |  |
| 4-BIT + K5-BIT | 47.25      | 15/72 + 57/72    |  |  |  |  |  |  |  |
|                | OPT-350M   |                  |  |  |  |  |  |  |  |
|                |            |                  |  |  |  |  |  |  |  |
| FP32           | 36.64      |                  |  |  |  |  |  |  |  |
|                |            |                  |  |  |  |  |  |  |  |
| 8-BIT          | 36.77      | 146/146          |  |  |  |  |  |  |  |
| 8-BIT + K6-BIT | 37.59      | 25/146 + 121/146 |  |  |  |  |  |  |  |
| 8-BIT + K5-BIT | 40.01      | 25/146 + 121/146 |  |  |  |  |  |  |  |
| 4-BIT          | 44.46      | 146/146          |  |  |  |  |  |  |  |
| 4-BIT + K6-BIT | 37.61      | 25/146 + 121/146 |  |  |  |  |  |  |  |
| 4-BIT + K5-BIT | 40.05      | 25/146 + 121/146 |  |  |  |  |  |  |  |
|                |            |                  |  |  |  |  |  |  |  |

First, we try to compare Kashin Decomposition with different orthogonal matrices for several layers of the opt-125m language model. Unlike randomly generated matrices, the convergence of Kashin decomposition for network weights can be quite unpredictable. Figure [3](#page-4-1) depicts the value of the convergence criterion for two different layers of the first transformer block. For the fc1 layer, the algorithm fails to converge in the maximum number of steps and *dct* converges slower than *butterfly* and *qr*. For the q\_proj layer, *dct* performs on par with *qr* and slightly better than *butterfly*. Kashin Decomposition with *householder reflection* performs poorly in both cases. In all further experiments, we use either *qr* or *butterfly* orthogonal matrices.

Next, we apply Kashin Quantization and measure LLM's perplexity. As seen in Figures [3](#page-4-1) and [7,](#page-8-0) Kashin Decomposition doesn't always converge for LLM weights, which leads to high quantization error. In our experiments with the OPT family of models, we encountered about 0.2 fractions of poorly converged layers. To compensate for these layers, we

<span id="page-9-0"></span>

| Table 3: Experiments on GLUE benchmark. We compare Kashin Quantization to common quantization methods such |
|------------------------------------------------------------------------------------------------------------|
| as Kmeans and Uniform Quantization. We quantize all linear layers except for embedding and lmhead.         |

| QUANTIZATION                                      | COLA                   | SST-2                   | QQP                                       | QNLI                    | MNLI                                      | RTE                     | STS-B                                    | MRPC                                     |  |  |
|---------------------------------------------------|------------------------|-------------------------|-------------------------------------------|-------------------------|-------------------------------------------|-------------------------|------------------------------------------|------------------------------------------|--|--|
| ROBERTA-BASE                                      |                        |                         |                                           |                         |                                           |                         |                                          |                                          |  |  |
| FP32                                              | 59.06                  | 93.8                    | 91.24/88.36                               | 92.62                   | 88.1/87.43                                | 67.87                   | 89.65/89.49                              | 87.75/91.2                               |  |  |
| UNIFORM 4BIT<br>KMEANS 4BIT                       | 0.0<br>46.97           | 49.08<br>92.77          | 36.82/53.82<br>88.77/87.39                | 49.46<br>89.27          | 31.82/31.82<br>83.98/82.85                | 52.71<br>55.23          | 10.08/9.37<br>79.65/80.47                | 68.38/81.22<br>71.32/75.77               |  |  |
| KASHIN 4BIT (OURS)                                | 52.09                  | 90.37                   | 89.53/86.73                               | 91.14                   | 86.41/85.51                               | 60.28                   | 87.29/87.26                              | 83.08/87.10                              |  |  |
| BERT-BASE                                         |                        |                         |                                           |                         |                                           |                         |                                          |                                          |  |  |
| FP32                                              | 59.31                  | 91.74                   | 90.66/87.39                               | 90.74                   | 83.96/84.24                               | 64.98                   | 88.94/88.77                              | 84.31/88.81                              |  |  |
| UNIFORM 4BIT<br>KMEANS 4BIT<br>KASHIN 4BIT (OURS) | 1.24<br>54.43<br>59.65 | 49.66<br>91.51<br>91.63 | 38.09/52.75<br>88.87/85.33<br>90.28/87.33 | 49.22<br>88.01<br>90.06 | 32.24/33.34<br>78.63/78.76<br>83.88/84.01 | 50.18<br>55.23<br>63.53 | -0.21/-0.25<br>85.06/85.0<br>88.76/88.56 | 63.97/76.02<br>34.55/8.87<br>84.80/89.31 |  |  |

![](_page_9_Figure_4.jpeg)

Figure 8: Scheme of post-training quantization approach.

leave their weights with the default quantization scheme (8-bit or 4-bit versions of weights from the huggingface hub). Results can be seen in Table [2.](#page-8-1)

Kashin Quantization achieves a trade-off between low bit weights, inference speed, and LLM prediction quality. For example, full 4-bit quantization significantly raises the model's perplexity, whereas 4-bit + Kashin 6-bit quantization almost restores the quality of the 8-bit model. That, in conjunction with the ability to perform lower-bit operations and faster matrix multiplication (with the right orthogonal matrix choice, for example, butterfly matrices) can significantly reduce LLM's inference speed and memory requirements.

Additionaly, we conduct experiments on text-classification with a set of downstream tasks (GLUE benchmark). We have finetuned Bert and RoBerta models, measured their accuracy as a baseline, then quantized linear layers in transformer blocks with three quantization methods: uniform, kmeans and kashin quantization (ours). Kashin quantization demonstrates superior quality on almost all GLUE datasets for both models (Figure [3\)](#page-9-0).

# 6 Related Work

Large Language Models (LLMs) nowadays are ubiquitous and used in all imaginable applications. However, their complexity heavily depends on several parameters. For example, the flagship of LLAMA-2 [Touvron et al.](#page-12-1) [\[2023a\]](#page-12-1) family of models has over 70 billion parameters. This impedes model speed and sometimes makes training or even inference impossible due to a lack of GPU memory.

Quantization [Nagel et al.](#page-11-6) [\[2021\]](#page-11-6) is a popular technique to reduce the model size and inference time. Naturally, it is often applied to LLMs. For instance, QLORA [Dettmers et al.](#page-11-7) [\[2023\]](#page-11-7) paper used quantized weights in conjunction with Low-Rank Adapters to fine-tune language models on downstream tasks, and LLM.int8 [Dettmers et al.](#page-11-8) [\[2022\]](#page-11-8) has introduced a new Int8 matrix multiplication procedure for feed-forward and attention projection layers in transformers. Still, the quantization of transformers often proves to be a tricky task, especially the quantization of activations. It happens due to the presence of huge outliers in activations that originate from the attention mechanism [\(Bondarenko](#page-11-9) [et al.](#page-11-9) [\[2021\]](#page-11-9), [Bondarenko et al.](#page-11-10) [\[2023\]](#page-11-10)).

Best accuracy rsults are usually obtained with quantization-aware training. Another approach, taken in [van Baalen et al.](#page-12-5) [\[2020\]](#page-12-5), is to learn bit-width and quantization parameters simultaneously with model weights. However, both techniques require dataset and resources to train the model with additional step of quantization on each weight update.

To avoid training expenses, methods that allow for no training/fine-tuning have been of particular interest in several papers: authors in [Eldad et al.](#page-11-11) [\[2019\]](#page-11-11) scale the weights of consecutive layers which allows them achieve smaller quality drop on a wide variety of networks; AdaRound [Nagel et al.](#page-11-12) [\[2020\]](#page-11-12) proves that rounding to the nearest node of the quantization grid is not the best strategy and propose to choose rounding by optimization process which requires only a few thousand samples of data, researches in [Hubara et al.](#page-11-13) [\[2020\]](#page-11-13) further develop the idea of AdaRound, complementing it with integer programming to determine the best bit-width for each layer.

It is important to note that there are other ways to reduce memory footprint when using large models, such as automatic mixed precision [Micikevicius et al.](#page-11-14) [\[2017\]](#page-11-14), operations approximation [Bershatsky et al.](#page-11-15) [\[2022\]](#page-11-15), [Novikov et al.](#page-11-16) [\[2023\]](#page-11-16), and checkpointing [Chen et al.](#page-11-17) [\[2016\]](#page-11-17), [Gusak et al.](#page-11-18) [\[2022\]](#page-11-18).

In our work we use *Kashin Representations*, introduced in [Kashin](#page-11-2) [\[1977\]](#page-11-2). It's an expansion of vector x in a redundant orthogonal basis which guarantees that the maximum among absolute values of coefficients (the infinity norm) is upper bounded. It is a source for representation in Eq. [1](#page-2-0) and Algorithm [1.](#page-3-0) [Garnaev and Gluskin](#page-11-19) [\[1984\]](#page-11-19) discusses the redundancy level in Kashin representations and [Lyubarskii and Vershynin](#page-11-3) [\[2010\]](#page-11-3) investigates the applicability of Kashin representations to vector quantization using tight orthogonal frames that satisfy uncertainty principle.

# 7 Conclusion and further research

We have proposed a matrix case generalization of the Kashin Representation algorithm and applied it to the weights of transformer language models. We have compared different choices of orthogonal matrices and theorized on efficacy of each based on both empirical results and metrics in Eq. [5](#page-4-0) estimation among eigenvectors of Q.

Kashin Quantization backed up by the conventional uniform quantization achieves a good compromise between model perplexity and memory requirements. Additionally, Kashin representation allows to use of faster matrix multiplication due to the choice of Q.

There is much yet to be determined about the properties of convergence of Algorithm [2.](#page-5-1) As noted in Section [5,](#page-7-3) the proposed decomposition for matrices of model weights doesn't always converge in a restricted number of iterations. The proper investigation on both failed matrix weights and special structure of orthonormal basis Q is a question of further research.

We are looking forward to applying Kashin Decomposition to the quantization of activations. As shown in [Bondarenko](#page-11-9) [et al.](#page-11-9) [\[2021\]](#page-11-9) and [Bondarenko et al.](#page-11-10) [\[2023\]](#page-11-10), quantization of transformer activations often suffers from huge outliers. Since Kashin Representation guarantees an upper bound on infinity norms (maximum absolute value) of decomposition factors, it can be assumed that Kashin Quantization should be particularly beneficial to LLM activations quantization.

#### References

- <span id="page-11-0"></span>Ebtesam Almazrouei, Hamza Alobeidli, Abdulaziz Alshamsi, Alessandro Cappelli, Ruxandra Cojocaru, Mérouane Debbah, Étienne Goffinet, Daniel Hesslow, Julien Launay, Quentin Malartic, et al. The falcon series of open language models. *arXiv preprint arXiv:2311.16867*, 2023.
- <span id="page-11-15"></span>Daniel Bershatsky, Aleksandr Mikhalev, Alexandr Katrutsa, Julia Gusak, Daniil Merkulov, and Ivan Oseledets. Memoryefficient backpropagation through large linear layers. *arXiv preprint arXiv:2201.13195*, 2022.
- <span id="page-11-9"></span>Yelysei Bondarenko, Markus Nagel, and Tijmen Blankevoort. Understanding and overcoming the challenges of efficient transformer quantization, 2021.
- <span id="page-11-10"></span>Yelysei Bondarenko, Markus Nagel, and Tijmen Blankevoort. Quantizable transformers: Removing outliers by helping attention heads do nothing, 2023.
- <span id="page-11-17"></span>Tianqi Chen, Bing Xu, Chiyuan Zhang, and Carlos Guestrin. Training deep nets with sublinear memory cost. *arXiv preprint arXiv:1604.06174*, 2016.
- <span id="page-11-8"></span>Tim Dettmers, Mike Lewis, Younes Belkada, and Luke Zettlemoyer. Llm.int8(): 8-bit matrix multiplication for transformers at scale, 2022.
- <span id="page-11-7"></span>Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, and Luke Zettlemoyer. Qlora: Efficient finetuning of quantized llms, 2023.
- <span id="page-11-11"></span>Meller Eldad, Finkelstein Alexander, Almog Uri, and Grobman Mark. Same, same but different: Recovering neural network quantization error through weight factorization. volume 2019-June, 2019.
- <span id="page-11-19"></span>A. Yu. Garnaev and E. D. Gluskin. On widths of the Euclidean ball. *Sov. Math., Dokl.*, 30:200–204, 1984. ISSN 0197-6788.
- <span id="page-11-4"></span>Olivier Guedon, Shahar Mendelson, Alain Pajor, and Nicole Tomczak-Jaegermann. Majorizing measures and proportional subsets of bounded orthonormal systems, 2008.
- <span id="page-11-18"></span>Julia Gusak, Daria Cherniuk, Alena Shilova, Alexander Katrutsa, Daniel Bershatsky, Xunyi Zhao, Lionel Eyraud-Dubois, Oleg Shlyazhko, Denis Dimitrov, Ivan Oseledets, et al. Survey on large scale neural network training. *arXiv preprint arXiv:2202.10435*, 2022.
- <span id="page-11-13"></span>Itay Hubara, Yury Nahshan, Yair Hanani, Ron Banner, and Daniel Soudry. Improving post training neural quantization: Layer-wise calibration and integer programming. 6 2020. doi[:10.48550/arxiv.2006.10518.](https://doi.org/10.48550/arxiv.2006.10518) URL [https://arxiv.](https://arxiv.org/abs/2006.10518) [org/abs/2006.10518](https://arxiv.org/abs/2006.10518).
- <span id="page-11-2"></span>Boris Sergeevich Kashin. Diameters of some finite-dimensional sets and classes of smooth functions. *Izvestiya Rossiiskoi Akademii Nauk. Seriya Matematicheskaya*, 41(2):334–351, 1977.
- <span id="page-11-1"></span>Boris Sergeevich Kashin and DG Romskii. An efficient algorithm for decomposing a vector into two vectors with a small uniform norm. *Matematicheskie Zametki*, 114(6):945–948, 2023.
- <span id="page-11-3"></span>Yurii Lyubarskii and Roman Vershynin. Uncertainty principles and vector quantization. *IEEE Transactions on Information Theory*, 56(7):3491–3501, July 2010. ISSN 1557-9654. doi[:10.1109/tit.2010.2048458.](https://doi.org/10.1109/tit.2010.2048458) URL [http:](http://dx.doi.org/10.1109/TIT.2010.2048458) [//dx.doi.org/10.1109/TIT.2010.2048458](http://dx.doi.org/10.1109/TIT.2010.2048458).
- <span id="page-11-14"></span>Paulius Micikevicius, Sharan Narang, Jonah Alben, Gregory Diamos, Erich Elsen, David Garcia, Boris Ginsburg, Michael Houston, Oleksii Kuchaiev, Ganesh Venkatesh, et al. Mixed precision training. *arXiv preprint arXiv:1710.03740*, 2017.
- <span id="page-11-12"></span>Markus Nagel, Rana Ali Amjad, Mart Van Baalen, Christos Louizos, and Tijmen Blankevoort. Up or down? adaptive rounding for post-training quantization. In *International Conference on Machine Learning*, pages 7197–7206. PMLR, 2020.
- <span id="page-11-6"></span>Markus Nagel, Marios Fournarakis, Rana Ali Amjad, Yelysei Bondarenko, Mart van Baalen, and Tijmen Blankevoort. A white paper on neural network quantization, 2021.
- <span id="page-11-16"></span>Georgii Sergeevich Novikov, Daniel Bershatsky, Julia Gusak, Alex Shonenkov, Denis Valerievich Dimitrov, and Ivan Oseledets. Few-bit backward: Quantized gradients of activation functions for memory footprint reduction. In *International Conference on Machine Learning*, pages 26363–26381. PMLR, 2023.
- <span id="page-11-5"></span>Denis Paperno, Germán Kruszewski, Angeliki Lazaridou, Ngoc Quan Pham, Raffaella Bernardi, Sandro Pezzelle, Marco Baroni, Gemma Boleda, and Raquel Fernandez. The lambada dataset: Word prediction requiring a broad discourse context. In *Proceedings of the 54th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*. Association for Computational Linguistics, 2016. doi[:10.18653/v1/p16-1144.](https://doi.org/10.18653/v1/p16-1144) URL <http://dx.doi.org/10.18653/v1/P16-1144>.

- <span id="page-12-3"></span>Mher Safaryan, Egor Shulgin, and Peter Richtárik. Uncertainty principle for communication compression in distributed and federated learning and the search for an optimal compressor. *Information and Inference: A Journal of the IMA*, 11(2):557–580, 2022.
- <span id="page-12-4"></span>Vladimir Nikolaevich Temlyakov. Nonlinear kolmogorov widths. *Mathematical Notes*, 63(6):785–795, 1998.
- <span id="page-12-1"></span>Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. *arXiv preprint arXiv:2302.13971*, 2023a.
- <span id="page-12-2"></span>Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. Llama 2: Open foundation and fine-tuned chat models. *arXiv preprint arXiv:2307.09288*, 2023b.
- <span id="page-12-5"></span>Mart van Baalen, Christos Louizos, Markus Nagel, Rana Ali Amjad, Ying Wang, Tijmen Blankevoort, and Max Welling. Bayesian bits: Unifying quantization and pruning. volume 2020-December, 2020.
- <span id="page-12-0"></span>Susan Zhang, Stephen Roller, Naman Goyal, Mikel Artetxe, Moya Chen, Shuohui Chen, Christopher Dewan, Mona Diab, Xian Li, Xi Victoria Lin, Todor Mihaylov, Myle Ott, Sam Shleifer, Kurt Shuster, Daniel Simig, Punit Singh Koura, Anjali Sridhar, Tianlu Wang, and Luke Zettlemoyer. Opt: Open pre-trained transformer language models, 2022.