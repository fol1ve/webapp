const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

/* ❄️ СНЕГ */
const snowContainer = document.querySelector(".snow-bg");
const snowIcon = document.querySelector(".snow-icon");
let snowEnabled = true;

function spawnSnowflake() {
    if (!snowEnabled) return;
    const flake = document.createElement("div");
    flake.className = "snowflake";
    flake.style.left = Math.random() * 100 + "vw";
    snowContainer.appendChild(flake);
    setTimeout(() => flake.remove(), 12000);
}
setInterval(spawnSnowflake, 220);

function toggleSnow() {
    snowEnabled = !snowEnabled;
    snowContainer.style.display = snowEnabled ? "block" : "none";
    snowIcon.classList.toggle("active", snowEnabled);
}

/* 🔘 ВЫБОР ФОРМАТОВ */
const formats = {
    users_txt: true,
    users_csv: false,
    chat_info: false
};

document.querySelectorAll(".format-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const type = btn.dataset.type;
        formats[type] = !formats[type];
        btn.classList.toggle("active", formats[type]);
    });
});

/* 🚀 ОТПРАВКА */
function sendLink() {
    const link = document.getElementById("link").value.trim();
    const error = document.getElementById("error");
    error.textContent = "";

    if (!link.includes("t.me/")) {
        error.textContent = "❌ Введите корректную ссылку Telegram";
        return;
    }

    tg.sendData(JSON.stringify({
        link: link,
        users_txt: formats.users_txt,
        users_csv: formats.users_csv,
        chat_info: formats.chat_info
    }));
}
