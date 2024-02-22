from setuptools import setup, find_packages

setup(
   name='b2sim',
   version='2.0.1',
   description='A module to simulate the generation of eco and farms in Bloons TD Battles 2',
   long_description='TODO',
   author='redlaserbm',
   author_email='redlaserbm@gmail.com',
   packages=find_packages(),  #same as name
   extras_require= {
      'analysis': [
           'pandas', 
           'matplotlib',
           'neat'
      ],
   },
   include_package_data=True
)