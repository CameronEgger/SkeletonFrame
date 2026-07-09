# skeleton

An abstract framework for **relating arbitrary images by shared data points**.

A `Skeleton` holds a set of **parts** and the declared **connections** between
them, then derives how all the images relate. It makes no assumptions about
what the images are, how many there are, what their points mean, or how they
are laid out.

- **`Part`** — one image (opaque: a surface, a file path, an array, an id,
  anything) plus a set of named **points**.
- **`Point`** — a named data point: a label, coordinates of arbitrary
  dimension, and optional opaque `data`.
- **`Connection`** — an explicit declaration that a point on part *A*
  corresponds to a point on part *B*.
- **`Skeleton`** — all parts + all connections. From them it derives
  neighbours, the full adjacency graph, and the transitively-related groups
  (connected components) across every image provided.

The core is pure Python — no rendering, no coordinate math, no domain
knowledge. Build any interpretation (posing, layout, compositing) on top.

## Usage

```python
from skeleton import Skeleton, Point

skel = Skeleton()

# Each part is an image plus named data points (coords are opaque to the core).
skel.add_part("head",  image="head.png",  points=[Point("neck", (100, 70))])
skel.add_part("torso", image="torso.png", points=[Point("neck", (100, 70)),
                                                   Point("hip",  (100, 180))])
skel.add_part("legs",  image="legs.png",  points=[Point("hip", (100, 180))])

# Relate the images by declaring which points correspond.
skel.connect("head",  "neck", "torso", "neck", label="spine")
skel.connect("torso", "hip",  "legs",  "hip")

skel.neighbors("torso")   # {'head', 'legs'}
skel.related("head")      # {'torso', 'legs'}  — transitive
skel.adjacency()          # {'head': {'torso'}, 'torso': {'head', 'legs'}, ...}
skel.components()         # [{'head', 'torso', 'legs'}]
skel.is_connected()       # True
```

## Composing an image

The skeleton owns imaging: attach each part's image, record non-destructive
per-part transforms, and `compose()` renders the whole thing — placing every
part so connected points coincide — into **one image**. The transformer acts on
the individual (smaller) part images; the skeleton keeps the joints aligned by
transforming each part's points in step.

```python
from skeleton.transform import scale, crop

skel.set_image("left_arm", arm_img)      # arm_img is any transforms.Image
skel.transform("left_arm", scale(2))     # recorded, not applied to the original
skel.transform("left_arm", crop((0, 0, 20, 60)))

composed = skel.compose()                # one image, parts placed by their joints
skel.reset("left_arm")                   # revert this part (or reset() for all)
```

Transforms are **non-destructive** — originals are never mutated, `compose()` is
pure, and `reset()` always returns to the untransformed images. Available part
transforms are what the image backend supports (Tk's `PhotoImage` does `scale`
and `crop`; not rotate/flip).

## API

- `Skeleton.add_part(name, image=None, points=None, data=None)`
- `Skeleton.connect(part_a, point_a, part_b, point_b, *, label=None)`
- `Skeleton.neighbors(part)` / `related(part)` / `connections_of(part)`
- `Skeleton.adjacency()` / `components()` / `is_connected()`
- `Skeleton.set_image(part, image)` / `transform(part, part_transform)` / `reset(part=None)`
- `Skeleton.compose()` → one composed image · `transformed_size(part)`
- `skeleton.transform.scale(factor)` / `crop(box)` — `PartTransform`s
- `skeleton.solve_offsets(...)` / `initial_coords(...)` — placement math
- `Part.add_point(name, coords=(), data=None)` / `Part.point(name)`
- `Connection.other(part)` / `endpoints()` / `involves(part)`

## Development

```sh
uv sync            # install the package and dev dependencies (pytest)
```

Requires Python 3.12+.

## Visualization

The `viewer` package is a Tkinter GUI — **standard library only, no extra
dependencies**. It is *pure visualization*: it holds no placement or imaging
logic, it just shows `skeleton.compose()` and records transforms on the skeleton.

```sh
uv run python -m viewer            # composed view (default)
uv run python -m viewer graph      # relationship graph
```

**Composed view** — displays the skeleton's composed image. Select a part and
hit a transform button; the viewer records it on the skeleton and re-renders, so
you see what the command does to that part *and* to the whole figure (joints stay
aligned because the skeleton transforms the points in step).

- Part images are `tkinter.PhotoImage` (`transforms.backends.photoimage.TkImage`).

**Relationship graph** — parts as nodes, connections as edges, coloured per
connected component. Uses only the skeleton's derived topology, so it works on
any skeleton without images or coordinates.

```python
from viewer import show, show_composed
show(my_skeleton)                         # graph window
show_composed(my_skeleton, build_images)  # build_images(skeleton) -> {part: TkImage}
```

The graph layout (`viewer.spring_layout`) is pure and importable without a
display; placement now lives in the skeleton (`skeleton.solve_offsets`).

## Running tests

```sh
uv run pytest                       # run the whole suite
uv run pytest tests/test_skeleton.py    # a single file
uv run pytest -k related -v         # tests matching a keyword, verbose
```
