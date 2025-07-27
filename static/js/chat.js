// Chat functionality JavaScript
// Get username from URL parameters
const urlParams = new URLSearchParams(window.location.search);
let currentUser = urlParams.get('username') || 'meranda';
// Map old username to new one
if (currentUser === 'musser') {
    currentUser = 'meranda';
}
let messageHistory = [];
let currentStreamingMessage = null;
let userProfile = null;
let guardianProfile = null;

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const messagesContainer = document.getElementById('messagesContainer');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Focus on input when page loads
    messageInput.focus();
    
    // Load user profile for avatar
    loadUserProfile();
    
    // Load guardian profile for avatar
    loadGuardianProfile();
    
    // Load conversation history
    loadConversationHistory();

    // Handle message submission
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;

        // Add user message to chat
        addMessage(message, 'user');
        messageInput.value = '';

        // Immediately start streaming - no loading screen
        try {
            // Send message to streaming API
            await sendStreamingMessage(message);
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
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

    // Load system analysis
    loadSystemAnalysis();
});

// Load user profile for avatar
async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile');
        const data = await response.json();
        
        if (data.success && data.profile) {
            userProfile = data.profile;
            // Update existing messages with user avatar
            updateUserAvatars();
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// Load guardian profile for avatar
async function loadGuardianProfile() {
    try {
        const response = await fetch('/api/guardian/profile');
        const data = await response.json();
        
        if (data.success && data.profile) {
            guardianProfile = data.profile;
            // Update existing messages with guardian avatar
            updateGuardianAvatars();
        }
    } catch (error) {
        console.error('Error loading guardian profile:', error);
    }
}

// Send streaming message to API
async function sendStreamingMessage(message) {
    const formData = new FormData();
    formData.append('message', message);

    // Create AI message container for streaming
    currentStreamingMessage = addStreamingMessage();
    
    try {
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            // Fallback to regular API if streaming fails
            console.log('Streaming not available, falling back to regular API');
            const regularResponse = await sendMessage(message);
            
            if (regularResponse.error) {
                throw new Error(regularResponse.error);
            }
            
            addMessage(regularResponse.response, 'ai');
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        await handleStreamData(data);
                    } catch (e) {
                        console.log('Error parsing stream data:', e);
                    }
                }
            }
        }

        // Finalize the streaming message
        if (currentStreamingMessage) {
            finalizeStreamingMessage(currentStreamingMessage);
            currentStreamingMessage = null;
        }

    } catch (error) {
        console.error('Error in streaming:', error);
        
        // Remove streaming message if there was an error
        if (currentStreamingMessage) {
            currentStreamingMessage.remove();
            currentStreamingMessage = null;
        }
        
        addMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
    }
}

