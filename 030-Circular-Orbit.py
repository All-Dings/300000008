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

	Angle_Array = Np.linspace(0.0, 2.0 * Np.pi, Body_Count, endpoint=False)

	for I, R_Orbit in enumerate(R_List):
		Theta = float(Angle_Array[I])

		X[I] = R_Orbit * Np.cos(Theta)
		Y[I] = R_Orbit * Np.sin(Theta)

		Vx[I] = -V_Orbit * Np.sin(Theta)
		Vy[I] = +V_Orbit * Np.cos(Theta)

	def Acc(Xv: float, Yv: float) -> tuple[float, float]:
		R = Np.hypot(Xv, Yv)
		Factor = -G / (R * R)  # => |a| = G/R
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

	R_Max = float(max(R_List))

	T_Orbit_Max = 2.0 * Np.pi * R_Max / V_Orbit
	T_Total = 1.0 * T_Orbit_Max  # one cycle for R=64

	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	X_All, Y_All = Simulate_Multi_Circular_Orbits(
		G=G,
		R_List=R_List,
		V_Orbit=V_Orbit,
		Dt=Dt,
		Step_Count=Step_Count,
	)

	Frame_Count = int(Np.ceil((T_Total / Time_Scale) * Fps)) + 1

	T_Video = Np.arange(Frame_Count, dtype=float) / float(Fps)
	T_Phys = T_Video * Time_Scale

	Idx = Np.clip((T_Phys / Dt).astype(int), 0, Step_Count - 1)

	X_Frame = X_All[:, Idx]
	Y_Frame = Y_All[:, Idx]

	Planet_Name_List = ["Merkur", "Venus", "Erde", "Mars", "Jupiter", "Saturn", "Uranus"]
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
	Grid = Fig.add_gridspec(1, 2, width_ratios=[1.05, 1.15], wspace=0.18)
	Ax_Left = Fig.add_subplot(Grid[0, 0])
	Ax_Right = Fig.add_subplot(Grid[0, 1])

	Limit = R_Max + 12.0
	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(-Limit, Limit)
	Ax_Left.set_ylim(-Limit, Limit)
	Ax_Left.set_xlabel("x")
	Ax_Left.set_ylabel("y")
	Ax_Left.set_title(f"Kreisbahnen (1 Umlauf bei R={R_Max:g})")

	Ax_Right.set_xlabel("x")
	Ax_Right.set_ylabel("Linie")
	Ax_Right.set_title("Gleiche Geschwindigkeit auf geraden Linien")
	Ax_Right.grid(True, alpha=0.25)

	Center_Left = Ax_Left.scatter([0], [0], s=650, c="yellow", edgecolors="black", zorder=2)
	Center_Right = Ax_Right.scatter([], [], s=0, alpha=0.0)

	Theta = Np.linspace(0.0, 2.0 * Np.pi, 600)
	for R_Orbit in R_List:
		Ax_Left.plot(R_Orbit * Np.cos(Theta), R_Orbit * Np.sin(Theta), linewidth=1, alpha=0.12, zorder=1)

	Distance_Total = V_Orbit * T_Total
	X_Min = -0.05 * Distance_Total
	X_Max = 1.05 * Distance_Total
	Ax_Right.set_xlim(X_Min, X_Max)
	Ax_Right.set_ylim(-1.5, len(R_List) - 0.5)

	Y_Offset_List = Np.linspace(len(R_List) - 1, 0, len(R_List))
	Y_Scale = 1.0

	for I, R_Orbit in enumerate(R_List):
		Color = Planet_Color_List[I]
		Y0 = float(Y_Offset_List[I] * Y_Scale)

		T_Orbit = 2.0 * Np.pi * float(R_Orbit) / V_Orbit
		Cycle_Count = int(Np.floor(T_Total / T_Orbit + 1e-9))

		Marker_X_List = [0.0 + (2.0 * Np.pi * float(R_Orbit)) * K for K in range(Cycle_Count + 1)]

		Ax_Right.hlines(Y0, 0.0, Distance_Total, linewidth=2, alpha=0.12, color=Color, zorder=1)

		for K, Xk in enumerate(Marker_X_List):
			Is_Ends = (K == 0) or (K == Cycle_Count)
			Tick_Half = 0.26 if Is_Ends else 0.18
			Lw = 3 if Is_Ends else 2
			Alpha = 0.95 if Is_Ends else 0.75
			Ax_Right.vlines(Xk, Y0 - Tick_Half, Y0 + Tick_Half, color=Color, linewidth=Lw, alpha=Alpha, zorder=2)

		Ax_Right.text(
			X_Min + 0.01 * (X_Max - X_Min),
			Y0,
			f"R={R_Orbit:g}",
			va="center",
			ha="left",
			fontsize=9,
			color=Color,
		)

	Ball_Left_List = []
	Trail_Left_List = []
	Trail_Left_X_List_List: list[list[float]] = []
	Trail_Left_Y_List_List: list[list[float]] = []

	Ball_Right_List = []
	Trail_Right_List = []
	Trail_Right_X_List_List: list[list[float]] = []
	Trail_Right_Y_List_List: list[list[float]] = []

	for I in range(len(R_List)):
		Color = Planet_Color_List[I]
		Label = Planet_Name_List[I] if I < len(Planet_Name_List) else f"Objekt {I+1}"

		Trail_Left, = Ax_Left.plot([], [], linewidth=2, alpha=0.55, color=Color, zorder=3)
		Ball_Left, = Ax_Left.plot(
			[],
			[],
			marker="o",
			markersize=9,
			linestyle="None",
			color=Color,
			zorder=5,
			label=f"{Label} (R={R_List[I]:g})",
		)

		Trail_Right, = Ax_Right.plot([], [], linewidth=2, alpha=0.55, color=Color, zorder=3)
		Ball_Right, = Ax_Right.plot(
			[],
			[],
			marker="o",
			markersize=9,
			linestyle="None",
			color=Color,
			zorder=5,
		)

		Ball_Left_List.append(Ball_Left)
		Trail_Left_List.append(Trail_Left)
		Trail_Left_X_List_List.append([])
		Trail_Left_Y_List_List.append([])

		Ball_Right_List.append(Ball_Right)
		Trail_Right_List.append(Trail_Right)
		Trail_Right_X_List_List.append([])
		Trail_Right_Y_List_List.append([])

	Ax_Left.legend(loc="upper right", framealpha=0.9)

	Info_Text = Fig.text(
		0.01,
		0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	U_Reference = 8.0
	T_Reference = U_Reference / V_Orbit

	def Init():
		Artist_List = [Center_Left, Center_Right, Info_Text]

		for I in range(len(R_List)):
			Ball_Left_List[I].set_data([], [])
			Trail_Left_List[I].set_data([], [])
			Trail_Left_X_List_List[I].clear()
			Trail_Left_Y_List_List[I].clear()

			Ball_Right_List[I].set_data([], [])
			Trail_Right_List[I].set_data([], [])
			Trail_Right_X_List_List[I].clear()
			Trail_Right_Y_List_List[I].clear()

			Artist_List += [
				Trail_Left_List[I],
				Ball_Left_List[I],
				Trail_Right_List[I],
				Ball_Right_List[I],
			]

		Info_Text.set_text("")
		return Artist_List

	def Update(Frame_Index: int):
		T_Video_Value = float(T_Video[Frame_Index])
		T_Phys_Value = float(T_Phys[Frame_Index])

		Artist_List = [Center_Left, Center_Right, Info_Text]

		Info_Text.set_text(
			f"Time_Scale = {Time_Scale:g}x\n"
			f"Videozeit t_video = {T_Video_Value:6.2f} s\n"
			f"Physikzeit t_phys  = {T_Phys_Value:6.2f} s\n"
			f"v = {V_Orbit:g} (Weg-Einheiten/s)\n"
			f"Referenz: U=8 -> T = U/v = {T_Reference:.2f} s"
		)

		X_Line = V_Orbit * T_Phys_Value

		for I in range(len(R_List)):
			Xv = float(X_Frame[I, Frame_Index])
			Yv = float(Y_Frame[I, Frame_Index])

			Trail_Left_X_List_List[I].append(Xv)
			Trail_Left_Y_List_List[I].append(Yv)

			Ball_Left_List[I].set_data([Xv], [Yv])
			Trail_Left_List[I].set_data(Trail_Left_X_List_List[I], Trail_Left_Y_List_List[I])

			Y_Line = float(Y_Offset_List[I] * Y_Scale)

			Trail_Right_X_List_List[I].append(X_Line)
			Trail_Right_Y_List_List[I].append(Y_Line)

			Ball_Right_List[I].set_data([X_Line], [Y_Line])
			Trail_Right_List[I].set_data(Trail_Right_X_List_List[I], Trail_Right_Y_List_List[I])

			Artist_List += [
				Trail_Left_List[I],
				Ball_Left_List[I],
				Trail_Right_List[I],
				Ball_Right_List[I],
			]

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

	Make_Orbit_And_Line_Animation(
		G=64.0,
		R_List=R_List,
		Output_Dir=Output_Dir,
		Name_Base="orbits_vs_lines_time_scale_one_cycle_R_64",
		V_Orbit=8.0,
		Dt=0.01,
		Fps=25,
		Time_Scale=2.0,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

