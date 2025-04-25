from flask import Blueprint, request, jsonify
from app.models import db, HealthProgram
from datetime import datetime, timezone

program_bp = Blueprint('program_bp', __name__)

# Route to get to add a health program
@program_bp.route('/programs', methods=['POST'])
def create_program():
    data = request.get_json()
    name = data.get('name')
    description = data.get('description')

    if not name:
        return jsonify({'error': 'Program name is required'}), 400

    if HealthProgram.query.filter_by(name=name).first():
        return jsonify({'error': 'Program already exists'}), 409

    program = HealthProgram(name=name, description=description)
    db.session.add(program)
    db.session.commit()

    return jsonify({'message': 'Program created', 'id': program.id}), 201


# Route to get all health programs
@program_bp.route('/programs', methods=['GET'])
def list_programs():
    programs = HealthProgram.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'created_at': p.created_at.isoformat()
    } for p in programs]), 200

# Route to get a specific health program by ID
@program_bp.route('/programs/<int:program_id>', methods=['GET'])
def get_program(program_id):
    program = HealthProgram.query.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404

    return jsonify({
        'id': program.id,
        'name': program.name,
        'description': program.description,
        'created_at': program.created_at.isoformat()
    }), 200

# Route to update a health program
@program_bp.route('/programs/<int:program_id>', methods=['PUT'])
def update_program(program_id):
    data = request.get_json()
    program = HealthProgram.query.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404

    name = data.get('name')
    description = data.get('description')

    if name:
        program.name = name
    if description:
        program.description = description

    db.session.commit()

    return jsonify({'message': 'Program updated'}), 200

# Route to delete a health program
@program_bp.route('/programs/<int:program_id>', methods=['DELETE'])
def delete_program(program_id):
    program = HealthProgram.query.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404

    db.session.delete(program)
    db.session.commit()

    return jsonify({'message': 'Program deleted'}), 200

# Route to get all clients enrolled in a specific program
@program_bp.route('/programs/<int:program_id>/clients', methods=['GET'])
def get_program_clients(program_id):
    program = HealthProgram.query.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404

    clients = [{'id': c.id, 'name': c.first_name} for c in program.clients]
    return jsonify({'clients': clients}), 200