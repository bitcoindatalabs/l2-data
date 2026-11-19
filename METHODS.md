# Methods: L2 audit dataset (release v0.1.1, Liquid)

This note is for readers of the dataset and of L2 Watch. It gives the definitions, the cutoffs, the verification
classes and the known limits. Every table and column is in `metadata/data_dictionary.md`. The checks this release
passed are in `metadata/validation.json`. Changes between releases are in [CHANGELOG.md](CHANGELOG.md).

> **Correction (2026-11-18, bdl-098).** Release v0.1 (tag `v2026.11.18`, never published) understated the
> emergency exposure of 2018–2022. It gave the federation's 2018–2023 change address (`a914 8ed14f3b…87`) the
> 4,032-block timelock of the 2018 peg script. That script's own timelock is **2,016 blocks**: it is the 2018 peg
> script with only the timelock changed. Its full script is known because exactly one timelock makes it hash to the
> witness script that all 26,210 of its spends reveal on Bitcoin. v0.1's statement that "the timelock is 4,032
> Bitcoin blocks for the 2018 … script" was right for the peg script but wrong for the outputs that used this
> change script. With the correct timelock:
> - the largest custody the 2-of-3 emergency keys could have spent is **870.06 BTC**, after Bitcoin block 634,326
>   (2020-06-12, 40.3% of the reserve), for 3 blocks. v0.1 said 20.02 BTC (2019-01-20);
> - 2,477 change outputs became spendable that way (13,344.71 BTC, each counted once). v0.1 counted 288.
> 
> The operator disclosed the cause in June 2020 (`incidents`, kind `timelock_lapse`). Only `csv_blocks`, the
> exposure columns and the tables built on them changed; reserve, supply, gap, flows and every September 2026
> figure are unchanged (CHANGELOG.md).

## 1. Sources and cutoffs

