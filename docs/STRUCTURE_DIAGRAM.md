# Visual Structure Diagrams

## Complete System Architecture

```
                        HALLOWEEN COSTUME CLASSIFIER
                         (Complete Data Flow)

┌─────────────────────────────────────────────────────────────────────────┐
│                    EDGE COMPUTE (Raspberry Pi 5)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────┐         ┌──────────────────────────────────┐  │
│  │  DoorBird Camera     │  RTSP   │    detect_people.py (176 LOC)    │  │
│  │  (RTSP Stream)       │◄────────│  - OpenCV video capture          │  │
│  │                      │         │  - YOLOv8n person detection      │  │
│  └──────────────────────┘         │  - Frame saving & storage        │  │
│                                   └──────────────────────────────────┘  │
│                                            │                             │
│                                   Detections Found                      │
│                                            │                             │
│                                            ▼                             │
│                          ┌──────────────────────────────┐               │
│                          │  supabase_client.py (269 LOC)│               │
│                          │  - Image upload to Storage   │               │
│                          │  - Record insertion to DB    │               │
│                          │  - Query operations          │               │
│                          │  - Costume classification    │               │
│                          │    updates                   │               │
│                          └──────────────────────────────┘               │
│                                            │                             │
│                                   HTTPS POST                            │
│                                            ▼                             │
└─────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │
                        ┌───────────────────┴───────────────────┐
                        │                                       │
                        ▼                                       ▼
        ┌─────────────────────────────────────────────────────────────┐
        │                  SUPABASE (Cloud Backend)                    │
        ├─────────────────────────────────────────────────────────────┤
        │                                                               │
        │  ┌───────────────────┐    ┌──────────────────────────────┐  │
        │  │  PostgreSQL DB    │    │  Supabase Storage            │  │
        │  ├───────────────────┤    ├──────────────────────────────┤  │
        │  │ person_detections │    │ detection-images/            │  │
        │  │ ├─ id             │    │ └─ device_id/                │  │
        │  │ ├─ timestamp      │    │    └─ YYYYMMDD_HHMMSS.jpg   │  │
        │  │ ├─ confidence     │    │                              │  │
        │  │ ├─ bounding_box   │    │ Public URLs available        │  │
        │  │ ├─ device_id      │    │                              │  │
        │  │ ├─ image_url      │    └──────────────────────────────┘  │
        │  │ ├─ costume_*      │                                       │
        │  │ └─ costume_conf   │    ┌──────────────────────────────┐  │
        │  └───────────────────┘    │  Supabase Realtime           │  │
        │                            │  (WebSocket Channel)          │  │
        │                            │  person_detections (INSERT)  │  │
        │                            └──────────────────────────────┘  │
        │                                       │                      │
        │                                 Realtime Events             │
        │                                       │                      │
        └───────────────────────────────────────┼──────────────────────┘
                                                │
                                   WebSocket Connection
                                                │
        ┌───────────────────────────────────────┴──────────────────────┐
        │                                                                │
        ▼                                                                │
┌──────────────────────────────────────────────────────────────────────┐│
│               FRONTEND (Next.js Dashboard on Vercel)                 ││
├──────────────────────────────────────────────────────────────────────┤│
│                                                                       ││
│  ┌──────────────────────────────────────────────────────────────┐  ││
│  │              app/page.tsx (134 LOC)                          │  ││
│  │  ┌────────────────────────────────────────────────────────┐ │  ││
│  │  │ 1. On Mount: Fetch initial detections                │ │  ││
│  │  │    - Query last 50 from person_detections table      │ │  ││
│  │  │    - Render list                                      │ │  ││
│  │  │                                                        │ │  ││
│  │  │ 2. Subscribe to Realtime                             │ │  ││
│  │  │    - channel: 'person_detections'                     │ │  ││
│  │  │    - event: INSERT                                    │ │  ││
│  │  │    - callback: prepend to list                        │ │  ││
│  │  │                                                        │ │  ││
│  │  │ 3. Display                                            │ │  ││
│  │  │    - Detection list with timestamps                  │ │  ││
│  │  │    - Confidence scores                                │ │  ││
│  │  │    - Costume classifications (if available)          │ │  ││
│  │  │    - Error handling & loading states                 │ │  ││
│  │  └────────────────────────────────────────────────────────┘ │  ││
│  └──────────────────────────────────────────────────────────────┘  ││
│                             │                                        ││
│                    lib/supabase.ts (12 LOC)                          ││
│                  [Supabase client initialization]                    ││
│                                                                       ││
│  ┌──────────────────────────────────────────────────────────────┐  ││
│  │  Styling: Tailwind CSS v4 (app/globals.css)                │  ││
│  │  Layout: app/layout.tsx (20 LOC)                            │  ││
│  └──────────────────────────────────────────────────────────────┘  ││
│                                                                       ││
└──────────────────────────────────────────────────────────────────────┘│
                                                                         │
 ════════════════════════════════════════════════════════════════════════
```

