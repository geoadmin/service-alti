const newBranchName = 'ltbtp_profile_cleanup';


function reverseProfile(profile) {
    let reversedProfile = $.extend(true, [], profile).reverse();
    // now we need to deal with `dist` property, which will be used by the hikingTime function
    const totalDistance = reversedProfile[0].dist;
    reversedProfile.forEach(coord => {
        coord.dist = totalDistance - coord.dist;
    });
    return reversedProfile;
}

function trendDifference(trendPreOverhaul, trendPostOverhaul) {
    if (trendPreOverhaul < 0 && trendPostOverhaul < 0 || (trendPreOverhaul >= 0 && trendPostOverhaul >= 0)) {
        return trendPostOverhaul - trendPreOverhaul;
    } else { // if trendPreOverhaul < 0 or trendPostOverhaul < 0
        return trendPostOverhaul + trendPreOverhaul;
    }
}

function addProfileStatistics(metadata, profile) {
    let elevation = {
        up: 0,
        down: 0,
        min: undefined,
        max: undefined,
        sum: function () { return this.up - this.down; }
    };
    let totalDistance = 0;
    let lastAltitude = undefined;
    let lastDistance = undefined;
    profile.forEach(profileValue => {
        const altitude = profileValue.alts['COMB'],
              distance = profileValue.dist;
        if (lastAltitude && lastDistance) {
            const altitudeDifference = altitude - lastAltitude,
                  distanceDifference = distance - lastDistance;
            if (altitudeDifference > 0) {
                elevation.up = elevation.up + altitudeDifference
            } else {
                elevation.down = elevation.down + Math.abs(altitudeDifference)
            }
            totalDistance += Math.sqrt((altitudeDifference * altitudeDifference) + (distanceDifference * distanceDifference));
        }
        if (elevation.min === undefined || elevation.min > altitude) {
            elevation.min = altitude;
        }
        if (elevation.max === undefined || elevation.max < altitude) {
            elevation.max = altitude;
        }
        lastAltitude = altitude;
        lastDistance = distance;
    });
    metadata.elevationUp = Math.round(elevation.up * 10) / 10.0;
    metadata.elevationDown = Math.round(elevation.down * 10) / 10.0;
    metadata.elevationMax = elevation.max;
    metadata.elevationMin = elevation.min;
    metadata.elevationSum = Math.round(elevation.sum() * 10) / 10.0;
    metadata.totalDistance = Math.round(totalDistance * 10) / 10.0;
}

function getProfile(wanderwegMetadata, callback) {
    const urlParams = '?elevation_models=COMB&projection=2056&offset=0';
    const requestConfig = {
        method: 'POST',
        headers: {
            'Referer': 'http://service-alti.int.bgdi.ch/'
        },
        body: JSON.stringify(wanderwegMetadata.geojson)
    };
    const startTimePreOverhaul = moment();
    fetch('http://service-alti.int.bgdi.ch/rest/services/profile.json' + urlParams, requestConfig)
    .then(response => response.json())
    .then(profile => {
        const time = hikingTime(profile),
              timeReversed = hikingTime(reverseProfile(profile)),
              startToFinishDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.startToFinish - time),
              finishToStartDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.finishToStart - timeReversed);
        wanderwegMetadata.geoadminBefore = {
            'startToFinish': time,
            'finishToStart': timeReversed,
            'deltaWithOfficial': {
                'startToFinish': startToFinishDeltaWithOfficial,
                'finishToStart': finishToStartDeltaWithOfficial,
            },
            'timeForRequest': moment.duration(moment().diff(startTimePreOverhaul)),
            'profile': profile
        };
        addProfileStatistics(wanderwegMetadata.geoadminBefore, profile);
        // requesting post overhaul profile
        const startTimePostOverhaul = moment();
        fetch('http://service-alti.int.bgdi.ch/' + newBranchName + '/rest/services/profile.json' + urlParams, requestConfig)
        .then(response => {
            if (!response.ok) throw Error(response.status); else return response;
        })
        .then(response => response.json())
        .then(profile => {
            const time = hikingTime(profile),
                  timeReversed = hikingTime(reverseProfile(profile)),
                  startToFinishDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.startToFinish - time),
                  finishToStartDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.finishToStart - timeReversed),
                  timeForRequest = moment.duration(moment().diff(startTimePostOverhaul));
            wanderwegMetadata.geoadminAfter = {
                'startToFinish': time,
                'finishToStart': timeReversed,
                'deltaWithOfficial': {
                    'startToFinish': startToFinishDeltaWithOfficial,
                    'finishToStart': finishToStartDeltaWithOfficial,
                },
                'timeForRequest': timeForRequest,
                'trend': {
                    'startToFinish': trendDifference(wanderwegMetadata.geoadminBefore.deltaWithOfficial.startToFinish, startToFinishDeltaWithOfficial),
                    'finishToStart': trendDifference(wanderwegMetadata.geoadminBefore.deltaWithOfficial.finishToStart, finishToStartDeltaWithOfficial),
                    'timeForRequest': () => timeForRequest - wanderwegMetadata.geoadminBefore.timeForRequest
                },
                'profile': profile
            };
            addProfileStatistics(wanderwegMetadata.geoadminAfter, profile);
            callback();
        })
        .catch(error => {
            console.log('Error while requesting profile for "' + wanderwegMetadata.name + '"', error);
            callback();
        })
    });
}

