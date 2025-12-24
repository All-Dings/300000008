#!/usr/bin/env python3
# Circular orbit with force decomposition (R=16, F_G=4)

import numpy as Np
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path


# ------------------------------------------------------------
# Physics
# ------------------------------------------------------------

def Gravity_Force_2D(G: float, X: float, Y: float):
	R = Np.hypot(X, Y)
	F = G / R
	Fx = -F * X / R
	Fy = -F * Y / R
	return F, Fx, Fy


# ------------------------------------------------------------
# Animation
# ------------------------------------------------------------

def Make_Circular_Orbit_Forces_Animation(
	G: float = 64.0,
	R_Orbit: float = 16.0,
	Time_Scale: float = 2.0,
	Frame_Count: int = 360,
	Fps: int = 25,
):

	# Derived constants
	F_G = G / R_Orbit        # = 4
	V = Np.sqrt(G)           # = 8
	Omega = V / R_Orbit

	T_Phys_End = 2 * Np.pi / Omega
	T_Phys = Np.linspace(0.0, T_Phys_End, Frame_Count)
	Theta = Omega * T_Phys

	X_Frame = R_Orbit * Np.cos(Theta)
	Y_Frame = R_Orbit * Np.sin(Theta)

	S_Frame = R_Orbit * Theta

	Fig, (Ax_Left, Ax_Right) = Plt.subplots(1, 2, figsize=(12, 6))

	# ---------------- Left: geometry ----------------

	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(-22, 22)
	Ax_Left.set_ylim(-22, 22)
	Ax_Left.set_title("Kreisbahn und Kraftzerlegung")
	Ax_Left.set_xlabel("x")
	Ax_Left.set_ylabel("y")

	Sun = Ax_Left.scatter([0], [0], s=600, c="gold", edgecolors="black", zorder=3)
	Ball, = Ax_Left.plot([], [], "o", color="tab:blue", markersize=10, zorder=5)

	Arrow_Total = None
	Arrow_X = None
	Arrow_Y = None
	Rect = None

	# ---------------- Right: forces vs path ----------------

	Ax_Right.set_title("Kraftkomponenten über Weg")
	Ax_Right.set_xlabel("Weg s")
	Ax_Right.set_ylabel("Kraft")
	Ax_Right.set_xlim(0, 2 * Np.pi * R_Orbit)
	Ax_Right.set_ylim(-F_G * 1.2, F_G * 1.2)
	Ax_Right.grid(True, alpha=0.3)

	Line_Fx, = Ax_Right.plot([], [], color="green", label="F_Gx")
	Line_Fy, = Ax_Right.plot([], [], color="red", label="F_Gy")
	Ax_Right.legend()

	S_List = []
	Fx_List = []
	Fy_List = []

	Info = Fig.text(
		0.02, 0.95, "", ha="left", va="top", fontsize=10, family="monospace"
	)

	def Remove(obj):
		if obj is not None:
			obj.remove()

	def Init():
		Ball.set_data([], [])
		Line_Fx.set_data([], [])
		Line_Fy.set_data([], [])
		S_List.clear()
		Fx_List.clear()
		Fy_List.clear()
		return Ball, Line_Fx, Line_Fy

	def Update(I: int):
		nonlocal Arrow_Total, Arrow_X, Arrow_Y, Rect

		Xv = float(X_Frame[I])
		Yv = float(Y_Frame[I])
		Sv = float(S_Frame[I])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		# remove old drawings
		Remove(Arrow_Total)
		Remove(Arrow_X)
		Remove(Arrow_Y)
		Remove(Rect)

		# draw total force (length exactly F_G)
		Dx = (Fgx / Fg) * Fg
		Dy = (Fgy / Fg) * Fg

		Arrow_Total = Ax_Left.arrow(
			Xv, Yv, Dx, Dy,
			width=0.08,
			color="black",
			zorder=4
		)

		Arrow_X = Ax_Left.arrow(
			Xv, Yv, Dx, 0.0,
			width=0.06,
			color="green",
			zorder=3
		)

		Arrow_Y = Ax_Left.arrow(
			Xv + Dx, Yv, 0.0, Dy,
			width=0.06,
			color="red",
			zorder=3
		)

		Rect = Ax_Left.add_patch(
			Plt.Rectangle(
				(Xv, Yv),
				Dx,
				Dy,
				facecolor="grey",
				alpha=0.5,
				linewidth=1.2,
			)
		)

		Ball.set_data([Xv], [Yv])

		S_List.append(Sv)
		Fx_List.append(Fgx)
		Fy_List.append(Fgy)

		Line_Fx.set_data(S_List, Fx_List)
		Line_Fy.set_data(S_List, Fy_List)

		Info.set_text(
			f"Time_Scale = {Time_Scale}x\n"
			f"t (phys) = {T_Phys[I]:5.2f} s\n"
			f"s = {Sv:6.2f}\n"
			f"Fg_x = {Fgx:6.3f}\n"
			f"Fg_y = {Fgy:6.3f}"
		)

		return (
			Ball,
			Arrow_Total,
			Arrow_X,
			Arrow_Y,
			Rect,
			Line_Fx,
			Line_Fy,
		)

	Anim = FuncAnimation(
		Fig,
		Update,
		frames=Frame_Count,
		init_func=Init,
		blit=False,
	)

	Output_Dir = Path("050-Circular-Orbit-Forces")
	Output_Dir.mkdir(exist_ok=True)

	Gif_Path = Output_Dir / "circular_orbit_forces_R16_F4.gif"
	Mp4_Path = Output_Dir / "circular_orbit_forces_R16_F4.mp4"

	Anim.save(Gif_Path, writer=PillowWriter(fps=Fps))
	Anim.save(Mp4_Path, writer=FFMpegWriter(fps=Fps))

	print("Saved:", Gif_Path)
	print("Saved:", Mp4_Path)

	Plt.close(Fig)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":
	Make_Circular_Orbit_Forces_Animation()
