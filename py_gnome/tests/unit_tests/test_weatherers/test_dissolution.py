'''
Test dissolution module
'''
from datetime import timedelta

import pytest
import numpy as np

from gnome.environment import constant_wind, Water, Waves
from gnome.outputters import WeatheringOutput
from gnome.spill.elements import floating
from gnome.weatherers import (Evaporation,
                              NaturalDispersion,
                              Dissolution,
                              weatherer_sort)

from conftest import weathering_data_arrays, build_waves_obj
from ..conftest import (sample_model_weathering,
                        sample_model_weathering2)

from pprint import PrettyPrinter
pp = PrettyPrinter(indent=2, width=120)

# also test with lower wind no dispersion
waves = build_waves_obj(15., 'knots', 270, 300.0)
water = waves.water
wind = waves.wind


def test_init():
    'test sort order for Dissolution weatherer'
    wind = constant_wind(15., 0)
    waves = Waves(wind, Water())
    diss = Dissolution(waves)

    print diss.array_types
    assert all([(at in diss.array_types)
                for at in ('mass', 'viscosity', 'density')])


def test_sort_order():
    'test sort order for Dissolution weatherer'
    wind = constant_wind(15., 0)
    waves = Waves(wind, Water())
    diss = Dissolution(waves)

    assert weatherer_sort(diss) == 8


def test_serialize_deseriailize():
    'test serialize/deserialize for webapi'
    wind = constant_wind(15., 0)
    water = Water()
    waves = Waves(wind, water)

    diss = Dissolution(waves)
    json_ = diss.serialize()
    pp.pprint(json_)

    assert json_['waves'] == waves.serialize()

    # deserialize and ensure the dict's are correct
    d_ = Dissolution.deserialize(json_)
    assert d_['waves'] == Waves.deserialize(json_['waves'])

    d_['waves'] = waves
    diss.update_from_dict(d_)

    assert diss.waves is waves


def test_prepare_for_model_run():
    'test sort order for Dissolution weatherer'
    et = floating(substance='ABU SAFAH')
    diss = Dissolution(waves)

    (sc, time_step) = weathering_data_arrays(diss.array_types,
                                             water,
                                             element_type=et)[:2]

    assert 'partition_coeff' in sc.data_arrays
    assert 'dissolution' not in sc.mass_balance

    diss.prepare_for_model_run(sc)

    assert 'dissolution' in sc.mass_balance


@pytest.mark.xfail
@pytest.mark.parametrize(('oil', 'temp', 'num_elems', 'k_ow', 'on'),
                         [('ABU SAFAH', 311.15, 3, 9.36058900e+15, True),
                          ('ALGERIAN BLEND', 311.15, 3, 50291442.58679, True),
                          ('ALASKA NORTH SLOPE (MIDDLE PIPELINE)',
                           311.15, 3, 0.0, False)])
def test_dissolution_k_ow(oil, temp, num_elems, k_ow, on):
    '''
        Here we are testing that the molar averaged oil/water partition
        coefficient (K_ow) is getting calculated with reasonable values
    '''
    et = floating(substance=oil)
    diss = Dissolution(waves)
    (sc, time_step) = weathering_data_arrays(diss.array_types,
                                             water,
                                             element_type=et,
                                             num_elements=num_elems)[:2]

    print 'num spills:', len(sc.spills)
    print 'spill[0] amount:', sc.spills[0].amount

    model_time = (sc.spills[0].get('release_time') +
                  timedelta(seconds=time_step))

    diss.on = on
    diss.prepare_for_model_run(sc)
    diss.initialize_data(sc, sc.num_released)

    diss.prepare_for_model_step(sc, time_step, model_time)
    diss.weather_elements(sc, time_step, model_time)

    assert all(np.isclose(sc._data_arrays['partition_coeff'], k_ow))


@pytest.mark.xfail
@pytest.mark.parametrize(('oil', 'temp', 'num_elems', 'drop_size', 'on'),
                         [('ABU SAFAH', 311.15, 3,
                           [235.41e-6, 230.34e-6, 225.30e-6],
                           True),
                          ('BAHIA', 311.15, 3,
                           [231.19e-6, 225.09e-6, 219.21e-6],
                           True),
                          ('ALASKA NORTH SLOPE (MIDDLE PIPELINE)', 311.15, 3,
                           [0.0, 0.0, 0.0],
                           False)])
