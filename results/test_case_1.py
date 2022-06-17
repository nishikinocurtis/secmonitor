import requests

print("Hello")
ret = requests.get("http://127.0.0.1:8080/")
print(ret.text)