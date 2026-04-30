import os

# Force mock Nokia NaC behavior for local test execution.
# Tests should never depend on external Nokia CAMARA network services.
os.environ['NOKIA_NAC_TOKEN'] = ''
os.environ['APP_ENV'] = 'test'
