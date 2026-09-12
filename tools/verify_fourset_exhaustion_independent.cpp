// Independent exhaustive verifier for the port-free support-4 difference-cut master.
//
// This checker intentionally uses a different decomposition from the producing
// exact_fourset_master.py search.  It does not use a pivot cut, root ordering,
// canonical root ownership, monotone-resume state, or any search checkpoint.
//
// Every four-set has a unique increasing order a<b<c<d.  We enumerate its
// first three vertices a<b<c.  For each cut not already hit by one of the three
// internal triple edges ab, ac, bc, the fourth vertex d must be adjacent in
// that cut to at least one of a,b,c.  Therefore the legal d values are exactly
// the intersection, over all still-unhit cuts, of
//
//     N_t(a) union N_t(b) union N_t(c),
//
// restricted to d>c.  Empty intersection eliminates that triple.  A surviving
// d is a genuine four-set hitting every cut.  Exhausting all increasing triples
// proves that no four-set hits all supplied cuts.
//
// The input mask library is reconstructed independently from validated A/B
// models by reconstruct_fourset_cuts_independent.py.

#include <algorithm>
#include <atomic>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <mutex>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace {

constexpr char MAGIC[8] = {'H','N','4','M','S','K','0','1'};

struct Library {
    int m = 0;
    int atom_count = 0;
    int k = 0;
    int edge_bytes = 0;
    int vwords = 0;
    std::vector<uint32_t> cut_sizes;
    std::vector<int> cut_order;
    // Flattened [cut][vertex][vertex-word] adjacency bitsets.
    std::vector<uint64_t> adj;
};

uint32_t read_u32(std::ifstream& f) {
    unsigned char b[4];
    f.read(reinterpret_cast<char*>(b), 4);
    if (!f) throw std::runtime_error("truncated uint32");
    return uint32_t(b[0]) | (uint32_t(b[1]) << 8) |
           (uint32_t(b[2]) << 16) | (uint32_t(b[3]) << 24);
}

size_t adj_base(const Library& lib, int t, int u) {
    return (static_cast<size_t>(t) * lib.m + u) * lib.vwords;
}

bool has_edge(const Library& lib, int t, int u, int v) {
    const size_t base = adj_base(lib, t, u);
    return (lib.adj[base + (v >> 6)] >> (v & 63)) & 1ULL;
}

Library read_library(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) throw std::runtime_error("cannot open input: " + path);
    char magic[8];
    f.read(magic, 8);
    if (!f || std::memcmp(magic, MAGIC, 8) != 0)
        throw std::runtime_error("bad HN4MSK01 magic");

    Library lib;
    lib.m = static_cast<int>(read_u32(f));
    lib.atom_count = static_cast<int>(read_u32(f));
    lib.k = static_cast<int>(read_u32(f));
    lib.edge_bytes = static_cast<int>(read_u32(f));
    if (lib.m < 4 || lib.k < 1) throw std::runtime_error("invalid dimensions");
    const int expected_atoms = lib.m * (lib.m - 1) / 2;
    if (lib.atom_count != expected_atoms)
        throw std::runtime_error("atom_count does not equal m choose 2");
    const int expected_bytes = (lib.atom_count + 7) / 8;
    if (lib.edge_bytes != expected_bytes)
        throw std::runtime_error("edge_bytes mismatch");

    std::vector<int> atom_u(lib.atom_count), atom_v(lib.atom_count);
    int aidx = 0;
    for (int u = 0; u < lib.m; ++u) {
        for (int v = u + 1; v < lib.m; ++v) {
            atom_u[aidx] = u;
            atom_v[aidx] = v;
            ++aidx;
        }
    }

    lib.vwords = (lib.m + 63) / 64;
    const size_t adj_words = static_cast<size_t>(lib.k) * lib.m * lib.vwords;
    lib.adj.assign(adj_words, 0ULL);
    lib.cut_sizes.resize(lib.k);

    std::vector<unsigned char> raw(lib.edge_bytes);
    for (int t = 0; t < lib.k; ++t) {
        const uint32_t declared = read_u32(f);
        lib.cut_sizes[t] = declared;
        f.read(reinterpret_cast<char*>(raw.data()), raw.size());
        if (!f) throw std::runtime_error("truncated cut mask");

        uint32_t counted = 0;
        for (int i = 0; i < lib.atom_count; ++i) {
            if ((raw[i >> 3] >> (i & 7)) & 1U) {
                ++counted;
                const int u = atom_u[i], v = atom_v[i];
                lib.adj[adj_base(lib, t, u) + (v >> 6)] |= 1ULL << (v & 63);
                lib.adj[adj_base(lib, t, v) + (u >> 6)] |= 1ULL << (u & 63);
            }
        }
        if (counted != declared)
            throw std::runtime_error("declared cut size does not match mask popcount");
    }
    char extra;
    if (f.read(&extra, 1)) throw std::runtime_error("trailing bytes after cut library");

    lib.cut_order.resize(lib.k);
    std::iota(lib.cut_order.begin(), lib.cut_order.end(), 0);
    std::stable_sort(lib.cut_order.begin(), lib.cut_order.end(), [&](int x, int y) {
        return lib.cut_sizes[x] < lib.cut_sizes[y];
    });
    return lib;
}

