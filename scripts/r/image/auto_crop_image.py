import argparse

import cv2
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("in_file", type=str)
    parser.add_argument("-o", "--out-file", type=str, default=None)
    parser.add_argument("--inplace", action="store_true")

    args = parser.parse_args()
    in_file = args.in_file
    if args.inplace:
        out_file = in_file
    else:
        if args.out_file:
            out_file = args.out_file
        else:
            out_file = args.in_file + ".out.png"

    img = cv2.imread(in_file)

    # Delete full white rows at the bottom of the image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    last_row = gray.shape[0] - 1
    while last_row >= 0 and np.all(gray[last_row, :] > 240):
        last_row -= 1
    print(last_row + 1)
    img = img[0 : last_row + 1, :, :]

    # Get color bounds of white region
    lower = (180, 180, 180)  # lower bound for each channel
    upper = (255, 255, 255)  # upper bound for each channel

    # Threshold
    threshold = cv2.inRange(img, lower, upper)

    # get the largest contour
    contours = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = contours[0] if len(contours) == 2 else contours[1]
    big_contour = max(contours, key=cv2.contourArea)

    # get bounding box
    x, y, w, h = cv2.boundingRect(big_contour)
    print(x, y, w, h)

    # Crop the image at the bounds
    crop = img[y : y + h, x : x + w]

    # Save the cropped image
    cv2.imwrite(out_file, crop)
