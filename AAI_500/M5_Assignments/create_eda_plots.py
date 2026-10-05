"""Create Assignment 5.1 EDA artifacts; no modeling or written answers."""
from pathlib import Path
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
deps = ROOT / '.tmp_heart_plot_deps'
if deps.exists():
    sys.path.insert(0, str(deps))
BASE = Path(__file__).resolve().parent
os.environ.setdefault('KAGGLEHUB_CACHE', str(BASE / '.kaggle_cache'))
os.environ.setdefault('MPLCONFIGDIR', str(BASE / '.matplotlib'))

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

LOAD_CODE = '''from pathlib import Path
import pandas as pd
import kagglehub
from kagglehub import KaggleDatasetAdapter

# The path is the filename inside the Kaggle dataset, not an empty string.
csv_path = Path("heart.csv")
if csv_path.exists():
    df = pd.read_csv(csv_path)
else:
    df = kagglehub.dataset_load(
        KaggleDatasetAdapter.PANDAS,
        "fedesoriano/heart-failure-prediction/versions/1",
        "heart.csv",
    )
    df.to_csv(csv_path, index=False)
print("Dataset shape:", df.shape)
display(df.head())
'''

CHECK_CODE = '''numeric_cols = ["Age", "RestingBP", "Cholesterol", "MaxHR", "Oldpeak"]
display(df.isna().sum().rename("Missing values").to_frame())
display(df[numeric_cols].describe())
display(df[numeric_cols].eq(0).sum().rename("Zero values").to_frame())
print("Duplicate rows:", df.duplicated().sum())
print("Columns:", df.columns.tolist())
# These four plots use no BP or cholesterol values; no rows are dropped or imputed.
'''

SETUP_CODE = '''import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from pathlib import Path

plot_dir = Path("plots")
plot_dir.mkdir(exist_ok=True)
plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})
colors = ["#3979A8", "#C35A45"]

def save_plot(fig, filename):
    fig.tight_layout()
    fig.savefig(plot_dir / filename, dpi=180, bbox_inches="tight")
    plt.show()
'''

AGE_CODE = '''# Common bin edges and within-class percentages allow a fair shape comparison.
fig, ax = plt.subplots(figsize=(9, 5))
bins = list(range(25, 86, 5))
for outcome, label, color in [(0, "No heart disease", colors[0]),
                              (1, "Heart disease", colors[1])]:
    ages = df.loc[df["HeartDisease"].eq(outcome), "Age"].dropna()
    ax.hist(ages, bins=bins, weights=[100 / len(ages)] * len(ages),
            histtype="step", linewidth=2.5, color=color,
            label=f"{label} (n={len(ages)})")
ax.set(title="Age distribution by heart disease status",
       xlabel="Age (years)", ylabel="Percentage within each outcome group")
ax.yaxis.set_major_formatter(PercentFormatter(100))
ax.legend(frameon=False)
ax.grid(axis="y", alpha=0.2)
save_plot(fig, "01_age_by_heart_disease.png")
'''

CHEST_CODE = '''# Mean of a binary 0/1 target equals the fraction with HeartDisease=1.
order = ["TA", "ATA", "NAP", "ASY"]
stats = df.groupby("ChestPainType")["HeartDisease"].agg(["mean", "count", "sum"]).reindex(order)
fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(order, stats["mean"] * 100, color=colors[1], width=0.6)
for bar, row in zip(bars, stats.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
            f"{row.mean:.1%}\\n{int(row.sum)}/{int(row.count)} patients",
            ha="center", va="bottom", fontsize=10)
ax.set_xticks(range(4), ["Typical angina\\n(TA)", "Atypical angina\\n(ATA)",
                       "Non-anginal pain\\n(NAP)", "Asymptomatic\\n(ASY)"])
ax.set(title="Observed heart disease frequency by chest pain type",
       xlabel="Chest pain category", ylabel="Patients with heart disease", ylim=(0, 108))
ax.yaxis.set_major_formatter(PercentFormatter(100))
ax.grid(axis="y", alpha=0.2)
ax.set_axisbelow(True)
save_plot(fig, "02_chest_pain_heart_disease_rate.png")
'''

HEAT_CODE = '''# Each cell estimates an observed P(HeartDisease=1 | two categorical features).
rates = df.pivot_table(index="ST_Slope", columns="ExerciseAngina",
                      values="HeartDisease", aggfunc="mean").reindex(index=["Up", "Flat", "Down"], columns=["N", "Y"])
counts = df.pivot_table(index="ST_Slope", columns="ExerciseAngina",
                       values="HeartDisease", aggfunc="count").reindex(index=rates.index, columns=rates.columns)
fig, ax = plt.subplots(figsize=(8, 5))
im = ax.imshow(rates.to_numpy() * 100, cmap="YlOrRd", vmin=0, vmax=100, aspect="auto")
for i in range(len(rates.index)):
    for j in range(len(rates.columns)):
        value, n = rates.iloc[i, j], counts.iloc[i, j]
        text = f"{value:.1%}\\nn={int(n)}" if pd.notna(value) else "No observations"
        ax.text(j, i, text, ha="center", va="center",
                color="white" if pd.notna(value) and value > 0.65 else "black", fontsize=12)
ax.set_xticks([0, 1], ["No", "Yes"])
ax.set_yticks([0, 1, 2], rates.index)
ax.set(title="Observed heart disease frequency by ST slope and exercise angina",
       xlabel="Exercise-induced angina", ylabel="ST slope")
fig.colorbar(im, ax=ax, format=PercentFormatter(100), label="Patients with heart disease")
save_plot(fig, "03_st_slope_exercise_angina.png")
'''

