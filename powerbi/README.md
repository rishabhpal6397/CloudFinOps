# CloudFinOps — Power BI

This folder contains the Power BI integration assets for CloudFinOps.

## Quick Start (Windows users)

1. **Generate fresh CSVs** (run in the Codespace, or after pulling the repo):

   ```bash
   python data-engineering/export_for_powerbi.py
   ```

   Outputs land in `data/powerbi/*.csv`.

2. **Get the CSVs to your Windows machine.** Pick one:

   - **Option A (simplest):** Download the `data/powerbi/` folder from GitHub
     (open the repo on github.com → navigate to the folder → **Code → Download ZIP**).
   - **Option B (best for auto-refresh):** Commit and push the CSVs to GitHub,
     then point Power BI at the raw file URLs:
     `https://raw.githubusercontent.com/<user>/CloudFinOps/main/data/powerbi/vw_kpi_summary.csv`

3. **Open Power BI Desktop** on Windows. Follow
   [`documentation/connection_guide.md`](documentation/connection_guide.md).

4. **Paste the DAX measures** from
   [`documentation/dax_measures.md`](documentation/dax_measures.md) into your model.

5. **Build the 7 report pages** following
   [`documentation/page_designs.md`](documentation/page_designs.md).

## Folder Layout

| File | Purpose |
|---|---|
| `README.md` | This file — overview and quick start |
| `documentation/connection_guide.md` | Step-by-step Power BI setup (CSV + live MySQL) |
| `documentation/dax_measures.md` | All DAX measures, ready to paste |
| `documentation/page_designs.md` | 7 report pages with layout descriptions |
| `documentation/data_model.md` | Relationships and model diagram |

## Why not live MySQL by default?

- The Codespace's MySQL listens on `localhost:3306` **inside the container**.
  To reach it from your Windows machine, you'd need to make the port **public**
  in the Codespace's Ports tab — which exposes your dev DB to the internet.
- For a portfolio project, CSV export is safer, faster, and demonstrates the
  same analytics. Live MySQL is documented in the connection guide for users
  who want it.