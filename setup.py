from distutils.core import setup

setup(name = 'grazer',
      version = '0.9',
      description = 'Grazer Scraper',
      author = 'Bohdan Mushkevych',
      author_email = 'mushkevych@gmail.com',
      url = 'https://github.com/mushkevych/grazer',
      packages = ['grazer', 'grazer.model', 'grazer.system', 'grazer.workers'],
      long_description = '''Grazer is a linearly-scalable content scraper''',
      license = 'Apache 2.0',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Environment :: Web Environment',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Utilities',
          ],
      requires=['werkzeug', 'jinja2', 'amqp', 'pymongo', 'psutil', 'fabric', 'setproctitle', 'synergy_odm',
                'mock']
)