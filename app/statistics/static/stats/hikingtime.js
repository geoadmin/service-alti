// Reap off of mf-geoadmin3 ProfileService.js file at line 197
// This is not ideal to have our frontend have the "truth" as to how we calculate hiking time, it's very hard
// to test and benchmark this way.

// Hiking time
// Official formula: http://www.wandern.ch/download.php?id=4574_62003b89
// Reference link: http://www.wandern.ch
// But we use a slightly modified version from schweizmobil
function hikingTime (data) {
  var wayTime = 0;

  // Constants of the formula (schweizmobil)
  var arrConstants = [
    14.271, 3.6991, 2.5922, -1.4384,
    0.32105, 0.81542, -0.090261, -0.20757,
    0.010192, 0.028588, -0.00057466, -0.0021842,
    1.5176e-5, 8.6894e-5, -1.3584e-7, -1.4026e-6
  ];

  if (data.length) {
    for (var i = 1; i < data.length; i++) {
      var row = data[i];
      var rowBefore = data[i - 1];

      // Distance betwen 2 points
      var distance = row.dist - rowBefore.dist;

      if (!distance) {
        continue;
      }

      // Difference of elevation between 2 points
      var elevDiff = row.alts['COMB'] - rowBefore.alts['COMB'];

      // Slope value between the 2 points
      // 10ths (schweizmobil formula) instead of % (official formula)
      var s = (elevDiff * 10.0) / distance;

      // The swiss hiking formula is used between -25% and +25%
      // but schweiz mobil use -40% and +40%
      var minutesPerKilometer = 0;
      if (s > -4 && s < 4) {
        for (var j = 0; j < arrConstants.length; j++) {
          minutesPerKilometer += arrConstants[j] * Math.pow(s, j);
        }
      // outside the -40% to +40% range, we use a linear formula
      } else if (s > 0) {
        minutesPerKilometer = (17 * s);
      } else {
        minutesPerKilometer = (-9 * s);
      }
      wayTime += distance * minutesPerKilometer / 1000;
    }
    return Math.round(wayTime);
  }
};