from dotenv import load_dotenv

from src.graphs.project_models import get_models
from pydantic import BaseModel,Field
from typing import Literal
from langchain_core.prompts import ChatPromptTemplate

#for testing
from src.graphs.chains.generation_chain import generation_chain
from src.tools.db_tools import get_schema_summary,execute_sql_query
from src.graphs.chains.sql_grader_chain import  sql_chain

load_dotenv()




llm = get_models(temperature=0.0)
class Hallucination(BaseModel):
    """Binary Score for Hallucination present in generated answer """
    binary_score:Literal["yes","no"] = Field(
        ...,
        description="'yes' if the generation contains hallucinations (unsupported facts/claims), 'no' if it is strictly grounded in the context."
    )

structure_llm = llm.with_structured_output(Hallucination)

system_prompt = """You are an Enterprise Quality & Fact-Checking Auditor.
Your single mission is to detect SEVERE HALLUCINATIONS (fabricated metrics, invented entities, or factual contradictions) in the assistant's response.

You must compare the ASSISTANT GENERATION against the PROVIDED VERIFIED CONTEXT.

SCORING CRITERIA:
- 'yes' (HALLUCINATION DETECTED):
  * The response invents numeric metrics, percentages, revenue figures, or dates that directly contradict or have zero grounding in the context.
  * The response invents completely fabricated product IDs, category names, or entities not found in the context.
  * The response makes extreme factual claims contrary to what the data indicates.

- 'no' (NO HALLUCINATION / ACCEPTABLE):
  * Metrics, category names, IDs, and rankings match the provided SQL or Context.
  * Qualitative Summaries & Customer Sentiment: Translating, abstracting, summarizing, or synthesizing general customer experience/feedback (e.g. summarizing reviews from Portuguese/English into Turkish) is FULLY GROUNDED and MUST be scored 'no'.
  * Do NOT mark a response as hallucination merely because the exact phrasing or wording does not appear verbatim in the source reviews/data.
  * Grounded paraphrases, executive summaries, aggregations, and reasonable qualitative synthesis of customer reviews must be scored 'no'.
  * High-level executive synthesis, contextual explanations, connective sentences, and polite introductions/conclusions are NOT hallucinations.

PRIMARY PRINCIPLE:
Do NOT penalize natural language summarization, translation, or strategic synthesis as hallucination unless it invents conflicting numbers or fake entities.

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