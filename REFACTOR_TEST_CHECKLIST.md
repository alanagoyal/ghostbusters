# Refactor Testing Checklist

## 🔍 Backend Tests

### Python Import Tests
- [ ] Test importing baseten_client: `uv run python -c "from backend.src.clients.baseten_client import BasetenClient; print('✅ Import successful')"`
- [ ] Test importing supabase_client: `uv run python -c "from backend.src.clients.supabase_client import SupabaseClient; print('✅ Import successful')"`
- [ ] Verify all `__init__.py` files exist:
  - [ ] `backend/src/__init__.py`
  - [ ] `backend/src/clients/__init__.py`
  - [ ] `backend/src/detection/__init__.py`
  - [ ] `backend/src/utils/__init__.py`

### Dependency Installation
- [ ] Run `uv sync` to ensure dependencies install correctly
- [ ] Verify `pyproject.toml` has correct package configuration

### Integration Tests (in order)
- [ ] **Test Baseten connection**: `uv run tests/integration/test_baseten_connection.py`
  - Should connect to Baseten API
  - Should successfully make a test classification request

- [ ] **Test Supabase connection**: `uv run tests/integration/test_supabase_connection.py`
  - Should connect to Supabase
  - Should upload test image to storage
  - Should create database entry
  - Should retrieve detection from database

- [ ] **Test DoorBird connection**: `uv run tests/integration/test_doorbird_connection.py`
  - Should connect to DoorBird camera
  - Should capture frames from RTSP stream

- [ ] **Test single-person costume detection**: `uv run tests/integration/test_costume_detection.py`
  - Should process test images from `tests/images/`
  - Should classify costumes using Baseten
  - Should upload to Supabase
  - Should create annotated images in `test_detections/`

- [ ] **Test multi-person detection**: `uv run tests/integration/test_multiple_people.py`
  - Should detect multiple people in test-6.png and test-7.png
  - Should classify each person separately
  - Should create individual database entries for each person

### Main Script
- [ ] **Run main detection script**: `uv run backend/scripts/main.py`
  - Should load YOLO model
  - Should connect to DoorBird RTSP stream
  - Should connect to Baseten (if configured)
  - Should connect to Supabase (if configured)
  - Should start watching for people
  - Should exit cleanly with Ctrl+C

## 🎨 Frontend Tests

### Setup
- [ ] Navigate to frontend: `cd frontend`
- [ ] Install dependencies: `npm install`
- [ ] Verify package.json exists
- [ ] Verify all TypeScript config files present

### Environment Configuration
- [ ] Copy `.env.example` to `.env.local`
- [ ] Add Supabase credentials
- [ ] Verify environment variables load correctly

### Development Server
- [ ] Start dev server: `npm run dev`
- [ ] Access dashboard at http://localhost:3000
- [ ] Verify page loads without errors
- [ ] Check browser console for errors

### Dashboard Components
- [ ] Stats cards display correctly
- [ ] Costume distribution chart renders
- [ ] Activity timeline shows data
- [ ] Live feed displays detections
- [ ] Confidence meter works

### Realtime Functionality
- [ ] Run a detection test while dashboard is open
- [ ] Verify new detection appears in real-time (sub-second latency)
- [ ] Check WebSocket connection in browser DevTools
- [ ] Verify no console errors during realtime updates

## 📚 Documentation Tests

### Verify All Docs Moved
- [ ] `docs/BASETEN_SETUP.md` exists
- [ ] `docs/DOORBIRD_SETUP.md` exists
- [ ] `docs/SUPABASE_SETUP.md` exists
- [ ] `docs/PROJECT_SPEC.md` exists
- [ ] `docs/BLOG_NOTES.md` exists

### README Links
- [ ] All documentation links in README work
- [ ] Project structure diagram is accurate
- [ ] All command examples use correct paths
- [ ] Frontend references use `frontend/` not `dashboard/`

## 🧪 Test Assets

### Test Images
- [ ] All images moved to `tests/images/`
- [ ] `tests/images/test-1.png` through `test-7.png` exist
- [ ] `tests/images/README.md` exists

### Test Output
- [ ] Running tests creates `test_detections/` directory
- [ ] Annotated images saved correctly
- [ ] No errors accessing test images

## 🗂️ File Structure Verification

### Root Directory Cleanup
- [ ] No Python `.py` files in root (except config files)
- [ ] No test files in root
- [ ] No documentation `.md` files in root (except README.md)
- [ ] Only config files remain: `pyproject.toml`, `.env.example`, `.gitignore`, `uv.lock`, `supabase_migration.sql`

### Directory Structure
```bash
tree -L 3 -I 'node_modules|.git|.next|__pycache__|*.pyc'
```
- [ ] Verify structure matches expected layout:
  - backend/src/clients/
  - backend/scripts/
  - frontend/app/, components/, lib/
  - tests/images/, integration/
  - docs/

## 🔧 Git Status

- [ ] Run `git status` to verify all changes tracked
- [ ] All renames shown as `R` (renamed) not `D` + `A`
- [ ] No unexpected untracked files
- [ ] All modifications intentional

## 🚀 End-to-End Test

### Complete Flow
1. [ ] Install dependencies: `uv sync`
2. [ ] Run integration test: `uv run tests/integration/test_costume_detection.py`
3. [ ] Start frontend: `cd frontend && npm run dev`
4. [ ] Verify detection appears in dashboard
5. [ ] Start main script: `uv run backend/scripts/main.py`
6. [ ] Verify real-time detections work end-to-end

## ✅ Success Criteria

All tests should pass with:
- ✅ No import errors
- ✅ All test scripts run successfully
- ✅ Frontend builds and runs without errors
- ✅ Realtime updates work
- ✅ Main detection script connects to all services
- ✅ Documentation is accessible and accurate

## 🐛 Common Issues to Check

- [ ] Module import errors → Check `sys.path` and `__init__.py` files
- [ ] Test image path errors → Verify `tests/images/` paths in test files
- [ ] Frontend build errors → Check `frontend/` paths in configs
- [ ] Missing dependencies → Run `uv sync` and `npm install`
- [ ] Environment variables → Verify `.env` and `.env.local` are configured

---

**Note**: Some tests require actual credentials (Baseten API key, Supabase config, DoorBird camera). Tests will gracefully fail with helpful messages if credentials are missing.
