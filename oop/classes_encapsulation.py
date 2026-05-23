# A class is a blueprint for creating objects
# Reference: https://docs.python.org/3/tutorial/classes.html


# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


class BankAccount:

    bank_name = "PyBank"  # class variable: shared by all instances

    def __init__(self, owner, balance=0):
        self.owner = owner  # public: accessible from anywhere
        self._balance = balance  # protected: convention: don't touch from outside

    # @property lets us access a method like an attribute (no parentheses)
    @property
    def balance(self):
        return self._balance

    # setter runs when us do: acc.balance = 500
    @balance.setter
    def balance(self, amount):
        if amount < 0:
            raise ValueError("Balance cannot be negative")
        self._balance = amount

    def deposit(self, amount):
        self._balance += amount

    def withdraw(self, amount):
        if amount > self._balance:
            raise ValueError("Insufficient funds")
        self._balance -= amount

    # @classmethod gets the class (cls) instead of the instance
    # useful as an alternative constructor
    @classmethod
    def create_empty(cls, owner):
        return cls(owner, 0)

    # @staticmethod is just a helper function grouped inside the class
    # doesn't get self or cls
    @staticmethod
    def is_valid_amount(amount):
        return amount > 0


acc = BankAccount("Alice", 500)
acc.deposit(200)
print(acc.owner, acc.balance)  # Alice 700

acc2 = BankAccount.create_empty("Bob")
acc2.balance = 1000  # uses the setter
print(acc2.owner, acc2.balance)  # Bob 1000

print(BankAccount.is_valid_amount(-10))  # False
print(BankAccount.bank_name)  # PyBank
