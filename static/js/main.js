// The Kitchen - Main JavaScript File

// Global variables
let currentLanguage = localStorage.getItem('language') || 'en';
let cartItems = [];
let currentUser = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    setLanguage(currentLanguage);
    loadCurrentUser();
    updateCartCount();
    initializeEventListeners();
}

// Language management
function setLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem('language', lang);
    
    const isArabic = lang === 'ar';
    
    // Update HTML attributes
    document.documentElement.lang = lang;
    document.documentElement.dir = isArabic ? 'rtl' : 'ltr';
    
    // Show/hide language-specific elements
    document.querySelectorAll('.en, .nav-en, .cart-en, .auth-en, .footer-en, .dropdown-en, .brand-en, .hero-en, .feature-en, .popular-en, .how-en, .step-en, .add-en, .filter-en, .empty-en, .summary-en, .info-en, .modal-en, .signup-en, .signin-en').forEach(el => {
        el.style.display = isArabic ? 'none' : '';
    });
    
    document.querySelectorAll('.ar, .nav-ar, .cart-ar, .auth-ar, .footer-ar, .dropdown-ar, .brand-ar, .hero-ar, .feature-ar, .popular-ar, .how-ar, .step-ar, .add-ar, .filter-ar, .empty-ar, .summary-ar, .info-ar, .modal-ar, .signup-ar, .signin-ar').forEach(el => {
        el.style.display = isArabic ? '' : 'none';
    });
    
    // Update language switcher
    const langEn = document.querySelector('.lang-en');
    const langAr = document.querySelector('.lang-ar');
    if (langEn) langEn.style.display = isArabic ? 'none' : '';
    if (langAr) langAr.style.display = isArabic ? '' : 'none';
}

// Load current user
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/auth/me');
        const data = await response.json();
        
        if (data.ok) {
            currentUser = data.user;
            updateUIForLoggedInUser();
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

// Update UI for logged in user
function updateUIForLoggedInUser() {
    if (!currentUser) return;
    
    // Update user name in navbar
    const userNameElement = document.querySelector('.user-name');
    if (userNameElement) {
        userNameElement.textContent = currentUser.name;
    }
    
    // Show/hide auth elements
    const authElements = document.querySelectorAll('.auth-only');
    authElements.forEach(el => el.style.display = 'block');
    
    const guestElements = document.querySelectorAll('.guest-only');
    guestElements.forEach(el => el.style.display = 'none');
}

// Update cart count
async function updateCartCount() {
    try {
        const response = await fetch('/api/cart');
        const data = await response.json();
        
        if (data.ok) {
            const cartCount = document.querySelector('.cart-count');
            if (cartCount) {
                cartCount.textContent = data.total_items;
            }
        }
    } catch (error) {
        console.error('Error updating cart count:', error);
    }
}

// Initialize event listeners
function initializeEventListeners() {
    // Language switcher
    const languageLinks = document.querySelectorAll('a[href*="set-language"]');
    languageLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const lang = this.getAttribute('href').split('/').pop();
            setLanguage(lang);
            
            // Update session language
            fetch(`/set-language/${lang}`);
        });
    });
    
    // Form validations
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        });
    });
    
    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            
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

// Utility functions
function showToast(message, type = 'info', duration = 3000) {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => toast.remove());
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    // Add to container or create one
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(toast);
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();
    
    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function formatPrice(price) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'EGP',
        minimumFractionDigits: 0
    }).format(price);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    if (currentLanguage === 'ar') {
        return date.toLocaleDateString('ar-EG', options);
    }
    
    return date.toLocaleDateString('en-US', options);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API helper functions
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Loading states
function showLoading(element, text = 'Loading...') {
    const originalContent = element.innerHTML;
    element.dataset.originalContent = originalContent;
    element.innerHTML = `<span class="loading-spinner me-2"></span>${text}`;
    element.disabled = true;
}

function hideLoading(element) {
    const originalContent = element.dataset.originalContent;
    if (originalContent) {
        element.innerHTML = originalContent;
        element.disabled = false;
        delete element.dataset.originalContent;
    }
}

// Form helpers
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^01[0-2]\d{8}$/;
    return re.test(phone);
}

function validatePassword(password) {
    // At least 8 characters, mixed case, and numbers
    const re = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    return re.test(password);
}

// Image handling
function handleImageUpload(input, callback) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            callback(e.target.result);
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Local storage helpers
function setLocalStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Error setting localStorage:', error);
    }
}

function getLocalStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Error getting localStorage:', error);
        return defaultValue;
    }
}

function removeLocalStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('Error removing localStorage:', error);
    }
}

// Export functions for use in other files
window.TheKitchen = {
    setLanguage,
    showToast,
    formatPrice,
    formatDate,
    apiRequest,
    showLoading,
    hideLoading,
    validateEmail,
    validatePhone,
    validatePassword,
    handleImageUpload,
    setLocalStorage,
    getLocalStorage,
    removeLocalStorage,
    currentLanguage,
    currentUser
};
