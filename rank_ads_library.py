"""
Script to query an ADS library and construct the Sabine plots.
"""

from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd

from plot_mod import plot_ranks_plot
from requests_mod import (
    scrape_all_papers_given_month,
    scrape_bib_code_results,
    scrape_bib_codes,
    check_calls_available,
)

REQUEST_GET_TIMEOUT = 10  # Seconds.


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
    Function that identifies the publication date and citation number for a single paper
    based on a bibcode, and then extracts the distribution of citations for all refereed astronomy
    papers published in the same month. A percentage rank is then computed, ranking the paper
    against other papers from the month base on citation count.

    Arguments
    ----------
    bibcode: ADS bibcode of the targeted paper.
    token: User token. Can be generated here: https://ui.adsabs.harvard.edu/user/settings/token
    """

    doc = scrape_bib_code_results(bib_code, token)
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

        docs = scrape_all_papers_given_month(pub_date, cite_start, cite_end, token)
        if len(docs) == 2000:
            warnings.warn(
                f"Query limits reached in citation raneg {cite_start} to {cite_end}"
            )

        # Extracting the histogram of citations
        for doc in docs:
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


def get_library_ranks(library_code: str, token: str) -> pd.DataFrame:
    """
    For a given ADS library, identify the relevant bibcodes,
    and compile the rank statistics, saving an output dataframe.

    Arguments
    ---------
    library_code: ADS library access code.
    token: User token. Can be generated here: https://ui.adsabs.harvard.edu/user/settings/token
    """

    bib_codes = scrape_bib_codes(library_code, token)

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
    return output


def do_all(library_code: str, token: str, file_name: str) -> None:
    """
    Essentially a main function that will perform all the steps. For lazies.

    Input:
    library_code: NASA ADS libaray code (e.g. g3xxlnShS_iiymcLRdSUFg).
    token: User token. Can be generated here: https://ui.adsabs.harvard.edu/user/settings/token
    file_name: The file_name structure which will be used for the output data file and plots.

    Output:
    No output. Saves the rank data as <file_name>.csv and the plot as <file_name>.pdf
    """
    data_outfile = f"{file_name}.csv"
    plot_outfile = f"{file_name}.pdf"

    # Scrape and save library data.
    rank_df = get_library_ranks(library_code, token)
    rank_df.to_csv(data_outfile, index=False)

    # Save plots as pdf.
    plot_ranks_plot(rank_df, plot_outfile)


if __name__ == "__main__":
    # personal access token
    # (user-specific, to be accessed online at )
    TOKEN = "htI76Huxt0eloDKERX53ZkrczUUUhDzTkSll9Pjo"
    LIBRARY_CODE = "g3xxlnShS_iiymcLRdSUFg"
    SCRAPED_DATA_NAME = "bellstedt_first_author.csv"

    # Save the data as csv
    rank_data = get_library_ranks(LIBRARY_CODE, TOKEN)
    rank_data.to_csv(SCRAPED_DATA_NAME, index=False)

    plot_ranks_plot(SCRAPED_DATA_NAME, "bellstedt_plot.pdf")

    # extracting the statistics for just a single paper.
    stats = get_paper_rank(bib_code="2022MNRAS.517.6035T", token=TOKEN)

    # checking you still have requests
    check_calls_available(TOKEN)
