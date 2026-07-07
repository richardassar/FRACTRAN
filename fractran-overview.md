That last fetch also let me correct the canonical PRIMEGAME list (it ends `… 13/11, 15/2, 1/7, 55/1` — 14 fractions). Now I've got enough to go deep. Here's the whole landscape, in the order you laid it out.

---

## 0. The substrate: bignum + divisibility (and the better idea)

The naive interpreter is genuinely three lines: state is a big integer `n`, a step is "find the first fraction `a/b` with `n % b == 0`, set `n = n*a // b`." Python gives you arbitrary-precision ints and `%` for free; in C you'd reach for GMP (`mpz_divisible_p`, `mpz_mul`, `mpz_divexact`).

But the *right* representation isn't a monolithic bignum — it's a **sparse exponent vector**. Since `n = ∏ pᵢ^{rᵢ}`, the "registers" are the exponents `rᵢ`. Then:

- a fraction `a/b` is just two sparse vectors `(num, den)` over primes,
- "`b` divides `n`" becomes "the state vector dominates `den` componentwise" (`rᵢ ≥ denᵢ` for all `i`),
- applying it is `state = state − den + num`.

No multiplication, no giant integers, no `%`. This is **exponentially faster** and it exposes the deep truth: **FRACTRAN is a Vector Addition System with States (a Petri net / VASS)** where each transition has a nonnegativity guard and a priority order. That reframing is worth keeping in your pocket — it's why so much theory transfers.

## 1. The theory — why it computes

Underneath, FRACTRAN *is a Minsky register machine* written multiplicatively:

- **Each prime = a register.** Register `i` holds `rᵢ` = the exponent of `pᵢ` in `n`.
- **Multiplying by `pⱼ / pᵢ`** = "if register `i` > 0, decrement it and increment register `j`." The divisibility test *is* the "is register nonzero?" test.

Minsky machines with just two instructions — `INC` and "decrement-or-branch" — are already Turing-complete (2 counters suffice). FRACTRAN reaches them, so it's Turing-complete, and consequently its halting problem is undecidable. The only cleverness beyond raw registers is **control flow**, which is encoded by dedicating some primes as **state markers**: `n` always carries exactly one state prime with exponent 1, telling you "which line we're on." ([Minsky-machine equivalence](https://esolangs.org/wiki/Minsky_machine), [raganwald overview](https://raganwald.com/2020/05/03/fractran.html))

## 2. Compilation — the actual recipe

This is the part that turns FRACTRAN from a curiosity into a target you can *compile to*. Assign a distinct prime `q_r` to each register `r`, and a distinct prime `s_L` to each program line/label `L`. Keep the invariant: exactly one state prime present at a time.

| Instruction | Fractions (in this order) |
|---|---|
| `L: INC(r); goto M` | `(q_r · s_M) / s_L` |
| `L: DEC(r) goto M else N`  (if r>0: dec, goto M; else goto N) | `s_M / (s_L · q_r)` , then `s_N / s_L` |
| `L: HALT` | *(no fraction with `s_L` in a denominator)* |

The whole trick is **ordering**: FRACTRAN always fires the *first* applicable fraction, so listing the decrement fraction (which needs both `s_L` and `q_r`) before the fall-through (`s_N / s_L`) gives you exactly "if nonzero, decrement; else jump." Start the machine at `s_start · ∏ q_r^{input_r}`.

Two concrete Conway examples that pop right out of this:

