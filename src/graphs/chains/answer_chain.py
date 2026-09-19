from dotenv import load_dotenv

from src.graphs.project_models import get_models
from pydantic import BaseModel,Field

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate

#for testing
from src.tools.db_tools import get_schema_summary,execute_sql_query
from src.graphs.chains.sql_grader_chain import sql_chain

from src.graphs.chains.generation_chain import generation_chain

load_dotenv()

class Answer(BaseModel):
    """Evaluates whether the generated response is sufficiently complete, useful, and directly resolves the user's intent."""
    binary_score:Literal["yes","no"] = Field(
        ...,
        description="'yes' if the answer helpfully addresses the core business question based on available data, 'no' if it is evasive, completely irrelevant, or empty"
    )

llm = get_models()
structure_llm = llm.with_structured_output(Answer)

system_prompt = """ROLE:
You are an Enterprise Business Intelligence Response Quality Auditor.
Your responsibility is to evaluate whether the assistant's generated answer USEFULLY and DIRECTLY addresses the user's business inquiry.

EVALUATION CRITERIA:
1. Intent Fulfillment: Does the answer address what the user asked (e.g., metrics, rankings, trends, customer sentiments) rather than evading it?
2. Multi-Channel / MultiStep Synthesis: If the user asked a multi-part question (e.g., top products + customer feedback) and the assistant provided the ranking/metrics along with the available feedback or truthfully noted data availability, this IS CONSIDERED USEFUL AND COMPLETE.
3. Reasonable Completeness: The assistant does NOT need exhaustive commentary on every single entity if internal records had limited reviews. Providing the high-level ranking and the synthesized qualitative insights fully counts as useful.
4. Security & Rejections: If the response correctly explains that a command cannot be executed due to security/scope boundaries (e.g., DROP TABLE), this IS USEFUL ('yes').

SCORING:
- 'yes': The response provides a helpful, analytical, and grounded answer or valid metric summary that serves the user's business intent.
- 'no': The response is completely irrelevant, hallucinated, blank, an unhelpful error message, or totally fails to touch the user's topic.

STRICT RULE:
Output strictly adhering to the schema with 'yes' or 'no'.
"""
answer_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","User Question:{question} Assistant Generation:{generation}")
    ]
)
ans_chain = answer_prompt | structure_llm


if __name__ == "__main__":
    question = "En az satış yapan 3 ürün hangisidir?"

    sql_scm = get_schema_summary()
    sql_ch = sql_chain.invoke({
        "question":question,
        "schema":sql_scm
    })

    sql_data = execute_sql_query(sql_ch.query)
    print("Üretilen SQL:", sql_ch.query)
    print("SQL Sonucu  :", sql_data)
    generation_test = generation_chain.invoke({
        "question":question,
        "rag_data":None,
        "sql_data": sql_data,
        "reasoning_steps": None,
        "web_data": None})

    answer = ans_chain.invoke({
        "question":question,
        "generation":generation_test.content
    })

    print(generation_test.content)
    print(answer)
