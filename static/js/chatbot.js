document.addEventListener('DOMContentLoaded', function() {
    
    // 1. ELEMEN SELEKTOR
    const chatbotButton = document.getElementById('chatbotButton');
    const chatPopup = document.getElementById('chatPopup');
    const chatClose = document.getElementById('chatClose');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const chatbotWrapper = document.getElementById('chatbot-wrapper');

    // Cek Login
    const isLoggedIn = chatbotWrapper ? JSON.parse(chatbotWrapper.getAttribute('data-user-logged-in')) : false;
    const loginUrl = chatbotWrapper ? chatbotWrapper.getAttribute('data-login-url') : '/login';

    // 2. TOGGLE CHATBOT
    if (chatbotButton) {
        chatbotButton.addEventListener('click', () => {
            if (!isLoggedIn) {
                window.location.href = loginUrl;
                return;
            }
            chatPopup.classList.add('active');
            setTimeout(() => chatInput.focus(), 300);
        });
    }

    if (chatClose) {
        chatClose.addEventListener('click', () => {
            chatPopup.classList.remove('active');
        });
    }

    // 3. FUNGSI RENDER PESAN
    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message-row user-row';
        div.innerHTML = `
            <div class="message-bubble user-bubble">
                <p>${text}</p>
                <span class="message-time">Kamu</span>
            </div>
        `;
        // Insert SEBELUM typing indicator
        if(typingIndicator && typingIndicator.parentNode === chatMessages) {
            chatMessages.insertBefore(div, typingIndicator);
        } else {
            chatMessages.appendChild(div);
        }
        scrollToBottom();
    }

    function appendBotMessage(text) {
        const div = document.createElement('div');
        div.className = 'message-row bot-row';
        div.innerHTML = `
            <div class="message-avatar">
                <img src="/static/images/cepot_avatar.png" onerror="this.src='https://cdn-icons-png.flaticon.com/512/4712/4712035.png'">
            </div>
            <div class="message-bubble bot-bubble">
                <p>${text}</p>
                <span class="message-time">Cepot AI</span>
            </div>
        `;
        
        if(typingIndicator && typingIndicator.parentNode === chatMessages) {
            chatMessages.insertBefore(div, typingIndicator);
        } else {
            chatMessages.appendChild(div);
        }
        scrollToBottom();
        playNotification();
    }

    function showTyping() {
        typingIndicator.style.display = 'block';
        scrollToBottom();
    }

    function hideTyping() {
        typingIndicator.style.display = 'none';
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function playNotification() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.frequency.setValueAtTime(600, ctx.currentTime);
            gain.gain.setValueAtTime(0.05, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.1);
            osc.start();
            osc.stop(ctx.currentTime + 0.1);
        } catch(e) {}
    }

    // 4. LOGIKA PENGIRIMAN
    async function handleSendMessage(textOverride) {
        const text = textOverride || chatInput.value.trim();
        if (!text) return;

        chatInput.value = '';
        appendUserMessage(text);
        showTyping();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            setTimeout(() => {
                hideTyping();
                const formatted = data.response.replace(/\n/g, '<br>');
                appendBotMessage(formatted);
            }, 800); // Delay buatan biar lebih natural

        } catch (error) {
            console.error(error);
            hideTyping();
            appendBotMessage("Maaf Jang, koneksi error. Coba lagi nanti ya.");
        }
    }

    // 5. EVENT LISTENERS
    if (sendButton) {
        sendButton.addEventListener('click', () => handleSendMessage());
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
    }

    // Handle Quick Replies (Pake Event Delegation)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('quick-btn')) {
            const text = e.target.getAttribute('data-text');
            handleSendMessage(text);
        }
    });

    document.addEventListener('DOMContentLoaded', function() {
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chat-window');
    const chatClose = document.getElementById('chat-close');
    const chatInput = document.getElementById('chat-input');
    const chatSend = document.getElementById('chat-send');
    const chatBody = document.getElementById('chat-body');
    const chatbotBadge = document.getElementById('chatbot-badge');

    // Buka/Tutup Jendela Chat
    chatbotToggle.addEventListener('click', function() {
        chatWindow.classList.toggle('active');
        // Sembunyikan badge saat chat dibuka
        if (chatWindow.classList.contains('active')) {
            chatbotBadge.style.display = 'none';
        }
    });

    chatClose.addEventListener('click', function() {
        chatWindow.classList.remove('active');
    });

    // Fungsi Kirim Pesan
    function sendMessage() {
        const message = chatInput.value.trim();
        if (message === '') return;

        // Tambahkan pesan pengguna
        appendMessage(message, 'user-message');
        chatInput.value = '';

        // Simulasi respons bot (Ganti dengan logika backend Anda nanti)
        setTimeout(() => {
            const botResponse = "Maaf, saat ini saya masih dalam pengembangan. Silakan coba lagi nanti!";
            appendMessage(botResponse, 'bot-message');
        }, 1000);
    }

    // Tambahkan Pesan ke Chat Body
    function appendMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        const messageText = document.createElement('p');
        messageText.textContent = message;
        messageDiv.appendChild(messageText);
        chatBody.appendChild(messageDiv);
        // Scroll ke bawah otomatis
        chatBody.scrollTop = chatBody.scrollHeight;
    }

    // Event Listener untuk Tombol Kirim dan Enter
    chatSend.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});

});