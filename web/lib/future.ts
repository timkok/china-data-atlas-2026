/**
 * Extension points for later versions. Nothing here calls a model or a paid API.
 *
 * V0.5: multi-indicator compare, scatter, growth-rate view, PNG/SVG export, share links.
 * The indicator page already keeps year and province in the query string (`year`, `region`),
 * which is the share-link seed. Chart series are plain arrays, so a scatter can pair two
 * indicator files on (region, year) without a new data model.
 *
 * V1.0: a research assistant may answer only from the validated observation table.
 * It must show the year, the source table, and the formula for any derived number.
 * It must label a sentence as fact, calculation, correlation, or inference.
 * Correlation is not a causal claim. It must refuse questions the table cannot answer.
 * No API key may be shipped to the browser.
 */

export type AnswerKind = "fact" | "calculation" | "correlation" | "inference" | "refusal";

export type GroundedStatement = {
  kind: AnswerKind;
  text: string;
  indicator_id?: string;
  year?: number;
  region_code?: string;
  source_table?: string;
  formula?: string;
};

export type CompareRequest = {
  indicator_ids: string[];
  region_codes: string[];
  year: number | null;
};
