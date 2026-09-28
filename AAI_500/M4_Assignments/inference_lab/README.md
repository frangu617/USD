# Statistical Inference Lab

A local Python app for the exercises in `AAI_500_M4_Assignment.ipynb`.
Open **Launch Inference Lab.bat** on Windows, or run from this folder:

```powershell
python -m pip install -r requirements.txt
python app.py
```

The browser opens automatically. Keep the terminal running; Ctrl+C stops the
server. Default address: http://127.0.0.1:8004. If occupied, a free port is used
and printed. Options: `--port 8005` and `--no-browser`.

## Exercise coverage

| Exercise | Analysis |
| --- | --- |
| 4.1 | 100,000 normal samples of size 100; quartile-average SD versus mean SE |
| 4.2 | Geometric likelihood for first success on trial 3 |
| 4.11 | 95% t intervals before and after replacing 4 with 24 |
| 4.14(a, b) | Students mean TV hours and Welch comparison between groups |
| 4.31 | Houses group descriptions and Welch price comparison |
| 5.6(a, b) | One-sided z and exact binomial tests; beta posterior probabilities |
| 5.8(a, b) | One-sample ideology t test against 4 and corresponding 95% CI |
| 5.10 | Welch comparison of weight by sheep survival |
| 5.23 | Exact starter-code simulation, observed/expected tables, chi-square test |

Students, Houses, and Sheep are not included in the workspace. Upload their
actual textbook data as CSV with a header row, then choose measurement and
group columns. No substitute datasets are used. Missing and nonnumeric
measurements are excluded and reported. Group comparisons use A minus B;
select the intended codes explicitly. No file is uploaded to an external service.

Charts have titles and axis labels and export as PNG or SVG. Tables export as
CSV; full results and settings export as JSON. The standalone HTML report can
be read in a browser or printed to PDF. The assignment notebook is unchanged.
Add relevant outputs and your own reasoning there before final HTML/PDF export.
This app is a calculation tool, not a finished written assignment.

Display values are rounded to two decimal places; small p-values display
`< 0.01`, rather than implying a probability of zero. Downloads preserve full
precision. The AI survey exactly follows the supplied legacy NumPy seed 2024
sequence, including all five columns. Simulation 4.1 has a configurable seed.

Review independence, representativeness, outliers, ordinal-score assumptions,
and chi-square expected counts before drawing conclusions. Group mean charts
do not display confidence intervals; use the interval columns in the tables.
The Houses exercise still requires a written report, and the Sheep exercise
requires you to specify the conceptual population. Two-sample calculations
use Welch's method and do not assume equal variances.

AI assistance: OpenAI Codex helped implement and check this app. Review and
understand the code and cite assistance as required by your course.

Run numerical checks with `python -m unittest discover -s tests`.
