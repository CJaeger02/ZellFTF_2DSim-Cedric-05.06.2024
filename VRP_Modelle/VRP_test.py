import numpy as np
import pandas as pd
from math import sqrt, ceil
import os

from FactoryObjects.Factory import Factory
from FactoryObjects.Warehouse import Warehouse
from FactoryObjects.Machine import Machine
from FactoryObjects.LoadingStation import LoadingStation
from FactoryObjects.AGV import AGV

from pulp import *


class VRP_cellAGV():
    """
    This class contains all the information for the VRP.
    """

    def __init__(self, factory: Factory):
        self.factory: Factory = factory
        self.agv = AGV()
        self.agv.thread_running = False
        self.agv.length = 500  # length of agv in mm
        self.agv.width = 500  # width of agv in mm
        self.amounts_of_objects = self.factory.get_amount_of_factory_objects()
        self.dimension = self.amounts_of_objects
        self.list_of_factory_objects = self.factory.get_list_of_factory_objects_loading_stations_first()
        self.distance_matrix = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        self.delivery_matrix = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        self.delivery_matrix_with_agv = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))

    def create_list_of_factory_objects(self):
        """
        This function writes all factory objects (Warehouses, Machines, Loading stations) to a list.
        :return: list_of_factory_objects_name
                 A list of all factory objects in the order mentioned above as a list
        """
        list_of_factory_objects_name = []
        for i in range(self.dimension):
            list_of_factory_objects_name.append(self.list_of_factory_objects[i].name)
        return list_of_factory_objects_name

    def create_dataframe_of_factory_objects(self):
        """
        This function creates a Pandas data frame for all factory objects from the list of all factory objects.
        :return: list_of_factory_objects_pd
                 The data frame with the factory objects.
        """
        list_of_factory_objects_name = []
        for i in range(self.dimension):
            list_of_factory_objects_name.append(self.list_of_factory_objects[i].name)
        list_of_factory_objects_pd = pd.DataFrame(list_of_factory_objects_name)
        list_of_factory_objects_pd['ID'] = list_of_factory_objects_pd.index + 1
        print(list_of_factory_objects_pd)
        return list_of_factory_objects_pd

    def create_file_for_list_of_factory_objects(self):
        """
        This function creates a CSV file from the Pandas data frame.
        The file is saved under the following path: data/Current_Factory/VRP/list_of_factory_objects.csv
        :return: None
        """
        list_of_factory_objects_pd = pd.DataFrame(self.create_list_of_factory_objects())
        list_of_factory_objects_pd.to_csv('data/Current_Factory/VRP/list_of_factory_objects.csv', sep=';')

    def get_distance_matrix(self):
        """
        Creates a matrix with the distance relationships between individual factory objects I and J.
        :return: distance_matrix as a 2D-np-array
        """
        # Die Matrix self.distance_matrix enthält die Distanzen aller Maschinen, Warenhäuser und Ladestationen.
        # Aus Gründen der Vereinfachung wird die Manhattan-Distanz verwendet. Mögliche Kollisionen werden ignoriert.
        distance_matrix = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        list_of_factory_objects_name = self.create_list_of_factory_objects()
        for i in range(self.dimension):
            for j in range(self.dimension):
                distance_x = abs(self.list_of_factory_objects[i].pos_x - self.list_of_factory_objects[j].pos_x)
                distance_y = abs(self.list_of_factory_objects[i].pos_y - self.list_of_factory_objects[j].pos_y)
                # Manhattan-Distance
                # self.distance_matrix[i][j] = distance_x + distance_y
                # distance_matrix[i][j] = distance_x + distance_y
                # Euklid-Distance
                self.distance_matrix[i][j] = sqrt((distance_x * distance_x) + (distance_y * distance_y))
                distance_matrix[i][j] = sqrt((distance_x * distance_x) + (distance_y * distance_y))
                # print(
                #     f'i = {i:02d} | j = {j:02d} --- X-Distanz = {distance_x:03d} | Y-Distanz = {distance_y:03d} --- '
                #     f'Distanz ={self.distance_matrix[i][j]}')
        distance_matrix_pd = pd.DataFrame(distance_matrix, columns=list_of_factory_objects_name,
                                          index=list_of_factory_objects_name)
        distance_matrix_pd.to_csv('data/Current_Factory/VRP/distance_matrix.csv', sep=';')
        print(distance_matrix.tolist())
        return distance_matrix

    def get_delivery_relationship(self):
        '''
        Creates a matrix with the delivery relationships between individual factory objects I and J.
        If a delivery from I to J takes place, a '1' is set at the corresponding position in the matrix.
        The matrix is saved as a CSV file under the path: data/Current_Factory/VRP/delivery_matrix.csv
        :return: delivery_matrix as a 2D-np-array
        '''
        list_of_factory_objects = self.factory.get_list_of_factory_objects_loading_stations_first()
        delivery_matrix = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        list_of_factory_objects_name = self.create_list_of_factory_objects()
        m = 1
        for i in range(self.dimension):
            for j in range(self.dimension):
                if type(list_of_factory_objects[i]) == Machine or type(list_of_factory_objects[i]) == Warehouse:
                    if type(list_of_factory_objects[j]) == Machine or type(list_of_factory_objects[j]) == Warehouse:
                        for output_product in list_of_factory_objects[i].output_products:
                            for input_product in list_of_factory_objects[j].input_products:
                                if output_product == input_product:
                                    # print('---------------------------------------------------------------------------')
                                    # print(f'{m}. Lieferbeziehung gefunden!')
                                    # print(f'Lieferung von {list_of_factory_objects[i].name} nach '
                                    #       f'{list_of_factory_objects[j].name}, Geliefertes Produkt: {input_product}')
                                    delivery_matrix[i][j] = 1
                                    self.delivery_matrix[i][j] = delivery_matrix[i][j]
                                    m += 1
        delivery_matrix_pd = pd.DataFrame(delivery_matrix, columns=list_of_factory_objects_name,
                                          index=list_of_factory_objects_name)
        delivery_matrix_pd.to_csv('data/Current_Factory/VRP/delivery_matrix.csv', sep=';')
        print(type(delivery_matrix))
        print(delivery_matrix)
        return delivery_matrix

    def get_amount_of_agv_for_delivery_as_matrix_free_configuration(self):
        """
        Creates a matrix with the delivery relationships between individual factory objects I and J,
        taking into account the number of AGVs required for transportation.
        If a delivery from I to J takes place, the number of AGVs required is set at the corresponding position in the
        matrix.
        The matrix is saved as a CSV file under the path: data/Current_Factory/VRP/delivery_matrix_with_agv.csv
        :return: delivery_matrix_with_agv as a 2D-np-array
        """
        list_of_factory_objects = self.factory.get_list_of_factory_objects_loading_stations_first()
        delivery_matrix_with_agv = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        list_of_factory_objects_name = self.create_list_of_factory_objects()
        m = 1
        for i in range(self.dimension):
            for j in range(self.dimension):
                if type(list_of_factory_objects[i]) == Machine or type(list_of_factory_objects[i]) == Warehouse:
                    if type(list_of_factory_objects[j]) == Machine or type(list_of_factory_objects[j]) == Warehouse:
                        for output_product in list_of_factory_objects[i].output_products:
                            for input_product in list_of_factory_objects[j].input_products:
                                if output_product == input_product:
                                    print('---------------------------------------------------------------------------')
                                    print(f'{m:03d}. Lieferbeziehung gefunden! '
                                          f'Lieferung von {list_of_factory_objects[i].name} nach '
                                          f'{list_of_factory_objects[j].name}, Geliefertes Produkt: {output_product}')
                                    delivery_matrix_with_agv[i][
                                        j] = self.check_amount_of_agvs_for_transport_free_configuration(
                                        self.factory.product_types[output_product])
                                    self.delivery_matrix_with_agv[i][j] = delivery_matrix_with_agv[i][j]
                                    m += 1
        delivery_matrix_with_agv_pd = pd.DataFrame(delivery_matrix_with_agv, columns=list_of_factory_objects_name,
                                                   index=list_of_factory_objects_name)
        delivery_matrix_with_agv_pd.to_csv('data/Current_Factory/VRP/delivery_matrix_with_agv.csv', sep=';')
        print(type(delivery_matrix_with_agv))
        print(delivery_matrix_with_agv.tolist())
        return delivery_matrix_with_agv

    def check_amount_of_agvs_for_transport_free_configuration(self, product):
        """
        Calculates the amount of agv, which is necessary to transport a product from I to J.
        Depending on the length of the product, it is determined how many AGVs have to travel one behind the other.
        Depending on the width of the product, the number of AGVs that must travel side by side is determined.
        :param product: product which is transported from I to J
        :return: amount_of_agv as an int
        """
        # print('Länge des Produkts : {}'.format(product['length']))
        # print('Breite des Produkts: {}'.format(product['width']))
        # print('Länge des AGV : {}'.format(self.agv.length / 1000))
        # print('Breite des AGV: {}'.format(self.agv.width / 1000))
        length_of_product = product['length']
        width_of_product = product['width']
        length_of_agv = self.agv.length / 1000
        width_of_agv = self.agv.width / 1000
        length_ratio = length_of_product / length_of_agv
        width_ratio = width_of_product / width_of_agv
        # print('Längenverhältnis : {}'.format(length_ratio))
        # print('Breitenverhältnis: {}'.format(width_ratio))
        agv_in_a_row = ceil(length_ratio)
        agv_side_by_side = ceil(width_ratio)
        amount_of_agv = agv_in_a_row * agv_side_by_side
        print('AGV hintereinander: {}'.format(agv_in_a_row))
        print('AGV nebeneinander : {}'.format(agv_side_by_side))
        print('AGV gesamt        : {}'.format(amount_of_agv))
        return amount_of_agv

    def get_amount_of_agv_for_delivery_as_matrix_1_4_6_configuration(self):
        """
        Creates a matrix with the delivery relationships between individual factory objects I and J,
        taking into account the number of AGVs required for transportation.
        If a delivery from I to J takes place, the number of AGVs required is set at the corresponding position in the
        matrix.
        The matrix is saved as a CSV file under the path: data/Current_Factory/VRP/delivery_matrix_with_agv.csv
        :return: delivery_matrix_with_agv as a 2D-np-array
        """
        list_of_factory_objects = self.factory.get_list_of_factory_objects_loading_stations_first()
        delivery_matrix_with_agv = np.zeros(shape=(self.amounts_of_objects, self.amounts_of_objects))
        list_of_factory_objects_name = self.create_list_of_factory_objects()
        m = 1
        for i in range(self.dimension):
            for j in range(self.dimension):
                if type(list_of_factory_objects[i]) == Machine or type(list_of_factory_objects[i]) == Warehouse:
                    if type(list_of_factory_objects[j]) == Machine or type(list_of_factory_objects[j]) == Warehouse:
                        for output_product in list_of_factory_objects[i].output_products:
                            for input_product in list_of_factory_objects[j].input_products:
                                if output_product == input_product:
                                    print('---------------------------------------------------------------------------')
                                    print(f'{m:03d}. Lieferbeziehung gefunden! '
                                          f'Lieferung von {list_of_factory_objects[i].name} nach '
                                          f'{list_of_factory_objects[j].name}, Geliefertes Produkt: {output_product}')
                                    delivery_matrix_with_agv[i][
                                        j] = self.check_amount_of_agvs_for_transport_1_4_6_configuration(
                                        self.factory.product_types[output_product])
                                    self.delivery_matrix_with_agv[i][j] = delivery_matrix_with_agv[i][j]
                                    m += 1
        delivery_matrix_with_agv_pd = pd.DataFrame(delivery_matrix_with_agv, columns=list_of_factory_objects_name,
                                                   index=list_of_factory_objects_name)
        delivery_matrix_with_agv_pd.to_csv('data/Current_Factory/VRP/delivery_matrix_with_agv.csv', sep=';')
        print(type(delivery_matrix_with_agv))
        print(delivery_matrix_with_agv.tolist())
        return delivery_matrix_with_agv

    def check_amount_of_agvs_for_transport_1_4_6_configuration(self, product):
        """
        Calculates the amount of agv, which is necessary to transport a product from I to J.
        Depending on the length of the product, it is determined how many AGVs have to travel one behind the other.
        Depending on the width of the product, the number of AGVs that must travel side by side is determined.
        :param product: product which is transported from I to J
        :return: amount_of_agv as an int
        """
        # print('Länge des Produkts : {}'.format(product['length']))
        # print('Breite des Produkts: {}'.format(product['width']))
        # print('Länge des AGV : {}'.format(self.agv.length / 1000))
        # print('Breite des AGV: {}'.format(self.agv.width / 1000))
        length_of_product = product['length']
        width_of_product = product['width']
        length_of_agv = self.agv.length / 1000
        width_of_agv = self.agv.width / 1000
        length_ratio = length_of_product / length_of_agv
        width_ratio = width_of_product / width_of_agv
        # print('Längenverhältnis : {}'.format(length_ratio))
        # print('Breitenverhältnis: {}'.format(width_ratio))
        if length_ratio <= 1:
            if width_ratio <= 1:
                agv_in_a_row = 1
                agv_side_by_side = 1
                amount_of_agv = agv_in_a_row * agv_side_by_side
                print('AGV hintereinander: {}'.format(agv_in_a_row))
                print('AGV nebeneinander : {}'.format(agv_side_by_side))
                print('AGV gesamt        : {}'.format(amount_of_agv))
                return amount_of_agv
        elif length_ratio <= 2:
            if width_ratio <= 2:
                agv_in_a_row = 2
                agv_side_by_side = 2
                amount_of_agv = agv_in_a_row * agv_side_by_side
                print('AGV hintereinander: {}'.format(agv_in_a_row))
                print('AGV nebeneinander : {}'.format(agv_side_by_side))
                print('AGV gesamt        : {}'.format(amount_of_agv))
                return amount_of_agv
        elif length_ratio <= 3:
            if width_ratio <= 2:
                agv_in_a_row = 3
                agv_side_by_side = 2
                amount_of_agv = agv_in_a_row * agv_side_by_side
                print('AGV hintereinander: {}'.format(agv_in_a_row))
                print('AGV nebeneinander : {}'.format(agv_side_by_side))
                print('AGV gesamt        : {}'.format(amount_of_agv))
                return amount_of_agv
        else:
            print('Transport nicht möglich')
            return None

        agv_in_a_row = ceil(length_ratio)
        agv_side_by_side = ceil(width_ratio)
        amount_of_agv = agv_in_a_row * agv_side_by_side
        print('AGV hintereinander: {}'.format(agv_in_a_row))
        print('AGV nebeneinander : {}'.format(agv_side_by_side))
        print('AGV gesamt        : {}'.format(amount_of_agv))
        return amount_of_agv

    def calculate_amount_of_objects(self):
        """
        Calculates the amount of all factory_objects inside the factory including:
            - Warehouses
            - Machines
            - Loading Stations
        This is necessary in order to obtain all the nodes for the deliveries.
        Each of the factory objects represents a node.
        :return: dim
                 amount of factory objects as an int
        """
        dim = 0
        for _ in self.factory.loading_stations:
            dim += 1
        for _ in self.factory.warehouses:
            dim += 1
        for _ in self.factory.machines:
            dim += 1
        print(f'Dimension Distance Matrix = {dim}')
        return dim

    def get_amount_of_available_agvs(self):
        amount_of_agvs = 0
        for i in range(len(self.factory.agvs)):
            amount_of_agvs += 1
        return amount_of_agvs


