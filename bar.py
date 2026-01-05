import time
import numpy as np
import pyautogui as pg
import dxcam

# === Настройки ===
monitor = (780, 450, 780 + 360, 450 + 98)
target_color = [0, 249, 135]  # BGR зелёной отметки
color_tolerance = 10
click_cooldown = 0.08
click_delay = 0.001  # задержка перед кликом (чем меньше — тем быстрее реакция)
no_green_timeout = 1.0  # сколько секунд нет зелёной метки — считаем, что миниигра закончилась
start_delay = 0.5       # пауза после запуска миниигры, перед тем как искать зелёную

pg.PAUSE = 0
pg.FAILSAFE = False

cam = dxcam.create(output_idx=0)

def find_color_mask(img, color, tol):
    b, g, r = color
    return (
        (img[:, :, 0] >= b - tol) & (img[:, :, 0] <= b + tol) &
        (img[:, :, 1] >= g - tol) & (img[:, :, 1] <= g + tol) &
        (img[:, :, 2] >= r - tol) & (img[:, :, 2] <= r + tol)
    )

was_visible = False
last_click_time = 0.0
last_green_seen = time.time()
game_active = False
waiting_to_start = False

print("Мониторинг запущен... (Ctrl+C для выхода)")

try:
    while True:
        frame = cam.grab(region=monitor)
        if frame is None:
            continue

        green_mask = find_color_mask(frame, target_color, color_tolerance)
        visible_now = np.any(green_mask)
        now = time.time()

        # Если миниигра не идёт — запускаем её
        if not game_active and not waiting_to_start:
            print(f"[{time.strftime('%H:%M:%S')}] Миниигра неактивна запускаем ПКМ")
            pg.click(button="right")
            waiting_to_start = True
            time.sleep(start_delay)
            continue

        # После нажатия ждём появления зелёной метки
        if waiting_to_start:
            if visible_now:
                print(f"[{time.strftime('%H:%M:%S')}] Обнаружена зелёная метка миниигра началась")
                waiting_to_start = False
                game_active = True
            continue

        # === Миниигра идёт ===
        if visible_now:
            last_green_seen = now

        # Если метка была видна и пропала — белая её перекрыла
        if was_visible and not visible_now and (now - last_click_time) >= click_cooldown:
            print(f"[{time.strftime('%H:%M:%S')}] Белая перекрыла зелёную клик через {click_delay:.3f}с")
            time.sleep(click_delay)
            pg.click(button="right")
            last_click_time = now

        # Если давно не видим зелёную метку — миниигра закончилась
        if game_active and (now - last_green_seen) > no_green_timeout:
            print(f"[{time.strftime('%H:%M:%S')}] Миниигра окончена, ждём перед рестартом")
            game_active = False
            time.sleep(1.5)
            continue

        was_visible = visible_now
        time.sleep(0.001)

except KeyboardInterrupt:
    print("Остановлено пользователем.")
