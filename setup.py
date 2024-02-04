from setuptools import setup, find_packages

setup(
   name='b2sim',
   version='1.3.0',
   description='A module to simulate the generation of eco and farms in Bloons TD Battles 2',
   long_description='TODO',
   author='redlaserbm',
   author_email='redlaserbm@gmail.com',
   packages=find_packages(),  #same as name
   install_requires=['pandas', 'matplotlib'], #external packages as dependencies
   include_package_data=True
)