from pathlib import Path

from environ import Env

CONFIG_DIR = Path(__file__).resolve().parent

BASE_DIR = CONFIG_DIR.parent

env = Env(
	DEBUG=(bool, False),
)
env.read_env(BASE_DIR.joinpath('.env'))
