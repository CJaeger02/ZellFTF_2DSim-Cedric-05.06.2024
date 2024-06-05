from pulp import *  # LpProblem, LpMinimize, LpVariable, lpSum, LpBinary
import math
import numpy as np
import json


##############################
###                        ###
### PYTHON 3.8 verwenden!!!###
###                        ###
##############################


def or_test_mit_1_depot_total_distance():
    '''
    This is a cellular VRP with Pickup and Delivery with a single for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs drive back to the depot.
    :return:
    '''
    print(listSolvers(onlyAvailable=True))
    print(listSolvers())

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    I = []  # Orte/Knoten, die besucht werden, wird aus der Distanzmatrix berechnet
    A = 11  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

    # Distanzmatrix - Distanzen
    D = [
        [0, 2, 8, 5, 10],
        [2, 0, 6, 3, 8],
        [8, 6, 0, 3, 8],
        [5, 3, 3, 0, 5],
        [10, 8, 8, 5, 0]
    ]

    num_locations = len(D)
    for i in range(len(D)):
        I.append(i)
    print(f"I = {I}")
    print("D =", D)

    # Transport-/Gewichtsmatrix
    G = [
        [0, 0, 0, 0, 0],  # Keine Güter werden vom Depot aus transportiert
        [0, 0, 500, 1000, 50],  # Güter von Ort 1 zu Ort 2
        [0, 0, 0, 0, 0],  # Güter von Ort 2 zu Ort 4
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 3 wird nichts transportiert
        [0, 0, 0, 0, 0]  # Angenommen, von Ort 4 wird nichts transportiert
    ]
    print("G =", G)

    # Konfigurationsmatrix
    C_np = np.zeros(shape=(num_locations, num_locations))
    Q = C_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                Q[i][j] = 0
            elif G[i][j] / K <= 1:
                Q[i][j] = 1
            elif G[i][j] / K <= 4:
                Q[i][j] = 4
            elif G[i][j] / K <= 6:
                Q[i][j] = 6
            else:
                Q[i][j] = 1000
    print("Q =", Q)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and a single Depot
    model = LpProblem("cVRPPDsD", LpMinimize)

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

    ###########################################
    # Jedes Fahrzeug startet und endet im Depot
    for k in range(A):
        model += lpSum(x[(0, j, k)] for j in I) == 1  # Start im Depot
    for k in range(A):
        model += lpSum(x[(i, 0, k)] for i in I) == 1  # Ende im Depot

    ########################################################################################################
    # Flusskonservierung - Fluss von Fahrzeugen in den Knoten entspricht Fluss von Fahrzeugen aus dem Knoten
    for j in I[1:]:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I if i != j) == lpSum(x[(j, h, k)] for h in I if h != j),
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

    # Vom Depot zu den Abholorten - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die das Depot verlassen muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte
    model += lpSum(x[(0, i, k)] for i in I[1:] for k in range(A)) >= max(Q[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(Q[i][j] for i in I for j in I)}")

    # Anzahl der Fahrzeuge berücksichtigen
    # Die Anzahl der Fahrzeuge, die vom Ort i zu Ort j fahren, darf die maximale Anzahl an Fahrzeugen nicht überschreiten.
    # Bedingung ggf. überflüssig?
    for i in I:
        for j in I:
            model += lpSum(x[(i, j, k)] for k in range(A)) <= A

    # Problem lösen
    solver = CPLEX_PY()
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

    for k in range(A):
        for i in I:
            for j in I:
                if value(x[(i, j, k)]) == 1:
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x(i, k, j) = {value(x[(i, j, k)])}.")

    print("Gesamte zurückgelegte Distanz =", value(model.objective))
    print("Status:", LpStatus[model.status])


########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_mit_H_depots_total_distance():
    '''
    This is a cellular VRP with Pickup and Delivery with multiple depots for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs drive back to the depot.
    :return:
    '''

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    print(listSolvers())
    print(listSolvers(onlyAvailable=True))

    H = []  # Anzahl der Depots, wo die einzelnen FTF stehen - jedes FTF hat ein Depot
    I = []  # Orte/Knoten, die besucht werden (inkl. Depots, Abhol- und Lieferpunkten), wird aus der Distanzmatrix berechnet
    J = []  # Orte/Knoten der Jobs (inkl. Abhol- und Lieferpunkten)
    A = 6  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

    for i in range(A):
        H.append(i)

    # Distanzmatrix - Distanzen
    '''D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 80.0, 50.0, 100.0],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 21.0, 81.0, 51.0, 99.0], [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 22.0, 82.0, 52.0, 98.0],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 23.0, 83.0, 53.0, 97.0], [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 24.0, 84.0, 54.0, 96.0],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 25.0, 85.0, 55.0, 95.0],
         [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 0.0, 60.0, 30.0, 80.0],
         [80.0, 81.0, 82.0, 83.0, 84.0, 85.0, 60.0, 0.0, 30.0, 80.0],
         [50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 30.0, 30.0, 0.0, 50.0],
         [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 80.0, 80.0, 50.0, 0.0]]'''

    D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 58.309518948453004, 50.0, 70.71067811865476],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 20.024984394500787, 58.83026432033091, 50.00999900019995, 70.00714249274856],
         [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 20.09975124224178, 59.36328831862332, 50.039984012787215, 69.31089380465383],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 20.223748416156685, 59.90826320300064, 50.08991914547278, 68.62215385719105],
         [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 20.396078054371138, 60.4648658313239, 50.15974481593781, 67.94115100585212],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 20.615528128088304, 61.032778078668514, 50.24937810560445, 67.26812023536856],
         [20.0, 20.024984394500787, 20.09975124224178, 20.223748416156685, 20.396078054371138, 20.615528128088304, 0.0,
          42.42640687119285, 30.0, 58.309518948453004],
         [58.309518948453004, 58.83026432033091, 59.36328831862332, 59.90826320300064, 60.4648658313239,
          61.032778078668514, 42.42640687119285, 0.0, 30.0, 80.0],
         [50.0, 50.00999900019995, 50.039984012787215, 50.08991914547278, 50.15974481593781, 50.24937810560445, 30.0,
          30.0, 0.0, 50.0],
         [70.71067811865476, 70.00714249274856, 69.31089380465383, 68.62215385719105, 67.94115100585212,
          67.26812023536856, 58.309518948453004, 80.0, 50.0, 0.0]]

    for i in range(len(D)):
        I.append(i)
    num_locations = len(D)

    J = list(set(I).difference(H))
    num_job_locations = len(H)
    print(f"H = {H}")
    print(f"I = {I}")
    print(f"J = {J}")
    print(f"D = {D}")

    # Gewichtsmatrix
    G = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 0
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 1
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 2
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 3
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 4
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 5
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 80, 500, 1000],   # 6 zu 8, 9
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], # 7
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000],# 8 zu 9
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0.0]] # 9

    print("G =", G)

    # Konfigurationsmatrix
    Q_np = np.zeros(shape=(num_locations, num_locations))
    Q = Q_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                Q[i][j] = 0
            elif G[i][j] / K <= 1:
                Q[i][j] = 1
            elif G[i][j] / K <= 4:
                Q[i][j] = 4
            elif G[i][j] / K <= 6:
                Q[i][j] = 6
            else:
                Q[i][j] = 1000
    print("Q =", Q)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and multiple Depots
    model = LpProblem("cVRPPDmD", LpMinimize)

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
        model += lpSum(x[(k, j, k)] for j in I) == 1  # i != j entfernt, da Fahrzeuge auch im Depot bleiben können

    ##################################
    # Fahrzeug k endet im Depot h == k
    for k in range(A):
        model += lpSum(x[(j, k, k)] for j in I) == 1

    #####################################################
    # In jedem Depot steht am Anfang maximal ein Fahrzeug
    for i in H:
        model += lpSum(x[(i, j, k)] for j in I for k in range(A) if i == k) <= 1  # if i == k macht Bed oben überflüssig.

    ###################################################
    # In jedem Depot steht am Ende maximal ein Fahrzeug
    for j in H:
        model += lpSum(x[(i, j, k)] for i in I for k in range(A)) <= 1

    ########################################################################################################
    # Flusskonservierung - Fluss von Fahrzeugen in den Knoten entspricht Fluss von Fahrzeugen aus dem Knoten
    for j in I:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I if i != j) == lpSum(x[(j, h, k)] for h in I if h != j),
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
    # Von Depots zu den Abholorten - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die die Depots verlassen muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte und mehrere Depots
    model += lpSum(x[(i, j, k)] for i in H for j in J for k in range(A)) >= max(Q[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(Q[i][j] for i in I for j in I)}")

    ######################################
    # Anzahl der Fahrzeuge berücksichtigen
    # Die Anzahl der Fahrzeuge, die vom Ort i zu Ort j fahren, darf die maximale Anzahl an Fahrzeugen nicht überschreiten.
    # Bedingung ggf. überflüssig?
    for i in I:
        for j in I:
            model += lpSum(x[(i, j, k)] for k in range(A)) <= A

    # Problem lösen
    solver = CPLEX_CMD()
    model.solve(solver)

    result = {
        'status': LpStatus[model.status],
        'objective': value(model.objective),
        'variables': {v.name: v.varValue for v in model.variables()}
    }

    # Ergebnisse ausgeben
    for v in model.variables():
        if v.varValue > 0:
            print(v.name, "=", v.varValue)

    for i in I:
        for j in I:
            for k in range(A):
                if value(x[(i, j, k)]) == 1 and (i <= 5 or j <= 5):
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x(i, j, k) = {value(x[(i, j, k)])}.")

    print("Gesamte zurückgelegte Distanz =", value(model.objective))
    print("Status:", LpStatus[model.status])


########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_mit_1_depot_total_distance_no_return_to_depot():
    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    I = []  # Orte/Knoten, die besucht werden, wird aus der Distanzmatrix berechnet
    A = 6  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

    # Distanzmatrix - Distanzen
    D = [
        [0, 2, 8, 5, 10],
        [2, 0, 6, 3, 8],
        [8, 6, 0, 3, 8],
        [5, 3, 3, 0, 5],
        [10, 8, 8, 5, 0]
    ]

    num_locations = len(D)
    for i in range(len(D)):
        I.append(i)
    print(f"I = {I}")
    print("D =", D)

    # Transport-/Gewichtsmatrix
    G = [
        [0, 0, 0, 0, 0],  # Keine Güter werden vom Depot aus transportiert
        [0, 0, 1000, 1000, 1000],  # Güter von Ort 1 zu Ort 2
        [0, 0, 0, 0, 0],  # Güter von Ort 2 zu Ort 4
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 3 wird nichts transportiert
        [0, 0, 0, 0, 0]  # Angenommen, von Ort 4 wird nichts transportiert
    ]
    print("G =", G)

    # Konfigurationsmatrix
    C_np = np.zeros(shape=(num_locations, num_locations))
    Q = C_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                Q[i][j] = 0
            elif G[i][j] / K <= 1:
                Q[i][j] = 1
            elif G[i][j] / K <= 4:
                Q[i][j] = 4
            elif G[i][j] / K <= 6:
                Q[i][j] = 6
            else:
                Q[i][j] = 1000
    print("Q =", Q)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and a single Depot
    model = LpProblem("cVRPPDsD", LpMinimize)

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

    ###########################################
    # Jedes Fahrzeug startet im Depot
    for k in range(A):
        model += lpSum(x[(0, j, k)] for j in I) == 1  # Start im Depot

    ########################################################################################################
    # Flusskonservierung - Fluss von Fahrzeugen in den Knoten entspricht Fluss von Fahrzeugen aus dem Knoten
    #                    - außer für das Depot
    for j in I[1:]:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I if i != j) == lpSum(x[(j, h, k)] for h in I[1:] if h != j),
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

    # Vom Depot zu den Abholorten - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die das Depot verlassen muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte
    model += lpSum(x[(0, i, k)] for i in I[1:] for k in range(A)) >= max(Q[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(Q[i][j] for i in I for j in I)}")

    # Anzahl der Fahrzeuge berücksichtigen
    # Die Anzahl der Fahrzeuge, die vom Ort i zu Ort j fahren, darf die maximale Anzahl an Fahrzeugen nicht überschreiten.
    # Bedingung ggf. überflüssig?
    for i in I:
        for j in I:
            model += lpSum(x[(i, j, k)] for k in range(A)) <= A

    # Problem lösen
    solver = CPLEX_PY()
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

    for k in range(A):
        for i in I:
            for j in I:
                if value(x[(i, j, k)]) == 1:
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x(i, k, j) = {value(x[(i, j, k)])}.")

    print("Gesamte zurückgelegte Distanz =", value(model.objective))
    print("Status:", LpStatus[model.status])

########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_mit_H_depots_total_distance_no_return_to_depot():

    """
    This is a cellular VRP with Pickup and Delivery with multiple depots for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs stay at their last delivery point.
    :return:
    """

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    H = []  # Anzahl der Depots, wo die einzelnen FTF stehen - jedes FTF hat ein Depot
    I = []  # Orte/Knoten, die besucht werden (inkl. Depots, Abhol- und Lieferpunkten), wird aus der Distanzmatrix berechnet
    J = []  # Orte/Knoten der Jobs (inkl. Abhol- und Lieferpunkten)
    A = 6  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

    for i in range(A):
        H.append(i)

    # Distanzmatrix - Distanzen
    D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 80.0, 50.0, 100.0],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 21.0, 81.0, 51.0, 99.0],
         [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 22.0, 82.0, 52.0, 98.0],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 23.0, 83.0, 53.0, 97.0],
         [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 24.0, 84.0, 54.0, 96.0],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 25.0, 85.0, 55.0, 95.0],
         [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 0.0, 60.0, 30.0, 80.0],
         [80.0, 81.0, 82.0, 83.0, 84.0, 85.0, 60.0, 0.0, 30.0, 80.0],
         [50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 30.0, 30.0, 0.0, 50.0],
         [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 80.0, 80.0, 50.0, 0.0]]

    '''D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 58.309518948453004, 50.0, 70.71067811865476],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 20.024984394500787, 58.83026432033091, 50.00999900019995, 70.00714249274856],
         [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 20.09975124224178, 59.36328831862332, 50.039984012787215, 69.31089380465383],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 20.223748416156685, 59.90826320300064, 50.08991914547278, 68.62215385719105],
         [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 20.396078054371138, 60.4648658313239, 50.15974481593781, 67.94115100585212],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 20.615528128088304, 61.032778078668514, 50.24937810560445, 67.26812023536856],
         [20.0, 20.024984394500787, 20.09975124224178, 20.223748416156685, 20.396078054371138, 20.615528128088304, 0.0,
          42.42640687119285, 30.0, 58.309518948453004],
         [58.309518948453004, 58.83026432033091, 59.36328831862332, 59.90826320300064, 60.4648658313239,
          61.032778078668514, 42.42640687119285, 0.0, 30.0, 80.0],
         [50.0, 50.00999900019995, 50.039984012787215, 50.08991914547278, 50.15974481593781, 50.24937810560445, 30.0,
          30.0, 0.0, 50.0],
         [70.71067811865476, 70.00714249274856, 69.31089380465383, 68.62215385719105, 67.94115100585212,
          67.26812023536856, 58.309518948453004, 80.0, 50.0, 0.0]]'''

    for i in range(len(D)):
        I.append(i)
    num_locations = len(D)

    J = list(set(I).difference(H))
    num_job_locations = len(H)
    print(f"H = {H}")
    print(f"I = {I}")
    print(f"J = {J}")
    print(f"D = {D}")

    # Gewichtsmatrix
    G = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 0
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 2
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 3
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 4
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 5
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 80, 500, 1000],  # 6 zu 8, 9
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 7
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000],  # 8 zu 9
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000, 0, 0.0]]  # 9 zu 7

    print("G =", G)

    # Konfigurationsmatrix
    Q_np = np.zeros(shape=(num_locations, num_locations))
    Q = Q_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                Q[i][j] = 0
            elif G[i][j] / K <= 1:
                Q[i][j] = 1
            elif G[i][j] / K <= 4:
                Q[i][j] = 4
            elif G[i][j] / K <= 6:
                Q[i][j] = 6
            else:
                Q[i][j] = 1000
    print("Q =", Q)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and multiple Depots with no Return to Depot
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
        model += lpSum(x[(k, j, k)] for j in I if j != k) == 1

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
            # model += (lpSum(x[(i, j, k)] for i in I if i != j) >= lpSum(x[(j, h, k)] for h in I if h != j),
            #           f"Flusskonservierung_Fahrzeug_{k}_Knoten_{j}")  # setzt x[(i, i, k)] = None

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
    # Von Depots zu den Abholorten - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die die Depots verlassen muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte und mehrere Depots
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
    model.solve(solver)

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

