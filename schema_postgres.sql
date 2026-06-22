DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user'
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    price NUMERIC(10,2),
    image TEXT,
    stock INT DEFAULT 10
);

CREATE TABLE cart (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    quantity INT DEFAULT 1
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    total_amount NUMERIC(10,2),
    status VARCHAR(50) DEFAULT 'Placed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    product_id INT REFERENCES products(id) ON DELETE CASCADE,
    quantity INT,
    price NUMERIC(10,2)
);

INSERT INTO users (name, email, password, role)
VALUES ('Admin', 'admin@gmail.com', 'admin123', 'admin');

INSERT INTO products (name, description, price, image, stock) VALUES
('Wireless Headphones', 'High-quality over-ear wireless headphones', 2999.00, 'https://images.unsplash.com/photo-1518444065439-e933c06ce9cd', 10),
('Smart Watch', 'Stylish smart watch with fitness tracking', 4999.00, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30', 10),
('Gaming Mouse', 'RGB gaming mouse with adjustable DPI', 1499.00, 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7', 10),
('Laptop Backpack', 'Water-resistant backpack for laptops up to 15.6 inch', 1999.00, 'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee', 10),
('Bluetooth Speaker', 'Portable Bluetooth speaker with deep bass', 2499.00, 'https://images.unsplash.com/photo-1585386959984-a4155224a1ad', 10);