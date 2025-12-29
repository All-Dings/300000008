#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from pathlib import Path
from typing import List, Tuple

import numpy as Np
import matplotlib
import matplotlib.pyplot as Plt
from matplotlib.animation import FuncAnimation, PillowWriter, FFMpegWriter

matplotlib.rcParams["text.usetex"] = False


def Save_Animation_Gif_And_Mp4(
	Anim: FuncAnimation,
	Output_Dir: Path,
	Name_Base: str,
	Fps: int,
) -> None:

	Gif_Path = Output_Dir / (Name_Base + ".gif")
	Mp4_Path = Output_Dir / (Name_Base + ".mp4")

	Anim.save(str(Gif_Path), writer=PillowWriter(fps=Fps))
	Anim.save(str(Mp4_Path), writer=FFMpegWriter(fps=Fps))

	print("Saved:", Gif_Path)
	print("Saved:", Mp4_Path)


def Acc(
	G: float,
	Xv: float,
	Yv: float,
) -> Tuple[float, float]:

	R = float(Np.hypot(Xv, Yv))
	Factor = -G / (R * R)
	return Factor * Xv, Factor * Yv


def Energy_And_Angular_Momentum(
	G: float,
	Xv: float,
	Yv: float,
	Vxv: float,
	Vyv: float,
) -> Tuple[float, float]:

	R = float(Np.hypot(Xv, Yv))
	E = 0.5 * (Vxv * Vxv + Vyv * Vyv) + G * math.log(R)
	L = Xv * Vyv - Yv * Vxv
	return E, L


def Unit_Tangent_At(
	Xv: float,
	Yv: float,
) -> Tuple[float, float]:

	R = float(Np.hypot(Xv, Yv))
	Tx = -Yv / R
	Ty = Xv / R
	return Tx, Ty


def Simulate_Orbit_With_Tangential_Kick(
	G: float,
	R0: float,
	V0: float,
	V1: float,
	Kick_Time: float,
	Dt: float,
	T_Total: float,
) -> Tuple[Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, int]:

	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	X = float(R0)
	Y = 0.0
	Vx = 0.0
	Vy = float(V0)

	X_Array = Np.zeros(Step_Count)
	Y_Array = Np.zeros(Step_Count)
	Vx_Array = Np.zeros(Step_Count)
	Vy_Array = Np.zeros(Step_Count)
	E_Array = Np.zeros(Step_Count)
	L_Array = Np.zeros(Step_Count)
	T_Array = Np.arange(Step_Count, dtype=float) * Dt

	Kick_Step = int(round(Kick_Time / Dt))
	Kick_Step = max(0, min(Step_Count - 1, Kick_Step))
	Kick_Done = False

	for Step in range(Step_Count):
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

		Vx = Vx + 0.5 * (Ax0 + Ax1) * Dt
		Vy = Vy + 0.5 * (Ay0 + Ay1) * Dt

		X = X_New
		Y = Y_New

		X_Array[Step] = X
		Y_Array[Step] = Y
		Vx_Array[Step] = Vx
		Vy_Array[Step] = Vy

		E, L = Energy_And_Angular_Momentum(G, X, Y, Vx, Vy)
		E_Array[Step] = E
		L_Array[Step] = L

	return X_Array, Y_Array, Vx_Array, Vy_Array, E_Array, L_Array, T_Array, Kick_Step


