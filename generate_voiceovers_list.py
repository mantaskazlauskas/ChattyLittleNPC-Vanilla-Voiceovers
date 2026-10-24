"""
Generate VoiceoversList.lua for each voiceover pack addon folder.

An addon folder is a subdirectory containing <same-name>.toc, one per locale:
    ChattyLittleNpc_Vanilla_enUS_voiceovers/   -> English
    ChattyLittleNpc_Vanilla_deDE_voiceovers/   -> German

Usage:
    python generate_voiceovers_list.py                 # every addon folder
    python generate_voiceovers_list.py <addon_folder>  # just that one
"""

import os
import sys

try:
    from mutagen.oggvorbis import OggVorbis
    from mutagen.mp3 import MP3
except ImportError:
    print("Error: mutagen library is required. Install it with: pip install mutagen")
    exit(1)


def get_audio_duration(file_path):
    """Get the duration of an audio file in seconds."""
    try:
        if file_path.lower().endswith('.ogg'):
            audio = OggVorbis(file_path)
        elif file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
        else:
            return None
        return round(audio.info.length, 2)
    except Exception as e:
        print(f"Warning: Could not read duration for {file_path}: {e}")
        return None


def find_addon_folders(root):
    """Return the addon folders under root, i.e. subdirectories containing <same-name>.toc."""
    folders = []
    for entry in sorted(os.listdir(root)):
        candidate = os.path.join(root, entry)
        if not os.path.isdir(candidate) or entry.startswith('.'):
            continue
        if os.path.isfile(os.path.join(candidate, f"{entry}.toc")):
            folders.append(candidate)
    return folders


def generate_voiceovers_lua_file(addon_folder):
    """Scan addon_folder/voiceovers for audio files and write addon_folder/VoiceoversList.lua."""
    addon_name = os.path.basename(os.path.abspath(addon_folder))
    folder_path = os.path.join(addon_folder, "voiceovers")
    output_file = os.path.join(addon_folder, "VoiceoversList.lua")

    if not os.path.isdir(folder_path):
        print(f"Warning: {folder_path} not found; {output_file} will be empty")

    voiceovers = []
    durations = {}
    
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.ogg') or file.endswith('.mp3'):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                # Use forward slashes for Lua compatibility
                lua_path = relative_path.replace(os.sep, '/')
                voiceovers.append(lua_path)
                
                duration = get_audio_duration(file_path)
                if duration is not None:
                    durations[lua_path] = duration
    
    # Sort for consistent output
    voiceovers.sort()
    
    with open(output_file, 'w') as lua_file:
        lua_file.write(f"---@class {addon_name}\n")
        lua_file.write(f"local {addon_name} = {{}}\n")
        lua_file.write(f"_G[\"{addon_name}\"] = {addon_name}\n\n")
        
        # Write Voiceovers list
        lua_file.write(f"{addon_name}.Voiceovers = {{\n")
        for path in voiceovers:
            lua_file.write(f"    '{path}',\n")
        lua_file.write("}\n\n")
        
        # Write VoiceoverDurations dictionary
        lua_file.write(f"{addon_name}.VoiceoverDurations = {{\n")
        for path in sorted(durations.keys()):
            lua_file.write(f'    ["{path}"] = {durations[path]},\n')
        lua_file.write("}\n")
    
    print(f"Generated {output_file} with {len(voiceovers)} voiceovers and {len(durations)} durations")


def main():
    if len(sys.argv) > 1:
        addon_folders = sys.argv[1:]
    else:
        addon_folders = find_addon_folders(os.path.dirname(os.path.abspath(__file__)))

    if not addon_folders:
        print("Error: no addon folders found (expected <Name>/<Name>.toc)")
        sys.exit(1)

    for addon_folder in addon_folders:
        generate_voiceovers_lua_file(addon_folder)


if __name__ == '__main__':
    main()