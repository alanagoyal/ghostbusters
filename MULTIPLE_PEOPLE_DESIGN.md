# Design Guide: Supporting Multiple People in a Single Frame

## Current Problem: Data Loss

```
SCENARIO: 2 trick-or-treaters approach door together

┌─────────────────────────────────────────────────────────────┐
│ FRAME                                                       │
│                                                             │
│  Person A                          Person B                │
│  (Witch costume)                   (Skeleton costume)      │
│  Position: (100,150) to (300,450)  Position: (350,100) to (500,400)
│  Confidence: 0.95                  Confidence: 0.87        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ YOLO Detection (Works Correctly)│
        │                                 │
        │ Box 1: (100, 150, 300, 450)     │
        │        Confidence: 0.95         │
        │        Class: person            │
        │                                 │
        │ Box 2: (350, 100, 500, 400)     │
        │        Confidence: 0.87         │
        │        Class: person            │
        └─────────────────────────────────┘
                          │
                          ▼
    ┌───────────────────────────────────────┐
    │ Current Code (PROBLEM!)               │
    │                                       │
    │ Loops through all detections...       │
    │ Keeps only highest confidence (0.95)  │
    │                                       │
    │ Result: Person B (0.87) DISCARDED!   │
    └───────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ Database Entry                  │
        │                                 │
        │ id: uuid-12345                  │
        │ timestamp: 2025-10-31 20:42:11  │
        │ device_id: halloween-pi         │
        │ confidence: 0.95                │
        │ bounding_box: {                 │
        │   "x1": 100,                    │
        │   "y1": 150,                    │
        │   "x2": 300,                    │
        │   "y2": 450                     │
        │ }                               │
        │                                 │
        │ MISSING: Person B data!         │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ Dashboard Display               │
        │                                 │
        │ Total Visitors: 1               │
        │ (Should be: 2)                  │
        │                                 │
        │ Recent Detections:              │
        │ - Witch with purple hat (0.95)  │
        │                                 │
        │ MISSING: Skeleton costume!      │
        └─────────────────────────────────┘

IMPACT: Lost data point - skeleton costume never recorded
```

---

## Solution Comparison: Which Approach?

### Option A: Multiple Bounding Boxes in One Record (RECOMMENDED)

**Database Schema:**
```sql
CREATE TABLE person_detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp timestamptz NOT NULL,
  confidence float4 NOT NULL,              -- YOLO confidence (DEPRECATED - use confidences)
  bounding_boxes jsonb[] NOT NULL,         -- Array of bounding boxes
  confidences float4[] NOT NULL,           -- Parallel array of confidences
  person_count int DEFAULT 1,              -- Number of people in frame
  image_url text,
  device_id text NOT NULL,
  costume_classifications text[],          -- Array of costume descriptions (future)
  costume_confidences float4[],            -- Array of costume confidences (future)
  created_at timestamptz DEFAULT now()
);
```

**Example Data:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-31T20:42:11Z",
  "device_id": "halloween-pi",
  "person_count": 2,
  "bounding_boxes": [
    {"x1": 100, "y1": 150, "x2": 300, "y2": 450},
    {"x1": 350, "y1": 100, "x2": 500, "y2": 400}
  ],
  "confidences": [0.95, 0.87],
  "image_url": "https://..../halloween-pi/20251031_204211.jpg",
  "costume_classifications": [
    "witch with purple hat and broom",
    "skeleton with glowing bones"
  ],
  "costume_confidences": [0.92, 0.88]
}
```

**Advantages:**
- Single database record = one moment in time
- Real-time dashboard sees one event with multiple people
- Simpler querying ("show all frames with 2+ people")
- Lower API overhead (1 insert vs. multiple)
- Natural grouping by timestamp

**Disadvantages:**
- PostgreSQL arrays can be harder to query in some cases
- Dashboard needs updates to handle arrays
- Harder to query individual people across all frames
- Costume classification becomes more complex (multiple API calls)

---

### Option B: Separate Table for Each Person (ALTERNATIVE)

**Database Schema:**
```sql
CREATE TABLE person_detections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  timestamp timestamptz NOT NULL,
  device_id text NOT NULL,
  image_url text,
  person_count int DEFAULT 1,
  created_at timestamptz DEFAULT now()
);

