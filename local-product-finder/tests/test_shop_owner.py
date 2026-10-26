import unittest
import io
from pathlib import Path
from app import create_app
from app.config import TestingConfig
from app.db import get_db, create_tables
from app.models import Shop, Product, User, compute_stock_status
from seed_data import seed_database

class ShopOwnerTestCase(unittest.TestCase):
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

    def login_as_greenvalley(self):
        return self.client.post("/auth/login", data={
            "email": "greenvalley@localfinder.demo",
            "password": "DemoPass123!"
        }, follow_redirects=True)

    def login_as_cornerstone(self):
        return self.client.post("/auth/login", data={
            "email": "cornerstone@localfinder.demo",
            "password": "DemoPass123!"
        }, follow_redirects=True)

    def test_stock_status_logic(self):
        """Verify dynamic status tags: 0 -> out_of_stock, 1-5 -> low_stock, >5 -> in_stock."""
        status_0 = compute_stock_status(0)
        self.assertEqual(status_0["code"], "out_of_stock")
        self.assertEqual(status_0["label"], "Out of stock")

        status_3 = compute_stock_status(3)
        self.assertEqual(status_3["code"], "low_stock")
        self.assertEqual(status_3["label"], "Low stock")

        status_10 = compute_stock_status(10)
        self.assertEqual(status_10["code"], "in_stock")
        self.assertEqual(status_10["label"], "In stock")

    def test_shop_owner_login_success(self):
        """Shop owner should be able to log in with valid credentials."""
        resp = self.login_as_greenvalley()
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Store Management", resp.data)
        self.assertIn(b"Green Valley Organic Grocers", resp.data)

    def test_unauthorized_dashboard_redirect(self):
        """Attempting to access /dashboard without signing in should redirect to login."""
        resp = self.client.get("/dashboard/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/auth/login", resp.headers["Location"])

    def test_shop_owner_isolation(self):
        """Shop owner A must not be able to edit or delete Shop owner B's products."""
        # Log in as Cornerstone Pharmacy
        self.login_as_cornerstone()

        with self.app.app_context():
            # Product 1 belongs to Green Valley Grocers
            prod = Product.get_by_id(1)
            self.assertIsNotNone(prod)
            green_valley_shop = Shop.get_by_slug("green-valley-organic-grocers")
            self.assertEqual(prod["shop_id"], green_valley_shop["id"])

        # Cornerstone tries to edit Green Valley's product 1
        resp = self.client.get("/dashboard/product/1/edit", follow_redirects=True)
        self.assertIn(b"access denied", resp.data.lower())

        # Cornerstone tries to delete Green Valley's product 1
        resp_del = self.client.post("/dashboard/product/1/delete", follow_redirects=True)
        self.assertIn(b"access denied", resp_del.data.lower())

    def test_add_and_update_product(self):
        """Shop owner can add a new product and update its stock quantity."""
        self.login_as_greenvalley()

        # Add product
        resp = self.client.post("/dashboard/product/add", data={
            "name": "Organic Honeycrisp Apple",
            "brand": "Washington Orchards",
            "category": "Produce",
            "size": "1 lb",
            "barcode": "0123456789999",
            "price": "3.50",
            "stock_quantity": "12",
            "is_published": "1"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Organic Honeycrisp Apple", resp.data)

        # Quick stock update via AJAX (+5 units)
        with self.app.app_context():
            db = get_db()
            item = db.execute("SELECT id, stock_quantity FROM products WHERE barcode = '0123456789999'").fetchone()
            self.assertEqual(item["stock_quantity"], 12)
            prod_id = item["id"]

        ajax_resp = self.client.post(f"/dashboard/product/{prod_id}/stock", data={
            "delta": 3
        }, headers={"X-Requested-With": "XMLHttpRequest"})
        
        self.assertEqual(ajax_resp.status_code, 200)
        import json
        data = json.loads(ajax_resp.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["new_quantity"], 15)

    def test_csv_import_validation(self):
        """Valid rows in CSV are imported, while malformed rows are flagged with clear errors."""
        self.login_as_greenvalley()

        csv_content = (
            "name,brand,category,size,barcode,price,stock_quantity\n"
            "Valid Test Item 1,Brand A,Groceries,500g,111222333,5.99,10\n"
            "Invalid Price Item,Brand B,Groceries,1kg,444555666,-2.50,10\n"
            ",Missing Name Brand,Groceries,1kg,777888999,3.99,5\n"
        )

        data = {
            "csv_file": (io.BytesIO(csv_content.encode("utf-8")), "inventory.csv")
        }

        resp = self.client.post("/dashboard/import-csv", data=data, content_type="multipart/form-data")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"READY TO IMPORT", resp.data)
        self.assertIn(b"INVALID ROWS", resp.data)
        self.assertIn(b"Valid Test Item 1", resp.data)
        self.assertIn(b"Price cannot be negative", resp.data)
        self.assertIn(b"Product name is required", resp.data)

if __name__ == "__main__":
    unittest.main()
