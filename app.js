const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const snowContainer = document.querySelector(".snow-bg");
const snowIcon = document.querySelector(".snow-icon");

let snowEnabled = true;
let currentMode = 'participants';
let selectedFormats = ['csv', 'txt'];

/* ❄️ СОЗДАНИЕ СНЕЖИНКИ */
function spawnSnowflake() {
    if (!snowEnabled) return;

    const flake = document.createElement("div");
    flake.className = "snowflake";

    const size = 4 + Math.random() * 6;
    const duration = 12 + Math.random() * 10;
    const opacity = 0.25 + Math.random() * 0.4;
    const blur = Math.random() * 1.5;
    const sway = (Math.random() * 40 - 20) + "px";

    flake.style.left = Math.random() * 100 + "vw";
    flake.style.setProperty("--size", size + "px");
    flake.style.setProperty("--opacity", opacity);
    flake.style.setProperty("--blur", blur + "px");
    flake.style.setProperty("--sway", sway);
    flake.style.animationDuration =
        duration + "s, " + (4 + Math.random() * 4) + "s";

    snowContainer.appendChild(flake);

    setTimeout(() => flake.remove(), duration * 1000);
}

/* ❄️ ИНТЕРВАЛ */
setInterval(spawnSnowflake, 220);

/* ❄️ ВКЛ / ВЫКЛ СНЕГА (ИКОНКА) */
function toggleSnow() {
    snowEnabled = !snowEnabled;

    snowContainer.style.display = snowEnabled ? "block" : "none";

    if (snowIcon) {
        snowIcon.classList.toggle("active", snowEnabled);
    }

    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred("light");
    }
}

/* 🔄 УСТАНОВКА РЕЖИМА */
function setMode(mode) {
    currentMode = mode;

    // Обновляем активную кнопку в нижней панели
    document.querySelectorAll('.nav-btn').forEach(btn => {
        // Сбрасываем active только у кнопок режимов (первые две)
        if (btn.id === 'nav-participants' || btn.id === 'nav-commentators') {
            btn.classList.remove('active');
        }
    });

    // Устанавливаем active на выбранную кнопку
    const activeBtn = document.getElementById(`nav-${mode}`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }

    // Обновляем текст подсказки
    const hintText = document.getElementById('hint-text');
    if (mode === 'participants') {
        hintText.textContent = 'Ты должен быть администратором канала для парсинга участников';
    } else {
        hintText.textContent = 'Собирает активных пользователей из комментариев и сообщений';
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

    // Хотя бы один формат должен быть выбран
    const btn = document.querySelector('.glow-btn');
    if (selectedFormats.length === 0) {
        btn.disabled = true;
        btn.textContent = '⚠️ Выберите формат файла';
    } else {
        btn.disabled = false;
        btn.textContent = '🚀 Начать парсинг';
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

    // Формируем JSON с данными
    const data = {
        link: link,
        mode: currentMode,
        formats: selectedFormats
    };

    tg.sendData(JSON.stringify(data));
}

/* ℹ️ ЗАГЛУШКА ДЛЯ НЕАКТИВНЫХ КНОПОК */
function showComingSoon() {
    const error = document.getElementById("error");
    error.textContent = "ℹ️ Эта функция в разработке";

    setTimeout(() => {
        error.textContent = "";
    }, 2000);

    if (tg.HapticFeedback) {
        tg.HapticFeedback.notificationOccurred("warning");
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    setMode('participants');
    updateFormatSelection();
});
