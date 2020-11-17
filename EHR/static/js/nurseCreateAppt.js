$(document).ready(function() {
    $("#doctor").addClass("disabled");
    $("#slot").addClass("disabled");
    $("select").empty();
    $("#status span").removeClass("visible");
    $("#status span").addClass("invisible");
    $.ajax({
      url: "http://localhost:5000/getDepartmentsForNurse",
      type: 'GET',
      success: function(res){
        for (let i=0; i < res.length; i++) {
          $("#department").append(new Option(res[i].deptName, res[i].deptID))
        }
      }
    });

    //--------------------form--------------------
    $("#department").on("change", function(){
      var deptID = $(this).children(":selected").value();
      $.ajax({
        url: "http://localhost:5000/nurseGetDoctorsForDepartment",
        type: 'POST',
        data: {'deptID': deptID},
        success: function(res){
          $(this).empty();
          for (let i=0; i < res.length; i++) {
            $(this).append(new Option(res[i].doctorName, res[i].doctorID))
          }
          $("#doctor").removeClass("disabled");
        }
      });
    });

    $("#doctor").on("change", function(){
      var doctorID = $(this).children(":selected").data();
      $.ajax({
        url: "http://localhost:5000/nurseGetSlotsForDoctor",
        type: 'POST',
        data: {'doctorID': doctorID},
        success: function(res){
          $(this).empty();
          for (let i=0; i < res.length; i++) {
            $(this).append(new Option(res[i].slotDateTime, res[i].slotID))
          }
          $("#slot").removeClass("disabled");
        }
      });
    });

    $("#createAppt").on("submit", function(event){
      event.preventDefault();
      var data = $(this).serializeArray();
      console.log(data);
      $.ajax({
        url: "http://localhost:5000/nurseCreateAppt",
        type: 'POST',
        data: data,
        success: function(res){
          if (res.ret == "0") {
            $("#status span").text("Success");
          } else {
            $("#status span").text("Error: failed to create the appointment");
          }
          $("#status span").removeClass("invisible");
          $("#status span").addClass("visible");
          setTimeout("window.location.replace('http://localhost:5000/nurseGoCreateAppt')", 1000);
        }
      });
    });

    //-----------------direct------------------
    $("#goBack").on("click", function(event) {
      setTimeout("window.location.replace('http://localhost:5000/loadHomePage')", 1000);
    });

    //-----------------style------------------
    // main navigation
    $(".nav-main").on("click", function(event) {
        event.preventDefault();
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
        event.preventDefault();
        var clickedItem = $(this);
        $(".nav-table").each( function() {
            if ($(this).hasClass("active disabled")) {
              $(this).removeClass("active disabled");
            }
        });
        clickedItem.addClass("active disabled");
    });
});