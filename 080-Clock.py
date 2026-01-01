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
		"/System/Library/Fonts/Courier New.ttf",
		"/Library/Fonts/Menlo.ttc",
		"/Library/Fonts/Monaco.ttf",
		"/Library/Fonts/Courier New.ttf",
		# Linux (Common)
		"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
		"/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
	]
	for Font_Path in Font_Path_List:
		if os.path.isfile(Font_Path):
			return Font_Path
	return None


def _Load_Mono_Font(Font_Size: int, Font_Path: Optional[str]) -> ImageFont.FreeTypeFont:
	if Font_Path is None:
		Font_Path = _Find_Font_Path()

	if Font_Path is not None:
		try:
			# Note: Some .ttc Fonts Contain Multiple Faces; PIL Usually Picks A Valid One.
			return ImageFont.truetype(Font_Path, Font_Size)
		except Exception:
			pass

	# Fallback: This Is Not Guaranteed Monospace, But Avoids Hard Failure.
	return ImageFont.load_default()


def _Format_Time(Second_Index: int) -> str:
	Hour = Second_Index // 3600
	Minute = (Second_Index % 3600) // 60
	Second = Second_Index % 60
	return f"{Hour:02d}:{Minute:02d}:{Second:02d}"


def _Text_BBox(Draw: ImageDraw.ImageDraw, Text: str, Font: ImageFont.FreeTypeFont) -> Tuple[int, int, int, int]:
	# Pillow Compatibility: textbbox Exists In Newer Versions.
	if hasattr(Draw, "textbbox"):
		return Draw.textbbox((0, 0), Text, font=Font)
	Size = Draw.textsize(Text, font=Font)  # type: ignore[attr-defined]
	return (0, 0, Size[0], Size[1])


def _Run_FFmpeg(
	Output_Path: str,
	Width: int,
	Height: int,
	Fps: int,
) -> subprocess.Popen:
	Ffmpeg_Path = shutil.which("ffmpeg")
	if Ffmpeg_Path is None:
		raise RuntimeError("ffmpeg Not Found. Please Install ffmpeg And Ensure It Is In PATH.")

	# ProRes 4444 With Alpha In .mov:
	# -c:v prores_ks -profile:v 4  => ProRes 4444
	# -pix_fmt yuva444p10le        => Alpha + 10-bit
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
		"4",
		"-pix_fmt",
		"yuva444p10le",
		"-movflags",
		"+faststart",
		Output_Path,
	]

	Process = subprocess.Popen(Cmd_List, stdin=subprocess.PIPE)
	if Process.stdin is None:
		raise RuntimeError("Failed To Open ffmpeg stdin.")
	return Process


def Main() -> int:
	# Settings
	Output_Path = "Digital_Clock_24h_240w_Alpha.mov"
	Width = 240
	Height = 80
	Fps = 1
	Font_Size = 56
	Font_Path: Optional[str] = None  # Or Set A Specific Path

	Start_Second = 0
	End_Second = 24 * 60 * 60 - 1  # 86399

	Font = _Load_Mono_Font(Font_Size, Font_Path)

	Process = _Run_FFmpeg(Output_Path, Width, Height, Fps)

	try:
		for Second_Index in range(Start_Second, End_Second + 1):
			Text = _Format_Time(Second_Index)

			Image_Obj = Image.new("RGBA", (Width, Height), (0, 0, 0, 0))
			Draw = ImageDraw.Draw(Image_Obj)

			L, T, R, B = _Text_BBox(Draw, Text, Font)
			Text_Width = R - L
			Text_Height = B - T

			X = (Width - Text_Width) // 2 - L
			Y = (Height - Text_Height) // 2 - T

			# Red Digits, Transparent Background
			Draw.text((X, Y), Text, font=Font, fill=(255, 0, 0, 255))

			Frame_Bytes = Image_Obj.tobytes()
			assert Process.stdin is not None
			Process.stdin.write(Frame_Bytes)

		assert Process.stdin is not None
		Process.stdin.close()
		Return_Code = Process.wait()
		if Return_Code != 0:
			print(f"ffmpeg Failed With Exit Code {Return_Code}", file=sys.stderr)
			return Return_Code

	except KeyboardInterrupt:
		try:
			if Process.stdin is not None:
				Process.stdin.close()
		except Exception:
			pass
		Process.terminate()
		return 130

	print(f"Done: {Output_Path}")
	return 0


if __name__ == "__main__":
	raise SystemExit(Main())

