const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const sunContainer = document.getElementById("sun-bg");
const sunIcon = document.getElementById("sun-toggle-btn");

let sunEnabled = true;
let currentMode = 'participants';
let selectedFormats = ['csv', 'txt'];

/* ☀️ СОЗДАНИЕ СОЛНЕЧНОГО ЛУЧА */
function spawnSunRay() {
    if (!sunEnabled) return;
    if (!sunContainer) return;

    const ray = document.createElement("div");
    ray.className = "sun-ray";

    const size = 80 + Math.random() * 150;
    const duration = 10 + Math.random() * 15;
    const opacity = 0.15 + Math.random() * 0.3;

    const colors = [
        'rgba(255, 159, 67,',
        'rgba(255, 107, 107,',
        'rgba(254, 202, 87,',
        'rgba(102, 126, 234,',
        'rgba(240, 147, 251,'
    ];
    const color = colors[Math.floor(Math.random() * colors.length)];

    ray.style.width = size + "px";
    ray.style.height = size + "px";
    ray.style.background = color + opacity + ")";
    ray.style.left = Math.random() * 100 + "vw";
    ray.style.top = Math.random() * 100 + "vh";
    ray.style.animationDuration = duration + "s";

    sunContainer.appendChild(ray);

    setTimeout(() => {
        if (ray.parentNode) ray.remove();
    }, duration * 1000);
}

/* ☀️ ИНТЕРВАЛ */
const sunInterval = setInterval(spawnSunRay, 500);

/* ☀️ ВКЛ / ВЫКЛ ЭФФЕКТОВ */
function toggleSun() {
    sunEnabled = !sunEnabled;

    if (sunContainer) {
        sunContainer.style.display = sunEnabled ? "block" : "none";
    }

    if (sunIcon) {
        sunIcon.classList.toggle("active", sunEnabled);
        sunIcon.textContent = sunEnabled ? "✨" : "💤";
    }

    // Очистить существующие лучи если выключили
    if (!sunEnabled && sunContainer) {
        sunContainer.innerHTML = '';
    }

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred("light");
    }
}

/* 🔄 УСТАНОВКА РЕЖИМА */
function setMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.id === 'nav-participants' || btn.id === 'nav-commentators') {
            btn.classList.remove('active');
        }
    });

    const activeBtn = document.getElementById(`nav-${mode}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    const hintText = document.getElementById('hint-text');
    if (hintText) {
        if (mode === 'participants') {
            hintText.textContent = 'Ты должен быть администратором канала для парсинга участников';
        } else {
            hintText.textContent = 'Собирает активных пользователей из комментариев и сообщений';
        }
    }

    if (tg.HapticFeedback) {
        tg.HapticFeedback.selectionChanged();
    }
}

/* 📁 ОБНОВЛЕНИЕ ВЫБОРА ФОРМАТОВ */
function updateFormatSelection() {
    const csvChecked = document.getElementById('format-csv').checked;
    const txtChecked = document.getElementById('format-txt').checked;
    const jsonChecked = document.getElementById('format-json').checked;

    selectedFormats = [];
    if (csvChecked) selectedFormats.push('csv');
    if (txtChecked) selectedFormats.push('txt');
    if (jsonChecked) selectedFormats.push('json');

    const btn = document.querySelector('.glow-btn');
    if (btn) {
        if (selectedFormats.length === 0) {
            btn.disabled = true;
            btn.textContent = '⚠️ Выберите формат файла';
        } else {
            btn.disabled = false;
            btn.textContent = '🚀 Начать парсинг';
        }
    }

    if (tg.HapticFeedback) {
        tg.HapticFeedback.selectionChanged();
    }
}

/* 🚀 ОТПРАВКА ССЫЛКИ */
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
        error.textContent = "❌ Выберите хотя бы один формат файла";
        return;
    }

    const data = {
        link: link,
        mode: currentMode,
        formats: selectedFormats
    };

    tg.sendData
