<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Copilot Chat Viewer</title>
  <style>
    :root{
      --bg:#0b1020; --panel:#111a33; --text:#e7ecff; --muted:#a9b4e3;
      --border:rgba(255,255,255,.10);
      --user:#2a4cff; --assistant:#1f2a52;
      --code:#0a0f1f;
      --chip:#0f1730;
    }
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
    header{position:sticky;top:0;z-index:5;background:rgba(11,16,32,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);padding:12px 16px}
    header .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .title{font-weight:700}
    .hint{color:var(--muted);font-size:.95rem}
    main{max-width:1100px;margin:0 auto;padding:16px}
    .card{border:1px solid var(--border);background:rgba(17,26,51,.65);border-radius:14px;padding:14px}
    .meta{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
    .meta a{color:var(--text)}
    .chip{display:inline-flex;gap:8px;align-items:center;background:var(--chip);border:1px solid var(--border);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:.9rem}
    .tabs{display:flex;gap:8px;margin:14px 0}
    button{border:1px solid var(--border);background:var(--chip);color:var(--text);padding:8px 10px;border-radius:10px;cursor:pointer}
    button[aria-pressed="true"]{background:#15224a}
    button:hover{background:#141f3e}
    input[type=file]{color:var(--muted)}

    .chat{display:flex;flex-direction:column;gap:12px}
    .msg{display:grid;grid-template-columns:130px 1fr;gap:12px;align-items:start}
    .who{color:var(--muted);font-size:.9rem;padding-top:10px}
    .bubble{border:1px solid var(--border);border-radius:14px;padding:12px 14px;background:var(--panel);overflow:auto}
    .msg.user .bubble{background:color-mix(in oklab, var(--user) 22%, var(--panel))}
    .msg.assistant .bubble{background:var(--assistant)}
    .ts{margin-top:8px;color:var(--muted);font-size:.8rem}

    pre,code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace}
    pre{background:var(--code);border:1px solid var(--border);border-radius:12px;padding:12px;overflow:auto}
    code{background:rgba(255,255,255,.06);padding:.15em .35em;border-radius:7px}
    pre code{background:transparent;padding:0}

    details{border:1px solid var(--border);border-radius:12px;background:rgba(10,15,31,.35);padding:10px}
    details summary{cursor:pointer;color:var(--text);font-weight:650}
    .filemeta{color:var(--muted);font-size:.9rem;margin-top:6px}
    .toolbar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:10px}
    .error{color:#ffb4b4;white-space:pre-wrap;background:rgba(255,0,0,.06);border:1px solid rgba(255,0,0,.25);padding:10px;border-radius:12px}
  </style>
</head>
<body>
<header>
  <div class="row">
    <div class="title">Copilot Chat Viewer</div>
    <div class="hint">Last inn <code>chat.json</code> og få lesbar “transcript”.</div>
    <div style="flex:1"></div>
    <input id="file" type="file" accept="application/json,.json" />
    <button id="loadLocal">Hent ./chat.json</button>
  </div>
</header>

<main>
  <div id="top" class="card">
    <div class="meta">
      <div class="chip"><span>Bruker:</span> <strong id="userLogin">—</strong></div>
      <div class="chip"><span>Tittel:</span> <strong id="threadName">—</strong></div>
      <div class="chip"><span>Tråd:</span> <a id="threadUrl" href="#" target="_blank" rel="noreferrer">—</a></div>
      <div class="chip"><span>Meldinger:</span> <strong id="count">0</strong></div>
    </div>

    <div class="tabs">
      <button id="tabChat" aria-pressed="true">Chat</button>
      <button id="tabFiles" aria-pressed="false">Filer</button>
    </div>

    <div id="viewChat">
      <div class="toolbar">
        <span class="hint">Tips: Meldinger rendres som Markdown.</span>
      </div>
      <div id="chat" class="chat" style="margin-top:12px"></div>
    </div>

    <div id="viewFiles" style="display:none">
      <div class="toolbar">
        <span class="hint">Viser <code>files</code>-seksjonen fra eksporten.</span>
      </div>
      <div id="files" style="margin-top:12px; display:flex; flex-direction:column; gap:10px"></div>
    </div>

    <div id="err" style="margin-top:12px"></div>
  </div>
</main>

<!-- Markdown + sanitizing -->
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>

<script>
  const el = (id) => document.getElementById(id);
  const chatEl = el("chat");
  const filesEl = el("files");
  const errEl = el("err");

  const tabChat = el("tabChat");
  const tabFiles = el("tabFiles");
  const viewChat = el("viewChat");
  const viewFiles = el("viewFiles");

  function setTab(which){
    const chat = which === "chat";
    tabChat.setAttribute("aria-pressed", String(chat));
    tabFiles.setAttribute("aria-pressed", String(!chat));
    viewChat.style.display = chat ? "" : "none";
    viewFiles.style.display = chat ? "none" : "";
  }
  tabChat.addEventListener("click", () => setTab("chat"));
  tabFiles.addEventListener("click", () => setTab("files"));

  function showError(e){
    errEl.innerHTML = "";
    const d = document.createElement("div");
    d.className = "error";
    d.textContent = String(e?.stack || e);
    errEl.appendChild(d);
  }

  function renderMarkdown(md){
    const html = marked.parse(md ?? "", { gfm:true, breaks:true });
    return DOMPurify.sanitize(html);
  }

  function formatTs(ts){
    if(!ts) return "";
    const d = new Date(ts);
    if(Number.isNaN(d.getTime())) return String(ts);
    // Bruk lokal tid (US/NO avhengig av maskin). Om du vil tvinge UTC: si ifra.
    return d.toLocaleString(undefined, { year:"numeric", month:"short", day:"2-digit", hour:"2-digit", minute:"2-digit" });
  }

  function isRootMessage(m){
    return m && m.id === "root" && !("content" in m);
  }

  function renderChat(messages){
    chatEl.innerHTML = "";
    const filtered = (messages || []).filter(m => !isRootMessage(m));
    for (const m of filtered){
      const row = document.createElement("div");
      row.className = "msg " + (m.role || "unknown");

      const who = document.createElement("div");
      who.className = "who";
      who.textContent = m.role || "unknown";

      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.innerHTML = renderMarkdown(m.content || "");

      const ts = document.createElement("div");
      ts.className = "ts";
      ts.textContent = formatTs(m.createdAt);

      const bubbleWrap = document.createElement("div");
      bubbleWrap.appendChild(bubble);
      if (ts.textContent) bubbleWrap.appendChild(ts);

      row.appendChild(who);
      row.appendChild(bubbleWrap);
      chatEl.appendChild(row);
    }
  }

  function renderFiles(files){
    filesEl.innerHTML = "";
    if(!files || typeof files !== "object"){
      filesEl.innerHTML = "<div class='hint'>Ingen filer i eksporten.</div>";
      return;
    }

    // files: { "index.html": [ {version, language, name, value, ...}, ... ], ... }
    for (const [fileName, versions] of Object.entries(files)){
      const wrapper = document.createElement("details");
      wrapper.open = false;

      const summary = document.createElement("summary");
      summary.textContent = fileName + (Array.isArray(versions) ? ` (${versions.length} versjon(er))` : "");
      wrapper.appendChild(summary);

      const body = document.createElement("div");
      body.style.marginTop = "10px";

      if (!Array.isArray(versions)) {
        body.innerHTML = "<div class='hint'>Uventet format: forventet liste.</div>";
      } else {
        for (const v of versions){
          const block = document.createElement("div");
          block.className = "card";
          block.style.marginTop = "10px";

          const meta = document.createElement("div");
          meta.className = "filemeta";
          meta.textContent =
            `version: ${v.version ?? "—"} • language: ${v.language ?? "—"} • messageId: ${v.messageId ?? "—"} • timestamp: ${v.timestamp ?? "—"}`;

          const pre = document.createElement("pre");
          const code = document.createElement("code");
          code.textContent = v.value ?? "";
          pre.appendChild(code);

          block.appendChild(meta);
          block.appendChild(pre);
          body.appendChild(block);
        }
      }

      wrapper.appendChild(body);
      filesEl.appendChild(wrapper);
    }
  }

  function renderAll(data){
    errEl.innerHTML = "";
    el("userLogin").textContent = data.currentUserLogin || "—";
    el("threadName").textContent = data.threadName || "—";

    const url = data.threadUrl || "";
    const a = el("threadUrl");
    a.textContent = url || "—";
    a.href = url || "#";

    const msgCount = Array.isArray(data.messages) ? data.messages.filter(m => !isRootMessage(m)).length : 0;
    el("count").textContent = String(msgCount);

    renderChat(data.messages || []);
    renderFiles(data.files || {});
  }

  async function loadUrl(url){
    const res = await fetch(url, { cache:"no-store" });
    if(!res.ok) throw new Error(`HTTP ${res.status} ved henting av ${url}`);
    return await res.json();
  }

  el("file").addEventListener("change", async (e) => {
    try{
      const f = e.target.files?.[0];
      if(!f) return;
      const text = await f.text();
      const data = JSON.parse(text);
      renderAll(data);
    } catch (err){
      showError(err);
    }
  });

  el("loadLocal").addEventListener("click", async () => {
    try{
      const data = await loadUrl("./chat.json");
      renderAll(data);
    } catch (err){
      showError(err);
    }
  });
</script>
</body>
</html>
