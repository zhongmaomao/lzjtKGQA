import requests

# user_info = {'name': 'Bob', 'password': '123'}
# r = requests.post("http://127.0.0.1:5000/register", data=user_info)


json_data = {'question': "傻子，有哪些人驾驶过桂B11555公交车？"}
print(json_data)

r = requests.post("http://127.0.0.1:5000/query", json=json_data)
print(r.headers)
print(r.text)
