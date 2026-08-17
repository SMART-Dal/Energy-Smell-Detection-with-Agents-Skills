"""C5.S3 -- and a test of `constant_sequence_literal`.

From Javad's ImproperDataStructure/AssignType. A constant tuple is stored whole
in the code object; a list literal is rebuilt with one store per element every
time the function runs.
"""

def before(n):
    total = 0
    for i in range(n):
        types = ["red", "blue", "green"]
        total += len(types[i % 3])
    return total


def after(n):
    total = 0
    for i in range(n):
        types = ("red", "blue", "green")
        total += len(types[i % 3])
    return total


def cases():
    return [("large", lambda: (300_000,)), ("small", lambda: (50,))]
