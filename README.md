# New Analytical Trading

## Project structure

- `app/dashboard.py` — Streamlit UI entrypoint.
- `core/analysis_models.py` — domain classes (`StockAnalyser`, `Strategiser`).
- `core/analysis_service.py` — orchestration/service helpers used by UI.
- `core/persistence.py` — save/load helpers.
- `core/plotting.py` — chart rendering helpers.

## Run

```bash
streamlit run app/dashboard.py
```

If Streamlit is executed from different working directories, `app/dashboard.py` now adds the repository root to `sys.path` automatically, so `core.*` imports resolve reliably.
