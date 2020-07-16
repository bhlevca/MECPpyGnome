"""
tests for classes in release module
Tests for release are in test_spill.py and test_release.py
test_spill.py was getting too big so moved the tests that do not use a Spill
object here - more comprehensive tests of release objects within a Spill are
in test_spill.py
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

from builtins import range
from builtins import open
from future import standard_library
standard_library.install_aliases()
from builtins import *
from builtins import object
import os
from datetime import datetime, timedelta

import pytest

import numpy as np

from gnome.spill import (Release,
                         PointLineRelease,
                         GridRelease)
from gnome.spill.release import release_from_splot_data
from gnome.spill.le import LEData


def test_init():
    Release(release_time=datetime.now())


class TestRelease(object):
    rel_time = datetime.now().replace(microsecond=0)

    def test_init(self):
        rel = Release(self.rel_time, 0)
        assert rel.num_elements == 0
        assert rel.release_time == self.rel_time
        assert rel.release_duration == 0


# def test_grid_release():
#     """
#     fixme: test something more here? like actually have the release do its thing?
#     """
#     bounds = ((0, 10), (2, 12))
#     release = GridRelease(datetime.now(), bounds, 3)
#
#     assert np.array_equal(release.start_position, [[0., 10., 0.],
#                                                    [1., 10., 0.],
#                                                    [2., 10., 0.],
#                                                    [0., 11., 0.],
#                                                    [1., 11., 0.],
#                                                    [2., 11., 0.],
#                                                    [0., 12., 0.],
#                                                    [1., 12., 0.],
#                                                    [2., 12., 0.]])

# todo: add other release to this test - need schemas for all

rel_time = datetime(2012, 8, 20, 13)
rel_type = [PointLineRelease(release_time=rel_time,
                             num_elements=5,
                             start_position=(0, 0, 0)),
            PointLineRelease(release_time=rel_time,
                             num_per_timestep=5,
                             start_position=(0, 0, 0))]
# SpatialRelease(rel_time, np.zeros((4, 3), dtype=np.float64))]


@pytest.mark.parametrize("rel_type", rel_type)
def test_release_serialization_deserialization(rel_type):
    '''
    test for a mid run state.
    'save' preserves midrun parameters
    'webapi' does not
    '''
    cls = rel_type.__class__
    n_rel = cls.deserialize(rel_type.serialize())
    assert n_rel == rel_type

rel_time = datetime(2014, 1, 1, 0, 0)
pos = (0, 10, 20)

@pytest.fixture('function')
def r1():
    #150 minute continuous release
    return PointLineRelease(release_time=rel_time,
                            start_position=pos,
                            end_position= (10, 20, 30),
                            end_release_time=rel_time + timedelta(seconds=900)*10,
                            num_elements=1000,
                            release_mass=5000)

@pytest.fixture('function')
def r2():
    return PointLineRelease(release_time=rel_time,
                            start_position=pos,
                            end_position= (10, 20, 30),
                            num_elements=1000)

@pytest.fixture('function')
def r3():
    return PointLineRelease(release_time=rel_time,
                            start_position=pos,
                            end_position= (10, 20, 30),
                            end_release_time=rel_time + timedelta(seconds=900)*10,
                            num_per_timestep=100,
                            release_mass=5000)

