# Rain probability lab

Double-click **Rain Probability Lab.lnk** in the `code` folder to open the app without a terminal window. Windows may display this shortcut as **Rain Probability Lab**. The shortcut uses the current Python installation and folder location; recreate it if you move the app.

Alternatively, run from the assignment folder:

```powershell
python code/rain_probability.py
```

The app uses Python's standard library (Tkinter); no pip packages are needed.

- Set **Chance of rain (%)** from 0 to 100.
- Set **Range: number of days** from 1 to 1,000,000, or select a preset.
- Click **Simulate**. Each run uses fresh randomness. Enter an optional integer seed to reproduce a run.
- Set **Number of runs** (1 to 100,000), or use the **1, 10, 100, 1000 runs** buttons, then click **Simulate** to run a batch. Day presets include **1** and **10** days.
- The progress bar tracks the entire batch. Estimated time remaining appears after a short measurement period and updates using elapsed time and simulated days; it is approximate. **Stop** cancels remaining work and keeps completed runs in the history and statistics. The current partial run stays on the graph and milestone table but is excluded from history statistics.
- Inputs are locked during a batch. The graph and milestone table show the current/latest run. A supplied seed reproduces the batch, using that seed for the first run and increasing it by one for each subsequent run.
- Compare the blue cumulative rain proportion with the orange chosen probability. Toggle the logarithmic day axis to change the graph scale.
- See the first 28 daily outcomes and a table at textbook milestones. All milestones belong to the same simulation.
- **Run history** keeps one result per completed run while the number of days stays the same. It shows the run number, days, rainy days, observed percentage, and chosen chance. Changing the chance preserves the log; changing to a different valid number of days clears it immediately. The log lasts until you close the app. Partial stopped runs are not added to the log.
- The **Current run milestones** tab shows the milestone table for the latest run. Day-count controls are disabled during a simulation; stop it first to change the range.
- **Run history statistics** shows the average, lowest, and highest rainy-day count and observed rain percentage across completed runs in the log. It updates after each completed run and resets with the log when the number of days changes. Changing the chosen chance keeps earlier runs in these statistics. Percentages are calculated from the original counts, not rounded table values; averages may include fractional days.
- **Stop** keeps the partial results. Click **Simulate** to start a new run with your current inputs.

Start with 20% and 7 days, then try 1,000,000 days. Small samples can differ considerably from 20%; larger samples tend to approach it, but the error does not decrease at every step. Results are random and will differ from the book.

“Range” here means the number of simulated days. Each day uses a uniform random value in [0, 1); a value below the chosen probability means rain. At 20%, this has the same rain probability as calling digits 0 and 1 rain among the ten equally likely digits 0–9, while supporting probabilities such as 23.5%.

The model assumes independent days with a constant probability. It demonstrates long-run (frequentist) probability; it does not estimate real weather probabilities or subjective beliefs.


## Gamma scale app (Problem 2.21)

From the assignment folder, run:

```powershell
python code/gamma_scale_problem_2_21.py
```

Requires NumPy and Matplotlib (`python -m pip install numpy matplotlib`).
The app plots shape k = 3 with scales 0.5, 1, 2, 3, 4, and 5 on matching axes.
Checkboxes show or hide individual curves; the Matplotlib toolbar supports zooming
and saving the current view. A table lists each mean, standard deviation, and mode.
Each run saves `gamma_scale_2_21.png` and `gamma_scale_2_21.svg` in the assignment
folder. Use `--no-show` to export without opening a window, or `--output-dir PATH`
to choose another destination.

Increasing scale stretches the distribution to the right and lowers its peak.
Mean, mode, and standard deviation increase proportionally to scale; variance
increases with scale squared. Total probability stays 1, and skewness stays fixed
because k is unchanged.


## Heights and weights (Problem 2.27)

From the assignment folder: `python code/height_weight_problem_2_27.py`.
Requires NumPy and Matplotlib. Simulates 1,000 pairs using a reproducible seed
(default 27), plots height against weight, and compares sample statistics with
model values. Resimulate increments the seed; Save plot + CSV exports the current
sample. Initial PNG, SVG, and CSV files are saved automatically to the assignment
folder as `height_weight_2_27.*`. Options: `--seed 27`, `--no-show`, and
`--output-dir PATH`.

The model generates X from N(162, 7^2) and Y = 3 + 0.40X + independent N(0, 8^2)
noise. Overall weight SD is sqrt(0.40^2 * 7^2 + 8^2), about 8.476 kg; the
population correlation is about 0.3304. Sample SDs use n - 1.
