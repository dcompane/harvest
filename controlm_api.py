"""
Control-M Automation API client for harvesting metadata.
"""

import sys
from typing import Any, Dict, Optional
from dataclasses import dataclass
# import json
# from xml.parsers.expat import errors
# from xmlrpc import server
import requests
from urllib3 import disable_warnings, exceptions
import Utility
from Utility import print_debug

# Disable only the InsecureRequestWarning
disable_warnings(exceptions.InsecureRequestWarning)

# =============================================================================
# Authentication
# =============================================================================

@dataclass
class Auth:
    """Authentication credentials for Control-M API."""
    api_key: Optional[str] = None
    bearer_token: Optional[str] = None


class ControlMApi:
    """Client for interacting with the Control-M Automation API."""
    def __init__(self, base_url: str, auth: Auth, timeout: int = 60):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["accept"] = "*/*"
        self.session.headers["x-api-key"] = auth.api_key

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None,
             headers: Optional[Dict[str, Any]] = None,
             action: Optional[str] = "GET", data=None) -> Any:
        """Internal method to perform a GET request to the Control-M API."""
        path = path if path.startswith("/") else "/" + path
        url = f"{self.base_url}{path}"
        query = {key: value for key, value in (params or {}).items() if value is not None}
        request_headers = {k: v for k, v in (headers or {}).items() if v is not None}

        # Merge headers: session defaults + per-request overrides
        merged_headers = dict(self.session.headers)
        merged_headers.update(request_headers)  # overwrite duplicates

        print_debug(f"URL: {url}", Utility.debug)

        print_debug(f"Session headers: {self.session.headers}", Utility.debug)
        print_debug(f"Request headers: {request_headers}", Utility.debug)
        print_debug(f"Effective headers: {merged_headers}", Utility.debug)

        print_debug(f"Query: {query}", Utility.debug)

        if action.upper() == "GET":
            r = self.session.get(
                url,
                params=query,
                headers=merged_headers,
                timeout=self.timeout,
                verify=False,
            )
        elif action.upper() == "POST":
            r = self.session.post(
                url,
                json=data if data else {},
                params=query,
                headers=merged_headers,
                timeout=self.timeout,
                verify=False,
            )
        else:
            raise ValueError(f"Unsupported HTTP action: {action}")

        try:
            resp = r.json()
        except ValueError:
            resp = r.text

        print_debug(f"Response: {resp}", Utility.debug)

        return resp

    # ---- Status / Metadata ----
    def initial_test(self):
        """Return the Control-M Automation API status metadata."""
        print ("Running initial test...")
        try:
            test = self._get("/config/servers")  # Test connection
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Control-M API: {e}." \
                  " Verify the URL or API key.")
            sys.exit(24)
        if isinstance(test, dict):
            if "errors" in test.keys():
                print(f"Error connecting to Control-M API: " \
                      f"{test['errors']}. Verify the API key.")
                sys.exit(25)

    def get_status(self):
        """Return the Control-M Automation API status metadata."""
        print ("Retrieving status...")
        return self._get("/status")

    def get_version(self):
        """Return the Control-M Automation API status metadata."""
        print ("Retrieving version...")
        return self._get("/build_time.txt")

    # ---- Build ----
    def build(self, data: Dict[str, Any]):
        """Build service."""
        print ("Running build service...")
        return self._get("/build", params=data)

    # ---- Auth ----
    # GET/authentication/tokens
    def auth_tokens(self):
        """Return the authentication tokens."""
        print ("Retrieving authentication tokens...")
        return self._get("/authentication/tokens")

   # GET/authorization/roles
    def auth_roles(self, data: Optional[str] = None):
        """Return the authorization roles."""
        print ("Retrieving authorization roles...")
        return self._get(f"/authorization/roles{f'?role={data}' if data else ''}")

   # GET/authorization/role_associates
    def auth_role_associates(self, data:Optional[str] = None):
        """Return the authorization role associates."""
        print ("Retrieving authorization role associates...")
        return self._get(f"/authorization/role/{data}/associates")

   # GET/authorization/users
    def auth_users(self, data: Optional[str] = None):
        """Return the authorization users."""
        print ("Retrieving authorization users...")
        return self._get(f"/authorization/users{f'?name={data}' if data else ''}")

    # GET/authorization/organizationgroup/roles
    def auth_organizationgroup_roles(self, ogroup:
                    Optional[str] = None, rolequery: Optional[str] = None):
        """Return the authorization organization group roles."""
        print ("Retrieving authorization organization group roles...")
        return self._get(f"/authorization/organizationgroup/{ogroup}" \
                         f"/roles{f'?name={rolequery}' if rolequery else ''}")

    # GET/authorization/organizationgroups
    def auth_organizationgroups(self, data: Optional[str] = None):
        """Return the authorization organization groups."""
        print ("Retrieving authorization organization groups...")
        return self._get(f"/authorization/organizationgroups" \
                         f"{f'?name={data}' if data else ''}")


    # ---- Config ----
    ## ---- Config - Archive ----
    # GET/config/archive/rules
    def config_archive_rules(self):
        """Return the Control-M Archive Rules."""
        print("Retrieving Control-M Archive Rules...")
        return self._get("/config/archive/rules")

    # GET/config/archive/statistics
    def config_archive_statistics(self):
        """Return the Control-M Archive Statistics."""
        print("Retrieving Control-M Archive Statistics...")
        return self._get("/config/archive/statistics")

    ## ---- Config - EM System Settings ----
    def config_systemsettings(self, ctm : Optional[str] = None):
        """Return the Control-M EM System Settings."""
        print(f"Retrieving Control-M {ctm if ctm else 'EM'} System Settings...")
        if ctm:
            endpoint = f"?server={ctm}"
        return self._get(f"/config/systemsettings{endpoint if ctm else ''}")

    ## ---- Config - Servers ----
    def config_servers(self):
        """Return the Control-M Servers."""
        print("Retrieving Control-M Servers...")
        return self._get("/config/servers")

    def config_server_definition(self, server: str):
        """Return the Control-M Servers configuration definition."""
        print(f"Retrieving configuration definition for server {server}...")
        return self._get(f"/config/server/{server}/definition")

    def config_server_params(self, server: Optional[str] = None):
        """Return the Control-M Servers configuration definition."""
        print(f"Retrieving parameters for server {server}...")
        if server:
            endpoint = f"?server={server}"
        else:
            endpoint = ""
        return self._get(f"/config/systemsettings/server{endpoint}")

    def config_server_gateways(self, server: str):
        """
        Return the Control-M Servers gateways.
        NOT USED IN HARVEST, BUT MAY BE USEFUL FOR FUTURE ENHANCEMENTS
        """
        print(f"Retrieving gateways for server {server}...")
        return self._get(f"/config/server/{server}/gateways")

    ## ---- Config - Agents ----
    def config_agents(self, server: str):
        """Return the Control-M Agents for the specified server."""
        print(f"Retrieving Control-M Agents for server {server}...")
        return self._get(f"/config/server/{server}/agents")

    ## ---- Config - HostGroups ----
    def config_hostgroups(self, server: str):
        """Return the Control-M HostGroups for the specified server."""
        print(f"Retrieving Control-M HostGroups for server {server}...")
        return self._get(f"/config/server/{server}/hostgroups/agents")

    ## ---- Config - Agentless Hosts ----
    def config_agentlesshosts(self, server: str):
        """Return the Control-M Agentless Hosts for the specified server."""
        print(f"Retrieving Control-M Agentless Hosts for server {server}...")
        return self._get(f"/config/server/{server}/agentlesshosts")

    ## ---- Config - Agentless Host Properties ----
    def config_agentlesshost(self, server: str, agent: str):
        """Return the Control-M Agentless Host properties for the specified server/agent."""
        print(f"Retrieving Control-M Agentless Host for server {server} and agent {agent}...")
        return self._get(f"/config/server/{server}/agentlesshost/{agent}")

    ## ---- Config - Runasuser ----
    def config_runasusers(self, server: str):
        """Return the Control-M Runasusers for the specified server."""
        print(f"Retrieving Control-M Runasusers for server {server}...")
        return self._get(f"/config/server/{server}/runasusers")


    ## ---- Config - Users and Roles ----
    def config_users(self, server: str):
        """Return the Control-M EM Users."""
        print("Retrieving Control-M EM Users...")
        return self._get(f"/config/server/{server}/runasusers")

    ## ---- Config - EM DB Details ----
    def config_emdb_details(self):
        """Return the Control-M EM DB Details."""
        print("Retrieving Control-M EM DB Details...")
        return self._get("/config/em/db/details")

    # ---- Config - EM DB Space ----
    # This may need additional logic to handle the requestdb_space
    def config_emdb_space(self):
        """Return the Control-M EM DB Space."""
        print("Retrieving Control-M EM DB Space...")
        response = self._get("/config/em/db/space",
            headers={"accept": "application/json", "Content-Type": "application/json"},
            data={},
            action="POST")
        return response

    ##############################################################################

    # ---- Provision ----
    ## ---- Provision - Images ----
    def provision_images(self, os: str = "Linux"):
        """Return the available provision images."""
        print(f"Retrieving Control-M Provision Images for OS {os}...")
        return self._get(f"/provision/images/{os}")

    ## ---- Provision - upgrades ----
    def provision_upgrades(self, data_type: str = "Agent"):
        """Return the available provision environments."""
        print(f"Retrieving Control-M Provision {data_type} Upgrades...")
        return self._get(f"/provision/upgrades/agents?type={data_type}")

    def provision_upgrade_versions(self):
        """Return the available provision environments."""
        print("Retrieving Avalaible Provision Upgrades...")
        return self._get("/provision/upgrades/versions")

    # ---- Deploy ----
    ## ---- Deploy - Jobtypes ----
    def deploy_jobtypes(self):
        """
        Return the Client developed jobtypes available to the EM
        """
        print ("Retrieving job types...")
        return self._get("/deploy/ai/jobtypes")

    ## ---- Deploy - Folders ----
    def deploy_folders(self, server: str, folder: Optional[str] = "*"):
        """
        Return the folders on the specific Control-M Server, 
          optionally filtered by folder name and z/OS library.
        """
        print(f"Retrieving folder {folder} for server {server}...")
        return self._get(f"/deploy/folders?server={server}&folder={folder}")

    ## ---- Deploy - Jobs ----
    def deploy_jobs(self, server: str, folder: Optional[str] = "*"):
        """
        Return the Control-M Jobs for the specified server and folder.
        """
        print(f"Retrieving jobs for folder {folder} on server {server}...")
        return self._get(f"/deploy/jobs?server={server}&folder={folder}&useArrayFormat=True")

    ## ---- Deploy - Calendars ----
    def deploy_calendars(self, server: Optional[str] = "*"):
        """
        Return the Control-M Calendars for the specified server.
        """
        print(f"Retrieving calendars for server {server}...")
        return self._get("/deploy/calendars")

# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    assert "You should not see this message" \
        == "This file is not meant to be run directly."
