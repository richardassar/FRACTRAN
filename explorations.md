# FRACTRAN — Explorations: statistical mechanics, continuum limits, Riemann

*A companion to [theory.md](theory.md) collecting the deeper and more speculative
threads: the Bost–Connes bridge to $\zeta$, the two objects named after Weil, the
several continuum limits, and (later) spectral / Fourier structure. Rigor level is
flagged per item: **[established]**, **[heuristic]**, **[research direction]**.*

---

## 1. Two theorems of Weil, wearing the same surname

These are routinely conflated and are **not** the same object.

- **Weil height** (Diophantine geometry). $h(x)=\sum_v \log^+|x|_v$ summed over all
  places $v$; for a positive integer $h(n)=\log n=\sum_p v_p(n)\log p$
  [Bombieri–Gubler 2006]. This is the "size" a FRACTRAN step shifts by
  $\log(a/b)$ — the coordinate of `theory.md` §7.

- **Weil quadratic form / Weil positivity** (explicit formula; Connes–Consani).
  RH $\iff$ positivity of the Weil functional $W(f\star f^{*})\ge 0$. The
  finite **Weil matrices** are its Hermitian/Toeplitz truncations, whose
  positive-semidefiniteness is what one certifies. Connes–Consani give a
  conceptual proof of the positivity via the *semilocal trace formula* and
  *prolate spheroidal wave functions*, controlling the error with Toeplitz-matrix
  theory [Connes–Consani 2021, arXiv:2006.13771; Connes 2024].

**No identity between them.** The one genuine shared structure is the coordinate:
both live on the **log-line of prime powers** $\{m\log p\}$. The height places
mass $v_p(n)$ at position $\log p$; the Weil functional's prime side
$\sum_p\sum_m \frac{\log p}{p^{m/2}} f(m\log p)$ uses the same points as
*evaluation nodes*. Shared skeleton, different use — a configuration versus a
pairing. This is a shared coordinate, not a shared theorem.

## 2. The Bost–Connes bridge — the connection that *is* real  **[established]**

Where FRACTRAN and the Connes(-Consani) world actually meet is the **Bost–Connes
system** [Bost–Connes 1995; Connes 1999]. It lives on $\ell^2(\mathbb{N}^\times)$
with orthonormal basis $\{|n\rangle : n\ge 1\}$, Hamiltonian and partition
function

$$
H\,|n\rangle=(\log n)\,|n\rangle,\qquad
Z(\beta)=\operatorname{Tr} e^{-\beta H}=\sum_{n\ge 1} n^{-\beta}=\zeta(\beta),
$$

and the multiplicative semigroup $\mathbb{N}^{\times}\cong\bigoplus_p\mathbb{N}$
realized by isometries $\mu_n$ ("multiply by $n$"), with a phase transition at
$\beta=1$ (the pole of $\zeta$) and symmetry group
$\operatorname{Gal}(\mathbb{Q}^{\mathrm{ab}}/\mathbb{Q})=\hat{\mathbb{Z}}^{\times}$.

**FRACTRAN lives on exactly this space.** Its states are the same $|n\rangle$;
its moves are words in $\mu_p,\mu_p^{*}$ (multiply / divide by primes) acting on
the prime-exponent lattice; and the FRACTRAN **height $\log n=\sum_p v_p(n)\log p$
is precisely the Bost–Connes Hamiltonian eigenvalue.** Hence:

> **FRACTRAN = deterministic *computation* on $\ell^2(\mathbb{N}^\times)$;
> Bost–Connes = the equilibrium *statistical mechanics* of the same space.**

One follows a single trajectory chosen by guards + priority; the other is the
Gibbs ensemble whose partition function is $\zeta$. The Euler product
$\zeta=\prod_p(1-p^{-\beta})^{-1}$ factorizes over exactly the FRACTRAN *registers*
(the primes), because the $\mu_p$ are free generators. The Galois symmetry, KMS
states, and phase transition are ensemble features a single FRACTRAN run does not
see, but the underlying arithmetic monoid is identical.

