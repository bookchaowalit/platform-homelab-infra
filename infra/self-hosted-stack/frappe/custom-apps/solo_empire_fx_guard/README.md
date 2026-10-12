# Solo Empire FX Guard

Small, provider-free Frappe app boundary for the internal ERPNext candidate.
It adds a trusted `custom_fx_snapshot_id` field to Sales Invoice and validates
the corresponding operator-controlled snapshot before submission.

This app is not installed on the main site by default. It does not fetch rates,
write snapshots, or enable multi-currency valuation. Install it only on a
disposable/private-pilot site after the exchange-rate policy and owner decision
are recorded.

The candidate image `Containerfile` packages this app, but site installation is
deliberately explicit. Runtime verification covered a real `Sales Invoice.submit()`
on a disposable site. The local image
`solo-empire-frappe:16-candidate-fx-guard` now builds and imports the packaged
module; repeat site migration and smoke checks before any private-pilot
promotion.
