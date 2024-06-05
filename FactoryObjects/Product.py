import config


class Product:
    def __init__(self):
        self.id = config.product['id']
        self.name = config.product['name']
        self.length = config.product['length']
        self.width = config.product['width']
        self.weight = config.product['weight']
        self.stored_in = None

        self.list = []

    def config_product(self, id_no=config.product['id'], name=config.product['name'], length=config.product['length'],
                       width=config.product['width'], weight=config.product['weight']):
        self.list = []
        self.id = id_no
        self.list.append(id_no)
        self.name = name
        self.list.append(name)
        self.length = length
        self.list.append(length)
        self.width = width
        self.list.append(width)
        self.weight = weight
        self.list.append(weight)
        return self.list
