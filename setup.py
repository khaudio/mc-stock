from distutils.core import setup


setup(
        name='mcstock',
        version='0.1.0',
        author='Kyle Hughes',
        author_email='kyle@kylehughesaudio.com',
        packages=['mcstock'],
        include_package_data=True,
        url='',
        license='LICENSE.txt',
        description='Checks stock on items at a given Microcenter location.',
        long_description=open('README.MD').read(),
        install_requires=[
                'aiohttp',
                'asyncio',
                'async_timeout',
                'getpass',
                're',
                'smtplib'
            ],
    )
