import os
import re

# Define a dictionary for custom replacements
replacement_dict = {
    "medic shot": "restorative shot",
    "surgeof power": "surge of power",

    # "bull": "abrams",
    # "nano": "calico",
    # "sumo": "dynamo",
    # "archer": "grey talon",
    # "astro": "holliday",
    # "inferno": "infernus",
    # "tengu": "ivy",
    # "spectre": "lady geist",
    # "engineer": "mcginnis",
    # "digger": "mo & krill",
    # "chrono": "paradox",
    # "synth": "pocket",
    # "gigawatt": "seven",
    # "hornet": "vindicta",

}


def rename_files_in_directory(root_dir):
    # Walk through each folder, subfolder, and file in the directory
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            # Check if the file is a .png file
            if filename.endswith(".png"):
                # Remove the file extension for processing
                file_base_name = filename[:-4]

                # Split words at uppercase letters and join with a space, then convert to lowercase
                new_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', file_base_name).lower()

                # Replace multiple spaces with a single space
                new_name = re.sub(r'\s+', ' ', new_name)

                # Check for any dictionary-based replacements
                for key, value in replacement_dict.items():

                    new_name = new_name.replace(key.lower(), value.lower())

                # Add the .png extension back to the new name
                new_name += ".png"

                # Create full paths for the old and new file names
                old_file = os.path.join(dirpath, filename)
                new_file = os.path.join(dirpath, new_name)

                # Only proceed if the new name is different from the old name
                if old_file != new_file:
                    # Show the old and new file name, and ask for confirmation
                    print(f"Renaming '{old_file}' to '{new_file}'")
                    input("Press Enter to proceed with this renaming, or Ctrl+C to cancel...")

                    # Perform the renaming
                    os.rename(old_file, new_file)


# Specify the directory where you want to rename the files
dir = 'D:/python/cursedapple/static/assets/game/icons/weapon'
# dir = 'D:/python/cursedapple/static/assets/game/icons/spirit'
# dir = 'D:/python/cursedapple/static/assets/game/icons/vitality'
# dir = 'D:/python/cursedapple/static/assets/game/portraits'

rename_files_in_directory(dir)
print("done")
