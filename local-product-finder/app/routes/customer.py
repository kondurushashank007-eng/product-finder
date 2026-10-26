from flask import (
    Blueprint, render_template, request, current_app, redirect, url_for
)
from app.models import Shop, Product
from app.services.distance import get_shop_open_status

bp = Blueprint("customer", __name__)

@bp.route("/")
def home():
    # Retrieve user location from query or cookie/session or default config
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    location_name = request.args.get("location_name", "").strip()

    if user_lat is None or user_lng is None:
        user_lat = current_app.config.get("DEFAULT_USER_LAT")
        user_lng = current_app.config.get("DEFAULT_USER_LNG")
        if not location_name:
            location_name = current_app.config.get("DEFAULT_USER_CITY", "San Francisco, CA")

    # Fetch featured shops with distance
    shops = Shop.get_all(user_lat=user_lat, user_lng=user_lng)
    categories = Product.get_distinct_categories()
    featured_brands = Product.get_distinct_brands()[:8]

    return render_template(
        "customer/home.html",
        shops=shops[:4],
        categories=categories,
        featured_brands=featured_brands,
        user_lat=user_lat,
        user_lng=user_lng,
        location_name=location_name
    )

@bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    brand = request.args.get("brand", "").strip()
    barcode = request.args.get("barcode", "").strip()
    min_price = request.args.get("min_price", type=float)
    max_price = request.args.get("max_price", type=float)
    in_stock_only = request.args.get("in_stock") in ["1", "true", "True", "on"]
    sort_by = request.args.get("sort_by", "distance")
    radius_km = request.args.get("radius", type=float)
    page = request.args.get("page", 1, type=int)
    page_size = current_app.config.get("ITEMS_PER_PAGE", 12)

    # Location
    user_lat = request.args.get("lat", type=float)
    user_lng = request.args.get("lng", type=float)
    location_name = request.args.get("location_name", "").strip()

    # Fallback default location if not provided
    if user_lat is None or user_lng is None:
        user_lat = current_app.config.get("DEFAULT_USER_LAT")
        user_lng = current_app.config.get("DEFAULT_USER_LNG")
        if not location_name:
            location_name = current_app.config.get("DEFAULT_USER_CITY", "San Francisco, CA")

    search_result = Product.search_customer_products(
        query=query if query else None,
        category=category if category else None,
        brand=brand if brand else None,
        barcode=barcode if barcode else None,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        user_lat=user_lat,
        user_lng=user_lng,
        max_distance_km=radius_km,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )

    all_categories = Product.get_distinct_categories()
    all_brands = Product.get_distinct_brands()

    return render_template(
        "customer/search.html",
        results=search_result["items"],
        total_count=search_result["total_count"],
        page=search_result["page"],
        total_pages=search_result["total_pages"],
        has_next=search_result["has_next"],
        has_prev=search_result["has_prev"],
        suggestions=search_result["suggestions"],
        query=query,
        category=category,
        brand=brand,
        barcode=barcode,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sort_by=sort_by,
        radius=radius_km,
        user_lat=user_lat,
        user_lng=user_lng,
        location_name=location_name,
        all_categories=all_categories,
        all_brands=all_brands
    )

@bp.route("/shop/<slug>")
def shop_details(slug):
    shop_row = Shop.get_by_slug(slug)
    if not shop_row:
        return render_template("customer/404.html", message="Shop not found"), 404

    shop = dict(shop_row)
    shop["hours_info"] = get_shop_open_status(shop.get("opening_hours_json"))

    # Compute distance if user location provided
    user_lat = request.args.get("lat", type=float) or current_app.config.get("DEFAULT_USER_LAT")
    user_lng = request.args.get("lng", type=float) or current_app.config.get("DEFAULT_USER_LNG")
    
    from app.services.distance import haversine_distance, format_distance
    if user_lat and user_lng:
        dist = haversine_distance(user_lat, user_lng, shop["latitude"], shop["longitude"])
        shop["distance_km"] = dist
        shop["distance_text"] = format_distance(dist)
    else:
        shop["distance_km"] = None
        shop["distance_text"] = None

    # In-shop inventory search & filter
    item_search = request.args.get("q", "").strip()
    item_category = request.args.get("cat", "").strip() or None

    products = Product.get_shop_inventory(
        shop_id=shop["id"],
        published_only=True,
        search_query=item_search,
        category=item_category
    )

    # Categories specific to this shop
    shop_categories = sorted(list(set(p["category"] for p in products if p.get("category"))))

    # Parse schedule for weekly display table
    import json
    schedule_dict = {}
    if shop.get("opening_hours_json"):
        try:
            schedule_dict = json.loads(shop["opening_hours_json"])
        except Exception:
            schedule_dict = {}

    return render_template(
        "customer/shop.html",
        shop=shop,
        products=products,
        shop_categories=shop_categories,
        selected_category=item_category,
        item_search=item_search,
        schedule_dict=schedule_dict,
        user_lat=user_lat,
        user_lng=user_lng
    )

@bp.route("/about")
def about():
    return render_template("customer/about.html")

@bp.route("/contact")
def contact():
    return render_template("customer/contact.html")
