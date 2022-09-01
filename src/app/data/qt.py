"""
qt.py - Contains functions for data extraction from Questrade
"""

from app.utils.db import DB
from app.config import _EXCHANGES_LITERAL, _YF_EXCHANGE_MAP

from typing import List, Literal, Tuple
import requests
import time
import traceback
import logging
import re

logger = logging.getLogger(__name__)


class QT:
    """A class to organize interaction with Questrade's API

    https://www.questrade.com/api/documentation/rest-operations/market-calls/symbols-id
    """

    def __init__(self) -> None:
        """Constructor method"""

        self.get_auth()

    def get_auth(self) -> Tuple:
        """Obtains credentials for QT API

        :return: tuple of (access token, refresh token, api server)
        """

        # obtain credentials from DB
        db = DB()
        rows = dict(db.get_temp_info(("QT_REFRESH", "QT_ACCESS", "QT_API_SERVER")))
        access_token = rows["QT_ACCESS"]
        api_server = rows["QT_API_SERVER"]
        refresh_token = rows["QT_REFRESH"]

        try:
            # attempt using credentials to get QT time
            headers = {"Authorization": f"Bearer {access_token}"}
            url = "v1/time"
            time.sleep(0.01)
            res = requests.get(f"{api_server}{url}", headers=headers)
            res = res.json()
            logger.info(f'Valid QT access token - time: {res["time"]}')
        except Exception as e:
            # if invalid, refresh credentials
            logger.error(f"Invalid QT access token - refreshing: {e}")
            access_token, refresh_token, api_server = self.update_tokens(refresh_token)

        self.access, self.refresh, self.api_server = (
            access_token,
            refresh_token,
            api_server,
        )

    def update_tokens(self, refresh_token: str) -> Tuple:
        """Obtains new credentials via QT OAuth and upserts new refresh to DB.

        :param refresh_token: QT refresh token
        :return: Tuple of access token, refresh token, api server url
        """

        # obtain new credentials
        db = DB()
        url = "https://login.questrade.com/oauth2/token"
        params = {"grant_type": "refresh_token", "refresh_token": refresh_token}
        res = requests.post(url, params=params)
        access_token, refresh_token, api_server = None, None, None

        if res.status_code == 200:
            res = res.json()
            access_token = res["access_token"]
            refresh_token = res["refresh_token"]
            api_server = res["api_server"]

            # upsert to DB
            db.upsert(
                "_temp",
                [
                    ("QT_REFRESH", refresh_token),
                    ("QT_ACCESS", access_token),
                    ("QT_API_SERVER", api_server),
                ],
            )
            logger.debug("QT API tokens successfully updated!")
        else:
            logger.error(f"QT API token failed to refresh: {res.content}")

        # return results
        db.close()
        return access_token, refresh_token, api_server

    def get_req(
        self,
        url: str,
        params: object,
        max_retries: int = 3,
        retry_interval: float = 1,
    ) -> dict:
        """Wrapper for QT GET API request

        :param url: GET url
        :param params: params for GET request
        :param max_retries: max num retries if rate limiting is encountered
        :param retry_interval: time in seconds to wait between retries
        :return: JSON response from GET request
        """

        num_retries = 0
        while num_retries < max_retries:
            if self.api_server is None or self.access is None:
                self.get_auth()
            try:
                headers = {"Authorization": f"Bearer {self.access}"}
                res = requests.get(
                    f"{self.api_server}{url}",
                    headers=headers,
                    params=params,
                    timeout=30,
                )

                if res.status_code == 200:
                    return res.json()

                if res.status_code == 429:
                    logger.debug(f"QT RATE LIMIT - wait a sec.")
                    time.sleep(retry_interval)

            except Exception as e:
                logger.error(f"QT API FAILED url:[{url}] params:[{params}]: {e}")
                logger.error(traceback.format_exc())

            num_retries += 1

        return None

    def get_time(self) -> tuple:
        """Gets current time from QT

        :return: tuple of (hour, minute)
        """

        ts = self.get_req("v1/time", {})["time"]
        groups = re.search(r"T(\d*):(\d*)", ts).groups()
        if len(groups) == 2:
            return (int(groups[0]), int(groups[1]))

        return None

    def get_mkt_quote(
        self,
        handler: object,
        info: List[
            Literal[
                "symbol",
                "symbolId",
                "tier",
                "bidPrice",
                "bidSize",
                "askPrice",
                "askSize",
                "lastTradePriceTrHrs",
                "lastTradePrice",
                "lastTradeSize",
                "lastTradeTick",
                "lastTradeTime",
                "volume",
                "openPrice",
                "highPrice",
                "lowPrice",
                "delay",
                "isHalted",
            ]
        ],
    ) -> List:
        """Obtains market quote for symbol on Questrade
        https://www.questrade.com/api/documentation/rest-operations/market-calls/markets-quotes-id

        :param handler: DataHandler object
        :param info: list of desired attributes available in QT JSON response
        :return: list of values matching request
        """

        # check if DB contains QID
        yf_ticker = handler.tickers["yf"]
        url = "v1/markets/quotes/"

        qid = None
        db = DB()
        qid = db.get_qid(yf_ticker)
        db.close()

        if qid:
            url += qid
            params = {}

            try:
                # extract desired attributes
                res = self.get_req(url, params)
                if res:
                    quotes = res["quotes"]
                    if quotes:
                        quote = quotes[0]
                        return [quote[i] if i in quote else None for i in info]

            except Exception as e:
                logger.error(f"QT quote extraction error for {url}: {e}")
                logger.error(traceback.format_exc())

        return [None] * len(info)

    def get_symbol_info(
        self,
        handler: object,
        info: List[
            Literal[
                "symbol",
                "symbolId",
                "prevDayClosePrice",
                "averageVol3Months",
                "outstandingShares",
                "eps",
                "pe",
                "dividend",
                "exDate",
                "marketCap",
                "listingExchange",
                "description",
                "securityType",
                "isQuotable",
                "currency",
                "industrySector",
            ]
        ],
        force_search: bool = False,
    ) -> List:
        """Obtains requested symbol info from QT endpoint v1/symbols/
        https://www.questrade.com/api/documentation/rest-operations/market-calls/symbols-id

        :param handler: DataHandler object
        :param info: list of desired attributes available in QT JSON response
        :param force_search: set to True to skip using id stored in DB for query, defaults to False
        :return: list of values matching request
        """

        # check if DB already contains QID
        yf_ticker = handler.tickers["yf"]
        qt_ticker = handler.tickers["qt"]
        url = "v1/symbols/"

        qid = None
        if not force_search:
            db = DB()
            qid = db.get_qid(yf_ticker)
            db.close()

        if qid:
            params = {"ids": qid}
        else:
            params = {"names": qt_ticker}

        try:
            # extract desired attributes
            res = self.get_req(url, params)
            if res:
                symbols = res["symbols"]
                for symbol_info in symbols:
                    if (
                        symbol_info["isQuotable"]
                        and symbol_info["securityType"] == "Stock"
                    ):
                        # exchange check
                        res_exchange = symbol_info["listingExchange"].lower()
                        if res_exchange == "nyseam":
                            res_exchange = "nyse"
                        elif res_exchange == "cnsx":
                            res_exchange = "cse"

                        exchange = handler.exchange.lower()
                        if exchange == res_exchange:
                            return [
                                symbol_info[i] if i in symbol_info else None
                                for i in info
                            ]
        except Exception as e:
            logger.error(f"QT symbol info extraction error for {params}: {e}")
            logger.error(traceback.format_exc())

        return [None] * len(info)

    def get_exchange(
        self,
        handler: object,
        info: List[Literal["listingExchange"]],
        prefix: str,
        currency: Literal["CAD", "USD"],
    ) -> List[_EXCHANGES_LITERAL]:
        """Searches for exchange on QT for a given prefix

        :param handler: unused - provided to allow for use in DataHandler
        :param info: hardcode to single item - ["listingExchange"]
        :param prefix: starting characters in ticker search query
        :param currency: currency ticker is associated with
        :return: single item array - [exchange]
        """

        # set up search request
        url = "v1/symbols/search"
        params = {"prefix": prefix}

        try:
            res = self.get_req(url, params)
            if res:
                symbols = res["symbols"]
                for symbol_info in symbols:

                    # exchange check
                    res_exchange = symbol_info["listingExchange"].lower()
                    if res_exchange == "nyseam":
                        res_exchange = "nyse"
                    elif res_exchange == "cnsx":
                        res_exchange = "cse"

                    if (
                        currency == symbol_info["currency"]
                        and symbol_info["isQuotable"]
                        and symbol_info["securityType"] == "Stock"
                        and res_exchange in _YF_EXCHANGE_MAP.keys()
                    ):
                        return [res_exchange]
        except Exception as e:
            logger.error(f"QT extraction error for {params}: {e}")
            logger.error(traceback.format_exc())

        return [None] * len(info)
