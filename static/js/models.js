// Models page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Load models on page load
    loadModels();
});

async function loadModels() {
    try {
        console.log('🔄 Loading models...');
        
        const response = await fetch('/api/model-status', {
            credentials: 'same-origin'
        });

        if (response.ok) {
            const data = await response.json();
            console.log('📊 Model status data:', data);
            
            if (data.success && data.status) {
                const status = data.status;
                console.log('🎯 Current model:', status.current_model);
                console.log('📈 Model index:', status.model_index);
                
                // Update current model section
                updateCurrentModel(status);
                
                // Update models grid
                updateModelsGrid(status);
                
                console.log('✅ Models loaded successfully');
            }
        } else {
            console.error('Failed to load model status');
            showStatusMessage('❌ Failed to load model status', 'error');
        }
    } catch (error) {
        console.error('Error loading models:', error);
        showStatusMessage('❌ Error loading models', 'error');
    }
}

function updateCurrentModel(status) {
    const currentModelInfo = document.getElementById('currentModelInfo');
    
    currentModelInfo.innerHTML = `
        <div class="current-model-title">${status.current_model}</div>
        <div class="current-model-info">
            Quota: ${status.current_quota} requests/day<br>
            Model ${status.model_index + 1} of ${status.total_models}<br>
            <span style="opacity: 0.8; font-size: 0.9rem;">🔄 Currently Active</span>
        </div>
    `;
}

function updateModelsGrid(status) {
    const modelsGrid = document.getElementById('modelsGrid');
    
    let modelsHtml = '';
    
    status.available_models.forEach((model, index) => {
        const isCurrent = index === status.model_index;
        const hasError = model.has_error;
        const statusClass = isCurrent ? 'current' : hasError ? 'error' : '';
        const clickable = !isCurrent ? 'clickable' : '';
        
        modelsHtml += `
            <div class="model-card ${statusClass} ${clickable}" 
                 data-model="${model.name}"
                 onclick="${!isCurrent ? `switchModel('${model.name}')` : ''}">
                <div class="model-name">${model.name}</div>
                <div class="model-quota">${model.quota} req/day</div>
                ${isCurrent ? '<div class="model-status status-current">🔄 Current</div>' : ''}
                ${hasError ? '<div class="model-status status-error">⚠️ Quota Exceeded</div>' : ''}
                ${!isCurrent ? '<div class="model-hint">Click to switch</div>' : ''}
            </div>
        `;
    });
    
    modelsGrid.innerHTML = modelsHtml;
    
    // Update error count in info section
    const errorCount = status.model_errors;
    const infoSection = document.querySelector('.models-info p:last-of-type');
    if (infoSection) {
        infoSection.innerHTML = `<strong>Error count:</strong> ${errorCount} models with quota issues`;
    }
}

async function switchModel(modelName) {
    try {
        console.log(`🔄 Switching to model: ${modelName}`);
        
        // Show loading state
        const modelCard = document.querySelector(`[data-model="${modelName}"]`);
        if (modelCard) {
            modelCard.classList.add('loading');
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
            showStatusMessage(`✅ Successfully switched to ${modelName}`, 'success');
            
            // Reload models to update the display
            setTimeout(() => {
                loadModels();
            }, 500);
        } else {
            showStatusMessage(`❌ Failed to switch to ${modelName}: ${data.error}`, 'error');
            
            // Restore model card if failed
            if (modelCard) {
                modelCard.classList.remove('loading');
            }
        }
    } catch (error) {
        console.error('Error switching model:', error);
        showStatusMessage('❌ Error switching model', 'error');
        
        // Restore model card if error
        const modelCard = document.querySelector(`[data-model="${modelName}"]`);
        if (modelCard) {
            modelCard.classList.remove('loading');
        }
    }
}

function showStatusMessage(message, type = 'info') {
    const statusMessages = document.getElementById('statusMessages');
    
    // Remove existing messages
    const existingMessages = statusMessages.querySelectorAll('.status-message');
    existingMessages.forEach(msg => msg.remove());
    
    // Create new message
    const messageElement = document.createElement('div');
    messageElement.className = `status-message status-${type}`;
    messageElement.textContent = message;
    
    statusMessages.appendChild(messageElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageElement.parentNode) {
            messageElement.remove();
        }
    }, 5000);
}

// Utility function for loading conversation archive (from chat.js)
async function loadConversationArchive() {
    try {
        const response = await fetch('/api/conversation-archive', {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Open in new window or redirect
                window.open('/chat', '_blank');
            }
        }
    } catch (error) {
        console.error('Error loading conversation archive:', error);
    }
} 
 