def test_dissolution_droplet_size(oil, temp, num_elems, drop_size, on):
    '''
        Here we are testing that the molar averaged oil/water partition
        coefficient (K_ow) is getting calculated with reasonable values
    '''
    et = floating(substance=oil)

    disp = NaturalDispersion(waves, water)
    diss = Dissolution(waves)

    (sc, time_step) = weathering_data_arrays(diss.array_types,
                                             water,
                                             element_type=et,
                                             num_elements=num_elems)[:2]

    print 'num spills:', len(sc.spills)
    print 'spill[0] amount:', sc.spills[0].amount, sc.spills[0].units

    model_time = (sc.spills[0]
                  .get('release_time') + timedelta(seconds=time_step))
    print 'model_time = ', model_time
    print 'time_step = ', time_step

    disp.on = on
    diss.on = on

    disp.prepare_for_model_run(sc)
    diss.prepare_for_model_run(sc)

    disp.initialize_data(sc, sc.num_released)
    diss.initialize_data(sc, sc.num_released)

    for i in range(3):
        disp.prepare_for_model_step(sc, time_step, model_time)
        diss.prepare_for_model_step(sc, time_step, model_time)

        disp.weather_elements(sc, time_step, model_time)
        diss.weather_elements(sc, time_step, model_time)

        print 'droplet_avg_size:', sc._data_arrays['droplet_avg_size']
        assert np.allclose(sc._data_arrays['droplet_avg_size'], drop_size[i])


mb_param_names = ('oil', 'temp', 'wind_speed',
                  'num_elems', 'expected_mb', 'on')
mb_params = [
             ('ALASKA NORTH SLOPE (MIDDLE PIPELINE)', 311.15, 15.,
              3, np.nan, False),
             ('ABU SAFAH', 288.15, 10., 3, 2.35278e-4, True),
             ('ABU SAFAH', 288.15, 15., 3, 4.557256e-4, True),
             ('ABU SAFAH', 288.15, 20., 3, 7.8214436e-4, True),
             # wind speed trends
             ('BAHIA',     288.15,  5., 3, 2.78469e-4, True),
             ('BAHIA',     288.15, 10., 3, 5.94589e-4, True),
             ('BAHIA',     288.15, 15., 3, 1.0844379e-3, True),
             ('BAHIA',     288.15, 20., 3, 1.842449e-3, True),
             # temperature trends
             ('BAHIA',     273.15, 15., 3, 7.80423e-4, True),
             ('BAHIA',     283.15, 15., 3, 1.009034e-3, True),
             ('BAHIA',     293.15, 15., 3, 1.147214e-3, True),
             ('BAHIA',     303.15, 15., 3, 1.24948e-3, True),
             ]


@pytest.mark.xfail
@pytest.mark.parametrize(mb_param_names, mb_params)
def test_dissolution_mass_balance(oil, temp, wind_speed,
                                  num_elems, expected_mb, on):
    '''
    Test a single dissolution step.
    - for this, we need a dispersion weatherer to give us a droplet size
      distribution.
    Fuel Oil #6 does not exist...
    '''
    et = floating(substance=oil)

    waves = build_waves_obj(wind_speed, 'knots', 270, temp)
    water = waves.water

    disp = NaturalDispersion(waves, water)
    diss = Dissolution(waves)

    all_array_types = diss.array_types.union(disp.array_types)

    (sc, time_step) = weathering_data_arrays(all_array_types,
                                             water,
                                             element_type=et,
                                             num_elements=num_elems,
                                             units='kg',
                                             amount_per_element=1.0
                                             )[:2]

    print 'time_step: {}'.format(time_step)
    print 'num spills:', len(sc.spills)
    print 'spill[0] amount: {} {}'.format(sc.spills[0].amount,
                                          sc.spills[0].units)
    print 'temperature = ', temp
    print 'wind = ',
    print '\n'.join(['\t{} {}'.format(ts[1][0], waves.wind.units)
                     for ts in waves.wind.timeseries])
    print

    initial_amount = sc.spills[0].amount
    model_time = (sc.spills[0].get('release_time') +
                  timedelta(seconds=time_step))

    disp.on = on
    disp.prepare_for_model_run(sc)
    disp.initialize_data(sc, sc.num_released)

    diss.on = on
    diss.prepare_for_model_run(sc)
    diss.initialize_data(sc, sc.num_released)

    disp.prepare_for_model_step(sc, time_step, model_time)
    diss.prepare_for_model_step(sc, time_step, model_time)

    disp.weather_elements(sc, time_step, model_time)
    diss.weather_elements(sc, time_step, model_time)

    if on:
        print ('fraction dissolved: {}'
               .format(sc.mass_balance['dissolution'] / initial_amount)
               )
        print ('fraction dissolved: {:.2%}'
               .format(sc.mass_balance['dissolution'] / initial_amount)
               )
        print sc.mass_balance['dissolution'], expected_mb
        assert np.isclose(sc.mass_balance['dissolution'], expected_mb)
    else:
        assert 'dissolution' not in sc.mass_balance

    # Here we stop the test to check on wind speed trends
    # if oil == 'BAHIA' and temp == 288.15:
    #     assert False

    # Here we stop the test to check on temperature trends
    # if oil == 'BAHIA' and wind_speed == 15.0:
    #     assert False


