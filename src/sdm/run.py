import click

from .dataset import (
    generate_training
)


@click.group()
def cli():
    """Main entry point for the CLI."""
    pass


@cli.command()
@click.option('--species_id', required=True, help='The SABAP2 bird id to process.')
def process_species(species_id: str):
    """Method to process a given species."""
    print(f"Processing species: {species_id}", flush=True)


@cli.command()
@click.option('--species_id', required=True, help='The SABAP2 bird id to process.')
def species_stats(species_id: str):
    """Get all the stats for a given species"""
    

@cli.command()
def process_all():
    """Method to process all species."""
    # Add your logic to process all species here.
    print("Processing all species...")

if __name__ == "__main__":
    cli()