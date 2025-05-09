#!/usr/bin/env python3
import click

@click.command()
@click.option(
    "--greeting",
    type=str,
    required=True,
    help="A greeting.",
)
def hello(greeting: str):

    with open("output.txt", "w") as f:
      f.write(f"{greeting}, World!")

if __name__ == "__main__":
    hello()
