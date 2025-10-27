# Comprehensive Codebase Structure Analysis
## Doorstep Costume Classifier

---

## 1. OVERVIEW

**Project Type:** Edge AI System + Web Dashboard  
**Primary Language Stack:** Python (backend/edge) + TypeScript/JavaScript (frontend)  
**Architecture:** Raspberry Pi edge compute + Supabase backend + Next.js frontend  
**Repository Size:** 28 files, 881 lines of Python code, mixed TypeScript/JavaScript

---

## 2. CURRENT DIRECTORY STRUCTURE

```
/root/repo/
├── README.md                              (4.8 KB - Main project readme)
├── PROJECT_SPEC.md                        (12.4 KB - System architecture spec)
├── BLOG_NOTES.md                          (34.7 KB - Implementation notes)
├── DOORBIRD_SETUP.md                      (4.3 KB - Camera setup guide)
├── SUPABASE_SETUP.md                      (5.7 KB - Database setup guide)
│
├── .env.example                           (Environment template)
├── .gitignore                             (Git exclusions)
├── pyproject.toml                         (Python dependencies config - 1.1 KB)
├── uv.lock                                (Dependency lock file - 328 KB)
├── supabase_migration.sql                 (Database schema - 3.6 KB)
│
├── PYTHON BACKEND (Root Level)
│   ├── detect_people.py                   (176 lines - Main detection loop)
│   ├── supabase_client.py                 (269 lines - Database client)
│   ├── test_doorbird_connection.py        (81 lines - Connection test)
│   └── test_supabase_connection.py        (355 lines - Integration test)
│
└── DASHBOARD/ (Next.js Frontend)
    ├── README.md                          (59 lines)
    ├── SETUP.md                           (80 lines)
    ├── .env.example                       (Environment template)
    ├── .gitignore                         (Node.js ignores)
    ├── package.json                       (npm dependencies)
    ├── package-lock.json                  (Dependency lock)
    │
    ├── TypeScript Configuration
    │   └── tsconfig.json                  (TypeScript compiler config)
    │
    ├── Next.js Configuration
    │   └── next.config.js                 (4 lines - Minimal config)
    │
    ├── Styling Configuration
    │   ├── postcss.config.js
    │   ├── tailwind.config.js
    │   └── app/globals.css
    │
    ├── APP/ (Next.js App Router)
    │   ├── layout.tsx                     (20 lines - Root layout)
    │   ├── page.tsx                       (134 lines - Dashboard component)
    │   └── globals.css                    (Tailwind styles)
    │
    └── LIB/ (Utilities)
        └── supabase.ts                    (12 lines - Supabase client)
```

---

## 3. FILE TYPE BREAKDOWN

| File Type | Count | Purpose |
|-----------|-------|---------|
| Markdown (.md) | 7 | Documentation |
| Python (.py) | 4 | Backend logic |
| TypeScript (.ts) | 1 | Type definitions |
| TypeScript/React (.tsx) | 2 | UI components |
| JavaScript (.js) | 3 | Config files |
| JSON (.json) | 3 | Dependencies & config |
| CSS (.css) | 1 | Styling |
| SQL (.sql) | 1 | Database schema |
| TOML (.toml) | 1 | Python config |
| Config/Other | 5 | .env.example, .gitignore, etc. |
| **TOTAL** | **28** | |

---

## 4. TECHNOLOGY STACK BREAKDOWN

### Backend/Edge (Python)
```
├── Python 3.10+
├── OpenCV (cv2) - Video capture & image processing
├── YOLOv8n - Person detection model
├── Supabase Python Client - Database operations
├── python-dotenv - Environment variables
├── ruff - Linting & formatting (dev)
└── uv - Package manager (by Astral)
```

**Lines of Code:**
- supabase_client.py: 269 lines
- test_supabase_connection.py: 355 lines
- detect_people.py: 176 lines
- test_doorbird_connection.py: 81 lines
- **Total: 881 lines**

### Frontend (Next.js + TypeScript)
```
├── Next.js 16.0
├── React 19.2
├── TypeScript 5.9
├── Tailwind CSS 4.1
├── @supabase/supabase-js - Realtime database client
└── PostCSS 8.5 + Autoprefixer
```

**Lines of Code:**
- page.tsx (Dashboard): 134 lines
- layout.tsx: 20 lines
- supabase.ts: 12 lines
- **Total: ~166 lines**

