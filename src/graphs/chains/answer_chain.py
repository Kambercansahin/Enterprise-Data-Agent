from dotenv import load_dotenv

from src.graphs.project_models import get_models
from pydantic import BaseModel, Field

from typing import Literal
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

load_dotenv()

class Answer(BaseModel):
    """Evaluates whether the generated response is sufficiently complete, useful, and directly resolves the user's intent."""
    binary_score: Literal["yes", "no"] = Field(
        ...,
        description="'yes' if the answer helpfully addresses the core business question based on available data, 'no' if it is evasive, completely irrelevant, or empty."
    )

llm = get_models()
structure_llm = llm.with_structured_output(Answer)

system_prompt = """ROLE:
You are an Enterprise Business Intelligence Response Quality Auditor.
Your responsibility is to evaluate whether the assistant's generated answer USEFULLY and DIRECTLY addresses the user's business inquiry.

MULTI-TURN CONVERSATION & FOLLOW-UP CONTEXT:
- The user may ask follow-up questions referencing previous entities (e.g. "bu satıcılardan puanı en kötü olanın cirosu", "birinci sıradakinin satışları").
- You MUST evaluate the response in light of the provided 'chat_history'. If the assistant correctly answers the follow-up question for an entity identified from the chat history, score it as 'yes'.

EVALUATION CRITERIA:
1. Intent Fulfillment: Does the answer address what the user asked (e.g., metrics, rankings, trends, customer sentiments) rather than evading it?
2. Scalar & Aggregate Metrics: If the user asked for total revenue, turnover, or counts, providing the exact numerical value (e.g., "79.90 BRL") directly and fully satisfies the inquiry ('yes').
3. Multi-Channel / MultiStep Synthesis: If the user asked a multi-part question and the assistant provided the ranking/metrics along with available feedback or noted boundaries, this counts as useful ('yes').
4. Security & Rejections: If the response correctly explains that a command cannot be executed due to boundaries, this IS USEFUL ('yes').

SCORING:
- 'yes': The response provides a helpful, analytical, or valid metric summary that serves the user's business intent.
- 'no': The response is completely irrelevant, blank, an unhelpful error message, or totally fails to address the user's inquiry.

STRICT RULE:
Output strictly adhering to the schema with 'yes' or 'no'.
"""

answer_prompt = ChatPromptTemplate(
    [
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("user", "User Question: {question}\nAssistant Generation: {generation}")
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