---

## Project Structure by Size

```
REPOSITORY (28 files, 1,047+ lines of code)

                       Documentation (7 files)
                              ▲
                              │
                      ┌───────┴────────┐
                      │                │
                    34 KB           5-6 KB each
                  (BLOG_NOTES)      (Setup Guides)
                      │
                 ┌────┴─────┐
                 │           │
            PROJECT_SPEC   README
             (12 KB)        (5 KB)

                  Code (7 files total)
                       ▲
                       │
        ┌──────────────┴──────────────┐
        │                             │
    Python (881 LOC)            React/TS (166 LOC)
    [4 files]                    [3 files]
        │                             │
    ┌───┴────────────┐           ┌────┴─────────┐
    │                │           │               │
 Backend Lib      Tests       Frontend       React Hook
    │                │           │
┌───┴──────┐    ┌───┴──────┐ page.tsx     useEffect
│           │    │           │ (134 LOC)    useState
269 LOC    176  355 LOC  81 LOC
│           │
SupabaseC  Detect
Client     People

             Configuration (8 files)
                    ▲
                    │
        ┌───────────┼───────────┐
        │           │           │
      .env        Python      Node
    examples      config      config
    (2 files)   pyproject   package.json
                 .toml      tsconfig.json
                           next.config.js
                           tailwind.config
                           postcss.config

           Infrastructure Files
                    ▲
                    │
            ┌───────┴──────┐
            │              │
        Database        .gitignore
      (SQL Schema)
       supabase_
       migration.sql
```

---

## File Organization: Current vs. Recommended

### CURRENT (Flat)
```
/root/repo/
├── README.md
├── PROJECT_SPEC.md
├── BLOG_NOTES.md
├── DOORBIRD_SETUP.md
├── SUPABASE_SETUP.md
│
├── detect_people.py              ← ⚠️ Root level
├── supabase_client.py            ← ⚠️ Root level
├── test_doorbird_connection.py   ← ⚠️ Root level
├── test_supabase_connection.py   ← ⚠️ Root level
│
├── pyproject.toml
├── .env.example                  ← ⚠️ Duplicate with dashboard
├── supabase_migration.sql
│
└── dashboard/
    ├── .env.example              ← ⚠️ Duplicate
    ├── README.md
    ├── SETUP.md
    ├── package.json
    ├── next.config.js
    ├── app/
    │   ├── page.tsx
    │   ├── layout.tsx
    │   └── globals.css
    └── lib/
        └── supabase.ts
```

