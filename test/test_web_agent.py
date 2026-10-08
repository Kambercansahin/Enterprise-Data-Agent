import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
#deepeval
from deepeval import evaluate
from deepeval.test_case import LLMTestCase,SingleTurnParams
from deepeval.metrics import HallucinationMetric,AnswerRelevancyMetric
#model
from src.graphs.workflow import graph

@pytest.mark.parametrize(
    "question_id,user_question",
    [
        ("1", "Türkiye e-ticaret pazarında son dönemdeki lojistik trendleri ve teslimat gecikmesi sorunları genel sektörü nasıl etkiliyor?"),
        ("2", "E-ticarette kargo süreçlerini iyileştirmek için son dönemde hangi yenilikçi yöntemler ve trendler konuşuluyor?"),
        ("3", "Türkiye'de e-ticaret lojistiğinde son dönemde yaşanan aksaklıklar ve kargo süreçlerinin iyileştirilmesine yönelik atılan adımlar nelerdir?")
    ]
)
def test_web_agent(question_id,user_question):
    question = user_question

    #response of model
    response_model = graph.invoke(
        {"question": question},
        config={"configurable": {"thread_id": f"test-{question_id}"}}
    )
    #generation data
    output_data = response_model.get("generation","")

    #web data
    web_data = response_model.get("web_data","")
    if web_data:
        context = [str(web_data)]
    else:
        context = ["Web Data is empty"]

    test_case = LLMTestCase(
        input=question,
        actual_output=output_data,
        context= context
    )

    #hallucination
    hallucination = HallucinationMetric(
        threshold=0.5,
        include_reason=True
    )
    #answer
    answer = AnswerRelevancyMetric(
        threshold=0.5,
        include_reason=True
    )
    evaluate(test_cases = [test_case],metrics = [hallucination,answer])
