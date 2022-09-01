"""
notify.py - Functions to perform email notifications via SendGrid
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

import pandas as pd
import base64
import os
import magic
from typing import List
import traceback
import logging

logger = logging.getLogger(__name__)


def send_email(
    to: List, subject: str = "TEST", html_content: str = "", attach_paths: List = []
) -> None:
    """Sends email notification via SendGrid API

    :param to: list of email recipients
    :param subject: email subject, defaults to 'TEST'
    :param html_content: email content (can use html tags), defaults to ''
    """

    # message details
    logger.info(f"Sending notification to {to}.")
    message = Mail(
        from_email="redacted@gmail.com",
        to_emails=to,
        subject=f"[REDACTED] {subject}",
        html_content=html_content,
    )

    # attachment
    for attach_path in attach_paths:
        with open(attach_path, "rb") as f:
            data = f.read()
            f.close()
        encoded_file = base64.b64encode(data).decode()

        mime = magic.Magic(mime=True)
        attached_file = Attachment(
            FileContent(encoded_file),
            FileName(os.path.basename(attach_path)),
            FileType(mime.from_file(attach_path)),
            Disposition("attachment"),
        )
        message.attachment = attached_file

    try:
        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)

        # check for valid response code
        if response.status_code != 202:
            logger.error("Status Code 202 not received - see below:")
            logger.error(response.body)
            logger.error(response.headers)
        else:
            logger.info("Notification successfully sent.")

    except Exception as e:
        logger.error(f"Sendgrid API invocation failed: {e.message}")
        logger.error(traceback.format_exc())


def send_error(to: List, script_name: str, e: str, tb: str, extra: str = "") -> None:
    """Wrapper for sending specifically error messages

    :param to: list of email recipients
    :param script_name: name of script that failed
    :param e: error message caught
    :param tb: traceback details
    :param extra: extra html content to include if any, defaults to ''
    """

    html_content = f"""
    <html>
        <body>
            <div>An error occurred during execution of <b>{script_name}</b>.</div>
            <div><b>Exception:</b></div>
            <div>{e}</div>
            <div><b>Traceback:</b></div>
            <div>{tb}</div>
            {extra}
        </body>
    </html>
    """

    send_email(to, f"FAILED SCRIPT: {script_name.upper()}", html_content=html_content)


def df_html_point(df_original: pd.DataFrame) -> str:
    """Helper function to clean up and return html of point dataframes

    :param df_original: Dataframe to clean
    :return: string representing html of dataframe table
    """

    df = df_original.copy()
    df = df.reset_index(drop=True)

    number_cols = ["q_id"]  # number only: e.g. 4000
    number_comma_cols = ["volume", "market_cap"]  # num with comma: e.g. 10,000

    for col in number_cols:
        if col in df.columns:
            df[col] = df[col].map("{:.0f}".format)

    for col in number_comma_cols:
        if col in df.columns:
            df[col] = df[col].map("{:,.0f}".format)

    if not df.empty:
        df["link"] = df.apply(
            lambda x: f'<a href="https://ca.finance.yahoo.com/quote/{x.symbol}" target="_blank">Link</a>',
            axis=1,
        )

    return df.to_html(escape=False)
