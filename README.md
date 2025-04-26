# TCG Collector Image Scraper

A Python script to extract card image URLs from the TCG Collector website.

## Installation

1. Clone this repository or download the files
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script can be run with different options:

```bash
python tcg_scraper.py [OPTIONS]
```

### Available Options

- `--order`: Order of release dates (`oldToNew` or `newToOld`)
- `--per-page`: Number of cards per page (`30`, `60`, or `120`). Default: `60`
- `--search`: Search term for cards (use quotes for terms with spaces, e.g.: `--search "vstar universe"`)
- `--start-page`: First page to extract (default: 1)
- `--end-page`: Last page to extract (if not specified, all available pages will be extracted)
- `--output`: Output file for image URLs (if not specified, will be automatically generated from the search term and date/time)
- `--jp`: Enable to extract Japanese cards (uses the URL "/cards/jp")
- `--sort-by`: Sort by rarity (`rarityDesc` for descending or `rarityAsc` for ascending)
- `--force`: Ignore the initially detected page limit, but will automatically stop when there are no more images

### Examples

Example 1: Extract all cards in chronological order (from oldest to newest)
```bash
python tcg_scraper.py --order oldToNew
```

Example 2: Search for "Pikachu" with 120 cards per page, only pages 1 to 3
```bash
python tcg_scraper.py --search "Pikachu" --per-page 120 --start-page 1 --end-page 3
```

Example 3: Extract the first 5 pages of the most recent cards
```bash
python tcg_scraper.py --order newToOld --end-page 5
```

Example 4: Extract Japanese cards
```bash
python tcg_scraper.py --jp
```

Example 5: Extract cards in descending rarity order
```bash
python tcg_scraper.py --sort-by rarityDesc
```

Example 6: Search for "VSTAR Universe" cards in Japanese, ignore the detected page limit
```bash
python tcg_scraper.py --jp --search "vstar universe" --sort-by rarityDesc --end-page 20 --force
```

## Output

The script generates a text file containing one image URL per line, with each line ending with a semicolon (`;`).

If no filename is specified with `--output`, the script automatically generates a filename based on:
- The search term (converted to lowercase and replacing special characters with underscores)
- Whether the `--jp` option is used
- The current date and time (in YYYY-MM-DD_HH-MM-SS format)

Examples of generated filenames:
- `vstar_universe_jp_2023-08-01_14-30-45.txt` (for a "vstar universe" search with the `--jp` option)
- `pikachu_2023-08-01_14-30-45.txt` (for a "Pikachu" search)
- `all-cards_2023-08-01_14-30-45.txt` (if no search term is specified) 