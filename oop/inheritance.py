# Inheritance lets a child class reuse code from a parent class
# Reference: https://docs.python.org/3/tutorial/classes.html#inheritance


# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):  # child classes will override this
        return "..."

    def describe(self):
        return f"I am {self.name}"


# Dog inherits everything from Animal
class Dog(Animal):
    def speak(self):  # overrides parent's speak()
        return "Woof!"


class Cat(Animal):
    def speak(self):
        return "Meow!"


# super() calls the parent class method
class Puppy(Dog):
    def __init__(self, name, toy):
        super().__init__(name)  # reuse Dog/Animal's __init__
        self.toy = toy

    def describe(self):
        base = super().describe()  # reuse Animal's describe()
        return f"{base}, favorite toy: {self.toy}"


animals = [Dog("Rex"), Cat("Whiskers")]
for a in animals:
    print(a.name, "says", a.speak())

puppy = Puppy("Max", "ball")
print(puppy.describe())  # I am Max, favorite toy: ball
print(puppy.speak())  # Woof! inherited from Dog
