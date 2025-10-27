# Quick Reference: Codebase Structure Overview

## File Organization at a Glance

```
REPOSITORY ROOT (28 files total)
│
├── 📄 Documentation (7 files)
│   ├── README.md (5 KB) - Main overview
│   ├── PROJECT_SPEC.md (13 KB) - Complete architecture
│   ├── BLOG_NOTES.md (35 KB) - Implementation details
│   ├── DOORBIRD_SETUP.md (4 KB) - Camera setup
│   ├── SUPABASE_SETUP.md (6 KB) - Database setup
│   ├── dashboard/README.md (1 KB)
│   └── dashboard/SETUP.md (1 KB)
│
├── 🐍 Python Backend (4 files, 881 lines)
│   ├── detect_people.py (176 lines) - Main detection loop
│   ├── supabase_client.py (269 lines) - Database client
│   ├── test_doorbird_connection.py (81 lines) - Connection test
│   └── test_supabase_connection.py (355 lines) - Integration test
│
├── ⚙️ Configuration (7 files)
│   ├── pyproject.toml - Python deps
│   ├── dashboard/package.json - Node deps
│   ├── dashboard/tsconfig.json - TS compiler
│   ├── dashboard/next.config.js - Next.js config
│   ├── dashboard/tailwind.config.js - Tailwind
│   ├── dashboard/postcss.config.js - PostCSS
│   └── 2x .env.example - Env templates
│
├── 📦 Dependencies
│   ├── uv.lock (328 KB) - Python lock file
│   └── dashboard/package-lock.json - Node lock file
│
├── 💾 Database
│   └── supabase_migration.sql (4 KB) - Schema
│
├── .gitignore (36 lines)
│
└── 📱 Dashboard (Next.js Frontend)
    └── /dashboard/
        ├── app/
        │   ├── page.tsx (134 lines) - Main dashboard
        │   ├── layout.tsx (20 lines) - Root layout
        │   └── globals.css - Styles
        └── lib/
            └── supabase.ts (12 lines) - Supabase client
```

---

## Technology Stack at a Glance

### Edge (Raspberry Pi)
- **Language:** Python 3.10+
- **Key Libraries:** OpenCV, YOLOv8n, Supabase client
- **Package Manager:** uv (by Astral)
- **Code Size:** ~880 lines

### Frontend (Dashboard)
- **Framework:** Next.js 16 + React 19
- **Language:** TypeScript 5.9
- **Styling:** Tailwind CSS 4.1
- **Database Client:** Supabase JS
- **Hosting:** Vercel
- **Code Size:** ~165 lines

### Infrastructure
- **Database:** Supabase (PostgreSQL)
- **Hardware:** Raspberry Pi 5 (8GB)
- **Camera:** DoorBird RTSP
- **AI:** YOLOv8n (detection), Baseten (classification)

---

## Directory Organization Grade

| Area | Grade | Status |
|------|-------|--------|
| **Backend Python** | D+ | ⚠️ Root-level files, no package structure |
| **Frontend React** | A- | ✅ Well-organized, but monolithic component |
| **Configuration** | C | ⚠️ Scattered across root and dashboard/ |
| **Documentation** | C- | ⚠️ 7 files, unclear structure |
| **Testing** | C | ⚠️ Integration tests only, no unit tests |
| **CI/CD** | F | ❌ No GitHub Actions or automation |
| **Type Safety** | B | ✅ TS frontend, partial Python hints |
| **Error Handling** | B- | ✅ Try/except blocks, basic recovery |
| **Scalability** | D | ⚠️ Single-device design |
| **Security** | C+ | ⚠️ .env files, no API auth, no rate limiting |
| **Overall** | C+ | ⚠️ **Functional MVP, needs refactoring** |

---

## Critical Issues Summary

### 1. Python Code at Root Level (Most Critical)
```
❌ Current:
/repo/detect_people.py
/repo/supabase_client.py
/repo/test_*.py

✅ Should be:
/repo/backend/src/detection/person_detector.py
/repo/backend/src/storage/supabase_client.py
/repo/backend/tests/test_*.py
```

