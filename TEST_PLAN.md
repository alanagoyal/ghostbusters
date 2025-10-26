# Costume Classification Testing Plan

Comprehensive testing strategy for the costume classification system.

## Test Objectives

1. Validate costume description quality and accuracy
2. Measure latency and throughput
3. Estimate costs for Halloween night
4. Identify edge cases and failure modes
5. Optimize prompts and parameters

## Test Setup

### Prerequisites

- ✅ Baseten account created
- ✅ Llama 3.2 11B Vision Instruct deployed
- ✅ API credentials configured in `.env`
- ✅ Dependencies installed (`uv sync`)

### Test Data Collection

Create a diverse test set representing real Halloween scenarios:

**Test Categories:**

1. **Simple Costumes** (10 images)
   - Single-color costumes
   - Classic costumes (ghost, witch, vampire)
   - Store-bought full outfits

2. **Complex Costumes** (10 images)
   - Multi-piece costumes
   - Props and accessories
   - Group costumes
   - DIY/homemade costumes

3. **Edge Cases** (10 images)
   - Kids in regular clothes (not costume)
   - Partial costumes (just mask or hat)
   - Face paint only
   - Multiple people in frame
   - Low light conditions
   - Motion blur

4. **Challenge Cases** (10 images)
   - Inflatable costumes
   - Character costumes (specific superheroes, movie characters)
   - Abstract/creative costumes
   - Pets in costumes
   - Baby/toddler costumes

**Total Test Set:** 40 images

### Test Data Sources

1. **Public datasets:**
   - Google Images (labeled for reuse)
   - Flickr Creative Commons
   - Unsplash

2. **Synthetic data:**
   - Generate test images with DALL-E or Stable Diffusion
   - Ensure diverse backgrounds and lighting

3. **Real DoorBird frames:**
   - Capture test frames from actual camera
   - Simulate Halloween night conditions

## Test Scenarios

### Test 1: Basic Functionality

**Objective:** Verify the API client works correctly

**Steps:**
1. Run `costume_classifier.py` with a simple costume image
2. Verify successful response
3. Check description quality
4. Validate response format

**Success Criteria:**
- ✅ No errors or exceptions
- ✅ Response contains `success: True`
- ✅ Description is coherent and relevant
- ✅ Latency < 5 seconds

**Test Command:**
```bash
uv run python costume_classifier.py test_images/witch_costume.jpg
```

**Expected Output:**
```
Costume Description: witch with black hat and broom
Latency: 2.34 seconds
Tokens: 123 in, 8 out
```

### Test 2: Description Quality

**Objective:** Evaluate accuracy and specificity of costume descriptions

**Method:**
1. Process all 40 test images
2. Compare AI descriptions to ground truth labels
3. Rate quality on 1-5 scale:
   - 1 = Completely wrong
   - 2 = Partially correct
   - 3 = Correct but generic
   - 4 = Correct and specific
   - 5 = Excellent, detailed, accurate

**Test Script:**
```python
import json
from costume_classifier import CostumeClassifier
from pathlib import Path

classifier = CostumeClassifier()
results = []

test_images = Path("test_images").glob("*.jpg")

for img_path in test_images:
    result = classifier.classify_from_file(str(img_path))

    results.append({
        "image": img_path.name,
        "description": result.get("description", ""),
        "success": result["success"],
        "latency": result.get("latency", 0),
        "error": result.get("error", "")
    })

    print(f"{img_path.name}: {result.get('description', 'ERROR')}")

# Save results
with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)

# Calculate stats
successful = sum(1 for r in results if r["success"])
avg_latency = sum(r["latency"] for r in results if r["success"]) / successful

print(f"\nSuccess rate: {successful}/{len(results)} ({100*successful/len(results):.1f}%)")
print(f"Average latency: {avg_latency:.2f} seconds")
```

**Success Criteria:**
- ✅ Success rate > 95%
- ✅ Average quality score > 3.5/5
- ✅ At least 80% score 4+

### Test 3: Parameter Optimization

**Objective:** Find optimal temperature and max_tokens settings

**Test Matrix:**

| Temperature | Max Tokens | Expected Behavior |
|------------|-----------|------------------|
| 0.0 | 20 | Very short, deterministic |
| 0.0 | 50 | Deterministic, concise |
| 0.3 | 50 | **Balanced (recommended)** |
| 0.5 | 50 | Slightly more creative |
| 0.7 | 50 | More creative, less consistent |
| 0.3 | 100 | Longer descriptions |

