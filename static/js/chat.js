// Chat functionality JavaScript
// Get username from URL parameters
const urlParams = new URLSearchParams(window.location.search);
let currentUser = urlParams.get('username');
// Map old username to new one
if (currentUser === 'musser') {
    currentUser = 'meranda';
}

// If no username in URL, we'll get it from the server
let messageHistory = [];
let currentStreamingMessage = null;
let userProfile = null;
let guardianProfile = null;
let attachedFiles = []; // Track attached files for current message

// Global variables for user avatars
let userAvatars = {};

let greetingShown = false;

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const messagesContainer = document.getElementById('messagesContainer');
    const loadingBanner = document.getElementById('loadingBanner');

    // Don't show loading banner immediately - only show if actually loading
    // showLoadingBanner(); // REMOVED - was causing slow loading perception
    
    // Load everything in parallel for speed
    Promise.all([
        loadUserProfile(),
        loadGuardianProfile(),
        loadConversationHistory(),
        loadSystemAnalysis()
    ]).then(() => {
        // Hide loading banner when everything is loaded
        hideLoadingBanner();
        
        // Focus on input after loading
        messageInput.focus();
        
        // Initialize technical steps toggles
        initializeTechnicalSteps();
        
        // Start login greeting
        startLoginGreeting();
    }).catch((error) => {
        console.error('Error during initialization:', error);
        hideLoadingBanner();
        messageInput.focus();
    });

    // Handle message submission
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message && attachedFiles.length === 0) return;

        // Add user message to chat with attached files
        addMessage(message, 'user', null, null, attachedFiles);
        messageInput.value = '';
        
        // Clear attached files
        attachedFiles = [];
        updateAttachedFilesDisplay();

        // Immediately start streaming - no loading screen
        try {
            // Send message to streaming API with attached files
            await sendStreamingMessage(message);
            
            // If there are attached images, analyze them
            for (const file of attachedFiles) {
                if (file.type && file.type.startsWith('image/')) {
                    await sendImageForAnalysis(file.path, file.name);
                }
            }
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
    
    // Initialize file upload functionality
    initializeFileUpload();
    
    // Initialize terminal
    initializeTerminal();

    // Инициализируем кнопки System Analysis
    initializeSystemAnalysisButtons();
});

// Initialize technical steps toggles
function initializeTechnicalSteps() {
    // Add event listeners to existing technical steps
    document.querySelectorAll('.technical-steps').forEach(details => {
        details.addEventListener('toggle', function() {
            const toggle = this.querySelector('.toggle-text');
            const icon = this.querySelector('.toggle-icon');
            
            if (this.open) {
                toggle.textContent = 'Hide Technical Steps';
                icon.textContent = '▲';
            } else {
                toggle.textContent = 'Show Technical Steps';
                icon.textContent = '▼';
            }
        });
    });
}

// Load user profile for avatar
async function loadUserProfile() {
    try {
        const response = await fetch('/api/profile', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.profile) {
                userProfile = data.profile;
                // Set currentUser from server response if not already set
                if (!currentUser && userProfile.username) {
                    currentUser = userProfile.username;
                    console.log('Set currentUser from server:', currentUser);
                }
                return userProfile;
            } else {
                console.error('Invalid profile data format:', data);
                return null;
            }
        } else {
            console.error('Failed to load user profile:', response.status);
            return null;
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
        return null;
    }
}

