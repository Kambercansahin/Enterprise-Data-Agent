from pydantic import BaseModel,Field
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from src.graphs.project_models import  get_models

class Router(BaseModel):
    """Route a user query to most relevant datasource"""

    datasource:Literal["SQL","RAG","MultiStep","OutOfScope","websearch"] =Field(
        ...,
        description="Given a user choose to route it to 'SQL','RAG','MultiStep','OutOfScope','web search'"
    )

llm = get_models()
structure_llm = llm.with_structured_output(Router)

system_prompt ="""
You are an advanced Intent Routing Engine for an Enterprise E-Commerce Business Intelligence platform.
Analyze the user query regardless of language (Turkish, English, Portuguese) and route it to the single best execution pipeline:

1. SQL:
   - Queries answered purely with structured relational data.
   - Core scopes: Sales metrics, counts, order totals, revenues, top/bottom product rankings, delivery durations, payment methods, customer/seller locations.

2. RAG:
   - Queries answered purely with qualitative, unstructured customer reviews from the vector database (Qdrant).
   - Core scopes: Customer feedback, sentiment, packaging condition, complaints, product defects, or delivery experiences.


3. MultiStep:
   - Any query requiring more than one data source, sequential execution, or diagnostic root-cause analysis.
   - Covers:
     * Combined SQL + RAG queries (e.g., getting metrics first, then examining customer feedback).
     * Sequential queries where target entities must first be computed via SQL before searching reviews.
     * Diagnostic investigations ("Why did revenue drop in Q2?").


4. WebSearch:
   - External public web information, macroeconomic data, competitor market benchmarks, industry trends, or public regulatory information outside our internal databases.


5. OutOfScope:
   - Casual greetings, small talk, personal queries, programming questions, weather forecasts, or topics entirely unrelated to e-commerce and business data.
"""


router_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","{question}")
    ]
)

router_chain = router_prompt | structure_llm

if __name__ == "__main__":
    response = router_chain.invoke(input={"question":"Kullanıcılarımızın kargo paketleme ve hasarlı teslimat konusundaki temel geri bildirimleri neler ve e-ticaret lojistiğinde son dönemde uygulanan sürdürülebilir/patpat koruyucu ambalaj trendleri hakkında dış kaynaklarda hangi çözümler öneriliyor"})


    print(response)

