{
  lib,
  python3Packages,
  portaudio,
}:

python3Packages.buildPythonApplication rec {
  pname = "tdmg";
  version = "0.1.0";

  pyproject = true;

  src = ./.;

  build-system = [
    python3Packages.setuptools
  ];

  dependencies = with python3Packages; [
    numpy
    sounddevice
    tkinter
    screeninfo
  ];

  nativeBuildInputs = [
    python3Packages.setuptools
  ];

  buildInputs = [
    portaudio
  ];

  pythonImportsCheck = [
    "main"
    "gui"
    "variables"
  ];

  meta = {
    description = "Trainiere dein musikalisches Gehör";
    mainProgram = "tdmg";
    license = lib.licenses.gpl3Plus;
    platforms = lib.platforms.linux;
  };
}
