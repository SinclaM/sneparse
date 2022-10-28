import unittest
from sneparse.coordinates import DecimalDegrees, HoursMinutesSeconds, DegreesMinutesSeconds

class StrTests(unittest.TestCase):
    def test_str_hms(self):
        self.assertEqual(str(HoursMinutesSeconds(-1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertNotEqual(str(HoursMinutesSeconds(1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 20, 33.5)), "+00:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 0, 0.0)), "+00:00:0.0")

    def test_str_degrees(self):
        self.assertEqual(str(DecimalDegrees(13.5)), "13.5°")
        self.assertEqual(str(DecimalDegrees(0.0)), "0.0°")
        self.assertEqual(str(DecimalDegrees(-20.0)), "-20.0°")

    def test_str_dms(self):
        self.assertEqual(str(DegreesMinutesSeconds(-1, 42, 20, 33.5)), "-42:20:33.5")
        self.assertNotEqual(str(DegreesMinutesSeconds(1, 42, 20, 33.5)), "-42:20:33.5")
        self.assertEqual(str(DegreesMinutesSeconds(1, 0, 20, 33.5)), "+00:20:33.5")
        self.assertEqual(str(DegreesMinutesSeconds(1, 0, 0, 0.0)), "+00:00:0.0")


class ConversionTests(unittest.TestCase):
    def test_deg_to_hms(self):
        self.assertEqual(HoursMinutesSeconds.from_decimal_degrees(DecimalDegrees(0.0)),
                         HoursMinutesSeconds(1, 0, 0, 0))
        self.assertEqual(HoursMinutesSeconds.from_decimal_degrees(DecimalDegrees(10.0)),
                         HoursMinutesSeconds(1, 0, 40, 0))
        self.assertEqual(HoursMinutesSeconds.from_decimal_degrees(DecimalDegrees(232.64)),
                         HoursMinutesSeconds(1, 15, 30, 33.6))

    def test_hms_to_deg(self):
        self.assertEqual(DecimalDegrees.from_hms(HoursMinutesSeconds(1, 0, 0, 0)), DecimalDegrees(0.0))
        self.assertEqual(DecimalDegrees.from_hms(HoursMinutesSeconds(-1, 0, 0, 0)), DecimalDegrees(0.0))
        self.assertEqual(DecimalDegrees.from_hms(HoursMinutesSeconds(1, 13, 24, 0)), DecimalDegrees(201.0))
        self.assertEqual(DecimalDegrees.from_hms(HoursMinutesSeconds(1, 15, 30, 33.6)), DecimalDegrees(232.64))

    def test_deg_to_dms(self):
        self.assertEqual(DegreesMinutesSeconds.from_decimal_degrees(DecimalDegrees(0.0)), 
                         DegreesMinutesSeconds(1, 0, 0, 0.0))
        self.assertEqual(DegreesMinutesSeconds.from_decimal_degrees(DecimalDegrees(100.0)), 
                         DegreesMinutesSeconds(1, 100, 0, 0.0))
        self.assertEqual(DegreesMinutesSeconds.from_decimal_degrees(DecimalDegrees(20.245)), 
                         DegreesMinutesSeconds(1, 20, 14, 42))

    def test_dms_to_deg(self):
        self.assertEqual(DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 0, 0, 0)), DecimalDegrees(0.0))
        self.assertEqual(DecimalDegrees.from_dms(DegreesMinutesSeconds(-1, 0, 0, 0)), DecimalDegrees(0.0))
        self.assertEqual(DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 234, 23, 42.2)), 
                         DecimalDegrees(234.3950556))
        self.assertEqual(DecimalDegrees.from_dms(DegreesMinutesSeconds(1, 10, 11, 12.3)), 
                         DecimalDegrees(10.18675))

class ParsingTests(unittest.TestCase):
    def test_parse_hms(self):
        self.assertEqual(HoursMinutesSeconds.from_str("+12:03:23.5"), HoursMinutesSeconds(1, 12, 3, 23.5))
        self.assertEqual(HoursMinutesSeconds.from_str("-00:10:59.7"), HoursMinutesSeconds(-1, 0, 10, 59.7))

        # empty input
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("")

        # malformed delimeters
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("+12:0323.5")

        # missing sign
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("12:03:23.5")

        # bad sign
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("?12:03:23.5")

        # bad hours
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("-12.1:03:23.5")

        # bad minutes
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("-12.1:3?:23.5")

        # bad seconds
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("-12.1:03:23.5.")

    def test_parse_dms(self):
        self.assertEqual(DegreesMinutesSeconds.from_str("+12:03:23.5"), DegreesMinutesSeconds(1, 12, 3, 23.5))
        self.assertEqual(DegreesMinutesSeconds.from_str("-00:10:59.7"), DegreesMinutesSeconds(-1, 0, 10, 59.7))

        # empty input
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("")

        # malformed delimeters
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("+12:0323.5")

        # missing sign
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("12:03:23.5")

        # bad sign
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("?12:03:23.5")

        # bad degrees
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("-12.1:03:23.5")

        # bad minutes
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("-12.1:3?:23.5")

        # bad seconds
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("-12.1:03:23.5.")


if __name__ == "__main__":
    unittest.main()
