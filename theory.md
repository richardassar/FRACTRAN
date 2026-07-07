# The Mathematics of FRACTRAN

*A theoretical landscape: prime valuations, additive lattices, vector addition
systems, binomial and toric ideals, p-adic and height dynamics, universality,
and the boundary of decidability.*

---

## 0. Orientation

FRACTRAN [Conway 1987] is deceptively small. A program is a finite ordered list
of positive rationals $f_1, \dots, f_k$; a state is a positive integer $n$; one
step replaces $n$ by $n f_i$ for the least $i$ with $n f_i \in \mathbb{Z}$, and
the machine halts when no such $i$ exists. That is the entire definition, and it
is Turing-complete.

The reason so much mathematics is visible through this pinhole is a single
change of coordinates: **take logarithms in the prime basis.** Everything that
follows is a consequence of the fundamental theorem of arithmetic reread as an
isomorphism of groups, together with two extra ingredients — *nonnegativity
guards* and a *priority order* — that inject exactly enough structure to make the
system universal, and therefore undecidable, and therefore rich.

This document develops the picture in layers, each a different mathematical
discipline seeing the same object: multiplicative number theory (§1–3),
computability and automata (§4–5), commutative algebra (§6), arithmetic
dynamics and heights (§7), recursion theory (§8), and a deliberately honest
account of what is *not* here — elliptic curves and the genus-1 world (§9).
Throughout, the connection to the accompanying implementation is noted, because
the abstractions are not decorative: they are literally the data structures.

---

## 1. The fundamental isomorphism: multiplication *is* addition on a lattice

Write $\mathbb{Q}_{>0}$ for the multiplicative group of positive rationals. The
fundamental theorem of arithmetic is precisely the statement that the map

$$
v : \mathbb{Q}_{>0} \xrightarrow{\ \sim\ } \bigoplus_{p\ \text{prime}} \mathbb{Z},
\qquad
n \longmapsto \big(v_p(n)\big)_{p},
$$

sending a rational to its vector of **prime exponents** $v_p$, is an isomorphism
of abelian groups: multiplication becomes coordinatewise addition, and the
direct sum is *restricted* (all but finitely many coordinates are zero). The
group $\bigoplus_p \mathbb{Z}$ is the free abelian group on the primes — a
countable-rank lattice — and it is the **character lattice of the
infinite-dimensional algebraic torus** $\mathbb{G}_m^{\infty}$. This is the first
and last fact one needs; every later section is a specialization of it.

Under $v$:

- a **state** $n$ is the exponent vector $\mathbf{e} = (v_p(n))_p \in \mathbb{N}^{(\infty)}$ (nonnegative because $n$ is an integer);
- a **fraction** $f = a/b$ is the pair of its numerator and denominator vectors $(\boldsymbol\alpha, \boldsymbol\beta)$ with $\boldsymbol\alpha = v(a)$, $\boldsymbol\beta = v(b)$;
- the **guard** $b \mid n$ becomes componentwise dominance $\mathbf{e} \ge \boldsymbol\beta$;
- **applying** $f$ becomes the translation $\mathbf{e} \mapsto \mathbf{e} + (\boldsymbol\alpha - \boldsymbol\beta)$.

So a FRACTRAN program is a finite set of lattice vectors $\boldsymbol\delta_i =
\boldsymbol\alpha_i - \boldsymbol\beta_i$ (the *moves*), each equipped with a
guard $\boldsymbol\beta_i$ and a priority index $i$, acting on the nonnegative
orthant $\mathbb{N}^{(\infty)}$. Multiplication of astronomically large integers
is replaced by addition of small, sparse integer vectors — which is exactly why
the vector interpreter in `core.py` never forms the giant integer, why the
native core stores `int64` exponents, and why `serialize._delta` records the
$\boldsymbol\delta_i$ directly. The "canonical" execution mode that carries the
literal element of $\mathbb{Q}_{>0}$ is the *only* place the isomorphism is run
backwards, and it is exponentially more expensive — a first hint that the
additive side is where the real structure lives.

---

## 2. The state is a vector of $p$-adic valuations

