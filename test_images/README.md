# Test Images

This directory contains sample Halloween costume images for testing the Baseten costume classification system.

## Images

The test images include:

1. **image-BVH1NL6gKJp8QQ3kW_9e1.png** - Tiger costume
2. **image-qORO3FwW7UYsD2iSDwVnA.png** - Elsa/Frozen princess costume
3. **image-2A26rvEwWK0QWW_i8WpIM.png** - Spider-Man costume
4. **image-zphDYn4_koLqtVOSssAT7.png** - Vampire/Dracula costume

## Image Format

- All images are PNG format
- Dimensions: ~1280x720 (captured from doorbell camera)
- Already include YOLO detection bounding boxes (green rectangles)
- Show full doorstep scene with person centered

## Usage

Run the test script to process all images:

```bash
uv run python test_costume_detection.py
```

This will:
1. Load each image
2. Classify the costume using Baseten API
3. Upload results to Supabase database
4. Save annotated images to `test_detections/`

## Expected Results

The Baseten vision model should identify:
- Tiger: "tiger" or "tiger costume"
- Elsa: "Elsa", "Frozen princess", or "princess"
- Spider-Man: "Spider-Man" or "superhero"
- Vampire: "vampire", "Dracula", or "vampire costume"

Results will include:
- **classification**: Short costume type (e.g., "tiger", "princess")
- **confidence**: 0.0-1.0 score
- **description**: Detailed description (e.g., "tiger costume with orange and black stripes")

## Notes

- These images are from actual doorbell camera detections
- Person bounding boxes are pre-computed for testing
- In production, YOLO runs on each frame to detect people and extract bounding boxes
- Images are used for development and testing only
