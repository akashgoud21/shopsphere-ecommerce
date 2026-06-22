from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
import os
import psycopg2
import psycopg2.extras

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "shopsphere_secret_key")


def get_db_connection():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise Exception("DATABASE_URL not set")
    return psycopg2.connect(database_url)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("role") != "admin":
            flash("Access denied! Admin only.", "danger")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/")
def index():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products ORDER BY id DESC LIMIT 6")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            conn.close()
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, password, "user")
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["role"] = user["role"]

            flash(f"Welcome, {user['name']}!", "success")
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("index"))
        else:
            flash("Invalid email or password!", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("index"))


@app.route("/products")
def products():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("products.html", products=products)


@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT * FROM cart WHERE user_id=%s AND product_id=%s", (user_id, product_id))
    existing = cur.fetchone()

    if existing:
        cur.execute("UPDATE cart SET quantity = quantity + 1 WHERE id=%s", (existing["id"],))
    else:
        cur.execute(
            "INSERT INTO cart (user_id, product_id, quantity) VALUES (%s, %s, %s)",
            (user_id, product_id, 1)
        )

    conn.commit()
    cur.close()
    conn.close()

    flash("Product added to cart!", "success")
    return redirect(url_for("products"))


@app.route("/cart")
@login_required
def cart():
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT cart.id as cart_id, cart.quantity, products.*
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, (user_id,))
    cart_items = cur.fetchall()

    cur.close()
    conn.close()

    total = sum(float(item["price"]) * item["quantity"] for item in cart_items)
    return render_template("cart.html", cart_items=cart_items, total=total)


@app.route("/update_cart/<int:cart_id>", methods=["POST"])
@login_required
def update_cart(cart_id):
    quantity = int(request.form["quantity"])

    conn = get_db_connection()
    cur = conn.cursor()

    if quantity <= 0:
        cur.execute("DELETE FROM cart WHERE id=%s", (cart_id,))
    else:
        cur.execute("UPDATE cart SET quantity=%s WHERE id=%s", (quantity, cart_id))

    conn.commit()
    cur.close()
    conn.close()

    flash("Cart updated successfully!", "success")
    return redirect(url_for("cart"))


@app.route("/remove_from_cart/<int:cart_id>")
@login_required
def remove_from_cart(cart_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM cart WHERE id=%s", (cart_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Item removed from cart.", "info")
    return redirect(url_for("cart"))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("""
        SELECT cart.id as cart_id, cart.quantity, products.*
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.user_id=%s
    """, (user_id,))
    cart_items = cur.fetchall()

    if not cart_items:
        cur.close()
        conn.close()
        flash("Your cart is empty!", "warning")
        return redirect(url_for("products"))

    total = sum(float(item["price"]) * item["quantity"] for item in cart_items)

    if request.method == "POST":
        cur.execute(
            "INSERT INTO orders (user_id, total_amount, status) VALUES (%s, %s, %s) RETURNING id",
            (user_id, total, "Placed")
        )
        order_id = cur.fetchone()["id"]

        for item in cart_items:
            cur.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item["id"], item["quantity"], item["price"]))

        cur.execute("DELETE FROM cart WHERE user_id=%s", (user_id,))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("order_success", order_id=order_id))

    cur.close()
    conn.close()
    return render_template("checkout.html", cart_items=cart_items, total=total)


@app.route("/order_success/<int:order_id>")
@login_required
def order_success(order_id):
    return render_template("order_success.html", order_id=order_id)


@app.route("/my_orders")
@login_required
def my_orders():
    user_id = session["user_id"]

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM orders WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
    orders = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("my_orders.html", orders=orders)


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT COUNT(*) as total_products FROM products")
    total_products = cur.fetchone()["total_products"]

    cur.execute("SELECT COUNT(*) as total_users FROM users WHERE role='user'")
    total_users = cur.fetchone()["total_users"]

    cur.execute("SELECT COUNT(*) as total_orders FROM orders")
    total_orders = cur.fetchone()["total_orders"]

    cur.execute("SELECT COALESCE(SUM(total_amount), 0) as revenue FROM orders")
    total_revenue = cur.fetchone()["revenue"]

    cur.execute("SELECT * FROM products ORDER BY id DESC")
    products = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_products=total_products,
        total_users=total_users,
        total_orders=total_orders,
        total_revenue=total_revenue,
        products=products
    )


@app.route("/admin/add_product", methods=["GET", "POST"])
@admin_required
def add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        image = request.form["image"]
        stock = request.form["stock"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO products (name, description, price, image, stock)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, description, price, image, stock))
        conn.commit()
        cur.close()
        conn.close()

        flash("Product added successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/add_product.html")


@app.route("/admin/edit_product/<int:product_id>", methods=["GET", "POST"])
@admin_required
def edit_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        image = request.form["image"]
        stock = request.form["stock"]

        cur.execute("""
            UPDATE products
            SET name=%s, description=%s, price=%s, image=%s, stock=%s
            WHERE id=%s
        """, (name, description, price, image, stock, product_id))
        conn.commit()
        cur.close()
        conn.close()

        flash("Product updated successfully!", "success")
        return redirect(url_for("admin_dashboard"))

    cur.execute("SELECT * FROM products WHERE id=%s", (product_id,))
    product = cur.fetchone()
    cur.close()
    conn.close()

    return render_template("admin/edit_product.html", product=product)


@app.route("/admin/delete_product/<int:product_id>")
@admin_required
def delete_product(product_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=%s", (product_id,))
    conn.commit()
    cur.close()
    conn.close()

    flash("Product deleted successfully!", "info")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/orders", methods=["GET", "POST"])
@admin_required
def admin_orders():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if request.method == "POST":
        order_id = request.form["order_id"]
        status = request.form["status"]

        cur.execute("UPDATE orders SET status=%s WHERE id=%s", (status, order_id))
        conn.commit()
        flash("Order status updated!", "success")

    cur.execute("""
        SELECT orders.*, users.name as customer_name
        FROM orders
        JOIN users ON orders.user_id = users.id
        ORDER BY orders.created_at DESC
    """)
    orders = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("admin/orders.html", orders=orders)


if __name__ == "__main__":
    app.run(debug=True)