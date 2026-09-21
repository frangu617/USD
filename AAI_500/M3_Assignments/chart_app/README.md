# Sampling Chart Lab

A Python app with a browser interface. Enter parameters, generate charts, and
download PNG/SVG images to insert into the assignment yourself. It does not read
or modify the assignment notebook and does not write assignment answers.

On your Mac, double-click **Launch Chart Lab.command** in Finder. The first run
creates a local Python environment and installs the three dependencies; later
runs reuse it.

From the USD workspace folder:

```bash
python3 -m pip install -r AAI_500/M3_Assignments/chart_app/requirements.txt
python3 AAI_500/M3_Assignments/chart_app/app.py
```

The app opens http://127.0.0.1:8003. Keep the terminal running; press Ctrl+C to stop.
If that port is occupied, the app automatically uses a free port and prints/opens
the correct address. Use `--port 8004` to request another port, or `--no-browser`
to open the printed address manually.
On Windows, use `python` instead of `python3` if needed.

1. Select an exercise preset.
2. Edit the inputs. Probabilities use decimals, e.g. 0.50 for 50%.
3. Click **Generate chart**. A fixed seed reproduces results; change it for new samples.
4. Download PNG or SVG. The CSV download contains the exact plotted observations
   (or density/probability coordinates); settings can be saved separately.
5. Drag the PNG into a Markdown cell in VS Code, or save it beside the notebook
   and reference it with `![My chart](my_chart.png)` in a Markdown cell.
   Write your own interpretation alongside it.

## Presets

| Exercise | Controls |
| --- | --- |
| 3.2 / 3.3 | Sample size, population probability, observed proportion, repetitions |
| 3.5(a) | Gamma population mean/SD, sample sizes, repetitions; presets for SD 5 and 8 |
| 3.5(b) | Gamma mean/SD and shaded interval |
| 3.8 | Probability of heads and flip counts; exact probability bars |
| 3.13 | Uniform bounds and sample sizes |
| 3.21 | Normal mean/SD; individual data and repeated sample means |
| AI | Both lognormal means/SDs, population size, bootstrap sample sizes and repetitions |

Charts include titles and axis labels. Statistical readouts show extra decimal
places so small SEs remain visible. Round as required when writing your answers.
Normal reference curves illustrate an approximation; small-sample distributions
need not match them. Simulations assume independent draws. Bootstrap sampling
uses replacement. The requested AI lognormal model can exceed 1; the app reports
this rather than silently clipping and changing its mean and SD.

For pasting raw observations or importing CSV columns to make ordinary
histograms/box plots, reuse `AAI_500/Module1/frequency_app/app.py`. For the old
rain, fixed-shape gamma, and height/weight apps, keep using the existing scripts
in `AAI_500/M2_Assignments/code/`. This app adds the repeated-sample and bootstrap
charts those apps do not provide.
