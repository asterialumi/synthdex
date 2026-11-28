/**
 * SynthDex Home Orbit Controls
 * - Per-track spin & slot angle initialization (no inline styles)
 * - Pause/Play toggle
 * - Zoom (+ / - / reset / Ctrl+Cmd+wheel, clamped 0.6x-1.6x)
 * - Ring dragging via Pointer Events with 6px click threshold
 * - Pan (drag empty sky or sun, mouse/pen only, clamped so sun stays on-screen)
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
  var sharedTooltip = document.getElementById('orbit-shared-tooltip');
  var tooltipTitleEl = sharedTooltip ? sharedTooltip.querySelector('.orbit-tooltip-title') : null;
  var tooltipArtistEl = sharedTooltip ? sharedTooltip.querySelector('.orbit-tooltip-artist') : null;

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

  // Shared top-layer planet label (C1)
  var activeTooltipPlanet = null;
  var isAnyRingDragging = false;

  function hideTooltip() {
    activeTooltipPlanet = null;
    if (!sharedTooltip) {
      return;
    }
    sharedTooltip.classList.remove('is-visible');
    sharedTooltip.setAttribute('aria-hidden', 'true');
  }

  function positionTooltipForPlanet(planet) {
    if (!sharedTooltip || !planet || isAnyRingDragging) {
      return;
    }
    var panelRect = panel.getBoundingClientRect();
    var planetRect = planet.getBoundingClientRect();
    var tipWidth = sharedTooltip.offsetWidth || 160;
    var tipHeight = sharedTooltip.offsetHeight || 42;
    var edgePad = 8;

    var centerX = (planetRect.left - panelRect.left) + (planetRect.width / 2);
    var left = centerX - (tipWidth / 2);
    left = Math.max(edgePad, Math.min(panelRect.width - tipWidth - edgePad, left));

    var top = (planetRect.top - panelRect.top) - tipHeight - 10;
    if (top < edgePad) {
      top = (planetRect.bottom - panelRect.top) + 10;
    }
    top = Math.max(edgePad, Math.min(panelRect.height - tipHeight - edgePad, top));

    sharedTooltip.style.left = Math.round(left) + 'px';
    sharedTooltip.style.top = Math.round(top) + 'px';
  }

  function showTooltipForPlanet(planet) {
    if (!sharedTooltip || !planet || isAnyRingDragging) {
      return;
    }
    activeTooltipPlanet = planet;
    if (tooltipTitleEl) {
      tooltipTitleEl.textContent = planet.getAttribute('data-title') || '';
    }
    if (tooltipArtistEl) {
      tooltipArtistEl.textContent = planet.getAttribute('data-artist') || '';
    }
    sharedTooltip.setAttribute('aria-hidden', 'false');
    sharedTooltip.classList.add('is-visible');
    positionTooltipForPlanet(planet);
  }

  var allPlanets = stage.querySelectorAll('.orbit-planet');
  for (var tpIdx = 0; tpIdx < allPlanets.length; tpIdx++) {
    allPlanets[tpIdx].addEventListener('dragstart', function (e) {
      e.preventDefault();
    });
  }

  // Use pointerover/pointermove/focusin delegation so moving planets under a stationary cursor and keyboard focus both show & track the label
  panel.addEventListener('pointerover', function (e) {
    var planet = e.target && e.target.closest ? e.target.closest('.orbit-planet') : null;
    if (planet) {
      showTooltipForPlanet(planet);
    }
  });

  panel.addEventListener('pointermove', function (e) {
    if (isAnyRingDragging) {
      return;
    }
    var planet = e.target && e.target.closest ? e.target.closest('.orbit-planet') : null;
    if (planet) {
      if (activeTooltipPlanet !== planet) {
        showTooltipForPlanet(planet);
      } else {
        positionTooltipForPlanet(planet);
      }
    } else if (activeTooltipPlanet && !activeTooltipPlanet.matches(':focus-visible')) {
      hideTooltip();
    }
  });

  panel.addEventListener('pointerleave', function () {
    if (activeTooltipPlanet && !activeTooltipPlanet.matches(':focus-visible')) {
      hideTooltip();
    }
  });

  stage.addEventListener('focusin', function (e) {
    var planet = e.target && e.target.closest ? e.target.closest('.orbit-planet') : null;
    if (planet) {
      showTooltipForPlanet(planet);
    }
  });

  stage.addEventListener('focusout', function (e) {
    if (activeTooltipPlanet && (!e.relatedTarget || !stage.contains(e.relatedTarget) || !e.relatedTarget.closest('.orbit-planet'))) {
      hideTooltip();
    }
  });

  // =========================================================================
  // Pan state (C4)
  // =========================================================================
  var panX = 0;
  var panY = 0;

  /**
   * Apply pan translation to the orbit-container.
   * We translate container (not stage) so zoom transform-origin stays centered.
   * container sits inside panel; stage inside container.
   */
  function applyPan(nx, ny) {
    panX = nx;
    panY = ny;
    container.style.setProperty('--pan-x', Math.round(panX) + 'px');
    container.style.setProperty('--pan-y', Math.round(panY) + 'px');
    if (activeTooltipPlanet) {
      positionTooltipForPlanet(activeTooltipPlanet);
    }
  }

  /**
   * Clamp panX/panY so the stage center (the sun) is always at least
   * `margin` pixels inside the panel edge in all four directions.
   * This guarantees the sun is never fully off-screen.
   */
  function clampPan(nx, ny) {
    var panelRect = panel.getBoundingClientRect();
    var containerRect = container.getBoundingClientRect();

    // Container natural center relative to panel (before this pan delta is applied)
    // We work in panel-local coords. The container currently has panX,panY applied.
    var containerNaturalCenterX = (containerRect.left - panelRect.left) + containerRect.width / 2 - panX;
    var containerNaturalCenterY = (containerRect.top - panelRect.top) + containerRect.height / 2 - panY;

    // With proposed pan nx,ny the sun center in panel coords would be:
    var sunX = containerNaturalCenterX + nx;
    var sunY = containerNaturalCenterY + ny;

    // Clamp sun center to [margin .. panelW-margin] x [margin .. panelH-margin]
    var margin = 56; // half-ish the sun vinyl width (82px) so a sliver is always visible
    sunX = Math.max(margin, Math.min(panelRect.width - margin, sunX));
    sunY = Math.max(margin, Math.min(panelRect.height - margin, sunY));

    return {
      x: sunX - containerNaturalCenterX,
      y: sunY - containerNaturalCenterY
    };
  }

  // =========================================================================
  // Zoom state (0.6x to 1.6x)
  // =========================================================================
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
    if (activeTooltipPlanet) {
      positionTooltipForPlanet(activeTooltipPlanet);
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
      // Reset pan together with zoom
      applyPan(0, 0);
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
  applyPan(0, 0);

  // Orbit ring animation & dragging (disabled under prefers-reduced-motion)
  var isUserPaused = false;
  var isTabHidden = document.hidden;
  var isOffscreen = false;
  var rafId = null;
  var lastTime = null;

  var ringEls = stage.querySelectorAll('.orbit-ring[data-ring-duration]');
  var rings = [];

  function renderRing(ring) {
    ring.el.style.transform = 'translate(-50%, -50%) rotate(' + ring.angle + 'deg)';
    for (var p = 0; p < ring.planets.length; p++) {
      ring.planets[p].style.transform = 'rotate(' + (-ring.angle) + 'deg)';
    }
  }

  for (var r = 0; r < ringEls.length; r++) {
    var ringEl = ringEls[r];
    var dur = parseFloat(ringEl.getAttribute('data-ring-duration')) || 60;
    var ringObj = {
      el: ringEl,
      planets: ringEl.querySelectorAll('.orbit-planet'),
      angle: Math.random() * 360,
      degPerSec: 360 / dur,
      dragging: false
    };
    rings.push(ringObj);
    renderRing(ringObj);
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
      if (activeTooltipPlanet && !isAnyRingDragging) {
        positionTooltipForPlanet(activeTooltipPlanet);
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

    function getSystemCenter() {
      var rect = stage.getBoundingClientRect();
      return {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2
      };
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
        var moved = false;

        planet.addEventListener('pointerdown', function (e) {
          if (e.button !== 0 && e.pointerType === 'mouse') {
            return;
          }
          pointerId = e.pointerId;
          startX = e.clientX;
          startY = e.clientY;
          moved = false;
          var center = getSystemCenter();
          lastPointerAngle = getPointerAngle(e.clientX, e.clientY, center.x, center.y);
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
            isAnyRingDragging = true;
            hideTooltip();
            planet.classList.add('is-dragging');
          }
          if (moved) {
            var center = getSystemCenter();
            var currentAngle = getPointerAngle(e.clientX, e.clientY, center.x, center.y);
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
          isAnyRingDragging = false;
          planet.classList.remove('is-dragging');
          try {
            planet.releasePointerCapture(e.pointerId);
          } catch (err) {
            /* ignore */
          }
        }

        planet.addEventListener('pointerup', endDrag);
        planet.addEventListener('pointercancel', endDrag);
        planet.addEventListener('lostpointercapture', endDrag);
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

  // =========================================================================
  // Pan: drag empty sky or the sun (mouse/pen only, disabled under reduced-motion)
  // =========================================================================
  if (!reducedMotion) {
    var isPanning = false;
    var panPointerId = null;
    var panStartClientX = 0;
    var panStartClientY = 0;
    var panStartX = 0;
    var panStartY = 0;
    var panMoved = false;
    var PAN_THRESHOLD_SQ = 25; // 5px threshold to separate tap from drag

    var sunEl = stage.querySelector('.orbit-sun');

    /**
     * Returns true when the pointer-down target is a valid pan handle:
     * the panel background, the orbit-container, the orbit-stage, or the sun.
     * Excludes planets, controls, the header, legend, tooltip, and the stage
     * rings themselves so planet-drag still takes priority.
     */
    function isPanTarget(target) {
      if (!target) { return false; }
      // Explicitly excluded: interactive controls/buttons/links
      if (target.closest('.orbit-controls') || target.closest('.orbit-sky-header') ||
          target.closest('.orbit-legend') || target.closest('#orbit-shared-tooltip')) {
        return false;
      }
      // Excluded: a planet link (ring drag handles those)
      if (target.closest('.orbit-planet')) { return false; }
      // Allowed: sun element subtree
      if (sunEl && sunEl.contains(target)) { return true; }
      // Allowed: container/stage/panel background
      if (target === panel || target === container || target === stage ||
          target.closest('.orbit-stage') === stage) {
        return true;
      }
      return false;
    }

    panel.addEventListener('pointerdown', function (e) {
      // Mouse/pen only — let touch fall through to native scroll
      if (e.pointerType === 'touch') { return; }
      if (!isPanTarget(e.target)) { return; }
      // Only primary button
      if (e.button !== 0) { return; }

      isPanning = true;
      panPointerId = e.pointerId;
      panStartClientX = e.clientX;
      panStartClientY = e.clientY;
      panStartX = panX;
      panStartY = panY;
      panMoved = false;

      try {
        panel.setPointerCapture(e.pointerId);
      } catch (err) { /* ignore */ }
    });

    panel.addEventListener('pointermove', function (e) {
      if (!isPanning || e.pointerId !== panPointerId) { return; }

      var dx = e.clientX - panStartClientX;
      var dy = e.clientY - panStartClientY;

      if (!panMoved && (dx * dx + dy * dy) >= PAN_THRESHOLD_SQ) {
        panMoved = true;
        panel.classList.add('is-panning');
        hideTooltip();
      }

      if (panMoved) {
        var clamped = clampPan(panStartX + dx, panStartY + dy);
        applyPan(clamped.x, clamped.y);
      }
    });

    function endPan(e) {
      if (!isPanning || e.pointerId !== panPointerId) { return; }
      isPanning = false;
      panPointerId = null;
      panel.classList.remove('is-panning');
      try {
        panel.releasePointerCapture(e.pointerId);
      } catch (err) { /* ignore */ }
    }

    panel.addEventListener('pointerup', endPan);
    panel.addEventListener('pointercancel', endPan);
    panel.addEventListener('lostpointercapture', endPan);
  }
})();
