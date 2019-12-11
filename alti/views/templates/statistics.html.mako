<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Service-alti statistics</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
    <style>
        #main-table {
            font-size: 11px;
        }
        #main-table thead th {
            position: -webkit-sticky;
            position: sticky;
            top: 21px;
        }
        #main-table thead .first-line th {
            top: 0;
        }
        #main-table thead .first-line {
            text-align: center;
        }
        #main-table td.name {
            max-width: 10vw;
        }
        #main-table tr .name,
        #main-table tbody .last {
            border-right: 1px solid #343a40;
        }
        #main-table td:not(.name) {
            text-align: right;
        }
        .table-xs td, .table-xs th {
            padding: 2px;
        }
    </style>
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
            <button v-on:click="exportToCsv()" class="btn btn-sm btn-primary">Export to CSV</button>
            <table id="main-table" class="table table-xs table-striped table-bordered">
                <thead class="thead-dark">
                    <tr class="first-line">
                        <th></th>
                        <th colspan="6" class="official last">Official (ASTRA)</th>
                        <th colspan="8" class="geoadmin-before last">Geoadmin before</th>
                        <th colspan="8" class="geoadmin-after last">Geoadmin after</th>
                        <th colspan="2" class="trend last">Trend</th>
                        <th colspan="2">Points in profile</th>
                    </tr>
                    <tr>
                        <th>Name</th>
                        <th class="official">&#8613;&nbsp;[m]</th>
                        <th class="official">&#8615;&nbsp;[m]</th>
                        <th class="official">&#177;&nbsp;[m]</th>
                        <th class="official">&#8614;&nbsp;[km]</th>
                        <th class="official">s&nbsp;&#8614;&nbsp;f [min]</th>
                        <th class="official last">f&nbsp;&#8614;&nbsp;s [min]</th>
                        <th class="geoadmin-before">&#8613;&nbsp;[m]</th>
                        <th class="geoadmin-before">&#8615;&nbsp;[m]</th>
                        <th class="geoadmin-before">&#177;&nbsp;[m]</th>
                        <th class="geoadmin-before">&#8614;&nbsp;[km]</th>
                        <th class="geoadmin-before">s&nbsp;&#8614;&nbsp;f [min]</th>
                        <th class="geoadmin-before">f&nbsp;&#8614;&nbsp;s [min]</th>
                        <th class="geoadmin-before">&Delta;s&nbsp;&#8614;&nbsp;f</th>
                        <th class="geoadmin-before last">&Delta;f&nbsp;&#8614;&nbsp;s</th>
                        <th class="geoadmin-after">&#8613;&nbsp;[m]</th>
                        <th class="geoadmin-after">&#8615;&nbsp;[m]</th>
                        <th class="geoadmin-after">&#177;&nbsp;[m]</th>
                        <th class="geoadmin-after">&#8614;&nbsp;[km]</th>
                        <th class="geoadmin-after">s&nbsp;&#8614;&nbsp;f</th>
                        <th class="geoadmin-after">f&nbsp;&#8614;&nbsp;s</th>
                        <th class="geoadmin-after">&Delta;s&nbsp;&#8614;&nbsp;f</th>
                        <th class="geoadmin-after last">&Delta;f&nbsp;&#8614;&nbsp;s</th>
                        <th class="trend">s&nbsp;&#8614;&nbsp;f</th>
                        <th class="trend last">f&nbsp;&#8614;&nbsp;s</th>
                        <th>Before</th>
                        <th>After</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="data in rawData">
                        <td class="name">{{ data.name }}</td>
## Official time
                        <td class="official">{{ data.officialTime.elevationUp }}</td>
                        <td class="official">{{ data.officialTime.elevationDown }}</td>
                        <td class="official">{{ data.officialTime.elevationUp - data.officialTime.elevationDown }}</td>
                        <td class="official">{{ Math.round(data.officialTime.totalDistance / 100.0) / 10.0 }}</td>
                        <td class="official"><strong>{{ data.officialTime.startToFinish }}</strong></td>
                        <td class="official last"><strong>{{ data.officialTime.finishToStart }}</strong></td>
