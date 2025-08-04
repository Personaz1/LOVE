// Guardian Profile JavaScript
document.addEventListener('DOMContentLoaded', function() {
    initializeGuardianProfile();
});

function initializeGuardianProfile() {
    // Initialize form handling
    const form = document.getElementById('guardianForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }

    // Initialize avatar upload
    const avatarInput = document.getElementById('guardianAvatarInput');
    if (avatarInput) {
        avatarInput.addEventListener('change', handleAvatarUpload);
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
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    
    // Show loading state
    setFormLoading(true);
    
    try {
        const response = await fetch('/api/guardian/profile/update', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccessModal('Guardian profile updated successfully!');
        } else {
            showErrorModal(result.error || 'Error updating guardian profile');
        }
    } catch (error) {
        console.error('Error updating guardian profile:', error);
        showErrorModal('An error occurred while saving changes');
    } finally {
        setFormLoading(false);
    }
}

async function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
        showErrorModal('Please select an image file');
        return;
    }
    
    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
        showErrorModal('Image file size must be less than 5MB');
        return;
    }
    
    const formData = new FormData();
    formData.append('avatar', file);
    
    try {
        const response = await fetch('/api/guardian/avatar', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateGuardianAvatar(result.avatar_url);
            showSuccessModal('Guardian avatar updated successfully!');
        } else {
            showErrorModal(result.error || 'Error uploading avatar');
        }
    } catch (error) {
        console.error('Error uploading avatar:', error);
        showErrorModal('An error occurred while uploading avatar');
    }
}

function updateGuardianAvatar(avatarUrl) {
    const avatar = document.getElementById('guardianAvatar');
    if (avatarUrl) {
        avatar.innerHTML = `<img src="${avatarUrl}" alt="Guardian Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
    } else {
        avatar.innerHTML = '<i class="fas fa-user"></i>';
    }
}

async function resetGuardianProfile() {
    if (!confirm('Are you sure you want to reset the Guardian profile to defaults?')) {
        return;
    }
    
    try {
        setLoading(true);
        const response = await fetch('/api/guardian/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('Guardian profile reset successfully!');
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Failed to reset profile'));
            }
        } else {
            alert('Error: Failed to reset profile');
        }
    } catch (error) {
        console.error('Error resetting profile:', error);
        alert('Error: Failed to reset profile');
    } finally {
        setLoading(false);
    }
}

async function updatePromptFromFile() {
    if (!confirm('Update the system prompt from the prompts file? This will overwrite the current prompt.')) {
        return;
    }
    
    try {
        setLoading(true);
        const response = await fetch('/api/guardian/update-prompt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                alert('Guardian prompt updated from file successfully!');
                location.reload();
            } else {
                alert('Error: ' + (data.error || 'Failed to update prompt'));
            }
        } else {
            alert('Error: Failed to update prompt');
        }
    } catch (error) {
        console.error('Error updating prompt:', error);
        alert('Error: Failed to update prompt');
    } finally {
        setLoading(false);
    }
}

function previewPrompt() {
    const promptText = document.getElementById('systemPrompt').value;
    const previewDiv = document.getElementById('promptPreview');
    
    if (promptText.trim()) {
        previewDiv.textContent = promptText;
        document.getElementById('preview-modal').style.display = 'block';
    } else {
        showErrorModal('Please enter a system prompt to preview');
    }
}

function setFormLoading(loading) {
    const saveBtn = document.querySelector('.save-btn');
    const resetBtn = document.querySelector('.reset-btn');
    const previewBtn = document.querySelector('.preview-btn');
    
    if (loading) {
        saveBtn.textContent = '💾 Saving...';
        saveBtn.disabled = true;
        resetBtn.disabled = true;
        previewBtn.disabled = true;
    } else {
        saveBtn.textContent = '💾 Save Changes';
        saveBtn.disabled = false;
        resetBtn.disabled = false;
        previewBtn.disabled = false;
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

// Auto-save functionality for system prompt
let autoSaveTimeout;
function setupAutoSave() {
    const systemPrompt = document.getElementById('systemPrompt');
    if (systemPrompt) {
        systemPrompt.addEventListener('input', () => {
            clearTimeout(autoSaveTimeout);
            autoSaveTimeout = setTimeout(() => {
                // Optional: Auto-save system prompt changes
                console.log('System prompt changed - consider auto-saving');
            }, 2000);
        });
    }
}

// Initialize auto-save
setupAutoSave(); 

// Функция для сохранения промпта
async function savePrompt() {
    const prompt = document.getElementById('systemPrompt').value;
    await fetch('/api/guardian/profile/update', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({system_prompt: prompt})
    });
} 