"""Human-readable output rendering for pipeline runs."""

from realcart_api.schemas import AnalysisRun


def render_markdown(run: AnalysisRun) -> str:
    report = run.report
    runtime = run.model_runtime
    lines = [
        f"# RealCart Insight Report: {report.persona_name}",
        "",
        f"**Gap score:** {report.gap_score}/100",
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
        "## Score provenance",
        "",
        f"- **Synthetic Pinterest saves:** {report.score_provenance.aspirational_item_count}",
        f"- **Synthetic purchases:** {report.score_provenance.purchase_item_count}",
        f"- **Kept purchases in behavior profile:** {report.score_provenance.kept_purchase_count}",
        f"- **Returned purchases excluded:** {report.score_provenance.returned_item_count}",
        f"- **Profile method:** {report.score_provenance.profile_method}",
        "",
        "## Dimensions",
        "",
        "| Dimension | Aspiration | Behavior | Gap |",
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
