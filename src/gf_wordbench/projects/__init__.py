"""Active-project domain and lifecycle package.

Stable cross-module consumers use :mod:`gf_wordbench.projects.public`.  This
package initializer intentionally performs no eager imports so importing
``gf_wordbench.projects`` remains side-effect free and cannot create dependency
cycles while the public facade composes project-owned contracts and use cases.
"""

__all__: tuple[str, ...] = ()
