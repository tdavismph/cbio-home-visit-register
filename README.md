# CBIO+ Home Visit Register

Pilot build 0.1 of a home visit register for Community Health Workers (CHWs) and Care Group Volunteers (CGVs) in CBIO+ programs. Kenya is the first country configuration.

**Status: training build.** Records are stored on each tablet only. There are no worker logins and no syncing between tablets yet. Do not enter real families' data until the server stage is complete and the data protection requirements are settled.

## What it does

- Census form that enrols households, with a short retrospective mortality section (births and deaths in the last 5 years)
- Two visit schedules: 10 scheduled CHW visits per household, and a CGV visit every 2 weeks
- Due lists ordered by urgency and risk (referred, sick, and youngest first)
- Danger-sign checks, referrals and counter-referrals, verbal autopsy with the four delays
- CGV dashboard of healthy practices in her households; CHW-area and administrator dashboards
- Modelled lives saved and DALYs averted (Lives Saved Tool method, simplified), measured mortality, coverage indicators
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

The app opens with generated example data: 8 CHW areas, 96 CGVs and 1,152 households. Care Group 8 is set up as a newly censused area with no visits. Example records are rebuilt at each start and never stored. **Settings → Remove example data** clears them; workers are then added under **Workers** in the administrator view.

## Next stage

- Managed database, worker logins with PINs, and syncing between tablets
- Access limited to each worker's own households
- SMS alert to the CHW when a CGV records a danger sign
- Additional languages
- Review of the Swahili text by a native speaker, and of the model parameters against the current Lives Saved Tool

## Sources for the Kenya defaults

Baseline mortality and coverage: Kenya Demographic and Health Survey 2022. Maternal mortality: 2019 census. Effect sizes: published Lives Saved Tool reviews (cited on the Model page). Values marked "assumed" on the Model page have no national source and should be replaced with project baseline data.
