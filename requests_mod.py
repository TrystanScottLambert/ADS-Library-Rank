"""
Module which handles the requests to NASA ADS
"""

from urllib.parse import urlencode
from datetime import datetime, UTC

import requests
import numpy as np

REQUEST_GET_TIMEOUT = 10  # Seconds.


def check_calls_available(token: str) -> None:
    """
    Checks how many ADS API calls are left using the given token.

    Prints remaining calls, total call limit, and reset time.
    """
    url = "https://api.adsabs.harvard.edu/v1/search/query?q=star"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers, timeout=REQUEST_GET_TIMEOUT)

    if response.status_code != 200:
        print(f"Error: HTTP {response.status_code}")
        print(response.text)
        return

    remaining = response.headers.get("X-RateLimit-Remaining")
    limit = response.headers.get("X-RateLimit-Limit")
    reset = response.headers.get("X-RateLimit-Reset")

    print(f"API Call Limit:     {limit}")
    print(f"Calls Remaining:    {remaining}")

    if reset:
        reset_time = datetime.fromtimestamp(int(reset), tz=UTC).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
        print(f"Limit Resets At:    {reset_time}")
    else:
        print("Reset time not provided in headers.")


def scrape_bib_code_results(bib_code: str, token) -> dict:
    """
    Scrapes ADS results for the given bib_code.
    """
    encoded_query = urlencode(
        {
            "q": f"bibcode:{bib_code}",
            "fl": "title, bibcode, citation_count, property, pubdate, author",
            "rows": 1000,
        }
    )

    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_GET_TIMEOUT,
    )

    doc = results.json()["response"]["docs"][0]
    return doc


def scrape_all_papers_given_month(
    pub_date: str, cite_start: int, cite_end: int, token: str
) -> list:
    """
    Scrapes all the ADS results for the month from a beginning citation to an ending citation
    (min/max citations)?
    """

    encoded_query = urlencode(
        {
            "q": (
                f"pubdate:[{pub_date} TO {pub_date}] "
                f"AND collection:astronomy AND property:refereed "
                f"AND citation_count:[{cite_start} TO {cite_end}]"
            ),
            "fl": "title, bibcode, citation_count, property, pubdate",
            "rows": 2000,
        }
    )

    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=REQUEST_GET_TIMEOUT,
    )
    return results.json()["response"]["docs"]


def scrape_bib_codes(library_code: str, token: str, rows: int = 1000) -> np.ndarray[str]:
    """
    Finds all the bib codes of the given library code
    """
    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_code}?rows={rows}",
        headers={"Authorization": "Bearer " + token},
        timeout=REQUEST_GET_TIMEOUT,
    )

    return np.array(
        [doc["bibcode"] for doc in results.json()["solr"]["response"]["docs"]]
    )
