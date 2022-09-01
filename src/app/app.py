"""
app.py - starting point for lambda function execution
"""

from app.utils.notify import send_error
from app.config import _IS_LAMBDA_ENV, _USERS
from app.utils.scrape import process_partition
from app.utils.aws import AWSClient
from app.exec.cleanup import update_point
from app.exec.txn import check_txns
from app.exec.after import update_stock_info
from app.exec.work import test_exec
from app.exec.test import test_pc

import json
import traceback
import logging


# Log settings
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(filename)s:%(funcName)s:%(lineno)d:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

# Additional set up based on environment ran from
if _IS_LAMBDA_ENV:
    logger.info("Setting up in AWS...")
else:
    logger.addHandler(stream_handler)
    logger.info("Setting up for local testing...")

    # add log file
    file_handler = logging.FileHandler("testing.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
logger.info("Set up complete!")


def lambda_handler(event: dict, context: dict) -> dict:
    """Starting point for AWS lambda call

    :param event: JSON doc containing data for lambda function to process
    :param context: Provides info about invocation, function and runtime env
    :return: Response object containing dictionary of results
    """

    # Process partition
    if "partitionPayload" in event:
        try:
            partition_payload = event["partitionPayload"]

            if bool(partition_payload):
                return process_partition(**partition_payload)
        except Exception as e:
            tb = traceback.format_exc()
            logger.info(f"An error occurred while processing partition: {e}")
            logger.error(tb)

            extra = f"""
            <div><b>Partition Payload:</b></div>
            <div>{event["partitionPayload"]}</div>
            """

            send_error(_USERS[0].notify_to, "partition", str(e), str(tb), extra)

            return {
                "statusCode": 500,
                "body": {"status": "Partition Processing Failed", "error": str(e)},
            }

    script = event["script"]
    logger.info(f"Initiating script: {script}")

    # Common scripts
    try:
        if script == "cleanup":
            update_point()
        elif script == "after":
            update_stock_info()
        elif script == "work":
            test_exec()
        elif script == "test":
            test_pc()

        ret_body = {
            "statusCode": 200,
            "body": {"status": f"Executed {script} successfully"},
        }
    except Exception as e:
        tb = traceback.format_exc()
        logger.info(f"Error during execution of common script {script}: {e}")
        logger.error(tb)

        send_error(_USERS[0].notify_to, script, str(e), str(tb))
        ret_body = {
            "statusCode": 500,
            "body": {
                "status": "Common Script Execution Failed",
                "error": f"{script}: {e}",
                "payload": [],
            },
        }

    # User-specific scripts
    if "SPLIT" in script:
        # denotes execution to be split among users
        logger.info(f"Splitting execution of {script}...")

        script = script.replace("SPLIT", "")
        lambda_client = AWSClient("lambda")
        lambda_client.pc_lambda(json.dumps({"script": script}))
        ret_body = {
            "statusCode": 200,
            "body": {"status": f"Successfully split {script}"},
        }
    else:
        for user in _USERS:
            try:
                if script == "test":
                    logger.info("Test script content here.")
                elif script == "txn":
                    check_txns(user)

                ret_body = {
                    "statusCode": 200,
                    "body": {
                        "status": f"Executed {script} successfully",
                        "payload": [],
                    },
                }
            except Exception as e:
                tb = traceback.format_exc()
                logger.info(
                    f"Error during execution of script {script} for {user.username}: {e}"
                )
                logger.error(tb)

                send_error(user.notify_to, script, str(e), str(tb))
                ret_body = {
                    "statusCode": 500,
                    "body": {
                        "status": "User Script Execution Failed",
                        "error": f"{script} for {user.username}: {e}",
                    },
                }

    logger.info(f"Script complete: {script}")
    return ret_body
