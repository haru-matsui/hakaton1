from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)

# Функция для загрузки данных из JSON файла
def load_json_data(filename):
    filepath = os.path.join('static', 'data', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    
    # Загружаем данные об аудиториях из JSON
    auditoriums_data = load_json_data('auditoriums.json')
    auditoriums_list = auditoriums_data.get('auditoriums', [])
    
    if query:
        for room in auditoriums_list:
            if (query.lower() in room.get('number', '').lower() or 
                query.lower() in room.get('description', '').lower() or
                query.lower() in room.get('teacher', '').lower()):
                results.append(room)
    
    return render_template('search.html', results=results, query=query)

@app.route('/events')
def events_page():
    # Загружаем данные о событиях из JSON файла
    events_data = load_json_data('events.json')
    events_list = events_data.get('events', [])
    return render_template('events.html', events=events_list)

@app.route('/clubs')
def clubs():
    # Загружаем данные о клубах из JSON файла
    clubs_data = load_json_data('clubs.json')
    clubs_list = clubs_data.get('clubs', [])
    return render_template('clubs.html', clubs=clubs_list)

@app.route('/faq')
def faq_page():
    # Загружаем данные FAQ из JSON файла
    faq_data = load_json_data('faq.json')
    faq_list = faq_data.get('faq', [])
    return render_template('faq.html', faq=faq_list)


if __name__ == '__main__':
    app.run(debug=True)