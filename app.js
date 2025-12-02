// AI Tutor - Production Web App
class AITutorApp {
    constructor() {
        this.API_BASE = 'http://localhost:8000/api/v1';
        this.currentChatId = null;
        this.isLoading = false;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }

    async init() {
        this.bindEvents();
        await this.loadInitialData();
        this.setupKeyboardShortcuts();
        this.checkBackendConnection();
    }

    bindEvents() {
        // New Chat
        document.getElementById('newChatBtn')?.addEventListener('click', () => this.createNewChat());
        
        // Send Message
        document.getElementById('sendBtn')?.addEventListener('click', () => this.sendMessage());
        
        // Input handling
        const input = document.getElementById('messageInput');
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
            
            input.addEventListener('input', () => this.updateSendButton());
        }

        // Example prompts
        document.querySelectorAll('.prompt-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const prompt = btn.getAttribute('data-prompt');
                if (prompt && input) {
                    input.value = prompt;
                    this.updateSendButton();
                    this.sendMessage();
                }
            });
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter = Send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                this.sendMessage();
            }
            
            // Escape = Clear input
            if (e.key === 'Escape') {
                const input = document.getElementById('messageInput');
                if (input && input.value) {
                    input.value = '';
                    this.updateSendButton();
                }
            }
        });
    }

    async loadInitialData() {
        this.showStatus('Connecting to AI Tutor...', 'info');
        
        try {
            await this.loadChatHistory();
            await this.checkDocumentStatus();
            this.showStatus('AI Tutor ready!', 'success');
            setTimeout(() => this.hideStatus(), 2000);
        } catch (error) {
            this.showStatus('Connection failed. Check if backend is running.', 'error');
            console.error('Failed to load initial data:', error);
        }
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.API_BASE.replace('/api/v1', '')}/health`);
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Backend connected:', data);
                return true;
            }
        } catch (error) {
            console.error('❌ Backend connection failed:', error);
            this.showStatus('Backend not available. Please start the server.', 'error');
            return false;
        }
    }

    async createNewChat() {
        if (this.isLoading) return;

        this.setLoading(true);
        this.showStatus('Creating new chat...', 'info');

        try {
            const response = await fetch(`${this.API_BASE}/chat/new`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: 'New Chat' })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.currentChatId = data.session_id;
            
            // Clear UI and show chat interface
            this.clearMessages();
            this.showChatInterface();
            this.updateChatTitle('New Chat');
            
            // Refresh chat list
            await this.loadChatHistory();
            
            // Focus input
            document.getElementById('messageInput')?.focus();
            
            this.showStatus('New chat created!', 'success');
            setTimeout(() => this.hideStatus(), 2000);

        } catch (error) {
            console.error('Error creating chat:', error);
            this.showStatus(`Failed to create chat: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async loadChatHistory() {
        try {
            const response = await fetch(`${this.API_BASE}/chat/list`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const chats = await response.json();
            this.renderChatHistory(chats);

        } catch (error) {
            console.error('Error loading chat history:', error);
            const historyEl = document.getElementById('chatHistory');
            if (historyEl) {
                historyEl.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load chats</p>
                        <button class="retry-btn" onclick="app.loadChatHistory()">Retry</button>
                    </div>
                `;
            }
        }
    }

    renderChatHistory(chats) {
        const historyEl = document.getElementById('chatHistory');
        if (!historyEl) return;

        if (!chats || chats.length === 0) {
            historyEl.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>No chats yet</p>
                    <small>Start a conversation!</small>
                </div>
            `;
            return;
        }

        const chatItems = chats.map(chat => {
            const isActive = chat.session_id === this.currentChatId;
            const snippet = chat.last_message_snippet || 'No messages yet';
            const date = new Date(chat.updated_at).toLocaleDateString();
            
            return `
                <div class="chat-item ${isActive ? 'active' : ''}" data-chat-id="${chat.session_id}">
                    <div class="chat-content" onclick="app.loadChat('${chat.session_id}')">
                        <div class="chat-title">${this.escapeHtml(chat.title)}</div>
                        <div class="chat-preview">${this.escapeHtml(snippet)}</div>
                        <div class="chat-date">${date}</div>
                    </div>
                    <div class="chat-actions">
                        <button class="action-btn" onclick="app.renameChat('${chat.session_id}', '${this.escapeHtml(chat.title)}')" title="Rename">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="action-btn delete" onclick="app.deleteChat('${chat.session_id}')" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        historyEl.innerHTML = chatItems;
    }

    async loadChat(chatId) {
        if (this.isLoading) return;

        this.setLoading(true);
        this.showStatus('Loading chat...', 'info');

        try {
            const response = await fetch(`${this.API_BASE}/chat/${chatId}`);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            this.currentChatId = chatId;
            
            this.updateChatTitle(data.session.title);
            this.renderMessages(data.messages);
            this.showChatInterface();
            this.updateActiveChatInSidebar(chatId);
            
            this.showStatus('Chat loaded!', 'success');
            setTimeout(() => this.hideStatus(), 1000);

        } catch (error) {
            console.error('Error loading chat:', error);
            this.showStatus(`Failed to load chat: ${error.message}`, 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input?.value.trim();
        
        if (!message || this.isLoading) return;

        // Create new chat if needed
        if (!this.currentChatId) {
            await this.createNewChat();
            if (!this.currentChatId) return;
        }

        this.setLoading(true);
        input.value = '';
        this.updateSendButton();

        // Add user message to UI
        this.addMessage(message, 'user');
        this.showTypingIndicator();

        try {
            const response = await fetch(`${this.API_BASE}/chat/${this.currentChatId}/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    question: message,
                    top_k: 5
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            
            this.hideTypingIndicator();
            this.addMessage(data.answer, 'assistant', {
                sources: data.sources || [],
                confidence: data.confidence_score || 0,
                followUp: data.follow_up
            });

            // Update chat history
            await this.loadChatHistory();

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage(`Sorry, I encountered an error: ${error.message}`, 'assistant', { isError: true });
        } finally {
            this.setLoading(false);
        }
    }

    addMessage(content, role, options = {}) {
        const messagesEl = document.getElementById('chatMessages');
        if (!messagesEl) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role} ${options.isError ? 'error' : ''}`;
        
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        let messageHTML = `
            <div class="message-avatar">
                <i class="fas fa-${role === 'user' ? 'user' : 'robot'}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${role === 'assistant' && !options.isError ? this.formatMarkdown(content) : this.escapeHtml(content)}</div>
                <div class="message-meta">
                    <span class="message-time">${time}</span>
        `;

        if (role === 'assistant' && !options.isError) {
            if (options.confidence) {
                messageHTML += `<span class="confidence">Confidence: ${Math.round(options.confidence * 100)}%</span>`;
            }
            
            if (options.sources && options.sources.length > 0) {
                messageHTML += `
                    <div class="sources">
                        <span class="sources-label">Sources:</span>
                        ${options.sources.map(source => `<span class="source-tag">${this.escapeHtml(source)}</span>`).join('')}
                    </div>
                `;
            }
        }

        messageHTML += `
                </div>
            </div>
        `;

        messageDiv.innerHTML = messageHTML;
        messagesEl.appendChild(messageDiv);
        
        this.scrollToBottom();
    }

    renderMessages(messages) {
        const messagesEl = document.getElementById('chatMessages');
        if (!messagesEl) return;

        messagesEl.innerHTML = '';
        
        messages.forEach(message => {
            this.addMessage(message.text, message.role, {
                timestamp: message.created_at
            });
        });
    }

    showChatInterface() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatMessages = document.getElementById('chatMessages');
        
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        if (chatMessages) chatMessages.classList.add('active');
    }

    clearMessages() {
        const messagesEl = document.getElementById('chatMessages');
        if (messagesEl) {
            messagesEl.innerHTML = '';
            messagesEl.classList.add('active');
        }
    }

    updateChatTitle(title) {
        const titleEl = document.getElementById('currentChatTitle');
        if (titleEl) titleEl.textContent = title;
    }

    updateActiveChatInSidebar(chatId) {
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.toggle('active', item.dataset.chatId === chatId);
        });
    }

    showTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.classList.add('active');
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.classList.remove('active');
    }

    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        const newChatBtn = document.getElementById('newChatBtn');
        
        if (sendBtn) sendBtn.disabled = loading;
        if (newChatBtn) newChatBtn.disabled = loading;
        
        if (loading) {
            document.body.classList.add('loading');
        } else {
            document.body.classList.remove('loading');
        }
    }

    updateSendButton() {
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        if (sendBtn && input) {
            sendBtn.disabled = !input.value.trim() || this.isLoading;
        }
    }

    scrollToBottom() {
        const messagesEl = document.getElementById('chatMessages');
        if (messagesEl) {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }
    }

    showStatus(message, type = 'info') {
        // Create or update status notification
        let statusEl = document.getElementById('statusNotification');
        
        if (!statusEl) {
            statusEl = document.createElement('div');
            statusEl.id = 'statusNotification';
            statusEl.className = 'status-notification';
            document.body.appendChild(statusEl);
        }
        
        statusEl.textContent = message;
        statusEl.className = `status-notification ${type} active`;
    }

    hideStatus() {
        const statusEl = document.getElementById('statusNotification');
        if (statusEl) {
            statusEl.classList.remove('active');
        }
    }

    async checkDocumentStatus() {
        try {
            const response = await fetch(`${this.API_BASE.replace('/api/v1', '')}/health`);
            if (response.ok) {
                const data = await response.json();
                const docCountEl = document.getElementById('docCount');
                if (docCountEl) {
                    const isConnected = data.components?.qdrant === 'connected';
                    docCountEl.textContent = isConnected ? '3 documents loaded' : 'Documents unavailable';
                }
            }
        } catch (error) {
            console.error('Error checking document status:', error);
        }
    }

    // Utility functions
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatMarkdown(text) {
        // Simple markdown formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    // Chat management functions
    async renameChat(chatId, currentTitle) {
        const newTitle = prompt('Enter new chat title:', currentTitle);
        if (!newTitle || newTitle === currentTitle) return;

        try {
            const response = await fetch(`${this.API_BASE}/chat/${chatId}/rename`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle })
            });

            if (response.ok) {
                await this.loadChatHistory();
                if (chatId === this.currentChatId) {
                    this.updateChatTitle(newTitle);
                }
                this.showStatus('Chat renamed successfully!', 'success');
            }
        } catch (error) {
            this.showStatus('Failed to rename chat', 'error');
        }
    }

    async deleteChat(chatId) {
        if (!confirm('Are you sure you want to delete this chat?')) return;

        try {
            const response = await fetch(`${this.API_BASE}/chat/${chatId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                if (chatId === this.currentChatId) {
                    this.currentChatId = null;
                    this.clearMessages();
                    document.getElementById('welcomeScreen').style.display = 'block';
                }
                await this.loadChatHistory();
                this.showStatus('Chat deleted successfully!', 'success');
            }
        } catch (error) {
            this.showStatus('Failed to delete chat', 'error');
        }
    }
}

// Initialize the app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new AITutorApp();
});

// Export for use in HTML onclick handlers
window.app = app;