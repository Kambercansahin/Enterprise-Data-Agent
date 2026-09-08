from dotenv import load_dotenv

from src.graphs.project_models import get_models
from pydantic import BaseModel,Field
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate

#for testing
from generation_chain import generation_chain
from src.tools.db_tools import get_schema_summary,execute_sql_query
from sql_grader_chain import  sql_chain

load_dotenv()




llm = get_models(temperature=0.0)
class Hallucination(BaseModel):
    """Binary Score for Hallucination present in generated answer """
    binary_score:Literal["yes","no"] = Field(
        ...,
        description="'yes' if the generation contains hallucinations (unsupported facts/claims), 'no' if it is strictly grounded in the context."
    )

structure_llm = llm.with_structured_output(Hallucination)

system_prompt = """
You are a strict Enterprise Quality & Fact-Checking Auditor.
Your single mission is to detect HALLUCINATIONS (fabricated facts, invented metrics, or unsupported claims) in the assistant's response.

You must rigorously compare the ASSISTANT GENERATION against the PROVIDED VERIFIED CONTEXT.

SCORING CRITERIA:
- 'yes' (HALLUCINATION DETECTED):
  * The response contains numbers, revenue figures, dates, or sales counts not present in the context.
  * The response invents product names, categories, or customer sentiments/quotes that do not exist in the context.
  * The response makes factual claims that cannot be traced directly back to the provided context.

- 'no' (NO HALLUCINATION / FULLY GROUNDED):
  * Every fact, entity, metric, and finding in the response is strictly supported by the provided context.
  * Translating or summarizing Portuguese customer reviews into Turkish is completely acceptable as long as facts remain true to the source.
  * Truthfully stating that data is missing or that no complaints were found is fully grounded and valid.

STRICT RULE:
Provide strictly adhering output with a binary score: 'yes' (hallucinated) or 'no' (grounded).

--- PROVIDED VERIFIED CONTEXT ---
{context}
"""
hallucination_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","Assistant Generation:{generation}")
    ]
)

hallucination_chain = hallucination_prompt | structure_llm

if __name__ == "__main__":
    question = "En çok satış yapan 10 ürün hangisi?"

    sql_sch = get_schema_summary()
    sql_ch = sql_chain.invoke({
        "schema":sql_sch,
        "question":question
    })

    sql_data = execute_sql_query(sql_ch.query)

    generation = generation_chain.invoke({
        "question":question,
        "rag_data":None,
        "sql_data": sql_data,
        "reasoning_steps": None,
        "web_data": None})

    context_test = str(sql_data)
    hallucination = hallucination_chain.invoke({
        "context":context_test,
        "generation":"En çok satan ürünümüz Apple iPhone 15 Pro Max olup toplam 2.500 adet satmıştır."
    })
    print(hallucination)