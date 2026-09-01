(function () {
  "use strict";

  function initMaterialCalculator() {
    var calculator = document.querySelector(".dp-material-calculator");
    if (!calculator) return;

    var dataNode = document.getElementById("dp-material-calculator-data");
    if (!dataNode) return;

    var config;
    try {
      config = JSON.parse(dataNode.textContent);
    } catch (error) {
      return;
    }

    var input = calculator.querySelector("#dp-area-input");
    var minus = calculator.querySelector("[data-area-minus]");
    var plus = calculator.querySelector("[data-area-plus]");
    var requiredResult = calculator.querySelector("[data-material-required]");
    var coatsResult = calculator.querySelector("[data-material-coats]");
    var packageResult = calculator.querySelector("[data-package-recommendation]");
    var rate = Number(config.calculation_rate);
    var coats = Number(config.coats) || 1;
    var packages = Array.isArray(config.packages) ? config.packages : [];
    if (!input || !minus || !plus || !requiredResult || !packageResult || !rate || !packages.length) return;

    function greatestCommonDivisor(first, second) {
      while (second) {
        var remainder = first % second;
        first = second;
        second = remainder;
      }
      return first;
    }

    function packagePlan(requiredAmount) {
      var scale = 100;
      var packageSteps = packages.map(function (item) {
        return Math.max(1, Math.round(Number(item.amount) * scale));
      });
      var divisor = packageSteps.reduce(greatestCommonDivisor);
      var normalisedPackages = packageSteps.map(function (steps) {
        return steps / divisor;
      });
      var requiredSteps = Math.ceil((requiredAmount * scale) / divisor - 0.0000001);
      var limit = requiredSteps + Math.max.apply(Math, normalisedPackages);
      var counts = new Array(limit + 1).fill(Infinity);
      var previous = new Array(limit + 1).fill(-1);
      var usedPackage = new Array(limit + 1).fill(-1);
      counts[0] = 0;

      for (var total = 0; total <= limit; total += 1) {
        if (!Number.isFinite(counts[total])) continue;
        for (var index = 0; index < normalisedPackages.length; index += 1) {
          var next = total + normalisedPackages[index];
          if (next <= limit && counts[total] + 1 < counts[next]) {
            counts[next] = counts[total] + 1;
            previous[next] = total;
            usedPackage[next] = index;
          }
        }
      }

      var selectedTotal = -1;
      for (var candidate = requiredSteps; candidate <= limit; candidate += 1) {
        if (Number.isFinite(counts[candidate])) {
          selectedTotal = candidate;
          break;
        }
      }
      if (selectedTotal < 0) return null;

      var quantities = new Array(packages.length).fill(0);
      var cursor = selectedTotal;
      while (cursor > 0 && usedPackage[cursor] >= 0) {
        quantities[usedPackage[cursor]] += 1;
        cursor = previous[cursor];
      }
      return {
        quantities: quantities,
        total: (selectedTotal * divisor) / scale,
      };
    }

    function formatAmount(value) {
      return new Intl.NumberFormat(document.documentElement.lang || "fi", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
      }).format(value);
    }

    function unitLabel() {
      return config.unit === "l" ? "L" : "kg";
    }

    function formatPlan(plan) {
      if (!plan) return "";
      var parts = [];
      for (var index = packages.length - 1; index >= 0; index -= 1) {
        if (plan.quantities[index]) {
          parts.push(plan.quantities[index] + " × " + packages[index].label);
        }
      }
      return parts.join(" + ") + " (" + formatAmount(plan.total) + " " + unitLabel() + ")";
    }

    function update(nextValue) {
      var area = Math.max(1, Number(String(nextValue).replace(",", ".")) || 1);
      var requiredAmount = Math.ceil(area * rate * 100 - 0.0000001) / 100;
      var plan = packagePlan(requiredAmount);
      input.value = String(area);
      requiredResult.textContent = formatAmount(requiredAmount) + " " + unitLabel();
      packageResult.textContent = formatPlan(plan);
      if (coatsResult && config.coats_explicit) {
        var coatLabel = coats === 1 ? coatsResult.dataset.coatOne : coatsResult.dataset.coatMany;
        coatsResult.textContent = " · " + coats + " " + coatLabel;
      } else if (coatsResult) {
        coatsResult.textContent = "";
      }
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
      target.textContent = value || target.dataset.emptyLabel || target.textContent;
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
