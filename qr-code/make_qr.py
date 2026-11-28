"""Build the freshnet.in QR code as SVG (brand brown, error level H)."""
import sys
import segno

URL = "https://freshnet.in"
BROWN = "#603913"

def svg(clear_centre: bool) -> str:
    qr = segno.make(URL, error="h", micro=False, boost_error=False)
    m = [list(r) for r in qr.matrix]
    n = len(m)
    # centre square left blank for the logo (an odd number of modules)
    c = 9 if clear_centre else 0
    lo, hi = (n - c) // 2, (n - c) // 2 + c
    def blank(r, col):
        return c and lo <= r < hi and lo <= col < hi
    quiet = 4
    size = n + 2 * quiet
    parts = []
    for r in range(n):
        for col in range(n):
            if m[r][col] and not blank(r, col):
                parts.append(f"M{col+quiet} {r+quiet}h1v1h-1z")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
            f'shape-rendering="crispEdges" data-modules="{n}" data-centre="{c}">'
            f'<rect width="{size}" height="{size}" fill="#fff"/>'
            f'<path fill="{BROWN}" d="{"".join(parts)}"/></svg>')

if __name__ == "__main__":
    out = sys.argv[1]
    open(f"{out}/qr-logo.svg", "w").write(svg(True))
    open(f"{out}/qr-plain.svg", "w").write(svg(False))
    q = segno.make(URL, error="h")
    print("version", q.version, "modules", q.symbol_size(border=0)[0], "error", q.error)
