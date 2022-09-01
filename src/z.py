"""
z.py - Scratch file to test code (run with ./build.sh "z")
"""

import app.app

from app.utils.db import DB
from app.config import _USERS, _TABLES

db = DB()

# from app.data.handler import DataHandler

# handler = DataHandler("AAPL", ticker_src="yf", exchange="nasdaq", currency="USD")

from app.exec.txn import check_txns

check_txns(_USERS[0])

db.close()
