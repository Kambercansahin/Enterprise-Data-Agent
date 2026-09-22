import pytest
from src.graphs.chains.router_chain import router_chain as router
from langchain_core.messages import  AIMessage,HumanMessage

@pytest.mark.parametrize("question,result",
                         [("En çok satış yapan 10 ürün hangisi?","SQL"),
                          ("When did the French Revolution take place?","OutOfScope"),
                          ("Müşteriler kargo paketlemesinden memnun mu?","RAG"),
                          ("Türkiye e-ticaret lojistik trendleri neler?","websearch"),
                          ("En çok satılan ilk 3 ürünün müşteri memnuniyeti ve yorumlardaki ana şikayetleri neler?","MultiStep")])


@pytest.mark.routers
def test_router_single(question,result):
    result_chain = router.invoke({"question":question,"chat_history":[]}).datasource
    assert result_chain == result


@pytest.mark.routers
def test_router_follow_up():
    history = [
        HumanMessage(content="En çok satan ilk 5 ürün kategorisi nedir?"),
        AIMessage(
            content="En çok satan ilk 5 ürün kategorisi aşağıdaki gibidir:1.cama_mesa_banho,2.esporte_lazer,3.moveis_decoracao,4.beleza_saude,5.utilidades_domesticas	"
        ),
    ]
    follow_up_question = "Peki bu ürünlere gelen yorumlar genel olarak ne ile ilgili?"

    result_chain =router.invoke({"question":follow_up_question,"chat_history":history}).datasource
    assert result_chain == "RAG"

