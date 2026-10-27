/* Optional administrator-entered information; independent of all calculations. */
(function () {
    'use strict';

    var currentPackage;

    window.prepareVariantMaterialInfo = function (size) {
        if (currentPackage !== size) {
            currentPackage = size;
            window.updateVariantMaterialInfo();
        }
    };

    window.updateVariantMaterialInfo = function (data) {
        data = data || {};
        var price = data.price_per_m2;
        var coverage = data.coverage_m2;
        var priceText = price === null || price === undefined || price === ''
            ? '' : 'alk. ' + String(price).replace('.', ',') + ' €/m²';
        var coverageText = coverage === null || coverage === undefined || String(coverage).trim() === ''
            ? '' : 'Riittoisuus ' + String(coverage).trim() + ' m²';

        [
            ['variant-price-per-m2', priceText],
            ['variant-coverage', coverageText]
        ].forEach(function (item) {
            var element = document.getElementById(item[0]);
            if (element) {
                element.textContent = item[1];
                element.hidden = item[1] === '';
            }
        });
    };
}());
