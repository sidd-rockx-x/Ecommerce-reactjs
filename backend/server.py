from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import os
import json
import uuid
from datetime import datetime
import jwt
from passlib.context import CryptContext
import uvicorn

# Environment setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')

app = FastAPI(title="Ecommerce API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory data storage (MongoDB simulation)
products_db = []
users_db = []
carts_db = {}
orders_db = []

# Models
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image: str
    category: str
    stock: int

class User(BaseModel):
    id: str
    email: str
    password: str
    name: str
    created_at: str

class CartItem(BaseModel):
    product_id: str
    quantity: int

class Cart(BaseModel):
    user_id: str
    items: List[CartItem]
    updated_at: str

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

# Initialize sample products
def init_products():
    sample_products = [
        {
            "id": str(uuid.uuid4()),
            "name": "Wireless Headphones",
            "description": "Premium wireless headphones with noise cancellation and superior sound quality",
            "price": 199.99,
            "image": "https://images.unsplash.com/photo-1498049794561-7780e7231661",
            "category": "Electronics",
            "stock": 50
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Athletic Sneakers",
            "description": "Comfortable and stylish athletic shoes perfect for running and daily wear",
            "price": 129.99,
            "image": "https://images.unsplash.com/photo-1560769629-975ec94e6a86",
            "category": "Fashion",
            "stock": 30
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Modern Office Chair",
            "description": "Ergonomic office chair with premium comfort and adjustable features",
            "price": 299.99,
            "image": "https://images.unsplash.com/photo-1579656592043-a20e25a4aa4b",
            "category": "Furniture",
            "stock": 25
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Desktop Computer Setup",
            "description": "Complete desktop workstation with high-performance components",
            "price": 1299.99,
            "image": "https://images.pexels.com/photos/356056/pexels-photo-356056.jpeg",
            "category": "Electronics",
            "stock": 15
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Fashion Accessories Set",
            "description": "Curated collection of stylish fashion accessories",
            "price": 79.99,
            "image": "https://images.unsplash.com/photo-1492707892479-7bc8d5a4ee93",
            "category": "Fashion",
            "stock": 40
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Home Decor Collection",
            "description": "Beautiful home decor items to enhance your living space",
            "price": 159.99,
            "image": "https://images.unsplash.com/photo-1496180727794-817822f65950",
            "category": "Home",
            "stock": 35
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Arduino Development Kit",
            "description": "Complete Arduino starter kit for electronics projects and learning",
            "price": 89.99,
            "image": "https://images.unsplash.com/photo-1603732551658-5fabbafa84eb",
            "category": "Electronics",
            "stock": 60
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Lifestyle Products Bundle",
            "description": "Carefully selected lifestyle products for modern living",
            "price": 249.99,
            "image": "https://images.unsplash.com/photo-1511556820780-d912e42b4980",
            "category": "Lifestyle",
            "stock": 20
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Beauty Essentials",
            "description": "Premium beauty products for your daily routine",
            "price": 119.99,
            "image": "https://images.pexels.com/photos/32497344/pexels-photo-32497344.jpeg",
            "category": "Beauty",
            "stock": 45
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Home Organization Set",
            "description": "Complete home organization solution for better living",
            "price": 179.99,
            "image": "https://images.pexels.com/photos/3735219/pexels-photo-3735219.jpeg",
            "category": "Home",
            "stock": 30
        }
    ]
    
    global products_db
    products_db = sample_products

# Initialize products on startup
init_products()

# Utility functions
def create_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload

# API Endpoints

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Ecommerce API is running"}

@app.get("/api/products", response_model=List[Product])
async def get_products(category: Optional[str] = None, search: Optional[str] = None):
    """Get all products with optional filtering"""
    filtered_products = products_db.copy()
    
    if category:
        filtered_products = [p for p in filtered_products if p["category"].lower() == category.lower()]
    
    if search:
        search_lower = search.lower()
        filtered_products = [
            p for p in filtered_products 
            if search_lower in p["name"].lower() or search_lower in p["description"].lower()
        ]
    
    return filtered_products

@app.get("/api/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get single product by ID"""
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.get("/api/categories")
async def get_categories():
    """Get all unique categories"""
    categories = list(set(p["category"] for p in products_db))
    return {"categories": sorted(categories)}

@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    """Register new user"""
    # Check if user exists
    if any(u["email"] == request.email for u in users_db):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user = {
        "id": str(uuid.uuid4()),
        "email": request.email,
        "password": pwd_context.hash(request.password),
        "name": request.name,
        "created_at": datetime.now().isoformat()
    }
    
    users_db.append(user)
    
    # Create token
    token = create_token({"user_id": user["id"], "email": user["email"]})
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login user"""
    user = next((u for u in users_db if u["email"] == request.email), None)
    if not user or not pwd_context.verify(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_token({"user_id": user["id"], "email": user["email"]})
    
    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"]
        }
    }

@app.get("/api/cart")
async def get_cart(current_user: dict = Depends(get_current_user)):
    """Get user's cart"""
    user_id = current_user["user_id"]
    cart = carts_db.get(user_id, {"user_id": user_id, "items": [], "updated_at": datetime.now().isoformat()})
    
    # Populate cart with product details
    cart_with_products = []
    for item in cart["items"]:
        product = next((p for p in products_db if p["id"] == item["product_id"]), None)
        if product:
            cart_with_products.append({
                "product": product,
                "quantity": item["quantity"]
            })
    
    return {
        "items": cart_with_products,
        "total": sum(item["product"]["price"] * item["quantity"] for item in cart_with_products)
    }

@app.post("/api/cart/add")
async def add_to_cart(product_id: str, quantity: int = 1, current_user: dict = Depends(get_current_user)):
    """Add item to cart"""
    user_id = current_user["user_id"]
    
    # Verify product exists
    product = next((p for p in products_db if p["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get or create cart
    if user_id not in carts_db:
        carts_db[user_id] = {"user_id": user_id, "items": [], "updated_at": datetime.now().isoformat()}
    
    cart = carts_db[user_id]
    
    # Check if item already in cart
    existing_item = next((item for item in cart["items"] if item["product_id"] == product_id), None)
    if existing_item:
        existing_item["quantity"] += quantity
    else:
        cart["items"].append({"product_id": product_id, "quantity": quantity})
    
    cart["updated_at"] = datetime.now().isoformat()
    
    return {"message": "Item added to cart", "cart_items": len(cart["items"])}

@app.put("/api/cart/update")
async def update_cart_item(product_id: str, quantity: int, current_user: dict = Depends(get_current_user)):
    """Update cart item quantity"""
    user_id = current_user["user_id"]
    
    if user_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = carts_db[user_id]
    item = next((item for item in cart["items"] if item["product_id"] == product_id), None)
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    if quantity <= 0:
        cart["items"].remove(item)
    else:
        item["quantity"] = quantity
    
    cart["updated_at"] = datetime.now().isoformat()
    
    return {"message": "Cart updated"}

@app.delete("/api/cart/remove/{product_id}")
async def remove_from_cart(product_id: str, current_user: dict = Depends(get_current_user)):
    """Remove item from cart"""
    user_id = current_user["user_id"]
    
    if user_id not in carts_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    cart = carts_db[user_id]
    cart["items"] = [item for item in cart["items"] if item["product_id"] != product_id]
    cart["updated_at"] = datetime.now().isoformat()
    
    return {"message": "Item removed from cart"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)