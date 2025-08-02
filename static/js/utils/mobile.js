// ===== MOBILE UTILITIES =====

// Mobile menu functionality
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('active');
        
        // Prevent body scroll when menu is open
        if (mobileMenu.classList.contains('active')) {
            document.body.style.overflow = 'hidden';
        } else {
            document.body.style.overflow = '';
        }
    }
}

// Close mobile menu when clicking outside
document.addEventListener('click', function(event) {
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
    
    if (mobileMenu && mobileMenu.classList.contains('active')) {
        if (!mobileMenu.contains(event.target) && !mobileMenuBtn.contains(event.target)) {
            toggleMobileMenu();
        }
    }
});

// Close mobile menu on escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const mobileMenu = document.getElementById('mobileMenu');
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            toggleMobileMenu();
        }
    }
});

// Utility function to check if device is mobile
function isMobileDevice() {
    return window.innerWidth <= 768;
}

// Utility function to check if device is tablet
function isTabletDevice() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

// Utility function to check if device is desktop
function isDesktopDevice() {
    return window.innerWidth > 1024;
}

// Responsive utilities
function handleResize() {
    const mobileMenu = document.getElementById('mobileMenu');
    
    // Auto-close mobile menu on desktop
    if (isDesktopDevice() && mobileMenu && mobileMenu.classList.contains('active')) {
        toggleMobileMenu();
    }
}

// Listen for window resize
window.addEventListener('resize', handleResize);

// Export functions for use in other modules
window.mobileUtils = {
    toggleMobileMenu,
    isMobileDevice,
    isTabletDevice,
    isDesktopDevice
}; 