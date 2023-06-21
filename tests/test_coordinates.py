from typing import Tuple
from pathlib import Path
import pickle
import unittest

from tqdm import tqdm
from astropy.coordinates import Angle

from sneparse.definitions import ROOT_DIR
from sneparse.coordinates import *

class StrTests(unittest.TestCase):
    def test_str_hms(self):
        self.assertEqual(str(HoursMinutesSeconds(-1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertNotEqual(str(HoursMinutesSeconds(1, 11, 20, 33.5)), "-11:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 20, 33.5)), "+00:20:33.5")
        self.assertEqual(str(HoursMinutesSeconds(1, 0, 0, 0.0)), "+00:00:0.0")

    def test_str_degrees(self):
        self.assertEqual(str(DecimalDegrees(13.5)), "13.5")
        self.assertEqual(str(DecimalDegrees(0.0)), "0.0")
        self.assertEqual(str(DecimalDegrees(-20.0)), "-20.0")

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

    def test_cartesian_from_angular(self):
        ra  = DecimalDegrees(26.017046)
        dec = DecimalDegrees(-15.937469)
        expected  = Cartesian(0.86412070797, 0.421778115284, -0.27458809793)
        converted = Cartesian.from_angular(ra, dec)

        self.assertAlmostEqual(expected.x, converted.x)
        self.assertAlmostEqual(expected.y, converted.y)
        self.assertAlmostEqual(expected.z, converted.z)

        ra  = DecimalDegrees(278.482530)
        dec = DecimalDegrees(51.719061)
        expected  = Cartesian(0.0913837529926, -0.612740943018, 0.78498251346)
        converted = Cartesian.from_angular(ra, dec)

        self.assertAlmostEqual(expected.x, converted.x)
        self.assertAlmostEqual(expected.y, converted.y)
        self.assertAlmostEqual(expected.z, converted.z)


class ParsingTests(unittest.TestCase):
    def test_parse_hms(self):
        self.assertEqual(HoursMinutesSeconds.from_str("+12:03:23.5"), HoursMinutesSeconds(1, 12, 3, 23.5))

        self.assertEqual(HoursMinutesSeconds.from_str("-00:10:59.7"), HoursMinutesSeconds(-1, 0, 10, 59.7))

        # missing sign is equivalent to positive
        self.assertEqual(HoursMinutesSeconds.from_str("12:03:23.5"), HoursMinutesSeconds(1, 12, 3, 23.5))

        self.assertEqual(HoursMinutesSeconds.from_str("12:023.5"), HoursMinutesSeconds(1, 12, 23, 30))

        self.assertEqual(HoursMinutesSeconds.from_str("023.5"), HoursMinutesSeconds(1, 23, 30, 0))

        # empty input
        with self.assertRaises(Exception):
            HoursMinutesSeconds.from_str("")

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

        # missing sign is equivalent to positive
        self.assertEqual(DegreesMinutesSeconds.from_str("12:03:23.5"), DegreesMinutesSeconds(1, 12, 3, 23.5))

        self.assertEqual(DegreesMinutesSeconds.from_str("-00:10:59.7"), DegreesMinutesSeconds(-1, 0, 10, 59.7))

        self.assertEqual(DegreesMinutesSeconds.from_str("12:023.5"), DegreesMinutesSeconds(1, 12, 23, 30))

        self.assertEqual(DegreesMinutesSeconds.from_str("023.5"), DegreesMinutesSeconds(1, 23, 30, 0))

        # empty input
        with self.assertRaises(Exception):
            DegreesMinutesSeconds.from_str("")

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


class BulkParsingTests(unittest.TestCase):
    def test_bulk(self):
        print("Beginning bulk test")
        with open(Path(__file__).parent.joinpath("angle_dump.pickle"), "rb") as f:
            angles: list[Tuple[str, str]] = pickle.load(f)

        for (ra, dec) in tqdm(angles):
            with self.subTest(ra=ra, dec=dec):
                self.assertAlmostEqual(DecimalDegrees.from_hms(HoursMinutesSeconds.from_str(ra)).degrees,
                                       Angle(f"{ra} h").degree)

                self.assertAlmostEqual(DecimalDegrees.from_dms(DegreesMinutesSeconds.from_str(dec)).degrees,
                                       Angle(f"{dec} d").degree)

class DistanceTests(unittest.TestCase):
    def test_angular_separation(self):
        self.assertEqual(angular_separation(DecimalDegrees(11.88804),
                                            DecimalDegrees(-25.288278),
                                            DecimalDegrees(233.73837),
                                            DecimalDegrees(23.502639)),
                         DecimalDegrees(141.99780547))

        self.assertEqual(angular_separation(DecimalDegrees(0.0),
                                            DecimalDegrees(-90.0),
                                            DecimalDegrees(0.0),
                                            DecimalDegrees(90.0)),
                         DecimalDegrees(180.0))

        self.assertEqual(angular_separation(DecimalDegrees(0.0),
                                            DecimalDegrees(-90.0),
                                            DecimalDegrees(360.0),
                                            DecimalDegrees(90.0)),
                         DecimalDegrees(180.0))

        self.assertEqual(angular_separation(DecimalDegrees(0.0),
                                            DecimalDegrees(0.0),
                                            DecimalDegrees(20.0),
                                            DecimalDegrees(0.0)),
                         DecimalDegrees(20.0))

        self.assertEqual(angular_separation(DecimalDegrees(0.0),
                                            DecimalDegrees(0.0),
                                            DecimalDegrees(0.0),
                                            DecimalDegrees(0.0)),
                         DecimalDegrees(0.0))

    def test_dist_sqr(self):
        p = Cartesian(0.0, 0.0, 0.0)
        q = Cartesian(0.0, 0.0, 0.0)
        self.assertAlmostEqual(dist_sqr(p, q), 0.0)

        p = Cartesian(1.0, 0.0, 0.0)
        q = Cartesian(0.0, 0.0, 0.0)
        self.assertAlmostEqual(dist_sqr(p, q), 1.0)

        p = Cartesian(1.0, 0.0, 0.0)
        q = Cartesian(0.0, 1.0, 0.0)
        self.assertAlmostEqual(dist_sqr(p, q), 2.0)

        p = Cartesian(7.0, 4.0, 3.0)
        q = Cartesian(17.0, 6.0, 2.0)
        self.assertAlmostEqual(dist_sqr(p, q), 105.0)

    def test_angle_between(self):
        p = Cartesian(1.0, 0.0, 0.0)
        q = Cartesian(1.0, 0.0, 0.0)
        self.assertAlmostEqual(angle_between(p, q).degrees, 0.0)

        p = Cartesian(1.0, 0.0, 0.0)
        q = Cartesian(0.0, 1.0, 0.0)
        self.assertAlmostEqual(angle_between(p, q).degrees, 90.0)

        p = Cartesian(3.0, 6.0, 1.0)
        q = Cartesian(-5.0, -9.0, 4.0)
        self.assertAlmostEqual(angle_between(p, q).degrees, 150.189, places=3)

if __name__ == "__main__":
    unittest.main()
