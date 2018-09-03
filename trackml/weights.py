"""TrackML metric weight calculation"""

from __future__ import print_function

__authors__ = ['Moritz Kiehn']

import math

import numpy
import pandas

from .utils import decode_particle_id

def _compute_order_weight_matrix(proposal, min_hits, max_hits):
    """Compute the hit order weight matrix.

    Returns
    -------
    numpy.ndarray
        Weight matrix indexed by (nhits, ihit), i.e. the total number of
        hits in the tracks and the hit index.
    """
    w = numpy.zeros((max_hits + 1, max_hits))
    for nhits in range(min_hits, max_hits + 1):
        # scale proposal weights to the number of hits on track
        supports = numpy.arange(len(proposal)) * (nhits - 1) / (len(proposal) - 1)
        # compute normalized weights so that a full track has a sum of 1
        weights = numpy.interp(numpy.arange(nhits), supports, proposal)
        weights /= weights.sum()
        w[nhits, :nhits] = weights
    return w

ORDER_PROPOSAL = [10., 8., 6., 5., 3., 3., 3., 5., 6.]
ORDER_MIN_HITS = 4
ORDER_MAX_HITS = 20
ORDER_MATRIX = _compute_order_weight_matrix(ORDER_PROPOSAL, ORDER_MIN_HITS, ORDER_MAX_HITS)

def print_order_weight_matrix(prefix=''):
    print(prefix, 'order weight matrix (weights in percent):', sep='')
    print(prefix, 'nhits | ihit', sep='')
    print(prefix, '      |', sep='', end='')
    for i in range(len(ORDER_MATRIX[1:][0])):
        print(' {:2d}'.format(i), end='')
    print()
    print(prefix, '------+' + len(ORDER_MATRIX[1:][0]) * 3 * '-', sep='')
    for nhits, row in enumerate(ORDER_MATRIX[1:], start=1):
        print(prefix, '  {: 3d} |'.format(nhits), sep='', end='')
        for ihit in range(nhits):
            print(' {:2.0f}'.format(100 * row[ihit]), end='')
        print()

def weight_order(args):
    """Return the weight due to the hit order along the track.
    """
    ihit, nhits = args
    if nhits < ORDER_MIN_HITS:
        return 0.
    if ORDER_MAX_HITS < nhits:
        nhits = ORDER_MAX_HITS
    if ORDER_MAX_HITS <= ihit:
        print("warning long true track ihit ", ihit, " proceeding with weight zero.")
        return 0.
    if nhits <= ihit:
        raise Exception("hit index ", ihit, " is larger than total number of hits ", nhits)
    if nhits < 0:
        raise Exception("total number of hits ", nhits, " is below zero")
    if ihit < 0:
        raise Exception("hit index ", ihit, " is below zero")
    return ORDER_MATRIX[nhits, ihit]

def weight_pt(pt, pt_inf=0.5, pt_sup=3, w_min=0.2, w_max=1.):
    """Return the transverse momentum dependent hit weight.
    """
    # lower cut just to be sure, should not happen except maybe for noise hits
    xp = [min(0.05, pt_inf), pt_inf, pt_sup]
    fp = [w_min, w_min, w_max]
    return numpy.interp(pt, xp, fp, left=0.0, right=w_max)

# particle id for noise hits
INVALID_PARTICLED_ID = 0

def weight_hits_phase1(truth, particles):
    """Compute per-hit weights for the phase 1 scoring metric.

    Hits w/ invalid particle ids, e.g. noise hits, have zero weight.

    Parameters
    ----------
    truth : pandas.DataFrame
        Truth information. Must have hit_id, particle_id, and tz columns.
    particles : pandas.DataFrame
        Particle information. Must have particle_id, vz, px, py, and nhits
        columns.

    Returns
    -------
    pandas.DataFrame
        `truth` augmented with additional columns: particle_nhits, ihit,
        weight_order, weight_pt, and weight.
    """
    # fill selected per-particle information for each hit
    selected = pandas.DataFrame({
        'particle_id': particles['particle_id'],
        'particle_vz': particles['vz'],
        'particle_nhits': particles['nhits'],
        'weight_pt': weight_pt(numpy.hypot(particles['px'], particles['py'])),
    })
    combined = pandas.merge(truth, selected,
                            how='left', on=['particle_id'],
                            validate='many_to_one')

    # fix pt weight for hits w/o associated particle
    combined['weight_pt'].fillna(0.0, inplace=True)
    # fix nhits for hits w/o associated particle
    combined['particle_nhits'].fillna(0.0, inplace=True)
    combined['particle_nhits'] = combined['particle_nhits'].astype('i4')
    # compute hit count and order using absolute distance from particle vertex
    combined['abs_dvz'] = numpy.absolute(combined['tz'] - combined['particle_vz'])
    combined['ihit'] = combined.groupby('particle_id')['abs_dvz'].rank().transform(lambda x: x - 1).fillna(0.0).astype('i4')
    # compute order-dependent weight
    combined['weight_order'] = combined[['ihit', 'particle_nhits']].apply(weight_order, axis=1)

    # compute combined weight normalized to 1
    w = combined['weight_pt'] * combined['weight_order']
    w /= w.sum()
    combined['weight'] = w

    # return w/o intermediate columns
    return combined.drop(columns=['particle_vz', 'abs_dvz'])

def weight_hits_phase2(truth, particles):
    """Compute per-hit weights for the phase 2 scoring metric.

    This is the phase 1 metric with an additional particle preselection, i.e.
    only a subset of the particles have a non-zero score.

    Parameters
    ----------
    truth : pandas.DataFrame
        Truth information. Must have hit_id, particle_id, and tz columns.
    particles : pandas.DataFrame
        Particle information. Must have particle_id, vz, px, py, and nhits
        columns.

    Returns
    -------
    pandas.DataFrame
        `truth` augmented with additional columns: particle_nhits, ihit,
        weight_order, weight_pt, and weight.
    """
    # fill selected per-particle information for each hit
    selected = pandas.DataFrame({
        'particle_id': particles['particle_id'],
        'particle_vz': particles['vz'],
        'particle_nhits': particles['nhits'],
        'weight_pt': weight_pt(numpy.hypot(particles['px'], particles['py'])),
    })
    selected = decode_particle_id(selected)
    combined = pandas.merge(truth, selected,
                            how='left', on=['particle_id'],
                            validate='many_to_one')

    # fix pt weight for hits w/o associated particle
    combined['weight_pt'].fillna(0.0, inplace=True)
    # fix nhits for hits w/o associated particle
    combined['particle_nhits'].fillna(0.0, inplace=True)
    combined['particle_nhits'] = combined['particle_nhits'].astype('i4')

    # compute hit count and order using absolute distance from particle vertex
    combined['abs_dvz'] = numpy.absolute(combined['tz'] - combined['particle_vz'])
    combined['ihit'] = combined.groupby('particle_id')['abs_dvz'].rank().transform(lambda x: x - 1).fillna(0.0).astype('i4')
    # compute order-dependent weight
    combined['weight_order'] = combined[['ihit', 'particle_nhits']].apply(weight_order, axis=1)

    # compute normalized combined weight w/ extra particle selection
    weight = combined['weight_pt'] * combined['weight_order']
    weight[combined['generation'] != 0] = 0
    weight /= weight.sum()
    # normalize total event weight
    combined['weight'] = weight

    # return w/o intermediate columns
    return combined.drop(columns=['particle_vz', 'abs_dvz'])
