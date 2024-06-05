from pulp import LpProblem, LpVariable, lpSum, LpMinimize, LpBinary, LpMaximize

# Gegebene Daten
N = 5  # Anzahl der Orte
A = 4  # Anzahl der FTF
K = 1  # Kapazität der FTF
D = [[0, 2, 8, 5, 8],
     [2, 0, 6, 3, 6],
     [8, 6, 0, 3, 6],
     [5, 3, 3, 0, 3],
     [8, 6, 6, 3, 0]]  # Distanzmatrix

W = [[0, 0, 0, 0, 0],
     [0, 1, 4, 2, 0],
     [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]]  # Gewichtsmatrix

# Initialisierung des LP-Problems
prob = LpProblem("VehicleRoutingProblem", LpMinimize)

# Variablen
x = LpVariable.dicts("Route", [(i, j, k) for i in range(1, A + 1) for j in range(1, N + 1) for k in range(1, N + 1)], 0, 1, LpBinary)
y = LpVariable.dicts("FTF_on_route", [(i, j) for i in range(1, A + 1) for j in range(1, N + 1)], 0, None)

# Zielfunktion
prob += lpSum(D[j-1][k-1] * x[(i, j, k)] for i in range(1, A + 1) for j in range(1, N + 1) for k in range(1, N + 1))

# Einschränkungen
# Jeder Ort wird genau einmal beliefert
for j in range(1, N+1):
    prob += lpSum(x[(i, j, k)] for i in range(1, A + 1) for k in range(1, N + 1)) == 1

# Summe der Gewichte darf Kapazität nicht überschreiten
for i in range(1, A + 1):
    for j in range(1, N+1):
        prob += lpSum(W[j-1][k-1] * x[(i, j, k)] for k in range(1, N+1)) <= K * y[(i, j)]

# Anzahl der gekoppelten FTF
for j in range(1, N+1):
    for k in range(1, N+1):
        prob += lpSum(x[(i, j, k)] for i in range(1, A + 1)) == 1

# Summe der gekoppelten FTF darf maximal 6 sein
for j in range(1, N+1):
    for k in range(1, N+1):
        prob += lpSum(x[(i, j, k)] for i in range(1, A + 1)) <= 6

# Flusskonsistenz
for i in range(1, A + 1):
    for j in range(1, N+1):
        for k in range(1, N+1):
            prob += y[(i, j)] - y[(i, k)] + 1 <= A * (1 - x[(i, j, k)])

# Optimierung des LP-Problems
prob.solve()

# Ausgabe der Ergebnisse
print("Status:", prob.status)
print("Optimale Lösung (minimal zurückgelegte Distanz):", prob.objective.value())

for v in prob.variables():
    print(v.name, "=", v.varValue)



'''from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary

# Parameterdefinition
I = [0, 1, 2, 3, 4]  # Orte inklusive Depot (0)
K = 1  # Kapazität eines FTF
A = 6  # Anzahl der FTFs
G = {0: 0, 1: 6, 2: 4, 3: 1, 4: 0}  # Gewicht der Produkte an den Orten

# Distanzmatrix (symmetrisch)
C_ij = {
    (0, 0): 0, (0, 1): 2, (0, 2): 8, (0, 3): 5, (0, 4): 8,
    (1, 0): 2, (1, 1): 0, (1, 2): 6, (1, 3): 3, (1, 4): 6,
    (2, 0): 8, (2, 1): 6, (2, 2): 0, (2, 3): 3, (2, 4): 6,
    (3, 0): 5, (3, 1): 3, (3, 2): 3, (3, 3): 0, (3, 4): 3,
    (4, 0): 8, (4, 1): 6, (4, 2): 6, (4, 3): 3, (4, 4): 0
}

# Entscheidungsvariablen
x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in [1, 4, 6]], cat=LpBinary)
y = LpVariable.dicts("y", [(i, k) for i in I for k in [1, 4, 6]], cat=LpBinary)

# Problemdefinition
model = LpProblem("VRP", LpMinimize)

# Zielfunktion
model += lpSum([x[i, j, k] * C_ij[i, j] for i in I for j in I for k in [1, 4, 6]])

# Nebenbedingungen
# Jeder Ort wird genau einmal beliefert und abgeholt
for i in I:
    model += lpSum([x[i, j, k] for j in I for k in [1, 4, 6]]) == (i != 0)  # Depot (0) ist ausgenommen
    model += lpSum([x[j, i, k] for j in I for k in [1, 4, 6]]) == (i != 0)  # Depot (0) ist ausgenommen

# Kapazitätsbeschränkungen
for i in I:
    for k in [1, 4, 6]:
        if k * K >= G[i]:
            model += y[i, k] >= 1
        else:
            model += y[i, k] == 0

# Fahrzeuge starten und enden im Depot
for k in [1, 4, 6]:
    model += lpSum([x[0, j, k] for j in I]) == A / k
    model += lpSum([x[i, 0, k] for i in I]) == A / k

# Sicherstellen, dass die Anzahl der gekoppelten FTFs korrekt ist
for k in [4, 6]:
    model += lpSum([y[i, k] for i in I]) <= A / k

# Verknüpfung der Routen mit den Koppelungen
for i in I:
    for j in I:
        for k in [1, 4, 6]:
            model += x[i, j, k] <= y[i, k]
            model += x[i, j, k] <= y[j, k]

# Das Modell lösen (Annahme: Es gibt einen installierten und verfügbaren Solver)
model.solve()

# Ausgabe der Lösung
for v in model.variables():
    if v.varValue > 0:
        print(v.name, "=", v.varValue)
'''