CREATE TABLE detected_people (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  detection_id uuid NOT NULL REFERENCES person_detections(id),
  person_index int NOT NULL,             -- 0, 1, 2, etc within detection
  bounding_box jsonb NOT NULL,
  confidence float4 NOT NULL,
  costume_classification text,
  costume_confidence float4,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX idx_detected_people_detection_id ON detected_people(detection_id);
```

**Example Data:**

person_detections table:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-10-31T20:42:11Z",
  "device_id": "halloween-pi",
  "person_count": 2,
  "image_url": "https://..."
}
```

detected_people table (2 rows):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "detection_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_index": 0,
  "bounding_box": {"x1": 100, "y1": 150, "x2": 300, "y2": 450},
  "confidence": 0.95,
  "costume_classification": "witch with purple hat and broom",
  "costume_confidence": 0.92
},
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "detection_id": "550e8400-e29b-41d4-a716-446655440000",
  "person_index": 1,
  "bounding_box": {"x1": 350, "y1": 100, "x2": 500, "y2": 400},
  "confidence": 0.87,
  "costume_classification": "skeleton with glowing bones",
  "costume_confidence": 0.88
}
```

**Advantages:**
- Easier to query individual people
- Can update/edit individual person records
- Better normalized schema
- Easier to add per-person metadata
- Can count unique people across all time

**Disadvantages:**
- Multiple database inserts per detection (more latency)
- Realtime subscription needs to handle related records
- Dashboard needs significant refactoring
- More complex join queries
- Higher storage overhead

---

## Recommendation: Option A (Multiple Bounding Boxes)

**Why?**
1. **Preserves real-time semantics** - One frame = one moment = one database record
2. **Simpler for dashboard** - Subscribe to one row, get all people from that moment
3. **Better performance** - Single write, atomic operation
4. **Matches real-world usage** - "At 8:42pm, 2 kids showed up"
5. **Future-proof** - Can add per-person metadata without schema changes

---

## Implementation Roadmap: Option A

### Step 1: Database Migration (Non-Breaking)

```sql
-- Add new columns alongside existing ones
ALTER TABLE person_detections 
ADD COLUMN bounding_boxes jsonb[] DEFAULT ARRAY[
  (bounding_box)::jsonb  -- Migrate existing data
];

ALTER TABLE person_detections 
ADD COLUMN confidences float4[] DEFAULT ARRAY[confidence];

ALTER TABLE person_detections 
ADD COLUMN person_count int DEFAULT 1;

-- Add placeholder columns for future use
ALTER TABLE person_detections 
ADD COLUMN costume_classifications text[] DEFAULT ARRAY[]::text[];

ALTER TABLE person_detections 
ADD COLUMN costume_confidences float4[] DEFAULT ARRAY[]::float4[];

-- Index the new arrays for performance
CREATE INDEX idx_person_detections_person_count 
ON person_detections(person_count DESC);
```

**Note:** Old `bounding_box` and `confidence` columns can stay for backward compatibility, but new code should use the array versions.

---

### Step 2: Update Python Code

**File: `/root/repo/supabase_client.py`**

```python
def insert_detection(
    self,
    timestamp: datetime,
    confidences: list[float],              # Changed: array
    bounding_boxes: list[dict],            # Changed: array
    image_url: Optional[str] = None,
    costume_classifications: Optional[list[str]] = None,
    costume_confidences: Optional[list[float]] = None,
) -> Optional[dict]:
    """
    Insert person detection record with support for multiple people.
    
    Args:
        timestamp: When people were detected
        confidences: List of YOLO confidence scores
        bounding_boxes: List of dicts with x1, y1, x2, y2 coordinates
        image_url: URL to uploaded image (optional)
        costume_classifications: List of AI costume descriptions (optional)
        costume_confidences: List of AI classification confidences (optional)
    
    Returns:
        Inserted record data, or None if insert fails
    """
    try:
        data = {
            "timestamp": timestamp.isoformat(),
            "confidences": confidences,           # Array
            "bounding_boxes": bounding_boxes,     # Array
            "person_count": len(bounding_boxes),  # Derived field
            "device_id": self.device_id,
        }

        if image_url:
            data["image_url"] = image_url
        if costume_classifications:
            data["costume_classifications"] = costume_classifications
        if costume_confidences:
            data["costume_confidences"] = costume_confidences

        response = (
            self.client.table("person_detections").insert(data).execute()
        )

        if response.data:
            return response.data[0]
        return None

    except Exception as e:
        print(f"Error inserting detection: {e}")
        return None


def save_detection(
    self,
    image_path: str,
    timestamp: datetime,
    confidences: list[float],              # Changed: array
    bounding_boxes: list[dict],            # Changed: array
    costume_classifications: Optional[list[str]] = None,
    costume_confidences: Optional[list[float]] = None,
) -> bool:
    """
    Complete workflow: upload image and insert detection with multiple people.
    """
    # Upload image
    image_url = self.upload_detection_image(image_path, timestamp)

    if not image_url:
        print("Image upload failed, saving detection without image URL")

    # Insert detection record
    result = self.insert_detection(
        timestamp=timestamp,
        confidences=confidences,
        bounding_boxes=bounding_boxes,
        image_url=image_url,
        costume_classifications=costume_classifications,
        costume_confidences=costume_confidences,
    )

    if result:
        print(f"Detection saved to Supabase (ID: {result['id']}, People: {result['person_count']})")
        if image_url:
            print(f"   Image URL: {image_url}")
        return True
    else:
        print("Failed to save detection to Supabase")
        return False
```

**File: `/root/repo/detect_people.py`**

```python
# Get ALL bounding boxes above confidence threshold (Lines 135-152)
all_boxes = []
all_confidences = []

