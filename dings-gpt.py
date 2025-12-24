#!/usr/bin/env python3
# dings-gpt.py
# Tool For Working With Dings And GPT-Generated Artifacts
# Python 3.8 Compatible

import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import re


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
) -> Tuple[Dict[str, Union[None, str, List[str]]], List[str]]:
	"""
	Parsing Rule: Options Must Come Before Positional Args.
	Exception: -about can occur multiple times and is collected into a List.
	"""
	Options: Dict[str, Union[None, str, List[str]]] = {}
	Rest: List[str] = []
	Index = 0
	Allowed_Lower = [O.lower() for O in Option_Name_List]

	while Index < len(Arg_List):
		Token = Arg_List[Index]
		if not _Is_Option(Token):
			Rest = Arg_List[Index:]
			break

		Name = Token.lstrip("-").lower()

		if Name in ("h", "help"):
			Options["help"] = None
			Index += 1
			continue
		if Name in ("v", "verbose"):
			Options["verbose"] = None
			Index += 1
			continue

		if Name not in Allowed_Lower:
			_Die(f"Unknown Option: -{Name}")

		if Index + 1 >= len(Arg_List):
			_Die(f"Missing Value For Option: -{Name}")

		Value = Arg_List[Index + 1]
		if _Is_Option(Value):
			_Die(f"Missing Value For Option: -{Name}")

		if Name == "about":
			Existing = Options.get("about")
			if Existing is None or isinstance(Existing, str):
				Options["about"] = [Value]
			else:
				Existing.append(Value)
			Index += 2
			continue

		Options[Name] = Value
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


def _Copy_Move_Link(Source: Path, Target: Path, Mode: str) -> None:
	if Target.exists():
		_Die(f"Target Already Exists: {Target}")
	if Mode == "copy":
		shutil.copy2(Source, Target)
	elif Mode == "move":
		shutil.move(str(Source), str(Target))
	elif Mode == "link":
		Target.symlink_to(Source.resolve())
	else:
		_Die(f"Unknown Mode: {Mode}")


def _Load_Dings_Name_Map(Index_Path: Path) -> Dict[int, str]:
	Map: Dict[int, str] = {}
	if not Index_Path.exists():
		return Map

	try:
		Text = Index_Path.read_text(encoding="utf-8", errors="replace")
	except OSError:
		return Map

	for Line in Text.splitlines():
		Line = Line.strip()
		if not Line or Line.startswith("#"):
			continue
		Parts = Line.split(None, 1)
		if not Parts:
			continue
		Id_Part = Parts[0]
		Name_Part = Parts[1].strip() if len(Parts) > 1 else ""
		Id_Part = Id_Part.split(".", 1)[0]
		if not Id_Part.isdigit():
			continue
		Id_Int = int(Id_Part)
		if Name_Part:
			Map[Id_Int] = Name_Part
	return Map


def _Normalize_Id_Token(Token: str) -> str:
	Token = Token.strip()
	if Token.lower().endswith(".md"):
		Token = Token[:-3]
	return Token.strip()


_MD_SIDE_RE = re.compile(r"^\[(?P<Name>[^\]]+)\]\((?P<Id>\d+)(?:\.md)?\)$")
def _Parse_About_Side(Token: str) -> Tuple[int, Optional[str]]:
	Token = Token.strip()
	Match = _MD_SIDE_RE.match(Token)
	if Match:
		return int(Match.group("Id")), Match.group("Name").strip()

	Token_N = _Normalize_Id_Token(Token)
	if Token_N.isdigit():
		return int(Token_N), None

	_Die(f"Invalid -about Side: {Token!r}")
	return 0, None


def _Parse_About_Pair(Token: str) -> Tuple[int, Optional[str], int, Optional[str]]:
	Token = Token.strip()
	if "=" not in Token:
		_Die(f"Invalid -about Pair (Missing '='): {Token!r}")

	Left, Right = Token.split("=", 1)
	Attr_Id, Attr_Name = _Parse_About_Side(Left.strip())
	Val_Id, Val_Name = _Parse_About_Side(Right.strip())
	return Attr_Id, Attr_Name, Val_Id, Val_Name


def _Render_About_Line(Attr_Id: int, Attr_Name: str, Value_Id: int, Value_Name: str) -> str:
	return f"- My [{Attr_Name}]({Attr_Id}.md) is [{Value_Name}]({Value_Id}.md)."


