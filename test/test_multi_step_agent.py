import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#pytest
import pytest

#deepeval
from deepeval import evaluate
from deepeval.test_case import LLMTestCase,SingleTurnParams
from deepeval.metrics import AnswerRelevancyMetric,HallucinationMetric,GEval

#model
from src.graphs.workflow import graph


@pytest.mark.parametrize(
    "question_id,user_question",
    [
     ("1","2018 Ağustos ayında en yüksek sipariş adedine ulaşan ürün kategorisinin, günümüzdeki pazar durumu veya benzer kategorilerdeki global e-ticaret trendleri nasıldır?"),
     ("2","1 puanlık (en düşük) değerlendirme alan siparişlerin toplam sayısı nedir ve bu olumsuz siparişlerin en yoğun görüldüğü ilk 2 ürün kategorisinin genel siparişler içindeki oranı yüzde kaçtır?"),
     ("3","En çok satılan ilk 3 ürünün müşteri memnuniyeti ve yorumlardaki ana şikayetleri neler?"),
     ("4","Kredi kartıyla 8 ve üzeri taksitle yapılan toplam sipariş tutarı ne kadardır ve bu ödemeleri yapan müşterilerin sipariş verdiği iller arasında ilk sırada hangi şehir yer almaktadır?")
     ]
)

def test_multi_step_agent(question_id,user_question):
    question = user_question

    #model
    response_model = graph.invoke(
        {"question":question},
        config={"configurable": {"thread_id": f"test-{question_id}"}}
    )

    #generation
    generation_output = response_model.get("generation","")
    #rag data
    rag_data = response_model.get("rag_data","")
    if rag_data:
        rag_context = [str(rag_data)]
    else:
        rag_context = ["Rag Data is None"]

    #web_search
    web_data = response_model.get("web_data","")
    if web_data:
        web_context = [str(web_data)]
    else:
        web_context = ["Web data is None"]

    #sql_data
    sql_data = response_model.get("sql_data","")
    if sql_data:
        sql_context = [str(sql_data)]
    else:
        sql_context = ["SQL data is None"]

    total_context = rag_context + sql_context + web_context

    test_case = LLMTestCase(
        input=question,
        actual_output=generation_output,
        context = total_context,
    )

    #hallucination
    hallucination_eval = HallucinationMetric(
        threshold=0.5,
        include_reason=True,
    )

    #answer
    answer_eval = AnswerRelevancyMetric(
        threshold=0.5,
        include_reason=True,
    )

    evaluate(test_cases = [test_case],metrics =[hallucination_eval,answer_eval])