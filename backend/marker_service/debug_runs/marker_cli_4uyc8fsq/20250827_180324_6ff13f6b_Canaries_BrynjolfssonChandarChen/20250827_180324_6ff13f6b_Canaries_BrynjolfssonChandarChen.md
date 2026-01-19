# Canaries in the Coal Mine? Six Facts about the Recent Employment Effects of Artificial Intelligence

Erik Brynjolfsson<sup>∗</sup> Bharat Chandar† Ruyu Chenद

August 26, 2025

#### **Abstract**

This paper examines changes in the labor market for occupations exposed to generative artificial intelligence using high-frequency administrative data from the largest payroll software provider in the United States. We present six facts that characterize these shifts. We find that since the widespread adoption of generative AI, early-career workers (ages 22-25) in the most AI-exposed occupations have experienced a 13 percent relative decline in employment even after controlling for firm-level shocks. In contrast, employment for workers in less exposed fields and more experienced workers in the same occupations has remained stable or continued to grow. We also find that adjustments occur primarily through employment rather than compensation. Furthermore, employment declines are concentrated in occupations where AI is more likely to *automate*, rather than *augment*, human labor. Our results are robust to alternative explanations, such as excluding technology-related firms and excluding occupations amenable to remote work. These six facts provide early, large-scale evidence consistent with the hypothesis that the AI revolution is beginning to have a significant and disproportionate impact on entry-level workers

in the American labor market.

<sup>∗</sup>Stanford University and NBER; [erikb@stanford.edu](mailto:erikb@stanford.edu)

<sup>†</sup>Stanford University; [chandarb@stanford.edu](mailto:chandarb@stanford.edu)

<sup>‡</sup>Stanford University; [ruyuchen@stanford.edu](mailto:ruyuchen@stanford.edu)

<sup>§</sup>Thanks to Nick Bloom, Joshua Gans, David Autor, Daniel Rock, Fei-Fei Li, Frank Li, Christina Langer, Sarah Bana, Cody Cook, Chris Forman, Andrew Wang, Brad Ross, Omeed Maghzian, Basil Halperin, Jiaxin Pei, Phil Trammell, Eric Bergman and participants at the Stanford Digital Economy Lab workshop for helpful feedback. We are grateful to ADP for access to the data and the Stanford Digital Economy Lab for financial support. All errors are our own.

<sup>¶</sup>**Latest version: <https://digitaleconomy.stanford.edu/publications/canaries-in-the-coal-mine/>**

## <span id="page-1-3"></span>**1 Introduction**

The proliferation of generative artificial intelligence (AI) has sparked a global debate about its potential impact on the labor market. This discourse, across academia, public policy, business, and popular media, spans utopian predictions of enhanced productivity, dystopian fears of widespread job displacement, and skeptical views that AI will have minimal effects on employment or productivity. Historically, technologies have affected different tasks, occupations, and industries in different ways, replacing work in some, augmenting others, and transforming still others. These heterogeneous effects suggest that there may be "canaries in the coal mine" which are harbingers of more widespread effects of AI.

