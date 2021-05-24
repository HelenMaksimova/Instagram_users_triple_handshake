import pymongo
import collections
from subprocess import Popen
import json


class TripleManager:

    def __init__(self, first_name, second_name):
        self.first_name = first_name
        self.second_name = second_name
        self.tasks = collections.deque()
        self.parse_size = 10
        self.coil = 0
        self.user_names = []
        self.task_creator(self.parse_process, [self.first_name], self.coil)
        self.database = DatabaseManager('instagram_triple_handshake')

    def task_creator(self, callback, *args, **kwargs):
        self.tasks.append(self.get_task(callback, *args, **kwargs))

    def run(self):
        while self.tasks:
            task = self.tasks.popleft()
            user_names, coil = task()
            for name in user_names:
                friends = self.database.get_friends(name, coil)
                if self.second_name not in friends:
                    username_groups = [friends[pos:pos + self.parse_size]
                                       for pos in range(0, len(friends), self.parse_size)]
                    for group in username_groups:
                        self.task_creator(self.parse_process, group, self.coil + 1)
                else:
                    self.database.create_chain(name, coil, self.first_name, self.second_name)
                    return

    @staticmethod
    def get_task(callback, *args, **kwargs):
        def task():
            return callback(*args, **kwargs)
        return task

    @staticmethod
    def parse_process(user_names: list, coil):
        spyder = Popen(['python', 'crawl_manager.py', json.dumps(user_names), str(coil)])
        spyder.wait()
        return user_names, coil


class DatabaseManager:

    def __init__(self, db_name):
        client = pymongo.MongoClient()
        self.db = client[db_name]
        self.chain = []

    def get_friends(self, username, coil):
        collection = self.db[f'{coil:02d}.{username}']
        followers = {record['username'] for record in collection.find({'user_type': 'followers'})}
        following = {record['username'] for record in collection.find({'user_type': 'following'})}
        friends = list(followers.intersection(following))
        self.insert_friends(f'{coil:02d}.{username}', friends)
        self.delete_records(f'{coil:02d}.{username}', {'user_type': 'followers'})
        self.delete_records(f'{coil:02d}.{username}', {'user_type': 'following'})
        return friends

    def insert_friends(self, collection, friends):
        collection = self.db[collection]
        if friends:
            collection.insert_many({'username': name, 'user_type': 'friends'} for name in friends)

    def delete_records(self, collection, filter_dict):
        collection = self.db[collection]
        collection.delete_many(filter_dict)

    def create_chain(self, name, coil, first_name, second_name):
        if coil == 0:
            self.get_chain(first_name, second_name)
            return
        coil = f'{coil - 1:02d}'
        db_collections = self.db.collection_names(include_system_collections=False)
        for collection in db_collections:
            if collection.startswith(coil):
                friends = {record['username'] for record in self.db[collection].find({'user_type': 'friends'})}
                if name in friends:
                    self.chain.append(name)
                    name = collection.lstrip(f'{coil}.')
                    return self.create_chain(name, int(coil), first_name, second_name)

    def get_chain(self, first_name, second_name):
        self.chain.reverse()
        self.chain.append(second_name)
        self.chain.insert(0, first_name)
        print(self.chain)
