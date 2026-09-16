/* Medidor — cliente del chat. Todo lo que depende del modelo (que perillas
   mostrar, si el cache es explicito, cuanto cuesta) sale de /api/models: aca
   no hay ningun id de modelo escrito a mano. */

const $ = (id) => document.getElementById(id);
const api = async (method, url, body) => {
  const r = await fetch(url, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
  return data;
};

const state = {
  models: [],
  model: null,
  conversation: null,
  chats: [],
  params: { reasoning_effort: null, thinking_budget: null, json_schema: null },
  jsonSchemaOn: false,
  busy: false,
};

const num = (n) => (n ?? 0).toLocaleString("es-AR");
const money = (n) => "$" + (n ?? 0).toFixed(6);
const signed = (n) => (n < 0 ? "−" : "+") + "$" + Math.abs(n ?? 0).toFixed(6);
const perM = (p) => (p == null ? "—" : "$" + p.toFixed(p < 1 ? 3 : 2));
const escapeHtml = (s) => String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

/* ---- selector de modelo ------------------------------------------------ */

function logoEl(model, className = "brand-logo") {
  const img = document.createElement("img");
  img.className = className;
  img.src = model.logo;
  img.alt = "";
  img.width = 18;
  img.height = 18;
  return img;
}

function setModelLogo(model) {
  const host = $("model-logo");
  host.replaceChildren(logoEl(model, "brand-logo brand-logo--lg"));
}

function renderPicker() {
  const m = state.model;
  setModelLogo(m);
  $("model-label").textContent = m.label;
  $("model-meta").textContent =
    `${perM(m.pricing_per_million.prompt)}/M in · ${perM(m.pricing_per_million.completion)}/M out`;

  $("model-menu").replaceChildren(...state.models.map((x) => {
    const b = document.createElement("button");
    b.className = "opt";
    b.type = "button";
    b.setAttribute("role", "option");
    b.setAttribute("aria-selected", String(x.id === m.id));
    const logo = document.createElement("span");
    logo.className = "opt__logo";
    logo.append(logoEl(x));
    const text = document.createElement("span");
    text.innerHTML = `
      <span class="opt__name">${escapeHtml(x.label)}</span>
      <span class="opt__does">${escapeHtml(x.provider)} · ${escapeHtml(x.ejercita)}</span>`;
    const price = document.createElement("span");
    price.className = "opt__price";
    price.innerHTML = `${perM(x.pricing_per_million.prompt)}/M in
      <br>${perM(x.pricing_per_million.completion)}/M out`;
    b.append(logo, text, price);
    b.addEventListener("click", () => selectModel(x));
    return b;
  }));
}

function togglePicker(open) {
  const t = $("model-trigger"), menu = $("model-menu"), picker = t.closest(".picker");
  const next = open ?? menu.hidden;
  menu.hidden = !next;
  t.setAttribute("aria-expanded", String(next));
  picker?.classList.toggle("is-open", next);
}

async function selectModel(m) {
  togglePicker(false);
  if (m.id === state.model?.id) return;
  // Cambiar de modelo inicia conversacion nueva: lo pide la consigna, y ademas
  // el historial de un modelo no es contexto valido para otro.
  if (state.conversation?.prompt_count > 0) {
    const ok = confirm(
      `Cambiar a ${m.label} cierra esta conversación (${state.conversation.prompt_count} prompts) ` +
      `y abre una nueva. El log queda guardado. ¿Seguimos?`);
    if (!ok) return;
  }
  state.model = m;
  state.params.reasoning_effort = null;
  renderPicker();
  renderKnobs();
  renderEffort();
  renderGauge();
  await newConversation();
}

/* ---- perillas, derivadas de las capacidades del modelo ------------------ */

function knobBudget() {
  const wrap = document.createElement("div");
  wrap.className = "knob";
  wrap.innerHTML = `<span class="knob__label">Thinking</span>`;
  const input = document.createElement("input");
  input.type = "number";
  input.min = "0";
  input.step = "512";
  input.placeholder = "tokens";
  input.value = state.params.thinking_budget ?? "";
  input.addEventListener("change", () => {
    state.params.thinking_budget = input.value ? Number(input.value) : null;
  });
  wrap.append(input);
  return wrap;
}

function knobSchema() {
  const wrap = document.createElement("div");
  wrap.className = "knob";
  const label = document.createElement("label");
  label.className = "knob__check";
  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.checked = state.jsonSchemaOn;
  cb.addEventListener("change", () => {
    state.jsonSchemaOn = cb.checked;
    if (!cb.checked) state.params.json_schema = null;
    renderKnobs();
  });
  label.append(cb, Object.assign(document.createElement("span"), {
    className: "knob__label", textContent: "JSON Schema",
  }));
  wrap.append(label);

  if (state.jsonSchemaOn) {
    const ta = document.createElement("input");
    ta.type = "text";
    ta.className = "knob__schema";
    ta.placeholder = '{"type":"object", ...}';
    ta.value = state.params.json_schema ? JSON.stringify(state.params.json_schema) : "";
    ta.style.cssText = "width:100%;padding:5px 8px;border:1px solid var(--rule);border-radius:3px;font-family:var(--mono);font-size:12px;background:var(--paper)";
    ta.addEventListener("change", () => {
      try {
        state.params.json_schema = ta.value.trim() ? JSON.parse(ta.value) : null;
        ta.style.borderColor = "var(--rule)";
      } catch {
        ta.style.borderColor = "var(--burn)";
      }
    });
    wrap.append(ta);
  }
  return wrap;
}

function renderKnobs() {
  const caps = state.model.caps;
  const knobs = [];
  if (caps.includes("thinking_budget")) knobs.push(knobBudget());
  if (caps.includes("structured_output")) knobs.push(knobSchema());
  $("knobs").replaceChildren(...knobs);
}

function renderEffort() {
  const sel = $("effort");
  const has = state.model?.caps.includes("reasoning_effort");
  sel.hidden = !has;
  if (!has) return;
  const levels = ["off", ...state.model.efforts];
  sel.replaceChildren(...levels.map((level) => {
    const opt = document.createElement("option");
    opt.value = level === "off" ? "" : level;
    opt.textContent = level === "off" ? "effort: off" : `effort: ${level}`;
    return opt;
  }));
  sel.value = state.params.reasoning_effort ?? "";
}

/* ---- contexto estatico ------------------------------------------------- */

function renderGauge() {
  const tokens = Number($("prefix-count").dataset.tokens || 0);
  const min = state.model?.min_cache_tokens;
  const gauge = $("prefix-gauge");
  const note = $("prefix-note");

  if (!min) {
    gauge.hidden = true;
    $("prefix-hint").textContent =
      `${state.model?.provider ?? ""} cachea por prefijo automático`;
    note.textContent =
      "Este proveedor cachea solo: alcanza con que este bloque salga idéntico al principio de cada conversación. " +
      "Un carácter de diferencia y el prefijo deja de matchear.";
    return;
  }

  gauge.hidden = false;
  const fill = $("prefix-fill");
  const pct = Math.min(100, (tokens / min) * 100);
  fill.style.width = pct + "%";
  fill.classList.toggle("is-enough", tokens >= min);
  $("prefix-hint").textContent = `${state.model.provider} necesita ≥ ${num(min)} tokens`;
  note.textContent = tokens >= min
    ? `Alcanza el mínimo de ${num(min)} tokens: el bloque se marca con cache_control y el segundo mensaje debería dar hit (el cache vive ~5 minutos).`
    : `Faltan ${num(min - tokens)} tokens para el mínimo de ${num(min)}. Por debajo de eso ${state.model.provider} no cachea, por más que se mande la marca.`;
}

function setPrefixCount(tokens) {
  const el = $("prefix-count");
  el.dataset.tokens = tokens;
  el.textContent = `~${num(tokens)} tok`;
  renderGauge();
}

/* ---- sidebar de chats -------------------------------------------------- */

function modelLabel(id) {
  return state.models.find((m) => m.id === id)?.label ?? id;
}

function modelOf(id) {
  return state.models.find((m) => m.id === id) ?? null;
}

function renderChatList() {
  const list = $("chat-list");
  list.replaceChildren(...state.chats.map((c) => {
    const row = document.createElement("div");
    row.className = "chat-item" + (c.id === state.conversation?.id ? " is-active" : "");

    const open = document.createElement("button");
    open.type = "button";
    open.className = "chat-item__open";

    const avatar = document.createElement("span");
    avatar.className = "chat-item__pfp";
    avatar.setAttribute("aria-hidden", "true");
    const model = modelOf(c.model_id);
    if (model) avatar.append(logoEl(model, "brand-logo brand-logo--pfp"));

    const text = document.createElement("span");
    text.className = "chat-item__text";
    text.innerHTML = `
      <span class="chat-item__title">${escapeHtml(c.title || "Chat nuevo")}</span>
      <span class="chat-item__meta">${escapeHtml(modelLabel(c.model_id))} · ${num(c.prompt_count)} prompts</span>`;

    open.append(avatar, text);
    open.addEventListener("click", () => openConversation(c.id));

    const del = document.createElement("button");
    del.type = "button";
    del.className = "chat-item__delete";
    del.title = "Eliminar chat";
    del.setAttribute("aria-label", "Eliminar chat");
    del.innerHTML = `<svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true"><path fill="currentColor" d="M9 3h6l1 2h4v2H4V5h4l1-2zm1 6h2v9h-2V9zm4 0h2v9h-2V9zM7 9h2v9H7V9zm-1 12h12a1 1 0 0 0 1-1V8H5v12a1 1 0 0 0 1 1z"/></svg>`;
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteConversation(c.id);
    });

    row.append(open, del);
    return row;
  }));
}

