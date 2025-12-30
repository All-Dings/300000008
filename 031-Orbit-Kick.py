#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from pathlib import Path
from typing import Tuple

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


def Potential(
	Dim: int,
	G: float,
	R: float,
) -> float:

	if Dim == 2:
		return G * math.log(R)
	return -G / float(Dim - 2) * (R ** (-(Dim - 2)))


def Acc_Vector(
	Dim: int,
	G: float,
	Pos: Np.ndarray,
) -> Np.ndarray:

	R = float(Np.linalg.norm(Pos))
	return (-G) * Pos / (R ** Dim)


def Energy_Lz_Speed(
	Dim: int,
	G: float,
	Pos: Np.ndarray,
	Vel: Np.ndarray,
) -> Tuple[float, float, float]:

	R = float(Np.linalg.norm(Pos))
	Speed = float(Np.linalg.norm(Vel))

	E = 0.5 * Speed * Speed + Potential(Dim, G, R)

	if Pos.shape[0] >= 2:
		Lz = float(Pos[0] * Vel[1] - Pos[1] * Vel[0])
	else:
		Lz = 0.0

	return E, Lz, Speed


def Circular_Speed(
	Dim: int,
	G: float,
	R0: float,
) -> float:

	if Dim == 2:
		return math.sqrt(G)
	return math.sqrt(G / (R0 ** (Dim - 2)))


def Unit_Tangent_2D(
	X: float,
	Y: float,
) -> Tuple[float, float]:

	R = float(math.hypot(X, Y))
	Tx = -Y / R
	Ty = X / R
	return Tx, Ty


def Simulate_With_Tangential_Kick(
	Dim: int,
	G: float,
	R0: float,
	V0: float,
	V1: float,
	Kick_Time: float,
	Dt: float,
	T_Total: float,
) -> Tuple[Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, Np.ndarray, int]:

	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	Pos = Np.zeros(Dim, dtype=float)
	Vel = Np.zeros(Dim, dtype=float)

	Pos[0] = float(R0)
	Vel[1] = float(V0)

	Pos_Array = Np.zeros((Step_Count, Dim), dtype=float)
	Vel_Array = Np.zeros((Step_Count, Dim), dtype=float)
	E_Array = Np.zeros(Step_Count, dtype=float)
	Lz_Array = Np.zeros(Step_Count, dtype=float)
	S_Array = Np.zeros(Step_Count, dtype=float)
	T_Array = Np.arange(Step_Count, dtype=float) * Dt

	Kick_Step = int(round(Kick_Time / Dt))
	Kick_Step = max(0, min(Step_Count - 1, Kick_Step))
	Kick_Done = False

	for Step in range(Step_Count):
		if (not Kick_Done) and (Step >= Kick_Step):
			Speed0 = float(Np.linalg.norm(Vel))
			if Speed0 > 0.0:
				Vel *= (V1 / Speed0)
			Kick_Done = True

		Acc0 = Acc_Vector(Dim, G, Pos)

		Pos_New = Pos + Vel * Dt + 0.5 * Acc0 * Dt * Dt
		Acc1 = Acc_Vector(Dim, G, Pos_New)

		Vel = Vel + 0.5 * (Acc0 + Acc1) * Dt
		Pos = Pos_New

		E, Lz, Speed = Energy_Lz_Speed(Dim, G, Pos, Vel)

		Pos_Array[Step, :] = Pos
		Vel_Array[Step, :] = Vel
		E_Array[Step] = E
		Lz_Array[Step] = Lz
		S_Array[Step] = Speed

	return Pos_Array, Vel_Array, E_Array, Lz_Array, S_Array, T_Array, Kick_Step


