"use client";

import { useEffect, useMemo, useState } from "react";

import {
  type DemoResponse,
  type SecondOpinionResponse,
  loadDemo,
  loadSecondOpinion,
} from "@/lib/api";
import { formatScore } from "@/lib/scoring";

function formatCurrency(value: number, currency: string) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPurchaseDate(value: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

export default function Home() {
  const [demo, setDemo] = useState<DemoResponse | null>(null);
  const [opinion, setOpinion] = useState<SecondOpinionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadingOpinion, setLoadingOpinion] = useState(false);
  const [surveyAnswers, setSurveyAnswers] = useState<Record<string, Record<string, string>>>({});
  const [surveyComments, setSurveyComments] = useState<Record<string, string>>({});
  const [surveySaved, setSurveySaved] = useState(false);

  useEffect(() => {
    loadDemo().then(setDemo).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load the demo");
    });
  }, []);

  const evidence = useMemo(
    () => new Map(demo?.report.evidence.map((item) => [item.id, item.label]) ?? []),
    [demo],
  );

  const surveyProgress = useMemo(() => {
    const total = demo?.survey.reduce((count, item) => count + item.prompts.length, 0) ?? 0;
    const answered = Object.values(surveyAnswers).reduce(
      (count, answers) => count + Object.keys(answers).length,
      0,
    );
    return { answered, total, complete: total > 0 && answered === total };
  }, [demo, surveyAnswers]);

  function selectSurveyAnswer(itemId: string, promptKey: string, answer: string) {
    setSurveyAnswers((current) => ({
      ...current,
      [itemId]: {
        ...current[itemId],
        [promptKey]: answer,
      },
    }));
    setSurveySaved(false);
  }

  function updateSurveyComment(itemId: string, comment: string) {
    setSurveyComments((current) => ({ ...current, [itemId]: comment }));
    setSurveySaved(false);
  }

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

          <section className="score-provenance" aria-label="How the gap score was calculated">
            <div>
              <p className="eyebrow">HOW THIS SCORE WAS CALCULATED</p>
              <h3>Individual signals become two profiles, then one gap.</h3>
            </div>
            <div className="provenance-flow">
              <span>
                <strong>{demo.report.score_provenance.aspirational_item_count}</strong>
                synthetic Pinterest saves
              </span>
              <b aria-hidden="true">→</b>
              <span>
                <strong>{demo.report.score_provenance.kept_purchase_count}</strong>
                kept Gmail purchases
              </span>
              <span>
                <strong>{demo.report.score_provenance.returned_item_count}</strong>
                returned item excluded
              </span>
              <b aria-hidden="true">→</b>
              <span>
                <strong>{demo.report.gap_score}</strong>
                average dimension gap
              </span>
            </div>
            <p className="provenance-note">
              Item-level style scores are hand-authored for Maya. RealCart calculates both
              profiles and the final score automatically. Returns inform regret patterns but do
              not count as everyday behavior.
            </p>
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
            <div className="survey-heading">
              <div>
                <p className="eyebrow">GMAIL RECEIPT CHECK-IN</p>
                <h2>A receipt says you bought it. You tell us what happened next.</h2>
                <p>
                  RealCart pairs order and return records with a few human signals: how the item
                  feels now, whether it became part of your life, and what drove the decision.
                </p>
              </div>
              <strong>{surveyProgress.answered}/{surveyProgress.total} signals</strong>
            </div>
            <div className="survey-grid">
              {demo.survey.map((item) => (
                <article className="survey-card" key={item.id}>
                  <header className="survey-item-heading">
                    <div>
                      <span className="source-chip">Gmail receipt</span>
                      <h3>{item.item_name}</h3>
                      <p>{item.merchant}</p>
                    </div>
                    <strong>{formatCurrency(item.price, item.currency)}</strong>
                  </header>

                  <div className="receipt-facts">
                    <span>
                      Bought <strong>{formatPurchaseDate(item.purchased_at)}</strong>
                    </span>
                    <span>
                      Return status <strong>{item.returned ? "Returned" : "Kept"}</strong>
                    </span>
                  </div>

                  <div className="survey-prompts">
                    {item.prompts.map((prompt) => (
                      <fieldset key={prompt.id}>
                        <legend>{prompt.question}</legend>
                        <div className="option-row">
                          {prompt.options.map((option) => {
                            const selected = surveyAnswers[item.item_id]?.[prompt.key] === option;
                            return (
                              <button
                                aria-pressed={selected}
                                className={selected ? "selected" : undefined}
                                type="button"
                                key={option}
                                onClick={() => selectSurveyAnswer(item.item_id, prompt.key, option)}
                              >
                                {option}
                              </button>
                            );
                          })}
                        </div>
                      </fieldset>
                    ))}
                  </div>

                  <label className="survey-comment">
                    <span>{item.comment_prompt}</span>
                    <textarea
                      maxLength={500}
                      placeholder="Optional — add context a receipt cannot show."
                      rows={3}
                      value={surveyComments[item.item_id] ?? ""}
                      onChange={(event) => updateSurveyComment(item.item_id, event.target.value)}
                    />
                    <small>Optional · {surveyComments[item.item_id]?.length ?? 0}/500</small>
                  </label>
                </article>
              ))}
            </div>

            <div className="survey-actions">
              <p>
                These answers become evidence for the Purchase Signal Agent—not a shopping
                recommendation.
              </p>
              <button
                className="primary-button"
                type="button"
                disabled={!surveyProgress.complete}
                onClick={() => setSurveySaved(true)}
              >
                Add signals to Maya&apos;s profile
              </button>
            </div>
            {surveySaved ? (
              <p className="survey-confirmation" role="status">
                Added for this demo session. A live build would save these responses and rerun the
                Taste Gap report.
              </p>
            ) : null}
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