async function deleteConversation(id) {
  if (!confirm("¿Eliminar este chat? Se borra de disco.")) return;
  const wasActive = state.conversation?.id === id;
  await api("DELETE", `/api/conversations/${id}`);
  await refreshChatList();
  if (!wasActive) return;
  if (state.chats.length) await openConversation(state.chats[0].id);
  else await newConversation();
}

async function refreshChatList() {
  const { conversations } = await api("GET", "/api/conversations");
  state.chats = conversations;
  renderChatList();
}

/* ---- render del hilo --------------------------------------------------- */

marked.setOptions({
  gfm: true,
  breaks: true,
});

function renderBody(text) {
  const raw = marked.parse(text ?? "", { async: false });
  return DOMPurify.sanitize(raw, {
    USE_PROFILES: { html: true },
  });
}

function messageEl(role, text, params) {
  const el = document.createElement("article");
  el.className = `msg msg--${role}`;
  const who = document.createElement("div");
  who.className = "msg__who";
  who.textContent = role === "user" ? "Vos" : role === "error" ? "Error" : state.model.label;
  if (params) {
    const p = document.createElement("span");
    p.className = "msg__params";
    p.textContent = params;
    who.append(p);
  }
  const body = document.createElement("div");
  body.className = "msg__body";
  if (role === "assistant") body.innerHTML = renderBody(text);
  else body.textContent = text;
  el.append(who, body);
  return el;
}

