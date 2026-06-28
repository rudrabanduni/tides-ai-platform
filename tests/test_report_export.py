import os
import time
import tempfile
import pytest
from app.modules.reporting import ReportBuilder, ReportExporter
from tests.test_report_builder import complex_graph


def test_json_export(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        ReportExporter.export_to_json(report, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        os.unlink(tmp_path)


def test_markdown_export(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        ReportExporter.export_to_markdown(report, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Due Diligence Report" in content
            assert "Investment Summary" in content
    finally:
        os.unlink(tmp_path)


def test_html_export(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        ReportExporter.export_to_html(report, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "<html>" in content
            assert "Due Diligence Report" in content
    finally:
        os.unlink(tmp_path)


def test_pdf_export(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        ReportExporter.export_to_pdf(report, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        os.unlink(tmp_path)


def test_docx_export(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        ReportExporter.export_to_docx(report, tmp_path)
        assert os.path.exists(tmp_path)
        assert os.path.getsize(tmp_path) > 0
    finally:
        os.unlink(tmp_path)


def test_large_report_performance(complex_graph):
    """Enforces SLA limits: Report generation <500 ms, Export <1 s."""
    # 1. Measure Generation Duration
    start_time = time.perf_counter()
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    gen_duration = (time.perf_counter() - start_time) * 1000.0
    
    assert gen_duration < 500.0, f"Report generation exceeded 500 ms SLA: {gen_duration:.2f} ms"

    # 2. Measure PDF Export Duration (typically the slowest format)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        start_time = time.perf_counter()
        ReportExporter.export_to_pdf(report, tmp_path)
        export_duration = (time.perf_counter() - start_time) * 1000.0
        
        assert export_duration < 1000.0, f"Report export exceeded 1000 ms SLA: {export_duration:.2f} ms"
    finally:
        os.unlink(tmp_path)
