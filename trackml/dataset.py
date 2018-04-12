"""TrackML dataset loading"""

__authors__ = ['Moritz Kiehn', 'Sabrina Amrouche']

import glob
import os.path as op

import pandas

HITS_DTYPES = dict([
    ('hit_id', 'i4'),
    ('x', 'f4'),
    ('y', 'f4'),
    ('z','f4'),
    ('volume_id', 'i4'),
    ('layer_id', 'i4'),
    ('module_id', 'i4'),
])
CELLS_DTYPES = dict([
    ('hit_id', 'i4'),
    ('ch0', 'i4'),
    ('ch1', 'i4'),
    ('value', 'f4'),
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

def _load_event_data(prefix, name, dtype):
    """
    Load per-event data for one single type, e.g. hits, or particles.
    """
    files = glob.glob('{}-{}.csv*'.format(prefix, name))
    if len(files) == 1:
        return pandas.read_csv(files[0], header=0, index_col=False, dtype=dtype)
    elif len(files) == 0:
        raise Exception('No file found matching {}-{}.csv*'.format(prefix, name))
    else:
        raise Exception('More than one file found matching {}-{}.csv*'.format(prefix, name))

def load_event_hits(prefix):
    """
    Load the hits information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'hits', HITS_DTYPES)

def load_event_cells(prefix):
    """
    Load the hit cells information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'cells', CELLS_DTYPES)

def load_event_particles(prefix):
    """
    Load the particles information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'particles', PARTICLES_DTYPES)

def load_event_truth(prefix):
    """
    Load only the truth information for a single event with the given prefix.
    """
    return _load_event_data(prefix, 'truth', TRUTH_DTYPES)

_LOAD_FUNCTIONS = {
    'hits': load_event_hits,
    'cells': load_event_cells,
    'particles': load_event_particles,
    'truth': load_event_truth, }

def load_event(prefix, parts=['hits', 'cells', 'particles', 'truth']):
    """
    Load data for a single event with the given prefix.

    With the default settings a tuple (hits, particles, truth) is returned.
    Each element is a pandas DataFrame with field names identical to the CSV
    column names and appropriate types. Depending on the options only a
    subset of the DataFrames is loaded.
    """
    return tuple(_LOAD_FUNCTIONS[_](prefix) for _ in parts)

def load_dataset(path, **kw):
    """
    Provide an iterator over all events in a dataset directory.

    For each event it returns the event_id and the output of `load_event`
    concatenated as a single tuple.
    """
    files = glob.glob(op.join(path, 'event*-*'))
    names = set(op.basename(_).split('-', 1)[0] for _ in files)
    names = sorted(names)
    for name in names:
        event_id = int(name[5:])
        yield (event_id,) + load_event(op.join(path, name), **kw)
