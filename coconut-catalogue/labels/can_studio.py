"""Coconut milk can packshot: real blank steel can (Wikimedia, Sun Ladder, CC BY-SA 3.0),
FreshNet label wrapped pixel-by-pixel around the cylinder, pressed lid added."""
import sys
import numpy as np
import cv2

SRC, OUT, LAB = sys.argv[1], sys.argv[2], sys.argv[3]
im = cv2.imread(f"{SRC}/Empty_tin_can2009-01-19.jpg").astype(np.float32)
H, W = im.shape[:2]
lab = cv2.imread(f"{LAB}/can.png", cv2.IMREAD_UNCHANGED)
if lab.shape[2] == 3:
    lab = np.dstack([lab, np.full(lab.shape[:2], 255, np.uint8)])
lab = lab[int(.024 * lab.shape[0]):int(.96 * lab.shape[0])]          # drop outer stripes
lh, lw = lab.shape[:2]

cx, R = .5 * W, .2925 * W
ytop, ybot, ry = .296 * H, .724 * H, .083 * H
ARC = np.radians(80)                                                  # visible half-angle mapped to label

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
xn = (xx - cx) / R
inside = np.abs(xn) < 1
s = np.sqrt(np.clip(1 - xn ** 2, 0, 1))
theta = np.arcsin(np.clip(xn, -1, 1))
u = (theta / ARC * .5 + .5) * (lw - 1)
v = (yy - (ytop + ry * s)) / (ybot - ytop) * (lh - 1)
mapx, mapy = u.astype(np.float32), v.astype(np.float32)
L = cv2.remap(lab, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
a = (L[:, :, 3].astype(np.float32) / 255) * inside * (np.abs(xn) < .992)
a = cv2.GaussianBlur(a, (0, 0), .8)
col = L[:, :, :3].astype(np.float32)

# studio lighting on a cylinder: soft key from front-left, rim light right, falloff to edges
light = (1 - .42 * np.abs(xn) ** 2.6) + .20 * np.exp(-((xn + .42) / .2) ** 2) + .07 * np.exp(-((xn - .66) / .1) ** 2)
# keep the photo's large-scale light (top brighter, shadow side)
gray = cv2.cvtColor(im.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
low = cv2.GaussianBlur(gray, (0, 0), W / 10)
mid = np.median(low[a > .5])
light = light * np.clip(low / mid, .85, 1.1) ** .5
col = col * light[:, :, None]
# glossy print: narrow specular streak
spec = .28 * np.exp(-((xn + .48) / .05) ** 2)
col = col + spec[:, :, None] * (255 - col)
# shadow cast by the top bead onto the label
top_curve = ytop + ry * s
col = col * (1 - .25 * np.exp(-np.clip(yy - top_curve, 0, None) / (.006 * H)))[:, :, None]
col = col + np.random.normal(0, 2.0, col.shape)
im = im * (1 - a[:, :, None]) + col * a[:, :, None]

# pressed lid over the open top
lcx, lcy, lrx, lry = .505 * W, .252 * H, .283 * W, .074 * H
d = ((xx - lcx) / lrx) ** 2 + ((yy - lcy) / lry) ** 2
lid = d <= 1
r = np.sqrt(d)
base = 196 - 26 * ((xx - lcx) / lrx) + 10 * ((yy - lcy) / lry)       # brushed metal gradient
rings = (-14 * np.exp(-((r - .93) / .03) ** 2) + 12 * np.exp(-((r - .86) / .03) ** 2)
         - 8 * np.exp(-((r - .62) / .02) ** 2) + 7 * np.exp(-((r - .57) / .02) ** 2)
         - 6 * np.exp(-((r - .36) / .02) ** 2) + 5 * np.exp(-((r - .32) / .02) ** 2))
metal = base + rings + 6 * np.exp(-(((xx - lcx + .1 * lrx) / (.25 * lrx)) ** 2 + ((yy - lcy + .2 * lry) / (.5 * lry)) ** 2))
metal = cv2.GaussianBlur(metal.astype(np.float32), (0, 0), 1.2) + np.random.normal(0, 1.5, metal.shape)
lidc = np.dstack([metal * 1.0, metal * .99, metal * .97])
la = cv2.GaussianBlur(lid.astype(np.float32), (0, 0), 1.0)[:, :, None]
im = im * (1 - la) + lidc * la

im = np.clip(im, 0, 255).astype(np.uint8)
im = im[int(.10 * H):int(.93 * H), int(.06 * W):int(.94 * W)]
cv2.imwrite(f"{OUT}/studio-can.jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 93])
print("ok", im.shape)
