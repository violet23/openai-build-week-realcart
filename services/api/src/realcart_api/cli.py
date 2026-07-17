"""Command-line entry point for running RealCart without a frontend."""

import argparse
import asyncio
from pathlib import Path

from realcart_api.output import render_markdown
from realcart_api.pipeline import (
    PipelineConfigurationError,
    PipelineExecutionError,
    run_pipeline,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch evidence, run RealCart analysis, and emit a report."
    )
    parser.add_argument("--data-mode", choices=("fixture", "live"))
    parser.add_argument("--analysis-mode", choices=("fixture", "agents"))
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser.add_argument("--output", type=Path, help="Optional output file; defaults to stdout.")
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        run = asyncio.run(
            run_pipeline(data_mode=args.data_mode, analysis_mode=args.analysis_mode)
        )
    except (PipelineConfigurationError, PipelineExecutionError) as error:
        parser.error(str(error))
    rendered = (
        run.model_dump_json(indent=2) + "\n"
        if args.format == "json"
        else render_markdown(run)
    )
    if args.output is None:
        print(rendered, end="")
        return
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Wrote {args.format} report to {args.output}")


if __name__ == "__main__":
    main()
