import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point


def plot_map(df, column, colors=None, filename=None, alongside=True):
    map = gpd.GeoSeries([Point(v) for v in df[["longitude", "latitude"]].values])

    # Define plot configurations
    plot_config = [
        {"title": "Pentad - Full View", "xlim": None, "ylim": None, "s": 0.01},
        {
            "title": "Pentad - Scaled View",
            "xlim": [15.5, 33.5],
            "ylim": [-36, -20.5],
            "s": 2,
        },
    ]

    # Configure plots
    for i, config in enumerate(plot_config):
        fig, ax = plt.subplots(figsize=(15, 8))

        map.plot(color="lightgrey", ax=ax)

        x = df["longitude"]
        y = df["latitude"]
        z = df[column]

        if colors is not None:
            ax.scatter(x, y, c=colors, s=config["s"], marker="s")
        else:
            sc = ax.scatter(x, y, c=z, s=config["s"], marker="s")
            fig.colorbar(sc, ax=ax, label=column)

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(config["title"])

        if config["xlim"]:
            ax.set_xlim(config["xlim"])

        if config["ylim"]:
            ax.set_ylim(config["ylim"])

        # Save and/or display plots
        if filename:
            if alongside and i == 0:
                plt.close(fig)  # Close the figure to free up memory
                continue
            else:
                suffix = "_africa" if i == 0 else "_cropped"
                fig.savefig(f"output/maps/{filename}{suffix}.png", dpi=1000)
                plt.close(fig)  # Close the figure to free up memory

        if not alongside:
            plt.show()
            plt.close(fig)  # Close the figure to free up memory

    if alongside:
        plt.show()
