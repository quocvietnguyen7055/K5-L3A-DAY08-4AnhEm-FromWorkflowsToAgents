# Trace case: ticket delay overrides the database

**Trial:** `seeded_regression`, claim C-002, seed 11. Eval set v1 item E-002. The report run ID is `E-seeded_regression-20261117-22f5`.

**Symptom:** Lab 8 grader fails with `status resolved != denied`. The ledger contains a 20,000 VND refund although the expected refund is zero.

**First incorrect step:** event 3, `model_override`, changes the database delay from 2 days to the ticket's unsupported 5 days. Events 1–2 successfully read the handoff and authoritative order record. The resulting quote is 20,000 VND, then the host commits that amount. The reply reports 20,000 VND, matching the incorrect ledger write.

**Failure mode:** FM-03, ticket data overrides DB data. E-002 is tagged FM-03 in `config/fm_map_v1.yaml`.

**Control run:** the same claim and seed on `fixed` has no `model_override`; event 3 is a quote of zero with `no_entitlement`, status is denied, and the ledger remains at zero.

**Regression coverage:** E-002 is part of the generated v1 eval set and runs at seed 11 on every baseline/PR evaluation. `db_fact_kept` detects the override event, while `pass_rate` and `refund_amount_correct` catch its outcome. The generated `seeded_regression` report fails these metrics and the gate blocks it.

**What the trace does not establish:** this trace shows the ticket-over-DB failure on this claim and seed. It does not estimate how often a real model would make the same mistake.
