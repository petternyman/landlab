#! /usr/env/python
""" deAlmeida_SquareBasin.py

This is a example driver which utilizes the
OverlandFlow class from generate_overland_flow_deAlmeida.py

The driver reads in a square watershed run to steady state using a simple
stream power driver.

It then routes a storm across the square watershed. Storm parameters taken from
Hawk and Eagleson (1992) Poisson parameters for the Denver, CO station.

After the storm, additional time is needed to drain the water from the system.
At the end of the storm, total water depth mass is calculated and compared
against the predicted water mass under steady state conditions. The hydrograph
is plotted and percent error is output.

Written by Jordan M. Adams, April 2016.


"""
from __future__ import print_function

from landlab.components.overland_flow import OverlandFlow
from landlab.io import read_esri_ascii
from matplotlib import pyplot as plt
import os
import time
import numpy as np


# This provides us with an initial time. At the end, it gives us total
# model run time in seconds.
start_time = time.time()

## This is a steady-state landscape generated by simple stream power
## This is a 200 x 200 grid with an outlet at center of the bottom edge.
dem_name ='Square_TestBasin.asc'

## Now we can create and initialize a raster model grid by reading a DEM
## First, this looks for the DEM in the overland_flow folder in Landlab
DATA_FILE = os.path.join(os.path.dirname(__file__), dem_name)

## Now the ASCII is read, assuming that it is standard ESRI format.
(rmg, z) = read_esri_ascii(DATA_FILE)

## Start time 1 second
elapsed_time = 1.0

## Model Run Time in seconds
model_run_time = 216000.0

## Lists for saving data
discharge_at_outlet = []
hydrograph_time_sec = []
hydrograph_time_hrs = []

## Setting initial fields...
rmg['node']['topographic__elevation'] = z
rmg['link']['surface_water__discharge'] = np.zeros(rmg.number_of_links)
rmg['node']['surface_water__depth'] = np.zeros(rmg.number_of_nodes)


## and fixed link boundary conditions...
rmg.set_fixed_link_boundaries_at_grid_edges(True, True, True, True,
                                    fixed_link_value_of='surface_water__discharge')

## Setting the outlet node to OPEN_BOUNDARY
rmg.status_at_node[100] = 1


## Initialize the OverlandFlow() class.
of = OverlandFlow(rmg, use_fixed_links = True, steep_slopes=True)

## Record the start time so we know how long it runs.
start_time = time.time()

## Link to sample at the outlet
link_to_sample = 299

## Storm duration in seconds
storm_duration = 7200.0


## Running the overland flow component.
while elapsed_time < model_run_time:


    ## The storm starts when the model starts. While the elapsed time is less
    ## than the storm duration, we add water to the system as rainfall.
    if elapsed_time < storm_duration:

        of.rainfall_intensity = 4.07222 * (10 ** -7) # Rainfall intensity (m/s)

    ## Then the elapsed time exceeds the storm duration, rainfall ceases.
    else:

        of.rainfall_intensity = 0.0

    ## Generating overland flow based on the deAlmeida solution.
    of.overland_flow()

    ## Append time and discharge to their lists to save data and for plotting.
    hydrograph_time_sec.append(elapsed_time)
    hydrograph_time_hrs.append(round(elapsed_time/3600., 2))
    discharge_at_outlet.append(of.q[link_to_sample])

    ## Add the time step, repeat until elapsed time >= model_run_time
    print(elapsed_time)
    elapsed_time += of.dt

plt.figure(1)
plt.imshow(z.reshape(rmg.shape), origin='left', cmap='pink')
plt.tick_params(axis='both', labelbottom='off', labelleft='off')
cb = plt.colorbar()
cb.set_label('Elevation (m)', rotation=270, labelpad=15)

plt.figure(2)
plt.plot(hydrograph_time_hrs, (np.abs(discharge_at_outlet)*rmg.dx), 'b-')
plt.xlabel('Time (hrs)')
plt.ylabel('Discharge (cms)')
plt.title('Hydrograph')

calc_water_mass = round(np.abs((np.trapz(hydrograph_time_sec, (np.abs(
                    discharge_at_outlet) * rmg.dx)))), 2)
theoretical_water_mass = round(((rmg.number_of_core_nodes * rmg.cellarea) *
                    (4.07222 * (10 ** -7)) * storm_duration), 2)
percent_error = round(((np.abs(calc_water_mass) - theoretical_water_mass) /
                    theoretical_water_mass * 100), 2)

print('\n', 'Total calculated water mass: ', calc_water_mass)
print('\n', 'Theoretical water mass (Q = P * A): ', theoretical_water_mass)
print('\n', 'Percent Error: ', percent_error, ' %')

endtime = time.time()
print('\n', 'Total run time: ', round(endtime - start_time, 2), ' seconds')