// Handle streaming data
async function handleStreamData(data) {
    switch (data.type) {
        case 'status':
            // Remove status messages - they're just decorative
            console.log('Status:', data.message);
            break;
            
        case 'chunk':
            if (currentStreamingMessage && data.content) {
                // Remove typing indicator when we start receiving content
                const typingIndicator = document.querySelector('.typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }
                
                currentStreamingMessage.textContent += data.content;
                scrollToBottom();
            }
            break;
            
        case 'complete':
            // Remove completion message - it's just decorative
            console.log('Streaming completed');
            break;
            
        case 'error':
            console.error('Streaming error:', data.message);
            if (currentStreamingMessage) {
                currentStreamingMessage.textContent = 'Sorry, I encountered an error. Please try again.';
            }
            break;
    }
}

// Add streaming message container
function addStreamingMessage() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message streaming';
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text"></div>
            <div class="message-time">${new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.appendChild(messageDiv);
    
    // Remove typing indicator - it's just decorative
    // const typingIndicator = document.createElement('div');
    // typingIndicator.className = 'typing-indicator';
    // typingIndicator.innerHTML = `
    //     <div class="typing-dot"></div>
    //     <div class="typing-dot"></div>
    //     <div class="typing-dot"></div>
    // `;
    // messagesContainer.appendChild(typingIndicator);
    
    scrollToBottom();
    
    return messageDiv.querySelector('.message-text');
}

// Finalize streaming message
function finalizeStreamingMessage(messageElement) {
    // Remove typing indicator if it exists
    const typingIndicator = document.querySelector('.typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
    
    // Remove streaming class
    const messageDiv = messageElement.closest('.message');
    if (messageDiv) {
        messageDiv.classList.remove('streaming');
    }
    
    // Add any final formatting or processing here
    const messageText = messageElement.textContent;
    messageElement.innerHTML = formatMessage(messageText);
}

// Show status message
// function showStatusMessage(message) {
//     const statusDiv = document.createElement('div');
//     statusDiv.className = 'status-message';
//     statusDiv.textContent = message;
    
//     const messagesContainer = document.getElementById('messagesContainer');
//     messagesContainer.appendChild(statusDiv);
    
//     // Remove status message after 3 seconds
//     setTimeout(() => {
//         if (statusDiv.parentNode) {
//             statusDiv.remove();
//         }
//     }, 3000);
    
//     scrollToBottom();
// }

// Send regular message to API (fallback)
async function sendMessage(message) {
    const formData = new FormData();
    formData.append('message', message);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error sending message:', error);
        return { error: error.message };
    }
}

// Add message to chat
function addMessage(text, sender, timestamp = null) {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const time = timestamp ? 
        new Date(timestamp).toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        }) :
        new Date().toLocaleTimeString('en-US', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

    const avatar = getAvatar(sender);
    const senderName = sender === 'user' ? currentUser.charAt(0).toUpperCase() + currentUser.slice(1) : 'ΔΣ Guardian';

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
    
    // Add to history only for new messages
    if (!timestamp) {
        messageHistory.push({
            text: text,
            sender: sender,
            timestamp: new Date().toISOString()
        });
    }
}

