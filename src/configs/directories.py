from dataclasses import dataclass
from pathlib import Path

@dataclass
class Directories:
    """Class with all paths used in the repository."""

    REPO_PATH = Path(__file__).parent.parent.parent
    MODULE_PATH = Path(__file__).parent.parent
    DATA_PATH = REPO_PATH / "data"

