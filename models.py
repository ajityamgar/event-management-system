# models.py - Production-Ready Event Management System Database Models
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import enum

db = SQLAlchemy()


class UserRole(enum.Enum):
    CLIENT = "CLIENT"
    ADMIN = "ADMIN"


class EventStatus(enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PaymentStatus(enum.Enum):
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


# ============================================
# USER MODEL
# ============================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    address = db.Column(db.Text)
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    pincode = db.Column(db.String(10))
    birthday = db.Column(db.Date)
    profile_image = db.Column(db.String(255))
    
    # Account settings
    role = db.Column(db.Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    email_verified = db.Column(db.Boolean, default=False)
    phone_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    events = db.relationship('Event', backref='client', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        return self.role == UserRole.ADMIN
    
    def is_client(self):
        return self.role == UserRole.CLIENT
    
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.username


# ============================================
# VENUE MODEL
# ============================================
class Venue(db.Model):
    __tablename__ = 'venues'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    description = db.Column(db.Text)
    location = db.Column(db.String(255), nullable=False, index=True)
    city = db.Column(db.String(50), index=True)
    state = db.Column(db.String(50))
    
    # Capacity and pricing
    capacity = db.Column(db.Integer, nullable=False, index=True)
    base_rent = db.Column(db.Float, nullable=False)
    additional_cost_per_hour = db.Column(db.Float, default=0)
    
    # Facilities and amenities
    facilities = db.Column(db.JSON, default={})
    amenities = db.Column(db.JSON, default={})
    
    # Rules and policies
    parking_capacity = db.Column(db.Integer, default=0)
    ac_available = db.Column(db.Boolean, default=True)
    catering_allowed = db.Column(db.Boolean, default=True)
    outside_catering_allowed = db.Column(db.Boolean, default=False)
    music_allowed = db.Column(db.Boolean, default=True)
    decoration_allowed = db.Column(db.Boolean, default=True)
    alcohol_allowed = db.Column(db.Boolean, default=False)
    smoking_allowed = db.Column(db.Boolean, default=False)
    
    # Operating hours
    opening_time = db.Column(db.String(5))  # HH:MM format
    closing_time = db.Column(db.String(5))
    
    # Contact information
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    
    # Media
    images = db.Column(db.JSON, default=[])
    
    # Rating and availability
    rating = db.Column(db.Float, default=0)
    reviews_count = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='venue', lazy=True)
    
    def __repr__(self):
        return f'<Venue {self.name}>'
    
    def get_price_for_guests(self, guest_count):
        """Calculate venue price based on guest count"""
        return self.base_rent
    
    def is_suitable_for_guests(self, guest_count):
        """Check if venue can accommodate guest count"""
        return guest_count <= self.capacity


# ============================================
# PACKAGE MODEL
# ============================================
class Package(db.Model):
    __tablename__ = 'packages'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    package_type = db.Column(db.String(50), nullable=False)  # Basic, Standard, Premium
    description = db.Column(db.Text)
    
    # Pricing
    base_price = db.Column(db.Float, nullable=False)
    price_per_guest = db.Column(db.Float, default=0)
    
    # Package details
    max_guests = db.Column(db.Integer)
    duration_hours = db.Column(db.Integer, default=4)
    setup_time = db.Column(db.Integer, default=2)
    cleanup_time = db.Column(db.Integer, default=1)
    
    # Services and features
    features = db.Column(db.JSON, default=[])
    decoration_type = db.Column(db.String(50))
    menu_type = db.Column(db.String(50))
    menu_items = db.Column(db.JSON, default=[])
    services_included = db.Column(db.JSON, default=[])
    
    # Policies
    cancellation_policy = db.Column(db.Text)
    additional_notes = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    events = db.relationship('Event', backref='package', lazy=True)
    
    def __repr__(self):
        return f'<Package {self.name}>'
    
    def calculate_cost(self, guest_count):
        """Calculate total package cost based on guest count"""
        return self.base_price + (self.price_per_guest * guest_count if self.price_per_guest else 0)


# ============================================
# VENDOR MODEL
# ============================================
class Vendor(db.Model):
    __tablename__ = 'vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    vendor_type = db.Column(db.String(50), nullable=False, index=True)  # Catering, Photography, DJ, etc.
    description = db.Column(db.Text)
    
    # Services
    services = db.Column(db.JSON, default=[])
    
    # Pricing
    base_price = db.Column(db.Float)
    hourly_rate = db.Column(db.Float)
    price_per_guest = db.Column(db.Float)
    
    # Contact information
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(120))
    website = db.Column(db.String(255))
    
    # Details
    address = db.Column(db.Text)
    business_hours = db.Column(db.String(200))
    experience_years = db.Column(db.Integer)
    
    # Media
    portfolio_images = db.Column(db.JSON, default=[])
    portfolio_links = db.Column(db.JSON, default=[])
    
    # Rating and availability
    rating = db.Column(db.Float, default=0)
    reviews_count = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    event_vendors = db.relationship('EventVendor', backref='vendor', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Vendor {self.name}>'


# ============================================
# EVENT MODEL
# ============================================
class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    name = db.Column(db.String(150), nullable=False, index=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # Birthday, Wedding, Corporate, etc.
    description = db.Column(db.Text)
    
    # Date and time
    event_date = db.Column(db.DateTime, nullable=False, index=True)
    event_time = db.Column(db.String(5))  # HH:MM format
    estimated_duration = db.Column(db.Integer, default=4)  # Hours
    
    # Guests
    expected_guest_count = db.Column(db.Integer, nullable=False, index=True)
    actual_guest_count = db.Column(db.Integer)
    
    # Associated data
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), index=True)
    package_id = db.Column(db.Integer, db.ForeignKey('packages.id'), index=True)
    
    # Special requirements
    dietary_requirements = db.Column(db.JSON, default=[])
    special_requests = db.Column(db.Text)
    
    # Status and tracking
    status = db.Column(db.Enum(EventStatus), default=EventStatus.PENDING, index=True)
    admin_notes = db.Column(db.Text)
    approval_date = db.Column(db.DateTime)
    
    # Payment tracking
    total_budget = db.Column(db.Float)
    total_cost = db.Column(db.Float, default=0)
    
    # Ratings and feedback (post-event)
    rating = db.Column(db.Integer)  # 1-5 stars
    feedback = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    guests = db.relationship('Guest', backref='event', lazy=True, cascade='all, delete-orphan')
    event_vendors = db.relationship('EventVendor', backref='event', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    def calculate_total_cost(self):
        """Calculate total cost of the event"""
        cost = 0
        
        # Package cost
        if self.package:
            cost += self.package.calculate_cost(self.expected_guest_count)
        
        # Venue cost
        if self.venue:
            cost += self.venue.get_price_for_guests(self.expected_guest_count)
        
        # Vendor costs
        for event_vendor in self.event_vendors:
            cost += event_vendor.total_cost
        
        self.total_cost = cost
        return cost
    
    def get_total_paid(self):
        """Get total amount paid so far"""
        return sum(p.amount for p in self.payments if p.status == PaymentStatus.PAID)
    
    def get_remaining_amount(self):
        """Get remaining amount to be paid"""
        return max(0, self.total_cost - self.get_total_paid())
    
    @property
    def is_upcoming(self):
        """Check if event is upcoming"""
        return self.event_date > datetime.utcnow() and self.status != EventStatus.CANCELLED
    
    @property
    def is_editable(self):
        """Check if event can be edited"""
        return self.status in [EventStatus.PENDING, EventStatus.APPROVED]


# ============================================
# GUEST MODEL
# ============================================
class Guest(db.Model):
    __tablename__ = 'guests'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Basic information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Event association
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    
    # Dietary and special requirements
    dietary_restrictions = db.Column(db.JSON, default=[])
    special_needs = db.Column(db.Text)
    
    # RSVP tracking
    rsvp_status = db.Column(db.String(20), default='PENDING')  # PENDING, CONFIRMED, DECLINED
    rsvp_date = db.Column(db.DateTime)
    plus_one_count = db.Column(db.Integer, default=0)
    
    # Additional information
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Guest {self.first_name} {self.last_name}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


# ============================================
# EVENT VENDOR JUNCTION TABLE
# ============================================
class EventVendor(db.Model):
    __tablename__ = 'event_vendors'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign keys
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False, index=True)
    
    # Vendor-specific details for this event
    quantity = db.Column(db.Integer, default=1)
    custom_price = db.Column(db.Float)  # If different from standard vendor price
    custom_services = db.Column(db.JSON, default=[])
    
    # Booking details
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    confirmation_date = db.Column(db.DateTime)
    cancellation_date = db.Column(db.DateTime)
    is_confirmed = db.Column(db.Boolean, default=False)
    
    # Notes
    notes = db.Column(db.Text)
    
    @property
    def total_cost(self):
        """Calculate total cost for this vendor assignment"""
        price = self.custom_price if self.custom_price else (self.vendor.base_price or 0)
        return price * self.quantity


# ============================================
# PAYMENT MODEL
# ============================================
class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Association
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Payment details
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    payment_method = db.Column(db.String(50))  # Credit Card, Debit Card, UPI, Net Banking, etc.
    
    # Transaction information
    transaction_id = db.Column(db.String(100), unique=True)
    receipt_number = db.Column(db.String(50))
    
    # Billing information
    billing_name = db.Column(db.String(120))
    billing_email = db.Column(db.String(120))
    billing_phone = db.Column(db.String(20))
    billing_address = db.Column(db.Text)
    gst_number = db.Column(db.String(20))
    
    # Dates
    payment_date = db.Column(db.DateTime)
    due_date = db.Column(db.DateTime)
    
    # Refund information
    is_refunded = db.Column(db.Boolean, default=False)
    refund_amount = db.Column(db.Float)
    refund_date = db.Column(db.DateTime)
    refund_reason = db.Column(db.Text)
    
    # Currency and notes
    currency = db.Column(db.String(3), default='INR')
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.transaction_id}>'


# ============================================
# AUDIT LOG MODEL (for admin tracking)
# ============================================
class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Action details
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=False)  # Event, Payment, User, etc.
    entity_id = db.Column(db.Integer)
    
    # Admin who performed the action
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    admin = db.relationship('User', backref='audit_logs')
    
    # Details
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    description = db.Column(db.Text)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} on {self.entity_type}>'
