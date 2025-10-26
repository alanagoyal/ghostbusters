# Supabase Setup Guide

This guide walks through setting up Supabase for the Halloween Costume Classifier project.

## Overview

The project uses Supabase for:
- **Database**: PostgreSQL table to store costume detection events
- **Realtime**: Live updates to the Next.js dashboard when new detections occur
- **RLS (Row Level Security)**: Secure access control for inserts and reads

## Database Schema

### `sightings` Table

| Column | Type | Description |
|--------|------|-------------|
| `id` | uuid | Primary key (auto-generated) |
| `description` | text | Open-ended costume description from vision-language model |
| `confidence` | numeric | Model confidence score (0-1), optional |
| `timestamp` | timestamptz | When the detection occurred (defaults to now()) |

### Example Records

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "description": "witch with purple hat and broom",
  "confidence": 0.92,
  "timestamp": "2025-10-31T02:42:11.123Z"
}
```

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project named `halloween-pi`
3. Choose a database password and save it securely
4. Wait for project to provision (~2 minutes)

### 2. Run Migration

You have two options to set up the database:

#### Option A: Using Supabase Dashboard (Recommended)

1. Open your Supabase project dashboard
2. Go to **SQL Editor** in the left sidebar
3. Click **+ New query**
4. Copy the contents of `supabase/migrations/001_create_sightings_table.sql`
5. Paste into the SQL editor
6. Click **Run** to execute

#### Option B: Using Supabase CLI

```bash
# Install Supabase CLI
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref <your-project-ref>

# Run migration
supabase db push
```

### 3. (Optional) Add Seed Data

For testing the dashboard UI, you can add sample data:

1. Go to **SQL Editor** in Supabase dashboard
2. Copy contents of `supabase/seed.sql`
3. Paste and run

This will create 20 sample costume detections to test your dashboard.

### 4. Get API Credentials

1. Go to **Settings** → **API** in your Supabase dashboard
2. Copy the following values:

   - **Project URL**: `https://xxx.supabase.co`
   - **anon/public key**: For Next.js frontend (read-only access)
   - **service_role key**: For Raspberry Pi (write access) ⚠️ **Keep secret!**

### 5. Configure Environment Variables

#### For Raspberry Pi

Create/update `.env` file:

```bash
# DoorBird credentials (existing)
DOORBIRD_USERNAME=your_username
DOORBIRD_PASSWORD=your_password
DOORBIRD_IP=192.168.x.x

# Supabase credentials (new)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...  # Use service_role key for write access
```

#### For Next.js Frontend

In your Next.js project, create `.env.local`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbG...  # Use anon key for read-only access
```

## Security Model

### Row Level Security (RLS) Policies

The migration automatically sets up two RLS policies:

1. **Insert Policy** (service_role only)
   - Only the Raspberry Pi (using service key) can insert new detections
   - Prevents unauthorized costume logging

2. **Select Policy** (public read access)
   - Anyone can read sightings data
   - Allows Next.js dashboard to display live results
   - No authentication required for viewing

### Key Security Practices

- ✅ **Service key on Pi only**: Never expose service_role key in frontend code
- ✅ **Anon key for frontend**: Use anon/public key in Next.js (safe to expose)
- ✅ **No updates/deletes**: RLS policies don't allow modifying or deleting records
- ✅ **No PII stored**: Only costume descriptions, no faces or identifiable information

## Realtime Configuration

The migration enables Realtime for the `sightings` table:

```sql
alter publication supabase_realtime add table public.sightings;
```

This allows the Next.js frontend to subscribe to live inserts:

```javascript
// Example Next.js code
const supabase = createClient(supabaseUrl, supabaseAnonKey)

supabase
  .channel('sightings')
  .on('postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'sightings' },
    (payload) => {
      console.log('New costume detected!', payload.new)
      // Update UI with new sighting
    }
  )
  .subscribe()
```

## Python Integration

### Install Supabase Client

```bash
uv add supabase
```

### Usage Example

```python
from supabase_client import SupabaseClient

# Initialize client
db = SupabaseClient()

# Log a detection
db.log_detection(
    description="witch with purple hat and broom",
    confidence=0.92
)

# Retrieve recent sightings
sightings = db.get_recent_sightings(limit=10)
for s in sightings:
    print(f"{s['description']} at {s['timestamp']}")
```

See `supabase_client.py` for the full helper class.

## Testing the Setup

### 1. Test Database Connection

```bash
uv run python supabase_client.py
```

Expected output:
```
✅ Connected to Supabase: https://xxx.supabase.co
📝 Testing detection logging...
✅ Logged detection: witch with purple hat and broom (confidence: 0.92)
📊 Recent sightings:
  - witch with purple hat and broom (confidence: 0.92, time: 2025-10-26T...)
📈 Total sightings: 1
```

### 2. Verify Realtime

1. Open Supabase dashboard
2. Go to **Table Editor** → **sightings**
3. Keep dashboard open
4. Run the test script: `uv run python supabase_client.py`
5. You should see new rows appear in real-time (no refresh needed)

### 3. Test from Next.js

Once your Next.js dashboard is deployed:
1. Open the dashboard in browser
2. Run test script on Pi: `uv run python supabase_client.py`
3. New detections should appear on dashboard instantly

## Integration with Detection Script

To integrate Supabase into your person detection script:

```python
# In detect_people.py

from supabase_client import SupabaseClient

# Initialize at startup
db = SupabaseClient()

# When person detected with costume classification:
if people_detected:
    # ... existing detection code ...

    # Call Baseten API to get costume description
    costume_description = classify_costume(person_crop)  # Your function

    # Log to Supabase
    db.log_detection(
        description=costume_description,
        confidence=confidence
    )
```

## Troubleshooting

### "Missing Supabase credentials" Error

Make sure your `.env` file has:
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...
```

### "Failed to log detection" Error

1. Check that the migration ran successfully
2. Verify your service key is correct (from Supabase dashboard → Settings → API)
3. Check RLS policies are enabled (should be automatic from migration)

### Realtime Not Working

1. Verify Realtime is enabled:
   - Go to Supabase dashboard → Database → Replication
   - Ensure `sightings` table is in the publication

2. Check browser console for websocket errors

3. Verify anon key is correct in frontend

### "permission denied" on Insert

You might be using the anon key instead of service_role key. The Pi needs the service_role key to insert records.

## Next Steps

1. ✅ Run the migration to create the database
2. ✅ Test the Python client
3. 🔄 Integrate `SupabaseClient` into your detection script
4. 🔄 Build the Next.js dashboard with Realtime subscription
5. 🎃 Ready for Halloween night!

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase Python Client](https://supabase.com/docs/reference/python/introduction)
- [Supabase Realtime Guide](https://supabase.com/docs/guides/realtime)
- [Row Level Security Guide](https://supabase.com/docs/guides/auth/row-level-security)
