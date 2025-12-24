#!/usr/bin/env python3
# Circular Orbit With Force Decomposition (R=16, F_G=4)
# - Left: Space Coordinates x/y ([-20,20]) + Force Axis ([-10,10])
# - Right: F_Gx(s), F_Gy(s) with matching Force Scale ([-10,10])
# - One Orbit

import numpy as Np
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path


def Gravity_Force_2D(G: float, X: float, Y: float) -> tuple[float, float, float]:
	R = float(Np.hypot(X, Y))
	F = float(G / R)  # 2D: |F| = G / R
	Fx = float(-F * X / R)
	Fy = float(-F * Y / R)
	return F, Fx, Fy


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

	print("Saved:", Gif_Path)
	print("Saved:", Mp4_Path)


def Make_Circular_Orbit_Forces_Animation(
	G: float = 64.0,
	R_Orbit: float = 16.0,
	Time_Scale: float = 2.0,
	Frame_Count: int = 360,
	Fps: int = 25,
) -> None:

	F_G = float(G / R_Orbit)          # = 4
	V = float(Np.sqrt(G))            # = 8 (for this 2D model)
	Omega = float(V / R_Orbit)

	T_Phys_End = float(2.0 * Np.pi / Omega)
	T_Phys_Frame = Np.linspace(0.0, T_Phys_End, Frame_Count)
	Theta_Frame = Omega * T_Phys_Frame

	X_Frame = R_Orbit * Np.cos(Theta_Frame)
	Y_Frame = R_Orbit * Np.sin(Theta_Frame)

	# Path length along orbit
	S_Frame = R_Orbit * Theta_Frame

	Fig = Plt.figure(figsize=(12, 6))
	Grid = Fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0], wspace=0.25)

	Ax_Left = Fig.add_subplot(Grid[0, 0])
	Ax_Right = Fig.add_subplot(Grid[0, 1])

	# ------------------------------------------------------------
	# Left: Space + Force Axis
	# ------------------------------------------------------------

	Space_Min = -20.0
	Space_Max = 20.0
	Force_Min = -10.0
	Force_Max = 10.0

	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(Space_Min, Space_Max)
	Ax_Left.set_ylim(Space_Min, Space_Max)
	Ax_Left.set_title("Kreisbahn und Kraftzerlegung")
	Ax_Left.set_xlabel("x")
	Ax_Left.set_ylabel("y")

	# Secondary axis: Force scale matching right plot
	Ax_Left_Force = Ax_Left.twinx()
	Ax_Left_Force.set_ylim(Force_Min, Force_Max)
	Ax_Left_Force.set_ylabel("Kraft")
	Ax_Left_Force.set_yticks([-10, -5, 0, 5, 10])

	# Conversion from force-units to space-units so that force axis matches right axis
	Space_Per_Force = (Space_Max - Space_Min) / (Force_Max - Force_Min)  # = 2

	# We keep this at 1.0 so that the force axis labels match the actual values.
	# (Visual size is still larger because Space_Per_Force = 2.)
	Force_Draw_Scale = 1.0

	# Sun (Center)
	Ax_Left.scatter([0], [0], s=600, c="gold", edgecolors="black", zorder=3)

	# Earth (Ball)
	Ball, = Ax_Left.plot([], [], marker="o", markersize=10, linestyle="None", color="tab:blue", zorder=6)

	Arrow_Total = None
	Arrow_X = None
	Arrow_Y = None
	Rect = None

	# ------------------------------------------------------------
	# Right: Force Components Over Path
	# ------------------------------------------------------------

	Ax_Right.set_title("Kraftkomponenten über Weg")
	Ax_Right.set_xlabel("Weg s")
	Ax_Right.set_ylabel("Kraft")
	Ax_Right.set_xlim(0.0, float(2.0 * Np.pi * R_Orbit))
	Ax_Right.set_ylim(Force_Min, Force_Max)
	Ax_Right.grid(True, alpha=0.3)

	Line_Fgx, = Ax_Right.plot([], [], color="green", linewidth=2, label="F_Gx")
	Line_Fgy, = Ax_Right.plot([], [], color="red", linewidth=2, label="F_Gy")
	Ax_Right.legend(loc="upper right")

	S_List: list[float] = []
	Fgx_List: list[float] = []
	Fgy_List: list[float] = []

	Info_Text = Fig.text(0.02, 0.95, "", ha="left", va="top", family="monospace")

	def Remove(Obj):
		if Obj is not None:
			Obj.remove()

	def Init():
		Ball.set_data([], [])
		Line_Fgx.set_data([], [])
		Line_Fgy.set_data([], [])
		S_List.clear()
		Fgx_List.clear()
		Fgy_List.clear()
		return Ball, Line_Fgx, Line_Fgy

	def Update(Frame_Index: int):
		nonlocal Arrow_Total, Arrow_X, Arrow_Y, Rect

		Xv = float(X_Frame[Frame_Index])
		Yv = float(Y_Frame[Frame_Index])
		Sv = float(S_Frame[Frame_Index])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		# Convert force components to space-units for drawing
		Dx = Space_Per_Force * Force_Draw_Scale * Fgx
		Dy = Space_Per_Force * Force_Draw_Scale * Fgy

		Remove(Arrow_Total)
		Remove(Arrow_X)
		Remove(Arrow_Y)
		Remove(Rect)

		Arrow_Total = Ax_Left.arrow(
			Xv,
			Yv,
			Dx,
			Dy,
			width=0.10,
			color="black",
			zorder=5,
			length_includes_head=True,
			head_width=0.9,
			head_length=1.2,
		)

		Arrow_X = Ax_Left.arrow(
			Xv,
			Yv,
			Dx,
			0.0,
			width=0.08,
			color="green",
			zorder=4,
			length_includes_head=True,
			head_width=0.8,
			head_length=1.1,
		)

		Arrow_Y = Ax_Left.arrow(
			Xv + Dx,
			Yv,
			0.0,
			Dy,
			width=0.08,
			color="red",
			zorder=4,
			length_includes_head=True,
			head_width=0.8,
			head_length=1.1,
		)

		Rect = Ax_Left.add_patch(
			Plt.Rectangle(
				(Xv, Yv),
				Dx,
				Dy,
				facecolor="grey",
				alpha=0.5,
				linewidth=1.2,
				zorder=2,
			)
		)

		Ball.set_data([Xv], [Yv])

		S_List.append(Sv)
		Fgx_List.append(Fgx)
		Fgy_List.append(Fgy)

		Line_Fgx.set_data(S_List, Fgx_List)
		Line_Fgy.set_data(S_List, Fgy_List)

		# Time: show physical time and video time scaling
		T_Phys = float(T_Phys_Frame[Frame_Index])
		T_Video = float(T_Phys / Time_Scale)

		Info_Text.set_text(
			f"Time_Scale = {Time_Scale:g}x\n"
			f"t (phys)  = {T_Phys:5.2f} s\n"
			f"t (video) = {T_Video:5.2f} s\n"
			f"s        = {Sv:6.2f}\n"
			f"|Fg|      = {Fg:6.3f}\n"
			f"Fg_x      = {Fgx:6.3f}\n"
			f"Fg_y      = {Fgy:6.3f}"
		)

		return Ball, Arrow_Total, Arrow_X, Arrow_Y, Rect, Line_Fgx, Line_Fgy

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Output_Dir = Path("050-Circular-Orbit-Forces")
	Output_Dir.mkdir(exist_ok=True)

	Save_Animation_Gif_And_Mp4(
		Anim=Anim,
		Output_Dir=Output_Dir,
		Name_Base="circular_orbit_forces_R16_F4",
		Fps=Fps,
	)

	Plt.close(Fig)


def Main() -> None:
	Make_Circular_Orbit_Forces_Animation()


if __name__ == "__main__":
	Main()