### RECOMMENDED (Organized)
```
/root/repo/
├── docs/                         ← ✅ NEW: Organized documentation
│   ├── README.md                    (Start here)
│   ├── architecture.md
│   ├── setup/
│   │   ├── doorbird.md
│   │   ├── supabase.md
│   │   ├── backend.md
│   │   └── frontend.md
│   ├── development/
│   │   ├── setup.md
│   │   └── testing.md
│   └── blog/
│       └── implementation-notes.md  (former BLOG_NOTES.md)
│
├── backend/                      ← ✅ NEW: Python package
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── detection/
│   │   │   ├── __init__.py
│   │   │   ├── person_detector.py   (former detect_people.py)
│   │   │   └── models.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── supabase_client.py   (former supabase_client.py)
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── constants.py
│   ├── tests/                       ← ✅ Organized tests
│   │   ├── __init__.py
│   │   ├── test_detection.py        (former test_doorbird_connection.py)
│   │   ├── test_supabase.py         (former test_supabase_connection.py)
│   │   └── conftest.py
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
│
├── dashboard/                    ← ✅ Keep as is (well-organized)
│   ├── src/                         (optional refactoring)
│   │   ├── components/
│   │   │   ├── DetectionList.tsx    ← ✅ Split from page.tsx
│   │   │   ├── DetectionCard.tsx
│   │   │   ├── LoadingState.tsx
│   │   │   └── ErrorState.tsx
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx             (refactored to use components)
│   │   │   └── globals.css
│   │   └── lib/
│   │       ├── supabase.ts
│   │       └── types.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── .env.example
│
├── .github/                      ← ✅ NEW: CI/CD
│   └── workflows/
│       ├── test-backend.yml
│       ├── test-frontend.yml
│       └── lint.yml
│
├── .env.example                  ← ✅ CONSOLIDATED: Single file with comments
├── .gitignore                    ← ✅ Keep
├── README.md                     ← ✅ Keep (main overview only)
└── docker-compose.yml            ← ✅ NEW: Local development
```

---

## Dependency Tree

```
Person Detection System Dependencies

┌─────────────────────────────────────────────┐
│         detect_people.py (176 LOC)          │
│  ┌───────────────────────────────────────┐  │
│  │  Imports:                             │  │
│  │  ├─ os, time, datetime (stdlib)      │  │
│  │  ├─ cv2 (OpenCV)                     │  │
│  │  ├─ dotenv                           │  │
│  │  ├─ ultralytics (YOLOv8)             │  │
│  │  └─ supabase_client                  │  │ ◄─── Main dependency
│  └───────────────────────────────────────┘  │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│      supabase_client.py (269 LOC)           │
│  ┌───────────────────────────────────────┐  │
│  │  Imports:                             │  │
│  │  ├─ os, datetime, pathlib (stdlib)   │  │
│  │  ├─ dotenv                           │  │
│  │  ├─ supabase (Client, create_client) │  │ ◄─── External SDK
│  │  └─ typing (Optional, dict, etc)    │  │
│  └───────────────────────────────────────┘  │
│                                              │
│  Exports:                                    │
│  ├─ SupabaseClient class                    │
│  │  ├─ upload_detection_image()             │
│  │  ├─ insert_detection()                   │
│  │  ├─ save_detection()                     │
│  │  ├─ get_recent_detections()              │
│  │  └─ update_costume_classification()      │
│  └─                                          │
└─────────────────────────────────────────────┘

Frontend Dependencies
┌──────────────────────────────────────────────┐
│        dashboard/app/page.tsx                │
│  ┌────────────────────────────────────────┐  │
│  │  Imports:                              │  │
│  │  ├─ React (useEffect, useState)        │  │
│  │  └─ lib/supabase (supabase client)     │  │ ◄─ Main dependency
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│        dashboard/lib/supabase.ts             │
│  ┌────────────────────────────────────────┐  │
│  │  Imports:                              │  │
│  │  └─ @supabase/supabase-js              │  │ ◄─ External SDK
│  │     (createClient)                     │  │
│  │                                        │  │
│  │  Exports:                              │  │
│  │  └─ supabase (initialized client)      │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘

External Service Dependencies
┌────────────────────────────────────┐
│  DoorBird Camera (RTSP stream)     │
│  ← Consumed by detect_people.py    │
└────────────────────────────────────┘

┌────────────────────────────────────┐
│  Supabase                          │
│  ├─ PostgreSQL Database            │
│  ├─ Storage (S3-like)              │
│  ├─ Realtime (WebSocket)           │
│  ├─ Auth (future)                  │
│  ← Used by supabase_client.py      │
│  ← Used by dashboard/app/page.tsx  │
└────────────────────────────────────┘
```

