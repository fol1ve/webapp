const tg = window.Telegram.WebApp;
tg.expand();

let selectedFormat = "txt";

// ❄️ СНЕГ
let snowEnabled = true;

function toggleSnow() {
    snowEnabled = !snowEnabled;
    document.querySelector(".snow-bg").style.display = snowEnabled ? "block" : "none";
    document.querySelector(".snow-icon").classList.toggle("active", snowEnabled);
}

function createSnow() {
    const bg = document.querySelector(".snow-bg");

    setInterval(() => {
        if (!snowEnabled) return;

        const s = document.createElement("div");
        s.className = "snowflake";

        s.style.left = Math.random() * 100 + "vw";
        s.style.setProperty("--size", Math.random() * 4 + 2 + "px");
        s.style.setProperty("--opacity", Math.random());
        s.style.setProperty("--blur", Math.random() * 2 + "px");
        s.style.setProperty("--sway", Math.random() * 40 - 20 + "px");
        s.style.animationDuration = Math.random() * 5 + 6 + "s";

        bg.appendChild(s);
        setTimeout(() => s.remove(), 12000);
    }, 200);
}

createSnow();

// 📦 ФОРМАТЫ
document.querySelectorAll(".formats .nav-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".formats .nav-btn")
            .forEach(b => b.classList.remove("active"));

        btn.classList.add("active");
        selectedFormat = btn.dataset.format;
    });
});

// 🚀 ОТПРАВКА
function sendLink() {
    const link = document.getElementById("link").value.trim();
    const error = document.getElementById("error");

    if (!link.includes("t.me")) {
        error.textContent = "❌ Введите корректную ссылку";
        return;
    }

    tg.sendData(JSON.stringify({
        link: link,
        format: selectedFormat
    }));
}
