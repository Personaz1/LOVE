// Chat functionality JavaScript
let currentUser = '{{ username }}';
// Map old username to new one
if (currentUser === 'musser') {
    currentUser = 'meranda';
}
let messageHistory = [];

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const messagesContainer = document.getElementById('messagesContainer');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Focus on input when page loads
    messageInput.focus();

    // Handle message submission
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        messageInput.value = '';

        // Show loading
        showLoading();

        try {
            // Send message to API
            const response = await sendMessage(message);
            
            if (response.error) {
                addMessage('Sorry, I encountered an error. Please try again.', 'ai');
            } else {
                addMessage(response.response, 'ai');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
        } finally {
            hideLoading();
        }
    });

    // Handle Enter key (send message)
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            messageForm.dispatchEvent(new Event('submit'));
        }
    });

    // Auto-resize textarea (if we add one later)
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
});

// Send message to API
async function sendMessage(message) {
    const formData = new FormData();
    formData.append('message', message);

    // Get current credentials from URL or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const username = urlParams.get('username') || currentUser;
    const password = urlParams.get('password') || '';

    // Use the correct credentials based on username
    let authUsername = username;
    let authPassword = password;
    
    // Map old credentials to new ones
    if (username === 'musser') {
        authUsername = 'meranda';
        authPassword = 'musser';
    }

    const response = await fetch('/api/chat', {
        method: 'POST',
        body: formData,
        headers: {
            'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
        }
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
}

// Add message to chat
function addMessage(text, sender) {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const time = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });

    const avatar = sender === 'user' ? '👤' : '💕';
    const senderName = sender === 'user' ? currentUser.charAt(0).toUpperCase() + currentUser.slice(1) : 'Dr. Harmony';

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender">${senderName}</span>
                <span class="time">${time}</span>
            </div>
            <div class="message-text">${formatMessage(text)}</div>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    // Add to history
    messageHistory.push({
        text: text,
        sender: sender,
        timestamp: new Date().toISOString()
    });
}

// Format message text (convert URLs to links, etc.)
function formatMessage(text) {
    // Convert URLs to links
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: inherit; text-decoration: underline;">$1</a>');
    
    // Convert line breaks to <br>
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

// Scroll to bottom of messages
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Show loading overlay
function showLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'flex';
}

// Hide loading overlay
function hideLoading() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    loadingOverlay.style.display = 'none';
}

// Quick message functions
function sendQuickMessage(message) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = message;
    document.getElementById('messageForm').dispatchEvent(new Event('submit'));
}

// Modal functions
function showProfile() {
    const modal = document.getElementById('profileModal');
    const content = document.getElementById('profileContent');
    
    // Load profile data
    loadProfileData().then(profile => {
        if (profile.error) {
            content.innerHTML = '<p>Error loading profile data.</p>';
        } else {
            content.innerHTML = `
                <div class="profile-details">
                    <h3>${profile.username}</h3>
                    <div class="profile-section">
                        <h4>Your Profile</h4>
                        <textarea id="profileText" class="profile-textarea">${profile.profile}</textarea>
                        <button onclick="updateProfile()" class="update-btn">💾 Update Profile</button>
                    </div>
                    <div class="profile-section">
                        <h4>Relationship Status</h4>
                        <p>${profile.relationship_status}</p>
                    </div>
                    <div class="profile-section">
                        <h4>Current Feeling</h4>
                        <p>${profile.current_feeling}</p>
                    </div>
                    <div class="profile-section">
                        <h4>Last Updated</h4>
                        <p>${profile.last_updated}</p>
                    </div>
                    <div class="profile-section">
                        <h4>Hidden Profile (Model's Notes)</h4>
                        <button onclick="loadHiddenProfile()" class="view-btn">👁️ View Hidden Profile</button>
                    </div>
                </div>
            `;
        }
    });
    
    modal.style.display = 'block';
}

function showDiary() {
    const modal = document.getElementById('diaryModal');
    modal.style.display = 'block';
    loadDiaryEntries();
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'none';
}

