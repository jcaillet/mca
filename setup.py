from setuptools import setup, find_packages

''' In order to distribute the python eggs, run the following command in your console:
    python setup.py bdist_egg
'''

setup(
    name = "mca",
    version = "0.1",
    packages = find_packages(),

    # scripts to create executable
    # scripts = ['mca.py'], TODO

    # resources
    package_data = {
        'resources':['help/*.pdf'],
        'resources':['images/*.png', 'images/*.gif'],
        'pgsql':['*.sql']
    },

    # dependencies
    install_requires = ['networkx>=1.7', 'GeoAlchemy>=0.7.1', 'Shapely>=1.2.16', 'pyshp>=1.1.4', 'wxPython>=2.8'],

    author = "Loïc Gasser, LASIG, EPFL; Jérôme Caillet",
    description = "Multiple Centrality Assessment"
)
