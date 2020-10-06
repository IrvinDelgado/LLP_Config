var engineData = (function () {
  var engineData = null;
  $.ajax({
    'async': false,
    'global': false,
    'url': "./back-end/Engines.txt",
    'dataType': "json",
    'success': function (data) {
      engineData = data;
    }
  });
  return engineData;
})();


var llp_parts = new Object()
var llp_part_promise = $().SPServices.SPGetListItemsJson({
  webURL: "https://spteam.aa.com/sites/TEQ/BMP/LLPCONFIG",
  listName: "LLP_Parts",
});
$.when(llp_part_promise).done(function() {
  llp_part_data = this.data;
  var day = new Date(llp_part_data[0].LASTUPDATED)
  var dayString = day.toLocaleDateString()
  $('#lastUpdatedOn').text('* Last Updated On '+dayString)
  $.each(llp_part_data,function(i,val){
    var usageCode = val.USAGECODE
    var figNum = val.FIGNUM
    if(usageCode==undefined){usa5geCode=''}
    if(figNum==undefined){figNum=''}
    llp_parts[val.PARTNUMBER]={
        'usageCode':usageCode,
        'figNum':figNum
    }
  })  
});



/*-----------------------------------------  CONFIGURATION BOX  ------------------------------------------------*/

/* Is a helper function to EventListeners to check the config Validation */
function checkValidation() {
  var isValid = true;
  if ($("#engineType").val() == 'Default')
    isValid = false;
  if ($("#engineModel").val() == 'Select Engine Model...')
    isValid = false;
  if ($("#engineModule").val() == 'Select Engine Module...')
    isValid = false;
  return isValid;
}

// Resets the config box
function resetConfig() {
  $("#engineModel").find('option').remove();
  $("#engineModule").find('option').remove();
  $('#engineType').val('Default')
  $("#engineModel").append("<option selected>Select Engine Model...</option>");
  $("#engineModule").append("<option selected>Select Engine Module...</option>");
}


// Dynamically Fills the Model Box in Config Menu
// Also Fills the Module at the end of the function
function modelFill() {
  if ($("#engineType").val() != 'Default') {
    $("#engineModel").find('option').remove();
    modelNames = Object.keys(engineData.AllEngines[$("#engineType").val()])
    $.each(modelNames, function (i, value) {
      $("#engineModel").append("<option value='" + value + "'>" +
        value + "</option>");
    });
    moduleFill();
  }
}



function moduleFill() {
  var list_modules = []
  var query = "<Query>" +
    "<Where>" +
    "<And>" +
    "<Eq><FieldRef Name='ENGINETYPE' LookupId='TRUE'/><Value Type='Text'>" + $("#engineType").val() + "</Value></Eq>" +
    "<Eq><FieldRef Name='ENGINEMODEL'/><Value Type='Text'>" + $("#engineModel").val().replace('/', '-') + "</Value></Eq>" +
    "</And>" +
    "</Where>" +
    "</Query>"
  var view = "<ViewFields><FieldRef Name='ENGINEMODULE'></FieldRef></ViewFields>"

  var traineePromise = $().SPServices.SPGetListItemsJson({
    webURL: "https://spteam.aa.com/sites/TEQ/Reliability/NRTFLIGHTOPS",
    listName: "LLP_TABLE_INFO",
    CAMLQuery: query,
    CAMLViewFields: view,
  });
  $.when(traineePromise).done(function () {
    info = this.data;
    $.each(info, function (i, val) {
      if (list_modules.indexOf(val.ENGINEMODULE)<0) list_modules.push(val.ENGINEMODULE) // would use include function but needs to be IE11 compatible
    })
  }).then(function () {
    $("#engineModule").find('option').remove();
    $.each(list_modules, function (i, value) {
      $("#engineModule").append("<option value='" + value + "'>" +
        value + "</option>");
    });
  });
}

/*---------------------------------------------- END OF CONFIGURATION BOX  ------------------------------------------------*/


/*---------------------------------------------- MODULE MODAL BOX  ---------------------------------------------------------*/

$("#kitMaker").click(function () {
  if (checkValidation()) {
    $("#kitBuilder").modal('show');
    modalFill();
  } else
    alert("Fill all of the Engine Values");
});

