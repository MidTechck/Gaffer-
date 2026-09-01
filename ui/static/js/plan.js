(function () {
  const board = document.querySelector(".plan-board");
  if (!board) return;

  const HOLD_MS = 280;
  const MOVE_CANCEL = 12;

  let holdTimer = null;
  let pending = null;
  let dragPid = null;
  let ghost = null;
  let startPt = null;

  function cardEl(t) {
    return t && t.closest ? t.closest(".slot-card[data-pid]") : null;
  }
  function slotEl(t) {
    return t && t.closest ? t.closest(".drop-slot") : null;
  }
  function point(e) {
    if (e.touches && e.touches[0]) return { x: e.touches[0].clientX, y: e.touches[0].clientY };
    if (e.changedTouches && e.changedTouches[0]) return { x: e.changedTouches[0].clientX, y: e.changedTouches[0].clientY };
    return { x: e.clientX, y: e.clientY };
  }
  function dist(a, b) {
    const dx = a.x - b.x, dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }

  function dropTo(pid, to) {
    const f = document.createElement("form");
    f.method = "post";
    f.action = "/drop";
    f.innerHTML =
      '<input name="pid" value="' + pid + '">' +
      '<input name="to" value="' + to + '">';
    document.body.appendChild(f);
    f.submit();
  }

  function makeGhost(card) {
    ghost = card.cloneNode(true);
    ghost.classList.add("ghost-drag");
    ghost.style.position = "fixed";
    ghost.style.pointerEvents = "none";
    ghost.style.zIndex = "80";
    ghost.style.width = Math.max(108, card.offsetWidth) + "px";
    document.body.appendChild(ghost);
    card.classList.add("lifting");
  }

  function moveGhost(x, y) {
    if (!ghost) return;
    ghost.style.left = x - ghost.offsetWidth / 2 + "px";
    ghost.style.top = y - 24 + "px";
  }

  function clearGhost() {
    document.querySelectorAll(".slot-card.lifting").forEach(function (el) {
      el.classList.remove("lifting");
    });
    if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost);
    ghost = null;
    document.querySelectorAll(".drop-slot.hot").forEach(function (el) {
      el.classList.remove("hot");
    });
  }

  function cancelHold() {
    if (holdTimer) {
      clearTimeout(holdTimer);
      holdTimer = null;
    }
    pending = null;
  }

  function arm(e) {
    const card = cardEl(e.target);
    if (!card || !card.getAttribute("data-pid")) return;
    startPt = point(e);
    pending = card;
    holdTimer = setTimeout(function () {
      if (!pending) return;
      dragPid = pending.getAttribute("data-pid");
      makeGhost(pending);
      moveGhost(startPt.x, startPt.y);
      pending = null;
    }, HOLD_MS);
  }

  function move(e) {
    const p = point(e);
    if (pending && startPt && dist(p, startPt) > MOVE_CANCEL) {
      cancelHold();
      return;
    }
    if (!dragPid) return;
    e.preventDefault();
    moveGhost(p.x, p.y);
    document.querySelectorAll(".drop-slot.hot").forEach(function (el) {
      el.classList.remove("hot");
    });
    ghost.style.visibility = "hidden";
    const under = document.elementFromPoint(p.x, p.y);
    ghost.style.visibility = "visible";
    const slot = slotEl(under);
    if (slot) slot.classList.add("hot");
  }

  function end(e) {
    cancelHold();
    if (!dragPid) return;
    const p = point(e);
    if (ghost) ghost.style.visibility = "hidden";
    const under = document.elementFromPoint(p.x, p.y);
    const slot = slotEl(under);
    const pid = dragPid;
    dragPid = null;
    clearGhost();
    if (slot) dropTo(pid, slot.getAttribute("data-slot") || "bench");
  }

  board.addEventListener("mousedown", arm);
  board.addEventListener("touchstart", arm, { passive: true });
  window.addEventListener("mousemove", move);
  window.addEventListener("touchmove", move, { passive: false });
  window.addEventListener("mouseup", end);
  window.addEventListener("touchend", end);
  window.addEventListener("touchcancel", end);
})();
