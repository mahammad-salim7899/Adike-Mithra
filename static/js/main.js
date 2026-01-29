// ADIKE MITRA - MAIN JAVASCRIPT FILE
// Interactive features and dynamic content

document.addEventListener('DOMContentLoaded', function() {
    // Mobile Navigation Toggle
    initMobileNavigation();
    
    // Flash Message Auto-Close
    initFlashMessages();
    
    // Form Validations
    initFormValidations();
    
    // Smooth Scrolling
    initSmoothScrolling();
    
    // Animation on Scroll
    initScrollAnimations();
});

// ========== MOBILE NAVIGATION ==========
function initMobileNavigation() {
    const hamburger = document.querySelector('.hamburger');
    const navLinks = document.querySelector('.nav-links');
    
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            
            // Toggle hamburger icon
            const icon = this.querySelector('i');
            if (icon.classList.contains('fa-bars')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!hamburger.contains(event.target) && !navLinks.contains(event.target)) {
                navLinks.classList.remove('active');
                const icon = hamburger.querySelector('i');
                if (icon.classList.contains('fa-times')) {
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            }
        });
    }
}

// ========== FLASH MESSAGES ==========
function initFlashMessages() {
    const closeButtons = document.querySelectorAll('.close-alert');
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const alert = this.parentElement;
            alert.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => {
                alert.remove();
            }, 300);
        });
    });
    
    // Auto-close flash messages after 5 seconds (only in flash-container)
    const flashAlerts = document.querySelectorAll('.flash-container .alert');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideUp 0.3s ease';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}

// ========== FORM VALIDATIONS ==========
function initFormValidations() {
    // Phone number validation (Indian format)
    const phoneInputs = document.querySelectorAll('input[type="text"][name="phone"]');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Remove non-digit characters
            this.value = this.value.replace(/\D/g, '');
            
            // Limit to 10 digits
            if (this.value.length > 10) {
                this.value = this.value.slice(0, 10);
            }
            
            // Visual feedback
            if (this.value.length === 10) {
                this.style.borderColor = '#4CAF50';
            } else {
                this.style.borderColor = '#E0E0E0';
            }
        });
        
        input.addEventListener('blur', function() {
            if (this.value.length > 0 && this.value.length !== 10) {
                showFieldError(this, 'Phone number must be exactly 10 digits');
            } else {
                removeFieldError(this);
            }
        });
    });
    
    // Password confirmation validation
    const passwordForm = document.querySelector('form[action*="register"]');
    if (passwordForm) {
        passwordForm.addEventListener('submit', function(e) {
            const password = this.querySelector('input[name="password"]');
            const confirmPassword = this.querySelector('input[name="confirm_password"]');
            
            if (password && confirmPassword) {
                if (password.value !== confirmPassword.value) {
                    e.preventDefault();
                    showFieldError(confirmPassword, 'Passwords do not match');
                    confirmPassword.focus();
                }
            }
        });
    }
    
    // Real-time password match checking
    const confirmPasswordInput = document.querySelector('input[name="confirm_password"]');
    const passwordInput = document.querySelector('input[name="password"]');
    
    if (confirmPasswordInput && passwordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (this.value.length > 0) {
                if (this.value === passwordInput.value) {
                    this.style.borderColor = '#4CAF50';
                    removeFieldError(this);
                } else {
                    this.style.borderColor = '#FF5722';
                }
            } else {
                this.style.borderColor = '#E0E0E0';
            }
        });
    }
}

function showFieldError(input, message) {
    removeFieldError(input);
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.color = '#FF5722';
    errorDiv.style.fontSize = '0.85rem';
    errorDiv.style.marginTop = '0.25rem';
    errorDiv.textContent = message;
    
    input.style.borderColor = '#FF5722';
    input.parentElement.appendChild(errorDiv);
}

function removeFieldError(input) {
    const existingError = input.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    if (input.value.length > 0) {
        input.style.borderColor = '#E0E0E0';
    }
}

// ========== SMOOTH SCROLLING ==========
function initSmoothScrolling() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// ========== SCROLL ANIMATIONS ==========
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animation = 'fadeInUp 0.6s ease forwards';
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe cards and sections
    const animatedElements = document.querySelectorAll(
        '.feature-card, .module-card, .stat-card, .weather-card, ' +
        '.price-card, .forecast-day, .history-card, .tip-card, ' +
        '.guideline-card, .info-card'
    );
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        observer.observe(el);
    });
}

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translateY(0);
        }
        to {
            opacity: 0;
            transform: translateY(-20px);
        }
    }
    
    @media (max-width: 768px) {
        .nav-links {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, var(--primary-green), var(--dark-green));
            flex-direction: column;
            padding: 1rem;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
        
        .nav-links.active {
            display: flex;
        }
        
        .nav-links a {
            width: 100%;
            text-align: center;
            padding: 1rem;
            border-radius: 8px;
        }
    }
`;
document.head.appendChild(style);

// ========== UTILITY FUNCTIONS ==========

// Format number as Indian currency
function formatCurrency(amount) {
    return '₹' + parseFloat(amount).toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,');
}

// Format date
function formatDate(date) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(date).toLocaleDateString('en-IN', options);
}

// Format time
function formatTime(date) {
    const options = { hour: '2-digit', minute: '2-digit' };
    return new Date(date).toLocaleTimeString('en-IN', options);
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-alert">&times;</button>
    `;
    
    const container = document.querySelector('.flash-container') || createFlashContainer();
    container.appendChild(notification);
    
    // Add close functionality
    notification.querySelector('.close-alert').addEventListener('click', function() {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function createFlashContainer() {
    const container = document.createElement('div');
    container.className = 'flash-container';
    const mainContent = document.querySelector('.main-content');
    mainContent.insertBefore(container, mainContent.firstChild);
    return container;
}

// Confirm action
function confirmAction(message) {
    return confirm(message);
}

// Loading indicator
function showLoading(element) {
    element.disabled = true;
    element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
}

function hideLoading(element, originalText) {
    element.disabled = false;
    element.innerHTML = originalText;
}

// ========== IMAGE PREVIEW ==========
function previewImage(input, previewElement) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            previewElement.innerHTML = `
                <img src="${e.target.result}" alt="Preview">
                <p>Preview of selected image</p>
            `;
            previewElement.style.display = 'block';
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// ========== TABLE SORTING ==========
function initTableSorting() {
    const tables = document.querySelectorAll('.data-table');
    
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    const isAscending = table.dataset.sortOrder !== 'asc';
    
    rows.sort((a, b) => {
        const aValue = a.children[columnIndex].textContent.trim();
        const bValue = b.children[columnIndex].textContent.trim();
        
        if (!isNaN(aValue) && !isNaN(bValue)) {
            return isAscending ? aValue - bValue : bValue - aValue;
        }
        
        return isAscending 
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });
    
    rows.forEach(row => tbody.appendChild(row));
    table.dataset.sortOrder = isAscending ? 'asc' : 'desc';
}

// ========== EXPORT FUNCTIONS ==========
// Make functions available globally
window.AdikeMitra = {
    formatCurrency,
    formatDate,
    formatTime,
    showNotification,
    confirmAction,
    showLoading,
    hideLoading,
    previewImage,
    initTableSorting
};

// Initialize table sorting if tables exist
if (document.querySelectorAll('.data-table').length > 0) {
    initTableSorting();
}

console.log('Adike Mitra - Smart Farming Assistant Loaded Successfully! 🌱');
