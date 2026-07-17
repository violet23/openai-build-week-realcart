"use client";

import { useEffect, useMemo, useState } from "react";

import { type AnalysisRun, loadAnalysisRun } from "@/lib/api";
import { formatScore } from "@/lib/scoring";

export default function Home() {
  const [run, setRun] = useState<AnalysisRun | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshReport() {
    setLoading(true);
    setError(null);
    try {
      setRun(await loadAnalysisRun());
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to load the report");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    let active = true;
    loadAnalysisRun()
      .then((result) => {
        if (active) setRun(result);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "Unable to load the report");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const evidence = useMemo(
    () => new Map(run?.report.evidence.map((item) => [item.id, item.label]) ?? []),
    [run],
  );

  return (
    <main>
      <header className="hero">
        <p className="eyebrow">UN-ALGORITHM / REPORT VIEWER</p>
        <h1>RealCart</h1>
        <p className="tagline">Understand yourself a little better — not to sell you anything.</p>
        <div className="toolbar">
          <p className="privacy-note">
            Fixture mode uses synthetic Pinterest and Gmail signals. No personal account is connected.
          </p>
          <button className="secondary-button" type="button" onClick={refreshReport} disabled={loading}>
            {loading ? "Loading…" : "Refresh report"}
          </button>
        </div>
      </header>

      {error ? (
        <section className="error" role="alert">
          <strong>Report unavailable.</strong> {error}. Start the backend with <code>make dev-api</code>,
          then try again.
        </section>
      ) : null}
      {loading && !run ? <p className="loading">Building the reflection…</p> : null}

      {run ? (
        <>
          <section className="report-heading">
            <div>
              <p className="eyebrow">INSIGHT REPORT</p>
              <h2>{run.report.persona_name}</h2>
              <p>{run.report.summary}</p>
              <div className="mode-row">
                <span>Data: {run.data_mode}</span>
                <span>Analysis: {run.analysis_mode}</span>
              </div>
            </div>
            <div className="score-orbit" aria-label={`Gap score ${run.report.gap_score} out of 100`}>
              <strong>{run.report.gap_score}</strong>
              <span>gap score</span>
            </div>
          </section>

          <section className="dimension-grid" aria-label="Taste gap dimensions">
            {run.report.dimensions.map((dimension) => (
              <article className="dimension-card" key={dimension.key}>
                <div className="dimension-title">
                  <h3>{dimension.label}</h3>
                  <span>{formatScore(dimension.gap * 100)}</span>
                </div>
                <div className="bar-row">
                  <span>Saved</span>
                  <div className="bar"><i style={{ width: `${dimension.aspiration * 100}%` }} /></div>
                  <b>{Math.round(dimension.aspiration * 100)}</b>
                </div>
                <div className="bar-row behavior">
                  <span>Bought</span>
                  <div className="bar"><i style={{ width: `${dimension.behavior * 100}%` }} /></div>
                  <b>{Math.round(dimension.behavior * 100)}</b>
                </div>
              </article>
            ))}
          </section>

          <section className="insights">
            <p className="eyebrow">WHAT THE SIGNALS SUGGEST</p>
            {run.report.insights.map((insight) => (
              <article key={insight.title}>
                <h3>{insight.title}</h3>
                <p>{insight.body}</p>
                <small>
                  Evidence: {insight.evidence_ids.map((id) => evidence.get(id) ?? id).join(" · ")}
                </small>
              </article>
            ))}
          </section>

          <div className="detail-grid">
            <section className="evidence-section">
              <p className="eyebrow">EVIDENCE USED</p>
              <ul>
                {run.report.evidence.map((item) => (
                  <li key={item.id}>
                    <span>{item.label}</span>
                    <small>{item.source.replaceAll("_", " ")}</small>
                  </li>
                ))}
              </ul>
            </section>

            <section className="pipeline-section">
              <p className="eyebrow">PIPELINE STATUS</p>
              <ol>
                {run.stages.map((stage) => (
                  <li key={stage.name}>
                    <span aria-hidden="true">✓</span>
                    <div>
                      <strong>{stage.name.replaceAll("_", " ")}</strong>
                      <p>{stage.detail}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          </div>
        </>
      ) : null}

      <footer>RealCart reflects evidence-backed signals. The interpretation remains yours.</footer>
    </main>
  );
}
