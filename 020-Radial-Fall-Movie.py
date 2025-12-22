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
	fig = Plt.figure(figsize=(11, 5))
	gs = fig.add_gridspec(1, 2, width_ratios=[1.05, 1.0], wspace=0.25)

	ax_left = fig.add_subplot(gs[0, 0])
	ax_right = fig.add_subplot(gs[0, 1])

	# --- Left: motion ---
	ax_left.set_aspect("equal", adjustable="box")
	ax_left.set_xlim(-70, 70)
	ax_left.set_ylim(-70, 70)
	ax_left.set_xlabel("R")
	ax_left.set_ylabel("R")
	ax_left.set_title(f"Radial Fall (B(R)=G/R), G={G:g}")

	ax_left.scatter([0], [0], s=500, c="yellow", edgecolors="black", zorder=4)

	ball_left, = ax_left.plot([], [], marker="o", markersize=10, linestyle="None")
	trail_left, = ax_left.plot([], [], linewidth=2, alpha=0.6)
	info = ax_left.text(0.02, 0.98, "", transform=ax_left.transAxes, va="top", ha="left")

	Trail_X, Trail_Y = [], []

	# --- Right: B(R) curve + moving point ---
	R_Curve = Np.linspace(R_Min, R_Start, 600)
	B_Curve = G / R_Curve

	ax_right.set_title("B in Abhängigkeit von R")
	ax_right.set_xlabel("R")
	ax_right.set_ylabel("B")
	ax_right.grid(True, alpha=0.35)

	# Axis limits with a little padding
	R_Pad = 0.05 * (R_Start - R_Min)
	B_Min = float(G / R_Start)
	B_Max = float(G / R_Min)
	B_Pad = 0.05 * (B_Max - B_Min)

	ax_right.set_xlim(R_Min - R_Pad, R_Start + R_Pad)
	ax_right.set_ylim(B_Min - B_Pad, B_Max + B_Pad)

	line_right, = ax_right.plot(R_Curve, B_Curve, linewidth=2, label=rf"$B={G:g}\cdot\frac{{1}}{{R}}$")
	point_right, = ax_right.plot([], [], marker="o", markersize=10, linestyle="None")

	# Optional legend (static)
	ax_right.legend(loc="upper right", framealpha=0.9)

	def init():
		ball_left.set_data([], [])
		trail_left.set_data([], [])
		info.set_text("")
		Trail_X.clear()
		Trail_Y.clear()

		point_right.set_data([], [])
		return ball_left, trail_left, info, point_right, line_right

	def update(I: int):
		Rv = float(R_Frame[I])
		Tv = float(T_Frame[I])
		Bv = G / Rv

		# Left panel updates
		Trail_X.append(Rv)
		Trail_Y.append(0.0)

		ball_left.set_data([Rv], [0.0])
		trail_left.set_data(Trail_X, Trail_Y)

		info.set_text(
			f"G = {G:g}\n"
			f"T = {Tv:.2f}\n"
			f"R = {Rv:.2f}\n"
			f"B(R) = {Bv:.2f}"
		)

		# Right panel moving point (R, B)
		point_right.set_data([Rv], [Bv]

