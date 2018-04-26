TrackML utility library
=======================

A python library to simplify working with the
[High Energy Physics Tracking Machine Learning challenge][kaggle_trackml]
dataset.

Installation
------------

The package can be installed as a user package via

    pip install --user <path/to/repository>

To make a local checkout of the repository available directly it can also be
installed in development mode

    pip install --user --editable .

In both cases, the package can be imported via `import trackml` without
additional configuration. In the later case, changes made to the code are
immediately visible without having to reinstall the package.

Usage
-----

To read the data for one event from the training dataset including the ground
truth information:

```python
from trackml.dataset import load_event

hits, cells, particles, truth = load_event('path/to/event000000123')
```

For the test dataset only the hit information is available. To read only this
data:

```python
from trackml.dataset import load_event

hits, cells = load_event('path/to/event000000456', parts=['hits', 'cells'])
```

To iterate over events in a dataset:

```python
from trackml.dataset import load_dataset

for event_id, hits, cells, particles, truth in load_dataset('path/to/dataset'):
    ...
```

The dataset path can be the path to a directory or to a zip file containing the
events `.csv` files. Each event is lazily loaded during the iteration. Options
are available to read only a subset of available events or only read selected
parts, e.g. only hits or only particles.

To generate a random test submission from truth information and compute the
expected score:

```python
from trackml.randomize import shuffle_hits
from trackml.score import score_event

shuffled = shuffle_hits(truth, 0.05) # 5% probability to reassign a hit
score = score_event(truth, shuffled)
```

All methods either take or return `pandas.DataFrame` objects. You can have a
look at the function docstrings for detailed information.

Authors
-------

*   David Rousseau
*   Ilija Vukotic
*   Moritz Kiehn
*   Sabrina Amrouche

License
-------

All code is licensed under the [MIT license][mit_license].

Dataset
-------

A dataset comprises multiple independent events, where each event contains
simulated measurements of particles generated in a collision between proton
bunches at the [Large Hadron Collider][lhc] at [CERN][cern]. The goal of the
tracking machine learning challenge is to group the recorded measurements or
hits for each event into tracks, sets of hits that belong to the same initial
particle. A solution must uniquely associate each hit to one track (although
some hits can be left unassigned). The training dataset contains the recorded
hits, their truth association to particles, and the initial parameters of those
particles. The test dataset contains only the recorded hits.

The dataset is provided as a set of plain `.csv` files. Each event has four
associated files that contain hits, hit cells, particles, and the ground truth
association between them. The common prefix, e.g. `event000000010`, is always
`event` followed by 9 digits.

    event000000000-hits.csv
    event000000000-cells.csv
    event000000000-particles.csv
    event000000000-truth.csv
    event000000001-hits.csv
    event000000001-cells.csv
    event000000001-particles.csv
    event000000001-truth.csv

Submissions must be provided as a single `.csv` file for the whole dataset with
a name starting with `submission`, e.g.

    submission-test.csv
    submission-final.csv

### Event hits

The hits file contains the following values for each hit/entry:

*   **hit_id**: numerical identifier of the hit inside the event.
*   **x, y, z**: measured x, y, z position (in millimeters) of the hit in
    global coordinates.
*   **volume_id**: numerical identifier of the detector group.
*   **layer_id**: numerical identifier of the detector layer inside the
    group.
*   **module_id**: numerical identifier of the detector module inside
    the layer.

The volume/layer/module id could be in principle be deduced from x, y, z. They
are given here to simplify detector-specific data handling.

### Event hit cells

The cells file contains the constituent active detector cells that comprise each
hit. A cell is the smallest granularity inside each detector module, much like a
pixel on a screen, except that depending on the volume_id a cell can be a square
or a long rectangle. It is identified by two channel identifiers that are unique
within each detector module and encode the position, much like column/row
numbers of a matrix. A cell can provide signal information that the detector
module has recorded in addition to the position. Depending on the detector type
only one of the channel identifiers is valid, e.g. for the strip detectors, and
the value might have different resolution.

*   **hit_id**: numerical identifier of the hit as defined in the hits file.
*   **ch0, ch1**: channel identifier/coordinates unique within one module.
*   **value**: signal value information, e.g. how much charge a particle has
    deposited.

### Event particles

The particles files contains the following values for each particle/entry:

*   **particle_id**: numerical identifier of the particle inside the event.
*   **vx, vy, vz**: initial position or vertex (in millimeters) in global
    coordinates.
*   **px, py, pz**: initial momentum (in GeV/c) along each global axis.
*   **q**: particle charge (as multiple of the absolute electron charge).
*   **nhits**: number of hits generated by this particle.

All entries contain the generated information or ground truth.

### Event truth

The truth file contains the mapping between hits and generating particles and
the true particle state at each measured hit. Each entry maps one hit to one
particle/track.

*   **hit_id**: numerical identifier of the hit as defined in the hits file.
*   **particle_id**: numerical identifier of the generating particle as defined
    in the particles file.
*   **tx, ty, tz** true intersection point in global coordinates (in
    millimeters) between the particle trajectory and the sensitive surface.
*   **tpx, tpy, tpz** true particle momentum (in GeV/c) in the global
    coordinate system at the intersection point. The corresponding vector
    is tangent to the particle trajectory at the intersection point.
*   **weight** per-hit weight used for the scoring metric; total sum of weights
    within one event equals to one.

### Dataset submission information

The submission file must associate each hit in each event to one and only one
reconstructed particle track. The reconstructed tracks must be uniquely
identified only within each event.  Participants are advised to compress the
submission file (with zip, bzip2, gzip) before submission to the
[Kaggle site][kaggle_trackml].

*   **event_id**: numerical identifier of the event; corresponds to the number
    found in the per-event file name prefix.
*   **hit_id**: numerical identifier of the hit inside the event as defined in
    the per-event hits file.
*   **track_id**: user-defined numerical identifier (non-negative integer) of
    the track.


[cern]: https://home.cern
[lhc]: https://home.cern/topics/large-hadron-collider
[mit_license]: http://www.opensource.org/licenses/MIT
[kaggle_trackml]: https://www.kaggle.com/c/trackml-particle-identification
