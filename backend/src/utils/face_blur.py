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

        # Load the pre-trained Haar Cascade classifier for frontal face detection
        # This is included with OpenCV by default
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        # Verify the cascade loaded successfully
        if self.face_cascade.empty():
            raise RuntimeError("Failed to load frontal face Haar Cascade classifier")

        # Also load profile face detector for better coverage
        self.profile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )

        if self.profile_cascade.empty():
            print("⚠️  Warning: Profile face cascade not loaded, only frontal faces will be detected")

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

        # Detect frontal faces
        # scaleFactor: How much the image size is reduced at each scale
        # minNeighbors: How many neighbors each candidate rectangle should have
        # Lower minNeighbors = more sensitive but more false positives
        frontal_faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,  # Reduced from 5 for better sensitivity
            minSize=(30, 30)
        )

        # Detect profile faces (left and right)
        profile_faces = []
        if not self.profile_cascade.empty():
            # Detect left-facing profiles
            left_profiles = self.profile_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30)
            )
            # Detect right-facing profiles by flipping the image
            flipped = cv2.flip(gray, 1)
            right_profiles = self.profile_cascade.detectMultiScale(
                flipped,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30)
            )
            # Convert right profile coordinates back to original orientation
            right_profiles_corrected = []
            if len(right_profiles) > 0:
                for (x, y, w, h) in right_profiles:
                    x_flipped = gray.shape[1] - x - w
                    right_profiles_corrected.append((x_flipped, y, w, h))

            # Combine left and right profiles
            profile_faces = list(left_profiles)
            if len(right_profiles_corrected) > 0:
                profile_faces.extend(right_profiles_corrected)

        # Combine all detected faces
        all_faces = list(frontal_faces) if len(frontal_faces) > 0 else []
        if len(profile_faces) > 0:
            all_faces.extend(profile_faces)

        # Remove duplicate detections (faces detected by multiple cascades)
        faces = self._remove_duplicate_faces(all_faces) if len(all_faces) > 0 else []

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

    def _remove_duplicate_faces(self, faces: list) -> list:
        """
        Remove duplicate face detections that overlap significantly.

        Args:
            faces: List of face bounding boxes (x, y, w, h)

        Returns:
            Filtered list with duplicates removed
        """
        if len(faces) == 0:
            return []

        # Convert to list of tuples if it's a numpy array
        faces_list = [tuple(f) for f in faces]

        # Sort by area (largest first) to keep larger detections
        faces_list = sorted(faces_list, key=lambda f: f[2] * f[3], reverse=True)

        filtered = []
        for face in faces_list:
            x1, y1, w1, h1 = face
            # Check if this face overlaps significantly with any already-kept face
            is_duplicate = False
            for kept_face in filtered:
                x2, y2, w2, h2 = kept_face
                # Calculate intersection over union (IoU)
                x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = x_overlap * y_overlap
                area1 = w1 * h1
                area2 = w2 * h2
                iou = overlap_area / (area1 + area2 - overlap_area) if (area1 + area2 - overlap_area) > 0 else 0
                # If IoU > 0.3, consider it a duplicate
                if iou > 0.3:
                    is_duplicate = True
                    break
            if not is_duplicate:
                filtered.append(face)

        return filtered

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
