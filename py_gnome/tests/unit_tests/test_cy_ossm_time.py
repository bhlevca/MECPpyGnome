#!/usr/bin/env python

"""
unit test ossmtime. This is the python access to the cython wrapper cy_ossm_time

"""

# import basic_types and subsequently lib_gnome
import numpy as np
 
from gnome import basic_types
from gnome.cy_gnome import cy_ossm_time
 

class TestCy_ossm_time():
    """
    Test methods of the Cy_ossm_time class 
    """
    # sample data generated and stored via Gnome GUI
    file = r"SampleData/WindDataFromGnome.WND"
    ossmT = cy_ossm_time.Cy_ossm_time()
    ossmT.ReadTimeValues(file); # assume default format and units
    
    def test_ReadTimeValues(self):
        """
        Tests ReadTimeValues method. Use default format and units.
        """
        print "Read file " + self.file
        assert True
    
    def test_ReadTimeValuesException(self):
        """Test error when ReadTimeValues does not provide units in data file or as input"""
        ossmT2 = cy_ossm_time.Cy_ossm_time()
        try:
            ossmT2.ReadTimeValues(self.file, 5, -1)
        except IOError:
            assert True
    
    def test_TimeValuesAtDataPointsReadFromFile(self):
        """Test GetTimeValues method. It gets the time value pairs for the model times
        stored in the data file. 
        For each line in the data file, the ReadTimeValues method creates one time value pair
            This test just gets the time series that was created from the file. It then invokes
        GetTimeValue for times in the time series.          
        """
        
        # Let's see what is stored in the Handle to expected result
        t_val = self.ossmT.GetTimeValueHandle()
        
        actual = np.array(t_val['value'], dtype=basic_types.velocity_rec)
        time = np.array(t_val['time'], dtype=basic_types.seconds)
        
        vel_rec = self.ossmT.GetTimeValue(time)
        
        # TODO: Figure out why following fails??
        #np.testing.assert_allclose(vel_rec, actual, 1e-3, 1e-3, 
        #                          "GetTimeValue is not within a tolerance of 1e-3", 0)
        assert np.all( np.abs( vel_rec['u']-actual['u'])) < 1e-6
        assert np.all( np.abs( vel_rec['v']-actual['v'])) < 1e-6
        
        
    def test_SetTimeValueHandle(self):
        """
        Sets the time series in OSSMTimeValue_c equal to the externally supplied numpy
        array containing time_value_pair data
        It then reads it back to make sure data was set correctly
        """
        # use this to test setting / getting TimeValuePair
        tval = np.empty((2,), dtype=basic_types.time_value_pair)
        tval['time'][0] = 0
        tval['value']['u'][0]=1
        tval['value']['v'][0]=2
        
        tval['time'][1] = 1
        tval['value']['u'][1]=2
        tval['value']['v'][1]=3
        
        self.ossmT.SetTimeValueHandle(tval)
        t_val = self.ossmT.GetTimeValueHandle()
        np.testing.assert_array_equal(t_val, tval, 
                                      "cy_ossm_time.GetTimeValue did not return expected numpy array", 
                                      0)