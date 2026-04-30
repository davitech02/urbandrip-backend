from app import create_app
from database import db
from models import Product

app = create_app()

def seed():
    with app.app_context():
        # Clear existing products
        Product.query.delete()
        
        items = [
            Product(name="Essential Black Hoodie", description="Heavyweight cotton blend, oversized fit.", price=45.0, category="Hoodies & Sweatshirts", stock_quantity=20, images=["/assets/products/hoodie.jpg"], sizes=["S","M","L","XL","XXL"]),
            Product(name="Urban Cargo Pants", description="Multi-pocket utility pants in olive green.", price=65.0, category="Pants & Shorts", stock_quantity=15, images=["/assets/products/cargo.jpg"], sizes=["30","32","34","36"]),
            Product(name="Drip Graphic Tee", description="Limited edition streetwear graphic.", price=30.0, category="T-Shirts", stock_quantity=50, images=["/assets/products/tee.jpg"], sizes=["S","M","L","XL"]),
            Product(name="Street Queen Bomber", description="Satin finish bomber jacket for women.", price=85.0, category="Jackets", stock_quantity=10, images=["/assets/products/jacket.jpg"], sizes=["XS","S","M","L"]),
            Product(name="Classic Polo Shirt", description="Premium cotton polo with urban design.", price=35.0, category="Polos", stock_quantity=25, images=["/assets/products/polo.jpg"], sizes=["S","M","L","XL"]),
            Product(name="Button Down Shirt", description="Slim fit button down shirt.", price=40.0, category="Shirts", stock_quantity=18, images=["/assets/products/shirt.jpg"], sizes=["S","M","L","XL"]),
            Product(name="Oversized Hoodie", description="Extra large fit hoodie for comfort.", price=55.0, category="Hoodies & Sweatshirts", stock_quantity=12, images=["/assets/products/hoodie2.jpg"], sizes=["S","M","L","XL","XXL"]),
            Product(name="Cargo Shorts", description="Military style cargo shorts.", price=45.0, category="Pants & Shorts", stock_quantity=22, images=["/assets/products/shorts.jpg"], sizes=["30","32","34","36"]),
        ]
        
        db.session.bulk_save_objects(items)
        db.session.commit()
        print("Database seeded with fresh drip!")

if __name__ == "__main__":
    seed()