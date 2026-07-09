#!/usr/bin/env python3
"""
ctm_inventory.py

Enterprise‑scalable Control‑M Automation API inventory exporter.

FEATURES
========
- Required CLI args: --base-url, --api-key
- Optional selectors: --include deploy,config
- Metadata worksheet (timestamp, AAPI host, status, version best‑effort)
- z/OS‑aware behavior via --zos-library
- Scalable iteration:
    Servers -> Folders -> Jobs
- Excel output using openpyxl (one dataset per worksheet)

TABLES CREATED
==============
Deploy:
- Deploy Folder Job Counts
- Deploy Agent Job Counts

Config:
- Config Servers
- Per-server Definitions (optional)
- Per-server Agents (optional)

SAFE FOR LARGE ENVIRONMENTS
===========================
No bulk download of all jobs. All job inspection is folder-scoped.
"""

from __future__ import annotations

# from csv import excel
import os
import sys
from datetime import datetime
from typing import Optional, Iterable
import argparse
import getpass
from urllib.parse import urlparse

import urllib3

import Utility
from Utility import print_debug
from controlm_api import ControlMApi, Auth
from ExcelWriter import ExcelWorkbookWriter  #, open_excel_worksheet
from config import harvest_em_settings

# Disable only the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =============================================================================
# Scalable Deploy Summaries
# =============================================================================

def collect_folder_job_counts(folder: dict, folder_only: bool = False):
    """
    Calculate job counts for each folder.
    """

    # Loop is to get the objects we need. there is always one folder in the items.
    for _, folder_obj in folder.items():
        print_debug (folder_obj, Utility.debug)
        job_count, jd = Utility.count_key_value_matches([folder_obj], "Type", "Job:*")
        sub_count, sd = Utility.count_key_value_matches([folder_obj], "Type", "SubFolder*")
        print_debug(f"JobCount:{job_count}, SubCount:{sub_count}", Utility.debug)

    job_depth = max(jd/2-1, 0)
    sub_depth = max(sd/2-1,0)
    print_debug(f"Name: {folder_obj[0]['Name']}", Utility.debug)
    print_debug(f"JobCount:{job_count}, SubCount:{sub_count}", Utility.debug)
    print_debug(f"JobDepth:{job_depth}, SubDepth:{sub_depth}", Utility.debug)

    return job_count, job_depth, sub_count, sub_depth

def collect_agent_job_counts(folders: dict, agent: str, server: str):
    """
    Calculate job counts for each agent by counting jobs in folders that 
    are associated with the agent.    
    """
    jc = 0
    for _, folder in folders.items():
        job_count, _ = Utility.count_key_value_matches(folder, "Host", agent)
        jc += job_count
    return int(jc)


# =============================================================================
# Worksheet specific
# =============================================================================
# Metadata
# =============================================================================

def metadata_worksheet(client: ControlMApi):
    """
    Create the Metadata worksheet with AAPI status information.
    """
    parsed = urlparse(client.base_url)
    status_line = split_status(client.get_status())
    metadata = {
        "Timestamp": datetime.now().isoformat(),
        "AAPI Base URL": client.base_url,
        "AAPI Host": parsed.hostname,
        "AAPI Version": client.get_version(),
        "AAPI Status:": status_line[1],
        "AAPI SaaS:": status_line[3],
        "AAPI GSR Heartbeat:": status_line[5] if len(status_line) > 4 else "N/A",
        "AAPI CSM Heartbeat:": status_line[6] if len(status_line) > 5 else "N/A"
    }
    Utility.isSaaS = True if status_line[3].find("true") != -1 else False
    print(f"Control-M environment is SaaS: {Utility.isSaaS}")
    return metadata

def split_status(status_lines):
    """Split the status lines into a dictionary."""
    lines = status_lines.splitlines()
    line_vars = {i + 1: line for i, line in enumerate(lines)}
    return line_vars

#Job Counts
# =============================================================================
def job_counts_worksheet(servers, client: ControlMApi):
    """Create the Job Counts per Control-M server worksheet."""
    config_servers = client.config_servers(servers)

    return config_servers

#Agent Counts
# =============================================================================
def agent_counts_worksheet(servers, client: ControlMApi):
    """Create the Agent Counts worksheet."""
    config_servers = client.config_servers(servers)

    return config_servers

# =============================================================================
# Main
# =============================================================================

