# FreshNet website QR code

`FreshNet-Website-QR.pdf` (A4, 2 pages) links to https://freshnet.in.

- Page 1: branded poster with the palm + FN mark in the centre.
- Page 2: plain code for packaging, labels and visiting cards.

The code is vector (sharp at any size) and uses error level H, so the centre
logo does not stop it scanning. `qr-plain.svg` and `qr-logo.svg` are the codes
on their own for designers. Print at least 2 cm wide and keep the white border.

Rebuild: `python3 make_qr.py .` then `node render.cjs`.
