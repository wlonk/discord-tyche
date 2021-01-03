import os
import sys

from tyche import run

print("===========================")
print(f"Python Path: {sys.path}")
print(f"CWD: {os.getcwd()}")
print("Environ:")
print(os.environ)
print("===========================")

run()
