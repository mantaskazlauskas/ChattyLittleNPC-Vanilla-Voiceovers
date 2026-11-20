#!/usr/bin/env python3
"""
Deploy script for WoW addon repos.
Copies the addon folder into the selected WoW version's Interface/AddOns directory.

Adapted from the ChattyLittleNpc deploy.py. Addon folders are discovered by
looking for a directory whose name matches a .toc file inside it, rather than
being hardcoded. A voiceover repo can hold several addon folders per locale
(the quest pack and the books & gossip pack); the script asks which language
to deploy (Enter = enUS) and deploys all of that language's packs, then asks
which WoW version, then asks for confirmation.

Usage:
    python deploy.py
"""

import os
import re
import stat
import sys
import shutil

# Maintainer's install path -- change this to wherever World of Warcraft is installed on your machine.
WOW_ROOT = r"D:\Games\World of Warcraft"

# Human-readable labels for known WoW version folders
VERSION_LABELS = {
    "_retail_":      "Retail (The War Within / Midnight)",
    "_classic_":     "Classic (Cataclysm / Mists)",
    "_classic_era_": "Classic Era (Season of Discovery)",
    "_anniversary_": "Classic Anniversary",
    "_ptr_":         "PTR (Public Test Realm)",
    "_xptr_":        "xPTR",
    "_beta_":        "Beta",
}

ADDONS_RELATIVE = os.path.join("Interface", "AddOns")

# Voiceover packs are named <Addon>_<locale>_voiceovers (e.g. _enUS_, _deDE_); a pack
# without a suffix is English (legacy naming).
LOCALE_PACK_RE = re.compile(r'_([a-z]{2}[A-Z]{2})_voiceovers$')
DEFAULT_LOCALE = "enUS"


def find_addon_sources():
    """
    Return the absolute paths to the addon folders next to this script.

    An addon folder is a subdirectory containing <same-name>.toc, which is the
    layout WoW itself requires, so this cannot pick the wrong directory.
    Voiceover repos may hold one addon folder per locale.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    matches = []
    for entry in sorted(os.listdir(script_dir)):
        candidate = os.path.join(script_dir, entry)
        if not os.path.isdir(candidate) or entry.startswith('.'):
            continue
        if os.path.isfile(os.path.join(candidate, f"{entry}.toc")):
            matches.append(candidate)

    if not matches:
        print("ERROR: No addon folder found next to this script.")
        print("       Expected a subdirectory containing a matching .toc file,")
        print("       e.g. ChattyLittleGossipTracker/ChattyLittleGossipTracker.toc")
        sys.exit(1)

    return matches


def get_locale(source):
    """Locale of a voiceover pack folder, e.g. deDE; packs without a locale suffix are English."""
    match = LOCALE_PACK_RE.search(os.path.basename(source))
    return match.group(1) if match else DEFAULT_LOCALE


def prompt_locale(sources):
    """
    Ask which language to deploy; Enter picks English. A language can ship as
    several packs (quests and books & gossip, see split_voiceovers.py), which
    only work as a set, so every pack of the chosen language is deployed.
    Returns a list of addon folders (all of them for 'a').
    """
    if len(sources) == 1:
        return sources

    by_locale = {}
    for source in sources:
        by_locale.setdefault(get_locale(source), []).append(source)
    locales = sorted(by_locale)
    if len(locales) == 1:
        return sources

    default = locales.index(DEFAULT_LOCALE) + 1 if DEFAULT_LOCALE in locales else 1

    print()
    print("Available voiceover languages:")
    print()
    for i, locale in enumerate(locales, start=1):
        marker = "  (default)" if i == default else ""
        packs = ", ".join(os.path.basename(s) for s in by_locale[locale])
        print(f"  [{i}] {locale}  {packs}{marker}")
    print("  [a] All of the above")
    print()

    while True:
        raw = input(f"Select language [1-{len(locales)}, a, Enter = {locales[default - 1]}]: ").strip().lower()
        if raw == "":
            return by_locale[locales[default - 1]]
        if raw == "a":
            return sources
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(locales):
                return by_locale[locales[choice - 1]]
        print(f"  Please enter a number between 1 and {len(locales)}, 'a', or press Enter.")


def discover_versions(wow_root):
    """
    Scan wow_root for version folders that contain Interface/AddOns.
    Returns a list of (folder_name, addons_path, label) sorted by folder name.
    """
    versions = []
    if not os.path.isdir(wow_root):
        print(f"ERROR: WoW root not found at: {wow_root}")
        sys.exit(1)

    for entry in sorted(os.listdir(wow_root)):
        full_path = os.path.join(wow_root, entry)
        if not os.path.isdir(full_path):
            continue
        addons_path = os.path.join(full_path, ADDONS_RELATIVE)
        if os.path.isdir(addons_path):
            label = VERSION_LABELS.get(entry, entry)
            versions.append((entry, addons_path, label))

    return versions


def prompt_version(versions):
    """Print a numbered menu and return the chosen (folder_name, addons_path, label)."""
    print()
    print("Available WoW versions:")
    print()
    for i, (folder, addons_path, label) in enumerate(versions, start=1):
        print(f"  [{i}] {label}")
        print(f"       {addons_path}")
    print()

    while True:
        raw = input(f"Select version [1-{len(versions)}]: ").strip()
        if raw.isdigit():
            choice = int(raw)
            if 1 <= choice <= len(versions):
                return versions[choice - 1]
        print(f"  Please enter a number between 1 and {len(versions)}.")


def _clear_readonly_and_retry(func, path, _exc):
    """rmtree error handler: Windows refuses to delete read-only files (e.g. .git objects)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree(path):
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_clear_readonly_and_retry)
    else:
        shutil.rmtree(path, onerror=_clear_readonly_and_retry)


def deploy(source_dir, addons_dir, addon_name):
    """Copy source_dir into addons_dir/<addon_name>, replacing any existing copy."""
    dest = os.path.join(addons_dir, addon_name)

    if os.path.exists(dest):
        print(f"\nRemoving existing: {dest}")
        remove_tree(dest)

    print(f"Copying: {source_dir}")
    print(f"     to: {dest}")
    shutil.copytree(source_dir, dest)
    print("\nDone.")


def main():
    source_dirs = prompt_locale(find_addon_sources())

    for source_dir in source_dirs:
        print(f"Addon source : {source_dir}")
    print(f"WoW root     : {WOW_ROOT}")

    versions = discover_versions(WOW_ROOT)
    if not versions:
        print("ERROR: No WoW version folders with Interface/AddOns found.")
        sys.exit(1)

    folder, addons_dir, label = prompt_version(versions)

    print()
    for source_dir in source_dirs:
        print(f"Deploying   : {os.path.basename(source_dir)}  ({get_locale(source_dir)})")
    print(f"Deploying to: {label}  ({addons_dir})")
    confirm = input("Confirm? [y/N]: ").strip().lower()
    if confirm != "y":
        print("Aborted.")
        sys.exit(0)

    for source_dir in source_dirs:
        deploy(source_dir, addons_dir, os.path.basename(source_dir))


if __name__ == "__main__":
    main()
