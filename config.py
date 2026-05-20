"""
Harvest config from the Control-M client and write to Excel.
"""
from Utility import print_debug, debug
import Utility

# EM Settings "errors" deleted
EMSettings = [
  "additionalParameters",
  "allowDuplicateJobNames",
  "annotations",
  "cmsCommMode",
  "enableExternalAlerts",
  "enabledVaultProviders",
  "enforceSiteStandards",
  "environmentBannerColor",
  "environmentDescription",
  "environmentTitle",
  "firstDayOfTheWeek",
  "historyRetentionDays",
  "ldapSettings",
  "newDayTime",
  "privacyNoticeURL",
  "saml2IdentityProvider",
  "siteInterfaceLanguage",
  "strictnesslevel",
  "userAuditAnnotation"
]

def harvest_em_settings(client, excel):
    """Harvest EM system settings from the Control-M client and write to Excel.

    Args:
        client: Control-M API client with method config_systemsettings().
        excel: ExcelWriter-like object with add_table(name, data, ...) method.
    """
    print_debug("Harvesting EM Settings...", debug)
    settings = client.config_systemsettings()
    if settings.get("errors", None) is not None or settings.get("Message", None) is not None :
        # use the 'errors' key returned by the API
        print_debug(f"Error harvesting EM Settings: {settings['errors']}", debug)
        return

    for key, setting in settings.items():
        # copy mutable values to avoid accidental mutation
        try:
            value = setting.copy()
        except Exception:
            value = setting

        if isinstance(value, list):
            direction = "horizontal"
        else:
            direction = "vertical"

        columns = ["Setting", "Value"] if key not in ["annotations"] else ["Settings"]

        excel.add_table(
            "EM Settings",
            value,
            table_title="Config EM Settings",
            description=f"Control-M EM System {key} Settings",
            direction=direction,
            columns=columns,
        )



if __name__ == "__main__":
    assert "You should not be here, you should not be around" == "True"





        # # EM System Settings - only relevant if at least one server is up since it is an EM-level setting
        # settings = client.config_systemsettings()
        # # Future: Commentiting until have time to fix
        # # excel.add_table("EM LDAP Settings", settings["ldapSettings"], table_title="Config EM LDAP Settings", 
        # #             description="Control-M EM LDAP System Settings", direction="vertical")
        # if not Utility.isSaaS:
        #     settings.pop("ldapSettings")
        # # Future: Commentiting until have time to fix
        # # excel.add_table("EM SAML Settings", settings["saml2IdentityProvider"], table_title="Config EM SAML Settings", 
        # #             description="Control-M EM SAML System Settings", direction="vertical")
        # settings.pop("saml2IdentityProvider")
        # set_rows = []
        # for item in settings["additionalParameters"]:
        #     set_toadd = {}
        #     set_toadd["Category"] = item["category"] if "category" in item.keys() else ''
        #     set_toadd["Parameter"] = item["name"]
        #     set_toadd["Value"] = item["value"]
        #     set_rows.append(set_toadd)

        # excel.add_table("EM System Settings", set_rows, table_title="Config EM System Settings", 
        #             description="Control-M EM System Settings")
        
        # # for server in srvs_up:
        # #     settings = client.config_systemsettings(server)
        # #     excel.add_table(f"{server} System Settings", settings, table_title=f"{server} System Settings", 
        # #                 description=f"Control-M EM System Settings for {server}")
    
        # # For each distributed server, get objects that are only relevant to distributed environments (agents, hostgroups, etc.)
        