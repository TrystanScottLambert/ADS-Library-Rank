"""
Module to handle plotting
"""

import os
import shutil

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


def plot_ranks_plot(rank_data: pd.DataFrame, outfile: str) -> None:
    """
    For a given ADS library, either read-in a pre-generated rank_data dataframe if available,
    or generate a new one one using the get_library_ranks function, then generate a plot presenting
    the ranks for all paper in the library.

    Arguments
    ---------
    library_code: ADS library access code (identifiable though the library url
    https://ui.adsabs.harvard.edu/user/libraries/<library_code>)

    outfile: Name of rank_data plot file name to be saved.
    """

    # Only update rows where '&' exists in Bibcode
    mask = rank_data["Bibcode"].str.contains("&", na=False)
    rank_data.loc[mask, "Bibcode"] = rank_data.loc[mask, "Bibcode"].str.replace(
        "&", r"\&", n=1
    )

    fig = plt.figure(figsize=(len(rank_data["Rank"]) * 0.25, 3))
    ax1 = fig.add_subplot(111)

    ax1.scatter(
        np.arange(len(rank_data["Rank"])),
        (rank_data["Rank"] + rank_data["Rank_upper"]) / 2,
        c="k",
    )
    sel = ((rank_data["Rank"] + rank_data["Rank_upper"]) / 2) < 5
    ax1.scatter(
        np.arange(len(rank_data["Rank"]))[sel],
        (rank_data["Rank"][sel] + rank_data["Rank_upper"][sel]) / 2,
        c="orange",
    )

    for i in range(len(rank_data["Rank"])):
        ax1.plot([i, i], [rank_data["Rank"][i], rank_data["Rank_upper"][i]], c="k")
    ax1.axhline(
        np.median((rank_data["Rank"] + rank_data["Rank_upper"]) / 2),
        c="k",
        linestyle="--",
    )

    ax1.set_xlim([-0.5, len(rank_data["Rank"]) - 0.5])
    ax1.set_ylim([100, 0])
    ax1.set_ylabel("Rank of paper")
    ax1.set_xticks(np.arange(len(rank_data["Rank"])))
    ax1.set_xticklabels(np.array(rank_data["Bibcode"]), rotation=90)

    ax1.grid()

    ax2 = ax1.twiny()
    ax2.set_xlim([-0.5, len(rank_data["Rank"]) - 0.5])
    ax2.set_xticks(np.arange(len(rank_data["Rank"])))
    ax2.set_xticklabels(np.array(rank_data["Author"]), rotation=90)

    plt.savefig(outfile, bbox_inches="tight")
    plt.close()


def read_saved_data(file_name: str) -> pd.DataFrame:
    """
    Helper function to read in the saved rank data.
    """
    if not os.path.isfile(file_name):
        raise FileNotFoundError(f"No file named {file_name}")

    return pd.read_csv(file_name)
