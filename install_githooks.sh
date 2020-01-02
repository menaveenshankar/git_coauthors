#!/bin/bash

## setup script to create symlinks to git hooks

if [ $# -ne 1 ]; then
	echo -e '\e[91mmissing argument - path to git repo\e[39m';
	exit
fi

# set paths
dir_path=$1
PWD=$(pwd)

# check if gitpython is installed
python -c "import git" &> /dev/null;
if [ $? -eq 1 ];
then
  echo "[INFO]: Installing gitpython";
  pip install gitpython;
fi

#check if PATH is updated in bashrc
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     bashrc_file=$HOME/.bashrc;;
    Darwin*)    bashrc_file=$HOME/.bash_profile;;
    *)          echo "[INFO]: Supported only on Linux and Mac. For other OSes carry out the following steps manually";;
esac

if [[ ! ${PWD} =~ $PATH ]]; then
  printf "#githooks to PATH\n" >> ${bashrc_file};
  printf "export PATH=\$PATH:$(pwd)" >> ${bashrc_file};
fi

# keep track of exit codes during symlinking
sum_exit_codes=0
function add_on_exit_code {
	if [ $? -ne 0 ]
	then
		sum_exit_codes=$(($sum_exit_codes+1))
	fi
}
## setup git hooks
chmod +x ${PWD}/git_hooks/prepare-commit-msg

# symlink git hooks
ln -s ${PWD}/git_hooks/authors.txt ${dir_path}/;
add_on_exit_code
ln -s ${PWD}/git_hooks/prepare-commit-msg ${dir_path}/hooks/;
add_on_exit_code

if [ $sum_exit_codes -ne 0 ]
then
	echo -e '\e[91mCould not create some symlinks!\e[39m';
else
	echo -e '\e[92mSymlinks created! Git hooks can be used now.\e[39m';
fi;