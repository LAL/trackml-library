"""TrackML utility functions"""

__authors__ = ['Moritz Kiehn']

import numpy as np

def add_position_quantities(data, prefix=''):
    """Add derived position quantities rho, phi, and r.
    """
    x = data['{}x'.format(prefix)]
    y = data['{}y'.format(prefix)]
    z = data['{}z'.format(prefix)]
    t = np.hypot(x, y)
    data['{}rho'.format(prefix)] = t
    data['{}phi'.format(prefix)] = np.arctan2(y, x)
    data['{}r'.format(prefix)] = np.hypot(t, z)
    return data

def add_momentum_quantities(data, prefix=''):
    """Add derived momentum quantities pt, pphi, peta, p.
    """
    px = data['{}px'.format(prefix)]
    py = data['{}py'.format(prefix)]
    pz = data['{}pz'.format(prefix)]
    pt = np.hypot(px, py)
    p = np.hypot(pt, pz)
    data['{}pt'.format(prefix)] = pt
    data['{}pphi'.format(prefix)] = np.arctan2(py, px)
    data['{}peta'.format(prefix)] = np.arctanh(pz / p)
    data['{}p'.format(prefix)] = p
    return data

def decode_particle_id(data):
    """Decode particle_id into vertex id, generation, etc.
    """
    components = [
        ('vertex_id',    0xfff0000000000000, 13 * 4),
        ('primary_id',   0x000ffff000000000, 9 * 4),
        ('generation',   0x0000000fff000000, 6 * 4),
        ('secondary_id', 0x0000000000fff000, 3 * 4),
        ('process',      0x0000000000000fff, 0),
    ]
    pid = data['particle_id'].values.astype('u8')
    for name, mask, shift in components:
        data[name] = (pid & mask) >> shift
    return data
