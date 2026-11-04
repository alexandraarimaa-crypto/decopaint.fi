(function () {
    "use strict";

    const allowedEvents = new Set([
        "view_item",
        "add_to_cart",
        "remove_from_cart",
        "view_cart",
        "begin_checkout",
        "add_shipping_info",
        "add_payment_info",
        "purchase",
        "view_search_results",
        "login",
        "sign_up",
        "generate_lead"
    ]);
    const forbiddenKeys = new Set([
        "email",
        "phone",
        "address",
        "postal",
        "city",
        "first_name",
        "last_name",
        "name",
        "notes",
        "transaction_provider_id"
    ]);
    const pendingEvents = [];
    const emailPattern = /[^@\s]+@[^@\s]+\.[^@\s]+/g;
    const phonePattern = /\+?\d[\d\s().-]{5,}\d/g;

    function readJsonElement(id) {
        const element = document.getElementById(id);
        if (!element) {
            return null;
        }
        try {
            return JSON.parse(element.textContent);
        } catch (error) {
            return null;
        }
    }

    function readConsent() {
        const encoded = document.cookie
            .split(";")
            .map(function (part) { return part.trim(); })
            .find(function (part) { return part.indexOf("cookie_settings=") === 0; });
        if (!encoded) {
            return {};
        }
        try {
            return JSON.parse(decodeURIComponent(encoded.split("=").slice(1).join("=")));
        } catch (error) {
            return {};
        }
    }

    function hasAnalyticsConsent() {
        return readConsent().analytics_storage === "granted";
    }

    function cleanString(value) {
        return String(value)
            .replace(emailPattern, "[redacted]")
            .replace(phonePattern, function(candidate) {
                const digits = (candidate.match(/\d/g) || []).length;
                const formatted = candidate.charAt(0) === "+" || /[\s().-]/.test(candidate);
                return formatted && digits >= 7 ? "[redacted]" : candidate;
            })
            .slice(0, 200);
    }

    function sanitize(value, key) {
        if (forbiddenKeys.has(String(key || "").toLowerCase())) {
            return undefined;
        }
        if (Array.isArray(value)) {
            return value.slice(0, 200).map(function (item) {
                return sanitize(item, "");
            }).filter(function (item) {
                return item !== undefined;
            });
        }
        if (value && typeof value === "object") {
            const output = {};
            Object.keys(value).forEach(function (childKey) {
                const cleanValue = sanitize(value[childKey], childKey);
                if (cleanValue !== undefined) {
                    output[childKey] = cleanValue;
                }
            });
            return output;
        }
        if (typeof value === "string") {
            return cleanString(value);
        }
        if (typeof value === "number" || typeof value === "boolean") {
            return value;
        }
        return undefined;
    }

    function dedupeKey(name, params) {
        if (name === "purchase" && params && params.transaction_id) {
            return "decopaint_ga4_purchase_" + params.transaction_id;
        }
        return "";
    }

    function send(name, params) {
        if (!allowedEvents.has(name) || typeof window.gtag !== "function") {
            return false;
        }
        const cleanParams = sanitize(params || {}, "");
        const storageKey = dedupeKey(name, cleanParams);
        if (storageKey && window.sessionStorage.getItem(storageKey)) {
            return false;
        }
        window.gtag("event", name, cleanParams);
        if (storageKey) {
            window.sessionStorage.setItem(storageKey, "sent");
        }
        return true;
    }

    function track(name, params) {
        if (!allowedEvents.has(name)) {
            return false;
        }
        if (!hasAnalyticsConsent()) {
            pendingEvents.push({name: name, params: params || {}});
            return false;
        }
        return send(name, params);
    }

    function applyUserContext() {
        if (!hasAnalyticsConsent() || typeof window.gtag !== "function") {
            return;
        }
        const config = readJsonElement("ga4-config");
        if (!config || !config.measurement_id || !config.user) {
            return;
        }
        const userContext = sanitize(config.user, "");
        if (userContext.user_id) {
            window.gtag("config", config.measurement_id, {
                user_id: userContext.user_id
            });
        }
        window.gtag("set", "user_properties", {
            login_status: userContext.login_status || "guest"
        });
    }

    function flushPending() {
        if (!hasAnalyticsConsent()) {
            return;
        }
        applyUserContext();
        while (pendingEvents.length) {
            const event = pendingEvents.shift();
            send(event.name, event.params);
        }
    }

    function queuePageEvent() {
        const event = readJsonElement("ga4-page-event");
        if (event && event.name && event.params) {
            track(event.name, event.params);
        }
    }

    window.DecoPaintAnalytics = {
        track: track,
        readPayload: readJsonElement,
        hasAnalyticsConsent: hasAnalyticsConsent,
        flush: flushPending
    };

    document.addEventListener("decopaint:consent-updated", flushPending);
    document.addEventListener("DOMContentLoaded", function () {
        applyUserContext();
        queuePageEvent();
    });
})();
