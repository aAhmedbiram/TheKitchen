from flask import Flask, render_template, session
from flask_cors import CORS
from flask_login import LoginManager
from config import Config
from auth import require_admin_page
from extensions import db
from models import User, MenuItem, Order, OrderItem, Payment, Cart

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure CORS to support credentials
    CORS(app, 
         supports_credentials=True,
         origins=["https://thekitchen.fly.dev", "http://localhost:5000", "http://127.0.0.1:5000"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         allow_headers=["Content-Type", "Authorization"])

    # Login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        return User.query.get(int(user_id))

    # API Blueprints
    from routes.menu_api import menu_api
    from routes.auth_api import auth_api
    from routes.orders_api import orders_api
    from routes.payments_api import payments_api
    from routes.admin_api import admin_api
    from routes.cart_api import cart_api

    app.register_blueprint(menu_api, url_prefix="/api")
    app.register_blueprint(auth_api, url_prefix="/api")
    app.register_blueprint(orders_api, url_prefix="/api")
    app.register_blueprint(payments_api, url_prefix="/api")
    app.register_blueprint(admin_api, url_prefix="/api")
    app.register_blueprint(cart_api, url_prefix="/api")

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables."""
        with app.app_context():
            db.create_all()
        print("✅ Database tables created.")

    @app.cli.command("seed-db")
    def seed_db_command():
        """Seed database with sample menu items."""
        from models import MenuItem
        
        samples = [
            ("كشري مصري", "Egyptian Koshary", 
             "مزيج شهي من الأرز والمكرونة والعدس والحمص بالصلصة والبصل المقلي.",
             "Delicious mix of rice, pasta, lentils, and chickpeas with tomato sauce and fried onions.",
             65, True, "koshary.jpg"),
            ("فول وفلافل", "Foul and Falafel",
             "فول مدمس بالزيت الحار والفلافل المقرمشة والخضار الطازجة.",
             "Fava beans with hot oil and crispy falafel with fresh vegetables.",
             45, True, "falfel.jpg"),
            ("شاورما لحم", "Meat Shawarma",
             "لحم ضأن متبل ومشوي على الفحم مع صوص الطحينة والخضار.",
             "Seasoned lamb meat grilled on charcoal with tahini sauce and vegetables.",
             85, True, "shawarma.jpg"),
            ("محشي ورق عنب", "Stuffed Grape Leaves",
             "ورق عنب محشو بالأرز واللحم المفروم والبهارات العطرية.",
             "Grape leaves stuffed with rice, ground meat, and aromatic spices.",
             75, True, "mahshi.jpg"),
            ("مخللات مشكلة", "Mixed Pickles",
             "تشكيلة من الخيار والجزر والقرنبيط والبصل المخلل.",
             "Assorted pickled cucumbers, carrots, cauliflower, and onions.",
             25, True, "pickles.jpg"),
            ("كنافة بالقشطة", "Kunafa with Cream",
             "خيوط الكنافة الذهبية مع القشطة الطازجة وشراب الورد.",
             "Golden kunafa threads with fresh cream and rose syrup.",
             55, True, "kunafa.jpg"),
        ]

        if MenuItem.query.count() > 0:
            print("ℹ️ Menu items already exist. Skipping seed.")
            return

        for name_ar, name_en, desc_ar, desc_en, price, available, image in samples:
            menu_item = MenuItem(
                name_ar=name_ar,
                name_en=name_en,
                description_ar=desc_ar,
                description_en=desc_en,
                price=price,
                is_available=available,
                image_urls=[image]
            )
            db.session.add(menu_item)
        
        db.session.commit()
        print("✅ Seeded sample menu items.")

    # Main routes
    @app.route("/")
    def index():
        # Check if language preference exists
        if 'language' not in session:
            session['language'] = 'en'
        return render_template("index.html")

    @app.route("/signup")
    def signup():
        return render_template("signup.html")

    @app.route("/signin")
    def signin():
        return render_template("signin.html")

    @app.route("/forgot-password")
    def forgot_password():
        return render_template("forgot_password.html")

    @app.route("/menu")
    def menu():
        from models import MenuItem
        menu_items = MenuItem.query.filter_by(is_available=True).order_by(MenuItem.id.desc()).all()
        return render_template("menu.html", items=menu_items)

    @app.route("/cart")
    def cart():
        return render_template("cart.html")

    @app.route("/checkout")
    def checkout():
        return render_template("checkout.html")

    @app.route("/orders")
    def orders():
        return render_template("orders.html")

    @app.route("/order/<int:order_id>")
    def order_detail(order_id):
        return render_template("order_detail.html", order_id=order_id)

    @app.route("/admin")
    @require_admin_page
    def admin_panel():
        return render_template("admin.html")

    @app.route("/admin/menu")
    @require_admin_page
    def admin_menu():
        return render_template("admin_menu.html")

    @app.route("/admin/orders")
    @require_admin_page
    def admin_orders():
        return render_template("admin_orders.html")

    @app.route("/admin/customers")
    @require_admin_page
    def admin_customers():
        return render_template("admin_customers.html")

    @app.route("/admin/analytics")
    @require_admin_page
    def admin_analytics():
        return render_template("admin_analytics.html")

    @app.route("/set-language/<lang>")
    def set_language(lang):
        if lang in ['en', 'ar']:
            session['language'] = lang
        return redirect(request.referrer or url_for('index'))

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True)
