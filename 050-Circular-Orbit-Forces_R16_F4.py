#!/usr/bin/env python3
# Circular orbit with force decomposition (R=16, F_G=4, draw scale = 2)

import numpy as Np
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path


def Gravity_Force_2D(G: float, X: float, Y: float):
	R = Np.hypot(X, Y)
	F = G / R
	Fx = -F * X / R
	Fy = -F * Y / R
	return F, Fx, Fy


def Make_Circular_Orbit_Forces_Animation(
	G: float = 64.0,
	R_Orbit: float = 16.0,
	Time_Scale: float = 2.0,
	Frame_Count: int = 360,
	Fps: int = 25,
):

	F_G = G / R_Orbit
	V = Np.sqrt(G)
	Omega = V / R_Orbit

	T_End = 2 * Np.pi / Omega
	T = Np.linspace(0.0, T_End, Frame_Count)
	Theta = Omega * T

	X = R_Orbit * Np.cos(Theta)
	Y = R_Orbit * Np.sin(Theta)
	S = R_Orbit * Theta

	Fig, (Ax_L, Ax_R) = Plt.subplots(1, 2, figsize=(12, 6))

	Ax_L.set_aspect("equal")
	Ax_L.set_xlim(-22, 22)
	Ax_L.set_ylim(-22, 22)
	Ax_L.set_title("Kreisbahn und Kraftzerlegung")
	Ax_L.set_xlabel("x")
	Ax_L.set_ylabel("y")
	# Secondary axes for force scale (visual)
	Ax_L_Force = Ax_L.twinx()
	Ax_L_Force.set_ylim(-11, 11)
	Ax_L_Force.set_ylabel("Kraft (skaliert, ×2)", color="black")
	Ax_L_Force.tick_params(axis="y", labelcolor="black")


	Ax_L.scatter([0], [0], s=600, c="gold", edgecolors="black", zorder=3)
	Ball, = Ax_L.plot([], [], "o", color="tab:blue", markersize=10, zorder=5)

	Arrow_T = None
	Arrow_X = None
	Arrow_Y = None
	Rect = None

	Ax_R.set_title("Kraftkomponenten über Weg")
	Ax_R.set_xlabel("Weg s")
	Ax_R.set_ylabel("Kraft")
	Ax_R.set_xlim(0, 2 * Np.pi * R_Orbit)
	Ax_R.set_ylim(-F_G * 2.5, F_G * 2.5)
	Ax_R.grid(True, alpha=0.3)

	Line_Fx, = Ax_R.plot([], [], color="green", label="F_Gx")
	Line_Fy, = Ax_R.plot([], [], color="red", label="F_Gy")
	Ax_R.legend()

	S_List = []
	Fx_List = []
	Fy_List = []

	Info = Fig.text(0.02, 0.95, "", ha="left", va="top", family="monospace")

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

	def Update(I):
		nonlocal Arrow_T, Arrow_X, Arrow_Y, Rect

		Xv = float(X[I])
		Yv = float(Y[I])
		Sv = float(S[I])

		Fg, Fgx, Fgy = Gravity_Force_2D(G, Xv, Yv)

		Remove(Arrow_T)
		Remove(Arrow_X)
		Remove(Arrow_Y)
		Remove(Rect)

		Force_Draw_Scale = 2.0

		Dx = (Fgx / Fg) * Fg * Force_Draw_Scale
		Dy = (Fgy / Fg) * Fg * Force_Draw_Scale

		Arrow_T = Ax_L.arrow(Xv, Yv, Dx, Dy, width=0.08, color="black", zorder=4)
		Arrow_X = Ax_L.arrow(Xv, Yv, Dx, 0.0, width=0.06, color="green", zorder=3)
		Arrow_Y = Ax_L.arrow(Xv + Dx, Yv, 0.0, Dy, width=0.06, color="red", zorder=3)

		Rect = Ax_L.add_patch(
			Plt.Rectangle((Xv, Yv), Dx, Dy, facecolor="grey", alpha=0.5, linewidth=1.2)
		)

		Ball.set_data([Xv], [Yv])

		S_List.append(Sv)
		Fx_List.append(Fgx)
		Fy_List.append(Fgy)

		Line_Fx.set_data(S_List, Fx_List)
		Line_Fy.set_data(S_List, Fy_List)

		Info.set_text(
			f"Time_Scale = {Time_Scale}x\n"
			f"t (phys) = {T[I]:5.2f} s\n"
			f"s = {Sv:6.2f}\n"
			f"Fg_x = {Fgx:6.3f}\n"
			f"Fg_y = {Fgy:6.3f}"
		)

		return Ball, Arrow_T, Arrow_X, Arrow_Y, Rect, Line_Fx, Line_Fy

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Out = Path("050-Circular-Orbit-Forces")
	Out.mkdir(exist_ok=True)

	Anim.save(Out / "circular_orbit_forces_R16_F4.gif", writer=PillowWriter(fps=Fps))
	Anim.save(Out / "circular_orbit_forces_R16_F4.mp4", writer=FFMpegWriter(fps=Fps))

	Plt.close(Fig)


if __name__ == "__main__":
	Make_Circular_Orbit_Forces_Animation()
