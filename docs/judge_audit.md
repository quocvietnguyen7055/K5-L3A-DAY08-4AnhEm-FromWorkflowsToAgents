# Judge audit

Confusion matrix treats `FAIL` as positive. Public CSV replay calibration (100 cases each; calculated directly from the committed CSVs):

| Criterion | n | κ | Precision | Recall | Floors κ≥0.6, P≥0.8, R≥0.7 | Decision |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Pass | Use only as an advisory style signal; not as a money or release gate. |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Fail | Reject as a gate; it misses most human-labeled failures. |

The tone score has enough agreement for a limited, calibrated style check on this replay set. It does not establish accuracy on new conversations. The helpfulness judge has high precision because it marks few cases as failures, but recall of 0.30 and κ of 0.375 make it unsafe for release decisions. Refund amount and approval remain code checks against the ledger.

## Disagreement audit

| Case | Judge | Human | Adjudication and rubric action |
|---|---|---|---|
| H-008 | PASS | FAIL | Overfamiliar pronouns and casual particle. Rubric: penalize register that is too familiar for customer support. |
| H-017 | PASS | FAIL | “Bạn” is inappropriate for the labeled older customer. Keep age/register context explicit in the rubric. |
| H-029 | PASS | FAIL | “Không cần nhắn thêm” sounds commanding despite polite opening. Score the full utterance, not a polite keyword. |
| H-042 | FAIL | PASS | Concise reply gives refund amount and timing. Do not require an apology when the task is already resolved. |
| H-051 | FAIL | PASS | “Refund” is accepted wording in the supplied support rubric. Do not reject English loanwords by themselves. |
| HL-015 | PASS | FAIL | Reply says 55,000 VND while the ledger says 40,000 VND. Add/retain an explicit ledger-grounded amount check; do not delegate money correctness to the judge. |

These rows illustrate the main disagreement categories. The helpful judge's recall problem is visible in repeated amount mismatches (for example HL-020 also states 90,000 VND against a 120,000 VND ledger). Audit decisions are rubric changes, not relabeling the public set to improve scores.

## Limits

This is replay calibration on the supplied public examples, not a held-out human study. Recalibrate on independently labeled cases before changing a release gate or relying on the style signal operationally.