**Where the bridge stops.** The Weil positivity / Weil matrices are a further
analytic layer — the spectral realization of the zeros — that FRACTRAN does not
touch. Correspondingly:

| object | connection to FRACTRAN |
|---|---|
| Weil **height** | **yes** — the Bost–Connes energy $\log n$; the log-prime-power line |
| Bost–Connes system | **yes** — same $\ell^2(\mathbb{N}^\times)$, same $\mu_p$, $\zeta$ = partition function |
| Weil **quadratic form / matrices / positivity** | **no direct link** — spectral/analytic; FRACTRAN is combinatorial |

**The RH tension.** FRACTRAN's own contact with RH is the *elementary–computational*
one: an "RHGAME" that halts iff a Robin/Lagarias counterexample exists
[Robin 1984; Lagarias 2002], i.e. RH $\iff$ that fraction list never halts — the
same idea as Yedidia–Aaronson's explicit RH Turing machine [Yedidia–Aaronson
2016] and the Davis–Matiyasevich–Robinson Diophantine route. That is a *different
attack* from Connes–Consani's spectral–geometric one, yet both pass through the
same monoid $\mathbb{N}^{\times}$. FRACTRAN makes the *isometries $\mu_n$* concrete
as computation; Connes–Consani study the *spectral geometry* of the same
operators. Bost–Connes is the hinge.

## 3. Continuum limits

Several natural continuum limits, in the spirit of the "geometry of program
synthesis" [Clift–Murfet–Wallbridge 2021].

**(A) Fluid limit → a continuous Petri net with priorities.  [established]**
Let exponents go real, $\mathbf e\in\mathbb{R}^P_{\ge 0}$ (the marking cone). Each
move is a translation by $\boldsymbol\delta_i$; the guards $e_p\ge\beta_p$ cut the
cone into polyhedra; the priority selects one move per region. The limit is a
**piecewise-constant vector field with switching manifolds at the guard
hyperplanes** — a hybrid ODE $\dot{\mathbf e}=\mathbf v(\mathbf e)$, i.e. a
continuous Petri net with priorities [David–Alla 1987/2010; *Stationary solutions
of continuous Petri nets with priorities*, arXiv:1612.07661]. The nondeterministic
"bundles of paths" become a foliation of the cone by this flow.

**(B) The height is the macroscopic coordinate; drift recovers Collatz.
[heuristic]**  Project $h=\langle\mathbf e,\boldsymbol\ell\rangle$,
$\boldsymbol\ell=(\log p)_p$. Then $\dot h=\langle\mathbf v(\mathbf e),\boldsymbol\ell\rangle$
is the height drift. For Collatz, the averaged move gives
$\mathbb E[\Delta h]=\tfrac12\log\tfrac12+\tfrac12\log\tfrac32=\tfrac12\log\tfrac34<0$
— the standard "Collatz is a biased random walk on $\log n$" heuristic, here
*derived* as the mean-field drift of the VAS. The conserved quantities (P-invariants,
e.g. $v_2+v_3$ for $\{2/3,3/2\}$, found by `reachability.analyze_region`) are the
**first integrals** of this flow.

**(C) The "all states" continuum — a transport PDE.  [buildable]**  The
nondeterministic reachability, taken to the continuum, evolves a density
$\rho(\mathbf e,t)$ on the cone by $\partial_t\rho+\nabla\!\cdot(\mathbf v\,\rho)=0$
— a linear conservation law with the drift field of (A). This is the continuum of
`analyze_region`.

