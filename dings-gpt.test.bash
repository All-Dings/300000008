#!/bin/bash
set -euo pipefail

# dings-gpt.import-simulations.bash
# Batch Import of Simulation Programs into All-Dings (Flat Directory)
#
# Usage:
#   ./dings-gpt.import-simulations.bash [OPTIONS]
#
# Options:
#   -bin DINGS_GPT_BIN   Path To dings-gpt Binary (Default: dings-gpt)
#   -about ABOUT_FILE   Path To .about File (Default: dings-gpt.about)
#   -cleanup 0|1        Remove Created Files After Import (Default: 0)
#   -verbose 0|1        Enable Verbose Mode (Default: 0)
#   -help               Show This Help
#
# Env (fallbacks):
#   DINGS_GPT_BIN, ABOUT_FILE, CLEAN_UP, VERBOSE
#
# Notes:
# - Options MUST come before the file argument (dings-host style).
# - Pick START_ID values that do not collide with existing files.

DINGS_GPT_BIN="${DINGS_GPT_BIN:-dings-gpt.exe}"
ABOUT_FILE="${ABOUT_FILE:-dings-gpt.about}"
CLEAN_UP="${CLEAN_UP:-0}"
VERBOSE="${VERBOSE:-0}"

_Show_Help() {
	grep '^#' "$0" | sed 's/^# //'
	exit 0
}

# ------------------------------------------------------------
# Parse CLI Options
# ------------------------------------------------------------
while [[ $# -gt 0 ]]; do
	case "$1" in
		-help|-h)
			_Show_Help
			;;
		-bin)
			DINGS_GPT_BIN="$2"
			shift 2
			;;
		-about)
			ABOUT_FILE="$2"
			shift 2
			;;
		-cleanup)
			CLEAN_UP="$2"
			shift 2
			;;
		-verbose)
			VERBOSE="$2"
			shift 2
			;;
		*)
			break
			;;
	esac
done

Run_Import() {
	local START_ID="$1"
	local TITLE="$2"
	local ALIAS_NAME="$3"
	local FILE_PATH="$4"
	shift 4

	local EXTRA_ABOUT_ARGS=()
	if [[ "$#" -gt 0 ]]; then
		EXTRA_ABOUT_ARGS=("$@")
	fi

	local CMD=("$DINGS_GPT_BIN" import text file "-start-id" "$START_ID" "-about-file" "$ABOUT_FILE" "-title" "$TITLE")
	if [[ "$VERBOSE" == "1" ]]; then
		CMD+=("-verbose")
	fi
	if [[ "${#EXTRA_ABOUT_ARGS[@]}" -gt 0 ]]; then
		for A in "${EXTRA_ABOUT_ARGS[@]}"; do
			CMD+=("-about" "$A")
		done
	fi
	if [[ -n "$ALIAS_NAME" ]]; then
		CMD+=("-alias" "$ALIAS_NAME")
	fi
	CMD+=("$FILE_PATH")

	echo
	echo "=== Import: $FILE_PATH (START_ID=$START_ID) ==="
	echo "+ ${CMD[*]}"
	"${CMD[@]}"

	if [[ -n "$ALIAS_NAME" ]]; then
		if [[ ! -L "$ALIAS_NAME" ]]; then
			echo "ERROR: alias '$ALIAS_NAME' was not created"
			exit 1
		fi
		local TARGET
		TARGET="$(readlink "$ALIAS_NAME")"
		echo "Alias points to: $TARGET"
		if [[ "$TARGET" != *.md ]]; then
			echo "ERROR: alias does not point to *.md"
			exit 1
		fi
	fi

	if [[ "$CLEAN_UP" == "1" ]]; then
		rm -f "${START_ID}.md" "${START_ID}.py" || true
		if [[ -n "$ALIAS_NAME" ]]; then
			rm -f "$ALIAS_NAME" || true
		fi
		echo "Cleaned: ${START_ID}.md/.py ${ALIAS_NAME}"
	fi
}

# --------------------------------------------------------------------
# Batch List
# --------------------------------------------------------------------

Run_Import "400007010" "010-Plot-B-vs-A.py" "" "010-Plot-B-vs-A.py"
Run_Import "400007020" "020-Radial-Fall-Movie.py" "020-Radial-Fall-Movie" "020-Radial-Fall-Movie.py"
Run_Import "400007030" "030-Circular-Orbit.py" "" "030-Circular-Orbit.py"
Run_Import "400007040" "050-Circular-Orbit-Forces-R64_F1.py" "" "050-Circular-Orbit-Forces-R64_F1.py" \
       "600051=10000000" \
       "60106=[Chat-GPT-5.2](9000150)" \
       60106=0

echo
echo "=== ALL IMPORTS DONE ==="
