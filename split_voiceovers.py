"""
Sort a language's audio files between its two Vanilla packs.

CurseForge limits how big one addon file can be, so each language ships as two
addons that are installed together:

    ChattyLittleNpc_Vanilla_<locale>_voiceovers         quests
    ChattyLittleNpc_Vanilla_Gossip_<locale>_voiceovers  gossip, books (Item),
                                                        objects (GameObject),
                                                        quest greetings

A quest file is <questId>_<phase>.ogg or <questId>_<phase>_<npcId>.ogg, where
phase is Desc, Prog or Comp. Every other file belongs to the gossip pack.
ChattyLittleNPC looks voiceovers up by file name in every loaded pack, so which
pack holds a file only matters for the download size.

Drop new files into either pack's voiceovers/ folder, then run this to move each
file to the pack it belongs in. A file that already exists in the other pack is
left where it is and reported, never overwritten.

Usage:
    python split_voiceovers.py            # enUS, dry run: only prints what would move
    python split_voiceovers.py --move     # enUS, move the files
    python split_voiceovers.py deDE --move
Afterwards regenerate both packs' file lists:
    uv run generate_voiceovers_list.py ChattyLittleNpc_Vanilla_enUS_voiceovers ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers
"""

import argparse
import os
import re
import shutil
import sys

QUEST_FILE_RE = re.compile(r'^\d+_(Desc|Prog|Comp)(_\d+)?\.(ogg|mp3)$')
AUDIO_EXTENSIONS = ('.ogg', '.mp3')


def quest_pack(locale):
    return f"ChattyLittleNpc_Vanilla_{locale}_voiceovers"


def gossip_pack(locale):
    return f"ChattyLittleNpc_Vanilla_Gossip_{locale}_voiceovers"


def is_quest_file(file_name):
    return QUEST_FILE_RE.match(file_name) is not None


def audio_dir(root, pack):
    return os.path.join(root, pack, "voiceovers")


def misplaced_files(root, source_pack, target_pack, belongs_in_target):
    """Audio files in source_pack's voiceovers/ that belong in target_pack."""
    source = audio_dir(root, source_pack)
    if not os.path.isdir(source):
        return []
    return [
        (os.path.join(source, name), os.path.join(audio_dir(root, target_pack), name))
        for name in sorted(os.listdir(source))
        if name.lower().endswith(AUDIO_EXTENSIONS) and belongs_in_target(name)
    ]


def main():
    parser = argparse.ArgumentParser(description="Sort audio files between a language's quest and gossip packs.")
    parser.add_argument('locale', nargs='?', default='enUS', help='Pack locale, e.g. enUS (default) or deDE')
    parser.add_argument('--move', action='store_true', help='Move the files (default is a dry run)')
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    quests, gossip = quest_pack(args.locale), gossip_pack(args.locale)
    for pack in (quests, gossip):
        if not os.path.isfile(os.path.join(root, pack, f"{pack}.toc")):
            print(f"Error: {pack}/{pack}.toc not found. Both packs must exist before files can be sorted.")
            sys.exit(1)

    moves = (
        misplaced_files(root, quests, gossip, lambda name: not is_quest_file(name))
        + misplaced_files(root, gossip, quests, is_quest_file)
    )
    if not moves:
        print(f"Nothing to move: every {args.locale} file is already in the right pack.")
        return

    conflicts = [(src, dst) for src, dst in moves if os.path.exists(dst)]
    moves = [(src, dst) for src, dst in moves if not os.path.exists(dst)]

    to_gossip = sum(1 for src, _ in moves if os.path.dirname(os.path.dirname(src)).endswith(quests))
    print(f"{len(moves)} file(s) to move: {to_gossip} to {gossip}, {len(moves) - to_gossip} to {quests}")
    for src, dst in conflicts:
        print(f"  SKIPPED, already in the other pack: {os.path.relpath(src, root)}")

    if not args.move:
        print("Dry run. Run again with --move to move them.")
        return

    for src, dst in moves:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
    print(f"Moved {len(moves)} file(s). Now regenerate both file lists:")
    print(f"  uv run generate_voiceovers_list.py {quests} {gossip}")


if __name__ == '__main__':
    main()