The coordinate $v_p$ is not an arbitrary label: it is the **$p$-adic valuation**,
the same function that defines the $p$-adic absolute value $|x|_p = p^{-v_p(x)}$
and the $p$-adic completion $\mathbb{Q}_p$. A FRACTRAN state is thus a point of
the restricted product $\prod'_p \mathbb{Z}$ of the value groups, i.e. an element
of $\bigoplus_p \mathbb{Z} \subset \prod_p \mathbb{Z}_p$ sitting inside the ring
of finite adeles' integral part.

Two things are worth making precise.

**The guard is a system of $p$-adic inequalities.** "Fraction $a/b$ is
applicable at $n$" is the conjunction, over all primes, of the local conditions
$v_p(n) \ge v_p(b)$ — a statement in each $\mathbb{Z}_p$ separately. FRACTRAN is
therefore a machine that reads and writes the *integer parts* of $p$-adic
valuations and branches on $p$-adic comparisons. It uses the valuations but not
the $p$-adic *topology* (no limits, no completion): it lives in the value group
$\mathbb{Z}$, the "tropical" or "skeleton" shadow of $\mathbb{Q}_p$.

**Where the full $p$-adic analysis does appear: Collatz.** FRACTRAN is Conway's
generalization of the $3x+1$ iteration, and the $3x+1$ world is genuinely
$2$-adic. The Collatz map $T$ (with $T(2m)=m$, $T(2m{+}1)=(6m{+}4)/2$) extends to a
continuous, measure-preserving map on $\mathbb{Z}_2$; Lagarias's parity map
$Q_\infty(x) = \sum_k t_k 2^k$, where $t_k$ is the parity of $T^{(k)}(x)$, records
the itinerary, and Bernstein and Lagarias proved that $Q_\infty$ **conjugates $T$
to the $2$-adic shift** $x \mapsto x/2$ with an explicit inverse built from powers
of $3^{-1}$ [Lagarias 1985; Bernstein–Lagarias 1996; Matthews]. The parity vector
— which residue class mod $2$ the orbit meets at each step — is precisely the data
a FRACTRAN encoding of Collatz manipulates. The `collatz` demo in this repository
computes that itinerary by testing $v_2(n) > 0$ (via `divmod` by $2$) and
branching, which is the $2$-adic coordinate made mechanical. Conway's own results
on the *undecidability* of the general family [Conway 1972; Conway 2013] are the
computational face of the same $p$-adic dynamics, and are taken up in §7.

---

## 3. Register machines: guards + priority = a zero test

Assign a distinct prime to each **register** and each **control line** of a
counter machine. Minsky machines [Minsky 1967] need only two instruction
shapes — $\mathrm{INC}(r)$ and "decrement-$r$-or-jump-if-zero" — and two counters
suffice for Turing-completeness. Their compilation to fractions is exact:

$$
\begin{aligned}
L:\ \mathrm{INC}(r)\to M &\ \rightsquigarrow\ \frac{q_r\, s_M}{s_L},\\[2pt]
L:\ \mathrm{DEC}(r)\to M\ \text{else}\ N &\ \rightsquigarrow\ \frac{s_M}{s_L\, q_r},\ \ \frac{s_N}{s_L}\quad(\text{in this order}).
\end{aligned}
$$

The one-hot control prime $s_L$ is the program counter; $q_r$ is register $r$.
The subtlety — and the whole source of computational power — is the **order**.

**Priority is a zero test.** A single fraction, viewed additively, is a *guarded
translation*: it fires only where the state dominates the guard. That alone is
the primitive of a Petri net (§5), and Petri nets are famously *unable to test a
place for zero*. FRACTRAN recovers the zero test from the priority rule: the
decrement fraction $s_M/(s_L q_r)$ requires $q_r \ge 1$ and is listed *first*, so
the fall-through $s_N/s_L$ fires **exactly when $r = 0$**. "Do the next fraction
only if all earlier ones are disabled" is precisely an *inhibitor arc*, and
inhibitor arcs are exactly what lift Petri nets to Turing power [Agerwala 1974;
Hack 1976]. This is not an analogy; it is the mechanism. In the additive picture,
determinism-by-priority is the ingredient that a plain vector addition system
lacks, and it sits exactly on the decidability boundary drawn in §5.

