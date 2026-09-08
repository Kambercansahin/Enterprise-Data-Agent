
from typing import Any,Dict
from src.graphs.state import GraphState
from src.graphs.chains.rag_grader_chain import rag_grader_chain

from src.tools.qrant_tools import search_reviews_in_qdrant

def rag(state:GraphState) -> Dict[str,Any]:
    print("---RAG NODE---")
    question =state["question"]

    rag_text = search_reviews_in_qdrant(query_text=question,limit=4)

    #if question is not in the qrant
    if not rag_text:
        return {"rag_data": None}

    for i, y in enumerate(rag_text, 1):
        print(f"\n[{i}] {y}")

    formatted_context = "\n\n".join([f"Review {i}: {r}" for i, r in enumerate(rag_text, 1)])

    response = rag_grader_chain.invoke({"question":question,"context":formatted_context} )

    if response.datasource == "yes":
        return {"rag_data":formatted_context}

    return {"rag_data":None}

