import json
import sqlite3
import os
from pathlib import Path
from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "instance" / "local_product_finder.db"))

def seed_database(db_path=None):
    if db_path is None:
        db_path = DATABASE_PATH

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    
    # Ensure tables exist
    from app.db import create_tables
    create_tables(conn)

    cursor = conn.cursor()

    # Check if demo data already seeded
    existing_shops = cursor.execute("SELECT COUNT(*) FROM shops WHERE is_demo = 1").fetchone()[0]
    if existing_shops > 0:
        print(f"Sample database already contains {existing_shops} demo shops. Skipping seed.")
        conn.close()
        return

    print("Seeding sample database with local shops, owners, and inventories...")

    default_password_hash = generate_password_hash("DemoPass123!")

    # 1. Demo Users
    users_data = [
        ("greenvalley@localfinder.demo", default_password_hash, "Sarah Jenkins", "shop_owner"),
        ("cornerstone@localfinder.demo", default_password_hash, "David Martinez", "shop_owner"),
        ("metrotech@localfinder.demo", default_password_hash, "Alex Chen", "shop_owner"),
        ("downware@localfinder.demo", default_password_hash, "Tom Reynolds", "shop_owner")
    ]

    user_ids = {}
    for email, pwd, name, role in users_data:
        cursor.execute(
            "INSERT INTO users (email, password_hash, name, role) VALUES (?, ?, ?, ?)",
            (email, pwd, name, role)
        )
        user_ids[email] = cursor.lastrowid

    # 2. Demo Opening Hours Schedules
    standard_hours = json.dumps({
        "mon": {"open": "08:00", "close": "20:00", "closed": False},
        "tue": {"open": "08:00", "close": "20:00", "closed": False},
        "wed": {"open": "08:00", "close": "20:00", "closed": False},
        "thu": {"open": "08:00", "close": "20:00", "closed": False},
        "fri": {"open": "08:00", "close": "21:00", "closed": False},
        "sat": {"open": "09:00", "close": "21:00", "closed": False},
        "sun": {"open": "09:00", "close": "18:00", "closed": False}
    })

    pharmacy_hours = json.dumps({
        "mon": {"open": "08:30", "close": "20:00", "closed": False},
        "tue": {"open": "08:30", "close": "20:00", "closed": False},
        "wed": {"open": "08:30", "close": "20:00", "closed": False},
        "thu": {"open": "08:30", "close": "20:00", "closed": False},
        "fri": {"open": "08:30", "close": "20:00", "closed": False},
        "sat": {"open": "09:00", "close": "18:00", "closed": False},
        "sun": {"open": "10:00", "close": "17:00", "closed": False}
    })

    tech_hours = json.dumps({
        "mon": {"open": "10:00", "close": "20:00", "closed": False},
        "tue": {"open": "10:00", "close": "20:00", "closed": False},
        "wed": {"open": "10:00", "close": "20:00", "closed": False},
        "thu": {"open": "10:00", "close": "20:00", "closed": False},
        "fri": {"open": "10:00", "close": "20:00", "closed": False},
        "sat": {"open": "10:00", "close": "20:00", "closed": False},
        "sun": {"open": "11:00", "close": "18:00", "closed": False}
    })

    hardware_hours = json.dumps({
        "mon": {"open": "07:30", "close": "19:00", "closed": False},
        "tue": {"open": "07:30", "close": "19:00", "closed": False},
        "wed": {"open": "07:30", "close": "19:00", "closed": False},
        "thu": {"open": "07:30", "close": "19:00", "closed": False},
        "fri": {"open": "07:30", "close": "19:00", "closed": False},
        "sat": {"open": "08:00", "close": "18:00", "closed": False},
        "sun": {"open": "09:00", "close": "17:00", "closed": False}
    })

    # 3. Demo Shops
    shops_data = [
        (
            user_ids["greenvalley@localfinder.demo"],
            "Green Valley Organic Grocers",
            "green-valley-organic-grocers",
            "Independent community grocery store offering organic produce, dairy, freshly baked bread, and sustainable pantry staples.",
            "Groceries & Produce",
            "428 Castro Street",
            "San Francisco",
            "94114",
            37.7618,
            -122.4350,
            "(415) 555-0142",
            "orders@greenvalleyorganic.demo",
            "https://greenvalleyorganic.demo",
            standard_hours,
            1
        ),
        (
            user_ids["cornerstone@localfinder.demo"],
            "Cornerstone Health & Pharmacy",
            "cornerstone-health-pharmacy",
            "Neighborhood pharmacy and health wellness shop carrying over-the-counter medicine, vitamins, first-aid, and personal care.",
            "Health & Pharmacy",
            "1850 Market Street",
            "San Francisco",
            "94102",
            37.7712,
            -122.4238,
            "(415) 555-0189",
            "care@cornerstonepharmacy.demo",
            "https://cornerstonepharmacy.demo",
            pharmacy_hours,
            1
        ),
        (
            user_ids["metrotech@localfinder.demo"],
            "Metro Tech & Gadget Hub",
            "metro-tech-gadget-hub",
            "Local electronics boutique with cables, chargers, audio gear, computer accessories, batteries, and tech repair supplies.",
            "Electronics & Gadgets",
            "742 Mission Street",
            "San Francisco",
            "94103",
            37.7865,
            -122.4042,
            "(415) 555-0210",
            "support@metrotechhub.demo",
            "https://metrotechhub.demo",
            tech_hours,
            1
        ),
        (
            user_ids["downware@localfinder.demo"],
            "Downtown Hardware & Home",
            "downtown-hardware-home",
            "Full-service local hardware store stocked with power tools, electrical supplies, fasteners, plumbing, and home essentials.",
            "Hardware & Home Improvement",
            "1200 Folsom Street",
            "San Francisco",
            "94103",
            37.7745,
            -122.4109,
            "(415) 555-0334",
            "desk@downtownhardware.demo",
            "https://downtownhardware.demo",
            hardware_hours,
            1
        )
    ]

    shop_ids = {}
    for owner_id, name, slug, desc, cat, addr, city, post, lat, lng, ph, em, web, hrs, is_demo in shops_data:
        cursor.execute("""
            INSERT INTO shops (
                owner_id, name, slug, description, category, address, city, postal_code,
                latitude, longitude, phone, email, website, opening_hours_json, is_demo
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, name, slug, desc, cat, addr, city, post, lat, lng, ph, em, web, hrs, is_demo))
        shop_ids[slug] = cursor.lastrowid

    # 4. Demo Products for each shop
    # Columns: shop_id, name, brand, category, size, barcode, price, stock_quantity, description, is_published, is_demo
    products_data = [
        # Green Valley Organic Grocers
        (shop_ids["green-valley-organic-grocers"], "Organic Whole Milk", "Organic Valley", "Dairy", "1L", "7350053850011", 4.49, 14, "Grade A certified organic whole milk in recyclable carton", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Basmati Rice Royal Blend", "Royal", "Groceries", "1 kg", "8901234567891", 3.99, 18, "Naturally aged authentic long grain aromatic basmati rice", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Artisan Sourdough Loaf", "San Francisco Bakery", "Bakery", "500g", "0123456789011", 4.25, 3, "Slow-fermented traditional sourdough loaf baked this morning", 1, 1), # low stock
        (shop_ids["green-valley-organic-grocers"], "Extra Virgin Olive Oil", "California Olive Ranch", "Pantry", "750ml", "0123456789012", 12.99, 8, "Cold pressed 100% California extra virgin olive oil", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Organic Free-Range Brown Eggs", "Vital Farms", "Dairy", "12pk", "0123456789013", 5.49, 0, "Pasture-raised grade A large brown eggs", 1, 1), # out of stock
        (shop_ids["green-valley-organic-grocers"], "Fresh Hass Avocados", "Dole", "Produce", "4pk", "0123456789014", 3.99, 6, "Ripe and ready to eat creamy Hass avocados", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Rolled Oats Whole Grain", "Bob's Red Mill", "Groceries", "1 kg", "0123456789015", 2.89, 15, "Non-GMO Project verified wholesome whole grain rolled oats", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Jasmine Rice Fragrant", "Dynasty", "Groceries", "1 kg", "0123456789016", 3.49, 4, "Fragrant Thai jasmine white rice", 1, 1), # low stock
        (shop_ids["green-valley-organic-grocers"], "Unsweetened Almond Milk", "Almond Breeze", "Dairy", "1L", "0123456789017", 3.79, 10, "Dairy-free, soy-free almond beverage with calcium & vitamin E", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Raw Honeycomb Honey", "Local Bloom", "Pantry", "350g", "0123456789018", 8.50, 2, "Unfiltered raw wildflower honey with edible comb piece", 1, 1), # low stock
        (shop_ids["green-valley-organic-grocers"], "Organic Baby Spinach", "Earthbound Farm", "Produce", "250g", "0123456789019", 2.99, 11, "Pre-washed tender organic baby spinach leaves", 1, 1),
        (shop_ids["green-valley-organic-grocers"], "Greek Yogurt Plain 0%", "Chobani", "Dairy", "907g", "0123456789020", 5.29, 9, "Triple strained high protein non-fat Greek yogurt", 1, 1),

        # Cornerstone Health & Pharmacy
        (shop_ids["cornerstone-health-pharmacy"], "Paracetamol Rapid Release 500mg", "Panadol", "Health & Pharmacy", "24 tabs", "5012345678903", 3.25, 25, "Fast relief of headache, fever, muscle aches and pains", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Vitamin C 1000mg with Rose Hips", "Nature Made", "Health & Pharmacy", "60 caps", "5012345678904", 8.99, 4, "Immune support antioxidant dietary supplement", 1, 1), # low stock
        (shop_ids["cornerstone-health-pharmacy"], "Advanced Hand Sanitizer Gel", "Purell", "Health & Pharmacy", "250ml", "5012345678905", 2.50, 16, "Kills 99.99% of common germs, with moisturizers & aloe", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Digital Fast-Read Oral Thermometer", "Vicks", "Health & Pharmacy", "1 unit", "5012345678906", 14.99, 5, "Accurate temperature reading in under 10 seconds", 1, 1), # low stock
        (shop_ids["cornerstone-health-pharmacy"], "Mineral Sunscreen SPF 50", "La Roche-Posay", "Health & Pharmacy", "150ml", "5012345678907", 18.50, 0, "Broad spectrum water resistant UVA/UVB mineral lotion", 1, 1), # out of stock
        (shop_ids["cornerstone-health-pharmacy"], "Deluxe Emergency First Aid Kit", "Johnson & Johnson", "Health & Pharmacy", "45pc", "5012345678908", 19.99, 7, "Comprehensive compact first aid kit for home, travel, or car", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Ibuprofen Liquid Gels 200mg", "Advil", "Health & Pharmacy", "30 tabs", "5012345678909", 4.50, 20, "Fast liquid relief for pain, inflammation, and headache", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Hydration Electrolyte Powder", "Liquid I.V.", "Health & Pharmacy", "10pk", "5012345678910", 11.99, 12, "Multiplication hydration drink mix lemon lime flavor", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Medical 3-Ply Protective Face Masks", "HealthGuard", "Health & Pharmacy", "50pk", "5012345678911", 9.49, 18, "Breathable disposable protective masks with adjustable nose wire", 1, 1),
        (shop_ids["cornerstone-health-pharmacy"], "Allergy Relief 24hr Antihistamine", "Claritin", "Health & Pharmacy", "30 tabs", "5012345678912", 16.75, 8, "Non-drowsy 24 hour relief from indoor and outdoor allergies", 1, 1),

        # Metro Tech & Gadget Hub
        (shop_ids["metro-tech-gadget-hub"], "USB-C Fast Charger 30W", "Anker", "Electronics & Gadgets", "Compact", "0123456789021", 16.99, 14, "PowerPort III 30W high speed USB-C charger for phone/tablet", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "Braided USB-C to USB-C Cable 2m", "Anker", "Electronics & Gadgets", "2m", "0123456789022", 9.99, 22, "Durable nylon braided high-speed charging cable 60W power delivery", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "True Wireless Bluetooth Earbuds", "Sony", "Electronics & Gadgets", "Black", "0123456789023", 29.99, 3, "Noise cancelling earbuds with 20hr battery case and mic", 1, 1), # low stock
        (shop_ids["metro-tech-gadget-hub"], "AA Long-Life Alkaline Batteries", "Duracell", "Electronics & Gadgets", "8pk", "0123456789024", 6.49, 30, "Long lasting copper top AA 1.5V batteries with Duralock", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "Ergonomic Adjustable Laptop Stand", "Besign", "Electronics & Gadgets", "Silver", "0123456789025", 24.99, 6, "Foldable aluminum riser suitable for laptops 10 to 15.6 inches", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "Silent Wireless Optical Mouse", "Logitech", "Electronics & Gadgets", "Grey", "0123456789026", 14.99, 8, "Compact 2.4GHz wireless mouse with 90% reduced click noise", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "HDMI 2.1 Ultra HD Cable 4K/8K", "Belkin", "Electronics & Gadgets", "1.8m", "0123456789027", 11.99, 0, "High speed 48Gbps braided HDMI cable supporting HDR & 120Hz", 1, 1), # out of stock
        (shop_ids["metro-tech-gadget-hub"], "Slim Power Bank 10000mAh", "Anker", "Electronics & Gadgets", "10000mAh", "0123456789028", 22.50, 5, "Dual output slim portable charger with PowerIQ technology", 1, 1), # low stock
        (shop_ids["metro-tech-gadget-hub"], "USB-C Multiport Adapter 6-in-1", "UGREEN", "Electronics & Gadgets", "Hub", "0123456789029", 25.99, 9, "Includes 4K HDMI, 100W PD charging, 3 USB 3.0 ports, SD reader", 1, 1),
        (shop_ids["metro-tech-gadget-hub"], "Screen Cleaning Kit Anti-Static", "Whoosh!", "Electronics & Gadgets", "100ml", "0123456789030", 7.99, 15, "Non-toxic screen shine spray with antimicrobial microfiber cloth", 1, 1),

        # Downtown Hardware & Home
        (shop_ids["downtown-hardware-home"], "Cordless Drill Driver 12V Kit", "DeWalt", "Hardware & Home Improvement", "12V Kit", "8859112345674", 45.00, 4, "Compact lightweight cordless drill with lithium-ion battery and charger", 1, 1), # low stock
        (shop_ids["downtown-hardware-home"], "LED Light Bulbs Warm White 60W", "Philips", "Hardware & Home Improvement", "4pk", "8859112345675", 7.99, 18, "Energy saving 800 lumen non-flicker dimmable A19 LED bulbs", 1, 1),
        (shop_ids["downtown-hardware-home"], "Heavy Duty Duct Tape All-Weather", "Gorilla", "Hardware & Home Improvement", "50m", "8859112345676", 5.49, 25, "Double-thick adhesive tough weatherproof repair tape", 1, 1),
        (shop_ids["downtown-hardware-home"], "Precision Screwdriver Set 6pc", "Craftsman", "Hardware & Home Improvement", "6pc", "8859112345677", 12.99, 9, "Magnetic tip Phillips and slotted alloy steel screwdrivers", 1, 1),
        (shop_ids["downtown-hardware-home"], "Bypass Garden Pruning Shears", "Fiskars", "Hardware & Home Improvement", "8 inch", "8859112345678", 15.50, 0, "Steel bypass pruner with non-slip grip for clean branches cuts", 1, 1), # out of stock
        (shop_ids["downtown-hardware-home"], "WD-40 Multi-Use Lubricant Spray", "WD-40", "Hardware & Home Improvement", "300ml", "8859112345679", 6.99, 16, "Stops squeaks, drives out moisture, cleans and protects metal", 1, 1),
        (shop_ids["downtown-hardware-home"], "Heavy Duty Indoor/Outdoor Extension Cord", "Southwire", "Hardware & Home Improvement", "5m", "8859112345680", 14.25, 7, "Grounded 16/3 SJTW heavy-duty vinyl cord with reinforced prongs", 1, 1),
        (shop_ids["downtown-hardware-home"], "Steel Claw Hammer 16oz", "Stanley", "Hardware & Home Improvement", "16oz", "8859112345681", 11.50, 12, "Fiberglass vibration absorbing core with heat-treated head", 1, 1),
        (shop_ids["downtown-hardware-home"], "Painter's Clean Release Masking Tape", "Scotch", "Hardware & Home Improvement", "24mm", "8859112345682", 4.99, 20, "14-day clean removal multi-surface blue masking tape", 1, 1),
        (shop_ids["downtown-hardware-home"], "Solid Brass Heavy Duty Padlock", "Master Lock", "Hardware & Home Improvement", "40mm", "8859112345683", 9.99, 14, "Hardened steel shackle with 4-pin cylinder and 2 keys", 1, 1)
    ]

    for p in products_data:
        cursor.execute("""
            INSERT INTO products (
                shop_id, name, brand, category, size, barcode, price, stock_quantity,
                description, is_published, is_demo, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, p)

    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")
    print(f"Seeded 4 shops and {len(products_data)} demo products across various categories.")

if __name__ == "__main__":
    seed_database()
