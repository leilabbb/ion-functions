#!/usr/bin/env python
"""
@package ion_functions.test.test_fdc_functions
@file ion_functions/test/test_fdc_functions.py
@author Russell Desiderio
@brief Unit tests for fdc_functions module
"""

from nose.plugins.attrib import attr
from ion_functions.test.base_test import BaseUnitTestCase

import numpy as np
from ion_functions.data import fdc_functions as fd
import os
#from ion_functions.utils import fill_value


@attr('UNIT', group='func')
class TestFdcFunctionsUnit(BaseUnitTestCase):

    def setUp(self):
        # fdchp operates on datasets of 12000 records; some of the datasets may have
        # slightly less than that (if so, pad to 12000) or more than that (if so,
        # delete overage). also, there are 2 slightly different processing lines
        # depending on the quality of the compass (heading) data, as signified by
        # the program's calculated goodcompass variable. both lines will be checked.

        # test values are generated by the test code that Jim Edson e-mailed (newer
        # version than in the original DPS); for screen diagnostics, increase
        # printout precision.
        np.set_printoptions(precision=16)
        # note also that the matlab and python code will not agree to 16 places because
        # the matlab function filtfilt and the scipy function filtfilt agree to at best
        # 12 places and at worst (when ahi2 and bhi2 filter used when goodcompass=1)
        # about 5 places.

        # 10 hz data
        self.daqrate = 10
        # number of seconds from each end of dataset to truncate after processing
        self.chop = 30

        # test data e-mailed by Jim Edson:
        # read in the input L0 test data ...
        file = os.path.join(os.getcwd(), 'ion_functions/data/matlab_scripts/fdchp/fdchp_test_dp.dat')
        with open(file, 'r') as f:
            lines = f.readlines()

        # ... parse it into a test data array (inputs) for further use
        data = []
        for ii in lines:
            data.append((ii.strip().split(",")))

        # dataset template
        inputs = np.array(data, dtype=float)
        # add timestamps
        npts = inputs.shape[0]
        self.time0 = 400000.0
        timestamps = self.time0 + np.arange(1.0, npts + 1) / self.daqrate  # 10 Hz data
        timestamps.shape = (npts, 1)
        # and latitudes
        lat = np.copy(timestamps)
        lat[:] = 38.5
        inputs = np.hstack((timestamps, inputs, lat))

        ### construct 3 single test datasets complete with unique timestamps,
        ### plus one dataset made by concatenating the 3 single datasets.

        # first dataset, as read in; more than 12000 pts (npts = 12009).
        # for this set, goodcompass calculates to 0.
        self.testset_01 = np.copy(inputs)

        # second dataset, make with less than 12000 pts, with wind_z data flipped:
        # for this set, goodcompass also calculates to 0.
        self.testset_02 = np.copy(inputs[0:11985, :])
        self.testset_02[:, 3] = np.flipud(self.testset_02[:, 3])
        # set timestamps ahead 1 hr
        self.testset_02[:, 0] = self.testset_02[:, 0] + 3600.0
        # re-set latitudes
        self.testset_02[:, -1] = -11.8

        # third dataset, goodcompass calculates to 1; 12000 points.
        piece = np.copy(inputs[4000:8000, :])
        self.testset_03 = np.tile(piece, (3, 1))
        # set timestamps ahead of first dataset by 2 hrs
        self.testset_03[:, 0] = self.testset_01[0:12000, 0] + 7200.0
        # re-set latitudes
        self.testset_03[:, -1] = -76.1

        ### construct 1 multiple testset.
        self.testset_04 = np.vstack((self.testset_01, self.testset_02, self.testset_03))

        # tuple of the 4 datasets
        self.Ldata = (self.testset_01, self.testset_02, self.testset_03, self.testset_04)

    def test_datasets(self):
        # this routine tests:
        #     dataset input into setup
        #     the function fdc_quantize_data
        #     the flux calculations of function fdc_flux_and_wind

        # expected values were calculated using matlab test code for a cutoff frequency
        # of 1/12.0
        # the first row are the uw, vw, wT flux values for the 1st dataset, etc.
        xpctd_fluxes = np.array([[-0.350371566926, 0.115496951668, -0.008274161328],
                                 [-0.410571629711, 0.092164914869, -0.006687641111],
                                 [-0.080418722438, -0.001432879153, -0.004455583513]])

        # the agreement is good for datasets 1 and 2, not so good for 3 because when
        # goodcompass calculates to 1 (True), filtfilt is executed with the ahi2 and
        # bhi2 filter coeffs, the matlab v. scipy results of which barely agree (the
        # calculation is not robust).
        reltol = np.array([1.e-9, 1.e-9, 0.0, 0.0])
        abstol = np.array([0.0, 0.0, 1.e-5, 1.e-5])

        ### NOTE that the variables parsed out from 'array' are not column vectors;
        ### they are python 1D arrays which is what these DPAs expect from CI.
        for ii in range(4):
            array = np.copy(self.Ldata[ii])
            timestamps = array[:, 0]
            windX = array[:, 1]
            windY = array[:, 2]
            windZ = array[:, 3]
            sound = array[:, 4]    # (temperature proxy)
            rateX = array[:, 5]
            rateY = array[:, 6]
            rateZ = array[:, 7]
            accelX = array[:, 8]
            accelY = array[:, 9]
            accelZ = array[:, 10]
            roll = array[:, 11]    # (not used by DPA)
            pitch = array[:, 12]   # (not used by DPA)
            heading = array[:, 13]
            lat = array[:, 14]

            if ii < 3:  # single datasets
                calc_fluxes, _ = fd.fdc_flux_and_wind(timestamps,
                                                      windX, windY, windZ,
                                                      sound, heading,
                                                      rateX, rateY, rateZ,
                                                      accelX, accelY, accelZ, lat)
                calc_fluxes = np.asarray(calc_fluxes).flatten()
                np.testing.assert_allclose(calc_fluxes, xpctd_fluxes[ii, :],
                                           rtol=reltol[ii], atol=abstol[ii])

            if ii == 3:  # multiple
                calc_fluxes, _ = fd.fdc_flux_and_wind(timestamps,
                                                      windX, windY, windZ,
                                                      sound, heading,
                                                      rateX, rateY, rateZ,
                                                      accelX, accelY, accelZ, lat)
                calc_fluxes = np.asarray(calc_fluxes).transpose()
                np.testing.assert_allclose(calc_fluxes, xpctd_fluxes,
                                           rtol=reltol[ii], atol=abstol[ii])

    def test_L2_products(self):
        # this routine tests the individual functions:
        #     fdc_fluxmom_alongwind
        #     fdc_fluxmom_crosswind
        #     fdc_fluxhot
        #     fdc_time_L2

        # as before, each row contains flux values for a given dataset.
        # the column values are uw, vw, wT (fluxmom_alongwind, fluxmom_crosswind, fluxhot)
        xpctd_fluxes = np.array([[-0.350371566926, 0.115496951668, -0.008274161328],
                                 [-0.410571629711, 0.092164914869, -0.006687641111],
                                 [-0.080418722438, -0.001432879153, -0.004455583513]])

        # the agreement is good for datasets 1 and 2, not so good for 3 because when
        # goodcompass calculates to 1 (True), filtfilt is executed with the ahi2 and
        # bhi2 filter coeffs, the matlab v. scipy results of which barely agree (the
        # calculation is not robust).
        reltol = np.array([1.e-9, 1.e-9, 0.0, 0.0])
        abstol = np.array([0.0, 0.0, 1.e-5, 1.e-5])

        xpctd_stamps = self.time0 + np.array([600.0, 4200.0, 7800.0])

        for ii in range(4):
            array = np.copy(self.Ldata[ii])
            timestamps = array[:, 0]
            windX = array[:, 1]
            windY = array[:, 2]
            windZ = array[:, 3]
            sound = array[:, 4]    # (temperature proxy)
            rateX = array[:, 5]
            rateY = array[:, 6]
            rateZ = array[:, 7]
            accelX = array[:, 8]
            accelY = array[:, 9]
            accelZ = array[:, 10]
            roll = array[:, 11]    # (not used by DPA)
            pitch = array[:, 12]   # (not used by DPA)
            heading = array[:, 13]
            lat = array[:, 14]

            if ii < 3:  # single datasets
                calc_flux = fd.fdc_fluxmom_alongwind(timestamps,
                                                     windX, windY, windZ,
                                                     heading,
                                                     rateX, rateY, rateZ,
                                                     accelX, accelY, accelZ, lat)
                np.testing.assert_allclose(calc_flux, xpctd_fluxes[ii, 0],
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_flux = fd.fdc_fluxmom_crosswind(timestamps,
                                                     windX, windY, windZ,
                                                     heading,
                                                     rateX, rateY, rateZ,
                                                     accelX, accelY, accelZ, lat)
                np.testing.assert_allclose(calc_flux, xpctd_fluxes[ii, 1],
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_flux = fd.fdc_fluxhot(timestamps,
                                           windX, windY, windZ,
                                           sound, heading,
                                           rateX, rateY, rateZ,
                                           accelX, accelY, accelZ, lat)
                np.testing.assert_allclose(calc_flux, xpctd_fluxes[ii, 2],
                                           rtol=reltol[ii], atol=abstol[ii])

                L2_timestamp = fd.fdc_time_L2(timestamps)
                np.testing.assert_array_equal(L2_timestamp, xpctd_stamps[ii])

            if ii == 3:  # multiple
                calc_flux = fd.fdc_fluxmom_alongwind(timestamps,
                                                     windX, windY, windZ,
                                                     heading,
                                                     rateX, rateY, rateZ,
                                                     accelX, accelY, accelZ, lat)

                np.testing.assert_allclose(calc_flux, xpctd_fluxes[:, 0],
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_flux = fd.fdc_fluxmom_crosswind(timestamps,
                                                     windX, windY, windZ,
                                                     heading,
                                                     rateX, rateY, rateZ,
                                                     accelX, accelY, accelZ, lat)
                np.testing.assert_allclose(calc_flux, xpctd_fluxes[:, 1],
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_flux = fd.fdc_fluxhot(timestamps,
                                           windX, windY, windZ,
                                           sound, heading,
                                           rateX, rateY, rateZ,
                                           accelX, accelY, accelZ, lat)
                np.testing.assert_allclose(calc_flux, xpctd_fluxes[:, 2],
                                           rtol=reltol[ii], atol=abstol[ii])

                L2_timestamp = fd.fdc_time_L2(timestamps)
                np.testing.assert_array_equal(L2_timestamp, xpctd_stamps)

    def test_L1time_and_temperature(self):
        # this routine tests the individual functions:
        #     fdc_time_L1
        #     fdc_tmpatur

        # number of array values to truncate on either side
        edge = self.daqrate * self.chop
        # however, the test sets do not necessarily start out with 12000 points - so:
        idx = range(edge, 12000-edge)

        # step through each single dataset to test functions;
        # also, accumulate single dataset products for multiple dataset test:
        tmpatur_mult = np.array([])
        L1_time_mult = np.array([])
        for ii in range(4):
            array = np.copy(self.Ldata[ii])
            timestamps = array[:, 0]
            sound = array[:, 4]  # (temperature proxy)
            sonic = sound / 100.0
            sonic = sonic * sonic / 403.0 - 273.15

            if ii < 3:  # single datasets
                tmpatur = fd.fdc_tmpatur(timestamps, sound)
                np.testing.assert_allclose(tmpatur, sonic[idx],
                                           rtol=1.e-12, atol=1.e-12)
                tmpatur_mult = np.hstack((tmpatur_mult, sonic[idx]))

                L1_timestamp = fd.fdc_time_L1(timestamps)
                np.testing.assert_array_equal(L1_timestamp, timestamps[idx])
                L1_time_mult = np.hstack((L1_time_mult, timestamps[idx]))

            if ii == 3:  # multiple
                tmpatur = fd.fdc_tmpatur(timestamps, sound)
                np.testing.assert_allclose(tmpatur, tmpatur_mult,
                                           rtol=1.e-12, atol=1.e-12)

                L1_timestamp = fd.fdc_time_L1(timestamps)
                np.testing.assert_array_equal(L1_timestamp, L1_time_mult)

    def test_L1wind(self):
        # this routine tests the individual functions:
        #     fdc_windtur_north
        #     fdc_windtur_west
        #     fdc_windtur_up

        # each of these products consists of 12000-2*300 = 11400 values per dataset!
        # so does tmpatur, but the calculation of the wind products is infinitely
        # more involved. therefore, characterize each of these wind product sets
        # by their mean and standard deviation, and compare to those values obtained
        # from the matlab test code.

        # rows are datasets, columns are (   mean         ,  stdev using 1/N)
        xpctd_stats_north = np.array([[-0.5011625586110554, 3.9363550354343246],
                                      [-0.4476709809886175, 3.8835916776201431],
                                      [4.6820432803193492,  1.2040569153455141]])

        xpctd_stats_west = np.array([[-5.5593736503555240, 3.4844006495394644],
                                    [-5.6032333201070035, 3.4709487063782660],
                                    [8.4280772593666438, 0.6964796732544405]])

        xpctd_stats_up = np.array([[0.5509162872369869, 0.4191059753708253],
                                   [0.5507316402911087, 0.6151446249615381],
                                   [0.8315342390443983, 0.3083012703149161]])

        # the agreement is good for datasets 1 and 2, not so good for 3 because when
        # goodcompass calculates to 1 (True), filtfilt is executed with the ahi2 and
        # bhi2 filter coeffs, the matlab v. scipy results of which barely agree (the
        # calculation is not robust).
        #
        # the expected values for dataset 4 are calculated from the accumulated python
        # products (not from the matlab code), so the expected and calculated values
        # should almost exactly match.
        reltol = np.array([1.e-9, 1.e-9, 0.0, 1.e-16])
        abstol = np.array([0.0, 0.0, 1.e-3, 0.0])

        # step through each single dataset to test functions;
        # also, accumulate single dataset products for multiple dataset test:
        windnorth_mult = np.array([])
        windwest_mult = np.array([])
        windup_mult = np.array([])
        for ii in range(4):
            array = np.copy(self.Ldata[ii])
            timestamps = array[:, 0]
            windX = array[:, 1]
            windY = array[:, 2]
            windZ = array[:, 3]
            sound = array[:, 4]    # (temperature proxy)
            rateX = array[:, 5]
            rateY = array[:, 6]
            rateZ = array[:, 7]
            accelX = array[:, 8]
            accelY = array[:, 9]
            accelZ = array[:, 10]
            roll = array[:, 11]    # (not used by DPA)
            pitch = array[:, 12]   # (not used by DPA)
            heading = array[:, 13]
            lat = array[:, 14]

            if ii < 3:  # single datasets
                calc_wind = fd.fdc_windtur_north(timestamps,
                                                 windX, windY, windZ,
                                                 heading,
                                                 rateX, rateY, rateZ,
                                                 accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                np.testing.assert_allclose(calc_stats, xpctd_stats_north[ii, :],
                                           rtol=reltol[ii], atol=abstol[ii])
                windnorth_mult = np.hstack((windnorth_mult, calc_wind))

                calc_wind = fd.fdc_windtur_west(timestamps,
                                                windX, windY, windZ,
                                                heading,
                                                rateX, rateY, rateZ,
                                                accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                np.testing.assert_allclose(calc_stats, xpctd_stats_west[ii, :],
                                           rtol=reltol[ii], atol=abstol[ii])
                windwest_mult = np.hstack((windwest_mult, calc_wind))

                calc_wind = fd.fdc_windtur_up(timestamps,
                                              windX, windY, windZ,
                                              heading,
                                              rateX, rateY, rateZ,
                                              accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                np.testing.assert_allclose(calc_stats, xpctd_stats_up[ii, :],
                                           rtol=reltol[ii], atol=abstol[ii])
                windup_mult = np.hstack((windup_mult, calc_wind))

            if ii == 3:  # multiple
                calc_wind = fd.fdc_windtur_north(timestamps,
                                                 windX, windY, windZ,
                                                 heading,
                                                 rateX, rateY, rateZ,
                                                 accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                xpctd_stats = np.array([np.mean(windnorth_mult), np.std(windnorth_mult, ddof=0)])

                np.testing.assert_allclose(calc_stats, xpctd_stats,
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_wind = fd.fdc_windtur_west(timestamps,
                                                windX, windY, windZ,
                                                heading,
                                                rateX, rateY, rateZ,
                                                accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                xpctd_stats = np.array([np.mean(windwest_mult), np.std(windwest_mult, ddof=0)])

                np.testing.assert_allclose(calc_stats, xpctd_stats,
                                           rtol=reltol[ii], atol=abstol[ii])

                calc_wind = fd.fdc_windtur_up(timestamps,
                                              windX, windY, windZ,
                                              heading,
                                              rateX, rateY, rateZ,
                                              accelX, accelY, accelZ, lat)
                calc_stats = np.array([np.mean(calc_wind), np.std(calc_wind, ddof=0)])
                xpctd_stats = np.array([np.mean(windup_mult), np.std(windup_mult, ddof=0)])

                np.testing.assert_allclose(calc_stats, xpctd_stats,
                                           rtol=reltol[ii], atol=abstol[ii])

    def test_extrapolation_fault(self):
        # this routine tests whether nans are output for the flux products, as occurs when
        # running the matlab test code, when the interpolation routine in the despikesimple
        # function encounters an extrapolation case. the original python coding was changed
        # to accommodate this behavior to avoid a series of runtime execution errors.
        for ii in (5, 8):
            array = np.copy(self.Ldata[0])
            array[0, ii] = 99999.9
            timestamps = array[:, 0]
            windX = array[:, 1]
            windY = array[:, 2]
            windZ = array[:, 3]
            sound = array[:, 4]    # (temperature proxy)
            rateX = array[:, 5]
            rateY = array[:, 6]
            rateZ = array[:, 7]
            accelX = array[:, 8]
            accelY = array[:, 9]
            accelZ = array[:, 10]
            roll = array[:, 11]    # (not used by DPA)
            pitch = array[:, 12]   # (not used by DPA)
            heading = array[:, 13]
            lat = array[:, 14]

            calc_fluxes, _ = fd.fdc_flux_and_wind(timestamps,
                                                  windX, windY, windZ,
                                                  sound, heading,
                                                  rateX, rateY, rateZ,
                                                  accelX, accelY, accelZ, lat)
            calc_fluxes = np.asarray(calc_fluxes).flatten()
            np.testing.assert_allclose(calc_fluxes, np.array([np.nan, np.nan, np.nan]))

