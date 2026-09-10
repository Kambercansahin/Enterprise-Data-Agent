import os
import sys
import time
import psycopg2
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.graphs.workflow import app
from golden_dataset import GOLDEN_BENCHMARK_SUITE

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "enterprise_db"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "password123")
    )


def execute_sql(sql: str):
    clean_sql = sql.replace("```sql", "").replace("```", "").strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SET work_mem = '16MB';")

            cur.execute(f"EXPLAIN (ANALYZE, FORMAT JSON) {clean_sql}")
            plan = cur.fetchone()[0]
            db_execution_time_ms = plan[0]["Execution Time"]

            cur.execute(clean_sql)
            rows = cur.fetchall()
            return rows, db_execution_time_ms


def evaluate_agent():
    print(f"\n{'Test ID':<26} | {'Accuracy':<10} | {'LLM Time':<12} | {'DB Time':<10}")
    print("-" * 65)

    total_tests = len(GOLDEN_BENCHMARK_SUITE)
    correct_answers = 0

    for test in GOLDEN_BENCHMARK_SUITE:
        # 1. Get the ground truth data from the answer key
        expected_data, _ = execute_sql(test["ground_truth_sql"])

        # 2. Run the LangGraph Agent and measure its execution time
        t0 = time.time()
        try:
            agent_response = app.invoke({"question": test["question"]})
            llm_latency = (time.time() - t0) * 1000

            # Debug: Print all keys available in the state
            print(f"\n--> [{test['id']}] State Keys: {list(agent_response.keys())}")

            # Check possible keys that may contain the generated SQL
            generated_sql = (
                agent_response.get("sql")
                or agent_response.get("sql_query")
                or agent_response.get("query")
                or agent_response.get("generated_sql")
            )

            if not generated_sql:
                raise ValueError(
                    f"SQL anahtarı bulunamadı. Mevcut anahtarlar: {list(agent_response.keys())}"
                )

            print(f"-->  SQL:\n{generated_sql.strip()}\n")

            # 3. Execute the agent's SQL query in the database
            actual_data, db_latency = execute_sql(generated_sql)

            # 4. Execution Accuracy
            is_correct = (expected_data == actual_data)
            if is_correct:
                correct_answers += 1
            acc_status = "PASS (1.0)" if is_correct else "FAIL (0.0)"

        except Exception as e:
            llm_latency = (time.time() - t0) * 1000
            db_latency = 0.0
            acc_status = "ERROR"
            print(f"ERROR: {e}")

        print(f"{test['id']:<26} | {acc_status:<10} | {llm_latency:>9.2f} ms | {db_latency:>7.2f} ms")

    accuracy_rate = (correct_answers / total_tests) * 100
    print("-" * 65)
    print(f"(Execution Accuracy): %{accuracy_rate:.1f}\n")


if __name__ == "__main__":
    evaluate_agent()