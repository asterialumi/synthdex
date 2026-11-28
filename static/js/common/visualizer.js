/**
 * SynthDex Visualizer Rings Background
 * Decorative concentric radial-bar rings on a fixed full-viewport canvas.
 */
(function () {
  'use strict';

  /* ========================================================================
     Tunable Constants
     ======================================================================== */
  var MOBILE_BREAKPOINT = 768;      // Viewport width (px) below which rings are disabled
  var MAX_DPR = 2;                  // Cap devicePixelRatio for performance
  var INNER_RADIUS_FACTOR = 0.42;   // Inner ring radius as fraction of max(width, height)
  var OUTER_RADIUS_FACTOR = 0.47;   // Outer ring radius as fraction of max(width, height)
  var INNER_BAR_COUNT = 120;        // Number of radial bars in the inner ring
  var OUTER_BAR_COUNT = 160;        // Number of radial bars in the outer ring
  var BAR_WIDTH = 2;                // Radial bar thickness (CSS px)
  var BAR_BASE_HEIGHT = 8;          // Resting bar length (CSS px)
  var BAR_MAX_AMPLITUDE = 28;       // Maximum extra bar length when active (CSS px)
  var INNER_IDLE_SPEED = 0.045;     // Inner ring idle angular speed (rad/s, clockwise)
  var OUTER_IDLE_SPEED = -0.032;    // Outer ring idle angular speed (rad/s, counter-clockwise)
  var SCROLL_GAIN = 0.0022;         // Angular speed boost per px of scroll delta
  var SCROLL_MAX_BOOST = 2.4;       // Maximum angular speed boost from scrolling (rad/s)
  var SCROLL_DECAY = 4.5;           // Exponential decay rate back to idle speed (1/s)
  var ACTIVITY_DECAY = 3.0;         // Exponential decay rate for bar activity (1/s)
  var TRACK_IDLE_ACTIVITY = 0.45;   // Constant moderate bar activity on track detail pages
  var IDLE_FPS = 30;                // Target frame rate when idle
  var ACTIVE_FPS = 60;              // Target frame rate during/after input
  var ACTIVE_WINDOW_MS = 1000;      // Duration (ms) to hold active FPS after input
  var RESIZE_DEBOUNCE_MS = 120;     // Debounce delay (ms) for resize handling

  var canvas = document.getElementById('viz-bg');
  if (!canvas || !canvas.getContext) {
    return;
  }

  var ctx = canvas.getContext('2d');
  if (!ctx) {
    return;
  }

  var reducedMotionQuery = window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null;
  var darkSchemeQuery = window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null;

  var width = 0;
  var height = 0;
  var dpr = 1;
  var ringColor = 'rgba(184, 121, 47, 0.16)';

  var innerAngle = 0;
  var outerAngle = 0;
  var scrollImpulse = 0;
  var lastScrollY = window.scrollY || 0;
  var lastWheelTime = 0;
  var lastInputTime = 0;

  var rafId = 0;
  var lastFrameTime = 0;
  var lastDrawTime = 0;
  var resizeTimer = 0;

  function isMobile() {
    return window.innerWidth < MOBILE_BREAKPOINT;
  }

  function isReducedMotion() {
    return Boolean(reducedMotionQuery && reducedMotionQuery.matches);
  }

  function readRingColor() {
    var value = getComputedStyle(document.documentElement)
      .getPropertyValue('--viz-ring-color')
      .trim();
    if (value) {
      ringColor = value;
    }
  }

  function resizeCanvas() {
    if (isMobile()) {
      width = 0;
      height = 0;
      canvas.width = 0;
      canvas.height = 0;
      return;
    }
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
  }

  function drawRing(cx, cy, radius, count, baseAngle) {
    var step = (Math.PI * 2) / count;
    for (var i = 0; i < count; i++) {
      var angle = baseAngle + i * step;
      var cos = Math.cos(angle);
      var sin = Math.sin(angle);
      var x0 = cx + cos * radius;
      var y0 = cy + sin * radius;
      var x1 = cx + cos * (radius + BAR_BASE_HEIGHT);
      var y1 = cy + sin * (radius + BAR_BASE_HEIGHT);
      ctx.moveTo(x0, y0);
      ctx.lineTo(x1, y1);
    }
  }

  function draw() {
    if (isMobile() || width <= 0 || height <= 0) {
      return;
    }

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);

    var cx = width * 0.5;
    var cy = height * 0.5;
    var span = Math.max(width, height);
    var innerRadius = span * INNER_RADIUS_FACTOR;
    var outerRadius = span * OUTER_RADIUS_FACTOR;

    ctx.strokeStyle = ringColor;
    ctx.lineWidth = BAR_WIDTH;
    ctx.lineCap = 'round';
    ctx.beginPath();
    drawRing(cx, cy, innerRadius, INNER_BAR_COUNT, innerAngle);
    drawRing(cx, cy, outerRadius, OUTER_BAR_COUNT, outerAngle);
    ctx.stroke();
  }

  function applyScrollDelta(delta) {
    if (!delta) {
      return;
    }
    scrollImpulse = Math.max(
      -SCROLL_MAX_BOOST,
      Math.min(SCROLL_MAX_BOOST, scrollImpulse + delta * SCROLL_GAIN)
    );
    lastInputTime = performance.now();
  }

  function onWheel(e) {
    if (e.ctrlKey || e.metaKey) {
      return;
    }
    lastWheelTime = performance.now();
    applyScrollDelta(e.deltaY);
  }

  function onScroll() {
    var currentY = window.scrollY || 0;
    var delta = currentY - lastScrollY;
    lastScrollY = currentY;
    if (performance.now() - lastWheelTime < 60) {
      return;
    }
    applyScrollDelta(delta);
  }

  function step(now) {
    if (document.hidden || isMobile() || isReducedMotion()) {
      rafId = 0;
      return;
    }

    rafId = window.requestAnimationFrame(step);

    var isActive =
      (now - lastInputTime) < ACTIVE_WINDOW_MS ||
      Math.abs(scrollImpulse) > 0.001;
    var minInterval = 1000 / (isActive ? ACTIVE_FPS : IDLE_FPS);
    if (lastDrawTime && (now - lastDrawTime) < minInterval) {
      return;
    }

    var dt = lastFrameTime ? Math.min((now - lastFrameTime) / 1000, 0.1) : 0;
    lastFrameTime = now;
    lastDrawTime = now;

    if (dt > 0) {
      var innerVel = INNER_IDLE_SPEED + scrollImpulse;
      var outerVel = OUTER_IDLE_SPEED - scrollImpulse;
      innerAngle = (innerAngle + innerVel * dt) % (Math.PI * 2);
      outerAngle = (outerAngle + outerVel * dt) % (Math.PI * 2);

      scrollImpulse *= Math.exp(-SCROLL_DECAY * dt);
      if (Math.abs(scrollImpulse) < 0.0001) {
        scrollImpulse = 0;
      }
    }

    draw();
  }

  function startLoop() {
    if (rafId || document.hidden || isMobile() || isReducedMotion()) {
      return;
    }
    lastFrameTime = performance.now();
    lastDrawTime = 0;
    rafId = window.requestAnimationFrame(step);
  }

  function stopLoop() {
    if (rafId) {
      window.cancelAnimationFrame(rafId);
      rafId = 0;
    }
  }

  function syncState() {
    readRingColor();
    resizeCanvas();
    if (isMobile()) {
      stopLoop();
      return;
    }
    if (isReducedMotion()) {
      stopLoop();
      draw();
      return;
    }
    draw();
    startLoop();
  }

  function onResize() {
    if (resizeTimer) {
      window.clearTimeout(resizeTimer);
    }
    resizeTimer = window.setTimeout(function () {
      resizeTimer = 0;
      syncState();
    }, RESIZE_DEBOUNCE_MS);
  }

  function onThemeChange() {
    readRingColor();
    if (isReducedMotion() && !isMobile()) {
      draw();
    }
  }

  window.addEventListener('wheel', onWheel, { passive: true });
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onResize);

  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      stopLoop();
    } else {
      syncState();
    }
  });

  if (window.MutationObserver) {
    var observer = new MutationObserver(function (mutations) {
      for (var i = 0; i < mutations.length; i++) {
        if (mutations[i].attributeName === 'data-theme') {
          onThemeChange();
          break;
        }
      }
    });
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });
  }

  if (darkSchemeQuery && darkSchemeQuery.addEventListener) {
    darkSchemeQuery.addEventListener('change', onThemeChange);
  }

  if (reducedMotionQuery && reducedMotionQuery.addEventListener) {
    reducedMotionQuery.addEventListener('change', syncState);
  }

  syncState();
})();