Consequences are immediate: FRACTRAN is Turing-complete, its halting problem is
undecidable, and by Rice's theorem essentially every nontrivial semantic
property of a fraction list is undecidable. The compiler in `minsky.py`
implements the table above; the decompiler in `decompile.py` inverts it,
recovering the control-flow graph by detecting the one-hot control primes — a
concrete witness that the register-machine structure is really *there* inside the
fractions and can be read back out.

---

## 4. Universality, catalogues, and the mechanized reductions

Conway went further than Turing-completeness and exhibited a *universal* program,
**POLYGAME**, together with a system of **catalogue numbers**: for a suitable
encoding, running POLYGAME on input $c\cdot 2^{2^{n}}$ yields $2^{2^{f_c(n)}}$,
where $c$ is the catalogue number of the partial-recursive function $f_c$
[Conway 1987]. Every recursively enumerable function has such a $c$; programming
becomes *choosing an integer*. This is a Gödel numbering / acceptable programming
system in the sense of recursion theory, with all the usual apparatus (an
$s$-$m$-$n$ theorem, a universal machine, fixed-point/recursion theorems, and
hence self-reference — the self-interpreters of Beder and Lomont, and the one
compiled from our own toolchain in `bootstrap.py`).

FRACTRAN's cleanest modern role is as an **intermediate language in mechanized
undecidability proofs**. Larchey-Wendling and Forster's Coq formalization of
Hilbert's Tenth Problem — the first full mechanization of the
Davis–Putnam–Robinson–Matiyasevich theorem — routes through the chain

$$
\textsf{Halt} \preceq \textsf{PCP} \preceq \textsf{MM} \preceq \textsf{FRACTRAN} \preceq \textsf{DIO},
$$

using FRACTRAN precisely *because* "FRACTRAN is very natural to describe using
polynomials," which makes the final reduction to Diophantine equations short and
comprehensible [Larchey-Wendling–Forster 2019; cf. Davis–Putnam–Robinson 1961;
Matiyasevich 1970]. The reason FRACTRAN is "natural with polynomials" is exactly
the monomial dictionary of §6.

---

## 5. Vector addition systems: the decidability fault line

Strip the priority order from FRACTRAN — fire *any* applicable fraction
nondeterministically — and what remains is exactly a **Vector Addition System
with States** (equivalently a Petri net): each fraction is a transition whose
input multiplicities are $\boldsymbol\beta_i$ (the denominator) and output
multiplicities $\boldsymbol\alpha_i$ (the numerator), enabled when the marking
dominates the input, with net effect $\boldsymbol\delta_i$. The primes are the
*places*; the state is the *marking*.

The two systems live on opposite sides of a sharp line:

| | nondeterministic (plain VAS/Petri net) | deterministic priority (FRACTRAN / Minsky) |
|---|---|---|
| extra power | none | zero test (inhibitor arc) |
| reachability | **decidable**, Ackermann-complete | **undecidable** |
| model | vector addition system | counter machine, Turing-complete |

