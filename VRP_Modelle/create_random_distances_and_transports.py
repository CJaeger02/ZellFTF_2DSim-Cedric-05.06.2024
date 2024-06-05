import numpy as np
import json
from datetime import datetime


def create_symmetric_distance_matrix(size):
    """
    Create a symmetric matrix of a given size with diagonal elements as 0 and off-diagonal elements as random integers.

    Parameters:
    size (int): The size of the matrix.

    Returns:
    np.array: A symmetric matrix.
    """
    # Create an empty matrix of the given size
    matrix = np.zeros((size, size), dtype=int)

    # Populate the matrix with random integers for the upper triangle
    upper_triangle = np.tril(np.random.randint(1, 11, (size, size)), -1)

    # Make the matrix symmetric
    matrix = upper_triangle + upper_triangle.T

    with open(f"random_distances_and_transport_configurations/{datetime.now().strftime('%Y%m%d-%H%M%S')}_"
              f"random_distance_matrix.json", "w") as outfile:
        json.dump(matrix.tolist(), outfile)

    return matrix


def create_symmetric_distance_matrix_with_ordered_entries(m, n):
    """
    Create a symmetric m x m matrix with the first n entries in each row and column
    increasing by 1 starting from 0, and the rest of the entries being random integers between 1 and 200.
    The diagonal entries will be 0.

    Parameters:
    m (int): The size of the matrix.
    n (int): The number of ordered entries in each row and column.

    Returns:
    numpy.ndarray: The symmetric matrix with specified entries.
    """
    if n > m:
        raise ValueError("n must be less or equal to m.")

    # Initialize the matrix with random integers between 1 and 200
    matrix = np.random.randint(1, 201, size=(m, m))

    # Make the matrix symmetric
    matrix = (matrix + matrix.T) // 2

    # Set diagonal to 0
    np.fill_diagonal(matrix, 0)

    # Update the first n entries in each row and column
    for i in range(n):
        for j in range(min(i, n)):
            matrix[i, j] = i - j
            matrix[j, i] = i - j  # Ensure symmetry

    with open(f"random_distances_and_transport_configurations/{datetime.now().strftime('%Y%m%d-%H%M%S')}_"
              f"random_distance_matrix.json", "w") as outfile:
        json.dump(matrix.tolist(), outfile)

    return matrix


def create_random_configuration_transport_matrix_with_zeros(size, n, num_entries):
    """
    Create a 2D matrix of a given size with zeros on the diagonal and first row.
    A specified number of entries are randomly distributed within the matrix with values 1, 4, or 6.

    Parameters:
    size (int): The size of the matrix.
    num_entries (int): The number of entries to be randomly distributed in the matrix.

    Returns:
    np.array: A 2D matrix with the specified conditions.
    """
    # Initialize the matrix with zeros
    matrix = np.zeros((size, size), dtype=float)

    # Exclude the first row and the diagonal from the random distribution
    valid_indices = [(i, j) for i in range(size) for j in range(size) if i >= n and j >= n and i != j]

    # Randomly select positions for the non-zero entries
    selected_positions = np.random.choice(len(valid_indices), min(num_entries, len(valid_indices)), replace=False)

    # Values to be randomly assigned
    possible_values = [1, 4, 6]

    # Assign random values to the selected positions
    for pos in selected_positions:
        i, j = valid_indices[pos]
        matrix[i, j] = np.random.choice(possible_values)

    # Ensure the diagonal is zeros
    np.fill_diagonal(matrix, 0)

    with open(f"random_distances_and_transport_configurations/{datetime.now().strftime('%Y%m%d-%H%M%S')}_"
              f"random_configuration_transport_matrix.json", "w") as outfile:
        json.dump(matrix.tolist(), outfile)

    return matrix


# Example
matrix_size = 20  # Size of the matrix
num_agvs = 12
num_transports = 25  # Number of non-zero entries to be randomly distributed

# Example
distance_matrix = create_symmetric_distance_matrix_with_ordered_entries(matrix_size, num_agvs)
print(distance_matrix)
print(distance_matrix.tolist())

transport_configuration_matrix = (
    create_random_configuration_transport_matrix_with_zeros(matrix_size, num_agvs, num_transports))
print(transport_configuration_matrix)
print(transport_configuration_matrix.tolist())
