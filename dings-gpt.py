#!/usr/bin/env python3
# dings-gpt.py
# Tool For Working With Dings And GPT-Generated Artifacts
# Python 3.8 Compatible

import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _Print(Line: str = "") -> None:
	print(Line)


def _Die(Message: str) -> None:
	raise SystemExit(Message)


def _Is_Option(Token: str) -> bool:
	return Token.startswith("-")


def _Match_Command(Token: str, Command_List: List[str]) -> str:
	Token_Lower = Token.lower()
	Matches = [Cmd for Cmd in Command_List if Cmd.lower().startswith(Token_Lower)]
	if len(Matches) == 1:
		return Matches[0]
	Exact = [Cmd for Cmd in Command_List if Cmd.lower() == Token_Lower]
	if len(Exact) == 1:
		return Exact[0]
	_Die(f"Unknown Or Ambiguous Command: {Token!r}. Possible: {', '.join(Command_List)}")
	return ""


def _Parse_Options(
	Arg_List: List[str],
	Option_Name_List: List[str],
) -> Tuple[Dict[str, Optional[str]], List[str]]:
	Options: Dict[str, Optional[str]] = {}
	Rest: List[str] = []
	Index = 0
	Allowed_Lower = [O.lower() for O in Option_Name_List]

	while Index < len(Arg_List):
		Token = Arg_List[Index]
		if not _Is_Option(Token):
			Rest = Arg_List[Index:]
			break

		Name = Token.lstrip("-")
		Name_Lower = Name.lower()

		if Name_Lower in ("h", "help"):
			Options["help"] = None
			Index += 1
			continue
		if Name_Lower in ("v", "verbose"):
			Options["verbose"] = None
			Index += 1
			continue

		if Name_Lower not in Allowed_Lower:
			_Die(f"Unknown Option: {Token!r}")

		if Index + 1 >= len(Arg_List):
			_Die(f"Missing Value For Option: {Token!r}")

		Value = Arg_List[Index + 1]
		if _Is_Option(Value):
			_Die(f"Missing Value For Option: {Token!r}")

		Options[Name_Lower] = Value
		Index += 2

	return Options, Rest


def _Find_Next_Free_Id(Start_Id: int, Directory: Path) -> int:
	Used = set()
	for Entry in Directory.iterdir():
		if Entry.is_file() and Entry.stem.isdigit():
			Used.add(int(Entry.stem))
	Current = Start_Id
	while Current in Used:
		Current += 1
	return Current


def _Write_Text(File_Path: Path, Text: str, Overwrite: bool, Verbose: bool) -> None:
	if File_Path.exists() and not Overwrite:
		_Die(f"Refusing To Overwrite Existing File: {File_Path}")
	File_Path.write_text(Text, encoding="utf-8")
	if Verbose:
		_Print(f"Written: {File_Path}")


def _Copy_Move_Link(Source_Path: Path, Target_Path: Path, Mode: str, Verbose: bool) -> None:
	if Target_Path.exists():
		_Die(f"Target Already Exists: {Target_Path}")

	if Mode == "copy":
		shutil.copy2(Source_Path, Target_Path)
		if Verbose:
			_Print(f"Copied: {Source_Path} -> {Target_Path}")
	elif Mode == "move":
		shutil.move(str(Source_Path), str(Target_Path))
		if Verbose:
			_Print(f"Moved: {Source_Path} -> {Target_Path}")
	elif Mode == "link":
		Target_Path.symlink_to(Source_Path.resolve())
		if Verbose:
			_Print(f"Linked: {Target_Path} -> {Source_Path.resolve()}")
	else:
		_Die(f"Unknown Mode: {Mode!r}. Expected: copy, move, link")


def _Sidecar_Create_Text_Md(
	Title: str,
	Dings_Id: int,
	Creator_Id: int,
	Data_File_Name: str,
) -> str:
	Data_Ext = Path(Data_File_Name).suffix
	return (
		f"# {Title}\n\n"
		f"I am a [Text](200200000.md).\n\n"
		f"## About\n\n"
		f"- My [Creator](60106.md) is [{Creator_Id}.md]({Creator_Id}.md).\n\n"
		f"## Data\n\n"
		f"![]({Dings_Id}{Data_Ext})\n"
	)


def _Help_Top() -> None:
	_Print("Dings-Gpt [COMMAND]")
	_Print("")
	_Print("Tool for working with Dings and GPT-related Helpers.")
	_Print("")
	_Print("Options:")
	_Print("  -help: Print Description of Command")
	_Print("  -verbose: Print verbose Messages")
	_Print("")
	_Print("Commands:")
	_Print("   Import: Import Data")


