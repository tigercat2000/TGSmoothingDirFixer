#!/usr/bin/env python
"""
This file contains the DMI class, which does all of the direct image modifications, state parsing, and general DMI interactions for the wall transformer script.
"""

import os, sys, re, math

from PIL import Image, PngImagePlugin


nasty_hardcoded_state_list = [
"1-i",
"2-i",
"3-i",
"4-i",
"1-n",
"2-n",
"3-s",
"4-s",
"1-w",
"2-e",
"3-w",
"4-e",
"1-nw",
"2-ne",
"3-sw",
"4-se",
"1-f",
"2-f",
"3-f",
"4-f",
"d-se-0",
"d-se-1",
"d-se",
"d-sw-0",
"d-sw-1",
"d-sw",
"d-ne-0",
"d-ne-1",
"d-ne",
"d-nw-0",
"d-nw-1",
"d-nw"
]

index_regex = re.compile(r"(.*)? =")
value_regex = re.compile(r"= (.*)?$")
def __get_line(line):
	index = index_regex.search(line)[1].replace('\t', '')

	value = value_regex.search(line)[1]

	if value.startswith('"'):
		value = value.replace('"', '')
	else:
		try:
			value = int(value)
		except ValueError:
			try:
				value = float(value)
			except ValueError:
				pass

	return (index, value)

def get_value(dmi_metainfo, dmi_index):
	i = 0
	while i < len(dmi_metainfo):
		if dmi_metainfo[i].startswith(dmi_index):
			obj = {}
			index_line = __get_line(dmi_metainfo[i])
			obj[index_line[0]] = index_line[1]
			while dmi_metainfo[i + 1].startswith('\t'):
				new_line = __get_line(dmi_metainfo[i + 1])
				obj[new_line[0]] = new_line[1]
				i += 1
			return obj

		i += 1

def get_all_states(dmi_metainfo):
	state_list = []

	for x in dmi_metainfo:
		if x.startswith("state"):
			state_list.append(__get_line(x)[1])

	return state_list

def get_frame_count(dmi_metainfo):
	i = 0
	for state in get_all_states(dmi_metainfo):
		value = get_value(dmi_metainfo, 'state = "%s"' % state)
		i += value["dirs"] * value["frames"]
	return i

class DMI:
	def __init__(self, image):
		self.icon_states = []
		self.frames_to_states = {}

		self.parse_metainfo(image)
		self.correlate_icons(image)

	def parse_metainfo(self, image):
		self.dmi_metainfo = image.info["Description"].split('\n')

		self._info = get_value(self.dmi_metainfo, "version")

		frame = 0
		for state in get_all_states(self.dmi_metainfo):
			value = get_value(self.dmi_metainfo, 'state = "%s"' % state)
			
			local_frames = []
			for f in range(value["frames"]):
				for i in range(value["dirs"]):
					self.frames_to_states[frame] = value
					local_frames.append(frame)
					frame += 1
			
			value["state_to_frames"] = local_frames
			value["icon_data"] = []
			self.icon_states.append(value)

		self.grid_size = math.ceil(math.sqrt(get_frame_count(self.dmi_metainfo)))


	def correlate_icons(self, image):
		current_frame = 0
		for oy in range(self.grid_size):
			for ox in range(self.grid_size):
				box = (
					ox * self._info["width"],
					oy * self._info["height"],
					ox * self._info["width"] + self._info["width"],
					oy * self._info["height"] + self._info["height"])

				try:
					self.frames_to_states[current_frame]["icon_data"].append(image.crop(box))
				except KeyError:
					pass

				current_frame += 1

	def place_icon(self, image, state, frame, grid_size):
		start_frame = frame
		current_iter = 0
		for frames in range(state["frames"]):
			for dirs in range(state["dirs"]):
				box = (
					(frame % grid_size) * self._info["width"],
					(math.floor(frame / grid_size)) * self._info["height"],
					(frame % grid_size) * self._info["width"] + self._info["width"],
					(math.floor(frame / grid_size)) * self._info["height"] + self._info["height"],
					)

				image.paste(state["icon_data"][current_iter], box)

				current_iter += 1
				frame += 1

		return frame - start_frame

	def place_directional_icon(self, image, state, frame, grid_size):
		start_frame = frame
		current_iter = -1
		for frames in range(state["frames"]):
			current_iter += 1
			for new_state in range(4):
				box = (
					(frame % grid_size) * self._info["width"],
					(math.floor(frame / grid_size)) * self._info["height"],
					(frame % grid_size) * self._info["width"] + self._info["width"],
					(math.floor(frame / grid_size)) * self._info["height"] + self._info["height"],
					)

				rotation = 0 #NORTH
				if new_state == 1: # SOUTH
					rotation = 180
				elif new_state == 2: # EAST
					rotation = 90
				elif new_state == 3: # WEST
					rotation = 270

				frame += 1

				image.paste(state["icon_data"][current_iter].rotate(rotation), box)

		return frame - start_frame

	def get_png_info(self):
		desc = "# BEGIN DMI\n"
		desc += "version = 4.0\n\twidth = 32\n\theight = 32\n"

		for state in self.icon_states:
			desc += 'state = "{0}"\n\tdirs = {1}\n\tframes = {2}\n'.format(state["state"], state["dirs"], state["frames"])
			if "delay" in state:
				desc += "\tdelay = {0}\n".format(state["delay"])

		desc += "# END DMI"

		data = PngImagePlugin.PngInfo()
		data.add_text("Description", desc, 1)
		return data

	def get_image(self):
		current_frame_count = get_frame_count(self.dmi_metainfo)

		current_smoothing_count = 0
		for state in self.icon_states:
			if state["state"] in nasty_hardcoded_state_list:
				current_smoothing_count += state["frames"] * state["dirs"]

		new_smoothing_count = (current_frame_count - current_smoothing_count) + current_smoothing_count * 4 

		new_grid_size = math.ceil(math.sqrt(new_smoothing_count))

		new_file_dimensions = new_grid_size * self._info["width"]

		new_file = Image.new("RGBA", (new_file_dimensions, new_file_dimensions))

		current_frame = 0
		for state in self.icon_states:
			if state["state"] in nasty_hardcoded_state_list:
				state["dirs"] = 4
				current_frame += self.place_directional_icon(new_file, state, current_frame, new_grid_size)
			else:
				current_frame += self.place_icon(new_file, state, current_frame, new_grid_size)

		return (new_file, self.get_png_info())