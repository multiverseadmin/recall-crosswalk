# Recall crosswalk

**Vehicle safety recalls that appear in more than one country’s register, matched on the manufacturer’s own campaign code.**

A recall is usually issued in several countries. Each regulator gives it a different
number, so from the outside the same fault looks like unrelated events. There is one
thing they share: the code the *manufacturer* used. This dataset joins on that.

| | |
|---|---|
| Recalls appearing in more than one register | **2058** |
| Registers joined | United States, Canada, European Union |
| Built | 2026-09-13T05:43:56+00:00 |
| Live copy | https://api.carsmultiverse.com/v1/crosswalk |

No regulator publishes this, because no regulator holds more than its own register.

## The matching rule

> Exact match on the manufacturer own campaign code after identical normalisation on every side. Nothing is paired on brand and date.

Where each code comes from:

| Register | Source | Where the code lives |
|---|---|---|
| United States | NHTSA | Code read out of the campaign remedy text. |
| Canada | Transport Canada Vehicle Recalls Database | Code is a published column. |
| European Union | Commission Safety Gate | Code is the companyRecallCode field. |

## What a row does and does not mean

> A row here means three registers used the same manufacturer reference, not that the recalls are word for word identical. Each register keeps its own identifier and date so any row can be checked at source. Absence is not evidence: a register may hold the recall without stating the code.

Read that before drawing conclusions. In particular **absence is not evidence** — a
register may well hold the recall without stating the manufacturer code, and it will
not appear here.

## What was deliberately thrown away

**54 candidate matches were excluded.** Codes of three characters or fewer are not identifiers and were producing matches decades apart. They are excluded rather than published.

They are excluded rather than published because a join key of three characters is not
an identifier, and publishing a wrong match is worse than publishing nothing.

## Files

| File | What it is |
|---|---|
| `crosswalk.csv` | One row per matched recall, flat. Start here. |
| `crosswalk.json` | The same data plus the metadata above, as served by the API. |
| `openapi.json` | OpenAPI 3.1 description of the live API. |
| `to-csv.js` | Node script that regenerates the CSV from the live JSON. |

### CSV columns

```csv
code,registers,us_campaign,us_filed,ca_recall,ca_filed,eu_case,eu_published,eu_notifying_country,eu_reference
0161,2,14V536,2014-09-05,2014392,2014-09-10,,,,
```

`registers` is how many registers this recall was found in — 2 or 3.

## Checking a row yourself

Every row is checkable at source, which is the point of keeping each register’s own
identifier and date rather than collapsing them.

Take code `0161`:

- **United States** — NHTSA campaign `14V536`, filed 2014-09-05
- **Canada** — Transport Canada recall `2014392`, filed 2014-09-10

Look each up in its own register and you will find the same manufacturer code and the
same fault, five days apart.

## Refreshing it

```bash
curl -s https://api.carsmultiverse.com/v1/crosswalk -o crosswalk.json
node to-csv.js crosswalk.json > crosswalk.csv
```

Or take the CSV straight from the edge, which flattens it for you:

```bash
curl -s https://api.carsmultiverse.com/v1/crosswalk.csv -o crosswalk.csv
```

## Citation

The dataset is deposited and has a permanent identifier, so it can be cited in work
that outlives this repository:

> CarsMultiverse (2026). *Vehicle safety recalls matched across national registers on
> the manufacturer’s own campaign code.* Zenodo. https://doi.org/10.5281/zenodo.22087136

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22087136.svg)](https://doi.org/10.5281/zenodo.22087136)

The deposit is a **fixed snapshot**, which is what a citation needs. The copy served
from the API is **rebuilt continuously**, which is what a reader needs. The two are
meant to differ, and the deposit records the date it was taken.

## Licence

> The filings belong to the regulators named above. The matching is ours and may be reused with attribution to carsmultiverse.com.

See `LICENSE`. In short: the underlying filings are the regulators’ and carry their own
terms; the matching, the normalisation and the comparison are ours, CC BY 4.0.

## Where this comes from

[carsmultiverse.com](https://carsmultiverse.com) is a public record of vehicle safety
recalls across five registers — the United States, Canada, the United Kingdom, the
Netherlands, and the EU Safety Gate. (This crosswalk joins three of them; the other two
do not publish the manufacturer code in a form that can be matched exactly.)

It also tracks two things nobody else does: whether a published recall notice was later
**reworded**, and what it said before; and whether the owner letter a notice promised was
ever recorded as **sent**.

There is an MCP server for agents at `https://carsmultiverse.com/wp-json/cmvmcp/v1/mcp`.