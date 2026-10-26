from flask import Blueprint, request, jsonify, current_app
from app.services.ai_search import parse_natural_language_query
from app.models import Product

bp = Blueprint("api", __name__, url_prefix="/api")

# Pre-mapped local neighborhoods for instant zero-dependency geocoding
GEOCODE_LOOKUP = {
    "castro": (37.7618, -122.4350, "Castro, San Francisco, CA"),
    "mission": (37.7599, -122.4148, "Mission District, San Francisco, CA"),
    "market": (37.7749, -122.4194, "Market St, San Francisco, CA"),
    "downtown": (37.7879, -122.4074, "Downtown San Francisco, CA"),
    "soma": (37.7785, -122.4056, "SoMa, San Francisco, CA"),
    "richmond": (37.7797, -122.4746, "Richmond District, San Francisco, CA"),
    "sunset": (37.7534, -122.4941, "Sunset District, San Francisco, CA"),
    "marina": (37.8037, -122.4368, "Marina District, San Francisco, CA"),
    "north beach": (37.8000, -122.4080, "North Beach, San Francisco, CA"),
    "haight": (37.7692, -122.4481, "Haight-Ashbury, San Francisco, CA"),
    "oakland": (37.8044, -122.2712, "Oakland, CA"),
    "berkeley": (37.8715, -122.2730, "Berkeley, CA"),
    "94114": (37.7618, -122.4350, "San Francisco, CA 94114"),
    "94102": (37.7712, -122.4238, "San Francisco, CA 94102"),
    "94103": (37.7785, -122.4056, "San Francisco, CA 94103"),
    "94110": (37.7599, -122.4148, "San Francisco, CA 94110")
}

@bp.route("/ai-search", methods=["POST"])
def ai_search():
    data = request.get_json(silent=True) or {}
    query_text = (data.get("query") or "").strip()
    user_lat = data.get("lat")
    user_lng = data.get("lng")

    try:
        user_lat = float(user_lat) if user_lat is not None else current_app.config.get("DEFAULT_USER_LAT")
        user_lng = float(user_lng) if user_lng is not None else current_app.config.get("DEFAULT_USER_LNG")
    except (ValueError, TypeError):
        user_lat = current_app.config.get("DEFAULT_USER_LAT")
        user_lng = current_app.config.get("DEFAULT_USER_LNG")

    if not query_text:
        return jsonify({"success": False, "error": "Query text is required."}), 400

    parsed = parse_natural_language_query(query_text)

    # If ambiguous, prompt user
    if parsed.get("clarification"):
        return jsonify({
            "success": True,
            "is_ambiguous": True,
            "clarification": parsed["clarification"],
            "explanation": parsed["explanation"],
            "parsed": parsed
        })

    # Search database using parsed parameters
    search_result = Product.search_customer_products(
        query=parsed.get("product_keyword"),
        category=parsed.get("category"),
        brand=parsed.get("brand"),
        max_price=parsed.get("max_price"),
        in_stock_only=parsed.get("in_stock_only", False),
        user_lat=user_lat,
        user_lng=user_lng,
        sort_by=parsed.get("sort_by", "distance"),
        page=1,
        page_size=8
    )

    # Build query params for search page redirect
    from urllib.parse import urlencode
    redirect_params = {
        "q": parsed.get("product_keyword") or "",
        "sort_by": parsed.get("sort_by", "distance"),
        "lat": user_lat,
        "lng": user_lng
    }
    if parsed.get("brand"):
        redirect_params["brand"] = parsed["brand"]
    if parsed.get("category"):
        redirect_params["category"] = parsed["category"]
    if parsed.get("max_price"):
        redirect_params["max_price"] = parsed["max_price"]
    if parsed.get("in_stock_only"):
        redirect_params["in_stock"] = "1"

    redirect_url = f"/search?{urlencode(redirect_params)}"

    return jsonify({
        "success": True,
        "is_ambiguous": False,
        "parsed": parsed,
        "explanation": parsed["explanation"],
        "total_results": search_result["total_count"],
        "results": search_result["items"],
        "suggestions": search_result["suggestions"],
        "redirect_url": redirect_url
    })

@bp.route("/geocode", methods=["POST"])
def geocode():
    data = request.get_json(silent=True) or {}
    address = (data.get("address") or "").strip().lower()

    if not address:
        return jsonify({"success": False, "error": "Address is required"}), 400

    for key, (lat, lng, formatted) in GEOCODE_LOOKUP.items():
        if key in address:
            return jsonify({
                "success": True,
                "lat": lat,
                "lng": lng,
                "formatted_address": formatted
            })

    # Default fallback to center of demo city
    return jsonify({
        "success": True,
        "lat": current_app.config.get("DEFAULT_USER_LAT", 37.7749),
        "lng": current_app.config.get("DEFAULT_USER_LNG", -122.4194),
        "formatted_address": f"{address.title()} (Estimated SF coordinates)"
    })
