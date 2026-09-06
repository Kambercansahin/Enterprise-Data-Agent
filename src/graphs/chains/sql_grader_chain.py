from dotenv import load_dotenv

from src.graphs.project_models import get_models
from langchain_core.prompts import ChatPromptTemplate
from src.tools.db_tools import get_schema_summary,execute_sql_query
from pydantic import  BaseModel,Field
from typing import Optional,Literal

load_dotenv()

class Sql(BaseModel):
    """SQL query generated for PostgreSQL and its explanation"""
    is_feasible: bool = Field(
        description="True if the user's question can be resolved using the tables and columns in the schema; otherwise, False."
    )
    query:str = Field(

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
   - If YES: Set `is_feasible = True` and generate an optimized PostgreSQL SELECT query (do not forget to include a LIMIT clause).
   - If NO (e.g., the question is about weather, stock markets, general small talk, or fields missing from the schema):
     Set `is_feasible = False`, leave `query = None`, and write in the `explanation` field that the question is unrelated to or cannot be answered by the database.
2. Under no circumstances should you force-guess or attempt to retrieve data from unrelated tables!
3. Write a valid PostgreSQL SELECT query using ONLY the table and column names provided in the schema.
4. Always append a reasonable LIMIT clause to prevent fetching excessively large datasets (default: LIMIT 10).
5. JOIN tables using the correct foreign key relationships (e.g., order_id between orders and order_items).
6. Generate SELECT queries ONLY; never write statements that modify data.
7. Write the EXPLANATION, in the LANGUAGE the user uses to ask the question.
"""

sql_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user", "DataBase Schema:{schema}" "Question:{question}")
    ]
)

llm = get_models(temperature=0.0)

structure_llm = llm.with_structured_output(Sql)

sql_chain = sql_prompt | structure_llm

if __name__ == "__main__":
    print("--- 1. ŞEMA ÇEKİLİYOR ---")
    current_schema = get_schema_summary()

    question = "adıyaman hava durumu?"

    result = sql_chain.invoke({
        "schema": current_schema,
        "question": question
    })

    print(f"\nÜretilen SQL:\n{result.query}")
    print(f"\nAçıklama:\n{result.explanation}")

    try:
        db_data = execute_sql_query(result.query)
        print("\nVeritabanından Dönen Gerçek Veri:")
        for satir in db_data:
            print(satir)
    except Exception as e:
        print(f"Hata oluştu: {e}")