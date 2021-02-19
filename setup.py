import setuptools

with open('README.md', 'r') as rmf:
    readme = rmf.read()
    
with open('VERSION', 'r') as verf:
    version = verf.read()
    
setuptools.setup(
    name='live2p',
    version=version,
    author='Will Hendricks & Mora Ogando',
    author_email='hendricksw@berkeley.edu',
    description='Real-time calcium imaging processing with caiman and suite2p.',
    long_description=readme,
    url='https://github.com/willyh101/live2p',
    license='MIT',
    packages=setuptools.find_packages()
)