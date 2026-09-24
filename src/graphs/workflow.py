from src.graphs.chains.rag_grader_chain import rag_grader_chain
from src.graphs.chains.sql_grader_chain import sql_chain
from src.graphs.node_constant import GENERATE,DECOMPOSE,WEBSEARCH,OUT_OF_SCOPE,SQL_NODE,RAG_NODE

from src.graphs.state import GraphState

#ALL NODES
from src.graphs.nodes.rag_node import rag
from src.graphs.nodes.sql_node import sql
from src.graphs.nodes.decompose_node import decompose
from src.graphs.nodes.generations_node import generation
from src.graphs.nodes.out_of_scope_node import out_of_scope
from src.graphs.nodes.web_search_node import websearch
#chains
from src.graphs.chains.router_chain import router_chain
from src.graphs.chains.hallucination_chains import hallucination_chain
from src.graphs.chains.answer_chain import ans_chain
#import END and StateGraph
from langgraph.graph import END,StateGraph
from typing import Dict,Any

#tools
from src.tools.db_tools import execute_sql_query,get_schema_summary
from src.tools.qrant_tools import search_reviews_in_qdrant

from langgraph.checkpoint.memory import MemorySaver

from dotenv import load_dotenv

load_dotenv()

#created work_flow
work_flow = StateGraph(GraphState)

def fallback(state: GraphState) -> Dict[str, Any]:
  print("--- FALLBACK NODE (GIVE UP) ---")
  return {
      "generation": "__INSUFFICIENT_DATA__",
      "sql_query": None,
      "sql_data": None,
      "rag_data": None,
      "web_data": None,
  }
#added all nodes
work_flow.add_node(GENERATE,generation)
work_flow.add_node(DECOMPOSE,decompose)
work_flow.add_node(WEBSEARCH,websearch)
work_flow.add_node(SQL_NODE,sql)
work_flow.add_node(RAG_NODE,rag)
work_flow.add_node(OUT_OF_SCOPE,out_of_scope)
work_flow.add_node("fallback", fallback)

def decided_to_router(state:GraphState) ->str:
    question = state["question"]
    raw_messages = state.get("messages") or []
    recent_history = raw_messages[-4:] if len(raw_messages) > 4 else raw_messages
    #router decision

    decision = router_chain.invoke({
        "question":question,
        "chat_history": recent_history
    })

    #if router choose the SQL
    if decision.datasource == "SQL":
        return SQL_NODE
    # if router choose the RAG
    elif decision.datasource == "RAG":
        return RAG_NODE
    # if router choose the MultiStep
    elif decision.datasource == "MultiStep":
        return DECOMPOSE
    # if router choose the websearch
    elif decision.datasource == "websearch":
        return  WEBSEARCH
    else:
        return OUT_OF_SCOPE

def grader_hallucination_and_answer(state:GraphState)->str:
    question = state["question"]
    generation_answer = state.get("generation")
    sql_data = state.get("sql_data")
    rag_data = state.get("rag_data")
    web_data = state.get("web_data")
    reasoning_steps = state.get("reasoning_steps")
    retry_count = state.get("retry_count", 0)
    #if retry count gh 2 return give up
    if retry_count >= 2:
        print(f"--- !!! RETRY COUNT ({retry_count})  !!! ---")
        return "give_up"

    #If the assistant already indicates that no data was found or that it is outside the scope of authorization, then the loop will be triggered
    if "No Data" in generation_answer or len(generation_answer.strip()) < 20:
        return "useful"

    #take the all data with get , now we have data or None so we can add all
    all_context = []

    #if sql data is not None we are adding
    if sql_data and str(sql_data).strip() not in ["No Data", "None","No SQL data found."]:
        all_context.append(f"SQL DATA:{sql_data}")

    # if rag data is not None we are adding
    if rag_data and str(rag_data).strip() not in ["No Data", "None"]:
        all_context.append(f"RAG DATA:{rag_data}")

    # if web  data is not None we are adding
    if web_data and str(web_data).strip() not in ["No Data", "None"]:
        all_context.append(f"WEB DATA:{web_data}")

    # if reasoning steps  is not None we are adding
    if reasoning_steps and str(reasoning_steps).strip() not in ["No Data", "None"]:
        all_context.append(f"Reasoning Steps:{reasoning_steps}")

    raw_messages = state.get("messages") or []
    recent_history = raw_messages[-4:] if len(raw_messages) > 4 else raw_messages
    if raw_messages:
        recent_history_texts = [
            f"{m.type.upper()}: {m.content[:200]}" for m in raw_messages[-3:]
        ]
        all_context.append(
            "RECENT CONVERSATION CONTEXT:\n" + "\n".join(recent_history_texts)
        )
    merged_context = "\n\n".join(all_context) if all_context else "No context available."

    hallucination = hallucination_chain.invoke({
        "generation":generation_answer,
        "context":merged_context
    })

    print(f"--Hallucination Control (binary_score: {hallucination.binary_score})--")
    if hallucination.binary_score == "no":
        print("--Decision:Not Hallucination--")
        answer = ans_chain.invoke({
            "question": question,
            "generation": generation_answer,
            "chat_history": recent_history
        })
        print(f"--Check the Answer (binary_score: {answer.binary_score})--")
        if answer.binary_score == "yes":
            print("--Decision:Answer is Useful---")
            return "useful"
        else:
            print("--Decision:Answer is not useful")
            return "not_useful"
    else:
        print("--Decision:Hallucination is Yes---")
        return "not_supported"

work_flow.set_conditional_entry_point(
    decided_to_router,
    {
        SQL_NODE:SQL_NODE,
        WEBSEARCH:WEBSEARCH,
        RAG_NODE:RAG_NODE,
        DECOMPOSE:DECOMPOSE,
        OUT_OF_SCOPE:OUT_OF_SCOPE
    }
    )

work_flow.add_edge(DECOMPOSE,GENERATE)
work_flow.add_edge(OUT_OF_SCOPE,END)
work_flow.add_edge(WEBSEARCH,GENERATE)
work_flow.add_edge(SQL_NODE,GENERATE)
work_flow.add_edge(RAG_NODE,GENERATE)

work_flow.add_edge("fallback", END)

work_flow.add_conditional_edges(
    GENERATE,
    grader_hallucination_and_answer,
    {
        "not_supported":GENERATE,
        "useful": END,
        "not_useful" : WEBSEARCH,
        "give_up": "fallback"

    }
)
checkpointer = MemorySaver()

graph =work_flow.compile(checkpointer=checkpointer)
graph.get_graph().draw_mermaid_png(output_file_path="graph.png")