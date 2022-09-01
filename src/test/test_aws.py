from app.utils.aws import AWSClient

import unittest
import logging

logger = logging.getLogger(__name__)


class TestAWS(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.info("\n=== TESTING AWS.PY ===")


if __name__ == "__main__":
    unittest.main()
