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


def Circular_Speed_Newton(
	G: float,
	R_Start: float,
) -> float:
	return math.sqrt(G / max(1e-12, R_Start))


def Unit_Tangent_2D(
	X: float,
	Y: float,
) -> Tuple[float, float]:

	R = float(math.hypot(X, Y))
	Tx = -Y / R
	Ty = X / R
	return Tx, Ty


def Potential_GR_Effective(
	G: float,
	C: float,
	R: float,
	L2: float,
) -> float:
	# Potential: Newton + Schwarzschild-Correction (Weak-Field, 1PN, Planar Effective Term)
	# U = -G/r - G*L^2/(c^2*r^3)
	return -G / R - (G * L2) / ((C * C) * (R ** 3))


def Acc_Vector_GR_Approx(
	G: float,
	C: float,
	Pos: Np.ndarray,
	Vel: Np.ndarray,
) -> Np.ndarray:
	"""
	Schwarzschild Weak-Field Approximation (Planar, 1PN Effective Term):
	a = -G * r / r^3  -  3*G*L^2/(c^2*r^5) * r
	"""

	R = float(Np.linalg.norm(Pos))
	R3 = R ** 3

	A_Newton = (-G) * Pos / R3

	L_Vec = Np.cross(Pos, Vel)
	L2 = float(Np.dot(L_Vec, L_Vec))

	A_GR = (-3.0 * G * L2 / ((C * C) * (R ** 5))) * Pos

	return A_Newton + A_GR


def Energy_Lz_Speed_GR_Effective(
	G: float,
	C: float,
	Pos: Np.ndarray,
	Vel: Np.ndarray,
) -> Tuple[float, float, float]:

	R = float(Np.linalg.norm(Pos))
	Speed = float(Np.linalg.norm(Vel))

	L_Vec = Np.cross(Pos, Vel)
	L2 = float(Np.dot(L_Vec, L_Vec))
	Lz = float(L_Vec[2])

	E = 0.5 * Speed * Speed + Potential_GR_Effective(G, C, R, L2)

	return E, Lz, Speed


def Simulate_Orbit_GR_With_Tangential_Kick(
	G: float,
	C: float,
	R_Start: float,
	V0: float,
	V1: float,
	T_Kick: float,
	Dt: float,
	T_Total: float,
):

	Dim = 3
	Step_Count = int(Np.ceil(T_Total / Dt)) + 1

	Pos = Np.zeros(Dim, dtype=float)
	Vel = Np.zeros(Dim, dtype=float)

	Pos[0] = float(R_Start)
	Vel[1] = float(V0)

	Pos_Array = Np.zeros((Step_Count, Dim), dtype=float)
	Vel_Array = Np.zeros((Step_Count, Dim), dtype=float)
	E_Array = Np.zeros(Step_Count, dtype=float)
	Lz_Array = Np.zeros(Step_Count, dtype=float)
	S_Array = Np.zeros(Step_Count, dtype=float)
	T_Array = Np.arange(Step_Count, dtype=float) * Dt

	Kick_Step = int(round(T_Kick / Dt))
	Kick_Step = max(0, min(Step_Count - 1, Kick_Step))
	Kick_Done = False

	for Step in range(Step_Count):
		if (not Kick_Done) and (Step >= Kick_Step):
			Speed0 = float(Np.linalg.norm(Vel))
			if Speed0 > 0.0:
				Vel *= (V1 / Speed0)
			Kick_Done = True

		Acc0 = Acc_Vector_GR_Approx(G, C, Pos, Vel)

		Pos_New = Pos + Vel * Dt + 0.5 * Acc0 * Dt * Dt
		Acc1 = Acc_Vector_GR_Approx(G, C, Pos_New, Vel)

		Vel = Vel + 0.5 * (Acc0 + Acc1) * Dt
		Pos = Pos_New

		E, Lz, Speed = Energy_Lz_Speed_GR_Effective(G, C, Pos, Vel)

		Pos_Array[Step, :] = Pos
		Vel_Array[Step, :] = Vel
		E_Array[Step] = E
		Lz_Array[Step] = Lz
		S_Array[Step] = Speed

	return Pos_Array, Vel_Array, E_Array, Lz_Array, S_Array, T_Array, Kick_Step