struct SearchResult {
    bool found = false;
    int a = -1, b = -1, c = -1, d = -1;
    uint64_t triples_checked = 0;
};

uint64_t expected_triples(int m) {
    // a<b<c<d requires a,b,c chosen from vertices 0..m-2.
    if (m < 4) return 0;
    const uint64_t n = static_cast<uint64_t>(m - 1);
    return n * (n - 1) * (n - 2) / 6;
}

SearchResult exhaustive_triple_extension(const Library& lib, int requested_threads,
                                         bool quiet = false) {
    std::atomic<bool> found(false);
    std::atomic<uint64_t> total_checked(0);
    std::atomic<int> completed_a(0);
    std::mutex answer_mutex;
    SearchResult answer;

#ifdef _OPENMP
    if (requested_threads > 0) omp_set_num_threads(requested_threads);
#pragma omp parallel for schedule(dynamic, 1)
#endif
    for (int a = 0; a <= lib.m - 4; ++a) {
        uint64_t local_checked = 0;
        std::vector<uint64_t> cand(lib.vwords);
        for (int b = a + 1; b <= lib.m - 3 && !found.load(std::memory_order_relaxed); ++b) {
            for (int c = b + 1; c <= lib.m - 2 && !found.load(std::memory_order_relaxed); ++c) {
                ++local_checked;
                std::fill(cand.begin(), cand.end(), 0ULL);
                // All d>c are initially legal.
                const int first = c + 1;
                const int fw = first >> 6;
                if (fw < lib.vwords) {
                    cand[fw] = ~0ULL << (first & 63);
                    for (int w = fw + 1; w < lib.vwords; ++w) cand[w] = ~0ULL;
                    if ((lib.m & 63) != 0)
                        cand.back() &= (1ULL << (lib.m & 63)) - 1ULL;
                }

                bool alive = true;
                for (int oi = 0; oi < lib.k; ++oi) {
                    const int t = lib.cut_order[oi];
                    if (has_edge(lib, t, a, b) || has_edge(lib, t, a, c) ||
                        has_edge(lib, t, b, c)) {
                        continue;
                    }
                    const size_t ba = adj_base(lib, t, a);
                    const size_t bb = adj_base(lib, t, b);
                    const size_t bc = adj_base(lib, t, c);
                    bool nonempty = false;
                    for (int w = fw; w < lib.vwords; ++w) {
                        cand[w] &= lib.adj[ba + w] | lib.adj[bb + w] | lib.adj[bc + w];
                        nonempty |= cand[w] != 0ULL;
                    }
                    if (!nonempty) {
                        alive = false;
                        break;
                    }
                }

                if (alive) {
                    int d = -1;
                    for (int w = fw; w < lib.vwords && d < 0; ++w) {
                        if (cand[w]) {
                            d = (w << 6) + __builtin_ctzll(cand[w]);
                        }
                    }
                    if (d > c && d < lib.m) {
                        bool expected = false;
                        if (found.compare_exchange_strong(expected, true)) {
                            std::lock_guard<std::mutex> lock(answer_mutex);
                            answer.found = true;
                            answer.a = a; answer.b = b; answer.c = c; answer.d = d;
                        }
                    }
                }
            }
        }
        total_checked.fetch_add(local_checked, std::memory_order_relaxed);
        const int done = completed_a.fetch_add(1, std::memory_order_relaxed) + 1;
        if (!quiet && (done <= 5 || done % 20 == 0 || done == lib.m - 3)) {
            std::cerr << "completed outer-a blocks " << done << "/" << (lib.m - 3)
                      << "; triples_checked~" << total_checked.load() << "\n";
        }
    }
    answer.triples_checked = total_checked.load();
    return answer;
}

