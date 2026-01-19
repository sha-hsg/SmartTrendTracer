# 3 Expectation

### 3.1 Expectation of a Randorn Variable

The mean, or expectation, of a random variable *X* is the average value of *x.* 

**3.1 Definition.** *The* expected value, *or* mean, *or* first moment, *of X is defined to be* 

$$\mathbb{E}(X) = \int x \, dF(x) = \begin{cases} \sum_{x} x f(x) & \text{if } X \text{ is discrete} \\ \int x f(x) dx & \text{if } X \text{ is continuous} \end{cases} \tag{3.1}$$

*assuming that the sum (or integral) is well defined. We use the following notation to denote the expected value of x:* 

$$\mathbb{E}(X) = \mathbb{E}X = \int x \, dF(x) = \mu = \mu_X. \tag{3.2}$$

The expectation is a one-number summary of the distribution. Think of *lE(X)* as the average L~=l *X;/n* of a large number of IID draws *Xl, ... ,X<sup>n</sup> .*  The fact that *lE(X)* ~ L~=l *X;/n* is actually more than a heuristic; it is a theorem called the law of large numbers that we will discuss in Chapter 5.

The notation *J x dF (x)* deserves some comment. We use it merely as a convenient unifying notation so we don't have to write *Lx xf(x)* for discrete random variables and  $\int x f(x) dx$  for continuous random variables, but you should be aware that  $\int x dF(x)$  has a precise meaning that is discussed in real analysis courses.

To ensure that  $\mathbb{E}(X)$  is well defined, we say that  $\mathbb{E}(X)$  exists if  $\int_x |x| dF_X(x) < 0$  $\infty$ . Otherwise we say that the expectation does not exist.

