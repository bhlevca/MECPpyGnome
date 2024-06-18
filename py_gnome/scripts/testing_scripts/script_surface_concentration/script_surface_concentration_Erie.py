import os
from datetime import datetime, timedelta

import gnome.scripting as gs
from gnome.utilities.projections import GeoProjection
from netCDF4 import Dataset
from gnome.utilities.distributions import UniformDistribution
from gnome.concentration.concentration_location import ConcentrationLocation
from gnome.movers import RandomMover, PointWindMover


data_folder = r"D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\data\Erie"
nba_file = os.path.join(data_folder,"Lake Erie-shoreline.bna")
current_netcdf_file = os.path.join(data_folder,"Lake Erie-netCDF File.nc")
images_dir = r'D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\Images_Erie'
depth_dfsu_file = os.path.join(data_folder,"2D all.dfsu")

"""
NBA File: D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\data\Erie\Lake Erie-shoreline.bna
Concentration Location: -79.7621575, 42.5153144

Spill - Point Line Release:
    Start Point: -79.76243830876352,  42.51537963667916
    End Point: -79.76243830876352,  42.52537963667916
    Duration: 6 hour
    Amount: 5000 bbl

"""

gs.set_verbose()
start_time = datetime(2024, 5, 22, 13)
mapfile = gs.get_datafile(nba_file)

model = gs.Model(
    start_time=start_time,
    duration=gs.hours(8),
    map=gs.MapFromBNA(mapfile, refloat_halflife=1),
    time_step=gs.minutes(1)
)


#model.concentration = ConcentrationLocation(locations=[[-79.7621575, 42.5153144,0]])
model.concentration = ConcentrationLocation(locations=[[-83.14, 42.03,0]])
#model.concentration = ConcentrationLocation(locations=[[-79.78065, 42.4786,0]])

current_mover = gs.PyCurrentMover.from_netCDF(current_netcdf_file)
model.movers += current_mover
model.movers += RandomMover(diffusion_coef=200000, uncertain_factor=2)
wind = gs.constant_wind(10, 0, 'm/s')
model.movers += gs.PointWindMover(wind)


ud = UniformDistribution(1,1)

# spill = gs.subsurface_spill(
#     num_elements=1000, 
#     start_position=(-79.76243830876352,  42.51537963667916, 0),
#     release_time=start_time,
#     end_release_time=start_time + gs.hours(3),
#     distribution=ud,
#     distribution_type='rise_velocity',
#     amount=5000,
#     units='bbl',
#     windage_range=(0.01, 0.02),
#     windage_persist=-1,
#     name='My spill'
# )

spill = gs.surface_point_line_spill(
    num_elements=1000,
    start_position=(-83.13832816,  42.061844, 0),
    release_time=start_time,
    end_position=(-83.13832816,  42.061844, 0),
    end_release_time=start_time + gs.hours(10),
    amount=100,
    units='m³',
    windage_range=(0.01, 0.02),
    windage_persist=-1,
    name='My spill'
)
model.spills += spill


gs.make_images_dir(images_dir=images_dir)

map_bounds = ((-83.25, 41.9), (-83.25, 42.1), (-83, 42.1), (-83, 41.9))

renderer = gs.Renderer(
    map_filename=mapfile,
    output_timestep=timedelta(minutes=30),
    output_dir=images_dir,
    draw_map_bounds=True,
    draw_spillable_area=True,
    image_size=(600, 800),
    map_BB=map_bounds,
    projection_class=GeoProjection
)
model.outputters += renderer

shp_file = os.path.join(images_dir, 'erie_results.shp')
outputer = gs.ShapeOutput(shp_file)
outputer.water_depth_dfsu_file = depth_dfsu_file
outputer.output_timestep=timedelta(hours=1)

model.outputters += outputer

netcdf_file = os.path.join(images_dir, 'output.nc')
gs.remove_netcdf(netcdf_file)
nc_outputter = gs.NetCDFOutput(
    netcdf_file,
    which_data='most',
    output_timestep=gs.hours(1),
    water_depth_dfsu_file = depth_dfsu_file
)
model.outputters += nc_outputter



x, y = [], []
for step in model:
    positions = model.get_spill_property('positions')
    x.append(positions[:, 0])
    y.append(positions[:, 1])

print(model.list_spill_properties())
model.full_run()
