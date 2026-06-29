import { describe, it, expect } from "vitest";
import { readFileSync } from "fs";
import { resolve } from "path";

describe("API path consistency", () => {
  it("matching.ts apiBaseUrl defaults to /api", () => {
    const src = readFileSync(
      resolve(__dirname, "../api/matching.ts"),
      "utf-8"
    );
    expect(src).toContain('"/api"');
  });

  it("client.ts baseURL defaults to /api", () => {
    const src = readFileSync(resolve(__dirname, "../api/client.ts"), "utf-8");
    expect(src).toContain('baseURL: import.meta.env.VITE_API_BASE_URL || "/api"');
  });

  it("Matching.tsx export URLs use /api prefix", () => {
    const src = readFileSync(
      resolve(__dirname, "../pages/Matching.tsx"),
      "utf-8"
    );
    const exportPdfMatch = src.match(/window\.open\(`([^`]+export\/pdf[^`]*)`/);
    const exportExcelMatch = src.match(
      /window\.open\(`([^`]+export\/excel[^`]*)`/
    );

    expect(exportPdfMatch).not.toBeNull();
    expect(exportExcelMatch).not.toBeNull();
    expect(exportPdfMatch![1]).toMatch(/^\/api\//);
    expect(exportExcelMatch![1]).toMatch(/^\/api\//);
  });
});