- **Addition**, `2^a·3^b → 3^{a+b}`, is the single fraction **`3/2`**. It just keeps moving register-2 into register-3.
- **Multiplication**, `2^a·3^b → 5^{ab}`, is **`(455/33, 11/13, 1/11, 3/7, 11/2, 1/3)`** — primes 2,3 are inputs, 5 is the product, 7/11/13 are scratch+state: an outer loop over register-2 runs, `a` times, an inner loop that copies register-3 into register-5 while stashing a copy in register-7 so it can be restored for the next pass. ([Wikipedia](https://en.wikipedia.org/wiki/FRACTRAN))

So the compiler stack is: **tiny imperative language → Minsky IR (INC / DEC-branch) → fraction list with auto-assigned primes.** That middle IR is the sweet spot — everything (`while`, `if`, `+`, `−`, `*`, copy) lowers to it mechanically.

## 3. I/O — three models, because FRACTRAN has none natively

FRACTRAN is a *closed* function: starting integer → (maybe) halting integer. So I/O is pure convention on the encoding. There are three genuinely different regimes:

1. **Batch (function) I/O.** Inputs are exponents of chosen input primes in the start integer; outputs are exponents of chosen output primes in the halt integer. `f(a,b)`: start `2^a·3^b`, read the exponent of 5 at halt. This is the default and needs no runtime support.

2. **Streaming output (watch the tape).** The program *never halts*; you observe the trajectory and emit a value whenever the state matches a "print pattern." PRIMEGAME is exactly this — it emits a prime every time the state is a **pure power of 2**. Generalize it: dedicate a "print-flag" prime; whenever the host interpreter sees that flag set, it reads a value register and emits it, then the program clears the flag. Your interpreter grows a hook: *on each step, test a predicate, extract, print.*

3. **Interactive/streaming input.** Harder, because the machine is deterministic and closed. You interleave: run until the program *blocks* on an input register (it reaches a state whose only progress needs a register that's currently zero — an input request), the host injects the next input value into that register, and resumes. This makes FRACTRAN into a coroutine. It's the most fun and the least standard — worth building.

## 4. The self-interpreter

Yes — a FRACTRAN interpreter *written in FRACTRAN*. The record is **Chris Lomont's 48-fraction CLF-INTERPRET** (down from Jesse Beder's 1779 and an 84-fraction version). It encodes the object program and its state into one integer as `2^p · 3^s`: the program `p` is a **base-11** number where each fraction's numerator/denominator digits are interleaved and framed by delimiter digits (base-11 buys a spare "digit 10" to use as a separator). One simulated step = extract the next fraction by base-11 division, test divisibility by repeated subtraction, conditionally multiply, else restore and advance — with a handful of primes acting as flow-control tokens. There's a standing **code-golf competition** for the fewest fractions. ([Lomont](http://lomont.org/posts/2017/fractran/), [Beder's on GitHub](https://github.com/jbeder/fractran)) A great milestone for us: run Lomont's interpreter, on *our* host, interpreting PRIMEGAME — meta-circular, and a real correctness test.

## 5. POLYGAME and catalogue numbers

POLYGAME is Conway's **universal** FRACTRAN program from his 1987 paper. Instead of decoding a directly-encoded program (Lomont's approach), it works through a **catalogue**: give POLYGAME the input `c · 2^{2ⁿ}` and it outputs `2^{2^{f_c(n)}}`, where `c` is the **catalogue number** naming the partial-recursive function `f_c`. Every recursively enumerable function has such a `c`, and for many nice functions `c` is small and computable — so "programming" reduces to *looking up a number*. The doubly-exponential `2^{2ⁿ}` wrapping is the encoding hygiene that makes the universal decoding clean. The exact fraction list lives in [Conway's 1987 paper](https://www.cs.unc.edu/~stotts/COMP210-s23/madMath/Conway87.pdf) (I can pull the precise fractions and the catalogue construction from there on request — the googology page that tabulates catalogue numbers is currently paywalled).

## 6. Literature — the √2 paper *and* a richer seam than you expected

The √2 paper is real and recent: **"Computing √2 with FRACTRAN"** (Kaushik, Murphy, Weed, [arXiv:2412.16185](https://arxiv.org/abs/2412.16185), Dec 2024). It gives two programs:

- **√2GAME** — mirrors Conway's unpublished **PIGAME** (for π) but drives **Catalan's infinite product** √2 = (2·2)/(1·3) · (6·6)/(5·7) · (10·10)/(9·11) ⋯. Because √2 is *algebraic*, they get a **simpler convergence proof than Conway's π argument** (no irrationality-measure machinery), and that simplification carries *back* to clean up PIGAME. Start at `2ⁿ·173`, halt at `2^{d}` where `d` is the n-th decimal digit.
- **NR√2GAME** — encodes **Newton–Raphson** on `x²−2` directly: `x_{k+1} = (p²+2q²)/(2pq)`, quadratic convergence so `2n` iterations give `n` digits, state stored in registers `r₂₉`, `r₆₇`.

But the deeper seam: FRACTRAN has become a favorite **clean intermediate model in formalized undecidability proofs**. Larchey-Wendling & Forster used FRACTRAN in **Coq** to mechanize the reduction all the way to **Hilbert's Tenth Problem** ([Hilbert's Tenth in Coq](https://arxiv.org/pdf/2003.04604), [MSELL undecidability via FRACTRAN](https://members.loria.fr/DLarchey/files/papers/slides-fscd2021.pdf)). And there's the Conway thread that closes a loop you'll love: FRACTRAN grew out of the same circle of ideas as Conway's proof that **generalized Collatz functions are undecidable** — the Collatz map is essentially a tiny FRACTRAN-flavored system, and "does this Collatz-like program halt?" is undecidable. ([Conway 1987](https://www.cs.unc.edu/~stotts/COMP210-s23/madMath/Conway87.pdf))

## 7. What else could we do — thinking deeply

Ranked by "cool per unit effort," roughly:

1. **Build the real toolchain** — the natural spine of everything else: (a) a fast **exponent-vector interpreter** with tracing and a live register view, (b) a **Minsky-IR assembler** → fractions, (c) a **structured-language front end** (`while`/`if`/arithmetic → IR). Then Fibonacci, gcd, factorial, even **Ackermann** fall out as tests.
2. **A decompiler / visualizer** — given a bag of fractions, recover which primes are *state* vs *register*, rebuild the control-flow graph, and draw the finite-state machine hiding inside. This makes PRIMEGAME *legible*. Strong candidate for an interactive HTML artifact (state as a live bar chart of register exponents, firing fraction highlighted).
3. **The I/O coroutine layer** (§3) — then do playful things: a program that "prints" its trajectory as music, or a genuine **FRACTRAN quine** (a program whose emitted output re-encodes its own fraction list — buildable once you have the self-interpreter's encoding).
4. **Reproduce the gallery** — PRIMEGAME, PIGAME, √2GAME, NR√2GAME, and run **Lomont's self-interpreter under our interpreter under our interpreter**. Measure the blow-up; it's grotesque and delightful.
5. **Acceleration / JIT** — detect decrement loops and collapse "run this loop `r` times" into a single multiply (superoperator acceleration), or JIT a fraction list straight to native counter-machine code. FRACTRAN as *source*, not as *execution model*.
6. **Golf & extremes** — a **FRACTRAN busy beaver** (fewest fractions, longest finite run), or attack the self-interpreter fraction-count record.
7. **Theory writeups / formalization** — make the VASS/Petri-net correspondence precise, or prove our compiler correct (echoing the Coq work). This is where "esolang toy" turns into a real artifact.

**My recommendation for step one:** build #1 (vector-interpreter + Minsky assembler) in Python with a clean tracing view, verify it against the correct PRIMEGAME and the `3/2`/multiplication examples, then immediately layer on #2's register-view so we can *watch* the machine. Everything else — I/O, the √2 programs, the self-interpreter, acceleration — plugs into that spine.

Where do you want to start: the interpreter+assembler spine, the √2 reproduction, or the self-interpreter meta-circular stunt?

**Sources:** [arXiv:2412.16185 (√2)](https://arxiv.org/abs/2412.16185) · [Conway 1987 (POLYGAME/PIGAME)](https://www.cs.unc.edu/~stotts/COMP210-s23/madMath/Conway87.pdf) · [Lomont 48-fraction interpreter](http://lomont.org/posts/2017/fractran/) · [Beder's FRACTRAN-in-FRACTRAN](https://github.com/jbeder/fractran) · [Wikipedia: FRACTRAN](https://en.wikipedia.org/wiki/FRACTRAN) · [raganwald overview](https://raganwald.com/2020/05/03/fractran.html) · [Minsky machine (esolangs)](https://esolangs.org/wiki/Minsky_machine) · [Hilbert's Tenth in Coq](https://arxiv.org/pdf/2003.04604) · [MSELL via FRACTRAN in Coq](https://members.loria.fr/DLarchey/files/papers/slides-fscd2021.pdf)

---

# Part II — the toolchain (built)

## 3′. Streaming I/O: the trampoline

To get **both** streaming input and output, overload FRACTRAN's one native signal — halting — to mean three things, told apart by the marker prime present in the halt state:

- **READ** (`s_read` present) → program wants input; host injects the next symbol, resumes.
- **WRITE** (`s_write` present) → program has output; host reads/clears a register, emits, resumes.
- **DONE** (any other halt) → stop.

Between services it is ordinary deterministic FRACTRAN, so the system is a deterministic **stream transducer**: input/output events fall on one totally-ordered interaction trace. Three subtleties: **zero is invisible** (a register at 0 = an absent prime, so always deliver a separate *token* alongside data), **EOF needs its own token** (so "waiting" and "finished" differ), and **productivity** (the program must reach a READ/WRITE in finite time — undecidable in general).

Worked example — the interactive doubler (reads `n`, emits `2n`, forever). Registers `x=2`, `y=3`; markers `R=5`, `A=7`, `W=11`, `T=19`; tokens `d=13`, `e=17`:

```
7/65    # R: input delivered (d) -> A            [7/(5·13)]
19/85   # R: EOF (e) -> T (done)                  [19/(5·17)]
63/14   # A: x-=1, y+=2, stay in A               [(3²·7)/(2·7)]
11/7    # A: x exhausted -> W (write)
```

This adds no computational power (a batch program could pre-encode the stream) but changes the interaction model to an **online transducer**.

## 8. What we built

A small pure-Python package (`fractran/`, no dependencies), driven by `demo.py`:

| Module | Role |
|---|---|
| `core.py` | Exponent-vector interpreter — state is a sparse `prime → exponent` dict; a step is a guarded vector subtract-then-add. No big-integer multiplication ever happens. `run`, `run_iter`, `step`, `render`. |
| `io.py` | The READ/WRITE/DONE `trampoline` + a `stream_host` implementing the marker convention above. |
| `minsky.py` | Minsky IR (`Inc` / `Dec` / `Halt`) and `assemble` → fraction list, auto-allocating a prime per register and per label, one-hot program counter. |
| `build.py` | Structured front-end: CPS combinators (`seq`, `loop`, `while_nz`, `if_nz`) and macros (`move`, `copy`/`add`, `mul`) that lower to IR. |
| `programs.py` | Gallery: PRIMEGAME + prime extraction, the doubler, and compiled `add`/`multiply`/`fibonacci`/`factorial`. |
| `decompile.py` | Recover structure: `classify` finds registers vs one-hot control primes by simulation; `cfg`/`describe` rebuild the control-flow graph. |
| `viz.py` + `visualize.py` | Live terminal visualizer — register bars (exponent = length), the firing fraction highlighted, an emitted-event log. `watch` animates in place; `record` returns frames for testing. Run `python3 visualize.py primegame`. |
| `accel.py` + `bench.py` | Loop accelerator: runs the CFG and collapses any loop with a provably-constant per-iteration effect into `state += k·delta`. Each head is analyzed once and cached (`const` deltas applied in O(1); `invlin` re-measured cheaply via cached inner summaries). Exact vs. the reference interpreter. |
| `native/fractran_core.cpp` + `native.py` | Native C++ core for the hot loop, two modes: **vector** (int64 exponents — the fast path) and **canonical** (a real GMP integer `n`, the faithful/unbounded oracle). Built with `make -C native` (GMP from the conda env). `native.py` shells out and keeps the rest of the toolchain in Python. Parses factored fractions (`67^11*5/...`) so self-interpreter factors beyond 2^64 stay exact. |
| `gallery.py` + `gallery_demo.py` | External programs, transcribed exactly: Conway's PRIMEGAME (verified), his PIGAME (transcribed, execution-unverified — a digit needs >10⁹ steps), and Lomont's 48-fraction self-interpreter CLF-INTERPRET with its base-11 `encode` (encoder verified against Lomont's published value). |
| `bootstrap.py` + `bootstrap_demo.py` | A FRACTRAN **self-interpreter compiled from our own toolchain**: `make_interpreter(k)` builds a program that reads a k-fraction object program + `n` off the input stream and simulates it to halt. Verified against the reference interpreter for k=1,2,3 (105 / 187 / 269 fractions). Correct by construction. |
| `demos.py` + `fractran/demos.py` | Terminal I/O demos, each a compiled fraction list: `pyramid`/`bars` (ASCII graphics — FRACTRAN emits char codes, host does `chr`), `march` (animation, code 12 = clear frame), `rule30` (elementary cellular automaton, ~1624 fractions at width 31 — the chaotic triangle), `collatz`/`gcd` (numeric I/O). `python3 demos.py <name> [args]`, `--show` prints the fractions. |
| `serialize.py` + `measure_repr.py` | Compact binary format: a program as exponent vectors over dense prime *indices* (bases free — index i is the i-th prime), varint + zigzag; an interleaved and a compression-oriented **columnar** variant (both round-trip exact). Finding: raw binary ≈ decimal text, but columnar+gzip beats text+gzip on large regular programs (rule30: 7022 vs 8815 bytes). |
| `calc.py` + `fractran/calc.py` | A **calculator compiled to FRACTRAN** (188 fractions). Reads `op a b` triples from stdin, writes results to stdout via the I/O trampoline: `0`=add, `1`=mul, `2`=monus, `3`=divmod. `printf '3 17 5' \| python3 calc.py` → `3` then `2`. Op-dispatch is a nested `if_nz` chain; `divmod`/`monus` are the arithmetic macros. |

Verified by `demo.py` (all green): PRIMEGAME emits `2,3,5,7,11,13,17,19`; `3/2` adds; Conway's `MULTIPLY` multiplies; the doubler transduces `[3,0,5,7] → [6,0,10,14]`; compiled `fib(0..10)` and `factorial(0..6)` are exact; the decompiler recovers the compiled-`add` CFG exactly and blindly classifies Conway's `MULTIPLY` as registers `{2,3,5,7}` / control `{11,13}` — correctly flagging it as **not** strictly one-hot (Conway reuses the "no marker present" state as an implicit third control state).

## 9. Compiling streaming I/O

The compiler already lowers `while`/`if`/arithmetic to fractions; I/O is one more lowering, because the trampoline's only signal is *halting*. `read`/`write` compile to **halt-and-resume waits**, with a **flag prime** the host keys on and the **program-counter label** preserving where to resume — that decoupling is what lets arbitrarily many I/O sites coexist:

- **`read(x)`** — raise a read-flag `RF`, move the PC to a wait label, and halt (no fraction fires while `RF` is up but no token is present). The host sees `RF`, deposits the next value into channel `IN` plus a `delivered` token — or an `eof` token at end of stream. Resume fractions: `on_got /(wait·delivered·RF)` and `on_eof /(wait·eof·RF)`; then `IN` is moved into `x`. The absence of a fallback fraction is exactly what makes it wait.
- **`write(x)`** — copy `x` into channel `OUT`, raise `WF`, halt. The host drains `OUT`, emits it, drops a `done` token; resume fraction `next /(wait·done·WF)`.

`ReadWait`/`WriteWait` IR nodes (`minsky.py`) emit those fractions; `read_until_eof`/`write` combinators (`build.py`) build them; `io_host` (`io.py`) services any read/write flag generically. `io_demo.py` compiles two stream transducers from structured code and runs them through the trampoline: an **echo-doubler** (`[3,0,5,7] → [6,0,10,14]`, 33 fractions — the invisible-zero handled by the delivered token) and a **running sum** (`[3,1,4,1,10] → [3,4,8,9,19]`, 24 fractions — state persists across reads). The hand-written `DOUBLER` from §3′ is now a *compiled* artifact.

## 10. Bootstrapping

The verified compiler makes a *correct* self-interpreter buildable — the honest fix for the Lomont transcription that decoded but wouldn't simulate. The ladder:

- **Rung 0 (done):** the compiler is verified.
- **Rung 1 (done):** `bootstrap.make_interpreter(k)` — a FRACTRAN program, compiled from our structured language, that reads a k-fraction object program + object `n` off the input stream (the streaming-I/O mechanism), runs the scan-apply-restart loop, and writes the result. Verified against the reference. The one hard primitive is `b | n` / `n ← (n/b)·a` on `n` as a unary magnitude — the `divmod_` macro (36 fractions, exact), the slow beating heart of every FRACTRAN self-interpreter.
- **Rung 2 (next):** the interpretation *tower*. Nesting (interpreter interpreting the interpreter) needs the object program **encoded into `n`** (Gödel-style) rather than read via I/O — an object program run *inside* another can't do stream I/O. That's the encoded-input variant to build next.
- **Rung 3:** self-hosting — compile `assemble` (IR → fractions) itself to FRACTRAN.

## 11. Visualization (`fractran/plot.py`)

All graph images go through one renderer and one style object, so a look change in
one place propagates everywhere.

**The graph.** `build_multiway(prog, starts, max_states)` grows the *multiway*
(nondeterministic) reachability graph: from each integer state, fire **every**
applicable fraction, keep the integer successors, iterate from the start(s). It
returns `(nodes, efrac, sources)` where `efrac[(a,b)]` is the index of the
fraction that produced edge `a→b`. (This is `reachability.reachable` unioned over
starts; deterministic/one-hot compiled programs give a single path, hand-written
multi-fraction programs branch.)

**The renderer.** `draw_graph(ax, nodes, efrac, pos, values, nfrac, style)` draws
fraction-coloured directed edges (each edge dim-tail → bright-head to show
direction) and nodes coloured by `values`. `Style` (the module default `STYLE`)
holds `node_size`, `node_cmap`, `node_floor`, `node_alpha`, `edge_cmap`,
`edge_lw`, `edge_alpha`, `tail_dim`, `dpi` — edit one field and every image
restyles. Layout is `graph_layout` (force-directed) or the exponent lattice for
two-prime programs.

**Node fields** (`node_field` / `NODE_FIELDS`) — structural and *spectral*
colourings of the same lattice; the spectral ones are graph signal processing on
the Pontryagin dual (`theory.md`/`explorations.md` §4):

| field | meaning | code |
|---|---|---|
| `depth` | BFS distance from the source (flow) | `node_depths` |
| `logn` | `log n` (the height / Bost–Connes energy) | `logn_values` |
| `fiedler` | 1st non-trivial Laplacian eigenvector — the lowest **graph-Fourier / Pontryagin** mode | `laplacian_harmonic(·,1)` |
| `harmonic2`,`harmonic3` | higher graph-Fourier modes; their nodal domains expose community/bottleneck structure | `laplacian_harmonic` |
| `chebyshev` | **Chebyshev**-polynomial graph filter `T_k(L̃)δ` from the source (GSP) | `chebyshev_response` |
| `wavelet` | spectral graph wavelet `(e^{-t₁L}-e^{-t₂L})δ` (difference of heat kernels) | `graph_wavelet` |
| `markov` | slow **random-walk** (Markov) mode — the metastable reaction coordinate | `markov_mode` |
| `stationary` | random-walk stationary `π ∝ degree` | `stationary_dist` |
| `heat` | heat kernel `exp(-tL)δ` diffused from the source | `heat_kernel` |
| `commute` | effective resistance / commute-time to the source (truncated spectral sum) | `commute_resistance` |

**Plot functions.** `plot_multiway(prog, starts, out, node_by=…)` — one lattice,
one colouring. `plot_spectral_gallery(prog, start, out, fields)` — one lattice by
many fields (layout computed once). `plot_network` — a reachability network with a
choice of layout (`kamada` for divisor-lattice hypercubes). `plot_multiway_montage`
— a grid across programs. `plot_reachability` — the small labelled graph behind
`reach.py --plot` and `plot_reach.py`. Plus line-art specials: `plot_collatz_coral`
(all Collatz trajectories to 1, with chosen runs highlighted), `plot_spacetime`
(the prime-exponent space-time heatmap of a run), `plot_rule30` (the Rule 30
triangle). Assets live in `assets/`.

**Conway flowcharts.** `plot_conway(prog, start, out)` draws a program the way
Conway did (his 1987 paper §7): a **register-machine flowchart** — one node per
program *line* / control state, each fraction a directed edge to the line it jumps
to (labelled with the fraction and its register `−dec`/`+inc` effect), the number
of arrowheads giving that fraction's **priority** at the node (single = first tried,
double = next, amalgamated for adjacent priorities), plus self-loops, a start stub,
and stop stubs. This is the *finite, collapsed* machine, independent of the input:
the control states are recovered from the bare fraction list by `decompile.classify`
/ `decompile.cfg`, so it works directly on a raw program. It is cleanest on compiled
(one-hot) programs; hand-golfed lists such as Conway's own MULTIPLY only decompile
heuristically. Layout uses graphviz `dot` (via `pydot`) when available, else the
built-in layered fallback `_layered_layout`.

**Themes.** Every renderer takes `style=`. `THEMES` provides `dark` (default),
`light`, `paper`, and `transparent`; a `Style` with `bg=None` renders on a
transparent background (`transparent=True` at save time). Construct any
`Style(node_size=…, node_cmap=…, edge_cmap=…, node_alpha=…, bg=…)` and pass it —
background colour and all other settings are user-controllable from that one object,
and `draw_graph` honours it everywhere.

## Roadmap status

- [x] **#1 Spine** — vector interpreter + tracing, Minsky assembler, structured front-end. Tests: fib, factorial.
- [x] **#3 I/O** — the streaming trampoline (READ/WRITE/DONE).
- [x] **#2a Decompiler** — register/control classification + CFG recovery (text).
- [x] **#2b Visualizer** — live terminal renderer (`viz.py`/`visualize.py`): register bars, firing fraction highlighted, emitted-event log; PRIMEGAME made legible.
- [x] **#5 Acceleration** — runtime loop-summarizer over the CFG (`accel.py`), analyze-once/apply-cheap. Exact vs. the reference. Measured: `mul` → O(1) (100,300×), `fib`/`factorial` → O(n) (`100!` in 1,402 ops, `fib(1000)`/209 digits in 11,000 ops). Non-constant loops (e.g. `f*=n`) fall back to stepping. Next depth here: symbolic affine summaries (matrix-power `fib` in O(log n)).
- [x] **Native C++/GMP core** — `native/fractran_core.cpp`. Vector mode ~**130×** over the Python stepper (103M steps/s on PRIMEGAME); GMP canonical mode agrees exactly and shows the authentic big-integer cost (drops to 338k/s once `n` becomes `5^14400` in MULTIPLY — the reason the vector view exists). Next: `int64`→GMP exponent promotion for accelerated runs that overflow.
- [x] **Bootstrap** — a FRACTRAN self-interpreter compiled from our verified toolchain (`bootstrap.py`), reading its object program via streaming I/O; verified for k=1,2,3. The correct, own-toolchain answer to the meta-circular goal.
- [~] **#4 Gallery** — PRIMEGAME runs on the native core (verified, first 15 primes). Lomont's 48-fraction CLF-INTERPRET transcribed (matches source, 32 primes) and its base-11 encoder **verified** against Lomont's published `284533968840`; running it completes the decode phase but not object simulation — the post gives no worked trace and calls the program unoptimized, so the run recipe is underspecified. PIGAME transcribed (40 fractions) but execution-unverified: a single digit needs >10⁹ steps and sources disagree on a few fractions. √2GAME/NR√2GAME not yet transcribed (paper renders them from a flowchart). Honest status, not faked.
- [ ] **#6 Golf / busy-beaver**, [ ] **#7 theory writeup** (VASS/Petri-net correspondence, compiler-correctness).