// Load guardian profile for avatar
async function loadGuardianProfile() {
    try {
        const response = await fetch('/api/guardian/profile', {
            credentials: 'include'
        });
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

// Load avatar for specific user
async function loadUserAvatar(username) {
    if (userAvatars[username]) {
        return userAvatars[username];
    }
    
    try {
        // Try different possible avatar file names
        const possibleNames = [
            `${username}_avatar.jpg`,
            `${username}_avatar.png`,
            `${username}.jpg`,
            `${username}.png`,
            `avatar_${username}.jpg`,
            `avatar_${username}.png`
        ];

        // Check each possible filename
        for (const filename of possibleNames) {
            const avatarUrl = `/static/avatars/${filename}`;
            
            // Check if avatar exists by trying to load it
            const exists = await checkImageExists(avatarUrl);
            if (exists) {
                userAvatars[username] = avatarUrl;
                return avatarUrl;
            }
        }
        
        // No avatar found
        userAvatars[username] = null;
        return null;
        
    } catch (error) {
        console.error(`Error loading avatar for ${username}:`, error);
        return null;
    }
}

// Check if image exists
function checkImageExists(url) {
    return new Promise((resolve) => {
        const img = new Image();
        img.onload = function() {
            resolve(true);
        };
        img.onerror = function() {
            resolve(false);
        };
        img.src = url;
    });
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
            body: formData,
            credentials: 'include'
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
            if (!currentStreamingMessage) {
                currentStreamingMessage = addStreamingMessage();
            }
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
        case 'message_complete':
            if (currentStreamingMessage) {
                finalizeStreamingMessage(currentStreamingMessage);
                currentStreamingMessage = null;
            }
            break;
        case 'final_response':
            // Заменяем текущее сообщение на финальный ответ с результатами tool calls
            if (currentStreamingMessage) {
                currentStreamingMessage.textContent = data.content;
                finalizeStreamingMessage(currentStreamingMessage);
                currentStreamingMessage = null;
            }
            break;
        case 'tool_result':
            // Показываем результат выполнения tool call
            console.log('Tool executed:', data.tool, 'Result:', data.result);
            break;
        case 'tool_error':
            // Показываем ошибку tool call
            console.error('Tool error:', data.tool, 'Error:', data.error);
            break;
        case 'greeting':
            greetingShown = true;
            addMessage(data.content, 'ai');
            break;
        case 'system_status':
            addMessage(data.content, 'ai');
            break;
        case 'greeting_complete':
            hideLoadingBanner();
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
        body: formData,
            credentials: 'include'
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
function addMessage(text, sender, timestamp = null, messageId = null, attachedFiles = []) {
    const messagesContainer = document.getElementById('messagesContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    if (messageId) {
        messageDiv.setAttribute('data-message-id', messageId);
    }
    
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
    
    // Handle different senders: 'ai', 'user' (current user), or specific usernames
    let senderName;
    if (sender === 'ai') {
        senderName = 'ΔΣ Guardian';
    } else if (sender === 'user') {
        // Use currentUser if available, otherwise try to get from userProfile
        let username = currentUser;
        if (!username && userProfile && userProfile.username) {
            username = userProfile.username;
            currentUser = username; // Update currentUser for future use
        }
        senderName = username ? username.charAt(0).toUpperCase() + username.slice(1) : 'User';
    } else {
        // Specific username from history (meranda, stepan, etc.)
        senderName = sender.charAt(0).toUpperCase() + sender.slice(1);
    }

    // Add edit/delete buttons for current user's messages only
    const actionsHtml = (sender === 'user' || sender === currentUser) ? `
        <div class="message-actions">
            <button class="message-action-btn" onclick="editMessage('${messageId || ''}')" title="Edit">✏️</button>
            <button class="message-action-btn" onclick="deleteMessage('${messageId || ''}')" title="Delete">🗑️</button>
        </div>
    ` : '';

    // Add attached files display
    let attachedFilesHtml = '';
    if (attachedFiles && attachedFiles.length > 0) {
        attachedFilesHtml = '<div class="attached-files">';
        attachedFiles.forEach(file => {
            if (file.type && file.type.startsWith('image/')) {
                attachedFilesHtml += `
                    <div class="attached-file">
                        <img src="${file.url}" alt="${file.name}" class="attached-image">
                        <div class="file-info">
                            <span class="file-name">${file.name}</span>
                        </div>
                    </div>
                `;
            } else {
                attachedFilesHtml += `
                    <div class="attached-file">
                        <div class="file-icon">📁</div>
                        <div class="file-info">
                            <span class="file-name">${file.name}</span>
                            <span class="file-size">${formatFileSize(file.size)}</span>
                        </div>
                    </div>
                `;
            }
        });
        attachedFilesHtml += '</div>';
    }

    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender">${senderName}</span>
                <span class="time">${time}</span>
            </div>
            <div class="message-text">${formatMessage(text)}</div>
            ${attachedFilesHtml}
            ${actionsHtml}
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    // Initialize technical steps for new message
    const technicalSteps = messageDiv.querySelector('.technical-steps');
    if (technicalSteps) {
        technicalSteps.addEventListener('toggle', function() {
            const toggle = this.querySelector('.toggle-text');
            const icon = this.querySelector('.toggle-icon');
            
            if (this.open) {
                toggle.textContent = 'Hide Technical Steps';
                icon.textContent = '▲';
            } else {
                toggle.textContent = 'Show Technical Steps';
                icon.textContent = '▼';
            }
        });
    }
    
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
    if (sender === 'ai') {
        return `<img src="/static/avatars/guardian_avatar.jpg" alt="Guardian Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
    } else if (sender === 'user') {
        // Current user
        if (userProfile && userProfile.username) {
            const avatarUrl = `/static/avatars/${userProfile.username}_avatar.jpg`;
            return `<img src="${avatarUrl}" alt="User Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
        }
        return '👤';
    } else {
        // Specific username from history (meranda, stepan, etc.)
        const avatarUrl = `/static/avatars/${sender}_avatar.jpg`;
        return `<img src="${avatarUrl}" alt="${sender} Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
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

// Format message with reasoning support
function formatMessage(text) {
    // Check for reasoning format
    if (text.includes('🤖 **REASONING PROCESS:**') && text.includes('💬 **FINAL RESPONSE:**')) {
        return formatReasoningMessage(text);
    }
    
    // Check for technical steps
    const hasTechnicalSteps = text.includes('🔧 **Executing:') || text.includes('✅ **Result:') || text.includes('🎯 **Ready for final response');
    
    if (hasTechnicalSteps) {
        // Show technical steps with proper formatting
        return formatTechnicalSteps(text);
    }
    
    // Enhanced formatting with rich text support
    return formatRichText(text);
}

// Format reasoning message with chain of thoughts
function formatReasoningMessage(text) {
    // Split reasoning into parts
    const reasoningMatch = text.match(/(🤖 \*\*REASONING PROCESS:\*\*|REASONING PROCESS:)([\s\S]*?)(💬 \*\*FINAL RESPONSE:\*\*|FINAL RESPONSE:)([\s\S]*)/);
    
    if (reasoningMatch) {
        const reasoningProcess = reasoningMatch[2].trim();
        const finalResponse = reasoningMatch[4].trim();
        
        // Format reasoning steps
        const reasoningSteps = formatReasoningSteps(reasoningProcess);
        
        // Format final response
        const formattedResponse = formatRichText(finalResponse);
        
        return `
            <div class="reasoning-container">
                <div class="reasoning-header">
                    <span class="reasoning-icon">🧠</span>
                    <span class="reasoning-title">Chain of Thoughts</span>
                </div>
                <div class="reasoning-steps">
                    ${reasoningSteps}
                </div>
                <div class="final-response">
                    <div class="final-response-header">
                        <span class="response-icon">💬</span>
                        <span class="response-title">Final Response</span>
                    </div>
                    <div class="response-content">
                        ${formattedResponse}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Fallback to regular formatting
    return formatRichText(text);
}

// Format reasoning steps
function formatReasoningSteps(reasoningText) {
    // Split by numbered steps
    const steps = reasoningText.split(/(\d+\.)/).filter(step => step.trim());
    let formattedSteps = '';
    
    for (let i = 0; i < steps.length; i += 2) {
        if (steps[i] && steps[i + 1]) {
            const stepNumber = steps[i];
            const stepContent = steps[i + 1].trim();
            
            formattedSteps += `
                <div class="reasoning-step">
                    <div class="step-number">${stepNumber}</div>
                    <div class="step-content">${formatRichText(stepContent)}</div>
                </div>
            `;
        }
    }
    
    return formattedSteps || `<div class="reasoning-text">${formatRichText(reasoningText)}</div>`;
}

function formatRichText(text) {
    // Convert URLs to links
    text = text.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color: inherit; text-decoration: underline;">$1</a>');
    
    // Markdown-style formatting
    // Bold text: **text** or __text__
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Italic text: *text* or _text_ (but preserve tool calls)
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Only apply italic formatting if not a tool call pattern
    // Protect underscores in tool calls and variable names
    text = text.replace(/(?<!tool_code\.|toolcode\.|print\s*\(\s*tool_code\.|print\s*\(\s*toolcode\.|read_file\(|create_file\(|append_to_file\(|write_file\(|edit_file\(|delete_file\(|list_files\(|search_files\(|safe_create_file\(|read_user_profile\(|read_emotional_history\(|search_user_data\(|update_current_feeling\(|add_user_observation\(|add_model_note\(|add_personal_thought\(|get_system_logs\(|get_error_summary\(|analyze_image\(|web_search\(|generate_system_greeting\(|plan_step\(|act_step\(|reflect\(|react_cycle\(|fetch_url\(|call_api\(|integrate_api\(|call_custom_api\(|get_weather\(|translate_text\(|create_event\(|get_upcoming_events\(|reschedule_event\(|complete_event\(|get_event_statistics\(|create_task_list\(|list_tasks\(|run_terminal_command\(|get_system_info\(|diagnose_network\(|get_project_structure\(|find_images\(|_file_path|_content|_entry|guardian_sandbox|guardiansandbox)_([^_]+)_/g, '<em>$1</em>');
    
    // Code blocks: ```code``` or `code`
    text = text.replace(/```([\s\S]*?)```/g, '<pre class="code-block"><code>$1</code></pre>');
    text = text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
    
    // Headers: # Header, ## Header, ### Header
    text = text.replace(/^### (.*$)/gm, '<h3 class="message-header">$1</h3>');
    text = text.replace(/^## (.*$)/gm, '<h2 class="message-header">$1</h2>');
    text = text.replace(/^# (.*$)/gm, '<h1 class="message-header">$1</h1>');
    
    // Lists: - item or * item
    text = text.replace(/^[\s]*[-*] (.*$)/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ul class="message-list">$1</ul>');
    
    // Numbered lists: 1. item
    text = text.replace(/^[\s]*\d+\. (.*$)/gm, '<li>$1</li>');
    text = text.replace(/(<li>.*<\/li>)/s, '<ol class="message-list">$1</ol>');
    
    // Blockquotes: > text
    text = text.replace(/^> (.*$)/gm, '<blockquote class="message-quote">$1</blockquote>');
    
    // Horizontal rules: ---
    text = text.replace(/^---$/gm, '<hr class="message-divider">');
    
    // Special formatting for system messages
    text = text.replace(/^🔧 (.*$)/gm, '<div class="system-step executing">🔧 $1</div>');
    text = text.replace(/^✅ (.*$)/gm, '<div class="system-step success">✅ $1</div>');
    text = text.replace(/^❌ (.*$)/gm, '<div class="system-step error">❌ $1</div>');
    text = text.replace(/^⚠️ (.*$)/gm, '<div class="system-step warning">⚠️ $1</div>');
    text = text.replace(/^🎯 (.*$)/gm, '<div class="system-step target">🎯 $1</div>');
    text = text.replace(/^💬 (.*$)/gm, '<div class="system-step chat">💬 $1</div>');
    
    // Convert line breaks to <br> (after all other formatting)
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

function formatTechnicalSteps(steps) {
    // Format technical steps with proper styling
    return steps
        .replace(/(🔧 \*\*Executing:\*\*)/g, '<div class="executing-step">$1</div>')
        .replace(/(✅ \*\*Result:\*\*)/g, '<div class="result-step">$1</div>')
        .replace(/(🎯 \*\*Ready for final response|\🎯 \*\*No more tools needed)/g, '<div class="step-header">$1</div>')
        .replace(/\n/g, '<br>');
}

function formatFinalResponse(response) {
    // Format final response, removing any remaining technical markers
    return response
        .replace(/(💬 \*\*Final response:\*\*)/g, '<div class="final-response-header">$1</div>')
        .replace(/(🎯 \*\*Ready for final response|\🎯 \*\*No more tools needed|\💬 \*\*Generating final response)/g, '')
        .replace(/\n/g, '<br>');
}

// Scroll to bottom of messages
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        // Use requestAnimationFrame for smooth scrolling
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }
}

// Loading banner functions
function showLoadingBanner() {
    const loadingBanner = document.getElementById('loadingBanner');
    const messagesContainer = document.getElementById('messagesContainer');
    if (loadingBanner) {
        loadingBanner.classList.remove('hidden');
    }
    if (messagesContainer) {
        messagesContainer.classList.add('loading');
    }
}

function hideLoadingBanner() {
    const loadingBanner = document.getElementById('loadingBanner');
    const messagesContainer = document.getElementById('messagesContainer');
    if (loadingBanner) {
        loadingBanner.classList.add('hidden');
    }
    if (messagesContainer) {
        messagesContainer.classList.remove('loading');
    }
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
    if (modal) {
        modal.style.display = 'none';
        modal.remove();
    }
}

// Close model status modal specifically
function closeModelStatus() {
    closeModal('modelStatusModal');
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
        // Show loading banner only if we're actually loading something
        showLoadingBanner();
        
        const response = await fetch('/api/conversation-history?limit=20', {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            
            // Display conversation history
            if (data.history && data.history.length > 0) {
                displayConversationHistory(data.history);
            }
            // Don't show welcome message - let login greeting handle it naturally
            
            // Update statistics if needed
            if (data.statistics) {
                updateConversationStats(data.statistics);
            }
        } else {
            console.error('Failed to load conversation history');
            showWelcomeMessage();
        }
    } catch (error) {
        console.error('Error loading conversation history:', error);
        showWelcomeMessage();
    } finally {
        // Always hide loading banner when done
        hideLoadingBanner();
    }
}

// Show welcome message when no history exists
function showWelcomeMessage() {
    // Don't show hardcoded welcome message - let the AI generate it naturally
    // The login greeting will handle this automatically
}

// Display conversation history in chat
function displayConversationHistory(history) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Clear existing messages
    messagesContainer.innerHTML = '';
    
    // Collect unique usernames from history
    const usernames = new Set();
    history.forEach(entry => {
        if (entry.user) {
            usernames.add(entry.user);
        }
    });
    
    // Load avatars for all users in history
    const avatarPromises = Array.from(usernames).map(username => loadUserAvatar(username));
    
    // Wait for avatars to load, then display messages
    Promise.all(avatarPromises).then(() => {
        // Add each message from history
        history.forEach(entry => {
            // Add user message with correct username
            if (entry.message) {
                const sender = entry.user || 'user'; // Use actual username from history
                addMessage(entry.message, sender, entry.timestamp, entry.id);
            }
            
            // Add AI response
            if (entry.ai_response) {
                addMessage(entry.ai_response, 'ai', entry.timestamp, entry.id);
            }
        });
        
        // Update avatars after loading history
        updateUserAvatars();
        updateGuardianAvatars();
        
        // Update avatars for specific users
        updateSpecificUserAvatars();
        
        // Scroll to bottom AFTER all messages are added
        setTimeout(() => {
            scrollToBottom();
        }, 100);
    });
}

// Update avatars for specific users in history
function updateSpecificUserAvatars() {
    const messages = document.querySelectorAll('.message');
    messages.forEach(message => {
        // Determine sender from message classes
        let sender = null;
        if (message.classList.contains('meranda-message')) {
            sender = 'meranda';
        } else if (message.classList.contains('stepan-message')) {
            sender = 'stepan';
        } else if (message.classList.contains('ai-message')) {
            sender = 'ai';
        }
        
        if (sender && sender !== 'ai') {
            const avatarElement = message.querySelector('.message-avatar');
            if (avatarElement) {
                const avatarUrl = userAvatars[sender];
                if (avatarUrl) {
                    avatarElement.innerHTML = `<img src="${avatarUrl}" alt="${sender} Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
                } else {
                    // Use fallback emoji
                    avatarElement.innerHTML = sender === 'meranda' ? '👩' : '👨';
                }
            }
        }
    });
}

// Update conversation statistics
function updateConversationStats(stats) {
    // You can add UI elements to show statistics
    console.log('Conversation stats:', stats);
}

// Load conversation archive
async function loadConversationArchive() {
    try {
        const response = await fetch('/api/conversation-archive', {
            credentials: 'include'
        });

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
    archiveContent += '<h2>📚 Conversation Archive</h2>';
    
    if (data.summary) {
        archiveContent += `<div class="archive-summary"><p><strong>📋 Overall Summary:</strong> ${data.summary}</p></div>`;
    }
    
    if (data.archive && data.archive.length > 0) {
        archiveContent += '<div class="archive-entries">';
        data.archive.forEach(entry => {
            const date = new Date(entry.timestamp);
            const formattedDate = date.toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'short', 
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
            
            archiveContent += `
                <div class="archive-entry">
                    <h3>${formattedDate}</h3>
                    <div class="archive-details">
                        <p><strong>⏰ Period:</strong> ${entry.period_start} to ${entry.period_end}</p>
                        <p><strong>💬 Messages:</strong> ${entry.original_count}</p>
                        <p><strong>📝 Summary:</strong> ${entry.summary}</p>
                    </div>
                    <button onclick="editArchiveEntry('${entry.id}')">
                        ✏️ Edit Summary
                    </button>
                </div>
            `;
        });
        archiveContent += '</div>';
    } else {
        archiveContent += '<div class="archive-empty"><p>📭 No archived conversations yet.</p></div>';
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
            body: formData,
            credentials: 'include'
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
            method: 'POST',
            credentials: 'include'
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
        const response = await fetch('/api/system-analysis', {
            credentials: 'same-origin'  // Internal agent endpoint, no auth required
        });
        
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
            console.log('System analysis not available or failed to load');
            // Don't show error for internal agent endpoint
        }
    } catch (error) {
        console.log('System analysis endpoint not available:', error);
        // Don't show error for internal agent endpoint
    }
}

// Force refresh system analysis (clear cache)
async function forceRefreshSystemAnalysis() {
    try {
        console.log('⚡ Force refreshing system analysis...');
        
        // Сначала очищаем кэш на сервере
        const clearResponse = await fetch('/api/system-analysis/clear-cache', {
            method: 'POST',
            credentials: 'same-origin'
        });
        
        if (clearResponse.ok) {
            console.log('✅ Cache cleared, refreshing...');
        }
        
        // Затем загружаем свежий анализ
        await loadSystemAnalysis();
    } catch (error) {
        console.error('Error force refreshing system analysis:', error);
        // Fallback to normal refresh
        await loadSystemAnalysis();
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
        console.log('🔄 Fetching model status...');
        const response = await fetch('/api/model-status', {
            credentials: 'same-origin'  // Internal agent endpoint, no auth required
        });

        if (response.ok) {
            const data = await response.json();
            console.log('📊 Model status data:', data);
            
            if (data.success && data.status) {
                const status = data.status;
                console.log('🎯 Current model:', status.current_model);
                console.log('📈 Model index:', status.model_index);
                
                let statusHtml = `
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
                    const clickable = !isCurrent ? 'clickable' : '';
                    
                    statusHtml += `
                        <div class="model-item ${statusClass} ${clickable}" 
                             data-model="${model.name}">
                            <div class="model-name">${model.name}</div>
                            <div class="model-quota">${model.quota} req/day</div>
                            ${isCurrent ? '<div class="model-status">🔄 Current</div>' : ''}
                            ${hasError ? '<div class="model-status">⚠️ Quota Exceeded</div>' : ''}
                            ${!isCurrent ? '<div class="model-hint">Click to switch</div>' : ''}
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
                `;
                
                // Update existing modal content
                const modalContent = document.getElementById('modelStatusContent');
                if (modalContent) {
                    modalContent.innerHTML = statusHtml;
                    
                    // Show modal
                    const modal = document.getElementById('modelStatusModal');
                    modal.style.display = 'block';
                    
                    // Add event listeners for model items
                    const modelItems = modalContent.querySelectorAll('.model-item.clickable');
                    modelItems.forEach(item => {
                        const modelName = item.getAttribute('data-model');
                        item.addEventListener('click', () => switchModel(modelName));
                    });
                    
                    console.log('✅ Model status modal displayed');
                } else {
                    console.error('Modal content element not found');
                }
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
        // Handle system_status as object with multiple fields
        let statusHtml = '';
        if (typeof analysis.system_status === 'object') {
            // Format object fields
            for (const [key, value] of Object.entries(analysis.system_status)) {
                const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                statusHtml += `
                    <div class="status-section">
                        <h5>${formattedKey}:</h5>
                        <p>${typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</p>
                    </div>
                `;
            }
        } else {
            // Handle as string
            statusHtml = `<div class="status-text">${analysis.system_status.replace(/\n/g, '<br>')}</div>`;
        }
        statusElement.innerHTML = statusHtml;
    }
    

}

function showSystemError(message) {
    const statusElement = document.getElementById('systemStatus');
    
    if (statusElement) {
        statusElement.innerHTML = `<div class="error-message">${message}</div>`;
    }
}

// Auto-refresh system analysis every 5 minutes
setInterval(loadSystemAnalysis, 5 * 60 * 1000);

// File upload functionality
function initializeFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const fileDropZone = document.getElementById('fileDropZone');
    const messageInput = document.getElementById('messageInput');
    
    // File input change handler
    fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop handlers
    messageInput.addEventListener('dragenter', showDropZone);
    messageInput.addEventListener('dragover', handleDragOver);
    messageInput.addEventListener('dragleave', handleDragLeave);
    messageInput.addEventListener('drop', handleDrop);
    
    // Drop zone handlers
    fileDropZone.addEventListener('dragenter', handleDragOver);
    fileDropZone.addEventListener('dragover', handleDragOver);
    fileDropZone.addEventListener('dragleave', handleDragLeave);
    fileDropZone.addEventListener('drop', handleDrop);
    
    // Click to upload
    fileDropZone.addEventListener('click', () => fileInput.click());
}

function showDropZone() {
    const fileDropZone = document.getElementById('fileDropZone');
    fileDropZone.style.display = 'block';
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const fileDropZone = document.getElementById('fileDropZone');
    fileDropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const fileDropZone = document.getElementById('fileDropZone');
    fileDropZone.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const fileDropZone = document.getElementById('fileDropZone');
    fileDropZone.classList.remove('drag-over');
    fileDropZone.style.display = 'none';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFiles(files);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFiles(files);
    }
    // Reset input
    e.target.value = '';
}

async function handleFiles(files) {
    for (const file of files) {
        await uploadFile(file);
        }
}

async function uploadFile(file) {
        const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload-file', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add file to attached files list
            attachedFiles.push({
                name: file.name,
                path: data.file_path,
                url: data.file_path,
                size: file.size,
                type: file.type
            });
            
            // Update display
            updateAttachedFilesDisplay();
            
            // Remove the temporary upload message
            const tempMessage = document.querySelector('.file-upload-message');
            if (tempMessage) {
                tempMessage.remove();
            }
        } else {
            showStatusMessage('Upload failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showStatusMessage('Upload failed', 'error');
    }
}

function addFileUploadMessage(file) {
    const messageId = 'file_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    const messagesContainer = document.getElementById('messagesContainer');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user-message';
    messageDiv.id = messageId;
    
    const avatar = getAvatar('user');
    const timestamp = new Date().toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="sender">${currentUser.charAt(0).toUpperCase() + currentUser.slice(1)}</span>
                <span class="time">${timestamp}</span>
            </div>
            <div class="message-text">
                <div class="file-message">
                    <div class="file-icon">📁</div>
                    <div class="file-info">
                        <div class="file-name">${file.name}</div>
                        <div class="file-size">${formatFileSize(file.size)}</div>
                        <div class="upload-progress">
                            <div class="upload-progress-bar"></div>
                        </div>
                    </div>
                    <div class="file-actions">
                        <button class="file-btn" disabled>Uploading...</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    scrollToBottom();
    
    // Simulate upload progress
    const progressBar = messageDiv.querySelector('.upload-progress-bar');
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 20;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
        }
        progressBar.style.width = progress + '%';
    }, 100);
    
    return messageId;
}

function updateFileMessage(messageId, data) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    const fileActions = messageDiv.querySelector('.file-actions');
    const progressBar = messageDiv.querySelector('.upload-progress-bar');
    
    if (data.error) {
        fileActions.innerHTML = `<button class="file-btn" style="background: #f44336;">Error: ${data.error}</button>`;
        progressBar.style.background = '#f44336';
    } else {
        fileActions.innerHTML = `
            <button class="file-btn" onclick="downloadFile('${data.file_path}')">Download</button>
            <button class="file-btn" onclick="deleteFile('${data.file_path}')">Delete</button>
        `;
        progressBar.style.width = '100%';
        progressBar.style.background = '#4CAF50';
        
        // Show image preview if it's an image
        if (data.file_type && data.file_type.startsWith('image/')) {
            const fileInfo = messageDiv.querySelector('.file-info');
            const img = document.createElement('img');
            img.src = data.file_path;
            img.className = 'image-preview';
            img.alt = data.file_name;
            fileInfo.appendChild(img);
        }
    }
}

async function sendImageForAnalysis(filePath, fileName) {
    try {
        const response = await fetch('/api/analyze-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_path: filePath,
                file_name: fileName
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            addMessage(data.analysis, 'ai');
        } else {
            addMessage('Sorry, I couldn\'t analyze the image. ' + data.error, 'ai');
        }
    } catch (error) {
        console.error('Image analysis error:', error);
        addMessage('Sorry, I couldn\'t analyze the image due to a technical error.', 'ai');
    }
}

function downloadFile(filePath) {
    const link = document.createElement('a');
    link.href = filePath;
    link.download = filePath.split('/').pop();
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

async function deleteFile(filePath) {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
        const response = await fetch('/api/delete-file', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ file_path: filePath }),
            credentials: 'include'
        });
        
            const data = await response.json();
        
            if (data.success) {
            // Remove the message from chat
            const messages = document.querySelectorAll('.message');
            for (const message of messages) {
                if (message.querySelector(`[onclick*="${filePath}"]`)) {
                    message.remove();
                    break;
                }
            }
        } else {
            alert('Error deleting file: ' + data.error);
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Error deleting file');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Update attached files display
function updateAttachedFilesDisplay() {
    const attachedFilesContainer = document.getElementById('attachedFilesContainer');
    if (!attachedFilesContainer) return;
    
    if (attachedFiles.length === 0) {
        attachedFilesContainer.style.display = 'none';
        return;
    }
    
    attachedFilesContainer.style.display = 'block';
    let html = '<div class="attached-files-preview">';
    
    attachedFiles.forEach((file, index) => {
        if (file.type && file.type.startsWith('image/')) {
            html += `
                <div class="attached-file-preview">
                    <img src="${file.url}" alt="${file.name}" class="preview-image">
                    <div class="file-info">
                        <span class="file-name">${file.name}</span>
                        <button class="remove-btn" onclick="removeAttachedFile(${index})">×</button>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="attached-file-preview">
                    <div class="file-icon">📁</div>
                    <div class="file-info">
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">${formatFileSize(file.size)}</span>
                        <button class="remove-btn" onclick="removeAttachedFile(${index})">×</button>
                    </div>
                </div>
            `;
        }
    });
    
    html += '</div>';
    attachedFilesContainer.innerHTML = html;
}

// Remove attached file
function removeAttachedFile(index) {
    attachedFiles.splice(index, 1);
    updateAttachedFilesDisplay();
}



// Message editing functions
async function editMessage(messageId) {
    if (!messageId) {
        console.error('No message ID provided for editing');
        return;
    }
    
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) {
        console.error('Message element not found');
        return;
    }
    
    const messageTextDiv = messageDiv.querySelector('.message-text');
    const originalText = messageTextDiv.textContent || messageTextDiv.innerText;
    
    // Create edit input
    const editInput = document.createElement('textarea');
    editInput.className = 'edit-input';
    editInput.value = originalText;
    editInput.rows = Math.max(3, originalText.split('\n').length);
    
    // Create edit actions
    const editActions = document.createElement('div');
    editActions.className = 'edit-actions';
    editActions.innerHTML = `
        <button class="edit-btn" onclick="saveMessageEdit('${messageId}')">Save</button>
        <button class="cancel-btn" onclick="cancelMessageEdit('${messageId}')">Cancel</button>
    `;
    
    // Replace content with edit form
    messageTextDiv.innerHTML = '';
    messageTextDiv.appendChild(editInput);
    messageTextDiv.appendChild(editActions);
    
    // Add edit mode class
    messageDiv.classList.add('edit-mode');
    
    // Focus on input
    editInput.focus();
    editInput.select();
}

async function saveMessageEdit(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) return;
    
    const editInput = messageDiv.querySelector('.edit-input');
    const newContent = editInput.value.trim();
    
    if (!newContent) {
        alert('Message cannot be empty');
        return;
    }
    
    try {
        const response = await fetch('/api/message/edit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId,
                new_content: newContent
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update message display
            const messageTextDiv = messageDiv.querySelector('.message-text');
            messageTextDiv.innerHTML = formatMessage(newContent);
            messageDiv.classList.remove('edit-mode');
            messageDiv.classList.add('edited');
            
            // Show success indicator
            showStatusMessage('Message edited successfully', 'success');
        } else {
            alert('Error editing message: ' + data.error);
        }
    } catch (error) {
        console.error('Error editing message:', error);
        alert('Error editing message');
    }
}

function cancelMessageEdit(messageId) {
    const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
    if (!messageDiv) return;
    
    // Reload the message from history to restore original content
    loadConversationHistory();
    messageDiv.classList.remove('edit-mode');
}

async function deleteMessage(messageId) {
    if (!messageId) {
        console.error('No message ID provided for deletion');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/message/delete', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message_id: messageId
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Remove message from DOM
            const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
            if (messageDiv) {
                messageDiv.remove();
            }
            
            showStatusMessage('Message deleted successfully', 'success');
        } else {
            alert('Error deleting message: ' + data.error);
        }
    } catch (error) {
        console.error('Error deleting message:', error);
        alert('Error deleting message');
    }
}

function showStatusMessage(message, type = 'info') {
    const statusDiv = document.createElement('div');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    
    document.body.appendChild(statusDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (statusDiv.parentNode) {
            statusDiv.parentNode.removeChild(statusDiv);
        }
    }, 3000);
} 

// Switch model function
async function switchModel(modelName) {
    try {
        // Show loading state
        const modelItem = document.querySelector(`[data-model="${modelName}"]`);
        if (modelItem) {
            modelItem.style.opacity = '0.6';
            modelItem.style.pointerEvents = 'none';
        }
        
        const response = await fetch('/api/model/switch', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify({ model_name: modelName })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatusMessage(`✅ Switched to ${modelName}`, 'success');
            // Close current modal and reopen with fresh data
            closeModal('modelStatusModal');
            // Force refresh by clearing any cached data
            setTimeout(() => {
                showModelStatus();
            }, 200);
        } else {
            showStatusMessage(`❌ Failed to switch to ${modelName}: ${data.error}`, 'error');
            // Restore model item if failed
            if (modelItem) {
                modelItem.style.opacity = '1';
                modelItem.style.pointerEvents = 'auto';
            }
        }
    } catch (error) {
        console.error('Error switching model:', error);
        showStatusMessage('❌ Error switching model', 'error');
        // Restore model item if error
        const modelItem = document.querySelector(`[data-model="${modelName}"]`);
        if (modelItem) {
            modelItem.style.opacity = '1';
            modelItem.style.pointerEvents = 'auto';
        }
    }
} 

async function startLoginGreeting() {
    try {
        const response = await fetch('/api/login-greeting', {
            method: 'POST',
            credentials: 'include'
        });
        if (!response.ok) return;
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
                        console.log('Error parsing greeting stream:', e);
                    }
                }
            }
        }
    } catch (error) {
        console.error('Error in login greeting:', error);
    }
}

// Terminal functionality
let terminalWebSocket = null;
let terminalOutput = null;

function initializeTerminal() {
    terminalOutput = document.getElementById('terminalOutput');
    
    // Connect to WebSocket
    connectTerminalWebSocket();
    
    // Add terminal controls
    document.querySelector('.terminal-header').addEventListener('click', function(e) {
        if (!e.target.classList.contains('terminal-btn')) {
            toggleTerminal();
        }
    });
}

function connectTerminalWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/logs`;
    
    terminalWebSocket = new WebSocket(wsUrl);
    
    terminalWebSocket.onopen = function() {
        console.log('WebSocket connected'); // Debug
    };
    
    terminalWebSocket.onmessage = function(event) {
        const logLine = event.data;
        console.log('WebSocket received:', logLine); // Debug
        addTerminalLine(logLine);
    };
    
    terminalWebSocket.onclose = function() {
        addTerminalLine('🔌 Disconnected from log stream', 'error');
        // Try to reconnect after 5 seconds
        setTimeout(connectTerminalWebSocket, 5000);
    };
    
    terminalWebSocket.onerror = function(error) {
        addTerminalLine('❌ WebSocket error: ' + error, 'error');
    };
}

function addTerminalLine(text, type = 'info') {
    if (!terminalOutput) return;
    
    const line = document.createElement('div');
    line.className = `terminal-line ${type}`;
    
    // Определяем тип сообщения по содержимому
    let displayType = type;
    if (text.includes('ERROR') || text.includes('❌')) {
        displayType = 'error';
    } else if (text.includes('WARNING') || text.includes('⚠️')) {
        displayType = 'warning';
    } else if (text.includes('INFO') || text.includes('✅') || text.includes('🔧') || text.includes('💾')) {
        displayType = 'info';
    } else if (text.includes('SUCCESS') || text.includes('✅')) {
        displayType = 'success';
    } else if (text.includes('🔌') || text.includes('📊')) {
        displayType = 'system';
    }
    
    line.className = `terminal-line ${displayType}`;
    line.textContent = text;
    
    terminalOutput.appendChild(line);
    
    // Auto-scroll to bottom
    const terminalWindow = terminalOutput.closest('.terminal-window');
    if (terminalWindow) {
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }
    
    // Limit number of lines to prevent memory issues
    const lines = terminalOutput.querySelectorAll('.terminal-line');
    if (lines.length > 1000) {
        lines[0].remove();
    }
}

function toggleTerminal() {
    const terminal = document.getElementById('terminalPanel');
    terminal.classList.toggle('expanded');
}

function clearTerminal() {
    if (terminalOutput) {
        terminalOutput.innerHTML = '';
        addTerminalLine('🗑️ Terminal cleared', 'system');
    }
}

function scrollTerminalToBottom() {
    const terminalWindow = document.querySelector('.terminal-window');
    if (terminalWindow) {
        terminalWindow.scrollTop = terminalWindow.scrollHeight;
    }
}

// Мобильное меню функции
function toggleMobileMenu() {
    const mobileMenu = document.getElementById('mobileMenu');
    if (mobileMenu) {
        mobileMenu.classList.toggle('active');
        console.log('Mobile menu toggled:', mobileMenu.classList.contains('active'));
    }
}

function showSystemAnalysisModal() {
    const modal = document.getElementById('systemAnalysisModal');
    if (modal) {
        modal.classList.add('active');
        console.log('System Analysis modal opened');
        
        // Загружаем System Analysis в модальное окно
        loadMobileSystemAnalysis();
    }
}

function closeSystemAnalysisModal() {
    const modal = document.getElementById('systemAnalysisModal');
    if (modal) {
        modal.classList.remove('active');
        console.log('System Analysis modal closed');
    }
}

// Улучшенный обработчик клика вне модального окна
document.addEventListener('click', function(event) {
    const modal = document.getElementById('systemAnalysisModal');
    const modalContent = document.querySelector('.system-analysis-modal-content');
    
    if (modal && modal.classList.contains('active')) {
        // Проверяем, что клик был вне модального окна
        if (event.target === modal || (modalContent && !modalContent.contains(event.target))) {
            console.log('Click outside modal detected, closing...');
            closeSystemAnalysisModal();
        }
    }
    
    // Обработчик для закрытия мобильного меню
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuContent = document.querySelector('.mobile-menu-content');
    
    if (mobileMenu && mobileMenu.classList.contains('active')) {
        // Проверяем, что клик был вне мобильного меню
        if (event.target === mobileMenu || (mobileMenuContent && !mobileMenuContent.contains(event.target))) {
            console.log('Click outside mobile menu detected, closing...');
            toggleMobileMenu();
        }
    }
});

// Добавляем обработчик для клавиши Escape
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('systemAnalysisModal');
        const mobileMenu = document.getElementById('mobileMenu');
        
        if (modal && modal.classList.contains('active')) {
            console.log('Escape key pressed, closing System Analysis modal');
            closeSystemAnalysisModal();
        }
        
        if (mobileMenu && mobileMenu.classList.contains('active')) {
            console.log('Escape key pressed, closing mobile menu');
            toggleMobileMenu();
        }
    }
});

// Проверка на мобильные устройства
function isMobileDevice() {
    return window.innerWidth <= 768;
}

async function loadMobileSystemAnalysis() {
    // Просто вызываем основную функцию - убираем дублирование
    await loadSystemAnalysis();
}

function updateMobileSystemPanel(analysis) {
    // Используем основную функцию - убираем дублирование
    updateSystemPanel(analysis);
}

function showMobileSystemError(message) {
    // Используем основную функцию - убираем дублирование
    showSystemError(message);
} 

// Инициализация обработчиков событий для кнопок System Analysis
function initializeSystemAnalysisButtons() {
    console.log('🔧 Initializing System Analysis buttons...');
    
    // Находим кнопки
    const refreshBtn = document.querySelector('.refresh-btn[onclick="loadSystemAnalysis()"]');
    const forceRefreshBtn = document.querySelector('.refresh-btn[onclick="forceRefreshSystemAnalysis()"]');
    
    if (refreshBtn) {
        console.log('✅ Found refresh button');
        refreshBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('🔄 Refresh button clicked');
            await loadSystemAnalysis();
        });
    }
    
    if (forceRefreshBtn) {
        console.log('✅ Found force refresh button');
        forceRefreshBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('⚡ Force refresh button clicked');
            await forceRefreshSystemAnalysis();
        });
    }
    
    console.log('✅ System Analysis buttons initialized');
} 