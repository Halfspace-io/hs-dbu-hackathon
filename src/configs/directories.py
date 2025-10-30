from dataclasses import dataclass
from pathlib import Path


@dataclass
class Directories:
    """Class with all paths used in the repository."""

    REPO_PATH = Path(__file__).parent.parent.parent
    MODULE_PATH = Path(__file__).parent.parent
    DATA_PATH = REPO_PATH / "data"
    MENS_PATH = DATA_PATH / "H_EURO2024"
    WOMENS_PATH = DATA_PATH / "Q_EURO2025"
    U21_PATH = DATA_PATH / "U21_EURO2025"
