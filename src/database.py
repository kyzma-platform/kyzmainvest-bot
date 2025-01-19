from pymongo import MongoClient
from dotenv import load_dotenv
from os import getenv

class MongoDB:
    """ Class for working with MongoDB"""
    def __init__(self):
        load_dotenv()
        self.client = MongoClient(getenv('MONGODB'))
        self.db = self.client['kyzma']
        self.users_collection = self.db['users']
        
    def find_users(self):
        """ Find all users in database. Returns list of dictionaries"""
        users_cursor = self.users_collection.find({})
        all_users = []
        for user in users_cursor:
            user['_id'] = str(user['_id'])
            all_users.append(user)
        return all_users
    
    def find_user_id(self, user_id):
        """ Find user by id. Returns user dictionary or None """
        user = self.users_collection.find_one({"user_id": user_id})
        if user:
            return user
        else:
            return None
        
    def find_user_nickname(self, nickname):
        """ Find user by nickname. Returns user dictionary or None """
        user = self.users_collection.find_one({"nickname": nickname})
        if user:
            return user
        else:
            return None
    
    def add_user(self, username, user_id, name):
        """ Add user to the database. Takes username and id """
        user = self.find_user_id(user_id)
        if user:
            print(f"User {username} already exists")
            return f"User {username} already exists"
        else:
            new_user = {
                'user_id': user_id,
                'nickname': username,
                'coins': 0,
                'last_farm_time': 0,
                'access_level': 'user',
                'debt': 0,
                'debt_limit_reached': False,
                'name': name,
            }
            self.users_collection.insert_one(new_user)
            print(f"User {username} added")
            return f"User {username} added"
        
    def update_user(self, user_id, update):
        """ Update user data. Takes id and dictionary with fields to update """
        self.users_collection.update_one({"user_id": user_id}, {"$set": update})
        return f"User {user_id} updated {update}"
    
    def add_new_field(self):
        self.users_collection.update_many(
            {},  # Empty filter, meaning all documents
            {"$set": {"deposit": 0}}  # Add 'name' field with None or default value
    )

    def get_access_level(self, user_id):
        """ Returns the access level of the user. Returns: 'admin', 'user' or None"""
        user = self.find_user_id(user_id)
        if user:
            return user['access_level']
        else:
            print("User not found")
            return None
        
        
        