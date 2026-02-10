const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const snowContainer = document.querySelector(".snow-bg");
const snowIcon = document.querySelector(".snow-icon");

let snowEnabled = true;
let currentMode = 'participants'; // 'participants' или 'commentators'

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

    // лёгкий haptic на мобиле (если поддерживается)
    if (tg.HapticFeedback) {
        tg.HapticFeedback.impactOccurred("light");
    }
}

/* 🔄 УСТАНОВКА РЕЖИМА */
function setMode(mode) {
    currentMode = mode;

    // Обновляем UI
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.getElementById(`mode-${mode}`).classList.add('active');

    // Обновляем подсказку
    const hintText = document.getElementById('hint-text');
    if (mode === 'participants') {
        hintText.textContent = 'Ты должен быть администратором канала для парсинга участников';
    } else {
        hintText.textContent = 'Собирает активных пользователей из комментариев и сообщений';
    }

    // Haptic feedback
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

    // Формируем JSON с данными
    const data = {
        link: link,
        mode: currentMode
    };

    tg.sendData(JSON.stringify(data));
}

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    // Устанавливаем начальный режим
    setMode('participants');
});
