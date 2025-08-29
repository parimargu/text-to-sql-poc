"""Script to seed the database with sample data."""

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session

from database.connection import db_manager
from database.models import Store, Customer, Product, Order, OrderItem


def seed_database():
    """Seed the database with sample retail data."""
    with db_manager.get_session() as session:
        # Clear existing data
        session.query(OrderItem).delete()
        session.query(Order).delete()
        session.query(Product).delete()
        session.query(Customer).delete()
        session.query(Store).delete()
        
        # Seed stores
        stores_data = [
            {"name": "Downtown Store", "location": "123 Main St, Downtown", "manager": "John Smith", "phone": "555-0101", "email": "downtown@retail.com"},
            {"name": "Mall Store", "location": "456 Mall Ave, Shopping Center", "manager": "Jane Doe", "phone": "555-0102", "email": "mall@retail.com"},
            {"name": "Suburban Store", "location": "789 Oak Rd, Suburbs", "manager": "Bob Johnson", "phone": "555-0103", "email": "suburban@retail.com"},
            {"name": "Airport Store", "location": "321 Terminal Blvd, Airport", "manager": "Alice Brown", "phone": "555-0104", "email": "airport@retail.com"},
        ]
        
        stores = []
        for store_data in stores_data:
            store = Store(**store_data)
            session.add(store)
            stores.append(store)
        
        session.flush()
        
        # Seed customers
        customers_data = [
            {"first_name": "Michael", "last_name": "Wilson", "email": "michael.wilson@email.com", "phone": "555-1001", "address": "100 First St"},
            {"first_name": "Sarah", "last_name": "Davis", "email": "sarah.davis@email.com", "phone": "555-1002", "address": "200 Second Ave"},
            {"first_name": "David", "last_name": "Miller", "email": "david.miller@email.com", "phone": "555-1003", "address": "300 Third Blvd"},
            {"first_name": "Lisa", "last_name": "Garcia", "email": "lisa.garcia@email.com", "phone": "555-1004", "address": "400 Fourth St"},
            {"first_name": "James", "last_name": "Rodriguez", "email": "james.rodriguez@email.com", "phone": "555-1005", "address": "500 Fifth Ave"},
            {"first_name": "Emily", "last_name": "Martinez", "email": "emily.martinez@email.com", "phone": "555-1006", "address": "600 Sixth St"},
            {"first_name": "Robert", "last_name": "Anderson", "email": "robert.anderson@email.com", "phone": "555-1007", "address": "700 Seventh Ave"},
            {"first_name": "Jessica", "last_name": "Taylor", "email": "jessica.taylor@email.com", "phone": "555-1008", "address": "800 Eighth St"},
        ]
        
        customers = []
        for customer_data in customers_data:
            customer = Customer(**customer_data)
            session.add(customer)
            customers.append(customer)
        
        session.flush()
        
        # Seed products
        products_data = [
            {"name": "Laptop Computer", "category": "Electronics", "price": 999.99, "description": "High-performance laptop", "in_stock": True},
            {"name": "Smartphone", "category": "Electronics", "price": 699.99, "description": "Latest smartphone model", "in_stock": True},
            {"name": "Headphones", "category": "Electronics", "price": 199.99, "description": "Wireless noise-canceling headphones", "in_stock": True},
            {"name": "Coffee Maker", "category": "Appliances", "price": 89.99, "description": "Programmable coffee maker", "in_stock": True},
            {"name": "Blender", "category": "Appliances", "price": 59.99, "description": "High-speed blender", "in_stock": True},
            {"name": "Running Shoes", "category": "Sports", "price": 129.99, "description": "Professional running shoes", "in_stock": True},
            {"name": "Yoga Mat", "category": "Sports", "price": 29.99, "description": "Non-slip yoga mat", "in_stock": True},
            {"name": "Office Chair", "category": "Furniture", "price": 299.99, "description": "Ergonomic office chair", "in_stock": True},
            {"name": "Desk Lamp", "category": "Furniture", "price": 49.99, "description": "LED desk lamp", "in_stock": True},
            {"name": "Backpack", "category": "Accessories", "price": 79.99, "description": "Waterproof backpack", "in_stock": True},
        ]
        
        products = []
        for product_data in products_data:
            product = Product(**product_data)
            session.add(product)
            products.append(product)
        
        session.flush()
        
        # Seed orders and order items
        order_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        
        for i in range(50):  # Create 50 orders
            order_date = datetime.utcnow() - timedelta(days=random.randint(1, 365))
            customer = random.choice(customers)
            store = random.choice(stores)
            status = random.choice(order_statuses)
            
            order = Order(
                customer_id=customer.id,
                store_id=store.id,
                order_date=order_date,
                total_amount=0.0,  # Will be calculated
                status=status
            )
            session.add(order)
            session.flush()
            
            # Add 1-5 items per order
            total_amount = 0.0
            num_items = random.randint(1, 5)
            
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                unit_price = product.price
                
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price
                )
                session.add(order_item)
                total_amount += unit_price * quantity
            
            order.total_amount = total_amount
        
        session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    seed_database()
