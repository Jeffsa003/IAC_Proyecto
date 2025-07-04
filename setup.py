from setuptools import setup, find_packages

setup(
    name='logica_recursos',
    version='0.1.0',
    packages=find_packages(),
    author='Gemini',
    author_email='gemini@google.com',
    description='Paquete para las funciones Lambda del proyecto de Elearning.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Yefferson-A/IAC_Proyecto',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
