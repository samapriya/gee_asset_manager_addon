"""Google cloud projects tools.

SPDX-License-Identifier: Apache-2.0
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import subprocess
import sys
from typing import Any


# ANSI color codes - works natively across all major terminals and OSes
class Colors(str):
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def is_gcloud_installed() -> bool:
    """Check if gcloud is installed (optimized)."""
    try:
        # Use shell=True on Windows, False on Unix for best compatibility
        is_windows = sys.platform.startswith('win')
        result = subprocess.run(
            'gcloud --version' if is_windows else ['gcloud', '--version'],
            shell=is_windows,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_gcloud_authenticated() -> bool:
    """Check if gcloud is authenticated (optimized)."""
    try:
        is_windows = sys.platform.startswith('win')
        result = subprocess.run(
            'gcloud auth list --format=json' if is_windows else ['gcloud', 'auth', 'list', '--format=json'],
            shell=is_windows,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            accounts = json.loads(result.stdout)
            return any(acc.get('status') == 'ACTIVE' for acc in accounts)
        return False
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return False


def check_gcloud() -> bool:
    """Verify gcloud installation and authentication."""
    return is_gcloud_installed() and is_gcloud_authenticated()


def list_enabled_services(pname: str) -> list[dict[str, Any]] | None:
    """Lists enabled services for a given project.

    Args:
        pname: The project name.

    Returns:
        A list of enabled services, or None if an error occurs.
    """
    is_windows = sys.platform.startswith('win')
    command = f'gcloud services list --project={pname} --enabled --format=json' if is_windows else [
        'gcloud', 'services', 'list', f'--project={pname}', '--enabled', '--format=json'
    ]
    try:
        output = subprocess.run(
            command,
            shell=is_windows,
            capture_output=True,
            text=True,
            timeout=30
        )
        if output.returncode == 0:
            return json.loads(output.stdout)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def project_permissions(pname: str) -> tuple[str, str, bool] | None:
    """Checks if Earth Engine API is enabled for a project.

    Args:
        pname: The project name.

    Returns:
        Tuple of (project_name, project_number, has_ee) or None if error.
    """
    enabled_services = list_enabled_services(pname)

    if not enabled_services:
        return None

    enabled_api_list = [item['name'].split('services/')[-1]
                       for item in enabled_services]

    if "earthengine.googleapis.com" in enabled_api_list:
        project_id = enabled_services[0]["parent"]
        project_number = project_id.split('/')[-1]
        return (pname, project_number, True)

    return None


def display_projects_table(ee_projects: list[tuple[str, str, bool]]) -> None:
    """Display projects in a 2-column table format.

    Args:
        ee_projects: List of tuples (project_name, project_number, has_ee)
    """
    # Calculate column widths
    max_name_len = max(len(pname) for pname, _, _ in ee_projects)
    max_number_len = max(len(pnumber) for _, pnumber, _ in ee_projects)

    # Ensure minimum widths for headers
    name_width = max(max_name_len, 12)  # "Project Name" length
    number_width = max(max_number_len, 14)  # "Project Number" length

    # Create divider
    col_divider = "  │  "
    divider = f"{'─' * name_width}──┬──{'─' * number_width}{col_divider}{'─' * name_width}──┬──{'─' * number_width}"
    header_divider = f"{'═' * name_width}══╪══{'═' * number_width}{col_divider}{'═' * name_width}══╪══{'═' * number_width}"

    # Print header
    print(f"{Colors.BOLD}{'Project Name':<{name_width}}  │  {'Project Number':<{number_width}}{col_divider}{'Project Name':<{name_width}}  │  {'Project Number':<{number_width}}{Colors.RESET}")
    print(header_divider)

    # Print projects in 2 columns
    for i in range(0, len(ee_projects), 2):
        left_name, left_number, _ = ee_projects[i]

        if i + 1 < len(ee_projects):
            right_name, right_number, _ = ee_projects[i + 1]
            print(f"{Colors.CYAN}{left_name:<{name_width}}{Colors.RESET}  │  {left_number:<{number_width}}{col_divider}{Colors.CYAN}{right_name:<{name_width}}{Colors.RESET}  │  {right_number:<{number_width}}")
        else:
            # Odd number of projects - only left column
            print(f"{Colors.CYAN}{left_name:<{name_width}}{Colors.RESET}  │  {left_number:<{number_width}}")

    print(f"\n{Colors.BOLD}Total: {len(ee_projects)} project(s){Colors.RESET}")


def get_projects() -> None:
    """Retrieves project list and checks Earth Engine permissions (parallelized)."""
    if not check_gcloud():
        print(f"{Colors.RED}✗ gcloud is either not installed or not authenticated.{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ gcloud is installed and authenticated{Colors.RESET}\n")

    # Get all projects
    is_windows = sys.platform.startswith('win')
    command = 'gcloud projects list --format=json' if is_windows else ['gcloud', 'projects', 'list', '--format=json']
    try:
        print(f"{Colors.CYAN}Checking Earth Engine permissions for all projects...{Colors.RESET}\n")
        services_json = subprocess.check_output(
            command,
            shell=is_windows,
            text=True,
            timeout=30
        )
        project_json = json.loads(services_json)

        if not project_json:
            print(f"{Colors.YELLOW}No projects found.{Colors.RESET}")
            return

        print(f"{Colors.BLUE}Found {len(project_json)} project(s). Checking permissions...{Colors.RESET}\n")

        # Process projects in parallel for massive speed improvement
        ee_projects = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_project = {
                executor.submit(project_permissions, item['projectId']): item['projectId']
                for item in project_json
            }

            for future in as_completed(future_to_project):
                result = future.result()
                if result:
                    ee_projects.append(result)

        # Display results
        if ee_projects:
            print(f"{Colors.GREEN}{Colors.BOLD}Projects with Earth Engine enabled:{Colors.RESET}\n")
            display_projects_table(ee_projects)
        else:
            print(f"{Colors.YELLOW}No projects found with Earth Engine API enabled.{Colors.RESET}")

    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error: {e.output}{Colors.RESET}")
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}Error: Command timed out{Colors.RESET}")
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Failed to parse JSON output{Colors.RESET}")


if __name__ == '__main__':
    get_projects()