def main(debug: bool = False, argv: Optional[Iterable[str]] = None):
    """Main entry point for the inventory exporter."""

    parser = argparse.ArgumentParser(
        description="Scalable Control-M Automation API inventory exporter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--base-url", required=True, 
            help="Base URL of the Control-M Automation API"+
                " (e.g. https://aapi.example.com:8443/automation-api)")
    parser.add_argument("--api-key", required=False, 
            help="Control-M Automation API key with appropriate permissions")
    parser.add_argument("--include", default="deploy,config,auth", 
            help="Comma-separated list of datasets to include (deploy, config, auth)")
    parser.add_argument("--zos-library", default=None, 
            help="(Optional) z/OS library name to filter deploy data for z/OS environments")
    parser.add_argument("--timeout", type=int, default=60, 
            help="HTTP request timeout in seconds")
    parser.add_argument("--output", default="controlm_inventory",
            help="Output Excel file name")
    parser.add_argument("--server", action="append", default=None, 
            help="(Optional) Control-M Server name to target (can specify multiple times)")
    parser.add_argument("--debug",  default=False, 
            help="Enable debug mode")
    parser.add_argument("--folderlimit",  default=10, 
            help="Limit the number of folders to include in the inventory (for testing with large environments) NOT IMPLEMENTED")

    args = parser.parse_args(list(argv) if argv else None)

    #Set Debug mode in Utility module
    Utility.debug= Utility.str_to_bool(str(args.debug))
    print_debug(f"Default debug is {args.debug}", True)

    if not args.api_key:
        args.api_key = getpass.getpass(prompt="Enter Control-M API key: ", echo_char="*")
        if bool(args.api_key) == False:
            print("Error: API key is required.")
            sys.exit(42)

    includes = Utility.parse_include(args.include)
    print_debug(f"Current debug is {args.debug}", True)
    args.output = args.output + f"_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
    print(f"File {args.output} will be written to {os.getcwd()}")

    client = ControlMApi(args.base_url, Auth(api_key=args.api_key), args.timeout)
    excel = ExcelWorkbookWriter()

    client.initial_test()

    # Metadata is always included
    # excel.add_sheet("Metadata")
    excel.add_table("Metadata", metadata_worksheet(client), direction="vertical", table_title="Metadata", description="Control-M Automation API environment metadata such as version, status, and host information")

    # Control-M Servers are always included
    servers = client.config_servers()
    # server_names = [
    #     s["name"] for s in servers if isinstance(s, dict)
    #     #s["name"] for s in servers if isinstance(s, dict) and s.get("state") == "Up" 
    # ]

    rows = None
    for server in servers:
        svr_def = client.config_server_definition(server["name"])
        if rows is None:
            rows = [{**server, **svr_def}]
        else:
            rows.append({**server, **svr_def})

    srvs_up = [s["name"] for s in rows if isinstance(s, dict) and s.get("state") == "Up" or []]
    srvs_dist_up = [s["name"] for s in rows if isinstance(s, dict) and s.get("state") == "Up"
                    and s.get("type") == "Distributed" or []]
    print_debug(f"Distributed servers: {srvs_dist_up}", Utility.debug)


    print_debug(f"Creating Config Servers worksheet: {len(rows)} rows", Utility.debug)
    excel.add_table("Config Servers", rows, table_title="Config Servers", 
            description="List of Control-M Servers with details such as type, version, and status",
            direction="horizontal" )

    for server in srvs_up:
        print_debug(f"Server parameters for {server}: {svr_def}", Utility.debug)
        svr_def = client.config_server_params(server=server)

        for item in svr_def:
            item.update({"server": server})

        excel.add_table("Config Servers", svr_def, table_title="Config Server Parameters",
            description=f"List of Control-M Server Parameters for server {server}",
            direction="horizontal", columns=None)

    all_jobs={"Folders":[]}
    all_folders = []

    for srv in srvs_up or []:
        folders = client.deploy_folders(server=srv)
        # \ is continuation line
        for folder_name in folders.keys():
            fldr_toadd = {}
            fldr_toadd["folder"] = folder_name
            fldr_toadd["Type"] = folders[folder_name]["Type"] \
                if "Type" in folders[folder_name].keys() else None
            fldr_toadd["server"] = folders[folder_name]["ControlmServer"] \
                if "ControlmServer" in folders[folder_name].keys() else srv
            fldr_toadd["Description"] = folders[folder_name]["Description"] \
                if "Description" in folders[folder_name].keys() else None
            fldr_toadd["application"] = folders[folder_name]["Application"] \
                if "Application" in folders[folder_name].keys() else None
            fldr_toadd["subapplication"] = folders[folder_name]["SubApplication"] \
                if "SubApplication" in folders[folder_name].keys() else None
            fldr_toadd["orderMethod"] = folders[folder_name]["OrderMethod"] \
                if "OrderMethod" in folders[folder_name].keys() else None
            fldr_toadd["SiteStandard"] = folders[folder_name]["SiteStandard"] \
                if "SiteStandard" in folders[folder_name].keys() else None
            fldr_toadd["activeRetentionPolicy"] = folders[folder_name]["ActiveRetentionPolicy"] \
                if "ActiveRetentionPolicy" in folders[folder_name].keys() else None
            fldr_toadd["createdBy"] = folders[folder_name]["CreatedBy"] \
                if "CreatedBy" in folders[folder_name].keys() else None

            print_debug(f"Loading {folder_name}'s jobs data...", Utility.debug)
            jobs_data = client.deploy_jobs(srv, folder_name)
            if "errors" in jobs_data.keys():
                print_debug(f"Error retrieving jobs for folder {folder_name}: {jobs_data['errors']}", Utility.debug)
                print_debug(f"{folder_name}'s contain an unsupported job or other error occurred.\n"+ \
                        f"Fix the folder and try again.\nReturned data: {jobs_data}", Utility.debug)
            else:
                if len(jobs_data["Folders"]) > 0:  # Non-Empty folder
                    all_jobs["Folders"].append(jobs_data["Folders"][0].copy()) 
                    JobCount, JobDepth, SubCount, SubDepth = collect_folder_job_counts(jobs_data)
                else:
                    all_jobs["Folders"].append(jobs_data["Folders"].copy())
                    JobCount, JobDepth, SubCount, SubDepth = 0, 0, 0, 0

                fldr_toadd["SubFolders #"] = SubCount
                fldr_toadd["SubFolders Depth"] = SubDepth
                fldr_toadd["Jobs #"] = JobCount
                fldr_toadd["Jobs Depth"] = JobDepth

        all_folders.append(fldr_toadd)

    excel.add_table("Folders", all_folders,
                table_title="Folders",
                description="List of folders in the deployment. Depth zero is no subfolders.")

