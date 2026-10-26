import re
import json
import urllib.request
import urllib.error
from flask import current_app

AMBIGUOUS_KEYWORDS = {
    "apple": {
        "question": "Did you mean fresh Apple fruits, or Apple electronics & accessories?",
        "options": ["Fresh Apple (Groceries)", "Apple iPhone / Charger / Accessories (Tech)"]
    },
    "charger": {
        "question": "What device are you looking to charge?",
        "options": ["USB-C Fast Charger", "Phone Cable & Charger", "Laptop Charger"]
    },
    "oil": {
        "question": "Which type of oil do you need?",
        "options": ["Extra Virgin Olive Oil (Cooking)", "Essential / Wellness Oil", "WD-40 / Machinery Lubricant"]
    },
    "battery": {
        "question": "What type of battery are you searching for?",
        "options": ["AA / AAA Alkaline Batteries", "Portable Power Bank", "Coin / Watch Batteries"]
    },
    "milk": {
        "question": "Which type of milk are you looking for?",
        "options": ["Whole Cow Milk", "Almond Milk / Plant-based", "Lactose-Free Milk"]
    }
}

KNOWN_BRANDS = [
    "organic valley", "kirkland", "chobani", "sony", "anker", "samsung", 
    "apple", "philips", "tylenol", "advil", "dewalt", "bosch", "dyson", 
    "nestle", "heinz", "dole", "california", "nature valley", "purell"
]

KNOWN_CATEGORIES = [
    "groceries", "produce", "dairy", "bakery", "health", "pharmacy", 
    "electronics", "tech", "hardware", "tools", "home"
]

def parse_natural_language_query(query_text):
    """
    Parses a natural language query into structured search parameters:
    - product_keyword: str
    - brand: str or None
    - category: str or None
    - size: str or None
    - max_price: float or None
    - in_stock_only: bool
    - sort_by: 'price_asc' | 'distance' | 'stock' | 'relevance'
    - clarification: dict or None
    - explanation: str
    - used_ai: bool
    """
    clean_query = query_text.strip()
    if not clean_query:
        return {
            "product_keyword": "",
            "brand": None,
            "category": None,
            "size": None,
            "max_price": None,
            "in_stock_only": False,
            "sort_by": "relevance",
            "clarification": None,
            "explanation": "Empty query",
            "used_ai": False
        }

    # Check for direct ambiguity first
    lower_query = clean_query.lower()
    for keyword, info in AMBIGUOUS_KEYWORDS.items():
        # Match standalone word
        if re.search(rf"\b{re.escape(keyword)}\b", lower_query):
            # If query is very short or just the ambiguous word, ask clarification
            words = lower_query.split()
            if len(words) <= 2:
                return {
                    "product_keyword": keyword,
                    "brand": None,
                    "category": None,
                    "size": None,
                    "max_price": None,
                    "in_stock_only": False,
                    "sort_by": "relevance",
                    "clarification": info,
                    "explanation": f"Query '{clean_query}' is ambiguous. Please select an option to narrow down results.",
                    "used_ai": False
                }

    # Attempt LLM parser if GEMINI_API_KEY is configured
    api_key = current_app.config.get("GEMINI_API_KEY") if current_app else ""
    if api_key and len(api_key) > 10:
        llm_result = _call_gemini_nlp(clean_query, api_key)
        if llm_result:
            return llm_result

    # Fallback to smart heuristic / rule-based NLP parser
    return _heuristic_nlp_parse(clean_query)

