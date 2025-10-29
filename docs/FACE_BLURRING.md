# Face Blurring for Privacy Protection

This document describes the face blurring feature that has been added to the costume classifier system to protect the privacy of detected individuals.

## Overview

All security stills captured by the system now have faces automatically blurred before being saved locally or uploaded to Supabase storage. This ensures privacy compliance while still maintaining the ability to detect people and classify costumes.

## Implementation

### Face Detection

The system uses **OpenCV's Haar Cascade classifier** for face detection:
- Pre-trained model: `haarcascade_frontalface_default.xml` (included with OpenCV)
- Fast and efficient for real-time processing
- Works well with frontal face detection
- No additional dependencies required beyond OpenCV

### Face Blurring

Once faces are detected, they are blurred using:
- **Gaussian blur** with kernel size of 51x51 pixels
- 20% padding around detected face regions to ensure full coverage
- Applied to the entire face region for privacy protection

### Processing Pipeline

1. **Frame Capture**: RTSP stream frame is captured from DoorBird camera
2. **Person Detection**: YOLOv8n detects people in the frame
3. **Bounding Box Drawing**: Green boxes and labels are drawn around detected people
4. **Face Blurring**: All faces in the frame are detected and blurred (NEW)
5. **Local Save**: Blurred frame is saved as JPEG file
6. **Supabase Upload**: Blurred image is uploaded to cloud storage
7. **Costume Classification**: Person crops (with blurred faces) are sent to Baseten API

## Files Modified

### New Files

- **`backend/src/utils/face_blur.py`**: Core face detection and blurring module
  - `FaceBlurrer` class with configurable blur strength
  - `blur_faces()`: Blur all faces in an image
  - `blur_faces_in_region()`: Blur faces only within a specific bounding box

- **`backend/scripts/test_face_blur.py`**: Test script to verify face blurring on test images
  - Processes all test images in `backend/tests/fixtures/`
  - Outputs blurred images to `backend/test_blurred_output/`
  - Reports number of faces detected and blurred

### Modified Files

- **`backend/scripts/main.py`**: Main detection script
  - Import `FaceBlurrer`
  - Initialize face blurrer at startup
  - Apply face blurring before saving frames
  - Report number of faces blurred in console output

## Usage

### In Production

Face blurring is automatically enabled when running the main detection script:

```bash
uv run backend/scripts/main.py
```

Console output will show:
```
✅ Face blurrer initialized (privacy protection enabled)
...
👤 2 person(s) detected! (Detection #1)
   🔒 3 face(s) blurred for privacy
   Saved locally: detection_20241029_143022.jpg
```

### Testing Face Blurring

To test face blurring on the fixture images:

```bash
uv run backend/scripts/test_face_blur.py
```

This will:
1. Process all `test-*.png` images in `backend/tests/fixtures/`
2. Detect and blur faces in each image
3. Save blurred versions to `backend/test_blurred_output/`
4. Report statistics on faces detected

### Adjusting Blur Strength

The blur strength can be adjusted when initializing the `FaceBlurrer`:

```python
# Default blur strength (51)
face_blurrer = FaceBlurrer()

# Lighter blur (31)
face_blurrer = FaceBlurrer(blur_strength=31)

# Heavier blur (71)
face_blurrer = FaceBlurrer(blur_strength=71)
```

Note: Blur strength must be an odd number. If an even number is provided, it will be automatically incremented by 1.

### Advanced Usage

Blur faces only within a person's bounding box (more targeted):

```python
from backend.src.utils.face_blur import FaceBlurrer

face_blurrer = FaceBlurrer()

# Define person bounding box
person_box = {"x1": 100, "y1": 150, "x2": 300, "y2": 450}

# Blur only faces within this region
blurred_image, num_faces = face_blurrer.blur_faces_in_region(
    image,
    region=person_box
)
```

## Privacy Considerations

### What is Protected

