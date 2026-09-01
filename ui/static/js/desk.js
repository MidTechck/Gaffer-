(function () {
  /* click tick only — no music button */
  const click = new Audio("/static/sfx/click.wav");
  click.volume = 0.2;
  document.addEventListener("click", function (e) {
    if (e.target.closest("a,button")) {
      try { click.currentTime = 0; click.play(); } catch (err) {}
    }
  }, true);
})();
