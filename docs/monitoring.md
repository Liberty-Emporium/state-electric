# State Electric - Monitoring Instructions for Mingo

## Setup (Tomorrow morning, after Tailscale is active)

1. **Copy the monitoring script from the repo:**
   ```bash
   git clone git@github.com:Liberty-Emporium/state-electric.git /home/mingo/state-electric
   cd /home/mingo/state-electric
   ```

2. **Set environment variables:**
   ```bash
   export OFFICE_HOST=<tailscale-ip-of-office-pc>
   export OFFICE_USER=django  # or whatever user they set up
   export OFFICE_FOLDERS="/home/django/Documents:/home/django/Desktop"
   export RAILWAY_URL=https://your-railway-app.up.railway.app
   ```

3. **Install dependencies:**
   ```bash
   pip install paramiko  # for SSH connections
   ```

4. **Test the connection:**
   ```bash
   ping <office-tailscale-ip>
   ssh django@<office-tailscale-ip> "echo connected"
   ```

## Monitoring Schedule

### Phase 1: Active Monitoring (Days 1-14)
Run health checks 3x per day:

| Time | Task |
|------|------|
| 8:00 AM | Check Tailscale connection, app reachable, sync files |
| 12:00 PM | Midday check — any new files? App accessible? |
| 6:00 PM | Evening check — end of business day sync |

Run: `cd /home/mingo/state-electric && python3 scripts/data_sync.py --once`

### Phase 2: Stepping Back (Days 15-30)
Once stable, reduce to 1x per day (8:00 AM only).

### Phase 3: Steady State (Day 31+)
Reduce to 1x per week (Monday 8:00 AM).

### Alert-Only (Day 60+)
Stop active monitoring. Only report if something breaks.

## What to Report

- ✅ OK: Everything connected, no new issues
- ❌ Tailscale down → attempt restart
- ❌ App unreachable → report URL
- ❌ Sync failed → report which files/files
- � New files detected: list them

## Key Contact

Report issues back to Jay via Telegram (the same channel you're using now).
