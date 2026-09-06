from pydantic import BaseModel,Field
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from src.graphs.project_models import  get_models

class Router(BaseModel):
    """Route a user query to most relevant datasource"""

    datasource:Literal["SQL","RAG","Hybrid","OutOfScope","websearch"] =Field(
        ...,
        description="Given a user choose to route it to 'SQL','RAG','Hybrid','Out of Scope','web search'"
    )

llm = get_models()
structure_llm = llm.with_structured_output(Router)

system_prompt ="""
You are an intent classification engine for an Enterprise E-Commerce Business Intelligence platform.
Analyze the user's input regardless of language (Turkish, English, Portuguese, etc.) and route it to the exact data source:

- SQL: Relational/structured e-commerce data lookups. Includes orders, sales volumes, total revenues, delivery dates, payment types, customer/seller locations, top-selling products, counts, sums, and database aggregations.
- RAG: Customer voice, subjective opinions, and qualitative feedback. Includes customer reviews, sentiment, product quality complaints, packaging issues, unboxing feedback, and delivery experience text stored in the vector database.
- Hybrid: Questions that require BOTH structured operational/sales metrics AND textual customer review analysis (e.g., "Which product category has the highest return/delay rate, and what are customers complaining about in their reviews?").
- websearch: External economic data, general e-commerce market trends, competitor benchmarks, or real-time public web information outside our internal database.
- OutOfScope: Casual greetings (hi, hello), chit-chat, weather queries, coding requests, general knowledge quizzes, poetry, or completely off-topic inputs unrelated to business and commerce.
"""


router_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","{question}")
    ]
)

router_chain = router_prompt | structure_llm

if __name__ == "__main__":
    response = router_chain.invoke(input={"question":"2026 yılında Brezilya e-ticaret pazarında Mercado Libre'nin güncel pazar payı ve kargo teslimat süreleri nedir?"})


    print(response)

