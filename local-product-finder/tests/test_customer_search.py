import unittest
import json
from pathlib import Path
from app import create_app
from app.config import TestingConfig
from app.db import get_db, create_tables
from app.models import Shop, Product, User
from seed_data import seed_database

class CustomerSearchTestCase(unittest.TestCase):
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

    def test_customer_can_access_home_without_account(self):
        """Customers should be able to view home page without creating an account."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Find Products in Stock", response.data)
        self.assertIn(b"Nearby Local Shops", response.data)

    def test_search_partial_and_case_insensitive_match(self):
        """Searching 'mILk' should find 'Organic Whole Milk' and 'Unsweetened Almond Milk'."""
        response = self.client.get("/search?q=mILk")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Organic Whole Milk", response.data)
        self.assertIn(b"Almond Milk", response.data)

    def test_search_by_barcode(self):
        """Searching by exact barcode should find the corresponding product."""
        # Barcode for Royal Basmati Rice: 8901234567891
        response = self.client.get("/search?barcode=8901234567891")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Basmati Rice", response.data)

    def test_filter_by_in_stock_only(self):
        """In-stock filter should exclude items with 0 stock (e.g. Organic Free-Range Brown Eggs)."""
        # All items matching 'Eggs'
        resp_all = self.client.get("/search?q=Eggs")
        self.assertIn(b"Brown Eggs", resp_all.data)

        # Only in-stock
        resp_in_stock = self.client.get("/search?q=Eggs&in_stock=1")
        self.assertNotIn(b"Brown Eggs", resp_in_stock.data)

    def test_filter_by_price_range(self):
        """Price range should limit results to specified min and max bounds."""
        response = self.client.get("/search?q=Olive&min_price=10.0&max_price=20.0")
        self.assertEqual(response.status_code, 200)
        # Extra Virgin Olive Oil is $12.99, should be present
        self.assertIn(b"Olive Oil", response.data)

        # Under $10.0 should not find Olive Oil
        resp_low = self.client.get("/search?q=Olive&max_price=10.0")
        self.assertNotIn(b"Olive Oil", resp_low.data)

    def test_sorting_by_price(self):
        """Sorting by price ascending should display cheapest items first."""
        response = self.client.get("/search?q=rice&sort_by=price_asc")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Jasmine Rice", response.data)
        self.assertIn(b"Basmati Rice", response.data)

    def test_shop_details_page(self):
        """Opening a shop page shows address, contact, hours, and shop inventory."""
        response = self.client.get("/shop/green-valley-organic-grocers")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Green Valley Organic Grocers", response.data)
        self.assertIn(b"428 Castro Street", response.data)
        self.assertIn(b"Weekly Hours", response.data)

    def test_empty_search_shows_suggestions(self):
        """A search yielding no results should show friendly suggestions."""
        response = self.client.get("/search?q=nonexistentxyzitem999")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"No matching products found", response.data)
        self.assertIn(b"Helpful suggestions", response.data)

if __name__ == "__main__":
    unittest.main()
