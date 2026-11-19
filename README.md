# l2-data

The public, versioned dataset behind **L2 Watch**: an audit of Bitcoin layer-2 systems from public chain data alone.
Liquid comes first; Ark and Spark will fill the same tables later.

Every number here can be recomputed by anyone with a Bitcoin node and an Elements (Liquid) node. No number comes
from the operators (one operator statement is cited, as the stated cause of an incident). Method, definitions and
known limits: [METHODS.md](METHODS.md). Changes and corrections between releases: [CHANGELOG.md](CHANGELOG.md).

## Releases

| Release | Tag | Bitcoin cutoff | Liquid cutoff | DOI |
|---|---|---|---|---|
| v0.1.1 | `v2026.11.19` | block 976,206 (2026-11-17 02:10:32 UTC) | block 4,148,532 | to be added after the Zenodo release |
| v0.1 | `v2026.11.18` | same | same | superseded by v0.1.1, never published: its 2018–2022 emergency exposure is too low (CHANGELOG.md) |

**Cite a tag, never `main`.** A paper or public comment that quotes a number pins the release:
- the tag (or its Zenodo DOI) in the citation;
- `metadata/release.json` names the inputs (SHA-256), the code commit and the cutoffs;
- `metadata/SHA256SUMS` lets a reader confirm they have the same files:
  `python3 scripts/verify_release.py` (or `sha256sum -c metadata/SHA256SUMS`).

## Layout

```
l2-data/
├── common/                  the common audit tables: every L2 fills the same columns (rows keyed by l2 + instance)
│   ├── custody.parquet          BTC held for the L2's users, per UTC day
│   ├── liabilities.parquet      claims outstanding on the L2 (Liquid: L-BTC), per UTC day
│   ├── backing.parquet          custody against liabilities, per UTC day, with the day's worst point
│   ├── flows.parquet            every entry into and exit from custody, both legs, delay
│   ├── control.parquet          who can move the custody and who signs blocks: paths, thresholds, keys, timelocks, rotations
│   ├── timelock_exposure.parquet custody a timelocked fallback path could spend, per UTC day
│   ├── liveness.parquet         block production per UTC day
│   ├── incidents.parquet        events found by fixed rules (shortfalls, emergency spends, halts, unexplained outflows),
│   │                            plus an operator-disclosed timelock lapse and a reviewed September 2026 summary
│   └── scorecard.parquet        headline metrics at the cutoff
├── liquid/                  Liquid's own evidence tables
│   ├── reserve_by_block.parquet      reserve vs L-BTC supply at every Bitcoin block since 540,000
│   ├── reserve_daily.parquet
│   ├── custody_outputs.parquet       every Bitcoin output that has held Liquid reserves
│   ├── federation_txs.parquet        every Bitcoin transaction signed by a federation script
│   ├── federation_inputs.parquet     their inputs: spend shape and path (11-of-15 or 2-of-3 emergency)
│   ├── federation_spend_outputs.parquet
│   ├── pegout_fulfilment.parquet     every Liquid peg-out matched to its Bitcoin payment
│   ├── pegout_daily.parquet, pegout_halts.parquet, unexplained_outflows.parquet
│   ├── lbtc_supply_changes.parquet   L-BTC supply at every Liquid block where it changed
│   ├── block_gaps.parquet            every gap of 10 minutes or more between Liquid blocks
│   └── fedpeg_generations.json       the federation's peg scripts, keys and timelocks
├── metadata/
│   ├── data_dictionary.md / .json    every table and column
│   ├── verification_classes.json     how each number is established
│   ├── validation.json               the invariant checks this release passed
│   ├── release.json                  cutoffs, input SHA-256s, code commit, file list
│   └── SHA256SUMS
├── scripts/verify_release.py
├── METHODS.md
├── CHANGELOG.md
└── CITATION.cff
```

Every row of a common table carries a `verification_class` and a `method`:
- `bitcoin_verified`: read from Bitcoin blocks alone.
- `l2_chain_verified`: read from the L2's own chain alone.
- `cross_chain_verified`: joins one value of each kind by a stated rule.
- `inferred`: depends on a modelling choice named in `method` (the September 2026 coin trace).
- `operator_reported`: taken from the operator's statements. Not used.

## Reading the data

```python
import duckdb
duckdb.sql("select utc_day, reserve_sats/1e8 reserve, supply_sats/1e8 supply, backing_ratio "
           "from 'common/backing.parquet' where utc_day >= '2026-08-01' order by utc_day").show()
duckdb.sql("select incident_id, duration_s/86400 days, magnitude_sats/1e8 btc, txids "
           "from 'common/incidents.parquet' order by start_time").show()
```

Amounts are integer satoshis. Times are UTC Unix seconds (header times). Txids are lowercase hex in display order.
`tx_key` (Liquid tables) is `height << 15 | position of the transaction in its block` on Bitcoin.

## How it is made

Bitcoin Data Labs runs the pipeline on its own server:
- a Bitcoin chain lake and a Liquid node;
- the audit tables are built from them;
- an exporter writes this repository only after every invariant passes (`metadata/validation.json`).

The pipeline code is not in this repository. `metadata/release.json` names its commit.

## License

Data: [CC BY 4.0](LICENSE). It is free to use, including commercially, with credit: "Source: Bitcoin Data Labs
(bitcoindatalabs.org)". The helper script in `scripts/` is MIT-licensed. Transactions, scripts and headers read from
the Bitcoin and Liquid blockchains are public chain data.
