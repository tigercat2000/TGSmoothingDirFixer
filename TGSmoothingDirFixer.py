#!/usr/bin/env python
"""
This script takes .dmi (BYOND Icon) files, specifically those that are used in /tg/station13's smoothing process, and outputs a client.dir compatible version.
Place any number of .dmi files in the `in/` directory, run `py DMIWallTransformer.py`, and the corrected versions will appear in `out/` with the same name.
"""

import time
from os import listdir
from os.path import isfile, join
from sys import path

from PIL import Image

from DMI import DMI

input_files = [f for f in listdir(join(path[0], "in")) if isfile(join(path[0], "in", f))]

for f in input_files:
	if not f.endswith(".dmi"):
		continue

	print("Fixing {0}...".format(f))
	start = time.time()
	dmi = DMI(Image.open(join(path[0], "in", f)))
	new_image, pnginfo = dmi.get_image()
	new_image.save(join(path[0], "out", f), format="PNG", pnginfo=pnginfo)
	end = time.time()
	print("Fixed {0} in {1}s".format(f, round(end - start, 2)))