import pulp
from pulp import *  # LpProblem, LpMinimize, LpVariable, lpSum, LpBinary
import math
import numpy as np

##############################
###                        ###
### PYTHON 3.8 verwenden!!!###
###                        ###
##############################


def or_test_mit_1_depot():

    print(listSolvers(onlyAvailable=True))
    print(listSolvers())

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

    # Gewichtsmatrix
    G = [
        [0, 0, 0, 0, 0],  # Keine Güter werden vom Depot aus transportiert
        [0, 0, 80, 500, 1200],  # Güter von Ort 1 zu Ort 2
        [0, 0, 0, 0, 1200],  # Güter von Ort 2 zu Ort 4
        [0, 0, 0, 0, 1200],  # Angenommen, von Ort 3 wird nichts transportiert
        [0, 0, 0, 0, 0]  # Angenommen, von Ort 4 wird nichts transportiert
    ]
    print("G =", G)

    # Konfigurationsmatrix
    C_np = np.zeros(shape=(num_locations, num_locations))
    C = C_np.tolist()

    for i in I:
        for j in I:
            if G[i][j] == 0:
                C[i][j] = 0
            elif G[i][j]/K <= 1:
                C[i][j] = 1
            elif G[i][j]/K <= 4:
                C[i][j] = 4
            elif G[i][j]/K <= 6:
                C[i][j] = 6
            else:
                C[i][j] = 1000
    print("C =", C)

    # Jobs
    J = []
    for i in I:
        for j in I:
            if G[i][j] != 0:
                J.append(G[i][j])
    print("J =", J)

    ##################################
    ###  Formulierung des Modells  ###
    ##################################


    ###################
    # Initialisierung #
    ###################

    model = LpProblem("cVRPPD", LpMinimize)


    ##########################
    # Entscheidungsvariablen #
    ##########################

    # x_(i, j, k) ist eine Binärvariable, die 1 ist, wenn das Transportfahrzeug k von Ort i direkt zu Ort j fährt; sonst 0.
    x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in range(A)], 0, 1, LpBinary)

    '''# y_(i, j) ist ein Integer und gibt an, wie viele FTF für den Transport eines Produkts von Ort i zu Ort j benötigt werden
    y = LpVariable.dicts("y", [(i, j) for i in I for j in I], cat='Integer')'''

    # z_(k_U) ist eine Binärvariable, die 1 ist, wenn das Set U
    # z = LpVariable.dicts("z", [(k, U) for k in range(A) for U in J], 0, 1, LpBinary)


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
    '''for j in range(1, num_locations):
        for k in range(A):
            model += lpSum(x[(i, j, k)] for i in range(num_locations) if i != j) - lpSum(
                x[(j, h, k)] for h in range(num_locations) if h != j) == 0'''
    '''for k in range(A):
        for i in I[1:]:
            model += lpSum(x[(i, j, k)] for j in I) - lpSum(x[(j, i, k)] for j in I) == 0'''
    for j in I[1:]:
        for k in range(A):
            model += (lpSum(x[(i, j, k)] for i in I if i != j) == lpSum(x[(j, h, k)] for h in I if h != j),
                      f"Flusskonservierung_Fahrzeug_{k}_Knoten_{j}")

    #####################################################################
    # Jeder Lieferung müssen die richtige Anzahl an AGV zugeordnet werden
    for i in I:
        for j in I:
            if i != j:
                num_vehicles = C[i][j]
                if num_vehicles > 0:
                    print("i =", i, "j =", j, "Benötigte Fahrzeuge =", num_vehicles)
                    model += lpSum(x[(i, j, k)] for k in range(A)) == num_vehicles

    # Vom Depot zum Abholort - Die Anzahl der AGV muss passen!
    # Die Anzahl an AGVs, die das Depot verlassen muss passen.
    # Diese Nebenbedingung ist so möglich für einen einzigen Abholort:
    '''for i in I:
        for j in I:
            if i != j:
                num_vehicles = C[i][j]
                if num_vehicles > 0:
                    model += lpSum(x[(0, i, k)] for k in range(A)) >= num_vehicles'''

    # Diese Nebenbedingung gilt für mehrere Abholorte
    model += lpSum(x[(0, i, k)] for i in I[1:] for k in range(A)) >= max(C[i][j] for i in I for j in I)
    print(f"Max Fahrzeuge: {max(C[i][j] for i in I for j in I)}")

    # Es müssen von den Lieferorten genug Fahrzeuge zum Abholort zurückfahren:
    '''for i in I:
        for j in I:
            if i != j:
                print("i =", i, "j =", j, "C[",i,"][",j,"] =", C[i][j])
                model += lpSum(x[(i, j, k)] for k in range(A) if C[i][j]>0) - lpSum(x[(j, i, k)] for k in range(A) if C[i][j]>0) >= 11 - A'''


    # Zu einem Abholort müssen genug Fahrzeuge hinfahren
    '''for i in I[1:]:
        for j in I[1:]:
            print(i, j)'''

    # Anzahl der Fahrzeuge berücksichtigen
    # Die Anzahl der Fahrzeuge, die vom Ort i zu Ort j fahren, darf die maximale Anzahl an Fahrzeugen nicht überschreiten.
    for i in I:
        for j in I:
            model += lpSum(x[(i, j, k)] for k in range(A)) <= A

    # Wenn zu wenige Fahrzeuge, dann Jobs nacheinander, sonst parallel
    '''# Each vehicle can do at most one delivery
    for k in range(A):
        model += lpSum(x[(i, j, k)] for i in I for j in I if i != j) <= 1, f"One_delivery_per_vehicle_{k}"'''

    # jede Lieferung muss genau einmal durchgeführt werden
    '''for i in I:
        for j in I:
            if i != j:
                model += pulp.lpSum(y[i, j])'''

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