def _heuristic_nlp_parse(query_text):
    text = query_text.lower().strip()
    explanation_parts = []
    
    sort_by = "relevance"
    max_price = None
    in_stock_only = False
    size = None
    brand = None
    category = None

    # Check for proximity intent
    if any(k in text for k in ["near me", "nearby", "closest", "around here", "local"]):
        sort_by = "distance"
        explanation_parts.append("prioritizing nearest shops")
        text = re.sub(r"\b(near me|nearby|closest|around here|local)\b", "", text)

    # Check for cheap / lowest price intent
    if any(k in text for k in ["cheap", "cheapest", "low price", "affordable", "best price"]):
        sort_by = "price_asc"
        explanation_parts.append("sorting by lowest price")
        text = re.sub(r"\b(cheap|cheapest|low price|affordable|best price)\b", "", text)

    # Check for price cap e.g. "under $10", "under 15", "below $5", "less than 20"
    price_match = re.search(r"(?:under|below|less than|max|within)\s*\$?(\d+(?:\.\d{1,2})?)", text)
    if price_match:
        try:
            max_price = float(price_match.group(1))
            explanation_parts.append(f"max price ${max_price:.2f}")
            text = text[:price_match.start()] + " " + text[price_match.end():]
        except ValueError:
            pass

    # Check for in-stock intent
    if any(k in text for k in ["in stock", "available now", "in-stock", "have stock"]):
        in_stock_only = True
        explanation_parts.append("only in-stock items")
        text = re.sub(r"\b(in stock|available now|in-stock|have stock)\b", "", text)

    # Check for weight / size / volume / packaging e.g. "1 kg", "500ml", "1000mg", "30w", "pack of 4", "12pk"
    size_match = re.search(r"(\d+(?:\.\d+)?\s*(?:kg|g|l|ml|mg|w|oz|lb|pack|pk|pcs|tabs|caps|count))", text)
    if size_match:
        size = size_match.group(1).strip()
        explanation_parts.append(f"size '{size}'")
        text = text[:size_match.start()] + " " + text[size_match.end():]

    # Check for known brands
    for b in KNOWN_BRANDS:
        if b in text:
            brand = b.title()
            explanation_parts.append(f"brand '{brand}'")
            text = text.replace(b, " ")
            break

    # Check for known categories
    for cat in KNOWN_CATEGORIES:
        if cat in text:
            category = cat.title()
            explanation_parts.append(f"category '{category}'")
            text = text.replace(cat, " ")
            break

    # Clean remaining tokens as product keyword
    clean_keyword = re.sub(r"[^\w\s-]", " ", text)
    clean_keyword = " ".join([w for w in clean_keyword.split() if w not in ["a", "an", "the", "for", "with", "or", "and", "find", "get", "show", "buy"]])
    
    if clean_keyword:
        explanation_parts.insert(0, f"searching for '{clean_keyword}'")

    explanation = "Parsed: " + (", ".join(explanation_parts) if explanation_parts else f"searching for '{query_text}'")

    return {
        "product_keyword": clean_keyword if clean_keyword else query_text.strip(),
        "brand": brand,
        "category": category,
        "size": size,
        "max_price": max_price,
        "in_stock_only": in_stock_only,
        "sort_by": sort_by,
        "clarification": None,
        "explanation": explanation,
        "used_ai": False
    }

def _call_gemini_nlp(query_text, api_key):
    """
    Optional call to Google Gemini 1.5/2.0 to interpret the natural language query.
    Falls back gracefully if network is unavailable or request fails.
    """
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    system_prompt = (
        "You are a local product search query interpreter. "
        "Extract search parameters from the user's natural language shopping query. "
        "Return ONLY a JSON object with keys: "
        "product_keyword (string), brand (string or null), category (string or null), "
        "size (string or null), max_price (number or null), in_stock_only (boolean), "
        "sort_by ('distance' | 'price_asc' | 'stock' | 'relevance'), "
        "clarification (null or object with 'question' and 'options' list if ambiguous), "
        "explanation (short 1-line summary). Do not invent items or hallucinate availability."
    )

    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\nQuery: {query_text}"}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                body = json.loads(response.read().decode("utf-8"))
                text_content = body["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)
                parsed["used_ai"] = True
                return parsed
    except Exception:
        # Graceful fallback to heuristic
        return None
