// Native FRACTRAN core: a fast stepper for the hot loop.
//
// Two execution modes over the same program:
//   vector    - the exponent-vector view (each prime a register, int64 exponent);
//               a step is a guarded vector subtract-then-add. No big integers,
//               so this is the fast path for raw stepping.
//   canonical - the authentic semantics: a single GMP integer n, each step
//               testing divisibility and doing n = n/den*num. Unbounded and
//               faithful, the reference oracle; slower by design.
//
// Program is read from stdin, one fraction per line. Each side may be a factored
// expression like "61^10*23*19" (so fractions with factors beyond 2^64, as in a
// self-interpreter, never form a giant integer) or a plain number; sides are
// separated by '/' or whitespace. Blank lines and '#' comments are ignored. The
// start state is a factorization "p:e,p:e,..." given on the command line.
// Output is key=value lines.

#include <gmpxx.h>

#include <cctype>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>
#include <vector>

using std::map;
using std::pair;
using std::string;
using std::vector;
using i64 = long long;
using u64 = unsigned long long;

static vector<pair<u64, int>> factor(u64 n) {
    vector<pair<u64, int>> f;
    if (n <= 1) return f;
    for (u64 d = 2; d * d <= n && d <= (1ull << 22); d += (d == 2 ? 1 : 2)) {
        if (n % d == 0) {
            int e = 0;
            while (n % d == 0) { n /= d; ++e; }
            f.push_back({d, e});
        }
    }
    if (n > 1) f.push_back({n, 1});  // remaining residue is prime
    return f;
}

// Parse a factored expression ("61^10*23*19", "455", "1") into prime -> exponent.
static map<u64, int> parse_expr(const string& s) {
    map<u64, int> m;
    size_t i = 0, n = s.size();
    while (i < n) {
        while (i < n && (s[i] == '*' || isspace((unsigned char)s[i]))) ++i;
        u64 base = 0;
        bool any = false;
        while (i < n && isdigit((unsigned char)s[i])) { base = base * 10 + (s[i] - '0'); ++i; any = true; }
        if (!any) break;
        int exp = 1;
        if (i < n && s[i] == '^') { ++i; exp = 0; while (i < n && isdigit((unsigned char)s[i])) { exp = exp * 10 + (s[i] - '0'); ++i; } }
        for (auto& pe : factor(base)) m[pe.first] += pe.second * exp;
    }
    return m;
}

static mpz_class from_factors(const map<u64, int>& m) {
    mpz_class r = 1, t;
    for (auto& pe : m) {
        mpz_pow_ui(t.get_mpz_t(), mpz_class((unsigned long)pe.first).get_mpz_t(), (unsigned long)pe.second);
        r *= t;
    }
    return r;
}

struct Frac {
    map<u64, int> nf, df;  // numerator / denominator factorizations
};

