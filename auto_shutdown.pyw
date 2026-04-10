"""
자동 종료 타이머 - 시스템 트레이 아이콘
매일 자정(00:00)에 컴퓨터를 자동 종료합니다.
"""

import os
import sys
import time
import threading
import datetime
import platform
from PIL import Image, ImageDraw, ImageFont
import pystray
from pystray import MenuItem as item


def get_seconds_until_midnight():
    """자정까지 남은 초 계산"""
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
    return (midnight - now).total_seconds()


def get_time_remaining_str():
    """남은 시간을 HH:MM:SS 형식으로 반환"""
    seconds = int(get_seconds_until_midnight())
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def shutdown_computer():
    """운영체제에 맞게 컴퓨터 종료"""
    system = platform.system()
    if system == "Windows":
        os.system("shutdown /s /t 0")
    elif system == "Linux":
        os.system("shutdown -h now")
    elif system == "Darwin":  # macOS
        os.system("sudo shutdown -h now")


def create_icon_image(time_str="00:00"):
    """트레이 아이콘 이미지 생성 (시계 모양)"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 원 배경 (빨간색 계열)
    draw.ellipse([2, 2, size - 2, size - 2], fill=(220, 50, 50, 255), outline=(180, 20, 20, 255), width=2)

    # 전원 아이콘 심볼
    cx, cy = size // 2, size // 2
    r = 18

    # 전원 버튼 원호
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=45, end=315, fill=(255, 255, 255, 255), width=4)

    # 전원 버튼 수직선
    draw.line([cx, cy - r - 4, cx, cy - 4], fill=(255, 255, 255, 255), width=4)

    return img


def create_countdown_icon(time_str):
    """남은 시간이 표시된 아이콘 생성"""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 시간이 1시간 미만이면 주황색, 30분 미만이면 빨간색
    seconds = int(get_seconds_until_midnight())
    if seconds < 1800:
        bg_color = (220, 50, 50, 255)    # 빨간색
    elif seconds < 3600:
        bg_color = (220, 130, 50, 255)   # 주황색
    else:
        bg_color = (50, 120, 220, 255)   # 파란색

    # 배경 원
    draw.ellipse([2, 2, size - 2, size - 2], fill=bg_color, outline=(30, 30, 30, 200), width=2)

    # 전원 아이콘
    cx, cy = size // 2, size // 2
    r = 18
    draw.arc([cx - r, cy - r, cx + r, cy + r], start=45, end=315, fill=(255, 255, 255, 230), width=3)
    draw.line([cx, cy - r - 3, cx, cy - 3], fill=(255, 255, 255, 230), width=3)

    return img


class AutoShutdownApp:
    def __init__(self):
        self.cancelled = False
        self.icon = None
        self._create_tray_icon()

    def _create_tray_icon(self):
        """트레이 아이콘 생성"""
        image = create_icon_image()

        menu = pystray.Menu(
            item(self._get_title, None, enabled=False),
            pystray.Menu.SEPARATOR,
            item("종료 취소", self._cancel_shutdown),
            item("지금 바로 종료", self._shutdown_now),
            pystray.Menu.SEPARATOR,
            item("프로그램 종료", self._quit_app),
        )

        self.icon = pystray.Icon(
            "auto_shutdown",
            image,
            "자동 종료 타이머",
            menu
        )

    def _get_title(self, item=None):
        """메뉴 타이틀 (남은 시간 표시)"""
        if self.cancelled:
            return "자동 종료: 취소됨"
        return f"자정까지: {get_time_remaining_str()}"

    def _cancel_shutdown(self, icon=None, item=None):
        """자동 종료 취소"""
        self.cancelled = True
        if self.icon:
            self.icon.title = "자동 종료: 취소됨"
            # 아이콘을 회색으로 변경
            gray_img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(gray_img)
            draw.ellipse([2, 2, 62, 62], fill=(120, 120, 120, 255), outline=(80, 80, 80, 255), width=2)
            cx, cy = 32, 32
            draw.arc([cx - 18, cy - 18, cx + 18, cy + 18], start=45, end=315, fill=(200, 200, 200, 230), width=3)
            draw.line([cx, cy - 21, cx, cy - 3], fill=(200, 200, 200, 230), width=3)
            self.icon.icon = gray_img

    def _shutdown_now(self, icon=None, item=None):
        """즉시 컴퓨터 종료"""
        self.icon.stop()
        shutdown_computer()

    def _quit_app(self, icon=None, item=None):
        """프로그램만 종료 (컴퓨터는 종료하지 않음)"""
        self.cancelled = True
        self.icon.stop()

    def _update_loop(self):
        """아이콘 및 툴팁 주기적 업데이트 + 자정 감지"""
        while self.icon.visible if hasattr(self.icon, 'visible') else True:
            if self.cancelled:
                time.sleep(5)
                continue

            remaining = get_seconds_until_midnight()

            # 아이콘 업데이트
            try:
                new_img = create_countdown_icon(get_time_remaining_str())
                self.icon.icon = new_img
                self.icon.title = f"자동 종료 | 자정까지 {get_time_remaining_str()} 남음"
            except Exception:
                pass

            # 자정 도달 시 종료
            if remaining <= 1:
                self.icon.stop()
                time.sleep(1)
                shutdown_computer()
                return

            # 1초마다 업데이트
            time.sleep(1)

    def run(self):
        """앱 실행"""
        # 백그라운드 업데이트 스레드 시작
        update_thread = threading.Thread(target=self._update_loop, daemon=True)
        update_thread.start()

        # 트레이 아이콘 실행 (블로킹)
        self.icon.run()


def main():
    print("자동 종료 타이머 시작")
    print(f"자정까지 남은 시간: {get_time_remaining_str()}")
    print("시스템 트레이 아이콘을 확인하세요.")

    try:
        app = AutoShutdownApp()
        app.run()
    except Exception as e:
        print(f"오류 발생: {e}")
        print("필요한 패키지를 설치하세요: pip install pystray Pillow")
        sys.exit(1)


if __name__ == "__main__":
    main()
