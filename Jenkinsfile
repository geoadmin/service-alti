#!/usr/bin/env groovy

node(label: "jenkins-slave") {

  try {
    stage("Checkout") {
      checkout scm
    }
    stage("Build") {
      sh 'source rc_ci && make cleanall all'
      echo sh(returnStdout: true, script: 'env')
    }
    stage("Lint") {
      sh 'make lint'
    }
    stage("Test") {
      parallel (
        'integration': {
          sh '.venv/bin/nosetests alti/tests/integration/'
        },
        'functional': {
          sh '.venv/bin/nosetests alti/tests/functional/'
        }
      )
    }
  } catch (e) {
    throw e
  }
  finally {
    stage("Clean") {
      cleanWs()
    }
  }
}
