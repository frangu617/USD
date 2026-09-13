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
- Compare the blue cumulative rain proportion with the orange chosen probability. Toggle the logarithmic day axis to change the graph scale.
- See the first 28 daily outcomes and a table at textbook milestones. All milestones belong to the same simulation.
- **Run history** keeps one result per completed run while the number of days stays the same. It shows the run number, days, rainy days, observed percentage, and chosen chance. Changing the chance preserves the log; changing to a different valid number of days clears it immediately. The log lasts until you close the app. Partial stopped runs are not added to the log.
- The **Current run milestones** tab shows the milestone table for the latest run. Day-count controls are disabled during a simulation; stop it first to change the range.
- **Run history statistics** shows the average, lowest, and highest rainy-day count and observed rain percentage across completed runs in the log. It updates after each completed run and resets with the log when the number of days changes. Changing the chosen chance keeps earlier runs in these statistics. Percentages are calculated from the original counts, not rounded table values; averages may include fractional days.
- **Stop** keeps the partial results. Click **Simulate** to start a new run with your current inputs.

Start with 20% and 7 days, then try 1,000,000 days. Small samples can differ considerably from 20%; larger samples tend to approach it, but the error does not decrease at every step. Results are random and will differ from the book.

“Range” here means the number of simulated days. Each day uses a uniform random value in [0, 1); a value below the chosen probability means rain. At 20%, this has the same rain probability as calling digits 0 and 1 rain among the ten equally likely digits 0–9, while supporting probabilities such as 23.5%.

The model assumes independent days with a constant probability. It demonstrates long-run (frequentist) probability; it does not estimate real weather probabilities or subjective beliefs.
