# 📍 Local Product Finder

A responsive web application that empowers shoppers to discover products at nearby local shops, compare real-time prices and verified in-store stock, and enables shop owners to manage and publish their inventory.

---

## ✨ Features

### 🛒 Customer Experience (No Account Required)
- **Multi-Factor Product Search**: Search by product name, brand, category, or barcode (with barcode simulation).
- **Proximity & Distance**: Real-time Haversine spherical distance calculation (e.g., *560 m away*, *1.2 km away*).
- **Location Flexibility**: Detect current device location via HTML5 Geolocation API, or choose/type neighborhood manually.
- **Sorting & Granular Filtering**:
  - Sort by nearest distance, lowest price, highest price, or stock availability.
  - Filter by distance radius (2 km, 5 km, 10 km, 25 km), price range, brand, category, and in-stock only.
- **Interactive Shop Details Page**:
  - Live **Open Now** / **Closed** badge computed dynamically from store operating hours and current local time.
  - Interactive SVG/Canvas coordinate map preview with direction links to Google Maps.
  - Complete searchable store catalog with category filters.
- **Data Trustworthiness**:
  - Never invents stock or prices.
  - Transparent timestamps for when inventory was last updated (*"Updated 2 hours ago"*).
  - Clear warning badge if inventory has not been updated in over 14 days.
  - Empty search states offer helpful recommendations to broaden the search.

### 🤖 AI-Assisted Natural Language Search
- Accepts conversational queries like:
  - *"cheap 1 kg rice near me"*
  - *"organic milk under $5"*
  - *"sony wireless earbuds in stock"*
- **Intent Interpretation**: Parses product keyword, brand, category, size/weight (*"1 kg"*, *"500 ml"*), price cap (*"under $5"*), and distance preference (*"near me"*).
- **Ambiguity Detection**: Queries like *"apple"* or *"charger"* trigger a clarifying prompt asking the user to choose between electronics vs groceries before querying.
- **Zero Hallucination**: AI only extracts structured query parameters; listings are queried directly from the real database.
- **Dual Engine**: Works with Google Gemini API if `GEMINI_API_KEY` is provided, with an intelligent built-in NLP parser that runs 100% offline out-of-the-box.

### 🏪 Shop Owner Portal
- **Secure Authentication**: Registration and sign-in with password hashing (`werkzeug.security`).
- **One-Click Demo Accounts**: Pre-configured buttons on `/auth/login` for instant testing.
- **Strict Authorization Isolation**: Shop owners can only view, edit, and delete their own inventory. Cross-shop access is strictly forbidden.
- **Live Inventory Dashboard**:
  - Overview metrics: Total products, In-stock, Low-stock items, Out-of-stock items, and inventory update timestamps.
  - Prominent **Low Stock Alert** table with quick `+5 Restock` actions.
  - Instant inline stock quantity adjusters (`+` / `-`) powered by AJAX without full page reloads.
  - Real-time stock status badge updates: **In stock** (>5), **Low stock** (1-5), **Out of stock** (0).
  - "Confirm & Publish Changes" action before listings appear to customers.
- **Batch CSV Import & Export**:
  - Upload inventory spreadsheets (`.csv`) with full row-level validation.
  - Pre-import preview screen highlighting valid rows and specific validation errors (e.g. negative prices, missing categories).
  - Downloadable sample CSV template (`sample_inventory.csv`).
  - One-click CSV export of current inventory.
- **Shop Profile & Hours Management**:
  - Update shop address, GPS coordinates, contact phone, email, and website.
  - Manage weekly opening and closing hours for every day of the week.

---

## 🛠️ Technology Stack & Architecture

- **Backend**: Python 3.14 + Flask 3.1.3 + Jinja2 + Werkzeug
- **Database**: SQLite 3 (persisted at `instance/local_product_finder.db`)
- **Frontend**: Semantic HTML5, modern custom responsive CSS system (CSS Grid, Flexbox, accessible contrast), and Vanilla ES6 JavaScript (zero heavy node runtime needed).
- **Automated Testing**: Python `unittest` with Flask test client.

---

## 🚀 Steps to Open and Run the Website Locally

### Prerequisites
- Python 3.10+ (Python 3.14 installed on this system)

### Step 1: Open Terminal in the Project Directory
```powershell
cd "C:\Users\K SHASHANK\.gemini\antigravity\scratch\local-product-finder"
```

### Step 2: (Optional) Seed Sample Database Standalone
The database automatically seeds on first launch, but you can also run the seed script directly:
```powershell
python seed_data.py
```
This populates 4 local shops and 42 realistic demo products with barcodes, stock levels, and store hours.

### Step 3: Start the Application Server
```powershell
python run.py
```

You will see:
```
============================================================
   LOCAL PRODUCT FINDER - Web Server Running
============================================================
 -> URL: http://127.0.0.1:5000
 -> Customer Mode: Search & browse freely without an account
 -> Shop Owner Mode: Use 1-Click demo logins on /auth/login
    Demo account 1: greenvalley@localfinder.demo (Pass: DemoPass123!)
    Demo account 2: cornerstone@localfinder.demo (Pass: DemoPass123!)
============================================================
```

### Step 4: Open in Your Browser
Open your favorite web browser (Chrome, Edge, Firefox) and navigate to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🔑 Demo Shop Owner Credentials

For testing the shop owner journey, navigate to **[http://127.0.0.1:5000/auth/login](http://127.0.0.1:5000/auth/login)**. You can click the **1-Click Demo Login** buttons or enter:

| Store Name | Email Address | Password | Category |
| :--- | :--- | :--- | :--- |
| **Green Valley Organic Grocers** | `greenvalley@localfinder.demo` | `DemoPass123!` | Groceries & Produce |
| **Cornerstone Health & Pharmacy** | `cornerstone@localfinder.demo` | `DemoPass123!` | Health & Pharmacy |
| **Metro Tech & Gadget Hub** | `metrotech@localfinder.demo` | `DemoPass123!` | Electronics & Tech |
| **Downtown Hardware & Home** | `downware@localfinder.demo` | `DemoPass123!` | Hardware & Tools |

---

## 🧪 Running the Automated Checks

Run the automated test suite covering customer search, shop owner management, owner isolation, and AI query parsing:

```powershell
python -m unittest discover tests -v
```

All 20 test cases run and verify:
1. Customer search without login
2. Case-insensitive and partial keyword matching
3. Barcode exact lookup
4. In-stock and price range filtering
5. Distance and price sorting
6. Shop details and weekly hours
7. Empty search suggestions
8. Shop owner authentication and session security
9. Cross-shop authorization protection (User A cannot modify User B's inventory)
10. Product CRUD and dynamic stock status calculation (In stock / Low stock / Out of stock)
11. CSV batch upload validation and error reporting
12. AI query extraction and ambiguity clarification prompts

---

## ⚙️ Configuration & Environment Variables

Copy `.env.example` to `.env` to configure optional settings:

```ini
SECRET_KEY=your-custom-secret-key
PORT=5000
HOST=127.0.0.1
APP_CURRENCY_SYMBOL="$"
DEFAULT_USER_LAT=37.7749
DEFAULT_USER_LNG=-122.4194
DEFAULT_USER_CITY="San Francisco, CA"
GEMINI_API_KEY=""  # Optional: Google Gemini API key for external LLM query processing
```

---

## 📋 Data Freshness & Trust Guarantee

1. **No Fake Listings**: Only products physically stocked by registered stores appear in results.
2. **Transparent Update Time**: Every product indicates when its stock was last verified by the merchant.
3. **Stale Flagging**: Items older than 14 days display a warning badge encouraging shoppers to call the store before visiting.
