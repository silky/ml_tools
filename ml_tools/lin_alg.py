import autograd.numpy as np
import scipy.sparse.linalg as spl
from scipy.linalg import cho_solve, cho_factor, solve_triangular


def cholesky_inverse(matrix):

    return cho_solve(cho_factor(matrix, lower=True), np.eye(matrix.shape[0]))


def compute_sparse_inverse(sparse_matrix):

    lu = spl.splu(sparse_matrix)
    inverse = lu.solve(np.eye(sparse_matrix.shape[0]))

    return inverse


def pos_def_mat_from_vector(vec, target_size, jitter=0):

    L = np.zeros((target_size, target_size))
    L[np.tril_indices(target_size)] = vec

    return np.matmul(L, L.T) + np.eye(target_size) * jitter


def vector_from_pos_def_mat(pos_def_mat, jitter=0):

    # Subtract jitter
    pos_def_mat -= np.eye(pos_def_mat.shape[0]) * jitter
    L = np.linalg.cholesky(pos_def_mat)
    elts = np.tril_indices_from(L)

    return L[elts]


def num_triangular_elts(mat_size, include_diagonal=True):

    if include_diagonal:
        return int(mat_size * (mat_size + 1) / 2)
    else:
        return int(mat_size * (mat_size - 1) / 2)


def solve_via_cholesky(k_chol, y):
    """Solves a positive definite linear system via a Cholesky decomposition.

    Args:
        k_chol: The Cholesky factor of the matrix to solve. A lower triangular
            matrix, perhaps more commonly known as L.
        y: The vector to solve.
    """

    # Solve Ls = y
    s = solve_triangular(k_chol, y, lower=True)

    # Solve Lt b = s
    b = solve_triangular(k_chol.T, s)

    return b


def generate_random_pos_def(n, jitter=10**-4):

    elements = np.random.randn(n, n)
    cov = elements @ elements.T + np.eye(n) * jitter

    return cov
