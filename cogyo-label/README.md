# Cogyo Coconut Cream 400 ml: Tin Wrap Label

FreshNet Farms Pvt Ltd (marketer) · Sakthi Coco Products (manufacturer)

| File | What it is |
|---|---|
| `label.html` | Master artwork (HTML/CSS + inline SVG). This is the editable template. |
| `label.pdf` | Print file: 272 × 130 mm sheet = 242 × 100 mm trim + 3 mm bleed + crop and fold marks. |
| `label-preview.png` | Full wrap at trim size, 300 dpi (2856 × 1178 px). |
| `front-preview.png` | Front panel only, 300 dpi. |
| `label-guides.png` | Proof with the fold lines (magenta) and the 3 mm safe zone (blue). |
| `mockup.png` | 3D tin mockup: front view, plus a second tin turned to show the info panel. |
| `mockup.html` | Mockup renderer. It wraps the label onto a cylinder column by column. |
| `render.cjs` | Rebuilds every output: `node render.cjs` (needs Playwright + Chromium). |
| `freshnet-logo.png` | Brand logo (1034 × 376 px). It is used as-is: no crop, no recolour. |
| `fonts/` | Embedded fonts (see below). |

Open `label.html?guides` in a browser to see the trim, fold and safe-zone guides on top of the art.

## Dieline

Standard 400 ml tin: 73 mm diameter × 110 mm tall.

| | Width | Content |
|---|---|---|
| Panel A: Nutrition | 69.6 mm (30 %) | Nutrition table, ingredients, allergen |
| Panel B: Front | 92.8 mm (40 %) | Brand block, hero, 22 % FAT seal, net quantity |
| Panel C: Legal / info | 69.6 mm (30 %) | Storage, addresses, FSSAI, inkjet area, barcode |
| Panel D: Glue overlap | 10 mm | Plain cream, **no text** |
| **Trim** | **242 × 100 mm** | + 3 mm bleed on all sides |

All of these numbers are CSS variables at the top of `label.html` (`--trim-w`, `--overlap`, `--label-h`, `--bleed`, `--safe`, `--k-nutri / --k-front / --k-legal`). When Sakthi sends the exact dieline, change them and run `node render.cjs`. The crop marks, fold marks, PDF page size and guides are all recalculated from these variables.

## Fonts

| Use | Font | Licence |
|---|---|---|
| "Cogyo" wordmark, seal numerals | **Fraunces** Black Italic (variable, wght 900) | SIL OFL (Google Fonts) |
| Everything else | **Inter** 400–800 (variable) | SIL OFL (Google Fonts) |

The font files are in `fonts/`. In the PDF they are embedded as outlines (Type 3), so the printer does not need them installed. To use Playfair Display Black Italic for "Cogyo" instead, add its `@font-face` and put it first in `--f-brand`.

## Colours (RGB in the artwork → print)

| Token | Hex | Use | Print note |
|---|---|---|---|
| `--front-bg` | #1F4D2B | Front background (deep tropical green) | CMYK approx. C80 M35 Y95 K40. Ask the printer to match to a drawdown. |
| `--gold` | #F2C14E | "Cogyo", tagline, seal, rules | **Consider a spot colour: PMS 7408 C** (or metallic PMS 871 C for a foil look) |
| `--cream` | #FBF8EF | Side panels, badges | Can be unprinted white tin + a light tint, or 3–5 % Y |
| `--ink` / `--ink-2` | #222 / #3D3D3D | Body text | Print **100 % K only** (no rich black on small text) |
| `--veg` | #0A8A2E | Veg mark | |

**The printer must convert to CMYK** (or CMYK + spot gold) with their tin-printing ICC profile. The files here are sRGB. Tin printing normally goes over a white base coat, so make sure the cream panels and the white parts of the hero sit on that white.

## Text sizes (checked by script)

- All text is ≥ 3 mm inside the trim. Nothing sits on the overlap strip.
- Smallest x-height on the label is **1.12 mm** (FSSAI minimum is 1 mm). Body text is 6.3 pt, the table is 6.4 pt.
- Net quantity "400 ml": numeral height **4.36 mm** (minimum for 200–500 ml is 4 mm).
- The veg mark is 6 mm, on a white background.

## Hero image

The supplied `hero.jpg` (in `brochure/img/`) is a busy grey flat-lay of many coconut products. It cannot give one focal point on a dark green panel, so the hero is a **vector illustration** instead: a halved coconut with a crown splash of cream, a second half, a whole coconut and palm fronds. In the PDF it is placed as a 600 dpi transparent image (Chromium cannot print SVG filters sharply), and all text stays vector.

To use a professional photo later: in `label.html`, replace the `<svg>` inside `<div class="hero">` with `<img src="hero.jpg" style="object-fit:cover">`. The photo needs to be at least **1100 × 640 px** (300 dpi at 92.8 × 54 mm) and should ideally be cut out on a transparent background.

## Printer must replace / supply

1. **GS1 barcode**: replace the 37 × 26 mm white box with the real EAN-13 from GS1 India. On a 73 mm tin, check the scan; GS1 may recommend "ladder" orientation (bars horizontal) for small diameters.
2. **FSSAI logo**: replace the dashed placeholder beside "Marketed by" with the official FSSAI logo artwork.
3. **Inkjet area** (MRP, unit sale price, batch no., packed on): keep this box free of varnish so the line inkjet can print on it.
4. **Exact dieline** from Sakthi Coco Products: confirm the wrap length, overlap side, label height and any can-seam keep-out areas.
5. **Colour**: CMYK conversion, the gold spot colour (PMS 7408 C suggested), and a white base under the tin.

## Reusing for the Cogyo cream range

Copy `label.html` and change:
- the `:root` colour tokens (e.g. a lighter green or a blue for "Coconut Milk"),
- the product name, tagline, seal value (`22%` / `FAT`) and net quantity in **PANEL B**,
- the nutrition values in **PANEL A**,
- the hero (the crown splash suits milk and cream; for other products, swap the SVG for a photo).

Then run `node render.cjs`.
