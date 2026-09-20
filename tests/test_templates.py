"""Contract tests for the first-party HTML, CSS and JavaScript UI."""

from html.parser import HTMLParser
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_JS_DIR = PROJECT_ROOT / "app" / "static" / "js"


class MarkupInspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.inline_styles = []
        self.scripts = []
        self.labels_for = set()
        self.tags_by_id = {}
        self.attributes_by_id = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.add(element_id)
            self.tags_by_id[element_id] = tag
            self.attributes_by_id[element_id] = attributes
        if "style" in attributes:
            self.inline_styles.append(attributes["style"])
        if tag == "script":
            self.scripts.append(attributes)
        if tag == "label" and attributes.get("for"):
            self.labels_for.add(attributes["for"])


def inspect(response):
    inspector = MarkupInspector()
    inspector.feed(response.get_data(as_text=True))
    return inspector


def test_home_template_exposes_accessible_ui_contract(client):
    response = client.get("/")
    inspector = inspect(response)

    assert response.status_code == 200
    assert {
        "mainContent",
        "landingSlider",
        "assistantSlide",
        "contactSlide",
        "prevSlideButton",
        "nextSlideButton",
        "slideStatus",
        "chatForm",
        "chatMessages",
        "messageInput",
        "askButton",
        "answerText",
        "leadForm",
        "nameInput",
        "phoneInput",
        "leadMessageInput",
        "saveLeadButton",
        "statusText",
    } <= inspector.ids
    assert {"messageInput", "nameInput", "phoneInput", "leadMessageInput"} <= (
        inspector.labels_for
    )
    assert inspector.tags_by_id["messageInput"] == "input"
    assert inspector.attributes_by_id["messageInput"]["type"] == "text"


def test_dashboard_template_exposes_safe_rendering_contract(client):
    response = client.get("/dashboard")
    inspector = inspect(response)

    assert response.status_code == 200
    assert {
        "mainContent",
        "refreshButton",
        "dashboardStatus",
        "leadCount",
        "leadList",
        "leadRowTemplate",
    } <= inspector.ids


@pytest.mark.parametrize("path", ["/", "/dashboard"])
def test_templates_use_external_module_scripts_and_no_inline_styles(client, path):
    response = client.get(path)
    inspector = inspect(response)

    assert inspector.inline_styles == []
    assert inspector.scripts
    assert all(script.get("src") for script in inspector.scripts)
    assert all(script.get("type") == "module" for script in inspector.scripts)


@pytest.mark.parametrize(
    "path, content_type",
    [
        ("/static/css/main.css", "text/css"),
        ("/static/js/api-client.js", "javascript"),
        ("/static/js/home.js", "javascript"),
        ("/static/js/dashboard.js", "javascript"),
        ("/static/images/favicon.svg", "svg"),
    ],
)
def test_static_assets_are_served(client, path, content_type):
    response = client.get(path)

    assert response.status_code == 200
    assert content_type in response.content_type
    assert response.data


def test_http_calls_are_isolated_in_api_client():
    source_by_name = {
        path.name: path.read_text(encoding="utf-8")
        for path in STATIC_JS_DIR.glob("*.js")
    }

    assert "fetch(" in source_by_name["api-client.js"]
    assert "fetch(" not in source_by_name["home.js"]
    assert "fetch(" not in source_by_name["dashboard.js"]


def test_frontend_never_renders_user_data_with_inner_html():
    sources = [path.read_text(encoding="utf-8") for path in STATIC_JS_DIR.glob("*.js")]

    assert all("innerHTML" not in source for source in sources)
    assert "textContent" in (STATIC_JS_DIR / "dashboard.js").read_text(encoding="utf-8")
