
from setuptools import setup, Extension


def main():

    setup(
        name='sysfstree',
        packages=['sysfstree'],
        package_dir={'': 'src'},
        version=open('VERSION.txt').read().strip(),
        author='Stuart Lynne',
        author_email='stuart.lynne@gmail.com',
        url='http://github.com/Belarra/sysfstree',
        download_url='http://github.com/Belarra/sysfstree.git',
        license='MIT',
        keywords=['configfs', 'sysfs', 'pi', 'usb', 'gadget'],
        description='sysfstree displayes gadget usb information from the ConfigFS and SysFS',
        entry_points={'console_scripts': ['sysfstree = sysfstree:main', ], },
        install_requires=["argparse", "python-magic"],
        classifiers=[
            "Programming Language :: Python",
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "Intended Audience :: System Administrators",
            "Operating System :: POSIX",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            'Topic :: System :: Logging',
            'Topic :: Text Processing',
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: System :: System Shells",
            "Topic :: System :: Systems Administration",
        ],
        long_description=open('README.md').read(),
        long_description_content_type='text/markdown'

    )


if __name__ == '__main__':
    main()
