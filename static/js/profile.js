// Profile Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeProfile();
});

function initializeProfile() {
    // Initialize form handling
    const form = document.getElementById('profile-form');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Initialize avatar upload
    const avatarInput = document.getElementById('avatar-input');
    if (avatarInput) {
        avatarInput.addEventListener('change', handleAvatarUpload);
    }

    // Load current avatar if exists
    loadCurrentAvatar();
}

async function loadCurrentAvatar() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        
        if (data.success && data.profile && data.profile.avatar_url) {
            updateAvatarDisplay(data.profile.avatar_url);
        }
    } catch (error) {
        console.error('Error loading avatar:', error);
    }

    // Initialize modal close buttons
    const closeButtons = document.querySelectorAll('.close');
    closeButtons.forEach(button => {
        button.addEventListener('click', closeModal);
    });

    // Close modal when clicking outside
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
    });

    // Initialize password validation
    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-password');
    
    if (newPassword && confirmPassword) {
        confirmPassword.addEventListener('input', validatePasswords);
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Validate passwords if changing
    if (formData.get('new_password') && !validatePasswords()) {
        return;
    }
    
    // Show loading state
    setFormLoading(true);
    
    try {
        const response = await fetch('/api/profile/update', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessModal('Profile updated successfully!');
            // Clear password fields
            clearPasswordFields();
            
            // Update form fields with saved data
            if (result.profile) {
                updateFormFields(result.profile);
            }
        } else {
            showErrorModal(result.error || 'Error updating profile');
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        showErrorModal('Произошла ошибка при сохранении');
    } finally {
        setFormLoading(false);
    }
}

function validatePasswords() {
    const newPassword = document.getElementById('new-password');
    const confirmPassword = document.getElementById('confirm-password');
    const currentPassword = document.getElementById('current-password');
    
    // Clear previous validation
    clearValidation(newPassword);
    clearValidation(confirmPassword);
    
    // If new password is provided, validate
    if (newPassword.value) {
        // Check if current password is provided
        if (!currentPassword.value) {
            showFieldError(currentPassword, 'Введите текущий пароль');
            return false;
        }
        
        // Check password strength
        if (newPassword.value.length < 6) {
            showFieldError(newPassword, 'Пароль должен содержать минимум 6 символов');
            return false;
        }
        
        // Check if passwords match
        if (newPassword.value !== confirmPassword.value) {
            showFieldError(confirmPassword, 'Пароли не совпадают');
            return false;
        }
        
        showFieldSuccess(newPassword);
        showFieldSuccess(confirmPassword);
    }
    
    return true;
}

function showFieldError(field, message) {
    const formGroup = field.closest('.form-group');
    formGroup.classList.add('error');
    
    // Remove existing error message
    const existingError = formGroup.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    formGroup.appendChild(errorDiv);
}

function showFieldSuccess(field) {
    const formGroup = field.closest('.form-group');
    formGroup.classList.remove('error');
    formGroup.classList.add('success');
    
    // Remove existing messages
    const existingError = formGroup.querySelector('.error-message');
    const existingSuccess = formGroup.querySelector('.success-message');
    if (existingError) existingError.remove();
    if (existingSuccess) existingSuccess.remove();
    
    // Add success message
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = '✓';
    formGroup.appendChild(successDiv);
}

function clearValidation(field) {
    const formGroup = field.closest('.form-group');
    formGroup.classList.remove('error', 'success');
    
    const existingError = formGroup.querySelector('.error-message');
    const existingSuccess = formGroup.querySelector('.success-message');
    if (existingError) existingError.remove();
    if (existingSuccess) existingSuccess.remove();
}

function setFormLoading(loading) {
    const form = document.getElementById('profile-form');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (loading) {
        form.classList.add('loading');
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Сохранение...';
        submitBtn.disabled = true;
    } else {
        form.classList.remove('loading');
        submitBtn.innerHTML = '<i class="fas fa-save"></i> Сохранить изменения';
        submitBtn.disabled = false;
    }
}

function clearPasswordFields() {
    const passwordFields = ['current-password', 'new-password', 'confirm-password'];
    passwordFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field) {
            field.value = '';
            clearValidation(field);
        }
    });
}

async function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showErrorModal('Пожалуйста, выберите изображение');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showErrorModal('Размер файла не должен превышать 5MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
        const response = await fetch('/api/profile/avatar', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateAvatarDisplay(result.avatar_url);
            showSuccessModal('Avatar uploaded successfully!');
        } else {
            showErrorModal(result.error || 'Error uploading avatar');
        }
    } catch (error) {
        console.error('Error uploading avatar:', error);
        showErrorModal('Error uploading avatar');
    }
}

function updateAvatarDisplay(avatarUrl) {
    const avatar = document.getElementById('avatar');
    if (avatarUrl) {
        avatar.innerHTML = `<img src="${avatarUrl}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
    } else {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    }
}

function resetForm() {
    if (confirm('Are you sure you want to reset all changes?')) {
        location.reload();
    }
}

async function deleteAccount() {
    if (!confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        return;
    }
    
            try {
                const response = await fetch('/api/profile/delete', {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
            alert('Account deleted. You will be redirected to the login page.');
            window.location.href = '/';
                } else {
            showErrorModal(result.error || 'Error deleting account');
                }
            } catch (error) {
                console.error('Error deleting account:', error);
        showErrorModal('Error deleting account');
    }
}

function showSuccessModal(message) {
    const modal = document.getElementById('success-modal');
    const messageElement = document.getElementById('success-message');
    
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    if (modal) {
        modal.style.display = 'block';
    }
}

function showErrorModal(message) {
    const modal = document.getElementById('error-modal');
    const messageElement = document.getElementById('error-message');
    
    if (messageElement) {
        messageElement.textContent = message;
    }
    
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    if (modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    } else {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.style.display = 'none';
        });
    }
}

// Utility functions
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Auto-save functionality
let autoSaveTimeout;
function setupAutoSave() {
    const form = document.getElementById('profile-form');
    const inputs = form.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Auto-save after 3 seconds of inactivity
                console.log('Auto-saving...');
                // You can implement auto-save logic here
            }, 3000);
        });
    });
}

// Initialize auto-save
setupAutoSave(); 

function updateFormFields(profileData) {
    // Update form fields with saved data
    const fields = {
        'full_name': profileData.full_name || '',
        'age': profileData.age || '',
        'location': profileData.location || '',
        'email': profileData.email || '',
        
        
        'bio': profileData.profile || ''  // bio field maps to profile
    };
    
    // Update each field
    Object.keys(fields).forEach(fieldName => {
        const field = document.getElementById(fieldName.replace('_', '-'));
        if (field) {
            if (field.tagName === 'SELECT') {
                // For select elements, find and select the correct option
                const value = fields[fieldName];
                for (let option of field.options) {
                    if (option.value === value) {
                        option.selected = true;
                        break;
                    }
                }
            } else {
                field.value = fields[fieldName];
            }
        }
    });
    
    // Update checkboxes
    const checkboxes = {
        
        'show_feelings': profileData.show_feelings,
        
    };
    
    Object.keys(checkboxes).forEach(checkboxName => {
        const checkbox = document.getElementById(checkboxName.replace('_', '-'));
        if (checkbox) {
            checkbox.checked = checkboxes[checkboxName] || false;
        }
    });
} 