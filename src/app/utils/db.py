"""
db.py - Contains the DB class which handles interaction with our CockroachDB Serverless instance.

NOTE: this file has had many functions removed from it
"""

from app.config import _TABLES, _SOURCES_BONDS, _SOURCES_INDICES
from app.utils.decorators import retry_db

from datetime import datetime, timedelta
import json
import os
import psycopg2
from typing import List, Tuple, Literal
import logging
import concurrent.futures

logger = logging.getLogger(__name__)


class DB:
    """A class to organize pc database operations"""

    def __init__(self):
        """Constructor method"""

        conn_string = os.environ.get("COCKROACHDB_CONN_STR")

        keepalive_kwargs = {
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 5,
        }
        self.conn = psycopg2.connect(conn_string, **keepalive_kwargs)
        logger.debug("DB connection initiated.")

    @retry_db
    def update_user_settings(
        self, user: object, settings: dict, strict_update: bool = False
    ) -> None:
        """Adds user settings to _settings table

        :param user: instance of PCUser class
        :param settings: dictionary of settings (buy, sell, etc.)
        :param strict_update: denotes whether settings should just be updated w/o insertion, defaults to False
        """

        with self.conn.cursor() as cur:
            if strict_update:
                cur.execute(
                    """
                    UPDATE public._settings
                    SET settings = %s
                    WHERE setting_id = (
                        SELECT setting_id
                        FROM public._settings
                        WHERE username = %s
                        ORDER BY mod_date DESC LIMIT 1
                    )
                    """,
                    [json.dumps(settings), user.username],
                )
            else:
                cur.execute(
                    """
                    INSERT INTO public._settings (username, settings)
                    VALUES (%s, %s)
                    """,
                    [user.username, json.dumps(settings)],
                )
            logger.info(f"Settings updated for {user.username}.")

        self.conn.commit()

    @retry_db
    def get_user_settings(self, user: object) -> dict:
        """Obtains latest settings for user

        :param user: instance of PCUser class
        :return: settings dictionary for user
        """

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT settings
                FROM public._settings
                WHERE username = %s
                ORDER BY mod_date DESC LIMIT 1 
                """,
                [user.username],
            )
            row = cur.fetchone()

        self.conn.commit()

        return row[0] if row else None

    @retry_db
    def get_qid(self, yf_ticker: str) -> str:
        """Extracts QT symbol id for provided yf_ticker

        :param yf_ticker: ticker in YF format
        :return: QT symbol id (array size 0 no result, 1 if result)
        """

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT q_id
                FROM public."_point"
                WHERE symbol = %s
                LIMIT 1
                """,
                [yf_ticker],
            )
            row = cur.fetchone()

        return str(row[0]) if row else None

    @retry_db
    def get_point_by_currency(self, currency: Literal["CAD", "USD"]) -> List:
        """Extracts point symbols based on their currency.

        :param currency: currency to filter data from _point by
        :return: list of tickers with point data (filtered by currency)
        """

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public."_point"
                WHERE currency = %s
                """,
                [currency],
            )
            rows = cur.fetchall()

        self.conn.commit()

        return rows

    def close(self):
        """Terminates database connection"""

        self.conn.close()
        logger.debug("DB connection terminated.")
