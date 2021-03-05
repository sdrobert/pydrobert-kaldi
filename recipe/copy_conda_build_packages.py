# adapted from https://github.com/rmcgibbo/python-appveyor-conda-example
import sys
import os
import glob
import shutil
import conda_build.config as config

binary_package_glob = os.path.join(
    config.Config().bldpkgs_dir, "{0}*.tar.bz2".format(sys.argv[1])
)
print(binary_package_glob)
binary_packages = glob.glob(binary_package_glob)
print(binary_packages)

if not os.path.isdir(sys.argv[2]):
    os.makedirs(sys.argv[2])
for binary_package in binary_packages:
    shutil.copy(binary_package, sys.argv[2])
