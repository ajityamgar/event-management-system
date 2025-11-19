// script.js - Enhanced JS functionality for Event Management System
// Modal functions
function showLoginModal() {
    document.getElementById('loginModal').style.display = 'block';
}

function closeLoginModal() {
    document.getElementById('loginModal').style.display = 'none';
}

function showRegisterModal() {
    document.getElementById('registerModal').style.display = 'block';
}

function closeRegisterModal() {
    document.getElementById('registerModal').style.display = 'none';
}

// Close modals when clicking outside
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = 'none';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Dropdown Toggle
    const dropdowns = document.querySelectorAll('.nav-dropdown');
    dropdowns.forEach(dropdown => {
        const link = dropdown.querySelector('.nav-link');
        link.addEventListener('click', (e) => {
            if (window.innerWidth <= 768) {
                e.preventDefault();
                dropdown.classList.toggle('active');
                
                // Close other dropdowns
                dropdowns.forEach(other => {
                    if (other !== dropdown) {
                        other.classList.remove('active');
                    }
                });
            }
        });
    });

    // Close dropdowns when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav-dropdown')) {
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });

    // Get CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Add CSRF token to all AJAX requests
    const originalFetch = window.fetch;
    window.fetch = function() {
        const resource = arguments[0];
        const config = arguments[1] || {};
        
        if (config.method && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method.toUpperCase())) {
            if (!config.headers) config.headers = {};
            config.headers['X-CSRFToken'] = csrfToken;
        }
        
        return originalFetch.apply(this, arguments);
    };

    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(el => {
        tippy(el, {
            content: el.getAttribute('data-tooltip'),
            placement: 'top',
            animation: 'scale',
        });
    });

    // Form validation with improved UI feedback
    function validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        let valid = true;
        const errorMessages = {
            required: 'This field is required',
            email: 'Please enter a valid email address',
            date: 'Please enter a valid date',
            number: 'Please enter a valid number',
        };

        form.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
            const errorSpan = input.nextElementSibling;
            
            // Clear previous errors
            input.classList.remove('error');
            if (errorSpan?.classList.contains('error-message')) {
                errorSpan.remove();
            }

            // Validate field
            if (!input.value) {
                valid = false;
                input.classList.add('error');
                showError(input, errorMessages.required);
            } else if (input.type === 'email' && !validateEmail(input.value)) {
                valid = false;
                input.classList.add('error');
                showError(input, errorMessages.email);
            } else if (input.type === 'date' && !validateDate(input.value)) {
                valid = false;
                input.classList.add('error');
                showError(input, errorMessages.date);
            } else if (input.type === 'number' && !validateNumber(input.value)) {
                valid = false;
                input.classList.add('error');
                showError(input, errorMessages.number);
            }
        });

        return valid;
    }

    // Show error message
    function showError(input, message) {
        const errorSpan = document.createElement('span');
        errorSpan.className = 'error-message';
        errorSpan.textContent = message;
        input.parentNode.insertBefore(errorSpan, input.nextSibling);
    }

    // Validation helper functions
    function validateEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function validateDate(date) {
        return !isNaN(Date.parse(date));
    }

    function validateNumber(value) {
        return !isNaN(value) && value !== '';
    }

    // Dynamic price calculation
    function updateTotalPrice() {
        const packageSelect = document.getElementById('package_id');
        const venueSelect = document.getElementById('venue_id');
        const attendeesInput = document.getElementById('attendees_count');
            // Get package row elements
            const packageRow = document.getElementById('package_row');
            const packageNameElement = document.getElementById('package_name');
            const packageCostElement = document.getElementById('package_cost');
        
            // Get venue row elements
            const venueRow = document.getElementById('venue_row');
            const venueNameElement = document.getElementById('venue_name');
            const venueRentElement = document.getElementById('venue_rent');
        
            const totalPriceElement = document.getElementById('total_price');

        let packageCost = 0;
        let venueRent = 0;

            // Update package information
        if (packageSelect && packageSelect.value) {
            const selectedOption = packageSelect.options[packageSelect.selectedIndex];
            packageCost = parseFloat(selectedOption.getAttribute('data-price')) || 0;
            
                // Show package row and update details
                if (packageRow) {
                    packageRow.style.display = 'flex';
                    packageNameElement.textContent = selectedOption.text;
                    packageCostElement.textContent = `₹${packageCost.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }
            } else if (packageRow) {
                // Hide package row if no package selected
                packageRow.style.display = 'none';
                packageNameElement.textContent = 'No package selected';
                packageCostElement.textContent = '₹0.00';
        }

            // Update venue information
        if (venueSelect && venueSelect.value) {
            const selectedOption = venueSelect.options[venueSelect.selectedIndex];
            venueRent = parseFloat(selectedOption.getAttribute('data-rent')) || 0;
            
                // Show venue row and update details
                if (venueRow) {
                    venueRow.style.display = 'flex';
                    venueNameElement.textContent = selectedOption.text;
                    venueRentElement.textContent = `₹${venueRent.toLocaleString('en-IN', {
                        minimumFractionDigits: 2,
                        maximumFractionDigits: 2
                    })}`;
                }
            } else if (venueRow) {
                // Hide venue row if no venue selected
                venueRow.style.display = 'none';
                venueNameElement.textContent = 'No venue selected';
                venueRentElement.textContent = '₹0.00';
        }

            // Calculate and update total
        const total = packageCost + venueRent;
        if (totalPriceElement) {
            totalPriceElement.textContent = `₹${total.toLocaleString('en-IN', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            })}`;
        }
    }

    // Event table updates
    if (window.location.pathname === '/events') {
        function updateEventTable(events) {
            const table = document.querySelector('table tbody');
            if (!table) return;
            
            table.innerHTML = events.map(event => `
                <tr class="fade-in">
                    <td>
                        <div class="event-name">${event.name}</div>
                        <span class="badge badge-${getStatusClass(event.status)}">${event.status}</span>
                    </td>
                    <td>
                        <div class="event-type">${event.type}</div>
                        <div class="event-date text-muted">${formatDate(event.date)}</div>
                    </td>
                    <td>
                        <div class="package-name">${event.package || 'N/A'}</div>
                        <div class="venue-name text-muted">${event.venue || 'N/A'}</div>
                    </td>
                    <td class="actions">
                        <div class="btn-group">
                            <a href="/event/${event.id}/edit" class="btn btn-outline" data-tooltip="Edit Event">
                                <i class="fas fa-edit"></i>
                            </a>
                            <a href="/event/${event.id}/vendors" class="btn btn-outline" data-tooltip="Manage Vendors">
                                <i class="fas fa-store"></i>
                            </a>
                            <a href="/event/${event.id}/guests" class="btn btn-outline" data-tooltip="Guest List">
                                <i class="fas fa-users"></i>
                            </a>
                            <a href="/event/${event.id}/payment" class="btn btn-outline" data-tooltip="Payments">
                                <i class="fas fa-credit-card"></i>
                            </a>
                            <button onclick="deleteEvent(${event.id})" class="btn btn-danger" data-tooltip="Delete Event">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

            // Reinitialize tooltips
            document.querySelectorAll('[data-tooltip]').forEach(el => {
                tippy(el, {
                    content: el.getAttribute('data-tooltip'),
                    placement: 'top',
                });
            });
        }

        function getStatusClass(status) {
            const statusClasses = {
                'Pending': 'warning',
                'Confirmed': 'success',
                'Cancelled': 'danger',
                'Completed': 'primary'
            };
            return statusClasses[status] || 'primary';
        }

        function formatDate(dateString) {
            const options = { year: 'numeric', month: 'short', day: 'numeric' };
            return new Date(dateString).toLocaleDateString('en-IN', options);
        }

        async function deleteEvent(eventId) {
            if (await confirmDialog('Are you sure you want to delete this event?')) {
                try {
                    const response = await fetch(`/event/${eventId}/delete`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    });
                    
                    if (response.ok) {
                        showNotification('Event deleted successfully', 'success');
                        pollEvents();
                    } else {
                        throw new Error('Failed to delete event');
                    }
                } catch (error) {
                    showNotification('Failed to delete event', 'error');
                }
            }
        }

        function showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type} fade-in`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.classList.add('fade-out');
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // Start polling for event updates
        const pollInterval = 5000;
        setInterval(pollEvents, pollInterval);
        pollEvents(); // Initial load
    }

    // Initialize event handlers for price calculation
    const priceInputs = document.querySelectorAll('#package_id, #venue_id, #attendees_count');
    priceInputs.forEach(input => {
        input.addEventListener('change', updateTotalPrice);
    });
    // Initial price calculation
    updateTotalPrice();

    // Initialize date pickers
    const datePickers = document.querySelectorAll('input[type="date"]');
    datePickers.forEach(input => {
        // If it's a birthday field, set max date to today
        if (input.id === 'register_birthday') {
            input.max = new Date().toISOString().split('T')[0];
        } 
        // For event dates, set min date to today
        else {
            input.min = new Date().toISOString().split('T')[0];
        }
    })
    
    // Add birthday validation to the register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const birthdayInput = document.getElementById('register_birthday');
            if (birthdayInput && birthdayInput.value) {
                const birthDate = new Date(birthdayInput.value);
                const today = new Date();
                
                if (birthDate >= today) {
                    e.preventDefault();
                    showError(birthdayInput, 'Birthday must be a date before today');
                    return false;
                }
            }
        });
    }
});