### Infrastructure
```
├── Supabase (PostgreSQL database + Auth + Realtime)
├── Raspberry Pi 5 (8GB RAM)
├── DoorBird Doorbell Camera (RTSP stream source)
├── Baseten API (Vision-language model - future)
└── Vercel (Dashboard hosting)
```

---

## 5. COMPONENT ARCHITECTURE

### 1. **Edge Detection System** (Raspberry Pi)
**Location:** `/root/repo/` (root level files)

**Purpose:** Captures video, detects people, logs to database

**Components:**
- `detect_people.py` - Main event loop
  - Connects to DoorBird RTSP stream
  - Runs YOLOv8n person detection
  - Saves frames locally on detection
  - Uploads to Supabase via SupabaseClient

- `supabase_client.py` - Database abstraction layer
  - Image upload to Supabase Storage
  - Detection record insertion
  - Query recent detections
  - Update costume classifications
  - Graceful error handling

- `test_doorbird_connection.py` - DoorBird connectivity validation
  - Tests RTSP stream connection
  - Captures test frame
  - Validates credentials

- `test_supabase_connection.py` - Full integration test suite
  - Environment variable validation
  - Client initialization
  - Database insert/query operations
  - Storage upload operations
  - Complete workflow testing
  - Costume classification updates

### 2. **Real-time Dashboard** (Next.js)
**Location:** `/root/repo/dashboard/`

**Purpose:** Display detections in real-time via Supabase Realtime

**Components:**
- `app/page.tsx` - Main dashboard component
  - Fetches initial detections
  - Subscribes to Supabase Realtime channel
  - Displays person detections list
  - Shows confidence scores
  - Shows costume classifications (if available)
  - Error handling & loading states

- `app/layout.tsx` - Root layout
  - Minimal structure
  - CSS globals import
  - Basic metadata

- `lib/supabase.ts` - Supabase client initialization
  - Creates Supabase client instance
  - Configures Realtime parameters
  - Uses public anon key (frontend)

- `globals.css` - Tailwind CSS stylesheet

### 3. **Configuration Layer**
**Location:** `/root/repo/` and `/root/repo/dashboard/`

**Files:**
- `pyproject.toml` - Python project metadata
  - Dependency declaration
  - Ruff linting rules
  - Format configuration
  
- `dashboard/package.json` - Node.js dependencies
  - Production dependencies
  - Build scripts
  
