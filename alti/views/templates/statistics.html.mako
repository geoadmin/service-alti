<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Service-alti statistics</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
</head>
<body>
    <h2>Wanderweg official hiking time <small>vs.</small> map.geo.admin.ch hiking time</h2>
    <div id="app">
        <div v-if="loading">
            <h4><i class="fas fa-circle-notch fa-spin"></i> {{ loadingMessage }}</h4>
            <div style="color: white">
                 <i class="fas fa-arrow-up"></i>
                 <i class="fas fa-arrow-down"></i>
            </div>
        </div>
        <div v-if="!loading">
            <table class="table table-sm table-striped table-bordered">
                <thead class="thead-dark">
                    <tr>
                        <td></td>
                        <th colspan="2">Official (ASTRA) [minutes]</th>
                        <th colspan="3">Geoadmin pre-overhaul [minutes]</th>
                        <th colspan="4">Geoadmin post-overhaul [minutes]</th>
                        <th colspan="3">Request time [ms]</th>
                    </tr>
                    <tr>
                        <th>Name</th>
                        <th>start &#8614; finish</th>
                        <th>finish &#8614; start</th>
                        <th>s &#8614; f</th>
                        <th>f &#8614; s</th>
                        <th>&Delta; official</th>
                        <th>s &#8614; f</th>
                        <th>f &#8614; s</th>
                        <th>&Delta; official</th>
                        <th>trend</th>
                        <th>Pre-overhaul</th>
                        <th>Post-overhaul</th>
                        <th>trend</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="data in rawData">
                        <td style="max-width: 20vw;">{{ data.name }}</td>
                        <td><strong>{{ data.officialTime.startToFinish }}</strong></td>
                        <td><strong>{{ data.officialTime.finishToStart }}</strong></td>
                        <td>{{ data.timePreOverhaul.startToFinish }}</td>
                        <td>{{ data.timePreOverhaul.finishToStart }}</td>
                        <td>{{ data.timePreOverhaul.deltaWithOfficial.startToFinish }} / {{ data.timePreOverhaul.deltaWithOfficial.finishToStart }}</td>
                        <td v-if="data.geoadminHikingTime">{{ data.geoadminHikingTime.startToFinish }}</td>
                        <td v-if="data.geoadminHikingTime">{{ data.geoadminHikingTime.finishToStart }}</td>
                        <td v-if="data.geoadminHikingTime">{{ data.geoadminHikingTime.deltaWithOfficial.startToFinish }} / {{ data.geoadminHikingTime.deltaWithOfficial.finishToStart }}</td>
                        <td v-if="data.geoadminHikingTime">
                            <span v-bind:class="{ 'text-danger': data.geoadminHikingTime.trend.startToFinish > 0, 'text-success': data.geoadminHikingTime.trend.startToFinish < 0 }">
                                <i class="fas" v-bind:class="{ 'fa-arrow-up': data.geoadminHikingTime.trend.startToFinish > 0, 'fa-arrow-down': data.geoadminHikingTime.trend.startToFinish < 0 }"></i>
                                {{ data.geoadminHikingTime.trend.startToFinish }}
                            </span>
                            &nbsp;/&nbsp;
                            <span v-bind:class="{ 'text-danger': data.geoadminHikingTime.trend.finishToStart > 0, 'text-success': data.geoadminHikingTime.trend.finishToStart < 0 }">
                                <i class="fas" v-bind:class="{ 'fa-arrow-up': data.geoadminHikingTime.trend.finishToStart > 0, 'fa-arrow-down': data.geoadminHikingTime.trend.finishToStart < 0 }"></i>
                                {{ data.geoadminHikingTime.trend.finishToStart }}
                            </span>
                        </td>
                        <td v-if="data.timePreOverhaul.timeForRequest">{{ data.timePreOverhaul.timeForRequest.asMilliseconds() }}</td>
                        <td v-if="data.geoadminHikingTime">{{ data.geoadminHikingTime.timeForRequest.asMilliseconds() }}</td>
                        <td v-if="data.geoadminHikingTime && data.timePreOverhaul.timeForRequest">
                            <span v-bind:class="{ 'text-danger': data.geoadminHikingTime.trend.timeForRequest() > 0, 'text-success': data.geoadminHikingTime.trend.timeForRequest() < 0 }">
                                <i class="fas" v-bind:class="{ 'fa-arrow-up': data.geoadminHikingTime.trend.timeForRequest() > 0, 'fa-arrow-down': data.geoadminHikingTime.trend.timeForRequest() < 0 }"></i>
                                {{ data.geoadminHikingTime.trend.timeForRequest() }}
                            </span>
                        </td>
                        <td v-if="!data.geoadminHikingTime">N/A</td>
                        <td v-if="!data.geoadminHikingTime">N/A</td>
                        <td v-if="!data.geoadminHikingTime">N/A</td>
                        <td v-if="!data.geoadminHikingTime">N/A</td>
                        <td v-if="!data.timePreOverhaul.timeForRequest">N/A</td>
                        <td v-if="!data.geoadminHikingTime">N/A</td>
                        <td v-if="!data.geoadminHikingTime || !data.timePreOverhaul.timeForRequest">N/A</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.7/umd/popper.min.js" integrity="sha384-UO2eT0CpHqdSJQ6hJty5KVphtPhzWj9WO1clHTMGa3JDZwrnQq4sF86dIHNDz0W1" crossorigin="anonymous"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/js/bootstrap.min.js" integrity="sha384-JjSmVgyd0p3pXB1rRibZUAYoIIy6OrQ6VrjIEaFf/nJGzIxFDsf4x0xIM+B07jRM" crossorigin="anonymous"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.8.0/dist/Chart.min.js"></script>
    <script src="https://momentjs.com/downloads/moment-with-locales.js"></script>
    <script src="https://kit.fontawesome.com/94b67b71c9.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/vue"></script>
    <script src="./static/stats/app.js"></script>
    <script src="./static/stats/hikingtime.js"></script>
</body>
</html>