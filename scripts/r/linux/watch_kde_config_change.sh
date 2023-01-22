inotifywait -m ~/.config -e create,modify,delete -e moved_to -r |
    while read path action file; do
        echo "The file '$file' appeared in directory '$path' via '$action'"
        # do something with the file
    done
