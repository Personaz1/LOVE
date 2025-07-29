// Mobile-specific JavaScript for ΔΣ Guardian
// Touch interactions, swipe gestures, mobile navigation

document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on mobile
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        initializeMobileFeatures();
    }
});

function initializeMobileFeatures() {
    console.log('📱 Initializing mobile features...');
    
    // Initialize mobile navigation
    initializeMobileNavigation();
    
    // Initialize touch gestures
    initializeTouchGestures();
    
    // Initialize pull to refresh
    initializePullToRefresh();
    
    // Initialize keyboard handling
    initializeKeyboardHandling();
    
    // Initialize swipe actions for messages
    initializeSwipeActions();
    
    // Initialize floating action button
    initializeFAB();
    
    // Initialize mobile-specific event listeners
    initializeMobileEventListeners();
}

// Mobile Navigation
function initializeMobileNavigation() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.mobile-nav-item');
    
    // Set active state based on current page
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href.split('?')[0])) {
            item.classList.add('active');
        }
    });
    
    // Adjust chat container for bottom nav if exists
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.style.paddingBottom = '80px';
    }
}

// Touch Gestures
function initializeTouchGestures() {
    let startX = 0;
    let startY = 0;
    let currentX = 0;
    let currentY = 0;
    
    // Touch start
    document.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
    }, { passive: true });
    
    // Touch move
    document.addEventListener('touchmove', function(e) {
        currentX = e.touches[0].clientX;
        currentY = e.touches[0].clientY;
        
        // Prevent default on horizontal swipes
        const deltaX = Math.abs(currentX - startX);
        const deltaY = Math.abs(currentY - startY);
        
        if (deltaX > deltaY && deltaX > 10) {
            e.preventDefault();
        }
    }, { passive: false });
    
    // Touch end
    document.addEventListener('touchend', function(e) {
        const deltaX = currentX - startX;
        const deltaY = currentY - startY;
        const minSwipeDistance = 50;
        
        if (Math.abs(deltaX) > minSwipeDistance && Math.abs(deltaX) > Math.abs(deltaY)) {
            handleSwipeGesture(deltaX, deltaY);
        }
    }, { passive: true });
}

function handleSwipeGesture(deltaX, deltaY) {
    // Handle horizontal swipes
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX > 0) {
            // Swipe right - could be used for navigation
            console.log('Swipe right detected');
        } else {
            // Swipe left - could be used for navigation
            console.log('Swipe left detected');
        }
    }
}

// Pull to Refresh
function initializePullToRefresh() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    let pullDistance = 0;
    
    // Add pull to refresh indicator
    const pullIndicator = document.createElement('div');
    pullIndicator.className = 'pull-to-refresh';
    pullIndicator.innerHTML = 'Pull to refresh';
    messagesContainer.insertBefore(pullIndicator, messagesContainer.firstChild);
    
    messagesContainer.addEventListener('touchstart', function(e) {
        if (messagesContainer.scrollTop === 0) {
            startY = e.touches[0].clientY;
            isPulling = true;
        }
    }, { passive: true });
    
    messagesContainer.addEventListener('touchmove', function(e) {
        if (!isPulling) return;
        
        currentY = e.touches[0].clientY;
        pullDistance = currentY - startY;
        
        if (pullDistance > 0 && messagesContainer.scrollTop === 0) {
            e.preventDefault();
            pullIndicator.style.transform = `translateY(${Math.min(pullDistance * 0.5, 60)}px)`;
            
            if (pullDistance > 100) {
                pullIndicator.textContent = 'Release to refresh';
                pullIndicator.classList.add('ready');
            } else {
                pullIndicator.textContent = 'Pull to refresh';
                pullIndicator.classList.remove('ready');
            }
        }
    }, { passive: false });
    
    messagesContainer.addEventListener('touchend', function(e) {
        if (!isPulling) return;
        
        if (pullDistance > 100) {
            // Trigger refresh
            pullIndicator.textContent = 'Refreshing...';
            pullIndicator.classList.add('loading');
            
            // Reload conversation history
            loadConversationHistory().then(() => {
                setTimeout(() => {
                    pullIndicator.textContent = 'Pull to refresh';
                    pullIndicator.classList.remove('loading', 'ready');
                    pullIndicator.style.transform = '';
                }, 1000);
            });
        } else {
            // Reset indicator
            pullIndicator.textContent = 'Pull to refresh';
            pullIndicator.classList.remove('ready');
            pullIndicator.style.transform = '';
        }
        
        isPulling = false;
        pullDistance = 0;
    }, { passive: true });
}

