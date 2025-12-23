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

	# |Fg| = G/R , direction to center
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

	# --- time mapping ---
	T_Phys_Total = (2.0 * Np.pi * R_Orbit) / V
	T_Video_Total = T_Phys_Total / Time_Scale
	Frame_Count = int(Np.ceil(T_Video_Total * Fps)) + 1

	T_Video = Np.arange(Frame_Count, dtype=float) / float(Fps)
	T_Phys = T_Video * Time_Scale

	Theta = (V / R_Orbit) * T_Phys

	X_Frame = R_Orbit * Np.cos(Theta)
	Y_Frame = R_Orbit * Np.sin(Theta)

	# arc length s = R * theta
	S_Frame = R_Orbit * Theta

	# --- figure layout ---
	Fig = Plt.figure(figsize=(13, 6))
	Grid = Fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0], wspace=0.3)

	Ax_Left = Fig.add_subplot(Grid[0, 0])
	Ax_Right = Fig.add_subplot(Grid[0, 1])

	# =========================================================
	# LEFT: orbit + force vectors
	# =========================================================

	Limit = R_Orbit + 15.0
	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(-Limit, Limit)
	Ax_Left.set_ylim(-Limit, Limit)
	Ax_Left.set_xlabel("x")
	Ax_Left.set_ylabel("y")
	Ax_Left.set_title("Kreisbahn und Kraftzerlegung")

	Ax_Left.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)

	Trail, = Ax_Left.plot([], [], linewidth=2, color="red", linestyle=":", zorder=3)
	Ball, = Ax_Left.plot([], [], "o", color="tab:blue", markersize=10, zorder=6)

	Arrow_Total = None
	Arrow_X = None
	Arrow_Y = None
	Rect = None

	Trail_X = []
	Trail_Y = []

	# =========================================================
	# RIGHT: Fx(s), Fy(s)
	# =========================================================

	Ax_Right.set_title("Kraft-Komponenten entlang des Kreiswegs")
	Ax_Right.set_xlabel("Weg s")
	Ax_Right.set_ylabel("Kraft")

	Ax_Right.set_xlim(0.0, float(S_Frame[-1]))
	Ax_Right.set_ylim(-1.1 * (G / R_Orbit), 1.1 * (G / R_Orbit))
	Ax_Right.grid(True, alpha=0.35)

	Line_Fx, = Ax_Right.plot([], [], color="tab:red", label="Fg_x(s)")
	Line_Fy, = Ax_Right.plot([], [], color="tab:green", label="Fg_y(s)")

	Point_Fx, = Ax_Right.plot([], [], "o", color="tab:red")
	Point_Fy, = Ax_Right.plot([], [], "o", color="tab:green")

	Ax_Right.legend(loc="upper right")

	S_List = []
	Fx_List = []
	Fy_List = []

	Info_Text = Fig.text(
		0.02, 0.98, "", va="top", ha="left", fontsize=11
	)

	def Remove(A):
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
		S_List.clear()
		Fx_List.clear()
		Fy_List.clear()

		Trail.set_data([], [])
		Ball.set_data([], [])
		Line_Fx.set_data([], [])
		Line_Fy.set_data([], [])
		Point_Fx.set_data([], [])
		Point_Fy.set_data([], [])

		Remove(Arrow_Total)
		Remove(Arrow_X)
		Remove(Arrow_Y)
		Remove(Rect)

		Arrow_Total = None
		Arrow_X = None
		Arrow_Y = None
		Rect = None
		Info_Text.set_text("")
		return []

	def Update(I: int):
		nonlocal Arrow_Total, Arrow_X, Arrow_Y, Rect

		Xv = float(X_Frame[I])
		Yv = float(Y_Frame[I])
		Sv = float(S_Frame[I])
		Tv = float(T_Phys[I])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		# --- left ---
		Trail_X.append(Xv)
		Trail_Y.append(Yv)
		Trail.set_data(Trail_X, Trail_Y)
		Ball.set_data([Xv], [Yv])

		Remove(Arrow_Total)
		Remove(Arrow_X)
		Remove(Arrow_Y)
		Remove(Rect)

		Scale = 25.0
		Dx = Scale * Fgx
		Dy = Scale * Fgy

		Arrow_Total = Ax_Left.arrow(
			Xv, Yv, Dx, Dy,
			head_width=2.0, head_length=3.0,
			length_includes_head=True,
			ec="black", fc="black", zorder=5,
		)

		Arrow_X = Ax_Left.arrow(
			Xv, Yv, Dx, 0.0,
			head_width=1.5, head_length=2.5,
			length_includes_head=True,
			ec="tab:red", fc="tab:red", zorder=4,
		)

		Arrow_Y = Ax_Left.arrow(
			Xv, Yv, 0.0, Dy,
			head_width=1.5, head_length=2.5,
			length_includes_head=True,
			ec="tab:green", fc="tab:green", zorder=4,
		)

		Rect_X0 = Xv + (Dx if Dx < 0 else 0.0)
		Rect_Y0 = Yv + (Dy if Dy < 0 else 0.0)

		Rect = Rectangle(
			(Rect_X0, Rect_Y0),
			abs(Dx), abs(Dy),
			fill=True,
			facecolor="0.5",
			alpha=0.5,
			edgecolor="0.25",
			linewidth=1.8,
			zorder=3,
		)
		Ax_Left.add_patch(Rect)

		# --- right ---
		S_List.append(Sv)
		Fx_List.append(Fgx)
		Fy_List.append(Fgy)

		Line_Fx.set_data(S_List, Fx_List)
		Line_Fy.set_data(S_List, Fy_List)
		Point_Fx.set_data([Sv], [Fgx])
		Point_Fy.set_data([Sv], [Fgy])

		Info_Text.set_text(
			f"Time_Scale = {Time_Scale:g}x\n"
			f"t (phys) = {Tv:6.2f} s\n"
			f"s = {Sv:7.2f}\n"
			f"Fg_x = {Fgx:7.4f}\n"
			f"Fg_y = {Fgy:7.4f}"
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
		Name_Base="circular_orbit_forces_sine_components",
		Fps=25,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()
