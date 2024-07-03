# general packages
import config
import numpy as np

# own packages
from FactoryObjects.AGV import AGV
from FactoryObjects.Forklift import Forklift
from FactoryObjects.LoadingStation import LoadingStation
from FactoryObjects.Machine import Machine
from FactoryObjects.Path import Path
from FactoryObjects.Product import Product
from FactoryObjects.Warehouse import Warehouse
from FactoryObjects.Product import Product


class Factory:
    def __init__(self):
        self.name = config.factory['name']
        self.length = config.factory['length']
        self.width = config.factory['width']
        self.cell_size = config.factory['cell_size']
        self.no_columns = int(self.length / self.cell_size)
        self.no_rows = int(self.width / self.cell_size)
        self.np_factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows))   # in this matrix all the data of
        # the factory cells is stored Zeilen, Spalten
        self.factory_grid_layout = self.np_factory_grid_layout.tolist()

        self.agvs = []
        self.loading_stations = []
        self.machines = []
        self.warehouses = []
        self.products = []
        self.product_types_list = []
        self.product_types = {'default_product_1': dict(length=500, width=500, weight=25.0)}
        self.create_default_product_types()
        self.products_id_count = 1000  # Product id's will start upwards with 1000

        # self.create_temp_factory_machines()
        # self.create_temp_factory_machines_2()

        # print(f'Factory Grid Layout: {self.factory_grid_layout}')
        # print(f'Product Types: {self.product_types}')

    def create_default_product_types(self):
        self.product_types['default_product_2'] = dict(length=1000, width=1000, weight=100.0)
        self.product_types['default_product_3'] = dict(length=1500, width=1000, weight=150.0)
        self.product_types['default_product_4'] = dict(length=500, width=1000, weight=50.0)
        print(self.product_types)
        self.dict_to_list()

    def load_factory(self):
        """

        :return:
        """
        self.product_types = []
        self.warehouses = []
        self.machines = []
        self.loading_stations = []

        pass

    def save_factory(self):
        pass

    def add_machine(self, factory_object):
        self.machines.append(factory_object)

    def add_warehouse(self, factory_object):
        self.warehouses.append(factory_object)

    def add_loading_station(self, factory_object):
        self.loading_stations.append(factory_object)

    def add_product_types(self, factory_object_list):
        self.product_types_list.append(factory_object_list)
        print(self.product_types_list)
        self.list_to_dict(self.product_types_list)

    def delete_machine(self, i):
        del self.machines[i]

    def delete_warehouse(self, i):
        del self.warehouses[i]

    def delete_loading_station(self, i):
        del self.loading_stations[i]

    def make_path(self):
        pass

    def make_default_products(self):
        # self.products.append(Product())
        pass

    def reload_settings(self):
        self.name = config.factory['name']
        self.length = config.factory['length']
        self.width = config.factory['width']
        self.cell_size = config.factory['cell_size']
        self.no_columns = int(self.length // self.cell_size)
        self.no_rows = int(self.width // self.cell_size)
        self.np_factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows))  # in this matrix all the data of
        # the factory cells is stored Zeilen, Spalten
        self.factory_grid_layout = self.np_factory_grid_layout.tolist()
        print(self.factory_grid_layout)

        # self.agv.reload_settings()
        # self.forklift.reload_settings()
        # self.machine.reload_settings()

    def reset(self):
        for agv in self.agvs:
            agv.reset()
        for machine in self.machines:
            machine.reset()
        for warehouse in self.warehouses:
            warehouse.reset()
        self.products = []

    def create_temp_factory_machines(self):
        self.length = 10
        self.width = 10
        self.no_columns = int(self.length // self.cell_size)
        self.no_rows = int(self.width // self.cell_size)
        self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

        self.warehouses.append(Warehouse())
        self.warehouses[0].pos_x = 0
        self.warehouses[0].pos_y = 8
        self.warehouses[0].length = 5
        self.warehouses[0].width = 2
        self.warehouses[0].pos_input = [4, 8]
        self.warehouses[0].pos_output = [1, 8]
        self.warehouses[0].input_products = ['product_4']    # ['four']
        self.warehouses[0].output_products = ['product_1']
        self.warehouses[0].factory = self
        self.warehouses[0].process_time = 10
        self.warehouses[0].rest_process_time = 10

        self.machines.append(Machine())
        self.machines[0].pos_x = 0
        self.machines[0].pos_y = 0
        self.machines[0].length = 3
        self.machines[0].width = 3
        self.machines[0].pos_input = [1, 2]
        self.machines[0].pos_output = [2, 1]
        self.machines[0].input_products = ['product_1']
        self.machines[0].output_products = ['product_2']
        self.machines[0].factory = self

        self.machines.append(Machine())
        self.machines[1].pos_x = 7
        self.machines[1].pos_y = 0
        self.machines[1].length = 3
        self.machines[1].width = 3
        self.machines[1].pos_input = [7, 1]
        self.machines[1].pos_output = [8, 2]
        self.machines[1].input_products = ['product_2']
        self.machines[1].output_products = ['product_3']
        self.machines[1].factory = self
        self.machines[1].process_time = 20
        self.machines[1].rest_process_time = 20


        self.machines.append(Machine())
        self.machines[2].pos_x = 7
        self.machines[2].pos_y = 7
        self.machines[2].length = 3
        self.machines[2].width = 3
        self.machines[2].pos_input = [8, 7]
        self.machines[2].pos_output = [7, 8]
        self.machines[2].input_products = ['product_3']
        self.machines[2].output_products = ['product_4']
        self.machines[2].factory = self
        self.machines[2].process_time = 10
        self.machines[2].rest_process_time = 10

        self.agvs.append(AGV([0, 4]))
        self.agvs[0].factory = self

        self.agvs.append(AGV([0, 5]))
        self.agvs[1].factory = self

        self.agvs.append(AGV([0, 6]))
        self.agvs[2].factory = self

        self.agvs.append(AGV([0, 7]))
        self.agvs[3].factory = self

        self.agvs.append(AGV([5, 9]))
        self.agvs[4].factory = self

        self.agvs.append(AGV([6, 9]))
        self.agvs[5].factory = self

        self.loading_stations.append(LoadingStation())
        self.loading_stations[0].pos_x = 0
        self.loading_stations[0].pos_y = 4
        self.loading_stations[0].length = 1
        self.loading_stations[0].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[1].pos_x = 0
        self.loading_stations[1].pos_y = 5
        self.loading_stations[1].length = 1
        self.loading_stations[1].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[2].pos_x = 0
        self.loading_stations[2].pos_y = 6
        self.loading_stations[2].length = 1
        self.loading_stations[2].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[3].pos_x = 0
        self.loading_stations[3].pos_y = 7
        self.loading_stations[3].length = 1
        self.loading_stations[3].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[4].pos_x = 5
        self.loading_stations[4].pos_y = 9
        self.loading_stations[4].length = 1
        self.loading_stations[4].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[5].pos_x = 6
        self.loading_stations[5].pos_y = 9
        self.loading_stations[5].length = 1
        self.loading_stations[5].width = 1

        self.fill_grid()
        print(self.factory_grid_layout)

        self.product_types['product_1'] = dict(length=1100, width=600, weight=4.5)  # dict(length=1100, width=600, weight=9.0)
        self.product_types['product_2'] = dict(length=600, width=600, weight=4.5)  # dict(length=600, width=600, weight=4.5)
        self.product_types['product_3'] = dict(length=250, width=250, weight=4.5)
        self.product_types['product_4'] = dict(length=250, width=250, weight=4.5)
        print(self.product_types)
        print(self.machines)

        # self.factory_grid_layout[5][5] = Path()

    def create_temp_factory_machines_2(self):
        self.length = 15
        self.width = 15
        self.no_columns = int(self.length // self.cell_size)
        self.no_rows = int(self.width // self.cell_size)
        self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

        self.warehouses.append(Warehouse())
        self.warehouses[0].pos_x = 0
        self.warehouses[0].pos_y = 13
        self.warehouses[0].length = 5
        self.warehouses[0].width = 2
        self.warehouses[0].pos_input = [4, 13]
        self.warehouses[0].pos_output = [1, 13]
        self.warehouses[0].input_products = ['default_product_1']
        self.warehouses[0].output_products = ['default_product_3']
        self.warehouses[0].factory = self

        self.machines.append(Machine())
        self.machines[0].pos_x = 0
        self.machines[0].pos_y = 0
        self.machines[0].length = 5
        self.machines[0].width = 3
        self.machines[0].pos_input = [1, 2]
        self.machines[0].pos_output = [4, 1]
        self.machines[0].input_products = ['default_product_3']
        self.machines[0].output_products = ['default_product_2']
        self.machines[0].factory = self

        self.machines.append(Machine())
        self.machines[1].pos_x = 10
        self.machines[1].pos_y = 0
        self.machines[1].length = 5
        self.machines[1].width = 5
        self.machines[1].pos_input = [10, 2]
        self.machines[1].pos_output = [13, 4]
        self.machines[1].input_products = ['default_product_2']
        self.machines[1].output_products = ['default_product_1']
        self.machines[1].factory = self
        self.machines[1].process_time = 10
        self.machines[1].rest_process_time = 10
        '''
        self.machines.append(Machine())
        self.machines[2].pos_x = 7
        self.machines[2].pos_y = 7
        self.machines[2].length = 3
        self.machines[2].width = 3
        self.machines[2].pos_input = [8, 7]
        self.machines[2].pos_output = [7, 8]
        self.machines[2].input_products = ['three']
        self.machines[2].output_products = ['four']
        self.machines[2].factory = self
        '''
        self.agvs.append(AGV([14, 14]))
        self.agvs[0].factory = self

        self.agvs.append(AGV([13, 14]))
        self.agvs[1].factory = self

        self.agvs.append(AGV([12, 14]))
        self.agvs[2].factory = self

        self.agvs.append(AGV([11, 14]))
        self.agvs[3].factory = self

        self.agvs.append(AGV([10, 14]))
        self.agvs[4].factory = self

        self.agvs.append(AGV([9, 14]))
        self.agvs[5].factory = self

        self.agvs.append(AGV([8, 14]))
        self.agvs[6].factory = self

        self.agvs.append(AGV([7, 14]))
        self.agvs[7].factory = self


        self.loading_stations.append(LoadingStation())
        self.loading_stations[0].pos_x = 14
        self.loading_stations[0].pos_y = 14
        self.loading_stations[0].length = 1
        self.loading_stations[0].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[1].pos_x = 13
        self.loading_stations[1].pos_y = 14
        self.loading_stations[1].length = 1
        self.loading_stations[1].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[2].pos_x = 12
        self.loading_stations[2].pos_y = 14
        self.loading_stations[2].length = 1
        self.loading_stations[2].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[3].pos_x = 11
        self.loading_stations[3].pos_y = 14
        self.loading_stations[3].length = 1
        self.loading_stations[3].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[4].pos_x = 10
        self.loading_stations[4].pos_y = 14
        self.loading_stations[4].length = 1
        self.loading_stations[4].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[5].pos_x = 9
        self.loading_stations[5].pos_y = 14
        self.loading_stations[5].length = 1
        self.loading_stations[5].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[6].pos_x = 8
        self.loading_stations[6].pos_y = 14
        self.loading_stations[6].length = 1
        self.loading_stations[6].width = 1

        self.loading_stations.append(LoadingStation())
        self.loading_stations[7].pos_x = 7
        self.loading_stations[7].pos_y = 14
        self.loading_stations[7].length = 1
        self.loading_stations[7].width = 1

        self.fill_grid()

    def fill_grid(self):
        self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()
        for warehouse in self.warehouses:
            self.add_to_grid(warehouse)

        for machine in self.machines:
            self.add_to_grid(machine)

        for loading_station in self.loading_stations:
            self.add_to_grid(loading_station)

    def add_to_grid(self, factor_object):
        for y in range(factor_object.width):
            for x in range(factor_object.length):
                self.factory_grid_layout[factor_object.pos_x + x][factor_object.pos_y + y] = factor_object
                # self.factory_grid_layout[factor_object.pos_y + y][factor_object.pos_x + x] = factor_object

    def delete_from_grid(self, factory_object):
        for y in range(factory_object.width):
            for x in range(factory_object.length):
                self.factory_grid_layout[factory_object.pos_x + x][factory_object.pos_y + y] = 0.0

    def check_collision(self, factory_object):
        for y in range(factory_object.width):
            for x in range(factory_object.length):
                if self.factory_grid_layout[factory_object.pos_x + x][factory_object.pos_y + y] != 0.0 and \
                        factory_object.name != \
                        self.factory_grid_layout[factory_object.pos_x + x][factory_object.pos_y + y].name:
                    # print('COLLISON!!!')
                    return True
        return False

    def check_factory_boundaries(self, factory_object):
        for y in range(factory_object.width):
            for x in range(factory_object.length):
                if factory_object.pos_x + x >= self.length or factory_object.pos_y + y >= self.width:
                    # print('OUT OF BOUNDARIES')
                    return True
        return False

    def check_for_duplicate_names(self, factory_object):
        if type(factory_object) == Machine:
            for i in range(len(self.machines)):
                if factory_object.name == self.machines[i].name and factory_object.id != self.machines[i].id:
                    return True
        elif type(factory_object) == Warehouse:
            for i in range(len(self.warehouses)):
                if factory_object.name == self.warehouses[i].name and factory_object.id != self.warehouses[i].id:
                    return True
        elif type(factory_object) == LoadingStation:
            for i in range(len(self.loading_stations)):
                if (factory_object.name == self.loading_stations[i].name and
                        factory_object.id != self.loading_stations[i].id):
                    return True
        else:
            print('No duplicate')
            return False

    def check_neighbours(self, factory_object):
        pass

    def get_factory_object_from_grid_layout(self, column, row):
        print(type(self.factory_grid_layout[column][row]))

    def get_color_grid(self):
        color_grid = np.ones(shape=(self.no_columns, self.no_rows)).tolist()
        for y in range(self.no_rows):
            for x in range(self.no_columns):
                if self.factory_grid_layout[x][y] == 0.0:
                    color_grid[x][y] = [255, 255, 255]
                else:
                    color_grid[x][y] = self.factory_grid_layout[x][y].get_color()
                    block_type = self.factory_grid_layout[x][y].get_block_type([x, y])
                    if block_type is not None or block_type != "machine_block":
                        if block_type == "input":
                            color_grid[x][y] = [255, 100, 100]
                        elif block_type == "output":
                            color_grid[x][y] = [100, 255, 100]
                        elif block_type == "input_output":
                            color_grid[x][y] = [255, 0, 220]

        return color_grid

    def create_product(self, product_name):
        new_product = Product()
        new_product.id = self.products_id_count
        new_product.length = self.product_types[product_name]['length']
        new_product.width = self.product_types[product_name]['width']
        new_product.weight = self.product_types[product_name]['weight']
        self.products_id_count += 10
        new_product.name = product_name
        new_product.stored_in = self
        self.products.append(new_product)
        return new_product

    def change_product(self, product, product_name):
        product.name = product_name
        product.length = self.product_types[product_name]['length']
        product.width = self.product_types[product_name]['width']
        product.weight = self.product_types[product_name]['weight']

    def get_type_by_name(self, factory_object_name):
        i = 0
        for machine in self.machines:
            if factory_object_name == self.machines[i].name:
                print(f' Get Type by Name: {factory_object_name}')
                print(f' Get Type by Name: {type(self.machines[i])}')
                return type(self.machines[i])
            i += 1
        i = 0
        for warehouse in self.warehouses:
            if factory_object_name == self.warehouses[i].name:
                print(f' Get Type by Name: {factory_object_name}')
                print(f' Get Type by Name: {type(self.warehouses[i])}')
                return type(self.warehouses[i])
            i += 1
        i = 0
        for loading_station in self.loading_stations:
            if factory_object_name == self.loading_stations[i].name:
                print(f' Get Type by Name: {factory_object_name}')
                print(f' Get Type by Name: {type(self.loading_stations[i])}')
                return type(self.loading_stations[i])
            i += 1
        return None

    def get_amount_of_factory_objects(self):
        # returns the amount of warehouses, machines and loading stations inside the factory
        dim = 0
        for _ in self.warehouses:
            dim += 1
        for _ in self.machines:
            dim += 1
        for _ in self.loading_stations:
            dim += 1
        print(f'Dimension Distance Matrix = {dim}')
        return dim

    def get_list_of_factory_objects(self):
        # returns a list with the factory objects in the order: warehouses, machines, loading stations
        list = []
        for warehouse in self.warehouses:
            list.append(warehouse)
        for machine in self.machines:
            list.append(machine)
        for loading_station in self.loading_stations:
            list.append(loading_station)
        print(f'List of Factory_Objects: {list}')
        return list

    def get_list_of_factory_objects_loading_stations_first(self):
        # returns a list with the factory objects in the order: warehouses, machines, loading stations
        list = []
        for loading_station in self.loading_stations:
            list.append(loading_station)
        for warehouse in self.warehouses:
            list.append(warehouse)
        for machine in self.machines:
            list.append(machine)
        print(f'List of Factory_Objects: {list}')
        return list

    def get_delivery_relationship(self):
        list_of_factory_objects = self.get_list_of_factory_objects()
        dimension = self.get_amount_of_factory_objects()
        m = 1
        for i in range(dimension):
            for j in range(dimension):
                if (type(list_of_factory_objects[i]) == Machine or type(list_of_factory_objects[i]) == Warehouse):
                    if (type(list_of_factory_objects[j]) == Machine or type(list_of_factory_objects[j]) == Warehouse):
                        for output_product in list_of_factory_objects[i].output_products:
                            for input_product in list_of_factory_objects[j].input_products:
                                if output_product == input_product:
                                    print(f'{m}. Lieferbeziehung gefunden!')
                                    print(f'Lieferung von {list_of_factory_objects[i].name} nach '
                                          f'{list_of_factory_objects[j].name}, Geliefertes Produkt: {input_product}')
                                    m += 1

    def get_delivery_relationship_between_objects(self, factory_object_1, factory_object_2):
        if (type(factory_object_1) == Machine or type(factory_object_1) == Warehouse):
            if (type(factory_object_2) == Machine or type(factory_object_2) == Warehouse):
                for output_product in factory_object_1.output_products:
                    for input_product in factory_object_2.input_products:
                        if output_product == input_product:
                            print(f'Lieferbeziehung gefunden!')
                            print(f'Lieferung von {factory_object_1} nach '
                                  f'{factory_object_2}, Geliefertes Produkt: {input_product}')
                            return True

    def get_agv_needed_for_product(self, product_name, agv):
        """
        Calculates the AGV positioning Matrix for a product delivery
        :param product_name: string
        :param agv: object
        :return: list
        """
        return [int(self.product_types[product_name]['width'] / agv.width + 0.99),
                int(self.product_types[product_name]['length'] / agv.length + 0.99)]

    def dict_to_list(self):
        for key, value in self.product_types.items():
            self.product_types_list.append([key, value['length'], value['width'], value['weight']])
            print(key)
            print(value)
        print(self.product_types_list)
        return self.product_types_list

    def list_to_dict(self, list):
        dict_product_types = {}
        for i in range(len(list)):
            dict_product_types[list[i][0]] = dict(length=list[i][1], width=list[i][2], weight=list[i][3])
        return dict_product_types

    def shout_down(self):
        for agv in self.agvs:
            agv.thread_running = False
