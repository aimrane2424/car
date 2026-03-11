// chatbot.js - نسخة نهائية مع mute واضح + click عادي
// =========================================================

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const speechSynthesis = window.speechSynthesis;

let voiceState = {
    isMuted: false,
    isRecording: false,
    isSpeaking: false
};

// ===== حفظ/تحميل الحالة =====
function saveVoiceState() { localStorage.setItem('voiceState', JSON.stringify(voiceState)); }
function loadVoiceState() {
    try {
        const saved = localStorage.getItem('voiceState');
        if (saved) voiceState = { ...voiceState, ...JSON.parse(saved) };
    } catch (e) {}
}

// ===== تبديل الكتم =====
function toggleMute() {
    voiceState.isMuted = !voiceState.isMuted;
    
    if (voiceState.isMuted && speechSynthesis?.speaking) {
        speechSynthesis.cancel();
        voiceState.isSpeaking = false;
    }
    
    showNotification(voiceState.isMuted ? '🔇 تم كتم الصوت' : '🔊 تم إلغاء كتم الصوت');
    updateReadMuteButton();
    saveVoiceState();
}

// ===== إنشاء زر القراءة/الكتم =====
function createReadMuteButton() {
    const chatInputBar = document.getElementById('chat-input-bar');
    if (!chatInputBar || document.getElementById('read-mute-btn')) {
        updateReadMuteButton();
        return;
    }

    const buttonHTML = `<button id="read-mute-btn" class="voice-btn" title="قراءة آخر رسالة">🔊</button>`;
    document.getElementById('send-btn')?.insertAdjacentHTML('beforebegin', buttonHTML);

    const readMuteBtn = document.getElementById('read-mute-btn');
    if (!readMuteBtn) return;

    // ✅ CLICK عادي واحد يكفي للكل!
    readMuteBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        if (voiceState.isMuted) {
            // إذا مكتوم → نقرة وحدة = إلغاء الكتم
            toggleMute();
        } else if (voiceState.isSpeaking && speechSynthesis?.speaking) {
            // إذا كيقرا → نقرة وحدة = إيقاف القراءة
            speechSynthesis.cancel();
            voiceState.isSpeaking = false;
            showNotification('⏹ تم إيقاف القراءة');
            updateReadMuteButton();
        } else {
            // إذا عادي → نقرة وحدة = قراءة آخر رسالة
            readLastMessage();
        }
    });

    updateReadMuteButton();
}

// ===== تحديث زر القراءة/الكتم (زر أحمر صغير للـ mute) =====
function updateReadMuteButton() {
    const btn = document.getElementById('read-mute-btn');
    if (!btn) return;

    btn.style.animation = 'none';
    
    if (voiceState.isMuted) {
        // 🔥 مكتوم: زر أحمر صغير مع لوجو 🔇 + اهتزاز
        btn.innerHTML = '🔇';
        btn.style.cssText = `
            width: 36px !important;
            height: 36px !important;
            border-radius: 50%;
            border: 2px solid #ff4757 !important;
            background: linear-gradient(135deg, #ff3838, #ff6b6b) !important;
            color: white !important;
            font-size: 16px !important;
            font-weight: bold !important;
            box-shadow: 0 4px 15px rgba(255, 71, 87, 0.5) !important;
            animation: shake 0.5s ease-in-out infinite alternate !important;
        `;
        btn.title = '🔇 اضغط لإلغاء كتم الصوت';
        
    } else if (voiceState.isSpeaking) {
        // كيقرا: أزرق نابض
        btn.innerHTML = '⏹️';
        btn.style.cssText = `
            width: 40px !important;
            height: 40px !important;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #3498db, #2980b9) !important;
            color: white !important;
            font-size: 18px !important;
            animation: pulse 1s infinite !important;
            box-shadow: 0 0 20px rgba(52, 152, 219, 0.6) !important;
        `;
        btn.title = '⏹️ اضغط لإيقاف القراءة';
        
    } else {
        // جاهز: أخضر
        btn.innerHTML = '🔊';
        btn.style.cssText = `
            width: 40px !important;
            height: 40px !important;
            border-radius: 50%;
            border: none;
            background: linear-gradient(135deg, #203ae0ff, #1654b1b8) !important;
            color: white !important;
            font-size: 18px !important;
            box-shadow: 0 4px 12px rgba(85, 124, 217, 0.4) !important;
        `;
        btn.title = '🔊 اضغط لقراءة آخر رسالة';
    }
}

// ===== باقي الدوال (نفسها) =====
function updateRecordButton() {
    const recordBtn = document.getElementById('voice-input-btn');
    if (!recordBtn) return;

    recordBtn.innerHTML = '🎤';
    Object.assign(recordBtn.style, {
        width: '40px', height: '40px', borderRadius: '50%', border: 'none',
        background: 'linear-gradient(135deg, var(--accent-cyan), #00a8e6)',
        color: 'var(--primary-dark)', fontSize: '18px', cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        margin: '0 4px', transition: 'all 0.3s'
    });

    ['mouseenter', 'mouseleave'].forEach((evt, i) => {
        recordBtn.addEventListener(evt, function() {
            if (!voiceState.isRecording) {
                this.style.transform = i ? 'scale(1.1)' : 'scale(1)';
                this.style.boxShadow = i ? '0 4px 12px rgba(0,0,0,0.3)' : 'none';
            }
        });
    });
}

