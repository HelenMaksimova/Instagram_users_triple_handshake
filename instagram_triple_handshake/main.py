from project_classes import TripleManager

first_name, second_name = input('Введите два имени пользователя через пробел: \n').split()

manager = TripleManager(first_name, second_name)
manager.run()

