"""
Script to query an ADS library and construct the Sabine plots.
"""

import os
from urllib.parse import urlencode

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


def GetPaperRank(bibCode, token):
    """
    function that identifies the publication date and citation number for a single paper
    based on a bibCode, and then extracts the distribution of citations for all refereed astronomy
    papers published in the same month. A perentage rank is then computed, rnking the paper against
    other papers from the month based on citation count.

    Arguments
    ----------

    bibcode: ADS bibcode of the targeted paper.

    token: ADS API token (user-specific, to be accessed online at
    https://ui.adsabs.harvard.edu/user/settings/token)

    Outputs
    -------

    NumberGreaterCitations: Number of refereed publications with greater citations than the target
                                                paper

    NumberTotalMonthPapers: Total number of refereed astro publications in the same month as target
                                                paper

    Percentage: Rank when compared against only papers with more citations

    Percentage_upper: Rank when compared against publications with more or equal number of
                                        citations.

    Author: Name of lead-author for target paper.

    PubDate: publication date of target paper.

    """
    encoded_query = urlencode(
        {
            "q": "bibcode:" + str(bibCode),
            "fl": "title, bibcode, citation_count, property, pubdate, author",
            "rows": 1000,
        }
    )
    results = requests.get(
        "https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query),
        headers={"Authorization": "Bearer " + token},
    )
    print(
        bibCode,
        results.json()["response"]["docs"][0]["pubdate"][0:7],
        "Citations:",
        results.json()["response"]["docs"][0]["citation_count"],
        results.json()["response"]["docs"][0]["author"][0],
    )
    CitationCount = results.json()["response"]["docs"][0]["citation_count"]
    PubDate = results.json()["response"]["docs"][0]["pubdate"][0:7]
    Author = results.json()["response"]["docs"][0]["author"][0].replace(" ", "")

    # dividing the citation ditribution into chunks with fewer than 2000 hits, to not hit limit.
    Citationbounds = [
        0,
        1,
        2,
        4,
        10,
    ]

    citations = np.array([])

    for i, citeBound in enumerate(Citationbounds):
        CiteStart = citeBound
        if i == len(Citationbounds) - 1:
            CiteEnd = 100000
        else:
            CiteEnd = Citationbounds[i + 1] - 1

        encoded_query = urlencode(
            {
                "q": "pubdate:["
                + PubDate
                + " TO "
                + PubDate
                + "] AND collection:astronomy AND property:refereed AND citation_count:["
                + str(CiteStart)
                + " TO "
                + str(CiteEnd)
                + "]",
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
            print(f"WARNING: number of results in citation range {CiteStart} to {CiteEnd} reached query limit")
            print("Need to add value to citationBounds ")

        # now extracting the histogram of citations
        for doc in results.json()["response"]["docs"]:
            citations = np.append(citations, doc["citation_count"])

    # now identifying the fraction with citations greater than or equal to the reference
    NumberGreaterCitations = len(citations[citations >= CitationCount])
    NumberTotalMonthPapers = len(citations)
    Percentage = (NumberGreaterCitations / NumberTotalMonthPapers) * 100
    Percentage_upper = (
        len(citations[citations > CitationCount]) / NumberTotalMonthPapers
    ) * 100
    print("Total astro refereed papers this month:", NumberTotalMonthPapers)
    print("Percentage rank of paper:", Percentage)
    print("############################################################")

    return [
        NumberGreaterCitations,
        NumberTotalMonthPapers,
        Percentage,
        Percentage_upper,
        Author,
        PubDate,
    ]


def GetLibraryRanks(LibraryCode, OutputName, token, rows=1000):
    """
    For a given ADS library, identify the relevant bibcodes,
    and compile the rank statistics, saving an output dataframe.

    Arguments
    ---------
    LibraryCode: ADS library access code

    OutputName: Name of output files

    rows: maximum number of papers to extract from library
                    (default 1000)


    """
    # now extracting my first-author library

    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/biblib/libraries/{LibraryCode}?rows={rows}",
        headers={"Authorization": "Bearer " + token},
        timeout=REQUEST_GET_TIMEOUT,
    )
    Bibcodes = np.array([])
    for ii in range(len(results.json()["solr"]["response"]["docs"])):
        Bibcodes = np.append(
            Bibcodes, results.json()["solr"]["response"]["docs"][ii]["bibcode"]
        )

    print(Bibcodes)

    ranks = np.array([])
    ranks_upper = np.array([])
    paper_number = np.array([])
    Authors = np.array([])
    pubDate = np.array([])
    for bibcode in Bibcodes:
        Statistics = GetPaperRank(bibCode=bibcode, token=token)
        ranks = np.append(ranks, Statistics[2])
        ranks_upper = np.append(ranks_upper, Statistics[3])
        paper_number = np.append(paper_number, Statistics[1])
        Authors = np.append(Authors, Statistics[4])
        pubDate = np.append(pubDate, Statistics[5])

    # now saving the outputs

    Output = pd.DataFrame(
        {
            "Bibcode": Bibcodes,
            "Author": Authors,
            "PublicationDate": pubDate,
            "Rank": ranks,
            "Rank_upper": ranks_upper,
            "PaperNumber": paper_number,
        }
    )
    Output.to_csv(OutputName + ".csv", index=False)


def MakeLibraryRanksPlot(LibraryCode, OutputName, token):
    """
    For a given ADS library, either read-in a pre-generated output dataframe if available,
    or generate a new one one using the GetLibraryRanks function, then generate a plot presenting
    the ranks for all paper in the library.

    Arguments
    ---------
    LibraryCode: ADS library access code (identifiable though the library url
    https://ui.adsabs.harvard.edu/user/libraries/<LibraryCode>)

    OutputName: Name of output files
    """
    if not os.path.isfile(f"{OutputName}.csv"):
        GetLibraryRanks(LibraryCode, OutputName, token)

    Output = pd.read_csv(f"{OutputName}.csv")

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

    plt.savefig(OutputName + ".pdf", bbox_inches="tight")
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
        LibraryCode="g3xxlnShS_iiymcLRdSUFg",
        OutputName="Ranks_BellstedtFirstAuthor",
        token=TOKEN,
    )

    # extracting the statistics for just a single paper.
    # Statistics = GetPaperRank(bibCode = '2022MNRAS.517.6035T', token=TOKEN)
