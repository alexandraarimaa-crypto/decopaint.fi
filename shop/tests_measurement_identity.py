from django.test import SimpleTestCase
from shop.measurement_identity import parse_ga_client_id, parse_ga_session_id


class MeasurementIdentityTests(SimpleTestCase):
    def test_client_cookie_envelope_is_not_a_new_user(self):
        self.assertEqual(parse_ga_client_id("GA1.1.123456789.1793340000"), "123456789.1793340000")
        self.assertEqual(parse_ga_client_id("123456789.1793340000"), "123456789.1793340000")

    def test_both_session_cookie_generations_become_numeric_ids(self):
        self.assertEqual(parse_ga_session_id("GS1.1.1793340000.4.1.1793340010.0.0.0"), "1793340000")
        self.assertEqual(parse_ga_session_id("GS2.1.s1793340000$o4$g1$t1793340010$j60$l0$h0"), "1793340000")
        self.assertEqual(parse_ga_session_id("1793340000"), "1793340000")

    def test_unknown_or_personal_values_are_not_invented_identities(self):
        for value in [None, "", "person@example.invalid", "GA1.1", "1.2.3", "x" * 513]:
            self.assertEqual(parse_ga_client_id(value), "")
        for value in [None, True, "", "0", "-1", "1.2", "GS2.1.o1$t1793340000", "bad", "x" * 513]:
            self.assertEqual(parse_ga_session_id(value), "")