class TestPointLineRelease(object):

    def test_LE_timestep_ratio(self, r1):
        r1.end_release_time = rel_time + timedelta(seconds=1000)*10
        #timestep of 10 seconds. 10,000 second release, min 1000 elements exactly
        assert r1.LE_timestep_ratio(10) == 1
        assert r1.LE_timestep_ratio(20) == 2

    def test_get_num_release_time_steps(self, r1):
        assert r1.get_num_release_time_steps(9000) == 1
        assert r1.get_num_release_time_steps(8999) == 2
        assert r1.get_num_release_time_steps(900) == 10
        assert r1.get_num_release_time_steps(899) == 11

    def test_prepare_for_model_run(self, r1, r2, r3):
        r1.prepare_for_model_run(900)
        assert len(r1._release_ts.data) == 11
        assert r1._release_ts.at(None, r1.release_time) == 0
        assert r1._release_ts.at(None, r1.end_release_time) == 1000
        assert np.all(r1._release_ts.data == np.linspace(0,1000, len(r1._release_ts.data)))
        assert r1._mass_per_le == 5
        assert r1.get_num_release_time_steps(900) == 10
        assert len(r1._pos_ts.time) == 11
        assert np.all(r1._pos_ts.at(None, r1.release_time + timedelta(seconds=900)*5) == np.array([(5.,15.,25.)]))

        r1.rewind()
        r1.release_mass = 2500
        r1.prepare_for_model_run(450)
        assert len(r1._release_ts.data) == 21
        assert r1._release_ts.at(None, r1.release_time) == 0
        assert r1._release_ts.at(None, r1.end_release_time) == 1000
        assert np.all(r1._release_ts.data == np.linspace(0,1000, len(r1._release_ts.data)))
        assert r1._mass_per_le == 2.5
        assert len(r1._pos_ts.time) == 21
        assert np.all(r1._pos_ts.at(None, r1.release_time + timedelta(seconds=450)*10) == np.array([(5.,15.,25.)]))

        #No end_release time. Timeseries must be 2 entries, 1 second apart

        r2.prepare_for_model_run(900)
        assert len(r2._release_ts.data) == 2
        assert r2._release_ts.at(None, r2.release_time) == 1000
        assert r2._release_ts.at(None, r2.release_time - timedelta(seconds=1)) == 1000
        assert r2._release_ts.at(None, r2.release_time + timedelta(seconds=1)) == 1000
        assert r2._release_ts.at(None, r2.release_time + timedelta(seconds=2)) == 1000
        assert np.all(r2._release_ts.data == np.linspace(1000,1000, len(r2._release_ts.data)))
        assert r2._mass_per_le == 0
        assert len(r2._pos_ts.time) == 2

        r3.prepare_for_model_run(900)
        assert len(r3._release_ts.data) == 11
        assert r3._release_ts.at(None, r3.release_time) == 0
        assert r3._release_ts.at(None, r3.end_release_time) == 1000
        assert np.all(r3._release_ts.data == np.linspace(0,1000, len(r3._release_ts.data)))
        assert len(r3._pos_ts.time) == 11
        assert np.all(r1._pos_ts.at(None, r3.release_time + timedelta(seconds=900)*5) == np.array([(5.,15.,25.)]))

