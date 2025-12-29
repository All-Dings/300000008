#!/usr/bin/env python3

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter
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


def Acc(
	G: float,
	Xv: float,
	Yv: float,
) -> Tuple[float, float]:
	R = float(Np.hypot(Xv, Yv))
	Factor = -G / (R * R)   # Magnitude: G/R
	return Factor * Xv, Factor * Yv


def Simulate_Orbit_With_Tangential_Kick(
	G: float,
	R0: float,
	V0: float,
	V1: float,
	Kick_Time: float,
	Dt: float,
	T_Total: float,
) -> Tuple[Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, int]:

	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	X = float(R0)
	Y = 0.0

	# Start: Counterclockwise Tangential Direction at (R0, 0) is +Y
	Vx = 0.0
	Vy = float(V0)

	X_Array = Np.zeros(Step_Count)
	Y_Array = Np.zeros(Step_Count)
	Vx_Array = Np.zeros(Step_Count)
	Vy_Array = Np.zeros(Step_Count)
	T_Array = Np.arange(Step_Count) * Dt

	Kick_Step = int(round(Kick_Time / Dt))
	Kick_Step = max(0, min(Step_Count - 1, Kick_Step))

	Kick_Done = False

	for Step in range(Step_Count):
		# Kick: Instant Tangential Speed Increase
		if (not Kick_Done) and (Step >= Kick_Step):
			Speed = float(Np.hypot(Vx, Vy))
			if Speed > 0.0:
				Scale = float(V1 / Speed)
				Vx *= Scale
				Vy *= Scale
			Kick_Done = True

		Ax0, Ay0 = Acc(G, X, Y)

		X_New = X + Vx * Dt + 0.5 * Ax0 * Dt * Dt
		Y_New = Y + Vy * Dt + 0.5 * Ay0 * Dt * Dt

		Ax1, Ay1 = Acc(G, X_New, Y_New)

		Vx += 0.5 * (Ax0 + Ax1) * Dt
		Vy += 0.5 * (Ay0 + Ay1) * Dt

		X, Y = X_New, Y_New

		X_Array[Step] = X
		Y_Array[Step] = Y
		Vx_Array[Step] = Vx
		Vy_Array[Step] = Vy

	return X_Array, Y_Array, Vx_Array, Vy_Array, T_Array, Kick_Step


def Make_Kick_Animation(
	G: float,
	R0: float,
	V0: float,
	V1: float,
	Kick_Time: float,
	Output_Dir: Path,
	Name_Base: str,
	Dt: float = 0.01,
	Fps: int = 25,
	Time_Scale: float = 2.0,
	Orbits_After_Kick: float = 2.5,
) -> None:

	# Baseline Circular Period (Model: v^2 = G)
	T_Orbit = 2.0 * Np.pi * R0 / V0

	# Total Time: One Orbit Before Kick + Some Orbits After Kick
	T_Total = max(Kick_Time + Orbits_After_Kick * T_Orbit, 1.2 * T_Orbit)

	X, Y, Vx, Vy, T, Kick_Step = Simulate_Orbit_With_Tangential_Kick(
		G=G,
		R0=R0,
		V0=V0,
		V1=V1,
		Kick_Time=Kick_Time,
		Dt=Dt,
		T_Total=T_Total,
	)

	Frame_Count = int(Np.ceil((T_Total / Time_Scale) * Fps)) + 1
	T_Video = Np.arange(Frame_Count) / Fps
	T_Phys = T_Video * Time_Scale

	Idx = Np.clip((T_Phys / Dt).astype(int), 0, len(T) - 1)

	Xf = X[Idx]
	Yf = Y[Idx]
	Vxf = Vx[Idx]
	Vyf = Vy[Idx]
	Tf = T[Idx]

	# Plot Limits: Adaptive by Max Radius
	R_Array = Np.hypot(X, Y)
	R_Max = float(Np.max(R_Array))
	Limit = max(R_Max * 1.15, R0 * 1.8)

	Fig = Plt.figure(figsize=(10, 10))
	Ax = Fig.add_subplot(1, 1, 1)
	Ax.set_aspect("equal", adjustable="box")
	Ax.set_xlim(-Limit, Limit)
	Ax.set_ylim(-Limit, Limit)
	Ax.set_xlabel("x")
	Ax.set_ylabel("y")
	Ax.set_title("R=4: Tangential Kick (V: 8 → 9)")

	# Sun
	Ax.scatter([0], [0], s=700, c="yellow", edgecolors="black", zorder=3)

	# Reference Circle (Initial Orbit)
	Theta = Np.linspace(0.0, 2.0 * Np.pi, 600)
	Ax.plot(R0 * Np.cos(Theta), R0 * Np.sin(Theta), alpha=0.15)

	# Artists
	Trail, = Ax.plot([], [], alpha=0.7)
	Body, = Ax.plot([], [], "o")
	Kick_Marker, = Ax.plot([], [], "o", markersize=10, alpha=0.0)

	Info = Fig.text(
		0.02, 0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	TX = []
	TY = []
	Kick_Shown = False

	Kick_X = float(X[Kick_Step])
	Kick_Y = float(Y[Kick_Step])

	def Init():
		TX.clear()
		TY.clear()
		Body.set_data([], [])
		Trail.set_data([], [])
		Kick_Marker.set_alpha(0.0)
		return []

	def Update(F: int):
		nonlocal Kick_Shown

		x = float(Xf[F])
		y = float(Yf[F])
		vx = float(Vxf[F])
		vy = float(Vyf[F])
		t = float(Tf[F])

		speed = float(Np.hypot(vx, vy))
		r = float(Np.hypot(x, y))

		TX.append(x)
		TY.append(y)

		Body.set_data(x, y)
		Trail.set_data(TX, TY)

		# Show Kick Marker Once (At/After Kick Time)
		if (not Kick_Shown) and (Idx[F] >= Kick_Step):
			Kick_Marker.set_data([Kick_X], [Kick_Y])
			Kick_Marker.set_alpha(0.9)
			Kick_Shown = True

		Info.set_text(
			f"G = {G:g}\n"
			f"R0 = {R0:g}\n"
			f"Kick_Time = {Kick_Time:g} s\n"
			f"t_phys = {t:6.2f} s\n"
			f"Speed = {speed:5.2f}\n"
			f"Radius = {r:5.2f}"
		)

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


def Main() -> None:
	Output_Dir = Path("031-Orbit-Kick-R4")
	Output_Dir.mkdir(exist_ok=True)

	Make_Kick_Animation(
		G=64.0,
		R0=4.0,
		V0=8.0,
		V1=9.0,
		Kick_Time=2.0,          # Seconds: Kick Moment
		Output_Dir=Output_Dir,
		Name_Base="r4_kick_v8_to_v9",
		Dt=0.01,
		Fps=25,
		Time_Scale=2.0,
		Orbits_After_Kick=20.0,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()

