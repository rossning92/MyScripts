@echo off
cd _threejs
.\node_modules\.bin\webpack-dev-server --env.entryFolder="{{ANIMATION_PROJECT_PATH}}" --open --watch
