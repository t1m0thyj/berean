import os
import subprocess
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.path.realpath(__file__)))
load_dotenv()

subprocess.run(["python", os.path.join(os.environ["PYTHONPATH"], "Tools", "i18n", "pygettext.py"), "-p", "src/locale", "src"], cwd="..")
