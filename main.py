import os
from load_file import stored_file_path, stored_file_path2
import buildersmart
import mahendra
import kglite
import jindal
import jswneo
import mahadev
import mccomart
import mahendra

file_path1 = stored_file_path
file_path2 = stored_file_path2


#delete paths if exists
if os.path.exists(file_path1):
    os.remove(file_path1)

if os.path.exists(file_path2):
    os.remove(file_path2)

modules = [
    buildersmart,
    mahendra,
    kglite,
    jindal,
    jswneo,
    mahadev,
    mccomart,
    # shermoham
]

# Run the main function of each module
for module in modules:
    try:
        print(f"Running main function of: {module.__name__}")
        module.main()  
    except AttributeError:
        print(f"The module {module.__name__} does not have a main() function.")
    except Exception as e:
        print(f"Unexpected error in {module.__name__}: {e}")
