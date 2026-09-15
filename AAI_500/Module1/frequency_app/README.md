# Frequency Lab

A local Python app for frequency distributions, histograms, and descriptive statistics. No third-party packages required; Python 3.9+ and a modern browser are sufficient.

From the course folder, run:

```bash
python3 frequency_app/app.py
```

The app opens at http://127.0.0.1:8000. If the browser does not open, visit that address manually. Stop with Ctrl+C. Use `--port 8001` if port 8000 is occupied, or `--no-browser` to disable automatic browser opening.

Enter numbers, paste labeled data such as `Nation CO2 Albania 2.0 Australia 15.4`, or import a UTF-8 CSV/TSV and select a column. Labeled data can be on one line or multiple lines, with multiword names. Only standalone numeric tokens become observations, so the digit in `CO2` is ignored. Expand “Extracted values used in calculations” to review the data. For multiple numeric columns or labels containing standalone numbers, use CSV import. Adjust the header checkbox for files without headers. Blank and nonnumeric CSV cells are excluded with visible counts. Manual input rejects invalid numbers. Use decimal points and no thousands separators.

Leave bins empty for Sturges' rule, or choose 1–100 equal-width bins. Bin widths round up to clean increments such as 0.5, 1, 2, 2.5, or 5, with aligned boundaries that may extend beyond the data. Frequency axis ticks are whole numbers. The last interval includes its upper boundary. Constant data uses one bin. Statistics are computed from original observations, not grouped midpoint estimates. Both sample (n−1) and population (n) standard deviation are shown; sample deviation is unavailable for a single observation. Download the frequency table as CSV.

The frequency curve is a frequency polygon connecting histogram bin midpoints, using the same axes as the histogram. It reflects the selected bins and does not assume normally distributed data. A single bin appears as one point.

The five-number summary shows minimum, Q1, median, Q3, and maximum. Quartiles use the median of each half of the sorted data, excluding the overall median for odd sample sizes. A single observation supplies all five numbers. The box plot spans Q1–Q3 with a median line; whiskers reach the outermost observations within 1.5 × IQR of the quartiles. Outliers are shown as circles and listed below the plot. Repeated outliers share a marker, with multiplicity shown on hover. These summaries use the original observations and do not depend on the bins.

Each chart has **Save SVG (compact)** and **Save PNG** buttons. SVG preserves sharp lines and text at any scale and is usually compact for these charts. PNG exports at the native chart size (960 × 360, or 960 × 240 for the box plot) to keep file sizes modest. Both formats include a white background and axis labels, and export entirely in your browser. The download status shows the file size.

Data is processed by the local Python server and is not saved. The app binds only to 127.0.0.1. CSV uploads are limited to 4.5 MB.

Run checks with:

```bash
python3 -m unittest discover -s frequency_app -p 'test_*.py'
```

## Pasted tables

Paste a table such as `income education race 16 10 B 18 7 B`, then click **Analyze data**. The app detects the columns, defaults to the first numeric column, and shows column and group selectors plus a ten-row preview. Choose income or education and optionally filter by race. All statistics, plots, and image exports reflect that selection. Counts show selected rows and excluded missing values.

Use single-word headers, whitespace/comma/semicolon separators, and two numeric columns at the start of the first row for automatic detection. Tables can be flattened to one line or spread across lines. HTML space entities such as `&#x20;` are decoded. Use `NA` for missing cells; incomplete rows and mixed invalid numeric columns are rejected. For other layouts, use CSV import. The earlier labeled CO2 format and plain number lists still work.

## Comparing groups

After pasting a table, click **Table data**. Choose income or education under **Analyze column**. The grouping column defaults to race when present. The single-group dropdown still filters the ordinary analysis. For comparison, check 2–12 groups and click **Compare selected groups**; these checkboxes determine the comparison independently of the single-group dropdown.

The comparison includes a statistics table and side-by-side histograms, frequency curves, and box plots. Bins are computed from the selected groups together. Histograms and curves use within-group percentages and a shared vertical scale; box plots share a horizontal scale. Missing observations are counted per group. Ordinary plots below summarize the selected groups combined. Each comparison chart can be exported as SVG or PNG.
