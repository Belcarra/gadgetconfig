
from setuptools import setup


def main():

    setup(
        name='gadgetconfig',
        packages=['gadgetconfig'],
        package_dir={'': 'src'},
        version=open('VERSION.txt').read().strip(),
        author='Stuart Lynne',
        author_email='stuart.lynne@belcarra.com',
        url='http://github.com/Belarra/gadgetconfig',
        download_url='http://github.com/Belarra/gadgetconfig.git',
        license='MIT',
        keywords=['usb', 'gadget'],
        description='gadgetconfig creates and controls Gadget USB Devices and integrates Gadget with systemd',
        entry_points={'console_scripts': ['gadgetconfig = gadgetconfig:main', ], },
        py_modules=['add', 'export', 'manage', 'remove'],
        install_requires=["argparse"],
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
        data_files=[
            ('/etc/gadgetservice', ['definitions/belcarra-2acm+ecm.json']),
            ('/usr/lib/gadgetservice', ['service/gadget.start', 'service/gadget.stop']),
            ('/lib/systemd/system', ['service/gadget.service']),
            ('/usr/share/doc/gadgetconfig', ['README.md', 'README-Gadget.md', 'README-Raspbian.md']), ],

        long_description=open('README.md').read(),
        long_description_content_type='text/markdown'

    )


if __name__ == '__main__':
    main()
