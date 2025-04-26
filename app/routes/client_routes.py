from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models import db, Client

client_bp = Blueprint('client_bp', __name__)

# Route to register a new client
@client_bp.route('/clients', methods=['POST'])
def register_client():
    data = request.get_json()

    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
        
    if Client.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Client with this email already exists'}), 409

    if 'date_of_birth' in data:
        try:
            # Parse the date string into a date object
            dob = datetime.strptime(data['date_of_birth'], '%d-%m-%Y').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use DD-MM-YYYY'}), 400
    else:
        dob = None

    client = Client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=dob,
        gender=data.get('gender'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        address=data.get('address'),
        programs=data.get('programs', [])
    )

    db.session.add(client)
    db.session.commit()

    return jsonify({'message': 'Client registered', 'id': client.id}), 201

# Route to list all clients
@client_bp.route('/clients', methods=['GET'])
def list_clients():
    try:
        clients = Client.query.all()
        client_list = []
        for c in clients:
            client_data = {
                'id': c.id,
                'first_name': c.first_name,
                'last_name': c.last_name,
                'email': c.email,
                'date_of_birth': c.date_of_birth,
                'gender': c.gender,
                'phone_number': c.phone_number,
                'address': c.address,
                'created_at': c.created_at,
                'programs': [{'id': p.id, 'name': p.name} for p in c.programs]
            }
            client_list.append(client_data)
        return jsonify(client_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to enroll a client in multiple health programs
@client_bp.route('/clients/<int:client_id>/enroll', methods=['POST'])
def enroll_client(client_id):
    data = request.get_json()
    program_ids = data.get('program_ids')  # A list of program ids to enroll the client in
    if not program_ids or not isinstance(program_ids, list):
        return jsonify({'error': 'Program/s id is required'}), 400

    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    from app.models import HealthProgram 
    for pid in program_ids:
        program = HealthProgram.query.get(pid)
        if program and program not in client.programs:
            client.programs.append(program)

    db.session.commit()

    return jsonify({'message': 'Client enrolled in programs'}), 200

# Route to get a client's profile
@client_bp.route('/clients/<int:client_id>', methods=['GET'])
def get_client_profile(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    return jsonify({
        'id': client.id,
        'first_name': client.first_name,
        'last_name': client.last_name,
        'email': client.email,
        'date_of_birth': client.date_of_birth,
        'gender': client.gender,
        'phone_number': client.phone_number,
        'address': client.address,
        'programs': [{'id': p.id, 'name': p.name} for p in client.programs]
    }), 200

# Route to update a client's profile
@client_bp.route('/clients/<int:client_id>', methods=['PUT'])
def update_client_profile(client_id):
    data = request.get_json()
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    for key, value in data.items():
        if hasattr(client, key):
            setattr(client, key, value)

    db.session.commit()

    return jsonify({'message': 'Client profile updated'}), 200

# Route to delete a client
@client_bp.route('/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    db.session.delete(client)
    db.session.commit()

    return jsonify({'message': 'Client deleted'}), 200

# Route to get all programs a client is enrolled in
@client_bp.route('/clients/<int:client_id>/programs', methods=['GET'])
def get_client_programs(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    programs = [{'id': p.id, 'name': p.name} for p in client.programs]
    return jsonify({'programs': programs}), 200

# Route to remove a client from a specific program
@client_bp.route('/clients/<int:client_id>/programs/<int:program_id>', methods=['DELETE'])
def remove_client_program(client_id, program_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    from app.models import HealthProgram 
    program = HealthProgram.query.get(program_id)
    if not program or program not in client.programs:
        return jsonify({'error': 'Program not found or not enrolled'}), 404

    client.programs.remove(program)
    db.session.commit()

    return jsonify({'message': 'Program removed from client'}), 200

# Route to enroll a client in a specific program
@client_bp.route('/clients/<int:client_id>/programs/<int:program_id>', methods=['POST'])
def enroll_client_in_program(client_id, program_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    from app.models import HealthProgram 
    program = HealthProgram.query.get(program_id)
    if not program:
        return jsonify({'error': 'Program not found'}), 404

    if program in client.programs:
        return jsonify({'message': 'Client already enrolled in this program'}), 200

    client.programs.append(program)
    db.session.commit()

    return jsonify({'message': 'Client enrolled in program'}), 200