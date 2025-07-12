// Global variables
let isUploading = false;
let isAsking = false;

// DOM elements
const fileInput = document.getElementById('file-input');
const uploadProgress = document.getElementById('upload-progress');
const chatMessages = document.getElementById('chat-messages');
const questionInput = document.getElementById('question-input');
const askButton = document.getElementById('ask-button');
const pdfStatus = document.getElementById('pdf-status');

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    setupFileUpload();
    setupChatInput();
    scrollToBottom();
});

// File upload setup
function setupFileUpload() {
    // File input change event
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

// Chat input setup
function setupChatInput() {
    // Enter key event
    questionInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            askQuestion();
        }
    });
}

// Handle file upload
async function handleFileUpload(file) {
    if (isUploading) return;
    
    isUploading = true;
    showUploadProgress();
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert(result.message, 'success');
            updatePdfStatus(result.filename, true);
            enableChatInput();
            
            // Clear any existing chat
            const emptyChat = chatMessages.querySelector('.empty-chat');
            if (emptyChat) {
                emptyChat.remove();
            }
        } else {
            showAlert(result.error || 'Upload failed', 'danger');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showAlert('Network error occurred during upload', 'danger');
    } finally {
        isUploading = false;
        hideUploadProgress();
    }
}

// Ask question
async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question || isAsking) return;
    
    isAsking = true;
    questionInput.disabled = true;
    askButton.disabled = true;
    
    // Add user message to chat
    addMessage('user', question);
    questionInput.value = '';
    
    // Add loading message
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const result = await response.json();
        
        // Remove loading message
        removeLoadingMessage(loadingId);
        
        if (result.success) {
            addMessage('assistant', result.answer);
        } else {
            showAlert(result.error || 'Failed to get answer', 'danger');
            addMessage('assistant', 'Sorry, I encountered an error while processing your question.');
        }
    } catch (error) {
        console.error('Question error:', error);
        removeLoadingMessage(loadingId);
        showAlert('Network error occurred', 'danger');
        addMessage('assistant', 'Sorry, I encountered a network error. Please try again.');
    } finally {
        isAsking = false;
        questionInput.disabled = false;
        askButton.disabled = false;
        questionInput.focus();
    }
}

// Add message to chat
function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const icon = role === 'user' ? 'bi-person-circle' : 'bi-robot';
    const label = role === 'user' ? 'You' : 'Assistant';
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <i class="bi ${icon}"></i> ${label}
            </div>
            <div class="message-text">${escapeHtml(content)}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Add loading message
function addLoadingMessage() {
    const loadingId = 'loading-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';
    messageDiv.id = loadingId;
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <i class="bi bi-robot"></i> Assistant
            </div>
            <div class="message-text loading-message">
                <span>Thinking</span>
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    return loadingId;
}

// Remove loading message
function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

// Clear chat
async function clearChat() {
    try {
        const response = await fetch('/clear', {
            method: 'POST'
        });
        
        if (response.ok) {
            chatMessages.innerHTML = `
                <div class="empty-chat">
                    <i class="bi bi-chat display-4 text-muted"></i>
                    <p class="text-muted mt-3">Upload a PDF and start asking questions!</p>
                </div>
            `;
            showAlert('Chat history cleared', 'info');
        }
    } catch (error) {
        console.error('Clear chat error:', error);
        showAlert('Failed to clear chat', 'danger');
    }
}

// Reset session
async function resetSession() {
    if (confirm('This will clear all data and reset the session. Continue?')) {
        try {
            const response = await fetch('/reset', {
                method: 'POST'
            });
            
            if (response.ok) {
                location.reload();
            }
        } catch (error) {
            console.error('Reset session error:', error);
            showAlert('Failed to reset session', 'danger');
        }
    }
}

// Utility functions
function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert-dismissible');
    existingAlerts.forEach(alert => alert.remove());
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of main content
    const mainContent = document.querySelector('.main-content');
    const firstChild = mainContent.querySelector('.d-flex');
    mainContent.insertBefore(alertDiv, firstChild.nextSibling);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showUploadProgress() {
    uploadProgress.style.display = 'block';
}

function hideUploadProgress() {
    uploadProgress.style.display = 'none';
}

function updatePdfStatus(filename, processed) {
    if (processed) {
        pdfStatus.innerHTML = `
            <div class="text-success">
                <i class="bi bi-check-circle"></i> ${filename} loaded
            </div>
        `;
    } else {
        pdfStatus.innerHTML = `
            <div class="text-warning">
                <i class="bi bi-exclamation-circle"></i> No PDF uploaded
            </div>
        `;
    }
}

function enableChatInput() {
    questionInput.disabled = false;
    askButton.disabled = false;
    questionInput.placeholder = "Ask a question about your PDF...";
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Mobile sidebar toggle (if needed)
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    sidebar.classList.toggle('show');
}
