import unittest
import app.utils.notify as notify
import logging

logger = logging.getLogger(__name__)


class TestNotify(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        logger.info("\n=== TESTING NOTIFY.PY ===")

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def test_send_email(self) -> None:
        """Ensure sendgrid notification is working"""

        notify.send_email(
            ["redacted@gmail.com"], "Testing", "<strong>Test content<strong>"
        )


if __name__ == "__main__":
    unittest.main()