function readingEl(u) {
  const el = document.createElement("div");
  el.className = "read";
  const total = Math.max(u.prompt_tokens + u.completion_tokens, 1);
  const pct = (n) => (n / total) * 100 + "%";
  el.innerHTML = `
    <div class="read__bar" role="img" aria-label="composición de los tokens de este turno">
      <span class="read__seg--cached" style="width:${pct(u.cached_tokens)}"></span>
      <span class="read__seg--fresh"  style="width:${pct(u.fresh_prompt_tokens)}"></span>
      <span class="read__seg--out"    style="width:${pct(u.completion_tokens)}"></span>
    </div>
    <div class="read__nums">
      <span>entrada <b>${num(u.prompt_tokens)}</b></span>
      <span class="${u.cache_hit ? "is-cache" : ""}">cacheados <b>${num(u.cached_tokens)}</b></span>
      <span>salida <b>${num(u.completion_tokens)}</b></span>
      <span>razonamiento <b>${num(u.reasoning_tokens)}</b></span>
      <span>costo <b>${money(u.cost)}</b></span>
      <span class="${u.cache_discount < 0 ? "is-burn" : u.cache_discount > 0 ? "is-cache" : ""}">cache <b>${signed(u.cache_discount)}</b></span>
    </div>`;
  return el;
}

