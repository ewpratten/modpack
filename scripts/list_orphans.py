import argparse
import sys
import logging
import requests
import json
import tomllib
from typing import List, Tuple, Dict, Union
from pathlib import Path

logger = logging.getLogger(__name__)


def main() -> int:
    # Handle program arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("--dot", help="Output a graphviz dot file here", type=Path)
    ap.add_argument(
        "-v", "--verbose", help="Enable verbose logging", action="store_true"
    )
    args = ap.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s:	%(message)s",
    )

    # Get a list of all toml files in the mods dir
    mods_tomls = list((Path(__file__).parent.parent / "mods").glob("*.toml"))

    # Look for update.modrinth.mod-id and update.modrinth.version
    mods = []
    for mod_toml in mods_tomls:
        with open(mod_toml, "rb") as f:
            mod = tomllib.load(f)
            if "update" in mod and "modrinth" in mod["update"]:
                mods.append(
                    {
                        "name": mod["name"],
                        "mod_id": mod["update"]["modrinth"]["mod-id"],
                        "version_id": mod["update"]["modrinth"]["version"],
                        "dependencies": [],
                    }
                )

    # Build a map of dependencies
    # mod_dependencies: Dict[str, List[str]] = {}
    for mod in mods:
        # Read the version metadata
        version_metadata = requests.get(
            f"https://api.modrinth.com/v2/version/{mod['version_id']}"
        ).json()

        # Track the dependencies
        for dependency in version_metadata.get("dependencies", {}):
            if "project_id" in dependency:
                mod["dependencies"].append(
                    {"name": None, "mod_id": dependency["project_id"]}
                )
                
    # In-fill all the dependency names (that we know about)
    for mod in mods:
        for dependency in mod["dependencies"]:
            for mod_data in mods:
                if mod_data["mod_id"] == dependency["mod_id"]:
                    dependency["name"] = mod_data["name"]
                    break
                
    # De-dupe dependencies
    for mod in mods:
        mod["dependencies"] = list({v['name']:v for v in mod["dependencies"]}.values())
        
    # If graphviz output requested, write it
    if args.dot:
        with open(args.dot, "w") as f:
            f.write("digraph {\n")
            for mod in mods:
                f.write(f'"{mod["name"]}" [label="{mod["name"]}"];\n')
                for dependency in mod["dependencies"]:
                    f.write(f'"{mod["name"]}" -> "{dependency["name"]}";\n')
            f.write("}\n")
                
    # Build a map of all mods, and which other mods depend upon them
    mod_to_dependers: Dict[str, List[str]] = {name:[] for name in [mod["name"] for mod in mods]}
    for mod in mods:
        for dependency in mod["dependencies"]:
            if dependency["name"] not in mod_to_dependers:
                mod_to_dependers[dependency["name"]] = []
            mod_to_dependers[dependency["name"]].append(mod["name"])
            
    print(json.dumps(mod_to_dependers, indent=4))


    return 0


if __name__ == "__main__":
    sys.exit(main())
