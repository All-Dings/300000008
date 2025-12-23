#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path

matplotlib.rcParams["text.usetex"] = False


# ------------------------------------------------------------
# Helper
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Physics: multi circular orbits (2D gravity B(R)=G/R)
# ------------------------------------------------------------

def Simulate_Multi_Circular_Orbits(
	G: float,
	R_List: list[float],
	V_Orbit: float,
	Dt: float,
	Step_Count: int,
) -> tuple[Np.ndarray, Np.ndarray]:

	Body_Count = len(R_List)

	X_Array = Np.zeros((Body_Count, Step_Count))
	Y_Array = Np.zeros((Body_Count, Step_Count))

	X = Np.zeros(Body_Count)
	Y = Np.zeros(Body_Count)
	Vx = Np.zeros(Body_Count)
	Vy = Np.zeros(Body_Count)

	Angle_Array = Np.linspace(0.0, 2.0 * Np.pi, Body_Count, endpoint=False)

	for I, R in enumerate(R_List):
		Theta = float(Angle_Array[I])
		X[I] = R * Np.cos(Theta)
		Y[I] = R * Np.sin(Theta)
		Vx[I] = -V_Orbit * Np.sin(Theta)
		Vy[I] = +V_Orbit * Np.cos(Theta)

	def Acc(Xv: float, Yv: float) -> tuple[float, float]:
		R = Np.hypot(Xv, Yv)
		Factor = -G / (R * R)   # |a| = G/R
		return Factor * Xv, Factor * Yv

	for Step in range(Step_Count):
		Ax0 = Np.zeros(Body_Count)
		Ay0 = Np.zeros(Body_Count)

		for I in range(Body_Count):
			Ax0[I], Ay0[I] = Acc(X[I], Y[I])

		X_New = X + Vx * Dt + 0.5 * Ax0 * Dt * Dt
		Y_New = Y + Vy * Dt + 0.5 * Ay0 * Dt * Dt

		Ax1 = Np.zeros(Body_Count)
		Ay1 = Np.zeros(Body_Count)

		for I in range(Body_Count):
			Ax1[I], Ay1[I] = Acc(X_New[I], Y_New[I])

		Vx += 0.5 * (Ax0 + Ax1) * Dt
		Vy += 0.5 * (Ay0 + Ay1) * Dt

		X, Y = X_New, Y_New

		X_Array[:, Step] = X
		Y_Array[:, Step] = Y

	return X_Array, Y_Array


# ------------------------------------------------------------
# Animation
# ------------------------------------------------------------

