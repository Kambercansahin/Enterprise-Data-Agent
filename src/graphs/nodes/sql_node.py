from src.graphs.state import GraphState

from typing import Any,Dict
#for sql query and take the tables
from src.tools.db_tools import execute_sql_query,get_schema_summary
from src.graphs.chains.sql_grader_chain import sql_chain

def sql(state:GraphState) -> Dict[str,Any]:
    print("---SQL NODE---")
    schema = get_schema_summary()
    question = state["question"]

    raw_messages = state.get("messages") or []
    recent_history = (
        raw_messages[-4:] if len(raw_messages) > 4 else raw_messages
    )
    sql_ch = sql_chain.invoke({
        "schema":schema,
        "question":question,
        "chat_history":recent_history
    })
    print(f"DEBUG SQL QUERY: {sql_ch.query}")
    print(f"DEBUG SQL EXPLANATION: {sql_ch.explanation}")

    if not sql_ch.is_feasible or not sql_ch.query:
        return {
            "question": question,
            "sql_data": f"Veritabanı ile yanıtlanamadı: {sql_ch.explanation}",
            "sql_query": None,
            "rag_data": None,
            "web_data": None,
            "reasoning_steps": None
        }

    try:
        sql_data = execute_sql_query(sql_ch.query)
    except Exception as e:
        sql_data = f"Sorgu çalıştırma hatası: {str(e)}"

    print(f"DEBUG SQL DATA: {sql_data}")

    return {
        "question": question,
        "sql_data": sql_data,
        "sql_query": sql_ch.query,
        "rag_data": None,
        "web_data": None,
        "reasoning_steps": None
    }