There have been rapid improvements in AI capabilities in several areas. For instance, according to the most recent AI Index Report, AI systems could solve just 4.4% of coding problems on SWE-Bench, a widely used benchmark for software engineering, in 2023, but performance increased to 71.7% in 2024 [\(Maslej et al.,](#page-31-0) [2025\)](#page-31-0).[1](#page-1-0) AI has improved on other benchmarks as well including language understanding, subject knowledge, and reasoning. At the same time, AI systems are increasingly widely adopted. According to [Hartley et al.](#page-30-0) [\(2025\)](#page-30-0), LLM adoption at work among U.S. survey respondents above age 18 reached 46% by June/July 2025.[2](#page-1-1)

Given the better capabilities and widespread adoption, a central concern, amplified in recent headlines, is whether AI is beginning to supplant human labor, particularly for younger, entry-level workers in highly exposed professions like software engineering and customer service.[3](#page-1-2)

Despite the intensity of this debate, empirical evidence has struggled to keep pace with technological advancement, leaving many fundamental questions unanswered. This paper confronts this empirical gap by leveraging a large-scale, high-frequency administrative dataset from ADP, the largest payroll software provider in the United States. Our sample consists of monthly, individuallevel payroll records through July 2025, encompassing millions of workers across tens of thousands of firms. This rich panel structure allows us to track employment dynamics with a high degree of

<span id="page-1-0"></span><sup>1</sup>SWE-bench is designed to evaluate the performance of large language models (LLMs) on real-world software engineering tasks. It uses a collection of GitHub issues to assess an LLM's ability to generate code that resolves those issues.

<span id="page-1-1"></span><sup>2</sup>Similarly, [Bick et al.](#page-27-0) [\(2024\)](#page-27-0) found that in late 2024, nearly 40% of the U.S. population age 18-64 reported using generative AI, with 23% of employed respondents saying they had used generative AI for work at least once in the previous week, and 9% every work day.

<span id="page-1-2"></span><sup>3</sup> Improved productivity of workers in an occupation could lead to either reduced or increased employment, depending on, among other things, how elastic demand is for the output of those workers.

granularity, providing a near real-time view of labor market adjustments. By linking this data to established measures of occupational AI exposure and other variables, we can quantify the realized employment changes since the widespread adoption of generative AI.

This paper systematically presents six key facts that emerge from the data, offering an assessment of how the AI revolution is reshaping the American workforce.

Our first key finding is that we uncover substantial declines in employment for early-career workers (ages 22-25) in occupations most exposed to AI, such as software developers and customer service representatives. In contrast, employment trends for more experienced workers in the same occupations, and workers of all ages in less-exposed occupations such as nursing aides, have remained stable or continued to grow.

Our second key fact is that overall employment continues to grow robustly, but employment growth for young workers in particular has been stagnant since late 2022. In jobs less exposed to AI young workers have experienced comparable employment growth to older workers. In contrast, workers aged 22 to 25 have experienced a 6% decline in employment from late 2022 to July 2025 in the most AI-exposed occupations, compared to a 6-9% increase for older workers. These results suggest that declining employment AI-exposed jobs is driving tepid overall employment growth for 22- to 25- year-olds as employment for older workers continues to grow.

Our third key fact is that not all uses of AI are associated with declines in employment. In particular, entry-level employment has declined in applications of AI that *automate* work, but not those that most *augment* it. We distinguish between automation and augmentation empirically using estimates of the extent to which observed queries to Claude, the LLM, substitute or complement for the tasks in that occupation. While we find employment declines for young workers in occupations where AI primarily automates work, we find employment growth in occupations in which AI use is most augmentative. These findings are consistent with automative uses of AI substituting for labor while augmentative uses do not.

Fourth, we find that employment declines for young, AI-exposed workers remain after conditioning on firm-time effects. One class of explanations for our patterns is that they may be driven by industry- or firm-level shocks such as interest rate changes that correlate with sorting patterns by age and measured AI exposure. We test for a class of such confounders by controlling for firm-time effects in an event study regression, absorbing aggregate firm shocks that impact all workers at a firm regardless of AI exposure. For workers aged 22-25, we find a 12 log-point decline in relative employment for the most AI-exposed quintiles compared to the least exposed quintile, a large and statistically significant effect. Estimates for other age groups are much smaller in magnitude and not statistically significant. These findings imply that the employment trends we observe are not driven by differential shocks to firms that employ a disproportionate share of AI-exposed young workers.

Fifth, the labor market adjustments are visible in employment more than compensation. In contrast to our findings for employment, we find little difference in annual salary trends by age or exposure quintile, suggesting possible wage stickiness. If so, AI may have larger effects on employment than on wages, at least initially.

Sixth, the above facts are largely consistent across various alternative sample constructions. We find that our results are not driven solely by computer occupations or by occupations susceptible to remote work and outsourcing. We also find that the AI exposure taxonomy did not meaningfully predict employment outcomes for young workers further back in time, before the widespread use of LLMs, including during the unemployment spike driven by the COVID-19 pandemic. The patterns we observe in the data appear most acutely starting in late 2022, around the time of rapid proliferation of generative AI tools.[4](#page-3-0) They also hold for both occupations with a high share of college graduates and ones with a low college share, suggesting deteriorating education outcomes during COVID-19 do not drive our results. For non-college workers, we find evidence that experience may serve as less of a buffer to labor market disruption, as low college share occupations exhibit divergent employment outcomes by AI exposure up to age 40.

While we caution that the facts we document may in part be influenced by factors other than generative AI, our results are consistent with the hypothesis that generative AI has begun to affect entry-level employment. We intend to continue to track the data on an ongoing basis to assess whether these trends change in the future.

Why might AI adversely affect exposed entry-level workers more than other age groups? One possibility is that, by nature of the model training process, AI replaces codified knowledge, the "book-learning" that forms the core of formal education. AI may be less capable of replacing

<span id="page-3-0"></span><sup>4</sup>OpenAI introduced ChatGPT in November 2022.

tacit knowledge, the idiosyncratic tips and tricks that accumulate with experience. [5](#page-4-0) As young workers supply relatively more codified knowledge than tacit knowledge, they may face greater task replacement from AI in exposed occupations, leading to greater employment reallocation [\(Acemoglu and Autor,](#page-26-0) [2011\)](#page-26-0). In contrast older workers with accumulated tacit knowledge may face less task replacement. These benefits of tacit knowledge may accrue less to non-college workers in occupations with low returns to experience. Furthermore, more experienced workers may be more skilled in other ways, making them less vulnerable to substitution by AI tools [\(Ide,](#page-31-1) [2025\)](#page-31-1). An important direction for research is to further model and test these predictions.

## <span id="page-4-3"></span>**2 Related Literature**

This paper engages with a large public debate in academia, public policy, business, and media on the employment effects of artificial intelligence. Much of this discourse centers on whether AI is displacing workers in exposed professions such as software engineers.[6](#page-4-1) Some work has noted that the unemployment rate for college graduates has risen above the rate for non-graduates, suggesting this as evidence of employment disruptions from AI [\(Thompson,](#page-32-0) [2025\)](#page-32-0). Others have noted that these trends long preceded the spread of AI and have noted that publicly available data such as the Current Population Survey (CPS) show mixed evidence on employment changes in AI-exposed occupations [\(Lim et al.,](#page-31-2) [2025;](#page-31-2) [The Economist,](#page-32-1) [2025;](#page-32-1) [Smith,](#page-32-2) [2025;](#page-32-2) [Eckhardt and](#page-29-0) [Goldschlag,](#page-29-0) [2025;](#page-29-0) [Frick,](#page-30-1) [2025\)](#page-30-1).[7](#page-4-2) These debates remain unsettled and in search of high quality data on labor market changes among exposed groups. Our paper provides large-scale data to measure employment changes with a high degree of granularity and precision, finding that young workers in AI-exposed occupations have indeed experienced employment declines.

<span id="page-4-0"></span><sup>5</sup> Ironically, one of the practical skills more likely to be learned on the job than in university computer science classes may be how to use AI software development.

<span id="page-4-1"></span><sup>6</sup>Some recent media on this topic includes [Horowitch](#page-30-2) [\(2025\)](#page-30-2); [Ettenheim](#page-29-1) [\(2025\)](#page-29-1); [Raman](#page-32-3) [\(2025\)](#page-32-3); [Roose](#page-32-4) [\(2025\)](#page-32-4); [Peck](#page-32-5) [\(2025\)](#page-32-5); [Hoover](#page-30-3) [\(2025\)](#page-30-3); [Milmo and Almeida](#page-31-3) [\(2025\)](#page-31-3); [Wu](#page-33-0) [\(2025\)](#page-33-0); [Raval](#page-32-6) [\(2025\)](#page-32-6). A number of technology executives have also warned of potential job loss from AI [\(Allen,](#page-27-1) [2025;](#page-27-1) [Sherman,](#page-32-7) [2025;](#page-32-7) [Bacon,](#page-27-2) [2025\)](#page-27-2) or laid off workers with the aim of incresing AI investments [\(Jamali,](#page-31-4) [2025\)](#page-31-4).

<span id="page-4-2"></span><sup>7</sup>Reports from industry have also shown mixed findings. Job posting platform TrueUp suggests a recent increase in postings in the tech sector [\(Lenny Rachitsky,](#page-31-5) [2025\)](#page-31-5). On the other hand, Revelio Labs finds a decline in job postings, with the decrease steeper for entry-level workers [\(Simon,](#page-32-8) [2025\)](#page-32-8). Indeed job posting data suggest declines in postings for new graduates but find these declines for less AI-exposed occupations as well [\(Lim et al.,](#page-31-2) [2025\)](#page-31-2). [Chandar](#page-28-0) [\(2025b\)](#page-28-0) notes that the correlation between job postings and employment has been weak over recent years. SignalFire finds steep declines in new graduate hires in the tech sector compared to pre-Pandemic levels [\(Doshay and Bantock,](#page-29-2) [2025\)](#page-29-2), consistent with the findings in this paper. Data from Gusto also suggests a decline in new graduate hiring [\(Bowen,](#page-27-3) [2025\)](#page-27-3).

In academia, there is a growing body of research seeking to measure the employment effects of AI. The advent of this literature included a series of influential papers that established methodologies for estimating which occupations and tasks were susceptible to automation [\(Frey and Osborne,](#page-30-4) [2017;](#page-30-4) [Brynjolfsson and Mitchell,](#page-27-4) [2017;](#page-27-4) [Brynjolfsson et al.,](#page-27-5) [2018;](#page-27-5) [Felten et al.,](#page-29-3) [2018,](#page-29-3) [2019;](#page-29-4) [Webb,](#page-33-1) [2019;](#page-33-1) [Felten et al.,](#page-29-5) [2021\)](#page-29-5). More recently, work such as [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6); [Felten et al.](#page-29-7) [\(2023\)](#page-29-7); [Gmyrek et al.](#page-30-5) [\(2023\)](#page-30-5); [Handa et al.](#page-30-6) [\(2025\)](#page-30-6), and [Tomlinson et al.](#page-32-9) [\(2025\)](#page-32-9) adapted this approach for Generative AI, forming the basis for exposure metrics used in this analysis. While these studies identify potential disruption, ours connect these exposure measures to actual employment changes. We find that these measures of exposure do indeed predict substantial employment changes for young workers in the period after the spread of generative AI.

Our work complements and broadens insights from studies that find significant effects in more specific settings, such as on online freelance platforms [\(Hui et al.,](#page-30-7) [2023;](#page-30-7) [Demirci et al.,](#page-28-1) [2025\)](#page-28-1) or within individual firms [\(Brynjolfsson et al.,](#page-27-6) [2025;](#page-27-6) [Dillon et al.,](#page-29-8) [2025\)](#page-29-8).[8](#page-5-0) We measure labor market changes across occupations spanning the US economy.

In this sense our work complements a small but growing list of papers that use economywide data to measure AI's impact. Recent findings have been varied. [Humlum and Vestergaard](#page-31-6) [\(2025\)](#page-31-6) use Danish administrative data to conclude there were minimal effects on earnings or hours worked, while [Jiang et al.](#page-31-7) [\(2025\)](#page-31-7) find AI exposure is correlated with longer work hours in the U.S.[9](#page-5-1) [Hampole et al.](#page-30-8) [\(2025\)](#page-30-8) use job postings and LinkedIn profile records from Revelio labs from 2011 to 2023 to find limited employment impacts overall, with growing overall labor demand at firms offsetting relative declines in demand for exposed occupations. [Chandar](#page-28-0) [\(2025b\)](#page-28-0) uses data from the CPS to compare employment changes in more and less AI-exposed professions, finding little differential trend overall but noting the difficulty of measuring changes for young workers because of the limited effective sample size. [Dominski and Lee](#page-29-9) [\(2025\)](#page-29-9) similarly use CPS data with alternative exposure measures and find declines in employment in AI-exposed occupations, though data limitations in the CPS limit the capacity for statistical inference. [Johnston and Makridis](#page-31-8) [\(2025\)](#page-31-8) find employment increases in state-industry pairs more exposed to AI using data from the

<span id="page-5-1"></span><span id="page-5-0"></span><sup>8</sup>See also [Noy and Zhang](#page-32-10) [\(2023\)](#page-32-10); [Peng et al.](#page-32-11) [\(2023\)](#page-32-11); [Dell'Acqua et al.](#page-28-2) [\(2023\)](#page-28-2).

<sup>9</sup>See also [Acemoglu et al.](#page-26-1) [\(2022\)](#page-26-1); [Bonney et al.](#page-27-7) [\(2024\)](#page-27-7); [Bick et al.](#page-27-0) [\(2024\)](#page-27-0); [Hartley et al.](#page-30-0) [\(2025\)](#page-30-0); [Frank et al.](#page-30-9) [\(2025\)](#page-30-9); [Chen et al.](#page-28-3) [\(2025\)](#page-28-3).

Quarterly Census of Employment and Wages (QCEW).[10](#page-6-0) These prior papers use data that lack either sufficient granularity or immediacy to reliably study employment changes by AI exposure and age [\(O'Brien,](#page-32-12) [2025\)](#page-32-12).[11](#page-6-1) In contrast, this paper uses large-scale, close to real-time data to take a step towards resolving the ongoing debate on the employment effects of AI on young workers.

## **3 Data Description**

#### <span id="page-6-3"></span>**3.1 Payroll Data**

This study uses data from ADP, the largest payroll processing firm in America. The company provides payroll services for firms employing over 25 million workers in the US. We use this information to track employment changes for workers in occupations measured as more or less exposed to artificial intelligence.

We make several sample restrictions for our main analysis sample. We include only workers employed by firms that use ADP's payroll product to maintain worker earnings records. We also exclude employees classified by firms as part-time from the analysis and subset to people between the age of 18 and 70.[12](#page-6-2)

The set of firms using payroll services changes over time as companies join or leave ADP's platform. We maintain a consistent set of firms across our main sample period by keeping only companies that have employee earnings records for each month from January 2021 through July 2025.

In addition, ADP observes job titles for about 70% of workers in its system. We exclude workers who do not have a recorded job title. There are over 7,000 standardized job titles, examples of which include "Search engineer optimization specialist," "Enterprise content management manager," and "Plant documentation control specialist." The company's internal research team maps each of

<span id="page-6-0"></span><sup>10</sup>[Johnston and Makridis](#page-31-8) [\(2025\)](#page-31-8) measure state-industry exposure by taking an average of [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6)'s occupational exposure weighted by state-industry employment. Industry-level labor market changes may be distinct from the occupation-level changes studied in this paper if firms make capital investments or become more productive in ways that increases overall labor demand [\(Hampole et al.,](#page-30-8) [2025\)](#page-30-8).

<span id="page-6-1"></span><sup>11</sup>As a comparison, the CPS surveyed between 44,000 and 51,000 employed individuals in total across all age groups in each month since 2021. Between 10,000 and 12,000 of these observations were in the outgoing rotation group and included earnings records. The data in our main analysis sample includes between 250,000 and 350,000 employed individuals in each month *just between the ages of 22 and 25*, all with earnings records.

<span id="page-6-2"></span><sup>12</sup>While we observe the year of birth for each worker, for privacy reasons we do not observe the exact date of birth. We impute month of birth from the distribution of birth months in the United States using data from the Center for Disease Control and Prevention.

these job titles to a 2010 Standard Occupational Classification (SOC) code, additionally using information such as the job description, industry, location, and other relevant data. We use these estimated SOC codes to merge our data to occupational AI exposure measures described below in Section [3.2.](#page-7-0)

After these restrictions we have records on between 3.5 and 5 million workers each month for our main analysis sample, though we consider robustness to alternative analyses such as allowing for firms to enter and leave the sample.

While the ADP data include millions of workers in each month, the distribution of firms using ADP services does not exactly match the distribution of firms across the broader US economy. Further details on differences in firm composition can be found in [Cajner et al.](#page-28-4) [\(2018\)](#page-28-4) and [ADP](#page-26-2) [Research](#page-26-2) [\(2025\)](#page-26-2).[13](#page-7-1)

#### <span id="page-7-0"></span>**3.2 Occupational AI Exposure**

We use two different approaches for measuring occupational exposure to AI. The first uses exposure measures from [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6). [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6) estimate AI exposure by O\*NET task using ChatGPT validated with human labeling. They then construct occupational exposure measures by aggregating the task data to the 2018 SOC code level. We focus on the GPT-4 based *β* exposure measures from their paper.

The second primary approach we take uses data on generative AI usage from the Anthropic Economic Index [\(Handa et al.,](#page-30-6) [2025\)](#page-30-6). This index reports the estimated share of queries pertaining to each O\*NET task based on a sample of several million conversations with Claude, Anthropic's generative AI model. It then aggregates the data to the occupational level based on these task shares. One feature of the Anthropic Economic Index is that for each task it also reports estimates of the share of queries pertaining to that task that are "automative," "augmentative," or none of the above. We use this information as an estimate of whether usage of AI for an occupation is primarily complementary or substitutable with labor.[14](#page-7-2)

<span id="page-7-1"></span><sup>13</sup>[Cajner et al.](#page-28-4) [\(2018\)](#page-28-4) find a somewhat higher share of manufacturing and services firms compared to the Quarterly Census of Employment and Wages (QCEW) using data from March 2016. They also find that ADP somewhat overrepresents firms in the Northeast. In addition, firms using ADP tend to grow faster on average than the typical firm in the US economy.

<span id="page-7-2"></span><sup>14</sup>Specifically, [Handa et al.](#page-30-6) [\(2025\)](#page-30-6) first use Claude to classify conversations into six categories: Directive, meaning complete task delegation with minimal interaction; Feedback Loop, meaning task completion guided by environmental feedback such as when repeatedly relaying coding errors to the model; Task Iteration, meaning a collaborative

Both the [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6) measures and the [Handa et al.](#page-30-6) [\(2025\)](#page-30-6) measures estimate AI exposure by 2018 SOC code. We use a 2010 SOC code to 2018 SOC code crosswalk from the BLS to merge the exposure measures to the payroll data. Table [A1](#page-55-0) shows example occupations for each AI exposure measure.

#### <span id="page-8-1"></span>**3.3 Other Data**

To compare employment changes for teleworkable versus non-teleworkable occupations, we use data from [Dingel and Neiman](#page-29-10) [\(2020\)](#page-29-10). We use the Personal Consumption Expenditure index from the BLS to compute real earnings, indexed to October 2017. We use monthly Current Population Survey (CPS) data as a comparison for our main findings.

## **4 Results**

# <span id="page-8-0"></span>**4.1 Fact 1: Employment for young workers has declined in AI-exposed occupations**

Consider software engineers and customer service agents, two occupations that are frequently considered to be highly exposed to generative AI tools. Media attention has raised the specter of widespread employment disruption for young software engineers in particular [\(Thompson,](#page-32-0) [2025;](#page-32-0) [Raman,](#page-32-3) [2025;](#page-32-3) [Allen,](#page-27-1) [2025;](#page-27-1) [Horowitch,](#page-30-2) [2025\)](#page-30-2).

Figure [1](#page-9-0) shows employment changes by age group for these occupations, normalized to 1 in October 2022. Both occupations present a similar pattern: employment for the youngest workers declines considerably after 2022, while employment for other age groups continues to grow. By July, 2025, employment for software developers aged 22-25 declined by nearly 20% compared to its peak in late 2022. Figure [A1](#page-34-0) shows that a similar pattern holds for computer occupations and service clerks more generally.

Figure [2](#page-10-0) shows four other professions as case studies, spanning varying levels of AI exposure according to the measures developed in [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6). Marketing and sales managers, in

refinement process; Learning, meaning knowledge acquisition and understanding; Validation, meaning work verification and improvement; or "None," with the model instructed to choose the None option "liberally." Conversations classified as Directive or Feedback Loop are considered as Automative, while ones classified as Task Iteration, Learning, or Validation are considered Augmentative. See [Handa et al.](#page-30-6) [\(2025\)](#page-30-6) for more details. Table [A2](#page-56-0) reproduces Table 1 from [Handa et al.](#page-30-6) [\(2025\)](#page-30-6) and shows more details about the automation and augmentation measures.

<span id="page-9-0"></span>![](_page_9_Figure_0.jpeg)

Figure 1: Employment changes for software developers and customer service agents by age, normalized to  $1$  in October 2022.

the fourth quintile of AI exposure, show a decline in employment for young workers much like the case of software and customer service, albeit with smaller magnitudes. Front-line production and operations supervisors, in quintile 3, show an increase in employment for young workers, though the growth in employment is smaller than the increase for workers over the age of 35.

In contrast, the trends for occupations that Eloundou et al.  $(2024)$  rated as less exposed do not fit the pattern of the more exposed occupations. Stock clerks and order fillers, in quintile 2, show no obvious difference by age. Strikingly, the series for health aides, comprising nursing aides, psychiatric aides, and home health aides, show a quite different trend from software or customer service: employment for young workers has been growing *faster* than for older workers.

<span id="page-10-0"></span>![](_page_10_Figure_2.jpeg)

Figure 2: Employment changes for marketing and sales managers (exposure quintile 4), first-line production supervisors (exposure quintile 3), stock clerks and order fillers (exposure quintile 2), and health aides (exposure quintile 1), normalized to 1 in October 2022. Exposure quintiles are defined based on the Eloundou et al. (2024) GPT-4  $\beta$  measure.

Figure 3 shows these patterns hold more generally across professions. The top left plot shows a divergence in employment outcomes for more and less exposed occupations for workers aged 22-25, with more exposed occupations experiencing declining employment. For older age groups, we find much less marked differences in employment growth across AI exposure quintiles.

<span id="page-11-0"></span>![](_page_11_Figure_1.jpeg)

Figure 3:  $GPT-4 \beta$ . Employment changes by age and exposure quintile using measures from Eloundou et al. (2024). Exposure quintiles are defined based on the GPT-4  $\beta$  measures. Darker lines are more exposed quintiles. The red line shows the overall trend pooling across quintiles.

#### <span id="page-12-1"></span> $4.2$ Fact 2: Though overall employment continues to grow, employment growth for young workers in particular has been stagnant

Figure 4 shows overall employment trends across age groups, pooling together all occupations. Overall employment remains robust, coinciding with a low national unemployment rate in the postpandemic period. However, Figure 4 suggests some leveling off in employment growth for young workers relative to other age groups, consistent with recent discussion of a potentially worsening job market for entry-level workers (Chen, 2025; Federal Reserve Bank of New York, 2025).

<span id="page-12-0"></span>![](_page_12_Figure_2.jpeg)

Figure 4: Employment changes by age. Including all occupations.

Figure 5 offers insight into how these trends relate to AI exposure. For each age group, employment growth from late 2022 to July 2025 was  $6-13\%$  for the lowest three AI exposure quintiles, with no clear ordering in employment growth by age. In contrast, for the highest two exposure quintiles employment for 22-25 year olds declined by  $6\%$  between late 2022 and July 2025, while employment for workers aged 35-49 grew by over 9%. These results show that declining employment in AI-exposed jobs is driving tepid overall emplyoment growth for workers between the ages of  $22$  and  $25$ .

<span id="page-13-0"></span>![](_page_13_Figure_0.jpeg)

Figure 5: Growth in employment between October 2022 and July 2025 by age and GPT-4 *β*-based AI exposure group.

While these findings suggest divergent employment outcomes by AI exposure for young workers, we caution the trends observed in these first two facts could be driven by other changes in the US economy. Our subsequent facts evaluate the robustness of the results to alternative analyses.

# <span id="page-13-1"></span>**4.3 Fact 3: Entry-level employment has declined in applications of AI that** *automate* **work, with muted changes for** *augmentation*

AI exposure can either complement or substitute for labor. These may have very different implications for the labor market [\(Brynjolfsson,](#page-27-8) [2022\)](#page-27-8).

To assess how employment patterns differ based on the complementarity or substitutability of AI with labor, we use data on generative AI usage from the Anthropic Economic Index [\(Handa](#page-30-6) [et al.,](#page-30-6) [2025\)](#page-30-6). The Index provides an estimate of the share of queries that pertain to each occupation. In addition, for each task it reports estimates of the share of queries pertaining to that task that are "automative," "augmentative," or none of the above. We use this information as an estimate of whether usage of AI for an occupation is primarily a substitute or complement for labor.[15](#page-14-0) Table [A1](#page-55-0) shows example occupations that are in the highest and lowest exposure category for each measure.

<span id="page-14-3"></span>Figure [6](#page-15-0) shows employment changes by overall prevalence of related Claude queries. The patterns match the findings using the [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6) measures closely. Figure [7](#page-16-0) likewise shows that the occupations with the highest estimated automation shares have experienced declining employment for the youngest workers.

In contrast, Figure [8](#page-17-0) indicates that the occupations with the highest estimated augmentation shares have *not* experienced a similar pattern. Employment changes for young workers are not ordered by augmentation exposure, as the fifth quintile has among the fastest employment growth. The findings are consistent with automative uses of AI substituting for labor while augmentative uses do not.[16](#page-14-1)

# **4.4 Fact 4: Employment declines for young, AI-exposed workers remain after conditioning on firm-time shocks**

While our results so far are consistent with the hypothesis that generative AI is causing a decline in entry-level employment, there are plausible alternative explanations. One class of explanations is that our patterns are explained by industry- or firm-level shocks correlated with sorting patterns by age and measured AI exposure. For example, one possibility is that young workers with high measured AI exposure are disproportionately likely to sort to firms heavily susceptible to interest rate increases.

We test for a class of such confounders by controlling for a rich set of fixed effects. For each age group, we estimate the Poisson regression

<span id="page-14-2"></span>
$$\log(E[y_{f,q,t}]) = \sum_{q' \neq 1} \sum_{j \neq -1} \gamma_{q',j} 1\{t = j\} 1\{q' = q\} + \alpha_{f,q} + \beta_{f,t} + \epsilon_{f,q,t} \tag{4.1}$$

<span id="page-14-0"></span><sup>15</sup>Figures [A2](#page-35-0) and [A3](#page-36-0) show that automation and augmentation results are similar when dropping occupations with low overall Claude usage.

<span id="page-14-1"></span><sup>16</sup>Note that occupations in the first two quintiles of the augmentation measure have very low Claude usage overall, with the average occupation in these quintiles comprising 0.01% and 0.09% of conversations, respectively. These occupations have a high share of conversations that are classified as neither automative nor augmentative. In contrast, occupations in the third through fifth quintiles average 0.47%, 0.39%, and 0.33% of Claude conversations. For the automation measure, overall Claude usage increases on average with the automation share, with the lowest exposure group averaging 0.05% of conversations and the highest group averaging 0.73%.

<span id="page-15-0"></span>![](_page_15_Figure_0.jpeg)

Figure 6: Overall Claude usage. Employment changes by age and exposure quintile using Claude usage data from Handa et al. (2025). Exposure quintiles are defined based on the share of queries to Claude that relate to tasks associated with an occupation. Darker lines are more exposed quintiles. The red line shows the overall trend pooling across quintiles. Occupations whose associated tasks all have fewer than the minimum number of queries to appear in the usage data are treated as a separate category, coded as  $0$ .

<span id="page-16-0"></span>![](_page_16_Figure_0.jpeg)

Figure 7: Automation. Employment changes by age and automation level using Claude usage data from Handa et al.  $(2025)$ . Automation levels are defined based on the share of queries related to an occupation that are classified by Claude as automative in nature. Darker lines are more automative. The red line shows the overall trend pooling across automation levels. Occupations whose associated tasks all have fewer than the minimum number of queries to appear in the usage data are treated as a separate category, coded as 0. Note that greater than  $20\%$  of occupations above the minimum query threshold have an estimated automation share of 0. All occupations in the first and second quintile are consequently grouped together in level 1. The remaining quintiles are coded as  $2$ ,  $3$  and  $4$ .

<span id="page-17-0"></span>![](_page_17_Figure_0.jpeg)

Figure 8: Augmentation. Employment changes by age and augmentation quintile using Claude usage data from Handa et al. (2025). Augmentation quintiles are defined based on the share of queries related to an occupation that are classified by Claude as augmentative. Darker lines are more augmentative quintiles. The red line shows the overall trend pooling across quintiles. Occupations whose associated tasks all have fewer than the minimum number of queries to appear in the usage data are treated as a separate category, coded as  $0$ .

*f* indexes firms, *q* indexes [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6) exposure quintiles, and *t* indexes months, with *t* = −1 corresponding to October 2022. The outcome variable *yf,q,t* is employment in *f, q, t*. Equation [4.1](#page-14-2) is a Poisson event study regression controlling for firm-quintile effects, *αf,q*, and firmtime effects, *βf,t*. The firm-time effects absorb aggregate firm shocks that impact each exposure quintile equally. The firm-quintile effects adjust for baseline differences in hiring across quintiles within the firm. The coefficients of interest, *γq,t*, measure differential changes in employment growth across quintiles after accounting for firm-time effects and firm-quintile effects.[17](#page-18-0)

We run this regression separately for each age group. For each regression, we restrict to firms that hire at least 10 workers within the age group in every period of the sample. Further, P *t yf,q,t* must equal at least 100 for each *q*, meaning that the firm must at least employ on average about 2 workers from each exposure quintile across months in the sample.[18](#page-18-1) Standard errors are clustered by firm.

Results are in Figure [9,](#page-19-0) which plots the *γq,t* coefficients for each age group. For workers aged 22-25, estimates for higher quintiles are large and statistically significant, with a 12 log point decline in relative employment comparable in magnitude to the estimates in the raw data in Figure [3.](#page-11-0) Estimates for other age groups are generally much smaller in magnitude and not statistically significant. These findings imply that the employment trends we observe are not driven by differential shocks to firms that employ a disproportionate share of AI-exposed young workers.

One alternative confounder that would not be controlled for with firm-time effects is that even conditional on the firm workers with high AI exposure were excessively hired after the COVID-19 pandemic, leading to a subsequent contraction in their hiring. To assess such alternatives we consider various other robustness checks in Section [4.6,](#page-20-0) such as removing computer occupations and conditioning on whether the occupation is amenable to work from home.

<span id="page-18-0"></span><sup>17</sup>Because of zero counts in the outcome variable, we estimate a Poisson regression instead of an OLS regression in logs following guidance from [Chen and Roth](#page-28-6) [\(2024\)](#page-28-6).

<span id="page-18-1"></span><sup>18</sup>Results are not sensitive to these restrictions, though there must be at least one non-zero value in each firm-month and each firm-quintile for observations to not get dropped in the Poisson regression.

<span id="page-19-0"></span>![](_page_19_Figure_0.jpeg)

Figure 9: Poisson regression event study estimates for employment changes by age and AI exposure. Estimates are all relative to occupational exposure quintile 1. Exposure quintiles use Eloundou et al. (2024) GPT-4  $\beta$  measures. Estimates control for firm-time and firm-quintile fixed effects following Equation 4.1. Shaded regions are 95% confidence intervals. Standard errors are clustered by firm.

# **4.5 Fact 5: Labor market adjustments are visible in employment more than compensation**

In addition to employment we observe workers' annual base compensation. We use this information to test for labor market adjustment along the compensation margin.[19](#page-20-1) Salary data are deflated to 2017 dollars using the PCE index.[20](#page-20-2)

Results are in Figure [10.](#page-21-0) The findings indicate a less marked divergence in compensation compared to employment across more and less exposed occupations. Figure [11](#page-22-0) shows results by age and [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6)-based exposure quintile. We find little difference in compensation trends by age or exposure quintile.

Prior work by [Autor and Thompson](#page-27-9) [\(2025\)](#page-27-9) notes that technology that replaces inexpert tasks may reduce occupational employment but increase occupational wages; technology that replaces expert tasks may do the opposite. The sign of the wage effect depends on the overall share of tasks displaced as well as the whether these tasks are expert or inexpert. The limited changes we find for wages suggest that these effects may be offsetting, at least in the short run. Alternatively, the results could be explained by wage stickiness in the short run, consistent with recent evidence from [Davis and Krolikowski](#page-28-7) [\(2025\)](#page-28-7).

# <span id="page-20-0"></span>**4.6 Fact 6: Findings are largely consistent under alternative sample constructions**

We test the robustness of these results to alternative sample constructions and robustness checks.

**Excluding Technology Occupations** One possibility is that our results are explained by a general slowdown in technology hiring from 2022 to 2023 as firms recovered from the COVID-19 Pandemic.[21](#page-20-3) Figure [A4](#page-37-0) shows employment changes by age and exposure quintile after excluding computer occupations, corresponding to 2010 SOC codes that start with 15-1. Figure [A5](#page-38-0) shows results when excluding firms in the information sector (NAICS code 51). Results are quite similar,

<span id="page-20-1"></span><sup>19</sup>Total compensation may additionally include bonuses, overtime pay, commissions, equity, tips, and other items. These may have a greater impact on overall compensation in certain professions and age groups than others.

<span id="page-20-2"></span><sup>20</sup>In contrast to the series for employment, results for compensation end in June 2025, the most recently available month for the PCE index.

<span id="page-20-3"></span><sup>21</sup>Under the Tax Cuts and Jobs Act, amendments to Internal Revenue Code §174 enacted in 2022 also disallowed companies from immediately deducting R&D expenditures, including software development costs. These costs instead had to be capitalized and amortized over five years for domestic research and fifteen years for foreign research.

<span id="page-21-0"></span>![](_page_21_Figure_0.jpeg)

Figure 10: Changes in annual base compensation by age and occupation. Annual base compensation is deflated to  $2017$  dollars using the PCE deflator.

<span id="page-22-0"></span>![](_page_22_Figure_0.jpeg)

Figure 11: Annual base compensation. Changes in annual base compensation by age and exposure quintile. Exposure quintiles are defined based on the GPT-4  $\beta$  measures from Eloundou et al.  $(2024)$ . Darker lines are more exposed quintiles. The red line shows the overall trend pooling across quintiles. Annual base compensation is deflated to  $2017$  dollars using the PCE deflator.

consistent with the case studies above that show employment changes are visible across a range of occupations. Results with firm-time fixed effects in Figure [9](#page-19-0) further show that our findings are robust to firm- or industry-level shocks that impact general hiring trends. These results indicate that our findings are not specific to technology roles.

<span id="page-23-3"></span>**Remote Work** Figures [A6](#page-39-0) and [A7](#page-40-0) show results for occupations amenable to remote work (telework) and those that are not, according to [Dingel and Neiman](#page-29-10) [\(2020\)](#page-29-10).[22](#page-23-0) We find that, for young workers, more exposed occupations have slower employment growth, both in teleworkable occupations and in non-teleworkable occupations. The results for non-teleworkable occupations in particular suggest that our findings are not driven by outsourcing or work-from-home disruptions, at least solely.[23](#page-23-1)

<span id="page-23-4"></span>**Longer Sample** Figure [A8](#page-41-0) shows results when extending the balanced sample of firms to 2018. This reduces the sample size and makes the data somewhat noisier. Nonetheless, the trends remain largely ordered by exposure in the post-GPT era, whereas this is not the case before 2022. A concern is that for the [Eloundou et al.](#page-29-6) [\(2024\)](#page-29-6) measures the most exposed quintile had slower employment growth starting around 2020. This is not the case for the Anthropic exposure measures, shown in Figures [A9,](#page-42-0) [A10,](#page-43-0) and [A11.](#page-44-0) For these measures the most exposed groups have comparable employment growth throughout the period before generative AI, with divergent trends afterwards.

<span id="page-23-5"></span>**Changes in Education** Another possibility is that the changes we observe are influenced by worsening education outcomes during the COVID-19 Pandemic. COVID-19 led to persistent harms in education outcomes [\(Kuhfeld and Lewis,](#page-31-9) [2025\)](#page-31-9). As more educated workers on average have greater measured AI exposure, deterioration in the quality of education in recent years could influence the trends we observe.[24](#page-23-2) In Figure [A12](#page-45-0) we show trends for occupations in which greater than

<span id="page-23-0"></span><sup>22</sup>Whether an occupation is amenable to remote work is positively correlated with AI exposure. Only two teleworkable occupations fall in the lowest quintile of estimated AI exposure according to the GPT-4 *β* measure. Likewise few non-teleworkable occupations fall in the highest quintile of AI exposure. For this reason in Figure [A6](#page-39-0) we pool together the two lowest AI exposure quintiles into one group. In Figure [A7](#page-40-0) we pool together the two highest AI exposure quintiles.

<span id="page-23-2"></span><span id="page-23-1"></span><sup>23</sup>Non-teleworkable occupations with high AI exposure include bank tellers, travel agents, and tax preparers.

<sup>24</sup>[Chandar](#page-28-8) [\(2025a\)](#page-28-8) finds that declines in average skill levels for college graduates explain a sizable share of the slowdown in the growth of the college wage gap in recent decades.

70% of workers have a college degree according to the 2017 American Community Survey (ACS).[25](#page-24-0) In Figure [A13](#page-46-0) we show trends for occupations in which fewer than 30% of workers have a college degree.

Occupations with a high share of college graduates have declining employment overall, with muted differences between more-exposed and less-exposed occupations compared to our main results. In contrast, occupations with a low share of college graduates have rising overall employment, with the least AI-exposed occupations growing and the most exposed occupations declining in employment. Further, for lower college share occupations, the dispersion in employment outcomes is visible in higher age groups as well, with workers up to age 40 showing separation in employment trends by AI exposure. These findings suggest that deteriorating education outcomes cannot fully explain our main results. They also suggest that for non-college workers, experience may serve as less of a buffer to labor market disruption than for college workers.

**Other Robustness Checks** Figures [A14](#page-47-0) and [A15](#page-48-0) show results separately for men and women. The results are similar, suggesting that diverging prospects for men and women are not driving our findings. Figure [A16](#page-49-0) shows that results are similar when we do not take a balanced sample of firms. Figure [A17](#page-50-0) shows similar results when including part-time and temporary workers.[26](#page-24-1)

<span id="page-24-2"></span>**Comparison to CPS Data** A useful benchmark for our findings is to compare them to estimates from the monthly Current Population Survey (CPS). The CPS surveys about 60,000 households nationwide each month to collect data on employment and other labor force characteristics. These data are released a few weeks after the reference month, giving close to real-time estimates of employment statistics. A number of prior analyses have used the CPS to assess how AI is impacting entry-level work [\(Chandar,](#page-28-0) [2025b;](#page-28-0) [Dominski and Lee,](#page-29-9) [2025;](#page-29-9) [Lim et al.,](#page-31-2) [2025;](#page-31-2) [Eckhardt and](#page-29-0) [Goldschlag,](#page-29-0) [2025\)](#page-29-0). We compare some of our main findings in the ADP data to estimates from the CPS.

<span id="page-24-0"></span>Figures [A18](#page-51-0) through [A20](#page-53-0) show employment changes by age for software developers, customer

<sup>25</sup>Not a single occupation in the first quintile of GPT-4 *β* based exposure measure has a college share above 35%, so that quintile is excluded from the results in Figure [A12.](#page-45-0)

<span id="page-24-1"></span><sup>26</sup>Another possibility is that employment trends are driven by Covid-19 Pandemic-era stimulus checks that distorted labor supply. However, these stimulus payments were conditioned on income requirements, and more AI-exposed occupations on average have higher incomes [\(Kochhar,](#page-31-10) [2023\)](#page-31-10), suggesting the observed declines in AI-exposed occupations are unlikely to be driven by this channel.

service representatives, and home health aides by age using data from the CPS. Though there are millions of workers employed in these professions across the US, the estimates are highly volatile, with common fluctuations of 20% or greater in estimated employment month-to-month. Figure [A21](#page-54-0) shows estimated employment changes by age and exposure quintile using the CPS, also suggesting a high degree of volatility in the estimates.

This volatility in CPS microdata reflects small sample sizes and the fact that the CPS is not stratified to target employment statistics for these demographic-occupation subgroups.[27](#page-25-0) The sample size and sampling procedure of the CPS may therefore make it challenging to assess employment changes by age and AI exposure with a high degree of confidence over the time horizon considered in this paper [\(Chandar,](#page-28-0) [2025b;](#page-28-0) [O'Brien,](#page-32-12) [2025\)](#page-32-12).

Other large-scale data sources such as the American Community Survey (ACS) may offer a more reliable comparison to the ADP data, though the ACS is released with a significant lag compared to the data from ADP. We encourage comparison of our findings to results from other data sources such as the ACS upon their release.[28](#page-25-1)

## <span id="page-25-2"></span>**5 Conclusion**

We document six facts about the recent labor market effects of artificial intelligence.

- First, we find substantial declines in employment for early-career workers in occupations most exposed to AI, such as software development and customer support.
- Second, we show that economy-wide employment continues to grow, but employment growth for young workers has been stagnant.
- Third, entry-level employment has declined in applications of AI that *automate* work, with muted effects for those that *augment* it.
- Fourth, these employment declines remain after conditioning on firm-time effects, with a 13% relative employment decline for young workers in the most exposed occupations.

<span id="page-25-0"></span><sup>27</sup>The CPS includes between 26 and 53 young software developers aged between 22 and 25 per month over our sample period. It includes between 49 and 95 young customer service representatives, and between 2 and 14 young home health aides.

<span id="page-25-1"></span><sup>28</sup>The 2024 ACS 1-Year Public Use Microdata Sample is scheduled to be released on October 16, 2025.

- Fifth, these labor market adjustments are more visible in employment than in compensation.
- Sixth, we find that these patterns hold in occupations unaffected by remote work and across various alternative sample constructions.

While our main estimates may be influenced by factors other than generative AI, our results are consistent with the hypothesis that generative AI has begun to significantly affect entry-level employment.

The adoption of new technologies typically leads to heterogeneous effects across workers, resulting in an adjustment period as workers reallocate from displaced forms of work to new forms with growing labor demand [\(Autor et al.,](#page-27-10) [2024\)](#page-27-10). Such endogenous adjustment may already be happening with AI, with emerging evidence of shifts in college majors away from AI-exposed categories such as computer science [\(Horowitch,](#page-30-2) [2025\)](#page-30-2). Past transitions such as the IT revolution ultimately led to robust growth in employment and real wages following physical and human capital adjustments, with some workers benefiting more than others [\(Bresnahan et al.,](#page-27-11) [2002;](#page-27-11) [Brynjolfsson et al.,](#page-28-9) [2021\)](#page-28-9).

Tracking employment trends on an ongoing basis will help determine if the adjustment to AI follows a similar pattern. Consequently, we will continue to monitor these outcomes to assess whether the trends documented in the paper accelerate in the future. Future work would benefit from better firm-level AI adoption data, which would provide sharper variation for estimating plausible causal effects of AI on employment.

## **References**

- <span id="page-26-0"></span>Acemoglu, D. and D. Autor (2011): "Skills, Tasks and Technologies: Implications for Employment and Earnings\*," in *Handbook of Labor Economics*, ed. by D. Card and O. Ashenfelter, Elsevier, vol. 4, 1043–1171. [1](#page-1-3)
- <span id="page-26-1"></span>Acemoglu, D., D. Autor, J. Hazell, and P. Restrepo (2022): "Artificial Intelligence and Jobs: Evidence from Online Vacancies," *Journal of Labor Economics*, 40, S293–S340, publisher: The University of Chicago Press. [9](#page-5-1)
- <span id="page-26-2"></span>ADP Research (2025): "ADP National Employment Report," . [3.1](#page-6-3)

- <span id="page-27-1"></span>Allen, Mike, J. V. (2025): "Behind the Curtain: Top AI CEO foresees white-collar bloodbath," *Axios*. [6,](#page-4-1) [4.1](#page-8-0)
- <span id="page-27-10"></span>Autor, D., C. Chin, A. Salomons, and B. Seegmiller (2024): "New Frontiers: The Origins and Content of New Work, 1940–2018\*," *The Quarterly Journal of Economics*, 139, 1399–1465. [5](#page-25-2)
- <span id="page-27-9"></span>Autor, D. and N. Thompson (2025): "Expertise," Working Paper, NBER. [4.5](#page-19-0)
- <span id="page-27-2"></span>Bacon, A. (2025): "Nvidia's Jensen Huang says AI could lead to job losses 'if the world runs out of ideas' | CNN Business," *CNN*. [6](#page-4-1)
- <span id="page-27-0"></span>Bick, A., A. Blandin, and D. J. Deming (2024): "The Rapid Adoption of Generative AI," Working Paper, National Bureau of Economic Research. [2,](#page-1-1) [9](#page-5-1)
- <span id="page-27-7"></span>Bonney, K., C. Breaux, C. Buffington, E. Dinlersoz, L. Foster, N. Goldschlag, J. Haltiwanger, Z. Kroff, and K. Savage (2024): "The impact of AI on the workforce: Tasks versus jobs?" *Economics Letters*, 244, 111971. [9](#page-5-1)
- <span id="page-27-3"></span>Bowen, T. (2025): "Graduating into a Slowdown: Class of 2025 Meets a Frozen Job Market," . [7](#page-4-2)
- <span id="page-27-11"></span>Bresnahan, T. F., E. Brynjolfsson, and L. M. Hitt (2002): "Information Technology, Workplace Organization, and the Demand for Skilled Labor: Firm-Level Evidence\*," *The Quarterly Journal of Economics*, 117, 339–376. [5](#page-25-2)
- <span id="page-27-8"></span>Brynjolfsson, E. (2022): "The Turing Trap: The Promise and Peril of Human-Like Artificial Intelligence," *Daedalus*, 151, 272–287. [4.3](#page-13-1)
- <span id="page-27-6"></span>Brynjolfsson, E., D. Li, and L. Raymond (2025): "Generative AI at Work\*," *The Quarterly Journal of Economics*, 140, 889–942. [2](#page-4-3)
- <span id="page-27-4"></span>Brynjolfsson, E. and T. Mitchell (2017): "What Can Machine Learning Do? Workforce Implications," *Science*, 358, 1530–1534. [2](#page-4-3)
- <span id="page-27-5"></span>Brynjolfsson, E., T. Mitchell, and D. Rock (2018): "What Can Machines Learn, and What Does It Mean for Occupations and the Economy?" *AEA Papers and Proceedings*, 108, 43–47. [2](#page-4-3)

- <span id="page-28-9"></span>Brynjolfsson, E., D. Rock, and C. Syverson (2021): "The Productivity J-Curve: How Intangibles Complement General Purpose Technologies," *American Economic Journal: Macroeconomics*, 13, 333–372. [5](#page-25-2)
- <span id="page-28-4"></span>Cajner, T., L. Crane, R. Decker, A. Hamins-Puertolas, C. Kurz, and T. Radler (2018): "Using Payroll Processor Microdata to Measure Aggregate Labor Market Activity," Tech. rep., The Federal Reserve Board of Governors. [3.1,](#page-6-3) [13](#page-7-1)
- <span id="page-28-8"></span>Chandar, B. (2025a): "Shifts in the Composition of College Workers: Implications for US Inequality and Labor Demand," Tech. rep., Social Science Research Network. [24](#page-23-2)
- <span id="page-28-0"></span>——— (2025b): "Tracking Employment in AI-Exposed Jobs," Tech. rep., Social Science Research Network. [7,](#page-4-2) [2,](#page-4-3) [4.6](#page-24-2)
- <span id="page-28-6"></span>Chen, J. and J. Roth (2024): "Logs with Zeros? Some Problems and Solutions\*," *The Quarterly Journal of Economics*, 139, 891–936. [17](#page-18-0)
- <span id="page-28-5"></span>Chen, J. L. a. T.-P. (2025): "Young Graduates Are Facing an Employment Crisis," *WSJ*, section: Economy. [4.2](#page-12-1)
- <span id="page-28-3"></span>Chen, W. X., S. Srinivasan, and S. Zakerinia (2025): "Displacement or Complementarity? The Labor Market Impact of Generative AI," . [9](#page-5-1)
- <span id="page-28-7"></span>Davis, S. J. and P. M. Krolikowski (2025): "Sticky Wages on the Layoff Margin," *American Economic Review*, 115, 491–524. [4.5](#page-19-0)
- <span id="page-28-2"></span>Dell'Acqua, F., E. McFowland III, E. R. Mollick, H. Lifshitz-Assaf, K. Kellogg, S. Rajendran, L. Krayer, F. Candelon, and K. R. Lakhani (2023): "Navigating the Jagged Technological Frontier: Field Experimental Evidence of the Effects of AI on Knowledge Worker Productivity and Quality," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [8](#page-5-0)
- <span id="page-28-1"></span>Demirci, O., J. Hannane, and X. Zhu (2025): "Who is AI replacing? The impact of generative AI on online freelancing platforms," *Management Science*. [2](#page-4-3)

- <span id="page-29-12"></span><span id="page-29-8"></span>Dillon, E., S. Jaffe, S. Peng, and A. Cambon (2025): "Early Impacts of M365 Copilot," Tech. Rep. MSR-TR-2025-18, Microsoft. [2](#page-4-3)
- <span id="page-29-10"></span>Dingel, J. I. and B. Neiman (2020): "How many jobs can be done at home?" *Journal of Public Economics*, 189, 104235. [3.3,](#page-8-1) [4.6,](#page-23-3) [A6,](#page-39-0) [A7](#page-40-0)
- <span id="page-29-9"></span>Dominski, J. and Y. S. Lee (2025): "Advancing AI Capabilities and Evolving Labor Outcomes," Tech. rep., arXiv, arXiv:2507.08244 [econ]. [2,](#page-4-3) [4.6](#page-24-2)
- <span id="page-29-2"></span>Doshay, H. and A. Bantock (2025): "The SignalFire State of Tech Talent Report - 2025," . [7](#page-4-2)
- <span id="page-29-0"></span>Eckhardt, S. and N. Goldschlag (2025): "AI and Jobs: The Final Word (Until the Next One)," *Economic Innovation Group*. [2,](#page-4-3) [4.6](#page-24-2)
- <span id="page-29-6"></span>Eloundou, T., S. Manning, P. Mishkin, and D. Rock (2024): "GPTs are GPTs: Labor market impact potential of LLMs," *Science*, 384, 1306–1308, publisher: American Association for the Advancement of Science. [2,](#page-4-3) [10,](#page-6-0) [3.2,](#page-7-0) [4.1,](#page-9-0) [2,](#page-10-0) [3,](#page-11-0) [4.3,](#page-13-1) [4.4,](#page-14-2) [9,](#page-19-0) [4.5,](#page-19-0) [11,](#page-22-0) [4.6,](#page-23-4) [A4,](#page-37-0) [A5,](#page-38-0) [A6,](#page-39-0) [A7,](#page-40-0) [A8,](#page-41-0) [A12,](#page-45-0) [A13,](#page-46-0) [A14,](#page-47-0) [A15,](#page-48-0) [A16,](#page-49-0) [A17,](#page-50-0) [A21,](#page-54-0) [A1](#page-55-0)
- <span id="page-29-1"></span>Ettenheim, L. E. a. K. B. |. G. b. R. (2025): "AI Is Wrecking an Already Fragile Job Market for College Graduates," *WSJ*, section: Tech. [6](#page-4-1)
- <span id="page-29-11"></span>Federal Reserve Bank of New York (2025): "The Labor Market for Recent College Graduates," . [4.2](#page-12-1)
- <span id="page-29-5"></span>Felten, E., M. Raj, and R. Seamans (2021): "Occupational, industry, and geographic exposure to artificial intelligence: A novel dataset and its potential uses," *Strategic Management Journal*, 42, 2195–2217, \_eprint: https://onlinelibrary.wiley.com/doi/pdf/10.1002/smj.3286. [2](#page-4-3)
- <span id="page-29-7"></span>——— (2023): "How will Language Modelers like ChatGPT Affect Occupations and Industries?" Tech. rep., arXiv, arXiv:2303.01157 [econ]. [2](#page-4-3)
- <span id="page-29-3"></span>Felten, E. W., M. Raj, and R. Seamans (2018): "A Method to Link Advances in Artificial Intelligence to Occupational Abilities," *AEA Papers and Proceedings*, 108, 54–57. [2](#page-4-3)

<span id="page-29-4"></span><sup>——— (2019): &</sup>quot;The Occupational Impact of Artificial Intelligence: Labor, Skills, and Polarization," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [2](#page-4-3)

- <span id="page-30-9"></span>Frank, M. R., Y.-Y. Ahn, and E. Moro (2025): "AI exposure predicts unemployment risk: A new approach to technology-driven job loss," *PNAS Nexus*, 4, pgaf107. [9](#page-5-1)
- <span id="page-30-4"></span>Frey, C. B. and M. A. Osborne (2017): "The future of employment: How susceptible are jobs to computerisation?" *Technological Forecasting and Social Change*, 114, 254–280. [2](#page-4-3)
- <span id="page-30-1"></span>Frick, W. (2025): "AI Is Everywhere But the Jobs Data," *Bloomberg.com*. [2](#page-4-3)
- <span id="page-30-5"></span>Gmyrek, P., J. Berg, and D. Bescond (2023): "Generative AI and Jobs: A Global Analysis of Potential Effects on Job Quantity and Quality," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [2](#page-4-3)
- <span id="page-30-8"></span>Hampole, M., D. Papanikolaou, L. D. Schmidt, and B. Seegmiller (2025): "Artificial Intelligence and the Labor Market," Working Paper, National Bureau of Economic Research. [2,](#page-4-3) [10](#page-6-0)
- <span id="page-30-6"></span>Handa, K., A. Tamkin, M. McCain, S. Huang, E. Durmus, S. Heck, J. Mueller, J. Hong, S. Ritchie, T. Belonax, K. K. Troy, D. Amodei, J. Kaplan, J. Clark, and D. Ganguli (2025): "Which Economic Tasks are Performed with AI? Evidence from Millions of Claude Conversations," Tech. rep., arXiv, arXiv:2503.04761 [cs]. [2,](#page-4-3) [3.2,](#page-7-0) [14,](#page-7-2) [4.3,](#page-13-1) [6,](#page-15-0) [7,](#page-16-0) [8,](#page-17-0) [A2,](#page-35-0) [A3,](#page-36-0) [A9,](#page-42-0) [A10,](#page-43-0) [A11,](#page-44-0) [A1,](#page-55-0) [A2](#page-56-0)
- <span id="page-30-0"></span>Hartley, J., F. Jolevski, V. Melo, and B. Moore (2025): "The Labor Market Effects of Generative Artificial Intelligence," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [1,](#page-1-3) [9](#page-5-1)
- <span id="page-30-3"></span>Hoover, A. (2025): "The AI coding apocalypse," *Business Insider*. [6](#page-4-1)
- <span id="page-30-2"></span>Horowitch, R. (2025): "The Computer-Science Bubble Is Bursting," *The Atlantic*, section: Economy. [6,](#page-4-1) [4.1,](#page-8-0) [5](#page-25-2)
- <span id="page-30-7"></span>Hui, X., O. Reshef, and L. Zhou (2023): "The Short-Term Effects of Generative Artificial Intelligence on Employment: Evidence from an Online Labor Market," SSRN Scholarly Paper, Rochester, NY. [2](#page-4-3)

- <span id="page-31-6"></span>Humlum, A. and E. Vestergaard (2025): "Large Language Models, Small Labor Market Effects," Working Paper, National Bureau of Economic Research. [2](#page-4-3)
- <span id="page-31-1"></span>Ide, E. (2025): "Automation, AI, and the Intergenerational Transmission of Knowledge," *arXiv preprint arXiv:2507.16078*. [1](#page-1-3)
- <span id="page-31-4"></span>Jamali, L. (2025): "Microsoft to cut up to 9,000 jobs as it invests in AI," *BBC*. [6](#page-4-1)
- <span id="page-31-7"></span>Jiang, W., J. Park, R. Xiao, and S. Zhang (2025): "AI and the Extended Workday: Productivity, Contracting Efficiency, and Distribution of Rents," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [2](#page-4-3)
- <span id="page-31-8"></span>Johnston, A. and C. Makridis (2025): "The Labor Market Effects of Generative AI: A Difference-in-Differences Analysis of AI Exposure," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [2,](#page-4-3) [10](#page-6-0)
- <span id="page-31-10"></span>Kochhar, R. (2023): "Which U.S. Workers Are More Exposed to AI on Their Jobs?" *Pew Research Center*. [26](#page-24-1)
- <span id="page-31-9"></span>Kuhfeld, M. and K. Lewis (2025): "5 years after COVID-19 hit: Test data converge on math gains, stalled reading recovery," *Brookings*. [4.6](#page-23-5)
- <span id="page-31-5"></span>Lenny Rachitsky (2025): "State of the product job market in 2025," *Lenny's Newsletter*, accessed: 2025-05-30. [7](#page-4-2)
- <span id="page-31-2"></span>Lim, S., D. Strauss, J. Burn-Murdoch, and C. Murray (2025): "Is AI killing graduate jobs?" *Financial Times*. [2,](#page-4-3) [7,](#page-4-2) [4.6](#page-24-2)
- <span id="page-31-0"></span>Maslej, N., L. Fattorini, R. Perrault, Y. Gil, V. Parli, N. Kariuki, E. Capstick, A. Reuel, E. Brynjolfsson, J. Etchemendy, et al. (2025): "Artificial intelligence index report 2025," *arXiv preprint arXiv:2504.07139*. [1](#page-1-3)
- <span id="page-31-3"></span>Milmo, D. and L. Almeida (2025): "'Workforce crisis': key takeaways for graduates battling AI in the jobs market," *The Guardian*. [6](#page-4-1)

- <span id="page-32-10"></span>Noy, S. and W. Zhang (2023): "Experimental evidence on the productivity effects of generative artificial intelligence," *Science*, 381, 187–192, publisher: American Association for the Advancement of Science. [8](#page-5-0)
- <span id="page-32-12"></span>O'Brien, C. (2025): "A viral chart on recent graduate unemployment is misleading," *Agglomerations*. [2,](#page-4-3) [4.6](#page-24-2)
- <span id="page-32-5"></span>Peck, E. (2025): "AI is keeping recent college grads out of work," *Axios*. [6](#page-4-1)
- <span id="page-32-11"></span>Peng, S., E. Kalliamvakou, P. Cihon, and M. Demirer (2023): "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot," Tech. rep., arXiv, arXiv:2302.06590 [cs]. [8](#page-5-0)
- <span id="page-32-3"></span>Raman, A. (2025): "Opinion | I'm a LinkedIn Executive. I See the Bottom Rung of the Career Ladder Breaking." *The New York Times*. [6,](#page-4-1) [4.1](#page-8-0)
- <span id="page-32-6"></span>Raval, A. (2025): "The AI job cuts are accelerating," *Financial Times*. [6](#page-4-1)
- <span id="page-32-4"></span>Roose, K. (2025): "For Some Recent Graduates, the A.I. Job Apocalypse May Already Be Here," *The New York Times*. [6](#page-4-1)
- <span id="page-32-7"></span>Sherman, N. (2025): "Amazon boss says AI will replace jobs at tech giant," *BBC News*. [6](#page-4-1)
- <span id="page-32-8"></span>Simon, L. K. (2025): "Is AI responsible for the rise in entry-level unemployment?" *Revelio Labs*. [7](#page-4-2)
- <span id="page-32-2"></span>Smith, N. (2025): "Stop pretending you know what AI does to the economy," . [2](#page-4-3)
- <span id="page-32-1"></span>The Economist (2025): "Why AI hasn't taken your job," *The Economist*. [2](#page-4-3)
- <span id="page-32-0"></span>Thompson, D. (2025): "Something Alarming Is Happening to the Job Market," *The Atlantic*, section: Economy. [2,](#page-4-3) [4.1](#page-8-0)
- <span id="page-32-9"></span>Tomlinson, K., S. Jaffe, W. Wang, S. Counts, and S. Suri (2025): "Working with AI: Measuring the Occupational Implications of Generative AI," Tech. rep., arXiv, arXiv:2507.07935 [cs]. [2](#page-4-3)

- <span id="page-33-1"></span>Webb, M. (2019): "The Impact of Artificial Intelligence on the Labor Market," SSRN Scholarly Paper, Social Science Research Network, Rochester, NY. [2](#page-4-3)
- <span id="page-33-0"></span>Wu, T. (2025): "Opinion | A 'White-Collar Blood Bath' Doesn't Have to Be Our Fate," *The New York Times*. [6](#page-4-1)

Appendix

<span id="page-34-0"></span>![](_page_34_Figure_1.jpeg)

Figure A1: Employment changes for computer occupations (2010 SOC codes starting with 15-1) and service clerks (starting with  $43-4$ ), normalized to 1 in October 2022.

<span id="page-35-0"></span>![](_page_35_Figure_0.jpeg)

Figure A2: Employment changes by age and automation level using Claude usage data from Handa et al.  $(2025)$ . Excluding occupations that have no Claude usage or are in the lowest quintile of overall Claude usage conditional on some usage.

<span id="page-36-0"></span>![](_page_36_Figure_0.jpeg)

Figure A3: Employment changes by age and augmentation quintile using Claude usage data from Handa et al.  $(2025)$ . Excluding occupations that have no Claude usage or are in the lowest quintile of overall Claude usage conditional on some usage.

<span id="page-37-0"></span>![](_page_37_Figure_0.jpeg)

 $\begin{minipage}{0.99\linewidth} Figure A4: \begin{minipage}{0.99\linewidth} Employment changes by age and exposure quintile using measures from Eloundou et al. \end{minipage} \end{minipage} \end{minipage}$ (2024). Excluding computer occupations (2010 SOC codes starting with 15-1).

<span id="page-38-0"></span>![](_page_38_Figure_0.jpeg)

Figure A5: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Excluding firms in the information sector (NAICS code 51).

<span id="page-39-0"></span>![](_page_39_Figure_0.jpeg)

Figure A6: Employment changes by age and exposure group using measures from Eloundou et al.  $(2024)$ . Including only teleworkable occupations according to Dingel and Neiman  $(2020)$ . Note that very few teleworkable occupations fall in the lowest exposure quintile. All occupations in the first and second quintile are consequently grouped together in level 1. The remaining quintiles are coded as  $2, 3, \text{ and } 4.$ 

<span id="page-40-0"></span>![](_page_40_Figure_0.jpeg)

Figure A7: Employment changes by age and exposure group using measures from Eloundou et al.  $(2024)$ . Including only non-teleworkable occupations according to Dingel and Neiman  $(2020)$ . Note that very few non-teleworkable occupations fall in the highest exposure quintile. All occupations in the fourth and fifth quintile are consequently grouped together in level 4. The remaining quintiles are coded as  $1, 2, \text{ and } 3.$ 

<span id="page-41-0"></span>![](_page_41_Figure_0.jpeg)

Figure A8: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Data is from 2018 to 2025.

<span id="page-42-0"></span>![](_page_42_Figure_0.jpeg)

Figure A9: Employment changes by age and exposure quintile using Claude usage data from Handa et al.  $(2025)$ . Occupations whose associated tasks all have fewer than the minimum number of queries to appear in the usage data are treated as a separate category, coded as 0. Data is from  $2018$  to  $2025$ .

<span id="page-43-0"></span>![](_page_43_Figure_0.jpeg)

Figure A10: Employment changes by age and automation level using Claude usage data from Handa et al. (2025). Data is from 2018 to 2025.

<span id="page-44-0"></span>![](_page_44_Figure_0.jpeg)

Figure A11: Employment changes by age and augmentation quintile using Claude usage data from Handa et al. (2025). Data is from 2018 to 2025.

<span id="page-45-0"></span>![](_page_45_Figure_0.jpeg)

Figure A12: Employment changes by age and exposure quintile using measures from Eloundou et al. (2024). Considering only occupations in which at least  $70\%$  of workers have a college degree in the 2017 ACS. Note that no such occupations lie in quintile 1 of the GPT-4  $\beta$  based exposure  $measure.$ 

<span id="page-46-0"></span>![](_page_46_Figure_0.jpeg)

Figure A13: Employment changes by age and exposure quintile using measures from Eloundou et al. (2024). Considering only occupations in which at most  $30\%$  of workers have a college degree in the 2017 ACS.

<span id="page-47-0"></span>![](_page_47_Figure_0.jpeg)

Figure A14: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Considering only men.

<span id="page-48-0"></span>![](_page_48_Figure_0.jpeg)

Figure A15: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Considering only women.

<span id="page-49-0"></span>![](_page_49_Figure_0.jpeg)

Figure A16: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Using the full sample of firms.

<span id="page-50-0"></span>![](_page_50_Figure_0.jpeg)

Figure A17: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Including part-time and temporary workers.

<span id="page-51-0"></span>![](_page_51_Figure_0.jpeg)

Figure A18: Employment changes for software developers by age, normalized to 1 in October 2022. Data come from the monthly CPS.

![](_page_52_Figure_0.jpeg)

Figure A19: Employment changes for customer service representatives by age, normalized to 1 in October 2022. Data come from the monthly CPS.

<span id="page-53-0"></span>![](_page_53_Figure_0.jpeg)

Figure A20: Employment changes for home health aides by age, normalized to 1 in October 2022. Data come from the monthly CPS.

<span id="page-54-0"></span>![](_page_54_Figure_0.jpeg)

Figure A21: Employment changes by age and exposure quintile using measures from Eloundou et al.  $(2024)$ . Data come from the monthly CPS.

<span id="page-55-0"></span>

| Metric                                | Least exposed (examples)                                                                                                                                                                               | Most exposed (examples)                                                                                                                                                           |
|---------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Eloundou et al. (2024)<br>GPT-4 β     | • Maintenance and Repair Workers,<br>General<br>• Nursing, Psychiatric, and Home<br>Health Aides<br>• Laborers and Freight, Stock, and<br>Material Movers, Hand<br>• Maids and Housekeeping Cleaners   | • Customer Service Representatives<br>• Accountants and Auditors<br>• Software Developers, Applications<br>and Systems Software<br>• Secretaries and Administrative<br>Assistants |
| Handa et al. (2025)<br>(Overall)      | • Taxi Drivers and Chauffers<br>• First-Line Supervisors of<br>Production and Operating<br>Workers<br>• Laborers and Freight, Stock, and<br>Material Movers, Hand<br>• Maids and Housekeeping Cleaners | • Computer Programmers<br>• Financial Managers<br>• Accountants and Auditors<br>• Sales Representatives, Wholesale<br>and Manufacturing                                           |
| Handa et al. (2025)<br>(Automation)   | • Maintenance and Repair Workers,<br>General<br>• Managers, All Other<br>• Nursing, Psychiatric, and Home<br>Health Aides<br>• Driver/Sales Workers and Truck<br>Drivers                               | • General and Operations Managers<br>• Accountants and Auditors<br>• Software Developers, Applications<br>and Systems Software<br>• Receptionists and Information<br>Clerks       |
| Handa et al. (2025)<br>(Augmentation) | • Cooks<br>• Welding, Soldering, and Brazing<br>Workers<br>• Tellers<br>• Drafters                                                                                                                     | • Chief Executives<br>• Maintenance and Repair Workers,<br>General<br>• Registered Nurses<br>• Computer and Information<br>Systems Managers                                       |

Table A1: Example occupations by exposure category

<span id="page-56-0"></span>

| Automative Behaviors                                                                                                                                                                                                                      | Augmentative Behaviors                                                                                                                                                                                                                        |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| AI directly executes tasks with minimal human                                                                                                                                                                                             | AI enhances human capabilities through collab                                                                                                                                                                                                 |
| involvement                                                                                                                                                                                                                               | oration                                                                                                                                                                                                                                       |
| Directive:                                                                                                                                                                                                                                | Task Iteration:                                                                                                                                                                                                                               |
| Complete task delegation with min                                                                                                                                                                                                         | Collaborative refinement pro                                                                                                                                                                                                                  |
| imal interaction                                                                                                                                                                                                                          | cess                                                                                                                                                                                                                                          |
| Illustrative                                                                                                                                                                                                                              | Illustrative Example:                                                                                                                                                                                                                         |
| Example:                                                                                                                                                                                                                                  | "Let's draft a marketing                                                                                                                                                                                                                      |
| "Format                                                                                                                                                                                                                                   | strategy for our new product.                                                                                                                                                                                                                 |
| this                                                                                                                                                                                                                                      |                                                                                                                                                                                                                                               |
| technical                                                                                                                                                                                                                                 | Good start,                                                                                                                                                                                                                                   |
| documentation in Markdown"                                                                                                                                                                                                                | but can we add some concrete metrics?"                                                                                                                                                                                                        |
| Feedback Loop:<br>Task completion guided by<br>environmental feedback<br>Illustrative Example: "Here's my Python script<br>for data analysis – it's giving an IndexError.<br>Can you help fix it?  Now I'm getting a dif<br>ferent error" | Learning:<br>Knowledge acquisition and under<br>standing<br>Illustrative<br>Example:<br>"Can<br>you<br>explain<br>how<br>neural networks work?"                                                                                               |
|                                                                                                                                                                                                                                           | Validation:<br>Work verification and improve<br>ment<br>Illustrative<br>Example:<br>"I've<br>written<br>this<br>SQL<br>query to find duplicate customer records.<br>Can<br>you check if my logic is correct and suggest any<br>improvements?" |

Table A2: Table 1 from [Handa et al.](#page-30-6) [\(2025\)](#page-30-6). [Handa et al.](#page-30-6) [\(2025\)](#page-30-6) classify conversations from Claude, the LLM, into five distinct patterns across two broad categories based on how people integrate AI into their workflow.