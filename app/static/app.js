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
  params: { reasoning_effort: null, thinking_budget: null, json_schema: null },
  jsonSchemaOn: false,
  busy: false,
};

const num = (n) => (n ?? 0).toLocaleString("es-AR");
const money = (n) => "$" + (n ?? 0).toFixed(6);
const signed = (n) => (n < 0 ? "−" : "+") + "$" + Math.abs(n ?? 0).toFixed(6);
const perM = (p) => (p == null ? "—" : "$" + p.toFixed(p < 1 ? 3 : 2));

/* ---- selector de modelo ------------------------------------------------ */

function renderPicker() {
  const m = state.model;
  $("model-slot").textContent = m.slot;
  $("model-label").textContent = m.label;
  $("model-meta").textContent =
    `${m.id}  ·  ${perM(m.pricing_per_million.prompt)}/M in  ·  ${perM(m.pricing_per_million.completion)}/M out`;

  $("model-menu").replaceChildren(...state.models.map((x) => {
    const b = document.createElement("button");
    b.className = "opt";
    b.type = "button";
    b.setAttribute("role", "option");
    b.setAttribute("aria-selected", String(x.id === m.id));
    b.innerHTML = `
      <span class="opt__slot">${x.slot}</span>
      <span>
        <span class="opt__name">${x.label}</span>
        <span class="opt__does">${x.provider} · ${x.ejercita}</span>
      </span>
      <span class="opt__price">${perM(x.pricing_per_million.prompt)}/M in
        <br>${perM(x.pricing_per_million.completion)}/M out</span>`;
    b.addEventListener("click", () => selectModel(x));
    return b;
  }));
}

function togglePicker(open) {
  const t = $("model-trigger"), menu = $("model-menu");
  const next = open ?? menu.hidden;
  menu.hidden = !next;
  t.setAttribute("aria-expanded", String(next));
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
  renderPicker();
  renderKnobs();
  renderGauge();
  await newConversation();
}

/* ---- perillas, derivadas de las capacidades del modelo ------------------ */

function knobEffort() {
  const wrap = document.createElement("div");
  wrap.className = "knob";
  wrap.innerHTML = `<span class="knob__label">Effort</span>`;
  const seg = document.createElement("div");
  seg.className = "seg";
  for (const level of ["off", ...state.model.efforts]) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = level;
    const value = level === "off" ? null : level;
    b.setAttribute("aria-pressed", String(state.params.reasoning_effort === value));
    b.addEventListener("click", () => {
      state.params.reasoning_effort = value;
      renderKnobs();
    });
    seg.append(b);
  }
  wrap.append(seg);
  return wrap;
}

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
    ta.style.cssText = "width:230px;padding:5px 8px;border:1px solid var(--rule);border-radius:3px;font-family:var(--mono);font-size:12px;background:var(--paper)";
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
  if (caps.includes("reasoning_effort")) knobs.push(knobEffort());
  if (caps.includes("thinking_budget")) knobs.push(knobBudget());
  if (caps.includes("structured_output")) knobs.push(knobSchema());
  $("knobs").replaceChildren(...knobs);
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

/* ---- render del hilo --------------------------------------------------- */

const escapeHtml = (s) => s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function renderBody(text) {
  // Markdown minimo: los modelos responden con bloques de codigo y poco mas.
  const parts = escapeHtml(text).split(/```(\w*)\n?/);
  let html = "";
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) continue;             // captura del lenguaje: solo marca el corte
    const inCode = (i / 2) % 2 === 1;      // los tramos pares alternan texto y codigo
    html += inCode
      ? `<pre><code>${parts[i]}</code></pre>`
      : parts[i].replace(/`([^`\n]+)`/g, "<code>$1</code>");
  }
  return html;
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

function updateMeter() {
  const c = state.conversation;
  const t = c?.totals ?? {};
  $("t-prompts").textContent = num(c?.prompt_count ?? 0);
  $("t-in").textContent = num(t.prompt_tokens);
  $("t-cached").textContent = num(t.cached_tokens);
  $("t-out").textContent = num(t.completion_tokens);
  $("t-reason").textContent = num(t.reasoning_tokens);
  $("t-cost").textContent = money(t.cost ?? 0);
  $("t-log").textContent = c?.log_path ?? "";
}

const scrollDown = () => { $("thread").scrollTop = $("thread").scrollHeight; };

/* ---- conversacion ------------------------------------------------------ */

async function newConversation() {
  state.conversation = await api("POST", "/api/conversations", { model_id: state.model.id });
  $("thread").replaceChildren();
  thread().append(renderCut());
  updateMeter();
}

async function send(text) {
  if (state.busy) return;
  state.busy = true;
  $("send").disabled = true;

  const inner = thread();
  inner.append(messageEl("user", text));
  const pending = document.createElement("div");
  pending.className = "pending";
  pending.textContent = "midiendo…";
  inner.append(pending);
  scrollDown();

  try {
    const res = await api("POST", "/api/chat", {
      conversation_id: state.conversation.id,
      text,
      params: state.params,
    });
    pending.remove();
    inner.append(messageEl("assistant", res.turn.reply, res.turn.params_label));
    inner.append(readingEl(res.turn.usage));
    state.conversation = { ...state.conversation, ...res };
    updateMeter();
  } catch (e) {
    pending.remove();
    inner.append(messageEl("error", e.message));
  } finally {
    state.busy = false;
    $("send").disabled = false;
    scrollDown();
  }
}

/* ---- arranque ---------------------------------------------------------- */

function wire() {
  $("model-trigger").addEventListener("click", () => togglePicker());
  document.addEventListener("click", (e) => {
    if (!e.target.closest(".picker")) togglePicker(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") togglePicker(false);
  });

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

  const ctx = await api("GET", "/api/static-context");
  $("prefix-text").value = ctx.text;
  setPrefixCount(ctx.tokens);

  await newConversation();
})();
