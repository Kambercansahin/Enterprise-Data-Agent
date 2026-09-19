from typing import Any, Dict
from langchain_tavily import TavilySearch
from src.graphs.state import GraphState

# Sadece onaylı kurumsal ve sektörel alan adları
trusted_domains = [
    "webrazzi.com",
    "eticaret.gov.tr",
    "ticaret.gov.tr",
    "bloomberght.com",
    "dunya.com",
    "ekonomim.com",
    "reuters.com",
    "lojistikdernegi.org.tr",
    "utikad.org.tr",
    "sikayetvar.com",
    "tuik.gov.tr",
    "tubisad.org.tr",
    "marketingturkiye.com.tr",
    "pazarlamasyon.com",
]

search = TavilySearch(max_results=10)


def websearch(state: GraphState) -> Dict[str, Any]:
    print("---WebSearch NODE---")
    question = state["question"]

    try:
        search_data = search.invoke({"query": question})

        # If TavilySearch returns a dict, get the 'results' list; if it returns a list directly, use that list
        if isinstance(search_data, dict):
            raw_items = search_data.get("results", [])
        elif isinstance(search_data, list):
            raw_items = search_data
        else:
            raw_items = []

        filtered_results = []
        for d in raw_items:
            if not isinstance(d, dict):
                continue
            source_url = d.get("url", "").lower()

            # URL check: Only pass the domains in the list.
            if any(domain in source_url for domain in trusted_domains):
                filtered_results.append(d)
                print(f"--- Allowed Source: {source_url}")
            else:
                print(f"--- Refused Source: {source_url}")

        if not filtered_results:
            formatted_result = (
                "No verified data regarding this question could be found in the permitted industry sources."
            )
        else:
            top_results = filtered_results[:5]
            formatted_result = "\n\n".join([
                f"Source ({r.get('url')}): {r.get('content')}" for r in top_results
            ])

    except Exception as e:
        print(f"Tavily Error: {e}")
        formatted_result = f"The search service was temporarily unable to respond: {str(e)}"

    return {"web_data": formatted_result,"sql_query": None,}