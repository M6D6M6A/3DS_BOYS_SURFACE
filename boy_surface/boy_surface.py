# -*- coding: utf-8 -*-
"""
boy_surface.py
==============

Bryant-Kusner Boy's surface generator for Autodesk 3ds Max 2025 +  
(Python 3.11 with NumPy available).

---------------------------------------------------------------------------
Key features
---------------------------------------------------------------------------
* Single-knob resolution - choose ``resolution``; the script derives the
  angular density automatically.
* Correct Möbius edge - outermost ring is glued with a half-turn twist,
  giving the surface the topology of the real projective plane.
* Vectorised computation - pure NumPy, typically 100x faster than nested
  Python loops.
* Clean Max mesh - converted to Editable Poly, quads generated, pivot
  centred, smoothing groups set.

---------------------------------------------------------------------------
Credits
---------------------------------------------------------------------------
* Original idea & Blender prototype - Sean, Inform Studio  
  "Rendering Boy's Surface in Blender", Nov 2020  
  <https://inform.studio/blog/rendering-boys-surface-in-blender/>
* Port, logic refinements - Philipp Reuter  <reuter.philipp@ymail.com>
* Additional refactor & documentation - ChatGPT (o3), May 2025

---------------------------------------------------------------------------
Licence   (Creative Commons — CC BY-NC 4.0)
---------------------------------------------------------------------------
You are free to share and adapt the code for non-commercial use,
provided you give appropriate credit.  For any commercial usage please
obtain written permission from Philipp Reuter.

"""

##############################################################################
# Imports
##############################################################################

from __future__ import annotations     # → future-proof type hints (PEP 563/649)

import math                            # → √5 and π
from typing import Tuple, List         # → explicit container types

import numpy as np                     # → vectorised numerics
from pymxs import runtime as rt        # → 3ds Max Python API (MAXScript bridge)

##############################################################################
# Main class
##############################################################################


