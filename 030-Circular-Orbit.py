#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path

matplotlib.rcParams["text.usetex"] = False


# ------------------------------------------------------------
# Simulation: Circular Orbit for B(R) = G / R
# ------------------------------------------------------------

def Simulate_Circular_Orbit(
	G: float,
	R_Orbit: float,
	Dt: float,
	Step_Count: int,
) -> tuple[Np.ndarray, Np.ndarray]:

	# Exact circular velocity
	V_Orbit = Np.sqrt(G)

	# Initial conditions
	X = R_Orbit
	Y = 0.0
	Vx = 0.0
	Vy = V_Orbit

	X_List = []
	Y_List = []

	def Acc(Xv: float, Yv: float) -> tuple[float, float]:
		R = Np.hypot(Xv, Yv)
		Factor = -G / (R * R)
		return Factor * Xv, Factor * Yv

	for _ in range(Step_Count):
		Ax0, Ay0 = Acc(X, Y)

		X_New = X + Vx * Dt + 0.5 * Ax0 * Dt * Dt
		Y_New = Y + Vy * Dt + 0.5 * Ay0 * Dt * Dt

		Ax1, Ay1 = Acc(X_New, Y_New)

		Vx_New = Vx + 0.5 * (Ax0 + Ax1) * Dt
		Vy_New = Vy + 0.5 * (Ay0 + Ay1) * Dt

		X, Y = X_New, Y_New
		Vx, Vy = Vx_New, Vy_New

		X_List.append(X)
		Y_List.append(Y)

	return Np.array(X_List), Np.array(Y_List)


# ------------------------------------------------------------
# Animation
# ------------------------------------------------------------

def Make_Circular_Orbit_Animation(
	G: float,
	R_Orbit: float,
	Output_Dir: Path,
	Name_Base: str,
	Dt: float = 0.02,
	Step_Count: int = 8_000,
	Frame_Count: int = 360,
	Fps: int = 25,
) -> None:

	X_Array, Y_Array = Simulate_Circular_Orbit(
		G=G,
		R_Orbit=R_Orbit,
		Dt=Dt,
		Step_Count=Step_Count,
	)

	Idx = Np.linspace(0, len(X_Array) - 1, Frame_Count).astype(int)
	X_Frame = X_Array[Idx]
	Y_Frame = Y_Array[Idx]

	Fig, Ax = Plt.subplots(figsize=(6, 6))

	Ax.set_aspect("equal", adjustable="box")
	Ax.set_xlim(-80, 80)
	Ax.set_ylim(-80, 80)
	Ax.set_xlabel("x")
	Ax.set_ylabel("y")
	Ax.set_title(f"Kreisbahn bei R={R_Orbit:g}, G={G:g}")

	# Center mass
	Center = Ax.scatter([0], [0], s=500, c="yellow", edgecolors="black", zorder=2)

	# Orbit trail
	Trail, = Ax.plot([], [], linewidth=2, color="red", linestyle=":", zorder=3)

	# Orbiting body
	Ball, = Ax.plot(
		[],
		[],
		marker="o",
		markersize=10,
		linestyle="None",
		color="tab:blue",
		zorder=5,
	)

	Trail_X: list[float] = []
	Trail_Y: list[float] = []

	def Init():
		Ball.set_data([], [])
		Trail.set_data([], [])
		Trail_X.clear()
		Trail_Y.clear()
		return Ball, Trail, Center

	def Update(I: int):
		Xv = float(X_Frame[I])
		Yv = float(Y_Frame[I])

		Trail_X.append(Xv)
		Trail_Y.append(Yv)

		Ball.set_data([Xv], [Yv])
		Trail.set_data(Trail_X, Trail_Y)

		return Ball, Trail, Center

	Anim = FuncAnimation(
		Fig,
		Update,
		frames=Frame_Count,
		init_func=Init,
		blit=True,
	)

	Gif_Path = Output_Dir / f"{Name_Base}.gif"
	Mp4_Path = Output_Dir / f"{Name_Base}.mp4"

	Anim.save(Gif_Path, writer=PillowWriter(fps=Fps))
	Anim.save(Mp4_Path, writer=FFMpegWriter(fps=Fps))

	print(f"Saved: {Gif_Path}")
	print(f"Saved: {Mp4_Path}")

	Plt.close(Fig)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def Main() -> None:
	Output_Dir = Path("030-Circular-Orbit")
	Output_Dir.mkdir(exist_ok=True)

	Make_Circular_Orbit_Animation(
		G=64.0,
		R_Orbit=64.0,
		Output_Dir=Output_Dir,
		Name_Base="circular_orbit_G_64_R_64",
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

