# Methods: L2 audit dataset (release v0.1, Liquid)

This note is for readers of the dataset and of L2 Watch. It gives the definitions, the cutoffs, the verification
classes and the known limits. Every table and column is in `metadata/data_dictionary.md`. The checks this release
passed are in `metadata/validation.json`.

## 1. Sources and cutoffs

| | Source | v0.1 cutoff |
|---|---|---|
| Bitcoin | every block from height 540,000 (before Liquid's first peg-in, 542,409), read from our own full chain extract | block **976,206** (`…1867e22c3c462ddd71f91a71a8c3c98b703f238320a0e`, 2026-11-17 02:10:32 UTC) |
| Liquid | every block from genesis, read from our own Elements 23.3.3 node (chain `liquidv1`) | block **4,148,532**: the last Liquid block whose header time is at or before the Bitcoin cutoff's |

- Times are block header times in UTC. Bitcoin header times can be off by up to about two hours, and Liquid's by a
  few seconds.
- **Mapping Liquid to Bitcoin:** each Bitcoin block is paired with the last Liquid block whose header time is at or
  before the Bitcoin block's. Liquid times are made non-decreasing first (running maximum).
- Nothing in this release comes from the federation, Blockstream, an exchange or the press.

## 2. Definitions (Liquid)

**Federation scripts.** We read Liquid's peg script (the *fedpegscript*) at every DynaFed epoch start from the node.
Four scripts have been current since 2018 (`control`, `liquid/fedpeg_generations.json`). Each has two spending
paths:
- the **normal** path: 11 of 15 functionary keys;
- the **emergency** path: 2 of 3 emergency keys, usable only after a relative timelock. The timelock is 4,032
  Bitcoin blocks for the 2018, 2023 and January 2026 scripts, and 8,064 for the July 2026 script.

**Custody (reserve).** Custody is every Bitcoin output the federation holds:
- peg-in deposits;
- change from federation transactions;
- payments into a federation program.

It is found in two ways:
- **From every Liquid peg-in claim.** The claimed Bitcoin output must have exactly the claimed value. Its script must
  equal the federation script tweaked with the claim script, by the same derivation as Liquid's own software
  (`calculate_contract`, checked against the node on 800 cases). When the output is spent, the spend must reveal
  that tweaked script.
- **From every Bitcoin transaction signed by a federation script.** The witness shape identifies these: a 626- or
  628-byte script with 11 signatures (normal path), or 2 signatures after the timelock (emergency path).

The reserve at a Bitcoin block is the sum of custody outputs that exist after it.

**Liabilities (L-BTC outstanding).** Peg-in claims, minus peg-outs, minus L-BTC explicitly destroyed, summed over
every Liquid block from genesis. Liquid's genesis block creates no L-BTC, and fees do not change the supply.

**Backing.**
- Gap = reserve − L-BTC outstanding, at each Bitcoin block and the Liquid block mapped to it. Ratio = reserve /
  L-BTC outstanding.
- The gap splits exactly into named components (`liquid/reserve_by_block`): deposits not yet claimed, payments into
  the program, deposits never claimed, federation fees, peg-outs in flight, unmatched outflows and burns. The
  residual is zero at every block.

**Flows.**
- **Peg-in:** a Bitcoin deposit and its Liquid claim, with the delay from deposit to claim.
- **Peg-out:** a Liquid peg-out request and the Bitcoin payment matched to it **one-to-one**.
  - Peg-outs are taken in Liquid order. Each takes the earliest unused federation payment to the same script, for
    the same amount, made no more than 2 hours (header-time tolerance) before the request.
  - One payment made earlier than that is matched and flagged `paid_before_pegout`.
  - Each payment serves at most one peg-out. Every payout equals the requested amount: the federation pays the
    Bitcoin fee from custody.
  - The delay is from request to payment.
- **Unexplained outflow:** an output paid by a federation transaction that no Liquid peg-out names.
- **Direct deposit:** a payment into a federation program by anyone else. It cannot be claimed as L-BTC.
- **Unclaimed deposit:** a deposit to a peg-in address that was never claimed, seen when the federation spent it.

**Emergency exposure.** Custody whose age has reached its script's timelock by the next block, so that the 2-of-3
emergency keys could spend it.

**Liveness.** Liquid blocks per UTC day against one block a minute (1,440). A gap is counted on the day of the block
that ends it.

**Incidents.** Incidents are selected by fixed rules, never by hand:
- reserve below liabilities: every run of Bitcoin blocks with reserve < L-BTC outstanding;
- any use of the emergency path;
- any unexplained outflow;
- any Liquid block gap of 1 hour or more;
- any redemption halt: 24 hours or more without a peg-out payment while a peg-out was waiting.

Each incident lists its transactions.

## 3. Verification classes

Every row of a common table says how its numbers are established (`metadata/verification_classes.json`):

| Class | Meaning | Examples |
|---|---|---|
| `bitcoin_verified` | Bitcoin blocks alone | direct deposits, emergency-path spends |
| `l2_chain_verified` | Liquid blocks alone | L-BTC outstanding, block production, the federation scripts |
| `cross_chain_verified` | one value from each chain, joined by a stated rule | custody (Bitcoin outputs, identified partly through Liquid claims), backing, peg flows, unexplained outflows |
| `inferred` | a modelling choice named in `method` | not used in v0.1's tables |
| `operator_reported` | the operator's statements | not used |

## 4. What the data cannot show

- **Who controls an address.** The data shows which outputs paid which; ownership is not on the chain.
- **Authorisation and intent.** A federation transaction carries valid signatures through a known path. The chain
  cannot show whether the key holders meant to sign, whether keys or software were compromised, or why.
- **Refused peg-out requests.** A request that never reached a Liquid block is invisible.
- **Deposits never claimed and never moved.** They are invisible until the federation spends them, so the reserve
  can be understated by such coins, never overstated.
- **Confidential amounts on Liquid.** v0.1 uses only explicit amounts: peg-ins, peg-outs and burns are explicit by
  construction. Other assets, USDt included, are not measured in v0.1.
- **Which functionaries signed a block.** Not measured in v0.1.

## 5. Known limits of v0.1

- **Sources.** The Liquid data comes from an audited import of an earlier extract up to Liquid block 4,050,000, plus
  our node from there on. A full re-extraction from our node's blocks is planned. Its checks are listed as
  `not_applicable` in `metadata/validation.json`.
- **Linking spends.** Above Bitcoin block 974,394, spends are linked by the first 8 bytes of the txid plus the output
  index. This matched the full links 4,251 of 4,251 times where both exist.
- **Missing txids.** 41 of the 42 unclaimed deposits lack a txid in our extract (`flows.btc_txid` is null). Their
  `btc_tx_key` (height and position in block) locates them.
- **Time mapping.** The Liquid–Bitcoin time mapping can shift a claim or payout by a few Bitcoin blocks. Daily
  tables use each UTC day's last Bitcoin block.
- **A snapshot, not a feed.** v0.1 is frozen at the cutoff. Later releases are new tags; old tags never change.

## 6. Reproducing a number

1. Confirm the files: `python3 scripts/verify_release.py`.
2. Read `metadata/release.json`. It gives the cutoffs, the SHA-256 of every input table the export read, and the
   commit of the pipeline that wrote this release.
3. Every common row names its source table in `method`. The Liquid tables in `liquid/` are those sources, at full
   detail.
