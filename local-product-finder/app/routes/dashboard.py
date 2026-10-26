import json
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, g, jsonify, Response, current_app
)
from app.routes.auth import login_required, shop_owner_required
from app.models import Product, Shop
from app.services.csv_handler import parse_and_validate_csv, export_products_to_csv, SAMPLE_CSV_CONTENT

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@bp.before_request
@login_required
@shop_owner_required
def dashboard_guard():
    # Enforces login and attaches g.current_shop
    pass

@bp.route("/")
def index():
    shop = g.current_shop
    status_filter = request.args.get("status", "all")
    search_query = request.args.get("q", "").strip()

    metrics = Product.get_shop_metrics(shop["id"])
    inventory = Product.get_shop_inventory(
        shop_id=shop["id"],
        published_only=False,
        search_query=search_query
    )

    # Filter by stock status if requested
    filtered_inventory = []
    for item in inventory:
        if status_filter == "in_stock" and item["stock_info"]["code"] != "in_stock":
            continue
        elif status_filter == "low_stock" and item["stock_info"]["code"] != "low_stock":
            continue
        elif status_filter == "out_of_stock" and item["stock_info"]["code"] != "out_of_stock":
            continue
        elif status_filter == "draft" and item["is_published"] != 0:
            continue
        filtered_inventory.append(item)

    # Low stock items for alert section
    low_stock_items = [item for item in inventory if item["stock_info"]["code"] in ["low_stock", "out_of_stock"]]

    return render_template(
        "dashboard/index.html",
        shop=shop,
        metrics=metrics,
        inventory=filtered_inventory,
        low_stock_items=low_stock_items[:5],
        status_filter=status_filter,
        search_query=search_query
    )

