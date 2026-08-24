#!/usr/bin/env node
/**
 * Flatten the crosswalk JSON into CSV.
 *
 *   node to-csv.js crosswalk.json > crosswalk.csv
 *
 * Writes exactly the columns the API serves at /v1/crosswalk.csv, so the two
 * cannot drift apart. Every field is quoted and internal quotes are doubled,
 * because model names contain commas often enough to matter.
 */

const fs = require("fs");

const path = process.argv[2];

if (!path) {
  console.error("usage: node to-csv.js <crosswalk.json>");
  process.exit(1);
}

const doc = JSON.parse(fs.readFileSync(path, "utf8"));
const rows = doc.recalls || doc.rows || doc;

if (!Array.isArray(rows)) {
  console.error("no array of recalls found in that file");
  process.exit(1);
}

const COLS = [
  "code", "registers",
  "us_campaign", "us_filed",
  "ca_recall", "ca_filed",
  "eu_case", "eu_published", "eu_notifying_country", "eu_reference",
];

const q = (v) => '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';

const line = (r) => COLS.map((c) => {
  if (c === "code" || c === "registers") return q(r[c]);
  const [reg, ...rest] = c.split("_");
  const key = rest.join("_");
  return q(r[reg] ? r[reg][key] : "");
}).join(",");

console.log(COLS.join(","));

for (const r of rows) {
  console.log(line(r));
}