#!/usr/bin/env python3
"""
Release script for ChattyLittleNpc voiceover packs.

Every addon folder has its own ## Version and its own release. A language ships as
two packs, quests and gossip (see split_voiceovers.py), so a pack is named by its
key: the locale for a quest pack, <Part>-<locale> for the others.
    enUS quest pack -> tag v<version>                e.g. v3.3.6        (continues the existing tag history)
    other quests    -> tag <locale>-v<version>       e.g. deDE-v1.0.0
    gossip packs    -> tag <Part>-<locale>-v<version> e.g. Gossip-enUS-v1.0.0
A pack whose tag already exists has not been bumped and is skipped, so only packs
with a new version get a release. The release workflow then builds the ZIP for
the pack named by the tag.

Usage:
    python release.py                                # Dry run - shows what would be released
    python release.py --create                       # Release every pack whose version was bumped
    python release.py --create --pack enUS           # Only the English packs (quests and gossip)
    python release.py --create --pack Gossip-enUS    # Only the English gossip pack
    python release.py --create --type beta           # Tags get a -beta suffix (pre-release)
    python release.py --create --pack deDE --force   # Recreate an existing tag
"""

import argparse
import os
import re
import subprocess
import sys


# Packs are named ChattyLittleNpc_Vanilla_[<Part>_]<locale>_voiceovers: no part for the
# quest pack, e.g. Gossip for the books & gossip pack. A pack without a locale is English
# (legacy naming).
PACK_RE = re.compile(r'^ChattyLittleNpc_Vanilla_(?:(?P<part>[A-Za-z]+)_)?(?P<locale>[a-z]{2}[A-Z]{2})_voiceovers$')
DEFAULT_LOCALE = 'enUS'


def find_addon_folders(root):
    """Subdirectories of root containing <same-name>.toc, i.e. one per pack."""
    folders = []
    for entry in sorted(os.listdir(root)):
        candidate = os.path.join(root, entry)
        if os.path.isdir(candidate) and not entry.startswith('.') \
                and os.path.isfile(os.path.join(candidate, f"{entry}.toc")):
            folders.append(candidate)
    return folders


def get_locale(addon_name):
    match = PACK_RE.match(addon_name)
    return match.group('locale') if match else DEFAULT_LOCALE


def get_pack_key(addon_name):
    """deDE for a quest pack, Gossip-enUS for a gossip pack."""
    match = PACK_RE.match(addon_name)
    part = match.group('part') if match else None
    locale = get_locale(addon_name)
    return f"{part}-{locale}" if part else locale


def get_version_from_toc(toc_path):
    with open(toc_path, 'r', encoding='utf-8') as f:
        match = re.search(r'^## Version:\s*(.+)$', f.read(), re.MULTILINE)
    return match.group(1).strip() if match else None


def tag_prefix_for(pack_key):
    """The English quest pack keeps the plain v<version> tags it always had; other packs are prefixed."""
    return 'v' if pack_key == DEFAULT_LOCALE else f'{pack_key}-v'


def run_command(cmd, check=True):
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=check)