// Keyboard Handling
function initializeKeyboardHandling() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    // Handle keyboard show/hide
    let initialViewportHeight = window.innerHeight;
    
    window.addEventListener('resize', function() {
        const currentHeight = window.innerHeight;
        const heightDifference = initialViewportHeight - currentHeight;
        
        if (heightDifference > 150) {
            // Keyboard is likely open
            document.body.classList.add('keyboard-open');
        } else {
            // Keyboard is likely closed
            document.body.classList.remove('keyboard-open');
        }
    });
    
    // Focus handling for mobile
    messageInput.addEventListener('focus', function() {
        // Scroll to input when focused
        setTimeout(() => {
            messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
    });
}

// Swipe Actions for Messages
function initializeSwipeActions() {
    const messages = document.querySelectorAll('.message');
    
    messages.forEach(message => {
        if (message.classList.contains('user-message')) {
            addSwipeActions(message);
        }
    });
}

function addSwipeActions(message) {
    let startX = 0;
    let currentX = 0;
    let isSwiping = false;
    
    // Add swipe actions container
    const swipeActions = document.createElement('div');
    swipeActions.className = 'message-swipe-actions';
    swipeActions.innerHTML = `
        <button class="swipe-action-btn edit" onclick="editMessage('${message.getAttribute('data-message-id') || ''}')">
            ✏️ Edit
        </button>
        <button class="swipe-action-btn delete" onclick="deleteMessage('${message.getAttribute('data-message-id') || ''}')">
            🗑️ Delete
        </button>
    `;
    message.appendChild(swipeActions);
    
    message.addEventListener('touchstart', function(e) {
        startX = e.touches[0].clientX;
        isSwiping = true;
    }, { passive: true });
    
    message.addEventListener('touchmove', function(e) {
        if (!isSwiping) return;
        
        currentX = e.touches[0].clientX;
        const deltaX = currentX - startX;
        
        if (deltaX < 0) {
            e.preventDefault();
            const translateX = Math.max(deltaX, -120);
            swipeActions.style.transform = `translateX(${translateX}px)`;
        }
    }, { passive: false });
    
    message.addEventListener('touchend', function(e) {
        if (!isSwiping) return;
        
        const deltaX = currentX - startX;
        
        if (deltaX < -60) {
            // Show swipe actions
            message.classList.add('swiped');
            swipeActions.style.transform = 'translateX(-120px)';
        } else {
            // Hide swipe actions
            message.classList.remove('swiped');
            swipeActions.style.transform = 'translateX(0)';
        }
        
        isSwiping = false;
    }, { passive: true });
}

// Floating Action Button
function initializeFAB() {
    const fabHtml = `
        <button class="fab" onclick="showQuickActions()" title="Quick Actions">
            +
        </button>
    `;
    
    document.body.insertAdjacentHTML('beforeend', fabHtml);
}

function showQuickActions() {
    const actions = [
        { icon: '📷', label: 'Camera', action: () => document.getElementById('fileInput').click() },
        { icon: '📁', label: 'Files', action: () => document.getElementById('fileInput').click() },
        { icon: '🗑️', label: 'Clear', action: () => clearConversationHistory() },
        { icon: '📤', label: 'Export', action: () => exportChat() }
    ];
    
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'block';
    
    let modalContent = '<div class="modal-content">';
    modalContent += '<div class="modal-header"><h2>Quick Actions</h2><span class="close" onclick="this.closest(\'.modal\').remove()">&times;</span></div>';
    modalContent += '<div class="modal-body">';
    
    actions.forEach(action => {
        modalContent += `
            <button class="quick-action-btn" onclick="this.closest('.modal').remove(); (${action.action.toString()})()">
                <span class="quick-action-icon">${action.icon}</span>
                <span class="quick-action-label">${action.label}</span>
            </button>
        `;
    });
    
    modalContent += '</div></div>';
    modal.innerHTML = modalContent;
    
    document.body.appendChild(modal);
    
    // Add styles for quick action buttons
    const style = document.createElement('style');
    style.textContent = `
        .quick-action-btn {
            display: flex;
            align-items: center;
            gap: 15px;
            width: 100%;
            padding: 15px;
            border: none;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 8px;
            margin-bottom: 10px;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .quick-action-btn:hover {
            background: rgba(102, 126, 234, 0.1);
        }
        
        .quick-action-icon {
            font-size: 1.5rem;
        }
        
        .quick-action-label {
            font-weight: 500;
        }
    `;
    document.head.appendChild(style);
}

// Mobile Event Listeners
function initializeMobileEventListeners() {
    // Handle orientation change
    window.addEventListener('orientationchange', function() {
        setTimeout(() => {
            // Adjust layout after orientation change
            if (window.innerWidth <= 768) {
                // Reinitialize mobile features
                initializeMobileFeatures();
            }
        }, 100);
    });
    
    // Handle viewport changes
    window.addEventListener('resize', function() {
        if (window.innerWidth <= 768 && !document.querySelector('.mobile-nav')) {
            // Switch to mobile mode
            initializeMobileFeatures();
        } else if (window.innerWidth > 768 && document.querySelector('.mobile-nav')) {
            // Switch to desktop mode
            document.querySelector('.mobile-nav')?.remove();
            document.querySelector('.fab')?.remove();
        }
    });
    
    // Prevent zoom on double tap
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function(event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
}

// Mobile-specific utility functions
function showMobileToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `mobile-toast ${type}`;
    toast.textContent = message;
    
    // Add mobile toast styles
    const style = document.createElement('style');
    style.textContent = `
        .mobile-toast {
            position: fixed;
            bottom: 100px;
            left: 20px;
            right: 20px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 12px 16px;
            border-radius: 8px;
            text-align: center;
            z-index: 2000;
            font-size: 0.9rem;
            animation: slideUp 0.3s ease;
        }
        
        @keyframes slideUp {
            from { transform: translateY(100%); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        
        .mobile-toast.success {
            background: rgba(76, 175, 80, 0.9);
        }
        
        .mobile-toast.error {
            background: rgba(244, 67, 54, 0.9);
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Override existing functions for mobile
const originalShowStatusMessage = window.showStatusMessage;
window.showStatusMessage = function(message, type = 'info') {
    if (window.innerWidth <= 768) {
        showMobileToast(message, type);
    } else {
        originalShowStatusMessage(message, type);
    }
};

// Mobile-specific message functions
function addMobileMessageActions(messageElement) {
    if (window.innerWidth <= 768) {
        // Add touch-friendly action buttons
        const actions = messageElement.querySelector('.message-actions');
        if (actions) {
            actions.style.display = 'flex';
            actions.style.gap = '10px';
            
            const buttons = actions.querySelectorAll('.message-action-btn');
            buttons.forEach(btn => {
                btn.style.minWidth = '44px';
                btn.style.minHeight = '44px';
                btn.style.padding = '8px';
            });
        }
    }
}

// Export mobile functions for global use
window.mobileUtils = {
    showToast: showMobileToast,
    addMessageActions: addMobileMessageActions,
    initializeFeatures: initializeMobileFeatures
}; 