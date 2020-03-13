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
// Integration tests disabled because Jenkins doesn't have access to the EFS
// and with the new COMB layer we would need more than 200Mo on Github to satisfy the old
// tile that was present int /data folder. Integration tests should be enabled again when the migration
// to AWS CodeBuild is done (and our CodeBuild instance has access to the EFS)
//       parallel (
//         'Integration tests': {
//           sh 'make testintegration'
//         },
//         'Unit testing': {
          sh 'make testunit'
//         }
//       )
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
