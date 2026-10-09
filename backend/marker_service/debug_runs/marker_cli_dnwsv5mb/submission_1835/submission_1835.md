# Squeezing More from Limited Data with Recursive Transformers

## Anonymous ACL submission

## **<sup>001</sup>** Abstract

 Pre-training under limited data requires a dif- ferent view of scaling than web-scale language modeling. With a fixed data budget but rela- tively abundant compute, increasing parameter count helps only up to an optimal scale; be- yond that point, models overfit and generaliza- tion worsens. We study this behavior across 10M–100M word pre-training budgets, two cor- pora, and multiple downstream evaluations, and find that optimal size depends strongly on both the data budget and the downstream target. We argue that standard Transformers scale down poorly to this setting, because em- beddings consume a large fraction of the pa- rameter budget and per-token computation is tied to representational capacity. To address this coupling, we study recursive Transformers, reusing a shared block across depth to scale compute, together with factorized embeddings to reduce vocabulary-map parameters. We train three recursive models and find that they out- perform standard Transformers at 10M and 100M words, while remaining competitive with BabyLM Challenge 2025 winners.

# **<sup>026</sup>** 1 Introduction

 Most work on language model pre-training has been developed in the web-scale regime, where performance is often improved by scaling model size, compute, and data together [\(Kaplan et al.,](#page-9-0) [2020;](#page-9-0) [Hoffmann et al.,](#page-8-0) [2022\)](#page-8-0). Here, we consider a different setting: pre-training under a limited data budget but relatively abundant compute, where web-scale scaling intuitions do not carry over. In limited-data training, more parameters cannot be paired with more data, so increasing model size changes the bias–variance tradeoff. This makes model size itself a regularization choice.

 This setting is scientifically interesting because it is closer to developmentally motivated data budgets [\(Hu et al.,](#page-9-1) [2024\)](#page-9-1), and practically important because continued scaling of foundation models may be constrained by the supply of high-quality human- **043** generated text [\(Villalobos et al.,](#page-10-0) [2024\)](#page-10-0). **044**

Human language learners are exposed to far less **045** linguistic input than today's language models, and **046** the BabyLM Challenge is designed around this idea **047** by evaluating pre-training under developmentally **048** motivated budgets such as 10M or 100M words **049** [\(Gilkerson et al.,](#page-8-1) [2017;](#page-8-1) [Hu et al.,](#page-9-1) [2024\)](#page-9-1). Naturally, **050** it is a controlled testbed for us to study how models **051** should be designed when data is scarce. **052**

We argue that standard Transformers scale down **053** poorly to this setting. Scaling down standard **054** Transformers reduces parameter count, but it also **055** changes the balance among vocabulary maps, block **056** capacity, and computational depth. At small scales, **057** a fixed vocabulary size means embeddings and the **058** LM head can dominate the parameter budget, and **059** the computation applied to each token can become **060** too limited. This couples per-token computation **061** to representational capacity, even though in this **062** setting we would like to control them separately. **063** We therefore explore architectural ways to break **064** this coupling: factorized embeddings reduce the **065** parameters spent on vocabulary maps, while recur- **066** sive weight sharing lets us increase computational **067** depth without a proportional increase in parameter **068** count. We refer to the resulting model family as **069** RecursiveGPT. **070**

We study the following research questions: **071**

- What sort of bottlenecks make standard lan- **072** guage model architectures scale down poorly **073** to limited-data pre-training budgets? **074**
- How does optimal model size depend on the **075** data budget and downstream evaluation tar- **076** get? **077**
- Can recursive Transformers provide a better **078** path for scaling compute under limited data? **079**

To study these questions, we run experiments span- **080** ning data budgets from 10M to 100M words and **081**  model sizes from 13M to 1.2B parameters, across two corpora and multiple benchmarks. Our results show that data-constrained pre-training behaves dif- ferently from the web-scale regime: the optimal model size depends strongly on both the amount of data and the downstream evaluation, and standard architectures scale down poorly.

 Our central claim is that limited-data pre-training benefits from architectures that decouple repre- sentational capacity from per-token computation; our goal is not to improve compute efficiency, but to provide another compute scaling axis that lets us squeeze out more performance out of limited data. RecursiveGPT provides a simple instance of this principle. Empirically, RecursiveGPT uses this additional computation to outperform standard Transformers at both 10M and 100M word bud- gets, while remaining competitive with BabyLM Challenge 2025 winners.

 We view RecursiveGPT as a useful architectural pathway for scaling up compute under fixed data, while remaining orthogonal to more specialized data-efficient training methods, such as those used in BabyLM. We openly release the training pipeline and models.[1](#page-1-0)

## **<sup>107</sup>** 2 Background

 We focus on the regime where data, rather than computation, is the binding constraint. With a fixed corpus but relatively abundant compute, pa- rameter count becomes a form of regularization: larger models can fit the training corpus more eas- ily, so the natural scaling direction is often to re- duce the number of trainable parameters. This creates a tension with compute. The same knobs that usually buy more computation, such as larger width, greater depth, or more passes over the data, also tend to increase the risk of overfitting. At the BabyLM scale, this compute-abundant view is not merely hypothetical. In the 10M-word setting, competitive models can be trained in minutes on a single GPU (see Appendix [D\)](#page-13-0), making it natural to ask, in the spirit of "The Bitter Lesson" [\(Sutton,](#page-10-1) [2019\)](#page-10-1), how to allocate more compute.

 Another layer to this tension is scaling down standard language model architectures. If vocab- ulary size is held fixed, reducing the hidden di- mension shrinks the Transformer blocks roughly quadratically, while the embedding matrix shrinks

only linearly. As a result, a small language model **130** can spend most of its parameters on token embed- **131** dings rather than on the computation performed at **132** each layer. **133**

Prior work has explored a training-dynamics ap- **134** proach to this problem, keeping models overparam- **135** eterized while controlling overfitting through ag- **136** gressively tuned training recipes, including weight **137** decay far above standard pre-training practice and, **138** in later stages, ensembles of independently trained **139** models [\(Kim et al.,](#page-9-2) [2026\)](#page-9-2). We instead explore an **140** architectural approach to solving this problem, de- **141** signing the model itself to be better-matched to the **142** data-constrained regime. **143**

#### 2.1 BabyLM Challenge **144**

The BabyLM Challenge [\(Hu et al.,](#page-9-1) [2024\)](#page-9-1) studies **145** language model pre-training under developmen- **146** tally plausible data budgets. Its standard tracks **147** restrict training to at most 10M or 100M words for **148** 10 epochs, but do not restrict FLOPs; making it a **149** useful benchmark for the limited-data setting we **150** consider. **151**

The 2025 challenge ranked systems separately **152** by track and by NLP-task versus human-likeness **153** metrics. The NLP track is most relevant for our **154** evaluations; its strict-small winner, AMLM hard **155** decay, is a masked language model that adapts **156** [t](#page-8-2)he masking distribution during training [\(Edman](#page-8-2) **157** [and Fraser,](#page-8-2) [2025\)](#page-8-2). Other strong systems combined **158** causal and masked objectives or used diffusion- **159** [s](#page-8-3)tyle masked language modeling [\(Charpentier and](#page-8-3) **160** [Samuel,](#page-8-3) [2024;](#page-8-3) [Kosmopoulou et al.,](#page-9-3) [2025;](#page-9-3) [Charpen-](#page-8-4) **161** [tier et al.,](#page-8-4) [2025\)](#page-8-4). **162**

Two evaluations used by the challenge that we **163** also use later are BLiMP [\(Warstadt et al.,](#page-10-2) [2020\)](#page-10-2) and **164** COMPS [\(Misra et al.,](#page-9-4) [2023\)](#page-9-4). For comparisons to **165** BabyLM 2025 models later, we also report BLiMP **166** Supplement, EWoK [\(Ivanova et al.,](#page-9-5) [2025\)](#page-9-5), and En- **167** tity Tracking [\(Kim and Schuster,](#page-9-6) [2023\)](#page-9-6), which we **168** treat as supplementary because they appear to be **169** noisier and are less central to our research ques- **170** tions. **171**

## 2.2 Recursive Transformers **172**

A simple way to untie per-token computation from **173** representational capacity is to share weights across **174** depth. Recursive Transformers do this by replac- **175** ing a stack of independently parameterized blocks **176** with repeated applications of a shared transition **177** function. Increasing recurrent depth therefore adds **178** computation between the embedding layer and the **179**

<span id="page-1-0"></span><sup>1</sup>Links to the repository and models will be added upon acceptance.

output head without adding another full set of block parameters. This idea connects several strands of prior work.

180

181

182

185

186

187

189

192 193

194

198

199

209

210

212

213

214

215

216

218

219

224

The Universal Transformer applies a selfattentive transition recurrently across depth, optionally with adaptive halting, and was motivated by combining the parallelism of Transformers with a recurrent inductive bias (Dehghani et al., 2019). ALBERT later showed that factorized embeddings and cross-layer parameter sharing can greatly reduce the parameter count of BERT-style encoders (Lan et al., 2020). Deep Equilibrium Models push weight-tied depth further by solving for the fixed point of an effectively infinite-depth network, including self-attention variants (Bai et al., 2019). More recent recursive-Transformer work has used layer tying and lightweight depth-specific adaptation to compress pretrained language models (Bae et al., 2025), while depth-recurrent language models, such as AbbIE and Huginn, study recurrent unrolling as a way to scale latent test-time computation (Aleksandrov et al., 2025; Geiping et al., 2026).

Recent small recursive reasoning models illustrate the same low-data principle outside language modeling. HRM and TRM solve supervised puzzle tasks by applying compact recurrent modules repeatedly to achieve strong generalization from small training sets (Wang et al., 2025; Jolicoeur-Martineau, 2025).

#### <span id="page-2-0"></span>2.3 Factorized Embeddings

Factorized embedding parameterization unties the embedding size E from the Transformer hidden size H. In the standard parameterization, the input embedding matrix has size  $V \times H$ , where V is the vocabulary size. ALBERT introduced factorized embeddings for parameter efficiency, replacing this matrix with two smaller matrices of size  $V \times E$  and  $E \times H$  (Lan et al., 2020). Equivalently, tokens are first mapped into an E-dimensional embedding space and are then projected into the H-dimensional hidden space used by the Transformer Concretely, for a one-hot token vector  $x_t$ , we compute

$$\text{Embed}_{\text{FE}}(x_t) = x_t W_{\text{emb}} W_{\text{proj}}.$$

Here  $\mathrm{Embed_{FE}}$  denotes the factorized embedding map,  $W_{\mathrm{emb}} \in \mathbf{R}^{V \times E}$  is the token embedding matrix, and  $W_{\mathrm{proj}} \in \mathbf{R}^{E \times H}$  projects into the Transformer hidden space. We use the same factorization

![](_page_2_Picture_7.jpeg)

Figure 1: Standard embeddings use a single  $V \times H$  matrix, while factorized embeddings introduce an embedding-size bottleneck by mapping tokens through an E-dimensional space before projecting to the H-dimensional hidden space. This reduces embedding parameter count when  $E \ll H$  and can act as a useful regularizer.

for the untied language-model head, mapping a hidden state  $h_t$  to vocabulary logits by

229

230

231

232

233

234

235

236

238

239

240

241

242

243

245

246

247

248

249

250

251

252

253

254

255

256

257

258

259

260

261

$$\text{Head}_{\text{FE}}(h_t) = h_t W_{\text{proj}} W_{\text{unembed}},$$

where, for the output head,  $W_{\text{proj}} \in \mathbf{R}^{H \times E}$  and  $W_{\text{unembed}} \in \mathbf{R}^{E \times V}$ . When  $E \ll H$ , each factorized vocabulary map uses O(VE + EH) parameters instead of O(VH) while leaving the hidden size unchanged. This lets us prevent vocabulary maps from dominating the parameter count at very small scales by reducing E independently of H. When we choose E = H, we set  $W_{\text{proj}} = I_H$ , recovering the standard embedding or output-head parameterization.

## <span id="page-2-1"></span>3 Optimal Scale for Standard Transformers Under Data Scarcity

#### 3.1 Scaling Experiment Setup

We first study optimal scale with standard, nonrecursive Transformers. All models use 12 layers, and we sweep hidden sizes from 256 to 3072. To keep embeddings from dominating the parameter budget at the smallest scales, we use factorized embeddings for the three smallest models, setting E to 96, 192, and 352 for H = 256, 384, and 512, respectively. The H=384, E=192 pairing is supported by the factorized-embedding sweep in Appendix E. For all larger models, we set E = H. We train on 10M, 25M, 50M, and 100M-word budgets for 10 epochs using two corpora: the BabyLM baseline corpus used by GPT-BERT (Charpentier and Samuel, 2024), and Nemotron-ClimbMix (Diao et al., 2026). Every 10M words corresponds to roughly 13M BPE tokens. Within each corpus, smaller budgets are constructed as nested, shuffled subsets of larger ones, so scaling dataset size does

<span id="page-3-0"></span>![](_page_3_Figure_0.jpeg)

Figure 2: Optimal scale with standard Transformers on the BabyLM baseline corpus across three representative evaluations. The preferred parameter count depends on the downstream target: BLiMP saturates relatively early, LAMBADA becomes more scale-favoring as dataset size grows, and COMPS continues to benefit from larger models at moderate and high data budgets.

**263** not intentionally change the data mixture. We defer **264** the exact architecture specification to Appendix [B.](#page-11-0)

 We report three representative evaluations in Fig- ure [2:](#page-3-0) BLiMP [\(Warstadt et al.,](#page-10-2) [2020\)](#page-10-2), LAMBADA [p](#page-9-4)ass@5 [\(Paperno et al.,](#page-9-9) [2016\)](#page-9-9), and COMPS [\(Misra](#page-9-4) [et al.,](#page-9-4) [2023\)](#page-9-4). BLiMP and COMPS are evaluated using the BabyLM evaluation pipeline [\(BabyLM,](#page-8-11) [2025\)](#page-8-11). BLiMP is a set of 67 English minimal- pair datasets targeting grammatical phenomena in syntax, morphology, and semantics. COMPS is a minimal-pair benchmark for conceptual prop- erty knowledge and property inheritance, testing whether models assign plausible properties to con- cepts and generalize them across category relations. LAMBADA is a benchmark for broad discourse un- derstanding in which models must predict a missing final word from a passage-level context. We evalu- ate it using pass@5 under gold-prefix scoring: at each continuation position, conditioned on the true preceding tokens, the reference token must appear among the model's top-5 predictions; multi-token continuations must satisfy this at every position.

#### **285** 3.2 Scaling Behavior by Evaluation

 Performance is clearly non-monotonic in parameter count, but the pattern differs substantially across evaluations, as illustrated by Figure [2.](#page-3-0) BLiMP im- proves with scale and then mostly saturates, with the clearest signs of overfitting appearing at the smallest data budgets. In contrast, COMPS contin- ues to benefit from larger parameter counts across much of the range we test, especially at 50M and 100M words, including in regions where BLiMP and low-budget LAMBADA have already flattened or begun to decline.

**297** One plausible explanation is that COMPS tests

<span id="page-3-1"></span>![](_page_3_Figure_7.jpeg)

Figure 3: Final training loss for the standard-model optimal-scale sweep on the BabyLM baseline corpus. The x-axis uses the same parameter counts as Figure [2.](#page-3-0) All data subsets use the same tokenizer and vocabulary, so losses are directly comparable. Training loss keeps falling even when downstream performance saturates or declines.

conceptual property knowledge and property inheri- **298** tance: the model must encode associations between **299** concepts and properties and apply them across cat- **300** egory relations. This makes the task more depen- **301** dent on memorized semantic knowledge from the **302** pre-training corpus. Larger models may therefore **303** continue to improve on COMPS because additional **304** parameters provide useful associative capacity even **305** after broader generalization gains have tapered off. **306** This again shows that the optimal scale depends **307** strongly on the downstream target. **308**

LAMBADA asks the model to predict a held-out **309** word from the preceding context. Its examples are **310** constructed so that the target word is predictable **311** from the semantic context of the full passage, but **312** not from short-range cues alone. This format re- **313** mains close to the language-modeling objective, **314** which may explain why its scaling curves are com- **315** **316** paratively smooth.

 The corresponding final training losses decrease steadily with parameter count (Figure [3\)](#page-3-1), so the downstream declines at small data budgets occur despite better training fit and are consistent with overfitting rather than optimization failure.

 The same qualitative picture appears on Climb- Mix: preferred parameter ranges remain broadly stable despite shifts in absolute scores, suggesting that scale is determined more by data budget and evaluation target than by corpus choice (Appendix Figure [6\)](#page-11-1).

 These results reveal a central obstacle for com- pute scaling under fixed data. Once model size exceeds the data-dependent optimum, spending ad- ditional compute by adding parameters no longer reliably improves generalization and can instead amplify overfitting. Progress in this regime may therefore benefit from an alternative scaling axis: increasing per-token computation without propor- tionally increasing the number of trainable parame-**337** ters.

## <span id="page-4-1"></span>**<sup>338</sup>** 4 RecursiveGPT Architecture

 We use recursive weight sharing as an architectural response to this compute-scaling problem. The ar- chitecture is a recursive causal decoder inspired by ALBERT [\(Lan et al.,](#page-9-7) [2020\)](#page-9-7), in which a shared Transformer block is applied recurrently across depth. Due to optimization difficulties with recur- sive weight sharing, and also to explicitly control depth, we keep the design deliberately simple and use a fixed number of recurrent steps. We return to these tradeoffs in Section [6.](#page-6-0) We refer to this model family as RecursiveGPT. Our approach is illustrated in Figure [4.](#page-4-0) Following the Universal [T](#page-8-5)ransformer view of depth recurrence [\(Dehghani](#page-8-5) [et al.,](#page-8-5) [2019\)](#page-8-5), we describe the model as repeated application of a single causal decoder transition, initialized by the factorized embedding map and read out with the factorized head from Section [2.3:](#page-2-0)

$$h^{(0)} = \text{Embed}_{\text{FE}}(x_t),$$
  

$$h^{(r)} = F_{\theta}(h^{(r-1)}; \phi_r), \quad r = 1, \dots, R,$$
  

$$y_t = \text{Head}_{\text{FE}}(h^{(R)}).$$

 Here F<sup>θ</sup> is the shared Transformer block, θ con- tains the attention and MLP weights reused at ev- ery recurrent step, ϕ<sup>r</sup> denotes the lightweight step- specific normalization parameters, and y<sup>t</sup> denotes the next-token logits produced by the factorized

<span id="page-4-0"></span>![](_page_4_Picture_8.jpeg)

Figure 4: RecursiveGPT architecture. Tokens are processed by applying a shared Transformer block R times. Each recurrent step r uses separate normalization and bias parameters for depth conditioning.

language-model head. In contrast to a standard **362** R-layer Transformer, increasing R therefore adds **363** computation without introducing another full set of **364** block parameters. **365**

Each step still has its own parameterized RM- **366** SNorm modules for the attention sublayer, MLP **367** sublayer, and QK normalization, with additional **368** learned biases on the first two. These per-step **369** normalization parameters act as lightweight depth **370** conditioning, and the learned biases in particular **371** function as a lightweight depth embedding, anal- **372** ogous to the recurrent-step timing signal used by **373** [Dehghani et al.](#page-8-5) [\(2019\)](#page-8-5), while most of the block **374** parameters are shared. **375**

Unless otherwise stated, RecursiveGPT uses the **376** same architectural and training details as the stan- **377** dard models described in Appendix [B;](#page-11-0) the key ar- **378** chitectural change is that the recurrent block shares **379** weights across depth. One exception is the feed- **380** forward sublayer: we use an unusually high expan- **381** sion factor of 16, because MLP neuron count scales **382** linearly with hidden size whereas total parameter **383** count scales quadratically, so simply scaling the **384** hidden size to the desired parameter count would **385** leave the model with too few feed-forward neu- **386** rons. This matters because feed-forward neurons **387** can be interpreted as an associative memory over **388** key–value pairs [\(Zhong et al.,](#page-10-4) [2025\)](#page-10-4). **389**

<span id="page-5-1"></span>![](_page_5_Figure_0.jpeg)

Figure 5: Average accuracy for recursive models with (H, E)=(640, 192) trained with recurrent depth R swept from 4 to 32 on the 10% subset of the 100M BabyLM-baseline corpus from the optimal scale experiment in Section [3.](#page-2-1) The horizontal reference lines mark the three-seed average scores from Table [1](#page-6-1) for the best standard model and an unfactorized standard model with the same hidden size.

## **<sup>390</sup>** 5 Results

 For the recursive experiments, we train three Re- cursiveGPT configurations: (H, E)=(640, 192) with R=16, (H, E)=(1408, 768) with R=24, and (H, E)=(2560, 2560) with R=24. The first con- figuration is trained at 10M words, while the other two are trained at 100M words. Because of com- pute constraints, the 100M-word recursive models remain well below the optimal scale identified in Section [3.](#page-2-1) These models use the same datasets as the BabyLM Challenge GPT-BERT baselines[2](#page-5-0) **400** at the corresponding budgets, so that the results are directly comparable to those baselines. Separately, for the recurrent-depth sweep and comparisons to standard models, we use the same configuration as the 10M model but train on the 10% subset of the 100M BabyLM-baseline corpus used in the scal- ing experiments, enabling direct comparison to the standard-model sweep. We analyze the prediction depth of our largest configuration in Appendix [C.](#page-12-0)

 Figure [5](#page-5-1) shows that, for the 27.6M-parameter recursive model trained on the 10% subset of the 100M BabyLM-baseline corpus from the optimal scale experiments, the average score across the three evaluations improves with recurrent depth up to depth 16 and then declines slightly. The trend is therefore not monotonic: additional recurrent steps increase computation, but they can also make op- timization more difficult. The strongest recursive setting reaches an average score of 46.16, com-

pared with 45.07 for the best standard model from **420** Section [3](#page-2-1) and 44.93 for an unfactorized standard **421** model with the same hidden size. Table [1](#page-6-1) compares **422** recursive models against standard alternatives at **423** both 10M and 100M words. All scores are aver- **424** aged over seeds 0, 1, and 2. Training-time and **425** FLOP estimates for these models are reported in **426** Appendix [D.](#page-13-0) **427**

Overall, the recursive models are highly com- **428** petitive; in the 10M-word setting, our recursive **429** model outperforms both standard models on all **430** three evaluations. At 100M words, the compact **431** 124.0M-parameter RecursiveGPT + FE model per- **432** forms well on BLiMP, exceeding the 1.22B stan- **433** dard model while using about 10% as many param- **434** eters, but trails it on COMPS, LAMBADA, and av- **435** erage score. Scaling the recursive model to 404.1M **436** parameters yields RecursiveGPT-Large, which uses **437** substantially higher compute and reaches the best **438** average score among our models while still being **439** smaller than the 1.22B standard baseline. Together, **440** these results show that recursion provides a useful **441** compute-scaling axis under limited data. **442**

#### <span id="page-5-3"></span>5.1 Comparison to BabyLM 2025 winners **443**

Table [2](#page-6-2) compares our recursive models with strong **444** BabyLM 2025 baselines at both 10M and 100M **445** words on BLiMP, BLiMP Supplement, EWoK, En- **446** tity Tracking, and COMPS. The baselines are the **447** causal GPT-BERT models[3](#page-5-2) and AMLM hard de- **448** cay, the winning masked language model in the **449** 10M-word NLP track. **450**

GPT-BERT is a hybrid causal/masked-language- **451** modeling approach rather than a plain decoder-only **452** [b](#page-8-4)aseline [\(Charpentier and Samuel,](#page-8-3) [2024;](#page-8-3) [Charp-](#page-8-4) **453** [entier et al.,](#page-8-4) [2025\)](#page-8-4). AMLM hard decay keeps a **454** masked-language-modeling objective, but changes **455** the masking distribution during training based on **456** [w](#page-8-2)hich tokens the model already predicts well [\(Ed-](#page-8-2) **457** [man and Fraser,](#page-8-2) [2025\)](#page-8-2). Our goal is not to compete **458** with these specialized recipes, but to establish Re- **459** cursiveGPT as a strong architectural blueprint. **460**

For this comparison, the recursive models use the **461** same datasets as GPT-BERT at the corresponding **462** budgets; the 10M model is therefore trained on the **463** BabyLM 10M corpus rather than the 10% subset **464** used for the depth sweep. **465**

At 10M words, RecursiveGPT achieves the **466** strongest BLiMP and EWoK scores, while AMLM **467** achieves the strongest COMPS and average scores. **468**

<span id="page-5-0"></span><sup>2</sup>The models compared here are not the ones introduced in the GPT-BERT paper, which do not satisfy the 10-epoch limit, but the ones submitted to BabyLM 2025.

<span id="page-5-2"></span><sup>3</sup>Causal refers to the causal-focus model evaluated in causal mode.

<span id="page-6-1"></span>

| Word Budget | Model                     | Params | BLiMP | COMPS | LAMBADA p@5 | Average |
|-------------|---------------------------|--------|-------|-------|-------------|---------|
| 10M         | Standard                  | 41.1M  | 68.97 | 52.88 | 12.93       | 44.93   |
| 10M         | Standard + FE             | 28.7M  | 70.09 | 52.62 | 12.48       | 45.07   |
| 10M         | RecursiveGPT + FE (R=16)  | 27.6M  | 70.95 | 52.96 | 13.48       | 45.80   |
| 100M        | Standard                  | 1.22B  | 79.71 | 60.65 | 50.04       | 63.47   |
| 100M        | RecursiveGPT + FE (R=24)  | 124.0M | 80.06 | 58.70 | 47.01       | 61.92   |
| 100M        | RecursiveGPT-Large (R=24) | 404.1M | 80.70 | 60.31 | 50.77       | 63.93   |

Table 1: Comparison between standard and recursive models at 10M and 100M words. FE denotes factorized embeddings and R denotes recurrent depth. The 10M rows include the best standard model from Section [3](#page-2-1) with H=384, an unfactorized H=384, E=384 model, and a depth-16 recursive model with factorized embeddings, all trained on the same 10% subset of the 100M BabyLM-baseline corpus used in the standard-model sweep. All rows are averaged over seeds 0, 1, and 2. The 100M standard row reports the best standard model by average score. Evaluation scores are reported as percentages; Average is the arithmetic mean across the three evaluations.

<span id="page-6-2"></span>

| Word Budget | Model              | Params | BLiMP | BLiMP S. | EWoK  | Entity T. | COMPS | Average |
|-------------|--------------------|--------|-------|----------|-------|-----------|-------|---------|
| 10M         | GPT-BERT (Causal)  | 31.0M  | 71.70 | 63.20    | 49.50 | 34.60     | 52.80 | 54.36   |
| 10M         | AMLM Hard Decay    | 34.7M  | 71.40 | 59.20    | 51.00 | 44.20     | 54.20 | 56.00   |
| 10M         | RecursiveGPT + FE  | 27.6M  | 72.21 | 58.28    | 52.01 | 24.51     | 53.33 | 52.07   |
| 100M        | GPT-BERT (Causal)  | 120.0M | 79.30 | 70.40    | 52.30 | 30.90     | 58.30 | 58.24   |
| 100M        | RecursiveGPT + FE  | 124.0M | 80.06 | 70.82    | 54.74 | 34.42     | 58.70 | 59.75   |
| 100M        | RecursiveGPT-Large | 404.1M | 80.70 | 70.75    | 54.97 | 32.67     | 60.31 | 59.88   |

Table 2: Comparison to the BabyLM 2025 GPT-BERT causal baselines [\(Charpentier and Samuel,](#page-8-3) [2024\)](#page-8-3), the highest-scoring causal models on both tracks [\(Charpentier et al.,](#page-8-4) [2025\)](#page-8-4), and AMLM hard decay, the winning masked language model in the 10M-word NLP track [\(Edman and Fraser,](#page-8-2) [2025\)](#page-8-2). RecursiveGPT scores are averaged over seeds 0, 1, and 2. Entity T. denotes Entity Tracking, and BLiMP S. denotes BLiMP Supplement. Scores are reported as percentages; Average is the arithmetic mean across the five evaluations.

 The main weak point for RecursiveGPT is Entity Tracking, but we treat that benchmark with caution: even GPT-BERT scores higher on Entity Track- ing at 10M words than at 100M words, which is counterintuitive for a data-scaling comparison. At 100M words, both RecursiveGPT models out- perform GPT-BERT on every reported benchmark and on the overall average. RecursiveGPT-Large gives the best BLiMP, EWoK, COMPS, and aver- age scores, while the smaller RecursiveGPT + FE model is slightly stronger on BLiMP Supplement and Entity Tracking. Overall, the recursive archi- tecture remains competitive with strong BabyLM models for both tracks.

## <span id="page-6-3"></span>**483** 5.2 Ablations

 Table [3](#page-7-0) ablates two components of the 10M-word depth-16 RecursiveGPT model from Table [1,](#page-6-1) us- ing the same 10% subset of the 100M BabyLM- baseline corpus. Sharing normalization parameters across recurrent steps slightly improves BLiMP, but reduces the other two evaluation scores and the overall average. Removing factorized embeddings hurts substantially, even when reducing the size of the model further to match parameter counts. The drop is larger than the corresponding gap between factorized and unfactorized standard models in Table [1,](#page-6-1) suggesting that the embedding bottleneck **495** is especially useful for the recursive model at this **496** scale. The difference in the normalization ablation **497** is smaller, indicating that depth conditioning is less **498** important than we anticipated. **499**

## 5.3 Compute-Matched Standard **500** Transformers **501**

The standard-model sweep shows that, under fixed **502** data, increasing parameter count beyond the best **503** scale reduces downstream performance. Another **504** axis of scaling compute is epoch count. We test this **505** by matching the FLOPs of the RecursiveGPT mod- **506** els by training standard models for more epochs. **507** We show that this results in degraded performance **508** at both word budgets in Appendix [F.](#page-14-0) **509**

## <span id="page-6-0"></span>6 Discussion **<sup>510</sup>**

The comparisons to BabyLM winners in Sec- **511** tion [5.1](#page-5-3) should not be read as positioning recursive **512** Transformers against specialized training recipes **513** or objectives. Our contribution is architectural: fac- **514** torized embeddings and recursive weight sharing **515** address parameter allocation and compute-depth **516** coupling, providing a pathway for scaling up com- **517** pute under fixed data. These architectural changes **518** are largely orthogonal to the specialized training **519**

<span id="page-7-0"></span>

| Variant                             | Params | BLiMP | COMPS | LAMBADA p@5 | Average |
|-------------------------------------|--------|-------|-------|-------------|---------|
| RecursiveGPT + FE (H, E)=(640, 192) | 27.6M  | 70.85 | 53.16 | 14.46       | 46.16   |
| Shared norm parameters              | 27.6M  | 71.38 | 52.83 | 13.97       | 46.06   |
| No Factorized Embeddings (H=640)    | 56.7M  | 68.13 | 52.75 | 13.81       | 44.90   |
| No Factorized Embeddings (H=384)    | 30.5M  | 68.70 | 52.41 | 11.17       | 44.09   |

Table 3: Ablations of the 10M-word depth-16 RecursiveGPT model trained on the 10% subset of the 100M BabyLM-baseline corpus with seed 0. FE denotes factorized embeddings. Shared norm parameters shares the normalization parameters across recurrent steps instead of using step-specific normalization and bias. No FE removes factorized input and output vocabulary maps. Scores are reported as percentages; Average is the arithmetic mean across the three evaluations.

 techniques used in GPT-BERT and AMLM hard decay. We therefore view RecursiveGPT as a use- ful architectural base on which more specialized data-efficient training methods can be built.

 Recursive weight sharing makes optimization more delicate. Because the same block is applied many times, small changes in the recurrent transi- tion can be amplified across depth; at the same time, if the transition is too close to an identity or a fixed point, additional recurrent steps may add little use- ful computation. This tension is consistent with the depth sweep in Figure [5,](#page-5-1) where performance im- proves up to R=16 and then drops slightly at larger depths. It is also related to known stability issues in deep Transformers, where residual-branch depen- dence can amplify parameter perturbations during training [\(Liu et al.,](#page-9-10) [2020\)](#page-9-10). Recent work has ana- lyzed this stability problem by treating recursive ar- chitectures as dynamical systems over the residual stream and linking instability to residual explosion, loss spikes, and large injection-parameter spectral norms [\(Prairie et al.,](#page-9-11) [2026\)](#page-9-11).

 Recursive Transformers also make it possible to control computation dynamically. Adaptive com- putation time (ACT) lets recurrent models learn when to halt [\(Graves,](#page-8-12) [2016\)](#page-8-12), so easier token posi- tions could use less compute at inference. During batched Transformer training, savings are less di- rect because token positions are processed in par- allel and the batch typically runs until the deepest active position halts. Depth scheduling is a simpler training-time alternative, starting with fewer recur- rent steps and increasing depth later. As discussed in Section [4,](#page-4-1) we do not use either technique here, but Appendix [C](#page-12-0) shows that many predictions set- tle before the final recurrent step, suggesting that adaptive or scheduled computation could reduce cost in future recursive models.

## 7 Conclusion **<sup>558</sup>**

We studied language model pre-training in a data- **559** limited, compute-abundant regime. Across 10M– **560** 100M word budgets, two corpora, and multiple **561** evaluations, standard decoder-only Transformers **562** often show non-monotonic performance with pa- **563** rameter count, and the best model size depends on **564** both the data budget and the downstream target. **565**

This behavior reflects an architectural mismatch. **566** Under a fixed data budget, the usual ways of giv- **567** ing a standard Transformer more compute also add **568** trainable capacity, and pushing along this coupled **569** scaling axis eventually hurts performance. Recur- **570** siveGPT addresses this mismatch by turning re- **571** current depth into a compute-scaling axis that is **572** decoupled from parameter count. This lets us scale **573** up compute and extract more performance from the **574** available data at both budgets we evaluate. **575**

RecursiveGPT is also competitive with strong **576** BabyLM 2025 models, improving over the causal **577** GPT-BERT baseline on all 100M-word evaluations **578** and remaining close to the best 10M-word mod- **579** els despite using a simple causal objective. More **580** broadly, our results suggest that limited-data pre- **581** training should be treated as its own scaling regime: **582** rather than simply shrinking web-scale architec- **583** tures, we should develop methods whose inductive **584** biases and scaling behavior are better matched to **585** the constraints of limited data. **586**

#### 7.1 Future Work **587**

An immediate next step is to combine recursive ar- **588** chitectures with the specialized objectives and train- **589** ing recipes that have proven effective in BabyLM. **590** The design space of recursion itself is also much **591** broader than the single-block, fixed-depth mod- **592** els studied here. Adaptive halting, depth schedul- **593** ing, partial sharing, and richer depth-conditioning **594** mechanisms could preserve the benefits of recur- **595** rence while reducing training and inference cost. **596**

## **<sup>597</sup>** Limitations

 Our hyperparameter tuning for experiments was limited. We tuned learning rates, optimizer settings, and architectural details locally to obtain stable and competitive runs, but did not retune hyperparam- eters separately for every combination of corpus, data budget, model size, and recurrent depth. Such a full search would be computationally infeasible with our resources.

 Our study also covers only a small part of the recursive Transformer design space. Our models use a single shared block, a fixed number of re- current steps, and simple per-depth conditioning parameters. Without efficiency mechanisms such as adaptive computation time or depth scheduling, increasing recurrent depth substantially increases training and inference cost.

## **<sup>614</sup>** References

- <span id="page-8-8"></span>**615** Preslav Aleksandrov, Meghdad Kurmanji, Fernando **616** Garcia Redondo, David O'Shea, William Shen, Alex **617** Iacob, Lorenzo Sani, Xinchi Qiu, Nicola Cancedda, **618** and Nicholas D. Lane. 2025. [AbbIE: Autoregressive](https://doi.org/10.48550/arXiv.2507.08567) **619** [block-based iterative encoder for efficient sequence](https://doi.org/10.48550/arXiv.2507.08567) **620** [modeling.](https://doi.org/10.48550/arXiv.2507.08567) *arXiv preprint arXiv:2507.08567*.
- <span id="page-8-11"></span>**621** BabyLM. 2025. BabyLM challenge evalua-**622** tion pipeline. [https://github.com/babylm/](https://github.com/babylm/evaluation-pipeline-2025) **623** [evaluation-pipeline-2025](https://github.com/babylm/evaluation-pipeline-2025). GitHub repository.
- <span id="page-8-7"></span>**624** Sangmin Bae, Adam Fisch, Hrayr Harutyunyan, Ziwei **625** Ji, Seungyeon Kim, and Tal Schuster. 2025. [Relaxed](https://openreview.net/forum?id=WwpYSOkkCt) **626** [recursive transformers: Effective parameter sharing](https://openreview.net/forum?id=WwpYSOkkCt) **627** [with layer-wise loRA.](https://openreview.net/forum?id=WwpYSOkkCt) In *The Thirteenth Interna-***628** *tional Conference on Learning Representations*.
- <span id="page-8-6"></span>**629** Shaojie Bai, J. Zico Kolter, and Vladlen Koltun. 2019. **630** Deep equilibrium models. In *Proceedings of the* **631** *33rd International Conference on Neural Information* **632** *Processing Systems*, Red Hook, NY, USA. Curran **633** Associates Inc.
- <span id="page-8-4"></span>**634** Lucas Charpentier, Leshem Choshen, Ryan Cotterell, **635** Mustafa Omer Gul, Michael Y. Hu, Jing Liu, Jaap **636** Jumelet, Tal Linzen, Aaron Mueller, Candace Ross, **637** Raj Sanjay Shah, Alex Warstadt, Ethan Gotlieb **638** Wilcox, and Adina Williams. 2025. [Findings of](https://doi.org/10.18653/v1/2025.babylm-main.28) **639** [the third BabyLM challenge: Accelerating language](https://doi.org/10.18653/v1/2025.babylm-main.28) **640** [modeling research with cognitively plausible data.](https://doi.org/10.18653/v1/2025.babylm-main.28) In **641** *Proceedings of the First BabyLM Workshop*, pages **642** 399–420, Suzhou, China. Association for Computa-**643** tional Linguistics.
- <span id="page-8-3"></span>**644** Lucas Georges Gabriel Charpentier and David Samuel. **645** 2024. [GPT or BERT: why not both?](https://aclanthology.org/2024.conll-babylm.24/) In *The 2nd* **646** *BabyLM Challenge at the 28th Conference on Com-***647** *putational Natural Language Learning*, pages 262– **648** 283, Miami, FL, USA. Association for Computa-**649** tional Linguistics.

- <span id="page-8-15"></span>Lizhang Chen, Jonathan Li, Kaizhao Liang, Baiyu Su, **650** Cong Xie, Chen Liang, Ni Lao, and qiang liu. 2026. **651** [Cautious weight decay.](https://openreview.net/forum?id=Gwe6gbGng5) In *The Fourteenth Interna-* **652** *tional Conference on Learning Representations*. **653**
- <span id="page-8-14"></span>[T](https://openreview.net/forum?id=mZn2Xyh9Ec)ri Dao. 2024. [Flashattention-2: Faster attention with](https://openreview.net/forum?id=mZn2Xyh9Ec) **654** [better parallelism and work partitioning.](https://openreview.net/forum?id=mZn2Xyh9Ec) In *The* **655** *Twelfth International Conference on Learning Repre-* **656** *sentations*. **657**
- <span id="page-8-5"></span>Mostafa Dehghani, Stephan Gouws, Oriol Vinyals, **658** Jakob Uszkoreit, and Lukasz Kaiser. 2019. [Universal](https://openreview.net/forum?id=HyzdRiR9Y7) **659** [transformers.](https://openreview.net/forum?id=HyzdRiR9Y7) In *International Conference on Learn-* **660** *ing Representations*. **661**
- <span id="page-8-10"></span>Shizhe Diao, Yu Yang, Yonggan Fu, Xin Dong, **662** Dan SU, Markus Kliegl, ZIJIA CHEN, Peter Bel- **663** cak, Yoshi Suhara, Hongxu Yin, Mostofa Patwary, **664** Yingyan Celine Lin, Jan Kautz, and Pavlo Molchanov. **665** 2026. [Nemotron-CLIMB: Clustering-based iterative](https://openreview.net/forum?id=aBlqKPkc4a) **666** [data mixture bootstrapping for language model pre-](https://openreview.net/forum?id=aBlqKPkc4a) **667** [training.](https://openreview.net/forum?id=aBlqKPkc4a) In *The Thirty-ninth Annual Conference on* **668** *Neural Information Processing Systems Datasets and* **669** *Benchmarks Track*. **670**
- <span id="page-8-2"></span>[L](https://doi.org/10.18653/v1/2025.babylm-main.31)ukas Edman and Alexander Fraser. 2025. [Mask and](https://doi.org/10.18653/v1/2025.babylm-main.31) **671** [you shall receive: Optimizing masked language mod-](https://doi.org/10.18653/v1/2025.babylm-main.31) **672** [eling for pretraining BabyLMs.](https://doi.org/10.18653/v1/2025.babylm-main.31) In *Proceedings of* **673** *the First BabyLM Workshop*, pages 445–453, Suzhou, **674** China. Association for Computational Linguistics. **675**
- <span id="page-8-9"></span>Jonas Geiping, Sean Michael McLeish, Neel Jain, John **676** Kirchenbauer, Siddharth Singh, Brian R. Bartold- **677** son, Bhavya Kailkhura, Abhinav Bhatele, and Tom **678** Goldstein. 2026. [Scaling up test-time compute with](https://openreview.net/forum?id=S3GhJooWIC) **679** [latent reasoning: A recurrent depth approach.](https://openreview.net/forum?id=S3GhJooWIC) In *The* **680** *Thirty-ninth Annual Conference on Neural Informa-* **681** *tion Processing Systems*. **682**
- <span id="page-8-1"></span>Jill Gilkerson, Jeffrey A. Richards, Steven F. Warren, Ju- **683** dith K. Montgomery, Charles R. Greenwood, D. Kim- **684** brough Oller, John H. L. Hansen, and Terrance D. **685** Paul. 2017. [Mapping the early language environ-](https://doi.org/10.1044/2016_AJSLP-15-0169) **686** [ment using all-day recordings and automated analy-](https://doi.org/10.1044/2016_AJSLP-15-0169) **687** [sis.](https://doi.org/10.1044/2016_AJSLP-15-0169) *American Journal of Speech-Language Pathol-* **688** *ogy*, 26(2):248–265. **689**
- <span id="page-8-12"></span>[A](https://arxiv.org/abs/1603.08983)lex Graves. 2016. [Adaptive computation time](https://arxiv.org/abs/1603.08983) **690** [for recurrent neural networks.](https://arxiv.org/abs/1603.08983) *arXiv preprint* **691** *arXiv:1603.08983*. **692**
- <span id="page-8-13"></span>Alex Henry, Prudhvi Raj Dachapally, Shubham Shan- **693** taram Pawar, and Yuxuan Chen. 2020. [Query-key](https://doi.org/10.18653/v1/2020.findings-emnlp.379) **694** [normalization for transformers.](https://doi.org/10.18653/v1/2020.findings-emnlp.379) In *Findings of the* **695** *Association for Computational Linguistics: EMNLP* **696** *2020*, pages 4246–4253, Online. Association for **697** Computational Linguistics. **698**
- <span id="page-8-0"></span>Jordan Hoffmann, Sebastian Borgeaud, Arthur Mensch, **699** Elena Buchatskaya, Trevor Cai, Eliza Rutherford, **700** Diego de Las Casas, Lisa Anne Hendricks, Johannes **701** Welbl, Aidan Clark, Tom Hennigan, Eric Noland, **702** Katie Millican, George van den Driessche, Bogdan **703** Damoc, Aurelia Guy, Simon Osindero, Karen Si- **704** monyan, Erich Elsen, and 3 others. 2022. Training **705**

 compute-optimal large language models. In *Proceed- ings of the 36th International Conference on Neu- ral Information Processing Systems*, NIPS '22, Red Hook, NY, USA. Curran Associates Inc.

<span id="page-9-1"></span> Michael Y. Hu, Aaron Mueller, Candace Ross, Ad- ina Williams, Tal Linzen, Chengxu Zhuang, Ryan Cotterell, Leshem Choshen, Alex Warstadt, and Ethan Gotlieb Wilcox. 2024. [Findings of the sec-](https://aclanthology.org/2024.conll-babylm.1/) [ond BabyLM challenge: Sample-efficient pretraining](https://aclanthology.org/2024.conll-babylm.1/) [on developmentally plausible corpora.](https://aclanthology.org/2024.conll-babylm.1/) In *The 2nd BabyLM Challenge at the 28th Conference on Com- putational Natural Language Learning*, pages 1–21, Miami, FL, USA. Association for Computational Lin-guistics.

<span id="page-9-5"></span> Anna A. Ivanova, Aalok Sathe, Benjamin Lipkin, Un- nathi U. Kumar, Setayesh Radkani, Thomas H. Clark, Carina Kauf, Jennifer Hu, R. T. Pramod, Gabriel Grand, Vivian C. Paulun, Maria Ryskina, Ekin Akyürek, Ethan G. Wilcox, Nafisa Rashid, Leshem Choshen, Roger Levy, Evelina Fedorenko, Joshua Tenenbaum, and Jacob Andreas. 2025. [Elements of](https://doi.org/10.1162/tacl.a.38) [world knowledge \( EWoK \): A cognition-inspired](https://doi.org/10.1162/tacl.a.38) [framework for evaluating basic world knowledge in](https://doi.org/10.1162/tacl.a.38) [language models.](https://doi.org/10.1162/tacl.a.38) *Transactions of the Association for Computational Linguistics*, 13:1245–1270.

<span id="page-9-8"></span>**731** [A](https://arxiv.org/abs/2510.04871)lexia Jolicoeur-Martineau. 2025. [Less is more: Re-](https://arxiv.org/abs/2510.04871)**732** [cursive reasoning with tiny networks.](https://arxiv.org/abs/2510.04871) *Preprint*, **733** arXiv:2510.04871.

<span id="page-9-15"></span> Keller Jordan, Yuchen Jin, Vlado Boza, Jiacheng You, Franz Cesista, Laker Newhouse, and Jeremy Bern- stein. 2024. [Muon: An optimizer for hidden layers](https://kellerjordan.github.io/posts/muon/) [in neural networks.](https://kellerjordan.github.io/posts/muon/)

<span id="page-9-0"></span> Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. 2020. [Scaling laws for neural language models.](https://arxiv.org/abs/2001.08361) *Preprint*, arXiv:2001.08361.

<span id="page-9-14"></span>**743** Andrej Karpathy. 2025. rustbpe: The missing tiktoken **744** training code. [https://github.com/karpathy/](https://github.com/karpathy/rustbpe) **745** [rustbpe](https://github.com/karpathy/rustbpe). GitHub repository.

<span id="page-9-2"></span> Konwoo Kim, Suhas Kotha, Percy Liang, and Tatsunori Hashimoto. 2026. [Pre-training under infinite com-](https://openreview.net/forum?id=ck0aZTAnwK) [pute.](https://openreview.net/forum?id=ck0aZTAnwK) In *The Fourteenth International Conference on Learning Representations*.

<span id="page-9-6"></span> [N](https://doi.org/10.18653/v1/2023.acl-long.213)ajoung Kim and Sebastian Schuster. 2023. [Entity](https://doi.org/10.18653/v1/2023.acl-long.213) [tracking in language models.](https://doi.org/10.18653/v1/2023.acl-long.213) In *Proceedings of the 61st Annual Meeting of the Association for Compu- tational Linguistics (Volume 1: Long Papers)*, pages 3835–3855, Toronto, Canada. Association for Com-putational Linguistics.

<span id="page-9-17"></span>**756** [D](https://api.semanticscholar.org/CorpusID:6628106)iederik P. Kingma and Jimmy Ba. 2014. [Adam:](https://api.semanticscholar.org/CorpusID:6628106) **757** [A method for stochastic optimization.](https://api.semanticscholar.org/CorpusID:6628106) *CoRR*, **758** abs/1412.6980.

<span id="page-9-3"></span>**759** Despoina Kosmopoulou, Efthymios Georgiou, Vaggelis **760** Dorovatas, Georgios Paraskevopoulos, and Alexan-**761** dros Potamianos. 2025. [Masked diffusion language](https://doi.org/10.18653/v1/2025.babylm-main.38)

[models with frequency-informed training.](https://doi.org/10.18653/v1/2025.babylm-main.38) In *Pro-* **762** *ceedings of the First BabyLM Workshop*, pages 531– **763** 539, Suzhou, China. Association for Computational **764** Linguistics. **765**

<span id="page-9-7"></span>Zhenzhong Lan, Mingda Chen, Sebastian Goodman, **766** Kevin Gimpel, Piyush Sharma, and Radu Soricut. **767** 2020. [ALBERT: A lite BERT for self-supervised](https://openreview.net/forum?id=H1eA7AEtvS) **768** [learning of language representations.](https://openreview.net/forum?id=H1eA7AEtvS) In *8th Inter-* **769** *national Conference on Learning Representations,* **770** *ICLR 2020, Addis Ababa, Ethiopia, April 26-30,* **771** *2020*. OpenReview.net. **772**

<span id="page-9-16"></span>Zichong Li, Liming Liu, Chen Liang, Weizhu Chen, **773** and Tuo Zhao. 2025. [Normuon: Making muon more](https://arxiv.org/abs/2510.05491) **774** [efficient and scalable.](https://arxiv.org/abs/2510.05491) *Preprint*, arXiv:2510.05491. **775**

<span id="page-9-10"></span>Liyuan Liu, Xiaodong Liu, Jianfeng Gao, Weizhu Chen, **776** and Jiawei Han. 2020. [Understanding the difficulty](https://doi.org/10.18653/v1/2020.emnlp-main.463) **777** [of training transformers.](https://doi.org/10.18653/v1/2020.emnlp-main.463) In *Proceedings of the 2020* **778** *Conference on Empirical Methods in Natural Lan-* **779** *guage Processing (EMNLP)*, pages 5747–5763, On- **780** line. Association for Computational Linguistics. **781**

<span id="page-9-4"></span>Kanishka Misra, Julia Rayz, and Allyson Ettinger. 2023. **782** [COMPS: Conceptual minimal pair sentences for test-](https://doi.org/10.18653/v1/2023.eacl-main.213) **783** [ing robust property knowledge and its inheritance in](https://doi.org/10.18653/v1/2023.eacl-main.213) **784** [pre-trained language models.](https://doi.org/10.18653/v1/2023.eacl-main.213) In *Proceedings of the* **785** *17th Conference of the European Chapter of the As-* **786** *sociation for Computational Linguistics*, pages 2928– **787** 2949, Dubrovnik, Croatia. Association for Computa- **788** tional Linguistics. **789**

<span id="page-9-18"></span>nostalgebraist. 2020. Interpreting gpt: the **790** logit lens. [https://www.lesswrong.](https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens) **791** [com/posts/AcKRB8wDpdaN6v6ru/](https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens) **792** [interpreting-gpt-the-logit-lens](https://www.lesswrong.com/posts/AcKRB8wDpdaN6v6ru/interpreting-gpt-the-logit-lens). **793**

<span id="page-9-9"></span>Denis Paperno, Germán Kruszewski, Angeliki Lazari- **794** dou, Ngoc Quan Pham, Raffaella Bernardi, Sandro **795** Pezzelle, Marco Baroni, Gemma Boleda, and Raquel **796** Fernández. 2016. [The LAMBADA dataset: Word](https://doi.org/10.18653/v1/P16-1144) **797** [prediction requiring a broad discourse context.](https://doi.org/10.18653/v1/P16-1144) In **798** *Proceedings of the 54th Annual Meeting of the As-* **799** *sociation for Computational Linguistics (Volume 1:* **800** *Long Papers)*, pages 1525–1534, Berlin, Germany. **801** Association for Computational Linguistics. **802**

<span id="page-9-11"></span>Hayden Prairie, Zachary Novack, Taylor Berg- **803** Kirkpatrick, and Daniel Y. Fu. 2026. [Parcae: Scal-](https://doi.org/10.48550/arXiv.2604.12946) **804** [ing laws for stable looped language models.](https://doi.org/10.48550/arXiv.2604.12946) *arXiv* **805** *preprint arXiv:2604.12946*. **806**

<span id="page-9-13"></span>Zihan Qiu, Zekun Wang, Bo Zheng, Zeyu Huang, **807** Kaiyue Wen, Songlin Yang, Rui Men, Le Yu, Fei **808** Huang, Suozhi Huang, Dayiheng Liu, Jingren Zhou, **809** and Junyang Lin. 2026. [Gated attention for large lan-](https://openreview.net/forum?id=1b7whO4SfY) **810** [guage models: Non-linearity, sparsity, and attention-](https://openreview.net/forum?id=1b7whO4SfY) **811** [sink-free.](https://openreview.net/forum?id=1b7whO4SfY) In *The Thirty-ninth Annual Conference on* **812** *Neural Information Processing Systems*. **813**

<span id="page-9-12"></span>Jianlin Su, Murtadha Ahmed, Yu Lu, Shengfeng Pan, **814** Wen Bo, and Yunfeng Liu. 2024. [Roformer: En-](https://doi.org/10.1016/j.neucom.2023.127063) **815** [hanced transformer with rotary position embedding.](https://doi.org/10.1016/j.neucom.2023.127063) **816** *Neurocomput.*, 568(C). **817** <span id="page-10-1"></span> Richard S. Sutton. 2019. The bitter lesson. [http://www.incompleteideas.net/IncIdeas/](http://www.incompleteideas.net/IncIdeas/BitterLesson.html) [BitterLesson.html](http://www.incompleteideas.net/IncIdeas/BitterLesson.html).

<span id="page-10-5"></span> Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia Polosukhin. 2017. Attention is all you need. In *Proceedings of the 31st International Conference on Neural Information Processing Sys- tems*, NIPS'17, page 6000–6010, Red Hook, NY, USA. Curran Associates Inc.

<span id="page-10-0"></span> Pablo Villalobos, Anson Ho, Jaime Sevilla, Tamay Be- siroglu, Lennart Heim, and Marius Hobbhahn. 2024. Position: will we run out of data? limits of llm scal- ing based on human-generated data. In *Proceed- ings of the 41st International Conference on Machine Learning*, ICML'24. JMLR.org.

<span id="page-10-3"></span> Guan Wang, Jin Li, Yuhao Sun, Xing Chen, Changling Liu, Yue Wu, Meng Lu, Sen Song, and Yasin Ab- basi Yadkori. 2025. [Hierarchical reasoning model.](https://arxiv.org/abs/2506.21734) *Preprint*, arXiv:2506.21734.

<span id="page-10-2"></span> Alex Warstadt, Alicia Parrish, Haokun Liu, Anhad Mo- hananey, Wei Peng, Sheng-Fu Wang, and Samuel R. Bowman. 2020. [BLiMP: The benchmark of linguis-](https://doi.org/10.1162/tacl_a_00321) [tic minimal pairs for English.](https://doi.org/10.1162/tacl_a_00321) *Transactions of the Association for Computational Linguistics*, 8:377– 392.

<span id="page-10-4"></span> Shu Zhong, Mingyu Xu, Tenglong Ao, and Guang Shi. 2025. [Understanding transformer from the](https://arxiv.org/abs/2505.19488) [perspective of associative memory.](https://arxiv.org/abs/2505.19488) *Preprint*, arXiv:2505.19488.

![](_page_11_Figure_0.jpeg)

<span id="page-11-1"></span>Figure 6: Optimal scale on ClimbMix across the same three evaluations shown in Figure [2.](#page-3-0) As in the BabyLM baseline corpus, the preferred parameter count depends on both dataset size and evaluation target.

## **<sup>848</sup>** A ClimbMix Scaling Curves

 Figure [6](#page-11-1) shows the same three evaluations on ClimbMix. Preferred parameter ranges remain broadly stable, while absolute scores shift: the best BLiMP scores stay within 1.2 points of those on the BabyLM-baseline corpus, the best COMPS scores are consistently higher, with a maximum gain of 1.6 points, and LAMBADA pass@5 is lower by 1.9 points at 10M words and 9.4 points at 100M words. Thus, the dependence on data budget and evalua- tion target remains qualitatively similar across the two corpora.

## <span id="page-11-0"></span>**<sup>860</sup>** B Architecture Details

 The standard parameter/data sweep uses a 12-layer decoder-only causal Transformer architecture fol- lowing [Vaswani et al.](#page-10-5) [\(2017\)](#page-10-5). Each model con- sists of independent Transformer blocks, with no recursive weight sharing or mixture-of-experts lay- ers. Each block uses a pre-norm residual structure, causal self-attention, and a dense two-layer ReLU<sup>2</sup> feed-forward sublayer.

 Attention uses fused QKV projections with an at- tention head size of 64, rotary position embeddings (RoPE; [Su et al.](#page-9-12) [\(2024\)](#page-9-12)), and query-key normaliza- tion [\(Henry et al.,](#page-8-13) [2020\)](#page-8-13). To support packed train- ing without allowing tokens to attend across doc- ument boundaries, we use variable-length causal attention computed with FlashAttention 2 kernels [\(Dao,](#page-8-14) [2024\)](#page-8-14). We also apply a learned per-head sigmoid gate to the scaled dot-product attention [o](#page-9-13)utput, following gated attention for LLMs [\(Qiu](#page-9-13) [et al.,](#page-9-13) [2026\)](#page-9-13). This is intended to reduce reliance on attention sinks, since our setup does not insert a BOS token or other special token that the model could use as an attention sink.

**883** Output projections in both the attention and MLP

sublayers are zero-initialized. Embeddings are un- **884** tied from the language-model head; where used, **885** both input embeddings and output heads follow **886** [t](#page-9-7)he ALBERT-style factorized projection idea [\(Lan](#page-9-7) **887** [et al.,](#page-9-7) [2020\)](#page-9-7). We use a vocabulary size of 32768 **888** [w](#page-9-14)ith a BPE tokenizer trained using rustbpe [\(Karpa-](#page-9-14) **889** [thy,](#page-9-14) [2025\)](#page-9-14) on the corresponding full corpus used to **890** construct the training subset. **891**

Training used a two-group optimizer. Trans- **892** former block parameters were optimized with **893** Muon [\(Jordan et al.,](#page-9-15) [2024\)](#page-9-15) augmented with neuron- **894** wise adaptive learning rates [\(Li et al.,](#page-9-16) [2025\)](#page-9-16), us- **895** ing learning rate 0.02, momentum 0.95, second- **896** moment coefficient 0.95, and weight decay 0.1. **897** Embeddings, normalization parameters, and other **898** auxiliary parameters were optimized with Adam **899** [\(Kingma and Ba,](#page-9-17) [2014\)](#page-9-17) using learning rate 0.005, **900** β = (0.9, 0.95), ϵ = 10−10, and weight decay **<sup>901</sup>** 0.005. In both groups we used cautious weight **902** decay [\(Chen et al.,](#page-8-15) [2026\)](#page-8-15), applying decay only to **903** coordinates where the parameter and update direc- **904** tions are aligned. Learning rates used 50 warmup **905** steps, followed by a constant phase and then a lin- **906** ear cooldown to 0 over the final 20% of training **907** steps. Gradients were clipped to norm 2.0 and **908** training used bfloat16 autocasting. All runs used **909** an effective global batch size of 32768 tokens and **910** random seed 0. Multi-seed runs used seeds 0, 1, **911** and 2. All individual models were trained on a **912** single NVIDIA A100 80GB GPU, except for the **913** 100M-word RecursiveGPT models, which were **914** trained on four such GPUs. **915**

![](_page_12_Figure_0.jpeg)

Figure 7: Histogram of settle depths for the depth-24 RecursiveGPT-Large model. "All tokens" includes all 65,536 analyzed token positions; "last tokens" includes only the final token of each sampled document.

<span id="page-12-1"></span>![](_page_12_Figure_2.jpeg)

<span id="page-12-2"></span><span id="page-12-0"></span>Figure 8: Prediction dynamics across recurrent depth. Final agreement measures whether the current top-1 prediction matches the depth-24 prediction; stable from depth measures whether it matches the depth-24 prediction and stays fixed through all later depths.

## **<sup>916</sup>** C Prediction Depth and Adaptive **<sup>917</sup>** Computation

 We analyze the R=24 RecursiveGPT-Large model trained on 100M words using 65,536 tokens from randomly chosen training documents. At each re- current depth, we read the intermediate hidden states through the model's own output head and record the resulting top-1 predictions (analogous to the logit lens; [nostalgebraist,](#page-9-18) [2020\)](#page-9-18). For each token position, we define its settle depth as the earliest recurrent depth whose top-1 prediction matches the final depth-24 prediction and remains unchanged thereafter. We report results for all token positions, and separately for the last token in each document.

**930** Figure [7](#page-12-1) shows that, even without ACT or an ex-**931** plicit incentive to predict early, the model naturally **932** learns to lock in its final prediction at particular re-

current depths. The largest masses for all tokens are **933** at depths 24 (19.1%), 14 (13.5%), and 23 (10.8%), **934** with a similar pattern for last-token positions. **935**

Figure [8](#page-12-2) suggests that adaptive halting could **936** save substantial inference compute. Among all **937** tokens, about half are already stable by depth 16, **938** 70.1% by depth 22, and 80.9% by depth 23. Thus **939** roughly four out of five tokens settle before the **940** final recurrent step, and only 29.9% need the last **941** two depths. **942**

| Word Budget | Model                     | Params | Neff    | A100-time           | Est. train FLOPs |
|-------------|---------------------------|--------|---------|---------------------|------------------|
| 10M         | Standard                  | 41.1M  | 15.97M  | 9 Minutes           | 1.25e16          |
| 10M         | Standard + FE             | 28.7M  | 16.12M  | 9 Minutes           | 1.26e16          |
| 10M         | RecursiveGPT + FE (R=16)  | 27.6M  | 236.32M | 21 Minutes          | 1.84e17          |
| 100M        | Standard                  | 1.22B  | 1.021B  | 17 hours 33 Minutes | 7.96e18          |
| 100M        | RecursiveGPT + FE (R=24)  | 124.0M | 1.716B  | 22 Hours 36 Minutes | 1.34e19          |
| 100M        | RecursiveGPT-Large (R=24) | 404.1M | 5.665B  | 64 Hours 24 Minutes | 4.42e19          |

<span id="page-13-2"></span><span id="page-13-0"></span>Table 4: Compute costs for the models in Table [1.](#page-6-1) Params is the total number of trainable parameters, including the input and output vocabulary maps. Neff is the non-vocabulary parameter count effectively executed per token. Estimated training FLOPs use 6NeffT [\(Kaplan et al.,](#page-9-0) [2020\)](#page-9-0). A100 time excludes initial compilation and is summed over devices for multi-GPU runs.

## **<sup>943</sup>** D Compute Cost

**944** For fixed model dimensions, compute scales ap-**945** proximately linearly with recurrent depth:

$$F(R) \approx F_{\text{fixed}} + RF_{\text{block}}.$$

**947** We make this relationship explicit below through **948** the effective parameter count and the 6NT FLOP **949** estimate.

 Table [4](#page-13-2) distinguishes the total parameter count, which includes the input and output vocabulary maps, from Neff, the parameter count used in the FLOP estimate. Following the non-vocabulary con- vention of [Kaplan et al.](#page-9-0) [\(2020\)](#page-9-0), Neff excludes the vocabulary maps but includes the dense embedding-to-hidden and hidden-to-embedding projections.

 We estimate training FLOPs as 6NeffT. All mod- els are trained for 10 epochs, giving T≈130M BPE tokens for the 10M-word setting and T≈1.3B for the 100M-word setting. For standard models, Neff counts every non-vocabulary parameter once. For recursive models, we use

$$N_{\text{eff}} = RN_{\text{shared block}} + N_{\text{step-specific}} + N_{\text{fixed}},$$

 so only the shared block is multiplied by R; step- specific normalization and bias parameters and fixed projections are counted once. The 6NT val- ues are approximate, so Table [4](#page-13-2) also reports mea-sured A100 time.

## <span id="page-13-1"></span>E Factorized-Embedding Sweep **<sup>969</sup>**

<span id="page-13-3"></span>

| E   | Embed | Total | BLiMP | COMPS | LAMBADA | Average |
|-----|-------|-------|-------|-------|---------|---------|
| 64  | 4.2M  | 20.2M | 70.51 | 51.96 | 9.79    | 44.09   |
| 128 | 8.5M  | 24.5M | 69.79 | 52.33 | 12.49   | 44.87   |
| 192 | 12.7M | 28.7M | 70.09 | 52.62 | 12.48   | 45.07   |
| 256 | 17.0M | 32.9M | 69.02 | 52.55 | 12.43   | 44.67   |
| 320 | 21.2M | 37.2M | 69.25 | 52.31 | 13.01   | 44.86   |
| 384 | 25.2M | 41.1M | 68.97 | 52.88 | 12.93   | 44.93   |

Table 5: Factorized-embedding sweep on the 10M-word setting with hidden size fixed at H=384. Embed and Total report vocabulary-map (input embedding plus output head) and total parameter counts; scores are percentages averaged over seeds 0, 1, and 2, LAMBADA is evaluated as pass@5, and Average is the arithmetic mean of the scores.

In Table [5,](#page-13-3) we evaluate factorized embeddings **970** by sweeping E while keeping H = 384 fixed for **971** a standard model trained on 10M words, report- **972** ing averages over seeds 0, 1, and 2. The final **973** row at E = 384 is the unfactorized input/output **974** vocabulary-map case. This sweep does not iden- **975** tify a precise optimum, and the differences be- **976** tween nearby settings are small. E=192 gives the **977** highest average score, E=64 gives the strongest **978** BLiMP score, E=320 gives the strongest LAM- **979** BADA pass@5 score, and unfactorized gives the **980** strongest COMPS score. We therefore identify **981** E=192 as a balanced choice rather than a defini- **982** tive optimum. In the RecursiveGPT ablations in **983** Section [5.2,](#page-6-3) we find that the benefit from factorized **984** embeddings is more substantial, suggesting that **985** this effect becomes clearer as we scale up compute. **986**

| Budget | Model                     | Params | Epochs | Est. train FLOPs | BLiMP | COMPS | LAMBADA | Average |
|--------|---------------------------|--------|--------|------------------|-------|-------|---------|---------|
| 10M    | Standard + FE             | 28.7M  | 10     | 1.26e16          | 70.09 | 52.62 | 12.48   | 45.07   |
| 10M    | Standard + FE             | 28.7M  | 146    | 1.84e17          | 63.11 | 51.31 | 10.00   | 41.47   |
| 10M    | RecursiveGPT + FE (R=16)  | 27.6M  | 10     | 1.84e17          | 70.95 | 52.96 | 13.48   | 45.80   |
| 100M   | Standard                  | 1.22B  | 10     | 7.96e18          | 79.71 | 60.65 | 50.04   | 63.47   |
| 100M   | Standard                  | 1.22B  | 50     | 3.98e19          | 74.63 | 58.74 | 36.68   | 56.68   |
| 100M   | RecursiveGPT-Large (R=24) | 404.1M | 10     | 4.42e19          | 80.70 | 60.31 | 50.77   | 63.93   |

<span id="page-14-1"></span><span id="page-14-0"></span>Table 6: Standard Transformers trained for additional epochs compared with the original 10-epoch baselines and recursive models. Estimated training FLOPs follow the calculation in Appendix [D.](#page-13-0) Scores are percentages averaged over seeds 0, 1, and 2; LAMBADA is pass@5, and Average is the arithmetic mean of BLiMP, COMPS, and LAMBADA.

## F Compute Matching with Additional Epochs

 To test whether the additional compute used by Re- cursiveGPT can instead be allocated to repeated passes over the training corpus, we train the se- lected standard baselines for additional epochs. Ta- ble [6](#page-14-1) compares them with the original 10-epoch baselines and recursive models on the three evalua- tions used in our main comparison. At 10M words, we train for 146 epochs, approximately matching the estimated training FLOPs of RecursiveGPT. At 100M words, we train for 50 epochs.

 Additional epochs reduce the average score from 45.07 to 41.47 at 10M words and from 63.47 to 56.68 at 100M words. This degradation is con- sistent with overfitting and shows that, in our ex- periments, neither increasing standard-model size nor allocating additional compute through repeated passes over the fixed data matches the performance of RecursiveGPT.