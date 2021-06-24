def Exists = null
def deployQas = null
def gitBranch =null
def test_results = false
def GIT_CRD = 'meemoo-ci'
def GITHUB_API_URL="https://github.com/api/v3/repos/${params.REPO_NAME}"
         
pipeline {
   agent {
    kubernetes {
      yaml """\
        apiVersion: v1
        kind: Pod
        metadata:
          labels:
            component: infra-builder
            lang: python
            app: archbot
        spec:
          containers:
          - name: default
            image: image-registry.openshift-image-registry.svc:5000/ci-cd/py:3.7
            command:
            - cat
            tty: true
            imagePullPolicy: Always
          
        """.stripIndent()
    }
  }  

  
  stages {
  
  

    stage('what will I do?') {
            steps {
               script {
     //          def issue = jiraGetIssue idOrKey: 'INFRA-324', site: 'meemoo'
   // echo issue.data.toString()
                        sh 'printenv'
                        echo 'Notice Build is done in openshift'
                        echo "Notice Everything is ran in a kubernetes container (agent included)"
                        echo 'Only build if there is no BuildConfig (openshift) with the name APP_NAME-BAANCH-SHORTCOMMIT'
                        echo "Running Tests in the puthon 3.8 container"
                        echo "IF tag on commit tag QAS"
                        echo getJiraIssueList()
       
              }
            }
    }
    stage('Setup parameters') {
            steps {
                script { 
                    properties([
                        parameters([

                            choice(
                                choices: ['dev', 'int','qas','prd'], 
                                name: 'env'
                            ),
                            booleanParam(
                                defaultValue: false, 
                                description: 'Run test?', 
                                name: 'TEST'
                            ),booleanParam(
                                defaultValue: true, 
                                description: 'Run build?', 
                                name: 'BUILD'
                            ),
                            booleanParam(
                                defaultValue: true, 
                                description: 'Run build?', 
                                name: 'DEPLOY',
                            ),                            
                            text(
                                defaultValue: '''
                                this is a multi-line 
                                string parameter example
                                ''', 
                                 name: 'COMMENT'
                            ),
                            string(
                                defaultValue: 'slack-bots', 
                                name: 'OC_PROJECT', 
                                trim: true
                            ),
                            string(
                                defaultValue: '8080', 
                                name: 'PORT', 
                                trim: true
                            ),
                            string(
                                defaultValue: 'python-slim:3.8', 
                                name: 'BASE_IMG', 
                                trim: true
                            ),
                            string(
                                defaultValue: 'archbot', 
                                name: 'IS', 
                                trim: true
                            ),
                            string(
                                defaultValue: "master", 
                                name: 'BRANCH', 
                                trim: true
                            ),
                            string(
                                defaultValue: 'https://github.com/viaacode/archbot.git', 
                                name: 'APP_REPO', 
                                trim: true
                            ),
                            string(
                                defaultValue: "/", 
                                name: 'CONTEXT_DIR', 
                                trim: true
                            ),
                            string(
                                defaultValue: 'archbot', 
                                name: 'APP_NAME', 
                                trim: true
                            ),
                            string(
                                defaultValue: 'archbot', 
                                name: 'REPO_NAME', 
                                trim: true
                            ),
                        ])
                    ])
                }
                
            }
        }    
    
    stage('checkout') {
        environment {
            ENDPOINT = 'https://c113-e.private.eu-de.containers.cloud.ibm.com:30227'
            IS = "${params.IS}"
            REGISTRY = 'default-route-openshift-image-registry.meemoo2-2bc857e5f10eb63ab790a3a1d19a696c-i000.eu-de.containers.appdomain.cloud'
            OC_PROJECT = "${params.OC_PROJECT}"
            APP_REPO = "${params.APP_REPO}"
            APP_NAME = "${params.APP_NAME}"
            BRANCH = "${params.BRANCH}"
            env = "${params.env}"
            BASE_IMG = "${params.BASE_IMG}"
            GIT_CRD = '79d1c1d0-4433-4550-984d-ae27466b0c11'
            GITHUB_API_URL="https://api.github.com/repos/viaacvode/${params.REPO_NAME}"
			}
     			steps {
     			container('default'){
                    script {
                        if (env.GIT_BRANCH) { env.BRANCH = env.GIT_BRANCH } // if in multibranch
                        sh '''#!/bin/bash
                        set -e
                        login_oc.sh $ENDPOINT > /dev/null || echo ok
                        oc project $OC_PROJECT
                        echo logged in'''	

                        git branch: "${BRANCH}", credentialsId: "${GIT_CRD}", url: "${APP_REPO}"
                        checkout([$class: 'GitSCM', branches: [[name: "*/${BRANCH}"]], extensions: [[$class: 'GitSCMStatusChecksExtension'], [$class: 'AuthorInChangelog'], [$class: 'LocalBranch', localBranch: "${BRANCH}"]], userRemoteConfigs: [[credentialsId: 'meemoo-ci', url: "${APP_REPO}"]]])
                        Exists=sh(returnStdout: true, script: 'oc -n $OC_PROJECT get build  -l ref=`git show-ref --head|head -n1|awk \'{print $1}\'`|egrep Complete&& echo true||echo false').trim()
                        echo 'The build exists: ' + Exists 
                        def shortCommit = sh(returnStdout: true, script: "git log -n 1 --pretty=format:'%h'").trim()
                        env.SHORTCOMMIT = shortCommit
                        gitRef=sh(returnStdout: true, script: 'git show-ref --head|head -n1|awk \'{print $1}\'').trim()
                        env.GIT_COMMIT = gitRef
                        env.GITREF = gitRef
                        gitTag=sh(returnStdout: true, script: "git tag --contains | head -1").trim()
                        if(gitTag) {
                            gitTagVersion=sh(returnStdout: true, script: "git describe --tags|| echo noTagFound").trim()
                            deployQas='true'
                            }
                        sh('git symbolic-ref HEAD|cut -d / -f3> BRANCH') 
                        sh('git ls-remote 2>/dev/null| grep refs/heads/dev-| awk \'{print $2}\'|cut -d / -f3 > branches')
                        echo 'Pulled.. ' + "${BRANCH}" + ' ...exists... ' +  Exists
                    } // script
                } // steps
            }//end container
        }//end sstage	
 		stage('Build code') {
        environment {
            ENDPOINT = 'https://c113-e.private.eu-de.containers.cloud.ibm.com:30227'
            IS = "${params.IS}"
            REGISTRY = 'default-route-openshift-image-registry.meemoo2-2bc857e5f10eb63ab790a3a1d19a696c-i000.eu-de.containers.appdomain.cloud'
            OC_PROJECT = "${params.OC_PROJECT}"
            APP_REPO = "${params.APP_REPO}"
            APP_NAME = "${params.APP_NAME}"
            BRANCH = "${params.BRANCH}"
            BASE_IMG = "${params.BASE_IMG}"
            SVC_PORT ="${params.PORT}"
            env = "${params.env}"
			}
        when {
            expression {
            return params.BUILD
            }
        } 	
			steps {
				container('default'){
					script {
                    if (env.GIT_BRANCH) { env.BRANCH = env.GIT_BRANCH } // if in multibranch

					sh '''#!/bin/bash
                        oc import-image $BASE_IMG --confirm
                        oc new-build -l ref=$GITREF,app=$APP_NAME,env=$env,branch=$BRANCH --strategy=docker --name $APP_NAME-$SHORTCOMMIT --docker-image=$BASE_IMG --to $IS:`git describe --tags|| echo latest` --context-dir=$CONTEXT_DIR  -n $OC_PROJECT .&& sleep 5
                        oc set build-secret --source=true bc/$APP_NAME-$SHORTCOMMIT github -n $OC_PROJECT && sleep 4
                        oc logs -f bc/$APP_NAME-$SHORTCOMMIT | egrep 'Push successful'|| oc start-build --follow=true $APP_NAME-$SHORTCOMMIT 
                        echo tagging dev 
                        oc tag $IS:`git describe --tags || echo latest` $IS:$env -n $OC_PROJECT
                        '''
                    setBuildStatus("Build complete", "SUCCESS");
                    try {
                        //comment_issues() // if branch starts with ticket but better use other method
                        updateJira()
                        }catch (err) {
                            echo err.getMessage()
                            echo "Could not update ticket, but we will continue."
                        }
                        echo 'BUILD DONE'
					} // script				
				}//end container			
			} // steps
		} // stage
		stage('Test code') {
            when {
                expression {
                return params.TEST
                }
            }
			steps {
				container('default'){
					script {
					sh '[ -d tests ]'
					sh 'pip3 install pytest==5.4.1 pytest-cov==2.8.1'
					sh 'python3 -m pytest --cov=./tests --junit-xml=./tests/test_results-py37.xml || echo test failed '
					test_results = true
                    } // script				
				}//end container	
				container('python38'){
					script {
					sh '[ -d tests ]'
					sh 'pip3 install pytest==5.4.1 pytest-cov==2.8.1'
					sh 'python3 -m pytest --cov=./tests --junit-xml=./tests/test_results-py38.xml || echo test failed'
                    test_results_38 = true
                    }
					// script				
				}//end container	
			} // steps
		} // stage
		stage('Deploy on ocp') {
            when {
                expression {
                return params.DEPLOY
                }
            }
            environment {
                ENDPOINT = 'https://c113-e.private.eu-de.containers.cloud.ibm.com:30227'
                IS = "${params.IS}"
                env = "${params.env}"
                REGISTRY = 'default-route-openshift-image-registry.meemoo2-2bc857e5f10eb63ab790a3a1d19a696c-i000.eu-de.containers.appdomain.cloud'
                OC_PROJECT = "${params.OC_PROJECT}"
                APP_REPO = "${params.APP_REPO}"
                APP_NAME = "${params.APP_NAME}"
                BRANCH = "${params.BRANCH}"
                BASE_IMG = "${params.BASE_IMG}"
                SVC_PORT = "${params.PORT}"
                GIT_CRD = 'meemoo-ci'
                }
			steps {
                script {
                    if (env.GIT_BRANCH) { env.BRANCH = env.GIT_BRANCH } // if in multibranch
                    echo 'Processing params env '  + params.env + ' branch ' + env.BRANCH + 'deploy ' + params.DEPLOY
                }
				container('default'){
					script {
                        sh '''#!/bin/bash
                        SVC_PORT=${SVC_PORT} IS=${IS} OC_PROJECT=${OC_PROJECT} APP_NAME=${APP_NAME} env=${env} oc_create /home/jenkins/app-deployment-tmpl.yaml 
                        SVC_PORT=${SVC_PORT} IS=${IS} OC_PROJECT=${OC_PROJECT} APP_NAME=${APP_NAME} env=${env} oc_create  /home/jenkins/app-service-tmpl.yaml 
                        oc set triggers deployment/$APP_NAME-$env --from-image $IS:$env -c $IS-${env} || echo image trigger set to $env ok
                        oc create configmap $APP_NAME-$env --from-env-file=.env.example || oc create configmap  $APP_NAME-$env & echo provide .env.example in git please
                        [ `ls openshift/*-gen.yaml 2>/dev/null`  ] && for f in `ls openshift/*-gen.yaml`;do oc_create ${f};done|| echo "no -gen.yaml files found to create"
                        # oc set env --from=configmap/$APP_NAME-$env deployment/$APP_NAME-$env -n $OC_PROJECT 
                        '''
                    sh('ls -ltrha')
                    } // script				
				}//end container			
			} // steps
		} // stage		
		
  stage('If tagged') {
      when {
        expression {
          deployQas == 'true';
        }
      }
      steps {
        // ... do something only if there's a tag for this project on this particular commit
        echo 'deploy qas'
        script {
         sh '''#/bin/bash
           echo "_____________________FOUND a TAG _____________________"
          '''
         }
				container('default'){
					script {
					sh '''#!/bin/bash
					oc tag $IS:`git describe --tags` $IS:qas -n $OC_PROJECT
					'''
                    //jiraNewVersion site: 'meemoo' 
                    } // script				
				}//end container	         
         
       }
    }//end stage

   
  }
      post {
    
        success {
            echo 'XXXXXXXXXXXXXXXX SUCESS XXXXXXXXXXXXXXXXXXX'
                setBuildStatus("Build", "SUCCESS");

        }
  
        failure {
            echo 'XXXXXXXXXXXXXXXX FAILED XXXXXXXXXXXXXXXXXXX'
                updateFailedJira()
                setBuildStatus("Build", "FAILED");
        }
      
        always {
            script {
              container('default'){
                 echo 'REPO_NAME: ' + params.APP_REPO +  ' BRANCH: ' + env.BRANCH
                 step([$class: 'JiraIssueUpdater', scm: [$class: 'GitSCM', branches: [[name: "*/${BRANCH}"]], extensions: [[$class: 'GitSCMStatusChecksExtension'], [$class: 'AuthorInChangelog'], [$class: 'LocalBranch', localBranch: "${BRANCH}"]], userRemoteConfigs: [[credentialsId: 'meemoo-ci', url: params.APP_REPO]]]])
                    if ( params.BUILD == true) {
                        jiraSendBuildInfo site: 'meemoo.atlassian.net' 

                    }
                    if ( params.DEPLOY == true) {
                        echo 'setting deployment info'
                        if (params.env =='qas'){  env.environmentType = 'staging'}
                        if  (params.env =='prd'){ env.environmentType = 'production'}
                        if  (params.env =='dev'){ env.environmentType = 'development'}
                        if  (params.env =='int'){ env.environmentType = 'development'}
                        echo ' XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX ' + env.environmentType + ' XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
                        //  def jiraNr = sh(returnStdout: true, script: "git branch -l --points-at HEAD|head -n1|cut -d ' ' -f 2|cut -d '-' -f1-2").trim()
                        def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector'])
                         jiraIssues.each { issueID ->
                            jiraSendDeploymentInfo site: 'meemoo.atlassian.net',environmentName: params.APP_NAME, environmentId: 'ibm-cloud', environmentType: env.environmentType, issueKeys: [issueID]
                         }
                    }
                    if (fileExists('./tests/test_results-py37.xml')) {
                            echo 'test for python 3.7: Yes'
                            junit 'tests/test_results-py37.xml'
                            archiveArtifacts artifacts: 'tests/test_results-py37.xml', onlyIfSuccessful: true
                            junit (
                                testResults: '**/tests/*.xml',
                                testDataPublishers: [
                                jiraTestResultReporter(
                                    configs: [
                                    jiraStringField(fieldKey: 'summary', value: '${DEFAULT_SUMMARY}'),
                                    jiraStringField(fieldKey: 'description', value: '${DEFAULT_DESCRIPTION}'),
                                    jiraStringArrayField(fieldKey: 'labels', values: [jiraArrayEntry(value: 'Jenkins'), jiraArrayEntry(value:'Integration')])
                                    ],
                                   projectKey: 'DEV',
                                   // issueType: '10107',
                                    autoRaiseIssue: false,
                                    autoResolveIssue: false,
                                    autoUnlinkIssue: false,
                            )])                  
                            
                    }
                    else { echo 'No test for python 3.7'}
                    if (fileExists('./tests/test_results-py38.xml')) {
                        echo 'test for python 3.8: Yes'
                        junit 'tests/test_results-py38.xml'
                        archiveArtifacts artifacts: 'tests/test_results-py38.xml', onlyIfSuccessful: true }
                    else { echo 'No test for python 3.8' }                            
            
              }//end container
            }//end script
            
        }//end always
        
   }//end post

} //end pipeline
void setBuildStatus(String message, String state) {
  step([
      $class: "GitHubCommitStatusSetter",
      reposSource: [$class: "ManuallyEnteredRepositorySource", url: "https://github.com/viaacode/${params.REPO_NAME}"],
   //   contextSource: [$class: "ManuallyEnteredCommitContextSource", context: "ci/jenkins/build-status"],
      errorHandlers: [[$class: "ChangingBuildStatusErrorHandler", result: "UNSTABLE"]],
      statusResultSource: [ $class: "ConditionalStatusResultSource", results: [[$class: "AnyBuildResult", message: message, state: state]] ]
  ]);
}
// alt way to gert ticket nr start of commit msg
// ((?<!([A-Z]{1,10})-?)[A-Z]+-\d+) seem to do the trick in default jira selector
void  getJiraNr() { 
    sh(returnStdout: true, script: " git log --format=%B -n 1 |head -n1|cut -d ' ' -f1 | egrep -v Merge || git log --format=%B -n 1 |head -n1|rev|cut -d'/' -f1|rev| cut -d '-' -f 1-2").trim()
}
void comment_issues() {
    def issue_pattern = getJiraNr() 
    JiraNR = getJiraNr()
    def comment = [ body: 'Jenkins has Built: SUCCESS!' ]
    jiraAddComment site: 'meemoo', idOrKey: JiraNR, input: comment
    echo 'Updated ticket: ' + JiraNR 
}
void updateJira() {
	def jiraServer = 'meemoo' // Define a Jira server entry in the Jenkins Jira Steps configuration named JIRA-PROD
  def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector'])
	jiraIssues.each { issue ->
		jiraAddComment comment: "{panel:bgColor=#97FF94}{code}Code was build ${RUN_TESTS_DISPLAY_URL}, ${JOB_BASE_NAME} ${BUILD_NUMBER}{code} {panel}" + getJiraIssueListNoHtml(), idOrKey: issue, site: jiraServer
    }  
}
void updateFailedJira() {
	def jiraServer = 'meemoo' // Define a Jira server entry in the Jenkins Jira Steps configuration named JIRA-PROD
  def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector'])
	jiraIssues.each { issue ->
		jiraAddComment comment: "{panel:bgColor=#FF9494}{code}Build has FAILED :( ${RUN_TESTS_DISPLAY_URL}, ${JOB_BASE_NAME} ${BUILD_NUMBER}{code} {panel}" + getJiraIssueListNoHtml() , idOrKey: issue, site: jiraServer
    }
}
void getJiraIssueList() {
    /**
     * Returns an HTML formatted list of Jira issues related in the build.
     * This requires the Jenkins JIRA Pipeline Steps plugin https://jenkinsci.github.io/jira-steps-plugin/getting-started/
     * @param None
     * @return An HTML string containing Jira issues
     */ 

    def jiraServer = 'meemoo' // Define a Jira server entry in the Jenkins Jira Steps configuration named JIRA-PROD
    def jiraURL = "https://meemoo.atlassian.net" // Define the Jira URL
    def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector']) // Get all related Jira issues in a list
    def issueList = "<h2>No changes since last build.</h2><ul>"
    
    if (jiraIssues.size() != 0) {
        issueList = "<h2>List of Changes</h2><ul>"
	    jiraIssues.each { issueID ->
            def issue = jiraGetIssue idOrKey: issueID, site: jiraServer // Retrieves the Jira issue 
            def summary = issue.data.fields.summary.toString() // Retrieves the summary field
            issueList = issueList.concat("<li><a href=\"${jiraURL}/browse/${issueID}\">${issueID} : ${summary}</a></li>")
        }
        issueList = issueList.concat("</ul>")
    }
    return (issueList)    
}



void getJiraIssueListNoHtml() {
    /**
     * Returns an HTML formatted list of Jira issues related in the build.
     * This requires the Jenkins JIRA Pipeline Steps plugin https://jenkinsci.github.io/jira-steps-plugin/getting-started/
     * @param None
     * @return An HTML string containing Jira issues
     */ 

    def jiraServer = 'meemoo' // Define a Jira server entry in the Jenkins Jira Steps configuration named JIRA-PROD
    def jiraURL = "https://meemoo.atlassian.net" // Define the Jira URL
    def jiraIssues = jiraIssueSelector(issueSelector: [$class: 'DefaultIssueSelector']) // Get all related Jira issues in a list
    def issueList = "{panel:bgColor=#97FF94}{code}"
    
    if (jiraIssues.size() != 0) {
        issueList = '''List of Tickets
        '''
	    jiraIssues.each { issueID ->
            def issue = jiraGetIssue idOrKey: issueID, site: jiraServer // Retrieves the Jira issue 
            def summary = issue.data.fields.summary.toString() // Retrieves the summary field
            issueList = issueList.concat("${jiraURL}/browse/${issueID} ${issueID} : ${summary}\n")
        }
        
    }
    return (issueList)    
}
