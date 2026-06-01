from setuptools import setup, find_packages

setup(
    name="shop-shared",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9.9",
        "redis>=5.0.0",
        "pyjwt>=2.10.1",
        "bcrypt>=4.2.0",
        "apscheduler>=3.10.0",
    ],
)
