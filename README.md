# ChattyLittleNPC - Vanilla AI Voiceover Packs
AI-generated voiceover packs for the [ChattyLittleNPC](https://github.com/mantaskazlauskas/ChattyLittleNpc) addon, covering World of Warcraft: Classic (Vanilla) quests and NPC gossip. Each language is a separate pack you install alongside ChattyLittleNPC.

## For players

### Installing
English comes as two addons, because CurseForge limits how big one addon can be. Install both:

| Addon | Contains | CurseForge |
|---|---|---|
| `ChattyLittleNpc_Vanilla_enUS_voiceovers` | quests | [chatty-little-npc-vanilla](https://www.curseforge.com/wow/addons/chatty-little-npc-vanilla) |
| `ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers` | gossip, books, objects, quest greetings | [chatty-little-npc-classic-forever-books-and-gossip](https://www.curseforge.com/wow/addons/chatty-little-npc-classic-forever-books-and-gossip) |

1. Install ChattyLittleNPC.
2. Download the ZIPs for your language from the [Releases](https://github.com/mantaskazlauskas/ChattyLittleNPC-Vanilla-Voiceovers/releases) page, e.g. `ChattyLittleNpc_Vanilla_enUS_voiceovers-v3.4.0.zip` and `ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers-v1.0.0.zip`.
3. Extract them into `World of Warcraft/<version>/Interface/AddOns/`. You should end up with `Interface/AddOns/ChattyLittleNpc_Vanilla_enUS_voiceovers/` and `Interface/AddOns/ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers/`.

Up to 3.3.8 the English pack held everything. From 3.4.0 it only has the quests, so install the books & gossip addon too, or NPC gossip, books and objects go silent.

By default, ChattyLittleNPC plays voiceovers in your game client's language if a pack for it is installed, and English otherwise. When your language's pack has no recording for a line, it plays the English one. Install the English pack as well to get that fallback. You can pick the language and turn the fallback off in ChattyLittleNPC's settings.

### Upgrading from 3.3.4 or earlier
The English pack folder was renamed from `ChattyLittleNpc_Vanilla_voiceovers` to `ChattyLittleNpc_Vanilla_enUS_voiceovers`. **Delete the old `ChattyLittleNpc_Vanilla_voiceovers` folder** from `Interface/AddOns`. Otherwise both packs load, and the old one never gets updates.

---

## For maintainers

### Repository layout
Every top-level folder that contains a `.toc` with the same name is one addon. Each addon is one language, and a language can be split into a quest pack and a books & gossip pack to stay under CurseForge's size limit:

```
ChattyLittleNpc_Vanilla_enUS_voiceovers/          <- English quest pack
    ChattyLittleNpc_Vanilla_enUS_voiceovers.toc      version, title, file list
    VoiceoversList.lua                               GENERATED: the pack's global table, file list + durations
    voiceovers/                                      the .ogg files, directly in this folder
ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers/   <- English books & gossip pack, same structure
ChattyLittleNpc_Vanilla_deDE_voiceovers/          <- German pack (not split yet), same structure
split_voiceovers.py                            moves each audio file into the right pack of its language
generate_voiceovers_list.py                    builds VoiceoversList.lua for every pack
compress_voiceovers.py                         re-encodes a pack's audio smaller (needs ffmpeg)
deploy.py                                      copies packs into your local WoW install
release.py                                     tags and releases every pack whose version was bumped
pyproject.toml, uv.lock                        Python dependencies for the scripts, managed with uv
.github/workflows/release.yml                  builds the ZIP for the pack named by a published release's tag
```

The folder name matters. ChattyLittleNPC finds packs by the pattern `ChattyLittleNpc_<Expansion>_<locale>_voiceovers` (for the books & gossip pack, `<Expansion>` is `Vanilla_Gossip`) and reads the language from `<locale>`, which is a WoW client locale code: `enUS`, `deDE`, `frFR`, `esES`, `esMX`, `ptBR`, `itIT`, `ruRU`, `koKR`, `zhCN` or `zhTW`. The folder name and the `.toc` name must match exactly. The generator names the pack's global table after the folder.

### One-time setup
```powershell
uv sync      # creates .venv and installs mutagen, which the generator uses to read audio durations
```
- Python dependencies are declared in `pyproject.toml` and pinned in `uv.lock`. Install [uv](https://docs.astral.sh/uv/) first if you don't have it.
- `release.py` needs the [GitHub CLI](https://cli.github.com/), logged in with `gh auth login`.
- `deploy.py` copies to `WOW_ROOT`, set near the top of the script. It is currently the maintainer's own path (`D:\Games\World of Warcraft`). **Change it to the folder where World of Warcraft is installed on your machine** (the one containing `_retail_`, `_classic_era_` and so on) before running the script.
- Commits that change `.github/workflows/` can only be pushed with a token that has `workflow` scope. If a push is rejected with `refusing to allow an OAuth App to create or update workflow`, run `gh auth refresh -h github.com -s workflow` and then `gh auth setup-git`, and push again.

### Adding a new language
Example: German (`deDE`).

1. Create the folder `ChattyLittleNpc_Vanilla_deDE_voiceovers/`.
2. Copy the `.toc` from the English folder into it.
3. Rename the `.toc` to `ChattyLittleNpc_Vanilla_deDE_voiceovers.toc`.
4. In the `.toc`, change `## Title` to `Chatty Little NPC: Vanilla voiceovers (deDE)` so players can tell the packs apart in the AddOns list. Set `## Version` to the new pack's own version, e.g. `1.0.0`. Each pack is versioned and released separately.
5. Put the audio directly in `ChattyLittleNpc_Vanilla_deDE_voiceovers/voiceovers/`, with no subfolders. Use the same file names as the English pack, because ChattyLittleNPC looks voiceovers up by file name (see [File naming](#file-naming)).
6. Generate the file list (see the next section) and commit.

Nothing else needs to change. The generator, `deploy.py`, `release.py` and the release workflow all pick up the new folder automatically.

### File naming
Files must be `.ogg`. The generator also lists `.mp3` files, but ChattyLittleNPC only looks for `.ogg` names, so an `.mp3` never plays.

| Kind | File name |
|---|---|
| Quest text | `<questId>_Desc.ogg`, `<questId>_Prog.ogg`, `<questId>_Comp.ogg` (description, progress, completion) |
| Quest greeting | `<npcId>_QuestGreeting.ogg` |
| Gossip / game object / item | `<id>_Gossip_<hash>[_<Male\|Female\|Neutral>].ogg`, likewise `_GameObject_` and `_Item_`. The gender suffix is optional. |

Quest text files, `<questId>_<phase>.ogg` and `<questId>_<phase>_<npcId>.ogg`, go in the quest pack. Everything else goes in the books & gossip pack. ChattyLittleNPC looks a file up in every loaded pack, so the split only matters for download size.

### Adding or updating voiceovers
1. Add or replace `.ogg` files directly in the pack's `voiceovers/` folder (no subfolders). For a split language you can drop them into either pack and let the script sort them:
   ```powershell
   uv run split_voiceovers.py          # dry run for enUS: shows what would move
   uv run split_voiceovers.py --move   # moves quest files to the quest pack, everything else to books & gossip
   ```
2. Regenerate `VoiceoversList.lua`:
   ```powershell
   uv run generate_voiceovers_list.py                                         # every pack
   uv run generate_voiceovers_list.py ChattyLittleNpc_Vanilla_deDE_voiceovers  # one pack
   ```
   ChattyLittleNPC only knows about files listed here, so a file that isn't in the list never plays.
3. Bump `## Version` in the `.toc` of each pack that changed.

The release workflow regenerates the list too, so a stale committed list can't end up in a release. Regenerating locally is still needed for local testing.

### Shrinking a pack
CurseForge limits upload size, so keep packs in the English pack's format: mono, 22050 Hz Vorbis at about 30–35 kbps. TTS output at 44.1 kHz has practically nothing above 11 kHz, so re-encoding it halves its size with no audible loss. This needs [ffmpeg](https://ffmpeg.org/) on PATH (`winget install ffmpeg`).

```powershell
# Try it on 50 files first and listen to the results
uv run compress_voiceovers.py ChattyLittleNpc_Vanilla_deDE_voiceovers --output ../compressed_test --limit 50
# Replace the pack's files, then regenerate the list (durations change slightly)
uv run compress_voiceovers.py ChattyLittleNpc_Vanilla_deDE_voiceovers --in-place
uv run generate_voiceovers_list.py ChattyLittleNpc_Vanilla_deDE_voiceovers
```
Each file is checked before it replaces the original: it must decode, keep its duration and be smaller. Files already at 22050 Hz or lower are skipped, so it is safe to re-run. `--in-place` overwrites the originals, so keep a copy if the pack isn't committed yet. For a smaller result, `--sample-rate 16000` gives about 2.5× instead of 2×, but sounds noticeably duller. A lower `--quality` doesn't help at 22050 Hz.

### Testing in game
```powershell
uv run deploy.py
```
The script asks three things:
1. **Language:** which language to deploy. Every pack of that language is deployed, so English deploys both the quest pack and the books & gossip pack. Press Enter for `enUS`, pick a number for another language, or `a` for all of them. This step is skipped when there is only one language.
2. **WoW version:** Retail, Classic Era, Anniversary, and so on.
3. **Confirmation:** it lists the pack(s) and the target folder. Type `y` to go ahead.

It then replaces the pack's folder in that version's `Interface/AddOns`. Run `/reload` in game, or restart the client if you added new files.

### Releasing
**Only the repository owner (@mantaskazlauskas) publishes releases.** Contributors: open a pull request with your changes, and the owner will release them. What enforces this is write access: creating tags and releases needs it, and only the owner has it. As a safety net against accidental releases, the release workflow also skips building unless the owner published the release.

Each pack has its own version (`## Version` in its `.toc`) and its own GitHub release. A pack is only released when its version has no tag yet, so bumping a pack's version is what triggers its release.

| Pack | Tag | ZIP |
|---|---|---|
| English quests | `v<version>`, e.g. `v3.4.0` | `ChattyLittleNpc_Vanilla_enUS_voiceovers-v3.4.0.zip` |
| English books & gossip | `Gossip-enUS-v<version>`, e.g. `Gossip-enUS-v1.0.0` | `ChattyLittleNpc_Vanilla_Gossip_enUS_voiceovers-v1.0.0.zip` |
| Other languages | `<locale>-v<version>`, e.g. `deDE-v1.0.0` | `ChattyLittleNpc_Vanilla_deDE_voiceovers-v1.0.0.zip` |

Only releases of the English quest pack are marked as the repository's **Latest** release.

On CurseForge the two English packs are separate projects. Each one lists the other as a **Required Dependency** (under the project's Relations, or when uploading a file), so the CurseForge app installs both.

1. Bump `## Version` in the `.toc` of each pack that changed.
2. Commit and push to `main`.
3. Dry run to see which packs would be released:
   ```powershell
   python release.py
   ```
   Packs whose version already has a tag are listed as skipped.
4. Create the releases:
   ```powershell
   python release.py --create                       # every bumped pack
   python release.py --create --pack enUS           # only the English packs (quests and books & gossip)
   python release.py --create --pack Gossip-enUS    # only the English books & gossip pack
   python release.py --create --type beta           # tags get -beta (marked as a pre-release), e.g. deDE-v1.0.0-beta
   ```
   For each pack, this creates and pushes the git tag, then creates the GitHub release. Its notes only list changes since that pack's previous tag. To redo a version that already exists, first delete its GitHub release (e.g. `gh release delete deDE-v1.0.0`), then run with `--pack <pack key> --force`, e.g. `--pack deDE` or `--pack Gossip-enUS`. `--force` only replaces the tag, not the release.
5. The **Package WoW Addon** workflow runs once per release. It works out the pack from the tag, checks that the tag matches the pack's `## Version`, regenerates that pack's `VoiceoversList.lua`, and attaches its ZIP to the release. You can follow it in the repository's **Actions** tab.
