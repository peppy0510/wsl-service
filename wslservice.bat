python source/wslservice.py
rem nircmd elevatecmd exec hide python source/wslservice.py
rem pwsh -WindowStyle Hidden -Command "Start-Process cmd -Verb RunAs -ArgumentList '/c start python.exe source/wslservice.py -d %CD%'"