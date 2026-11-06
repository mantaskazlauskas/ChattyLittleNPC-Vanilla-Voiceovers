# ChattyLittleNPC - Vanilla AI Voiceover Packs
AI-generated voiceover packs for the [ChattyLittleNPC](https://github.com/mantaskazlauskas/ChattyLittleNpc) addon, covering World of Warcraft: Classic (Vanilla) quests and NPC gossip. Each language is a separate pack you install alongside ChattyLittleNPC.

## For players

### Installing
1. Install ChattyLittleNPC.
2. Download the ZIP for your language from the [Releases](https://github.com/mantaskazlauskas/ChattyLittleNPC-Vanilla-Voiceovers/releases) page, e.g. `ChattyLittleNpc_Vanilla_enUS_voiceovers-v3.3.5.zip`.
3. Extract it into `World of Warcraft/<version>/Interface/AddOns/`. You should end up with `Interface/AddOns/ChattyLittleNpc_Vanilla_enUS_voiceovers/`.

By default, ChattyLittleNPC plays voiceovers in your game client's language if a pack for it is installed, and English otherwise. When your language's pack has no recording for a line, it plays the English one. Install the English pack as well to get that fallback. You can pick the language and turn the fallback off in ChattyLittleNPC's settings.

### Upgrading from 3.3.4 or earlier
The English pack folder was renamed from `ChattyLittleNpc_Vanilla_voiceovers` to `ChattyLittleNpc_Vanilla_enUS_voiceovers`. **Delete the old `ChattyLittleNpc_Vanilla_voiceovers` folder** from `Interface/AddOns`. Otherwise both packs load, and the old one never gets updates.

---

## For maintainers

### Repository layout
Every top-level folder that contains a `.toc` with the same name is one addon, and each addon is one language:

```
ChattyLittleNpc_Vanilla_enUS_voiceovers/       <- English pack
    ChattyLittleNpc_Vanilla_enUS_voiceovers.toc   version, title, file list
    VoiceoversList.lua                            GENERATED: the pack's global table, file list + durations
    voiceovers/                                   the .ogg files, directly in this folder
ChattyLittleNpc_Vanilla_deDE_voiceovers/       <- e.g. a German pack, same structure
generate_voiceovers_list.py                    builds VoiceoversList.lua for every pack
compress_voiceovers.py                         re-encodes a pack's audio smaller (needs ffmpeg)
deploy.py                                      copies packs into your local WoW install
release.py                                     tags and releases every pack whose version was bumped
pyproject.toml, uv.lock                        Python dependencies for the scripts, managed with uv
.github/workflows/release.yml                  builds the ZIP for the pack named by a published release's tag
```

The folder name matters. ChattyLittleNPC finds packs by the pattern `ChattyLittleNpc_<Expansion>_<locale>_voiceovers` and reads the language from `<locale>`, which is a WoW client locale code: `enUS`, `deDE`, `frFR`, `esES`, `esMX`, `ptBR`, `itIT`, `ruRU`, `koKR`, `zhCN` or `zhTW`. The folder name and the `.toc` name must match exactly. The generator names the pack's global table after the folder.

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

### Adding or updating voiceovers
1. Add or replace `.ogg` files directly in the pack's `voiceovers/` folder (no subfolders).
2. Regenerate `VoiceoversList.lua`:
   ```powershell
   uv run generate_voiceovers_list.py                                         # every pack
   uv run generate_voiceovers_list.py ChattyLittleNpc_Vanilla_deDE_voiceovers  # one pack
   ```
   ChattyLittleNPC only knows about files listed here, so a file that isn't in the list never plays.
3. Bump `## Version` in that pack's `.toc`.

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
1. **Language:** which pack to deploy. Press Enter for `enUS`, pick a number for another language, or `a` for all of them. This step is skipped when there is only one pack.
2. **WoW version:** Retail, Classic Era, Anniversary, and so on.
3. **Confirmation:** it lists the pack(s) and the target folder. Type `y` to go ahead.

It then replaces the pack's folder in that version's `Interface/AddOns`. Run `/reload` in game, or restart the client if you added new files.

### Releasing
**Only the repository owner (@mantaskazlauskas) publishes releases.** Contributors: open a pull request with your changes, and the owner will release them. What enforces this is write access: creating tags and releases needs it, and only the owner has it. As a safety net against accidental releases, the release workflow also skips building unless the owner published the release.

Each pack has its own version (`## Version` in its `.toc`) and its own GitHub release. A pack is only released when its version has no tag yet, so bumping a pack's version is what triggers its release.

| Pack | Tag | ZIP |
|---|---|---|
| English | `v<version>`, e.g. `v3.3.6` | `ChattyLittleNpc_Vanilla_enUS_voiceovers-v3.3.6.zip` |
| Other languages | `<locale>-v<version>`, e.g. `deDE-v1.0.0` | `ChattyLittleNpc_Vanilla_deDE_voiceovers-v1.0.0.zip` |

Only English releases are marked as the repository's **Latest** release.

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
   python release.py --create --pack deDE           # only the German pack
   python release.py --create --type beta           # tags get -beta (marked as a pre-release), e.g. deDE-v1.0.0-beta
   ```
   For each pack, this creates and pushes the git tag, then creates the GitHub release. Its notes only list changes since that pack's previous tag. To redo a version that already exists, first delete its GitHub release (e.g. `gh release delete deDE-v1.0.0`), then run with `--pack <locale> --force`. `--force` only replaces the tag, not the release.
5. The **Package WoW Addon** workflow runs once per release. It works out the pack from the tag, checks that the tag matches the pack's `## Version`, regenerates that pack's `VoiceoversList.lua`, and attaches its ZIP to the release. You can follow it in the repository's **Actions** tab.
