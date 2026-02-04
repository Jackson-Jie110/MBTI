from __future__ import annotations


def test_base_includes_htmx_and_view_transitions(client):
    r = client.get("/")
    assert r.status_code == 200

    assert 'src="/static/js/htmx.min.js"' in r.text
    assert 'src="/static/js/htmx-ext-sse.js"' in r.text
    assert 'src="/static/js/htmx-ext-preload.js"' in r.text
    assert '<meta name="htmx-config"' in r.text
    assert '"historyCacheSize": 0' in r.text
    assert '<meta name="view-transition" content="same-origin" />' in r.text
    assert 'hx-boost="true"' in r.text
    assert 'hx-indicator=".htmx-indicator"' in r.text
    assert '<div class="htmx-indicator"></div>' in r.text

    assert "cdn.jsdelivr.net" not in r.text
