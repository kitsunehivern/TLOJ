import os
import shutil

shutil.rmtree("Contestants", ignore_errors=True)
shutil.rmtree("Submissions", ignore_errors=True)
shutil.rmtree("Moss", ignore_errors=True)
os.mkdir("Contestants")
os.mkdir("Submissions")
