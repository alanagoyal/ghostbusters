# Documentation Index

This repository has been thoroughly analyzed. Use this index to navigate the documentation.

## Quick Start for Understanding the System

### For High-Level Overview
1. Start here: **[SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)** - Visual diagrams and file relationships
2. Then: **[CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md)** - Detailed technical breakdown

### For Multiple People Support
1. Read: **[MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md)** - Problem statement and solutions
2. Implement: Follow the implementation roadmap in that document
3. Test: Use the testing section to validate changes

### For Specific Topics

#### Costume Detection
- Current implementation: [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 1
- The problem: YOLOv8n detection works fine, but only highest confidence saved
- Missing feature: Baseten API integration for costume classification

#### Database & Storage
- Schema definition: [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 2
- Migration script: `/root/repo/supabase_migration.sql`
- Python client: `/root/repo/supabase_client.py`

#### Real-Time Dashboard
- Architecture: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- Main component: `/root/repo/dashboard/components/dashboard/dashboard-client.tsx`
- Data flow: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) "Critical Data Flow" section

#### Image Processing
- Current implementation: [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 4
- Privacy measures (incomplete): [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 4.3

---

## Document Summaries

### CODEBASE_ANALYSIS.md
**What it covers:**
- How costume detection is implemented (YOLOv8n locally)
- How detections are saved to database (Supabase)
- Current state of multiple people support (CRITICAL ISSUE IDENTIFIED)
- Database schema details
- Complete code flow from detection to storage
- Current limitations and issues

**Key findings:**
- YOLO detects all people correctly
- BUT only highest confidence person is saved to database
- Costume classification planned but not implemented
- Privacy measures incomplete

**Use this when:** You need technical details about any component

---

### MULTIPLE_PEOPLE_DESIGN.md
**What it covers:**
- Visualization of the current problem
- Comparison of two architectural approaches
- Detailed implementation roadmap
- Code changes needed in Python and TypeScript
- Database migration strategy
- Testing procedures

**Key content:**
- Option A (Recommended): Arrays in single record
- Option B (Alternative): Separate table per person
- Step-by-step implementation guide
- Before/after code snippets
- Migration strategy for backward compatibility

**Use this when:** You're ready to implement multiple people support

---

### SYSTEM_ARCHITECTURE.md
**What it covers:**
- Complete component map (4-layer architecture)
- File relationships and dependencies
- Critical data flow (detection to dashboard)
- Data structures at each layer
- Environment variables required
- Known issues and limitations
- Testing checklist
- Deployment architecture

**Key diagrams:**
- 4-layer system architecture
- Component dependency graph
- Data flow from detection to UI update
- Production deployment architecture

**Use this when:** You need to understand how components fit together

---

### PROJECT_SPEC.md
**What it covers:**
- Original project goals and constraints
- Hardware setup details
- Architecture decisions and trade-offs
- Vision-language model approach for costume classification
- Privacy considerations
- Performance requirements

**Use this when:** You need context about why things are designed a certain way

---

### BLOG_NOTES.md
**What it covers:**
- Implementation journey and decisions
- Why certain technologies were chosen
- Open-ended classification rationale
- Why Baseten was selected for ML inference
- Privacy-first design approach

**Use this when:** You want to understand the design philosophy

---

## Key Files in Codebase

### Core Detection & Storage
- **`detect_people.py`** - Main detection loop
  - Line 40: YOLO model loading
  - Lines 52-83: Frame capture and processing loop
  - Lines 85-116: YOLO inference and visualization
  - Lines 135-152: CRITICAL BUG - only saves highest confidence person
  
- **`supabase_client.py`** - Database operations
  - Lines 39-77: Image upload to storage
  - Lines 79-129: Database insertion
  - Lines 131-177: Complete workflow (save_detection)
  - Lines 202-234: Update costume classification

- **`supabase_migration.sql`** - Database schema
  - Lines 8-18: person_detections table
  - Lines 27-34: Indexes for performance
  - Lines 40-59: Row-level security policies
  - Lines 62-66: Realtime configuration

### Dashboard & Frontend
- **`dashboard/components/dashboard/dashboard-client.tsx`**
  - Lines 32-48: Realtime subscription setup
  - Lines 51-73: Costume statistics calculation
  - Lines 75-89: Activity trend calculation
  
- **`dashboard/components/dashboard/live-feed.tsx`**
  - Shows 5-8 most recent detections
  - Displays costume description if available

- **`dashboard/components/dashboard/costume-distribution.tsx`**
  - Bar chart of top 5 costumes

- **`dashboard/components/dashboard/activity-timeline.tsx`**
  - Line chart of activity over time

### Testing & Configuration
- **`test_supabase_connection.py`** - Complete test suite for backend
- **`test_doorbird_connection.py`** - Camera connectivity test
- **`.env.example`** - Configuration template

---

## Critical Code Locations

### The Multiple People Problem
```
File: /root/repo/detect_people.py
Lines: 135-152
Status: NEEDS FIX
```

The code loops through all detected people but only keeps the one with highest confidence:
```python
first_box = None
max_confidence = 0.0

for result in results:
    boxes = result.boxes
    for box in boxes:
        if int(box.cls[0]) == 0:  # person class
            conf = float(box.conf[0])
            if conf > 0.5 and conf > max_confidence:
                max_confidence = conf
                first_box = {...}  # Only stores ONE box
```

### How to Call save_detection()
```
File: /root/repo/detect_people.py
Lines: 155-164
```

Currently passes single detection:
```python
supabase_client.save_detection(
    image_path=filename,
    timestamp=detection_timestamp,
    confidence=max_confidence,        # Single value
    bounding_box=first_box,          # Single box
)
```

Needs to pass arrays:
```python
supabase_client.save_detection(
    image_path=filename,
    timestamp=detection_timestamp,
    confidences=all_confidences,     # Array
    bounding_boxes=all_boxes,        # Array
)
```

### Database Insertion Code
```
File: /root/repo/supabase_client.py
Methods: insert_detection() lines 79-129
         save_detection() lines 131-177
```

Currently designed for single person. Needs modification to accept arrays.

### Real-Time Subscription
```
File: /root/repo/dashboard/components/dashboard/dashboard-client.tsx
Lines: 32-48
```

Subscribe to new INSERT events and update state.

---

## Implementation Path: Multiple People Support

### Phase 1: Database Migration (1-2 hours)
1. Read: [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Step 1: Database Migration"
2. Run the ALTER TABLE commands in Supabase SQL Editor
3. Keep old columns for backward compatibility

### Phase 2: Update Python Code (1-2 hours)
1. Read: [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Step 2: Update Python Code"
2. Modify `/root/repo/supabase_client.py` - insert_detection() and save_detection() methods
3. Modify `/root/repo/detect_people.py` - lines 135-152 to collect all detections

### Phase 3: Update Dashboard (1-2 hours)
1. Read: [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Step 3: Update Dashboard"
2. Update `/root/repo/dashboard/components/dashboard/dashboard-client.tsx`
3. Update costume stats calculation to handle arrays

### Phase 4: Testing (1-2 hours)
1. Read: [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Testing the Multiple People Flow"
2. Test with simulated detections
3. Test with real DoorBird stream if available

**Total estimated time: 4-8 hours**

---

## Common Questions Answered

### Q: How does person detection work?
A: YOLOv8n (tiny model, ~6MB) runs on Raspberry Pi 5, detects all objects with person class = 0. See [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 1.1

### Q: How are detections saved?
A: Frame is uploaded to Supabase Storage, metadata inserted into person_detections table. See [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 2

### Q: What's the multiple people issue?
A: When 2+ people detected, only the highest confidence person is saved. Others discarded. See [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Current Problem"

### Q: Is costume classification working?
A: No, it's planned but not implemented. Baseten API integration is missing. See [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 1.2

### Q: How does real-time work?
A: Supabase Realtime broadcasts database changes via WebSocket. Dashboard subscribes and updates instantly. See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) "Critical Data Flow"

### Q: What's the recommended approach for multiple people?
A: Option A - Arrays in single record (simpler, better for real-time). See [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) "Recommendation: Option A"

### Q: How do I implement the fix?
A: Follow the 4-phase implementation path in [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) with provided code snippets.

---

## Environment Setup Checklist

### Raspberry Pi
- [ ] DOORBIRD_USERNAME, PASSWORD, IP configured
- [ ] NEXT_PUBLIC_SUPABASE_URL configured
- [ ] SUPABASE_SERVICE_ROLE_KEY configured
- [ ] HOSTNAME or DEVICE_ID set

### Dashboard
- [ ] NEXT_PUBLIC_SUPABASE_URL configured
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY configured
- [ ] npm install in /dashboard directory

See [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) "Environment Variables Required" for full details.

---

## File Organization

```
/root/repo/
├── detect_people.py                    # Main detection loop
├── supabase_client.py                  # Database & storage operations
├── supabase_migration.sql              # Database schema
├── test_doorbird_connection.py         # Camera connectivity test
├── test_supabase_connection.py         # Backend test suite
│
├── dashboard/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx                   # Server-side data fetch
│   ├── components/
│   │   └── dashboard/
│   │       ├── dashboard-client.tsx   # Main real-time component
│   │       ├── live-feed.tsx
│   │       ├── costume-distribution.tsx
│   │       ├── activity-timeline.tsx
│   │       ├── confidence-meter.tsx
│   │       ├── stats-card.tsx
│   │       └── ui/                    # Reusable components
│   └── lib/
│       └── supabase.ts               # Supabase client init
│
├── CODEBASE_ANALYSIS.md               # Technical details (THIS FILE)
├── MULTIPLE_PEOPLE_DESIGN.md          # Implementation guide
├── SYSTEM_ARCHITECTURE.md             # Component relationships
├── DOCUMENTATION_INDEX.md             # This file
├── PROJECT_SPEC.md                    # Original spec
├── BLOG_NOTES.md                      # Design decisions
├── README.md                          # Quick start
├── DOORBIRD_SETUP.md                  # Camera setup
└── SUPABASE_SETUP.md                  # Database setup
```

---

## Next Steps

### If you're just understanding the system:
1. Read [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) (20 min)
2. Read [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) (30 min)
3. Review code locations mentioned above (15 min)

### If you're implementing multiple people support:
1. Read [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) (30 min)
2. Follow Phase 1-4 implementation roadmap (4-8 hours)
3. Test using provided test cases

### If you're fixing other issues:
1. Consult specific section in [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md)
2. Locate relevant files using [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
3. Check test files to understand expected behavior

---

## Support & References

### Original Documentation
- [PROJECT_SPEC.md](PROJECT_SPEC.md) - Complete system specification
- [BLOG_NOTES.md](BLOG_NOTES.md) - Design philosophy and decisions
- [README.md](README.md) - Quick start guide
- [DOORBIRD_SETUP.md](DOORBIRD_SETUP.md) - Camera configuration
- [SUPABASE_SETUP.md](SUPABASE_SETUP.md) - Database setup

### Generated Documentation (This Session)
- [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) - Comprehensive technical analysis
- [MULTIPLE_PEOPLE_DESIGN.md](MULTIPLE_PEOPLE_DESIGN.md) - Implementation design guide
- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) - Component relationships and data flow
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - This file

---

**Generated:** 2025-10-29  
**Current Branch:** terragon/handle-multiple-people-p1otfx  
**Repository:** Halloween Costume Detection System

