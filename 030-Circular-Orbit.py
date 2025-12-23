#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path

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


def Simulate_Multi_Circular_Orbits(
	G: float,
	R_List: list[float],
	V_Orbit: float,
	Dt: float,
	Step_Count: int,
) -> tuple[Np.ndarray, Np.ndarray]:

	Body_Count = len(R_List)

	X_Array = Np.zeros((Body_Count, Step_Count), dtype=float)
	Y_Array = Np.zeros((Body_Count, Step_Count), dtype=float)

	X = Np.zeros(Body_Count, dtype=float)
	Y = Np.zeros(Body_Count, dtype=float)
	Vx = Np.zeros(Body_Count, dtype=float)
	Vy = Np.zeros(Body_Count, dtype=float)

	# Spread start angles so bodies don't overlap
	Angle_Array = Np.linspace(0.0, 2.0 * Np.pi, Body_Count, endpoint=False)

	for I, R_Orbit in enumerate(R_List):
		Theta = float(Angle_Array[I])

		X[I] = R_Orbit * Np.cos(Theta)
		Y[I] = R_Orbit * Np.sin(Theta)

		# Tangential direction: rotate radial vector by +90°
		Vx[I] = -V_Orbit * Np.sin(Theta)
		Vy[I] = +V_Orbit * Np.cos(Theta)

	def Acc(Xv: float, Yv: float) -> tuple[float, float]:
		R = Np.hypot(Xv, Yv)
		Factor = -G / (R * R)  # so |a| = G/R
		return Factor * Xv, Factor * Yv

	for Step in range(Step_Count):
		Ax0 = Np.zeros(Body_Count, dtype=float)
		Ay0 = Np.zeros(Body_Count, dtype=float)

		for I in range(Body_Count):
			Ax0[I], Ay0[I] = Acc(float(X[I]), float(Y[I]))

		X_New = X + Vx * Dt + 0.5 * Ax0 * Dt * Dt
		Y_New = Y + Vy * Dt + 0.5 * Ay0 * Dt * Dt

		Ax1 = Np.zeros(Body_Count, dtype=float)
		Ay1 = Np.zeros(Body_Count, dtype=float)

		for I in range(Body_Count):
			Ax1[I], Ay1[I] = Acc(float(X_New[I]), float(Y_New[I]))

		Vx_New = Vx + 0.5 * (Ax0 + Ax1) * Dt
		Vy_New = Vy + 0.5 * (Ay0 + Ay1) * Dt

		X, Y = X_New, Y_New
		Vx, Vy = Vx_New, Vy_New

		X_Array[:, Step] = X
		Y_Array[:, Step] = Y

	return X_Array, Y_Array


def Make_Multi_Orbit_Animation(
	G: float,
	R_List: list[float],
	Output_Dir: Path,
	Name_Base: str,
	V_Orbit: float = 8.0,
	Dt: float = 0.02,
	Step_Count: int = 10_000,
	Frame_Count: int = 360,
	Fps: int = 25,
) -> None:

	X_All, Y_All = Simulate_Multi_Circular_Orbits(
		G=G,
		R_List=R_List,
		V_Orbit=V_Orbit,
		Dt=Dt,
		Step_Count=Step_Count,
	)

	Idx = Np.linspace(0, Step_Count - 1, Frame_Count).astype(int)
	X_Frame = X_All[:, Idx]
	Y_Frame = Y_All[:, Idx]

	Planet_Name_List = ["Merkur", "Venus", "Erde", "Mars", "Jupiter", "Saturn", "Uranus"]

	# Planet-ish colors (approx)
	Planet_Color_List = [
		"#9e9e9e",  # Merkur (gray)
		"#d2b48c",  # Venus (tan)
		"#1f77b4",  # Erde (blue)
		"#d62728",  # Mars (red)
		"#bc7c3a",  # Jupiter (brown/orange)
		"#e6d8a8",  # Saturn (pale yellow)
		"#7fd3ff",  # Uranus (light cyan)
	]

	Fig, Ax = Plt.subplots(figsize=(7, 7))

	Limit = max(R_List) + 12
	Ax.set_aspect("equal", adjustable="box")
	Ax.set_xlim(-Limit, Limit)
	Ax.set_ylim(-Limit, Limit)
	Ax.set_xlabel("x")
	Ax.set_ylabel("y")
	Ax.set_title(f"7 Kreisbahnen (R=1..64), G={G:g}, v={V_Orbit:g}")

	Center = Ax.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)

	# Optional: show reference circles for each radius
	for R_Orbit in R_List:
		Theta = Np.linspace(0.0, 2.0 * Np.pi, 400)
		Ax.plot(R_Orbit * Np.cos(Theta), R_Orbit * Np.sin(Theta), linewidth=1, alpha=0.15, zorder=1)

	Trail_List = []
	Ball_List = []
	Trail_X_List_List: list[list[float]] = []
	Trail_Y_List_List: list[list[float]] = []

	for I in range(len(R_List)):
		Color = Planet_Color_List[I]

		Trail, = Ax.plot([], [], linewidth=2, alpha=0.6, color=Color, zorder=3)
		Ball, = Ax.plot(
			[],
			[],
			marker="o",
			markersize=9,
			linestyle="None",
			color=Color,
			zorder=5,
			label=f"{Planet_Name_List[I]} (R={R_List[I]:g})",
		)

		Trail_List.append(Trail)
		Ball_List.append(Ball)
		Trail_X_List_List.append([])
		Trail_Y_List_List.append([])

	Ax.legend(loc="upper right", framealpha=0.9)

	def Init():
		Artist_List = [Center]
		for I in range(len(R_List)):
			Ball_List[I].set_data([], [])
			Trail_List[I].set_data([], [])
			Trail_X_List_List[I].clear()
			Trail_Y_List_List[I].clear()
			Artist_List += [Trail_List[I], Ball_List[I]]
		return Artist_List

	def Update(Frame_Index: int):
		Artist_List = [Center]
		for I in range(len(R_List)):
			Xv = float(X_Frame[I, Frame_Index])
			Yv = float(Y_Frame[I, Frame_Index])

			Trail_X_List_List[I].append(Xv)
			Trail_Y_List_List[I].append(Yv)

			Ball_List[I].set_data([Xv], [Yv])
			Trail_List[I].set_data(Trail_X_List_List[I], Trail_Y_List_List[I])

			Artist_List += [Trail_List[I], Ball_List[I]]

		return Artist_List

	Anim = FuncAnimation(
		Fig,
		Update,
		frames=Frame_Count,
		init_func=Init,
		blit=True,
	)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


def Main() -> None:
	Output_Dir = Path("030-Circular-Orbit")
	Output_Dir.mkdir(exist_ok=True)

	R_List = [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0]

	Make_Multi_Orbit_Animation(
		G=64.0,
		R_List=R_List,
		Output_Dir=Output_Dir,
		Name_Base="multi_orbit_planets_G_64_R_1_to_64",
		V_Orbit=8.0,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

