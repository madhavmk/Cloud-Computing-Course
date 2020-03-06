import requests 
  
temp_request = requests.get(url = "http://52.203.75.160:8080/api/v1/users") 
data = temp_request.json())
