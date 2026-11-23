/**
 * SynthDex Search Page Interactions
 * Loading feedback on search submit, double submit prevention,
 * and asynchronous favorite toggling enhancement.
 */
(function () {
  'use strict';

  var searchForm = document.getElementById('search-form');
  var submitBtn = document.getElementById('search-submit-btn');

  if (searchForm && submitBtn) {
    searchForm.addEventListener('submit', function (e) {
      if (searchForm.dataset.submitting === 'true') {
        e.preventDefault();
        return;
      }
      searchForm.dataset.submitting = 'true';
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner" aria-hidden="true"></span> <span>Searching…</span>';
    });
  }

  // Progressive enhancement for heart/favorite toggle buttons on search results
  document.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form.classList.contains('favorite-form-inline')) {
      return;
    }

    e.preventDefault();
    var button = form.querySelector('.btn-heart');
    var isCurrentlyFavorite = button.classList.contains('is-favorite');
    var nextState = !isCurrentlyFavorite;

    // Optimistically update UI
    button.classList.toggle('is-favorite', nextState);
    button.setAttribute('aria-label', nextState ? 'Remove from favorites' : 'Save to favorites');
    button.title = nextState ? 'Remove from favorites' : 'Save to favorites';
    button.innerHTML = nextState
      ? '<svg class="icon" aria-hidden="true"><use href="#i-heart-fill"/></svg>'
      : '<svg class="icon" aria-hidden="true"><use href="#i-heart"/></svg>';

    var formData = new FormData(form);
    fetch(form.action, {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    }).catch(function () {
      // Revert if network error
      button.classList.toggle('is-favorite', isCurrentlyFavorite);
    });
  });
})();
