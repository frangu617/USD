"""Plot Gamma(shape=3) for six scales. Run with --no-show to export only."""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import CheckButtons


SHAPE = 3
SCALES = (0.5, 1, 2, 3, 4, 5)
EXPLANATION = (
    "Increasing the scale stretches the distribution horizontally to the right.\n"
    "The mean (3θ), mode (2θ), and standard deviation (√3 θ) increase in direct\n"
    "proportion to θ; variance (3θ²) increases quadratically. The peak becomes\n"
    "lower, while total area stays 1. Right skewness remains 2/√3 ≈ 1.155\n"
    "because the shape parameter stays fixed. This is a stretch, not a simple shift."
)


def gamma_pdf(x, scale):
    """Gamma density for k=3 and scale θ: x² exp(-x/θ)/(2θ³)."""
    x = np.asarray(x, dtype=float)
    positive = np.maximum(x, 0)
    return (positive / scale) ** 2 * np.exp(-positive / scale) / (2 * scale)


def create_plot():
    fig, ax = plt.subplots(figsize=(12, 8))
    fig.subplots_adjust(left=0.08, right=0.75, top=0.88, bottom=0.32)
    x = np.linspace(0, 60, 6001)
    lines = []
    for scale in SCALES:
        line, = ax.plot(x, gamma_pdf(x, scale), linewidth=2,
                        label=f"θ = {scale:g}")
        lines.append(line)
    ax.set(title="Gamma probability densities: fixed shape k = 3",
           xlabel="x", ylabel="Probability density f(x)", xlim=(0, 60), ylim=(0, 0.58))
    ax.grid(alpha=0.25)
    ax.legend(title="Scale θ")
    fig.suptitle("Effect of the gamma scale parameter", fontsize=18)

    table_ax = fig.add_axes((0.78, 0.36, 0.21, 0.27))
    table_ax.axis("off")
    rows = [[f"{s:g}", f"{3*s:g}", f"{np.sqrt(3)*s:.3f}", f"{2*s:g}"]
            for s in SCALES]
    table = table_ax.table(cellText=rows, colLabels=["Scale", "Mean", "SD", "Mode"],
                           cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    controls_ax = fig.add_axes((0.80, 0.66, 0.17, 0.22))
    controls_ax.set_title("Show / hide curves", fontsize=11)
    labels = [line.get_label() for line in lines]
    checks = CheckButtons(controls_ax, labels, [True] * len(lines))

    def toggle(label):
        line = lines[labels.index(label)]
        line.set_visible(not line.get_visible())
        fig.canvas.draw_idle()

    checks.on_clicked(toggle)
    # Keep the widget alive for as long as the figure is open.
    fig._gamma_checks = checks
    fig.text(0.08, 0.23, "What happens as scale increases?", fontsize=13, weight="bold")
    fig.text(0.08, 0.08, EXPLANATION, fontsize=11, linespacing=1.5)
    fig.text(0.08, 0.025,
             "f(x) = x² exp(−x/θ) / (2θ³), x ≥ 0. Curves extend beyond the plotted range.",
             fontsize=10, color="#444444")
    return fig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-show", action="store_true", help="Save plots without opening a window")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent.parent,
                        help="Folder for the PNG and SVG plots (default: assignment folder)")
    args = parser.parse_args()
    fig = create_plot()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        path = args.output_dir / f"gamma_scale_2_21.{extension}"
        fig.savefig(path, dpi=180)
        print(f"Saved {path}")
    print(EXPLANATION.replace("θ", "theta").replace("√3", "sqrt(3)")
          .replace("≈", "approximately").replace("²", "^2"))
    if args.no_show:
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    main()
