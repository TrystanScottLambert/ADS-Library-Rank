"""
Script to query an ADS library and construct the Sabine plots.
"""

from urllib.parse import urlencode
from dataclasses import dataclass

import numpy as np
import pandas as pd
import requests

from plot_mod import plot_ranks_plot

REQUEST_GET_TIMEOUT = 10  #Seconds.


@dataclass
class PaperRankResult:
    """
    Class for storing the results from the get_paper_rank function.


    greater_citaitons: Number of refereed publications with greater citations than the target paper
    total_papers_month: Number of refereed astro publications in the same month as target paper
    percentage: Rank when compared against only papers with more citations
    percentage_upper: Rank when compared against publications with >= number of citations.
    author: Name of lead-author for target paper.
    pub_date: publication date of target paper.
    """

    greater_citations: int
    total_papers_month: int
    percentage: float
    percentage_upper: float
    author: str
    pub_date: str


def get_paper_rank(bib_code: str, token: str) -> PaperRankResult:
    """
    function that identifies the publication date and citation number for a single paper
    based on a bibcode, and then extracts the distribution of citations for all refereed astronomy
    papers published in the same month. A perentage rank is then computed, rnking the paper against
    other papers from the month base on citation count.

    Arguments
    ----------

    bibcode: ADS bibcode of the targeted paper.

    token: ADS API token (user-specific, to be accessed online at
    https://ui.adsabs.harvard.edu/user/settings/token)

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
    print(
        bib_code,
        doc["pubdate"][0:7],
        "Citations:",
        doc["citation_count"],
        doc["author"][0],
    )
    citation_count = doc["citation_count"]
    pub_date = doc["pubdate"][0:7]
    author = doc["author"][0].replace(" ", "")

    # Dividing the citation ditribution into chunks with fewer than 2000 hits, to not hit limit.
    citation_bounds = [0, 1, 2, 4, 10]

    citations = np.array([])

    for i, cite_bound in enumerate(citation_bounds):
        cite_start = cite_bound
        if i == len(citation_bounds) - 1:
            cite_end = 100_000
        else:
            cite_end = citation_bounds[i + 1] - 1

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
            headers={"Authorization": "Bearer " + token},
            timeout=REQUEST_GET_TIMEOUT,
        )

        if len(results.json()["response"]["docs"]) == 2000:
            print(
                (
                    f"WARNING: number of results in citation range {cite_start} to {cite_end} "
                    f"reached query limit"
                )
            )
            print("Need to add value to citationBounds ")

        # Extracting the histogram of citations
        for doc in results.json()["response"]["docs"]:
            citations = np.append(citations, doc["citation_count"])

    # Identifying the fraction with citations greater than or equal to the reference
    num_greater_citaitons = len(citations[citations >= citation_count])
    num_total_month_papers = len(citations)
    percentage = (num_greater_citaitons / num_total_month_papers) * 100
    percentage_upper = (
        len(citations[citations > citation_count]) / num_total_month_papers
    ) * 100
    print("Total astro refereed papers this month:", num_total_month_papers)
    print("Percentage rank of paper:", percentage)
    print("############################################################")

    result = PaperRankResult(
        num_greater_citaitons,
        num_total_month_papers,
        percentage,
        percentage_upper,
        author,
        pub_date,
    )
    return result


def get_library_ranks(library_code, output_name, token, rows=1000):
    """
    For a given ADS library, identify the relevant bibcodes,
    and compile the rank statistics, saving an output dataframe.

    Arguments
    ---------
    library_code: ADS library access code
    output_name: Name of output files
    token: api token
    rows: maximum number of papers to extract from library (default 1000)
    """

    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_code}?rows={rows}",
        headers={"Authorization": "Bearer " + token},
        timeout=REQUEST_GET_TIMEOUT,
    )
    bib_codes = np.array([])
    for doc in results.json()["solr"]["response"]["docs"]:
        bib_codes = np.append(bib_codes, doc["bibcode"])

    print(bib_codes)

    records = []
    for bibcode in bib_codes:
        statistics = get_paper_rank(bib_code=bibcode, token=token)
        records.append(
            {
                "Bibcode": bibcode,
                "Author": statistics.author,
                "PublicationDate": statistics.pub_date,
                "Rank": statistics.percentage,
                "Rank_upper": statistics.percentage_upper,
                "PaperNumber": statistics.total_papers_month,
            }
        )

    output = pd.DataFrame(records)
    output.to_csv(output_name + ".csv", index=False)


if __name__ == "__main__":

    # personal access token
    # (user-specific, to be accessed online at https://ui.adsabs.harvard.edu/user/settings/token)
    TOKEN = "htI76Huxt0eloDKERX53ZkrczUUUhDzTkSll9Pjo"

    # making the full output for a single ADS library.
    #make_library_ranks_plot(
    #    library_code="g3xxlnShS_iiymcLRdSUFg",
    #    output_name="Ranks_BellstedtFirstAuthor",
    #    token=TOKEN,
    #)

    plot_ranks_plot("Ranks_BellstedtFirstAuthor.csv", "Poo.pdf")

    # extracting the statistics for just a single paper.
    stats = get_paper_rank(bib_code = '2022MNRAS.517.6035T', token=TOKEN)
