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

@app.route('/campus_map')
def campus_map():
    return render_template('campus_map.html')


def load_auditoriums():
    with open('static/data/auditoriums.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['auditoriums']

def search_auditoriums(query):
    auditoriums = load_auditoriums()
    results = []
    
    query_lower = query.lower()
    
    for room in auditoriums:
        if (query_lower in room['number'].lower() or 
            query_lower in room['description'].lower() or
            query_lower in room['building'].lower()):
            results.append(room)
    
    return results

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = []
    
    if query:
        results = search_auditoriums(query)
    
    return render_template('search.html', query=query, results=results)

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