class Person:
    def __init__(self, name, age):
        self.__name__ = name
        self.__age__ = age
    
    def get_name(self):
        return self.__name__

    def set_name(self, name):
        self.__name__ = name
    
    def get_age(self):
        return self.__age__
    
    def set_age(self, age):
        self.__age__ = age
    
    def __str__(self):
        return f"{self.__name__}, {self.__age__}"

def compute_object(n: int):
    person_representations = []
    for i in range(n):
        person = Person(f"person {i}", i)
        person_representations.append(f"{person}")


n = int(1e6)
for _ in range(5):
    a = compute_object(n)