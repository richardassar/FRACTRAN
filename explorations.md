# FRACTRAN — Explorations: statistical mechanics, continuum limits, Riemann

*A companion to [theory.md](theory.md) collecting the deeper and more speculative
threads: the two objects named after Weil, the several continuum limits,
spectral / Fourier structure, and RHGAME (Robin's inequality as a fraction list).
Rigor level is flagged per item: **[established]**, **[heuristic]**,
**[research direction]**.*

---

## 1. The Weil height

**Weil height** (Diophantine geometry). $h(x)=\sum_v \log^+|x|_v$ summed over all
places $v$; for a positive integer $h(n)=\log n=\sum_p v_p(n)\log p$
[Bombieri–Gubler 2006]. This is the "size" a FRACTRAN step shifts by
$\log(a/b)$ — the coordinate of `theory.md` §7, living on the **log-line of
prime powers** $\{m\log p\}$: the height places mass $v_p(n)$ at position
$\log p$.

## 2. Continuum limits

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

## 4. Spectral structure — graph Fourier as the Pontryagin transform

The nondeterministic reachability graph of §2 (fire any applicable fraction) is
exactly a **multiway system** in Wolfram's sense; doing graph signal processing on
it is graph Fourier analysis of a FRACTRAN machine [Shuman et al. 2013; Ortega et
al. 2018; Sandryhaila–Moura 2013]. The point of this section is that on FRACTRAN
this collapses onto classical harmonic analysis.

**The Cayley graph, and GFT = Pontryagin transform.  [established]**  States form
the abelian group $G=\bigoplus_p\mathbb{Z}$ and the fractions are a generating set
of moves $\{\boldsymbol\delta_i\}$, so the natural graph is the Cayley graph of
$G$: adjacency $A=\sum_i T_{\boldsymbol\delta_i}$ (translations). The $T_{\boldsymbol\delta_i}$
commute and are simultaneously diagonalized by the characters
$\chi_{\boldsymbol\theta}(\mathbf e)=e^{2\pi i\langle\boldsymbol\theta,\mathbf e\rangle}$,
$\boldsymbol\theta\in\hat G=\prod_p\mathbb{T}=\mathbb{T}^{\infty}$. The eigenvalue is the
**Fourier symbol / dispersion**

$$
\lambda(\boldsymbol\theta)=\sum_i e^{2\pi i\langle\boldsymbol\theta,\boldsymbol\delta_i\rangle},
$$

a Laurent polynomial in $z_p=e^{2\pi i\theta_p}$. So **the graph Fourier transform
of a FRACTRAN system is the Pontryagin transform on $\bigoplus_p\mathbb{Z}$** — the
GFT eigenvectors are the group characters, the graph spectrum is the phonon
dispersion of a crystal whose bonds are the fractions. The finite *multiway* graph
is the guarded, boundary-truncated version of this clean bulk.

This threads through the earlier sections:

1. **Bulk vs boundary.  [established]**  On the full group (the unguarded VAS
   bulk) the dynamics is translation-invariant and *exactly* Fourier-diagonal
   (plane waves, dispersion $\lambda$). All computational content — the guards
   $\mathbf e\ge\boldsymbol\beta$, the priority — is the failure of translation
   invariance at the **orthant walls**: hard-wall boundary conditions on an
   otherwise free lattice particle. Undecidability is a *boundary* phenomenon;
   GFT is the transform that trivializes the bulk so the walls stand out (whence
   Wiener–Hopf / random walks in a cone).

2. **Dual torus and Kronecker flow.  [established]**  $\hat G=\mathbb{T}^{\infty}$
   is the character group of $\mathbb{Q}_{>0}$. Under Fourier $v_p\leftrightarrow\tfrac{1}{2\pi i}\partial_{\theta_p}$,
   the height Hamiltonian becomes
   $\widehat H=\tfrac{1}{2\pi i}\sum_p(\log p)\,\partial_{\theta_p}$, the generator of a
   **Kronecker flow on $\mathbb{T}^\infty$** with velocity $(\log p)_p$. Since the
   $\log p$ are $\mathbb{Q}$-independent the flow is minimal and uniquely ergodic
   (equidistribution, Weyl), and $e^{it\widehat H}$ is the time evolution
   $n\mapsto n^{it}$. Graph Fourier lands the height dynamics on the
   arithmetic torus.

3. **Low frequencies = the continuum limit.  [established]**  Near $\boldsymbol\theta=0$,
   $\lambda(\boldsymbol\theta)=|S|+2\pi i\langle\boldsymbol\theta,\sum_i\boldsymbol\delta_i\rangle
   -2\pi^2\sum_i\langle\boldsymbol\theta,\boldsymbol\delta_i\rangle^2+\cdots$: the first-order
   term is the **drift** $\sum_i\boldsymbol\delta_i$ (§2B, the Collatz $\tfrac12\log\tfrac34$),
   the second is the **diffusion** — the advection–diffusion coefficients of the
   transport PDE (§2C). Low GFT modes are the fluid limit; high modes the machine.

4. **The dispersion is the toric Laurent polynomial.  [established]**  $\lambda(\boldsymbol\theta)=\sum_i z^{\boldsymbol\delta_i}$
   lives in the coordinate ring of the torus; its **Newton polytope is the convex
   hull of the moves** and its amoeba is the toric geometry of `theory.md` §6.
   Spectral (GFT), polyhedral (VAS), and toric (binomial ideals) are one object.

5. **Collatz's diagonalization is $2$-adic (Walsh).  [established]**  The
   Bernstein–Lagarias conjugacy to the $2$-adic shift *is* a Fourier
   diagonalization in the $2$-adic character (Walsh) basis — "the GFT of Collatz"
   is Walsh–Fourier on the $2$-adic completion (§2E).

6. **The multiway graph's GFT (numerical).  [buildable]**  For a finite
   reachability box, the symmetric graph Laplacian's **zero modes = connected
   components = conserved-quantity level sets** (the P-invariants, e.g. $v_2+v_3$
   for $\{2/3,3/2\}$ are the null space); the directed adjacency's **unit-circle
   eigenvalues = cyclic components** (a length-$\ell$ cycle contributes $\ell$-th
   roots of unity); and the **spectral gap = mixing rate**. The SCC decomposition
   of `reachability.analyze_region` is the coarse shadow of this spectrum.

**One line.**  Because FRACTRAN's states are an abelian group and its moves are
translations, its graph Fourier transform is harmonic analysis on
$\bigoplus_p\mathbb{Z}$: the bulk diagonalizes to a phonon dispersion (a toric
Laurent polynomial), the dual is the arithmetic torus where the height runs as an
ergodic Kronecker flow, the low frequencies give the fluid continuum limit, and
the computational hardness is pushed entirely into the orthant boundary
conditions. Computed by `fractran/spectral.py`.

---

## 4. RHGAME — Robin's inequality as a fraction list

**The construction.**  Robin's theorem [Robin 1984]: RH $\iff
\sigma(n)<e^{\gamma}\,n\,\ln\ln n$ for all $n>5040$, where $\sigma$ is the
sum-of-divisors function (the inequality fails at exactly $27$ integers, all
$\le 5040$). So a machine that enumerates $n>5040$, computes $\sigma(n)$, and
**halts iff the inequality is ever violated — i.e. halts iff RH is false**. This
is the FRACTRAN sibling of the explicit RH Turing machines [Yedidia–Aaronson 2016]
and the Davis–Matiyasevich–Robinson Diophantine route (the same reduction chain
$\textsf{MM}\preceq\textsf{FRACTRAN}\preceq\textsf{DIO}$). `fractran/rhgame.py`
gives the Python reference search plus the **compiled FRACTRAN kernel**
`make_sigma` (71 fractions) that computes $\sigma(n)$ as an actual fraction list;
`rhgame_demo.py` verifies it and confirms no Robin violation up to $10^6$ (record
ratio $\approx 1.7558$ at $n=10080$, below $e^{\gamma}\approx 1.7811$).

**The transcendental subtlety.**  The bound $e^{\gamma}\,n\,\ln\ln n$ is
irrational, so a *rigorous* RHGAME does not compute it exactly; it brackets it
with rational **upper bounds of increasing precision** (rational approximations
of $e^{\gamma}$ and the logarithms), and halts only when $\sigma(n)$ exceeds a
certified upper bound — sound (halt $\Rightarrow$ genuine violation) and complete
(a real violation has a definite margin and is eventually detected). $\sigma(n)$
is the clean integer heart and is what we compile; the precision management is
computable but large and is specified rather than compiled here.

**Siblings and lineage.**  RHGAME sits in a well-populated computational lineage.
The reduction chain $\textsf{MM}\preceq\textsf{FRACTRAN}\preceq\textsf{DIO}$ also
yields the Diophantine form (Davis–Matiyasevich–Robinson) and the explicit RH
Turing machines [Yedidia–Aaronson 2016]; RHGAME is the FRACTRAN member of that
family — RH written as "this fraction list never halts." Computation has a real
track record around RH: large-scale verification along the critical line, and — the
cautionary counterpoint — the refutation of over-strong conjectures once believed,
such as the Mertens conjecture $|M(n)|<\sqrt n$, disproved by Odlyzko–te Riele.
RHGAME's value is as a concrete artifact: RH as a specific, runnable object on the
shared monoid $\mathbb{N}^{\times}$.

---

## References

- **[Bombieri–Gubler 2006]** E. Bombieri, W. Gubler. *Heights in Diophantine Geometry.* Cambridge, 2006.
- **[Bernstein–Lagarias 1996]** D. J. Bernstein, J. C. Lagarias. *The $3x+1$ conjugacy map.* Canad. J. Math. 48(6):1154–1169, 1996.
- **[Clift–Murfet–Wallbridge 2021]** J. Clift, D. Murfet, J. Wallbridge. *Geometry of Program Synthesis.* arXiv:2103.16080, 2021.
- **[David–Alla 2010]** R. David, H. Alla. *Discrete, Continuous, and Hybrid Petri Nets.* Springer, 2010 (continuous Petri nets, David–Alla 1987).
- **[Lagarias 2002]** J. C. Lagarias. *An elementary problem equivalent to the Riemann hypothesis.* Amer. Math. Monthly 109(6):534–543, 2002.
- **[Odlyzko–te Riele 1985]** A. M. Odlyzko, H. J. J. te Riele. *Disproof of the Mertens conjecture.* J. Reine Angew. Math. 357:138–160, 1985.
- **[Ortega et al. 2018]** A. Ortega, P. Frossard, J. Kovačević, J. M. F. Moura, P. Vandergheynst. *Graph signal processing: overview, challenges, and applications.* Proc. IEEE 106(5):808–828, 2018.
- **[Robin 1984]** G. Robin. *Grandes valeurs de la fonction somme des diviseurs et hypothèse de Riemann.* J. Math. Pures Appl. 63:187–213, 1984.
- **[Sandryhaila–Moura 2013]** A. Sandryhaila, J. M. F. Moura. *Discrete signal processing on graphs.* IEEE Trans. Signal Process. 61(7):1644–1656, 2013.
- **[Shuman et al. 2013]** D. I. Shuman, S. K. Narang, P. Frossard, A. Ortega, P. Vandergheynst. *The emerging field of signal processing on graphs.* IEEE Signal Process. Mag. 30(3):83–98, 2013.
- **[Watanabe 2009]** S. Watanabe. *Algebraic Geometry and Statistical Learning Theory.* Cambridge, 2009.
- **[Weil 1952]** A. Weil. *Sur les « formules explicites » de la théorie des nombres.* Comm. Sém. Math. Univ. Lund, 252–265, 1952.
- **[Wolfram 2020]** S. Wolfram. *A Class of Models with the Potential to Represent Fundamental Physics.* Complex Systems 29(2):107–536, 2020. (Multiway systems.)
- **[Yedidia–Aaronson 2016]** A. Yedidia, S. Aaronson. *A relatively small Turing machine whose behavior is independent of set theory.* arXiv:1605.04343, 2016. (Also the explicit RH machine.)
- *Stationary solutions of discrete and continuous Petri nets with priorities.* arXiv:1612.07661.