function thread() {
  let inner = document.querySelector(".thread__inner");
  if (!inner) {
    inner = document.createElement("div");
    inner.className = "thread__inner";
    $("thread").append(inner);
  }
  return inner;
}

function renderCut() {
  const c = document.createElement("div");
  const hay = (state.conversation?.static_context || "").trim().length > 0;
  c.className = hay ? "cut" : "cut cut--none";
  c.textContent = hay
    ? `Fin del prefijo cacheable · ~${num(state.conversation.static_context_tokens)} tokens`
    : "Sin prefijo estático";
  return c;
}

function renderThreadFromTurns(turns) {
  $("thread").replaceChildren();
  const inner = thread();
  inner.append(renderCut());
  for (const t of turns) {
    inner.append(messageEl("user", t.prompt));
    inner.append(messageEl("assistant", t.reply, t.params_label));
    inner.append(readingEl(t.usage));
  }
  scrollDown();
}

function updateMeter() {
  const c = state.conversation;
  const t = c?.totals ?? {};
  $("t-prompts").textContent = num(c?.prompt_count ?? 0);
  $("t-in").textContent = num(t.prompt_tokens);
  $("t-cached").textContent = num(t.cached_tokens);
  $("t-out").textContent = num(t.completion_tokens);
  $("t-reason").textContent = num(t.reasoning_tokens);
  $("t-cost").textContent = money(t.cost ?? 0);
  $("m-title").textContent = c?.title || "Chat nuevo";
  $("m-path").textContent = c?.chat_dir ?? "";
  $("t-log").textContent = c?.log_path ?? "";
}

const scrollDown = () => { $("thread").scrollTop = $("thread").scrollHeight; };
const focusInput = () => { $("input").focus(); };

/* ---- conversacion ------------------------------------------------------ */

async function newConversation() {
  state.conversation = await api("POST", "/api/conversations", { model_id: state.model.id });
  $("thread").replaceChildren();
  thread().append(renderCut());
  updateMeter();
  await refreshChatList();
  focusInput();
}

function renderNewMenu() {
  const menu = $("new-menu");
  menu.replaceChildren(...state.models.map((m) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "new-menu__item";
    b.setAttribute("role", "menuitem");
    const pfp = document.createElement("span");
    pfp.className = "new-menu__pfp";
    pfp.append(logoEl(m, "brand-logo brand-logo--pfp"));
    const text = document.createElement("span");
    text.innerHTML = `
      <span class="new-menu__name">${escapeHtml(m.label)}</span>
      <span class="new-menu__meta">${escapeHtml(m.provider)} · slot ${m.slot}</span>`;
    b.append(pfp, text);
    b.addEventListener("click", () => startChatWithModel(m));
    return b;
  }));
}

function toggleNewMenu(open) {
  const btn = $("new-chat"), menu = $("new-menu");
  const next = open ?? menu.hidden;
  menu.hidden = !next;
  btn.setAttribute("aria-expanded", String(next));
}

async function startChatWithModel(m) {
  toggleNewMenu(false);
  state.model = m;
  state.params.reasoning_effort = null;
  renderPicker();
  renderKnobs();
  renderEffort();
  renderGauge();
  await newConversation();
}

async function openConversation(id) {
  if (state.busy) return;
  if (id === state.conversation?.id) {
    focusInput();
    return;
  }
  const data = await api("GET", `/api/conversations/${id}`);
  state.conversation = data;
  const model = state.models.find((m) => m.id === data.model_id);
  if (model) {
    state.model = model;
    renderPicker();
    renderKnobs();
    renderEffort();
    renderGauge();
  }
  renderThreadFromTurns(data.turns || []);
  updateMeter();
  renderChatList();
  focusInput();
}

async function readSSE(response, onEvent) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const block of parts) {
      let event = "message";
      const dataLines = [];
      for (const line of block.split("\n")) {
        if (line.startsWith("event: ")) event = line.slice(7).trim();
        else if (line.startsWith("data: ")) dataLines.push(line.slice(6));
      }
      if (!dataLines.length) continue;
      onEvent(event, JSON.parse(dataLines.join("\n")));
    }
  }
}