$("#kitMakerEngine").click(function () {
  if (checkValidation()) {
    $("#kitBuilder").modal('show');
    buildWholeEngine();
  } else
    alert("Fill all of the Engine Values");
});

/* This function builds the inside of the Modal when Module is clicked */
function linkGenerator(urlKey){
  var link = engineData.Keys.EM[$("#engineType").val()].replace(/CHANGEHERE/g,urlKey)
  return link.replace(/viewXMLFrameContent/g, "manPage")
}
function modalFill() {
  $(".kitBuilderGrid").empty();
  var engineModule =  $("#engineModule").val()
  var engineModuleClass = engineModule.replace(/ /g,'_')
  var query = "<Query>"+
                  "<Where>"+
                      "<And>"+
                      "<Eq><FieldRef Name='ENGINETYPE' LookupId='TRUE'/><Value Type='Text'>" + $("#engineType").val() + "</Value></Eq>"+
                      "<And>"+
                      "<Eq><FieldRef Name='ENGINEMODEL'/><Value Type='Text'>" + $("#engineModel").val().replace('/', '-') + "</Value></Eq>"+
                      "<Eq><FieldRef Name='ENGINEMODULE'/><Value Type='Text'>" + $("#engineModule").val() + "</Value></Eq>"+
                      "</And>"+
                      "</And>"+
                  "</Where>"+
               "</Query>"

  var table_info_promise = $().SPServices.SPGetListItemsJson({
    webURL: "https://spteam.aa.com/sites/TEQ/Reliability/NRTFLIGHTOPS",
    listName: "LLP_TABLE_INFO",
    CAMLQuery: query,
  });
  var engine_data_promise = $().SPServices.SPGetListItemsJson({
    webURL: "https://spteam.aa.com/sites/TEQ/BMP/LLPCONFIG",
    listName: "LLP_ENGINE_DATA",
    CAMLQuery: query,
  });
  $.when(table_info_promise).done(function() {
    table_info = this.data;
    var ataCode = table_info[0].TABLEATACODE
    var urlKey = table_info[0].TABLEKEY
    var link = linkGenerator(urlKey)
    $(".kitBuilderGrid").append("<h3><a href='" + link + "' target='_blank'> TO EM: " + ataCode + "</a></h3>");
    
  }).then($.when(engine_data_promise).done(function() {
    engine_data = this.data;
    $.each(engine_data,function(i,part){
      var moduleName = part.ENGINEMODULE
      var partNum = part.PARTTEXT.replace(/ *\([^)]*\) */g, "");
      var partClassTitle = part.PARTTITLE.replace(/ /g,'_')
      llp_parts[partNum]['cycles'] = part.PARTCYCLE

      if ($("." + partClassTitle + "Table").length == 0)
          $(".kitBuilderGrid").append("<div class='" + partClassTitle + "Table modalInline col-md-4'><h5>" + part.PARTTITLE + "</h5></div>");
      $("." + partClassTitle + "Table").append("<div class= 'form-check " + partNum + "' ></div>");
      $('.' + partNum).append(
        "<input class='form-check-input " + partClassTitle + " " + engineModuleClass + "' type='checkbox' name='partNum' value='" + partNum + "' " +
        "id=" + partNum + " onclick = checkFilter('" + partClassTitle + "','" + partNum + "','" + engineModuleClass + "')>\n" +
        "<label class='form-check-label' for=" + partNum + " >" + part.PARTTEXT + "</label>"
      );

      
    });
    if(table_info[0].hasOwnProperty('TABLENOTES'))
      $(".kitBuilderGrid").append("<div><pre><i>" + table_info[0].TABLENOTES + "</i></pre></div>")
    else
      $(".kitBuilderGrid").append("<div><i>NO NOTES FOR THIS MODULE</i></div>")
  }));

  $("#moduleTitle").text($("#engineModule").val())


}

/*---------------------------------------------- END OF MODULE MODAL BOX  ---------------------------------------------------*/


/*---------------------------------------------- ENGINE MODAL BOX  -----------------------------------------------------------*/

/*  This Builds the complete engine when the Engine button is clicked */

