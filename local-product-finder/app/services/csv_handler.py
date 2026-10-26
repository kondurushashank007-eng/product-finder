import csv
import io

REQUIRED_COLUMNS = ["name", "category", "price", "stock_quantity"]
OPTIONAL_COLUMNS = ["brand", "size", "barcode", "description"]
ALL_COLUMNS = ["name", "brand", "category", "size", "barcode", "price", "stock_quantity", "description"]

SAMPLE_CSV_CONTENT = """name,brand,category,size,barcode,price,stock_quantity,description
Organic Whole Milk,Organic Valley,Dairy,1L,7350053850011,4.49,15,Fresh certified organic whole pasteurized milk
Basmati Rice Royal Blend,Royal,Groceries,1 kg,8901234567891,3.99,20,Premium long-grain aromatic aged basmati rice
USB-C Fast Charger 30W,Anker,Electronics,Compact,0123456789012,18.50,8,PowerPort III 30W high speed USB-C charger
Paracetamol 500mg,Panadol,Health,24 tabs,5012345678903,3.25,35,Fast pain and fever relief caplets
Cordless Drill Driver 12V,DeWalt,Hardware,Kit,8859112345674,49.99,4,12V MAX cordless drill with battery and charger
"""

def parse_and_validate_csv(csv_file_stream_or_text):
    """
    Parses a CSV file and validates each row.
    Returns:
    {
        "valid_rows": [...],
        "invalid_rows": [{"row_index": 2, "errors": [...], "data": {...}}],
        "total_rows": int,
        "valid_count": int,
        "invalid_count": int
    }
    """
    if isinstance(csv_file_stream_or_text, str):
        stream = io.StringIO(csv_file_stream_or_text)
    else:
        # File stream (bytes or text)
        content = csv_file_stream_or_text.read()
        if isinstance(content, bytes):
            # Try utf-8, fallback to latin-1
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
        else:
            text = str(content)
        stream = io.StringIO(text)

    reader = csv.DictReader(stream)
    
    # Check headers
    if not reader.fieldnames:
        return {
            "error": "The uploaded file is empty or missing headers.",
            "valid_rows": [],
            "invalid_rows": [],
            "total_rows": 0,
            "valid_count": 0,
            "invalid_count": 0
        }

    # Normalize fieldnames (lowercase and strip)
    clean_fieldnames = {f: f.strip().lower().replace(" ", "_") for f in reader.fieldnames if f}
    
    # Check required columns
    missing_required = []
    for req in REQUIRED_COLUMNS:
        if req not in clean_fieldnames.values():
            missing_required.append(req)

    if missing_required:
        return {
            "error": f"Missing required CSV column(s): {', '.join(missing_required)}. Required headers are: {', '.join(REQUIRED_COLUMNS)}.",
            "valid_rows": [],
            "invalid_rows": [],
            "total_rows": 0,
            "valid_count": 0,
            "invalid_count": 0
        }

    valid_rows = []
    invalid_rows = []

    for index, raw_row in enumerate(reader, start=2): # Line 1 is header
        # Normalize keys in raw_row
        row = {}
        for original_key, val in raw_row.items():
            if original_key and original_key in clean_fieldnames:
                row[clean_fieldnames[original_key]] = (val or "").strip()

        errors = []

        # Validate name
        name = row.get("name", "").strip()
        if not name:
            errors.append("Product name is required.")
        elif len(name) > 200:
            errors.append("Product name cannot exceed 200 characters.")

        # Validate category
        category = row.get("category", "").strip()
        if not category:
            errors.append("Category is required.")

        # Validate price
        price_raw = row.get("price", "").replace("$", "").replace("€", "").replace("£", "").strip()
        price = None
        try:
            price = float(price_raw)
            if price < 0:
                errors.append("Price cannot be negative.")
            else:
                price = round(price, 2)
        except (ValueError, TypeError):
            errors.append(f"Invalid price value '{price_raw}'. Must be a valid positive number.")

        # Validate stock_quantity
        stock_raw = row.get("stock_quantity", "").strip()
        stock = None
        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock quantity cannot be negative.")
        except (ValueError, TypeError):
            errors.append(f"Invalid stock quantity '{stock_raw}'. Must be an integer >= 0.")

        # Barcode
        barcode = row.get("barcode", "").strip()
        if barcode and len(barcode) > 50:
            errors.append("Barcode is too long (max 50 chars).")

        brand = row.get("brand", "").strip()
        size = row.get("size", "").strip()
        description = row.get("description", "").strip()

        cleaned_item = {
            "name": name,
            "brand": brand,
            "category": category,
            "size": size,
            "barcode": barcode,
            "price": price,
            "stock_quantity": stock,
            "description": description
        }

        if errors:
            invalid_rows.append({
                "row_number": index,
                "data": cleaned_item,
                "errors": errors
            })
        else:
            valid_rows.append(cleaned_item)

    return {
        "error": None,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "total_rows": len(valid_rows) + len(invalid_rows),
        "valid_count": len(valid_rows),
        "invalid_count": len(invalid_rows)
    }

def export_products_to_csv(products_list):
    """
    Exports a list of product dictionaries or sqlite rows to CSV string.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=ALL_COLUMNS)
    writer.writeheader()

    for p in products_list:
        writer.writerow({
            "name": p["name"],
            "brand": p.get("brand", "") or "",
            "category": p["category"],
            "size": p.get("size", "") or "",
            "barcode": p.get("barcode", "") or "",
            "price": f"{p['price']:.2f}",
            "stock_quantity": p["stock_quantity"],
            "description": p.get("description", "") or ""
        })

    return output.getvalue()
