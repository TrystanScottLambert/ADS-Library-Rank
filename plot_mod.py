"""
Module to handle plotting
"""

import shutil
import os

import pandas as pd
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

FONT_SIZE = 12


def is_latex_installed():
    """Checks if system has latex installed and uses it in the plots if it does."""
    return shutil.which("latex") is not None


latex_avail = is_latex_installed()
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
        "text.usetex": latex_avail,
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


def plot_ranks_plot(infile: str, outfile: str) -> None:
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
    if not os.path.isfile(infile):
        raise FileNotFoundError(f"No file named {infile}")

    output = pd.read_csv(infile)

    # Only update rows where '&' exists in Bibcode
    mask = output["Bibcode"].str.contains("&", na=False)
    output.loc[mask, "Bibcode"] = output.loc[mask, "Bibcode"].str.replace(
        "&", r"\&", n=1
    )

    fig = plt.figure(figsize=(len(output["Rank"]) * 0.25, 3))
    ax1 = fig.add_subplot(111)

    ax1.scatter(
        np.arange(len(output["Rank"])),
        (output["Rank"] + output["Rank_upper"]) / 2,
        c="k",
    )
    sel = ((output["Rank"] + output["Rank_upper"]) / 2) < 5
    ax1.scatter(
        np.arange(len(output["Rank"]))[sel],
        (output["Rank"][sel] + output["Rank_upper"][sel]) / 2,
        c="orange",
    )

    for i in range(len(output["Rank"])):
        ax1.plot([i, i], [output["Rank"][i], output["Rank_upper"][i]], c="k")
    ax1.axhline(
        np.median((output["Rank"] + output["Rank_upper"]) / 2), c="k", linestyle="--"
    )

    ax1.set_xlim([-0.5, len(output["Rank"]) - 0.5])
    ax1.set_ylim([100, 0])
    ax1.set_ylabel("Rank of paper")
    ax1.set_xticks(np.arange(len(output["Rank"])))
    ax1.set_xticklabels(np.array(output["Bibcode"]), rotation=90)

    ax1.grid()

    ax2 = ax1.twiny()
    ax2.set_xlim([-0.5, len(output["Rank"]) - 0.5])
    ax2.set_xticks(np.arange(len(output["Rank"])))
    ax2.set_xticklabels(np.array(output["Author"]), rotation=90)

    plt.savefig(outfile, bbox_inches="tight")
    plt.close()
