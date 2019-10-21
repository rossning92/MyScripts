var project = app.project;

var first = app.project.rootItem.children[2];
project.activeSequence.videoTracks[0].insertClip(first, 0.0);
