CREATE DATABASE IF NOT EXISTS ecommerce_db;
USE ecommerce_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(120) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user'
);

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image VARCHAR(255) DEFAULT 'https://via.placeholder.com/300x200',
    stock INT DEFAULT 0
);

CREATE TABLE IF NOT EXISTS cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

INSERT INTO users (name, email, password, role)
VALUES ('Admin', 'admin@gmail.com', 'admin123', 'admin')
ON DUPLICATE KEY UPDATE email=email;

INSERT INTO products (name, description, price, image, stock) VALUES
('Wireless Headphones', 'Premium over-ear wireless headphones with noise cancellation.', 2999.00, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e', 20),
('Smart Watch', 'Track fitness, notifications, and more with this stylish smartwatch.', 4999.00, 'https://images.unsplash.com/photo-1523275335684-37898b6baf30', 15),
('Gaming Mouse', 'High precision gaming mouse with RGB lighting.', 1499.00, 'https://images.unsplash.com/photo-1587202372775-e229f172b9d7', 25),
('Laptop Backpack', 'Water-resistant backpack suitable for laptops up to 15.6 inches.', 1999.00, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff', 30),
('Bluetooth Speaker', 'Portable speaker with deep bass and long battery life.', 2499.00, 'https://images.unsplash.com/photo-1512446816042-444d64126727', 18);