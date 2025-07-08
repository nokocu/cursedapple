import os
import re

# dictionary
replacement_dict = {
    "medic shot": "restorative shot",
    "surgeof power": "surge of power",
    "enchanters barrier": "enchanter's barrier",
    "diviners kevlar": "diviner's kevlar",
    "health nova": "healing nova",
    "head hunter": "headhunter",
    "quick silver reload": "quicksilver reload",
}


def rename_files_in_directory(root_dir):
    # walk through each folder subfolder and file
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            # check if the file is a .png file
            if filename.endswith(".png"):
                # remove the file extension for processing
                file_base_name = filename[:-4]

                # split words at uppercase letters and join with a space then convert to lowercase
                new_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', file_base_name).lower()

                # replace multiple spaces with a single space
                new_name = re.sub(r'\s+', ' ', new_name)

                # check for any dictionary-based replacements
                for key, value in replacement_dict.items():
                    new_name = new_name.replace(key.lower(), value.lower())

                # add the .png extension back to the new name
                new_name += ".png"

                # create full paths for the old and new file names
                old_file = os.path.join(dirpath, filename)
                new_file = os.path.join(dirpath, new_name)

                # pnly proceed if the new name is different from the old name
                if old_file != new_file:
                    # show the old and new file name and ask for confirmation
                    print(f"Renaming '{old_file}' to '{new_file}'")
                    input("Press Enter to proceed with this renaming, or Ctrl+C to cancel...")

                    os.rename(old_file, new_file)


dir = 'D:/python/cursedapple/static/assets/game/icons'
# dir = 'D:/python/cursedapple/static/assets/game/portraits'


rename_files_in_directory(dir)
print("done")
