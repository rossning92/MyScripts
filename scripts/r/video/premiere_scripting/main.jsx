var project = app.project;

// var first = app.project.rootItem.children[2];
// project.activeSequence.videoTracks[0].insertClip(first, 0.0);

// app.sourceMonitor.closeClip();


function getSelectedProjectItem() {
    var viewIDs = app.getProjectViewIDs();
    for (var a = 0; a < app.projects.numProjects; a++) {
        var currentProject = app.getProjectFromViewID(viewIDs[a]);
        if (currentProject) {
            if (currentProject.documentID === app.project.documentID) { // We're in the right project!
                var selectedItems = app.getProjectViewSelection(viewIDs[a]);
                for (var b = 0; b < selectedItems.length; b++) {
                    var currentItem = selectedItems[b];
                    return currentItem;
                }
            }
        }
        return null;
    }
}


var projectItem = getSelectedProjectItem();

// var markers = projectItem.getMarkers();

// if (markers) {
//     var markerCount = markers.numMarkers;
//     if (markerCount) {
//         for (var thisMarker = markers.getFirstMarker(); thisMarker !== undefined; thisMarker = markers.getNextMarker(thisMarker)) {
//             var oldColor = thisMarker.getColorByIndex();
//             var newColor = oldColor + 1;
//             if (newColor > 7) {
//                 newColor = 0;
//             }
//             thisMarker.setColorByIndex(newColor);
//             // $._PPP_.updateEventPanel("Changed color of marker named \'" + thisMarker.name + "\' from " + oldColor + " to " + newColor + ".");
//         }
//     }
// }



function addSubClip() {
    var startTime = new Time();
    startTime.seconds = 0.0;

    var endTime = new Time();
    endTime.seconds = 3.21;

    var hasHardBoundaries = 0;
    var sessionCounter = 1;
    var takeVideo = 1; // optional, defaults to 1
    var takeAudio = 1; // optional, defaults to 1

    var projectItem = getSelectedProjectItem();
    if (projectItem) {
        if ((projectItem.type == ProjectItemType.CLIP) || (projectItem.type == ProjectItemType.FILE)) {
            var newSubClipName = prompt('Name of subclip?', projectItem.name + '_' + sessionCounter, 'Name your subclip');
            if (newSubClipName) {
                var newSubClip = projectItem.createSubClip(newSubClipName,
                    startTime,
                    endTime,
                    hasHardBoundaries,
                    takeVideo,
                    takeAudio);
                if (newSubClip) {
                    var newStartTime = new Time();
                    newStartTime.seconds = 12.345;
                    newSubClip.setStartTime(newStartTime);
                }
            } else {
                $._PPP_.updateEventPanel("No name provided for sub-clip.");
            }
        } else {
            $._PPP_.updateEventPanel("Could not sub-clip " + projectItem.name + ".");
        }
    } else {
        $._PPP_.updateEventPanel("No project item found.");
    }
}


var seq = app.project.activeSequence;
var numVTracks = seq.videoTracks.numTracks;
var targetVTrack = seq.videoTracks[(numVTracks - 1)];
if (targetVTrack) {
    targetVTrack.insertClip(projectItem, 10.0);

    // var newClip = seq.insertClip(first, time, (seq.videoTracks.numTracks - 1), (seq.audioTracks.numTracks - 1));
    var newClip = targetVTrack.clips[targetVTrack.clips.numItems - 1];
    newClip.start = 1.0;
    newClip.end = 2.0;
    newClip.inPoint = 2.0;
}

