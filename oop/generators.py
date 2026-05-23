# Generators produce values one at a time using yield.
# They pause at yield and resume from the same spot next time.
# Great for large sequences, no need to store everything in memory.
# Reference: https://docs.python.org/3/tutorial/classes.html#generators


# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


# Generator function
def count_up(limit):
    n = 1
    while n <= limit:
        yield n  # pause, send n back, resume here next time
        n += 1


print(list(count_up(5)))  # [1, 2, 3, 4, 5]

# Step through manually with next()
gen = count_up(3)
print(next(gen))  # 1
print(next(gen))  # 2
print(next(gen))  # 3
# next(gen) here would raise StopIteration


# Generator expression (like list comprehension but lazy)
squares = (x * x for x in range(1, 6))
print(list(squares))  # [1, 4, 9, 16, 25]


# Practical: only yield what passes a condition
def even_numbers(limit):
    for n in range(limit):
        if n % 2 == 0:
            yield n


print(list(even_numbers(10)))  # [0, 2, 4, 6, 8]
