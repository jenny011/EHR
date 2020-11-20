function goToPage(route, delay){
  setTimeout("window.location.replace('http://localhost:5000/" + route + "')", delay);
}

function sendRequest(route, type, data, successHandler){
  $.ajax({
    url: "http://localhost:5000/nurse" + route,
    type: type,
    data: data,
    success: (res) => {
      successHandler(res);
      $("#overlay").addClass("d-none");
    },
    error: (err) => console.log(err)
  });
}

function jsonify(data){
  var obj = {};
  for(var i=0;i<data.length;i++){
    obj[data[i].name]=data[i].value;
  }
  return obj;
}

//-------------------------tab styling--------------------------
// main navigation
$(".nav-main").on("click", function(event) {
    var clickedItem = $(this);
    $(".nav-main").each( function() {
      if ($(this).hasClass("active disabled")) {
        $(this).removeClass("active disabled");
      }
    });
    clickedItem.addClass("active disabled");
});

// table navigation
$(".nav-table").on("click", function(event) {
    var clickedItem = $(this);
    $(".nav-table").each( function() {
        if ($(this).hasClass("active disabled")) {
          $(this).removeClass("active disabled");
        }
    });
    clickedItem.addClass("active disabled");
});
