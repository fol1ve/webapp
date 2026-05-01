const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const effectsBg = document.getElementById("effects-bg");
const effectsBtn = document.getElementById("effects-btn");
const effectsIcon = document.getElementById("effects-icon");

let effectsEnabled = true;
let currentMode = 'participants';
let selectedFormats = ['csv', 'txt'];
let effectsInterval = null;

/* ===== ЭФФЕКТЫ ===== */

function createParticle() {
    if (!effectsEnabled || !effectsBg) return;

    const type = Math.random() > 0.6 ? 'sparkle' : 'float-circle';
    const particle = document.createElement('div');
    particle.className = `particle ${type}`;

    const size = type === 'sparkle'
        ? 2 + Math.random() * 4
        : 20 + Math.random() * 60;

    particle.style.width = size + 'px';
    particle.style.height = size + 'px';
    particle.style.left = Math.random() * 100 + 'vw';

    if (type === 'float-circle') {
        particle.style.top = '100vh';
        const duration = 8 + Math.random() * 12;
        particle.style.animationDuration = duration + 's';
        particle.style.opacity = 0.1 + Math.random() * 0.3;
    } else {
        particle.style.top = Math.random() * 100 + 'vh';
        const duration = 2 + Math.random() * 4;
        particle.style.animationDuration = duration + 's';
        particle.style.animationDelay = Math.random() * 2 + 's';
    }

    effectsBg.appendChild(particle);

    const removeTime = type === 'float-circle'
        ? (parseFloat(particle.style.animationDuration) * 1000)
        : 6000;

    setTimeout(() => {
        if (particle.parentNode) particle.remove();
    }, removeTime);
}

function startEffects() {
    if (effectsInterval) clearInterval(effectsInterval);
    // Создаём начальные частицы
    for (let i = 0; i < 8; i++) {
        setTimeout(createParticle, i * 300);
    }
    effectsInterval = setInterval(createParticle, 800);
}

function stopEffects() {
    if (effectsInterval) {
        clearInterval(effectsInterval);
        effectsInterval = null;
    }
    if (effectsBg) effectsBg.innerHTML = '';
}

/* ===== ПЕРЕКЛЮЧАТЕЛЬ ===== */

function toggleEffects() {
    effectsEnabled = !effectsEnabled;

    if (effectsBtn) {
        effectsBtn.classList.toggle('active', effectsEnabled);
    }

    if (effectsIcon) {
        effectsIcon.textContent = effectsEnabled ? '✨' : '💤';
    }

    if (effectsEnabled) {
        startEffects();
    } else {
        stopEffects();
    }

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred(effectsEnabled ? "light" : "medium");
    }
}

/* ===== РЕЖИМЫ ===== */

function setMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.id === 'nav-participants' || btn.id === 'nav-commentators') {
            btn.classList.remove('active');
        }
    });

    const activeBtn = document.getElementById(`nav-${mode}`);
    if (activeBtn) activeBtn.classList.add('active');

    const hintText = document.getElementById('hint-text');
    if (hintText) {
        hintText.textContent = mode === 'participants'
            ? 'Ты должен быть администратором канала для парсинга участников'
            : 'Собирает активных пользователей из комментариев и сообщений';
    }

    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

/* ===== ФОРМАТЫ ===== */

function updateFormatSelection() {
    selectedFormats = [];
    if (document.getElementById('format-csv').checked) selectedFormats.push('csv');
    if (document.getElementById('format-txt').checked) selectedFormats.push('txt');
    if (document.getElementById('format-json').checked) selectedFormats.push('json');

    const btn = document.querySelector('.glow-btn');
    if (btn) {
        btn.disabled = selectedFormats.length === 0;
        btn.textContent = selectedFormats.length === 0
            ? '⚠️ Выберите формат'
            : '🚀 Начать парсинг';
    }

    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

/* ===== ОТПРАВКА ===== */

function sendLink() {
    const linkInput = document.getElementById("link");
    const error = document.getElementById("error");

    const link = linkInput.value.trim();
    error.textContent = "";

    if (!link.includes("t.me/")) {
        error.textContent = "❌ Введите корректную ссылку Telegram";
        return;
    }

    if (selectedFormats.length === 0) {
        error.textContent = "❌ Выберите хотя бы один формат";
        return;
    }

    tg.sendData(JSON.stringify({
        link: link,
        mode: currentMode,
        formats: selectedFormats
    }));
}

/* ===== ЗАГЛУШКА ===== */

function showComingSoon() {
    const error = document.getElementById("error");
    error.textContent = "ℹ️ Эта функция в разработке";
    setTimeout(() => error.textContent = "", 2000);
    if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred("warning");
}

/* ===== ИНИЦИАЛИЗАЦИЯ ===== */

document.addEventListener('DOMContentLoaded', function() {
    setMode('participants');
    updateFormatSelection();
    startEffects();
});