async function send(text) {
  if (state.busy) return;
  state.busy = true;
  $("send").disabled = true;

  const inner = thread();
  inner.append(messageEl("user", text));
  const assistant = messageEl("assistant", "");
  const bodyEl = assistant.querySelector(".msg__body");
  bodyEl.textContent = "";
  inner.append(assistant);
  scrollDown();

  let reply = "";
  try {
    const r = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: state.conversation.id,
        text,
        params: state.params,
      }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }

    let finished = false;
    await readSSE(r, (event, data) => {
      if (event === "delta") {
        reply += data.text;
        bodyEl.innerHTML = renderBody(reply);
        scrollDown();
      } else if (event === "done") {
        finished = true;
        if (data.turn.params_label) {
          const p = document.createElement("span");
          p.className = "msg__params";
          p.textContent = data.turn.params_label;
          assistant.querySelector(".msg__who").append(p);
        }
        bodyEl.innerHTML = renderBody(data.turn.reply);
        inner.append(readingEl(data.turn.usage));
        state.conversation = { ...state.conversation, ...data };
        updateMeter();
        refreshChatList();
      } else if (event === "error") {
        throw new Error(data.detail || "Error de streaming");
      }
    });
    if (!finished) throw new Error("El stream terminó sin evento done");
  } catch (e) {
    assistant.remove();
    inner.append(messageEl("error", e.message));
  } finally {
    state.busy = false;
    $("send").disabled = false;
    scrollDown();
  }
}

/* ---- arranque ---------------------------------------------------------- */

function wire() {
  $("model-trigger").addEventListener("click", (e) => {
    e.stopPropagation();
    togglePicker();
  });
  $("new-chat").addEventListener("click", (e) => {
    e.stopPropagation();
    renderNewMenu();
    toggleNewMenu();
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".picker")) togglePicker(false);
    if (!e.target.closest(".new-wrap")) toggleNewMenu(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      togglePicker(false);
      toggleNewMenu(false);
    }
  });

  $("effort").addEventListener("change", () => {
    state.params.reasoning_effort = $("effort").value || null;
  });

  // Scrollbar del hilo: visible al hover/scroll, fade lento al quieto.
  const threadEl = $("thread");
  let scrollFadeTimer = null;
  const bumpScroll = () => {
    threadEl.classList.add("is-scrolling");
    clearTimeout(scrollFadeTimer);
    scrollFadeTimer = setTimeout(() => threadEl.classList.remove("is-scrolling"), 1200);
  };
  threadEl.addEventListener("scroll", bumpScroll, { passive: true });
  threadEl.addEventListener("pointermove", bumpScroll, { passive: true });

  $("prefix-toggle").addEventListener("click", () => {
    const open = $("prefix-body").hidden;
    $("prefix-body").hidden = !open;
    $("prefix-toggle").setAttribute("aria-expanded", String(open));
  });

  $("prefix-text").addEventListener("input", () =>
    setPrefixCount(Math.floor($("prefix-text").value.length / 4)));

  $("prefix-save").addEventListener("click", async () => {
    const res = await api("PUT", "/api/static-context", { text: $("prefix-text").value });
    setPrefixCount(res.tokens);
    if (state.conversation?.prompt_count === 0) {
      await newConversation();
      $("prefix-saved").textContent = "guardado · ya rige en esta conversación";
    } else {
      $("prefix-saved").textContent = "guardado · rige desde la próxima conversación";
    }
    setTimeout(() => ($("prefix-saved").textContent = ""), 5000);
  });

  const input = $("input");
  input.addEventListener("input", () => {
    input.style.height = "auto";
    input.style.height = input.scrollHeight + "px";
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      $("composer").requestSubmit();
    }
  });

  $("composer").addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    input.style.height = "";
    await send(text);
  });
}

(async function init() {
  wire();
  const { models } = await api("GET", "/api/models");
  state.models = models;
  state.model = models[0];
  renderPicker();
  renderKnobs();
  renderEffort();

  const ctx = await api("GET", "/api/static-context");
  $("prefix-text").value = ctx.text;
  setPrefixCount(ctx.tokens);

  await refreshChatList();
  if (state.chats.length) {
    await openConversation(state.chats[0].id);
  } else {
    await newConversation();
  }
})();
