"""Place FreshNet labels onto real product photos.

Each label is curved (cylinder) where needed, warped into the label quad,
then relit with the photo's own shading, highlights and grain.
"""
import sys
import numpy as np
import cv2

SRC = sys.argv[1]   # folder with source photos
OUT = sys.argv[2]   # folder for branded photos
LAB = sys.argv[3]   # folder with label PNGs


def load(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def cylinder(label, arc_deg, sag=0.0):
    """Compress label toward its edges as if wrapped on a cylinder; sag curves
    the top and bottom edges like a can seen from slightly above."""
    h0, w = label.shape[:2]
    pad = int(abs(sag) * h0) + 2
    label = cv2.copyMakeBorder(label, pad, pad, 0, 0, cv2.BORDER_CONSTANT, value=0)
    h = label.shape[0]
    t = np.radians(arc_deg)
    xs = np.linspace(-np.sin(t), np.sin(t), w)
    u = (np.arcsin(xs) / t + 1) / 2 * (w - 1)
    xn = xs / np.sin(t)
    off = sag * h0 * (1 - xn ** 2) - sag * h0 / 2
    mapx = np.tile(u.astype(np.float32), (h, 1))
    mapy = (np.arange(h, dtype=np.float32)[:, None] - off[None, :]).astype(np.float32)
    return cv2.remap(label, mapx, mapy, cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)


def place(photo, label, quad, arc=0, shade=0.7, gloss=0.5, edge_dark=0.25, keep=None, sag=0.0):
    H, W = photo.shape[:2]
    q = np.float32([[x * W, y * H] for x, y in quad])
    if arc:
        label = cylinder(label, arc, sag)
    lh, lw = label.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]]), q)
    warped = cv2.warpPerspective(label, M, (W, H), flags=cv2.INTER_CUBIC)
    a = warped[:, :, 3:4].astype(np.float32) / 255.0
    a = cv2.GaussianBlur(a, (0, 0), 0.8)[:, :, None]
    lab = warped[:, :, :3].astype(np.float32)

    # lighting from the photo: large-scale luminance under the label
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY).astype(np.float32)
    m = a[:, :, 0] > 0.5
    # lighting = heavily smoothed luminance, so the old label's print is averaged away
    k = max(W, H) / 14
    low = cv2.GaussianBlur(gray, (0, 0), k)
    ref = np.median(low[m]) if m.any() else 128
    light = np.clip((low / ref), 0.8, 1.15) ** shade
    # darken toward cylinder edges
    if arc:
        xs = np.linspace(-1, 1, lw, dtype=np.float32)
        fall = 1 - edge_dark * xs ** 4
        fl = np.tile(fall, (lh, 1))[:, :, None]
        fl = cv2.warpPerspective(fl, M, (W, H), flags=cv2.INTER_LINEAR)
        light = light * np.where(fl > 0, fl, 1)
    lab = lab * light[:, :, None]
    # specular highlights from the original (glass / can shine)
    thr = max(np.percentile(gray[m], 99.3), 232) if m.any() else 255
    hi = np.clip((gray - thr) / 18, 0, 1)
    hi = cv2.GaussianBlur(hi.astype(np.float32), (0, 0), 2)
    lab = lab + gloss * hi[:, :, None] * (255 - lab)
    # grain to match the photo
    noise = cv2.GaussianBlur(np.random.normal(0, 3.2, lab.shape).astype(np.float32), (0, 0), 0.6)
    lab = np.clip(cv2.GaussianBlur(lab, (0, 0), 0.55) + noise, 0, 255)

    if keep is not None:          # pixels that stay in front (e.g. a thumb)
        a = a * (1 - keep[:, :, None])
    out = photo.astype(np.float32) * (1 - a) + lab * a
    return out.astype(np.uint8)


