import os
from datetime import datetime, timedelta

import gnome.scripting as gs
from gnome.utilities.projections import GeoProjection
from netCDF4 import Dataset
from gnome.concentration.concentration_location import ConcentrationLocation

data_folder = r"D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\data\StClair"
nba_file = os.path.join(data_folder,"Lake St. Clair-shoreline.bna")
current_netcdf_file = os.path.join(data_folder,"Lake St. Clair-netCDF File.nc")
images_dir = r'D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\Images_StClair'
depth_dfsu_file = os.path.join(data_folder,"2D all.dfsu")

gs.set_verbose()
start_time = datetime(2024, 5, 22, 13)
mapfile = gs.get_datafile(nba_file)

model = gs.Model(
    start_time=start_time,
    duration=gs.hours(8),
    map=gs.MapFromBNA(mapfile, refloat_halflife=1),
    time_step=gs.minutes(1)
)

model.concentration = ConcentrationLocation(locations=[[-82.945024, 42.349559,0]])

map_bounds = ((-83.4, 41.85), (-83.4, 43.03), (-82.3, 43.03), (-82.3, 41.85))

current_mover = gs.PyCurrentMover.from_netCDF(current_netcdf_file)
model.movers += current_mover

spill = gs.surface_point_line_spill(
    num_elements=1000,
    start_position=(-82.90146720210102, 42.35556045123851, 0),
    release_time=start_time,
    end_position=(-82.90146720210102, 42.36556045123851, 0),
    end_release_time=start_time + gs.hours(6),
    amount=5000,
    units='bbl',
    windage_range=(0.01, 0.02),
    windage_persist=-1,
    name='My spill'
)

model.spills += spill


gs.make_images_dir(images_dir=images_dir)

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

netcdf_file = os.path.join(images_dir, 'output.nc')
gs.remove_netcdf(netcdf_file)
nc_outputter = gs.NetCDFOutput(
    netcdf_file,
    which_data='most',
    output_timestep=gs.hours(1),
    water_depth_dfsu_file = depth_dfsu_file
)
model.outputters += nc_outputter

#kmz_file = os.path.join(images_dir, 'gnome_results.kmz')
#model.outputters += gs.KMZOutput(kmz_file, output_timestep=timedelta(hours=1))

shp_file = os.path.join(images_dir, 'st_clair_results.shp')
model.outputters += gs.ShapeOutput(shp_file,
                                   water_depth_dfsu_file = depth_dfsu_file,
                                   output_timestep=timedelta(hours=1))


x, y = [], []
for step in model:
    positions = model.get_spill_property('positions')
    x.append(positions[:, 0])
    y.append(positions[:, 1])

print(model.list_spill_properties())
model.full_run()
