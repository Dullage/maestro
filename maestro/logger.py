import logging
from os import sys

log = logging.getLogger()
log.setLevel("INFO")
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s]: %(message)s", "%Y-%m-%d %H:%M:%S"
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)
log.addHandler(handler)