Library toy_library(int m, const std::vector<std::vector<std::pair<int,int>>>& cuts) {
    Library lib;
    lib.m = m;
    lib.atom_count = m * (m - 1) / 2;
    lib.edge_bytes = (lib.atom_count + 7) / 8;
    lib.k = static_cast<int>(cuts.size());
    lib.vwords = (m + 63) / 64;
    lib.adj.assign(static_cast<size_t>(lib.k) * m * lib.vwords, 0ULL);
    lib.cut_sizes.resize(lib.k);
    for (int t = 0; t < lib.k; ++t) {
        lib.cut_sizes[t] = static_cast<uint32_t>(cuts[t].size());
        for (auto [u,v] : cuts[t]) {
            if (u > v) std::swap(u,v);
            lib.adj[adj_base(lib,t,u)+(v>>6)] |= 1ULL << (v&63);
            lib.adj[adj_base(lib,t,v)+(u>>6)] |= 1ULL << (u&63);
        }
    }
    lib.cut_order.resize(lib.k);
    std::iota(lib.cut_order.begin(), lib.cut_order.end(), 0);
    std::stable_sort(lib.cut_order.begin(), lib.cut_order.end(), [&](int x,int y){
        return lib.cut_sizes[x] < lib.cut_sizes[y];
    });
    return lib;
}

bool brute_exists(const Library& lib) {
    for (int a=0; a<lib.m; ++a) for (int b=a+1; b<lib.m; ++b)
    for (int c=b+1; c<lib.m; ++c) for (int d=c+1; d<lib.m; ++d) {
        bool ok = true;
        for (int t=0; t<lib.k && ok; ++t) {
            ok = has_edge(lib,t,a,b) || has_edge(lib,t,a,c) || has_edge(lib,t,a,d) ||
                 has_edge(lib,t,b,c) || has_edge(lib,t,b,d) || has_edge(lib,t,c,d);
        }
        if (ok) return true;
    }
    return false;
}

void self_test() {
    std::mt19937_64 rng(0x484E363256455249ULL);
    int trials = 0;
    for (int m=5; m<=10; ++m) {
        std::vector<std::pair<int,int>> atoms;
        for (int u=0; u<m; ++u) for (int v=u+1; v<m; ++v) atoms.push_back({u,v});
        for (int rep=0; rep<100; ++rep) {
            const int k = 1 + (rng() % 15);
            std::vector<std::vector<std::pair<int,int>>> cuts(k);
            for (int t=0; t<k; ++t) {
                const int threshold = 5 + (rng() % 71); // 5..75 percent
                for (auto e : atoms) if (int(rng()%100) < threshold) cuts[t].push_back(e);
                if (cuts[t].empty()) cuts[t].push_back(atoms[rng()%atoms.size()]);
            }
            Library lib = toy_library(m,cuts);
            const bool brute = brute_exists(lib);
            const SearchResult got = exhaustive_triple_extension(lib,1,true);
            if (got.found != brute) {
                throw std::runtime_error("self-test mismatch at m=" + std::to_string(m));
            }
            if (!got.found && got.triples_checked != expected_triples(m)) {
                throw std::runtime_error("self-test did not exhaust all increasing triples");
            }
            ++trials;
        }
    }
    std::cout << "independent verifier self-test OK: " << trials
              << " randomized instances matched brute force\n";
}