// Get avatar for sender
function getAvatar(sender) {
    if (sender === 'user') {
        if (userProfile && userProfile.avatar_url) {
            return `<img src="${userProfile.avatar_url}" alt="User Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        }
        return '👤';
    } else {
        if (guardianProfile && guardianProfile.avatar_url) {
            return `<img src="${guardianProfile.avatar_url}" alt="Guardian Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        }
        return '💕';
    }
}

// Update user avatars in existing messages
function updateUserAvatars() {
    if (!userProfile || !userProfile.avatar_url) return;
    
    const userMessages = document.querySelectorAll('.user-message .message-avatar');
    userMessages.forEach(avatarDiv => {
        if (!avatarDiv.querySelector('img')) {
            avatarDiv.innerHTML = `<img src="${userProfile.avatar_url}" alt="User Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        }
    });
}

// Update guardian avatars in existing messages
function updateGuardianAvatars() {
    if (!guardianProfile || !guardianProfile.avatar_url) return;
    
    const guardianMessages = document.querySelectorAll('.ai-message .message-avatar');
    guardianMessages.forEach(avatarDiv => {
        if (!avatarDiv.querySelector('img')) {
            avatarDiv.innerHTML = `<img src="${guardianProfile.avatar_url}" alt="Guardian Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        }
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

// Show loading overlay - DISABLED for streaming
function showLoading() {
    // Loading overlay removed - streaming shows live generation instead
    console.log('Loading disabled - using streaming instead');
}

// Hide loading overlay - DISABLED for streaming
function hideLoading() {
    // Loading overlay removed - streaming shows live generation instead
    console.log('Loading disabled - using streaming instead');
}

// Quick message functions
function sendQuickMessage(message) {
    const messageInput = document.getElementById('messageInput');
    messageInput.value = message;
    document.getElementById('messageForm').dispatchEvent(new Event('submit'));
}

// Modal functions
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.style.display = 'none';
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

// Load conversation history
async function loadConversationHistory() {
    try {
        const response = await fetch('/api/conversation-history');

        if (response.ok) {
            const data = await response.json();
            
            // Display conversation history
            if (data.history && data.history.length > 0) {
                displayConversationHistory(data.history);
            }
            
            // Update statistics if needed
            if (data.statistics) {
                updateConversationStats(data.statistics);
            }
        }
    } catch (error) {
        console.error('Error loading conversation history:', error);
    }
}

// Display conversation history in chat
function displayConversationHistory(history) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Clear existing messages
    messagesContainer.innerHTML = '';
    
    // Add each message from history
    history.forEach(entry => {
        // Add user message
        if (entry.message) {
            addMessage(entry.message, 'user', entry.timestamp);
        }
        
        // Add AI response
        if (entry.ai_response) {
            addMessage(entry.ai_response, 'ai', entry.timestamp);
        }
    });
    
    // Update avatars after loading history
    updateUserAvatars();
    updateGuardianAvatars();
    
    // Scroll to bottom
    scrollToBottom();
}

// Update conversation statistics
function updateConversationStats(stats) {
    // You can add UI elements to show statistics
    console.log('Conversation stats:', stats);
}

// Load conversation archive
async function loadConversationArchive() {
    try {
        const response = await fetch('/api/conversation-archive');

        if (response.ok) {
            const data = await response.json();
            displayConversationArchive(data);
        } else {
            console.error('Failed to load conversation archive');
        }
    } catch (error) {
        console.error('Error loading conversation archive:', error);
    }
}

// Display conversation archive
function displayConversationArchive(data) {
    // Create modal for archive display
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'archiveModal';
    
    let archiveContent = '<div class="modal-content">';
    archiveContent += '<span class="close" onclick="closeModal(\'archiveModal\')">&times;</span>';
    archiveContent += '<h2>Conversation Archive</h2>';
    
    if (data.summary) {
        archiveContent += `<p><strong>Summary:</strong> ${data.summary}</p>`;
    }
    
    if (data.archive && data.archive.length > 0) {
        archiveContent += '<div class="archive-entries">';
        data.archive.forEach(entry => {
            archiveContent += `
                <div class="archive-entry">
                    <h3>${entry.timestamp}</h3>
                    <p><strong>Period:</strong> ${entry.period_start} to ${entry.period_end}</p>
                    <p><strong>Messages:</strong> ${entry.original_count}</p>
                    <p><strong>Summary:</strong> ${entry.summary}</p>
                    <button onclick="editArchiveEntry('${entry.id}')">Edit Summary</button>
                </div>
            `;
        });
        archiveContent += '</div>';
    } else {
        archiveContent += '<p>No archived conversations yet.</p>';
    }
    
    archiveContent += '</div>';
    modal.innerHTML = archiveContent;
    
    document.body.appendChild(modal);
    modal.style.display = 'block';
}

// Edit archive entry
async function editArchiveEntry(archiveId) {
    const summary = prompt('Enter new summary for this conversation:');
    if (!summary) return;

    try {
        const formData = new FormData();
        formData.append('summary', summary);

        const response = await fetch(`/api/conversation-archive/${archiveId}`, {
            method: 'PUT',
            body: formData
        });

        if (response.ok) {
            alert('Archive entry updated successfully!');
            loadConversationArchive(); // Reload the archive
        } else {
            alert('Failed to update archive entry');
        }
    } catch (error) {
        console.error('Error editing archive entry:', error);
        alert('Error updating archive entry');
    }
}

// Clear conversation history
async function clearConversationHistory() {
    if (!confirm('Are you sure you want to clear all conversation history? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/conversation-clear', {
            method: 'POST'
        });

        if (response.ok) {
            // Clear the chat display
            const messagesContainer = document.getElementById('messagesContainer');
            messagesContainer.innerHTML = '';
            
            // Add a system message
            addMessage('Conversation history has been cleared.', 'system');
            
            alert('Conversation history cleared successfully!');
        } else {
            alert('Failed to clear conversation history');
        }
    } catch (error) {
        console.error('Error clearing conversation history:', error);
        alert('Error clearing conversation history');
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

// Load system analysis
async function loadSystemAnalysis() {
    try {
        const response = await fetch('/api/system-analysis');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.analysis) {
                updateSystemPanel(data.analysis);
                
                // Apply theme automatically if provided
                if (data.theme) {
                    applyTheme(data.theme);
                }
            }
        } else {
            showSystemError('Failed to load system analysis');
        }
    } catch (error) {
        console.error('Error loading system analysis:', error);
        showSystemError('Error loading system analysis');
    }
}

// Apply theme automatically
function applyTheme(themeName) {
    // Remove existing theme classes
    document.body.classList.remove('theme-romantic', 'theme-neutral', 'theme-melancholy');
    
    // Add new theme class
    if (themeName && ['romantic', 'neutral', 'melancholy'].includes(themeName)) {
        document.body.classList.add(`theme-${themeName}`);
        console.log(`Applied theme: ${themeName}`);
    }
}

// Show model status
async function showModelStatus() {
    try {
        const response = await fetch('/api/model-status');
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.success && data.status) {
                const status = data.status;
                
                let statusHtml = `
                    <div class="model-status-modal">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h2>🤖 AI Model Status</h2>
                                <span class="close" onclick="closeModal('modelStatusModal')">&times;</span>
                            </div>
                            <div class="modal-body">
                                <div class="current-model">
                                    <h3>Current Model: ${status.current_model}</h3>
                                    <p>Quota: ${status.current_quota} requests/day</p>
                                    <p>Model ${status.model_index + 1} of ${status.total_models}</p>
                                </div>
                                
                                <div class="model-list">
                                    <h3>Available Models:</h3>
                                    <div class="model-grid">
                `;
                
                status.available_models.forEach((model, index) => {
                    const isCurrent = index === status.model_index;
                    const hasError = model.has_error;
                    const statusClass = isCurrent ? 'current' : hasError ? 'error' : 'available';
                    
                    statusHtml += `
                        <div class="model-item ${statusClass}">
                            <div class="model-name">${model.name}</div>
                            <div class="model-quota">${model.quota} req/day</div>
                            ${isCurrent ? '<div class="model-status">🔄 Current</div>' : ''}
                            ${hasError ? '<div class="model-status">⚠️ Quota Exceeded</div>' : ''}
                        </div>
                    `;
                });
                
                statusHtml += `
                                    </div>
                                </div>
                                
                                <div class="model-info">
                                    <p><strong>Auto-fallback:</strong> System automatically switches models when quota is exceeded</p>
                                    <p><strong>Error count:</strong> ${status.model_errors} models with quota issues</p>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add modal to page
                const modalContainer = document.createElement('div');
                modalContainer.id = 'modelStatusModal';
                modalContainer.className = 'modal';
                modalContainer.innerHTML = statusHtml;
                document.body.appendChild(modalContainer);
                
                // Show modal
                modalContainer.style.display = 'block';
            }
        } else {
            console.error('Failed to load model status');
        }
    } catch (error) {
        console.error('Error loading model status:', error);
    }
}

function updateSystemPanel(analysis) {
    // Update system status
    const statusElement = document.getElementById('systemStatus');
    if (statusElement && analysis.system_status) {
        statusElement.innerHTML = `
            <div class="status-text">
                ${analysis.system_status.replace(/\n/g, '<br>')}
            </div>
        `;
    }
    
    // Update tips
    const tipsElement = document.getElementById('systemTips');
    if (tipsElement && analysis.tips) {
        tipsElement.innerHTML = analysis.tips.map(tip => `
            <div class="tip-item">
                 ${tip}
            </div>
        `).join('');
    }
}

function showSystemError(message) {
    const statusElement = document.getElementById('systemStatus');
    const tipsElement = document.getElementById('systemTips');
    
    if (statusElement) {
        statusElement.innerHTML = `<div class="error-message">${message}</div>`;
    }
    
    if (tipsElement) {
        tipsElement.innerHTML = `<div class="error-message">Failed to load tips</div>`;
    }
}

// Auto-refresh system analysis every 5 minutes
setInterval(loadSystemAnalysis, 5 * 60 * 1000);