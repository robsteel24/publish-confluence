import argparse
import logging
import os

from atlassian import Confluence
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = os.getenv("CONFLUENCE_BASE_URL", "https://example.atlassian.com")
PAGE_ID = os.getenv("CONFLUENCE_PAGE_ID", "123456")
USERNAME = os.getenv("ATLASSIAN_USERNAME")
API_TOKEN = os.getenv("ATLASSIAN_API_TOKEN")

confluence = Confluence(url=BASE_URL, username=USERNAME, password=API_TOKEN)


def get_page_content(page_id: str) -> BeautifulSoup:
    """
    Fetches the HTML content and title of a Confluence page by its page ID.

    Parameters:
        page_id (str): The ID of the Confluence page to retrieve.

    Returns:
        tuple: A tuple containing:
            - BeautifulSoup: Parsed HTML content of the Confluence page.
            - str: The title of the Confluence page.

    Raises:
        requests.exceptions.RequestException: If there is an issue with the network
        or API request.
    """
    logger.info(f"Fetching content for page ID: {page_id}")
    page_details = confluence.get_page_by_id(page_id, expand="body.storage,title")
    page_content = page_details["body"]["storage"]["value"]
    page_title = page_details.get("title", "Default Page Title")
    logger.debug(f"Page content fetched: {page_content[:100]}...")
    return BeautifulSoup(page_content, "html.parser"), page_title


def update_version_in_cell(
    soup: BeautifulSoup, environment: str, component: str, new_version: str
) -> BeautifulSoup:
    """
    Updates the version number of a specified component within a Confluence table
    based on the environment.

    Parameters:
        soup (BeautifulSoup): Parsed HTML content of the Confluence page.
        environment (str): The name of the environment (e.g., "DEV", "PROD") to
        locate in the table.
        component (str): The component name to locate in the table.
        new_version (str): The new version number to set for the component in the
        specified environment.

    Returns:
        BeautifulSoup: The updated BeautifulSoup object with the new version number
        in the appropriate cell.

    Raises:
        ValueError: If the specified component or environment is not found in the
        table.
    """
    logger.info(
        f"Updating version for component '{component}' in environment "
        f"'{environment}' to '{new_version}'"
    )
    table = soup.find("table")

    header_rows = table.find_all("tr")[:2]
    component_index = None
    for i, cell in enumerate(header_rows[1].find_all(["th", "td"])):
        if cell.get_text(strip=True).lower() == component.lower():
            component_index = i + 1
            logger.debug(f"Component '{component}' found at index {component_index}")
            break

    if component_index is None:
        logger.error(f"Component '{component}' not found in the table.")
        raise ValueError(f"Component '{component}' not found")

    for row in table.find_all("tr")[2:]:
        env_cell = row.find(["th", "td"])
        if env_cell and env_cell.get_text(strip=True).upper() == environment.upper():
            target_cell = row.find_all(["td"])[component_index - 1]
            target_cell.p.string = new_version
            logger.info(
                f"Updated cell for '{component}' in '{environment}' with "
                f"version '{new_version}'"
            )
            return soup

    logger.error(f"Environment '{environment}' not found in the table.")
    raise ValueError(f"Environment '{environment}' not found")


def update_confluence_page(environment: str, component: str, new_version: str) -> None:
    """
    Updates a Confluence page with a new version number for a specific component in
    a specific environment.

    Parameters:
        environment (str): The environment in which to update the component version
        (e.g., "DEV").
        component (str): The name of the component to update.
        new_version (str): The new version number to be applied.

    Returns:
        None

    Side Effects:
        Calls Confluence API to update the specified page with the new content.

    Raises:
        requests.exceptions.RequestException: If the update request to Confluence
        fails.
    """
    soup, current_title = get_page_content(PAGE_ID)
    updated_soup = update_version_in_cell(soup, environment, component, new_version)
    updated_content = str(updated_soup)
    confluence.update_page(
        page_id=PAGE_ID,
        title=current_title,
        body=updated_content,
        minor_edit=True,
    )
    logger.info(
        f"Page updated successfully for component '{component}' in environment "
        f"'{environment}' for version number {new_version}"
    )


def main() -> None:
    """
    Command-line interface for updating a Confluence table with version information.

    Parses command-line arguments to specify the environment, component, and version
    number, then calls `update_confluence_page` to update the Confluence page with the
    new version data.

    Parameters:
        None (reads from CLI arguments)

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description=(
            "Update Confluence table with version info for a specific component and "
            "environment."
        )
    )
    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        help="The environment name (e.g., 'dev')",
    )
    parser.add_argument(
        "--component", type=str, required=True, help="The component name (e.g., 'app')"
    )
    parser.add_argument(
        "--version", type=str, required=True, help="The version number (e.g., '1.1.1')"
    )
    args = parser.parse_args()

    logger.info(f"Environment: {args.environment}")
    logger.info(f"Component: {args.component}")
    logger.info(f"Version: {args.version}")

    update_confluence_page(args.environment, args.component, args.version)


if __name__ == "__main__":
    main()