def Make_Animation(
	Dim: int,
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

	if Dim < 2:
		raise ValueError("Dim must be >= 2 for the Orbit Plot and Lz.")

	T_Orbit = 2.0 * math.pi * R0 / max(1e-9, V0)
	T_Total = max(Kick_Time + Orbits_After_Kick * T_Orbit, 1.2 * T_Orbit)

	Pos, Vel, E, Lz, S, T, Kick_Step = Simulate_With_Tangential_Kick(
		Dim=Dim,
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

	Xf = Pos[Idx, 0]
	Yf = Pos[Idx, 1]
	Ef = E[Idx]
	Lf = Lz[Idx]
	Sf = S[Idx]
	Tf = T[Idx]

	R_Array = Np.linalg.norm(Pos, axis=1)
	R_Max = float(Np.max(R_Array))
	Limit = max(R_Max * 1.15, R0 * 1.8)

	Kick_X = float(Pos[Kick_Step, 0])
	Kick_Y = float(Pos[Kick_Step, 1])

	Tan_X, Tan_Y = Unit_Tangent_2D(Kick_X, Kick_Y)

	Comet_T_Start = max(0.0, Kick_Time - Comet_Appear_Delta_T)
	Comet_V = Comet_Distance_Behind / max(1e-9, (Kick_Time - Comet_T_Start))

	Comet_Xf = Np.full(Frame_Count, Np.nan)
	Comet_Yf = Np.full(Frame_Count, Np.nan)

	for i in range(Frame_Count):
		tp = float(T_Phys[i])
		if tp < Comet_T_Start:
			continue
		if tp <= Kick_Time:
			d = (Kick_Time - tp) * Comet_V
			Comet_Xf[i] = Kick_X - d * Tan_X
			Comet_Yf[i] = Kick_Y - d * Tan_Y

	Fig = Plt.figure(figsize=(16, 9))
	Gs = Fig.add_gridspec(3, 2, width_ratios=[1.35, 1.0])

	Ax_Orbit = Fig.add_subplot(Gs[:, 0])
	Ax_E = Fig.add_subplot(Gs[0, 1])
	Ax_L = Fig.add_subplot(Gs[1, 1])
	Ax_S = Fig.add_subplot(Gs[2, 1])

	Ax_Orbit.set_aspect("equal", adjustable="box")
	Ax_Orbit.set_xlim(-Limit, Limit)
	Ax_Orbit.set_ylim(-Limit, Limit)
	Ax_Orbit.set_xlabel("x")
	Ax_Orbit.set_ylabel("y")
	Ax_Orbit.set_title("Dim={0}: Tangential Kick With Comet (V: {1:g} → {2:g})".format(Dim, V0, V1))

	Ax_Orbit.scatter([0.0], [0.0], s=700, c="yellow", edgecolors="black", zorder=5)

	Theta = Np.linspace(0.0, 2.0 * math.pi, 600)
	Ax_Orbit.plot(R0 * Np.cos(Theta), R0 * Np.sin(Theta), alpha=0.15)

	Trail, = Ax_Orbit.plot([], [], alpha=0.65)
	Body, = Ax_Orbit.plot([], [], "o", markersize=10)
	Comet, = Ax_Orbit.plot([], [], "o", markersize=7)
	Kick_Marker, = Ax_Orbit.plot([], [], "o", markersize=11, alpha=0.0)

	Ax_E.plot(Tf, Ef, alpha=0.35)
	Ax_L.plot(Tf, Lf, alpha=0.35)
	Ax_S.plot(Tf, Sf, alpha=0.35)

	for Ax in (Ax_E, Ax_L, Ax_S):
		Ax.axvline(Kick_Time, alpha=0.4)
		Ax.set_xlabel("t")

	Ax_E.set_ylabel("E")
	Ax_L.set_ylabel("Lz")
	Ax_S.set_ylabel("V")

	E_Cursor, = Ax_E.plot([], [], "o")
	L_Cursor, = Ax_L.plot([], [], "o")
	S_Cursor, = Ax_S.plot([], [], "o")

	Info = Fig.text(
		0.02, 0.98,
		"",
		va="top",
		ha="left",
		fontsize=11,
		family="monospace",
		bbox=dict(
			boxstyle="round,pad=0.4",
			facecolor="#E6E6E6",
			edgecolor="black",
			alpha=0.95,
		)
	)

	TX = []
	TY = []
	Kick_Shown = False

	def Init():
		nonlocal Kick_Shown
		TX.clear()
		TY.clear()
		Kick_Shown = False
		Trail.set_data([], [])
		Body.set_data([], [])
		Comet.set_data([], [])
		Kick_Marker.set_alpha(0.0)
		E_Cursor.set_data([], [])
		L_Cursor.set_data([], [])
		S_Cursor.set_data([], [])
		Info.set_text("")
		return []

	def Update(F: int):
		nonlocal Kick_Shown

		x = float(Xf[F])
		y = float(Yf[F])
		t = float(Tf[F])

		TX.append(x)
		TY.append(y)

		Body.set_data([x], [y])
		Trail.set_data(TX, TY)

		cx = float(Comet_Xf[F])
		cy = float(Comet_Yf[F])
		if Np.isfinite(cx) and Np.isfinite(cy):
			Comet.set_data([cx], [cy])
		else:
			Comet.set_data([], [])

		if (not Kick_Shown) and (Idx[F] >= Kick_Step):
			Kick_Marker.set_data([Kick_X], [Kick_Y])
			Kick_Marker.set_alpha(0.9)
			Kick_Shown = True

		e = float(Ef[F])
		l = float(Lf[F])
		v = float(Sf[F])
		r = float(math.hypot(x, y))

		E_Cursor.set_data([t], [e])
		L_Cursor.set_data([t], [l])
		S_Cursor.set_data([t], [v])

		Info.set_text(
			"Dim       = {0:>6d}\n"
			"G         = {1:>6.2f}\n"
			"R0        = {2:>6.2f}\n"
			"Kick_Time = {3:>6.2f}\n"
			"\n"
			"t_phys    = {4:>6.2f}\n"
			"Speed     = {5:>6.2f}\n"
			"Radius    = {6:>6.2f}\n"
			"\n"
			"E         = {7:>9.4f}\n"
			"Lz        = {8:>9.4f}"
			.format(Dim, G, R0, Kick_Time, t, v, r, e, l)
		)

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


# Dim = 2, 3, or 4
def Make_Animation_4_Dim(Dim: int) -> None:

	G = 64.0
	R0 = 4.0

	V0 = Circular_Speed(Dim, G, R0)
	V1 = V0 + 1.0

	Kick_Time = 2.0

	Output_Dir = Path("031-Orbit-Kick-Dim{0}".format(Dim))
	Output_Dir.mkdir(exist_ok=True)

	Make_Animation(
		Dim=Dim,
		G=G,
		R0=R0,
		V0=V0,
		V1=V1,
		Kick_Time=Kick_Time,
		Output_Dir=Output_Dir,
		Name_Base="kick_with_comet_E_Lz_V_info",
		Dt=0.01,
		Fps=25,
		Time_Scale=2.0,
		Orbits_After_Kick=2.0,
		Comet_Distance_Behind=7.0,
		Comet_Appear_Delta_T=1.0,
	)

	print("Done. Files written to:", Output_Dir)

def Main() -> None:
	Make_Animation_4_Dim(2)
	Make_Animation_4_Dim(3)
	Make_Animation_4_Dim(4)

if __name__ == "__main__":
	Main()
