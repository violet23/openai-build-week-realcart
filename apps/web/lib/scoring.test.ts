import { describe, expect, it } from "vitest";

import { formatScore } from "./scoring";

describe("formatScore", () => {
  it("rounds and bounds display values", () => {
    expect(formatScore(42.4)).toBe("42/100");
    expect(formatScore(140)).toBe("100/100");
    expect(formatScore(-2)).toBe("0/100");
  });
});
