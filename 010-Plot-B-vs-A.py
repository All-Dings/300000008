#!/usr/bin/env python3
# Generate PNG plots with identical coordinate system
# including an initial empty plot

import numpy as Np
import matplotlib.pyplot as Plt
from pathlib import Path


def Setup_Axes(
	X_Min: float,
	X_Max: float,
	Y_Min: float,
	Y_Max: float,
) -> None:
	Plt.xlim(X_Min, X_Max)
	Plt.ylim(Y_Min, Y_Max)
	Plt.gca().set_aspect("equal", adjustable="box")
	Plt.xlabel("R")
	Plt.ylabel("B")
	Plt.grid(True, linestyle="--", alpha=0.5)


def Main() -> None:
	# Output directory
	Output_Dir = Path("010-Plot-B-vs-A")
	Output_Dir.mkdir(exist_ok=True)

	# Data
	R_Array = Np.array([1, 2, 4, 8, 16, 32, 64], dtype=float)
	B_Array = Np.array([64, 32, 16, 8, 4, 2, 1], dtype=float)

	# Function
	R_Function = Np.linspace(1.0, 64.0, 500)
	B_Function = 64.0 / R_Function

	# Fixed axes
	X_Min: float = 0.0
	X_Max: float = 70.0
	Y_Min: float = 0.0
	Y_Max: float = 70.0

	# --- Plot 0: empty coordinate system ---
	Plt.figure(figsize=(6, 6))
	Setup_Axes(X_Min, X_Max, Y_Min, Y_Max)
	Title = "B in Abhängigkeit von R"
	Plt.title(Title)
	File_Empty = Output_Dir / "B_vs_R_00_empty.png"
	Plt.savefig(File_Empty, dpi=300, bbox_inches="tight")
	Plt.close()
	print(f"Gespeichert: {File_Empty}")

	# --- Prefix plots: only data points ---
	for Length in range(1, len(B_Array) + 1):
		Plt.figure(figsize=(6, 6))
		Setup_Axes(X_Min, X_Max, Y_Min, Y_Max)

		Plt.scatter(
			R_Array[:Length],
			B_Array[:Length],
			s=80,
			c="black",
			zorder=3,
			label=f"Daten-Punkte (1–{Length})",
		)

		Plt.title(Title)
		Plt.legend()

		File_Name = Output_Dir / f"B_vs_R_{Length:02d}_points.png"
		Plt.savefig(File_Name, dpi=300, bbox_inches="tight")
		Plt.close()
		print(f"Gespeichert: {File_Name}")

	# --- Final plot: all data + function ---
	Plt.figure(figsize=(6, 6))
	Setup_Axes(X_Min, X_Max, Y_Min, Y_Max)

	Plt.scatter(
		R_Array,
		B_Array,
		s=80,
		c="black",
		zorder=3,
		label=f"Daten-Punkte (1–{Length})",
	)

	Plt.plot(
		R_Function,
		B_Function,
		linewidth=2,
		label=r"$B=64*\dfrac{1}{R}$",
	)

	Plt.title(Title)
	Plt.legend()

	File_Final = Output_Dir / "B_vs_R_08_all_with_function.png"
	Plt.savefig(File_Final, dpi=300, bbox_inches="tight")
	Plt.close()
	print(f"Gespeichert: {File_Final}")


if __name__ == "__main__":
	Main()

