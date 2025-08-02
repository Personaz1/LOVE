// ===== THEME UTILITIES - ΔΣ Guardian =====

// Theme management
const ThemeManager = {
  // Get current theme
  getCurrentTheme() {
    return localStorage.getItem('theme') || 'light';
  },

  // Set theme
  setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    
    // Update theme toggle button
    this.updateThemeToggle(theme);
  },

  // Toggle theme
  toggleTheme() {
    const currentTheme = this.getCurrentTheme();
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  },

  // Update theme toggle button
  updateThemeToggle(theme) {
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.innerHTML = theme === 'light' ? '🌙' : '☀️';
      toggleBtn.title = theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode';
    }
  },

  // Initialize theme
  init() {
    const savedTheme = this.getCurrentTheme();
    this.setTheme(savedTheme);
    
    // Add theme toggle button to header
    this.addThemeToggle();
  },

  // Add theme toggle button
  addThemeToggle() {
    const headerActions = document.querySelector('.header-actions');
    if (headerActions && !document.getElementById('themeToggle')) {
      const themeToggle = document.createElement('button');
      themeToggle.id = 'themeToggle';
      themeToggle.className = 'btn btn-ghost btn-sm';
      themeToggle.onclick = () => this.toggleTheme();
      themeToggle.title = 'Toggle Theme';
      
      // Insert before logout button
      const logoutForm = headerActions.querySelector('form');
      if (logoutForm) {
        headerActions.insertBefore(themeToggle, logoutForm);
      } else {
        headerActions.appendChild(themeToggle);
      }
      
      this.updateThemeToggle(this.getCurrentTheme());
    }
  }
};

// Initialize theme on DOM load
document.addEventListener('DOMContentLoaded', function() {
  ThemeManager.init();
});

// Export for use in other modules
window.ThemeManager = ThemeManager; 