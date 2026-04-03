# /// script
# dependencies = [
#   "pygame-ce",
# ]
# ///

import asyncio
import pygame

from particles import main as particles_main


if __name__ == "__main__":
    asyncio.run(particles_main())
