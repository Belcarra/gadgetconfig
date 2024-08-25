from setuptools import setup, find_packages

# Read the contents of your README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gadgetconfig",  # Replace with your project's name
    version=open('VERSION.txt').read().strip(),
    author="Stuart Lynne",
    author_email="stuart.lynne@gmail.com",
    description="Command line and GUI Gadget Config for Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/myproject",  # Replace with your project's URL
    packages=find_packages(),  # Automatically find all packages and sub-packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your chosen license
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',  # Specify your Python version requirement
    install_requires=[
        "argparse",
        "commentjson",
        "prettyjson",
        "scandir",
        "inotify",
        "termcolor",
        "python-magic",
        "gadgetconfig"
    ],
    entry_points={
        'console_scripts': [
            'gadgetconfig = gadgetconfig.gadgetconfig.gadgetconfig:main',
            'gadgetapp = gadgetconfig.gadgetapp.gadgetapp:main',
            'sysfstree = gadgetconfig.sysfstree.sysfstree:main',
        ],
    },
)

