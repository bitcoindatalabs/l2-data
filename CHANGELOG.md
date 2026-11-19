# Changelog

Each release is a git tag. Old tags never change; a correction is a new release, recorded here.

## v0.1.1 (tag `v2026.11.19`): correction of the 2018–2022 emergency exposure

Same cutoffs as v0.1: Bitcoin block 976,206, Liquid block 4,148,532. Schema 1.1.

### Correction (2026-11-18, bdl-098)

v0.1 gave the federation's 2018–2023 change address, P2SH-P2WSH `a914 8ed14f3b870f8d9012c423ec7a76148ba84f650587 87`,
the 4,032-block emergency timelock of the 2018 peg script. Its own timelock is **2,016 blocks**: it is the 2018 peg
script with only the timelock changed. The script is known exactly because only one timelock makes it hash to the
witness script that all 26,210 of its spends reveal on Bitcoin. With the right timelock:

| | v0.1 | v0.1.1 |
|---|---|---|
| Largest custody the 2-of-3 emergency keys could spend | 20.02 BTC (after block 559,346, 2019-01-20) | **870.06 BTC** (after block 634,326, 2020-06-12; 40.3% of the reserve; 3 blocks) |
| Change outputs that became spendable that way | 288 (24.23 BTC) | 2,477 (13,344.71 BTC) |
| Bitcoin blocks with any exposure | 276,832 | 300,305 |
| UTC days with any exposure | 1,922 | 2,260 |

The operator disclosed the cause in June 2020: change was "refreshed shortly after expiry, instead of before". It is
now an incident (`timelock_lapse`). The last change output of 0.001 BTC or more that became spendable was spent on
2020-07-01; after that only dust (at most 45,619 sats) until 2022-12-05.

### What changed in the files

Rows are compared by each table's key; every number here was checked against v0.1 column by column.

| File | Change |
|---|---|
| `liquid/custody_outputs` | `csv_blocks` 4,032 → 2,016 in **26,210** rows: exactly the outputs paying the change script. `txid` and `script` filled in the **41** unclaimed-deposit rows that lacked them (below). Nothing else. |
| `liquid/federation_inputs` | `prev_csv_blocks` 4,032 → 2,016 in the 26,210 inputs that spend those outputs |
| `liquid/reserve_by_block` | `emergency_exposed_sats`, `emergency_exposed_utxos`, `exposed_sats_legacy_2018` higher at 90,434 blocks (never lower) |
| `liquid/reserve_daily` | the same three columns, on 626 days |
| `common/timelock_exposure` | `exposed_sats` and `exposed_utxos` on 626 days, `exposed_max_sats` on 845. `method` now says each output takes its own script's timelock |
| `common/scorecard` | `max_emergency_exposed_sats` 2,002,329,167 → 87,005,750,634 sats. New: `block_signing_path` (11-of-15) and `keys_changed_block_signing_last_rotation` (2) |
| `common/control` | Built from the federation key sets. New column `role`. The 8 peg-script rows keep every value, with only the `method` text new. Added: the change script (2 rows, timelock 2,016, `bitcoin_verified`) and the five block-signing key sets (5 rows) |
| `common/incidents` | New column `references`. 3 new rows: `timelock_lapse` (2018-11-16 → 2020-07-01, magnitude 870.06 BTC); `event_summary` and `coin_trace` for September 2026, from a forensic review still in review, `coin_trace` being `inferred`. The 17 rule-detected rows are unchanged |
| `common/flows` | The 41 unclaimed deposits now carry `btc_txid`. Their `flow_id` takes the standard form `unclaimed_deposit:<txid>:<vout>` (v0.1: `unclaimed_deposit:tx_key<key>:<vout>`). No other column changed |
| `metadata/` | Schema 1.1 dictionary. Validation: 78 checks pass (v0.1: 76). New: every custody output's timelock equals its own script's, and every custody output has its txid. `release.json` also lists `federation_keysets.parquet` and `curated_incidents.json` as inputs |
| `METHODS.md`, `README.md`, `CITATION.cff` | correction note, definitions, releases table, version `v2026.11.19` |

Content identical to v0.1 (only the release name and code commit in the Parquet metadata differ): `common/backing`,
`custody`, `liabilities`, `liveness`; `liquid/block_gaps`, `federation_txs`, `federation_spend_outputs`,
`lbtc_supply_changes`, `pegout_fulfilment`, `pegout_daily`, `pegout_halts`, `unexplained_outflows`;
`liquid/fedpeg_generations.json`.

**Txids of unclaimed deposits.** 41 of the 42 deposits that no Liquid peg-in claimed had no txid in v0.1: we find
such a deposit only when the federation spends it, so our extract had not kept the transaction that made it. v0.1.1
reads those 41 transactions from our Bitcoin chain extract. Each output's value equals the value the spend consumed,
and its script is the P2WSH (or P2SH-P2WSH) of the witness script hash the federation's spend reveals.

### Unchanged

Reserve, L-BTC supply, gap and its components, backing, every peg-in and peg-out, the peg-out matching, unexplained
outflows, block gaps and liveness, and every figure of the September 2026 event.

## v0.1 (tag `v2026.11.18`): superseded, never published

First release. Superseded by v0.1.1 because its 2018–2022 emergency exposure is too low (above).