def check_gh_cli():
    try:
        subprocess.run(['gh', '--version'], capture_output=True, check=True)
        subprocess.run(['gh', 'auth', 'status'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def list_tags(pattern):
    result = subprocess.run(['git', 'tag', '-l', pattern, '--sort=-v:refname'],
                            capture_output=True, text=True, check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def tag_exists(tag_name):
    return tag_name in list_tags(tag_name)


def previous_tag(prefix, current):
    """Newest existing tag of the same pack, so generated release notes only cover that pack."""
    pattern = re.compile(rf'^{re.escape(prefix)}\d')
    for tag in list_tags(f'{prefix}*'):
        if tag != current and pattern.match(tag):
            return tag
    return None


def main():
    parser = argparse.ArgumentParser(description='Create one release per voiceover pack whose .toc version was bumped')
    parser.add_argument('--create', action='store_true', help='Actually create tags and releases (default is dry run)')
    parser.add_argument('--pack', action='append', metavar='KEY',
                        help='Only consider these packs: a locale (every pack of that language, e.g. enUS) '
                             'or one pack key (e.g. Gossip-enUS). Repeatable. Default: all packs.')
    parser.add_argument('--force', action='store_true',
                        help='Delete and recreate tags that already exist (requires --pack; '
                             'each --pack is then an exact pack key, e.g. enUS is only the quest pack)')
    parser.add_argument('--type', dest='release_type', choices=['release', 'beta', 'alpha'], default='release',
                        help='Release type: release (default), beta, or alpha. Appends -beta/-alpha suffix to tags.')
    args = parser.parse_args()

    if args.force and not args.pack:
        print("Error: --force needs --pack, so existing releases of other packs are not recreated by accident")
        sys.exit(1)

    root = os.path.dirname(os.path.abspath(__file__))
    folders = find_addon_folders(root)
    if not folders:
        print("Error: no addon folders found (expected <Name>/<Name>.toc)")
        sys.exit(1)

    names = [os.path.basename(f) for f in folders]
    known = {get_locale(n) for n in names} | {get_pack_key(n) for n in names}
    for key in args.pack or []:
        if key not in known:
            print(f"Error: no pack {key}. Available: {', '.join(sorted(known))}")
            sys.exit(1)

    # Make sure tags created elsewhere are known, so an already released version is not released again.
    subprocess.run(['git', 'fetch', '--tags', '--quiet', 'origin'], check=False)

    tag_suffix = f"-{args.release_type}" if args.release_type != 'release' else ''
    to_release = []
    for folder in folders:
        addon_name = os.path.basename(folder)
        locale = get_locale(addon_name)
        pack_key = get_pack_key(addon_name)
        # A locale selects every pack of that language, except with --force: recreating a tag
        # is for one pack, so there --pack enUS means the enUS quest pack only, not Gossip-enUS.
        if args.pack and pack_key not in args.pack and (args.force or locale not in args.pack):
            continue

        version = get_version_from_toc(os.path.join(folder, f"{addon_name}.toc"))
        if not version:
            print(f"Error: {addon_name}.toc has no ## Version line")
            sys.exit(1)

        prefix = tag_prefix_for(pack_key)
        tag_name = f"{prefix}{version}{tag_suffix}"
        exists = tag_exists(tag_name)
        # A full release of this version means it was not bumped, so a beta/alpha of it is skipped too.
        # (A beta can still be promoted: the plain tag does not exist yet.)
        released = exists or tag_exists(f"{prefix}{version}")
        if released and not args.force:
            print(f"  {pack_key}  {addon_name} {version}: already released - version not bumped, skipping")
            continue

        dirty = subprocess.run(['git', 'status', '--porcelain', '--', folder],
                               capture_output=True, text=True, check=True).stdout.strip()
        if dirty and args.create:
            print(f"Error: {addon_name} has uncommitted changes. The tag would point at a commit without them;")
            print("       commit and push first.")
            sys.exit(1)

        status = "exists - will be recreated (--force)" if exists else "new"
        print(f"  {pack_key}  {addon_name} {version}: tag {tag_name} {status}")
        to_release.append((addon_name, pack_key, version, prefix, tag_name, exists))

    print()
    if not to_release:
        print("Nothing to release. Bump ## Version in a pack's .toc to release it.")
        return

    if not check_gh_cli():
        print("Error: GitHub CLI (gh) is not installed or not authenticated")
        print("Install: https://cli.github.com/")
        print("Authenticate: gh auth login")
        sys.exit(1)

    for addon_name, pack_key, version, prefix, tag_name, exists in to_release:
        gh_cmd = ['gh', 'release', 'create', tag_name,
                  '--title', f"{addon_name} {version}",
                  '--generate-notes']
        start_tag = previous_tag(prefix, tag_name)
        if start_tag:
            gh_cmd += ['--notes-start-tag', start_tag]
        if args.release_type != 'release':
            gh_cmd.append('--prerelease')
        # Only a full release of the English quest pack becomes the repository's "Latest" release.
        is_latest = pack_key == DEFAULT_LOCALE and not tag_suffix
        gh_cmd.append(f"--latest={'true' if is_latest else 'false'}")

        if not args.create:
            print(f"Would release {addon_name} {version}:")
            if exists:
                print(f"  git tag -d {tag_name}")
                print(f"  git push origin --delete {tag_name}")
            print(f"  git tag {tag_name}")
            print(f"  git push origin {tag_name}")
            print(f"  {' '.join(gh_cmd)}")
            print()
            continue

        print(f"Releasing {addon_name} {version} as {tag_name}...")
        if exists:
            run_command(['git', 'tag', '-d', tag_name])
            run_command(['git', 'push', 'origin', '--delete', tag_name], check=False)
        run_command(['git', 'tag', tag_name])
        run_command(['git', 'push', 'origin', tag_name])
        try:
            run_command(gh_cmd)
        except subprocess.CalledProcessError:
            print(f"Error: tag {tag_name} was pushed but creating the release failed.")
            print(f"       Rerun with: python release.py --create --pack {pack_key} --force")
            sys.exit(1)
        print()

    if not args.create:
        print("DRY RUN - use --create to actually create the tags and releases")
    else:
        print("Done! The GitHub Actions workflow will now build and attach each pack's ZIP to its release.")


if __name__ == '__main__':
    main()
