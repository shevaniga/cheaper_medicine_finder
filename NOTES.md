
# Project Notes – Cheaper Medicine Finder

## Phase 0 – Setup
- Python installed
- Git installed
- VS Code configured
- Dataset selected and loaded

## Phase 1 – Data Audit
- Inspected 253,973 medicine records.
- Standardized column names in the audit copy.
- Checked missing values and duplicate records.
- Analysed price distribution and invalid prices.
- Analysed active and discontinued medicines.
- Inspected medicine composition formats.
- Examined dosage categories and pack-size descriptions.
- Created docs/data_quality.md.

## Important Findings
- composition2 is missing in approximately 55.83% of records.
- No exact duplicate rows were found.
- 2,928 records share a medicine name and manufacturer.
- 7,905 records are discontinued.
- Four records have zero prices.
- The dosage_form column contains only "allopathy".
- The dataset has two separate composition fields.

## Phase 2 – Data Cleaning and Composition Parsing

- Standardized the original dataset column names.
- Cleaned text fields by removing extra spaces and inconsistent whitespace.
- Preserved original price values in `price_original`.
- Classified prices using `price_status`.
- Excluded zero and invalid prices from the cleaned price field without deleting records.
- Parsed medicine ingredients and strengths from composition fields.
- Extracted ingredient names, strength values, units, denominators, and strength bases.
- Identified missing and unrecognized strength formats.
- Normalized ingredient names to lowercase and standardized whitespace.
- Applied synonym mapping for Paracetamol/Acetaminophen.
- Converted compatible mass strengths (mcg, mg, g) into mg.
- Preserved non-mass units such as IU, %, million, billion, and AU.
- Extracted product forms from pack-size descriptions.
- Identified formulation modifiers such as SR, ER, XR, CR, MR, DR, DT, MD, and IR.
- Compared formulation modifiers from medicine names and pack descriptions.
- Flagged uncertain formulation information for manual review.
- Generated canonical ingredient signatures for each medicine.
- Created SHA-256 canonical identity keys.
- Established match-eligibility rules for automatic comparison.
- Validated canonical identity groups for consistency.
- Preserved uncertain and duplicate-component records instead of deleting them.

## Important Findings

- Total medicine records: 253,973.
- Cleaned dataset shape: 253,973 rows × 11 columns.
- Valid prices: 253,969.
- Zero-price records: 4.
- Total ingredient records: 366,144.
- Successfully parsed strengths: 360,677.
- Parser coverage: 98.51%.
- Missing strengths: 5,377 (1.47%).
- Unparsed strengths: 90 (0.02%).
- Unique original ingredient names: 1,718.
- Unique normalized ingredient names: 1,716.
- Paracetamol/Acetaminophen synonym mapping: 275 records.
- Mass strengths converted to mg: 335,336.
- Non-mass strength records preserved unchanged: 25,341.
- Records with unparsed or missing strength normalization: 5,467.
- Product form categories identified: 69.
- Unknown product forms: 143.
- Formulation review required: 5,348 medicine records.
- Duplicate-component medicines flagged for review: 3.
- Match-eligible medicine records: 244,649 (96.33%).
- Medicine records excluded from automatic matching: 9,324.
- Unique eligible canonical identity groups: 14,503.
- Groups containing multiple medicine records: 7,960.
- No inconsistencies found in ingredient signatures, product forms, formulation statuses, or normalized modifiers within eligible identity groups.

## Important Implementation Decisions

- Original raw data and composition values were preserved.
- Zero-price records were retained but excluded from valid price calculations.
- Chemically distinct ingredient salts and forms were not merged.
- Specialized biological potency units were not converted into mass units.
- Unrecognized strength formats were retained for manual review.
- Unspecified formulation was not automatically treated as immediate-release.
- Canonical identity groups represent potential comparison candidates, not confirmed clinical interchangeability.
- Records requiring review were preserved but excluded from automatic matching.



## Phase 3: Pack Size Parsing and Price Normalization

**Status:** Completed

### Dataset
- Input: `data/processed/medicines_cleaned.parquet`
- Output: `data/processed/medicines_phase3.parquet`
- Total records: 253,973
- Output columns: 22

### Pack Size Parsing
- Parsed records: 253,952
- Records requiring manual review: 21
- Parser coverage: 99.99%
- Missing pack-size labels: 0

### Price Normalization
- Created `pack_quantity`
- Created `pack_unit`
- Created `pack_container`
- Created `pack_parse_status`
- Created `price_per_unit`

Price per unit is calculated by dividing medicine price by the parsed pack quantity, subject to valid price and quantity checks.

### Important Decisions
- Volume units are normalized to millilitres.
- Weight units are normalized to grams.
- Proprietary dosage forms are kept separate.
- Uncertain pack descriptions are retained for manual review.
- Records with missing or invalid prices do not receive a valid price-per-unit value.
- Different measurement units must not be compared directly.

### Limitations
- A successfully parsed pack does not automatically establish clinical or commercial comparability.
- Price comparisons must consider medicine identity, formulation and compatible pack units.
- Unresolved pack descriptions are retained rather than assigned potentially incorrect units.

### Output
`data/processed/medicines_phase3.parquet`
