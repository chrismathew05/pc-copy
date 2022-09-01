import app.app as app

import time
import unittest
import logging

logger = logging.getLogger(__name__)


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.info("\n=== TESTING APP.PY ===")

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    # runs for each test
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_lambda_handler(self) -> None:
        """Ensure lambda env configured properly"""

        self.assertTrue(time.tzname[0] == "EST")


if __name__ == "__main__":
    unittest.main()
