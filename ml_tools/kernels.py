import numpy as np


def rbf_kernel_1d(x1, x2, alpha, rho):

    differences = np.subtract.outer(x1, x2)
    sq_diff = differences**2

    return alpha**2 * np.exp(-sq_diff / (2 * rho**2))


def ard_rbf_kernel(x1, x2, lengthscales, alpha, jitter=1e-5):

    # x1 is N1 x D
    # x2 is N2 x D (and N1 can be equal to N2)

    # Must have same number of dimensions
    assert(x1.shape[1] == x2.shape[1])

    # Also must match lengthscales
    assert(lengthscales.shape[0] == x1.shape[1])

    # Use broadcasting
    # X1 will be (N1, 1, D)
    x1_expanded = np.expand_dims(x1, axis=1)
    # X2 will be (1, N2, D)
    x2_expanded = np.expand_dims(x2, axis=0)

    # These will be N1 x N2 x D
    sq_differences = (x1_expanded - x2_expanded)**2
    inv_sq_lengthscales = 1. / lengthscales**2

    # Use broadcasting to do a dot product
    exponent = np.sum(sq_differences * inv_sq_lengthscales, axis=2)
    exponentiated = np.exp(-0.5 * exponent)

    kern = alpha**2 * exponentiated
    kern[np.diag_indices_from(kern)] = np.diag(kern) + jitter

    # Find gradients
    # Gradient with respect to alpha:
    alpha_grad = 2 * alpha * exponentiated

    # Gradient with respect to lengthscales
    # Square differences should be [N1 x N2 x D]
    lengthscale_grads = (alpha**2 * np.expand_dims(exponentiated, axis=2) *
                         sq_differences / (lengthscales**3))

    return kern, lengthscale_grads, alpha_grad