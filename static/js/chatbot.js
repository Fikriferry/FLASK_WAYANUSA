document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Chatbot Script Ready!");

    // 1. Ambil Elemen
    const wrapper = document.getElementById('chatbot-wrapper');
    const btnChat = document.getElementById('chatbotButton');
    const popup = document.getElementById('chatPopup');
    const btnClose = document.getElementById('chatClose');
    const input = document.getElementById('chatInput');
    const btnSend = document.getElementById('sendButton');
    const messagesArea = document.getElementById('chatMessages');

    if (!wrapper || !btnChat || !popup) {
        console.error("❌ Elemen Chatbot tidak lengkap!");
        return;
    }

    // 2. Cek Status Login
    const isLoggedIn = JSON.parse(wrapper.getAttribute('data-user-logged-in'));
    const loginUrl = wrapper.getAttribute('data-login-url');

    // --- FUNGSI BUKA/TUTUP CHAT ---
    btnChat.addEventListener('click', () => {
        if (!isLoggedIn) {
            alert("Silakan login terlebih dahulu untuk ngobrol sama Cepot!");
            window.location.href = loginUrl;
            return;
        }
        popup.classList.toggle('show');
        if (popup.classList.contains('show')) input.focus();
    });

    btnClose.addEventListener('click', () => {
        popup.classList.remove('show');
    });

    // --- FUNGSI KIRIM PESAN ---
    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;

        // A. Tampilkan Pesan User
        appendMessage(text, 'user-message');
        input.value = '';

        // B. Tampilkan Loading Bubble
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message bot-message';
        loadingDiv.id = loadingId;
        loadingDiv.innerHTML = '<em>Cepot lagi mikir...</em>';
        messagesArea.appendChild(loadingDiv);
        messagesArea.scrollTop = messagesArea.scrollHeight;

        try {
            // C. Kirim ke API Flask
            // Perhatikan URL: /api/chat sesuai blueprint
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text })
            });

            const data = await response.json();

            // D. Hapus Loading & Tampilkan Balasan
            document.getElementById(loadingId).remove();
            
            // Format baris baru (\n jadi <br>)
            const reply = data.response.replace(/\n/g, '<br>');
            appendMessage(reply, 'bot-message');

        } catch (error) {
            console.error("Chat Error:", error);
            document.getElementById(loadingId).remove();
            appendMessage("Waduh, error koneksi Jang. Cek internetmu ya!", 'bot-message');
        }
    }

    // Helper: Tambah Bubble Chat
    function appendMessage(htmlText, className) {
        const div = document.createElement('div');
        div.className = `message ${className}`;
        div.innerHTML = `<p>${htmlText}</p>`;
        messagesArea.appendChild(div);
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }

    // --- EVENT LISTENER ---
    btnSend.addEventListener('click', sendMessage);
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});