#!/bin/bash
set -e

Clean_Up=False

if ! $Clean_Up; then
	echo "Clean_Up"
fi


echo "=== dings-gpt self import ==="

dings-gpt.exe import text file \
	-start-id 400007010 \
	-about-file dings-gpt.about \
	010-Plot-B-vs-A.py

if $Clean_Up; then
	rm 400007010.*
	echo "OK: 010-Plot-B-vs-A.py imported"
fi

echo
echo "=== alias test ==="

dings-gpt.exe import text file \
	-start-id 400007020 \
	-about-file dings-gpt.about \
	-alias 020-Radial-Fall-Movie \
	020-Radial-Fall-Movie.py

if [ ! -L 020-Radial-Fall-Movie ]; then
	echo "ERROR: alias '020-Radial-Fall-Movie' was not created"
	exit 1
fi

TARGET="$(readlink 020-Radial-Fall-Movie)"
echo "Alias points to: $TARGET"

if [[ "$TARGET" != *.md ]]; then
	echo "ERROR: alias does not point to *.md"
	exit 1
fi

if $Clean_Up; then
	rm 400007020.*
	rm 020-Radial-Fall-Movie
fi

echo "OK: alias created correctly"


echo
echo "=== program import without alias ==="

dings-gpt.exe import text file \
	-start-id 400007030 \
	-about-file dings-gpt.about \
	030-Circular-Orbit.py

if $Clean_Up; then
	rm 400007030.*
fi

echo "OK: program imported without alias"


echo
echo "=== manual about syntax test ==="

dings-gpt.exe import text file \
	-start-id 400007040 \
	-about "600051.md=10000000" \
	-about "60106=[Chat-GPT-5.2](9000150)" \
	-about "60106=0" \
	050-Circular-Orbit-Forces-R64_F1.py

if $Clean_Up; then
	rm 400007040.*
fi

echo "OK: manual -about syntax accepted"

echo
echo "=== ALL TESTS PASSED ==="