@pytest.mark.parametrize(('oil', 'temp', 'expected_balance'),
                         [('ABU SAFAH', 288.7, 93.0136),
                          ('ALASKA NORTH SLOPE (MIDDLE PIPELINE)', 288.7,
                           42.979),
                          ('BAHIA', 288.7, 94.9979),
                          ('ALASKA NORTH SLOPE, OIL & GAS', 279.261,
                           167.409),
                          ]
                         )
@pytest.mark.xfail
def test_full_run(sample_model_fcn2, oil, temp, expected_balance):
    '''
    test dissolution outputs post step for a full run of model. Dump json
    for 'weathering_model.json' in dump directory
    '''
    model = sample_model_weathering2(sample_model_fcn2, oil, temp)
    model.environment += [Water(temp), wind,  waves]
    model.weatherers += Evaporation()
    model.weatherers += NaturalDispersion()
    model.weatherers += Dissolution(waves)

    for sc in model.spills.items():
        print sc.__dict__.keys()
        print sc._data_arrays

        print 'num spills:', len(sc.spills)
        print 'spill[0] amount:', sc.spills[0].amount
        original_amount = sc.spills[0].amount

    # set make_default_refs to True for objects contained in model after adding
    # objects to the model
    model.set_make_default_refs(True)
    model.setup_model_run()

    dissolved = []
    for step in model:
        for sc in model.spills.items():
            if step['step_num'] > 0:
                assert (sc.mass_balance['dissolution'] > 0)
                assert (sc.mass_balance['natural_dispersion'] > 0)
                assert (sc.mass_balance['sedimentation'] > 0)

            dissolved.append(sc.mass_balance['dissolution'])

            # print ("\nDissolved: {0}".
            #        format(sc.mass_balance['dissolution']))
            # print ("Mass: {0}".
            #        format(sc._data_arrays['mass']))
            # print ("Mass Components: {0}".
            #        format(sc._data_arrays['mass_components']))

    print ('Fraction dissolved after full run: {}'
           .format(dissolved[-1] / original_amount))

    assert dissolved[0] == 0.0
    assert np.isclose(dissolved[-1], expected_balance)


@pytest.mark.parametrize(('oil', 'temp', 'expected_balance'),
                         # [(_sample_oils['benzene'], 288.7, 2.98716)
                         [('benzene', 288.7, 9729.56707)
                          ]
                         )
def test_full_run_no_evap(sample_model_fcn2, oil, temp, expected_balance):
    '''
    test dissolution outputs post step for a full run of model. Dump json
    for 'weathering_model.json' in dump directory
    '''
    low_wind = constant_wind(1., 270, 'knots')
    low_waves = Waves(low_wind, Water(temp))
    model = sample_model_weathering2(sample_model_fcn2, oil, temp)
    model.environment += [Water(temp), low_wind,  low_waves]
    # model.weatherers += Evaporation(Water(temp), low_wind)
    model.weatherers += NaturalDispersion(low_waves, Water(temp))
    model.weatherers += Dissolution(low_waves)

    for sc in model.spills.items():
        print sc.__dict__.keys()
        print sc._data_arrays

        print 'num spills:', len(sc.spills)
        print 'spill[0] amount:', sc.spills[0].amount
        original_amount = sc.spills[0].amount

    # set make_default_refs to True for objects contained in model after adding
    # objects to the model
    model.set_make_default_refs(True)
    model.setup_model_run()

    dissolved = []
    for step in model:
        for sc in model.spills.items():
            if step['step_num'] > 0:
                assert (sc.mass_balance['dissolution'] > 0)
                assert (sc.mass_balance['natural_dispersion'] > 0)
                assert (sc.mass_balance['sedimentation'] > 0)

            dissolved.append(sc.mass_balance['dissolution'])

            print ("\nDissolved: {0}".
                   format(sc.mass_balance['dissolution']))
            print ("Mass: {0}".
                   format(sc._data_arrays['mass']))
            print ("Mass Components: {0}".
                   format(sc._data_arrays['mass_components']))

    print ('Fraction dissolved after full run: {}'
           .format(dissolved[-1] / original_amount))

    assert dissolved[0] == 0.0
    assert np.isclose(dissolved[-1], expected_balance)


def test_full_run_dissolution_not_active(sample_model_fcn):
    'no water/wind/waves object and no evaporation'
    model = sample_model_weathering(sample_model_fcn, 'oil_6')
    model.environment += [Water(288.7), wind,  waves]
    model.weatherers += Evaporation()
    model.weatherers += NaturalDispersion()
    model.weatherers += Dissolution(waves=waves, on=False)

    model.outputters += WeatheringOutput()
    for step in model:
        '''
        if no weatherers, then no weathering output - need to add on/off
        switch to WeatheringOutput
        '''
        assert 'dissolution' not in step['WeatheringOutput']
        assert ('time_stamp' in step['WeatheringOutput'])
        print ("Completed step: {0}".format(step['step_num']))
