#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from matplotlib.patches import Rectangle
from pathlib import Path
from typing import Tuple

matplotlib.rcParams["text.usetex"] = False


def Save_Animation_Gif_And_Mp4(
	Anim: FuncAnimation,
	Output_Dir: Path,
	Name_Base: str,
	Fps: int,
) -> None:

	Gif_Path = Output_Dir / f"{Name_Base}.gif"
	Mp4_Path = Output_Dir / f"{Name_Base}.mp4"

	Anim.save(Gif_Path, writer=PillowWriter(fps=Fps))
	Anim.save(Mp4_Path, writer=FFMpegWriter(fps=Fps))

	print(f"Saved: {Gif_Path}")
	print(f"Saved: {Mp4_Path}")


def Gravity_Force_2D(
	G: float,
	X: float,
	Y: float,
) -> Tuple[float, float, float]:

	R = float(Np.hypot(X, Y))
	if R <= 0.0:
		return 0.0, 0.0, 0.0

	Factor = -G / (R * R)
	Fx = Factor * X
	Fy = Factor * Y
	F = float(Np.hypot(Fx, Fy))
	return F, Fx, Fy


def Make_Circular_Orbit_Forces_Animation(
	G: float,
	R_Orbit: float,
	V: float,
	Time_Scale: float,
	Output_Dir: Path,
	Name_Base: str,
	Fps: int = 25,
) -> None:

	T_Phys_Total = (2.0 * Np.pi * R_Orbit) / V
	T_Video_Total = T_Phys_Total / Time_Scale

	Frame_Count = int(Np.ceil(T_Video_Total * Fps)) + 1

	T_Video = Np.arange(Frame_Count, dtype=float) / float(Fps)
	T_Phys = T_Video * Time_Scale

	Theta_Frame = (V / R_Orbit) * T_Phys

	X_Frame = R_Orbit * Np.cos(Theta_Frame)
	Y_Frame = R_Orbit * Np.sin(Theta_Frame)

	Fig, Ax = Plt.subplots(figsize=(7, 7))

	Limit = R_Orbit + 15.0
	Ax.set_aspect("equal", adjustable="box")
	Ax.set_xlim(-Limit, Limit)
	Ax.set_ylim(-Limit, Limit)
	Ax.set_xlabel("x")
	Ax.set_ylabel("y")
	Ax.set_title("Kreisbahn mit Gravitationskraft-Vektoren")

	Ax.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)

	Trail, = Ax.plot([], [], linewidth=2, color="red", linestyle=":", zorder=3)
	Ball, = Ax.plot([], [], "o", color="tab:blue", markersize=10, zorder=6)

	Arrow_Total = None
	Arrow_X = None
	Arrow_Y = None
	Rect = None

	Info_Text = Fig.text(
		0.02,
		0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	Trail_X = []
	Trail_Y = []

	def Remove_Artist(A):
		if A is None:
			return
		try:
			A.remove()
		except Exception:
			pass

	def Init():
		nonlocal Arrow_Total, Arrow_X, Arrow_Y, Rect
		Trail_X.clear()
		Trail_Y.clear()
		Trail.set_data([], [])
		Ball.set_data([], [])
		Info_Text.set_text("")

		Remove_Artist(Arrow_Total)
		Remove_Artist(Arrow_X)
		Remove_Artist(Arrow_Y)
		Remove_Artist(Rect)

		Arrow_Total = None
		Arrow_X = None
		Arrow_Y = None
		Rect = None
		return []

	def Update(I: int):
		nonlocal Arrow_Total, Arrow_X, Arrow_Y, Rect

		Xv = float(X_Frame[I])
		Yv = float(Y_Frame[I])
		Tv = float(T_Phys[I])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		Trail_X.append(Xv)
		Trail_Y.append(Yv)

		Trail.set_data(Trail_X, Trail_Y)
		Ball.set_data([Xv], [Yv])

		Remove_Artist(Arrow_Total)
		Remove_Artist(Arrow_X)
		Remove_Artist(Arrow_Y)
		Remove_Artist(Rect)

		Scale = 25.0
		Dx = Scale * Fgx
		Dy = Scale * Fgy

		Arrow_Total = Ax.arrow(
			Xv, Yv, Dx, Dy,
			head_width=2.0, head_length=3.0,
			length_includes_head=True,
			ec="black", fc="black", zorder=5,
		)

		Arrow_X = Ax.arrow(
			Xv, Yv, Dx, 0.0,
			head_width=1.5, head_length=2.5,
			length_includes_head=True,
			ec="tab:red", fc="tab:red", zorder=4,
		)

		Arrow_Y = Ax.arrow(
			Xv, Yv, 0.0, Dy,
			head_width=1.5, head_length=2.5,
			length_includes_head=True,
			ec="tab:green", fc="tab:green", zorder=4,
		)

		Rect_X0 = Xv + (Dx if Dx < 0 else 0.0)
		Rect_Y0 = Yv + (Dy if Dy < 0 else 0.0)
		Rect_W = abs(Dx)
		Rect_H = abs(Dy)

		Rect = Rectangle(
			(Rect_X0, Rect_Y0),
			Rect_W, Rect_H,
			fill=True,
			facecolor="0.5",
			alpha=0.5,
			edgecolor="0.25",
			linewidth=1.8,
			zorder=3,
		)
		Ax.add_patch(Rect)

		Info_Text.set_text(
			f"Time_Scale = {Time_Scale:g}x\n"
			f"t (phys) = {Tv:6.2f} s\n"
			f"Fg   = {Fg:8.4f}\n"
			f"Fg_x = {Fgx:8.4f}\n"
			f"Fg_y = {Fgy:8.4f}"
		)

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)
	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


def Main() -> None:
	Output_Dir = Path("050-Circular-Orbit-Forces")
	Output_Dir.mkdir(exist_ok=True)

	Make_Circular_Orbit_Forces_Animation(
		G=64.0,
		R_Orbit=64.0,
		V=8.0,
		Time_Scale=2.0,
		Output_Dir=Output_Dir,
		Name_Base="circular_orbit_forces_timescale_2x",
		Fps=25,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()
