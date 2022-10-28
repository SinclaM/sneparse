import unittest
from sneparse.coordinates import DecimalDegrees, HoursMinutesSeconds, DegreesMinutesSeconds

class StrTests(unittest.TestCase):
    def test_str_hours(self):
        self.assertEqual(str(HoursMinutesSeconds(-1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertNotEqual(str(HoursMinutesSeconds(1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 20, 33.5)), "+00:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 0, 0.0)), "+00:00:0.0")

    def test_str_degrees(self):
        self.assertEqual(str(DecimalDegrees(13.5)), "13.5°")
        self.assertEqual(str(DecimalDegrees(0.0)), "0.0°")
        self.assertEqual(str(DecimalDegrees(-20.0)), "-20.0°")

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

if __name__ == "__main__":
    unittest.main()
