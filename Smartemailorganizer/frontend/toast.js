// Toast notification utility
function showToast(message, type = 'info', duration = 4000) {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    // Determine icon and title based on type
    let icon = '';
    let title = '';
    
    switch (type) {
        case 'success':
            icon = '✓';
            title = 'Success';
            break;
        case 'error':
            icon = '✕';
            title = 'Error';
            break;
        case 'info':
            icon = 'ℹ';
            title = 'Info';
            break;
        default:
            icon = 'ℹ';
            title = 'Notification';
    }

    // Build toast HTML
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${icon} ${title}</strong>
            <button type="button" class="btn-close btn-close-sm" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${escapeHtml(message)}
        </div>
    `;

    // Add close button functionality
    const closeBtn = toast.querySelector('.btn-close');
    closeBtn.addEventListener('click', () => {
        removeToast(toast);
    });

    // Add toast to container
    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);

    // Auto-remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);
}

function removeToast(toast) {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Add initial styles for toast animations
const style = document.createElement('style');
style.textContent = `
    .toast {
        opacity: 0;
        transform: translateX(100%);
        transition: opacity 0.3s ease, transform 0.3s ease;
    }
`;
document.head.appendChild(style);