✅ **Faces are blurred** in:
- All locally saved detection images
- All images uploaded to Supabase storage
- Person crops sent to Baseten for costume classification

### What Remains Visible

ℹ️ The following information is **still visible/stored**:
- Body shape and posture (needed for costume classification)
- Bounding box coordinates (stored in database)
- Person detection metadata (timestamps, confidence scores)
- Costume classifications and descriptions

### Limitations

⚠️ Current limitations of the face detection:
- Works best with **frontal faces** (Haar Cascades)
- May miss faces that are:
  - Turned to the side (profile views)
  - Partially occluded
  - Too small in the frame
  - Wearing masks or heavy makeup
- Does not blur faces in real-time video stream (only saved frames)

### Future Improvements

Potential enhancements for better privacy protection:

1. **Multi-angle face detection**: Add profile face detection cascades
2. **Deep learning face detection**: Switch to DNN-based models (MTCNN, RetinaFace)
3. **Pixelation option**: Alternative to Gaussian blur
4. **Full body blur**: Option to blur entire person, not just face
5. **Configurable via environment**: Allow enabling/disabling via `.env`

## Testing

### Unit Testing

To add unit tests for face blurring:

```python
# backend/tests/unit/test_face_blur.py
import cv2
import numpy as np
from backend.src.utils.face_blur import FaceBlurrer

def test_face_blurrer_initialization():
    blurrer = FaceBlurrer(blur_strength=51)
    assert blurrer.blur_strength == 51

def test_blur_faces_returns_tuple():
    blurrer = FaceBlurrer()
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    result, count = blurrer.blur_faces(test_image)
    assert isinstance(result, np.ndarray)
    assert isinstance(count, int)
```

### Integration Testing

Test with real costume images:

```bash
uv run backend/scripts/test_face_blur.py
```

Check output in `backend/test_blurred_output/` directory.

## Performance Impact

- **Negligible latency**: Haar Cascade detection is very fast (~10-50ms per frame)
- **No additional dependencies**: Uses OpenCV which is already required
- **Memory efficient**: Processes in-place where possible
- **Scales well**: Multiple faces can be detected and blurred simultaneously

## Compliance

This implementation helps with:
- **GDPR** (General Data Protection Regulation) - minimizes identifiable personal data
- **CCPA** (California Consumer Privacy Act) - reduces PII collection
- **BIPA** (Biometric Information Privacy Act) - anonymizes biometric identifiers

⚠️ **Note**: This is a technical privacy measure and does not constitute legal advice. Consult with legal counsel for compliance requirements in your jurisdiction.

## Troubleshooting

### Faces not being detected

**Symptoms**: Console shows "0 face(s) blurred" but faces are visible

**Possible causes**:
1. Faces are at an angle or in profile
2. Faces are too small in the frame
3. Poor lighting conditions
4. Faces are partially occluded

**Solutions**:
- Adjust camera angle for better frontal face capture
- Increase camera resolution
- Improve lighting
- Consider switching to deep learning face detector

### Blur strength too weak/strong

**Symptoms**: Faces still recognizable or entire image looks distorted

**Solution**:
Adjust blur strength in `backend/scripts/main.py`:

```python
# Weaker blur (more detail, less privacy)
face_blurrer = FaceBlurrer(blur_strength=31)

# Stronger blur (less detail, more privacy)
face_blurrer = FaceBlurrer(blur_strength=71)
```

### Performance issues

**Symptoms**: Detection system slows down after adding face blurring

**Solutions**:
1. Reduce blur strength (smaller kernel = faster)
2. Use `blur_faces_in_region()` to only process person bounding boxes
3. Increase frame skip interval (process every 60 frames instead of 30)

## References

- [OpenCV Haar Cascades Documentation](https://docs.opencv.org/4.x/db/d28/tutorial_cascade_classifier.html)
- [OpenCV Face Detection Tutorial](https://docs.opencv.org/4.x/d2/d99/tutorial_py_face_detection.html)
- [Gaussian Blur in OpenCV](https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html)
