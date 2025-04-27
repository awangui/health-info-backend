from flask import Blueprint, request, jsonify
from datetime import datetime
from app.models import db, Client, HealthProgram

client_bp = Blueprint('client_bp', __name__)

@client_bp.route('/clients', methods=['POST'])
def register_client():
    data = request.get_json()
    
    # Required fields validation
    required_fields = ['first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
        
    # Email uniqueness check
    if 'email' in data and data['email']:
        if Client.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Client with this email already exists'}), 409

    # Date parsing with better error handling
    dob = None
    if 'date_of_birth' in data and data['date_of_birth']:
        try:
            # Handle both date string and empty values
            if isinstance(data['date_of_birth'], str) and data['date_of_birth'].strip():
                dob = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
        except ValueError as e:
            return jsonify({
                'error': f'Invalid date format. Use YYYY-MM-DD. Error: {str(e)}'
            }), 400

    # Process programs - handle both array of IDs and array of objects
    programs = []
    if 'programs' in data:
        if isinstance(data['programs'], list):
            # Extract IDs whether we get objects or direct IDs
            program_ids = []
            for p in data['programs']:
                if isinstance(p, dict) and 'id' in p:
                    program_ids.append(p['id'])
                elif isinstance(p, (int, str)):
                    try:
                        program_ids.append(int(p))
                    except ValueError:
                        continue
            
            # Get all valid programs
            programs = HealthProgram.query.filter(HealthProgram.id.in_(program_ids)).all()
        else:
            return jsonify({'error': 'Programs must be an array'}), 400

    # Create client
    client = Client(
        first_name=data['first_name'],
        last_name=data['last_name'],
        date_of_birth=dob,
        gender=data.get('gender'),
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        address=data.get('address')
    )

    # Add programs if any
    if programs:
        client.programs = programs

    try:
        db.session.add(client)
        db.session.commit()
        
      
        client_data = {
            'id': client.id,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'email': client.email,
            'date_of_birth': client.date_of_birth.isoformat() if client.date_of_birth else None,
            'gender': client.gender,
            'phone_number': client.phone_number,
            'address': client.address,
            'programs': [{'id': p.id, 'name': p.name} for p in client.programs]
        }
        
        return jsonify({
            'message': 'Client registered successfully',
            'client': client_data
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Database error',
            'details': str(e)
        }), 500


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
        'created_at': client.created_at,
        'programs': [{'id': p.id, 'name': p.name} for p in client.programs]
    }), 200

@client_bp.route('/clients/<int:client_id>', methods=['PUT'])
def update_client_profile(client_id):
    data = request.get_json()
    client = Client.query.get(client_id)
    
    if not client:
        return jsonify({'error': 'Client not found'}), 404

    try:
        # Handle program updates if present
        if 'programs' in data:
            if not isinstance(data['programs'], list):
                return jsonify({'error': 'Programs must be provided as an array'}), 400
                
            # Extract program IDs
            program_ids = []
            for item in data['programs']:
                if isinstance(item, dict) and 'id' in item:
                    program_ids.append(item['id'])
                elif isinstance(item, (int, str)):
                    try:
                        program_ids.append(int(item))
                    except ValueError:
                        continue
            
            # Verify all programs exist
            existing_programs = HealthProgram.query.filter(HealthProgram.id.in_(program_ids)).all()
            if len(existing_programs) != len(program_ids):
                found_ids = {p.id for p in existing_programs}
                missing_ids = [pid for pid in program_ids if pid not in found_ids]
                return jsonify({
                    'error': 'Some programs not found',
                    'missing_program_ids': missing_ids
                }), 404
            
            # Update programs 
            current_program_ids = {p.id for p in client.programs}
            new_program_ids = set(program_ids)
            
            # Remove programs not in new set
            for program in list(client.programs):  # Create a copy to iterate over
                if program.id not in new_program_ids:
                    client.programs.remove(program)
            
            # Add programs not in current set
            for program in existing_programs:
                if program.id not in current_program_ids:
                    client.programs.append(program)

        # Update other fields
        for key, value in data.items():
            if key != 'programs' and hasattr(client, key):
                # Special handling for date_of_birth if needed
                if key == 'date_of_birth' and isinstance(value, str):
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({
                            'error': f'Invalid date format for {key}. Use YYYY-MM-DD'
                        }), 400
                setattr(client, key, value)

        db.session.commit()
        
        # Return updated client data
        client_data = {
            'id': client.id,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'email': client.email,
            'date_of_birth': client.date_of_birth.isoformat() if client.date_of_birth else None,
            'programs': [{'id': p.id, 'name': p.name} for p in client.programs]
        }
        
        return jsonify({
            'message': 'Client updated successfully',
            'client': client_data
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update client',
            'details': str(e)
        }), 500


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