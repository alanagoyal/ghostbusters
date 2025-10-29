#!/usr/bin/env python3
"""
Face detection and blurring utility for privacy protection.
Uses OpenCV's Haar Cascade classifier to detect faces and apply Gaussian blur.
"""

import cv2
import numpy as np
from typing import Tuple


class FaceBlurrer:
    """Detects and blurs faces in images for privacy protection."""

    def __init__(self, blur_strength: int = 51):
        """
        Initialize the face blurrer.

        Args:
            blur_strength: Kernel size for Gaussian blur (must be odd number).
                          Higher values = more blur. Default: 51
        """
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1

        # Load pre-trained Haar Cascade face detector
        # This comes bundled with OpenCV
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        if self.face_cascade.empty():
            raise RuntimeError("Failed to load Haar Cascade face detector")

    def blur_faces(self, image: np.ndarray) -> Tuple[np.ndarray, int]:
        """
        Detect and blur all faces in an image.

        Args:
            image: Input image as numpy array (BGR format from cv2)

        Returns:
            Tuple of (blurred_image, num_faces_detected)
        """
        # Create a copy to avoid modifying the original
        blurred_image = image.copy()

        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        # Parameters tuned for doorbell camera scenarios:
        # - scaleFactor: 1.1 (how much image size is reduced at each scale)
        # - minNeighbors: 5 (how many neighbors each candidate rectangle should have)
        # - minSize: (30, 30) (minimum face size to detect)
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Blur each detected face
        for (x, y, w, h) in faces:
            # Extract face region with some padding for better coverage
            padding = int(w * 0.2)  # 20% padding
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)

            # Extract face region
            face_region = blurred_image[y1:y2, x1:x2]

            # Apply Gaussian blur to face region
            blurred_face = cv2.GaussianBlur(
                face_region,
                (self.blur_strength, self.blur_strength),
                0
            )

            # Replace face region with blurred version
            blurred_image[y1:y2, x1:x2] = blurred_face

        return blurred_image, len(faces)

    def blur_faces_in_region(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int
    ) -> Tuple[np.ndarray, int]:
        """
        Detect and blur faces only within a specific region of the image.
        Useful when you already have a person bounding box.

        Args:
            image: Input image as numpy array (BGR format from cv2)
            x1, y1, x2, y2: Bounding box coordinates defining the region

        Returns:
            Tuple of (blurred_image, num_faces_detected_in_region)
        """
        # Create a copy to avoid modifying the original
        blurred_image = image.copy()

        # Extract the region of interest
        roi = image[y1:y2, x1:x2]

        # Blur faces in the region
        blurred_roi, num_faces = self.blur_faces(roi)

        # Replace the region in the original image
        blurred_image[y1:y2, x1:x2] = blurred_roi

        return blurred_image, num_faces


def blur_faces(image: np.ndarray, blur_strength: int = 51) -> Tuple[np.ndarray, int]:
    """
    Convenience function to blur faces in an image without creating a FaceBlurrer instance.

    Args:
        image: Input image as numpy array (BGR format from cv2)
        blur_strength: Kernel size for Gaussian blur (must be odd). Default: 51

    Returns:
        Tuple of (blurred_image, num_faces_detected)

    Example:
        import cv2
        from face_blur import blur_faces

        # Read image
        image = cv2.imread('photo.jpg')

        # Blur faces
        blurred, num_faces = blur_faces(image)

        print(f"Blurred {num_faces} face(s)")
        cv2.imwrite('photo_blurred.jpg', blurred)
    """
    blurrer = FaceBlurrer(blur_strength=blur_strength)
    return blurrer.blur_faces(image)


if __name__ == "__main__":
    """Test the face blurring functionality."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python face_blur.py <image_path> [output_path]")
        print("\nExample:")
        print("  python face_blur.py detection_20241029_120000.jpg")
        print("  python face_blur.py input.jpg output_blurred.jpg")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace('.jpg', '_blurred.jpg')

    print(f"Loading image: {input_path}")
    image = cv2.imread(input_path)

    if image is None:
        print(f"Error: Could not read image from {input_path}")
        sys.exit(1)

    print("Detecting and blurring faces...")
    blurred, num_faces = blur_faces(image)

    print(f"✓ Detected and blurred {num_faces} face(s)")

    cv2.imwrite(output_path, blurred)
    print(f"✓ Saved blurred image to: {output_path}")
