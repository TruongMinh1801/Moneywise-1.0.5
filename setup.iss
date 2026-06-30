; ==============================================================================
; INNO SETUP CONFIGURATION FOR MONEYWISE VERSION 1.0.5
; ==============================================================================

#define AppName "Moneywise 1.0.5"
#define AppVersion "1.0.5"
#define AppPublisher "BFF - Build for the Future"
#define AppExeName "Moneywise 1.0.5.exe"

[Setup]
AppId={{C7B8A9E0-2B3C-4D5E-6F7A-8B9C0D1E2F3A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}

DefaultDirName={autopf}\{#AppName}
DisableProgramGroupPage=yes

; Đường dẫn xuất file cài đặt về thư mục của ông
OutputDir=F:\Samsung solve for tomorrow\Bài làm của tôi\MoneyWise 1.0.4
OutputBaseFilename=Moneywise_1.0.5_Setup
PrivilegesRequired=admin

Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Đọc file .exe phiên bản mới sau khi ông chạy PyInstaller
Source: "F:\Samsung solve for tomorrow\Bài làm của tôi\MoneyWise 1.0.5\dist\Moneywise 1.0.5.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion
Source: "F:\Samsung solve for tomorrow\Bài làm của tôi\MoneyWise 1.0.4\assets\icons\icon.ico"; DestDir: "{app}\assets\icons"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\assets\icons\icon.ico"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Khởi chạy {#AppName} ngay lập tức"; Flags: nowait postinstall skipifsilent