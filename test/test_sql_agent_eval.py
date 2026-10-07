import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pytest
#deepeval
from deepeval import evaluate
from deepeval.metrics import HallucinationMetric,AnswerRelevancyMetric,GEval
from deepeval.test_case import LLMTestCase,SingleTurnParams

#models
from src.graphs.workflow import graph

@pytest.mark.parametrize(
    "id_number,user_question",
    [("1","2018 Ağustos ayında teslim edilmiş siparişlerde ciroya göre ilk 5 ürün kategorisi nedir?"),
     ("2","2018 yılında teslim edilen siparişler arasında 1 puan alan toplam sipariş sayısı kaçtır?"),
     ("3","Kredi kartıyla 8 ve üzeri taksitle yapılan siparişlerin toplam tutarı nedir?")] )

def test_sql_agent(id_number,user_question):
    question = user_question

    agent_response = graph.invoke({
        "question":question},
        config={"configurable": {"thread_id": f"test-{id_number}"}}
    )
    #generation
    actual_output = agent_response.get("generation","")

    #sql data for hallucination
    sql_data = agent_response.get("sql_data","")
    if sql_data:
        context = [str(sql_data)]
    else:
        context = ["SQL DB datas"]

    test_case = LLMTestCase(
        input=question,
        actual_output=actual_output,
        context= context
    )

    #hallucination control
    hallucination_eval = HallucinationMetric(
        threshold=0.5,
        include_reason=True
    )
    #answer control
    answer_control = AnswerRelevancyMetric(
        threshold=0.5,
        include_reason=True
    )

    evaluate(test_cases=[test_case], metrics=[hallucination_eval, answer_control])

