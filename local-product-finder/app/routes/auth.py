from functools import wraps
import re
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, g
)
from app.models import User, Shop

bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def shop_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please sign in to manage your shop.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        
        # Verify shop exists for this owner
        shop = Shop.get_by_owner_id(session["user_id"])
        if not shop:
            flash("You do not have an active shop profile yet.", "warning")
            return redirect(url_for("auth.register_shop"))
        
        g.current_shop = shop
        return f(*args, **kwargs)
    return decorated_function

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        g.shop = None
    else:
        g.user = User.get_by_id(user_id)
        if g.user:
            g.shop = Shop.get_by_owner_id(user_id)
        else:
            session.clear()
            g.user = None
            g.shop = None

@bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard.index"))

    demo_presets = [
        {"email": "greenvalley@localfinder.demo", "name": "Green Valley Organic Grocers", "badge": "Groceries & Produce"},
        {"email": "cornerstone@localfinder.demo", "name": "Cornerstone Health & Pharmacy", "badge": "Health & Pharmacy"},
        {"email": "metrotech@localfinder.demo", "name": "Metro Tech & Gadget Hub", "badge": "Electronics & Tech"},
        {"email": "downware@localfinder.demo", "name": "Downtown Hardware & Home", "badge": "Hardware & Tools"}
    ]

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        next_url = request.args.get("next") or request.form.get("next") or url_for("dashboard.index")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("auth/login.html", email=email, demo_presets=demo_presets)

        user = User.get_by_email(email)
        if user and User.verify_password(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(next_url)
        else:
            flash("Invalid email or password. Please try again or use a demo login.", "danger")

    return render_template("auth/login.html", demo_presets=demo_presets)

@bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        shop_name = request.form.get("shop_name", "").strip()
        shop_category = request.form.get("shop_category", "").strip()
        shop_address = request.form.get("shop_address", "").strip()
        shop_city = request.form.get("shop_city", "").strip()
        shop_phone = request.form.get("shop_phone", "").strip()

        errors = []

        if not name or len(name) < 2:
            errors.append("Please enter your full name (at least 2 characters).")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Please provide a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if not shop_name or len(shop_name) < 2:
            errors.append("Please enter your shop name.")
        if not shop_address or not shop_city:
            errors.append("Shop address and city are required.")

        # Check existing email
        if not errors and User.get_by_email(email):
            errors.append("An account with this email address already exists. Please log in.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", form=request.form)

        # Generate unique slug
        base_slug = re.sub(r"[^\w\s-]", "", shop_name.lower()).replace(" ", "-")
        slug = base_slug
        counter = 1
        while Shop.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1

        # Use default coordinates (or approx offset based on city)
        latitude = float(request.form.get("latitude") or 37.7749)
        longitude = float(request.form.get("longitude") or -122.4194)

        try:
            user_id = User.create(email=email, password=password, name=name, role="shop_owner")
            
            # Default hours
            import json
            default_hours = json.dumps({
                "mon": {"open": "09:00", "close": "19:00", "closed": False},
                "tue": {"open": "09:00", "close": "19:00", "closed": False},
                "wed": {"open": "09:00", "close": "19:00", "closed": False},
                "thu": {"open": "09:00", "close": "19:00", "closed": False},
                "fri": {"open": "09:00", "close": "19:00", "closed": False},
                "sat": {"open": "10:00", "close": "18:00", "closed": False},
                "sun": {"open": "11:00", "close": "16:00", "closed": False}
            })

            Shop.create(
                owner_id=user_id,
                name=shop_name,
                slug=slug,
                description=request.form.get("shop_description", f"Local neighborhood store in {shop_city}"),
                category=shop_category or "General Retail",
                address=shop_address,
                city=shop_city,
                postal_code=request.form.get("shop_postal_code", ""),
                latitude=latitude,
                longitude=longitude,
                phone=shop_phone,
                email=email,
                website=request.form.get("shop_website", ""),
                opening_hours_json=default_hours,
                is_demo=0
            )

            session.clear()
            session["user_id"] = user_id
            session["user_name"] = name
            session["user_role"] = "shop_owner"

            flash("Registration successful! Your shop is created. Start adding products to your inventory.", "success")
            return redirect(url_for("dashboard.index"))

        except Exception as e:
            flash(f"Registration failed: {str(e)}", "danger")
            return render_template("auth/register.html", form=request.form)

    return render_template("auth/register.html", form={})

@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("customer.home"))