def or_test_1():

    # Parameter definition
    n = 5  # Number of locations including depot
    A = 6  # Number of vehicles
    K = 50  # Capacity of each vehicle

    # Distance matrix (symmetric)
    D = [
        [0, 2, 8, 5, 8],
        [2, 0, 6, 3, 6],
        [8, 6, 0, 3, 6],
        [5, 3, 3, 0, 3],
        [8, 6, 6, 3, 0]
    ]

    # Weight matrix from problem description
    W = [
        [0, 0, 0, 0, 0],  # Depot does not have pickup or delivery
        [0, 0, 300, 200, 50],  # Deliveries from location 1 to 2, 3, and 4
        [0, 0, 0, 0, 0],  # No deliveries from location 2
        [0, 0, 0, 0, 0],  # No deliveries from location 3
        [0, 0, 0, 0, 0]  # No deliveries from location 4
    ]

    # Initialize the problem
    prob = LpProblem("VRP_Pickup_and_Delivery", LpMinimize)

    # Decision variables
    x = LpVariable.dicts("x", [(i, j, k) for i in range(n) for j in range(n) if i != j for k in range(A)], cat='Binary')
    y = LpVariable.dicts("y", [(i, j) for i in range(n) for j in range(n) if i != j], cat='Integer', lowBound=0)

    # Objective function
    prob += lpSum(
        D[i][j] * x[(i, j, k)] for i in range(n) for j in range(n) if i != j for k in range(A)), "Total_Distance"

    # Constraints
    for k in range(A):
        prob += lpSum(x[(0, j, k)] for j in range(1, n)) == 1, f"Start_from_depot_vehicle_{k}"
        prob += lpSum(x[(i, 0, k)] for i in range(1, n)) == 1, f"Return_to_depot_vehicle_{k}"

    for j in range(1, n):
        for k in range(A):
            prob += lpSum(x[(i, j, k)] for i in range(n) if i != j) - lpSum(
                x[(j, h, k)] for h in range(n) if h != j) == 0, f"Flow_conservation_{j}_{k}"

    for i in range(n):
        for j in range(n):
            if i != j:
                # Ceiling division of the weight by the vehicle capacity to get the number of vehicles required
                required_vehicles = (W[i][j] + K - 1) // K
                # Ensure y_ij represents the required number of vehicles if the weight is greater than the vehicle capacity
                prob += y[(i, j)] >= required_vehicles, f"Min_vehicles_for_weight_{i}_{j}"

    # Constraint to ensure that the number of vehicles used does not exceed the available number
    prob += lpSum(y[(i, j)] for i in range(n) for j in range(n) if i != j) <= A, "Total_number_of_vehicles"

    # Each vehicle can do at most one delivery
    for k in range(A):
        prob += lpSum(x[(i, j, k)] for i in range(n) for j in range(n) if i != j) <= 1, f"One_delivery_per_vehicle_{k}"

    # The configuration of vehicles must meet the transport requirements
    for i in range(n):
        for j in range(n):
            if i != j:
                for k in range(A):
                    prob += x[(i, j, k)] <= y[(i, j)], f"Vehicle_configuration_{i}_{j}_{k}"

    # Solve the problem
    prob.solve()

    # Output the results
    result = {
        'status': LpStatus[prob.status],
        'objective': value(prob.objective),
        'variables': {v.name: v.varValue for v in prob.variables() if v.varValue != 0}
    }

    result


