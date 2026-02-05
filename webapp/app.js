const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

const API_URL = "https://YOUR_APP.scalingo.io";

async function sendLink() {
    const link = document.getElementById("link").value.trim();
    const error = document.getElementById("error");
    const result = document.getElementById("result");

    error.textContent = "";
    result.textContent = "";

    if (!link.includes("t.me/")) {
        error.textContent = "❌ Некорректная ссылка";
        return;
    }

    result.textContent = "⏳ Парсинг запущен...";

    const res = await fetch(`${API_URL}/parse`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ link })
    });

    const data = await res.json();

    if (!data.ok) {
        error.textContent = "❌ Ошибка сервера";
        return;
    }

    result.innerHTML = `
        ✅ Готово<br><br>
        📄 <a href="${API_URL}/${data.csv}" target="_blank">CSV файл</a><br>
        📄 <a href="${API_URL}/${data.txt}" target="_blank">TXT файл</a>
    `;
}
