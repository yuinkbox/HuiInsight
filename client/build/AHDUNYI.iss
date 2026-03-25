; 徽鉴 HuiInsight - Inno Setup Script
; Wraps the PyInstaller onedir output into a standard Windows installer.
;
; Prerequisites:
;   Inno Setup 6.x  https://jrsoftware.org/isinfo.php
;
; Usage (local):
;   ISCC.exe client\build\AHDUNYI.iss
;
; Output:
;   installer\HuiInsight_Setup_<version>.exe
;
; Author : xvyu
; Version: 1.0.0

#define AppName      "徽鉴 HuiInsight"
#define AppVersion   "1.0.0"
#define AppPublisher "xvyu"
#define AppExeName   "HuiInsight.exe"
#define SourceDir    "..\..\dist\AHDUNYI_Terminal_PRO"
#define OutputDir    "..\..\installer"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir={#OutputDir}
OutputBaseFilename=HuiInsight_Setup_{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
SetupIconFile=
WizardSmallImageFile=
ShowLanguageDialog=no
LanguageDetectionMethod=none

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startmenuicon"; Description: "创建开始菜单快捷方式"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Main application directory - include everything from PyInstaller onedir output
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\卸载 {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartmenu}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