// Load profile data
async function loadProfileData() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        // Use the correct credentials based on username
        let authUsername = username;
        let authPassword = password;
        
        // Map old credentials to new ones
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch('/api/profile', {
            headers: {
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error loading profile:', error);
        return { error: 'Failed to load profile' };
    }
}

// Update profile
async function updateProfile() {
    try {
        const profileText = document.getElementById('profileText').value;
        
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        let authUsername = username;
        let authPassword = password;
        
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch('/api/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            },
            body: JSON.stringify({ profile: profileText })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('✅ Profile updated successfully!');
            showProfile(); // Reload profile
        } else {
            alert('❌ Error updating profile: ' + result.error);
        }
    } catch (error) {
        console.error('Error updating profile:', error);
        alert('Error updating profile. Please try again.');
    }
}

// Load hidden profile
async function loadHiddenProfile() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        let authUsername = username;
        let authPassword = password;
        
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch('/api/hidden-profile', {
            headers: {
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const hiddenProfile = await response.json();
        if (hiddenProfile.error) {
            alert('Error loading hidden profile: ' + hiddenProfile.error);
        } else {
            const content = document.getElementById('profileContent');
            content.innerHTML = `
                <div class="profile-details">
                    <h3>Hidden Profile - ${hiddenProfile.username}</h3>
                    <div class="profile-section">
                        <h4>Model's Private Notes</h4>
                        <textarea id="hiddenProfileText" class="profile-textarea">${hiddenProfile.hidden_profile}</textarea>
                        <button onclick="updateHiddenProfile()" class="update-btn">💾 Update Hidden Profile</button>
                    </div>
                    <div class="profile-section">
                        <h4>Last Updated</h4>
                        <p>${hiddenProfile.last_updated}</p>
                    </div>
                    <div class="profile-section">
                        <button onclick="showProfile()" class="back-btn">← Back to Profile</button>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading hidden profile:', error);
        alert('Error loading hidden profile. Please try again.');
    }
}

// Update hidden profile
async function updateHiddenProfile() {
    try {
        const hiddenProfileText = document.getElementById('hiddenProfileText').value;
        
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        let authUsername = username;
        let authPassword = password;
        
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch('/api/hidden-profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            },
            body: JSON.stringify({ hidden_profile: hiddenProfileText })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            alert('✅ Hidden profile updated successfully!');
            loadHiddenProfile(); // Reload hidden profile
        } else {
            alert('❌ Error updating hidden profile: ' + result.error);
        }
    } catch (error) {
        console.error('Error updating hidden profile:', error);
        alert('Error updating hidden profile. Please try again.');
    }
}

// Load diary entries
async function loadDiaryEntries() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        // Use the correct credentials based on username
        let authUsername = username;
        let authPassword = password;
        
        // Map old credentials to new ones
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch('/api/diary', {
            headers: {
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const entries = await response.json();
        displayDiaryEntries(entries);
    } catch (error) {
        console.error('Error loading diary:', error);
        displayDiaryEntries([]);
    }
}

// Display diary entries
function displayDiaryEntries(entries) {
    const container = document.getElementById('diaryEntries');
    
    if (!entries || entries.length === 0) {
        container.innerHTML = '<div class="diary-entry empty">No diary entries yet. Write "write in diary - [your thoughts]" in the chat to create your first entry!</div>';
        return;
    }

    container.innerHTML = entries.map(entry => `
        <div class="diary-entry" data-id="${entry.id}">
            <div class="diary-entry-header">
                <span class="diary-entry-date">${formatDate(entry.timestamp)}</span>
                <div class="diary-entry-actions">
                    <button class="diary-entry-edit" onclick="editDiaryEntry('${entry.id}')" title="Edit">✏️</button>
                    <button class="diary-entry-delete" onclick="deleteDiaryEntry('${entry.id}')" title="Delete">🗑️</button>
                </div>
            </div>
            <div class="diary-entry-content">${entry.content}</div>
        </div>
    `).join('');
}

// Format date for display
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Edit diary entry
async function editDiaryEntry(entryId) {
    const newContent = prompt('Edit your diary entry:');
    if (!newContent) return;

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        // Use the correct credentials based on username
        let authUsername = username;
        let authPassword = password;
        
        // Map old credentials to new ones
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch(`/api/diary/${entryId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            },
            body: JSON.stringify({ content: newContent })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            // Reload diary entries immediately
            await loadDiaryEntries();
            console.log('✅ Diary entry updated successfully');
        } else {
            alert('Error updating diary entry: ' + result.error);
        }
    } catch (error) {
        console.error('Error editing diary:', error);
        alert('Error editing diary entry. Please try again.');
    }
}

// Delete diary entry
async function deleteDiaryEntry(entryId) {
    if (!confirm('Are you sure you want to delete this diary entry?')) return;

    try {
        const urlParams = new URLSearchParams(window.location.search);
        const username = urlParams.get('username') || currentUser;
        const password = urlParams.get('password') || '';

        // Use the correct credentials based on username
        let authUsername = username;
        let authPassword = password;
        
        // Map old credentials to new ones
        if (username === 'musser') {
            authUsername = 'meranda';
            authPassword = 'musser';
        }

        const response = await fetch(`/api/diary/${entryId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': 'Basic ' + btoa(authUsername + ':' + authPassword)
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        if (result.success) {
            // Reload diary entries immediately
            await loadDiaryEntries();
            console.log('✅ Diary entry deleted successfully');
        } else {
            alert('Error deleting diary entry: ' + result.error);
        }
    } catch (error) {
        console.error('Error deleting diary:', error);
        alert('Error deleting diary entry. Please try again.');
    }
}

// Utility functions
function clearChat() {
    if (confirm('Are you sure you want to clear the chat history?')) {
        const messagesContainer = document.getElementById('messagesContainer');
        // Keep only the welcome message
        const welcomeMessage = messagesContainer.querySelector('.ai-message');
        messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            messagesContainer.appendChild(welcomeMessage);
        }
        messageHistory = [];
    }
}

function exportChat() {
    const chatData = {
        user: currentUser,
        timestamp: new Date().toISOString(),
        messages: messageHistory
    };
    
    const dataStr = JSON.stringify(chatData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `dr-harmony-chat-${currentUser}-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/';
    }
}

// Close modals when clicking outside
window.addEventListener('click', function(e) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

// Add some CSS for profile details
const profileStyles = document.createElement('style');
profileStyles.textContent = `
    .profile-details {
        padding: 20px;
    }
    
    .profile-details h3 {
        color: #ff1493;
        margin-bottom: 20px;
        font-size: 1.5rem;
        text-align: center;
    }
    
    .profile-section {
        margin-bottom: 20px;
        padding: 15px;
        background: #fff0f5;
        border-radius: 10px;
        border-left: 4px solid #ff1493;
    }
    
    .profile-section h4 {
        color: #c71585;
        margin-bottom: 8px;
        font-size: 1rem;
    }
    
    .profile-section p {
        color: #666;
        line-height: 1.4;
    }
`;
document.head.appendChild(profileStyles);

// Add floating hearts effect to chat
function createChatHearts() {
    setInterval(() => {
        const heart = document.createElement('div');
        heart.innerHTML = '💕';
        heart.style.cssText = `
            position: fixed;
            left: ${Math.random() * 100}%;
            bottom: -50px;
            font-size: ${Math.random() * 15 + 10}px;
            opacity: 0.6;
            pointer-events: none;
            z-index: 1;
            animation: floatUp 6s linear forwards;
        `;
        
        document.body.appendChild(heart);
        
        setTimeout(() => {
            if (heart.parentNode) {
                heart.parentNode.removeChild(heart);
            }
        }, 6000);
    }, 5000);
}

// Start floating hearts
createChatHearts(); 