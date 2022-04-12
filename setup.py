from setuptools import setup

setup(
    name='tagcounter',
    version='1.0',
    author='Author',
    packages=['tagcounter'],
    description='Description',
    package_data={'': ['config.yaml']},
    include_package_data=True,
    install_requires=['requests','sqlalchemy','url_normalize','validators','datetime','pyyaml','click','pyttk'],
    entry_points={'console_scripts': ['tagcounter = tagcounter.tagcounter:main']},
)