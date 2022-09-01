"""
decorators.py - Contains decorators utilized throughout the script
"""

from app.utils.driver import terminate_driver
from app.utils.notify import send_email

import os
from datetime import datetime
import time
import random
import psycopg2
from functools import wraps
import traceback
import logging

logger = logging.getLogger(__name__)
_MAX_RETRIES = 5


def retry_db(func: object) -> None:
    """Decorator to wait + retry DB functions in case of serialization errors

    :param func: function to retry when serialization error encountered
    :raises ValueError: raised when max number of retries reached
    :raises e: error raised in case of non-serialization failure
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # retry fx until max retries reached
        conn = args[0].conn
        retries = 0
        while True:
            retries += 1
            if retries == _MAX_RETRIES:
                err_msg = f"Transaction did not succeed after {_MAX_RETRIES} retries"
                raise ValueError(err_msg)

            try:
                return func(*args, **kwargs)

            except psycopg2.Error as e:
                # check if error codes pertain to serialization errors
                # venv/lib/python3.8/site-packages/psycopg2/errorcodes.py
                logger.info("e.pgcode: {}".format(e.pgcode))
                if e.pgcode == "40001" or e.pgcode == "25P02":

                    # exponential backoff while retrying txn
                    conn.rollback()
                    logger.info("SERIALIZATION FAILURE: RETRYING TXN")
                    sleep_ms = (2**retries) * 0.1 * (random.random() + 0.5)
                    logger.info("Sleeping {} seconds".format(sleep_ms))
                    time.sleep(sleep_ms)
                    continue
                else:
                    # error not pertaining to serialization failure - simply raise normally
                    logger.error(f"NON-SERIALIZATION_FAILURE: {e}")
                    logger.error(traceback.format_exc())
                    raise e

    return wrapper


def alert_driver_failure(func: object) -> None:
    """Decorator to screenshot/quit driver execution in case of failure

    :param func: driver execution to try
    :raises e: error raised in case of driver execution failure
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # retry fx until max retries reached
        # driver = args[1]
        # user = args[2]
        driver = kwargs["driver"]
        user = kwargs["user"]

        try:
            return func(*args, **kwargs)

        except Exception as e:
            # save screenshot of driver page
            dt_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            screenshot_path = f"/tmp/{dt_str}-SCREENSHOT.png"
            driver.get_screenshot_as_file(screenshot_path)

            # save page source
            source_path = f"/tmp/{dt_str}-SOURCE.txt"
            with open(source_path, "w") as f:
                f.write(driver.page_source)

            # log details
            tb = traceback.format_exc()
            logger.info(f"An error occurred during driver execution: {e}")
            logger.error(tb)

            # notify user
            html_content = f"""
            <html>
                <body>
                    <div>An error occurred during driver execution. See attachments for details.</div>
                    <div><b>Exception:</b></div>
                    <div>{e}</div>
                    <div><b>Traceback:</b></div>
                    <div>{tb}</div>
                </body>
            </html>
            """

            send_email(
                user.notify_to,
                subject="DRIVER EXECUTION ERROR",
                html_content=html_content,
                attach_paths=[screenshot_path, source_path],
            )

            os.remove(screenshot_path)
            os.remove(source_path)

            raise e

    return wrapper
