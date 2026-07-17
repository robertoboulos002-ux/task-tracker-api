from pathlib import Path


def test_modal_styles_include_dark_card_and_input_rules():
    html_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
    html = html_path.read_text(encoding="utf-8")

    assert 'class="modal-overlay"' in html
    assert 'class="modal-dialog"' in html
    assert '.modal-dialog' in html
    assert '.modal-field input,.modal-field textarea,.modal-field select' in html
    assert 'background-color:#0b1220' in html
    assert 'color:#e6eef8' in html
