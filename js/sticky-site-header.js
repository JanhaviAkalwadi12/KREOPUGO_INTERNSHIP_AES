(function () {
  'use strict';

  function updateStickyOffsets() {
    var root = document.documentElement;
    var social = document.querySelector('.top-social-bar');
    var schoolHeader = document.querySelector('.school-header');

    if (social) {
      root.style.setProperty('--site-social-height', social.getBoundingClientRect().height + 'px');
    }

    if (schoolHeader) {
      root.style.setProperty('--site-school-header-height', schoolHeader.getBoundingClientRect().height + 'px');
    }
  }

  function init() {
    updateStickyOffsets();

    if (window.ResizeObserver) {
      var observer = new ResizeObserver(updateStickyOffsets);
      var social = document.querySelector('.top-social-bar');
      var schoolHeader = document.querySelector('.school-header');
      if (social) observer.observe(social);
      if (schoolHeader) observer.observe(schoolHeader);
    }

    window.addEventListener('resize', updateStickyOffsets, { passive: true });
    window.addEventListener('load', updateStickyOffsets, { once: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
