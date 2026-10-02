from string.templatelib import Interpolation, Template

nome = "Marco"
eta = 42
t = t"Ciao {nome}, hai {eta} anni"

print(type(t))                 # <class 'string.templatelib.Template'>
print(t.strings)               # ('Ciao ', ', hai ', ' anni')
for parte in t:
    if isinstance(parte, Interpolation):
        print("interpolazione:", parte.expression, "=", parte.value)
    else:
        print("testo:", repr(parte))
