"""TrackML dataset loading"""

__authors__ = ['Moritz Kiehn', 'Sabrina Amrouche', 'Nimar Arora']

import glob
import os
import os.path as op
import re
import zipfile

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
    ('particle_type', 'i4'),
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
DEFAULT_PARTS = ['hits', 'cells', 'particles', 'truth']

def _load_event_data(prefix, name):
    """Load per-event data for one single type, e.g. hits, or particles.
    """
    # csv files can be individually zipped with extension .csv.gz
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

def load_event(prefix, parts=DEFAULT_PARTS):
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

def load_dataset(path, skip=None, nevents=None, parts=DEFAULT_PARTS):
    """Provide an iterator over (all) events in a dataset.

    Parameters
    ----------
    path : str or pathlib.Path
        Path to a directory or a zip file containing event files.
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
    # extract a sorted list of event file prefixes.
    def list_prefixes(files):
        # Note: the file names may optionally have a directory prefix if they
        # are derived from a zipfile, for example. Hence the regular expression
        # can't be anchored at the beginning of the file name.
        regex = re.compile('.*event\d{9}-[a-zA-Z]+.csv(.gz)?$')
        files = filter(regex.match, files)
        prefixes = set(_.split('-', 1)[0] for _ in files)
        prefixes = sorted(prefixes)
        if skip is not None:
            prefixes = prefixes[skip:]
        if nevents is not None:
            prefixes = prefixes[:nevents]
        return prefixes

    # TODO use `yield from` once we increase the python requirement
    if op.isdir(path):
        for x in _iter_dataset_dir(path, list_prefixes(os.listdir(path)), parts):
            yield x
    else:
        with zipfile.ZipFile(path, mode='r') as z:
            for x in _iter_dataset_zip(z, list_prefixes(z.namelist()), parts):
                yield x

def _extract_event_id(prefix):
    """Extract event_id from prefix.

    E.g. event_id=1 from `event000000001` or from `train_1/event000000001`
    """
    regex = r'.*event(\d+)'
    groups = re.findall(regex, prefix)
    return int(groups[0])

def _iter_dataset_dir(directory, prefixes, parts):
    """Iterate over selected events files inside a directory.
    """
    for p in prefixes:
        yield (_extract_event_id(p),) + load_event(op.join(directory, p), parts)

def _iter_dataset_zip(zipfile, prefixes, parts):
    """Iterate over selected event files inside a zip archive.
    """
    for p in prefixes:
        files = [zipfile.open('{}-{}.csv'.format(p, _), mode='r') for _ in parts]
        dtypes = [DTYPES[_] for _ in parts]
        data = tuple(pandas.read_csv(f, header=0, index_col=False, dtype=d)
                                     for f, d in zip(files, dtypes))
        yield (_extract_event_id(p),) + data
