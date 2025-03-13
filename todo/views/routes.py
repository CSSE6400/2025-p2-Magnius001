from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
    # Get the set 
    args_dict = request.args.to_dict()
    if not set(args_dict.keys()).issubset({'title', 'description', 'completed', 'deadline_at', 'id', 'window'}):
        return jsonify({'error': 'Illegal field'}), 400
    # Convert "true"/"false" into 1/0
    if "completed" in args_dict.keys():
        args_dict["completed"] = int(args_dict["completed"] == 'true')

    window_flags = False
    window_value = 0
    if "window" in args_dict.keys():
        window_flags = True
        window_value = timedelta(days = int(args_dict["window"]))
        del args_dict["window"]
        
        # print(todo.deadline_at - datetime.now())
    # Filter db
    todos = Todo.query.filter_by(**args_dict)
    # Get results
    result = []
    for todo in todos:
        if window_flags and todo.deadline_at is not None and (todo.deadline_at - datetime.now()) <= window_value:
            result.append(todo.to_dict())
        elif not window_flags:
            result.append(todo.to_dict())
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    
    request_fields = set(request.json.keys())
    required_fields = {'title'}
    all_fields = {'title', 'completed', 'id', 'created_at', 'description', 'deadline_at'}
    if not required_fields <= request_fields:
        return jsonify({'error': 'Missing field'}), 400
    
    if not request_fields <= all_fields:
        return jsonify({'error': 'Illegal field'}), 400
    
    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    
    # Adds a new record to the database or will update an existing record.
    db.session.add(todo)
    # Commits the changes to the database.
    # This must be called for the changes to be saved.
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    request_fields = set(request.json.keys())
    all_fields = {'title', 'completed', 'created_at', 'description', 'deadline_at'}
    if not request_fields <= all_fields:
        return jsonify({'error': 'Illegal field'}), 400
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    if request.json.get('id', todo.id) != todo.id:
        return jsonify({'error': 'Bad request'}), 400
    
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()
    
    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