########################################################################################################################
###   BEISPIEL ALEX
########################################################################################################################

def create_default_factory(self):
    print('############################################')
    print('##### Creating default factory for VRP #####')
    print('############################################')
    self.length = 10
    self.width = 10
    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

    self.product_types['one'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['two'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['three'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['four'] = dict(length=0.5, width=0.5, weight=4.5)
    print(self.product_types)

    self.warehouses.append(Warehouse())
    self.warehouses[0].pos_x = 0
    self.warehouses[0].pos_y = 8
    self.warehouses[0].length = 5
    self.warehouses[0].width = 2
    self.warehouses[0].pos_input = [4, 8]
    self.warehouses[0].pos_output = [1, 8]
    self.warehouses[0].input_products = ['two']  # ['four']
    self.warehouses[0].output_products = ['one']
    self.warehouses[0].factory = self

    self.machines.append(Machine())
    self.machines[0].pos_x = 0
    self.machines[0].pos_y = 0
    self.machines[0].length = 3
    self.machines[0].width = 3
    self.machines[0].pos_input = [1, 2]
    self.machines[0].pos_output = [2, 1]
    self.machines[0].input_products = ['one']
    self.machines[0].output_products = ['two']
    self.machines[0].factory = self

    self.machines.append(Machine())
    self.machines[1].pos_x = 7
    self.machines[1].pos_y = 0
    self.machines[1].length = 3
    self.machines[1].width = 3
    self.machines[1].pos_input = [7, 1]
    self.machines[1].pos_output = [8, 2]
    self.machines[1].input_products = ['two']
    self.machines[1].output_products = ['three']
    self.machines[1].factory = self

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

    self.agvs.append(AGV([0, 6]))
    self.agvs[0].factory = self

    self.agvs.append(AGV([0, 7]))
    self.agvs[1].factory = self

    self.loading_stations.append(LoadingStation())
    self.loading_stations[0].pos_x = 0
    self.loading_stations[0].pos_y = 7
    self.loading_stations[0].length = 1
    self.loading_stations[0].width = 1

    self.loading_stations.append(LoadingStation())
    self.loading_stations[1].pos_x = 0
    self.loading_stations[1].pos_y = 6
    self.loading_stations[1].length = 1
    self.loading_stations[1].width = 1

    self.loading_stations.append(LoadingStation())
    self.loading_stations[2].pos_x = 0
    self.loading_stations[2].pos_y = 5
    self.loading_stations[2].length = 1
    self.loading_stations[2].width = 1

    self.loading_stations.append(LoadingStation())
    self.loading_stations[3].pos_x = 0
    self.loading_stations[3].pos_y = 4
    self.loading_stations[3].length = 1
    self.loading_stations[3].width = 1

    return self


########################################################################################################################
###   GITTERROST PRODUKTION
########################################################################################################################
def create_default_factory_2(self):
    print('############################################')
    print('##### Creating default factory for VRP #####')
    print('############################################')
    self.length = 200
    self.width = 100
    self.cell_size = 10
    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

    # Produkte innerhalb der Fabrik
    self.product_types['extern_0'] = dict(length=0.1, width=0.1, weight=0.1)  # in: W0
    self.product_types['extern_WA'] = dict(length=0.1, width=0.1, weight=0.1)  # out: W7
    self.product_types['coil'] = dict(length=1.5, width=0.8, weight=1000)  # out: W0 | in: M0, M1, M2
    self.product_types['anbauteile'] = dict(length=1.2, width=0.8, weight=200)  # out: W0 | in: M15
    self.product_types['randeinfassungen_1'] = dict(length=1, width=0.8, weight=50)  # out: W0 | in: W6
    self.product_types['spaltband_1'] = dict(length=1, width=0.8, weight=100)  # out: M0, M1, M2 | in: W1
    self.product_types['spaltband_2'] = dict(length=1, width=0.8, weight=100)  # out: W1 | in: M3, M4, M5, M6
    self.product_types['gestanzt_spaltband_1'] = dict(length=1, width=0.8, weight=95)  # out: M3, M4 | in: W2
    self.product_types['gestanzt_spaltband_2'] = dict(length=1, width=0.8, weight=95)  # out: W2 | in: M5, M6
    self.product_types['abfall'] = dict(length=0.5, width=0.4, weight=20)  # out: M3, M4, M13 | in: W5
    self.product_types['extern_1'] = dict(length=0.1, width=0.1, weight=0.1)  # out: W5
    self.product_types['abgelaengtes_spaltband_1'] = dict(length=1, width=0.5, weight=50)  # out: M5, M6 | in: W3
    self.product_types['abgelaengtes_spaltband_2'] = dict(length=1, width=0.5, weight=50)  # out: W3 | in: M7, M8, M9
    # self.product_types['rohrost'] = dict(length=1, width=0.8, weigth=20)  # out: M7, M8, M9 | in: M10, M11, M12
    self.product_types['rohrost_1'] = dict(length=1, width=0.8, weigth=20)  # out: M7 | in: M10
    self.product_types['rohrost_2'] = dict(length=1, width=0.8, weigth=20)  # out: M8 | in: M11
    self.product_types['rohrost_3'] = dict(length=1, width=0.8, weigth=20)  # out: M9 | in: M12
    self.product_types['randeinfassungen_2'] = dict(length=1, width=0.8, weight=50)  # out: W6 | in: M10, M11, M12
    self.product_types['rost'] = dict(length=1, width=0.8, weight=20)  # out: M10, M11, M12 | in: W4
    self.product_types['fertiger_rost'] = dict(length=1, width=0.8, weight=20)  # out: W4 | in: W7
    self.product_types['rost_weiterbearbeitung'] = dict(length=1, width=0.8, weight=20)  # out: W4 | in: M13, M14
    self.product_types['rost_geschnitten'] = dict(length=1, width=0.8, weight=20)  # out: M13 | in: M14

    # LAGER / WARENHÄUSER

    # Wareneingangslager
    self.warehouses.append(Warehouse())
    self.warehouses[0].name = 'Wareneingang'
    self.warehouses[0].pos_x = 0
    self.warehouses[0].pos_y = 0
    self.warehouses[0].input_products = ['extern_0']
    self.warehouses[0].output_products = ['coil', 'anbauteile', 'randeinfassungen_1']
    self.warehouses[0].factory = self

    # Zwischenlager 1 - Spaltbänder
    self.warehouses.append(Warehouse())
    self.warehouses[1].name = 'Zwischenlager - Spaltbänder'
    self.warehouses[1].pos_x = 50
    self.warehouses[1].pos_y = 50
    self.warehouses[1].input_products = ['spaltband_1']
    self.warehouses[1].output_products = ['spaltband_2']
    self.warehouses[1].factory = self

    # Zwischenlager 2 - gestanzte Spaltbänder
    self.warehouses.append(Warehouse())
    self.warehouses[2].name = 'Zwischenlager - gestanzte Spaltbänder'
    self.warehouses[2].pos_x = 80
    self.warehouses[2].pos_y = 90
    self.warehouses[2].input_products = ['gestanzt_spaltband_1']
    self.warehouses[2].output_products = ['gestanzt_spaltband_2']
    self.warehouses[2].factory = self

    # Zwischenlager 3 - abgelängte Spaltbänder
    self.warehouses.append(Warehouse())
    self.warehouses[3].name = 'Zwischenlager - abgelängte Spaltbänder'
    self.warehouses[3].pos_x = 100
    self.warehouses[3].pos_y = 10
    self.warehouses[3].input_products = ['abgelaengtes_spaltband_1']
    self.warehouses[3].output_products = ['abgelaengtes_spaltband_2']
    self.warehouses[3].factory = self

    # Zwischenlager 4 - Roste
    self.warehouses.append(Warehouse())
    self.warehouses[4].name = 'Zwischenlager - Roste'
    self.warehouses[4].pos_x = 160
    self.warehouses[4].pos_y = 50
    self.warehouses[4].input_products = ['rost']
    self.warehouses[4].output_products = ['fertiger_rost', 'rost_weiterbearbeitung']
    self.warehouses[4].factory = self

    # Zwischenlager 5 - Abfall gestanzte Spaltbänder
    self.warehouses.append(Warehouse())
    self.warehouses[5].name = 'Metallschrott'
    self.warehouses[5].pos_x = 100
    self.warehouses[5].pos_y = 100
    self.warehouses[5].input_products = ['abfall']
    self.warehouses[5].output_products = ['extern_1']
    self.warehouses[5].factory = self

    # Zwischenlager 6 - Randeinfassungen
    self.warehouses.append(Warehouse())
    self.warehouses[6].name = 'Zwischenlager - Randeinfassung'
    self.warehouses[6].pos_x = 140
    self.warehouses[6].pos_y = 0
    self.warehouses[6].input_products = ['randeinfassungen_1']
    self.warehouses[6].output_products = ['randeinfassungen_2']
    self.warehouses[6].factory = self

    # Warenausgangslager (7)
    self.warehouses.append(Warehouse())
    self.warehouses[7].name = 'Warenausgang'
    self.warehouses[7].pos_x = 200
    self.warehouses[7].pos_y = 0
    self.warehouses[7].input_products = ['fertiger_rost']
    self.warehouses[7].output_products = ['extern_WA']
    self.warehouses[7].factory = self

    # MASCHINEN

    # Maschine 0 - Coil spalten
    self.machines.append(Machine())
    self.machines[0].name = 'Spaltanlage 1'
    self.machines[0].pos_x = 20
    self.machines[0].pos_y = 20
    self.machines[0].input_products = ['coil']
    self.machines[0].output_products = ['spaltband_1']
    self.machines[0].factory = self

    # Maschine 1 - Coil spalten
    self.machines.append(Machine())
    self.machines[1].name = 'Spaltanlage 2'
    self.machines[1].pos_x = 20
    self.machines[1].pos_y = 50
    self.machines[1].input_products = ['coil']
    self.machines[1].output_products = ['spaltband_1']
    self.machines[1].factory = self

    # Maschine 2 - Coil spalten
    self.machines.append(Machine())
    self.machines[2].name = 'Spaltanlage 3'
    self.machines[2].pos_x = 20
    self.machines[2].pos_y = 80
    self.machines[2].input_products = ['coil']
    self.machines[2].output_products = ['spaltband_1']
    self.machines[2].factory = self

    # Maschine 3 - Stanzen
    self.machines.append(Machine())
    self.machines[3].name = 'Stanzanlage 1'
    self.machines[3].pos_x = 50
    self.machines[3].pos_y = 90
    self.machines[3].input_products = ['spaltband_2']
    self.machines[3].output_products = ['gestanzt_spaltband_1', 'abfall']
    self.machines[3].factory = self

    # Maschine 4 - Stanzen
    self.machines.append(Machine())
    self.machines[4].name = 'Stanzanlage 2'
    self.machines[4].pos_x = 70
    self.machines[4].pos_y = 90
    self.machines[4].input_products = ['spaltband_2']
    self.machines[4].output_products = ['gestanzt_spaltband_1', 'abfall']
    self.machines[4].factory = self

    # Maschine 5 - Ablängen
    self.machines.append(Machine())
    self.machines[5].name = 'Ablänganlage 1'
    self.machines[5].pos_x = 80
    self.machines[5].pos_y = 50
    self.machines[5].input_products = ['spaltband_2', 'gestanzt_spaltband_2']
    self.machines[5].output_products = ['abgelaengtes_spaltband_1']
    self.machines[5].factory = self

    # Maschine 6 - Ablängen
    self.machines.append(Machine())
    self.machines[6].name = 'Ablänganlage 2'
    self.machines[6].pos_x = 80
    self.machines[6].pos_y = 20
    self.machines[6].input_products = ['spaltband_2', 'gestanzt_spaltband_2']
    self.machines[6].output_products = ['abgelaengtes_spaltband_1']
    self.machines[6].factory = self

    # Maschine 7 - Setzen
    self.machines.append(Machine())
    self.machines[7].name = 'Setzanlage 1'
    self.machines[7].pos_x = 110
    self.machines[7].pos_y = 20
    self.machines[7].input_products = ['spaltband_2', 'abgelaengtes_spaltband_2']
    self.machines[7].output_products = ['rohrost_1']
    self.machines[7].factory = self

    # Maschine 8 - Setzen
    self.machines.append(Machine())
    self.machines[8].name = 'Setzanlage 2'
    self.machines[8].pos_x = 110
    self.machines[8].pos_y = 50
    self.machines[8].input_products = ['spaltband_2', 'abgelaengtes_spaltband_2']
    self.machines[8].output_products = ['rohrost_2']
    self.machines[8].factory = self

    # Maschine 9 - Setzen
    self.machines.append(Machine())
    self.machines[9].name = 'Setzanlage 3'
    self.machines[9].pos_x = 110
    self.machines[9].pos_y = 80
    self.machines[9].input_products = ['spaltband_2', 'abgelaengtes_spaltband_2']
    self.machines[9].output_products = ['rohrost_3']
    self.machines[9].factory = self

    # Maschine 10 - Randeinfassen
    self.machines.append(Machine())
    self.machines[10].name = 'Randeinfassung 1'
    self.machines[10].pos_x = 150
    self.machines[10].pos_y = 20
    self.machines[10].input_products = ['rohrost_1', 'randeinfassungen_2']
    self.machines[10].output_products = ['rost']
    self.machines[10].factory = self

    # Maschine 11 - Randeinfassen
    self.machines.append(Machine())
    self.machines[11].name = 'Randeinfassung 2'
    self.machines[11].pos_x = 150
    self.machines[11].pos_y = 50
    self.machines[11].input_products = ['rohrost_2', 'randeinfassungen_2']
    self.machines[11].output_products = ['rost']
    self.machines[11].factory = self

    # Maschine 12 - Randeinfassen
    self.machines.append(Machine())
    self.machines[12].name = 'Randeinfassung 3'
    self.machines[12].pos_x = 150
    self.machines[12].pos_y = 80
    self.machines[12].input_products = ['rohrost_3', 'randeinfassungen_2']
    self.machines[12].output_products = ['rost']
    self.machines[12].factory = self

    # Maschine 13 - Schneiden
    self.machines.append(Machine())
    self.machines[13].name = 'Schneidanlage 1'
    self.machines[13].pos_x = 160
    self.machines[13].pos_y = 90
    self.machines[13].input_products = ['rost_weiterbearbeitung']
    self.machines[13].output_products = ['rost_geschnitten', 'abfall']
    self.machines[13].factory = self

    # Maschine 14 - Sonder-Randeinfassung
    self.machines.append(Machine())
    self.machines[14].name = 'Sonder-Randeinfassung 1'
    self.machines[14].pos_x = 190
    self.machines[14].pos_y = 90
    self.machines[14].input_products = ['rost_geschnitten']
    self.machines[14].output_products = ['fertiger_rost']
    self.machines[14].factory = self

    # LOADING STATIONS - DEPOTS der AGVs

    '''# Version 1 - pro Ladestation 1 AGV
    i = 0
    n = 10  # Anzahl der Ladestationen = Anzahl der AGVs - pro Ladestation 1 AGV
    for i in range(n):
        self.loading_stations.append(LoadingStation)
        self.loading_stations[i].pos_x = 0
        self.loading_stations[i].pos_y = 10*i + 20
        self.agvs.append(AGV([0, 10*i+20]))
        self.agvs[i].factory = self'''

    # Version 2 - eine Ladestation als Depot mit allen AGVs
    self.loading_stations.append(LoadingStation)
    self.loading_stations[0].name = 'Depot_0_AGVs'
    self.loading_stations[0].pos_x = 0
    self.loading_stations[0].pos_y = 20
    i = 0
    n = 10  # Anzahl der AGVs
    for i in range(n):
        self.agvs.append(AGV([0, 20]))
        self.agvs[i].thread_running = False
        self.agvs[i].factory = self

    return self


########################################################################################################################
###   BEISPIEL mit 3 Maschinen
###   1x Transport mit 1 AGV, 1x Transport mit 4 AGV, 1x Transport mit 6 AGV
########################################################################################################################

def create_default_factory_3(self):
    print('############################################')
    print('##### Creating default factory for VRP #####')
    print('############################################')
    self.length = 10
    self.width = 10
    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

    self.product_types['lager_m1'] = dict(length=1.5, width=1, weight=4.5)
    self.product_types['m1_m2'] = dict(length=1, width=1, weight=4.5)
    self.product_types['m2_m3'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['m3_lager'] = dict(length=0.5, width=0.5, weight=4.5)
    print(self.product_types)

    self.warehouses.append(Warehouse())
    self.warehouses[0].pos_x = 0
    self.warehouses[0].pos_y = 8
    self.warehouses[0].length = 5
    self.warehouses[0].width = 2
    self.warehouses[0].pos_input = [4, 8]
    self.warehouses[0].pos_output = [1, 8]
    self.warehouses[0].input_products = ['m3_lager']  # ['four']
    self.warehouses[0].output_products = ['lager_m1']
    self.warehouses[0].factory = self

    self.machines.append(Machine())
    self.machines[0].name = 'M1'
    self.machines[0].pos_x = 0
    self.machines[0].pos_y = 0
    self.machines[0].length = 3
    self.machines[0].width = 3
    self.machines[0].pos_input = [1, 2]
    self.machines[0].pos_output = [2, 1]
    self.machines[0].input_products = ['lager_m1']
    self.machines[0].output_products = ['m1_m2']
    self.machines[0].factory = self

    self.machines.append(Machine())
    self.machines[1].name = 'M2'
    self.machines[1].pos_x = 7
    self.machines[1].pos_y = 0
    self.machines[1].length = 3
    self.machines[1].width = 3
    self.machines[1].pos_input = [7, 1]
    self.machines[1].pos_output = [8, 2]
    self.machines[1].input_products = ['m1_m2']
    self.machines[1].output_products = ['m2_m3']
    self.machines[1].factory = self

    self.machines.append(Machine())
    self.machines[2].name = 'M3'
    self.machines[2].pos_x = 7
    self.machines[2].pos_y = 7
    self.machines[2].length = 3
    self.machines[2].width = 3
    self.machines[2].pos_input = [8, 7]
    self.machines[2].pos_output = [7, 8]
    self.machines[2].input_products = ['m2_m3']
    self.machines[2].output_products = ['m3_lager']
    self.machines[2].factory = self

    self.loading_stations.append(LoadingStation())
    self.loading_stations[0].pos_x = 0
    self.loading_stations[0].pos_y = 7
    self.loading_stations[0].length = 1
    self.loading_stations[0].width = 1

    i = 0
    n = 6  # Anzahl der AGVs
    for i in range(n):
        self.agvs.append(AGV([0, 7]))
        self.agvs[i].thread_running = False
        self.agvs[i].factory = self

    return self


def create_default_factory_4(self):
    '''
    This function creates a default factory, where 3 machines get deliveries from a warehouse
    ________
    |     1|
    |      |
    |      |
    |D W  2|
    |      |
    |      |
    |      |
    |      |
    |     3|
    :param self:
    :return:
    '''
    print('############################################')
    print('##### Creating default factory for VRP #####')
    print('############################################')
    self.length = 100
    self.width = 100
    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()

    self.product_types['lager_m1'] = dict(length=1, width=1, weight=4.5)
    self.product_types['lager_m2'] = dict(length=1.5, width=0.5, weight=4.5)
    self.product_types['lager_m3'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['m1_m2'] = dict(length=1, width=1, weight=4.5)
    self.product_types['m2_m3'] = dict(length=0.5, width=0.5, weight=4.5)
    self.product_types['m3_lager'] = dict(length=0.5, width=0.5, weight=4.5)
    print(self.product_types)

    self.warehouses.append(Warehouse())
    self.warehouses[0].pos_x = 20
    self.warehouses[0].pos_y = 30
    self.warehouses[0].length = 1
    self.warehouses[0].width = 1
    self.warehouses[0].pos_input = [20, 30]
    self.warehouses[0].pos_output = [20, 30]
    self.warehouses[0].input_products = ['empty_w1']  # ['four']
    self.warehouses[0].output_products = ['lager_m1', 'lager_m2', 'lager_m3']
    self.warehouses[0].factory = self

    self.machines.append(Machine())
    self.machines[0].name = 'M1'
    self.machines[0].pos_x = 50
    self.machines[0].pos_y = 0
    self.machines[0].length = 1
    self.machines[0].width = 1
    self.machines[0].pos_input = [50, 0]
    self.machines[0].pos_output = [50, 0]
    self.machines[0].input_products = ['lager_m1']
    self.machines[0].output_products = ['emtpy_m1']
    self.machines[0].factory = self

    self.machines.append(Machine())
    self.machines[1].name = 'M2'
    self.machines[1].pos_x = 50
    self.machines[1].pos_y = 30
    self.machines[1].length = 1
    self.machines[1].width = 1
    self.machines[1].pos_input = [50, 30]
    self.machines[1].pos_output = [50, 30]
    self.machines[1].input_products = ['lager_m2']
    self.machines[1].output_products = ['empty_m2']
    self.machines[1].factory = self

    self.machines.append(Machine())
    self.machines[2].name = 'M3'
    self.machines[2].pos_x = 50
    self.machines[2].pos_y = 80
    self.machines[2].length = 1
    self.machines[2].width = 1
    self.machines[2].pos_input = [50, 80]
    self.machines[2].pos_output = [50, 80]
    self.machines[2].input_products = ['lager_m3']
    self.machines[2].output_products = ['empty_m3']
    self.machines[2].factory = self

    i = 0
    n = 12  # Anzahl der AGVs + Loading Stations

    # self.loading_stations.append(LoadingStation())
    # self.loading_stations[0].pos_x = 0
    # self.loading_stations[0].pos_y = 30 + i
    # self.loading_stations[0].length = 1
    # self.loading_stations[0].width = 1

    for i in range(n):
        self.loading_stations.append(LoadingStation())
        self.loading_stations[i].pos_x = 0
        self.loading_stations[i].pos_y = 30 + i
        self.loading_stations[i].length = 1
        self.loading_stations[i].width = 1

    for i in range(n):
        self.agvs.append(AGV([0, 30 + i]))
        self.agvs[i].thread_running = False
        self.agvs[i].factory = self

    return self


def create_default_logistic_environment(self):
    print('#########################################################')
    print('##### Creating default logistic environment for VRP #####')
    print('#########################################################')
    self.length = 100
    self.width = 100
    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()


def create_random_factory(self):
    print('###########################################')
    print('##### Creating random factory for VRP #####')
    print('###########################################')

    # FOLGENDE PARAMETER EINGEBEN
    self.length = 250
    self.width = 250

    self.amount_of_warehouses = 3
    self.amount_of_machines = 10
    self.amount_of_loading_stations = 10  # entspricht hier der Anzahl an AGVs

    self.no_columns = int(self.length // self.cell_size)
    self.no_rows = int(self.width // self.cell_size)
    self.factory_grid_layout = np.zeros(shape=(self.no_columns, self.no_rows)).tolist()


def cVRPPDmDnR(D, Q, A):

    """
    This is a cellular VRP with Pickup and Delivery with multiple depots for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs stay at their last delivery point.
    :return:
    """

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    I = []  # Orte/Knoten, die besucht werden (inkl. Depots, Abhol- und Lieferpunkten), wird aus der Distanzmatrix berechnet
    H = []  # Anzahl der Depots, wo die einzelnen FTF stehen - jedes FTF hat ein Depot
    J = []  # Orte/Knoten der Jobs (inkl. Abhol- und Lieferpunkten)
    for i in range(len(D)):
        I.append(i)
    for i in range(A):
        H.append(i)
    J = list(set(I).difference(H))
    print(f"H = {H}")
    print(f"I = {I}")
    print(f"J = {J}")
    print(f"D = {D}")
    print(type(D))
    print(f"Q = {Q}")
    print(f"A = {A}")

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and multiple Depots
    model = LpProblem("cVRPPDmDnR", LpMinimize)

    ##########################
    # Entscheidungsvariablen #
    ##########################

    # x_(i, j, k) ist eine Binärvariable, die 1 ist, wenn das Transportfahrzeug k von Ort i direkt zu Ort j fährt; sonst 0.
    x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in range(A)], 0, 1, LpBinary)

    ################
    # Zielfunktion #
    ################

    model += lpSum(
        D[i][j] * x[(i, j, k)] for i in I for j in I for k in range(A)), "Total_Distance"

    ####################
    # Nebenbedingungen #
    ####################

    ####################################
    # Fahrzeug k startet im Depot h == k
    for k in range(A):
        model += lpSum(x[(k, j, k)] for j in I) == 1

    # In jedem Depot steht am Anfang genau ein Fahrzeug.
    for i in H:
        model += lpSum(x[(i, j, k)] for j in I for k in range(A)) <= 1
        # model += lpSum(x[(i, j, k)] for j in I if i != j for k in range(A)) <= 1  # setzt x[(i, i, k)] = None

    ########################################################################################################
    # Flusskonservierung - Fluss von Fahrzeugen in den Knoten entspricht Fluss von Fahrzeugen aus dem Knoten
    for j in J:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I) >= lpSum(x[(j, h, k)] for h in I),
                      f"Flusskonservierung_Fahrzeug_{k}_Knoten_{j}")

    #####################################################################
    # Jeder Lieferung müssen die richtige Anzahl an AGV zugeordnet werden
    for i in I:
        for j in I:
            if i != j:
                num_vehicles = Q[i][j]
                if num_vehicles > 0:
                    print("i =", i, "j =", j, "Benötigte Fahrzeuge =", num_vehicles)
                    model += lpSum(x[(i, j, k)] for k in range(A)) == num_vehicles

    ####################################################################
    # Die Anzahl an AGVs, die die Depots verlassen und zu den Abholorten fahren, muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte und mehrere Depots.
    model += lpSum(x[(i, j, k)] for i in H for j in J for k in range(A)) >= max(Q[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(Q[i][j] for i in I for j in I)}")

    ######################################
    # Anzahl der Fahrzeuge berücksichtigen
    # Die Anzahl der Fahrzeuge, die vom Ort i zu Ort j fahren, darf die maximale Anzahl an Fahrzeugen nicht überschreiten.
    for i in I:
        for j in I:
            model += lpSum(x[(i, j, k)] for k in range(A)) <= A

    # Problem lösen
    solver = CPLEX_CMD()
    model.solve()

    result = {
        'status': LpStatus[model.status],
        'objective': value(model.objective),
        'variables': {v.name: v.varValue for v in model.variables()}
    }

    # Ergebnisse ausgeben
    for v in model.variables():
        if v.varValue > 0:
            print(v.name, "=", v.varValue)

    dict_result_1 = dict()
    dict_result_2 = dict()

    for k in range(A):
        for i in I:
            for j in I:
                if value(x[(i, j, k)]) == 1:
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x({i}, {j}, {k}) = {value(x[(i, j, k)])}.")

    for i in I:
        for j in I:
            for k in range(A):
                if value(x[(i, j, k)]) == 1:
                    dict_result_1[f'x({i},{j},{k})'] = value(x[i, j, k])

    for i in I:
        for j in I:
            for k in range(A):
                dict_result_2[f"x({i},{j},{k})"] = value(x[(i, j, k)])

    print(dict_result_1)
    print(dict_result_2)
    print(dict_result_2.items())

    with open("result_1.txt", "w") as convert_file:
        convert_file.write(json.dumps(dict_result_1))
    with open("result_1.json", "w") as outfile:
        json.dump(dict_result_1, outfile)

    with open("result_2.txt", "w") as convert_file:
        convert_file.write(json.dumps(dict_result_2))
    with open("result_2.json", "w") as outfile:
        json.dump(dict_result_2, outfile)

    print("Gesamte zurückgelegte Distanz =", value(model.objective))
    print("Status:", LpStatus[model.status])

    return dict_result_1, dict_result_2

def main():
    factory = Factory()

    # create_default_factory(factory)  # einfaches Beispiel
    # default_factory = create_default_factory_2(factory)  # Gitterrostproduktion
    # create_default_factory_3(factory)  # einfaches Beispiel
    default_factory = create_default_factory_4(factory)  # einfaches Beispiel
    # create_default_logistic_environment(factory)
    print(f"Default Factory AGVs: {default_factory.agvs}")
    print(f"Default Factory machines: {default_factory.machines}")

    # create_random_logistic_environment(factory)
    # create_random_factory(factory)  # randomisierte Fabrik mit Warenhäusern und Maschinen

    vrp = VRP_cellAGV(default_factory)

    vrp.create_file_for_list_of_factory_objects()
    vrp.create_dataframe_of_factory_objects()
    D = vrp.get_distance_matrix()
    print(f"D = {D.tolist()}")
    vrp.get_delivery_relationship()
    # Q = vrp.get_amount_of_agv_for_delivery_as_matrix_free_configuration()  # Konfiguration der FTF
    Q = vrp.get_amount_of_agv_for_delivery_as_matrix_1_4_6_configuration()  # Konfiguration der FTF
    print(f"Q = {Q.tolist()}")
    A = vrp.get_amount_of_available_agvs()

    model = cVRPPDmDnR(D, Q, A)


if __name__ == '__main__':
    main()

"""
Notizen:
- Transportkostensätze darstellen durch Matrixmultiplikation (Menge AGV * Distanz)
- Zeitabhängigkeit reinbringen: immer wenn ein Produkt neu angeboten/nachgefragt wird, Modell neu durchrechnen?!
"""
