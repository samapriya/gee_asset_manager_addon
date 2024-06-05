__copyright__ = """

    Copyright 2024 Samapriya Roy

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""

import json
import shlex
import subprocess
import sys


def is_gcloud_installed():
    try:
        # Run the 'gcloud --version' command to check if gcloud is installed
        result = subprocess.run(['gcloud', '--version'], shell=True,capture_output=True, text=True)
        if result.returncode == 0:
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def is_gcloud_authenticated():
    try:
        # Run the 'gcloud auth list' command to check if gcloud is authenticated
        result = subprocess.run(['gcloud', 'auth', 'list'], shell=True,capture_output=True, text=True)
        if result.returncode == 0:
            output = result.stdout.strip()
            if "ACTIVE" in output:
                return True
            else:
                return False
        else:
            return False
    except FileNotFoundError:
        return False

def check_gcloud():
    if is_gcloud_installed() and is_gcloud_authenticated():
        return True
    else:
        return False

def list_enabled_services(pname):
    """Lists enabled services for a given project.

    Args:
        pname: The project name.

    Returns:
        A list of enabled services as a JSON object, or None if an error occurs.
    """
    command = f"gcloud services list --project={pname} --enabled --format=json"
    try:
        output = subprocess.run(shlex.split(command), shell=True, capture_output=True, text=True)
        return json.loads(output.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: gcloud command failed with code {e.returncode}.")
        return None
    except Exception as e:
        return None
def project_permissions(pname):
    """Checks if Earth Engine API is enabled for a project.

    Args:
        pname: The project name.
    """
    enabled_services = list_enabled_services(pname)
    data = enabled_services
    enabled_api_list = []
    if data is not None:
        for item in data:
            project_id = item["parent"]
            enabled_api_list.append(item['name'].split('services/')[-1])
        enabled_api_list = [item['name'].split('services/')[-1] for item in data if data is not None]
        if "earthengine.googleapis.com" in enabled_api_list:
            print(f"Project Name: {pname} Project Number: {project_id.split('/')[-1]}")

def get_projects():
    """Retrieves project list and checks Earth Engine permissions."""
    if not check_gcloud():
        sys.exit("gcloud is either not installed or not authenticated.")
    else:
        print("\n"+"gcloud is installed and authenticated")
    command = f"gcloud projects list --format=json"
    try:
        print("\n"+"Checking Earth Engine permissions for all projects..."+"\n")
        services_json = subprocess.check_output(command, shell=True, text=True)
        project_json  = json.loads(services_json)
        for item in project_json:
            project_permissions(item['projectId'])
    except subprocess.CalledProcessError as e:
        print("Error:", e.output)

#get_projects()
