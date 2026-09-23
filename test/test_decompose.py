import pytest
from src.graphs.chains.decompose_chain import decompose_chain


@pytest.mark.parametrize("question",
                         [
                             ("En çok satılan ilk 3 ürünün sipariş sayıları ve bu ürünler hakkındaki olumsuz müşteri yorumları nelerdir?"),
                             ("Müşteri yorumlarında en sık şikayet edilen teslimat sorununu belirleyin ve bu sorundan etkilenen siparişlerin toplam sayısını bulun."),
                             ("En çok gelir getiren 5 ürün kategorisini bulun. Her kategori için müşterilerin en sık dile getirdiği sorunları belirleyin ve bu sorunların satış performansıyla ilişkisini değerlendirin."),
                             ("En çok satış yapan 5 ürünü belirleyin. Bu ürünlerin müşteri yorumlarını inceleyerek teslimat, ürün kalitesi ve müşteri hizmetleri açısından öne çıkan sorunları karşılaştırın")
                         ])
@pytest.mark.decompose
def test_decompose_sql_rag(question):
    result = decompose_chain.invoke({"question":question,"chat_history":[]})

    assert result.web_query is None

    assert result.rag_query is not None
    assert "{context}" in result.rag_query

    assert result.sql_question is not None
    assert "SELECT" not in result.sql_question.upper()


@pytest.mark.decompose
def test_decompose_sql_rag_and_web():

  question = ( "İptal edilen sipariş oranımızın yüksek olmasının ardındaki temel sebepleri hem müşteri şikayetleri hem de sektör genelindeki kargo gecikme trendleriyle kıyasla")

  result = decompose_chain.invoke({"question": question, "chat_history": []})

  assert result.sql_question is not None or result.rag_query is not None
  assert result.web_query is not None
  assert ("trend" in result.web_query.lower() or "kargo" in result.web_query.lower()or "gecikme" in result.web_query.lower())

