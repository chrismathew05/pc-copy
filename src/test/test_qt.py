from app.data.qt import QT
from app.data.handler import DataHandler

import unittest
import logging

logger = logging.getLogger(__name__)


class TestQt(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.info("\n=== TESTING QT.PY ===")
        cls.qt = QT()

    def test_get_mkt_quote(self) -> None:
        """Test market quote extraction from QT"""
        handler = DataHandler("AAPL", "yf", exchange="nasdaq", qt=self.qt)
        [symbol, isHalted] = self.qt.get_mkt_quote(handler, ["symbol", "isHalted"])
        self.assertTrue(not isHalted)
        self.assertEqual(symbol, "AAPL")

    def test_get_symbol_info(self) -> None:
        """Test symbol info extraction from QT"""

        handler = DataHandler("AAPL", "yf", exchange="nasdaq", qt=self.qt)
        [vol, cap] = self.qt.get_symbol_info(
            handler, ["averageVol3Months", "marketCap"]
        )
        self.assertGreater(float(vol), 1000000)
        self.assertGreater(float(cap), 1000000)

    def test_get_exchange(self) -> None:
        """Test exchange extraction from QT"""

        [exchange] = self.qt.get_exchange({}, ["listingExchange"], "AAPL", "USD")
        self.assertEqual(exchange.lower(), "nasdaq")


if __name__ == "__main__":
    unittest.main()
