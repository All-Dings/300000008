#!/usr/bin/env python3
# Radial Fall Animations For B(R)=G/R
# - Stop at R = 1.0
# - Output GIF + MP4 into "020-Radial-Fall-4-Gs"
# - Single animation for G=64 (LEFT: motion, RIGHT: B(R) graph with moving point)
# - Combined 2x2 animation for G=16,32,64,128
# - Increased spacing between subplots

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
from pathlib import Path

matplotlib.rcParams["text.usetex"] = False


# ------------------------------------------------------------
# Physics simulation (Velocity Verlet)
# ------------------------------------------------------------

def Simulate_Radial_Fall(
	G: float,
	R_Start: float,
	V_Start: float,
	Dt: float,
	Step_Count: int,
	R_Min: float,
) -> tuple[Np.ndarray, Np.ndarray]:

	Time_List = []
	R_List = []

	R: float = R_Start
	V: float = V_Start
	T: float = 0.0

	def Acc(R_Value: float) -> float:
		return -G / R_Value

	for _ in range(Step_Count):
		if R <= R_Min:
			break

		A0 = Acc(R)
		R_New = R + V * Dt + 0.5 * A0 * Dt * Dt

		if R_New <= R_Min:
			R = R_Min
			T += Dt
			Time_List.append(T)
			R_List.append(R)
			break

		A1 = Acc(R_New)
		V_New = V + 0.5 * (A0 + A1) * Dt

		R, V = R_New, V_New
		T += Dt

		Time_List.append(T)
		R_List.append(R)

	return Np.array(Time_List), Np.array(R_List)


def Interpolate_R_T_With_Stop(
	T_Array: Np.ndarray,
	R_Array: Np.ndarray,
	T_Query_Array: Np.ndarray,
) -> tuple[Np.ndarray, Np.ndarray]:

	T_End = float(T_Array[-1])
	R_End = float(R_Array[-1])

	T_Out = Np.empty_like(T_Query_Array, dtype=float)
	R_Out = Np.empty_like(T_Query_Array, dtype=float)

	for I, Tq in enumerate(T_Query_Array):
		if float(Tq) <= T_End:
			T_Out[I] = float(Tq)
			R_Out[I] = float(Np.interp(float(Tq), T_Array, R_Array))
		else:
			T_Out[I] = T_End
			R_Out[I] = R_End

	return T_Out, R_Out


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
# Single animation (G = 64) with B(R) graph on the right
# ------------------------------------------------------------

def Make_Single_Animation(
	G: float,
	Output_Dir: Path,
	Name_Base: str,
	R_Start: float = 64.0,
	V_Start: float = 0.0,
	Dt: float = 0.01,
	Step_Count: int = 200_000,
	R_Min: float = 1.0,
	Frame_Count: int = 180,
	Fps: int = 25,
) -> None:

	T_Array, R_Array = Simulate_Radial_Fall(
		G, R_Start, V_Start, Dt, Step_Count, R_Min
	)

	T_End = float(T_Array[-1])
	T_Query = Np.linspace(0.0, T_End, Frame_Count)
	T_Frame, R_Frame = Interpolate_R_T_With_Stop(T_Array, R_Array, T_Query)

	# --- Figure with two panels ---
	Fig = Plt.figure(figsize=(11, 5))
	Grid = Fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.25)

	Ax_Left = Fig.add_subplot(Grid[0, 0])
	Ax_Right = Fig.add_subplot(Grid[0, 1])

	# --- Left: motion ---
	Ax_Left.set_aspect("equal", adjustable="box")
	Ax_Left.set_xlim(-70, 70)
	Ax_Left.set_ylim(-70, 70)
	Ax_Left.set_xlabel("R")
	Ax_Left.set_ylabel("R")
	Ax_Left.set_title(f"Radial Fall (B(R)=G/R), G={G:g}")

	Ax_Left.scatter([0], [0], s=500, c="yellow", edgecolors="black", zorder=4)

	Ball_Color = "tab:blue"

	Ball_Left, = Ax_Left.plot(
		[],
		[],
		marker="o",
		markersize=10,
		linestyle="None",
		color=Ball_Color,
	)

	Trail_Left, = Ax_Left.plot([], [], linewidth=2, alpha=0.6)

	Info_Text = Ax_Left.text(
		0.02, 0.98, "", transform=Ax_Left.transAxes, va="top", ha="left"
	)

	Trail_X_List: list[float] = []
	Trail_Y_List: list[float] = []

	# --- Right: B(R) curve ---
	R_Curve = Np.linspace(R_Min, R_Start, 600)
	B_Curve = G / R_Curve

	Ax_Right.set_title("B in Abhängigkeit von R")
	Ax_Right.set_xlabel("R")
	Ax_Right.set_ylabel("B")
	Ax_Right.grid(True, alpha=0.35)

	R_Pad = 0.05 * (R_Start - R_Min)
	B_Min = float(G / R_Start)
	B_Max = float(G / R_Min)
	B_Pad = 0.05 * (B_Max - B_Min)

	Ax_Right.set_xlim(R_Min - R_Pad, R_Start + R_Pad)
	Ax_Right.set_ylim(B_Min - B_Pad, B_Max + B_Pad)

	Line_Right, = Ax_Right.plot(
		R_Curve, B_Curve, linewidth=2, label=rf"$B={G:g}\cdot\frac{{1}}{{R}}$"
	)

	Point_Right, = Ax_Right.plot(
		[],
		[],
		marker="o",
		markersize=10,
		linestyle="None",
		color=Ball_Color,
	)

	Ax_Right.legend(loc="upper right", framealpha=0.9)

	def Init():
		Ball_Left.set_data([], [])
		Trail_Left.set_data([], [])
		Info_Text.set_text("")
		Trail_X_List.clear()
		Trail_Y_List.clear()
		Point_Right.set_data([], [])
		return Ball_Left, Trail_Left, Info_Text, Point_Right, Line_Right

	def Update(Frame_Index: int):
		R_Value = float(R_Frame[Frame_Index])
		T_Value = float(T_Frame[Frame_Index])
		B_Value = G / R_Value

		Trail_X_List.append(R_Value)
		Trail_Y_List.append(0.0)

		Ball_Left.set_data([R_Value], [0.0])
		Trail_Left.set_data(Trail_X_List, Trail_Y_List)

		Info_Text.set_text(
			f"G = {G:g}\n"
			f"T = {T_Value:.2f}\n"
			f"R = {R_Value:.2f}\n"
			f"B(R) = {B_Value:.2f}"
		)

		Point_Right.set_data([R_Value], [B_Value])

		return Ball_Left, Trail_Left, Info_Text, Point_Right, Line_Right

	Fig.tight_layout()

	Anim = FuncAnimation(
		Fig,
		Update,
		frames=Frame_Count,
		init_func=Init,
		blit=True,
	)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


