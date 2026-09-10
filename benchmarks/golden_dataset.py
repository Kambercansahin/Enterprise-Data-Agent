GOLDEN_BENCHMARK_SUITE = [
    {
        "id": "tc_01_high_margin_categories",
        "question": "2018 Ağustos ayında teslim edilmiş siparişlerde ciroya göre ilk 5 ürün kategorisi nedir?",
        "ground_truth_sql": """
            SELECT p.product_category_name, ROUND(SUM(oi.price), 2) AS total_revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.order_purchase_timestamp >= '2018-08-01'
              AND o.order_status = 'delivered'
            GROUP BY p.product_category_name
            ORDER BY total_revenue DESC
            LIMIT 5;
        """,
        "expected_tables": ["orders", "order_items", "products"]
    },
    {
            "id": "tc_02_negative_feedback",
            "question": "2018 yılında teslim edilen siparişler arasında 1 puan alan toplam sipariş sayısı kaçtır?",
            "ground_truth_sql": """
                    SELECT COUNT(DISTINCT o.order_id) AS low_score_count
                    FROM order_reviews r
                    JOIN orders o ON r.order_id = o.order_id
                    WHERE r.review_score = 1
                      AND o.order_status = 'delivered'
                      AND o.order_purchase_timestamp >= '2018-01-01'
                      AND o.order_purchase_timestamp < '2019-01-01';
                """,
            "expected_tables": ["order_reviews", "orders"]

    },
    {
        "id": "tc_03_installment_risk",
        "question": "Kredi kartıyla 8 ve üzeri taksitle yapılan siparişlerin toplam tutarı nedir?",
        "ground_truth_sql": """
            SELECT ROUND(SUM(p.payment_value), 2) AS total_val
            FROM order_payments p
            JOIN orders o ON p.order_id = o.order_id
            WHERE p.payment_type = 'credit_card'
              AND p.payment_installments >= 8;
        """,
        "expected_tables": ["order_payments", "orders"]
    }
]