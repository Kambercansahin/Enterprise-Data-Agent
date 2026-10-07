import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest

#deepeval
from deepeval import evaluate
from deepeval.metrics import GEval,HallucinationMetric,AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase,SingleTurnParams

#model
from src.graphs.workflow import graph


#cevap Qdrant sonuçlarına dayanıyor mu
@pytest.mark.parametrize(
    "question_id,user_question",
    [("1","Müşterilerin kargo süreçleri ve geç teslimatlarla ilgili yaptığı en yaygın şikayetler nelerdir?"),
     ("2","Düşük puan (1 veya 2 yıldız) veren müşteriler genellikle ürün kalitesi hakkında hangi konulardan yakınıyor?"),
     ("3","Müşteri yorumlarında satıcıların iletişimi ve paketleme özeni hakkında öne çıkan olumlu veya olumsuz eleştiriler nelerdir?")]
)
def test_rag_agent(question_id,user_question):
    question = user_question

    #agent response
    agent_response = graph.invoke(
        {"question":question},
        config={"configurable": {"thread_id": f"test-{question_id}"}}
    )
    #answer
    actual_output = agent_response.get("generation","")
    #rag data
    rag_data = agent_response.get("rag_data","")
    if rag_data:
        context = rag_data.split("\n\n")
    else:
        context = ["Rag Data is empty"]

    test_case = LLMTestCase(
        input=question,
        actual_output= actual_output,
        context = context
    )
    hallucination_eval = HallucinationMetric(
        threshold=0.5,
        include_reason=True
    )
    answer_eval = AnswerRelevancyMetric(
        threshold=0.5,
        include_reason=True
    )

    evaluate(test_cases = [test_case],metrics = [hallucination_eval,answer_eval])