#     @pytest.mark.parametrize('r', [r1, r3])
#     def test_num_elements_after_time(self, r):
#
#         #not _prepared yet so it should return 0 for anything
#         assert r.num_elements_after_time(r.end_release_time, 0) == 0
#         assert r.num_elements_after_time(r.release_time, 900) == 0
#
#         r.prepare_for_model_run(900)
#         assert r.num_elements_after_time(r.release_time, 0) == 0
#         assert r.num_elements_after_time(r.release_time, 150) == int(r._release_ts.data[1] * 150./900)
#         assert r.num_elements_after_time(r.end_release_time, 10) == r._release_ts.data[-1]
#
#         assert r.num_elements_after_time(r.release_time - timedelta(seconds=450), 900) == int(r._release_ts.data[1]/2)
    def test_rewind(self, r1):
        r1.prepare_for_model_run(900)
        assert r1._prepared == True
        assert r1._release_ts is not None
        r1.rewind()
        assert r1._prepared == False
        assert r1._release_ts is None

    def test__eq__(self, r1, r2):
        assert r1 != r2
        assert r1 == r1

    def test_serialization(self, r1):
        ser = r1.serialize()
        deser = PointLineRelease.deserialize(ser)
        assert deser == r1

        r1.prepare_for_model_run(900)
        ser = r1.serialize()
        deser = PointLineRelease.deserialize(ser)
        assert deser == r1

    #This isn't supported yet in pytest????
    #@pytest.mark.parametrize('r', [r1, r3])
    def test_LE_initialization(self, r1, r3):
        for r in [r1, r3]:
            #initialize_LEs(self, to_rel, data, current_time, time_step)
            data = LEData()
            ts = 900
            r.prepare_for_model_run(ts)
            data.prepare_for_model_run(r.array_types, None)
            data.extend_data_arrays(10)
            #initialize over the time interval 0-10%
            r.initialize_LEs(10, data, r.release_time, ts)

            #particles should have positions spread over 0-10% (frac) of the
            #line from start_position to end_position
            assert len(data['positions']) == 10
            for pos in data['positions']:
                for d in [0,1,2]:
                    assert pos[d] >= r.start_position[d]
                    #only 1 time step out of 10, so particles should only be on 10% of the line
                    assert pos[d] <= r.start_position[d] + (r.end_position[d] - r.start_position[d]) / 10

            assert np.all(data['mass'] == r._mass_per_le)

            #reset and try overlap beginning
            data.rewind()
            data.prepare_for_model_run(r.array_types, None)
            data.extend_data_arrays(100)
            #initialize 100 LEs overlapping the start of the release
            r.initialize_LEs(100, data, r.release_time - timedelta(seconds=ts/2), ts)
            for pos in data['positions']:
                for d in [0,1,2]:
                    assert pos[d] >= r.start_position[d]
                    #only 1/2 time step out of 10, so particles should only be on 5% of the line
                    assert pos[d] <= r.start_position[d] + (r.end_position[d] - r.start_position[d]) / 20

            assert np.all(data['mass'] == r._mass_per_le)

            data.extend_data_arrays(900)
            #Should be fine initializing over a longer or shorter time interval than was prepared with
            r.initialize_LEs(1000, data, r.release_time - timedelta(seconds=ts/2), 10000)
            for pos in data['positions']:
                for d in [0,1,2]:
                    assert pos[d] >= r.start_position[d]
                    assert pos[d] <= r.end_position[d]
            assert data['mass'].sum() == 5000

            data.rewind()
            data.prepare_for_model_run(r.array_types, None)
            data.extend_data_arrays(100)
            r.initialize_LEs(100, data, r.release_time + timedelta(seconds=ts/4), 225)
            for pos in data['positions']:
                for d in [0,1,2]:
                    assert pos[d] >= r._pos_ts.at(None, r.release_time + timedelta(seconds=ts/4))[d]
                    assert pos[d] <= r._pos_ts.at(None, r.release_time + timedelta(seconds=ts/2))[d]


def test_release_from_splot_data():
    '''
    test release_from_splot_data by creating file with fake data
    '''
    test_data = \
        ('-7.885776000000000E+01    4.280546000000000E+01   4.4909252E+01\n'
         '-7.885776000000000E+01    4.279556000000000E+01   4.4909252E+01\n'
         '-8.324346000000000E+01    4.196396000000001E+01   3.0546749E+01\n')
    here = os.path.dirname(__file__)
    td_file = os.path.join(here, 'test_data.txt')
    with open(td_file, 'w') as td:
        td.write(test_data)

    exp = np.asarray((44.909252, 44.909252, 30.546749),
                     dtype=int)
    exp_num_elems = exp.sum()
    rel = release_from_splot_data(datetime(2015, 1, 1), td_file)
    assert rel.num_elements == exp_num_elems
    assert len(rel.start_position) == exp_num_elems
    cumsum = np.cumsum(exp)
    for ix in range(len(cumsum) - 1):
        assert np.all(rel.start_position[cumsum[ix]] ==
                      rel.start_position[cumsum[ix]:cumsum[ix + 1]])
    assert np.all(rel.start_position[0] == rel.start_position[:cumsum[0]])

    os.remove(td_file)

