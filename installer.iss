; Inno Setup 6 script of StoppedFlowKinetiX (built by BuildInstaller.bat).
; The version is passed by BuildInstaller.bat from src/version.py (/DMyAppVersion=...);
; the value below is used only when the script is compiled by hand.
#ifndef MyAppVersion
  #define MyAppVersion "2.0.0"
#endif
#define MyAppName "StoppedFlowKinetiX"
#define MyAppExeName "StoppedFlowKinetiX.exe"
#define MyAppFolder "StoppedFlowKinetiX"
#define MyAppPublisher "Institute of Biophysics of the Czech Academy of Sciences"
#define MyAppURL "https://www.ibp.cz/en/research/departments/biophysics-of-nucleic-acids/research-profile"
#define MyOutputDir "installer"
#define MySetupIcon "installer_assets\setupicon.ico"
#define MyUninstallIcon "uninstall_icon.ico"

[Setup]
AppId={{bcd1ccca-49f5-4069-87da-50a038723fd5}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppFolder}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; The uninstaller (Settings > Apps, Control Panel) shows its own icon
UninstallDisplayIcon={app}\{#MyUninstallIcon}
UninstallDisplayName={#MyAppName} {#MyAppVersion}
OutputBaseFilename=Setup_for_{#MyAppName}_ver_{#MyAppVersion}
OutputDir={#MyOutputDir}
SetupIconFile={#MySetupIcon}
WizardImageFile=installer_assets\wizardimage.bmp,installer_assets\wizardimage_150.bmp
WizardSmallImageFile=installer_assets\wizardsmallimage.bmp,installer_assets\wizardsmallimage_150.bmp
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
LicenseFile=installer_assets\license.txt
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ShowLanguageDialog=auto
UsePreviousTasks=no
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
; Tell Windows (Explorer) that file associations changed, see [Registry]
ChangesAssociations=yes
CloseApplications=yes
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName} setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "czech"; MessagesFile: "compiler:Languages\Czech.isl"

[InstallDelete]
; An upgrade installs into the same folder; remove the bundled libraries of the
; previous version so that leftovers of an older build never stay on sys.path.
Type: filesandordirs; Name: "{app}\_internal"

[Files]
Source: "dist\{#MyAppFolder}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\{#MyAppFolder}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "installer_assets\uninstall_icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_assets\license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "installer_assets\readme.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start menu: the program and its uninstaller (with the uninstall icon)
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"; IconFilename: "{app}\{#MyUninstallIcon}"
; Desktop shortcut (task "desktopicon")
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "assocsfkx"; Description: "{cm:AssocSfkx}"; GroupDescription: "{cm:AssocGroup}"
Name: "readme"; Description: "{cm:ReadmeTaskDescription}"; Flags: unchecked

[Registry]
; Double-click on a project (.sfkx) opens it in StoppedFlowKinetiX (task "assocsfkx").
Root: HKA; Subkey: "Software\Classes\.sfkx"; ValueType: string; ValueName: ""; ValueData: "StoppedFlowKinetiX.sfkx"; Flags: uninsdeletevalue; Tasks: assocsfkx
Root: HKA; Subkey: "Software\Classes\.sfkx\OpenWithProgids"; ValueType: string; ValueName: "StoppedFlowKinetiX.sfkx"; ValueData: ""; Flags: uninsdeletevalue; Tasks: assocsfkx
Root: HKA; Subkey: "Software\Classes\StoppedFlowKinetiX.sfkx"; ValueType: string; ValueName: ""; ValueData: "StoppedFlowKinetiX project"; Flags: uninsdeletekey; Tasks: assocsfkx
Root: HKA; Subkey: "Software\Classes\StoppedFlowKinetiX.sfkx\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"; Tasks: assocsfkx
Root: HKA; Subkey: "Software\Classes\StoppedFlowKinetiX.sfkx\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: assocsfkx
; "Open with -> StoppedFlowKinetiX" for the Chirascan CSV exports (without taking over .csv)
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".sfkx"; ValueData: ""
Root: HKA; Subkey: "Software\Classes\Applications\{#MyAppExeName}\SupportedTypes"; ValueType: string; ValueName: ".csv"; ValueData: ""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
Filename: "notepad.exe"; Parameters: "{app}\readme.txt"; Flags: shellexec skipifsilent; Check: WizardIsTaskSelected('readme')

[UninstallDelete]
; files the program itself wrote into its folder (none normally) - user data in
; %LOCALAPPDATA%\StoppedFlowKinetiX (log, help pages) is removed only on request, see [Code]
Type: dirifempty; Name: "{app}"

[CustomMessages]
english.ReadmeTaskDescription=View README after install
czech.ReadmeTaskDescription=Zobrazit README po instalaci
english.AssocGroup=File types:
czech.AssocGroup=Typy souboru:
english.AssocSfkx=Open projects (.sfkx) with StoppedFlowKinetiX by double-click
czech.AssocSfkx=Otevirat projekty (.sfkx) dvojklikem v StoppedFlowKinetiX
english.RemoveUserData=Remove also the log files and help pages of StoppedFlowKinetiX (%LOCALAPPDATA%\StoppedFlowKinetiX)?
czech.RemoveUserData=Odstranit take logy a stranky napovedy StoppedFlowKinetiX (%LOCALAPPDATA%\StoppedFlowKinetiX)?
czech.LaunchProgram=Spustit aplikaci %1

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{localappdata}\{#MyAppName}');
    if DirExists(DataDir) and (not UninstallSilent) then
      if MsgBox(ExpandConstant('{cm:RemoveUserData}'), mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
        DelTree(DataDir, True, True, True);
  end;
end;
