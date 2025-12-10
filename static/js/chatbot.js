document.addEventListener('DOMContentLoaded', function() {
    // --- SETUP ELEMEN ---
    const chatbotButton = document.getElementById('chatbotButton');
    const chatPopup = document.getElementById('chatPopup');
    const chatClose = document.getElementById('chatClose');
    const chatInput = document.getElementById('chatInput');
    const sendButton = document.getElementById('sendButton');
    const chatMessages = document.getElementById('chatMessages');
    const micButton = document.getElementById('micButton');
    
    // Panel
    const panelChat = document.getElementById('panelChat');
    const panelWayang = document.getElementById('panelWayang');
    const btnModeChat = document.getElementById('btnModeChat');
    const btnModeWayang = document.getElementById('btnModeWayang');

    // Arduino & Status
    const portSelect = document.getElementById('portSelect');
    const btnConnect = document.getElementById('btnConnect');
    const statusWayang = document.getElementById('statusWayang');

    // State Variables
    let currentMode = 'chat'; // 'chat' or 'wayang'
    let isConnected = false;
    
    // VARIABEL KHUSUS WAKE WORD
    let recognition = null;
    let isListening = false;
    let wakeWordActive = false; // True jika baru saja dipanggil "Halo Cepot"
    const WAKE_WORDS = ["cepot", "halo cepot", "he cepot", "si cepot", "pot"];

    // Cek Login
    const wrapper = document.getElementById('chatbot-wrapper');
    const isLoggedIn = wrapper ? JSON.parse(wrapper.getAttribute('data-user-logged-in')) : false;
    const loginUrl = wrapper ? wrapper.getAttribute('data-login-url') : '/login';

    // --- 1. SETUP SPEECH RECOGNITION ---
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'id-ID';
        recognition.continuous = true; // Terus mendengarkan
        recognition.interimResults = false;

        recognition.onresult = (event) => {
            const last = event.results.length - 1;
            const transcript = event.results[last][0].transcript.trim().toLowerCase();
            console.log("Suara masuk:", transcript);

            if (currentMode === 'wayang') {
                handleWayangVoice(transcript);
            } else {
                // Mode chat biasa (manual klik mic)
                chatInput.value = transcript;
            }
        };

        recognition.onend = () => {
            // Auto restart jika di mode wayang (agar always listening)
            if (currentMode === 'wayang' && isListening) {
                console.log("Restarting mic...");
                try { recognition.start(); } catch(e){}
            } else {
                isListening = false;
                micButton.classList.remove('listening');
            }
        };
        
        recognition.onerror = (e) => {
            console.error("Mic Error:", e.error);
            // Restart jika error 'no-speech'
            if (currentMode === 'wayang' && e.error === 'no-speech') {
                recognition.stop();
            }
        };
    }

    // --- 2. LOGIKA WAKE WORD (CEPOT) ---
    function handleWayangVoice(text) {
        // STATE 1: Menunggu Wake Word
        if (!wakeWordActive) {
            // Cek apakah ada kata "Cepot"
            const foundWakeWord = WAKE_WORDS.some(word => text.includes(word));
            
            if (foundWakeWord) {
                wakeWordActive = true;
                playBeep(); // Efek suara 'Ting!'
                
                // Visual Feedback
                statusWayang.innerHTML = "🎤 <b>NGOMONG BAE JANG...</b> (Mendengarkan)";
                statusWayang.style.color = "#D4A373";
                
                // Tampilkan di chat kalau user memanggil
                appendMessage("Halo Cepot!", "user-message");
            }
        } 
        // STATE 2: Menunggu Perintah (Setelah dipanggil)
        else {
            // Jika user bilang "batal" atau "stop"
            if (text.includes("batal") || text.includes("stop")) {
                wakeWordActive = false;
                statusWayang.innerHTML = "Standby (Panggil 'Halo Cepot')";
                statusWayang.style.color = "#666";
                return;
            }

            // Kirim Perintah ke Backend
            sendMessageToWayang(text);
            
            // Reset state (harus panggil Cepot lagi untuk perintah selanjutnya)
            // Atau biarkan true jika ingin percakapan bersambung (opsional)
            wakeWordActive = false; 
            statusWayang.innerHTML = "Sedang menjawab... 🔊";
            statusWayang.style.color = "green";
        }
    }

    // --- 3. NAVIGASI UI ---
    if(chatbotButton) {
        chatbotButton.addEventListener('click', () => {
            if (!isLoggedIn) { window.location.href = loginUrl; return; }
            chatPopup.classList.toggle('show');
        });
    }
    if(chatClose) chatClose.addEventListener('click', () => chatPopup.classList.remove('show'));

    window.switchMode = function(mode) {
        currentMode = mode;
        if (mode === 'chat') {
            // UI Switch
            panelChat.style.display = 'flex';
            panelWayang.style.display = 'none';
            btnModeChat.classList.add('active');
            btnModeWayang.classList.remove('active');
            
            // Stop Always Listening
            stopListening();
            
        } else {
            // UI Switch
            panelChat.style.display = 'none';
            panelWayang.style.display = 'block';
            btnModeChat.classList.remove('active');
            btnModeWayang.classList.add('active');
            
            // Init Port & Start Listening
            refreshPorts();
            startListening(); // <--- Mulai dengarkan "Halo Cepot"
            statusWayang.innerHTML = "Standby (Panggil 'Halo Cepot')";
        }
    };

    function startListening() {
        if (recognition && !isListening) {
            recognition.start();
            isListening = true;
            micButton.classList.add('listening'); // Merah berdenyut
        }
    }

    function stopListening() {
        if (recognition) {
            isListening = false;
            wakeWordActive = false;
            recognition.stop();
            micButton.classList.remove('listening');
        }
    }

    // --- 4. KIRIM PESAN ---
    // Fungsi untuk mode Web Chat (Manual)
    async function sendMessageManual() {
        const text = chatInput.value.trim();
        if (!text) return;
        chatInput.value = '';
        appendMessage(text, 'user-message');
        
        // Kirim ke API Chat Biasa
        try {
            const res = await fetch('/api/chat', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            appendMessage(data.response.replace(/\n/g, '<br>'), 'bot-message');
        } catch (e) { appendMessage("Error koneksi.", 'bot-message'); }
    }

    // Fungsi untuk mode Smart Wayang (Otomatis dari Suara)
    async function sendMessageToWayang(text) {
        appendMessage(text, 'user-message'); // Tampilkan apa yang didengar mic
        
        try {
            const res = await fetch('/api/cepot/talk', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text })
            });
            const data = await res.json();
            
            // Tampilkan balasan teks di layar
            appendMessage(data.response, 'bot-message');
            
            // Kembalikan status ke standby setelah menjawab
            setTimeout(() => {
                statusWayang.innerHTML = "Standby (Panggil 'Halo Cepot')";
                statusWayang.style.color = "#666";
            }, 3000);

        } catch (e) {
            console.error(e);
            statusWayang.innerText = "Error Sistem";
        }
    }

    // Helper UI
    function appendMessage(text, className) {
        const div = document.createElement('div');
        div.className = `message ${className}`;
        div.innerHTML = `<p>${text}</p>`;
        chatMessages.appendChild(div);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function playBeep() {
        // Bunyi 'Ting' sederhana pakai AudioContext biar gak perlu file mp3
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = 800;
        gain.gain.value = 0.1;
        osc.start();
        setTimeout(() => osc.stop(), 200);
    }

    // --- ARDUINO CONTROLS ---
    window.refreshPorts = async function() {
        try {
            const res = await fetch('/api/cepot/ports');
            const data = await res.json();
            portSelect.innerHTML = '<option value="">-- Pilih Port --</option>';
            data.ports.forEach(p => portSelect.innerHTML += `<option value="${p}">${p}</option>`);
        } catch (e) {}
    };

    window.toggleConnect = async function() {
        if (!isConnected) {
            const port = portSelect.value;
            if(!port) return alert("Pilih Port!");
            
            try {
                const res = await fetch('/api/cepot/connect', {
                    method:'POST', headers:{'Content-Type':'application/json'},
                    body: JSON.stringify({port:port})
                });
                const data = await res.json();
                if(data.status==='success') {
                    isConnected = true;
                    btnConnect.innerText = "PUTUSKAN";
                    btnConnect.style.background = "#d9534f";
                    alert("Terhubung! Panggil 'Halo Cepot' untuk mulai.");
                } else alert(data.message);
            } catch(e) { alert("Gagal connect"); }
        } else {
            await fetch('/api/cepot/disconnect', {method:'POST'});
            isConnected = false;
            btnConnect.innerText = "HUBUNGKAN";
            btnConnect.style.background = "";
        }
    };

    // Event Listener Tombol Kirim Manual (Hanya aktif di mode chat biasa)
    if(sendButton) sendButton.addEventListener('click', () => {
        if(currentMode === 'chat') sendMessageManual();
    });
    
    // Mic Button Manual (Opsional, untuk force listen)
    if(micButton) micButton.addEventListener('click', () => {
        if(isListening) recognition.stop();
        else recognition.start();
    });
});