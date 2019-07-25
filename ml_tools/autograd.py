from autograd import make_jvp
import autograd.numpy as np
from typing import Callable, Tuple
from autograd import hessian, jacobian
from scipy.optimize import minimize


def forward_grad_vector(fun, arg_no, n_derivs, *args):
    # Example call:
    # forward_grad_vector(
    # ard_rbf_kernel_efficient, 3, lscales.shape[0], X, X, var, lscales)
    # TODO: Maybe make syntax agree even more with the current autograd.

    grad = make_jvp(fun, arg_no)
    all_indices = np.eye(n_derivs)

    all_grads = list()

    for cur_index in all_indices:

        all_grads.append(grad(*args)(cur_index)[1])

    return np.stack(all_grads, -1)


def multivariate_normal_zero_mean_from_inv(x, cov_inv):

    n = cov_inv.shape[0]
    sign, logdet = np.linalg.slogdet(cov_inv)
    logdet = sign * logdet
    det_term = 0.5 * (logdet - n * np.log(2 * np.pi))

    logpdf = det_term - 0.5 * x @ cov_inv @ x
    return logpdf


def multivariate_normal_logpdf(x, cov):

    sign, logdet = np.linalg.slogdet(np.pi * 2 * cov)
    logdet = sign * logdet
    det_term = -0.5 * logdet

    # TODO: Could be improved by using some kind of Cholesky here rather than
    # inverse -- or even a solve.
    total_prior = det_term - 0.5 * x @ np.linalg.inv(cov) @ x

    return total_prior


def logdet_via_cholesky(mat):

    chol = np.linalg.cholesky(mat)
    logdet = 2 * np.sum(np.log(np.diag(chol)))
    return logdet


def fit_laplace_approximation(neg_log_posterior_fun: Callable[[np.ndarray],
                                                              float],
                              start_val: np.ndarray,
                              optimization_method: str = 'Newton-CG') \
        -> Tuple[np.ndarray, np.ndarray, bool]:
    """
    Fits a Laplace approximation to the posterior.
    Args:
        neg_log_posterior_fun: Returns the [unnormalized] negative log
            posterior density for a vector of parameters.
        start_val: The starting point for finding the mode.
        optimization_method: The method to use to find the mode. This will be
            fed to scipy.optimize.minimize, so it has to be one of its
            supported methods. Defaults to "Newton-CG".
    Returns:
        A tuple containing three entries; mean, covariance and a boolean flag
        indicating whether the optimization succeeded.
    """

    jac = jacobian(neg_log_posterior_fun)
    hess = hessian(neg_log_posterior_fun)

    result = minimize(neg_log_posterior_fun, start_val, jac=jac, hess=hess,
                      method=optimization_method)

    covariance_approx = np.linalg.inv(hess(result.x))
    mean_approx = result.x

    return mean_approx, covariance_approx, result.success


def linear_regression_online_update(m_km1, P_km1, H, m_obs, var_obs):
    # m_km1: Prior mean
    # P_km1: Prior cov
    # H: Link from latent to observed
    # m_obs: Mean of observation
    # var_obs: Variance of observation

    # We need to work with matrices here or the maths will be wrong
    assert all([len(x.shape) == 2 for x in [m_km1, H]]), \
        'm_km1 and H must have two dimensions each!'

    v_k = m_obs - H @ m_km1

    S_k = H @ P_km1 @ H.T + var_obs
    K_k = P_km1 @ H.T * (1 / S_k)
    m_k = m_km1 + K_k * v_k
    P_k = P_km1 - (K_k * S_k) @ K_k.T

    # Calculate the log marginal likelihood here too
    # sign, logdet = np.linalg.slogdet(2 * np.pi * S_k)
    # logdet_a = sign * logdet

    # Do this another way
    # rel_chol = np.linalg.cholesky(2 * np.pi * S_k)
    # TODO: CHECK THIS
    logdet = logdet_via_cholesky(2 * np.pi * S_k)

    # Second part
    quadratic_term = 0.5 * v_k.T @ np.linalg.solve(S_k, v_k)
    energy_contrib = 0.5 * logdet + quadratic_term

    return m_k, P_k, np.squeeze(energy_contrib)
