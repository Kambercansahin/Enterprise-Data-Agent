from typing import Any,Dict

from langchain_tavily import TavilySearch

from src.graphs.state import GraphState

#search with tavily only allowed domains
search = TavilySearch(max_results=5,
                                 include_domains = ["sikayetvar.com",
                                                    "webrazzi.com",
                                                    "donanimhaber.com",
                                                    "eksisozluk.com",
                                                    "bloomberght.com"
                                                ])

def websearch(state:GraphState) ->Dict[str,Any]:
    print("---WebSearch NODE---")
    question = state["question"]

    try:
        search_data = search.invoke({"query":question})
        if not search_data:
            formatted_result = "No relevant result was found in the web search."

        else:
            #take the search results url and content
            formatted_result ="\n\n".join([f"Source ({r.get('url')}): {r.get('content')}" for r in search_data])

    except Exception as e:
        formatted_result = f"Web search Error: {str(e)}"

    return {"web_data":formatted_result}


