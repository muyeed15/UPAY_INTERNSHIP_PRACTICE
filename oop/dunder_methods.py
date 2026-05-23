# Dunder (double underscore) methods let us define how built-in
# operations behave on our objects like str(), len(), == etc.
# Reference: https://docs.python.org/3/reference/datamodel.html#special-method-names


# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


class Book:
    def __init__(self, title, pages):
        self.title = title
        self.pages = pages

    def __str__(self):  # called by print() and str()
        return f"{self.title} ({self.pages} pages)"

    def __repr__(self):  # called by repr() for debugging
        return f"Book(title={self.title!r}, pages={self.pages})"

    def __len__(self):  # called by len()
        return self.pages

    def __eq__(self, other):  # called by ==
        return self.title == other.title and self.pages == other.pages


b1 = Book("Python Basics", 300)
b2 = Book("OOP Guide", 200)
b3 = Book("Python Basics", 300)

print(str(b1))  # Python Basics (300 pages)
print(repr(b2))  # Book(title='OOP Guide', pages=200)
print(len(b1))  # 300
print(b1 == b3)  # True
print(b1 == b2)  # False
