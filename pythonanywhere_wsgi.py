import os
import sys

project_home = os.path.expanduser("~/CoCoPress")
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")
os.environ.setdefault("STANZA_RESOURCES_DIR", os.path.expanduser("~/stanza_resources"))

from app import app as application
