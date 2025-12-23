#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
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

	# 2D model: |Fg| = G/R and vector points to the center
	Factor = -G / (R * R)
	Fx = Factor * X
	Fy = Factor * Y
	F = float(Np.hypot(Fx, Fy))
	return F, Fx, Fy


def Make_Circular_Orbit_Forces_Animation(
	G: float,
	R_Orbit: float,
	V: float,
	Output_Dir: Path,
	Name_Base: str,
	Fps: int = 25,
) -> None:

	T_Total = (2.0 * Np.pi * R_Orbit) / V
	Frame_Count = int(Np.ceil(T_Total * Fps)) + 1

	T_Frame = Np.arange(Frame_Count, dtype=float) / float(Fps)
	Theta_Frame = (V / R_Orbit) * T_Frame

	X_Frame = R_Orbit * Np.cos(Theta_Frame)
	Y_Frame = R_Orbit * Np.sin(Theta_Frame)

	Fig, Ax = Plt.subplots(figsize=(7, 7))

	Limit = R_Orbit + 15.0
	Ax.set_aspect("equal", adjustable="box")
	Ax.set_xlim(-Limit, Limit)
	Ax.set_ylim(-Limit, Limit)
	Ax.set_xlabel("x")
	Ax.set_ylabel("y")
	Ax.set_title(f"Kreisbahn (R={R_Orbit:g}, V={V:g}) mit Gravitationskraft-Komponenten")

	Center = Ax.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)

	Trail, = Ax.plot([], [], linewidth=2, color="red", linestyle=":", zorder=3)
	Ball, = Ax.plot(
		[],
		[],
		marker="o",
		markersize=10,
		linestyle="None",
		color="tab:blue",
		zorder=6,
	)

	Force_Arrow = None

	Info_Text = Fig.text(
		0.02,
		0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	Trail_X_List = []
	Trail_Y_List = []

	def Init():
		nonlocal Force_Arrow
		Trail_X_List.clear()
		Trail_Y_List.clear()
		Trail.set_data([], [])
		Ball.set_data([], [])
		Info_Text.set_text("")

		if Force_Arrow is not None:
			try:
				Force_Arrow.remove()
			except Exception:
				pass
			Force_Arrow = None

		return []

	def Update(I: int):
		nonlocal Force_Arrow

		Xv = float(X_Frame[I])
		Yv = float(Y_Frame[I])
		Tv = float(T_Frame[I])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		Trail_X_List.append(Xv)
		Trail_Y_List.append(Yv)

		Trail.set_data(Trail_X_List, Trail_Y_List)
		Ball.set_data([Xv], [Yv])

		if Force_Arrow is not None:
			try:
				Force_Arrow.remove()
			except Exception:
				pass

		Arrow_Scale = 25.0  # visual scale only
		Force_Arrow = Ax.arrow(
			Xv,
			Yv,
			Arrow_Scale * Fgx,
			Arrow_Scale * Fgy,
			head_width=2.0,
			head_length=3.0,
			length_includes_head=True,
			ec="black",
			fc="black",
			zorder=5,
		)

		Info_Text.set_text(
			f"G = {G:g}\n"
			f"t = {Tv:6.2f} s\n"
			f"R = {R_Orbit:g}, V = {V:g}\n"
			f"Fg   = {Fg:8.4f}\n"
			f"Fg_x = {Fgx:8.4f}\n"
			f"Fg_y = {Fgy:8.4f}"
		)

		return []

	Anim = FuncAnimation(
		Fig,
		Update,
		frames=Frame_Count,
		init_func=Init,
		blit=False,
	)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


def Main() -> None:
	Output_Dir = Path("050-Circular-Orbit-Forces")
	Output_Dir.mkdir(exist_ok=True)

	Make_Circular_Orbit_Forces_Animation(
		G=64.0,
		R_Orbit=64.0,
		V=8.0,
		Output_Dir=Output_Dir,
		Name_Base="circular_orbit_forces_G_64_R_64_V_8",
		Fps=25,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()
