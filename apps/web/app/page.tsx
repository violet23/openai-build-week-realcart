/* eslint-disable @next/next/no-img-element */
"use client";

import { useEffect, useMemo, useState, type FormEvent } from "react";

import { type DemoResponse, loadDemo, submitAnalysis } from "@/lib/api";
import { formatScore } from "@/lib/scoring";

type DetailTab = "refine" | "analysis";

function neutralizeCopy(value: string) {
  return value
    .replaceAll("Style World", "Style Reference")
    .replaceAll("Purchase Reality", "Shopping History")
    .replaceAll("Style Gap", "Pattern Difference")
    .replaceAll("style gap", "pattern difference");
}

function formatCurrency(value: number | null, currency: string) {
  if (value === null) return "Price unavailable";
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

function withRevision(url: string, revision: number) {
  if (!revision) return url;
  return `${url}${url.includes("?") ? "&" : "?"}revision=${revision}`;
}

export default function Home() {
  const [demo, setDemo] = useState<DemoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [profileReady, setProfileReady] = useState(false);
  const [activeTab, setActiveTab] = useState<DetailTab | null>(null);
  const [profile, setProfile] = useState({
    username: "Maya",
    pinterest: "@maya-style-demo",
    gmail: "maya.shopping@example.com",
  });
  const [surveyAnswers, setSurveyAnswers] = useState<Record<string, Record<string, string>>>({});
  const [surveyComments, setSurveyComments] = useState<Record<string, string>>({});
  const [surveySaved, setSurveySaved] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisRevision, setAnalysisRevision] = useState(0);

  useEffect(() => {
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

  const insightBubbles = useMemo(() => {
    if (!demo) return [];
    const report = demo.report;
    const returnRate = report.score_provenance.purchase_item_count
      ? Math.round(
          (report.score_provenance.returned_item_count /
            report.score_provenance.purchase_item_count) *
            100,
        )
      : 0;
    const returnedItem = demo.survey.find((item) => item.returned);
    const keptItem = demo.survey.find((item) => !item.returned);
    const prices = demo.survey
      .filter((item) => item.price !== null)
      .map((item) => item.price as number);
    const strongestDifference = [...report.dimensions].sort((a, b) => b.gap - a.gap)[0];
    const surveySignals = Object.values(surveyAnswers).flatMap((values) => Object.values(values));

    return [
      {
        tone: "return",
        metric: `${returnRate}%`,
        title: "returned",
        body: `${report.score_provenance.returned_item_count} of ${report.score_provenance.purchase_item_count} purchases`,
      },
      returnedItem
        ? {
            tone: "match",
            metric: formatCurrency(returnedItem.price, returnedItem.currency),
            title: "style match returned",
            body: `${returnedItem.item_name} matched warm + structured references.`,
          }
        : null,
      prices.length
        ? {
            tone: "price",
            metric: `${formatCurrency(Math.min(...prices), "USD")}–${formatCurrency(Math.max(...prices), "USD")}`,
            title: "surveyed price range",
            body: returnedItem?.price
              ? "Highest-priced surveyed item was returned."
              : "Tracked with use, feeling, and returns.",
          }
        : null,
      keptItem && returnedItem
        ? {
            tone: "brand",
            metric: "0",
            title: "confirmed favorite brands",
            body: `${keptItem.merchant}: kept · ${returnedItem.merchant}: returned`,
          }
        : null,
      strongestDifference
        ? {
            tone: "difference",
            metric: `${Math.round(strongestDifference.gap * 100)} pts`,
            title: `${strongestDifference.label} differs most`,
            body: `History ${Math.round(strongestDifference.behavior * 100)} · Reference ${Math.round(strongestDifference.aspiration * 100)}`,
          }
        : null,
      {
        tone: "reference",
        metric: `${Math.min(3, report.vision_themes.length)}`,
        title: "top reference themes",
        body: report.vision_themes
          .slice(0, 3)
          .map((theme) => theme.name.toLowerCase())
          .join(" · "),
      },
      surveySaved && surveySignals.length
        ? {
            tone: "survey",
            metric: `${surveySignals.length}`,
            title: "survey signals added",
            body: surveySignals.join(" · "),
          }
        : null,
    ].filter(
      (item): item is { tone: string; metric: string; title: string; body: string } =>
        item !== null,
    );
  }, [demo, surveyAnswers, surveySaved]);

  function generateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileReady(true);
    setActiveTab(null);
    setAnalysisRevision((current) => current + 1);
  }

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
      setAnalysisRevision((current) => current + 1);
      setActiveTab("analysis");
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to rerun the analysis");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <main>
      <header className="hero compact-hero">
        <p className="eyebrow">REALCART / SHOPPING PATTERN REFLECTION</p>
        <h1>RealCart</h1>
        <p className="tagline">See what you buy, keep, use, return—and what may be shaping it.</p>
      </header>

      <form className="profile-form" onSubmit={generateProfile}>
        <div className="profile-form-heading">
          <div>
            <p className="eyebrow">BUILD YOUR PROFILE</p>
            <h2>Connect your shopping history and style reference.</h2>
          </div>
          <p>For this demo, these fields label a synthetic profile. No account is contacted.</p>
        </div>
        <div className="profile-fields">
          <label>
            <span>Your name</span>
            <input
              required
              value={profile.username}
              onChange={(event) => setProfile({ ...profile, username: event.target.value })}
            />
          </label>
          <label>
            <span>Pinterest account</span>
            <input
              required
              value={profile.pinterest}
              onChange={(event) => setProfile({ ...profile, pinterest: event.target.value })}
            />
          </label>
          <label>
            <span>Gmail shopping account</span>
            <input
              required
              type="email"
              value={profile.gmail}
              onChange={(event) => setProfile({ ...profile, gmail: event.target.value })}
            />
          </label>
          <button className="primary-button" disabled={!demo} type="submit">
            {profileReady ? "Regenerate profile" : "Generate my profile"}
          </button>
        </div>
      </form>

      {error ? <div className="error">{error}. Check the API terminal for details.</div> : null}
      {!demo && !error ? <p className="loading">Reading the demo signals…</p> : null}

      {demo && profileReady ? (
        <>
          <section className="profile-result">
            <div className="result-intro">
              <div>
                <p className="eyebrow">{profile.username.toUpperCase()} / PROFILE {analysisRevision}</p>
                <h2>Two views of one shopping pattern.</h2>
              </div>
              <p>
                Shopping history leads the behavioral analysis. Saved images provide style
                context—not proof of what you should own.
              </p>
            </div>
            <div className="portrait-grid portrait-grid-featured">
              {demo.report.portraits.map((portrait) => (
                <figure key={portrait.kind}>
                  <div className="portrait-image-wrap">
                    <img
                      src={withRevision(portrait.image.image_url, analysisRevision)}
                      alt={portrait.image.alt_text}
                    />
                    <span>{portrait.kind === "style_world" ? "REFERENCE" : "OBSERVED"}</span>
                  </div>
                  <figcaption>
                    <strong>
                      {portrait.kind === "style_world" ? "Style Reference" : "Shopping History"}
                    </strong>
                    <span>
                      {portrait.kind === "style_world"
                        ? `${demo.report.vision_themes.slice(0, 3).map((theme) => theme.name).join(" · ")}`
                        : `${demo.report.score_provenance.kept_purchase_count} kept · ${demo.report.score_provenance.returned_item_count} returned`}
                    </span>
                  </figcaption>
                </figure>
              ))}
            </div>
            <div className="quick-read">
              <strong>Quick read</strong>
              <p>{neutralizeCopy(demo.report.summary)}</p>
            </div>
          </section>

          <nav className="detail-tabs" role="tablist" aria-label="Profile details">
            <button
              aria-selected={activeTab === "refine"}
              className={activeTab === "refine" ? "active" : undefined}
              onClick={() => setActiveTab(activeTab === "refine" ? null : "refine")}
              role="tab"
              type="button"
            >
              <span>01</span>
              Refine with a survey
              <small>{surveyProgress.answered}/{surveyProgress.total} answered</small>
            </button>
            <button
              aria-selected={activeTab === "analysis"}
              className={activeTab === "analysis" ? "active" : undefined}
              onClick={() => setActiveTab(activeTab === "analysis" ? null : "analysis")}
              role="tab"
              type="button"
            >
              <span>02</span>
              View the analysis
              <small>{demo.report.gap_score}/100 difference</small>
            </button>
          </nav>

          {activeTab === "refine" ? (
            <section className="survey-section detail-panel" role="tabpanel">
              <div className="survey-heading">
                <div>
                  <p className="eyebrow">UNDERSTAND THE DECISION</p>
                  <h2>Tell us what the receipt cannot.</h2>
                  <p>Use, feeling, motivation, and return reasons help explain buying behavior.</p>
                </div>
                <strong>{surveyProgress.answered}/{surveyProgress.total}</strong>
              </div>
              <div className="survey-grid">
                {demo.survey.map((item) => (
                  <article className="survey-card" key={item.id}>
                    <div className="survey-product">
                      {item.image ? (
                        <img src={item.image.image_url} alt={item.image.alt_text} />
                      ) : (
                        <div className="image-fallback">Product image unavailable</div>
                      )}
                      <header className="survey-item-heading">
                        <div>
                          <span className="source-chip">SHOPPING RECORD</span>
                          <h3>{item.item_name}</h3>
                          <p>{item.merchant}</p>
                        </div>
                        <strong>{formatCurrency(item.price, item.currency)}</strong>
                      </header>
                    </div>
                    <div className="receipt-facts">
                      <span>Bought <strong>{formatPurchaseDate(item.purchased_at)}</strong></span>
                      <span>Status <strong>{item.returned ? "Returned" : "Kept"}</strong></span>
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
                                  key={option}
                                  onClick={() => selectSurveyAnswer(item.item_id, prompt.key, option)}
                                  type="button"
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
                        placeholder="Optional context"
                        rows={3}
                        value={surveyComments[item.item_id] ?? ""}
                        onChange={(event) => updateSurveyComment(item.item_id, event.target.value)}
                      />
                      <small>{surveyComments[item.item_id]?.length ?? 0}/500</small>
                    </label>
                  </article>
                ))}
              </div>
              <div className="survey-actions">
                <p>
                  Submitting rebuilds the analysis. With image generation enabled, it also
                  regenerates both portraits.
                </p>
                <button
                  className="primary-button"
                  disabled={!surveyProgress.complete || analyzing}
                  onClick={analyzeSurvey}
                  type="button"
                >
                  {analyzing ? "Rebuilding…" : "Update my analysis"}
                </button>
              </div>
            </section>
          ) : null}

          {activeTab === "analysis" ? (
            <section className="analysis-panel detail-panel" role="tabpanel">
              <div className="analysis-title">
                <div>
                  <p className="eyebrow">AT A GLANCE</p>
                  <h2>Shopping history vs. style reference.</h2>
                </div>
                <div className="score-pill">
                  <strong>{demo.report.gap_score}</strong>
                  <span>pattern difference</span>
                </div>
              </div>

              <section className="comparison-section">
                <div className="comparison-counts">
                  <span><strong>{demo.report.score_provenance.purchase_item_count}</strong>shopping records</span>
                  <span><strong>{Math.round((demo.report.score_provenance.kept_purchase_count / demo.report.score_provenance.purchase_item_count) * 100)}%</strong>kept</span>
                  <span><strong>{Math.round((demo.report.score_provenance.returned_item_count / demo.report.score_provenance.purchase_item_count) * 100)}%</strong>returned</span>
                  <span><strong>{demo.report.score_provenance.aspirational_item_count}</strong>saved references</span>
                </div>
                <div className="dimension-grid">
                  {[...demo.report.dimensions].sort((a, b) => b.gap - a.gap).map((dimension) => (
                    <article className="dimension-card" key={dimension.key}>
                      <div className="dimension-title">
                        <h3>{dimension.label}</h3>
                        <span>{formatScore(dimension.gap * 100)}</span>
                      </div>
                      <div className="bar-row behavior">
                        <span>History</span>
                        <div className="bar"><i style={{ width: `${dimension.behavior * 100}%` }} /></div>
                        <b>{Math.round(dimension.behavior * 100)}</b>
                      </div>
                      <div className="bar-row reference">
                        <span>Reference</span>
                        <div className="bar"><i style={{ width: `${dimension.aspiration * 100}%` }} /></div>
                        <b>{Math.round(dimension.aspiration * 100)}</b>
                      </div>
                    </article>
                  ))}
                </div>
              </section>

              <section className="bubble-section">
                <p className="eyebrow">WHAT REALCART NOTICED</p>
                <div className="insight-cloud">
                  {insightBubbles.map((insight, index) => (
                    <article className={`insight-bubble ${insight.tone}`} key={`${insight.title}-${index}`}>
                      <strong className="bubble-metric">{insight.metric}</strong>
                      <h3>{insight.title}</h3>
                      <p>{insight.body}</p>
                    </article>
                  ))}
                </div>
              </section>

              <details className="evidence-details">
                <summary>See the evidence behind this analysis</summary>
                <p>{demo.report.evidence.map((item) => evidence.get(item.id) ?? item.id).join(" · ")}</p>
              </details>
            </section>
          ) : null}
        </>
      ) : null}

      <footer>Shopping history shows outcomes. Saved images add context. You supply the meaning.</footer>
    </main>
  );
}
