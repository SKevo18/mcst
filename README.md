# Minecraft Server Tracker

A Python application to scrap Minecraft servers from publicly available sources and track their historical records. Tested with Python 3.11.

## Installation

1. `git clone` this repository;
2. `cd` into the cloned repository;
3. Optional, but recommended: create a Python virtual environment (`python3.11 -m venv .venv`);
    - Afterwards, activate the virtual environment with:
        - `source .venv/bin/activate` for Unix systems (Linux/macOS);
        - `.venv\Scripts\Activate.ps1` for Windows (via PowerShell);
        - alternatively, `.venv\Scripts\activate.bat` if you don't have/use PowerShell;
4. Install requirements (`pip install -r requirements.txt`);

## How it works?

The app consists of 3 main parts:

1. Server scraper (`python -m mcst.scripts.scraper`);
    - Scraps public server list sources and saves servers in the database
2. Server pinger (`python -m mcst.scripts.pinger`);
    - Fetches scraped server results from the database, pings 10 at the same time and saves the results in the records table
3. Flask webapp to view scraped data (module: `mcst.web`);
    - Displays the data in table format
    - This is assumed to be run on a Linux (Ubuntu) server, where it was tested
    - See live data at [mcst.svit.ac](https://mcst.svit.ac) (my personal self-hosted instance, it runs a Cronjob to scrap new servers every week and pings them every day)

All data is saved in a `database.sqlite` SQLite3 database file. I have chosen this format for portability and simplicity,
but it shouldn't be a problem to swap the database URL in `mcst.database.engine` (although this code was tested with SQLite only).

Server scrapers are defined in `mcst.scripts.scraper` - feel free to create a PR to add more! In general, you just need to implement 2 functions: `get_max_pages` and `get_servers` (see the `mcst/scripts/scraper.py` file for examples on how it works)

Both Java and Bedrock servers are supported

## Like it?

This is a personal project that was developed in my spare time. Consider supporting me by [sponsoring my open-source projects through GitHub](https://github.com/sponsors/SKevo18)
