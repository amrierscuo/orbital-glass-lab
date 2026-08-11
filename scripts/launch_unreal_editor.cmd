@echo off
setlocal

set "UE_EDITOR=C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
set "PROJECT=D:\UnrealProjects\OrbitalGlassLab\OrbitalGlassLab.uproject"

if not exist "%UE_EDITOR%" (
  echo Unreal Editor 5.8 non trovato in:
  echo %UE_EDITOR%
  pause
  exit /b 1
)

if exist "%PROJECT%" (
  start "" "%UE_EDITOR%" "%PROJECT%"
) else (
  start "" "%UE_EDITOR%"
)

endlocal