def Make_GR_Animation(
	G: float,
	C: float,
	R_Start: float,
	V0: float,
	V1: float,
	T_Kick: float,
	Output_Dir: Path,
	Name_Base: str,
	Dt: float = 0.01,
	Fps: int = 25,
	Time_Scale: float = 2.0,
	Orbits_After_Kick: float = 6.0,
	Comet_Distance_Behind: float = 7.0,
	Comet_Appear_Delta_T: float = 1.0,
) -> None:

	T_Orbit = 2.0 * math.pi * R_Start / max(1e-9, V0)
	T_Total = max(T_Kick + Orbits_After_Kick * T_Orbit, 1.2 * T_Orbit)

	Pos, Vel, E, Lz, S, T, Kick_Step = Simulate_Orbit_GR_With_Tangential_Kick(
		G=G,
		C=C,
		R_Start=R_Start,
		V0=V0,
		V1=V1,
		T_Kick=T_Kick,
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
	Limit = max(R_Max * 1.15, R_Start * 1.8)

	Kick_X = float(Pos[Kick_Step, 0])
	Kick_Y = float(Pos[Kick_Step, 1])

	Tan_X, Tan_Y = Unit_Tangent_2D(Kick_X, Kick_Y)

	Comet_T_Start = max(0.0, T_Kick - Comet_Appear_Delta_T)
	Comet_V = Comet_Distance_Behind / max(1e-9, (T_Kick - Comet_T_Start))

	Comet_Xf = Np.full(Frame_Count, Np.nan)
	Comet_Yf = Np.full(Frame_Count, Np.nan)

	for i in range(Frame_Count):
		tp = float(T_Phys[i])
		if tp < Comet_T_Start:
			continue
		if tp <= T_Kick:
			d = (T_Kick - tp) * Comet_V
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
	Ax_Orbit.set_xlabel("X")
	Ax_Orbit.set_ylabel("Y")
	Ax_Orbit.set_title("GR Approx (Schwarzschild 1PN): Kick With Comet (V: {0:g} → {1:g})".format(V0, V1))

	Ax_Orbit.scatter([0.0], [0.0], s=700, c="yellow", edgecolors="black", zorder=5)

	Theta = Np.linspace(0.0, 2.0 * math.pi, 600)
	Ax_Orbit.plot(R_Start * Np.cos(Theta), R_Start * Np.sin(Theta), alpha=0.15)

	Trail, = Ax_Orbit.plot([], [], alpha=0.65)
	Body, = Ax_Orbit.plot([], [], "o", markersize=10)
	Comet, = Ax_Orbit.plot([], [], "o", markersize=7)
	Kick_Marker, = Ax_Orbit.plot([], [], "o", markersize=11, alpha=0.0)

	Ax_E.plot(Tf, Ef, alpha=0.35)
	Ax_L.plot(Tf, Lf, alpha=0.35)
	Ax_S.plot(Tf, Sf, alpha=0.35)

	for Ax in (Ax_E, Ax_L, Ax_S):
		Ax.axvline(T_Kick, alpha=0.4)
		Ax.set_xlabel("T")

	Ax_E.set_ylabel("E_Sum")
	Ax_L.set_ylabel("L_Spin (Lz)")
	Ax_S.set_ylabel("V_Cur")

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
		T_Phys = float(Tf[F])

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

		E_Sum = float(Ef[F])
		L_Spin = float(Lf[F])
		V_Cur = float(Sf[F])
		R_Cur = float(math.hypot(x, y))

		E_Cursor.set_data([T_Phys], [E_Sum])
		L_Cursor.set_data([T_Phys], [L_Spin])
		S_Cursor.set_data([T_Phys], [V_Cur])

		Info.set_text(
			"G       = {0:>7.2f} GU\n"
			"C       = {2:>7.2f} VU\n"
			"T_Scale = {1:>7.2f} ×\n"
			"R_Start = {3:>7.2f} SU\n"
			"T_Kick  = {4:>7.2f} Sec\n"
			"\n"
			"T_Phys  = {5:>7.2f} Sec\n"
			"V_Cur   = {6:>7.2f} VU\n"
			"R_Cur   = {7:>7.2f} SU\n"
			"\n"
			"E_Sum   = {8:>7.4f} EU\n"
			"L_Spin  = {9:>7.4f} SU·VU"
			.format(G, Time_Scale, C, R_Start, T_Kick, T_Phys, V_Cur, R_Cur, E_Sum, L_Spin)
		)

		return []

	Anim = FuncAnimation(Fig, Update, frames=Frame_Count, init_func=Init, blit=False)

	Save_Animation_Gif_And_Mp4(Anim, Output_Dir, Name_Base, Fps)
	Plt.close(Fig)


# Choose C large for weak GR. Smaller C => stronger Precession (for Visualization).
def Make_GR_Animation_4_C(C: float) -> None:
	G = 64.0
	R_Start = 4.0

	V0 = Circular_Speed_Newton(G, R_Start)
	V1 = V0 + 1.0

	T_Kick = 2.0

	Output_Dir = Path("032-Orbit-Kick-ART")
	Output_Dir.mkdir(exist_ok=True)

	Make_GR_Animation(
		G=G,
		C=C,
		R_Start=R_Start,
		V0=V0,
		V1=V1,
		T_Kick=T_Kick,
		Output_Dir=Output_Dir,
		Name_Base=f"gr_kick_with_comet_Eeff_Lz_V-{C}",
		Dt=0.01,
		Fps=25,
		Time_Scale=6.0,
		Orbits_After_Kick=20.0,
		Comet_Distance_Behind=7.0,
		Comet_Appear_Delta_T=1.0,
	)

	print("Done. Files written to:", Output_Dir)

def Main() -> None:
	Make_GR_Animation_4_C(240.0)
	Make_GR_Animation_4_C(120.0)
	Make_GR_Animation_4_C(60.0)

if __name__ == "__main__":
	Main()
