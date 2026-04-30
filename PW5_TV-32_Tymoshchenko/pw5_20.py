import cv2
import numpy as np


def process_image(file_path):
    # 1. Завантажуємо оригінальне зображення
    image = cv2.imread(file_path)

    if image is None:
        print("Помилка: Не вдалося знайти або завантажити зображення.")
        return

    # Створюємо копію для малювання, щоб зберегти оригінал
    result_image = image.copy()

    # 2. Перетворюємо в чорно-білий формат (Grayscale)
    # Це потрібно, бо алгоритми пошуку контурів працюють з інтенсивністю світла
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Розмазуємо зображення (Gaussian Blur)
    # Це прибирає дрібні деталі та шум, щоб обводилися лише великі об'єкти
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 4. Детектор Кенні (Canny Edge Detection)
    # Знаходить різкі перепади кольору (межі)
    edges = cv2.Canny(blurred, 100, 200)

    # 5. Знаходимо контури як вектори (масиви точок)
    # cv2.RETR_EXTERNAL — шукає тільки зовнішні контури
    # cv2.CHAIN_APPROX_SIMPLE — стискає горизонтальні/вертикальні сегменти для економії пам'яті
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 6. Малюємо знайдені контури на копії оригіналу
    # (0, 255, 0) — це зелений колір у форматі BGR
    # 3 — товщина лінії обведення
    cv2.drawContours(result_image, contours, -1, (0, 255, 0), 3)

    # 7. Виводимо результати на екран
    cv2.imshow('1. Original', image)
    cv2.imshow('2. Edges (Canny)', edges)
    cv2.imshow('3. Final Contours', result_image)

    print(f"Знайдено об'єктів (контурів): {len(contours)}")

    # Чекаємо натискання клавіші та закриваємо вікна
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# Запуск програми
if __name__ == "__main__":
    process_image('best_image.jpg')