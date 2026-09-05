import polars as pl
import psycopg2
from psycopg2.extras import execute_values

# 1. Doğrudan Psycopg2 Bağlantısı
conn = psycopg2.connect(
    dbname="enterprise_db",
    user="admin",
    password="password123",
    host="localhost",
    port=5433
)
cur = conn.cursor()

loading_order = [
    ("customers", "olist_customers_dataset.csv"),
    ("products", "olist_products_dataset.csv"),
    ("sellers", "olist_sellers_dataset.csv"),
    ("orders", "olist_orders_dataset.csv"),
    ("order_items", "olist_order_items_dataset.csv"),
    ("order_payments", "olist_order_payments_dataset.csv"),
    ("order_reviews", "olist_order_reviews_dataset.csv"),
]

print("PostgreSQL aktarımı başlıyor...\n")

for table_name, file_name in loading_order:
    print(f"[{table_name.upper()}] hazırlanıyor...")
    df = pl.read_csv(file_name, ignore_errors=True)

    # 1. Products düzeltmesi
    if table_name == "products":
        df = df.rename({
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length"
        }).with_columns(
            pl.col("product_category_name").fill_null("unknown")
        )

    # 2. Orders tarih düzeltmesi
    if table_name == "orders":
        timestamp_cols = [c for c in df.columns if "date" in c or "timestamp" in c]
        for c in timestamp_cols:
            df = df.with_columns(pl.col(c).str.to_datetime(strict=False))

    # 3. Reviews tarih düzeltmesi
    if table_name == "order_reviews":
        df = df.with_columns([
            pl.col("review_creation_date").str.to_datetime(strict=False),
            pl.col("review_answer_timestamp").str.to_datetime(strict=False)
        ])

    # 4. Polars -> Python Dicts -> Tuple Listesi (Sıfır pyarrow bağımlılığı)
    columns = df.columns
    cols_str = ",".join(columns)
    query = f"INSERT INTO {table_name} ({cols_str}) VALUES %s"

    # Polars satırlarını ham python nesneleri olarak alıyoruz
    data_tuples = df.iter_rows()

    # Yüksek hızlı batch yükleme
    execute_values(cur, query, data_tuples, page_size=10000)
    conn.commit()
    print(f"✓ {table_name.upper()} başarıyla yüklendi ({df.height:,} satır)")

cur.close()
conn.close()
print("\nTüm veriler PostgreSQL veritabanına eksiksiz aktarıldı!")