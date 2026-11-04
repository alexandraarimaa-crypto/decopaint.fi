(function () {
    "use strict";
    function packs(area, reserve, rate, amount) {
        if (![area, reserve, rate, amount].every(Number.isFinite) || area <= 0 || area > 100000 || reserve < 0 || reserve > 30 || rate <= 0 || amount <= 0) return null;
        return Math.ceil((area * (1 + reserve / 100) * rate) / amount - 1e-10);
    }
    window.DecoPaintSalesPacks = packs;
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("cart_form");
        if (!form) return;
        const calculatorElement = document.getElementById("sales-calculator-data");
        const calculator = calculatorElement ? JSON.parse(calculatorElement.textContent) : null;
        const result = document.getElementById("sales-calculator-result");
        const apply = document.getElementById("sales-apply-quantity");
        const area = document.getElementById("sales-area");
        const reserve = document.getElementById("sales-reserve");
        let selection = null, count = null;
        const submitButtons = () => document.querySelectorAll('#cart_form [type="submit"], .dp-mobile-sticky-buy button');
        function update() {
            if (!calculator) return;
            const size = selection && calculator.packages.find(pack => pack.label === selection.size);
            count = size ? packs(Number(area.value), Number(reserve.value), calculator.calculation_rate, size.amount) : null;
            apply.disabled = !count;
            result.textContent = count ? count + " × " + size.label + " · yhteensä " + (count * selection.price).toLocaleString("fi-FI", {style: "currency", currency: "EUR"}) + " (valittu pintamateriaali)" : "Valitse pakkauskoko ja syötä pinta-ala.";
        }
        document.addEventListener("decopaint:price-loading", function () {
            selection = null;
            submitButtons().forEach(button => { button.disabled = true; });
            update();
        });
        document.addEventListener("decopaint:price-ready", function (event) {
            selection = event.detail;
            submitButtons().forEach(button => { button.disabled = false; });
            update();
        });
        form.addEventListener("submit", function (event) {
            if (!selection) event.preventDefault();
        });
        if (calculator) {
            [area, reserve].forEach(input => input.addEventListener("input", update));
            apply.addEventListener("click", function () {
                if (!count) return;
                const quantity = document.getElementById("quantity");
                quantity.value = count;
                quantity.dispatchEvent(new Event("change", {bubbles: true}));
            });
        }
    });
})();
