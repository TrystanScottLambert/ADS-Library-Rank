"""
Script to query an ADS library and construct the Sabine plots.
"""

import os
from urllib.parse import urlencode
from dataclasses import dataclass

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

FONT_SIZE = 12
REQUEST_GET_TIMEOUT = 10  # seconds
mpl.rcParams.update(
    {
        "font.size": FONT_SIZE,
        "xtick.major.size": 8,
        "ytick.major.size": 8,
        "xtick.major.width": 1,
        "ytick.major.width": 1,
        "ytick.minor.size": 4,
        "xtick.minor.size": 4,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "axes.linewidth": 1,
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": "Times New Roman",
        "legend.numpoints": 1,
        "legend.columnspacing": 1,
        "legend.fontsize": FONT_SIZE - 2,
        "legend.frameon": False,
        "legend.labelspacing": 0.3,
        "lines.markeredgewidth": 1.0,
        "errorbar.capsize": 3.0,
        "xtick.top": True,
        "ytick.right": True,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
    }
)


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
    other papers from the month based on citation count.

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

    print(
        bib_code,
        results.json()["response"]["docs"][0]["pubdate"][0:7],
        "Citations:",
        results.json()["response"]["docs"][0]["citation_count"],
        results.json()["response"]["docs"][0]["author"][0],
    )
    citation_count = results.json()["response"]["docs"][0]["citation_count"]
    pub_date = results.json()["response"]["docs"][0]["pubdate"][0:7]
    author = results.json()["response"]["docs"][0]["author"][0].replace(" ", "")

    # Dividing the citation ditribution into chunks with fewer than 2000 hits, to not hit limit.
    citation_bounds = [0, 1, 2, 4, 10]

    citations = np.array([])

    for i, cite_bound in enumerate(citation_bounds):
        cite_start = cite_bound
        if i == len(citation_bounds) - 1:
            cite_end = 100000
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
        records.append({
            "Bibcode": bibcode,
            "Author": statistics.author,
            "PublicationDate": statistics.pub_date,
            "Rank": statistics.percentage,
            "Rank_upper": statistics.percentage_upper,
            "PaperNumber": statistics.total_papers_month
        })

    output = pd.DataFrame(records)
    output.to_csv(output_name + ".csv", index=False)


def MakeLibraryRanksPlot(library_code, output_name, token):
    """
    For a given ADS library, either read-in a pre-generated output dataframe if available,
    or generate a new one one using the get_library_ranks function, then generate a plot presenting
    the ranks for all paper in the library.

    Arguments
    ---------
    library_code: ADS library access code (identifiable though the library url
    https://ui.adsabs.harvard.edu/user/libraries/<library_code>)

    output_name: Name of output files
    """
    if not os.path.isfile(f"{output_name}.csv"):
        get_library_ranks(library_code, output_name, token)

    Output = pd.read_csv(f"{output_name}.csv")

    for i in range(len(Output["Rank"])):
        if "&" in Output["Bibcode"][i]:
            Output.loc[i, "Bibcode"] = (
                Output["Bibcode"][i].split("&")[0]
                + "\&"
                + Output["Bibcode"][i].split("&")[1]
            )

    # now finally making a plot of the output
    fig = plt.figure(figsize=(len(Output["Rank"]) * 0.25, 3))
    ax1 = plt.subplot(111)

    ax1.scatter(
        np.arange(len(Output["Rank"])),
        (Output["Rank"] + Output["Rank_upper"]) / 2,
        c="k",
    )
    Sel = ((Output["Rank"] + Output["Rank_upper"]) / 2) < 5
    ax1.scatter(
        np.arange(len(Output["Rank"]))[Sel],
        (Output["Rank"][Sel] + Output["Rank_upper"][Sel]) / 2,
        c="orange",
    )
    # ax1.scatter(np.arange(len(Output['Rank_upper'])), Output['Rank_upper'], c='k', marker='_')
    for jj in range(len(Output["Rank"])):
        ax1.plot([jj, jj], [Output["Rank"][jj], Output["Rank_upper"][jj]], c="k")
    ax1.axhline(
        np.median((Output["Rank"] + Output["Rank_upper"]) / 2), c="k", linestyle="--"
    )

    ax1.set_xlim([-0.5, len(Output["Rank"]) - 0.5])
    ax1.set_ylim([100, 0])
    ax1.set_ylabel("Rank of paper")
    ax1.set_xticks(np.arange(len(Output["Rank"])))
    ax1.set_xticklabels(np.array(Output["Bibcode"]), rotation=90)

    ax1.grid()

    ax2 = ax1.twiny()
    ax2.set_xlim([-0.5, len(Output["Rank"]) - 0.5])
    ax2.set_xticks(np.arange(len(Output["Rank"])))
    ax2.set_xticklabels(np.array(Output["Author"]), rotation=90)

    plt.savefig(output_name + ".pdf", bbox_inches="tight")
    plt.close()


def check_calls_available(token: str) -> None:
    """
    Runs a curl command with the given token to check how many calls are left.
    """
    url = "https://api.adsabs.harvard.edu/v1/search/query?q=star"
    command = f"curl -v -H 'Authorization: Bearer {token}' '{url}'"
    os.system(command)


if __name__ == "__main__":

    # personal access token
    # (user-specific, to be accessed online at https://ui.adsabs.harvard.edu/user/settings/token)
    TOKEN = ""

    # making the full output for a single ADS library.
    MakeLibraryRanksPlot(
        library_code="g3xxlnShS_iiymcLRdSUFg",
        output_name="Ranks_BellstedtFirstAuthor",
        token=TOKEN,
    )

    # extracting the statistics for just a single paper.
    # Statistics = get_paper_rank(bib_code = '2022MNRAS.517.6035T', token=TOKEN)
