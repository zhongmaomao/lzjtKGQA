import requests
import re

# user_info = {'name': 'Bob', 'password': '123'}
# r = requests.post("http://127.0.0.1:5000/register", data=user_info)

# pattern = '([桂]{1}[A-Z]{1}[A-Z0-9]{5})'
# m = re.search(pattern, "傻子，有哪些人驾驶过桂B1155公交车？")
# print(m)

json_data = {'question': "傻子，有哪些人驾驶过桂B11555公交车？"}
print(json_data)

r = requests.post("http://lzjtanswer.zhinengwenda-test.svc.cluster.hz:31540/query", json=json_data)
# r = requests.post("http://127.0.0.1:5000/query", json=json_data)
print(r.headers)
print(r.text)
