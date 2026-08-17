class Car:
    def __init__(self, name, opening_year):
        self.name = name
        self.openinig_year = opening_year

    def compare_year(self, car1, car2):
        return car1.openinig_year > car2.openinig_year


car1 = Car("a", 1980)
car2 = Car("b", 1980)
car_obj = Car("", 0)
for _ in range(int(4e7)):
    a = car_obj.compare_year(car1, car2)