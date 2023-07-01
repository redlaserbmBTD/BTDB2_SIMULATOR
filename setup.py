from setuptools import setup

setup(
   name='b2sim',
   version='1.0.2',
   description='A module to simulate the generation of eco and farms in Bloons TD Battles 2',
   author='redlaserbm',
   author_email='redlaserbm@gmail.com',
   packages=['b2sim'],  #same as name
   install_requires=['numpy', 'pandas', 'matplotlib'], #external packages as dependencies
   include_package_data=True
)