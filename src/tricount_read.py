from tricount_api import TricountAPI
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()


def fetch_tricount_data():
    # Initialize with tricount public identifier token from env
    key = os.environ.get("TRICOUNT_KEY")
    trapi = TricountAPI(tricount_key=key)
    # Access raw JSON data
    return trapi.get_data()


def get_net_from_tricount(data: Any) -> Dict[str, float]:
    # data may be a dict (already loaded JSON) or a path to the JSON file
    if isinstance(data, str):
        with open(data, "r", encoding="utf-8") as f:
            data = json.load(f)
    reg = data["Response"][0]["Registry"]

    # id -> display_name
    members = {
        mm["RegistryMembershipNonUser"]["id"]: mm["RegistryMembershipNonUser"]["alias"][
            "display_name"
        ]
        for mm in reg.get("memberships", [])
    }

    paid = {name: 0.0 for name in members.values()}
    share = {name: 0.0 for name in members.values()}

    for ewrap in reg.get("all_registry_entry", []):
        e = ewrap.get("RegistryEntry")
        if not e:
            continue
        amt = float(e["amount"]["value"])
        mo = e.get("membership_owned")
        if mo and mo.get("RegistryMembershipNonUser"):
            owner_rm = mo["RegistryMembershipNonUser"]
            owner_name = members.get(owner_rm["id"], owner_rm["alias"]["display_name"])
            paid[owner_name] += -amt
        for alloc in e.get("allocations", []):
            a_amt = float(alloc["amount"]["value"])
            mem = alloc.get("membership")
            if mem and mem.get("RegistryMembershipNonUser"):
                rm = mem["RegistryMembershipNonUser"]
                name = members.get(rm["id"], rm["alias"]["display_name"])
                share[name] += -a_amt

    # round to 2 decimal places and return floats
    net = {}
    for name in paid:
        net[name] = round(paid[name] - share[name], 3)
    return net


if __name__ == "__main__":
    data = fetch_tricount_data()
    balances = get_net_from_tricount(data)
    print(balances)
