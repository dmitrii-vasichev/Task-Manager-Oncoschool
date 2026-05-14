from app.services.content_factory import glossary as glossary_module


def test_get_terms_returns_list_of_dicts():
    terms = glossary_module.get_terms()
    assert isinstance(terms, list)
    assert len(terms) >= 8
    for term in terms:
        assert set(term.keys()) >= {"term", "definition"}


def test_known_terms_present():
    keys = {t["term"] for t in glossary_module.get_terms()}
    expected = {
        "Bundle",
        "Publication",
        "Sibling publication",
        "Window",
        "Confidence",
        "Segment role: exclusion",
        "Funnel template",
        "Retro",
    }
    missing = expected - keys
    assert not missing, f"missing terms: {missing}"


def test_terms_are_sorted_by_display_order():
    terms = glossary_module.get_terms()
    orders = [t["display_order"] for t in terms]
    assert orders == sorted(orders)
