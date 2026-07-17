export function formatScore(score: number): string {
  const bounded = Math.max(0, Math.min(100, Math.round(score)));
  return `${bounded}/100`;
}
