from app.services.ai.disclaimer import MEDICAL_DISCLAIMER, ensure_disclaimer


def test_appends_when_absent():
    out = ensure_disclaimer("Your glucose looks elevated.")
    assert "not a substitute for professional medical" in out.lower()
    assert out.startswith("Your glucose looks elevated.")


def test_does_not_double_append():
    once = ensure_disclaimer("Some advice.")
    twice = ensure_disclaimer(once)
    assert once == twice
    assert twice.lower().count("not a substitute for professional medical") == 1


def test_handles_none_and_empty():
    assert MEDICAL_DISCLAIMER in ensure_disclaimer(None)
    assert MEDICAL_DISCLAIMER in ensure_disclaimer("")
