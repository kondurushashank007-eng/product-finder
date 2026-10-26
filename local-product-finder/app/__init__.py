import os
from flask import Flask, render_template
from app.config import Config
from app.db import close_db, init_db
from app.services.distance import format_distance, format_relative_time, format_time_12h

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Register DB teardown
    app.teardown_appcontext(close_db)

    # Initialize tables and seed if empty
    with app.app_context():
        init_db(app)
        if not app.config.get("TESTING"):
            from app.db import get_db
            db = get_db()
            count = db.execute("SELECT COUNT(*) FROM shops").fetchone()[0]
            if count == 0:
                from seed_data import seed_database
                seed_database(app.config["DATABASE_PATH"])

    # Custom Jinja Template Filters
    @app.template_filter("currency")
    def currency_filter(value):
        symbol = app.config.get("APP_CURRENCY_SYMBOL", "$")
        try:
            return f"{symbol}{float(value):.2f}"
        except (ValueError, TypeError):
            return f"{symbol}0.00"

    @app.template_filter("relative_time")
    def relative_time_filter(dt_val):
        return format_relative_time(dt_val)

    @app.template_filter("distance")
    def distance_filter(dist_km):
        return format_distance(dist_km)

    @app.template_filter("time12")
    def time12_filter(t_str):
        return format_time_12h(t_str)

    # Context Processor for Global Template Variables
    @app.context_processor
    def inject_globals():
        return {
            "APP_NAME": app.config.get("APP_NAME", "Local Product Finder"),
            "CURRENCY_SYMBOL": app.config.get("APP_CURRENCY_SYMBOL", "$"),
            "DEFAULT_CITY": app.config.get("DEFAULT_USER_CITY", "San Francisco, CA"),
            "DEFAULT_LAT": app.config.get("DEFAULT_USER_LAT", 37.7749),
            "DEFAULT_LNG": app.config.get("DEFAULT_USER_LNG", -122.4194)
        }

    # Register Blueprints
    from app.routes.customer import bp as customer_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.api import bp as api_bp

    app.register_blueprint(customer_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("customer/404.html", message="The page or store you are looking for does not exist."), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template("customer/500.html", message="An unexpected error occurred. Please try again."), 500

    return app
