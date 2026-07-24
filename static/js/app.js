function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^|; )" + name + "=([^;]*)"));
  return match ? decodeURIComponent(match[2]) : null;
}

async function postJSON(url, data) {
  const body = new URLSearchParams(data || {});
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  if (!response.ok) throw new Error("request failed");
  return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".js-confirm-delete").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!confirm("Удалить безвозвратно?")) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll(".js-task-done").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const taskId = btn.dataset.taskId;
      btn.disabled = true;
      try {
        await postJSON(`/tasks/${taskId}/done/`);
        const row = btn.closest("[data-task-id]");
        row.style.opacity = "0.5";
        btn.remove();
      } catch (err) {
        btn.disabled = false;
        alert("Не удалось отметить задачу. Попробуйте ещё раз.");
      }
    });
  });

  initKanban();
  initPasswordToggles();
  initThemeToggle();
  initPasswordGenerator();
  initTelegramChat();
});

function initThemeToggle() {
  const btn = document.getElementById("js-theme-toggle");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const current = document.documentElement.getAttribute("data-theme") || (prefersDark ? "dark" : "light");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  });
}

const EYE_ICON =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7-11-7-11-7z"/><circle cx="12" cy="12" r="3"/></svg>';
const EYE_OFF_ICON =
  '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a20.5 20.5 0 0 1 5.06-5.94M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 7 11 7a20.5 20.5 0 0 1-2.16 3.19"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

function initPasswordToggles() {
  document.querySelectorAll('input[type="password"]').forEach((input) => {
    const wrapper = document.createElement("div");
    wrapper.className = "password-field";
    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "password-toggle";
    toggle.setAttribute("aria-label", "Показать пароль");
    toggle.innerHTML = EYE_ICON;
    wrapper.appendChild(toggle);

    toggle.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      toggle.innerHTML = show ? EYE_OFF_ICON : EYE_ICON;
      toggle.setAttribute("aria-label", show ? "Скрыть пароль" : "Показать пароль");
    });
  });
}

function generateStrongPassword(length = 14) {
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789!@#$%^&*";
  const values = new Uint32Array(length);
  window.crypto.getRandomValues(values);
  return Array.from(values, (v) => chars[v % chars.length]).join("");
}

function initPasswordGenerator() {
  const pairs = [
    ["password1", "password2"],
    ["new_password1", "new_password2"],
  ];

  pairs.forEach(([name1, name2]) => {
    const field1 = document.querySelector(`input[name="${name1}"]`);
    const field2 = document.querySelector(`input[name="${name2}"]`);
    if (!field1 || !field2) return;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn--secondary btn--small js-generate-password";
    btn.textContent = "Сгенерировать надёжный пароль";

    const hint = document.createElement("p");
    hint.className = "muted";
    hint.style.fontSize = "12px";
    hint.style.margin = "6px 0 0";
    hint.textContent = "Скопируйте пароль сейчас — после сохранения его нельзя будет посмотреть.";
    hint.style.display = "none";

    const anchor = field1.closest("p") || field1.parentElement;
    anchor.insertAdjacentElement("afterend", hint);
    anchor.insertAdjacentElement("afterend", btn);

    btn.addEventListener("click", () => {
      const password = generateStrongPassword();
      [field1, field2].forEach((input) => {
        input.value = password;
        input.type = "text";
        const toggle = input.closest(".password-field")?.querySelector(".password-toggle");
        if (toggle) {
          toggle.innerHTML = EYE_OFF_ICON;
          toggle.setAttribute("aria-label", "Скрыть пароль");
        }
      });
      hint.style.display = "block";
    });
  });
}

function initKanban() {
  const board = document.querySelector(".kanban");
  if (board) {
    board.scrollLeft = 0;
    initKanbanFade(board);
  }

  const cards = document.querySelectorAll(".kanban-card");
  const dropzones = document.querySelectorAll(".js-kanban-dropzone");
  if (!cards.length || !dropzones.length) return;

  cards.forEach((card) => {
    card.addEventListener("dragstart", (event) => {
      event.dataTransfer.setData("text/plain", card.dataset.dealId);
      event.dataTransfer.effectAllowed = "move";
    });
  });

  dropzones.forEach((zone) => {
    zone.addEventListener("dragover", (event) => {
      event.preventDefault();
      zone.classList.add("kanban-column__body--over");
    });

    zone.addEventListener("dragleave", () => {
      zone.classList.remove("kanban-column__body--over");
    });

    zone.addEventListener("drop", async (event) => {
      event.preventDefault();
      zone.classList.remove("kanban-column__body--over");

      const dealId = event.dataTransfer.getData("text/plain");
      const card = document.querySelector(`.kanban-card[data-deal-id="${dealId}"]`);
      if (!card) return;

      const stageId = zone.dataset.stageId;
      const sourceZone = card.closest(".js-kanban-dropzone");
      try {
        await postJSON(`/deals/${dealId}/move/`, { stage_id: stageId });
        zone.appendChild(card);
        refreshEmptyPlaceholder(zone);
        if (sourceZone && sourceZone !== zone) refreshEmptyPlaceholder(sourceZone);
        updateColumnCounts();
      } catch (err) {
        alert("Не удалось перенести сделку. Попробуйте ещё раз.");
      }
    });
  });
}

