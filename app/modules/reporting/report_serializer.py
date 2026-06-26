import json
from app.modules.reporting.report_models import Report
from app.modules.reporting.report_renderer import MarkdownRenderer, HTMLRenderer, JSONRenderer


class ReportSerializer:
    """Handles saving, loading, and formatting exports of Reports."""

    @staticmethod
    def to_json(report: Report) -> str:
        """Serialize a Report model into a formatted JSON string."""
        return JSONRenderer().render(report)

    @staticmethod
    def from_json(json_str: str) -> Report:
        """Deserialize a JSON string back into a Report model."""
        if hasattr(Report, "model_validate_json"):
            return Report.model_validate_json(json_str)
        if hasattr(Report, "parse_raw"):
            return Report.parse_raw(json_str)
            
        data = json.loads(json_str)
        return Report(**data)

    @staticmethod
    def export_markdown(report: Report) -> str:
        """Render and export report as a structured Markdown document."""
        return MarkdownRenderer().render(report)

    @staticmethod
    def export_html(report: Report) -> str:
        """Render and export report as a styled HTML page."""
        return HTMLRenderer().render(report)