**(D) Smooth relaxation and the *toric* geometry of synthesis.
[research direction]**  Soften the priority to a temperature-$\tau$ softmax over
applicable fractions (deterministic FRACTRAN as $\tau\to 0$) and relax the
fractions to real move-vectors $\boldsymbol\delta_i\in\mathbb{R}^P$. Because every
operation is **monomial/binomial** (`theory.md` §6), the resulting parameter space
and input→output map are real-algebraic and **toric**. Program synthesis is then
optimization on a toric variety; its loss landscape is singular, and by Watanabe's
singular learning theory the **real log canonical threshold** — the resolution of
those toric singularities — governs learnability, exactly as in
[Clift–Murfet–Wallbridge 2021; Watanabe 2009]. The FRACTRAN twist: the
singularities sit at explicit toric strata (two fractions colliding, a guard
threshold crossing a lattice wall, an exponent hitting $0$), so the geometry is a
*known* toric variety rather than a generic one. This is the tightest bond between
FRACTRAN's binomial-ideal structure and the geometry-of-synthesis programme.

**(E) The other completion is $p$-adic.  [established]**  Arithmetic FRACTRAN has
no smooth real continuum; Collatz-type systems complete at $2$, not $\infty$: the
$2$-adic dynamics of Bernstein–Lagarias (conjugacy to the $2$-adic shift). CA-type
systems (Rule 30) are chaotic (statistical/ergodic limit); additive rules
(Rule 90) have fractal continua (Sierpiński).

**Summary.** The *real-place* continuum is a fluid Petri net (an ODE/PDE on the
marking cone, A–C); the *program-space* continuum is a singular toric variety à la
Murfet (D); the *$p$-adic* continuum is the Bernstein–Lagarias dynamics (E) —
three completions of the same discrete lattice machine.

---

## References

- **[Bombieri–Gubler 2006]** E. Bombieri, W. Gubler. *Heights in Diophantine Geometry.* Cambridge, 2006.
- **[Bost–Connes 1995]** J.-B. Bost, A. Connes. *Hecke algebras, type III factors and phase transitions with spontaneous symmetry breaking in number theory.* Selecta Math. 1(3):411–457, 1995.
- **[Bernstein–Lagarias 1996]** D. J. Bernstein, J. C. Lagarias. *The $3x+1$ conjugacy map.* Canad. J. Math. 48(6):1154–1169, 1996.
- **[Clift–Murfet–Wallbridge 2021]** J. Clift, D. Murfet, J. Wallbridge. *Geometry of Program Synthesis.* arXiv:2103.16080, 2021.
- **[Connes 1999]** A. Connes. *Trace formula in noncommutative geometry and the zeros of the Riemann zeta function.* Selecta Math. 5:29–106, 1999.
- **[Connes–Consani 2021]** A. Connes, C. Consani. *Weil positivity and trace formula, the archimedean place.* Selecta Math. 27:77, 2021. arXiv:2006.13771.
- **[Connes 2024]** A. Connes. *Zeta zeros and prolate wave operators.* 2024. (See also Connes–Consani, *The Scaling Hamiltonian.*)
- **[David–Alla 2010]** R. David, H. Alla. *Discrete, Continuous, and Hybrid Petri Nets.* Springer, 2010 (continuous Petri nets, David–Alla 1987).
- **[Lagarias 2002]** J. C. Lagarias. *An elementary problem equivalent to the Riemann hypothesis.* Amer. Math. Monthly 109(6):534–543, 2002.
- **[Robin 1984]** G. Robin. *Grandes valeurs de la fonction somme des diviseurs et hypothèse de Riemann.* J. Math. Pures Appl. 63:187–213, 1984.
- **[Watanabe 2009]** S. Watanabe. *Algebraic Geometry and Statistical Learning Theory.* Cambridge, 2009.
- **[Weil 1952]** A. Weil. *Sur les « formules explicites » de la théorie des nombres.* Comm. Sém. Math. Univ. Lund, 252–265, 1952.
- **[Yedidia–Aaronson 2016]** A. Yedidia, S. Aaronson. *A relatively small Turing machine whose behavior is independent of set theory.* arXiv:1605.04343, 2016. (Also the explicit RH machine.)
- *Stationary solutions of discrete and continuous Petri nets with priorities.* arXiv:1612.07661.
