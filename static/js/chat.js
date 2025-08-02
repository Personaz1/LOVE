// ===== CHAT.JS - Modern Modular Architecture =====

// Global state
const ChatState = {
    messages: [],
    currentStreamingMessage: null,
    isStreaming: false,
    attachedFile: null,
    systemPanelVisible: true,
    terminalVisible: false
};

// DOM Elements
const Elements = {
    chatMessages: null,
    chatForm: null,
    chatInput: null,
    sendBtn: null,
    loadingIndicator: null,
    attachmentPreview: null,
    attachmentName: null,
    fileInput: null,
    systemPanel: null,
    terminalPanel: null,
    terminalWindow: null
};

// Initialize chat application
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    initializeEventListeners();
    loadInitialData();
});

// Initialize DOM elements
function initializeElements() {
    Elements.chatMessages = document.getElementById('chatMessages');
    Elements.chatForm = document.getElementById('chatForm');
    Elements.chatInput = document.getElementById('chatInput');
    Elements.sendBtn = document.getElementById('sendBtn');
    Elements.loadingIndicator = document.getElementById('loadingIndicator');
    Elements.attachmentPreview = document.getElementById('attachmentPreview');
    Elements.attachmentName = document.getElementById('attachmentName');
    Elements.fileInput = document.getElementById('fileInput');
    Elements.systemPanel = document.getElementById('systemPanel');
    Elements.terminalPanel = document.getElementById('terminalPanel');
    Elements.terminalWindow = document.getElementById('terminalWindow');
}

// Initialize event listeners
function initializeEventListeners() {
    // Chat form submission
    Elements.chatForm.addEventListener('submit', handleChatSubmit);
    
    // Input auto-resize
    Elements.chatInput.addEventListener('input', autoResizeInput);
    
    // Enter key handling
    Elements.chatInput.addEventListener('keydown', handleKeyDown);
    
    // File input change
    Elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Drag and drop
    setupDragAndDrop();
}

// Load initial data
async function loadInitialData() {
    try {
        // Load everything in parallel
        await Promise.all([
            loadConversationHistory(),
            loadSystemAnalysis(),
            loadModelStatus()
        ]);
        
        hideLoadingIndicator();
        Elements.chatInput.focus();
        
    } catch (error) {
        console.error('Error loading initial data:', error);
        hideLoadingIndicator();
        showErrorMessage('Failed to load initial data');
    }
}

// ===== CHAT FUNCTIONALITY =====

// Handle chat form submission
async function handleChatSubmit(event) {
    event.preventDefault();
    
    const message = Elements.chatInput.value.trim();
    if (!message && !ChatState.attachedFile) return;
    
    // Add user message
    addMessage('user', message, ChatState.attachedFile);
    Elements.chatInput.value = '';
    clearAttachment();
    autoResizeInput();
    
    // Start streaming response
    await streamResponse(message);
}

// Stream response from AI
async function streamResponse(userMessage) {
    try {
        ChatState.isStreaming = true;
        updateSendButton();
        
        // Create assistant message placeholder
        const assistantMessage = addMessage('assistant', '', null, true);
        
        // Start streaming
        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                message: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let content = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            content += chunk;
            
            // Update message content
            updateMessageContent(assistantMessage, content);
        }
        
        // Finalize message
        finalizeMessage(assistantMessage);
        
    } catch (error) {
        console.error('Streaming error:', error);
        showErrorMessage('Failed to get response from AI');
    } finally {
        ChatState.isStreaming = false;
        updateSendButton();
    }
}