For plain VAS, reachability was shown EXPSPACE-hard [Lipton 1976], decidable
[Mayr 1981; Kosaraju 1982], given an Ackermannian upper bound
[Leroux–Schmitz 2019], and finally proved **Ackermann-complete** — settling a
problem open for 45 years — independently by Leroux and by Czerwiński and
Orlikowski in 2021 [Leroux 2021; Czerwiński–Orlikowski 2021]. That the problem is
*decidable at all* is remarkable and rests on the well-quasi-ordering of
$\mathbb{N}^d$ (Dickson's lemma) and the theory of well-structured transition
systems; **coverability** (can we reach a marking $\ge$ a target) is easier,
EXPSPACE-complete, precisely because it is monotone.

The single ingredient that pushes the decidable Ackermannian VAS all the way to
undecidable Turing power is the zero test of §3. FRACTRAN is therefore best
understood as *the minimal deterministic completion of a vector addition system*
— the smallest thing you can add (a fixed firing priority) to a Petri net to make
it universal. Everything undecidable about FRACTRAN, and everything rich, lives in
that one added bit of structure.

---

## 6. Binomial, lattice, and toric ideals: the commutative-algebra view

Return to the monomial dictionary. Identify the state $n=\prod_p p^{e_p}$ with the
monomial $\mathbf{x}^{\mathbf e} = \prod_p x_p^{e_p}$ in the polynomial ring
$k[x_2, x_3, x_5, \dots]$. Then:

- a fraction $a/b$ is the **binomial** $\mathbf{x}^{\boldsymbol\alpha} - \mathbf{x}^{\boldsymbol\beta}$;
- the move $\boldsymbol\delta = \boldsymbol\alpha - \boldsymbol\beta \in \mathbb{Z}^{(\infty)}$ is its exponent difference;
- applying $a/b$ at $n$ is a **monomial rewrite**: if $\mathbf{x}^{\boldsymbol\beta} \mid \mathbf{x}^{\mathbf e}$, replace $\mathbf{x}^{\mathbf e}$ by $\mathbf{x}^{\mathbf e + \boldsymbol\delta}$.

This lands FRACTRAN squarely in the world of **binomial ideals** and **lattice
ideals** [Eisenbud–Sturmfels 1996]. The moves $\boldsymbol\delta_i$ generate a
sublattice $\mathcal L \subseteq \mathbb{Z}^{(\infty)}$; its **lattice ideal**
$I_{\mathcal L} = \big(\mathbf{x}^{\boldsymbol\delta^+} -
\mathbf{x}^{\boldsymbol\delta^-} : \boldsymbol\delta \in \mathcal L\big)$ (with
$\boldsymbol\delta = \boldsymbol\delta^+ - \boldsymbol\delta^-$ the positive/
negative parts) is a **toric ideal** when $\mathcal L$ is saturated. In the
language of algebraic statistics, a generating set of moves is a **Markov basis**,
and the Fundamental Theorem of Markov Bases [Diaconis–Sturmfels 1998] says a
Markov basis of a toric ideal is exactly a set of binomial generators — the moves
that connect all lattice points with the same image under the toric map, by
walks that stay nonnegative. This is the precise sense in which a FRACTRAN
program is "a set of Markov moves," and the connection between reachability and
**lattice walks** and primary decomposition of binomial ideals is developed in
[Diaconis–Eisenbud–Sturmfels 1998; Sturmfels 1996].

Two caveats sharpen the analogy rather than dissolve it, and they recover the
undecidability from a world (commutative algebra) that is otherwise tame.

1. **Toric reachability is reversible and decidable; FRACTRAN's is not.** The
   toric/lattice ideal treats moves as bidirectional ($\pm\boldsymbol\delta$),
   and membership/connectivity questions reduce to linear algebra over
   $\mathbb{Z}$ plus a saturation. FRACTRAN's moves are **oriented** (only
   $+\boldsymbol\delta$) and **guarded** (only where $\mathbf{x}^{\boldsymbol\beta}$
   divides), i.e. a one-directional, nonnegativity-constrained rewriting — the
   VAS of §5. Orientation + guard is what turns decidable lattice geometry into
   undecidable reachability.

2. **The priority order is not a term order.** FRACTRAN reduces by the *program's*
   fixed list order, not by a monomial order, and the resulting rewriting system
   is deliberately *non-confluent* (the whole point is that the order matters).
   So this is emphatically **not** Gröbner reduction; it is a prioritized,
   non-confluent binomial rewriting system. The contrast is instructive: Gröbner
   theory buys termination and confluence at the cost of computing a basis;
   FRACTRAN keeps a fixed finite basis and spends the difference on
   undecidability.

This dictionary is also why the Coq proof of §4 finds FRACTRAN "natural with
polynomials": a step is a binomial substitution, and a run is a chain of them,
which is immediately a Diophantine statement.

---

## 7. Heights and arithmetic dynamics

Take a second logarithm. The **size** of a state is

$$
\log n \;=\; \sum_p v_p(n)\,\log p \;=\; \sum_p e_p \log p,
$$

which for the rational $n$ is its **logarithmic Weil height** $h(n)$
[Bombieri–Gubler 2006]. A FRACTRAN step changes the height by the fixed real
number $\log(a_i/b_i) = \langle \boldsymbol\delta_i, (\log p)_p\rangle$. A
trajectory is therefore a walk on the height line whose increments are chosen,
by the priority rule, as a function of *which residue classes* the current state
occupies (i.e. which guards hold) — a **piecewise-multiplicative discrete
dynamical system**.