def _Sidecar_Program_Md(Title: str, Dings_Id: int, About_Line_List: List[str]) -> str:
	About_Text = "\n".join(About_Line_List)
	return (
		f"# {Title}\n\n"
		f"I am a [Program](60086.md).\n\n"
		f"## About\n\n"
		f"{About_Text}\n\n"
		f"## Data\n\n"
		f"![]({Dings_Id}.py)\n"
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
	_Print("   Import: Import Data Into Dings")


def _Help_Import() -> None:
	_Print("Dings-Gpt Import [COMMAND]")
	_Print("")
	_Print("Import Data Into Dings")
	_Print("")
	_Print("Options:")
	_Print("  -help: Print Description of Command")
	_Print("  -verbose: Print verbose Messages")
	_Print("")
	_Print("Commands:")
	_Print("   Text: Import Text Data")


def _Help_Import_Text() -> None:
	_Print("Dings-Gpt Import Text [COMMAND]")
	_Print("")
	_Print("Import Text Data Into Dings")
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
	_Print("  -start-id START_ID: First Dings-Id Candidate")
	_Print("  -creator CREATOR_ID: Dings-Id Of Creator (Optional)")
	_Print("  -mode MODE: copy|move|link (Default: copy)")
	_Print("  -title TITLE: Title For Side-Car Markdown (Default: Original File-Name)")
	_Print("  -overwrite OVERWRITE: 0|1 (Default: 0) Overwrite Existing Side-Car")
	_Print("  -about ABOUT_PAIR: About Pair, Markdown-Like, Repeatable")
	_Print("  -about-file ABOUT_FILE: Path To .about Config (Optional)")
	_Print("  -alias ALIAS_NAME: Create Soft-Link with explicit ALIAS_NAME (Optional)")
	_Print("")
	_Print("About Syntax Examples:")
	_Print("  -about-file GW-010-Plot-B-vs-A.about")
	_Print("  -about [Creator](60106)=[GPT](9000150)")
	_Print("  -about [Creator](60106)=9000150")
	_Print("  -about 60106=9000150")
	_Print("")
	_Print("Args:")
	_Print("  <file>: Path To Text File (e.g. .py)")


def _Write_Text(File_Path: Path, Text: str, Overwrite: bool, Verbose: bool) -> None:
	if File_Path.exists() and not Overwrite:
		_Die(f"Refusing To Overwrite Existing File: {File_Path}")
	File_Path.write_text(Text, encoding="utf-8")
	if Verbose:
		_Print(f"Written: {File_Path}")


def _Load_About_File(About_Path: Path) -> List[str]:
	Line_List: List[str] = []
	if not About_Path.exists():
		_Die(f"About-File Not Found: {About_Path}")
	try:
		Text = About_Path.read_text(encoding="utf-8", errors="replace")
	except OSError as Exc:
		_Die(f"Could Not Read About-File: {About_Path} ({Exc})")
	for Line in Text.splitlines():
		Line = Line.strip()
		if not Line or Line.startswith("#"):
			continue
		Line_List.append(Line)
	return Line_List


def _Cmd_Import_Text_File(Arg_List: List[str]) -> None:
	Options, Rest = _Parse_Options(
		Arg_List,
		Option_Name_List=["start-id", "creator", "mode", "title", "overwrite", "about", "about-file", "alias"],
	)

	Verbose = "verbose" in Options
	if "help" in Options or not Rest:
		_Help_Import_Text_File()
		return

	Start_Id_Str = Options.get("start-id")
	if Start_Id_Str is None or not isinstance(Start_Id_Str, str):
		_Die("Missing Option: -start-id")

	Mode = str(Options.get("mode") or "copy").lower()
	Title = Options.get("title")
	Overwrite = str(Options.get("overwrite") or "0").lower() in ("1", "true", "yes")

	Creator_Str = Options.get("creator")
	Creator_Id: Optional[int] = None
	if isinstance(Creator_Str, str):
		try:
			Creator_Id = int(Creator_Str)
		except ValueError:
			_Die(f"Invalid -creator: {Creator_Str!r}")

	try:
		Start_Id = int(Start_Id_Str)
	except ValueError:
		_Die(f"Invalid -start-id: {Start_Id_Str!r}")

	Source_Path = Path(Rest[0])
	if not Source_Path.exists():
		_Die(f"File Not Found: {Source_Path}")

	Dir_Path = Path(".").resolve()
	Next_Id = _Find_Next_Free_Id(Start_Id, Dir_Path)

	Target_Data_Path = Dir_Path / f"{Next_Id}{Source_Path.suffix}"
	Target_Md_Path = Dir_Path / f"{Next_Id}.md"

	_Copy_Move_Link(Source_Path, Target_Data_Path, Mode=Mode)

	# Optional Alias (Soft-Link)
	Alias_Opt = Options.get("alias")
	if isinstance(Alias_Opt, str) and Alias_Opt:
		Alias_Path = Dir_Path / Alias_Opt
		# Remove existing alias if overwrite is enabled
		if Alias_Path.exists() or Alias_Path.is_symlink():
			if not Overwrite:
				_Die(f"Refusing To Overwrite Existing Alias: {Alias_Path}")
			try:
				Alias_Path.unlink()
			except OSError as Exc:
				_Die(f"Could Not Remove Existing Alias: {Alias_Path} ({Exc})")
		try:
			Alias_Path.symlink_to(Target_Md_Path.name)
		except OSError as Exc:
			_Die(f"Could Not Create Alias: {Alias_Path} -> {Target_Data_Path.name} ({Exc})")
		if Verbose:
			_Print(f"Alias: {Alias_Path.name} -> {Target_Data_Path.name}")

	Title_Final = str(Title) if isinstance(Title, str) and Title else Source_Path.name

	Name_Map = _Load_Dings_Name_Map(Dir_Path / "0.txt")

	def _Name_For(Id_Int: int, Override: Optional[str]) -> str:
		if Override:
			return Override
		return Name_Map.get(Id_Int, str(Id_Int))

	About_Line_List: List[str] = []

	if Source_Path.suffix.lower() == ".py":
		# Defaults
		About_Line_List.append(
			_Render_About_Line(
				Attr_Id=9010000,
				Attr_Name=_Name_For(9010000, "Programming-Language"),
				Value_Id=9010003,
				Value_Name=_Name_For(9010003, "Python"),
			)
		)
		About_Line_List.append(
			_Render_About_Line(
				Attr_Id=611006,
				Attr_Name=_Name_For(611006, "Original-Name"),
				Value_Id=Next_Id,
				Value_Name=Source_Path.name,
			)
		)

		# Optional Creator
		if Creator_Id is not None:
			About_Line_List.append(
				_Render_About_Line(
					Attr_Id=60106,
					Attr_Name=_Name_For(60106, "Creator"),
					Value_Id=Creator_Id,
					Value_Name=_Name_For(Creator_Id, None),
				)
			)

		# About From Config File (.about)
		About_File_Opt = Options.get("about-file")
		if isinstance(About_File_Opt, str) and About_File_Opt:
			About_Path = Path(About_File_Opt)
			if About_Path.suffix == "":
				About_Path = About_Path.with_suffix(".about")
			for Pair_Str in _Load_About_File(About_Path):
				Attr_Id, Attr_Name_Override, Val_Id, Val_Name_Override = _Parse_About_Pair(Pair_Str)
				About_Line_List.append(
					_Render_About_Line(
						Attr_Id=Attr_Id,
						Attr_Name=_Name_For(Attr_Id, Attr_Name_Override),
						Value_Id=Val_Id,
						Value_Name=_Name_For(Val_Id, Val_Name_Override),
					)
				)

		# Manual About Pairs (CLI Overrides Config)
		About_Opt = Options.get("about")
		if isinstance(About_Opt, list):
			for Pair_Str in About_Opt:
				Attr_Id, Attr_Name_Override, Val_Id, Val_Name_Override = _Parse_About_Pair(Pair_Str)
				About_Line_List.append(
					_Render_About_Line(
						Attr_Id=Attr_Id,
						Attr_Name=_Name_For(Attr_Id, Attr_Name_Override),
						Value_Id=Val_Id,
						Value_Name=_Name_For(Val_Id, Val_Name_Override),
					)
				)

		Md_Text = _Sidecar_Program_Md(
			Title=Title_Final,
			Dings_Id=Next_Id,
			About_Line_List=About_Line_List,
		)
	else:
		_Die("Currently Only Python (.py) Is Supported Here")

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
