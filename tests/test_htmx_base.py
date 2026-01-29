from __future__ import annotations


def test_base_includes_htmx_and_view_transitions(client):
    r = client.get("/")
    assert r.status_code == 200

    assert 'src="https://cdnjs.cloudflare.com/ajax/libs/htmx/1.9.10/htmx.min.js"' in r.text
    assert 'src="https://cdnjs.cloudflare.com/ajax/libs/htmx/1.9.10/ext/sse.min.js"' in r.text
    assert 'src="https://cdnjs.cloudflare.com/ajax/libs/htmx/1.9.10/ext/preload.min.js"' in r.text
    assert '<meta name="htmx-config"' in r.text
    assert '"historyCacheSize": 0' in r.text
    assert '<meta name="view-transition" content="same-origin" />' in r.text
    assert 'hx-boost="true"' in r.text
    assert 'hx-indicator=".htmx-indicator"' in r.text
    assert '<div class="htmx-indicator"></div>' in r.text
