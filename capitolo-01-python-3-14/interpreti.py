from concurrent.futures import InterpreterPoolExecutor


def quadrato(n):
    return n * n


if __name__ == "__main__":
    with InterpreterPoolExecutor(max_workers=2) as esecutore:
        print(list(esecutore.map(quadrato, range(5))))
