"""Unit tests for multi_site_search (site:-scoped fan-out, r074 s34)."""

import pytest

from crawl4ai_mcp.core import search as search_core


@pytest.mark.asyncio
async def test_multi_site_search_builds_site_queries_per_domain(monkeypatch):
    """Each domain becomes exactly one site:<domain> query, deduped in order."""
    captured = {}

    class _Fake:
        async def batch_search(self, queries, num_results_per_query, max_concurrent,
                               language, region, search_genre):
            captured['queries'] = queries
            captured['region'] = region
            # One hit per query for the first two, empty for the third.
            return [
                {'success': True, 'total_results': 3, 'results': [{'url': 'a'}]},
                {'success': True, 'total_results': 2, 'results': [{'url': 'b'}]},
                {'success': False, 'error': 'throttled'},
            ]

    monkeypatch.setattr(search_core, 'google_search_processor', _Fake())

    result = await search_core.multi_site_search({
        'domains': ['asiainch.org', 'dsource.in', 'asiainch.org', 'globalinch.org'],
        'query': 'plain weave',
        'region': 'in-en',
    })

    # 4 domains -> deduped to 3 (asiainch.org appears twice).
    assert captured['queries'] == [
        'site:asiainch.org plain weave',
        'site:dsource.in plain weave',
        'site:globalinch.org plain weave',
    ]
    assert captured['region'] == 'in-en'
    assert result['success'] is True
    assert result['total_domains'] == 3
    assert result['domains_with_hits'] == 2
    assert [e['domain'] for e in result['per_domain']] == [
        'asiainch.org', 'dsource.in', 'globalinch.org',
    ]
    assert result['per_domain'][2]['success'] is False


@pytest.mark.asyncio
async def test_multi_site_search_rejects_empty_inputs(monkeypatch):
    calls = []

    class _Fake:
        async def batch_search(self, **kwargs):
            calls.append(kwargs)
            return []

    monkeypatch.setattr(search_core, 'google_search_processor', _Fake())

    # Missing domains.
    r = await search_core.multi_site_search({'query': 'plain weave'})
    assert r['success'] is False
    assert 'domains' in r['error']

    # Missing query.
    r = await search_core.multi_site_search({'domains': ['asiainch.org']})
    assert r['success'] is False
    assert 'query' in r['error']

    # No batch_search call fired for invalid inputs.
    assert calls == []