class BoysSurfaceGenerator:
    """
    Efficient, seam-correct Boy's-surface mesh builder.

    Parameters
    ----------
    resolution : int, default 64
        Number of *radial* subdivisions :math:`n_r`.  Must be ≥ 2.
    ratio : float, keyword-only, default 2.0
        Angular-to-radial density multiplier.  The script sets
        :math:`n_φ = \\operatorname{round}(\\text{ratio} x \\text{resolution})`
        and enforces *evenness* so the ½-turn Möbius pairing works.

    Examples
    --------
    >>> # quick preview mesh (open disk + Möbius edge)
    >>> BoysSurfaceGenerator(resolution=32).build()
    >>> # square-ish aspect (n_φ ≈ n_r)
    >>> BoysSurfaceGenerator(resolution=200, ratio=1.0).build()
    """

    # --------------------------------------------------------------------- #
    # Construction & parameter validation                                   #
    # --------------------------------------------------------------------- #
    def __init__(self, resolution: int = 64, *, ratio: float = 2.0) -> None:
        """
        Validate user input, then store final grid sizes.

        * ``resolution`` drives radial density.
        * ``ratio`` scales angular density and must yield an even integer
          so that vertex j and j+½-turn can be paired cleanly.
        """
        # --- basic sanity --------------------------------------------------
        if resolution < 2:
            raise ValueError("resolution must be at least 2.")
        n_phi = ratio * resolution
        if n_phi < 4 or int(round(n_phi)) % 2:
            raise ValueError("ratio * resolution must be an even integer ≥ 4.")

        # --- store final dimensions (integers!) ----------------------------
        self.n_r: int = int(resolution)         # number of concentric rings
        self.n_phi: int = int(round(n_phi))     # vertices on each ring (even)

    # --------------------------------------------------------------------- #
    # Bryant-Kusner immersion (vectorised)                                  #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _xyz(w: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Map complex parameter *w* to Cartesian coordinates (Bryant-Kusner).

        The *auxiliary functions* g₁, g₂, g₃ minimise the Willmore energy of
        the projective plane.  Everything below is pure NumPy and therefore
        broadcasts to any shape.

        Parameters
        ----------
        w : np.ndarray
            Complex array with |w| ≤ 1.

        Returns
        -------
        x, y, z : np.ndarray
            Cartesian coordinates matching the shape of *w*.
        """
        w = np.asarray(w, dtype=np.complex128)   # ensure proper dtype

        z6 = w  6                              #   w⁶
        denom = z6 + math.sqrt(5) * w  3 - 1   #   w⁶ + √5 w³ − 1

        # ---- auxiliary functions g₁, g₂, g₃ --------------------------------
        g1 = -1.5 * np.imag(w * (1 - w  4) / denom)      # Im part → y-axis
        g2 = -1.5 * np.real(w * (1 + w  4) / denom)      # Re part → x-axis
        g3 = np.imag((1 + z6) / denom) - 0.5               # z-axis component
        g = g1  2 + g2  2 + g3  2                    # common denominator

        # final Cartesian position
        return g1 / g, g2 / g, g3 / g

    # --------------------------------------------------------------------- #
    # Main build routine                                                    #
    # --------------------------------------------------------------------- #
    def build(self) -> rt.Mesh:
        """
        Generate the mesh and return a 3ds Max ``Mesh`` object.

        The routine is split into logical steps:

        1. Parameter grid - build NumPy arrays for r and φ (include *r = 1*).
        2. Vertices      - evaluate Bryant-Kusner map, prepend centre.
        3. Faces         - create triangles (radial strips, Möbius strip,
                               central fan).
        4. Post-process  - Editable Poly, quads, pivot, smoothing.
        """
        ############################################################################
        # 1) Parameter grid
        ############################################################################
        ring: int = self.n_phi                   # vertices per ring (even)

        r_vals = np.linspace(0.0, 1.0, self.n_r, endpoint=True)[1:]  # omit r=0
        phi_vals = np.linspace(0.0, 2 * math.pi, ring, endpoint=False)
        R, Phi = np.meshgrid(r_vals, phi_vals, indexing="ij")        # shape (n_r-1, n_phi)
        w = R * np.exp(1j * Phi)                                     # complex coordinates

        ############################################################################
        # 2) Vertices
        ############################################################################
        X, Y, Z = self._xyz(w)                                       # NumPy arrays
        verts_np = np.column_stack((X.ravel(), Y.ravel(), Z.ravel()))  # flatten grid

        # --- centre vertex (w = 0) ------------------------------------------
        centre_xyz = list(map(float, self._xyz(0j)))                  # convert to floats
        verts_np = np.vstack((centre_xyz, verts_np))                  # prepend centre

        # Convert to rt.Point3 (NumPy scalar → Python float → Max float)
        verts_rt: List[rt.Point3] = [
            rt.Point3(float(x), float(y), float(z)) for x, y, z in verts_np
        ]

        ############################################################################
        # Helper indices (Max is 1-based)
        ############################################################################
        centre_idx: int = 1
        first_ring_start: int = 2
        outer_ring_start: int = first_ring_start + (self.n_r - 2) * ring
        half_turn: int = ring // 2                                     # even by design

        ############################################################################
        # 3) Faces (triangles)
        ############################################################################
        faces: List[Tuple[int, int, int]] = []

        # 3-a) Radial strips (quad split into two triangles)
        for i in range(self.n_r - 2):                                  # up to penultimate ring
            inner = first_ring_start + i * ring                        # base index of inner ring
            outer = inner + ring                                       # next ring outward
            for j in range(ring):
                a = inner + j
                b = outer + j
                c = outer + (j + 1) % ring
                d = inner + (j + 1) % ring
                #  two triangles per rectangular cell
                faces.extend([(a, b, c), (a, c, d)])

        # 3-b) Möbius strip (outer ring glued with half-turn twist)
        for j in range(ring):
            a = outer_ring_start + j
            an = outer_ring_start + (j + 1) % ring
            b = outer_ring_start + (j + half_turn) % ring
            bn = outer_ring_start + (j + half_turn + 1) % ring
            #  orientation (an, b, a) + (an, bn, b) induces the required twist
            faces.extend([(an, b, a), (an, bn, b)])

        # 3-c) Central fan (all first-ring vertices meet at centre)
        for j in range(ring):
            v2 = first_ring_start + j
            v3 = first_ring_start + (j + 1) % ring
            faces.append((centre_idx, v3, v2))

        # Convert triangle list to rt.Point3 triplets
        faces_rt: List[rt.Point3] = [
            rt.Point3(int(i), int(j), int(k)) for i, j, k in faces
        ]

        ############################################################################
        # 4) Create mesh and tidy up
        ############################################################################
        mesh = rt.mesh(vertices=verts_rt,
                       faces=faces_rt,
                       name="Boy's Surface")

        self._postprocess(mesh)  # pivot, quads, smoothing, etc.
        return mesh

    # --------------------------------------------------------------------- #
    # Post-processing helper                                                #
    # --------------------------------------------------------------------- #
    @staticmethod
    def _postprocess(mesh: rt.Mesh) -> None:
        """
        Convert to Editable Poly, quadrify, centre the pivot, rotate, and
        assign a single smoothing group.

        Rotation of −90 ° about the Y-axis aligns the “umbrella” opening with
        Max's +Z axis for intuitive viewing.
        """
        poly = rt.convertToPoly(mesh)                       # Editable Poly
        rt.select(poly)                                     # make the mesh active
        rt.execute("PolyToolsModeling.Quadrify true false") # all-quad faces
        rt.centerPivot(poly)                                # pivot = geometric centre
        poly.position = rt.Point3(0, 0, 0)                  # move to world origin
        poly.rotation = rt.Eulerangles(0, -90, 0)           # rotate for display
        rt.polyOp.setFaceSmoothGroup(poly, poly.faces, 1)   # single smoothing group


##############################################################################
# Demo entry-point (will only run when the file is executed directly)
##############################################################################
if __name__ == "__main__":
    # 128 radial rings x 256 vertices per ring → ~65 k triangles
    BoysSurfaceGenerator(resolution=128).build()