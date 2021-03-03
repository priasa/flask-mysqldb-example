#!venv/bin/python

import uuid

from flask import Flask
from flask import abort
from flask import jsonify
from flask import make_response
from flask import request
from flask import url_for

from flask_mysqldb import MySQL

app = Flask(__name__)
app.config['SECRET_KEY'] = uuid.uuid4().hex

app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '********'
app.config['MYSQL_DB'] = 'todoapps_py'

mysql = MySQL(app)


@app.route('/')
def index():
    print(uuid.uuid4())
    return "Hello, World!"


@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    cursor = mysql.connect.cursor()
    cursor.execute('''SELECT * FROM tbl_task''')
    results = cursor.fetchall()
    cursor.close()

    if len(results) == 0:
        abort(404)

    task_list = []
    for result in results:
        task = {
            'id': result[0],
            'title': result[1],
            'description': result[2],
            'done': True if result[3] == 1 else False
        }
        task_list.append(task)
    return make_response(jsonify({'tasks': [make_public_task(task) for task in task_list]}), 200)


@app.route('/todo/api/v1.0/tasks/<string:task_id>', methods=['GET'])
def get_task(task_id):
    task = find_task_by_id(task_id)
    if task is None:
        abort(404)

    return jsonify({'task': make_public_task(task)})


@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or 'title' not in request.json:
        abort(500)
    generated_id = str(uuid.uuid4())
    task = {
        'id': generated_id,
        'title': request.json['title'],
        'description': request.json.get('description', ''),
        'done': False
    }

    query = 'INSERT INTO tbl_task(id,title,description,is_done) VALUES ("{id}","{title}","{description}",{is_done})' \
        .format(id=generated_id, title=request.json['title'], description=request.json.get('description', ''),
                is_done=0)
    connection = mysql.connection
    cursor = connection.cursor()
    result = cursor.execute(str(query))
    if result < 1:
        abort(500)
    connection.commit()
    cursor.close()
    return make_response({'task': make_public_task(task)}, 201)


@app.route('/todo/api/v1.0/tasks/<string:task_id>', methods=['PUT'])
def update_task(task_id):
    task = find_task_by_id(task_id)
    if task is None:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and not isinstance(request.json['title'], type(u"")):
        abort(400)
    if 'description' in request.json and not isinstance(request.json['description'], type(u"")):
        abort(400)
    if 'done' in request.json:
        if type(request.json['done']) is not bool:
            abort(400)
        else:
            task['done'] = 1 if request.json.get('done') is True else 0
    task['title'] = request.json.get('title', task['title'])
    task['description'] = request.json.get('description', task['description'])

    query = 'UPDATE tbl_task set title="{title}", description="{description}", is_done={is_done} WHERE id="{id}"' \
        .format(id=task['id'], title=task['title'], description=task['description'], is_done=task['done'])
    connection = mysql.connection
    cursor = connection.cursor()
    result = cursor.execute(str(query))
    if result < 1:
        abort(500)
    connection.commit()
    cursor.close()
    return make_response({'task': make_public_task(task)}, 200)


@app.route('/todo/api/v1.0/tasks/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = find_task_by_id(task_id)
    if task is None:
        abort(404)
    query = 'DELETE FROM tbl_task WHERE id="{id}"'.format(id=task['id'])
    connection = mysql.connection
    cursor = connection.cursor()
    result = cursor.execute(str(query))
    if result < 1:
        abort(500)
    connection.commit()
    cursor.close()
    return make_response({'status': True}, 200)


@app.errorhandler(404)
def not_found_error(error):
    return make_response(jsonify({'error': 'Not Found'}), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({'error': 'Internal Server Error'}), 500)


@app.errorhandler(400)
def bad_request_error(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)


def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['url'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]

    return new_task


def find_task_by_id(task_id):
    cursor = mysql.connect.cursor()
    query = 'SELECT * FROM tbl_task WHERE id = "%(task_id)s"' % {"task_id": task_id}
    cursor.execute(str(query))
    results = cursor.fetchone()
    cursor.close()

    task = {}
    if results is not None:
        task['id'] = results[0]
        task['title'] = results[1]
        task['description'] = results[2]
        task['done'] = True if results[3] == 1 else False
    else:
        task = None
    return task


if __name__ == '__main__': app.run(debug=True)
