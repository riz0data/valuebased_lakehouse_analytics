# Data Sources

This project runs entirely on **open government data and open-source synthetic data**. No proprietary, client-derived, or real patient/member data is used anywhere in this repository.

## No PHI / No Client Data Statement

Every dataset referenced below is either (a) public domain government data, (b) explicitly published by its source for open developer/research use, or (c) synthetically generated open-source software with no real patient identities. Nothing in this repository derives from any employer's, client's, or third party's proprietary systems, contracts, or confidential data. Any resemblance in structure to real-world payer systems is intentional - it reflects publicly documented industry patterns (Data Vault 2.0, CMS-HCC methodology, HEDIS-style quality measurement) - not the reproduction of any non-public source.

## Datasets Used

### CMS DE-SynPUF (Data Entrepreneurs' Synthetic Public Use Files)
- **Publisher:** Centers for Medicare and Medicaid Services (CMS)
- **What it is:** Fully synthetic Medicare claims data - inpatient, outpatient, carrier, prescription drug events - explicitly created and published by CMS for developers to build and test healthcare applications without any real beneficiary data.
- **License:** Public domain, U.S. government work. Published by CMS specifically for this use case.
- **Used for:** Claims, encounters, and the backbone of the Payment Integrity and Risk Adjustment domains.

### Synthea
- **Publisher:** The MITRE Corporation
- **What it is:** An open-source synthetic patient generator producing realistic but entirely fake patient records in FHIR format - demographics, encounters, conditions, medications, procedures.
- **License:** Apache License 2.0.
- **Used for:** Clinical encounter and condition data supporting the Clinical Quality domain.

### NPPES NPI Registry
- **Publisher:** Centers for Medicare and Medicaid Services (CMS)
- **What it is:** The real, public registry of National Provider Identifiers for every licensed healthcare provider and organization in the United States.
- **License:** Public domain, freely downloadable in bulk.
- **Used for:** Provider and facility reference data (`hub_provider`, `hub_facility`). Note: this is the only real-world (non-synthetic) data source used, and it contains no patient or member information - only public provider directory data.

### ICD-10-CM
- **Publisher:** National Center for Health Statistics (NCHS) / CMS
- **What it is:** The diagnosis coding standard used across U.S. healthcare.
- **License:** Public domain.
- **Used for:** Diagnosis reference data (`hub_diagnosis`) and the risk adjustment diagnosis-to-HCC crosswalk.

### HCPCS Level II
- **Publisher:** CMS
- **What it is:** The procedure and supply coding standard used alongside CPT codes.
- **License:** Public domain.
- **Used for:** Procedure reference data (`hub_procedure`). **Important:** this project deliberately uses HCPCS Level II rather than CPT, because CPT codes are copyrighted and licensed by the American Medical Association. HCPCS Level II covers a meaningful subset of procedure and supply reporting without any licensing requirement.

### FDA National Drug Code (NDC) Directory
- **Publisher:** U.S. Food and Drug Administration
- **What it is:** The official directory of drug identifiers for every drug marketed in the United States.
- **License:** Public domain.
- **Used for:** Drug reference data (`hub_drug`) supporting the Pharmacy domain.

### CMS-HCC Risk Adjustment Model
- **Publisher:** CMS
- **What it is:** The publicly documented methodology and diagnosis-to-condition-category crosswalk CMS uses to calculate Medicare Advantage risk scores.
- **License:** Public domain, published as part of CMS's annual rate announcement and technical documentation.
- **Used for:** The risk adjustment domain in full, including `lnk_diagnosis_hcc_crosswalk` and risk score calculation logic.

### CMS Part C and Part D Star Ratings Technical Notes
- **Publisher:** CMS
- **What it is:** The public technical documentation describing the measures, weights, and methodology behind Medicare Advantage and Part D Star Ratings.
- **License:** Public domain.
- **Used for:** The Clinical Quality domain's measure definitions and scoring logic. **Important:** this project deliberately uses the public CMS Star Ratings measure set rather than full HEDIS technical specifications, because complete HEDIS specifications are licensed by NCQA and are not open data. Star Ratings measures overlap substantially with HEDIS in concept while remaining fully public.

## What Is Explicitly Excluded

- No CPT codes (AMA-licensed)
- No full HEDIS technical specifications (NCQA-licensed)
- No real patient, member, or claims data of any kind
- No data, schema, or business logic derived from any employer or client engagement

## Summary Table

| Source | Real or Synthetic | License | Domain |
|---|---|---|---|
| CMS DE-SynPUF | Synthetic | Public domain (CMS) | Payment Integrity, Risk Adjustment |
| Synthea | Synthetic | Apache 2.0 | Clinical Quality |
| NPPES NPI Registry | Real (public directory only) | Public domain | Core (Provider/Facility) |
| ICD-10-CM | Real (code set, not patient data) | Public domain | Core, Risk Adjustment |
| HCPCS Level II | Real (code set, not patient data) | Public domain | Payment Integrity |
| FDA NDC Directory | Real (code set, not patient data) | Public domain | Pharmacy |
| CMS-HCC Model | Real (methodology, not patient data) | Public domain | Risk Adjustment |
| CMS Star Ratings Technical Notes | Real (methodology, not patient data) | Public domain | Clinical Quality |
