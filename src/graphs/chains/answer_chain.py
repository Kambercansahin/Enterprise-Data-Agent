from dotenv import load_dotenv

from src.graphs.project_models import get_models
from pydantic import BaseModel,Field

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate

#for testing
from src.tools.db_tools import get_schema_summary,execute_sql_query
from sql_grader_chain import sql_chain

from generation_chain import generation_chain

load_dotenv()

class Answer(BaseModel):
    """Evaluates whether the generated response is sufficiently complete, useful, and directly resolves the user's intent."""
    binary_score:Literal["yes","no"] = Field(
        ...,
        description="'yes' if the answer completely and helpfully resolves the inquiry, 'no' if it is incomplete, evasive, or insufficient."
    )

llm = get_models()
structure_llm = llm.with_structured_output(Answer)

system_prompt = """ROLE:
You are an Enterprise Business Intelligence Response Quality Auditor.
Your sole responsibility is to evaluate whether the assistant's generated answer FULLY and USEFULLY resolves the user's specific inquiry.

EVALUATION CRITERIA:
1. Intent Fulfillment: Does the answer directly solve what the user is truly asking for, rather than talking around the issue?
2. Completeness: Are all key constraints addressed? (e.g., if asked for "top 3 products with root causes of complaints", does it deliver both the products AND the complaints, or did it omit one half?)
3. Actionability & Sufficiency: Is the insight sufficient for decision-making? If the assistant gives a non-answer, gives up easily ("bilgi bulunamadı" when context had data), or leaves the query fundamentally unresolved, it fails.

SCORING:
- 'yes': The answer is a direct, helpful, and reasonably complete resolution to the user's business question.
- 'no': The answer is partial, evasive, fails to address major parts of the question, or leaves the inquiry unresolved.

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
