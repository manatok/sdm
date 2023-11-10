import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# axes[1].set_xlim([15.5, 33.5])
# axes[1].set_ylim([-36, -20.5])


def plot_map(df, column, colors=None, filename=None, alongside=True):
    map = gpd.GeoSeries([Point(v) for v in df[["longitude", "latitude"]].values])

    # Define plot configurations
    plot_config = [
        {"title": "Pentad - Full View", "xlim": None, "ylim": None},
        {"title": "Pentad - Scaled View", "xlim": [15.5, 33.5], "ylim": [-36, -20.5]},
    ]

    # Configure plots
    for i, config in enumerate(plot_config):
        fig, ax = plt.subplots(figsize=(15, 8))

        map.plot(color="lightgrey", ax=ax)

        x = df["longitude"]
        y = df["latitude"]
        z = df[column]

        if colors is not None:
            ax.scatter(x, y, c=colors, s=2)
        else:
            sc = ax.scatter(x, y, c=z, s=2)
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
                continue
            else:
                prefix = "africa_" if i == 0 else "cropped_"
                fig.savefig(f"{prefix}{filename}.png", dpi=500)

        if not alongside:
            plt.show()

    if alongside:
        plt.show()
