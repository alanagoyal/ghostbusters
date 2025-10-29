# Test Images

This directory contains sample Halloween costume images for testing the Baseten costume classification system and multi-person detection.

## Images

### Single Person Images (test-1 through test-5)

1. **test-1.png** - Tiger costume
2. **test-2.png** - Elsa/Frozen princess costume
3. **test-3.png** - Spider-Man costume
4. **test-4.png** - Vampire/Dracula costume
5. **test-5.png** - Additional costume

### Multi-Person Images (test-6 and test-7)

6. **test-6.png** - 3 kids in costumes (pumpkin, tiger, ghost)
7. **test-7.png** - 3 kids in costumes (witch, shark/dinosaur, superhero)

## Image Format

- All images are PNG format
- Dimensions: ~1280x720 to 1920x1080 (captured from doorbell camera)
- No pre-existing bounding boxes (YOLO generates them)
- Show full doorstep scene with people centered

## Usage

### Single Person Detection Test

Run the original test script to process images expecting one person:

```bash
uv run test_costume_detection.py
```

This will:
1. Load each image
2. Classify the costume using Baseten API
3. Upload results to Supabase database
4. Save annotated images to `backend/tests/test_detections/`

### Multi-Person Detection Test

Run the multi-person test script to detect all people in each image:

```bash
uv run test_multiple_people.py
```

This will:
1. Load each image
2. Use YOLOv8n to detect ALL people in the frame
3. Process each detected person separately
4. Classify each person's costume using Baseten API
5. Create separate database entries for each person
6. Upload all detections to Supabase database
7. Save annotated frames with all bounding boxes drawn
8. Save individual person crops to `backend/tests/test_detections/`

## Expected Results

### Single Person Images

The Baseten vision model should identify:
- Tiger: "tiger" or "animal"
- Elsa: "princess"
- Spider-Man: "superhero"
- Vampire: "vampire" or "monster"

### Multi-Person Images

For **test-6.png** (3 people):
- Person 1: "character" (pumpkin costume)
- Person 2: "animal" (tiger costume)
- Person 3: "ghost"

For **test-7.png** (3 people):
- Person 1: "witch"
- Person 2: "animal" or "monster" (shark/dinosaur costume)
- Person 3: "superhero"

All results include:
- **classification**: Short costume type (e.g., "tiger", "princess", "witch")
- **confidence**: 0.0-1.0 score
- **description**: Detailed description (e.g., "child in orange pumpkin costume with jack-o-lantern face")

### Multi-Person Detection Highlights

When running `test_multiple_people.py` on test-6.png and test-7.png:
- **6 total database entries created** (3 per image)
- Each person gets individual costume classification
- Accurate visitor counting (3 + 3 = 6 kids, not just 2 images)
- No data loss when groups arrive together

## Notes

- test-1 through test-5 are from actual doorbell camera detections
- test-6 and test-7 demonstrate multi-person scenarios (groups of trick-or-treaters)
- YOLO runs on each frame to detect people and generate bounding boxes
- In production, the system processes all detected people separately
- Images are used for development and testing only
