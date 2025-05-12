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

    out = open("output.txt", "w") 
    out.write(f"{greeting}, World!") 
    out.close()

if __name__ == "__main__":
    hello()