function baseEngineSections(){
  document.getElementById("moduleTitle").textContent = $("#engineModel").val()
  $.each(engineData.engineSections[$("#engineType").val()], function (i, ch) {
    $(".kitBuilderGrid").append("<div class='" + ch.Section + " chapterWE'><h2>" + ch.Title + " (" + ch.Section + ")</h2></div>");
    $.each(ch.SubSection, function (j, sect) {
      $("." + ch.Section).append("<div class='" + sect.Section + " sectionWE'><h4>" + sect.Title + " (" + sect.Section + ")</h4></div>");
    })
  })  
}
function buildWholeEngine() {
  $(".kitBuilderGrid").empty();
  baseEngineSections();

    var query = "<Query>"+
                  "<Where>"+
                      "<And>"+
                      "<Eq><FieldRef Name='ENGINETYPE' LookupId='TRUE'/><Value Type='Text'>" + $("#engineType").val() + "</Value></Eq>"+
                      "<Eq><FieldRef Name='ENGINEMODEL'/><Value Type='Text'>" + $("#engineModel").val().replace('/', '-') + "</Value></Eq>"+
                      "</And>"+
                  "</Where>"+
               "</Query>"

  var engine_data_promise = $().SPServices.SPGetListItemsJson({
    webURL: "https://spteam.aa.com/sites/TEQ/BMP/LLPCONFIG",
    listName: "LLP_ENGINE_DATA",
    CAMLQuery: query,
  });
  $.when(engine_data_promise).done(function() {
    engine_data = this.data;
    $.each(engine_data,function(i,part){
      var moduleName = part.ENGINEMODULE.replace(/ /g,'_')
      var partNum = part.PARTTEXT.replace(/ *\([^)]*\) */g, "");
      var partClassTitle = part.PARTTITLE.replace(/ /g,'_')
      var partFigNum = llp_parts[partNum].figNum.slice(0,5)
      llp_parts[partNum]['cycles'] = part.PARTCYCLE

      if ($("." + partClassTitle + partFigNum + "Table").length == 0)
         $("." + partFigNum).append("<div class='" + partClassTitle + partFigNum + "Table modalInline col-md-2'><h5>" + part.PARTTITLE + "</h5></div>");

      $("." + partClassTitle + partFigNum + "Table").append("<div class= 'form-check " + partNum + "' ></div>");
      $('.' + partNum).append(
        "<input class='form-check-input " + partClassTitle +" "+ moduleName+ "' type='checkbox' name='partNum' value='" + partNum +"' "+
        "id='" + partNum + "' onclick = checkFilter('" + partClassTitle + "','" + partNum + "','" + moduleName + "')>\n" +
        "<label class='form-check-label' for='" + partNum + "' >" + partNum + "</label>"
      );

      
    });
    
  }).then(function(){
    cleanWEModal()
  })
  

}

/*  Uses Parent Node so that it works with IE
    Also Some Models don't have sections or even Chapters of an Engine
    So it removes those parts
*/
function cleanWEModal() {
  $.each($(".sectionWE"), function (i, val) {
    if (val.children.length == 1)
      val.parentNode.removeChild(val)
  })
  $.each($(".chapterWE"), function (i, val) {
    if (val.children.length == 1)
      val.parentNode.removeChild(val)
  })
}

// All checked boxes become unchecked and every box becomes enabled
function resetModal() {
  var checkedBoxes = document.querySelectorAll('input[name=partNum]:checked');
  $.each(checkedBoxes, function (i, input) {
    $("#" + input.value).prop("checked", false)
  })
  var disabledBoxes = document.querySelectorAll('input[name=partNum]:disabled');
  $.each(disabledBoxes, function (i, input) {
    $("#" + input.value).prop("disabled", false)
  })
}

/*---------------------------------------------- END OF ENGINE MODAL BOX  ---------------------------------------------------------------*/

/*---------------------------------------------- FILTERING PROCESS  ---------------------------------------------------------------*/

/* Start of the Filtering Process */
var orderChecklist_g = []
$(".close").click(function () {
  orderChecklist_g = []
});
$(".resetMod").click(function () {
  orderChecklist_g = []
});