def Make_Orbit_And_Line_Animation(
	G: float,
	R_List: list[float],
	Output_Dir: Path,
	Name_Base: str,
	V_Orbit: float = 8.0,
	Dt: float = 0.01,
	Fps: int = 25,
	Time_Scale: float = 2.0,
) -> None:

	R_Max = max(R_List)
	T_Orbit_Max = 2.0 * Np.pi * R_Max / V_Orbit
	T_Total = T_Orbit_Max   # one orbit for R=64

	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	X_All, Y_All = Simulate_Multi_Circular_Orbits(
		G, R_List, V_Orbit, Dt, Step_Count
	)

	Frame_Count = int(Np.ceil((T_Total / Time_Scale) * Fps)) + 1
	T_Video = Np.arange(Frame_Count) / Fps
	T_Phys = T_Video * Time_Scale

	Idx = Np.clip((T_Phys / Dt).astype(int), 0, Step_Count - 1)
	X_Frame = X_All[:, Idx]
	Y_Frame = Y_All[:, Idx]

	Planet_Color_List = [
		"#9e9e9e",
		"#d2b48c",
		"#1f77b4",
		"#d62728",
		"#bc7c3a",
		"#e6d8a8",
		"#7fd3ff",
	]

	Fig = Plt.figure(figsize=(14, 7))
	Grid = Fig.add_gridspec(1, 2, wspace=0.22)
	Ax_Left = Fig.add_subplot(Grid[0, 0])
	Ax_Right = Fig.add_subplot(Grid[0, 1])

	# ---------------- Left ----------------

	Limit = R_Max + 12
	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(-Limit, Limit)
	Ax_Left.set_ylim(-Limit, Limit)
	Ax_Left.set_xlabel("x")
	Ax_Left.set_ylabel("y")
	Ax_Left.set_title("Kreisbahnen (1 Umlauf bei R=64)")

	Ax_Left.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)

	Theta = Np.linspace(0.0, 2.0 * Np.pi, 600)
	for R in R_List:
		Ax_Left.plot(R * Np.cos(Theta), R * Np.sin(Theta), alpha=0.12)

	# ---------------- Right ----------------

	Ax_Right.set_title("Gleiche Geschwindigkeit auf Geraden")
	Ax_Right.set_xlabel("Weg")
	Ax_Right.set_ylabel("R")
	Ax_Right.grid(True, alpha=0.25)

	Distance_Total = V_Orbit * T_Total
	Ax_Right.set_xlim(0.0, Distance_Total * 1.05)

	# reversed vertical order: R=1 top, R=64 bottom
	Y_Pos_List = list(reversed(range(len(R_List))))
	Ax_Right.set_ylim(-0.6, len(R_List) - 0.4)
	Ax_Right.set_yticks(Y_Pos_List)
	Ax_Right.set_yticklabels([str(int(R)) for R in R_List])

	for I, R in enumerate(R_List):
		Color = Planet_Color_List[I]
		Y0 = float(Y_Pos_List[I])

		T_Orbit = 2.0 * Np.pi * R / V_Orbit
		Cycle_Count = int(Np.floor(T_Total / T_Orbit + 1e-9))
		Marker_X_List = [(2.0 * Np.pi * R) * K for K in range(Cycle_Count + 1)]

		Ax_Right.hlines(Y0, 0.0, Distance_Total, color=Color, alpha=0.12, linewidth=2)

		for K, Xk in enumerate(Marker_X_List):
			Half = 0.26 if K in (0, Cycle_Count) else 0.18
			Lw = 3 if K in (0, Cycle_Count) else 2
			Alpha = 0.95 if K in (0, Cycle_Count) else 0.75

			Ax_Right.vlines(Xk, Y0 - Half, Y0 + Half, color=Color, linewidth=Lw, alpha=Alpha)

	# ---------------- Artists ----------------

	Ball_L, Trail_L = [], []
	Ball_R, Trail_R = [], []
	TLX, TLY, TRX, TRY = [], [], [], []

	for I in range(len(R_List)):
		Color = Planet_Color_List[I]

		Tl, = Ax_Left.plot([], [], color=Color, alpha=0.6)
		Bl, = Ax_Left.plot([], [], "o", color=Color)

		Tr, = Ax_Right.plot([], [], color=Color, alpha=0.6)
		Br, = Ax_Right.plot([], [], "o", color=Color)

		Trail_L.append(Tl)
		Ball_L.append(Bl)
		Trail_R.append(Tr)
		Ball_R.append(Br)

		TLX.append([])
		TLY.append([])
		TRX.append([])
		TRY.append([])

	Info = Fig.text(
		0.01, 0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	def Init():
		for I in range(len(R_List)):
			TLX[I].clear()
			TLY[I].clear()
			TRX[I].clear()
			TRY[I].clear()
		return []

	def Update(F: int):
		t_phys = float(T_Phys[F])

		Info.set_text(
			f"Time_Scale = {Time_Scale}x\n"
			f"t_phys = {t_phys:6.2f} s\n"
			f"v = {V_Orbit:g}"
		)

		for I in range(len(R_List)):
			x = float(X_Frame[I, F])
			y = float(Y_Frame[I, F])

			TLX[I].append(x)
			TLY[I].append(y)
			Ball_L[I].set_data(x, y)
			Trail_L[I].set_data(TLX[I], TLY[I])

			xl = V_Orbit * t_phys
			y0 = float(Y_Pos_List[I])

			TRX[I].append(xl)
			TRY[I].append(y0)
			Ball_R[I].set_data(xl, y0)
			Trail_R[I].set_data(TRX[I], TRY[I])

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def Main() -> None:
	Output_Dir = Path("030-Circular-Orbit")
	Output_Dir.mkdir(exist_ok=True)

	R_List = [1, 2, 4, 8, 16, 32, 64]

	Make_Orbit_And_Line_Animation(
		G=64.0,
		R_List=R_List,
		Output_Dir=Output_Dir,
		Name_Base="orbits_vs_lines_reversed_order",
		Time_Scale=2.0,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

