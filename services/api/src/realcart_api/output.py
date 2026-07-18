"""Human-readable output rendering for pipeline runs."""

from realcart_api.schemas import AnalysisRun


def render_markdown(run: AnalysisRun) -> str:
    report = run.report
    runtime = run.model_runtime
    lines = [
        f"# RealCart Shopping-Pattern Report: {report.persona_name}",
        "",
        f"**Style gap:** {report.gap_score}/100",
        "",
        report.summary,
        "",
        "## Runtime",
        "",
        f"- **Data:** {run.data_mode}",
        f"- **Analysis:** {run.analysis_mode}",
        f"- **Provider:** {runtime.provider}",
    ]
    if runtime.specialist_model is not None:
        lines.append(
            f"- **Specialists:** {runtime.specialist_model} "
            f"({runtime.specialist_reasoning_effort} reasoning)"
        )
    if runtime.synthesis_model is not None:
        lines.append(
            f"- **Synthesis:** {runtime.synthesis_model} "
            f"({runtime.synthesis_reasoning_effort} reasoning)"
        )
    if runtime.trace_id is not None:
        lines.append(f"- **Trace ID:** `{runtime.trace_id}`")
    lines.extend(
        [
        "",
        "## Style-gap provenance",
        "",
        f"- **Synthetic vision-board pins:** {report.score_provenance.aspirational_item_count}",
        f"- **Synthetic purchases:** {report.score_provenance.purchase_item_count}",
        f"- **Kept purchases in Purchase Reality:** {report.score_provenance.kept_purchase_count}",
        f"- **Returned purchases excluded:** {report.score_provenance.returned_item_count}",
        f"- **Profile method:** {report.score_provenance.profile_method}",
        ]
    )
    lines.extend(["", "## Style World themes", ""])
    lines.extend(
        f"- **{theme.name}:** {round(theme.strength * 100)}% strength, "
        f"{round(theme.confidence * 100)}% confidence "
        f"(evidence: {', '.join(theme.evidence_ids)})"
        for theme in report.vision_themes
    )
    lines.extend(
        [
            "",
            "## Dimensions",
            "",
            "| Dimension | Style World | Purchase Reality | Gap |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    lines.extend(
        f"| {item.label} | {item.aspiration:.2f} | {item.behavior:.2f} | {item.gap:.2f} |"
        for item in report.dimensions
    )
    lines.extend(["", "## Grounded insights", ""])
    for insight in report.insights:
        evidence = ", ".join(insight.evidence_ids)
        lines.extend(
            [
                f"### {insight.title}",
                "",
                insight.body,
                "",
                f"Evidence: `{evidence}`",
                "",
            ]
        )
    lines.extend(["## Pipeline", ""])
    lines.extend(f"- **{stage.name}:** {stage.detail}" for stage in run.stages)
    return "\n".join(lines).rstrip() + "\n"
