"""
aws.py - Contains the AWSClient class which handles Lambda/S3 usage
"""

from app.config import _IS_LAMBDA_ENV

from typing import Literal
import boto3
import botocore
import os
import json
import traceback
import logging

logger = logging.getLogger(__name__)


class AWSClient:
    """A class to organize AWS functionality for PC"""

    def __init__(self, client_type: Literal["s3", "lambda"]) -> None:
        """Constructor method

        :param client_type: type of boto3 AWS client to instantiate
        """

        config = botocore.config.Config(
            read_timeout=900,
            connect_timeout=900,
            retries={"max_attempts": 0},
        )
        session = boto3.Session()

        if _IS_LAMBDA_ENV:
            client = session.client(client_type, config=config)
        else:
            client = session.client(
                client_type,
                aws_access_key_id=os.environ.get("USER_AWS_ACCESS_ID"),
                aws_secret_access_key=os.environ.get("USER_AWS_SECRET_KEY"),
                region_name=os.environ.get("AWS_REGION"),
                config=config,
            )

        self.client = client
        self.client_type = client_type

    def pc_lambda(self, payload: dict) -> dict:
        """Calls this lambda function (recursively)

        :param payload: dict of params for lambda execution
        :return: body of lambda call results
        """

        lambda_arn = os.environ.get("LAMBDA_ARN")

        try:
            res = self.client.invoke(
                FunctionName=lambda_arn,
                InvocationType="RequestResponse",
                Payload=payload,
            )
            data = json.loads(res.get("Payload").read())

            if ("statusCode" in data) and (data["statusCode"] == 200):
                return data["body"]
            else:
                logger.error(f"Failed status for lambda call - output: {data}")
        except Exception as e:
            logger.error(f"PC Lambda call error: {e}")
            logger.error(traceback.format_exc())

        return None

    def pc_s3_get(self, s3_key: str) -> object:
        """Gets object from S3 storage

        :param s3_key: key of file to retrieve
        :return: binary of retrieved file
        """

        bucket = os.environ.get("BUCKET_NAME")
        try:
            s3_res = self.client.get_object(Bucket=bucket, Key=s3_key)
            return s3_res["Body"].read()
        except Exception as e:
            logger.error(f"S3 GET error for {bucket}: {e}")
            logger.error(traceback.format_exc())

        return None

    def pc_s3_del(self, s3_key: str) -> None:
        """Deletes object from PC's S3 storage

        :param s3_key: key of file to delete
        """

        bucket = os.environ.get("BUCKET_NAME")
        try:
            self.client.delete_object(Bucket=bucket, Key=s3_key)
        except Exception as e:
            logger.error(f"S3 DELETE error for {bucket}: {e}")
            logger.error(traceback.format_exc())

    def pc_s3_upload(self, upload_path: str, s3_key: str) -> None:
        """Uploads object to PC's S3 storage

        :param upload_path: path where file to upload is located
        :param s3_key: upload file key
        """

        bucket = os.environ.get("BUCKET_NAME")
        try:
            self.client.upload_file(upload_path, bucket, s3_key)
        except Exception as e:
            logger.error(f"S3 UPLOAD error for {bucket}: {e}")
            logger.error(traceback.format_exc())
