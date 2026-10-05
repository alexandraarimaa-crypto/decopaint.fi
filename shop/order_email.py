SUPPORTED_EMAIL_LANGUAGES = {"fi", "sv", "en"}


ORDER_EMAIL_COPY = {
    "fi": {
        "subject": "Tilausvahvistus – Deco Paint",
        "greeting": "Hei",
        "thanks": "Kiitos tilauksestasi verkkokaupassamme!",
        "summary": "Tilauksen yhteenveto",
        "order_number": "Tilausnumero",
        "order_date": "Tilauksen päivämäärä",
        "delivery_address": "Toimitusosoite",
        "pickup_location": "Noutopaikka",
        "shipping_method": "Toimitustapa",
        "payment_method": "Maksutapa",
        "products": "Tilaamasi tuotteet",
        "description": "Kuvaus",
        "quantity": "Määrä",
        "price": "Hinta",
        "size": "Koko",
        "color": "Sävy",
        "grain": "Raekoko",
        "gloss": "Kiilto",
        "subtotal": "Välisumma",
        "discount": "Alennus",
        "shipping": "Toimitus",
        "free_shipping": "Ilmainen toimitus",
        "total": "Yhteensä",
        "vat": "Josta arvonlisävero",
        "questions": "Jos sinulla on kysyttävää tilauksestasi, autamme mielellämme.",
        "closing": "Ystävällisin terveisin",
        "team": "Deco Paint Finland Oy -tiimi",
    },
    "sv": {
        "subject": "Orderbekräftelse – Deco Paint",
        "greeting": "Hej",
        "thanks": "Tack för din beställning i vår webbutik!",
        "summary": "Sammanfattning av beställningen",
        "order_number": "Ordernummer",
        "order_date": "Beställningsdatum",
        "delivery_address": "Leveransadress",
        "pickup_location": "Upphämtningsplats",
        "shipping_method": "Leveranssätt",
        "payment_method": "Betalningssätt",
        "products": "Produkter i din beställning",
        "description": "Beskrivning",
        "quantity": "Antal",
        "price": "Pris",
        "size": "Storlek",
        "color": "Kulör",
        "grain": "Kornstorlek",
        "gloss": "Glans",
        "subtotal": "Delsumma",
        "discount": "Rabatt",
        "shipping": "Leverans",
        "free_shipping": "Fri leverans",
        "total": "Totalt",
        "vat": "Varav moms",
        "questions": "Om du har frågor om din beställning hjälper vi dig gärna.",
        "closing": "Med vänliga hälsningar",
        "team": "Deco Paint Finland Oy-teamet",
    },
    "en": {
        "subject": "Order confirmation – Deco Paint",
        "greeting": "Hello",
        "thanks": "Thank you for your order from our online store!",
        "summary": "Order summary",
        "order_number": "Order number",
        "order_date": "Order date",
        "delivery_address": "Delivery address",
        "pickup_location": "Pickup location",
        "shipping_method": "Delivery method",
        "payment_method": "Payment method",
        "products": "Products in your order",
        "description": "Description",
        "quantity": "Quantity",
        "price": "Price",
        "size": "Size",
        "color": "Colour",
        "grain": "Grain size",
        "gloss": "Gloss",
        "subtotal": "Subtotal",
        "discount": "Discount",
        "shipping": "Delivery",
        "free_shipping": "Free delivery",
        "total": "Total",
        "vat": "Including VAT",
        "questions": "If you have any questions about your order, we are happy to help.",
        "closing": "Kind regards",
        "team": "Deco Paint Finland Oy team",
    },
}


SHIPPING_METHOD_COPY = {
    "pickup": {
        "fi": "Nouto myymälästä",
        "sv": "Hämtning i butik",
        "en": "Store pickup",
    },
    "weight_based": {
        "fi": "Painoperusteinen toimitus",
        "sv": "Viktbaserad leverans",
        "en": "Weight-based delivery",
    },
    "postnord_lokero": {
        "fi": "PostNord-palvelupiste",
        "sv": "PostNord-serviceställe",
        "en": "PostNord service point",
    },
    "postnord_kotiinkuljetus": {
        "fi": "PostNord-kotiinkuljetus",
        "sv": "PostNord hemleverans",
        "en": "PostNord home delivery",
    },
}


PAYMENT_METHOD_COPY = {
    "online": {
        "fi": "Verkkomaksu",
        "sv": "Nätbetalning",
        "en": "Online payment",
    },
    "cod": {
        "fi": "Maksetaan noudettaessa",
        "sv": "Betalas vid upphämtning",
        "en": "Pay on pickup",
    },
}


def normalize_email_language(language_code):
    language = str(language_code or "fi").lower().replace("_", "-").split("-", 1)[0]
    return language if language in SUPPORTED_EMAIL_LANGUAGES else "fi"


def build_order_email_context(order, order_detail_url, language_code):
    language = normalize_email_language(language_code)
    copy = ORDER_EMAIL_COPY[language]
    is_pickup = order.shipping_method == "pickup"

    shipping_method = SHIPPING_METHOD_COPY.get(order.shipping_method, {}).get(
        language,
        order.get_shipping_method_display(),
    )
    payment_method = PAYMENT_METHOD_COPY.get(order.payment_method, {}).get(
        language,
        order.get_payment_method_display(),
    )

    if is_pickup:
        address_label = copy["pickup_location"]
        address_value = "Deco Paint Finland Oy, Asessorinkatu 12, 20780 Kaarina"
    else:
        address_label = copy["delivery_address"]
        address_value = f"{order.address}, {order.postal} {order.city}"

    return {
        "order": order,
        "order_detail_url": order_detail_url,
        "email_language": language,
        "copy": copy,
        "address_label": address_label,
        "address_value": address_value,
        "shipping_method_label": shipping_method,
        "payment_method_label": payment_method,
    }
