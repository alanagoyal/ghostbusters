import unittest
from unittest.mock import MagicMock, patch

from backend.src.camera import camera_source, open_camera, region_of_interest


class CameraTests(unittest.TestCase):
    def test_usb_index(self):
        self.assertEqual(camera_source({"CAMERA_SOURCE": "0"}), 0)

    def test_generic_source_takes_precedence(self):
        self.assertEqual(
            camera_source(
                {"CAMERA_SOURCE": "rtsp://camera/live", "DOORBIRD_IP": "old"}
            ),
            "rtsp://camera/live",
        )

    def test_legacy_credentials_are_encoded(self):
        self.assertEqual(
            camera_source(
                {
                    "DOORBIRD_USERNAME": "a@b",
                    "DOORBIRD_PASSWORD": "a:/#",
                    "DOORBIRD_IP": "camera",
                }
            ),
            "rtsp://a%40b:a%3A%2F%23@camera/mpeg/media.amp",
        )

    def test_missing_configuration(self):
        with self.assertRaises(ValueError):
            camera_source({})

    def test_roi_defaults_preserve_legacy_and_allow_full_new_camera(self):
        self.assertEqual(region_of_interest({}), (0, 0.7, 0, 1))
        self.assertEqual(region_of_interest({"CAMERA_SOURCE": "0"}), (0, 1, 0, 1))

    def test_invalid_roi(self):
        for value in ("-1", "2", "nan", "0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                region_of_interest({"ROI_X_MAX": value})

    def test_network_timeouts_are_passed_when_opening(self):
        cv = MagicMock()
        with patch.dict("sys.modules", {"cv2": cv}):
            open_camera("rtsp://camera/live")
        cv.VideoCapture.assert_called_once_with(
            "rtsp://camera/live",
            cv.CAP_FFMPEG,
            [
                cv.CAP_PROP_OPEN_TIMEOUT_MSEC,
                10000,
                cv.CAP_PROP_READ_TIMEOUT_MSEC,
                10000,
            ],
        )

    def test_usb_does_not_force_ffmpeg(self):
        cv = MagicMock()
        with patch.dict("sys.modules", {"cv2": cv}):
            open_camera(0)
        cv.VideoCapture.assert_called_once_with(0)
