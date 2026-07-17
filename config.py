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
        if key in ["additionalParameters"]:
            columns = None


        excel.add_table(
            "EM Settings",
            value,
            table_title="Config EM Settings",
            description=f"Control-M EM System {key} Settings",
            direction=direction,
            columns=columns,
        )

    # em DB Details
    db_details = client.config_emdb_details()

    if "errors" in db_details.keys():
        print_debug(f"Error harvesting EM DB Details: {db_details['errors']}", debug)
    else:
        excel.add_table(
            "Misc",db_details,
            table_title="Config EM DB Details",
            description="Control-M EM DB Details",
            direction="vertical")
        if Utility.isSaaS:
            print_debug("Skipping EM DB Space harvest for SaaS environment.", debug)
        else:
            db_space = client.config_emdb_space()
            excel.add_table(
                "Misc",db_space[0],
                table_title="Config EM DB Space",
                description="Control-M EM DB Space",
                direction="vertical")

if __name__ == "__main__":
    assert "You should not be here, you should not be around" == "True"
