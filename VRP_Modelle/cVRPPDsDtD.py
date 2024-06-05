from pulp import *  # LpProblem, LpMinimize, LpVariable, lpSum, LpBinary
import numpy as np


##############################
###                        ###
### PYTHON 3.8 verwenden!!!###
###                        ###
##############################


def cVRPPDsDtD(D=None, Q=None, A=None):
    '''
    This is a cellular VRP with Pickup and Delivery with a single depot for the AGV.
    Goal is to reduce the total distances of all agvs.
    After the task, the AGVs drive back to the depot.
    :return:
    '''

    ###################################
    ###  Eingabegrößen des Modells  ###
    ###################################

    if D is None:
        D = [
            [0, 2, 8, 5, 10],
            [2, 0, 6, 3, 8],
            [8, 6, 0, 3, 8],
            [5, 3, 3, 0, 5],
            [10, 8, 8, 5, 0]
        ]
    I = []  # Orte/Knoten, die besucht werden, wird aus der Distanzmatrix berechnet
    if A is None:
        A = 6  # Anzahl der zur Verfügung stehenden Fahrzeuge
    K = 200  # Kapazität eines einzelnen FTF

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
    if Q is None:
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
    model = LpProblem("cVRPPDsDtD", LpMinimize)

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


cVRPPDsDtD()