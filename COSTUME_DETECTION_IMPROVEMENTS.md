# Full-Body Costume Detection Improvements

## Problem

YOLO wasn't consistently detecting people wearing full-body costumes (dinosaurs, mascots, etc.) because these costumes don't look like typical "person" shapes that the model was trained on.

**Example**: A person in a T-Rex costume was not being detected while a normally-dressed person next to them was.

## Solution

Implemented a multi-faceted approach to improve detection of people in costumes:

### 1. Lower Confidence Threshold (Primary Fix)

**Before**: `CONFIDENCE_THRESHOLD = 0.7` (70%)
**After**: `CONFIDENCE_THRESHOLD = 0.5` (50%, configurable via env var)

YOLO may detect costume-wearing people with lower confidence scores (0.5-0.6 range) because the shape doesn't perfectly match the "person" class training data.

### 2. Lower YOLO Inference Thresholds

Added two new parameters passed directly to YOLO during inference:

- **`YOLO_CONF_THRESHOLD = 0.3`** (30%): Initial detection threshold
  - Even more permissive than post-filtering threshold
  - Ensures YOLO considers costume-wearing people as candidates

- **`YOLO_IOU_THRESHOLD = 0.4`** (40%, down from default 0.45)
  - IOU = Intersection Over Union
  - Lower value = more permissive for overlapping/partial detections
  - Helps with groups of people in costumes

### 3. Configurable YOLO Model Size

**Before**: Fixed to `yolov8n.pt` (nano - fastest but least accurate)
**After**: Configurable via `YOLO_MODEL` environment variable

Options:
- `yolov8n.pt` (default): ~6MB, fastest, good for regular people
- `yolov8s.pt`: ~22MB, better accuracy for costumes, slight performance impact
- `yolov8m.pt`: ~50MB, best accuracy for difficult cases, slower

Larger models have been trained on more data and handle edge cases (like costumes) better.

## Configuration

All parameters can be tuned via environment variables:

```bash
# Detection thresholds (for post-filtering detected persons)
CONFIDENCE_THRESHOLD=0.5       # Default: 0.5 (was 0.7)

# YOLO inference parameters (passed to model during detection)
YOLO_CONF_THRESHOLD=0.3        # Default: 0.3 (initial detection threshold)
YOLO_IOU_THRESHOLD=0.4         # Default: 0.4 (overlap tolerance)

# Model selection
YOLO_MODEL=yolov8n.pt         # Default: yolov8n.pt (nano)
# YOLO_MODEL=yolov8s.pt       # Alternative: small (better accuracy)
# YOLO_MODEL=yolov8m.pt       # Alternative: medium (best accuracy)
```

### Recommended Settings

**For Halloween/Costume Detection** (current defaults):
```bash
CONFIDENCE_THRESHOLD=0.5
YOLO_CONF_THRESHOLD=0.3
YOLO_IOU_THRESHOLD=0.4
YOLO_MODEL=yolov8n.pt
```

**For Better Accuracy (if detection still misses costumes)**:
```bash
CONFIDENCE_THRESHOLD=0.45
YOLO_CONF_THRESHOLD=0.25
YOLO_IOU_THRESHOLD=0.35
YOLO_MODEL=yolov8s.pt
```

**For Maximum Accuracy (slower, use if needed)**:
```bash
CONFIDENCE_THRESHOLD=0.4
YOLO_CONF_THRESHOLD=0.2
YOLO_IOU_THRESHOLD=0.3
YOLO_MODEL=yolov8m.pt
```

## Trade-offs

### Lower Thresholds
- ✅ **Pro**: Detects more people in costumes
- ⚠️ **Con**: May occasionally detect false positives (furniture, decorations, etc.)
- **Mitigation**: The ROI (Region of Interest) filter and 2-frame consecutive detection requirement help reduce false positives

### Larger Models
- ✅ **Pro**: Better accuracy, especially for unusual shapes
- ⚠️ **Con**: Slower inference, more memory usage
- ⚠️ **Con**: Larger download size (first run)
- **Context**: Running on Raspberry Pi 5 with 8GB RAM, so `yolov8s` should work fine

## Testing

A test script has been created to compare detection with different thresholds:

```bash
# Install dependencies first (if not already installed)
pip install opencv-python ultralytics

# Run test on an image
python backend/tests/test_costume_detection.py /path/to/costume/image.jpg
```

This will:
1. Test with original settings (conf=0.7)
2. Test with costume-optimized settings (conf=0.3, iou=0.4)
3. Save annotated images showing detections
4. Print summary comparison

## Technical Details

### Code Changes

**File**: `/root/repo/backend/scripts/main.py`

**Lines 41-48**: Configurable model loading
```python
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
model = YOLO(YOLO_MODEL)
```

**Lines 72-83**: New detection parameters
```python
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU_THRESHOLD", "0.4"))
YOLO_CONF_THRESHOLD = float(os.getenv("YOLO_CONF_THRESHOLD", "0.3"))
```

**Line 200**: YOLO inference with new parameters
```python
results = model(frame, conf=YOLO_CONF_THRESHOLD, iou=YOLO_IOU_THRESHOLD, verbose=False)
```

### Why Two Confidence Thresholds?

1. **`YOLO_CONF_THRESHOLD`** (0.3): Initial threshold during YOLO inference
   - YOLO only returns detections above this threshold
   - Very permissive to catch costume-wearing people

2. **`CONFIDENCE_THRESHOLD`** (0.5): Post-filtering threshold
   - After YOLO returns detections, we filter them again
   - Provides a second layer of quality control
   - Prevents very low-quality detections from triggering captures

This two-stage approach maximizes recall (finding costumes) while maintaining precision (avoiding false positives).

## Expected Improvement

Based on the T-Rex costume example:
- **Before**: 1 person detected (normally-dressed person only)
- **After**: 2 people detected (both the normally-dressed person AND the dinosaur costume)

The lower thresholds should allow YOLO to detect the dinosaur costume with a confidence score around 0.4-0.6, which would have been filtered out before but is now captured.

## Monitoring

The script will print the detection parameters on startup:

```
🎭 Costume mode: YOLO conf=0.3, IOU=0.4
```

Watch for detection messages showing confidence scores to verify costume detections are being captured.

## Future Improvements

If costume detection is still problematic:

1. **Multi-class detection**: Detect other classes that might represent costumes
   - Class 16: "cat" (for cat costumes)
   - Class 17: "dog" (for dog costumes)
   - Class 21: "cow" (for cow costumes)
   - Class 74: "teddy bear" (for mascot-like costumes)

2. **Fine-tuning**: Train YOLOv8 on a custom dataset of Halloween costumes
   - Collect images of people in various costumes
   - Fine-tune the model to recognize "person in costume" as a variant of "person"

3. **Ensemble approach**: Use multiple detection methods
   - YOLO for standard person detection
   - Segment Anything Model (SAM) for unusual shapes
   - Combine results

4. **Pose estimation**: Use YOLO-Pose to detect human body keypoints
   - Can detect people even when wearing costumes
   - Body structure (head, shoulders, limbs) is still detectable
