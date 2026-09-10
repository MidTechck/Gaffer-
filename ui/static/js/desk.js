(function () {
  const KEY = "ml26-audio";
  const def = { music: true, sfx: true, mvol: 0.35, svol: 0.25, idx: 0, t: 0 };
  function load() {
    try { return Object.assign({}, def, JSON.parse(sessionStorage.getItem(KEY) || localStorage.getItem(KEY) || "{}")); }
    catch (e) { return Object.assign({}, def); }
  }
  function save(s) {
    const blob = JSON.stringify(s);
    sessionStorage.setItem(KEY, blob);
    localStorage.setItem(KEY, blob);
  }
  const state = load();
  const tracks = ["/static/sfx/loop1.mp3", "/static/sfx/loop2.mp3"];
  let idx = (state.idx || 0) % tracks.length;
  const music = new Audio(tracks[idx]);
  music.preload = "auto";
  music.volume = state.mvol;
  function persist() {
    state.idx = idx;
    state.t = music.currentTime || 0;
    save(state);
  }
  music.addEventListener("timeupdate", function () {
    if (Math.floor(music.currentTime) % 2 === 0) persist();
  });
  music.addEventListener("ended", function () {
    idx = (idx + 1) % tracks.length;
    state.t = 0;
    persist();
    music.src = tracks[idx];
    if (state.music) music.play().catch(function () {});
  });
  function startMusic() {
    if (!state.music) { music.pause(); return; }
    music.volume = state.mvol;
    const resume = function () {
      if (state.t > 1 && state.t < (music.duration || 9999) - 1) {
        try { music.currentTime = state.t; } catch (e) {}
      }
      music.play().catch(function () {});
    };
    if (music.readyState >= 1) resume();
    else music.addEventListener("loadedmetadata", resume, { once: true });
  }
  document.addEventListener("pointerdown", function once() {
    startMusic();
    document.removeEventListener("pointerdown", once);
  });
  startMusic();
  window.addEventListener("pagehide", persist);
  const click = new Audio("/static/sfx/click.wav");
  click.volume = state.svol;
  document.addEventListener("click", function (e) {
    if (!state.sfx) return;
    if (e.target.closest("a,button")) {
      persist();
      try { click.currentTime = 0; click.volume = state.svol; click.play(); } catch (err) {}
    }
  }, true);
  function bind() {
    const m = document.getElementById("set-music");
    const s = document.getElementById("set-sfx");
    const mv = document.getElementById("set-mvol");
    const sv = document.getElementById("set-svol");
    if (!m) return;
    m.checked = state.music;
    s.checked = state.sfx;
    mv.value = Math.round(state.mvol * 100);
    sv.value = Math.round(state.svol * 100);
    function apply() {
      state.music = m.checked;
      state.sfx = s.checked;
      state.mvol = Number(mv.value) / 100;
      state.svol = Number(sv.value) / 100;
      save(state);
      music.volume = state.mvol;
      click.volume = state.svol;
      if (state.music) startMusic();
      else music.pause();
    }
    m.onchange = s.onchange = mv.oninput = sv.oninput = apply;
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", bind);
  else bind();
})();





  (function boot() {
    const box = document.getElementById("boot");
    const fill = document.getElementById("boot-fill");
    const pct = document.getElementById("boot-pct");
    if (!box) return;
    const word = box.querySelector(".boot-word");
    let timer = null;
    let locked = false;
    let busy = false;

    function setWord(s) {
      if (!word) return;
      word.textContent = s;
    }
    window.addEventListener("popstate", function () {
      if (locked) history.pushState({ ml26lock: 1 }, "");
    });
    function runBar(ms) {
      const t0 = Date.now();
      clearInterval(timer);
      timer = setInterval(function () {
        const p = Math.min(99, Math.round(((Date.now() - t0) / ms) * 100));
        if (fill) fill.style.width = p + "%";
        if (pct) pct.textContent = p + "%";
        if (p >= 99) clearInterval(timer);
      }, 80);
    }
    function show(label) {
      box.hidden = false;
      if (fill) { fill.style.width = "4%"; fill.style.transition = "width .35s linear"; }
      if (pct) pct.textContent = "4%";
      setWord(label || "LOADING");
    }
    function hide() {
      locked = false;
      if (fill) fill.style.width = "100%";
      if (pct) pct.textContent = "100%";
      setTimeout(function () { box.hidden = true; }, 200);
    }

    const STEPS = {
      preseason: [[0,"Pre-season camp"],[0.3,"Fitness work"],[0.65,"Updating the diary"]],
      rest: [[0,"Rest days"],[0.4,"Updating fitness"],[0.75,"Checking the calendar"]],
      league: [[0,"Playing league matches"],[0.35,"Calculating points"],[0.7,"Updating the table"],[0.88,"Finalising results"]],
      cups: [[0,"Playing cup ties"],[0.45,"Updating brackets"],[0.8,"Finalising results"]],
      mix: [[0,"Playing league matches"],[0.3,"Cup ties in progress"],[0.55,"Calculating points"],[0.8,"Finalising results"]],
      d2: [[0,"Reading the diary"],[0.45,"Updating fitness"],[0.8,"Checking fixtures"]],
      load: [[0,"Opening save"],[0.4,"Calculating data"],[0.75,"Ready"]]
    };

    function playSteps(key, ms) {
      const steps = STEPS[key] || STEPS.d2;
      const t0 = Date.now();
      function tick() {
        const f = Math.min(1, (Date.now() - t0) / ms);
        let label = steps[0][1];
        for (let i = 0; i < steps.length; i++) if (f >= steps[i][0]) label = steps[i][1];
        setWord(label);
        if (f < 1) requestAnimationFrame(tick);
      }
      tick();
    }

    if (!sessionStorage.getItem("ml26-opened")) {
      sessionStorage.setItem("ml26-opened", "1");
      show("LOADING");
      runBar(3600);
      setTimeout(hide, 3600);
    } else {
      box.hidden = true;
    }

    document.addEventListener("submit", function (e) {
      const form = e.target;
      if (!form || !form.getAttribute) return;
      const act = (form.getAttribute("action") || "").toLowerCase();
      let kind = null;
      let wait = 0;
      const phase = (form.getAttribute("data-phase") || "").toLowerCase();
      if (act === "/advance/2") { kind = phase || "d2"; wait = 6000; }
      else if (act === "/advance/30") { kind = phase || "league"; wait = 12000; }
      else if (act === "/advance/90") { kind = phase || "mix"; wait = 28000; }
      else if (act === "/start") { kind = "start"; wait = 3600; }
      else if (act === "/load" || act === "/next-season") { kind = "load"; wait = 2800; }
      else if (act === "/goto-match") { kind = phase || "d2"; wait = 5000; }
      if (!kind) return;
      e.preventDefault();
      if (busy) return;
      busy = true;
      locked = true;
      history.pushState({ ml26lock: 1 }, "");
      Array.prototype.forEach.call(document.querySelectorAll("button"), function (b) { b.disabled = true; });
      show(kind === "start" ? "LOADING" : "Working");
      if (kind === "start") setWord("LOADING");
      else playSteps(kind, wait);
      runBar(wait);
      const body = new URLSearchParams(new FormData(form));
      const begun = Date.now();
      fetch(form.getAttribute("action"), { method: "POST", headers: {"Content-Type":"application/x-www-form-urlencoded"}, body: body.toString(), redirect: "follow", credentials: "same-origin" })
        .then(function (res) {
          const left = Math.max(0, wait - (Date.now() - begun));
          return new Promise(function (ok) { setTimeout(function () { ok(res); }, left); });
        })
        .then(function (res) {
          window.location.replace(res.url || "/home");
        })
        .catch(function () {
          window.location.replace("/home");
        });
    }, true);
  })();
