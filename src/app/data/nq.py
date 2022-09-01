"""
nq.py - Contains functions for data extraction from https://www.nasdaq.com
"""

from app.utils.scrape import extract_json, get_user_agent

import requests
from typing import List, Literal
import traceback
import logging

logger = logging.getLogger(__name__)


def get_quote_nq(
    handler: object,
    info: List[
        Literal[
            "data.summaryData.Exchange.value",
            "data.summaryData.Sector.value",
            "data.summaryData.Industry.value",
            "data.summaryData.OneYrTarget.value",
            "data.summaryData.TodayHighLow.value",
            "data.summaryData.ShareVolume.value",
            "data.summaryData.AverageVolume.value",
            "data.summaryData.PreviousClose.value",
            "data.summaryData.FiftTwoWeekHighLow.value",
            "data.summaryData.MarketCap.value",
            "data.summaryData.PERatio.value",
            "data.summaryData.ForwardPE1Yr.value",
            "data.summaryData.EarningsPerShare.value",
            "data.summaryData.AnnualizedDividend.value",
            "data.summaryData.ExDividendDate.value",
            "data.summaryData.DividendPaymentDate.value",
            "data.summaryData.Yield.value",
            "data.summaryData.Beta.value",
        ]
    ],
) -> List:
    """Obtains quote info from nasdaq.com

    :param handler: DataHandler instance of stock
    :param info: list of attributes to extract from response object
    :return: list of info contained from GET request
    """

    if handler.currency == "USD":
        ticker = handler.tickers["nq"]
        url = f"https://api.nasdaq.com/api/quote/{ticker}/summary?assetclass=stocks"

        try:
            res = requests.get(
                url, headers={"User-Agent": get_user_agent()}, timeout=30
            )

            if res.status_code == 200:
                results = res.json()
                if results["data"]:
                    return [extract_json(ref, results) for ref in info]

        except Exception as e:
            logger.error(f"Nasdaq API failed for {url} - looking for {info}: {e}")
            logger.error(traceback.format_exc())

    return [None] * len(info)


def get_exchange_nq(
    handler: object,
    info: List[Literal["data.summaryData.Exchange.value"]],
    prefix: str,
    currency: Literal["CAD", "USD"],
) -> List:
    """Searches for exchange on nasdaq.com for a given prefix

    :param handler: unused - DataHandler instance of stock
    :param info: hardcode to single item - ["summaryData.Exchange.value"]
    :param prefix: starting characters in ticker search query
    :param currency: currency ticker is associated with
    :return: single item array - [exchange]
    """

    if currency == "USD":
        url = f"https://api.nasdaq.com/api/quote/{prefix}/summary?assetclass=stocks"

        try:
            res = requests.get(
                url, headers={"User-Agent": get_user_agent()}, timeout=30
            )

            if res.status_code == 200:
                results = res.json()
                if results["data"]:
                    res_exchange = extract_json(
                        "data.summaryData.Exchange.value", results
                    )
                    logger.info(f"We got a response?: {res_exchange}")
                    if res_exchange:
                        res_exchange = res_exchange.lower()
                        if "nasdaq" in res_exchange:
                            return ["nasdaq"]
                        elif "nyse" in res_exchange:
                            return ["nyse"]

        except Exception as e:
            logger.error(f"Nasdaq API failed for {url} - looking for {info}: {e}")
            logger.error(traceback.format_exc())

    return [None] * len(info)
