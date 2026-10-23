# Reader-facing scientific and policy outputs

The communication generator consumes only already committed **aggregate, non-sensitive source-derived** counts and metrics, never original AR6 Model/Scenario source rows. It verifies expected counts, generates an accessible SVG category funnel (not a gross emissions decomposition), a policy-facing summary emphasizing source limits and a SHA-256 provenance manifest for all outputs.

Run: python -m residual_pathways publish-brief --output results/communication. CI publishes a policy_brief.md, reporting_funnel.svg and communication_manifest.json under results/communication/. The policy brief is limited to the independently published teaching dataset and explicitly not an IIASA or IPCC conclusion.

This does not substitute for an original peer-reviewed working paper or independent case-specific review. All data are educational/exploratory, and official AR6 v1.1 authentication remains a scientific gate.
