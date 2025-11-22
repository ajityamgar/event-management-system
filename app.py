# app.py - Production-Ready Event Management System
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Import models
from models import (
    db, User, Event, Venue, Package, Vendor, Payment, Guest, EventVendor,
    AuditLog, UserRole, EventStatus, PaymentStatus
)


def create_app():
    app = Flask(__name__)

       
# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///events.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', False)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ============================================
# DECORATORS
# ============================================
def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def client_required(f):
    """Decorator to require client role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_client():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def log_audit(action, entity_type, entity_id, old_values=None, new_values=None, description=None):
    """Log an audit entry"""
    if current_user.is_authenticated and current_user.is_admin():
        audit = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            admin_id=current_user.id,
            old_values=old_values,
            new_values=new_values,
            description=description
        )
        db.session.add(audit)
        db.session.commit()


# ============================================
# CONTEXT PROCESSORS
# ============================================
@app.context_processor
def inject_globals():
    """Inject global variables into templates"""
    return {
        'current_date': datetime.utcnow(),
        'EventStatus': EventStatus,
        'PaymentStatus': PaymentStatus
    }


# ============================================
# ERROR HANDLERS
# ============================================
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template('errors/403.html'), 403


@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}')
    db.session.rollback()
    return render_template('errors/500.html'), 500


# ============================================
# AUTHENTICATION ROUTES
# ============================================
@app.route('/')
def home():
    """Home page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))
    
    # Get statistics for home page
    packages = Package.query.filter_by(is_active=True).limit(6).all()
    venues = Venue.query.filter_by(is_available=True).limit(6).all()
    
    return render_template('home.html', packages=packages, venues=venues)


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            phone = request.form.get('phone', '').strip()
            
            # Validation
            if not all([username, email, password, confirm_password]):
                flash('All fields are required!', 'error')
                return redirect(url_for('register'))
            
            if len(password) < 8:
                flash('Password must be at least 8 characters long!', 'error')
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('register'))
            
            if len(username) < 3:
                flash('Username must be at least 3 characters long!', 'error')
                return redirect(url_for('register'))
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists!', 'error')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first():
                flash('Email already registered!', 'error')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password=generate_password_hash(password),
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                role=UserRole.CLIENT
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Registration error: {e}')
            flash('An error occurred during registration. Please try again.', 'error')
            return redirect(url_for('register'))
    
    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)
            
            if not username or not password:
                flash('Username and password are required!', 'error')
                return redirect(url_for('login'))
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                if not user.is_active:
                    flash('Your account has been deactivated.', 'error')
                    return redirect(url_for('login'))
                
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                flash(f'Welcome back, {user.username}!', 'success')
                
                next_page = request.args.get('next')
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                
                if user.is_admin():
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('client_dashboard'))
            else:
                flash('Invalid username or password!', 'error')
                return redirect(url_for('login'))
                
        except Exception as e:
            logger.error(f'Login error: {e}')
            flash('An error occurred during login. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))


# ============================================
# CLIENT ROUTES (Blueprint-like organization)
# ============================================
@app.route('/client/dashboard')
@login_required
@client_required
def client_dashboard():
    """Client dashboard"""
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.created_at.desc()).all()
    
    # Statistics
    total_events = len(events)
    upcoming_events = len([e for e in events if e.is_upcoming])
    completed_events = len([e for e in events if e.status == EventStatus.COMPLETED])
    total_spent = sum(e.total_cost or 0 for e in events)
    
    return render_template('client/dashboard.html',
                          events=events,
                          total_events=total_events,
                          upcoming_events=upcoming_events,
                          completed_events=completed_events,
                          total_spent=total_spent)


