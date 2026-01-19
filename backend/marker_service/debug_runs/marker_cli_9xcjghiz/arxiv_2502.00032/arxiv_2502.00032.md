# QUERYING DATABASES WITH FUNCTION CALLING

| Connor Shorten | Charles Pierse                  | Thomas Benjamin Smith | Karel D'Oosterlinck       | Tuana Celik     |
|----------------|---------------------------------|-----------------------|---------------------------|-----------------|
| Weaviate       | Weaviate                        | Weaviate              | Contextual AI             | Weaviate        |
| Erika Cardenas | Leonie Monigatti                | Mohd Shukri Hasan     | Edward Schmuhl            | Daniel Williams |
| Weaviate       | Weaviate                        | Weaviate              | Weaviate                  | Weaviate        |
|                | Aravind Kesiraju<br>Morningstar |                       | Bob van Luijt<br>Weaviate |                 |

## ABSTRACT

The capabilities of Large Language Models (LLMs) are rapidly accelerating largely thanks to their integration with external tools. Querying databases is among the most effective of these integrations, enabling LLMs to access private or continually updating data. While Function Calling is the most common method for interfacing external tools to LLMs, its application to database querying as a tool has been underexplored. In this report, we propose and extensively test a tool definition for database querying that unifies accessing data with search queries, filters, or a combination both, as well as transforming results with aggregation and groupby operators. Our proposed tool definition additionally enables the LLM to route queries across multiple collections of data. To evaluate its effectiveness, we conduct a study with 8 LLMs spanning 5 model families. We present a novel pipeline adapting the Gorilla LLM framework to create synthetic search database schemas and queries. We present an analysis comparing our proposed DBGorilla dataset to popular text-to-SQL benchmarks such as BIRD, Spider, and WikiSQL. Using the DBGorilla benchmark, we show that Claude 3.5 Sonnet, GPT-4o, GPT-4o mini, and Gemini 1.5 Pro are all highly effective at utilizing our proposed tool definition for querying databases. We primarily evaluate these models with the Exact Match of predicted and ground truth query APIs. To gain a more holistic understanding of model performance, we also report Abstract Syntax Tree (AST) alignment scores and LLM-as-Judge preference rankings of predicted queries. Among the eight models tested, Claude 3.5 Sonnet achieves the highest performance with an Exact Match score of 74.3%, followed by GPT-4o mini at 73.7%, GPT-4o at 71.8%, and Gemini 1.5 Pro at 70.2%. We further breakdown these results by API component, finding that LLMs are highly effective at utilizing operators on boolean-valued properties, but struggle to understand text property filters and differentiate them from search queries. We further visualize the performance across the synthetic use cases, showing robust results with the higher performing models such as GPT-4o, but significant performance variance across use cases from lower performing models. To further understand the impact of tool definitions on connecting LLMs with querying databases, we conduct ablation studies exploring the impact of parallel tool calling, adding a rationale as an argument of the tool call, using a separate tool per database collection, and tool calling with structured outputs. We find minimal performance variance across these ablation experiments with GPT-4o. Our findings demonstrate the effectiveness of enabling LLMs to query databases with Function Calling. We have open-sourced our experimental code and results at github.com/weaviate/gorilla.

## 1 Introduction

