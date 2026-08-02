from setuptools import setup, find_packages

from VERSION import VERSION

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gadgetconfig",  # Replace with your project's name
    version=VERSION,
    author="Stuart Lynne",
    author_email="stuart.lynne@gmail.com",
    description="Command line and GUI Gadget Config for Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/myproject",  # Replace with your project's URL
    packages=find_packages(),  # Automatically find all packages and sub-packages
    py_modules=["VERSION"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your chosen license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Specify your Python version requirement
    # Keep the base install offline-friendly. Optional runtime helpers such as
    # commentjson, inotify, termcolor, and python-magic can be supplied by the
    # distro packages on Raspberry Pi systems.
    install_requires=[],
    extras_require={
        'mcp': [
            'mcp>=1.28.1,<2',
        ],
    },
    entry_points={
        'console_scripts': [
            'gadgetconfig = gadgetconfig.gadgetconfig.gadgetconfig:main',
            'gadgetapp = gadgetconfig.gadgetapp.gadgetapp:main',
            'pigadget-mcp = gadgetconfig.pigadget_mcp.server:main',
            'sysfstree = gadgetconfig.sysfstree.sysfstree:main',
        ],
    },
)
