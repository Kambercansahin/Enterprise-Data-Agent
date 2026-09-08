from src.graphs.state import GraphState

from typing import Any,Dict
#for sql query and take the tables
from src.tools.db_tools import execute_sql_query,get_schema_summary
from src.graphs.chains.sql_grader_chain import sql_chain

def sql(state:GraphState) -> Dict[str,Any]:
    print("---SQL NODE---")
    schema = get_schema_summary()
    question = state["question"]

    sql_ch = sql_chain.invoke({
        "schema":schema,
        "question":question
    })

    if not sql_ch.is_feasible or not sql_ch.query:
        return {
            "sql_data": f"Veritabanı ile yanıtlanamadı: {sql_ch.explanation}",
            "sql_query": None
        }

    try:
        sql_data = execute_sql_query(sql_ch.query)
    except Exception as e:
        sql_data = f"Sorgu çalıştırma hatası: {str(e)}"


    return {"question":question,"sql_data":sql_data,"sql_query":sql_ch.query}

