# ADS-Library-Rank

# Creating the Sabine Plots for a Given ADS Library

Useful for ropes 🪢.

----------

## Set Up

### Setting up a PAT for NASA ADS

You can download your NASA ADS personal access token (PAT) [here](https://ui.adsabs.harvard.edu/user/settings/token). You’ll need to pass this token to the functions below.

You can check how many requests you have left and when your quota resets using the `check_calls_available` function from the `request_mod` module:

```python
from request_mod import check_calls_available

TOKEN = "abc123"
check_calls_available(TOKEN)

```
----------

### Getting the NASA ADS Library

The plot is generated by scraping a NASA ADS library. You'll need to provide the library ID from any public NASA ADS library. Navigate to the library URL and extract the ID from it.

For example, this library:  
[https://ui.adsabs.harvard.edu/user/libraries/GBL8GWARSHe6hTpBhODkGw](https://ui.adsabs.harvard.edu/user/libraries/GBL8GWARSHe6hTpBhODkGw)

Has the ID: `"GBL8GWARSHe6hTpBhODkGw"`

Once you have the token and the library ID, you can generate the plots.

----------

## Usage

### Scraping the Rank Data

You can generate a pandas DataFrame from the library ID and token:

```python
from rank_ads_library import get_library_ranks

TOKEN = "abc123"
LIBRARY_ID = "123abcxyz"
rank_data_df = get_library_ranks(LIBRARY_ID, TOKEN)

# Save the data if you'd like.
rank_data_df.to_csv("data.csv", index=False)

```
----------

### Creating the Rank Plot

You can generate the plot using the same DataFrame:

```python
from plot_mod import plot_ranks_plot

plot_ranks_plot(rank_data_df, "rank_plot.pdf")

```

If the data has already been saved, you can read it back in as a pandas DataFrame and pass it to `plot_ranks_plot`, or use the helper function `read_saved_data`:

```python
from plot_mod import read_saved_data

rank_df = read_saved_data("data.csv")
plot_ranks_plot(rank_df, "rank_plot.pdf")

```
----------

### One-Step "Do Everything"

Scraping, rank calculation, and plot generation can all be done in one step using the `do_all` function:

```python
from rank_ads_library import do_all

TOKEN = "abc123"
LIBRARY_ID = "567xyz"
FILE_NAME = "rank_data"
do_all(LIBRARY_ID, TOKEN, FILE_NAME)

```
This will scrape the website, save the data as `rank_data.csv`, and save the plot as `rank_data.pdf` — all in one step.

----------

## Running the Script Directly

You don't have to use the module functions in a separate script. You can simply run `rank_ads_library` directly, as long as `LIBRARY_ID`, `TOKEN`, and `FILE_NAME` are set in the `if __name__ == "__main__"` section.

The script will automatically run the `do_all` function.

```sh
python3 rank_ads_library.py` 
```
----------

## Getting Statistics for a Single Paper

You can also get the rank for a single paper by passing its bibcode and your token:

```python
from rank_ads_library import get_paper_rank

TOKEN = "123abc"
stats = get_paper_rank(bib_code="2022MNRAS.517.6035T", token=TOKEN)

```
