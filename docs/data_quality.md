
# Medicine Dataset – Data Quality Audit

## 1. Dataset Overview

- Total records: 253,973
- Total columns: 9
- Dataset source: Raw_A_Z_medicines_dataset_of_India.csv

## 2. Missing Values

- Missing composition1: 0
- Missing composition2: 141,802
- Missing composition2 percentage: 55.83%
- Missing values in other columns: 0

**Decision:** composition2 is optional. Records with one ingredient
will be retained.

## 3. Duplicate Records

- Exact duplicate rows: 0
- Duplicate name + manufacturer combinations: 2,928

**Decision:** Do not remove records based only on name and manufacturer.
Different pack sizes, strengths, or prices may represent valid products.

## 4. Price Quality

- Mean price: ₹270.53
- Median price: ₹79.00
- Minimum price: ₹0.00
- Maximum price: ₹436,000.00
- Zero-price records: 4
- Negative-price records: 0
- Missing-price records: 0

**Decision:** Zero and invalid prices will be flagged and excluded from
price recommendations. High prices will be investigated rather than
automatically deleted.

## 5. Medicine Status

- Active medicines: 246,068 (96.89%)
- Discontinued medicines: 7,905 (3.11%)

**Decision:** Discontinued records will be retained for traceability
but excluded from recommendations.

## 6. Composition Analysis

- Records with one listed ingredient: 141,802
- Records with two listed ingredients: 112,171
- Records with three or more listed ingredients: 0
- Records with no listed ingredients: 0

**Limitation:** The dataset provides two separate composition columns.
The absence of a third listed ingredient does not establish that every
medicine has at most two ingredients in reality.

## 7. Name Normalization

- Unique names before normalization: 249,398
- Unique names after lowercase and whitespace normalization: 249,345
- Difference: 53

**Decision:** Names will be standardized for searching, while original
names will be preserved for display.

## 8. Dosage Form and Pack Size

The dosage_form column contains only the value 'allopathy'.
It does not identify the actual pharmaceutical form.

The pack_size column contains descriptions such as strips, bottles,
vials, and tubes, with units including tablets, ml, and gm.

**Decision:** Actual dosage form and release type will be inferred
from medicine names and pack descriptions during the cleaning phase.

## 9. Key Data Quality Issues and Planned Actions

| Issue | Planned action |
|---|---|
| Missing composition2 | Retain as a valid optional field |
| Logical duplicate combinations | Preserve different product variants |
| Zero prices | Flag and exclude from recommendations |
| Very high prices | Investigate outliers; do not delete automatically |
| Inconsistent ingredient names | Normalize using a reviewed synonym dictionary |
| Inconsistent spacing | Standardize text |
| Multiple strength formats | Parse and normalize units carefully |
| Generic dosage category | Infer actual dosage form from available text |
| Discontinued medicines | Exclude from recommendation results |

## 10. Conclusion

The dataset contains a substantial number of medicine records and
provides useful information about product names, prices, manufacturers,
compositions, and packaging.

The main challenge is standardizing composition strengths, ingredient
names, dosage forms, and pack sizes before reliable price comparisons
can be performed.
