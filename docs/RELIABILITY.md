# Reliability Scoring System

## Overview

The reliability scoring system provides a transparent, multi-factor assessment of each paper's trustworthiness. Results are color-coded for quick visual identification.

## Color Coding

### Green (Score 0.80 - 1.00) - High Reliability

Papers in this category are:
- Peer-reviewed in reputable journals
- Highly cited (100+ citations)
- Verified across multiple databases
- From established publishers

**Confidence level:** High - suitable for citations and research decisions

### Yellow (Score 0.50 - 0.79) - Moderate Reliability

Papers in this category may be:
- Preprints not yet peer-reviewed
- Newer papers with few citations
- Found in only one source
- Conference papers or proceedings

**Confidence level:** Moderate - verify before citing

### Red (Score 0.00 - 0.49) - Lower Reliability

Papers in this category may be:
- Unverified sources
- Retracted papers (score = 0)
- Grey literature without peer review
- Contradicted by other research

**Confidence level:** Low - use with caution, verify thoroughly

## Scoring Algorithm

Total score is calculated from five components:

### 1. Peer Review Score (0.00 - 0.30)

| Status | Score |
|--------|-------|
| Peer-reviewed journal article | 0.30 |
| Conference paper | 0.20 |
| Preprint | 0.10 |
| Unknown/Grey literature | 0.05 |

### 2. Journal Reputation Score (0.00 - 0.20)

| Criteria | Score |
|----------|-------|
| High-impact journal (Nature, Science, Cell, etc.) | 0.20 |
| Reputable publisher (Springer, Elsevier, etc.) | 0.15 |
| Other journals | 0.10 |
| Unknown journal | 0.00 |

**High-impact journals include:**
- Nature, Science, Cell
- The Lancet, NEJM, JAMA, BMJ
- Nature Medicine, Nature Genetics
- PNAS, Physical Review Letters
- JACS, Angewandte Chemie

**Reputable publishers include:**
- Nature Publishing Group, Springer
- Elsevier, Wiley, Cell Press
- ACS, RSC, IEEE
- Oxford University Press
- Cambridge University Press
- PLOS, Frontiers, BMC

### 3. Citation Impact Score (0.00 - 0.20)

| Citations | Score |
|-----------|-------|
| 500+ | 0.20 |
| 100-499 | 0.15 |
| 25-99 | 0.10 |
| 5-24 | 0.05 |
| 1-4 | 0.02 |
| 0 | 0.00 |

### 4. Cross-Source Verification Score (0.00 - 0.20)

| Sources Found In | Score |
|------------------|-------|
| 5+ sources | 0.20 |
| 3-4 sources | 0.15 |
| 2 sources | 0.10 |
| 1 source | 0.05 |

### 5. Recency Score (0.00 - 0.10)

| Age | Score |
|-----|-------|
| 0-2 years | 0.10 |
| 3-5 years | 0.07 |
| 6-10 years | 0.04 |
| 10+ years | 0.02 |

## Special Cases

### Retracted Papers

If a paper is marked as retracted, the total score is automatically 0.00 regardless of other factors.

### Contradicted Research

Each contradiction reduces the score by 0.05, up to a maximum penalty of 0.25.

## Example Calculations

### Example 1: High-Quality Paper

```
Paper: "CRISPR-Cas9 mechanism study" in Nature (2020)
- Peer review: 0.30 (peer-reviewed)
- Journal: 0.20 (Nature)
- Citations: 0.20 (800 citations)
- Verification: 0.15 (found in 4 sources)
- Recency: 0.07 (5 years old)

Total: 0.92 -> GREEN
```

### Example 2: Recent Preprint

```
Paper: "Novel ML approach" on arXiv (2024)
- Peer review: 0.10 (preprint)
- Journal: 0.00 (no journal)
- Citations: 0.02 (3 citations)
- Verification: 0.05 (1 source)
- Recency: 0.10 (new)

Total: 0.27 -> RED
```

### Example 3: Moderate Paper

```
Paper: "Clinical trial results" in BMJ (2022)
- Peer review: 0.30 (peer-reviewed)
- Journal: 0.20 (BMJ - high impact)
- Citations: 0.05 (15 citations)
- Verification: 0.10 (2 sources)
- Recency: 0.10 (recent)

Total: 0.75 -> YELLOW
```

## Using Reliability in Research

### Recommendations

1. **For literature reviews:** Include papers of all reliability levels but note the color coding in your analysis.

2. **For citations:** Prefer green papers; yellow papers should be verified; red papers should have additional corroboration.

3. **For trend analysis:** All papers are valuable regardless of reliability.

4. **For clinical decisions:** Only rely on green papers from established medical journals.

### Limitations

The reliability score is:
- An automated assessment, not human review
- Based on available metadata
- Subject to data quality in source databases
- Not a substitute for expert judgment

## API Response

The reliability information is included in each paper object:

```json
{
  "reliability": {
    "score": 0.85,
    "color": "green",
    "level": "high",
    "components": {
      "peerReview": 0.30,
      "journal": 0.20,
      "citations": 0.15,
      "verification": 0.15,
      "recency": 0.05
    },
    "isRetracted": false,
    "contradictions": []
  }
}
```

## Future Enhancements

Planned improvements:
- Retraction Watch integration
- Altmetrics data
- Author h-index consideration
- Field-normalized citation scores
- Journal impact factor integration
