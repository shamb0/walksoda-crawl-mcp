"""Unit tests for the search_and_crawl query builder (OR-split fix, r074 s33).

The OR-split bug: search_and_crawl used `" OR ".join(query.split())` on every
multi-word query, which destroyed `site:`/`filetype:`/`after:`/`before:`
operators and quoted phrases. `site:asiainch.org plain weave` became
`site:asiainch.org OR plain OR weave` and returned non-whitelist domains
(verified live, r074 s32). `_build_enhanced_query` preserves operators and
quoted phrases while OR-joining only the loose plain words.
"""

import pytest

from crawl4ai_mcp.core.search_crawl import _build_enhanced_query


@pytest.mark.parametrize(
    "query, expected",
    [
        # Operator + multi-word plain -> AND the operator with the OR-group.
        ("site:asiainch.org plain weave", "site:asiainch.org (plain OR weave)"),
        # Operator + single plain word -> no redundant OR-group.
        ("site:asiainch.org Gharchola", "site:asiainch.org Gharchola"),
        # Plain multi-word -> OR-joined (unchanged behavior).
        ("plain weave", "plain OR weave"),
        # Quoted phrase is atomic; operators AND the OR-group of loose words.
        (
            'site:nic.in "kuzhi thari" pit loom',
            'site:nic.in (pit OR loom OR "kuzhi thari")',
        ),
        # filetype: operator preserved.
        ("filetype:pdf GI registration", "filetype:pdf (GI OR registration)"),
        # after: operator preserved.
        ("after:2020 Banarasi brocade", "after:2020 (Banarasi OR brocade)"),
        # Single plain word -> unchanged.
        ("plain", "plain"),
        # Operator only -> unchanged (nothing to OR-join).
        ("site:asiainch.org", "site:asiainch.org"),
        # Operator is case-insensitive.
        ("SITE:asiainch.org plain weave", "SITE:asiainch.org (plain OR weave)"),
        # Multiple operators, single plain word -> both operators AND the word.
        (
            "after:2020 site:asiainch.org brocade",
            "after:2020 site:asiainch.org brocade",
        ),
    ],
)
def test_build_enhanced_query_preserves_operators(query, expected):
    assert _build_enhanced_query(query) == expected


def test_build_enhanced_query_preserves_site_restriction():
    """The site: domain must survive as a hard constraint, never an OR-term."""
    out = _build_enhanced_query("site:asiainch.org plain weave")
    # The domain is a constraint, not OR-joined with the loose words.
    assert "site:asiainch.org" in out
    assert out.startswith("site:asiainch.org")
    # The loose words ARE OR-joined (inside the parenthesized group).
    assert "plain OR weave" in out
