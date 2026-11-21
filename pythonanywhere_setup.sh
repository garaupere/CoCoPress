#!/bin/bash
set -e

cd "$HOME/CoCoPress"

python3.11 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p "$HOME/stanza_resources"
python -c "import stanza; stanza.download('ca', model_dir='$HOME/stanza_resources', verbose=False)"
