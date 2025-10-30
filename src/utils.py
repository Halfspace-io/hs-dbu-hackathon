from pathlib import Path
from typing import Iterable, Set
import pandas as pd


def _visible_children(p: Path) -> list[Path]:
    return sorted(
        [
            c
            for c in p.iterdir()
            if not c.name.startswith(".") and c.name != "__pycache__"
        ],
        key=lambda x: (not x.is_dir(), x.name.lower()),  # dirs first, then files
    )


def print_tree(path: Path, prefix: str = "", collapse_folders: Set[str] | None = None):
    """
    Pretty prints a directory tree, skipping hidden files and __pycache__,
    and collapsing 'game-like' subdirectories under specific parent folders.

    For each folder named in `collapse_folders`, it will:
      - Show ONE example subdirectory (fully expanded)
      - Then show a line like '... (N more games)' if there are more

    Args:
        path: Directory to print.
        prefix: Indentation prefix for recursive levels.
        collapse_folders: Folder names under which to collapse subfolders.
    """
    if collapse_folders is None:
        collapse_folders = {"H_EURO2024", "Q_EURO2025", "U21_EURO2025"}

    contents = _visible_children(path)
    if not contents:
        return

    pointers = ["├── "] * (len(contents) - 1) + ["└── "]
    for pointer, p in zip(pointers, contents):
        print(prefix + pointer + p.name)
        if p.is_dir():
            extension = "│   " if pointer == "├── " else "    "

            # Special handling for the collapse folders
            if p.name in collapse_folders:
                subitems = _visible_children(p)
                subdirs = [c for c in subitems if c.is_dir()]
                files = [c for c in subitems if not c.is_dir()]

                collapsed_items: list[tuple[str, Path | int]] = []

                if subdirs:
                    example_dir = subdirs[0]  # show the first game folder
                    collapsed_items.append(("example_dir", example_dir))
                    if len(subdirs) > 1:
                        collapsed_items.append(("ellipsis", len(subdirs) - 1))

                # Also list any files directly under the collapse folder (rare, but supported)
                for f in files:
                    collapsed_items.append(("file", f))

                if collapsed_items:
                    inner_pointers = ["├── "] * (len(collapsed_items) - 1) + ["└── "]
                    for inner_ptr, (kind, obj) in zip(inner_pointers, collapsed_items):
                        line_prefix = prefix + extension
                        if kind == "example_dir":
                            ex: Path = obj  # type: ignore
                            print(line_prefix + inner_ptr + ex.name + "/")
                            # Recurse into the example directory to show its contents fully
                            inner_extension = "│   " if inner_ptr == "├── " else "    "
                            print_tree(
                                ex, line_prefix + inner_extension, collapse_folders
                            )
                        elif kind == "ellipsis":
                            more_count: int = obj  # type: ignore
                            print(
                                line_prefix
                                + inner_ptr
                                + f"... ({more_count} more games)"
                            )
                        elif kind == "file":
                            f: Path = obj  # type: ignore
                            print(line_prefix + inner_ptr + f.name)
                else:
                    # No visible children inside the collapse folder
                    print(prefix + extension + "└── (empty)")
            else:
                # Normal recursion for non-collapsed folders
                print_tree(p, prefix + extension, collapse_folders)


def matchPeriod_to_half(matchPeriod: str):
    """
    Convert match period string to half number.
    E.g., '1H' -> 1, '2H' -> 2, '1ET' -> 3, 'PEN' -> 4
    """
    mapping = {
        "1H": 1,
        "2H": 2,
        "1E": 3,
        "2E": 4,
        "P": 5,
    }
    return mapping.get(matchPeriod, None)


def convert_HHMMSS_to_secs(HHMMSS: str) -> int:

    first_half_offset_parts = HHMMSS.split(":")

    first_half_offset = (
        int(first_half_offset_parts[0]) * 60 * 60
        + int(first_half_offset_parts[1]) * 60
        + float(first_half_offset_parts[2])
    )

    return first_half_offset