This is exactly Conway's family of **periodically piecewise-linear** maps: a
function $g$ with $g(n) = a_i n / b_i$ whenever $n \equiv i \pmod N$, of which
Collatz ($N=2$) is the smallest nontrivial case and FRACTRAN is the fully general
one [Conway 1972; Conway 2013]. Conway proved that the reachability question for
this family — does the orbit of $n$ ever hit $1$? — is **undecidable**, and
Kurtz and Simon later established undecidability even for the *totally decidable*
generalized Collatz functions in a strong ($\Pi^0_2$-complete) sense
[Kurtz–Simon 2007]. The obstruction is precisely the absence of a monotone
height: if some $\log(a_i/b_i)$ are positive and some negative and the residue
selection is expressive enough to simulate a counter machine, no potential
function can certify termination — which is the dynamical restatement of §3–§5.
The still-open Collatz conjecture is the assertion that *one specific* such map,
against the odds of its undecidable family, always descends to $1$.

Two threads worth flagging. First, the increments $\log p$ being
$\mathbb{Q}$-linearly independent (logarithms of distinct primes) gives the height
walk an equidistribution/ergodic flavor that Matthews and Watts exploited for
generalized $3x+1$ maps via Markov chains and ergodic theory [Matthews]. Second,
the height is the genuine *arithmetic-geometry* object attached to a FRACTRAN
orbit — a point stressed again in §9 — even though, as we now argue, the geometry
underneath is a torus and not an elliptic curve.

---

## 8. A dictionary

The same object, read in six languages:

| view | state | fraction $a/b$ | step | halting |
|---|---|---|---|---|
| number theory | rational $n \in \mathbb{Q}_{>0}$ | element of $\mathbb{Q}_{>0}$ | left multiply | no divisor works |
| $p$-adic | valuations $(v_p(n))_p$ | $(v(a),v(b))$ | add, guarded by $v_p \ge v_p(b)$ | all guards fail |
| lattice / torus | point of $\mathbb{N}^{(\infty)} \subset \bigoplus_p\mathbb{Z}$ | move $\boldsymbol\delta$ + guard $\boldsymbol\beta$ | translate in orthant | deadlock |
| automata | Petri marking / counter values | transition (+ priority) | fire (+ zero test) | Minsky HALT |
| commutative algebra | monomial $\mathbf{x}^{\mathbf e}$ | binomial $\mathbf{x}^{\boldsymbol\alpha}-\mathbf{x}^{\boldsymbol\beta}$ | oriented rewrite | irreducible |
| dynamics | height $\log n$ | increment $\log(a/b)$ | piecewise-linear map | fixed sink |

The unifying statement: **prime factorization is the logarithm that turns
multiplicative number theory into additive lattice combinatorics; guards make it
a vector addition system; and a firing priority adds the zero test that makes it
Turing-complete.** Undecidability enters at, and only at, that last bit.

---

## 9. What is *not* here: the genus-0 / genus-1 divide

It is worth being exact about a tempting but false lead: **elliptic curves.**

FRACTRAN's ambient group is $\mathbb{Q}_{>0} \cong \bigoplus_p \mathbb{Z}$, the
character lattice of the multiplicative group / infinite torus
$\mathbb{G}_m^{\infty}$. This is the **genus-0** world: the group law is trivial
lattice addition, the "curve" is a torus, and its arithmetic invariants are
valuations and heights. Elliptic curves are **genus-1** abelian varieties whose
group law is the chord-and-tangent construction, carrying $j$-invariants,
Mordell–Weil ranks, torsion, and $L$-functions [Silverman 2009]. Nothing in the
FRACTRAN formalism produces any of that structure: there is no non-linear group
law, no place where a cubic relation or a Weierstrass form appears intrinsically.

Three honest caveats, so this is a real boundary and not hand-waving:

1. **Simulation is not structure.** FRACTRAN is Turing-complete, so it can *run* a
   program that adds points on an elliptic curve over $\mathbb{Q}$ or $\mathbb{F}_p$,
   counts points, or evaluates an $L$-function to precision. That is a statement
   about computability, not about FRACTRAN carrying elliptic geometry — exactly as
   a Turing machine "contains" no elliptic curve despite being able to compute
   with one.

