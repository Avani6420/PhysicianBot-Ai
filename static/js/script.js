document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const messagesContainer = document.getElementById('messagesContainer');
    const typingIndicator = document.getElementById('typingIndicator');
    const clearChatBtn = document.getElementById('clearChatBtn');
    const mobileToggleBtn = document.getElementById('mobileToggleBtn');
    const sidebar = document.getElementById('sidebar');
    const promptChips = document.querySelectorAll('.prompt-chip');

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
    });

    // Enter key submits form (Shift+Enter for newline)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    // Mobile sidebar toggle
    if (mobileToggleBtn) {
        mobileToggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
    }

    // Quick prompt chips
    promptChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            if (query) {
                userInput.value = query;
                if (window.innerWidth <= 900) {
                    sidebar.classList.remove('open');
                }
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // Clear chat
    clearChatBtn.addEventListener('click', () => {
        const introMessage = messagesContainer.querySelector('.intro-message');
        messagesContainer.innerHTML = '';
        if (introMessage) {
            messagesContainer.appendChild(introMessage);
        }
    });

    // Handle form submit
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Append user message
        appendMessage('user', message);
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        // Show typing indicator & scroll
        typingIndicator.classList.add('active');
        scrollToBottom();

        try {
            const response = await fetch('/get', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ msg: message })
            });

            const data = await response.json();

            if (response.ok && data.answer) {
                appendMessage('bot', data.answer);
            } else {
                appendMessage('bot', `⚠️ Error: ${data.error || 'Failed to receive answer from medical assistant.'}`);
            }
        } catch (err) {
            appendMessage('bot', '⚠️ Connection error. Please verify the server is running.');
            console.error(err);
        } finally {
            typingIndicator.classList.remove('active');
            sendBtn.disabled = false;
            scrollToBottom();
            userInput.focus();
        }
    });

    function appendMessage(sender, text) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}-message`;

        const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        let avatarHtml = '';
        let headerHtml = '';

        if (sender === 'user') {
            avatarHtml = `<div class="msg-avatar"><i class="fa-solid fa-user"></i></div>`;
            headerHtml = `
                <div class="msg-header">
                    <span class="user-name">You</span>
                    <span class="msg-time">${timeString}</span>
                </div>
            `;
        } else {
            avatarHtml = `<div class="msg-avatar"><i class="fa-solid fa-user-doctor"></i></div>`;
            headerHtml = `
                <div class="msg-header">
                    <span class="bot-name">MediBot</span>
                    <span class="msg-time">${timeString}</span>
                </div>
            `;
        }

        // Format basic markdown (bold, lists, paragraphs)
        const formattedContent = formatMarkdown(text);

        msgDiv.innerHTML = `
            ${avatarHtml}
            <div class="msg-content">
                ${headerHtml}
                <div class="msg-text">${formattedContent}</div>
            </div>
        `;

        messagesContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function formatMarkdown(text) {
        let clean = escapeHtml(text);
        // Bold **text**
        clean = clean.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic *text*
        clean = clean.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Bullet points
        clean = clean.replace(/^[\*\-]\s+(.*)$/gm, '• $1');
        return clean;
    }

    function escapeHtml(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function scrollToBottom() {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});
