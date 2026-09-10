import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5433"),
        dbname=os.getenv("POSTGRES_DB", "enterprise_db"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "password123")
    )


def run_explain_analyze(query: str):
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {query}"
    with get_connection() as conn:
        with conn.cursor() as cur:
            #Bellek arttırımı
            cur.execute("SET work_mem = '16MB';")
            cur.execute(explain_query)
            plan_lines = cur.fetchall()

    print("\n" + "=" * 50)
    print("Sorgu:")
    print(query)
    print("=" * 50)
    print("Execution Plan:")
    for line in plan_lines:
        print(line[0])
    print("=" * 50)


def create_composite_index():
    """index_sql =
    CREATE INDEX IF NOT EXISTS idx_orders_status_date_id 
    ON orders (order_status, order_purchase_timestamp) 
    INCLUDE (order_id);

    index_sql =

        CREATE INDEX IF NOT EXISTS idx_reviews_score_order_id 
        ON order_reviews (review_score) 
        INCLUDE (order_id);

    index_sql =
    CREATE INDEX IF NOT EXISTS idx_payments_type_inst_cov 
    ON order_payments (payment_type, payment_installments) 
    INCLUDE (order_id, payment_value);
    """
    index_sql ="""
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(index_sql)
            conn.commit()
            print("Index oluşturuldu veya zaten mevcut.")


if __name__ == "__main__":
    create_composite_index()

    sample_query = """
        SELECT 
        s.seller_state,
        COUNT(oi.order_id) AS total_items_sold,
        ROUND(AVG(oi.freight_value), 2) AS avg_freight
    FROM sellers s
    JOIN order_items oi ON s.seller_id = oi.seller_id
    WHERE s.seller_state = 'SP'
      AND oi.price >= 100.0
    GROUP BY s.seller_state;
        """


    run_explain_analyze(sample_query)