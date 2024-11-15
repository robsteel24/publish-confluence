import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from src.update_confluence import (
    get_page_content,
    main,
    update_confluence_page,
    update_version_in_cell,
)

DUMMY_ENV_VARS = {
    "CONFLUENCE_BASE_URL": "https://example.atlassian.com",
    "CONFLUENCE_PAGE_ID": "123456",
    "ATLASSIAN_USERNAME": "dummy_user",
    "ATLASSIAN_API_TOKEN": "dummy_token",
}

HTML_CONTENT = """
<html><body>
<table>
    <tr><th rowspan="2">Environment</th><th colspan="3">Application Components</th></tr>
    <tr><td>cpt1</td><td>cpt2</td><td>cpt3</td></tr>
    <tr><th>DEV</th><td><p>1.0.0</p></td><td><p></p></td><td><p></p></td></tr>
</table>
</body></html>
"""


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.update_confluence.confluence")
def test_get_page_content(mock_confluence, caplog):
    mock_confluence.get_page_by_id.return_value = {
        "body": {"storage": {"value": HTML_CONTENT}},
        "title": "Mock Page Title",
    }

    with caplog.at_level(logging.INFO):
        page_content = get_page_content("123456")
        assert "Fetching content for page ID" in caplog.text
        assert "<table>" in str(page_content)

    mock_confluence.get_page_by_id.assert_called_once_with(
        "123456", expand="body.storage,title"
    )


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_update_version_in_cell(caplog):
    soup = BeautifulSoup(HTML_CONTENT, "html.parser")
    environment = "DEV"
    component = "cpt1"
    new_version = "2.3.4"

    with caplog.at_level(logging.INFO):
        updated_soup = update_version_in_cell(soup, environment, component, new_version)
        cell_text = updated_soup.find_all("tr")[2].find_all("td")[0].p.get_text()

        assert "Updating version for component" in caplog.text
        assert "2.3.4" in cell_text


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_update_version_in_cell_component_not_found():
    soup = BeautifulSoup(HTML_CONTENT, "html.parser")
    environment = "DEV"
    component = "cpt_missing"
    new_version = "2.3.4"

    with pytest.raises(ValueError, match="Component 'cpt_missing' not found"):
        update_version_in_cell(soup, environment, component, new_version)


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_update_version_in_cell_environment_not_found():
    soup = BeautifulSoup(HTML_CONTENT, "html.parser")
    environment = "PROD"
    component = "cpt1"
    new_version = "2.3.4"

    with pytest.raises(ValueError, match="Environment 'PROD' not found"):
        update_version_in_cell(soup, environment, component, new_version)


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.update_confluence.confluence")
def test_update_confluence_page(mock_confluence, caplog):
    mock_confluence.update_page = MagicMock()
    soup = BeautifulSoup(HTML_CONTENT, "html.parser")

    with (
        patch(
            "src.update_confluence.get_page_content",
            return_value=(soup, "Mock Page Title"),
        ),
        caplog.at_level(logging.INFO),
    ):
        update_confluence_page("DEV", "cpt1", "2.3.4")

        mock_confluence.update_page.assert_called_once_with(
            page_id="123456",
            title="Mock Page Title",
            body=str(soup),
            minor_edit=True,
        )
        assert (
            "Page updated successfully for component 'cpt1' in environment 'DEV' "
            "for version number 2.3.4" in caplog.text
        )


@patch(
    "sys.argv",
    [
        "update_confluence.py",
        "--environment",
        "DEV",
        "--component",
        "cpt1",
        "--version",
        "2.3.4",
    ],
)
@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.update_confluence.update_confluence_page")
def test_main_cli(mock_update_confluence_page):
    main()
    mock_update_confluence_page.assert_called_once_with("DEV", "cpt1", "2.3.4")
