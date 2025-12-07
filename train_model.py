import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression

data = pd.read_csv('data/data.csv')

# Разделение на признаки и целевую переменную
X = data.drop('target', axis=1)
y = data['target']

# Обучение модели на всех данных
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X, y)

# Сохранение модели
with open('models/model.pkl', 'wb') as f:
    pickle.dump(model, f)

print('Модель обучена и сохранена как model.pkl')
print(f'Количество обучающих примеров: {len(data)}')