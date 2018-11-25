from setuptools import setup, find_packages


setup(name='minesweeper_solver',
      version='1.0',
      description='Minesweeper solver',
      author='Johnny Deuss',
      author_email='johnnydeuss@gmail.com',
      url='https://github.com/JohnnyDeuss/minesweeper_solver',
      project_urls={'Source': 'https://github.com/JohnnyDeuss/minesweeper_solver'},
      install_requires=['scipy==1.1.0', 'numpy==1.15.4', 'python-constraint==1.4.0'],
      packages=find_packages()
    )
