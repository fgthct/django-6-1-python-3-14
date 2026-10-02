def converti(valore):
    try:
        return int(valore)
    except ValueError, TypeError:      # PEP 758: niente parentesi
        return None


print(converti("12"), converti("x"), converti(None))
