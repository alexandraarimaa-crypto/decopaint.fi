"""Public showroom information for the owner-confirmed December relocation."""
from datetime import datetime, date
from zoneinfo import ZoneInfo

MOVE_DATE = date(2026, 12, 1)
NOTICE_START = date(2026, 11, 17)
NOTICE_END = date(2027, 1, 1)
NEW_STREET = "Voivalantie 30"
POSTCODE_CITY = "20780 Kaarina"
DIRECTIONS_URL = "https://www.google.com/maps/dir/?api=1&destination=Voivalantie+30%2C+20780+Kaarina%2C+Finland"

COPY = {
    "fi": {
        "moving_title": "Muutamme 1.12.",
        "open_title": "Uusi showroom on avoinna",
        "moving_text": "Showroom on suljettu muuton ajan. Verkkokauppa palvelee normaalisti.",
        "open_text": "Tervetuloa uuteen showroomiin! Verkkokauppa palvelee normaalisti.",
        "future_address": "Uusi osoite 1.12.2026 alkaen",
        "current_address": "Showroomin osoite",
        "old_location": "Asessorinkatu 12: showroom on suljettu muuton vuoksi.",
        "future_hours": "Showroomin aukioloajat 1.12. alkaen",
        "current_hours": "Showroomin aukioloajat",
        "closed": "Showroom on suljettu 30.11.2026 asti muuton vuoksi.",
        "weekdays": "Ma–Pe", "weekend": "La–Su", "appointment": "Sovittaessa",
        "shop": "Verkkokauppaan", "details": "Lisätiedot",
        "future_directions": "Reitti uuteen showroomiin (1.12. alkaen)",
        "directions": "Reittiohjeet",
        "pickup_moving": "Showroom on suljettu muuton ajan. Sovi noudosta etukäteen: 0400 414 838. Uusi osoite 1.12. alkaen: Voivalantie 30, Kaarina.",
        "pickup_open": "Nouto: Voivalantie 30, 20780 Kaarina. Ma–Pe 9:00–17:00, La–Su sovittaessa.",
        "online": "Verkkokauppa palvelee normaalisti.",
    },
    "sv": {
        "moving_title": "Vi flyttar den 1.12.",
        "open_title": "Vårt nya showroom är öppet",
        "moving_text": "Showroomet är stängt under flytten. Webbutiken fungerar som vanligt.",
        "open_text": "Välkommen till vårt nya showroom! Webbutiken fungerar som vanligt.",
        "future_address": "Ny adress från 1.12.2026", "current_address": "Showroomets adress",
        "old_location": "Asessorinkatu 12: showroomet är stängt på grund av flytten.",
        "future_hours": "Showroomets öppettider från 1.12.", "current_hours": "Showroomets öppettider",
        "closed": "Showroomet är stängt till och med 30.11.2026 på grund av flytten.",
        "weekdays": "Mån–Fre", "weekend": "Lör–Sön", "appointment": "Enligt överenskommelse",
        "shop": "Till webbutiken", "details": "Mer information",
        "future_directions": "Hitta till det nya showroomet (från 1.12.)", "directions": "Vägbeskrivning",
        "pickup_moving": "Showroomet är stängt under flytten. Kom överens om avhämtning i förväg: 0400 414 838. Ny adress från 1.12.: Voivalantie 30, Kaarina.",
        "pickup_open": "Avhämtning: Voivalantie 30, 20780 Kaarina. Mån–Fre 9:00–17:00, Lör–Sön enligt överenskommelse.",
        "online": "Webbutiken fungerar som vanligt.",
    },
    "en": {
        "moving_title": "We are moving on 1 December",
        "open_title": "Our new showroom is open",
        "moving_text": "The showroom is closed during the move. Our online shop is operating as usual.",
        "open_text": "Welcome to our new showroom! Our online shop is operating as usual.",
        "future_address": "New address from 1 December 2026", "current_address": "Showroom address",
        "old_location": "Asessorinkatu 12: the showroom is closed for relocation.",
        "future_hours": "Showroom opening hours from 1 December", "current_hours": "Showroom opening hours",
        "closed": "The showroom is closed through 30 November 2026 for relocation.",
        "weekdays": "Mon–Fri", "weekend": "Sat–Sun", "appointment": "By appointment",
        "shop": "Shop online", "details": "More information",
        "future_directions": "Directions to the new showroom (from 1 December)", "directions": "Directions",
        "pickup_moving": "The showroom is closed during the move. Please arrange collection in advance: 0400 414 838. New address from 1 December: Voivalantie 30, Kaarina.",
        "pickup_open": "Collection: Voivalantie 30, 20780 Kaarina. Mon–Fri 9:00–17:00, Sat–Sun by appointment.",
        "online": "Our online shop is operating as usual.",
    },
}


def showroom_information(language="fi", today=None):
    """Switch on the Helsinki calendar date, independently of visitor time zone."""
    today = today if today is not None else datetime.now(ZoneInfo("Europe/Helsinki")).date()
    language = (language or "fi").lower().split("-")[0]
    text = COPY.get(language, COPY["fi"])
    moved = today >= MOVE_DATE
    return {
        **text,
        "moved": moved,
        "show_banner": NOTICE_START <= today < NOTICE_END,
        "title": text["open_title"] if moved else text["moving_title"],
        "text": text["open_text"] if moved else text["moving_text"],
        "address_label": text["current_address"] if moved else text["future_address"],
        "hours_title": text["current_hours"] if moved else text["future_hours"],
        "map_label": text["directions"] if moved else text["future_directions"],
        "pickup_notice": text["pickup_open"] if moved else text["pickup_moving"],
        "new_street": NEW_STREET, "postcode_city": POSTCODE_CITY,
        "directions_url": DIRECTIONS_URL,
    }
