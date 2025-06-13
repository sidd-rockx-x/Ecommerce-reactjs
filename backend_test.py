
import requests
import unittest
import uuid
import time

class EcommerceAPITester(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the public endpoint from frontend/.env
        self.base_url = "https://602f2b71-821f-4171-9cbf-20596caaf1cc.preview.emergentagent.com"
        self.token = None
        self.user_id = None
        self.test_user_email = f"test_user_{uuid.uuid4().hex[:8]}@example.com"
        self.test_user_password = "TestPassword123!"
        self.test_user_name = "Test User"
        self.product_id = None

    def setUp(self):
        print(f"\n🔍 Testing API at {self.base_url}")

    def test_01_health_check(self):
        """Test the health check endpoint"""
        print("\n🔍 Testing health check endpoint...")
        response = requests.get(f"{self.base_url}/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        print("✅ Health check passed")

    def test_02_get_products(self):
        """Test getting all products"""
        print("\n🔍 Testing get products endpoint...")
        response = requests.get(f"{self.base_url}/api/products")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        self.assertIsInstance(products, list)
        self.assertGreater(len(products), 0)
        # Save a product ID for later tests
        self.product_id = products[0]["id"]
        print(f"✅ Got {len(products)} products")

    def test_03_get_product_by_id(self):
        """Test getting a single product by ID"""
        if not self.product_id:
            self.test_02_get_products()
        
        print(f"\n🔍 Testing get product by ID endpoint for product {self.product_id}...")
        response = requests.get(f"{self.base_url}/api/products/{self.product_id}")
        self.assertEqual(response.status_code, 200)
        product = response.json()
        self.assertEqual(product["id"], self.product_id)
        print(f"✅ Got product: {product['name']}")

    def test_04_get_categories(self):
        """Test getting all categories"""
        print("\n🔍 Testing get categories endpoint...")
        response = requests.get(f"{self.base_url}/api/categories")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("categories", data)
        self.assertIsInstance(data["categories"], list)
        self.assertGreater(len(data["categories"]), 0)
        print(f"✅ Got categories: {', '.join(data['categories'])}")

    def test_05_filter_products_by_category(self):
        """Test filtering products by category"""
        print("\n🔍 Testing filter products by category...")
        # First get categories
        response = requests.get(f"{self.base_url}/api/categories")
        categories = response.json()["categories"]
        
        # Test with the first category
        category = categories[0]
        response = requests.get(f"{self.base_url}/api/products?category={category}")
        self.assertEqual(response.status_code, 200)
        products = response.json()
        
        # Verify all returned products have the correct category
        for product in products:
            self.assertEqual(product["category"], category)
        
        print(f"✅ Successfully filtered products by category '{category}'")

    def test_06_search_products(self):
        """Test searching products"""
        print("\n🔍 Testing search products...")
        # Get all products first
        response = requests.get(f"{self.base_url}/api/products")
        all_products = response.json()
        
        # Use a word from the first product's name as search term
        search_term = all_products[0]["name"].split()[0]
        
        response = requests.get(f"{self.base_url}/api/products?search={search_term}")
        self.assertEqual(response.status_code, 200)
        search_results = response.json()
        
        # Verify we got results
        self.assertGreater(len(search_results), 0)
        
        # Verify search term is in product name or description
        found = False
        for product in search_results:
            if (search_term.lower() in product["name"].lower() or 
                search_term.lower() in product["description"].lower()):
                found = True
                break
        
        self.assertTrue(found, f"Search term '{search_term}' not found in results")
        print(f"✅ Successfully searched products with term '{search_term}'")

    def test_07_register_user(self):
        """Test user registration"""
        print(f"\n🔍 Testing user registration with email {self.test_user_email}...")
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password,
            "name": self.test_user_name
        }
        
        response = requests.post(f"{self.base_url}/api/auth/register", json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify response contains token and user info
        self.assertIn("token", result)
        self.assertIn("user", result)
        self.assertEqual(result["user"]["email"], self.test_user_email)
        self.assertEqual(result["user"]["name"], self.test_user_name)
        
        # Save token and user ID for later tests
        self.token = result["token"]
        self.user_id = result["user"]["id"]
        
        print("✅ User registration successful")

    def test_08_login_user(self):
        """Test user login"""
        # If we don't have a registered user, register one first
        if not self.token:
            self.test_07_register_user()
            
        print(f"\n🔍 Testing user login with email {self.test_user_email}...")
        data = {
            "email": self.test_user_email,
            "password": self.test_user_password
        }
        
        response = requests.post(f"{self.base_url}/api/auth/login", json=data)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify response contains token and user info
        self.assertIn("token", result)
        self.assertIn("user", result)
        self.assertEqual(result["user"]["email"], self.test_user_email)
        
        # Update token
        self.token = result["token"]
        
        print("✅ User login successful")

    def test_09_get_cart(self):
        """Test getting user's cart"""
        if not self.token:
            self.test_08_login_user()
            
        print("\n🔍 Testing get cart endpoint...")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.base_url}/api/cart", headers=headers)
        self.assertEqual(response.status_code, 200)
        cart = response.json()
        
        # Verify cart structure
        self.assertIn("items", cart)
        self.assertIn("total", cart)
        
        print("✅ Successfully retrieved cart")

    def test_10_add_to_cart(self):
        """Test adding item to cart"""
        if not self.token:
            self.test_08_login_user()
        if not self.product_id:
            self.test_02_get_products()
            
        print(f"\n🔍 Testing add to cart endpoint for product {self.product_id}...")
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/api/cart/add?product_id={self.product_id}&quantity=2", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIn("message", result)
        
        # Verify item was added by checking cart
        response = requests.get(f"{self.base_url}/api/cart", headers=headers)
        cart = response.json()
        
        # Find the added product in cart
        found = False
        for item in cart["items"]:
            if item["product"]["id"] == self.product_id:
                found = True
                break
                
        self.assertTrue(found, "Added product not found in cart")
        print("✅ Successfully added item to cart")

    def test_11_update_cart_quantity(self):
        """Test updating cart item quantity"""
        if not self.token:
            self.test_08_login_user()
        if not self.product_id:
            self.test_10_add_to_cart()
            
        print(f"\n🔍 Testing update cart quantity for product {self.product_id}...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        # Update quantity to 3
        response = requests.put(
            f"{self.base_url}/api/cart/update?product_id={self.product_id}&quantity=3", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify quantity was updated
        response = requests.get(f"{self.base_url}/api/cart", headers=headers)
        cart = response.json()
        
        # Find the updated product in cart
        for item in cart["items"]:
            if item["product"]["id"] == self.product_id:
                self.assertEqual(item["quantity"], 3)
                break
                
        print("✅ Successfully updated cart item quantity")

    def test_12_remove_from_cart(self):
        """Test removing item from cart"""
        if not self.token:
            self.test_08_login_user()
        if not self.product_id:
            self.test_10_add_to_cart()
            
        print(f"\n🔍 Testing remove from cart for product {self.product_id}...")
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.delete(
            f"{self.base_url}/api/cart/remove/{self.product_id}", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify item was removed
        response = requests.get(f"{self.base_url}/api/cart", headers=headers)
        cart = response.json()
        
        # Check that the product is not in cart
        for item in cart["items"]:
            self.assertNotEqual(item["product"]["id"], self.product_id)
                
        print("✅ Successfully removed item from cart")

if __name__ == "__main__":
    # Run tests in order
    test_suite = unittest.TestSuite()
    test_suite.addTest(EcommerceAPITester('test_01_health_check'))
    test_suite.addTest(EcommerceAPITester('test_02_get_products'))
    test_suite.addTest(EcommerceAPITester('test_03_get_product_by_id'))
    test_suite.addTest(EcommerceAPITester('test_04_get_categories'))
    test_suite.addTest(EcommerceAPITester('test_05_filter_products_by_category'))
    test_suite.addTest(EcommerceAPITester('test_06_search_products'))
    test_suite.addTest(EcommerceAPITester('test_07_register_user'))
    test_suite.addTest(EcommerceAPITester('test_08_login_user'))
    test_suite.addTest(EcommerceAPITester('test_09_get_cart'))
    test_suite.addTest(EcommerceAPITester('test_10_add_to_cart'))
    test_suite.addTest(EcommerceAPITester('test_11_update_cart_quantity'))
    test_suite.addTest(EcommerceAPITester('test_12_remove_from_cart'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(test_suite)
