import pytest
from src.graphs.workflow import graph
from langchain_core.messages import AIMessage,HumanMessage
from src.graphs.nodes.web_search_node import websearch


@pytest.mark.hygiene
def test_nodes_hygiene():
    question = "Fransız İhtilali ne zaman gerçekleşti?"
    result = graph.invoke({"question":question},config={"configurable": {"thread_id": "test_hygiene_1"}})
    assert result.get("sql_query") is None
    assert result.get("sql_data") is None
    assert result.get("rag_query") is None
    assert result.get("rag_data") is None
    assert result.get("reasoning_steps") is None


@pytest.mark.hygiene
def test_nodes_hygiene_follow_up():
    history = [
        HumanMessage(content="En çok satan ilk 5 ürün kategorisi nedir?"),
        AIMessage(
            content="En çok satan ilk 5 ürün kategorisi aşağıdaki gibidir:1.cama_mesa_banho,2.esporte_lazer,3.moveis_decoracao,4.beleza_saude,5.utilidades_domesticas	"
        ),
    ]
    follow_up_question = "Fransız İhtilali ne zaman gerçekleşti?"

    result = graph.invoke({"question":follow_up_question,"chat_history":history},config={"configurable": {"thread_id": "test_hygiene_2"}})
    assert result.get("sql_query") is None
    assert result.get("sql_data") is None
    assert result.get("rag_query") is None
    assert result.get("rag_data") is None
    assert result.get("reasoning_steps") is None


@pytest.mark.hygiene
def test_websearch():
    state = {
        "question": "Türkiye'de e-ticaret sektöründeki lojistik trendleri nelerdir?"
    }

    result = websearch(state)

    assert result.get("web_data") != ""
    assert result.get("web_data") is not None



