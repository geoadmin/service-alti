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
        wanderwegMetadata.timePreOverhaul = {
            'startToFinish': time,
            'finishToStart': timeReversed,
            'deltaWithOfficial': {
                'startToFinish': startToFinishDeltaWithOfficial,
                'finishToStart': finishToStartDeltaWithOfficial,
            },
            'timeForRequest': moment.duration(moment().diff(startTimePreOverhaul)),
            'amountPoints': profile.length
        };
        // requesting post overhaul profile
        const startTimePostOverhaul = moment();
        fetch('http://service-alti.int.bgdi.ch/' + newBranchName + '/rest/services/profile.json' + urlParams, requestConfig)
        .then(response => {
            if (!response.ok) throw Error(response.status); else return response;
        })
        .then(response => response.json())
        .then(profile => {
            wanderwegMetadata.profile = profile;
            const time = hikingTime(profile),
                  timeReversed = hikingTime(reverseProfile(profile)),
                  startToFinishDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.startToFinish - time),
                  finishToStartDeltaWithOfficial = Math.abs(wanderwegMetadata.officialTime.finishToStart - timeReversed),
                  timeForRequest = moment.duration(moment().diff(startTimePostOverhaul));
            wanderwegMetadata.geoadminHikingTime = {
                'startToFinish': time,
                'finishToStart': timeReversed,
                'deltaWithOfficial': {
                    'startToFinish': startToFinishDeltaWithOfficial,
                    'finishToStart': finishToStartDeltaWithOfficial,
                },
                'timeForRequest': timeForRequest,
                'trend': {
                    'startToFinish': trendDifference(wanderwegMetadata.timePreOverhaul.deltaWithOfficial.startToFinish, startToFinishDeltaWithOfficial),
                    'finishToStart': trendDifference(wanderwegMetadata.timePreOverhaul.deltaWithOfficial.finishToStart, finishToStartDeltaWithOfficial),
                    'timeForRequest': () => timeForRequest - wanderwegMetadata.timePreOverhaul.timeForRequest
                },
                'amountPoints': profile.length
            };
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
            created: function () {
                fetch('stats_data').then(response => response.json()).then(json => {
                    console.log('data received from the server: ', json);
                    json.forEach(data => {
                        data.timePreOverhaul.deltaWithOfficial = {
                            startToFinish: Math.abs(data.officialTime.startToFinish - data.timePreOverhaul.startToFinish),
                            finishToStart: Math.abs(data.officialTime.finishToStart - data.timePreOverhaul.finishToStart)
                        };
                    });
                    // for each wanderweg, we will ask for the profile, and then calculate hiking time to compare
                    // with official hiking time data
                    // we will launch this requests in batches, in order to not overload our backend
                    let currentIndex = 0;
                    let pendingRequestsCounter = 0;
                    let finishedRequestsCounter = 0;
                    const maxConcurrentRequests = 1;
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