// Decodes the partName and Module 
// Checked if the user unchecked or checked a box
function checkFilter(partName, prtNum, moduleName) {
  partName = partName.replace(/_/g, " ");
  moduleName = moduleName.replace(/_/g, " ");
  var isChecked = $('#' + prtNum).prop('checked');
  if (isChecked) {
    orderChecklist_g.push([partName, prtNum, moduleName])
    filterHelper(partName, prtNum, moduleName)
  } else {
    var idx = findRightIndex(orderChecklist_g, prtNum)
    orderChecklist_g = orderChecklist_g.slice(0, idx);
    resetModal();
    $.each(orderChecklist_g, function (i, part) {
      $("#" + part[1]).prop("checked", true)
      filterHelper(part[0], part[1], part[2])
    })
  }

}

// Since the orderCheckList is a 2D array this helper function helps look for the index in the array
function findRightIndex(arr, target) {
  val = 0
  $.each(arr, function (i, pair) {
    if (pair[1] == target) {
      val = i
    }
  });
  return val
}

// This function helper is what determines what is disabled
// Filters by using checked boxes 
function filterHelper(partName, prtNum, moduleName) {
  var currPart = llp_parts[prtNum]
  var uCode = (currPart.usageCode).split("");
  var figNum = currPart.figNum;
  var inputsOnScreen = document.querySelectorAll('input[name=partNum]');


  $.each(inputsOnScreen, function (i, input) {
    var inputPrtName = input.classList[1].replace(/_/g, " ");
    var inputModuleName = input.classList[2].replace(/_/g, " ");
    var inputNumber = input.value;
    var inputUCode = (llp_parts[inputNumber].usageCode).split("");
    var inputFigNum = llp_parts[inputNumber].figNum;

    if (inputPrtName == partName && inputNumber != prtNum && inputModuleName == moduleName) {
      $("#" + inputNumber).prop("disabled", true)
    } else {
      if (uCode.length != 0 && figNum == inputFigNum && !isIn(inputUCode, uCode) && inputUCode.length != 0) {
        $("#" + inputNumber).prop("disabled", true)
      }
    }

  });
}

// Helper function to check if 2 arrays share an Element
function isIn(curr, ref) {
  var flag = false;
  $.each(curr, function (i, val) {
    if (ref.indexOf(val) >= 0)
      flag = true
  });
  return flag
}

/*---------------------------------------------- END OF FILTERING  ---------------------------------------------------------------*/





function createTable() {
  var checkedBoxes = document.querySelectorAll('input[name=partNum]:checked');

  $(".engTable").append(
    "<table class='tg'  id='mainTable'>" +
    "<tr class='header'>" +
    "<th class='cell MPN'>MPN</th>" +
    "<th class='cell Desc'>Description</th>" +
    "<th class='cell Cyc'>Cycles</th>" +
    "</tr>" +
    "</table>"
  );

  $.each(checkedBoxes, function (i, val) {
    $(".tg").append(
      "<tr class='cellRow'>" +
      "<td class='cell MPN'>" + val.value + "</td>" +
      "<td class='cell Desc'>" + val.classList[1].replace(/_/g, ' ') + "</td>" +
      "<td class='cell Cyc'>" + llp_parts[val.value].cycles + "</td>" +
      "</tr>"
    );
  });
  $('.tg').prop("style", "border:1px solid black;border-collapse:collapse;padding:10px 5px;");
  $('.cell').prop("style", "border:1px solid black;border-collapse:collapse;padding:10px 5px;");
  //Appending the reset button to the end of the table
  $(".engTable").append(
    "<button type='button' id='reset' onclick='resetPage()' class='btn btn-danger tableButtons'>Reset</button>" +
    "<button type='button' id='print' onclick='printPage()' class='btn btn-success tableButtons'>Print</button>" +
    "<button type='button' id='reset' onclick='goBack()' class='btn btn-primary tableButtons'>Return</button>"
  );

  $(".config").hide();
  $("#kitBuilder").modal('hide');
}

//Allows the user to go back to the Selection
function goBack() {
  $("#kitBuilder").modal('show');
  $(".engTable").empty();
  $(".config").show();
}

function printPage() {
  print();

}

function resetPage() {
  location.reload();
}