for result in results:
    boxes = result.boxes
    for box in boxes:
        if int(box.cls[0]) == 0:  # person class
            conf = float(box.conf[0])
            if conf > 0.5:  # Only high-confidence detections
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                all_boxes.append({
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                })
                all_confidences.append(conf)

# Sort by confidence (descending)
sorted_detections = sorted(
    zip(all_confidences, all_boxes),
    key=lambda x: x[0],
    reverse=True
)
all_confidences = [conf for conf, _ in sorted_detections]
all_boxes = [box for _, box in sorted_detections]

# Upload to Supabase with ALL detections
if supabase_client and all_boxes:
    try:
        supabase_client.save_detection(
            image_path=filename,
            timestamp=detection_timestamp,
            confidences=all_confidences,        # Changed: array
            bounding_boxes=all_boxes,          # Changed: array
        )
    except Exception as e:
        print(f"Supabase upload failed: {e}")
```

---

### Step 3: Update Dashboard

**File: `/root/repo/dashboard/components/dashboard/dashboard-client.tsx`**

```typescript
interface PersonDetection {
  id: string;
  timestamp: string;
  confidences: number[];              // Changed: array
  bounding_boxes: Array<{x1:number, y1:number, x2:number, y2:number}>;  // Changed: array
  image_url: string | null;
  device_id: string;
  person_count: number;               // NEW
  costume_classifications: string[] | null;
  costume_confidences: number[] | null;
}

export function DashboardClient({ initialDetections }: DashboardClientProps) {
  // Calculate stats - now counting PEOPLE not detections
  const peopleStats = useMemo(() => {
    let totalPeople = 0;
    
    detections.forEach((d) => {
      totalPeople += d.person_count;
    });
    
    return { totalPeople };
  }, [detections]);

  // Update total visitors to count people instead of detections
  <StatsCard
    title="Total Visitors"
    value={peopleStats.totalPeople}        // Count people, not detections
    description="All-time trick-or-treaters"
    ...
  />
}
```

---

### Step 4: Migration Strategy

**Phase 1: Backward Compatibility (Immediate)**
- Add new columns to database
- Keep old columns for reads
- New code writes to both (arrays + old fields)
- Dashboard can read either format

**Phase 2: Update Code (2-3 hours)**
- Update Python code to collect all people
- Update dashboard to use array format
- Test with multiple people in frame

**Phase 3: Cleanup (Optional)**
- Remove old single-person columns once fully tested
- Update data migration script for historical records

---

## Testing the Multiple People Flow

### Test Case 1: Two People in Frame

```python
# Simulated detection
results = [
    {"confidence": 0.95, "bbox": {"x1": 100, "y1": 150, "x2": 300, "y2": 450}},
    {"confidence": 0.87, "bbox": {"x1": 350, "y1": 100, "x2": 500, "y2": 400}},
]

# Expected database record:
{
  "person_count": 2,
  "bounding_boxes": [
    {"x1": 100, "y1": 150, "x2": 300, "y2": 450},
    {"x1": 350, "y1": 100, "x2": 500, "y2": 400}
  ],
  "confidences": [0.95, 0.87],
  "costume_classifications": [
    "witch with purple hat",
    "skeleton with glowing bones"
  ]
}

# Expected dashboard display:
"Total Visitors: 2 (not 1)"
"Recent: witch with purple hat, skeleton with glowing bones"
```

### Test Case 2: Three Low-Confidence Detections

```python
results = [
    {"confidence": 0.6, "bbox": {...}},   # Low confidence, but included
    {"confidence": 0.55, "bbox": {...}},
    {"confidence": 0.48, "bbox": {...}},  # Below 0.5 threshold, excluded
]

# Expected:
{
  "person_count": 2,                      # Only 2 above threshold
  "confidences": [0.6, 0.55],
}
```

---

## Future: Costume Classification at Scale

Once multiple people support is working, adding costume classification becomes easier:

```python
# For each person in frame:
for i, (bbox, confidence) in enumerate(zip(all_boxes, all_confidences)):
    # Crop person from frame
    x1, y1, x2, y2 = bbox["x1"], bbox["y1"], bbox["x2"], bbox["y2"]
    person_crop = frame[y1:y2, x1:x2]
    
    # Send to Baseten API (parallelizable)
    costume_desc = call_baseten_api(person_crop)
    costume_classifications.append(costume_desc["description"])
    costume_confidences.append(costume_desc["confidence"])

# Save all at once
supabase_client.save_detection(
    ...,
    costume_classifications=costume_classifications,
    costume_confidences=costume_confidences,
)
```

This makes the system ready to handle busy Halloween nights where multiple trick-or-treaters appear simultaneously!

---

## Summary

| Aspect | Current | With Multiple Support |
|--------|---------|----------------------|
| **Data Loss** | 50%+ with 2+ people | 0% - all people saved |
| **DB Writes** | 1 per frame | 1 per frame (same) |
| **Dashboard** | 1 person/detection | Multiple people/detection |
| **Complexity** | Simple | Moderate (arrays) |
| **Scalability** | Poor (loses data) | Good (handles crowds) |
| **Real-time Performance** | ~1s | ~1s (no change) |

