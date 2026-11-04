/* Keep advertising attribution without copying arbitrary query parameters. */
(function (root) {
    "use strict";
    root.DecoPaintAnalyticsLocation = function (href) {
        try {
            var url = new URL(href);
            if (url.protocol !== "https:" && url.protocol !== "http:") { return ""; }
            var safe = new URL(url.origin + url.pathname);
            ["gclid", "gbraid", "wbraid", "dclid", "utm_source", "utm_medium", "utm_campaign", "utm_id"].forEach(function (key) {
                var value = url.searchParams.get(key) || "";
                if (/^[A-Za-z0-9._~-]{1,256}$/.test(value)) {
                    safe.searchParams.set(key, value);
                }
            });
            return safe.href;
        } catch (error) {
            return "";
        }
    };
}(window));
