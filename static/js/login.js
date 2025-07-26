// Login page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login-form');
    const loginBtn = document.querySelector('.login-btn');
    const inputs = document.querySelectorAll('input');

    // Add focus effects to inputs
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.style.transform = 'scale(1.02)';
        });

        input.addEventListener('blur', function() {
            this.parentElement.style.transform = 'scale(1)';
        });
    });

    // Form submission with loading state
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            showError('Please fill in all fields');
            return;
        }

        // Add loading state
        loginBtn.classList.add('loading');
        loginBtn.querySelector('.btn-text').textContent = 'Entering...';
        
        // Map old credentials to new ones
        let authUsername = username;
        let authPassword = password;
        
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }
        
        // Simulate authentication (in real app, this would be handled by the server)
        setTimeout(() => {
            // Redirect to chat page with correct credentials
            window.location.href = `/chat?username=${encodeURIComponent(authUsername)}&password=${encodeURIComponent(authPassword)}`;
        }, 1000);
    });

    // Error display function
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        errorDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ff4757;
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            errorDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => {
                document.body.removeChild(errorDiv);
            }, 300);
        }, 3000);
    }

    // Add CSS animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);

    // Add floating hearts effect
    createFloatingHearts();
});

// Create additional floating hearts
function createFloatingHearts() {
    const container = document.querySelector('.container');
    
    setInterval(() => {
        const heart = document.createElement('div');
        heart.className = 'floating-heart';
        heart.innerHTML = '💕';
        heart.style.cssText = `
            position: fixed;
            left: ${Math.random() * 100}%;
            bottom: -50px;
            font-size: ${Math.random() * 20 + 15}px;
            opacity: 0.7;
            pointer-events: none;
            z-index: 2;
            animation: floatUp 8s linear forwards;
        `;
        
        container.appendChild(heart);
        
        setTimeout(() => {
            if (heart.parentNode) {
                heart.parentNode.removeChild(heart);
            }
        }, 8000);
    }, 2000);
}

// Add CSS for floating hearts
const floatingHeartStyle = document.createElement('style');
floatingHeartStyle.textContent = `
    @keyframes floatUp {
        0% {
            transform: translateY(0) rotate(0deg);
            opacity: 0.7;
        }
        100% {
            transform: translateY(-100vh) rotate(360deg);
            opacity: 0;
        }
    }
`;
document.head.appendChild(floatingHeartStyle);

// Add keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Enter key to submit form
    if (e.key === 'Enter' && document.activeElement.tagName === 'INPUT') {
        const form = document.querySelector('.login-form');
        if (form) {
            form.dispatchEvent(new Event('submit'));
        }
    }
    
    // Escape key to clear form
    if (e.key === 'Escape') {
        const inputs = document.querySelectorAll('input');
        inputs.forEach(input => input.value = '');
    }
});

// Add input validation
document.addEventListener('input', function(e) {
    if (e.target.type === 'text' || e.target.type === 'password') {
        const input = e.target;
        const value = input.value.trim();
        
        // Add visual feedback
        if (value.length > 0) {
            input.style.borderColor = '#ff1493';
            input.style.boxShadow = '0 0 0 3px rgba(255, 20, 147, 0.1)';
        } else {
            input.style.borderColor = '#f0f0f0';
            input.style.boxShadow = 'none';
        }
    }
});

// Add welcome animation
window.addEventListener('load', function() {
    const loginCard = document.querySelector('.login-card');
    if (loginCard) {
        loginCard.style.animation = 'slideIn 0.8s ease-out';
    }
    
    // Add typing effect to subtitle
    const subtitle = document.querySelector('.subtitle');
    if (subtitle) {
        const text = subtitle.textContent;
        subtitle.textContent = '';
        subtitle.style.borderRight = '2px solid #ff1493';
        
        let i = 0;
        const typeWriter = () => {
            if (i < text.length) {
                subtitle.textContent += text.charAt(i);
                i++;
                setTimeout(typeWriter, 50);
            } else {
                subtitle.style.borderRight = 'none';
            }
        };
        
        setTimeout(typeWriter, 1000);
    }
}); 