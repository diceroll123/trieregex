from collections import defaultdict
from re import escape
from typing import Any, DefaultDict, Dict, List, Optional

from .memoizer import memoizer


class TrieRegEx:
    """Builds a regular expression from a trie based on user-provided words

    Includes methods for:
    (1) adding and removing words from a trie, 
    (2) checking whether a word exists in the trie, 
    (3) inspecting initial and final characters in the trie, and
    (4) creating a boundary-less regular expression pattern from the trie.
    """
    __slots__ = ['_trie', '_initials', '_finals']

    def __init__(self, *words: str) -> None:
        self._trie: Dict[str, Any] = {}
        self._initials: DefaultDict[str, int] = defaultdict(int)
        self._finals: DefaultDict[str, int] = defaultdict(int)
        self.add(*words)
    
    @memoizer()
    def add(self, *words: str) -> None:
        """Add a word or words to the trie"""
        self.regex.clear_cache()
        
        for word in words:
            if word != '' and not self.has(word):
                self._initials[word[0]] += 1
                self._finals[word[-1]] += 1
                trie = self._trie
                for char in word:
                    if char not in trie:
                        trie[char] = {}
                    trie = trie[char]
                trie['**'] = {}

    def remove(self, *words: str) -> None:
        """Remove a word or words from the trie"""
        self.add.clear_cache()
        self.regex.clear_cache()

        for word in words:
            remove_word = False
            for i in range(len(word), 0, -1):
                is_end = i == len(word)
                if is_end and self.has(word[:i]):
                    remove_word = True
                    self._initials[word[0]] -= 1
                    self._finals[word[-1]] -= 1
                if remove_word:
                    node = self._trie
                    for j in range(i-1):
                        node = node[word[j]]
                    penult_node = node[word[i-1]]
                    if is_end:
                        if '**' in penult_node:
                            if len(penult_node) == 1:
                                del node[word[i-1]]
                            else:
                                del penult_node['**']
                    else:
                        if len(penult_node) == 0:
                            del node[word[i-1]]
                else:
                    break

    def has(self, word: str) -> bool:
        """Check if a word exists in the trie"""
        trie = self._trie
        for char in word:
            if char in trie:
                trie = trie[char]
            else:
                return False
        return '**' in trie

    def initials(self) -> List[str]:
        """Returns a list of unique initial characters in the trie"""
        result = [key for key in self._initials if self._initials[key] > 0]
        return sorted(result)

    def finals(self) -> List[str]:
        """Returns a list of unique final characters in the trie"""
        result = [key for key in self._finals if self._finals[key] > 0]
        return sorted(result)

    @memoizer()
    def regex(self, trie: Optional[Dict[str, Any]] = None, reset: bool = True) -> str:
        """Returns a boundary-less escaped regex string based on the trie"""
        if trie is None:
            trie = {}

        if reset:
            trie = self._trie

        if len(trie) == 0:
            return ''

        elif len(trie) == 1:
            key = list(trie.keys())[0]
            if key == '**':
                return ''
            return f'{escape(key)}{self.regex(trie[key], False)}'

        else:
            sequences = [f'{escape(key)}{self.regex(trie[key], False)}'
                         for key in trie if key != '**']
            sequences.sort(key=lambda x: (-len(x), x))

            if len(sequences) == 1:
                result = sequences[0]
                if len(result) > 1:
                    result = f'(?:{result})'
            elif len(sequences) == len("".join(sequences)):
                result = f'[{"".join(sequences)}]'
            else:
                result = f'(?:{"|".join(sequences)})'

            if '**' in trie:
                return f'{result}?'
            return result
