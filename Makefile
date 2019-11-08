#include Makefile-yaml
PROJECT=archbot
WD=/tmp
REPO_URI=https://github.com/viaacode/archbot.git
GIT_NAME=archbot
APP_NAME=archbot
#ENV=prd
#BRANCH=master
TOKEN=`oc whoami -t`
path_to_oc=`which oc`
oc_registry=docker-registry-default.apps.do-prd-okp-m0.do.viaa.be
.ONESHELL:
SHELL = /bin/bash
.PHONY:	all
check-env:
ifndef ENV
  $(error ENV is undefined)
endif
OC_PROJECT=viaa-tools
ifndef BRANCH
  $(error BRANCH is undefined)
endif
TAG=${ENV}

commit:
	git add .
	git commit -a
	git push
checkTools:
	if [ -x "${path_to_executable}" ]; then  echo "OC tools found here: ${path_to_executable}"; else echo please install the oc tools: https://github.com/openshiftorigin/releases/tag/v3.9.0; fi; uname && netstat | grep docker| grep -e CONNECTED  1> /dev/null || echo docker not running or not using linux
login:	checkTools
	oc login do-prd-okp-m0.do.viaa.be:8443
	oc project "${OC_PROJECT}" ||  oc new-project "${OC_PROJECT}"
	docker login -p "${TOKEN}" -u unused ${oc_registry}

clone:
	cd /tmp && git clone  --single-branch -b ${BRANCH} "${REPO_URI}"
buildimage:
	docker build -t ${oc_registry}/${OC_PROJECT}/${APP_NAME}:${TAG} .
push:
	docker push ${oc_registry}/${OC_PROJECT}/${APP_NAME}:${TAG}
clean:
	rm -rf /tmp/${GIT_NAME}
delete:
	oc delete dc/${APP_NAME}
all:	clean checkTools login clone buildimage push clean

