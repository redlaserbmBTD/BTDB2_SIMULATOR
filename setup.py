from setuptools import setup, find_packages

setup(
   name='b2sim',
   version='2.2.4',
   description='A module to simulate the generation of eco and farms in Bloons TD Battles 2',
   long_description='TODO',
   long_description_content_type='text/markdown',
   author='redlaserbm',
   author_email='redlaserbm@gmail.com',
   packages=find_packages(),  #same as name
   extras_require= {
      'analysis': [
           'pandas', 
           'matplotlib',
      ],
   },
   include_package_data=True
)