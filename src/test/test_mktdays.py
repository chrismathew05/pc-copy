import app.utils.mktdays as mktdays

from datetime import datetime
import unittest
import logging

logger = logging.getLogger(__name__)


class TestMktDays(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.info("\n=== TESTING MKTDAYS.PY ===")

    def test_is_weekend(self) -> None:
        """Test weekend check"""

        dt = datetime(2022, 4, 17)
        self.assertTrue(mktdays.is_weekend(dt))

    def test_mkt_open(self) -> None:
        "Test market open check"

        # Washington's Birthday
        dt = datetime(2022, 2, 21)
        self.assertTrue(not mktdays.mkt_open("nyse", dt))

        # Martin Luther King, Jr. Day
        dt = datetime(2022, 1, 17)
        self.assertTrue(not mktdays.mkt_open("nyse", dt))

        # Good Friday
        dt = datetime(2022, 4, 15)
        self.assertTrue(not mktdays.mkt_open("nyse", dt))

        # Canada Day
        dt = datetime(2022, 7, 1)
        self.assertTrue(not mktdays.mkt_open("tsx", dt))

        # Next year Christmas Day
        today = datetime.today()
        dt = datetime(today.year + 1, 12, 25)
        self.assertTrue(not mktdays.mkt_open("tsx", dt))


if __name__ == "__main__":
    unittest.main()
