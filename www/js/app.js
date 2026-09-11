/* M.L26 offline — accounts, career, match sim, no server. */
(function () {
  const FORMATIONS = {
    "4-3-3": ["GK", "LB", "CB", "CB", "RB", "CM", "CM", "CM", "LW", "ST", "RW"],
    "4-2-3-1": ["GK", "LB", "CB", "CB", "RB", "CDM", "CDM", "CAM", "LW", "ST", "RW"],
    "4-4-2": ["GK", "LB", "CB", "CB", "RB", "LM", "CM", "CM", "RM", "ST", "ST"],
    "3-5-2": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "CM", "RM", "ST", "ST"],
    "3-4-3": ["GK", "CB", "CB", "CB", "LM", "CM", "CM", "RM", "LW", "ST", "RW"]
  };
  const LINE = { GK: "gk", LB: "def", CB: "def", RB: "def", CDM: "mid", CM: "mid", CAM: "mid", LM: "mid", RM: "mid", LW: "att", RW: "att", ST: "att" };
  const NEAR = {
    ST: ["LW", "RW", "CAM"], LW: ["ST", "LM", "CAM"], RW: ["ST", "RM", "CAM"],
    CAM: ["CM", "ST"], CM: ["CDM", "CAM", "LM", "RM"], CDM: ["CM", "CB"],
    LB: ["LM", "CB"], RB: ["RM", "CB"], CB: ["CDM", "LB", "RB"]
  };

  let PACK = null;
  let W = null;
  let USER = null;
  const $ = (s) => document.querySelector(s);
  const app = () => $("#app");

  function idb() {
    return new Promise((ok, err) => {
      const r = indexedDB.open("ml26", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("kv");
      r.onsuccess = () => ok(r.result);
      r.onerror = () => err(r.error);
    });
  }
  async function idbGet(k) {
    const db = await idb();
    return new Promise((ok) => {
      const q = db.transaction("kv").objectStore("kv").get(k);
      q.onsuccess = () => ok(q.result);
      q.onerror = () => ok(null);
    });
  }
  async function idbSet(k, v) {
    const db = await idb();
    return new Promise((ok, err) => {
      const q = db.transaction("kv", "readwrite").objectStore("kv").put(v, k);
      q.onsuccess = () => ok();
      q.onerror = () => err(q.error);
    });
  }

  function users() {
    try { return JSON.parse(localStorage.getItem("ml26.users") || "{}"); } catch { return {}; }
  }
  function saveUsers(u) { localStorage.setItem("ml26.users", JSON.stringify(u)); }
  function suggestions(name) {
    const u = users();
    const out = [];
    for (let i = 1; i < 30 && out.length < 3; i++) {
      for (const c of [name + i, name + "_" + i]) if (!u[c] && !out.includes(c)) out.push(c);
    }
    return out;
  }
  function register(name) {
    name = (name || "").trim().toLowerCase();
    if (name.length < 3) return { ok: false, msg: "Name needs 3+ letters." };
    const u = users();
    if (u[name]) return { ok: false, msg: name + " is taken. Try " + suggestions(name).join(", ") + "." };
    u[name] = { name, created: Date.now() };
    saveUsers(u);
    localStorage.setItem("ml26.session", name);
    USER = name;
    return { ok: true };
  }
  function login(name) {
    name = (name || "").trim().toLowerCase();
    const u = users();
    if (!u[name]) return { ok: false, msg: "No account with that name. Create one first." };
    localStorage.setItem("ml26.session", name);
    USER = name;
    return { ok: true };
  }

  function club(w, id) { return w.clubs.find((c) => c.id === id) || { id: 0, name: "?", short: "?" }; }
  function squad(w, cid) { return w.players.filter((p) => p.club_id === cid && !p.retired); }
  function leagueOf(w, cid) { return w.leagues.find((l) => l.id === club(w, cid).league_id); }
  function roleOf(p) { return (p.roles && p.roles[0] && p.roles[0].code) || "CM"; }
  function slotRole(s) { return String(s).replace(/[0-9]/g, ""); }
  function posFit(p, slot) {
    slot = slotRole(slot);
    const ovr = +p.overall || 70;
    const prim = roleOf(p);
    const codes = new Set((p.roles || []).map((r) => r.code).concat([prim]));
    if (slot === "GK" || prim === "GK") {
      if (slot === "GK" && prim === "GK") return { dot: "green", shown: ovr, m: 1 };
      return { dot: "red", shown: Math.max(40, ovr * 0.58), m: 0.58 };
    }
    if (codes.has(slot)) return { dot: "green", shown: ovr, m: 1 };
    if ((NEAR[prim] || []).includes(slot) || LINE[slot] === LINE[prim]) return { dot: "amber", shown: ovr * 0.955, m: 0.955 };
    return { dot: "red", shown: Math.max(40, ovr * 0.72), m: 0.72 };
  }
  function xiStrength(xi) {
    const lines = { gk: [], def: [], mid: [], att: [] };
    Object.entries(xi).forEach(([slot, p]) => {
      if (!p) return;
      const v = (+p.overall || 70) * posFit(p, slot).m * Math.max(0.55, (+p.condition || 88) / 100);
      lines[LINE[slotRole(slot)] || "mid"].push(v);
    });
    const avg = (a) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 62);
    const gk = avg(lines.gk), de = avg(lines.def), mi = avg(lines.mid), at = avg(lines.att);
    return { total: +(gk * 0.15 + de * 0.27 + mi * 0.27 + at * 0.31).toFixed(1), gk, def: de, mid: mi, att: at };
  }
  function autoXi(w, cid, form) {
    const slots = FORMATIONS[form] || FORMATIONS["4-3-3"];
    const pool = squad(w, cid).slice().sort((a, b) => b.overall - a.overall);
    const used = new Set();
    const xi = {};
    slots.forEach((role, i) => {
      const key = slots.filter((s) => s === role).length > 1 ? role + (slots.slice(0, i + 1).filter((s) => s === role).length) : role;
      let pick = pool.find((p) => !used.has(p.id) && roleOf(p) === role);
      if (!pick) pick = pool.find((p) => !used.has(p.id) && LINE[roleOf(p)] === LINE[role]);
      if (!pick) pick = pool.find((p) => !used.has(p.id));
      if (pick) { used.add(pick.id); xi[key] = pick.id; }
    });
    return xi;
  }
  function resolveXi(w, ids) {
    const map = {};
    Object.entries(ids || {}).forEach(([k, pid]) => {
      const p = w.players.find((x) => x.id === pid);
      if (p) map[k] = p;
    });
    return map;
  }
  function tableFor(w, lid) {
    const rows = {};
    w.clubs.filter((c) => c.league_id === lid).forEach((c) => { rows[c.id] = { club_id: c.id, name: c.name, short: c.short, p: 0, w: 0, d: 0, l: 0, gf: 0, ga: 0, pts: 0 }; });
    w.fixtures.forEach((f) => {
      if (f.league_id !== lid || !f.played) return;
      const h = rows[f.home_id], a = rows[f.away_id];
      if (!h || !a) return;
      h.p++; a.p++; h.gf += f.home_goals; h.ga += f.away_goals; a.gf += f.away_goals; a.ga += f.home_goals;
      if (f.home_goals > f.away_goals) { h.w++; a.l++; h.pts += 3; }
      else if (f.away_goals > f.home_goals) { a.w++; h.l++; a.pts += 3; }
      else { h.d++; a.d++; h.pts++; a.pts++; }
    });
    return Object.values(rows).sort((x, y) => y.pts - x.pts || (y.gf - y.ga) - (x.gf - x.ga) || y.gf - x.gf);
  }
  function nextUserFx(w) {
    const cid = w.user.club_id;
    return w.fixtures.filter((f) => !f.played && (f.home_id === cid || f.away_id === cid)).sort((a, b) => a.date.localeCompare(b.date))[0];
  }
  function sampleGoals(xg) {
    xg = Math.max(0.2, Math.min(3.4, xg));
    let g = 0, p = 1 - Math.exp(-xg);
    for (let i = 0; i < 6; i++) {
      if (Math.random() < Math.min(0.78, p)) { g++; p *= 0.55; } else if (Math.random() > 0.35) break;
    }
    return g;
  }
  function playFixture(w, fid) {
    const f = w.fixtures.find((x) => x.id === fid);
    if (!f || f.played) return f;
    const hf = f.home_id === w.user.club_id ? w.user.formation : club(w, f.home_id).formation || "4-3-3";
    const af = f.away_id === w.user.club_id ? w.user.formation : club(w, f.away_id).formation || "4-3-3";
    const hx = resolveXi(w, f.home_id === w.user.club_id ? w.user.xi : autoXi(w, f.home_id, hf));
    const ax = resolveXi(w, f.away_id === w.user.club_id ? w.user.xi : autoXi(w, f.away_id, af));
    const hs = xiStrength(hx).total + 2.2;
    const as = xiStrength(ax).total;
    const diff = hs - as;
    const hg = sampleGoals(1.15 + Math.max(-1.1, Math.min(1.8, diff * 0.14)));
    const ag = sampleGoals(0.95 + Math.max(-1.1, Math.min(1.8, -diff * 0.12)));
    f.played = true; f.home_goals = hg; f.away_goals = ag;
    const att = (xi) => Object.values(xi).filter((p) => ["ST", "LW", "RW", "CAM"].includes(roleOf(p)));
    function credit(xi, n) {
      const pool = att(xi).concat(Object.values(xi));
      for (let i = 0; i < n; i++) {
        const p = pool[Math.floor(Math.random() * pool.length)];
        if (!p) continue;
        p.season_stats = p.season_stats || { apps: 0, goals: 0, assists: 0 };
        p.season_stats.goals = (p.season_stats.goals || 0) + 1;
      }
    }
    credit(hx, hg); credit(ax, ag);
    w.news = w.news || [];
    w.news.unshift({ date: w.meta.current_date, text: club(w, f.home_id).name + " " + hg + "–" + ag + " " + club(w, f.away_id).name, kind: "result" });
    return f;
  }
  function addDays(d, n) {
    const x = new Date(d + "T00:00:00");
    x.setDate(x.getDate() + n);
    return x.toISOString().slice(0, 10);
  }
  function advance(w, days) {
    const end = addDays(w.meta.current_date, days);
    const cid = w.user.club_id;
    let guard = 0;
    while (w.meta.current_date < end && guard++ < days + 20) {
      const dueUser = w.fixtures.find((f) => !f.played && f.date <= w.meta.current_date && (f.home_id === cid || f.away_id === cid));
      if (dueUser) { playFixture(w, dueUser.id); continue; }
      w.fixtures.filter((f) => !f.played && f.date <= w.meta.current_date).forEach((f) => playFixture(w, f.id));
      w.meta.current_date = addDays(w.meta.current_date, 1);
    }
    if (w.meta.current_date < end) {
      w.meta.current_date = end;
      w.fixtures.filter((f) => !f.played && f.date <= end && f.home_id !== cid && f.away_id !== cid).forEach((f) => playFixture(w, f.id));
    }
  }

  async function persist() {
    if (USER && W) await idbSet("save:" + USER, W);
  }
  async function loadSave() {
    if (!USER) return null;
    return await idbGet("save:" + USER);
  }

  function newCareer(clubId, profile) {
    W = JSON.parse(JSON.stringify(PACK));
    W.user = {
      manager_name: (profile.first || "Alex") + " " + (profile.last || "Reed"),
      first_name: profile.first || "Alex",
      last_name: profile.last || "Reed",
      age: +profile.age || 38,
      nationality: profile.nation || "England",
      club_id: clubId,
      account: USER,
      formation: "4-3-3",
      style: "balanced",
      stance: "balanced",
      xi: autoXi(W, clubId, "4-3-3"),
      trophies: [],
      fan_mood: 62
    };
    W.news = [{ date: W.meta.current_date, kind: "board", text: W.user.manager_name + " appointed at " + club(W, clubId).name }];
    W.results = [];
    W.meta.europe_on = false;
    return W;
  }

  function rarity(o) {
    if (o >= 97) return "dia";
    if (o >= 85) return "gold";
    if (o >= 75) return "blue";
    return "bronze";
  }
  function badge(c) {
    const col = (c.colors && c.colors[0]) || "#345";
    return `<span class="mini-badge" style="background:${col}">${(c.short || "?").slice(0, 3)}</span>`;
  }
  function shell(title, inner) {
    if (!W) return inner;
    const c = club(W, W.user.club_id);
    const nxt = nextUserFx(W);
    const nxts = nxt ? club(W, nxt.home_id === c.id ? nxt.away_id : nxt.home_id).name + " · " + nxt.date.slice(5) : "—";
    return `<header class="top">
      <div class="brand">M.L26</div>
      <div class="meta">${c.name} · ${W.meta.current_date} · Next ${esc(nxts)}</div>
    </header>
    <nav class="tabs">
      <a href="#/home">Home</a>
      <a href="#/plan">Game plan</a>
      <a href="#/table">Table</a>
      <a href="#/news">News</a>
      <a href="#/trophies">Trophies</a>
      <a href="#/menu">Exit</a>
    </nav>
    ${inner}`;
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  function viewLogin(msg) {
    return `<section class="panel start office">
      <h1>M.L26</h1>
      <p class="lede">Offline career. Accounts stay on this device.</p>
      <p class="warn">${esc(msg || "")}</p>
      <form id="f-login" class="stack">
        <label>Username <input name="user" required minlength="3"></label>
        <button class="primary">Sign in</button>
      </form>
      <p><a href="#/register">Create account</a></p>
    </section>`;
  }
  function viewRegister(msg) {
    return `<section class="panel start office">
      <h1>Create account</h1>
      <p class="warn">${esc(msg || "")}</p>
      <form id="f-reg" class="stack">
        <label>Username <input name="user" required minlength="3"></label>
        <button class="primary">Create</button>
      </form>
      <p><a href="#/login">Back</a></p>
    </section>`;
  }
  function viewMenu() {
    return `<section class="panel start office">
      <h1>M.L26 · ${esc(USER)}</h1>
      <p class="lede">This copy runs on the phone. No server after install.</p>
      <p><a class="btn primary" href="#/new">New career</a>
      <a class="btn" href="#/load">Load my career</a>
      <a class="btn ghost" href="#/out">Sign out</a></p>
    </section>`;
  }
  function viewNew() {
    const groups = PACK.leagues.map((l) => {
      const opts = PACK.clubs.filter((c) => c.league_id === l.id).map((c) => `<option value="${c.id}">${esc(c.name)}</option>`).join("");
      return `<optgroup label="${esc(l.name)}">${opts}</optgroup>`;
    }).join("");
    return `<section class="panel start">
      <h1>New career</h1>
      <p><a href="#/menu">Back</a></p>
      <form id="f-start" class="career-form">
        <label>First name <input name="first" value="Alex"></label>
        <label>Surname <input name="last" value="Reed"></label>
        <label>Age <input name="age" value="38"></label>
        <label>Nationality <input name="nation" value="England"></label>
        <label>Club <select name="club">${groups}</select></label>
        <button class="primary">Take the job</button>
      </form>
    </section>`;
  }
  function viewHome() {
    const cid = W.user.club_id;
    const c = club(W, cid);
    const nxt = nextUserFx(W);
    const table = tableFor(W, c.league_id);
    const place = table.findIndex((r) => r.club_id === cid) + 1;
    const me = table.find((r) => r.club_id === cid) || { pts: 0, p: 0 };
    let match = "<p class='muted'>No fixture left this season.</p>";
    if (nxt) {
      const hid = nxt.home_id, aid = nxt.away_id;
      match = `<div class="hero-fx">
        <div><b>${esc(club(W, hid).name)}</b></div>
        <div>v · ${nxt.date}</div>
        <div><b>${esc(club(W, aid).name)}</b></div>
        <p>
          <a class="btn" href="#/plan">Set XI</a>
          <button class="btn primary" data-act="play">Play match</button>
          <button class="btn" data-act="d2">+2 days</button>
          <button class="btn" data-act="d30">+1 month</button>
        </p>
      </div>`;
    }
    const inbox = (W.news || []).slice(0, 6).map((n) => `<li>${n.date.slice(5)} · ${esc(n.text)}</li>`).join("");
    const trows = table.slice(0, 5).map((r, i) => `<tr><td>${i + 1}</td><td>${esc(r.short)}</td><td>${r.pts}</td></tr>`).join("");
    return shell("Home", `
      <h1>${esc(c.name)}</h1>
      <p>${place}st · ${me.pts} pts · ${me.p} played</p>
      ${match}
      <div class="split-eu">
        <div class="panel"><h3>Inbox</h3><ul class="feed">${inbox}</ul></div>
        <div class="panel"><h3>Table</h3><table class="grid slim">${trows}</table></div>
      </div>`);
  }
  function viewPlan() {
    const form = W.user.formation || "4-3-3";
    const slots = FORMATIONS[form];
    const sq = squad(W, W.user.club_id);
    const used = new Set(Object.values(W.user.xi || {}));
    const pitch = slots.map((role, i) => {
      const key = slots.filter((s) => s === role).length > 1 ? role + (slots.slice(0, i + 1).filter((s) => s === role).length) : role;
      const p = sq.find((x) => x.id === (W.user.xi || {})[key]);
      const fit = p ? posFit(p, role) : { dot: "green", shown: 0 };
      const card = p
        ? `<div class="pcard pitch ${rarity(p.overall)}"><span class="pc-ovr">${Math.round(fit.shown)}<i class="fit-dot ${fit.dot}"></i></span><span class="pc-pos">${role}</span><span class="pc-name">${esc(p.last_name)}</span></div>`
        : `<div class="pcard empty"><span class="pc-pos">${role}</span></div>`;
      return `<div class="slot" data-slot="${key}">${card}</div>`;
    }).join("");
    const bench = sq.filter((p) => !used.has(p.id)).sort((a, b) => b.overall - a.overall).slice(0, 12).map((p) =>
      `<div class="pcard bench-card ${rarity(p.overall)}"><span class="pc-ovr">${p.overall|0}</span><span class="pc-pos">${roleOf(p)}</span><span class="pc-name">${esc(p.last_name)}</span></div>`
    ).join("");
    const mapped = resolveXi(W, W.user.xi);
    const st = xiStrength(mapped);
    const fopts = Object.keys(FORMATIONS).map((f) => `<option ${f === form ? "selected" : ""}>${f}</option>`).join("");
    return shell("Plan", `
      <h1>Game plan</h1>
      <p>XI ${st.total} · GK ${st.gk|0} DEF ${st.def|0} MID ${st.mid|0} ATT ${st.att|0}</p>
      <form id="f-form" class="row tight"><select name="formation">${fopts}</select><button>Apply</button></form>
      <div class="pitch">${pitch}</div>
      <div class="bench-list">${bench}</div>`);
  }
  function viewTable() {
    const lid = club(W, W.user.club_id).league_id;
    const rows = tableFor(W, lid).map((r, i) =>
      `<tr class="${r.club_id === W.user.club_id ? "me" : ""}"><td>${i + 1}</td><td>${esc(r.name)}</td><td>${r.p}</td><td>${r.w}</td><td>${r.d}</td><td>${r.l}</td><td>${r.pts}</td></tr>`
    ).join("");
    return shell("Table", `<h1>${esc(leagueOf(W, W.user.club_id).name)}</h1>
      <table class="grid"><thead><tr><th>#</th><th>Club</th><th>P</th><th>W</th><th>D</th><th>L</th><th>Pts</th></tr></thead><tbody>${rows}</tbody></table>`);
  }
  function viewNews() {
    const items = (W.news || []).slice(0, 30).map((n) => `<article class="desk-card"><time>${n.date}</time><p>${esc(n.text)}</p></article>`).join("") || "<p>No stories yet.</p>";
    return shell("News", `<h1>News</h1><div class="desk-col">${items}</div>`);
  }
  function viewTrophies() {
    const rows = W.user.trophies || [];
    return shell("Trophies", `<h1>Trophy room</h1><p>${esc(club(W, W.user.club_id).name)} · ${rows.length} titles</p>
      <ul class="feed">${rows.map((t) => `<li>${esc(t.season || "")} · ${esc(t.title)}</li>`).join("") || "<li>0</li>"}</ul>`);
  }

  async function route() {
    const hash = (location.hash || "#/login").slice(1);
    if (hash === "/out") {
      localStorage.removeItem("ml26.session"); USER = null; W = null; location.hash = "#/login"; return;
    }
    if (!USER && hash !== "/login" && hash !== "/register") { location.hash = "#/login"; return; }
    if (hash === "/login") { app().innerHTML = viewLogin(); bind(); return; }
    if (hash === "/register") { app().innerHTML = viewRegister(); bind(); return; }
    if (hash === "/menu") { app().innerHTML = viewMenu(); bind(); return; }
    if (hash === "/new") { app().innerHTML = viewNew(); bind(); return; }
    if (hash === "/load") {
      W = await loadSave();
      location.hash = W ? "#/home" : "#/menu";
      if (!W) alert("No saved career on this account.");
      return;
    }
    if (!W) { location.hash = "#/menu"; return; }
    if (hash === "/home") app().innerHTML = viewHome();
    else if (hash === "/plan") app().innerHTML = viewPlan();
    else if (hash === "/table") app().innerHTML = viewTable();
    else if (hash === "/news") app().innerHTML = viewNews();
    else if (hash === "/trophies") app().innerHTML = viewTrophies();
    else app().innerHTML = viewHome();
    bind();
  }

  function bind() {
    const login = $("#f-login");
    if (login) login.onsubmit = (e) => {
      e.preventDefault();
      const r = loginFn(new FormData(login).get("user"));
      if (!r.ok) { app().innerHTML = viewLogin(r.msg); bind(); } else location.hash = "#/menu";
    };
    const reg = $("#f-reg");
    if (reg) reg.onsubmit = (e) => {
      e.preventDefault();
      const r = register(new FormData(reg).get("user"));
      if (!r.ok) { app().innerHTML = viewRegister(r.msg); bind(); } else location.hash = "#/menu";
    };
    const start = $("#f-start");
    if (start) start.onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(start);
      const cid = +fd.get("club");
      if (!cid) return;
      newCareer(cid, { first: fd.get("first"), last: fd.get("last"), age: fd.get("age"), nation: fd.get("nation") });
      await persist();
      location.hash = "#/home";
    };
    const form = $("#f-form");
    if (form) form.onsubmit = async (e) => {
      e.preventDefault();
      W.user.formation = new FormData(form).get("formation");
      W.user.xi = autoXi(W, W.user.club_id, W.user.formation);
      await persist();
      route();
    };
    document.querySelectorAll("[data-act]").forEach((b) => {
      b.onclick = async () => {
        const act = b.getAttribute("data-act");
        if (act === "play") {
          const nxt = nextUserFx(W);
          if (nxt) playFixture(W, nxt.id);
          W.meta.current_date = addDays(W.meta.current_date, 1);
        }
        if (act === "d2") advance(W, 2);
        if (act === "d30") advance(W, 30);
        await persist();
        route();
      };
    });
  }
  function loginFn(name) { return login(name); }

  async function boot() {
    const fill = $("#boot-fill"), pct = $("#boot-pct"), boot = $("#boot");
    let n = 8;
    const t = setInterval(() => {
      n = Math.min(90, n + 4);
      if (fill) fill.style.width = n + "%";
      if (pct) pct.textContent = n + "%";
    }, 80);
    try {
      const res = await fetch("data/world.json");
      PACK = await res.json();
    } catch (e) {
      if (pct) pct.textContent = "Pack missing";
      return;
    }
    USER = localStorage.getItem("ml26.session");
    if (USER && !users()[USER]) { localStorage.removeItem("ml26.session"); USER = null; }
    if (USER) W = await loadSave();
    clearInterval(t);
    if (fill) fill.style.width = "100%";
    if (pct) pct.textContent = "100%";
    setTimeout(() => { if (boot) boot.hidden = true; }, 400);
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
    window.addEventListener("hashchange", route);
    if (!location.hash) location.hash = USER ? (W ? "#/home" : "#/menu") : "#/login";
    else route();
  }
  boot();
})();
