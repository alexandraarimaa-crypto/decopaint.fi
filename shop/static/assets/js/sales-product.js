(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        const form = document.getElementById("cart_form");
        if (!form) return;
        let selection = null;
        const submitButtons = () => document.querySelectorAll('#cart_form [type="submit"], .dp-mobile-sticky-buy button');
        document.addEventListener("decopaint:price-loading", function () {
            selection = null;
            submitButtons().forEach(button => { button.disabled = true; });
            document.querySelectorAll('[data-mobile-price]').forEach(label => { label.textContent = 'Ladataan hintaa…'; });
        });
        document.addEventListener("decopaint:price-ready", function (event) {
            selection = event.detail;
            submitButtons().forEach(button => { button.disabled = false; });
        });
        form.addEventListener("submit", function (event) {
            if (!selection) event.preventDefault();
        });
    });
})();
