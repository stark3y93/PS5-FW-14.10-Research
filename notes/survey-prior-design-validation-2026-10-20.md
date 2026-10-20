# Survey prior-design validation — 2026-10-20

The independent window planner reconstructs earlier evenly spaced window starts before excluding their overlap from its candidate frame. Previously, it accepted a `prior_samples` count larger than the number of distinct byte starts available to a window. In that case, the reconstructed earlier survey contains duplicate starts even though the earlier entropy sampler would reject that configuration. The planner could therefore describe an impossible prior design as the basis for an independent survey.

The planner and frame-size helper now reject this configuration with `ValueError`. The bound is `prior_samples <= size - window_size + 1`, matching the distinct-start check in `sample_entropy`. This does not reinterpret the observed 14.10 data; it only validates a caller-supplied synthetic or local survey design.

Verification: `PYTHONPATH=src python -m unittest discover -s tests -v` passed 50 synthetic tests on this branch, including the new repeated-start regression. No firmware data or device was accessed for this change.
