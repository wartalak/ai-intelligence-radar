"""
Report and analysis API endpoints.
"""

from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.analysis.report_generator import ReportGenerator
from app.analysis.topic_analyzer import TopicAnalyzer

router = APIRouter()


class TopicRequest(BaseModel):
    query: str


@router.get("/report/today")
async def get_today_report(db: AsyncSession = Depends(get_db)):
    """Return today's AI intelligence report."""
    generator = ReportGenerator(db)
    report = await generator.generate_daily_report(date.today())
    return report


@router.get("/report/{report_date}")
async def get_report_by_date(report_date: str, db: AsyncSession = Depends(get_db)):
    """Return a report for a specific date (YYYY-MM-DD)."""
    try:
        d = date.fromisoformat(report_date)
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DD."}
    generator = ReportGenerator(db)
    report = await generator.generate_daily_report(d)
    return report


@router.post("/analysis/topic")
async def analyze_topic(request: TopicRequest, db: AsyncSession = Depends(get_db)):
    """Generate an AI analysis for a user-specified topic."""
    analyzer = TopicAnalyzer(db)
    analysis = await analyzer.analyze(request.query)
    return analysis
