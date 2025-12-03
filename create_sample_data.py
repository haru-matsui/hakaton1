"""
Script to create sample data for testing the Conspectus Helper application
"""
from app import app, db
from models import User, Conspectus, Tag, Subject, Rating, Comment

def create_sample_data():
    with app.app_context():
        print("Creating sample users...")
        
        # Create a student
        student = User(username='ivan_student', email='ivan@example.com', role='student')
        student.set_password('password123')
        student.bio = 'Студент 3 курса, увлекаюсь математикой и программированием'
        
        # Create a teacher
        teacher = User(username='maria_teacher', email='maria@example.com', role='teacher')
        teacher.set_password('password123')
        teacher.bio = 'Преподаватель информатики с 10-летним опытом'
        
        db.session.add(student)
        db.session.add(teacher)
        db.session.commit()
        
        print("Creating sample conspectuses...")
        
        # Get subjects
        math_subject = Subject.query.filter_by(name='Математика').first()
        cs_subject = Subject.query.filter_by(name='Информатика').first()
        physics_subject = Subject.query.filter_by(name='Физика').first()
        
        # Create tags
        tags_data = ['дифференциальные уравнения', 'алгоритмы', 'структуры данных', 
                     'квантовая механика', 'линейная алгебра', 'машинное обучение']
        tags = []
        for tag_name in tags_data:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            tags.append(tag)
        db.session.commit()
        
        # Sample conspectus 1 - Mathematics
        conspectus1 = Conspectus(
            author_id=student.id,
            title='Введение в дифференциальные уравнения',
            content='''# Дифференциальные уравнения

## Определение

**Дифференциальное уравнение** — это уравнение, которое связывает независимую переменную, искомую функцию и её производные.

## Типы дифференциальных уравнений

### 1. Обыкновенные дифференциальные уравнения (ОДУ)

Содержат функцию одной переменной и её производные:

```
dy/dx = f(x, y)
```

### 2. Дифференциальные уравнения в частных производных

Содержат функции нескольких переменных и их частные производные.

## Примеры

**Пример 1:** Уравнение первого порядка
```
dy/dx = 2x
```

Решение: `y = x² + C`

**Пример 2:** Линейное уравнение второго порядка
```
y'' + 3y' + 2y = 0
```

## Методы решения

1. **Разделение переменных**
2. **Метод вариации постоянной**
3. **Метод неопределённых коэффициентов**
4. **Преобразование Лапласа**

## Применение

- Физика (движение тел, колебания)
- Инженерия (электрические цепи)
- Биология (популяционная динамика)
- Экономика (модели роста)
''',
            subject_id=math_subject.id,
            visibility='public',
            is_draft=False
        )
        conspectus1.tags.extend([tags[0], tags[4]])
        db.session.add(conspectus1)
        
        # Sample conspectus 2 - Computer Science
        conspectus2 = Conspectus(
            author_id=teacher.id,
            title='Алгоритмы сортировки: обзор и сравнение',
            content='''# Алгоритмы сортировки

## Введение

Сортировка — это процесс упорядочивания элементов массива по возрастанию или убыванию.

## Основные алгоритмы

### 1. Пузырьковая сортировка (Bubble Sort)

**Временная сложность:** O(n²)

```python
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr
```

**Преимущества:**
- Простая реализация
- Стабильная сортировка

**Недостатки:**
- Медленная для больших массивов

### 2. Быстрая сортировка (Quick Sort)

**Временная сложность:** O(n log n) в среднем

```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
```

### 3. Сортировка слиянием (Merge Sort)

**Временная сложность:** O(n log n)

- Использует принцип "разделяй и властвуй"
- Стабильная сортировка
- Требует дополнительной памяти

## Сравнительная таблица

| Алгоритм | Лучший случай | Средний случай | Худший случай | Память |
|----------|---------------|----------------|---------------|--------|
| Bubble   | O(n)          | O(n²)          | O(n²)         | O(1)   |
| Quick    | O(n log n)    | O(n log n)     | O(n²)         | O(log n)|
| Merge    | O(n log n)    | O(n log n)     | O(n log n)    | O(n)   |

## Выбор алгоритма

- Для малых массивов: **Insertion Sort**
- Для больших массивов: **Quick Sort** или **Merge Sort**
- Когда нужна стабильность: **Merge Sort**
''',
            subject_id=cs_subject.id,
            visibility='public',
            is_draft=False
        )
        conspectus2.tags.extend([tags[1], tags[2]])
        db.session.add(conspectus2)
        
        # Sample conspectus 3 - Physics
        conspectus3 = Conspectus(
            author_id=student.id,
            title='Основы квантовой механики',
            content='''# Квантовая механика

## Основные принципы

### 1. Принцип неопределённости Гейзенберга

Невозможно одновременно точно измерить координату и импульс частицы:

**Δx · Δp ≥ ℏ/2**

где ℏ — приведённая постоянная Планка.

### 2. Волновая функция

Состояние квантовой системы описывается волновой функцией Ψ(x, t).

Вероятность найти частицу в точке x: **P(x) = |Ψ(x)|²**

### 3. Уравнение Шрёдингера

Основное уравнение квантовой механики:

**iℏ ∂Ψ/∂t = ĤΨ**

где Ĥ — оператор Гамильтона (энергии).

## Квантование энергии

В микромире энергия принимает дискретные значения:

- Энергия фотона: **E = hν**
- Энергия электрона в атоме: **E_n = -13.6/n² эВ**

## Применения

1. **Квантовые компьютеры**
   - Кубиты вместо битов
   - Суперпозиция состояний

2. **Квантовая криптография**
   - Абсолютная защита данных
   - Обнаружение прослушивания

3. **Лазеры и полупроводники**
   - Светодиоды
   - Солнечные батареи

## Интересные факты

> "Если квантовая механика вас не шокировала, значит вы её не поняли" — Нильс Бор

- Кот Шрёдингера — мысленный эксперимент о суперпозиции
- Квантовая телепортация уже реализована!
- Туннельный эффект позволяет частицам проходить через барьеры
''',
            subject_id=physics_subject.id,
            visibility='public',
            is_draft=False
        )
        conspectus3.tags.append(tags[3])
        db.session.add(conspectus3)
        
        # Sample conspectus 4 - Draft
        conspectus4 = Conspectus(
            author_id=student.id,
            title='Машинное обучение: введение (черновик)',
            content='''# Машинное обучение

## Что это такое?

Машинное обучение (Machine Learning) — это...

*Этот конспект еще в разработке*
''',
            subject_id=cs_subject.id,
            visibility='private',
            is_draft=True
        )
        conspectus4.tags.append(tags[5])
        db.session.add(conspectus4)
        
        db.session.commit()
        
        print("Adding ratings and comments...")
        
        # Add some ratings
        rating1 = Rating(user_id=teacher.id, conspectus_id=conspectus1.id, vote=1)
        rating2 = Rating(user_id=student.id, conspectus_id=conspectus2.id, vote=1)
        rating3 = Rating(user_id=teacher.id, conspectus_id=conspectus3.id, vote=1)
        
        db.session.add_all([rating1, rating2, rating3])
        
        # Add some comments
        comment1 = Comment(
            user_id=teacher.id,
            conspectus_id=conspectus1.id,
            text='Отличный конспект! Очень понятно объясняете основы.',
            is_author_reply=False
        )
        
        comment2 = Comment(
            user_id=student.id,
            conspectus_id=conspectus2.id,
            text='Спасибо за подробный разбор алгоритмов сортировки!',
            is_author_reply=False
        )
        
        db.session.add_all([comment1, comment2])
        db.session.commit()
        
        # Update views count
        conspectus1.views_count = 15
        conspectus2.views_count = 23
        conspectus3.views_count = 8
        
        db.session.commit()
        
        print("Sample data created successfully!")
        print("\nTest users:")
        print("  Student: ivan_student / password123")
        print("  Teacher: maria_teacher / password123")

if __name__ == '__main__':
    create_sample_data()
