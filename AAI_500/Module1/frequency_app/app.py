"""Local frequency distribution app. Run: python3 app.py"""
import argparse
import csv
import io
import html
import json
import math
import re
import statistics
import webbrowser
from decimal import Decimal, ROUND_FLOOR, localcontext
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def parse_numbers(raw):
    tokens = re.split(r"[,;\s]+", raw.strip())
    if not raw.strip():
        raise ValueError("Enter at least one number.")
    values = []
    for token in tokens:
        if not token:
            continue
        try:
            value = float(token)
        except ValueError:
            raise ValueError(f"Invalid number: {token!r}.") from None
        if not math.isfinite(value):
            raise ValueError("All numbers must be finite (no NaN or infinity).")
        values.append(value)
    if not values:
        raise ValueError("Enter at least one number.")
    return values


def parse_data(raw):
    """Accept a numeric list or text labels followed by standalone numbers.

    Whole-token parsing keeps the 2 in CO2 out of the observations.
    """
    tokens = [t for t in re.split(r"[,;\s]+", raw.strip()) if t]
    if not tokens:
        return parse_numbers(raw), False
    try:
        float(tokens[0])
    except ValueError:
        pass
    else:
        return parse_numbers(raw), False
    values, labels = [], []
    for token in tokens:
        try:
            value = float(token)
        except ValueError:
            if re.match(r"^[+\-.\d]", token):
                raise ValueError(f"Invalid number: {token!r}.") from None
            labels.append(token)
            continue
        if not math.isfinite(value):
            raise ValueError("All numbers must be finite (no NaN or infinity).")
        if not labels:
            raise ValueError("Expected a label before each value. For multiple numeric columns, import a CSV and select a column.")
        values.append(value)
        labels = []
    if not values:
        raise ValueError("No numeric values found. Paste numbers or labels followed by numbers.")
    if labels:
        raise ValueError(f"Missing numeric value after {' '.join(labels)!r}.")
    return values, True


def pasted_table(raw):
    """Recognize flattened numeric-first tables; preserve every row and column."""
    raw = html.unescape(raw).strip().lstrip('\ufeff')
    tokens = [t for t in re.split(r'[,;\s]+', raw) if t]
    first = next((i for i, token in enumerate(tokens)
                  if _is_number(token)), len(tokens))
    if first < 2 or first + 1 >= len(tokens) or not _is_number(tokens[first + 1]):
        return None
    headers, cells = tokens[:first], tokens[first:]
    if len(set(headers)) != len(headers):
        raise ValueError('Table column names must be unique.')
    if len(cells) % len(headers):
        raise ValueError(f'Table has {len(headers)} headers but an incomplete row. Each row needs one value per column; use NA for missing cells.')
    rows = [cells[i:i + len(headers)] for i in range(0, len(cells), len(headers))]
    numeric = []
    missing = {'na', 'n/a', 'null', 'none', '-'}
    for col in range(len(headers)):
        present = [row[col] for row in rows if row[col].lower() not in missing]
        if present and any(_is_number(cell) for cell in present):
            if not all(_is_number(cell) and math.isfinite(float(cell)) for cell in present):
                raise ValueError(f'Column {headers[col]!r} mixes numbers with invalid values. Correct the values or mark missing entries as NA.')
            numeric.append(col)
    return dict(headers=headers, rows=rows, numeric=numeric)


def compare_groups(table, column, group_column, selected, bins=None):
    import bisect
    if column not in table['numeric'] or not 0 <= group_column < len(table['headers']):
        raise ValueError('Choose a numeric column and a valid grouping column.')
    if not isinstance(selected, list) or not 2 <= len(set(selected)) <= 12:
        raise ValueError('Select between 2 and 12 groups to compare.')
    groups, pooled = [], []
    for name in dict.fromkeys(selected):
        rows = [row for row in table['rows'] if row[group_column] == name]
        values = [float(row[column]) for row in rows if _is_number(row[column])]
        if not values:
            raise ValueError(f'Group {name!r} has no numeric observations.')
        summary = analyze(values, bins)
        groups.append(dict(name=name, summary=summary, values=values, missing=len(rows)-len(values)))
        pooled.extend(values)
    overall = analyze(pooled, bins)
    template = overall['rows']
    edges = [row['lower'] for row in template] + [template[-1]['upper']]
    for group in groups:
        counts = [0] * len(template)
        for value in group.pop('values'):
            counts[min(len(counts)-1, max(0, bisect.bisect_right(edges, value)-1))] += 1
        cumulative = 0
        rows = []
        for row, count in zip(template, counts):
            cumulative += count
            rows.append(dict(row, frequency=count, relative=count/group['summary']['n'], cumulative=cumulative))
        group['summary']['rows'] = rows
    overall.update(values=pooled, input_note='Combined observations from the selected comparison groups. Individual group results appear above.')
    return dict(groups=groups, overall=overall, column=table['headers'][column], group_column=table['headers'][group_column])


def _is_number(token):
    try:
        float(token)
        return True
    except ValueError:
        return False


def nice_edges(low, high, count):
    """Round bin widths upward and align boundaries to multiples of that width."""
    with localcontext() as context:
        context.prec = 40
        lower, upper = Decimal(str(low)), Decimal(str(high))
        target = (upper - lower) / count
        scale = Decimal(10) ** target.adjusted()
        while True:
            for multiplier in ('1', '2', '2.5', '5', '10'):
                width = scale * Decimal(multiplier)
                if width < target:
                    continue
                start = (lower / width).to_integral_value(rounding=ROUND_FLOOR) * width
                # A single bin spanning zero cannot start at a width multiple.
                if count == 1 and lower < 0 < upper:
                    start = (lower / scale).to_integral_value(rounding=ROUND_FLOOR) * scale
                if start + count * width >= upper:
                    return [float(start + i * width) for i in range(count + 1)]
            scale *= 10


