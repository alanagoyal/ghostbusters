# MVP Plan: Person Detection with Supabase & Next.js

## Overview

This MVP connects our YOLOv8 person detection system (running on Raspberry Pi) to Supabase for data storage and a Next.js dashboard for real-time visualization.

## Current State

- ✅ YOLOv8n model running on Raspberry Pi
- ✅ RTSP stream from DoorBird camera
- ✅ Person detection with confidence scores
- ✅ Local image saving with bounding boxes

## MVP Goal

**Simple end-to-end flow**: Raspberry Pi detects person → sends to Supabase → dashboard shows "Person detected!" in real-time.

No costume classification in MVP - just person detection to validate the full pipeline works.

## Architecture

```
┌─────────────────┐
│  Raspberry Pi   │
│   + YOLOv8      │
│   + Camera      │
└────────┬────────┘
         │
         │ Person Detected
         │ (image + metadata)
         ▼
┌─────────────────┐
│    Supabase     │
│  - PostgreSQL   │
│  - Storage      │
└────────┬────────┘
         │
         │ Real-time subscription
         ▼
┌─────────────────┐
│  Next.js        │
│  Dashboard      │
└─────────────────┘
```

## Database Schema

### Table: `person_detections`

```sql
create table person_detections (
  id uuid primary key default gen_random_uuid(),
  timestamp timestamptz not null,
  confidence float4 not null,
  bounding_box jsonb not null,  -- {x1, y1, x2, y2}
  image_url text,
  device_id text not null,

  -- Future costume classification fields
  costume_classification text,
  costume_confidence float4,

  created_at timestamptz default now()
);

create index idx_person_detections_timestamp on person_detections(timestamp desc);
create index idx_person_detections_device on person_detections(device_id);
```

**Why this schema?**
- MVP only uses: id, timestamp, confidence, bounding_box, image_url, device_id
- costume_classification fields are nullable and ready for future use
- Indexes optimize dashboard queries (recent detections)

### Storage Bucket: `detection-images`

Path structure: `{device_id}/{timestamp}.jpg`

## Implementation Phases

### Phase 1: Supabase Setup (Follow-up Task)

**See**: Separate follow-up task for detailed instructions

Quick checklist:
- [ ] Create Supabase project
- [ ] Create `person_detections` table
- [ ] Create `detection-images` storage bucket
- [ ] Configure RLS policies
- [ ] Get API keys (URL, anon key, service role key)
- [ ] Test with manual insert

### Phase 2: Raspberry Pi Integration (Main MVP)

**File**: `detect_people.py`

**Changes needed**:
1. Install Supabase client: `pip install supabase`
2. Add Supabase config to `.env`:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=your-service-role-key
   ```
3. Modify detection logic:
   - Upload image to Supabase Storage
   - Insert detection record to database
   - Keep local save as backup
   - Add retry logic for network failures

**Code changes**:
```python
from supabase import create_client

# Initialize Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# When person detected:
# 1. Upload image
image_path = f"{device_id}/{timestamp}.jpg"
with open(local_filename, 'rb') as f:
    supabase.storage.from_('detection-images').upload(image_path, f)

# 2. Get public URL
image_url = supabase.storage.from_('detection-images').get_public_url(image_path)

# 3. Insert detection record
supabase.table('person_detections').insert({
    'timestamp': datetime.now().isoformat(),
    'confidence': confidence,
    'bounding_box': {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2},
    'image_url': image_url,
    'device_id': 'rpi-doorbird-1'
}).execute()

print(f"✅ Sent to Supabase: {timestamp}")
```

### Phase 3: Next.js Dashboard (Follow-up Task)

**See**: Separate follow-up task for detailed instructions

**MVP Features**:
- Show list of recent detections (last 50)
- Display: timestamp, image, confidence %
- Real-time updates when new person detected
- Simple "Person Detected!" notification

**No costume classification UI** - that comes later.

## MVP Success Criteria

1. ✅ Person walks in front of camera
2. ✅ Raspberry Pi detects person (confidence > 0.5)
3. ✅ Detection sent to Supabase (< 2 seconds)
4. ✅ Dashboard updates in real-time
5. ✅ Image visible on dashboard
6. ✅ Can view detection history

## Environment Variables

### Raspberry Pi `.env`
```bash
# DoorBird (existing)
DOORBIRD_USERNAME=
DOORBIRD_PASSWORD=
DOORBIRD_IP=

# Supabase (new)
SUPABASE_URL=
SUPABASE_KEY=  # Service role key for write access
```

### Dashboard `.env.local`
```bash
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=  # Anon key for read access
```

## Testing Plan

### 1. Supabase Connection Test
```python
# Quick test script
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Test insert
result = supabase.table('person_detections').insert({
    'timestamp': '2024-01-01T00:00:00Z',
    'confidence': 0.95,
    'bounding_box': {'x1': 100, 'y1': 100, 'x2': 200, 'y2': 200},
    'device_id': 'test'
}).execute()

print("Test successful!", result)
```

### 2. End-to-End Test
1. Run `detect_people.py` on Raspberry Pi
2. Walk in front of camera
3. Check Raspberry Pi output: "✅ Sent to Supabase"
4. Check Supabase dashboard: new row in table
5. Check Next.js dashboard: detection appears
6. Verify image loads

### 3. Real-time Test
1. Open dashboard
2. Trigger detection
3. Verify dashboard updates without refresh

## Future Enhancements (Post-MVP)

- 🎃 Costume classification (new model)
- 📊 Analytics dashboard
- 🔔 Push notifications
- 🎥 Video clip storage
- 👥 Multiple camera support
- 📱 Mobile app
- 🤖 Training data collection

## File Structure After MVP

```
halloween-costume-detector/
├── detect_people.py           # Modified with Supabase integration
├── dashboard/                 # New Next.js app
│   ├── app/
│   ├── components/
│   └── lib/supabase.ts
├── .env                       # Raspberry Pi config
├── .env.example              # Updated with Supabase vars
├── MVP_PLAN.md               # This file
├── SUPABASE_SETUP.md         # Setup instructions
└── README.md                 # Updated with MVP info
```

## Timeline Estimate

- Supabase setup: 30-60 min
- Raspberry Pi integration: 1-2 hours
- Next.js dashboard: 2-3 hours
- Testing & debugging: 1-2 hours

**Total**: ~5-8 hours for complete MVP

## Next Steps

1. **Complete Supabase setup** (use follow-up task)
2. **Integrate Supabase into detect_people.py** (this repo)
3. **Build Next.js dashboard** (use follow-up task)
4. **Test end-to-end**
5. **Document deployment**

## Questions & Decisions

- **Device ID**: Use `rpi-doorbird-1` or read from .env?
  - Suggestion: Add `DEVICE_ID` to .env for multi-camera future
- **Image storage**: Keep local backup?
  - Suggestion: Yes, for debugging
- **Error handling**: What if Supabase is down?
  - Suggestion: Queue locally, retry every 10 seconds
- **Duplicate detection**: 2-second cooldown sufficient?
  - Suggestion: Keep for MVP, tune later

## Resources

- [Supabase Python Docs](https://supabase.com/docs/reference/python)
- [Supabase JS Docs](https://supabase.com/docs/reference/javascript)
- [Next.js Docs](https://nextjs.org/docs)
- [YOLOv8 Docs](https://docs.ultralytics.com)