---

## Data Model Relationships

```
PERSON DETECTION RECORD
┌─────────────────────────────────────┐
│      person_detections              │
│  ┌─────────────────────────────────┐│
│  │ id: UUID (Primary Key)          ││
│  │ timestamp: timestamptz          ││
│  │ confidence: numeric (0.0-1.0)   ││
│  │ bounding_box: JSON              ││
│  │   ├─ x1: int                    ││
│  │   ├─ y1: int                    ││
│  │   ├─ x2: int                    ││
│  │   └─ y2: int                    ││
│  │ device_id: text                 ││ ◄── Future: Foreign key to devices table
│  │ image_url: text (optional)      ││────┐
│  │ costume_classification: text    ││    │
│  │ costume_confidence: numeric     ││    │
│  └─────────────────────────────────┘│    │
│                                     │    │
│  Indexes:                           │    │
│  ├─ UNIQUE: id                      │    │
│  ├─ INDEX: timestamp DESC           │    │
│  ├─ INDEX: device_id                │    │
│  └─ INDEX: created_at               │    │
│                                     │    │
│  RLS Policies:                      │    │
│  ├─ SELECT: anyone (public)         │    │
│  └─ INSERT: service_role only       │    │
└─────────────────────────────────────┘    │
                                            │
         Linked to Storage Bucket           │
         ┌────────────────────────────────┐ │
         │  detection-images bucket       │ │
         ├────────────────────────────────┤ │
         │ Path: {device_id}/{TIMESTAMP}  │◄┘
         │.jpg                             │
         │                                │
         │ Public URLs available          │
         └────────────────────────────────┘
```

---

## Deployment Architecture

```
DEVELOPMENT (Local Machine)
┌──────────────────────────────────────────────┐
│                                              │
│  Backend Development                        │
│  ├─ uv sync (install dependencies)         │
│  ├─ uv run python detect_people.py          │
│  ├─ uv run python test_*.py                 │
│  └─ .env file (local credentials)           │
│                                              │
│  Frontend Development                       │
│  ├─ npm install (in dashboard/)            │
│  ├─ npm run dev                             │
│  ├─ localhost:3000 (dev server)             │
│  └─ .env.local file (dev API keys)         │
│                                              │
│  Supabase (cloud staging)                   │
│  └─ Uses staging project for testing        │
│                                              │
└──────────────────────────────────────────────┘

PRODUCTION (Deployment)
┌──────────────────────────────────────────────┐
│                                              │
│  Raspberry Pi (Edge)                         │
│  ├─ SSH access (headless)                    │
│  ├─ Python 3.10+ with dependencies          │
│  ├─ detect_people.py running as service     │
│  │  (future: systemd service file)          │
│  ├─ .env file (production credentials)     │
│  └─ Local detection & frame storage         │
│                                              │
│  Supabase (Cloud)                           │
│  ├─ PostgreSQL Database                     │
│  ├─ Storage (detection images)              │
│  ├─ Realtime (WebSocket)                    │
│  └─ Production API keys                     │
│                                              │
│  Vercel (Dashboard)                         │
│  ├─ Next.js app deployment                  │
│  ├─ Auto-deployment on GitHub push          │
│  ├─ Environment variables configured        │
│  ├─ https://example.vercel.app              │
│  └─ Production API keys                     │
│                                              │
└──────────────────────────────────────────────┘

FUTURE: Multi-Device Setup
┌──────────────────────────────────────────────┐
│  Multiple Raspberry Pis                      │
│  ├─ Each with device_id environment var     │
│  ├─ All report to same Supabase project     │
│  ├─ Dashboard shows all devices             │
│  ├─ Device management UI (future)           │
│  └─ Aggregated statistics                   │
│                                              │
│  Extended Dashboard                         │
│  ├─ Device selector dropdown                │
│  ├─ Per-device statistics                   │
│  ├─ Combined view (all devices)             │
│  └─ Device health monitoring                │
└──────────────────────────────────────────────┘
```