# ---- Auth ----
    if "auth" in includes:

        tokens = client.auth_tokens()["tokens"]
        # excel.add_sheet(f"Tokens Info")
        excel.add_table("Tokens Info", tokens, table_title="Tokens Info ", description="List of active authentication tokens with details such as user, creation time, and expiration time", direction="horizontal" )

# ---- Config ----
    if "config" in includes:

        harvest_em_settings(client, excel)

        # For all servers
        all_agents = []
        for srv in srvs_dist_up:
            # agents for a svr
            agents = client.config_agents(srv)
            upgrades = client.provision_upgrades(type="Agent")
            for _, agent in agents.items():
                for _, agent_item in enumerate(agent):
                    agent_item["server"] = srv
                    agent_item.pop("associatedAgents", None)
                    agent_item.pop("hostgroups", None)
                    agent_item["Job Count"] = collect_agent_job_counts(all_jobs, agent_item["nodeid"], srv)
                    if not Utility.isSaaS:
                        for upgrade in upgrades:
                            if (upgrade["ctm"] == srv and upgrade["agent"] == agent_item["nodeid"] and
                                    upgrade.get("eligibleToUpgrade", False) is True and upgrade["type"] == "Agent"):
                                agent_item["eligibleToUpgrade"] = True
                                agent_item["platform"] = upgrade["platform"]
                                agent_item["fromVersion"] = upgrade["fromVersion"]
                                agent_item["toVersion"] = upgrade["toVersion"]
                                agent_item["packageName"] = upgrade["packageName"]

                                break

                    all_agents.append(agent_item)

            # deferring the writing of the worksheet until the end of the server loop. 
            #   This allows us to gather all the relevant data across all servers before committing it
            #   to the worksheet, which is more efficient and ensures that the worksheet is complete 
            #   and well-organized when it's created.
            
            # hostgroups
            hostgroups = client.config_hostgroups(srv)
            all_hostgroups = []
            for hostgroup in hostgroups:
                for agent in hostgroup["agentslist"]:
                    hg_toadd = {}
                    hg_toadd["server"] = srv
                    hg_toadd["hostgroup"] = hostgroup["hostgroup"]
                    hg_toadd["applicationType"] = hostgroup["applicationType"]
                    hg_toadd["tag"] = hostgroup["tag"]
                    hg_toadd["agent"] = agent["host"]
                    if "participationRules" in agent.keys():
                        hg_toadd["participation rules"] = agent["participationRules"]
                    else:
                        hg_toadd["participation rules"] = None
                    all_hostgroups.append(hg_toadd)

            # Agentless
            agentlesshosts = client.config_agentlesshosts(srv)
            all_agentless = []
            for agentless in agentlesshosts:
                agent = client.config_agentlesshost(srv, agentless)
                agls_toadd = {}
                agls_toadd["server"] = srv
                agls_toadd["agentlesshost"] = agent["remotehost"]
                agls_toadd["connectionType"] = agent["connectionType"] \
                    if "connectionType" in agent.keys() else None
                agls_toadd["port"] = agent["port"] if "port" in agent.keys() else None
                agls_toadd["encryptAlgorithm"] = agent["encryptAlgorithm"] \
                    if "encryptAlgorithm" in agent.keys() else None
                agls_toadd["compression"] = agent["compression"] \
                    if "compression" in agent.keys() else None
                agls_toadd["tag"] = agent["tag"] if "tag" in agent.keys() else None
                agls_toadd["wMISysoutDirectory"] = agent["wMISysoutDirectory"] \
                    if "wMISysoutDirectory" in agent.keys() else None
                agls_toadd["agents"] = ", ".join(agent["agents"]) \
                    if "agents" in agent.keys() else None
                all_agentless.append(agls_toadd)

            # Runasusers
            runasusers = client.config_runasusers(srv)
            all_runasusers = []
            for runasuser in runasusers:
                rau_toadd = {}
                rau_toadd["server"] = srv
                rau_toadd["agent"] = runasuser["agent"]
                rau_toadd["runasuser"] = runasuser["user"]
                rau_toadd["auth Method"] = "key" if "key" in runasuser.keys() else "password"
                if "key" in runasuser.keys():
                    rau_toadd["keyname"] = runasuser["key"]["keyname"]

                all_runasusers.append(rau_toadd)


        # Commit the worksheets once the servers have been processed
        excel.add_table("Agents", all_agents, table_title="Config Agents",
            description="List of Control-M Agents with details across all distributed servers")
        # excel.add_table("HostGroups", all_hostgroups, table_title="Config HostGroups", description="List of Control-M HostGroups with details across all distributed servers")
        excel.add_table("HostGroups", all_hostgroups, table_title="Hostgroups",
            description="List of Control-M HostGroups with details across all distributed servers")
        excel.add_table("Agentless Hosts", all_agentless,
            description="List of Control-M Agentless Hosts with details across all distributed servers")
        excel.add_table("Runasusers", all_runasusers, table_title="Config Runasusers",
            description="List of Control-M Runasusers with details across all distributed servers")
        
        # Archive Rules
        archive_rules = client.config_archive_rules()
        archive_stats = client.config_archive_statistics()

        if "errors" in archive_rules.keys():
            print(f"Error retrieving archive rules: {archive_rules['errors']}")
        else:
            rules_stats_summary = [
                {"totalNumberOfJobs": archive_stats["summary"]["totalNumberOfJobs"] if "totalNumberOfJobs" in archive_stats["summary"].keys() else None},
                {"totalDataSize": archive_stats["summary"]["totalDataSize"] if "totalDataSize" in archive_stats["summary"].keys() else None},
                {"actualDbSize": archive_stats["summary"]["actualDbSize"] if "actualDbSize" in archive_stats["summary"].keys() else None},
                {"diskUsage": archive_stats["summary"]["diskUsage"] if "diskUsage" in archive_stats["summary"].keys() else None}
            ]
            excel.add_table("Archive", rules_stats_summary, table_title="Archive Rules Summary", description="Summary of Control-M Archive Rules statistics such as total number of archived jobs and data size")

            all_archive = []
            for rule in archive_stats["rulesStatisticList"].get("ruleStatistics",[]):
                rule_toadd = {}
                rule_toadd["rulename"] = rule["ruleName"]
                rule_toadd["retention"] = rule["retention"] if "retention" in rule.keys() else None
                rule_toadd["retentionType"] = rule["retentionType"] if "retentionType" in rule.keys() else None
                rule_toadd["oldestItem"] = rule["oldestItem"] if "oldestItem" in rule.keys() else None
                rule_toadd["newestItem"] = rule["newestItem"] if "newestItem" in rule.keys() else None
                rule_toadd["totalJobs"] = rule["totalJobs"] if "totalJobs" in rule.keys() else None
                rule_toadd["dataSize"] = rule["dataSize"] if "dataSize" in rule.keys() else None
                if "statistics" in archive_stats.keys():
                    for stat in archive_stats["statistics"]:
                        if stat.get("archiveRule") == rule["name"]:
                            rule_toadd["lastArchiveTime"] = stat.get("lastArchiveTime")
                            rule_toadd["lastArchiveStatus"] = stat.get("lastArchiveStatus")
                            break
                all_archive.append(rule_toadd)


            excel.add_table("Archive Rules", archive_rules, table_title="Config Archive Rules",
                description="List of Control-M Archive Rules with details "+
                    "such as name, type, and retention period")

    # ---- Provision ----    
    # Add the ctm provision images "Linux" and "Windows" to the workbook to see
    #   what is available in the environment. This is not server specific,
    #   so we can do it outside of the server loop.
    if "provision" in includes:

        excel.add_table("Images", client.provision_images("Linux"),
                        table_title="Provision Images - Linux",
                        description="List of available Control-M provision images for Linux")
        excel.add_table("Images", client.provision_images("Windows"),
                        table_title="Provision Images - Windows",
                        description="List of available Control-M provision images for Windows")
        if not Utility.isSaaS:
            excel.add_table("Upgrades", client.provision_upgrades(type="Agent"),
                        table_title="Provision Upgrades - Agents",
                        description="List of available agent upgrade packages")
            excel.add_table("Upgrades", client.provision_upgrades(type="MFT"),
                        table_title="Provision Upgrades - MFT",
                        description="List of available agent upgrade packages")
            excel.add_table("Upgrades", client.provision_upgrade_versions(),
                        table_title="Provision Upgrades - Versions",
                        description="List of available upgrade versions.")

        # Should be in deploy, but it is really a Provision item
        jobtypes = client.deploy_jobtypes()
        all_jobtypes = []
        for jobtype in jobtypes["jobtypes"]:
            jobtype_toadd = {}
            jobtype_toadd["name"] = jobtype["jobTypeName"]
            jobtype_toadd["jobTypeId"] = jobtype["jobTypeId"]
            jobtype_toadd["status"] = jobtype["status"]
            jobtype_toadd["description"] = jobtype["description"]
            all_jobtypes.append(jobtype_toadd)

        excel.add_table("Plugins", all_jobtypes,
                        table_title="Jobtypes",
                        description="List of jobtypes available custom-developed.")

    # ---- Deploy ----
    if "deploy" in includes:

        # ---- Deploy - App-SubApps ----
        print_debug("Collecting App-SubApp data...", Utility.debug)
        apps = Utility.count_job_combinations(all_jobs, ["ControlmServer", "Application", "SubApplication"])

        excel.add_table("App-SubApps", apps, table_title="AppSubApps",
            description="List of all jobs in the deployment with details such as folder, server, and job type")
        
        # ---- Deploy - Calendars ----
        print_debug("Collecting Calendar data...", Utility.debug)
        calendars = client.deploy_calendars()

        all_calendars = []

        if "message" in calendars:
            message = calendars.get("message", "")
            for calendar in calendars["calendars"]:
                calendar_toadd = {}
                calendar_toadd["server"] = calendar.get("Server", "*")
                calendar_toadd["name"] = calendar.get("Name", "Undefined")
                calendar_toadd["Type"] = calendar["Type"].split(":")[1] if "Type" in calendar.keys() else None
                calendar_toadd["Alias"] = calendar.get("Alias", "N/A")
                calendar_toadd["Description"] = calendar.get("Description", "")
                calendar_toadd["When"] = ""
                if calendar_toadd["Type"] == "Regular":
                    calendar_toadd["When"] = Utility.get_values_for_key(calendar["When"]["Years"], "Year") if "When" in calendar.keys() else "No information available"
                all_calendars.append(calendar_toadd)
        else:
            message = ""
            for name, calendar in calendars.items():
                calendar_toadd = {}
                calendar["server"] = calendar.get("Server", "*")
                calendar_toadd["name"] = name
                calendar_toadd["Type"] = calendar["Type"].split(":")[1] \
                        if "Type" in calendar.keys() else None
                calendar_toadd["Alias"] = calendar.get("Alias", "N/A")
                calendar_toadd["Description"] = calendar.get("Description", "")
                calendar_toadd["When"] = ""
                if calendar_toadd["Type"] == "Regular":
                    calendar_toadd["When"] = Utility. \
                    get_values_for_key(calendar["When"]["Years"], "Year")

                all_calendars.append(calendar_toadd)

        excel.add_table("Calendars", all_calendars, table_title="Calendars",
            description=f"List of all calendars. {message}")


    # It's a wrap!
    current_dir_os = os.getcwd()
    excel.save(args.output)
    print(f"\n✅ Inventory workbook created in {current_dir_os}{os.path.sep}{args.output}")


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    print("Starting Control-M Inventory...")
    print(f"harvest version: {Utility.harvest_version}")
    sys.exit(main(debug=Utility.debug)) 