### 2. Documentation Scattered Everywhere
```
❌ Current:
/repo/README.md (5 KB)
/repo/PROJECT_SPEC.md (13 KB)
/repo/BLOG_NOTES.md (35 KB) ← Very long
/repo/DOORBIRD_SETUP.md (4 KB)
/repo/SUPABASE_SETUP.md (6 KB)
/repo/dashboard/README.md
/repo/dashboard/SETUP.md

✅ Should be:
/repo/docs/
├── README.md
├── architecture.md
├── setup/
│   ├── doorbird.md
│   ├── supabase.md
│   └── backend.md
└── blog/
    └── implementation-notes.md
```

### 3. Configuration Files Not Coordinated
```
❌ Current:
/repo/.env.example (generic)
/repo/dashboard/.env.example (generic)
No clear documentation of what goes where

✅ Should be:
/repo/.env.example (with comments)
[BACKEND SECTION]
DOORBIRD_USERNAME=
DOORBIRD_PASSWORD=
DOORBIRD_IP=

[SUPABASE SECTION]
NEXT_PUBLIC_SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

[FRONTEND SECTION]
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

### 4. No Testing Infrastructure
```
❌ Current:
- Integration tests only (test_supabase_connection.py)
- Manual testing model
- No pytest.ini or tox.ini
- No GitHub Actions

✅ Should Have:
/repo/backend/pyproject.toml
[tool.pytest]
testpaths = ["tests"]

.github/workflows/test-backend.yml
- Run pytest on PR
- Check with mypy and ruff
```

### 5. Hardcoded Magic Numbers
```
❌ detect_people.py line 82:
if frame_count % 30 != 0:
    continue

❌ detect_people.py line 99:
if confidence > 0.5:

❌ detect_people.py line 123:
if current_time - last_detection_time > 2:

✅ Should be:
# backend/src/config.py
FRAME_SKIP_INTERVAL = 30
CONFIDENCE_THRESHOLD = 0.5
DUPLICATE_DETECTION_TIMEOUT_SECONDS = 2
```

---

## Strengths of Current Organization

✅ **Good separations:**
- Edge compute (Python) separate from frontend (Next.js)
- Database operations abstracted in SupabaseClient class
- Frontend uses App Router pattern effectively

✅ **Good practices:**
- Environment variables templated (.env.example)
- Dependencies locked (uv.lock, package-lock.json)
- .gitignore properly configured
- TypeScript in frontend
- Clear module imports

✅ **Good documentation:**
- Comprehensive PROJECT_SPEC.md
- Setup guides for each component
- Implementation blog notes

---

## What Needs Refactoring

### Immediate (Blocking Issues)

1. **Move Python files to package structure**
   - Create backend/src/, backend/tests/
   - Add __init__.py files
   - Use relative imports within package

2. **Consolidate documentation**
   - Create docs/ directory
   - Move BLOG_NOTES to docs/blog/
   - Create docs/README.md with index

3. **Coordinate environment variables**
   - Single .env.example with sections
   - Clear comments for each variable
   - Document where they're used

### Short Term (Quality Issues)

4. **Add CI/CD**
   - GitHub Actions for testing
   - Pre-commit hooks for linting
   - Automated deployment

5. **Improve error handling**
   - Use logging module (not print)
   - Add retry logic with backoff
   - Health check endpoint

6. **Extract configuration**
   - Create backend/config.py
   - Move hardcoded values to constants
   - Make settings overrideable

### Medium Term (Scalability)

7. **Component refactoring**
   - Split dashboard page.tsx into components
   - Add unit tests
   - Create reusable components

8. **Multi-device support**
   - Device management in database
   - Device selector UI
   - Multi-Pi deployment guide

---

## File Dependency Graph

```
detect_people.py
    ↓
supabase_client.py ← Used by detect_people.py
    ↓
