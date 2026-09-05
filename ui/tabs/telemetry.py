"""Zakładka „Telemetria” — przebiegi kanałów i delta czasu."""

from __future__ import annotations

from f1tele.pipeline import AnalysisResult

from ..components import chart, empty_module, subheader


def render(result: AnalysisResult) -> None:
    drawn = chart(result.figures.get("telemetry"))

    if "delta_time" in result.figures:
        subheader("Delta czasu")
        drawn = chart(result.figures["delta_time"]) or drawn

    if not drawn:
        empty_module("Telemetria")