def Make_Kick_Animation_With_Comet_And_Conservation_Plots(
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
	Orbits_After_Kick: float = 3.0,
	Comet_Distance_Behind: float = 7.0,
	Comet_Appear_Delta_T: float = 1.0,
) -> None:

	T_Orbit = 2.0 * math.pi * R0 / V0
	T_Total = max(Kick_Time + Orbits_After_Kick * T_Orbit, 1.2 * T_Orbit)

	X, Y, Vx, Vy, E, L, T, Kick_Step = Simulate_Orbit_With_Tangential_Kick(
		G=G,
		R0=R0,
		V0=V0,
		V1=V1,
		Kick_Time=Kick_Time,
		Dt=Dt,
		T_Total=T_Total,
	)

	Frame_Count = int(Np.ceil((T_Total / Time_Scale) * Fps)) + 1
	T_Video = Np.arange(Frame_Count, dtype=float) / float(Fps)
	T_Phys = T_Video * float(Time_Scale)

	Idx = Np.clip((T_Phys / float(Dt)).astype(int), 0, len(T) - 1)

	Xf = X[Idx]
	Yf = Y[Idx]
	Vxf = Vx[Idx]
	Vyf = Vy[Idx]
	Ef = E[Idx]
	Lf = L[Idx]
	Tf = T[Idx]

	R_Array = Np.hypot(X, Y)
	R_Max = float(Np.max(R_Array))
	Limit = max(R_Max * 1.15, R0 * 1.8)

	Kick_X = float(X[Kick_Step])
	Kick_Y = float(Y[Kick_Step])

	Tan_X, Tan_Y = Unit_Tangent_At(Kick_X, Kick_Y)

	Comet_T_Start = max(0.0, Kick_Time - Comet_Appear_Delta_T)
	Comet_V = Comet_Distance_Behind / max(1e-9, (Kick_Time - Comet_T_Start))

	Comet_Xf = Np.full(Frame_Count, Np.nan, dtype=float)
	Comet_Yf = Np.full(Frame_Count, Np.nan, dtype=float)

	for i in range(Frame_Count):
		tp = float(T_Phys[i])
		if tp < Comet_T_Start:
			continue
		if tp <= Kick_Time:
			d = (Kick_Time - tp) * Comet_V
			Comet_Xf[i] = Kick_X - d * Tan_X
			Comet_Yf[i] = Kick_Y - d * Tan_Y

	# Figure Layout
	Fig = Plt.figure(figsize=(14, 8))
	Gs = Fig.add_gridspec(2, 2, width_ratios=[1.35, 1.0], height_ratios=[1.0, 1.0])

	Ax_Orbit = Fig.add_subplot(Gs[:, 0])
	Ax_E = Fig.add_subplot(Gs[0, 1])
	Ax_L = Fig.add_subplot(Gs[1, 1])

	Ax_Orbit.set_aspect("equal", adjustable="box")
	Ax_Orbit.set_xlim(-Limit, Limit)
	Ax_Orbit.set_ylim(-Limit, Limit)
	Ax_Orbit.set_xlabel("x")
	Ax_Orbit.set_ylabel("y")
	Ax_Orbit.set_title("R=4: Tangential Kick With Comet (V: 8 → 9)")

	Ax_Orbit.scatter([0.0], [0.0], s=700, c="yellow", edgecolors="black", zorder=5)

	Theta = Np.linspace(0.0, 2.0 * math.pi, 600)
	Ax_Orbit.plot(R0 * Np.cos(Theta), R0 * Np.sin(Theta), alpha=0.15)

	Trail, = Ax_Orbit.plot([], [], alpha=0.65)
	Body, = Ax_Orbit.plot([], [], "o", markersize=10)
	Comet, = Ax_Orbit.plot([], [], "o", markersize=7, alpha=0.9)
	Kick_Marker, = Ax_Orbit.plot([], [], "o", markersize=11, alpha=0.0)

	# Conservation Plots
	T_Line = Tf
	Ax_E.plot(T_Line, Ef, alpha=0.35)
	Ax_L.plot(T_Line, Lf, alpha=0.35)

	Ax_E.axvline(Kick_Time, alpha=0.4)
	Ax_L.axvline(Kick_Time, alpha=0.4)

	Ax_E.set_title("Energy E(t)")
	Ax_L.set_title("Angular Momentum L(t)")
	Ax_E.set_xlabel("t")
	Ax_L.set_xlabel("t")

	Ax_E.set_ylabel("E")
	Ax_L.set_ylabel("L")

	E_Cursor, = Ax_E.plot([], [], "o")
	L_Cursor, = Ax_L.plot([], [], "o")

	Info = Fig.text(
		0.02, 0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
	)

	TX_List = []
	TY_List = []
	Kick_Shown = False

	def Init():
		nonlocal Kick_Shown
		TX_List.clear()
		TY_List.clear()
		Kick_Shown = False

		Trail.set_data([], [])
		Body.set_data([], [])
		Comet.set_data([], [])
		Kick_Marker.set_alpha(0.0)

		E_Cursor.set_data([], [])
		L_Cursor.set_data([], [])

		return []

	def Update(F: int):
		nonlocal Kick_Shown

		x = float(Xf[F])
		y = float(Yf[F])
		vx = float(Vxf[F])
		vy = float(Vyf[F])
		e = float(Ef[F])
		l = float(Lf[F])
		t = float(Tf[F])

		speed = float(Np.hypot(vx, vy))
		r = float(Np.hypot(x, y))

		TX_List.append(x)
		TY_List.append(y)

		Body.set_data([x], [y])
		Trail.set_data(TX_List, TY_List)

		cx = float(Comet_Xf[F])
		cy = float(Comet_Yf[F])
		if Np.isfinite(cx) and Np.isfinite(cy):
			Comet.set_data([cx], [cy])
			Comet.set_alpha(0.9)
		else:
			Comet.set_data([], [])
			Comet.set_alpha(0.0)

		if (not Kick_Shown) and (Idx[F] >= Kick_Step):
			Kick_Marker.set_data([Kick_X], [Kick_Y])
			Kick_Marker.set_alpha(0.9)
			Kick_Shown = True

		E_Cursor.set_data([t], [e])
		L_Cursor.set_data([t], [l])

		Info.set_text(
			"G = {0:g}\n"
			"R0 = {1:g}\n"
			"Kick_Time = {2:g}\n"
			"t_phys = {3:6.2f}\n"
			"Speed = {4:5.2f}\n"
			"Radius = {5:5.2f}\n"
			"E = {6:9.4f}\n"
			"L = {7:9.4f}".format(G, R0, Kick_Time, t, speed, r, e, l)
		)

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


def Main() -> None:
	Output_Dir = Path("040-Orbit-Kick-R4")
	Output_Dir.mkdir(exist_ok=True)

	Make_Kick_Animation_With_Comet_And_Conservation_Plots(
		G=64.0,
		R0=4.0,
		V0=8.0,
		V1=9.0,
		Kick_Time=2.0,
		Output_Dir=Output_Dir,
		Name_Base="r4_kick_v8_to_v9_with_comet_energy_L",
		Dt=0.01,
		Fps=25,
		Time_Scale=2.0,
		Orbits_After_Kick=3.0,
		Comet_Distance_Behind=7.0,
		Comet_Appear_Delta_T=1.0,
	)

	print("Done. Files written to:", Output_Dir)


if __name__ == "__main__":
	Main()
