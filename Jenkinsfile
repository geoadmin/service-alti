#!/usr/bin/env groovy

node(label: "jenkins-slave") {

  try {
    stage("Checkout") {
      checkout scm
    }
    stage("Build") {
      sh '. ./rc_ci && make cleanall setup templates'
      echo sh(returnStdout: true, script: 'env')
    }
    stage("Lint") {
      sh 'make lint'
    }
    stage("Fix rights") {
      sh 'make fixrights'
    }
    stage("Test") {
       parallel (
         'Integration tests': {
           sh 'make testintegration'
         },
         'Unit testing': {
          sh 'make testunit'
         }
       )
    }
  } catch (e) {
    throw e
  }
  finally {
    stage("Clean") {
      sh 'make cleanall'
      sh 'git clean -dx --force'
    }
  }
}
