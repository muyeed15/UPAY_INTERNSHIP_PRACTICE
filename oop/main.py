# Project: Animal Shelter


# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


# DECORATOR
def log_action(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        print(f"[LOG] {func.__name__} called")
        return result

    return wrapper


# CLASSES + INHERITANCE
class Animal:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        self.adopted = False

    def speak(self):
        return "..."

    def __str__(self):
        status = "adopted" if self.adopted else "available"
        return f"{self.name} (age {self.age}) : {status}"

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, age={self.age})"

    def __eq__(self, other):
        return self.name == other.name and self.age == other.age


class Dog(Animal):
    def speak(self):
        return "Woof!"


class Cat(Animal):
    def speak(self):
        return "Meow!"


# Kitten extends Cat and uses super()
class Kitten(Cat):
    def __init__(self, name):
        super().__init__(name, age=0)  # kittens are always age 0

    def speak(self):
        base = super().speak()  # reuse Cat's speak
        return f"{base} (tiny)"


# DUNDER METHODS on Shelter
class Shelter:
    def __init__(self, name):
        self.name = name
        self.animals = []

    def __str__(self):
        return f"Shelter '{self.name}' has {len(self.animals)} animals"

    def __len__(self):  # len(shelter)
        return len(self.animals)

    def __repr__(self):
        return f"Shelter(name={self.name!r}, count={len(self.animals)})"

    # DECORATOR applied to methods
    @log_action
    def add(self, animal):
        self.animals.append(animal)

    @log_action
    def adopt(self, name):
        for animal in self.animals:
            if animal.name == name and not animal.adopted:
                animal.adopted = True
                return animal
        return None

    # GENERATOR
    def available(self):
        for animal in self.animals:
            if not animal.adopted:
                yield animal

    # @property: access as shelter.available_count, not a method call
    @property
    def available_count(self):
        return sum(1 for a in self.animals if not a.adopted)


# RUNNING THE PROJECT
shelter = Shelter("Happy Paws")

shelter.add(Dog("Rex", 3))
shelter.add(Cat("Whiskers", 5))
shelter.add(Dog("Buddy", 2))
shelter.add(Kitten("Tiny"))

print()
print(shelter)
print(f"Total animals: {len(shelter)}")
print()

# Show all available animals using the generator
print("Available animals:")
for animal in shelter.available():
    print(" ", animal, ":", animal.speak())

print()

# Adopt one
adopted = shelter.adopt("Rex")
print(f"\nAdopted: {adopted}")

print(f"Available now : {shelter.available_count}")  # uses @property
print()

# Check equality using
dog_a = Dog("Rex", 3)
dog_b = Dog("Rex", 3)
dog_c = Dog("Buddy", 2)
print(f"dog_a == dog_b -> {dog_a == dog_b}")  # True
print(f"dog_a == dog_c -> {dog_a == dog_c}")  # False
