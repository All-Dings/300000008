#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


def _Find_Font_Path() -> Optional[str]:
	Font_Path_List: List[str] = [
		# macOS
		"/System/Library/Fonts/Menlo.ttc",
		"/System/Library/Fonts/Monaco.ttf",
		"/Library/Fonts/Menlo.ttc",
		"/Library/Fonts/Monaco.ttf",
		# Linux
		"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
		"/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
	]
	for Font_Path in Font_Path_List:
		if os.path.isfile(Font_Path):
			return Font_Path
	return None


def _Text_BBox(
	Draw: ImageDraw.ImageDraw,
	Text: str,
	Font: ImageFont.FreeTypeFont,
) -> Tuple[int, int, int, int]:
	if hasattr(Draw, "textbbox"):
		return Draw.textbbox((0, 0), Text, font=Font)
	Size = Draw.textsize(Text, font=Font)  # type: ignore[attr-defined]
	return (0, 0, Size[0], Size[1])


def _Load_Font(Font_Path: Optional[str], Font_Size: int) -> ImageFont.FreeTypeFont:
	if Font_Path is None:
		Font_Path = _Find_Font_Path()
	if Font_Path is not None:
		return ImageFont.truetype(Font_Path, Font_Size)
	return ImageFont.load_default()


def _Pick_Font_To_Fit(
	Width: int,
	Height: int,
	Text: str,
	Font_Path: Optional[str],
	Padding_X: int,
	Padding_Y: int,
	Max_Font_Size: int,
	Min_Font_Size: int,
) -> ImageFont.FreeTypeFont:
	Temp_Image = Image.new("RGBA", (Width, Height), (0, 0, 0, 0))
	Draw = ImageDraw.Draw(Temp_Image)

	Font_Size = Max_Font_Size
	while Font_Size >= Min_Font_Size:
		Font = _Load_Font(Font_Path, Font_Size)
		L, T, R, B = _Text_BBox(Draw, Text, Font)
		Text_Width = R - L
		Text_Height = B - T

		if (
			Text_Width <= (Width - 2 * Padding_X)
			and Text_Height <= (Height - 2 * Padding_Y)
		):
			return Font

		Font_Size -= 1

	return _Load_Font(Font_Path, Min_Font_Size)


def _Format_Time(Second_Index: int) -> str:
	Hour = Second_Index // 3600
	Minute = (Second_Index % 3600) // 60
	Second = Second_Index % 60
	return f"{Hour:02d}:{Minute:02d}:{Second:02d}"


def _Run_FFmpeg(
	Output_Path: str,
	Width: int,
	Height: int,
	Fps: int,
) -> subprocess.Popen:
	Ffmpeg_Path = shutil.which("ffmpeg")
	if Ffmpeg_Path is None:
		raise RuntimeError("ffmpeg Not Found In PATH.")

	Cmd_List: List[str] = [
		Ffmpeg_Path,
		"-y",
		"-f",
		"rawvideo",
		"-pix_fmt",
		"rgba",
		"-s",
		f"{Width}x{Height}",
		"-r",
		str(Fps),
		"-i",
		"-",
		"-c:v",
		"prores_ks",
		"-profile:v",
		"4",                 # ProRes 4444
		"-pix_fmt",
		"yuva444p10le",       # Alpha
		"-movflags",
		"+faststart",
		Output_Path,
	]

	Process = subprocess.Popen(Cmd_List, stdin=subprocess.PIPE)
	if Process.stdin is None:
		raise RuntimeError("ffmpeg stdin Not Available.")
	return Process


def Main() -> int:
	# Directory
	Output_Dir = "./"
	os.makedirs(Output_Dir, exist_ok=True)

	Output_Path = os.path.join(
		Output_Dir,
		"400003552.mov",
	)

	Width = 240
	Height = 80
	Fps = 1

	Padding_X = 6
	Padding_Y = 6

	Font_Path: Optional[str] = None  # Optional: Set Explicit Path
	Max_Font_Size = 80
	Min_Font_Size = 10

	Reference_Text = "00:00:00"
	Font = _Pick_Font_To_Fit(
		Width=Width,
		Height=Height,
		Text=Reference_Text,
		Font_Path=Font_Path,
		Padding_X=Padding_X,
		Padding_Y=Padding_Y,
		Max_Font_Size=Max_Font_Size,
		Min_Font_Size=Min_Font_Size,
	)

	Process = _Run_FFmpeg(Output_Path, Width, Height, Fps)

	try:
		for Second_Index in range(0, 24 * 60 * 60):
			Text = _Format_Time(Second_Index)

			Image_Obj = Image.new("RGBA", (Width, Height), (0, 0, 0, 0))
			Draw = ImageDraw.Draw(Image_Obj)

			L, T, R, B = _Text_BBox(Draw, Text, Font)
			Text_Width = R - L
			Text_Height = B - T

			X = (Width - Text_Width) // 2 - L
			Y = (Height - Text_Height) // 2 - T

			Draw.text((X, Y), Text, font=Font, fill=(255, 0, 0, 255))

			assert Process.stdin is not None
			Process.stdin.write(Image_Obj.tobytes())

		assert Process.stdin is not None
		Process.stdin.close()
		Return_Code = Process.wait()
		if Return_Code != 0:
			print("ffmpeg Failed.", file=sys.stderr)
			return Return_Code

	except KeyboardInterrupt:
		try:
			if Process.stdin is not None:
				Process.stdin.close()
		except Exception:
			pass
		Process.terminate()
		return 130

	print("Done:", Output_Path)
	return 0


if __name__ == "__main__":
	raise SystemExit(Main())