void write_result(const std::string& path, const Library& lib, const SearchResult& r) {
    std::ofstream o(path);
    if (!o) throw std::runtime_error("cannot write result: " + path);
    if (r.found) {
        o << "{\n"
          << "  \"status\": \"FOURSET-CANDIDATE-FOUND\",\n"
          << "  \"method\": \"independent increasing-triple to fourth-vertex intersection\",\n"
          << "  \"vertex_count\": " << lib.m << ",\n"
          << "  \"unique_cut_count\": " << lib.k << ",\n"
          << "  \"support_positions\": [" << r.a << ", " << r.b << ", "
          << r.c << ", " << r.d << "],\n"
          << "  \"triples_checked_before_candidate\": " << r.triples_checked << "\n"
          << "}\n";
    } else {
        const uint64_t expected = expected_triples(lib.m);
        if (r.triples_checked != expected)
            throw std::runtime_error("search returned no candidate without full triple count");
        o << "{\n"
          << "  \"status\": \"INDEPENDENT-EXHAUSTION-VERIFIED\",\n"
          << "  \"method\": \"independent increasing-triple to fourth-vertex intersection\",\n"
          << "  \"vertex_count\": " << lib.m << ",\n"
          << "  \"unique_cut_count\": " << lib.k << ",\n"
          << "  \"triples_checked\": " << r.triples_checked << ",\n"
          << "  \"expected_triples\": " << expected << ",\n"
          << "  \"decomposition_note\": \"Every four-set has unique a<b<c<d; for each a<b<c, legal d>c are intersected over all cuts not already hit inside the triple.\",\n"
          << "  \"independent_of_producing_root_order\": true\n"
          << "}\n";
    }
}

} // namespace

int main(int argc, char** argv) {
    try {
        bool do_self_test = false;
        std::string input, result;
        int threads = 0;
        for (int i=1; i<argc; ++i) {
            std::string a = argv[i];
            if (a == "--self-test") do_self_test = true;
            else if (a == "--input" && i+1<argc) input = argv[++i];
            else if (a == "--result" && i+1<argc) result = argv[++i];
            else if (a == "--threads" && i+1<argc) threads = std::stoi(argv[++i]);
            else throw std::runtime_error("unknown or incomplete argument: " + a);
        }
        if (do_self_test) {
            self_test();
            return 0;
        }
        if (input.empty() || result.empty())
            throw std::runtime_error("usage: --input cuts.bin --result result.json [--threads N]");

        Library lib = read_library(input);
        std::cerr << "loaded independent cut library: vertices=" << lib.m
                  << " cuts=" << lib.k << " adjacency_words=" << lib.adj.size() << "\n";
#ifdef _OPENMP
        std::cerr << "OpenMP enabled; requested_threads=" << threads << "\n";
#else
        std::cerr << "OpenMP not enabled; serial verifier\n";
#endif
        SearchResult r = exhaustive_triple_extension(lib, threads, false);
        write_result(result, lib, r);
        if (r.found) {
            std::cout << "candidate found at positions " << r.a << "," << r.b << ","
                      << r.c << "," << r.d << "\n";
            return 2;
        }
        std::cout << "INDEPENDENT EXHAUSTION VERIFIED: checked " << r.triples_checked
                  << " increasing triples\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 1;
    }
}
