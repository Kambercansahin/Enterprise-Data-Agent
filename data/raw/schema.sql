-- 1. CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);

-- 2. PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100) DEFAULT 'unknown',
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g FLOAT,
    product_length_cm FLOAT,
    product_height_cm FLOAT,
    product_width_cm FLOAT
);

-- 3. SELLERS
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
);

-- 4. ORDERS
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id),
    order_status VARCHAR(50),
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

-- 5. ORDER_ITEMS (Composite PK)
CREATE TABLE IF NOT EXISTS order_items (
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(50) NOT NULL REFERENCES products(product_id),
    seller_id VARCHAR(50) NOT NULL REFERENCES sellers(seller_id),
    shipping_limit_date TIMESTAMP,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    freight_value NUMERIC(10, 2) CHECK (freight_value >= 0),
    PRIMARY KEY (order_id, order_item_id)
);

-- 6. ORDER_PAYMENTS (Composite PK)
CREATE TABLE IF NOT EXISTS order_payments (
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(50) NOT NULL,
    payment_installments INTEGER DEFAULT 1,
    payment_value NUMERIC(10, 2) NOT NULL CHECK (payment_value >= 0),
    PRIMARY KEY (order_id, payment_sequential)
);

-- 7. ORDER_REVIEWS (Surrogate Identity PK)
CREATE TABLE IF NOT EXISTS order_reviews (
    review_pk BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    review_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL REFERENCES orders(order_id),
    review_score INTEGER CHECK (review_score BETWEEN 1 AND 5),
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

-- İNDEKSLER (SQL Agent Performansı İçin)
CREATE INDEX IF NOT EXISTS idx_customers_unique_id ON customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_timestamp ON orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_order_items_seller_id ON order_items(seller_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(product_category_name);
CREATE INDEX IF NOT EXISTS idx_order_reviews_order_id ON order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_order_reviews_review_id ON order_reviews(review_id);