"""Google Earth Engine Projects Dashboard.

SPDX-License-Identifier: Apache-2.0
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any
import webbrowser

import ee
from google.auth.transport.requests import AuthorizedSession


# ANSI color codes - works natively across all major terminals and OSes
class Colors:
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


def get_registration_status(project_id: str, session: AuthorizedSession) -> str:
    """Get Earth Engine registration status for a project.

    Args:
        project_id: The project ID.
        session: Authorized session for EE API.

    Returns:
        Registration status string or 'UNKNOWN' if error.
    """
    try:
        url = f"https://earthengine.googleapis.com/v1/projects/{project_id}/config"
        response = session.get(url=url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return data.get('registrationState', 'UNKNOWN')
        else:
            return 'UNKNOWN'
    except Exception as e:
        print(f"{Colors.YELLOW}Warning: Could not get registration status for {project_id}: {e}{Colors.RESET}")
        return 'UNKNOWN'


def project_permissions_with_registration(pname: str, session: AuthorizedSession) -> dict[str, Any] | None:
    """Checks if Earth Engine API is enabled and gets registration status.

    Args:
        pname: The project name.
        session: Authorized session for EE API.

    Returns:
        Dict with project info or None if error.
    """
    enabled_services = list_enabled_services(pname)

    if enabled_services is None or not enabled_services:
        return None

    enabled_api_list = [item['name'].split('services/')[-1]
                       for item in enabled_services]

    if "earthengine.googleapis.com" in enabled_api_list:
        project_id = enabled_services[0]["parent"]
        project_number = project_id.split('/')[-1]

        # Get registration status
        registration_status = get_registration_status(pname, session)

        return {
            "project_name": pname,
            "project_id": project_number,
            "registration_status": registration_status
        }

    return None


def display_projects_table(ee_projects: list[dict[str, Any]]) -> None:
    """Display projects in a formatted table.

    Args:
        ee_projects: List of dicts with project info
    """
    if not ee_projects:
        return

    # Calculate column widths
    max_name_len = max(len(p["project_name"]) for p in ee_projects)
    max_id_len = max(len(p["project_id"]) for p in ee_projects)
    max_status_len = max(len(p["registration_status"]) for p in ee_projects)

    # Ensure minimum widths for headers
    name_width = max(max_name_len, 12)
    id_width = max(max_id_len, 10)
    status_width = max(max_status_len, 19)

    # Print header
    print(f"\n{Colors.BOLD}{'Project Name':<{name_width}}  │  {'Project ID':<{id_width}}  │  {'Registration Status':<{status_width}}{Colors.RESET}")
    print(f"{'─' * name_width}──┼──{'─' * id_width}──┼──{'─' * status_width}")

    # Print projects
    for proj in ee_projects:
        status_color = Colors.GREEN if 'REGISTERED' in proj['registration_status'] else Colors.YELLOW
        print(f"{Colors.CYAN}{proj['project_name']:<{name_width}}{Colors.RESET}  │  {proj['project_id']:<{id_width}}  │  {status_color}{proj['registration_status']:<{status_width}}{Colors.RESET}")

    print(f"\n{Colors.BOLD}Total: {len(ee_projects)} project(s){Colors.RESET}")


def is_headless() -> bool:
    """Check if the system is running in a headless environment."""
    try:
        # Check for display on Unix-like systems
        if sys.platform != 'win32':
            return os.environ.get('DISPLAY') is None
        # Windows always has a display in interactive sessions
        return False
    except:
        return True


def create_html_dashboard(projects_data, output_path="ee_projects_dashboard.html"):
    script_dir = Path(__file__).parent.resolve()
    output_file = script_dir / output_path
    html_content = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Earth Engine Projects Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        body {
            font-family: 'Montserrat', sans-serif;
        }

        @keyframes fade-in {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border: 1px solid transparent;
        }

        /* --- Light Mode Status Badge Colors --- */
        .status-commercial {
            background: #a7f3d0; /* Light Green */
            color: #064e3b; /* Dark Green */
            border-color: #052e16;
        }

        .status-non-commercial {
            background: #bfdbfe; /* Light Blue */
            color: #1e3a8a; /* Dark Blue */
            border-color: #1e1b4b;
        }

        .status-not-registered {
            background: #fde68a; /* Light Yellow */
            color: #78350f; /* Dark Orange */
            border-color: #451a03;
        }

        .status-unknown {
            background: #d1d5db; /* Light Gray */
            color: #374151; /* Dark Gray */
            border-color: #1f2937;
        }
        /* --- End Light Mode Colors --- */

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 600;
            padding: 0.5rem 1rem;
            text-decoration: none;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }

        .btn-primary {
            background-color: #4285F4;
            color: #ffffff;
            border-color: #4285F4;
        }

        .btn-primary:hover {
            background-color: #1a73e8;
            border-color: #1a73e8;
        }

        .btn-secondary {
            background-color: #4285F4;
            color: #ffffff;
            border-color: #4285F4;
        }

        .btn-secondary:hover {
            background-color: #1a73e8;
            border-color: #1a73e8;
        }

        .copy-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.25rem;
            border-radius: 0.375rem;
            color: #6b7280; /* Darker gray for light mode */
            transition: all 0.2s ease;
            flex-shrink: 0;
        }

        .copy-btn:hover {
            background-color: #e5e7eb; /* Light gray hover */
            color: #1f2937; /* Dark text on hover */
        }

        .stat-card {
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-4px);
        }

        .stat-card.active {
            /* Updated shadow to use blue for light mode */
            box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.4);
            transform: scale(1.02);
        }

        .project-card {
            transition: all 0.3s ease;
        }

        .project-card.hidden {
            display: none;
        }
    </style>
</head>

<body class="p-4 sm:p-8 text-gray-800 bg-gray-100">

    <div class="max-w-7xl mx-auto relative z-10">
        <div class="border border-gray-200 bg-white shadow-lg rounded-2xl p-6 sm:p-8 mb-8 flex items-center justify-between">
            <div>
                <h1 class="text-3xl lg:text-4xl font-bold text-gray-900 mb-2">Earth Engine Projects</h1>
                <p class="text-gray-600">Overview of your Google Earth Engine enabled projects</p>
            </div>

            <div class="flex items-center space-x-4">
                <img src="https://storage.googleapis.com/gweb-uniblog-publish-prod/original_images/image_3_for_carousel.gif"
                    alt="Earth Engine Logo" class="w-20 h-20 rounded-full object-cover border-2 border-gray-300"
                    onerror="this.src='https://placehold.co/80x80/9ca3af/FFFFFF?text=EE';this.onerror=null;">
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8" id="stats-container"></div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" id="projects-container"></div>

        <footer class="text-center text-gray-600 text-sm py-8 mt-12">
            <p class="mb-2">
                Created by GEE Asset Manager Addon. For details, visit
                <a href="https://geeadd.geetools.xyz" target="_blank"
                   rel="noopener noreferrer"
                   class="text-blue-600 hover:text-blue-800 underline">
                   https://geeadd.geetools.xyz
                </a>.
            </p>
            <p>
                Created by
                <a href="https://www.linkedin.com/in/samapriya/" target="_blank"
                   rel="noopener noreferrer"
                   class="text-blue-600 hover:text-blue-800 underline">
                   Samapriya Roy
                </a>.
            </p>
        </footer>
    </div>

    <script>
        const projectsData = """ + json.dumps(projects_data) + """;
        let currentFilter = null;

        function copyToClipboard(text, buttonEl) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = 0;
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                const originalContent = buttonEl.innerHTML;
                buttonEl.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4 text-green-500">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                    </svg>
                `;
                setTimeout(() => {
                    buttonEl.innerHTML = originalContent;
                }, 1500);
            } catch (err) {
                console.error('Failed to copy text: ', err);
            }
            document.body.removeChild(textarea);
        }

        function filterProjects(filterType) {
            const projectCards = document.querySelectorAll('.project-card');
            const statCards = document.querySelectorAll('.stat-card');
            statCards.forEach(card => card.classList.remove('active'));

            if (currentFilter === filterType) {
                currentFilter = null;
                projectCards.forEach(card => card.classList.remove('hidden'));
            } else {
                currentFilter = filterType;
                const activeCard = document.querySelector(`[data-filter="${filterType}"]`);
                if (activeCard) activeCard.classList.add('active');

                projectCards.forEach(card => {
                    const status = card.dataset.status;
                    if (filterType === 'all') card.classList.remove('hidden');
                    else if (filterType === 'commercial' && status === 'REGISTERED_COMMERCIALLY') card.classList.remove('hidden');
                    else if (filterType === 'non-commercial' && status === 'REGISTERED_NOT_COMMERCIALLY') card.classList.remove('hidden');
                    else if (filterType === 'not-registered' && status === 'NOT_REGISTERED') card.classList.remove('hidden');
                    else card.classList.add('hidden');
                });
            }
        }

        const stats = {
            total: projectsData.length,
            commercial: projectsData.filter(p => p.registration_status === 'REGISTERED_COMMERCIALLY').length,
            nonCommercial: projectsData.filter(p => p.registration_status === 'REGISTERED_NOT_COMMERCIALLY').length,
            notRegistered: projectsData.filter(p => p.registration_status === 'NOT_REGISTERED').length
        };

        const statsContainer = document.getElementById('stats-container');
        statsContainer.innerHTML = `
            <div class="stat-card rounded-2xl p-6 shadow-lg bg-white border border-gray-200/80"
                 data-filter="all" onclick="filterProjects('all')">
                <div class="text-gray-600 text-sm font-medium mb-2">Total Projects</div>
                <div class="text-blue-600 text-3xl font-bold">${stats.total}</div>
            </div>
            <div class="stat-card rounded-2xl p-6 shadow-lg bg-white border border-gray-200/80"
                 data-filter="commercial" onclick="filterProjects('commercial')">
                <div class="text-gray-600 text-sm font-medium mb-2">Commercial</div>
                <div class="text-green-600 text-3xl font-bold">${stats.commercial}</div>
            </div>
            <div class="stat-card rounded-2xl p-6 shadow-lg bg-white border border-gray-200/80"
                 data-filter="non-commercial" onclick="filterProjects('non-commercial')">
                <div class="text-gray-600 text-sm font-medium mb-2">Non-Commercial</div>
                <div class="text-yellow-600 text-3xl font-bold">${stats.nonCommercial}</div>
            </div>
            <div class="stat-card rounded-2xl p-6 shadow-lg bg-white border border-gray-200/80"
                 data-filter="not-registered" onclick="filterProjects('not-registered')">
                <div class="text-gray-600 text-sm font-medium mb-2">Not Registered</div>
                <div class="text-red-600 text-3xl font-bold">${stats.notRegistered}</div>
            </div>
        `;

        function getStatusBadgeClass(status) {
            if (status === 'REGISTERED_COMMERCIALLY') return 'status-commercial';
            if (status === 'REGISTERED_NOT_COMMERCIALLY') return 'status-non-commercial';
            if (status === 'NOT_REGISTERED') return 'status-not-registered';
            return 'status-unknown';
        }

        function formatStatus(status) {
            return status.replace(/_/g, ' ');
        }

        function getButtons(project) {
            const externalIcon = `
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-4 h-4 ml-1.5 shrink-0">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                </svg>
            `;

            const registerUrl = `https://console.cloud.google.com/earth-engine/configuration/register?project=${project.project_name}`;
            const manageUrl = `https://console.cloud.google.com/earth-engine/configuration/manage-registration?project=${project.project_name}`;
            const quotaUrl = `https://console.cloud.google.com/iam-admin/quotas?metric=earthengine.googleapis.com%2Fdaily_eecu_usage_time&service=earthengine.googleapis.com&project=${project.project_name}`;

            if (project.registration_status === 'NOT_REGISTERED')
                return `<a href="${registerUrl}" target="_blank" class="btn btn-primary">Register Now ${externalIcon}</a>`;

            return `
                <a href="${quotaUrl}" target="_blank" class="btn btn-secondary">Manage Quota ${externalIcon}</a>
                <a href="${manageUrl}" target="_blank" class="btn btn-secondary">Manage Registration ${externalIcon}</a>
            `;
        }

        const projectsContainer = document.getElementById('projects-container');
        projectsContainer.innerHTML = projectsData.map((project, index) => `
            <div class="project-card rounded-2xl p-6 flex flex-col justify-between bg-white border border-gray-200/80 shadow-md hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
                 style="animation-delay: ${index * 50}ms"
                 data-status="${project.registration_status}">
                <div class="flex-grow">
                    <div class="flex items-center justify-between mb-4 gap-2">
                        <h3 class="text-xl font-semibold text-gray-900 truncate pr-2">${project.project_name}</h3>
                        <button class="copy-btn"
                                title="Copy project name"
                                onclick="copyToClipboard('${project.project_name.replace(/'/g, "\\\\'")}', this)">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 8.25V6a2.25 2.25 0 00-2.25-2.25H6A2.25 2.25 0 003.75 6v8.25A2.25 2.25 0 006 16.5h2.25m8.25-8.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-7.5A2.25 2.25 0 018.25 18v-1.5m8.25-8.25h-6a2.25 2.25 0 00-2.25 2.25v6" /></svg>
                        </button>
                    </div>

                    <div class="space-y-3">
                        <div>
                            <div class="text-gray-500 text-xs font-medium mb-1">Project ID</div>
                            <div class="flex items-center justify-between">
                                <span class="text-gray-700 text-sm font-mono">${project.project_id}</span>
                                <button class="copy-btn"
                                        title="Copy project ID"
                                        onclick="copyToClipboard('${project.project_id}', this)">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 8.25V6a2.25 2.25 0 00-2.25-2.25H6A2.25 2.25 0 003.75 6v8.25A2.25 2.25 0 006 16.5h2.25m8.25-8.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-7.5A2.25 2.25 0 018.25 18v-1.5m8.25-8.25h-6a2.25 2.25 0 00-2.25 2.25v6" /></svg>
                                </button>
                            </div>
                        </div>

                        <div>
                            <div class="text-gray-500 text-xs font-medium mb-2">Registration Status</div>
                            <span class="status-badge ${getStatusBadgeClass(project.registration_status)}">
                                ${formatStatus(project.registration_status)}
                            </span>
                        </div>
                    </div>
                </div>

                <div class="mt-6 pt-4 border-t border-gray-200/80 flex justify-end items-center flex-wrap gap-2">
                    ${getButtons(project)}
                </div>
            </div>
        `).join('');
    </script>

</body>
</html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_file


def get_projects_with_dashboard(output_dir=None):
    """Retrieves project list with registration status and creates dashboard.

    Args:
        output_dir: Optional path to directory for output files.
                   If None, saves to script directory.
    """
    if not check_gcloud():
        print(f"{Colors.RED}✗ gcloud is either not installed or not authenticated.{Colors.RESET}")
        sys.exit(1)

    print(f"{Colors.GREEN}✓ gcloud is installed and authenticated{Colors.RESET}\n")

    # Initialize Earth Engine session
    try:
        session = AuthorizedSession(ee.data.get_persistent_credentials())
        print(f"{Colors.GREEN}✓ Earth Engine session initialized{Colors.RESET}\n")
    except Exception as e:
        print(f"{Colors.RED}✗ Failed to initialize Earth Engine: {e}{Colors.RESET}")
        print(f"{Colors.YELLOW}Run 'earthengine authenticate' to authenticate.{Colors.RESET}")
        sys.exit(1)

    # Determine output directory
    if output_dir:
        output_path = Path(output_dir).resolve()
        try:
            output_path.mkdir(parents=True, exist_ok=True)
            print(f"{Colors.CYAN}Using custom output directory: {output_path}{Colors.RESET}\n")
        except Exception as e:
            print(f"{Colors.RED}Error creating output directory: {e}{Colors.RESET}")
            print(f"{Colors.YELLOW}Falling back to script directory{Colors.RESET}\n")
            output_path = Path(__file__).parent.resolve()
    else:
        output_path = Path(__file__).parent.resolve()

    # Get all projects
    is_windows = sys.platform.startswith('win')
    command = 'gcloud projects list --format=json' if is_windows else ['gcloud', 'projects', 'list', '--format=json']
    try:
        print(f"{Colors.CYAN}Checking Earth Engine permissions and registration status...{Colors.RESET}\n")
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

        # Process projects in parallel
        ee_projects = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_project = {
                executor.submit(project_permissions_with_registration, item['projectId'], session): item['projectId']
                for item in project_json
            }

            for future in as_completed(future_to_project):
                result = future.result()
                if result:
                    ee_projects.append(result)

        # Display results
        if ee_projects:
            print(f"{Colors.GREEN}{Colors.BOLD}Projects with Earth Engine enabled:{Colors.RESET}")
            display_projects_table(ee_projects)

            # Save JSON
            json_path = output_path / "ee_projects.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(ee_projects, f, indent=2)
            print(f"\n{Colors.GREEN}✓ Saved project data to: {json_path}{Colors.RESET}")

            # Create HTML dashboard in the output directory
            output_path = "ee_projects_dashboard.html"
            if output_dir is not None:
                output_path = Path(output_dir).resolve() / "ee_projects_dashboard.html"
            html_path = create_html_dashboard(ee_projects, output_path)

            print(f"{Colors.GREEN}✓ Created dashboard at: {html_path}{Colors.RESET}")

            # Try to open in browser if not headless
            if not is_headless():
                try:
                    webbrowser.open(f'file://{html_path}')
                    print(f"{Colors.CYAN}✓ Opened dashboard in default browser{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.YELLOW}Note: Could not auto-open browser: {e}{Colors.RESET}")
                    print(f"{Colors.CYAN}Open {html_path} in your browser to view the dashboard{Colors.RESET}")
            else:
                print(f"{Colors.CYAN}Open {html_path} in your browser to view the dashboard{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}No projects found with Earth Engine API enabled.{Colors.RESET}")

    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}Error: {e.output}{Colors.RESET}")
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}Error: Command timed out{Colors.RESET}")
    except json.JSONDecodeError:
        print(f"{Colors.RED}Error: Failed to parse JSON output{Colors.RESET}")


# Example usage:
# get_projects_with_dashboard()  # Uses script directory
# get_projects_with_dashboard(output_dir=r"C:\Users\samiam\Downloads\masks")  # Uses custom directory
