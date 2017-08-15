# root dir (template for production use)

1. env ---> .env : 
- define all the environment variables, e.g. DB_USER, DB_PWD
- we have autoenv installed, so the .env file will be execuated automatically when we cd in this dir
2. db.py : 
- define the database connection. here singleton means when we create a NewDatabase object, we will get the existing NewsDatabase object if NewsDatabase object already exists. in other words, we only have one NewsDatabase object in the program life cycle.
- we consider ssh tunnel here. need the environment variables defined in .env

3. environment_dl_tf.yml
- define the conda env: tensorflow, autoenv, pdbpp

> Here is the codebase for production use. strongly recommend using this template


# ./ref
provide some references for backend db connections and environment setup

1. env : as above
2. loc_dev: the template for local development use. here we have config.py and dbconfig.py where we define the global db connection parameters 
3. prod_dev: the template for production use.
4. conda_env: my conda env yml files
5. deployment: in deployment stage, we need to use ansible_hosts. We can define different environment variables in different stages (dev, qa-testing, prod).


