function chart(dates, data) {
    $('#chart').highcharts({
        title: {
            text: 'Severity',
            x: -20 //center
        },
        xAxis: {
            categories: dates
        },
        yAxis: {
            title: {
                text: 'Scale (1-10)'
            },
            plotLines: [{
                value: 0,
                width: 1,
                color: '#808080'
            }]
        },
        series: [{
            name: 'Severity',
            data: data
        }]
    });
}

// Extract the dates from data in order. 
function data_dates(data) {
	dates = [];
	for(var i in data) {
		date = data[i][0];
		date = date.replace("T", " @ ");
		dates.push(date);
	}
	return dates;
}

// Extract the values from data in order. 
function data_values(data) {
	values = [];
	for(var i in data) {
		value = data[i][1];
		if($.trim(value)=="1 out of 10") {
			value = 1;
		}
		else if($.trim(value)=="2 out of 10") {
			value = 2;
		}
		else if($.trim(value)=="3 out of 10") {
			value = 3;
		}
		else if($.trim(value)=="4 out of 10") {
			value = 4;
		}
		else if($.trim(value)=="5 out of 10") {
			value = 5;
		}
		else if($.trim(value)=="6 out of 10") {
			value = 6;
		}
		else if($.trim(value)=="7 out of 10") {
			value = 7;
		}
		else if($.trim(value)=="8 out of 10") {
			value = 8;
		}
		else if($.trim(value)=="9 out of 10") {
			value = 9;
		}
		else if($.trim(value)=="10 out of 10") {
			value = 10;
		}
		else {
			value=0;
		}

		values.push(value);
	}
	return values;
}


	function populateValues() {
		var patients = document.getElementById("patients");
		var patient_id = patients.options[patients.selectedIndex].value;

		var field = document.getElementById("field_select");
		var ids = field.options[field.selectedIndex].value.split("-");

		var field_id = ids[0];
		var template_id = ids[1];

		$.ajax({
			type: "GET",
			url: '/clinical/values/' + patient_id + '/' + template_id + '/' + field_id + '/',
			data: {},
			beforeSend: function() {
				$('#chart').empty();
				$('#values_table').empty();
				html = "<img src='http://k37.kn3.net/taringa/9/0/8/7/0/5/4/amigacho123/6BA.gif'/>";
				$('#values_table').html(html);
			},
			complete: function() {
				$('#values_table img').remove();
			},
			success: function(data) {
				var opts = JSON.parse(JSON.stringify(data));
				var html = '';
				if(opts['vals'].length==0) {
					//opts['vals'].push([" T ", "No values available"]);
					html = '<tr class="even_row"><td>No values available.</td></tr>';
					$('#values_table').html(html);
					return;
				}
				else if(field_id == "28217931") {
					dates = data_dates(opts['vals']);
					values = data_values(opts['vals']);
					chart(dates, values);
				}
				// For some reason, the table headers to not display....
				html += '<tr><th>Date</th><th>Time</th><th>Value</th></tr>';
				html += '<tbody id="values">';
				for (var i in opts['vals']) {
					date = opts['vals'][i][0].split("T")[0];
					time = opts['vals'][i][0].split("T")[1];
					row_class="odd_row";
					if(i%2==0) {
						row_class="even_row";
					}
					html += '<tr class="' + row_class + '"><td>' + date + '</td><td>' + time + '</td><td>' + opts['vals'][i][1] + '</td></tr>';
				}
				html += '</tbody>';
				$('#values_table').html(html);
			}});
	}
