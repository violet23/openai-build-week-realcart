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

type TabId = "overview" | "signals" | "check-in" | "comparison";

const tabs: { id: TabId; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "signals", label: "Signals" },
  { id: "check-in", label: "Check-in" },
  { id: "comparison", label: "Comparison" },
];

function neutralizeCopy(value: string) {
  return value
    .replaceAll("Style World", "Saved Style Signals")
    .replaceAll("Purchase Reality", "Purchase Patterns")
    .replaceAll("Style Gap", "Signal Distance")
    .replaceAll("style gap", "signal distance");
}

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
  const [activeTab, setActiveTab] = useState<TabId>("overview");

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
      setActiveTab("comparison");
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
        <p className="tagline">Notice what draws you in—and what becomes part of your life.</p>
        <p className="hero-philosophy">
          RealCart compares saved visual signals with purchase history, returns, usage and
          emotional feedback. Both are partial: saved images show attention and imagination;
          purchases also reflect need, budget, fit, availability and circumstance.
        </p>
        <p className="framing-note">
          <strong>Neither source is the “real you.”</strong> The comparison describes patterns
          between two kinds of evidence—it does not rank one as better or more authentic.
        </p>
        <p className="privacy-note">
          {connections?.data_mode === "live"
            ? "Live mode reads only the sources you authorize and keeps imported images in a private local cache."
            : "This demo uses a synthetic persona. No mailbox, Pinterest account, or personal data is connected."}
        </p>
      </header>

      {error ? <div className="error">{error}. Check the API terminal for details.</div> : null}
      {!demo && !error ? <p className="loading">Building the reflection…</p> : null}

      {demo ? (
        <div className="tab-shell">
          <nav className="tab-list" role="tablist" aria-label="RealCart report sections">
            {tabs.map((tab) => (
              <button
                aria-controls={`panel-${tab.id}`}
                aria-selected={activeTab === tab.id}
                className={activeTab === tab.id ? "active" : undefined}
                id={`tab-${tab.id}`}
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                role="tab"
                type="button"
              >
                {tab.label}
                {tab.id === "check-in" ? ` ${surveyProgress.answered}/${surveyProgress.total}` : ""}
              </button>
            ))}
          </nav>

          <div
            aria-labelledby={`tab-${activeTab}`}
            className="tab-panel"
            id={`panel-${activeTab}`}
            role="tabpanel"
          >
            {activeTab === "overview" ? (
              <>
                <section className="report-heading">
                  <div>
                    <p className="eyebrow">SHOPPING-PATTERN MODEL</p>
                    <h2>{demo.report.persona_name}</h2>
                    <p>{neutralizeCopy(demo.report.summary)}</p>
                  </div>
                  <div
                    className="score-orbit"
                    aria-label={`Signal distance ${demo.report.gap_score} out of 100`}
                  >
                    <strong>{demo.report.gap_score}</strong>
                    <span>signal distance</span>
                  </div>
                </section>
                <aside className="interpretation-note">
                  <strong>A distance is not a grade.</strong> A higher number means these two
                  evidence sets differ more across the measured dimensions. It does not mean the
                  saved world is better, or that purchases reveal a truer self.
                </aside>
                {demo.report.portraits.length ? (
                  <section className="portrait-section">
                    <div>
                      <p className="eyebrow">TWO SIGNAL PORTRAITS</p>
                      <h2>Two partial views, placed side by side without ranking either one.</h2>
                      <p>These are symbolic summaries of evidence—not images of identity.</p>
                    </div>
                    <div className="portrait-grid">
                      {demo.report.portraits.map((portrait) => (
                        <figure key={portrait.kind}>
                          <img src={portrait.image.image_url} alt={portrait.image.alt_text} />
                          <figcaption>
                            <strong>
                              {portrait.kind === "style_world"
                                ? "Saved Style Signals"
                                : "Purchase Patterns"}
                            </strong>
                            <span>
                              {portrait.generation_mode === "openai"
                                ? `Generated with ${portrait.model}`
                                : "Synthetic demo fixture"}
                            </span>
                          </figcaption>
                        </figure>
                      ))}
                    </div>
                  </section>
                ) : null}
              </>
            ) : null}

            {activeTab === "signals" ? (
              <>
                {connections ? (
                  <section className="connection-panel" aria-label="Data source connections">
                    <div>
                      <p className="eyebrow">TWO INCOMPLETE SIGNAL SOURCES</p>
                      <h2>Saved attention and shopping behavior offer different context.</h2>
                    </div>
                    <div className="connection-grid">
                      {connections.sources.map((source) => (
                        <article key={source.source}>
                          <span className={`connection-status ${source.connected ? "connected" : ""}`}>
                            {source.connected ? "Connected" : source.configured ? "Ready to connect" : "Needs setup"}
                          </span>
                          <h3>{source.source === "gmail" ? "Purchase records" : "Saved visual references"}</h3>
                          <p>
                            {source.source === "gmail"
                              ? "Orders and returns reflect preference plus budget, function, fit, timing and availability."
                              : "Repeated images reveal visual attention—not desire, intent, an ideal self, or a wishlist."}
                          </p>
                          {source.configured && !source.connected ? (
                            <a className="secondary-button" href={source.connect_url}>Connect {source.source}</a>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  </section>
                ) : null}
                <section className="vision-profile">
                  <div>
                    <p className="eyebrow">SAVED STYLE SIGNALS</p>
                    <h2>Patterns in the visual world that repeatedly holds your attention.</h2>
                    <p>
                      RealCart looks for repeated scenes, colors, textures, forms and atmosphere.
                      A saved image is evidence of attention, not proof that the person wants to
                      own it or live exactly that way.
                    </p>
                  </div>
                  <div className="vision-theme-grid">
                    {demo.report.vision_themes.map((theme) => (
                      <article key={theme.name}>
                        <strong>{Math.round(theme.strength * 100)}%</strong>
                        <h3>{theme.name}</h3>
                        <p>{theme.evidence_ids.length} supporting saves · {Math.round(theme.confidence * 100)}% confidence</p>
                      </article>
                    ))}
                  </div>
                </section>
              </>
            ) : null}

            {activeTab === "check-in" ? (
              <section className="survey-section">
            <div className="survey-heading">
              <div>
                <p className="eyebrow">PURCHASE CONTEXT CHECK-IN</p>
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
              <p>These answers add context to purchase patterns. They are not a shopping recommendation or a judgment.</p>
              <button className="primary-button" type="button" disabled={!surveyProgress.complete || analyzing} onClick={analyzeSurvey}>
                {analyzing ? "Rebuilding your reflection…" : "Add signals and rerun analysis"}
              </button>
            </div>
            {surveySaved ? <p className="survey-confirmation" role="status">The answers were added and the shopping-pattern model was rebuilt for this session.</p> : null}
              </section>
            ) : null}

            {activeTab === "comparison" ? (
              <>
                <section className="score-provenance" aria-label="How signal distance was calculated">
                  <div>
                    <p className="eyebrow">HOW SIGNAL DISTANCE WAS CALCULATED</p>
                    <h3>Saved style signals and kept-purchase signals become one neutral comparison.</h3>
                  </div>
                  <div className="provenance-flow">
                    <span><strong>{demo.report.score_provenance.aspirational_item_count}</strong>saved references</span>
                    <b aria-hidden="true">→</b>
                    <span><strong>{demo.report.score_provenance.kept_purchase_count}</strong>kept purchases</span>
                    <span><strong>{demo.report.score_provenance.returned_item_count}</strong>returns kept as context</span>
                    <b aria-hidden="true">→</b>
                    <span><strong>{demo.report.gap_score}</strong>signal distance</span>
                  </div>
                  <p className="provenance-note">
                    Returns inform the pattern but are excluded from the kept-item profile. The
                    score measures difference, not quality, authenticity, discipline or buying power.
                  </p>
                </section>
                <section className="dimension-grid" aria-label="Signal distance dimensions">
                  {demo.report.dimensions.map((dimension) => (
                    <article className="dimension-card" key={dimension.key}>
                      <div className="dimension-title">
                        <h3>{dimension.label}</h3><span>{formatScore(dimension.gap * 100)}</span>
                      </div>
                      <div className="bar-row"><span>Saved</span><div className="bar"><i style={{ width: `${dimension.aspiration * 100}%` }} /></div><b>{Math.round(dimension.aspiration * 100)}</b></div>
                      <div className="bar-row behavior"><span>Bought</span><div className="bar"><i style={{ width: `${dimension.behavior * 100}%` }} /></div><b>{Math.round(dimension.behavior * 100)}</b></div>
                    </article>
                  ))}
                </section>
                <section className="insights">
                  <p className="eyebrow">WHAT THE SIGNALS SUGGEST</p>
                  {demo.report.insights.map((insight) => (
                    <article key={insight.title}>
                      <h3>{neutralizeCopy(insight.title)}</h3><p>{neutralizeCopy(insight.body)}</p>
                      <small>Evidence: {insight.evidence_ids.map((id) => evidence.get(id) ?? id).join(" · ")}</small>
                    </article>
                  ))}
                </section>
              </>
            ) : null}
          </div>
        </div>
      ) : null}

      <footer>Neither source is your “real self.” RealCart reflects relationships between signals.</footer>
    </main>
  );
}