########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_2():
    # Parameter
    I = [0, 1, 2, 3, 4]  # Orte inklusive Depot (Ort 0)
    N = len(I)
    c = [1, 4, 6]  # Mögliche Konfigurationen der FTF
    A = 6  # Anzahl der vorhandenen Fahrzeuge
    K = 1  # Kapazität eines FTF

    # Gegebene Datenstrukturen (Beispielwerte, sollten durch Ihre Daten ersetzt werden)
    # Distanzmatrix
    D = [
        [0, 2, 8, 5, 8],
        [2, 0, 6, 3, 6],
        [8, 6, 0, 3, 6],
        [5, 3, 3, 0, 3],
        [8, 6, 6, 3, 0]
    ]

    # Gewichtsmatrix
    G = [
        [0, 0, 0, 0, 0],  # Keine Güter werden vom Depot aus transportiert
        [0, 0, 3, 1, 6],  # Güter von Ort 1 zu Ort 2, 3, und 4
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 2 wird nichts transportiert
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 3 wird nichts transportiert
        [0, 0, 0, 0, 0]  # Angenommen, von Ort 4 wird nichts transportiert
    ]

    # Problem
    prob = LpProblem("Vehicle_Routing_Problem", LpMinimize)

    # Entscheidungsvariablen
    # x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in [1, 4, 6]], cat='Binary')
    x = LpVariable.dicts("x", [(i, j, k) for i in I for j in I for k in c], cat=LpBinary)
    y = LpVariable.dicts("y", [(i, j) for i in I for j in I if i != j], cat='Integer')

    # Zielfunktion
    prob += lpSum(D[i][j] * x[i, j, k] for i in I for j in I for k in c)

    # Nebenbedingungen

    '''# Jeder Ort außer das Depot wird einmal beliefert.
    for j in I[1:]:  # Orte ohne das Depot
        prob += lpSum(x[i, j, k] for i in I for k in range(A)) == 1'''

    # Die FTF starten und enden im Depot
    prob += lpSum(x[0, j, k] for j in I for k in c) == 1
    prob += lpSum(x[i, 0, k] for i in I for k in c) == 1

    for i in I:
        for j in I:
            if i != j:
                # Kapazitätsbeschränkung
                prob += y[i, j] >= math.ceil(G[i][j] / K)
                # Transportkonfigurationen
                prob += y[i, j] * K >= G[i][j]
                # Beschränkung auf Transportkonfigurationen
                prob += y[i, j] <= A

    for k in c:
        for i in I:
            prob += lpSum(x[i, j, k] for j in I) - lpSum(x[j, i, k] for j in I) == 0

    # Löse das Problem
    prob.solve()

    # Ergebnisse ausgeben
    for v in prob.variables():
        if v.varValue > 0:
            print(v.name, "=", v.varValue)

    print("Gesamte zurückgelegte Distanz =", value(prob.objective))

########################################################################################################################
########################################################################################################################
########################################################################################################################

