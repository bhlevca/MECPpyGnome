import xarray

file = r"D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\Images_Erie\output.nc"
#file = r"D:\WebGnome\git\PyGnome\py_gnome\scripts\testing_scripts\script_surface_concentration\Images_StClair\output.nc"

ds = xarray.open_dataset(file)

for d in ds.variables:
    print(d)

print(ds.variables["surface_concentration"])
print(ds.variables["surface_concentration"].values)

print(ds.variables["volumetric_concentration"])
print(ds.variables["volumetric_concentration"].values)