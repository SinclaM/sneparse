from typing import Any
import unittest
import json
from datetime import datetime

from sneparse.record import SneRecord
from sneparse.coordinates import DegreesMinutesSeconds, HoursMinutesSeconds

class RecordParsingTests(unittest.TestCase):
    def test_from_oac(self):
        s = \
        """
        {
            "ASASSN-20ao":{
                "schema":"https://github.com/astrocatalogs/supernovae/blob/d3ef5fc/SCHEMA.md",
                "name":"ASASSN-20ao",
                "sources":[
                    {
                        "name":"2016A&A...594A..13P",
                        "bibcode":"2016A&A...594A..13P",
                        "reference":"Planck Collaboration et al. (2016)",
                        "alias":"1"
                    },
                    {
                        "name":"ATel 13413",
                        "url":"http://www.astronomerstelegram.org/?read=13413",
                        "alias":"2"
                    },
                    {
                        "name":"Gaia Photometric Science Alerts",
                        "url":"http://gsaweb.ast.cam.ac.uk/alerts/alertsindex",
                        "alias":"3"
                    },
                    {
                        "name":"ASAS-SN Supernovae",
                        "url":"http://www.astronomy.ohio-state.edu/~assassin/sn_list.html",
                        "alias":"4"
                    },
                    {
                        "name":"Latest Supernovae",
                        "secondary":true,
                        "url":"http://www.rochesterastronomy.org/snimages/snredshiftall.html",
                        "alias":"5"
                    },
                    {
                        "name":"The Open Supernova Catalog",
                        "bibcode":"2017ApJ...835...64G",
                        "reference":"Guillochon et al. (2017)",
                        "secondary":true,
                        "url":"https://sne.space",
                        "alias":"6"
                    }
                ],
                "alias":[
                    {
                        "value":"ASASSN-20ao",
                        "source":"2,5"
                    },
                    {
                        "value":"AT2020aap",
                        "source":"2,3,4,5"
                    },
                    {
                        "value":"Gaia20aok",
                        "source":"2,5"
                    }
                ],
                "claimedtype":[
                    {
                        "value":"Candidate",
                        "source":"3"
                    }
                ],
                "comovingdist":[
                    {
                        "value":"109.71",
                        "derived":true,
                        "u_value":"Mpc",
                        "source":"1,2,4,5,6"
                    }
                ],
                "dec":[
                    {
                        "value":"-51:30:39.47",
                        "u_value":"degrees",
                        "source":"2,5"
                    },
                    {
                        "value":"-51:30:39.6",
                        "u_value":"degrees",
                        "source":"2,3,4"
                    }
                ],
                "discoverdate":[
                    {
                        "value":"2020/01/15",
                        "source":"2,5"
                    }
                ],
                "discoverer":[
                    {
                        "value":"ASAS-SN",
                        "source":"2,5"
                    }
                ],
                "host":[
                    {
                        "value":"WISEA J005446.43-513036.9",
                        "source":"2,4"
                    }
                ],
                "hostdec":[
                    {
                        "value":"-51:30:36.9",
                        "derived":true,
                        "u_value":"degrees",
                        "source":"6"
                    }
                ],
                "hostoffsetang":[
                    {
                        "value":"3.47",
                        "u_value":"arcseconds",
                        "source":"2,4"
                    }
                ],
                "hostoffsetdist":[
                    {
                        "value":"1.8",
                        "source":"1,2,4,5,6"
                    }
                ],
                "hostra":[
                    {
                        "value":"00:54:46.43",
                        "derived":true,
                        "u_value":"hours",
                        "source":"6"
                    }
                ],
                "lumdist":[
                    {
                        "value":"112.443",
                        "derived":true,
                        "u_value":"Mpc",
                        "source":"1,2,4,5,6"
                    }
                ],
                "maxabsmag":[
                    {
                        "value":"-19.0479",
                        "derived":true,
                        "source":"1,2,4,5,6"
                    }
                ],
                "maxappmag":[
                    {
                        "value":"16.18",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "maxband":[
                    {
                        "value":"G",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "maxdate":[
                    {
                        "value":"2020/02/01",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "maxvisualabsmag":[
                    {
                        "value":"-19.0747",
                        "derived":true,
                        "source":"1,2,4,5,6"
                    }
                ],
                "maxvisualappmag":[
                    {
                        "value":"16.18",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "maxvisualband":[
                    {
                        "value":"G",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "maxvisualdate":[
                    {
                        "value":"2020/02/01",
                        "derived":true,
                        "source":"3,6"
                    }
                ],
                "ra":[
                    {
                        "value":"00:54:46.189",
                        "u_value":"hours",
                        "source":"2,5"
                    },
                    {
                        "value":"00:54:46.248",
                        "u_value":"hours",
                        "source":"3"
                    },
                    {
                        "value":"00:54:46.176",
                        "u_value":"hours",
                        "source":"2,4"
                    }
                ],
                "redshift":[
                    {
                        "value":"0.024934",
                        "source":"2,4,5"
                    }
                ],
                "velocity":[
                    {
                        "value":"7381.9",
                        "u_value":"km/s",
                        "source":"6"
                    }
                ],
                "photometry":[
                    {
                        "time":"58880.42288",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"16.22",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58880.59903",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"16.18",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58880.67303",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"16.22",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58900.44174",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"17.05",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58900.61789",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"17.04",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58900.69190",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"17.04",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58951.19833",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"18.71",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58951.27234",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"18.73",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58978.23619",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"19.19",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    },
                    {
                        "time":"58978.31020",
                        "band":"G",
                        "e_magnitude":"0.0",
                        "instrument":"Astrometric",
                        "magnitude":"19.25",
                        "telescope":"GAIA",
                        "u_time":"MJD",
                        "source":"3"
                    }
                ]
            }
        }
        """

        d: dict[str, Any] = json.loads(s)
        self.assertEqual(SneRecord.from_oac(d),
                         SneRecord("ASASSN-20ao",
                                   HoursMinutesSeconds.from_str("00:54:46.189"),
                                   DegreesMinutesSeconds.from_str("-51:30:39.47"),
                                   datetime(2020, 1, 15),
                                   "Candidate",
                                   "OAC")
                         )

if __name__ == "__main__":
    unittest.main()
