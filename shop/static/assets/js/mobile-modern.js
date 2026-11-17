(function () {
  "use strict";

  function initStickyProductPrice() {
    var source = document.getElementById("price-container");
    var target = document.querySelector("[data-mobile-price]");
    if (!source || !target) return;

    function syncPrice() {
      var value = (source.textContent || "").trim();
      target.textContent = value || "Valitse vaihtoehto";
    }

    syncPrice();
    if ("MutationObserver" in window) {
      new MutationObserver(syncPrice).observe(source, {
        childList: true,
        characterData: true,
        subtree: true,
        attributes: true,
      });
    }
  }

  function improveMenuState() {
    var menu = document.getElementById("offCanvasNavBar");
    if (!menu) return;

    menu.addEventListener("shown.bs.offcanvas", function () {
      var input = menu.querySelector("#mobile-search-input");
      if (input) input.focus();
    });
  }

  function improveCheckoutSelection() {
    var radios = document.querySelectorAll(
      ".dp-checkout-form-column .form-check-input[type='radio']"
    );
    if (!radios.length) return;

    function updateCards() {
      radios.forEach(function (radio) {
        var card = radio.closest(".form-check");
        if (card) card.classList.toggle("is-selected", radio.checked);
      });
    }

    radios.forEach(function (radio) {
      radio.addEventListener("change", updateCards);
    });
    updateCards();
  }

  document.addEventListener("DOMContentLoaded", function () {
    initStickyProductPrice();
    improveMenuState();
    improveCheckoutSelection();
  });
})();
