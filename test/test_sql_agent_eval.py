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
from benchmarks.golden_dataset import GOLDEN_BENCHMARK_SUITE
from src.tools.db_tools import get_schema_summary

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

@pytest.mark.parametrize("benchmark", GOLDEN_BENCHMARK_SUITE)
def test_sql_query(benchmark):
    correctness = GEval(
        name="correctness",
        criteria="does the generated SQL query express the user's question accurately and without errors, in accordance with the database schema?",
        evaluation_params=[SingleTurnParams.ACTUAL_OUTPUT,SingleTurnParams.EXPECTED_OUTPUT],
        threshold=0.6
    )

    question = benchmark["question"]

    #schema
    sqlSchema = get_schema_summary()

    response_model = graph.invoke(
        {"question":question},
        config={"configurable": {"thread_id": f"test-{benchmark['id']}"}}
    )

    #sql query for GEval
    sql_query = response_model.get("sql_query","")
    if sql_query:
        context_query = str(sql_query)
    else:
        context_query = "SQL query is empty"

    test_case= LLMTestCase(
        input=question,
        actual_output=context_query,
        expected_output= benchmark["ground_truth_sql"],
        context=[sqlSchema]
    )

    evaluate(test_cases=[test_case], metrics=[correctness])

