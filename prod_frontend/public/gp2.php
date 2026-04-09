<!doctype html>
<html lang="no">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Copilot Chat Arkiv</title>
  <style>
    :root{
      --bg:#0b1020; --panel:#111a33; --text:#e7ecff; --muted:#a9b4e3;
      --border:rgba(255,255,255,.10);
      --user:#2a4cff; --assistant:#1f2a52; --code:#0a0f1f; --chip:#0f1730;
    }
    *{box-sizing:border-box}
    body{margin:0;background:var(--bg);color:var(--text);font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
    header{position:sticky;top:0;z-index:5;background:rgba(11,16,32,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--border);padding:12px 16px}
    header .row{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
    .title{font-weight:800}
    .hint{color:var(--muted);font-size:.95rem}
    main{max-width:1250px;margin:0 auto;padding:16px;display:grid;grid-template-columns:380px 1fr;gap:14px}
    @media (max-width: 980px){ main{grid-template-columns:1fr} }
    .card{border:1px solid var(--border);background:rgba(17,26,51,.65);border-radius:14px;padding:14px;min-height:100px}
    input, button{border:1px solid var(--border);background:var(--chip);color:var(--text);padding:8px 10px;border-radius:10px}
    button{cursor:pointer}
    button:hover{background:#141f3e}
    .list{display:flex;flex-direction:column;gap:10px;max-height:70vh;overflow:auto;padding-right:6px}
    .item{border:1px solid var(--border);border-radius:12px;padding:10px;background:rgba(10,15,31,.35);cursor:pointer}
    .item:hover{background:rgba(15,23,48,.55)}
    .item.active{outline:2px solid rgba(42,76,255,.55)}
    .item .name{font-weight:750}
    .item .meta{color:var(--muted);font-size:.85rem;margin-top:4px;display:flex;gap:10px;flex-wrap:wrap}

    .metaRow{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
    .chip{display:inline-flex;gap:8px;align-items:center;background:var(--chip);border:1px solid var(--border);border-radius:999px;padding:6px 10px;color:var(--muted);font-size:.9rem}

    .chat{display:flex;flex-direction:column;gap:12px}
    .msg{display:grid;grid-template-columns:120px 1fr;gap:12px;align-items:start}
    .who{color:var(--muted);font-size:.9rem;padding-top:10px}
    .bubble{border:1px solid var(--border);border-radius:14px;padding:12px 14px;background:var(--panel);overflow:auto}
    .msg.user .bubble{background:color-mix(in oklab, var(--user) 22%, var(--panel))}
    .msg.assistant .bubble{background:var(--assistant)}
    .ts{margin-top:8px;color:var(--muted);font-size:.8rem}
    pre,code{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace}
    pre{background:var(--code);border:1px solid var(--border);border-radius:12px;padding:12px;overflow:auto}
    code{background:rgba(255,255,255,.06);padding:.15em .35em;border-radius:7px}
    pre code{background:transparent;padding:0}
    .error{color:#ffb4b4;white-space:pre-wrap;background:rgba(255,0,0,.06);border:1px solid rgba(255,0,0,.25);padding:10px;border-radius:12px}
  </style>
</head>
<body>
<header>
  <div class="row">
    <div class="title">Copilot Chat Arkiv</div>
    <div class="hint">Velg en chat fra venstre. Kilde: <code>manifest.json</code>.</div>
    <div style="flex:1"></div>
    <button id="reload">Oppdater liste</button>
  </div>
</header>

<main>
  <section class="card">
    <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:10px">
      <input id="q" placeholder="Søk (tittel/innhold)..." style="flex:1; min-width: 200px" />
      <button id="clear">Nullstill</button>
    </div>
    <div class="hint" id="count"></div>
    <div class="list" id="list"></div>
  </section>

  <section class="card">
    <div class="metaRow">
      <span class="chip"><span>Tittel:</span> <strong id="threadName">—</strong></span>
      <span class="chip"><span>Bruker:</span> <strong id="userLogin">—</strong></span>
      <span class="chip"><span>Meldinger:</span> <strong id="msgCount">—</strong></span>
      <span class="chip"><span>Tråd:</span> <a id="threadUrl" href="#" target="_blank" rel="noreferrer">—</a></span>
      <span class="chip"><span>Fil:</span> <code id="fileName">—</code></span>
    </div>

    <div id="err"></div>
    <div id="chat" class="chat"></div>
  </section>
</main>

<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dompurify@3.1.6/dist/purify.min.js"></script>

<script>
  const el = (id) => document.getElementById(id);
  const listEl = el("list");
  const chatEl = el("chat");
  const errEl = el("err");

  let index = [];      // [{ file, title, snippet, msgCount, dateMin, dateMax, data? }]
  let activeFile = ""; // manifest entry .file

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
    return d.toLocaleString(undefined, { year:"numeric", month:"short", day:"2-digit", hour:"2-digit", minute:"2-digit" });
  }

  function isRootMessage(m){
    return m && m.id === "root" && !("content" in m);
  }

  function computeDateRange(messages){
    const ts = (messages || [])
      .map(m => m?.createdAt)
      .filter(Boolean)
      .map(t => new Date(t))
      .filter(d => !Number.isNaN(d.getTime()))
      .sort((a,b)=>a-b);
    return {
      min: ts[0] ? ts[0].toISOString() : "",
      max: ts[ts.length-1] ? ts[ts.length-1].toISOString() : ""
    };
  }

  function buildSnippet(messages){
    const m = (messages || []).find(x => (x?.content || "").trim().length > 0);
    if(!m) return "";
    const s = String(m.content).replace(/\s+/g, " ").trim();
    return s.slice(0, 120);
  }

  async function fetchJson(path){
    const res = await fetch(path, { cache:"no-store" });
    if(!res.ok) throw new Error(`HTTP ${res.status} ved henting av ${path}`);
    return await res.json();
  }

  async function loadManifest(){
    const manifest = await fetchJson("./manifest.json"); // forventer array
    if(!Array.isArray(manifest)) throw new Error("manifest.json må være en JSON-array av objekter som {file: '...'}");

    // bygg en lett indeks (leser hver chat for å hente tittel/metadata)
    const entries = [];
    for (const m of manifest){
      if(!m || typeof m.file !== "string") continue;
      try{
        const data = await fetchJson(m.file);
        const msgs = Array.isArray(data.messages) ? data.messages.filter(x => !isRootMessage(x)) : [];
        const range = computeDateRange(msgs);
        entries.push({
          file: m.file,
          title: data.threadName || "(uten tittel)",
          user: data.currentUserLogin || "",
          msgCount: msgs.length,
          dateMin: range.min,
          dateMax: range.max,
          snippet: buildSnippet(msgs)
        });
      }catch(e){
        entries.push({ file: m.file, title: "(kunne ikke lastes)", msgCount: 0, dateMin:"", dateMax:"", snippet: String(e) });
      }
    }

    // sorter nyeste først (dateMax)
    entries.sort((a,b) => (b.dateMax || "").localeCompare(a.dateMax || ""));
    index = entries;
  }

  function renderList(){
    const q = el("q").value.trim().toLowerCase();
    listEl.innerHTML = "";

    const filtered = index.filter(x => {
      if(!q) return true;
      return (
        (x.title || "").toLowerCase().includes(q) ||
        (x.snippet || "").toLowerCase().includes(q) ||
        (x.file || "").toLowerCase().includes(q)
      );
    });

    el("count").textContent = `${filtered.length} / ${index.length} chatter`;

    for (const item of filtered){
      const d = document.createElement("div");
      d.className = "item" + (item.file === activeFile ? " active" : "");
      d.addEventListener("click", () => openChat(item.file));

      const name = document.createElement("div");
      name.className = "name";
      name.textContent = item.title;

      const meta = document.createElement("div");
      meta.className = "meta";
      meta.innerHTML = `
        <span>${item.msgCount} meldinger</span>
        <span>${item.dateMax ? formatTs(item.dateMax) : ""}</span>
        <span style="opacity:.9">${item.file}</span>
      `.trim();

      const snip = document.createElement("div");
      snip.className = "hint";
      snip.style.marginTop = "6px";
      snip.textContent = item.snippet || "";

      d.appendChild(name);
      d.appendChild(meta);
      if (snip.textContent) d.appendChild(snip);
      listEl.appendChild(d);
    }
  }

  function renderChat(data, file){
    errEl.innerHTML = "";
    chatEl.innerHTML = "";

    el("threadName").textContent = data.threadName || "—";
    el("userLogin").textContent = data.currentUserLogin || "—";
    el("fileName").textContent = file || "—";

    const url = data.threadUrl || "";
    const a = el("threadUrl");
    a.textContent = url || "—";
    a.href = url || "#";

    const messages = Array.isArray(data.messages) ? data.messages.filter(m => !isRootMessage(m)) : [];
    el("msgCount").textContent = String(messages.length);

    for (const m of messages){
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

      const wrap = document.createElement("div");
      wrap.appendChild(bubble);
      if(ts.textContent) wrap.appendChild(ts);

      row.appendChild(who);
      row.appendChild(wrap);
      chatEl.appendChild(row);
    }
  }

  async function openChat(file){
    try{
      activeFile = file;
      renderList(); // oppdater highlight

      const data = await fetchJson(file);
      renderChat(data, file);

      // oppdater URL så du kan bookmarke: index.html?file=...
      const u = new URL(window.location.href);
      u.searchParams.set("file", file);
      history.replaceState(null, "", u.toString());
    }catch(e){
      showError(e);
    }
  }

  async function init(){
    try{
      await loadManifest();
      renderList();

      const u = new URL(window.location.href);
      const file = u.searchParams.get("file");
      if(file){
        await openChat(file);
      } else if (index[0]?.file) {
        await openChat(index[0].file);
      }
    }catch(e){
      showError(e);
    }
  }

  el("q").addEventListener("input", renderList);
  el("clear").addEventListener("click", () => { el("q").value=""; renderList(); });
  el("reload").addEventListener("click", async () => { await init(); });

  init();
</script>
</body>
</html>
