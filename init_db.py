from app import app, db
from models import Venue, Package, User
from werkzeug.security import generate_password_hash
import json

def init_db():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        # Create tables
        db.create_all()

        # Venue data
        venues = [
            {
                "name": "Shivaji Garden Hall",
                "location": "Pune West",
                "capacity": 50,
                "rent": 25000,
                "facilities": json.dumps([
                    "Parking",
                    "Air Conditioning",
                    "Basic Sound System",
                    "Garden Area",
                    "Changing Rooms"
                ]),
                "description": "Perfect for intimate gatherings with a beautiful garden setting"
            },
            {
                "name": "Mangal Karyalaya",
                "location": "Pune East",
                "capacity": 50,
                "rent": 20000,
                "facilities": json.dumps([
                    "Parking",
                    "Air Conditioning",
                    "Kitchen Area",
                    "Basic Decoration"
                ]),
                "description": "Traditional venue ideal for small functions and gatherings"
            },
            {
                "name": "Rajwada Banquet",
                "location": "Pune Central",
                "capacity": 100,
                "rent": 45000,
                "facilities": json.dumps([
                    "Valet Parking",
                    "Central AC",
                    "Premium Sound System",
                    "Stage",
                    "Green Room",
                    "Kitchen"
                ]),
                "description": "Royal ambiance with modern amenities"
            },
            {
                "name": "Sudarshan Auditorium",
                "location": "Pune North",
                "capacity": 100,
                "rent": 40000,
                "facilities": json.dumps([
                    "Large Parking",
                    "Air Conditioning",
                    "Professional Sound System",
                    "Projector",
                    "Dining Area"
                ]),
                "description": "Perfect blend of elegance and functionality"
            },
            {
                "name": "Saraswati Bhavan",
                "location": "Pune South",
                "capacity": 150,
                "rent": 60000,
                "facilities": json.dumps([
                    "Multilevel Parking",
                    "Central AC",
                    "Premium Audio System",
                    "Banquet Hall",
                    "Bride Room",
                    "Groom Room"
                ]),
                "description": "Luxurious venue with traditional touch"
            },
            {
                "name": "Ganesh Utsav Hall",
                "location": "Pune Central",
                "capacity": 150,
                "rent": 55000,
                "facilities": json.dumps([
                    "Spacious Parking",
                    "Air Conditioning",
                    "DJ Setup",
                    "Stage",
                    "Dining Hall"
                ]),
                "description": "Modern amenities with traditional architecture"
            },
            {
                "name": "Laxmi Convention Center",
                "location": "Pune West",
                "capacity": 200,
                "rent": 85000,
                "facilities": json.dumps([
                    "Multilevel Parking",
                    "Central AC",
                    "Premium Sound & Lighting",
                    "Grand Stage",
                    "VIP Lounge",
                    "Bridal Suite",
                    "Kitchen"
                ]),
                "description": "Luxurious space perfect for grand celebrations"
            },
            {
                "name": "Pune Palace Hall",
                "location": "Pune East",
                "capacity": 200,
                "rent": 80000,
                "facilities": json.dumps([
                    "Valet Parking",
                    "Central AC",
                    "Professional AV System",
                    "Grand Ballroom",
                    "Outdoor Garden",
                    "Changing Rooms"
                ]),
                "description": "Magnificent venue for memorable events"
            }
        ]

        # Package data
        packages = [
            {
                "name": "Basic Package",
                "type": "Basic",
                "description": "Essential services for your event",
                "price": 35000,
                "price_per_guest": 150,
                "features": json.dumps([
                    "Basic Decoration",
                    "Standard Menu (10 items)",
                    "Basic Sound System",
                    "4 Hours Duration",
                    "Basic Photography",
                    "Welcome Drinks"
                ]),
                "decoration_type": "Basic",
                "menu_type": "Standard",
                "services_included": json.dumps([
                    "Basic Lighting",
                    "Standard Seating",
                    "Basic Stage Setup",
                    "Service Staff",
                    "Clean-up Service"
                ]),
                "max_guests": 100,
                "duration_hours": 4,
                "setup_time": 2,
                "cleanup_time": 1,
                "cancellation_policy": "48 hours notice required for 80% refund"
            },
            {
                "name": "Standard Package",
                "type": "Standard",
                "description": "Enhanced services for a memorable celebration",
                "price": 75000,
                "price_per_guest": 250,
                "features": json.dumps([
                    "Premium Decoration",
                    "Deluxe Menu (15 items)",
                    "Professional Sound System",
                    "6 Hours Duration",
                    "Professional Photography",
                    "Video Coverage",
                    "DJ Services",
                    "Welcome Drinks & Snacks"
                ]),
                "decoration_type": "Premium",
                "menu_type": "Deluxe",
                "services_included": json.dumps([
                    "Theme Lighting",
                    "Premium Seating",
                    "Designer Stage",
                    "MC/Host",
                    "Valet Parking",
                    "Dedicated Event Coordinator"
                ]),
                "max_guests": 150,
                "duration_hours": 6,
                "setup_time": 3,
                "cleanup_time": 2,
                "cancellation_policy": "72 hours notice required for 75% refund"
            },
            {
                "name": "Premium Package",
                "type": "Premium",
                "description": "Luxury services for a grand celebration",
                "price": 150000,
                "price_per_guest": 500,
                "features": json.dumps([
                    "Luxury Decoration",
                    "Gourmet Menu (20 items)",
                    "Premium Sound & Lighting System",
                    "8 Hours Duration",
                    "Professional Photo & Video",
                    "Drone Coverage",
                    "360° Photo Booth",
                    "Live Band",
                    "Fireworks Display"
                ]),
                "decoration_type": "Luxury",
                "menu_type": "Gourmet",
                "services_included": json.dumps([
                    "Custom Theme Design",
                    "Premium Bar Setup",
                    "VIP Seating",
                    "Grand Stage & Dance Floor",
                    "Professional MC",
                    "Live Music",
                    "Valet Parking",
                    "Red Carpet Welcome",
                    "Celebrity Event Planner"
                ]),
                "max_guests": 200,
                "duration_hours": 8,
                "setup_time": 4,
                "cleanup_time": 2,
                "cancellation_policy": "96 hours notice required for 70% refund"
            }
        ]

        # Add venues if they don't exist (map legacy keys to model fields)
        for venue_data in venues:
            if not Venue.query.filter_by(name=venue_data['name']).first():
                v = {
                    'name': venue_data.get('name'),
                    'location': venue_data.get('location'),
                    'capacity': venue_data.get('capacity'),
                    'base_rent': venue_data.get('rent') or venue_data.get('base_rent'),
                    'description': venue_data.get('description'),
                    'facilities': json.loads(venue_data['facilities']) if isinstance(venue_data.get('facilities'), str) else venue_data.get('facilities') or [],
                }
                venue = Venue(**v)
                db.session.add(venue)

        # Add packages if they don't exist (map legacy keys)
        for package_data in packages:
            if not Package.query.filter_by(name=package_data['name']).first():
                p = {
                    'name': package_data.get('name'),
                    'package_type': package_data.get('type') or package_data.get('package_type'),
                    'description': package_data.get('description'),
                    'base_price': package_data.get('price') or package_data.get('base_price') or 0,
                    'price_per_guest': package_data.get('price_per_guest') or package_data.get('price_per_guest') or 0,
                    'features': json.loads(package_data['features']) if isinstance(package_data.get('features'), str) else package_data.get('features') or [],
                    'decoration_type': package_data.get('decoration_type'),
                    'menu_type': package_data.get('menu_type'),
                    'services_included': json.loads(package_data['services_included']) if isinstance(package_data.get('services_included'), str) else package_data.get('services_included') or [],
                    'max_guests': package_data.get('max_guests'),
                    'duration_hours': package_data.get('duration_hours'),
                    'setup_time': package_data.get('setup_time'),
                    'cleanup_time': package_data.get('cleanup_time'),
                    'cancellation_policy': package_data.get('cancellation_policy')
                }
                package = Package(**p)
                db.session.add(package)

        # Add admin user
        if not User.query.filter_by(username='Admin').first():
            admin = User(
                username='Admin',
                email='admin@eventmanagement.com',
                password=generate_password_hash('Admin@123')
            )
            db.session.add(admin)

        # Commit changes
        db.session.commit()
        print("Database initialized with venues, packages, and Admin user!")
        print("Admin Credentials - ID: Admin | Password: Admin@123")

if __name__ == '__main__':
    init_db()