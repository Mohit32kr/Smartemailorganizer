// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// DOM Elements
const registerForm = document.getElementById('register-form');
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const confirmPasswordInput = document.getElementById('confirm-password');
const registerButton = document.getElementById('register-button');
const messageDiv = document.getElementById('message');

// Check if user is already logged in
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        // User already has a token, redirect to inbox
        window.location.href = 'inbox.html';
    }
});

// Handle registration form submission
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;
    
    // Validate inputs
    if (!email || !password || !confirmPassword) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    // Check if passwords match
    if (password !== confirmPassword) {
        showMessage('Passwords do not match', 'error');
        return;
    }
    
    // Validate password length (Gmail app passwords are 16 characters)
    if (password.length < 8) {
        showMessage('Password must be at least 8 characters long', 'error');
        return;
    }
    
    // Disable form during registration
    setLoading(true);
    hideMessage();
    
    try {
        await register(email, password);
    } catch (error) {
        showMessage(error.message || 'Registration failed. Please try again.', 'error');
        setLoading(false);
    }
});

/**
 * Register function - calls the backend API
 * @param {string} email - User's email address
 * @param {string} password - User's password
 */
async function register(email, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
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
            let errorMessage = 'Registration failed';
            
            if (typeof data === 'string') {
                errorMessage = data;
            } else if (data.detail) {
                // FastAPI validation errors
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    // Pydantic validation errors
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
            
            // Show success message
            showMessage('Account created successfully! Redirecting...', 'success');
            
            // Redirect to inbox after short delay
            setTimeout(() => {
                window.location.href = 'inbox.html';
            }, 1500);
        } else {
            throw new Error('No access token received');
        }
        
    } catch (error) {
        // Re-throw with proper error message
        if (error.message) {
            throw error;
        } else {
            throw new Error('Registration failed: ' + String(error));
        }
    }
}

/**
 * Show message
 * @param {string} message - Message to display
 * @param {string} type - Message type ('success' or 'error')
 */
function showMessage(message, type) {
    messageDiv.textContent = message;
    messageDiv.classList.remove('d-none');
    
    if (type === 'success') {
        messageDiv.classList.add('alert-success');
        messageDiv.classList.remove('alert-danger');
    } else {
        messageDiv.classList.add('alert-danger');
        messageDiv.classList.remove('alert-success');
    }
}

/**
 * Hide message
 */
function hideMessage() {
    messageDiv.classList.add('d-none');
}

/**
 * Set loading state for the form
 * @param {boolean} loading - Whether the form is in loading state
 */
function setLoading(loading) {
    registerButton.disabled = loading;
    emailInput.disabled = loading;
    passwordInput.disabled = loading;
    confirmPasswordInput.disabled = loading;
    
    if (loading) {
        registerButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Creating account...';
    } else {
        registerButton.innerHTML = 'Create Account';
    }
}
