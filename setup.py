import os
import sys
import shutil
from setuptools import setup

setup(
    name = "trainconfig",
    version = "0.0.1",
    author = "Dmytro Levin",
    author_email = "dmtlevin@gmail.com",
    packages = ["trainconfig"],
    install_requires = [
        "PyYAML>=5.3.1",
        "streamlit==1.7.0",
        "click==7.1.2",
        "dotdict @ https://github.com/dmtlvn/dotdict/archive/refs/heads/main.zip",
    ],
    url = "https://github.com/dmtlvn/trainconfig",
    license = "MIT License",
    description = "Reproducible NN training pipeline controller",
    zip_safe = True,
)

# REGISTER BASH COMMAND
BASH_CMD = """FILE=$(python -c "import sysconfig; print(sysconfig.get_paths()['purelib'] + '/trainconfig/frontend.py')")
streamlit run $FILE --server.headless=True --server.port=${1:-8501} --server.runOnSave=True\n"""

BIN_PATH, _ = os.path.split(sys.executable)
CMD_PATH = os.path.join(BIN_PATH, 'trainconfig')
with open(CMD_PATH, 'w') as file:
    file.write(BASH_CMD)
os.chmod(CMD_PATH, mode = 0o775)

# CLEAN UP
TMP_DIR = os.path.expanduser("~/.train_config")
if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)
