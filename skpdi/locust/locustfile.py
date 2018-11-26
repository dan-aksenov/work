from locust import HttpLocust, TaskSet

def login(l):
    l.client.post("/login", {"username":"Admin", "password":"admin321"})

def logout(l):
    l.client.post("/logout")

def index(l):
    l.client.get("/")

def MobileMissionFactRegistryView(l):
    l.client.get("/registry?code=additionRegistryForm&bk=ODH/Base/MobileMissionFactRegistryView")

class UserBehavior(TaskSet):
    tasks = {index: 2, MobileMissionFactRegistryView: 1}

    def on_start(self):
        login(self)

    def on_stop(self):
        logout(self)

class WebsiteUser(HttpLocust):
    task_set = UserBehavior
    min_wait = 5000
    max_wait = 9000