def box_summary(values):
    ordered = sorted(values)
    n = len(ordered)
    middle = n // 2
    q1 = statistics.median(ordered[:middle]) if n > 1 else ordered[0]
    q3 = statistics.median(ordered[(n + 1) // 2:]) if n > 1 else ordered[0]
    iqr = q3 - q1
    lower_fence, upper_fence = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    if not all(math.isfinite(v) for v in (q1, q3, iqr, lower_fence, upper_fence)):
        raise ValueError("The numbers are too extreme to summarize. Rescale the data.")
    inside = [v for v in ordered if lower_fence <= v <= upper_fence]
    return dict(minimum=ordered[0], q1=q1, median=statistics.median(ordered),
                q3=q3, maximum=ordered[-1], iqr=iqr,
                lower_whisker=inside[0], upper_whisker=inside[-1],
                outliers=[v for v in ordered if v < lower_fence or v > upper_fence])


def analyze(values, bins=None):
    if not values or any(not math.isfinite(x) for x in values):
        raise ValueError("Provide at least one finite number.")
    n = len(values)
    low, high = min(values), max(values)
    count = min(100, math.ceil(math.log2(n) + 1)) if bins is None else bins
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 100:
        raise ValueError("The number of bins must be an integer from 1 to 100.")
    if low == high:
        edges = [low, high]
        frequencies = [n]
    else:
        width = (high - low) / count
        if not math.isfinite(width) or width == 0:
            raise ValueError("The numeric range is too extreme to bin. Rescale the data.")
        edges = nice_edges(low, high, count)
        if any(not math.isfinite(edge) for edge in edges):
            raise ValueError("The numeric range is too extreme to bin. Rescale the data.")
        if any(a >= b for a, b in zip(edges, edges[1:])):
            raise ValueError("Bins are too narrow for these numbers. Use fewer bins or rescale.")
        import bisect
        frequencies = [0] * count
        for value in values:
            index = min(len(frequencies) - 1, bisect.bisect_right(edges, value) - 1)
            frequencies[index] += 1
    rows, cumulative = [], 0
    for i, frequency in enumerate(frequencies):
        cumulative += frequency
        rows.append(dict(lower=edges[i], upper=edges[i + 1], frequency=frequency,
                         relative=frequency / n, cumulative=cumulative,
                         closed_right=i == len(frequencies) - 1))
    result = dict(n=n, mean=statistics.mean(values), median=statistics.median(values),
                  sample_sd=statistics.stdev(values) if n > 1 else None,
                  population_sd=statistics.pstdev(values), minimum=low, maximum=high,
                  rows=rows, box=box_summary(values))
    if any(isinstance(v, float) and not math.isfinite(v) for v in result.values()):
        raise ValueError("The numbers are too extreme to summarize. Rescale the data.")
    return result


def csv_columns(raw, header=True):
    try:
        dialect = csv.Sniffer().sniff(raw[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    rows = [row for row in csv.reader(io.StringIO(raw), dialect) if any(c.strip() for c in row)]
    if not rows:
        raise ValueError("The CSV is empty.")
    names = rows.pop(0) if header else [f"Column {i + 1}" for i in range(len(rows[0]))]
    columns = []
    for index, name in enumerate(names):
        values, invalid, missing = [], 0, 0
        for row in rows:
            cell = row[index].strip() if index < len(row) else ""
            if not cell:
                missing += 1
                continue
            try:
                value = float(cell)
                if not math.isfinite(value):
                    raise ValueError()
                values.append(value)
            except ValueError:
                invalid += 1
        columns.append(dict(name=name or f"Column {index + 1}", values=values,
                            invalid=invalid, missing=missing))
    return columns


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_error(404)
            return
        body = Path(__file__).with_name("index.html").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 5_000_000:
                raise ValueError("Input must be smaller than 5 MB.")
            payload = json.loads(self.rfile.read(length))
            if self.path == "/analyze":
                raw = html.unescape(payload['text'])
                table = pasted_table(raw)
                if table is not None:
                    body = json.dumps({'table': table}, allow_nan=False).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                values, labeled = parse_data(raw)
                result = analyze(values, payload.get("bins"))
                result['input_note'] = (
                    f"Read {len(values)} numeric values from labeled text. Labels and headers are excluded. "
                    "Check the extracted values below, especially if any labels contain separate numbers."
                    if labeled else f"Read {len(values)} numeric values."
                )
                result['values'] = values
            elif self.path == '/compare':
                table = pasted_table(payload['text'])
                if table is None:
                    raise ValueError('Paste a table with headers and numeric columns first.')
                result = compare_groups(table, int(payload['column']), int(payload['group_column']), payload['groups'], payload.get('bins'))
            elif self.path == "/csv":
                result = csv_columns(payload["text"].lstrip("\ufeff"), payload.get("header", True))
            else:
                self.send_error(404)
                return
            body, status = json.dumps(result, allow_nan=False).encode(), 200
        except (ValueError, TypeError, KeyError, OverflowError, csv.Error) as exc:
            body, status = json.dumps({"error": str(exc)}).encode(), 400
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), Handler) as server:
        url = f"http://127.0.0.1:{server.server_port}"
        print(f"Open {url} — press Ctrl+C to stop.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