**Test Script:**
```python
from costume_classifier import CostumeClassifier

classifier = CostumeClassifier()
test_image = "test_images/witch_costume.jpg"

configs = [
    (0.0, 20),
    (0.0, 50),
    (0.3, 50),
    (0.5, 50),
    (0.7, 50),
    (0.3, 100),
]

print("Temperature | Max Tokens | Description | Tokens Out | Latency")
print("-" * 80)

for temp, max_tok in configs:
    result = classifier.classify_from_file(
        test_image,
        temperature=temp,
        max_tokens=max_tok
    )

    if result["success"]:
        desc = result["description"][:50] + "..." if len(result["description"]) > 50 else result["description"]
        tokens = result.get("usage", {}).get("output_tokens", 0)
        latency = result["latency"]

        print(f"{temp:6.1f}      | {max_tok:10d} | {desc:50s} | {tokens:10d} | {latency:6.2f}s")
```

**Success Criteria:**
- ✅ Identify optimal temperature for consistency
- ✅ Identify optimal max_tokens for speed/quality balance

### Test 4: Prompt Engineering

**Objective:** Optimize prompt for best costume descriptions

**Prompts to Test:**

**Prompt A (Current):**
```
Describe this person's Halloween costume in one short phrase (5-10 words maximum).
Focus only on the costume, not the background.
```

**Prompt B (More Examples):**
```
Describe this Halloween costume in 5-10 words. Focus only on the costume.

Examples:
- "witch with purple hat and broom"
- "inflatable dinosaur costume"
- "Spider-Man with web shooters"
- "pirate with eyepatch and sword"

Now describe this costume:
```

**Prompt C (Structured):**
```
Identify the Halloween costume in this image.

Format: [character/type] in/with [key features]
Examples:
- "witch in black dress with pointed hat"
- "superhero with red cape and mask"

Describe the costume:
```

**Prompt D (Minimal):**
```
What Halloween costume is this person wearing? Describe in 5-10 words.
```

**Test Script:**
```python
prompts = {
    "A": "...",  # current
    "B": "...",  # more examples
    "C": "...",  # structured
    "D": "...",  # minimal
}

for name, prompt in prompts.items():
    result = classifier.classify_from_file(
        test_image,
        custom_prompt=prompt,
        temperature=0.3
    )
    print(f"Prompt {name}: {result.get('description', 'ERROR')}")
```

**Success Criteria:**
- ✅ Identify prompt that produces most consistent, specific descriptions
- ✅ Compare across different costume types

### Test 5: Latency and Throughput

**Objective:** Measure performance under load

**Test Cases:**

1. **Single Inference Latency**
   - Measure cold start (first request after idle)
   - Measure warm inference (subsequent requests)
   - Compare to Baseten's advertised latency

2. **Sequential Processing**
   - Process 10 images sequentially
   - Measure total time and average per image

3. **Concurrent Processing** (if applicable)
   - Process multiple images in parallel
   - Measure throughput (images/minute)

**Test Script:**
```python
import time
from costume_classifier import CostumeClassifier

classifier = CostumeClassifier()
test_images = list(Path("test_images").glob("*.jpg"))[:10]

# Cold start
print("Testing cold start...")
start = time.time()
result = classifier.classify_from_file(str(test_images[0]))
cold_start_time = time.time() - start
print(f"Cold start: {cold_start_time:.2f}s")

# Warm inferences
print("\nTesting warm inferences...")
latencies = []
for img_path in test_images[1:]:
    result = classifier.classify_from_file(str(img_path))
    if result["success"]:
        latencies.append(result["latency"])

avg_latency = sum(latencies) / len(latencies)
print(f"Average warm latency: {avg_latency:.2f}s")
print(f"Min: {min(latencies):.2f}s, Max: {max(latencies):.2f}s")

# Throughput
total_time = sum(latencies)
throughput = len(latencies) / (total_time / 60)  # images per minute
print(f"\nThroughput: {throughput:.1f} images/minute")
```

**Success Criteria:**
- ✅ Cold start < 10 seconds
- ✅ Warm inference < 3 seconds
- ✅ Throughput > 20 images/minute

### Test 6: Cost Estimation

**Objective:** Validate cost estimates for Halloween night

