# CBIO+ Home Visit Register

Pilot build 0.1 of a home visit register for Community Health Workers (CHWs) and Care Group Volunteers (CGVs) in CBIO+ programs. Kenya is the first country configuration.

**Status: pilot build 0.3.** Workers sign in with a name and PIN, records sync through a Supabase database, and each worker sees only her own households (a Care Group Volunteer), her Care Group (a CHW) or everything (the administrator). Use test data only until the hosting location and the data protection requirements are settled and the security has been independently reviewed.

## What it does

- Census form that enrols households, with a short retrospective mortality section (births and deaths in the last 5 years)
- Two visit schedules: 10 scheduled CHW visits per household, and a CGV visit every 2 weeks
- Due lists ordered by urgency and risk (referred, sick, and youngest first)
- Danger-sign checks, referrals and counter-referrals, verbal autopsy with the four delays
- CGV dashboard of healthy practices in her households; CHW-area and administrator dashboards
- Modelled lives saved and DALYs averted (Lives Saved Tool method, simplified), measured mortality, coverage indicators
- Administrator Reports page: programme summary (lives saved and DALYs averted to date), coverage for a chosen period beside the previous period and the baseline, mortality, worker activity, and action lists; each table downloads as a CSV file and the page prints or saves as a PDF
- English and Swahili; works offline once opened

## Files

| File | Purpose |
|---|---|
| `index.html` | The whole app: forms, logic, country configuration, example data generator |
| `sw.js` | Service worker that keeps the app available offline. Change `VERSION` whenever `index.html` changes |
| `manifest.webmanifest`, `icon-*.png` | Let Android install the app on the home screen |

## Publishing with GitHub Pages

1. Repository **Settings → Pages → Build and deployment → Source: Deploy from a branch**.
2. Choose branch `main`, folder `/ (root)`, and save.
3. After a minute the app is at `https://<username>.github.io/<repository>/`.

## Installing on a tablet

1. Open the app address in Chrome while connected.
2. Chrome menu → **Add to Home screen** (or **Install app**).
3. Open it from the home screen. It now works with no connection.

## Example data

Choose **Try it with example data** on the opening screen: 8 CHW areas, 96 CGVs and 1,152 households. Care Group 8 is set up as a newly censused area with no visits. Example records are rebuilt at each start, never stored and never sent to the server.

## Server setup (once)

1. In Supabase, open **SQL Editor**, paste the whole of [`server/setup.sql`](server/setup.sql) and run it. It can be run again safely.
2. Open the app, choose **First-time setup (administrator only)**, and create the administrator. This works once; do it straight after step 1.
3. As administrator, open **Workers** and add each CHW, then her Care Group Volunteers, giving each a sign-in name and a PIN of 6 or more digits.

The project URL and publishable key are set near the top of the script in `index.html` (`SERVER`). Both are public values. The secret key and database password are never used by the app.

## How signing in and syncing work

- The first sign-in on a tablet needs a connection. After that the app opens offline and asks for the PIN each time.
- Records are saved on the tablet first and sent when a connection is available. The newest edit of a record wins.
- The app never touches database tables directly. Every table is locked by Row Level Security; the app calls functions that check the session and the worker's scope.
- Five wrong PINs lock a worker for 15 minutes. The administrator can set a new PIN.
- Signing out removes that worker's records from the tablet. Records not yet sent are lost, and the app warns first.
- **Try it with example data** on the opening screen runs the generated example (8 CHW areas, 1,152 households) and never contacts the server.

## Testing

`server/setup.sql` and the app were tested end to end against an in-process PostgreSQL that imitates the Supabase function interface: several simulated tablets, scope checks, offline entry and later sync. They have not yet been exercised by an independent reviewer.

## Next stage

- SMS alert to the CHW when a volunteer records a danger sign
- Additional languages, and review of the Swahili text by a native speaker
- Review of the model parameters against the current Lives Saved Tool
- Independent security review; hosting that meets Kenya's data protection rules

## Sources for the Kenya defaults

Baseline mortality and coverage: Kenya Demographic and Health Survey 2022. Maternal mortality: 2019 census. Effect sizes: published Lives Saved Tool reviews (cited on the Model page). Values marked "assumed" on the Model page have no national source and should be replaced with project baseline data.
