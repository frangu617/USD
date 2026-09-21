"""Interactive sampling charts. Run with python3 app.py; opens a local browser."""
import argparse
import base64
import csv
import errno
import io
import json
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import webbrowser

import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
import numpy as np
from scipy import stats


def number(data, key, default, low=None, high=None, integer=False):
    try:
        value = float(data.get(key, default))
    except (ValueError, TypeError):
        raise ValueError(f'{key}: enter a number.') from None
    if not math.isfinite(value):
        raise ValueError(f'{key}: enter a finite number.')
    if low is not None and value < low or high is not None and value > high:
        raise ValueError(f'{key}: must be between {low} and {high}.')
    if integer and value != int(value):
        raise ValueError(f'{key}: enter a whole number.')
    return int(value) if integer else value


def render(data):
    """Return a chart and the exact plotted sample values, without writing files."""
    mode = data.get('mode', 'poll')
    if mode not in {'poll', 'coin', 'gamma_means', 'gamma_area', 'uniform', 'normal', 'bootstrap'}:
        raise ValueError('Choose a chart type.')
    repetitions = number(data, 'repetitions', 10000, 100, 100000, True)
    seed = number(data, 'seed', 42, 0, 2**32 - 1, True)
    bins = number(data, 'bins', 35, 5, 100, True)
    rng = np.random.default_rng(seed)
    fig = Figure(figsize=(11, 5), layout='constrained')
    summaries, series, messages = [], [], []

    def summary(label, values, theoretical=None):
        item = {'Series': label, 'Mean': f'{np.mean(values):.4f}',
                'SD / empirical SE': f'{np.std(values, ddof=1):.4f}' if len(values) > 1 else 'N/A (one value)'}
        if theoretical is not None:
            item['Theoretical SE'] = f'{theoretical:.4f}'
        summaries.append(item)
        series.append((label, np.asarray(values)))

    def sizes(default):
        raw = str(data.get('sizes', default)).split(',')
        if not 1 <= len(raw) <= 6:
            raise ValueError('Enter 1 to 6 sample sizes, separated by commas.')
        result = [number({'n': x}, 'n', 1, 1, 10000, True) for x in raw]
        if repetitions * sum(result) > 10_000_000:
            raise ValueError('Reduce repetitions or sample sizes (maximum 10 million draws).')
        return result

    def panel_axes(count):
        cols = min(3, count)
        rows = math.ceil(count / cols)
        fig.set_size_inches(6 * cols, 4 * rows)
        axes = fig.subplots(rows, cols, squeeze=False).ravel()
        for ax in axes[count:]:
            ax.set_visible(False)
        return axes[:count]

    def histogram(ax, values, label, mean=None, se=None):
        ax.hist(values, bins=bins, density=True, alpha=0.65, label=label)
        if mean is not None and se is not None and se > 0:
            x = np.linspace(min(values.min(), mean - 4 * se),
                            max(values.max(), mean + 4 * se), 500)
            ax.plot(x, stats.norm.pdf(x, mean, se), label='Normal reference')
        ax.set(ylabel='Probability density')
        ax.legend(fontsize=8)

    if mode == 'poll':
        n = number(data, 'n', 1648, 1, 1000000, True)
        p = number(data, 'p', 0.5, 0, 1)
        observed = number(data, 'observed', 0.515, 0, 1)
        values = rng.binomial(n, p, repetitions) / n
        se = np.sqrt(p * (1 - p) / n)
        ax = fig.subplots()
        histogram(ax, values, 'Simulated sample proportions', p, se)
        ax.axvline(observed, color='crimson', label=f'Observed proportion: {observed:g}')
        ax.set(title=f'Sample proportions: n={n}, population p={p:g}', xlabel='Sample proportion')
        ax.legend()
        summary('Sample proportion', values, se)
        messages.extend([f'Simulated upper tail (proportion ≥ observed): {np.mean(values >= observed):.2%}',
                         f'Simulated two-sided tail: {np.mean(np.abs(values-p) >= abs(observed-p)-1e-12):.2%}'])
    elif mode == 'coin':
        p = number(data, 'p', 0.5, 0, 1)
        ns = sizes('1,2,3,4')
        if max(ns) > 100:
            raise ValueError('Exact coin charts support at most 100 flips per panel.')
        for ax, n in zip(panel_axes(len(ns)), ns):
            x = np.arange(n + 1) / n
            probabilities = stats.binom.pmf(np.arange(n + 1), n, p)
            ax.bar(x, probabilities, width=0.6/n)
            ax.set(title=f'{n} flips, P(heads)={p:g}', xlabel='Proportion of heads', ylabel='Probability')
            series.extend([(f'n={n}: proportion', x), (f'n={n}: probability', probabilities)])
            summaries.append({'Series': f'n={n}', 'Mean': f'{p:.4f}', 'Theoretical SE': f'{np.sqrt(p*(1-p)/n):.4f}'})
    elif mode == 'gamma_area':
        mean = number(data, 'mean', 20, 0.0001, 10000)
        sd = number(data, 'sd', 5, 0.0001, 10000)
        lower = number(data, 'lower', 15, 0, 100000)
        upper = number(data, 'upper', 25, 0, 100000)
        if lower >= upper:
            raise ValueError('Interval upper bound must exceed lower bound.')
        shape, scale = (mean / sd)**2, sd**2 / mean
        dist = stats.gamma(a=shape, scale=scale)
        x = np.linspace(max(dist.ppf(0.0001), 1e-10), max(dist.ppf(0.999), upper), 1500)
        y = dist.pdf(x)
        ax = fig.subplots()
        ax.plot(x, y)
        ax.fill_between(x, y, where=(x >= lower) & (x <= upper), alpha=0.4)
        ax.set(title=f'Gamma density: mean={mean:g}, SD={sd:g}', xlabel='Individual value', ylabel='Probability density')
        messages.append(f'Probability between {lower:g} and {upper:g}: {dist.cdf(upper)-dist.cdf(lower):.2%}')
        summaries.append({'Shape': f'{shape:.4f}', 'Scale': f'{scale:.4f}'})
        series.extend([('x', x), ('density', y)])
    elif mode in {'gamma_means', 'uniform', 'normal'}:
        ns = sizes('25' if mode != 'uniform' else '1,2,10,30')
        mean = number(data, 'mean', 20 if mode == 'gamma_means' else 3, -10000, 10000)
        sd = number(data, 'sd', 5 if mode == 'gamma_means' else 0.4, 0.0001, 10000)
        low = number(data, 'lower', 0, -10000, 10000)
        high = number(data, 'upper', 1, -10000, 10000)
        if mode == 'uniform':
            if low >= high:
                raise ValueError('Uniform upper bound must exceed lower bound.')
            mean, sd = (low + high) / 2, (high - low) / np.sqrt(12)
        if mode == 'gamma_means' and mean <= 0:
            raise ValueError('Gamma mean must be positive.')
        axes = panel_axes(len(ns) + (mode == 'normal'))
        if mode == 'normal':
            sample = rng.normal(mean, sd, ns[0])
            histogram(axes[0], sample, 'One sample of individuals', mean, sd)
            axes[0].set(title=f'Individual observations: n={ns[0]}', xlabel='Individual value')
            summary('One sample of individuals', sample)
            axes = axes[1:]
        for ax, n in zip(axes, ns):
            if mode == 'uniform':
                draws = rng.uniform(low, high, (repetitions, n))
            elif mode == 'normal':
                draws = rng.normal(mean, sd, (repetitions, n))
            else:
                draws = rng.gamma((mean/sd)**2, sd**2/mean, (repetitions, n))
            values = draws.mean(axis=1)
            se = sd / np.sqrt(n)
            histogram(ax, values, 'Simulated means', mean, se)
            ax.set(title=f'{mode.replace("_", " ").title()}: n={n}', xlabel='Sample mean')
            summary(f'Means, n={n}', values, se)
    else:
        ns = sizes('50,500')
        population_size = number(data, 'population_size', 10000, 10, 1000000, True)
        populations = []
        for label, mean_key, sd_key, default_mean, default_sd in [
            ('Model A', 'mean', 'sd', 0.85, 0.10), ('Model B', 'mean_b', 'sd_b', 0.88, 0.08)]:
            mean = number(data, mean_key, default_mean, 0.0001, 10000)
            sd = number(data, sd_key, default_sd, 0.0001, 10000)
            log_variance = np.log1p((sd / mean)**2)
            values = rng.lognormal(np.log(mean)-log_variance/2, np.sqrt(log_variance), population_size)
            populations.append((label, values))
            summary(f'{label} population', values)
            messages.append(f'{label}: {np.mean(values > 1):.2%} of population scores exceed 1.')
        messages.append('Lognormal scores can exceed 1; this model does not enforce the bounds of real precision. Values are not clipped.')
        for ax, n in zip(panel_axes(len(ns)), ns):
            means_by_model = []
            for (label, population), color in zip(populations, ('#2563eb', '#ea580c')):
                means = rng.choice(population, (repetitions, n), replace=True).mean(axis=1)
                means_by_model.append(means)
                ax.hist(means, bins=bins, density=True, alpha=0.5, color=color, label=label)
                ax.axvline(population.mean(), color=color, linestyle='--')
                summary(f'{label} bootstrap means, n={n}', means, population.std(ddof=0)/np.sqrt(n))
            ax.set(title=f'Bootstrap means: n={n}', xlabel='Mean simulated score', ylabel='Probability density')
            ax.legend()
            messages.append(f'n={n}: Model A mean exceeds Model B in {np.mean(means_by_model[0] > means_by_model[1]):.2%} of independent pairs.')

    title = str(data.get('title', '')).strip()[:160]
    if title:
        fig.suptitle(title)
    exports = {}
    for extension in ('png', 'svg'):
        stream = io.BytesIO()
        fig.savefig(stream, format=extension, dpi=160, facecolor='white')
        exports[extension] = base64.b64encode(stream.getvalue()).decode('ascii')
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['series', 'index', 'value'])
    for label, values in series:
        writer.writerows((label, i+1, float(value)) for i, value in enumerate(values))
    exports['csv'] = base64.b64encode(output.getvalue().encode()).decode('ascii')
    return dict(exports=exports, summaries=summaries, messages=messages,
                parameters=data, seed=seed)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ('/', '/index.html'):
            self.send_error(404)
            return
        body = Path(__file__).with_name('index.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != '/chart':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 10000:
                raise ValueError('Request is too large or empty.')
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError('Expected chart parameters.')
            result = render(data)
            status = 200
        except (ValueError, TypeError, OverflowError) as error:
            result, status = {'error': str(error)}, 400
        body = json.dumps(result).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(body)


def create_server(port):
    try:
        return HTTPServer(('127.0.0.1', port), Handler)
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        # Let the OS reserve a free port atomically, avoiding another bind race.
        server = HTTPServer(('127.0.0.1', 0), Handler)
        print(f'Port {port} is already in use; using port {server.server_port}.', flush=True)
        return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8003)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    if not 0 <= args.port <= 65535:
        parser.error('--port must be between 0 and 65535 (0 selects a free port).')
    server = create_server(args.port)
    url = f'http://127.0.0.1:{server.server_port}'
    print(f'Chart Lab: {url}\nPress Ctrl+C to stop.', flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
