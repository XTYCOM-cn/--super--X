#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PyInstaller打包脚本 - 将浮动文字桌宠打包为exe文件
"""

import os
import sys
import shutil
import subprocess

def main():
    print("=" * 60)
    print("浮动文字桌宠 - EXE打包工具")
    print("=" * 60)
    print("\n此脚本将帮助您将浮动文字桌宠程序打包为可执行的exe文件。")
    print("打包完成后，您可以在没有Python环境的电脑上直接运行程序。\n")
    
    # 检查PyInstaller是否已安装
    try:
        import PyInstaller
        print("✓ PyInstaller已安装")
    except ImportError:
        print("× PyInstaller未安装，正在安装...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✓ PyInstaller安装成功")
        except Exception as e:
            print(f"× PyInstaller安装失败: {e}")
            print("请手动运行: pip install pyinstaller")
            input("按Enter键退出...")
            return
    
    # 检查主程序文件
    main_file = "main_enhanced_with_super_library_bugfixed.py"
    if not os.path.exists(main_file):
        main_file = input("请输入主程序文件名 (默认: main_enhanced_with_super_library_bugfixed.py): ")
        if not main_file:
            main_file = "main_enhanced_with_super_library_bugfixed.py"
        if not os.path.exists(main_file):
            print(f"× 找不到文件: {main_file}")
            input("按Enter键退出...")
            return
    
    # 检查词库文件
    library_file = "text_styles.py"
    if not os.path.exists(library_file):
        if os.path.exists("super_enhanced_text_library.py"):
            print("! 发现super_enhanced_text_library.py文件")
            rename = input("是否将super_enhanced_text_library.py重命名为text_styles.py? (y/n): ")
            if rename.lower() == 'y':
                try:
                    shutil.copy("super_enhanced_text_library.py", "text_styles.py")
                    print("✓ 文件已复制为text_styles.py")
                except Exception as e:
                    print(f"× 文件复制失败: {e}")
                    input("按Enter键退出...")
                    return
        else:
            print("× 找不到词库文件: text_styles.py")
            library_file = input("请输入词库文件名: ")
            if not os.path.exists(library_file):
                print(f"× 找不到文件: {library_file}")
                input("按Enter键退出...")
                return
    
    # 询问图标文件
    icon_file = None
    use_icon = input("是否使用自定义图标? (y/n): ")
    if use_icon.lower() == 'y':
        icon_file = input("请输入图标文件路径 (.ico文件): ")
        if not os.path.exists(icon_file):
            print(f"× 找不到图标文件: {icon_file}")
            icon_file = None
    
    # 询问程序名称
    app_name = input("请输入生成的程序名称 (默认: 浮动文字桌宠): ")
    if not app_name:
        app_name = "浮动文字桌宠"
    
    # 构建PyInstaller命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", app_name
    ]
    
    if icon_file:
        cmd.extend(["--icon", icon_file])
    
    cmd.append(main_file)
    
    # 执行打包命令
    print("\n开始打包程序，请稍候...")
    try:
        subprocess.run(cmd, check=True)
        print("\n✓ 打包完成!")
        print(f"可执行文件位置: dist/{app_name}.exe")
    except Exception as e:
        print(f"\n× 打包失败: {e}")
    
    input("\n按Enter键退出...")

if __name__ == "__main__":
    main()
