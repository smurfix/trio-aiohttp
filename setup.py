from setuptools import setup, find_packages

exec(open("trio_aiohttp/_version.py", encoding="utf-8").read())

LONG_DESC = open("README.rst", encoding="utf-8").read()

setup(
    name="trio-aiohttp",
    version=__version__,
    description="Helpers for running aiohttp under Trio",
    url="https://github.com/smurfix/trio-aiohttp",
    long_description=LONG_DESC,
    author="Matthias Urlichs",
    author_email="matthias@urlichs.de",
    license="GPLv3 or later",
    packages=find_packages(),
    install_requires=[
        "trio-asyncio",
        "aiohttp",
    ],
    keywords=[
        "html", "server"
    ],
    python_requires=">=3.5",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Framework :: Trio",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Framework :: Trio",
    ],
)
