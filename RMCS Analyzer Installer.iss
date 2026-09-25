#define MyAppName "RMCS Analyzer"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "Rocket Analyst"
#define MyAppExeName "RMCS Analyzer.exe"

[Setup]
AppId={{RMCS-Analyzer-v1.0.1}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\RMCS Analyzer
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=RMCS_Analyzer_v1.0.1_Setup
SetupIconFile=RMCS_Analyzer.ico
UninstallDisplayIcon={app}\RMCS_Analyzer.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\RMCS Analyzer\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "RMCS_Analyzer.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\RMCS_Analyzer.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\RMCS_Analyzer.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent