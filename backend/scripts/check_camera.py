"""Read one frame without saving it, classifying it, or uploading it."""

from dotenv import load_dotenv

from backend.src.camera import camera_source, open_camera


def main():
    load_dotenv()
    try:
        source = camera_source()
    except ValueError as error:
        print(error)
        return 1
    cap = open_camera(source)
    try:
        ok, frame = cap.read()
        if not ok or frame is None:
            print(
                "Camera check failed: check power, network, credentials and stream URL."
            )
            return 1
        height, width = frame.shape[:2]
        print(f"Camera check passed: {width}x{height}. No image saved or uploaded.")
        return 0
    finally:
        cap.release()


if __name__ == "__main__":
    raise SystemExit(main())