function startRecording() {
    if (!SpeechRecognition) return alert("La reconnaissance vocale n'est pas supportée");

    const recordBtn = document.getElementById('voice-input-btn');
    recordBtn.innerHTML = '🎙️';
    recordBtn.style.background = 'linear-gradient(135deg, #f39c12, #e67e22)';
    recordBtn.style.color = 'white';
    recordBtn.style.animation = 'pulse 1s infinite';

    voiceState.isRecording = true;
    const recognition = new SpeechRecognition();
    recognition.lang = 'fr-FR';
    recognition.interimResults = false;

    recognition.onstart = () => showNotification('🎤 جاري التسجيل...');
    recognition.onresult = (e) => {
        document.getElementById("chat-input").value = e.results[0][0].transcript;
        sendChatMessage();
    };
    recognition.onerror = recognition.onend = () => {
        voiceState.isRecording = false;
        resetRecordButton();
        showNotification('✅ انتهى التسجيل');
    };
    recognition.start();
}

function resetRecordButton() {
    const btn = document.getElementById('voice-input-btn');
    if (btn) {
        btn.innerHTML = '🎤';
        btn.style.background = 'linear-gradient(135deg, var(--accent-cyan), #00a8e6)';
        btn.style.color = 'var(--primary-dark)';
        btn.style.animation = 'none';
    }
}

function readLastMessage() {
    if (voiceState.isMuted || !speechSynthesis) {
        showNotification(voiceState.isMuted ? '🔇 الصوت مكتوم' : '⚠️ القراءة غير مدعومة');
        return;
    }

    const messages = document.querySelectorAll('#chat-messages .chat-message.bot');
    if (!messages.length) return showNotification('⚠️ لا رسائل');

    const text = messages[messages.length - 1].textContent.replace('Bot : ', '').trim();
    if (!text) return showNotification('⚠️ لا نص للقراءة');

    speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'fr-FR';
    utterance.rate = 1.0;

    utterance.onstart = () => {
        voiceState.isSpeaking = true;
        updateReadMuteButton();
        showNotification('🔊 جاري القراءة...');
    };
    utterance.onend = utterance.onerror = () => {
        voiceState.isSpeaking = false;
        updateReadMuteButton();
    };

    speechSynthesis.speak(utterance);
}

function showNotification(msg) {
    document.querySelector('.voice-notification')?.remove();
    const notif = document.createElement('div');
    notif.className = 'voice-notification';
    notif.textContent = msg;
    Object.assign(notif.style, {
        position: 'fixed', top: '100px', right: '20px',
        background: 'rgba(20,28,45,0.95)', color: 'var(--accent-cyan)',
        padding: '12px 18px', borderRadius: '10px', border: '2px solid var(--accent-cyan)',
        fontSize: '14px', fontWeight: 'bold', zIndex: '9999',
        animation: 'slideIn 0.3s ease, fadeOut 0.3s ease 2s',
        boxShadow: '0 5px 20px rgba(0,0,0,0.3)', backdropFilter: 'blur(10px)'
    });
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 2500);
}

function addMessage(sender, text) {
    const box = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = `chat-message ${sender === 'Vous' ? 'user' : 'bot'}`;
    Object.assign(div.style, {
        margin: "6px 0", maxWidth: "85%", padding: "8px 12px",
        borderRadius: "10px", fontSize: "14px", wordWrap: "break-word"
    });

    if (sender === "Vous") {
        Object.assign(div.style, {
            alignSelf: "flex-end", backgroundColor: "#3498db",
            color: "#fff", borderBottomRightRadius: "5px"
        });
    } else {
        Object.assign(div.style, {
            alignSelf: "flex-start", backgroundColor: "#ecf0f1",
            color: "#2c3e50", borderBottomLeftRadius: "5px"
        });
    }

    div.textContent = `${sender} : ${text}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
}

function sendChatMessage() {
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;

    addMessage("Vous", message);
    input.value = "";

    const formData = new FormData();
    formData.append('message', message);

    fetch('/api/chat', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => data.success ? addMessage("Bot", data.response) : addMessage("Bot", "❌ Erreur"))
        .catch(() => addMessage("Bot", "Indisponible"));
}

// ===== التهيئة =====
document.addEventListener("DOMContentLoaded", function() {
    loadVoiceState();
    
    createReadMuteButton();
    updateRecordButton();

    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.05);opacity:.8} }
        @keyframes slideIn { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }
        @keyframes fadeOut { from{opacity:1} to{opacity:0} }
        
        @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-3px); }
            75% { transform: translateX(3px); }
        }
        
        .voice-btn { 
            width:40px;height:40px;border-radius:50%;border:none;font-size:18px;cursor:pointer;
            transition:all .3s;display:flex;align-items:center;justify-content:center;margin:0 4px; 
        }
        .voice-btn:hover { transform:scale(1.1);box-shadow:0 4px 12px rgba(0,0,0,.3); }
    `;
    document.head.appendChild(style);

    document.getElementById('voice-input-btn')?.addEventListener('click', startRecording);
    
    const input = document.getElementById("chat-input");
    input?.addEventListener("keydown", e => e.key === "Enter" && sendChatMessage());
    document.getElementById("send-btn")?.addEventListener("click", sendChatMessage);

    setTimeout(() => addMessage("Bot", "Bonjour ! Comment puis-je vous aider ?"), 1000);
});

console.log("✅ chatbot.js جاهز - CLICK وحدة تكفي للكل!");
