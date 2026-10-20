import unittest
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from backend.src.costume_detector import detect_people_and_costumes


def model_with_boxes(*classes):
    boxes = [
        SimpleNamespace(cls=[cls], conf=[0.95], xyxy=[[2, 2, 20, 20]])
        for cls in classes
    ]
    model = Mock(return_value=[SimpleNamespace(boxes=boxes)])
    model.names = {2: "car"}
    return model


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.frame = np.zeros((32, 32, 3), dtype=np.uint8)

    def test_people_work_without_classifier(self):
        detections = detect_people_and_costumes(
            self.frame, model_with_boxes(0, 0, 2), None
        )
        self.assertEqual(len(detections), 2)
        self.assertTrue(all(d["detection_type"] == "person" for d in detections))

    def test_inflatable_requires_positive_validation(self):
        client = Mock()
        client.classify_costume.return_value = ("Dinosaur", 0.9, "Inflatable T-Rex")
        result = detect_people_and_costumes(self.frame, model_with_boxes(2), client)
        self.assertEqual(result[0]["costume_classification"], "Dinosaur")
        self.assertEqual(result[0]["detection_type"], "inflatable")

    def test_non_costume_and_unavailable_classifier_are_rejected(self):
        for response in (("Person", 0.9, "No costume"), (None, None, None)):
            client = Mock()
            client.classify_costume.return_value = response
            self.assertEqual(
                detect_people_and_costumes(self.frame, model_with_boxes(2), client), []
            )

    def test_classifier_failure_preserves_standard_people(self):
        client = Mock()
        client.classify_costume.side_effect = RuntimeError("offline")
        result = detect_people_and_costumes(self.frame, model_with_boxes(0, 2), client)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["detection_type"], "person")
