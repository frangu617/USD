"""Simulate 1,000 height-weight pairs. Run with --no-show to export only."""

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button


def simulate(seed=27):
    rng = np.random.default_rng(seed)
    height = rng.normal(162, 7, 1000)
    weight = 3 + 0.40 * height + rng.normal(0, 8, 1000)
    return height, weight


def summarize(height, weight):
    return np.array([height.mean(), height.std(ddof=1), weight.mean(),
                     weight.std(ddof=1), np.corrcoef(height, weight)[0, 1]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=27)
    parser.add_argument('--no-show', action='store_true')
    parser.add_argument('--output-dir', type=Path,
                        default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 8))
    fig.subplots_adjust(left=0.09, right=0.95, top=0.9, bottom=0.40)
    state = {'seed': args.seed}
    theoretical = [162, 7, 67.8, np.sqrt(0.4**2 * 7**2 + 8**2),
                   0.4 * 7 / np.sqrt(0.4**2 * 7**2 + 8**2)]
    table_ax = fig.add_axes((0.09, 0.17, 0.86, 0.17))
    table_ax.axis('off')
    note = fig.text(0.09, 0.105, '', fontsize=11)
    status = fig.text(0.09, 0.025, '', fontsize=9)

    def render():
        height, weight = simulate(state['seed'])
        state['height'], state['weight'] = height, weight
        stats = summarize(height, weight)
        ax.clear()
        ax.scatter(height, weight, s=18, alpha=0.45, color='#215ec6',
                   edgecolors='none', label='Simulated women')
        x = np.array([height.min()-2, height.max()+2])
        ax.plot(x, 3+0.4*x, color='#c05020', linewidth=2,
                label='Expected weight given height: 3 + 0.40x')
        ax.set(xlabel='Height X (cm)', ylabel='Weight Y (kg)',
               title=f'1,000 simulated height-weight pairs (seed {state["seed"]})')
        ax.grid(alpha=0.2)
        ax.legend(loc='upper left', fontsize=9)
        table_ax.clear()
        table_ax.axis('off')
        labels = ['Height mean (cm)', 'Height SD (cm)', 'Weight mean (kg)',
                  'Weight SD (kg)', 'Correlation']
        rows = [[label, f'{value:.3f}', f'{target:.3f}']
                for label, value, target in zip(labels, stats, theoretical)]
        table = table_ax.table(cellText=rows,
                              colLabels=['Statistic', 'Simulation', 'Model'],
                              cellLoc='center', loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.25)
        note.set_text('Taller women tend to weigh more, with substantial variation at each height.\n'
                      'The 8 kg SD is conditional on height; overall weight SD is about 8.48 kg.')
        status.set_text('Sample SDs use n - 1. Resimulate changes the seed; Save exports the current data and plot.')
        fig.canvas.draw_idle()
        print(f'Seed: {state["seed"]}')
        for label, value, target in zip(labels, stats, theoretical):
            print(f'{label}: simulated {value:.4f}; model {target:.4f}')

    def save(event=None):
        stem = args.output_dir / 'height_weight_2_27'
        for extension in ('png', 'svg'):
            fig.savefig(stem.with_suffix('.'+extension), dpi=180)
        np.savetxt(stem.with_suffix('.csv'),
                   np.column_stack((state['height'], state['weight'])),
                   delimiter=',', header='height_cm,weight_kg', comments='')
        status.set_text(f'Saved PNG, SVG, CSV in {args.output_dir.name} (seed {state["seed"]}).')
        fig.canvas.draw_idle()
        print(f'Saved PNG, SVG, CSV: {stem}')

    def resimulate(event):
        state['seed'] += 1
        render()

    fig.suptitle('Problem 2.27: Heights and weights', fontsize=17)
    buttons = []
    for bounds, label, callback in [((0.60, 0.045, 0.16, 0.035), 'Resimulate', resimulate),
                                    ((0.79, 0.045, 0.16, 0.035), 'Save plot + CSV', save)]:
        button = Button(fig.add_axes(bounds), label)
        button.on_clicked(callback)
        buttons.append(button)
    render()
    save()
    if args.no_show:
        plt.close(fig)
    else:
        plt.show()


if __name__ == '__main__':
    main()
