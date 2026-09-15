from typing import Any,Dict

from src.graphs.chains.generation_chain import generation_chain
from src.graphs.state import GraphState
#for last messages
from langchain_core.messages import HumanMessage, AIMessage


def generation(state:GraphState) ->Dict[str,Any]:
    print("---GENERATIONS NODE---")
    question = state["question"]
    #if sql_data ,rag_data,web_data or reasoning_steps are None system throws an error
    sql_data = state.get("sql_data") or "No Data"
    rag_data = state.get("rag_data") or "No Data"
    web_data = state.get("web_data") or "No Data"
    reasoning_steps = state.get("reasoning_steps") or "No Data"

    current_retry = state.get("retry_count",0)

    all_messages = state.get("messages") or []


    recent_history = all_messages[-4:] if len(all_messages) > 4 else all_messages

    #created generation
    result_generation = generation_chain.invoke({
        "question":question,
        "chat_history": recent_history,
        "sql_data":sql_data,
        "rag_data":rag_data,
        "web_data":web_data,
        "reasoning_steps":reasoning_steps
    })

    return {"generation": result_generation,"retry_count": current_retry + 1,
            "messages": [
            HumanMessage(content=question),
            AIMessage(content=result_generation)
        ]
    }