import cv2 as cv
import numpy as np
import functools

im = cv.imread('Image.png')
rift_w = 1200
rift_h = 1200
aspect = rift_w / rift_h

if im.shape[1] / im.shape[0] > aspect:
    new_h = im.shape[0]
    new_w = int(im.shape[0] * aspect)
else:
    new_w = im.shape[1]
    new_h = int(im.shape[1] / aspect)

new_x = (im.shape[1] - new_w) // 2
new_y = (im.shape[0] - new_h) // 2

im = im[new_y:new_y + new_h, new_x:new_x + new_w, :]
im = cv.resize(im, (rift_w, rift_h), interpolation=cv.INTER_LANCZOS4)

cv.imwrite('out.png', im)


def make_foveation(im, s):
    im = cv.resize(im, dsize=(0, 0), fx=1 / s, fy=1 / s, interpolation=cv.INTER_NEAREST)
    im = cv.resize(im, dsize=(0, 0), fx=s, fy=s, interpolation=cv.INTER_NEAREST)
    return im


def mask_func(r, cx, cy, i, j, k):
    dy = (i - cy)
    dx = (j - cx)
    return (np.sqrt(dx * dx + dy * dy) > r) * 1


def create_mask(r, cx, cy):
    return np.fromfunction(functools.partial(mask_func, r, cx, cy), im.shape, dtype=np.uint32)


def create_foveation(im, cx, cy):
    im2 = make_foveation(im, 10)
    im3 = make_foveation(im, 20)

    m1 = create_mask(125, cx, cy)
    m2 = create_mask(350, cx, cy)
    m3 = create_mask(525, cx, cy)

    im1 = im * (1 - m1)
    im2 = im2 * (m1 - m2)
    im3 = im3 * m2

    final = im1 + im2 * 0.8 + im3 * 0.6
    return final


cx = im.shape[1] / 2
cy = im.shape[0] / 2
im_left_foveated = create_foveation(im, cx + 100, cy + 25)
im_right_foveated = create_foveation(im, cx - 100, cy + 25)


def distort(im, cx=0.5):
    cam_matrix = np.array([
        [1, 0, im.shape[1] * cx],
        [0, 1, im.shape[0] * 0.55],
        [0, 0, 1]
    ])
    dist_coeff = np.array([5e-6, 0, 0, 0])
    new_cam_matrix = np.array([
        [1.5, 0, im.shape[1] * cx],
        [0, 1.5, im.shape[0] * 0.55],
        [0, 0, 1]
    ])
    return cv.undistort(im, cam_matrix, dist_coeff, None, new_cam_matrix)


im_left_eye = distort(im_left_foveated, 0.6)
im_right_eye = distort(im_right_foveated, 0.4)
im_full = np.concatenate((im_left_eye, im_right_eye), axis=1)
cv.imwrite('out.png', im_full)
