$(document).ready(function (){load()});

function load(){
    $("#txt").focus();
    $("#btn").click(function (){ 
        $("#AddControll").empty(); 

 

        var NoOfRec = $("#txt").val();

         if (NoOfRec > 0){
        createControll(NoOfRec)
     }
    });
}

function createControll(NoOfRec){
    var tb1 = "";

    tb1 ="<table>"+
    "<tr>"+
        "<th> Period No </th>"+
        "<th> Start Time Hr </th>"+
        "<th> Start Time Min </th>"+
        "<th> End Time Hr </th>"+
        "<th> End Time Min </th>"+
       
        "</tr>";

        for (i = 1; i <= NoOfRec; i++){
            tb1 += "<tr>"+
            "<td>" + i + "</td>"+
            "<td> <input class='input--style-6 ' type='text' name='shr["+i+"]' id='S1' placeholder='Enter Start Time in hr' autofocus/> </td>"+
            "<td> <input class='input--style-6' type='text' name='smin["+i+"]' id='S2' placeholder='Enter Start Time in min' autofocus/> </td>"+
            "<td> <input class='input--style-6' type='text' name='ehr["+i+"]' id='E1' placeholder='Enter End Time in hr' autofocus/> </td>"+
            "<td> <input class='input--style-6' type='text' name='emin["+i+"]' id='E2' placeholder='Enter End Time in min' autofocus/> </td>"+
            
       "</tr>";
        }
        
        tb1 += "</table>";

        $("#AddControll").append(tb1);
        

}