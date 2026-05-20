"""Fetch Google Trends search interest data using the pytrends library."""

import pandas as pd
from pytrends.request import TrendReq


def fetch_trends(
    keywords: list[str],
    timeframe: str = "today 12-m",
    geo: str = "DE",
) -> pd.DataFrame:
    """Fetch interest over time data from Google Trends for the given keywords.

    Args:
        keywords: Search terms to query. Google Trends accepts at most 5 per request.
        timeframe: pytrends time range string. Default is the past 12 months.
        geo: Two letter country code restricting the search interest data. Default Germany.

    Returns:
        DataFrame indexed by date with one column per keyword (values 0 to 100)
        plus an 'isPartial' column flagging incomplete final periods.

    Raises:
        ValueError: If more than 5 keywords are passed.
    """
    if len(keywords) > 5:
        raise ValueError(
            f"Google Trends accepts at most 5 keywords per request, got {len(keywords)}"
        )

    # Realistic browser User-Agent so Google does not immediately flag the request
    # as automated. Without this, pytrends sends a Python default UA that Google
    # has learned to rate limit on the first request.
    browser_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    # hl is the host language (affects how Google interprets keywords).
    # tz is timezone offset in minutes from UTC; 60 is Berlin standard time.
    # retries + backoff_factor make pytrends retry transient 429 / 5xx responses
    # with exponential delays (1s, 2s, 4s) before giving up.
    pytrends = TrendReq(
        hl="de-DE",
        tz=60,
        retries=3,
        backoff_factor=1.0,
        requests_args={"headers": browser_headers},
    )

    pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)
    return pytrends.interest_over_time()
