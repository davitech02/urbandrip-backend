from app import create_app
from database import db
from models import Product

app = create_app()

def seed():
    with app.app_context():
        # Clear existing products
        Product.query.delete()
        
        items = [
            Product(name="Essential Black Hoodie", description="Heavyweight cotton blend, oversized fit.", price=45.0, category="Hoodies & Sweatshirts", stock=20, image_url="/assets/products/hoodie.jpg", sizes="S,M,L,XL,XXL"),
            Product(name="Urban Cargo Pants", description="Multi-pocket utility pants in olive green.", price=65.0, category="Pants & Shorts", stock=15, image_url="/assets/products/cargo.jpg", sizes="30,32,34,36"),
            Product(name="Drip Graphic Tee", description="Limited edition streetwear graphic.", price=30.0, category="T-Shirts", stock=50, image_url="/assets/products/tee.jpg", sizes="S,M,L,XL"),
            Product(name="Street Queen Bomber", description="Satin finish bomber jacket for women.", price=85.0, category="Jackets", stock=10, image_url="/assets/products/jacket.jpg", sizes="XS,S,M,L"),
            Product(name="Classic Polo Shirt", description="Premium cotton polo with urban design.", price=35.0, category="Polos", stock=25, image_url="/assets/products/polo.jpg", sizes="S,M,L,XL"),
            Product(name="Button Down Shirt", description="Slim fit button down shirt.", price=40.0, category="Shirts", stock=18, image_url="/assets/products/shirt.jpg", sizes="S,M,L,XL"),
            Product(name="Oversized Hoodie", description="Extra large fit hoodie for comfort.", price=55.0, category="Hoodies & Sweatshirts", stock=12, image_url="/assets/products/hoodie2.jpg", sizes="S,M,L,XL,XXL"),
            Product(name="Cargo Shorts", description="Military style cargo shorts.", price=45.0, category="Pants & Shorts", stock=22, image_url="/assets/products/shorts.jpg", sizes="30,32,34,36"),
        ]
        
        db.session.bulk_save_objects(items)
        db.session.commit()
        print("Database seeded with fresh drip!")

if __name__ == "__main__":
    seed()