**Calculation:**
```python
import time
from costume_classifier import CostumeClassifier

classifier = CostumeClassifier()

# Measure average inference time
num_tests = 20
total_time = 0

for i in range(num_tests):
    result = classifier.classify_from_file("test_images/sample.jpg")
    if result["success"]:
        total_time += result["latency"]

avg_inference_time = total_time / num_tests

# Cost calculation
gpu_cost_per_hour = 9.984  # A100 pricing
scenarios = [50, 100, 150, 200]  # number of trick-or-treaters

print(f"Average inference time: {avg_inference_time:.2f}s\n")
print("Halloween Night Cost Estimates:")
print("=" * 60)

for num_inferences in scenarios:
    total_seconds = num_inferences * avg_inference_time
    total_hours = total_seconds / 3600
    cost = total_hours * gpu_cost_per_hour

    print(f"{num_inferences:3d} trick-or-treaters:")
    print(f"  Total time: {total_seconds:6.1f}s ({total_seconds/60:.1f} min)")
    print(f"  Cost: ${cost:.2f}")
    print()
```

**Success Criteria:**
- ✅ Cost for 150 inferences < $2
- ✅ Total processing time < 10 minutes

### Test 7: Error Handling

**Objective:** Validate graceful error handling

**Test Cases:**

1. **Invalid API Key**
   ```python
   classifier = CostumeClassifier(api_key="invalid")
   result = classifier.classify_from_file("test.jpg")
   assert not result["success"]
   assert "401" in result["error"]
   ```

2. **Invalid Image File**
   ```python
   result = classifier.classify_from_file("nonexistent.jpg")
   assert not result["success"]
   assert "Failed to load" in result["error"]
   ```

3. **Network Timeout**
   ```python
   classifier = CostumeClassifier(timeout=0.1)  # Very short timeout
   result = classifier.classify_from_file("test.jpg")
   # May timeout or succeed depending on network
   ```

4. **Corrupted Image**
   ```python
   # Create corrupted image file
   with open("corrupted.jpg", "wb") as f:
       f.write(b"not an image")

   result = classifier.classify_from_file("corrupted.jpg")
   assert not result["success"]
   ```

**Success Criteria:**
- ✅ All error cases return `success: False`
- ✅ All error cases include descriptive error messages
- ✅ No unhandled exceptions

### Test 8: Integration Test (YOLO → Classifier)

**Objective:** Test integration with YOLO person detection

**Prerequisites:**
- YOLO model deployed
- Sample DoorBird video frame

**Test Script:**
```python
import cv2
from costume_classifier import CostumeClassifier

# This will be actual integration code later
classifier = CostumeClassifier()

# Load test frame
frame = cv2.imread("doorbird_frame.jpg")

# Simulate YOLO detection (replace with actual YOLO later)
# Assuming YOLO returns bounding boxes: (x1, y1, x2, y2)
mock_detections = [
    (100, 50, 300, 400),  # Person 1
    (350, 60, 500, 420),  # Person 2
]

for i, (x1, y1, x2, y2) in enumerate(mock_detections):
    # Crop person from frame
    person_crop = frame[y1:y2, x1:x2]

    # Classify costume
    result = classifier.classify_from_array(person_crop)

    if result["success"]:
        print(f"Person {i+1}: {result['description']}")
    else:
        print(f"Person {i+1}: Error - {result['error']}")
```

**Success Criteria:**
- ✅ Successfully processes YOLO-cropped images
- ✅ Handles multiple people in same frame
- ✅ Preserves image quality through pipeline

## Test Deliverables

After completing all tests, produce:

1. **Test Results Report** (`TEST_RESULTS.md`)
   - Summary of all test outcomes
   - Quality scores for test images
   - Optimal parameters identified
   - Performance metrics

2. **Test Images Archive** (`test_images/`)
   - Organized test dataset
   - Ground truth labels
   - Results annotations

3. **Cost Analysis** (`COST_ANALYSIS.md`)
   - Actual measured costs
   - Halloween night projections
   - Recommendations for cost optimization

4. **Recommendations Document**
   - Optimal configuration settings
   - Prompt to use in production
   - Known limitations and workarounds

## Next Steps After Testing

1. ✅ All tests pass with acceptable quality
2. ✅ Costs validated within budget
3. ✅ Optimal parameters identified
4. Integrate with YOLO detection
5. Connect to Supabase
6. Build main detection pipeline
7. Create monitoring dashboard

## Notes

- Save all test results for documentation
- Take screenshots of Baseten dashboard during testing
- Document any unexpected behaviors or edge cases
- Keep test dataset for future model comparisons
