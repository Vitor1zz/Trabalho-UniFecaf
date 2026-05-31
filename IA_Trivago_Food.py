"""
Inicia o Trivago Food (encaminha para flask/run.py).
Mantido para compatibilidade com o comando antigo.
"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
FLASK_DIR = os.path.join(ROOT_DIR, "flask")

os.chdir(ROOT_DIR)
sys.path.insert(0, ROOT_DIR)

if FLASK_DIR in sys.path:
    sys.path.remove(FLASK_DIR)

sys.path.insert(0, FLASK_DIR)
from trivago_app import iniciar_servidor

if __name__ == "__main__":
    iniciar_servidor()
