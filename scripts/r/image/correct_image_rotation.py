import argparse

import cv2
import numpy as np


def correct_image_rotation(image_path):
    # Load the image
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image at {image_path}")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect edges
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    # Detect lines using Hough Transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    # Calculate the rotation angle
    if lines is not None:
        angles = []
        for rho, theta in lines[:, 0]:
            angle = (theta - np.pi / 2) * (180 / np.pi)
            angles.append(angle)

        # Compute the median angle (to reduce outlier influence)
        median_angle = np.median(angles)
        print(median_angle)

        # Rotate the image to correct it
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h))

        output_path = "rotated_" + image_path
        cv2.imwrite(output_path, rotated_image)
        print(f"Rotated image saved as {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_path", type=str)
    args = parser.parse_args()

    correct_image_rotation(args.image_path)
