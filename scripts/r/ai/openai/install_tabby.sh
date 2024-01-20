# https://github.com/TabbyML/tabby
docker run -it \
    --gpus all -p 8080:8080 -v $HOME/.tabby:/data \
    tabbyml/tabby \
    serve --model TabbyML/StarCoder-1B --device cuda