// Показывает/прячет заглушку «Пусто» в колонке в зависимости от того, есть ли
// в ней карточки — чтобы после перетаскивания не оставалось «Пусто» рядом с
// картой и наоборот.
function refreshEmptyPlaceholder(zone) {
  const hasCards = zone.querySelector(".kanban-card");
  let empty = zone.querySelector(".kanban-column__empty");
  if (hasCards && empty) {
    empty.remove();
  } else if (!hasCards && !empty) {
    empty = document.createElement("div");
    empty.className = "kanban-column__empty";
    empty.textContent = "Пусто";
    zone.appendChild(empty);
  }
}

function updateColumnCounts() {
  document.querySelectorAll(".kanban-column").forEach((column) => {
    const count = column.querySelectorAll(".kanban-card").length;
    const counter = column.querySelector(".kanban-column__count");
    if (counter) counter.textContent = count;
  });
}

function initKanbanFade(board) {
  const fade = document.querySelector(".kanban-wrap__fade");
  if (!fade) return;

  const update = () => {
    const atEnd = board.scrollLeft + board.clientWidth >= board.scrollWidth - 4;
    const scrollable = board.scrollWidth > board.clientWidth;
    fade.classList.toggle("is-hidden", atEnd || !scrollable);
  };

  update();
  board.addEventListener("scroll", update);
  window.addEventListener("resize", update);
}

function initTelegramChat() {
  const chat = document.getElementById("js-chat");
  if (!chat) return;

  chat.scrollTop = chat.scrollHeight;

  const contactId = chat.dataset.contactId;
  let lastId = parseInt(chat.dataset.lastId, 10) || 0;

  function appendMessage(message) {
    if (chat.querySelector(`[data-msg-id="${message.id}"]`)) return;

    const emptyHint = document.getElementById("js-chat-empty");
    if (emptyHint) emptyHint.remove();

    const bubble = document.createElement("div");
    bubble.className = `chat__bubble chat__bubble--${message.direction}`;
    if (message.failed) bubble.classList.add("chat__bubble--failed");
    bubble.dataset.msgId = message.id;

    const text = document.createElement("div");
    text.className = "chat__text";
    text.textContent = message.text;
    bubble.appendChild(text);

    if (message.failed) {
      const err = document.createElement("div");
      err.className = "chat__error";
      err.textContent = "⚠ Не доставлено" + (message.error ? ": " + message.error : "");
      bubble.appendChild(err);
    }

    const time = document.createElement("div");
    time.className = "chat__time";
    time.textContent = message.created_at;
    bubble.appendChild(time);

    chat.appendChild(bubble);
    if (message.id > lastId) lastId = message.id;
    chat.scrollTop = chat.scrollHeight;
  }

  // Догоняем сообщения, пришедшие между рендером страницы и открытием сокета.
  async function catchUp() {
    try {
      const response = await fetch(
        `/contacts/${contactId}/telegram/messages.json?after_id=${lastId}`
      );
      if (!response.ok) return;
      const data = await response.json();
      data.messages.forEach(appendMessage);
    } catch (err) {
      /* нет сети — сокет всё равно попробует */
    }
  }

  // --- Отправка ответа менеджера через сокет ---
  const form = document.querySelector(".chat__form");
  const input = form ? form.querySelector('[name="text"]') : null;
  let socket = null;

  if (form && input) {
    form.addEventListener("submit", (event) => {
      if (socket && socket.readyState === WebSocket.OPEN && input.value.trim()) {
        event.preventDefault();
        socket.send(JSON.stringify({ text: input.value }));
        input.value = "";
        input.focus();
      }
      // иначе — обычная отправка формой (fallback без сокета)
    });
  }

  // --- WebSocket с автопереподключением; polling — только если WS недоступен ---
  const wsProto = location.protocol === "https:" ? "wss" : "ws";
  const wsUrl = `${wsProto}://${location.host}/ws/contacts/${contactId}/chat/`;
  let reconnectDelay = 2000;
  let pollTimer = null;

  function startPollingFallback() {
    if (pollTimer) return;
    pollTimer = setInterval(catchUp, 6000);
  }

  function connect() {
    let ws;
    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      startPollingFallback();
      return;
    }

    ws.addEventListener("open", () => {
      socket = ws;
      reconnectDelay = 2000;
      if (pollTimer) {
        clearInterval(pollTimer);
        pollTimer = null;
      }
      catchUp();
    });

    ws.addEventListener("message", (event) => {
      try {
        appendMessage(JSON.parse(event.data));
      } catch (err) {
        /* пропускаем некорректный кадр */
      }
    });

    ws.addEventListener("close", () => {
      socket = null;
      // временный фолбэк на polling, пока переподключаемся
      startPollingFallback();
      setTimeout(connect, reconnectDelay);
      reconnectDelay = Math.min(reconnectDelay * 2, 15000);
    });

    ws.addEventListener("error", () => ws.close());
  }

  connect();
}
