from flask import Flask, abort ,request
from flask_restful import Api, Resource, reqparse
from pymongo import MongoClient
import random
import string
import config
from cryptography.fernet import Fernet
import os

app = Flask(__name__)
api = Api(app)

client = MongoClient(config.MONGO_URI)
db = client.systems

mycollection = db.user

users = db.users

encryption_key = Fernet.generate_key()
cipher_suite = Fernet(encryption_key)


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Define the allowed file extensions
ALLOWED_EXTENSIONS = {'csv'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class UserResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        args = parser.parse_args()

        username = args['username']
        password = args['password']

        # Check if the username already exists
        existing_user = users.find_one({'username': username})
        if existing_user:
            return {'message': 'Username already exists'}, 400

        # Generate a random API key
        api_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(32))

        # Store user and API key in the database
        user_data = {'username': username, 'password': password, 'api_key': api_key}
        users.insert_one(user_data)

        return {'message': 'User created', 'api_key': api_key}, 201
class DataResource(Resource):
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str, required=True, help='API key is required')
        parser.add_argument('data_key', type=str, required=True, help='Data key is required')
        parser.add_argument('data', type=str, required=True, help='Data is required')
        args = parser.parse_args()

        api_key = args['api_key']
        data_key = args['data_key']
        data = args['data']

        # Check if API key exists in the database
        user = users.find_one({'api_key': api_key})
        if user is None:
            abort(401, message='Invalid API key')

        # Encrypt the data before storing
        encrypted_data = cipher_suite.encrypt(data.encode())

        # Store or update data in MongoDB using data_key
        data_entry = {
            'username': user['username'],
            'data_key': data_key,
            'data': encrypted_data
        }
        db.data_collection.replace_one({'username': user['username'], 'data_key': data_key}, data_entry, upsert=True)

        return {'message': 'Encrypted data stored or updated in MongoDB'}, 201
class Get_Data(Resource):
    def get(self, data_key):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str, required=True, help='API key is required')
        args = parser.parse_args()

        api_key = args['api_key']

        # Check if API key exists in the database
        user = users.find_one({'api_key': api_key})
        if user is None:
            abort(401, message='Invalid API key')

        # Retrieve encrypted data from MongoDB using data_key
        data_entry = db.data_collection.find_one({'username': user['username'], 'data_key': data_key})
        if data_entry is None:
            return {'message': 'Data not found'}, 404

        # Decrypt the data
        encrypted_data = data_entry['data']
        decrypted_data = cipher_suite.decrypt(encrypted_data).decode()

        return {'data': decrypted_data}, 200
class CSVUploadResource(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('api_key', type=str, required=True, help='API key is required')
        args = parser.parse_args()

        api_key = args['api_key']

        # Check if API key exists in the database
        user = users.find_one({'api_key': api_key})
        if user is None:
            abort(401, message='Invalid API key')

        # Check if the POST request contains a file named 'csv_file'
        if 'csv_file' not in request.files:
            return {'message': 'No CSV file provided'}, 400

        csv_file = request.files['csv_file']

        if csv_file and allowed_file(csv_file.filename):
            # Define the path based on the provided structure: data/api_key/name.csv
            filename = os.path.join(app.config['UPLOAD_FOLDER'], 'data', api_key, csv_file.filename)

            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # Save the uploaded CSV file, overwriting if the file already exists
            csv_file.save(filename)
            return {'message': 'CSV file uploaded successfully'}, 201
        else:
            return {'message': 'Invalid file format. Only CSV files are allowed.'}, 400

api.add_resource(CSVUploadResource, '/csv_upload')
api.add_resource(DataResource, '/send_data')
api.add_resource(Get_Data, '/get_data/<string:data_key>')
api.add_resource(UserResource, '/users')

if __name__ == '__main__':
    app.run(debug=True)
