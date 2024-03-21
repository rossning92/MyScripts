fmt --width=72 <(git log --format=%B -n 1)
# fmt --width=72 <(git log --format=%B -n 1) >temp_message.txt
# git commit --amend -F temp_message.txt
# rm temp_message.txt
