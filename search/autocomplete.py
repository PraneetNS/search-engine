class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        cur = self.root
        for ch in word:
            if ch not in cur.children:
                cur.children[ch] = TrieNode()
            cur = cur.children[ch]
        cur.is_end = True

    def _dfs(self, node, prefix):
        results = []
        if node.is_end:
            results.append(prefix)
        for ch, nxt in node.children.items():
            results.extend(self._dfs(nxt, prefix + ch))
        return results

    def autocomplete(self, prefix):
        cur = self.root
        for ch in prefix:
            if ch not in cur.children:
                return []
            cur = cur.children[ch]

        return self._dfs(cur, prefix)
