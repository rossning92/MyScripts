import cv2 as cv
import numpy as np
import functools

im = cv.imread('Image.png')


def make_foveation(im, s):
    im = cv.resize(im, dsize=(0, 0), fx=1 / s, fy=1 / s, interpolation=cv.INTER_NEAREST)
    im = cv.resize(im, dsize=(0, 0), fx=s, fy=s, interpolation=cv.INTER_NEAREST)
    return im


im2 = make_foveation(im, 8)
im3 = make_foveation(im, 16)


def mask_func(r, i, j, k):
    cy = im.shape[0] / 2
    cx = im.shape[1] / 2
    dy = (i - cy)
    dx = (j - cx)

    return (np.sqrt(dx * dx + dy * dy) > r) * 1


def create_mask(r):
    return np.fromfunction(functools.partial(mask_func, r), im.shape, dtype=np.uint32)


m1 = create_mask(500)
m2 = create_mask(1000)
m3 = create_mask(1500)

im1 = im * (1 - m1)
im2 = im2 * (m1 - m2)
im3 = im3 * m2

final = im1 + im2 * 0.8 + im3 * 0.6

cam_matrix = np.array([
    [1, 0, im.shape[1] / 2],
    [0, 1, im.shape[0] / 2],
    [0, 0, 1]
])
out = cv.undistort(final, cam_matrix, np.array([1e-6, 0, 0, 0]))

cv.imwrite('out.png', out)

