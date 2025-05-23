
# Boy's Surface Generator

![Demo Rendering](demo/boys_demo.png)

**Bryant–Kusner Boy’s Surface** generator script for Autodesk **3ds Max 2025+** (Python 3.11, NumPy, Arnold).

> *Generate a Watertight, Möbius‑correct mesh of the real projective plane, with one line of Python.*

---
## Features
- **One‑knob resolution** – `resolution` parameter controls both radial and angular density.
- **Seam‑free Möbius edge** – outer ring glued with a half‑turn twist, no post‑welding required.
- **Vectorised NumPy maths** – ~100× faster than naïve for‑loops.
- **3ds Max friendly** – mesh is Editable Poly, quad‑ified, pivot centred, smoothing groups set.
- **Licensed CC BY‑NC 4.0** – free for academic & personal use; ask author for commercial projects.

## Project Layout
```
boys_surface_repo/
├── boy_surface/            # Python package
│   ├── __init__.py         # ← keeps the folder importable
│   └── boy_surface.py      # ← script
├── images/
│   └── demo_rendering.png  # demo image
├── LICENSE.md              # CC BY‑NC 4.0 text
└── README.md               # this file
```

## Quick Start
```bash
git clone https://github.com/your-user/boys_surface.git
cd boys_surface/boy_surface
python boy_surface.py
```

## Parameters
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `resolution` | `int`  | `64` | Radial ring count. Angular count is `ratio × resolution`. |
| `ratio` (kw‑only) | `float` | `2.0` | angular : radial ratio, must yield an even integer. |

## Rendering Guide
*[Autodesk’s official Thin‑Film “Soap Bubble” settings (2025 Help)](https://help.autodesk.com/view/ARNOL/ENU/?guid=arnold_user_guide_ac_standard_surface_ac_standard_thinfilm_html)*
```
Base Weight.................. 0
Specular Weight.............. 1
Specular IOR................. 1.0
Specular Roughness........... 0
Transmission Weight.......... 1
Coat Weight.................. 1
Coat IOR..................... 1.5
Thin‑Film Thickness.......... 500 nm
Thin‑Film IOR................ 1.4
Thin‑Walled.................. ON
```

## License
**Creative Commons — CC BY‑NC 4.0**  
© 2025 Philipp Reuter & ChatGPT (o3).  
Please contact *reuter.philipp@ymail.com* for commercial licensing.

## Acknowledgements
- Original Blender prototype by **Sean / Inform Studio**  
  _“Rendering Boy’s Surface in Blender”_ (2020)  
  <https://inform.studio/blog/rendering-boys-surface-in-blender/>
- NumPy, Autodesk Arnold, 3ds Max 2025 Python bridge.