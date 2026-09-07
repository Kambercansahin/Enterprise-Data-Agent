from dotenv import load_dotenv
from pydantic import BaseModel,Field
from typing import Literal

from src.graphs.project_models import get_models
from langchain_core.prompts import ChatPromptTemplate
from src.tools.qrant_tools import  search_reviews_in_qdrant
load_dotenv()

class RagGrader(BaseModel):
    """You will check whether the answer retrieved from the context is consistent with the user's question."""

    datasource:Literal["yes","no"]=Field(
        ...,
        description="Return 'yes' if the reviews provide relevant context to the question, otherwise 'no'."
    )

system_prompt = """You are a specialized Relevance Grader evaluating customer reviews and feedback for an enterprise e-commerce platform.
Your task is to determine whether retrieved customer reviews provide valid, meaningful, and contextual grounding to answer the user's question.

EVALUATION CRITERIA:
1. Binary Scoring ('yes' or 'no'):
   - 'yes': Grade as 'yes' if ANY of the retrieved reviews touch upon the topic (e.g., product condition, electronics, packaging, delivery box, delays, satisfaction/complaints).
   - 'no': Grade as 'no' ONLY if the reviews discuss completely unrelated items/topics or provide zero signal about the question.

2. Critical Rules:
   - The user query is in Turkish/English, while reviews are in Portuguese. Translate and map concepts semantically (e.g., 'paketleme kalitesi' -> 'embalagem', 'veio quebrado', 'caixa', 'proteção').
   - Even partial or indirect evidence is sufficient for 'yes'. Do not require all reviews to match.

Reviews Context:
{context}
"""

rag_grader_prompt = ChatPromptTemplate(
    [
        ("system",system_prompt),
        ("user","User Question:{question}")
    ]
)

llm = get_models()
structure_llm = llm.with_structured_output(RagGrader)

rag_grader_chain = rag_grader_prompt | structure_llm

if __name__ == "__main__":
    question= "En çok satış yapan 10 ürün hangisi?"
    review = search_reviews_in_qdrant(query_text=question,limit=4)
    for i, y in enumerate(review, 1):
        print(f"\n[{i}] {y}")

    formatted_context = "\n\n".join([f"Review {i}: {r}" for i, r in enumerate(review, 1)])

    response = rag_grader_chain.invoke({"question":question,"context":review} )

    print(response)
    print(review)
