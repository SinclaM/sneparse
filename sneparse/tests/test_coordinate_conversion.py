import unittest
from sneparse.coordinates import Degrees, HoursMinutesSeconds

class StrTests(unittest.TestCase):
    def test_str_hours(self):
        self.assertEqual(str(HoursMinutesSeconds(-1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertNotEqual(str(HoursMinutesSeconds(1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 20, 33.5)), "+00:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 0, 0.0)), "+00:00:0.0")

    def test_str_degrees(self):
        self.assertEqual(str(Degrees(13.5)), "13.5°")
        self.assertEqual(str(Degrees(0.0)), "0.0°")
        self.assertEqual(str(Degrees(-20.0)), "-20.0°")

class ConversionTests(unittest.TestCase):
    def test_deg_to_hms(self):
        self.assertEqual(HoursMinutesSeconds.fromDegrees(Degrees(0.0)), HoursMinutesSeconds(1, 0, 0, 0))
        self.assertEqual(HoursMinutesSeconds.fromDegrees(Degrees(10.0)), HoursMinutesSeconds(1, 0, 40, 0))
        self.assertEqual(HoursMinutesSeconds.fromDegrees(Degrees(232.64)), HoursMinutesSeconds(1, 15, 30, 33.6))

    def test_hms_to_deg(self):
        self.assertEqual(Degrees.fromHms(HoursMinutesSeconds(1, 0, 0, 0)), Degrees(0.0))
        self.assertEqual(Degrees.fromHms(HoursMinutesSeconds(-1, 0, 0, 0)), Degrees(0.0))
        self.assertEqual(Degrees.fromHms(HoursMinutesSeconds(1, 13, 24, 0)), Degrees(201.0))
        self.assertEqual(Degrees.fromHms(HoursMinutesSeconds(1, 15, 30, 33.6)), Degrees(232.64))

if __name__ == "__main__":
    unittest.main()