def skin_mask(photo, xmin):
    H, W = photo.shape[:2]
    hsv = cv2.cvtColor(photo, cv2.COLOR_BGR2HSV)
    b, g, r = [photo[:, :, i].astype(int) for i in range(3)]
    m = ((r > 95) & (r > g + 15) & (r > b + 25) & (hsv[:, :, 1] > 40)).astype(np.float32)
    m[:, : int(xmin * W)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return cv2.GaussianBlur(m, (0, 0), 1.5)


def save(name, im, q=92):
    cv2.imwrite(f"{OUT}/{name}", im[:, :, :3], [cv2.IMWRITE_JPEG_QUALITY, q])


L = lambda n: load(f"{LAB}/{n}.png")
P = lambda n: cv2.imread(f"{SRC}/{n}.jpg")

# coconut oil: flat PET bottle
im = P("kaleeswari")
im = place(im, L("oil"), [(.424, .398), (.667, .398), (.667, .632), (.424, .632)], arc=38, shade=.6, gloss=.35, edge_dark=.18)
save("brand-oil.jpg", im)

# virgin coconut oil: glass jar, label band
im = P("jar")
im = place(im, L("jar"), [(.093, .600), (.889, .590), (.886, .950), (.096, .955)], arc=62, shade=.85, gloss=.35, edge_dark=.4, sag=.07)
save("brand-vco.jpg", im)

# coconut milk: tin can
im = P("can")
im = place(im, L("can"), [(.008, .398), (.454, .398), (.454, .780), (.008, .780)], arc=68, shade=.85, gloss=.3, edge_dark=.5, sag=.055)
save("brand-milk.jpg", im)

# coconut milk powder: clear box, front label
im = P("powderbox")
im = place(im, L("box"), [(.205, .655), (.845, .655), (.82, .935), (.228, .935)], shade=.6, gloss=.2)
# soften background brand signage outside the box
H, W = im.shape[:2]
box = np.zeros((H, W), np.float32)
poly = np.int32([[x * W, y * H] for x, y in [(.26, .105), (.84, .115), (.93, .55), (.87, .83), (.81, .975), (.25, .985), (.17, .85), (.04, .56)]])
cv2.fillPoly(box, [poly], 1.0)
box = cv2.GaussianBlur(box, (0, 0), 14)[:, :, None]
bg = cv2.GaussianBlur(im, (0, 0), 9)
im = (im * box + bg * (1 - box)).astype(np.uint8)
H, W = im.shape[:2]
save("brand-milkpowder.jpg", im[int(.07 * H):, int(.02 * W):int(.98 * W)])

# coconut flour: tall cylinder tube (crop away the old upside-down label at top)
im = P("flourbag")
im = place(im, L("flour"), [(.17, .37), (.735, .37), (.80, .63), (.17, .63)], arc=55, shade=.8, gloss=.3, edge_dark=.35)
H = im.shape[0]
save("brand-flour.jpg", im[int(.16 * H):, :])

# testa oil: FreshNet's own photo, keep the thumb in front
im = P("testa")
keep = skin_mask(im, .5)
im = place(im, L("testa"), [(.205, .268), (.577, .268), (.587, .936), (.233, .936)], arc=40, shade=.55, gloss=.45, edge_dark=.2, keep=keep)
save("brand-testa.jpg", im)

# coconut sugar: logo branded (burnt) onto the wooden spoon handle
im = P("sugar")
H, W = im.shape[:2]
logo = load(f"{LAB}/../img/logo.png")
lh = int(.068 * H)
lw = int(logo.shape[1] * lh / logo.shape[0])
logo = cv2.resize(logo, (lw, lh), interpolation=cv2.INTER_AREA)
a = logo[:, :, 3].astype(np.float32) / 255
canvas_a = np.zeros((H, W), np.float32)
cx, cy, ang = .80 * W, .444 * H, 5.5
M = cv2.getRotationMatrix2D((lw / 2, lh / 2), ang, 1.0)
M[0, 2] += cx - lw / 2
M[1, 2] += cy - lh / 2
canvas_a = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_CUBIC)
canvas_a = cv2.GaussianBlur(canvas_a, (0, 0), 0.9)[:, :, None]
burn = im.astype(np.float32) * np.array([0.28, 0.34, 0.42])  # dark brown, BGR
im = (im * (1 - .82 * canvas_a) + burn * .82 * canvas_a).astype(np.uint8)
save("brand-sugar.jpg", im)
print("done")
