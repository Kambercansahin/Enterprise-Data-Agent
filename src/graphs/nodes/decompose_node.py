from typing import Any,Dict

from src.graphs.chains.sql_grader_chain import sql_chain
from src.graphs.state import GraphState
from src.graphs.chains.decompose_chain import decompose_chain

from src.tools.db_tools import get_schema_summary,execute_sql_query
from src.tools.qrant_tools import search_reviews_in_qdrant

from langchain_tavily import TavilySearch

# if router node chooses the multiStep

def decompose(state:GraphState) -> Dict[str,Any]:
    print("---DECOMPOSE NODE---- ")
    question = state["question"]

   #we are using for generations node
    sql_data = None
    sql_query=None
    rag_data = None
    web_data = None
    #for sql + rag or rag+web or sql+web
    context_pool = {}
    reasoning_logs = []

    decompose_c = decompose_chain.invoke({
        "question":question
    })

    if decompose_c.sql_question:
        #take the tables and columns
        sql_sch = get_schema_summary()

        #created sql
        sql_ch = sql_chain.invoke({
            "schema":sql_sch,
            "question":decompose_c.sql_question
        })

        if sql_ch.is_feasible and sql_ch.query:
            #take in the postgresql services
            try:
                sql_data = execute_sql_query(query=sql_ch.query)
                sql_query =sql_ch.query
                #for rag query
                context_pool["sql"] = str(sql_data)
                reasoning_logs.append(f"SQL Question ({decompose_c.sql_question}): {context_pool['sql']}")
            except Exception as e:
                sql_data = f"Sql data exception: {e}"
        else:
            sql_data = f"Sql query cannot created {sql_ch.explanation}"

    if decompose_c.rag_query:
        #rag query
        query_text = decompose_c.rag_query
        if "{context}" in decompose_c.rag_query and "sql" in context_pool:
            query_text = query_text.replace("{context}",context_pool["sql"])
        #if the model skips writing {context} in the prompt, we must append the SQL result to the query.
        elif "sql" in context_pool:
            query_text = f"{context_pool['sql']} {query_text}".strip()

        reviews = search_reviews_in_qdrant(query_text=query_text,limit=4)
        if reviews:
            formatted = "\n\n".join([f"Review {i}: {r}" for i, r in enumerate(reviews, 1)])
            rag_data = formatted
            context_pool["rag"] = formatted
            reasoning_logs.append(f"Customer feedback ({query_text}): {len(reviews)} .")

        #for web query
    if decompose_c.web_query:
        #take the tavily search only allowed websites
        search = TavilySearch(max_results=5,
                                     include_domains=["sikayetvar.com",
                                                      "webrazzi.com",
                                                      "donanimhaber.com",
                                                      "eksisozluk.com",
                                                      "bloomberght.com"
                                                      ])

        search_query = decompose_c.web_query
        if "{context}" in search_query:
            available_context = context_pool.get("rag") or context_pool.get("sql") or ""
            search_query = search_query.replace("{context}",available_context[:200])

        try:
            search_res = search.invoke({"query": search_query})
            web_data = str(search_res)
            reasoning_logs.append(f"Web Search ({search_query}).")
        except Exception as e:
            web_data = f"Web Search Error: {str(e)}"

    reasoning_steps = "\n".join(reasoning_logs) if reasoning_logs else None

    return {"sql_data": sql_data,"sql_query": sql_query,"rag_data": rag_data,"web_data": web_data,"reasoning_steps": reasoning_steps}