## Before
                        <td v-if="data.geoadminBefore" class="geoadmin-before">{{ data.geoadminBefore.elevationUp }}</td>
                        <td v-if="data.geoadminBefore" class="geoadmin-before">{{ data.geoadminBefore.elevationDown }}</td>
                        <td v-if="data.geoadminBefore" class="geoadmin-before">{{ data.geoadminBefore.elevationSum }}</td>
                        <td v-if="data.geoadminBefore" class="geoadmin-before">{{ Math.round(data.geoadminBefore.totalDistance / 100.0) / 10.0 }}</td>
                        <td v-if="!data.geoadminBefore" class="geoadmin-before">N/A</td>
                        <td v-if="!data.geoadminBefore" class="geoadmin-before">N/A</td>
                        <td v-if="!data.geoadminBefore" class="geoadmin-before">N/A</td>
                        <td v-if="!data.geoadminBefore" class="geoadmin-before">N/A</td>
                        <td class="geoadmin-before"><strong>{{ data.geoadminBefore.startToFinish }}</strong></td>
                        <td class="geoadmin-before"><strong>{{ data.geoadminBefore.finishToStart }}</strong></td>
                        <td class="geoadmin-before">{{ data.geoadminBefore.deltaWithOfficial.startToFinish }}</td>
                        <td class="geoadmin-before last">{{ data.geoadminBefore.deltaWithOfficial.finishToStart }}</td>
## After
                        <td v-if="data.geoadminAfter" class="geoadmin-after">{{ data.geoadminAfter.elevationUp }}</td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after">{{ data.geoadminAfter.elevationDown }}</td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after">{{ data.geoadminAfter.elevationSum }}</td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after">{{ Math.round(data.geoadminAfter.totalDistance / 100.0) / 10.0 }}</td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after"><strong>{{ data.geoadminAfter.startToFinish }}</strong></td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after"><strong>{{ data.geoadminAfter.finishToStart }}</strong></td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after">{{ data.geoadminAfter.deltaWithOfficial.startToFinish }}</td>
                        <td v-if="data.geoadminAfter" class="geoadmin-after last">{{ data.geoadminAfter.deltaWithOfficial.finishToStart }}</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after">N/A</td>
                        <td v-if="!data.geoadminAfter" class="geoadmin-after last">N/A</td>
## Trend
                        <td v-if="data.geoadminAfter" class="trend" v-bind:class="{ 'text-danger': data.geoadminAfter.trend.startToFinish > 0, 'text-success': data.geoadminAfter.trend.startToFinish < 0 }">
                            <i class="fas"
                               v-bind:class="{ 'fa-arrow-up': data.geoadminAfter.trend.startToFinish > 0, 'fa-arrow-down': data.geoadminAfter.trend.startToFinish < 0 }">
                            </i>&nbsp;{{ data.geoadminAfter.trend.startToFinish }}
                        </td>
                        <td v-if="data.geoadminAfter" class="trend last" v-bind:class="{ 'text-danger': data.geoadminAfter.trend.finishToStart > 0, 'text-success': data.geoadminAfter.trend.finishToStart < 0 }">
                            <i class="fas"
                               v-bind:class="{ 'fa-arrow-up': data.geoadminAfter.trend.finishToStart > 0, 'fa-arrow-down': data.geoadminAfter.trend.finishToStart < 0 }">
                            </i>&nbsp;{{ data.geoadminAfter.trend.finishToStart }}
                        </td>
                        <td v-if="!data.geoadminAfter" class="trend">N/A</td>
                        <td v-if="!data.geoadminAfter" class="trend last">N/A</td>
## Amount of points
                        <td v-if="data.geoadminBefore && data.geoadminBefore.profile">
                            {{ data.geoadminBefore.profile.length }}
                        </td>
                        <td v-if="data.geoadminAfter">
                            {{ data.geoadminAfter.profile.length }}
                        </td>
                        <td v-if="!data.geoadminBefore || !data.geoadminBefore.profile">N/A</td>
                        <td v-if="!data.geoadminAfter">N/A</td>
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