def extract_half_and_time_passed_in_half(event: pd.Series):
    # convert matchPeriod string to half
    half = matchPeriod_to_half(event["matchPeriod"])

    # make sure we're subtracting the half offset (ie second half starts at 45:00, third half at 90:00, fourth half at 105:00)
    minute_offset = 45 if half == 2 else 90 if half == 3 else 105 if half == 4 else 0

    # compute actual time passed in half by convert the HH:MM:SS timestamp to seconds and subtracting the minute offset
    time_passed_in_half = (
        convert_HHMMSS_to_secs(event["matchTimestamp"]) - minute_offset * 60
    )

    return half, time_passed_in_half


def _timestamp_helper(half, time, tracking, time_column="time_passed_in_half"):
    """
    Helper function to find the closest tracking row for a given half and time.
    """
    # Filter tracking DataFrame for the specific half
    half_tracking = tracking[tracking["half"] == half]
    if half_tracking.empty:
        raise ValueError("No tracking data for the specified half.")

    # Find the closest timestamp
    closest_idx = (half_tracking["time_passed_in_half"] - time).abs().idxmin()
    return half_tracking.loc[closest_idx][time_column]


def plot_tracking(
    home,
    away,
    half,
    time,
    time_column="time_passed_in_half",
    home_color="red",
    away_color="blue",
    home_label="Home",
    away_label="Away",
):
    import mplsoccer
    import matplotlib.pyplot as plt

    # Initialize the pitch with dimensions 105 x 68
    pitch = mplsoccer.Pitch(
        pitch_type="skillcorner",
        pitch_length=105,
        pitch_width=68,
    )  # axis=True,label=True)
    fig, ax = pitch.draw(figsize=(10, 7))

    closest_timestamp = _timestamp_helper(half, time, home, time_column)

    for side, team, col in zip(
        ["home", "away"], [home, away], [home_color, away_color]
    ):
        # Get x and y columns for each team
        x_columns = [c for c in team.keys() if c[-2:].lower() == "_x" and c != "ball_x"]
        y_columns = [c for c in team.keys() if c[-2:].lower() == "_y" and c != "ball_y"]

        for i, (x_col, y_col) in enumerate(zip(x_columns, y_columns)):
            pitch.scatter(
                team[(team["half"] == half) & (team[time_column] == closest_timestamp)][
                    x_col
                ],
                team[(team["half"] == half) & (team[time_column] == closest_timestamp)][
                    y_col
                ],
                s=100,
                color=col,
                edgecolors="k",
                ax=ax,
                label=side if i == 0 else None,  # Only label first player
            )

        # plot the ball
        pitch.scatter(
            team[(team["half"] == half) & (team[time_column] == closest_timestamp)][
                "ball_x"
            ],
            team[(team["half"] == half) & (team[time_column] == closest_timestamp)][
                "ball_y"
            ],
            ax=ax,
            color="black",
        )

        player_nums = [
            c.split("_")[1]
            for c in team.keys()
            if c[-2:].lower() == "_x" and c != "ball_x"
        ]

        player_xs = team[
            (team["half"] == half) & (team[time_column] == closest_timestamp)
        ][x_columns].values.flatten()
        player_ys = team[
            (team["half"] == half) & (team[time_column] == closest_timestamp)
        ][y_columns].values.flatten()

        for i, txt in enumerate(player_nums):
            a = ax.annotate(
                txt,
                (player_xs[i], player_ys[i]),
                ha="center",
                va="center",
                c="white",
                fontsize="x-small",
                fontweight="bold",
            )

    ax.annotate(
        home_label,
        (-4, 35),  # Place it outside the pitch on the left
        ha="center",
        va="bottom",
        c=home_color,
        fontsize="large",
        fontweight="bold",
    )

    ax.annotate(
        "",
        xy=(-2, 34.5),  # Arrow end
        xytext=(-6, 34.5),  # Arrow start
        arrowprops=dict(arrowstyle="->", color=home_color, lw=2),
    )

    ax.annotate(
        away_label,
        (4, 35),  # Place it outside the pitch on the right
        ha="center",
        va="bottom",
        c=away_color,
        fontsize="large",
        fontweight="bold",
    )

    ax.annotate(
        "",
        xy=(2, 34.5),  # Arrow end
        xytext=(6, 34.5),  # Arrow start
        arrowprops=dict(arrowstyle="->", color=away_color, lw=2),
    )

    # Add legend and display plot
    # ax.legend(["Home Team", "Away Team"], loc="upper right")
    # ax.legend()
    plt.show()
