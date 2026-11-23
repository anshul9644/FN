"""Studio packshots and label fixes for the catalogue.

- FreshNet's own amber bottle cut out of its phone photo (no hand, no clutter),
  relabelled (testa / MCT / VCO) and placed on a clean backdrop with a real shadow
- round sticker on the glass oil cruet, round label on the lip-balm lid
- FreshNet logo burnt into the wooden scoop (milk powder)
- coconut milk can relit with the can's own column shading
"""
import sys
import numpy as np
import cv2

SRC, OUT, LAB = sys.argv[1], sys.argv[2], sys.argv[3]


def load(p):
    im = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if im.shape[2] == 3:
        im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
    return im


def poly_mask(shape, pts, feather=1.2):
    H, W = shape[:2]
    m = np.zeros((H, W), np.float32)
    cv2.fillPoly(m, [np.int32([[x * W, y * H] for x, y in pts])], 1.0, lineType=cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), feather) if feather else m


def warp_label(label, quad, size, arc=0):
    H, W = size
    if arc:
        h, w = label.shape[:2]
        t = np.radians(arc)
        xs = np.linspace(-np.sin(t), np.sin(t), w)
        u = ((np.arcsin(xs) / t + 1) / 2 * (w - 1)).astype(np.float32)
        label = cv2.remap(label, np.tile(u, (h, 1)), np.tile(np.arange(h, dtype=np.float32)[:, None], (1, w)),
                          cv2.INTER_CUBIC)
    lh, lw = label.shape[:2]
    q = np.float32([[x * W, y * H] for x, y in quad])
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [lw, 0], [lw, lh], [0, lh]]), q)
    w = cv2.warpPerspective(label, M, (W, H), flags=cv2.INTER_CUBIC)
    return w[:, :, :3].astype(np.float32), w[:, :, 3].astype(np.float32) / 255, M, (lw, lh)


def column_shading(photo, mask, M, lsize, edge=0.35, strength=1.0):
    """Shading that varies across the label width only, taken from the photo
    (heavily smoothed so old print is averaged out) plus cylinder falloff."""
    H, W = photo.shape[:2]
    lw, lh = lsize
    Minv = np.linalg.inv(M)
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ys, xs = np.nonzero(mask > .5)
    pts = cv2.perspectiveTransform(np.float32(np.stack([xs, ys], 1))[None], Minv)[0]
    u = np.clip((pts[:, 0] / lw * 63).astype(int), 0, 63)
    prof = np.bincount(u, gray[ys, xs], 64) / np.maximum(np.bincount(u, minlength=64), 1)
    prof = cv2.GaussianBlur(prof.reshape(1, -1).astype(np.float32), (0, 0), 6).ravel()
    prof = (prof / np.median(prof)) ** strength
    xn = np.linspace(-1, 1, 64)
    prof = np.clip(prof * (1 - edge * np.abs(xn) ** 3), .45, 1.3)
    # back to image space
    grid = np.zeros((lh, lw), np.float32) + np.interp(np.linspace(0, 63, lw), np.arange(64), prof)[None, :]
    sh = cv2.warpPerspective(grid, M, (W, H), flags=cv2.INTER_LINEAR)
    return np.where(sh > 0, sh, 1)


def finish(lab, photo, a, shade, gloss=0.25, grain=2.6):
    gray = cv2.cvtColor(photo, cv2.COLOR_BGR2GRAY).astype(np.float32)
    lab = lab * shade[:, :, None]
    m = a > .5
    if m.any() and gloss:
        thr = max(np.percentile(gray[m], 99.0), 228)
        hi = cv2.GaussianBlur(np.clip((gray - thr) / 20, 0, 1), (0, 0), 3)
        lab = lab + gloss * hi[:, :, None] * (255 - lab)
    noise = cv2.GaussianBlur(np.random.normal(0, grain, lab.shape).astype(np.float32), (0, 0), .6)
    lab = np.clip(cv2.GaussianBlur(lab, (0, 0), .5) + noise, 0, 255)
    a = cv2.GaussianBlur(a, (0, 0), .7)[:, :, None]
    return (photo.astype(np.float32) * (1 - a) + lab * a).astype(np.uint8)


def save(name, im, q=93):
    cv2.imwrite(f"{OUT}/{name}", im, [cv2.IMWRITE_JPEG_QUALITY, q])


