from typing import Any,Dict

from src.graphs.chains.generation_chain import generation_chain
from src.graphs.state import GraphState


def generation(state:GraphState) ->Dict[str,Any]:
    print("---GENERATIONS NODE---")
    question = state["question"]
    #if sql_data ,rag_data,web_data or reasoning_steps are None system throws an error
    sql_data = state.get("sql_data")
    rag_data = state.get("rag_data")
    web_data = state.get("web_data")
    reasoning_steps = state.get("reasoning_steps")

    current_retry = state.get("retry_count",0)

    #created generation
    result_generation = generation_chain.invoke({
        "question":question,
        "sql_data":sql_data,
        "rag_data":rag_data,
        "web_data":web_data,
        "reasoning_steps":reasoning_steps
    })

    return {"generation":result_generation.content,"retry_count":current_retry +1}