def or_test_3():
    # Parameter
    I = 5  # Anzahl der Orte
    D = [
        [0, 2, 8, 5, 8],
        [2, 0, 6, 3, 6],
        [8, 6, 0, 3, 6],
        [5, 3, 3, 0, 3],
        [8, 6, 6, 3, 0]
    ]

    # Gewichtsmatrix
    G = [
        [0, 0, 0, 0, 0],  # Keine Güter werden vom Depot aus transportiert
        [0, 0, 3, 1, 6],  # Güter von Ort 1 zu Ort 2, 3, und 4
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 2 wird nichts transportiert
        [0, 0, 0, 0, 0],  # Angenommen, von Ort 3 wird nichts transportiert
        [0, 0, 0, 0, 0]  # Angenommen, von Ort 4 wird nichts transportiert
    ]
    K = 10  # Kapazität eines Transportfahrzeugs
    A = 1  # Anzahl der Transportfahrzeuge
    c = [1, 4, 6]  # Konfiguration der Transportfahrzeug-Teams

    # Entscheidungsvariablen
    x = LpVariable.dicts("x", [(i, j, k) for i in range(I) for j in range(I) for k in range(A)], 0, 1, LpBinary)
    y = LpVariable.dicts("y", [(i, j) for i in range(I) for j in range(I)], cat='Integer')

    # Initialisiere das Problem
    prob = LpProblem("VRP_with_PUD", LpMinimize)

    # Zielfunktion
    prob += lpSum(D[i][j] * x[(i, j, k)] for i in range(I) for j in range(I) for k in range(A))

    # Nebenbedingungen

    # 1. Jedes Produkt wird genau einmal geliefert
    for i in range(I):
        for j in range(I):
            if G[i][j] > 0:
                prob += lpSum(x[(i, j, k)] for k in range(A)) == 1

    # Hilfsfunktion für Kapazitätsbeschränkungen
    def get_y(G_ij, KK):
        if G_ij <= KK:
            return 1
        elif KK < G_ij <= 4 * KK:
            return 4
        elif 4 * KK < G_ij <= 6 * KK:
            return 6
        else:
            raise ValueError("Das Gewicht liegt außerhalb der erlaubten Konfigurationen")

    # 2. Kapazitätsbeschränkungen
    for i in range(I):
        for j in range(I):
            if G[i][j] > 0:  # Stelle sicher, dass nur gültige Routen betrachtet werden
                y_value = get_y(G[i][j], K)
                prob += y[(i, j)] == y_value
                prob += G[i][j] <= y[(i, j)] * K

    # 3. Fahrzeuge starten und enden im Depot
    for k in range(A):
        prob += lpSum(x[(0, j, k)] for j in range(1, I)) == 1
        prob += lpSum(x[(j, 0, k)] for j in range(1, I)) == 1

    # 4. Einhaltung der Fahrzeugkonfigurationen
    for i in range(I):
        for j in range(I):
            # Erlaube y[(i, j)] nur, Werte aus der Konfigurationsliste c zu nehmen
            if G[i][j] > 0:
                # Füge Nebenbedingungen hinzu, die y[(i, j)] auf Werte aus c beschränken
                prob += y[(i, j)] >= min(c)
                prob += y[(i, j)] <= max(c)
                # Hier wird für jeden Wert in c eine Bedingung erstellt,
                # die sicherstellt, dass y[(i, j)] diesem Wert entspricht,
                # falls keine der anderen Bedingungen wahr ist.
                prob += lpSum([y[(i, j)] == value for value in c]) >= 1

    # 5. Kein Überschneiden von Fahrten
    for k in range(A):
        for i in range(I):
            prob += lpSum(x[(i, j, k)] for j in range(I) if j != i) <= 1
            prob += lpSum(x[(j, i, k)] for j in range(I) if j != i) <= 1

    # 6. Einhaltung der Anzahl der Fahrzeuge
    for k in range(A):
        prob += lpSum(x[(i, j, k)] for i in range(I) for j in range(I) if j != i) <= 1

    # 7. Konnektivität sicherstellen (jedes Fahrzeug bildet eine Tour)
    # Hier müssen Sie möglicherweise zusätzliche Nebenbedingungen hinzufügen, um sicherzustellen, dass jeder Weg eine geschlossene Schleife bildet

    # Das Problem lösen
    prob.solve()

    # Status und Lösung ausgeben
    print("Status:", LpStatus[prob.status])
    for v in prob.variables():
        print(v.name, "=", v.varValue)

def plot_transport():
    pass


#print('or_test_1')
#or_test_1()
#print('###############################################################################################################')
#print('or_test_2')
#or_test_2()
#print('###############################################################################################################')
#print('or_test_3')
#or_test_3()
#print('###############################################################################################################')
print('or_test_final')
or_test_mit_1_depot()
print('###############################################################################################################')

