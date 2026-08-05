(function () {
  const app = document.getElementById("chat-app");
  if (!app) return;

  const roomSlug = app.dataset.roomSlug;
  const username = app.dataset.username;
  const list = document.getElementById("message-list");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const statusText = document.getElementById("connection-status");
  const statusDot = document.querySelector(".status-dot");
  const presenceLabel = document.getElementById("presence-label");

  const AVATAR_PALETTE = [
    "#2f7a5a",
    "#ce5a32",
    "#3d6b8a",
    "#8a5a2f",
    "#5a4a8a",
    "#2f6b6b",
    "#8a3d5a",
    "#4a6b2f",
  ];

  const seenIds = new Set(
    Array.from(list.querySelectorAll(".message[data-id]")).map((el) => el.dataset.id)
  );

  let socket;
  let reconnectTimer;
  let online = new Set([username]);

  function protocol() {
    return window.location.protocol === "https:" ? "wss" : "ws";
  }

  function hashUser(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i += 1) {
      hash = (hash << 5) - hash + name.charCodeAt(i);
      hash |= 0;
    }
    return Math.abs(hash);
  }

  function initials(name) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length === 0) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }

  function paintAvatar(el, name) {
    if (!el) return;
    const color = AVATAR_PALETTE[hashUser(name) % AVATAR_PALETTE.length];
    el.style.setProperty("--avatar-bg", color);
    el.textContent = initials(name);
    el.title = name;
  }

  function paintAllAvatars() {
    document.querySelectorAll(".avatar[data-user]").forEach((el) => {
      paintAvatar(el, el.dataset.user || "");
    });
  }

  function setStatus(state, label) {
    statusDot.dataset.status = state;
    statusText.textContent = label;
  }

  function updatePresence(users) {
    if (Array.isArray(users)) {
      online = new Set(users);
    }
    const others = [...online].filter((name) => name !== username);
    if (others.length === 0) {
      presenceLabel.hidden = true;
      presenceLabel.textContent = "";
      return;
    }
    presenceLabel.hidden = false;
    presenceLabel.textContent =
      others.length === 1
        ? `· ${others[0]} is here`
        : `· ${others.length} others here`;
  }

  function formatTime(iso) {
    try {
      return new Date(iso).toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  function lastMessage() {
    const items = list.querySelectorAll(".message");
    return items.length ? items[items.length - 1] : null;
  }

  function appendMessage({ id, username: user, message, created_at }) {
    const key = String(id);
    if (seenIds.has(key)) return;
    seenIds.add(key);

    const empty = document.getElementById("empty-chat");
    if (empty) empty.remove();

    const mine = user === username;
    const prev = lastMessage();
    const stacked = Boolean(prev && prev.dataset.user === user);

    const article = document.createElement("article");
    article.className =
      "message" + (mine ? " mine" : "") + (stacked ? " stacked" : "");
    article.dataset.id = key;
    article.dataset.user = user;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.dataset.user = user;
    avatar.setAttribute("aria-hidden", "true");
    paintAvatar(avatar, user);

    const bubble = document.createElement("div");
    bubble.className = "bubble";

    const header = document.createElement("header");
    header.className = "bubble-meta";

    const nameEl = document.createElement("span");
    nameEl.className = "msg-user";
    nameEl.textContent = user;

    const timeEl = document.createElement("time");
    timeEl.dateTime = created_at || "";
    timeEl.textContent = formatTime(created_at);

    header.append(nameEl, timeEl);

    const body = document.createElement("p");
    body.className = "bubble-text";
    body.textContent = message;

    bubble.append(header, body);
    article.append(avatar, bubble);
    list.appendChild(article);
    list.scrollTop = list.scrollHeight;
  }

  function enhanceServerMessages() {
    const messages = list.querySelectorAll(".message");
    let prevUser = null;
    messages.forEach((el) => {
      const user = el.dataset.user || "";
      if (prevUser === user) el.classList.add("stacked");
      prevUser = user;
    });
  }

  function connect() {
    const url = `${protocol()}://${window.location.host}/ws/chat/${roomSlug}/`;
    socket = new WebSocket(url);

    socket.onopen = () => {
      setStatus("connected", "Live");
      socket.send(JSON.stringify({ type: "join", username }));
      updatePresence();
    };

    socket.onclose = () => {
      setStatus("disconnected", "Reconnecting…");
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, 1500);
    };

    socket.onerror = () => {
      socket.close();
    };

    socket.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      if (data.type === "history") {
        (data.messages || []).forEach(appendMessage);
        list.scrollTop = list.scrollHeight;
      } else if (data.type === "chat_message") {
        appendMessage(data);
      } else if (data.type === "presence") {
        updatePresence(data.users);
      } else if (data.type === "error") {
        setStatus("disconnected", data.message || "Error");
      }
    };
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message || !socket || socket.readyState !== WebSocket.OPEN) return;

    socket.send(JSON.stringify({ type: "chat_message", message }));
    input.value = "";
    input.focus();
  });

  paintAllAvatars();
  enhanceServerMessages();
  connect();
  input.focus();
})();
