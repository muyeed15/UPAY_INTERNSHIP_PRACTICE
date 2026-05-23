# A decorator wraps a function to add extra behavior without changing it.
# @decorator_name is just shorthand for: func = decorator_name(func)
# Reference: https://docs.python.org/3/glossary.html#term-decorator

import time

# Author Information
__author__ = "Syed Abdullah Al Muyeed"
__email__ = "muyeed.al.abdullah@gmail.com"


# Timer decorator
def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result

    return wrapper


# Logger decorator
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"Calling: {func.__name__}{args}")
        return func(*args, **kwargs)

    return wrapper


@timer
def slow_add(a, b):
    time.sleep(0.05)
    return a + b


@logger
def greet(name):
    return f"Hello, {name}!"


print(slow_add(2, 3))  # slow_add took 0.05s
print(greet("Alice"))  # Calling: greet('Alice',)


# Stacking decorators
# Applied bottom-up: logger wraps greet first, then timer wraps that
@timer
@logger
def add(a, b):
    return a + b


add(3, 4)
