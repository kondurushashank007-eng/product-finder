from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import get_db
from app.services.distance import (
    haversine_distance, 
    format_distance, 
    format_relative_time, 
    is_inventory_stale,
    get_shop_open_status
)

def compute_stock_status(quantity):
    if quantity <= 0:
        return {
            "code": "out_of_stock",
            "label": "Out of stock",
            "badge_class": "badge-danger",
            "is_available": False
        }
    elif 1 <= quantity <= 5:
        return {
            "code": "low_stock",
            "label": "Low stock",
            "badge_class": "badge-warning",
            "is_available": True
        }
    else:
        return {
            "code": "in_stock",
            "label": "In stock",
            "badge_class": "badge-success",
            "is_available": True
        }

class User:
    @staticmethod
    def create(email, password, name, role="shop_owner"):
        db = get_db()
        hashed = generate_password_hash(password)
        cursor = db.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), hashed, name.strip(), role)
        )
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(user_id):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    @staticmethod
    def get_by_email(email):
        db = get_db()
        return db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),)).fetchone()

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)


class Shop:
    @staticmethod
    def create(owner_id, name, slug, description, category, address, city, postal_code, 
               latitude, longitude, phone, email, website, opening_hours_json, is_demo=0):
        db = get_db()
        cursor = db.execute("""
            INSERT INTO shops (
                owner_id, name, slug, description, category, address, city, postal_code,
                latitude, longitude, phone, email, website, opening_hours_json, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            owner_id, name.strip(), slug.strip(), description, category, address.strip(),
            city.strip(), postal_code, float(latitude), float(longitude),
            phone, email, website, opening_hours_json, is_demo
        ))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(shop_id):
        db = get_db()
        return db.execute("SELECT * FROM shops WHERE id = ?", (shop_id,)).fetchone()

    @staticmethod
    def get_by_slug(slug):
        db = get_db()
        return db.execute("SELECT * FROM shops WHERE slug = ?", (slug,)).fetchone()

    @staticmethod
    def get_by_owner_id(owner_id):
        db = get_db()
        return db.execute("SELECT * FROM shops WHERE owner_id = ?", (owner_id,)).fetchone()

    @staticmethod
    def get_all(user_lat=None, user_lng=None):
        db = get_db()
        rows = db.execute("SELECT * FROM shops WHERE is_active = 1 ORDER BY id ASC").fetchall()
        shops = []
        for row in rows:
            shop = dict(row)
            if user_lat is not None and user_lng is not None:
                dist = haversine_distance(user_lat, user_lng, shop["latitude"], shop["longitude"])
                shop["distance_km"] = dist
                shop["distance_text"] = format_distance(dist)
            else:
                shop["distance_km"] = None
                shop["distance_text"] = None

            shop["hours_info"] = get_shop_open_status(shop.get("opening_hours_json"))
            shops.append(shop)

        if user_lat is not None and user_lng is not None:
            shops.sort(key=lambda s: (s["distance_km"] if s["distance_km"] is not None else 99999))

        return shops

    @staticmethod
    def update_profile(shop_id, name, description, category, address, city, postal_code,
                       latitude, longitude, phone, email, website, opening_hours_json):
        db = get_db()
        db.execute("""
            UPDATE shops SET
                name = ?, description = ?, category = ?, address = ?, city = ?, postal_code = ?,
                latitude = ?, longitude = ?, phone = ?, email = ?, website = ?,
                opening_hours_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            name.strip(), description, category, address.strip(), city.strip(), postal_code,
            float(latitude), float(longitude), phone, email, website, opening_hours_json, shop_id
        ))
        db.commit()


