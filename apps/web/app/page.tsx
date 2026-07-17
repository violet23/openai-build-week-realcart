"use client";

import { useEffect, useMemo, useState } from "react";

import {
  type DemoResponse,
  type SecondOpinionResponse,
  loadDemo,
  loadSecondOpinion,
} from "@/lib/api";
import { formatScore } from "@/lib/scoring";

export default function Home() {
  const [demo, setDemo] = useState<DemoResponse | null>(null);
  const [opinion, setOpinion] = useState<SecondOpinionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingOpinion, setLoadingOpinion] = useState(false);

  useEffect(() => {
    loadDemo().then(setDemo).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load the demo");
    });
  }, []);

  const evidence = useMemo(
    () => new Map(demo?.report.evidence.map((item) => [item.id, item.label]) ?? []),
    [demo],
  );

  async function requestOpinion() {
    if (!demo) return;
    setLoadingOpinion(true);
    setError(null);
    try {
      setOpinion(await loadSecondOpinion(demo.candidate));
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to load a second opinion");
    } finally {
      setLoadingOpinion(false);
    }
  }

  return (
    <main>
      <header className="hero">
        <p className="eyebrow">UN-ALGORITHM / FIXTURE DEMO</p>
        <h1>RealCart</h1>
        <p className="tagline">Understand yourself a little better — not to sell you anything.</p>
        <p className="privacy-note">
          This demo uses a synthetic persona. No mailbox, Pinterest account, or personal data is connected.
        </p>
      </header>

      {error ? <div className="error">{error}. Start the API with <code>make dev-api</code>.</div> : null}
      {!demo && !error ? <p className="loading">Building the reflection…</p> : null}

      {demo ? (
        <>
          <section className="report-heading">
            <div>
              <p className="eyebrow">INSIGHT REPORT</p>
              <h2>{demo.report.persona_name}</h2>
              <p>{demo.report.summary}</p>
            </div>
            <div className="score-orbit" aria-label={`Gap score ${demo.report.gap_score} out of 100`}>
              <strong>{demo.report.gap_score}</strong>
              <span>gap score</span>
            </div>
          </section>

          <section className="dimension-grid" aria-label="Taste gap dimensions">
            {demo.report.dimensions.map((dimension) => (
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
            {demo.report.insights.map((insight) => (
              <article key={insight.title}>
                <h3>{insight.title}</h3>
                <p>{insight.body}</p>
                <small>
                  Evidence: {insight.evidence_ids.map((id) => evidence.get(id) ?? id).join(" · ")}
                </small>
              </article>
            ))}
          </section>

          <section className="survey-section">
            <p className="eyebrow">30-SECOND SIGNAL CHECK</p>
            <h2>A purchase is not proof of taste.</h2>
            <div className="survey-grid">
              {demo.survey.map((question) => (
                <fieldset key={question.id}>
                  <legend>{question.question}</legend>
                  <div className="option-row">
                    {question.options.map((option) => (
                      <button type="button" key={option}>{option}</button>
                    ))}
                  </div>
                </fieldset>
              ))}
            </div>
          </section>

          <section className="opinion-section">
            <div>
              <p className="eyebrow">SECOND OPINION</p>
              <h2>{demo.candidate.name}</h2>
              <p>${demo.candidate.price.toFixed(2)} · brought by the user, not recommended by RealCart</p>
            </div>
            <button className="primary-button" type="button" onClick={requestOpinion} disabled={loadingOpinion}>
              {loadingOpinion ? "Reading the signals…" : "Read against my profile"}
            </button>
          </section>

          {opinion ? (
            <section className="opinion-result" aria-live="polite">
              <p>{opinion.reading}</p>
              <div className="opinion-grid">
                {opinion.dimensions.map((dimension) => (
                  <article key={dimension.label}>
                    <strong>{dimension.score}</strong>
                    <h3>{dimension.label}</h3>
                    <p>{dimension.note}</p>
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </>
      ) : null}

      <footer>RealCart reflects signals back to you. The decision remains yours.</footer>
    </main>
  );
}
