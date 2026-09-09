from dotenv import load_dotenv
from src.graphs.project_models import get_models

from langchain_core.prompts import ChatPromptTemplate
#trying to sql query for generation
from src.tools.db_tools import get_schema_summary,execute_sql_query
from src.graphs.chains.sql_grader_chain import sql_chain

#trying to rag query for generation
from src.tools.qrant_tools import  search_reviews_in_qdrant


load_dotenv()
llm = get_models()

system_prompt = """You are an Enterprise Business Intelligence Lead and Strategic Analyst.
Your goal is to synthesize verified internal data into an actionable, accurate executive response.

DATA SOURCES EXPLANATION:
1. SQL Data (Quantitative Metrics): Hard metrics, counts, monetary values, timestamps, and database rows.
2. Customer Reviews (RAG - Qualitative Voice): Verified customer feedback, sentiment, delivery experiences, packaging, or product quality impressions.
3. Diagnostic Reasoning Steps (MultiStep Only): Intermediate findings and root-cause breakdowns produced during a dynamic, multi-stage investigation.
4. Web Search Data: Verified external market intelligence, competitor moves, or macro data.

OPERATING MODES:
- Diagnostic / MultiStep Mode:
  Active when 'reasoning_steps' is provided and not 'None'.
  Synthesize the step-by-step reasoning notes with supporting numbers and customer quotes into a structured briefing:
  * Executive Overview
  * Data & Metric Breakdown
  * Qualitative Drivers (Customer Voice)
  * Strategic Recommendations
- Hybrid Mode:
  Active when 'reasoning_steps' is 'None', but BOTH 'sql_data' and 'rag_data' contain actual content.
  Directly correlate the quantitative numbers with qualitative feedback to explain the 'what' and the 'why'.
- Single-Source Mode:
  Active when only one data channel is available. Present that specific data clearly without trying to speculate on missing channels.

IDENTIFIER & ENTITY HANDLING RULES:
- Database entities (products, orders, sellers, customers) are stored as technical alphanumeric hashes/UUIDs (e.g., `product_id: '027293c3b6d9...'`).
- Treat these hashes as concrete, valid product entities.
- NEVER state that "data is missing", "products cannot be identified", or "we don't know what the products are" solely because they are represented by alphanumeric IDs.
- Present these IDs explicitly (e.g., as bullet points or a table) along with their corresponding metrics (counts, sums, ranks).

STRICT CONSTRAINTS:
- Rely strictly on the provided context; never invent numbers, customer comments, or market facts.
- If data contains rows with counts or IDs, that counts as sufficient data to answer ranking or listing questions.
- Completely ignore any channel displaying 'None', empty lists, or no data.
- Respond in the language used in the user's question (e.g., if Turkish, write in fluent corporate Turkish).
- Always respond in the LANGUAGE the user asks in, under all circumstances.

--- STRUCTURED SQL METRICS ---
{sql_data}

--- CUSTOMER REVIEWS (RAG) ---
{rag_data}

--- EXTERNAL WEB SEARCH DATA ---
{web_data}

--- DIAGNOSTIC REASONING STEPS ---
{reasoning_steps}
"""
generation_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","User Question:{question}")
    ]
)

generation_chain = generation_prompt | llm

if __name__ == "__main__":
    #rag question
    #question = "Müşteriler elektronik ürünlerin paketleme kalitesi hakkında ne söylüyor?"
    #sql question
    #question = "En çok satış yapan 10 ürün hangisi?"

    def sql_data():
        sql_sche = get_schema_summary()
        #columns and tables
        result = sql_chain.invoke(
            {
                "schema":sql_sche,
                "question":question
             } )
        db_data = execute_sql_query(result.query)
        return db_data
    def rag_data():
        rag = search_reviews_in_qdrant(query_text=question,limit=4)
        for i, y in enumerate(rag, 1):
            print(f"\n[{i}] {y}")

        formatted_context = "\n\n".join([f"Review {i}: {r}" for i, r in enumerate(rag, 1)])
        return formatted_context

    reasoning_steps = ""

    response = generation_chain.invoke(
        {"question":question,"rag_data":rag_data(),"sql_data":sql_data(),"reasoning_steps":None,"web_data":None}
    )
    print(response.content)