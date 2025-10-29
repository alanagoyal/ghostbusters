"""
Face detection and blurring utilities for privacy protection.
Uses OpenCV's Haar Cascade classifier for face detection.
"""

import cv2
import numpy as np
from typing import Optional


class FaceBlurrer:
    """Detects and blurs faces in images for privacy protection."""

    def __init__(self, blur_strength: int = 51):
        """
        Initialize the face blurrer with Haar Cascade classifier.

        Args:
            blur_strength: Kernel size for Gaussian blur (must be odd number).
                          Higher values = more blur. Default is 51.
        """
        self.blur_strength = blur_strength if blur_strength % 2 == 1 else blur_strength + 1

        # Load the pre-trained Haar Cascade classifier for face detection
        # This is included with OpenCV by default
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def blur_faces(self, image: np.ndarray, padding: float = 0.2) -> tuple[np.ndarray, int]:
        """
        Detect and blur all faces in an image.

        Args:
            image: Input image as numpy array (BGR format from cv2)
            padding: Extra padding around detected face as percentage (0.2 = 20%)

        Returns:
            Tuple of (blurred_image, num_faces_detected)
        """
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect faces
        # scaleFactor: How much the image size is reduced at each scale
        # minNeighbors: How many neighbors each candidate rectangle should have
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )

        # Create a copy of the image to modify
        blurred_image = image.copy()

        # Blur each detected face
        for (x, y, w, h) in faces:
            # Add padding to ensure entire face is covered
            pad_w = int(w * padding)
            pad_h = int(h * padding)

            # Calculate padded coordinates (ensure they stay within image bounds)
            x1 = max(0, x - pad_w)
            y1 = max(0, y - pad_h)
            x2 = min(image.shape[1], x + w + pad_w)
            y2 = min(image.shape[0], y + h + pad_h)

            # Extract face region
            face_region = blurred_image[y1:y2, x1:x2]

            # Apply Gaussian blur to the face region
            blurred_face = cv2.GaussianBlur(
                face_region,
                (self.blur_strength, self.blur_strength),
                0
            )

            # Replace the face region with blurred version
            blurred_image[y1:y2, x1:x2] = blurred_face

        return blurred_image, len(faces)

    def blur_faces_in_region(
        self,
        image: np.ndarray,
        region: dict,
        padding: float = 0.2
    ) -> tuple[np.ndarray, int]:
        """
        Detect and blur faces only within a specific region (e.g., person bounding box).

        Args:
            image: Input image as numpy array
            region: Dictionary with keys 'x1', 'y1', 'x2', 'y2' defining the region
            padding: Extra padding around detected faces

        Returns:
            Tuple of (blurred_image, num_faces_detected)
        """
        x1, y1 = region['x1'], region['y1']
        x2, y2 = region['x2'], region['y2']

        # Extract the region
        region_img = image[y1:y2, x1:x2]

        # Blur faces in the region
        blurred_region, num_faces = self.blur_faces(region_img, padding)

        # Create a copy and replace the region
        result_image = image.copy()
        result_image[y1:y2, x1:x2] = blurred_region

        return result_image, num_faces
