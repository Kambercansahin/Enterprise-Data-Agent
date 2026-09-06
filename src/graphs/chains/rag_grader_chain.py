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
        description="You will return 'yes' if there is a logical relationship between the user's question and the document, or 'no' if there is none."
    )

system_prompt = """You are a specialized Relevance Grader evaluating customer reviews and feedback for an enterprise e-commerce platform.
Your task is to determine whether a retrieved customer review from the vector database (Qdrant) provides valid, meaningful, and contextual grounding to answer the user's question.

EVALUATION CRITERIA:
1. Binary Scoring ('yes' or 'no'):
   - 'yes': Grade as 'yes' if the retrieved review is semantically or directly related to the user's inquiry, covering topics such as product quality, categories, delivery timelines, transit damage, packaging condition, returns, or general customer sentiment/complaints.
   - 'no': Grade as 'no' if the review discusses an entirely unrelated product or issue, contains only coincidental keyword overlaps, or fails to provide useful information relevant to the user's intent.

2. Critical Rules:
   - If the user's input is casual chit-chat, greetings (e.g., 'hello', 'hi', 'how are you'), or completely off-topic, you MUST strictly grade it as 'no', regardless of the retrieved review content.
   - The user query may be in English, Turkish, or other languages, while reviews are primarily in Portuguese; focus strictly on semantic intent and thematic alignment rather than language differences.
   - The document does NOT need to be a complete answer by itself; if it provides partial evidence or relevant context, grade it as 'yes'.

Provide your output strictly adhering to the specified schema with a binary score and a brief rationale.

Context of RAG:{context}
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
    question= "İyi akşamlar, yarın hava nasıl olacak?"
    review = search_reviews_in_qdrant(query_text=question,limit=4)
    for i, y in enumerate(review, 1):
        print(f"\n[{i}] {y}")

    response = rag_grader_chain.invoke({"question":question,"context":review} )

    print(response)
