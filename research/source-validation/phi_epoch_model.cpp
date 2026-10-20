// PC-only model of the graph bookkeeping described in WebKit commit b21a503.
// This is original test code, not a WebKit build or a firmware test.
#include <cassert>
#include <cstddef>
#include <vector>

struct Node {
    bool escaped = false;
    std::vector<std::size_t> incoming;
};

static void old_escape(std::vector<Node>& nodes, std::size_t id) {
    nodes.at(id).escaped = true;
}

static void transitive_escape(std::vector<Node>& nodes, std::size_t id) {
    std::vector<std::size_t> work{id};
    while (!work.empty()) {
        auto current = work.back();
        work.pop_back();
        auto& node = nodes.at(current);
        if (node.escaped) continue;
        node.escaped = true;
        for (auto predecessor : node.incoming) work.push_back(predecessor);
    }
}

int main() {
    // Two incoming values feed a phi; one incoming value has a predecessor.
    std::vector<Node> old(4), fixed(4);
    old[3].incoming = {1, 2};
    old[1].incoming = {0};
    fixed = old;
    old_escape(old, 3);
    transitive_escape(fixed, 3);
    assert(old[3].escaped && !old[1].escaped && !old[0].escaped);
    assert(fixed[3].escaped && fixed[2].escaped && fixed[1].escaped && fixed[0].escaped);
    // A cycle should terminate and preserve the same invariant.
    fixed[0].incoming = {3};
    for (auto& n : fixed) n.escaped = false;
    transitive_escape(fixed, 3);
    for (const auto& n : fixed) assert(n.escaped);
}
