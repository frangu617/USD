import json
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import webbrowser

from ucimlrepo import fetch_ucirepo


PAGE_SIZE = 100


def create_handler(data):
    """Serve one page at a time, sorting the full dataset when requested."""
    viewer_html = Path(__file__).with_name("poker_hand_viewer.html").read_bytes()
    columns = data.columns.tolist()
    # Reuse the sorted dataframe when moving between pages.
    @lru_cache(maxsize=1)
    def sorted_rows(column, order):
        return (
            data.sort_values(column, ascending=order == "asc", kind="stable")
            if column else data
        )

    class DataHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            request = urlparse(self.path)

            if request.path == "/":
                self.respond(viewer_html, "text/html; charset=utf-8")
                return
            if request.path != "/data":
                self.send_error(404)
                return

            params = parse_qs(request.query)
            try:
                page = int(params.get("page", ["1"])[0])
            except ValueError:
                self.send_error(400, "Page must be a whole number.")
                return

            column = params.get("sort", [""])[0]
            order = params.get("order", ["asc"])[0]
            if (column and column not in columns) or order not in ("asc", "desc"):
                self.send_error(400, "Invalid sort column or direction.")
                return

            total_pages = max(1, (len(data) + PAGE_SIZE - 1) // PAGE_SIZE)
            page = max(1, min(page, total_pages))
            start = (page - 1) * PAGE_SIZE
            rows = sorted_rows(column, order).iloc[start:start + PAGE_SIZE]
            payload = {
                "columns": columns,
                "rows": json.loads(rows.to_json(orient="values")),
                "page": page,
                "page_size": PAGE_SIZE,
                "total_rows": len(data),
                "total_pages": total_pages,
                "sort": column,
                "order": order,
            }
            self.respond(json.dumps(payload).encode("utf-8"), "application/json")

        def respond(self, body, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            # Keep page requests from filling the terminal.
            pass

    return DataHandler


def main():
    print("Fetching the poker hand dataset...")
    poker_hand = fetch_ucirepo(id=158)

    # Data (as pandas dataframes).
    X = poker_hand.data.features
    y = poker_hand.data.targets
    data = X.join(y)

    print(poker_hand.metadata)
    print(poker_hand.variables)

    # Pick an available local port and open the browser viewer.
    with ThreadingHTTPServer(("127.0.0.1", 0), create_handler(data)) as server:
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"\nView all {len(data):,} rows at {url}")
        print("Keep this script running while using the table. Press Ctrl+C to stop.")
        try:
            if not webbrowser.open(url):
                print("Open the URL above in your browser to view the table.")
        except webbrowser.Error:
            print("Open the URL above in your browser to view the table.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nViewer stopped.")


if __name__ == "__main__":
    main()


# Additional Variable Information

# 1) S1 "Suit of card #1"
#     Ordinal (1-4) representing {Hearts, Spades, Diamonds, Clubs}

# 2) C1 "Rank of card #1"
#     Numerical (1-13) representing (Ace, 2, 3, ... , Queen, King)

# 3) S2 "Suit of card #2"
#     Ordinal (1-4) representing {Hearts, Spades, Diamonds, Clubs}

# 4) C2 "Rank of card #2"
#     Numerical (1-13) representing (Ace, 2, 3, ... , Queen, King)

# 5) S3 "Suit of card #3"
#     Ordinal (1-4) representing {Hearts, Spades, Diamonds, Clubs}

# 6) C3 "Rank of card #3"
#     Numerical (1-13) representing (Ace, 2, 3, ... , Queen, King)

# 7) S4 "Suit of card #4"
#     Ordinal (1-4) representing {Hearts, Spades, Diamonds, Clubs}

# 8) C4 "Rank of card #4"
#     Numerical (1-13) representing (Ace, 2, 3, ... , Queen, King)

# 9) S5 "Suit of card #5"
#     Ordinal (1-4) representing {Hearts, Spades, Diamonds, Clubs}

# 10) C5 "Rank of card 5"
#     Numerical (1-13) representing (Ace, 2, 3, ... , Queen, King)

# 11) CLASS "Poker Hand"
#     Ordinal (0-9)

#     0: Nothing in hand; not a recognized poker hand 
#     1: One pair; one pair of equal ranks within five cards
#     2: Two pairs; two pairs of equal ranks within five cards
#     3: Three of a kind; three equal ranks within five cards
#     4: Straight; five cards, sequentially ranked with no gaps
#     5: Flush; five cards with the same suit
#     6: Full house; pair + different rank three of a kind
#     7: Four of a kind; four equal ranks within five cards
#     8: Straight flush; straight + flush
#     9: Royal flush; {Ace, King, Queen, Jack, Ten} + flush
