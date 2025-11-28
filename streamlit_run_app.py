"""
Streamlit 가계부 애플리케이션 실행 스크립트
"""
import subprocess
import sys
import os

def check_and_install_requirements():
    """필요한 패키지가 설치되어 있는지 확인하고 없으면 설치합니다."""
    required_packages = {
        'streamlit': 'streamlit',
        'pandas': 'pandas',
        'plotly': 'plotly'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"필요한 패키지를 설치합니다: {', '.join(missing_packages)}")
        for package in missing_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("패키지 설치가 완료되었습니다.")
    else:
        print("모든 필요한 패키지가 설치되어 있습니다.")

def run_streamlit():
    """Streamlit 애플리케이션을 실행합니다."""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    
    if not os.path.exists(app_path):
        print(f"오류: {app_path} 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    print("Streamlit 애플리케이션을 실행합니다...")
    print(f"애플리케이션 경로: {app_path}")
    print("\n브라우저에서 자동으로 열립니다.")
    print("종료하려면 Ctrl+C를 누르세요.\n")
    
    try:
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            app_path,
            "--server.headless",
            "false"
        ])
    except KeyboardInterrupt:
        print("\n애플리케이션이 종료되었습니다.")

if __name__ == "__main__":
    print("=" * 50)
    print("가계부 관리 시스템 실행")
    print("=" * 50)
    print()
    
    # 패키지 확인 및 설치
    check_and_install_requirements()
    print()
    
    # Streamlit 실행
    run_streamlit()

