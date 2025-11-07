// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const loginForm = document.getElementById('login-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const loginButton = document.getElementById('login-button');
const errorMessage = document.getElementById('error-message');
const registerLink = document.getElementById('register-link');

// Check if user is already logged in
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        // User already has a token, redirect to inbox
        window.location.href = 'inbox.html';
    }
});

// Handle login form submission
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    
    // Validate inputs
    if (!email || !password) {
        showError('Please enter both email and password');
        return;
    }
    
    // Disable form during login
    setLoading(true);
    hideError();
    
    try {
        await login(email, password);
    } catch (error) {
        showError(error.message || 'Login failed. Please try again.');
        setLoading(false);
    }
});

// Handle register link click
registerLink.addEventListener('click', (e) => {
    e.preventDefault();
    window.location.href = 'register.html';
});

/**
 * Login function - calls the backend API
 * @param {string} email - User's email address
 * @param {string} password - User's app password
 */
async function login(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('Server error: Unable to parse response');
        }
        
        if (!response.ok) {
            // Handle error response - extract message from various possible formats
            let errorMessage = 'Invalid credentials';
            
            if (typeof data === 'string') {
                errorMessage = data;
            } else if (data.detail) {
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    errorMessage = data.detail.map(err => err.msg).join(', ');
                } else if (typeof data.detail === 'object') {
                    errorMessage = JSON.stringify(data.detail);
                }
            } else if (data.message) {
                errorMessage = data.message;
            } else if (data.error) {
                errorMessage = data.error;
            }
            
            throw new Error(errorMessage);
        }
        
        // Store JWT token in localStorage
        if (data.access_token) {
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user_email', email);
            
            // Show success message briefly
            showSuccess('Login successful! Redirecting...');
            
            // Redirect to inbox after short delay
            setTimeout(() => {
                window.location.href = 'inbox.html';
            }, 500);
        } else {
            throw new Error('No access token received');
        }
        
    } catch (error) {
        // Re-throw with proper error message
        if (error.message) {
            throw error;
        } else {
            throw new Error('Login failed: ' + String(error));
        }
    }
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('d-none');
    errorMessage.classList.add('alert-danger');
    errorMessage.classList.remove('alert-success');
}

/**
 * Show success message
 * @param {string} message - Success message to display
 */
function showSuccess(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('d-none');
    errorMessage.classList.add('alert-success');
    errorMessage.classList.remove('alert-danger');
}

/**
 * Hide error/success message
 */
function hideError() {
    errorMessage.classList.add('d-none');
}

/**
 * Set loading state for the form
 * @param {boolean} loading - Whether the form is in loading state
 */
function setLoading(loading) {
    loginButton.disabled = loading;
    emailInput.disabled = loading;
    passwordInput.disabled = loading;
    
    if (loading) {
        loginButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Signing in...';
    } else {
        loginButton.innerHTML = 'Sign In';
    }
}
