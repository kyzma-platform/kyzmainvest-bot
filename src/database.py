from pymongo import MongoClient
from os import getenv

class MongoDB:
    """ Class for working with MongoDB """
    def __init__(self):
        self.client = MongoClient(getenv('MONGODB'))
        self.db = self.client['kyzma']
        self.users_collection = self.db['users']
        self.parties_collection = self.db['parties']
        self.admin = getenv('ADMIN_ID')
        
    def find_users(self):
        """ Find all users in database. Returns list of dictionaries """
        return [self._convert_id(user) for user in self.users_collection.find({})]
    
    def find_user_id(self, user_id):
        """ Find user by user_id. Returns user dictionary or None """
        user = self.users_collection.find_one({"user_id": user_id})
        return self._convert_id(user) if user else None
    
    def find_user_nickname(self, nickname):
        """ Find user by nickname. Returns user dictionary or None """
        user = self.users_collection.find_one({"nickname": nickname})
        return self._convert_id(user) if user else None
    
    def add_user(self, username, user_id, name):
        """ Add user to the database. Takes username and user_id """
        if self.find_user_id(user_id):
            return f"User {username} already exists"
        
        new_user = {
            'user_id': user_id,
            'nickname': f"@{username}",
            'coins': 0,
            'last_farm_time': 0,
            'access_level': 'user',
            'debt': 0,
            'debt_limit_reached': False,
            'name': name,
            'deposit': 0,
            'grechka': 0,
            'party': None,
        }
        try:
            self.users_collection.insert_one(new_user)
            return f"User {username} added successfully"
        except Exception as e:
            self._log_error(f"Error adding user {username}: {e}")
            return f"Error adding user {username}: {e}"
        
    def update_user(self, user_id, updated_data):
        """ Update user data. Takes user_id and dictionary with fields to update """
        updated_data.pop('_id', None)
        self.users_collection.update_one({"user_id": user_id}, {"$set": updated_data})
        return f"User {user_id} updated successfully"
    
    def add_new_field(self, field_name, default_value):
        """ Add new field to all users in the database. Takes field name and default value """
        self.users_collection.update_many({}, {"$set": {field_name: default_value}})
        return f"Field {field_name} added successfully"

    def get_access_level(self, user_id):
        """ Returns the access level of the user. Returns: 'admin', 'user' or None """
        user = self.find_user_id(user_id)
        return user['access_level'] if user else None
    
    def find_party_name(self, party_name):
        """ Find party by party_name. Returns party dictionary or None """
        party = self.parties_collection.find_one({"party_name": party_name})
        return self._convert_id(party) if party else None

    def find_party_id(self, party_id):
        """ Find party by creator's user_id. Returns party dictionary or None """
        party = self.parties_collection.find_one({"party_creator": party_id})
        return self._convert_id(party) if party else None
    
    def add_party(self, party_name, party_creator):
        """ Add party to the database. Takes party name and creator's user_id """
        if self.find_party_name(party_name):
            return f"Партия с таким именем уже существует."
        
        new_party = {
            'party_name': party_name,
            'party_creator': party_creator,
            'party_members': [party_creator],
            'grechka': 0,
        }
        try:
            self.parties_collection.insert_one(new_party)
            return f"Поздравляем! Партия {party_name} была успешно зарегистрирована!"
        except Exception as e:
            self._log_error(f"Error adding party {party_name}: {e}")
            return f"Error creating party {party_name}: {e}"
    
    def update_party(self, party_name, **updated_data):
        """ Update party data. Takes party_name and dictionary with fields to update """
        updated_data.pop("_id", None)
        self.parties_collection.update_one({"party_name": party_name}, {"$set": updated_data})
        return f"Party {party_name} updated successfully"
    
    def add_party_member(self, party_name, user_id):
        """ Add user to the party. Takes party_name and user_id """
        party = self.find_party_name(party_name)
        user = self.find_user_id(user_id)
        if not party:
            return f"Партия {party_name} не найдена."
        
        if user_id in party['party_members']:
            return f"Гражданин {user['nickname']} уже состоит в партии {party_name}."
        
        party['party_members'].append(user_id)
        self.update_party(party_name, party_members=party['party_members'])
        user = self.find_user_id(user_id)
        updated_data = {'party': party_name}
        self.update_user(user_id, updated_data)
        return f"Гражданин {user['nickname']} успешно присоиденился к партии {party_name}!"
    
    def remove_party_member(self, party_name, user_id):
        """ Remove user from the party. Takes party_name and user_id """
        party = self.find_party_name(party_name)
        if not party:
            return f"Партия {party_name} не найдена."
        
        if user_id not in party['party_members']:
            return f"Гражданин {user_id} не состоит в партии {party_name}."
        
        party['party_members'].remove(user_id)
        self.update_party(party_name, party_members=party['party_members'])
        user = self.find_user_id(user_id)
        self.update_user(user_id, party=None)
        return f"Гражданин {user['nickname']} был изгнан с партии {party_name}."
    
    def _convert_id(self, document):
        """ Convert ObjectId to string for JSON serialization """
        if document and '_id' in document:
            document['_id'] = str(document['_id'])
        return document
    
    def _log_error(self, message):
        """ Log error message to admin """
        if self.admin:
            print(f"Admin ({self.admin}) Notification: {message}")
        print(message)
