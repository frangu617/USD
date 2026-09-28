"""Statistical calculations for Assignment 4.1; independent of the UI."""
import io

import numpy as np
import pandas as pd
from scipy import stats


def mean_interval(values):
    values = np.asarray(values, dtype=float)
    if len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("Provide at least two finite observations per group.")
    sd = values.std(ddof=1)
    se = sd / np.sqrt(len(values))
    margin = stats.t.ppf(.975, len(values) - 1) * se
    return {"n": len(values), "Mean": values.mean(), "SD": sd,
            "SE": se, "CI lower": values.mean() - margin,
            "CI upper": values.mean() + margin}


def compare(a, b):
    left, right = mean_interval(a), mean_interval(b)
    va, vb = left["SE"] ** 2, right["SE"] ** 2
    if va + vb == 0:
        raise ValueError("A t comparison needs nonzero sampling variability.")
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    se = np.sqrt(va + vb)
    difference = left["Mean"] - right["Mean"]
    t = difference / se
    margin = stats.t.ppf(.975, df) * se
    return {"Difference (A - B)": difference, "SE": se, "df": df,
            "t": t, "p-value (two-sided)": 2 * stats.t.sf(abs(t), df),
            "CI lower": difference - margin, "CI upper": difference + margin}


def analyze(request):
    mode = request.get("mode", "precision")
    rows, charts, notes, tables = [], [], [], []

    def chart(title, x_label, y_label, x, series):
        charts.append({"title": title, "x_label": x_label, "y_label": y_label,
                       "x": list(x), "series": series})

    if mode == "precision":
        seed = int(request.get("seed", 42))
        rng = np.random.default_rng(seed)
        # Batch the required 10 million draws to bound memory consumption.
        estimates, means = [], []
        for _ in range(100):
            sample = rng.normal(size=(1000, 100))
            estimates.extend(np.quantile(sample, [.25, .75], axis=1).mean(axis=0))
            means.extend(sample.mean(axis=1))
        empirical = np.std(estimates, ddof=1)
        rows = [{"Estimator": "Average of quartiles", "SD": empirical},
                {"Estimator": "Sample mean (simulation)", "SD": np.std(means, ddof=1)},
                {"Estimator": "Sample mean (theory)", "SD": .1},
                {"Estimator": "Quartile / theoretical mean SE", "SD": empirical / .1}]
        edges = np.linspace(min(min(estimates), min(means)), max(max(estimates), max(means)), 55)
        chart("Sampling distributions: 100,000 samples of n = 100", "Estimated mean", "Count",
              (edges[:-1] + edges[1:]) / 2,
              [{"name": name, "y": np.histogram(values, edges)[0].tolist()}
               for name, values in [("Average of quartiles", estimates), ("Sample mean", means)]])
        notes = [f"N(0, 1) independent draws; seed {seed}; NumPy linear sample quartiles.",
                 "Compare estimator spread, not just its center. Larger SD means less precision under this model."]
    elif mode == "likelihood":
        p = np.linspace(0, 1, 301)
        likelihood = (1 - p) ** 2 * p
        rows = [{"First success trial": 3, "MLE p": 1 / 3, "Maximum likelihood": 4 / 27}]
        chart("Geometric likelihood: first success on trial 3", "Success probability p", "Likelihood L(p)",
              p, [{"name": "(1 - p)^2 p", "y": likelihood.tolist()}])
        notes = ["L(p) = (1 - p)^2 p for 0 <= p <= 1. Trials are independent with constant success probability.",
                 "A likelihood is a function of the parameter for the observed data, not a probability density over p."]
    elif mode == "outlier":
        original = [0, 0, 1, 1, 1, 2, 2, 3, 3, 4]
        altered = original[:-1] + [24]
        rows = [{"Data": name, **mean_interval(v)} for name, v in [("Original", original), ("4 replaced by 24", altered)]]
        chart("Daily TV observations: effect of recording error", "Subject", "Daily TV hours", range(1, 11),
              [{"name": "Original", "y": original}, {"name": "With error", "y": altered}])
        notes = ["Two-sided 95% one-sample t intervals, df = 9. Compare both interval center and width.",
                 "Independence and representative sampling matter. With n = 10, skew and outliers can substantially weaken t-interval validity."]
    elif mode == "polls":
        grid = np.linspace(.25, .8, 301)
        series = []
        for state, k, n in [("A", 59, 100), ("B", 525, 1000)]:
            z = (k / n - .5) / np.sqrt(.25 / n)
            a, b = 50 + k, 50 + n - k
            rows.append({"State": state, "Sample proportion": k / n, "z": z,
                         "One-sided z p-value": stats.norm.sf(z),
                         "Exact binomial p-value": stats.binomtest(k, n, .5, alternative="greater").pvalue,
                         "Posterior alpha": a, "Posterior beta": b,
                         "Posterior P(p < 0.50)": stats.beta.cdf(.5, a, b)})
            series.append({"name": f"State {state} posterior", "y": stats.beta.pdf(grid, a, b).tolist()})
        series.append({"name": "Beta(50, 50) prior", "y": stats.beta.pdf(grid, 50, 50).tolist()})
        chart("Prior and posterior support for vote proportion", "Population proportion", "Density", grid, series)
        notes = ["H0: p = 0.50; H1: p > 0.50. The z test uses the null standard error; the exact binomial test is shown separately.",
                 "Posterior Beta(50 + successes, 50 + failures). A posterior tail probability and a frequentist p-value have different meanings.",
                 "Assume independent random binomial samples and representative responses within each state."]
    elif mode == "ai":
        # RandomState reproduces the assignment's np.random.seed(2024) sequence.
        rng = np.random.RandomState(2024)
        frame = pd.DataFrame({
            "sentiment": rng.choice(["Positive", "Neutral", "Negative"], 300, p=[.44, .33, .23]),
            "gender": rng.choice(["Male", "Female", "Other"], 300, p=[.49, .48, .03]),
            "age": rng.randint(18, 75, 300),
            "ai_usage_frequency": rng.choice(["Daily", "Weekly", "Rarely", "Never"], 300),
            "trust_in_ai": rng.randint(1, 6, 300)})
        observed = pd.crosstab(frame.sentiment, frame.gender)
        chi, p, df, expected = stats.chi2_contingency(observed, correction=False)
        rows = [{"Chi-square": chi, "df": df, "p-value": p,
                 "Minimum expected count": expected.min(), "Cells expected < 5": int((expected < 5).sum())}]
        for label, table in [("Observed counts", observed), ("Expected counts under independence", pd.DataFrame(expected, index=observed.index, columns=observed.columns))]:
            tables.append({"title": label, "rows": table.rename_axis("Sentiment").reset_index().to_dict("records")})
        chart("Sentiment counts by gender", "Sentiment", "Respondents", observed.index,
              [{"name": c, "y": observed[c].tolist()} for c in observed])
        notes = ["The starter generator samples sentiment and gender independently. Sample differences are not evidence of a causal effect.",
                 "Check expected counts before interpreting the chi-square approximation; sparse cells weaken its accuracy. Do not merge identities just to improve counts.",
                 "Synthetic data illustrate the method and do not establish real-world public attitudes."]
        tables.append({"title": "Generated survey data", "rows": frame.to_dict("records")})
    elif mode in {"students_mean", "students_compare", "houses", "ideology", "sheep"}:
        raw = request.get("csv", "").strip()
        if not raw:
            raise ValueError("Upload or paste the actual textbook CSV data first.")
        frame = pd.read_csv(io.StringIO(raw))
        value = request.get("value", "")
        if value not in frame:
            raise ValueError("Choose the numeric measurement column.")
        values = pd.to_numeric(frame[value], errors="coerce")
        valid = values.notna() & np.isfinite(values)
        notes = ["Use the actual textbook file. No example data have been substituted.",
                 "95% t intervals assume independent, representative observations. Small groups require particular care with outliers and non-normality."]
        if mode in {"students_mean", "ideology"}:
            a = values[valid].to_numpy()
            result = mean_interval(a)
            if mode == "ideology":
                if result["SE"] == 0:
                    raise ValueError("The t test requires nonzero sample variability.")
                t = (result["Mean"] - 4) / result["SE"]
                result.update({"Null mean": 4, "t": t, "df": len(a) - 1,
                               "Two-sided p-value": 2 * stats.t.sf(abs(t), len(a) - 1)})
                notes.append("H0: mean = 4; H1: mean != 4; alpha = 0.05. Compare the test with whether 4 is inside the 95% CI. Treating ordinal ideology scores as quantitative is an additional assumption.")
            rows = [result]
            counts, edges = np.histogram(a, bins="auto")
            chart(f"Distribution of {value}", value, "Count", (edges[:-1] + edges[1:]) / 2,
                  [{"name": value, "y": counts.tolist()}])
        else:
            group = request.get("group", "")
            if group not in frame:
                raise ValueError("Choose the group column.")
            valid &= frame[group].notna()
            labels = frame[group].astype(str).str.strip()
            ga, gb = str(request.get("a", "")).strip(), str(request.get("b", "")).strip()
            if ga == gb:
                raise ValueError("Choose two different group values.")
            a = values[valid & (labels == ga)].to_numpy()
            b = values[valid & (labels == gb)].to_numpy()
            rows = [{"Group": ga, **mean_interval(a)}, {"Group": gb, **mean_interval(b)},
                    {"Group": f"{ga} minus {gb}", **compare(a, b)}]
            chosen = valid & labels.isin([ga, gb])
            notes.append(f"Included {int(chosen.sum())} rows; excluded {int((~chosen).sum())} with missing/non-numeric values or unselected groups.")
            chart(f"Group means for {value}", f"Group ({group})", f"Mean {value}", [ga, gb],
                  [{"name": "Group mean", "y": [a.mean(), b.mean()]}])
            notes.append("Welch's independent two-sample t procedure; equal variances are not assumed. The difference is group A minus group B; the null difference is zero.")
            if mode == "houses":
                notes.append("Select new = 1 as A and older = 0 as B. Prices are in thousands of dollars. Discuss skew, outliers, and confounding; observational differences do not prove a new-house effect.")
            if mode == "sheep":
                notes.append("Select survived = 1 as A and did not survive = 0 as B. Weight is in kg. Define a population comparable to the observed sheep and discuss selection and dependence; this is not a causal survival test.")
        notes.append(f"Total source rows: {len(frame)}; finite measurement rows with required group present: {int(valid.sum())}.")
    else:
        raise ValueError("Unknown exercise.")
    return {"rows": rows, "charts": charts, "notes": notes, "tables": tables}
