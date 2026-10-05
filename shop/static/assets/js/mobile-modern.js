(function () {
  "use strict";

  function initMaterialCalculator() {
    var calculator = document.querySelector(".dp-material-calculator");
    if (!calculator) return;

    var input = calculator.querySelector("#dp-area-input");
    var minus = calculator.querySelector("[data-area-minus]");
    var plus = calculator.querySelector("[data-area-plus]");
    var result = calculator.querySelector(".dp-calculator-result strong");
    var coverage = Number(calculator.getAttribute("data-coverage")) || 9;
    var coats = Number(calculator.getAttribute("data-coats")) || 2;

    function update(nextValue) {
      var area = Math.max(1, Number(nextValue) || 1);
      var litres = Math.ceil((area * coats) / coverage);
      input.value = String(area);
      result.textContent = litres + (litres === 1 ? " litra" : " litraa");
    }

    minus.addEventListener("click", function () {
      update(Number(input.value) - 1);
    });
    plus.addEventListener("click", function () {
      update(Number(input.value) + 1);
    });
    input.addEventListener("input", function () {
      update(input.value);
    });

    update(input.value);
  }

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
    initMaterialCalculator();
    initStickyProductPrice();
    improveMenuState();
    improveCheckoutSelection();
  });
})();
