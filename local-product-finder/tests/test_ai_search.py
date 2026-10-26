import unittest
import json
from pathlib import Path
from app import create_app
from app.config import TestingConfig
from app.db import get_db, create_tables
from app.services.ai_search import parse_natural_language_query
from seed_data import seed_database

class AiSearchTestCase(unittest.TestCase):
    def setUp(self):
        test_db = Path(TestingConfig.DATABASE_PATH)
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()

        with self.app.app_context():
            seed_database(TestingConfig.DATABASE_PATH)

    def tearDown(self):
        test_db = Path(TestingConfig.DATABASE_PATH)
        if test_db.exists():
            try:
                test_db.unlink()
            except Exception:
                pass

    def test_parse_cheap_rice_near_me(self):
        """Query 'cheap 1 kg rice near me' extracts rice, size 1 kg, price/distance intent."""
        parsed = parse_natural_language_query("cheap 1 kg rice near me")
        self.assertIn("rice", parsed["product_keyword"].lower())
        self.assertIn("1 kg", parsed["size"].lower())
        self.assertIn(parsed["sort_by"], ["distance", "price_asc"])
        self.assertIsNone(parsed["clarification"])

    def test_parse_price_cap(self):
        """Query 'organic milk under $5' extracts milk and max_price=5.0."""
        parsed = parse_natural_language_query("organic milk under $5")
        self.assertIn("milk", parsed["product_keyword"].lower())
        self.assertEqual(parsed["max_price"], 5.0)

    def test_parse_in_stock_preference(self):
        """Query with 'in stock' sets in_stock_only=True."""
        parsed = parse_natural_language_query("cordless drill in stock")
        self.assertTrue(parsed["in_stock_only"])
        self.assertIn("drill", parsed["product_keyword"].lower())

    def test_ambiguity_detection_for_apple(self):
        """Ambiguous single-word queries like 'apple' prompt a clarifying question."""
        parsed = parse_natural_language_query("apple")
        self.assertIsNotNone(parsed["clarification"])
        self.assertIn("options", parsed["clarification"])
        self.assertGreaterEqual(len(parsed["clarification"]["options"]), 2)

    def test_ai_search_api_endpoint(self):
        """POST /api/ai-search returns parsed intent, match count, and redirect url."""
        payload = {
            "query": "cheap 1 kg rice near me",
            "lat": 37.7749,
            "lng": -122.4194
        }
        resp = self.client.post(
            "/api/ai-search",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["success"])
        self.assertFalse(data["is_ambiguous"])
        self.assertIn("results", data)
        self.assertIn("redirect_url", data)

    def test_ai_search_api_ambiguity_response(self):
        """POST /api/ai-search with 'charger' returns is_ambiguous=True with clarification."""
        payload = {
            "query": "charger"
        }
        resp = self.client.post(
            "/api/ai-search",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data["is_ambiguous"])
        self.assertIn("clarification", data)

if __name__ == "__main__":
    unittest.main()
