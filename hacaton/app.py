from flask import Flask, render_template, request
import json

app = Flask(__name__)

# Простые данные
auditoriums = [
    {"number": "5-101", "building": "Главный корпус", "floor": "1 этаж", "description": "Большая лекционная аудитория"},
    {"number": "205", "building": "Главный корпус", "floor": "2 этаж", "description": "Компьютерный класс"},
    {"number": "301", "building": "Техническое здание", "floor": "3 этаж", "description": "Лаборатория физики"},
    {"number": "15", "building": "Библиотека", "floor": "1 этаж", "description": "Читальный зал"},
    {"number": "110", "building": "Главный корпус", "floor": "1 этаж", "description": "Актовый зал"},
]

events = [
    {"name": "Знакомство с научно-учебной комиссией", "date": "25 сентября", "place": "Карла Маркса 12, аудитория 9-501"},
    {"name": "Школа актива", "date": "3 октября", "place": "Школа студенческого профсоюзного актива «Активация»"},
]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        for room in auditoriums:
            if query.lower() in room['number'].lower() or query.lower() in room['description'].lower():
                results.append(room)
    
    return render_template('search.html', results=results, query=query)

@app.route('/events')
def events_page():
    return render_template('events.html', events=events)

@app.route('/clubs')
def clubs():
    # Загружаем данные о клубах из JSON файла
    try:
        with open('static/data/clubs.json', 'r', encoding='utf-8') as f:
            clubs_data = json.load(f)
        return render_template('clubs.html', clubs=clubs_data['clubs'])
    except FileNotFoundError:
        # Если файл не найден, возвращаем пустой список
        return render_template('clubs.html', clubs=[])

@app.route('/faq')
def faq_page():
    return render_template('faq.html')


if __name__ == '__main__':
    app.run(debug=True)