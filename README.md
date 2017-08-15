# root dir

1. env ---> .env : 
- define all the environment variables, e.g. DB_USER, DB_PWD
- we have autoenv installed, so the .env file will be execuated automatically when we cd in this dir
2. db.py : 
- define the database connection. here singleton means when we create a NewDatabase object, we will get the existing NewsDatabase object if NewsDatabase object already exists. in other words, we only have one NewsDatabase object in the program life cycle.
- we consider ssh tunnel here. need the environment variables defined in .env

3. environment_dl_tf.yml
- define the conda env: tensorflow, autoenv, pdbpp

> Here is the codebase for production use. strongly recommend using this template







ref: some files for your reference