########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_mit_H_depots_total_distance_no_return_to_depot_order():

    print(listSolvers())
    print(listSolvers(onlyAvailable=True))

    """
    This is a cellular VRP with Pickup and Delivery with multiple depots for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs stay at their last delivery point.
    :return:
    """

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    H = []  # Anzahl der Depots, wo die einzelnen FTF stehen - jedes FTF hat ein Depot
    I = []  # Orte/Knoten, die besucht werden (inkl. Depots, Abhol- und Lieferpunkten), wird aus der Distanzmatrix berechnet
    J = []  # Orte/Knoten der Jobs (inkl. Abhol- und Lieferpunkten)
    A = 6  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

    for i in range(A):
        H.append(i)

    # Distanzmatrix - Distanzen
    '''D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 80.0, 50.0, 100.0],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 21.0, 81.0, 51.0, 99.0],
         [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 22.0, 82.0, 52.0, 98.0],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 23.0, 83.0, 53.0, 97.0],
         [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 24.0, 84.0, 54.0, 96.0],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 25.0, 85.0, 55.0, 95.0],
         [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 0.0, 60.0, 30.0, 80.0],
         [80.0, 81.0, 82.0, 83.0, 84.0, 85.0, 60.0, 0.0, 30.0, 80.0],
         [50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 30.0, 30.0, 0.0, 50.0],
         [100.0, 99.0, 98.0, 97.0, 96.0, 95.0, 80.0, 80.0, 50.0, 0.0]]'''

    D = [[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 20.0, 58.309518948453004, 50.0, 70.71067811865476],
         [1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 20.024984394500787, 58.83026432033091, 50.00999900019995, 70.00714249274856],
         [2.0, 1.0, 0.0, 1.0, 2.0, 3.0, 20.09975124224178, 59.36328831862332, 50.039984012787215, 69.31089380465383],
         [3.0, 2.0, 1.0, 0.0, 1.0, 2.0, 20.223748416156685, 59.90826320300064, 50.08991914547278, 68.62215385719105],
         [4.0, 3.0, 2.0, 1.0, 0.0, 1.0, 20.396078054371138, 60.4648658313239, 50.15974481593781, 67.94115100585212],
         [5.0, 4.0, 3.0, 2.0, 1.0, 0.0, 20.615528128088304, 61.032778078668514, 50.24937810560445, 67.26812023536856],
         [20.0, 20.024984394500787, 20.09975124224178, 20.223748416156685, 20.396078054371138, 20.615528128088304, 0.0,
          42.42640687119285, 30.0, 58.309518948453004],
         [58.309518948453004, 58.83026432033091, 59.36328831862332, 59.90826320300064, 60.4648658313239,
          61.032778078668514, 42.42640687119285, 0.0, 30.0, 80.0],
         [50.0, 50.00999900019995, 50.039984012787215, 50.08991914547278, 50.15974481593781, 50.24937810560445, 30.0,
          30.0, 0.0, 50.0],
         [70.71067811865476, 70.00714249274856, 69.31089380465383, 68.62215385719105, 67.94115100585212,
          67.26812023536856, 58.309518948453004, 80.0, 50.0, 0.0]]

    for i in range(len(D)):
        I.append(i)
    num_locations = len(D)

    J = list(set(I).difference(H))
    num_job_locations = len(H)
    print(f"H = {H}")
    print(f"I = {I}")
    print(f"J = {J}")
    print(f"D = {D}")

    # Gewichtsmatrix
    G = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 0
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 1
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 2
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 3
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 4
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 5
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1000, 1000],  # 6 zu 8, 9
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 7
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],  # 8
         [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]  # 9

    print("G =", G)

    # Konfigurationsmatrix
    Q_np = np.zeros(shape=(num_locations, num_locations))
    Q = Q_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                Q[i][j] = 0
            elif G[i][j] / K <= 1:
                Q[i][j] = 1
            elif G[i][j] / K <= 4:
                Q[i][j] = 4
            elif G[i][j] / K <= 6:
                Q[i][j] = 6
            else:
                Q[i][j] = 1000
    print("Q =", Q)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################

    ###################
    # Initialisierung #
    ###################

    # cellular VRP with Pickups and Delivery and a single Depot
    model = LpProblem("cVRPPDsD", LpMinimize)

    ##########################
    # Entscheidungsvariablen #
    ##########################

    # x_(i, j, k) ist eine Binärvariable, die 1 ist, wenn das Transportfahrzeug k von Ort i direkt zu Ort j fährt; sonst 0.
    x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in range(A)], 0, 1, LpBinary)

    s = LpVariable.dicts("s", [(i, j, k) for i in I for j in I for k in range(A)], 0, None, LpInteger)

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
        model += lpSum(x[(k, j, k)] for j in I if j != k) == 1

    # In jedem Depot steht am Anfang genau ein Fahrzeug.
    for i in H:
        model += lpSum(x[(i, j, k)] for j in I if i != j for k in range(A)) <= 1


    ########################################################################################################
    # Flusskonservierung - Fluss von Fahrzeugen in den Knoten entspricht Fluss von Fahrzeugen aus dem Knoten
    for j in J:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I if i != j) >= lpSum(x[(j, h, k)] for h in I if h != j),
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
    # Von Depots zu den Abholorten - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die die Depots verlassen muss passen.
    # Diese Nebenbedingung gilt für mehrere Abholorte und mehrere Depots
    model += lpSum(x[(i, j, k)] for i in H for j in J for k in range(A)) >= max(Q[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(Q[i][j] for i in I for j in I)}")

    ####################
    # Reihenfolge bilden
    # Initiierung der Schrittfolge für das Verlassen der Depots mit s[(i, j, k)] = 1
    for i in H:
        for j in I:
            for k in range(A):
                model += s[(i, j, k)] == x[(i, j, k)]

    # Reihenfolgebedingung hinzufügen
    # Bedingung funktioniert nicht
    M = 50
    for k in range(A):
        for i in I:
            for j in I:
                model += s[(i, j, k)] <= M*x[(i, j, k)]
                for h in I:
                    model += s[(j, h, k)] >= s[(i, j, k)] + x[(i, j, k)] - M*(1 - x[(j, h, k)])

    # Problem lösen
    solver = CPLEX_CMD()
    model.solve()

    result = {
        'status': LpStatus[model.status],
        'objective': value(model.objective),
        'variables': {v.name: v.varValue for v in model.variables()}
    }

    result_variables = {v.name: v.varValue for v in model.variables()}

    print(result_variables)
    print(result_variables['x_(0,_6,_0)'])


    # Ergebnisse ausgeben
    for v in model.variables():
        if v.varValue > 0:
            print(v.name, "=", v.varValue)

    for k in range(A):
        for i in I:
            for j in I:
                if value(x[(i, j, k)]) == 1:
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x(i, j, k) = {value(x[(i, j, k)])}.")

    print("###")

    for i in I:
        for j in I:
            for k in range(A):
                if value(x[(i, j, k)]) == 1:
                    print(f"Fahrzeug {k} fährt von {i} nach {j} mit x(i, j, k) = {value(x[(i, j, k)])}.")

    print("Gesamte zurückgelegte Distanz =", value(model.objective))
    print("Status:", LpStatus[model.status])
    print(result_variables)
    print(result_variables['x_(0,_6,_0)'])

    return result_variables


def reconstruct_path(x_decision_vars, A, start_points):
    paths = {k: [] for k in range(A)}  # Initialisiere Pfade für jedes Fahrzeug

    for k in range(A):
        current_point = start_points[k]  # Startpunkt des Fahrzeugs
        paths[k].append(current_point)



        # Folge der Route des Fahrzeugs, bis kein nächster Punkt gefunden wird
        while True:
            next_point = None
            for (i, j, k_val), val in x_decision_vars.items():
                if i == current_point and k_val == k and val == 1.0:
                    next_point = j
                    paths[k].append(next_point)
                    break
            if next_point is None:  # Kein weiterer Punkt zu besuchen
                break
            else:
                current_point = next_point

    return paths


# Beispiel: x_decision_vars ist ein Dictionary Ihrer x[i, j, k] Werte, start_points sind die Startpunkte der Fahrzeuge
# paths = reconstruct_path(x_decision_vars, A, start_points)
# print(paths)


print('or_test_final')
# or_test_mit_1_depot_total_distance()
# or_test_mit_H_depots_total_distance()
or_test_mit_1_depot_total_distance_no_return_to_depot()
# or_test_mit_H_depots_total_distance_no_return_to_depot()
# or_test_mit_H_depots_total_distance_no_return_to_depot_order()

'''with open('result_1.json', 'r') as file:
    result_decision_variables_1 = json.load(file)
print(result_decision_variables_1)

with open('result_2.json', 'r') as file:
    result_decision_variables_2 = json.load(file)
print(result_decision_variables_2)
print(result_decision_variables_2['x(0,0,0)'])'''

print('###############################################################################################################')
