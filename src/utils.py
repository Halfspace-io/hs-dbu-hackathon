from pathlib import Path
import pandas as pd






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


def convert_HHMMSS_to_secs(HHMMSS: str) -> float:

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
    home: pd.DataFrame,
    away: pd.DataFrame,
    half: int,
    time: float,
    time_column: str = "time_passed_in_half",
    home_color: str = "red",
    away_color: str = "blue",
    home_label: str = "Home",
    away_label: str = "Away",
) -> None:
    """
    Plot tracking data for both teams on a football pitch.
    
    Args:
        home: DataFrame containing home team tracking data with player positions and ball position
        away: DataFrame containing away team tracking data with player positions and ball position  
        half: Match half number (1, 2, 3, 4, etc.)
        time: Time passed in the specified half (in seconds)
        time_column: Column name for time data in tracking DataFrames
        home_color: Color for home team players on the plot
        away_color: Color for away team players on the plot
        home_label: Label text for home team
        away_label: Label text for away team
        
    Returns:
        None: Displays the plot using matplotlib
        
    Note:
        Tracking DataFrames should contain columns like 'player_1_x', 'player_1_y', 
        'ball_x', 'ball_y', 'half', and the specified time_column.
    """
    import mplsoccer
    import matplotlib.pyplot as plt
    from typing import Any

    # Initialize the pitch with dimensions 105 x 68
    pitch = mplsoccer.Pitch(
        pitch_type="skillcorner",
        pitch_length=105,
        pitch_width=68,
    )  # axis=True,label=True)
    fig, ax = pitch.draw(figsize=(10, 7))  # type: ignore

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
            a = ax.annotate(  # type: ignore
                txt,
                (player_xs[i], player_ys[i]),
                ha="center",
                va="center",
                c="white",
                fontsize="x-small",
                fontweight="bold",
            )

    ax.annotate(  # type: ignore
        home_label,
        (-4, 35),  # Place it outside the pitch on the left
        ha="center",
        va="bottom",
        c=home_color,
        fontsize="large",
        fontweight="bold",
    )

    ax.annotate(  # type: ignore
        "",
        xy=(-2, 34.5),  # Arrow end
        xytext=(-6, 34.5),  # Arrow start
        arrowprops=dict(arrowstyle="->", color=home_color, lw=2),
    )

    ax.annotate(  # type: ignore
        away_label,
        (4, 35),  # Place it outside the pitch on the right
        ha="center",
        va="bottom",
        c=away_color,
        fontsize="large",
        fontweight="bold",
    )

    ax.annotate(  # type: ignore
        "",
        xy=(2, 34.5),  # Arrow end
        xytext=(6, 34.5),  # Arrow start
        arrowprops=dict(arrowstyle="->", color=away_color, lw=2),
    )

    # Add legend and display plot
    # ax.legend(["Home Team", "Away Team"], loc="upper right")
    # ax.legend()
    plt.show()