// Add message to chat
function addMessage(role, content, attachment = null, isStreaming = false) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${role}`;
    if (isStreaming) messageElement.classList.add('streaming');
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageElement.innerHTML = `
        <div class="message-avatar">${getAvatar(role)}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${getSenderName(role)}</span>
                <span class="message-time">${timestamp}</span>
            </div>
            <div class="message-text">${formatMessageContent(content, attachment)}</div>
        </div>
    `;
    
    Elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
    
    if (isStreaming) {
        ChatState.currentStreamingMessage = messageElement;
    }
    
    return messageElement;
}

// Update streaming message content
function updateMessageContent(messageElement, content) {
    const textElement = messageElement.querySelector('.message-text');
    if (textElement) {
        textElement.innerHTML = formatMessageContent(content);
    }
}

// Finalize streaming message
function finalizeMessage(messageElement) {
    messageElement.classList.remove('streaming');
    ChatState.currentStreamingMessage = null;
}

// Format message content with rich text
function formatMessageContent(content, attachment = null) {
    let formatted = content;
    
    // Handle markdown-like formatting
    formatted = formatted
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\n/g, '<br>');
    
    // Add attachment if present
    if (attachment) {
        formatted += `<div class="attachment">📎 ${attachment.name}</div>`;
    }
    
    return formatted;
}

// Get avatar for message
function getAvatar(role) {
    switch (role) {
        case 'user': return '👤';
        case 'assistant': return '🤖';
        case 'system': return '⚙️';
        default: return '💬';
    }
}

// Get sender name
function getSenderName(role) {
    switch (role) {
        case 'user': return 'You';
        case 'assistant': return 'ΔΣ Guardian';
        case 'system': return 'System';
        default: return 'Unknown';
    }
}

// ===== INPUT HANDLING =====

// Auto-resize input
function autoResizeInput() {
    const input = Elements.chatInput;
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 120) + 'px';
}

// Handle key down events
function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        Elements.chatForm.dispatchEvent(new Event('submit'));
    }
}

// Update send button state
function updateSendButton() {
    const btn = Elements.sendBtn;
    if (ChatState.isStreaming) {
        btn.disabled = true;
        btn.innerHTML = '<span class="loading-spinner"></span>';
    } else {
        btn.disabled = false;
        btn.innerHTML = '<span class="send-icon">↩️</span>';
    }
}

// ===== FILE HANDLING =====

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        setAttachment(file);
    }
}

// Set attachment
function setAttachment(file) {
    ChatState.attachedFile = file;
    Elements.attachmentName.textContent = file.name;
    Elements.attachmentPreview.style.display = 'block';
}

// Clear attachment
function clearAttachment() {
    ChatState.attachedFile = null;
    Elements.attachmentPreview.style.display = 'none';
    Elements.fileInput.value = '';
}

// Remove attachment
function removeAttachment() {
    clearAttachment();
}

// Attach file (trigger file input)
function attachFile() {
    Elements.fileInput.click();
}

// Setup drag and drop
function setupDragAndDrop() {
    const dropZone = Elements.chatMessages;
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            setAttachment(files[0]);
        }
    });
}

// ===== SYSTEM PANEL =====

// Load system analysis
async function loadSystemAnalysis() {
    try {
        const response = await fetch('/api/system-analysis');
        const data = await response.json();
        
        if (data.success) {
            updateSystemPanel(data.analysis);
        }
    } catch (error) {
        console.error('Error loading system analysis:', error);
    }
}

// Update system panel
function updateSystemPanel(analysis) {
    const statusContent = document.getElementById('systemStatusContent');
    const tipsContent = document.getElementById('systemTipsContent');
    const logsContent = document.getElementById('systemLogsContent');
    
    if (statusContent) {
        statusContent.innerHTML = `
            <div class="system-status-item">
                <strong>Status:</strong> ${analysis.system_status || 'System operational'}
            </div>
        `;
    }
    
    if (tipsContent && analysis.tips) {
        tipsContent.innerHTML = `
            <ul class="tips-list">
                ${analysis.tips.map(tip => `<li>${tip}</li>`).join('')}
            </ul>
        `;
    }
    
    if (logsContent) {
        logsContent.innerHTML = `
            <div class="system-logs">
                <p>Recent activity loaded</p>
            </div>
        `;
    }
}

// Refresh system analysis
function refreshSystemAnalysis() {
    loadSystemAnalysis();
}

// Force refresh system analysis
function forceRefreshSystemAnalysis() {
    fetch('/api/system-analysis/clear-cache', { method: 'POST' })
        .then(() => loadSystemAnalysis());
}

// Toggle system panel
function toggleSystemPanel() {
    if (window.mobileUtils && window.mobileUtils.isMobileDevice()) {
        // On mobile, show modal
        showSystemAnalysisModal();
    } else {
        // On desktop, toggle visibility
        ChatState.systemPanelVisible = !ChatState.systemPanelVisible;
        Elements.systemPanel.style.display = ChatState.systemPanelVisible ? 'flex' : 'none';
    }
}

// ===== TERMINAL =====

// Toggle terminal
function toggleTerminal() {
    ChatState.terminalVisible = !ChatState.terminalVisible;
    Elements.terminalPanel.classList.toggle('expanded', ChatState.terminalVisible);
}

// Clear terminal
function clearTerminal() {
    if (Elements.terminalWindow) {
        Elements.terminalWindow.innerHTML = '';
    }
}

// Add terminal line
function addTerminalLine(text, type = 'info') {
    if (Elements.terminalWindow) {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
        Elements.terminalWindow.appendChild(line);
        Elements.terminalWindow.scrollTop = Elements.terminalWindow.scrollHeight;
    }
}

// ===== UTILITIES =====

// Scroll to bottom
function scrollToBottom() {
    Elements.chatMessages.scrollTop = Elements.chatMessages.scrollHeight;
}

// Show loading indicator
function showLoadingIndicator() {
    if (Elements.loadingIndicator) {
        Elements.loadingIndicator.style.display = 'flex';
    }
}

// Hide loading indicator
function hideLoadingIndicator() {
    if (Elements.loadingIndicator) {
        Elements.loadingIndicator.style.display = 'none';
    }
}

// Show error message
function showErrorMessage(message) {
    addMessage('system', `❌ ${message}`);
}

// Load conversation history
async function loadConversationHistory() {
    try {
        const response = await fetch('/api/conversation-history?limit=20');
        const data = await response.json();
        
        if (data.success && data.messages) {
            // Clear existing messages
            Elements.chatMessages.innerHTML = '';
            
            // Add historical messages
            data.messages.forEach(msg => {
                addMessage(msg.sender, msg.message);
            });
        }
    } catch (error) {
        console.error('Error loading conversation history:', error);
    }
}

// Load model status
async function loadModelStatus() {
    try {
        const response = await fetch('/api/model-status');
        const data = await response.json();
        
        if (data.success) {
            const currentModel = document.getElementById('currentModel');
            if (currentModel) {
                currentModel.textContent = data.current_model || 'Unknown';
            }
        }
    } catch (error) {
        console.error('Error loading model status:', error);
    }
}

// Clear conversation
function clearConversation() {
    if (confirm('Are you sure you want to clear the conversation?')) {
        fetch('/api/conversation-clear', { method: 'POST' })
            .then(() => {
                Elements.chatMessages.innerHTML = '';
                addMessage('system', 'Conversation cleared');
            })
            .catch(error => {
                console.error('Error clearing conversation:', error);
                showErrorMessage('Failed to clear conversation');
            });
    }
}

// Export chat
function exportChat() {
    const messages = Array.from(Elements.chatMessages.querySelectorAll('.message'))
        .map(msg => {
            const sender = msg.querySelector('.message-sender')?.textContent || 'Unknown';
            const content = msg.querySelector('.message-text')?.textContent || '';
            return `[${sender}]: ${content}`;
        })
        .join('\n\n');
    
    const blob = new Blob([messages], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chat-export-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
}

// Demo reasoning
function demoReasoning() {
    addMessage('system', '🧠 Demo reasoning mode activated');
    // Add demo message
    addMessage('assistant', '🤖 **THOUGHT PROCESS:**\nI am analyzing the user\'s request and considering the best approach...\n\n💬 **FINAL RESPONSE:**\nThis is a demo of the reasoning process.');
}

// Show model status
function showModelStatus() {
    window.location.href = '/models';
}

// ===== GLOBAL FUNCTIONS =====

// Make functions globally available
window.clearConversation = clearConversation;
window.exportChat = exportChat;
window.demoReasoning = demoReasoning;
window.showModelStatus = showModelStatus;
window.attachFile = attachFile;
window.removeAttachment = removeAttachment;
window.toggleSystemPanel = toggleSystemPanel;
window.refreshSystemAnalysis = refreshSystemAnalysis;
window.forceRefreshSystemAnalysis = forceRefreshSystemAnalysis;
window.toggleTerminal = toggleTerminal;
window.clearTerminal = clearTerminal; 