from dotenv import load_dotenv

from src.graphs.project_models import get_models
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
from src.tools.db_tools import get_schema_summary,execute_sql_query
from pydantic import  BaseModel,Field
from typing import Optional,Literal

load_dotenv()

class Sql(BaseModel):
    """SQL query generated for PostgreSQL and its explanation"""
    is_feasible: bool = Field(
        description="True if the user's question can be resolved using the tables and columns in the schema; otherwise, False."
    )
    query:Optional[str] = Field(
        default=None,
        description="A single-line, valid PostgreSQL SELECT query to be executed on the database."
    )
    explanation: str = Field(
        description="A concise technical summary of how this query joins tables and columns."
    )

system_prompt = """
You are an expert PostgreSQL Data Engineer.
You will be provided with a database schema and a user's e-commerce-related question.

Your task:
1. Carefully inspect the schema: CAN the question be answered using the provided tables (orders, products, payments, customer locations, etc.)?
   - If YES: Set `is_feasible = True` and generate an optimized PostgreSQL SELECT query.
   - If NO (e.g., the question is about weather, stock markets, general small talk, or fields missing from the schema):
     Set `is_feasible = False`, leave `query = None`, and write in the `explanation` field that the question is unrelated to or cannot be answered by the database.
2. Under no circumstances should you force-guess or attempt to retrieve data from unrelated tables!
3. Write a valid PostgreSQL SELECT query using ONLY the table and column names provided in the schema.
4. Always append a reasonable LIMIT clause to prevent fetching excessively large datasets (default: LIMIT 10), unless an aggregate without grouping is computed.
5. SCHEMA RELATIONSHIPS & JOINS:
   - CRITICAL: 'seller_id' exists ONLY in 'order_items' (and 'sellers'). It DOES NOT exist in 'orders' or 'order_reviews'. 
   - Never write 'SELECT seller_id FROM order_reviews' or 'SELECT seller_id FROM orders'. You must always join 'order_items' to access 'seller_id'.
6. Generate SELECT queries ONLY; never write statements that modify data.
7. DATE/TIME HANDLING & SARGABILITY:
   - The database contains historical snapshot data. Never use `NOW()` or `CURRENT_DATE`.
   - For all date-based filtering and chronological analysis, ALWAYS use `orders.order_purchase_timestamp`.
   - NEVER use functions like `EXTRACT(YEAR FROM ...)` or `DATE_TRUNC(...)` in WHERE clauses because they bypass B-Tree indexes. Always use sargable range comparisons (e.g. `order_purchase_timestamp >= '2018-01-01' AND order_purchase_timestamp < '2019-01-01'`).
8. BUSINESS & REVENUE RULES:
   - When calculating revenue, sales turnover, or total amount sold, ALWAYS compute `SUM(oi.price)`. Do NOT add `freight_value` unless the user explicitly mentions shipping or delivery cost.
   - Completed orders must be filtered using `order_status = 'delivered'`.
9. Write the EXPLANATION in the LANGUAGE the user uses to ask the question.
10. AGGREGATION & UNIQUENESS:
    When counting entities from joined tables (e.g., counting orders, customers, or sellers), ALWAYS use `COUNT(DISTINCT column_id)` (e.g., `COUNT(DISTINCT o.order_id)`) to avoid duplicate counts caused by one-to-many relationships (like orders having multiple reviews or items).
11. MULTI-TURN & CONTEXTUAL REFERENCES:
    - If the user query is referential or requests a visualization (e.g. "can you visualize these", "graph this", "draw a chart of it", "make a table"):
      * It IS ALWAYS FEASIBLE (is_feasible = True).
      * Do NOT decline just because the user asked for a "graph" or "visualize".
      * Look at the immediately preceding turn in 'chat_history'. Identify the query and metrics that produced those records (e.g., top 3 ordered products: order_items joined with products, counting orders).
      * RE-GENERATE the exact same SQL SELECT query that yields those exact data rows so the downstream charting engine can render the graph.
    - TIE-BREAKING RULE (MANDATORY):
      If the user asks for a SINGLE entity from a previous ranking (e.g., "the worst one", "the best one", "the first one") and TWO OR MORE rows in that previous ranking are EXACTLY TIED on the referenced metric:
      * Do NOT set is_feasible = False just because the tie makes the choice ambiguous.
      * Apply this deterministic tie-breaking order, in sequence, until the tie is broken:
        1. Fewer supporting review/order rows first (e.g., ORDER BY COUNT(DISTINCT r.review_id) ASC) — an entity with fewer reviews reaching the same extreme score is considered more strongly representative of that extreme.
        2. Fewer total orders (COUNT(DISTINCT o.order_id) ASC).
        3. seller_id (or the relevant entity id) in ascending alphabetical order, as a final deterministic fallback.
      * Scope the new query to ONLY the tied entities from the previous turn (WHERE seller_id IN (...)) combined with the tie-breaker, so exactly one entity is selected.
      * In the `explanation` field, briefly state which tie-breaker was applied and why (e.g., "Sellers X, Y, Z were tied at score 1.0; selected X due to fewest reviews").
    - GROUP VISUALIZATION REFERENCES:
      If the user asks to visualize/graph a previous finding using a PLURAL reference (e.g., "these", "bunları", "onları") shortly after discussing a GROUP of entities from an earlier turn (e.g., a ranking of 3 sellers) and/or a follow-up metric computed for only ONE entity from that group (e.g., "the worst one's revenue was X"):
      * Interpret the plural reference as referring to the ENTIRE previously discussed group (all N entities), not just the single entity most recently mentioned.
      * Re-scope the query to compute the SAME metric just discussed (e.g., revenue) for ALL entities in that group, using WHERE seller_id IN (...) with all their IDs, so the resulting chart shows a meaningful comparison across the group.
      * STRICT PROHIBITION: NEVER generate a generic, unrelated ranking query (e.g., a fresh "top sellers by revenue" query unrelated to the conversation) as a fallback when a specific referenced group or entity already exists in chat_history. Doing so produces answers disconnected from the conversation and is considered a critical failure.
      * If, and only if, chat_history truly contains no concrete entity list or scalar result to reference, treat the request as a standalone new question and proceed normally.
      When regenerating a query for visualization (e.g. pie chart), you MUST use the EXACT SAME aggregation function and distinct clauses as the preceding turn (e.g. keep COUNT(DISTINCT order_id), do not switch to COUNT()).
12. FLOATING POINT FORMATTING:
    - When calculating average review scores with AVG(), ALWAYS wrap it with ROUND(..., 2) (e.g. ROUND(AVG(r.review_score), 2) AS average_review_score).
    - For revenue, turnover, or sums, use bare SUM(oi.price).
"""

sql_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        MessagesPlaceholder(variable_name="chat_history",optional=True),
        ("user", "DataBase Schema:{schema} Question:{question}")
    ]
)

llm = get_models(temperature=0.0)

structure_llm = llm.with_structured_output(Sql)

sql_chain = sql_prompt | structure_llm

if __name__ == "__main__":
    print("--- 1. ŞEMA ÇEKİLİYOR ---")
    current_schema = get_schema_summary()

    question = "En iyi 10 yorumu getir"

    result = sql_chain.invoke({
        "schema": current_schema,
        "question": question
    })
    print(f"Feasible:{result.is_feasible}")
    print(f"SQL:{result.query}")
    print(f"Açıklama:{result.explanation}")

    try:
        db_data = execute_sql_query(result.query)
        print("\nVeritabanından Dönen Gerçek Veri:")
        for satir in db_data:
            print(satir)
    except Exception as e:
        print(f"Hata oluştu: {e}")