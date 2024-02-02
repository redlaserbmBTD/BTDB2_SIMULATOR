from setuptools import setup

setup(
   name='b2sim',
   version='1.2.8',
   description='A module to simulate the generation of eco and farms in Bloons TD Battles 2',
   long_description='TODO',
   author='redlaserbm',
   author_email='redlaserbm@gmail.com',
   packages=['b2sim'],  #same as name
   install_requires=['pandas', 'matplotlib'], #external packages as dependencies
   include_package_data=True
)