2. **A shared category is not a functor.** A Mordell–Weil group $E(\mathbb{Q})$ is
   finitely generated abelian — the *same category* as the valuation lattice
   $\bigoplus_p \mathbb{Z}$ (also, locally, finitely generated). But there is no
   natural map, no functor, linking a FRACTRAN program to an elliptic curve; the
   shared abstraction (f.g. abelian groups) is where the resemblance ends.

3. **The genuine arithmetic-geometry object is the height (§7),** which belongs to
   Diophantine *geometry* in general and is not special to elliptic curves. If one
   insisted on an elliptic connection, the only non-arbitrary one runs the other
   way: elliptic curves *use* $p$-adic valuations and heights (Néron–Tate height,
   reduction mod $p$, the $p$-adic $L$-functions of Iwasawa theory), so FRACTRAN
   and elliptic curves are cousins that both drink from the well of $p$-adic
   valuations — not one contained in the other.

The correct one-line placement: **FRACTRAN is an arithmetic dynamical system on a
torus, analyzed by valuations and heights; elliptic curves are a different variety
that shares those analytic tools but none of FRACTRAN's mechanism.**

---

## 10. Loose threads and directions

- **Semilinearity and dimension.** Reachability sets of $2$-dimensional VAS are
  semilinear [Hopcroft–Pansiot 1979] but not in general; where a given compiled
  program's reachable set sits in this hierarchy is a concrete question our
  `decompile` output could feed.
- **Acceleration = geometric series in the lattice.** The loop accelerator in
  `accel.py` collapses a constant-effect loop by summing a fixed vector
  $k\boldsymbol\delta$ — literally computing a term of an arithmetic progression
  in $\bigoplus_p\mathbb{Z}$ in closed form. Affine (non-constant) loops would be
  matrix powers of a unipotent map, i.e. polynomial closed forms; general loops
  are where undecidability bites. This is the computational shadow of §5–§7.
- **Toric/VAS made explicit.** A module that emits, for a given program, its move
  matrix, guard matrix, and lattice $\mathcal L$ would turn "these fractions" into
  "this Petri net / this binomial ideal," making the §5–§6 correspondence runnable
  and the (un)decidability boundary tangible.
- **Height certificates.** For programs that *do* halt, a monotone height (a linear
  functional decreasing on every reachable transition) is a termination proof;
  finding one is a linear-programming problem over the moves — a partial,
  decidable island inside the undecidable sea of §7.
- **Computing constants.** Conway's PIGAME (digits of $\pi$ via Wallis) and the
  recent $\sqrt 2$ programs via Catalan's product and Newton–Raphson
  [Kaushik–Murphy–Weed 2024] show the height dynamics tracking a real limit — a
  bridge from the discrete lattice walk to classical analysis.

---

## References

