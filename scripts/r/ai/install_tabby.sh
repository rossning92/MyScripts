# https://github.com/TabbyML/tabby
# https://tabby.tabbyml.com/docs/models/
docker run -it \
    --gpus all -p 8080:8080 -v $HOME/.tabby:/data \
    tabbyml/tabby \
    serve --model TabbyML/StarCoder-3B --device cuda