def L(n):
    im = load(f"{LAB}/{n}.png")
    if n in ("round", "oilsticker"):
        h, w = im.shape[:2]
        c = np.zeros((h, w), np.uint8)
        cv2.circle(c, (w // 2, h // 2), min(h, w) // 2 - 2, 255, -1, cv2.LINE_AA)
        im[:, :, 3] = (im[:, :, 3].astype(np.float32) * c / 255).astype(np.uint8)
    return im

# ---------------------------------------------------------------- amber bottle
src = cv2.imread(f"{SRC}/XF_coconut-testa-oil.jpeg")
src = cv2.resize(src, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
H, W = src.shape[:2]
BOTTLE = [(.375, .022), (.615, .022), (.62, .19), (.64, .193), (.70, .198), (.716, .208), (.722, .235),
          (.681, .800), (.672, .814), (.655, .822), (.355, .822), (.338, .814), (.331, .800), (.277, .235),
          (.282, .208), (.30, .198), (.355, .193), (.37, .19)]
bmask = poly_mask(src.shape, BOTTLE, 1.4)
LABEL_Q = [(.313, .237), (.694, .237), (.650, .819), (.356, .819)]
LABEL_CLIP = cv2.erode(bmask, np.ones((5, 5), np.uint8))


def bottle_shot(label_name):
    lab, a, M, ls = warp_label(L(label_name), LABEL_Q, (H, W), arc=34)
    a = a * LABEL_CLIP
    sh = column_shading(src, a, M, ls, edge=.45, strength=.55)
    im = finish(lab, src, a, sh, gloss=.3)
    return im


def stage(bottles, out_w, out_h, scale, xs, bg_top=(236, 241, 246), bg_bot=(214, 224, 232)):
    """Place bottle cut-outs on a seamless backdrop with contact shadow + soft reflection.
    Colours are BGR (warm cream)."""
    y = np.linspace(0, 1, out_h)[:, None, None]
    bg = (np.array(bg_top) * (1 - y) + np.array(bg_bot) * y) * np.ones((out_h, out_w, 3))
    # subtle vignette
    yy, xx = np.mgrid[0:out_h, 0:out_w]
    v = 1 - .10 * (((xx - out_w / 2) / out_w) ** 2 + ((yy - out_h * .45) / out_h) ** 2) * 2
    bg = bg * v[:, :, None]
    floor = int(out_h * .88)
    x0, y0, x1, y1 = [int(v) for v in (.26 * W, .012 * H, .74 * W, .83 * H)]
    for im, cx in zip(bottles, xs):
        crop = im[y0:y1, x0:x1].astype(np.float32)
        m = bmask[y0:y1, x0:x1]
        ch, cw = crop.shape[:2]
        s = scale * out_h / ch
        crop = cv2.resize(crop, (int(cw * s), int(ch * s)), interpolation=cv2.INTER_AREA)
        m = cv2.resize(m, (crop.shape[1], crop.shape[0]), interpolation=cv2.INTER_AREA)
        h, w = m.shape
        left, top = int(cx * out_w - w / 2), floor - h
        # contact + cast shadow
        sh = np.zeros((out_h, out_w), np.float32)
        cv2.ellipse(sh, (left + w // 2, floor - 4), (int(w * .62), int(h * .035)), 0, 0, 360, 1, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), w * .09)
        sh2 = np.zeros_like(sh)
        cv2.ellipse(sh2, (left + w // 2, floor - 2), (int(w * .45), int(h * .012)), 0, 0, 360, 1, -1)
        sh2 = cv2.GaussianBlur(sh2, (0, 0), w * .03)
        bg = bg * (1 - .38 * sh[:, :, None]) * (1 - .45 * sh2[:, :, None])
        # faint reflection
        rf = crop[::-1][: int(h * .22)]
        rm = m[::-1][: int(h * .22)] * np.linspace(.16, 0, rf.shape[0])[:, None]
        rb = min(out_h, floor + rf.shape[0])
        n = rb - floor
        reg = bg[floor:rb, left:left + w]
        bg[floor:rb, left:left + w] = reg * (1 - rm[:n, :, None]) + rf[:n] * rm[:n, :, None]
        reg = bg[top:floor, left:left + w]
        bg[top:floor, left:left + w] = reg * (1 - m[:, :, None]) + crop * m[:, :, None]
    noise = np.random.normal(0, 1.6, bg.shape)
    return np.clip(bg + noise, 0, 255).astype(np.uint8)


shots = {k: bottle_shot(k) for k in ("testa", "mct2", "vco3")}
save("studio-testa.jpg", stage([shots["testa"]], 1500, 1900, .80, [.5]))
save("studio-mct.jpg", stage([shots["mct2"]], 1500, 1900, .80, [.5]))
save("studio-vco-bottle.jpg", stage([shots["vco3"]], 1500, 1900, .80, [.5]))
save("studio-range.jpg", stage([shots["vco3"], shots["mct2"], shots["testa"]], 2400, 1700, .78, [.24, .5, .76]))

# ---------------------------------------------------------------- oil cruet
im = cv2.imread(f"{SRC}/BS_virgin-coconut-oil.jpg")
H, W = im.shape[:2]
st = L("oilsticker")
d = int(.068 * W)
cx, cy, ry = .568 * W, .675 * H, .92
q = [(cx - d / 2) / W, (cy - d * ry / 2) / H, (cx + d / 2) / W, (cy + d * ry / 2) / H]
lab, a, M, ls = warp_label(st, [(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])], (H, W), arc=40)
sh = column_shading(im, a, M, ls, edge=.4, strength=.35)
im = finish(lab, im, a * .97, sh, gloss=.45)
save("brand-oil.jpg", im)

# ---------------------------------------------------------------- lip balm lid
im = cv2.imread(f"{SRC}/QY_virgin-coconut-oil-lip-balm.jpeg")
H, W = im.shape[:2]
lb = L("round")
cx, cy, rx, ry = .6255 * W, .512 * H, .0815 * W, .1535 * H
lb = cv2.resize(lb, (int(2 * rx), int(2 * ry)), interpolation=cv2.INTER_AREA)
Mr = cv2.getRotationMatrix2D((rx, ry), 6, 1)
Mr[0, 2] += cx - rx
Mr[1, 2] += cy - ry
w = cv2.warpAffine(lb, Mr, (W, H), flags=cv2.INTER_CUBIC)
a = w[:, :, 3].astype(np.float32) / 255
gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
low = cv2.GaussianBlur(gray, (0, 0), W / 25)
shade = np.clip(low / np.median(low[a > .5]), .85, 1.12)
im = finish(w[:, :, :3].astype(np.float32), im, a, shade, gloss=.35)
save("brand-lipbalm.jpg", im)

# ---------------------------------------------------------------- milk powder scoop
im = cv2.imread(f"{SRC}/FD_coconut-milk-powder.jpeg")
im = cv2.resize(im, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
H, W = im.shape[:2]
logo = load(f"{LAB}/../img/logo.png")
lw = int(.20 * W)
lh = int(logo.shape[0] * lw / logo.shape[1])
logo = cv2.resize(logo, (lw, lh), interpolation=cv2.INTER_AREA)
a = logo[:, :, 3].astype(np.float32) / 255
Mr = cv2.getRotationMatrix2D((lw / 2, lh / 2), -17, 1)
Mr[0, 2] += .145 * W - lw / 2
Mr[1, 2] += .625 * H - lh / 2
a = cv2.GaussianBlur(cv2.warpAffine(a, Mr, (W, H), flags=cv2.INTER_CUBIC), (0, 0), 1.0)[:, :, None]
burn = im.astype(np.float32) * np.array([.30, .36, .46])
im = (im * (1 - .8 * a) + burn * .8 * a).astype(np.uint8)
save("brand-milkpowder.jpg", im)
print("done")

# ---------------------------------------------------------------- coconut milk can
im = cv2.imread(f"{SRC}/can.jpg")
H, W = im.shape[:2]
t = np.linspace(0, np.pi, 40)
bottom = [(.2475 - .2075 * np.cos(tt), .742 + .05 * np.sin(tt)) for tt in t]
CAN_C = [(.029, .402), (.227, .409), (.43, .396), (.455, .742)] + bottom[::-1][1:] + [(.040, .742)]
cm = poly_mask(im.shape, CAN_C, 1.2)
cm = cv2.erode(cm, np.ones((2, 2), np.uint8))
lab_im = L("can")
# bow top and bottom edges like a cylinder seen from above
h0, w0 = lab_im.shape[:2]
pad = int(.09 * h0)
lab_im = cv2.copyMakeBorder(lab_im, pad, pad, 0, 0, cv2.BORDER_CONSTANT, value=0)
xn = np.linspace(-1, 1, w0)
off = (.075 * h0 * (1 - xn ** 2)).astype(np.float32)
mapy = (np.arange(lab_im.shape[0], dtype=np.float32)[:, None] - off[None, :]).astype(np.float32)
lab_im = cv2.remap(lab_im, np.tile(np.arange(w0, dtype=np.float32), (lab_im.shape[0], 1)), mapy, cv2.INTER_CUBIC)
lab, a, M, ls = warp_label(lab_im, [(.018, .372), (.466, .372), (.466, .812), (.018, .812)], (H, W), arc=70)
a = a * cm
sh = column_shading(im, a, M, ls, edge=0, strength=.35)
# metal cylinder lighting: dark edges, key highlight left of centre, faint rim light right
xg = np.linspace(-1, 1, ls[0])
prof = (1 - .62 * np.abs(xg) ** 2.2) + .30 * np.exp(-((xg + .38) / .16) ** 2) + .10 * np.exp(-((xg - .72) / .08) ** 2)
grid = np.zeros((ls[1], ls[0]), np.float32) + prof[None, :].astype(np.float32)
cyl = cv2.warpPerspective(grid, M, (W, H), flags=cv2.INTER_LINEAR)
sh = sh * np.where(cyl > 0, cyl, 1)
# printed tin: add the can's vertical sheen
gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
im = finish(lab, im, a, sh, gloss=.15, grain=2.2)
save("brand-milk.jpg", im)
print("can done")