- **[Agerwala 1974]** T. Agerwala. *A complete model for representing the coordination of asynchronous processes.* Hopkins Computer Research Report, Johns Hopkins Univ., 1974. (Inhibitor-arc Petri nets are Turing-complete; see also M. Hack, MIT, 1976.)
- **[Bernstein–Lagarias 1996]** D. J. Bernstein and J. C. Lagarias. *The $3x+1$ conjugacy map.* Canadian J. Math. 48(6):1154–1169, 1996. <https://cr.yp.to/papers/3x1conjmap-19960215-retypeset20220326.pdf>
- **[Bombieri–Gubler 2006]** E. Bombieri and W. Gubler. *Heights in Diophantine Geometry.* Cambridge Univ. Press, 2006.
- **[Conway 1972]** J. H. Conway. *Unpredictable iterations.* Proc. 1972 Number Theory Conf., Univ. of Colorado, Boulder, pp. 49–52, 1972.
- **[Conway 1987]** J. H. Conway. *FRACTRAN: A simple universal programming language for arithmetic.* In *Open Problems in Communication and Computation* (T. M. Cover, B. Gopinath, eds.), Springer, pp. 4–26, 1987. <https://www.cs.unc.edu/~stotts/COMP210-s23/madMath/Conway87.pdf>
- **[Conway 2013]** J. H. Conway. *On unsettleable arithmetical problems.* Amer. Math. Monthly 120(3):192–198, 2013. <https://raganwald.com/assets/fractran/Conway-On-Unsettleable-Arithmetical-Problems.pdf>
- **[Czerwiński–Orlikowski 2021]** W. Czerwiński and Ł. Orlikowski. *Reachability in vector addition systems is Ackermann-complete.* FOCS 2021. <https://arxiv.org/abs/2104.13866>
- **[Davis–Putnam–Robinson 1961]** M. Davis, H. Putnam, J. Robinson. *The decision problem for exponential Diophantine equations.* Ann. of Math. 74:425–436, 1961. (With Matiyasevich 1970, the DPRM theorem.)
- **[Diaconis–Eisenbud–Sturmfels 1998]** P. Diaconis, D. Eisenbud, B. Sturmfels. *Lattice walks and primary decomposition.* In *Mathematical Essays in Honor of Gian-Carlo Rota*, Birkhäuser, pp. 173–193, 1998.
- **[Diaconis–Sturmfels 1998]** P. Diaconis and B. Sturmfels. *Algebraic algorithms for sampling from conditional distributions.* Ann. Statist. 26(1):363–397, 1998.
- **[Eisenbud–Sturmfels 1996]** D. Eisenbud and B. Sturmfels. *Binomial ideals.* Duke Math. J. 84(1):1–45, 1996.
- **[Hopcroft–Pansiot 1979]** J. Hopcroft and J.-J. Pansiot. *On the reachability problem for 5-dimensional vector addition systems.* Theoret. Comput. Sci. 8(2):135–159, 1979.
- **[Kaushik–Murphy–Weed 2024]** K. Kaushik, T. Murphy, D. Weed. *Computing $\sqrt 2$ with FRACTRAN.* arXiv:2412.16185, 2024. <https://arxiv.org/abs/2412.16185>
- **[Kurtz–Simon 2007]** S. A. Kurtz and J. Simon. *The undecidability of the generalized Collatz problem.* TAMC 2007, LNCS 4484, Springer, pp. 542–553. <https://link.springer.com/chapter/10.1007/978-3-540-72504-6_49>
- **[Lagarias 1985]** J. C. Lagarias. *The $3x+1$ problem and its generalizations.* Amer. Math. Monthly 92(1):3–23, 1985.
- **[Larchey-Wendling–Forster 2019]** D. Larchey-Wendling and Y. Forster. *Hilbert's Tenth Problem in Coq.* FSCD 2019, LIPIcs 131. Extended version: arXiv:2003.04604. <https://arxiv.org/pdf/2003.04604>
- **[Leroux 2021]** J. Leroux. *The reachability problem for Petri nets is not primitive recursive.* FOCS 2021. <https://arxiv.org/abs/2104.12695>
- **[Leroux–Schmitz 2019]** J. Leroux and S. Schmitz. *Reachability in vector addition systems is primitive-recursive in fixed dimension.* LICS 2019.
- **[Lipton 1976]** R. J. Lipton. *The reachability problem requires exponential space.* Tech. Report 62, Yale Univ., 1976.
- **[Matiyasevich 1970]** Yu. Matiyasevich. *Enumerable sets are Diophantine.* Dokl. Akad. Nauk SSSR 191:279–282, 1970.
- **[Matthews]** K. R. Matthews. *Generalized $3x+1$ mappings: Markov chains and ergodic theory.* <http://www.numbertheory.org/PDFS/matthews-final-revised.pdf>
- **[Mayr 1981]** E. W. Mayr. *An algorithm for the general Petri net reachability problem.* STOC 1981, pp. 238–246; SIAM J. Comput. 13(3):441–460, 1984. (Independently Kosaraju, STOC 1982.)
- **[Minsky 1967]** M. Minsky. *Computation: Finite and Infinite Machines.* Prentice-Hall, 1967.
- **[Silverman 2009]** J. H. Silverman. *The Arithmetic of Elliptic Curves*, 2nd ed. GTM 106, Springer, 2009.
- **[Sturmfels 1996]** B. Sturmfels. *Gröbner Bases and Convex Polytopes.* AMS University Lecture Series 8, 1996.
