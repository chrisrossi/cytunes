# Install, globally
$ sudo apt install npm
$ npm install --global gulp-cli

# Install, locally
$ mkvirtualenv -p `which python3` cytunes
$ pip install -e .
$ npm install --save-dev gulp
$ npm install

# Publish
$ publish
$ rsync -avz wwwdata/ cytunes.org:wwwdata/