@bp.route("/product/add", methods=["GET", "POST"])
def add_product():
    shop = g.current_shop

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        category = request.form.get("category", "").strip()
        size = request.form.get("size", "").strip()
        barcode = request.form.get("barcode", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock_quantity", "").strip()
        description = request.form.get("description", "").strip()
        is_published = 1 if request.form.get("is_published") == "1" else 0

        errors = []
        if not name:
            errors.append("Product name is required.")
        if not category:
            errors.append("Category is required.")

        price = None
        try:
            price = float(price_raw)
            if price < 0:
                errors.append("Price must be a positive number.")
        except (ValueError, TypeError):
            errors.append("Valid price number is required.")

        stock = None
        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock quantity must be a non-negative integer.")
        except (ValueError, TypeError):
            errors.append("Valid integer stock quantity is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("dashboard/product_form.html", product=request.form, is_edit=False)

        try:
            Product.create(
                shop_id=shop["id"],
                name=name,
                brand=brand,
                category=category,
                size=size,
                barcode=barcode,
                price=price,
                stock_quantity=stock,
                description=description,
                is_published=is_published,
                is_demo=0
            )
            flash(f"Product '{name}' added successfully to your inventory!", "success")
            return redirect(url_for("dashboard.index"))
        except Exception as e:
            flash(f"Error adding product: {str(e)}", "danger")
            return render_template("dashboard/product_form.html", product=request.form, is_edit=False)

    return render_template("dashboard/product_form.html", product={}, is_edit=False)

@bp.route("/product/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    shop = g.current_shop
    product = Product.get_by_id(product_id)

    if not product or product["shop_id"] != shop["id"]:
        flash("Product not found or access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        category = request.form.get("category", "").strip()
        size = request.form.get("size", "").strip()
        barcode = request.form.get("barcode", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock_quantity", "").strip()
        description = request.form.get("description", "").strip()
        is_published = 1 if request.form.get("is_published") == "1" else 0

        errors = []
        if not name:
            errors.append("Product name is required.")
        if not category:
            errors.append("Category is required.")

        price = None
        try:
            price = float(price_raw)
            if price < 0:
                errors.append("Price must be a positive number.")
        except (ValueError, TypeError):
            errors.append("Valid price number is required.")

        stock = None
        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock quantity must be a non-negative integer.")
        except (ValueError, TypeError):
            errors.append("Valid integer stock quantity is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("dashboard/product_form.html", product=request.form, is_edit=True, product_id=product_id)

        try:
            Product.update(
                product_id=product_id,
                name=name,
                brand=brand,
                category=category,
                size=size,
                barcode=barcode,
                price=price,
                stock_quantity=stock,
                description=description,
                is_published=is_published
            )
            flash(f"Product '{name}' updated successfully!", "success")
            return redirect(url_for("dashboard.index"))
        except Exception as e:
            flash(f"Error updating product: {str(e)}", "danger")
            return render_template("dashboard/product_form.html", product=request.form, is_edit=True, product_id=product_id)

    return render_template("dashboard/product_form.html", product=product, is_edit=True, product_id=product_id)

@bp.route("/product/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    shop = g.current_shop
    product = Product.get_by_id(product_id)

    if not product or product["shop_id"] != shop["id"]:
        flash("Product not found or access denied.", "danger")
        return redirect(url_for("dashboard.index"))

    name = product["name"]
    Product.delete(product_id, shop["id"])
    flash(f"Product '{name}' removed from your inventory.", "info")
    return redirect(url_for("dashboard.index"))

@bp.route("/product/<int:product_id>/stock", methods=["POST"])
def update_stock(product_id):
    shop = g.current_shop
    product = Product.get_by_id(product_id)

    if not product or product["shop_id"] != shop["id"]:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "Unauthorized"}), 403
        flash("Unauthorized", "danger")
        return redirect(url_for("dashboard.index"))

    delta = request.form.get("delta", type=int)
    new_quantity = request.form.get("quantity", type=int)

    if delta is not None:
        target_qty = max(0, product["stock_quantity"] + delta)
    elif new_quantity is not None:
        target_qty = max(0, new_quantity)
    else:
        target_qty = product["stock_quantity"]

    Product.update_stock(product_id, shop["id"], target_qty)
    
    # Re-fetch updated item
    updated = Product.get_by_id(product_id)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "product_id": product_id,
            "new_quantity": updated["stock_quantity"],
            "status_code": updated["stock_info"]["code"],
            "status_label": updated["stock_info"]["label"],
            "badge_class": updated["stock_info"]["badge_class"],
            "relative_updated": updated["relative_updated"]
        })

    flash(f"Stock for '{product['name']}' updated to {target_qty}.", "success")
    return redirect(url_for("dashboard.index"))

@bp.route("/publish-all", methods=["POST"])
def publish_all():
    shop = g.current_shop
    Product.publish_all_for_shop(shop["id"])
    flash("All inventory changes confirmed and published! Your listings are now live for customers.", "success")
    return redirect(url_for("dashboard.index"))

@bp.route("/import-csv", methods=["GET", "POST"])
def import_csv():
    shop = g.current_shop

    if request.method == "POST":
        # Check if confirming previously validated rows
        confirm_import = request.form.get("confirm_import") == "1"
        if confirm_import:
            raw_json = request.form.get("rows_json", "[]")
            try:
                rows_to_insert = json.loads(raw_json)
                inserted_count = 0
                for item in rows_to_insert:
                    Product.create(
                        shop_id=shop["id"],
                        name=item["name"],
                        brand=item.get("brand", ""),
                        category=item["category"],
                        size=item.get("size", ""),
                        barcode=item.get("barcode", ""),
                        price=float(item["price"]),
                        stock_quantity=int(item["stock_quantity"]),
                        description=item.get("description", ""),
                        is_published=1,
                        is_demo=0
                    )
                    inserted_count += 1
                flash(f"Successfully imported {inserted_count} products into your inventory!", "success")
                return redirect(url_for("dashboard.index"))
            except Exception as e:
                flash(f"Failed to import products: {str(e)}", "danger")

        # Initial upload & validation
        if "csv_file" not in request.files:
            flash("Please choose a CSV file to upload.", "warning")
            return render_template("dashboard/import_csv.html", shop=shop)

        file = request.files["csv_file"]
        if file.filename == "":
            flash("No file selected.", "warning")
            return render_template("dashboard/import_csv.html", shop=shop)

        if not file.filename.lower().endswith(".csv"):
            flash("Please upload a file with a .csv extension.", "danger")
            return render_template("dashboard/import_csv.html", shop=shop)

        result = parse_and_validate_csv(file)

        if result.get("error"):
            flash(result["error"], "danger")
            return render_template("dashboard/import_csv.html", shop=shop)

        return render_template(
            "dashboard/import_csv.html",
            shop=shop,
            preview_mode=True,
            valid_rows=result["valid_rows"],
            invalid_rows=result["invalid_rows"],
            total_rows=result["total_rows"],
            valid_count=result["valid_count"],
            invalid_count=result["invalid_count"],
            rows_json=json.dumps(result["valid_rows"])
        )

    return render_template("dashboard/import_csv.html", shop=shop)

@bp.route("/export-csv")
def export_csv():
    shop = g.current_shop
    products = Product.get_shop_inventory(shop["id"], published_only=False)
    csv_text = export_products_to_csv(products)
    
    filename = f"{shop['slug']}-inventory.csv"
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@bp.route("/sample-csv")
def download_sample_csv():
    return Response(
        SAMPLE_CSV_CONTENT,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=sample_inventory.csv"}
    )

@bp.route("/settings", methods=["GET", "POST"])
def settings():
    shop = g.current_shop

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        address = request.form.get("address", "").strip()
        city = request.form.get("city", "").strip()
        postal_code = request.form.get("postal_code", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        website = request.form.get("website", "").strip()

        lat_raw = request.form.get("latitude")
        lng_raw = request.form.get("longitude")

        errors = []
        if not name:
            errors.append("Shop name is required.")
        if not address or not city:
            errors.append("Address and City are required.")

        lat = None
        lng = None
        try:
            lat = float(lat_raw)
            lng = float(lng_raw)
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                errors.append("Coordinates are out of range.")
        except (ValueError, TypeError):
            errors.append("Valid decimal latitude and longitude are required.")

        # Opening hours json from form
        days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        schedule = {}
        for d in days:
            closed = request.form.get(f"{d}_closed") == "1"
            open_t = request.form.get(f"{d}_open", "09:00")
            close_t = request.form.get(f"{d}_close", "18:00")
            schedule[d] = {
                "open": open_t,
                "close": close_t,
                "closed": closed
            }
        hours_json = json.dumps(schedule)

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("dashboard/shop_settings.html", shop=request.form, schedule=schedule)

        try:
            Shop.update_profile(
                shop_id=shop["id"],
                name=name,
                description=description,
                category=category,
                address=address,
                city=city,
                postal_code=postal_code,
                latitude=lat,
                longitude=lng,
                phone=phone,
                email=email,
                website=website,
                opening_hours_json=hours_json
            )
            flash("Shop profile and hours updated successfully!", "success")
            return redirect(url_for("dashboard.settings"))
        except Exception as e:
            flash(f"Error updating shop profile: {str(e)}", "danger")

    # Load schedule dict
    schedule = {}
    if shop.get("opening_hours_json"):
        try:
            schedule = json.loads(shop["opening_hours_json"])
        except Exception:
            schedule = {}

    return render_template("dashboard/shop_settings.html", shop=shop, schedule=schedule)