- `dashboard/tsconfig.json` - TypeScript configuration
  - Compiler options
  - Path aliases (@/*)
  
- `dashboard/next.config.js` - Next.js configuration
  - Currently minimal (no customizations)
  
- `dashboard/tailwind.config.js` - Tailwind configuration
- `dashboard/postcss.config.js` - PostCSS plugins

### 4. **Documentation Layer**
**Location:** `/root/repo/`

**Files:**
- `README.md` - Main project overview
  - Quick start guide
  - Pi management instructions
  - Development workflow
  
- `PROJECT_SPEC.md` - Complete system specification
  - Architecture diagram
  - Hardware requirements
  - Software responsibilities
  - Data flow walkthrough
  
- `BLOG_NOTES.md` - Implementation journey
  - Design decisions
  - Problem-solving notes
  
- `DOORBIRD_SETUP.md` - Camera configuration guide
- `SUPABASE_SETUP.md` - Database setup instructions
- `dashboard/SETUP.md` - Dashboard deployment guide

### 5. **Database Schema**
**Location:** `/root/repo/supabase_migration.sql`

**Tables:**
- `person_detections` - Stores detection events
  - Fields: id, timestamp, confidence, bounding_box, device_id, image_url, costume_classification, costume_confidence

---

## 6. DATA FLOW & INTEGRATION

```
[DoorBird Camera] --RTSP--> [Raspberry Pi]
                                   |
                          detect_people.py
                          ├─ OpenCV capture
                          ├─ YOLOv8n detection
                          └─ Frame saving
                                   |
                        supabase_client.py
                        ├─ Image upload
                        └─ Record insert
                                   |
                                   v
                         [Supabase Backend]
                        ├─ PostgreSQL DB
                        ├─ Storage (images)
                        └─ Realtime channel
                                   |
                    WebSocket (Realtime)
                                   |
                                   v
                   [Next.js Dashboard] (Vercel)
                  page.tsx + supabase.ts
                   ├─ Fetch initial data
                   ├─ Subscribe to updates
                   └─ Render live detection list
```

---

## 7. ORGANIZATIONAL ISSUES & INCONSISTENCIES

### CRITICAL ISSUES

1. **Python Code at Root Level**
   - **Problem:** All Python backend files (detect_people.py, supabase_client.py, tests) are in root directory
   - **Impact:** Difficult to scale; no module structure; no separation of concerns
   - **Example:**
     ```
     /root/repo/
     ├── detect_people.py
     ├── supabase_client.py
     ├── test_doorbird_connection.py
     ├── test_supabase_connection.py
     ```
   - **Should Be:**
     ```
     /root/repo/
     ├── backend/
     │   ├── src/
     │   │   ├── detection/
     │   │   │   └── person_detector.py
     │   │   ├── storage/
     │   │   │   └── supabase_client.py
     │   │   ├── models/
     │   │   │   └── detection.py
     │   │   └── main.py
     │   └── tests/
     │       ├── test_doorbird.py
     │       └── test_supabase.py
     ```

2. **Missing Module Structure**
   - **Problem:** No Python packages defined; can't be imported as a library
   - **Missing:** `__init__.py` files; no src/ directory; no proper package hierarchy
   - **Result:** Can only run scripts directly, not import utilities

3. **Test Files Mixed with Code**
   - **Problem:** Test files in root level alongside production code
   - **Pattern:** test_doorbird_connection.py, test_supabase_connection.py in root
   - **Best Practice:** Should be in `tests/` or `backend/tests/` directory with pytest configuration

4. **Configuration Mixing**
   - **Problem:** .env.example exists in both root AND dashboard
   - **Issue:** Unclear which env vars are shared, which are specific
   - **Impact:** Maintenance confusion; duplication
   - **Ideally:** Single .env.example with clear sections for backend/frontend

5. **Documentation Proliferation**
   - **Problem:** 7 markdown files in root and dashboard
   - **Files:** README.md, PROJECT_SPEC.md, BLOG_NOTES.md, DOORBIRD_SETUP.md, SUPABASE_SETUP.md, dashboard/README.md, dashboard/SETUP.md
   - **Issue:** Unclear which is current; hard to maintain single source of truth
   - **Suggestion:** Organize into docs/ directory with clear structure

### MODERATE ISSUES

6. **No CI/CD Configuration**
   - **Missing:** No GitHub Actions, no pre-commit hooks, no automated testing
   - **Files Missing:** .github/workflows/, setup.cfg, tox.ini, pytest.ini
   - **Impact:** Can't validate code quality on each commit

7. **Minimal Next.js Configuration**
   - **Problem:** `next.config.js` is completely empty
   - **Issue:** No custom build optimizations; no API routes defined
   - **Observation:** Currently frontend-only, but extensibility limited

8. **No Environment Variable Documentation**
   - **Problem:** .env.example files exist but are generic
   - **Issue:** Developers must read source code to understand required vars
   - **Should Have:** Detailed comments in .env.example files

9. **Missing Logging Configuration**
   - **Problem:** No centralized logging setup; relies on print() statements
   - **Impact:** Difficult to debug on production Pi; no log rotation; no structured logging

10. **No Error Recovery Strategy**
    - **Problem:** detect_people.py has basic error handling but no retry logic
    - **Issue:** If DoorBird connection drops, reconnect is basic (sleeps 1 second)
    - **Missing:** Exponential backoff, connection pooling, graceful degradation

### MINOR ISSUES

11. **Inconsistent Code Style Enforcement**
    - **Problem:** Only Python has ruff configured; JavaScript/TypeScript lacks strict linting rules
    - **Missing:** ESLint configuration for dashboard; Next.js lint rules not customized

12. **No Type Safety in Python**
    - **Problem:** supabase_client.py uses Optional[] but could use more strict typing
    - **Issue:** detect_people.py has minimal type hints
    - **Suggestion:** Use mypy with strict mode

13. **Dashboard Component Simplicity**
    - **Problem:** page.tsx is a single 134-line component
    - **Issue:** Not modular; all logic in one component; no component breakdown
    - **Example:**
      ```
      Should split into:
      - DetectionList.tsx
      - DetectionCard.tsx
      - LoadingState.tsx
      - ErrorState.tsx
      ```

14. **Hardcoded Values in Code**
    - **detect_people.py:**
      - Frame skip: `if frame_count % 30 != 0` (hardcoded 30)
      - Detection threshold: `if confidence > 0.5` (hardcoded 0.5)
      - Duplicate detection timeout: `if current_time - last_detection_time > 2` (hardcoded 2s)
    - **Should be:** Config file or constants module

15. **No Secrets Management**
    - **Problem:** API keys stored in .env files (good for development)
    - **Missing:** Secrets rotation policy; no mention of how to rotate keys on production Pi

16. **Incomplete Error Messages**
    - **Problem:** Some error messages are vague
    - **Example:** "⚠️ Failed to read frame, reconnecting..."
    - **Better:** Include specific error details, retry count, last successful read time

---

## 8. DETAILED ANALYSIS BY COMPONENT

### 8.1 Backend (Python) Organization: ⚠️ POOR

**Current State:**
```
4 Python files in root directory with no package structure
- Direct script execution only
- All imports are absolute (requires PYTHONPATH manipulation)
- No clear module boundaries
- Circular dependency risk (detect_people imports supabase_client)
```

**Problems:**
- Cannot be installed as package with pip
- Cannot be imported in other projects
- Difficult to test individual components
- No version control for source code separate from environment

**Code Quality:**
- ✅ Good: Clear docstrings, error handling with try/except
- ✅ Good: Environment variable validation
- ❌ Bad: Hardcoded magic numbers (30 frames, 0.5 threshold, 2s timeout)
- ❌ Bad: print() statements instead of logging module
- ⚠️ Mixed: Type hints present but not comprehensive

### 8.2 Frontend (Next.js) Organization: ✅ GOOD

**Current State:**
```
Well-structured Next.js 16 app with App Router
- Clear separation: app/ (routes/components), lib/ (utilities)
- TypeScript throughout
- Minimal but functional configuration
```

**Problems:**
- Single monolithic component (page.tsx - 134 lines)
- No component library or design system
- Limited styling customization
- No API routes (could be useful for webhook from Pi)

**Code Quality:**
- ✅ Good: Modern React hooks (useEffect, useState)
- ✅ Good: TypeScript interfaces for type safety
- ✅ Good: Error handling & loading states
- ⚠️ Mixed: Realtime subscription, but no unsubscribe cleanup check

### 8.3 Configuration Organization: ⚠️ FAIR

**Current State:**
```
Multiple config files scattered across root and dashboard/
- pyproject.toml (Python) in root
- package.json (Node) in dashboard/
- tsconfig.json in dashboard/
- Multiple .env.example files
- Minimal documentation of configuration
```

**Issues:**
- Duplicate env var definitions in two .env.example files
- No single source of truth for environment configuration
- Backend and frontend config files not coordinated

### 8.4 Documentation Organization: ⚠️ CLUTTERED

**Current State:**
```
7 markdown files scattered:
- Root: README.md, PROJECT_SPEC.md, BLOG_NOTES.md, DOORBIRD_SETUP.md, SUPABASE_SETUP.md
- Dashboard: README.md, SETUP.md
- No index; no structure; unclear which is current
```

**File Sizes:**
- BLOG_NOTES.md: 34 KB (very long, detailed implementation notes)
- PROJECT_SPEC.md: 13 KB (system specification - good)
- README.md: 5 KB (main overview)
- Others: 4-6 KB (setup guides)

**Issues:**
- Duplicate setup instructions (main README + SETUP.md in dashboard)
- No table of contents
- Blog notes mixed with specifications
- Hard to find specific information

---

## 9. SCALABILITY ASSESSMENT

### Current Scale
- Single Pi instance
- Single DoorBird camera
- Single dashboard view
- ~881 lines of Python code

### Scaling Bottlenecks
1. **Python Code:** No package structure limits distribution to other Pis
2. **Database:** Supabase can scale, but no multi-device support code
3. **Frontend:** Single device dashboard; would need multi-device UI
4. **Detection Logic:** No model management; costume classification not yet implemented

### Scaling Readiness
- ⚠️ Not ready for multiple Pi instances
- ⚠️ No device management system
- ✅ Supabase supports multi-device
- ✅ Frontend Realtime can handle multiple devices

---

## 10. SECURITY CONSIDERATIONS

### Current Implementation
- ✅ Uses Supabase service role key for backend (full access)
- ✅ Uses public anon key for frontend (RLS protected)
- ✅ Face blurring planned but not yet implemented
- ✅ No raw frames uploaded to cloud
- ⚠️ Credentials in .env files (standard practice)

### Gaps
- ❌ No API authentication on Pi (internal network assumed)
- ❌ No rate limiting on detection uploads
- ❌ No validation of detection data before insertion
- ⚠️ No secrets rotation mechanism
- ⚠️ No audit logging of detections

---

## 11. DEPLOYMENT READINESS

### Production Checklist
- ✅ Environment variables templated
- ✅ .gitignore configured
- ✅ Dependencies locked (uv.lock, package-lock.json)
- ⚠️ No deployment scripts
- ⚠️ No systemd service file for Pi startup
- ⚠️ No monitoring/alerting setup
- ⚠️ No log rotation
- ❌ No health check endpoint
- ❌ No graceful shutdown handler

---

## 12. SUMMARY: ORGANIZATION QUALITY SCORE

| Aspect | Score | Notes |
|--------|-------|-------|
| Backend Code Organization | 3/10 | Root-level Python files, no package structure |
| Frontend Code Organization | 8/10 | Good Next.js structure, but single component |
| Configuration Management | 5/10 | Multiple scattered configs, duplicate .env files |
| Documentation | 4/10 | 7 markdown files, unclear structure and ownership |
| Testing | 6/10 | Has integration tests, but no unit tests or test structure |
| Type Safety | 7/10 | TypeScript in frontend, partial types in Python |
| Error Handling | 7/10 | Try/except blocks present, basic error messages |
| Scalability | 3/10 | Single-device focused, no multi-instance support |
| Security | 6/10 | Basic measures, but gaps in API authentication and validation |
| **OVERALL** | **5.5/10** | **Functional MVP but needs structural refactoring for growth** |

---

## 13. RECOMMENDED REFACTORING STRUCTURE

```
costume-classifier/
├── backend/                           ← NEW: Python edge compute
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── detection/
│   │   │   ├── __init__.py
│   │   │   ├── person_detector.py
│   │   │   └── models.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   └── supabase_client.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── logger.py
│   │       └── constants.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_doorbird.py
│   │   ├── test_supabase.py
│   │   └── test_detector.py
│   ├── pyproject.toml
│   ├── README.md
│   └── .env.example
│
├── dashboard/                         ← EXISTING: Next.js frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── DetectionList.tsx
│   │   │   ├── DetectionCard.tsx
│   │   │   ├── LoadingState.tsx
│   │   │   └── ErrorState.tsx
│   │   ├── lib/
│   │   │   └── supabase.ts
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── globals.css
│   │   └── types/
│   │       └── detection.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── README.md
│   └── .env.example
│
├── docs/                              ← NEW: Organized documentation
│   ├── README.md                      (Start here)
│   ├── architecture.md
│   ├── setup/
│   │   ├── doorbird.md
│   │   ├── supabase.md
│   │   ├── backend.md
│   │   └── frontend.md
│   ├── development/
│   │   ├── python-setup.md
│   │   ├── testing.md
│   │   └── contributing.md
│   └── blog/
│       └── implementation-notes.md
│
├── .github/                           ← NEW: CI/CD
│   └── workflows/
│       ├── test-backend.yml
│       ├── test-frontend.yml
│       └── lint.yml
│
├── .env.example                       ← CONSOLIDATED
├── README.md                          ← Main overview only
├── pyproject.toml                     ← Root Python config (if needed)
├── docker-compose.yml                 ← NEW: Local development
└── .gitignore
```

---

## 14. NEXT STEPS FOR IMPROVEMENT

### Priority 1: Critical Refactoring
1. Move Python code to `backend/src/` package structure
2. Create `backend/tests/` directory with pytest configuration
3. Reorganize documentation to `docs/` directory
4. Create consolidated `.env.example` with comments

### Priority 2: Code Quality
1. Add mypy type checking to Python backend
2. Configure ESLint for TypeScript/JavaScript
3. Add pre-commit hooks for linting and formatting
4. Add GitHub Actions for CI/CD

### Priority 3: Scalability
1. Implement multi-device support in backend
2. Add device management UI to dashboard
3. Create constants/config module for magic numbers
4. Implement structured logging

### Priority 4: Production Readiness
1. Add systemd service file for Pi
2. Implement health check endpoint
3. Add graceful shutdown handling
4. Create deployment documentation

---

## CONCLUSION

The codebase is a **functional MVP** with a clear technology vision and good documentation of intent. However, it suffers from **poor structural organization** at the Python backend level and scattered documentation. The frontend is well-structured and modern.

**Key Strengths:**
- Clear architecture and data flow
- Good separation of concerns between edge and cloud
- Modern tech stack (Next.js 16, React 19, Supabase)
- Comprehensive setup documentation

**Key Weaknesses:**
- Python code not organized as a package
- Scattered configuration files and documentation
- No CI/CD or automated testing infrastructure
- Not designed for multi-device scaling
- Limited error handling and logging

**Recommendation:** Perform structural refactoring (moving Python to package structure) before adding more features. This will significantly improve code quality, testability, and scalability.
