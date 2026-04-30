import matplotlib.pyplot as plt
import seaborn as sns


def plot_benchmark_results(results_df):
    # Налаштування стилю
    sns.set_theme(style="whitegrid")

    # Створення вікна для трьох графіків
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Аналіз ефективності форматів збереження енергетичних даних', fontsize=16)

    # Налаштування параметрів для кожного графіка, щоб уникнути FutureWarning
    plot_params = {
        'data': results_df,
        'x': 'Format',
        'hue': 'Format',
        'legend': False
    }

    # 1. Швидкість запису
    sns.barplot(y='Write Time (s)', ax=axes[0], palette='viridis', **plot_params)
    axes[0].set_title('Швидкість запису (менше = краще)')

    # 2. Швидкість читання
    sns.barplot(y='Read Time (s)', ax=axes[1], palette='magma', **plot_params)
    axes[1].set_title('Швидкість читання (менше = краще)')

    # 3. Розмір файлів
    sns.barplot(y='Size (MB)', ax=axes[2], palette='rocket', **plot_params)
    axes[2].set_title('Розмір файлу на диску (МБ)')

    # Оптимізація розташування
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # Збереження результату
    plt.savefig('benchmark_plot.png')
    print("Графік збережено як 'benchmark_plot.png'")
    plt.show()