| | Source | Cutoff (v0.1 and v0.1.1) |
|---|---|---|
| Bitcoin | every block from height 540,000 (before Liquid's first peg-in, 542,409), read from our own full chain extract | block **976,206** (`…1867e22c3c462ddd71f91a71a8c3c98b703f238320a0e`, 2026-11-17 02:10:32 UTC) |
| Liquid | every block from genesis, read from our own Elements 23.3.3 node (chain `liquidv1`) | block **4,148,532**: the last Liquid block whose header time is at or before the Bitcoin cutoff's |

- Times are block header times in UTC. Bitcoin header times can be off by up to about two hours, and Liquid's by a
  few seconds.
- **Mapping Liquid to Bitcoin:** each Bitcoin block is paired with the last Liquid block whose header time is at or
  before the Bitcoin block's. Liquid times are made non-decreasing first (running maximum).
- No number in this release comes from the federation, Blockstream, an exchange or the press. One operator
  statement is cited as the stated cause of an incident (`incidents.references`, kind `timelock_lapse`); the numbers
  in that row are chain facts.

## 2. Definitions (Liquid)

**Federation scripts.** We read Liquid's peg script (the *fedpegscript*) at every DynaFed epoch start from the node.
Four peg scripts have been current since 2018 (`control`, `liquid/fedpeg_generations.json`). From 2018 to 2023 the
federation also sent its change to a fifth script, which is not a Liquid parameter: the 2018 peg script with another
timelock (`control`, role `custody_change`). Each has two spending paths:
- the **normal** path: 11 of 15 functionary keys;
- the **emergency** path: 2 of 3 emergency keys, usable only after a relative timelock (CSV). The timelock is 4,032
  Bitcoin blocks for the 2018, 2023 and January 2026 peg scripts, 8,064 for the July 2026 peg script, and **2,016
  for the 2018–2023 change script**.

Each custody output takes the timelock of **its own script**. For an output paying a federation script, that is the
script's CSV. For a peg-in deposit, it is its peg script's CSV, because the peg-in tweak changes only keys. A check
compares this, for every spent output, with the CSV of the script its spend reveals. The 42 deposits that no peg-in
claimed are the exception: without a claim, the tweak and so the full script are unknown. They take the shortest
timelock of any peg script of the same length (4,032), which is conservative.

`control` also lists the five block-signing key sets (11 of 15) that have signed Liquid's blocks since 2018.

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

**Emergency exposure.** Custody whose age has reached its own script's timelock by the next block, so that the
2-of-3 emergency keys could spend it.

**Liveness.** Liquid blocks per UTC day against one block a minute (1,440). A gap is counted on the day of the block
that ends it.

**Incidents.** Most incidents are selected by fixed rules, never by hand:
- reserve below liabilities: every run of Bitcoin blocks with reserve < L-BTC outstanding;
- any use of the emergency path;
- any unexplained outflow;
- any Liquid block gap of 1 hour or more;
- any redemption halt: 24 hours or more without a peg-out payment while a peg-out was waiting.

Since v0.1.1, three kinds are not rule-selected, and `kind` and `detection_rule` say so:
- `timelock_lapse`: an incident the operator disclosed, located on Bitcoin. The 2018–2020 change-script lapse runs
  from the first to the last block in which a change output of 0.001 BTC or more was spendable by the emergency keys
  (2018-11-16 to 2020-07-01). Its numbers are chain facts; the cause is the operator's statement, cited in
  `references`.
- `event_summary`: the September 2026 event as a forensic review (Bitcoin Data Labs) grouped it. Its figures are
  checked against the tables, and its `method` names the rule-detected rows it groups.
- `coin_trace`: the same review's value-weighted trace of the coins that left custody in September 2026, to the
  payments back. It is `inferred`: how much of a payment comes from which earlier coin is a modelling choice.

Each incident lists its transactions.

## 3. Verification classes

Every row of a common table says how its numbers are established (`metadata/verification_classes.json`):

| Class | Meaning | Examples |
|---|---|---|
| `bitcoin_verified` | Bitcoin blocks alone | direct deposits, emergency-path spends |
| `l2_chain_verified` | Liquid blocks alone | L-BTC outstanding, block production, the federation scripts |
| `cross_chain_verified` | one value from each chain, joined by a stated rule | custody (Bitcoin outputs, identified partly through Liquid claims), backing, peg flows, unexplained outflows |
| `inferred` | a modelling choice named in `method` | the September 2026 coin trace (`incidents`, kind `coin_trace`) |
| `operator_reported` | the operator's statements | not used: the one operator statement cited (`incidents.references`) is a source for a cause, not for a number |

## 4. What the data cannot show

- **Who controls an address.** The data shows which outputs paid which; ownership is not on the chain.
- **Authorisation and intent.** A federation transaction carries valid signatures through a known path. The chain
  cannot show whether the key holders meant to sign, whether keys or software were compromised, or why.
- **Refused peg-out requests.** A request that never reached a Liquid block is invisible.
- **Deposits never claimed and never moved.** They are invisible until the federation spends them, so the reserve
  can be understated by such coins, never overstated.
- **Confidential amounts on Liquid.** This release uses only explicit amounts: peg-ins, peg-outs and burns are
  explicit by construction. Other assets, USDt included, are not measured yet.
- **Which functionaries signed a block.** Not measured in this release.

## 5. Known limits of v0.1.1

- **Sources.** The Liquid data comes from an audited import of an earlier extract up to Liquid block 4,050,000, plus
  our node from there on. A full re-extraction from our node's blocks is planned. Its checks are listed as
  `not_applicable` in `metadata/validation.json`.
- **Linking spends.** Above Bitcoin block 974,394, spends are linked by the first 8 bytes of the txid plus the output
  index. This matched the full links 4,251 of 4,251 times where both exist.
- **Missing txids (fixed in v0.1.1).** In v0.1, 41 of the 42 unclaimed deposits had no txid (`flows.btc_txid`
  null). v0.1.1 reads their transactions from our Bitcoin extract. Each is checked by value, and its script against
  the witness script hash the federation's spend reveals.
- **Time mapping.** The Liquid–Bitcoin time mapping can shift a claim or payout by a few Bitcoin blocks. Daily
  tables use each UTC day's last Bitcoin block.
- **A snapshot, not a feed.** Each release is frozen at its cutoff. Later releases are new tags; old tags never
  change. v0.1.1 has the same cutoffs as v0.1.

## 6. Reproducing a number

1. Confirm the files: `python3 scripts/verify_release.py`.
2. Read `metadata/release.json`. It gives the cutoffs, the SHA-256 of every input table the export read, and the
   commit of the pipeline that wrote this release.
3. Every common row names its source table in `method`. The Liquid tables in `liquid/` are those sources, at full
   detail.