Large Language Models (LLMs) have achieved remarkable successes in natural language understanding and reasoning. The applications of LLMs are rapidly advancing as they are connected with other software tools in architectures broadly described as Compound AI Systems. From Zaharia et al., a Compound AI System "tackles AI tasks using multiple interacting components, including multiple calls to models, retrievers, or external tools" [\[1\]](#page-11-0). Connecting AI models to external software tools complements their weaknesses, such as accessing private or continually updating data, as well as

| LLM<br>Tested            | Exact<br>Match | Simple<br>Queries | Moderate<br>Queries | Complex<br>Queries | AST<br>Score | Collection<br>Routing |
|--------------------------|----------------|-------------------|---------------------|--------------------|--------------|-----------------------|
| <b>Claude 3.5 Sonnet</b> | 74.3%          | 77.5%             | 76.4%               | 72.1%              | 0.973        | 96.9%                 |
| <b>GPT 40 mini</b>       | 73.7%          | 80.0%             | 69.1%               | 75.2%              | 0.952        | 97.5%                 |
| GPT 4o                   | 71.8%          | 87.5%             | 70.0%               | 69.1%              | 0.966        | 96.8%                 |
| Gemini 1.5 Pro           | 70.2%          | 67.5%             | 63.6%               | 75.2%              | 0.956        | 93.0%                 |
| Command R+               | 59.4%          | 72.5%             | 68.2%               | 50.3%              | 0.933        | 94.3%                 |
| <b>Command R7B</b>       | 39.1%          | 55.0%             | 44.6%               | 31.5%              | 0.887        | 84.4%                 |
| Gemini 2.0 Flash         | 37.1%          | 35.0%             | 36.4%               | 38.2%              | 0.449        | 46.0%                 |
| Llama 3.1 8B Instruct    | 32.1%          | 27.5%             | 26.4%               | 37.0%              | 0.894        | 76.8%                 |

Figure 1: DBGorilla Leaderboard results (last updated January 1st, 2025). The Exact Match and AST Score columns report the respective averages across all tested queries. Query scores are further separated into categories of "Simple", "Moderate", and "Complex" according to how many arguments are used in the ground truth function call with 1, 2, and 3 or more, respectively. Collection routing reports the percentage the predicted query is routed to the correct database collection.

symbolic computation. However, understanding the most effective interface between LLMs and external tools remains an open question. Pioneered by works such as ReAct [\[2\]](#page-11-1) and the Gorilla LLM [\[3\]](#page-11-2), Function Calling has emerged as a powerful architecture for Compound AI Systems. Defined in OpenAI's developer documentation, "function calling enables developers to connect language models to external data and systems. You can define a set of functions as tools that the model has access to, and it can use them when appropriate based on the conversation history. You can then execute those functions on the application side, and provide results back to the model"[\[4\]](#page-11-3). OpenAI, as well as many other model providers and open-source tools provide JSON schemas with which to define these functions with. In our work, we propose and test a function definition following this interface for querying databases.

Function Calling has seen enormous application in Compound AI System design, but has mostly been limited to relatively simple tools. For example, a get\_unread\_emails function that does not require any input arguments and returns unread emails. Another common example demonstrating Function Calling is the get\_weather function. Interestingly, this function has constraints on its input argument, requiring a 5 digit integer-valued zip code to access the weather across cities in the United States of America. This is very similar to how one might approach interfacing database querying with SQL through Function Calling, requiring constraints on a string-valued sql\_query argument of a query\_database function. Unfortunately, Function Calling does not yet support advanced constraints on input arguments, limiting the effectiveness of SQL with Function Calling. We instead show how we can decompose query APIs into a series of optional JSON-valued arguments to better utilize SQL-style query operators with Function Calling.

Most previous works on database querying with machine learning models has focused on text-to-SQL translations. However, as highlighted in recent works such as Spider 2.0, "real-world data are stored across a diverse array of database systems, each with its own unique SQL dialects, introducing a wide range of SQL syntax and functions" [\[5\]](#page-11-4). These SQL dialects are often highly specific to the underlying database system being queried. For example, the query operators available in a database system built on top of the relational data model differ from document or graph data models. Thus we propose disentangling the SQL syntax from the particular query operators the LLM has access to. Shown in Figure 2, we translate natural language commands into Function Calling arguments, instead of SQL. One notable benefit of decoupling query operators from SQL syntax is how easily we can plug and play with different query operators. As one example of what this allows us to do, we unify structured data access and result transformations with search queries. As highlighted by Wu et al. in the presentation of the STaRK benchmark, "many previous works studied textual and relational retrieval tasks as separate topics" [\[6\]](#page-11-5). We propose that this isolation is due to textual and relational retrieval tasks being built on distinct underlying data models. The relational data model typically assumes multiple

![](_page_2_Figure_0.jpeg)

Figure 2: An illustration of a natural language command, How many menu items are priced under 20?, translated to Function Calling arguments for database querying.

normalized tables linked together with foreign keys and frequent use of the JOIN query operator. On the other hand, textual retrieval typically assumes a single collection of data with a single text property per object that is stored in a search index. Our tool definition for Function Calling adds the search operator to a collection of operators derived from the relational data model. This tool definition can be trivially mapped to and from custom SQL dialects or extended with functionality from less conventional data models such as SPARQL [\[7\]](#page-12-0). We can also easily integrate new operators introduced in emerging languages such as LOTUS [\[8\]](#page-12-1), TAG [\[9\]](#page-12-2), or SUQL [\[10\]](#page-12-3) to Function Calling arguments.

To evaluate LLMs' ability to format database queries with Function Calling, we present the DBGorilla benchmark. DBGorilla is an adaption of the Berkley Function Calling Leaderboard [\[11\]](#page-12-4) and Gorilla LLM following the use of Self-Instruct to create synthetic natural language commands targeted towards the combinatorics of API operators. Extending the original Gorilla LLM methodology, DBGorilla requires a synthetic database schema in order to ground the natural language commands and ground truth query operator values. We thus begin by presenting a framework to generate synthetic database use cases. Each generated use case represents a distinct business domain and consists of three interrelated collection schemas. Every collection is designed with a searchable text property and three additional properties, one numeric, one textual, and one boolean, to enable comprehensive testing of different query patterns. This structured approach allows us to systematically assess how well LLMs can interpret database schemas and translate natural language requests into appropriate database operations. Given this dataset of schemas, we then create a comprehensive test dataset of queries covering all combinations of query operators defined in the tool schema. These capabilities include search queries for finding relevant results based on relevance ranking algorithms, property filters for matching on integer, text, and boolean fields, aggregations for computing statistics over integer, text, and boolean properties, and grouping operations to segment results by property values.

Utilizing the DBGorilla benchmark, we compare 8 LLMs from 5 model families on the task of choosing the correct database query API given the schemas of collections available to query and a natural language command as input. Some queries only require a single API, such as: How many unique menu items are priced under \$20?. This can be answered with an integer filter that sets the price less than \$20. Contrastively, the query: What is the average price of seasonal specialty menu items under \$20, grouped by whether they are vegetarian or not? requires a search query for "seasonal specialties", setting a price filter of less than \$20, calculating the average price of the results, and grouping them by the isVegetarian boolean property. All queries require routing to the appropriate collection.

We primarly report Exact Match as our performance metric. Exact Match is a boolean metric assessing if the predicted query from the LLM is identical to the ground truth query. This metric is particularly insightful thanks to the targeted nature of the synthetic benchmark dataset. To gain more insight into the accuracy of predicted queries, we also report the structural similarity of predicted and ground truth queries with Abstract Syntax Tree (AST) scoring. The AST approach breaks down queries into their hierarchical components starting with the target collection as the root node, followed by branches for search queries, filters, aggregations, and grouping operations. The scoring heavily weights getting the target collection correct (40% of total score), as this is fundamental to query correctness. The remaining score is evenly distributed (15% each) across matching the search query text, filter specifications, aggregation operations, and grouping property. This hierarchical scoring approach allows us to quantify partial successes in query generation and identify specific areas where models struggle. We additionally present an LLM-as-judge preference ranking analysis as another lens into LLM querying performance. This entails using an LLM to rank the predicted queries from each of the 8

LLMs for a given natural language command and database schema. We further present the Collection Routing accuracy, the percentage of time the predicted query targets the correct collection. Finally, we report the tool selection rate as the number of times the LLM decides it needs to perform a function call in the initial step of the Function Calling framework.

In summary our contributions are as follows:

- We introduce DBGorilla, a collection of 5 use cases, each with 3 related collections and 4 properties per collection. We additionally present 315 queries, 63 unique combinations of query APIs for each of the 5 use cases. We present a cost analysis of maintaining and creating this benchmark, as well as a discussion of directions for expansion.
- We present a tool definition schema that unifies search queries and structured data access. We demonstrate that Claude 3.5 Sonnet, GPT-4o, GPT-4o-mini, and Gemini 1.5 Pro are all highly effective at formatting API calls for querying a search database using this tool definition with Function Calling.
- We present ablation studies demonstrating that parallel tool calling, rationale generation, separate tool definitions per collection, and tool calling with structured outputs all have minimal impact on the resulting performance.

## 2 Related Works

## 2.1 Compound AI Systems

Tool use is one of the most promising opportunities to improve the capabilities of LLMs. There are two common design patterns for interfacing tool use in Compound AI Systems: Function Calling and Flow Engineering [\[12\]](#page-12-5). Visualized in Figure 4, Function Calling entails equipping the LLM with a set of functions described in the prompt. The LLM inference is then orchestrated in a function calling loop. At each step, the LLM either chooses to complete the response, or call one or multiple functions and wait for their respective responses to continue the next iteration of the loop. Contrastively, Flow Engineering describes a pre-determined flow of inferences and external tools calls. This abstraction helps clarify how tools are interfaced to LLMs. However, there is a significant overlap and this is a constantly evolving area of AI research. For example, an engineered LLM and tool calling flow could be itself abstracted and interfaced as a function for the agent to call. In a similar analog, a flow could implement the open-ended looping core to the definition of Function Calling. Understanding these distinctions is important for the evolution of prior works on interfacing search and database querying as an LLM tool. In either case, we need methods to evaluate how well LLMs can select the correct tool for the task and format the tool's respective arguments [\[3\]](#page-11-2).

Search has been one of the most commonly used tools for LLMs. Most commonly, this has taken the shape of RAG [\[13\]](#page-12-6), a pre-determined flow of retrieval with the user input as query, followed by response generation. RAG flows were further pioneered with architectures such as Baleen RAG, in which the user input is first translated into search queries with an LLM inference, sent to a retrieval engine, and passed into a final response generation. One of the early efforts to expand search to the Function Calling interface was WebGPT [\[14\]](#page-12-7), in which the LLM can format search queries to send to the web, as well as paginate through the results. Zhang et al. debuted the term "Agentic Information Retrieval" [\[15\]](#page-12-8) to capture the intersection of learning to search with the Function Calling interface.

## 2.2 Text-to-SQL

Developing mostly in parallel to search as a tool, AI researchers and practitioners have been exploring the use of database APIs as a tool. Even before breakthrough capabilities in LLMs, Text-to-SQL research has been a heavily studied discipline [\[16\]](#page-12-9). Text-to-SQL research has mostly targeted the application of making it easier for humans to learn how to query databases. We primarily studied three popular Text-to-SQL benchmarks in this work: WikiSQL [\[17\]](#page-12-10), Spider [\[18,](#page-12-11) [5\]](#page-11-4), and BIRD [\[19\]](#page-12-12). WikiSQL consists of 80,654 hand-annotated examples of questions and SQL queries distributed across 24,241 tables from Wikipedia. The original Spider dataset contains 10,181 questions and 5,693 unique complex SQL queries on 200 databases with multiple tables, covering 138 different domains. BIRD contains 12,751 Text-to-SQL pairs and 95 databases spanning 37 professional domains. We visualize samples from the BIRD dataset in Figure 3 to help readers further understand the current state-of-the-art in Text-to-SQL benchmarking. In Spider 2.0, the authors diverge from Text-to-SQL prediction to Text-to-SQL workflows, adopting a more holistic view of data querying and transformation with SQL.

Now that most databases are evolving to support search indexes and integration with LLMs, additional query languages are emerging to expand SQL, such as LOTUS [\[8\]](#page-12-1) and SUQL [\[10\]](#page-12-3). Our work is further related to managing multiple database collections in architectures such as Data Warehouses, Lakehouses [\[20\]](#page-12-13), or Ontologies [\[21\]](#page-12-14). In order to study machine learning for databases, we need new benchmarks and datasets reflective of the challenges of database systems.

![](_page_4_Figure_0.jpeg)

Figure 3: Examples of queries in the BIRD Text-to-SQL benchmark [\[19\]](#page-12-12). We visualize these to help readers gain a better understanding of how Text-to-SQL is currently studied and how BIRD differs from DBGorilla.

Similarly to our synthetic schemas, Lim et al. [\[22\]](#page-12-15) present Database Gyms, focusing on system-level optimization and workload simulation.

## 3 Methodology

## 3.1 Details of Function Calling Setup

As described in the context of Compound AI Systems, Function Calling entails equipping the LLM with a set of functions described in the prompt. The LLM inference is then orchestrated in a Function Calling loop. At each step, the LLM either chooses to complete the response, or call one or multiple functions and wait for their respective responses to continue the next iteration of the loop. We limit the Function Calling loop to a single step and evaluate the accuracy of the predicted Function Calling arguments. We use the tool definition shown in Appendix A.

More concretely, we store each record in our DBGorilla dataset with the properties, nl\_command, ground\_truth\_query, and schema. We send the schema to the database to create the collections. We then retrieve metadata about available collections and their properties from the database, although you could also achieve this from the schema stored in the dataset. We then parse this meta information into a description string detailing the collections and their properties, as well as a list of collection names that are used for routing queries as an enum-valued API argument. The description of collections and database querying is carefully constructed to fit within 1024 tokens due to token limits from the LLMs tested when using their respective Function Calling SDKs. The tool schema then exposes a query\_database function with parameters tailored to the database's querying capabilities. The collection\_name argument is the only required argument, which is restricted to the enumerated list of available collections. Optional parameters enable search queries, filters, aggregations, and groupby. We then pass the natural language command stored in the dataset to the LLM with the tool definition and record the arguments used in the function call. If the LLM chooses not to call a function, it achieves a score of 0 for this instance. This is motivated by the highly targeted nature of these natural language commands, which we will discuss further later on. We test the GPT-4o and GPT-4o mini LLMs [\[23\]](#page-12-16), Gemini 1.5 Pro and Gemini 2.0 Flash experimental [\[24\]](#page-12-17), Claude 3.5 Sonnet [\[25\]](#page-12-18), Command R+ and Command R7B [\[26\]](#page-12-19), and Llama 3.1 8B Instruct [\[27\]](#page-13-0).

## 3.2 DBGorilla Dataset Construction

We present a novel dataset for measuring the effectiveness of LLMs to query databases with Function Calling, DBGorilla. DBGorilla consists of two phases: synthetic schema and query generation. The construction of this dataset heavily relies on structured generation methods [\[28,](#page-13-1) [29,](#page-13-2) [30\]](#page-13-3). Structured outputs lets us easily control the validitiy of generated schema and query structure. We can easily use this framework to generate more synthetic schemas, or schemas with different property distributions. Further, we can easily switch out the query operators available to the LLM and construct

![](_page_5_Figure_0.jpeg)

Figure 4: An illustration of the Function Calling loop. Beginning with the user's input prompt, the LLM then enters a loop where it can either choose to call one or multiple functions, or return a response to the user. If a function is called, the function is executed, the response is sent back to the LLM, and the Function Calling loop continues.

a corresponding query set. In our discussion section, we present further thoughts on how to extend this benchmark and predictions for the evolution of benchmarking text-to-SQL and database use in Compound AI Systems.

#### 3.2.1 Synthetic Database Schemas

The schema generation process utilizes GPT-4o to create synthetic database schemas through a structured prompt. The database generation prompt contains a reference example schema that demonstrates the desired structure and detail level, along with specific requirements for each collection including two text properties (one with rich searchable content), one numeric property, and one boolean property. We note that these requirements can be varied to create diverse schema types, such as eight boolean properties and one searchable text property if desired. In order to test routing queries to multiple collections, the generator is further instructed to ensure collections are meaningfully related. However, we do not explicitly link these collections together with foreign key relationships. Using these inputs, we produce five schema sets, each containing three interconnected collections. An example is shown in Table 1, a use case modeling a restaurant system with Restaurants, Menus, and Reservations collections. Each generated schema follows consistent conventions with collection names in camel case format, comprehensive property definitions including types and detailed descriptions. We further generate a use\_case\_overview to facilitate interpretability of generated schemas.

#### 3.2.2 Synthetic Queries

The query generation process follows the algorithms introduced in Self-Instruct [\[31\]](#page-13-4) to create comprehensive test cases of API use cases. We extend Self-Instruct to add Reflexion [\[32\]](#page-13-5) to assess, and potentially correct, generated queries with another LLM inference. The addition of Reflexion to synthetic query generation helps us get a quantitative sense of dataset quality and qualitatively when manually inspecting individual queries with the user interface shown in Figure 6. We generate all valid combinations of query operators, including options for semantic search, filters (integer, text, boolean), aggregations, and grouping operations. For each operator combination, we create a Pydantic model that specifies required fields and includes descriptions of how each operator should be used, ensuring that the natural language query necessitates all selected operators. Using GPT-4o, we then generate natural language queries by providing the database schema and operator requirements, validating that each query requires all specified operators to be answered correctly by creating structured output models on the fly for each query combination. We run this

| Collection Name | Property Name                                                                             |
|-----------------|-------------------------------------------------------------------------------------------|
| Restaurants     | name (string)<br>description (string)<br>averageRating (number)<br>openNow (boolean)      |
| Menus           | menuItem (string)<br>itemDescription (string)<br>price (number)<br>isVegetarian (boolean) |
| Reservations    | reservationName (string)<br>notes (string)<br>partySize (number)<br>confirmed (boolean)   |

Table 1: A visualization of the Restaurant synthetic database schema.

process to yield 63 queries per schema. We produce 315 queries in total across 5 database schemas. We use our dataset visualizer GUI shown in Figure 6 to manually verify the quality of these queries.

## 3.3 Evaluating Predicted Queries

We present three strategies for evaluating the quality of predicted database queries with Function Calling. We primarily use Exact Match Scoring evaluation. Exact Match scoring returns a boolean assessment if the predicted and ground truth queries are exactly identical. We additionally utilize Abstract Syntax Tree (AST) evaluation. AST scores are a highly effective method to measure how aligned predicted queries are with the ground truth API components the natural language command is crafted to target. We further introduce a preference ranking evaluation using LLM-as-judge. This is largely inspired by the challenge of evaluating real-world queries that do not come with a ground truth API path. Preference ranking evaluation further offers additionally flexibility in query quality judgement and leniency in cases where the LLM chooses not to call a function. Although we note that due to the highly targeted nature of natural language commands in our dataset, it is never effective to choose not to call a function. Additionally, in our controlled environment with ground truth API queries, we can gain insight into the alignment of these metrics.

The AST evaluation methodology employs a weighted scoring system to assess query similarity. The largest weight (40%) is assigned to correctly matching the target collection, mismatching collections results in a score of 0. The remaining 60% is evenly distributed (15% each) across four components: search queries, filters, aggregations, and group by operations. We do not evaluate if the search queries are similar, only if the predicted and ground truth queries both use the search query or not. Contrastively, filters, aggregations, and groupby values must be identical to the ground truth query to achieve the 0.15 points for the match. The final score ranges from 0.0 to 1.0, with 1.0 indicating perfect structural alignment across all elements.

In order to better understand the performance of Large Language Models to format database queries, we conduct an llm-as-judge preference ranking test. The test utilized structured outputs to rank the 8 LLM responses on a scale of 1 to 8. The model additionally presents an explanation of why it decided on the particular ranking for the user query. We report the number of 1st place rankings each model receive, as well as a weighted score across ranks. We report the number of first place ranks each model achieves, as well as a weighted rank scoring. The weighted scoring system grants 100 points for first place, 70 for second, 50 for third, 35 for fourth, 25 for fifth, 20 for sixth, 15 for seventh, 10 for eighth, 5 for ninth, and 0 for tenth place and beyond. This approach heavily rewards finishing near the top but still provides partial credit for mid-range positions, aiming to capture strong overall performance rather than sporadic high placements.

#### 3.4 DBGorilla Expansion and Maintenance Cost

The computational costs associated with running the DBGorilla benchmark reveal significant economic implications for model selection, deployment, and benchmark maintenance. As shown in Table 2, there is a stark contrast in costs across model families, with Claude 3.5 Sonnet being the most expensive at \$2.84 total cost, while Command R7B is the most economical at  $$0.03$ . These cost differentials do not strictly correlate with performance. For example, GPT-40 mini achieves strong results (73.7% Exact Match score) at \$0.12 total cost, suggesting a pareto-optimal frontier of price-performance. The benchmark's total token consumption (245,000 input tokens and 140,000 output tokens) provides a standardized basis for comparing model costs. From a benchmark maintenance perspective, the aggregate cost to evaluate all eight models is approximately \$8.10 per run. This translates to roughly \$97.20 annually for monthly evaluations. These maintenance costs are particularly relevant for the research community, as they enable regular updates to track the rapid evolution of LLM capabilities in database querying. The total cost supports the DBGorilla benchmark's sustainability and encourages broader participation in model evaluation and provide transparency about the resources required for replication studies. Generating the synthetic benchmark of 315 queries required a total of 413,516 input tokens and 86,457 output tokens. Shown in Table 2, this totals to \$1.89 with OpenAI GPT-4o.

| Model                 | Input Cost (\$) | Output Cost (\$) | Total Cost (\$) | Input Pricing $(\$/1M)$ | Output Pricing $(\$/1M)$ |
|-----------------------|-----------------|------------------|-----------------|-------------------------|--------------------------|
| Claude 3.5 Sonnet     | 0.74            | 2.10             | 2.84            | 3.00                    | 15.00                    |
| OpenAI GPT-40         | 0.61            | 1.40             | 2.00            | 2.50                    | 10.00                    |
| Command $R+$          | 0.61            | 1.40             | 2.00            | 2.50                    | 10.00                    |
| Gemini 1.5 Pro        | 0.31            | 0.70             | 1.01            | 1.25                    | 5.00                     |
| GPT-40 Mini           | 0.04            | 0.08             | 0.12            | 0.15                    | 0.60                     |
| Llama 3.1 8B Instruct | 0.02            | 0.014            | 0.04            | 0.10                    | 0.10                     |
| Gemini 1.5 Flash      | 0.02            | 0.04             | 0.06            | 0.075                   | 0.30                     |
| Command R7B           | 0.01            | 0.02             | 0.03            | 0.0375                  | 0.15                     |

Table 2: Cost comparison of models tested (last updated January 1st, 2025).

#### 4 **Experimental Results**

The DBGorilla leaderboard shown in Figure 1 illustrates a clear hierarchy in model performance across different evaluation metrics, with interesting patterns in performance. Claude 3.5 Sonnet leads overall with an Exact Match score of 74.3%, followed closely by GPT-40 mini at 73.7%, GPT-40 at 71.8% and Gemini 1.5 Pro at 70.2%. There is then a somewhat steep dropoff to  $59.4\%$  from Command R+, followed by a significant performance gap to Gemini 2.0 Flash ( $\exp$ ) at 37.1% and Llama 3.1 8B Instruct at 32.1%. Performance varies across different query complexities. For simple queries (requiring a single argument), the top models perform remarkably well, with GPT-4o achieving a score of 87.5% and Claude Sonnet 3.5 reaching 77.5%. Looking across query complexities, measured as requiring more than 1 operator, we see an encouraging robustness in performance. Claude 3.5 Sonnet's performance on Simple Queries at  $77.5\%$  is not too far off its' effectiveness with Complex Queries at 72.1%. The collection routing metric reveals another interesting pattern, while most top models hover around 96 to 98%, Command  $R$ + stands out with 94.3% accuracy despite a relatively lower 59.4% total Exact Match score, suggesting it has a particular strength in understanding and correctly selecting the appropriate database collection. The Abstract Syntax Tree (AST) scoring analysis reveals further nuance into model performance beyond Exact Match metrics. Claude 3.5 Sonnet achieves a nearly perfect 0.973 AST score. This indicates near perfect structural understanding of query components in cases missing the strict criterion of Exact Match scoring. The top four performing models all maintain AST scores above 0.95, additionally illustrating strong comprehension of query operator structure.

#### 4.1 Component and Schema Variance Analysis

To better understand where the LLMs went wrong in their predicted queries, we break performance down by API component involved in the ground truth queries. We present a radar plot visualization of this in Figure 5 and a detailed view of results in Table 6 and Table 7. Boolean filters stand out as the most successfully handled component across all models, with GPT-4o and Claud 3.5 Sonnet both achieving 87.5% Exact Match accuracy. However, their performance drops on boolean aggregations with scores of  $62.5\%$  and  $66.25\%$ , respectively. Most interestingly, the models show a significant performance decline on text filters, failing to distinguish them from search queries. The evaluation across different database schemas, shown in Table 2, reveals varying levels of domain adaptability among the models. GPT-4o demonstrated the most consistent cross-domain performance, with results ranging from 73.44% on the Restaurants use case to  $67.8\%$  on the Visual Arts use case, a range of  $5.64\%$ . This stability stands in marked contrast to smaller models. Gemini 2.0 Flash exhibited dramatic performance variance, ranging from 57.81% to 23.44%. These findings indicate a strong correlation between model size and the ability to maintain consistent performance across varied domains, with larger models demonstrating superior schema adaptability.

![](_page_8_Figure_0.jpeg)

Figure 5: Radar plots highlighting how well each model tested can access particular Search Database API components.

| Model                 | Restaurants | Health Clinics | Courses | Travel Planning | Visual Art |
|-----------------------|-------------|----------------|---------|-----------------|------------|
| GPT-4o                | 73.44%      | 76.56%         | 70.31%  | 70.31%          | 67.80%     |
| GPT-4o mini           | 75.00%      | 75.00%         | 68.75%  | 75.00%          | 74.58%     |
| Claude 3.5 Sonnet     | 71.88%      | 73.44%         | 71.88%  | 71.88%          | 83.05%     |
| Command R+            | 60.94%      | 50.00%         | 54.69%  | 60.94%          | 71.19%     |
| Command R 7B          | 39.06%      | 37.50%         | 35.94%  | 43.75%          | 38.98%     |
| Gemini 1.5 Pro        | 73.44%      | 65.62%         | 68.75%  | 73.44%          | 69.49%     |
| Gemini 2.0 Flash      | 57.81%      | 23.44%         | 35.94%  | 25.00%          | 44.07%     |
| Llama 3.1 8B Instruct | 31.25%      | 37.50%         | 31.25%  | 28.12%          | 32.20%     |

Table 3: Performance Across Different Schemas for All Tested Models

## 4.2 No Tool Selected

Shown in Figure 4, the Function Calling Loop begins with an initial design to call a function or respond to the user. We find that all LLMs tested occasionally skip function calling and immediately return the response without querying the database. This is particularly emphasized in the Gemini 2.0 Flash model, which skips function calling more often than not at a rate of 53.97%. This also explains Gemini 2.0 Flash's poor performance on the broader set of evaluation metrics such as Exact Match, Abstract Syntax Scoring, and Preference Ranking.

## 4.3 Preference Rankings

Across the 315 tested queries, only 5 result in identical predictions for the 8 LLMs tested. On average, each query has 5.8 unique predictions from the 8 LLMs. From the preference ranking results shown in Table 3, Gemini 1.5 Pro, GPT-4o mini and GPT-4o emerge as the most favored models, consistently occupying the highest portion of first-place votes. Meanwhile, Command R7B, Llama 3.1 8B Instruct, and Claude 3.5 Sonnet often fall toward the bottom in aggregated rankings. These results vary significantly from the Abstract Syntax Tree (AST) evaluations, which highlighted the same top three as highly skilled in generating structurally correct database queries. However, the slight discrepancies, such as Gemini 1.5-pro coming in first on llm-as-judge preference rankings, but fifth on AST, point to a key difference between technical correctness (how accurately the query matches a reference structure) and user preference (readability, clarity, or "perceived helpfulness").

| Model             | No Tool Selected Rate (%) |
|-------------------|---------------------------|
| GPT-4o            | 2.86%                     |
| GPT-4o-mini       | 0.95%                     |
| Claude 3.5 Sonnet | 3.17%                     |
| Command R+        | 4.44%                     |
| Command R7B       | 13.33%                    |
| Gemini 1.5 Pro    | 5.40%                     |
| Gemini 2.0 Flash  | 53.97%                    |
| Llama 3.1 8B      | 21.90%                    |

Table 4: As shown in Figure 4, the LLM is tasked with the decision to call a function or submit a response to the user. Despite our benchmark being particularly constructed to create natural language commands that require database queries, some models choose not to call a function in a surprisingly high percentage of test cases.

This preference ranking mechanism suggests an opportunity for query validation and refinement before execution. Recent works, such as Reflexion prompting [\[33\]](#page-13-6), DSPy Assertions [\[34\]](#page-13-7), and SPADE [\[35\]](#page-13-8), demonstrate how computational constraints can guide LLMs to automatically refine their outputs through self-correction. A similar approach could be applied to database querying, where low preference scores trigger a retry mechanism with specific feedback about potential issues like schema violations, operator misuse, or unclear query intent. This could help prevent problematic queries from reaching the database while providing targeted improvements for subsequent attempts. This further enables future work on preference optimization [\[36,](#page-13-9) [37\]](#page-13-10) for Function Calling. We present a sample of queries, ranking, and ranking rationales in Table 9.

| Model                       | Weighted Rank Score | Ranked 1st (%) |
|-----------------------------|---------------------|----------------|
| Gemini 1.5 Pro              | 17170               | 20.6%          |
| GPT-4o mini                 | 16545               | 29.0%          |
| GPT-4o                      | 15535               | 19.7%          |
| Command R+                  | 11845               | 8.7%           |
| Claude 3.5 Sonnet           | 11605               | 4.5%           |
| Gemini 2.0 Flash (exp)      | 11490               | 10.0%          |
| Llama 3.1 8B Instruct Turbo | 8305                | 4.2%           |
| Command R7B                 | 8255                | 3.2%           |

Table 5: Preference Ranking results of 8 LLM generated database queries on the DBGorilla benchmark.

## 5 Ablation Studies

Our main experiments highlight the performance of different LLMs at querying databases with Function Calling using our proposed tool definition and query operators. We additionally present a series of ablation studies to assess how various experimental factors and emerging schools of thought on Compound AI System design influence performance. We explore the impact of requiring a rationale for each tool call, enabling parallel tool calls, using structured output formats rather than Function Calling, and distributing queries across multiple per-collection tools instead of a single unified tool. Shown in Table 6, we find minimal performance variance across these ablations.

## 5.1 Tool Rationale

We begin by introducing a required rationale argument to our database querying tool. This achieves an Exact Match score of 73.2% with 96.8% collection routing accuracy. While the addition of rationales enhances human interpretability for system debugging, its potential benefit for LLM response parsing remains untested. An illustrative example demonstrates how rationales can reveal model misconceptions. When processing the query "How many different types of exhibit highlights are featured in each museum, grouped by museum name?", we observed:

Ground truth: Museums, TextAggregation(exhibitHighlights:COUNT), GroupBy(museumName)

Predicted: Museums, TextAggregation(exhibitHighlights:TYPE), GroupBy(museumName)

| Experiment Type                        | Exact Match Score | Collection Routing Accuracy |  |
|----------------------------------------|-------------------|-----------------------------|--|
| Original                               | 71.8%             | 96.5%                       |  |
| Original + Tool Rationale              | 73.2%             | 96.8%                       |  |
| Original + Parallel Tool Calls Enabled | 71.2%             | 95.9%                       |  |
| One Tool per Collection                | 72.3%             | 96.8%                       |  |
| Structured Generation                  | 72.8%             | 97.1%                       |  |

Table 6: Performance comparison across different ablation experiments with GPT-4o.

The model's rationale for this query was: To determine the variety of exhibit highlights featured in each museum, I will query the 'Museums' collection and perform a frequency analysis on the 'exhibitHighlights' property. This reveals an interesting misconception where it equates the TYPE aggregation as a frequency analysis operator. This insight suggests opportunities for improving the model's understanding of aggregation and other query operators.

#### 5.2 Parallel Function Calls

Another key aspect of Function Calling, illustrated in Figure 4, is the use of parallel tool calls. At each step, the LLM can be allowed to make simultaneous tool calls. In this ablation, we set parallel\_tool\_calls to be true and score each query based on the highest scoring tool called. This achieves a slightly lower Exact Match score of 71.2% with 95.9% collection routing accuracy. With parallel tool calls enabled, GPT-4o averages 1.21 calls per query. Upon inspecting the parallel tool calls, we find that this typically results in calls to complementary collections such as a query for the Restaurants collection and Reservations collection in the use case shown in Table 1. In our discussion section, we present a further analysis of how parallel function calls may impact Compound AI System design.

## 5.3 One Tool per Collection

We begin by decomposing our tool definition into a tool per collection. This has important implications for scaling given the token limit for tool descriptions imposed by the LLM providers tested in this study. Splitting collection across multiple tools provides a practical solution for systems with a large number of collections. In our experiments, the one tool per collection approach achieved an Exact Match score of 72.3% with 96.8% collection routing accuracy, demonstrating performance comparable to other implementations. We hypothesize that future Compound AI Systems may use the natural language command as input to only create tools for potentially useful collections, or transform multiple collections into a materialized view for Function Calling.

#### 5.4 Structured Generation

Our final ablation study challenges the potential bias in LLMs towards their specific Function Calling SDK. We replace Function Calling with Structured Generation using the ResponseOrFunctionCall model shown in Appendix A. Structured generation of function calls achieved a similar Exact Match score of 72.8% with a collection routing accuracy of 97.1%. The result suggest that models can effectively work with alternative interfaces for calling external functions. However, this experiment does not eliminate the potential bias towards the Function Calling SDK when processing longer sequences of function calls and their responses.

## 6 Discussion and Future Work

## 6.1 Database Gyms

A key advantage of synthetic database environments, or database gyms [\[22\]](#page-12-15), is the control offered over schema complexity, such as the number of collections and their property type distributions, as well as query patterns. Real-world databases often contain numerous collections with complex relationships, but publicly available datasets are limited or subject to confidentiality concerns. Synthetic data generation allows us to vary schema sizes, property types, naming conventions, and data relationships. This approach also supports benchmarking edge cases in data management that are challenging to obtain from real data, such as inconsistent naming schemes, partial null fields, or schema evolutions.

Our current setup uses three collections per use case and four properties per collection. Future versions of DBGorilla can introduce more collections, variance in property distribution per collection, and explicit relationships between collections, such as foreign keys. This would enable more sophisticated queries and enable testing for deeper reasoning about interrelated data. Furthermore, generating multiple commands per query-operator combination and introducing more abstract or multi-hop queries would better mimic real-world information needs. This expansion could also include iterative querying scenarios where the result of one query informs subsequent ones. Another opportunity to make the evaluation more robust is to generate multiple queries for each combination of query components, rather than a single query per combination. For instance, if a query involves a text filter and a boolean aggregation, we might produce multiple variations of the natural language command or scenario.

Another avenue for improving the DBGorilla dataset is broadening the function set itself [\[38\]](#page-13-11), extending beyond database querying to incorporate tools such as web search, data visualization, and external analytics platforms. In such a setting, the LLM would need to select among multiple specialized tools based on user intent, possibly orchestrating dependencies between tools (e.g., retrieving data from a database and then creating a chart). This raises fresh design and optimization questions, including how to reliably route requests, how to handle partial results or errors, and how best to refine queries.

#### 6.2 Querying Databases with Compound AI Systems

Recent efforts such as Reflexion prompting [\[33\]](#page-13-6), DSPy Assertions [\[34\]](#page-13-7), SPADE [\[35\]](#page-13-8), and Network of Networks [\[39\]](#page-13-12) show how LLMs can automatically refine problematic outputs through self-correction steps. Applying similar ideas to database querying could enable an iterative process wherein queries are revised based on validation or user feedback. Recent work has explored more systematic approaches to developing and optimizing LLM pipelines [\[40\]](#page-13-13), such as DSPy which introduces a programming model that abstracts LLM pipelines as text transformation graphs with declarative modules that can be automatically optimized [\[41,](#page-13-14) [42\]](#page-13-15). Approaches such as MIPRO [\[43\]](#page-13-16) or AvaTaR [\[44\]](#page-13-17) could further optimize prompt design and function definitions by contrasting successful and unsuccessful samples, ensuring models learn to manage tokens effectively for large-scale schemas.

## 7 Conclusion

This work demonstrates that Function Calling provides an effective and generalizable interface for enabling natural language database access. Through comprehensive evaluation of 8 LLMs across 5 model families, we show that leading models can achieve high accuracy in translating natural language to structured database operations, with Claude 3.5 Sonnet reaching an Exact Match score of 74.3% and GPT-4o achieving 71.8%. Our analysis reveals particular strengths in boolean operations across all models, suggesting a promising direction for optimizing database schemas around boolean properties. The DBGorilla benchmark, with its synthetic schema generation and comprehensive query evaluation framework, provides a foundation for future research in this area. As database systems continue to evolve toward natural language interfaces, Function Calling provides a promising foundation for bridging the gap between human intent and database operations.

## 8 Acknowledgements

We thank Matei Zaharia, Jared Quincy Davis, and the organizers of the Compound AI Systems workshop. We additionally thank Shishir G. Patil, Joseph E. Gonzalez, and the organizers of Sky Camp. For helpful conversations, we thank Liana Patel, Omar Khattab, Krista Opsahl-Ong, Arnav Singhvi, Isaac Miller, Thomas Ahle, Herumb Shandilya, Charlie Cheng-Jie Ji, Sarah Wooders, Charles Packer, Shirley Wu, Devin Petersohn, Augustas Skaburskas, Sebastian Neira Farriol, John Trengrove, Sebastian Witalec, JP Hwang, and Jonathan Tuite.

## <span id="page-11-0"></span>References

- [1] Matei Zaharia, Omar Khattab, Lingjiao Chen, Jared Quincy Davis, Heather Miller, Chris Potts, James Zou, Michael Carbin, Jonathan Frankle, Naveen Rao, and Ali Ghodsi. The shift from models to compound ai systems. <https://bair.berkeley.edu/blog/2024/02/18/compound-ai-systems/>, 2024.
- <span id="page-11-1"></span>[2] Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, and Yuan Cao. React: Synergizing reasoning and acting in language models. *arXiv preprint arXiv:2210.03629*, 2023.
- <span id="page-11-2"></span>[3] Shishir G. Patil, Tianjun Zhang, Xin Wang, and Joseph E. Gonzalez. Gorilla: Large language model connected with massive apis. *arXiv preprint arXiv:2305.15334*, 2023.
- <span id="page-11-3"></span>[4] OpenAI. Function calling in the chat completions api. [https://platform.openai.com/docs/guides/](https://platform.openai.com/docs/guides/function-calling) [function-calling](https://platform.openai.com/docs/guides/function-calling). Accessed: January 3, 2025.
- <span id="page-11-4"></span>[5] Fangyu Lei, Yujie Zhu, Wanjun Zhu, Qian Yin, Yicheng Yin, Jiawei Yin, Yusen Zhuang, Bowen Qin, Victor Zhong, Xuandong Yin, et al. Spider 2.0: Evaluating language models on real-world enterprise text-to-sql workflows. *arXiv preprint arXiv:2411.07763*, 2024.
- <span id="page-11-5"></span>[6] Shirley Wu, Shiyu Zhao, Michihiro Yasunaga, Kexin Huang, Kaidi Cao, Qian Huang, Vassilis N. Ioannidis, Karthik Subbian, James Zou, and Jure Leskovec. Stark: Benchmarking llm retrieval on textual and relational knowledge bases. *arXiv preprint arXiv:2404.13207*, 2024.

- <span id="page-12-0"></span>[7] Sparql query language. <https://www.w3.org/TR/sparql11-query/>, 2013.
- <span id="page-12-1"></span>[8] Liana Patel, Siddharth Jha, Parth Asawa, Melissa Pan, Carlos Guestrin, and Matei Zaharia. Semantic operators: A declarative model for rich, ai-based analytics over text data. *arXiv preprint arXiv:2407.11418*, 2024.
- <span id="page-12-2"></span>[9] Asim Biswal, Liana Patel, Siddarth Jha, Amog Kamsetty, Shu Liu, Joseph E. Gonzalez, Carlos Guestrin, and Matei Zaharia. Text2sql is not enough: Unifying ai and databases with tag. *arXiv preprint arXiv:2408.14717*, 2024.
- <span id="page-12-3"></span>[10] Shicheng Liu, Jialiang Xu, Wesley Tjangnaka, Sina J. Semnani, Chen Jie Yu, and Monica S. Lam. Suql: Conversational search over structured and unstructured data with large language models. *arXiv preprint arXiv:2311.09818*, 2024.
- <span id="page-12-4"></span>[11] Fanjia Yan, Huanzhi Mao, Charlie Cheng-Jie Ji, Tianjun Zhang, Shishir G. Patil, Ion Stoica, and Joseph E. Gonzalez. Berkeley function calling leaderboard. [https://gorilla.cs.berkeley.edu/blogs/8\\_berkeley\\_](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html) [function\\_calling\\_leaderboard.html](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html), 2024.
- <span id="page-12-5"></span>[12] Tal Ridnik, Dedy Kredo, and Itamar Friedman. Code generation with alphacodium: From prompt engineering to flow engineering. *arXiv preprint arXiv:2401.08500*, 2024.
- <span id="page-12-6"></span>[13] Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-augmented generation for knowledge-intensive nlp tasks. In H. Larochelle, M. Ranzato, R. Hadsell, M.F. Balcan, and H. Lin, editors, *Advances in Neural Information Processing Systems*, volume 33, pages 9459–9474. Curran Associates, Inc., 2020.
- <span id="page-12-7"></span>[14] Reiichiro Nakano, Jacob Hilton, Suchir Balaji, Jeff Wu, Long Ouyang, Christina Kim, Christopher Hesse, Shantanu Jain, Vineet Kosaraju, William Saunders, Xu Jiang, Karl Cobbe, Tyna Eloundou, Gretchen Krueger, Kevin Button, Matthew Knight, Benjamin Chess, and John Schulman. Webgpt: Browser-assisted question-answering with human feedback. *arXiv preprint arXiv:2112.09332*, 2022.
- <span id="page-12-8"></span>[15] Weinan Zhang, Junwei Liao, Ning Li, and Kounianhua Du. Agentic information retrieval. *arXiv preprint arXiv:2410.09713*, 2024.
- <span id="page-12-9"></span>[16] Zijin Hong, Zheng Yuan, Qinggang Zhang, Hao Chen, Junnan Dong, Feiran Huang, and Xiao Huang. Nextgeneration database interfaces: A survey of llm-based text-to-sql. *arXiv preprint arXiv:2406.08426*, 2024.
- <span id="page-12-10"></span>[17] Victor Zhong, Caiming Xiong, and Richard Socher. Seq2sql: Generating structured queries from natural language using reinforcement learning. *arXiv preprint arXiv:1709.00103*, 2017.
- <span id="page-12-11"></span>[18] Tao Yu, Rui Zhang, Kai Yang, Michihiro Yasunaga, Dongxu Wang, Zifan Li, James Ma, Irene Li, Qingning Yao, Shanelle Roman, Zilin Zhang, and Dragomir Radev. Spider: A large-scale human-labeled dataset for complex and cross-domain semantic parsing and text-to-sql task. In *Proceedings of the 2018 Conference on Empirical Methods in Natural Language Processing*, pages 3911–3921. Association for Computational Linguistics, 2018.
- <span id="page-12-12"></span>[19] Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, Bailin Wang, Bowen Qin, Ruiying Geng, Nan Huo, et al. Can llm already serve as a database interface? a big bench for large-scale database grounded text-to-sqls. *Advances in Neural Information Processing Systems*, 36, 2024.
- <span id="page-12-13"></span>[20] Matei Zaharia, Ali Ghodsi, Reynold Xin, and Michael Armbrust. Lakehouse: A new generation of open platforms that unify data warehousing and advanced analytics. In *11th Conference on Innovative Data Systems Research, CIDR 2021, Virtual Event, January 11-15, 2021, Online Proceedings*. www.cidrdb.org, 2021.
- <span id="page-12-14"></span>[21] Bob van Luijt and Micha Verhagen. Bringing semantic knowledge graph technology to your data. *IEEE Software*, 37(2):89–94, 2020.
- <span id="page-12-15"></span>[22] Wan Shen Lim, Matthew Butrovich, William Zhang, Andrew Crotty, Lin Ma, Peijing Xu, Johannes Gehrke, and Andrew Pavlo. Database gyms. *Conference on Innovative Data Systems Research*.
- <span id="page-12-16"></span>[23] OpenAI and Josh Achiam et al. Gpt-4 technical report. *arXiv preprint arXiv:2303.08774*, 2024.
- <span id="page-12-17"></span>[24] Gemini Team Google. Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. *arXiv preprint arXiv:2403.05530*, 2024.
- <span id="page-12-18"></span>[25] Claude 3.5 sonnet. <https://www.anthropic.com/news/claude-3-5-sonnet>, 2024.
- <span id="page-12-19"></span>[26] The command r model (details and applications). <https://docs.cohere.com/v2/docs/command-r>, 2024.

- <span id="page-13-0"></span>[27] AI@Meta. Llama 3 model card, Accessed July 2024.
- <span id="page-13-1"></span>[28] Brandon T. Willard and Rémi Louf. Efficient guided generation for large language models. *arXiv preprint arXiv:2307.09702*, 2023.
- <span id="page-13-2"></span>[29] Zhi Rui Tam, Cheng-Kuang Wu, Yi-Lin Tsai, Chieh-Yen Lin, Hung yi Lee, and Yun-Nung Chen. Let me speak freely? a study on the impact of format restrictions on performance of large language models. *arXiv preprint arXiv:2408.02442*, 2024.
- <span id="page-13-3"></span>[30] Connor Shorten, Charles Pierse, Thomas Benjamin Smith, Erika Cardenas, Akanksha Sharma, John Trengrove, and Bob van Luijt. Structuredrag: Json response formatting with large language models. *arXiv preprint arXiv:2408.11061*, 2024.
- <span id="page-13-4"></span>[31] Yizhong Wang, Yeganeh Kordi, Swaroop Mishra, Alisa Liu, Noah A. Smith, Daniel Khashabi, and Hannaneh Hajishirzi. Self-instruct: Aligning language models with self-generated instructions. In Anna Rogers, Jordan Boyd-Graber, and Naoaki Okazaki, editors, *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pages 13484–13508, Toronto, Canada, July 2023. Association for Computational Linguistics.
- <span id="page-13-5"></span>[32] Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. Reflexion: Language agents with verbal reinforcement learning. *arXiv preprint arXiv:2303.11366*, 2023.
- <span id="page-13-6"></span>[33] Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, and Shunyu Yao. Reflexion: Language agents with verbal reinforcement learning. *arXiv preprint arXiv:2303.11366*, 2023.
- <span id="page-13-7"></span>[34] Arnav Singhvi, Manish Shetty, Shangyin Tan, Christopher Potts, Koushik Sen, Matei Zaharia, and Omar Khattab. Dspy assertions: Computational constraints for self-refining language model pipelines. *arXiv preprint arXiv:2312.13382*, 2024.
- <span id="page-13-8"></span>[35] Shreya Shankar, Haotian Li, Parth Asawa, Madelon Hulsebos, Yiming Lin, J. D. Zamfirescu-Pereira, Harrison Chase, Will Fu-Hinthorn, Aditya G. Parameswaran, and Eugene Wu. Spade: Synthesizing data quality assertions for large language model pipelines. *arXiv preprint arXiv:2401.03038*, 2024.
- <span id="page-13-9"></span>[36] Rafael Rafailov, Archit Sharma, Eric Mitchell, Christopher D Manning, Stefano Ermon, and Chelsea Finn. Direct preference optimization: Your language model is secretly a reward model. *Advances in Neural Information Processing Systems*, 36, 2024.
- <span id="page-13-10"></span>[37] Karel D'Oosterlinck, Winnie Xu, Chris Develder, Thomas Demeester, Amanpreet Singh, Christopher Potts, Douwe Kiela, and Shikib Mehri. Anchored preference optimization and contrastive revisions: Addressing underspecification in alignment. *arXiv preprint arXiv:2408.06266*, 2024.
- <span id="page-13-11"></span>[38] Shishir G. Patil, Tianjun Zhang, Vivian Fang, Noppapon C., Roy Huang, Aaron Hao, Martin Casado, Joseph E. Gonzalez, Raluca Ada Popa, and Ion Stoica. GoEX: Perspectives and designs towards a runtime for autonomous llm applications. *arXiv preprint arXiv:2404.06921*, 2024.
- <span id="page-13-12"></span>[39] Jared Quincy Davis, Boris Hanin, Lingjiao Chen, Peter Bailis, Ion Stoica, and Matei Zaharia. Networks of networks: Complexity class principles applied to compound ai systems design. *arXiv preprint arXiv:2407.16831*, 2024.
- <span id="page-13-13"></span>[40] Ion Stoica, Matei Zaharia, Joseph Gonzalez, Ken Goldberg, Koushik Sen, Hao Zhang, Anastasios Angelopoulos, Shishir G. Patil, Lingjiao Chen, Wei-Lin Chiang, and Jared Q. Davis. Specifications: The missing link to making the development of llm systems an engineering discipline. *arXiv preprint arXiv:2412.05299*, 2024.
- <span id="page-13-14"></span>[41] Omar Khattab, Keshav Santhanam, Xiang Lisa Li, David Hall, Percy Liang, Christopher Potts, and Matei Zaharia. Demonstrate-search-predict: Composing retrieval and language models for knowledge-intensive NLP. *arXiv preprint arXiv:2212.14024*, 2022.
- <span id="page-13-15"></span>[42] Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna Moazam, Heather Miller, Matei Zaharia, and Christopher Potts. Dspy: Compiling declarative language model calls into self-improving pipelines. *arXiv preprint arXiv:2310.03714*, 2023.
- <span id="page-13-16"></span>[43] Krista Opsahl-Ong, Michael J Ryan, Josh Purtell, David Broman, Christopher Potts, Matei Zaharia, and Omar Khattab. Optimizing instructions and demonstrations for multi-stage language model programs. *arXiv preprint arXiv:2406.11695*, 2024.
- <span id="page-13-17"></span>[44] Shirley Wu, Shiyu Zhao, Qian Huang, Kexin Huang, Michihiro Yasunaga, Kaidi Cao, Vassilis N. Ioannidis,

Karthik Subbian, Jure Leskovec, and James Zou. Avatar: Optimizing llm agents for tool usage via contrastive reasoning. *arXiv preprint arXiv:2406.11200*, 2024.

## A Primary Tool Schema Tested

The OpenAI interface for defining tools to be used with Function Calling contains a string-valued type of the tool and a JSON-valued [function]. The nested function has a string-valued name of the function, another string-valued description of what the tool does, a list of strings-valued required arguments signaling which of the parameters are required for the tool call and finally, another nested JSON-valued parameters for controlling the tool. The nested parameters further have a string-valued type of the argument such as string, integer, or boolean, followed by a JSON-valued properties.

```
1 query_database_tool = {
2 "type" : " function " ,
3 " function " : {
4 "name": "query_database" ,
5 " description " : f"Query a database with an optional search query or optional filters or aggregations on the
        results .\ n\nIMPORTANT! Please be mindful of the available query APIs you can use such as search queries ,
        filters , aggregations , and groupby!\n\ nAvailable collections in this database :\ n{ collections_description }" ,
6 "parameters" : {
7 "type" : " object " ,
8 " properties " : {
9 "collection_name" : {
10 "type" : " string " ,
11 " description " : "The collection to query. " ,
12 "enum": collections_list
13 },
14 "search_query" : {
15 "type" : " string " ,
16 " description " : "A search query to return objects from a search index. "
17 },
18 " integer_property_filter " : {
19 "type" : " object " ,
20 " description " : " Filter numeric properties using comparison operators . " ,
21 " properties " : {
22 "property_name": { "type" : " string " },
23 " operator " : { "type" : " string " , "enum": ["=", "<", ">", "<=", ">="] },
24 "value" : { "type" : "number" }
25 }
26 },
27 " text_property_filter " : {
28 "type" : " object " ,
29 " description " : " Filter text properties using equality or LIKE operators" ,
30 " properties " : {
31 "property_name": { "type" : " string " },
32 " operator " : { "type" : " string " , "enum": ["=", "LIKE"] },
33 "value" : { "type" : " string " }
34 }
35 },
36 " boolean_property_filter " : {
37 "type" : " object " ,
38 " description " : " Filter boolean properties using equality operators " ,
39 " properties " : {
40 "property_name": { "type" : " string " },
41 " operator " : { "type" : " string " , "enum": ["=", "!="] },
42 "value" : { "type" : "boolean" }
43 }
44 },
45 " integer_property_aggregation " : {
46 "type" : " object " ,
47 " description " : "Aggregate numeric properties using statistical functions " ,
48 " properties " : {
49 "property_name": { "type" : " string " },
50 "metrics " : {
51 "type" : " string " ,
52 "enum": ["COUNT", "TYPE", "MIN", "MAX", "MEAN", "MEDIAN", "MODE", "SUM"]
53 }
54 }
```

```
55 },
56 " text_property_aggregation " : {
57 "type" : " object " ,
58 " description " : "Aggregate text properties using frequency analysis " ,
59 " properties " : {
60 "property_name": { "type" : " string " },
61 "metrics " : {
62 "type" : " string " ,
63 "enum": ["COUNT", "TYPE", "TOP_OCCURRENCES"]
64 },
65 " top_occurrences_limit " : { "type" : " integer " }
66 }
67 },
68 " boolean_property_aggregation " : {
69 "type" : " object " ,
70 " description " : "Aggregate boolean properties using statistical functions " ,
71 " properties " : {
72 "property_name": { "type" : " string " },
73 "metrics " : {
74 "type" : " string " ,
75 "enum": [
76 "COUNT",
77 "TYPE",
78 "TOTAL_TRUE",
79 "TOTAL_FALSE",
80 "PERCENTAGE_TRUE",
81 "PERCENTAGE_FALSE"
82 ]
83 }
84 }
85 },
86 "groupby_property": {
87 "type" : " string " ,
88 " description " : "Group the results by a property . "
89 }
90 },
91 " required " : ["collection_name"]
92 }
93 }
94 }
```

```
1 class ToolArguments(BaseModel):
2 collection_name : str
3 search_query: Optional[ str ] = None
4 integer_property_filter : Optional[ IntPropertyFilter ] = None
5 text_property_filter : Optional[ TextPropertyFilter ] = None
6 boolean_property_filter : Optional[ BooleanPropertyFilter ] = None
7 integer_property_aggregation : Optional[IntAggregation ] = None
8 text_property_aggregation : Optional[TextAggregation] = None
9 boolean_property_aggregation : Optional[BooleanAggregation] = None
10 groupby_property: Optional[ str ] = None
11
12 class ToolCall(BaseModel):
13 function_name: str
14 arguments: ToolArguments
15
16 class ResponseOrToolCall(BaseModel):
17 tool_rationale : Optional[ str ] = Field (
18 default =None,
19 description ="A rationale regarding whether tool calls are needed."
20 )
21 use_tools : bool
22 response : Optional[ str ] = None
23 tool_calls : Optional[ List [ToolCall ]] = None
```

## B Additional Query Visualization

We present a visualization to helper readers further understand the synthetic database schemas and use cases. Table 1 illustrates the 3 collections created in the synthetic Restaurant use case. Each collection contains 4 properties, 2 text, 1 numeric, and 1 boolean. Table 5 further visualizes examples of queries grouped by whether they use text, integer, boolean, or no aggregations. This visualization tool helps overcome the challenge of manually inspecting schemas, a current challenge for inspecting these datasets with CSVs.

| Home                                                                                                                                                                                                              |                  | Dataset Visualizer<br>Q Search Queries                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|                                                                                                                                                                                                                   |                  | Query 1 of 315                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Restaurants<br>Healthcare<br>Courses                                                                                                                                                                              | Travel<br>Art    | <b>Query Details</b><br>Edit Query<br>+ Query Builder                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Restaurants<br>This schema focuses on enabling users to discover restaurants based on a comprehensive profile. With semantic search, users can find restaurants by<br>cuisine, ambiance, or special features.     | $\sim$           | Natural Language Query<br>Find restaurants with a cozy ambiance and Italian cuisine, where the average rating is at least 4, count how many<br>such restaurants there are, and group them by whether they are currently open or not.                                                                                                                                                                                                                                                                                                                                                        |
| name<br>The name of the restaurant.                                                                                                                                                                               | string           | Query APIs Utilized<br>Collection: Restaurants<br>Search Query: Find restaurants with a cozy ambiance and Italian cuisine                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| description<br>A detailed description and summary of the restaurant, including cuisine type and ambiance.<br>averageRating<br>The average rating score out of 5 for the restaurant                                | string<br>number | Integer Filter: averageRating $\ge 4$<br>Integer Aggregation: COUNT of averageRating<br>Group By: openNow                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| openNow<br>A flag indicating whether the restaurant is currently open                                                                                                                                             | boolean          | Query Validation<br>LLM-as-Judge Query Assessment: Valid<br>The generated query uses the expected operators correctly. It starts with a 'search_query' to find restaurants with specific attributes                                                                                                                                                                                                                                                                                                                                                                                         |
| enus Menus<br>This schema assists in linking dining experiences with specific restaurants through their menus. Rich search features allow customers to find dishes<br>tailored to dietary needs and price points. | $\sim$           | ('cozy ambiance' and 'Italian cuisine'). The 'integer_property_filter' applies a condition on 'averageRating $\geq$ 4', matching the expected<br>operator. It uses 'integer_property_aggregation' with COUNT on 'averageRating' to determine the number of such restaurants, aligning<br>with the aggregation requirement. Finally, it groups the results by the 'openNow' status with 'groupby_property', which is in line with the<br>expected operators. All expected operators are present and used logically, with no missing or incorrect operators.<br><b>Query Execution Result</b> |
| menuitem<br>The name of the menu item.                                                                                                                                                                            | string           | Grouped aggregation results:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| itemDescription<br>A detailed description of the menu item, including ingredients and preparation style.                                                                                                          | string           | $Group: openNow = true$<br>Property: averageRating<br>count: 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| price<br>The price of the menu item.                                                                                                                                                                              | number           | Group count: 5                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| isVegetarian<br>A flag to indicate if the menu item is vegetarian.                                                                                                                                                | boolean          |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |

Figure 6: Visualization tool for manually inspecting synthetic query quality and results.

![](_page_18_Figure_2.jpeg)

Figure 7: An illustration of natural language commands translated to Function Calling arguments for our proposed tool definition. Natural language command to Function Calling examples are further separated by simple, requiring a single argument, intermediate, requiring two arguments, and complex, requiring three or more arguments.

| Text Property Aggregations                                                                                                                                                                                  | Integer Property Aggregations                                                                                                                              | Boolean Property Aggregations                                                                                                                                     | No Aggregations                                                                                                                                                          |
|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Find all Italian restaurants with a<br>cozy ambiance and an average rat-<br>ing of 3.5 or below. Group them<br>by whether they are open, and ag-<br>gregate the most common words in<br>their descriptions. | What is the average price of sea-<br>sonal specialty menu items under<br>$$20$ , grouped by whether they are<br>vegetarian or not?                         | What are the most highly-rated<br>vegan-friendly brunch spots that are<br>currently open, and can you provide<br>a breakdown of these spots by cui-<br>sine type? | What romantic dining locations have<br>an average rating greater than $4.5$ ,<br>and can you group them by whether<br>they are currently open?                           |
| Find restaurants with a romantic din-<br>ner setting and outdoor seating that<br>have an average rating greater than 4.<br>Aggregate the top 5 most mentioned<br>cuisines.                                  | What is the average price of vegetar-<br>ian healthy salads offered by differ-<br>ent restaurants?                                                         | How many romantic restaurants<br>with a relaxing atmosphere are cur-<br>rently open and have an average rat-<br>ing of at least 4?                                | What are some affordable vegetarian<br>dishes that cost less than $$15?$                                                                                                 |
| Find live jazz music restaurants that<br>are currently open, suitable for a ro-<br>mantic dinner. Group by cuisine<br>style.                                                                                | What is the average rating of open<br>restaurants with a cozy ambiance,<br>categorized by cuisine type?                                                    | Find romantic Italian restaurants<br>that offer organic options and group<br>them by average rating. Show how<br>many are currently open.                         | Find cozy Italian restaurants that are<br>currently open and group the results<br>by their average rating.                                                               |
| How many romantic Italian restau-<br>rants with vegan options and a rating<br>above 4.5 are there? Show examples<br>of their descriptions.                                                                  | What is the average party size for<br>reservations with more than 5 peo-<br>ple, grouped by whether the reserva-<br>tion is confirmed?                     | What percentage of restaurants<br>known for romantic dining settings<br>are currently open, and how are they<br>grouped by average ratings?                       | Show me open restaurants with a ro-<br>mantic ambiance and group the re-<br>sults by their average rating.                                                               |
| How many restaurants are currently<br>open and known for a cozy atmo-<br>sphere, categorized by cuisine?                                                                                                    | What is the average price of afford-<br>able vegetarian meals with healthy<br>ingredients, grouped by restaurant?                                          | How many Italian restaurants are<br>currently open?                                                                                                               | Find trendy restaurants with a cozy<br>atmosphere and group them by<br>whether they are currently open or<br>not.                                                        |
| What are some cozy restaurants that<br>are currently open? Summarize the<br>most common types of cuisine.                                                                                                   | What is the highest average rat-<br>ing among currently open restau-<br>rants with excellent ambiance and<br>food quality, whose names start with<br>'La'? | Find Asian restaurants with a cozy<br>ambiance. Determine what percent-<br>age are open, and group open restau-<br>rants by average rating.                       | Find restaurants characterized by a<br>cozy ambiance suitable for an inti-<br>mate dinner, that are currently open<br>and have an average rating of at least<br>4 stars. |
| Can you find cozy Italian restaurants<br>with a romantic ambiance and group<br>them by their average rating? Pro-<br>vide a summary of common features<br>for open restaurants.                             | What is the average price of all the<br>menu items available across the var-<br>ious restaurants in the system?                                            | How many reservations are there<br>with a party size of 5 or more?<br>Count how many are confirmed and<br>group by party size.                                    | Find all restaurants that have the<br>word 'Cafe' in their name.                                                                                                         |
| Which restaurants have a cozy at-<br>mosphere and a romantic ambiance?<br>Aggregate the top 5 cuisines overall.                                                                                             | Find clinics that provide orthopedic<br>care and are rated above 4.0 in sat-<br>isfaction. Group results by whether<br>they are accepting new patients.    | For each name under which reserva-<br>tions are made, what percentage are<br>confirmed?                                                                           | Show me all the vegetarian items on<br>the menu and group them by their<br>name.                                                                                         |
| How many unique menu items are<br>there in the restaurant menus priced<br>under \$20?                                                                                                                       |                                                                                                                                                            |                                                                                                                                                                   | Which vegetarian menu items are<br>available, and can you group them<br>by their price?                                                                                  |

Table 7: A visualization of query samples from the Restaurant synthetic use case categorized by aggregation type.

| C | Performance Analysis by API Component |  |  |  |  |  |
|---|---------------------------------------|--|--|--|--|--|
|---|---------------------------------------|--|--|--|--|--|

| Component Type       | GPT-4o | GPT-4o-mini | Claude 3.5 Sonnet | Command R+ | Command R7B |
|----------------------|--------|-------------|-------------------|------------|-------------|
| Search Queries       | 78.75% | 79.38%      | 83.75%            | 50.00%     | 38.75%      |
| Integer Filters      | 71.25% | 86.25%      | 73.75%            | 68.75%     | 35.00%      |
| Text Filters         | 37.50% | 42.50%      | 46.25%            | 38.75%     | 31.25%      |
| Boolean Filters      | 87.50% | 86.25%      | 87.50%            | 65.00%     | 42.50%      |
| Integer Aggregations | 73.75% | 72.50%      | 73.75%            | 60.00%     | 45.00%      |
| Text Aggregations    | 70.00% | 66.25%      | 73.75%            | 52.50%     | 35.00%      |
| Boolean Aggregations | 62.50% | 72.50%      | 66.25%            | 63.75%     | 31.25%      |
| GroupBy Operations   | 71.70% | 75.47%      | 72.96%            | 53.46%     | 31.45%      |

Table 8: Performance Analysis by API Component (GPT-4o, GPT-4o-mini, Claude 3.5 Sonnet, Command R+, Command R7B)

| Component Type       | Gemini 1.5 Pro | Gemini 2.0 Flash | Llama 3.1 8B |
|----------------------|----------------|------------------|--------------|
| Search Queries       | 81.25%         | 41.88%           | 52.50%       |
| Integer Filters      | 82.50%         | 46.25%           | 26.25%       |
| Text Filters         | 41.25%         | 25.00%           | 27.50%       |
| Boolean Filters      | 86.25%         | 42.50%           | 32.50%       |
| Integer Aggregations | 77.50%         | 36.25%           | 32.50%       |
| Text Aggregations    | 70.00%         | 37.50%           | 30.00%       |
| Boolean Aggregations | 52.50%         | 31.25%           | 30.00%       |
| GroupBy Operations   | 72.33%         | 35.85%           | 23.27%       |

Table 9: Performance Analysis by API Component (Gemini 1.5 Pro, Gemini 2.0 Flash, Llama 3.1 8B)

## D Preference Ranking Explanations

| Query                                                                                                                       | Ranking Explanation                                                                                                                                  | Ranking                                                                                                                                                                                                    |
|-----------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Which<br>museums<br>that<br>are<br>specifically open today can I<br>visit?                                                  | All models except Llama-3.1-8B-Instruct-Turbo<br>correctly used boolean filter. Llama model mis<br>takenly used integer filter.                      | gpt-4o-mini (1), command-r<br>plus (2), gpt-4o (3), gemini<br>1.5-pro (4), gemini-2.0-flash<br>exp (5),<br>command-r7b (6),<br>claude-3-5-sonnet (7), Llama<br>3.1-8B-Instruct-Turbo (8)                   |
| What is the average entry<br>fee for museums grouped by<br>whether they are open today<br>or not?                           | Most models correctly grouped by openTo<br>day property and calculated mean entry fee.<br>Command-r7b introduced unnecessary boolean<br>aggregation. | gpt-4o-mini (1), command-r<br>plus (1), gpt-4o (1), gemini<br>1.5-pro (1), gemini-2.0-flash<br>exp<br>(1),<br>claude-3-5-sonnet<br>(1),<br>Llama-3.1-8B-Instruct<br>Turbo (2), command-r7b (3)             |
| What is the total market valu<br>ation of all art pieces that are<br>currently on display in the mu<br>seum?                | Models needed to filter displayed pieces and<br>sum valuations. Some models failed to perform<br>correct aggregation or used wrong filter type.      | gpt-4o-mini (1), gpt-4o (1),<br>gemini-1.5-pro (1), gemini<br>2.0-flash-exp (1), claude-3-5-<br>sonnet (1), command-r7b (5),<br>command-r-plus (6), Llama<br>3.1-8B-Instruct-Turbo (7)                     |
| How many different types of<br>exhibit highlights are featured<br>in each museum, grouped by<br>museum name?                | Required grouping by museum name and count<br>ing distinct types.<br>Best models used both<br>groupby_property and TYPE metric.                      | gpt-4o (1), gemini-2.0-flash<br>exp (2), claude-3-5-sonnet (3),<br>command-r-plus (4), gpt-4o<br>mini (5), command-r7b (6),<br>gemini-1.5-pro<br>(7),<br>Llama<br>3.1-8B-Instruct-Turbo (7)                |
| What are the top 3 most fre<br>quently mentioned exhibits<br>among all museums, and how<br>many museums are open to<br>day? | Required both exhibit identification and open<br>museum counting. Some models missed count<br>ing open museums.                                      | gemini-2.0-flash-exp (1), gpt<br>4o-mini (2), command-r-plus<br>(3), gpt-4o (3), gemini-1.5-<br>pro (3),<br>command-r7b (3),<br>claude-3-5-sonnet (3), Llama<br>3.1-8B-Instruct-Turbo (5)                  |
| What is the percentage of<br>exhibitions currently running<br>grouped by each exhibition ti<br>tle?                         | Required grouping by exhibitionTitle and calcu<br>lating PERCENTAGE_TRUE of currentlyRun<br>ning. Some models missed groupby_property.               | command-r-plus (1), gpt-4o<br>(2),<br>claude-3-5-sonnet<br>(3),<br>gpt-4o-mini<br>(4),<br>gemini<br>1.5-pro<br>(5),<br>Llama-3.1-8B<br>Instruct-Turbo (5), command<br>r7b (5), gemini-2.0-flash-exp<br>(5) |
| What percentage of exhibi<br>tions are currently open to the<br>public?                                                     | Required calculating percentage using boolean<br>property aggregation. Command-r-plus incor<br>rectly used boolean filter instead.                   | gpt-4o-mini (1), gpt-4o (1),<br>gemini-2.0-flash-exp<br>(1),<br>command-r7b (1), claude-3-5-<br>sonnet (1), command-r-plus<br>(6),<br>gemini-1.5-pro<br>(7),<br>Llama-3.1-8B-Instruct<br>Turbo (7)         |

Table 10: A detailed view at preference rankings and their explanations produced by the LLM-as-Judge ranker.

| Query                                                                                                                      | Ranking Explanation                                                                                                                           | Ranking                                                                                                                                                                                                        |
|----------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Which<br>museums<br>open<br>to<br>day have notable historical<br>exhibits and how are they<br>grouped by their entry fees? | Required filtering open museums with histori<br>cal exhibits and grouping by entry fees. Some<br>models missed grouping component.            | gpt-4o<br>(1),<br>gemini-1.5-pro<br>(2),<br>claude-3-5-sonnet<br>(3),<br>Llama-3.1-8B-Instruct<br>Turbo (4),<br>command-r-plus<br>(5),<br>command-r7b<br>(6),<br>gpt-4o-mini (7), gemini-2.0-<br>flash-exp (8) |
| Find all Italian restaurants<br>with a cozy ambiance and an<br>average rating of 3.5 or be<br>low                          | Required filtering restaurants, grouping by open<br>status, and aggregating common words. Some<br>models missed text aggregation or grouping. | gemini-1.5-pro (1), claude-3-<br>5-sonnet (2), Llama-3.1-8B<br>Instruct-Turbo (3), command<br>r7b (4), gpt-4o (5), command<br>r-plus (6), gemini-2.0-flash<br>exp (7), gpt-4o-mini (7)                         |
| How many doctors have more<br>than 10 years of experience,<br>and are currently practicing,<br>grouped by their expertise? | Required filtering doctors and grouping by ex<br>pertise with proper COUNT aggregation. Some<br>models missed COUNT configuration.            | gpt-4o<br>(1),<br>gemini-1.5-pro<br>(2),<br>gemini-2.0-flash-exp<br>(3),<br>command-r-plus<br>(4),<br>Llama-3.1-8B-Instruct<br>Turbo (5), claude-3-5-sonnet<br>(6),<br>command-r7b<br>(7),<br>gpt-4o-mini (8)  |