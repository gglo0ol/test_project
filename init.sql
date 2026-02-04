-- Категории (дерево)
CREATE TABLE categories (
    id          BIGSERIAL       PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    parent_id   BIGINT          REFERENCES categories(id) ON DELETE SET NULL,
    sort_order  INTEGER         NOT NULL DEFAULT 0,
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    
    CONSTRAINT chk_no_self_parent CHECK (id != parent_id)
);

-- Товары / номенклатура
CREATE TABLE items (
    id              BIGSERIAL       PRIMARY KEY,
    sku             VARCHAR(64)     UNIQUE,
    name            VARCHAR(300)    NOT NULL,
    category_id     BIGINT          REFERENCES categories(id) ON DELETE SET NULL,
    price           DECIMAL(15,2)   NOT NULL CHECK (price >= 0),
    stock_quantity  INTEGER         NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Клиенты
CREATE TABLE customers (
    id          BIGSERIAL       PRIMARY KEY,
    name        VARCHAR(200)    NOT NULL,
    phone       VARCHAR(40),
    email       VARCHAR(120)    UNIQUE,
    address     TEXT,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Заказы
CREATE TABLE orders (
    id              BIGSERIAL       PRIMARY KEY,
    customer_id     BIGINT          NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_date      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    status          VARCHAR(40)     NOT NULL DEFAULT 'new',
    total_amount    DECIMAL(15,2)   NOT NULL DEFAULT 0 CHECK (total_amount >= 0),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Позиции заказа
CREATE TABLE order_items (
    id          BIGSERIAL       PRIMARY KEY,
    order_id    BIGINT          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    item_id     BIGINT          NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
    quantity    INTEGER         NOT NULL CHECK (quantity > 0),
    price       DECIMAL(15,2)   NOT NULL CHECK (price >= 0),
    CONSTRAINT unique_item_per_order UNIQUE (order_id, item_id)
);

-- Индексы
CREATE INDEX idx_categories_parent_id    ON categories(parent_id);
CREATE INDEX idx_items_category_id       ON items(category_id);
CREATE INDEX idx_orders_customer_id      ON orders(customer_id);
CREATE INDEX idx_order_items_order_id    ON order_items(order_id);
CREATE INDEX idx_order_items_item_id     ON order_items(item_id);

-- Тестовые данные
INSERT INTO categories (id, name) VALUES 
    (1, 'Electronics'),
    (2, 'Books');

INSERT INTO items (id, sku, name, category_id, price, stock_quantity) VALUES
    (1, 'PHONE-001', 'Smartphone X', 1, 999.99, 50),
    (2, 'LAPTOP-001', 'Laptop Pro', 1, 1499.99, 20),
    (3, 'BOOK-001', 'Python Guide', 2, 49.99, 100),
    (4, 'BOOK-002', 'SQL Mastery', 2, 39.99, 0);  -- Out of stock

INSERT INTO customers (id, name, email, phone) VALUES
    (1, 'John Doe', 'john@example.com', '+1234567890'),
    (2, 'Jane Smith', 'jane@example.com', '+0987654321');

INSERT INTO orders (id, customer_id, status) VALUES
    (1, 1, 'new'),
    (2, 1, 'paid'),
    (3, 2, 'new');

-- Reset sequences
SELECT setval('categories_id_seq', 10);
SELECT setval('items_id_seq', 10);
SELECT setval('customers_id_seq', 10);
SELECT setval('orders_id_seq', 10);