class Product:
    @staticmethod
    def create(shop_id, name, brand, category, size, barcode, price, stock_quantity, 
               description="", is_published=1, is_demo=0):
        db = get_db()
        cursor = db.execute("""
            INSERT INTO products (
                shop_id, name, brand, category, size, barcode, price, stock_quantity,
                description, is_published, is_demo, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            shop_id, name.strip(), (brand or "").strip(), category.strip(),
            (size or "").strip(), (barcode or "").strip(), float(price),
            int(stock_quantity), description.strip(), is_published, is_demo
        ))
        db.commit()
        return cursor.lastrowid

    @staticmethod
    def get_by_id(product_id):
        db = get_db()
        row = db.execute("""
            SELECT p.*, s.name as shop_name, s.slug as shop_slug, s.address as shop_address,
                   s.latitude as shop_lat, s.longitude as shop_lng, s.phone as shop_phone,
                   s.is_demo as shop_is_demo
            FROM products p
            JOIN shops s ON p.shop_id = s.id
            WHERE p.id = ?
        """, (product_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["stock_info"] = compute_stock_status(item["stock_quantity"])
        item["relative_updated"] = format_relative_time(item["updated_at"])
        item["is_stale"] = is_inventory_stale(item["updated_at"])
        return item

    @staticmethod
    def update(product_id, name, brand, category, size, barcode, price, stock_quantity, description, is_published=1):
        db = get_db()
        db.execute("""
            UPDATE products SET
                name = ?, brand = ?, category = ?, size = ?, barcode = ?,
                price = ?, stock_quantity = ?, description = ?, is_published = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            name.strip(), (brand or "").strip(), category.strip(),
            (size or "").strip(), (barcode or "").strip(), float(price),
            int(stock_quantity), description.strip(), is_published, product_id
        ))
        db.commit()

    @staticmethod
    def delete(product_id, shop_id):
        db = get_db()
        cursor = db.execute("DELETE FROM products WHERE id = ? AND shop_id = ?", (product_id, shop_id))
        db.commit()
        return cursor.rowcount > 0

    @staticmethod
    def update_stock(product_id, shop_id, new_quantity):
        db = get_db()
        db.execute("""
            UPDATE products SET
                stock_quantity = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND shop_id = ?
        """, (max(0, int(new_quantity)), product_id, shop_id))
        db.commit()

    @staticmethod
    def publish_all_for_shop(shop_id):
        db = get_db()
        db.execute("""
            UPDATE products SET
                is_published = 1, updated_at = CURRENT_TIMESTAMP
            WHERE shop_id = ?
        """, (shop_id,))
        db.commit()

    @staticmethod
    def get_shop_inventory(shop_id, published_only=True, search_query="", category=None):
        db = get_db()
        sql = "SELECT * FROM products WHERE shop_id = ?"
        params = [shop_id]

        if published_only:
            sql += " AND is_published = 1"
        if search_query:
            sql += " AND (name LIKE ? OR brand LIKE ? OR barcode LIKE ?)"
            term = f"%{search_query.strip()}%"
            params.extend([term, term, term])
        if category:
            sql += " AND category = ?"
            params.append(category)

        sql += " ORDER BY name ASC"
        rows = db.execute(sql, params).fetchall()

        items = []
        for r in rows:
            p = dict(r)
            p["stock_info"] = compute_stock_status(p["stock_quantity"])
            p["relative_updated"] = format_relative_time(p["updated_at"])
            p["is_stale"] = is_inventory_stale(p["updated_at"])
            items.append(p)
        return items

    @staticmethod
    def get_shop_metrics(shop_id):
        db = get_db()
        rows = db.execute("SELECT stock_quantity, updated_at, price FROM products WHERE shop_id = ?", (shop_id,)).fetchall()
        total_products = len(rows)
        in_stock = sum(1 for r in rows if r["stock_quantity"] > 5)
        low_stock = sum(1 for r in rows if 1 <= r["stock_quantity"] <= 5)
        out_of_stock = sum(1 for r in rows if r["stock_quantity"] == 0)
        
        last_updated = None
        if rows:
            # find latest updated_at
            latest_dt = max((r["updated_at"] for r in rows if r["updated_at"]), default=None)
            last_updated = format_relative_time(latest_dt)

        return {
            "total_products": total_products,
            "in_stock": in_stock,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "last_updated": last_updated or "Never"
        }

    @staticmethod
    def get_distinct_categories():
        db = get_db()
        rows = db.execute("SELECT DISTINCT category FROM products WHERE is_published = 1 AND category != '' ORDER BY category ASC").fetchall()
        return [r["category"] for r in rows]

    @staticmethod
    def get_distinct_brands():
        db = get_db()
        rows = db.execute("SELECT DISTINCT brand FROM products WHERE is_published = 1 AND brand IS NOT NULL AND brand != '' ORDER BY brand ASC").fetchall()
        return [r["brand"] for r in rows]

    @staticmethod
    def search_customer_products(
        query=None,
        category=None,
        brand=None,
        barcode=None,
        min_price=None,
        max_price=None,
        in_stock_only=False,
        user_lat=None,
        user_lng=None,
        max_distance_km=None,
        sort_by="distance",
        page=1,
        page_size=12
    ):
        """
        Customer search engine: searches across published products and active shops.
        Calculates real-time distance and opening status.
        Supports sorting by distance, price (asc/desc), and stock availability.
        Returns: {
            "items": [...],
            "total_count": int,
            "page": int,
            "total_pages": int,
            "page_size": int,
            "has_next": bool,
            "has_prev": bool,
            "suggestions": [...]
        }
        """
        db = get_db()

        # Build base SQL query
        sql_select = """
            SELECT p.*,
                   s.name as shop_name, s.slug as shop_slug, s.address as shop_address,
                   s.city as shop_city, s.postal_code as shop_postal_code,
                   s.latitude as shop_lat, s.longitude as shop_lng,
                   s.phone as shop_phone, s.opening_hours_json,
                   s.is_demo as shop_is_demo
            FROM products p
            JOIN shops s ON p.shop_id = s.id
            WHERE p.is_published = 1 AND s.is_active = 1
        """
        params = []

        # Barcode exact or partial match
        if barcode:
            sql_select += " AND p.barcode LIKE ?"
            params.append(f"%{barcode.strip()}%")

        # Category filter
        if category:
            sql_select += " AND p.category = ?"
            params.append(category.strip())

        # Brand filter (can be comma-separated or single)
        if brand:
            brands = [b.strip() for b in brand.split(",") if b.strip()]
            if len(brands) == 1:
                sql_select += " AND LOWER(p.brand) = LOWER(?)"
                params.append(brands[0])
            elif len(brands) > 1:
                placeholders = ",".join(["?"] * len(brands))
                sql_select += f" AND LOWER(p.brand) IN ({placeholders})"
                params.extend([b.lower() for b in brands])

        # Price range
        if min_price is not None:
            try:
                sql_select += " AND p.price >= ?"
                params.append(float(min_price))
            except ValueError:
                pass

        if max_price is not None:
            try:
                sql_select += " AND p.price <= ?"
                params.append(float(max_price))
            except ValueError:
                pass

        # In-stock condition
        if in_stock_only:
            sql_select += " AND p.stock_quantity > 0"

        # General text query matching name, brand, category, barcode, or shop name
        if query:
            clean_q = query.strip()
            tokens = [t.strip() for t in clean_q.split() if t.strip()]
            if tokens:
                for token in tokens:
                    sql_select += """ AND (
                        p.name LIKE ? OR 
                        p.brand LIKE ? OR 
                        p.category LIKE ? OR 
                        p.barcode LIKE ? OR 
                        s.name LIKE ?
                    )"""
                    t_param = f"%{token}%"
                    params.extend([t_param, t_param, t_param, t_param, t_param])

        rows = db.execute(sql_select, params).fetchall()

        # Compute distance and open status for each result
        all_results = []
        for r in rows:
            item = dict(r)
            item["stock_info"] = compute_stock_status(item["stock_quantity"])
            item["relative_updated"] = format_relative_time(item["updated_at"])
            item["is_stale"] = is_inventory_stale(item["updated_at"])
            item["shop_hours_info"] = get_shop_open_status(item.get("opening_hours_json"))

            if user_lat is not None and user_lng is not None:
                dist = haversine_distance(user_lat, user_lng, item["shop_lat"], item["shop_lng"])
                item["distance_km"] = dist
                item["distance_text"] = format_distance(dist)
            else:
                item["distance_km"] = None
                item["distance_text"] = None

            # Filter by max_distance if specified
            if max_distance_km is not None and item["distance_km"] is not None:
                if item["distance_km"] > float(max_distance_km):
                    continue

            all_results.append(item)

        # Apply sorting
        if sort_by == "price_asc":
            all_results.sort(key=lambda x: (x["price"], x["distance_km"] or 99999))
        elif sort_by == "price_desc":
            all_results.sort(key=lambda x: (-x["price"], x["distance_km"] or 99999))
        elif sort_by == "stock":
            all_results.sort(key=lambda x: (-x["stock_quantity"], x["price"]))
        else:
            # Default: distance (if user location provided) or shop name / relevance
            if user_lat is not None and user_lng is not None:
                all_results.sort(key=lambda x: (x["distance_km"] if x["distance_km"] is not None else 99999, x["price"]))
            else:
                all_results.sort(key=lambda x: (x["name"].lower(), x["price"]))

        total_count = len(all_results)
        total_pages = max(1, (total_count + page_size - 1) // page_size)
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = all_results[start_idx:end_idx]

        # Generate helpful suggestions if 0 results
        suggestions = []
        if total_count == 0:
            if max_distance_km:
                suggestions.append("Try expanding or removing the distance radius limit.")
            if brand:
                suggestions.append("Try clearing the brand filter to see all local alternatives.")
            if category:
                suggestions.append(f"Explore other items in the {category} category.")
            if min_price or max_price:
                suggestions.append("Try adjusting your price range filter.")
            if in_stock_only:
                suggestions.append("Include out-of-stock items to see which shops carry this item normally.")
            if query:
                suggestions.append(f"Check the spelling of '{query}' or try generic keywords (e.g. 'milk' instead of brand).")

        return {
            "items": paginated_items,
            "total_count": total_count,
            "page": page,
            "total_pages": total_pages,
            "page_size": page_size,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "suggestions": suggestions
        }
