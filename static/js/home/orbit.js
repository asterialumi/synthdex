/**
 * SynthDex Home Orbit Controls
 * - Per-track spin & slot angle initialization (no inline styles)
 * - Pause/Play toggle
 * - Zoom (+ / - / reset / Ctrl+Cmd+wheel, clamped 0.6x-1.6x)
 * - Ring dragging via Pointer Events with 6px click threshold
 * - Tab visibility & offscreen pausing for performance
 */
(function () {
  'use strict';

  var panel = document.getElementById('orbit-sky-panel');
  var container = document.getElementById('orbit-container');
  var stage = document.getElementById('orbit-stage');
  var toggleBtn = document.getElementById('orbit-toggle-btn');
  var zoomInBtn = document.getElementById('orbit-zoom-in');
  var zoomOutBtn = document.getElementById('orbit-zoom-out');
  var zoomResetBtn = document.getElementById('orbit-zoom-reset');

  if (!panel || !container || !stage) {
    return;
  }

  var reducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Apply slot angles and per-track spin durations without inline style attributes
  var slots = stage.querySelectorAll('.orbit-planet-slot[data-angle]');
  for (var i = 0; i < slots.length; i++) {
    var slotAngle = slots[i].getAttribute('data-angle');
    if (slotAngle !== null) {
      slots[i].style.setProperty('--slot-angle', slotAngle + 'deg');
    }
  }

  var spinCovers = stage.querySelectorAll('.orbit-cover-spin[data-spin-duration]');
  for (var j = 0; j < spinCovers.length; j++) {
    var sec = spinCovers[j].getAttribute('data-spin-duration');
    if (sec) {
      spinCovers[j].style.setProperty('--spin-duration', sec + 's');
    }
  }

  // Zoom state (0.6x to 1.6x)
  var MIN_ZOOM = 0.6;
  var MAX_ZOOM = 1.6;
  var ZOOM_STEP = 0.15;
  var zoom = 1.0;

  function applyZoom(nextZoom) {
    zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, Math.round(nextZoom * 100) / 100));
    stage.style.transform = 'scale(' + zoom + ')';
    if (zoomResetBtn) {
      zoomResetBtn.textContent = Math.round(zoom * 100) + '%';
    }
    if (zoomInBtn) {
      zoomInBtn.disabled = zoom >= MAX_ZOOM;
    }
    if (zoomOutBtn) {
      zoomOutBtn.disabled = zoom <= MIN_ZOOM;
    }
  }

  if (zoomInBtn) {
    zoomInBtn.addEventListener('click', function () {
      applyZoom(zoom + ZOOM_STEP);
    });
  }
  if (zoomOutBtn) {
    zoomOutBtn.addEventListener('click', function () {
      applyZoom(zoom - ZOOM_STEP);
    });
  }
  if (zoomResetBtn) {
    zoomResetBtn.addEventListener('click', function () {
      applyZoom(1.0);
    });
  }

  // Ctrl/Cmd + wheel zoom only (never hijack plain scroll)
  panel.addEventListener('wheel', function (e) {
    if (!e.ctrlKey && !e.metaKey) {
      return;
    }
    e.preventDefault();
    var delta = e.deltaY < 0 ? 0.1 : -0.1;
    applyZoom(zoom + delta);
  }, { passive: false });

  applyZoom(1.0);

  // Orbit ring animation & dragging (disabled under prefers-reduced-motion)
  var isUserPaused = false;
  var isTabHidden = document.hidden;
  var isOffscreen = false;
  var rafId = null;
  var lastTime = null;

  var ringEls = stage.querySelectorAll('.orbit-ring[data-ring-duration]');
  var rings = [];

  for (var r = 0; r < ringEls.length; r++) {
    var ringEl = ringEls[r];
    var dur = parseFloat(ringEl.getAttribute('data-ring-duration')) || 60;
    rings.push({
      el: ringEl,
      planets: ringEl.querySelectorAll('.orbit-planet'),
      angle: 0,
      degPerSec: 360 / dur,
      dragging: false
    });
  }

  function renderRing(ring) {
    ring.el.style.transform = 'translate(-50%, -50%) rotate(' + ring.angle + 'deg)';
    for (var p = 0; p < ring.planets.length; p++) {
      ring.planets[p].style.transform = 'rotate(' + (-ring.angle) + 'deg)';
    }
  }

  function shouldAnimate() {
    return !reducedMotion && !isUserPaused && !isTabHidden && !isOffscreen && rings.length > 0;
  }

  function syncInactiveClass() {
    var inactive = isTabHidden || isOffscreen;
    panel.classList.toggle('is-inactive', inactive);
  }

  function tick(now) {
    if (!shouldAnimate()) {
      rafId = null;
      lastTime = null;
      return;
    }
    if (lastTime !== null) {
      var dt = Math.min(0.1, (now - lastTime) / 1000);
      for (var k = 0; k < rings.length; k++) {
        if (!rings[k].dragging) {
          rings[k].angle = (rings[k].angle + rings[k].degPerSec * dt) % 360;
          renderRing(rings[k]);
        }
      }
    }
    lastTime = now;
    rafId = window.requestAnimationFrame(tick);
  }

  function updateAnimationState() {
    syncInactiveClass();
    if (shouldAnimate()) {
      if (rafId === null) {
        lastTime = null;
        rafId = window.requestAnimationFrame(tick);
      }
    } else if (rafId !== null) {
      window.cancelAnimationFrame(rafId);
      rafId = null;
      lastTime = null;
    }
  }

  if (toggleBtn) {
    var labelEl = toggleBtn.querySelector('.orbit-toggle-label');
    toggleBtn.addEventListener('click', function () {
      isUserPaused = panel.classList.toggle('is-paused');
      toggleBtn.setAttribute('aria-pressed', isUserPaused ? 'true' : 'false');
      toggleBtn.setAttribute('aria-label', isUserPaused ? 'Play orbit animation' : 'Pause orbit animation');
      if (labelEl) {
        labelEl.textContent = isUserPaused ? 'Play' : 'Pause';
      }
      updateAnimationState();
    });
  }

  document.addEventListener('visibilitychange', function () {
    isTabHidden = document.hidden;
    updateAnimationState();
  });

  if ('IntersectionObserver' in window) {
    var observer = new IntersectionObserver(function (entries) {
      for (var eIdx = 0; eIdx < entries.length; eIdx++) {
        if (entries[eIdx].target === panel) {
          isOffscreen = !entries[eIdx].isIntersecting;
          updateAnimationState();
        }
      }
    }, { threshold: 0.05 });
    observer.observe(panel);
  }

  if (!reducedMotion && rings.length > 0) {
    panel.classList.add('is-js-orbit');
    for (var initIdx = 0; initIdx < rings.length; initIdx++) {
      renderRing(rings[initIdx]);
    }
    updateAnimationState();

    // Pointer-based ring dragging (6px threshold so normal clicks still navigate)
    var DRAG_THRESHOLD_SQ = 36;
    var suppressClickPlanet = null;

    function findRingForEl(el) {
      for (var idx = 0; idx < rings.length; idx++) {
        if (rings[idx].el === el) {
          return rings[idx];
        }
      }
      return null;
    }

    function getPointerAngle(clientX, clientY, centerX, centerY) {
      return Math.atan2(clientY - centerY, clientX - centerX) * (180 / Math.PI);
    }

    function normalizeDelta(delta) {
      while (delta > 180) { delta -= 360; }
      while (delta < -180) { delta += 360; }
      return delta;
    }

    var planets = stage.querySelectorAll('.orbit-planet');
    for (var pIdx = 0; pIdx < planets.length; pIdx++) {
      (function (planet) {
        var ringElRef = planet.closest('.orbit-ring');
        var ringObj = findRingForEl(ringElRef);
        if (!ringObj) {
          return;
        }

        var pointerId = null;
        var startX = 0;
        var startY = 0;
        var lastPointerAngle = 0;
        var centerX = 0;
        var centerY = 0;
        var moved = false;

        planet.addEventListener('pointerdown', function (e) {
          if (e.button !== 0 && e.pointerType === 'mouse') {
            return;
          }
          pointerId = e.pointerId;
          startX = e.clientX;
          startY = e.clientY;
          moved = false;
          var rect = stage.getBoundingClientRect();
          centerX = rect.left + rect.width / 2;
          centerY = rect.top + rect.height / 2;
          lastPointerAngle = getPointerAngle(e.clientX, e.clientY, centerX, centerY);
          ringObj.dragging = true;
          try {
            planet.setPointerCapture(pointerId);
          } catch (err) {
            /* ignore */
          }
        });

        planet.addEventListener('pointermove', function (e) {
          if (e.pointerId !== pointerId) {
            return;
          }
          var dx = e.clientX - startX;
          var dy = e.clientY - startY;
          if (!moved && (dx * dx + dy * dy) >= DRAG_THRESHOLD_SQ) {
            moved = true;
            planet.classList.add('is-dragging');
          }
          if (moved) {
            var currentAngle = getPointerAngle(e.clientX, e.clientY, centerX, centerY);
            var delta = normalizeDelta(currentAngle - lastPointerAngle);
            lastPointerAngle = currentAngle;
            ringObj.angle = (ringObj.angle + delta) % 360;
            renderRing(ringObj);
          }
        });

        function endDrag(e) {
          if (e.pointerId !== pointerId) {
            return;
          }
          if (moved) {
            suppressClickPlanet = planet;
            window.setTimeout(function () {
              if (suppressClickPlanet === planet) {
                suppressClickPlanet = null;
              }
            }, 50);
          }
          pointerId = null;
          ringObj.dragging = false;
          planet.classList.remove('is-dragging');
          try {
            planet.releasePointerCapture(e.pointerId);
          } catch (err) {
            /* ignore */
          }
        }

        planet.addEventListener('pointerup', endDrag);
        planet.addEventListener('pointercancel', endDrag);
        planet.addEventListener('click', function (e) {
          if (suppressClickPlanet === planet) {
            e.preventDefault();
            e.stopPropagation();
            suppressClickPlanet = null;
          }
        });
      })(planets[pIdx]);
    }
  }
})();
