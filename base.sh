#! /bin/bash

GITHUB="github.com/cilt-uct/Brightspace-Middleware-Lite.git"
REGISTRY="localhost:5000"

AUTH_FILE=/usr/local/serverconfig/middleware.cfg
USERS_FILE=/usr/local/serverconfig/users.cfg

SCRIPT_FOLDER=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_FOLDER

CURRENT_USER=$(logname)

# Function to retrieve a value from a .env file
get_env_value() {

  local key=$1

  if [ -f ".env" ]; then
    local file_path='.env'
  elif [ -f ".env.run" ]; then
    local file_path='.env.run'
  else
    local file_path='.env.template'
  fi

  # Check if the file exists
  if [ ! -f "$file_path" ]; then
    echo "File $file_path not found!"
    return 1
  fi

  # Extract the value for the given key
  local value=$(grep -oP "^${key}=\K.*" "$file_path")

  if [ -z "$value" ]; then
    echo "Key $key not found in $file_path"
    return 1
  fi

  # Remove surrounding quotes if present
  value=$(echo "$value" | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" | tr -d '"' | tr -d "'")

  echo "$value"
  return 0
}

remove_file_if_exists() {
  local file_path=$1

  if [ -f "$file_path" ]; then
    rm "$file_path"
  fi
}

writeConfiguration() {
  INPUT=$1
  OUTPUT=$2

  while read line
  do
      [[ $line = \#* ]] && continue

      if [ ! -z "$line" ]; then

        IFS="=" read find replace <<< "$line"

        sed -i -e "/#.*/! s|$find|$replace|" $OUTPUT
      fi

  done < $INPUT
}

# Get the display name of the user
# params:
# $1 -- the section (if any)
# $2 -- the key
getCurrentUser() {

  section="git"
  key=$CURRENT_USER

  value=$(
    if [ -n "$section" ]; then
      sed -n "/^\[$section\]/, /^\[/p" $USERS_FILE
    else
      cat $USERS_FILE
    fi |

    egrep "^ *\b$key\b *=" |

    head -1 | cut -f2 -d'=' |
    sed 's/^[ "'']*//g' |
    sed 's/[ ",'']*$//g' )

  if [ -n "$value" ]; then
    echo $value
    return
  else
    echo 'NA'
    return
  fi
}

# Function to extract name from the string
get_name() {
  local input="$1"
  local name_pattern="^([^<]+)"
  [[ $input =~ $name_pattern ]] && echo "${BASH_REMATCH[1]}"
}

# Function to extract email from the string
get_email() {
  local input="$1"
  local email_pattern="<([^>]+)>"
  [[ $input =~ $email_pattern ]] && echo "${BASH_REMATCH[1]}"
}

# check to see if git exists
if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
  branch_name=$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)
else
  branch_name=''
fi

user="$(getCurrentUser)"

name=$(get_name "$user")
email=$(get_email "$user")

export GIT_COMMITTER_NAME="$name"
export GIT_COMMITTER_EMAIL="$email"
export GIT_AUTHOR_NAME="$name"
export GIT_AUTHOR_EMAIL="$email"

version=`cat VERSION`
local_registry="localhost:5000"

cp .env.template .env.run
writeConfiguration "$AUTH_FILE" .env.run

# remove dev versions
remove_file_if_exists app/services/web/VERSION
