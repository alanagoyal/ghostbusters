# Test Images

This directory contains sample Halloween costume images for testing the Baseten costume classification system and multi-person detection.

## Images

### Single Person Images (prefix: `test-single-`)

Images containing one person for single-person detection testing:

- Example: `test-single-1.png`, `test-single-2.png`, etc.
- These images should feature one person in a Halloween costume
- Used to test basic costume classification

### Multi-Person Images (prefix: `test-multiple-`)

Images containing multiple people for multi-person detection testing:

- Example: `test-multiple-1.png`, `test-multiple-2.png`, etc.
- These images should feature 2 or more people in Halloween costumes
- Used to test YOLO detection and separate classification for each person

## Image Format

- All images are PNG format
- Dimensions: ~1280x720 to 1920x1080 (captured from doorbell camera)
- No pre-existing bounding boxes (YOLO generates them)
- Show full doorstep scene with people centered

## Usage

### Single Person Detection Test

Run the original test script to process all images with `test-single-` prefix:

```bash
uv run test_costume_detection.py
```

This will:
1. Load all images matching `test-single-*` pattern
2. Classify the costume using Baseten API
3. Upload results to Supabase database
4. Save annotated images to `backend/tests/test_detections/`

### Multi-Person Detection Test

Run the multi-person test script to detect all people in each image with `test-multiple-` prefix:

```bash
uv run test_multiple_people.py
```

This will:
1. Load all images matching `test-multiple-*` pattern
2. Use YOLOv8n to detect ALL people in the frame
3. Process each detected person separately
4. Classify each person's costume using Baseten API
5. Create separate database entries for each person
6. Upload all detections to Supabase database
7. Save annotated frames with all bounding boxes drawn
8. Save individual person crops to `backend/tests/test_detections/`

## Expected Results

### Single Person Images

The Baseten vision model should identify common costume types such as:
- Animals: "tiger", "cat", "dog", etc.
- Characters: "princess", "superhero", "witch", etc.
- Creatures: "vampire", "ghost", "monster", etc.

### Multi-Person Images

When multiple people are detected in an image:
- Each person gets a separate detection and classification
- YOLO confidence scores for person detection
- Individual costume classifications for each person
- Separate database entries for accurate counting

All results include:
- **classification**: Short costume type (e.g., "tiger", "princess", "witch")
- **confidence**: 0.0-1.0 score
- **description**: Detailed description (e.g., "child in orange pumpkin costume with jack-o-lantern face")

### Multi-Person Detection Highlights

When running `test_multiple_people.py`:
- **One database entry per person** (not per image)
- Each person gets individual costume classification
- Accurate visitor counting (groups counted separately)
- No data loss when groups arrive together

## Notes

- Images with `test-single-` prefix are for single-person detection testing
- Images with `test-multiple-` prefix demonstrate multi-person scenarios (groups of trick-or-treaters)
- YOLO runs on each frame to detect people and generate bounding boxes
- In production, the system processes all detected people separately
- Images are used for development and testing only
- Add new test images following the naming convention: `test-single-*.png` or `test-multiple-*.png`
