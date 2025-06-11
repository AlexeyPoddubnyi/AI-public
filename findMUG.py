import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog

# Выбор файла
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename(title="Выберите фото", filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])

if not file_path:
    print("Файл не выбран.")
    exit()

# Загружаем
img = cv2.imread(file_path)
output = img.copy()
height, width = img.shape[:2]

# Переводим в LAB (яркость)
lab = cv2.cvtColor(img, cv2.COLOR_BGR2Lab)
L, a, b = cv2.split(lab)

# Маска по яркости – тарелка обычно светлая
_, mask = cv2.threshold(L, 190, 255, cv2.THRESH_BINARY)

# Морфология для очистки
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

# Контуры
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

for cnt in contours:
    area = cv2.contourArea(cnt)
    if area > 5000:
        (x, y), radius = cv2.minEnclosingCircle(cnt)
        center = (int(x), int(y))
        radius = int(radius)

        # Проверим, чтобы весь круг помещался в кадр
        if (center[0] - radius >= 0 and center[0] + radius <= width and
            center[1] - radius >= 0 and center[1] + radius <= height):
            cv2.circle(output, center, radius, (0, 255, 0), 3)

cv2.imshow("Обнаружение кружки (не выходя за кадр)", output)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Сохраняем
cv2.imwrite("result_no_outside.jpg", output)
print("Готово! Результат в result_no_outside.jpg")