**3.2 Example.** Let  $X \sim \text{Bernoulli}(p)$ . Then  $\mathbb{E}(X) = \sum_{x=0}^{1} x f(x) = (0 \times (1$  $p) + (1 \times p) = p. \blacksquare$ 

**3.3 Example.** Flip a fair coin two times. Let  $X$  be the number of heads. Then,  $\mathbb{E}(X) = \int x dF_X(x) = \sum_x x f_X(x) = (0 \times f(0)) + (1 \times f(1)) + (2 \times f(2)) =$  $(0 \times (1/4)) + (1 \times (1/2)) + (2 \times (1/4)) = 1. \blacksquare$ 

**3.4 Example.** Let  $X \sim \text{Uniform}(-1,3)$ . Then,  $\mathbb{E}(X) = \int x dF_X(x) = \int x f_X(x) dx =$  $\frac{1}{4} \int_{-1}^{3} x \, dx = 1. \ \blacksquare$ 

3.5 Example. Recall that a random variable has a Cauchy distribution if it has density  $f_X(x) = {\pi(1+x^2)}^{-1}$ . Using integration by parts, (set  $u = x$ and  $v = \tan^{-1} x$ ,

$$\int |x| dF(x) = \frac{2}{\pi} \int_0^\infty \frac{x \, dx}{1 + x^2} = \left[ x \ \tan^{-1}(x) \right]_0^\infty - \int_0^\infty \tan^{-1} x \, dx = \infty$$

so the mean does not exist. If you simulate a Cauchy distribution many times and take the average, you will see that the average never settles down. This is because the Cauchy has thick tails and hence extreme observations are  $\text{common.} \blacksquare$ 

From now on, whenever we discuss expectations, we implicitly assume that  $\text{they exist.}$ 

Let  $Y = r(X)$ . How do we compute  $\mathbb{E}(Y)$ ? One way is to find  $f_Y(y)$  and then compute  $\mathbb{E}(Y) = \int y f_Y(y) dy$ . But there is an easier way.

**3.6 Theorem** (The Rule of the Lazy Statistician). Let 
$$Y = r(X)$$
. Then
$$\mathbb{E}(Y) = \mathbb{E}(r(X)) = \int r(x) dF_X(x). \tag{3.3}$$

This result makes intuitive sense. Think of playing a game where we draw X at random and then I pay you  $Y = r(X)$ . Your average income is  $r(x)$  times the chance that  $X = x$ , summed (or integrated) over all values of x. Here is a special case. Let A be an event and let  $r(x) = I_A(x)$  where  $I_A(x) = 1$  if  $x \in A$  and  $I_A(x) = 0$  if  $x \notin A$ . Then

$$\mathbb{E}(I_A(X)) = \int I_A(x) f_X(x) dx = \int_A f_X(x) dx = \mathbb{P}(X \in A).$$

In other words, probability is a special case of expectation.

**3.7 Example.** Let  $X \sim \text{Unif}(0,1)$ . Let  $Y = r(X) = e^X$ . Then,

$$\mathbb{E}(Y) = \int_0^1 e^x f(x) dx = \int_0^1 e^x dx = e - 1.$$

Alternatively, you could find  $f_Y(y)$  which turns out to be  $f_Y(y) = 1/y$  for  $1 < y < e$ . Then,  $\mathbb{E}(Y) = \int_1^e y f(y) dy = e - 1$ .

**3.8 Example.** Take a stick of unit length and break it at random. Let  $Y$  be the length of the longer piece. What is the mean of  $Y$ ? If X is the break point then  $X \sim \text{Unif}(0,1)$  and  $Y = r(X) = \max\{X, 1 - X\}$ . Thus,  $r(x) = 1 - x$ when  $0 < x < 1/2$  and  $r(x) = x$  when  $1/2 \le x < 1$ . Hence,

$$\mathbb{E}(Y) = \int r(x)dF(x) = \int_0^{1/2} (1-x)dx + \int_{1/2}^1 x\,dx = \frac{3}{4}. \quad \blacksquare$$

Functions of several variables are handled in a similar way. If  $Z = r(X, Y)$  $\text{then}$ 

$$\mathbb{E}(Z) = \mathbb{E}(r(X,Y)) = \int \int r(x,y)dF(x,y). \tag{3.4}$$

**3.9 Example.** Let  $(X,Y)$  have a jointly uniform distribution on the unit square. Let  $Z = r(X, Y) = X^2 + Y^2$ . Then,

$$\mathbb{E}(Z) = \int \int r(x,y) dF(x,y) = \int_0^1 \int_0^1 (x^2 + y^2) dx dy$$
$$= \int_0^1 x^2 dx + \int_0^1 y^2 dy = \frac{2}{3}. \quad \blacksquare$$

The  $k^{th}$  moment of X is defined to be  $\mathbb{E}(X^k)$  assuming that  $\mathbb{E}(|X|^k) < \infty$ . **3.10 Theorem.** If the  $k^{th}$  moment exists and if  $j < k$  then the  $j^{th}$  moment  $exists.$ 

 $\text{PROOF. We have}$ 

$$\mathbb{E}|X|^j = \int_{-\infty}^{\infty} |x|^j f_X(x) dx$$

50  $3.$  Expectation

$$= \int_{|x|\leq 1} |x|^j f_X(x) dx + \int_{|x|>1} |x|^j f_X(x) dx$$
  
$$\leq \int_{|x|\leq 1} f_X(x) dx + \int_{|x|>1} |x|^k f_X(x) dx$$
  
$$\leq 1 + \mathbb{E}(|X|^k) < \infty. \quad \blacksquare$$

The  $k^{th}$  central moment is defined to be  $\mathbb{E}((X-\mu)^k)$ .

#### Properties of Expectations $3.2$

**3.11 Theorem.** If  $X_1, \ldots, X_n$  are random variables and  $a_1, \ldots, a_n$  are constants, then

$$\mathbb{E}\left(\sum_{i} a_{i} X_{i}\right) = \sum_{i} a_{i} \mathbb{E}(X_{i}).\tag{3.5}$$

**3.12 Example.** Let  $X \sim \text{Binomial}(n, p)$ . What is the mean of X? We could try to appeal to the definition:

$$\mathbb{E}(X) = \int x \, dF_X(x) = \sum_x x f_X(x) = \sum_{x=0}^n x \binom{n}{x} p^x (1-p)^{n-x}$$

but this is not an easy sum to evaluate. Instead, note that  $X = \sum_{i=1}^{n} X_i$ where  $X_i = 1$  if the *i*<sup>th</sup> toss is heads and  $X_i = 0$  otherwise. Then  $\mathbb{E}(X_i) =$  $(p \times 1) + ((1-p) \times 0) = p$  and  $\mathbb{E}(X) = \mathbb{E}(\sum_i X_i) = \sum_i \mathbb{E}(X_i) = np.$ 

**3.13 Theorem.** Let  $X_1, \ldots, X_n$  be independent random variables. Then,

$$\mathbb{E}\left(\prod_{i=1}^{n} X_{i}\right) = \prod_{i} \mathbb{E}(X_{i}).\tag{3.6}$$

Notice that the summation rule does not require independence but the multiplication rule does.

#### Variance and Covariance $3.3$

The variance measures the "spread" of a distribution.  $^{1}$ 

<sup>&</sup>lt;sup>1</sup>We can't use  $\mathbb{E}(X-\mu)$  as a measure of spread since  $\mathbb{E}(X-\mu) = \mathbb{E}(X) - \mu = \mu - \mu = 0$ . We can and sometimes do use  $\mathbb{E}|X-\mu|$  as a measure of spread but more often we use the variance.

**3.14 Definition.** Let  $X$  be a random variable with mean  $\mu$ . The variance of  $X$  — denoted by  $\sigma^2$  or  $\sigma_X^2$  or  $\mathbb{V}(X)$  or  $\mathbb{V}X$  — is defined by

$$\sigma^2 = \mathbb{E}(X - \mu)^2 = \int (x - \mu)^2 dF(x) \tag{3.7}$$

assuming this expectation exists. The standard deviation is  $\operatorname{sd}(X) = \sqrt{\mathbb{V}(X)}$  and is also denoted by  $\sigma$  and  $\sigma_X$ .

**3.15 Theorem.** Assuming the variance is well defined, it has the following  $properties:$ 

- 1.  $\mathbb{V}(X) = \mathbb{E}(X^2) \mu^2$ .
- 2. If a and b are constants then  $\mathbb{V}(aX + b) = a^2 \mathbb{V}(X)$ .
- 3. If  $X_1, \ldots, X_n$  are independent and  $a_1, \ldots, a_n$  are constants, then

$$\mathbb{V}\left(\sum_{i=1}^{n} a_i X_i\right) = \sum_{i=1}^{n} a_i^2 \mathbb{V}(X_i). \tag{3.8}$$

**3.16 Example.** Let  $X \sim \text{Binomial}(n, p)$ . We write  $X = \sum_i X_i$  where  $X_i = 1$ if toss i is heads and  $X_i = 0$  otherwise. Then  $X = \sum_i X_i$  and the random variables are independent. Also,  $\mathbb{P}(X_i = 1) = p$  and  $\mathbb{P}(X_i = 0) = 1 - p$ . Recall  $\text{that}$ 

$$\mathbb{E}(X_i) = \left(p \times 1\right) + \left((1-p) \times 0\right) = p.$$

Now,

$$\mathbb{E}(X_i^2) = \left(p \times 1^2\right) + \left((1-p) \times 0^2\right) = p$$

Therefore,  $\mathbb{V}(X_i) = \mathbb{E}(X_i^2) - p^2 = p - p^2 = p(1-p)$ . Finally,  $\mathbb{V}(X) =$  $\mathbb{V}(\sum_i X_i) = \sum_i \mathbb{V}(X_i) = \sum_i p(1-p) = np(1-p)$ . Notice that  $\mathbb{V}(X) = 0$ if  $p = 1$  or  $p = 0$ . Make sure you see why this makes intuitive sense.

If  $X_1, \ldots, X_n$  are random variables then we define the **sample mean** to be

$$\overline{X}_n = \frac{1}{n} \sum_{i=1}^n X_i \tag{3.9}$$

and the sample variance to be

$$S_n^2 = \frac{1}{n-1} \sum_{i=1}^n \left( X_i - \overline{X}_n \right)^2.$$
 (3.10)

**3.17 Theorem.** *Let* Xl"'" *Xn be* IID *and let It* = IE(Xi), *(J2* = V(Xi)' *Then* 

$$\mathbb{E}(\overline{X}_n) = \mu, \quad \mathbb{V}(\overline{X}_n) = \frac{\sigma^2}{n} \quad \text{and} \quad \mathbb{E}(S_n^2) = \sigma^2.$$

If *X* and Yare random variables, then the covariance and correlation between *X* and *Y* measure how strong the linear relationship is between *X* and *Y.* 

**3.18 Definition.** *Let X and Y be random variables with means fLx and fLy and standard deviations (Jx and (Jy. Define the* covariance *between X and Y by* 

$$Cov(X,Y) = \mathbb{E}\bigg((X-\mu_X)(Y-\mu_Y)\bigg) \tag{3.11}$$

*and the* correlation *by* 

$$\rho = \rho_{X,Y} = \rho(X,Y) = \frac{\text{Cov}(X,Y)}{\sigma_X \sigma_Y}.$$
(3.12)

**3.19 Theorem.** *The covariance satisfies:* 

$$\mathsf{Cov}(X,Y) = \mathbb{E}(XY) - \mathbb{E}(X)\mathbb{E}(Y).$$

*The correlation satisfies:* 

$$-1 \le \rho(X, Y) \le 1.$$

*If Y* = *aX* + *b for some constants a and b then p(X, Y)* = 1 *if a* > 0 *and p(X, Y)* = -1 *if a* < O. *If X and Yare independent, then* Cov(X, *Y)* = *P* = O. *The converse is not true in general.* 

**3.20 Theorem.** V(X + *Y)* = V(X) + V(Y) + 2Cov(X, *Y) and* V(X - *Y) <sup>=</sup>* V(X) + V(Y) -2Cov(X, *Y). More generally, for random variables* Xl,"" *X n,* 

$$\mathbb{V}\left(\sum_{i} a_i X_i\right) = \sum_{i} a_i^2 \mathbb{V}(X_i) + 2 \sum_{i < j} \sum_{a_i a_j} \text{Cov}(X_i, X_j).$$

## 3.4 Expectation and Variance of Irnportant Randorn Variables

Here we record the expectation of some important random variables:

| Distribution                        | Mean                    | Variance                                          |
|-------------------------------------|-------------------------|---------------------------------------------------|
| Point mass at $a$                   | a                       |                                                   |
| $\text{Bernoulli}(p)$               | p                       | $p(1-p)$                                          |
| $\text{Binomial}(n, p)$             | np                      | $np(1-p)$                                         |
| $\text{Geometric}(p)$               | 1/p                     | $(1-p)/p^2$                                       |
| $\text{Poisson}(\lambda)$           |                         |                                                   |
| $\text{Uniform}(a, b)$              | $(a+b)/2$               | $(b-a)^2/12$                                      |
| $\text{Normal}(\mu, \sigma^2)$      | $\mu$                   | $\sigma^2$                                        |
| $Exponential(\beta)$                | $\beta$                 | $\beta^2$                                         |
| $\text{Gamma}(\alpha, \beta)$       | $\alpha\beta$           | $\alpha \beta^2$                                  |
| $\text{Beta}(\alpha, \beta)$        | $\alpha/(\alpha+\beta)$ | $\alpha\beta/((\alpha+\beta)^2(\alpha+\beta+1))$  |
| $t_{\nu}$                           |                         | 0 (if $\nu > 1$ ) $\nu/(\nu - 2)$ (if $\nu > 2$ ) |
| $\chi_p^2$                          | p                       | 2p                                                |
| $\text{Multinomial}(n, p)$          | np                      | $\text{see below}$                                |
| Multivariate Normal $(\mu, \Sigma)$ | $\mu$                   | $\Sigma$                                          |

We derived  $\mathbb{E}(X)$  and  $\mathbb{V}(X)$  for the Binomial in the previous section. The calculations for some of the others are in the exercises.

The last two entries in the table are multivariate models which involve a random vector  $X$  of the form

$$X = \left(\begin{array}{c} X_1 \\ \vdots \\ X_k \end{array}\right).$$

The mean of a random vector  $X$  is defined by

$$\mu = \left(\begin{array}{c} \mu_1 \\ \vdots \\ \mu_k \end{array}\right) = \left(\begin{array}{c} \mathbb{E}(X_1) \\ \vdots \\ \mathbb{E}(X_k) \end{array}\right).$$

The variance-covariance matrix  $\Sigma$  is defined to be

$$\mathbb{V}(X) = \begin{bmatrix} \mathbb{V}(X_1) & \operatorname{Cov}(X_1, X_2) & \cdots & \operatorname{Cov}(X_1, X_k) \\ \operatorname{Cov}(X_2, X_1) & \mathbb{V}(X_2) & \cdots & \operatorname{Cov}(X_2, X_k) \\ \vdots & \vdots & \vdots & \vdots \\ \operatorname{Cov}(X_k, X_1) & \operatorname{Cov}(X_k, X_2) & \cdots & \mathbb{V}(X_k) \end{bmatrix}$$

If  $X \sim \text{Multinomial}(n, p)$  then  $\mathbb{E}(X) = np = n(p_1, \dots, p_k)$  and

$$\mathbb{V}(X) = \begin{pmatrix} np_1(1-p_1) & -np_1p_2 & \cdots & -np_1p_k \\ -np_2p_1 & np_2(1-p_2) & \cdots & -np_2p_k \\ \vdots & \vdots & \vdots & \vdots \\ -np_kp_1 & -np_kp_2 & \cdots & np_k(1-p_k) \end{pmatrix}$$

To see this, note that the marginal distribution of anyone component of the vector *Xi* rv Binomial(n,pi)' Thus, lE(Xi) = *npi* and V(Xi) = *npi(l* - *Pi)'*  Note also that *Xi* + *Xj* rv Binomial(n,pi + *Pj).* Thus, V(Xi + *Xj)* = *n(pi + pj)(l* - *[pi* + *Pj]).* On the other hand, using the formula for the variance of a sum, we have that V(Xi + *Xj)* = V(Xi) + *V(Xj)* + 2COV(Xi' *Xj) <sup>=</sup> npi(l* - *Pi)* + *npj(l* - *Pj)* + 2COV(Xi' *Xj)'* If we equate this formula with *n(pi* + *pj)(l* - *[Pi* + *Pj])* and solve, we get COV(Xi' *Xj)* = *-npiPj'* 

Finally, here is a lemma that can be useful for finding means and variances of linear combinations of multivariate random vectors.

**3.21 lemma.** *If a is a vector and X is a random vector with mean It and*  variance~, *thenlE(aTX)* = *aT,t andV(aTX)* = aT~a. *If A is a matrix then lE(AX)* = *AIL and V(AX)* <sup>=</sup>A~AT.

### 3.5 Conditional Expectation

Suppose that *X* and Yare random variables. What is the mean of *X* among those times when *Y* = *y?* The answer is that we compute the mean of *X* as before but we substitute *fXIY(xly)* for *fx(x)* in the definition of expectation.

**3.22 Definition.** The conditional expectation of X given 
$$Y = y$$
 is  

$$\mathbb{E}(X|Y=y) = \begin{cases} \sum x f_{X|Y}(x|y) \, dx & \text{discrete case} \\ \int x f_{X|Y}(x|y) \, dx & \text{continuous case.} \end{cases} \tag{3.13}$$
If  $r(x, y)$  is a function of x and y then  

$$\mathbb{E}(r(X,Y)|Y=y) = \begin{cases} \sum r(x,y) f_{X|Y}(x|y) \, dx & \text{discrete case} \\ \int r(x,y) f_{X|Y}(x|y) \, dx & \text{continuous case.} \end{cases} \tag{3.14}$$

**Warning!** Here is a subtle point. Whereas lE(X) is a number, lE(XIY = *y)*  is a function of *y.* Before we observe *Y,* we don't know the value oflE(XIY = *y)*  so it is a random variable which we denote lE(XIY). In other words, lE(XIY) is the random variable whose value is lE(XIY = *y)* when *Y* = *y.* Similarly, lE(r(X, *Y)IY)* is the random variable whose value is lE(r(X, *Y)IY* = *y)* when *Y* = *y.* This is a very confusing point so let us look at an example.

**3.23 Example.** Suppose we draw *X* rv Unif(O, 1). After we observe *X* = *x,*  we draw *YIX* = *x* rv Unif(x, 1). Intuitively, we expect that lE(YIX = *x) =*  (1 + *x)/2.* **In** fact, *jylx(ylx)* = 1/(1 - *x)* for *x* < *y* < 1 and

$$\mathbb{E}(Y|X=x) = \int_x^1 y \, f_{Y|X}(y|x) dy = \frac{1}{1-x} \int_x^1 y \, dy = \frac{1+x}{2}$$

as expected. Thus, *IE(YIX)* = (1 + *X)/2.* Notice that *IE(YIX)* = (1 + *X)/2* is a random variable whose value is the number *IE(YIX* = *x)* = (1 + *x)/2* once *X* = *x* is observed. \_

**3.24 Theorem** (The Rule of Iterated Expectations). *For random variables X and* Y, *assuming the expectations exist, we have that* 

$$\mathbb{E}\left[\mathbb{E}(Y|X)\right] = \mathbb{E}(Y) \quad \text{and} \quad \mathbb{E}\left[\mathbb{E}(X|Y)\right] = \mathbb{E}(X). \tag{3.15}$$

*More generally, for any function r(x, y) we have* 

$$\mathbb{E}\left[\mathbb{E}(r(X,Y)|X)\right] = \mathbb{E}(r(X,Y)).\tag{3.16}$$

PROOF. We'll prove the first equation. Using the definition of conditional expectation and the fact that *f(x, y)* = *f(x)f(Ylx),* 

$$\begin{array}{rcl} \mathbb{E}\left[\mathbb{E}(Y|X)\right] & = & \int \mathbb{E}(Y|X=x)f_X(x)dx = \int \int yf(y|x)dyf(x)dx \\ \\ & = & \int \int yf(y|x)f(x)dxdy = \int \int yf(x,y)dxdy = \mathbb{E}(Y). \end{array}$$

**3.25 Example.** Consider example 3.23. How can we compute IE(Y)? One method is to find the joint density *f(x, y)* and then compute IE(Y) = *J J yf(x, y)dxdy.*  An easier way is to do this in two steps. First, we already know that *IE(YIX) =*  (1 + *X)* /2. Thus,

$$\mathbb{E}(Y) = \mathbb{E}(Y|X) = \mathbb{E}\left(\frac{(1+X)}{2}\right)$$
$$= \frac{(1+\mathbb{E}(X))}{2} = \frac{(1+(1/2))}{2} = 3/4. \blacksquare$$

**3.26 Definition.** *The* **conditional variance** *is defined as* 

$$\mathbb{V}(Y|X=x) = \int (y-\mu(x))^2 f(y|x) dy \qquad (3.17)$$

*where fL(X)* = *IE(YIX* = *x).* 

**3.27 Theorem.** *For random variables X and* Y,

$$\mathbb{V}(Y) = \mathbb{E}\mathbb{V}(Y|X) + \mathbb{V}\mathbb{E}(Y|X).$$

**3.28 Example.** Draw a county at random from the United States. Then draw *17,* people at random from the county. Let *X* be the number of those people who have a certain disease. If *Q* denotes the proportion of people in that county with the disease, then *Q* is also a random variable since it varies from county to county. Given *Q* = *q,* we have that *X* rv Binomial(n, *q).* Thus, IE(XIQ = *q)* = *nq* and V(XIQ = *q)* = *nq(l* - *q).* Suppose that the random variable *Q* has a Uniform (0,1) distribution. A distribution that is constructed in stages like this is called a **hierarchical model** and can be written as

$$Q \sim \text{Uniform}(0, 1)$$
  
 $X|Q = q \sim \text{Binomial}(n, q).$ 

Now, IE(X) = IEIE(XIQ) = *IE(nQ)* = *nIE(Q)* = *n/2.* Let us compute the variance of *X.* Now, V(X) = IEV(XIQ) + VJE(XIQ). Let's compute these two terms. First, IEV(XIQ) = *IE[nQ(l* - *Q)]* = *nIE(Q(l* - *Q))* = *n I q(l q)f(q)dq* = *n I01 q(l* - *q)dq* = *n/6.* Next, VIE(XIQ) = *V(nQ)* = *n 2V(Q) <sup>n</sup> 2 I(q* - *(1/2))2dq* = *17,2/12.* Hence, V(X) = *(n/6)* + *(n 2/12) .•* 

### **3.6 Moment Generating Functions**

Now we will define the moment generating function which is used for finding moments, for finding the distribution of sums of random variables and which is also used in the proofs of some theorems.

**3.29 Definition.** *The* **moment generating function** MGF, *or* **Laplace transform,** *of X is defined by* 

$$\psi_X(t) = \mathbb{E}(e^{tX}) = \int e^{tx} dF(x)$$

*where t varies over the real numbers.* 

**In** what follows, we assume that the MGF is well defined for all *t* in some open interval around *t* = O. 2

When the MGF is well defined, it can be shown that we can interchange the operations of differentiation and "taking expectation." This leads to

$$\psi'(0) = \left[\frac{d}{dt}\mathbb{E}e^{tX}\right]_{t=0} = \mathbb{E}\left[\frac{d}{dt}e^{tX}\right]_{t=0} = \mathbb{E}\left[Xe^{tX}\right]_{t=0} = \mathbb{E}(X).$$

<sup>2</sup>A related function is the characteristic function, defined by lEt *eitX )* where i = y'=1. This function is always well defined for all *t.* 

By taking *k* derivatives we conclude that *1j)k)* (0) = *JE(Xk).* This gives us a method for computing the moments of a distribution.

**3.30 Example.** Let *X* rv Exp(l). For any t < 1,

$$\psi_X(t) = \mathbb{E}e^{tX} = \int_0^\infty e^{tx}e^{-x}dx = \int_0^\infty e^{(t-1)x}dx = \frac{1}{1-t}.$$

The integral is divergent if t ~ 1. So, *1jJx(t)* = 1/(1 - t) for all *t* < 1. Now, ¢'(O) = 1 and 1/;//(0) = 2. Hence, JE(X) = 1 and V(X) = JE(X2) *-1L2* = 2 -1 = **1..** 

**3.31 Lemma.** *Properties of the* MGF.

*(1) IfY* = *aX* + *b, then¢y(t)* = *ebt¢x(at).* 

*(2) If* Xl"'" *Xn are independent and Y* = *Li Xi, then 1jJy(t)* = ITi *1/;i(t) where 1jJi is the* MGF *of Xi'* 

**3.32 Example.** Let *X* rv Binomial(n,p). We know that *X* = L~=l *Xi* where JP'(Xi = 1) = *p* and JP'(Xi = 0) = 1 - *p.* Now¢i(t) = JEeX;t = *(p* x *et )* + ((1 *p))* = *pet* + *q* where *q* = 1 - *p.* Thus, *1jJx(t)* = ITi *1jJi(t)* = *(pet* + *q)n .•* 

Recall that *X* and Yare equal in distribution if they have the same distribution function and we write *X* ~ *Y.* 

**3.33 Theorem.** *Let X and Y be random variables. If 1/;x(t) =¢y(t) for all t in an open interval around 0, then X* ~ *Y.* 

**3.34 Example.** Let Xl rv Binomial(nl,p) and *X <sup>2</sup>*rv Binomial(n2,p) be independent. Let *Y* = Xl + *X <sup>2</sup> •* Then,

$$\psi_Y(t) = \psi_1(t)\psi_2(t) = (pe^t + q)^{n_1}(pe^t + q)^{n_2} = (pe^t + q)^{n_1 + n_2}$$

and we recognize the latter as the MGF of a Binomial(nl + *n2,p)* distribution. Since the MGF characterizes the distribution (i.e., there can't be another random variable which has the same MGF) we conclude that *Y* rv Binomial(nl + *n2,p) .•* 

| Moment Generating Functions for Some Common Distributions |                                                                                                        |  |
|-----------------------------------------------------------|--------------------------------------------------------------------------------------------------------|--|
| Distribution                                              | MGF $\psi(t)$                                                                                          |  |
| Bernoulli $(p)$ $pe^{t} + (1-p)$                          |                                                                                                        |  |
|                                                           | $\text{Binomial}(n, p) \quad (pe^t + (1 - p))^n$                                                       |  |
| $\text{Poisson}(\lambda)$                                 | $e^{\lambda(e^t-1)}$                                                                                   |  |
| $\text{Normal}(\mu, \sigma)$                              | $\exp\left\{\mu t + \frac{\sigma^2 t^2}{2}\right\}$                                                    |  |
|                                                           | $\text{Gamma}(\alpha, \beta) \quad \left(\frac{1}{1-\beta t}\right)^{\alpha} \text{ for } t < 1/\beta$ |  |
|                                                           |                                                                                                        |  |

**3.35 Example.** Let  $Y_1 \sim \text{Poisson}(\lambda_1)$  and  $Y_2 \sim \text{Poisson}(\lambda_2)$  be independent. The moment generating function of  $Y = Y_1 + Y + 2$  is  $\psi_Y(t) = \psi_{Y_1}(t)\psi_{Y_2}(t) =$  $e^{\lambda_1(e^t-1)}e^{\lambda_2(e^t-1)} = e^{(\lambda_1+\lambda_2)(e^t-1)}$  which is the moment generating function of a Poisson( $\lambda_1 + \lambda_2$ ). We have thus proved that the sum of two independent Poisson random variables has a Poisson distribution.

#### Appendix $3.7$

EXPECTATION AS AN INTEGRAL. The integral of a measurable function  $r(x)$ is defined as follows. First suppose that  $r$  is simple, meaning that it takes finitely many values  $a_1, \ldots, a_k$  over a partition  $A_1, \ldots, A_k$ . Then define

$$\int r(x)dF(x) = \sum_{i=1}^{k} a_i \mathbb{P}(r(X) \in A_i).$$

The integral of a positive measurable function r is defined by  $\int r(x) dF(x) =$  $\lim_{i} \int r_{i}(x) dF(x)$  where  $r_{i}$  is a sequence of simple functions such that  $r_{i}(x) \leq$  $r(x)$  and  $r_i(x) \to r(x)$  as  $i \to \infty$ . This does not depend on the particular sequence. The integral of a measurable function r is defined to be  $\int r(x) dF(x) =$  $\int r^+(x) dF(x) - \int r^-(x) dF(x)$  assuming both integrals are finite, where  $r^+(x) =$  $\max\{r(x), 0\}$  and  $r^-(x) = -\min\{r(x), 0\}.$ 

#### 3.8 Exercises

1. Suppose we play a game where we start with  $c$  dollars. On each play of the game you either double or halve your money, with equal probability. What is your expected fortune after  $n$  trials?

- 2. Show that  $\mathbb{V}(X) = 0$  if and only if there is a constant c such that  $P(X=c) = 1.$
- 3. Let  $X_1, \ldots, X_n \sim \text{Uniform}(0, 1)$  and let  $Y_n = \max\{X_1, \ldots, X_n\}$ . Find  $\mathbb{E}(Y_n).$
- 4. A particle starts at the origin of the real line and moves along the line in jumps of one unit. For each jump the probability is  $p$  that the particle will jump one unit to the left and the probability is  $1-p$  that the particle will jump one unit to the right. Let  $X_n$  be the position of the particle after *n* units. Find  $\mathbb{E}(X_n)$  and  $\mathbb{V}(X_n)$ . (This is known as a **random**  $\text{walk.})$
- 5. A fair coin is tossed until a head is obtained. What is the expected number of tosses that will be required?
- 6. Prove Theorem 3.6 for discrete random variables.
- 7. Let  $X$  be a continuous random variable with CDF  $F$ . Suppose that  $P(X > 0) = 1$  and that  $\mathbb{E}(X)$  exists. Show that  $\mathbb{E}(X) = \int_0^\infty \mathbb{P}(X > 0)$  $x)dx.$

Hint: Consider integrating by parts. The following fact is helpful: if  $\mathbb{E}(X)$ exists then  $\lim_{x\to\infty} x[1-F(x)]=0.$ 

- $8. \text{Prove Theorem 3.17.}$
- 9. (Computer Experiment.) Let  $X_1, X_2, \ldots, X_n$  be  $N(0, 1)$  random variables and let  $\overline{X}_n = n^{-1} \sum_{i=1}^n X_i$ . Plot  $\overline{X}_n$  versus  $n$  for  $n = 1, \ldots, 10, 000$ . Repeat for  $X_1, X_2, \ldots, X_n \sim \text{Cauchy. Explain why there is such a dif$ ference.
- 10. Let  $X \sim N(0, 1)$  and let  $Y = e^X$ . Find  $\mathbb{E}(Y)$  and  $\mathbb{V}(Y)$ .
- 11. (Computer Experiment: Simulating the Stock Market.) Let  $Y_1, Y_2, \ldots$  be independent random variables such that  $P(Y_i = 1) = P(Y_i = -1) =$  $1/2$ . Let  $X_n = \sum_{i=1}^n Y_i$ . Think of  $Y_i = 1$  as "the stock price increased by one dollar",  $Y_i = -1$  as "the stock price decreased by one dollar", and  $X_n$  as the value of the stock on day n.

(a) Find  $\mathbb{E}(X_n)$  and  $\mathbb{V}(X_n)$ .

(b) Simulate  $X_n$  and plot  $X_n$  versus n for  $n = 1, 2, \ldots, 10, 000$ . Repeat the whole simulation several times. Notice two things. First, it's easy to "see" patterns in the sequence even though it is random. Second,

### 60 3. Expectation

you will find that the four runs look very different even though they were generated the same way. How do the calculations in (a) explain the second observation?

- 12. Prove the formulas given in the table at the beginning of Section 3.4 for the Bernoulli, Poisson, Uniform, Exponential, Gamma, and Beta. Here are some hints. For the mean of the Poisson, use the fact that *<sup>e</sup>a* = 2..:::=0 *aX Ix!.* To compute the variance, first compute lE(X(X -1)). For the mean of the Gamma, it will help to multiply and divide by f(a + 1)/;600+1 and use the fact that a Gamma density integrates to l. For the Beta, multiply and divide by r(a + l)f(;6)/f(a +;6 + 1).
- 13. Suppose we generate a random variable X in the following way. First we flip a fair coin. If the coin is heads, take X to have a Unif(O,l) distribution. If the coin is tails, take X to have a Unif(3,4) distribution.
  - (a) Find the mean of X.
  - (b) Find the standard deviation of X.
- 14. Let Xl, ... *,Xm* and Yl , ... , *Yn* be random variables and let al, ... , *am*  and bl , ... *,bn* be constants. Show that

$$\mathsf{Cov}\left(\sum_{i=1}^{m} a_i X_i, \sum_{j=1}^{n} b_j Y_j\right) = \sum_{i=1}^{m} \sum_{j=1}^{n} a_i b_j \mathsf{Cov}(X_i, Y_j).$$

15. Let

$$f_{X,Y}(x,y) = \begin{cases} \frac{1}{3}(x+y) & 0 \le x \le 1, \ 0 \le y \le 2\\ 0 & \text{otherwise.} \end{cases}$$

Find V(2X - *3Y* + 8).

16. Let r(x) be a function of x and let s(y) be a function of y. Show that

$$\mathbb{E}(r(X)s(Y)|X) = r(X)\mathbb{E}(s(Y)|X).$$

Also, show that lE(r(X)IX) = *r(X).* 

17. Prove that

$$\mathbb{V}(Y) = \mathbb{E}\,\mathbb{V}(Y\mid X) + \mathbb{V}\,\mathbb{E}(Y\mid X).$$

Hint: Let m = lE(Y) and let *b(x)* = lE(YIX = *x).* Note that lE(b(X)) = lElE(YIX) = lE(Y) = m. Bear in mind that *b* is a function of *x.* Now write *V(Y)* = lE(Y - *m)2* = lE( *(Y* - *b(X))* + *(b(X)* - *m))2.* Expand the square and take the expectation. You then have to take the expectation of three terms. In each case, use the rule of the iterated expectation:  $\mathbb{E}(\text{stuff}) = \mathbb{E}(\mathbb{E}(\text{stuff}|X)).$ 

- 18. Show that if  $\mathbb{E}(X|Y=y) = c$  for some constant c, then X and Y are uncorrelated.
- 19. This question is to help you understand the idea of a **sampling distribution.** Let  $X_1,\ldots,X_n$  be IID with mean  $\mu$  and variance  $\sigma^2$ . Let  $\overline{X}_n = n^{-1} \sum_{i=1}^n X_i$ . Then  $\overline{X}_n$  is a **statistic**, that is, a function of the data. Since  $\overline{X}_n$  is a random variable, it has a distribution. This distribution is called the *sampling distribution of the statistic*. Recall from Theorem 3.17 that  $\mathbb{E}(\overline{X}_n) = \mu$  and  $\mathbb{V}(\overline{X}_n) = \sigma^2/n$ . Don't confuse the distribution of the data  $f_X$  and the distribution of the statistic  $f_{\overline{X}_n}$ . To make this clear, let  $X_1, \ldots, X_n \sim \text{Uniform}(0, 1)$ . Let  $f_X$  be the density of the Uniform(0,1). Plot  $f_X$ . Now let  $\overline{X}_n = n^{-1} \sum_{i=1}^n X_i$ . Find  $\mathbb{E}(\overline{X}_n)$ and  $\mathbb{V}(\overline{X}_n)$ . Plot them as a function of n. Interpret. Now simulate the distribution of  $\overline{X}_n$  for  $n = 1, 5, 25, 100$ . Check that the simulated values of  $\mathbb{E}(\overline{X}_n)$  and  $\mathbb{V}(\overline{X}_n)$  agree with your theoretical calculations. What do you notice about the sampling distribution of  $\overline{X}_n$  as *n* increases?
- $20.$  Prove Lemma  $3.21.$
- 21. Let X and Y be random variables. Suppose that  $\mathbb{E}(Y|X) = X$ . Show that  $\text{Cov}(X,Y) = \mathbb{V}(X)$ .
- 22. Let  $X \sim \text{Uniform}(0, 1)$ . Let  $0 < a < b < 1$ . Let

$$Y = \begin{cases} 1 & 0 < x < b \\ 0 & \text{otherwise} \end{cases}$$

 $\text{and let}$ 

$$Z = \begin{cases} 1 & a < x < 1 \\ 0 & \text{otherwise} \end{cases}$$

- (a) Are  $Y$  and  $Z$  independent? Why/Why not?
- (b) Find  $\mathbb{E}(Y|Z)$ . Hint: What values  $z \text{ can } Z \text{ take? Now find } \mathbb{E}(Y|Z=z)$ .
- 23. Find the moment generating function for the Poisson, Normal, and  $\text{Gamma distributions.}$
- 24. Let  $X_1, \ldots, X_n \sim \text{Exp}(\beta)$ . Find the moment generating function of  $X_i$ . Prove that  $\sum_{i=1}^{n} X_i \sim \text{Gamma}(n, \beta)$ .