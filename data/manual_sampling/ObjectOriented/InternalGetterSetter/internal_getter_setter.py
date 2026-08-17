class User:
    def __init__(self, name):
        self._name = name

    def __get_name(self):
        return self._name

    def __set_name(self, name):
        self._name = name

    def print_name(self):
        return f"The name is {self.__get_name()}" 

    def change_name(self, new_name):
        self.__set_name(new_name)
        # do some logging operations


u = User("abc")
for i in range(10_000_000):
    u.print_name()
    u.change_name(f"user {i}")
