
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

## Next Phase
Phase 2 – Data Cleaning and Composition Parsing.