int main(int argc, char** argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: fractran_core <vector|canonical> <start p:e,...>"
                        " [--max N] [--watch-pow2 LIMIT] [--read P[,P...]]\n");
        return 2;
    }
    string mode = argv[1];
    string startspec = argv[2];
    u64 maxsteps = 0, watch_limit = 0;
    bool watch = false;
    vector<u64> read_primes;
    for (int i = 3; i < argc; ++i) {
        string a = argv[i];
        if (a == "--max" && i + 1 < argc) maxsteps = strtoull(argv[++i], nullptr, 10);
        else if (a == "--watch-pow2" && i + 1 < argc) { watch = true; watch_limit = strtoull(argv[++i], nullptr, 10); }
        else if (a == "--read" && i + 1 < argc)
            for (char* tok = strtok(argv[++i], ","); tok; tok = strtok(nullptr, ",")) read_primes.push_back(strtoull(tok, nullptr, 10));
    }

    // -- read program from stdin --
    vector<Frac> prog;
    {
        char* line = nullptr;
        size_t cap = 0;
        while (getline(&line, &cap, stdin) != -1) {
            string s(line);
            size_t a = s.find_first_not_of(" \t\r\n");
            if (a == string::npos || s[a] == '#') continue;
            size_t b = s.find_last_not_of(" \t\r\n");
            s = s.substr(a, b - a + 1);
            string numexpr, denexpr;
            size_t slash = s.find('/');
            if (slash != string::npos) {
                numexpr = s.substr(0, slash);
                denexpr = s.substr(slash + 1);
            } else {
                size_t sp = s.find_first_of(" \t");
                if (sp == string::npos) continue;
                numexpr = s.substr(0, sp);
                denexpr = s.substr(s.find_first_not_of(" \t", sp));
            }
            prog.push_back({parse_expr(numexpr), parse_expr(denexpr)});
        }
        free(line);
    }

    // -- parse start factorization "p:e,p:e" --
    vector<pair<u64, i64>> start;
    {
        char* s = strdup(startspec.c_str());
        for (char* tok = strtok(s, ","); tok; tok = strtok(nullptr, ",")) {
            u64 pr; i64 ex;
            if (sscanf(tok, "%llu:%lld", &pr, &ex) == 2) start.push_back({pr, ex});
        }
        free(s);
    }

    auto t0 = std::chrono::steady_clock::now();
    u64 steps = 0;
    const char* status = "halt";
    vector<i64> emitted;
    map<u64, string> read_out;

    if (mode == "vector") {
        map<u64, int> idx;
        auto id = [&](u64 p) {
            auto it = idx.find(p);
            if (it != idx.end()) return it->second;
            int k = (int)idx.size();
            idx[p] = k;
            return k;
        };
        for (auto& f : prog) { for (auto& pe : f.nf) id(pe.first); for (auto& pe : f.df) id(pe.first); }
        for (auto& pe : start) id(pe.first);

        int P = (int)idx.size();
        vector<vector<pair<int, i64>>> need(prog.size()), delta(prog.size());
        for (size_t i = 0; i < prog.size(); ++i) {
            map<int, i64> d;
            for (auto& pe : prog[i].df) { need[i].push_back({idx[pe.first], pe.second}); d[idx[pe.first]] -= pe.second; }
            for (auto& pe : prog[i].nf) d[idx[pe.first]] += pe.second;
            for (auto& kv : d) if (kv.second) delta[i].push_back(kv);
        }

        vector<i64> state(P, 0);
        int nz = 0;
        for (auto& pe : start) if (pe.second) { state[idx[pe.first]] = pe.second; ++nz; }
        int p2 = idx.count(2) ? idx[2] : -1;

        while (true) {
            if (maxsteps && steps >= maxsteps) { status = "maxsteps"; break; }
            int fired = -1;
            for (size_t i = 0; i < prog.size(); ++i) {
                bool ok = true;
                for (auto& na : need[i]) if (state[na.first] < na.second) { ok = false; break; }
                if (ok) {
                    for (auto& dd : delta[i]) {
                        i64 old = state[dd.first], nv = old + dd.second;
                        if (old == 0 && nv != 0) ++nz;
                        else if (old != 0 && nv == 0) --nz;
                        state[dd.first] = nv;
                    }
                    fired = (int)i;
                    break;
                }
            }
            if (fired < 0) { status = "halt"; break; }
            ++steps;
            if (watch && p2 >= 0 && nz == 1 && state[p2] > 1) {
                emitted.push_back(state[p2]);
                if (watch_limit && emitted.size() >= watch_limit) { status = "watchdone"; break; }
            }
        }
        for (u64 pr : read_primes) read_out[pr] = idx.count(pr) ? std::to_string(state[idx[pr]]) : "0";

    } else if (mode == "canonical") {
        vector<pair<mpz_class, mpz_class>> fr;
        for (auto& f : prog) fr.push_back({from_factors(f.nf), from_factors(f.df)});
        mpz_class n = 1, t;
        for (auto& pe : start) { mpz_pow_ui(t.get_mpz_t(), mpz_class((unsigned long)pe.first).get_mpz_t(), (unsigned long)pe.second); n *= t; }
        while (true) {
            if (maxsteps && steps >= maxsteps) { status = "maxsteps"; break; }
            int fired = -1;
            for (size_t i = 0; i < fr.size(); ++i) {
                if (mpz_divisible_p(n.get_mpz_t(), fr[i].second.get_mpz_t())) {
                    n = n / fr[i].second * fr[i].first;
                    fired = (int)i;
                    break;
                }
            }
            if (fired < 0) { status = "halt"; break; }
            ++steps;
            if (watch && mpz_popcount(n.get_mpz_t()) == 1) {
                i64 e = (i64)mpz_scan1(n.get_mpz_t(), 0);
                if (e > 1) {
                    emitted.push_back(e);
                    if (watch_limit && emitted.size() >= watch_limit) { status = "watchdone"; break; }
                }
            }
        }
        for (u64 pr : read_primes) {
            mpz_class base((unsigned long)pr), r = n, cnt = 0;
            while (r != 0 && mpz_divisible_p(r.get_mpz_t(), base.get_mpz_t())) { r /= base; cnt += 1; }
            read_out[pr] = cnt.get_str();
        }
        read_out[0] = std::to_string((size_t)mpz_sizeinbase(n.get_mpz_t(), 10));
    } else {
        fprintf(stderr, "unknown mode: %s\n", mode.c_str());
        return 2;
    }

    double dt = std::chrono::duration<double>(std::chrono::steady_clock::now() - t0).count();
    printf("mode=%s\n", mode.c_str());
    printf("steps=%llu\n", steps);
    printf("status=%s\n", status);
    printf("elapsed=%.6f\n", dt);
    printf("rate=%.0f\n", dt > 0 ? steps / dt : 0.0);
    if (watch) {
        printf("emitted=");
        for (size_t i = 0; i < emitted.size(); ++i) printf("%s%lld", i ? " " : "", emitted[i]);
        printf("\n");
    }
    for (auto& kv : read_out) {
        if (kv.first == 0) printf("result_digits=%s\n", kv.second.c_str());
        else printf("read[%llu]=%s\n", kv.first, kv.second.c_str());
    }
    return 0;
}