@app.route('/client/profile', methods=['GET', 'POST'])
@login_required
@client_required
def client_profile():
    """Client profile management"""
    if request.method == 'POST':
        try:
            current_user.first_name = request.form.get('first_name', '').strip()
            current_user.last_name = request.form.get('last_name', '').strip()
            current_user.email = request.form.get('email', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.address = request.form.get('address', '').strip()
            current_user.city = request.form.get('city', '').strip()
            current_user.state = request.form.get('state', '').strip()
            current_user.pincode = request.form.get('pincode', '').strip()
            
            birthday = request.form.get('birthday')
            if birthday:
                current_user.birthday = datetime.strptime(birthday, '%Y-%m-%d').date()
            
            new_password = request.form.get('new_password', '').strip()
            if new_password:
                if len(new_password) < 8:
                    flash('Password must be at least 8 characters!', 'error')
                    return redirect(url_for('client_profile'))
                current_user.password = generate_password_hash(new_password)
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('client_profile'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Profile update error: {e}')
            flash('An error occurred while updating profile!', 'error')
            return redirect(url_for('client_profile'))
    
    return render_template('client/profile.html', user=current_user)


@app.route('/client/event/create', methods=['GET', 'POST'])
@login_required
@client_required
def create_event():
    """Create new event"""
    packages = Package.query.filter_by(is_active=True).all()
    venues = Venue.query.filter_by(is_available=True).all()
    
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            event_type = request.form.get('event_type', '').strip()
            event_date_str = request.form.get('event_date', '')
            event_time = request.form.get('event_time', '14:00')
            expected_guest_count = request.form.get('expected_guest_count', 0)
            package_id = request.form.get('package_id')
            venue_id = request.form.get('venue_id')
            description = request.form.get('description', '').strip()
            special_requests = request.form.get('special_requests', '').strip()
            
            # Validation
            if not all([name, event_type, event_date_str, expected_guest_count]):
                flash('Please fill in all required fields!', 'error')
                return redirect(url_for('create_event'))
            
            try:
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                expected_guest_count = int(expected_guest_count)
                
                if expected_guest_count <= 0:
                    flash('Guest count must be positive!', 'error')
                    return redirect(url_for('create_event'))
                
                if event_date <= datetime.utcnow():
                    flash('Event date must be in the future!', 'error')
                    return redirect(url_for('create_event'))
                
            except ValueError as e:
                flash('Invalid date or guest count format!', 'error')
                return redirect(url_for('create_event'))
            
            # Check venue capacity
            if venue_id:
                venue = Venue.query.get(venue_id)
                if venue and not venue.is_suitable_for_guests(expected_guest_count):
                    flash(f'Venue capacity ({venue.capacity}) is less than expected guests!', 'error')
                    return redirect(url_for('create_event'))
            
            # Create event
            event = Event(
                name=name,
                event_type=event_type,
                event_date=event_date,
                event_time=event_time,
                expected_guest_count=expected_guest_count,
                user_id=current_user.id,
                package_id=package_id if package_id else None,
                venue_id=venue_id if venue_id else None,
                description=description,
                special_requests=special_requests,
                status=EventStatus.PENDING
            )
            
            # Calculate total cost
            event.calculate_total_cost()
            
            db.session.add(event)
            db.session.commit()
            
            log_audit('CREATE', 'Event', event.id, None, 
                     {'name': name, 'type': event_type}, 'Event created by client')
            
            flash(f'Event "{name}" created successfully!', 'success')
            return redirect(url_for('view_event', event_id=event.id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Event creation error: {e}')
            flash('An error occurred while creating event!', 'error')
            return redirect(url_for('create_event'))
    
    return render_template('client/create_event.html', packages=packages, venues=venues)


@app.route('/client/event/<int:event_id>')
@login_required
def view_event(event_id):
    """View event details"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view this event!', 'error')
        return redirect(url_for('home'))
    
    return render_template('client/view_event.html', event=event)


@app.route('/client/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    """Edit event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to edit this event!', 'error')
        return redirect(url_for('home'))
    
    # Check if event can be edited
    if not event.is_editable:
        flash('This event cannot be edited in its current status!', 'error')
        return redirect(url_for('view_event', event_id=event_id))
    
    packages = Package.query.filter_by(is_active=True).all()
    venues = Venue.query.filter_by(is_available=True).all()
    
    if request.method == 'POST':
        try:
            event.name = request.form.get('name', '').strip()
            event.event_type = request.form.get('event_type', '').strip()
            event_date_str = request.form.get('event_date', '')
            event.event_time = request.form.get('event_time', '14:00')
            event.expected_guest_count = int(request.form.get('expected_guest_count', 1))
            event.package_id = request.form.get('package_id') or None
            event.venue_id = request.form.get('venue_id') or None
            event.description = request.form.get('description', '').strip()
            event.special_requests = request.form.get('special_requests', '').strip()
            
            if event_date_str:
                event.event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
            
            # Recalculate total cost
            event.calculate_total_cost()
            event.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            log_audit('UPDATE', 'Event', event.id, None, None, 'Event updated by client')
            
            flash('Event updated successfully!', 'success')
            return redirect(url_for('view_event', event_id=event_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'Event edit error: {e}')
            flash('An error occurred while updating event!', 'error')
            return redirect(url_for('edit_event', event_id=event_id))
    
    return render_template('client/edit_event.html', event=event, packages=packages, venues=venues)


@app.route('/client/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to delete this event!', 'error')
        return redirect(url_for('home'))
    
    # Check if event can be deleted
    if event.status not in [EventStatus.PENDING, EventStatus.REJECTED]:
        flash('Only pending or rejected events can be deleted!', 'error')
        return redirect(url_for('view_event', event_id=event_id))
    
    try:
        event_name = event.name
        db.session.delete(event)
        db.session.commit()
        
        log_audit('DELETE', 'Event', event_id, None, None, f'Event deleted by client')
        
        flash(f'Event "{event_name}" deleted successfully!', 'success')
        return redirect(url_for('client_dashboard'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Event deletion error: {e}')
        flash('An error occurred while deleting event!', 'error')
        return redirect(url_for('view_event', event_id=event_id))


# ============================================
# GUEST MANAGEMENT ROUTES
# ============================================
@app.route('/client/event/<int:event_id>/guests')
@login_required
def manage_guests(event_id):
    """Manage guest list"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view guests!', 'error')
        return redirect(url_for('home'))
    
    guests = Guest.query.filter_by(event_id=event_id).all()
    return render_template('client/manage_guests.html', event=event, guests=guests)


@app.route('/client/event/<int:event_id>/guest/add', methods=['POST'])
@login_required
def add_guest(event_id):
    """Add guest to event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to add guests!', 'error')
        return redirect(url_for('home'))
    
    try:
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        dietary_restrictions = request.form.getlist('dietary_restrictions[]')
        special_needs = request.form.get('special_needs', '').strip()
        
        if not all([first_name, last_name]):
            flash('First and last name are required!', 'error')
            return redirect(url_for('manage_guests', event_id=event_id))
        
        guest = Guest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            event_id=event_id,
            dietary_restrictions=dietary_restrictions,
            special_needs=special_needs
        )
        
        db.session.add(guest)
        db.session.commit()
        
        log_audit('CREATE', 'Guest', guest.id, None, None, f'Guest added to event {event_id}')
        
        flash(f'Guest "{guest.full_name}" added successfully!', 'success')
        return redirect(url_for('manage_guests', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Add guest error: {e}')
        flash('An error occurred while adding guest!', 'error')
        return redirect(url_for('manage_guests', event_id=event_id))


@app.route('/client/event/<int:event_id>/guest/<int:guest_id>/delete', methods=['POST'])
@login_required
def delete_guest(event_id, guest_id):
    """Delete guest"""
    event = Event.query.get_or_404(event_id)
    guest = Guest.query.get_or_404(guest_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to delete guests!', 'error')
        return redirect(url_for('home'))
    
    try:
        guest_name = guest.full_name
        db.session.delete(guest)
        db.session.commit()
        
        log_audit('DELETE', 'Guest', guest_id, None, None, f'Guest deleted from event {event_id}')
        
        flash(f'Guest "{guest_name}" deleted successfully!', 'success')
        return redirect(url_for('manage_guests', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Delete guest error: {e}')
        flash('An error occurred while deleting guest!', 'error')
        return redirect(url_for('manage_guests', event_id=event_id))


# ============================================
# VENDOR MANAGEMENT ROUTES
# ============================================
@app.route('/client/event/<int:event_id>/vendors')
@login_required
def manage_vendors(event_id):
    """Manage event vendors"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view vendors!', 'error')
        return redirect(url_for('home'))
    
    event_vendors = EventVendor.query.filter_by(event_id=event_id).all()
    available_vendors = Vendor.query.filter_by(is_available=True).all()
    
    return render_template('client/manage_vendors.html',
                          event=event,
                          event_vendors=event_vendors,
                          available_vendors=available_vendors)


@app.route('/client/event/<int:event_id>/vendor/add', methods=['POST'])
@login_required
def add_vendor(event_id):
    """Add vendor to event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to add vendors!', 'error')
        return redirect(url_for('home'))
    
    try:
        vendor_id = request.form.get('vendor_id')
        quantity = request.form.get('quantity', 1)
        custom_price = request.form.get('custom_price')
        notes = request.form.get('notes', '').strip()
        
        vendor = Vendor.query.get_or_404(vendor_id)
        quantity = int(quantity)
        
        if quantity <= 0:
            flash('Quantity must be positive!', 'error')
            return redirect(url_for('manage_vendors', event_id=event_id))
        
        # Check if vendor already added
        existing = EventVendor.query.filter_by(event_id=event_id, vendor_id=vendor_id).first()
        if existing:
            flash('This vendor is already added to the event!', 'error')
            return redirect(url_for('manage_vendors', event_id=event_id))
        
        event_vendor = EventVendor(
            event_id=event_id,
            vendor_id=vendor_id,
            quantity=quantity,
            custom_price=float(custom_price) if custom_price else None,
            notes=notes
        )
        
        db.session.add(event_vendor)
        event.calculate_total_cost()
        db.session.commit()
        
        log_audit('CREATE', 'EventVendor', event_vendor.id, None, None, 
                 f'Vendor {vendor.name} added to event {event_id}')
        
        flash(f'Vendor "{vendor.name}" added successfully!', 'success')
        return redirect(url_for('manage_vendors', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Add vendor error: {e}')
        flash('An error occurred while adding vendor!', 'error')
        return redirect(url_for('manage_vendors', event_id=event_id))


@app.route('/client/event/<int:event_id>/vendor/<int:vendor_id>/delete', methods=['POST'])
@login_required
def remove_vendor(event_id, vendor_id):
    """Remove vendor from event"""
    event = Event.query.get_or_404(event_id)
    event_vendor = EventVendor.query.filter_by(event_id=event_id, vendor_id=vendor_id).first_or_404()
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to remove vendors!', 'error')
        return redirect(url_for('home'))
    
    try:
        vendor_name = event_vendor.vendor.name
        db.session.delete(event_vendor)
        event.calculate_total_cost()
        db.session.commit()
        
        log_audit('DELETE', 'EventVendor', event_vendor.id, None, None,
                 f'Vendor removed from event {event_id}')
        
        flash(f'Vendor "{vendor_name}" removed successfully!', 'success')
        return redirect(url_for('manage_vendors', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Remove vendor error: {e}')
        flash('An error occurred while removing vendor!', 'error')
        return redirect(url_for('manage_vendors', event_id=event_id))


# ============================================
# PAYMENT ROUTES
# ============================================
@app.route('/client/event/<int:event_id>/payment')
@login_required
def view_payment(event_id):
    """View payment details for event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view payment!', 'error')
        return redirect(url_for('home'))
    
    total_paid = event.get_total_paid()
    remaining = event.get_remaining_amount()
    payments = Payment.query.filter_by(event_id=event_id).order_by(Payment.created_at.desc()).all()
    
    return render_template('client/payment.html',
                          event=event,
                          total_paid=total_paid,
                          remaining=remaining,
                          payments=payments)


@app.route('/client/event/<int:event_id>/payment/make', methods=['POST'])
@login_required
def make_payment(event_id):
    """Record payment for event"""
    event = Event.query.get_or_404(event_id)
    
    # Check authorization
    if event.user_id != current_user.id:
        flash('You do not have permission to make payment!', 'error')
        return redirect(url_for('home'))
    
    try:
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method', '')
        
        if amount <= 0:
            flash('Payment amount must be positive!', 'error')
            return redirect(url_for('view_payment', event_id=event_id))
        
        remaining = event.get_remaining_amount()
        if amount > remaining:
            flash(f'Payment amount exceeds remaining balance (₹{remaining:.2f})!', 'error')
            return redirect(url_for('view_payment', event_id=event_id))
        
        # Create payment record (mock payment processing)
        payment = Payment(
            event_id=event_id,
            user_id=current_user.id,
            amount=amount,
            payment_method=payment_method,
            status=PaymentStatus.PAID,
            payment_date=datetime.utcnow(),
            transaction_id=f"TXN{int(datetime.utcnow().timestamp())}",
            receipt_number=f"RCP{int(datetime.utcnow().timestamp())}"
        )
        
        db.session.add(payment)
        db.session.commit()
        
        log_audit('CREATE', 'Payment', payment.id, None, 
                 {'amount': amount, 'method': payment_method}, 
                 f'Payment made for event {event_id}')
        
        flash(f'Payment of ₹{amount:.2f} recorded successfully!', 'success')
        return redirect(url_for('view_payment', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Payment error: {e}')
        flash('An error occurred while processing payment!', 'error')
        return redirect(url_for('view_payment', event_id=event_id))


# ============================================
# ADMIN ROUTES
# ============================================
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    # Statistics
    total_users = User.query.filter_by(role=UserRole.CLIENT).count()
    total_events = Event.query.count()
    pending_events = Event.query.filter_by(status=EventStatus.PENDING).count()
    total_revenue = sum(p.amount for p in Payment.query.filter_by(status=PaymentStatus.PAID).all())
    
    # Recent events
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(10).all()
    
    # Events by status
    status_breakdown = {}
    for status in EventStatus:
        count = Event.query.filter_by(status=status).count()
        status_breakdown[status.value] = count
    
    return render_template('admin/dashboard.html',
                          total_users=total_users,
                          total_events=total_events,
                          pending_events=pending_events,
                          total_revenue=total_revenue,
                          recent_events=recent_events,
                          status_breakdown=status_breakdown)


@app.route('/admin/events')
@login_required
@admin_required
def admin_events():
    """Manage all events"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Event.query
    if status_filter:
        query = query.filter_by(status=EventStatus[status_filter])
    
    events = query.order_by(Event.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/events.html',
                          events=events,
                          statuses=EventStatus,
                          selected_status=status_filter)


@app.route('/admin/event/<int:event_id>')
@login_required
@admin_required
def admin_view_event(event_id):
    """View event details as admin"""
    event = Event.query.get_or_404(event_id)
    return render_template('admin/view_event.html', event=event)


@app.route('/admin/event/<int:event_id>/status', methods=['POST'])
@login_required
@admin_required
def update_event_status(event_id):
    """Update event status"""
    event = Event.query.get_or_404(event_id)
    
    try:
        new_status = request.form.get('status', '')
        admin_notes = request.form.get('admin_notes', '').strip()
        
        if new_status not in [s.name for s in EventStatus]:
            flash('Invalid status!', 'error')
            return redirect(url_for('admin_view_event', event_id=event_id))
        
        old_status = event.status.value
        event.status = EventStatus[new_status]
        event.admin_notes = admin_notes
        
        if new_status == 'APPROVED':
            event.approval_date = datetime.utcnow()
        
        db.session.commit()
        
        log_audit('UPDATE', 'Event', event_id,
                 {'status': old_status},
                 {'status': new_status},
                 f'Event status updated to {new_status}')
        
        flash(f'Event status updated to {new_status}!', 'success')
        return redirect(url_for('admin_view_event', event_id=event_id))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Status update error: {e}')
        flash('An error occurred while updating status!', 'error')
        return redirect(url_for('admin_view_event', event_id=event_id))


@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Manage all users"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    
    query = User.query
    if role_filter:
        query = query.filter_by(role=UserRole[role_filter])
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('admin/users.html',
                          users=users,
                          roles=UserRole,
                          selected_role=role_filter)


@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account!', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        status = 'activated' if user.is_active else 'deactivated'
        log_audit('UPDATE', 'User', user_id,
                 {'is_active': not user.is_active},
                 {'is_active': user.is_active},
                 f'User {status}')
        
        flash(f'User {user.username} {status} successfully!', 'success')
        return redirect(url_for('admin_users'))
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Toggle user error: {e}')
        flash('An error occurred!', 'error')
        return redirect(url_for('admin_users'))


@app.route('/admin/venues')
@login_required
@admin_required
def admin_venues():
    """Manage venues"""
    page = request.args.get('page', 1, type=int)
    venues = Venue.query.order_by(Venue.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/venues.html', venues=venues)


@app.route('/admin/vendors')
@login_required
@admin_required
def admin_vendors():
    """Manage vendors"""
    page = request.args.get('page', 1, type=int)
    vendors = Vendor.query.order_by(Vendor.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/vendors.html', vendors=vendors)


@app.route('/admin/packages')
@login_required
@admin_required
def admin_packages():
    """Manage packages"""
    page = request.args.get('page', 1, type=int)
    packages = Package.query.order_by(Package.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/packages.html', packages=packages)


# ============================================
# API ENDPOINTS
# ============================================
@app.route('/api/venues/filter')
def api_filter_venues():
    """Filter venues by capacity and other criteria"""
    try:
        min_capacity = request.args.get('min_capacity', 0, type=int)
        max_capacity = request.args.get('max_capacity', 10000, type=int)
        city = request.args.get('city', '')
        
        query = Venue.query.filter(
            Venue.is_available == True,
            Venue.capacity >= min_capacity,
            Venue.capacity <= max_capacity
        )
        
        if city:
            query = query.filter_by(city=city)
        
        venues = query.all()
        
        return jsonify({
            'success': True,
            'venues': [
                {
                    'id': v.id,
                    'name': v.name,
                    'capacity': v.capacity,
                    'location': v.location,
                    'base_rent': v.base_rent,
                    'rating': v.rating
                }
                for v in venues
            ]
        })
        
    except Exception as e:
        logger.error(f'API filter venues error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/packages/<int:package_id>')
def api_get_package(package_id):
    """Get package details"""
    try:
        package = Package.query.get_or_404(package_id)
        
        return jsonify({
            'success': True,
            'package': {
                'id': package.id,
                'name': package.name,
                'description': package.description,
                'base_price': package.base_price,
                'price_per_guest': package.price_per_guest,
                'max_guests': package.max_guests,
                'features': package.features,
                'services_included': package.services_included
            }
        })
        
    except Exception as e:
        logger.error(f'API get package error: {e}')
        return jsonify({'success': False, 'error': str(e)}), 400


# ============================================
# DATABASE INITIALIZATION
# ============================================
def init_database():
    """Initialize database with default data"""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if User.query.filter_by(username='Admin').first():
            return
        
        print("Initializing database with default data...")
        
        # Create admin user
        admin = User(
            username='Admin',
            email='admin@eventmanagement.com',
            password=generate_password_hash('Admin@123'),
            first_name='Admin',
            role=UserRole.ADMIN,
            is_active=True
        )
        db.session.add(admin)
        
        # Create sample venues
        venues_data = [
            {
                'name': 'Grand Ballroom Palace',
                'city': 'Mumbai',
                'location': 'Downtown Mumbai',
                'capacity': 500,
                'base_rent': 150000,
                'description': 'Luxurious ballroom perfect for grand celebrations'
            },
            {
                'name': 'Elite Event Center',
                'city': 'Pune',
                'location': 'Pune Central',
                'capacity': 300,
                'base_rent': 100000,
                'description': 'Modern event center with premium amenities'
            },
            {
                'name': 'Garden Villa Resort',
                'city': 'Bangalore',
                'location': 'Whitefield',
                'capacity': 200,
                'base_rent': 80000,
                'description': 'Beautiful garden venue for outdoor events'
            },
            {
                'name': 'Urban Banquet Hall',
                'city': 'Delhi',
                'location': 'New Delhi',
                'capacity': 250,
                'base_rent': 75000,
                'description': 'Contemporary banquet hall in heart of city'
            },
            {
                'name': 'Riverside Convention',
                'city': 'Kolkata',
                'location': 'South Kolkata',
                'capacity': 400,
                'base_rent': 120000,
                'description': 'Convention center with riverside views'
            }
        ]
        
        for venue_data in venues_data:
            venue = Venue(**venue_data)
            db.session.add(venue)
        
        # Create sample packages
        packages_data = [
            {
                'name': 'Starter Package',
                'package_type': 'Basic',
                'description': 'Perfect for small intimate gatherings',
                'base_price': 25000,
                'price_per_guest': 300,
                'max_guests': 100,
                'features': ['Basic decoration', 'Standard menu', 'Basic sound system']
            },
            {
                'name': 'Professional Package',
                'package_type': 'Standard',
                'description': 'Ideal for medium-sized events',
                'base_price': 60000,
                'price_per_guest': 500,
                'max_guests': 250,
                'features': ['Premium decoration', 'Deluxe menu', 'Professional AV', 'Photography']
            },
            {
                'name': 'Luxury Package',
                'package_type': 'Premium',
                'description': 'Ultimate experience for grand celebrations',
                'base_price': 150000,
                'price_per_guest': 1000,
                'max_guests': 500,
                'features': ['Designer decoration', 'Gourmet menu', 'Premium AV', 'Photo+Video', 'Live band']
            }
        ]
        
        for pkg_data in packages_data:
            package = Package(**pkg_data)
            db.session.add(package)
        
        # sample vendors
        vendors_data = [
            {
                'name': 'Gourmet Catering Co.',
                'vendor_type': 'Catering',
                'description': 'Premium catering services',
                'base_price': 10000,
                'price_per_guest': 250,
                'contact_email': 'catering@gourmet.com'
            },
            {
                'name': 'Pro Photography Studio',
                'vendor_type': 'Photography',
                'description': 'Professional photography and videography',
                'base_price': 15000,
                'contact_email': 'photos@pro.com'
            },
            {
                'name': 'DJ Sound Masters',
                'vendor_type': 'DJ & Music',
                'description': 'DJ services and sound equipment',
                'base_price': 8000,
                'hourly_rate': 2000,
                'contact_email': 'dj@soundmasters.com'
            },
            {
                'name': 'Floral Designs Ltd',
                'vendor_type': 'Decoration',
                'description': 'Flower arrangements and decorations',
                'base_price': 5000,
                'contact_email': 'flowers@floral.com'
            }
        ]
        
        for vendor_data in vendors_data:
            vendor = Vendor(**vendor_data)
            db.session.add(vendor)
        
        db.session.commit()
        print("✓ Database initialized successfully!")
        print("  Admin Credentials: Username: Admin, Password: Admin@123")
    return app

# ============================================
# RUN APPLICATION
# ============================================
if __name__ == '__main__':
    init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
