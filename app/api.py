from pathlib import Path
import sys
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.analysis_service import (
    create_stock_analysis,
    prepare_analysis_view_data,
    run_selected_strategies,
)
from core.persistence import load_analysis_from_file, save_analysis_to_file


app = FastAPI(title="Analytical Trading API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateAnalysisRequest(BaseModel):
    analysis_name: str = Field(min_length=1)
    ticker: str = Field(min_length=1)
    outliers: bool = False


class LoadAnalysisRequest(BaseModel):
    analysis_name: str = Field(min_length=1)


class RunAnalysisRequest(BaseModel):
    analysis_name: str = Field(min_length=1)
    indicator_params: dict[str, list[str]]
    strategy_names: list[str]


class SaveAnalysisRequest(BaseModel):
    analysis_name: str = Field(min_length=1)


def _analysis_filename(analysis_name: str) -> str:
    return f"{analysis_name}.pkl"


def _serialize_frame(frame: pd.DataFrame) -> list[dict[str, Any]]:
    serializable = frame.copy()
    if "Date" in serializable.columns:
        serializable["Date"] = pd.to_datetime(serializable["Date"]).dt.strftime("%Y-%m-%d")
    return serializable.to_dict(orient="records")


def _serialize_analysis(analysis_name: str):
    try:
        analysis = load_analysis_from_file(_analysis_filename(analysis_name))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    analysis_view_data = prepare_analysis_view_data(analysis)
    if analysis_view_data is None:
        raise HTTPException(status_code=500, detail="Could not prepare analysis data.")

    strategies: dict[str, Any] = {}
    for strategy_name, payload in analysis_view_data["strategies_data"].items():
        strategy_frame = payload.get("dataframe")
        stats_frame = payload.get("stats")
        strategies[strategy_name] = {
            "data": _serialize_frame(strategy_frame) if strategy_frame is not None else [],
            "stats": _serialize_frame(stats_frame.reset_index()) if stats_frame is not None else [],
        }

    return {
        "analysis_name": analysis_name,
        "ticker": analysis.name,
        "price_data": _serialize_frame(analysis_view_data["dataframe"]),
        "strategies": strategies,
    }


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/api/analysis/create")
def create_analysis(payload: CreateAnalysisRequest):
    try:
        analysis = create_stock_analysis(
            ticker_symbol=payload.ticker.upper(),
            indicators={"ema": ["5"], "rsi": ["14"]},
            detect_outliers=payload.outliers,
        )
        save_analysis_to_file(analysis, _analysis_filename(payload.analysis_name))
        return _serialize_analysis(payload.analysis_name)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/analysis/load")
def load_analysis(payload: LoadAnalysisRequest):
    return _serialize_analysis(payload.analysis_name)


@app.post("/api/analysis/run")
def run_analysis(payload: RunAnalysisRequest):
    try:
        analysis = load_analysis_from_file(_analysis_filename(payload.analysis_name))
        updated_analysis = run_selected_strategies(
            analysis,
            payload.indicator_params,
            payload.strategy_names,
        )
        save_analysis_to_file(updated_analysis, _analysis_filename(payload.analysis_name))
        return _serialize_analysis(payload.analysis_name)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/analysis/save")
def save_analysis(payload: SaveAnalysisRequest):
    try:
        analysis = load_analysis_from_file(_analysis_filename(payload.analysis_name))
        save_analysis_to_file(analysis, _analysis_filename(payload.analysis_name))
        return {"message": f"Saved {payload.analysis_name}"}
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
