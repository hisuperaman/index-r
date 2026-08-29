import logging
from pathlib import Path

from environ import Env

CONFIG_DIR = Path(__file__).resolve().parent

BASE_DIR = CONFIG_DIR.parent

try:
	LOG_DIR = Path('/var/log/indexr')
	LOG_DIR.mkdir(exist_ok=True)
except PermissionError as e:
	logging.error(f"Permission denied: {e}")
	LOG_DIR = Path.home() / 'logs' / 'indexr'
	logging.info(f'Using home directory for logs {LOG_DIR}')
	LOG_DIR.mkdir(exist_ok=True, parents=True)

env = Env(
	DEBUG=(bool, False),
)
env.read_env(BASE_DIR.joinpath('.env'))
