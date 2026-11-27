/**
 * SynthDex Home Orbit Controls
 * Applies per-track spin durations and handles Pause/Play toggling.
 */
(function () {
  'use strict';

  var panel = document.getElementById('orbit-sky-panel');
  var toggleBtn = document.getElementById('orbit-toggle-btn');

  // Apply per-track spin durations without inline style attributes
  var spinCovers = document.querySelectorAll('.orbit-cover-spin[data-spin-duration]');
  for (var i = 0; i < spinCovers.length; i++) {
    var sec = spinCovers[i].getAttribute('data-spin-duration');
    if (sec) {
      spinCovers[i].style.setProperty('--spin-duration', sec + 's');
    }
  }

  if (panel && toggleBtn) {
    var labelEl = toggleBtn.querySelector('.orbit-toggle-label');
    toggleBtn.addEventListener('click', function () {
      var isPaused = panel.classList.toggle('is-paused');
      toggleBtn.setAttribute('aria-pressed', isPaused ? 'true' : 'false');
      toggleBtn.setAttribute('aria-label', isPaused ? 'Play orbit animation' : 'Pause orbit animation');
      if (labelEl) {
        labelEl.textContent = isPaused ? 'Play' : 'Pause';
      }
    });
  }
})();
