from dotenv import load_dotenv
from typing import Optional

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from src.graphs.project_models import get_models

#for trying
from src.tools.db_tools import get_schema_summary, execute_sql_query
from sql_grader_chain import sql_chain
from src.tools.qrant_tools import search_reviews_in_qdrant

load_dotenv()
llm = get_models(temperature=0.0)


class MultiStepDecompose(BaseModel):
    """Decompose complex queries into interdependent execution targets."""

    sql_question: Optional[str] = Field(
        default=None,
        description="A natural language question in Turkish/English for the database. STRICTLY NO SQL SYNTAX OR CODE."
    )
    web_query: Optional[str] = Field(
        default=None,
        description="External search query. Can include '{{context}}'."
    )
    rag_query: Optional[str] = Field(
        default=None,
        description="Natural language search query for customer reviews. Must include '{{context}}' if dependent on SQL."
    )


structure_llm = llm.with_structured_output(MultiStepDecompose)

system_prompt = """You are a Dynamic Query Planner for an Enterprise BI Platform.
Analyze complex analytical user questions and decompose them into plain natural language sub-inquiries.

CRITICAL INSTRUCTION FOR 'sql_question':
- NEVER write SQL keywords (DO NOT use SELECT, FROM, WHERE, ORDER BY, JOIN).
- Write ONLY a plain conversational question asking for the metric.
- Correct: "En çok satılan ilk 3 ürün hangisidir?"
- WRONG: "SELECT product_name FROM products..."

CRITICAL INSTRUCTION FOR 'rag_query':
- If the review search targets entities that must first be found by the database (like top products), you MUST put '{{context}}' in the text.
- Correct: "{{context}} ürünleri hakkında müşteri memnuniyeti ve ana şikayetler nelerdir?"

CHANNELS:
1. 'sql_question': Natural language metric question for internal DB.
2. 'web_query': External market/benchmark search query.
3. 'rag_query': Customer review sentiment search with '{{context}}'.

Set unused channels strictly to None."""

decompose_prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("user", "Question: {question}")
])

decompose_chain = decompose_prompt | structure_llm

if __name__ == "__main__":
    question = "En çok satılan ilk 3 ürünün müşteri memnuniyeti ve yorumlardaki ana şikayetleri neler?"

    plan = decompose_chain.invoke({"question": question})
    print("SQL Alt Sorusu :", plan.sql_question)
    print("RAG Şablonu    :", plan.rag_query)
    print("Web Şablonu:",plan.web_query)
    schema = get_schema_summary()
    sql_res = sql_chain.invoke({"schema": schema, "question": plan.sql_question})

    if not sql_res.is_feasible or not sql_res.query:
        print(f"SQL üretilemedi: {sql_res.explanation}")
        exit()

    print("SQL:", sql_res.query)
    db_data = execute_sql_query(sql_res.query)
    print("SQL Sonucu:", db_data)

    context_str = str(db_data)

    if plan.rag_query:
        if "{context}" in plan.rag_query:
            rag_sorusu = plan.rag_query.replace("{context}", context_str)
        else:
            rag_sorusu = f"{context_str} {plan.rag_query}"

        print("\nRAG'e Gidecek Soru:", rag_sorusu)

        review = search_reviews_in_qdrant(query_text=rag_sorusu, limit=4)
        print("Bulunan Reviews:")
        for y in review:
            print("-", y)