---

## Testing Coverage

```
CURRENT (Integration Tests Only)
├─ test_doorbird_connection.py
│  ├─ Tests RTSP connection
│  ├─ Validates frame capture
│  └─ Saves test frame
│
└─ test_supabase_connection.py
   ├─ Tests environment variables
   ├─ Tests client initialization
   ├─ Tests database insert
   ├─ Tests database query
   ├─ Tests storage upload
   ├─ Tests complete workflow
   └─ Tests costume classification update

MISSING (Should Add)
├─ Unit Tests
│  ├─ PersonDetector.detect()
│  ├─ SupabaseClient methods
│  ├─ Image processing functions
│  └─ Configuration loading
│
├─ Integration Tests (in /tests/)
│  ├─ E2E: Capture → Detection → Upload
│  ├─ Retry logic on failure
│  └─ Error recovery
│
├─ Frontend Tests
│  ├─ Dashboard component rendering
│  ├─ Realtime subscription
│  ├─ Error handling
│  └─ Loading states
│
└─ CI/CD Testing
   ├─ Pytest + coverage
   ├─ Ruff linting
   ├─ MyPy type checking
   └─ GitHub Actions on PR
```

---

## Key Metrics

```
Code Size
├─ Python: 881 lines (4 files)
│  ├─ supabase_client.py: 269 lines (30%)
│  ├─ test_supabase_connection.py: 355 lines (40%)
│  ├─ detect_people.py: 176 lines (20%)
│  └─ test_doorbird_connection.py: 81 lines (10%)
│
├─ Frontend: 166 lines (3 files)
│  ├─ page.tsx: 134 lines (81%)
│  ├─ layout.tsx: 20 lines (12%)
│  └─ supabase.ts: 12 lines (7%)
│
└─ Total: 1,047+ lines of code

Documentation
├─ Total: 2,257 lines across 7 files
│  ├─ BLOG_NOTES.md: 1,125 lines (50%) ← Very long
│  ├─ PROJECT_SPEC.md: 391 lines (17%)
│  ├─ README.md: 227 lines (10%)
│  ├─ SUPABASE_SETUP.md: 237 lines (10%)
│  ├─ DOORBIRD_SETUP.md: 138 lines (6%)
│  ├─ dashboard/SETUP.md: 80 lines (4%)
│  └─ dashboard/README.md: 59 lines (3%)
│
└─ Ratio: 2.15:1 (docs to code) ← Good!

File Count
├─ Total Files: 28
├─ Python: 4 files
├─ Frontend: 3 files
├─ Configuration: 8 files
├─ Documentation: 7 files
└─ Infrastructure: 6 files
```

---

## Organizational Scoring

```
Component Organization Scores

Backend (Python)
├─ Code Structure: 3/10    (Root-level files)
├─ Module Design: 2/10    (No package structure)
├─ Testing: 6/10          (Integration tests exist)
├─ Type Safety: 5/10      (Some type hints)
└─ Average: 4/10          Grade: D

Frontend (React/TS)
├─ Code Structure: 8/10   (Good app structure)
├─ Component Design: 6/10 (Monolithic page.tsx)
├─ Testing: 3/10          (No tests)
├─ Type Safety: 9/10      (Full TypeScript)
└─ Average: 6.5/10        Grade: C+

Configuration
├─ Organization: 5/10     (Scattered files)
├─ Documentation: 3/10    (Generic .env.example)
├─ Maintainability: 4/10  (Duplicate .env)
└─ Average: 4/10          Grade: D

Documentation
├─ Completeness: 8/10     (Good coverage)
├─ Organization: 3/10     (7 files, unclear)
├─ Maintainability: 3/10  (Hard to update)
├─ Clarity: 7/10          (Well-written)
└─ Average: 5.25/10       Grade: D+

Overall Score: 4.9/10 (C-)
├─ Status: Functional MVP with structural issues
├─ Verdict: Refactoring needed before scaling
└─ Priority: Reorganize code structure first
```