const app = new Vue({
            el: '#app',
            data: {
                loadingMessage: '1/2 Loading metadata',
                loading: true,
                rawData: null
            },
            methods: {
                exportToCsv: function () {
                    let csvData = [];
                    document.querySelectorAll('#main-table tr').forEach(row => {
                        let csvDataRow = [];
                        row.querySelectorAll("td, th").forEach(cols => csvDataRow.push(cols.innerText));
                        csvData.push(csvDataRow);
                    });
                    const csvContent = 'data:text/csv;charset=utf-8,' + csvData.map(row => row.join(";")).join('\r\n');
                    const encodedUri = encodeURI(csvContent);
                    const link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    link.setAttribute("download", "service-app.csv");
                    document.body.appendChild(link); // Required for FF
                    link.click();
                    document.body.removeChild(link);
                }
            },
            created: function () {
                fetch('stats_data').then(response => response.json()).then(json => {
                    json.forEach(data => {
                        data.geoadminBefore.deltaWithOfficial = {
                            startToFinish: Math.abs(data.officialTime.startToFinish - data.geoadminBefore.startToFinish),
                            finishToStart: Math.abs(data.officialTime.finishToStart - data.geoadminBefore.finishToStart)
                        };
                    });
                    // for each wanderweg, we will ask for the profile, and then calculate hiking time to compare
                    // with official hiking time data
                    // we will launch this requests in batches, in order to not overload our backend
                    let currentIndex = 0;
                    let pendingRequestsCounter = 0;
                    let finishedRequestsCounter = 0;
                    const maxConcurrentRequests = 1;
                    // when developing, change this to any number to shorten page load time
                    const debug_nb_request_max = json.length;

                    const _getProfileRecurse = () => {
                        if (pendingRequestsCounter === 0 && currentIndex < debug_nb_request_max - 1) {
                            while (pendingRequestsCounter < maxConcurrentRequests) {
                                pendingRequestsCounter++;
                                getProfile(json[currentIndex], () => {
                                    pendingRequestsCounter--;
                                    finishedRequestsCounter++;
                                    this.loadingMessage = '2/2 Loading profiles... (' + finishedRequestsCounter + '/' + debug_nb_request_max + ')';
                                    _getProfileRecurse();
                                });
                                currentIndex++;
                            }
                        } else if (finishedRequestsCounter === debug_nb_request_max - 1) {
                            console.log('loading done', json);
                            this.rawData = json;
                            this.loading = false;
                        }
                    };

                    this.loadingMessage = '2/2 Loading profiles...';
                    _getProfileRecurse();
                });
            }
        });
