"""Consent-aware, idempotent GA4 purchase delivery via Measurement Protocol."""
from __future__ import annotations

import logging
import os
from datetime import timedelta

import requests
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from shop.analytics import build_purchase_event

from .models import Order

logger = logging.getLogger(__name__)

DEFAULT_MEASUREMENT_ID = "G-HXEJKEB3MW"
COLLECT_URL = "https://region1.google-analytics.com/mp/collect"
DEBUG_URL = "https://region1.google-analytics.com/debug/mp/collect"


def _setting(name, default=""):
    return str(
        getattr(settings, name, "") or os.environ.get(name, default)
    ).strip()


def _request_params():
    measurement_id = _setting("GA4_MEASUREMENT_ID", DEFAULT_MEASUREMENT_ID)
    api_secret = _setting("GA4_API_SECRET")
    if not measurement_id or not api_secret:
        raise RuntimeError("GA4 Measurement Protocol is not configured")
    return {
        "measurement_id": measurement_id,
        "api_secret": api_secret,
    }


def _payload(order, debug_mode=False):
    purchase = build_purchase_event(order)
    params = dict(purchase["params"])
    params["engagement_time_msec"] = 1
    if order.ga_session_id:
        params["session_id"] = order.ga_session_id
    if debug_mode:
        params["debug_mode"] = True

    event_time = order.paid_at or order.updated or order.created
    consent = {
        "ad_user_data": (
            "GRANTED" if order.ads_consent == "granted" else "DENIED"
        ),
        "ad_personalization": (
            "GRANTED"
            if order.ads_personalization_consent == "granted"
            else "DENIED"
        ),
    }
    return {
        "client_id": order.ga_client_id,
        "timestamp_micros": int(event_time.timestamp() * 1_000_000),
        "consent": consent,
        "events": [{"name": "purchase", "params": params}],
    }


def _mark(order, status, error="", **extra):
    order.ga_purchase_status = status
    order.ga_purchase_last_error = error[:1000]
    update_fields = [
        "ga_purchase_status",
        "ga_purchase_last_error",
        "updated",
    ]
    for field, value in extra.items():
        setattr(order, field, value)
        update_fields.append(field)
    order.save(update_fields=update_fields)


def validate_ga4_purchase(order):
    """Validate the exact production payload without collecting an event."""
    payload = _payload(order, debug_mode=True)
    payload["validation_behavior"] = "ENFORCE_RECOMMENDATIONS"
    response = requests.post(
        DEBUG_URL,
        params=_request_params(),
        json=payload,
        timeout=25,
    )
    response.raise_for_status()
    messages = response.json().get("validationMessages", [])
    return messages if isinstance(messages, list) else []


def upload_ga4_purchase(order_id):
    """Send one paid, consented order to GA4 exactly once."""
    try:
        with transaction.atomic():
            order = Order.objects.select_for_update().get(id=order_id)
            if order.ga_purchase_status == "sent":
                return "sent"
            if (
                order.ga_purchase_status == "pending"
                and order.ga_purchase_last_attempt_at
                and order.ga_purchase_last_attempt_at
                > timezone.now() - timedelta(minutes=5)
            ):
                return "pending"
            if not order.payed:
                _mark(order, "not_ready")
                return "not_ready"
            if order.analytics_consent != "granted":
                _mark(order, "skipped_no_consent")
                return "skipped_no_consent"
            if not order.ga_client_id:
                _mark(order, "skipped_no_client_id")
                return "skipped_no_client_id"

            order.ga_purchase_status = "pending"
            order.ga_purchase_attempts += 1
            order.ga_purchase_last_attempt_at = timezone.now()
            order.ga_purchase_last_error = ""
            order.save(update_fields=[
                "ga_purchase_status",
                "ga_purchase_attempts",
                "ga_purchase_last_attempt_at",
                "ga_purchase_last_error",
                "updated",
            ])
    except Order.DoesNotExist:
        return "missing"

    try:
        messages = validate_ga4_purchase(order)
        if messages:
            error = "; ".join(
                str(message.get("description") or message)
                for message in messages
                if isinstance(message, dict)
            ) or "GA4 rejected the purchase payload"
            _mark(order, "failed", error)
            return "failed"

        response = requests.post(
            COLLECT_URL,
            params=_request_params(),
            json=_payload(order),
            timeout=25,
        )
        if response.status_code != 204:
            _mark(
                order,
                "failed",
                f"GA4 collection request returned HTTP {response.status_code}",
            )
            return "failed"
    except RuntimeError as exc:
        _mark(order, "waiting_configuration", str(exc))
        return "waiting_configuration"
    except Exception:
        _mark(order, "failed", "GA4 purchase delivery failed")
        logger.exception("GA4 purchase delivery failed for order %s", order_id)
        return "failed"

    _mark(order, "sent", ga_purchase_sent_at=timezone.now())
    return "sent"


def reconcile_paid_ga4_purchases(limit=200):
    """Retry paid purchases that were not durably delivered."""
    from django_q.tasks import async_task

    order_ids = list(
        Order.objects.filter(
            payed=True,
            analytics_consent="granted",
            ga_purchase_status__in=[
                "not_ready",
                "pending",
                "waiting_configuration",
                "failed",
            ],
        )
        .exclude(ga_client_id="")
        .values_list("id", flat=True)[:limit]
    )
    for order_id in order_ids:
        async_task("order.ga4.upload_ga4_purchase", order_id)
    return {"uploads": len(order_ids)}