# ------------------------------------------------------------
# Combined animation (unchanged logic, style consistent)
# ------------------------------------------------------------

def Make_Combined_Animation_2x2(
	G_List: list[float],
	Output_Dir: Path,
	Name_Base: str,
	R_Start: float = 64.0,
	V_Start: float = 0.0,
	Dt: float = 0.01,
	Step_Count: int = 200_000,
	R_Min: float = 1.0,
	Frame_Count: int = 240,
	Fps: int = 25,
) -> None:

	Series = []
	T_End_List = []

	for G in G_List:
		Ta, Ra = Simulate_Radial_Fall(G, R_Start, V_Start, Dt, Step_Count, R_Min)
		Series.append((G, Ta, Ra))
		T_End_List.append(float(Ta[-1]))

	T_End_Max = max(T_End_List)
	T_Query = Np.linspace(0.0, T_End_Max, Frame_Count)

	T_Frame_List, R_Frame_List = [], []
	for (_, Ta, Ra) in Series:
		Tf, Rf = Interpolate_R_T_With_Stop(Ta, Ra, T_Query)
		T_Frame_List.append(Tf)
		R_Frame_List.append(Rf)

	Fig, Ax = Plt.subplots(2, 2, figsize=(9, 9))
	Fig.subplots_adjust(wspace=0.35, hspace=0.35)

	Ax_List = [Ax[0, 0], Ax[0, 1], Ax[1, 0], Ax[1, 1]]

	Balls, Trails, Texts = [], [], []
	Trail_X_List = [[], [], [], []]
	Trail_Y_List = [[], [], [], []]

	for Ax_i, G in zip(Ax_List, G_List):
		Ax_i.set_aspect("equal", adjustable="box")
		Ax_i.set_xlim(-70, 70)
		Ax_i.set_ylim(-70, 70)
		Ax_i.set_xlabel("R")
		Ax_i.set_ylabel("R")
		Ax_i.set_title(f"G = {G:g}")

		Ax_i.scatter([0], [0], s=500, c="yellow", edgecolors="black", zorder=4)

		B, = Ax_i.plot([], [], marker="o", markersize=10, linestyle="None")
		T, = Ax_i.plot([], [], linewidth=2, alpha=0.6)
		Txt = Ax_i.text(0.02, 0.98, "", transform=Ax_i.transAxes, va="top", ha="left")

		Balls.append(B)
		Trails.append(T)
		Texts.append(Txt)

	Fig.suptitle("Radial Fall Vergleich: B(R)=G/R", fontsize=14)
	Fig.tight_layout(rect=[0, 0, 1, 0.94])

	def Init():
		A = []
		for I in range(4):
			Balls[I].set_data([], [])
			Trails[I].set_data([], [])
			Texts[I].set_text("")
			Trail_X_List[I].clear()
			Trail_Y_List[I].clear()
			A += [Balls[I], Trails[I], Texts[I]]
		return A

	def Update(Frame: int):
		A = []
		for I, G in enumerate(G_List):
			Rv = float(R_Frame_List[I][Frame])
			Tv = float(T_Frame_List[I][Frame])
			Bv = G / Rv

			Trail_X_List[I].append(Rv)
			Trail_Y_List[I].append(0.0)

			Balls[I].set_data([Rv], [0.0])
			Trails[I].set_data(Trail_X_List[I], Trail_Y_List[I])

			Texts[I].set_text(
				f"T = {Tv:.2f}\n"
				f"R = {Rv:.2f}\n"
				f"B(R) = {Bv:.2f}"
			)

			A += [Balls[I], Trails[I], Texts[I]]
		return A

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=True)
	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def Main() -> None:
	Output_Dir = Path("020-Radial-Fall-4-Gs")
	Output_Dir.mkdir(exist_ok=True)

	Make_Single_Animation(
		G=64.0,
		Output_Dir=Output_Dir,
		Name_Base="radial_fall_single_G_64",
	)

	Make_Combined_Animation_2x2(
		G_List=[16.0, 32.0, 64.0, 128.0],
		Output_Dir=Output_Dir,
		Name_Base="radial_fall_combined_G_16_32_64_128",
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

