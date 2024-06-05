import config


class Forklift:
    def __init__(self):
        self.max_speed = config.forklift['max_speed']
        self.length = config.forklift['length']
        self.width = config.forklift['width']
        self.payload = config.forklift['payload']

    def reload_settings(self):
        self.max_speed = config.forklift['max_speed']
        self.length = config.forklift['length']
        self.width = config.forklift['width']
        self.payload = config.forklift['payload']
    def reset(self):
        pass
