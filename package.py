import os
import subprocess
import customtkinter

ctk_dir = os.path.dirname(customtkinter.__file__)
main_script = "main.py" 
build_mode = "--onefile" 

cmd = [
    "pyinstaller",
    "--noconfirm",
    build_mode,
    "--windowed",
    # 1. Nạp tài nguyên của CustomTkinter
    f'--add-data "{ctk_dir}{os.pathsep}customtkinter/"', 
    
    # 2. 🔥 DÒNG QUAN TRỌNG NÀY ĐỂ FIX LỖI: Nạp toàn bộ thư mục assets của ông vào file .exe
    f'--add-data "assets{os.pathsep}assets"', 
    
    main_script
]

full_command = " ".join(cmd)
print(f"[*] Đang thực thi lệnh đóng gói:\n{full_command}\n")
subprocess.run(full_command, shell=True)
print("\n[+] ĐÓNG GÓI HOÀN TẤT!")