"""TrackML dataset loading"""

__authors__ = ['Moritz Kiehn', 'Sabrina Amrouche']

import glob
import os.path as op

import pandas

CELLS_DTYPES = dict([
    ('hit_id', 'i4'),
    ('ch0', 'i4'),
    ('ch1', 'i4'),
    ('value', 'f4'),
])
HITS_DTYPES = dict([
    ('hit_id', 'i4'),
    ('x', 'f4'),
    ('y', 'f4'),
    ('z','f4'),
    ('volume_id', 'i4'),
    ('layer_id', 'i4'),
    ('module_id', 'i4'),
])
PARTICLES_DTYPES = dict([
    ('particle_id', 'i8'),
    ('vx', 'f4'),
    ('vy', 'f4'),
    ('vz', 'f4'),
    ('px', 'f4'),
    ('py', 'f4'),
    ('pz', 'f4'),
    ('q', 'i4'),
    ('nhits', 'i4'),
])
TRUTH_DTYPES = dict([
    ('hit_id', 'i4'),
    ('particle_id', 'i8'),
    ('tx', 'f4'),
    ('ty', 'f4'),
    ('tz', 'f4'),
    ('tpx', 'f4'),
    ('tpy', 'f4'),
    ('tpz', 'f4'),
    ('weight', 'f4'),
])
DTYPES = {
    'cells': CELLS_DTYPES,
    'hits': HITS_DTYPES,
    'particles': PARTICLES_DTYPES,
    'truth': TRUTH_DTYPES,
}

def _load_event_data(prefix, name):
    """Load per-event data for one single type, e.g. hits, or particles.
    """
    expr = '{!s}-{}.csv*'.format(prefix, name)
    files = glob.glob(expr)
    dtype = DTYPES[name]
    if len(files) == 1:
        return pandas.read_csv(files[0], header=0, index_col=False, dtype=dtype)
    elif len(files) == 0:
        raise Exception('No file matches \'{}\''.format(expr))
    else:
        raise Exception('More than one file matches \'{}\''.format(expr))

def load_event_hits(prefix):
    """Load the hits information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'hits')

def load_event_cells(prefix):
    """Load the hit cells information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'cells')

def load_event_particles(prefix):
    """Load the particles information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'particles')

def load_event_truth(prefix):
    """Load only the truth information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'truth')

def load_event(prefix, parts=['hits', 'cells', 'particles', 'truth']):
    """Load data for a single event with the given prefix.

    Parameters
    ----------
    prefix : str or pathlib.Path
        The common prefix name for the event files, i.e. without `-hits.csv`).
    parts : List[{'hits', 'cells', 'particles', 'truth'}], optional
        Which parts of the event files to load.

    Returns
    -------
    tuple
        Contains a `pandas.DataFrame` for each element of `parts`. Each
        element has field names identical to the CSV column names with
        appropriate types.
    """
    return tuple(_load_event_data(prefix, name) for name in parts)

def load_dataset(path, skip=None, nevents=None, **kw):
    """Provide an iterator over (all) events in a dataset directory.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to the dataset directory.
    skip : int, optional
        Skip the first `skip` events.
    nevents : int, optional
        Only load a maximum of `nevents` events.
    parts : List[{'hits', 'cells', 'particles', 'truth'}], optional
        Which parts of each event files to load.

    Yields
    ------
    event_id : int
        The event identifier.
    *data
        Event data element as specified in `parts`.
    """
    files = glob.glob(op.join(path, 'event*-*'))
    names = set(op.basename(_).split('-', 1)[0] for _ in files)
    names = sorted(names)
    if skip is not None:
        names = names[skip:]
    if nevents is not None:
        names = names[:nevents]
    for name in names:
        event_id = int(name[5:])
        yield (event_id,) + load_event(op.join(path, name), **kw)