def _Help_Import() -> None:
	_Print("Dings-Gpt Import [COMMAND]")
	_Print("")
	_Print("Import Data")
	_Print("")
	_Print("Options:")
	_Print("  -help: Print Description of Command")
	_Print("  -verbose: Print verbose Messages")
	_Print("")
	_Print("Commands:")
	_Print("   Text: Import Text")


def _Help_Import_Text() -> None:
	_Print("Dings-Gpt Import Text [COMMAND]")
	_Print("")
	_Print("Import Text")
	_Print("")
	_Print("Options:")
	_Print("  -help: Print Description of Command")
	_Print("  -verbose: Print verbose Messages")
	_Print("")
	_Print("Commands:")
	_Print("   File: Import Text File")


def _Help_Import_Text_File() -> None:
	_Print("Dings-Gpt Import Text File [COMMAND]")
	_Print("")
	_Print("Import Text File And Create Side-Car")
	_Print("")
	_Print("Options:")
	_Print("  -help: Print Description of Command")
	_Print("  -verbose: Print verbose Messages")
	_Print("  -start-id: First Dings-Id Candidate")
	_Print("  -creator: Dings-Id Of Creator (Usually a Program Dings)")
	_Print("  -mode: copy|move|link (Default: copy)")
	_Print("  -title: Title For Side-Car Markdown (Default: Original File-Name)")
	_Print("  -overwrite: 0|1 (Default: 0) Overwrite Existing Side-Car")
	_Print("")
	_Print("Args:")
	_Print("  <file>: Path To Text File")


def _Cmd_Import_Text_File(Arg_List: List[str]) -> None:
	Options, Rest = _Parse_Options(
		Arg_List,
		Option_Name_List=["start-id", "creator", "mode", "title", "overwrite"],
	)

	Verbose = "verbose" in Options
	if "help" in Options or not Rest:
		_Help_Import_Text_File()
		return

	Start_Id_Str = Options.get("start-id")
	Creator_Str = Options.get("creator")

	if Start_Id_Str is None:
		_Die("Missing Option: -start-id")
	if Creator_Str is None:
		_Die("Missing Option: -creator")

	Start_Id = int(Start_Id_Str)
	Creator_Id = int(Creator_Str)

	Mode = (Options.get("mode") or "copy").lower()
	Title = Options.get("title")
	Overwrite = (Options.get("overwrite") or "0") in ("1", "true", "yes")

	Source_Path = Path(Rest[0])
	if not Source_Path.exists():
		_Die(f"File Not Found: {Source_Path}")

	Dir_Path = Path(".").resolve()
	Next_Id = _Find_Next_Free_Id(Start_Id, Dir_Path)

	Target_Data_Path = Dir_Path / f"{Next_Id}{Source_Path.suffix}"
	Target_Md_Path = Dir_Path / f"{Next_Id}.md"

	_Copy_Move_Link(Source_Path, Target_Data_Path, Mode=Mode, Verbose=Verbose)

	Title_Final = Title if Title else Source_Path.name
	Md_Text = _Sidecar_Create_Text_Md(
		Title=Title_Final,
		Dings_Id=Next_Id,
		Creator_Id=Creator_Id,
		Data_File_Name=Target_Data_Path.name,
	)
	_Write_Text(Target_Md_Path, Md_Text, Overwrite=Overwrite, Verbose=Verbose)

	_Print(f"Created Dings {Next_Id}")
	_Print(f"- {Target_Data_Path.name}")
	_Print(f"- {Target_Md_Path.name}")


def Main() -> None:
	Arg_List = sys.argv[1:]
	if not Arg_List:
		_Help_Top()
		return

	Top_Options, Rest = _Parse_Options(Arg_List, Option_Name_List=[])
	if "help" in Top_Options:
		_Help_Top()
		return

	if not Rest:
		_Help_Top()
		return

	Top_Command = _Match_Command(Rest[0], ["Import"])
	Sub_Arg_List = Rest[1:]

	if Top_Command == "Import":
		Sub_Options, Sub_Rest = _Parse_Options(Sub_Arg_List, Option_Name_List=[])
		if "help" in Sub_Options or not Sub_Rest:
			_Help_Import()
			return
		Sub_Command = _Match_Command(Sub_Rest[0], ["Text"])
		Sub2_Arg_List = Sub_Rest[1:]

		if Sub_Command == "Text":
			Sub2_Options, Sub2_Rest = _Parse_Options(Sub2_Arg_List, Option_Name_List=[])
			if "help" in Sub2_Options or not Sub2_Rest:
				_Help_Import_Text()
				return
			Leaf_Command = _Match_Command(Sub2_Rest[0], ["File"])
			Leaf_Arg_List = Sub2_Rest[1:]
			if Leaf_Command == "File":
				_Cmd_Import_Text_File(Leaf_Arg_List)
				return

	_Die("Unhandled Command")


if __name__ == "__main__":
	Main()
