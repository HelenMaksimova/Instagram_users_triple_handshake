import pymongo
import collections
from subprocess import Popen
import time
import json


class TripleManager:

    def __init__(self, first_name, second_name):
        self.first_name = first_name
        self.second_name = second_name
        self.tasks = collections.deque()
        self.chain = []
        self.parse_size = 10
        self.coil = 0
        self.user_names = []
        client = pymongo.MongoClient()
        self.db = client['instagram_triple_handshake']
        self.task_creator(self.parse_process, [self.first_name], self.coil)

    def task_creator(self, callback, *args, **kwargs):
        self.tasks.append(self.get_task(callback, *args, **kwargs))

    def get_friends(self, username, coil):
        collection = self.db[f'{coil:02d}.{username}']
        followers = {record['username'] for record in collection.find({'user_type': 'followers'})}
        following = {record['username'] for record in collection.find({'user_type': 'following'})}
        friends = list(followers.intersection(following))
        if friends:
            collection.insert_many({'username': name, 'user_type': 'friends'} for name in friends)
        return friends

    def run(self):
        while self.tasks:
            task = self.tasks.popleft()
            user_names, coil = task()
            time.sleep(7)
            for name in user_names:
                friends = self.get_friends(name, coil)
                if self.second_name not in friends:
                    username_groups = [friends[pos:pos + self.parse_size]
                                       for pos in range(0, len(friends), self.parse_size)]
                    for group in username_groups:
                        self.task_creator(self.parse_process, group, self.coil + 1)
                else:
                    self.get_chain(name, coil)
                    return

    def get_chain(self, name, coil):
        if coil == 0:
            self.chain.reverse()
            self.chain.append(self.second_name)
            self.chain.insert(0, self.first_name)
            print(self.chain)
            return
        coil = f'{coil - 1:02d}' if coil > 0 else f'{coil:02d}'
        db_collections = self.db.collection_names(include_system_collections=False)
        for collection in db_collections:
            if collection.startswith(coil):
                friends = {record['username'] for record in self.db[collection].find({'user_type': 'friends'})}
                if name in friends:
                    self.chain.append(name)
                    name = collection.lstrip(f'{coil}.')
                    return self.get_chain(name, int(coil))

    @staticmethod
    def get_task(callback, *args, **kwargs):
        def task():
            return callback(*args, **kwargs)
        return task

    @staticmethod
    def parse_process(user_names: list, coil):
        spyder = Popen(['python', 'main.py', json.dumps(user_names), str(coil)])
        spyder.wait()
        return user_names, coil


if __name__ == '__main__':
    manager = TripleManager('mystery_voice_xoxo', 'himnar_edel')
    manager.run()
