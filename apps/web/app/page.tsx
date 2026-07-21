/* eslint-disable @next/next/no-img-element */
"use client";

import { useEffect, useMemo, useState } from "react";

import {
  type ConnectionOverview,
  type DemoResponse,
  loadConnections,
  loadDemo,
  submitAnalysis,
} from "@/lib/api";
import { formatScore } from "@/lib/scoring";

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "Price not found";
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
  const [connections, setConnections] = useState<ConnectionOverview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [surveyAnswers, setSurveyAnswers] = useState<Record<string, Record<string, string>>>({});
  const [surveyComments, setSurveyComments] = useState<Record<string, string>>({});
  const [surveySaved, setSurveySaved] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    loadConnections().then(setConnections).catch(() => undefined);
    loadDemo().then(setDemo).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Unable to load the analysis");
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
      [itemId]: { ...current[itemId], [promptKey]: answer },
    }));
    setSurveySaved(false);
  }

  function updateSurveyComment(itemId: string, comment: string) {
    setSurveyComments((current) => ({ ...current, [itemId]: comment }));
    setSurveySaved(false);
  }

  async function analyzeSurvey() {
    if (!demo) return;
    setAnalyzing(true);
    setError(null);
    try {
      const answers = demo.survey.map((item) => ({
        item_id: item.item_id,
        values: surveyAnswers[item.item_id] ?? {},
        notes: surveyComments[item.item_id] ?? "",
      }));
      setDemo(await submitAnalysis(answers));
      setSurveySaved(true);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to rerun the analysis");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <main>
      <header className="hero">
        <p className="eyebrow">
          UN-ALGORITHM / {connections?.data_mode === "live" ? "LIVE SOURCES" : "FIXTURE DEMO"}
        </p>
        <h1>RealCart</h1>
        <p className="tagline">Get closer to yourself. Know what you actually like.</p>
        <p className="hero-philosophy">
          RealCart turns your Style World, purchase history, returns, usage and emotional
          feedback into a personal shopping-pattern model. It reveals patterns in your taste
          and behavior you may not have noticed—an overlooked part of yourself worth
          understanding even when you are not shopping.
        </p>
        <p className="privacy-note">
          {connections?.data_mode === "live"
            ? "Live mode reads only the sources you authorize and keeps imported images in a private local cache."
            : "This demo uses a synthetic persona. No mailbox, Pinterest account, or personal data is connected."}
        </p>
      </header>

      {connections ? (
        <section className="connection-panel" aria-label="Data source connections">
          <div>
            <p className="eyebrow">YOUR TWO SIGNAL SOURCES</p>
            <h2>Connect the world you save and the things you bought.</h2>
          </div>
          <div className="connection-grid">
            {connections.sources.map((source) => (
              <article key={source.source}>
                <span className={`connection-status ${source.connected ? "connected" : ""}`}>
                  {source.connected ? "Connected" : source.configured ? "Ready to connect" : "Needs setup"}
                </span>
                <h3>{source.source === "gmail" ? "Gmail purchases" : "Pinterest Style World"}</h3>
                <p>
                  {source.source === "gmail"
                    ? "Order, receipt and return messages, including available product images."
                    : "Sandbox boards and Pin images, interpreted as a vision world—not a wishlist."}
                </p>
                {source.configured && !source.connected ? (
                  <a className="secondary-button" href={source.connect_url}>Connect {source.source}</a>
                ) : null}
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {error ? <div className="error">{error}. Check the API terminal for details.</div> : null}
      {!demo && !error ? <p className="loading">Building the reflection…</p> : null}

      {demo ? (
        <>
          <section className="report-heading">
            <div>
              <p className="eyebrow">SHOPPING-PATTERN MODEL</p>
              <h2>{demo.report.persona_name}</h2>
              <p>{demo.report.summary}</p>
            </div>
            <div className="score-orbit" aria-label={`Style gap ${demo.report.gap_score} out of 100`}>
              <strong>{demo.report.gap_score}</strong>
              <span>style gap</span>
            </div>
          </section>

          {demo.report.portraits.length ? (
            <section className="portrait-section">
              <div>
                <p className="eyebrow">TWO VISUAL SELVES</p>
                <h2>The world that draws you in, beside the life your purchases describe.</h2>
                <p>These are symbolic visual summaries of the evidence—not images of your identity.</p>
              </div>
              <div className="portrait-grid">
                {demo.report.portraits.map((portrait) => (
                  <figure key={portrait.kind}>
                    <img src={portrait.image.image_url} alt={portrait.image.alt_text} />
                    <figcaption>
                      <strong>{portrait.title}</strong>
                      <span>{portrait.generation_mode === "openai" ? `Generated with ${portrait.model}` : "Synthetic demo fixture"}</span>
                    </figcaption>
                  </figure>
                ))}
              </div>
            </section>
          ) : null}

          <section className="vision-profile">
            <div>
              <p className="eyebrow">STYLE WORLD</p>
              <h2>The fashion world you return to.</h2>
              <p>
                Pinterest is a vision board, not a wishlist. RealCart finds the fashion and
                lifestyle signals carried by repeated scenes, colors, textures, forms, and
                atmosphere—only when multiple Pins support them.
              </p>
            </div>
            <div className="vision-theme-grid">
              {demo.report.vision_themes.map((theme) => (
                <article key={theme.name}>
                  <strong>{Math.round(theme.strength * 100)}%</strong>
                  <h3>{theme.name}</h3>
                  <p>{theme.evidence_ids.length} supporting Pins · {Math.round(theme.confidence * 100)}% confidence</p>
                </article>
              ))}
            </div>
          </section>

          <section className="score-provenance" aria-label="How the style gap was calculated">
            <div>
              <p className="eyebrow">HOW THE STYLE GAP WAS CALCULATED</p>
              <h3>Style World and Purchase Reality become one traceable comparison.</h3>
            </div>
            <div className="provenance-flow">
              <span><strong>{demo.report.score_provenance.aspirational_item_count}</strong>Style World Pins</span>
              <b aria-hidden="true">→</b>
              <span><strong>{demo.report.score_provenance.kept_purchase_count}</strong>kept purchases</span>
              <span><strong>{demo.report.score_provenance.returned_item_count}</strong>returned items excluded</span>
              <b aria-hidden="true">→</b>
              <span><strong>{demo.report.gap_score}</strong>style gap</span>
            </div>
            <p className="provenance-note">
              Scenes and atmosphere stay in the narrative. Returns inform behavior patterns but
              do not count as kept-item style. Every insight remains traceable to source IDs.
            </p>
          </section>

          <section className="dimension-grid" aria-label="Style gap dimensions">
            {demo.report.dimensions.map((dimension) => (
              <article className="dimension-card" key={dimension.key}>
                <div className="dimension-title">
                  <h3>{dimension.label}</h3><span>{formatScore(dimension.gap * 100)}</span>
                </div>
                <div className="bar-row"><span>World</span><div className="bar"><i style={{ width: `${dimension.aspiration * 100}%` }} /></div><b>{Math.round(dimension.aspiration * 100)}</b></div>
                <div className="bar-row behavior"><span>Reality</span><div className="bar"><i style={{ width: `${dimension.behavior * 100}%` }} /></div><b>{Math.round(dimension.behavior * 100)}</b></div>
              </article>
            ))}
          </section>

          <section className="insights">
            <p className="eyebrow">WHAT THE SIGNALS SUGGEST</p>
            {demo.report.insights.map((insight) => (
              <article key={insight.title}>
                <h3>{insight.title}</h3><p>{insight.body}</p>
                <small>Evidence: {insight.evidence_ids.map((id) => evidence.get(id) ?? id).join(" · ")}</small>
              </article>
            ))}
          </section>

          <section className="survey-section">
            <div className="survey-heading">
              <div>
                <p className="eyebrow">PURCHASE REALITY CHECK-IN</p>
                <h2>A receipt says you bought it. You tell us what happened next.</h2>
                <p>
                  RealCart pairs order and return records—and their available product images—with
                  a few human signals a receipt cannot provide.
                </p>
              </div>
              <strong>{surveyProgress.answered}/{surveyProgress.total} signals</strong>
            </div>
            <div className="survey-grid">
              {demo.survey.map((item) => (
                <article className="survey-card" key={item.id}>
                  <div className="survey-product">
                    {item.image ? <img src={item.image.image_url} alt={item.image.alt_text} /> : <div className="image-fallback">Product image unavailable</div>}
                    <header className="survey-item-heading">
                      <div><span className="source-chip">Gmail receipt</span><h3>{item.item_name}</h3><p>{item.merchant}</p></div>
                      <strong>{formatCurrency(item.price, item.currency)}</strong>
                    </header>
                  </div>
                  <div className="receipt-facts">
                    <span>Bought <strong>{formatPurchaseDate(item.purchased_at)}</strong></span>
                    <span>Return status <strong>{item.returned ? "Returned" : "Kept"}</strong></span>
                  </div>
                  <div className="survey-prompts">
                    {item.prompts.map((prompt) => (
                      <fieldset key={prompt.id}>
                        <legend>{prompt.question}</legend>
                        <div className="option-row">
                          {prompt.options.map((option) => {
                            const selected = surveyAnswers[item.item_id]?.[prompt.key] === option;
                            return <button aria-pressed={selected} className={selected ? "selected" : undefined} type="button" key={option} onClick={() => selectSurveyAnswer(item.item_id, prompt.key, option)}>{option}</button>;
                          })}
                        </div>
                      </fieldset>
                    ))}
                  </div>
                  <label className="survey-comment">
                    <span>{item.comment_prompt}</span>
                    <textarea maxLength={500} placeholder="Optional — add context a receipt cannot show." rows={3} value={surveyComments[item.item_id] ?? ""} onChange={(event) => updateSurveyComment(item.item_id, event.target.value)} />
                    <small>Optional · {surveyComments[item.item_id]?.length ?? 0}/500</small>
                  </label>
                </article>
              ))}
            </div>
            <div className="survey-actions">
              <p>These answers become evidence for Purchase Reality—not a shopping recommendation.</p>
              <button className="primary-button" type="button" disabled={!surveyProgress.complete || analyzing} onClick={analyzeSurvey}>
                {analyzing ? "Rebuilding your reflection…" : "Add signals and rerun analysis"}
              </button>
            </div>
            {surveySaved ? <p className="survey-confirmation" role="status">The answers were added and the shopping-pattern model was rebuilt for this session.</p> : null}
          </section>
        </>
      ) : null}

      <footer>RealCart reflects the patterns in what draws you in and what became part of your life.</footer>
    </main>
  );
}
