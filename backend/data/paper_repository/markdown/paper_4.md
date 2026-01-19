# SVFAP: Self-supervised Video Facial Affect Perceiver

Licai Sun, Zheng Lian, Kexin Wang, Yu He, Mingyu Xu, Haiyang Sun, Bin Liu, *Member, IEEE,* and Jianhua Tao, *Senior Member, IEEE*

**Abstract**—Video-based facial affect analysis has recently attracted increasing attention owing to its critical role in human-computer interaction. Previous studies mainly focus on developing various deep learning architectures and training them in a fully supervised manner. Although significant progress has been achieved by these supervised methods, the longstanding lack of large-scale high-quality labeled data severely hinders their further improvements. Motivated by the recent success of self-supervised learning in computer vision, this paper introduces a self-supervised approach, termed Self-supervised Video Facial Affect Perceiver (SVFAP), to address the dilemma faced by supervised methods. Specifically, SVFAP leverages masked facial video autoencoding to perform self-supervised pre-training on massive unlabeled facial videos. Considering that large spatiotemporal redundancy exists in facial videos, we propose a novel temporal pyramid and spatial bottleneck Transformer as the encoder of SVFAP, which not only largely reduces computational costs but also achieves excellent performance. To verify the effectiveness of our method, we conduct experiments on nine datasets spanning three downstream tasks, including dynamic facial expression recognition, dimensional emotion recognition, and personality recognition. Comprehensive results demonstrate that SVFAP can learn powerful affect-related representations via large-scale self-supervised pre-training and it significantly outperforms previous state-of-the-art methods on all datasets. Code is available at [https://github.com/sunlicai/SVFAP.](https://github.com/sunlicai/SVFAP)

**Index Terms**—Video-based facial affect analysis, self-supervised learning, masked autoencoding,Transformer, spatial bottleneck, temporal pyramid

✦

## **1 INTRODUCTION**

V IDEO-BASED facial affect analysis, which aims to auto-matically detect and understand human affective states from facial videos, has recently gained considerable attention due to its great potential in developing natural and harmonious human-computer interaction systems [\[1\]](#page-14-0), [\[2\]](#page-14-1), [\[3\]](#page-14-2), [\[4\]](#page-14-3). Early attempts for this task focus on designing advanced handcrafted features and machine learning algorithms on small lab-controlled datasets. With the advent of deep learning and larger labeled datasets, the research paradigm has changed to train supervised deep neural networks in an end-to-end manner. Researchers have developed a variety of deep architectures to improve model performance, including convolutional neural networks (CNN) [\[5\]](#page-14-4), [\[6\]](#page-14-5), recurrent neural networks (RNN) [\[7\]](#page-14-6), [\[8\]](#page-14-7), Transformers [\[9\]](#page-14-8), [\[10\]](#page-14-9), and their combinations [\[6\]](#page-14-5), [\[11\]](#page-14-10), [\[12\]](#page-14-11), [\[13\]](#page-14-12), [\[14\]](#page-14-13).

Although tremendous progress has been achieved by supervised learning, there are still two major obstacles that

*E-mail: sunlicai2019@ia.ac.cn, liubin@nlpr.ia.ac.cn*

• *Zheng Lian is with the National Laboratory of Pattern Recognition, Institute of Automation, Chinese Academy of Sciences, Beijing, China, 100190.*

• *Jianhua Tao is with the Department of Automation, Tsinghua University, and Beijing National Research Center for Information Science and Technology, Tsinghua University, Beijing, China, 100084. E-mail: jhtao@tsinghua.edu.cn*

*Manuscript received February 8, 2023, revised April 24, 2024. (Corresponding authors: Zheng Lian, Bin Liu and Jianhua Tao)*

impede its further development: 1) Supervised learning methods are prone to overfitting due to limited training data and the existence of label noise in current datasets [\[15\]](#page-14-14), [\[16\]](#page-14-15), thus having poor generalization ability on the unseen test set. 2) Collecting large-scale and high-quality labeled data is extremely time-consuming and labor-intensive because of the sparsity and imbalanced distribution of emotional moments in videos [\[15\]](#page-14-14), and also the subjectivity and ambiguity in human emotion perception [\[17\]](#page-14-16), [\[18\]](#page-14-17). These two irreconcilable factors make video-based facial affect analysis still far from real-world applications.

As an alternative to supervised learning, self-supervised learning has drawn massive attention recently due to its strong generalization ability and data efficiency [\[19\]](#page-14-18). Specifically, in contrast to supervised learning, self-supervised learning leverages input data itself as the supervisory signal for self-supervised pre-training and thus can learn powerful representations from large-scale data without using any human-annotated labels [\[19\]](#page-14-18), [\[20\]](#page-14-19). Self-supervised learning, especially generative self-supervised learning, has shown unprecedented success in lots of deep learning fields [\[21\]](#page-15-0), including natural language processing and computer vision. For instance, BERT [\[22\]](#page-15-1) introduces masked language modeling as the pre-training objective for language representation learning and achieves state-of-the-art results on over ten natural language processing tasks. Similarly, MAE [\[23\]](#page-15-2) utilizes masked image autoencoding to perform selfsupervised visual pre-training and outperforms its supervised counterpart in many downstream vision tasks.

Despite its great success in many deep learning fields, self-supervised learning has rarely been explored in video-

<sup>•</sup> *Licai Sun, Kexin Wang, Yu He, Mingyu Xu, Haiyang Sun, and Biu Liu are with the School of Artificial Intelligence, University of Chinese Academy of Sciences, Beijing, China, 100049, and the National Laboratory of Pattern Recognition, Institute of Automation, Chinese Academy of Sciences, Beijing, China, 100190.*

*E-mail: lianzheng2016@ia.ac.cn*

based affective computing. To this end, this paper presents a self-supervised learning method, named Self-supervised Video Facial Affect Perceiver (SVFAP), to unleash the power of large-scale self-supervised learning for video-based facial affect analysis. As shown in Fig. [1,](#page-3-0) SVFAP involves twostage training, i.e., self-supervised pre-training and downstream fine-tuning. Its whole pipeline is conceptually simple and generally inherits those of MAE [\[23\]](#page-15-2) and its video versions [\[24\]](#page-15-3), [\[25\]](#page-15-4) considering their big success in computer vision. Concretely, during the pre-training stage, SVFAP utilizes masked facial video autoencoding to learn useful and transferable spatiotemporal representations from a large amount of unlabeled facial video data. The architecture adopts an asymmetric encoder-decoder design [\[23\]](#page-15-2) to enable efficient pre-training, in which a high-capacity encoder only processes limited visible input (since the masking ratio is very high) and a lightweight decoder operates all input and reconstructs the masked part. During fine-tuning, it discards the decoder and fine-tunes the pre-trained high-capacity encoder on downstream datasets. Note that, since the vanilla Vision Transformer (ViT) [\[26\]](#page-15-5) is typically employed as the encoder in MAE and its video versions, the computational costs are very expensive during downstream fine-tuning (especially for videos) despite the architecture efficiency in pre-training. Considering that large redundancy (e.g., facial symmetry and temporal correlation) exists in 3D facial video data, we thus propose a novel Temporal Pyramid and Spatial Bottleneck Transformer (TPSBT) as the highcapacity encoder of SVFAP to achieve both efficient pretraining and fine-tuning. As the name suggests, TPSBT (Fig. [2\)](#page-4-0) utilizes spatial bottleneck mechanism and temporal pyramid learning to minimize redundant information in spatial and temporal dimensions, which not only reduces the computational costs greatly (about 43% FLOPs reduction during fine-tuning) but also leads to superior performance.

To verify the effectiveness of SVFAP, we conduct experiments on nine datasets from three video-based facial affect analysis tasks, including six datasets for dynamic facial expression recognition, two datasets for dimensional emotion recognition, and one dataset for personality recognition. Comprehensive experimental results demonstrate that our SVFAP can learn powerful affect-related representations from large-scale unlabeled facial video data via selfsupervised pre-training and significantly outperforms previous state-of-the-art methods on all downstream datasets. For instance, on three in-the-wild dynamic facial expression recognition datasets, our best model surpasses the previous best by 5.72% UAR and 5.02% WAR on DFEW [\[6\]](#page-14-5), 4.38% UAR and 3.75% WAR on FERV39k [\[27\]](#page-15-6), and 7.91% UAR and 6.10% WAR on MAFW [\[28\]](#page-15-7). To sum up, the main contributions of this paper are three-fold:

- We introduce a self-supervised learning approach, SVFAP, to address the dilemma faced by supervised learning methods in video-based facial affect analysis. It leverages masked facial video autoencoding as the pre-training objective and can learn powerful affect-related representations from large-scale unlabeled facial video data.
- We propose a novel TPSBT model as the encoder of SVFAP to eliminate large spatiotemporal redun-

dancy in facial videos, which not only enjoys lower computational costs but also has superior performance when compared with the vanilla ViT.

• Comprehensive experiments on nine downstream datasets demonstrate that our SVFAP achieves stateof-the-art performance in three popular video-based facial affect analysis tasks.

## **2 RELATED WORK**

### **2.1 Video-based Facial Affect Analysis**

Most studies on video-based facial affect analysis fall into the supervised learning paradigm. They mainly concentrate on developing more advanced deep learning architectures to extract discriminative spatiotemporal representations from raw facial videos. Generally, there are two lines of research. The first line of research treats the spatial and temporal dimension of 3D video data in an independent manner [\[6\]](#page-14-5), [\[11\]](#page-14-10), [\[12\]](#page-14-11), [\[27\]](#page-15-6), [\[28\]](#page-15-7), [\[29\]](#page-15-8). Typically, 2D CNN (e.g., VGGNet [\[30\]](#page-15-9) and ResNet [\[31\]](#page-15-10)) is first used to extract spatial features from each static frame and then RNN (e.g., LSTM [\[32\]](#page-15-11) and GRU [\[33\]](#page-15-12)) runs over them to integrate the dynamic temporal information across all frames. Recently, inspired by the great success of Transformer [\[34\]](#page-15-13) in natural language processing and computer vision, there are also several studies that utilize the global dependency modeling ability of Transformer to enhance spatial and temporal feature extraction of traditional CNN and RNN [\[9\]](#page-14-8), [\[10\]](#page-14-9), [\[13\]](#page-14-12), [\[14\]](#page-14-13), [\[35\]](#page-15-14). Another line of research tries to simultaneously encode spatial appearance features and dynamic motion information by extending the 2D convolution kernel to the 3D convolution kernel along the temporal axis. With the help of 3D kernels, 3D CNN (e.g., C3D [\[36\]](#page-15-15), R(2+1)D [\[37\]](#page-15-16), P3D [\[38\]](#page-15-17), and 3D ResNet [\[39\]](#page-15-18)) is expected to extract discriminative spatiotemporal representations from raw videos.

Although the above supervised deep learning methods have achieved remarkable improvement over traditional machine learning methods, they still suffer from the notorious overfitting issue due to limited training data and label noise in current datasets [\[15\]](#page-14-14), [\[16\]](#page-14-15). In contrast to these supervised methods, we propose a self-supervised learning method in this study to address their dilemma by pretraining on abundantly available unlabeled facial videos.

### **2.2 Self-supervised Learning**

Self-supervised learning aims to solve the data-hungry issue in supervised learning by exploiting massive unlabeled data. It can be roughly divided into two categories: discriminative and generative [\[21\]](#page-15-0). The discriminative method generally follows the supervised counterpart by designing a discriminative loss. Early studies focused on developing various geometry-based pretext tasks, such as predicting image rotation [\[40\]](#page-15-19) and sorting shuffled video frames [\[41\]](#page-15-20). In recent years, the trend has shifted from handcrafted tasks to contrastive learning methods, e.g., MoCo [\[42\]](#page-15-21), and SwAV [\[43\]](#page-15-22). Contrastive learning has been the dominant selfsupervised pre-training framework in computer vision until the more recent reviving success of generative learning. The generative method typically involves an autoencoding process, in which an encoder maps the input into a latent representation and a decoder reconstructs the original input from the encoded representation. Early generative work can be dated back to denoising autoencoder [\[44\]](#page-15-23), i.e., reconstructing the clean input from a partially corrupted one. Recently, motivated by the unprecedented success in natural language processing (e.g., BERT [\[22\]](#page-15-1) and GPT [\[45\]](#page-15-24)), generative methods have also achieved impressive results in computer vision [\[23\]](#page-15-2), [\[46\]](#page-15-25). One of the most representative methods is masked autoencoder (MAE) [\[23\]](#page-15-2). MAE and its video versions [\[24\]](#page-15-3), [\[25\]](#page-15-4) utilize an asymmetric encoder-decoder architecture to efficiently pre-train vanilla ViT and outperform its supervised counterpart and state-of-the-art contrastive learning methods by large margins in many downstream tasks (e.g., object recognition/detection/segmentation, and action recognition/detection).

Despite the great success of self-supervised learning in many deep learning fields, it has rarely been explored in video-based facial affect analysis. Roy et al. [\[47\]](#page-15-26) present a spatiotemporal contrastive learning method pre-trained on a small lab-controlled labeled dataset. Unlike it, the proposed SVFAP is built upon more advanced generative methods (i.e., MAE and its video versions) and leverages largescale in-the-wild unlabeled facial videos for self-supervised pre-training. There are also several self-supervised studies in the relevant research field (i.e., facial action unit detection). For instance, FAb-Net [\[48\]](#page-15-27) exploits relative facial movements between adjacent frames as free supervisory signals to perform self-supervised pre-training. TCAE [\[49\]](#page-15-28) improves FAb-Net by disentangling the head poserelated movements and facial action-related ones. FaceCycle [\[50\]](#page-15-29) further introduces facial motion and identity cycleconsistency to promote facial representation learning. Lu et al. [\[51\]](#page-15-30) propose a triplet-based frame ranking method for temporal consistency modeling. Recently, there are also a few studies focusing on general self-supervised facial representation learning. Bulat et al. [\[52\]](#page-15-31) pre-train SwAV [\[43\]](#page-15-22) on large-scale face recognition datasets and find that it achieves significant improvements over previous supervised methods on five face analysis tasks. FaRL [\[53\]](#page-15-32) utilizes both lowlevel masked facial image modeling and high-level facetext contrastive learning for self-supervised pre-training and outperforms state-of-the-art methods on many face analysis tasks. Although achieving promising results, these methods use 2D models for self-supervised pre-training, thus could not capture rich spatiotemporal information in 3D facial videos.

### **2.3 Vision Transformer**

Originated from natural language processing, Transformer [\[34\]](#page-15-13) based architectures have recently revolutionized various computer vision tasks by means of its strong longrange dependency modeling ability [\[54\]](#page-15-33). Among them, the pioneering work of ViT [\[26\]](#page-15-5) directly applies the standard Transformer to a sequence of image patches and performs very well on image classification tasks, challenging the dominant paradigm of CNN in computer vision. Since ViT relies on large amounts of labeled data (i.e., JFT-300M) to achieve successful supervised pre-training, DeiT [\[55\]](#page-15-34) introduces several training strategies to allow it can be trained on a much smaller dataset (i.e., ImageNet-1K). After that, numerous ViT variants have emerged by incorporating more or less vision-friendly priors (e.g., local self-attention and hierarchical design) to reduce the quadratic scaling cost of vanilla ViT and improve model performance in vision tasks [\[56\]](#page-15-35), [\[57\]](#page-15-36), [\[58\]](#page-15-37), [\[59\]](#page-15-38), [\[60\]](#page-15-39). For instance, in the video domain, TimeSformer [\[57\]](#page-15-36) applies factorized temporal and spatial attention in the standard Transformer block to achieve spatiotemporal representation learning. MViT [\[58\]](#page-15-37) introduces multi-scale feature hierarchies to the vanilla ViT. Video Swin Transformer [\[60\]](#page-15-39) utilizes 3D-shifted window attention to inject spatiotemporal locality inductive bias into video Transformers. Although these variants usually perform better than vanilla ViT in the supervised setting, they are typically not suitable for masked autoencoding in self-supervised pre-training. This is because they could not drop masked tokens due to the incorporation of local operations (e.g., window-based attention and patch merging) in their architectures. Thus, they can not enjoy the efficiency of vanilla ViT during masked autoencoding. This is why MAE and its video versions all employ ViT as the encoder. Nevertheless, ViT still suffers from expensive computational costs during downstream fine-tuning. To this end, in this paper, we introduce temporal pyramid learning and spatial bottleneck mechanism to ViT to enable both efficient pretraining and fine-tuning.

## **3 METHOD**

To tackle the longstanding data scarcity issue in videobased affective computing, we propose Self-supervised Video Facial Affect Perceiver (SVFAP) in this paper, with its whole pipeline illustrated in Fig. [1.](#page-3-0) Specifically, it first utilizes masked facial video autoencoding to perform selfsupervised pre-training on massive unlabeled facial video data, then discards the decoder and fine-tunes the pretrained encoder in downstream video-based facial affect analysis tasks. In the following sections, we elaborate on both pre-training and fine-tuning details.

### **3.1 Self-supervised Pre-training**

The idea of masked facial video autoencoding is simple, i.e., reconstructing the original facial video given partially observed input. Concretely, SVFAP consists of an encoder to project the original video to a high-level spatiotemporal representation in the latent space, and then a decoder to reconstruct the original input from the encoded representation. Moreover, similar to MAE [\[23\]](#page-15-2) and its video versions [\[24\]](#page-15-3), [\[25\]](#page-15-4), SVFAP adopts an asymmetric encoder-decoder architecture, where a high-capacity encoder only accepts limited visible tokens (e.g., 10%) as input and a lightweight decoder operates on all tokens to perform the video reconstruction. With this special design, the computational costs could be largely reduced to allow fast pre-training.

#### *3.1.1 Patch Embedding*

We employ a Transformer-based encoder to encode raw facial videos. Considering that Transformer accepts a sequence of tokens as input, we thus split the 3D video clip V with a spacetime shape of T × H × W × 3 (T is the number of frames, H and W are frame height and width

![](_page_3_Figure_1.jpeg)

<span id="page-3-0"></span>Fig. 1. An overview of the proposed method (i.e., SVFAP). It consists of two stages, including self-supervised pre-training (a) and downstream fine-tuning (b). During pre-training, SVFAP utilizes masked facial video autoencoding as the training objective. Following previous studies [23], [24], [25], it adopts an asymmetric encoder-decoder architecture and a high masking ratio (e.g., 90%) to enable fast pre-training on large-scale unlabeled facial video data. After pre-training, the lightweight decoder is discarded and the high-capacity encoder is fine-tuned in downstream tasks.

respectively) into a regular grid of non-overlapping spatiotemporal patches (Fig.  $1$  (a)), then flatten and embed them to tokens by linear projection. Following VideoMAE [24], the patch size is set to  $2 \times 16 \times 16$ . Therefore, the raw video clip is transformed to token embeddings with the shape of  $\frac{T}{2} \times \frac{H}{16} \times \frac{W}{16} \times C$  (C is the embedding dimension) after patch embedding. Finally, to inject the position information into the sequence, we add sinusoidal positional embeddings [34] to the embedded tokens.

#### 3.1.2 Tube Masking

In order to make video reconstruction a challenging and meaningful pre-training task, we need to mask some embedded patches. Different modalities usually require different masking ratios. For the high-level and information-dense text modality, BERT [22] chooses to randomly mask 15% of tokens in the sequence. For the low-level and informationredundant image modality, MAE advocates a masking ratio of 75%. For video data, it has one more temporal dimension compared with static images and has high spatiotemporal redundancy. The empirical findings in previous studies suggest that 90% works best for video data [24], [25]. Following them, we also adopt a masking ratio of  $\rho = 90\%$ . With such a high masking ratio, most masked tokens can be dropped and only a small subset (i.e., 10%) of visible tokens will be processed by the encoder, leading to large computational cost reduction and efficient pre-training.

Moreover, considering that consecutive frames in videos are highly similar, spacetime-agnostic random masking might incur information leakage and make masked video reconstruction too easy. The reason is that the model could easily reconstruct the masked patches by simply finding similar visible ones in adjacent frames. Thus, the shortcut signal will encourage the model to capture low-level temporal correspondence and undermine the desired high-level spatiotemporal structure learning. To address this issue, we follow VideoMAE to employ a simple masking strategy, termed tube masking or space-only masking, i.e., first masking spatial patches in one temporal slice and then sharing it along the temporal axis (Fig.  $1$  (a)).

#### 3.1.3 Encoder

Typically, the vanilla ViT  $[26]$  is employed as the encoder in masked autoencoding [23], [24], [25]. Although it enjoys much efficiency during pre-training by discarding many masked tokens, its computational costs are still very expensive during downstream fine-tuning as it must take as input all embedded tokens. Meanwhile, we notice that large redundancy exists in 3D facial videos, such as facial symmetry and temporal correlation. Motivated by this, we propose the Temporal Pyramid and Spatial Bottleneck Transformer (TPSBT) as the encoder of our SVFAP to enable both fast pre-training and fine-tuning. As shown in Fig. 2, our TPSBT has three stages. The first stage is composed of several standard Transformer blocks, while in the last two stages, they are replaced by spatial bottleneck Transformer blocks to reduce spatial redundancy. Moreover, benefiting from tube masking, we could further utilize temporal pyramid learning to reduce redundancy in the temporal dimension. For convenience, in the following part, we denote as  $\mathbf{X} \in \mathbb{R}^{N \times C}$ the reshaped input token embeddings after tube masking, where  $N = \frac{T}{2} \cdot S$  is the total number of visible tokens and  $S = \frac{H}{16} \cdot \frac{W}{16} \cdot (1 - \rho)$  denotes the spatial token number. And  $\mathbf{X}_i \in \mathbb{R}^{N_i \times C}$  represents the output of stage  $i$  ( $N_i$  is the number of tokens in each stage,  $i \in \{1, 2, 3\}$ ).

![](_page_4_Figure_1.jpeg)

<span id="page-4-0"></span>Fig. 2. The encoder in SVFAP, i.e., TPSBT. We perform summation-based multi-scale fusion for features from three stages during pre-training and empirically do not use it in fine-tuning. The temporal length in each stage  $i \in \{1, 2, 3\}$ ). The spatial size  $S = \frac{H}{16} \cdot \frac{W}{16} \cdot (1 - \rho)$  ( $\rho$  is the masking ratio and  $\rho = 90\%$ ) during pre-training and  $S = \frac{H}{16} \cdot \frac{W}{16}$  during fine-tuning.

Standard Transformer. The standard Transformer in stage 1 is used to retain the global spatiotemporal representation learning ability of vanilla ViT. It consists of a sequence of  $M_1$  Transformer blocks, each of which is composed of alternating layers of Multi-Head Self-Attention (MHSA) and Feed-Forward Network (FFN), with Layer Normalization (LN) applied before each layer and residual connections after each layer. Formally, we define a standard Transformer block as follows:

$$\begin{array}{c} \mathbf{Y}_{1}^{(j-1)} = \text{MHSA}(\text{LN}(\mathbf{X}_{1}^{(j-1)})) + \mathbf{X}_{1}^{(j-1)} \\ \mathbf{X}_{1}^{(j)} = \text{FFN}(\text{LN}(\mathbf{Y}_{1}^{(j-1)})) + \mathbf{Y}_{1}^{(j-1)} \end{array} \tag{1}$$

<span id="page-4-1"></span>where the superscript  $j \in \{1, ..., M_1\}$  is the block index,  $\mathbf{X}_1^{(0)} = \mathbf{X}$ , and the output of stage 1 is  $\mathbf{X}_1 = \mathbf{X}_1^{(M_1)}$ .

The MHSA operation in Eq. (1) employs multi-head scaled dot-product attention [34] to explore long-range spatiotemporal dependencies in input tokens, i.e.,

$$\begin{aligned} \text{MHSA}(\mathbf{X}) &= \text{Concat}(\text{head}_1, ..., \text{head}_H) \mathbf{W}^O \\ \text{head}_h &= \text{Softmax}(\frac{\mathbf{Q}_h \mathbf{K}_h^\top}{\sqrt{d_h}}) \mathbf{V}_h \end{aligned} \tag{2}$$

<span id="page-4-4"></span>where  $\mathbf{Q}_h = \mathbf{X} \mathbf{W}_h^Q$  is the query,  $\mathbf{K}_h = \mathbf{X} \mathbf{W}_h^K$  is the key,<br> $\mathbf{V}_h = \mathbf{X} \mathbf{W}_h^V$  is the value,  $\mathbf{W}_h^* \in \mathbb{R}^{C \times d_h}$  ( $* \in \{Q, K, V\}$ ),<br> $\mathbf{W}^O \in \mathbb{R}^{C \times C}$ ,  $H$  is the number of heads, feature dimension of head  $h$ , and the superscript  $^{\top}$  is matrix transpose. Finally, FFN in Eq. (1) consists of two linear layers with a GELU [61] non-linearity in between, i.e.,

<span id="page-4-3"></span>
$$FFN(\mathbf{X}) = GELU(\mathbf{X}\mathbf{W}_1 + \mathbf{b}_1)\mathbf{W}_2 + \mathbf{b}_2 \tag{3}$$

where  $\mathbf{W}_1 \in \mathbb{R}^{C \times 4C}$ ,  $\mathbf{b}_1 \in \mathbb{R}^{4C}$ ,  $\mathbf{W}_2 \in \mathbb{R}^{4C \times C}$ ,  $\mathbf{b}_2 \in \mathbb{R}^{C}$ .

**Temporal Pyramid.** As illustrated in Fig. 2, a temporal downsampling module is inserted before spatial bottleneck Transformer blocks in the last two stages to achieve temporal redundancy reduction. We utilize a strided convolution layer to implement this module:

$$\mathbf{T} \downarrow (\mathbf{X}_{i-1}) = \text{Conv}(\mathbf{X}_{i-1}, k) \in \mathbb{R}^{N_i \times C} \tag{4}$$

<span id="page-4-2"></span>where  $i \in \{2,3\}$  is the stage index,  $N_i = T_i \cdot S$ ,  $T_i = \frac{T}{2k^{i-1}}$ is the temporal length in stage  $i$ , and  $k$  is the kernel size and stride of the convolution layer. Empirically,  $k$  is set to 2, which means that the temporal length is halved after the temporal downsampling module. Alternatives to convolution-based downsampling could be more simple average pooling or max pooling, however, we observed slight performance degradation in experiments.

Spatial Bottleneck Transformer. After temporal information aggregation, we further employ the Spatial Bottleneck Transformer (SBT) in stage 2 and stage 3 to reduce spatial redundancy. The main idea of SBT is to introduce a small number of bottleneck tokens via spatial attention and employ them instead of the original redundant embedded tokens to perform further spatiotemporal interactions.

As shown in the bottom right of Fig. 2, SBT is composed of a spatial attention module,  $M_i - 1$   $(i \in \{2, 3\})$  SBT blocks, and 1 reverse SBT block. To be specific, the spatial attention module is used to compress the original fine-grained and redundant spatial tokens into a few global semantic bottleneck tokens. For convenience, we reuse  $\mathbf{X}_{i-1} \, \in \, \mathbb{R}^{T_i \cdot S \times C}$  $(i \in \{2,3\})$  as the notation of the output of temporal downsampling module in Eq. (4). Then, the spatial attention is formulated as follows:

$$\begin{aligned} &\hat{\mathbf{X}}_{i-1} = \text{Reshape}(\mathbf{X}_{i-1}) \in \mathbb{R}^{T_i \times S \times C} \\ &\mathbf{Y}_i = \text{GELU}(\hat{\mathbf{X}}_{i-1}\mathbf{W}_1 + \mathbf{b}_1)\mathbf{W}_2 + \mathbf{b}_2 \in \mathbb{R}^{T_i \times S \times G} \\ &\tilde{\mathbf{X}}_{i-1} = \text{Reshape}(\mathbf{X}_{i-1}) \in \mathbb{R}^{T_i \times C \times S} \\ &\mathbf{Z}_i = \tilde{\mathbf{X}}_{i-1}\mathbf{Y}_i \in \mathbb{R}^{T_i \times C \times G} \\ &\mathbf{B}_i = \text{Reshape}(\mathbf{Z}_i) \in \mathbb{R}^{T_i \cdot G \times C} \end{aligned} \tag{5}$$

where  $\mathbf{W}_1$ ,  $\mathbf{b}_1$ ,  $\mathbf{W}_2$ , and  $\mathbf{b}_2$  have similar feature dimensions to those in Eq. (3). After spatial attention, the redundant  $S$ spatial tokens of each temporal slice in the original input  $\mathbf{X}_{i-1}$  are summarized into *G* bottleneck tokens in  $\mathbf{B}_i$ .

Subsequently, we utilize  $M_i - 1$  SBT blocks to operate on the summarized bottleneck tokens to achieve efficient global spatiotemporal interactions. As shown in Fig. 2, an SBT block mainly consists of a Multi-Head Cross-Attention (MHCA) layer [62], an MHSA layer, and an FFN layer. Formally, it can be defined as follows:

$$\begin{array}{l} \mathbf{Y}_{i}^{(j-1)} = \text{MHCA}(\text{LN}(\mathbf{B}_{i}^{(j-1)}), \text{LN}(\mathbf{X}_{i-1})) + \mathbf{B}_{i}^{(j-1)} \\ \mathbf{Z}_{i}^{(j-1)} = \text{MHSA}(\text{LN}(\mathbf{Y}_{i}^{(j-1)})) + \mathbf{Y}_{i}^{(j-1)} \\ \mathbf{B}_{i}^{(j)} = \text{FFN}(\text{LN}(\mathbf{Z}_{i}^{(j-1)})) + \mathbf{Z}_{i}^{(j-1)} \end{array} \tag{6}$$

where the superscript  $j \in \{1, ..., M_i - 1\}$  is the block index,  $\mathbf{B}_{i}^{(0)} = \mathbf{B}_{i}$ . The MHCA layer iteratively distills necessary information from the original input back into the bottleneck embeddings to avoid key information being lost during spatial compression. It is a variant of MHSA, whose query is the bottleneck embeddings while the key and value come from the original input to allow information flow from the latter to the former, i.e.,

$$\begin{aligned} \text{MHCA}(\mathbf{X}, \mathbf{Y}) &= \text{Concat}(\text{head}_1, ..., \text{head}_H) \mathbf{W}^O \\ \text{head}_h &= \text{Softmax}(\frac{\mathbf{Q}_h^X \mathbf{K}_h^Y^\top}{\sqrt{d_h}}) \mathbf{V}_h^Y \end{aligned} \tag{7}$$

where  $\mathbf{Q}_h^X = \mathbf{X} \mathbf{W}_h^Q$ ,  $\mathbf{K}_h^Y = \mathbf{Y} \mathbf{W}_h^K$ ,  $\mathbf{V}_h^Y = \mathbf{Y} \mathbf{W}_h^V$  , other notations are similar to those in Eq. (2).

Compared with a standard Transformer block, the computational complexity of an SBT block is reduced from the quadratic  $O(S^2T_i^2)$  to  $O(G(G+S)T_i^2)$  thanks to the introduction of spatial bottleneck tokens. Considering that  $G$  is a small constant, an SBT block thus enjoys linear computational complexity with respect to the spatial size  $S$ . Note that, empirically, we have  $G \approx S$  during pre-training and  $G \ll S$  during fine-tuning (Sec. 4.1). Therefore, the computational costs of pre-training remain approximately unchanged (actually, slightly decrease) and large computations can be reduced during downstream fine-tuning, allowing both efficient pre-training and fine-tuning (Sec. 4.2.2).

Ultimately, a reverse SBT block is employed to recover the spatial resolution of the original input for the final reconstruction. As shown in Fig. 2, the query and key/value of this reverse block are just the opposite of the normal block, i.e.,

$$\begin{aligned} \mathbf{Y}_{i} &= \text{MHCA}(\text{LN}(\mathbf{X}_{i-1}), \text{LN}(\mathbf{B}_{i}^{(M_{i}-1)})) + \mathbf{X}_{i-1} \\ \mathbf{Z}_{i} &= \text{MHSA}(\text{LN}(\mathbf{Y}_{i})) + \mathbf{Y}_{i} \\ \mathbf{X}_{i} &= \text{FFN}(\text{LN}(\mathbf{Z}_{i})) + \mathbf{Z}_{i} \end{aligned} \tag{8}$$

where  $\mathbf{X}_i \in \mathbb{R}^{N_i \times C}$  is the final output of stage  $i \ (i \in \{2, 3\}).$ 

#### 3.1.4 Decoder

The decoder is only utilized during pre-training to reconstruct the original input facial video. Therefore, it is flexible to build the decoder architecture in a way that is independent of the encoder design. For simplicity, we follow previous work [23], [24] to employ the standard Transformer. Moreover, since it has demonstrated that the decoder can be lightweight, the number of Transformer blocks is set to 4, which is much smaller than that of the encoder (Sec. 4.1).

As illustrated in Fig. 1 (a), the input to the decoder is the combination of visible and masked tokens. It should be noted that, due to the existence of temporal downsampling modules in the encoder, it is necessary to recover the temporal resolution of visible tokens. Hence, we apply corresponding temporal upsampling to the outputs of the last two stages. To avoid increasing model parameters, we simply use nearest-neighbor interpolation for upsampling:

$$T \uparrow (\mathbf{X}_i) = \text{Interp}(\mathbf{X}_i, k^{i-1}) \in \mathbb{R}^{N \times C}$$
(9)

where  $\mathbf{X}_i$  is the output of stage  $i$   $(i \in \{2,3\})$  in the encoder,  $k^{i-1}$  is the upscaling factor. Moreover, to enable the decoder to be aware of spatiotemporal features at different levels, summation-based multi-scale fusion is employed to aggregate the outputs of three stages in the encoder, i.e.,

$$\mathbf{X} = \mathbf{X}_1 + T \uparrow (\mathbf{X}_2) + T \uparrow (\mathbf{X}_3) \tag{10}$$

where  $\mathbf{X} \in \mathbb{R}^{N \times C}$  denotes the encoded visible tokens. After multi-scale fusion, we first concatenate  $\mathbf{X}$  and the trainable masked tokens, then add sinusoidal positional embeddings to them, and finally pass them through the Transformerbased decoder for video reconstruction. Finally, the mean squared error between the original video  ${\bf V}$  and the reconstructed video  $\mathbf{V}$  in the pixel space is calculated as the reconstruction loss:

$$\mathcal{L} = \frac{1}{|\mathcal{M}|} \sum_{m \in \mathcal{M}} ||\mathbf{V}(m) - \hat{\mathbf{V}}(m)||^2 \tag{11}$$

where  $\mathcal{M}$  is the set of masked positions.

### <span id="page-5-0"></span>3.2 Downstream Fine-tuning

After self-supervised pre-training, we then discard the lightweight decoder and only use the pre-trained highcapacity encoder for downstream fine-tuning (Fig.  $1$  (b)). The main difference in the encoder behavior between finetuning and pre-training is that we do not perform multiscale fusion to aggregate the outputs of three stages (i.e., only use the high-level spatiotemporal representations in the last stage, as shown in Fig. 2), as we observe worse results in our experiments.

Based upon the pre-trained encoder, we apply global average pooling to the extracted spatiotemporal feature and append a fully connected network for final prediction. We use different loss functions for different types of video-based facial affect analysis tasks. For the classification task, the cross-entropy loss is employed, i.e.,

$$\mathcal{L}_{\text{cls}} = -\sum_{k=1}^{K} y_k \log \hat{y}_k \tag{12}$$

![](_page_6_Figure_1.jpeg)

<span id="page-6-1"></span>Fig. 3. The illustration of the face patch location for VoxCeleb2 videos.

where  $\hat{\mathbf{y}} \in \mathbb{R}^K$  denotes the prediction,  $\mathbf{y} \in \mathbb{R}^K$  is the target, and  $K$  is the number of emotion classes. For the regression task, we compute the mean square error between the prediction and the target:

$$\mathcal{L}_{\text{reg}} = \frac{1}{K} ||\mathbf{y} - \hat{\mathbf{y}}||^2 \tag{13}$$

where  $K$  is the number of emotion dimensions.

## 4 EXPERIMENTS

<span id="page-6-0"></span>

### 4.1 Implementation Details

**TPSBT architecture.** To meet different needs in real-world applications, we build two versions (i.e., base and small) of TPSBT as the encoder of SVFAP. For the small version TPSBT-S,  $C = 384$ ,  $M_1 = 8$ ,  $M_2 = 4$ ,  $M_3 = 2$ . For the base version TPSBT-B,  $C = 512$ ,  $M_1 = 12$ ,  $M_2 = 6$ ,  $M_3 = 3$ . The model size and computational costs of the small version are approximately half of the base version. Besides, for both versions, the spatial bottleneck token number  $G$  is set to 8.

Self-supervised pre-training. We pre-train TPSBT on a large-scale audio-visual dataset of human speech, Vox-Celeb2 [63]. It includes more than 1 million video clips for over 6K celebrities extracted from about 150K videos uploaded to YouTube. We use its development set for selfsupervised pre-training, which has 1,092,009 video clips from 145,569 videos. As shown in Fig. 3, the resolution of the original videos in VoxCeleb2 is  $224 \times 224$ , where faces typically appear in the upper-central part of the video. The remaining parts display the shoulders and neck, along with extraneous background information. Therefore, we only use a  $160 \times 160$  patch from the upper-central location of the video, allowing us to remove irrelevant information while also reducing the model's input size, thus lowering computational costs. We sample 16 frames from each video clip using a temporal stride of 4, resulting in  $8 \times 10 \times 10$  input tokens after patch embedding when using the patch size of  $2 \times 16 \times 16$ .

We conduct experiments using the PyTorch framework with 4 Nvidia GeForce RTX 3090 GPUs. For the hyperparameter setting, we mainly follow VideoMAE [24]. The main differences include the learning rate, batch size, and training epochs. Specifically, we adopt an AdamW optimizer with  $\beta_1 = 0.9$  and  $\beta_2 = 0.95$ . The base learning rate is  $3e-4$ and the weight decay is 0.05. The overall batch size is 256. We linearly scale the base learning rate with respect to the overall batch size, i.e.,  $\text{lr} = \text{base learning rate} \times \frac{\text{batch size}}{256}$ . Besides, we employ a cosine decay learning rate scheduler. By default, we pre-train the model for  $100$  epochs with  $5$ warmup epochs and it takes about 5-6 days in our setting.

**Downstream fine-tuning.** The input video clip size is also  $16 \times 160 \times 160$  and the temporal stride is 4 in most

cases. We adopt an AdamW optimizer with  $\beta_1 = 0.9$  and  $\beta_2 = 0.999$ . The base learning rate is  $1e - 3$  and the overall batch size is 96. Other hyperparameters are the basically same as those in pre-training and can also refer to  $[24]$  for more details. We fine-tune the pre-trained model for 100 epochs with 5 warmup epochs. For inference, we uniformly sample two clips along the temporal axis for each video sample and then compute the average score as the final prediction.

### 4.2 **Dynamic Facial Expression Recognition**

#### 4.2.1 Datasets

We conduct experiments on 6 dynamic facial expression recognition datasets, including 3 large-scale in-the-wild datasets (i.e., DFEW [6], MAFW [28], and FERV39k [27]) and 3 small lab-controlled datasets (i.e., CREMA-D [64], RAVDESS [65], and eNTERFACE05 [66]). We briefly introduce each of them below.

**DFEW** consists of 16,372 video clips which are extracted from more than 1,500 high-definition movies. Each video clip is annotated by  $10$  well-trained annotators with 7 basic emotions (i.e., anger, disgust, fear, happy, sad, surprise, and neutral). To align with previous studies [6], [13], we evaluate the proposed method on 11,697 single-labeled clips using the default 5-fold cross-validation protocol.

**MAFW** is a multimodal compound affective dataset in the wild. It is composed of 10,045 video clips annotated with 11 compound emotions, including contempt, anxiety, helplessness, disappointment, and 7 basic emotions. In this paper, we only consider the video modality and conduct experiments on 9,172 single-labeled video clips. For evaluation, we follow the original paper [28] to adopt the 5-fold cross-validation protocol.

**FERV39k** is currently the largest real-world dynamic facial expression recognition dataset. It includes 38,935 video clips which belong to 22 representative scenes in 4 different scenarios. Each sample is annotated by 30 professional annotators with 7 basic emotions. The whole dataset has been officially split into 80% for training and the rest 20% for test.

**CREMA-D** is a high-quality audio-visual dataset for multimodal expression and perception of acted emotions. It consists of 7,442 video clips from 91 actors. Each video clip is labeled with 6 emotions, including happy, sad, anger, fear, disgust, and neutral. Since there is no official split for this dataset, we employ a 5-fold subject-independent crossvalidation protocol.

RAVDESS is an audio-visual dataset of emotional speech and song. It consists of 2,880 video clips from 24 professional actors, each of which is labeled with 8 emotions (i.e., 7 basic emotions and calm). In this paper, we only use the speech part with 1,440 video clips. This dataset has no official split, we thus follow [67], [68] to adopt the same 6fold subject-independent cross-validation protocol.

eNTERFACE05 is also an audio-visual emotion dataset that contains about  $1,200$  video clips from more than  $40$ subjects. Each subject is asked to simulate six emotions, including anger, disgust, fear, happy, sad, and surprise. To make a fair comparison with previous work [9], we employ a 5-fold subject-independent cross-validation protocol.

![](_page_7_Figure_1.jpeg)

<span id="page-7-2"></span>Fig. 4. Ablation study of training from scratch.

Following previous work [6], [13], [27], [28], we use the weighted average recall (WAR, i.e., the accuracy) and unweighted average recall (UAR, i.e., the mean class accuracy) as evaluation metrics for all datasets. Note that, for crossvalidation, we aggregate the predictions and labels from all splits and then report the overall UAR and WAR.

<span id="page-7-0"></span>

#### 4.2.2 Ablation Studies

In this section, we conduct in-depth ablation experiments to investigate the impacts of several key factors in our proposed SVFAP. By default, we use TPSBT-B as the encoder. During downstream fine-tuning, all models share the same evaluation protocol. In addition to fine-tuning performance, we also show the number of model parameters and computational overhead measured in Floating Point Operations  $(FLOPs)$ <sup>1</sup> for efficiency comparison. Note that we denote pre-training FLOPs as FLOPs-P. Unless otherwise stated, all experiments are conducted on split 1 of DFEW.

**Training from scratch.** We first show the superiority of the proposed self-supervised pre-training method SVFAP by comparing it with training from scratch. Fig. 4 presents the comparison results on DFEW and FERV39k. From the figure, we first observe that it is hard to achieve good results when training TPSBT-B from scratch. This observation is consistent with previous findings (i.e., vision Transformers are data-hungry) in computer vision [26], [69], and can be largely attributed to the lack of inductive bias and the small size of training datasets. Moreover, we find that our SVFAP significantly outperforms training from scratch, achieving about 42% UAR and 45% WAR improvements on DFEW, and 21% UAR and 20% WAR improvements on FERV39k. These encouraging results demonstrate that SVFAP provides an effective self-supervised pre-training mechanism for video-based facial affect analysis. We also notice that the performance gap between SVFAP and training from scratch on FERV39k is smaller than that on DFEW, probably due to the larger dataset size of the former (39K vs. 13K).

**Training schedule.** We then explore the effect of training schedule length. As shown in Fig. 5, we find that as the pre-training process goes on, the pre-training loss decreases

![](_page_7_Figure_9.jpeg)

<span id="page-7-3"></span>Fig. 5. Ablation study of training schedule.

steadily and the downstream fine-tuning performance improves consistently. This finding is in line with previous works on self-supervised learning [23], [24], [25]. It also should be noted that we do not observe clear performance saturation when reaching default maximum epochs (i.e., 100), which indicates that longer pre-training could further improve model performance in downstream fine-tuning. However, due to limited computational resources, we leave it for future work and hope the community can conduct follow-up studies.

Moreover, we visualize several reconstructed video samples using our best pre-trained model in Fig. 6. Note that these samples are randomly selected from the test set of VoxCeleb2, whose speakers are disjoint with those from the development set used for pre-training. Thus, they are not seen by our model during pre-training. We find that even under such a high masking ratio (i.e., 90%), SVFAP still can generate satisfying reconstruction results, especially for dynamic facial expressions. This indicates that, benefiting from the challenging masked facial video autoencoding task, our model can reason over high-level and meaningful spatiotemporal semantics from limited visible input to recover masked information.

**Dataset scale.** We investigate how the model behaves when pre-trained with different dataset scales. For this purpose, we randomly generate a range of subsets with increasing sizes from the whole dataset, i.e., 1%, 5%, 10%, and 20%. Note that we proportionally increase the pre-training epochs for these subsets to ensure the same pre-training cost. The results are shown in Table 1. We can observe that larger pre-training datasets generally lead to better fine-tuning results. This is expected as more diversified training samples typically result in better generalization. It is also worth noting that, even with 11K unlabeled data, our method still achieves promising performance, which demonstrates that our SVFAP is a data-efficient self-supervised video facial affect learner.

<span id="page-7-1"></span><sup>1.</sup> https://github.com/facebookresearch/fvcore

![](_page_8_Figure_1.jpeg)

<span id="page-8-0"></span>Fig. 6. Reconstruction results of three randomly selected video samples from the test set of VoxCeleb2 with a masking ratio of 90%. For each sample, we show the original video (top), masked input video (middle), and the reconstructed video (bottom).

TABLE 1 Ablation study of pre-training dataset scale.

<span id="page-8-1"></span>

| Percentage | Size | Epochs | UAR   | WAR   |
|------------|------|--------|-------|-------|
| 1%         | 11K  | 10000  | 57.65 | 70.61 |
| 5%         | 55K  | 2000   | 60.34 | 73.00 |
| 10%        | 110K | 1000   | 61.09 | 73.56 |
| 20%        | 220K | 500    | 61.54 | 73.76 |
| 100%       | 1.1M | 100    | 62.63 | 74.81 |

<span id="page-8-2"></span>TABLE 2 Ablation study of the masking ratio. FLOPs-P: Pre-training FLOPs.

| Percentage | $\#Params$<br>(M) | FLOPS<br>(G) | $FLOPs-P$<br>(G) | UAR   | WAR   |
|------------|-------------------|--------------|------------------|-------|-------|
| 75%        | 77.6              | 43.6         | 18.4             | 60.89 | 73.91 |
| 85%        | 77.6              | 43.6         | 14.7             | 61.87 | 74.77 |
| 90%        | 77.6              | 43.6         | 12.9             | 62.63 | 74.81 |
| 95%        | 77.6              | 43.6         | 11.2             | 59.93 | 73.17 |

**Masking ratio.** The influence of the masking ratio is presented in Table 2. We can find that the masking ratio of 90% has the best performance. The lower masking ratios of 75% and 85% achieve worse performance, although the encoder accepts more video tokens as input and has higher computational costs during pre-training. A higher masking ratio of 95% results in lower pre-training cost, however, the performance degrades significantly. These results are consistent with previous findings [24], [25]. Therefore, we set 90% as the default masking ratio.

Model variants. We ablate different model variants of

<span id="page-8-3"></span>TABLE 3 Ablation study of model variants. TP: Temporal Pyramid. SBT: Spatial Bottleneck Transformer. FLOPs-P: Pre-training FLOPs.

| TP | SBT | #Params<br>(M) | FLOPs<br>(G) | FLOPs-P<br>(G) | UAR   | WAR   |
|----|-----|----------------|--------------|----------------|-------|-------|
| ×  | ×   | 76.4           | 76.9         | 14.9           | 61.71 | 74.41 |
| ✓  | ×   | 77.5           | 53.1         | 13.1           | 60.84 | 74.28 |
| ×  | ✓   | 76.6           | 49.9         | 13.5           | 62.66 | 75.02 |
| ✓  | ✓   | 77.6           | 43.6         | 12.9           | 62.63 | 74.81 |

TPSBT, including 1) no TP and SBT, i.e., the vanilla ViT baseline, by removing temporal pyramid learning modules and replacing SBT with a standard Transformer of similar size in the last two stages. 2) only TP, by replacing SBT with a standard Transformer of similar size. 3) only SBT, by removing temporal pyramid learning modules. As presented in Table 3, we have the following observations: 1) When compared with the vanilla ViT baseline, TP largely reduces computational overhead (about  $30\%$ and 14% FLOPs reduction for fine-tuning and pre-training respectively) and achieves comparable performance, with only 1.1M additional parameters. 2) SBT not only reduces large computations (about 35% FLOPs and 11% FLOPs-P reduction) but also achieves the best performance among all variants. 3) When combining TP and SBT together, our default full model achieves the lowest computational costs while almost maintaining the best performance of SBT. Specifically, TPSBT significantly reduces about 43% and 15% FLOPs during fine-tuning and pre-training and outperforms the vanilla ViT baseline by 0.92% UAR and 0.40% WAR,

TABI F 4 Ablation study of multi-scale fusion.

<span id="page-9-0"></span>

| Pre-training | Fine-tuning | UAR          | WAR          |
|--------------|-------------|--------------|--------------|
| X            | X           | 61.78        | 74.43        |
| X            | ✓           | 61.24        | 74.17        |
| ✓            | X           | <b>62.63</b> | <b>74.81</b> |
| ✓            | ✓           | 62.39        | 74.74        |

<span id="page-9-1"></span>TABLE 5 Ablation study of spatial bottleneck tokens. FLOPs-P: Pre-training FLOPs.

| Number | #Params<br>(M) | FLOPS<br>(G) | FLOPS-P<br>(G) | UAR   | WAR   |
|--------|----------------|--------------|----------------|-------|-------|
| 4      | 77.6           | 43.2         | 12.6           | 61.76 | 74.08 |
| 8      | 77.6           | 43.6         | 12.9           | 62.63 | 74.81 |
| 16     | 77.6           | 44.4         | 13.7           | 62.86 | 74.69 |
| Type   | #Params (M)    | FLOPS (G)    | FLOPS-P (G)    | UAR   | WAR   |
| Avg    | 76.6           | 43.3         | 12.9           | 62.04 | 74.42 |
| Max    | 76.6           | 43.3         | 12.9           | 62.25 | 74.16 |
| Conv   | 77.6           | 43.6         | 12.9           | 62.63 | 74.81 |

with the sacrifice of a slight increase of model parameters  $(1.2M)$ . These results indicate that temporal pyramid learning and spatial bottleneck mechanism can greatly remove redundant spatiotemporal information in 3D facial videos (from temporal and spatial perspectives respectively) and help the model to concentrate on the informative one, thus contributing to lower computational costs and better model performance.

**Multi-scale fusion.** We explore the effect of multi-scale spatiotemporal feature fusion during both self-supervised pre-training and downstream fine-tuning. As shown in Table 4, we find that employing multi-scale fusion during pretraining achieves better results than those that do not use it, which shows that integrating spatiotemporal features in different levels for decoder reconstruction can help the encoder to learn more useful representations. However, we observe slight performance degradation when using it during finetuning. This result could be partly ascribed to the simple and parameter-free temporal upsampling method (i.e., nearestneighbor interpolation) used for multi-scale fusion. Another reason is that, compared to low-level details, high-level emotional semantics are more crucial for downstream affect analysis tasks. Therefore, we only use the high-level feature from the last stage of the encoder during fine-tuning.

**Spatial bottleneck tokens.** SBT utilizes spatial attention to generate several global semantic bottleneck tokens for spatial redundancy elimination and computational cost reduction, thus it is necessary to investigate how the number of spatial bottleneck tokens influence model performance. Table 5 presents the ablation results. We see that too few tokens (i.e., 4) hurt the model performance as it might be too aggressive to perform spatial compression and incur critical information loss. Besides, too many tokens (i.e., 16) increase model computational costs but do not contribute to significantly better results. Therefore, we set the spatial bottleneck token number to 8 by default.

**Temporal downsampling.** We explore the effect of three different methods for temporal downsampling in temporal pyramid learning, including simple average pooling, max pooling, and the default strided convolution. As presented in Tab. 6, we find that the convolution-based method outperforms the other two pooling methods with the sacrifice

<span id="page-9-2"></span>TABI F 6 Ablation study of temporal downsampling. FLOPs-P: Pre-training FLOPs.

of slightly more model parameters and negligible FLOPs increase, which justifies our default design choice.

#### 4.2.3 Comparison with Previous Pre-trained Models

In this section, we show the effectiveness of the proposed self-supervised learning method by comparing it with previous state-of-the-art supervised and self-supervised pretrained models. The supervised models contain four advanced video Transformers pre-trained on large-scale labeled video or image datasets, including TimeSformer [57], MViT [58], MViTv2 [59], and Video Swin Transformer [60]. The self-supervised part involves eight cutting-edge models pre-trained on massive unlabeled data (most are facial images or videos), including FAb-Net [48], TCAE [49], Face-Cycle [50], BMVC'20 [51], MoCo [70], SwAV [52], ρBYOL [71], SVT [72], VideoMAE [24], and FaRL [53]. It should be noted, all self-supervised models except  $\rho$ BYOL, SVT, and VideoMAE are 2D models, i.e., they can not process video inputs directly. Therefore, we add a standard Transformer block on top of them to enable temporal sequential modeling. Besides, all models share the same evaluation protocol to ensure a fair comparison.

The comprehensive comparison results on the split 1 of DFEW are presented in Table 7. From the table, we have the following key observations:

- Our SVFAP outperforms all supervised pre-trained video Transformers. Specifically, SVFAP-B surpasses the best-performing Video Swin Base (Swin-B) model by 3.25% UAR and 2.91% WAR, although Swin-B has a larger model size (87.6M vs. 77.6M) and more than double FLOPs (92.5G vs. 43.6G), and is pre-trained on the combination of large-scale labeled images and videos. The more encouraging thing is that even our small model SVFAP-S still outperforms Swin-B slightly, thus amply demonstrating the remarkable superiority of our proposed method. We also notice that TimeSformer also achieves satisfying results but it suffers from huge computational costs and has much more parameters. To sum up, the comparison results with supervised models show that our method can learn strong and transferable affectrelated facial representations from large-scale video data without using any human-annotated labels.
- Compared with self-supervised pre-trained models, SVFAP also achieves the best performance. Notably, when using the same Voxceleb2 dataset for pretraining, both our base and small model improve FAb-Net, TCAE, FaceCycle, and BMVC'20, by a significant margin, which indicates that masked facial video autoencoding is an effective task for self-

11

TABLE 7

<span id="page-10-0"></span>Comparison with state-of-the-art supervised and self-supervised pre-trained models on split 1 of DFEW. SSL: Self-Supervised Learning or not.

| Method           | SSL          | Pre-training Dataset                    | Dataset Type | Architecture | #Params (M) | FLOPs (G) | UAR   | WAR   |
|------------------|--------------|-----------------------------------------|--------------|--------------|-------------|-----------|-------|-------|
| TimeSformer [57] | $\times$     | ImageNet-21K+Kinetics-400               | Image+Video  | TimeSformer  | 121         | 198       | 58.90 | 71.48 |
| TimeSformer [57] | $\times$     | ImageNet-21K+Kinetics-400<br>+HowTo100M | Image+Video  | TimeSformer  | 121         | 198       | 59.13 | 71.62 |
| MViT [58]        | $\times$     | Kinetics-400                            | Video        | MViT-B       | 53          | 45        | 54.19 | 65.27 |
| MViT [58]        | $\times$     | Kinetics-600                            | Video        | MViT-B       | 53          | 45        | 55.80 | 66.85 |
| MViTv2 [59]      | $\times$     | Kinetics-400                            | Video        | MViTv2-B     | 51          | 42        | 55.12 | 67.88 |
| Video Swin [60]  | $\times$     | ImageNet-1K+Kinetics-400                | Image+Video  | Swin-S       | 50          | 55        | 57.13 | 69.96 |
| Video Swin [60]  | $\times$     | ImageNet-21K+Kinetics-400               | Image+Video  | Swin-B       | 88          | 93        | 59.38 | 71.90 |
| FAb-Net [48]     | $\checkmark$ | VoxCeleb1&2                             | Video        | ConvNet      | 6           | 33        | 45.52 | 56.01 |
| TCAE [49]        | $\checkmark$ | VoxCeleb1&2                             | Video        | ConvNet      | 6           | 33        | 45.29 | 56.35 |
| FaceCycle [50]   | $\checkmark$ | VoxCeleb1&2                             | Video        | ConvNet      | 4           | 42        | 42.27 | 54.05 |
| BMVC'20 [51]     | $\checkmark$ | VoxCeleb2                               | Video        | ResNet-18    | 12          | 15        | 56.55 | 67.12 |
| MoCo [70]        | $\checkmark$ | CelebA                                  | Image        | ResNet-50    | 32          | 34        | 53.47 | 67.45 |
| SwAV [52]        | $\checkmark$ | VGGFace2                                | Image        | ResNet-50    | 32          | 34        | 58.18 | 68.99 |
| $\rho$ BYOL [71] | $\checkmark$ | Kinetics-400                            | Video        | SlowOnly-R50 | 32          | 43        | 58.60 | 69.81 |
| SVT [72]         | $\checkmark$ | Kinetics-400                            | Video        | TimeSformer  | 121         | 198       | 57.07 | 70.01 |
| VideoMAE [24]    | $\checkmark$ | Kinetics-400                            | Video        | ViT-B        | 86          | 81        | 58.32 | 70.94 |
| FaRL [53]        | $\checkmark$ | LAION-FACE                              | Image+Text   | ViT-B        | 93          | 141       | 58.91 | 72.15 |
| SVFAP-S (ours)   | $\checkmark$ | VoxCeleb2                               | Video        | TPSBT-S      | 30          | 18        | 59.70 | 72.70 |
| SVFAP-B (ours)   | $\checkmark$ | VoxCeleb2                               | Video        | TPSBT-B      | 78          | 44        | 62.63 | 74.81 |

TABLE 8 Comparison with state-of-the-art methods on DFEW.

<span id="page-10-1"></span>

| Method              | #Params (M) | FLOPs (G) | Accuracy of Each Emotion (%) |       |         |       |          |         | Metric (%) |       |       |
|---------------------|-------------|-----------|------------------------------|-------|---------|-------|----------|---------|------------|-------|-------|
|                     |             |           | Happy                        | Sad   | Neutral | Anger | Surprise | Disgust | Fear       | UAR   | WAR   |
| 3D ResNet-18 [39]   | -           | 8         | 76.32                        | 50.21 | 64.18   | 62.85 | 47.52    | 0.00    | 24.56      | 46.52 | 58.27 |
| EC-STFL [6]         | -           | 8         | 79.18                        | 49.05 | 57.85   | 60.98 | 46.15    | 2.76    | 21.51      | 45.35 | 56.51 |
| ResNet-18+LSTM [13] | -           | 8         | 83.56                        | 61.56 | 68.27   | 65.29 | 51.26    | 0.00    | 29.34      | 51.32 | 63.85 |
| ResNet-18+GRU [13]  | -           | 8         | 82.87                        | 63.83 | 65.06   | 68.51 | 52.00    | 0.86    | 30.14      | 51.68 | 64.02 |
| Former-DFER [13]    | 18          | 9         | 84.05                        | 62.57 | 67.52   | 70.03 | 56.43    | 3.45    | 31.78      | 53.69 | 65.70 |
| CEFLNet [73]        | 13          | -         | 84.00                        | 68.00 | 67.00   | 70.00 | 52.00    | 0.00    | 17.00      | 51.14 | 65.35 |
| EST [10]            | 43          | -         | 86.87                        | 66.58 | 67.18   | 71.84 | 47.53    | 5.52    | 28.49      | 53.43 | 65.85 |
| STT [14]            | -           | -         | 87.36                        | 67.90 | 64.97   | 71.24 | 53.10    | 3.49    | 34.04      | 54.58 | 66.65 |
| DPCNet [29]         | 51          | 10        | -                            | -     | -       | -     | -        | -       | -          | 57.11 | 66.32 |
| NR-DFERNet [74]     | -           | 6         | 88.47                        | 64.84 | 70.03   | 75.09 | 61.60    | 0.00    | 19.43      | 54.21 | 68.19 |
| IAL [35]            | -           | -         | 87.95                        | 67.21 | 70.10   | 76.06 | 62.22    | 0.00    | 26.44      | 55.71 | 69.24 |
| M3DFEL [75]         | -           | 2         | 89.59                        | 68.38 | 67.88   | 74.24 | 59.69    | 0.00    | 31.63      | 56.10 | 69.25 |
| SVFAP-S (ours)      | 30          | 18        | 92.39                        | 74.92 | 70.40   | 76.90 | 62.70    | 8.28    | 37.58      | 60.45 | 72.67 |
| SVFAP-B (ours)      | 78          | 44        | 93.13                        | 76.98 | 72.31   | 77.54 | 65.42    | 15.17   | 39.25      | 62.83 | 74.27 |

TABLE 9 Comparison with state-of-the-art methods on FERV39k.

<span id="page-10-2"></span>

| Method                  | #Params (M) | FLOPs (G) | Happy | Sad   | Neutral | Anger | Surprise | Disgust | Fear  | UAR   | WAR   |
|-------------------------|-------------|-----------|-------|-------|---------|-------|----------|---------|-------|-------|-------|
| C3D [36]                | 78          | -         | 48.20 | 35.53 | 52.71   | 13.72 | 3.45     | 4.93    | 0.23  | 22.68 | 31.69 |
| P3D [38]                | -           | -         | 61.85 | 42.21 | 49.80   | 42.57 | 10.50    | 0.86    | 5.57  | 30.48 | 40.81 |
| R(2+1)D [76]            | -           | -         | 59.33 | 42.43 | 50.82   | 42.57 | 16.30    | 4.50    | 4.87  | 31.55 | 41.28 |
| 3D ResNet-18 [39]       | 33          | -         | 57.64 | 28.21 | 59.60   | 33.29 | 4.70     | 0.21    | 3.02  | 26.67 | 37.57 |
| ResNet-18+LSTM [27]     | -           | -         | 61.91 | 31.95 | 61.70   | 45.93 | 14.26    | 0.00    | 0.70  | 30.92 | 42.59 |
| VGG-13+LSTM [27]        | -           | -         | 66.26 | 51.26 | 53.22   | 37.93 | 13.64    | 0.43    | 4.18  | 32.42 | 43.37 |
| Two C3D [27]            | -           | -         | 54.85 | 52.91 | 60.67   | 31.34 | 5.96     | 2.36    | 6.96  | 30.72 | 41.77 |
| Two ResNet-18+LSTM [27] | -           | -         | 59.00 | 45.87 | 61.90   | 40.15 | 9.87     | 1.71    | 0.46  | 31.28 | 43.20 |
| Two VGG-13+LSTM [27]    | -           | -         | 69.65 | 47.31 | 52.55   | 47.88 | 7.68     | 1.93    | 2.55  | 32.79 | 44.54 |
| Former-DFER [13]        | 18          | 9         | 65.65 | 51.33 | 56.74   | 43.64 | 21.94    | 8.57    | 12.53 | 37.20 | 46.85 |
| STT [14]                | -           | -         | 69.77 | 47.81 | 59.14   | 47.41 | 20.22    | 10.49   | 9.51  | 37.76 | 48.11 |
| NR-DFERNet [74]         | -           | 6         | 69.18 | 54.77 | 51.12   | 49.70 | 13.17    | 0.00    | 0.23  | 33.99 | 45.97 |
| IAL [35]                | -           | -         | -     | -     | -       | -     | -        | -       | -     | 35.82 | 48.54 |
| M3DFEL [75]             | -           | 2         | -     | -     | -       | -     | -        | -       | -     | 35.94 | 47.67 |
| $SVFAP-S$ (ours)        | 30          | 18        | 75.02 | 52.12 | 61.34   | 48.69 | 23.04    | 12.85   | 15.31 | 41.19 | 51.34 |
| $SVFAP-B$ (ours)        | 78          | 44        | 74.00 | 53.34 | 62.26   | 51.11 | 25.24    | 13.28   | 15.78 | 42.14 | 52.29 |

![](_page_11_Figure_1.jpeg)

<span id="page-11-0"></span>Fig. 7. Comparisons with state-of-the-art supervised and self-supervised pre-trained models on the split 1 of DFEW in the few-shot setting.

<span id="page-11-1"></span>TABLE 10 Comparison with state-of-the-art methods on MAFW. AN: Anger. DI: Disgust. FE: Fear. HA: Happiness. NE: Neutral. SA: Sadness. SU: Surprise. CO: Contempt. AX: Anxiety. HL: Helplessness. DS: Disappointment.

| Method              | #Params<br>(M) | FLOPs<br>(G) | Accuracy of Each Emotion (%) |       |       |       |       |       |       |      | Metric (%) |      |      |       |       |
|---------------------|----------------|--------------|------------------------------|-------|-------|-------|-------|-------|-------|------|------------|------|------|-------|-------|
|                     |                |              | AN                           | DI    | FE    | HA    | NE    | SA    | SU    | CO   | AX         | HL   | DS   | UAR   | WAR   |
| ResNet-18 [31]      | 11             | -            | 45.02                        | 9.25  | 22.51 | 70.69 | 35.94 | 52.25 | 39.04 | 0.00 | 6.67       | 0.00 | 0.00 | 25.58 | 36.65 |
| ViT [26]            | 86             | -            | 46.03                        | 18.18 | 27.49 | 76.89 | 50.70 | 68.19 | 45.13 | 1.27 | 18.93      | 1.53 | 1.65 | 32.36 | 45.04 |
| C3D [36]            | 78             | -            | 51.47                        | 10.66 | 24.66 | 70.64 | 43.81 | 55.04 | 46.61 | 1.68 | 24.34      | 5.73 | 4.93 | 31.17 | 42.25 |
| ResNet-18+LSTM [28] | -              | -            | 46.25                        | 4.70  | 25.56 | 68.92 | 44.99 | 51.91 | 45.88 | 1.69 | 15.75      | 1.53 | 1.65 | 28.08 | 39.38 |
| ViT+LSTM [28]       | -              | -            | 42.42                        | 14.58 | 35.69 | 76.25 | 54.48 | 68.87 | 41.01 | 0.00 | 24.40      | 0.00 | 1.65 | 32.67 | 45.56 |
| C3D+LSTM [28]       | -              | -            | 54.91                        | 0.47  | 9.00  | 73.43 | 41.39 | 64.92 | 58.43 | 0.00 | 24.62      | 0.00 | 0.00 | 29.75 | 43.76 |
| Former-DFER [13]    | 18             | 9            | -                            | -     | -     | -     | -     | -     | -     | -    | -          | -    | -    | 31.16 | 43.27 |
| T-ESFL [28]         | -              | -            | 62.70                        | 2.51  | 29.90 | 83.82 | 61.16 | 67.98 | 48.50 | 0.00 | 9.52       | 0.00 | 0.00 | 33.28 | 48.18 |
| SVFAP-S (ours)      | 30             | 18           | 63.88                        | 19.56 | 30.88 | 84.46 | 62.83 | 68.37 | 59.61 | 1.27 | 31.88      | 7.63 | 7.69 | 39.82 | 53.89 |
| SVFAP-B (ours)      | 78             | 44           | 64.60                        | 25.20 | 35.68 | 82.77 | 57.12 | 70.41 | 58.58 | 8.05 | 32.42      | 8.40 | 9.89 | 41.19 | 54.28 |

supervised pre-training. Our method also beats contrastive learning-based methods (i.e., MoCo, SwAV, and SVT), verifying the advantage of the generative paradigm in self-supervised learning. When compared to VideoMAE, SVFAP-S still shows better performance while having  $2.9 \times$  fewer parameters and  $4.5 \times$  fewer FLOPs. Finally, our method also outperforms the best-performing FaRL (i.e., 3.72% UAR and 2.66% WAR improvements for SVFAP-B, 0.32% UAR and 0.80% WAR improvements for SVFAP-S), although FaRL has much more FLOPs and parameters and is pre-trained on a huge multimodal dataset. To summarize, the above comparison results with self-supervised models show that our SVFAP is an effective and efficient self-supervised video facial affect perceiver.

In addition to the evaluation in full data regime, we also conduct experiments to investigate the generalization ability of SVFAP under few-shot settings. To this end, we randomly select  $50\%$ ,  $20\%$ , and  $10\%$  samples from the training set of DFEW split 1 to obtain a series of new training sets while keeping the test set unchanged. For simplicity, we only choose several representative models in Table 7 for

evaluation. Note that, for the method with more than one model, we only use the best one. The results are reported in Fig. 7. We can observe that: 1) As expected, the performance of all methods degrades accordingly when fewer training samples are used. 2) SVFAP consistently outperforms all compared methods under each few-shot setting, which verifies the strong adaptation ability of the proposed methods in the low data regime. This ability is particularly important considering the longstanding data scarcity issue in affective computing. Notably, even with 10% (about 935 samples) training data, our method still achieves promising results (more than 50% UAR and 63% WAR).

#### 4.2.4 Comparisons with State-of-the-art Methods

In this section, we compare the proposed method with stateof-the-art methods on both in-the-wild and lab-controlled dynamic facial expression recognition datasets.

We first show the comparison results on three large inthe-wild datasets, including DFEW, FERV39k, and MAFW. The results on three datasets are reported in Table  $8$ ,  $9$ , and 10, respectively. The comparison baselines can be roughly divided into three categories: 1) the combination of convolution neural network (CNN) and recurrent neural network (RNN), i.e., CNN+RNN, such as ResNet+LSTM [31], [32]. 2)

<span id="page-12-0"></span>TABLE 11 Comparison with state-of-the-art methods on CREMA-D.

| Method                | Modality    | UAR   | WAR   |
|-----------------------|-------------|-------|-------|
| VO-LSTM [77]          | Video       | -     | 66.80 |
| Goncalves et al. [78] | Video       | -     | 62.20 |
| Lei et al. [79]       | Video       | 64.68 | 64.76 |
| AV-LSTM [77]          | Video+Audio | -     | 72.90 |
| AV-Gating [77]        | Video+Audio | -     | 74.00 |
| TFN [80]              | Video+Audio | -     | 63.09 |
| EF-GRU [81]           | Video+Audio | -     | 57.06 |
| LF-GRU [81]           | Video+Audio | -     | 58.53 |
| MulT Base [81]        | Video+Audio | -     | 68.87 |
| MulT Large [81]       | Video+Audio | -     | 70.22 |
| Goncalves et al. [78] | Video+Audio | -     | 77.30 |
| SVFAP-S (ours)        | Video       | 74.58 | 74.58 |
| SVFAP-B (ours)        | Video       | 77.31 | 77.37 |

classic 3D CNNs, including 3D ResNet [\[39\]](#page-15-18), C3D [\[36\]](#page-15-15), P3D [\[38\]](#page-15-17), and R(2+1)D [\[76\]](#page-16-12). 3) hybrid architectures of CNN and Transformer, e.g., Former-DFER [\[13\]](#page-14-12), STT [\[14\]](#page-14-13), NR-DFERNet [\[74\]](#page-16-10), IAL [\[35\]](#page-15-14), and T-ESFL [\[28\]](#page-15-7).

As shown in Table [8,](#page-10-1) we observe that SVFAP-B outperforms previous state-of-the-art methods on DFEW significantly (i.e., 5.72% UAR and 5.02% WAR improvement), setting a new record on this dataset. Besides, the small version, SVFAP-S, also surpasses the best-performing methods by a large margin, achieving a better accuracy-complexity trade-off. When comparing the fine-grained performance of each class, we find that our methods achieve remarkable improvements for most emotions (e.g., *happy* and *sad*). Notably, for the rare *disgust* emotion which only accounts for 1.2% (about 146 samples) in the whole dataset, most baseline methods fail to classify its samples correctly. Nevertheless, our SVFAP-B improves the previous best performer by about 10%. This result demonstrates that the proposed method can learn generic affect-related representations via large-scale self-supervised pre-training, thus alleviating the unbalanced learning in minority classes. Moreover, we have similar observations on the other two datasets. On the largest DFER dataset FERV39k, as shown in Table [9,](#page-10-2) SVFAP-B achieves 42.14% UAR and 52.29% WAR, outperforming the best baselines by 4.38% UAR and 3.75% WAR. On the MAFW dataset, as given in Table [10,](#page-11-1) SVFAP-B improves over the state-of-the-art T-ESFL by 7.91% UAR and 6.10% WAR. Besides, a slight performance drop is also observed for both datasets. To sum up, the above encouraging results on three in-the-wild datasets verify the strong generalization ability of our SVFAP in real-world scenarios.

Finally, we present the comparison results on three small lab-controlled datasets, including CREMA-D, RAVDESS, and eNTERFACE05. The results are reported in Table [11,](#page-12-0) [12,](#page-12-1) and [13,](#page-12-2) respectively. Similarly, we observe consistently significant performance improvements on these datasets. For instance, as shown in Table [11,](#page-12-0) SVFAP-B outperforms the best-performing unimodal methods by about 12% UAR and 10% WAR on CREMA-D. We also report the results of several multimodal methods. Compared with them, SVFAP-B still shows slightly better performance without using the audio information, which demonstrates the overwhelming superiority of the proposed method again.

<span id="page-12-1"></span>TABLE 12 Comparison with state-of-the-art methods on RAVDESS.

| Method             | Modality    | UAR          | WAR          |
|--------------------|-------------|--------------|--------------|
| VO-LSTM [77]       | Video       | -            | 60.50        |
| 3D ResNeXt-50 [67] | Video       | -            | 62.99        |
| AV-LSTM [77]       | Video+Audio | -            | 65.80        |
| AV-Gating [77]     | Video+Audio | -            | 67.70        |
| MCBP [67]          | Video+Audio | -            | 71.32        |
| MMTM [67]          | Video+Audio | -            | 73.12        |
| MSAF [67]          | Video+Audio | -            | 74.86        |
| CFN-SR [68]        | Video+Audio | -            | 75.76        |
| SVFAP-S (ours)     | Video       | 73.59        | 73.90        |
| SVFAP-B (ours)     | Video       | <b>75.15</b> | <b>75.01</b> |

<span id="page-12-2"></span>TABLE 13 Comparison with state-of-the-art methods on eNTERFACE05.

| Method                    | UAR   | WAR   |
|---------------------------|-------|-------|
| Mansoorizadeh et al. [82] | -     | 37.00 |
| 3DCNN [83]                | -     | 41.05 |
| 3DCNN-DAP [83]            | -     | 41.36 |
| Zhalehpour et al. [84]    | -     | 42.16 |
| FAN [85]                  | -     | 51.44 |
| STA-FER [86]              | -     | 42.98 |
| TSA-FER [87]              | -     | 43.72 |
| C-LSTM [88]               | -     | 45.29 |
| EC-LSTM [89]              | -     | 49.26 |
| Graph-Tran [9]            | -     | 54.62 |
| SVFAP-S (ours)            | 57.16 | 57.12 |
| SVFAP-B (ours)            | 60.58 | 60.54 |

### **4.3 Dimensional Emotion Recognition**

#### *4.3.1 Datasets*

**Werewolf-XL** [\[90\]](#page-16-26) is a spontaneous audio-visual dataset with a total of 890 minutes of videos recorded during competitive group interactions in Werewolf games. It contains 131,688 video clips from 129 subjects in 30 game sessions, including 14,632 samples from active speakers and the rest from listeners in the game. Werewolf-XL provides both selfreported categorical emotion labels and externally assessed dimensional emotion scores. In this paper, we only use 14,632 speaker samples and dimensional annotations. As the goal is to predict continuous scores, we formulate it as a regression problem as stated in Section [3.2.](#page-5-0) Besides, we adopt a 5-fold session-independent cross-validation protocol for evaluation. Two types of standard metrics, i.e., Concordance Correlation Coefficient (CCC) and Pearson Correlation Coefficient (PCC), are reported in this paper. They are computed as follows:

$$\text{PCC} = \frac{\text{cov}(y, \hat{y})}{\sigma_{\hat{y}} \sigma_{y}}$$

$$\text{CCC} = \frac{2 \text{cov}(y, \hat{y})}{\sigma_{\hat{y}}^{2} + \sigma_{y}^{2} + (\mu_{\hat{y}} - \mu_{y})^{2}}$$
(14)

<span id="page-12-3"></span>where µy<sup>ˆ</sup> and µ<sup>y</sup> are mean values of the overall predictions yˆ and overall labels y respectively, σy<sup>ˆ</sup> and σ<sup>y</sup> are their standard deviations, and cov(y, yˆ) calculates the covariance between predictions and labels.

**AVCAffe** [\[91\]](#page-16-27) is currently the largest audio-visual dataset with both affect and cognitive load attributes. It is recorded by simulating a remote work setting and contains

TABI F 14 Comparison with state-of-the-art methods on Werewolf-XL.

<span id="page-13-0"></span>

| Method            | Modality    | Dimension | PCC    | CCC    |
|-------------------|-------------|-----------|--------|--------|
| HOG [92]          | Video       | Arousal   | 0.2082 | 0.1443 |
|                   |             | Valence   | 0.5254 | 0.3456 |
|                   |             | Dominance | 0.2476 | 0.1690 |
| VGGFace-LSTM [90] | Video       | Arousal   | 0.0724 | 0.0461 |
|                   |             | Valence   | 0.6296 | 0.6038 |
|                   |             | Dominance | 0.1430 | 0.0820 |
| Zhang et al. [90] | Video+Audio | Arousal   | 0.1641 | 0.2770 |
|                   |             | Valence   | 0.6314 | 0.6234 |
|                   |             | Dominance | 0.3540 | 0.3840 |
| SVFAP-S (ours)    | Video       | Arousal   | 0.2211 | 0.1786 |
|                   |             | Valence   | 0.6566 | 0.6374 |
|                   |             | Dominance | 0.3202 | 0.2799 |
| SVFAP-B (ours)    | Video       | Arousal   | 0.2351 | 0.1896 |
|                   |             | Valence   | 0.6711 | 0.6427 |
|                   |             | Dominance | 0.3461 | 0.2969 |

TABLE 15 Comparison with state-of-the-art methods on AVCAffe.

<span id="page-13-1"></span>

| Method                      | Modality      | Arousal | Valence |
|-----------------------------|---------------|---------|---------|
| MC3-18 [76]                 | Video         | 34.00   | 38.80   |
| 3D ResNet-18 [39]           | Video         | 30.90   | 39.50   |
| $R(2+1)D-18$ [76]           | Video         | 33.30   | 34.90   |
| MC3-18+VGG-16 [91]          | $Video+Audio$ | 38.90   | 41.70   |
| 3D ResNet-18+VGG-16 [91]    | $Video+Audio$ | 37.30   | 39.40   |
| $R(2+1)D-18+VGG-16$ [91]    | $Video+Audio$ | 40.50   | 39.50   |
| MC3-18+ResNet-18 [91]       | $Video+Audio$ | 36.00   | 39.20   |
| 3D ResNet-18+ResNet-18 [91] | $Video+Audio$ | 35.10   | 39.10   |
| $R(2+1)D-18+ResNet-18$ [91] | $Video+Audio$ | 39.50   | 37.70   |
| $SVFAP-S$ (ours)            | Video         | 39.24   | 40.22   |
| $SVFAP-B$ (ours)            | Video         | 40.36   | 41.49   |

more than 108 hours of video from 106 subjects. Each subject is asked to participate in 7 specially designed tasks. After each task, self-reported affect (i.e., arousal and valence) and cognitive load scores are collected as ground truth labels. We only predict arousal and valence scores on a scale of 0-4 and formulate it as a classification problem according to the original paper. Since the duration of each task is too long  $(7.5)$ minutes), each video has been segmented into multiple 6second short clips for model training. We follow the paper to obtain video-level predictions by averaging clip-level scores and employ the weighted F1 score as the evaluation metric. The dataset provides an official split: 86 subjects for training and 20 subjects for test.

#### 4.3.2 Comparison with State-of-the-art Methods

The results on Werewolf-XL are shown in Table 14. As we can see, our method achieves much better performance than unimodal baseline methods in three emotion dimensions. Specifically, SVFAP-B outperforms the best-performing ones by about 0.04 CCC and 0.03 PCC in arousal, 0.04 CCC and 0.04 PCC in valence, and 0.13 CCC and 0.10 PCC in dominance. Besides, we also show the multimodal baseline in the table. Compared with it, SVFAP-B still shows superior performance in valence, although worse results are achieved in arousal and dominance. Besides, we only observe a moderate performance degradation for SVFAP-S on this dataset.

We further present the comparison results on AVCAffe in Table 15. Similarly, we observe that both SVFAP-B and SVFAP-S surpass the state-of-the-art unimodal methods by

TABLE 16

<span id="page-13-2"></span>

| Comparison with state-of-the-art methods on Challearn 2016 First  |  |
|-------------------------------------------------------------------|--|
| Impression in terms of CCC. O: Openness. C: Conscientiousness. E: |  |
| Extraversion. A: Agreeableness. N: Neuroticism.                   |  |

| Method          | O      | C      | E      | A      | N      | Average |
|-----------------|--------|--------|--------|--------|--------|---------|
| DAN [93]        | 0.5693 | 0.6254 | 0.6070 | 0.4855 | 0.6025 | 0.5779  |
| ResNet [94]     | 0.1561 | 0.1902 | 0.1355 | 0.0838 | 0.1373 | 0.1406  |
| CRNet [95]      | 0.3748 | 0.3646 | 0.3987 | 0.2390 | 0.3226 | 0.3399  |
| CAM-DAN+ [96]   | 0.5882 | 0.6550 | 0.6326 | 0.5003 | 0.6199 | 0.5992  |
| PersEmoN [97]   | 0.2067 | 0.2441 | 0.2675 | 0.1369 | 0.1768 | 0.2064  |
| Amb-Fac [98]    | 0.5858 | 0.6750 | 0.5997 | 0.4971 | 0.5765 | 0.5868  |
| SENet [99]      | 0.5300 | 0.5580 | 0.5815 | 0.4493 | 0.5708 | 0.5379  |
| HRNet [100]     | 0.5923 | 0.6912 | 0.6436 | 0.5195 | 0.6273 | 0.6148  |
| Swin [56]       | 0.2223 | 0.2426 | 0.2531 | 0.1224 | 0.1942 | 0.2069  |
| 3D ResNet [39]  | 0.3248 | 0.3601 | 0.3601 | 0.2120 | 0.3352 | 0.3185  |
| Slow-Fast [101] | 0.0256 | 0.0320 | 0.0185 | 0.0105 | 0.0184 | 0.0210  |
| TPN [102]       | 0.4427 | 0.4767 | 0.4998 | 0.3230 | 0.4675 | 0.4420  |
| VAT [103]       | 0.6216 | 0.6753 | 0.6836 | 0.5228 | 0.6456 | 0.6298  |
| SVFAP-S (ours)  | 0.6313 | 0.6974 | 0.7210 | 0.5427 | 0.6648 | 0.6514  |
| SVFAP-B (ours)  | 0.6511 | 0.7141 | 0.7351 | 0.5498 | 0.6724 | 0.6645  |

<span id="page-13-3"></span>TABI F 17 Comparison with state-of-the-art methods on ChaLearn 2016 First Impression in terms of ACC. O: Openness. C: Conscientiousness. E: Extraversion. A: Agreeableness. N: Neuroticism.

| Method          | O             | C             | E             | A             | N             | Average       |
|-----------------|---------------|---------------|---------------|---------------|---------------|---------------|
| DAN [93]        | 0.9098        | 0.9106        | 0.9096        | 0.9102        | 0.9061        | 0.9093        |
| CNN-LSTM [104]  | 0.8832        | 0.8742        | 0.8778        | 0.8933        | 0.8770        | 0.8811        |
| ResNet [94]     | 0.8896        | 0.8835        | 0.8837        | 0.8968        | 0.8830        | 0.8873        |
| CRNet [95]      | 0.8987        | 0.8932        | 0.8952        | 0.9018        | 0.8908        | 0.8960        |
| CAM-DAN+ [96]   | 0.9115        | 0.9139        | 0.9126        | 0.9118        | 0.9089        | 0.9118        |
| PersEmoN [97]   | 0.8934        | 0.8893        | 0.8913        | 0.8994        | 0.8866        | 0.8920        |
| Amb-Fac [98]    | 0.9101        | 0.9141        | 0.9082        | 0.9095        | 0.9038        | 0.9091        |
| SENet [99]      | 0.9076        | 0.9060        | 0.9080        | 0.9097        | 0.9061        | 0.9075        |
| HRNet [100]     | 0.9101        | 0.9154        | 0.9111        | 0.9113        | 0.9084        | 0.9113        |
| Swin [56]       | 0.8937        | 0.8870        | 0.8893        | 0.8983        | 0.8860        | 0.8909        |
| 3D ResNet [39]  | 0.8964        | 0.8921        | 0.8933        | 0.9008        | 0.8915        | 0.8948        |
| Slow-Fast [101] | 0.8780        | 0.8604        | 0.8443        | 0.8809        | 0.8613        | 0.8650        |
| TPN [102]       | 0.9025        | 0.8963        | 0.9019        | 0.9013        | 0.8992        | 0.9003        |
| VAT [103]       | 0.9115        | 0.9123        | 0.9153        | 0.9099        | 0.9098        | 0.9118        |
| SVFAP-S (ours)  | 0.9144        | 0.9175        | 0.9208        | 0.9135        | 0.9134        | 0.9159        |
| SVFAP-B (ours)  | <b>0.9162</b> | <b>0.9187</b> | <b>0.9227</b> | <b>0.9152</b> | <b>0.9145</b> | <b>0.9175</b> |

a large margin (especially in arousal). For instance, SVFAP-B achieves about 6% F1-score improvement in arousal and about 2% in valence. Moreover, when compared with multimodal methods, our base model still presents a comparable performance in both arousal and valence, which verifies the effectiveness of large-scale self-supervised pre-training for dimension emotion recognition.

### 4.4 Personality Recognition

Finally, to further verify the general applicability of the proposed method, we evaluate it on the personality recognition task. Different from the above two tasks we have explored, this task requires stable and prototypical facial behavior modeling to capture relevant features that reflect personality traits. Thus, experiments on this task can provide a more comprehensive evaluation of our proposed method.

The classic ChaLearn First Impression dataset [105] is selected for evaluation. It consists of 10,000 talking-tothe-camera clips extracted from over 3,000 high-definition YouTube videos. Each video clip has a duration of about 15 seconds and is annotated with the Big Five personality traits (i.e., openness, conscientiousness, extraversion, agreeableness, and neuroticism). This dataset has been split into three sets: 6000 videos for training, 2000 videos for validation,

and 2000 videos for the final test. Since the task is to predict continuous scores in different personality dimensions, we formulate it as a regression problem. Following [\[106\]](#page-17-0), we use two standard evaluation metrics, i.e., CCC and the Accuracy (ACC). CCC is defined in Eq. [\(14\)](#page-12-3). The definition of ACC is given as follows:

$$\text{ACC} = 1 - \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i| \tag{15}$$

where yˆ is the prediction, y is the label, and N is the number of test videos.

The comparison results in terms of CCC and ACC are shown in Table [16](#page-13-2) and Table [17,](#page-13-3) respectively. For CCC, we observe that two versions of our models achieve similar performance. Both of them outperform the best-performing supervised baseline largely, achieving about 0.02-0.03 CCC improvement. For ACC, we find that the variation between different methods is relatively small. Nevertheless, our methods still show the best performance.

## **5 CONCLUSION**

In this paper, we have presented a self-supervised learning method, termed Self-supervised Video Facial Affect Perceiver (SVFAP), to unleash the power of large-scale selfsupervised pre-training for video-based facial affect analysis. SVFAP utilizes masked facial video autoencoding as the objective to perform self-supervised pre-training on a large amount of unlabeled facial videos. Besides, it employs a novel TBSBT model as the encoder to minimize large redundancy in 3D facial video data from both spatial and temporal perspectives, leading to significantly lower computational costs and superior performance. To verify the effectiveness of SVFAP, we conduct extensive experiments on nine datasets in three popular downstream tasks, including dynamic facial expression recognition, dimensional emotion recognition, and personality recognition. The results demonstrate that SVFAP can learn powerful affect-related representations via large-scale self-supervised pre-training. Specifically, it largely outperforms previous pre-trained supervised and self-supervised models and also shows strong adaptation ability in the low data regime. Moreover, our SVFAP achieves significant improvements over state-of-theart methods in three downstream tasks, setting new records on all datasets.

In future work, we plan to investigate the scaling behavior of SVFAP using larger models and more unlabeled data. Besides, it is also interesting to evaluate SVFAP in other downstream tasks, such as dynamic micro-expression recognition and depression level detection. We also hope our work can inspire more relevant research to further advance the development of video-based facial affect analysis.

## **ACKNOWLEDGMENTS**

This work is supported by the National Natural Science Foundation of China (NSFC) ( No.62276259, No.62201572, No.U21B2010, No.62271083, No.62306316).

## **REFERENCES**

- <span id="page-14-0"></span>[1] M. Pantic and L. J. M. Rothkrantz, "Automatic analysis of facial expressions: The state of the art," *IEEE Transactions on pattern analysis and machine intelligence*, vol. 22, no. 12, pp. 1424–1445, 2000.
- <span id="page-14-1"></span>[2] P. V. Rouast, M. T. Adam, and R. Chiong, "Deep learning for human affect recognition: Insights and new developments," *IEEE Transactions on Affective Computing*, vol. 12, no. 2, pp. 524–543, 2019.
- <span id="page-14-2"></span>[3] E. Sariyanidi, H. Gunes, and A. Cavallaro, "Automatic analysis of facial affect: A survey of registration, representation, and recognition," *IEEE transactions on pattern analysis and machine intelligence*, vol. 37, no. 6, pp. 1113–1133, 2014.
- <span id="page-14-3"></span>[4] S. Zhao, X. Yao, J. Yang, G. Jia, G. Ding, T.-S. Chua, B. W. Schuller, and K. Keutzer, "Affective image content analysis: Two decades review and new perspectives," *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 44, no. 10, pp. 6729–6751, 2021.
- <span id="page-14-4"></span>[5] Y. Fan, X. Lu, D. Li, and Y. Liu, "Video-based emotion recognition using cnn-rnn and c3d hybrid networks," in *Proceedings of the 18th ACM international conference on multimodal interaction*, 2016, pp. 445–450.
- <span id="page-14-5"></span>[6] X. Jiang, Y. Zong, W. Zheng, C. Tang, W. Xia, C. Lu, and J. Liu, "Dfew: A large-scale database for recognizing dynamic facial expressions in the wild," in *Proceedings of the 28th ACM International Conference on Multimedia*, 2020, pp. 2881–2889.
- <span id="page-14-6"></span>[7] S. Ebrahimi Kahou, V. Michalski, K. Konda, R. Memisevic, and C. Pal, "Recurrent neural networks for emotion recognition in video," in *Proceedings of the 2015 ACM on international conference on multimodal interaction*, 2015, pp. 467–474.
- <span id="page-14-7"></span>[8] L. Chao, J. Tao, M. Yang, Y. Li, and Z. Wen, "Long short term memory recurrent neural network based multimodal dimensional emotion recognition," in *Proceedings of the 5th international workshop on audio/visual emotion challenge*, 2015, pp. 65–72.
- <span id="page-14-8"></span>[9] R. Zhao, T. Liu, Z. Huang, D. P. Lun, and K.-M. Lam, "Spatialtemporal graphs plus transformers for geometry-guided facial expression recognition," *IEEE Transactions on Affective Computing*, 2022.
- <span id="page-14-9"></span>[10] Y. Liu, W. Wang, C. Feng, H. Zhang, Z. Chen, and Y. Zhan, "Expression snippet transformer for robust video-based facial expression recognition," *arXiv preprint arXiv:2109.08409*, 2021.
- <span id="page-14-10"></span>[11] D. Kollias and S. Zafeiriou, "Exploiting multi-cnn features in cnnrnn based dimensional emotion recognition on the omg in-thewild dataset," *IEEE Transactions on Affective Computing*, vol. 12, no. 3, pp. 595–606, 2020.
- <span id="page-14-11"></span>[12] L. Sun, Z. Lian, J. Tao, B. Liu, and M. Niu, "Multi-modal continuous dimensional emotion recognition using recurrent neural network and self-attention mechanism," in *Proceedings of the 1st International on Multimodal Sentiment Analysis in Real-life Media Challenge and Workshop*, 2020, pp. 27–34.
- <span id="page-14-12"></span>[13] Z. Zhao and Q. Liu, "Former-dfer: Dynamic facial expression recognition transformer," in *Proceedings of the 29th ACM International Conference on Multimedia*, 2021, pp. 1553–1561.
- <span id="page-14-13"></span>[14] F. Ma, B. Sun, and S. Li, "Spatio-temporal transformer for dynamic facial expression recognition in the wild," *arXiv preprint arXiv:2205.04749*, 2022.
- <span id="page-14-14"></span>[15] S. Li and W. Deng, "Deep facial expression recognition: A survey," *IEEE transactions on affective computing*, vol. 13, no. 3, pp. 1195–1215, 2020.
- <span id="page-14-15"></span>[16] C. Zhang, S. Bengio, M. Hardt, B. Recht, and O. Vinyals, "Understanding deep learning (still) requires rethinking generalization," *Communications of the ACM*, vol. 64, no. 3, pp. 107–115, 2021.
- <span id="page-14-16"></span>[17] R. Lotfian and C. Busso, "Formulating emotion perception as a probabilistic model with application to categorical emotion classification," in *2017 Seventh International Conference on Affective Computing and Intelligent Interaction (ACII)*. IEEE, 2017, pp. 415– 420.
- <span id="page-14-17"></span>[18] V. Sethu, E. M. Provost, J. Epps, C. Busso, N. Cummins, and S. Narayanan, "The ambiguous world of emotion representation," *arXiv preprint arXiv:1909.00360*, 2019.
- <span id="page-14-18"></span>[19] X. Liu, F. Zhang, Z. Hou, L. Mian, Z. Wang, J. Zhang, and J. Tang, "Self-supervised learning: Generative or contrastive," *IEEE Transactions on Knowledge and Data Engineering*, vol. 35, no. 1, pp. 857–876, 2021.
- <span id="page-14-19"></span>[20] L. Jing and Y. Tian, "Self-supervised visual feature learning with deep neural networks: A survey," *IEEE transactions on pattern analysis and machine intelligence*, vol. 43, no. 11, pp. 4037–4058, 2020.

- <span id="page-15-0"></span>[21] C. Zhang, C. Zhang, J. Song, J. S. K. Yi, K. Zhang, and I. S. Kweon, "A survey on masked autoencoder for self-supervised learning in vision and beyond," *arXiv preprint arXiv:2208.00173*, 2022.
- <span id="page-15-1"></span>[22] J. Devlin, M.-W. Chang, K. Lee, and K. Toutanova, "Bert: Pretraining of deep bidirectional transformers for language understanding," *arXiv preprint arXiv:1810.04805*, 2018.
- <span id="page-15-2"></span>[23] K. He, X. Chen, S. Xie, Y. Li, P. Dollar, and R. Girshick, "Masked ´ autoencoders are scalable vision learners," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 16 000–16 009.
- <span id="page-15-3"></span>[24] Z. Tong, Y. Song, J. Wang, and L. Wang, "VideoMAE: Masked autoencoders are data-efficient learners for self-supervised video pre-training," in *Advances in Neural Information Processing Systems*, 2022.
- <span id="page-15-4"></span>[25] C. Feichtenhofer, H. Fan, Y. Li, and K. He, "Masked autoencoders as spatiotemporal learners," *arXiv preprint arXiv:2205.09113*, 2022.
- <span id="page-15-5"></span>[26] A. Dosovitskiy, L. Beyer, A. Kolesnikov, D. Weissenborn, X. Zhai, T. Unterthiner, M. Dehghani, M. Minderer, G. Heigold, S. Gelly *et al.*, "An image is worth 16x16 words: Transformers for image recognition at scale," *arXiv preprint arXiv:2010.11929*, 2020.
- <span id="page-15-6"></span>[27] Y. Wang, Y. Sun, Y. Huang, Z. Liu, S. Gao, W. Zhang, W. Ge, and W. Zhang, "Ferv39k: A large-scale multi-scene dataset for facial expression recognition in videos," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 20 922–20 931.
- <span id="page-15-7"></span>[28] Y. Liu, W. Dai, C. Feng, W. Wang, G. Yin, J. Zeng, and S. Shan, "Mafw: A large-scale, multi-modal, compound affective database for dynamic facial expression recognition in the wild," in *Proceedings of the 30th ACM International Conference on Multimedia*, 2022, pp. 24–32.
- <span id="page-15-8"></span>[29] Y. Wang, Y. Sun, W. Song, S. Gao, Y. Huang, Z. Chen, W. Ge, and W. Zhang, "Dpcnet: Dual path multi-excitation collaborative network for facial expression representation learning in videos," in *Proceedings of the 30th ACM International Conference on Multimedia*, 2022, pp. 101–110.
- <span id="page-15-9"></span>[30] K. Simonyan and A. Zisserman, "Very deep convolutional networks for large-scale image recognition," *arXiv preprint arXiv:1409.1556*, 2014.
- <span id="page-15-10"></span>[31] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in *Proceedings of the IEEE conference on computer vision and pattern recognition*, 2016, pp. 770–778.
- <span id="page-15-11"></span>[32] S. Hochreiter and J. Schmidhuber, "Long short-term memory," *Neural computation*, vol. 9, no. 8, pp. 1735–1780, 1997.
- <span id="page-15-12"></span>[33] J. Chung, C. Gulcehre, K. Cho, and Y. Bengio, "Empirical evaluation of gated recurrent neural networks on sequence modeling," *arXiv preprint arXiv:1412.3555*, 2014.
- <span id="page-15-13"></span>[34] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez, Ł. Kaiser, and I. Polosukhin, "Attention is all you need," *Advances in neural information processing systems*, vol. 30, 2017.
- <span id="page-15-14"></span>[35] H. Li, H. Niu, Z. Zhu, and F. Zhao, "Intensity-aware loss for dynamic facial expression recognition in the wild," in *Proceedings of the AAAI Conference on Artificial Intelligence*, vol. 37, no. 1, 2023, pp. 67–75.
- <span id="page-15-15"></span>[36] D. Tran, L. Bourdev, R. Fergus, L. Torresani, and M. Paluri, "Learning spatiotemporal features with 3d convolutional networks," in *Proceedings of the IEEE international conference on computer vision*, 2015, pp. 4489–4497.
- <span id="page-15-16"></span>[37] J. Carreira and A. Zisserman, "Quo vadis, action recognition? a new model and the kinetics dataset," in *proceedings of the IEEE Conference on Computer Vision and Pattern Recognition*, 2017, pp. 6299–6308.
- <span id="page-15-17"></span>[38] Z. Qiu, T. Yao, and T. Mei, "Learning spatio-temporal representation with pseudo-3d residual networks," in *proceedings of the IEEE International Conference on Computer Vision*, 2017, pp. 5533–5541.
- <span id="page-15-18"></span>[39] K. Hara, H. Kataoka, and Y. Satoh, "Can spatiotemporal 3d cnns retrace the history of 2d cnns and imagenet?" in *Proceedings of the IEEE conference on Computer Vision and Pattern Recognition*, 2018, pp. 6546–6555.
- <span id="page-15-19"></span>[40] N. Komodakis and S. Gidaris, "Unsupervised representation learning by predicting image rotations," in *International conference on learning representations (ICLR)*, 2018.
- <span id="page-15-20"></span>[41] H.-Y. Lee, J.-B. Huang, M. Singh, and M.-H. Yang, "Unsupervised representation learning by sorting sequences," in *Proceedings of the IEEE international conference on computer vision*, 2017, pp. 667– 676.
- <span id="page-15-21"></span>[42] K. He, H. Fan, Y. Wu, S. Xie, and R. Girshick, "Momentum contrast for unsupervised visual representation learning," in *Pro-*

*ceedings of the IEEE/CVF conference on computer vision and pattern recognition*, 2020, pp. 9729–9738.

- <span id="page-15-22"></span>[43] M. Caron, I. Misra, J. Mairal, P. Goyal, P. Bojanowski, and A. Joulin, "Unsupervised learning of visual features by contrasting cluster assignments," *Advances in Neural Information Processing Systems*, vol. 33, pp. 9912–9924, 2020.
- <span id="page-15-23"></span>[44] P. Vincent, H. Larochelle, Y. Bengio, and P.-A. Manzagol, "Extracting and composing robust features with denoising autoencoders," in *Proceedings of the 25th international conference on Machine learning*, 2008, pp. 1096–1103.
- <span id="page-15-24"></span>[45] A. Radford, K. Narasimhan, T. Salimans, I. Sutskever *et al.*, "Improving language understanding by generative pre-training," 2018.
- <span id="page-15-25"></span>[46] H. Bao, L. Dong, S. Piao, and F. Wei, "Beit: Bert pre-training of image transformers," *arXiv preprint arXiv:2106.08254*, 2021.
- <span id="page-15-26"></span>[47] S. Roy and A. Etemad, "Spatiotemporal contrastive learning of facial expressions in videos," in *2021 9th International Conference on Affective Computing and Intelligent Interaction (ACII)*. IEEE, 2021, pp. 1–8.
- <span id="page-15-27"></span>[48] O. Wiles, A. Koepke, and A. Zisserman, "Self-supervised learning of a facial attribute embedding from video," *arXiv preprint arXiv:1808.06882*, 2018.
- <span id="page-15-28"></span>[49] Y. Li, J. Zeng, S. Shan, and X. Chen, "Self-supervised representation learning from videos for facial action unit detection," in *Proceedings of the IEEE/CVF Conference on Computer vision and pattern recognition*, 2019, pp. 10 924–10 933.
- <span id="page-15-29"></span>[50] J.-R. Chang, Y.-S. Chen, and W.-C. Chiu, "Learning facial representations from the cycle-consistency of face," in *Proceedings of the IEEE/CVF International Conference on Computer Vision*, 2021, pp. 9680–9689.
- <span id="page-15-30"></span>[51] L. Lu, L. Tavabi, and M. Soleymani, "Self-supervised learning for facial action unit recognition through temporal consistency," in *BMVC*, 2020.
- <span id="page-15-31"></span>[52] A. Bulat, S. Cheng, J. Yang, A. Garbett, E. Sanchez, and G. Tzimiropoulos, "Pre-training strategies and datasets for facial representation learning," in *European Conference on Computer Vision*. Springer, 2022, pp. 107–125.
- <span id="page-15-32"></span>[53] Y. Zheng, H. Yang, T. Zhang, J. Bao, D. Chen, Y. Huang, L. Yuan, D. Chen, M. Zeng, and F. Wen, "General facial representation learning in a visual-linguistic manner," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 18 697–18 709.
- <span id="page-15-33"></span>[54] K. Han, Y. Wang, H. Chen, X. Chen, J. Guo, Z. Liu, Y. Tang, A. Xiao, C. Xu, Y. Xu *et al.*, "A survey on vision transformer," *IEEE transactions on pattern analysis and machine intelligence*, vol. 45, no. 1, pp. 87–110, 2022.
- <span id="page-15-34"></span>[55] H. Touvron, M. Cord, M. Douze, F. Massa, A. Sablayrolles, and H. Jegou, "Training data-efficient image transformers & distil- ´ lation through attention," in *International conference on machine learning*. PMLR, 2021, pp. 10 347–10 357.
- <span id="page-15-35"></span>[56] Z. Liu, Y. Lin, Y. Cao, H. Hu, Y. Wei, Z. Zhang, S. Lin, and B. Guo, "Swin transformer: Hierarchical vision transformer using shifted windows," in *Proceedings of the IEEE/CVF International Conference on Computer Vision*, 2021, pp. 10 012–10 022.
- <span id="page-15-36"></span>[57] G. Bertasius, H. Wang, and L. Torresani, "Is space-time attention all you need for video understanding?" in *ICML*, vol. 2, no. 3, 2021, p. 4.
- <span id="page-15-37"></span>[58] H. Fan, B. Xiong, K. Mangalam, Y. Li, Z. Yan, J. Malik, and C. Feichtenhofer, "Multiscale vision transformers," in *Proceedings of the IEEE/CVF International Conference on Computer Vision*, 2021, pp. 6824–6835.
- <span id="page-15-38"></span>[59] Y. Li, C.-Y. Wu, H. Fan, K. Mangalam, B. Xiong, J. Malik, and C. Feichtenhofer, "Mvitv2: Improved multiscale vision transformers for classification and detection," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 4804–4814.
- <span id="page-15-39"></span>[60] Z. Liu, J. Ning, Y. Cao, Y. Wei, Z. Zhang, S. Lin, and H. Hu, "Video swin transformer," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 3202–3211.
- <span id="page-15-40"></span>[61] D. Hendrycks and K. Gimpel, "Gaussian error linear units (gelus)," *arXiv preprint arXiv:1606.08415*, 2016.
- <span id="page-15-41"></span>[62] A. Jaegle, F. Gimeno, A. Brock, O. Vinyals, A. Zisserman, and J. Carreira, "Perceiver: General perception with iterative attention," in *International conference on machine learning*. PMLR, 2021, pp. 4651–4664.
- <span id="page-15-42"></span>[63] J. S. Chung, A. Nagrani, and A. Zisserman, "Voxceleb2: Deep speaker recognition," *Proc. Interspeech 2018*, pp. 1086–1090, 2018.

- <span id="page-16-0"></span>[64] H. Cao, D. G. Cooper, M. K. Keutmann, R. C. Gur, A. Nenkova, and R. Verma, "Crema-d: Crowd-sourced emotional multimodal actors dataset," *IEEE transactions on affective computing*, vol. 5, no. 4, pp. 377–390, 2014.
- <span id="page-16-1"></span>[65] S. R. Livingstone and F. A. Russo, "The ryerson audio-visual database of emotional speech and song (ravdess): A dynamic, multimodal set of facial and vocal expressions in north american english," *PloS one*, vol. 13, no. 5, p. e0196391, 2018.
- <span id="page-16-2"></span>[66] O. Martin, I. Kotsia, B. Macq, and I. Pitas, "The enterface'05 audio-visual emotion database," in *22nd International Conference on Data Engineering Workshops (ICDEW'06)*. IEEE, 2006, pp. 8–8.
- <span id="page-16-3"></span>[67] L. Su, C. Hu, G. Li, and D. Cao, "Msaf: Multimodal split attention fusion," *arXiv preprint arXiv:2012.07175*, 2020.
- <span id="page-16-4"></span>[68] Z. Fu, F. Liu, H. Wang, J. Qi, X. Fu, A. Zhou, and Z. Li, "A cross-modal fusion network based on self-attention and residual structure for multimodal emotion recognition," *arXiv preprint arXiv:2111.02172*, 2021.
- <span id="page-16-5"></span>[69] Y. Liu, E. Sangineto, W. Bi, N. Sebe, B. Lepri, and M. Nadai, "Efficient training of visual transformers with small datasets," *Advances in Neural Information Processing Systems*, vol. 34, pp. 23 818–23 830, 2021.
- <span id="page-16-6"></span>[70] N. Zhao, Z. Wu, R. W. Lau, and S. Lin, "What makes instance discrimination good for transfer learning?" in *International Conference on Learning Representations*, 2020.
- <span id="page-16-7"></span>[71] C. Feichtenhofer, H. Fan, B. Xiong, R. Girshick, and K. He, "A large-scale study on unsupervised spatiotemporal representation learning," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2021, pp. 3299–3309.
- <span id="page-16-8"></span>[72] K. Ranasinghe, M. Naseer, S. Khan, F. S. Khan, and M. S. Ryoo, "Self-supervised video transformer," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2022, pp. 2874–2884.
- <span id="page-16-9"></span>[73] Y. Liu, C. Feng, X. Yuan, L. Zhou, W. Wang, J. Qin, and Z. Luo, "Clip-aware expressive feature learning for video-based facial expression recognition," *Information Sciences*, vol. 598, pp. 182– 195, 2022.
- <span id="page-16-10"></span>[74] H. Li, M. Sui, Z. Zhu *et al.*, "Nr-dfernet: Noise-robust network for dynamic facial expression recognition," *arXiv preprint arXiv:2206.04975*, 2022.
- <span id="page-16-11"></span>[75] H. Wang, B. Li, S. Wu, S. Shen, F. Liu, S. Ding, and A. Zhou, "Rethinking the learning paradigm for dynamic facial expression recognition," in *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, 2023, pp. 17 958–17 968.
- <span id="page-16-12"></span>[76] D. Tran, H. Wang, L. Torresani, J. Ray, Y. LeCun, and M. Paluri, "A closer look at spatiotemporal convolutions for action recognition," in *Proceedings of the IEEE conference on Computer Vision and Pattern Recognition*, 2018, pp. 6450–6459.
- <span id="page-16-13"></span>[77] E. Ghaleb, M. Popa, and S. Asteriadis, "Multimodal and temporal perception of audio-visual cues for emotion recognition," in *2019 8th International Conference on Affective Computing and Intelligent Interaction (ACII)*. IEEE, 2019, pp. 552–558.
- <span id="page-16-14"></span>[78] L. Goncalves and C. Busso, "Robust audiovisual emotion recognition: Aligning modalities, capturing temporal information, and handling missing features," *IEEE Transactions on Affective Computing*, vol. 13, no. 04, pp. 2156–2170, 2022.
- <span id="page-16-15"></span>[79] Y. Lei and H. Cao, "Audio-visual emotion recognition with preference learning based on intended and multi-modal perceived labels," *IEEE Transactions on Affective Computing*, pp. 1–16, 2023.
- <span id="page-16-16"></span>[80] A. Zadeh, M. Chen, S. Poria, E. Cambria, and L.-P. Morency, "Tensor fusion network for multimodal sentiment analysis," in *Proceedings of the 2017 Conference on Empirical Methods in Natural Language Processing*, 2017, pp. 1103–1114.
- <span id="page-16-17"></span>[81] M. Tran and M. Soleymani, "A pre-trained audio-visual transformer for emotion recognition," in *ICASSP 2022-2022 IEEE International Conference on Acoustics, Speech and Signal Processing (ICASSP)*. IEEE, 2022, pp. 4698–4702.
- <span id="page-16-18"></span>[82] M. Mansoorizadeh and N. Moghaddam Charkari, "Multimodal information fusion application to human emotion recognition from face and speech," *Multimedia Tools and Applications*, vol. 49, no. 2, pp. 277–297, 2010.
- <span id="page-16-19"></span>[83] Y.-H. Byeon and K.-C. Kwak, "Facial expression recognition using 3d convolutional neural network," *International journal of advanced computer science and applications*, vol. 5, no. 12, 2014.
- <span id="page-16-20"></span>[84] S. Zhalehpour, O. Onder, Z. Akhtar, and C. E. Erdem, "Baum-1: A spontaneous audio-visual face database of affective and mental states," *IEEE Transactions on Affective Computing*, vol. 8, no. 3, pp. 300–313, 2016.

- <span id="page-16-21"></span>[85] D. Meng, X. Peng, K. Wang, and Y. Qiao, "Frame attention networks for facial expression recognition in videos," in *2019 IEEE international conference on image processing (ICIP)*. IEEE, 2019, pp. 3866–3870.
- <span id="page-16-22"></span>[86] X. Pan, G. Ying, G. Chen, H. Li, and W. Li, "A deep spatial and temporal aggregation framework for video-based facial expression recognition," *IEEE Access*, vol. 7, pp. 48 807–48 815, 2019.
- <span id="page-16-23"></span>[87] X. Pan, W. Guo, X. Guo, W. Li, J. Xu, and J. Wu, "Deep temporal– spatial aggregation for video-based facial expression recognition," *Symmetry*, vol. 11, no. 1, p. 52, 2019.
- <span id="page-16-24"></span>[88] R. Miyoshi, N. Nagata, and M. Hashimoto, "Facial-expression recognition from video using enhanced convolutional lstm," in *2019 Digital Image Computing: Techniques and Applications (DICTA)*. IEEE, 2019, pp. 1–6.
- <span id="page-16-25"></span>[89] R. Miyoshi, N. Nagata, and M. Hashimoto, "Enhanced convolutional lstm with spatial and temporal skip connections and temporal gates for facial expression recognition from video," *Neural Computing and Applications*, vol. 33, no. 13, pp. 7381–7392, 2021.
- <span id="page-16-26"></span>[90] K. Zhang, X. Wu, X. Xie, X. Zhang, H. Zhang, X. Chen, and L. Sun, "Werewolf-xl: A database for identifying spontaneous affect in large competitive group interactions," *IEEE Transactions on Affective Computing*, vol. 14, no. 02, pp. 1201–1214, 2023.
- <span id="page-16-27"></span>[91] P. Sarkar, A. Posen, and A. Etemad, "Avcaffe: A large scale audiovisual dataset of cognitive load and affect for remote work," *arXiv preprint arXiv:2205.06887*, 2022.
- <span id="page-16-28"></span>[92] N. Dalal and B. Triggs, "Histograms of oriented gradients for human detection," in *2005 IEEE computer society conference on computer vision and pattern recognition (CVPR'05)*, vol. 1. Ieee, 2005, pp. 886–893.
- <span id="page-16-29"></span>[93] X.-S. Wei, C.-L. Zhang, H. Zhang, and J. Wu, "Deep bimodal regression of apparent personality traits from short video sequences," *IEEE Transactions on Affective Computing*, vol. 9, no. 3, pp. 303–315, 2017.
- <span id="page-16-30"></span>[94] Y. Guc¸l ¨ ut¨ urk, U. G ¨ uc¸l ¨ u, M. A. van Gerven, and R. van Lier, "Deep ¨ impression: Audiovisual deep residual networks for multimodal apparent personality trait recognition," in *European conference on computer vision*. Springer, 2016, pp. 349–358.
- <span id="page-16-31"></span>[95] Y. Li, J. Wan, Q. Miao, S. Escalera, H. Fang, H. Chen, X. Qi, and G. Guo, "Cr-net: A deep classification-regression network for multimodal apparent personality analysis," *International Journal of Computer Vision*, vol. 128, no. 12, pp. 2763–2780, 2020.
- <span id="page-16-32"></span>[96] C. Ventura, D. Masip, and A. Lapedriza, "Interpreting cnn models for apparent personality trait regression," in *Proceedings of the IEEE conference on computer vision and pattern recognition workshops*, 2017, pp. 55–63.
- <span id="page-16-33"></span>[97] L. Zhang, S. Peng, and S. Winkler, "Persemon: a deep network for joint analysis of apparent personality, emotion and their relationship," *IEEE Transactions on Affective Computing*, 2019.
- <span id="page-16-34"></span>[98] C. Suman, S. Saha, A. Gupta, S. K. Pandey, and P. Bhattacharyya, "A multi-modal personality prediction system," *Knowledge-Based Systems*, vol. 236, p. 107715, 2022.
- <span id="page-16-35"></span>[99] J. Hu, L. Shen, and G. Sun, "Squeeze-and-excitation networks," in *Proceedings of the IEEE conference on computer vision and pattern recognition*, 2018, pp. 7132–7141.
- <span id="page-16-36"></span>[100] J. Wang, K. Sun, T. Cheng, B. Jiang, C. Deng, Y. Zhao, D. Liu, Y. Mu, M. Tan, X. Wang *et al.*, "Deep high-resolution representation learning for visual recognition," *IEEE transactions on pattern analysis and machine intelligence*, vol. 43, no. 10, pp. 3349–3364, 2020.
- <span id="page-16-37"></span>[101] C. Feichtenhofer, H. Fan, J. Malik, and K. He, "Slowfast networks for video recognition," in *Proceedings of the IEEE/CVF international conference on computer vision*, 2019, pp. 6202–6211.
- <span id="page-16-38"></span>[102] C. Yang, Y. Xu, J. Shi, B. Dai, and B. Zhou, "Temporal pyramid network for action recognition," in *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition*, 2020, pp. 591– 600.
- <span id="page-16-39"></span>[103] R. Girdhar, J. Carreira, C. Doersch, and A. Zisserman, "Video action transformer network," in *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition*, 2019, pp. 244–253.
- <span id="page-16-40"></span>[104] A. Subramaniam, V. Patel, A. Mishra, P. Balasubramanian, and A. Mittal, "Bi-modal first impressions recognition using temporally ordered deep audio and stochastic visual features," in *European conference on computer vision*. Springer, 2016, pp. 337– 348.
- <span id="page-16-41"></span>[105] V. Ponce-Lopez, B. Chen, M. Oliu, C. Corneanu, A. Clap ´ es, ´ I. Guyon, X. Baro, H. J. Escalante, and S. Escalera, "Chalearn ´

#### JOURNAL OF LATEX CLASS FILES, VOL. 14, NO. 8, AUGUST 2015 18

lap 2016: First round challenge on first impressions-dataset and results," in *European conference on computer vision*. Springer, 2016, pp. 400–418.

<span id="page-17-0"></span>[106] R. Liao, S. Song, and H. Gunes, "An open-source benchmark of deep learning models for audio-visual apparent and selfreported personality recognition," *IEEE Transactions on Affective Computing*, 2024.

![](_page_17_Picture_3.jpeg)

**Mingyu Xu** received the B.S. degree from Peking University, Beijing, China, in 2021. He is currently working toward the M.S. degree with the Institute of Automation, China Academy of Sciences, Beijing, China. His current research interests include uncertainty learning and partial label learning.

![](_page_17_Picture_5.jpeg)

**Licai Sun** received the B.S. degree from Beijing Forestry University, Beijing, China, in 2016, and the M.S. degree from University of Chinese Academy of Sciences, Beijing, China, in 2019. He is currently working toward the Ph.D. degree with the School of Artificial Intelligence, University of Chinese Academy of Sciences, Beijing, China. His current research interests include affective computing, deep learning, and multimodal representation learning.

![](_page_17_Picture_7.jpeg)

**Haiyang Sun** received the B.E. degree from Shandong University of Science and Technology, China, in 2021. He is currently working toward the M.S. degree with the Institute of Automation, China Academy of Sciences, Beijing, China. His current research interests include multimodal emotion recognition and neural architecture search.

![](_page_17_Picture_9.jpeg)

cations (BUPT), Beijing, China, in 2016. And he received the Ph.D. degree from the Institute of Automation, Chinese Academy of Sciences, Beijing, China, in 2021. He is currently an Assistant Professor at National Laboratory of Pattern Recognition, Institute of Automation, Chinese Academy of Sciences, Beijing, China. His current research interests include affective computing, deep learning, and multimodal emotion

**Zheng Lian** received the B.S. degree from the Beijing University of Posts and Telecommuni-

recognition.

![](_page_17_Picture_12.jpeg)

**Bin Liu** received his the B.S. degree and the M.S. degree from Beijing institute of technology (BIT), Beijing, China, in 2007 and 2009 respectively. He received Ph.D. degree from the National Laboratory of Pattern Recognition, Institute of Automation, Chinese Academy of Sciences, Beijing, China, in 2015. He is currently an Associate Professor in the National Laboratory of Pattern Recognition, Institute of Automation, Chinese Academy of Sciences, Beijing, China. His current research interests include affective

computing and audio signal processing.

![](_page_17_Picture_15.jpeg)

**Kexin Wang** received the B.S. degree from Beijing University of Aeronautics and Astronautics, Beijing, China, in 2021. She is currently working toward the M.S. degree with the Institute of Automation, China Academy of Sciences, Beijing, China. Her current research interests include multi-label emotion recognition and noisy label learning.

![](_page_17_Picture_17.jpeg)

**Yu He** received the B.S. degree from Hunan University, China, in 2013. He is currently working toward the M.S. degree with the University of Chinese Academy of Sciences, Beijing, China. His current research interests include multimodal affective computing and physiological signal prediction.

![](_page_17_Picture_19.jpeg)

**Jianhua Tao** received the Ph.D. degree from Tsinghua University, Beijing, China, in 2001, and the M.S. degree from Nanjing University, Nanjing, China, in 1996. He is currently a Professor with Department of Automation, Tsinghua University, Beijing, China. He has authored or coauthored more than eighty papers on major journals and proceedings. His current research interests include speech recognition, speech synthesis and coding methods, human–computer interaction, multimedia information processing,

and pattern recognition. He is the Chair or Program Committee Member for several major conferences, including ICPR, ACII, ICMI, ISCSLP, etc. He is also the Steering Committee Member for the IEEE Transactions on Affective Computing, an Associate Editor for Journal on Multimodal User Interface and International Journal on Synthetic Emotions, and the Deputy Editor-in-Chief for Chinese Journal of Phonetics.