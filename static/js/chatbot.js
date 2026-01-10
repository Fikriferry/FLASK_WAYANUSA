document.addEventListener('DOMContentLoaded', function() {
    
    // ============================================================
    // 1. ELEMEN SELEKTOR (Sesuaikan dengan ID di HTML)
    // ============================================================
    const chatbotButton = document.getElementById('chatbotButton');
    const chatPopup = document.getElementById('chatPopup');
    const chatClose = document.getElementById('chatClose');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const typingIndicator = document.getElementById('typingIndicator');
    const chatbotWrapper = document.getElementById('chatbot-wrapper');
    
    // ELEMENT BARU: SWITCH MODE
    const modeToggle = document.getElementById('aiModeToggle');
    const statusText = document.getElementById('chatStatusText');

    // Cek Login (Dari atribut data HTML)
    const isLoggedIn = chatbotWrapper ? JSON.parse(chatbotWrapper.getAttribute('data-user-logged-in')) : false;
    const loginUrl = chatbotWrapper ? chatbotWrapper.getAttribute('data-login-url') : '/auth/login';

    // ============================================================
    // 2. TOGGLE BUKA/TUTUP CHAT
    // ============================================================
    if (chatbotButton) {
        chatbotButton.addEventListener('click', () => {
            if (!isLoggedIn) {
                // Arahkan ke login jika belum login
                window.location.href = loginUrl;
                return;
            }
            chatPopup.classList.add('active');
            // Fokus ke input otomatis saat dibuka
            setTimeout(() => chatInput.focus(), 300);
        });
    }

    if (chatClose) {
        chatClose.addEventListener('click', () => {
            chatPopup.classList.remove('active');
        });
    }

    // ============================================================
    // 3. LOGIKA SWITCH MODE (GEMINI VS RAG)
    // ============================================================
    if (modeToggle) {
        modeToggle.addEventListener('change', function() {
            if(this.checked) {
                // Mode ON (Kanan/Hijau) -> Gemini
                if(statusText) statusText.innerText = "Mode: Gemini (Umum)";
                addSystemMessage("🔄 Mode beralih ke <b>Gemini</b> (Pengetahuan Umum).");
            } else {
                // Mode OFF (Kiri/Coklat) -> RAG Wayanusa
                if(statusText) statusText.innerText = "Mode: Wayanusa (RAG)";
                addSystemMessage("🔄 Mode beralih ke <b>Wayanusa</b> (Data Spesifik Wayang).");
            }
        });
    }

    // Helper: Menambahkan pesan sistem kecil di tengah (abu-abu)
    function addSystemMessage(htmlMsg) {
        const div = document.createElement('div');
        div.style.textAlign = 'center';
        div.style.fontSize = '0.75rem';
        div.style.color = '#888';
        div.style.margin = '10px 0';
        div.style.fontStyle = 'italic';
        div.innerHTML = htmlMsg;
        
        chatMessages.appendChild(div);
        scrollToBottom();
    }

    // ============================================================
    // 4. FUNGSI RENDER PESAN (UI)
    // ============================================================
    function appendUserMessage(text) {
        const div = document.createElement('div');
        div.className = 'message-row user-row';
        div.innerHTML = `
            <div class="message-bubble user-bubble">
                <p>${text}</p>
                <span class="message-time">Kamu</span>
            </div>
        `;
        insertMessage(div);
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
        insertMessage(div);
        playNotification();
    }

    function insertMessage(divElement) {
        // Insert sebelum typing indicator agar indikator selalu di bawah
        if(typingIndicator && typingIndicator.parentNode === chatMessages) {
            chatMessages.insertBefore(divElement, typingIndicator);
        } else {
            chatMessages.appendChild(divElement);
        }
        scrollToBottom();
    }

    function showTyping() {
        if(typingIndicator) {
            typingIndicator.style.display = 'flex'; // Pakai flex biar titiknya rapi
            scrollToBottom();
        }
    }

    function hideTyping() {
        if(typingIndicator) typingIndicator.style.display = 'none';
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

    // ============================================================
    // 5. LOGIKA PENGIRIMAN PESAN (API)
    // ============================================================
    async function handleSendMessage(textOverride) {
        const text = textOverride || chatInput.value.trim();
        if (!text) return;

        // Reset input & Tampilkan pesan user
        if(chatInput) chatInput.value = '';
        appendUserMessage(text);
        showTyping();

        // Tentukan Mode: Jika checked = 'gemini', jika tidak = 'rag'
        // Default ke 'rag' jika tombol toggle belum ada
        const currentMode = (modeToggle && modeToggle.checked) ? 'gemini' : 'rag';

        try {
            // KIRIM KE ENDPOINT BARU: /api/chat-smart
            const response = await fetch('/api/chat-smart', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: text,
                    mode: currentMode // Kirim mode yang dipilih user
                })
            });

            const data = await response.json();

            // Sembunyikan typing & tampilkan balasan
            setTimeout(() => {
                hideTyping();
                
                // Format baris baru jadi <br> agar rapi
                let formatted = "Maaf, tidak ada respon.";
                if (data.response) {
                    formatted = data.response.replace(/\n/g, '<br>');
                    // Opsional: Parse Markdown bold (**) jadi <b>
                    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
                }
                
                appendBotMessage(formatted);
            }, 500); 

        } catch (error) {
            console.error("Chat Error:", error);
            hideTyping();
            appendBotMessage("Maaf Jang, koneksi lagi error euy. Coba lagi nanti ya.");
        }
    }

    // ============================================================
    // 6. EVENT LISTENERS INPUT
    // ============================================================
    if (sendButton) {
        sendButton.addEventListener('click', () => handleSendMessage());
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
    }

    // Handle Quick Replies (Tombol Cepat)
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('quick-btn')) {
            const text = e.target.getAttribute('data-text');
            handleSendMessage(text);
        }
    });

});