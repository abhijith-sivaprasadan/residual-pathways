# Accounting v3 quantitative gate (provisional)

Based on v3 section A.3a. **Do not apply these numerical parameters as an official IIASA or IAMC tolerance.** They remain provisional until original source reporting precision is established during G0 scientific review.

Given net N, source-verified complete disjoint positive components summing to G, and source-verified atmospheric removals summing to R, the diagnostic is N − (G − R) in Mt CO2/year. A correct arithmetic identity is neither sufficient to prove that the input branches are compatible nor evidence of a real reviewed model case.

Gates are independent: model-specific semantic mapping with exhaustive boundaries and no fossil source CCS counted as atmospheric removal; source-stated quantization per term with a primary source URL; numerical error below half the sum of reported quantization steps plus the tiny floating-point allowance; materiality bound max(0.1 Mt/year, 0.0001 × abs(net)), tightened to 1% of the smallest nonzero component if it is smaller than 10 Mt/year; and source provenance.

The numerical bound is evaluated at strict half, registered and loose double settings without ever changing the semantic evaluation. The existing fixtures include exact 120−20=100, near-zero 100−100=0, deliberately wrong 100−100≠5, overlapping components that balance numerically, missing land scope and unverified source quantization. All real AR6 source records remain unreviewed; passing *synthetic* flags only returns PENDING_INDEPENDENT_REVIEW, never scientific approval.

Reviewers must establish identities and precision from original source records and model documentation before making I1–I3 determinations. Run the tests with python -m pytest tests/test_accounting.py -q.