HR_CODE = '''fig, ax = plt.subplots(figsize=(9, 5))
groups = [df.loc[df["HeartDisease"].eq(k), "MaxHR"].dropna() for k in [0, 1]]
boxes = ax.boxplot(groups, tick_labels=["No heart disease", "Heart disease"],
                   patch_artist=True, widths=0.45,
                   medianprops={"color": "black", "linewidth": 2})
for box, color in zip(boxes["boxes"], colors):
    box.set_facecolor(color)
    box.set_alpha(0.65)
for pos, values in enumerate(groups, 1):
    ax.text(pos, 0.97, f"n={len(values)}", transform=ax.get_xaxis_transform(),
            ha="center", va="top")
ax.set(title="Maximum achieved heart rate by heart disease status",
       xlabel="Heart disease status", ylabel="Maximum achieved heart rate (beats/min)",
       ylim=(50, 220))
ax.grid(axis="y", alpha=0.2)
save_plot(fig, "04_maxhr_by_heart_disease.png")
'''

def main():
    os.chdir(BASE)
    if not Path('heart.csv').exists():
        import kagglehub
        from kagglehub import KaggleDatasetAdapter
        df = kagglehub.dataset_load(KaggleDatasetAdapter.PANDAS,
             'fedesoriano/heart-failure-prediction/versions/1', 'heart.csv')
        df.to_csv('heart.csv', index=False)
    else:
        df = pd.read_csv('heart.csv')
    required = {'Age', 'ChestPainType', 'HeartDisease', 'ST_Slope', 'ExerciseAngina', 'MaxHR'}
    assert required.issubset(df.columns), f'Missing columns: {required - set(df.columns)}'
    assert set(df.HeartDisease.unique()) <= {0, 1}
    report = {
        'source': 'https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction/versions/1',
        'shape': list(df.shape), 'columns': df.columns.tolist(),
        'missing': {k:int(v) for k,v in df.isna().sum().items()},
        'zeros_numeric': {k:int(v) for k,v in df[['Age','RestingBP','Cholesterol','MaxHR','Oldpeak']].eq(0).sum().items()},
        'duplicate_rows': int(df.duplicated().sum()),
    }
    Path('eda_data_checks.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    namespace = {'df': df, 'pd': pd}
    exec(SETUP_CODE.replace('plt.show()', 'plt.close(fig)'), namespace)
    plots = [AGE_CODE, CHEST_CODE, HEAT_CODE, HR_CODE]
    for code in plots:
        exec(code.replace('plt.show()', 'plt.close()'), namespace)
    template = json.loads(Path('AAI_500_M5_Assignment_Template.ipynb').read_text(encoding='utf-8'))
    cells = template['cells']
    def cell(kind, source):
        result = {'cell_type': kind, 'metadata': {}, 'source': source.splitlines(keepends=True)}
        if kind == 'code':
            result.update(execution_count=None, outputs=[])
        return result
    additions = [cell('markdown', '### EDA plots\nDataset source: [Kaggle, version 1](https://www.kaggle.com/datasets/fedesoriano/heart-failure-prediction/versions/1).\n\nInstall if needed: `%pip install "kagglehub[pandas-datasets]" matplotlib`\n\nThe plots show associations in this sample, not causal effects or calibrated clinical predictions. Counts are shown to help assess small groups. No rows are dropped or imputed for these plots. The written interpretation is left for you.\n'),
                 cell('code', LOAD_CODE), cell('code', CHECK_CODE), cell('code', SETUP_CODE)]
    prompts = [
        'Plot 1: Do the age distributions overlap? Compare their shapes; each outcome group is normalized separately.',
        'Plot 2: Compare within-category percentages rather than raw counts. Which categories have smaller samples?',
        'Plot 3: Compare angina states within each ST slope. These are empirical conditional frequencies, not Bayesian network query results.',
        'Plot 4: Compare medians, spreads, and overlap. A box spans the middle 50%; whiskers extend to observations within 1.5 times the interquartile range. Points beyond them are not automatically errors.',
    ]
    filenames = ['01_age_by_heart_disease.png', '02_chest_pain_heart_disease_rate.png', '03_st_slope_exercise_angina.png', '04_maxhr_by_heart_disease.png']
    for code, prompt, filename in zip(plots, prompts, filenames):
        additions.extend([cell('markdown', prompt), cell('code', code),
                          cell('markdown', f'![{prompt.split(":")[0]}](plots/{filename})')])
    additions.append(cell('markdown', '### Your interpretation\nWrite your own 3–5 sentence summary here after inspecting the plots.'))
    cells[2:3] = additions
    Path('AAI_500_M5_Assignment_EDA.ipynb').write_text(json.dumps(template, indent=1, ensure_ascii=False), encoding='utf-8')
    print('Created four PNG plots and AAI_500_M5_Assignment_EDA.ipynb')

if __name__ == '__main__':
    main()