Supabase (Cloud)
    ↑
dashboard/lib/supabase.ts ← Used by dashboard/app/page.tsx
    ↓
dashboard/app/page.tsx (Main component)
    ↓
dashboard/app/layout.tsx
    ↓
dashboard/globals.css

Configuration Files:
pyproject.toml (Python)
dashboard/package.json (Node)
dashboard/tsconfig.json (TypeScript)
dashboard/next.config.js (Next.js)
.env.example (Both)
```

---

## Component Interaction Map

```
RASPBERRY PI
├── detect_people.py
│   ├── Uses: OpenCV (RTSP capture)
│   ├── Uses: YOLOv8n (Person detection)
│   ├── Uses: SupabaseClient
│   └── Outputs: Detection events to Supabase
│
└── supabase_client.py
    ├── Uploads images to Supabase Storage
    ├── Inserts records to person_detections table
    ├── Queries recent detections
    └── Updates costume classifications

SUPABASE (Cloud)
├── PostgreSQL Database
│   └── person_detections table
├── Storage
│   └── detection-images bucket
└── Realtime
    └── WebSocket channel

DASHBOARD (Next.js on Vercel)
├── app/layout.tsx (Root)
├── app/page.tsx (Main component)
│   ├── Fetches initial data via lib/supabase.ts
│   ├── Subscribes to Realtime channel
│   └── Re-renders on new detections
└── styles (Tailwind CSS)
```

---

## Lines of Code Summary

| Component | Files | Lines | Purpose |
|-----------|-------|-------|---------|
| detect_people.py | 1 | 176 | Main detection loop |
| supabase_client.py | 1 | 269 | Database abstraction |
| test_supabase_connection.py | 1 | 355 | Integration tests |
| test_doorbird_connection.py | 1 | 81 | Connection test |
| **Python Total** | **4** | **881** | Edge compute |
| dashboard/app/page.tsx | 1 | 134 | Main dashboard |
| dashboard/app/layout.tsx | 1 | 20 | Root layout |
| dashboard/lib/supabase.ts | 1 | 12 | DB client init |
| **Frontend Total** | **3** | **166** | Web dashboard |
| **TOTAL** | **7** | **1,047** | |

*Not including configuration files, dependencies, or documentation*

---

## Environment Variables Checklist

### Backend (Raspberry Pi)
- [ ] DOORBIRD_USERNAME
- [ ] DOORBIRD_PASSWORD
- [ ] DOORBIRD_IP
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] SUPABASE_SERVICE_ROLE_KEY
- [ ] HOSTNAME (device identifier)

### Frontend (Dashboard)
- [ ] NEXT_PUBLIC_SUPABASE_URL
- [ ] NEXT_PUBLIC_SUPABASE_ANON_KEY

### Both
- [ ] .env file created from .env.example
- [ ] Never committed to git
- [ ] Kept private and secure

---

## Running the Project

```bash
# Backend (on Raspberry Pi)
cd /repo
uv sync                           # Install dependencies
uv run python test_doorbird_connection.py    # Test camera
uv run python test_supabase_connection.py    # Test database
uv run python detect_people.py    # Start detection

# Frontend (Dashboard)
cd /repo/dashboard
npm install                       # Install dependencies
npm run dev                       # Start dev server
npm run build                     # Build for production
npm run start                     # Run production server
```

---

## Next Steps (Priority Order)

1. **Refactor Python code** to package structure
2. **Consolidate documentation** to docs/ directory
3. **Add CI/CD** with GitHub Actions
4. **Add type checking** with mypy
5. **Improve error handling** with logging
6. **Extract configuration** to constants
7. **Refactor dashboard** into smaller components
8. **Add multi-device support** to backend and frontend

---

## Key Takeaway

The project is a **well-intentioned MVP** with good technology choices and clear architecture, but **poor structural organization** that will become a liability as the project grows. Priority #1 should be refactoring the Python backend into a proper package structure before adding more features.
