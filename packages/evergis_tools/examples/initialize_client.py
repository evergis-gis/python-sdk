from time import perf_counter


from evergis_tools import Client
class Timer:
    def __init__(self, label):
        self.label = label

    def __enter__(self):
        self.start = perf_counter()
        return self

    def __exit__(self, *args):
        end = perf_counter()
        print(f"[{self.label}] done in {end - self.start:.3f} sec.")

with Timer("Client initialization"):
    client = Client()
    print(client)