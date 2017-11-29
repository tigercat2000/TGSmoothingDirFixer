# /tg/station13 smoothing sprite dir fixer

This script takes .dmi (BYOND image) files, specifically those used by /tg/station13 for "smooth" sprites,
and makes them work correctly with the new 511 "client.dir" variable. 

# Setup

Install [pillow](https://pillow.readthedocs.io/en/3.4.x/installation.html) with [pip](https://pip.pypa.io/en/stable/installing/) using the follow command:
```
pip install pillow
```

# Usage

Place any number of smooth icon files in the `in/` directory, then run the following:
```
py TGSmoothingDirFixer.py
```

Corrected files will appear under the same name in the `out/` directory.